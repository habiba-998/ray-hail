"""RAY | رَيّ – Satellite-powered irrigation intelligence for your farm.

Streamlit app (hackathon prototype). Run with:  streamlit run app.py

Structure:
  * sidebar      – data source, area, zones, analysis date, rule thresholds (settings)
  * pipeline     – unchanged scientific engine (src/): Earth Engine or DEMO data -> zone statistics ->
                   rule-based stress classes -> Isolation Forest anomaly share
  * presentation – Farmer mode (src/ui/farmer.py, default) or Technical mode (src/ui/technical.py);
                   both read the SAME results object, so switching mode never recomputes the analysis.
"""
from __future__ import annotations

import base64
import datetime as dt
import json
import os
import uuid
from pathlib import Path

import pandas as pd
import streamlit as st

from src import analysis, ml
from src import weather as wxmod
from src.storage import make_store
from src.config import AOI, AOI_PRESETS, APP_NAME_AR, DEFAULT_PRESET, Thresholds
from src.preprocessing import make_zone_grid
from src.ui import farmer, styles, technical
from src.ui.common import Ctx, ee_connect, ee_dates, ee_samples, ee_weather, ee_zone_stats, get_demo_farm, synced_control
from src.ui.i18n import is_ar, t

st.set_page_config(page_title="RAY | رَيّ – Satellite irrigation intelligence", page_icon="💧", layout="wide",
                   initial_sidebar_state="collapsed")
LOGO_B64 = base64.b64encode((Path(__file__).parent / "assets" / "logo.svg").read_bytes()).decode()
# Icon-only mark (the drop + leaf from assets/logo.svg) for the top bar, next to the text title
ICON_B64 = base64.b64encode(
    b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="24 12 72 84"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
    b'<stop offset="0" stop-color="#0F766E"/><stop offset="1" stop-color="#65A30D"/></linearGradient></defs>'
    b'<path d="M60 18 C60 18 30 55 30 75 A30 30 0 0 0 90 75 C90 55 60 18 60 18 Z" fill="url(#g)"/>'
    b'<path d="M48 86 C50 70 62 62 76 60 C72 74 62 84 48 86 Z" fill="#fff" opacity=".92"/>'
    b'<path d="M50 84 L70 64" stroke="#65A30D" stroke-width="2"/></svg>'
).decode()
DEMO_SRC, EE_SRC = "Demo mode (simulated data)", "Google Earth Engine (real satellite data)"

st.session_state.setdefault("lang", "ar")  # Arabic first
st.session_state.setdefault("mode", "farmer")
st.session_state.setdefault("crop", "unknown")  # "Not specified" until the farmer chooses
styles.inject(rtl=is_ar() and st.session_state.mode == "farmer")


def _secret(name: str) -> str | None:
    try:
        return st.secrets.get(name)  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001 -- no secrets file is fine
        return None


def _service_account_json() -> str | None:
    """Earth Engine service-account key for deployments, read ONLY from the environment or Streamlit Secrets.

    Preferred: a TOML table [ee_service_account] in Streamlit Secrets (the fields of the Google JSON key).
    Also accepted: EE_SERVICE_ACCOUNT_JSON as a JSON string (env var or secret). Nothing is ever read from the repo.
    """
    if os.environ.get("EE_SERVICE_ACCOUNT_JSON"):
        return os.environ["EE_SERVICE_ACCOUNT_JSON"]
    try:
        if "ee_service_account" in st.secrets:
            return json.dumps(dict(st.secrets["ee_service_account"]))
    except Exception:  # noqa: BLE001 -- no secrets file is fine
        pass
    return _secret("EE_SERVICE_ACCOUNT_JSON")


def use_demo() -> None:
    st.session_state.source = DEMO_SRC


# ---------------------------------------------------------------------------
# Top bar: brand · language · mode
# ---------------------------------------------------------------------------
tb1, tb2 = st.columns([1.6, 1], vertical_alignment="center")
tb1.markdown(
    f"<div class='topbar'><img src='data:image/svg+xml;base64,{ICON_B64}' alt=''>"
    f"<div><h1>RAY <span style='opacity:.4'>|</span> <span class='ar'>{APP_NAME_AR}</span></h1>"
    f"<div class='sub'>{t('subtitle')}</div></div></div>",
    unsafe_allow_html=True,
)
with tb2:
    st.segmented_control("Language", ["ar", "en"], format_func={"ar": "العربية", "en": "English"}.get, key="lang",
                         required=True, label_visibility="collapsed")
    synced_control("Mode", ["farmer", "tech"], "mode", lambda m: t("mode_farmer" if m == "farmer" else "mode_tech"))

# ---------------------------------------------------------------------------
# Sidebar – settings (collapsed by default; farmers do not need it)
# ---------------------------------------------------------------------------
sa_json = _service_account_json()
default_project = os.environ.get("EE_PROJECT") or _secret("EE_PROJECT") or ""
if sa_json and not default_project:
    try:
        default_project = json.loads(sa_json).get("project_id", "")
    except Exception:  # noqa: BLE001 -- a malformed key is reported by the connection step
        pass
