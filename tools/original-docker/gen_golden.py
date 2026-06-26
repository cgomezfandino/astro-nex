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

if __name__ == "__main__":
    ds = json.load(open(sys.argv[1]))
    json.dump(dump(ds), open(sys.argv[2], "w"), indent=2)
    print("wrote %s" % sys.argv[2])
