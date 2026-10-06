"""Farmer mode – Arabic first, one screen → one decision.

Home ("What needs my attention today?") → Map ("Where?") → Zones ("What could the cause be?") →
Plant check ("What do I photograph / check?") → Irrigation ("What is the better decision?") → About.

Nothing here computes a new satellite classification: statuses, scores and colours come from `c.scored`
(analysis.score_zones); possible causes come from src/fusion.py; crop facts from src/knowledge.py.
"""
from __future__ import annotations

import datetime as dt

import numpy as np
import streamlit as st

from .. import analysis, fusion, knowledge, ml
from ..config import CLASS_COLORS
from ..image_analysis import ANALYZER, prepare_for_storage
from .common import (LIMITATIONS, Ctx, anomaly_watch, ee_s1, finite, fmt, priority_zones, render_farm_map,
                     synced_control, synced_select, zone_row)
from .i18n import is_ar, ltr, t, tr

ICON = {"HIGH": "‼", "MODERATE": "!", "HEALTHY": "✓", "NO_CROP": "–", "NO_DATA": "?"}
EMOJI = {"HIGH": "🔴", "MODERATE": "🟡", "HEALTHY": "🟢", "NO_CROP": "⚪", "NO_DATA": "⚫"}
STATUS_TEXT_COLOR = {"HIGH": "#A12F2B", "MODERATE": "#7A5600", "HEALTHY": "#1E5B38", "NO_CROP": "#5E6E66", "NO_DATA": "#5E6E66"}
FARM_STATUS = {"RED": ("status_RED", "HIGH"), "YELLOW": ("status_YELLOW", "MODERATE"),
               "GREEN": ("status_GREEN", "HEALTHY"), "NONE": ("status_NONE", "NO_CROP")}
PAGES = ["home", "map", "zones", "plant", "water", "about"]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def go(page: str, zone: str | None = None) -> None:
    st.session_state.fpage = page
    if zone:
        st.session_state.zone_sel = zone


def go_tech() -> None:
    st.session_state.mode = "tech"


def cls_label(cls: str) -> str:
    return t(f"cls_{cls}")


def zone_label(z: str, cls: str) -> str:
    return f"{EMOJI[cls]} {t('zone')} {z} — {cls_label(cls)}"


def crop_label(cid: str) -> str:
    c = knowledge.crop(cid)
    return f"{c['icon']} {c['name_ar'] if is_ar() else c['name_en']}"


def pill(cls: str, text: str | None = None) -> str:
    bg = {"HIGH": "#FDE7E6", "MODERATE": "#FFF3D6", "HEALTHY": "#E5F3EA", "NO_CROP": "#F2F4F3", "NO_DATA": "#F2F4F3"}[cls]
    return (f"<span class='pill' style='background:{bg};color:{STATUS_TEXT_COLOR[cls]}'>"
            f"{EMOJI[cls]} {text or cls_label(cls)}</span>")


def section(title: str) -> None:
    st.markdown(f"<div class='section-title'>{title}</div>", unsafe_allow_html=True)


def farm_status(c: Ctx) -> str:
    counts = c.scored.cls.value_counts()
    if counts.get("HIGH", 0):
        return "RED"
    if counts.get("MODERATE", 0):
        return "YELLOW"
    return "GREEN" if counts.get("HEALTHY", 0) else "NONE"


def score_text(z: dict) -> str:
    return ltr(f"{fmt(z['score'] * 100, 0, '%')} ({z['points']}/{z['max_points']})") if finite(z["score"]) else "—"


def src_link(source_id: str | None) -> str:
    s = knowledge.source(source_id)
    return f"[{s['publisher']}]({s['url']})" if s else knowledge.unavailable(is_ar())


def zone_card(z: dict, extra: str = "") -> None:
    cls = z["cls"]
    st.markdown(
        f"<div class='zone-card' style='border-inline-start-color:{CLASS_COLORS[cls]}'>"
        f"<div class='z'>📍 {t('zone')} {z['zone_id']}</div>"
        f"<div class='s' style='color:{STATUS_TEXT_COLOR[cls]}'>{EMOJI[cls]} {cls_label(cls)}</div>"
        f"<div class='d'>{t('sub_' + cls)}</div>"
        f"<div class='d'>➜ {t('do_' + cls)}</div>{extra}</div>",
        unsafe_allow_html=True,
    )


