"""
style.py — l'apparence de l'application (inspirée de la capture « SABC Portail »).

📘 Concepts Streamlit vus ici :
   - st.markdown(..., unsafe_allow_html=True) : injecter du HTML/CSS
   - st.columns : disposer des éléments côte à côte
"""
import html
import streamlit as st

BURGUNDY = "#8B0A28"
PALETTE = [BURGUNDY, "#D9798C", "#E8A87C", "#5B8E7D", "#8E7DBE", "#C9B8B1"]

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, .stApp { font-family: 'Inter', sans-serif; }
.stApp { background: #FBF4F1; }
.block-container { padding-top: 2rem; max-width: 1200px; }

/* --- Sidebar façon portail --- */
[data-testid="stSidebar"] { background: #FFFFFF; border-right: 1px solid #F0E3DF; }
[data-testid="stSidebarNav"]::before {
    content: "▣  Data Studio"; display: block; font-weight: 700; font-size: 1.05rem;
    color: #8B0A28; padding: 1rem 1rem .4rem;
}
[data-testid="stSidebarNavLink"] { border-radius: 8px; margin: 2px 8px; }
[data-testid="stSidebarNavLink"][aria-current="page"] { background: #8B0A28; }
[data-testid="stSidebarNavLink"][aria-current="page"] * { color: #FFFFFF !important; }

/* --- Bandeau de titre --- */
.hero { background: linear-gradient(180deg, #FDEFEA, #FBF4F1); border: 1px solid #F3E1DB;
        border-radius: 16px; padding: 1.3rem 1.6rem; margin-bottom: 1rem; }
.eyebrow { color: #8B0A28; font-size: .68rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
.hero h1 { font-size: 1.9rem; margin: .2rem 0; padding: 0; color: #1E1215; }
.hero p { color: #6B5A5E; margin: 0; font-size: .9rem; }

/* --- Cartes KPI et cartes simples --- */
.kpi { background: #fff; border: 1px solid #F0E3DF; border-radius: 12px; padding: .9rem 1rem; }
.kpi .l { font-size: .62rem; text-transform: uppercase; letter-spacing: .06em; color: #8A777B; font-weight: 600; }
.kpi .v { font-size: 1.6rem; font-weight: 700; color: #1E1215; line-height: 1.3; }
.kpi .s { font-size: .72rem; color: #6B5A5E; }
.card { background: #fff; border: 1px solid #F0E3DF; border-radius: 12px; padding: 1rem; height: 100%; }
.card h4 { margin: 0 0 .3rem; font-size: .95rem; padding: 0; }
.card p { margin: 0 0 .6rem; font-size: .8rem; color: #6B5A5E; }

/* --- Pastilles --- */
.badge { display: inline-block; padding: 2px 9px; border-radius: 999px; font-size: .7rem; font-weight: 600; }
.b-ok { background: #E3F6EA; color: #17803D; }
.b-warn { background: #FFF1CC; color: #9A6700; }
.b-grey { background: #EFE9E7; color: #5E4E52; }
.b-bad { background: #FBE0E3; color: #B4162C; }
</style>
"""


def inject_css():
    """À appeler une fois (dans app.py) : le CSS s'applique ensuite à toutes les pages."""
    st.markdown(CSS, unsafe_allow_html=True)


def page_header(eyebrow: str, title: str, subtitle: str):
    st.markdown(
        f'<div class="hero"><div class="eyebrow">{html.escape(eyebrow)}</div>'
        f'<h1>{html.escape(title)}</h1><p>{html.escape(subtitle)}</p></div>',
        unsafe_allow_html=True)


def kpi_row(items):
    """items = liste de (libellé, valeur, sous-texte). Une carte par élément, en colonnes."""
    cols = st.columns(len(items))
    for col, (label, value, sub) in zip(cols, items):
        col.markdown(
            f'<div class="kpi"><div class="l">{html.escape(str(label))}</div>'
            f'<div class="v">{html.escape(str(value))}</div>'
            f'<div class="s">{html.escape(str(sub))}</div></div>', unsafe_allow_html=True)


def badge(text: str, kind: str = "grey") -> str:
    """Retourne le HTML d'une pastille (kind : ok, warn, grey, bad)."""
    return f'<span class="badge b-{kind}">{html.escape(text)}</span>'


def style_fig(fig):
    """Applique la palette et un fond transparent à un graphique Plotly."""
    fig.update_layout(colorway=PALETTE, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#FFFFFF",
                      margin=dict(l=10, r=10, t=50, b=10), font=dict(family="Inter, sans-serif"))
    return fig
