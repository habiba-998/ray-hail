"""Farmer interface – the only interface of RAY (Arabic, plain language, no technical terms).

Journey: Home (what needs attention?) → Map (where?) → Zones (evidence, alternatives, what to check) → Irrigation
(decide after verifying) → Field inspection log (optional, non-photographic) → Technical details → About.

All statuses come from the existing pipeline (`c.scored` from analysis.score_zones); causes from src/fusion.py;
crop facts from src/knowledge.py. Nothing technical (data sources, indices, algorithms, IDs) is shown here.
"""
from __future__ import annotations

import datetime as dt
import logging

import pandas as pd
import streamlit as st

from .. import analysis, fusion, knowledge, ml, storage, validation
from ..config import CLASS_COLORS, TREND_MIN_OBS
from . import details
from .common import (ANOMALY_NOTE_FACTOR, Ctx, anomaly_watch, ee_ts, finite, fmt, priority_zones, render_farm_map, synced_control,
                     synced_select, zone_row)
from .i18n import area_noun, count_areas, is_ar, ltr, t, tr

ICON = {"HIGH": "‼", "MODERATE": "!", "HEALTHY": "✓", "NO_CROP": "–", "NO_DATA": "?"}
EMOJI = {"HIGH": "🔴", "MODERATE": "🟡", "HEALTHY": "🟢", "NO_CROP": "⚪", "NO_DATA": "⚫"}
TEXT_COLOR = {"HIGH": "#A12F2B", "MODERATE": "#7A5600", "HEALTHY": "#1E5B38", "NO_CROP": "#5E6E66", "NO_DATA": "#5E6E66"}
PAGES = ["home", "map", "zones", "water", "log", "tech", "about"]
log = logging.getLogger("ray")


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def go(page: str, zone: str | None = None) -> None:
    st.session_state.fpage = page
    if zone:
        st.session_state.zone_sel = zone


def cls_label(cls: str) -> str:
    return t(f"cls_{cls}")


def zone_label(z: str, cls: str) -> str:
    return f"{EMOJI[cls]} {t('zone')} {z} — {cls_label(cls)}"


def crop_label(cid: str) -> str:
    c = knowledge.crop(cid)
    return f"{c['icon']} {c['name_ar'] if is_ar() else c['name_en']}"


def crop_name(cid: str) -> str:
    c = knowledge.crop(cid)
    return c["name_ar"] if is_ar() else c["name_en"]


def section(title: str) -> None:
    st.markdown(f"<div class='section-title'>{title}</div>", unsafe_allow_html=True)


def question(text: str) -> None:
    st.markdown(f"<div class='q'>{text}</div>", unsafe_allow_html=True)


def checklist(items: list[str]) -> None:
    st.markdown("<ul class='checklist'>" + "".join(f"<li>☐ {s}</li>" for s in items) + "</ul>", unsafe_allow_html=True)


def zone_card(z: dict, extra: str = "") -> None:
    """Answers: where is the problem? why does it deserve attention? what do I do now?"""
    cls = z["cls"]
    meta = ""
    if cls not in ("NO_CROP", "NO_DATA") and z.get("n_signals"):
        meta = f"<div class='meta'>{t('ind_flagged')}: {int(z.get('n_flagged') or 0)} / {int(z['n_signals'])}</div>"
    st.markdown(
        f"<div class='zone-card' style='border-inline-start-color:{CLASS_COLORS[cls]}'>"
        f"<div class='top'><span class='z'>{t('zone')} {z['zone_id']}</span>"
        f"<span class='pill {cls}'>{ICON[cls]} {cls_label(cls)}</span></div>"
        f"<div class='d'>{t('why_' + cls)}</div>"
        f"<div class='d'><b>➜ {t('do_' + cls)}</b></div>{meta}{extra}</div>",
        unsafe_allow_html=True,
    )


def level_badge(level: str, level_ar: str) -> str:
    return f"<span class='lvl {level}'>{t('suspicion_level')}: {level_ar if is_ar() else level}</span>"


