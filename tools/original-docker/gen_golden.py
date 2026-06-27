# -*- coding: utf-8 -*-
import json, sys
import pysw

EPHEFLAG = 4  # Moshier, matching the legacy default (nex.py ephe_flag = 4)

def dump(ds):
    out = []
    for c in ds:
        jd = pysw.julday(c["y"], c["m"], c["d"], c["h"])
        planets = pysw.planets(jd, EPHEFLAG)        # list of 11 longitudes
        houses = list(pysw.houses(jd, c["lat"], c["lon"]))
        try:
            local = list(pysw.local_houses(jd, c["lon"], c["lat"], EPHEFLAG))
        except Exception as exc:
            local = None
        with_speed = []
        for i in range(12):
            if i == 10:
                continue
            s, lon, spd, err = pysw.calc_ut_with_speed(jd, i, EPHEFLAG)
            with_speed.append([lon, spd])
        out.append({
            "name": c["name"],
            "jd_y": c["y"], "jd_m": c["m"], "jd_d": c["d"], "jd_h": c["h"],
            "lat": c["lat"], "lon": c["lon"], "jd": jd,
            "planets": planets, "houses": houses,
            "local_houses": local, "with_speed": with_speed,
        })
    return out


def dump_directions(ds):
    """Run the ORIGINAL legacy solar_rev/sec_prog via a boss-stub; capture outputs.

    Golden fields per dataset:
      natal_sun_lon, target_year, birth_month, birth_day, zone, now_dt,
      jd_solrev, dt_solrev, progdt, progdt_alltimes

    Output format conventions (the Py3 port MUST match each exactly):
      - natal_dt_iso, now_dt : legacy-internal form "YYYY-MM-DDTHH:MM:SS+0000UTC"
        (what parsestrtime/strdate_to_date consume).
      - jd_solrev            : authoritative solar-return JD (a float), re-derived
                               from the captured UT tuple via pysw.julday. This is
                               the value solar_rev should reproduce; not a datetime.
      - dt_solrev            : local rendering of the return moment,
                               "%Y-%m-%dT%H:%M:%S%z" (zone-aware, offset like +0100).
      - progdt / progdt_alltimes : naive datetime (legacy combine_date strips tz),
                               "%Y-%m-%d %H:%M:%S" (no zone).
    """
    from boss_stub import Boss
    import directions as legacy_dir
    out = []
    for c in ds:
        jd = pysw.julday(c["y"], c["m"], c["d"], c["h"])
        planets = pysw.planets(jd, EPHEFLAG)

        # --- solar_rev (sec_alltimes irrelevant) ---
        boss = Boss(c, planets, epheflag=EPHEFLAG)
        legacy_dir.solar_rev(boss)
        # The legacy passes sol = pysw.revjul(julday) into getnewdt; the stub
        # captured it. Re-derive the authoritative JD from that UT tuple.
        sol_tuple = boss.state.date.captured_sol
        jd_solrev = pysw.julday(sol_tuple[0], sol_tuple[1], sol_tuple[2], sol_tuple[3])
        dt_solrev = boss.da.panel.captured
        dt_solrev_iso = dt_solrev.strftime("%Y-%m-%dT%H:%M:%S%z") if dt_solrev else None

        # --- sec_prog, sec_alltimes=False ---
        boss2 = Boss(c, planets, epheflag=EPHEFLAG)
        boss2.da.sec_alltimes = False
        legacy_dir.sec_prog(boss2)
        progdt = boss2.state.calcdt.captured_setdt
        progdt_iso = progdt.strftime("%Y-%m-%d %H:%M:%S") if progdt else None

        # --- sec_prog, sec_alltimes=True ---
        boss3 = Boss(c, planets, epheflag=EPHEFLAG)
        boss3.da.sec_alltimes = True
        legacy_dir.sec_prog(boss3)
        progdt_all = boss3.state.calcdt.captured_setdt
        progdt_all_iso = progdt_all.strftime("%Y-%m-%d %H:%M:%S") if progdt_all else None

        natal_dt_iso = "%04d-%02d-%02dT%02d:%02d:00+0000UTC" % (
            c["y"], c["m"], c["d"], int(c["h"]), int(round((c["h"] - int(c["h"])) * 60)))

        out.append({
            "name": c["name"],
            "natal_sun_lon": planets[0],
            "target_year": c["target_year"],
            "birth_month": c["m"], "birth_day": c["d"],
            "zone": c["zone"],
            "natal_dt_iso": natal_dt_iso,
            "now_dt": c["now_dt"],
            "jd_solrev": jd_solrev,
            "dt_solrev": dt_solrev_iso,
            "progdt": progdt_iso,
            "progdt_alltimes": progdt_all_iso,
        })
    return out


