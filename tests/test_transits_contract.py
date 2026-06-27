"""Transits (Tier C) contract: a transit chart is a second radix Chart computed
at the transit JD, paired with the natal. There is no chart-type-specific
transform -- the bi-wheel is two radix charts + aspects between their planets.

This test pins that contract so the GUI layer (Phase 2D) has a stable basis.
"""
from datetime import datetime
from zoneinfo import ZoneInfo
from astronex.core.chart import Chart
from astronex.core.nexdate import NeXDate


def _transit_aspects(natal, transit):
    """Aspect pairs between natal and transiting planets (cross-chart).

    Mirrors the legacy cross-aspect: for each natal/transit planet pair, the orb
    is the angular distance; keep those within a 9-degree hard cut.
    """
    out = []
    for i, np in enumerate(natal.planets):
        for j, tp in enumerate(transit.planets):
            dis = abs(np - tp)
            orb = dis - int(dis / 30) * 30
            if orb > 20.0:
                orb = 30.0 - orb
            if orb <= 9.0:
                out.append((i, j, round(orb, 4)))
    return out


def test_transit_chart_is_a_second_radix_chart():
    # Natal: 1985-06-15 08:30 London. Transits: "now" = 2025-06-15 12:00 UT.
    natal = Chart()
    natal.calc((1985, 6, 15, 7.5), loc=(51.5074, -0.1278), epheflag=4)

    nd = NeXDate(datetime(2025, 6, 15, 12, 0), tz=ZoneInfo("UTC"))
    transit = Chart()
    transit.calc(nd.dateforcalc(), loc=(51.5074, -0.1278), epheflag=4)

    # Both are full radix charts (11 planets, 12 houses each)
    assert len(natal.planets) == 11 and len(transit.planets) == 11
    assert len(natal.houses) == 12 and len(transit.houses) == 12

    # Cross-chart aspects are computable from the two charts alone (no boss,
    # no extra transform) -- this is the Tier C contract.
    aspects = _transit_aspects(natal, transit)
    assert len(aspects) > 0
    # each aspect is (natal_idx, transit_idx, orb<=9)
    assert all(o <= 9.0 for _, _, o in aspects)
    assert all(0 <= i < 11 and 0 <= j < 11 for i, j, _ in aspects)
