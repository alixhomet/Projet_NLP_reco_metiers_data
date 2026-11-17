"""Transparence : carte de similarité, détail du calcul, paramètres modifiables."""
import ui  # noqa: F401  (doit rester le premier import : configure sys.path)
import pandas as pd
import streamlit as st

from src import config, recommend, viz

st.set_page_config(page_title="Transparence", page_icon="🔍")
st.title("Transparence")
ui.fake_banner()
answers, _ = ui.require_results()
refs = ui.get_reference()

# Paramètres : seuls scoring et recommend sont relancés (pas les embeddings).
st.sidebar.header("Paramètres")
tau_low = st.sidebar.slider("τ_bas", 0.0, 1.0, config.TAU_LOW, 0.01)
tau_high = st.sidebar.slider("τ_haut", 0.0, 1.0, config.TAU_HIGH, 0.01)
alpha = st.sidebar.slider("α (poids de la couverture)", 0.0, 1.0, config.ALPHA, 0.05)
if tau_low >= tau_high:
    st.error("τ_bas doit être inférieur à τ_haut.")
    st.stop()
params = {"tau_low": tau_low, "tau_high": tau_high, "alpha": alpha}
results = recommend.run_engine(answers, refs, params)
st.session_state["results"] = results  # la page Résultats reflète les paramètres choisis

st.header("Carte de similarité")
labels = dict(zip(refs["competencies"]["competency_id"], refs["competencies"]["label"]))
if results["similarity_matrix"]["rows"]:
    st.plotly_chart(viz.similarity_heatmap(results["similarity_matrix"], labels), width="stretch")
    # Valeur en texte du graphique.
    st.dataframe(pd.DataFrame(results["similarity_matrix"]["values"],
                              index=results["similarity_matrix"]["rows"],
                              columns=results["similarity_matrix"]["cols"]).round(2),
                 width="stretch")
else:
    st.info("Aucun segment de texte : renseignez les questions ouvertes.")

st.header("Détail du calcul")
st.latex(r"s'(c)=\mathrm{clip}\left(\frac{sim(c)-\tau_{bas}}{\tau_{haut}-\tau_{bas}},0,1\right)")
st.latex(r"Couv_j=\frac{\sum_c w_{jc}\,s'(c)}{\sum_c w_{jc}}\qquad Score_j=\alpha\,Couv_j+(1-\alpha)\,Aff_j")
st.dataframe(pd.DataFrame([
    {"Métier": j["title"], "Couverture": j["coverage"], "Affinité": j["affinity"],
     "Bonus préférences": j["pref_bonus"], "Score": j["score"]}
    for j in results["job_ranking"]]), width="stretch", hide_index=True)

st.header("Paramètres en vigueur")
st.dataframe(pd.DataFrame({"Valeur": {**config.DEFAULT_PARAMS, **params}}), width="stretch")
