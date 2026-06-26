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
    # 15821015 = Gregorian calendar adopted 1582-10-15; earlier dates use Julian.
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
    """Compute planet position, adding delta-T so the jd is treated as ET.

    The +delta(jd) shift is required for golden parity: the original engine
    fed (UT jd + delta-T) into the ET calc routine. It is deliberate, not an
    oversight -- do NOT remove it or switch to swe.calc_ut.
    """
    status, xx, err = _calc(jd + delta(jd), pl, epheflag)
    return status, xx[0], err


def calc_ut(jd, pl, epheflag=MOSEPH):
    """Compute planet position treating jd as UT directly (no delta-T shift).

    This is the counterpart to calc(): same routine, but WITHOUT the delta-T
    addition. The legacy engine called the ET routine on a raw UT jd here -- a
    deliberate quirk preserved for golden parity, not a bug to "fix".
    """
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
    # swe.houses_armc expects a positive ARMC angle; normalize west (negative)
    # longitudes by adding 360. Removing this breaks western-longitude charts.
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
            # The legacy engine emitted 11 bodies, omitting body 10; keeping
            # this skip preserves index alignment with the golden output.
            continue
        status, lon, err = calc(jd, i, epheflag)
        if status < 0:
            return None
        out.append(lon)
    return out
