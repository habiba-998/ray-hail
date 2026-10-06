"""REAL DATA acquisition from Google Earth Engine.

Datasets:
  * Sentinel-2 MSI Level-2A surface reflectance (COPERNICUS/S2_SR_HARMONIZED), 10-20 m, ~5-day revisit
  * Landsat 8 & 9 Collection-2 Level-2 surface temperature (ST_B10), 100 m native (served at 30 m)
  * ERA5-Land daily aggregates (air temperature, precipitation), ~11 km reanalysis

All functions take plain Python arguments (tuples / strings / dicts) so they can
be cached by Streamlit. Earth Engine is imported lazily.
"""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd

from .config import (
    ERA5_COLLECTION,
    L8_COLLECTION,
    L9_COLLECTION,
    LANDSAT_WINDOW_DAYS,
    MIN_CLEAR_FRACTION,
    S2_BANDS,
    S2_COLLECTION,
    TS_MIN_CLEAR_FRACTION,
    VEG_NDVI_MIN,
    Thresholds,
)
from .indices import PALETTES, VIS_RANGES
from .preprocessing import landsat_lst_prepare, s2_clear_mask, s2_prepare

Bounds = tuple  # (min_lon, min_lat, max_lon, max_lat)


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------
def init_earth_engine(project: str | None, service_account_json: str | None = None) -> tuple[bool, str]:
    """Try to initialise Earth Engine. Returns (ok, message). Never raises."""
    try:
        import ee
    except ImportError:
        return False, "The 'earthengine-api' package is not installed (pip install earthengine-api)."
    try:
        sa = service_account_json or os.environ.get("EE_SERVICE_ACCOUNT_JSON")
        if sa:
            info = json.loads(sa) if sa.strip().startswith("{") else json.load(open(sa, encoding="utf-8"))
            creds = ee.ServiceAccountCredentials(info["client_email"], key_data=json.dumps(info))
            ee.Initialize(creds, project=project or info.get("project_id"))
        else:
            ee.Initialize(project=project or None)
        ee.Number(1).getInfo()  # round-trip to prove the connection works
        return True, "Connected to Google Earth Engine."
    except Exception as exc:  # noqa: BLE001 -- surface any auth problem to the UI
        return False, f"{type(exc).__name__}: {exc}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _ee():
    import ee

    return ee


def _rect(bounds: Bounds):
    return _ee().Geometry.Rectangle(list(bounds))


def _s2_collection(region, start: str, end: str, max_cloud: int):
    ee = _ee()
    return (
        ee.ImageCollection(S2_COLLECTION)
        .filterBounds(region)
        .filterDate(start, end)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", max_cloud))
    )


def _s2_on_date(region, date: str):
    """Cloud-masked, scaled Sentinel-2 image (bands + indices + CLEAR) for one acquisition day."""
    ee = _ee()
    d = ee.Date(date)
    col = ee.ImageCollection(S2_COLLECTION).filterBounds(region).filterDate(d, d.advance(1, "day")).map(s2_prepare)
    vals = col.select(S2_BANDS + ["NDVI", "NDRE", "NDMI"]).mean()
    return vals.addBands(col.select("CLEAR").max())


def _lst_near(region, date: str):
    """Median Landsat 8/9 LST (deg C) within +/- LANDSAT_WINDOW_DAYS of date, plus the dates used."""
    ee = _ee()
    d = ee.Date(date)
    col = (
        ee.ImageCollection(L8_COLLECTION)
        .merge(ee.ImageCollection(L9_COLLECTION))
        .filterBounds(region)
        .filterDate(d.advance(-LANDSAT_WINDOW_DAYS, "day"), d.advance(LANDSAT_WINDOW_DAYS + 1, "day"))
        .filter(ee.Filter.lt("CLOUD_COVER", 60))
        .map(landsat_lst_prepare)
    )
    times = col.aggregate_array("system:time_start").getInfo()
    if not times:
        return None, []
    dates = sorted({pd.to_datetime(t, unit="ms").strftime("%Y-%m-%d") for t in times})
    return col.select("LST").median(), dates


