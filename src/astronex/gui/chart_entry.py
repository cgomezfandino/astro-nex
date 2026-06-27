# -*- coding: utf-8 -*-
"""GTK 3 birth-data entry form that builds a computed Chart and hands it to a callback.

Text-field input (no calendar popup) with validation: malformed input pops a
``Gtk.MessageDialog`` with a readable error instead of crashing the handler.
Captures first/last name (stored on the chart for display/save).
"""
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from datetime import datetime
from zoneinfo import ZoneInfo
from ..core.nexdate import NeXDate
from ..core.chart import Chart

FIELD_DEFAULTS = [
    ("Name", "Jane Doe"),
    ("Date (YYYY-MM-DD)", "1985-06-15"),
    ("Time (HH:MM)", "08:30"),
    ("Latitude", "51.5074"),
    ("Longitude", "-0.1278"),
    ("Timezone", "Europe/London"),
]


class ChartEntry(Gtk.Box):
    """Form: name, date, time, lat, lon, tz -> emits a computed Chart via callback."""

    def __init__(self, on_chart):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.on_chart = on_chart
        self.fields = {}
        for label, default in FIELD_DEFAULTS:
            row = Gtk.Box(spacing=6)
            row.pack_start(Gtk.Label(label=label), False, False, 0)
            entry = Gtk.Entry(text=default)
            row.pack_start(entry, True, True, 0)
            self.pack_start(row, False, False, 0)
            self.fields[label] = entry
        btn = Gtk.Button(label="Calcular")
        btn.connect("clicked", self._on_calc)
        self.pack_start(btn, False, False, 0)

    def _error(self, msg):
        """Show a modal error dialog (no crash). Tolerates missing toplevel."""
        dlg = Gtk.MessageDialog(
            transient_for=self.get_toplevel(),
            flags=Gtk.DialogFlags.MODAL,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text_format="Datos no válidos",
            secondary_text=msg)
        dlg.run()
        dlg.destroy()

    def _parse(self):
        """Parse the fields into a computed Chart. Raises ValueError on bad input."""
        f = self.fields
        date_s = f["Date (YYYY-MM-DD)"].get_text().strip()
        time_s = f["Time (HH:MM)"].get_text().strip()
        parts = date_s.split("-")
        if len(parts) != 3:
            raise ValueError("Fecha debe ser AAAA-MM-DD")
        tparts = time_s.split(":")
        if len(tparts) != 2:
            raise ValueError("Hora debe ser HH:MM")
        try:
            y, mo, d = [int(x) for x in parts]
            hh, mm = [int(x) for x in tparts]
        except ValueError:
            raise ValueError("Fecha/hora contienen valores no numéricos")
        if not (1 <= mo <= 12 and 1 <= d <= 31 and 0 <= hh <= 23 and 0 <= mm <= 59):
            raise ValueError("Valores fuera de rango (mes/día/hora/min)")
        try:
            lat = float(f["Latitude"].get_text())
            lon = float(f["Longitude"].get_text())
        except ValueError:
            raise ValueError("Latitud/longitud deben ser números")
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            raise ValueError("Latitud (-90..90) o longitud (-180..180) fuera de rango")
        tz_name = f["Timezone"].get_text().strip()
        try:
            tz = ZoneInfo(tz_name)
        except Exception:
            raise ValueError("Zona horaria desconocida: %s" % tz_name)
        nd = NeXDate(datetime(y, mo, d, hh, mm), tz=tz)
        ch = Chart()
        dateforcalc = nd.dateforcalc()
        ch.calc(dateforcalc, loc=(lat, lon), epheflag=4)
        # stash natal jd + loc for local-house recompute by the controller
        ch._natal_dateforcalc = dateforcalc
        ch._natal_loc = (lat, lon)
        name = f["Name"].get_text().strip()
        if name:
            parts = name.split(None, 1)
            ch.first = parts[0]
            ch.last = parts[1] if len(parts) > 1 else ""
        return ch

    def _on_calc(self, _btn):
        try:
            ch = self._parse()
        except (ValueError, Exception) as exc:
            self._error(str(exc))
            return
        self.on_chart(ch)
