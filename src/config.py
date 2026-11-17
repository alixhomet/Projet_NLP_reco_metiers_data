"""Configuration partagée : chemins et paramètres de scoring.

Fichier commun aux quatre membres : toute modification passe par une PR dédiée.
Les valeurs numériques sont des points de départ à calibrer, pas des résultats.
"""
from pathlib import Path

# --- Chemins -----------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
REFERENCE_DIR = ROOT / "data" / "reference"
QUESTIONNAIRE_PATH = ROOT / "data" / "questionnaire.json"
SESSIONS_DIR = ROOT / "data" / "sessions"      # ignoré par Git
TEST_PROFILES_DIR = ROOT / "data" / "test_profiles"
CACHE_DIR = ROOT / ".cache"                    # ignoré par Git

# --- Modèle d'embeddings (hypothèse, à tester sur le référentiel avant de le figer)
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

# --- Paramètres de scoring (docs/conception.md, section Scoring) -------------
TAU_LOW = 0.25         # τ_bas : en dessous, la similarité compte pour 0
TAU_HIGH = 0.75        # τ_haut : au dessus, la similarité compte pour 1
ALPHA = 0.70           # poids de la couverture dans le score final
LAMBDA = 0.20          # poids de l'auto-évaluation Likert dans le score de bloc
KAPPA = 0.60           # plancher de s'(c) pour un outil coché
PREF_BONUS = 0.05      # bonus maximal lié aux préférences de poste
GUARD_THRESHOLD = 0.35 # garde-fou : meilleur score en dessous => pas de recommandation

# --- Autres seuils de la conception ------------------------------------------
LEVEL_STRONG = 0.65    # niveau « fort » à partir de ce score
LEVEL_MEDIUM = 0.40    # niveau « moyen » à partir de ce score, « faible » en dessous
GAP_MIN_IMPORTANCE = 2 # une lacune est une compétence d'importance >= 2 ...
GAP_THRESHOLD = 0.30   # ... avec s' < 0.30
TIE_MARGIN = 0.02      # égalité de classement à 0.02 près
TOP_N = 3

# Paramètres modifiables à l'exécution (page Transparence) : clé -> valeur par défaut.
DEFAULT_PARAMS = {
    "tau_low": TAU_LOW,
    "tau_high": TAU_HIGH,
    "alpha": ALPHA,
    "lambda_": LAMBDA,
    "kappa": KAPPA,
    "pref_bonus": PREF_BONUS,
    "guard_threshold": GUARD_THRESHOLD,
}

# Phase 1 : les similarités sont factices (pas de SBERT). P3 passe ce drapeau à False
# quand le vrai moteur est branché ; les pages affichent un bandeau tant qu'il vaut True.
PHASE1_FAKE_SCORES = True
