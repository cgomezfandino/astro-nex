from datetime import datetime
from zoneinfo import ZoneInfo
from astronex.core.nexdate import NeXDate


def test_dateforcalc_converts_to_ut():
    # 1985-06-15 08:30 in London (BST, +1) -> 07:30 UT
    nd = NeXDate(datetime(1985, 6, 15, 8, 30), tz=ZoneInfo("Europe/London"))
    y, m, d, h = nd.dateforcalc()
    assert (y, m, d) == (1985, 6, 15)
    assert abs(h - 7.5) < 1e-6


def test_utc_input_is_identity():
    nd = NeXDate(datetime(2000, 1, 1, 0, 0), tz=ZoneInfo("UTC"))
    y, m, d, h = nd.dateforcalc()
    assert (y, m, d, round(h, 6)) == (2000, 1, 1, 0.0)


def test_getnewdt_converts_ut_tuple_to_local():
    # 2025-06-15 12:00 UT -> 14:00 in Madrid (CEST, +2)
    nd = NeXDate(datetime(2025, 1, 1), tz=ZoneInfo("UTC"))
    nd.tz = ZoneInfo("Europe/Madrid")
    loc = nd.getnewdt((2025, 6, 15, 12.0))
    assert loc.year == 2025 and loc.month == 6 and loc.day == 15
    assert loc.hour == 14 and loc.minute == 0


# --- setdt: naive local datetime -> aware local + UT (fold=1 = prefer DST) ---

def test_setdt_localizes_naive_datetime():
    # 1985-06-15 08:30 local in London (BST, +1) -> 07:30 UT
    nd = NeXDate(datetime(2000, 1, 1), tz=ZoneInfo("Europe/London"))
    nd.setdt(datetime(1985, 6, 15, 8, 30))
    y, m, d, h = nd.dateforcalc()
    assert (y, m, d) == (1985, 6, 15)
    assert abs(h - 7.5) < 1e-6


def test_setdt_round_trip_local_ut_consistent():
    # setdt(local) then dt must equal local_aware.astimezone(UTC)
    from astronex.core.nexdate import UTC
    local_naive = datetime(2000, 7, 20, 20, 17)
    nd = NeXDate(datetime(2000, 1, 1), tz=ZoneInfo("Europe/Paris"))
    nd.setdt(local_naive)
    expected = local_naive.replace(tzinfo=ZoneInfo("Europe/Paris")).astimezone(UTC)
    assert nd.dt == expected


def test_setdt_ambiguous_time_prefers_dst_fold0():
    # 2023-10-29 02:30 in Madrid is ambiguous (DST fall-back: 02:30 occurs twice).
    # Legacy is_dst=True = CEST (+2) -> 00:30 UT; zoneinfo fold=0 = the earlier
    # (DST) side, matching. fold=1 would give CET (+1) -> 01:30 UT.
    nd = NeXDate(datetime(2000, 1, 1), tz=ZoneInfo("Europe/Madrid"))
    nd.setdt(datetime(2023, 10, 29, 2, 30))
    assert nd.dt.hour == 0 and nd.dt.minute == 30


# --- set_now ---

def test_set_now_sets_current_time():
    # set_now uses datetime.now() (naive, system-local) localized to self.tz.
    # Use the system zone so the comparison against now(utc) is meaningful.
    import time as _time
    sys_zone = _time.tzname[0] or "UTC"
    try:
        from datetime import timezone
        nd = NeXDate(datetime(2000, 1, 1), tz=ZoneInfo(sys_zone))
    except Exception:
        nd = NeXDate(datetime(2000, 1, 1), tz=ZoneInfo("UTC"))
    nd.set_now()
    drift = abs((nd.dt - datetime.now(timezone.utc)).total_seconds())
    assert drift < 5


# --- dateforstore: serialize ld to ISO-ish string ---

def test_dateforstore_modern_round_trips_through_strdate_to_date():
    from astronex.core.utils import strdate_to_date
    nd = NeXDate(datetime(1985, 6, 15, 8, 30), tz=ZoneInfo("Europe/London"))
    s = nd.dateforstore()
    # strdate_to_date recovers the same UT instant (naive UTC)
    recovered = strdate_to_date(s)
    assert recovered.year == 1985 and recovered.month == 6 and recovered.day == 15
    assert recovered.hour == 8 and recovered.minute == 30


def test_dateforstore_modern_format():
    nd = NeXDate(datetime(2020, 1, 15, 9, 30), tz=ZoneInfo("UTC"))
    s = nd.dateforstore()
    # strftime branch: YYYY-MM-DDTHH:MM:SS+0000UTC
    assert s.startswith("2020-01-15T09:30:00")


# --- set_delta: calendar arithmetic ---

def test_set_delta_minutes():
    nd = NeXDate(datetime(2020, 6, 15, 12, 0), tz=ZoneInfo("UTC"))
    nd.set_delta((30, "minutes"))
    assert nd.ld.hour == 12 and nd.ld.minute == 30


def test_set_delta_days():
    nd = NeXDate(datetime(2020, 6, 15, 12, 0), tz=ZoneInfo("UTC"))
    nd.set_delta((10, "days"))
    assert nd.ld.day == 25


def test_set_delta_month_rollover_clamps_feb():
    # Jan 31 + 1 month -> Feb 28/29 (legacy clamp: try day, day-1, day-2)
    nd = NeXDate(datetime(2020, 1, 31, 12, 0), tz=ZoneInfo("UTC"))
    nd.set_delta((1, "month"))
    assert nd.ld.month == 2 and nd.ld.day == 29  # 2020 is a leap year


def test_set_delta_getback_returns_without_applying():
    nd = NeXDate(datetime(2020, 6, 15, 12, 0), tz=ZoneInfo("UTC"))
    result = nd.set_delta((5, "days"), getback=True)
    assert result.day == 20
    assert nd.ld.day == 15  # not applied