def cause_rows(causes: list[dict], limit: int | None = None) -> None:
    shown = [r for r in causes if r["score"] > 0][:limit]
    if not shown:
        st.markdown(f"<div class='card soft'>{t('no_evidence')}</div>", unsafe_allow_html=True)
        return
    for r in shown:
        st.markdown(f"<div class='cause'><span class='ic'>{r['icon']}</span><span class='nm'>{r['ar'] if is_ar() else r['en']}</span>"
                    f"{level_badge(r['level'], r['level_ar'])}</div>", unsafe_allow_html=True)
        with st.expander(f"{t('why_reasons')} — {r['ar'] if is_ar() else r['en']}"):
            for reason in r["reasons"]:
                st.markdown(f"- {fusion.reason_text(reason, is_ar())}")


def problem_details(p: dict) -> None:
    """Sourced disease / pest information (symptoms, conditions, what to check, similar problems, reference image)."""
    icon = "🦠" if p["type"] == "disease" else "🐛"
    with st.expander(f"{icon} {p['name_ar'] if is_ar() else p['name_en']}"):
        st.markdown(f"**{t('symptoms')}:** {p['symptoms_ar'] if is_ar() else p['symptoms_en']}")
        cond = p.get("conditions_ar") if is_ar() else p.get("conditions_en")
        if cond:
            st.markdown(f"**{t('conditions')}:** {cond}")
        st.markdown(f"**{t('what_check')}:**\n" + "\n".join(f"- {s}" for s in (p["inspection_ar"] if is_ar() else p["inspection_en"])))
        sim = [knowledge.problem(s) for s in p.get("similar", [])]
        if sim:
            st.markdown(f"**{t('similar')}:** " + "، ".join(x["name_ar"] if is_ar() else x["name_en"] for x in sim if x))
        imgs = knowledge.images_for(p)
        if imgs:
            im = imgs[0]
            st.image(im["image_url"], width=300, caption=t("ref_image"))
            st.caption(t("img_credit", a=im["author"] or "—", lic=im["license"]) + f" · [{tr('image page', 'صفحة الصورة')}]({im['source_page']})")
        else:
            st.caption(t("no_ref_image"))
        s = knowledge.source(p["source"])
        if s:
            st.caption(f"{t('source')}: [{s['publisher']}]({s['url']})")


def weather_line(c: Ctx) -> None:
    w = c.wx_summary
    if not w:
        if c.use_ee:
            st.caption("🌦️ " + t("weather_none"))
        return
    rh = fmt(w["rh_mean"], 0, "٪" if is_ar() else "%") if finite(w["rh_mean"]) else "—"
    st.markdown(f"<div class='muted'>🌦️ {t('weather_line', t=w['tmax_mean'], rh=ltr(rh), p=w['precip_sum'])}</div>", unsafe_allow_html=True)
    st.caption(t("weather_until", d=ltr(w["last_date"])), unsafe_allow_html=True)


def zone_causes(c: Ctx, z: dict, **extra) -> list[dict]:
    return fusion.possible_causes(z, weather=c.wx_summary, anomaly_share=z.get("anomaly_share"),
                                  contamination=ml.IF_CONTAMINATION, **extra)


def choose_zone(c: Ctx, label: str | None = None) -> dict:
    prio = list(priority_zones(c).zone_id)
    order = prio + [z for z in c.scored.zone_id if z not in prio]
    synced_select(label or t("choose_area"), order, "zone_sel", lambda z: zone_label(z, zone_row(c, z)["cls"]))
    return zone_row(c, st.session_state.zone_sel)


