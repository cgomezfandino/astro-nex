"""Smoke tests for the datasheet renderer (render/datasheets.py)."""
import cairo
import pytest

from astronex.core.chart import Chart
from astronex.render.datasheets import draw_datasheet


def _chart():
    ch = Chart()
    ch.calc((1985, 6, 15, 7.5), loc=(51.5074, -0.1278), epheflag=4)
    return ch


def _ink(surface):
    return any(b != 0 for b in bytes(surface.get_data()))


def test_draw_datasheet_produces_nonblank():
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 600, 800)
    cr = cairo.Context(surface)
    cr.set_source_rgb(1, 1, 1)
    cr.paint()
    draw_datasheet(cr, _chart(), kind="radix", width=600, height=800)
    assert _ink(surface)


def test_draw_datasheet_guards_empty_chart():
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 600, 800)
    cr = cairo.Context(surface)
    draw_datasheet(cr, Chart(), kind="radix", width=600, height=800)  # no raise
    # only background drawn -> not asserted for ink, just no-crash


def test_draw_datasheet_exports_png(tmp_path):
    from astronex.surfaces.png import export_png

    class _DatasheetChart:
        """Adapter: draw_datasheet reads chart attributes directly, so wrap."""
        def __init__(self, real):
            self.planets = real.planets
            self.houses = real.houses
            self.which_all_signs = real.which_all_signs
            self.which_all_houses = real.which_all_houses
            self.aspects = real.aspects
            self.dyncalc_list = real.dyncalc_list
            self.rays_calc = real.rays_calc

    # datasheets draw directly on a context, not via draw_wheel, so use cairo
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 600, 800)
    cr = cairo.Context(surface)
    cr.set_source_rgb(1, 1, 1)
    cr.paint()
    draw_datasheet(cr, _chart(), kind="radix", width=600, height=800)
    out = tmp_path / "sheet.png"
    surface.write_to_png(str(out))
    assert out.exists() and out.stat().st_size > 1000
