"""Encodage SBERT avec cache disque (.cache/, invalidé par un hash des CSV).

Propriétaire : P2 (NLP). Phase 1 : squelette. `reference_hash` est réel, le reste sera
écrit par P2 (le moteur factice de scoring.py n'a pas besoin d'embeddings).
"""
import hashlib
from pathlib import Path

import numpy as np

from . import config


def reference_hash(path: Path = config.REFERENCE_DIR) -> str:
    """Hash du contenu des CSV du référentiel : clé d'invalidation du cache."""
    digest = hashlib.sha256()
    for csv in sorted(Path(path).glob("*.csv")):
        digest.update(csv.name.encode() + csv.read_bytes())
    return digest.hexdigest()[:16]


def get_model(name: str = config.MODEL_NAME):
    """Charge le modèle SentenceTransformer (côté app : l'envelopper dans st.cache_resource)."""
    raise NotImplementedError("P2 : charger SentenceTransformer(name)")


def encode(texts: list[str], model=None) -> np.ndarray:
    """Encode des textes en matrice (n_textes, dim), vecteurs normalisés."""
    raise NotImplementedError("P2 : model.encode(texts, normalize_embeddings=True)")


def encode_reference(refs: dict, model=None) -> dict[str, np.ndarray]:
    """Embeddings des compétences et des métiers, lus dans .cache/<hash>/*.npy si présents,
    sinon calculés puis écrits."""
    raise NotImplementedError("P2 : cache .npy invalidé par reference_hash()")
