"""End-to-end smoke for the GUI vertical: entry-parse -> chart -> view-modes ->
export. Exercises the function chain the MainWindow wires, headless (no Gtk
widget construction, no display needed).
"""
import os
import pytest

from astronex.core.chart import Chart
from astronex.core.state import Current
from astronex.core.ephemeris import julday, local_houses
from astronex.gui.chart_entry import ChartEntry
from astronex.gui.chart_view import VIEW_MODES, CHART_KINDS
from astronex.render.wheel import draw_wheel
from astronex.render.datasheets import draw_datasheet
from astronex.render.diagrams import draw_dyn_stars
from astronex.surfaces.png import export_png
from astronex.surfaces.pdf import export_pdf


class _FakeEntry:
    def __init__(self, text):
        self._t = text

    def get_text(self):
        return self._t


def _entry(fields):
    obj = ChartEntry.__new__(ChartEntry)
    obj.fields = {k: _FakeEntry(v) for k, v in fields.items()}
    return obj


GOOD = {
    "Name": "Test Person",
    "Date (YYYY-MM-DD)": "1985-06-15",
    "Time (HH:MM)": "08:30",
    "Latitude": "51.5074",
    "Longitude": "-0.1278",
    "Timezone": "Europe/London",
}


def test_full_vertical_wheel_datasheet_diagram(tmp_path):
    # 1. entry parse -> chart
    ch = _entry(GOOD)._parse()
    assert isinstance(ch, Chart) and len(ch.planets) == 11

    # 2. every chart kind draws as a wheel
    for kind in CHART_KINDS:
        export_png(ch, str(tmp_path / ("wheel_%s.png" % kind)),
                   kind=kind, view_mode="wheel", size=400)

    # 3. every view mode exports a valid file
    for mode in VIEW_MODES:
        out = tmp_path / ("view_%s.png" % mode)
        export_png(ch, str(out), kind="radix", view_mode=mode, size=400)
        assert out.exists() and out.stat().st_size > 500, mode

    # 4. pdf export in datasheet mode
    pdf_out = tmp_path / "sheet.pdf"
    export_pdf(ch, str(pdf_out), kind="radix", view_mode="datasheet", size=500)
    assert pdf_out.read_bytes().startswith(b"%PDF")


def test_local_kind_recomputes_houses():
    ch = _entry(GOOD)._parse()
    natal_houses = list(ch.houses)
    jd = julday(*ch._natal_dateforcalc)
    # mirror MainWindow._on_kind local branch
    ch.houses = list(local_houses(jd, ch._natal_loc[1], ch._natal_loc[0], 4))
    # local houses differ from natal Koch cusps (same place, ARMC-based)
    assert ch.houses != natal_houses
    assert len(ch.houses) == 12


def test_current_singleton_wiring():
    # MainWindow stores the computed chart into Current.master; verify replicate.
    Current._reset_singleton()
    state = Current(homedir="/tmp/astro_e2e_state")
    ch = _entry(GOOD)._parse()
    state.replicate(ch, state.master)
    state.curr_chart = state.master
    assert state.master.planets == ch.planets
    assert state.curr_chart is state.master
