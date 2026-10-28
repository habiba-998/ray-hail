"""Technical details page for advanced users: indices, bands, resolutions, thresholds, data quality rules, models.

Everything here describes what the code actually does (see src/); nothing is claimed that is not implemented.
Bilingual through tr(); the farmer pages stay free of this jargon.
"""
from __future__ import annotations

from dataclasses import asdict

import pandas as pd
import streamlit as st

from .. import config, ml
from ..brand import NAME_AR, NAME_EN
from ..indices import INDEX_INFO
from .common import LIMITATIONS, Ctx, fmt
from .i18n import is_ar, t, tr


def _h(title: str) -> None:
    st.markdown(f"<div class='section-title'>{title}</div>", unsafe_allow_html=True)


def render(c: Ctx) -> None:
    st.markdown(f"<div class='q'>{tr('Technical details', 'التفاصيل التقنية')}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='note-card'>ⓘ {tr('For advanced users. ' + NAME_EN + ' is a screening and prioritisation tool: it is not a plant-disease diagnostic system, not a soil-moisture sensor, not an irrigation controller and has no proven water savings.', 'للمستخدمين المتقدمين. ' + NAME_AR + ' أداة فحص أولي وترتيب أولويات: ليست نظام تشخيص لأمراض النبات، ولا حساس رطوبة تربة، ولا متحكمًا في الري، ولم يثبت لها توفير في المياه.')}</div>", unsafe_allow_html=True)

    st.markdown(f"<div class='section-title'>{t('pipe_title')}</div><div class='pipeline'>"
                + "".join(f"<div class='step'><span class='num'>{i}</span><b>{t(f'pipe_{i}')}</b><small>{t(f'pipe_{i}d')}</small></div>"
                          for i in range(1, 6)) + "</div>", unsafe_allow_html=True)

    _h(tr("This run", "هذه النتيجة"))
    status = tr("REAL (Earth Engine)", "حقيقية (Earth Engine)") if c.use_ee else tr("DEMO (simulated, not a real place)", "تجريبية (محاكاة، ليست مكانًا حقيقيًا)")
    lst_dates = (c.meta or {}).get("lst_dates") or []
    n_pix = len(c.samples) if c.samples is not None else 0
    rows = {
        tr("Data status", "حالة البيانات"): status,
        tr("Sentinel-2 date used", "تاريخ Sentinel-2 المستخدم"): c.date,
        tr("Earlier date for change", "التاريخ السابق لحساب التغير"): c.prev_date or tr("none (≥10 days earlier not available)", "لا يوجد (لا توجد صورة قبل ١٠ أيام أو أكثر)"),
        tr("Landsat thermal dates (±12 days)", "تواريخ Landsat الحرارية (±١٢ يومًا)"): ", ".join(lst_dates) or tr("none available", "غير متاحة"),
        tr("Farm median NDVI (cropped zones)", "وسيط NDVI للمزرعة (المناطق المزروعة)"): fmt(c.ref.get("ndvi_median")),
        tr("Farm mean LST °C", "متوسط حرارة السطح للمزرعة °م"): fmt(c.ref.get("lst_mean"), 1),
        tr("Isolation Forest features / pixels", "ميزات Isolation Forest / عدد البكسلات"): f"{', '.join(c.if_feats) or '—'} / {len(c.pix) if c.pix is not None else 0} ({tr('sampled', 'من أصل')} {n_pix})",
    }
    st.table(pd.Series(rows, name="").to_frame())

    with st.expander(tr("Data sources", "مصادر البيانات"), expanded=False):
        st.markdown(
            f"- **Sentinel-2 L2A** `{config.S2_COLLECTION}` – {tr('surface reflectance, 10–20 m, ~5-day revisit. Used for NDVI/NDRE/NDMI.', 'انعكاس سطحي بدقة ١٠–٢٠ م وزيارة كل ~٥ أيام. يُستخدم لحساب NDVI/NDRE/NDMI.')}\n"
            f"- **Landsat 8/9 C2 L2** `{config.L8_COLLECTION}`, `{config.L9_COLLECTION}` – {tr('surface temperature (ST_B10), 100 m native, composite of ±12 days around the Sentinel-2 date.', 'حرارة السطح (ST_B10) بدقة ١٠٠ م، وهي وسيط لصور ±١٢ يومًا حول تاريخ Sentinel-2.')}\n"
            f"- **ERA5-Land** `{config.ERA5_COLLECTION}` – {tr('daily reanalysis (~11 km). Environmental CONTEXT only; not a field-level soil-moisture measurement.', 'إعادة تحليل يومية (~١١ كم). سياق بيئي فقط وليست قياسًا لرطوبة التربة على مستوى الحقل.')}\n"
            f"- **Sentinel-1** – {tr('not used in scoring.', 'لا يدخل في التقييم.')}\n"
            f"- **Esri World Imagery** – {tr('basemap only.', 'خريطة أساس فقط.')}")

    with st.expander(tr("Indices, bands and resolution", "المؤشرات والحزم والدقة المكانية"), expanded=False):
        res = {"NDVI": "B8 10 m, B4 10 m", "NDRE": "B8 10 m, B5 20 m", "NDMI": "B8 10 m, B11 20 m", "LST": "ST_B10 100 m (native)"}
        for k, v in INDEX_INFO.items():
            st.markdown(f"**{k}** – {v['ar'] if is_ar() else v['name']}  \n`{v['formula']}`  \n{tr('Native resolution', 'الدقة الأصلية')}: {res[k]}")
        st.caption(tr("The indices do NOT share one resolution. Earth Engine resamples the 20 m bands when they are combined with 10 m bands, and zone statistics are reduced at 20 m. These indices are proxies for canopy condition; they are not measurements of root-zone soil moisture or delivered irrigation volume.",
                      "لا تتشارك المؤشرات الدقة نفسها. يعيد Earth Engine أخذ عينات الحزم ٢٠ م عند دمجها مع حزم ١٠ م، وتُحسب إحصاءات المناطق بدقة ٢٠ م. هذه المؤشرات بدائل لحالة الغطاء النباتي وليست قياسًا لرطوبة منطقة الجذور أو لكمية الري."))

    with st.expander(tr("Data quality rules", "قواعد جودة البيانات"), expanded=False):
        st.markdown(
            f"- {tr('Sentinel-2 pixels with SCL classes', 'تُستبعد بكسلات Sentinel-2 ذات فئات SCL')} {config.S2_SCL_INVALID} {tr('(no data, saturated, cloud shadow, medium/high cloud, thin cirrus, snow) are masked.', '(بلا بيانات، مشبعة، ظل سحاب، سحب متوسطة/كثيفة، سحب رقيقة، ثلج).')}\n"
            f"- {tr('Landsat: dilated cloud, cirrus, cloud and cloud shadow bits of QA_PIXEL are masked; scene cloud cover < 60 %.', 'Landsat: تُستبعد بتات السحب الموسعة والسحب الرقيقة والسحب وظل السحب في QA_PIXEL، مع نسبة سحب للمشهد أقل من ٦٠٪.')}\n"
            f"- {tr('A date is used only if the farm area is at least', 'لا يُستخدم تاريخ إلا إذا كانت منطقة المزرعة صافية بنسبة')} {config.MIN_CLEAR_FRACTION:.0%} {tr('clear.', 'على الأقل.')}\n"
            f"- {tr('A zone is a crop zone if at least', 'تُعدّ المنطقة مزروعة إذا كان')} {config.MIN_VEG_FRACTION:.0%} {tr('of its clear pixels have NDVI >', 'على الأقل من بكسلاتها الصافية بقيمة NDVI أكبر من')} {config.VEG_NDVI_MIN}.\n"
            f"- {tr('A zone needs ≥', 'تحتاج المنطقة إلى')} {config.MIN_INDICATORS} {tr('evaluable indicators, otherwise it is “Insufficient data” (a single indicator never decides a class).', 'مؤشرات قابلة للتقييم على الأقل، وإلا فهي «بيانات غير كافية» (لا يحسم مؤشر واحد الفئة).')}\n"
            f"- {tr('The time series uses only dates that are ≥', 'تستخدم السلسلة الزمنية التواريخ التي تزيد نسبة صفائها عن')} {config.TS_MIN_CLEAR_FRACTION:.0%} {tr('clear and averages ALL clear pixels of the zone (including bare soil), unlike the current-date statistics that use crop pixels only.', 'فقط وتحسب متوسط كل البكسلات الصافية في المنطقة (بما فيها التربة العارية)، بخلاف إحصاءات التاريخ الحالي التي تستخدم بكسلات المحصول فقط.')}")

    with st.expander(tr("Zone geometry", "هندسة المناطق"), expanded=False):
        st.markdown(tr("Zones are a regular 4×4 grid over a square area (~4 km × 4 km). They are an analysis grid, not verified field, parcel or irrigation-pivot boundaries; one pivot can span several zones and one zone can contain several fields. Real boundaries are required before any statement about a specific pivot.",
                       "المناطق شبكة منتظمة ٤×٤ فوق مربع (~٤ كم × ٤ كم). هي شبكة تحليل وليست حدود حقول أو قطع أو محاور ري موثّقة؛ فقد يمتد محور واحد على عدة مناطق وقد تضم منطقة واحدة عدة حقول. تلزم الحدود الفعلية قبل أي حديث عن محور محدد."))

    with st.expander(tr("Thresholds and priority index (provisional)", "العتبات ومؤشر الأولوية (مؤقتة)"), expanded=False):
        st.warning(tr("All thresholds are provisional screening rules. They are NOT calibrated against field data in Hail and are the same for every crop.",
                      "كل العتبات قواعد فحص أولية مؤقتة، وغير معايَرة ميدانيًا في حائل، وهي نفسها لكل المحاصيل."))
        st.dataframe(pd.DataFrame([{"parameter": k, "value": v} for k, v in asdict(c.thr).items()]), hide_index=True)
        st.markdown(tr("Priority index = points ÷ maximum possible points over the indicators that could be evaluated (each indicator gives 0, 1 or 2 points). It orders zones for inspection; it is a heuristic, **not a probability**, and it is not calibrated. Class: index ≥ red_share → needs inspection; ≥ yellow_share → needs follow-up.",
                       "مؤشر الأولوية = النقاط ÷ أقصى نقاط ممكنة للمؤشرات التي أمكن تقييمها (كل مؤشر يعطي ٠ أو ١ أو ٢). يرتب المناطق للفحص، وهو قاعدة تقريبية **وليس احتمالًا** وغير معايَر. الفئة: المؤشر ≥ red_share → يحتاج إلى فحص؛ ≥ yellow_share → يحتاج إلى متابعة."))

    with st.expander(tr("Temporal analysis", "التحليل عبر الزمن"), expanded=False):
        st.markdown(tr(f"For one zone, the latest NDVI is compared with the median of the up-to-3 preceding clear observations of the SAME zone. It needs at least {config.TREND_MIN_OBS} clear observations, otherwise the result is “insufficient data”. A drop larger than {config.TREND_DROP} (provisional) is a decline; if the previous observation was also lower, it is a repeated decline. No seasonal baseline, crop type or growth stage is modelled, so harvest, cutting, planting and phenology also appear as changes.",
                       f"لمنطقة واحدة، تُقارَن أحدث قيمة NDVI بوسيط ما يصل إلى ٣ ملاحظات صافية سابقة للمنطقة نفسها. يلزم {config.TREND_MIN_OBS} ملاحظات صافية على الأقل وإلا فالنتيجة «بيانات غير كافية». الانخفاض الذي يتجاوز {config.TREND_DROP} (قيمة مؤقتة) يُعد تراجعًا، وإذا كانت الملاحظة السابقة أقل أيضًا فهو تراجع متكرر. لا تُنمذج خطوط أساس موسمية ولا نوع المحصول ولا مرحلة النمو، لذلك يظهر الحصاد والحش والزراعة والتغيرات الموسمية أيضًا كتغيرات."))

    with st.expander("Isolation Forest", expanded=False):
        st.markdown(tr(f"Unsupervised detector of unusual combinations of NDVI/NDRE/NDMI(/LST) among the cropped pixels sampled from THIS farm on THIS date (reference population = the farm itself). `contamination={ml.IF_CONTAMINATION}` fixes that ~{ml.IF_CONTAMINATION:.0%} of pixels are flagged by construction, so the flagged share is a model setting, not a finding; a zone matters only when its share is well above that. Zones with fewer than {config.MIN_ZONE_PIXELS} sampled pixels get no value. It is a secondary hint: it is not a probability of water stress and does not identify a cause.",
                       f"كاشف غير مُشرَف لتركيبات غير معتادة من NDVI/NDRE/NDMI(/LST) بين بكسلات المحصول المأخوذة من هذه المزرعة في هذا التاريخ (المجتمع المرجعي هو المزرعة نفسها). يثبّت `contamination={ml.IF_CONTAMINATION}` أن نحو {ml.IF_CONTAMINATION:.0%} من البكسلات تُعلَّم بحكم التصميم، فالنسبة إعداد للنموذج وليست نتيجة؛ وتهم المنطقة فقط حين تكون نسبتها أعلى كثيرًا. المناطق التي تقل بكسلاتها المأخوذة عن {config.MIN_ZONE_PIXELS} لا تُعطى قيمة. هو تلميح ثانوي: ليس احتمالًا للإجهاد المائي ولا يحدد السبب."))
        if c.pix is not None and len(c.pix):
            st.caption(tr(f"This run: {len(c.pix)} pixels, {int(c.pix.anomaly.sum())} flagged.", f"في هذه النتيجة: {len(c.pix)} بكسلًا، عُلِّم منها {int(c.pix.anomaly.sum())}."))
        else:
            st.caption(tr("This run: the model did not run (not enough pixels or an error); results above do not use it.", "في هذه النتيجة: لم يعمل النموذج (بكسلات غير كافية أو خطأ)، ولا تستخدمه النتائج أعلاه."))

    with st.expander("Random Forest", expanded=False):
        sup = ml.supervised_status()
        st.markdown(tr("**Not trained and not used.** No verified field labels exist, so no supervised model is trained and no accuracy, precision or recall can be reported. The training code is dormant and is never called by the app.",
                       "**غير مدرّب وغير مستخدم.** لا توجد بيانات ميدانية موثّقة، لذلك لا يُدرَّب أي نموذج إشرافي ولا يمكن ذكر دقة أو استدعاء أو ضبط. شيفرة التدريب خاملة ولا يستدعيها التطبيق."))
        st.caption(sup.get("reason", ""))

    with st.expander(tr("Limitations", "القيود"), expanded=False):
        st.markdown("\n".join(f"- {ar if is_ar() else en}" for en, ar in LIMITATIONS))