def causes_block(causes: list[dict], top_n: int | None = None) -> None:
    rows = causes[:top_n] if top_n else causes
    for r in rows:
        st.markdown(
            f"<div class='cause'><span class='ic'>{r['icon']}</span><span class='nm'>{r['ar'] if is_ar() else r['en']}</span>"
            f"<span class='lvl {r['level']}'>{(r['level_ar'] if is_ar() else ('No evidence yet' if r['level'] == 'none' else r['level'].capitalize()))}</span></div>",
            unsafe_allow_html=True,
        )
        if r["reasons"]:
            with st.expander(f"{t('why_reasons')} — {r['ar'] if is_ar() else r['en']}"):
                for reason in r["reasons"]:
                    st.markdown(f"- {fusion.reason_text(reason, is_ar())}")
    st.caption("ⓘ " + t("why_note"))


def problem_details(p: dict) -> None:
    """Expandable crop problem with sourced symptoms, inspection steps and (lazy) licensed reference image."""
    name = p["name_ar"] if is_ar() else p["name_en"]
    icon = "🦠" if p["type"] == "disease" else "🐛"
    with st.expander(f"{icon} {name}"):
        st.markdown(f"**{t('symptoms')}:** {p['symptoms_ar'] if is_ar() else p['symptoms_en']}")
        steps = p["inspection_ar"] if is_ar() else p["inspection_en"]
        st.markdown(f"**{t('what_check')}:**\n" + "\n".join(f"- {s}" for s in steps))
        cond = p.get("conditions_ar") if is_ar() else p.get("conditions_en")
        if cond:
            st.caption(cond)
        imgs = knowledge.images_for(p)
        if imgs:
            im = imgs[0]
            st.image(im["image_url"], width=320)
            st.caption(t("img_credit", a=im["author"] or "—", lic=im["license"], src=f"Wikimedia Commons") + f" · [{tr('page', 'الصفحة')}]({im['source_page']})")
        else:
            st.caption(t("no_ref_image"))
        st.caption(f"{t('source')}: {src_link(p['source'])} · {p['scientific_name']}")


def weather_line(c: Ctx) -> None:
    w = c.wx_summary
    if not w:
        st.caption("🌦️ " + (t("weather_none") if c.use_ee else tr("Weather: not available in demo mode.", "الطقس: غير متوفر في الوضع التجريبي.")))
        return
    rh = fmt(w["rh_mean"], 0, "%") if finite(w["rh_mean"]) else "—"
    st.markdown(f"<div class='muted'>🌦️ {t('weather_line', t=w['tmax_mean'], rh=ltr(rh), p=w['precip_sum'])}</div>", unsafe_allow_html=True)
    st.caption(t("weather_src", src=w["source"].split(" (")[0], d=ltr(w["last_date"])), unsafe_allow_html=True)


def zone_causes(c: Ctx, z: dict, **extra) -> list[dict]:
    return fusion.possible_causes(z, weather=c.wx_summary, anomaly_share=z.get("anomaly_share"),
                                  contamination=ml.IF_CONTAMINATION, **extra)


