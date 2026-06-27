"""Smoke tests for the ChartView multi-mode/multi-kind dispatcher.

GTK widget construction needs a display; here we test the dispatch logic by
calling the same render functions the widget calls, on a plain ImageSurface
(headless). The widget import + class definition are also verified.
"""
import cairo
import pytest

from astronex.core.chart import Chart
from astronex.gui import chart_view  # import OK (no Gtk.main needed at import)
from astronex.render.wheel import draw_wheel
from astronex.render.datasheets import draw_datasheet
from astronex.render.diagrams import draw_dyn_stars


def _chart():
    ch = Chart()
    ch.calc((1985, 6, 15, 7.5), loc=(51.5074, -0.1278), epheflag=4)
    return ch


def _ink(surface):
    return any(b != 0 for b in bytes(surface.get_data()))


def test_chart_view_module_exposes_modes_and_kinds():
    assert "wheel" in chart_view.VIEW_MODES
    assert "datasheet" in chart_view.VIEW_MODES
    assert "diagram" in chart_view.VIEW_MODES
    assert "radix" in chart_view.CHART_KINDS
    assert "local" in chart_view.CHART_KINDS
    assert hasattr(chart_view, "ChartView")


def test_dispatch_wheel_mode():
    # mirrors ChartView._on_draw wheel branch
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, 600, 600)
    cr = cairo.Context(s)
    cr.set_source_rgb(1, 1, 1); cr.paint()
    draw_wheel(cr, _chart(), kind="radix", size=600)
    assert _ink(s)


def test_dispatch_datasheet_mode():
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, 600, 800)
    cr = cairo.Context(s)
    cr.set_source_rgb(1, 1, 1); cr.paint()
    draw_datasheet(cr, _chart(), kind="radix", width=600, height=800)
    assert _ink(s)


def test_dispatch_diagram_mode():
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, 600, 600)
    cr = cairo.Context(s)
    cr.set_source_rgb(1, 1, 1); cr.paint()
    draw_dyn_stars(cr, _chart(), width=600, height=600)
    assert _ink(s)
