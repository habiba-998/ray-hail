"""Farmer mode: simple, visual, bilingual pages built on the existing RAY results.

Nothing here computes a new classification. Farm status, priority, colours, scores and the plain-language
"signals" are read from `c.scored` (the output of analysis.score_zones) and its per-rule points.
"""
from __future__ import annotations

import numpy as np
import streamlit as st

from .. import analysis, ml
from ..config import CLASS_COLORS
from .common import (LIMITATIONS, Ctx, anomaly_watch, finite, fmt, priority_zones, render_farm_map, synced_control,
                     zone_picker, zone_row)
from .i18n import is_ar, ltr, t, tr

TINT = {"HIGH": "#FDECEA", "MODERATE": "#FFF6DD", "HEALTHY": "#E7F5EC", "NO_CROP": "#F1F3F4", "NO_DATA": "#ECEFF1"}
ICON = {"HIGH": "‼", "MODERATE": "!", "HEALTHY": "✓", "NO_CROP": "–", "NO_DATA": "?"}
MAP_ICON = {"HIGH": "⚠", "MODERATE": "●", "HEALTHY": "✓", "NO_CROP": "–", "NO_DATA": "?"}
# farm-level status  ->  (i18n key, colour class used for the palette)
FARM_STATUS = {"RED": ("status_RED", "HIGH"), "YELLOW": ("status_YELLOW", "MODERATE"),
               "GREEN": ("status_GREEN", "HEALTHY"), "NONE": ("status_NONE", "NO_CROP")}
LEVEL_COLOR = {0: CLASS_COLORS["HEALTHY"], 1: CLASS_COLORS["MODERATE"], 2: CLASS_COLORS["HIGH"], None: CLASS_COLORS["NO_DATA"]}

PAGES = ["home", "map", "zone", "water", "about"]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def go(page: str, zone: str | None = None) -> None:
    """Button callback: switch farmer page (and optionally the selected zone)."""
    st.session_state.fpage = page
    if zone:
        st.session_state.zone_sel = zone


def go_tech() -> None:
    st.session_state.mode = "tech"


def farm_status(c: Ctx) -> str:
    counts = c.scored.cls.value_counts()
    if counts.get("HIGH", 0):
        return "RED"
    if counts.get("MODERATE", 0):
        return "YELLOW"
    if counts.get("HEALTHY", 0):
        return "GREEN"
    return "NONE"


def cls_label(cls: str) -> str:
    return t(f"cls_{cls}")


def farmer_zone_label(z: str, cls: str) -> str:
    return f"{MAP_ICON[cls]} {t('zone')} {z} — {cls_label(cls)}"


def score_text(z: dict) -> str:
    if not finite(z["score"]):
        return "—"
    return ltr(f"{fmt(z['score'] * 100, 0, '%')} ({z['points']}/{z['max_points']})")


def rule_points(z: dict, rule: str):
    return z["rules"][rule][0]


def signals(z: dict) -> list[tuple[str, str, int | None]]:
    """Plain-language view of the existing rule points (no new thresholds)."""
    out = []
    for title, rule, prefix in (
        ("sig_veg", "NDVI vs farm median", "veg"),
        ("sig_moist", "NDMI (canopy water)", "moist"),
        ("sig_temp", "LST vs farm mean (°C)", "temp"),
        ("sig_change", "NDVI change (~2 weeks)", "change"),
    ):
        p = rule_points(z, rule)
        out.append((t(title), t(f"{prefix}_{p}") if p is not None else t("na"), p))
    return out


def status_card(title: str, sub: str, cls: str) -> str:
    color = CLASS_COLORS[cls]
    return (f"<div class='status-card' style='background:{TINT[cls]};border-color:{color}'>"
            f"<div class='icon' style='background:{color}'>{ICON[cls]}</div>"
            f"<div><h2>{title}</h2><div class='sub'>{sub}</div></div></div>")


def section(title: str) -> None:
    st.markdown(f"<div class='section-title'>{title}</div>", unsafe_allow_html=True)


def pill(cls: str, text: str | None = None) -> str:
    fg = "#0B2530" if cls == "MODERATE" else "#fff"
    return f"<span class='pill' style='background:{CLASS_COLORS[cls]};color:{fg}'>{ICON[cls]} {text or cls_label(cls)}</span>"


