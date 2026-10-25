"""Unit checks for the knowledge base, evidence fusion, storage and weather summary.

Run from the project root:  python -m tests.core_test
"""
import sys
import tempfile
from pathlib import Path

import pandas as pd

from src import fusion, knowledge, weather
from src.storage import SQLiteStore

FAIL = []


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        FAIL.append(msg)


def zone(points: dict, cls="HIGH"):
    names = ["NDMI (canopy water)", "NDRE (chlorophyll)", "NDVI vs farm median", "LST vs farm mean (°C)", "NDVI change (~2 weeks)"]
    return {"zone_id": "A4", "cls": cls, "rules": {n: (points.get(n), 0.0, "") for n in names}}


def main() -> int:
    # --- knowledge base ---
    errs = knowledge.validate()
    check(not errs, f"knowledge base integrity ({errs[:2]})")
    check(all(p.get("source") for p in knowledge.all_problems()), "every disease/pest has a source")
    check(all(im["license"] for im in knowledge._load()["images"].values()), "every reference image has a licence")
    check(knowledge.crop("date_palm")["water_requirement_mm"] is None, "missing data stays missing (date palm water need)")
    check(len(knowledge.problems_for("cereals")) >= 3, "cereals have sourced problems")

    # --- fusion ---
    z = zone({"NDMI (canopy water)": 2, "LST vs farm mean (°C)": 2, "NDRE (chlorophyll)": 1, "NDVI vs farm median": 2})
    top = fusion.possible_causes(z)[0]
    check(top["cause"] == "water" and top["level"] in ("moderate", "strong"), f"satellite-only evidence ranks water first ({top['cause']}, {top['level']})")
    r = fusion.possible_causes(z, symptoms=["insects_visible", "honeydew"], soil="wet", spread="one")
    check(r[0]["cause"] == "pest", f"insects + honeydew + wet soil ranks pest first ({r[0]['cause']})")
    water = next(x for x in r if x["cause"] == "water")
    check(water["score"] < next(x for x in fusion.possible_causes(z) if x["cause"] == "water")["score"], "wet soil lowers water-stress evidence")
    hot = fusion.possible_causes(zone({}, "HEALTHY"), weather={"hot": True, "tmax_mean": 42.0})
    check(hot[0]["cause"] == "heat", "hot weather adds heat-stress evidence")
    none = fusion.possible_causes(zone({}, "HEALTHY"))
    check(all(x["level"] == "none" for x in none), "no evidence → 'no evidence yet' for every cause")
    check(all("%" not in fusion.reason_text(x, True) or "رطوبة" in fusion.reason_text(x, True)
              for c in r for x in c["reasons"]), "reasons render in Arabic")

    # --- storage (SQLite) ---
    with tempfile.TemporaryDirectory() as d:
        st = SQLiteStore(Path(d))
        base = {"session_id": "s1", "zone_id": "A4", "crop_id": "fodder", "inspection_date": "2026-10-01",
                "condition": "needs_attention", "irrigation_issue": "yes", "alt_causes": ["heat"], "soil_moisture_pct": 12.5}
        oid = st.save_observation(base)
        st.save_observation({**base, "session_id": "s2", "zone_id": "B1", "condition": "no_problem", "irrigation_issue": "no",
                             "alt_causes": None, "soil_moisture_pct": None})
        rows = st.list_observations("s1")
        check(len(rows) == 1 and rows[0]["id"] == oid and rows[0]["alt_causes"] == ["heat"] and rows[0]["soil_moisture_pct"] == 12.5,
              "inspection saved and read back (JSON + numeric fields)")
        check(len(st.list_observations("s2")) == 1 and all(r["session_id"] == "s1" for r in rows), "sessions only see their own records")
        for bad in ({**base, "condition": "x"}, {**base, "soil_moisture_pct": 140}, {**base, "zone_id": ""}, {**base, "alt_causes": ["ufo"]}):
            try:
                st.save_observation(bad)
                check(False, f"invalid record rejected {bad}")
            except ValueError:
                check(True, "invalid inspection record rejected")
        check(st.counts() == {"observations": 2}, f"counts {st.counts()}")

    # --- weather summary ---
    df = pd.DataFrame({"date": pd.date_range("2026-09-15", periods=10), "air_temp_c": 33.0, "air_temp_max_c": 41.0,
                       "precip_mm": 0.0, "rel_humidity_pct": 12.0, "wind_speed_ms": 3.0, "source": "ERA5-Land"})
    s = weather.summarize(df, "2026-09-22")
    check(s["n_days"] == 7 and s["hot"] and s["dry_air"] and not s["rain"], "weather summary over the 7 days before the image")
    s2 = weather.summarize(df, "2026-10-06")
    check(s2 and s2["last_date"] == "2026-09-24", "reanalysis lag: falls back to the latest available days")
    res = weather.get_weather(27, 42, "2026-09-01", "2026-09-02", lambda *a: pd.DataFrame())
    check(res.source_id == "none" and not res.statuses[0].connected, "NCM reported as not connected; no data fabricated")

    print(f"\n{'ALL PASS' if not FAIL else f'{len(FAIL)} FAILURE(S)'}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
