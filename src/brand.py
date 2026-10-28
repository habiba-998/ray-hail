"""SATRA | ساترا – single source of truth for the product identity.

Every user-facing brand string, tagline, colour and logo path comes from here, so a future rename touches one file.
The logo geometry lives in the SVG files under assets/branding/ (favicon.png is generated from the same geometry by
tools/build_brand_assets.py).

Historical names kept for compatibility (do not rename without a migration): the GitHub repository and Streamlit app
URL `ray-hail`, the Google Cloud project `ray-hail-2026`, the service account `ray-streamlit`, the local SQLite file
`data/user_data/ray.db` and the `RAY_DATA_DIR` environment variable (SATRA_DATA_DIR is preferred).
"""
from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path

NAME_EN = "SATRA"
NAME_AR = "ساترا"
DESCRIPTION_AR = "منصة ذكية لرصد الأراضي الزراعية من الفضاء"
DESCRIPTION_EN = "An intelligent platform for monitoring agricultural land from space"
TAGLINE_AR = "من الفضاء إلى قرار زراعي أذكى"
TAGLINE_EN = "From Space to Smarter Agricultural Decisions"

# Design tokens (semantic status colours are paired with text and icons everywhere; colour is never the only cue)
PALETTE = {
    "green": "#174D3A",      # deep agricultural green – primary
    "navy": "#142B45",       # satellite navy – headings, wordmark
    "teal": "#168C86",       # observation / interactive accent
    "paper": "#F6F7F2",      # warm off-white background
    "ink": "#263238",        # body text
    "muted": "#5F6B70",      # secondary text
    "line": "#DCE1DA",       # borders
    "amber": "#D99A2B",      # follow-up / caution
    "red": "#C94C4C",        # higher inspection priority (not a diagnosis)
    "ok": "#2F8A5B",         # no clear abnormal signal (not "healthy")
    "gray": "#7A858C",       # insufficient / unavailable data
}

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets" / "branding"
SYMBOL_SVG = ASSETS / "satra-symbol.svg"
SYMBOL_MONO_DARK_SVG = ASSETS / "satra-symbol-mono-dark.svg"
SYMBOL_MONO_LIGHT_SVG = ASSETS / "satra-symbol-mono-light.svg"
LOGO_EN_SVG = ASSETS / "satra-logo-en.svg"
LOGO_AR_SVG = ASSETS / "satra-logo-ar.svg"
FAVICON_PNG = ASSETS / "favicon.png"


@lru_cache(maxsize=None)
def data_uri(path: Path) -> str:
    """Inline an SVG/PNG asset as a data URI (Streamlit serves no static files by default)."""
    mime = "image/svg+xml" if path.suffix == ".svg" else "image/png"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


def page_icon() -> str:
    """Path for st.set_page_config(page_icon=...); falls back to an emoji if the asset is missing."""
    return str(FAVICON_PNG) if FAVICON_PNG.exists() else "🛰️"
