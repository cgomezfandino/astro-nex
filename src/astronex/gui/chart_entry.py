# -*- coding: utf-8 -*-
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from datetime import datetime
from zoneinfo import ZoneInfo
from ..core.nexdate import NeXDate
from ..core.chart import Chart

class ChartEntry(Gtk.Box):
    """Form: date, time, lat, lon, tz -> emits a computed Chart via callback."""
    def __init__(self, on_chart):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.on_chart = on_chart
        self.fields = {}
        for label, default in [("Date (YYYY-MM-DD)", "1985-06-15"),
                               ("Time (HH:MM)", "08:30"),
                               ("Latitude", "51.5074"),
                               ("Longitude", "-0.1278"),
                               ("Timezone", "Europe/London")]:
            row = Gtk.Box(spacing=6)
            row.pack_start(Gtk.Label(label=label), False, False, 0)
            entry = Gtk.Entry(text=default)
            row.pack_start(entry, True, True, 0)
            self.pack_start(row, False, False, 0)
            self.fields[label] = entry
        btn = Gtk.Button(label="Calcular")
        btn.connect("clicked", self._on_calc)
        self.pack_start(btn, False, False, 0)

    def _on_calc(self, _btn):
        f = self.fields
        y, mo, d = [int(x) for x in f["Date (YYYY-MM-DD)"].get_text().split("-")]
        hh, mm = [int(x) for x in f["Time (HH:MM)"].get_text().split(":")]
        lat = float(f["Latitude"].get_text())
        lon = float(f["Longitude"].get_text())
        tz = ZoneInfo(f["Timezone"].get_text())
        nd = NeXDate(datetime(y, mo, d, hh, mm), tz=tz)
        ch = Chart()
        ch.calc(nd.dateforcalc(), loc=(lat, lon), epheflag=4)
        self.on_chart(ch)