# ---------------------------------------------------------------------------
# pages
# ---------------------------------------------------------------------------
def page_home(c: Ctx) -> None:
    question(t("q_home"))
    counts = c.scored.cls.value_counts()
    n = {k: int(counts.get(k, 0)) for k in ("HIGH", "MODERATE", "HEALTHY", "NO_DATA", "NO_CROP")}
    nocrop = list(c.scored.loc[c.scored.cls == "NO_CROP", "zone_id"])
    tiles = [("HIGH", n["HIGH"], t("cls_HIGH")), ("MODERATE", n["MODERATE"], t("cls_MODERATE")),
             ("HEALTHY", n["HEALTHY"], t("cls_HEALTHY")), ("NO_DATA", n["NO_DATA"], t("cls_NO_DATA"))]
    st.markdown(
        f"<div class='section-title'>{t('today_status')}</div><div class='kpis'>"
        + "".join(f"<div class='kpi {k}'><div class='n'>{v}</div><div class='l'>{lbl}</div></div>" for k, v, lbl in tiles)
        + "</div>"
        + (f"<div class='muted'>⚪ {t('n_nocrop', z='، '.join(nocrop))}</div>" if nocrop else ""),
        unsafe_allow_html=True,
    )
    prio = priority_zones(c)
    st.write("")
    if len(prio):
        top = prio.iloc[0].to_dict()
        section(t("next_action"))
        zone_card(top)
        st.write("")
        st.button(t("btn_top"), on_click=go, args=("zones", top["zone_id"]), type="primary", width="stretch", key="b_prio")
        others = list(prio.iloc[1:].zone_id)
        if others:
            st.caption(t("others_watch", z="، ".join(others)))
    elif n["NO_DATA"] == len(c.scored):
        st.markdown(f"<div class='card soft'>⚫ {t('do_NO_DATA')}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='card soft'>✓ {t('no_priority')}</div>", unsafe_allow_html=True)
    for w in anomaly_watch(c, ml.IF_CONTAMINATION).itertuples(index=False):
        st.markdown(f"<div class='note-card'>🔎 {t('anomaly_note', z=w.zone_id)}</div>", unsafe_allow_html=True)

    section(t("crop"))
    synced_select(t("crop"), [cc["id"] for cc in knowledge.crops()], "crop", crop_label, label_visibility="collapsed")
    st.write("")
    b1, b2 = st.columns(2)
    b1.button(t("btn_map"), on_click=go, args=("map",), width="stretch", key="b_map")
    b2.button(t("nav_log"), on_click=go, args=("log",), width="stretch", key="b_log")


def page_map(c: Ctx) -> None:
    question(t("q_map"))
    st.session_state.setdefault("fmap_view", "status")
    view = synced_control("map view", ["status", "image"], "fmap_view", lambda v: t(f"view_{v}"))
    st.markdown("<div class='legend-big'>" + "".join(
        f"<span><span class='sw' style='background:{CLASS_COLORS[k]}'></span>{ICON[k]} {cls_label(k)}</span>"
        for k in ("HIGH", "MODERATE", "HEALTHY", "NO_DATA", "NO_CROP")) + "</div>", unsafe_allow_html=True)
    labels = {z: f"{z} {ICON[cl]}" for z, cl in zip(c.scored.zone_id, c.scored.cls)}
    mcol, pcol = st.columns([2, 1])
    with mcol:
        render_farm_map(c, "True Color", f"farmer_map_{view}", zone_fill=0.38 if view == "status" else 0.0, height=460,
                        labels=labels, label_px=15, short_attribution=True, basemap_attr="© Esri",
                        class_labels={k: cls_label(k) for k in CLASS_COLORS},
                        tooltip_aliases=(t("zone"), t("status"), t("ind_flagged")))
        st.caption("👆 " + t("map_help"))
    with pcol:
        z = choose_zone(c)
        zone_card(z)
        st.button(t("view_details"), on_click=go, args=("zones",), type="primary", width="stretch", key="b_details")
    st.caption("ⓘ " + t("grid_note"))
    st.caption("ⓘ " + t("sky_ground"))


IND_KEY = {"NDVI vs farm median": "ind_ndvi", "NDMI (canopy water)": "ind_ndmi", "NDRE (chlorophyll)": "ind_ndre",
           "LST vs farm mean (°C)": "ind_lst", "NDVI change (~2 weeks)": "ind_dndvi"}


def _limits(thr) -> dict:
    """Screening limit (the 1-point threshold) of each rule, as shown to the user."""
    return {"NDVI vs farm median": f"< {thr.ndvi_rel_mod:.2f}", "NDMI (canopy water)": f"< {thr.ndmi_mod:.2f}",
            "NDRE (chlorophyll)": f"< {thr.ndre_mod:.2f}", "LST vs farm mean (°C)": f"> +{thr.lst_mod:.1f}",
            "NDVI change (~2 weeks)": f"< {thr.dndvi_mod:.2f}"}


