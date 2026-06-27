# -*- coding: utf-8 -*-
"""Tests for the port of state.py (issue #12).

We build state.py bottom-up, unit by unit, comparing against the behaviour of
the original Astro-Nex (Py2). This file starts with the pure, dependency-free
units: Locality, PersonInfo and the operation/category constant lists.
"""
import pytest

from astronex.core.state import (
    Locality,
    datlist,
    dialist,
    biolist,
    tranlist,
    clicklist,
    opdouble,
    optriplepair,
    listlabels,
)


# ---------------------------------------------------------------------------
# Locality
# ---------------------------------------------------------------------------
class TestLocality:
    """Locality is a plain data holder for a geographic place."""

    def test_defaults_are_empty_or_none(self):
        loc = Locality()
        assert loc.country == ""
        assert loc.country_code == ""
        assert loc.city == ""
        assert loc.region == ""
        assert loc.region_code == ""
        assert loc.latitud == ""
        assert loc.longitud == ""
        assert loc.zone == ""
        # decimal coords start as None (unset), matching the original
        assert loc.latdec is None
        assert loc.longdec is None

    def test_attributes_are_writable(self):
        loc = Locality()
        loc.country = "Spain"
        loc.city = "Girona"
        loc.latdec = 41.98
        loc.longdec = 2.82
        loc.zone = "Europe/Madrid"
        assert loc.country == "Spain"
        assert loc.latdec == 41.98

    def test_two_instances_are_independent(self):
        a = Locality()
        b = Locality()
        a.city = "Barcelona"
        assert b.city == ""


# ---------------------------------------------------------------------------
# Operation / category constant lists (module-level data from the original)
# ---------------------------------------------------------------------------
class TestOpLists:
    """The constant deques/lists drive the toolbar/chart-type selection."""

    def test_opdouble_contains_all_chart_types(self):
        # Every draw_* chart type from the original boss.py suffixes must be here
        for kind in ("draw_nat", "draw_house", "draw_nod", "draw_soul",
                     "draw_dharma", "draw_ur_nodal", "draw_local", "draw_prof",
                     "draw_int", "draw_single", "draw_radsoul", "draw_planetogram"):
            assert kind in list(opdouble)

    def test_clicklist_contents(self):
        assert set(clicklist) == {"click_hh", "click_nn", "click_hn", "click_nh",
                                  "subject_click", "click_rr", "click_bridge"}

    def test_datlist_contents(self):
        assert set(datlist) == {"dat_nat", "dat_house", "dat_nod",
                                "prog_nat", "prog_nod", "prog_local", "prog_soul"}

    def test_dialist_contents(self):
        assert set(dialist) == {"dyn_cuad", "dyn_cuad2", "dyn_stars"}

    def test_biolist_contents(self):
        assert set(biolist) == {"bio_nat", "bio_nod", "bio_soul"}

    def test_tranlist_contents(self):
        assert set(tranlist) == {"draw_transits", "rad_and_transit"}

    def test_optriplepair_is_subset_of_clicks_plus_ss(self):
        assert set(optriplepair) == {"click_hh", "click_nn", "click_hn", "click_nh",
                                     "click_ss", "click_rr", "subject_click"}

    def test_listlabels_keys(self):
        for key in ("opdouble", "charts", "data", "clicks", "bio",
                    "diagram", "transit", "double1", "double2",
                    "triple1", "triple2"):
            assert key in listlabels

    def test_listlabels_charts_maps_to_opdouble(self):
        assert list(listlabels["charts"]) == list(opdouble)
        assert list(listlabels["opdouble"]) == list(opdouble)


# ---------------------------------------------------------------------------
# PersonInfo
# ---------------------------------------------------------------------------
from astronex.core.state import PersonInfo


class TestPersonInfo:
    """PersonInfo holds the active person's name, with a default placeholder."""

    def test_default_first_name_is_placeholder(self):
        p = PersonInfo()
        # The original used a gettext placeholder "sin_nombre<N>"; we keep a
        # deterministic, untranslated placeholder so tests are stable.
        assert p.first  # non-empty default
        assert p.last == ""

    def test_set_first_noname_clears(self):
        p = PersonInfo()
        p.set_first(noname=True)
        assert p.first == ""

    def test_set_first_assigns_placeholder_and_increments(self):
        PersonInfo.count = 1  # reset class counter
        p = PersonInfo()
        assert p.first == "sin_nombre1"
        assert PersonInfo.count == 1  # __init__ does not increment
        p.set_first()
        assert PersonInfo.count == 2  # set_first advances the counter
        # The next instance sees the incremented counter
        q = PersonInfo()
        assert q.first == "sin_nombre2"
