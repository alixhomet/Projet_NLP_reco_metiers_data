"""Résultats : synthèse, couverture globale, top 3 expliqué, radar et barres par bloc."""
import ui  # noqa: F401  (doit rester le premier import : configure sys.path)
import pandas as pd
import streamlit as st

from src import explain, viz

st.set_page_config(page_title="Résultats", page_icon="📊")
st.title("Résultats")
ui.fake_banner()
answers, results = ui.require_results()
refs = ui.get_reference()

col1, col2 = st.columns(2)
col1.metric("Couverture globale", f"{results['global_coverage']:.0%}")
col2.metric("Blocs évalués", len(results["block_scores"]))
st.write(results["profile_summary"])

st.header("Top 3 des métiers")
if not results["job_ranking"]:
    st.warning("Profil insuffisamment documenté : aucune recommandation n'est forcée. "
               "Complétez le questionnaire avec des réponses ouvertes plus détaillées.")
for rank, job in enumerate(results["job_ranking"], start=1):
    level = explain.level(job["score"])
    with st.expander(f"{rank}. {job['title']} : score {job['score']:.2f} ({level})", expanded=rank == 1):
        c1, c2, c3 = st.columns(3)
        c1.metric("Score", f"{job['score']:.2f}")
        c2.metric("Couverture", f"{job['coverage']:.2f}")
        c3.metric("Affinité", f"{job['affinity']:.2f}")
        st.write(explain.explain_job(job, refs))
        if job["pref_bonus"]:
            st.caption(f"Bonus de préférences : +{job['pref_bonus']:.2f}")

st.header("Scores par bloc")
left, right = st.columns(2)
left.plotly_chart(viz.radar(results["block_scores"]), width="stretch")
right.plotly_chart(viz.block_bars(results["block_scores"]), width="stretch")
# Valeur en texte de chaque graphique (accessibilité et lisibilité en démo).
st.dataframe(pd.Series(results["block_scores"], name="Score de bloc").round(2).to_frame(),
             width="stretch")