st.session_state.setdefault("source", EE_SRC if default_project or sa_json else DEMO_SRC)
with st.sidebar:
    st.markdown(f"<img src='data:image/svg+xml;base64,{LOGO_B64}' width='170'>", unsafe_allow_html=True)
    st.caption("Hackathon prototype · University of Hail Space Innovation Hackathon 2026 · AI & Space Data Science")

    st.subheader("1 · Data source")
    source = st.radio("Data source", [DEMO_SRC, EE_SRC], key="source", label_visibility="collapsed")
    use_ee = source == EE_SRC
    ee_ok, ee_msg = False, ""
    if use_ee:
        # On a deployment (service account configured) the project is fixed: the Earth Engine client is shared by
        # every visitor of the server process, so one visitor must not be able to re-point it for everyone.
        project = st.text_input("Earth Engine Cloud project ID", value=default_project, disabled=bool(sa_json),
                                help="Fixed by the deployment's service account." if sa_json else
                                "The Google Cloud project registered for Earth Engine (e.g. my-ee-project).")
        ee_ok, ee_msg = ee_connect(default_project if sa_json else project, sa_json)
        if ee_ok:
            st.success(ee_msg)
        else:
            st.error("Earth Engine is not connected – no real data loaded.")
            if st.button("Retry connection"):
                ee_connect.clear()
                st.rerun()

    st.subheader("2 · Area of interest")
    preset = st.selectbox("Agricultural area in Hail", list(AOI_PRESETS), index=list(AOI_PRESETS).index(DEFAULT_PRESET))
    p = AOI_PRESETS[preset]
    c1, c2 = st.columns(2)
    lat = c1.number_input("Latitude", value=p["lat"], format="%.4f", step=0.005, key=f"lat_{preset}")
    lon = c2.number_input("Longitude", value=p["lon"], format="%.4f", step=0.005, key=f"lon_{preset}")
    half_km = st.slider("Half-width of area (km)", 0.5, 5.0, p["half_km"], 0.25, key=f"hk_{preset}")
    st.caption("Preset centres were located from Sentinel-2 NDVI (Sep 2026) – check the satellite photo and adjust if needed.")
    g1, g2 = st.columns(2)
    n_rows = g1.slider("Zone rows", 2, 6, 4)
    n_cols = g2.slider("Zone cols", 2, 6, 4)

    start = end = max_cloud = None
    if use_ee:
        st.subheader("3 · Dates")
        today = dt.date.today()
        d1, d2 = st.columns(2)
        start = d1.date_input("From", today - dt.timedelta(days=150))
        end = d2.date_input("To", today)
        max_cloud = st.slider("Max scene cloud %", 5, 80, 30, 5)

    with st.expander("⚙️ Advanced – rule thresholds"):
        st.caption("Prototype values, not field-calibrated. Changing them updates the classification live.")
        d = Thresholds()
        thr = Thresholds(
            ndmi_high=st.slider("NDMI high-stress below", -0.2, 0.3, d.ndmi_high, 0.01),
            ndmi_mod=st.slider("NDMI moderate below", -0.1, 0.4, d.ndmi_mod, 0.01),
            ndre_high=st.slider("NDRE high-stress below", 0.0, 0.4, d.ndre_high, 0.01),
            ndre_mod=st.slider("NDRE moderate below", 0.0, 0.5, d.ndre_mod, 0.01),
            ndvi_rel_high=st.slider("NDVI / farm median – high below", 0.4, 1.0, d.ndvi_rel_high, 0.01),
            ndvi_rel_mod=st.slider("NDVI / farm median – moderate below", 0.5, 1.0, d.ndvi_rel_mod, 0.01),
            lst_high=st.slider("LST above farm mean – high (°C)", 0.5, 8.0, d.lst_high, 0.5),
            lst_mod=st.slider("LST above farm mean – moderate (°C)", 0.5, 6.0, d.lst_mod, 0.5),
            red_share=st.slider("RED if score ≥", 0.2, 1.0, d.red_share, 0.05),
            yellow_share=st.slider("YELLOW if score ≥", 0.05, 0.8, d.yellow_share, 0.05),
        )

# ---------------------------------------------------------------------------
# Earth Engine selected but unavailable: say so clearly – never show demo results silently
# ---------------------------------------------------------------------------
if use_ee and not ee_ok:
    st.error(f"🛰️ {t('ee_fail_title')}")
    st.markdown(t("ee_fail_text"))
    with st.expander("Technical details / how to connect"):
        st.code(ee_msg or "Earth Engine initialisation failed.")
        st.markdown(
            "1. `pip install earthengine-api`\n"
            "2. `earthengine authenticate` (opens a browser once)\n"
            "3. Enter your Earth Engine-enabled Cloud project ID in the sidebar (or set `EE_PROJECT` in `.streamlit/secrets.toml`)\n"
            "4. Click **Retry connection** in the sidebar\n\n"
            "**Hosted deployment (Streamlit Community Cloud):** add `EE_PROJECT` and the `[ee_service_account]` table "
            "in *App settings → Secrets* – see DEPLOYMENT.md.\n\nSee README → *Earth Engine authentication*."
        )
    st.button(t("use_demo"), on_click=use_demo, key="b_use_demo")
    st.stop()

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
    st.error(f"Could not list satellite acquisitions: {exc}")
    st.stop()

