"""DEMO DATA generator -- SIMULATED, NOT SATELLITE OBSERVATIONS.

This module synthesises a small farm with four centre-pivot fields so the
application can be demonstrated without Earth Engine credentials or internet.
Reflectances are produced by mixing typical soil and vegetation spectra; every
index is then computed from those synthetic bands with exactly the same code
used for real Sentinel-2 data. Nothing here should be interpreted as a
measurement of any real place.

Scenario (known by construction, useful for demonstrating the pipeline):
  * NW pivot  – healthy crop
  * NE pivot  – a sector develops progressive water stress late in the period
  * SW pivot  – fallow (no active crop)
  * SE pivot  – mild whole-field stress late in the period
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter

from .config import VEG_NDVI_MIN
from .indices import compute_indices

BANDS = ["B2", "B3", "B4", "B5", "B8", "B11"]
SOIL = np.array([0.12, 0.17, 0.24, 0.28, 0.32, 0.42], dtype="float32")
VEG_WET = np.array([0.03, 0.07, 0.03, 0.10, 0.45, 0.18], dtype="float32")
VEG_DRY = np.array([0.05, 0.09, 0.07, 0.15, 0.33, 0.30], dtype="float32")

PIVOTS = [
    # cy, cx (fraction of image, y down), radius, max cover, growth midpoint (0-1 of period), stress type
    dict(cy=0.27, cx=0.27, r=0.21, fmax=0.90, tmid=0.22, stress=None),
    dict(cy=0.27, cx=0.73, r=0.21, fmax=0.90, tmid=0.18, stress="sector"),
    dict(cy=0.73, cx=0.27, r=0.21, fmax=0.04, tmid=0.50, stress=None),
    dict(cy=0.73, cx=0.73, r=0.21, fmax=0.86, tmid=0.30, stress="mild"),
]


def _ramp(t: np.ndarray, t0: float, t1: float) -> np.ndarray:
    return np.clip((t - t0) / (t1 - t0), 0, 1)


class DemoFarm:
    """Synthetic multi-date scene over the AOI bounds."""

    def __init__(self, bounds: tuple[float, float, float, float], n: int = 160, seed: int = 7):
        self.bounds = bounds
        self.n = n
        self.seed = seed
        rng = np.random.default_rng(seed)
        H = W = n
        yy, xx = np.mgrid[0:H, 0:W] / (n - 1)

        dates = pd.date_range(end="2026-09-20", periods=40, freq="5D")
        dates = dates.delete([7, 19, 30])  # a few "cloudy" acquisitions are skipped, as in reality
        self.dates = [d.strftime("%Y-%m-%d") for d in dates]
        T = len(self.dates)
        t = np.linspace(0, 1, T)

        soil_tex = gaussian_filter(rng.normal(0, 1, (H, W)), 6)
        self.soil_tex = (soil_tex / soil_tex.std() * 0.05).astype("float32")

        fc = np.zeros((T, H, W), dtype="float32")
        w = np.ones((T, H, W), dtype="float32")
        for p in PIVOTS:
            d = np.hypot(yy - p["cy"], xx - p["cx"])
            inside = np.clip((p["r"] - d) / 0.01, 0, 1).astype("float32")
            grow = p["fmax"] / (1 + np.exp(-(t - p["tmid"]) / 0.06))
            tex = gaussian_filter(rng.normal(0, 1, (H, W)), 3)
            tex = 1 + 0.06 * tex / tex.std()
            fc += (inside * tex)[None] * grow[:, None, None].astype("float32")
            if p["stress"] == "sector":
                ang = np.degrees(np.arctan2(yy - p["cy"], xx - p["cx"]))
                sector = ((ang > -100) & (ang < 25)).astype("float32") * inside * np.clip(d / p["r"] + 0.3, 0.6, 1)
                # sudden onset (e.g. simulated nozzle blockage) followed by progressive worsening
                sev = 0.55 * (t >= 0.62) + 0.40 * _ramp(t, 0.62, 1.0)
                w -= sev[:, None, None].astype("float32") * sector[None]
            elif p["stress"] == "mild":
                sev = 0.45 * _ramp(t, 0.70, 1.0)
                w -= sev[:, None, None].astype("float32") * inside[None]
        self.fc = np.clip(fc, 0, 0.95)
        self.w = np.clip(w, 0.1, 1.0)
        self.fc_eff = self.fc * (1 - 0.3 * (1 - self.w))

        doy = np.array([pd.Timestamp(d).dayofyear for d in self.dates])
        self.lst_base = 33 + 17 * np.clip(np.sin(np.pi * (doy - 60) / 250), 0, 1)

        # Pre-compute index stacks (T, H, W)
        self.stack = {k: np.empty((T, H, W), dtype="float32") for k in ("NDVI", "NDRE", "NDMI", "LST")}
        for i in range(T):
            idx = compute_indices(self.bands(i))
            for k, v in idx.items():
                self.stack[k][i] = v
            self.stack["LST"][i] = self._lst(i)

    # ------------------------------------------------------------------
    def bands(self, i: int) -> dict[str, np.ndarray]:
        rng = np.random.default_rng(self.seed * 1000 + i)
        fc = self.fc_eff[i][..., None]
        w = self.w[i][..., None]
        veg = w * VEG_WET + (1 - w) * VEG_DRY
        refl = fc * veg + (1 - fc) * SOIL * (1 + self.soil_tex[..., None])
        refl = refl + rng.normal(0, 0.006, refl.shape)
        refl = np.clip(refl, 0.001, 1).astype("float32")
        return {b: refl[..., k] for k, b in enumerate(BANDS)}

    def _lst(self, i: int) -> np.ndarray:
        rng = np.random.default_rng(self.seed * 2000 + i)
        fc, w = self.fc_eff[i], self.w[i]
        lst = self.lst_base[i] - fc * (12 * w + 3 * (1 - w)) + self.soil_tex * 20
        lst = lst + rng.normal(0, 0.7, lst.shape)
        return gaussian_filter(lst, 2).astype("float32")  # thermal data are coarser

    # ------------------------------------------------------------------
    def date_index(self, date: str) -> int:
        return self.dates.index(date)

    def _zone_mask(self, min_lon, min_lat, max_lon, max_lat) -> np.ndarray:
        bx0, by0, bx1, by1 = self.bounds
        n = self.n
        c0 = int(round((min_lon - bx0) / (bx1 - bx0) * n))
        c1 = int(round((max_lon - bx0) / (bx1 - bx0) * n))
        r0 = int(round((by1 - max_lat) / (by1 - by0) * n))
        r1 = int(round((by1 - min_lat) / (by1 - by0) * n))
        m = np.zeros((n, n), dtype=bool)
        m[max(r0, 0) : min(r1, n), max(c0, 0) : min(c1, n)] = True
        return m

    def zone_stats(self, zones: pd.DataFrame, date: str, prev_date: str | None) -> pd.DataFrame:
        i = self.date_index(date)
        ndvi = self.stack["NDVI"][i]
        veg = ndvi > VEG_NDVI_MIN
        prev = self.stack["NDVI"][self.date_index(prev_date)] if prev_date else None
        recs = []
        for z in zones.itertuples(index=False):
            m = self._zone_mask(z.min_lon, z.min_lat, z.max_lon, z.max_lat)
            mv = m & veg
            rec = {"zone_id": z.zone_id, "clear_frac": 1.0, "veg_frac": float(veg[m].mean())}
            for k in ("NDVI", "NDRE", "NDMI", "LST"):
                rec[k.lower()] = float(np.nanmean(self.stack[k][i][mv])) if mv.any() else np.nan
            rec["ndvi_prev"] = float(np.nanmean(prev[mv])) if (prev is not None and mv.any()) else np.nan
            recs.append(rec)
        return zones.merge(pd.DataFrame(recs), on="zone_id")

    def index_grid(self, date: str, name: str) -> np.ndarray:
        return self.stack[name][self.date_index(date)]

    def veg_mask(self, date: str) -> np.ndarray:
        return self.index_grid(date, "NDVI") > VEG_NDVI_MIN

    def pixel_samples(self, date: str, n: int = 4000) -> pd.DataFrame:
        i = self.date_index(date)
        veg = self.veg_mask(date)
        rows, cols = np.nonzero(veg)
        if rows.size == 0:
            return pd.DataFrame()
        rng = np.random.default_rng(42)
        pick = rng.choice(rows.size, size=min(n, rows.size), replace=False)
        r, c = rows[pick], cols[pick]
        bx0, by0, bx1, by1 = self.bounds
        df = pd.DataFrame(
            {
                "lon": bx0 + (c + 0.5) / self.n * (bx1 - bx0),
                "lat": by1 - (r + 0.5) / self.n * (by1 - by0),
            }
        )
        for k in ("NDVI", "NDRE", "NDMI", "LST"):
            df[k] = self.stack[k][i][r, c]
        return df

    def timeseries(self, bounds: tuple[float, float, float, float]) -> pd.DataFrame:
        m = self._zone_mask(*bounds)
        recs = []
        for i, d in enumerate(self.dates):
            rec = {"date": pd.Timestamp(d)}
            for k in ("NDVI", "NDRE", "NDMI", "LST"):
                rec[k] = float(np.nanmean(self.stack[k][i][m]))
            recs.append(rec)
        return pd.DataFrame(recs)
