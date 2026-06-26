# -*- coding: utf-8 -*-
import cairo
from ..render.wheel import draw_radix


def export_pdf(chart, path, size=800):
    surface = cairo.PDFSurface(path, size, size)
    cr = cairo.Context(surface)
    draw_radix(cr, chart, size=size)
    cr.show_page()
    surface.finish()
