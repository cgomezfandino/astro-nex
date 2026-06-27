# -*- coding: utf-8 -*-
"""Huber dynamics diagrams: signs/houses/energy/differences/bars + low-points.

Ported from legacy drawing/diagrams.py. These are the dynamic-distribution
diagrams that visualize the element/cross strength (dynstar_signs/houses,
dyncalc_list, dyncalc_stress) already ported in core/chart.py.

The composite view ``draw_dyn_stars`` lays out the five sub-diagrams in a grid
(mirroring legacy dyn_stars): signs (top-left), houses (top-right), energy
(bottom-left), differences (bottom-right), bars (centred). The interactive
quadrant diagram (dyn_cuad/dyn_cuad2, click-chart dependent) is deferred.

Pure cairo: draws into a passed ``cairo.Context``; replaces legacy pango with
cr.show_text. No boss/GUI coupling. The caller supplies the chart.
"""
import math
import cairo
from math import pi as PI

RAD = PI / 180

# Cross colours (match legacy diagrams.py:27-29 and core/zodiac.py crosscolors).
CARD = (0.7, 0, 0.2)
FIX = (0.1, 0.1, 0.6)
MUT = (0, 0.6, 0.1)
# Element-ish palette cycled by i%4 (legacy used zodiac aux colours).
ZODCOLS = [(0.85, 0.55, 0.1), (0.2, 0.6, 0.25), (0.55, 0.35, 0.75), (0.8, 0.3, 0.3)]


def _title(cr, text, size=8):
    cr.select_font_face("sans-serif")
    cr.set_font_size(size)
    cr.set_source_rgb(0, 0, 0.6)
    cr.show_text(text)


def draw_dyn_stars(cr, chart, width=600, height=600):
    """Composite dynamics view: signs, houses, energy, differences, bars."""
    if not getattr(chart, "planets", None) or len(getattr(chart, "houses", [])) < 12:
        return
    cx = cy = width / 2.5
    cr.save()
    cr.set_line_width(0.6)

    _dyn_signs(cr, cx, cy, chart)
    cr.translate(cx * 1.5, 0)
    _dyn_houses(cr, cx, cy, chart)
    cr.translate(-cx * 1.5, cy * 1.5)
    _dyn_energy(cr, cx, cy, chart)
    cr.translate(cx * 1.5, 0)
    _dyn_differences(cr, cx, cy, chart)
    cr.translate(-cx * 0.65, -cx * 0.65)
    cr.scale(0.9, 0.9)
    _dyn_bars(cr, cx * 0.95, cy, chart)
    cr.restore()


def _dyn_signs(cr, w, h, chart):
    dyns = chart.dynstar_signs()
    cx, cy = w / 2, h / 2
    radius = min(cx, cy)
    cr.save()
    cr.translate(cx, cy)
    r = radius * 0.7
    ro = radius * 0.34
    ru = (r - ro) / 50
    cr.set_source_rgb(0, 0, 0)
    cr.arc(0, 0, r, 0, 180 * PI)
    cr.stroke()
    for i, p in enumerate(dyns):
        off = 180 - i * 30
        cr.set_source_rgb(*ZODCOLS[i % 4])
        cr.move_to((ro + p * ru) * math.cos(off * RAD),
                   (ro + p * ru) * math.sin(off * RAD))
        cr.line_to(ro * math.cos((off + 15) * RAD),
                   ro * math.sin((off + 15) * RAD))
        cr.arc_negative(0, 0, ro, (off + 15) * RAD, (off - 15) * RAD)
        cr.close_path()
        cr.fill()
    cr.move_to(-cx + 3, -cy + 3)
    _title(cr, "Diagrama de signos")
    cr.restore()


def _dyn_houses(cr, w, h, chart):
    dynh = chart.dynstar_houses()
    cx, cy = w / 2, h / 2
    radius = min(cx, cy)
    cr.save()
    cr.translate(cx, cy)
    r = radius * 0.7
    ro = radius * 0.34
    ru = (r - ro) / 50
    cr.set_source_rgb(0, 0, 0)
    cr.arc(0, 0, r, 0, 180 * PI)
    cr.stroke()
    for i, p in enumerate(dynh):
        off = 180 - i * 30
        cr.set_source_rgb(*ZODCOLS[i % 4])
        cr.move_to((ro + p * ru) * math.cos(off * RAD),
                   (ro + p * ru) * math.sin(off * RAD))
        cr.line_to(ro * math.cos((off + 15) * RAD),
                   ro * math.sin((off + 15) * RAD))
        cr.arc_negative(0, 0, ro, (off + 15) * RAD, (off - 15) * RAD)
        cr.close_path()
        cr.fill()
    cr.move_to(-cx + 3, -cy + 3)
    _title(cr, "Diagrama de casas")
    cr.restore()


