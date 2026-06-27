# -*- coding: utf-8 -*-
"""Aspect geometry (the visual shapes drawn between planet pairs).

Ported verbatim from legacy drawing/aspects.py. These are PURE cairo drawing
classes -- they draw into a passed ``cairo.Context`` and have ZERO boss/GUI/
surface coupling. An aspect is a dict with keys ``p1, p2`` (ecliptic
longitudes, degrees), ``f1, f2`` (orb factors), ``col`` (RGB tuple). The port's
``Chart.aspects()`` produces these dicts; ``arrange`` maps planet indices to
screen longitudes before drawing.

The five Huber aspect shapes:
  * ConjunctioAspect -- filled lens/vesica between two points
  * UnilateralAspect -- half-dashed / half-solid line (one-directional)
  * GoodwillAspect   -- simple dashed chord
  * AgePointAspect   -- dashed line from a planet to the age-point (pe)
  * FususAspect      -- the default curved "spindle/bowtie" shape
"""
import math
from math import pi as PI

RAD = PI / 180


class ConjunctioAspect(object):
    def draw(self, cr, r, aspects, filter, extend=None):
        if extend:
            ex = extend
            fdivfac = 20
        else:
            ex = 1.105
            fdivfac = 10

        cr.save()
        for asp in aspects:
            p1 = asp["p1"] % 360.0
            p2 = asp["p2"] % 360.0
            f1 = asp["f1"]
            f2 = asp["f2"]
            col = asp["col"]
            x1 = r * math.cos(p1 * RAD)
            y1 = r * math.sin(p1 * RAD)
            x2 = r * math.cos(p2 * RAD)
            y2 = r * math.sin(p2 * RAD)
            f1 = ex * 0.99 if f1 > 1 else 1 + f1 / fdivfac
            f2 = ex * 0.99 if f2 > 1 else 1 + f2 / fdivfac
            dis = abs(p1 - p2)
            dis = min(dis, 360 - dis)
            if dis == 0.0 or filter:  # zero div when same chart
                da = 3.0
            else:
                da = (((dis / asp["f1"] + dis / asp["f2"]) / 2) - dis) / 2
            if da < 0:
                da = -da
            a1 = min(p1, p2) - da
            a2 = max(p1, p2) + da
            if a1 < 0:
                a1 += 360.0
            if a2 < 0:
                a2 += 360.0
            a1 %= 360.0
            a2 %= 360.0
            if min(p1, p2) != p1:
                a1, a2 = a2, a1

            ebx1 = r * ex * math.cos(a1 * RAD)
            eby1 = r * ex * math.sin(a1 * RAD)
            ebx2 = r * ex * math.cos(a2 * RAD)
            eby2 = r * ex * math.sin(a2 * RAD)

            cr.set_source_rgb(1, 0.3, 0)
            cr.move_to(x1 * f1, y1 * f1)
            cr.line_to(ebx1, eby1)
            if (a1 < a2 and a2 - a1 < 180.0) or (a1 - a2) > 180.0:
                cr.arc(0, 0, r * ex, a1 * RAD, a2 * RAD)
            else:
                cr.arc_negative(0, 0, r * ex, a1 * RAD, a2 * RAD)
            cr.line_to(x2 * f2, y2 * f2)
            cr.close_path()
            cr.fill()

            cr.set_source_rgb(*col)
            cr.move_to(x1 * f1, y1 * f1)
            cr.line_to(x1 * ex, y1 * ex)
            cr.line_to(x2 * ex, y2 * ex)
            cr.line_to(x2 * f2, y2 * f2)
            cr.close_path()
            cr.fill()
        cr.restore()


class UnilateralAspect(object):
    def __init__(self, baseline):
        self.lw = baseline

    def draw(self, cr, r, aspects):
        cr.save()
        cr.set_line_width(0.6 * float(self.lw))
        for asp in aspects:
            p1, p2 = asp["p1"], asp["p2"]
            f1, f2 = asp["f1"], asp["f2"]
            col = asp["col"]
            x1 = r * math.cos(p1 * RAD)
            y1 = r * math.sin(p1 * RAD)
            x2 = r * math.cos(p2 * RAD)
            y2 = r * math.sin(p2 * RAD)
            if f1 < f2:
                x2, x1 = x1, x2
                y2, y1 = y1, y2
            xx = (x2 + x1) / 2
            yy = (y2 + y1) / 2
            cr.set_source_rgb(*col)
            cr.set_dash([4, 3, 12, 4, 18, 5, 24, 6, 30, 6, 36, 6, 48, 6, 60, 6], 0)
            cr.move_to(x1, y1)
            cr.line_to(xx, yy)
            cr.stroke()
            cr.set_dash([1, 0], 0)
            cr.set_source_rgb(*col)
            cr.move_to(xx, yy)
            cr.line_to(x2, y2)
            cr.stroke()
        cr.restore()


class GoodwillAspect(object):
    def __init__(self, baseline):
        self.lw = baseline

    def draw(self, cr, r, aspects):
        cr.save()
        cr.set_dash([12, 6], 2)
        cr.set_line_width(0.7 * float(self.lw))
        for asp in aspects:
            p1, p2 = asp["p1"], asp["p2"]
            col = asp["col"]
            x1 = r * math.cos(p1 * RAD)
            y1 = r * math.sin(p1 * RAD)
            x2 = r * math.cos(p2 * RAD)
            y2 = r * math.sin(p2 * RAD)
            cr.set_source_rgb(*col)
            cr.move_to(x1, y1)
            cr.line_to(x2, y2)
            cr.stroke()
        cr.restore()


class AgePointAspect(object):
    def draw(self, cr, r, aspects, pe):
        cr.save()
        cr.set_dash([3, 3], 2)
        for asp in aspects:
            p1 = asp["p1"]
            col = asp["col"]
            f = asp["f"]
            x1 = r * math.cos(p1 * RAD)
            y1 = r * math.sin(p1 * RAD)
            x2 = r * math.cos(pe * RAD)
            y2 = r * math.sin(pe * RAD)
            awidth = 1.2 - f
            if awidth < 0.3:
                awidth = 0.3
            cr.set_line_width(awidth)
            cr.set_source_rgb(*col)
            cr.move_to(x1, y1)
            cr.line_to(x2, y2)
            cr.stroke()
        cr.restore()


class FususAspect(object):
    """Normal aspect (fusus form) -- the default curved spindle/bowtie shape."""
    def draw(self, cr, r, aspects):
        cr.save()
        scl = r * 0.00065
        for asp in aspects:
            p1, p2 = asp["p1"], asp["p2"]
            f1, f2 = asp["f1"], asp["f2"]
            col = asp["col"]
            f = 3 * ((5 - 5 * f1) + (5 - 5 * f2)) * scl
            x1 = r * math.cos(p1 * RAD)
            y1 = r * math.sin(p1 * RAD)
            x2 = r * math.cos(p2 * RAD)
            y2 = r * math.sin(p2 * RAD)
            xx = (x2 + x1) / 2
            yy = (y2 + y1) / 2
            cr.set_source_rgb(*col)
            angle = math.atan((y2 - y1) / (x2 - x1)) / RAD
            dx = math.cos((90 + angle) * RAD) * f
            dy = math.sin((90 + angle) * RAD) * f
            cr.move_to(x1, y1)
            cr.curve_to((xx + dx), (yy + dy), (xx + dx), (yy + dy), x2, y2)
            cr.curve_to((xx - dx), (yy - dy), (xx - dx), (yy - dy), x1, y1)
            cr.fill_preserve()
            cr.set_line_width(0.425)
            cr.stroke()
        cr.restore()
