"""
app.py — le point d'entrée : `streamlit run app.py`

📘 Concepts Streamlit vus ici :
   - st.set_page_config : titre, icône, largeur (toujours en premier !)
   - st.navigation + st.Page : application à plusieurs pages, menu groupé
   - st.sidebar : contenu de la barre latérale
Chaque page vit dans le dossier views/ et s'exécute avec nav.run().
"""
import streamlit as st
from style import inject_css, badge

st.set_page_config(page_title="Data Studio", page_icon="📊", layout="wide")
inject_css()

nav = st.navigation({
    "Navigation principale": [
        st.Page("views/nettoyage.py", title="Nettoyage", icon=":material/cleaning_services:", default=True),
        st.Page("views/dashboard.py", title="Dashboard", icon=":material/dashboard:"),
        st.Page("views/suivi.py", title="Suivi", icon=":material/trending_up:"),
        st.Page("views/rapports.py", title="Rapports", icon=":material/description:"),
        st.Page("views/prediction.py", title="Prédiction", icon=":material/auto_awesome:"),
    ]
})

# État du fichier en cours, lu depuis la mémoire de session (voir utils.py)
with st.sidebar:
    st.divider()
    if "clean" in st.session_state:
        df = st.session_state["clean"]
        st.markdown(badge("Données nettoyées", "ok"), unsafe_allow_html=True)
        st.caption(f"{st.session_state.get('source', 'fichier')} · {len(df)} lignes × {df.shape[1]} colonnes")
    elif "raw" in st.session_state:
        df = st.session_state["raw"]
        st.markdown(badge("Fichier brut", "warn"), unsafe_allow_html=True)
        st.caption(f"{st.session_state.get('source', 'fichier')} · {len(df)} lignes × {df.shape[1]} colonnes")
    else:
        st.markdown(badge("Aucun fichier", "grey"), unsafe_allow_html=True)

nav.run()
