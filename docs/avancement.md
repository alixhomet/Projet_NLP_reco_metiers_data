# Avancement du projet

Fichier de suivi commun : mettez-le à jour dans la PR de votre tâche (cochez, ajoutez une ligne datée dans l'historique). Les difficultés vont dans `journal_difficultes.md`.

**État au 2026-11-18 : phase 1 terminée.** L'application tourne de bout en bout (questionnaire, résultats, transparence, référentiel) avec le mini-référentiel d'exemple et des **similarités factices**. Le classement affiché n'a aucune valeur réelle (bandeau orange dans l'app, drapeau `PHASE1_FAKE_SCORES` dans `src/config.py`).

**2026-11-22 : référentiel réel livré par P1 (branche `data/referentiel`).** `data/reference/` contient maintenant le référentiel construit à partir du ROME 4.0 : 6 blocs, 70 compétences, 14 métiers, 272 liens. Plus de mention `EXEMPLE` dans le référentiel. `pytest` vert (15 tests) et l'appli tourne. Les similarités restent factices tant que P2 et P3 n'ont pas branché SBERT.

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
- [x] ROME 4.0 version 62 (publiée le 19/10/2026) téléchargé sur data.gouv.fr le 22/11/2026, rangé dans `data/raw/` (ignoré par Git, 38 Mo). Licence Ouverte (à citer dans le notebook).
- [x] Extraction des 14 métiers data par `scripts/extraire_rome.py` vers `data/interim/` : `rome_jobs.csv` (14 métiers), `rome_competences.csv` (327 compétences), `rome_savoirs.csv` (149 savoirs, diplômes retirés), `rome_liens.csv` (695 liens).
- [x] Référentiel dans `data/reference/`, construit par `scripts/construire_referentiel.py` :
  - 6 blocs choisis à partir des données (regroupement des 14 métiers selon leurs compétences ROME, plus un bloc transverse) : B01 Analyse & statistiques, B02 IA & Machine Learning, B03 Ingénierie & bases de données, B04 BI & aide à la décision, B05 Gouvernance & conformité, B06 Pilotage & communication.
  - 70 compétences : les ~280 savoir-faire ROME regroupés par sens et reformulés (descriptions de 8 à 20 mots, mots-clés pour les cases à cocher). Correspondance traçable dans `data/curation/competences_retenues.csv` (colonne `codes_rome`). 4 compétences trop vagues écartées.
  - 14 métiers (`J01` à `J14`) avec leur définition ROME et leur `rome_code`.
  - 272 liens métier-compétence. Importance : 3 si la compétence est dans un bloc cœur du métier, 1 si elle est transverse (B06) hors cœur, 2 sinon.
- [x] Tests adaptés (`tests/test_reference.py`) : volumes du vrai référentiel, chaque bloc et chaque métier utilisé, plus de mention `EXEMPLE`.
- [ ] Relire la curation (`data/curation/competences_retenues.csv`), corriger si besoin et relancer le script.
- [ ] 11 à 28 compétences par métier, au-dessus de la cible de 8 à 15 de la conception : à réduire seulement si P3 voit un problème au scoring.
- [ ] Documenter l'origine (ROME 4.0, e-CF 3.0 si utilisé) et chaque transformation dans le notebook.
- [ ] `notebooks/01_referentiel.ipynb` (commenté), validation par clustering (KMeans, silhouette).
- [ ] Proposer des colonnes secteur / type de poste si l'équipe les retient (voir décisions).

### P2 NLP (`nlp/embeddings`)
- [ ] Vérifier que `paraphrase-multilingual-MiniLM-L12-v2` existe, le tester sur 20 paires du référentiel, puis figer le choix. Vérifier l'installation de torch / sentence-transformers sur Python 3.14.
- [ ] Implémenter `get_model`, `encode`, `encode_reference` (cache `.npy` dans `.cache/`, invalidé par `reference_hash`).
- [ ] Baseline TF-IDF (et fastText si le temps le permet), comparaison des modèles et justification.
- [ ] `notebooks/02_nlp.ipynb`, ajout des dépendances à `requirements.txt` (PR dédiée).

