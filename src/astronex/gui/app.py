# -*- coding: utf-8 -*-
"""GTK 3 application shell: a window pairing the entry form with the chart view,
plus chart-type / view-mode selectors and PNG/PDF export. This layer only
orchestrates; all calculation and drawing live in ``core``/``render``/``surfaces``.
"""
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from .chart_entry import ChartEntry
from .chart_view import ChartView, VIEW_MODES, CHART_KINDS
from ..core.ephemeris import julday, local_houses
from ..surfaces.png import export_png
from ..surfaces.pdf import export_pdf

VIEW_MODE_LABELS = {
    "wheel": "Rueda", "datasheet": "Hoja de datos", "diagram": "Diagrama"}
KIND_LABELS = {
    "radix": "Radix", "soul": "Alma", "house": "Casas", "dharma": "Dharma",
    "nodal": "Nodal", "ur_nodal": "UR-Nodal", "local": "Local"}


class MainWindow(Gtk.ApplicationWindow):
    """Main window: entry + selectors + export on the left, chart view on the right."""

    def __init__(self, app):
        super().__init__(application=app, title="Astro-Nex")
        self.set_default_size(1000, 640)
        self.current = None
        self._natal_jd = None  # for local-house recompute

        paned = Gtk.Paned()
        self.view = ChartView()
        entry = ChartEntry(self._on_chart)

        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        left.pack_start(entry, False, False, 0)

        # --- view-mode selector ---
        vm_row = Gtk.Box(spacing=6)
        vm_row.pack_start(Gtk.Label(label="Vista:"), False, False, 0)
        self.vm_combo = Gtk.ComboBoxText()
        for mode in VIEW_MODES:
            self.vm_combo.append_text(VIEW_MODE_LABELS[mode])
        self.vm_combo.set_active(0)
        self.vm_combo.connect("changed", self._on_view_mode)
        vm_row.pack_start(self.vm_combo, True, True, 0)
        left.pack_start(vm_row, False, False, 0)

        # --- chart-type selector ---
        kind_row = Gtk.Box(spacing=6)
        kind_row.pack_start(Gtk.Label(label="Tipo:"), False, False, 0)
        self.kind_combo = Gtk.ComboBoxText()
        for kind in CHART_KINDS:
            self.kind_combo.append_text(KIND_LABELS[kind])
        self.kind_combo.set_active(0)
        self.kind_combo.connect("changed", self._on_kind)
        kind_row.pack_start(self.kind_combo, True, True, 0)
        left.pack_start(kind_row, False, False, 0)

        for label, fn in [("Export PNG", self._png), ("Export PDF", self._pdf)]:
            b = Gtk.Button(label=label); b.connect("clicked", fn)
            left.pack_start(b, False, False, 0)

        paned.add1(left); paned.add2(self.view)
        self.add(paned)

    # --- selection handlers ---
    def _current_view_mode(self):
        return VIEW_MODES[self.vm_combo.get_active()]

    def _current_kind(self):
        return CHART_KINDS[self.kind_combo.get_active()]

    def _on_view_mode(self, _combo):
        self.view.set_view_mode(self._current_view_mode())

    def _on_kind(self, _combo):
        kind = self._current_kind()
        if kind == "local" and self.current is not None and self._natal_jd is not None:
            # recompute houses for the relocated place (same coords here)
            loc = self.current._natal_loc
            self.current.houses = list(local_houses(self._natal_jd, loc[1], loc[0], 4))
        self.view.set_kind(kind)

    # --- chart arrival from entry ---
    def _on_chart(self, chart):
        self.current = chart
        # stash natal jd + loc for local-house recompute
        self._natal_jd = julday(*chart._natal_dateforcalc) if hasattr(chart, "_natal_dateforcalc") else None
        self.view.set_chart(chart)

    # --- export ---
    def _save_dialog(self, suffix):
        d = Gtk.FileChooserDialog(title="Guardar", parent=self,
            action=Gtk.FileChooserAction.SAVE)
        d.add_buttons("_Cancelar", Gtk.ResponseType.CANCEL,
                      "_Guardar", Gtk.ResponseType.OK)
        d.set_current_name("carta" + suffix)
        path = d.get_filename() if d.run() == Gtk.ResponseType.OK else None
        d.destroy()
        return path

    def _png(self, _b):
        if self.current and (p := self._save_dialog(".png")):
            export_png(self.current, p, kind=self._current_kind(),
                       view_mode=self._current_view_mode())

    def _pdf(self, _b):
        if self.current and (p := self._save_dialog(".pdf")):
            export_pdf(self.current, p, kind=self._current_kind(),
                       view_mode=self._current_view_mode())


class AstroNexApp(Gtk.Application):
    """The Astro-Nex GTK application; shows the main window on activation."""
    def __init__(self):
        super().__init__(application_id="net.astronex.App")

    def do_activate(self):
        MainWindow(self).show_all()
