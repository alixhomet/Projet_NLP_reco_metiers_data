# Reco métiers : analyse sémantique

Projet ECE ING5 Data & IA 2026-27 (Big Data & Data Science). Application Streamlit qui lit des réponses en langage naturel, les compare sémantiquement à un référentiel de compétences et de métiers, puis recommande les 3 métiers les plus proches avec une explication. Le moteur NLP fonctionne sans LLM ni API externe.

**État : phase 1.** L'application tourne de bout en bout avec un mini-référentiel d'exemple (mentionné `EXEMPLE`) et des similarités factices. Chacun remplace ensuite son module sans bloquer les autres.

**Suivi : ce qui est fait, ce qu'il reste à faire par personne et les décisions ouvertes sont dans [`docs/avancement.md`](docs/avancement.md).**

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows ; sous Linux/macOS : source .venv/bin/activate
pip install -r requirements.txt
nbstripout --install          # une fois par clone : nettoie les notebooks avant commit
```

## Lancement

```bash
streamlit run app/Accueil.py
pytest
```

## Équipe et branches

| Rôle | Branches | Fichiers dont il est propriétaire |
| --- | --- | --- |
| P1 Données | `data/*` | `data/reference/`, `src/data_loader.py`, `notebooks/01_referentiel.ipynb` |
| P2 NLP | `nlp/*` | `src/preprocess.py`, `src/embeddings.py`, `notebooks/02_nlp.ipynb` |
| P3 Scoring | `scoring/*` | `src/scoring.py`, `src/recommend.py`, `src/explain.py`, `data/test_profiles/`, `notebooks/03_scoring.ipynb`, `notebooks/04_evaluation.ipynb` |
| P4 Application | `app/*` | `app/`, `src/viz.py`, `src/storage.py`, `data/questionnaire.json`, `.streamlit/`, `README.md` |

`src/config.py`, les trois contrats d'interface et `docs/journal_difficultes.md` appartiennent à tout le monde. Workflow : `main` protégée, `dev` pour l'intégration, une branche et une PR par tâche relue par une autre personne.

---

# Conception – Reco métiers par analyse sémantique

Nov 17, 2026

## Objectif et périmètre

L'application lit des réponses en langage naturel, les compare sémantiquement à un référentiel de compétences et de métiers, puis recommande les 3 métiers les plus proches, chacun avec une explication.

- **Exigences du sujet couvertes** : questionnaire mixte (ouvert, Likert, guidé, cases à cocher), référentiel documenté, pipeline NLP (embeddings + cosinus), scoring justifié, score de couverture par bloc, top 3 expliqué, visualisations (radar, barres, carte de similarité).
- **Hors périmètre obligatoire** : LLM, RAG, chatbot, agents (bonus A à E). Le moteur doit fonctionner sans eux.
- **Livrables Boostcamp** : repo avec notebooks commentés, documentation, support de présentation. Chaque membre présente une partie (évaluation individuelle). La présentation expose aussi les difficultés rencontrées et leur résolution (docs/journal\_difficultes.md).
- **Date limite** : non indiquée dans le sujet, à confirmer en cours.

## Architecture globale

Le flux va du questionnaire au classement en six étapes, chacune portée par un module Python indépendant.

1. L'utilisateur remplit le questionnaire (page Streamlit).
2. Les réponses sont enregistrées en JSON (`data/sessions/`).
3. `preprocess` nettoie les textes libres et les découpe en segments (une phrase = un segment).
4. `embeddings` encode les segments et les compétences avec SBERT.
5. `scoring` calcule similarités, scores calibrés, couverture par bloc et par métier.
6. `recommend` classe les métiers, `explain` rédige les explications, `viz` dessine les graphiques.

| Module (`src/`) | Rôle | Entrée | Sortie |
| --- | --- | --- | --- |
| `data_loader.py` | Charge et valide les CSV du référentiel | Chemins des fichiers | DataFrames |
| `preprocess.py` | Nettoyage, segmentation | Réponses JSON | Liste de segments |
| `embeddings.py` | Encodage avec cache disque | Textes | Matrice numpy |
| `scoring.py` | Similarité, calibration, couverture | Embeddings | Dictionnaire de scores |
| `recommend.py` | Classement, filtres, garde-fous | Scores | Top N métiers |
| `explain.py` | Explications par gabarit | Scores + segments | Textes |
| `viz.py` | Radar, barres, carte de similarité | Scores | Figures |
| `storage.py` | Sauvegarde des sessions | Réponses | JSON |

## Référentiel de données

Quatre CSV dans `data/reference/` : les blocs, les compétences, les métiers, et le lien pondéré entre métiers et compétences.

| Fichier | Colonnes |
| --- | --- |
| `blocks.csv` | `block_id`, `block_name`, `description` |
| `competencies.csv` | `competency_id`, `label`, `description`, `block_id`, `keywords` |
| `jobs.csv` | `job_id`, `title`, `description`, `rome_code` (facultatif) |
| `job_competencies.csv` | `job_id`, `competency_id`, `importance` (1 à 3) |

**Volume cible (suggestion, le sujet ne fixe pas de minimum pour ce thème)** : 6 à 8 blocs, 60 à 100 compétences, 15 à 20 métiers, 8 à 15 compétences par métier.

**Blocs de départ (ceux de la maquette)** : Data Analysis, Machine Learning, NLP, Programmation, Gestion de projet, Cloud & MLOps. Deux blocs optionnels : Données & ingénierie, Communication métier.

**Règles d'écriture**

- Chaque compétence a une phrase descriptive de 8 à 20 mots (par exemple « nettoyer, normaliser et valider des données brutes avant analyse »), pas un mot seul. Hypothèse à tester : une phrase donne de meilleurs embeddings qu'un mot isolé.
- Chaque métier a une description de 2 à 3 phrases, utilisée pour l'affinité globale.
- Une compétence peut servir plusieurs métiers, avec une importance différente (3 = indispensable, 1 = utile).

**Sources** : ROME (data.gouv.fr) et e-CF 3.0, cités dans le sujet. Documenter l'origine, la date de téléchargement et chaque transformation. À vérifier avant import : le format et la licence actuels de ROME.

## Questionnaire

Six sections, pensées pour que le texte libre porte l'essentiel du signal (au moins 3 questions ouvertes).

| Section | Type de question | Usage dans l'analyse |
| --- | --- | --- |
| 1. Profil | Choix simple (études, expérience) | Contexte et filtre |
| 2. Auto-évaluation | Likert 1 à 5, un item par bloc | Poids faible dans le score de bloc (λ) |
| 3. Outils | Cases à cocher | Preuve directe, confiance moyenne |
| 4. Expérience | Questions ouvertes | Cœur de l'analyse sémantique |
| 5. Questions guidées | Oui / non + précision libre | Segments supplémentaires si précision remplie |
| 6. Préférences | Choix multiples (secteur, type de poste) | Filtre ou bonus de départage |

Les questions sont décrites dans `data/questionnaire.json` (identifiant, type, texte, options, bloc ciblé), pour que l'interface se construise à partir du fichier et qu'on puisse ajouter une question sans toucher au code.

La maquette montre les six sections sur une seule page, avec trois questions ouvertes (projet, goûts, sujet appris seul). Il n'y a pas d'étape de validation séparée : le bouton « Analyser mon profil » termine le questionnaire.

Format d'une réponse enregistrée :

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

## Pipeline NLP

Le modèle retenu par hypothèse est un SBERT multilingue, confirmé ou rejeté par l'évaluation sur les profils de test.

1. **Prétraitement léger** : normaliser les espaces et les apostrophes, découper en phrases. Ne pas lemmatiser ni retirer les mots vides pour SBERT, qui lit le texte brut. La lemmatisation sert seulement à la baseline TF-IDF.
2. **Embeddings** : `paraphrase-multilingual-MiniLM-L12-v2` si le questionnaire est en français (à vérifier sur Hugging Face et sur 20 paires de phrases du référentiel). Le modèle de l'exemple du sujet, `all-MiniLM-L6-v2`, est anglophone.
3. **Similarité** : cosinus entre chaque segment et chaque compétence, puis entre le texte complet et la description de chaque métier.
4. **Cache** : les embeddings du référentiel sont calculés une fois, stockés en `.npy`, invalidés par un hash des CSV.
5. **Validation du référentiel (optionnel)** : KMeans sur les compétences, puis comparaison des clusters avec les blocs (score de silhouette).

Pour justifier le choix du modèle, comparer trois approches sur les mêmes profils de test :

| Approche | Capte le sens | Coût | Rôle |
| --- | --- | --- | --- |
| TF-IDF + cosinus | Non (mots exacts) | Très faible | Baseline mots-clés |
| fastText, vecteurs moyennés | Partiel (mots voisins) | Fichier de vecteurs lourd | Baseline optionnelle (embeddings de mots) |
| SBERT multilingue | Oui (phrase entière) | CPU suffisant | Modèle retenu, hypothèse |

## Scoring

Le score d'un métier combine une couverture compétence par compétence et une affinité globale. Les valeurs numériques ci-dessous sont des points de départ à calibrer, pas des résultats.

**1. Similarité brute d'une compétence** : la meilleure preuve parmi tous les segments `u_k` du profil.

```latex
sim(c) = \max_k \cos\big(e(u_k),\, e(c)\big)
```

**2. Calibration.** Les cosinus SBERT se concentrent rarement au-dessus de 0.6 : on les étire entre deux seuils (départ : τ\_bas = 0.25, τ\_haut = 0.75).

```latex
s'(c) = \mathrm{clip}\left(\frac{sim(c) - \tau_{bas}}{\tau_{haut} - \tau_{bas}},\, 0,\, 1\right)
```

**3. Cases à cocher.** Un outil coché impose un plancher s'(c) ≥ κ (départ : 0.6), car une auto-déclaration est moins fiable qu'une preuve en texte libre.

**4. Score de bloc** (radar et barres) : moyenne des s'(c) du bloc, mélangée à l'auto-évaluation Likert L\_b (1 à 5), avec λ = 0.2.

```latex
B_b = (1-\lambda)\,\overline{s'}_{c \in b} + \lambda\,\frac{L_b - 1}{4}
```

**5. Couverture d'un métier j**, pondérée par l'importance w (1 à 3) de chaque compétence requise.

```latex
Couv_j = \frac{\sum_c w_{jc}\, s'(c)}{\sum_c w_{jc}}
```

**6. Score final**, avec l'affinité globale Aff\_j (similarité entre tout le texte et la description du métier, calibrée de la même façon, avec ses propres seuils si sa distribution diffère) et α = 0.70 au départ.

```latex
Score_j = \alpha\, Couv_j + (1-\alpha)\, Aff_j
```

Niveaux affichés : fort ≥ 0.65, moyen de 0.40 à 0.64, faible < 0.40. Les préférences (secteur, type de poste) filtrent ou départagent après le score, avec un bonus de 0.05 au plus (paramètre PREF\_BONUS, exposé par métier dans la sortie du moteur).

7. Couverture globale (carte « Couverture globale » de la page Résultats) : moyenne pondérée des scores de bloc, avec W\_b = 1 par défaut (blocs de même importance). Exemple de la maquette : (0.80 + 0.78 + 0.66 + 0.52 + 0.40 + 0.30) / 6 = 0.58.

```latex
Couv_{globale} = \frac{\sum_b W_b\, B_b}{\sum_b W_b}
```

**Exemple chiffré (valeurs fictives de la maquette, métier Data Scientist, 6 compétences sur le référentiel complet)**

| Compétence | Poids w | s' | w × s' |
| --- | --- | --- | --- |
| Nettoyage de données | 3 | 0.92 | 2.76 |
| Visualisation | 2 | 0.82 | 1.64 |
| Classification | 3 | 0.98 | 2.94 |
| Transformers | 1 | 0.76 | 0.76 |
| Pilotage de projet | 1 | 0.26 | 0.26 |
| Conteneurisation | 1 | 0.00 | 0.00 |

Couverture = 8.36 / 11 = 0.76. Avec une affinité de 0.64 : score = 0.70 × 0.76 + 0.30 × 0.64 = 0.72.

**Calibration des seuils (méthode proposée)** : annoter à la main une cinquantaine de paires phrase / compétence (pertinente ou non). τ\_bas = percentile 90 des similarités des paires non pertinentes. τ\_haut = médiane des similarités des paires pertinentes. Puis tester la sensibilité : α dans {0.5, 0.7, 0.9} et chaque seuil ± 0.1, et vérifier si le top 3 change.

## Recommandation et explications

Le top 3 est trié par `Score_j`. En cas d'égalité à 0.02 près, le métier qui couvre le mieux ses compétences d'importance 3 passe devant. Chaque recommandation expose : le score, la couverture, l'affinité, les deux blocs les plus forts, une ou deux lacunes (compétences d'importance ≥ 2 avec s' < 0.30) et les preuves (segment, compétence, similarité).

**Explication par gabarit, sans modèle génératif** :

```text
Recommandé parce que votre phrase « {segment} » est proche de
{compétence} (similarité {sim}). Points forts : {blocs forts}.
À renforcer : {lacunes}.
```

**Synthèse du profil** : une phrase générée de la même façon à partir des blocs forts (≥ 0.65), moyens et faibles.

**Garde-fou** : si le meilleur score est inférieur à 0.35, ou si aucune similarité ne dépasse τ\_bas, l'application affiche « profil insuffisamment documenté » et invite à compléter le questionnaire, sans recommandation forcée (seuil de départ, à calibrer).

**Contrat de sortie du moteur** (le même dictionnaire alimente l'interface, les graphiques et le notebook) :

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

## Interface Streamlit

Trois écrans sont maquettés dans le canvas « Maquette Streamlit » : Questionnaire, Résultats, Transparence. L'application suit le format multipage de Streamlit (un fichier principal, un dossier `pages/`).

| Page | Contenu | Composants Streamlit pressentis |
| --- | --- | --- |
| `Accueil.py` | Présentation, bouton de démarrage | `st.title`, `st.page_link` |
| `1_Questionnaire.py` | Six sections, progression | `st.form`, `st.select_slider`, `st.multiselect`, `st.text_area`, `st.radio`, `st.progress` |
| `2_Resultats.py` | Synthèse, top 3, radar, barres par bloc | `st.metric`, `st.columns`, `st.expander`, graphiques Plotly |
| `3_Transparence.py` | Carte de similarité, détail du calcul, paramètres | `st.dataframe` ou heatmap Plotly, `st.sidebar.slider` |
| `4_Referentiel.py` | Explorer blocs, compétences, métiers | `st.dataframe`, `st.selectbox` |

**Points techniques**

- État partagé entre pages : `st.session_state["answers"]` et `st.session_state["results"]`.
- Le modèle SBERT et les embeddings du référentiel se chargent une fois avec `st.cache_resource` et `st.cache_data`, sinon Streamlit les recharge à chaque interaction.
- Les paramètres de la page Transparence (τ\_bas, τ\_haut, α) relancent seulement `scoring` et `recommend`, pas les embeddings.
- Thème (couleurs, police) dans `.streamlit/config.toml`.
- Le questionnaire est généré à partir de `data/questionnaire.json`.
- Chaque graphique a aussi sa valeur en texte (accessibilité et lisibilité en démo).

## Évaluation

L'évaluation sert à prouver que l'analyse est sémantique et non lexicale, et à fixer les paramètres. Avec 8 à 10 profils, les résultats sont descriptifs : pas de conclusion statistique.

| Test | Ce qu'il vérifie | Mesure |
| --- | --- | --- |
| Profils de test | 8 à 10 profils écrits à la main, avec le métier attendu (2 par métier ciblé) | Top-1, top-3, rang moyen du métier attendu |
| TF-IDF contre SBERT | L'apport du sens par rapport aux mots-clés | Écart de top-3 sur les mêmes profils |
| Paraphrases | Même sens, mots différents : le classement doit tenir | Stabilité du top 3 (c'est la démo clé pour l'oral) |
| Ablations | Utilité du Likert, de l'affinité globale (α = 1), des cases à cocher | Variation du classement |
| Sensibilité | α dans {0.5, 0.7, 0.9}, seuils ± 0.1 | Le top 3 change-t-il ? |
| Profil pauvre | Texte très court | Le garde-fou se déclenche |
| Tests unitaires (`tests/`) | Identifiants uniques, clés étrangères valides, scores dans \[0, 1\], résultat déterministe | `pytest` |

Les profils de test sont versionnés dans `data/test_profiles/` au même format que les réponses du questionnaire. Ils servent aussi de jeux de démo.

## Structure du repo et conventions

```text
reco-metiers/
├── README.md
├── requirements.txt
├── .streamlit/config.toml
├── app/
│   ├── Accueil.py
│   └── pages/ (1_Questionnaire, 2_Resultats, 3_Transparence, 4_Referentiel)
├── src/
│   ├── config.py, data_loader.py, preprocess.py, embeddings.py
│   └── scoring.py, recommend.py, explain.py, viz.py, storage.py
├── data/
│   ├── reference/ (4 CSV)
│   ├── questionnaire.json
│   ├── test_profiles/
│   └── sessions/ (ignoré par Git)
├── notebooks/ (01_referentiel, 02_nlp, 03_scoring, 04_evaluation)
├── tests/
└── docs/ (conception, slides, journal_difficultes.md)
```

**Trois contrats d'interface, figés dès le jour 1** : le JSON des réponses (section Questionnaire), les quatre CSV du référentiel (section Référentiel), le dictionnaire de sortie du moteur (section Recommandation). Un changement de contrat se discute à quatre et se fait dans une PR dédiée.

**Conventions Git**

- `main` protégée (livrable), `dev` pour l'intégration, une branche par tâche (`feat/scoring`, `data/referentiel`).
- Une PR par tâche, relue par une autre personne que l'auteur, avant fusion dans `dev`.
- Messages de commit courts, au format `type: sujet` (`feat: ajoute la calibration`).
- `nbstripout` pour que les notebooks ne créent pas de conflits. Les embeddings en cache (`.cache/`) et `data/sessions/` sont dans `.gitignore`.
- `requirements.txt` avec versions épinglées. Chaque notebook se lance de haut en bas avec des commentaires à chaque étape (exigence du sujet).

## Planning et répartition

Le découpage est en phases relatives, car la date limite n'est pas connue. Jalon de la phase 1 : l'application tourne de bout en bout avec un mini-référentiel et des scores factices, en respectant les trois contrats. Ensuite chacun remplace son module sans bloquer les autres.

| Personne | Rôle | Phase 1 : socle | Phase 2 : moteur | Phase 3 : intégration | Phase 4 : preuves et livrables |
| --- | --- | --- | --- | --- | --- |
| P1 | Données | Mini-référentiel (6 blocs, 30 compétences, 6 métiers) | Référentiel complet et documenté (origine, prétraitement) | Corrections suite aux écarts détectés, validation par clustering | Section dataset du document et des slides |
| P2 | NLP | Prétraitement, SBERT et baseline TF-IDF sur le mini-référentiel, cache | Comparaison des modèles, justification du choix | Optimisation, tests unitaires | Slides analyse sémantique |
| P3 | Scoring | Formules en fonctions, profils de test écrits | Calibration des seuils, explications par gabarit | Évaluation, ablations, sensibilité | Slides scoring et résultats |
| P4 | Application | Squelette Streamlit, `questionnaire.json`, stockage, écrans avec données factices | Pages Résultats et Transparence | Branchement du moteur réel, graphiques, README | Démo, répétition, dépôt Boostcamp |

P4 fait aussi la gestion du repo (fusions dans `dev`, `main` à jour). Chacun rédige les commentaires de notebook et les slides de sa partie, puis la présente à l'oral. Chacun consigne aussi ses difficultés et leur résolution dans docs/journal\_difficultes.md au fil de l'eau (le sujet demande de les présenter). L'extension LLM (bonus) n'est ouverte qu'après la phase 4, si le reste est fini.

## Risques et points à valider

| Risque ou question | Réponse prévue |
| --- | --- |
| Date limite inconnue | La demander en cours, ajuster les phases |
| Format et licence de ROME | Vérifier sur data.gouv.fr avant import. Plan B : e-CF 3.0, ou référentiel maison documenté |
| Modèle français ou anglais | Fixer la langue au jour 1 et tester le modèle sur 20 paires du référentiel |
| Scores SBERT peu dispersés | Calibration par paires annotées, plutôt que les seuils 0.7 et 0.5 de l'exemple du sujet |
| Référentiel trop pauvre en texte | Cible de 60 compétences ou plus, avec phrases descriptives |
| Une compétence écrite en jargon que SBERT ne rapproche pas du langage courant | Ajouter des synonymes dans `keywords`, puis tester |
| Données personnelles dans le texte libre | Pas de nom demandé, stockage local, sessions ignorées par Git, message d'information sur la page Questionnaire |
| Rechargement du modèle à chaque clic | `st.cache_resource` dès la phase 1 |
| Dérive vers le bonus LLM | Ouvert seulement après la phase 4 |

Questions à trancher à quatre : langue du questionnaire, liste des 15 à 20 métiers, personne qui tient le rôle de relecteur des PR sur chaque module.
