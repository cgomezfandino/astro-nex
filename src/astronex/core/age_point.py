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
"""
from datetime import datetime, timedelta


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
