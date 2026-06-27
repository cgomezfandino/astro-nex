# -*- coding: utf-8 -*-
"""Radix subset of the legacy Chart model (Huber/API method), ported to Py3.

Ported faithfully from the legacy ``astronex/chart.py``. Only the radix
(birth-chart geometry) slice is implemented here; everything that depends on
the GTK ``boss``/config layer, on ``self.date``/``pytz`` machinery, or on the
age-point milestone is intentionally NOT ported.

DEFERRED (out of scope for this slice; see legacy chart.py):
- calc_localhouses (the legacy boss-coupled Chart method). The decoupled
  contract -- local_houses(jd, lon, lat, epheflag) -- IS implemented in
  ephemeris.py and tested (Tier B).
- calc_plan_with_retrogression (uses self.date/self.zone/pytz)
- calc_aspects              (bi-wheel/click variant)
- chiron_calc, vulcan_calc
- All age-point machinery: calc_agep, calc_nodal_agep, calc_house_agep,
  calc_house_nodal_agep, pl_midpoints, nodal_pl_midpoints, house_time_lapsus,
  house_degree, birthday_frac, cp_time_lapsus, when_angle, when_angle_nodal,
  which_degree_today*, calc_cross_points, calc_pe_houses, which_house_today,
  get_cycles, evcmp.  (issue #17)
- All "dynamics" methods: signdyn, housedyn, resolve_dyn, dyncalc_*,
  dynstar_*, dyn_span_diff.
- rays_calc, plagram_*, house_force_all, sign_force_all (display-only force
  variants). The Huber professional factors (pers_force family) ARE ported.

Ported chart-type transforms (issue #18), verified vs the legacy golden
(tests/golden/chart_types.json):
  * Tier A (exact 1e-9, pure arithmetic): nod_plan_long, nod_sign_long,
    nodal_cusp_degrees, house_sign_long, sign_sizes, sign_in_house,
    invert_house_plan, invert_house_sign, which_house_nodal.
  * Tier B (1e-6, fresh ephemeris): local_houses contract (ephemeris.py).
  * Tier D (exact 1e-6, pure arithmetic): pers_house_force, pers_sign_force,
    pers_aspects_force, pers_zone_force, pers_force.
  * Tier C (contract): Transits = a second radix Chart.calc(transit_jd) +
    cross-chart aspects (no chart-type-specific transform).
The age point is a later milestone and is deliberately left for then.
"""

