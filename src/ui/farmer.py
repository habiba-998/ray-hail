"""Farmer interface – the only interface of RAY (Arabic, plain language, no technical terms).

Journey: Home (what needs attention?) → Map (where?) → Zones (likely cause? what to check?) → Plant check (photo →
preliminary suspicion) → Irrigation (decide after verifying) → Farm record → About.

All statuses come from the existing pipeline (`c.scored` from analysis.score_zones); causes from src/fusion.py;
crop facts from src/knowledge.py. Nothing technical (data sources, indices, algorithms, IDs) is shown here.
"""
from __future__ import annotations

import numpy as np
import streamlit as st

from .. import fusion, knowledge, ml
from ..config import CLASS_COLORS
from ..image_analysis import ANALYZER, prepare_for_storage
from .common import (Ctx, anomaly_watch, finite, fmt, priority_zones, render_farm_map, synced_control,
                     synced_select, zone_row)
from .i18n import count_areas, is_ar, ltr, t, tr

ICON = {"HIGH": "‼", "MODERATE": "!", "HEALTHY": "✓", "NO_CROP": "–", "NO_DATA": "?"}
EMOJI = {"HIGH": "🔴", "MODERATE": "🟡", "HEALTHY": "🟢", "NO_CROP": "⚪", "NO_DATA": "⚫"}
TEXT_COLOR = {"HIGH": "#A12F2B", "MODERATE": "#7A5600", "HEALTHY": "#1E5B38", "NO_CROP": "#5E6E66", "NO_DATA": "#5E6E66"}
PAGES = ["home", "map", "zones", "plant", "water", "log", "about"]
ACTIONS = ["act_none", "act_fix", "act_water", "act_treat", "act_expert", "act_other"]


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
    st.markdown(
        f"<div class='zone-card' style='border-inline-start-color:{CLASS_COLORS[cls]}'>"
        f"<div class='z'>📍 {t('zone')} {z['zone_id']}</div>"
        f"<div class='s' style='color:{TEXT_COLOR[cls]}'>{EMOJI[cls]} {cls_label(cls)}</div>"
        f"<div class='d'>{t('why_' + cls)}</div>"
        f"<div class='d'><b>➜ {t('do_' + cls)}</b></div>{extra}</div>",
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
    n_r, n_m, n_h = counts.get("HIGH", 0), counts.get("MODERATE", 0), counts.get("HEALTHY", 0)
    st.markdown(
        f"<div class='card'><div class='section-title' style='margin-top:0'>{t('today_status')}</div>"
        f"<div class='status-line'>🔴 {count_areas(n_r, 'check')}</div>"
        f"<div class='status-line'>🟡 {count_areas(n_m, 'watch')}</div>"
        f"<div class='status-line'>🟢 {count_areas(n_h, 'ok')}</div>"
        f"<div class='muted' style='margin-top:6px'>{t('farm')}: {c.farm_name}</div></div>",
        unsafe_allow_html=True,
    )
    prio = priority_zones(c)
    st.write("")
    if len(prio):
        top = prio.iloc[0].to_dict()
        st.button(t("btn_top"), on_click=go, args=("zones", top["zone_id"]), type="primary", width="stretch", key="b_prio")
        section(t("top_zone"))
        zone_card(top)
        others = list(prio.iloc[1:].zone_id)
        if others:
            st.caption(t("others_watch", z="، ".join(others)))
    else:
        st.markdown(f"<div class='card soft'>✓ {t('no_priority')}</div>", unsafe_allow_html=True)
    for w in anomaly_watch(c, ml.IF_CONTAMINATION).itertuples(index=False):
        st.markdown(f"<div class='note-card'>🔎 {t('anomaly_note', z=w.zone_id)}</div>", unsafe_allow_html=True)

    section(t("crop"))
    synced_select(t("crop"), [cc["id"] for cc in knowledge.crops()], "crop", crop_label, label_visibility="collapsed")
    st.write("")
    b1, b2 = st.columns(2)
    b1.button(t("btn_map"), on_click=go, args=("map",), width="stretch", key="b_map")
    b2.button(t("btn_photo"), on_click=go, args=("plant",), width="stretch", key="b_photo")


def page_map(c: Ctx) -> None:
    question(t("q_map"))
    st.session_state.setdefault("fmap_view", "status")
    view = synced_control("map view", ["status", "photo"], "fmap_view", lambda v: t(f"view_{v}"))
    st.markdown("<div class='legend-big'>" + "".join(
        f"<span><span class='sw' style='background:{CLASS_COLORS[k]}'></span>{ICON[k]} {cls_label(k)}</span>"
        for k in ("HEALTHY", "MODERATE", "HIGH", "NO_CROP")) + "</div>", unsafe_allow_html=True)
    labels = {z: f"{z} {ICON[cl]}" for z, cl in zip(c.scored.zone_id, c.scored.cls)}
    mcol, pcol = st.columns([2, 1])
    with mcol:
        render_farm_map(c, "True Color", f"farmer_map_{view}", zone_fill=0.38 if view == "status" else 0.0, height=460,
                        labels=labels, label_px=15, short_attribution=True, basemap_attr="© Esri",
                        class_labels={k: cls_label(k) for k in CLASS_COLORS},
                        tooltip_aliases=(t("zone"), t("status"), t("priority_score") + " %"))
        st.caption("👆 " + t("map_help"))
    with pcol:
        z = choose_zone(c)
        zone_card(z)
        st.button(t("view_details"), on_click=go, args=("zones",), type="primary", width="stretch", key="b_details")
    st.caption("ⓘ " + t("sky_ground"))


def page_zones(c: Ctx) -> None:
    z = choose_zone(c)
    zone_card(z)
    if z["cls"] not in ("NO_CROP", "NO_DATA"):
        question(t("q_cause"))
        last = _last_observation(c, z["zone_id"])
        extra = {"symptoms": last.get("symptoms"), "soil": last.get("soil_condition"), "spread": last.get("spread")} if last else {}
        cause_rows(zone_causes(c, z, **extra), limit=3)
        st.markdown(f"<div class='note-card'>ⓘ {t('prelim')}</div>", unsafe_allow_html=True)
        weather_line(c)
        section(t("q_check"))
        checklist([t(f"check_{i}") for i in range(1, 6)])
        st.warning(t("irr_rule"))
    st.button(t("btn_photo_zone"), on_click=go, args=("plant",), type="primary", width="stretch", key="b_zone_photo")

    crop_id = st.session_state.get("crop", "unknown")
    probs = knowledge.problems_for(crop_id)
    section(t("common_problems", crop=crop_name(crop_id)) if probs else t("crop"))
    if probs:
        for p in probs:
            problem_details(p)
    else:
        st.caption(t("pick_crop"))


def _last_observation(c: Ctx, zone_id: str) -> dict | None:
    try:
        rows = c.store.list_observations(c.session_id, zone_id=zone_id, limit=1)
    except Exception:  # noqa: BLE001
        return None
    return rows[0] if rows else None


def page_plant(c: Ctx) -> None:
    question(t("plant_title"))
    section(t("step_where"))
    st.markdown(f"<div class='muted'>{t('farm')}: {c.farm_name}</div>", unsafe_allow_html=True)
    w1, w2 = st.columns(2)
    with w1:
        z = choose_zone(c, t("zone"))
    with w2:
        crop_id = synced_select(t("crop"), [cc["id"] for cc in knowledge.crops()], "crop", crop_label)

    section(t("step_photo"))
    up = st.file_uploader(t("upload"), type=["jpg", "jpeg", "png", "webp"], key="plant_photo")
    photo = up.getvalue() if up else None
    if photo:
        st.image(photo, width=300)

    section(t("step_see"))
    vocab = knowledge.symptom_vocabulary()
    crop_tags = {tag for p in knowledge.problems_for(crop_id) for tag in p["visual_tags"]}
    base = ["yellowing", "leaf_spots", "wilting", "insects_visible"]
    tags = base + sorted(crop_tags - set(base)) if crop_tags else list(vocab)
    cols = st.columns(2)
    chosen = [tag for i, tag in enumerate(tags) if cols[i % 2].checkbox(vocab[tag]["ar"] if is_ar() else vocab[tag]["en"], key=f"sym_{tag}")]
    soil_l = {v: t(f"soil_{v}") for v in ("dry", "wet", "normal", "unknown")}
    spread_l = {v: t(f"spread_{v}") for v in ("one", "many", "unknown")}
    soil = st.radio(t("soil_q"), list(soil_l), format_func=soil_l.get, horizontal=True, index=3, key="soil")
    spread = st.radio(t("spread_q"), list(spread_l), format_func=spread_l.get, horizontal=True, index=2, key="spread")

    if st.button(t("btn_analyze"), type="primary", width="stretch", key="b_analyze"):
        if not photo and not chosen and soil == "unknown" and spread == "unknown":
            st.warning(t("need_input"))
        else:
            screening = ANALYZER.analyze(photo) if photo else None
            causes = zone_causes(c, z, symptoms=chosen, soil=soil if soil in ("dry", "wet") else None,
                                 spread=spread if spread in ("one", "many") else None, photo=screening)
            st.session_state.plant_result = {
                "zone": z["zone_id"], "crop": crop_id, "symptoms": chosen, "soil": soil, "spread": spread,
                "screening": screening, "causes": causes, "specific": fusion.specific_suspicions(crop_id, chosen),
                "photo": photo, "saved_id": None,
            }
    res = st.session_state.get("plant_result")
    if res and res["zone"] == z["zone_id"]:
        _plant_result(c, z, res)


def _plant_result(c: Ctx, z: dict, res: dict) -> None:
    section(t("step_result"))
    sc = res["screening"]
    if sc is not None:
        if sc.get("ok"):
            a, b = st.columns([1, 1.4])
            a.image(sc["overlay"], width=240, caption=tr("Yellow and brown areas highlighted", "تظليل المناطق الصفراء والبنية"))
            b.markdown(t("photo_colors", g=round(sc["green_share"] * 100), y=round(sc["yellow_share"] * 100), b=round(sc["brown_share"] * 100)))
            b.caption("ⓘ " + t("photo_method"))
        else:
            st.warning(t(f"photo_quality_{sc['reason']}"))

    vocab = knowledge.symptom_vocabulary()
    spec = res["specific"]
    top_cause = next((r for r in res["causes"] if r["score"] >= 3), None)
    if spec:
        m, p = spec[0], spec[0]["problem"]
        words = "، ".join(vocab[x]["ar"] if is_ar() else vocab[x]["en"] for x in m["matches"])
        st.markdown(
            f"<div class='zone-card' style='border-inline-start-color:#2F7D4E'>"
            f"<div class='s'>{t('first_suspicion')}: {p['group_ar'] if is_ar() else p['group_en']}</div>"
            f"<div class='d'>{t('may_match')}: <b>{p['name_ar'] if is_ar() else p['name_en']}</b></div>"
            f"<div class='d'>{level_badge(m['level'], m['level_ar'])}</div>"
            f"<div class='d'>{t('matching_symptoms')}: {words}</div></div>", unsafe_allow_html=True)
        problem_details(p)
    elif top_cause:
        st.markdown(
            f"<div class='zone-card' style='border-inline-start-color:#2F7D4E'>"
            f"<div class='s'>{t('first_suspicion')}: {top_cause['icon']} {top_cause['ar'] if is_ar() else top_cause['en']}</div>"
            f"<div class='d'>{level_badge(top_cause['level'], top_cause['level_ar'])}</div></div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='card soft'>{t('insufficient')}</div>", unsafe_allow_html=True)

    if "yellowing" in res["symptoms"] or (sc and "photo_yellow" in (sc.get("signals") or [])):
        st.markdown(f"<div class='note-card'>ⓘ {t('yellowing_note')}</div>", unsafe_allow_html=True)

    others = [r for r in res["causes"] if r["score"] > 0 and r is not top_cause]
    if others or len(spec) > 1:
        section(t("other_possibilities"))
        cause_rows(others, limit=3)
        for m in spec[1:3]:
            st.caption(f"{t('may_match')}: {m['problem']['name_ar'] if is_ar() else m['problem']['name_en']} ({m['level_ar'] if is_ar() else m['level']})")

    section(t("q_check"))
    steps = [t(f"plant_check_{i}") for i in range(1, 6)]
    if spec:
        steps += (spec[0]["problem"]["inspection_ar"] if is_ar() else spec[0]["problem"]["inspection_en"])[:2]
    checklist(list(dict.fromkeys(steps)))
    st.info(t("final_note"))

    if not res["saved_id"]:
        if st.button(t("btn_save"), width="stretch", key="b_save_obs"):
            _save_observation(c, z, res)
    else:
        st.success(t("saved"))
        st.caption(c.store.persistent_note_ar if is_ar() else c.store.persistent_note_en)
        _validation_form(c, res["saved_id"], res["crop"], res.get("top_cause"), key=f"val_{res['saved_id']}")


def _save_observation(c: Ctx, z: dict, res: dict) -> None:
    sc, spec = res["screening"], res["specific"]
    rec = {
        "session_id": c.session_id, "farm_id": c.farm_id, "farm_name": c.farm_name,
        "data_mode": "real" if c.use_ee else "demo", "zone_id": z["zone_id"], "crop_id": res["crop"],
        "satellite_date": c.date, "satellite_class": z["cls"], "satellite_score": z["score"] if finite(z["score"]) else None,
        "lat": (z["min_lat"] + z["max_lat"]) / 2, "lon": (z["min_lon"] + z["max_lon"]) / 2,
        "symptoms": res["symptoms"], "soil_condition": res["soil"], "spread": res["spread"],
        "photo_screening": {k: v for k, v in sc.items() if k != "overlay"} if sc else None,
        "possible_causes": [{"cause": r["cause"], "score": r["score"], "level": r["level"]} for r in res["causes"]],
        "candidate_problems": [{"id": m["problem"]["id"], "level": m["level"], "matches": m["matches"]} for m in spec[:3]],
        "notes": None,
    }
    try:
        jpeg = prepare_for_storage(res["photo"]) if res["photo"] and sc and sc.get("reason") != "unreadable" else None
        res["saved_id"] = c.store.save_observation(rec, jpeg)
        res["top_cause"] = res["causes"][0]["cause"] if res["causes"] and res["causes"][0]["score"] > 0 else None
        st.session_state.plant_result = res
        st.rerun()
    except Exception:  # noqa: BLE001
        st.error(t("save_failed"))


def _validation_form(c: Ctx, obs_id: str, crop_id: str, prediction: str | None, key: str) -> None:
    section(t("validate_title"))
    st.caption(t("validate_note"))
    with st.form(key):
        fc_l = {"soil_dry": t("fc_dry"), "soil_not_dry": t("fc_not_dry"), "not_checked": t("fc_none")}
        fc = st.radio(t("field_check"), list(fc_l), format_func=fc_l.get, horizontal=True, index=2)
        cause_l = {k: f"{v['icon']} " + (v["ar"] if is_ar() else v["en"]) for k, v in fusion.CAUSES.items()}
        cause_l.update({"none": t("cause_none"), "unknown": t("cause_unknown")})
        cause = st.selectbox(t("actual_cause"), list(cause_l), index=len(cause_l) - 1, format_func=cause_l.get)
        prob_l = {"": "—", **{p["id"]: (p["name_ar"] if is_ar() else p["name_en"]) for p in knowledge.problems_for(crop_id)}}
        pid = st.selectbox(t("actual_problem"), list(prob_l), format_func=prob_l.get) or None
        act_l = {a: t(a) for a in ACTIONS}
        action = st.selectbox(t("action"), list(act_l), format_func=act_l.get)
        notes = st.text_area(t("notes"), max_chars=500)
        if st.form_submit_button(t("btn_save_validation"), type="primary"):
            try:
                c.store.save_validation({"session_id": c.session_id, "observation_id": obs_id, "ray_prediction": prediction,
                                         "field_check": fc, "actual_cause": cause, "actual_problem_id": pid,
                                         "action_taken": action, "notes": notes or None})
                st.success(t("validation_saved"))
            except Exception:  # noqa: BLE001
                st.error(t("save_failed"))


def page_log(c: Ctx) -> None:
    question(t("log_title"))
    st.caption(t("log_session_note"))
    try:
        rows = c.store.list_observations(c.session_id, limit=30)
        vals = {v["observation_id"]: v for v in c.store.list_validations([r["id"] for r in rows])}
    except Exception:  # noqa: BLE001
        rows, vals = [], {}
    if not rows:
        st.markdown(f"<div class='card soft'>{t('log_empty')}</div>", unsafe_allow_html=True)
        st.button(t("btn_photo"), on_click=go, args=("plant",), key="b_log_photo")
        return
    vocab = knowledge.symptom_vocabulary()
    for r in rows:
        v = vals.get(r["id"])
        state = "✅ " + t("log_validated") if v else "⏳ " + t("log_pending")
        with st.expander(f"📍 {t('zone')} {r['zone_id']} · {crop_name(r.get('crop_id') or 'unknown')} · {str(r['created_at'])[:10]} · {state}"):
            st.markdown(f"**{t('farm')}:** {r.get('farm_name') or '—'}")
            img = None
            try:
                img = c.store.get_image(r.get("photo_path"))
            except Exception:  # noqa: BLE001
                pass
            if img:
                st.image(img, width=260, caption=t("log_photo"))
            sym = r.get("symptoms") or []
            if sym:
                st.markdown(f"**{t('log_symptoms')}:** " + "، ".join(vocab[s]["ar"] if is_ar() else vocab[s]["en"] for s in sym if s in vocab))
            cands = r.get("candidate_problems") or []
            first = cands[0] if cands and isinstance(cands[0], dict) else None
            top = next((x for x in (r.get("possible_causes") or []) if x.get("score", 0) > 0), None)
            if first and knowledge.problem(first["id"]):
                p = knowledge.problem(first["id"])
                result = f"{p['group_ar'] if is_ar() else p['group_en']} — {t('may_match')}: {p['name_ar'] if is_ar() else p['name_en']}"
            elif top:
                cz = fusion.CAUSES[top["cause"]]
                result = f"{cz['icon']} {cz['ar'] if is_ar() else cz['en']}"
            else:
                result = t("insufficient")
            st.markdown(f"**{t('log_result')}:** {result}")
            if v:
                cause = fusion.CAUSES.get(v.get("actual_cause"), {})
                act = v.get("action_taken")
                st.markdown(f"**{t('actual_cause')}:** {(cause.get('ar') if is_ar() else cause.get('en')) or t('cause_none' if v.get('actual_cause') == 'none' else 'cause_unknown')}")
                if act in ACTIONS:
                    st.markdown(f"**{t('action')}:** {t(act)}")
                if v.get("notes"):
                    st.markdown(f"**{t('notes')}:** {v['notes']}")
            else:
                _validation_form(c, r["id"], r.get("crop_id") or "unknown", top["cause"] if top else None, key=f"logval_{r['id']}")


def page_water(c: Ctx) -> None:
    question(t("irr_title"))
    st.markdown(f"<div class='card soft'>ⓘ {t('irr_dss')}</div>", unsafe_allow_html=True)
    section(t("irr_list"))
    for k in range(1, 7):
        st.checkbox(t(f"irr_check_{k}"), key=f"irr_{k}")
    st.warning(t("irr_rule"))
    section(t("irr_zones"))
    prio = priority_zones(c)
    if len(prio):
        for r in prio.itertuples(index=False):
            st.button(f"{EMOJI[r.cls]} {t('zone')} {r.zone_id} — {cls_label(r.cls)}", on_click=go, args=("zones", r.zone_id),
                      width="stretch", key=f"b_irr_{r.zone_id}")
    else:
        st.markdown(f"<div class='card soft'>✓ {t('irr_none')}</div>", unsafe_allow_html=True)
    weather_line(c)
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


def page_about(c: Ctx) -> None:
    question(t("about_title"))
    st.markdown(f"<div class='card'>{t('about_text')}<br><br><b>{t('about_not')}</b></div>", unsafe_allow_html=True)
    section(t("how_title"))
    st.markdown("<div class='card soft'>" + "<br>".join(t(f"how_{i}") for i in range(1, 7)) + "</div>", unsafe_allow_html=True)
    section(t("not_title"))
    st.markdown("\n".join(f"- {t(f'not_{i}')}" for i in range(1, 4)))
    section(t("privacy_title"))
    st.markdown(f"<div class='card'>🔒 {t('privacy_text')}</div>", unsafe_allow_html=True)


RENDER = {"home": page_home, "map": page_map, "zones": page_zones, "plant": page_plant,
          "water": page_water, "log": page_log, "about": page_about}


def nav_labels() -> dict:
    return {p: t(f"nav_{p}") for p in PAGES}


def render(c: Ctx) -> None:
    st.session_state.setdefault("fpage", "home")
    if st.session_state.fpage not in PAGES:
        st.session_state.fpage = "home"
    RENDER[st.session_state.fpage](c)
