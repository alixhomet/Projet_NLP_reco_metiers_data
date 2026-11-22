# Extraction des métiers data du ROME 4.0 (France Travail, data.gouv.fr, Licence Ouverte)
#
# Entrée  : les CSV du ROME dézippés dans data/raw/
# Sortie  : 4 fichiers dans data/interim/
#   - rome_jobs.csv         : les métiers et leur description
#   - rome_competences.csv  : les compétences de ces métiers
#   - rome_savoirs.csv      : les savoirs (Python, SQL, BI...)
#   - rome_liens.csv        : quel métier utilise quelle compétence ou quel savoir
#
# Lancement depuis la racine du projet : python scripts/extraire_rome.py

import os
import pandas as pd

DOSSIER_BRUT = "data/raw"
DOSSIER_SORTIE = "data/interim"
VERSION = "v462"  # numéro dans le nom des fichiers du ROME

# Les 14 métiers data qu'on garde : code ROME -> nom affiché dans l'appli
METIERS = {
    "M1419": "Data Analyst",
    "M1405": "Data Scientist",
    "M1811": "Data Engineer",
    "M1889": "Ingénieur IA / Machine Learning",
    "M1873": "Spécialiste IA embarquée",
    "M1414": "Ingénieur statisticien",
    "K2403": "Biostatisticien",
    "M1824": "Développeur BI",
    "M1851": "Analyste BI",
    "M1872": "Consultant BI",
    "M1868": "Architecte bases de données",
    "M1894": "Administrateur bases de données",
    "M1423": "Chief Data Officer",
    "K1906": "Délégué à la protection des données (DPO)",
}
codes = list(METIERS.keys())


def lire(nom):
    """Lit un fichier du ROME, par exemple lire("texte")."""
    chemin = f"{DOSSIER_BRUT}/unix_{nom}_{VERSION}_utf8.csv"
    return pd.read_csv(chemin, dtype=str, keep_default_na=False)


def nettoyer(texte):
    """Le ROME écrit d''apprentissage au lieu de d'apprentissage : on corrige."""
    texte = texte.replace("''", "'")
    return " ".join(texte.split())  # enlève les espaces en trop


os.makedirs(DOSSIER_SORTIE, exist_ok=True)


# ---------- 1. Les métiers ----------
rome = lire("referentiel_code_rome")
textes = lire("texte")

# On garde seulement nos 14 métiers
textes = textes[textes["code_rome"].isin(codes)]

# Le ROME stocke une phrase par ligne, numérotée : on les trie par métier puis par numéro
# (converti en nombre, sinon "10" passerait avant "2"). Le recollage des phrases se fait dans la boucle.
textes["position_phrase"] = textes["position_phrase"].astype(int)
textes = textes.sort_values(["code_rome", "position_phrase"])

lignes = []
for code in codes:
    intitule = rome.loc[rome["code_rome"] == code, "libelle_rome"].iloc[0]
    textes_metier = textes[textes["code_rome"] == code]
    definition = textes_metier[textes_metier["libelle_type_texte"] == "definition"]
    acces = textes_metier[textes_metier["libelle_type_texte"] == "acces_metier"]
    lignes.append({
        "code_rome": code,
        "title": METIERS[code],
        "libelle_rome": intitule,
        "acces_metier": nettoyer(" ".join(acces["libelle_texte"])),
        "description": nettoyer(" ".join(definition["libelle_texte"])),
    })
metiers = pd.DataFrame(lignes)


# ---------- 2. Les liens métier -> compétence / savoir ----------
liens = lire("liens_rome_referentiels")

# On garde nos 14 métiers et seulement le bloc 5 du ROME (« Compétences »)
liens = liens[liens["code_rome"].isin(codes)]
liens = liens[liens["code_compo_bloc"] == "5"]

# Dans ce bloc, la rubrique dit de quel type d'élément il s'agit ( savoir, savoir-faire ou savoir-être )
types = {"1": "Savoir-faire", "2": "Savoir-être", "3": "Savoir"}
liens["type"] = liens["code_rubrique"].map(types)
liens = liens[["code_rome", "code_ogr", "type"]].drop_duplicates()

