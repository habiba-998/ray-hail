"""Weather connector layer.

Priority (per design): local official observations (NCM) when an authorised connection exists, otherwise
ERA5-Land reanalysis. Every value carries its source.

Status today:
  * ERA5-Land  – ACTIVE (via Google Earth Engine; ~11 km grid; reanalysis, published with a delay of several days).
  * NCM        – NOT CONNECTED. The National Center for Meteorology provides data to legal entities under a licence
                 ("Meteorological Data Publishing or Utilization Service", https://www.ncm.gov.sa/en/services/our-services/
                 meteorological-data-publishing-or-utilization-service); no public self-service API was found.
                 The connector below is a ready slot: implement `fetch` once a licence and API credentials exist,
                 and store credentials only in Streamlit Secrets ([ncm]).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

# Prototype thresholds used only to describe the weather context in plain words (not calibrated).
HOT_TMAX_C = 40.0
WARM_TMAX_C = 35.0
DRY_RH_PCT = 20.0
RAIN_MM = 5.0


@dataclass
class ConnectorStatus:
    id: str
    name: str
    name_ar: str
    connected: bool
    detail: str
    detail_ar: str


@dataclass
class WeatherResult:
    df: pd.DataFrame
    source_id: str
    source_name: str
    statuses: list[ConnectorStatus] = field(default_factory=list)


class NCMConnector:
    """Slot for the National Center for Meteorology (Saudi Arabia). Not connected in this version."""

    id = "ncm"
    name = "National Center for Meteorology (NCM)"
    name_ar = "المركز الوطني للأرصاد"

    def __init__(self, credentials: dict | None = None):
        self.credentials = credentials or {}

    def status(self) -> ConnectorStatus:
        return ConnectorStatus(
            self.id, self.name, self.name_ar, False,
            "Not connected: NCM data access requires a licence for a legal entity; no public API is available to RAY.",
            "غير متصل: الوصول إلى بيانات المركز يتطلب ترخيصًا لجهة اعتبارية، ولا توجد واجهة برمجية عامة متاحة لـ RAY.",
        )

    def fetch(self, lat: float, lon: float, start: str, end: str) -> pd.DataFrame | None:
        return None  # intentionally unimplemented – never fabricate data


class ERA5LandConnector:
    id = "era5_land"
    name = "ERA5-Land (ECMWF / Copernicus)"
    name_ar = "ERA5-Land (المركز الأوروبي / كوبرنيكوس)"

    def __init__(self, fetch_fn):
        self._fetch = fetch_fn  # cached gee.weather wrapper

    def status(self, ok: bool = True) -> ConnectorStatus:
        return ConnectorStatus(self.id, self.name, self.name_ar, ok,
                               "Active via Google Earth Engine (reanalysis, ~11 km, delayed by several days)." if ok
                               else "Unavailable (Earth Engine not connected).",
                               "متصل عبر Google Earth Engine (إعادة تحليل، ~١١ كم، يتأخر عدة أيام)." if ok
                               else "غير متاح (Earth Engine غير متصل).")

    def fetch(self, lat, lon, start, end) -> pd.DataFrame | None:
        df = self._fetch(lat, lon, start, end)
        return df if df is not None and not df.empty else None


def get_weather(lat: float, lon: float, start: str, end: str, era5_fetch, ncm: NCMConnector | None = None) -> WeatherResult:
    """Return weather from the highest-priority connector that has data (NCM first, then ERA5-Land)."""
    ncm = ncm or NCMConnector()
    statuses = [ncm.status()]
    df = ncm.fetch(lat, lon, start, end)
    if df is not None and not df.empty:
        statuses.append(ERA5LandConnector(era5_fetch).status(True))
        return WeatherResult(df.assign(source=ncm.name), ncm.id, ncm.name, statuses)
    era5 = ERA5LandConnector(era5_fetch)
    try:
        df = era5.fetch(lat, lon, start, end)
    except Exception:  # noqa: BLE001 -- weather is optional context
        df = None
    statuses.append(era5.status(df is not None))
    if df is None:
        return WeatherResult(pd.DataFrame(), "none", "", statuses)
    return WeatherResult(df, era5.id, era5.name, statuses)


def summarize(df: pd.DataFrame, date: str, days: int = 7) -> dict | None:
    """Mean conditions over the `days` days up to the satellite date (or the latest available before it)."""
    if df is None or df.empty:
        return None
    d = pd.Timestamp(date)
    w = df[(df.date <= d) & (df.date > d - pd.Timedelta(days=days))]
    if w.empty:  # reanalysis lags: fall back to the last `days` days available before the date
        w = df[df.date <= d].tail(days)
    if w.empty:
        return None
    s = {
        "n_days": len(w), "first_date": w.date.min().strftime("%Y-%m-%d"), "last_date": w.date.max().strftime("%Y-%m-%d"),
        "tmax_mean": float(w.air_temp_max_c.mean()), "tmean": float(w.air_temp_c.mean()),
        "precip_sum": float(w.precip_mm.sum()),
        "rh_mean": float(w.rel_humidity_pct.mean()) if "rel_humidity_pct" in w else np.nan,
        "wind_mean": float(w.wind_speed_ms.mean()) if "wind_speed_ms" in w else np.nan,
        "source": str(w["source"].iloc[-1]) if "source" in w else "",
    }
    s["hot"] = s["tmax_mean"] >= HOT_TMAX_C
    s["warm"] = WARM_TMAX_C <= s["tmax_mean"] < HOT_TMAX_C
    s["dry_air"] = bool(np.isfinite(s["rh_mean"]) and s["rh_mean"] <= DRY_RH_PCT)
    s["rain"] = s["precip_sum"] >= RAIN_MM
    return s
