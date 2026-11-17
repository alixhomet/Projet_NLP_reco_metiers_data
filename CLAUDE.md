# CLAUDE.md — Reco métiers (analyse sémantique)

Projet ECE ING5 Data & IA 2026-27 (Big Data & Data Science). Application Streamlit qui lit des réponses en langage naturel, les compare sémantiquement à un référentiel de compétences et de métiers, puis recommande les 3 métiers les plus proches avec une explication.

**Lis `docs/conception.md` (aussi dans `README.md`) avant toute modification.** C'est la source de vérité : formules, schémas, contrats, planning. En cas de conflit entre ce fichier et la conception, signale-le au lieu de choisir.

## Équipe et propriété des fichiers

Quatre personnes, un rôle chacune. Chacun ne modifie que ses fichiers. Un changement dans les fichiers d'un autre passe par une PR relue par son propriétaire.

| Rôle | Branches | Fichiers dont il est propriétaire |
| --- | --- | --- |
| P1 Données | `data/*` | `data/reference/`, `src/data_loader.py`, `notebooks/01_referentiel.ipynb` |
| P2 NLP | `nlp/*` | `src/preprocess.py`, `src/embeddings.py`, `notebooks/02_nlp.ipynb` |
| P3 Scoring | `scoring/*` | `src/scoring.py`, `src/recommend.py`, `src/explain.py`, `data/test_profiles/`, `notebooks/03_scoring.ipynb`, `notebooks/04_evaluation.ipynb` |
| P4 Application | `app/*` | `app/`, `src/viz.py`, `src/storage.py`, `data/questionnaire.json`, `.streamlit/`, `README.md` |

`src/config.py` et les trois contrats ci-dessous appartiennent à tout le monde : toute modification passe par une PR dédiée, annoncée aux quatre.

`docs/journal_difficultes.md` appartient aussi à tout le monde : chacun y consigne au fil de l'eau ses difficultés et comment il les a résolues, car le sujet demande de les présenter à l'oral (une ligne par difficulté : date, problème, solution, auteur).

## Commandes

```bash
pip install -r requirements.txt
streamlit run app/Accueil.py
pytest
```

## Trois contrats d'interface (figés)

1. **Réponses du questionnaire** : un JSON par session dans `data/sessions/` (ignoré par Git).

```json
{
  "session_id": "2026-11-17T10-30-00_a1b2",
  "profile": {"niveau": "Bac+5", "experience_annees": 1},
  "likert": {"python": 4, "stats": 3, "ml": 3, "nlp": 2, "gestion_projet": 3},
  "tools": ["Python", "SQL", "pandas"],
  "open": {"q_projet": "...", "q_gout": "...", "q_appris": "..."},
  "guided": {"tokenisation": {"reponse": "oui", "detail": "..."}},
  "preferences": {"secteur": ["télécom"]}
}
```

2. **Référentiel** : quatre CSV dans `data/reference/`.
   - `blocks.csv` : `block_id`, `block_name`, `description`
   - `competencies.csv` : `competency_id`, `label`, `description`, `block_id`, `keywords`
   - `jobs.csv` : `job_id`, `title`, `description`, `rome_code` (facultatif)
   - `job_competencies.csv` : `job_id`, `competency_id`, `importance` (1 à 3)

3. **Sortie du moteur** : un dictionnaire, le même pour l'app, les graphiques et les notebooks.

```json
{
  "profile_summary": "Profil orienté analyse de données ...",
  "global_coverage": 0.58,
  "block_scores": {"Data Analysis": 0.78, "Machine Learning": 0.66},
  "job_ranking": [
    {
      "job_id": "J03", "title": "Data Scientist",
      "score": 0.72, "coverage": 0.76, "affinity": 0.64, "pref_bonus": 0.0,
      "strengths": ["Data Analysis", "Machine Learning"],
      "gaps": ["C12"],
      "evidence": [{"segment": "...", "competency": "C01", "sim": 0.71}]
    }
  ],
  "similarity_matrix": {"rows": ["P1"], "cols": ["C01"], "values": [[0.71]]}
}
```

## Règles de code

- Le moteur NLP doit fonctionner sans aucun LLM ni API externe. Les bonus génératifs (LLM, RAG, agents) ne sont ajoutés qu'après la phase 4, dans un module séparé, et ne remplacent rien.
- Paramètres de scoring dans `src/config.py`, jamais en dur dans le code : `TAU_LOW=0.25`, `TAU_HIGH=0.75`, `ALPHA=0.70`, `LAMBDA=0.20`, `KAPPA=0.60`, `PREF_BONUS=0.05`, seuil de garde-fou `0.35`. Ce sont des points de départ à calibrer, pas des résultats.
- Couverture globale (`global_coverage`) : moyenne pondérée des scores de bloc, `Σ W_b·B_b / Σ W_b`, avec `W_b = 1` par défaut. Elle alimente la carte « Couverture globale » de la page Résultats.
- Préférences de poste (secteur, type de poste) : appliquées après le calcul du score, en filtre ou en bonus de départage d'au plus `PREF_BONUS`. Le bonus de chaque métier est renvoyé dans `pref_bonus` pour rester explicable.
- Questionnaire : six sections (profil, auto-évaluation Likert, outils, expérience en questions ouvertes, questions guidées, préférences), au moins trois questions ouvertes. Pas d'étape de validation séparée. Les questions de `data/questionnaire.json` sont provisoires (marquées `EXEMPLE`) : l'équipe les décide ensemble.
- Modèle d'embeddings dans `src/config.py` : `paraphrase-multilingual-MiniLM-L12-v2` par hypothèse (vérifier qu'il existe sous ce nom et le tester sur le référentiel avant de le figer).
- Commentaires internes à chaque étape du code et des notebooks (exigence du sujet), en français.
- Streamlit : modèle et embeddings chargés avec `st.cache_resource` et `st.cache_data`. État partagé dans `st.session_state`.
- Embeddings du référentiel en cache dans `.cache/` (ignoré par Git), invalidés par un hash des CSV.
- Ne jamais inventer de données de référentiel présentées comme réelles. Les données d'exemple portent la mention `EXEMPLE` dans leur description tant que P1 n'a pas livré le vrai référentiel.
- Tests unitaires dans `tests/` : identifiants uniques, clés étrangères valides, scores dans [0, 1], résultat déterministe.

## Git

- `main` protégée (livrable), `dev` pour l'intégration, une branche par tâche (`feat/scoring`, `data/referentiel`).
- Une PR par tâche, relue par une autre personne que l'auteur, avant fusion dans `dev`.
- Commits courts au format `type: sujet` (`feat: ajoute la calibration`).
- `nbstripout` installé pour les notebooks. Ne jamais committer `data/sessions/`, `.cache/`, ni de secret.
- Ne jamais faire de push forcé sur `main` ou `dev`.

## Définition de « phase 1 terminée »

L'application tourne de bout en bout (questionnaire, résultats, transparence) avec le mini-référentiel d'exemple et des scores factices, en respectant les trois contrats. Ensuite chacun remplace son module sans bloquer les autres.

## Livrables Boostcamp

Dépôt du repo avec notebooks commentés et documentation, plus un support de présentation. Chaque membre présente une partie à l'oral (évaluation individuelle), en mettant en évidence l'analyse sémantique et les difficultés rencontrées (voir `docs/journal_difficultes.md`). Date limite : à confirmer auprès de l'enseignante.
