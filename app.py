"""RAY | رَيّ – decision support for farmers (Streamlit). Run with:  streamlit run app.py

Farmer-only interface. Structure:
  * settings     – fixed defaults in the background (no technical controls are shown to the farmer)
  * pipeline     – unchanged scientific engine (src/): Earth Engine (or local demo data when no Earth Engine
                   project is configured) -> zone statistics -> rule-based classes -> Isolation Forest share
  * presentation – src/ui/farmer.py (Arabic, plain language)

The former technical dashboard (src/ui/technical.py) is kept in the code base for developers but is not reachable
from the interface. Technical details are documented in README.md.
"""
from __future__ import annotations

import base64
import datetime as dt
import json
import logging
import os
import uuid
from pathlib import Path

import pandas as pd
import streamlit as st


def _refresh_stale_project_modules() -> None:
    """Re-import src.* when the project files changed since they were loaded.

    After a git update, Streamlit Community Cloud can run the new app.py while still holding the previously imported
    src.* modules in memory (e.g. a new app.py calling a translation key that the old, cached i18n module lacks →
    KeyError). Hashing the source files and dropping src.* from sys.modules when they change guarantees that app.py
    and its modules always come from the same version. Cheap: only file hashing on each run.
    """
    import hashlib
    import sys

    root = Path(__file__).parent
    h = hashlib.sha1()
    for f in sorted([root / "app.py", *(root / "src").rglob("*.py")]):
        h.update(f.read_bytes())
    digest = h.hexdigest()
    if getattr(sys, "_ray_source_digest", None) != digest:
        for name in [m for m in sys.modules if m == "src" or m.startswith("src.")]:
            del sys.modules[name]
        sys._ray_source_digest = digest


_refresh_stale_project_modules()

from src import analysis, ml  # noqa: E402  (imported after the stale-module refresh above)
from src import weather as wxmod
from src.config import AOI, AOI_PRESETS, DEFAULT_PRESET, Thresholds
from src.preprocessing import make_zone_grid
from src.storage import make_store
from src.ui import farmer, styles
from src.ui.common import Ctx, ee_connect, ee_dates, ee_samples, ee_weather, ee_zone_stats, get_demo_farm, synced_control
from src.ui.i18n import is_ar, t

log = logging.getLogger("ray")
st.set_page_config(page_title="رَيّ | RAY", page_icon="💧", layout="wide", initial_sidebar_state="auto")
ICON_B64 = base64.b64encode(
    b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="24 12 72 84"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
    b'<stop offset="0" stop-color="#1E5B38"/><stop offset="1" stop-color="#65A30D"/></linearGradient></defs>'
    b'<path d="M60 18 C60 18 30 55 30 75 A30 30 0 0 0 90 75 C90 55 60 18 60 18 Z" fill="url(#g)"/>'
    b'<path d="M48 86 C50 70 62 62 76 60 C72 74 62 84 48 86 Z" fill="#fff" opacity=".92"/>'
    b'<path d="M50 84 L70 64" stroke="#65A30D" stroke-width="2"/></svg>'
).decode()
DEMO_SRC, EE_SRC = "demo", "earth_engine"
# Farmer-facing farm names (coordinates are never shown)
FARMS = {k: f"مزرعة حائل {i + 1}" for i, k in enumerate(k for k in AOI_PRESETS if not k.startswith("Custom"))}

st.session_state.setdefault("lang", "ar")
st.session_state.setdefault("crop", "unknown")
st.session_state.setdefault("farm", DEFAULT_PRESET)
st.session_state.setdefault("fpage", "home")
styles.inject(rtl=is_ar())


def _secret(name: str) -> str | None:
    try:
        return st.secrets.get(name)  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001 -- no secrets file is fine
        return None


def _service_account_json() -> str | None:
    """Earth Engine service-account key, read ONLY from the environment or Streamlit Secrets (never from the repo)."""
    if os.environ.get("EE_SERVICE_ACCOUNT_JSON"):
        return os.environ["EE_SERVICE_ACCOUNT_JSON"]
    try:
        if "ee_service_account" in st.secrets:
            return json.dumps(dict(st.secrets["ee_service_account"]))
    except Exception:  # noqa: BLE001
        pass
    return _secret("EE_SERVICE_ACCOUNT_JSON")


def friendly_stop(detail: object) -> None:
    """Log the technical cause for developers; show the farmer a plain message only."""
    log.warning("RAY data loading failed: %s", detail)
    st.markdown(f"<div class='card soft'>⚠️ {t('load_failed')}</div>", unsafe_allow_html=True)
    if st.button(t("btn_retry"), key="b_retry"):
        ee_connect.clear()
        st.cache_data.clear()
        st.rerun()
    st.stop()


# ---------------------------------------------------------------------------
# Background settings (defaults; not shown to the farmer)
# ---------------------------------------------------------------------------
sa_json = _service_account_json()
project = os.environ.get("EE_PROJECT") or _secret("EE_PROJECT") or ""
if sa_json and not project:
    try:
        project = json.loads(sa_json).get("project_id", "")
    except Exception:  # noqa: BLE001
        pass
project = st.session_state.get("_ee_project_override", project)  # test hook only
st.session_state.setdefault("source", EE_SRC if project or sa_json else DEMO_SRC)
use_ee = st.session_state.source == EE_SRC

preset = st.session_state.farm if st.session_state.farm in FARMS else DEFAULT_PRESET
p = AOI_PRESETS[preset]
lat, lon, half_km = p["lat"], p["lon"], p["half_km"]
n_rows = n_cols = 4
thr = Thresholds()
today = dt.date.today()
start, end, max_cloud = (today - dt.timedelta(days=150), today, 30) if use_ee else (None, None, None)

