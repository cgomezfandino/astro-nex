# -*- coding: utf-8 -*-
"""Stub of the legacy ``boss`` object so solar_rev/sec_prog run headless.

Implements ONLY the surface touched by directions.py: captures the outputs we
need for the golden file. Runs under Python 2 inside the Docker container.

Surface audit (from legacy directions.py):
  solar_rev reads : boss.state.curr_chart.date, .curr_chart.planets[0],
                    .date.dt.year, .epheflag, .curr_chart.zone
  solar_rev writes: boss.state.date.getnewdt(sol)  [captured],
                    boss.da.panel.set_date_only(dt) [captured]
  sec_prog  reads : boss.state.curr_chart (with .date), .now, .date.dt.year,
                    .date.dt, boss.da.sec_alltimes
  sec_prog  writes: boss.state.calcdt.setdt(dt)    [captured],
                    boss.state.setprogchart(chart)  [no-op],
                    boss.da.panel.set_date_only(..) [captured]
"""
from datetime import datetime
from pytz import timezone


def _parse_now(now_str):
    # "2025-07-01T12:00:00+0000" -> aware UTC datetime
    base = now_str[:19]
    dt = datetime.strptime(base, "%Y-%m-%dT%H:%M:%S")
    return dt.replace(tzinfo=timezone("UTC"))


class _Panel(object):
    """Absorbs set_date_only (GUI); captures its argument."""
    def __init__(self):
        self.captured = None

    def set_date_only(self, dt):
        self.captured = dt


class _DA(object):
    def __init__(self, sec_alltimes=False):
        self.panel = _Panel()
        self.sec_alltimes = sec_alltimes


class _Date(object):
    """Minimal stand-in for NeXDate: holds .dt (aware UTC) and .tz; replicates
    the legacy getnewdt conversion UT->local so the captured datetime matches
    the real app."""
    def __init__(self, dt, tz):
        self.dt = dt
        self.tz = tz
        self.captured_getnewdt = None
        self.captured_sol = None
        self.captured_setdt = None

    def getnewdt(self, dateset):
        self.captured_sol = dateset          # UT tuple input, for golden capture
        y, m, d, h = dateset
        ho = int(h)
        mi = (h - ho) * 60
        se = int((mi - int(mi)) * 60)
        mi = int(mi)
        dt = datetime(y, m, d, ho, mi, se, tzinfo=timezone("utc"))
        loc = dt.astimezone(self.tz)
        self.captured_getnewdt = loc
        return loc

    def setdt(self, dt):
        self.captured_setdt = dt


class _Chart(object):
    def __init__(self, date_str, planets, zone):
        self.date = date_str
        self.planets = planets
        self.zone = zone


class _State(object):
    def __init__(self, ds, planets, now_dt, zone, epheflag):
        self.epheflag = epheflag
        # ISO date string the legacy expects: YYYY-MM-DDTHH:MM:SS+0000UTC
        # (parsestrtime/strdate_to_date both parse this form)
        y, mo, d = ds["y"], ds["m"], ds["d"]
        ho = int(ds["h"])
        mif = int(round((ds["h"] - ho) * 60))
        date_str = "%04d-%02d-%02dT%02d:%02d:00+0000UTC" % (y, mo, d, ho, mif)
        self.curr_chart = _Chart(date_str, planets, zone)
        self.now = _Chart(date_str, planets, zone)   # sec_prog fallback; only used
                                                      # when curr_chart.date is falsy
                                                      # (not exercised by these datasets)
        tz = timezone(zone)
        self.date = _Date(now_dt, tz)
        # calcdt is a SEPARATE _Date so sec_prog's setdt capture is independent of
        # solar_rev's getnewdt capture on .date (no aliasing).
        self.calcdt = _Date(now_dt, tz)
        self._zone = zone

    def setprogchart(self, chart):
        pass   # no-op for golden capture

    def settz(self, zone):
        self._zone = zone


class Boss(object):
    """Builds the stub from a dataset + precomputed natal planets."""
    def __init__(self, ds, planets, epheflag=4):
        now_dt = _parse_now(ds["now_dt"])
        self.da = _DA()
        self.state = _State(ds, planets, now_dt, ds["zone"], epheflag)
