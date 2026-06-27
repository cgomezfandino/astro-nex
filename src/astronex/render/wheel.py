# -*- coding: utf-8 -*-
"""Clean, self-contained cairo renderer for the radix (birth) wheel.

This is a deliberately fresh renderer that consumes the ported ``Chart`` model
and produces a recognizable Huber-style radix wheel. It does NOT depend on GTK,
pango, or any legacy drawing module (coredraw.py / roundedcharts.py). Pixel-
faithful reproduction of the original (colour zones, low points, age-point
spiral) is a later milestone; this v1 aims for "clearly a radix chart".

Layers drawn, outermost to innermost:
  - outer circle
  - 12 zodiac sign sectors (boundaries every 30 deg from the Ascendant) with a
    sign glyph centred in each sector on the outer ring
  - inner circle bounding the house ring
  - 12 house cusp lines at the chart's cusp longitudes, with house-number labels
  - planets as glyphs on a mid-radius ring, positioned by ecliptic longitude
  - aspect lines connecting planet pairs from chart.aspects(), faint, across
    the centre

Orientation: the Ascendant (chart.houses[0]) sits on the LEFT (screen angle
pi) and ecliptic longitude increases counter-clockwise -- the conventional
astrological layout.
"""

import math

from . import glyphs


def _pos(lon_deg, radius, asc, cx, cy):
    """Map an ecliptic longitude to a screen (x, y) on a circle of ``radius``.

    Ascendant on the left (screen angle pi); longitude increases CCW. The
    ``cy - r*sin`` flips cairo's downward y axis so increasing longitude runs
    counter-clockwise on screen.
    """
    theta = math.pi - (lon_deg - asc) * math.pi / 180.0
    return cx + radius * math.cos(theta), cy - radius * math.sin(theta)


def _glyph(cr, ch, x, y, size, use_font):
    """Draw a single glyph/label centred at (x, y).

    If the symbol font is active, ``ch`` is the symbol-font character; otherwise
    ``ch`` is treated as a short fallback label in the default sans font.
    """
    if use_font:
        cr.set_font_size(size)
    else:
        cr.select_font_face("sans-serif")
        cr.set_font_size(size * 0.55)
    try:
        ext = cr.text_extents(ch)
    except Exception:
        return
    cr.move_to(x - ext.width / 2 - ext.x_bearing, y - ext.height / 2 - ext.y_bearing)
    cr.show_text(ch)


def draw_radix(cr, chart, size=600, cfg=None):
    """Render a radix wheel for ``chart`` onto cairo context ``cr``.

    Equivalent to ``draw_wheel(cr, chart, kind='radix', size=size)``. Kept as an
    alias for existing callers (surfaces/png.py, surfaces/pdf.py, the GUI).
    """
    draw_wheel(cr, chart, kind="radix", size=size, cfg=cfg)


def _planet_list(chart, kind):
    """Return the ecliptic-longitude list for the given chart ``kind``.

    Mirrors legacy roundedcharts.<Type>Chart.get_planets(), which delegate to the
    already-ported core/chart.py data transforms:
      radix    : chart.planets
      soul     : chart.soulplan()
      house    : chart.house_plan_long()
      dharma   : chart.house_plan_long()  (same data; differs only in drawing)
      nodal    : chart.planets with [10] = houses[0] (node<->asc swap)
      ur_nodal : chart.urnodplan()
      local    : chart.planets (houses recomputed by the caller)
    """
    if kind == "soul":
        return list(chart.soulplan())
    if kind in ("house", "dharma"):
        return list(chart.house_plan_long())
    if kind == "ur_nodal":
        return list(chart.urnodplan())
    if kind == "nodal":
        pl = list(chart.planets)
        if len(pl) > 10 and len(chart.houses) > 0:
            pl[10] = chart.houses[0]
        return pl
    # radix / local
    return list(chart.planets)


