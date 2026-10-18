"""
Étape 1 — Dépôt du fichier + nettoyage guidé.

📘 Concepts Streamlit vus ici :
   - st.file_uploader        : déposer un fichier
   - st.button / st.checkbox : interactions (chaque clic relance le script de haut en bas !)
   - st.session_state        : garder le tableau en mémoire pour les autres pages
   - st.tabs, st.download_button, st.dataframe
"""
import pandas as pd
import streamlit as st
from cleaning import diagnose, apply, quality_score
from style import page_header, kpi_row
from utils import read_file, sheet_names, demo_data, to_excel_bytes

page_header("Étape 1 · Données", "Nettoyage des données",
            "Dépose ton fichier : l'outil repère ce qui doit être corrigé et te laisse choisir quoi appliquer.")

# --- 1. Chargement -----------------------------------------------------------
file = st.file_uploader("Dépose ton fichier Excel ou CSV", type=["xlsx", "xls", "csv"])
if file is not None:
    data = file.getvalue()
    sheet = None
    if not file.name.lower().endswith(".csv"):
        names = sheet_names(data)
        sheet = st.selectbox("Feuille à analyser", names) if len(names) > 1 else names[0]
    source = f"{file.name}" + (f" ({sheet})" if sheet else "")
    if st.session_state.get("source") != source:      # nouveau fichier : on repart de zéro
        st.session_state["raw"] = read_file(data, file.name, sheet)
        st.session_state["source"] = source
        st.session_state.pop("clean", None)
elif st.button("Essayer avec un fichier d'exemple", icon=":material/science:"):
    st.session_state["raw"] = demo_data()
    st.session_state["source"] = "exemple"
    st.session_state.pop("clean", None)

raw = st.session_state.get("raw")
if raw is None:
    st.info("Aucun fichier pour l'instant. Dépose un fichier ou lance l'exemple pour voir comment ça marche.")
    st.stop()

# --- 2. Diagnostic -----------------------------------------------------------
detected, catalog = diagnose(raw)
kpi_row([
    ("Lignes", f"{len(raw):,}".replace(",", " "), "dans le fichier"),
    ("Colonnes", raw.shape[1], "détectées"),
    ("Cellules vides", int(raw.isna().sum().sum()), "avant nettoyage"),
    ("Score qualité", f"{quality_score(raw)} / 100", "vides + doublons"),
])

st.subheader("Ce qu'il faut faire pour nettoyer ce fichier")
if not catalog:
    st.success("Rien à corriger : le fichier est déjà propre.")
else:
    st.caption("Coche les corrections à appliquer. La dernière (valeurs manquantes) est décochée par défaut : elle invente des valeurs.")
    chosen = set()
    for item in catalog:
        label = f"**{item['title']}** — {item['detail']}  \n→ {item['action']}"
        if st.checkbox(label, value=item["default"], key=f"fix_{item['step']}"):
            chosen.add(item["step"])

    # --- 3. Application -----------------------------------------------------
    if st.button("Appliquer le nettoyage", type="primary", icon=":material/check:"):
        cleaned, log = apply(raw, detected, chosen)
        st.session_state["clean"] = cleaned
        st.session_state["log"] = log
        st.rerun()   # relance le script pour que la barre latérale se mette à jour

# --- 4. Résultat -------------------------------------------------------------
if "clean" in st.session_state:
    clean, log = st.session_state["clean"], st.session_state.get("log", [])
    st.subheader("Résultat")
    kpi_row([
        ("Lignes", len(clean), f"{len(clean) - len(raw):+d} vs avant"),
        ("Colonnes", clean.shape[1], f"{clean.shape[1] - raw.shape[1]:+d} vs avant"),
        ("Cellules vides", int(clean.isna().sum().sum()), f"{int(clean.isna().sum().sum() - raw.isna().sum().sum()):+d} vs avant"),
        ("Score qualité", f"{quality_score(clean)} / 100", f"{quality_score(clean) - quality_score(raw):+.1f} pts"),
    ])
    t1, t2, t3 = st.tabs(["Avant", "Après", "Journal des corrections"])
    t1.dataframe(raw, use_container_width=True)
    t2.dataframe(clean, use_container_width=True)
    with t3:
        for line in log or ["Aucune correction appliquée"]:
            st.write("• " + line)
    a, b = st.columns(2)
    a.download_button("Télécharger en Excel", to_excel_bytes({"Données propres": clean, "Journal": pd.DataFrame({"Correction": log})}),
                      file_name="donnees_propres.xlsx", icon=":material/download:")
    b.download_button("Télécharger en CSV", clean.to_csv(index=False).encode("utf-8-sig"),
                      file_name="donnees_propres.csv", icon=":material/download:")
    st.success("Les autres pages utilisent maintenant ces données propres.")

with st.expander("💡 Concept Streamlit : pourquoi st.session_state ?"):
    st.markdown("""
À chaque clic, Streamlit **relance tout le script** et les variables sont perdues.
`st.session_state` est un dictionnaire qui **survit** aux relances et se partage entre les pages.
Ici : `st.session_state["raw"]` (fichier brut) et `st.session_state["clean"]` (fichier nettoyé).
""")
