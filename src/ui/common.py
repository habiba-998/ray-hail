"""Helpers shared by Farmer and Technical modes: cached data access, formatting, zone picker, map, limitations.

The cached wrappers call the unchanged functions in src.data_acquisition; they were moved here from app.py so
both modes reuse the same cache (switching mode never recomputes the analysis).
"""
from __future__ import annotations

from dataclasses import asdict
from types import SimpleNamespace

import numpy as np
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from .. import analysis
from .. import data_acquisition as gee
from ..config import LANDSAT_WINDOW_DAYS
from ..demo_data import DemoFarm
from ..indices import PALETTES, VIS_RANGES, colorize, true_color
from ..preprocessing import zone_at
from ..visualization import build_map

Ctx = SimpleNamespace  # holds every result of the pipeline for the current run (built in app.py)

# Show the "unusual pattern" note for a zone the rules did NOT flag when its share of Isolation-Forest-unusual
# pixels is at least this multiple of the farm-wide share fixed by the model (contamination). Presentation only.
ANOMALY_NOTE_FACTOR = 2.0


# ---------------------------------------------------------------------------
# Cached data access (unchanged calls)
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner="Generating DEMO scene (simulated data)…")
def get_demo_farm(bounds: tuple) -> DemoFarm:
    return DemoFarm(bounds)


_EE_STATE: dict = {}  # Earth Engine is a process-wide singleton: remember which credentials it was last initialised with


def ee_connect(project: str, sa_json: str | None) -> tuple[bool, str]:
    """Initialise Earth Engine once per (project, credentials); re-initialise whenever they change.

    A plain cache would keep returning an old success after a different (e.g. mistyped) project had
    re-initialised the global Earth Engine client, sending later queries to the wrong project.
    """
    key = (project or None, sa_json)
    if _EE_STATE.get("key") == key and _EE_STATE.get("ok"):
        return True, _EE_STATE["msg"]
    with st.spinner("Connecting to Google Earth Engine…"):
        ok, msg = gee.init_earth_engine(project or None, sa_json)
    _EE_STATE.update(key=key, ok=ok, msg=msg)
    return ok, msg


ee_connect.clear = _EE_STATE.clear  # used by the "Retry connection" button


def synced_control(label: str, options: list, state_key: str, format_func) -> str:
    """Segmented control whose value lives in st.session_state[state_key] (not in the widget).

    The option labels change with the language, which gives Streamlit a new widget identity and would reset a
    keyed widget. Keeping the canonical value in a plain session key (and a per-language widget key) keeps the
    selection when the language changes and lets buttons set it from callbacks.
    """
    from .i18n import lang

    wkey = f"_w_{state_key}_{lang()}"
    st.session_state[wkey] = st.session_state[state_key]

    def _sync():
        st.session_state[state_key] = st.session_state[wkey]

    labels = {o: format_func(o) for o in options}  # resolved now, in the user's language (not lazily later)
    st.segmented_control(label, options, format_func=labels.get, key=wkey, on_change=_sync, required=True,
                         label_visibility="collapsed")
    return st.session_state[state_key]


@st.cache_data(ttl=3600, show_spinner="Searching Sentinel-2 acquisitions…")
def ee_dates(bounds, start, end, max_cloud):
    return gee.list_s2_dates(bounds, start, end, max_cloud)


@st.cache_data(ttl=3600, show_spinner="Computing zone statistics from Sentinel-2 & Landsat…")
def ee_zone_stats(bounds, zones_records, date, prev_date):
    return gee.zone_stats(bounds, zones_records, date, prev_date)


@st.cache_data(ttl=3600, show_spinner="Rendering satellite layer…")
def ee_layer(bounds, date, layer, farm_ref, thr):
    url = gee.layer_tile_url(bounds, date, layer, farm_ref, thr)
    if url:
        _warm_tiles(url, bounds)
    return url


