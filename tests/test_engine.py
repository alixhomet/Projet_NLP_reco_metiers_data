"""Tests du moteur (phase 1, scores factices) : forme du contrat, bornes, déterminisme."""
import pytest

from src import config, data_loader, recommend, scoring, storage

ANSWERS = {
    "profile": {"niveau": "Bac+5", "experience_annees": 1},
    "likert": {"python": 4, "stats": 3, "ml": 3, "nlp": 2, "gestion_projet": 3, "cloud": 1},
    "tools": ["Python", "SQL"],
    "open": {"q_projet": "J'ai analysé des données de ventes. J'ai construit un tableau de bord.",
             "q_gout": "J'aime nettoyer des données et entraîner des modèles."},
    "guided": {"tokenisation": {"reponse": "oui", "detail": "Découpage d'avis clients en phrases."}},
    "preferences": {"secteur": ["télécom"]},
}


@pytest.fixture(scope="module")
def refs():
    return data_loader.load_reference()


@pytest.fixture(scope="module")
def result(refs):
    return recommend.run_engine(ANSWERS, refs)


def test_forme_du_contrat(result):
    assert set(result) == {"profile_summary", "global_coverage", "block_scores",
                           "job_ranking", "similarity_matrix"}
    assert len(result["job_ranking"]) == config.TOP_N
    assert set(result["job_ranking"][0]) == {"job_id", "title", "score", "coverage", "affinity",
                                             "pref_bonus", "strengths", "gaps", "evidence"}
    assert set(result["similarity_matrix"]) == {"rows", "cols", "values"}


def test_scores_entre_0_et_1(result):
    assert 0 <= result["global_coverage"] <= 1
    assert all(0 <= v <= 1 for v in result["block_scores"].values())
    for job in result["job_ranking"]:
        assert all(0 <= job[k] <= 1 for k in ("score", "coverage", "affinity"))
        assert 0 <= job["pref_bonus"] <= config.PREF_BONUS


def test_couverture_globale_est_la_moyenne_des_blocs(result):
    blocks = result["block_scores"].values()
    assert result["global_coverage"] == pytest.approx(sum(blocks) / len(blocks), abs=1e-3)
    assert scoring.global_coverage({"a": 0.8, "b": 0.4}, {"a": 3, "b": 1}) == pytest.approx(0.7)


def test_deterministe(refs, result):
    assert recommend.run_engine(ANSWERS, refs) == result


def test_classement_trie(result):
    scores = [j["score"] + j["pref_bonus"] for j in result["job_ranking"]]
    # Tri décroissant à la marge d'égalité près (le départage peut inverser deux scores proches).
    assert all(a >= b - config.TIE_MARGIN for a, b in zip(scores, scores[1:]))


def test_garde_fou_profil_vide(refs):
    result = recommend.run_engine({"open": {}}, refs)
    assert result["job_ranking"] == []
    assert "insuffisamment" in result["profile_summary"]


def test_calibration():
    assert scoring.calibrate(0.25, 0.25, 0.75) == 0
    assert scoring.calibrate(0.75, 0.25, 0.75) == 1
    assert scoring.calibrate(0.5, 0.25, 0.75) == pytest.approx(0.5)


def test_build_answers_respecte_le_contrat():
    q = storage.load_questionnaire()
    values = {"profile.niveau": "Bac+5", "profile.experience_annees": 1, "likert.nlp": 2,
              "tools.outils": ["Python", "SQL"], "open.q_projet": "Texte.",
              "guided.tokenisation": "oui", "guided.tokenisation.detail": "Détail",
              "preferences.secteur": ["télécom"]}
    answers = storage.build_answers(q, values)
    assert answers["tools"] == ["Python", "SQL"]
    assert answers["guided"] == {"tokenisation": {"reponse": "oui", "detail": "Détail"}}
    assert answers["open"] == {"q_projet": "Texte."}
    assert set(answers) == {"session_id", "profile", "likert", "tools", "open", "guided", "preferences"}


def test_questionnaire_six_sections_et_trois_questions_ouvertes():
    q = storage.load_questionnaire()
    assert len(q["sections"]) == 6
    assert sum(len(s["questions"]) for s in q["sections"] if s["id"] == "open") >= 3
