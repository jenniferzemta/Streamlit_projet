"""
cleaning.py — la logique de nettoyage, SANS Streamlit.

📘 Bon réflexe : séparer la logique (ici, testable) de l'interface (dans views/).
Le principe : detect() trouve les problèmes, apply() corrige ceux que l'utilisateur a cochés.
"""
import re
import unicodedata
import warnings
import pandas as pd

DATE_RE = r"\d{1,4}[/\-.]\d{1,2}[/\-.]\d{1,4}"
SKIP_NUM = ("tel", "phone", "matricule", "code", "id", "num")   # ex : ne pas convertir un téléphone en nombre


def norm(s: pd.Series) -> pd.Series:
    """Texte propre : sans espaces superflus, vide -> valeur manquante."""
    return s.astype("string").str.strip().str.replace(r"\s+", " ", regex=True).replace("", pd.NA)


def to_num(s: pd.Series) -> pd.Series:
    t = s.astype("string").str.replace("[\\s\u202f\u00a0]", "", regex=True).str.replace(",", ".", regex=False)
    return pd.to_numeric(t, errors="coerce")


def to_date(s: pd.Series) -> pd.Series:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return pd.to_datetime(s, errors="coerce", dayfirst=True, format="mixed")


def norm_name(name) -> str:
    s = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def _text_cols(df):
    return list(df.select_dtypes(include=["object", "string"]).columns)


def _harmonize(s: pd.Series) -> pd.Series:
    """'douala', 'DOUALA', 'Douala' -> l'écriture la plus fréquente."""
    s = norm(s)
    low = s.str.lower()
    best = s.groupby(low).agg(lambda x: x.value_counts().idxmax())
    return low.map(best)


def apply(df, d, steps):
    """Applique les étapes cochées (dans un ordre logique). Retourne (tableau, journal)."""
    out, log = df.copy(), []
    if "trim" in steps and d["trim"]:
        for c in d["trim"]:
            out[c] = norm(out[c])
        log.append(f"Espaces superflus supprimés dans {len(d['trim'])} colonne(s)")
    if "empty" in steps:
        n = len(out)
        out = out.dropna(how="all")
        if n - len(out):
            log.append(f"{n - len(out)} ligne(s) vide(s) supprimée(s)")
    for c in (d["numbers"] if "numbers" in steps else []):
        out[c] = to_num(out[c])
        log.append(f"« {c} » converti en nombres")
    for c in (d["dates"] if "dates" in steps else []):
        out[c] = to_date(out[c])
        log.append(f"« {c} » converti en dates")
    for c in (d["case"] if "case" in steps else []):
        out[c] = _harmonize(out[c])
        log.append(f"Casse harmonisée dans « {c} »")
    if "dups" in steps:
        n = len(out)
        out = out.drop_duplicates()
        if n - len(out):
            log.append(f"{n - len(out)} doublon(s) supprimé(s)")
    if "drop_cols" in steps and d["drop_cols"]:
        out = out.drop(columns=[c for c in d["drop_cols"] if c in out.columns])
        log.append("Colonnes trop vides supprimées : " + ", ".join(d["drop_cols"]))
    if "fill" in steps:
        for c in d["fill"]:
            if c not in out.columns or not out[c].isna().any():
                continue
            if pd.api.types.is_numeric_dtype(out[c]):
                out[c] = out[c].fillna(out[c].median())
            elif not pd.api.types.is_datetime64_any_dtype(out[c]):
                m = out[c].mode(dropna=True)
                if len(m):
                    out[c] = out[c].fillna(m.iloc[0])
            log.append(f"Valeurs manquantes remplies dans « {c} »")
    if "names" in steps and d["names"]:
        out.columns = [norm_name(c) for c in out.columns]
        log.append("Noms de colonnes normalisés")
    return out, log


def diagnose(df):
    """Retourne (détection, catalogue). Le catalogue = liste de problèmes affichables."""
    d = {k: [] for k in ["trim", "numbers", "dates", "case", "drop_cols", "fill", "names"]}
    text = _text_cols(df)
    d["trim"] = [c for c in text if (norm(df[c]).fillna("<NA>") != df[c].astype("string").fillna("<NA>")).any()]
    tmp = df.copy()
    for c in d["trim"]:
        tmp[c] = norm(tmp[c])
    n_empty = int(tmp.isna().all(axis=1).sum())
    tmp = tmp.dropna(how="all")

    for c in _text_cols(tmp):
        s = tmp[c].dropna()
        if s.empty:
            continue
        if not any(k in str(c).lower() for k in SKIP_NUM) and to_num(s).notna().mean() >= .8:
            d["numbers"].append(c)
        elif s.astype("string").str.contains(DATE_RE).mean() >= .6:
            d["dates"].append(c)
    tmp, _ = apply(tmp, d, {"numbers", "dates"})

    for c in _text_cols(tmp):
        s = norm(tmp[c]).dropna()
        if 2 <= s.nunique() <= 30 and s.str.lower().nunique() < s.nunique():
            d["case"].append(c)
    tmp, _ = apply(tmp, d, {"case"})

    n_dups = int(tmp.duplicated().sum())
    tmp = tmp.drop_duplicates()
    for c in tmp.columns:
        miss = tmp[c].isna().mean()
        if miss > .5:
            d["drop_cols"].append(c)
        elif miss > 0:
            d["fill"].append(c)
    d["names"] = [c for c in df.columns if norm_name(c) != str(c)]

    catalog = []
    def add(step, title, detail, action, default=True):
        catalog.append({"step": step, "title": title, "detail": detail, "action": action, "default": default})
    if d["trim"]:
        add("trim", "Espaces superflus", f"{len(d['trim'])} colonne(s) : {', '.join(map(str, d['trim'][:4]))}", "Supprimer les espaces en trop")
    if n_empty:
        add("empty", "Lignes entièrement vides", f"{n_empty} ligne(s)", "Supprimer ces lignes")
    if d["numbers"]:
        add("numbers", "Nombres stockés comme du texte", ", ".join(map(str, d["numbers"])), "Convertir en nombres")
    if d["dates"]:
        add("dates", "Dates stockées comme du texte", ", ".join(map(str, d["dates"])), "Convertir en vraies dates")
    if d["case"]:
        add("case", "Écritures incohérentes (casse)", ", ".join(map(str, d["case"])), "Harmoniser (ex : douala / DOUALA → Douala)")
    if n_dups:
        add("dups", "Doublons", f"{n_dups} ligne(s) en double", "Supprimer les doublons")
    if d["drop_cols"]:
        add("drop_cols", "Colonnes presque vides (> 50 %)", ", ".join(map(str, d["drop_cols"])), "Supprimer ces colonnes")
    if d["fill"]:
        add("fill", "Valeurs manquantes", f"{len(d['fill'])} colonne(s) : {', '.join(map(str, d['fill'][:4]))}",
            "Remplir (médiane pour les nombres, valeur la plus fréquente pour le texte)", default=False)
    if d["names"]:
        add("names", "Noms de colonnes", f"{len(d['names'])} colonne(s) avec espaces, accents ou majuscules", "Normaliser (minuscules, sans accents)")
    return d, catalog


def quality_score(df) -> float:
    if df.size == 0:
        return 0.0
    return round(max(0.0, 100 - df.isna().mean().mean() * 100 - df.duplicated().mean() * 100), 1)
