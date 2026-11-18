# Avancement du projet

Fichier de suivi commun : mettez-le à jour dans la PR de votre tâche (cochez, ajoutez une ligne datée dans l'historique). Les difficultés vont dans `journal_difficultes.md`.

**État au 2026-11-18 : phase 1 terminée.** L'application tourne de bout en bout (questionnaire, résultats, transparence, référentiel) avec le mini-référentiel d'exemple et des **similarités factices**. Le classement affiché n'a aucune valeur réelle (bandeau orange dans l'app, drapeau `PHASE1_FAKE_SCORES` dans `src/config.py`).

## Ce qui a été fait (phase 1, squelette)

- Arborescence conforme à la conception, `.gitignore`, `.gitattributes` (nbstripout), `.streamlit/config.toml`, `pytest.ini`, `requirements.txt` épinglé (Python 3.14.3).
- Référentiel d'exemple dans `data/reference/` : 6 blocs, 30 compétences, 6 métiers, 65 liens métier-compétence. Chaque description commence par `EXEMPLE`.
- `data/questionnaire.json` : 6 sections, 3 questions ouvertes, 3 questions guidées, 6 items Likert (un par bloc). Toutes les questions sont marquées `EXEMPLE`.
- `src/` : un module par ligne du tableau de la conception, avec docstrings et commentaires.
  - Réel : chargement et validation du référentiel, segmentation en phrases, stockage des sessions, calibration `s'(c)`, plancher κ des outils cochés, score de bloc avec Likert (λ), couverture par métier, couverture globale (moyenne pondérée des blocs), départage à 0.02 près, lacunes, preuves, garde-fou, explications par gabarit, graphiques Plotly.
  - Factice : les similarités segment-compétence et texte-métier (`scoring._similarities` et `scoring._affinity_raw`, hash déterministe).
  - Squelette : `embeddings.py` (seul `reference_hash` est réel).
- Application Streamlit : `Accueil` et 4 pages. Questionnaire généré depuis le JSON, sauvegarde en `data/sessions/`, résultats (top 3, radar, barres, valeurs en texte), transparence (carte de similarité, paramètres τ_bas, τ_haut, α), référentiel.
- `tests/` : 14 tests `pytest` (identifiants, clés étrangères, volumes, bornes [0, 1], forme du contrat, déterminisme, garde-fou).
- Vérification : `pytest` vert, parcours complet testé dans un navigateur sans erreur console.
- Branches créées : `main`, `dev`, `data/referentiel`, `nlp/embeddings`, `scoring/engine`, `app/streamlit`.

## Ce qu'il reste à faire

### P1 Données (`data/referentiel`)
- [ ] Référentiel complet et documenté : 60 à 100 compétences, 15 à 20 métiers, 8 à 15 compétences par métier. Retirer les mentions `EXEMPLE`.
- [ ] Documenter l'origine (ROME, e-CF 3.0), la date de téléchargement et chaque transformation. Vérifier le format et la licence de ROME.
- [ ] `notebooks/01_referentiel.ipynb` (commenté), validation par clustering (KMeans, silhouette).
- [ ] Proposer des colonnes secteur / type de poste si l'équipe les retient (voir décisions).

### P2 NLP (`nlp/embeddings`)
- [ ] Vérifier que `paraphrase-multilingual-MiniLM-L12-v2` existe, le tester sur 20 paires du référentiel, puis figer le choix. Vérifier l'installation de torch / sentence-transformers sur Python 3.14.
- [ ] Implémenter `get_model`, `encode`, `encode_reference` (cache `.npy` dans `.cache/`, invalidé par `reference_hash`).
- [ ] Baseline TF-IDF (et fastText si le temps le permet), comparaison des modèles et justification.
- [ ] `notebooks/02_nlp.ipynb`, ajout des dépendances à `requirements.txt` (PR dédiée).

### P3 Scoring (`scoring/engine`)
- [ ] Remplacer `_similarities` et `_affinity_raw` par le cosinus sur les embeddings de P2, puis passer `PHASE1_FAKE_SCORES` à `False` (PR sur `config.py`).
- [ ] Écrire 8 à 10 profils de test dans `data/test_profiles/` (même format que les sessions).
- [ ] Calibrer τ_bas, τ_haut (paires annotées), α, κ, λ, seuil du garde-fou.
- [ ] Évaluation : top-1 / top-3, TF-IDF contre SBERT, paraphrases, ablations, sensibilité, profil pauvre. `notebooks/03_scoring.ipynb` et `04_evaluation.ipynb`.
- [ ] Implémenter `pref_bonus` une fois le critère décidé.

### P4 Application (`app/streamlit`)
- [ ] Brancher le moteur réel (modèle en `st.cache_resource`, embeddings en `st.cache_data`).
- [ ] Finaliser les questions avec l'équipe, polir les pages Résultats et Transparence.
- [ ] Gestion du repo : protéger `main`, fusions dans `dev`, `main` à jour.
- [ ] Démo, répétition, dépôt Boostcamp, slides de la partie application.

### Tous
- [ ] Journal des difficultés au fil de l'eau (`journal_difficultes.md`).
- [ ] Notebooks commentés à chaque étape, slides de sa partie, présentation orale individuelle.
- [ ] Confirmer la date limite auprès de l'enseignante et ajuster les phases.

## Décisions à prendre à quatre

1. **Langue du questionnaire** et liste des 15 à 20 métiers.
2. **Relecteur des PR** de chaque module.
3. **Préférences de poste** : `jobs.csv` n'a ni secteur ni type de poste. Quel critère de correspondance pour `pref_bonus` ? Le bonus est-il inclus dans `score` ? (aujourd'hui : exclu du `score`, ajouté pour le classement, valeur 0.0)
4. **Garde-fou** : le contrat de sortie n'a pas de champ « insuffisant ». Aujourd'hui `job_ranking` est vide et `profile_summary` porte le message. Ajouter un champ (PR dédiée) ou garder ainsi ?
5. **Likert** : 6 items, un par bloc, dont `cloud` (l'exemple du contrat n'en avait que 5).
6. **Fichiers hors structure** ajoutés pour que tout tourne : `app/ui.py`, `pytest.ini`, `.gitattributes`, `src/__init__.py`. À garder ?
7. **Questionnaire** : widgets libres plutôt que `st.form` (progression en direct, précision affichée seulement si « oui »).

## Lancer et tester

```bash
pip install -r requirements.txt
nbstripout --install        # une fois par clone
streamlit run app/Accueil.py
pytest
```

## Historique

| Date | Changement | Auteur |
| --- | --- | --- |
| 2026-11-17 | Squelette phase 1 (voir ci-dessus) | P4 avec Claude |
| 2026-11-18 | `Conception.md` renommé en `conception.md` | P4 avec Claude |
