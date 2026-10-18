"""
Étape 3 — Suivi d'un indicateur par rapport à un objectif.

📘 Concepts Streamlit vus ici :
   - st.number_input : saisir l'objectif
   - st.columns      : zone de réglages en une ligne
   - st.warning / st.success : messages d'alerte
"""
import plotly.graph_objects as go
import streamlit as st
from style import page_header, kpi_row, style_fig, PALETTE
from utils import require_data, column_kinds, fmt

page_header("Étape 3 · Pilotage", "Suivi des indicateurs",
            "Choisis un indicateur et un objectif : l'outil montre où tu en es et signale les périodes en retard.")
df, _ = require_data()
k = column_kinds(df)
if not (k["dates"] and k["num"]):
    st.warning("Le suivi nécessite une colonne de dates et une colonne numérique. Vérifie l'étape Nettoyage.")
    st.stop()

a, b, c, d = st.columns(4)
dcol = a.selectbox("Colonne de date", k["dates"])
ncol = b.selectbox("Indicateur suivi", k["num"])
agg = c.selectbox("Calcul", ["sum", "mean", "count"], format_func={"sum": "Somme", "mean": "Moyenne", "count": "Nombre"}.get)
per = d.selectbox("Période", ["Mois", "Semaine", "Jour"])
rule = {"Mois": "MS", "Semaine": "W", "Jour": "D"}[per]

s = df.dropna(subset=[dcol]).set_index(dcol)[ncol].resample(rule).agg(agg)
default_goal = float(round(s.mean(), 0)) if len(s) else 0.0
goal = st.number_input(f"Objectif par {per.lower()}", min_value=0.0, value=default_goal, step=max(default_goal / 20, 1.0))

res = s.reset_index()
res.columns = ["periode", "valeur"]
res["atteint"] = res["valeur"] >= goal
last, prev = res["valeur"].iloc[-1], res["valeur"].iloc[-2] if len(res) > 1 else None
variation = f"{(last - prev) / prev * 100:+.1f} % vs période précédente" if prev else "—"
kpi_row([
    ("Dernière période", fmt(last), variation),
    ("Objectif", fmt(goal), f"par {per.lower()}"),
    ("Périodes à l'objectif", f"{res['atteint'].mean() * 100:.0f} %", f"{int(res['atteint'].sum())} sur {len(res)}"),
    ("Périodes en retard", int((~res["atteint"]).sum()), "sous l'objectif"),
])

if last < goal:
    st.warning(f"La dernière période est sous l'objectif (écart de {fmt(goal - last)}).")
else:
    st.success("La dernière période atteint l'objectif.")

fig = go.Figure()
fig.add_bar(x=res["periode"], y=res["valeur"], marker_color=[PALETTE[3] if ok else PALETTE[0] for ok in res["atteint"]], name=ncol)
fig.add_hline(y=goal, line_dash="dash", annotation_text="Objectif")
fig.update_layout(title=f"{ncol} par {per.lower()} (vert = objectif atteint)")
st.plotly_chart(style_fig(fig), use_container_width=True)

res["Statut"] = res["atteint"].map({True: "✅ Atteint", False: "⚠️ En retard"})
st.dataframe(res.drop(columns="atteint").rename(columns={"periode": "Période", "valeur": ncol}).sort_values("Période", ascending=False),
             use_container_width=True, hide_index=True)
