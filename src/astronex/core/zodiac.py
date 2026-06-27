# -*- coding: utf-8 -*-
"""Zodiac — port of ``astronex/zodiac.py`` (issue #14).

The :class:`Zodiac` class caches sign/planet glyphs as cairo paths (for
efficient drawing) and bookkeeps the colour palette used across the app.

Port notes
----------
* The original instantiated a ``cairo.Context`` inside ``__init__`` and called
  ``cr.select_font_face('Astro-Nex')``. That toy-font path does not work on this
  macOS/cairo build (see :mod:`astronex.render.glyphs`), so glyph-path caching
  uses :func:`astronex.render.glyphs.set_symbol_font`, which loads the bundled
  TTF via FreeType and pushes the real font face onto the context.
* Colours come from :mod:`astronex.core.config` (no GTK). The parse_* helpers
  there replaced the original ``gtk.gdk.color_parse``.
* Class-level caches (``Zodiac.zod``, ``Zodiac.plan``, ...) are kept as in the
  original; :meth:`reset_cache` clears them so tests get deterministic state.
"""
import cairo
from collections import deque

from . import config
from ..render.glyphs import set_symbol_font


# ---------------------------------------------------------------------------
# Constant glyph/size/category tuples (match the original exactly)
# ---------------------------------------------------------------------------
zodlet = ('q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', 'a', 's')
plantuples = (('d', 30.0, 'pers'), ('f', 32.0, 'pers'), ('h', 26.0, 'tool'),
              ('j', 26.0, 'tool'), ('k', 26.0, 'tool'), ('l', 26.0, 'tool'),
              ('g', 32.0, 'pers'), ('z', 26.0, 'trans'), ('x', 26.0, 'trans'),
              ('c', 26.0, 'trans'), ('v', 26.0, 'node'), ('b', 32.0, 'pers'),
              ('Z', 26.0, 'trans'), ('C', 26.0, 'trans'))
plagram_tuples = (('d', 24.0), ('f', 25.0), ('h', 24.0), ('j', 24.0),
                  ('k', 24.0), ('l', 25.0), ('g', 24.0), ('z', 24.0),
                  ('x', 24.0), ('c', 24.0), ('v', 22.0), ('b', 25.0))
plagram_extra = (('D', 24.0), ('f', 25.0), ('H', 24.0), ('J', 24.0),
                 ('K', 24.0), ('l', 25.0), ('g', 24.0), ('Y', 24.0),
                 ('x', 24.0), ('c', 24.0), ('V', 22.0))
crosscolors = {'card': (0.7, 0, 0.2), 'fix': (0.1, 0.1, 0.6), 'mut': (0, 0.6, 0.1)}