### P3 Scoring (`scoring/engine`)
- [ ] Remplacer `_similarities` et `_affinity_raw` par le cosinus sur les embeddings de P2, puis passer `PHASE1_FAKE_SCORES` à `False` (PR sur `config.py`).
- [ ] Écrire 8 à 10 profils de test dans `data/test_profiles/` (même format que les sessions), à partir des 14 métiers de `data/reference/jobs.csv` (décision 9).
- [ ] Calibrer τ_bas, τ_haut (paires annotées), α, κ, λ, seuil du garde-fou.
- [ ] Évaluation : top-1 / top-3, TF-IDF contre SBERT, paraphrases, ablations, sensibilité, profil pauvre. `notebooks/03_scoring.ipynb` et `04_evaluation.ipynb`.
- [ ] Implémenter `pref_bonus` une fois le critère décidé.

### P4 Application (`app/streamlit`)
- [ ] Adapter `data/questionnaire.json` aux 6 nouveaux blocs : les items Likert pointent encore sur les anciens (`nlp` → B03, `python` → B04, `gestion_projet` → B05, `cloud` → B06), ce qui ne plante pas mais donne un sens faux. Revoir aussi les questions guidées (`tokenisation` → B03) et les outils à cocher (mots-clés disponibles dans `competencies.csv`).
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
8. **Métiers hors ROME** : le ROME 4.0 (v62) ne contient ni Ingénieur NLP ni Ingénieur MLOps (ils sont fondus dans M1889 « Ingénieur IA »). Les ajouter à la main (description + compétences, documentés dans le notebook 01) ou s'en tenir aux 14 métiers ROME ? Conséquence : sans eux, les blocs « NLP » et « Cloud & MLOps » ne mènent à aucun métier et doivent être remplacés par des blocs adaptés aux 14 métiers (BI, bases de données, gouvernance…), ce qui change aussi les items Likert (décision 5).
9. **Liste des 14 métiers ROME retenus** (voir `data/reference/jobs.csv`) : Data Analyst, Data Scientist, Data Engineer, Ingénieur IA / Machine Learning, Spécialiste IA embarquée, Ingénieur statisticien, Biostatisticien, Développeur BI, Analyste BI, Consultant BI, Architecte bases de données, Administrateur bases de données, Chief Data Officer, DPO. À valider avant que P3 écrive les profils de test.
10. **Blocs** : les 6 blocs d'exemple (Data Analysis, ML, NLP, Programmation, Gestion de projet, Cloud & MLOps) sont remplacés par 6 blocs issus des données ROME (voir P1). Programmation et cloud ne sont plus des blocs : les outils (Python, SQL, Docker…) sont des mots-clés des compétences. Si l'équipe ajoute Ingénieur NLP ou MLOps (décision 8), un bloc NLP pourra être ajouté.

## Lancer et tester

```bash
pip install -r requirements.txt
nbstripout --install        # une fois par clone
streamlit run app/Accueil.py
pytest
```

Extraction ROME (P1, nécessite le ZIP du ROME dézippé dans `data/raw/`) :

```bash
python scripts/extraire_rome.py            # ROME brut -> data/interim/
python scripts/construire_referentiel.py   # data/interim/ + curation -> data/reference/
```

## Historique

| Date | Changement | Auteur |
| --- | --- | --- |
| 2026-11-17 | Squelette phase 1 (voir ci-dessus) | P4 avec Claude |
| 2026-11-18 | `Conception.md` renommé en `conception.md` | P4 avec Claude |
| 2026-11-22 | Extraction des 14 métiers data du ROME 4.0 v62 (`scripts/extraire_rome.py`, `data/interim/`), décisions 8 et 9 ajoutées | P1 |
| 2026-11-22 | Référentiel réel dans `data/reference/` (6 blocs, 70 compétences, 14 métiers, 272 liens) via `scripts/construire_referentiel.py` et `data/curation/`, tests adaptés, décision 10 ajoutée | P1 |
