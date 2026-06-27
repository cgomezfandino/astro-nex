# -*- coding: utf-8 -*-
"""Tests for the port of config.py (issue #13).

We port the dependency-free, behaviour-defining parts first: the default
constants, the NexConf object, and the colour-parsing helpers. The original
used gtk.gdk.color_parse and the configobj library; the port parses hex colours
directly (no GTK dependency) and uses stdlib semantics, while preserving the
exact default colour values of the original.
"""
import pytest

from astronex.core import config as cfg


# ---------------------------------------------------------------------------
# Default constants
# ---------------------------------------------------------------------------
class TestDefaults:
    def test_default_colors_present(self):
        # Every colour key referenced by the parse_* and zodiac code must exist
        for key in ("pers", "tool", "trans", "node",
                    "fire", "earth", "air", "water",
                    "orange", "green", "blue", "red",
                    "click1", "click2", "inv", "low", "transcol",
                    "overlay", "clicksoul"):
            assert key in cfg.default_colors

    def test_default_color_values_match_original(self):
        assert cfg.default_colors["pers"] == "ff5600"
        assert cfg.default_colors["tool"] == "0000ff"
        assert cfg.default_colors["fire"] == "dd0000"
        assert cfg.default_colors["earth"] == "00bb00"
        assert cfg.default_colors["air"] == "ffb600"
        assert cfg.default_colors["water"] == "0000ff"
        assert cfg.default_colors["orange"] == "ff8000"
        assert cfg.default_colors["green"] == "00cc00"
        assert cfg.default_colors["red"] == "ee0000"

    def test_orbs_defaults(self):
        assert cfg.ORBS["lum"] == [3.0, 5.0, 6.0, 8.0, 9.0]
        assert cfg.ORBS["normal"] == [2.0, 4.0, 5.0, 6.0, 7.0]
        assert cfg.ORBS["transits"] == [1.0, 1.0, 1.0, 1.0, 1.0,
                                        2.0, 2.0, 2.0, 2.0, 2.0, 1.0]

    def test_default_section_values(self):
        assert cfg.DEFAULT["country"] == "SP"
        assert cfg.DEFAULT["region"] == 53
        assert cfg.DEFAULT["locality"] == "Las Palmas de Gran Canaria"
        assert cfg.DEFAULT["database"] == "personal"


# ---------------------------------------------------------------------------
# Colour hex parsing
# ---------------------------------------------------------------------------
class TestHexToRgb:
    """parse_*_colors convert hex strings to (r,g,b) tuples in 0..1.

    The original divided gtk.gdk channels by 65535. Hex "rrggbb" → r/255 etc.
    """
    def test_pure_red(self):
        assert cfg.hex_to_rgb("ff0000") == (1.0, 0.0, 0.0)

    def test_pure_green(self):
        assert cfg.hex_to_rgb("00ff00") == (0.0, 1.0, 0.0)

    def test_mid_orange(self):
        r, g, b = cfg.hex_to_rgb("ff8000")
        assert r == pytest.approx(1.0)
        assert g == pytest.approx(0x80 / 255)
        assert b == 0.0


# ---------------------------------------------------------------------------
# parse_*_colors
# ---------------------------------------------------------------------------
class TestParseColors:
    def setup_method(self):
        # Initialise the module colour map from defaults (as read_config does)
        cfg.init_cfgcols(cfg.default_colors)

    def test_parse_zod_colors_has_four_elements(self):
        cols = cfg.parse_zod_colors()
        assert len(cols) == 4

    def test_parse_zod_colors_values(self):
        cols = cfg.parse_zod_colors()
        # fire dd0000
        assert cols[0] == pytest.approx((0xdd / 255, 0.0, 0.0))
        # water 0000ff
        assert cols[3] == pytest.approx((0.0, 0.0, 1.0))

    def test_parse_plan_colors_keys(self):
        cols = cfg.parse_plan_colors()
        for key in ("pers", "tool", "trans", "node"):
            assert key in cols
        assert cols["pers"] == pytest.approx((1.0, 0x56 / 255, 0.0))

    def test_parse_asp_colors_keys(self):
        cols = cfg.parse_asp_colors()
        for key in ("orange", "green", "blue", "red"):
            assert key in cols
        assert cols["green"] == pytest.approx((0.0, 0xcc / 255, 0.0))

    def test_parse_aux_colors_keys(self):
        cols = cfg.parse_aux_colors()
        for key in ("click1", "click2", "clicksoul", "inv", "low", "transcol"):
            assert key in cols


# ---------------------------------------------------------------------------
# NexConf
# ---------------------------------------------------------------------------
class TestNexConf:
    def test_has_all_section_attributes(self):
        opts = cfg.NexConf()
        # attributes come from every section's keys
        assert opts.country == "SP"
        assert opts.database == "personal"
        assert opts.font == "Sans 11"
        assert opts.transtyle == "huber"

    def test_lang_defaults_to_known_locale(self):
        opts = cfg.NexConf()
        assert opts.lang in ("es", "en", "ca", "de")
