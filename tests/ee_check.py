"""Verify the REAL Earth Engine path using the app's own functions (no UI).

Run from the project root after `earthengine authenticate`:
    python -m tests.ee_check YOUR_PROJECT_ID

Every step prints PASS/FAIL. Nothing is reported as real unless the query returns it.
"""
import io
import math
import sys
import urllib.request
from datetime import date, timedelta

import numpy as np
from PIL import Image

from src import analysis
from src import data_acquisition as gee
from src.config import AOI, AOI_PRESETS, DEFAULT_PRESET, Thresholds
from src.preprocessing import make_zone_grid


def tile_xy(lat, lon, z):
    n = 2**z
    x = int((lon + 180) / 360 * n)
    y = int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)
    return x, y


def main(project: str | None) -> int:
    ok, msg = gee.init_earth_engine(project)
    print(f"[{'PASS' if ok else 'FAIL'}] Earth Engine init: {msg}")
    if not ok:
        return 1

    p = AOI_PRESETS[DEFAULT_PRESET]
    aoi = AOI(p["lat"], p["lon"], p["half_km"])
    bounds = tuple(round(b, 6) for b in aoi.bounds)
    end = date.today()
    start = end - timedelta(days=150)
    print(f"AOI: {DEFAULT_PRESET} centre {p['lat']}, {p['lon']}, bounds {bounds}; period {start}..{end}")

    dates = gee.list_s2_dates(bounds, str(start), str(end + timedelta(days=1)), 30)
    print(f"[{'PASS' if dates else 'FAIL'}] Sentinel-2 acquisitions (scene cloud < 30% AND AOI ≥ 50% clear): {len(dates)}"
          + (f", first {dates[0]}, last {dates[-1]}" if dates else ""))
    if not dates:
        return 1
    d = dates[-1]
    prev = analysis.pick_previous_date(dates, d)

    zones = make_zone_grid(aoi, 4, 4)
    zs, meta = gee.zone_stats(bounds, zones.to_dict("records"), d, prev)
    scored, ref = analysis.score_zones(zs, Thresholds())
    has_vals = zs[["ndvi", "ndre", "ndmi"]].notna().any().all()
    print(f"[{'PASS' if has_vals else 'FAIL'}] Zone statistics for {d} (compared with {prev}); Landsat dates: {meta['lst_dates']}")
    print(scored[["zone_id", "clear_frac", "veg_frac", "ndvi", "ndre", "ndmi", "lst", "cls"]].round(3).to_string(index=False))
    print(f"Farm reference: {ref}")

    x, y = tile_xy(p["lat"], p["lon"], 14)
    for layer in ("True Color", "NDVI", "NDRE", "NDMI"):
        try:
            url = gee.layer_tile_url(bounds, d, layer, ref["ndvi_median"] if ref["ndvi_median"] == ref["ndvi_median"] else 0.6, vars(Thresholds()))
            # The first tile of a NEW map layer is computed on demand and the server may close that first request;
            # retry up to twice and report it (the app warms tiles in the background for the same reason).
            for retries in range(3):
                try:
                    with urllib.request.urlopen(url.format(z=14, x=x, y=y), timeout=60) as r:
                        body, ctype = r.read(), r.headers.get("Content-Type")
                    break
                except Exception:  # noqa: BLE001
                    if retries == 2:
                        raise
            if retries:
                print(f"       ({layer}: succeeded after {retries} retry/retries – cold first tile)")
            alpha = np.asarray(Image.open(io.BytesIO(body)).convert("RGBA"))[..., 3]
            filled = float((alpha > 0).mean())  # share of tile pixels that carry data (not masked)
            good = ctype.startswith("image/") and filled > 0.5
            print(f"[{'PASS' if good else 'FAIL'}] {layer} tile z14/{x}/{y}: {ctype}, {len(body)} bytes, "
                  f"{filled:.0%} of pixels have data")
        except Exception as exc:  # noqa: BLE001
            print(f"[FAIL] {layer} tile: {exc}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
