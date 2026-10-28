"""Storage for non-photographic field-inspection records.

Backends (chosen automatically):
  * SupabaseStore – Postgres table, used when Streamlit Secrets contain [supabase] url = "...", service_key = "...".
    The service key is used server-side only (never sent to the browser). Schema: db/schema.sql (+ db/migrations).
  * SQLiteStore   – local file data/user_data/ray.db (git-ignored; file name kept from the former product name so
                    existing records stay readable).
    On Streamlit Community Cloud the local disk is NOT persistent: data are lost when the app restarts.

A record is what a person typed in after visiting a zone. It is NOT verified ground truth: the collection procedure
(who inspected, how, with which instrument) is not controlled. Records carry a random per-browser-session id (no names,
phone numbers or accounts) and the UI only lists the current session's own records.
Older databases may still contain photo_* columns from a removed feature; they are neither written nor read any more.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
# SATRA_DATA_DIR overrides the folder (tests); RAY_DATA_DIR is still honoured for existing setups
LOCAL_DIR = Path(os.environ.get("SATRA_DATA_DIR") or os.environ.get("RAY_DATA_DIR") or ROOT / "data" / "user_data")

OBS_FIELDS = ["id", "created_at", "session_id", "farm_id", "farm_name", "data_mode", "zone_id", "crop_id",
              "satellite_date", "satellite_class", "satellite_score", "lat", "lon",
              "inspection_date", "condition", "irrigation_issue", "alt_causes", "soil_moisture_pct", "inspector", "notes"]
JSON_FIELDS = {"alt_causes"}
CONDITIONS = ("needs_attention", "no_problem", "not_sure")
IRRIGATION_ISSUE = ("yes", "no", "not_checked")
ALT_CAUSES = ("heat", "salinity", "disease", "pest", "nutrient", "harvest", "growth_stage", "other")


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def validate_record(rec: dict) -> list[str]:
    """Problems with an inspection record (empty list = valid). Keeps junk out of the validation data set."""
    errs = []
    if not rec.get("zone_id"):
        errs.append("zone_id")
    if rec.get("condition") not in CONDITIONS:
        errs.append("condition")
    if rec.get("irrigation_issue") not in IRRIGATION_ISSUE:
        errs.append("irrigation_issue")
    if not rec.get("inspection_date"):
        errs.append("inspection_date")
    sm = rec.get("soil_moisture_pct")
    if sm not in (None, "") and not (isinstance(sm, (int, float)) and 0 <= sm <= 100):
        errs.append("soil_moisture_pct")
    bad = [c for c in (rec.get("alt_causes") or []) if c not in ALT_CAUSES]
    if bad:
        errs.append("alt_causes")
    return errs


class SQLiteStore:
    name = "SQLite (local)"
    persistent_note_en = "Saved on this server only. On the hosted demo, data are deleted when the app restarts."
    persistent_note_ar = "تُحفظ السجلات مؤقتًا، وقد تُحذف عند تحديث التطبيق."

    def __init__(self, folder: Path = LOCAL_DIR):
        self.folder = folder
        folder.mkdir(parents=True, exist_ok=True)
        self.db = folder / "ray.db"
        with self._con() as c:
            c.execute(f"CREATE TABLE IF NOT EXISTS field_observations ({', '.join(f + ' TEXT' for f in OBS_FIELDS)})")
            # forward-compatible migration: add columns introduced after the table was first created (no data loss)
            have = {r[1] for r in c.execute("PRAGMA table_info(field_observations)")}
            for f in OBS_FIELDS:
                if f not in have:
                    c.execute(f"ALTER TABLE field_observations ADD COLUMN {f} TEXT")

    @contextmanager
    def _con(self):
        """Connection that commits on success and is ALWAYS closed (sqlite3's own context manager never closes)."""
        con = sqlite3.connect(self.db)
        try:
            yield con
            con.commit()
        finally:
            con.close()

    def save_observation(self, rec: dict) -> str:
        errs = validate_record(rec)
        if errs:
            raise ValueError(f"invalid inspection record: {errs}")
        rec = {**rec, "id": rec.get("id") or str(uuid.uuid4()), "created_at": _now()}
        row = [json.dumps(rec.get(f), ensure_ascii=False) if f in JSON_FIELDS else (None if rec.get(f) is None else str(rec.get(f)))
               for f in OBS_FIELDS]
        with self._con() as c:
            c.execute(f"INSERT INTO field_observations ({','.join(OBS_FIELDS)}) VALUES ({','.join('?' * len(OBS_FIELDS))})", row)
        return rec["id"]

    def list_observations(self, session_id: str, zone_id: str | None = None, limit: int = 50) -> list[dict]:
        q = f"SELECT {','.join(OBS_FIELDS)} FROM field_observations WHERE session_id = ?" + (" AND zone_id = ?" if zone_id else "")
        q += " ORDER BY created_at DESC LIMIT ?"
        args = [session_id] + ([zone_id] if zone_id else []) + [limit]
        with self._con() as c:
            c.row_factory = sqlite3.Row
            rows = [dict(r) for r in c.execute(q, args)]
        for r in rows:
            for f in JSON_FIELDS:
                r[f] = json.loads(r[f]) if r.get(f) else None
            for f in ("soil_moisture_pct", "satellite_score"):
                r[f] = float(r[f]) if r.get(f) not in (None, "") else None
        return rows

    def counts(self) -> dict:
        with self._con() as c:
            return {"observations": c.execute("SELECT COUNT(*) FROM field_observations").fetchone()[0]}


class SupabaseStore:
    name = "Supabase (Postgres)"
    persistent_note_en = "Saved permanently in the project database (Supabase)."
    persistent_note_ar = "تُحفظ السجلات بشكل دائم."

    def __init__(self, url: str, service_key: str):
        self.url = url.rstrip("/")
        self.h = {"apikey": service_key, "Authorization": f"Bearer {service_key}"}

    def _rest(self, method, table, **kw):
        r = requests.request(method, f"{self.url}/rest/v1/{table}", headers={**self.h, "Content-Type": "application/json",
                             "Prefer": "return=representation"}, timeout=20, **kw)
        r.raise_for_status()
        return r.json() if r.content else None

    def save_observation(self, rec: dict) -> str:
        errs = validate_record(rec)
        if errs:
            raise ValueError(f"invalid inspection record: {errs}")
        row = {k: rec.get(k) for k in OBS_FIELDS if k not in ("id", "created_at")}
        oid = str(uuid.uuid4())
        self._rest("POST", "field_observations", json={**row, "id": oid})
        return oid

    def list_observations(self, session_id: str, zone_id: str | None = None, limit: int = 50) -> list[dict]:
        params = {"select": ",".join(OBS_FIELDS), "session_id": f"eq.{session_id}", "order": "created_at.desc", "limit": str(limit)}
        if zone_id:
            params["zone_id"] = f"eq.{zone_id}"
        return self._rest("GET", "field_observations", params=params) or []

    def counts(self) -> dict:
        r = requests.get(f"{self.url}/rest/v1/field_observations", params={"select": "id"},
                         headers={**self.h, "Prefer": "count=exact", "Range": "0-0"}, timeout=20)
        return {"observations": int(r.headers.get("content-range", "*/0").split("/")[-1] or 0) if r.ok else None}


def make_store(secrets: dict | None):
    """Supabase when configured in secrets, otherwise local SQLite."""
    sb = (secrets or {}).get("supabase") or {}
    if sb.get("url") and sb.get("service_key"):
        return SupabaseStore(sb["url"], sb["service_key"])
    return SQLiteStore()
