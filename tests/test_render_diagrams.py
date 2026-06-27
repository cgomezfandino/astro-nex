"""Smoke tests for the dynamics diagrams renderer (render/diagrams.py)."""
import cairo
import pytest

from astronex.core.chart import Chart
from astronex.render.diagrams import draw_dyn_stars


def _chart():
    ch = Chart()
    ch.calc((1985, 6, 15, 7.5), loc=(51.5074, -0.1278), epheflag=4)
    return ch


def _ink(surface):
    return any(b != 0 for b in bytes(surface.get_data()))


def test_draw_dyn_stars_produces_nonblank():
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 600, 600)
    cr = cairo.Context(surface)
    cr.set_source_rgb(1, 1, 1)
    cr.paint()
    draw_dyn_stars(cr, _chart(), width=600, height=600)
    assert _ink(surface)


def test_draw_dyn_stars_guards_empty_chart():
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 600, 600)
    cr = cairo.Context(surface)
    draw_dyn_stars(cr, Chart(), width=600, height=600)  # no raise


def test_draw_dyn_stars_exports_png(tmp_path):
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 600, 600)
    cr = cairo.Context(surface)
    cr.set_source_rgb(1, 1, 1)
    cr.paint()
    draw_dyn_stars(cr, _chart(), width=600, height=600)
    out = tmp_path / "dyn.png"
    surface.write_to_png(str(out))
    assert out.exists() and out.stat().st_size > 1000
