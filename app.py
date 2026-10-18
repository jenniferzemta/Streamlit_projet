"""
app.py — le point d'entrée : `streamlit run app.py`

📘 Concepts Streamlit vus ici :
   - st.set_page_config : titre, icône, largeur (toujours en premier !)
   - st.navigation + st.Page : application à plusieurs pages, menu groupé
   - st.sidebar : contenu de la barre latérale
Chaque page vit dans le dossier views/ et s'exécute avec nav.run().
"""
import hmac
import os

import streamlit as st
from style import inject_css, badge

st.set_page_config(page_title="Data Studio", page_icon="📊", layout="wide")
inject_css()

authenticated = st.session_state.get("authenticated", False)
nav = st.navigation({
    "Navigation principale": [
        st.Page("views/nettoyage.py", title="Nettoyage", icon=":material/cleaning_services:", default=True),
        st.Page("views/dashboard.py", title="Dashboard", icon=":material/dashboard:"),
        st.Page("views/suivi.py", title="Suivi", icon=":material/trending_up:"),
        st.Page("views/rapports.py", title="Rapports", icon=":material/description:"),
        st.Page("views/prediction.py", title="Prédiction", icon=":material/auto_awesome:"),
    ]
}, position="sidebar" if authenticated else "hidden")

if not authenticated:
    _, login_column, _ = st.columns([1, 1.2, 1])
    with login_column:
        st.title("Data Studio", anchor=False)
        st.caption("Connecte-toi pour accéder à ton espace d’analyse.")
        with st.form("login_form"):
            password = st.text_input("Mot de passe", type="password")
            submitted = st.form_submit_button(
                "Se connecter", type="primary", icon=":material/login:"
            )

        if submitted:
            expected_password = os.environ.get("DATA_STUDIO_PASSWORD") or "admin123"
            if hmac.compare_digest(password, expected_password):
                st.session_state["authenticated"] = True
                st.rerun()
            st.error("Mot de passe incorrect.")
    st.stop()

# État du fichier en cours, lu depuis la mémoire de session (voir utils.py)
with st.sidebar:
    if st.button("Se déconnecter", icon=":material/logout:"):
        st.session_state["authenticated"] = False
        st.rerun()
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
