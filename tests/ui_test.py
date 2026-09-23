"""Headless UI test of every mode / page / language (Streamlit AppTest).

Run from the project root:
    python -m tests.ui_test                 # demo mode + Earth Engine failure path
    python -m tests.ui_test YOUR_PROJECT_ID # additionally Earth Engine mode with real data

It checks that nothing raises, that the right data badge is shown, and that the farmer
views show exactly the classes produced by the unchanged pipeline (no new classification).
"""
import sys

from streamlit.testing.v1 import AppTest

from src import analysis
from src.config import AOI, AOI_PRESETS, DEFAULT_PRESET, Thresholds
from src.demo_data import DemoFarm
from src.preprocessing import make_zone_grid

FAIL = []


def check(cond: bool, msg: str) -> None:
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        FAIL.append(msg)


def text(at) -> str:
    return " ".join(m.value for m in at.markdown) + " " + " ".join(c.value for c in at.caption)


def no_errors(at, where: str) -> None:
    check(not at.exception, f"{where}: no exceptions {[e.value for e in at.exception][:1]}")
    check(not at.error, f"{where}: no error boxes {[e.value for e in at.error][:1]}")


DEMO_SRC, EE_SRC = "Demo mode (simulated data)", "Google Earth Engine (real satellite data)"


def new_app(source: str, project: str | None = None) -> AppTest:
    """Start the app with an explicit data source (and project ID typed into the sidebar field)."""
    at = AppTest.from_file("../app.py", default_timeout=600)
    at.session_state["source"] = source
    at.run()
    if source == EE_SRC and project is not None:
        at.text_input[0].set_value(project).run()
    return at


def run_pages(at, where: str) -> None:
    for page in ("home", "map", "zone", "water", "about"):
        at.session_state["fpage"] = page
        at.run()
        no_errors(at, f"{where} farmer/{page}")
    for lang in ("ar", "en"):
        at.session_state["lang"] = lang
        at.session_state["fpage"] = "home"
        at.run()
        no_errors(at, f"{where} farmer/home lang={lang}")
    check("حالة المزرعة" not in text(at), f"{where}: English restored after switching back")
    at.session_state["lang"] = "ar"
    at.run()
    check("حالة المزرعة" in text(at), f"{where}: Arabic farmer text shown")
    at.session_state["lang"] = "en"
    at.session_state["mode"] = "tech"
    at.run()
    no_errors(at, f"{where} technical")
    labels = [tb.label for tb in at.tabs]
    check(labels[:6] == ["📊 Overview", "🛰️ Satellite Map", "📈 Analytics", "💧 Water Intelligence", "🧠 AI & Method",
                         "⚠️ Limitations"], f"{where}: technical tabs present {labels[:6]}")
    check(any("NOT TRAINED" in m.value for m in at.markdown), f"{where}: Random Forest NOT TRAINED shown")
    words = text(at).lower()
    check(not any(w in words for w in ("balanced accuracy", "precision:", "recall:", "f1:")), f"{where}: no supervised metrics")
    at.session_state["mode"] = "farmer"
    at.run()
    no_errors(at, f"{where} back to farmer")


def expected_demo_classes() -> dict:
    p = AOI_PRESETS[DEFAULT_PRESET]
    aoi = AOI(p["lat"], p["lon"], p["half_km"])
    farm = DemoFarm(tuple(round(b, 6) for b in aoi.bounds))
    d = farm.dates[-1]
    s, _ = analysis.score_zones(farm.zone_stats(make_zone_grid(aoi, 4, 4), d, analysis.pick_previous_date(farm.dates, d)),
                                Thresholds())
    return dict(zip(s.zone_id, s.cls))


def main(project: str | None) -> int:
    # ---- demo mode ----
    at = new_app(DEMO_SRC)
    no_errors(at, "demo home")
    check("DEMO DATA" in text(at), "demo: DEMO DATA badge visible")
    check(at.session_state["mode"] == "farmer", "demo: Farmer mode is the default")
    exp = expected_demo_classes()
    top = sorted([z for z, c in exp.items() if c == "HIGH"])
    check(bool(top) and f"Area {top[0]}" in text(at), f"demo: today's priority matches pipeline HIGH zone {top}")
    at.button(key="b_prio").click().run()
    check(at.session_state["fpage"] == "zone" and at.session_state["zone_sel"] == top[0], "demo: 'Check Priority Area' opens that zone")
    no_errors(at, "demo zone via button")
    at.session_state["fpage"] = "home"
    at.run()
    at.button(key="b_map").click().run()
    check(at.session_state["fpage"] == "map", "demo: 'View Farm Map' navigates")
    at.button(key="b_details").click().run()
    check(at.session_state["fpage"] == "zone", "demo: 'View details' navigates")
    run_pages(at, "demo")

    # ---- Earth Engine selected but failing: explicit error, no silent demo ----
    bad = new_app(EE_SRC, "ray-nonexistent-project-000")
    check(any("could not be loaded" in e.value for e in bad.error), "EE failure: clear error shown")
    check("Real Satellite Data" not in text(bad) and "DEMO DATA" not in text(bad), "EE failure: no results shown silently")
    bad.button(key="b_use_demo").click().run()
    no_errors(bad, "EE failure -> explicit demo")
    check("DEMO DATA" in text(bad), "EE failure: demo only after explicit click")

    # ---- Earth Engine mode (real data) ----
    if project:
        ee = new_app(EE_SRC, project)
        no_errors(ee, "EE home")
        check("Real Satellite Data" in text(ee), "EE: real-data badge visible")
        check("DEMO DATA" not in text(ee), "EE: no demo label in real mode")
        run_pages(ee, "EE")

    print(f"\n{'ALL PASS' if not FAIL else f'{len(FAIL)} FAILURE(S)'}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
