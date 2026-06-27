# -*- coding: utf-8 -*-
"""GTK 3 drawing-area widget that paints a chart via the renderer layer.

Supports three view modes (wheel / datasheet / diagram) and the seven chart
types (radix / soul / house / dharma / nodal / ur_nodal / local). Dispatches in
``_on_draw`` to the matching pure-cairo renderer in ``render/``.
"""
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from ..render.wheel import draw_wheel
from ..render.datasheets import draw_datasheet
from ..render.diagrams import draw_dyn_stars

VIEW_MODES = ("wheel", "datasheet", "diagram")
CHART_KINDS = ("radix", "soul", "house", "dharma", "nodal", "ur_nodal", "local")


class ChartView(Gtk.DrawingArea):
    """A ``Gtk.DrawingArea`` rendering the current chart in the selected mode/kind."""

    def __init__(self):
        super().__init__()
        self.chart = None
        self.view_mode = "wheel"
        self.kind = "radix"
        self.set_size_request(600, 600)
        self.connect("draw", self._on_draw)

    def set_chart(self, chart):
        self.chart = chart
        self.queue_draw()

    def set_view_mode(self, mode):
        if mode not in VIEW_MODES:
            raise ValueError("unknown view mode: %r" % mode)
        self.view_mode = mode
        # datasheet/diagram have different aspect ratios than the square wheel
        if mode == "datasheet":
            self.set_size_request(600, 800)
        elif mode == "diagram":
            self.set_size_request(600, 600)
        else:
            self.set_size_request(600, 600)
        self.queue_draw()

    def set_kind(self, kind):
        if kind not in CHART_KINDS:
            raise ValueError("unknown chart kind: %r" % kind)
        self.kind = kind
        self.queue_draw()

    def _on_draw(self, _widget, cr):
        if self.chart is None:
            return False
        w = self.get_allocated_width()
        h = self.get_allocated_height()
        cr.set_source_rgb(1, 1, 1)
        cr.paint()

        if self.view_mode == "datasheet":
            draw_datasheet(cr, self.chart, kind=self.kind, width=w, height=h)
        elif self.view_mode == "diagram":
            draw_dyn_stars(cr, self.chart, width=w, height=h)
        else:  # wheel
            size = min(w, h)
            draw_wheel(cr, self.chart, kind=self.kind, size=size)
        return False
