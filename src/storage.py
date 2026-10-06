"""Storage for farmer observations, photos and field validations.

Backends (chosen automatically):
  * SupabaseStore – Postgres tables + private Storage bucket, used when Streamlit Secrets contain
        [supabase] url = "...", service_key = "...", bucket = "farmer-images" (optional)
    The service key is used server-side only (never sent to the browser). Schema: db/schema.sql.
  * SQLiteStore   – local file data/user_data/ray.db + data/user_data/images/ (git-ignored).
    On Streamlit Community Cloud the local disk is NOT persistent: data are lost when the app restarts.

Privacy: photos are re-encoded without EXIF metadata before storage, records carry a random per-browser-session id
(no names, phone numbers or accounts), and the UI only lists the current session's own observations.
Farmer photos are never written to the Git repository.
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
LOCAL_DIR = Path(os.environ.get("RAY_DATA_DIR") or ROOT / "data" / "user_data")  # override for tests

OBS_FIELDS = ["id", "created_at", "session_id", "farm_id", "farm_name", "data_mode", "zone_id", "crop_id",
              "satellite_date", "satellite_class", "satellite_score", "lat", "lon", "symptoms", "soil_condition",
              "spread", "photo_path", "photo_screening", "possible_causes", "candidate_problems", "notes"]
VAL_FIELDS = ["id", "created_at", "session_id", "observation_id", "ray_prediction", "field_check", "actual_cause",
              "actual_problem_id", "action_taken", "notes"]
JSON_FIELDS = {"symptoms", "photo_screening", "possible_causes", "candidate_problems"}


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


class SQLiteStore:
    name = "SQLite (local)"
    persistent_note_en = "Saved on this server only. On the hosted demo, data are deleted when the app restarts."
    persistent_note_ar = "تُحفظ السجلات مؤقتًا، وقد تُحذف عند تحديث التطبيق."

    def __init__(self, folder: Path = LOCAL_DIR):
        self.folder = folder
        (folder / "images").mkdir(parents=True, exist_ok=True)
        self.db = folder / "ray.db"
        with self._con() as c:
            c.execute(f"CREATE TABLE IF NOT EXISTS field_observations ({', '.join(f + ' TEXT' for f in OBS_FIELDS)})")
            c.execute(f"CREATE TABLE IF NOT EXISTS field_validations ({', '.join(f + ' TEXT' for f in VAL_FIELDS)})")
            # forward-compatible migration: add columns introduced after the table was first created (no data loss)
            for table, fields in (("field_observations", OBS_FIELDS), ("field_validations", VAL_FIELDS)):
                have = {r[1] for r in c.execute(f"PRAGMA table_info({table})")}
                for f in fields:
                    if f not in have:
                        c.execute(f"ALTER TABLE {table} ADD COLUMN {f} TEXT")

    @contextmanager
    def _con(self):
        """Connection that commits on success and is ALWAYS closed (sqlite3's own context manager never closes)."""
        con = sqlite3.connect(self.db)
        try:
            yield con
            con.commit()
        finally:
            con.close()

    def save_observation(self, rec: dict, image_jpeg: bytes | None) -> str:
        rec = {**rec, "id": rec.get("id") or str(uuid.uuid4()), "created_at": _now()}
        if image_jpeg:
            rel = f"images/{rec['id']}.jpg"
            (self.folder / rel).write_bytes(image_jpeg)
            rec["photo_path"] = rel
        row = [json.dumps(rec.get(f), ensure_ascii=False) if f in JSON_FIELDS else (None if rec.get(f) is None else str(rec.get(f)))
               for f in OBS_FIELDS]
        with self._con() as c:
            c.execute(f"INSERT INTO field_observations ({','.join(OBS_FIELDS)}) VALUES ({','.join('?' * len(OBS_FIELDS))})", row)
        return rec["id"]

    def save_validation(self, rec: dict) -> str:
        rec = {**rec, "id": str(uuid.uuid4()), "created_at": _now()}
        with self._con() as c:
            c.execute(f"INSERT INTO field_validations ({','.join(VAL_FIELDS)}) VALUES ({','.join('?' * len(VAL_FIELDS))})",
                      [None if rec.get(f) is None else str(rec.get(f)) for f in VAL_FIELDS])
        return rec["id"]

    def list_observations(self, session_id: str, zone_id: str | None = None, limit: int = 20) -> list[dict]:
        q = "SELECT * FROM field_observations WHERE session_id = ?" + (" AND zone_id = ?" if zone_id else "")
        q += " ORDER BY created_at DESC LIMIT ?"
        args = [session_id] + ([zone_id] if zone_id else []) + [limit]
        with self._con() as c:
            c.row_factory = sqlite3.Row
            rows = [dict(r) for r in c.execute(q, args)]
        for r in rows:
            for f in JSON_FIELDS:
                r[f] = json.loads(r[f]) if r.get(f) else None
        return rows

    def list_validations(self, observation_ids: list[str]) -> list[dict]:
        if not observation_ids:
            return []
        with self._con() as c:
            c.row_factory = sqlite3.Row
            q = f"SELECT * FROM field_validations WHERE observation_id IN ({','.join('?' * len(observation_ids))})"
            return [dict(r) for r in c.execute(q, observation_ids)]

    def get_image(self, path: str | None) -> bytes | None:
        p = self.folder / path if path else None
        return p.read_bytes() if p and p.exists() else None

    def counts(self) -> dict:
        with self._con() as c:
            return {"observations": c.execute("SELECT COUNT(*) FROM field_observations").fetchone()[0],
                    "validations": c.execute("SELECT COUNT(*) FROM field_validations").fetchone()[0],
                    "photos": c.execute("SELECT COUNT(*) FROM field_observations WHERE photo_path IS NOT NULL").fetchone()[0]}


class SupabaseStore:
    name = "Supabase (Postgres + Storage)"
    persistent_note_en = "Saved permanently in the project database (Supabase)."
    persistent_note_ar = "تُحفظ السجلات بشكل دائم."

    def __init__(self, url: str, service_key: str, bucket: str = "farmer-images"):
        self.url, self.bucket = url.rstrip("/"), bucket
        self.h = {"apikey": service_key, "Authorization": f"Bearer {service_key}"}

    def _rest(self, method, table, **kw):
        r = requests.request(method, f"{self.url}/rest/v1/{table}", headers={**self.h, "Content-Type": "application/json",
                             "Prefer": "return=representation"}, timeout=20, **kw)
        r.raise_for_status()
        return r.json() if r.content else None

    def save_observation(self, rec: dict, image_jpeg: bytes | None) -> str:
        rec = {k: rec.get(k) for k in OBS_FIELDS if k not in ("id", "created_at")}
        oid = str(uuid.uuid4())
        if image_jpeg:
            path = f"{rec.get('farm_id') or 'farm'}/{oid}.jpg"
            r = requests.post(f"{self.url}/storage/v1/object/{self.bucket}/{path}", data=image_jpeg,
                              headers={**self.h, "Content-Type": "image/jpeg"}, timeout=30)
            r.raise_for_status()
            rec["photo_path"] = path
        self._rest("POST", "field_observations", json={**rec, "id": oid})
        return oid

    def save_validation(self, rec: dict) -> str:
        row = {k: rec.get(k) for k in VAL_FIELDS if k not in ("id", "created_at")}
        return self._rest("POST", "field_validations", json=row)[0]["id"]

    def list_observations(self, session_id: str, zone_id: str | None = None, limit: int = 20) -> list[dict]:
        params = {"select": "*", "session_id": f"eq.{session_id}", "order": "created_at.desc", "limit": str(limit)}
        if zone_id:
            params["zone_id"] = f"eq.{zone_id}"
        return self._rest("GET", "field_observations", params=params) or []

    def list_validations(self, observation_ids: list[str]) -> list[dict]:
        if not observation_ids:
            return []
        return self._rest("GET", "field_validations", params={"select": "*", "observation_id": f"in.({','.join(observation_ids)})"}) or []

    def get_image(self, path: str | None) -> bytes | None:
        if not path:
            return None
        r = requests.get(f"{self.url}/storage/v1/object/authenticated/{self.bucket}/{path}", headers=self.h, timeout=30)
        return r.content if r.ok else None

    def counts(self) -> dict:
        def n(table, extra=None):
            r = requests.get(f"{self.url}/rest/v1/{table}", params={"select": "id", **(extra or {})},
                             headers={**self.h, "Prefer": "count=exact", "Range": "0-0"}, timeout=20)
            return int(r.headers.get("content-range", "*/0").split("/")[-1] or 0) if r.ok else None
        return {"observations": n("field_observations"), "validations": n("field_validations"),
                "photos": n("field_observations", {"photo_path": "not.is.null"})}


def make_store(secrets: dict | None):
    """Supabase when configured in secrets, otherwise local SQLite."""
    sb = (secrets or {}).get("supabase") or {}
    if sb.get("url") and sb.get("service_key"):
        return SupabaseStore(sb["url"], sb["service_key"], sb.get("bucket", "farmer-images"))
    return SQLiteStore()
