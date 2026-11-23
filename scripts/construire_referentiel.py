# Construction du référentiel de l'application (data/reference/) à partir du ROME
#
# Entrées :
#   - data/interim/rome_jobs.csv et rome_liens.csv   (produits par extraire_rome.py)
#   - data/curation/competences_retenues.csv          (table écrite à la main)
# Sorties : les 4 CSV de data/reference/ (blocks, competencies, jobs, job_competencies)
#
# Lancement depuis la racine du projet : python scripts/construire_referentiel.py

import pandas as pd

DOSSIER_INTERIM = "data/interim"
DOSSIER_REFERENCE = "data/reference"
FICHIER_CURATION = "data/curation/competences_retenues.csv"


# ---------- 1. Les blocs ----------
# Choisis à partir des données : les 14 métiers se regroupent en 5 familles quand on
# compare leurs compétences ROME (clustering), plus un bloc pour les compétences transverses.
blocs = pd.DataFrame([
    ("B01", "Analyse & statistiques",
     "Explorer, modéliser et interpréter des données avec des méthodes statistiques pour éclairer une décision."),
    ("B02", "IA & Machine Learning",
     "Concevoir, évaluer, déployer et maintenir des modèles d'apprentissage automatique et des systèmes d'IA."),
    ("B03", "Ingénierie & bases de données",
     "Concevoir, administrer, sécuriser et faire circuler les données dans des bases et des systèmes fiables."),
    ("B04", "BI & aide à la décision",
     "Construire des tableaux de bord, des reportings et des outils décisionnels pour piloter l'activité."),
    ("B05", "Gouvernance & conformité",
     "Encadrer l'usage des données : RGPD, confidentialité, sécurité, stratégie et qualité à l'échelle de l'organisation."),
    ("B06", "Pilotage & communication",
     "Mener un projet, collaborer avec les équipes, comprendre les besoins et présenter des résultats clairement."),
], columns=["block_id", "block_name", "description"])


# ---------- 2. Les compétences ----------
# Le ROME formule une même idée différemment pour chaque métier (ex. « Analyser des données
# pour identifier des tendances » et « Analyser, exploiter, structurer des données »).
# La table de curation regroupe ces formulations en une seule compétence, rangée dans un
# bloc, avec une description de 8 à 20 mots et des mots-clés (outils, synonymes).
curation = pd.read_csv(FICHIER_CURATION, dtype=str, keep_default_na=False)
competences = curation[["competency_id", "label", "description", "block_id", "keywords"]]


# ---------- 3. Les métiers ----------
rome_jobs = pd.read_csv(f"{DOSSIER_INTERIM}/rome_jobs.csv", dtype=str, keep_default_na=False)
metiers = pd.DataFrame({
    "job_id": [f"J{i:02d}" for i in range(1, len(rome_jobs) + 1)],
    "title": rome_jobs["title"],
    "description": rome_jobs["description"],   # définition officielle du ROME
    "rome_code": rome_jobs["code_rome"],
})
code_vers_job = dict(zip(metiers["rome_code"], metiers["job_id"]))


# ---------- 4. Les liens métier -> compétence ----------
# Un métier est lié à une compétence retenue si au moins une des compétences ROME
# regroupées dedans fait partie de sa fiche ROME.
rome_liens = pd.read_csv(f"{DOSSIER_INTERIM}/rome_liens.csv", dtype=str)

# Table « code ROME de la compétence -> compétence retenue »
correspondance = {}
for ligne in curation.itertuples():
    for code in ligne.codes_rome.split(";"):
        correspondance[code] = ligne.competency_id

rome_liens["competency_id"] = rome_liens["code_ogr"].map(correspondance)
rome_liens = rome_liens.dropna(subset=["competency_id"])  # savoirs et compétences écartées
liens = rome_liens[["code_rome", "competency_id"]].drop_duplicates()
liens["job_id"] = liens["code_rome"].map(code_vers_job)

# Importance (le ROME ne la donne pas, règle à justifier dans le notebook) :
#   3 = la compétence est dans un bloc « cœur » du métier
#   1 = compétence transverse (bloc Pilotage & communication) hors cœur de métier
#   2 = tous les autres cas
BLOCS_COEUR = {
    "M1419": ["B01", "B04"],  # Data Analyst
    "M1405": ["B01", "B02"],  # Data Scientist
    "M1811": ["B03"],         # Data Engineer
    "M1889": ["B02"],         # Ingénieur IA / Machine Learning
    "M1873": ["B02"],         # Spécialiste IA embarquée
    "M1414": ["B01"],         # Ingénieur statisticien
    "K2403": ["B01"],         # Biostatisticien
    "M1824": ["B04", "B03"],  # Développeur BI
    "M1851": ["B04"],         # Analyste BI
    "M1872": ["B04"],         # Consultant BI
    "M1868": ["B03"],         # Architecte bases de données
    "M1894": ["B03"],         # Administrateur bases de données
    "M1423": ["B05", "B06"],  # Chief Data Officer
    "K1906": ["B05"],         # DPO
}
bloc_de = dict(zip(competences["competency_id"], competences["block_id"]))


def importance(ligne):
    bloc = bloc_de[ligne["competency_id"]]
    if bloc in BLOCS_COEUR[ligne["code_rome"]]:
        return 3
    if bloc == "B06":
        return 1
    return 2


liens["importance"] = liens.apply(importance, axis=1)
liens = liens[["job_id", "competency_id", "importance"]].sort_values(["job_id", "competency_id"])


# ---------- 5. Enregistrement ----------
blocs.to_csv(f"{DOSSIER_REFERENCE}/blocks.csv", index=False)
competences.to_csv(f"{DOSSIER_REFERENCE}/competencies.csv", index=False)
metiers.to_csv(f"{DOSSIER_REFERENCE}/jobs.csv", index=False)
liens.to_csv(f"{DOSSIER_REFERENCE}/job_competencies.csv", index=False)

print(f"{len(blocs)} blocs, {len(competences)} compétences, {len(metiers)} métiers, {len(liens)} liens")
print()
print("Compétences par bloc :")
print(competences["block_id"].map(dict(zip(blocs["block_id"], blocs["block_name"]))).value_counts().to_string())
print()
print("Compétences par métier (et combien d'importance 3) :")
resume = liens.groupby("job_id").agg(competences=("competency_id", "count"),
                                     importance_3=("importance", lambda s: (s == 3).sum()))
resume.index = resume.index.map(dict(zip(metiers["job_id"], metiers["title"])))
print(resume.to_string())
