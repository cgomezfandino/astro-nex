# -*- coding: utf-8 -*-
"""Export a chart to a PNG file by rendering the radix wheel onto an image surface."""
import cairo
from ..render.wheel import draw_radix


def export_png(chart, path, size=800):
    """Render ``chart`` to a ``size``x``size`` PNG at ``path`` on a white background."""
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, size, size)
    cr = cairo.Context(surface)
    cr.set_source_rgb(1, 1, 1)
    cr.paint()
    draw_radix(cr, chart, size=size)
    surface.write_to_png(path)