from . import ephemeris
# Re-export legacy module-level names so the ported method bodies work
# unchanged. The legacy aspects() reads module globals ``planclass``,
# ``aspclass`` and ``orbs``.
from .constants import planclass, aspclass, PHI, RAD, DEFAULT_ORBS, points
from .utils import parsestrtime
from datetime import timedelta

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

    # --- Tier A chart-type pure transforms (ported verbatim from legacy) ---
    # These read only self.planets / self.houses (no ephemeris call of their
    # own), so they verify EXACT (1e-9) against the legacy golden.

    def nod_plan_long(self):
        """Nodal chart planet longitudes (node <-> asc swap, reversed houses)."""
        factor = [s / 30 for s in self.sizes()]
        plan = self.planets[:]
        asc = self.houses[0]
        plan[10], asc = asc, plan[10]
        ndpl = []
        for p in plan:
            dist = 360 - (p - asc) % 360
            h, d = divmod(dist, 30)
            h = int(h)
            ndpl.append(self.houses[h] + d * factor[h])
        return ndpl

    def nod_sign_long(self):
        """Nodal chart sign (house-cusp) longitudes."""
        nod = self.planets[10]
        asc = self.houses[0]
        factor = [s / 30 for s in self.sizes()]
        sign, deg = divmod(nod, 30)
        hssg = []
        for i in range(12):
            res = self.houses[i] + deg * factor[i]
            hssg.append(res - asc)
        return hssg

    def nodal_cusp_degrees(self):
        """Equal 30-degree nodal cusps counted backwards from the node."""
        nodasc = self.planets[10]
        hn = []
        for i in range(12):
            c = nodasc - 30 * i
            if c < 0:
                c += 360.0
            hn.append(c)
        return hn

    def house_sign_long(self):
        """Sign (zodiac) longitudes repositioned onto the unequal-house wheel."""
        signinh = self.sign_in_house()
        factor = [30 / s for s in self.sizes()]
        hssg = []
        for i in range(12):
            h = signinh[i]
            dist = (i * 30 - self.houses[h]) % 360
            res = h * 30 + dist * factor[h]
            hssg.append(res)
        return hssg

    def sign_in_house(self):
        """For each zodiac sign cusp (0,30,...,330), which house it falls in."""
        signinh = []
        for i in range(12):
            sign = 30 * i
            for j in range(len(self.houses)):
                h1 = self.houses[j]
                h2 = self.houses[(j + 1) % 12]
                if h1 > h2:
                    if sign < h1 and sign < h2:
                        sign += 360
                    h2 += 360
                if sign > h1 and sign < h2:
                    signinh.append(j)
                    break
        return signinh

    def sign_sizes(self):
        """Angular size of each sign on the unequal-house wheel."""
        ss = self.house_sign_long()
        sizes = [0] * 12
        for i in range(len(ss)):
            s = ss[(i + 1) % 12] - ss[i]
            if s < 0:
                s += 360
            sizes[i] = s
        return sizes

    def invert_house_plan(self, hspl):
        """Inverse of house_plan_long: equal-house longitudes back to radix."""
        factor = [s / 30 for s in self.sizes()]
        ipl = [0] * 11
        for i, hp in enumerate(hspl):
            h, deg = divmod(hp, 30)
            ipl[i] = self.houses[int(h)] + deg * factor[int(h)]
        return ipl

    def invert_house_sign(self, hssg):
        """Inverse of house_sign_long."""
        factor = [s / 30 for s in self.sizes()]
        isg = [0] * 12
        for i, hp in enumerate(hssg):
            h, deg = divmod(hp, 30)
            isg[i] = self.houses[int(h)] + deg * factor[int(h)]
        return isg

    def which_house_nodal(self, p):
        """House index in the nodal (equal-30, node-based) wheel.

        Returns (11 - i) -- inverted numbering. May return None if the point
        falls exactly on a cusp boundary (matches legacy behaviour).
        """
        point = p
        house = self.planets[10]
        for i in range(12):
            h1 = (house + 30.0 * i) % 360.0
            h2 = (house + 30 * (i + 1)) % 360.0
            if h1 > h2:  # piscis - aries
                if point < h1 and point < h2:
                    point += 360
                h2 += 360
            if point > h1 and point <= h2:
                return (11 - i)
        return None

    # --- Tier D: profession force (Huber professional factors) ---
    # Output is a weighted (sun, moon, saturn) 3-tuple, not longitudes.
    # Ported verbatim from legacy chart.py; verified exact (1e-6) vs golden.

    def pers_house_force(self):
        hspl = self.house_plan_long()
        pl = []
        for l in [hspl[0], hspl[1], hspl[6]]:
            f = l - int(l)
            p = int(l) % 30 + f
            if p > 22.35:
                p = 30 - p
            pl.append(p)
        tups = [(pl[0], "sun"), (pl[1], "moon"), (pl[2], "sat")]
        tups.sort()
        phforce = {}
        for i, t in enumerate(tups):
            phforce[t[1]] = 3 - i
        return phforce

    def pers_sign_force(self):
        n = 30 - 30 * PHI
        fac = n * (PHI - 1)
        sl = self.planets[:]
        pl = []
        for l in [sl[0], sl[1], sl[6]]:
            f = l - int(l)
            p = int(l) % 30 + f
            if p > n:
                p = (p * PHI) - fac
            pl.append(abs(n - p))
        tups = [(pl[0], "sun"), (pl[1], "moon"), (pl[2], "sat")]
        tups.sort()
        phforce = {}
        for i, t in enumerate(tups):
            phforce[t[1]] = 3 - i
        return phforce

    def pers_aspects_force(self):
        asp = self.aspects()
        pl = [0] * 11
        for a in asp:
            if a["gw"]:
                continue
            f1 = a["f1"]
            f2 = a["f2"]
            if f1 > 1:
                f1 = 0.95
            if f2 > 1:
                f2 = 0.95
            f1 = 2 - 2 * f1
            f2 = 2 - 2 * f2
            if a["p1"] == 10 or a["p2"] == 10:
                f1 /= 2
                f2 /= 2
            pl[a["p1"]] += f1
            pl[a["p2"]] += f2
        tups = [(pl[0], "sun"), (pl[1], "moon"), (pl[6], "sat")]
        tups.sort()
        phforce = {}
        for i, t in enumerate(tups):
            phforce[t[1]] = i + 1
        return phforce

    def pers_zone_force(self):
        pl = self.house_plan_long()
        sun = abs(270 - pl[0])
        if sun > 180:
            sun = 360 - sun
        sat = abs(90 - pl[6])
        if sat > 180:
            sat = 360 - sat
        moon = pl[1]
        if moon > 90 and moon <= 270:
            moon = abs(180 - moon)
        elif moon > 270:
            moon = 360 - moon
        tups = [(sun, "sun"), (moon, "moon"), (sat, "sat")]
        tups.sort()
        phforce = {}
        for i, t in enumerate(tups):
            phforce[t[1]] = 3 - i
        return phforce

    def pers_force(self):
        """Huber professional factors: weighted (sun, moon, saturn) strength."""
        h = self.pers_house_force()
        s = self.pers_sign_force()
        a = self.pers_aspects_force()
        z = self.pers_zone_force()
        sun = h["sun"] * 1.5 + s["sun"] + a["sun"] * 0.75 + z["sun"] * 0.5
        moon = h["moon"] * 1.5 + s["moon"] + a["moon"] * 0.75 + z["moon"] * 0.5
        sat = h["sat"] * 1.5 + s["sat"] + a["sat"] * 0.75 + z["sat"] * 0.5
        return (sun, moon, sat)

    # --- Dynamics (element/cross strength) + cross-points + rays ---
    # Pure numeric calc (no ephemeris call of its own); verified EXACT vs the
    # legacy golden (tests/golden/dynamics.json). Ported verbatim.

    def signdyn(self):
        sum1 = 0
        signs = [0] * 12
        hou = [0] * 12
        for h in (0, 3, 6, 9):
            hou[h] = int(self.houses[h] / 30)
        for i in range(len(self.planets)):
            p = self.planets[i]
            sign = int(p / 30)
            deg = p - sign * 30
            point = points[i]
            if deg < 2 or deg >= 27:
                point -= 3
            elif deg >= 7 and deg <= 18:
                point += 3
            signs[sign] += point
            if sign == hou[0]:
                sum1 += 1
            if deg >= 29 and deg < 30:
                signs[(sign + 1) % 12] += int(point / 2)
            elif deg >= 0 and deg < 1:
                signs[(sign + 11) % 12] += int(point / 2)
        if sum1 == 1:
            signs[hou[0]] += 5
        else:
            signs[hou[0]] += 3 * sum1
        return self.resolve_dyn(signs)

    def housedyn(self):
        magick = [0.206, 0.412, 0.6847, 0.745, 0.8727, 0.966]
        houses = [0] * 12
        plinh = self.plan_in_house()
        sizes = self.sizes()
        for i in range(11):
            point = points[i]
            hou = plinh[i]
            houplus = (hou + 1) % 12
            if hou % 3 == 0:
                plus = 5
            else:
                plus = 3
            p = self.planets[i] - self.houses[hou]
            if p < 0:
                p += 360
            zone = [0] * 6
            for j in range(6):
                zone[j] = sizes[hou] * magick[j]
            if p < zone[0]:
                houses[hou] += (point + plus)
            elif p < zone[1]:
                houses[hou] += point
            elif p < zone[2]:
                houses[hou] += (point - 3)
            elif p < zone[3]:
                houses[hou] += (point - 3)
                houses[houplus] += (point - 3)
            elif p < zone[4]:
                houses[hou] += point
                houses[houplus] += point
            elif p < zone[5]:
                if houplus % 3 == 0:
                    plus = 5
                else:
                    plus = 3
                houses[hou] += (point + plus)
                houses[houplus] += (point + plus)
            else:
                if houplus % 3 == 0:
                    plus = 5
                else:
                    plus = 3
                houses[houplus] += (point + plus)
        return self.resolve_dyn(houses)

    def resolve_dyn(self, dinary):
        elem = {'fire': 0, 'earth': 0, 'air': 0, 'water': 0}
        cross = {'card': 0, 'fix': 0, 'mut': 0}
        for i in range(len(self.houses)):
            if i % 4 == 3:
                elem['water'] += dinary[i]
            elif i % 4 == 0:
                elem['fire'] += dinary[i]
            elif i % 4 == 1:
                elem['earth'] += dinary[i]
            elif i % 4 == 2:
                elem['air'] += dinary[i]
            if i % 3 == 2:
                cross['mut'] += dinary[i]
            elif i % 3 == 0:
                cross['card'] += dinary[i]
            elif i % 3 == 1:
                cross['fix'] += dinary[i]
        return {'elem': elem, 'cross': cross}

    def dyncalc_stress(self):
        ds = self.signdyn()
        dh = self.housedyn()
        tots = ds['cross']['card'] + ds['cross']['fix'] + ds['cross']['mut']
        toth = dh['cross']['card'] + dh['cross']['fix'] + dh['cross']['mut']
        return toth - tots

    def dyncalc_list(self):
        ds = self.signdyn()
        dh = self.housedyn()
        tots = ds['cross']['card'] + ds['cross']['fix'] + ds['cross']['mut']
        toth = dh['cross']['card'] + dh['cross']['fix'] + dh['cross']['mut']
        cr = ds['cross']; el = ds['elem']
        srow = (tots, cr['card'], cr['fix'], cr['mut'],
                el['fire'], el['earth'], el['air'], el['water'])
        cr = dh['cross']; el = dh['elem']
        hrow = (toth, cr['card'], cr['fix'], cr['mut'],
                el['fire'], el['earth'], el['air'], el['water'])
        # legacy: zip(hrow,srow) then reduce(lambda x,y:x-y, pair) -> h-s per col
        dif = [h - s for h, s in zip(hrow, srow)]
        srow = [str(s) for s in srow]
        hrow = [str(s) for s in hrow]
        dif = [str(s) for s in dif]
        return srow, hrow, dif

    def dynstar_signs(self):
        return self._dynstar(self.signdyn())

    def dynstar_houses(self):
        return self._dynstar(self.housedyn())

    def _dynstar(self, d):
        el = d['elem']
        cr = d['cross']
        return [
            cr['card'] + el['fire'],   cr['fix'] + el['earth'],
            cr['mut'] + el['air'],     cr['card'] + el['water'],
            cr['fix'] + el['fire'],    cr['mut'] + el['earth'],
            cr['card'] + el['air'],    cr['fix'] + el['water'],
            cr['mut'] + el['fire'],    cr['card'] + el['earth'],
            cr['fix'] + el['air'],     cr['mut'] + el['water'],
        ]

    def dyn_span_diff(self):
        ds = self.signdyn()
        dh = self.housedyn()
        scr = ds['cross']; sel = ds['elem']
        hcr = dh['cross']; hel = dh['elem']
        keys = [('card', 'fire'), ('fix', 'earth'), ('mut', 'air'),
                ('card', 'water'), ('fix', 'fire'), ('mut', 'earth'),
                ('card', 'air'), ('fix', 'water'), ('mut', 'fire'),
                ('card', 'earth'), ('fix', 'air'), ('mut', 'water')]
        return [(hcr[c] + hel[e]) - (scr[c] + sel[e]) for c, e in keys]

    def plan_conflicts(self):
        pl = []
        for i, p in enumerate(self.house_plan_long()):
            pl.append({'degree': p, 'ix': i, 'conflict': None})
        pl = sorted(pl, key=lambda d: d['degree'])
        for i in range(len(pl)):
            dif = pl[(i + 1) % 11]["degree"] - pl[i]["degree"]
            if dif < 0:
                dif += 360.0
            if dif <= 6.5:
                pl[i]["conflict"] = pl[(i + 1) % 11]["conflict"] = True
        return pl

    def cuad_plan(self):
        pl = self.plan_conflicts()
        low = 30 - 30 * PHI
        ii = []
        try:
            while pl[-1]['degree'] > (330 - low):
                ii.insert(0, pl.pop())
        except IndexError:
            pass
        ind = []
        try:
            while pl[-1]['degree'] > (240 - low):
                ind.insert(0, pl.pop())
        except IndexError:
            pass
        you = []
        try:
            while pl[-1]['degree'] > (150 - low):
                you.insert(0, pl.pop())
        except IndexError:
            pass
        col = []
        try:
            while pl[-1]['degree'] > (60 - low):
                col.insert(0, pl.pop())
        except IndexError:
            pass
        ii = ii + pl
        return (ind, you, col, ii)

    def which_all_houses(self):
        hh = []
        sz = self.sizes()
        for h in range(len(self.houses)):
            d = self.houses[h]
            g = sz[h] * PHI
            l = d + g
            i = d + sz[h] - g
            d = self.which_sign(d)
            l = self.which_sign(l)
            i = self.which_sign(i)
            hh.append((d, i, l))
        return hh

    def which_all_signs(self):
        return [self.which_sign(p) for p in self.planets]

    def rays_calc(self):
        pertab = [1, 4, 6, 5, 2]
        minortab = [6, 7, 5, 4]
        mayortab = [1, 3, 2]
        asc = self.houses[0]
        mc = self.houses[9]
        lim1 = asc - int(asc / 30) * 30
        lim2 = mc - int(mc / 30) * 30
        pasc = int(asc / 30) % 3
        pmc = int(mc / 30) % 3
        if lim1 > 29.0 or lim1 < 1.0 or lim2 > 29.0 or lim2 < 1.0:
            rpers = 7
        else:
            rpers = pasc + pmc
            if rpers == 2 and pasc == pmc:
                rpers = 3
            else:
                rpers = pertab[rpers]
        rays = [rpers]
        asc = int(asc / 30) % 12
        mc = int(mc / 30) % 12
        for i in [0, 1, 6, 7, 8, 9]:
            pl = int(self.planets[i] / 30) % 12
            if pl == asc or (pl + 6) % 12 == asc or pl == mc or (pl + 6) % 12 == mc:
                rays.append(mayortab[pl % 3])
            else:
                rays.append(minortab[pl % 4])
        nd = int(self.planets[10] / 30) % 12
        rays.append(mayortab[nd % 3])
        return rays

    def calc_cross_points(self, cross=None):
        sizes = self.sizes()
        hasc = self.houses[0]
        nnode = self.planets[10]
        h = 0
        hn = self.which_house(nnode)
        while hn > h:
            if hn - h == 1 and hn < self.which_house((nnode - 30) % 360):
                break
            if h == 0 and hn == 1:
                break
            h = (h + 1) % 12
            hasc = self.houses[h]
            nnode = (nnode - 30) % 360
            hn = self.which_house(nnode)
        dist = nnode - hasc
        if dist < 0:
            if dist < -30:  # aries pisces
                dist += 360
            else:
                h = (h - 1) % 12  # cp in prev h.
        else:
            if h > hn:
                dist -= 360
                h = (h - 1) % 12  # cp in prev h.
        va = sizes[h] / 6
        vn = 5.0
        la = dist * va / (va + vn)
        if not cross:
            return (hasc + la) % 360
        r = {}
        r['cp1'] = self.which_sign((hasc + la) % 360)
        r['cp2'] = self.which_sign((hasc + la + 180) % 360)
        h += [0, 1][la < 0]
        r['dat1'] = self.cp_time_lapsus(h, la)
        r['dat2'] = self.cp_time_lapsus((h + 6) % 12, la)
        return r

    def cp_time_lapsus(self, h, off):
        """Date of the cross-point in house h at angular offset ``off``.

        Ported from legacy chart.py. Uses house_time_lapsus (in age_point) and
        self.date (ISO string) for the natal year.
        """
        from .age_point import house_time_lapsus
        from datetime import datetime
        date, _ = parsestrtime(self.date)
        d_str, m_str, y_str = date.split("/")
        birth_dt = datetime(int(y_str), int(m_str), int(d_str))
        t = house_time_lapsus(birth_dt, h)
        off = off / self.sizes()[h]
        days = t["lapsus"].days * off
        d = t["begin"] + timedelta(days)
        return "%s.%s.%s" % (str(d.day).rjust(2, '0'),
                             str(d.month).rjust(2, '0'),
                             str(d.year))
