"""SATRA | ساترا – agricultural earth-observation decision support (Streamlit). Run with:  streamlit run app.py

Farmer-only interface. Structure:
  * settings     – fixed defaults in the background (no technical controls are shown to the farmer)
  * pipeline     – unchanged scientific engine (src/): Earth Engine (or local demo data when no Earth Engine
                   project is configured) -> zone statistics -> rule-based classes -> Isolation Forest share
  * presentation – src/ui/farmer.py (Arabic, plain language)

Technical details for advanced users live on the "Technical details" page (src/ui/details.py) and in README.md.

Data status is always explicit (src/status.py): REAL (Earth Engine), DEMO (simulated; only when no Earth Engine
credentials are configured) or UNAVAILABLE (retrieval failed / insufficient data -> nothing is shown, never demo data).
"""
from __future__ import annotations

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
    if getattr(sys, "_satra_source_digest", None) != digest:
        for name in [m for m in sys.modules if m == "src" or m.startswith("src.")]:
            del sys.modules[name]
        sys._satra_source_digest = digest


_refresh_stale_project_modules()

from src import analysis, brand, ml, status  # noqa: E402  (imported after the stale-module refresh above)
from src import weather as wxmod
from src.config import AOI, AOI_PRESETS, DEFAULT_PRESET, Thresholds
from src.preprocessing import make_zone_grid
from src.storage import make_store
from src.ui import farmer, styles
from src.ui.common import Ctx, ee_connect, ee_dates, ee_samples, ee_weather, ee_zone_stats, get_demo_farm, synced_control
from src.ui.i18n import days_ago, is_ar, ltr, t

log = logging.getLogger("satra")
st.set_page_config(page_title=f"{brand.NAME_AR} | {brand.NAME_EN}", page_icon=brand.page_icon(), layout="wide", initial_sidebar_state="collapsed")
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
    """UNAVAILABLE state: log the technical cause for developers; show the user a plain, category-specific message.

    The app never substitutes demo data here.
    """
    log.warning("SATRA data loading failed: %s", detail)
    msg = status.FAILURE_MESSAGES_AR[status.classify_failure(detail)]
    status_slot.markdown(status_row("unavailable", f"⛔ {t('st_unavailable')}", []), unsafe_allow_html=True)
    st.markdown(f"<div class='databadge unavailable'>⚠️ {msg}</div>", unsafe_allow_html=True)
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
st.session_state.setdefault("source", EE_SRC if status.choose_source(project, sa_json) == "earth_engine" else DEMO_SRC)
use_ee = st.session_state.source == EE_SRC

preset = st.session_state.farm if st.session_state.farm in FARMS else DEFAULT_PRESET
p = AOI_PRESETS[preset]
lat, lon, half_km = p["lat"], p["lon"], p["half_km"]
n_rows = n_cols = 4
thr = Thresholds()
today = dt.date.today()
start, end, max_cloud = (today - dt.timedelta(days=150), today, 30) if use_ee else (None, None, None)

# ---------------------------------------------------------------------------
# Header: brand + farm picker; the data-status line is filled once the data are known
# ---------------------------------------------------------------------------
def status_row(chip_cls: str, chip_text: str, items: list[tuple[str, str]]) -> str:
    """Second header row: data-status chip + labelled facts (label above value), so each fact reads on its own."""
    facts = "".join(f"<div class='fact'><span class='lbl'>{lbl}</span><span class='val'>{val}</span></div>" for lbl, val in items)
    return f"<div class='statusbar'><span class='chip {chip_cls}'>{chip_text}</span>{facts}</div>"


with st.container(key="header"):
    # Row 1: brand identity (first in the DOM so it stacks on top on phones) + the farm picker as its own labelled group.
    # In Arabic the row flows right-to-left (CSS), so the brand sits on the right and the picker on the left.
    brand_col, farm_col = st.columns([5, 3], vertical_alignment="center", gap="medium")
    secondary = f"<span class='brand-latin'>{brand.NAME_EN}</span>" if is_ar() else ""
    brand_col.markdown(
        f"<div class='brand'><img src='{brand.data_uri(brand.SYMBOL_SVG)}' alt='' width='84' height='84'>"
        f"<div class='brand-text'><div class='brand-name' role='heading' aria-level='1'>{t('app_name')}{secondary}</div>"
        f"<div class='brand-sub'>{t('subtitle')}</div></div></div>",
        unsafe_allow_html=True,
    )
    with farm_col:
        st.session_state.farm = preset
        st.selectbox(t("farm"), list(FARMS), format_func=FARMS.get, key="farm")
    # Row 2: data status (filled once the data are known)
    status_slot = st.empty()

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
    fr = status.freshness(date)
    status_slot.markdown(status_row("real", f"🛰️ {t('st_real')}", [
        (t("hdr_latest"), ltr(date)),
        (t("hdr_age"), days_ago(fr.age_days)),
        (t("hdr_period"), t("hdr_period_val", a=ltr(start), b=ltr(end))),
    ]), unsafe_allow_html=True)
    if fr.stale:
        st.markdown(f"<div class='databadge demo'>⚠️ {t('stale_note')}</div>", unsafe_allow_html=True)
else:
    status_slot.markdown(status_row("demo", f"⚠️ {t('st_demo')}", [(t("hdr_sim_date"), ltr(date))]), unsafe_allow_html=True)
    st.markdown(f"<div class='databadge demo'>{t('demo_banner')}</div>", unsafe_allow_html=True)
with st.container(key="topnav"):
    synced_control("nav", farmer.PAGES, "fpage", farmer.nav_labels().get)
farmer.render(ctx)

st.markdown(
    f"<div class='footer'><b>{brand.NAME_AR} · {brand.NAME_EN}</b> — {brand.TAGLINE_AR}<br>"
    "منصة لدعم القرار، ونتائجها مؤشرات أولية للفحص وليست تشخيصًا نهائيًا."
    + ("<br>الصور الفضائية: © برنامج كوبرنيكوس الأوروبي" if use_ee else "") + "</div>",
    unsafe_allow_html=True,
)
