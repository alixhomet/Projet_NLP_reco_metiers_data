"""Page d'accueil : présentation et bouton de démarrage."""
import ui  # noqa: F401  (doit rester le premier import : configure sys.path)
import streamlit as st

st.set_page_config(page_title="Reco métiers", page_icon="🧭")

st.title("Reco métiers")
st.write(
    "Décrivez votre parcours avec vos propres mots. L'application compare vos réponses "
    "au sens près à un référentiel de compétences et vous propose les 3 métiers les plus "
    "proches, avec une explication."
)
ui.fake_banner()
st.page_link("pages/1_Questionnaire.py", label="Commencer le questionnaire", icon="📝")
st.caption("Pages : Questionnaire, Résultats, Transparence (détail du calcul), Référentiel.")
