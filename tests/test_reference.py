"""Tests du référentiel : identifiants uniques, clés étrangères, longueurs des descriptions."""
import pytest

from src import data_loader


@pytest.fixture(scope="module")
def refs():
    return data_loader.load_reference()  # valide déjà unicité, clés étrangères et importance 1..3


def test_volume_referentiel(refs):
    # Cibles de la conception : 6 à 8 blocs, 60 à 100 compétences, au moins 14 métiers (ROME)
    assert 6 <= len(refs["blocks"]) <= 8
    assert 60 <= len(refs["competencies"]) <= 100
    assert len(refs["jobs"]) >= 14


def test_chaque_bloc_et_chaque_metier_est_utilise(refs):
    # Un bloc vide donnerait une moyenne indéfinie ; un métier sans compétence, une division par 0.
    assert set(refs["blocks"]["block_id"]) == set(refs["competencies"]["block_id"])
    assert set(refs["jobs"]["job_id"]) == set(refs["job_competencies"]["job_id"])


def test_validate_detecte_cle_etrangere_invalide(refs):
    bad = {**refs, "job_competencies": refs["job_competencies"].assign(competency_id="C99")}
    with pytest.raises(ValueError):
        data_loader.validate_reference(bad)


def test_validate_detecte_id_en_double(refs):
    bad = {**refs, "jobs": refs["jobs"].assign(job_id="J01")}
    with pytest.raises(ValueError):
        data_loader.validate_reference(bad)


def test_descriptions_de_competences_8_a_20_mots(refs):
    for text in refs["competencies"]["description"]:
        assert 8 <= len(data_loader.strip_example(text).split()) <= 20, text


def test_plus_de_donnees_d_exemple(refs):
    # Le vrai référentiel (ROME 4.0) remplace l'exemple de la phase 1
    for name in ("blocks", "competencies", "jobs"):
        assert not refs[name]["description"].str.startswith("EXEMPLE").any()
