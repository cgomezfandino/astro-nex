# -*- coding: utf-8 -*-
"""Radix subset of the legacy Chart model (Huber/API method), ported to Py3.

Ported faithfully from the legacy ``astronex/chart.py``. Only the radix
(birth-chart geometry) slice is implemented here; everything that depends on
the GTK ``boss``/config layer, on ``self.date``/``pytz`` machinery, or on the
age-point milestone is intentionally NOT ported.

DEFERRED (out of scope for this slice; see legacy chart.py):
- calc_localhouses          (uses boss.get_state())
- calc_plan_with_retrogression (uses self.date/self.zone/pytz)
- calc_aspects              (bi-wheel/click variant)
- chiron_calc, vulcan_calc
- All age-point machinery: calc_agep, calc_nodal_agep, calc_house_agep,
  calc_house_nodal_agep, pl_midpoints, nodal_pl_midpoints, house_time_lapsus,
  house_degree, birthday_frac, cp_time_lapsus, when_angle, when_angle_nodal,
  which_degree_today*, calc_cross_points, calc_pe_houses, nodal_cusp_degrees,
  which_house_today, get_cycles, evcmp.
- All "dynamics" methods: signdyn, housedyn, resolve_dyn, dyncalc_*,
  dynstar_*, dyn_span_diff.
- Draw-house / sign / nodal helpers and force/ray/data-sheet methods not in
  the radix subset (sign_sizes, house_sign_long, sign_in_house, nod_*,
  invert_*, rays_calc, *_force, plagram_*, etc.).
The age point is the next milestone and is deliberately left for then.
"""

from . import ephemeris
# Re-export legacy module-level names so the ported method bodies work
# unchanged. The legacy aspects() reads module globals ``planclass``,
# ``aspclass`` and ``orbs``.
from .constants import planclass, aspclass, PHI, RAD, DEFAULT_ORBS

# Legacy config filled ``orbs`` at runtime; bind the standalone default here.
# Intentionally a mutable module global, NOT an immutable constant: future
# config wiring (and tests) override the active orb table by rebinding this
# name. Do not "clean this up" into a frozen constant -- that would break the
# override path the legacy app relies on.
orbs = DEFAULT_ORBS


class Chart(object):

    def __init__(self, id=None):
        self.id = id
        self.first = ""
        self.last = ""
        self.category = ""
        self.city = ""
        self.region = ""
        self.country = ""
        self.date = ""
        self.latitud = ""
        self.longitud = ""
        self.zone = ""
        self.planets = []
        self.houses = []
        self.comment = ""

    def __repr__(self):
        person = ",".join([self.first, self.last, self.category])
        country = ",".join([self.city, self.region, self.country])
        geo = ",".join([self.date, str(self.latitud), str(self.longitud), self.zone])
        planets = ",".join((str(p) for p in self.planets))
        houses = ",".join((str(h) for h in self.houses))
        return ",".join([person, country, geo, planets, houses, self.comment])

    def calc(self, date, loc, epheflag=4):
        d = ephemeris.julday(*date)
        lat, lon = loc
        self.planets = list(ephemeris.planets(d, epheflag))
        self.houses = list(ephemeris.houses(d, lat, lon))
        return self.planets, self.houses

    def soulplan(self):
        sizes = self.sizes()
        splan = []
        for p in iter(self.planets):
            s = int(p / 30)
            dh = (p - s * 30) * sizes[s] / 30
            pos = self.houses[s] + dh
            if pos > 360:
                pos -= 360
            splan.append(pos)
        return splan

    def urnodplan(self):
        sizes = self.sizes()
        plans = self.planets[:]
        plans[10] = self.houses[0]
        nod = self.planets[10]
        n = nod % 30.0
        uplan = []
        for p in iter(plans):
            # nodal house index: count houses from the node, inverted (house 0
            # = node's sign), carry the remainder distance
            h = 11 - int(((p - nod) / 30.0) % 12)
            dist = (n - p % 30.0) % 30.0
            uplan.append((self.houses[h] + dist * sizes[h] / 30.0) % 360)
        return uplan

    def aspects(self, kind='radix'):
        if kind == 'house':
            pl = self.house_plan_long()
        elif kind == 'soul':
            pl = self.soulplan()
        else:
            pl = self.planets[:]
        if kind == 'nodal':
            pl[10] = self.houses[0]
        chart_orbs = []
        for i in range(len(pl)):
            for j in range(i + 1, len(pl)):
                pci = planclass[i]
                if j != 10:
                    pcj = planclass[j]
                else:
                    pcj = planclass[i]
                dis = abs(pl[i] - pl[j])
                nsig = int(dis / 30)
                orb = dis - nsig * 30
                # fold: an orb > 20 deg belongs to the next sign/aspect; measure
                # it from that boundary
                if orb > 20.0:
                    nsig += 1
                    orb = 30.0 - orb
                acl = aspclass[nsig % 12]
                if orb <= 9.0:
                    orb1 = orbs[pci][acl]
                    orb2 = orbs[pcj][acl]
                    if orb <= orb1 or orb <= orb2:
                        f1 = orb / orb1
                        f2 = orb / orb2
                        chart_orbs.append({"p1": i, "p2": j, "a": nsig % 12, "f1": f1, "f2": f2, 'gw': False})
                    elif orb <= orb1 * 1.1 or orb <= orb2 * 1.1:
                        chart_orbs.append({"p1": i, "p2": j, "a": nsig % 12, "f1": 0, "f2": 0, 'gw': True})
        return chart_orbs

    def sizes(self):
        hs = self.houses[0:7]
        sizes = [0] * 6
        for i in range(6):
            s = hs[(i + 1)] - hs[i]
            if s < 0:
                s += 360
            sizes[i] = s
        return sizes * 2

    def house_plan_long(self):
        '''House chart planet longitud, from asc.'''
        plinh = self.plan_in_house()
        factor = [30 / s for s in iter(self.sizes())]
        hspl = [0] * 11
        for i in range(11):
            h = plinh[i]
            dist = self.planets[i] - self.houses[h]
            if dist < 0:
                dist += 360
            hspl[i] = h * 30 + dist * factor[h]
        return hspl

    def plan_in_house(self):
        plinh = [0] * 11
        for i, plan in enumerate(self.planets):
            for j in range(len(self.houses)):
                h1 = self.houses[j]
                h2 = self.houses[(j + 1) % 12]
                if h1 > h2:
                    # planet between 0 and h2
                    if plan < h1 and plan < h2:
                        plan += 360
                    h2 += 360
                if plan > h1 and plan < h2:
                    plinh[i] = j
                    break
        return plinh

    def get_low_points(self):
        pr = []
        sz = self.sizes()
        for h in range(len(self.houses)):
            d = self.houses[h]
            g = sz[h] * PHI
            l = d + g
            pr.append(l)
        return pr

    def which_sign(self, d):
        deg = d
        name = int(deg / 30) % 12
        col = int(deg / 30) % 12
        deg = deg - 30 * int(deg / 30)
        mint = int(60 * (deg - int(deg)))
        mint = str(mint).rjust(2, '0')
        deg = int(deg)
        deg = str(deg).rjust(2, '0')
        return {'deg': u"%s° %s´" % (deg, mint), 'name': name, 'col': col}

    def which_house(self, p):
        point = p
        for i in range(12):
            h1 = self.houses[i]
            h2 = self.houses[(i + 1) % 12]
            if h1 > h2:  # piscis - aries
                if point < h1 and point < h2:
                    point += 360
                h2 += 360
            if point > h1 and point <= h2:
                return i
        return None
