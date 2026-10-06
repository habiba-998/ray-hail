"""Headless test of the farmer-only interface (Streamlit AppTest).

Run from the project root:
    python -m tests.ui_test                 # local demo data + failure path
    python -m tests.ui_test YOUR_PROJECT_ID # additionally real Earth Engine data

Checks: every page renders without exceptions or error boxes; no technical term and no colloquial Arabic is visible;
there is no technical mode; Earth Engine errors are never shown to the farmer; the plant-check rules
(first suspicion / yellowing ambiguity) behave as specified; observations and field results are saved and listed
in the farm record.
"""
import os
import re
import sys
import tempfile

from streamlit.testing.v1 import AppTest

from src import analysis
from src.config import AOI, AOI_PRESETS, DEFAULT_PRESET, Thresholds
from src.demo_data import DemoFarm
from src.preprocessing import make_zone_grid

FAIL = []
PAGES = ["home", "map", "zones", "plant", "water", "log", "about"]
TECH_TERMS = ["Google Earth Engine", "Earth Engine", "Sentinel", "Landsat", "ERA5", "NDVI", "NDRE", "NDMI", "LST",
              "Isolation Forest", "Random Forest", "Demo mode", "DEMO", "Cloud project", "Latitude", "Longitude",
              "AI & Method", "Fusion", "IoT", "Permission", "Technical", "earthengine", "Overview", "Analytics"]
COLLOQUIAL = ["وش", "وين", "تشوف", "اللي", "يبي", "ليش", "ابي", "زين", "مب"]  # matched as whole words


def check(cond: bool, msg: str) -> None:
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        FAIL.append(msg)


def visible_text(at) -> str:
    parts = [m.value for m in at.markdown if "<style" not in m.value]
    parts += [c.value for c in at.caption] + [b.label for b in at.button] + [e.label for e in at.expander]
    parts += [w.label for w in at.radio] + [w.label for w in at.selectbox] + [w.label for w in at.checkbox]
    parts += [str(o) for w in at.radio for o in w.options] + [str(o) for w in at.selectbox for o in w.options]
    parts += [x.value for x in at.info] + [x.value for x in at.warning] + [x.value for x in at.success] + [x.value for x in at.error]
    return " ".join(parts)


def no_errors(at, where: str) -> None:
    check(not at.exception, f"{where}: no exceptions {[e.value for e in at.exception][:1]}")
    check(not at.error, f"{where}: no error boxes {[e.value for e in at.error][:1]}")


def new_app(source: str, project: str | None = None) -> AppTest:
    at = AppTest.from_file("../app.py", default_timeout=600)
    at.session_state["source"] = source
    if project is not None:
        at.session_state["_ee_project_override"] = project
    at.run()
    return at


def expected_demo_top() -> str:
    p = AOI_PRESETS[DEFAULT_PRESET]
    aoi = AOI(p["lat"], p["lon"], p["half_km"])
    farm = DemoFarm(tuple(round(b, 6) for b in aoi.bounds))
    d = farm.dates[-1]
    s, _ = analysis.score_zones(farm.zone_stats(make_zone_grid(aoi, 4, 4), d, analysis.pick_previous_date(farm.dates, d)), Thresholds())
    return str(s.sort_values("score", ascending=False).iloc[0].zone_id)


