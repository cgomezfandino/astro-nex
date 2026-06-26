# -*- coding: utf-8 -*-
from datetime import tzinfo, timedelta


class FixedOffset(tzinfo):
    """Fixed offset in minutes east of UTC (used for pre-standard-time longitudes)."""

    def __init__(self, minutes):
        if abs(minutes) >= 1440:
            raise ValueError("absolute offset is too large", minutes)
        self._minutes = minutes
        self._offset = timedelta(minutes=minutes)

    def utcoffset(self, dt):
        return self._offset

    def dst(self, dt):
        return timedelta(0)

    def tzname(self, dt):
        return "LMT"

    def __repr__(self):
        return "FixedOffset(%d)" % self._minutes
