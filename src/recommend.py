"""Classement des métiers, filtres, garde-fou et assemblage du contrat de sortie.

Propriétaire : P3 (Scoring). Phase 1 : s'appuie sur scoring.py (similarités factices) ;
la forme du dictionnaire renvoyé est déjà celle du contrat n°3.
"""
from functools import cmp_to_key

from . import config, explain
from .scoring import compute_scores, merged_params

INSUFFICIENT = "Profil insuffisamment documenté : complétez le questionnaire (réponses ouvertes plus détaillées)."


def pref_bonus(job, preferences: dict, bonus: float) -> float:
    """Bonus de départage (<= PREF_BONUS) selon les préférences de secteur / type de poste.

    Phase 1 : 0.0 partout. jobs.csv n'a pas de colonne secteur ni type de poste : le critère
    de correspondance est à décider à quatre (voir le compte rendu d'amorçage).
    """
    return 0.0


def _compare(a: dict, b: dict) -> int:
    """Score décroissant ; à 0.02 près, le métier qui couvre le mieux ses compétences
    d'importance 3 passe devant."""
    ka, kb = a["score"] + a["pref_bonus"], b["score"] + b["pref_bonus"]
    if abs(ka - kb) <= config.TIE_MARGIN and a["_cov3"] != b["_cov3"]:
        return -1 if a["_cov3"] > b["_cov3"] else 1
    return -1 if ka > kb else (1 if ka < kb else 0)


def recommend(scores: dict, refs: dict, answers: dict, params: dict | None = None) -> dict:
    """Classe les métiers et renvoie le dictionnaire du contrat de sortie."""
    p = merged_params(params)
    comps, jc = refs["competencies"], refs["job_competencies"]
    comp_block = dict(zip(comps["competency_id"], comps["block_id"]))
    block_name = dict(zip(refs["blocks"]["block_id"], refs["blocks"]["block_name"]))
    cs = scores["comp_scores"]

    entries = []
    for job in refs["jobs"].itertuples():
        j = scores["jobs"][job.job_id]
        rows = jc[jc["job_id"] == job.job_id]
        importance = dict(zip(rows["competency_id"], rows["importance"]))
        score = p["alpha"] * j["coverage"] + (1 - p["alpha"]) * j["affinity"]
        # Points forts : les deux meilleurs blocs parmi ceux que le métier requiert.
        job_blocks = {block_name[comp_block[c]] for c in importance}
        strengths = sorted(job_blocks, key=lambda b: -scores["block_scores"][b])[:2]
        # Lacunes : compétences d'importance >= 2 avec s' < 0.30, les plus importantes d'abord.
        gaps = sorted((c for c, w in importance.items()
                       if w >= config.GAP_MIN_IMPORTANCE and cs[c] < config.GAP_THRESHOLD),
                      key=lambda c: (-importance[c], cs[c]))[:2]
        # Preuves : les deux compétences du métier les mieux appuyées par un segment.
        proofs = sorted((c for c in importance if c in scores["evidence"]),
                        key=lambda c: -scores["evidence"][c]["sim"])[:2]
        cov3 = [cs[c] for c, w in importance.items() if w == 3]
        entries.append({
            "job_id": job.job_id, "title": job.title,
            "score": score, "coverage": j["coverage"], "affinity": j["affinity"],
            "pref_bonus": pref_bonus(job, answers.get("preferences", {}), p["pref_bonus"]),
            "strengths": strengths, "gaps": gaps,
            "evidence": [{"segment": scores["evidence"][c]["segment"], "competency": c,
                          "sim": round(scores["evidence"][c]["sim"], 4)} for c in proofs],
            "_cov3": sum(cov3) / max(len(cov3), 1),  # clé de départage, retirée plus bas
        })
    # ponytail: cmp non transitif aux égalités à 0.02 près ; suffisant pour 6 à 20 métiers
    entries.sort(key=cmp_to_key(_compare))
    ranking = entries[:config.TOP_N]
    for e in ranking:
        e.pop("_cov3")
        for k in ("score", "coverage", "affinity", "pref_bonus"):
            e[k] = round(e[k], 4)

    # Garde-fou : meilleur score trop bas, ou aucune similarité au-dessus de τ_bas.
    insufficient = (not ranking or ranking[0]["score"] < p["guard_threshold"]
                    or scores["max_sim"] <= p["tau_low"])
    return {
        "profile_summary": INSUFFICIENT if insufficient else explain.summarize_profile(scores["block_scores"]),
        "global_coverage": round(scores["global_coverage"], 4),
        "block_scores": {b: round(v, 4) for b, v in scores["block_scores"].items()},
        "job_ranking": [] if insufficient else ranking,
        "similarity_matrix": scores["similarity_matrix"],
    }


def run_engine(answers: dict, refs: dict, params: dict | None = None) -> dict:
    """Point d'entrée unique pour l'app et les notebooks : réponses -> contrat de sortie."""
    return recommend(compute_scores(answers, refs, params), refs, answers, params)
