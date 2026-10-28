"""Pytest unit tests for the scientific core (no Streamlit, no Earth Engine, no network).

Run from the project root:  python -m pytest tests/test_satra.py -q
Synthetic arrays/tables below are TEST FIXTURES only; they are never shown to users as data.
"""
import datetime as dt
import re

import numpy as np
import pandas as pd
import pytest

from src import analysis, ml, status, validation
from src.config import MIN_INDICATORS, Thresholds
from src.indices import compute_indices, normalized_difference
from src.preprocessing import make_zone_grid
from src.config import AOI
from src.storage import SQLiteStore, validate_record


# ------------------------------------------------------------------ index calculations
def test_ndvi_ndre_ndmi_formulas():
    b = {k: np.array([[v]], dtype="float32") for k, v in {"B4": 0.1, "B5": 0.2, "B8": 0.5, "B11": 0.25}.items()}
    idx = compute_indices(b)
    assert idx["NDVI"][0, 0] == pytest.approx((0.5 - 0.1) / (0.5 + 0.1))   # (B8-B4)/(B8+B4)
    assert idx["NDRE"][0, 0] == pytest.approx((0.5 - 0.2) / (0.5 + 0.2))   # (B8-B5)/(B8+B5)
    assert idx["NDMI"][0, 0] == pytest.approx((0.5 - 0.25) / (0.5 + 0.25)) # (B8-B11)/(B8+B11)


def test_normalized_difference_handles_zero_and_nan():
    out = normalized_difference(np.array([0.0, np.nan, 0.4]), np.array([0.0, 0.2, 0.2]))
    assert np.isnan(out[0]) and np.isnan(out[1]) and out[2] == pytest.approx(1 / 3)


# ------------------------------------------------------------------ zone scoring
def _zone(**kw):
    base = dict(zone_id="A1", clear_frac=1.0, veg_frac=0.8, ndvi=0.6, ndre=0.4, ndmi=0.3, lst=35.0, ndvi_prev=0.6)
    base.update(kw)
    return base


def _score(*zones):
    out, ref = analysis.score_zones(pd.DataFrame(list(zones)), Thresholds())
    return out.set_index("zone_id"), ref


def test_healthy_zone_has_no_flagged_indicators():
    out, _ = _score(_zone(zone_id="A1"), _zone(zone_id="A2"))
    assert out.loc["A1", "cls"] == "HEALTHY" and out.loc["A1", "n_flagged"] == 0


def test_clearly_stressed_zone_is_flagged_for_inspection():
    stressed = _zone(zone_id="A2", ndvi=0.35, ndre=0.15, ndmi=0.0, lst=42.0, ndvi_prev=0.6)
    out, _ = _score(_zone(zone_id="A1"), _zone(zone_id="A3"), stressed)
    assert out.loc["A2", "cls"] == "HIGH"
    assert out.loc["A2", "n_flagged"] >= 3 and out.loc["A2", "n_signals"] == 5


def test_too_few_indicators_gives_insufficient_data_not_a_class():
    # only NDMI available (below the high threshold): a single indicator must not decide the class
    z = _zone(zone_id="A2", ndre=np.nan, ndmi=0.0, lst=np.nan, ndvi_prev=np.nan)
    out, _ = _score(_zone(zone_id="A1"), z)
    # NDVI still gives ndvi_rel, so 2 indicators (< MIN_INDICATORS=3)
    assert out.loc["A2", "n_signals"] < MIN_INDICATORS
    assert out.loc["A2", "cls"] == "NO_DATA"


def test_cloudy_zone_is_insufficient_data():
    out, _ = _score(_zone(zone_id="A1"), _zone(zone_id="A2", clear_frac=0.2))
    assert out.loc["A2", "cls"] == "NO_DATA"


def test_zone_without_crop_is_not_a_stress_class():
    out, _ = _score(_zone(zone_id="A1"), _zone(zone_id="A2", veg_frac=0.0, ndvi=np.nan, ndre=np.nan, ndmi=np.nan, lst=np.nan))
    assert out.loc["A2", "cls"] == "NO_CROP"


