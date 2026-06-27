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
