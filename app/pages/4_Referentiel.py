"""Référentiel : explorer blocs, compétences et métiers."""
import ui  # noqa: F401  (doit rester le premier import : configure sys.path)
import streamlit as st

st.set_page_config(page_title="Référentiel", page_icon="📚")
st.title("Référentiel")
refs = ui.get_reference()

st.header("Blocs")
st.dataframe(refs["blocks"], width="stretch", hide_index=True)

st.header("Compétences")
block_names = dict(zip(refs["blocks"]["block_id"], refs["blocks"]["block_name"]))
choice = st.selectbox("Bloc", ["Tous"] + list(block_names.values()))
comps = refs["competencies"].assign(bloc=lambda d: d["block_id"].map(block_names))
if choice != "Tous":
    comps = comps[comps["bloc"] == choice]
st.dataframe(comps, width="stretch", hide_index=True)

st.header("Métiers")
job = st.selectbox("Métier", refs["jobs"]["title"])
row = refs["jobs"][refs["jobs"]["title"] == job].iloc[0]
st.write(row["description"])
st.dataframe(refs["job_competencies"][refs["job_competencies"]["job_id"] == row["job_id"]]
             .merge(refs["competencies"][["competency_id", "label"]], on="competency_id")
             .sort_values("importance", ascending=False)[["competency_id", "label", "importance"]],
             width="stretch", hide_index=True)
