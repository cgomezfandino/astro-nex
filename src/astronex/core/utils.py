# -*- coding: utf-8 -*-
"""Pure helper functions ported from legacy astronex/utils.py (Python 2 → 3)."""

import math
from datetime import datetime
from zoneinfo import ZoneInfo

RAD = math.pi / 180


def degtodec(d):
    """Convert a packed-string degree representation to a decimal float.

    Format: ['-'] <deg> <mm> <ss>  where mm and ss are always 2 digits.
    Example: "103000" -> 10 deg 30 min 00 sec -> 10.5
    """
    sign = 1
    if d.startswith('-'):
        sign = -sign
        d = d[1:]
    sec, rest = d[-2:], d[:-2]
    mint, deg = rest[-2:], rest[:-2]
    mint = int(mint) + int(sec) / 60.0
    if not deg:
        deg = '0'
    deg = int(deg) + mint / 60
    deg *= sign
    return deg


def dectodeg(d):
    """Convert a decimal degree float to a packed-string representation.

    Example: 10.5 -> "103000"  (10 deg, 30 min, 00 sec)
             0.0  -> "00000"   (sign='' + "0" + "00" + "00")
    """
    sign = ''
    if d < 0:
        sign = '-'
    absd = abs(d)
    deg = int(math.floor(absd))
    rest = (absd - deg) * 60
    mint = int(math.floor(rest))
    sec = int(math.floor((rest - mint) * 60))
    return sign + str(deg) + str(mint).zfill(2) + str(sec).zfill(2)


def parsestrtime(strdate):
    """Parse an ISO-8601 datetime string into a (date_str, time_str) tuple."""
    date, _, time = strdate.partition('T')
    date = "/".join(reversed(date.split('-')))
    zone, time = time[8:], time[:5]
    try:
        zone.index(':')
        delta, zone = zone[:6], zone[6:]
    except ValueError:
        delta, zone = zone[:5], zone[5:]
        d1, d2 = delta[1:3], delta[3:5]
        delta = delta[0] + str(int(d1) + int(d2)).rjust(2, '0')
    time += ' ' + delta + zone
    return (date, time)


def format_longitud(long):
    """Format a decimal longitude in the legacy display form: deg<hemi>min.

    The hemisphere letter ('E'/'W') is placed between degrees and minutes,
    e.g. format_longitud(-3.7038) == "3W42" (3 deg, West, 42 min).
    """
    longitud = dectodeg(long)[:-2]
    if longitud[0] == '-':
        let = 'W'
        longitud = longitud[1:]
    else:
        let = 'E'
    return longitud[0:-2] + let + longitud[-2:]


def format_latitud(lat):
    """Format a decimal latitude in the legacy display form: deg<hemi>min.

    The hemisphere letter ('N'/'S') is placed between degrees and minutes,
    e.g. format_latitud(40.4168) == "40N25" (40 deg, North, 25 min).
    """
    latitud = dectodeg(lat)[:-2]
    if latitud[0] == '-':
        let = 'S'
        latitud = latitud[1:]
    else:
        let = 'N'
    return latitud[0:-2] + let + latitud[-2:]


def points_from_angle(angles):
    """Convert a list of angles (degrees) to (cos, sin) coordinate pairs."""
    points = []
    for a in angles:
        points.append((math.cos(a * RAD), math.sin(a * RAD)))
    return points


def strdate_to_date(strdate):
    """Parse an ISO-8601 datetime string into a naive UTC datetime object.

    Py2 transform: replaced pytz.timezone('UTC') with ZoneInfo('UTC'),
    then strips tzinfo to return a naive datetime (matching legacy behaviour).
    """
    date, _, time = strdate.partition('T')
    try:
        y, mo, d = [int(x) for x in date.split('-')]
    except ValueError:
        print(date)
        raise
    zone, time = time[8:], time[:5]
    try:
        zone.index(':')
        delta, zone = zone[:6], zone[6:]
        d1, d2 = delta[1:3], delta[4:6]
        tot = int(d1) + int(d2) / 60.0
    except ValueError:
        delta, zone = zone[:5], zone[5:]
        d1, d2 = delta[1:3], delta[3:5]
        tot = int(d1) + int(d2)
    sign = {'+': 1, '-': -1}[delta[0]]
    delta = tot * sign
    h, m = [int(x) for x in time.split(':')]
    dt = datetime(y, mo, d, int(h), m, 0, tzinfo=ZoneInfo("UTC"))
    dt = datetime.combine(dt.date(), dt.time())
    return dt