def _indicator_table(c: Ctx, z: dict) -> None:
    """Plain HTML table (right-to-left, no data-grid toolbar) with the value, the provisional limit and the flag."""
    lim = _limits(c.thr)
    head = "".join(f"<th>{t(k)}</th>" for k in ("ind_col_name", "ind_col_value", "ind_col_limit", "ind_col_flag"))
    body = ""
    for k, (pts, val, _rule) in z["rules"].items():
        flag = t("flag_na") if pts is None else t("flag_yes") if pts > 0 else t("flag_no")
        cls = "na" if pts is None else "yes" if pts > 0 else "no"
        value = fmt(val, 2, signed=k.startswith(("LST", "NDVI change")))
        body += (f"<tr><td>{t(IND_KEY[k])}</td><td>{ltr(value)}</td><td>{ltr(lim[k] if pts is not None else '—')}</td>"
                 f"<td><span class='flag {cls}'>{flag}</span></td></tr>")
    st.markdown(f"<table class='ind-table'><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"
                f"<div class='muted' style='margin-top:6px'>{t('ind_note')}</div>", unsafe_allow_html=True)
    with st.expander(tr("Technical rule table", "جدول القواعد التقني")):
        st.dataframe(analysis.rule_table(z), hide_index=True, width="stretch")


def _quality_line(z: dict) -> None:
    clear, veg = z.get("clear_frac"), z.get("veg_frac")
    st.caption(t("z_quality_line", clear=round(clear * 100) if finite(clear) else "—", veg=round(veg * 100) if finite(veg) else "—",
                 n=int(z.get("n_signals") or 0)))


def _reference_text(c: Ctx) -> str:
    prev = ltr(c.prev_date) if c.prev_date else t("z_reference_noprev")
    return t("z_reference_text", ndvi=fmt(c.ref.get("ndvi_median")), prev=prev)


def page_zones(c: Ctx) -> None:
    z = choose_zone(c)
    zone_card(z)
    if z["cls"] in ("NO_CROP", "NO_DATA"):
        section(t("z_quality"))
        _quality_line(z)
    else:
        section(t("z_why_flag"))
        st.markdown("\n".join(f"- {w}" for w in _why_lines(z)))
        section(t("z_values"))
        _indicator_table(c, z)
        section(t("z_quality"))
        _quality_line(z)
        section(t("z_reference"))
        st.markdown(f"<div class='muted'>{_reference_text(c)}</div>", unsafe_allow_html=True)
        trend_block(c, z)
        section(t("z_alt"))
        cause_rows(zone_causes(c, z), limit=3)
        st.markdown(f"<div class='note-card'>ⓘ {t('prelim')}</div>", unsafe_allow_html=True)
        weather_line(c)
        section(t("q_check"))
        checklist([t(f"check_{i}") for i in range(1, 6)])
        st.warning(t("irr_rule"))

    crop_id = st.session_state.get("crop", "unknown")
    probs = knowledge.problems_for(crop_id)
    section(t("common_problems", crop=crop_name(crop_id)) if probs else t("crop"))
    if probs:
        for p in probs:
            problem_details(p)
    else:
        st.caption(t("pick_crop"))


