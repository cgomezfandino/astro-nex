# -*- coding: utf-8 -*-
"""Tests for the port of countries.py (issue #15).

countries.py is mostly static data (a dict of country names in 4 languages plus
a catalan region map). ``install(lang)`` is *destructive*: it collapses the
multilingual dict to a single-language one in place. Each test that exercises
``install`` therefore restores the multilingual dict afterwards via the module's
``_multilingual`` snapshot.
"""
import copy

import pytest

from astronex.core import countries as c


@pytest.fixture(autouse=True)
def restore_multilingual():
    """Snapshot the multilingual dict before each test and restore it after.

    ``install`` mutates the module global destructively, so without this the
    tests would interfere with each other depending on execution order.
    """
    saved = copy.deepcopy(c.countries)
    yield
    c.countries = saved


class TestData:
    def test_countries_is_multilingual(self):
        # each value is [es, en, de, ca]
        assert "España" in c.countries
        assert c.countries["España"] == ["España", "Spain", "Spanien", "Espanya"]

    def test_germany_entry(self):
        assert c.countries["Alemania"][1] == "Germany"

    def test_cata_reg_present(self):
        assert "Cataluña" in c.cata_reg
        assert c.cata_reg["Cataluña"] == "Catalunya"


class TestInstall:
    def test_install_collapses_to_english(self):
        c.install("en")
        assert c.countries["España"] == "Spain"
        assert c.countries["Alemania"] == "Germany"

    def test_install_adds_usa(self):
        c.install("en")
        assert c.countries["USA"] == "USA"

    def test_install_spanish(self):
        c.install("es")
        assert c.countries["España"] == "España"


class TestTrad:
    def test_trad_known(self):
        c.install("en")
        assert c.trad("España") == "Spain"

    def test_trad_unknown_returns_input(self):
        c.install("en")
        assert c.trad("NoSuchPlace") == "NoSuchPlace"
