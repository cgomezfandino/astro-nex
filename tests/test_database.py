# -*- coding: utf-8 -*-
"""Tests for the port of database.py (issue #11).

Validates the locality lookups against the bundled local.db (the same SQLite
store shipped with the original Astro-Nex) and the chart store round-trip
against an ephemeral charts.db in tmp_path.

The functions are exercised as in the original: connect once, then query.
``countries.install`` is invoked so the ``t`` builtin (name translation) exists.
"""
import pytest

from astronex.core import countries
from astronex.core import database as db
from astronex.core.state import Locality


@pytest.fixture(scope="module", autouse=True)
def connected(tmp_path_factory):
    """Connect to the bundled localities DB + an ephemeral charts DB."""
    home = tmp_path_factory.mktemp("home")
    countries.install("es")  # registers the `t` builtin used by get_states
    db.connect(homedir=str(home))
    yield


# ---------------------------------------------------------------------------
# Country / region lookups
# ---------------------------------------------------------------------------
class TestCountryLookups:
    def test_get_name_from_code_spain(self):
        assert db.get_name_from_code("SP") == "España"

    def test_get_code_from_name_spain(self):
        assert db.get_code_from_name("España") == "SP"

    def test_get_name_from_usacode_california(self):
        assert db.get_name_from_usacode("CA") == "California"

    def test_get_usacode_from_name_california(self):
        assert db.get_usacode_from_name("California") == "CA"

    def test_get_states_returns_dict(self):
        states = db.get_states()
        assert "España" in states
        assert states["España"] == "SP"

    def test_get_states_usa(self):
        states = db.get_states(usa=True)
        assert "California" in states
        assert states["California"] == "CA"

    def test_list_regions_spain(self):
        regs = db.list_regions("SP")
        assert len(regs) > 0
        # each entry is (name, code)
        assert all(len(r) == 2 for r in regs)


# ---------------------------------------------------------------------------
# City lookups (world)
# ---------------------------------------------------------------------------
class TestCityLookups:
    def test_fetch_worldcity_girona(self):
        """fetch_worldcity fills a Locality for a known city."""
        loc = Locality()
        # table 'sp' (Spain), Girona, region code 56 (Catalunya)
        db.fetch_worldcity("sp", "Girona", "56", loc)
        assert loc.city == "Girona"
        assert loc.country_code == "SP"
        assert loc.country == "España"
        # decimals parsed from the dmsg textual coords
        assert loc.latdec is not None
        assert loc.longdec is not None
        assert loc.zone  # timezone resolved

    def test_fetch_blindly_girona(self):
        loc = Locality()
        result = db.fetch_blindly("sp", "Girona", loc)
        assert result is loc
        assert loc.city == "Girona"
        assert loc.latdec is not None

    def test_fetch_blindly_missing_returns_message(self):
        loc = Locality()
        result = db.fetch_blindly("sp", "CiudadInexistenteXYZ123", loc)
        assert isinstance(result, str)
        assert "no encontrada" in result

    def test_fetch_all_from_country_spain(self):
        cities = db.fetch_all_from_country("sp")
        assert len(cities) > 100
        # each entry is (city, region_code, formatted_geo)
        first = cities[0]
        assert len(first) == 3

    def test_coalesce_geo_format(self):
        # textual coords '-22021' (lon) / '370825' (lat) -> formatted W/N string
        out = db.coalesce_geo("-22021", "370825")
        assert "W" in out and "N" in out
        assert out == "2W20 37N08"


# ---------------------------------------------------------------------------
# Chart store round-trip
# ---------------------------------------------------------------------------
class TestChartStore:
    def test_create_table_and_store_and_load(self):
        from astronex.core.chart import Chart
        db.create_table("testcharts")
        ch = Chart()
        ch.first = "Ada"
        ch.last = "Lovelace"
        ch.date = "10121815"
        ch.city = "London"
        ch.region = "Greater London"
        ch.country = "England"
        ch.longitud = -0.127
        ch.latitud = 51.507
        ch.zone = "Europe/London"
        ch.planets = [float(i) for i in range(11)]
        ch.houses = [float(i) for i in range(12)]
        ch.comment = "test"
        rowid = db.store_chart("testcharts", ch)
        assert rowid > 0

        loaded = Chart()
        db.load_chart("testcharts", rowid, loaded)
        assert loaded.first == "Ada"
        assert loaded.last == "Lovelace"
        assert loaded.city == "London"
        assert loaded.planets == [float(i) for i in range(11)]
        assert loaded.houses == [float(i) for i in range(12)]

    def test_get_databases_lists_table(self):
        db.create_table("listme")
        dbs = db.get_databases()
        assert "listme" in dbs

    def test_get_chartlist(self):
        db.create_table("chartlist")
        from astronex.core.chart import Chart
        ch = Chart()
        ch.first = "Zed"
        ch.last = "Alpha"
        ch.planets = [0.0] * 11
        ch.houses = [0.0] * 12
        db.store_chart("chartlist", ch)
        rows = db.get_chartlist("chartlist")
        assert any(r[1] == "Zed" for r in rows)

    def test_delete_chart(self):
        db.create_table("deleteme")
        from astronex.core.chart import Chart
        ch = Chart()
        ch.first = "Tmp"
        ch.last = "Del"
        ch.planets = [0.0] * 11
        ch.houses = [0.0] * 12
        rid = db.store_chart("deleteme", ch)
        db.delete_chart("deleteme", rid)
        rows = db.get_chartlist("deleteme")
        assert all(r[0] != rid for r in rows)
