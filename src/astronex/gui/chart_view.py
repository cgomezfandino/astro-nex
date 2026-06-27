# -*- coding: utf-8 -*-
"""GTK 3 drawing-area widget that paints a chart's radix wheel via the renderer."""
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from ..render.wheel import draw_radix

class ChartView(Gtk.DrawingArea):
    """A ``Gtk.DrawingArea`` that renders the current chart, redrawing on resize."""
    def __init__(self):
        super().__init__()
        self.chart = None
        self.set_size_request(600, 600)
        self.connect("draw", self._on_draw)

    def set_chart(self, chart):
        self.chart = chart
        self.queue_draw()

    def _on_draw(self, _widget, cr):
        if self.chart is None:
            return False
        size = min(self.get_allocated_width(), self.get_allocated_height())
        cr.set_source_rgb(1, 1, 1)
        cr.paint()
        draw_radix(cr, self.chart, size=size)
        return False
