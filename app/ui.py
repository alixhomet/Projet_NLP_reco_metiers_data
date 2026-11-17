"""Aides communes aux pages Streamlit (propriétaire : P4).

À importer EN PREMIER dans chaque page (`import ui`) : Streamlit met le dossier de
Accueil.py dans sys.path, et ce module ajoute la racine du repo pour `from src import ...`.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st  # noqa: E402

from src import config, data_loader, storage  # noqa: E402


@st.cache_data
def get_reference() -> dict:
    """Référentiel (4 DataFrames), chargé une seule fois."""
    return data_loader.load_reference()


@st.cache_data
def get_questionnaire() -> dict:
    """Description du questionnaire, chargée une seule fois."""
    return storage.load_questionnaire()


def fake_banner() -> None:
    """Bandeau tant que le moteur renvoie des scores factices (phase 1)."""
    if config.PHASE1_FAKE_SCORES:
        st.warning("Phase 1 : les similarités sont factices (pas encore de SBERT). "
                   "Le classement n'a aucune valeur réelle.")


def require_results() -> tuple[dict, dict]:
    """Renvoie (answers, results) de la session, ou invite à remplir le questionnaire."""
    if "results" not in st.session_state:
        st.info("Aucun résultat : remplissez d'abord le questionnaire.")
        st.page_link("pages/1_Questionnaire.py", label="Aller au questionnaire")
        st.stop()
    return st.session_state["answers"], st.session_state["results"]