# Pour chaque élément : combien de nos métiers l'utilisent, et lesquels
nb_metiers = liens.groupby("code_ogr")["code_rome"].nunique().rename("nb_metiers")
liste_metiers = (liens.groupby("code_ogr")["code_rome"]
                 .apply(lambda c: ";".join(sorted(c))).rename("metiers"))


# ---------- 3. Les compétences ----------
toutes_competences = lire("referentiel_competence")
arborescence = lire("arborescence_competences")

codes_competences = liens.loc[liens["type"] != "Savoir", "code_ogr"]
competences = toutes_competences[toutes_competences["code_ogr"].isin(codes_competences)]
competences = competences[["code_ogr", "libelle_competence", "definition",
                           "cat_comp", "sous_cat_comp"]]

# On ajoute le domaine et la macro-compétence donnés par l'arborescence du ROME
arborescence = arborescence[["code_ogr_competence", "domaine_competence", "enjeu",
                             "objectif", "libelle_macro_competence"]]
arborescence = arborescence.drop_duplicates("code_ogr_competence")
arborescence = arborescence.rename(columns={"code_ogr_competence": "code_ogr"})
competences = competences.merge(arborescence, on="code_ogr", how="left")

# On ajoute le nombre de métiers, la liste des métiers et le type
competences = competences.merge(nb_metiers, on="code_ogr")
competences = competences.merge(liste_metiers, on="code_ogr")
type_par_code = liens[["code_ogr", "type"]].drop_duplicates("code_ogr")
competences = competences.merge(type_par_code, on="code_ogr")

competences["libelle_competence"] = competences["libelle_competence"].apply(nettoyer)
competences["definition"] = competences["definition"].apply(nettoyer)

# Les plus partagées en premier
competences = competences.sort_values(["nb_metiers", "libelle_competence"],
                                      ascending=[False, True])


# ---------- 4. Les savoirs ----------
tous_savoirs = lire("referentiel_savoir")

codes_savoirs = liens.loc[liens["type"] == "Savoir", "code_ogr"]
savoirs = tous_savoirs[tous_savoirs["code_ogr_savoir"].isin(codes_savoirs)]
savoirs = savoirs[["code_ogr_savoir", "libelle_savoir", "categorie_savoir",
                   "sous_categorie_savoir"]]
savoirs = savoirs.rename(columns={"code_ogr_savoir": "code_ogr"})

# Les diplômes (« Ingénieur diplômé de l'école... ») ne sont pas des compétences
savoirs = savoirs[savoirs["categorie_savoir"] != "Certifications et habilitations"]

savoirs = savoirs.merge(nb_metiers, on="code_ogr")
savoirs = savoirs.merge(liste_metiers, on="code_ogr")
savoirs = savoirs.sort_values(["nb_metiers", "libelle_savoir"], ascending=[False, True])


# ---------- 5. On retire les liens vers les éléments supprimés (les diplômes) ----------
codes_gardes = list(competences["code_ogr"]) + list(savoirs["code_ogr"])
nb_avant = len(liens)
liens = liens[liens["code_ogr"].isin(codes_gardes)]


# ---------- 6. Enregistrement ----------
metiers.to_csv(f"{DOSSIER_SORTIE}/rome_jobs.csv", index=False)
competences.to_csv(f"{DOSSIER_SORTIE}/rome_competences.csv", index=False)
savoirs.to_csv(f"{DOSSIER_SORTIE}/rome_savoirs.csv", index=False)
liens.to_csv(f"{DOSSIER_SORTIE}/rome_liens.csv", index=False)

print(f"{len(metiers)} métiers, {len(competences)} compétences, "
      f"{len(savoirs)} savoirs, {len(liens)} liens")
print(f"{nb_avant - len(liens)} liens écartés (diplômes)")
print()
print("Nombre d'éléments par métier :")
print(pd.crosstab(liens["code_rome"].map(METIERS), liens["type"]))
