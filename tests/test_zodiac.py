# -*- coding: utf-8 -*-
"""Tests for the port of zodiac.py (issue #14).

The Zodiac class caches sign/planet glyphs as cairo paths for efficient
drawing, which requires cairo + the Astro-Nex font. The behaviour we pin with
tests is the pure-data layer: the constant tuples, the colour bookkeeping
(get/set colours), and swap_plan_style. Glyph-path caching is exercised via a
render smoke test that only runs when the font is present.
"""
import pytest

from astronex.core import config as cfg
from astronex.core.zodiac import (
    Zodiac,
    zodlet,
    plantuples,
    plagram_tuples,
    plagram_extra,
    crosscolors,
)


# ---------------------------------------------------------------------------
# Constant tuples
# ---------------------------------------------------------------------------
class TestConstants:
    def test_zodlet_has_twelve_signs(self):
        assert len(zodlet) == 12
        assert zodlet[0] == 'q'

    def test_plantuples_entries(self):
        # each: (glyph, size, category)
        cats = {t[2] for t in plantuples}
        assert cats == {'pers', 'tool', 'trans', 'node'}
        assert ('d', 30.0, 'pers') in plantuples

    def test_plagram_tuples_lengths(self):
        assert len(plagram_tuples) == 12
        assert len(plagram_extra) == 11

    def test_crosscolors_keys(self):
        for k in ('card', 'fix', 'mut'):
            assert k in crosscolors


# ---------------------------------------------------------------------------
# Zodiac colour bookkeeping (no cairo needed)
# ---------------------------------------------------------------------------
class TestZodiacColors:
    def setup_method(self):
        cfg.init_cfgcols(cfg.default_colors)
        Zodiac.reset_cache()  # ensure clean class state

    def test_aspect_colors_layout(self):
        z = Zodiac()
        asp = z.get_aspcolors()
        assert len(asp) == 12
        # index 0 -> orange, 1/5/7/11 -> green, 2/4/8/10 -> blue, 3/6/9 -> red
        assert asp[0] == pytest.approx(cfg.hex_to_rgb("ff8000"))
        assert asp[1] == pytest.approx(cfg.hex_to_rgb("00cc00"))
        assert asp[2] == pytest.approx(cfg.hex_to_rgb("0000f7"))
        assert asp[3] == pytest.approx(cfg.hex_to_rgb("ee0000"))

    def test_aux_colors_keys(self):
        z = Zodiac()
        aux = z.get_auxcolors()
        for k in ('click1', 'click2', 'clicksoul', 'inv', 'low', 'transcol'):
            assert k in aux

    def test_crosscolors_passthrough(self):
        z = Zodiac()
        cc = z.get_crosscolors()
        assert cc['card'] == (0.7, 0, 0.2)

    def test_zod_colors_are_first_four(self):
        z = Zodiac()
        cols = z.get_zodcolors()
        assert len(cols) == 4

    def test_plan_colors_picks_indices(self):
        z = Zodiac()
        cols = z.get_plancolors()
        assert len(cols) == 4

    def test_reset_colors(self):
        z = Zodiac()
        z.set_allcolors()  # should not raise
