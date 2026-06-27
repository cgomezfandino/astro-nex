# -*- coding: utf-8 -*-
"""Timezone helpers for the chart core.

Provides :class:`FixedOffset`, a constant UTC offset used for births before
standard time existed (local mean time derived from longitude). Standard
named zones are handled with the stdlib :mod:`zoneinfo` in ``nexdate``.
"""
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