def anomaly_notes(c: Ctx, only: str | None = None) -> None:
    for w in anomaly_watch(c, ml.IF_CONTAMINATION).itertuples(index=False):
        if only and w.zone_id != only:
            continue
        st.markdown(f"<div class='note-card'>🔎 <b>{t('also_look')}:</b> "
                    f"{t('anomaly_note', z=w.zone_id, p=fmt(w.anomaly_share * 100, 0))}</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# pages
# ---------------------------------------------------------------------------
def page_home(c: Ctx) -> None:
    s = c.scored
    counts = s.cls.value_counts()
    n_r, n_m, n_h = counts.get("HIGH", 0), counts.get("MODERATE", 0), counts.get("HEALTHY", 0)
    n_nc = counts.get("NO_CROP", 0) + counts.get("NO_DATA", 0)
    fs = farm_status(c)
    key, cls = FARM_STATUS[fs]

    section(t("farm_status"))
    st.markdown(status_card(t(key), t("status_sub", n_bad=n_r + n_m, n_crop=n_r + n_m + n_h, date=c.date), cls),
                unsafe_allow_html=True)
    st.markdown(f"<div class='chips'>{t('chips', h=n_h, m=n_m, r=n_r, n=n_nc)}</div>", unsafe_allow_html=True)

    section(t("todays_priority"))
    prio = priority_zones(c)
    if len(prio):
        z = prio.iloc[0].to_dict()
        color = CLASS_COLORS[z["cls"]]
        st.markdown(
            f"<div class='prio-card' style='border-left-color:{color}'>"
            f"<div class='zone'>{ICON[z['cls']]} {t('zone')} {z['zone_id']}</div>"
            f"<div class='lbl' style='color:{color if z['cls'] == 'HIGH' else '#8A6100'}'>{cls_label(z['cls'])}</div>"
            f"<div class='act'>➜ {t('do_' + z['cls'])}</div>"
            f"<div class='note'>{t('screening_note')}</div></div>",
            unsafe_allow_html=True,
        )
        others = [f"{r.zone_id}" for r in prio.iloc[1:].itertuples(index=False)]
        if others:
            st.caption(tr(f"Other areas to watch: {', '.join(others)}", f"مناطق أخرى للمتابعة: {'، '.join(others)}"))
    else:
        st.markdown(f"<div class='soft'><p>✓ {t('no_priority')}</p></div>", unsafe_allow_html=True)
    anomaly_notes(c)

    st.write("")
    top = prio.iloc[0].zone_id if len(prio) else None
    b1, b2 = st.columns(2)
    b1.button(t("btn_map"), on_click=go, args=("map",), width="stretch", key="b_map")
    b2.button(t("btn_priority"), on_click=go, args=("zone" if top else "map", top), width="stretch", key="b_prio",
              type="primary" if top else "secondary")
    b3, b4 = st.columns(2)
    b3.button(t("btn_water"), on_click=go, args=("water",), width="stretch", key="b_water")
    b4.button(t("btn_tech"), on_click=go_tech, width="stretch", key="b_tech")


def page_map(c: Ctx) -> None:
    section(t("nav_map").split(" ", 1)[1])
    st.session_state.setdefault("fmap_view", "status")
    view = synced_control(t("map_view"), ["status", "photo"], "fmap_view", lambda v: t(f"view_{v}"))
    st.markdown(
        "<div class='legend-big'>" + "".join(
            f"<span><span class='sw' style='background:{CLASS_COLORS[k]}'></span>{MAP_ICON[k]} {cls_label(k)}</span>"
            for k in ("HEALTHY", "MODERATE", "HIGH", "NO_CROP")) + "</div>",
        unsafe_allow_html=True,
    )
    # zone ID + status icon (the legend above explains each icon, so status never relies on colour alone)
    labels = {z: f"{z} {MAP_ICON[cl]}" for z, cl in zip(c.scored.zone_id, c.scored.cls)}
    mcol, pcol = st.columns([2, 1])
    with mcol:
        render_farm_map(
            c, "True Color", f"farmer_map_{view}", zone_fill=0.38 if view == "status" else 0.0, height=470,
            labels=labels, label_px=15, short_attribution=True,
            class_labels={k: cls_label(k) for k in TINT},
            tooltip_aliases=(t("zone"), t("status"), t("score") + " %"),
        )
        st.caption("👆 " + t("map_help") + ("  ·  ⚠️ DEMO DATA" if not c.use_ee else ""))
    with pcol:
        zone_picker(c, "fmap", farmer_zone_label, label=t("choose_area"))
        z = zone_row(c, st.session_state.zone_sel)
        _zone_summary(z)
        st.button(t("view_details"), on_click=go, args=("zone",), width="stretch", key="b_details", type="primary")


def _zone_summary(z: dict) -> None:
    color = CLASS_COLORS[z["cls"]]
    st.markdown(
        f"<div class='prio-card' style='border-left-color:{color}'>"
        f"<div class='zone'>{t('zone').upper()} {z['zone_id']}</div>"
        f"<div style='margin:6px 0'>{pill(z['cls'])}</div>"
        f"<div class='act'><b>{t('score')}:</b> {score_text(z)}</div>"
        f"<div class='act'><b>{t('what_means')}:</b> {t('mean_' + z['cls'])}</div>"
        f"<div class='act'><b>{t('what_do')}:</b> {t('do_' + z['cls'])}</div></div>",
        unsafe_allow_html=True,
    )


def page_zone(c: Ctx) -> None:
    section(t("nav_zone").split(" ", 1)[1])
    zone_picker(c, "fzone", farmer_zone_label, label=t("choose_area"))
    z = zone_row(c, st.session_state.zone_sel)
    cls = z["cls"]
    st.markdown(status_card(f"{t('zone')} {z['zone_id']} · {cls_label(cls)}",
                            f"{t('score')}: {score_text(z)} · {ltr(c.date)}", cls), unsafe_allow_html=True)
    st.write("")
    st.markdown(f"<div class='soft'><h4>{t('what_means')}</h4><p>{t('mean_' + cls)}</p></div>", unsafe_allow_html=True)
    st.write("")
    st.markdown(f"<div class='soft'><h4>➜ {t('what_do')}</h4><p>{t('do_' + cls)}</p></div>", unsafe_allow_html=True)
    if cls in ("HIGH", "MODERATE"):
        st.caption("ⓘ " + t("screening_note"))

    if cls not in ("NO_CROP", "NO_DATA"):
        section(t("signals"))
        sig = signals(z)
        for row in (sig[:2], sig[2:]):
            cols = st.columns(2)
            for col, (title, text, p) in zip(cols, row):
                icon = {0: "✓", 1: "!", 2: "‼", None: "–"}[p]
                col.markdown(f"<div class='sig' style='border-top-color:{LEVEL_COLOR[p]}'><div class='t'>{title}</div>"
                             f"<div class='v'>{icon} {text}</div></div>", unsafe_allow_html=True)
            st.write("")
    anomaly_notes(c, only=z["zone_id"])

    with st.expander(t("tech_expander")):
        m = st.columns(4)
        m[0].metric("NDVI", fmt(z["ndvi"]), None if not finite(z["dndvi"]) else fmt(z["dndvi"], 2, signed=True),
                    help=tr("Vegetation index", "مؤشر الغطاء النباتي"))
        m[1].metric("NDRE", fmt(z["ndre"]), help=tr("Red-edge (chlorophyll) index", "مؤشر الحافة الحمراء (الكلوروفيل)"))
        m[2].metric("NDMI", fmt(z["ndmi"]), help=tr("Canopy moisture index", "مؤشر رطوبة النبات"))
        m[3].metric("LST", fmt(z["lst"], 1, " °C"), None if not finite(z["lst_anom"]) else fmt(z["lst_anom"], 1, " °C", signed=True),
                    delta_color="inverse", help=tr("Land surface temperature (Landsat); delta = vs farm mean",
                                                   "درجة حرارة سطح الأرض (Landsat)؛ الفرق مقارنة بمتوسط المزرعة"))
        m2 = st.columns(2)
        m2[0].metric(tr("Crop cover", "الغطاء المحصولي"), fmt(z["veg_frac"] * 100 if finite(z["veg_frac"]) else np.nan, 0, "%"))
        m2[1].metric(tr("Unusual pixels (Isolation Forest)", "بكسلات غير معتادة (Isolation Forest)"),
                     fmt(z["anomaly_share"] * 100 if finite(z["anomaly_share"]) else np.nan, 0, "%"))
        st.dataframe(analysis.rule_table(z), hide_index=True)
        st.caption(tr("Same values and rules as Technical mode.", "القيم والقواعد نفسها المستخدمة في الوضع الفني."))

    b1, b2 = st.columns(2)
    b1.button(t("go_water"), on_click=go, args=("water",), width="stretch", key="b_zwater")
    b2.button(t("btn_map"), on_click=go, args=("map",), width="stretch", key="b_zmap")


def _irrigation_card(z: dict) -> None:
    cls = z["cls"]
    color = CLASS_COLORS[cls]
    reasons = "".join(f"<li>{t('reason_' + r)}</li>" for r in z.get("reasons", []))
    st.markdown(
        f"<div class='prio-card' style='border-left-color:{color}'>"
        f"<div style='display:flex;gap:10px;flex-wrap:wrap;align-items:center'>"
        f"<span class='zone'>{t('zone')} {z['zone_id']}</span>{pill(cls, t('priority') + ': ' + t('prio_' + cls))}</div>"
        f"<div class='act'><b>{t('recommendation')}:</b> {t('do_' + cls)}</div>"
        f"<div class='act'><b>{t('why')}</b> {t('why_' + cls)}<ul class='checklist' style='margin:4px 0 0 0'>{reasons}</ul></div>"
        f"<div class='note'>⚠️ {t('important')} {t('no_volume')}</div></div>",
        unsafe_allow_html=True,
    )


def page_water(c: Ctx) -> None:
    section(t("irr_title"))
    prio = priority_zones(c)
    if len(prio):
        _irrigation_card(prio.iloc[0].to_dict())
        if len(prio) > 1:
            with st.expander(tr(f"Other areas that need attention ({len(prio) - 1})",
                                f"مناطق أخرى تحتاج متابعة ({len(prio) - 1})")):
                for r in prio.iloc[1:].itertuples(index=False):
                    _irrigation_card(zone_row(c, r.zone_id))
                    st.write("")
        section(t("checklist"))
        st.markdown("<ul class='checklist'>" + "".join(f"<li>☐ {t(f'chk_{i}')}</li>" for i in range(1, 5)) + "</ul>",
                    unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='soft'><p>✓ {t('all_good')}</p></div>", unsafe_allow_html=True)

    anomaly_notes(c)
    nc = list(c.scored.loc[c.scored.cls == "NO_CROP", "zone_id"])
    if nc:
        section(t("no_crop_title"))
        st.markdown(f"<div class='soft'><p>⚪ {t('no_crop_text', zones=', '.join(nc))}</p></div>", unsafe_allow_html=True)

    section(t("how_helps"))
    st.markdown(f"<div class='soft'><p>1️⃣ {t('help_1')}<br>2️⃣ {t('help_2')}<br>3️⃣ {t('help_3')}</p></div>",
                unsafe_allow_html=True)
    st.caption(t("help_note"))


def page_about(c: Ctx) -> None:
    section(t("about_title"))
    st.markdown(f"<div class='soft'><p>{t('about_text')}</p></div>", unsafe_allow_html=True)
    section(t("how_status"))
    st.markdown(f"<div class='soft'><p>{t('how_status_text')}</p></div>", unsafe_allow_html=True)
    section(t("data_title"))
    current = (tr(f"This screen uses REAL satellite data from Google Earth Engine (Sentinel-2 image of {ltr(c.date)}).",
                  f"تستخدم هذه الشاشة بيانات أقمار صناعية حقيقية من Google Earth Engine (صورة Sentinel-2 بتاريخ {ltr(c.date)}).")
               if c.use_ee else
               tr("This screen uses DEMO DATA: a simulated farm, not real satellite observations.",
                  "تستخدم هذه الشاشة بيانات تجريبية: مزرعة محاكاة وليست رصدًا حقيقيًا بالأقمار الصناعية."))
    st.markdown(
        f"<div class='soft'><p>🛰️ {tr('Sentinel-2 (European Copernicus satellites): farm images about every 5 days.', 'Sentinel-2 (أقمار كوبرنيكوس الأوروبية): صور للمزرعة كل 5 أيام تقريبًا.')}<br>"
        f"🌡️ {tr('Landsat 8/9 (USGS/NASA): surface temperature.', 'Landsat 8/9 (هيئة المساحة الأمريكية/ناسا): درجة حرارة السطح.')}<br>"
        f"🌦️ {tr('ERA5-Land: regional weather (air temperature, rain).', 'ERA5-Land: الطقس الإقليمي (حرارة الهواء، الأمطار).')}<br><br>"
        f"<b>{current}</b></p></div>",
        unsafe_allow_html=True,
    )
    section(t("limits_title"))
    st.markdown("\n".join(f"- {a if is_ar() else e}" for e, a in LIMITATIONS))
    st.button(t("btn_tech"), on_click=go_tech, width="stretch", key="b_about_tech")


def render(c: Ctx) -> None:
    st.session_state.setdefault("fpage", "home")
    labels = {"home": t("nav_home"), "map": t("nav_map"), "zone": t("nav_zone"), "water": t("nav_water"), "about": t("nav_about")}
    page = synced_control("nav", PAGES, "fpage", labels.get)
    {"home": page_home, "map": page_map, "zone": page_zone, "water": page_water, "about": page_about}[page](c)