# ---------------------------------------------------------------------------
# pages
# ---------------------------------------------------------------------------
def page_home(c: Ctx) -> None:
    st.markdown(f"<div class='q'>{t('today_q')}</div>", unsafe_allow_html=True)
    counts = c.scored.cls.value_counts()
    n_r, n_m, n_h = counts.get("HIGH", 0), counts.get("MODERATE", 0), counts.get("HEALTHY", 0)
    key, cls = FARM_STATUS[farm_status(c)]
    st.markdown(
        f"<div class='status-hero'><div class='dot' style='background:{CLASS_COLORS[cls]}'>{ICON[cls]}</div>"
        f"<div><h2>{t(key)}</h2><div class='sub'>{t('your_farm')}: {c.farm_name} · {ltr(c.date)}</div></div></div>"
        f"<div class='tiles'>"
        f"<div class='tile'><div class='n' style='color:#1E5B38'>🟢 {n_h}</div><div class='l'>{t('tile_ok')}</div></div>"
        f"<div class='tile'><div class='n' style='color:#7A5600'>🟡 {n_m}</div><div class='l'>{t('tile_watch')}</div></div>"
        f"<div class='tile'><div class='n' style='color:#A12F2B'>🔴 {n_r}</div><div class='l'>{t('tile_check')}</div></div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    section(t("top_zone"))
    prio = priority_zones(c)
    if len(prio):
        z = prio.iloc[0].to_dict()
        zone_card(z, f"<div class='n'>ⓘ {t('screening_note')}</div>")
        st.button(t("btn_inspect"), on_click=go, args=("zones", z["zone_id"]), type="primary", width="stretch", key="b_prio")
        others = list(prio.iloc[1:].zone_id)
        if others:
            st.caption(t("others_watch", z="، ".join(others) if is_ar() else ", ".join(others)))
    else:
        st.markdown(f"<div class='card soft'>✓ {t('no_priority')}</div>", unsafe_allow_html=True)
    for w in anomaly_watch(c, ml.IF_CONTAMINATION).itertuples(index=False):
        st.markdown(f"<div class='note-card'>🔎 <b>{t('also_look')}:</b> {t('anomaly_note', z=w.zone_id)}</div>",
                    unsafe_allow_html=True)

    section(t("crop"))
    synced_select(t("crop"), [cc["id"] for cc in knowledge.crops()], "crop", crop_label, label_visibility="collapsed")

    st.write("")
    b1, b2 = st.columns(2)
    b1.button(t("btn_map"), on_click=go, args=("map",), width="stretch", key="b_map")
    b2.button(t("btn_photo"), on_click=go, args=("plant",), width="stretch", key="b_photo")
    st.button(t("btn_tech"), on_click=go_tech, width="stretch", key="b_tech")


def page_map(c: Ctx) -> None:
    st.markdown(f"<div class='q'>{tr('Where is the problem?', 'وين المشكلة؟')}</div>", unsafe_allow_html=True)
    st.session_state.setdefault("fmap_view", "status")
    view = synced_control("map view", ["status", "photo"], "fmap_view", lambda v: t(f"view_{v}"))
    st.markdown("<div class='legend-big'>" + "".join(
        f"<span><span class='sw' style='background:{CLASS_COLORS[k]}'></span>{ICON[k]} {cls_label(k)}</span>"
        for k in ("HEALTHY", "MODERATE", "HIGH", "NO_CROP")) + "</div>", unsafe_allow_html=True)
    labels = {z: f"{z} {ICON[cl]}" for z, cl in zip(c.scored.zone_id, c.scored.cls)}
    mcol, pcol = st.columns([2, 1])
    with mcol:
        render_farm_map(c, "True Color", f"farmer_map_{view}", zone_fill=0.38 if view == "status" else 0.0, height=460,
                        labels=labels, label_px=15, short_attribution=True,
                        class_labels={k: cls_label(k) for k in CLASS_COLORS},
                        tooltip_aliases=(t("zone"), t("status"), t("score") + " %"))
        st.caption("👆 " + t("map_help") + ("  ·  ⚠️ DEMO DATA" if not c.use_ee else ""))
    with pcol:
        ids = list(c.scored.zone_id)
        synced_select(t("choose_area"), ids, "zone_sel", lambda z: zone_label(z, zone_row(c, z)["cls"]))
        z = zone_row(c, st.session_state.zone_sel)
        zone_card(z)
        st.button(t("view_details"), on_click=go, args=("zones",), type="primary", width="stretch", key="b_details")


def page_zones(c: Ctx) -> None:
    ids = list(c.scored.zone_id)
    prio = list(priority_zones(c).zone_id)
    order = prio + [z for z in ids if z not in prio]
    synced_select(t("choose_area"), order, "zone_sel", lambda z: zone_label(z, zone_row(c, z)["cls"]))
    z = zone_row(c, st.session_state.zone_sel)
    zone_card(z)

    if z["cls"] not in ("NO_CROP", "NO_DATA"):
        st.markdown(f"<div class='q' style='margin-top:16px'>{t('why_q')}</div>", unsafe_allow_html=True)
        last = _last_observation(c, z["zone_id"])
        extra = {"symptoms": last.get("symptoms"), "soil": last.get("soil_condition"), "spread": last.get("spread")} if last else {}
        causes_block(zone_causes(c, z, **extra))
        if last:
            st.caption(tr("Includes your saved observation for this area.", "يشمل ملاحظتك المحفوظة لهذه المنطقة."))
        weather_line(c)

    st.button(t("photo_this"), on_click=go, args=("plant",), type="primary", width="stretch", key="b_zone_photo")

    crop_id = st.session_state.get("crop", "unknown")
    probs = knowledge.problems_for(crop_id)
    section(t("common_problems", crop=crop_label(crop_id)))
    if probs:
        for p in probs:
            problem_details(p)
    else:
        st.caption(t("pick_crop"))

    with st.expander(t("tech_expander")):
        m = st.columns(4)
        m[0].metric("NDVI", fmt(z["ndvi"]), None if not finite(z["dndvi"]) else fmt(z["dndvi"], 2, signed=True))
        m[1].metric("NDRE", fmt(z["ndre"]))
        m[2].metric("NDMI", fmt(z["ndmi"]))
        m[3].metric("LST", fmt(z["lst"], 1, " °C"), None if not finite(z["lst_anom"]) else fmt(z["lst_anom"], 1, " °C", signed=True),
                    delta_color="inverse")
        st.caption(f"{t('score')}: {score_text(z)}", unsafe_allow_html=True)
        st.dataframe(analysis.rule_table(z), hide_index=True)
        if c.use_ee:
            try:
                s1, meta = ee_s1(c.bounds, c.zones.to_dict("records"), c.date)
                row = s1[s1.zone_id == z["zone_id"]]
                if len(row):
                    r = row.iloc[0]
                    st.caption(f"Sentinel-1 ({meta['s1_date']}): VV {r.vv_db:.1f} dB · VH {r.vh_db:.1f} dB — "
                               + tr("context only, not used in scoring", "للسياق فقط ولا يدخل في التقييم"))
            except Exception:  # noqa: BLE001 -- optional context
                pass


def _last_observation(c: Ctx, zone_id: str) -> dict | None:
    try:
        rows = c.store.list_observations(c.session_id, zone_id=zone_id, limit=1)
    except Exception:  # noqa: BLE001
        return None
    return rows[0] if rows else None


def page_plant(c: Ctx) -> None:
    st.markdown(f"<div class='q'>📷 {t('plant_title')}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='step'>{t('step_where')}</div>", unsafe_allow_html=True)
    w1, w2 = st.columns(2)
    with w1:
        ids = list(c.scored.zone_id)
        synced_select(t("zone"), ids, "zone_sel", lambda z: zone_label(z, zone_row(c, z)["cls"]))
    with w2:
        crop_id = synced_select(t("crop"), [cc["id"] for cc in knowledge.crops()], "crop", crop_label)
    z = zone_row(c, st.session_state.zone_sel)

    st.markdown(f"<div class='step'>{t('step_photo')}</div>", unsafe_allow_html=True)
    up = st.file_uploader(t("upload"), type=["jpg", "jpeg", "png", "webp"], key="plant_photo")
    photo_bytes = up.getvalue() if up else None
    if photo_bytes:
        st.image(photo_bytes, width=320)

    st.markdown(f"<div class='step'>{t('step_see')}</div>", unsafe_allow_html=True)
    vocab = knowledge.symptom_vocabulary()
    crop_tags = {tag for p in knowledge.problems_for(crop_id) for tag in p["visual_tags"]}
    base = ["yellowing", "leaf_spots", "wilting", "insects_visible"]
    tags = base + sorted(crop_tags - set(base)) if crop_tags else list(vocab)
    cols = st.columns(2)
    chosen = [tag for i, tag in enumerate(tags)
              if cols[i % 2].checkbox(vocab[tag]["ar"] if is_ar() else vocab[tag]["en"], key=f"sym_{tag}")]
    soil_l = {v: t(f"soil_{v}") for v in ("dry", "wet", "normal", "unknown")}
    spread_l = {v: t(f"spread_{v}") for v in ("one", "many", "unknown")}
    soil = st.radio(t("soil_q"), list(soil_l), format_func=soil_l.get,
                    horizontal=True, index=3, key="soil")
    spread = st.radio(t("spread_q"), list(spread_l), format_func=spread_l.get,
                      horizontal=True, index=2, key="spread")

    if st.button(t("btn_analyze"), type="primary", width="stretch", key="b_analyze"):
        if not photo_bytes and not chosen and soil == "unknown" and spread == "unknown":
            st.warning(t("need_photo_or_symptom"))
        else:
            screening = ANALYZER.analyze(photo_bytes) if photo_bytes else None
            causes = zone_causes(c, z, symptoms=chosen, soil=None if soil in ("unknown", "normal") else soil,
                                 spread=None if spread == "unknown" else spread, photo=screening)
            st.session_state.plant_result = {
                "zone": z["zone_id"], "crop": crop_id, "symptoms": chosen, "soil": soil, "spread": spread,
                "screening": screening, "causes": causes, "matches": fusion.matching_problems(crop_id, chosen),
                "photo": photo_bytes, "saved_id": None,
            }

    res = st.session_state.get("plant_result")
    if res and res["zone"] == z["zone_id"]:
        _plant_result(c, z, res)
    _history(c)


def _plant_result(c: Ctx, z: dict, res: dict) -> None:
    st.markdown(f"<div class='step'>{t('step_result')}</div>", unsafe_allow_html=True)
    sc = res["screening"]
    if sc is not None:
        if sc.get("ok"):
            col1, col2 = st.columns([1, 1.4])
            col1.image(sc["overlay"], width=260, caption=tr("Yellow / brown tissue highlighted", "الأنسجة الصفراء/البنية مظللة"))
            col2.markdown(t("photo_colors", g=round(sc["green_share"] * 100), y=round(sc["yellow_share"] * 100), b=round(sc["brown_share"] * 100)))
            col2.caption("ⓘ " + t("photo_method"))
        else:
            st.warning(t(f"photo_quality_{sc['reason']}"))

    st.markdown(f"<div class='section-title'>{t('why_q')}</div>", unsafe_allow_html=True)
    causes_block(res["causes"])

    section(t("matches_title"))
    if res["matches"]:
        vocab = knowledge.symptom_vocabulary()
        for m in res["matches"][:3]:
            words = "، ".join(vocab[x]["ar"] for x in m["matches"]) if is_ar() else ", ".join(vocab[x]["en"] for x in m["matches"])
            st.caption(t("matched_on", m=words))
            problem_details(m["problem"])
    else:
        st.caption(t("pick_crop") if res["crop"] in ("unknown", "other") else t("matches_none"))

    section(t("check_title"))
    steps = [t(f"gen_check_{i}") for i in range(1, 5)]
    for m in res["matches"][:2]:
        steps += (m["problem"]["inspection_ar"] if is_ar() else m["problem"]["inspection_en"])[:2]
    st.markdown("<ul class='checklist'>" + "".join(f"<li>☐ {s}</li>" for s in dict.fromkeys(steps)) + "</ul>",
                unsafe_allow_html=True)
    st.info(t("advice"))

    if not res["saved_id"]:
        if st.button(t("btn_save"), width="stretch", key="b_save_obs"):
            _save_observation(c, z, res)
    if res["saved_id"]:
        st.success(t("saved", z=z["zone_id"], d=dt.date.today().isoformat()))
        st.caption(c.store.persistent_note_ar if is_ar() else c.store.persistent_note_en)
        _validation_form(c, res)


def _save_observation(c: Ctx, z: dict, res: dict) -> None:
    sc = res["screening"]
    rec = {
        "session_id": c.session_id, "farm_id": c.farm_id, "farm_name": c.farm_name,
        "data_mode": "real" if c.use_ee else "demo", "zone_id": z["zone_id"], "crop_id": res["crop"],
        "satellite_date": c.date, "satellite_class": z["cls"], "satellite_score": z["score"] if finite(z["score"]) else None,
        "lat": (z["min_lat"] + z["max_lat"]) / 2, "lon": (z["min_lon"] + z["max_lon"]) / 2,
        "symptoms": res["symptoms"], "soil_condition": res["soil"], "spread": res["spread"],
        "photo_screening": {k: v for k, v in sc.items() if k != "overlay"} if sc else None,
        "possible_causes": [{"cause": r["cause"], "score": r["score"], "level": r["level"]} for r in res["causes"]],
        "candidate_problems": [m["problem"]["id"] for m in res["matches"][:3]],
        "notes": None,
    }
    try:
        jpeg = prepare_for_storage(res["photo"]) if res["photo"] and sc and sc.get("reason") != "unreadable" else None
        res["saved_id"] = c.store.save_observation(rec, jpeg)
        res["top_cause"] = res["causes"][0]["cause"] if res["causes"] and res["causes"][0]["score"] > 0 else None
        st.session_state.plant_result = res
        st.rerun()
    except Exception as exc:  # noqa: BLE001
        st.error(t("save_failed", e=exc))


def _validation_form(c: Ctx, res: dict) -> None:
    section(t("validate_title"))
    st.caption(t("validate_note"))
    with st.form(f"val_{res['saved_id']}"):
        fc_l = {"soil_dry": t("fc_dry"), "soil_not_dry": t("fc_not_dry"), "not_checked": t("fc_none")}
        fc = st.radio(t("field_check"), list(fc_l), format_func=fc_l.get, horizontal=True, index=2)
        cause_l = {k: f"{v['icon']} " + (v["ar"] if is_ar() else v["en"]) for k, v in fusion.CAUSES.items()}
        cause_l.update({"none": t("cause_none"), "unknown": t("cause_unknown")})
        cause = st.selectbox(t("actual_cause"), list(cause_l), index=len(cause_l) - 1, format_func=cause_l.get)
        prob_l = {"": "—", **{p["id"]: (p["name_ar"] if is_ar() else p["name_en"]) for p in knowledge.problems_for(res["crop"])}}
        pid = st.selectbox(t("actual_problem"), list(prob_l), format_func=prob_l.get) or None
        notes = st.text_area(t("notes"), max_chars=500)
        if st.form_submit_button(t("btn_save_validation"), type="primary"):
            try:
                c.store.save_validation({"session_id": c.session_id, "observation_id": res["saved_id"],
                                         "ray_prediction": res.get("top_cause"), "field_check": fc, "actual_cause": cause,
                                         "actual_problem_id": pid, "notes": notes or None})
                st.success(t("validation_saved"))
            except Exception as exc:  # noqa: BLE001
                st.error(t("save_failed", e=exc))


def _history(c: Ctx) -> None:
    try:
        rows = c.store.list_observations(c.session_id, limit=10)
        vals = {v["observation_id"] for v in c.store.list_validations([r["id"] for r in rows])}
    except Exception:  # noqa: BLE001
        rows, vals = [], set()
    with st.expander(f"🗂️ {t('history')} ({len(rows)})"):
        if not rows:
            st.caption(t("history_empty"))
        for r in rows:
            top = (r.get("possible_causes") or [{}])[0]
            cause = fusion.CAUSES.get(top.get("cause"), {})
            st.markdown(f"- **{t('zone')} {r['zone_id']}** · {crop_label(r.get('crop_id') or 'unknown')} · "
                        f"{cause.get('icon', '')} {(cause.get('ar') if is_ar() else cause.get('en')) or '—'} · "
                        f"{'✅ ' + t('validated') if r['id'] in vals else '⏳ ' + t('not_validated')} · {ltr(str(r['created_at'])[:16])}",
                        unsafe_allow_html=True)


def page_water(c: Ctx) -> None:
    st.markdown(f"<div class='q'>{t('irr_title')}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='card soft'>ⓘ {t('irr_dss')}</div>", unsafe_allow_html=True)
    prio = priority_zones(c)
    if len(prio):
        for i, r in enumerate(prio.itertuples(index=False)):
            if i == 1:
                st.caption(tr("Other areas:", "مناطق أخرى:"))
            with st.expander(f"{EMOJI[r.cls]} {t('zone')} {r.zone_id} — {cls_label(r.cls)}", expanded=(i == 0)):
                for k in range(1, 6):
                    st.checkbox(t(f"irr_check_{k}"), key=f"irr_{r.zone_id}_{k}")
                st.markdown(f"**➜ {t('irr_rule')}**")
                st.button(t("btn_photo"), on_click=go, args=("plant", r.zone_id), key=f"b_irr_photo_{r.zone_id}")
    else:
        st.markdown(f"<div class='card soft'>✓ {t('irr_none')}</div>", unsafe_allow_html=True)

    section(tr("Weather", "الطقس"))
    weather_line(c)

    crop_id = st.session_state.get("crop", "unknown")
    cr = knowledge.crop(crop_id)
    if crop_id not in ("unknown", "other"):
        section(t("crop_water", crop=crop_label(crop_id)))
        val = cr["water_requirement_ar"] if is_ar() else cr["water_requirement_mm"]
        st.markdown(f"<div class='card'>{val or knowledge.unavailable(is_ar())}</div>", unsafe_allow_html=True)
        if val:
            st.caption(t("crop_water_note") + " · " + t("source") + ": " + src_link(cr["water_source"]))
        note = cr.get("ray_note_ar") if is_ar() else cr.get("ray_note")
        if note:
            st.caption("ⓘ " + note)

    nc = list(c.scored.loc[c.scored.cls == "NO_CROP", "zone_id"])
    if nc:
        section(t("no_crop_title"))
        st.markdown(f"<div class='card'>⚪ {t('no_crop_text', zones=', '.join(nc))}</div>", unsafe_allow_html=True)
    section(t("future_title"))
    st.caption(t("future_text"))


def page_about(c: Ctx) -> None:
    section(t("about_title"))
    st.markdown(f"<div class='card'>{t('about_text')}</div>", unsafe_allow_html=True)
    section(t("about_flow"))
    st.markdown(f"<div class='card soft'>{t('flow_steps')}</div>", unsafe_allow_html=True)
    section(t("how_status"))
    st.markdown(f"<div class='card'>{t('how_status_text')}</div>", unsafe_allow_html=True)
    section(t("data_title"))
    mode = (tr(f"This screen uses REAL satellite data (Google Earth Engine, image of {c.date}).",
               f"تستخدم هذه الشاشة بيانات أقمار صناعية حقيقية (Google Earth Engine، صورة بتاريخ {ltr(c.date)}).")
            if c.use_ee else tr("This screen uses DEMO DATA (simulated farm).", "تستخدم هذه الشاشة بيانات تجريبية (مزرعة محاكاة)."))
    st.markdown(
        "<div class='card'>"
        f"🛰️ Sentinel-2 — {tr('crop condition images every ~5 days', 'صور حالة المحصول كل ٥ أيام تقريبًا')}<br>"
        f"🌡️ Landsat 8/9 — {tr('surface temperature', 'حرارة السطح')}<br>"
        f"📡 Sentinel-1 — {tr('radar, works through clouds (context only)', 'رادار يعمل رغم الغيوم (للسياق فقط)')}<br>"
        f"🌦️ ERA5-Land — {tr('temperature, humidity, wind, rain', 'الحرارة والرطوبة والرياح والأمطار')}<br>"
        f"🏛️ {tr('National Center for Meteorology — not connected yet (licence required)', 'المركز الوطني للأرصاد — غير متصل حاليًا (يتطلب ترخيصًا)')}<br>"
        f"🌱 {tr('Crop, disease and pest information from FAO, University of California IPM and other cited sources', 'معلومات المحاصيل والأمراض والآفات من FAO وبرنامج المكافحة المتكاملة بجامعة كاليفورنيا ومصادر موثقة أخرى')}<br><br>"
        f"<b>{mode}</b></div>", unsafe_allow_html=True)
    section(t("privacy_title"))
    st.markdown(f"<div class='card'>🔒 {t('privacy_text')}</div>", unsafe_allow_html=True)
    section(t("storage_title"))
    st.caption(f"{c.store.name} — " + (c.store.persistent_note_ar if is_ar() else c.store.persistent_note_en))
    section(t("limits_title"))
    st.markdown("\n".join(f"- {a if is_ar() else e}" for e, a in LIMITATIONS))
    st.button(t("btn_tech"), on_click=go_tech, width="stretch", key="b_about_tech")


def render(c: Ctx) -> None:
    st.session_state.setdefault("fpage", "home")
    if st.session_state.fpage not in PAGES:
        st.session_state.fpage = "home"
    labels = {p: t(f"nav_{p}") for p in PAGES}
    page = synced_control("nav", PAGES, "fpage", labels.get)
    {"home": page_home, "map": page_map, "zones": page_zones, "plant": page_plant,
     "water": page_water, "about": page_about}[page](c)
