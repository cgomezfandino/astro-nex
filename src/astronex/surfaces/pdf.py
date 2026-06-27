# -*- coding: utf-8 -*-
"""Export a chart to a PDF file by rendering the radix wheel onto a PDF surface."""
import cairo
from ..render.wheel import draw_radix


def export_pdf(chart, path, size=800):
    """Render ``chart`` to a single ``size``x``size`` point PDF page at ``path``."""
    surface = cairo.PDFSurface(path, size, size)
    cr = cairo.Context(surface)
    draw_radix(cr, chart, size=size)
    cr.show_page()
    surface.finish()
