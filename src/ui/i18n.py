"""Farmer-facing text – clear, simple Modern Standard Arabic (no dialect, no technical terms).

Statuses come from the existing RAY classes; causes from src/fusion.py; crop facts from src/knowledge.py.
English strings are kept for developers/tests; the farmer interface is Arabic.
"""
from __future__ import annotations

import streamlit as st

S: dict[str, tuple[str, str]] = {
    # --- chrome -------------------------------------------------------------
    "app_name": ("RAY", "رَيّ"),
    "subtitle": ("Decision support for your farm.", "نظام يساعدك على متابعة مزرعتك واتخاذ القرار."),
    "image_date": ("Latest satellite image of your farm: {date}", "آخر صورة فضائية لمزرعتك: {date}"),
    "demo_note": ("Demonstration data only", "بيانات تجريبية للعرض فقط"),
    "menu": ("Menu", "القائمة"),
    "farm": ("Farm", "المزرعة"),
    # --- navigation ---------------------------------------------------------
    "nav_home": ("🏠 Home", "🏠 الرئيسية"),
    "nav_map": ("🗺️ Farm map", "🗺️ خريطة المزرعة"),
    "nav_zones": ("📍 Zones", "📍 المناطق"),
    "nav_plant": ("🌱 Plant check", "🌱 فحص النبات"),
    "nav_water": ("💧 Irrigation", "💧 الري"),
    "nav_log": ("📋 Farm record", "📋 سجل المزرعة"),
    "nav_about": ("ℹ️ About RAY", "ℹ️ عن رَيّ"),
    # --- home ---------------------------------------------------------------
    "q_home": ("What needs attention on my farm?", "ما الذي يحتاج إلى انتباه في مزرعتي؟"),
    "today_status": ("Your farm today", "حالة مزرعتك اليوم"),
    "btn_top": ("➜ Go to the highest priority", "➜ الانتقال إلى أعلى أولوية"),
    "top_zone": ("Highest priority", "أعلى أولوية"),
    "no_priority": ("No area needs inspection today. Continue your usual monitoring.",
                    "لا توجد اليوم منطقة تحتاج إلى فحص. استمر في المتابعة المعتادة."),
    "anomaly_note": ("Area {z} also deserves a look: it is not among the areas that need inspection, but the analysis found an unusual pattern there.",
                     "تستحق المنطقة {z} نظرة أيضًا: لم تُصنَّف ضمن المناطق التي تحتاج إلى فحص، لكن التحليل رصد فيها نمطًا غير معتاد."),
    "crop": ("Crop", "المحصول"),
    "btn_map": ("🗺️ Farm map", "🗺️ خريطة المزرعة"),
    "btn_photo": ("🌱 Photograph a plant", "🌱 تصوير نبات"),
    "others_watch": ("Other areas to follow up: {z}", "مناطق أخرى تحتاج إلى متابعة: {z}"),
    # --- zone classes (farmer wording of the existing classes) --------------
    "cls_HIGH": ("Needs inspection", "تحتاج إلى فحص"),
    "cls_MODERATE": ("Needs follow-up", "تحتاج إلى متابعة"),
    "cls_HEALTHY": ("Normal", "طبيعية"),
    "cls_NO_CROP": ("No active crop", "لا يوجد محصول نشط"),
    "cls_NO_DATA": ("Not enough data", "لا توجد بيانات كافية"),
    "why_HIGH": ("This area shows unusual signs compared with the surrounding areas; a field check is recommended.",
                 "توجد في هذه المنطقة مؤشرات غير طبيعية مقارنة بالمناطق المحيطة، ويُنصح بفحصها ميدانيًا."),
    "why_MODERATE": ("Some signs in this area are weaker than in the rest of the farm; follow-up is recommended.",
                     "بعض المؤشرات في هذه المنطقة أضعف من بقية المزرعة، ويُنصح بمتابعتها."),
    "why_HEALTHY": ("This area looks similar to the healthy parts of the farm.", "مؤشرات هذه المنطقة مشابهة للأجزاء السليمة من المزرعة."),
    "why_NO_CROP": ("No green crop cover is visible in this area in the satellite image.", "لا يظهر في هذه المنطقة غطاء نباتي أخضر في الصورة الفضائية."),
    "why_NO_DATA": ("This area could not be read in the latest image (clouds or missing data).",
                    "تعذّرت قراءة هذه المنطقة في الصورة الأخيرة بسبب الغيوم أو نقص البيانات."),
    "do_HIGH": ("Start by checking water delivery, soil moisture and plant condition.", "ابدأ بفحص وصول المياه ورطوبة التربة وحالة النبات."),
    "do_MODERATE": ("Please check this area on your next field visit.", "يُرجى فحص هذه المنطقة في زيارتك القادمة للحقل."),
    "do_HEALTHY": ("No action is needed. Continue monitoring.", "لا يلزم أي إجراء. استمر في المتابعة."),
    "do_NO_CROP": ("If this area is irrigated, please check whether this water is needed.", "إذا كانت هذه المنطقة تُروى، فيُرجى التحقق من الحاجة إلى هذه المياه."),
    "do_NO_DATA": ("Please try again after a new satellite image arrives.", "يُرجى المحاولة بعد وصول صورة فضائية جديدة."),
    "zone": ("Area", "المنطقة"),
    "status": ("Status", "الحالة"),
    "priority_score": ("Priority score", "درجة الأولوية"),
    # --- map ------------------------------------------------------------------
    "q_map": ("Where are the areas that need attention?", "أين توجد المناطق التي تحتاج إلى انتباه؟"),
    "view_status": ("🟩 Area status", "🟩 حالة المناطق"),
    "view_photo": ("🛰️ Satellite image", "🛰️ الصورة الفضائية"),
    "map_help": ("Tap any square on the map to see that area's details.", "اضغط على أي مربع في الخريطة لعرض تفاصيل المنطقة."),
    "choose_area": ("Choose an area", "اختر المنطقة"),
    "view_details": ("View details", "عرض التفاصيل"),
    "sky_ground": ("Satellite images help decide where to start checking; the field visit tells what the problem is.",
                   "تساعد الصور الفضائية على تحديد المكان الذي يبدأ منه الفحص، أما الزيارة الميدانية فتوضح طبيعة المشكلة."),
    # --- zones ------------------------------------------------------------------
    "q_cause": ("What is the likely cause?", "ما السبب المحتمل؟"),
    "prelim": ("These results are preliminary indicators, not a final diagnosis.", "هذه النتائج مؤشرات أولية وليست تشخيصًا نهائيًا."),
    "suspicion_level": ("Suspicion level", "درجة الاشتباه"),
    "why_reasons": ("Why?", "لماذا؟"),
    "no_evidence": ("There is not enough evidence yet. A field check or a plant photo will help.",
                    "لا توجد دلائل كافية حتى الآن. يساعد الفحص الميداني أو تصوير النبات على التوضيح."),
    "q_check": ("What should be checked?", "ما الذي ينبغي فحصه؟"),
    "check_1": ("Make sure water reaches the area.", "التأكد من وصول المياه إلى المنطقة."),
    "check_2": ("Check soil moisture.", "فحص رطوبة التربة."),
    "check_3": ("Check the condition of the plants.", "فحص حالة النباتات."),
    "check_4": ("Look for signs of pests or diseases.", "البحث عن علامات الآفات أو الأمراض."),
    "check_5": ("Check the heat and weather conditions.", "التحقق من الظروف الحرارية والطقس."),
    "irr_rule": ("Do not change the amount of irrigation before checking the cause in the field.",
                 "لا تغيّر كمية الري قبل التحقق من السبب ميدانيًا."),
    "btn_photo_zone": ("🌱 Photograph a plant in this area", "🌱 تصوير نبات من هذه المنطقة"),
    "common_problems": ("Common problems in {crop}", "مشكلات شائعة في محصول {crop}"),
    "pick_crop": ("Choose the crop type to see its common diseases and pests.", "اختر نوع المحصول لعرض الأمراض والآفات الشائعة فيه."),
    "weather_line": ("Recent weather: average maximum {t:.0f}°C, humidity {rh}, rainfall {p:.0f} mm.",
                     "الطقس في الأيام الأخيرة: متوسط درجة الحرارة العظمى {t:.0f}°م، والرطوبة {rh}، والأمطار {p:.0f} مم."),
    "weather_until": ("Latest available weather data: {d}", "آخر بيانات طقس متاحة: {d}"),
    "weather_none": ("Weather information is not available at the moment.", "معلومات الطقس غير متاحة حاليًا."),
    "symptoms": ("Symptoms", "الأعراض"),
    "what_check": ("What to check", "ما الذي ينبغي فحصه"),
    "conditions": ("Conditions that favour it", "الظروف المساعدة على ظهوره"),
    "similar": ("Similar problems", "مشكلات مشابهة"),
    "source": ("Source", "المصدر"),
    "no_ref_image": ("No reference image available", "لا تتوفر صورة مرجعية"),
    "img_credit": ("Image: {a} · licence {lic}", "الصورة: {a} · الترخيص {lic}"),
    "ref_image": ("Reference image (not from your farm)", "صورة مرجعية (ليست من مزرعتك)"),
    # --- plant check ------------------------------------------------------------
    "plant_title": ("🌱 Plant check", "🌱 فحص النبات"),
    "step_where": ("1. Place and crop", "١. المكان والمحصول"),
    "step_photo": ("2. Plant photo", "٢. صورة النبات"),
    "step_see": ("3. Visible symptoms (if any)", "٣. الأعراض الظاهرة (إن وُجدت)"),
    "step_result": ("4. Preliminary analysis result", "٤. نتيجة التحليل المبدئي"),
    "upload": ("Take a photo of the plant or choose one from your device (a close-up of the leaves is best).",
               "التقط صورة للنبات أو اختر صورة من جهازك (يُفضَّل تصوير الأوراق عن قرب)."),
    "soil_q": ("Soil around the plant", "حالة التربة حول النبات"),
    "soil_dry": ("Dry", "جافة"), "soil_wet": ("Very wet", "رطبة جدًا"), "soil_normal": ("Normal", "طبيعية"), "soil_unknown": ("Not checked", "لم أتحقق"),
    "spread_q": ("How widespread is the problem?", "مدى انتشار المشكلة"),
    "spread_one": ("One or a few plants", "نبات واحد أو عدد قليل من النباتات"), "spread_many": ("Widespread in the area", "منتشرة في المنطقة"),
    "spread_unknown": ("Unknown", "غير معروف"),
    "btn_analyze": ("🔍 Preliminary analysis", "🔍 تحليل مبدئي"),
    "need_input": ("Please add a photo or choose at least one symptom.", "يُرجى إضافة صورة أو اختيار عرض واحد على الأقل."),
    "photo_quality_too_small": ("The photo is too small. Please take a closer, clearer photo.", "الصورة صغيرة جدًا. يُرجى التقاط صورة أقرب وأوضح."),
    "photo_quality_too_dark": ("The photo is too dark. Please take it again in daylight.", "الصورة مظلمة. يُرجى إعادة التصوير في ضوء النهار."),
    "photo_quality_no_leaf": ("Not enough leaves are visible. Please move closer to the plant.", "لا تظهر أوراق كافية في الصورة. يُرجى الاقتراب من النبات."),
    "photo_quality_unreadable": ("The file could not be read as an image.", "تعذّرت قراءة الملف بوصفه صورة."),
    "photo_colors": ("Leaf colours in the photo: green {g}%, yellow {y}%, brown {b}%.", "ألوان الأوراق في الصورة: أخضر {g}٪، وأصفر {y}٪، وبني {b}٪."),
    "photo_method": ("The photo check measures leaf colours only; it does not identify diseases by itself.",
                     "يقيس فحص الصورة ألوان الأوراق فقط، ولا يحدد المرض بمفرده."),
    "first_suspicion": ("🔍 First suspicion", "🔍 الاشتباه الأول"),
    "may_match": ("May match", "قد يتوافق مع"),
    "matching_symptoms": ("Matching symptoms", "الأعراض المتوافقة"),
    "other_possibilities": ("Other possibilities", "احتمالات أخرى"),
    "insufficient": ("There is not enough information to identify a clear suspicion. A field check of the plant is recommended.",
                     "لا توجد معلومات كافية لتحديد اشتباه واضح. يُنصح بفحص النبات ميدانيًا."),
    "yellowing_note": ("Yellow leaves can have several causes, such as water stress, nutrient deficiency or disease. Check the soil, irrigation and leaves before deciding.",
                       "اصفرار الأوراق قد يرتبط بعدة أسباب، منها الإجهاد المائي أو نقص العناصر أو المرض. يُنصح بفحص التربة والري والأوراق قبل اتخاذ قرار."),
    "final_note": ("This is a preliminary result, not a final diagnosis. Field verification is recommended.",
                   "هذه نتيجة أولية وليست تشخيصًا نهائيًا، ويُنصح بالتحقق ميدانيًا."),
    "plant_check_1": ("How far the symptoms have spread.", "مدى انتشار الأعراض."),
    "plant_check_2": ("The underside of the leaves.", "الجهة السفلية من الأوراق."),
    "plant_check_3": ("Moisture in the area.", "رطوبة المنطقة."),
    "plant_check_4": ("Presence of pests or insects.", "وجود آفات أو حشرات."),
    "plant_check_5": ("Soil condition and irrigation.", "حالة التربة والري."),
    "btn_save": ("💾 Save to the farm record", "💾 حفظ في سجل المزرعة"),
    "saved": ("Saved to the farm record.", "تم الحفظ في سجل المزرعة."),
    "save_failed": ("Saving failed. Please try again.", "تعذّر الحفظ. يُرجى المحاولة مرة أخرى."),
    # --- field validation ---------------------------------------------------------
    "validate_title": ("✅ Field check result", "✅ نتيجة التحقق الميداني"),
    "validate_note": ("After visiting the field, record what you found. This information helps improve RAY in the future.",
                      "بعد زيارة الحقل، سجّل ما وجدته فعلًا. تساعد هذه المعلومات على تحسين رَيّ مستقبلًا."),
    "field_check": ("Soil check", "فحص التربة"),
    "fc_dry": ("Soil is dry", "التربة جافة"), "fc_not_dry": ("Soil is not dry", "التربة ليست جافة"), "fc_none": ("Not checked", "لم أتحقق"),
    "actual_cause": ("Actual cause found", "السبب الفعلي"),
    "actual_problem": ("Specific disease or pest (if known)", "المرض أو الآفة بالتحديد (إن عُرف)"),
    "cause_none": ("No problem found", "لم أجد مشكلة"), "cause_unknown": ("Not known yet", "غير معروف حتى الآن"),
    "action": ("Action taken", "الإجراء الذي قمت به"),
    "act_none": ("No action yet", "لم أتخذ إجراءً بعد"), "act_fix": ("Fixed a problem in the irrigation system", "أصلحت مشكلة في نظام الري"),
    "act_water": ("Changed the amount of irrigation", "غيّرت كمية الري"), "act_treat": ("Treated a disease or pest", "عالجت مرضًا أو آفة"),
    "act_expert": ("Consulted an agricultural engineer", "استشرت مهندسًا زراعيًا"), "act_other": ("Other", "إجراء آخر"),
    "notes": ("Notes", "ملاحظات"),
    "btn_save_validation": ("Save the field result", "حفظ نتيجة التحقق"),
    "validation_saved": ("The field result was saved. Thank you.", "تم حفظ نتيجة التحقق الميداني. شكرًا لك."),
    # --- farm record ---------------------------------------------------------------
    "log_title": ("📋 Farm record", "📋 سجل المزرعة"),
    "log_empty": ("There are no records yet. You can add one from the plant check page.", "لا توجد سجلات بعد. يمكنك إضافة سجل من صفحة فحص النبات."),
    "log_photo": ("Plant photo", "صورة النبات"),
    "log_result": ("Preliminary result", "نتيجة الفحص المبدئي"),
    "log_symptoms": ("Recorded symptoms", "الأعراض المسجلة"),
    "log_validated": ("Field check recorded", "تم تسجيل التحقق الميداني"),
    "log_pending": ("Waiting for the field check result", "بانتظار نتيجة التحقق الميداني"),
    "log_session_note": ("Only the records saved from this device during this session are shown.", "تُعرض السجلات المحفوظة من هذا الجهاز خلال هذه الجلسة فقط."),
    # --- irrigation -------------------------------------------------------------
    "irr_title": ("💧 Irrigation", "💧 الري"),
    "irr_dss": ("RAY does not control the irrigation system and does not set the amount of water automatically.",
                "رَيّ لا يتحكم في نظام الري ولا يحدد كمية المياه تلقائيًا."),
    "irr_list": ("Checklist before changing irrigation", "قائمة الفحص قبل تغيير الري"),
    "irr_check_1": ("Check that water reaches the area.", "التحقق من وصول المياه."),
    "irr_check_2": ("Check soil moisture.", "التحقق من رطوبة التربة."),
    "irr_check_3": ("Check the condition of the plants.", "فحص حالة النبات."),
    "irr_check_4": ("Look for disease or pests.", "البحث عن مرض أو آفة."),
    "irr_check_5": ("Review the weather.", "مراجعة حالة الطقس."),
    "irr_check_6": ("Check the irrigation system.", "التحقق من نظام الري."),
    "irr_zones": ("Areas to check first", "المناطق التي يُبدأ بفحصها"),
    "irr_none": ("No area needs an irrigation check today.", "لا توجد اليوم منطقة تحتاج إلى فحص الري."),
    "crop_water": ("Seasonal water need of {crop}", "الاحتياج المائي الموسمي لمحصول {crop}"),
    "crop_water_note": ("This is the total for the whole season (FAO guide values), not a daily amount for your field.",
                        "هذه قيمة إجمالية لكامل الموسم (قيم إرشادية من منظمة الأغذية والزراعة)، وليست كمية يومية لحقلك."),
    "no_crop_title": ("Areas without an active crop", "مناطق لا يوجد فيها محصول نشط"),
    "no_crop_text": ("No green crop is visible in: {zones}. If these areas are irrigated, this water may not be needed.",
                     "لا يظهر محصول أخضر في: {zones}. إذا كانت هذه المناطق تُروى، فقد لا تكون هذه المياه ضرورية."),
    # --- about --------------------------------------------------------------
    "about_title": ("About RAY", "عن رَيّ"),
    "about_text": ("RAY helps the farmer know which areas of the farm need inspection, using satellite images, weather data and smart analysis.",
                   "رَيّ يساعد المزارع على معرفة المناطق التي تحتاج إلى فحص في مزرعته باستخدام بيانات الأقمار الصناعية والطقس والتحليل الذكي."),
    "about_not": ("RAY does not replace the field check and does not control the irrigation system.",
                  "رَيّ لا يستبدل الفحص الميداني، ولا يتحكم في نظام الري."),
    "how_title": ("How does RAY work?", "كيف يعمل رَيّ؟"),
    "how_1": ("🛰️ From the sky: find the areas that look unusual.", "🛰️ من السماء: تحديد المناطق التي تظهر فيها مؤشرات غير طبيعية."),
    "how_2": ("📍 The area: start your check here.", "📍 المنطقة: ابدأ الفحص من هنا."),
    "how_3": ("🌱 From the ground: photograph the plant if you see symptoms.", "🌱 من الأرض: صوّر النبات إذا لاحظت أعراضًا."),
    "how_4": ("🔍 Analysis: a preliminary suspicion of a possible problem.", "🔍 التحليل: اشتباه مبدئي في مشكلة محتملة."),
    "how_5": ("📋 Check: the things to verify.", "📋 الفحص: الأمور التي ينبغي التحقق منها."),
    "how_6": ("💧 Decision: decide on irrigation after verification.", "💧 القرار: اتخذ قرار الري بعد التحقق."),
    "not_title": ("What RAY does not do", "ما الذي لا يفعله رَيّ"),
    "not_1": ("It does not give a final diagnosis of plant diseases.", "لا يقدم تشخيصًا نهائيًا لأمراض النبات."),
    "not_2": ("It does not set irrigation amounts and does not run the irrigation system.", "لا يحدد كميات الري ولا يشغّل نظام الري."),
    "not_3": ("Satellite images show areas, not individual plants.", "الصور الفضائية تُظهر المناطق، ولا تُظهر النبات الواحد."),
    "privacy_title": ("Your privacy", "خصوصيتك"),
    "privacy_text": ("Photos are saved without location or device information, and your records are not shown to other users.",
                     "تُحفظ الصور دون معلومات الموقع أو الجهاز، ولا تُعرض سجلاتك على المستخدمين الآخرين."),
    # --- errors -------------------------------------------------------------
    "load_failed": ("The farm data could not be loaded at the moment. Please try again later.",
                    "تعذّر تحميل بيانات المزرعة حاليًا. يُرجى المحاولة لاحقًا."),
    "btn_retry": ("Try again", "إعادة المحاولة"),
}

AR_NUM = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")


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
    if kw and "date" in kw:
        kw = {**kw, "date": ltr(kw["date"])}
    return s.format(**kw) if kw else s


def count_areas(n: int, kind: str) -> str:
    """Arabic number agreement for 'N area(s) …' (kind: 'check' | 'watch' | 'ok')."""
    if not is_ar():
        word = {"check": "need inspection", "watch": "need follow-up", "ok": "normal"}[kind]
        return f"{n} area{'s' if n != 1 else ''} {word}"
    verb = {"check": ("تحتاج إلى فحص", "تحتاجان إلى فحص"), "watch": ("تحتاج إلى متابعة", "تحتاجان إلى متابعة"),
            "ok": ("طبيعية", "طبيعيتان")}[kind]
    if n == 0:
        return {"check": "لا توجد مناطق تحتاج إلى فحص", "watch": "لا توجد مناطق تحتاج إلى متابعة", "ok": "لا توجد مناطق طبيعية"}[kind]
    if n == 1:
        return f"منطقة واحدة {verb[0]}"
    if n == 2:
        return f"منطقتان {verb[1]}"
    if 3 <= n <= 10:
        return f"{n} مناطق {verb[0]}"
    return f"{n} منطقة {verb[0]}"