def dump_chart_types(ds):
    """Run the ORIGINAL legacy Tier-A chart-type methods (pure transforms of
    planets/houses) via a minimal Chart stub; capture outputs.

    These methods read only self.planets / self.houses (no boss, no ephemeris
    call of their own), so the golden verifies EXACT arithmetic parity (no
    engine-tolerance needed). Golden fields per dataset:
      nod_plan[11], nod_sign[12], nodal_cusps[12],
      house_sign_long[12], sign_sizes[12], sign_in_house[12],
      invert_house_plan[11] (inverse of house_plan_long),
      invert_house_sign[12] (inverse of house_sign_long),
      which_house_nodal samples[11]  (per-planet nodal house lookup)
    """
    import chart as legacy_chart

    class _StubChart(legacy_chart.Chart):
        # bypass __init__ (which does not read boss); set planets/houses directly
        def __init__(self, planets, houses):
            self.planets = list(planets)
            self.houses = list(houses)

    # The legacy module-global `orbs` is [] until boss/config populates it at
    # runtime. Populate it with the default table (matches the port's
    # DEFAULT_ORBS) so aspects()-dependent methods (pers_force) work headless.
    legacy_chart.orbs = [
        [3.0, 5.0, 6.0, 8.0, 9.0],
        [2.0, 4.0, 5.0, 6.0, 7.0],
        [1.5, 3.0, 4.0, 5.0, 6.0],
        [1.0, 2.0, 3.0, 4.0, 5.0],
        [1.0, 2.0, 2.0, 3.0, 4.0],
    ]

    out = []
    for c in ds:
        jd = pysw.julday(c["y"], c["m"], c["d"], c["h"])
        planets = pysw.planets(jd, EPHEFLAG)
        houses = list(pysw.houses(jd, c["lat"], c["lon"]))
        ch = _StubChart(planets, houses)

        nod_plan = ch.nod_plan_long()
        nod_sign = ch.nod_sign_long()
        nodal_cusps = ch.nodal_cusp_degrees()
        house_sign = ch.house_sign_long()
        sign_sz = ch.sign_sizes()
        sign_in_h = ch.sign_in_house()
        hpl = ch.house_plan_long()
        invert_hp = ch.invert_house_plan(hpl)
        invert_hs = ch.invert_house_sign(house_sign)
        whn = [ch.which_house_nodal(p) for p in planets]

        out.append({
            "name": c["name"],
            "jd_y": c["y"], "jd_m": c["m"], "jd_d": c["d"], "jd_h": c["h"],
            "lat": c["lat"], "lon": c["lon"],
            "planets": planets, "houses": houses,
            "nod_plan": nod_plan, "nod_sign": nod_sign,
            "nodal_cusps": nodal_cusps,
            "house_sign_long": house_sign, "sign_sizes": sign_sz,
            "sign_in_house": sign_in_h,
            "invert_house_plan": invert_hp,
            "invert_house_sign": invert_hs,
            "which_house_nodal": whn,
            # Tier B: local houses (relocated) -- decoupled, computed at the same
            # jd with the dataset lat/lon via the ephemeris directly (no boss).
            "local_houses": list(pysw.local_houses(jd, c["lon"], c["lat"], EPHEFLAG)),
            # Tier D: profession force (output is a 3-tuple, not longitudes)
            "pers_force": list(ch.pers_force()),
        })
    return out


def dump_age_point(ds):
    """Run the ORIGINAL legacy Age Point pointer methods via a stub; capture.

    The pointer (Lebensuhr) advances ~1 house per 6 years of life, sweeping the
    wheel in 72 years. It is PURE arithmetic on house longitudes + age, so the
    golden verifies EXACT parity when the same houses are fed in.

    Golden fields per dataset:
      birth_date_iso : the chart date string the legacy methods parse
      node_lon       : planets[10] (mean node), for the nodal variant
      now_year       : the projection target year (fixed for determinism)
      cycles         : get_cycles(now_dt) result
      pe_radix       : which_degree_today(now, cycles, 'radix')
      pe_nodal       : which_degree_today(now, cycles, 'nodal')
    """
    import chart as legacy_chart

    class _StubChart(legacy_chart.Chart):
        def __init__(self, date_iso, planets, houses):
            self.date = date_iso
            self.planets = list(planets)
            self.houses = list(houses)

    from datetime import datetime

    out = []
    NOW_YEAR = 2025
    now_dt = datetime(NOW_YEAR, 7, 1, 12, 0, 0)
    for c in ds:
        jd = pysw.julday(c["y"], c["m"], c["d"], c["h"])
        planets = pysw.planets(jd, EPHEFLAG)
        houses = list(pysw.houses(jd, c["lat"], c["lon"]))
        # legacy date string format: YYYY-MM-DDTHH:MM:SS+0000UTC
        ho = int(c["h"])
        mi = int(round((c["h"] - ho) * 60))
        date_iso = "%04d-%02d-%02dT%02d:%02d:00+0000UTC" % (
            c["y"], c["m"], c["d"], ho, mi)
        ch = _StubChart(date_iso, planets, houses)

        cycles = ch.get_cycles(now_dt)
        pe_radix = ch.which_degree_today(now_dt, cycles, kind="radix")
        pe_nodal = ch.which_degree_today(now_dt, cycles, kind="nodal")

        out.append({
            "name": c["name"],
            "birth_date_iso": date_iso,
            "houses": houses,
            "node_lon": planets[10],
            "now_year": NOW_YEAR,
            "cycles": cycles,
            "pe_radix": pe_radix,
            "pe_nodal": pe_nodal,
        })
    return out


