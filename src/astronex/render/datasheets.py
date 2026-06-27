# -*- coding: utf-8 -*-
"""Data-sheet renderers: tabular chart data (planets, houses, aspects, dynamics).

Ported from legacy drawing/datasheets.py. These are TEXT TABLES (not circles):
planet positions, the 12x12 aspect matrix, the element/cross dynamics table,
and the Huber rays. They consume the already-ported core/chart.py dynamics
methods (which_all_signs/houses, aspects, dyncalc_list, rays_calc).

The legacy used pango layouts + tab arrays; this port uses absolute positioning
with ``cr.show_text`` and the bundled Astro-Nex symbol font for glyphs (via
``render.glyphs``), mirroring how ``render/wheel.py`` renders glyph text.

Pure cairo: draws into a passed ``cairo.Context``, no boss/GUI coupling. The
caller supplies the ``chart`` (a core.chart.Chart) and a width/height canvas.
"""
import math

from . import glyphs

# Symbol-font characters (Astro-Nex font) for planets and signs, matching the
# legacy planlet/zodlet tables (datasheets.py:59-61).
PLANLET = ['d', 'f', 'h', 'j', 'k', 'l', 'g', 'z', 'x', 'c', 'v']
ZODLET = ('q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', 'a', 's')
ASPLET = ('1', '2', '3', '4', '5', '6', '7', '6', '5', '4', '3', '2')

ROMAN = ["I", "II", "III", "IV", "V", "VI",
         "VII", "VIII", "IX", "X", "XI", "XII"]


def _text(cr, x, y, s, rgb=(0, 0, 0), size=9):
    """Place a text string (left-baseline at x,y) in the sans font."""
    cr.select_font_face("sans-serif")
    cr.set_font_size(size)
    cr.set_source_rgb(*rgb)
    cr.move_to(x, y)
    cr.show_text(s)


def _glyph_char(cr, x, y, ch, rgb=(0, 0, 0), size=11):
    """Place one Astro-Nex symbol-font glyph centred roughly at (x,y)."""
    cr.set_font_size(size)
    cr.set_source_rgb(*rgb)
    ext = cr.text_extents(ch)
    cr.move_to(x - ext.width / 2 - ext.x_bearing,
               y - ext.height / 2 - ext.y_bearing)
    cr.show_text(ch)


def draw_datasheet(cr, chart, kind="radix", width=600, height=800):
    """Render a radix data sheet (planets + aspect matrix + dynamics + rays).

    Kind 'radix' is implemented; 'house'/'nodal' swap the planet/house table and
    the aspect kind (deferred to keep this slice focused -- the radix sheet is
    the canonical data view).
    """
    if not getattr(chart, "planets", None) or len(getattr(chart, "houses", [])) < 12:
        return
    cr.save()
    cr.set_line_width(0.5)

    # title underline
    cr.set_source_rgb(0, 0, 0)
    cr.move_to(50, 80)
    cr.line_to(width - 60, 80)
    cr.stroke()

    _planets_table(cr, chart)
    _aspect_matrix(cr, chart, kind="radix")
    _dynamics_table(cr, chart)
    _rays_table(cr, chart)
    cr.restore()


def _planets_table(cr, chart):
    """Planets (sign glyph + degree), houses (cusp + low points), inverted points."""
    use_font = glyphs.set_symbol_font(cr)
    _text(cr, 50, 86, "Planetas", (0, 0, 0.4), size=9)
    _text(cr, 200, 86, "Casas", (0, 0, 0.4), size=9)

    signs = chart.which_all_signs()
    hh = chart.which_all_houses()

    for i in range(11):
        y = 105 + i * 16
        # planet degree text
        _text(cr, 70, y, signs[i]["deg"], (0, 0, 0), size=9)
        # planet glyph
        if use_font:
            _glyph_char(cr, 58, y - 4, PLANLET[i], (0.6, 0, 0), size=11)

    cr.set_source_rgb(0, 0, 0)
    for i in range(12):
        y = 105 + i * 16
        d, ii, l = hh[i]
        row = "%s  %s  %s  %s" % (ROMAN[i], d["deg"], ii["deg"], l["deg"])
        _text(cr, 200, y, row, (0, 0, 0), size=9)