# ---------------------------------------------------------------------------
# Public API (mirrors DemoFarm)
# ---------------------------------------------------------------------------
def list_s2_dates(bounds: Bounds, start: str, end: str, max_cloud: int, min_aoi_clear: float = MIN_CLEAR_FRACTION) -> list[str]:
    """Acquisition dates whose AOI (not just the whole granule) is mostly cloud-free.

    CLOUDY_PIXEL_PERCENTAGE describes a ~110 km granule, so a scene can pass that filter while the
    farm itself is under cloud. We therefore measure the SCL clear fraction over the AOI for every
    image and keep a date if its best-covering granule is at least `min_aoi_clear` clear.
    """
    ee = _ee()
    region = _rect(bounds)

    def aoi_clear(img):
        frac = s2_clear_mask(img).unmask(0).reduceRegion(
            reducer=ee.Reducer.mean(), geometry=region, scale=60, maxPixels=1e9, bestEffort=True
        ).values().get(0)
        return ee.Feature(None, {"t": img.get("system:time_start"), "clear": frac})

    feats = ee.FeatureCollection(_s2_collection(region, start, end, max_cloud).map(aoi_clear)).getInfo()["features"]
    df = pd.DataFrame([f["properties"] for f in feats])
    if df.empty:
        return []
    df["date"] = pd.to_datetime(df["t"], unit="ms").dt.strftime("%Y-%m-%d")
    best = df.groupby("date")["clear"].max()
    return sorted(best[best >= min_aoi_clear].index)