# ---------------------------------------------------------------------------
# Header + farmer menu (sidebar)
# ---------------------------------------------------------------------------
st.markdown(
    f"<div class='topbar'><img src='data:image/svg+xml;base64,{ICON_B64}' alt=''>"
    f"<div><h1>{t('app_name')}</h1><div class='sub'>{t('subtitle')}</div></div></div>",
    unsafe_allow_html=True,
)
with st.sidebar:
    st.markdown(f"<div class='side-brand'><img src='data:image/svg+xml;base64,{ICON_B64}' alt=''> {t('app_name')}</div>",
                unsafe_allow_html=True)
    farm_keys = list(FARMS)
    st.session_state.farm = preset
    st.selectbox(t("farm"), farm_keys, format_func=FARMS.get, key="farm")
    labels = farmer.nav_labels()
    wkey = f"_r_fpage_{'ar' if is_ar() else 'en'}"
    st.session_state[wkey] = st.session_state.fpage

    def _nav():
        st.session_state.fpage = st.session_state[wkey]

    st.radio(t("menu"), farmer.PAGES, format_func=labels.get, key=wkey, on_change=_nav)

# ---------------------------------------------------------------------------
# Data connection
# ---------------------------------------------------------------------------
if use_ee:
    ee_ok, ee_msg = ee_connect(project, sa_json)
    if not ee_ok:
        friendly_stop(ee_msg)

aoi = AOI(lat, lon, half_km)
bounds = tuple(round(b, 6) for b in aoi.bounds)
zones = make_zone_grid(aoi, n_rows, n_cols)

# ---------------------------------------------------------------------------
# Scientific pipeline (unchanged)
# ---------------------------------------------------------------------------
meta: dict = {}
farm = None
try:
    if use_ee:
        dates = ee_dates(bounds, str(start), str(end + dt.timedelta(days=1)), max_cloud)
    else:
        farm = get_demo_farm(bounds)
        dates = farm.dates
except Exception as exc:  # noqa: BLE001
    friendly_stop(exc)
if not dates:
    friendly_stop("no clear Sentinel-2 acquisition in the period")
date = dates[-1]  # latest clear image
prev_date = analysis.pick_previous_date(dates, date)

try:
    if use_ee:
        zs, meta = ee_zone_stats(bounds, zones.to_dict("records"), date, prev_date)
    else:
        zs = farm.zone_stats(zones, date, prev_date)
except Exception as exc:  # noqa: BLE001
    friendly_stop(exc)

scored, ref = analysis.score_zones(zs, thr)

samples = pd.DataFrame()
try:
    samples = ee_samples(bounds, date) if use_ee else farm.pixel_samples(date)
    pix, if_feats = ml.isolation_forest(samples)
except Exception as exc:  # noqa: BLE001
    log.warning("anomaly model skipped: %s", exc)
    pix, if_feats = pd.DataFrame(), []
share = ml.anomaly_share_by_zone(pix, zones) if not pix.empty else pd.Series(dtype=float)
scored["anomaly_share"] = scored.zone_id.map(share)

zone_ids = list(scored.zone_id)
if st.session_state.get("zone_sel") not in zone_ids:
    worst = scored.sort_values("score", ascending=False, na_position="last")
    st.session_state.zone_sel = str(worst.iloc[0].zone_id)

st.session_state.setdefault("session_id", uuid.uuid4().hex)


@st.cache_resource(show_spinner=False)
def _store(cfg_key: str):
    try:
        cfg = {"supabase": dict(st.secrets["supabase"])} if "supabase" in st.secrets else {}
    except Exception:  # noqa: BLE001
        cfg = {}
    return make_store(cfg)


wx = wx_summary = None
if use_ee:
    d0 = (pd.Timestamp(date) - pd.Timedelta(days=30)).strftime("%Y-%m-%d")
    d1 = (pd.Timestamp(date) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    wx = wxmod.get_weather(lat, lon, d0, d1, ee_weather)
    wx_summary = wxmod.summarize(wx.df, date)

ctx = Ctx(
    crop=st.session_state.get("crop", "unknown"), store=_store("v1"), session_id=st.session_state.session_id,
    farm_id=f"hail-{lat:.3f}-{lon:.3f}", farm_name=FARMS[preset], wx=wx, wx_summary=wx_summary,
    use_ee=use_ee, farm=farm, bounds=bounds, zones=zones, scored=scored, ref=ref, pix=pix, samples=samples,
    if_feats=if_feats, meta=meta, dates=dates, date=date, prev_date=prev_date, thr=thr, lat=lat, lon=lon,
    half_km=half_km, n_rows=n_rows, n_cols=n_cols, start=start, end=end, max_cloud=max_cloud,
)

# ---------------------------------------------------------------------------
# Farmer interface
# ---------------------------------------------------------------------------
if use_ee:
    st.markdown(f"<div class='databadge real'>📅 {t('image_date', date=date)}</div>", unsafe_allow_html=True)
else:
    st.markdown(f"<div class='databadge demo'>⚠️ {t('demo_note')}</div>", unsafe_allow_html=True)
synced_control("nav", farmer.PAGES, "fpage", farmer.nav_labels().get)
farmer.render(ctx)

st.markdown(
    "<div class='footer'>رَيّ — نظام لدعم القرار، ونتائجه مؤشرات أولية وليست تشخيصًا نهائيًا."
    + ("<br>الصور الفضائية: © برنامج كوبرنيكوس الأوروبي" if use_ee else "") + "</div>",
    unsafe_allow_html=True,
)
