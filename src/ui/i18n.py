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
    "nav_home": (":material/home: Home", ":material/home: الرئيسية"),
    "nav_map": (":material/map: Farm map", ":material/map: خريطة المزرعة"),
    "nav_zones": (":material/location_on: Zones", ":material/location_on: المناطق"),
    "nav_water": (":material/water_drop: Irrigation", ":material/water_drop: الري"),
    "nav_about": (":material/info: About RAY", ":material/info: عن رَيّ"),
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
    "others_watch": ("Other areas to follow up: {z}", "مناطق أخرى تحتاج إلى متابعة: {z}"),
    # --- zone classes (farmer wording of the existing classes) --------------
    "cls_HIGH": ('Needs inspection', 'يحتاج إلى فحص'),
    "cls_MODERATE": ('Needs follow-up', 'يحتاج إلى متابعة'),
    "cls_HEALTHY": ('No clear abnormal signal', 'لا توجد إشارة غير طبيعية واضحة'),
    "cls_NO_CROP": ("No active crop", "لا يوجد محصول نشط"),
    "cls_NO_DATA": ('Insufficient data', 'بيانات غير كافية'),
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
    "view_image": ("🛰️ Satellite image", "🛰️ الصورة الفضائية"),
    "ind_flagged": ("Indicators flagged", "مؤشرات تجاوزت العتبة"),
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
    "no_evidence": ('There is not enough evidence yet. A field check will help.', 'لا توجد دلائل كافية حتى الآن. يساعد الفحص الميداني على التوضيح.'),
    "q_check": ("What should be checked?", "ما الذي ينبغي فحصه؟"),
    "check_1": ("Make sure water reaches the area.", "التأكد من وصول المياه إلى المنطقة."),
    "check_2": ("Check soil moisture.", "فحص رطوبة التربة."),
    "check_3": ("Check the condition of the plants.", "فحص حالة النباتات."),
    "check_4": ("Look for signs of pests or diseases.", "البحث عن علامات الآفات أو الأمراض."),
    "check_5": ("Check the heat and weather conditions.", "التحقق من الظروف الحرارية والطقس."),
    "irr_rule": ("Do not change the amount of irrigation before checking the cause in the field.",
                 "لا تغيّر كمية الري قبل التحقق من السبب ميدانيًا."),
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
    # --- field inspection log (non-photographic) -------------------------------------
    "nav_log": (":material/assignment: Field inspections", ":material/assignment: سجل الفحص"),
    "log_title": ("📋 Field inspection log", "📋 سجل الفحص الميداني"),
    "log_intro": ("Record what you found after visiting an area. These records are your own notes: they are not verified measurements, but they let RAY be checked against the field later.",
                  "سجّل ما وجدته بعد زيارة المنطقة. هذه ملاحظاتك الشخصية وليست قياسات موثّقة، لكنها تسمح بمقارنة نتائج رَيّ بالواقع الميداني لاحقًا."),
    "save_failed": ("Saving failed. Please try again.", "تعذّر الحفظ. يُرجى المحاولة مرة أخرى."),
    "log_add": ("Add an inspection", "إضافة فحص ميداني"),
    "log_date": ("Inspection date", "تاريخ الفحص"),
    "log_condition": ("What did you find?", "ماذا وجدت؟"),
    "cond_needs_attention": ("A problem that needs action", "مشكلة تحتاج إلى إجراء"),
    "cond_no_problem": ("No problem found", "لم أجد مشكلة"),
    "cond_not_sure": ("Not sure", "غير متأكد"),
    "log_irrigation": ("Was there a problem in the irrigation system?", "هل وُجدت مشكلة في نظام الري؟"),
    "irr_yes": ("Yes", "نعم"), "irr_no": ("No", "لا"), "irr_not_checked": ("Not checked", "لم أتحقق"),
    "log_alt": ("Other possible causes you noticed (optional)", "أسباب أخرى محتملة لاحظتها (اختياري)"),
    "alt_heat": ("Heat", "الحرارة"), "alt_salinity": ("Salinity", "الملوحة"), "alt_disease": ("Disease", "مرض"),
    "alt_pest": ("Pests", "آفات"), "alt_nutrient": ("Nutrient shortage", "نقص العناصر الغذائية"),
    "alt_harvest": ("Harvest or cutting", "حصاد أو حش"), "alt_growth_stage": ("Crop growth stage", "مرحلة نمو المحصول"),
    "alt_other": ("Other", "أخرى"),
    "log_moisture": ("Measured soil moisture, % (optional, leave 0 if not measured)", "رطوبة التربة المقاسة ٪ (اختياري، اتركها صفرًا إن لم تُقَس)"),
    "log_inspector": ("Who inspected? (optional: name or role)", "من قام بالفحص؟ (اختياري: الاسم أو الصفة)"),
    "notes": ("Notes", "ملاحظات"),
    "log_moisture_short": ("Measured soil moisture, %", "رطوبة التربة المقاسة ٪"),
    "btn_log_save": ("Save the inspection", "حفظ الفحص"),
    "log_saved": ("The inspection was saved.", "تم حفظ الفحص."),
    "log_empty": ("No inspections recorded yet in this session.", "لا توجد فحوص مسجلة بعد في هذه الجلسة."),
    "log_session_note": ("Only the records saved from this device during this session are shown.", "تُعرض السجلات المحفوظة من هذا الجهاز خلال هذه الجلسة فقط."),
    "log_sat": ("Satellite status at the time", "حالة القمر الصناعي وقتها"),
    "log_by": ("Recorded by", "سُجّل بواسطة"),
    "val_title": ("How do the satellite flags compare with your inspections?", "كيف تقارن إشارات القمر الصناعي بفحوصك؟"),
    "val_flagged": ("Flagged areas you inspected: {n}, of which a problem was found in: {k}",
                    "مناطق مُعلَّمة فحصتها: {n}، وُجدت مشكلة في: {k}"),
    "val_unflagged": ("Unflagged areas you inspected: {n}, of which a problem was found in: {k}",
                      "مناطق غير مُعلَّمة فحصتها: {n}، وُجدت مشكلة في: {k}"),
    "val_small": ("These are just a few records, so they say nothing reliable about RAY's accuracy yet (at least {m} inspections of flagged areas are needed).",
                  "هذه سجلات قليلة، ولا تدل على دقة رَيّ بعد (يلزم {m} فحصًا على الأقل للمناطق المُعلَّمة)."),
    "val_none": ("No comparable records yet.", "لا توجد سجلات قابلة للمقارنة بعد."),
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
    # --- irrigation: decision support ----------------------------------------------
    "irr_status": ("Irrigation status", "حالة الري"),
    "irr_ok_line": ("{n} with no worrying signs at the moment", "{n} لا تظهر فيها مؤشرات مقلقة حاليًا"),
    "irr_top": ("Highest priority for inspection: {z}", "أعلى أولوية للفحص: {z}"),
    "btn_show_on_map": ("🗺️ Show {z} on the map", "🗺️ عرض {z} على الخريطة"),
    "irr_zone_pick": ("Area to analyse", "المنطقة المراد تحليلها"),
    "ws_likely": ('Signs consistent with possible water stress (a hypothesis to verify in the field)', 'مؤشرات متوافقة مع إجهاد مائي محتمل (فرضية تحتاج إلى تحقق ميداني)'),
    "ws_some": ('Some signs may be consistent with water stress (a hypothesis to verify in the field)', 'قد تتوافق بعض المؤشرات مع إجهاد مائي (فرضية تحتاج إلى تحقق ميداني)'),
    "ws_none": ("Unusual signs, but no clear sign of water stress", "مؤشرات غير طبيعية، دون مؤشرات واضحة على الإجهاد المائي"),
    "ws_explain": ("This area shows signs that differ from the surrounding areas. Satellite images alone cannot prove that the cause is lack of water.",
                   "تظهر في هذه المنطقة مؤشرات تختلف عن المناطق المحيطة. ولا تثبت الصور الفضائية وحدها أن السبب هو نقص المياه."),
    "ws_why": ("Why did this area appear?", "لماذا ظهرت هذه المنطقة؟"),
    "why_plant": ("Plant condition in this area is weaker than in the surrounding areas.", "حالة النبات في هذه المنطقة أضعف من المناطق المحيطة."),
    "why_moisture": ("There are signs linked to lower plant moisture.", "توجد مؤشرات مرتبطة بانخفاض رطوبة النبات."),
    "why_heat": ("The surface temperature of this area is higher than the farm average.", "درجة حرارة سطح هذه المنطقة أعلى من متوسط المزرعة."),
    "why_heat_na": ("Surface-temperature information for this area is not available at the moment.", "معلومات حرارة السطح لهذه المنطقة غير متاحة حاليًا."),
    "why_change": ("Plant condition declined over roughly the last two weeks.", "تراجعت حالة النبات خلال الأسبوعين الأخيرين تقريبًا."),
    "why_green": ("Leaf greenness is lower than expected.", "خضرة الأوراق أقل من المتوقع."),
    "why_unusual": ("The analysis found an unusual pattern in this area.", "رصد التحليل نمطًا غير معتاد في هذه المنطقة."),
    "why_none": ("No single sign stands out; the area deserves follow-up.", "لا يبرز مؤشر بعينه، لكن المنطقة تستحق المتابعة."),
    "cmp_top": ("This is the highest-priority area for inspection on the farm.", "هذه المنطقة هي الأعلى أولوية للفحص في المزرعة."),
    "cmp_rank": ("This area is priority {r} of {n} areas that deserve attention.", "هذه المنطقة في الترتيب {r} من بين {n} مناطق تستحق الانتباه."),
    "cmp_ok": ("This area does not differ worryingly from the rest of the farm.", "لا تختلف هذه المنطقة بشكل مقلق عن بقية المزرعة."),
    "trend_title": ("How the area has changed", "تطور حالة المنطقة"),
    "trend_up": ("🟢 Improving", "🟢 تحسن"), "trend_flat": ("🟡 Stable", "🟡 مستقر"), "trend_down": ("🔴 Declining", "🔴 تراجع"),
    "trend_basis": ("Based on {n} satellite images from {a} to {b}. Harvest or cutting can also appear as a decline.",
                    "مبني على {n} صورة فضائية من {a} إلى {b}. قد يظهر الحصاد أو الحش أيضًا على شكل تراجع."),
    "trend_na": ("Not enough images over time are available for this area.", "لا تتوفر صور كافية عبر الزمن لهذه المنطقة."),
    "trend_axis": ("Vegetation condition", "حالة الغطاء النباتي"),
    "causes_title": ("Possible causes", "الأسباب المحتملة"),
    "causes_note": ("These are possible causes, not a confirmed diagnosis.", "هذه أسباب محتملة وليست تشخيصًا مؤكدًا."),
    "cz_water": ("💧 A problem with water delivery", "💧 مشكلة في وصول المياه"),
    "cz_water_1": ("Weak water delivery.", "ضعف وصول المياه."), "cz_water_2": ("A blocked or weak irrigation point.", "انسداد أو ضعف إحدى نقاط الري."),
    "cz_water_3": ("Uneven water distribution.", "عدم انتظام توزيع المياه."), "cz_water_4": ("A leak in the system.", "تسرب في النظام."),
    "cz_heat": ("🌡️ Heat", "🌡️ الحرارة"),
    "cz_heat_1": ("High temperatures can stress plants even when water is available.", "ارتفاع الحرارة قد يسبب إجهادًا للنبات حتى مع وجود المياه."),
    "cz_soil": ("🌱 Soil", "🌱 التربة"),
    "cz_soil_1": ("Dry soil.", "جفاف التربة."), "cz_soil_2": ("Poor drainage.", "سوء الصرف."),
    "cz_soil_3": ("Differences in soil properties.", "اختلاف خصائص التربة."),
    "cz_salt": ("🧂 Salinity", "🧂 الملوحة"),
    "cz_salt_1": ("Salts in the soil make it harder for the plant to take up water, so it can suffer water stress even in moist soil.",
                  "الأملاح في التربة تجعل حصول النبات على الماء أصعب، فقد يتعرض لإجهاد مائي حتى في تربة رطبة."),
    "cz_pest": ("🐛 Pests and diseases", "🐛 الآفات والأمراض"),
    "cz_pest_1": ("Some diseases and pests cause symptoms that look like water stress.", "بعض الأمراض والآفات تسبب أعراضًا تشبه الإجهاد المائي."),
    "cz_fert": ("🌿 Fertilisation", "🌿 التسميد"),
    "cz_fert_1": ("A possible fertilisation problem or a shortage of a nutrient.", "مشكلة محتملة في التسميد أو نقص أحد العناصر الغذائية."),
    "cz_fert_2": ("Review the fertilisation programme and, if needed, test the soil or the plant.", "يُنصح بمراجعة برنامج التسميد، وعند الحاجة إجراء فحص للتربة أو النبات."),
    "ev_supported": ("Supported by the available data", "تدعمه البيانات المتاحة"),
    "ev_field": ("No direct data — needs a field check", "لا تتوفر بيانات مباشرة، ويحتاج إلى فحص ميداني"),
    "ev_label": ("Evidence", "الدلائل"),
    "yellow_many": ("Yellow leaves do not automatically mean a lack of fertiliser or water. They can come from water, heat, salinity, diseases, pests, nutrient shortage or other factors. Please check in the field before deciding.",
                    "اصفرار الأوراق لا يعني تلقائيًا نقص السماد أو نقص الماء؛ فقد ينتج عن الماء أو الحرارة أو الملوحة أو الأمراض أو الآفات أو نقص العناصر الغذائية أو عوامل أخرى. يُنصح بالتحقق ميدانيًا قبل اتخاذ القرار."),
    "chk_sys": ("First: the irrigation system", "أولًا: نظام الري"),
    "chk_sys_1": ("Does water reach the area?", "هل تصل المياه إلى المنطقة؟"), "chk_sys_2": ("Are there weak or blocked irrigation points?", "هل توجد نقاط ري ضعيفة أو مسدودة؟"),
    "chk_sys_3": ("Is there a leak?", "هل يوجد تسرب؟"), "chk_sys_4": ("Is water distributed evenly?", "هل توزيع المياه متساوٍ؟"),
    "chk_sys_5": ("Is the area dry compared with other areas?", "هل توجد منطقة جافة مقارنة بالمناطق الأخرى؟"),
    "chk_soil": ("Second: the soil", "ثانيًا: التربة"),
    "chk_soil_1": ("Check soil moisture.", "فحص رطوبة التربة."), "chk_soil_2": ("Check for uneven dryness.", "التحقق من وجود جفاف غير متجانس."),
    "chk_soil_3": ("Look for standing water.", "البحث عن تجمع المياه."), "chk_soil_4": ("Check for poor drainage.", "التحقق من سوء الصرف."),
    "chk_soil_5": ("Check salinity if there are signs of it.", "التحقق من الملوحة عند وجود مؤشرات عليها."),
    "chk_plant": ("Third: the plant", "ثالثًا: النبات"),
    "chk_plant_1": ("Check for wilting.", "فحص الذبول."), "chk_plant_2": ("Check leaf colour.", "فحص لون الأوراق."),
    "chk_plant_3": ("Compare growth with the surrounding areas.", "مقارنة النمو بالمناطق المحيطة."),
    "chk_plant_4": ("Look for spots or disease symptoms.", "البحث عن بقع أو أعراض مرضية."), "chk_plant_5": ("Look for insects or signs of pests.", "البحث عن حشرات أو آثار آفات."),
    "chk_fert": ("Fourth: fertilisation", "رابعًا: التسميد"),
    "chk_fert_1": ("Review the fertilisation programme.", "مراجعة برنامج التسميد."), "chk_fert_2": ("Check how the fertiliser was distributed.", "التحقق من توزيع السماد."),
    "chk_fert_3": ("Note any yellowing or weak growth.", "ملاحظة وجود اصفرار أو ضعف نمو."),
    "chk_fert_4": ("Test the soil or the plant if needed.", "إجراء فحص للتربة أو النبات عند الحاجة."),
    "now_title": ("What do I do now?", "ماذا أفعل الآن؟"),
    "now_1": ("Start by inspecting the priority area.", "ابدأ بفحص المنطقة ذات الأولوية."), "now_2": ("Check that water reaches it.", "تحقق من وصول المياه."),
    "now_3": ("Check soil moisture.", "افحص رطوبة التربة."), "now_4": ("Check the condition of the plants.", "افحص حالة النبات."),
    "now_5": ("Check for disease or pests.", "تحقق من وجود مرض أو آفة."),
    "now_6": ("Review soil, salinity and fertilisation if needed.", "راجع التربة والملوحة والتسميد عند الحاجة."),
    "now_7": ("After finding the cause, make the right irrigation decision.", "بعد تحديد السبب، اتخذ قرار الري المناسب."),
    "prio_title": ("Area priorities", "أولوية المناطق"),
    "prio_high": ("🔴 High priority — start inspecting here.", "🔴 أولوية عالية — ابدأ الفحص هنا."),
    "prio_mid": ("🟡 Medium priority — follow the area.", "🟡 أولوية متوسطة — تابع المنطقة."),
    "prio_ok": ("🟢 Stable — no worrying signs at the moment: {n}", "🟢 حالة مستقرة — لا توجد مؤشرات مقلقة حاليًا: {n}"),
    "dss_goal": ("RAY is a decision-support system, not an automatic irrigation controller. Its aim is to show where to start checking and what to verify before deciding on irrigation.",
                 "رَيّ نظام لدعم القرار، وليس نظامًا للتحكم التلقائي في الري. هدفه تحديد المكان الذي يبدأ منه الفحص، وما ينبغي التحقق منه قبل اتخاذ قرار الري."),
    # --- data status & dashboard -----------------------------------------------------
    "nav_tech": (":material/science: Technical details", ":material/science: التفاصيل التقنية"),
    "st_real": ("Real satellite data", "بيانات فضائية حقيقية"),
    "st_unavailable": ("Real data unavailable", "البيانات الحقيقية غير متاحة حاليًا"),
    "st_demo": ("DEMO data (simulated)", "بيانات تجريبية (محاكاة)"),
    "demo_banner": ("DEMO MODE: no satellite connection is configured, so everything shown is simulated and does not describe a real farm.",
                    "وضع تجريبي: لم يُضبط الاتصال بالأقمار الصناعية، لذلك كل ما يظهر محاكاة ولا يصف مزرعة حقيقية."),
    "latest_obs": ("Latest valid observation: {date} ({n} days ago)", "آخر ملاحظة صالحة: {date} (قبل {n} يومًا)"),
    "latest_obs_demo": ("Simulated observation date: {date}", "تاريخ الملاحظة المحاكاة: {date}"),
    "stale_note": ("This image is old; recent changes on the farm are not visible in it.", "هذه الصورة قديمة نسبيًا، ولا تظهر فيها التغيرات الأخيرة في المزرعة."),
    "period": ("Analysis period: {a} to {b}", "فترة التحليل: من {a} إلى {b}"),
    "n_nocrop": ("No active crop: {z}", "لا يوجد محصول نشط في: {z}"),
    "next_action": ("Next step", "الخطوة التالية"),
    "grid_note": ("The squares are a regular analysis grid, not the real boundaries of fields or irrigation pivots.",
                  "المربعات شبكة تحليل منتظمة، وليست حدود الحقول أو محاور الري الفعلية."),
    "legend": ("Legend", "دليل الألوان"),
    # --- zone details -----------------------------------------------------------------
    "z_why_flag": ("Why was this area flagged?", "لماذا ظُهرت هذه المنطقة؟"),
    "z_values": ("Current indicator values", "قيم المؤشرات الحالية"),
    "z_quality": ("Data quality", "جودة البيانات"),
    "z_quality_line": ("Clear (cloud-free) pixels: {clear}% · crop cover: {veg}% · indicators evaluated: {n} of 5",
                       "البكسلات الصافية (بلا غيوم): {clear}٪ · الغطاء النباتي: {veg}٪ · المؤشرات المقيّمة: {n} من ٥"),
    "z_reference": ("Reference used for comparison", "المرجع المستخدم للمقارنة"),
    "z_reference_text": ("The area is compared with the median of the cropped areas of the same farm on the same date (vegetation index {ndvi}), and with the closest earlier image at least 10 days before ({prev}). These thresholds are provisional screening rules, not calibrated against field data.",
                         "تُقارَن المنطقة بوسيط المناطق المزروعة في المزرعة نفسها في التاريخ نفسه (مؤشر الغطاء النباتي {ndvi})، وبأقرب صورة سابقة بفارق ١٠ أيام على الأقل ({prev}). هذه العتبات قواعد فحص أولية وليست معايَرة ميدانيًا."),
    "z_reference_noprev": ("no earlier image available", "لا توجد صورة سابقة مناسبة"),
    "z_alt": ("Possible explanations (hypotheses, not findings)", "التفسيرات المحتملة (فرضيات وليست نتائج)"),
    "tr_insufficient": ("Insufficient data for a comparison over time ({n} clear images; at least {m} are needed).",
                        "بيانات غير كافية للمقارنة عبر الزمن ({n} صور صافية؛ يلزم {m} على الأقل)."),
    "tr_stable": ("No large change compared with the recent images (this does not mean the area is healthy).", "لا تغيّر كبير مقارنة بالصور الأخيرة (وهذا لا يعني أن المنطقة سليمة)."),
    "tr_decline": ("The latest image is lower than the previous images (one observation only).", "أحدث صورة أقل من الصور السابقة (ملاحظة واحدة فقط)."),
    "tr_persistent_decline": ("Lower than the previous images in the last two images in a row.", "أقل من الصور السابقة في آخر صورتين متتاليتين."),
    "tr_below_earlier": ("No sharp recent drop, but clearly lower than the earlier peak of this period ({peak}). This can be harvest, cutting or the crop's growth stage, or a problem worth checking.",
                         "لا يوجد تراجع حاد مؤخرًا، لكن القيمة أقل بوضوح من أعلى مستوى سابق في هذه الفترة ({peak}). قد يكون ذلك بسبب الحصاد أو الحش أو مرحلة نمو المحصول، أو مشكلة تستحق الفحص."),
    "tr_unavailable": ("The time series for this area could not be loaded right now; this says nothing about the area itself.",
                       "تعذّر تحميل السلسلة الزمنية لهذه المنطقة حاليًا، وهذا لا يدل على شيء بخصوص المنطقة نفسها."),
    "tr_axis_date": ("Image date", "تاريخ الصورة"),
    "tr_axis_val": ("Vegetation index (NDVI)", "مؤشر الغطاء النباتي"),
    "tr_legend_base": ("Dashed line: median of the 3 images before the latest one", "الخط المتقطع: وسيط الصور الثلاث السابقة لأحدث صورة"),
    "ind_col_limit": ("Screening limit (provisional)", "حد الفحص (مؤقت)"),
    "ind_note": ("An indicator is flagged when it passes its screening limit. The limits are provisional and not calibrated in the field; a flag is a reason to look, not a diagnosis.",
                 "يُعلَّم المؤشر عندما يتجاوز حد الفحص. الحدود مؤقتة وغير معايَرة ميدانيًا، والعلامة سبب للفحص وليست تشخيصًا."),
    "tr_baseline": ("Latest value {latest} vs. the median of the preceding images {base}.", "آخر قيمة {latest} مقابل وسيط الصور السابقة {base}."),
    "ind_ndvi": ("Plant cover vs. farm median (ratio)", "الغطاء النباتي مقارنة بوسيط المزرعة (نسبة)"), "ind_ndmi": ("Plant moisture", "رطوبة النبات"),
    "ind_ndre": ("Leaf greenness", "خضرة الأوراق"), "ind_lst": ("Surface temperature vs. farm (°C)", "حرارة السطح مقارنة بالمزرعة (°م)"),
    "ind_dndvi": ("Change since earlier image", "التغير منذ الصورة السابقة"),
    "ind_col_name": ("Indicator", "المؤشر"), "ind_col_value": ("Value", "القيمة"), "ind_col_flag": ("Flagged?", "تجاوز العتبة؟"),
    "flag_yes": ("yes", "نعم"), "flag_no": ("no", "لا"), "flag_na": ("n/a", "غير متاح"),
    "unusual_hint": ("A secondary statistical hint found an unusual pattern here; it does not say what the cause is.",
                     "رصد تحليل إحصائي ثانوي نمطًا غير معتاد هنا، ولا يحدد السبب."),
    # --- about --------------------------------------------------------------
    "about_title": ("About RAY", "عن رَيّ"),
    "about_text": ("RAY helps the farmer know which areas of the farm need inspection, using satellite images, weather data and smart analysis.",
                   "رَيّ يساعد المزارع على معرفة المناطق التي تحتاج إلى فحص في مزرعته باستخدام بيانات الأقمار الصناعية والطقس والتحليل الذكي."),
    "about_not": ("RAY does not replace the field check and does not control the irrigation system.",
                  "رَيّ لا يستبدل الفحص الميداني، ولا يتحكم في نظام الري."),
    "how_title": ("How does RAY work?", "كيف يعمل رَيّ؟"),
    "how_1": ("🛰️ From the sky: find the areas that look unusual.", "🛰️ من السماء: تحديد المناطق التي تظهر فيها مؤشرات غير طبيعية."),
    "how_2": ("📍 The area: start your check here.", "📍 المنطقة: ابدأ الفحص من هنا."),
    "how_3": ('🌱 From the ground: inspect the area and record what you find.', '🌱 من الأرض: افحص المنطقة وسجّل ما وجدته.'),
    "how_4": ("🔍 Analysis: a preliminary suspicion of a possible problem.", "🔍 التحليل: اشتباه مبدئي في مشكلة محتملة."),
    "how_5": ("📋 Check: the things to verify.", "📋 الفحص: الأمور التي ينبغي التحقق منها."),
    "how_6": ("💧 Decision: decide on irrigation after verification.", "💧 القرار: اتخذ قرار الري بعد التحقق."),
    "not_title": ("What RAY does not do", "ما الذي لا يفعله رَيّ"),
    "not_1": ("It does not give a final diagnosis of plant diseases.", "لا يقدم تشخيصًا نهائيًا لأمراض النبات."),
    "not_2": ("It does not set irrigation amounts and does not run the irrigation system.", "لا يحدد كميات الري ولا يشغّل نظام الري."),
    "not_3": ("Satellite images show areas, not individual plants.", "الصور الفضائية تُظهر المناطق، ولا تُظهر النبات الواحد."),
    "privacy_title": ("Your privacy", "خصوصيتك"),
    "privacy_text": ("Inspection records contain only what you type (for example an inspector name, if you enter one) and are not shown to other users.",
                     "تحتوي سجلات الفحص على ما تكتبه فقط (مثل اسم الفاحص إن أدخلته)، ولا تُعرض على المستخدمين الآخرين."),
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
    """Arabic number agreement for 'N area(s) …' (kind: 'check' | 'watch' | 'ok' | 'nodata')."""
    if not is_ar():
        word = {"check": "need inspection", "watch": "need follow-up", "ok": "show no clear abnormal signal",
                "nodata": "cannot be assessed (insufficient data)"}[kind]
        return f"{n} area{'s' if n != 1 else ''} {word}"
    verb = {"check": ("تحتاج إلى فحص", "تحتاجان إلى فحص"), "watch": ("تحتاج إلى متابعة", "تحتاجان إلى متابعة"),
            "ok": ("لا توجد فيها إشارة غير طبيعية واضحة", "لا توجد فيهما إشارة غير طبيعية واضحة"),
            "nodata": ("ببيانات غير كافية للتقييم", "ببيانات غير كافية للتقييم")}[kind]
    if n == 0:
        return {"check": "لا توجد مناطق تحتاج إلى فحص", "watch": "لا توجد مناطق تحتاج إلى متابعة",
                "ok": "لا توجد مناطق خالية من الإشارات غير الطبيعية", "nodata": "لا توجد مناطق ببيانات غير كافية"}[kind]
    if n == 1:
        return f"منطقة واحدة {verb[0]}"
    if n == 2:
        return f"منطقتان {verb[1]}"
    if 3 <= n <= 10:
        return f"{n} مناطق {verb[0]}"
    return f"{n} منطقة {verb[0]}"


def area_noun(n: int) -> str:
    """'N area(s)' with Arabic number agreement (no verb)."""
    if not is_ar():
        return f"{n} area{'s' if n != 1 else ''}"
    if n == 0:
        return "لا توجد مناطق"
    if n == 1:
        return "منطقة واحدة"
    if n == 2:
        return "منطقتان"
    return f"{n} مناطق" if n <= 10 else f"{n} منطقة"