def page_log(c: Ctx) -> None:
    question(t("log_title"))
    st.caption(t("log_intro"))
    prio = list(priority_zones(c).zone_id)
    ids = prio + [z for z in c.scored.zone_id if z not in prio]
    cur = st.session_state.get("zone_sel")
    with st.expander(t("log_add"), expanded=True):
        with st.form("inspection_form", clear_on_submit=True):
            zid = st.selectbox(t("zone"), ids, index=ids.index(cur) if cur in ids else 0, key="log_zone",
                               format_func=lambda x: zone_label(x, zone_row(c, x)["cls"]))
            day = st.date_input(t("log_date"), value=dt.date.today(), max_value=dt.date.today(), key="log_day")
            cond = st.radio(t("log_condition"), list(storage.CONDITIONS), format_func=lambda v: t(f"cond_{v}"), index=2, key="log_cond")
            irr = st.radio(t("log_irrigation"), list(storage.IRRIGATION_ISSUE), format_func=lambda v: t(f"irr_{v}"), index=2,
                           horizontal=True, key="log_irr")
            alt = st.multiselect(t("log_alt"), list(storage.ALT_CAUSES), format_func=lambda v: t(f"alt_{v}"), key="log_alt")
            moist = st.number_input(t("log_moisture"), min_value=0.0, max_value=100.0, value=0.0, step=1.0, key="log_moist")
            by = st.text_input(t("log_inspector"), max_chars=60, key="log_by")
            notes = st.text_area(t("notes"), max_chars=500, key="log_notes")
            submitted = st.form_submit_button(t("btn_log_save"), type="primary")
        if submitted:
            z = zone_row(c, zid)
            rec = {
                "session_id": c.session_id, "farm_id": c.farm_id, "farm_name": c.farm_name,
                "data_mode": "real" if c.use_ee else "demo", "zone_id": zid, "crop_id": st.session_state.get("crop", "unknown"),
                "satellite_date": c.date, "satellite_class": z["cls"], "satellite_score": z["score"] if finite(z["score"]) else None,
                "lat": (z["min_lat"] + z["max_lat"]) / 2, "lon": (z["min_lon"] + z["max_lon"]) / 2,
                "inspection_date": day.isoformat(), "condition": cond, "irrigation_issue": irr, "alt_causes": alt or None,
                "soil_moisture_pct": float(moist) if moist > 0 else None, "inspector": by.strip() or None, "notes": notes.strip() or None,
            }
            try:
                c.store.save_observation(rec)
                st.success(t("log_saved"))
                st.caption(c.store.persistent_note_ar if is_ar() else c.store.persistent_note_en)
            except Exception as exc:  # noqa: BLE001
                log.warning("inspection not saved: %s", exc)
                st.error(t("save_failed"))

    st.caption(t("log_session_note"))
    try:
        rows = c.store.list_observations(c.session_id, limit=50)
    except Exception:  # noqa: BLE001
        rows = []
    if not rows:
        st.markdown(f"<div class='card soft'>{t('log_empty')}</div>", unsafe_allow_html=True)
        return
    section(t("val_title"))
    v = validation.summarize([r for r in rows if r.get("data_mode") != "demo"])
    if not v["n_usable"]:
        st.caption(t("val_none"))
    else:
        st.markdown(f"- {t('val_flagged', n=v['n_flagged_inspected'], k=v['n_flagged_confirmed'])}\n"
                    f"- {t('val_unflagged', n=v['n_unflagged_inspected'], k=v['n_unflagged_problem'])}")
        if not v["reliable"]:
            st.caption(t("val_small", m=validation.MIN_RECORDS))
    for r in rows:
        demo = " · " + t("st_demo") if r.get("data_mode") == "demo" else ""
        with st.expander(f"📍 {t('zone')} {r['zone_id']} · {r.get('inspection_date') or '—'} · {t('cond_' + r['condition']) if r.get('condition') in storage.CONDITIONS else '—'}{demo}"):
            st.markdown(f"**{t('farm')}:** {r.get('farm_name') or '—'}")
            if r.get("satellite_class") in CLASS_COLORS:
                st.markdown(f"**{t('log_sat')}:** {cls_label(r['satellite_class'])} ({ltr(r.get('satellite_date') or '—')})", unsafe_allow_html=True)
            if r.get("irrigation_issue") in storage.IRRIGATION_ISSUE:
                st.markdown(f"**{t('log_irrigation')}** {t('irr_' + r['irrigation_issue'])}")
            if r.get("alt_causes"):
                st.markdown(f"**{t('log_alt')}:** " + "، ".join(t(f"alt_{a}") for a in r["alt_causes"] if a in storage.ALT_CAUSES))
            if r.get("soil_moisture_pct") is not None:
                st.markdown(f"**{t('log_moisture_short')}:** {fmt(r['soil_moisture_pct'], 0)}")
            if r.get("inspector"):
                st.markdown(f"**{t('log_by')}:** {r['inspector']}")
            if r.get("notes"):
                st.markdown(f"**{t('notes')}:** {r['notes']}")


def page_tech(c: Ctx) -> None:
    details.render(c)


