# -*- coding: utf-8 -*-
"""Swiss Ephemeris access, re-implementing the legacy ``pysw`` interface
on top of pyswisseph. Behavior is pinned to golden data from the original.
Ephemeris flag: 4 = Moshier (no .se1 files), 2 = Swiss, 256 = speed."""
import swisseph as swe

MOSEPH = 4
SWIEPH = 2
SPEED = 256
KOCH = b"K"


def setpath(path):
    swe.set_ephe_path(str(path))


def delta(jd):
    return swe.deltat(jd)


def julday(y, m, d, h):
    gregflag = swe.JUL_CAL if (y * 10000 + m * 100 + d) < 15821015 else swe.GREG_CAL
    return swe.julday(y, m, d, h, gregflag)


def revjul(jd, gregflag=swe.GREG_CAL):
    return swe.revjul(jd, gregflag)


def _calc(jd, pl, epheflag):
    """Call swe.calc and normalise return shape.

    Modern pyswisseph returns ``(xx_6tuple, retflag_int)``.
    We extract longitude (xx[0]) and speed (xx[3]) from the inner tuple.
    """
    try:
        xx, retflag = swe.calc(jd, pl, epheflag)
        return retflag, xx, ""
    except swe.Error as exc:
        return -1, (0.0,) * 6, str(exc)


def calc(jd, pl, epheflag=MOSEPH):
    """Compute planet position in ET (adds delta-T to UT jd)."""
    status, xx, err = _calc(jd + delta(jd), pl, epheflag)
    return status, xx[0], err


def calc_ut(jd, pl, epheflag=MOSEPH):
    """Compute planet position treating jd as UT directly (legacy quirk)."""
    status, xx, err = _calc(jd, pl, epheflag)
    return status, xx[0], err


def calc_ut_with_speed(jd, pl, epheflag=MOSEPH):
    """Compute planet position + speed with SPEED flag set."""
    status, xx, err = _calc(jd, pl, epheflag | SPEED)
    return status, xx[0], xx[3], err


def houses(jd, glt, glg):
    """Return 12 Koch house cusps for given UT jd, latitude, longitude."""
    cusps, ascmc = swe.houses(jd, glt, glg, KOCH)
    return cusps


def local_houses(jd, glg, glt, epheflag):
    """Compute local houses via ARMC (as the legacy engine did)."""
    armc = glg + 360 if glg < 0 else glg
    status, eps, err = calc(jd, -1, epheflag)
    cusps, ascmc = swe.houses_armc(armc, glt, eps, KOCH)
    return cusps


def planets(jd, epheflag, p=12):
    """Return ecliptic longitudes for bodies 0-11, skipping body 10 (mean node).

    Replicates the legacy pysw loop: adds delta-T to jd via ``calc()``.
    Returns a list of 11 floats, or None on error.
    """
    out = []
    for i in range(p):
        if i == 10:
            continue
        status, lon, err = calc(jd, i, epheflag)
        if status < 0:
            return None
        out.append(lon)
    return out
