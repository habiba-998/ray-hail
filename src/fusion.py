"""Evidence fusion: which causes are CONSISTENT with the available evidence for a zone?

Inputs (all optional except the zone): satellite rule points (existing RAY rules), Isolation-Forest unusual-pixel
share, recent weather (ERA5-Land / NCM), crop, the farmer's symptom answers, and the colour screening of a photo.

Output: for each cause category an evidence score, a qualitative level (strong / moderate / weak / none) and the list
of reasons that produced it. This is a transparent, rule-based prototype:
  * it is NOT a probability and NOT a diagnosis – every category always needs field confirmation;
  * weights are prototype values, not calibrated; field validations collected by RAY are stored so they can be used
    to calibrate these rules in the future (no automatic learning happens today);
  * Sentinel-1 SAR is shown as context but deliberately not scored (no local calibration).
"""
from __future__ import annotations

import numpy as np

from . import knowledge

CAUSES = {
    "water": {"icon": "💧", "en": "Possible water stress", "ar": "إجهاد مائي محتمل"},
    "heat": {"icon": "☀️", "en": "Possible heat stress", "ar": "إجهاد حراري محتمل"},
    "disease": {"icon": "🦠", "en": "Possible plant disease", "ar": "مرض نباتي محتمل"},
    "pest": {"icon": "🐛", "en": "Possible pest or insect", "ar": "آفة أو حشرة محتملة"},
    "nutrient": {"icon": "🧪", "en": "Possible nutrient deficiency", "ar": "نقص غذائي محتمل"},
    "other": {"icon": "🌱", "en": "Other possible problem (e.g. salinity, harvest, growth stage)", "ar": "مشكلة أخرى محتملة (مثل الملوحة أو الحصاد أو مرحلة النمو)"},
}
LEVELS = [(5, "strong", "مرتفعة"), (3, "moderate", "متوسطة"), (1, "weak", "منخفضة")]

# symptom tag -> {cause: points}   (farmer questionnaire, see problems.json symptom_vocabulary)
SYMPTOM_WEIGHTS = {
    "leaf_spots": {"disease": 2},
    "rust_pustules": {"disease": 3},
    "yellowing": {"nutrient": 1, "water": 1, "disease": 1},
    "streaks": {"pest": 1, "disease": 1},
    "wilting": {"water": 2, "heat": 1},
    "leaf_curl": {"pest": 1, "water": 1},
    "insects_visible": {"pest": 3},
    "honeydew": {"pest": 2},
    "webbing_dust": {"pest": 2},
    "leaf_mines": {"pest": 3},
    "chewed_leaves": {"pest": 2},
    "trunk_damage": {"pest": 3},
    "root_rot": {"disease": 2, "other": 1},
    "fruit_damage": {"pest": 1, "disease": 1},
}
PHOTO_WEIGHTS = {
    "photo_yellow": {"nutrient": 1, "water": 1},
    "photo_brown": {"water": 1, "disease": 1},
    "photo_dark_spots": {"disease": 1},
}
REASONS = {
    "sat_ndmi": ("Satellite moisture signal is low", "إشارة الرطوبة من القمر الصناعي منخفضة"),
    "sat_lst": ("Area is warmer than the farm average (satellite)", "المنطقة أدفأ من متوسط المزرعة (قمر صناعي)"),
    "sat_ndre": ("Leaf greenness is low while moisture looks normal", "خضرة الأوراق منخفضة بينما الرطوبة تبدو طبيعية"),
    "sat_decline": ("Vegetation is weaker than the farm or declined recently", "النباتات أضعف من بقية المزرعة أو تراجعت مؤخرًا"),
    "ml_unusual": ("AI found an unusual satellite pattern here", "الذكاء الاصطناعي رصد نمطًا غير معتاد هنا"),
    "wx_hot": ("Very hot recent days (≥ {t:.0f} °C average max)", "أيام حارة جدًا مؤخرًا (متوسط العظمى ≥ {t:.0f} °م)"),
    "wx_warm": ("Hot recent days ({t:.0f} °C average max)", "أيام حارة مؤخرًا (متوسط العظمى {t:.0f} °م)"),
    "wx_dry": ("Very dry air (≈{rh:.0f}% humidity)", "هواء جاف جدًا (رطوبة ≈{rh:.0f}٪)"),
    "wx_rain": ("Recent rain ({p:.0f} mm)", "أمطار حديثة ({p:.0f} مم)"),
    "soil_dry": ("You reported dry soil", "أفدت بأن التربة جافة"),
    "soil_wet": ("You reported wet / waterlogged soil", "أفدت بأن التربة رطبة جدًا أو مشبعة بالماء"),
    "spread_one": ("Problem limited to single plants", "المشكلة في نباتات قليلة متفرقة"),
    "spread_many": ("Problem widespread across the area", "المشكلة منتشرة في المنطقة"),
}


def _add(scores, reasons, cause, pts, reason_key, **fmt):
    if pts == 0:
        return
    scores[cause] = scores.get(cause, 0) + pts
    reasons.setdefault(cause, []).append((reason_key, fmt, pts))


