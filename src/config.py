"""Central configuration: areas of interest, thresholds, colours and dataset IDs.

Every threshold used by the stress rules lives here so that it is visible,
documented and easy to change. None of these thresholds has been calibrated
against field measurements in Hail -- they are literature-informed starting
points for a prototype.
"""
from __future__ import annotations

from dataclasses import dataclass

APP_NAME = "RAY"
APP_NAME_AR = "رَيّ"
TAGLINE = "Smarter Irrigation from Space"
TAGLINE_AR = "ري أذكى من الفضاء"

# ---------------------------------------------------------------------------
# Areas of interest (Hail region, Saudi Arabia)
# Preset centres were located from REAL data: 4 km grid cells over 26.6–28.2°N,
# 41.2–42.8°E ranked by the share of pixels with NDVI > 0.4 in a cloud-masked
# Sentinel-2 median composite (1–22 Sep 2026). Share shown in brackets. Fields
# change between seasons – re-check with the True Color / NDVI layers.
# ---------------------------------------------------------------------------
AOI_PRESETS: dict[str, dict] = {
    "Hail region – east farmland 27.40°N 42.53°E (52% veg, Sep 2026)": {"lat": 27.3986, "lon": 42.5262, "half_km": 2.0},
    "Hail region – north-east farmland 27.94°N 42.10°E (32% veg)": {"lat": 27.9376, "lon": 42.0951, "half_km": 2.0},
    "Hail region – north farmland 28.01°N 41.77°E (30% veg)": {"lat": 28.0095, "lon": 41.7717, "half_km": 2.0},
    "Custom location": {"lat": 27.520, "lon": 41.700, "half_km": 2.0},
}
DEFAULT_PRESET = "Hail region – east farmland 27.40°N 42.53°E (52% veg, Sep 2026)"


@dataclass(frozen=True)
class AOI:
    """Rectangular area of interest defined by a centre point and half-width."""

    lat: float
    lon: float
    half_km: float

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        """(min_lon, min_lat, max_lon, max_lat) in degrees."""
        import math

        dlat = self.half_km / 110.574
        dlon = self.half_km / (111.320 * math.cos(math.radians(self.lat)))
        return (self.lon - dlon, self.lat - dlat, self.lon + dlon, self.lat + dlat)


# ---------------------------------------------------------------------------
# Earth Engine datasets
# ---------------------------------------------------------------------------
S2_COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"          # Sentinel-2 L2A surface reflectance
L8_COLLECTION = "LANDSAT/LC08/C02/T1_L2"               # Landsat 8 Collection 2 Level 2
L9_COLLECTION = "LANDSAT/LC09/C02/T1_L2"               # Landsat 9 Collection 2 Level 2
ERA5_COLLECTION = "ECMWF/ERA5_LAND/DAILY_AGGR"         # ERA5-Land daily aggregates
S2_BANDS = ["B2", "B3", "B4", "B5", "B8", "B11"]
# Scene Classification Layer classes treated as invalid (no data, saturated,
# cloud shadow, cloud medium/high probability, thin cirrus, snow)
S2_SCL_INVALID = [0, 1, 3, 8, 9, 10, 11]
LANDSAT_WINDOW_DAYS = 12  # search Landsat thermal +/- N days around the Sentinel-2 date

# ---------------------------------------------------------------------------
# Analysis thresholds (prototype values -- NOT field calibrated)
# ---------------------------------------------------------------------------
VEG_NDVI_MIN = 0.25          # pixels above this NDVI are treated as crop canopy
MIN_VEG_FRACTION = 0.10      # zones with less canopy than this are "No active crop"
MIN_CLEAR_FRACTION = 0.50    # zones with fewer cloud-free pixels are "Insufficient data"
TS_MIN_CLEAR_FRACTION = 0.60 # time-series observations below this are dropped


@dataclass
class Thresholds:
    # NDMI (canopy water content). Irrigated canopies are typically > 0.2.
    ndmi_high: float = 0.05      # below -> 2 points
    ndmi_mod: float = 0.18       # below -> 1 point
    # NDRE (chlorophyll / canopy vigour)
    ndre_high: float = 0.20
    ndre_mod: float = 0.30
    # NDVI of the zone relative to the farm's median cropped-zone NDVI
    ndvi_rel_high: float = 0.75
    ndvi_rel_mod: float = 0.90
    # Land surface temperature minus farm cropped-zone mean (deg C)
    lst_high: float = 3.0
    lst_mod: float = 1.5
    # NDVI change since previous clear observation
    dndvi_high: float = -0.10
    dndvi_mod: float = -0.05
    # Share of maximum possible points
    red_share: float = 0.50
    yellow_share: float = 0.25


# ---------------------------------------------------------------------------
# Visual identity
# ---------------------------------------------------------------------------
CLASS_COLORS = {
    "HEALTHY": "#2E9E5B",
    "MODERATE": "#F2B01E",
    "HIGH": "#D64541",
    "NO_CROP": "#9AA3A8",
    "NO_DATA": "#5B6770",
}
CLASS_LABELS = {
    "HEALTHY": "Healthy / Low stress",
    "MODERATE": "Moderate stress",
    "HIGH": "High potential water stress",
    "NO_CROP": "No active crop",
    "NO_DATA": "Insufficient clear data",
}
CLASS_LABELS_AR = {
    "HEALTHY": "سليم / إجهاد منخفض",
    "MODERATE": "إجهاد متوسط",
    "HIGH": "إجهاد مائي محتمل مرتفع",
    "NO_CROP": "لا يوجد محصول نشط",
    "NO_DATA": "بيانات غير كافية",
}
CLASS_EMOJI = {"HEALTHY": "🟢", "MODERATE": "🟡", "HIGH": "🔴", "NO_CROP": "⚪", "NO_DATA": "⚫"}

BRAND = {
    "primary": "#0F766E",
    "accent": "#65A30D",
    "sand": "#F5EFE0",
    "ink": "#0B2530",
}
