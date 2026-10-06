"""Unit checks for the knowledge base, evidence fusion, photo screening, storage and weather summary.

Run from the project root:  python -m tests.core_test
Synthetic images below are TEST FIXTURES only (solid colours) – they are never shown to users.
"""
import io
import sys
import tempfile
from pathlib import Path

import pandas as pd
from PIL import Image

from src import fusion, knowledge, weather
from src.image_analysis import ANALYZER, prepare_for_storage
from src.storage import SQLiteStore

FAIL = []


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        FAIL.append(msg)


def img_bytes(color, size=(400, 300), exif_gps=False):
    im = Image.new("RGB", size, color)
    buf = io.BytesIO()
    if exif_gps:
        ex = Image.Exif()
        ex[0x8825] = {1: "N", 2: (27.0, 24.0, 0.0)}  # GPSInfo
        ex[0x010F] = "TestCamera"
        im.save(buf, format="JPEG", exif=ex)
    else:
        im.save(buf, format="PNG")
    return buf.getvalue()


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
    m = fusion.matching_problems("cereals", ["rust_pustules", "streaks"])
    check(bool(m) and m[0]["problem"]["id"] == "stripe_rust", "symptom matching finds stripe rust for pustules + streaks")
    check(all("%" not in fusion.reason_text(x, True) or "رطوبة" in fusion.reason_text(x, True)
              for c in r for x in c["reasons"]), "reasons render in Arabic")

    # --- photo screening ---
    g = ANALYZER.analyze(img_bytes((40, 140, 50)))
    check(g["ok"] and g["green_share"] > 0.9 and not g["signals"], "green leaf colour → no warning signals")
    y = ANALYZER.analyze(img_bytes((215, 190, 40)))
    check(y["ok"] and "photo_yellow" in y["signals"], "yellow tissue → photo_yellow signal")
    check(not ANALYZER.analyze(img_bytes((40, 140, 50), size=(100, 80)))["ok"], "too-small photo rejected")
    check(not ANALYZER.analyze(img_bytes((5, 5, 5)))["ok"], "too-dark photo rejected")
    check(not ANALYZER.analyze(b"not an image")["ok"], "unreadable file rejected")
    clean = prepare_for_storage(img_bytes((40, 140, 50), exif_gps=True))
    ex = Image.open(io.BytesIO(clean)).getexif()
    check(0x8825 not in ex and 0x010F not in ex, "EXIF (GPS, camera) removed before storage")

    # --- storage (SQLite) ---
    with tempfile.TemporaryDirectory() as d:
        st = SQLiteStore(Path(d))
        oid = st.save_observation({"session_id": "s1", "zone_id": "A4", "crop_id": "fodder", "symptoms": ["wilting"],
                                   "possible_causes": [{"cause": "water", "score": 5, "level": "strong"}]}, clean)
        st.save_observation({"session_id": "s2", "zone_id": "B1"}, None)
        rows = st.list_observations("s1")
        check(len(rows) == 1 and rows[0]["id"] == oid and rows[0]["symptoms"] == ["wilting"], "observation saved and read back (JSON fields)")
        check(st.get_image(rows[0]["photo_path"]) == clean, "photo stored and retrievable")
        check(len(st.list_observations("s2")) == 1 and all(r["session_id"] == "s1" for r in rows), "sessions only see their own observations")
        st.save_validation({"session_id": "s1", "observation_id": oid, "ray_prediction": "water", "field_check": "soil_not_dry", "actual_cause": "pest"})
        check(len(st.list_validations([oid])) == 1, "field validation saved and linked")
        check(st.counts() == {"observations": 2, "validations": 1, "photos": 1}, f"counts {st.counts()}")

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