def _warm_tiles(url: str, bounds: tuple) -> None:
    """Request the central tiles once in the background.

    Earth Engine computes a new map layer on the first tile request; that first request can take ~20 s and be closed
    by the server, and the browser map does not retry failed tiles. Warming the tiles server-side means they are
    usually ready by the time the user's browser asks for them. Failures here are harmless.
    """
    import math
    import threading
    import urllib.request

    lat, lon = (bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2

    def xy(z):
        n = 2 ** z
        return int((lon + 180) / 360 * n), int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)

    def run():
        for z in (13, 14, 15):
            x, y = xy(z)
            for dx, dy in ((0, 0), (1, 0), (0, 1), (-1, 0), (0, -1)):
                try:
                    urllib.request.urlopen(url.format(z=z, x=x + dx, y=y + dy), timeout=60).read()
                except Exception:  # noqa: BLE001
                    pass

    threading.Thread(target=run, daemon=True).start()


@st.cache_data(ttl=3600, show_spinner="Sampling cropped pixels…")
def ee_samples(bounds, date):
    return gee.pixel_samples(bounds, date)


@st.cache_data(ttl=3600, show_spinner="Building Sentinel-2 time series…")
def ee_ts(bounds, start, end, max_cloud):
    return gee.timeseries(bounds, start, end, max_cloud)


@st.cache_data(ttl=3600, show_spinner="Building Landsat thermal time series…")
def ee_lst_ts(bounds, start, end):
    return gee.lst_timeseries(bounds, start, end)


@st.cache_data(ttl=3600, show_spinner="Loading ERA5-Land weather…")
def ee_weather(lat, lon, start, end):
    return gee.weather(lat, lon, start, end)


@st.cache_data(ttl=3600, show_spinner="Loading Sentinel-1 radar…")
def ee_s1(bounds, zones_records, date):
    return gee.s1_zone_stats(bounds, zones_records, date)


def synced_select(label: str, options: list, state_key: str, format_func, **kw):
    """Selectbox whose value lives in st.session_state[state_key] (survives language changes / page switches)."""
    from .i18n import lang

    wkey = f"_s_{state_key}_{lang()}"
    if st.session_state.get(state_key) not in options:
        st.session_state[state_key] = options[0]
    st.session_state[wkey] = st.session_state[state_key]

    def _sync():
        st.session_state[state_key] = st.session_state[wkey]

    labels = {o: format_func(o) for o in options}  # resolved now, in the user's language (not lazily later)
    st.selectbox(label, options, format_func=labels.get, key=wkey, on_change=_sync, **kw)
    return st.session_state[state_key]


# ---------------------------------------------------------------------------
# Formatting / zone helpers
# ---------------------------------------------------------------------------
def fmt(v, nd=2, suffix="", signed=False):
    if v is None or (isinstance(v, float) and not np.isfinite(v)):
        return "—"
    v = round(float(v), nd) + 0.0  # + 0.0 turns -0.0 into 0.0 so we never print "-0.00"
    return f"{v:+.{nd}f}{suffix}" if signed else f"{v:.{nd}f}{suffix}"


def finite(v) -> bool:
    return v is not None and isinstance(v, (int, float, np.floating)) and bool(np.isfinite(v))


def zone_row(c: Ctx, zid: str) -> dict:
    return c.scored[c.scored.zone_id == zid].iloc[0].to_dict()


def zone_picker(c: Ctx, where: str, fmt_label, label: str = "Zone") -> str:
    """Selectbox bound to st.session_state.zone_sel (shared by every page)."""
    ids = list(c.scored.zone_id)
    cur = st.session_state.zone_sel
    labels = {z: fmt_label(z, cl) for z, cl in zip(c.scored.zone_id, c.scored.cls)}
    choice = st.selectbox(label, ids, index=ids.index(cur), format_func=labels.get, key=f"zp_{where}_{cur}")
    if choice != cur:
        st.session_state.zone_sel = choice
        st.rerun()
    return cur


def priority_zones(c: Ctx) -> pd.DataFrame:
    """Zones the existing rules classed HIGH or MODERATE, most concerning first."""
    order = {"HIGH": 0, "MODERATE": 1}
    p = c.scored[c.scored.cls.isin(order)]
    return p.assign(_o=p.cls.map(order)).sort_values(["_o", "score"], ascending=[True, False])


def anomaly_watch(c: Ctx, contamination: float) -> pd.DataFrame:
    """Zones NOT flagged by the rules whose unusual-pixel share is well above the farm-wide share."""
    s = c.scored
    return s[s.cls.isin(["HEALTHY"]) & (s.anomaly_share >= ANOMALY_NOTE_FACTOR * contamination)].sort_values(
        "anomaly_share", ascending=False)


