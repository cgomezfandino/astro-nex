# -*- coding: utf-8 -*-
"""Export a chart to a PNG file by rendering it via the renderer layer.

Threads ``kind`` and ``view_mode`` so the exported file matches the on-screen
view (wheel / datasheet / diagram, in the selected chart type).
"""
import cairo
from ..render.wheel import draw_wheel
from ..render.datasheets import draw_datasheet
from ..render.diagrams import draw_dyn_stars


def export_png(chart, path, kind="radix", view_mode="wheel", size=800):
    """Render ``chart`` to a PNG at ``path`` in the given view/kind.

    ``size`` is the square edge for wheel/diagram; for datasheet the canvas is
    ``size`` x ``size*4/3`` to keep the table's aspect.
    """
    if view_mode == "datasheet":
        w, h = size, int(size * 4 / 3)
    else:
        w = h = size
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    cr = cairo.Context(surface)
    cr.set_source_rgb(1, 1, 1)
    cr.paint()
    if view_mode == "datasheet":
        draw_datasheet(cr, chart, kind=kind, width=w, height=h)
    elif view_mode == "diagram":
        draw_dyn_stars(cr, chart, width=w, height=h)
    else:  # wheel
        draw_wheel(cr, chart, kind=kind, size=min(w, h))
    surface.write_to_png(path)
