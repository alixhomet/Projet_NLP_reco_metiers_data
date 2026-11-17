"""Tests du référentiel : identifiants uniques, clés étrangères, longueurs des descriptions."""
import pytest

from src import data_loader


@pytest.fixture(scope="module")
def refs():
    return data_loader.load_reference()  # valide déjà unicité, clés étrangères et importance 1..3


def test_volume_phase1(refs):
    assert (len(refs["blocks"]), len(refs["competencies"]), len(refs["jobs"])) == (6, 30, 6)


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


def test_donnees_d_exemple_marquees(refs):
    for name in ("blocks", "competencies", "jobs"):
        assert refs[name]["description"].str.startswith("EXEMPLE").all()
