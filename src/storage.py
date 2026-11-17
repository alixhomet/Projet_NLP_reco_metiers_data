"""Questionnaire (lecture de questionnaire.json) et sauvegarde des sessions en JSON.

Propriétaire : P4 (Application). Pas de nom demandé, stockage local uniquement
(data/sessions/ est ignoré par Git).
"""
import json
import secrets
from datetime import datetime
from pathlib import Path

from . import config


def load_questionnaire(path: Path = config.QUESTIONNAIRE_PATH) -> dict:
    """Lit la description du questionnaire (sections, questions, options)."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def likert_blocks(questionnaire: dict | None = None) -> dict[str, str]:
    """Correspondance clé Likert -> block_id, lue dans le champ `block` des questions."""
    questionnaire = questionnaire or load_questionnaire()
    section = next(s for s in questionnaire["sections"] if s["id"] == "likert")
    return {q["id"]: q["block"] for q in section["questions"]}


def build_answers(questionnaire: dict, values: dict) -> dict:
    """Construit le JSON de réponses (contrat n°1) à partir des valeurs saisies.

    `values` est indexé par "<section>.<question>" ; pour une question yes_no_detail,
    la précision est sous "<section>.<question>.detail".
    """
    answers = {"session_id": new_session_id()}
    for section in questionnaire["sections"]:
        sid = section["id"]
        out = {}
        for q in section["questions"]:
            value = values.get(f"{sid}.{q['id']}")
            if q["type"] == "yes_no_detail":
                if value is not None:
                    detail = (values.get(f"{sid}.{q['id']}.detail") or "").strip()
                    out[q["id"]] = {"reponse": value, "detail": detail}
            elif value not in (None, "", []):
                out[q["id"]] = value
        # La section « outils » est une simple liste dans le contrat, pas un dictionnaire.
        answers[sid] = [t for lst in out.values() for t in lst] if sid == "tools" else out
    return answers


def new_session_id() -> str:
    """Identifiant au format 2026-11-17T10-30-00_a1b2."""
    return f"{datetime.now():%Y-%m-%dT%H-%M-%S}_{secrets.token_hex(2)}"


def save_session(answers: dict, directory: Path = config.SESSIONS_DIR) -> Path:
    """Écrit les réponses dans data/sessions/<session_id>.json et renvoie le chemin."""
    Path(directory).mkdir(parents=True, exist_ok=True)
    path = Path(directory) / f"{answers['session_id']}.json"
    path.write_text(json.dumps(answers, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_session(path: Path) -> dict:
    """Relit une session (ou un profil de test, même format)."""
    return json.loads(Path(path).read_text(encoding="utf-8"))
