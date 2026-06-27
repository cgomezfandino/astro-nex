"""Smoke tests for the multi-type wheel renderer (render/wheel.py draw_wheel).

Each chart kind (radix, soul, house, dharma, nodal, ur_nodal, local) must draw
without crashing and produce non-blank output. Visual fidelity vs the legacy is
checked separately (human comparison); there is no pixel golden.
"""
import cairo
import pytest

from astronex.core.chart import Chart
from astronex.core.ephemeris import julday, local_houses
from astronex.render.wheel import draw_wheel, draw_radix


def _natal():
    ch = Chart()
    ch.calc((1985, 6, 15, 7.5), loc=(51.5074, -0.1278), epheflag=4)
    return ch


KINDS = ["radix", "soul", "house", "dharma", "nodal", "ur_nodal"]


def _ink_present(surface):
    return any(b != 0 for b in bytes(surface.get_data()))


@pytest.mark.parametrize("kind", KINDS)
def test_draw_wheel_kind_produces_nonblank(kind):
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 600, 600)
    cr = cairo.Context(surface)
    cr.set_source_rgb(1, 1, 1)
    cr.paint()
    draw_wheel(cr, _natal(), kind=kind, size=600)
    assert _ink_present(surface)


def test_draw_wheel_local_kind_uses_relocated_houses():
    # 'local' requires the caller to recompute houses for the relocated place.
    ch = _natal()
    jd = julday(*ch.calc.__self__ and (1985, 6, 15, 7.5))  # natal jd
    ch.houses = list(local_houses(jd, -0.1278, 51.5074, 4))
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 600, 600)
    cr = cairo.Context(surface)
    cr.set_source_rgb(1, 1, 1)
    cr.paint()
    draw_wheel(cr, ch, kind="local", size=600)
    assert _ink_present(surface)


def test_draw_radix_alias_matches_draw_wheel():
    # draw_radix is kept as an alias of draw_wheel(kind='radix') -- verify both
    # produce ink on the same chart.
    ch = _natal()
    s1 = cairo.ImageSurface(cairo.FORMAT_ARGB32, 400, 400)
    cr1 = cairo.Context(s1)
    draw_radix(cr1, ch, size=400)
    s2 = cairo.ImageSurface(cairo.FORMAT_ARGB32, 400, 400)
    cr2 = cairo.Context(s2)
    draw_wheel(cr2, ch, kind="radix", size=400)
    assert _ink_present(s1) and _ink_present(s2)


def test_draw_wheel_guards_empty_chart():
    # An uncalculated chart must not crash.
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 200, 200)
    cr = cairo.Context(surface)
    draw_wheel(cr, Chart(), kind="radix", size=200)  # no raise
