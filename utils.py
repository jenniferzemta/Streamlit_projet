"""
utils.py — fonctions partagées par toutes les pages.

📘 Concepts Streamlit vus ici :
   - st.session_state : mémoire de l'application entre deux clics / entre deux pages
   - @st.cache_data   : ne pas recalculer ce qui n'a pas changé
   - st.stop()        : arrêter l'exécution de la page
"""
import io
import numpy as np
import pandas as pd
import streamlit as st


@st.cache_data(show_spinner=False)
def read_file(data: bytes, name: str, sheet=None) -> pd.DataFrame:
    buf = io.BytesIO(data)
    if name.lower().endswith(".csv"):
        try:
            return pd.read_csv(buf, sep=None, engine="python")
        except UnicodeDecodeError:
            buf.seek(0)
            return pd.read_csv(buf, sep=None, engine="python", encoding="latin-1")
    return pd.read_excel(buf, sheet_name=sheet if sheet is not None else 0)


@st.cache_data(show_spinner=False)
def sheet_names(data: bytes):
    return pd.ExcelFile(io.BytesIO(data)).sheet_names


def require_data():
    """Retourne (tableau, est_nettoyé). S'il n'y a rien en mémoire, affiche un message et stoppe la page."""
    if "clean" in st.session_state:
        return st.session_state["clean"], True
    if "raw" in st.session_state:
        return st.session_state["raw"], False
    st.info("Aucun fichier chargé. Commence par l'étape Nettoyage.")
    st.page_link("views/nettoyage.py", label="Aller au nettoyage", icon=":material/arrow_forward:")
    st.stop()


def column_kinds(df: pd.DataFrame) -> dict:
    """Classe les colonnes : nombres, dates, catégories (peu de valeurs différentes), texte libre."""
    num = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and not pd.api.types.is_bool_dtype(df[c])]
    dates = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
    rest = [c for c in df.columns if c not in num + dates]
    cat = [c for c in rest if 2 <= df[c].nunique() <= 30]
    text = [c for c in rest if c not in cat]
    return {"num": num, "dates": dates, "cat": cat, "text": text}


def fmt(x) -> str:
    if pd.isna(x):
        return "—"
    s = f"{x:,.0f}" if abs(x) >= 100 else f"{x:,.1f}"
    return s.replace(",", " ")


def to_excel_bytes(sheets: dict) -> bytes:
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="xlsxwriter") as xw:
        for name, d in sheets.items():
            d.to_excel(xw, sheet_name=name[:31], index=False)
    return out.getvalue()


def demo_data(n: int = 150, seed: int = 7) -> pd.DataFrame:
    """Fichier d'exemple volontairement sale : espaces, casse, dates et montants en texte, doublons, lignes vides."""
    rng = np.random.default_rng(seed)
    prices = {"Produit A": 4500, "Produit B": 9000, "Produit C": 15000}
    rows = []
    for i in range(n):
        prod = rng.choice(list(prices))
        qte = int(rng.integers(1, 12))
        ville = rng.choice(["Douala", "douala ", "DOUALA", "Yaoundé", "yaoundé", "Bafoussam"], p=[.3, .1, .1, .25, .1, .15])
        d = pd.Timestamp("2025-01-01") + pd.Timedelta(days=int(rng.integers(0, 600)))
        d_txt = d.strftime(rng.choice(["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]))
        montant = int(qte * prices[prod] * rng.uniform(.9, 1.1) + (3000 if ville.strip().lower() == "douala" else 0))
        m_txt = f"{montant:,}".replace(",", " ") if rng.random() < .7 else str(montant)
        rows.append({
            "Nom Client": f"  Client {int(rng.integers(1, 60)):02d}  ",
            "Ville": ville,
            "Produit": prod,
            "Date commande": d_txt,
            "Quantité": np.nan if rng.random() < .05 else qte,
            "Montant (FCFA)": m_txt,
            "Statut": rng.choice(["Livré", "livré", "En cours", "Annulé"], p=[.5, .2, .2, .1]),
            "Remarque": "RAS" if rng.random() < .08 else None,
        })
    df = pd.DataFrame(rows)
    df = pd.concat([df, df.sample(8, random_state=1), pd.DataFrame([[None] * df.shape[1]] * 3, columns=df.columns)],
                   ignore_index=True)
    return df.sample(frac=1, random_state=3).reset_index(drop=True)
