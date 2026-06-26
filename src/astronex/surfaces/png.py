# -*- coding: utf-8 -*-
import cairo
from ..render.wheel import draw_radix


def export_png(chart, path, size=800):
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, size, size)
    cr = cairo.Context(surface)
    cr.set_source_rgb(1, 1, 1)
    cr.paint()
    draw_radix(cr, chart, size=size)
    surface.write_to_png(path)