def zone_stats(bounds: Bounds, zones_records: list[dict], date: str, prev_date: str | None) -> tuple[pd.DataFrame, dict]:
    """Mean indices over cropped pixels in each zone for one date (REAL Sentinel-2 / Landsat)."""
    ee = _ee()
    region = _rect(bounds)
    cur = _s2_on_date(region, date)
    veg = cur.select("NDVI").gt(VEG_NDVI_MIN)
    img = cur.select(["NDVI", "NDRE", "NDMI"]).updateMask(veg)
    img = img.addBands(veg.rename("VEG")).addBands(cur.select("CLEAR"))
    if prev_date:
        prev = _s2_on_date(region, prev_date).select("NDVI").updateMask(veg).rename("NDVI_PREV")
        img = img.addBands(prev)
    lst_img, lst_dates = _lst_near(region, date)
    if lst_img is not None:
        img = img.addBands(lst_img.updateMask(veg).rename("LST"))

    fc = ee.FeatureCollection(
        [
            ee.Feature(ee.Geometry.Rectangle([z["min_lon"], z["min_lat"], z["max_lon"], z["max_lat"]]), {"zone_id": z["zone_id"]})
            for z in zones_records
        ]
    )
    res = img.reduceRegions(collection=fc, reducer=ee.Reducer.mean(), scale=20).getInfo()
    recs = []
    for f in res["features"]:
        p = f["properties"]
        recs.append(
            {
                "zone_id": p["zone_id"],
                "clear_frac": p.get("CLEAR"),
                "veg_frac": p.get("VEG"),
                "ndvi": p.get("NDVI"),
                "ndre": p.get("NDRE"),
                "ndmi": p.get("NDMI"),
                "lst": p.get("LST"),
                "ndvi_prev": p.get("NDVI_PREV"),
            }
        )
    df = pd.DataFrame(recs)
    for c in df.columns.drop("zone_id"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return pd.DataFrame(zones_records).merge(df, on="zone_id"), {"lst_dates": lst_dates}


def layer_tile_url(bounds: Bounds, date: str, layer: str, farm_ref_ndvi: float, thr: dict) -> str | None:
    """XYZ tile URL for a map layer rendered by Earth Engine."""
    region = _rect(bounds)
    cur = _s2_on_date(region, date)
    if layer == "True Color":
        img, vis = cur.select(["B4", "B3", "B2"]), {"min": 0.0, "max": 0.35, "gamma": 1.2}
    elif layer in ("NDVI", "NDRE", "NDMI"):
        lo, hi = VIS_RANGES[layer]
        img, vis = cur.select(layer), {"min": lo, "max": hi, "palette": PALETTES[layer]}
    elif layer == "LST":
        lst, _ = _lst_near(region, date)
        if lst is None:
            return None
        lo, hi = VIS_RANGES["LST"]
        img, vis = lst, {"min": lo, "max": hi, "palette": PALETTES["LST"]}
    elif layer == "Stress (pixel)":
        img, vis = pixel_stress_ee(cur, farm_ref_ndvi, Thresholds(**thr)), {"min": 0, "max": 2, "palette": PALETTES["STRESS"]}
    else:
        return None
    return img.clip(region).getMapId(vis)["tile_fetcher"].url_format


def true_color_png(bounds: Bounds, date: str, width: int = 800) -> bytes:
    """True-colour PNG of the farm for one Sentinel-2 date, computed with ee.data.computePixels.

    Unlike getMapId (tile layers), this needs only the 'computations' permission – the same one the zone statistics
    use – so it works for a service account that is not allowed to create map layers ('earthengine.maps.create').
    """
    ee = _ee()
    region = _rect(bounds)
    img = _s2_on_date(region, date).select(["B4", "B3", "B2"]).visualize(min=0.0, max=0.35, gamma=1.2)
    min_lon, min_lat, max_lon, max_lat = bounds
    height = max(1, int(round(width * (max_lat - min_lat) / (max_lon - min_lon) / np.cos(np.radians((min_lat + max_lat) / 2)))))
    return ee.data.computePixels({
        "expression": img,
        "fileFormat": "PNG",
        "grid": {
            "dimensions": {"width": width, "height": height},
            "affineTransform": {"scaleX": (max_lon - min_lon) / width, "shearX": 0, "translateX": min_lon,
                                "shearY": 0, "scaleY": -(max_lat - min_lat) / height, "translateY": max_lat},
            "crsCode": "EPSG:4326",
        },
    })


def pixel_stress_ee(cur, farm_ref_ndvi: float, t: Thresholds):
    """Per-pixel stress class (0 green, 1 yellow, 2 red) from NDMI, NDRE and relative NDVI."""
    ndvi, ndre, ndmi = cur.select("NDVI"), cur.select("NDRE"), cur.select("NDMI")
    rel = ndvi.divide(max(farm_ref_ndvi, 1e-3))

    def pts(x, high, mod):
        return x.lt(high).multiply(2).add(x.gte(high).And(x.lt(mod)))

    share = pts(ndmi, t.ndmi_high, t.ndmi_mod).add(pts(ndre, t.ndre_high, t.ndre_mod)).add(
        pts(rel, t.ndvi_rel_high, t.ndvi_rel_mod)
    ).divide(6)
    cls = share.gte(t.yellow_share).add(share.gte(t.red_share))
    return cls.updateMask(ndvi.gt(VEG_NDVI_MIN))


def pixel_samples(bounds: Bounds, date: str, n: int = 3000) -> pd.DataFrame:
    """Random cropped-pixel samples of index values (used by the unsupervised anomaly model)."""
    region = _rect(bounds)
    cur = _s2_on_date(region, date)
    img = cur.select(["NDVI", "NDRE", "NDMI"]).updateMask(cur.select("NDVI").gt(VEG_NDVI_MIN))
    lst, _ = _lst_near(region, date)
    if lst is not None:
        img = img.addBands(lst.rename("LST"))
    fc = img.sample(region=region, scale=20, numPixels=n, seed=42, geometries=True).limit(4500)
    feats = fc.getInfo()["features"]
    rows = []
    for f in feats:
        lon, lat = f["geometry"]["coordinates"]
        rows.append({"lon": lon, "lat": lat, **f["properties"]})
    return pd.DataFrame(rows)


def timeseries(bounds: Bounds, start: str, end: str, max_cloud: int) -> pd.DataFrame:
    """Mean NDVI / NDRE / NDMI over all clear pixels of a zone for every Sentinel-2 acquisition."""
    ee = _ee()
    region = _rect(bounds)
    col = _s2_collection(region, start, end, max_cloud).limit(250, "system:time_start").map(s2_prepare)

    def per_image(img):
        stats = img.select(["NDVI", "NDRE", "NDMI", "CLEAR"]).reduceRegion(
            reducer=ee.Reducer.mean(), geometry=region, scale=20, maxPixels=1e9, bestEffort=True
        )
        return ee.Feature(None, stats).set("t", img.get("system:time_start"))

    feats = ee.FeatureCollection(col.map(per_image)).getInfo()["features"]
    df = pd.DataFrame([f["properties"] for f in feats])
    if df.empty or "NDVI" not in df:
        return pd.DataFrame(columns=["date", "NDVI", "NDRE", "NDMI"])
    df["date"] = pd.to_datetime(df["t"], unit="ms").dt.normalize()
    df = df[df["CLEAR"] >= TS_MIN_CLEAR_FRACTION].dropna(subset=["NDVI"])
    return df.groupby("date", as_index=False)[["NDVI", "NDRE", "NDMI"]].mean().sort_values("date")


def lst_timeseries(bounds: Bounds, start: str, end: str) -> pd.DataFrame:
    ee = _ee()
    region = _rect(bounds)
    col = (
        ee.ImageCollection(L8_COLLECTION)
        .merge(ee.ImageCollection(L9_COLLECTION))
        .filterBounds(region)
        .filterDate(start, end)
        .filter(ee.Filter.lt("CLOUD_COVER", 60))
        .map(landsat_lst_prepare)
    )

    def per_image(img):
        stats = img.reduceRegion(reducer=ee.Reducer.mean(), geometry=region, scale=30, maxPixels=1e9, bestEffort=True)
        return ee.Feature(None, stats).set("t", img.get("system:time_start"))

    feats = ee.FeatureCollection(col.map(per_image)).getInfo()["features"]
    df = pd.DataFrame([f["properties"] for f in feats])
    if df.empty or "LST" not in df:
        return pd.DataFrame(columns=["date", "LST"])
    df["date"] = pd.to_datetime(df["t"], unit="ms").dt.normalize()
    df = df[df["CLEAR"] >= TS_MIN_CLEAR_FRACTION].dropna(subset=["LST"])
    return df.groupby("date", as_index=False)["LST"].mean().sort_values("date")


ERA5_BANDS = ["temperature_2m", "temperature_2m_max", "total_precipitation_sum",
              "dewpoint_temperature_2m", "u_component_of_wind_10m", "v_component_of_wind_10m"]


def weather(lat: float, lon: float, start: str, end: str) -> pd.DataFrame:
    """Daily weather from ERA5-Land (reanalysis, ~11 km grid) at the farm centre.

    Columns: air temperature (daily mean / max, °C), precipitation (mm), relative humidity (%, approximated from
    the daily-mean temperature and dew point with the Magnus formula), wind speed (m/s, magnitude of the daily-mean
    10 m wind vector – underestimates gusty days) and wind direction (° the wind blows FROM).
    """
    ee = _ee()
    pt = ee.Geometry.Point([lon, lat])
    col = ee.ImageCollection(ERA5_COLLECTION).filterDate(start, end).select(ERA5_BANDS)

    def per_image(img):
        v = img.reduceRegion(reducer=ee.Reducer.first(), geometry=pt, scale=11132)
        return ee.Feature(None, v).set("t", img.get("system:time_start"))

    feats = ee.FeatureCollection(col.map(per_image)).getInfo()["features"]
    df = pd.DataFrame([f["properties"] for f in feats])
    if df.empty or "temperature_2m" not in df:
        return pd.DataFrame()
    df["date"] = pd.to_datetime(df["t"], unit="ms")
    t = df["temperature_2m"] - 273.15
    out = pd.DataFrame(
        {
            "date": df["date"],
            "air_temp_c": t,
            "air_temp_max_c": df["temperature_2m_max"] - 273.15,
            "precip_mm": df["total_precipitation_sum"] * 1000,
        }
    )
    if "dewpoint_temperature_2m" in df:
        td = df["dewpoint_temperature_2m"] - 273.15
        out["rel_humidity_pct"] = (100 * np.exp(17.625 * td / (243.04 + td)) / np.exp(17.625 * t / (243.04 + t))).clip(0, 100)
    if "u_component_of_wind_10m" in df and "v_component_of_wind_10m" in df:
        u, v = df["u_component_of_wind_10m"], df["v_component_of_wind_10m"]
        out["wind_speed_ms"] = np.hypot(u, v)
        out["wind_dir_deg"] = (270 - np.degrees(np.arctan2(v, u))) % 360
    out["source"] = "ERA5-Land (ECMWF/Copernicus via Google Earth Engine)"
    return out.sort_values("date")


# ---------------------------------------------------------------------------
# Sentinel-1 SAR (supplementary context – NOT used by the stress rules)
# ---------------------------------------------------------------------------
S1_COLLECTION = "COPERNICUS/S1_GRD"


def s1_zone_stats(bounds: Bounds, zones_records: list[dict], date: str, window_days: int = 12) -> tuple[pd.DataFrame, dict]:
    """Mean Sentinel-1 C-band backscatter (VV, VH in dB) per zone from the acquisition closest to `date`.

    Uses IW-mode GRD scenes with both VV and VH. Averaging is done in linear power and converted back to dB.
    Backscatter responds to surface/soil moisture and canopy structure; it is cloud-independent but not
    calibrated for crop stress here, so RAY shows it as context only.
    """
    ee = _ee()
    region = _rect(bounds)
    d = ee.Date(date)
    col = (
        ee.ImageCollection(S1_COLLECTION)
        .filterBounds(region)
        .filterDate(d.advance(-window_days, "day"), d.advance(window_days + 1, "day"))
        .filter(ee.Filter.eq("instrumentMode", "IW"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH"))
    )
    info = col.aggregate_array("system:time_start").getInfo()
    if not info:
        return pd.DataFrame(), {"s1_date": None}
    target = pd.Timestamp(date).value // 10**6
    best = min(info, key=lambda ms: abs(ms - target))
    best_day = pd.to_datetime(best, unit="ms").strftime("%Y-%m-%d")
    bd = ee.Date(best_day)
    day = col.filterDate(bd, bd.advance(1, "day"))
    passes = sorted(set(day.aggregate_array("orbitProperties_pass").getInfo()))
    lin = day.select(["VV", "VH"]).map(lambda im: ee.Image(10).pow(im.divide(10)).copyProperties(im)).mean()
    fc = ee.FeatureCollection(
        [ee.Feature(ee.Geometry.Rectangle([z["min_lon"], z["min_lat"], z["max_lon"], z["max_lat"]]), {"zone_id": z["zone_id"]})
         for z in zones_records]
    )
    res = lin.reduceRegions(collection=fc, reducer=ee.Reducer.mean(), scale=20).getInfo()
    rows = []
    for f in res["features"]:
        p = f["properties"]
        vv, vh = p.get("VV"), p.get("VH")
        vv_db = 10 * np.log10(vv) if vv else np.nan
        vh_db = 10 * np.log10(vh) if vh else np.nan
        rows.append({"zone_id": p["zone_id"], "vv_db": vv_db, "vh_db": vh_db, "vh_minus_vv_db": vh_db - vv_db})
    return pd.DataFrame(rows), {"s1_date": best_day, "orbit_pass": ", ".join(passes)}
