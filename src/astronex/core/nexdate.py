# -*- coding: utf-8 -*-
"""
NeXDate: local datetime → UT conversion for ephemeris calculations.

Ported from legacy Python 2 / pytz implementation to Python 3 / zoneinfo.

Intentionally deferred to a later milestone:
  - set_delta / dateforstore       (calendar arithmetic & storage formatting)
  - tz_sup historical-DST patching (oldtimes transition-time patching)
"""
from datetime import datetime
from zoneinfo import ZoneInfo

UTC = ZoneInfo("UTC")


class NeXDate(object):
    """Holds an aware local datetime and its UT projection for ephemeris calc."""

    def __init__(self, dt=None, tz=UTC, current=None):
        self.tz = tz
        self.current = current
        if dt is None:
            dt = datetime.now()
        self.set_local(dt)

    def set_local(self, naive_or_aware):
        dt = naive_or_aware
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=self.tz)
        self.ld = dt
        self.dt = dt.astimezone(UTC)

    def settz(self, tz):
        self.tz = tz
        self.set_local(self.ld.replace(tzinfo=None))

    def dateforcalc(self):
        """Return (year, month, day, hour_as_float) in UT for ephemeris use."""
        t = self.dt
        h = t.hour + (t.minute + t.second / 60.0) / 60.0
        return t.year, t.month, t.day, h

    def getnewdt(self, dateset):
        """Convert a (y, m, d, hour_float) UT tuple to a local aware datetime.

        Ported verbatim from legacy NeXDate.getnewdt (Py2 -> Py3:
        timezone('utc') -> UTC). Used by solar_rev to render the return date.
        """
        y, m, d, h = dateset
        ho = int(h)
        mi = (h - ho) * 60
        se = int((mi - int(mi)) * 60)
        mi = int(mi)
        dt = datetime(y, m, d, ho, mi, se, tzinfo=UTC)
        loc = dt.astimezone(self.tz)
        return loc
