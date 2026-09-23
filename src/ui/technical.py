"""Technical / AI mode: the original expert dashboard (moved here unchanged) plus a Limitations tab.

All values come from the pipeline results in the context object built by app.py.
"""
from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd
import streamlit as st

from .. import analysis, ml
from ..config import CLASS_COLORS, CLASS_EMOJI, CLASS_LABELS, CLASS_LABELS_AR, LANDSAT_WINDOW_DAYS
from ..indices import INDEX_INFO
from ..raster_io import array_to_geotiff_bytes, rasterio_available
from ..visualization import (
    anomaly_scatter,
    anomaly_score_hist,
    class_donut,
    legend_html,
    lst_weather_chart,
    timeseries_chart,
    zone_anomaly_bars,
    zone_comparison_chart,
    zone_grid_heatmap,
    zone_indicator_bars,
)
from .common import LIMITATIONS, Ctx, anomaly_watch, ee_lst_ts, ee_ts, ee_weather, fmt, render_farm_map, zone_picker, zone_row


def _tech_label(z, cl):
    return f"{CLASS_EMOJI[cl]} Zone {z} – {CLASS_LABELS[cl]}"


def render(c: Ctx) -> None:
    scored, ref, zones, pix, samples, if_feats, meta = c.scored, c.ref, c.zones, c.pix, c.samples, c.if_feats, c.meta
    date, prev_date, use_ee, thr, bounds = c.date, c.prev_date, c.use_ee, c.thr, c.bounds
    lat, lon, half_km = c.lat, c.lon, c.half_km

    counts = scored.cls.value_counts()
    n_h, n_m, n_r = counts.get("HEALTHY", 0), counts.get("MODERATE", 0), counts.get("HIGH", 0)
    n_nc = counts.get("NO_CROP", 0) + counts.get("NO_DATA", 0)

    st.markdown("## 🔬 AI & Technical Analysis")
    st.caption("Full expert view for judges, engineers and agronomists: satellite indices, thermal data, anomaly detection, "
               "transparent rules, analytics and limitations. Same data and results as Farmer mode.")

    tab_ov, tab_map, tab_an, tab_wi, tab_me, tab_lim = st.tabs(
        ["📊 Overview", "🛰️ Satellite Map", "📈 Analytics", "💧 Water Intelligence", "🧠 AI & Method", "⚠️ Limitations"]
    )

    # -----------------------------------------------------------------------
    # A. Overview
    # -----------------------------------------------------------------------
    with tab_ov:
        if n_r:
            status, color = f"{n_r} zone(s) need inspection", CLASS_COLORS["HIGH"]
        elif n_m:
            status, color = f"{n_m} zone(s) to watch", CLASS_COLORS["MODERATE"]
        elif not n_h:
            status, color = "No cropped zones to assess", CLASS_COLORS["NO_DATA"]
        else:
            status, color = "No significant stress", CLASS_COLORS["HEALTHY"]
        cards = [
            ("Farm location", f"{lat:.3f}°N, {lon:.3f}°E", f"Hail region · {2 * half_km:.1f} × {2 * half_km:.1f} km"),
            ("Current status", f"<span style='color:{color}'>{status}</span>", f"Analysis date {date}"),
            ("🟢 Healthy zones", n_h, "Low stress"),
            ("🟡 Moderate stress", n_m, "Inspect field"),
            ("🔴 High potential stress", n_r, "Inspect irrigation"),
            ("⚪ No crop / no data", n_nc, "Excluded from scoring"),
        ]
        cols = st.columns(3)
        for i, (lbl, val, sub) in enumerate(cards):
            size = "1.05rem" if lbl in ("Farm location", "Current status") else "1.6rem"
            cols[i % 3].markdown(
                f"<div class='card' style='margin-bottom:10px'><div class='lbl'>{lbl}</div>"
                f"<div class='val' style='font-size:{size}'>{val}</div><div class='sub'>{sub}</div></div>",
                unsafe_allow_html=True,
            )
        o1, o2, o3 = st.columns([1, 1, 1.3])
        with o1:
            st.markdown("**Zone status distribution**")
            st.plotly_chart(class_donut(scored), key="donut", config={"displayModeBar": False})
        with o2:
            st.markdown("**Zone map (grid view)**")
            st.plotly_chart(zone_grid_heatmap(scored), key="gridmap", config={"displayModeBar": False})
        with o3:
            st.markdown("**What RAY sees on this date**")
            red = ", ".join(scored[scored.cls == "HIGH"].zone_id) or "none"
            yel = ", ".join(scored[scored.cls == "MODERATE"].zone_id) or "none"
            nc = ", ".join(scored[scored.cls == "NO_CROP"].zone_id) or "none"
            st.markdown(
                f"- 🔴 **High potential water stress:** {red}\n"
                f"- 🟡 **Moderate stress:** {yel}\n"
                f"- ⚪ **No active crop canopy:** {nc}\n"
                f"- Farm median NDVI of cropped zones: **{fmt(ref['ndvi_median'])}**\n"
                f"- Farm mean canopy LST: **{fmt(ref['lst_mean'], 1, ' °C')}**"
            )
            st.markdown(
                "<div class='caveat'>RAY highlights <b>where to look first</b>. A red zone is a prompt to "
                "<b>inspect the irrigation system and the field</b> – not an instruction to add water. Vegetation stress can "
                "also come from heat, disease, nutrient deficiency, salinity or pests.</div>",
                unsafe_allow_html=True,
            )
        src_txt = (
            f"Sentinel-2 L2A acquisition **{date}** (cloud-masked with SCL); comparison **{prev_date or '—'}**; "
            f"Landsat thermal dates used: **{', '.join(meta.get('lst_dates', [])) or 'none within ±%d days' % LANDSAT_WINDOW_DAYS}**."
            if use_ee
            else "**DEMO DATA** – synthetic scene generated by `src/demo_data.py`. No real measurements are shown."
        )
        st.caption("Data provenance: " + src_txt)

    # -----------------------------------------------------------------------
    # B. Satellite map
    # -----------------------------------------------------------------------
    with tab_map:
        layer = st.radio("Layer", ["True Color", "NDVI", "NDRE", "NDMI", "LST", "Water Stress"], horizontal=True,
                         label_visibility="collapsed", key="tech_layer")
        mcol, scol = st.columns([2.6, 1.2])
        with mcol:
            render_farm_map(c, layer, "tech_map", zone_fill=0.28 if layer == "Water Stress" else 0.04)
            st.caption("Click any zone on the map to select it. " + ("⚠️ DEMO DATA overlay on a real Esri basemap." if not use_ee else ""))
        with scol:
            st.markdown(legend_html(layer), unsafe_allow_html=True)
            if layer in INDEX_INFO:
                info = INDEX_INFO[layer]
                st.markdown(f"**{info['name']}** · <span class='rtl'>{info['ar']}</span>", unsafe_allow_html=True)
                st.caption(f"`{info['formula']}`")
                st.caption(info["meaning"])
            elif layer == "Water Stress":
                st.caption("Pixel colours use NDMI, NDRE and NDVI-vs-farm rules. Zone colours use all rules including "
                           "LST and the ~2-week NDVI change. Grey = no crop canopy (NDVI < 0.25).")
            zone_picker(c, "map", _tech_label)
            z = zone_row(c, st.session_state.zone_sel)
            rec = analysis.recommendation(z)
            st.markdown(
                f"<div class='zonecard' style='background:{CLASS_COLORS[z['cls']]}'><h3>Zone {z['zone_id']}</h3>"
                f"<b>{CLASS_LABELS[z['cls']]}</b> · <span style='font-family:Tajawal'>{CLASS_LABELS_AR[z['cls']]}</span><br>"
                f"Stress score: {fmt(z['score'] * 100 if np.isfinite(z['score']) else np.nan, 0, '%')} "
                f"({z['points']}/{z['max_points']} pts)</div>",
                unsafe_allow_html=True,
            )
            m1, m2, m3 = st.columns(3)
            m1.metric("NDVI", fmt(z["ndvi"]), None if not np.isfinite(z["dndvi"]) else fmt(z["dndvi"], 2, signed=True))
            m2.metric("NDRE", fmt(z["ndre"]))
            m3.metric("NDMI", fmt(z["ndmi"]))
            st.markdown(f"**➜ {rec['en']}**")
            st.markdown(f"<div class='rtl'>{rec['ar']}</div>", unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # C. Analytics
    # -----------------------------------------------------------------------
    with tab_an:
        a1, a2 = st.columns([1, 2])
        with a1:
            zone_picker(c, "analytics", _tech_label)
        zsel = zone_row(c, st.session_state.zone_sel)

        st.markdown("#### 📊 Zone comparison")
        metrics = {
            "Stress score (%)": scored.score * 100, "NDVI": scored.ndvi, "NDRE": scored.ndre, "NDMI": scored.ndmi,
            "LST (°C)": scored.lst, "Unusual pixels (%)": scored.anomaly_share * 100,
        }
        with a2:
            metric = st.segmented_control("Compare zones by", list(metrics), default="Stress score (%)", key="cmp_metric") \
                or "Stress score (%)"
        st.plotly_chart(zone_comparison_chart(scored.assign(_v=metrics[metric]), "_v", metric, zsel["zone_id"]),
                        key="cmp_chart", config={"displayModeBar": False})
        st.caption(f"Bar colour = rule-based class; the selected zone ({zsel['zone_id']}) is outlined. Values come from the "
                   "current analysis; zones without crop canopy have no index values.")

        zb = (zsel["min_lon"], zsel["min_lat"], zsel["max_lon"], zsel["max_lat"])
        wx = None
        try:
            if use_ee:
                s, e = str(c.start), str(c.end + dt.timedelta(days=1))
                zone_ts = ee_ts(zb, s, e, c.max_cloud)
                farm_ts = ee_ts(bounds, s, e, c.max_cloud)
                lst_ts = ee_lst_ts(zb, s, e)
                try:
                    wx = ee_weather(lat, lon, s, e)
                except Exception:  # noqa: BLE001 -- weather is optional
                    wx = None
            else:
                zone_ts = c.farm.timeseries(zb)
                farm_ts = c.farm.timeseries(bounds)
                lst_ts = zone_ts[["date", "LST"]]
        except Exception as exc:  # noqa: BLE001
            st.error(f"Time-series extraction failed: {exc}")
            zone_ts, farm_ts, lst_ts = pd.DataFrame(columns=["date", "NDVI", "NDRE", "NDMI"]), None, None

        st.markdown(f"#### 📈 Satellite observations over time · zone {zsel['zone_id']}")
        if len(zone_ts) >= 2:
            an = analysis.detect_anomalies(zone_ts, "NDVI")
            an = analysis.detect_anomalies(an, "NDMI")
            slope_v = analysis.trend_slope(zone_ts, "NDVI")
            slope_m = analysis.trend_slope(zone_ts, "NDMI")
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Observations", len(zone_ts))
            k2.metric("NDVI trend (recent)", fmt(slope_v, 3, " /10 d"))
            k3.metric("NDMI trend (recent)", fmt(slope_m, 3, " /10 d"))
            k4.metric("Observations with a sudden drop", int((an.NDVI_anomaly | an.NDMI_anomaly).sum()))
            st.plotly_chart(timeseries_chart(zone_ts, farm_ts, date, zsel["zone_id"], an), key="ts_chart")
            st.caption("Zone values are means over all cloud-free pixels in the zone (crop + soil), so harvest and planting "
                       "appear as large changes. ✕ = NDVI or NDMI observation more than 0.08 below the median of the previous 3 observations.")
            flagged = an[an.NDVI_anomaly | an.NDMI_anomaly][["date", "NDVI", "NDVI_delta", "NDMI", "NDMI_delta"]]
            if len(flagged):
                with st.expander(f"Anomalous observations ({len(flagged)})"):
                    st.dataframe(flagged, hide_index=True, column_config={
                        k: st.column_config.NumberColumn(format="%.3f") for k in ("NDVI", "NDVI_delta", "NDMI", "NDMI_delta")})
        else:
            st.info("Not enough clear observations for a time series in this zone / period.")

        st.markdown("#### 🌡️ Temperature" + (" · DEMO DATA" if not use_ee else ""))
        if (lst_ts is not None and not lst_ts.empty) or (wx is not None and not wx.empty):
            st.plotly_chart(lst_weather_chart(lst_ts, wx, date), key="lst_chart")
            st.caption("LST from Landsat 8/9 (100 m thermal, ~8-day combined revisit, clear scenes only). "
                       "Air temperature / precipitation from ERA5-Land reanalysis (~11 km grid) – regional context only."
                       if use_ee else "Simulated surface temperature (DEMO DATA). No weather data in demo mode.")
        else:
            st.info("No temperature data available for this period.")

        st.markdown("#### 📋 Index values by zone")
        show = scored[["zone_id", "cls", "veg_frac", "ndvi", "ndre", "ndmi", "lst", "lst_anom", "dndvi", "score", "anomaly_share"]].copy()
        show["cls"] = show.cls.map(lambda cl: f"{CLASS_EMOJI[cl]} {CLASS_LABELS[cl]}")
        show["score"] = show.score * 100
        show["veg_frac"] = show.veg_frac * 100
        show["anomaly_share"] = show.anomaly_share * 100
        st.dataframe(
            show,
            hide_index=True,
            column_config={
                "zone_id": "Zone",
                "cls": "Status",
                "veg_frac": st.column_config.NumberColumn("Crop cover %", format="%.0f"),
                "ndvi": st.column_config.NumberColumn("NDVI", format="%.3f"),
                "ndre": st.column_config.NumberColumn("NDRE", format="%.3f"),
                "ndmi": st.column_config.NumberColumn("NDMI", format="%.3f"),
                "lst": st.column_config.NumberColumn("LST °C", format="%.1f"),
                "lst_anom": st.column_config.NumberColumn("LST vs farm", format="%+.1f"),
                "dndvi": st.column_config.NumberColumn("ΔNDVI ~2 wk", format="%+.3f"),
                "score": st.column_config.ProgressColumn("Stress score", min_value=0, max_value=100, format="%.0f%%"),
                "anomaly_share": st.column_config.NumberColumn("Unusual pixels %", format="%.0f"),
            },
        )
        e1, e2 = st.columns(2)
        e1.download_button("⬇️ Download zone table (CSV)", show.to_csv(index=False).encode("utf-8"),
                           file_name=f"ray_zones_{date}{'_DEMO' if not use_ee else ''}.csv", mime="text/csv")
        if not use_ee and rasterio_available():
            e2.download_button("⬇️ NDVI GeoTIFF (DEMO DATA)",
                               array_to_geotiff_bytes(c.farm.index_grid(date, "NDVI"), bounds, "NDVI - DEMO DATA (simulated)"),
                               file_name=f"ray_ndvi_{date}_DEMO.tif", mime="image/tiff")

        st.markdown("#### 🧠 AI anomaly detection (unsupervised)")
        if not pix.empty:
            c_a, c_b = st.columns([2, 1])
            c_a.plotly_chart(anomaly_scatter(pix), key="if_scatter")
            c_b.markdown(
                f"An **Isolation Forest** was fitted to **{len(pix):,} cropped pixels** on {date} using "
                f"**{', '.join(if_feats)}**. It marks the ~5% of pixels whose combination of values is most unusual "
                "for this farm on this date.\n\n"
                "This needs **no labels** and makes **no claim** about the cause. It is used as an extra "
                "“look here” signal (column *Unusual pixels %*), **not** in the stress score."
            )
        else:
            st.info("Not enough cropped pixels to fit the anomaly model on this date.")

    # -----------------------------------------------------------------------
    # D. Water intelligence
    # -----------------------------------------------------------------------
    with tab_wi:
        w1, w2 = st.columns([1, 2])
        with w1:
            zone_picker(c, "water", _tech_label)
        z = zone_row(c, st.session_state.zone_sel)
        rec = analysis.recommendation(z)
        left, right = st.columns([1.2, 1])
        with left:
            st.markdown(
                f"<div class='zonecard' style='background:{CLASS_COLORS[z['cls']]}'>"
                f"<h3>{CLASS_EMOJI[z['cls']]} Zone {z['zone_id']} · {CLASS_LABELS[z['cls']]}</h3>"
                f"<div style='font-size:1.1rem;font-weight:600'>{rec['en']}</div>"
                f"<div class='rtl' style='margin-top:6px'>{CLASS_LABELS_AR[z['cls']]} — {rec['ar']}</div></div>",
                unsafe_allow_html=True,
            )
            if rec["hints"]:
                st.markdown("**Why this zone was flagged – what to check:**")
                for h in rec["hints"]:
                    st.markdown(f"- {h}")
            st.markdown("**Rule breakdown (fully transparent)**")
            st.dataframe(analysis.rule_table(z), hide_index=True)
            st.caption(f"Score = {z['points']} / {z['max_points']} points"
                       f" → {fmt(z['score'] * 100 if np.isfinite(z['score']) else np.nan, 0, '%')}. "
                       f"RED ≥ {thr.red_share:.0%}, YELLOW ≥ {thr.yellow_share:.0%}. Rules with missing data are skipped (n/a).")
        with right:
            st.markdown("**Zone vs farm**")
            st.plotly_chart(zone_indicator_bars(z, scored), key="zone_bars", config={"displayModeBar": False})
            k1, k2, k3 = st.columns(3)
            k1.metric("Crop cover", fmt(z["veg_frac"] * 100 if np.isfinite(z["veg_frac"]) else np.nan, 0, "%"))
            k2.metric("LST vs farm", fmt(z["lst_anom"], 1, " °C"))
            k3.metric("Unusual pixels", fmt(z["anomaly_share"] * 100 if np.isfinite(z["anomaly_share"]) else np.nan, 0, "%"))
            st.markdown(
                "<div class='caveat'><b>Important:</b> RAY indicates <i>potential</i> water stress from satellite "
                "indicators. It cannot confirm the cause. Similar signals can come from heat stress, disease, nutrient "
                "deficiency, soil salinity, pests, recent harvest/cutting or crop growth stage. Always verify in the field "
                "before changing irrigation. RAY does <b>not</b> calculate irrigation volumes.</div>",
                unsafe_allow_html=True,
            )

        st.markdown("#### All zones – inspection list")
        order = {"HIGH": 0, "MODERATE": 1, "HEALTHY": 2, "NO_CROP": 3, "NO_DATA": 4}
        lst_df = scored.assign(_o=scored.cls.map(order)).sort_values(["_o", "score"], ascending=[True, False])
        st.dataframe(
            pd.DataFrame(
                {
                    "Zone": lst_df.zone_id,
                    "Status": lst_df.cls.map(lambda cl: f"{CLASS_EMOJI[cl]} {CLASS_LABELS[cl]}"),
                    "Score %": (lst_df.score * 100).round(0),
                    "Triggered indicators": lst_df.reasons.map(lambda r: ", ".join(r) or "—"),
                    "Recommendation": lst_df.apply(lambda r: analysis.recommendation(r.to_dict())["en"], axis=1),
                }
            ),
            hide_index=True,
        )

        st.markdown("#### 💧 How RAY supports more efficient irrigation")
        h1, h2, h3 = st.columns(3)
        h1.markdown("**1 · Target inspections**  \nInstead of walking every field, the farm team checks red and yellow zones "
                    "first – where the satellite indicators diverge from the rest of the farm.")
        h2.markdown("**2 · Fix before adding water**  \nUneven stress inside a pivot often points to a blocked nozzle, "
                    "pressure loss or a stuck span. Repairing it can address stress without raising irrigation for the whole field.")
        h3.markdown("**3 · Avoid irrigating what doesn't need it**  \nZones with no active crop canopy are shown in grey – if they "
                    "are still being irrigated, that water may be unnecessary.")
        st.caption("RAY is designed to support more efficient irrigation decisions. Water-saving effects have not been measured in this prototype.")

    # -----------------------------------------------------------------------
    # E. AI & method
    # -----------------------------------------------------------------------
    with tab_me:
        _render_ai_method(c)

    # -----------------------------------------------------------------------
    # F. Limitations
    # -----------------------------------------------------------------------
    with tab_lim:
        render_limitations(ar=False)


def render_limitations(ar: bool) -> None:
    st.markdown("\n".join(f"- {a if ar else e}" for e, a in LIMITATIONS))


def _render_ai_method(c: Ctx) -> None:
    scored, zones, pix, samples, if_feats, meta = c.scored, c.zones, c.pix, c.samples, c.if_feats, c.meta
    date, use_ee, thr = c.date, c.use_ee, c.thr

    # Everything below is computed from the current analysis (samples / pix / scored) – nothing is hard-coded.
    lst_used = meta.get("lst_dates", []) if use_ee else []
    if use_ee:
        src_lbl = f"REAL Sentinel-2 L2A acquisition {date}" + (f" + Landsat 8/9 thermal {', '.join(lst_used)}" if lst_used else "")
        img_lbl = f"Sentinel-2 L2A · {date}"
        thermal_lbl = f"Landsat 8/9 · {', '.join(lst_used)}" if lst_used else f"No Landsat scene within ±{LANDSAT_WINDOW_DAYS} days"
    else:
        src_lbl = "DEMO DATA (simulated scene) – not satellite observations"
        img_lbl = f"DEMO DATA · simulated scene {date}"
        thermal_lbl = "DEMO DATA · simulated temperature"
    has_if = not pix.empty
    n_raw, n_used = len(samples), len(pix)
    n_anom = int(pix.anomaly.sum()) if has_if else 0
    pct_anom = n_anom / n_used if n_used else float("nan")
    scored_mask = scored.cls.isin(["HEALTHY", "MODERATE", "HIGH"])
    red_z = list(scored.loc[scored.cls == "HIGH", "zone_id"])
    yel_z = list(scored.loc[scored.cls == "MODERATE", "zone_id"])
    clear_mean = scored.clear_frac.mean()

    st.markdown("### 🧠 How RAY's AI works")
    st.caption(f"Every number on this page is computed live from the current analysis · {src_lbl}.")
    steps = [
        ("🛰️ 1 · Satellite imagery", img_lbl, ""),
        ("🧹 2 · Preprocessing", f"SCL cloud mask · {fmt(clear_mean * 100, 0, '%')} of the area cloud-free · reflectance scaling", ""),
        ("🌿 3 · Spectral features", "NDVI · NDRE · NDMI (Sentinel-2 bands B4, B5, B8, B11)", ""),
        ("🌡️ 4 · Thermal information", thermal_lbl, ""),
        ("🧠 5 · Anomaly detection", f"Isolation Forest: {n_used:,} pixels × {len(if_feats)} features → {n_anom:,} unusual "
                                     f"({fmt(pct_anom * 100, 1, '%')})", "ml"),
        ("📊 6 · Multi-indicator stress assessment", f"{int(scored_mask.sum())} cropped zones × 5 transparent rules", ""),
        ("🎯 7 · Priority zones", f"RED: {', '.join(red_z) or 'none'} · YELLOW: {', '.join(yel_z) or 'none'}", ""),
        ("👩‍🌾 8 · Field inspection", "The farm team checks the cause before changing irrigation", ""),
    ]
    html = '<div class="flow">' + '<div class="fa">➜</div>'.join(
        f'<div class="fs {cls}"><b>{h}</b><small>{s}</small></div>' for h, s, cls in steps) + "</div>"
    st.markdown(html, unsafe_allow_html=True)
    st.caption(
        "Steps 5 and 6 read the same satellite features. The transparent rules set each zone's colour. The Isolation Forest adds "
        "a separate 'unusual pattern' signal that is shown next to each priority zone; it does not change the stress score."
    )

    # ---- 1. Isolation Forest -------------------------------------------------
    st.markdown("### 1 · Isolation Forest — unsupervised anomaly detection <span class='badge on'>ACTIVE</span>", unsafe_allow_html=True)
    st.markdown("**The model identifies satellite observations that are statistically unusual compared with the rest of the "
                "farm. An anomaly is not proof of water stress.**")
    if has_if:
        i1, i2, i3, i4 = st.columns(4)
        i1.metric("Pixel samples used", f"{n_used:,}",
                  help=f"{n_raw:,} cropped-pixel samples returned; {n_raw - n_used:,} dropped for missing feature values.")
        i2.metric("Unusual pixels detected", f"{n_anom:,}")
        i3.metric("Unusual share", fmt(pct_anom * 100, 1, "%"))
        i4.metric("Features used", len(if_feats), help=", ".join(if_feats))
        st.markdown(
            f"**What it does:** an Isolation Forest ({ml.IF_N_ESTIMATORS} trees, scikit-learn) learns what is *typical* for "
            f"this farm on {date} from the standardized features **{', '.join(if_feats)}**. Pixels that the trees isolate "
            "quickly get a high anomaly score. **No labels are needed**, so it runs on real data today.\n\n"
            f"**How to read the numbers:** `contamination = {ml.IF_CONTAMINATION}` is a model sensitivity parameter. It fixes "
            f"the farm-wide share of unusual pixels, so {fmt(pct_anom * 100, 1, '%')} is a setting, not a measured prevalence "
            "of water stress. The useful output is **where** the unusual pixels cluster (right-hand chart) and **how** they "
            "differ from typical pixels (table below)."
        )
        h1, h2 = st.columns(2)
        with h1:
            st.markdown("**Anomaly score distribution**")
            st.plotly_chart(anomaly_score_hist(pix), key="if_hist", config={"displayModeBar": False})
        with h2:
            st.markdown("**Where unusual pixels concentrate (by zone)** · bar colour = rule-based class")
            st.plotly_chart(zone_anomaly_bars(scored, ml.IF_CONTAMINATION), key="if_zones", config={"displayModeBar": False})
        watch = anomaly_watch(c, ml.IF_CONTAMINATION)
        for w in watch.itertuples(index=False):
            st.info(f"**{w.zone_id}** is not classified as water stressed by the current rules, but the anomaly detector "
                    f"identifies an unusual satellite pattern there ({fmt(w.anomaly_share * 100, 0, '%')} of its sampled crop "
                    "pixels) that may warrant inspection. The two methods complement each other.")
        comp = pix.groupby("anomaly")[if_feats].mean().T.rename(columns={False: "Typical pixels (mean)", True: "Unusual pixels (mean)"})
        comp["Difference"] = comp["Unusual pixels (mean)"] - comp["Typical pixels (mean)"]
        c1, c2 = st.columns([1.3, 1])
        with c1:
            st.markdown("**How unusual pixels differ** (means of the actual samples)")
            st.dataframe(comp.round(3), column_config={"_index": "Feature"})
        with c2:
            pz = ml.assign_zones(pix, zones).merge(scored[["zone_id", "cls"]], on="zone_id")
            in_prio = pz.cls.isin(["HIGH", "MODERATE"])
            if len(pz) and pz.anomaly.any():
                share_anom = in_prio[pz.anomaly].mean()
                share_all = in_prio.mean()
                st.markdown("**Overlap with rule-based priority zones**")
                st.metric("Unusual pixels inside RED/YELLOW zones", fmt(share_anom * 100, 0, "%"),
                          help="Share of Isolation-Forest-unusual pixels located in zones the rules classed RED or YELLOW.")
                st.caption(f"By comparison, {fmt(share_all * 100, 0, '%')} of all sampled cropped pixels lie in those zones. "
                           "This is a descriptive overlap between two methods, not a validation. Neither method has been checked against field data.")
    else:
        st.info("The Isolation Forest could not be fitted on this date: there were fewer than 50 cropped-pixel samples with complete features.")

    # ---- 2. Rules --------------------------------------------------------------
    st.markdown("### 2 · Multi-indicator stress assessment — transparent rules <span class='badge on'>ACTIVE</span>", unsafe_allow_html=True)
    st.markdown(
        "The decision-support model is **rule-based on purpose**. Every zone's colour can be traced to named indicators and "
        "thresholds (see *Water Intelligence → Rule breakdown*), so a farmer or judge can check exactly why a zone is flagged."
    )
    st.dataframe(
        pd.DataFrame(
            {
                "Indicator": ["NDMI (canopy water)", "NDRE (chlorophyll)", "NDVI ÷ farm median", "LST − farm mean (°C)", "NDVI change (~2 weeks)"],
                "2 points if": [f"< {thr.ndmi_high}", f"< {thr.ndre_high}", f"< {thr.ndvi_rel_high}", f"> +{thr.lst_high}", f"< {thr.dndvi_high}"],
                "1 point if": [f"< {thr.ndmi_mod}", f"< {thr.ndre_mod}", f"< {thr.ndvi_rel_mod}", f"> +{thr.lst_mod}", f"< {thr.dndvi_mod}"],
            }
        ),
        hide_index=True,
    )
    st.caption(f"Class = points ÷ maximum available points: RED ≥ {thr.red_share:.0%}, YELLOW ≥ {thr.yellow_share:.0%}. "
               "These thresholds are the values currently set in the sidebar.")

    # ---- 3. Priority zones ---------------------------------------------------
    st.markdown("### 3 · Priority zones → field inspection")
    prio = scored[scored.cls.isin(["HIGH", "MODERATE"])].sort_values("score", ascending=False)
    if len(prio):
        st.dataframe(
            pd.DataFrame(
                {
                    "Zone": prio.zone_id,
                    "Status": prio.cls.map(lambda cl: f"{CLASS_EMOJI[cl]} {CLASS_LABELS[cl]}"),
                    "Rule score %": (prio.score * 100).round(0),
                    "Triggered indicators": prio.reasons.map(lambda r: ", ".join(r) or "—"),
                    "Unusual pixels % (Isolation Forest)": (prio.anomaly_share * 100).round(0),
                    "Next step": prio.apply(lambda r: analysis.recommendation(r.to_dict())["en"], axis=1),
                }
            ),
            hide_index=True,
        )
    else:
        st.success("No zones reach YELLOW or RED on this date.")

    # ---- 4. Random Forest ------------------------------------------------------
    st.markdown("### 4 · Random Forest — supervised model <span class='badge off'>NOT TRAINED</span>", unsafe_allow_html=True)
    st.markdown("**Random Forest is reserved for future supervised calibration once real field observations are available.** "
                "Supervised calibration is reserved for future field-labeled data.")
    status = ml.supervised_status()
    if status["ready"]:
        st.info("A labels file was found in data/ground_truth/. Supervised training is intentionally not run in this prototype.")
    else:
        st.caption(f"Status: {status['reason']}")
    st.markdown(
        "- There are **no real ground-truth labels** for these fields, so the model is not trained.\n"
        "- We **do not generate synthetic labels**. Labels derived from our own rules would only teach the model to copy the rules.\n"
        "- For the same reason, **no accuracy, precision, recall or F1** is reported. There is nothing valid to measure them against.\n"
        "- **Path to training:** collect dated field observations (soil-moisture probes, agronomist stress scores, irrigation-fault logs), "
        "pair them with the satellite features for the same dates, and save them to `data/ground_truth/labels.csv` using the template in that folder."
    )

    st.markdown("### Real data vs demo data")
    st.markdown(
        "| Component | Earth Engine mode | Demo mode |\n|---|---|---|\n"
        "| True-colour imagery, NDVI, NDRE, NDMI | **Real** Sentinel-2 L2A (10–20 m), SCL cloud mask | Simulated |\n"
        "| Surface temperature (LST) | **Real** Landsat 8/9 C2 L2 ST_B10 (±12 days) | Simulated |\n"
        "| Air temperature, precipitation | **Real** ERA5-Land reanalysis | Not shown |\n"
        "| Stress classes | Prototype rules applied to real indices | Prototype rules on simulated indices |\n"
        "| Isolation Forest anomalies | Fitted to real pixel samples | Fitted to simulated pixels |\n"
        "| Random Forest | Not trained (no real field labels) | Not trained |\n"
        "| Basemap | Esri World Imagery (reference only) | Esri World Imagery (reference only) |"
    )
    st.markdown("### Spectral indicators")
    for k, info in INDEX_INFO.items():
        st.markdown(f"**{info['name']}** — <span class='rtl'>{info['ar']}</span>", unsafe_allow_html=True)
        st.caption(f"`{info['formula']}` · {info['meaning']}")

    st.markdown("### Prototype decision-support model (rule-based)")
    st.markdown(
        "Each cropped zone (≥10% pixels with NDVI > 0.25) gets 0–2 points from each available indicator: "
        "**NDMI**, **NDRE**, **NDVI relative to the farm median**, **LST above the farm mean**, and **NDVI change "
        "over ~2 weeks**. The class depends on the share of the maximum points (GREEN < 25% ≤ YELLOW < 50% ≤ RED by "
        "default). All thresholds are editable in the sidebar and are **not calibrated** against field data. They are "
        "reasonable starting points for arid irrigated crops."
    )
    st.markdown("### Limitations")
    render_limitations(ar=False)
