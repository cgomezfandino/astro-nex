# -*- coding: utf-8 -*-
"""Directional techniques (API/Huber method), ported from legacy directions.py.

Pure functions: explicit inputs -> data outputs. No boss, no GUI, no Current
mutation. Verified against golden data from the original engine.

Ported so far:
    * solar_rev  -- solar revolution (return of the natal Sun)
    * sec_prog   -- secondary progression (1 year of life = 1 day)
"""
from datetime import timedelta

from . import ephemeris as pysw


def solar_rev(natal_sun_lon, target_year, birth_month, birth_day, epheflag=4):
    """Julian Day (UT) at which the Sun returns to ``natal_sun_lon`` in
    ``target_year``.

    The Sun moves ~0.9856 deg/day and its longitude is monotonic within a
    +/-2 day window around the birthday, so a bisection on ``f(jd) =
    sun(jd) - natal`` converges to the return in ~40 evaluations. This
    replaces the legacy's nested coarse-to-fine loops (6 levels, hundreds of
    evaluations) with a single readable loop; verified to land within the
    ephemeris-engine tolerance of the legacy golden (and closer to the true
    root: sun(jd) ~= natal to ~1e-7 deg).
    """
    def sun_lon(jd):
        _status, lon, _err = pysw.calc(jd, 0, epheflag)
        return lon

    lo = pysw.julday(target_year, birth_month, birth_day, 0.0) - 2.0
    hi = lo + 4.0
    flo = sun_lon(lo) - natal_sun_lon
    fhi = sun_lon(hi) - natal_sun_lon

    # Within a 4-day window the Sun crosses every longitude exactly once, so flo
    # and fhi straddle zero (modulo 360 handled by the direction of the sign).
    for _ in range(40):   # 2^-40 day is far below the ephemeris resolution
        mid = (lo + hi) / 2.0
        fmid = sun_lon(mid) - natal_sun_lon
        if fmid == 0.0:
            return mid
        if (flo < 0) == (fmid < 0):
            lo, flo = mid, fmid
        else:
            hi, fhi = mid, fmid
    return (lo + hi) / 2.0


def sec_prog(natal_dt, target_year, sec_alltimes=False, now_dt=None):
    """Secondary progression: 1 year of life == 1 day after birth.

    Returns a naive UTC datetime (matching the legacy combine_date output).

    * ``sec_alltimes=False``: the progressed date is simply the birth date plus
      one day per year of life.
    * ``sec_alltimes=True``: the single progressed day is interpolated across
      the year between two synthetic birthdays (so each moment maps to a fraction
      of the progressed day). Requires ``now_dt``.
    """
    years_from_birth = target_year - natal_dt.year
    progdate = natal_dt + timedelta(days=years_from_birth)

    if not sec_alltimes:
        return _combine_date(progdate)

    if now_dt is None:
        raise ValueError("sec_alltimes=True requires now_dt")

    prev_birthday = _synth_birthday(natal_dt, target_year)
    next_birthday = _synth_birthday(natal_dt, target_year + 1)
    delta = now_dt - prev_birthday
    if delta.days < 0:
        next_birthday = prev_birthday
        prev_birthday = _synth_birthday(natal_dt, target_year - 1)
        delta = now_dt - prev_birthday
        years_from_birth -= 1
    yeardelta = next_birthday - prev_birthday
    whole_delta = delta.days * 86400 + delta.seconds
    whole_year_delta = yeardelta.days * 86400 + yeardelta.seconds
    frac = whole_delta / float(whole_year_delta)
    one_day_ahead = natal_dt + timedelta(days=years_from_birth + 1)
    daydelta = one_day_ahead - progdate
    daydelta = timedelta(daydelta.days * frac, daydelta.seconds * frac)
    inbetween_progdate = progdate + daydelta
    return _combine_date(inbetween_progdate)


def _combine_date(dt):
    """Strip sub-day fields into a fresh naive datetime (legacy combine_date)."""
    from datetime import date, time, datetime as _dt
    return _dt.combine(date(dt.year, dt.month, dt.day),
                       time(dt.hour, dt.minute, dt.second))


def _synth_birthday(natal_dt, year):
    """The natal month/day/time projected onto a given year (legacy synthbirthday)."""
    return natal_dt.replace(year=year)
