"""Scoring : similarités, calibration, scores de bloc, couverture (docs/conception.md).

Propriétaire : P3 (Scoring). PHASE 1 : seules les SIMILARITÉS sont factices
(`fake_unit` : valeur déterministe issue d'un hash, sans SBERT). Calibration, plancher
des outils, scores de bloc, couverture par métier et couverture globale suivent déjà
les vraies formules : P3 remplacera `_similarities` / `_affinity_raw` par le calcul
cosinus sur les embeddings de P2.
"""
import hashlib

import numpy as np

from . import config, storage
from .preprocess import extract_segments


def merged_params(params: dict | None) -> dict:
    """Paramètres par défaut de config.py, surchargés par ceux de l'appelant."""
    return {**config.DEFAULT_PARAMS, **(params or {})}


def fake_unit(*parts: str) -> float:
    """Nombre déterministe dans [0, 1[ dérivé d'un hash (jamais hash(), non stable)."""
    digest = hashlib.md5("|".join(parts).encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") / 2**32


def calibrate(sim, tau_low: float, tau_high: float):
    """s'(c) = clip((sim - τ_bas) / (τ_haut - τ_bas), 0, 1). Accepte un scalaire ou un tableau."""
    return np.clip((np.asarray(sim, dtype=float) - tau_low) / (tau_high - tau_low), 0.0, 1.0)


def global_coverage(block_scores: dict[str, float], weights: dict[str, float] | None = None) -> float:
    """Couverture globale = Σ W_b·B_b / Σ W_b, avec W_b = 1 par défaut."""
    if not block_scores:
        return 0.0
    w = {b: (weights or {}).get(b, 1.0) for b in block_scores}
    return sum(w[b] * v for b, v in block_scores.items()) / sum(w.values())


def _similarities(segments: list[dict], comp_ids: list[str]) -> np.ndarray:
    """FACTICE : matrice (segments x compétences) de cosinus entre 0.15 et 0.65."""
    sim = np.array([[0.15 + 0.50 * fake_unit(s["text"], c) for c in comp_ids] for s in segments])
    return sim.reshape(len(segments), len(comp_ids))


def _affinity_raw(text: str, job_ids: list[str]) -> np.ndarray:
    """FACTICE : similarité brute entre tout le texte du profil et chaque métier."""
    if not text:
        return np.zeros(len(job_ids))
    return np.array([0.15 + 0.50 * fake_unit(text, j) for j in job_ids])


def compute_scores(answers: dict, refs: dict, params: dict | None = None) -> dict:
    """Calcule tous les scores intermédiaires d'un profil.

    Renvoie un dictionnaire consommé par `recommend.recommend` :
    segments, comp_scores {competency_id: s'}, comp_sims {competency_id: sim},
    block_scores {block_name: B_b}, global_coverage, jobs {job_id: {coverage, affinity}},
    evidence {competency_id: {segment, sim}}, similarity_matrix, max_sim.
    """
    p = merged_params(params)
    comps, blocks, jc = refs["competencies"], refs["blocks"], refs["job_competencies"]
    comp_ids = list(comps["competency_id"])

    # 1. Similarité brute : meilleure preuve parmi les segments du profil.
    segments = extract_segments(answers)
    sim_matrix = _similarities(segments, comp_ids)
    if len(segments):
        sims, best = sim_matrix.max(axis=0), sim_matrix.argmax(axis=0)
    else:
        sims, best = np.zeros(len(comp_ids)), None

    # 2. Calibration entre τ_bas et τ_haut.
    s = calibrate(sims, p["tau_low"], p["tau_high"])

    # 3. Cases à cocher : un outil coché impose un plancher κ sur les compétences qui le citent.
    tools = {t.lower() for t in answers.get("tools", [])}
    for i, kw in enumerate(comps["keywords"]):
        if tools & {k.strip().lower() for k in kw.split(";")}:
            s[i] = max(s[i], p["kappa"])
    comp_scores = dict(zip(comp_ids, s))

    # 4. Score de bloc : moyenne des s'(c), mélangée à l'auto-évaluation Likert (λ).
    likert_by_block = {b: answers.get("likert", {}).get(k)
                       for k, b in storage.likert_blocks().items()}
    block_scores = {}
    for b in blocks.itertuples():
        ids = comps.loc[comps["block_id"] == b.block_id, "competency_id"]
        mean = float(np.mean([comp_scores[c] for c in ids]))
        L = likert_by_block.get(b.block_id)
        block_scores[b.block_name] = mean if L is None else (1 - p["lambda_"]) * mean + p["lambda_"] * (L - 1) / 4

    # 5. Couverture par métier (pondérée par l'importance) et affinité globale calibrée.
    job_ids = list(refs["jobs"]["job_id"])
    text = " ".join(seg["text"] for seg in segments)
    affinity = calibrate(_affinity_raw(text, job_ids), p["tau_low"], p["tau_high"])
    jobs = {}
    for j, aff in zip(job_ids, affinity):
        rows = jc[jc["job_id"] == j]
        cov = sum(w * comp_scores[c] for c, w in zip(rows["competency_id"], rows["importance"])) / rows["importance"].sum()
        jobs[j] = {"coverage": float(cov), "affinity": float(aff)}

    return {
        "segments": segments,
        "comp_scores": {c: float(v) for c, v in comp_scores.items()},
        "comp_sims": dict(zip(comp_ids, map(float, sims))),
        "block_scores": block_scores,
        "global_coverage": global_coverage(block_scores),
        "jobs": jobs,
        "evidence": {c: {"segment": segments[best[i]]["text"], "sim": float(sims[i])}
                     for i, c in enumerate(comp_ids)} if best is not None else {},
        "similarity_matrix": {"rows": [seg["id"] for seg in segments], "cols": comp_ids,
                              "values": sim_matrix.round(4).tolist()},
        "max_sim": float(sims.max()) if len(segments) else 0.0,
    }
