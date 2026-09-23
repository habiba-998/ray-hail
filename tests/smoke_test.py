"""Quick end-to-end check of the demo pipeline without the UI.

Run from the project root:  python -m tests.smoke_test
"""
from src import analysis, ml
from src.config import AOI, AOI_PRESETS, DEFAULT_PRESET, Thresholds
from src.demo_data import DemoFarm
from src.preprocessing import make_zone_grid
from src.visualization import build_map, class_donut, timeseries_chart

p = AOI_PRESETS[DEFAULT_PRESET]
aoi = AOI(p["lat"], p["lon"], p["half_km"])
zones = make_zone_grid(aoi, 4, 4)
farm = DemoFarm(aoi.bounds)
date = farm.dates[-1]
prev = analysis.pick_previous_date(farm.dates, date)

zs = farm.zone_stats(zones, date, prev)
scored, ref = analysis.score_zones(zs, Thresholds())
print(f"DEMO date {date} (prev {prev}); farm ref {ref}")
print(scored[["zone_id", "veg_frac", "ndvi", "ndre", "ndmi", "lst_anom", "dndvi", "points", "max_points", "cls"]].round(3).to_string())

pix, feats = ml.isolation_forest(farm.pixel_samples(date))
print("Isolation Forest features:", feats, "| unusual share:", round(pix.anomaly.mean(), 3))
print("Anomaly share by zone:", ml.anomaly_share_by_zone(pix, zones).round(2).to_dict())
print("Supervised status:", ml.supervised_status()["reason"] if not ml.supervised_status()["ready"] else "ready")

ts = farm.timeseries(tuple(zones.iloc[3][["min_lon", "min_lat", "max_lon", "max_lat"]]))
an = analysis.detect_anomalies(ts, "NDVI")
timeseries_chart(ts, None, date, "A4", an)
class_donut(scored)
build_map(aoi.bounds, scored, "A4", image_rgba=None)
print("Charts and map built OK. Classes:", scored.cls.value_counts().to_dict())