def run_all(at, where: str) -> None:
    check("mode" not in at.session_state and not at.tabs, f"{where}: no technical mode / tabs")
    for page in PAGES:
        at.session_state["fpage"] = page
        at.run()
        no_errors(at, f"{where} page {page}")
        txt = visible_text(at)
        tech = [w for w in TECH_TERMS if w in txt]
        check(not tech, f"{where} page {page}: no technical terms visible {tech}")
        words = set(re.findall(r"[؀-ۿ]+", txt))
        coll = [w for w in COLLOQUIAL if w in words] + (["فيه منطقة"] if "فيه منطقة" in txt else [])
        check(not coll, f"{where} page {page}: no colloquial Arabic {coll}")
    # irrigation page: decision support, hedged wording, shortcuts to the map / plant check
    at.session_state["fpage"] = "water"
    at.run()
    txt = visible_text(at)
    for phrase in ("حالة الري", "ماذا أفعل الآن؟", "لا تغيّر كمية الري قبل التحقق من السبب ميدانيًا.", "أولًا: نظام الري",
                   "رابعًا: التسميد", "أولوية المناطق", "وليس نظامًا للتحكم التلقائي في الري"):
        check(phrase in txt, f"{where}: irrigation page shows «{phrase}»")
    check("تم تشخيص" not in txt and not {"لتر", "لترات", "م³"} & set(re.findall(r"[؀-ۿ³م]+", txt)), f"{where}: irrigation page gives no diagnosis or water volume")
    btn = [b for b in at.button if b.key == "b_irr_map"]
    if btn:
        check("إجهاد مائي" in txt, f"{where}: possible water stress assessment shown")
        check("الأسباب المحتملة" in txt and "اصفرار" in txt, f"{where}: possible causes + yellowing note shown")
        check("تطور حالة المنطقة" in txt, f"{where}: time-trend section shown")
        at.button(key="b_irr_map").click().run()
        no_errors(at, f"{where} irrigation → map")
        check(at.session_state["fpage"] == "map" and f" {at.session_state['zone_sel']} " in f" {btn[0].label} ",
              f"{where}: 'show on map' opens the map with the priority area selected")
        at.session_state["fpage"] = "water"
        at.run()
        at.button(key="b_irr_plant").click().run()
        no_errors(at, f"{where} irrigation → plant")
        check(at.session_state["fpage"] == "plant", f"{where}: 'plant check' opens the plant page")
    else:
        check("لا توجد اليوم منطقة تحتاج إلى فحص الري" in txt, f"{where}: irrigation page states no area needs a check")
    at.session_state["fpage"] = "home"
    at.run()
    check("ما الذي يحتاج إلى انتباه في مزرعتي؟" in visible_text(at), f"{where}: home question in Standard Arabic")
    check("حالة مزرعتك اليوم" in visible_text(at), f"{where}: farm status summary shown")
    at.button(key="b_prio").click().run()
    check(at.session_state["fpage"] == "zones", f"{where}: 'go to highest priority' opens the zone page")
    txt = visible_text(at)
    for phrase in ("ما السبب المحتمل؟", "هذه النتائج مؤشرات أولية وليست تشخيصًا نهائيًا.", "ما الذي ينبغي فحصه؟",
                   "لا تغيّر كمية الري قبل التحقق من السبب ميدانيًا."):
        check(phrase in txt, f"{where}: zone page shows «{phrase}»")
    at.session_state["crop"] = "date_palm"
    at.run()
    check(any("سوسة النخيل الحمراء" in e.label for e in at.expander), f"{where}: crop-specific problems listed (date palm)")
    # plant check: distinctive symptoms → specific suspicion
    at.session_state["crop"] = "cereals"
    at.session_state["fpage"] = "plant"
    at.run()
    at.checkbox(key="sym_rust_pustules").check()
    at.checkbox(key="sym_streaks").check()
    at.run()
    at.button(key="b_analyze").click().run()
    no_errors(at, f"{where} plant analyse (rust)")
    txt = visible_text(at)
    check("الاشتباه الأول" in txt and "قد يتوافق مع" in txt and "الصدأ المخطط" in txt, f"{where}: first suspicion 'may match' stripe rust")
    check("هذه نتيجة أولية وليست تشخيصًا نهائيًا" in txt, f"{where}: preliminary-result disclaimer shown")
    check("تم تشخيص" not in txt, f"{where}: never says 'diagnosed'")
    at.button(key="b_save_obs").click().run()
    no_errors(at, f"{where} save observation")
    check(bool(at.session_state["plant_result"]["saved_id"]), f"{where}: observation saved to the farm record")
    # yellowing alone → no specific disease, several causes + note
    at.checkbox(key="sym_rust_pustules").uncheck()
    at.checkbox(key="sym_streaks").uncheck()
    at.checkbox(key="sym_yellowing").check()
    at.run()
    at.button(key="b_analyze").click().run()
    txt = visible_text(at)
    check("قد يتوافق مع" not in txt, f"{where}: yellowing alone does not name a specific disease")
    check("اصفرار الأوراق قد يرتبط بعدة أسباب" in txt, f"{where}: yellowing ambiguity note shown")
    # farm record + field validation
    at.session_state["fpage"] = "log"
    at.run()
    no_errors(at, f"{where} farm record")
    check(any("المنطقة" in e.label for e in at.expander), f"{where}: saved observation listed in the farm record")
    sub = [b for b in at.button if "حفظ نتيجة التحقق" in str(b.label)]
    check(bool(sub), f"{where}: field-validation form available in the record")
    if sub:
        sub[0].click().run()
        no_errors(at, f"{where} save field result")
        check(any("تم حفظ نتيجة التحقق" in s.value for s in at.success), f"{where}: field result saved")


def main(project: str | None) -> int:
    os.environ["RAY_DATA_DIR"] = tempfile.mkdtemp(prefix="ray_test_")  # never touch real farmer data
    at = new_app("demo")
    no_errors(at, "demo start")
    check(at.session_state["fpage"] == "home", "app opens on the farmer home page")
    top = expected_demo_top()
    check(f"المنطقة {top}" in visible_text(at), f"demo: highest-priority zone from the pipeline shown ({top})")
    run_all(at, "demo")

    bad = new_app("earth_engine", "ray-nonexistent-project-000")
    txt = visible_text(bad)
    check("تعذّر تحميل بيانات المزرعة حاليًا" in txt, "Earth Engine failure: plain farmer message")
    check(not [w for w in TECH_TERMS if w in txt] and not bad.exception and not bad.error,
          "Earth Engine failure: no technical error or stack trace shown")

    if project:
        ee = new_app("earth_engine", project)
        no_errors(ee, "real-data start")
        check("آخر صورة فضائية لمزرعتك" in visible_text(ee), "real data: satellite image date shown")
        ee.session_state["fpage"] = "map"
        ee.run()
        check(not ee.error and "تعذّر تحميل إحدى طبقات الخريطة" not in visible_text(ee), "real data: map image loads without error")
        run_all(ee, "real")

    print(f"\n{'ALL PASS' if not FAIL else f'{len(FAIL)} FAILURE(S)'}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