if not dates:
    st.warning("No Sentinel-2 acquisitions found for this area / date range / cloud limit. Widen the dates or raise the cloud limit.")
    st.stop()

with st.sidebar:
    st.subheader("4 · Analysis date")
    date = st.select_slider("📅 Sentinel-2 acquisition", options=dates, value=dates[-1])
    prev_date = analysis.pick_previous_date(dates, date)
    st.caption(f"Compared with: **{prev_date or '—'}** (previous clear date ≥10 days earlier)")

try:
    if use_ee:
        zs, meta = ee_zone_stats(bounds, zones.to_dict("records"), date, prev_date)
    else:
        zs = farm.zone_stats(zones, date, prev_date)
except Exception as exc:  # noqa: BLE001
    st.error(f"Zone analysis failed: {exc}")
    st.stop()

scored, ref = analysis.score_zones(zs, thr)

# Unsupervised ML: Isolation Forest on cropped pixels
samples = pd.DataFrame()
try:
    samples = ee_samples(bounds, date) if use_ee else farm.pixel_samples(date)
    pix, if_feats = ml.isolation_forest(samples)
except Exception as exc:  # noqa: BLE001
    pix, if_feats = pd.DataFrame(), []
    st.toast(f"Anomaly model skipped: {exc}")
share = ml.anomaly_share_by_zone(pix, zones) if not pix.empty else pd.Series(dtype=float)
scored["anomaly_share"] = scored.zone_id.map(share)

zone_ids = list(scored.zone_id)
if st.session_state.get("zone_sel") not in zone_ids:
    worst = scored.sort_values("score", ascending=False, na_position="last")
    st.session_state.zone_sel = str(worst.iloc[0].zone_id)

# Farm identity (no personal data) and per-browser-session id used to keep each visitor's observations private
farm_names = {k: (f"مزرعة حائل {i + 1}" if not k.startswith("Custom") else "موقع مخصص") for i, k in enumerate(AOI_PRESETS)}
st.session_state.setdefault("session_id", uuid.uuid4().hex)


@st.cache_resource(show_spinner=False)
def _store(cfg_key: str):
    try:
        cfg = {"supabase": dict(st.secrets["supabase"])} if "supabase" in st.secrets else {}
    except Exception:  # noqa: BLE001 -- no secrets file
        cfg = {}
    return make_store(cfg)


# Weather context (ERA5-Land now; NCM connector slot not connected) – real mode only
wx = wx_summary = None
if use_ee:
    d0 = (pd.Timestamp(date) - pd.Timedelta(days=30)).strftime("%Y-%m-%d")
    d1 = (pd.Timestamp(date) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    wx = wxmod.get_weather(lat, lon, d0, d1, ee_weather)
    wx_summary = wxmod.summarize(wx.df, date)

ctx = Ctx(
    crop=st.session_state.get("crop", "unknown"), store=_store("v1"), session_id=st.session_state.session_id,
    farm_id=f"hail-{lat:.3f}-{lon:.3f}", farm_name=farm_names.get(preset, preset), wx=wx, wx_summary=wx_summary,
    use_ee=use_ee, farm=farm, bounds=bounds, zones=zones, scored=scored, ref=ref, pix=pix, samples=samples,
    if_feats=if_feats, meta=meta, dates=dates, date=date, prev_date=prev_date, thr=thr, lat=lat, lon=lon,
    half_km=half_km, n_rows=n_rows, n_cols=n_cols, start=start, end=end, max_cloud=max_cloud,
)

# ---------------------------------------------------------------------------
# Data badge + presentation
# ---------------------------------------------------------------------------
if use_ee:
    st.markdown(f"<div class='databadge real'>{t('badge_real', date=date)}</div>", unsafe_allow_html=True)
else:
    st.markdown(f"<div class='databadge demo'>{t('badge_demo')}</div>", unsafe_allow_html=True)

if st.session_state.mode == "tech":
    if is_ar():
        st.caption(t("tech_lang_note"))
    technical.render(ctx)
else:
    farmer.render(ctx)

st.markdown(
    "<div class='footer'>RAY | رَيّ · Hackathon prototype · University of Hail Space Innovation Hackathon 2026 · "
    "Decision support only – not an agronomic diagnosis. "
    + ("Contains modified Copernicus Sentinel data processed in Google Earth Engine." if use_ee else "Currently showing DEMO DATA.")
    + "</div>",
    unsafe_allow_html=True,
)