# ---------------------------------------------------------------------------
# Map (same rendering path as the original Satellite Map tab)
# ---------------------------------------------------------------------------
def render_farm_map(c: Ctx, layer: str, key_prefix: str, zone_fill: float, height: int = 580,
                    short_attribution: bool = False, **map_kw) -> None:
    tile_url, img = None, None
    attribution = ("Copernicus Sentinel-2 · Google Earth Engine" if short_attribution
                   else "Contains modified Copernicus Sentinel data, processed in Google Earth Engine")
    try:
        if c.use_ee:
            ee_name = "Stress (pixel)" if layer == "Water Stress" else layer
            tile_url = ee_layer(c.bounds, c.date, ee_name,
                                c.ref["ndvi_median"] if np.isfinite(c.ref["ndvi_median"]) else 0.6, asdict(c.thr))
            if layer == "LST":
                attribution = "Landsat 8/9 Collection-2 surface temperature (USGS), via Google Earth Engine"
            if tile_url is None:
                st.info(f"No cloud-free Landsat thermal scene within ±{LANDSAT_WINDOW_DAYS} days of {c.date}.")
        else:
            farm = c.farm
            i = farm.date_index(c.date)
            if layer == "True Color":
                img = true_color(farm.bands(i))
            elif layer == "Water Stress":
                cls = analysis.pixel_stress_np(
                    farm.index_grid(c.date, "NDVI"), farm.index_grid(c.date, "NDRE"), farm.index_grid(c.date, "NDMI"),
                    c.ref["ndvi_median"] if np.isfinite(c.ref["ndvi_median"]) else 0.6, c.thr,
                )
                img = colorize(cls, PALETTES["STRESS"], 0, 2)
            else:
                lo, hi = VIS_RANGES[layer]
                img = colorize(farm.index_grid(c.date, layer), PALETTES[layer], lo, hi, alpha=235)
            attribution = "DEMO DATA – simulated"
    except Exception as exc:  # noqa: BLE001
        st.error(f"Layer rendering failed: {exc}")

    fmap = build_map(c.bounds, c.scored, st.session_state.zone_sel, tile_url, img, layer,
                     zone_fill=zone_fill, attribution=attribution, **map_kw)
    # Explicit center/zoom: fit_bounds alone fails when the map is built inside a hidden tab (zero-size container)
    zoom = int(np.clip(np.floor(np.log2(156543 * np.cos(np.radians(c.lat)) * 700 / (2 * c.half_km * 1000))), 10, 17))
    # streamlit-folium only evaluates the map script on first mount, so a key that changes with the
    # content forces a re-render when the source / date / layer / selection changes.
    lbl_sig = hash(tuple(sorted((map_kw.get("labels") or {}).items())))
    map_key = (f"{key_prefix}_{c.use_ee}_{c.date}_{layer}_{st.session_state.zone_sel}_"
               f"{hash((c.bounds, c.n_rows, c.n_cols, tile_url, lbl_sig))}")
    out = st_folium(fmap, height=height, use_container_width=True, center=[c.lat, c.lon], zoom=zoom,
                    returned_objects=["last_clicked"], key=map_key)
    click = (out or {}).get("last_clicked")
    if click:
        ck = (round(click["lat"], 6), round(click["lng"], 6))
        if ck != st.session_state.get("last_click"):
            st.session_state.last_click = ck
            zc = zone_at(c.zones, click["lat"], click["lng"])
            if zc and zc != st.session_state.zone_sel:
                st.session_state.zone_sel = zc
                st.rerun()