def test_empty_and_all_invalid_farm_does_not_crash():
    out, ref = _score(_zone(zone_id="A1", clear_frac=0.0, veg_frac=0.0, ndvi=np.nan, ndre=np.nan, ndmi=np.nan, lst=np.nan, ndvi_prev=np.nan))
    assert out.loc["A1", "cls"] == "NO_DATA" and np.isnan(ref["ndvi_median"])


def test_priority_index_is_a_share_of_points_not_a_percentage():
    out, _ = _score(_zone(zone_id="A1"), _zone(zone_id="A2", ndmi=0.0))
    s = out.loc["A2", "score"]
    assert 0.0 <= s <= 1.0 and s == pytest.approx(out.loc["A2", "points"] / out.loc["A2", "max_points"])


# ------------------------------------------------------------------ temporal analysis
def _series(vals, start="2026-06-01", step=5):
    return pd.DataFrame({"date": pd.date_range(start, periods=len(vals), freq=f"{step}D"), "NDVI": vals})


def test_temporal_insufficient_with_few_observations():
    s = analysis.temporal_summary(_series([0.6, 0.6, 0.5]), "2026-12-31")
    assert s["status"] == "insufficient" and s["n"] == 3


def test_temporal_stable_decline_and_persistent_decline():
    assert analysis.temporal_summary(_series([0.6, 0.61, 0.6, 0.59, 0.6]), "2026-12-31")["status"] == "stable"
    assert analysis.temporal_summary(_series([0.6, 0.61, 0.6, 0.6, 0.45]), "2026-12-31")["status"] == "decline"
    assert analysis.temporal_summary(_series([0.6, 0.61, 0.6, 0.45, 0.44]), "2026-12-31")["status"] == "persistent_decline"


def test_temporal_flags_values_below_the_earlier_peak_without_a_recent_drop():
    # growth to a plateau, an older sharp drop, then a flat recent period: short-term "stable" would hide the drop
    s = analysis.temporal_summary(_series([0.3, 0.4, 0.5, 0.6, 0.6, 0.6, 0.6, 0.45, 0.45, 0.44, 0.44]), "2026-12-31")
    assert s["status"] == "below_earlier" and s["earlier_peak"] == pytest.approx(0.6)


def test_temporal_peak_ignores_a_single_noisy_spike():
    s = analysis.temporal_summary(_series([0.4, 0.4, 0.9, 0.4, 0.4, 0.4, 0.4, 0.4]), "2026-12-31")
    assert s["status"] == "stable"


def test_temporal_ignores_observations_after_the_analysis_date_and_nan():
    ts = _series([0.6, np.nan, 0.6, 0.6, 0.6, 0.2])
    s = analysis.temporal_summary(ts, "2026-06-16")   # excludes later (collapsed) observations and the NaN
    assert s["n"] == 3 and s["status"] == "insufficient"
    assert analysis.temporal_summary(pd.DataFrame(), "2026-06-16")["status"] == "insufficient"
    assert analysis.temporal_summary(None, "2026-06-16")["status"] == "insufficient"


def test_previous_date_requires_minimum_gap():
    assert analysis.pick_previous_date(["2026-09-01", "2026-09-15", "2026-09-20"], "2026-09-20") == "2026-09-01"
    assert analysis.pick_previous_date(["2026-09-18", "2026-09-20"], "2026-09-20") is None


# ------------------------------------------------------------------ Isolation Forest
def _samples(n, seed=0, outliers=0):
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({"lon": rng.uniform(0, 1, n), "lat": rng.uniform(0, 1, n), "NDVI": rng.normal(0.7, 0.03, n),
                       "NDRE": rng.normal(0.5, 0.03, n), "NDMI": rng.normal(0.3, 0.03, n)})
    df.loc[:outliers - 1, ["NDVI", "NDRE", "NDMI"]] = [0.3, 0.1, -0.1]
    return df


def test_isolation_forest_needs_enough_samples():
    pix, feats = ml.isolation_forest(_samples(20))
    assert pix.empty and feats


def test_isolation_forest_handles_missing_feature_columns_and_empty_input():
    pix, feats = ml.isolation_forest(pd.DataFrame())
    assert pix.empty and feats == []
    s = _samples(200).drop(columns=["NDRE"])
    pix, feats = ml.isolation_forest(s)
    assert "NDRE" not in feats and len(pix) == 200


