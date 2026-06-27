# -*- coding: utf-8 -*-
"""Huber Age Point (Lebensuhr / Life Clock) pointer -- ported from legacy.

The Age Point advances ~1 house per 6 years of life, sweeping the whole wheel
in 72 years (one cycle). Within a house it interpolates linearly in the house's
ANGULAR space (Koch houses are unequal, so the rate is variable: faster through
a large house). The pointer starts at the Ascendant (houses[0]) at birth.

Two variants:
  * radix  -- sweeps FORWARDS from the Ascendant through unequal Koch houses.
  * nodal  -- sweeps BACKWARDS from the Mean Node through equal 30-degree houses.

This module implements the POINTER (the "where is it now" longitude) only --
the full 72-year event timetable (calc_agep family) is a later task. The
pointer is pure arithmetic on house longitudes + age, so it verifies EXACTLY
against the legacy golden (tests/golden/age_point.json).

Pure functions: explicit inputs -> data outputs. No boss, no GUI, no Chart.

Scope note: this module ports the radix variants only. The nodal variants
(which_degree_today nodal is here; calc_nodal_agep is NOT) and the legacy
``local=True`` relocated-houses branch of calc_agep (recalculates houses for a
relocated time/place) are deferred. The radix calc_agep is the GUI default.
"""
from datetime import datetime, timedelta
from functools import cmp_to_key

from .constants import zodnames, aspnames, planames, PHI


def _evcmp(a, b):
    """Event comparison by scusp (legacy chart.py:1340). Used to sort each
    house's events chronologically. Both Py2 and Py3 sorts are stable, so
    equal-scusp events keep insertion order -- hence the append order in
    calc_agep MUST mirror the legacy to reproduce tie-breaks."""
    ac, bc = a["scusp"], b["scusp"]
    if ac == bc:
        return 0
    return -1 if ac < bc else 1


def get_cycles(birth_year, now_year):
    """Number of complete 72-year life cycles elapsed by ``now_year``.

    Ported verbatim from legacy Chart.get_cycles (the integer-divmod by 72).
    """
    cycles, _ = divmod(now_year - birth_year, 72)
    return cycles


def house_time_lapsus(birth_dt, house, cycles=0):
    """The 6-year time span covering ``house`` in cycle ``cycles``.

    Returns {'begin': datetime, 'lapsus': timedelta}. The boundaries preserve
    the natal month/day/hour/minute (leap-day fallback to day-1, matching the
    legacy ValueError branch).
    """
    year = birth_dt.year + cycles * 72
    try:
        begin = datetime(year + house * 6, birth_dt.month, birth_dt.day,
                         birth_dt.hour, birth_dt.minute, 0)
        end = datetime(year + (house + 1) * 6, birth_dt.month, birth_dt.day,
                       birth_dt.hour, birth_dt.minute, 0)
    except ValueError:  # Feb-29 natal in a non-leap projection year
        begin = datetime(year + house * 6, birth_dt.month, birth_dt.day - 1,
                         birth_dt.hour, birth_dt.minute, 0)
        end = datetime(year + (house + 1) * 6, birth_dt.month, birth_dt.day - 1,
                       birth_dt.hour, birth_dt.minute, 0)
    return {"begin": begin, "lapsus": end - begin}


def age_point_longitude(houses, birth_dt, now_dt, cycles, kind="radix",
                        node_lon=None):
    """Longitude of the Age Point at ``now_dt``.

    * ``kind='radix'`` (default): sweeps forwards from ``houses[0]`` (Ascendant)
      through the unequal Koch houses; the pointer covers house ``h`` during
      the years [h*6, (h+1)*6] of cycle ``cycles``.
    * ``kind='nodal'``: sweeps backwards from the Mean Node (``node_lon``)
      through equal 30-degree houses. Requires ``node_lon``.

    Note: ``frac`` uses ``.days`` (sub-day time-of-day is deliberately dropped),
    matching the legacy -- the pointer steps roughly daily, not continuously.
    """
    wh = 0
    found = False
    for h in range(12):
        t = house_time_lapsus(birth_dt, h, cycles=cycles)
        if (now_dt - t["begin"]) < t["lapsus"]:
            wh = h
            found = True
            break
    if not found:
        # now overruns all 12 houses of this cycle. In normal use cycles is
        # derived from now_dt (every legacy call site does this), so now always
        # lands inside the cycle and this branch is unreachable. The legacy's
        # for/else left `t` as house 11's lapsus while setting wh=0 (a latent
        # bug -- inconsistent); we rebind t to house 0 to keep wh and t in sync.
        t = house_time_lapsus(birth_dt, 0, cycles=cycles)
        wh = 0

    frac = (now_dt - t["begin"]).days / float(t["lapsus"].days)

    if kind == "nodal":
        if node_lon is None:
            raise ValueError("kind='nodal' requires node_lon")
        off = 30 * frac
        deg = node_lon - wh * 30 - off
        if deg < 0:
            deg += 360
        return deg
    else:
        sizes = _sizes(houses)
        off = sizes[wh] * frac
        return (houses[wh] + off) % 360


