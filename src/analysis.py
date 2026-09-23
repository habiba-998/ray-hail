"""Transparent rule-based stress scoring, temporal anomaly detection and recommendations.

This is a PROTOTYPE DECISION-SUPPORT MODEL. Each indicator adds 0, 1 or 2 points
when it crosses a documented threshold (see config.Thresholds). The zone class
is set by the share of the maximum possible points. The rules flag *potential*
water stress; the same spectral symptoms can be caused by heat, disease,
nutrient deficiency, salinity, pests, harvest or crop growth stage.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import MIN_CLEAR_FRACTION, MIN_VEG_FRACTION, VEG_NDVI_MIN, Thresholds


def _pts(value: float, high: float, mod: float, higher_is_worse: bool = False) -> int | None:
    if value is None or not np.isfinite(value):
        return None
    if higher_is_worse:
        return 2 if value > high else (1 if value > mod else 0)
    return 2 if value < high else (1 if value < mod else 0)


def farm_reference(zones: pd.DataFrame) -> dict:
    """Farm-level references computed from cropped, cloud-free zones."""
    ok = zones[(zones.veg_frac >= MIN_VEG_FRACTION) & (zones.clear_frac >= MIN_CLEAR_FRACTION)]
    return {
        "ndvi_median": float(ok.ndvi.median()) if len(ok) else np.nan,
        "lst_mean": float(ok.lst.mean()) if len(ok) and ok.lst.notna().any() else np.nan,
    }


def score_zones(zones: pd.DataFrame, t: Thresholds) -> tuple[pd.DataFrame, dict]:
    """Add rule points, score share, class and reasons to each zone."""
    ref = farm_reference(zones)
    out = []
    for z in zones.to_dict("records"):
        z["ndvi_rel"] = z["ndvi"] / ref["ndvi_median"] if ref["ndvi_median"] else np.nan
        z["lst_anom"] = z["lst"] - ref["lst_mean"] if np.isfinite(ref["lst_mean"]) else np.nan
        z["dndvi"] = z["ndvi"] - z["ndvi_prev"] if z.get("ndvi_prev") is not None else np.nan

        rules = {
            "NDMI (canopy water)": (_pts(z["ndmi"], t.ndmi_high, t.ndmi_mod), z["ndmi"], f"< {t.ndmi_high} → 2 · < {t.ndmi_mod} → 1"),
            "NDRE (chlorophyll)": (_pts(z["ndre"], t.ndre_high, t.ndre_mod), z["ndre"], f"< {t.ndre_high} → 2 · < {t.ndre_mod} → 1"),
            "NDVI vs farm median": (_pts(z["ndvi_rel"], t.ndvi_rel_high, t.ndvi_rel_mod), z["ndvi_rel"], f"< {t.ndvi_rel_high} → 2 · < {t.ndvi_rel_mod} → 1"),
            "LST vs farm mean (°C)": (_pts(z["lst_anom"], t.lst_high, t.lst_mod, True), z["lst_anom"], f"> +{t.lst_high} → 2 · > +{t.lst_mod} → 1"),
            "NDVI change (~2 weeks)": (_pts(z["dndvi"], t.dndvi_high, t.dndvi_mod), z["dndvi"], f"< {t.dndvi_high} → 2 · < {t.dndvi_mod} → 1"),
        }
        got = {k: v for k, v in rules.items() if v[0] is not None}
        pts = sum(v[0] for v in got.values())
        max_pts = 2 * len(got)
        z["points"] = pts
        z["max_points"] = max_pts
        z["score"] = pts / max_pts if max_pts else np.nan
        z["rules"] = rules

        if not np.isfinite(z.get("clear_frac") or np.nan) or z["clear_frac"] < MIN_CLEAR_FRACTION:
            z["cls"] = "NO_DATA"
        elif not np.isfinite(z.get("veg_frac") or np.nan) or z["veg_frac"] < MIN_VEG_FRACTION:
            z["cls"] = "NO_CROP"
        elif not max_pts:
            z["cls"] = "NO_DATA"
        elif z["score"] >= t.red_share:
            z["cls"] = "HIGH"
        elif z["score"] >= t.yellow_share:
            z["cls"] = "MODERATE"
        else:
            z["cls"] = "HEALTHY"
        z["reasons"] = [k for k, v in got.items() if v[0] > 0]
        out.append(z)
    return pd.DataFrame(out), ref


def rule_table(zone: dict) -> pd.DataFrame:
    rows = []
    for name, (p, val, rule) in zone["rules"].items():
        rows.append(
            {
                "Indicator": name,
                "Value": None if val is None or not np.isfinite(val) else round(float(val), 3),
                "Rule (points)": rule,
                "Points": "n/a" if p is None else p,
            }
        )
    return pd.DataFrame(rows)


def pixel_stress_np(ndvi: np.ndarray, ndre: np.ndarray, ndmi: np.ndarray, farm_ref_ndvi: float, t: Thresholds) -> np.ndarray:
    """Per-pixel class (0/1/2, NaN for non-crop) using the same thresholds as pixel_stress_ee."""

    def pts(x, high, mod):
        return np.where(x < high, 2, np.where(x < mod, 1, 0))

    rel = ndvi / max(farm_ref_ndvi, 1e-3)
    share = (pts(ndmi, t.ndmi_high, t.ndmi_mod) + pts(ndre, t.ndre_high, t.ndre_mod) + pts(rel, t.ndvi_rel_high, t.ndvi_rel_mod)) / 6
    cls = (share >= t.yellow_share).astype("float32") + (share >= t.red_share).astype("float32")
    cls[~(ndvi > VEG_NDVI_MIN)] = np.nan
    return cls


# ---------------------------------------------------------------------------
# Temporal analysis
# ---------------------------------------------------------------------------
def detect_anomalies(ts: pd.DataFrame, col: str, drop: float = 0.08, window: int = 3) -> pd.DataFrame:
    """Flag observations that fall more than `drop` below the median of the previous `window` observations."""
    ts = ts.sort_values("date").copy()
    base = ts[col].shift(1).rolling(window, min_periods=2).median()
    ts[f"{col}_baseline"] = base
    ts[f"{col}_delta"] = ts[col] - base
    ts[f"{col}_anomaly"] = ts[f"{col}_delta"] < -drop
    return ts


def trend_slope(ts: pd.DataFrame, col: str, last_n: int = 6) -> float:
    """Linear slope of the index per 10 days over the most recent observations."""
    d = ts.dropna(subset=[col]).sort_values("date").tail(last_n)
    if len(d) < 3:
        return np.nan
    x = (d["date"] - d["date"].iloc[0]).dt.days.to_numpy(dtype=float)
    return float(np.polyfit(x, d[col].to_numpy(dtype=float), 1)[0] * 10)


def pick_previous_date(dates: list[str], date: str, min_gap_days: int = 10) -> str | None:
    """Latest available date at least `min_gap_days` before `date` (for the ~2-week change rule)."""
    target = pd.Timestamp(date) - pd.Timedelta(days=min_gap_days)
    earlier = [d for d in dates if pd.Timestamp(d) <= target]
    return earlier[-1] if earlier else None


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------
RECOMMENDATIONS = {
    "HEALTHY": (
        "No significant vegetation stress detected. Continue monitoring.",
        "لم يُرصد إجهاد نباتي ملحوظ. استمر في المراقبة.",
    ),
    "MODERATE": (
        "Moderate stress detected. Inspect irrigation and field conditions.",
        "تم رصد إجهاد متوسط. افحص نظام الري وظروف الحقل.",
    ),
    "HIGH": (
        "High potential water stress detected. Inspect irrigation before applying water.",
        "تم رصد إجهاد مائي محتمل مرتفع. افحص نظام الري قبل إضافة المياه.",
    ),
    "NO_CROP": (
        "No active crop canopy detected. If this area is being irrigated, check whether that water is needed.",
        "لا يوجد غطاء محصولي نشط. إذا كانت هذه المنطقة تُروى، تحقق من الحاجة إلى تلك المياه.",
    ),
    "NO_DATA": (
        "Not enough cloud-free pixels on this date. Select another date.",
        "لا تتوفر بكسلات صافية كافية في هذا التاريخ. اختر تاريخًا آخر.",
    ),
}

REASON_HINTS = {
    "NDMI (canopy water)": "Low NDMI suggests reduced canopy water content (check emitters/nozzles, pressure, pivot end-gun).",
    "NDRE (chlorophyll)": "Low NDRE suggests reduced chlorophyll – can be water stress but also nitrogen deficiency or disease.",
    "NDVI vs farm median": "Canopy is weaker than the rest of the farm – compare with irrigation coverage and soil differences.",
    "LST vs farm mean (°C)": "Canopy is warmer than the farm average – may indicate reduced transpiration.",
    "NDVI change (~2 weeks)": "Vegetation declined recently – rule out harvest/cutting before assuming stress.",
}


def recommendation(zone: dict) -> dict:
    en, ar = RECOMMENDATIONS[zone["cls"]]
    hints = [REASON_HINTS[r] for r in zone.get("reasons", []) if r in REASON_HINTS]
    return {"en": en, "ar": ar, "hints": hints}
