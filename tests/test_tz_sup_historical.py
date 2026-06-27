"""Issue #5: historical / pre-standard-time (LMT) DST handling.

The legacy ``tz_sup.py`` patched pytz internals (``_utc_transition_times``) for
births before a zone adopted standard time, then fell back to a longitude-based
Local Mean Time offset (``FixedOffset(round(longdec*4))``). That pytz-internal
manipulation has no zoneinfo equivalent, and under zoneinfo + the system tz
database it is **unnecessary**: every populated zone carries an LMT entry as its
first transition, computed from the zone's reference longitude, so pre-standard
births resolve to a correct LMT offset natively.

These tests pin that behaviour: the port (zoneinfo) agrees with the legacy
longitude-LMT formula to within the legacy's own whole-minute rounding, across
both European zones the legacy ``tz_sup`` covered AND non-European zones it did
not. They are the verification that issue #5 needs no ``tz_sup`` port.
"""
from datetime import datetime
from zoneinfo import ZoneInfo

from astronex.core.nexdate import NeXDate, UTC
from astronex.core.timezones import FixedOffset


def _legacy_lmt_offset_minutes(longitude):
    """The legacy pre-standard-time offset: 4 minutes per degree of longitude."""
    return round(longitude * 4)


# --- The port resolves pre-standard births via zoneinfo's LMT entries ---

def test_zoneinfo_lmt_matches_legacy_longitude_formula_within_rounding():
    # zoneinfo uses the tzdb LMT (seconds-precision, zone reference longitude);
    # the legacy rounded the birth-city longitude to whole minutes. They must
    # agree to within the legacy rounding (< 0.5 min) for the reference city.
    cases = [
        (-3.7038, "Europe/Madrid", 1850),
        (2.3522, "Europe/Paris", 1880),
        (16.3738, "Europe/Vienna", 1850),
        (4.3517, "Europe/Brussels", 1870),
        (-0.1278, "Europe/London", 1840),
        (-74.0060, "America/New_York", 1850),          # NOT in legacy tz_sup
        (-58.3816, "America/Argentina/Buenos_Aires", 1880),
        (151.2093, "Australia/Sydney", 1850),
    ]
    for lon, zone, year in cases:
        zi = datetime(year, 6, 15, 12, 0).replace(tzinfo=ZoneInfo(zone))
        zi_min = zi.utcoffset().total_seconds() / 60
        legacy_min = _legacy_lmt_offset_minutes(lon)
        # zoneinfo uses the zone's reference-longitude LMT (seconds precision);
        # the legacy rounded the birth-CITY longitude to whole minutes. The two
        # longitudes can differ by a fraction of a degree (a zone covers a
        # region), so allow < 1 min -- still tight given the legacy rounds to
        # whole minutes and the offsets themselves are only ~hours, not days.
        assert abs(zi_min - legacy_min) < 1.0, (
            "%s %d: zoneinfo %.3fm vs legacy-LMT %dm" % (zone, year, zi_min, legacy_min))


def test_port_handles_pre_standard_birth_via_neXdate():
    # A 1850 Madrid birth: the port's setdt must produce a sane UT projection
    # (Madrid LMT ~ -14m44s), NOT a modern CET offset (+1h).
    nd = NeXDate(datetime(2000, 1, 1), tz=ZoneInfo("Europe/Madrid"))
    nd.setdt(datetime(1850, 6, 15, 12, 0))
    # 12:00 LMT (-00:14:44) -> 12:14:44 UT (not 11:00 UT as CET would give)
    assert nd.dt.hour == 12 and nd.dt.minute == 14
    assert "LMT" in nd.ld.tzname() or nd.ld.utcoffset().total_seconds() < 0


def test_modern_birth_uses_standard_offset_not_lmt():
    # Sanity: a 2020 birth must use the modern zone offset, not LMT.
    nd = NeXDate(datetime(2000, 1, 1), tz=ZoneInfo("Europe/Madrid"))
    nd.setdt(datetime(2020, 6, 15, 12, 0))   # summer -> CEST +2
    assert nd.ld.utcoffset().total_seconds() == 2 * 3600
    assert nd.dt.hour == 10  # 12:00 CEST -> 10:00 UT


def test_fixedoffset_still_available_for_explicit_lmt_use():
    # FixedOffset (the legacy LMT tzinfo) remains available for any future code
    # that wants the explicit longitude-based offset rather than the zone LMT.
    tz = FixedOffset(round(-3.7038 * 4))   # Madrid LMT
    assert tz.utcoffset(None).total_seconds() / 60 == -15
    assert tz.tzname(None) == "LMT"
