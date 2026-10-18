"""
Étape 5 — Outil de prédiction (machine learning simple avec scikit-learn).

📘 Concepts Streamlit vus ici :
   - st.button + st.session_state : entraîner une fois, réutiliser le modèle
   - st.form                      : regrouper des champs, un seul envoi
   - st.spinner                   : indiquer un calcul en cours
"""
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from style import page_header, kpi_row, style_fig
from utils import require_data, column_kinds, fmt

page_header("Étape 5 · Intelligence", "Outil de prédiction",
            "Choisis ce que tu veux prédire : l'outil entraîne un modèle, mesure sa fiabilité et te laisse tester des cas.")
df, cleaned = require_data()
if not cleaned:
    st.warning("Pour de bons résultats, nettoie d'abord les données (étape 1).")
k = column_kinds(df)


def build_X(data, feats):
    """Prépare les variables : les dates deviennent année / mois / jour de semaine."""
    X = pd.DataFrame(index=data.index)
    for c in feats:
        if c in k["dates"]:
            X[f"{c}_année"], X[f"{c}_mois"], X[f"{c}_jour_semaine"] = data[c].dt.year, data[c].dt.month, data[c].dt.dayofweek
        elif c in k["num"]:
            X[c] = data[c]
        else:
            X[c] = data[c].astype(object).where(data[c].notna(), np.nan)
    return X


targets = k["num"] + [c for c in k["cat"] if df[c].nunique() <= 10]
if not targets:
    st.warning("Aucune colonne ne peut servir de cible (il faut une colonne numérique ou une catégorie à ≤ 10 valeurs).")
    st.stop()
target = st.selectbox("Que veux-tu prédire ?", targets)
is_reg = target in k["num"]
cands = [c for c in df.columns if c != target and (c in k["num"] or c in k["dates"] or c in k["cat"])]
feats = st.multiselect("Variables utilisées pour la prédiction", cands, default=cands)
st.caption(("Régression : prédire un nombre." if is_reg else "Classification : prédire une catégorie.") + " Modèle : forêt aléatoire.")

data = df.dropna(subset=[target])
if len(data) < 30 or not feats:
    st.warning("Il faut au moins 30 lignes avec une valeur cible et au moins une variable.")
    st.stop()

if st.button("Entraîner le modèle", type="primary", icon=":material/model_training:"):
    with st.spinner("Entraînement en cours…"):
        X, y = build_X(data, feats), data[target]
        num_c = list(X.select_dtypes("number").columns)
        cat_c = [c for c in X.columns if c not in num_c]
        pre = ColumnTransformer([
            ("num", SimpleImputer(strategy="median"), num_c),
            ("cat", Pipeline([("imp", SimpleImputer(strategy="most_frequent")),
                              ("oh", OneHotEncoder(handle_unknown="ignore"))]), cat_c)])
        rf = RandomForestRegressor(200, random_state=42) if is_reg else RandomForestClassifier(200, random_state=42)
        model = Pipeline([("pre", pre), ("rf", rf)])
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=.25, random_state=42)
        model.fit(Xtr, ytr)
        pred = model.predict(Xte)
        names = model.named_steps["pre"].get_feature_names_out()
        imp = {}
        for n, v in zip(names, model.named_steps["rf"].feature_importances_):
            base = n.split("__", 1)[1]
            owner = max((c for c in X.columns if base == c or base.startswith(c + "_")), key=len, default=base)
            imp[owner] = imp.get(owner, 0) + v
        st.session_state["model"] = {
            "model": model, "target": target, "feats": feats, "is_reg": is_reg, "n": len(data),
            "metrics": ({"r2": r2_score(yte, pred), "mae": mean_absolute_error(yte, pred)} if is_reg
                        else {"acc": accuracy_score(yte, pred)}),
            "imp": pd.Series(imp).sort_values().rename_axis("variable").reset_index(name="importance")}

m = st.session_state.get("model")
if not m or m["target"] != target or m["feats"] != feats:
    st.info("Clique sur « Entraîner le modèle » pour lancer l'apprentissage avec ces réglages.")
    st.stop()

st.subheader("Fiabilité du modèle")
if m["is_reg"]:
    kpi_row([("R² (0 à 1)", f"{m['metrics']['r2']:.2f}", "part de variation expliquée"),
             ("Erreur moyenne", fmt(m["metrics"]["mae"]), "écart typique de la prédiction"),
             ("Lignes utilisées", m["n"], "75 % apprentissage · 25 % test")])
    if m["metrics"]["r2"] < .3:
        st.warning("Fiabilité faible : le modèle explique peu de variation. Ajoute des variables ou plus de données.")
else:
    kpi_row([("Précision", f"{m['metrics']['acc'] * 100:.0f} %", "bonnes réponses sur le jeu de test"),
             ("Lignes utilisées", m["n"], "75 % apprentissage · 25 % test")])

st.plotly_chart(style_fig(px.bar(m["imp"], x="importance", y="variable", orientation="h", title="Variables les plus influentes")),
                use_container_width=True)

st.subheader("Tester une prédiction")
with st.form("predict"):
    inputs, cols = {}, st.columns(3)
    for i, c in enumerate(m["feats"]):
        with cols[i % 3]:
            if c in k["num"]:
                med = df[c].median()
                inputs[c] = st.number_input(c, value=float(med) if pd.notna(med) else 0.0)
            elif c in k["dates"]:
                inputs[c] = pd.Timestamp(st.date_input(c, value=df[c].max()))
            else:
                inputs[c] = st.selectbox(c, sorted(df[c].dropna().astype(str).unique()))
    go = st.form_submit_button("Prédire", type="primary")
if go:
    row = build_X(pd.DataFrame([inputs]), m["feats"])
    res = m["model"].predict(row)[0]
    st.success(f"Prédiction pour « {target} » : **{fmt(res) if m['is_reg'] else res}**")
    if not m["is_reg"]:
        probs = pd.Series(m["model"].predict_proba(row)[0], index=m["model"].classes_).sort_values(ascending=False)
        st.dataframe(probs.rename("probabilité").map("{:.0%}".format))

with st.expander("💡 Concept Streamlit : st.form"):
    st.markdown("""
Sans `st.form`, chaque champ modifié relance le script. Avec `st.form`, **rien ne se passe** tant que
l'utilisateur n'a pas cliqué sur le bouton d'envoi : idéal pour saisir plusieurs valeurs d'un coup.
""")
