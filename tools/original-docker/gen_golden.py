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
      natal_sun_lon, target_year, birth_month, birth_day, zone, natal_dt_iso,
      now_dt, jd_solrev, dt_solrev, progdt, progdt_alltimes
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


if __name__ == "__main__":
    ds = json.load(open(sys.argv[1]))
    mode = sys.argv[3] if len(sys.argv) > 3 else "ephemeris"
    if mode == "directions":
        result = dump_directions(ds)
    else:
        result = dump(ds)
    json.dump(result, open(sys.argv[2], "w"), indent=2)
    print("wrote %s" % sys.argv[2])