def dump_age_timetable(ds):
    """Run the ORIGINAL legacy calc_agep (radix full 72-year timetable) + its
    helpers via a stub; capture the exact ordered event list.

    calc_agep produces a biograph: for each of 12 houses (6 years each) an
    ordered list of {day, mon, year, lab, cl} events (house entry, sign cusps,
    planet aspects, midpoints, Huber Pr/Pi low-points). The ORDER matters for
    the GUI, so we capture the exact list (including tie-break from Py2 sort
    stability on equal scusp).

    Golden fields per dataset:
      birth_date_iso, houses, plan[{degree,ix}] (sorted planets input),
      house_degree[12], pl_midpoints[{degree,sign,house,name}],
      age_prog[...]  -- the full calc_agep output (ordered events)
    """
    import chart as legacy_chart

    class _StubChart(legacy_chart.Chart):
        def __init__(self, date_iso, planets, houses):
            self.date = date_iso
            self.planets = list(planets)
            self.houses = list(houses)

    out = []
    for c in ds:
        jd = pysw.julday(c["y"], c["m"], c["d"], c["h"])
        planets = pysw.planets(jd, EPHEFLAG)
        houses = list(pysw.houses(jd, c["lat"], c["lon"]))
        ho = int(c["h"])
        mi = int(round((c["h"] - ho) * 60))
        date_iso = "%04d-%02d-%02dT%02d:%02d:00+0000UTC" % (
            c["y"], c["m"], c["d"], ho, mi)
        ch = _StubChart(date_iso, planets, houses)

        # plan input: sorted [{degree, ix}], exactly as roundedcharts.sortplan
        plan = [{"degree": planets[i], "ix": i} for i in range(11)]
        plan = sorted(plan)

        house_degree = ch.house_degree()
        mids = ch.pl_midpoints(plan)
        age_prog = ch.calc_agep(plan)

        out.append({
            "name": c["name"],
            "birth_date_iso": date_iso,
            "houses": houses,
            "plan": plan,
            "house_degree": house_degree,
            "pl_midpoints": mids,
            "age_prog": age_prog,
        })
    return out


def dump_dynamics(ds):
    """Run the ORIGINAL legacy dynamics/cross-points/rays methods via a stub;
    capture outputs. These feed the datasheets/diagrams renderers.

    Pure numeric/text calculation (no ephemeris call of its own), so the golden
    verifies EXACT parity. Golden fields per dataset:
      signdyn, housedyn  : {elem, cross} dicts
      dyncalc_list       : [srow, hrow, dif] string rows
      dynstar_signs/houses, dyn_span_diff : 12-lists
      cuad_plan          : [ind, you, col, ii] lists of {degree,ix,conflict}
      which_all_houses   : 12-lists of (d,i,l) which_sign dicts
      which_all_signs    : 11-list of which_sign dicts
      rays_calc          : 8-list of ints
      cross_point        : float (calc_cross_points())
      cross_point_full   : {cp1,cp2,dat1,dat2} (calc_cross_points(cross=True))
    """
    import chart as legacy_chart

    class _StubChart(legacy_chart.Chart):
        def __init__(self, planets, houses):
            self.date = "2000-01-01T00:00:00+0000UTC"  # for cp_time_lapsus
            self.planets = list(planets)
            self.houses = list(houses)

    out = []
    for c in ds:
        jd = pysw.julday(c["y"], c["m"], c["d"], c["h"])
        planets = pysw.planets(jd, EPHEFLAG)
        houses = list(pysw.houses(jd, c["lat"], c["lon"]))
        ch = _StubChart(planets, houses)

        out.append({
            "name": c["name"],
            "planets": planets, "houses": houses,
            "signdyn": ch.signdyn(),
            "housedyn": ch.housedyn(),
            "dyncalc_list": list(ch.dyncalc_list()),
            "dynstar_signs": ch.dynstar_signs(),
            "dynstar_houses": ch.dynstar_houses(),
            "dyn_span_diff": ch.dyn_span_diff(),
            "cuad_plan": [[dict(e) for e in group] for group in ch.cuad_plan()],
            "which_all_houses": ch.which_all_houses(),
            "which_all_signs": ch.which_all_signs(),
            "rays_calc": ch.rays_calc(),
            "cross_point": ch.calc_cross_points(),
            "cross_point_full": ch.calc_cross_points(cross=True),
        })
    return out


if __name__ == "__main__":
    ds = json.load(open(sys.argv[1]))
    mode = sys.argv[3] if len(sys.argv) > 3 else "ephemeris"
    if mode == "directions":
        result = dump_directions(ds)
    elif mode == "chart_types":
        result = dump_chart_types(ds)
    elif mode == "age_point":
        result = dump_age_point(ds)
    elif mode == "age_timetable":
        result = dump_age_timetable(ds)
    elif mode == "dynamics":
        result = dump_dynamics(ds)
    else:
        result = dump(ds)
    json.dump(result, open(sys.argv[2], "w"), indent=2)
    print("wrote %s" % sys.argv[2])
