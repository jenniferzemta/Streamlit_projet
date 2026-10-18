"""
Étape 2 — Propositions de dashboards selon les colonnes du fichier.

📘 Concepts Streamlit vus ici :
   - st.columns + cartes HTML   : afficher des propositions
   - st.radio / st.selectbox    : l'utilisateur choisit, le graphique se met à jour
   - st.plotly_chart            : graphiques interactifs
"""
import plotly.express as px
import streamlit as st
from style import page_header, kpi_row, badge, style_fig, PALETTE
from utils import require_data, column_kinds, fmt

page_header("Étape 2 · Analyse", "Dashboards proposés",
            "L'outil regarde le type de tes colonnes et te propose les dashboards qui ont du sens.")
df, cleaned = require_data()
if not cleaned:
    st.warning("Ces données n'ont pas été nettoyées : les résultats peuvent être faussés.")
k = column_kinds(df)
num, dates, cat = k["num"], k["dates"], k["cat"]

# --- Propositions : (titre, description, disponible ?) ------------------------
proposals = {
    "overview": ("Vue d'ensemble", "Totaux, moyennes et distribution d'une variable numérique.", bool(num)),
    "time": ("Évolution dans le temps", "Courbe d'un indicateur par jour, semaine ou mois.", bool(dates and num)),
    "category": ("Répartition par catégorie", "Quelle catégorie pèse le plus (ville, produit, statut…).", bool(cat)),
    "corr": ("Corrélations", "Quelles variables numériques évoluent ensemble.", len(num) >= 2),
}
cols = st.columns(len(proposals))
for col, (key, (title, desc, ok)) in zip(cols, proposals.items()):
    col.markdown(f'<div class="card"><h4>{title}</h4><p>{desc}</p>'
                 f'{badge("Disponible", "ok") if ok else badge("Colonnes manquantes", "grey")}</div>', unsafe_allow_html=True)

available = [k_ for k_, v in proposals.items() if v[2]]
if not available:
    st.warning("Aucun dashboard possible : il faut au moins une colonne numérique ou catégorielle.")
    st.stop()
choice = st.radio("Dashboard à afficher", available, format_func=lambda x: proposals[x][0], horizontal=True)
st.divider()

# --- Rendu selon le choix -------------------------------------------------------
if choice == "overview":
    kpi_row([(c, fmt(df[c].sum()), f"moyenne {fmt(df[c].mean())}") for c in num[:4]])
    col = st.selectbox("Variable à explorer", num)
    st.plotly_chart(style_fig(px.histogram(df, x=col, nbins=20, title=f"Distribution de {col}")), use_container_width=True)

elif choice == "time":
    a, b, c, d = st.columns(4)
    dcol = a.selectbox("Colonne de date", dates)
    ncol = b.selectbox("Indicateur", num)
    agg = c.selectbox("Calcul", ["sum", "mean", "count"], format_func={"sum": "Somme", "mean": "Moyenne", "count": "Nombre"}.get)
    per = d.selectbox("Période", ["Mois", "Semaine", "Jour"])
    rule = {"Mois": "MS", "Semaine": "W", "Jour": "D"}[per]
    serie = df.dropna(subset=[dcol]).set_index(dcol)[ncol].resample(rule).agg(agg).reset_index()
    st.plotly_chart(style_fig(px.line(serie, x=dcol, y=ncol, markers=True, title=f"{ncol} par {per.lower()}")), use_container_width=True)

elif choice == "category":
    a, b, c = st.columns(3)
    ccol = a.selectbox("Catégorie", cat)
    ncol = b.selectbox("Indicateur", ["Nombre de lignes"] + num)
    top = c.slider("Nombre de catégories affichées", 3, 20, 10)
    if ncol == "Nombre de lignes":
        agg_df = df[ccol].value_counts().head(top).rename_axis(ccol).reset_index(name="valeur")
    else:
        agg_df = df.groupby(ccol)[ncol].sum().nlargest(top).reset_index(name="valeur")
    fig = px.bar(agg_df.sort_values("valeur"), x="valeur", y=ccol, orientation="h", title=f"{ncol} par {ccol}")
    st.plotly_chart(style_fig(fig), use_container_width=True)

elif choice == "corr":
    corr = df[num].corr()
    fig = px.imshow(corr, text_auto=".2f", color_continuous_scale=["#FFFFFF", PALETTE[1], PALETTE[0]], zmin=0, zmax=1,
                    title="Corrélation entre variables numériques")
    st.plotly_chart(style_fig(fig), use_container_width=True)
    st.caption("Plus la case est foncée, plus les deux variables évoluent ensemble (1 = parfaitement liées).")

with st.expander("💡 Concept Streamlit : widgets et relance"):
    st.markdown("""
Quand tu changes un `selectbox` ou un `radio`, Streamlit relance le script avec la **nouvelle valeur** :
le graphique se redessine tout seul. Pas de bouton « Actualiser » à coder.
""")
