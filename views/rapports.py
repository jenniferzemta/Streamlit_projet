"""
Étape 4 — Générateur de rapports (HTML + Excel).

📘 Concepts Streamlit vus ici :
   - st.text_input / st.multiselect : paramétrer le rapport
   - st.components.v1.html          : afficher du HTML dans la page
   - st.download_button             : télécharger un fichier généré en mémoire
"""
import html
from datetime import date
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components
from style import page_header, style_fig
from utils import require_data, column_kinds, fmt, to_excel_bytes

page_header("Étape 4 · Livrables", "Générateur de rapports",
            "Compose un rapport à partir de tes données, prévisualise-le, puis télécharge-le.")
df, cleaned = require_data()
k = column_kinds(df)

a, b = st.columns(2)
title = a.text_input("Titre du rapport", "Rapport d'analyse")
author = b.text_input("Auteur", "")
sections = st.multiselect("Sections à inclure", ["Résumé du fichier", "Indicateurs clés", "Statistiques détaillées", "Qualité des données", "Graphique"],
                          default=["Résumé du fichier", "Indicateurs clés", "Statistiques détaillées"])
chart_html = ""
if "Graphique" in sections:
    if k["cat"]:
        c1, c2 = st.columns(2)
        ccol = c1.selectbox("Graphique : catégorie", k["cat"])
        ncol = c2.selectbox("Graphique : indicateur", ["Nombre de lignes"] + k["num"])
        agg_df = (df[ccol].value_counts().rename_axis(ccol).reset_index(name="valeur") if ncol == "Nombre de lignes"
                  else df.groupby(ccol)[ncol].sum().reset_index(name="valeur"))
        fig = style_fig(px.bar(agg_df.sort_values("valeur", ascending=False).head(12), x=ccol, y="valeur", title=f"{ncol} par {ccol}"))
        chart_html = fig.to_html(full_html=False, include_plotlyjs="cdn")
    else:
        st.info("Aucune colonne catégorielle pour le graphique.")

# --- Construction du rapport ------------------------------------------------------
def table_html(d):
    return d.to_html(classes="t", border=0, na_rep="—", float_format=lambda x: f"{x:,.1f}")

parts, excel = [], {}
if "Résumé du fichier" in sections:
    parts.append(f"<h2>Résumé du fichier</h2><p>{len(df)} lignes et {df.shape[1]} colonnes. "
                 f"Colonnes : {html.escape(', '.join(map(str, df.columns)))}.</p>")
if "Indicateurs clés" in sections and k["num"]:
    kp = "".join(f'<div class="kpi"><small>{html.escape(str(c))}</small><b>{fmt(df[c].sum())}</b><span>moyenne {fmt(df[c].mean())}</span></div>' for c in k["num"][:4])
    parts.append(f'<h2>Indicateurs clés</h2><div class="kpis">{kp}</div>')
if "Statistiques détaillées" in sections and k["num"]:
    desc = df[k["num"]].describe().T.reset_index().rename(columns={"index": "variable"})
    parts.append("<h2>Statistiques détaillées</h2>" + table_html(desc.set_index("variable")))
    excel["Statistiques"] = desc
if "Qualité des données" in sections:
    q = df.isna().sum().reset_index()
    q.columns = ["colonne", "valeurs_manquantes"]
    q["pourcentage"] = (q["valeurs_manquantes"] / max(len(df), 1) * 100).round(1)
    parts.append(f"<h2>Qualité des données</h2><p>{int(df.duplicated().sum())} doublon(s).</p>" + table_html(q.set_index("colonne")))
    excel["Qualité"] = q
if chart_html:
    parts.append("<h2>Graphique</h2>" + chart_html)
excel["Données"] = df

REPORT = f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>{html.escape(title)}</title>
<style>body{{font-family:Inter,Arial,sans-serif;max-width:900px;margin:2rem auto;color:#2B1B1F;padding:0 1rem}}
h1{{color:#8B0A28;margin-bottom:0}} h2{{border-bottom:2px solid #F0E3DF;padding-bottom:.2rem;margin-top:2rem}}
.meta{{color:#6B5A5E}} .kpis{{display:flex;gap:12px;flex-wrap:wrap}}
.kpi{{border:1px solid #F0E3DF;border-radius:10px;padding:.7rem 1rem;min-width:150px}}
.kpi small{{display:block;color:#8A777B}} .kpi b{{font-size:1.4rem}} .kpi span{{display:block;font-size:.8rem;color:#6B5A5E}}
table.t{{border-collapse:collapse;width:100%;font-size:.85rem}} .t th{{background:#FDEFEA;text-align:left}}
.t td,.t th{{padding:6px 8px;border-bottom:1px solid #F0E3DF}}</style></head><body>
<h1>{html.escape(title)}</h1><p class="meta">{html.escape(author)} · {date.today():%d/%m/%Y}</p>
{''.join(parts)}</body></html>"""

st.subheader("Aperçu")
components.html(REPORT, height=600, scrolling=True)
c1, c2 = st.columns(2)
c1.download_button("Télécharger le rapport (HTML)", REPORT.encode("utf-8"), file_name="rapport.html", mime="text/html",
                   type="primary", icon=":material/download:")
c2.download_button("Télécharger les tableaux (Excel)", to_excel_bytes(excel), file_name="rapport_tableaux.xlsx", icon=":material/download:")
st.caption("Astuce : ouvre le fichier HTML dans ton navigateur puis « Imprimer → Enregistrer en PDF » pour obtenir un PDF.")
