"""Smoke tests for ChartEntry validation/parse logic (headless).

The widget needs a display; here we test the _parse() method by stubbing the
fields dict with objects exposing get_text(), so no Gtk widget is constructed.
"""
import pytest

from astronex.core.chart import Chart
from astronex.gui.chart_entry import ChartEntry, FIELD_DEFAULTS


class _FakeEntry:
    def __init__(self, text):
        self._t = text

    def get_text(self):
        return self._t


def _entry_with_fields(field_values):
    """Build a ChartEntry-like object with _parse working against fake fields."""
    obj = ChartEntry.__new__(ChartEntry)  # bypass Gtk.Box.__init__ (needs display)
    obj.fields = {label: _FakeEntry(val) for label, val in field_values.items()}
    return obj


GOOD = {
    "Name": "Jane Doe",
    "Date (YYYY-MM-DD)": "1985-06-15",
    "Time (HH:MM)": "08:30",
    "Latitude": "51.5074",
    "Longitude": "-0.1278",
    "Timezone": "Europe/London",
}


def test_parse_valid_input_returns_chart():
    obj = _entry_with_fields(GOOD)
    ch = obj._parse()
    assert isinstance(ch, Chart)
    assert len(ch.planets) == 11 and len(ch.houses) == 12
    assert ch.first == "Jane" and ch.last == "Doe"


def test_parse_bad_date_format_raises():
    bad = dict(GOOD, **{"Date (YYYY-MM-DD)": "15/06/1985"})
    with pytest.raises(ValueError, match="AAAA-MM-DD"):
        _entry_with_fields(bad)._parse()


def test_parse_bad_time_raises():
    bad = dict(GOOD, **{"Time (HH:MM)": "8.30"})
    with pytest.raises(ValueError, match="HH:MM"):
        _entry_with_fields(bad)._parse()


def test_parse_nonnumeric_lat_raises():
    bad = dict(GOOD, **{"Latitude": "north"})
    with pytest.raises(ValueError, match="números"):
        _entry_with_fields(bad)._parse()


def test_parse_lat_out_of_range_raises():
    bad = dict(GOOD, **{"Latitude": "999"})
    with pytest.raises(ValueError, match="fuera de rango"):
        _entry_with_fields(bad)._parse()


def test_parse_bad_timezone_raises():
    bad = dict(GOOD, **{"Timezone": "Mars/Olympus"})
    with pytest.raises(ValueError, match="Zona horaria"):
        _entry_with_fields(bad)._parse()


def test_field_defaults_has_name():
    labels = [lbl for lbl, _ in FIELD_DEFAULTS]
    assert "Name" in labels