def _zone_series(c: Ctx, z: dict) -> tuple[pd.DataFrame | None, bool]:
    """Real NDVI series of one zone up to the analysis date (cached satellite query, or the local demo farm).

    Returns (series or None, query_failed). A failed query is reported as unavailable, never as "insufficient data".
    Nothing is interpolated.
    """
    zb = (z["min_lon"], z["min_lat"], z["max_lon"], z["max_lat"])
    try:
        if c.use_ee:
            ts = ee_ts(zb, str(c.start), str(c.end + dt.timedelta(days=1)), c.max_cloud)
        else:
            ts = c.farm.timeseries(zb)
    except Exception as exc:  # noqa: BLE001 -- optional context, never blocks the page
        log.warning("zone trend unavailable: %s", exc)
        return None, True
    if ts is None or ts.empty or "NDVI" not in ts:
        return None, False
    ts = ts.dropna(subset=["NDVI"])
    return ts[ts.date <= pd.Timestamp(c.date)], False


def _trend_chart(ts: pd.DataFrame, baseline: float):
    """NDVI over time with day/month dates (no English month names), Arabic axis titles and the baseline as a dashed line."""
    import altair as alt

    d = ts[["date", "NDVI"]].copy()
    x = alt.X("date:T", title=t("tr_axis_date"), axis=alt.Axis(format="%d/%m", labelAngle=0, tickCount=6))
    y = alt.Y("NDVI:Q", title=t("tr_axis_val"), scale=alt.Scale(zero=False))
    line = alt.Chart(d).mark_line(color="#2F7D4E", strokeWidth=2.5).encode(x=x, y=y)
    pts = alt.Chart(d).mark_circle(color="#2F7D4E", size=28).encode(
        x=x, y=y, tooltip=[alt.Tooltip("date:T", title=t("tr_axis_date"), format="%Y-%m-%d"),
                           alt.Tooltip("NDVI:Q", title=t("tr_axis_val"), format=".2f")])
    rule = alt.Chart(pd.DataFrame({"b": [baseline]})).mark_rule(color="#5E6E66", strokeDash=[5, 4]).encode(y="b:Q")
    return (line + pts + rule).properties(height=230).configure_axis(labelFontSize=12, titleFontSize=13, titleFontWeight=600)


def trend_block(c: Ctx, z: dict) -> None:
    """Same-zone temporal comparison; says 'insufficient data' / 'unavailable' instead of inventing a conclusion."""
    section(t("trend_title"))
    ts, failed = _zone_series(c, z)
    if failed:
        st.caption(t("tr_unavailable"))
        return
    summ = analysis.temporal_summary(ts, c.date) if ts is not None else {"n": 0, "status": "insufficient"}
    if summ["status"] == "insufficient":
        st.caption(t("tr_insufficient", n=summ["n"], m=TREND_MIN_OBS))
        return
    # neutral icon for "stable": no recent change is not the same as healthy
    dot = {"stable": "⚪", "below_earlier": "🟠", "decline": "🟡", "persistent_decline": "🔴"}[summ["status"]]
    text = t("tr_below_earlier", peak=fmt(summ["earlier_peak"])) if summ["status"] == "below_earlier" else t("tr_" + summ["status"])
    st.markdown(f"<div class='status-line'>{dot} {text}</div>", unsafe_allow_html=True)
    st.altair_chart(_trend_chart(ts, summ["baseline"]), width="stretch")
    st.caption(t("tr_legend_base") + " · " + t("tr_baseline", latest=fmt(summ["latest"]), base=fmt(summ["baseline"])) + " "
               + t("trend_basis", n=summ["n"], a=ltr(summ["first_date"]), b=ltr(summ["last_date"])), unsafe_allow_html=True)


def _why_lines(z: dict) -> list[str]:
    """Plain-language reasons built only from this area's existing rule points (no new thresholds)."""
    pts = {k: v[0] for k, v in z["rules"].items()}
    lines = []
    if pts.get("NDVI vs farm median"):
        lines.append(t("why_plant"))
    if pts.get("NDMI (canopy water)"):
        lines.append(t("why_moisture"))
    if pts.get("LST vs farm mean (°C)") is None:
        lines.append(t("why_heat_na"))
    elif pts["LST vs farm mean (°C)"]:
        lines.append(t("why_heat"))
    if pts.get("NDVI change (~2 weeks)"):
        lines.append(t("why_change"))
    if pts.get("NDRE (chlorophyll)"):
        lines.append(t("why_green"))
    share = z.get("anomaly_share")
    if finite(share) and share >= ANOMALY_NOTE_FACTOR * ml.IF_CONTAMINATION:
        lines.append(t("why_unusual"))
    return lines if any(x != t("why_heat_na") for x in lines) else [t("why_none"), *lines]


