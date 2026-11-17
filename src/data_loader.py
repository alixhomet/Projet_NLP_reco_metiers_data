"""Chargement et validation du référentiel (4 CSV de data/reference/).

Propriétaire : P1 (Données). Contrat : voir CLAUDE.md, « Référentiel ».
La colonne `keywords` sépare les mots-clés par « ; ».
"""
import re
from pathlib import Path

import pandas as pd

from . import config

FILES = ("blocks", "competencies", "jobs", "job_competencies")


def load_reference(path: Path = config.REFERENCE_DIR) -> dict[str, pd.DataFrame]:
    """Lit les quatre CSV, valide le contrat et renvoie {nom: DataFrame}."""
    refs = {name: pd.read_csv(Path(path) / f"{name}.csv", dtype=str, keep_default_na=False)
            for name in FILES}
    refs["job_competencies"]["importance"] = refs["job_competencies"]["importance"].astype(int)
    validate_reference(refs)
    return refs


def validate_reference(refs: dict[str, pd.DataFrame]) -> None:
    """Lève ValueError si un identifiant est dupliqué, une clé étrangère invalide
    ou une importance hors de 1..3."""
    keys = {"blocks": "block_id", "competencies": "competency_id", "jobs": "job_id"}
    for name, key in keys.items():
        if refs[name][key].duplicated().any():
            raise ValueError(f"{name}.csv : {key} en double")
    comp, jc = refs["competencies"], refs["job_competencies"]
    if not comp["block_id"].isin(refs["blocks"]["block_id"]).all():
        raise ValueError("competencies.csv : block_id inconnu")
    if not jc["job_id"].isin(refs["jobs"]["job_id"]).all():
        raise ValueError("job_competencies.csv : job_id inconnu")
    if not jc["competency_id"].isin(comp["competency_id"]).all():
        raise ValueError("job_competencies.csv : competency_id inconnu")
    if not jc["importance"].between(1, 3).all():
        raise ValueError("job_competencies.csv : importance hors de 1..3")
    if jc.duplicated(["job_id", "competency_id"]).any():
        raise ValueError("job_competencies.csv : paire (job_id, competency_id) en double")


def strip_example(text: str) -> str:
    """Retire la mention « EXEMPLE : » en tête d'une description (données d'exemple)."""
    return re.sub(r"^EXEMPLE\s*:\s*", "", text)
