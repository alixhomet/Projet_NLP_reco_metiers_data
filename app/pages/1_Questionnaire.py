"""Questionnaire : six sections sur une seule page, générées depuis data/questionnaire.json."""
import ui  # noqa: F401  (doit rester le premier import : configure sys.path)
import streamlit as st

from src import recommend, storage

st.set_page_config(page_title="Questionnaire", page_icon="📝")
st.title("Questionnaire")
st.info("Ne saisissez aucun nom ni donnée personnelle. Vos réponses sont stockées "
        "localement et ne sont pas partagées.")

questionnaire = ui.get_questionnaire()
# Types dont la réponse compte dans la barre de progression (le Likert et le nombre ont
# toujours une valeur par défaut).
COUNTED = {"single", "multi", "open", "yes_no_detail"}


def render(section_id: str, q: dict) -> None:
    """Affiche le widget d'une question ; la valeur reste dans st.session_state[clé]."""
    key = f"{section_id}.{q['id']}"
    kind = q["type"]
    if kind == "single":
        st.radio(q["text"], q["options"], index=None, key=key)
    elif kind == "number":
        st.number_input(q["text"], min_value=q["min"], max_value=q["max"], step=1, key=key)
    elif kind == "likert":
        st.select_slider(q["text"], options=[1, 2, 3, 4, 5], value=3, key=key)
    elif kind == "multi":
        st.multiselect(q["text"], q["options"], key=key)
    elif kind == "open":
        st.text_area(q["text"], key=key)
    elif kind == "yes_no_detail":
        st.radio(q["text"], ["oui", "non"], index=None, horizontal=True, key=key)
        if st.session_state.get(key) == "oui":
            st.text_area(q["detail_label"], key=f"{key}.detail")


for section in questionnaire["sections"]:
    st.subheader(section["title"])
    for q in section["questions"]:
        render(section["id"], q)

# Valeurs saisies, indexées par "<section>.<question>" (format attendu par storage.build_answers).
values = {k: v for k, v in st.session_state.items() if isinstance(k, str) and "." in k}
counted = [f"{s['id']}.{q['id']}" for s in questionnaire["sections"]
           for q in s["questions"] if q["type"] in COUNTED]
done = sum(values.get(k) not in (None, "", []) for k in counted)
st.progress(done / len(counted), text=f"{done} / {len(counted)} questions renseignées")

if st.button("Analyser mon profil", type="primary"):
    answers = storage.build_answers(questionnaire, values)
    storage.save_session(answers)
    st.session_state["answers"] = answers
    st.session_state["results"] = recommend.run_engine(answers, ui.get_reference())
    st.switch_page("pages/2_Resultats.py")