def _cause_card(title_key: str, lines: list[str], r: dict | None = None, source_id: str | None = None) -> None:
    """One possible cause: plain explanation + whether the available data supports it or it needs a field check."""
    if r and r["score"] > 0:
        ev = level_badge(r["level"], r["level_ar"]) + f" <span class='muted'>· {t('ev_supported')}</span>"
    else:
        ev = f"<span class='lvl none'>{t('ev_field')}</span>"
    body = "".join(f"<li>{t(k)}</li>" for k in lines)
    st.markdown(f"<div class='card' style='margin-bottom:8px'><b>{t(title_key)}</b><ul style='margin:6px 0'>{body}</ul>"
                f"<div>{ev}</div></div>", unsafe_allow_html=True)
    if r and r["score"] > 0:
        with st.expander(f"{t('why_reasons')} — {t(title_key)}"):
            for reason in r["reasons"]:
                st.markdown(f"- {fusion.reason_text(reason, is_ar())}")
    s = knowledge.source(source_id) if source_id else None
    if s:
        st.caption(f"{t('source')}: [{s['publisher']}]({s['url']})")


def page_water(c: Ctx) -> None:
    question(t("irr_title"))
    st.markdown(f"<div class='card soft'>ⓘ {t('irr_dss')}</div>", unsafe_allow_html=True)

    # 1. irrigation status of the farm (counts of the existing classes)
    counts = c.scored.cls.value_counts()
    n_r, n_m, n_h = (int(counts.get(k, 0)) for k in ("HIGH", "MODERATE", "HEALTHY"))
    section(t("irr_status"))
    st.markdown(
        f"<div class='card'><div class='status-line'>🔴 {count_areas(n_r, 'check')}</div>"
        f"<div class='status-line'>🟡 {count_areas(n_m, 'watch')}</div>"
        f"<div class='status-line'>🟢 {t('irr_ok_line', n=area_noun(n_h))}</div></div>", unsafe_allow_html=True)

    prio = priority_zones(c)
    if not len(prio):
        st.markdown(f"<div class='card soft'>✓ {t('irr_none')}</div>", unsafe_allow_html=True)
    else:
        # 2. highest priority + shortcut to the map with the area selected
        top = str(prio.iloc[0].zone_id)
        section(t("irr_top", z=top))
        st.button(t("btn_show_on_map", z=top), on_click=go, args=("map", top), type="primary", width="stretch", key="b_irr_map")

        # 3. possible water stress in the chosen area (always hedged)
        ids = [str(x) for x in prio.zone_id]
        synced_select(t("irr_zone_pick"), ids, "zone_sel", lambda zz: zone_label(zz, zone_row(c, zz)["cls"]))
        z = zone_row(c, st.session_state.zone_sel)
        causes = {r["cause"]: r for r in zone_causes(c, z)}
        wscore = causes["water"]["score"]
        head = t("ws_likely") if wscore >= 3 else t("ws_some") if wscore >= 1 else t("ws_none")
        st.markdown(
            f"<div class='zone-card' style='border-inline-start-color:{CLASS_COLORS[z['cls']]}'>"
            f"<div class='z'>📍 {t('zone')} {z['zone_id']}</div>"
            f"<div class='s' style='color:{TEXT_COLOR[z['cls']]}'>💧 {head}</div>"
            f"<div class='d'>{t('ws_explain')}</div></div>", unsafe_allow_html=True)

        # 4. why did it appear? (rule points in plain words) + comparison with the other areas
        section(t("ws_why"))
        st.markdown("\n".join(f"- {w}" for w in _why_lines(z)))
        rank = ids.index(str(z["zone_id"])) + 1
        st.caption(t("cmp_top") if rank == 1 else t("cmp_rank", r=rank, n=len(ids)))
        weather_line(c)

        # 5. change over time (real images only)
        trend_block(c, z)

        # 6. possible causes (fertilisation never names a specific nutrient)
        section(t("causes_title"))
        st.caption(t("causes_note"))
        _cause_card("cz_water", ["cz_water_1", "cz_water_2", "cz_water_3", "cz_water_4"], causes["water"])
        _cause_card("cz_heat", ["cz_heat_1"], causes["heat"])
        _cause_card("cz_soil", ["cz_soil_1", "cz_soil_2", "cz_soil_3"])
        _cause_card("cz_salt", ["cz_salt_1"], source_id="fao_water_quality")
        _cause_card("cz_pest", ["cz_pest_1"], max(causes["disease"], causes["pest"], key=lambda r: r["score"]))
        _cause_card("cz_fert", ["cz_fert_1", "cz_fert_2"], causes["nutrient"])
        st.markdown(f"<div class='note-card'>ⓘ {t('yellow_many')}</div>", unsafe_allow_html=True)

    # 7. what to check, grouped (replaces the former flat checklist)
    section(t("q_check"))
    for grp, n in (("chk_sys", 5), ("chk_soil", 5), ("chk_plant", 5), ("chk_fert", 4)):
        with st.expander(t(grp), expanded=grp == "chk_sys"):
            for k in range(1, n + 1):
                st.checkbox(t(f"{grp}_{k}"), key=f"irr_{grp}_{k}")

    # 8. what do I do now?
    section(t("now_title"))
    st.markdown("\n".join(f"{i}. {t(f'now_{i}')}" for i in range(1, 8)))
    st.warning(t("irr_rule"))

    # 9. area priorities (existing priority list, now with high / medium labels)
    section(t("prio_title"))
    for r in prio.itertuples(index=False):
        st.button(f"{t('zone')} {r.zone_id}: {t('prio_high') if r.cls == 'HIGH' else t('prio_mid')}", on_click=go,
                  args=("zones", r.zone_id), width="stretch", key=f"b_irr_{r.zone_id}")
    st.markdown(f"<div class='muted'>{t('prio_ok', n=area_noun(n_h))}</div>", unsafe_allow_html=True)

    # existing context: crop water need, areas without crop
    crop_id = st.session_state.get("crop", "unknown")
    cr = knowledge.crop(crop_id)
    val = cr["water_requirement_ar"] if is_ar() else cr["water_requirement_mm"]
    if crop_id not in ("unknown", "other") and val:
        section(t("crop_water", crop=crop_name(crop_id)))
        st.markdown(f"<div class='card'>{val}</div>", unsafe_allow_html=True)
        st.caption(t("crop_water_note"))
    nc = list(c.scored.loc[c.scored.cls == "NO_CROP", "zone_id"])
    if nc:
        section(t("no_crop_title"))
        st.markdown(f"<div class='card'>⚪ {t('no_crop_text', zones='، '.join(nc))}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='card soft'>ⓘ {t('dss_goal')}</div>", unsafe_allow_html=True)


def page_about(c: Ctx) -> None:
    question(t("about_title"))
    st.markdown(f"<div class='card'>{t('about_text')}<br><br><b>{t('about_not')}</b></div>", unsafe_allow_html=True)
    section(t("how_title"))
    st.markdown("<div class='card soft'>" + "<br>".join(t(f"how_{i}") for i in range(1, 7)) + "</div>", unsafe_allow_html=True)
    section(t("not_title"))
    st.markdown("\n".join(f"- {t(f'not_{i}')}" for i in range(1, 4)))
    section(t("privacy_title"))
    st.markdown(f"<div class='card'>🔒 {t('privacy_text')}</div>", unsafe_allow_html=True)


RENDER = {"home": page_home, "map": page_map, "zones": page_zones, "water": page_water, "log": page_log,
          "tech": page_tech, "about": page_about}


def nav_labels() -> dict:
    return {p: t(f"nav_{p}") for p in PAGES}


def render(c: Ctx) -> None:
    st.session_state.setdefault("fpage", "home")
    if st.session_state.fpage not in PAGES:
        st.session_state.fpage = "home"
    RENDER[st.session_state.fpage](c)
