# Apprendre Streamlit avec Data Studio

## Ordre de lecture conseillé
1. `app.py` : set_page_config, st.navigation, st.Page, st.sidebar
2. `style.py` : st.markdown (HTML/CSS), st.columns
3. `utils.py` : st.session_state, @st.cache_data, st.stop
4. `views/nettoyage.py` : file_uploader, button, checkbox, tabs, download_button, rerun
5. `views/dashboard.py` : radio, selectbox, plotly_chart
6. `views/suivi.py` : number_input, métriques, alertes
7. `views/rapports.py` : text_input, multiselect, components.html
8. `views/prediction.py` : st.form, spinner, scikit-learn
`cleaning.py` ne contient aucun appel Streamlit : c'est la logique pure.

## Règle d'or
À chaque interaction, Streamlit **relance le script de haut en bas**. Ce qui doit survivre va dans `st.session_state`.

## Exercices (du plus simple au plus difficile)
1. Change la couleur BURGUNDY dans `style.py` et dans `.streamlit/config.toml`.
2. Dans `suivi.py`, ajoute le choix « Trimestre » dans la période (règle pandas : "QS").
3. Dans `dashboard.py`, ajoute un 5e dashboard : camembert (px.pie) d'une catégorie.
4. Dans `cleaning.py`, ajoute une détection : colonnes avec des e-mails invalides.
5. Dans `prediction.py`, ajoute un second modèle (LinearRegression) et compare les R².
6. Ajoute une page `views/apropos.py` et déclare-la avec st.Page dans `app.py`.

## Lancer
    pip install -r requirements.txt
    streamlit run app.py