def _dyn_energy(cr, w, h, chart):
    dyns = chart.dynstar_signs()
    dynh = chart.dynstar_houses()
    cx, cy = w / 2, h / 2
    radius = min(cx, cy)
    cr.save()
    cr.translate(cx, cy)
    r = radius * 0.7
    ro = radius * 0.34
    ru = (r - ro) / 50
    cr.set_source_rgb(0, 0, 0)
    cr.arc(0, 0, r, 0, 180 * PI)
    cr.stroke()
    for i in range(12):
        off = 180 - i * 30
        ps = dyns[i]; ph = dynh[i]
        outer, inner = (ps, ph) if ps >= ph else (ph, ps)
        cr.set_source_rgb(*ZODCOLS[i % 4])
        cr.move_to((ro + outer * ru) * math.cos(off * RAD),
                   (ro + outer * ru) * math.sin(off * RAD))
        cr.line_to(ro * math.cos((off + 15) * RAD),
                   ro * math.sin((off + 15) * RAD))
        cr.arc_negative(0, 0, ro, (off + 15) * RAD, (off - 15) * RAD)
        cr.close_path()
        cr.fill()
        cr.set_source_rgb(0.8, 0.8, 0.8)
        cr.move_to((ro + inner * ru) * math.cos(off * RAD),
                   (ro + inner * ru) * math.sin(off * RAD))
        cr.line_to(ro * math.cos((off + 15) * RAD),
                   ro * math.sin((off + 15) * RAD))
        cr.arc_negative(0, 0, ro, (off + 15) * RAD, (off - 15) * RAD)
        cr.close_path()
        cr.fill()
    cr.move_to(-cx + 3, cy - 13)
    _title(cr, "Diagrama de energia")
    cr.restore()


def _dyn_differences(cr, w, h, chart):
    dyns = chart.dynstar_signs()
    dynh = chart.dynstar_houses()
    stress = abs(chart.dyncalc_stress())
    if stress > 100:
        stress = 100
    if stress < 3:
        stress = 3
    cx, cy = w / 2, h / 2
    radius = min(cx, cy)
    cr.save()
    cr.translate(cx, cy)
    fac = 0.7
    r = radius * fac
    ri = radius * (fac - (stress / 450.0))
    rui = (r - ri) / stress
    cr.set_source_rgb(0, 0, 0)
    cr.arc(0, 0, ri, 0, 180 * PI)
    cr.stroke()
    cr.arc(0, 0, r, 0, 180 * PI)
    cr.stroke()
    for i in range(12):
        off = 180 - i * 30
        ps = dyns[i]; ph = dynh[i]
        dif = ph - ps
        cr.set_source_rgb(*ZODCOLS[i % 4])
        inn = r - ps * rui
        cr.move_to(r * math.cos(off * RAD), r * math.sin(off * RAD))
        cr.line_to(inn * math.cos(off * RAD), inn * math.sin(off * RAD))
        cr.stroke()
    cr.move_to(-cx + 3, cy - 13)
    _title(cr, "Diagrama de diferencias")
    cr.restore()


def _dyn_bars(cr, w, h, chart):
    srow, hrow, diff = chart.dyncalc_list()
    cols = [CARD, FIX, MUT, ZODCOLS[0], ZODCOLS[1], ZODCOLS[2], ZODCOLS[3]]
    cr.save()
    barwidth = w * 0.9
    columnwidth = barwidth / 8
    cbase = h * 0.47
    vstep = (h / 2 * 0.9) / 90

    cr.set_source_rgb(0.44, 0.32, 0.25)
    cr.rectangle(w * 0.05, cbase, barwidth, h * 0.06)
    cr.fill()

    # house bars (up), sign bars (down), diff triangles
    for i, hr in enumerate(hrow[1:]):
        cheight = int(hr) * vstep
        cr.set_source_rgb(*cols[i])
        cr.rectangle(w * 0.05 * 1.2 + (i + 1) * columnwidth,
                     cbase - cheight, columnwidth * 0.7, cheight)
        cr.fill()
    cdownbase = h - cbase
    for i, sr in enumerate(srow[1:]):
        cheight = int(sr) * vstep
        cr.set_source_rgb(*cols[i])
        cr.rectangle(w * 0.05 * 1.2 + (i + 1) * columnwidth,
                     cdownbase, columnwidth * 0.7, cheight)
        cr.fill()
    cr.set_source_rgb(0.85, 0.85, 0.85)
    for i, dt in enumerate(diff[1:]):
        t = int(dt)
        ini = w * 0.05 * 1.2 + (i + 1) * columnwidth
        theight = t * vstep
        base = cbase if t > 0 else cdownbase
        cr.move_to(ini, base)
        cr.line_to(ini + columnwidth * 0.7, base)
        cr.line_to(ini + columnwidth * 0.7 / 2, base - theight)
        cr.close_path()
        cr.fill()
    cr.move_to(3, 3)
    _title(cr, "Diagrama de barras")
    cr.restore()
