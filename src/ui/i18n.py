"""Farmer-facing text in English and Arabic.

Only wording lives here. Every status shown with these strings comes from the
existing RAY classes (HEALTHY / MODERATE / HIGH / NO_CROP / NO_DATA) and the
existing rule points -- no new classification is introduced.
"""
from __future__ import annotations

import streamlit as st

S: dict[str, tuple[str, str]] = {
    # --- chrome -------------------------------------------------------------
    "subtitle": ("Satellite-powered irrigation intelligence for your farm.", "ذكاء الري لمزرعتك بقوة الأقمار الصناعية."),
    "mode_farmer": ("👨‍🌾 Farmer", "👨‍🌾 المزارع"),
    "mode_tech": ("🔬 Technical", "🔬 فني"),
    "badge_real": ("🛰️ Google Earth Engine — Real Satellite Data · Sentinel-2 image of {date}",
                   "🛰️ Google Earth Engine — بيانات أقمار صناعية حقيقية · صورة Sentinel-2 بتاريخ {date}"),
    "badge_demo": ("⚠️ DEMO DATA — simulated farm, not real satellite observations",
                   "⚠️ بيانات تجريبية (DEMO DATA) — مزرعة محاكاة وليست رصدًا حقيقيًا بالأقمار الصناعية"),
    "tech_lang_note": ("Technical analysis is presented in English.", "يُعرض التحليل الفني باللغة الإنجليزية."),
    # --- navigation ---------------------------------------------------------
    "nav_home": ("🏠 Home", "🏠 الرئيسية"),
    "nav_map": ("🗺️ Farm Map", "🗺️ خريطة المزرعة"),
    "nav_zone": ("📍 Zone Details", "📍 تفاصيل المنطقة"),
    "nav_water": ("💧 Irrigation", "💧 الري"),
    "nav_about": ("ℹ️ About", "ℹ️ حول"),
    # --- home ---------------------------------------------------------------
    "farm_status": ("Farm Status", "حالة المزرعة"),
    "status_RED": ("Area needs inspection", "منطقة تحتاج إلى فحص"),
    "status_YELLOW": ("Some areas need attention", "بعض المناطق تحتاج متابعة"),
    "status_GREEN": ("Farm looks healthy", "المزرعة تبدو بحالة جيدة"),
    "status_NONE": ("No active crop to assess", "لا يوجد محصول نشط للتقييم"),
    "status_sub": ("{n_bad} of {n_crop} crop areas flagged · satellite image of {date}",
                   "{n_bad} من {n_crop} مناطق زراعية تحتاج انتباهًا · صورة الأقمار الصناعية بتاريخ {date}"),
    "todays_priority": ("Today's Priority", "أولوية اليوم"),
    "no_priority": ("No area needs inspection today. Continue regular monitoring.",
                    "لا توجد منطقة تحتاج إلى فحص اليوم. استمر في المتابعة المعتادة."),
    "screening_note": ("Satellite screening signal — not a confirmed field diagnosis.",
                       "إشارة فحص من الأقمار الصناعية — وليست تشخيصًا ميدانيًا مؤكدًا."),
    "btn_map": ("🗺️ View Farm Map", "🗺️ عرض خريطة المزرعة"),
    "btn_priority": ("📍 Check Priority Area", "📍 فحص المنطقة المهمة"),
    "btn_water": ("💧 Irrigation Guidance", "💧 إرشادات الري"),
    "btn_tech": ("🔬 Technical Analysis", "🔬 التحليل الفني"),
    "chips": ("{h} healthy · {m} need attention · {r} inspect · {n} no crop",
              "{h} جيدة · {m} تحتاج متابعة · {r} للفحص · {n} بدون محصول"),
    "also_look": ("Also worth a look", "تستحق نظرة أيضًا"),
    "anomaly_note": ("{z} is not classified as water stressed by the current rules, but the anomaly detector found an "
                     "unusual satellite pattern here ({p}% of sampled crop pixels). It may be worth a look on your next visit.",
                     "المنطقة {z} غير مصنفة كمجهدة مائيًا وفق القواعد الحالية، لكن كاشف الأنماط غير المعتادة رصد نمطًا "
                     "غير معتاد فيها ({p}% من بكسلات المحصول المفحوصة). قد تستحق نظرة في زيارتك القادمة."),
    # --- zone classes (farmer wording of the existing classes) --------------
    "cls_HIGH": ("Potential water stress", "إجهاد مائي محتمل"),
    "cls_MODERATE": ("Needs attention", "تحتاج متابعة"),
    "cls_HEALTHY": ("Healthy", "جيدة"),
    "cls_NO_CROP": ("No active crop", "لا يوجد محصول نشط"),
    "cls_NO_DATA": ("Not enough clear data", "لا توجد بيانات كافية"),
    "short_HIGH": ("Inspect", "افحص"),
    "short_MODERATE": ("Watch", "تابِع"),
    "short_HEALTHY": ("OK", "جيدة"),
    "short_NO_CROP": ("No crop", "بدون محصول"),
    "short_NO_DATA": ("No data", "لا بيانات"),
    "mean_HIGH": ("Satellite indicators show a pattern that may be associated with water stress.",
                  "تُظهر مؤشرات الأقمار الصناعية نمطًا قد يرتبط بالإجهاد المائي."),
    "mean_MODERATE": ("Some satellite indicators are weaker here than in the rest of the farm.",
                      "بعض مؤشرات الأقمار الصناعية هنا أضعف من بقية المزرعة."),
    "mean_HEALTHY": ("Satellite indicators look similar to the healthy parts of the farm.",
                     "مؤشرات الأقمار الصناعية مشابهة للأجزاء الجيدة من المزرعة."),
    "mean_NO_CROP": ("No active crop canopy was detected in this area.", "لم يُرصد غطاء محصولي نشط في هذه المنطقة."),
    "mean_NO_DATA": ("Clouds or missing data — no reliable reading on this date.",
                     "غيوم أو بيانات ناقصة — لا توجد قراءة موثوقة في هذا التاريخ."),
    "do_HIGH": ("Inspect irrigation in this area before applying additional water.",
                "افحص نظام الري في هذه المنطقة قبل إضافة مياه."),
    "do_MODERATE": ("Inspect irrigation and field conditions in this area.",
                    "افحص نظام الري وحالة الحقل في هذه المنطقة."),
    "do_HEALTHY": ("No action needed. Continue regular monitoring.", "لا حاجة لأي إجراء. استمر في المتابعة المعتادة."),
    "do_NO_CROP": ("If this area is being irrigated, check whether that water is needed.",
                   "إذا كانت هذه المنطقة تُروى، تحقّق من الحاجة إلى تلك المياه."),
    "do_NO_DATA": ("Choose another date or check again after the next satellite image.",
                   "اختر تاريخًا آخر أو أعد الفحص بعد صورة الأقمار الصناعية القادمة."),
    # --- map / zone ---------------------------------------------------------
    "map_view": ("Map view", "عرض الخريطة"),
    "view_status": ("🟩 Farm status", "🟩 حالة المزرعة"),
    "view_photo": ("🛰️ Satellite photo", "🛰️ صورة القمر الصناعي"),
    "map_help": ("Tap any square on the map to see that area.", "اضغط على أي مربع في الخريطة لعرض تلك المنطقة."),
    "zone": ("Area", "المنطقة"),
    "status": ("Status", "الحالة"),
    "score": ("RAY score", "مؤشر RAY"),
    "what_means": ("What this means", "ماذا يعني هذا"),
    "what_do": ("What to do", "ماذا تفعل"),
    "view_details": ("View details →", "عرض التفاصيل ←"),
    "choose_area": ("Choose an area", "اختر منطقة"),
    "signals": ("Satellite signals for this area", "إشارات الأقمار الصناعية لهذه المنطقة"),
    "sig_veg": ("Vegetation condition", "حالة النباتات"),
    "sig_moist": ("Moisture signal", "إشارة الرطوبة"),
    "sig_temp": ("Temperature signal", "إشارة الحرارة"),
    "sig_change": ("Recent change", "التغير الأخير"),
    "veg_0": ("Similar to the rest of the farm", "مماثلة لبقية المزرعة"),
    "veg_1": ("Slightly weaker than the rest of the farm", "أضعف قليلًا من بقية المزرعة"),
    "veg_2": ("Weaker than the rest of the farm", "أضعف من بقية المزرعة"),
    "moist_0": ("Normal", "طبيعية"),
    "moist_1": ("Lower than expected", "أقل من المتوقع"),
    "moist_2": ("Low", "منخفضة"),
    "temp_0": ("Normal", "طبيعية"),
    "temp_1": ("Warmer than the farm average", "أدفأ من متوسط المزرعة"),
    "temp_2": ("Much warmer than the farm average", "أدفأ بكثير من متوسط المزرعة"),
    "change_0": ("Stable", "مستقرة"),
    "change_1": ("Slight decline", "تراجع طفيف"),
    "change_2": ("Sharp decline — check whether it was harvested or cut", "تراجع حاد — تحقّق مما إذا تم الحصاد أو القص"),
    "na": ("Not available", "غير متوفرة"),
    "tech_expander": ("🔬 Technical satellite indicators", "🔬 المؤشرات الفنية للأقمار الصناعية"),
    "go_water": ("💧 Irrigation guidance for this area", "💧 إرشادات الري لهذه المنطقة"),
    # --- irrigation ---------------------------------------------------------
    "irr_title": ("💧 Irrigation Check", "💧 فحص الري"),
    "priority": ("Priority", "الأولوية"),
    "prio_HIGH": ("HIGH", "عالية"),
    "prio_MODERATE": ("MEDIUM", "متوسطة"),
    "recommendation": ("Recommendation", "التوصية"),
    "why": ("Why?", "لماذا؟"),
    "why_HIGH": ("Multiple satellite indicators show a pattern associated with potential water stress.",
                 "عدة مؤشرات من الأقمار الصناعية تُظهر نمطًا مرتبطًا بإجهاد مائي محتمل."),
    "why_MODERATE": ("Some satellite indicators are weaker than in the rest of the farm.",
                     "بعض مؤشرات الأقمار الصناعية أضعف من بقية المزرعة."),
    "important": ("Important: this is a remote-sensing screening signal, not a field diagnosis. The same signs can come "
                  "from heat, disease, nutrient shortage, salinity, pests or a recent harvest.",
                  "مهم: هذه إشارة فحص عن بُعد وليست تشخيصًا ميدانيًا. قد تنتج العلامات نفسها عن الحرارة أو الأمراض أو "
                  "نقص العناصر الغذائية أو الملوحة أو الآفات أو حصاد حديث."),
    "no_volume": ("RAY does not calculate how much water to apply.", "لا يحسب RAY كمية المياه الواجب إضافتها."),
    "checklist": ("What to check in the field", "ماذا تفحص في الحقل"),
    "chk_1": ("Sprinklers, nozzles and pipes — blockages or leaks", "الرشاشات والفوهات والأنابيب — انسداد أو تسريب"),
    "chk_2": ("Water pressure, and whether the pivot completes its full circle", "ضغط المياه، وهل يُكمل المحور دورته كاملة"),
    "chk_3": ("Dry patches or wilting plants in the area", "بقع جافة أو نباتات ذابلة في المنطقة"),
    "chk_4": ("Recent harvest or cutting, pests or disease", "حصاد أو قص حديث، أو آفات أو أمراض"),
    "reason_NDMI (canopy water)": ("Moisture signal is lower than expected", "إشارة الرطوبة أقل من المتوقع"),
    "reason_NDRE (chlorophyll)": ("Leaf greenness is lower than expected", "خُضرة الأوراق أقل من المتوقع"),
    "reason_NDVI vs farm median": ("Vegetation is weaker than the rest of the farm", "النباتات أضعف من بقية المزرعة"),
    "reason_LST vs farm mean (°C)": ("The area is warmer than the farm average", "المنطقة أدفأ من متوسط المزرعة"),
    "reason_NDVI change (~2 weeks)": ("Vegetation declined in the last ~2 weeks", "تراجعت النباتات خلال الأسبوعين الماضيين تقريبًا"),
    "no_crop_title": ("Areas with no active crop", "مناطق بدون محصول نشط"),
    "no_crop_text": ("No crop canopy was detected in: {zones}. If these areas are still being irrigated, that water may not be needed.",
                     "لم يُرصد غطاء محصولي في: {zones}. إذا كانت هذه المناطق لا تزال تُروى، فقد لا تكون تلك المياه ضرورية."),
    "all_good": ("No area needs an irrigation check on this date.", "لا توجد منطقة تحتاج إلى فحص الري في هذا التاريخ."),
    "how_helps": ("How RAY helps you use water better", "كيف يساعدك RAY على استخدام المياه بشكل أفضل"),
    "help_1": ("Check the flagged areas first instead of walking every field.", "افحص المناطق المُشار إليها أولًا بدلًا من المرور على كل الحقول."),
    "help_2": ("Fix blocked nozzles or low pressure before adding more water.", "أصلح الفوهات المسدودة أو الضغط المنخفض قبل إضافة مياه أكثر."),
    "help_3": ("Avoid watering areas with no active crop.", "تجنّب ري المناطق التي لا يوجد بها محصول نشط."),
    "help_note": ("RAY is designed to support more efficient irrigation decisions. Water savings have not been measured.",
                  "صُمّم RAY لدعم قرارات ري أكثر كفاءة. لم يتم قياس توفير المياه بعد."),
    # --- about --------------------------------------------------------------
    "about_title": ("About RAY", "حول RAY"),
    "about_text": ("RAY looks at your farm with free satellite images. It compares each area with the rest of the farm and "
                   "points out where to look first. It does not replace a visit to the field.",
                   "يراقب RAY مزرعتك باستخدام صور الأقمار الصناعية المجانية، ويقارن كل منطقة ببقية المزرعة، ويحدد أين تبدأ "
                   "الفحص أولًا. لا يغني عن زيارة الحقل."),
    "how_status": ("How the colours are decided", "كيف تُحدَّد الألوان"),
    "how_status_text": ("Each area gets points from five satellite signals (moisture, leaf greenness, vegetation compared "
                        "with the farm, temperature, and recent change). More points = higher concern. The rules are "
                        "transparent and can be seen in Technical mode.",
                        "تحصل كل منطقة على نقاط من خمس إشارات (الرطوبة، خُضرة الأوراق، النباتات مقارنة بالمزرعة، الحرارة، "
                        "والتغير الأخير). كلما زادت النقاط زاد القلق. القواعد واضحة ويمكن الاطلاع عليها في الوضع الفني."),
    "limits_title": ("Limitations", "القيود"),
    "data_title": ("Where the data comes from", "مصدر البيانات"),
    # --- errors -------------------------------------------------------------
    "ee_fail_title": ("Real satellite data could not be loaded.", "تعذّر تحميل بيانات الأقمار الصناعية الحقيقية."),
    "ee_fail_text": ("Google Earth Engine is not connected, so no farm results are shown. You can fix the connection "
                     "(details below) or switch to Demo Mode, which uses clearly labelled simulated data.",
                     "Google Earth Engine غير متصل، لذلك لا تُعرض أي نتائج للمزرعة. يمكنك إصلاح الاتصال (التفاصيل أدناه) "
                     "أو التبديل إلى الوضع التجريبي الذي يستخدم بيانات محاكاة موضّحة بوضوح."),
    "use_demo": ("Use Demo Mode (simulated data)", "استخدم الوضع التجريبي (بيانات محاكاة)"),
}


def lang() -> str:
    return st.session_state.get("lang", "en")


def is_ar() -> bool:
    return lang() == "ar"


def ltr(s) -> str:
    """Isolate numbers/dates so they read correctly inside right-to-left text."""
    return f"<bdi dir='ltr' style='white-space:nowrap'>{s}</bdi>"


def tr(en: str, ar: str) -> str:
    """Inline bilingual text for one-off strings."""
    return ar if is_ar() else en


def t(key: str, **kw) -> str:
    en, ar = S[key]
    s = ar if is_ar() else en
    if kw and "date" in kw:  # keep ISO dates left-to-right (and unbroken) inside Arabic sentences
        kw = {**kw, "date": f"<bdi dir='ltr' style='white-space:nowrap'>{kw['date']}</bdi>"}
    return s.format(**kw) if kw else s
