# -*- coding: utf-8 -*-
"""
NeXDate: local datetime → UT conversion for ephemeris calculations.

Ported from legacy Python 2 / pytz implementation to Python 3 / zoneinfo.

Intentionally deferred to a later milestone:
  - tz_sup historical-DST patching (oldtimes transition-time patching) -- issue #5:
    under zoneinfo + the system tz database, named zones already resolve LMT
    offsets correctly, so the legacy longitude-based FixedOffset branch is not
    needed for the standard path.
"""
from datetime import datetime, timedelta
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
            # fold=0 honors the legacy pytz localize(is_dst=True) intent for
            # ambiguous wall-clock times (DST fall-back): in zoneinfo fold=0 is
            # the EARLIER instant, i.e. the DST side -- matching is_dst=True.
            dt = dt.replace(tzinfo=self.tz)
        self.ld = dt
        self.dt = dt.astimezone(UTC)

    def setdt(self, dt):
        """Set the held instant from a naive local datetime.

        Standard path (post-standard-time): identical to ``set_local``. The
        legacy's pre-standard-time branch (longitude-based LMT via FixedOffset,
        gated by bisect_right on tz internals) is deferred to issue #5: under
        zoneinfo + the system tz database, named zones already resolve LMT
        offsets correctly for the pre-standard era.
        """
        self.set_local(dt)

    def set_now(self):
        """Set the held instant to the wall-clock now."""
        self.setdt(datetime.now())

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

    def set_delta(self, delta, getback=False):
        """Calendar arithmetic on the held local datetime.

        ``delta`` is ``(amount, unit)`` where unit is one of
        'minutes'/'hours'/'days'/'month'/'year'. Month rollover clamps to the
        last valid day of the target month (legacy tries day, day-1, day-2).
        With ``getback=True`` returns the computed datetime without applying.
        """
        amount, what = delta[0], delta[1]
        dt = datetime.combine(self.ld.date(), self.ld.time())
        if what == "minutes":
            dt = dt + timedelta(minutes=amount)
        elif what == "hours":
            dt = dt + timedelta(hours=amount)
        elif what == "days":
            dt = dt + timedelta(days=amount)
        elif what == "month":
            change = dt.month + amount
            if change < 1:
                y, m = dt.year - 1, 12 + change
            elif change > 12:
                y, m = dt.year + 1, change - 12
            else:
                y, m = dt.year, change
            try:
                dt = dt.replace(year=y, month=m)
            except ValueError:
                try:
                    dt = dt.replace(year=y, month=m, day=dt.day - 1)
                except ValueError:
                    dt = dt.replace(year=y, month=m, day=dt.day - 2)  # February
        elif what == "year":
            dt = dt.replace(year=(dt.year + amount))
        if not getback:
            self.setdt(dt)
        else:
            return dt

    def dateforstore(self):
        """Serialize the held local datetime to the legacy storage string.

        Two branches for parity with the legacy:
          * pre-1900: manual formatting (legacy strftime couldn't handle <1900);
            produces ``+HH:MMzone`` or ``+HH00zone``.
          * else: strftime ``%Y-%m-%dT%H:%M:%S%z%Z``.
        Both round-trip through ``utils.strdate_to_date``.
        """
        if self.ld.year < 1900:
            mth = str(self.ld.month).rjust(2, "0")
            day = str(self.ld.day).rjust(2, "0")
            hour = str(self.ld.hour).rjust(2, "0")
            minute = str(self.ld.minute).rjust(2, "0")
            sec = str(self.ld.second).rjust(2, "0")
            zname = self.ld.tzname()
            td = self.ld.utcoffset()
            d, s = td.days, td.seconds
            if d < 0:
                sign = "-"
                s = 86400 - s
            else:
                sign = "+"
            total_min = s // 60
            hpart = sign + str(total_min // 60).rjust(2, "0")
            if total_min % 60 != 0:
                hpart += ":" + str(total_min % 60).rjust(2, "0")
            else:
                hpart += "00"
            return "%s-%s-%sT%s:%s:%s%s%s" % (
                self.ld.year, mth, day, hour, minute, sec, hpart, zname)
        else:
            return self.ld.strftime("%Y-%m-%dT%H:%M:%S%z%Z")