def test_isolation_forest_flags_roughly_the_contamination_share_and_outliers():
    pix, _ = ml.isolation_forest(_samples(400, outliers=12))
    assert pix.anomaly.mean() == pytest.approx(ml.IF_CONTAMINATION, abs=0.02)   # fixed by the model setting
    assert pix.loc[:11, "anomaly"].all()


def test_zone_share_is_nan_when_too_few_pixels():
    zones = make_zone_grid(AOI(27.4, 42.5, 2.0), 1, 2)
    b = (zones.min_lon.min(), zones.min_lat.min(), zones.max_lon.max(), zones.max_lat.max())
    left = zones.iloc[0]
    pix = pd.DataFrame({"lon": [left.min_lon + 1e-4] * 5, "lat": [left.min_lat + 1e-4] * 5, "anomaly": [True] * 5})
    share = ml.anomaly_share_by_zone(pix, zones, min_pixels=30)
    assert share.isna().all() and b
    assert ml.anomaly_share_by_zone(pd.DataFrame(), zones).empty


def test_random_forest_is_not_trained_without_labels(tmp_path, monkeypatch):
    monkeypatch.setattr(ml, "LABELS_PATH", tmp_path / "labels.csv")
    assert ml.supervised_status()["ready"] is False


# ------------------------------------------------------------------ real / demo / unavailable states
def test_source_selection_is_demo_only_without_any_credentials():
    assert status.choose_source(None, None) == "demo" and status.choose_source("", "") == "demo"
    assert status.choose_source("my-project", None) == "earth_engine"
    assert status.choose_source(None, '{"client_email": "x"}') == "earth_engine"


@pytest.mark.parametrize("detail,expected", [
    ("no clear Sentinel-2 acquisition in the period", "no_images"),
    ("EEException: Earth Engine client library not initialized", "other"),
    ("HttpError 403: caller does not have permission", "auth"),
    ("ConnectionError: Max retries exceeded, connection timed out", "network"),
    ("something odd", "other"),
])
def test_failures_are_classified_and_always_have_an_arabic_message(detail, expected):
    assert status.classify_failure(detail) == expected
    assert status.FAILURE_MESSAGES_AR[expected]


def test_freshness_flags_old_observations_and_missing_dates():
    today = dt.date(2026, 10, 25)
    assert status.freshness("2026-10-20", today).age_days == 5 and not status.freshness("2026-10-20", today).stale
    assert status.freshness("2026-09-01", today).stale
    assert status.freshness(None, today).stale and status.freshness(None, today).age_days is None


# ------------------------------------------------------------------ field inspections and validation framework
def _rec(**kw):
    base = dict(zone_id="A1", condition="needs_attention", irrigation_issue="yes", inspection_date="2026-10-01",
                satellite_class="HIGH", session_id="s")
    base.update(kw)
    return base


def test_inspection_record_validation():
    assert validate_record(_rec()) == []
    assert "condition" in validate_record(_rec(condition="maybe"))
    assert "soil_moisture_pct" in validate_record(_rec(soil_moisture_pct=-1))
    assert "alt_causes" in validate_record(_rec(alt_causes=["aliens"]))
    assert "inspection_date" in validate_record(_rec(inspection_date=""))


def test_store_has_no_photo_path(tmp_path):
    st = SQLiteStore(tmp_path)
    st.save_observation(_rec())
    row = st.list_observations("s")[0]
    assert "photo_path" not in row and not (tmp_path / "images").exists()


def test_validation_summary_counts_only_and_flags_small_samples():
    recs = [_rec(), _rec(condition="no_problem"), _rec(satellite_class="HEALTHY", condition="no_problem"),
            _rec(condition="not_sure"), _rec(satellite_class=None)]
    v = validation.summarize(recs)
    assert (v["n_flagged_inspected"], v["n_flagged_confirmed"], v["n_unflagged_inspected"], v["n_unflagged_problem"]) == (2, 1, 1, 0)
    assert v["confirmation_rate"] == 0.5 and v["reliable"] is False
    assert validation.summarize([])["confirmation_rate"] is None