def draw_wheel(cr, chart, kind="radix", size=600, cfg=None):
    """Render a single-wheel Huber chart of the given ``kind``.

    Kinds: radix, soul, house, dharma, nodal, ur_nodal, local. They differ in
    which planet-longitude list is drawn and (for house/dharma/nodal) whether
    the houses are equal-30 vs the natal Koch cusps; the wheel structure
    (sign ring, cusps, planets, aspects) is shared.

    Guards against an empty/uncalculated chart: if there are no planets or no
    houses, it draws just the outer circle and returns -- never raises.

    For ``local``, the caller should recompute chart.houses for the relocated
    place (via core.ephemeris.local_houses) before calling; this function only
    draws the provided houses.
    """
    cx = cy = size / 2.0
    radius = size * 0.45
    cr.set_line_width(max(1.0, size / 600.0))

    # --- outer circle (always safe to draw) ---
    cr.set_source_rgb(0, 0, 0)
    cr.arc(cx, cy, radius, 0, 2 * math.pi)
    cr.stroke()

    houses = getattr(chart, "houses", None) or []
    if len(houses) < 12:
        return
    try:
        planets = _planet_list(chart, kind)
    except Exception:
        return
    if not planets:
        return

    asc = houses[0]

    # Ring radii.
    sign_ring = radius                 # outer band: zodiac signs
    inner_circle = radius * 0.80       # boundary between sign band and house ring
    house_label_ring = radius * 0.74   # house number labels just inside
    planet_ring = radius * 0.55        # planets on a mid ring
    aspect_ring = radius * 0.50        # aspect lines drawn from here inward
    cusp_inner = radius * 0.30         # inner extent of the house cusp lines

    use_font = glyphs.set_symbol_font(cr)

    # --- zodiac sign sectors + glyphs ---
    asc_sign_start = math.floor(asc / 30.0) * 30.0
    for i in range(12):
        boundary = asc_sign_start + i * 30.0
        bx, by = _pos(boundary, sign_ring, asc, cx, cy)
        ix, iy = _pos(boundary, inner_circle, asc, cx, cy)
        cr.set_source_rgb(0.0, 0.0, 0.0)
        cr.move_to(ix, iy)
        cr.line_to(bx, by)
        cr.stroke()

    # inner circle bounding the house ring
    cr.set_source_rgb(0, 0, 0)
    cr.arc(cx, cy, inner_circle, 0, 2 * math.pi)
    cr.stroke()

    # sign glyphs centred in each 30-deg sector on the sign band
    glyph_ring = (sign_ring + inner_circle) / 2.0
    glyph_size = size * 0.045
    cr.set_source_rgb(0.15, 0.15, 0.45)
    for i in range(12):
        sign_index = (int(asc_sign_start / 30.0) + i) % 12
        mid = asc_sign_start + i * 30.0 + 15.0
        gx, gy = _pos(mid, glyph_ring, asc, cx, cy)
        if use_font:
            _glyph(cr, glyphs.ZODIAC_GLYPHS[sign_index], gx, gy, glyph_size, True)
        else:
            _glyph(cr, str(sign_index), gx, gy, glyph_size, False)

    # --- house cusp lines + number labels ---
    cr.set_line_width(max(1.0, size / 600.0))
    for i in range(12):
        cusp = houses[i]
        x0, y0 = _pos(cusp, inner_circle, asc, cx, cy)
        cr.set_source_rgb(0.4, 0.4, 0.4)
        xin, yin = _pos(cusp, cusp_inner, asc, cx, cy)
        cr.move_to(x0, y0)
        cr.line_to(xin, yin)
        cr.stroke()
        label_lon = cusp + 4.0
        lx, ly = _pos(label_lon, house_label_ring, asc, cx, cy)
        cr.set_source_rgb(0.3, 0.3, 0.3)
        _glyph(cr, str(i + 1), lx, ly, size * 0.030, False)

    # --- aspect lines (faint) between the drawn planet positions ---
    try:
        aspects = chart.aspects(kind=("house" if kind in ("house", "dharma") else
                                      "soul" if kind == "soul" else "radix"))
    except Exception:
        aspects = []
    cr.set_line_width(max(0.6, size / 1000.0))
    cr.set_source_rgba(0.2, 0.4, 0.8, 0.45)
    for asp in aspects:
        p1 = asp.get("p1")
        p2 = asp.get("p2")
        if p1 is None or p2 is None:
            continue
        if p1 >= len(planets) or p2 >= len(planets):
            continue
        ax, ay = _pos(planets[p1], aspect_ring, asc, cx, cy)
        bx, by = _pos(planets[p2], aspect_ring, asc, cx, cy)
        cr.move_to(ax, ay)
        cr.line_to(bx, by)
        cr.stroke()

    # --- planets as glyphs on the mid ring ---
    if use_font:
        glyphs.set_symbol_font(cr)
    pl_size = size * 0.045
    cr.set_source_rgb(0.6, 0.0, 0.0)
    n_planets = min(len(planets), len(glyphs.PLANET_GLYPHS))
    for i in range(n_planets):
        lon = planets[i]
        tx0, ty0 = _pos(lon, planet_ring + size * 0.03, asc, cx, cy)
        tx1, ty1 = _pos(lon, planet_ring + size * 0.05, asc, cx, cy)
        cr.set_line_width(max(0.8, size / 800.0))
        cr.set_source_rgb(0.5, 0.0, 0.0)
        cr.move_to(tx0, ty0)
        cr.line_to(tx1, ty1)
        cr.stroke()
        px, py = _pos(lon, planet_ring, asc, cx, cy)
        cr.set_source_rgb(0.6, 0.0, 0.0)
        if use_font:
            _glyph(cr, glyphs.PLANET_GLYPHS[i], px, py, pl_size, True)
        else:
            _glyph(cr, str(i), px, py, pl_size, False)
