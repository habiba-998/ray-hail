"""Spectral index definitions (numpy + Earth Engine) and their explanations.

Band naming follows Sentinel-2 MSI:
  B2 blue, B3 green, B4 red, B5 red-edge (705 nm), B8 NIR (842 nm), B11 SWIR-1 (1610 nm)
"""
from __future__ import annotations

import numpy as np


def normalized_difference(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a = a.astype("float32")
    b = b.astype("float32")
    with np.errstate(divide="ignore", invalid="ignore"):
        out = (a - b) / (a + b)
    out[~np.isfinite(out)] = np.nan
    return out


def compute_indices(bands: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    """Compute NDVI, NDRE and NDMI from a dict of reflectance arrays (0-1)."""
    return {
        "NDVI": normalized_difference(bands["B8"], bands["B4"]),
        "NDRE": normalized_difference(bands["B8"], bands["B5"]),
        "NDMI": normalized_difference(bands["B8"], bands["B11"]),
    }


def add_indices_ee(img):
    """Earth Engine equivalent of compute_indices (expects reflectance bands)."""
    ndvi = img.normalizedDifference(["B8", "B4"]).rename("NDVI")
    ndre = img.normalizedDifference(["B8", "B5"]).rename("NDRE")
    ndmi = img.normalizedDifference(["B8", "B11"]).rename("NDMI")
    return img.addBands([ndvi, ndre, ndmi])


# Colour palettes shared by the Earth Engine tile renderer and the numpy renderer
PALETTES = {
    "NDVI": ["#8c510a", "#d8b365", "#f6e8c3", "#c7e9c0", "#74c476", "#238b45", "#00441b"],
    "NDRE": ["#7f3b08", "#e08214", "#fee0b6", "#d9f0d3", "#7fbf7b", "#1b7837"],
    "NDMI": ["#8c510a", "#d8b365", "#f5f5f5", "#9ecae1", "#3182bd", "#08306b"],
    "LST": ["#313695", "#4575b4", "#abd9e9", "#fee090", "#f46d43", "#a50026"],
    "STRESS": ["#2E9E5B", "#F2B01E", "#D64541"],
}
VIS_RANGES = {
    "NDVI": (0.0, 0.9),
    "NDRE": (0.0, 0.6),
    "NDMI": (-0.3, 0.5),
    "LST": (25.0, 60.0),
}

INDEX_INFO = {
    "NDVI": {
        "name": "NDVI – Normalized Difference Vegetation Index",
        "ar": "مؤشر الغطاء النباتي",
        "formula": "(NIR − Red) / (NIR + Red)  →  (B8 − B4) / (B8 + B4)",
        "meaning": "Amount and greenness of vegetation. Bare desert soil is usually < 0.2; "
        "dense irrigated crops are usually > 0.6. A drop can indicate stress, harvest or thinning.",
    },
    "NDRE": {
        "name": "NDRE – Normalized Difference Red-Edge Index",
        "ar": "مؤشر الحافة الحمراء (الكلوروفيل)",
        "formula": "(NIR − RedEdge) / (NIR + RedEdge)  →  (B8 − B5) / (B8 + B5)",
        "meaning": "Sensitive to leaf chlorophyll. It saturates later than NDVI, so it can reveal "
        "vigour differences in dense canopies. Low values can reflect nutrient or water stress.",
    },
    "NDMI": {
        "name": "NDMI – Normalized Difference Moisture Index (Gao NDWI)",
        "ar": "مؤشر رطوبة النبات",
        "formula": "(NIR − SWIR1) / (NIR + SWIR1)  →  (B8 − B11) / (B8 + B11)",
        "meaning": "Related to canopy water content. Well-watered canopies are typically > 0.2; "
        "values near or below 0 over a crop suggest low canopy water (or sparse canopy).",
    },
    "LST": {
        "name": "LST – Land Surface Temperature (Landsat 8/9 thermal)",
        "ar": "درجة حرارة سطح الأرض",
        "formula": "ST_B10 × 0.00341802 + 149.0 − 273.15  (°C, Landsat Collection-2 L2)",
        "meaning": "Transpiring crops cool themselves. A canopy warmer than the rest of the farm can "
        "indicate reduced transpiration (possible water stress). Resolution is coarser (100 m native).",
    },
}


def colorize(arr: np.ndarray, palette: list[str], vmin: float, vmax: float, alpha: int = 220) -> np.ndarray:
    """Map a 2-D float array to an RGBA uint8 image using a hex palette; NaN -> transparent."""
    cols = np.array([[int(h[i : i + 2], 16) for i in (1, 3, 5)] for h in palette], dtype="float32")
    t = np.clip((arr - vmin) / (vmax - vmin), 0, 1)
    t = np.nan_to_num(t, nan=0.0)
    pos = t * (len(palette) - 1)
    lo = np.floor(pos).astype(int)
    hi = np.minimum(lo + 1, len(palette) - 1)
    frac = (pos - lo)[..., None]
    rgb = cols[lo] * (1 - frac) + cols[hi] * frac
    a = np.where(np.isnan(arr), 0, alpha).astype("uint8")[..., None]
    return np.concatenate([rgb.astype("uint8"), a], axis=-1)


def true_color(bands: dict[str, np.ndarray], gain: float = 3.2) -> np.ndarray:
    """Simple RGB stretch of reflectance bands (B4, B3, B2) to RGBA uint8."""
    rgb = np.stack([bands["B4"], bands["B3"], bands["B2"]], axis=-1) * gain
    rgb = np.clip(rgb ** (1 / 1.2), 0, 1) * 255
    a = np.full(rgb.shape[:2] + (1,), 255, dtype="uint8")
    return np.concatenate([rgb.astype("uint8"), a], axis=-1)
