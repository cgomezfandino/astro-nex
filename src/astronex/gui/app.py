# -*- coding: utf-8 -*-
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from .chart_entry import ChartEntry
from .chart_view import ChartView
from ..surfaces.png import export_png
from ..surfaces.pdf import export_pdf

class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Astro-Nex")
        self.set_default_size(1000, 640)
        self.current = None
        paned = Gtk.Paned()
        self.view = ChartView()
        entry = ChartEntry(self._on_chart)
        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        left.pack_start(entry, False, False, 0)
        for label, fn in [("Export PNG", self._png), ("Export PDF", self._pdf)]:
            b = Gtk.Button(label=label); b.connect("clicked", fn)
            left.pack_start(b, False, False, 0)
        paned.add1(left); paned.add2(self.view)
        self.add(paned)

    def _on_chart(self, chart):
        self.current = chart
        self.view.set_chart(chart)

    def _save_dialog(self, suffix):
        d = Gtk.FileChooserDialog(title="Save", parent=self,
            action=Gtk.FileChooserAction.SAVE)
        d.add_buttons("_Cancel", Gtk.ResponseType.CANCEL, "_Save", Gtk.ResponseType.OK)
        d.set_current_name("chart" + suffix)
        path = d.get_filename() if d.run() == Gtk.ResponseType.OK else None
        d.destroy()
        return path

    def _png(self, _b):
        if self.current and (p := self._save_dialog(".png")):
            export_png(self.current, p)

    def _pdf(self, _b):
        if self.current and (p := self._save_dialog(".pdf")):
            export_pdf(self.current, p)

class AstroNexApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="net.astronex.App")

    def do_activate(self):
        MainWindow(self).show_all()