def _sizes(houses):
    """Angular sizes of the first 6 houses (Koch), replicated to 12.

    Duplicated from Chart.sizes BY DESIGN: age_point is decoupled from Chart
    (pure functions, no Chart import), mirroring the directions.py pattern.
    """
    hs = houses[0:7]
    sizes = [0] * 6
    for i in range(6):
        s = hs[(i + 1)] - hs[i]
        if s < 0:
            s += 360
        sizes[i] = s
    return sizes * 2


# --- 72-year event timetable (calc_agep family) ---
# Pure functions, decoupled from Chart. ``plan`` is a sorted list of
# {degree, ix} dicts (built by the caller, mirroring legacy sortplan).

def house_degree(houses):
    """Within-sign degree of each house cusp (legacy Chart.house_degree)."""
    degs = []
    for h in houses:
        sign = int(h / 30)
        degs.append(h - sign * 30)
    return degs


def pl_midpoints(houses, plan):
    """Consecutive-planet midpoints located in their natal house.

    ``plan`` is sorted by degree. Returns [{degree, sign, house, name, pair}].
    Ported verbatim from legacy Chart.pl_midpoints.
    """
    all_midpoints = []
    for i in range(len(plan)):
        midpoint = plan[(i + 1) % 11]["degree"] - plan[i]["degree"]
        if midpoint < 0:
            midpoint += 360
        midpoint = plan[i]["degree"] + midpoint / 2
        if midpoint > 360:
            midpoint -= 360
        name = planames[plan[i]["ix"]] + "/" + planames[plan[(i + 1) % 11]["ix"]]
        pair = (plan[i]["ix"], plan[(i + 1) % 11]["ix"])
        for j in range(len(houses)):
            h1 = houses[j]
            h2 = houses[(j + 1) % 12]
            if h1 > h2:
                if midpoint < h1 and midpoint < h2:
                    midpoint += 360
                h2 += 360
            if midpoint > h1 and midpoint < h2:
                sign = int(midpoint / 30)
                midpoint = midpoint - 30 * int(midpoint / 30)
                all_midpoints.append({
                    "degree": midpoint, "sign": sign,
                    "house": j, "name": name, "pair": pair})
                break
    return all_midpoints


def calc_agep(houses, birth_dt, plan):
    """Full 72-year Age Point event timetable (radix variant).

    For each of 12 houses (6 years each), produces an ordered list of events
    in chronological order: house entry (Cc N), sign cusps, planet aspects,
    midpoints, and the Huber Pr/Pi low-points (golden-ratio split).

    Returns [{day, mon, year, lab, cl}] with zero-padded string fields, matching
    the legacy format. The order is the legacy's exact sort order (stable on
    equal scusp via insertion order), verified against the golden.
    """
    degs = house_degree(houses)
    sizes = _sizes(houses)
    mids = pl_midpoints(houses, plan)
    age_prog = []

    for i in range(12):
        events = []
        time_obj = house_time_lapsus(birth_dt, i)
        d = time_obj["begin"]
        day = str(d.day).rjust(2, "0")
        month = str(d.month).rjust(2, "0")
        year = d.year
        age_prog.append({
            "day": day, "mon": month, "year": year,
            "lab": "Cc %s" % str(i + 1), "cl": "txt_cp"})
        house = houses[i]
        s = 0
        scusp = 30.0 - degs[i]
        sign = int(house / 30)
        while scusp < sizes[i]:
            events.append({
                "scusp": scusp,
                "sname": zodnames[(sign + 1 + s) % 12],
                "cl": "sign"})
            s += 1
            scusp += s * 30

        for m in mids:
            dif = abs(sign - m["sign"])
            lg = m["degree"] + 30 * dif - degs[i]
            if lg < 0:
                lg += 30
            if m["house"] == i:
                events.append({"scusp": lg, "sname": m["name"], "cl": "mid"})

        for p in plan:
            pl_lg = p["degree"]
            pl_sign = int(pl_lg / 30)
            pl_lg = pl_lg - 30 * pl_sign
            lg = pl_lg - degs[i]
            if lg < 0:
                lg += 30
            c = 0
            while lg + 30 * c < sizes[i]:
                aspsign = int((house + lg + 30 * c) / 30) % 12
                realasp = abs(pl_sign - aspsign)
                label = aspnames[realasp] + "/" + planames[p["ix"]]
                events.append({"scusp": lg + 30 * c, "sname": label, "cl": "asp"})
                c += 1

        pr = sizes[i] * PHI
        pi = sizes[i] - pr
        events.append({"scusp": pr, "sname": "Pr %s" % str(i + 1), "cl": "pr"})
        events.append({"scusp": pi, "sname": "Pi %s" % str(i + 1), "cl": "pi"})
        events.sort(key=cmp_to_key(_evcmp))
        for e in events:
            fac = e["scusp"] / sizes[i]
            days = time_obj["lapsus"].days * fac
            dat = time_obj["begin"] + timedelta(days)
            hday = str(dat.day).rjust(2, "0")
            hmonth = str(dat.month).rjust(2, "0")
            hyear = dat.year
            age_prog.append({
                "day": hday, "mon": hmonth, "year": hyear,
                "lab": e["sname"], "cl": e["cl"]})

    return age_prog
