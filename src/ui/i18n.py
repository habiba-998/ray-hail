"""Farmer-facing text – Arabic first, English second.

Only wording lives here. Every status shown with these strings comes from the existing RAY classes
(HEALTHY / MODERATE / HIGH / NO_CROP / NO_DATA), the existing rule points, or src/fusion.py.
"""
from __future__ import annotations

import streamlit as st

S: dict[str, tuple[str, str]] = {
    # --- chrome -------------------------------------------------------------
    "subtitle": ("Satellite-powered decision support for your farm.", "نظام دعم قرار لمزرعتك بقوة الأقمار الصناعية."),
    "mode_farmer": ("👨‍🌾 Farmer", "👨‍🌾 المزارع"),
    "mode_tech": ("🔬 Technical", "🔬 فني"),
    "badge_real": ("🛰️ Real satellite data (Google Earth Engine) · image of {date}",
                   "🛰️ بيانات أقمار صناعية حقيقية (Google Earth Engine) · صورة بتاريخ {date}"),
    "badge_demo": ("⚠️ DEMO DATA — simulated farm, not real satellite observations",
                   "⚠️ بيانات تجريبية (DEMO DATA) — مزرعة محاكاة وليست رصدًا حقيقيًا"),
    "tech_lang_note": ("Technical analysis is presented in English.", "يُعرض التحليل الفني باللغة الإنجليزية."),
    # --- navigation ---------------------------------------------------------
    "nav_home": ("🏠 Home", "🏠 الرئيسية"),
    "nav_map": ("🗺️ Farm map", "🗺️ خريطة المزرعة"),
    "nav_zones": ("📍 Zones", "📍 المناطق"),
    "nav_plant": ("📷 Plant check", "📷 فحص النبات"),
    "nav_water": ("💧 Irrigation", "💧 الري"),
    "nav_about": ("ℹ️ About RAY", "ℹ️ عن رَيّ"),
    # --- home ---------------------------------------------------------------
    "today_q": ("What needs my attention today?", "وش يحتاج انتباهي اليوم؟"),
    "your_farm": ("Your farm", "مزرعتك"),
    "status_RED": ("An area needs inspection", "فيه منطقة تحتاج فحص"),
    "status_YELLOW": ("Some areas need follow-up", "بعض المناطق تحتاج متابعة"),
    "status_GREEN": ("Farm looks normal", "المزرعة تبدو طبيعية"),
    "status_NONE": ("No active crop to assess", "لا يوجد محصول نشط للتقييم"),
    "tile_ok": ("normal", "طبيعية"),
    "tile_watch": ("need follow-up", "تحتاج متابعة"),
    "tile_check": ("need inspection", "تحتاج فحص"),
    "top_zone": ("Most important area", "أهم منطقة"),
    "btn_inspect": ("🔍 Inspect this area", "🔍 افحص المنطقة"),
    "no_priority": ("No area needs inspection today. Keep your usual routine.",
                    "لا توجد منطقة تحتاج فحص اليوم. استمر في متابعتك المعتادة."),
    "screening_note": ("This is a satellite screening signal — not a confirmed diagnosis.",
                       "هذه إشارة من الأقمار الصناعية — وليست تشخيصًا مؤكدًا."),
    "btn_map": ("🗺️ Farm map", "🗺️ خريطة المزرعة"),
    "btn_photo": ("📷 Photograph a plant", "📷 صوّر النبات"),
    "btn_tech": ("🔬 Technical analysis", "🔬 التحليل الفني"),
    "also_look": ("Also worth a look", "تستحق نظرة أيضًا"),
    "anomaly_note": ("{z} is not flagged by the rules, but the AI found an unusual pattern there.",
                     "المنطقة {z} ليست ضمن المناطق المنبّه عليها، لكن الذكاء الاصطناعي رصد فيها نمطًا غير معتاد."),
    "crop": ("Crop", "المحصول"),
    "others_watch": ("Other areas to follow up: {z}", "مناطق أخرى للمتابعة: {z}"),
    # --- zone classes (farmer wording of the existing classes) --------------
    "cls_HIGH": ("Needs inspection", "تحتاج فحص"),
    "cls_MODERATE": ("Needs follow-up", "تحتاج متابعة"),
    "cls_HEALTHY": ("Normal", "طبيعية"),
    "cls_NO_CROP": ("No active crop", "لا يوجد محصول نشط"),
    "cls_NO_DATA": ("Not enough clear data", "لا توجد بيانات كافية"),
    "sub_HIGH": ("Possible unusual change", "تغير غير طبيعي محتمل"),
    "sub_MODERATE": ("Some signs are weaker than the rest of the farm", "بعض المؤشرات أضعف من بقية المزرعة"),
    "sub_HEALTHY": ("Similar to the healthy parts of the farm", "مشابهة للأجزاء السليمة من المزرعة"),
    "sub_NO_CROP": ("No green crop seen from space", "لا يظهر محصول أخضر من الفضاء"),
    "sub_NO_DATA": ("Clouds or missing image on this date", "غيوم أو صورة ناقصة في هذا التاريخ"),
    "do_HIGH": ("Inspect this area in the field before changing irrigation.",
                "يفضّل فحص المنطقة ميدانيًا قبل تغيير الري."),
    "do_MODERATE": ("Check this area on your next field visit.", "افحص المنطقة في زيارتك القادمة للحقل."),
    "do_HEALTHY": ("No action needed. Keep monitoring.", "لا حاجة لأي إجراء. استمر في المتابعة."),
    "do_NO_CROP": ("If this area is still irrigated, check whether that water is needed.",
                   "إذا كانت هذه المنطقة تُروى، تحقّق هل تحتاج فعلًا لهذه المياه."),
    "do_NO_DATA": ("Choose another date or wait for the next satellite image.", "اختر تاريخًا آخر أو انتظر صورة القمر الصناعي القادمة."),
    # --- map ------------------------------------------------------------------
    "view_status": ("🟩 Area status", "🟩 حالة المناطق"),
    "view_photo": ("🛰️ Satellite photo", "🛰️ صورة القمر الصناعي"),
    "map_help": ("Tap a square on the map to open that area.", "اضغط على أي مربع في الخريطة لفتح المنطقة."),
    "zone": ("Area", "المنطقة"),
    "status": ("Status", "الحالة"),
    "score": ("RAY score", "مؤشر RAY"),
    "view_details": ("View details", "عرض التفاصيل"),
    "choose_area": ("Choose an area", "اختر منطقة"),
    # --- zones ------------------------------------------------------------------
    "why_q": ("What could the cause be?", "وش ممكن يكون السبب؟"),
    "why_note": ("Ranked by how well each cause fits the evidence we have. None is confirmed — the field check decides.",
                 "مرتبة حسب توافقها مع الدلائل المتوفرة. لا يوجد سبب مؤكد — الفحص الميداني هو الذي يحسم."),
    "fit": ("Fit with evidence", "التوافق مع الدلائل"),
    "why_reasons": ("Why?", "لماذا؟"),
    "no_evidence": ("No evidence yet — a field check or photo can help.", "لا توجد دلائل بعد — الفحص أو الصورة يساعدان."),
    "photo_this": ("📷 Photograph a plant in this area", "📷 صوّر نباتًا في هذه المنطقة"),
    "common_problems": ("Common problems in {crop}", "مشاكل شائعة في {crop}"),
    "pick_crop": ("Choose your crop on the home page to see its common diseases and pests.",
                  "اختر نوع محصولك في الصفحة الرئيسية لعرض الأمراض والآفات الشائعة."),
    "weather_line": ("Last days: max {t:.0f}°C · humidity {rh} · rain {p:.0f} mm", "الأيام الأخيرة: العظمى {t:.0f}° · الرطوبة {rh} · مطر {p:.0f} مم"),
    "weather_src": ("Source: {src}, until {d}", "المصدر: {src}، حتى {d}"),
    "weather_none": ("Weather data not available.", "بيانات الطقس غير متوفرة."),
    "tech_expander": ("🔬 Technical details", "🔬 تفاصيل فنية"),
    "source": ("Source", "المصدر"),
    "symptoms": ("Symptoms", "الأعراض"),
    "what_check": ("What to check", "وش تفحص"),
    "no_ref_image": ("No reference image available", "لا تتوفر صورة مرجعية"),
    "img_credit": ("Image: {a} · {lic} · {src}", "الصورة: {a} · {lic} · {src}"),
    # --- plant check ------------------------------------------------------------
    "plant_title": ("Photograph the plant", "صوّر النبات"),
    "step_where": ("1 · Where?", "١ · وين؟"),
    "step_photo": ("2 · Photo", "٢ · الصورة"),
    "step_see": ("3 · What do you see?", "٣ · وش تشوف؟"),
    "step_result": ("4 · Result", "٤ · النتيجة"),
    "upload": ("Take a photo or choose one (close-up of the leaves works best)", "صوّر أو اختر صورة (صورة قريبة للأوراق أفضل)"),
    "soil_q": ("Soil around the plant", "التربة حول النبات"),
    "soil_dry": ("Dry", "جافة"), "soil_wet": ("Very wet", "رطبة جدًا"), "soil_normal": ("Normal", "طبيعية"), "soil_unknown": ("Didn't check", "لم أتحقق"),
    "spread_q": ("How widespread?", "هل المشكلة منتشرة؟"),
    "spread_one": ("One / few plants", "نبات واحد أو قليل"), "spread_many": ("Spread across the area", "منتشرة في المنطقة"), "spread_unknown": ("Not sure", "لا أعرف"),
    "btn_analyze": ("🔍 Analyse", "🔍 حلّل"),
    "photo_quality_too_small": ("The photo is too small — take a closer, larger photo.", "الصورة صغيرة جدًا — صوّر صورة أقرب وأكبر."),
    "photo_quality_too_dark": ("The photo is too dark — try again in daylight.", "الصورة مظلمة — أعد التصوير في ضوء النهار."),
    "photo_quality_no_leaf": ("Not enough leaves in the photo — get closer to the plant.", "لا تظهر أوراق كافية — اقترب من النبات."),
    "photo_quality_unreadable": ("The file could not be read as an image.", "تعذّر قراءة الملف كصورة."),
    "photo_colors": ("Photo colours: green {g}% · yellow {y}% · brown {b}%", "ألوان الصورة: أخضر {g}٪ · أصفر {y}٪ · بني {b}٪"),
    "photo_method": ("Simple colour check — it cannot identify a disease.", "فحص ألوان مبسّط — لا يستطيع تحديد المرض."),
    "matches_title": ("The symptoms match…", "الأعراض تتوافق مع…"),
    "matches_none": ("No listed disease or pest of this crop matches the symptoms you chose.",
                     "لا يوجد مرض أو آفة مسجلة لهذا المحصول تتوافق مع الأعراض المختارة."),
    "matched_on": ("Matches: {m}", "يتوافق في: {m}"),
    "check_title": ("What to check now", "وش تفحص الآن"),
    "gen_check_1": ("Is the soil dry around the roots?", "هل التربة جافة حول الجذور؟"),
    "gen_check_2": ("Is irrigation water reaching this area?", "هل مياه الري تصل لهذه المنطقة؟"),
    "gen_check_3": ("Look under the leaves for spots or insects", "افحص أسفل الأوراق بحثًا عن بقع أو حشرات"),
    "gen_check_4": ("Is it one plant or many?", "هل المشكلة في نبات واحد أو عدة نباتات؟"),
    "advice": ("Recommended: confirm in the field before treating or changing irrigation.",
               "يُنصح بالتأكد ميدانيًا قبل أي علاج أو تغيير في الري."),
    "btn_save": ("💾 Save this observation", "💾 احفظ الملاحظة"),
    "saved": ("Saved. Area {z} · {d}", "تم الحفظ. المنطقة {z} · {d}"),
    "save_failed": ("Could not save: {e}", "تعذّر الحفظ: {e}"),
    "validate_title": ("✅ After your field check", "✅ بعد الفحص الميداني"),
    "validate_note": ("Tell RAY what you actually found. This is the most valuable data for improving RAY later.",
                      "أخبر رَيّ بما وجدته فعلًا. هذه أهم بيانات لتحسين رَيّ مستقبلًا."),
    "field_check": ("Soil check result", "نتيجة فحص التربة"),
    "fc_dry": ("Soil is dry", "التربة جافة"), "fc_not_dry": ("Soil is not dry", "التربة ليست جافة"), "fc_none": ("Not checked", "لم أتحقق"),
    "actual_cause": ("Actual cause found", "السبب الفعلي"),
    "actual_problem": ("Specific disease / pest (if known)", "المرض أو الآفة بالتحديد (إن عُرف)"),
    "cause_none": ("No problem found", "لا توجد مشكلة"), "cause_unknown": ("Still unknown", "غير معروف بعد"),
    "notes": ("Notes", "ملاحظات"),
    "btn_save_validation": ("Save field result", "احفظ نتيجة الفحص"),
    "validation_saved": ("Field result saved. Thank you!", "تم حفظ نتيجة الفحص. شكرًا لك!"),
    "history": ("Your observations (this session)", "ملاحظاتك (هذه الجلسة)"),
    "history_empty": ("No observations yet.", "لا توجد ملاحظات بعد."),
    "validated": ("field result recorded", "تم تسجيل نتيجة الفحص"),
    "not_validated": ("waiting for field result", "بانتظار نتيجة الفحص"),
    "need_photo_or_symptom": ("Add a photo or choose at least one symptom.", "أضف صورة أو اختر عرضًا واحدًا على الأقل."),
    # --- irrigation -------------------------------------------------------------
    "irr_title": ("💧 Irrigation check", "💧 فحص الري"),
    "irr_dss": ("RAY supports your decision. It does not run irrigation and does not calculate water amounts.",
                "رَيّ يدعم قرارك، ولا يشغّل الري ولا يحسب كمية المياه."),
    "irr_check_1": ("Check soil moisture", "تحقق من رطوبة التربة"),
    "irr_check_2": ("Check that water reaches the area", "تحقق من وصول المياه"),
    "irr_check_3": ("Inspect the plants", "افحص النبات"),
    "irr_check_4": ("Check for disease or pests", "تحقق من وجود مرض أو آفة"),
    "irr_check_5": ("Review the weather", "راجع حالة الطقس"),
    "irr_rule": ("Don't add water before you know the cause.", "لا تضف مياه قبل التحقق من السبب."),
    "irr_none": ("No area needs an irrigation check today.", "لا توجد منطقة تحتاج فحص ري اليوم."),
    "crop_water": ("Seasonal water need of {crop}", "الاحتياج المائي الموسمي لـ {crop}"),
    "crop_water_note": ("Total for the whole season (FAO guide values) — not a daily amount for your field.",
                        "إجمالي لكامل الموسم (قيم إرشادية من FAO) — وليست كمية يومية لحقلك."),
    "no_crop_title": ("Areas with no active crop", "مناطق بدون محصول نشط"),
    "no_crop_text": ("No green crop seen in: {zones}. If these are irrigated, that water may not be needed.",
                     "لا يظهر محصول أخضر في: {zones}. إذا كانت تُروى، فقد لا تحتاج تلك المياه."),
    "future_title": ("Coming later", "مستقبلًا"),
    "future_text": ("Satellite + soil sensors (IoT) + AI → smarter irrigation scheduling, after field validation.",
                    "أقمار صناعية + حساسات تربة (IoT) + ذكاء اصطناعي ← جدولة ري أذكى، بعد التحقق الميداني."),
    # --- about --------------------------------------------------------------
    "about_title": ("About RAY", "عن رَيّ"),
    "about_text": ("RAY looks at your farm from space, finds areas that changed in an unusual way, and helps you decide where to start your field check. It does not replace your visit to the field.",
                   "يراقب رَيّ مزرعتك من الفضاء، ويكتشف المناطق التي تغيّرت بشكل غير معتاد، ويساعدك تعرف «وين تبدأ الفحص». لا يغني عن زيارتك للحقل."),
    "about_flow": ("How it works", "كيف يعمل"),
    "flow_steps": ("Satellite data → AI analysis → unusual areas → priority area → field check → better decision",
                   "بيانات الأقمار الصناعية ← تحليل بالذكاء الاصطناعي ← مناطق غير معتادة ← منطقة ذات أولوية ← فحص ميداني ← قرار أفضل"),
    "how_status": ("How colours are decided", "كيف تُحدَّد الألوان"),
    "how_status_text": ("Each area gets points from five satellite signals (moisture, leaf greenness, vegetation compared with the farm, temperature, recent change). More points = more attention needed.",
                        "تحصل كل منطقة على نقاط من خمس إشارات (الرطوبة، خضرة الأوراق، النباتات مقارنة بالمزرعة، الحرارة، التغير الأخير). كلما زادت النقاط زادت الحاجة للانتباه."),
    "data_title": ("Where the data come from", "مصادر البيانات"),
    "privacy_title": ("Your privacy", "خصوصيتك"),
    "privacy_text": ("Photos are saved without location or device information, never uploaded to GitHub, and only you see your own observations in this session.",
                     "تُحفظ الصور بدون الموقع أو بيانات الجهاز، ولا تُرفع إلى GitHub، ولا يرى ملاحظاتك في هذه الجلسة غيرك."),
    "limits_title": ("Limitations", "القيود"),
    "storage_title": ("Where your observations are saved", "أين تُحفظ ملاحظاتك"),
    # --- errors -------------------------------------------------------------
    "ee_fail_title": ("Real satellite data could not be loaded.", "تعذّر تحميل بيانات الأقمار الصناعية الحقيقية."),
    "ee_fail_text": ("Google Earth Engine is not connected, so no farm results are shown. Fix the connection (details below) or switch to Demo Mode, which uses clearly labelled simulated data.",
                     "Google Earth Engine غير متصل، لذلك لا تُعرض نتائج للمزرعة. أصلح الاتصال (التفاصيل أدناه) أو انتقل إلى الوضع التجريبي ذي البيانات المحاكاة الموضّحة."),
    "use_demo": ("Use Demo Mode (simulated data)", "استخدم الوضع التجريبي (بيانات محاكاة)"),
}


def lang() -> str:
    return st.session_state.get("lang", "ar")


def is_ar() -> bool:
    return lang() == "ar"


def ltr(s) -> str:
    """Isolate numbers/dates so they read correctly inside right-to-left text."""
    return f"<bdi dir='ltr' style='white-space:nowrap'>{s}</bdi>"


def tr(en: str, ar: str) -> str:
    return ar if is_ar() else en


def t(key: str, **kw) -> str:
    en, ar = S[key]
    s = ar if is_ar() else en
    if kw and "date" in kw:  # keep ISO dates left-to-right inside Arabic sentences
        kw = {**kw, "date": ltr(kw["date"])}
    return s.format(**kw) if kw else s