def _aspect_matrix(cr, chart, kind="radix"):
    """The 12x12 aspect grid: rows/cols are planets, cells are aspect glyphs."""
    hm, vm = 50, 325
    ho, vo = 44, 20
    use_font = glyphs.set_symbol_font(cr)

    _text(cr, hm, vm - 20, "Tabla de aspectos", (0, 0, 0.4), size=9)

    # grid lines
    cr.set_source_rgb(0, 0, 0)
    cr.set_line_width(0.4)
    for i in range(12):
        cr.move_to(hm, vm + vo * i)
        cr.line_to(hm + 484, vm + vo * i)
        cr.stroke()
    for i in range(12):
        cr.move_to(hm + ho * i, vm)
        cr.line_to(hm + ho * i, vm + vo * 11)
        cr.stroke()

    try:
        aspects = chart.aspects(kind)
    except Exception:
        aspects = []
    # place each aspect's glyph at the (p1,p2) cell
    for asp in aspects:
        p1, p2 = asp.get("p1"), asp.get("p2")
        a = asp.get("a")
        if p1 is None or p2 is None or a is None:
            continue
        if p1 >= 11 or p2 >= 11:
            continue
        cx = hm + ho * (min(p1, p2) + 1) + ho / 2
        cy = vm + vo * (max(p1, p2) + 1) - 4
        if use_font:
            _glyph_char(cr, cx, cy, ASPLET[a % 12], (0.2, 0.2, 0.4), size=11)
        else:
            _text(cr, cx - 4, cy + 4, str(a % 12), (0.2, 0.2, 0.4), size=9)


def _dynamics_table(cr, chart):
    """Element/cross dynamics: 3 rows (signs/houses/diff) x 8 columns."""
    hm, vm = 50, 680
    ho, vo = 44, 20
    headers = ("Total", "Card", "Fija", "Mut", "Fuego", "Tierra",
               "Aire", "Agua")

    _text(cr, hm, vm - 44, "Calculos dinamicos", (0, 0, 0.4), size=9)
    for i, htext in enumerate(headers):
        _text(cr, hm + ho * i, vm - 20, htext, (0, 0, 0.4), size=9)

    rows = chart.dyncalc_list()  # [srow, hrow, dif] -- string lists
    for j, row in enumerate(rows):
        for i in range(min(8, len(row))):
            _text(cr, hm + 8 + ho * i, vm + vo * j, row[i].rjust(3), (0, 0, 0), size=9)

    # framing lines
    cr.set_source_rgb(0, 0, 0)
    cr.set_line_width(0.4)
    cr.move_to(hm, vm - 4); cr.line_to(hm + ho * 8, vm - 4)
    cr.move_to(hm, vm + vo * 3); cr.line_to(hm + ho * 8, vm + vo * 3)
    cr.stroke()


def _rays_table(cr, chart):
    """Huber rays: a personal-ray number + planet ray values."""
    hm, vm = 426, 620
    try:
        rays = chart.rays_calc()
    except Exception:
        rays = []
    if not rays:
        return
    _text(cr, hm + 10, vm + 16, "Carta de Rayos", (0, 0, 0.4), size=9)
    _text(cr, hm + 10, vm + 38, str(rays[0]), (0, 0, 0), size=9)
    rest1 = " ".join(str(r) for r in rays[1:4])
    rest2 = "(%s) %s" % (" ".join(str(r) for r in rays[4:7]), rays[7])
    _text(cr, hm + 26, vm + 38, rest1, (0, 0, 0), size=9)
    _text(cr, hm + 63, vm + 38, rest2, (0, 0, 0), size=9)