def possible_causes(zone: dict, *, weather: dict | None = None, anomaly_share: float | None = None,
                    contamination: float = 0.05, symptoms: list[str] | None = None, soil: str | None = None,
                    spread: str | None = None, photo: dict | None = None) -> list[dict]:
    scores: dict[str, int] = {c: 0 for c in CAUSES}
    reasons: dict[str, list] = {}
    rp = {k: v[0] for k, v in zone.get("rules", {}).items()}

    # --- satellite (existing RAY rule points) ---
    ndmi, lst, ndre = rp.get("NDMI (canopy water)"), rp.get("LST vs farm mean (°C)"), rp.get("NDRE (chlorophyll)")
    rel, chg = rp.get("NDVI vs farm median"), rp.get("NDVI change (~2 weeks)")
    if ndmi:
        _add(scores, reasons, "water", ndmi, "sat_ndmi")
    if lst:
        _add(scores, reasons, "water", 1, "sat_lst")
        _add(scores, reasons, "heat", 1, "sat_lst")
    if ndre and not ndmi:
        _add(scores, reasons, "nutrient", ndre, "sat_ndre")
    if (rel or 0) + (chg or 0) > 0:
        for c in ("disease", "pest", "other"):
            _add(scores, reasons, c, 1, "sat_decline")
    if anomaly_share is not None and np.isfinite(anomaly_share) and anomaly_share >= 2 * contamination:
        _add(scores, reasons, "other", 1, "ml_unusual")

    # --- weather context ---
    if weather:
        if weather.get("hot"):
            _add(scores, reasons, "heat", 2, "wx_hot", t=weather["tmax_mean"])
        elif weather.get("warm"):
            _add(scores, reasons, "heat", 1, "wx_warm", t=weather["tmax_mean"])
        if weather.get("dry_air"):
            _add(scores, reasons, "water", 1, "wx_dry", rh=weather["rh_mean"])
        if weather.get("rain"):
            _add(scores, reasons, "disease", 1, "wx_rain", p=weather["precip_sum"])
            _add(scores, reasons, "water", -1, "wx_rain", p=weather["precip_sum"])

    # --- farmer answers ---
    for tag in symptoms or []:
        for cause, pts in SYMPTOM_WEIGHTS.get(tag, {}).items():
            _add(scores, reasons, cause, pts, f"sym:{tag}")
    if soil == "dry":
        _add(scores, reasons, "water", 2, "soil_dry")
    elif soil == "wet":
        _add(scores, reasons, "water", -2, "soil_wet")
        _add(scores, reasons, "disease", 1, "soil_wet")
    if spread == "one":
        _add(scores, reasons, "disease", 1, "spread_one")
        _add(scores, reasons, "pest", 1, "spread_one")
    elif spread == "many":
        _add(scores, reasons, "water", 1, "spread_many")
        _add(scores, reasons, "heat", 1, "spread_many")

    # --- photo colour screening ---
    if photo and photo.get("ok"):
        for sig in photo.get("signals", []):
            for cause, pts in PHOTO_WEIGHTS[sig].items():
                _add(scores, reasons, cause, pts, f"photo:{sig}")

    out = []
    for cause, meta in CAUSES.items():
        s = max(scores[cause], 0)
        level = next(((en, ar) for th, en, ar in LEVELS if s >= th), ("none", "لا توجد دلائل بعد"))
        out.append({"cause": cause, **meta, "score": s, "level": level[0], "level_ar": level[1],
                    "reasons": [r for r in reasons.get(cause, []) if r[2] > 0]})
    return sorted(out, key=lambda r: -r["score"])


def reason_text(reason: tuple, ar: bool) -> str:
    key, fmt, _ = reason
    if key.startswith("sym:"):
        v = knowledge.symptom_vocabulary()[key[4:]]
        return ("لاحظت: " + v["ar"]) if ar else ("You observed: " + v["en"].lower())
    if key.startswith("photo:"):
        t = {"photo_yellow": ("Photo: a lot of yellow tissue", "الصورة: نسبة كبيرة من الأنسجة الصفراء"),
             "photo_brown": ("Photo: a lot of brown / dry tissue", "الصورة: نسبة كبيرة من الأنسجة البنية أو الجافة"),
             "photo_dark_spots": ("Photo: dark spots", "الصورة: بقع داكنة")}[key[6:]]
        return t[1] if ar else t[0]
    en, a = REASONS[key]
    return (a if ar else en).format(**fmt)


def matching_problems(crop_id: str, symptoms: list[str] | None) -> list[dict]:
    """Crop-specific diseases/pests whose documented visual symptoms overlap with what the farmer observed."""
    sym = set(symptoms or [])
    ranked = []
    for p in knowledge.problems_for(crop_id):
        hits = sym & set(p["visual_tags"])
        if hits:
            ranked.append({"problem": p, "matches": sorted(hits), "n": len(hits)})
    return sorted(ranked, key=lambda r: -r["n"])