# ------------------------------------------------------------------ plant photography is gone
def test_no_photo_modules_or_symbols_remain():
    import importlib.util
    import pathlib
    assert importlib.util.find_spec("src.image_analysis") is None
    root = pathlib.Path(__file__).resolve().parents[1]
    offenders = [str(p.relative_to(root)) for p in (root / "src").rglob("*.py")
                 if any(w in p.read_text(encoding="utf-8") for w in ("file_uploader", "ANALYZER", "camera_input", "prepare_for_storage"))]
    assert offenders == []


# ------------------------------------------------------------------ UI helpers (no Streamlit run needed)
def test_trend_query_failure_is_unavailable_not_insufficient():
    from types import SimpleNamespace
    from src.ui import farmer

    class Boom:
        def timeseries(self, _):
            raise ConnectionError("timed out")

    c = SimpleNamespace(use_ee=False, farm=Boom(), date="2026-09-20")
    ts, failed = farmer._zone_series(c, {"min_lon": 0, "min_lat": 0, "max_lon": 1, "max_lat": 1})
    assert ts is None and failed is True


def test_ndvi_ratio_label_says_it_is_a_ratio_in_both_languages():
    from src.ui.i18n import S
    en, ar = S["ind_ndvi"]
    assert "ratio" in en and "نسبة" in ar


# ------------------------------------------------------------------ SATRA identity
OLD_BRAND = ("RAYY", "Rayy", "رَيّ", "رَي ")


def test_brand_assets_exist_and_are_valid_svg():
    import xml.dom.minidom

    from src import brand
    for p in (brand.SYMBOL_SVG, brand.SYMBOL_MONO_DARK_SVG, brand.SYMBOL_MONO_LIGHT_SVG, brand.LOGO_EN_SVG, brand.LOGO_AR_SVG):
        assert p.exists(), p
        xml.dom.minidom.parse(str(p))
    assert brand.FAVICON_PNG.exists() and brand.page_icon().endswith("favicon.png")
    assert brand.data_uri(brand.SYMBOL_SVG).startswith("data:image/svg+xml;base64,")


def test_no_old_brand_in_user_facing_text():
    import re

    from src.ui.common import LIMITATIONS
    from src.ui.i18n import S
    texts = [x for pair in S.values() for x in pair] + [x for pair in LIMITATIONS for x in pair]
    offenders = [x for x in texts if any(o in x for o in OLD_BRAND) or re.search(r"\bRAY\b", x)]
    assert offenders == []
    assert S["app_name"] == ("SATRA", "ساترا")


def test_irrigation_word_is_not_rebranded():
    from src.ui.i18n import S
    assert "الري" in S["irr_rule"][1] and "ساترا" not in S["irr_rule"][1]


def test_observation_age_uses_correct_arabic_number_agreement():
    import streamlit as st

    from src.ui.i18n import days_ago
    st.session_state["lang"] = "ar"
    assert [days_ago(n) for n in (0, 1, 2, 3, 10, 11)] == ["اليوم", "قبل يوم واحد", "قبل يومين", "قبل 3 أيام", "قبل 10 أيام", "قبل 11 يومًا"]
    assert days_ago(None) == "—"


def test_interface_uses_one_digit_system():
    """Dates and values are Western digits; Arabic-Indic digits inside sentences would mix two systems on screen."""
    import re

    from src.ui.common import LIMITATIONS
    from src.ui.i18n import S
    texts = [x for pair in S.values() for x in pair] + [x for pair in LIMITATIONS for x in pair]
    assert [x for x in texts if re.search("[٠-٩]", x)] == []


def test_header_labels_and_placeholders_are_arabic():
    from src.ui.i18n import S
    for key in ("hdr_latest", "hdr_age", "hdr_period", "hdr_period_val", "hdr_sim_date", "log_alt_placeholder"):
        assert key in S and S[key][1] and not re.search("[A-Za-z]", S[key][1].replace("{a}", "").replace("{b}", ""))
    assert S["log_title"][1] == "سجل الفحص الميداني" and S["irr_title"][1] == "الري"