class Zodiac(object):
    """Caches glyphs as cairo paths and holds the colour palette.

    Instantiating populates the class-level glyph caches (once per process)
    and reads the colour palette from :mod:`config`.
    """
    zod = []
    plan = []
    extraplan = []
    aspcolors = []
    auxcolors = {}
    crosscolors = []
    plagram = []
    plagram_extra = []

    def __init__(self, style='huber'):
        # Ensure the colour map is initialised from defaults if nobody has
        # called read_config yet (e.g. in tests / headless use).
        if not config.cfgcols:
            config.init_cfgcols(config.default_colors)

        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 100, 100)
        cr = cairo.Context(surface)
        set_symbol_font(cr)

        if not Zodiac.zod:
            self.set_zod_paths(cr)
        if not Zodiac.plan:
            self.set_plan_paths(cr, style)
        if not Zodiac.plagram:
            self.set_plagram_paths(cr)
        if not Zodiac.plagram_extra:
            self.set_plagram_extra(cr)
        if not Zodiac.aspcolors:
            self.set_aspcolors()
        if not Zodiac.auxcolors:
            self.set_auxcolors()
        Zodiac.crosscolors = crosscolors

    # --- glyph path caching -------------------------------------------------
    def set_zod_paths(self, cr):
        """Cache of glyphs in symbol font for efficiency."""
        class zod_obj(object):
            pass
        cr.set_font_size(72.0)
        dq = deque(config.parse_zod_colors())
        for s in zodlet:
            z = zod_obj()
            z.let = s
            z.col = dq[0]
            dq.rotate(-1)
            z.extents = cr.text_extents(s)
            cr.text_path(s)
            z.paths = cr.copy_path()
            cr.new_path()  # critical!
            Zodiac.zod.append(z)

    def set_plan_paths(self, cr, style):
        class plan_obj(object):
            pass
        cols = config.parse_plan_colors()
        for s, size, cat in plantuples:
            p = plan_obj()
            p.let = s
            p.col = cols[cat]
            cr.set_font_size(size)
            p.extents = cr.text_extents(s)
            cr.text_path(s)
            p.paths = cr.copy_path()
            cr.new_path()
            Zodiac.plan.append(p)
        Zodiac.extraplan.append(Zodiac.plan.pop())
        Zodiac.extraplan.insert(0, Zodiac.plan.pop())
        if style == 'classic':
            Zodiac.extraplan[0], Zodiac.plan[7] = Zodiac.plan[7], Zodiac.extraplan[0]
            Zodiac.extraplan[1], Zodiac.plan[9] = Zodiac.plan[9], Zodiac.extraplan[1]

    def set_plagram_paths(self, cr):
        class plan_obj(object):
            pass
        for s, size in plagram_tuples:
            p = plan_obj()
            p.let = s
            cr.set_font_size(size)
            p.extents = cr.text_extents(s)
            cr.text_path(s)
            p.paths = cr.copy_path()
            cr.new_path()
            Zodiac.plagram.append(p)

    def set_plagram_extra(self, cr):
        class plan_obj(object):
            pass
        for s, size in plagram_extra:
            p = plan_obj()
            p.let = s
            cr.set_font_size(size)
            p.extents = cr.text_extents(s)
            cr.text_path(s)
            p.paths = cr.copy_path()
            cr.new_path()
            Zodiac.plagram_extra.append(p)

    def swap_plan_style(self):
        Zodiac.extraplan[0], Zodiac.plan[7] = Zodiac.plan[7], Zodiac.extraplan[0]
        Zodiac.extraplan[1], Zodiac.plan[9] = Zodiac.plan[9], Zodiac.extraplan[1]

    # --- colour bookkeeping -------------------------------------------------
    def set_aspcolors(self):
        aspcol = config.parse_asp_colors()
        if not self.aspcolors:
            self.aspcolors = [0] * 12
        self.aspcolors[0] = aspcol['orange']
        for i in (1, 5, 7, 11):
            self.aspcolors[i] = aspcol['green']
        for i in (2, 4, 8, 10):
            self.aspcolors[i] = aspcol['blue']
        for i in (3, 6, 9):
            self.aspcolors[i] = aspcol['red']

    def set_auxcolors(self):
        auxcol = config.parse_aux_colors()
        if not self.auxcolors:
            self.auxcolors = {}
        for cl in ('click1', 'click2', 'clicksoul', 'inv', 'low', 'transcol'):
            self.auxcolors[cl] = auxcol[cl]

    def get_crosscolors(self):
        return self.crosscolors

    def get_zodcolors(self):
        return [z.col for z in self.zod][0:4]

    def get_plancolors(self):
        cols = [pl.col for pl in self.plan]
        return [cols[i] for i in (0, 2, 7, 10)]

    def get_aspcolors(self):
        return self.aspcolors

    def get_auxcolors(self):
        return self.auxcolors

    def set_zodcolors(self):
        dq = deque(config.parse_zod_colors())
        for z in self.zod:
            z.col = dq[0]
            dq.rotate(-1)

    def set_plancolors(self):
        cols = config.parse_plan_colors()
        for p, t in zip(self.plan, plantuples):
            p.col = cols[t[2]]

    def set_allcolors(self):
        self.set_zodcolors()
        self.set_plancolors()
        self.set_aspcolors()
        self.set_auxcolors()

    @staticmethod
    def change_uk_glyphs():
        """TODO: figure how to do this (parity stub from the original)."""

    @classmethod
    def reset_cache(cls):
        """Clear the class-level glyph/colour caches (for deterministic tests)."""
        cls.zod = []
        cls.plan = []
        cls.extraplan = []
        cls.aspcolors = []
        cls.auxcolors = {}
        cls.crosscolors = []
        cls.plagram = []
        cls.plagram_extra = []
