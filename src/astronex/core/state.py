# -*- coding: utf-8 -*-
"""Global application state — port of ``astronex/state.py`` (issue #12).

This module holds the mutable, application-wide state of Astro-Nex. It is being
ported bottom-up, unit by unit, alongside the rest of milestone 2A.

Currently ported (dependency-free units):
    * The operation/category constant lists (``opdouble``, ``datlist``, ...).
    * :class:`Locality` — a plain holder for a geographic locality.

Not yet ported (blocked on sibling 2A issues):
    * :class:`Current` — depends on ``database`` (#11), ``chart.Chart`` and
      ``NeXDate``. Will be added once the database layer lands.

The constants must match the original Astro-Nex (Py2) exactly: they drive the
toolbar/chart-type selection and are compared against the original via the
golden/behaviour tests.
"""
from collections import deque


# ---------------------------------------------------------------------------
# Operation / category constant lists
#
# These deques are module-level in the original and referenced directly by the
# GUI (boss, mainnb, oppanel). They are kept as deques (not lists) because the
# original rotates them in-place via set_opdelta.
# ---------------------------------------------------------------------------
datlist = deque(['dat_nat', 'dat_house', 'dat_nod',
                 'prog_nat', 'prog_nod', 'prog_local', 'prog_soul'])
dialist = deque(['dyn_cuad', 'dyn_cuad2', 'dyn_stars'])
biolist = deque(['bio_nat', 'bio_nod', 'bio_soul'])
tranlist = deque(['draw_transits', 'rad_and_transit'])
clicklist = deque(['click_hh', 'click_nn', 'click_hn', 'click_nh',
                   'subject_click', 'click_rr', 'click_bridge'])
opdouble = deque([
    'draw_nat', 'draw_house', 'draw_nod', 'draw_soul', 'draw_dharma',
    'draw_ur_nodal', 'draw_local', 'draw_prof', 'draw_int', 'draw_single',
    'draw_radsoul', 'draw_planetogram'])
optriplepair = deque(['click_hh', 'click_nn', 'click_hn', 'click_nh',
                      'click_ss', 'click_rr', 'subject_click'])

listlabels = {
    'opdouble': opdouble, 'charts': opdouble,
    'data': datlist, 'clicks': clicklist, 'bio': biolist,
    'diagram': dialist, 'transit': tranlist,
    'double1': opdouble, 'double2': opdouble,
    'triple1': opdouble, 'triple2': optriplepair,
}


# ---------------------------------------------------------------------------
# PersonInfo
# ---------------------------------------------------------------------------
class PersonInfo(object):
    """The active person's name, with a default placeholder.

    In the original this used a gettext-translated placeholder
    (``_("sin_nombre%d") % count``). We keep a deterministic, untranslated
    placeholder here so the default name is stable and testable; the GUI/i18n
    layer (milestone 2D) is responsible for any user-facing translation.
    """
    count = 1

    def __init__(self):
        self.first = "sin_nombre%d" % self.count
        self.last = ""

    def set_first(self, noname=False):
        if noname:
            self.first = ''
        else:
            self.first = "sin_nombre%d" % self.count
            PersonInfo.count += 1


# ---------------------------------------------------------------------------
# Locality
# ---------------------------------------------------------------------------
class Locality(object):
    """Data for a locality (geographic place).

    A plain attribute holder. Decimal coordinates (``latdec``/``longdec``) start
    as ``None`` to signal "unset", matching the original; the textual
    ``latitud``/``longitud`` start as empty strings.
    """
    def __init__(self):
        self.country = ""
        self.country_code = ""
        self.city = ""
        self.region = ""
        self.region_code = ""
        self.latitud = ""
        self.longitud = ""
        self.latdec = None
        self.longdec = None
        self.zone = ""
