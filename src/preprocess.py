"""Prétraitement léger des réponses : normalisation et segmentation en phrases.

Propriétaire : P2 (NLP). SBERT lit le texte brut : pas de lemmatisation ni de retrait
des mots vides ici (la lemmatisation ne servira qu'à la baseline TF-IDF).
"""
import re


def normalize(text: str) -> str:
    """Normalise les espaces et les apostrophes."""
    text = text.replace("’", "'").replace("`", "'")
    return re.sub(r"\s+", " ", text).strip()


def split_sentences(text: str) -> list[str]:
    """Découpe un texte en phrases (une phrase = un segment)."""
    # ponytail: découpage par ponctuation ; spaCy/nltk si les abréviations posent problème
    parts = re.split(r"(?<=[.!?])\s+|\n+", normalize(text))
    return [p for p in parts if len(p) > 2]


def extract_segments(answers: dict) -> list[dict]:
    """Extrait les segments d'un profil : questions ouvertes, plus les précisions
    des questions guidées dont la réponse est « oui ».

    Renvoie [{"id": "P1", "text": "...", "source": "open.q_projet"}, ...].
    """
    raw = [(f"open.{k}", v) for k, v in answers.get("open", {}).items()]
    raw += [(f"guided.{k}", g.get("detail", "")) for k, g in answers.get("guided", {}).items()
            if g.get("reponse") == "oui"]
    segments = []
    for source, text in raw:
        for sentence in split_sentences(text or ""):
            segments.append({"id": f"P{len(segments) + 1}", "text": sentence, "source": source})
    return segments
