"""Agricultural knowledge base: crops, diseases/pests, reference images and their sources.

The data live in data/knowledge/*.json (not in the code) so they can be reviewed, extended, or loaded into the
database (see db/schema.sql, tables crops / diseases / pests / disease_images / data_sources).
Every record points to a source in sources.json; missing values stay None and are shown as "not available".
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

KB_DIR = Path(__file__).resolve().parents[1] / "data" / "knowledge"


@lru_cache(maxsize=1)
def _load() -> dict:
    def rd(name):
        return json.loads((KB_DIR / name).read_text(encoding="utf-8"))

    crops = rd("crops.json")
    problems = rd("problems.json")
    return {
        "crops": {c["id"]: c for c in crops["crops"]},
        "crop_order": [c["id"] for c in crops["crops"]],
        "unavailable": (crops["unavailable_en"], crops["unavailable_ar"]),
        "problems": {p["id"]: p for p in problems["problems"]},
        "vocab": problems["symptom_vocabulary"],
        "images": rd("images.json"),
        "sources": rd("sources.json")["sources"],
    }


def crops() -> list[dict]:
    kb = _load()
    return [kb["crops"][i] for i in kb["crop_order"]]


def crop(crop_id: str) -> dict:
    return _load()["crops"].get(crop_id) or _load()["crops"]["unknown"]


def problems_for(crop_id: str) -> list[dict]:
    kb = _load()
    return [kb["problems"][p] for p in crop(crop_id)["common_problems"] if p in kb["problems"]]


def all_problems() -> list[dict]:
    return list(_load()["problems"].values())


def problem(pid: str) -> dict | None:
    return _load()["problems"].get(pid)


def symptom_vocabulary() -> dict:
    return _load()["vocab"]


def images_for(prob: dict) -> list[dict]:
    imgs = _load()["images"]
    return [imgs[k] for k in prob.get("reference_images", []) if k in imgs]


def source(source_id: str | None) -> dict | None:
    return _load()["sources"].get(source_id) if source_id else None


def all_sources() -> dict:
    return _load()["sources"]


def unavailable(ar: bool) -> str:
    en, a = _load()["unavailable"]
    return a if ar else en


def validate() -> list[str]:
    """Integrity checks used by the tests: every reference resolves and every record has a source."""
    kb, errs = _load(), []
    for c in kb["crops"].values():
        for p in c["common_problems"]:
            if p not in kb["problems"]:
                errs.append(f"crop {c['id']}: unknown problem {p}")
        for k in ("water_source", "growth_period_source"):
            if c.get(k) and c[k] not in kb["sources"]:
                errs.append(f"crop {c['id']}: unknown source {c[k]}")
        if c.get("water_requirement_mm") and not c.get("water_source"):
            errs.append(f"crop {c['id']}: water requirement without source")
    for p in kb["problems"].values():
        if p.get("source") not in kb["sources"]:
            errs.append(f"problem {p['id']}: missing/unknown source")
        for tag in p["visual_tags"]:
            if tag not in kb["vocab"]:
                errs.append(f"problem {p['id']}: unknown tag {tag}")
        for crop_id in p["crops"]:
            if crop_id not in kb["crops"]:
                errs.append(f"problem {p['id']}: unknown crop {crop_id}")
        for im in p["reference_images"]:
            if im not in kb["images"]:
                errs.append(f"problem {p['id']}: unknown image {im}")
        for s in p.get("similar", []):
            if s not in kb["problems"]:
                errs.append(f"problem {p['id']}: unknown similar {s}")
    for k, im in kb["images"].items():
        if not im.get("license") or not im.get("source_page"):
            errs.append(f"image {k}: licence/source missing")
    return errs
