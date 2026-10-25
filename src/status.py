"""Data-status handling: is what the user sees REAL, DEMO or UNAVAILABLE?

  * REAL        – retrieved from Earth Engine and processed in this run.
  * DEMO        – simulated by src/demo_data.py. Chosen ONLY when no Earth Engine credentials are configured.
  * UNAVAILABLE – real retrieval was attempted and failed, or the data are insufficient. The app NEVER falls back to
                  simulated data in this case.

Pure functions (no Streamlit, no Earth Engine) so they can be unit-tested.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

REAL, DEMO, UNAVAILABLE = "REAL", "DEMO", "UNAVAILABLE"
STALE_AFTER_DAYS = 20  # a latest valid image older than this is flagged as old (Sentinel-2 revisit is ~5 days)


def choose_source(project: str | None, service_account_json: str | None) -> str:
    """'earth_engine' when any Earth Engine credential/project is configured, otherwise 'demo' (never a silent switch later)."""
    return "earth_engine" if (project or service_account_json) else "demo"


def classify_failure(detail: object) -> str:
    """Map a technical failure to a coarse category used for the user-facing message: auth | network | no_images | other."""
    s = str(detail).lower()
    if "no clear sentinel-2" in s or "no_images" in s:
        return "no_images"
    if any(k in s for k in ("not installed", "credential", "permission", "403", "401", "invalid_grant", "unauthenticated",
                            "not signed up", "project", "serviceaccount", "default credentials")):
        return "auth"
    if any(k in s for k in ("timeout", "timed out", "connection", "network", "name resolution", "unreachable", "ssl", "503", "502")):
        return "network"
    return "other"


FAILURE_MESSAGES_AR = {
    "auth": "تعذّر الاتصال بخدمة الصور الفضائية (إعدادات الاعتماد أو المشروع غير صالحة). لا تُعرض أي نتائج بدلًا منها.",
    "network": "تعذّر الوصول إلى خدمة الصور الفضائية بسبب مشكلة في الاتصال. حاول مرة أخرى بعد قليل.",
    "no_images": "لا توجد صورة فضائية صافية كافية لهذه المزرعة في الفترة الأخيرة (غيوم أو غبار)، لذلك لا يمكن تقييم المناطق الآن.",
    "other": "تعذّر تحميل بيانات المزرعة حاليًا. لا تُعرض أي نتائج بدلًا منها.",
}


@dataclass(frozen=True)
class Freshness:
    age_days: int | None
    stale: bool


def freshness(latest_valid_date: str | dt.date | None, today: dt.date | None = None) -> Freshness:
    """Age of the latest valid observation in days relative to `today`."""
    if latest_valid_date is None:
        return Freshness(None, True)
    today = today or dt.date.today()
    d = latest_valid_date if isinstance(latest_valid_date, dt.date) else dt.date.fromisoformat(str(latest_valid_date)[:10])
    age = (today - d).days
    return Freshness(age, age > STALE_AFTER_DAYS)
