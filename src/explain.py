"""Explications par gabarit, sans modèle génératif.

Propriétaire : P3 (Scoring).
"""
from . import config


def level(score: float) -> str:
    """Niveau affiché : fort (>= 0.65), moyen (0.40 à 0.64), faible (< 0.40)."""
    if score >= config.LEVEL_STRONG:
        return "fort"
    return "moyen" if score >= config.LEVEL_MEDIUM else "faible"


def explain_job(job: dict, refs: dict) -> str:
    """Gabarit : « Recommandé parce que votre phrase « {segment} » est proche de
    {compétence} (similarité {sim}). Points forts : {blocs}. À renforcer : {lacunes}. »"""
    label = dict(zip(refs["competencies"]["competency_id"], refs["competencies"]["label"]))
    parts = []
    if job["evidence"]:
        ev = job["evidence"][0]
        parts.append(f"Recommandé parce que votre phrase « {ev['segment']} » est proche de "
                     f"{label[ev['competency']]} (similarité {ev['sim']:.2f}).")
    if job["strengths"]:
        parts.append(f"Points forts : {', '.join(job['strengths'])}.")
    if job["gaps"]:
        parts.append(f"À renforcer : {', '.join(label[c] for c in job['gaps'])}.")
    return " ".join(parts)


def summarize_profile(block_scores: dict[str, float]) -> str:
    """Synthèse en une phrase : blocs forts (>= 0.65), moyens, faibles."""
    groups = {"fort": [], "moyen": [], "faible": []}
    for block, v in block_scores.items():
        groups[level(v)].append(block)
    labels = (("fort", "solide en"), ("moyen", "intermédiaire en"), ("faible", "à développer en"))
    phrases = [f"{text} {', '.join(groups[lvl])}" for lvl, text in labels if groups[lvl]]
    return "Profil " + " ; ".join(phrases) + "."