# ---------------------------------------------------------------------------
# Limitations (shown in Farmer "About" and Technical "Limitations")
# ---------------------------------------------------------------------------
LIMITATIONS: list[tuple[str, str]] = [
    ("Stress thresholds are prototype starting points. They are not field-calibrated for every crop, growth stage or "
     "soil condition, including Hail soils.",
     "حدود الإجهاد قيم أولية للنموذج التجريبي، وغير معايَرة ميدانيًا لكل محصول أو مرحلة نمو أو نوع تربة، بما في ذلك ترب حائل."),
    ("Satellite indicators are screening signals. They cannot separate water stress from heat, disease, nutrient "
     "shortage, salinity or pests.",
     "مؤشرات الأقمار الصناعية إشارات فحص أولي، ولا يمكنها التمييز بين الإجهاد المائي والحرارة أو الأمراض أو نقص العناصر أو الملوحة أو الآفات."),
    ("Anomalies found by the Isolation Forest are statistical outliers, not proof of water stress. The farm-wide share "
     "of unusual pixels is set by the model's contamination parameter.",
     "الأنماط غير المعتادة التي يرصدها نموذج Isolation Forest قيم شاذة إحصائيًا وليست دليلًا على الإجهاد المائي، ونسبتها في المزرعة يحددها إعداد النموذج."),
    ("Zones are a regular grid, not real field or pivot boundaries.",
     "المناطق شبكة مربعات منتظمة، وليست حدود الحقول أو المحاور الفعلية."),
    ("No evapotranspiration or soil-water balance is computed, so RAY gives no irrigation volumes.",
     "لا يُحسب التبخر-النتح ولا الميزان المائي للتربة، لذلك لا يقدّم RAY كميات للري."),
    ("Clouds and dust can remove satellite observations.", "قد تحجب الغيوم والغبار صور الأقمار الصناعية."),
    ("Sentinel-2 revisits about every 5 days. Landsat thermal data is coarser (100 m) and less frequent.",
     "يعود القمر Sentinel-2 كل 5 أيام تقريبًا، وبيانات Landsat الحرارية أقل دقة مكانية (100 م) وأقل تكرارًا."),
    ("The rules can raise false alarms during early crop growth, when young canopies are sparse and uneven.",
     "قد تعطي القواعد إنذارات خاطئة في بداية نمو المحصول عندما يكون الغطاء النباتي قليلًا وغير منتظم."),
    ("No water-saving, early-detection or accuracy figures have been measured.",
     "لم تُقَس أي أرقام لتوفير المياه أو الكشف المبكر أو الدقة."),
    ("Potential water stress is not proof: the same satellite signals can come from heat, diseases, pests, nutrient "
     "deficiency, salinity, harvest/cutting or the crop's growth stage.",
     "الإجهاد المائي المحتمل ليس دليلًا: نفس إشارات الأقمار الصناعية قد تنتج عن الحرارة أو الأمراض أو الآفات أو نقص "
     "العناصر أو الملوحة أو الحصاد/الحش أو مرحلة نمو المحصول."),
    ("The 'possible causes' ranking is a transparent rule-based fit with the available evidence, not a probability and "
     "not a diagnosis.", "ترتيب «الأسباب المحتملة» توافق مبني على قواعد واضحة مع الدلائل المتوفرة، وليس احتمالًا ولا تشخيصًا."),
    ("The photo check measures colours only (green / yellow / brown). It is not a trained disease classifier and has "
     "no measured accuracy.", "فحص الصورة يقيس الألوان فقط (أخضر/أصفر/بني)، وليس نموذجًا مدرّبًا لتشخيص الأمراض وليس له دقة مقاسة."),
    ("Crop-specific calibration is still required; thresholds are the same for all crops in this version.",
     "ما زالت المعايرة حسب المحصول مطلوبة؛ العتبات نفسها لكل المحاصيل في هذه النسخة."),
    ("No supervised model is trained yet because there are not enough labelled field observations. Field results "
     "recorded in RAY are stored for future calibration; RAY does not learn automatically.",
     "لا يوجد نموذج إشرافي مدرّب حاليًا بسبب عدم توفر بيانات ميدانية مصنفة كافية. نتائج الفحص الميداني المسجلة تُحفظ "
     "للمعايرة مستقبلًا، ورَيّ لا يتعلم تلقائيًا."),
    ("Weather comes from ERA5-Land reanalysis (~11 km grid, published several days late). The National Center for "
     "Meteorology is not connected: its data require a licence.",
     "بيانات الطقس من ERA5-Land (شبكة ~١١ كم وتُنشر متأخرة عدة أيام). المركز الوطني للأرصاد غير متصل لأن بياناته تتطلب ترخيصًا."),
    ("Sentinel-1 radar is shown as context only and is not used in the scores (no local calibration).",
     "رادار Sentinel-1 يُعرض كسياق فقط ولا يدخل في التقييم (لا توجد معايرة محلية)."),
    ("No IoT sensors are connected in this version.", "لا توجد حساسات (IoT) متصلة في هذه النسخة."),
    ("Field validation is required before relying on the results.", "يلزم التحقق الميداني قبل الاعتماد على النتائج."),
]
