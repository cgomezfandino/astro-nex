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


# ---------------------------------------------------------------------------
# Current (application-wide singleton state)
# ---------------------------------------------------------------------------
import os
import pickle

from . import database
from .chart import Chart
from .nexdate import NeXDate


class Current(object):
    """Singleton holding the application's mutable state.

    The original used ``__new__`` to cache a single instance for the process.
    Construction wires up the four core charts (master/click/now/calc), the
    active locality, the operation-mode bookkeeping and the persisted pools.

    Port notes:
        * ``app`` (original) is optional; for headless/test use pass ``homedir``
          (the user config dir where ``charts.db`` / pickles live). When neither
          is given, ``~/.astronex`` is used.
        * ``NeXDate`` is partially ported (no ``set_now``/``dateforstore`` yet);
          methods that need those (``setchart``/``init_nowchart``/``set_now``)
          are ported structurally but rely on the missing pieces landing in 2B.
        * :meth:`_reset_singleton` clears the cached instance for deterministic
          tests (the original never needed it because there was exactly one app).
    """
    datab = database

    def __new__(cls, app=None, homedir=None):
        it = cls.__dict__.get("_singleton_instance")
        if it:
            return it
        cls._singleton_instance = it = object.__new__(cls)
        it.init(app, homedir)
        return it

    def init(self, app, homedir):
        self.datab.connect(app=app, homedir=homedir)
        self.epheflag = 4
        self.country = ''
        self.usa = False
        self.orbs = []
        self.peorbs = []
        self.transits = []
        self.master = Chart('master')
        self.click = Chart('click')
        self.now = Chart('now')
        self.calc = Chart('calc')
        self.loc = Locality()
        self.date = NeXDate(current=self)
        self.calcdt = NeXDate(current=self)
        self.person = PersonInfo()
        self.charts = {'master': self.master, 'click': self.click,
                       'now': self.now, 'calc': self.calc}
        self.curr_chart = None
        self.curr_click = None
        self.crossed = True

        self.opmode = 'simple'
        self.curr_op = 'draw_nat'
        self.opright = 'draw_house'
        self.opleft = 'draw_nat'
        self.opup = 'draw_nat'
        self.clickmode = 'master'
        self.curr_list = opdouble

        self.pool = deque([])
        home = self._home_dir(app, homedir)
        poolfile = os.path.join(home, 'mruch.pkl')
        if os.path.exists(poolfile):
            with open(poolfile, "rb") as fh:
                self.pool = pickle.load(fh)
        self.couples = []
        self.coup_ix = 0
        coupfile = os.path.join(home, 'coups.pkl')
        if os.path.exists(coupfile):
            with open(coupfile, "rb") as fh:
                self.couples = pickle.load(fh)

        self.fav = []
        self.fav_ix = 0

    @staticmethod
    def _home_dir(app, homedir):
        if app is not None:
            return app.home_dir
        if homedir:
            return homedir
        return os.path.expanduser('~/.astronex')

    # --- queries ------------------------------------------------------------
    def is_valid(self, type):
        chart = self.charts[type]
        if not chart.date or not chart.city:
            return False
        else:
            return True

    def get_active(self, active):
        return self.charts[active]

    def newchart(self):
        return Chart()

    # --- operation mode -----------------------------------------------------
    def set_op(self, op):
        self.curr_op = op

    def set_opdelta(self, delta, side):
        if side == 'up' and self.clickmode == 'click':
            oplist = optriplepair
        else:
            oplist = opdouble
        ix = list(oplist).index(getattr(self, 'op' + side))
        oplist.rotate(-ix - delta)
        opside = oplist[0]
        setattr(self, 'op' + side, opside)

        if self.opmode == 'simple':
            self.curr_op = self.opleft
            return

        if self.clickmode == 'click':
            if opside == self.opleft:
                self.opright = self.opleft
            else:
                self.opleft = self.opright

    def reset_opup(self):
        if self.clickmode == 'click':
            self.opup = optriplepair[0]
        else:
            self.opup = opdouble[0]

    def set_list(self, label):
        self.curr_list = listlabels[label]

    # --- coordinate formatting (parity with original display format) --------
    def format_longitud(self, kind='chart'):
        from .utils import dectodeg
        chart = self.curr_chart if kind == 'chart' else self.curr_click
        longitud = dectodeg(chart.longitud)[:-2]
        if longitud[0] == '-':
            let = 'W'
            longitud = longitud[1:]
        else:
            let = 'E'
        return longitud[0:-2] + let + longitud[-2:]

    def format_latitud(self, kind='chart'):
        from .utils import dectodeg
        chart = self.curr_chart if kind == 'chart' else self.curr_click
        lat = dectodeg(chart.latitud)[:-2]
        if lat[0] == '-':
            let = 'S'
            lat = lat[1:]
        else:
            let = 'N'
        return lat[0:-2] + let + lat[-2:]

    # --- chart replication / pools -----------------------------------------
    def replicate(self, src, dest):
        dest.first = src.first
        dest.last = src.last
        dest.category = src.category
        dest.city = src.city
        dest.region = src.region
        dest.country = src.country
        dest.date = src.date
        dest.latitud = src.latitud
        dest.longitud = src.longitud
        dest.zone = src.zone
        dest.planets = src.planets
        dest.houses = src.houses
        dest.comment = src.comment

    def load_from_pool(self, ix, id):
        if len(self.pool) == 0:
            return False
        self.pool.rotate(-ix)
        poolch = self.pool[0]
        chart = self.charts[id]
        self.replicate(poolch, chart)
        return True

    def load_from_fav(self, ix, id):
        chart = self.charts[id]
        fav = self.fav[ix]
        self.fav_ix = ix
        self.replicate(fav, chart)
        return True

    def add_to_pool(self, chart, ow):
        if ow:
            self.pool[0] = chart
        else:
            name = " ".join([chart.first, chart.last])
            for ch in list(self.pool):
                if " ".join([ch.first, ch.last]) == name:
                    return
            self.pool.appendleft(chart)
            if len(self.pool) > 6:
                self.pool.pop()

    def save_pool(self, app):
        if len(self.pool) == 0:
            return
        home = self._home_dir(app, None)
        with open(os.path.join(home, 'mruch.pkl'), 'wb') as fh:
            pickle.dump(self.pool, fh, -1)

    def save_couples(self, app):
        if len(self.couples) == 0:
            return
        home = self._home_dir(app, None)
        with open(os.path.join(home, 'coups.pkl'), 'wb') as fh:
            pickle.dump(self.couples, fh, -1)

    # --- couples safety checks ---------------------------------------------
    def safe_delete_chart(self, tbl, id):
        for c in self.couples:
            if (tbl == c['fem'][1] and id == c['fem'][2]) or \
               (tbl == c['mas'][1] and id == c['mas'][2]):
                return False
        return True

    def safe_delete_table(self, tbl):
        for c in self.couples:
            if tbl == c['fem'][1] or tbl == c['mas'][1]:
                return False
        return True

    @classmethod
    def _reset_singleton(cls):
        """Clear the cached singleton (for deterministic tests)."""
        if '_singleton_instance' in cls.__dict__:
            delattr(cls, '_singleton_instance')

