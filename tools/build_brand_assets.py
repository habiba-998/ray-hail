"""Build the SATRA brand assets that are derived from the master symbol: monochrome symbols, logo lockups, favicon.png.

Run from the project root:  python tools/build_brand_assets.py
The colour symbol (assets/branding/satra-symbol.svg) is the master. The monochrome variants reuse its geometry, and the
PNG favicon is drawn with Pillow from the same coordinates (no SVG renderer dependency).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import brand  # noqa: E402

A = brand.ASSETS
P = brand.PALETTE
MASTER = brand.SYMBOL_SVG.read_text(encoding="utf-8")
FONT_LATIN = "'IBM Plex Sans', 'Segoe UI', Arial, sans-serif"
FONT_AR = "'IBM Plex Sans Arabic', 'Segoe UI', Tahoma, sans-serif"
DETAILS = [r'<polygon points="45,12[^>]*/>',                 # observation beam
           r'<circle cx="21" cy="45" r="8\.5"[^>]*/>',        # irrigated ring
           r'<path d="M45 33v7[^>]*/>']                      # crop rows


def _inner(svg: str) -> str:
    g = re.search(r"<svg[^>]*>(.*)</svg>", svg, re.S).group(1)
    return re.sub(r"<title>.*?</title>|<!--.*?-->", "", g, flags=re.S)


def mono(color: str) -> str:
    """One colour: pivot as an outlined disc with its arm, parcel solid, flagged parcel outlined with a dot; no beam/rows."""
    g = _inner(MASTER)
    g = g.replace('<circle cx="21" cy="45" r="15" fill="#174D3A"/>',
                  f'<circle cx="21" cy="45" r="13.8" fill="none" stroke="{color}" stroke-width="2.4"/>')
    g = g.replace('stroke-width="1.8" stroke-linecap="round" opacity="0.85"/>', 'stroke-width="2.2" stroke-linecap="round"/>')
    for pat in DETAILS:
        g = re.sub(pat, "", g)
    g = g.replace('<rect x="40" y="46" width="18" height="14" rx="2.5" fill="#D99A2B"/>',
                  f'<rect x="41" y="47" width="16" height="12" rx="2" fill="none" stroke="{color}" stroke-width="2"/>')
    for c in ("#F6F7F2", "#174D3A", "#142B45", "#168C86"):
        g = g.replace(c, color)
    g = re.sub(r"\n\s*\n+", "\n", g)
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="SATRA symbol">'
            f"<title>SATRA</title>{g}</svg>\n")


def lockup(ar: bool) -> str:
    """Horizontal logo: symbol + wordmark + tagline (live SVG text in the brand fonts)."""
    sym = _inner(MASTER)
    if ar:
        return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 104" role="img" '
                f'aria-label="{brand.NAME_AR}"><title>{brand.NAME_AR}</title>'
                f'<g transform="translate(272 10) scale(1.3)">{sym}</g>'
                f'<text x="262" y="60" text-anchor="end" font-family="{FONT_AR}" font-size="48" font-weight="700" '
                f'fill="{P["green"]}">{brand.NAME_AR}</text>'
                f'<text x="262" y="88" text-anchor="end" font-family="{FONT_AR}" font-size="16" '
                f'fill="{P["muted"]}">{brand.TAGLINE_AR}</text></svg>\n')
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 104" role="img" '
            f'aria-label="{brand.NAME_EN}"><title>{brand.NAME_EN}</title>'
            f'<g transform="translate(6 10) scale(1.3)">{sym}</g>'
            f'<text x="104" y="60" font-family="{FONT_LATIN}" font-size="44" font-weight="700" letter-spacing="7" '
            f'fill="{P["navy"]}">{brand.NAME_EN}</text>'
            f'<text x="106" y="86" font-family="{FONT_LATIN}" font-size="14" fill="{P["muted"]}">{brand.TAGLINE_EN}</text>'
            "</svg>\n")


def favicon(size: int = 128) -> Image.Image:
    """Simplified symbol for 16–32 px: pivot field, parcel, flagged parcel, orbit and satellite."""
    s = 8  # supersampling
    k = size * s / 64
    im = Image.new("RGBA", (size * s, size * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    def r(x, y, w, h, fill, rad=2.5):
        d.rounded_rectangle([x * k, y * k, (x + w) * k, (y + h) * k], radius=rad * k, fill=fill)

    d.ellipse([6 * k, 30 * k, 36 * k, 60 * k], fill=P["green"])
    r(40, 30, 18, 13, P["green"])
    r(40, 46, 18, 14, P["amber"])
    pts = []
    for i in range(41):  # cubic Bezier M4 31 C12 14 34 6 60 9
        t = i / 40
        x = (1 - t) ** 3 * 4 + 3 * (1 - t) ** 2 * t * 12 + 3 * (1 - t) * t ** 2 * 34 + t ** 3 * 60
        y = (1 - t) ** 3 * 31 + 3 * (1 - t) ** 2 * t * 14 + 3 * (1 - t) * t ** 2 * 6 + t ** 3 * 9
        pts.append((x * k, y * k))
    d.line(pts, fill=P["navy"], width=int(3.2 * k), joint="curve")
    r(34.5, 8.3, 6, 4, P["teal"], 0.8)
    r(49.5, 5.7, 6, 4, P["teal"], 0.8)
    r(41.5, 5, 7, 7, P["navy"], 1.6)
    return im.resize((size, size), Image.LANCZOS)


def main() -> int:
    (A / "satra-symbol-mono-dark.svg").write_text(mono(P["navy"]), encoding="utf-8")
    (A / "satra-symbol-mono-light.svg").write_text(mono("#FFFFFF"), encoding="utf-8")
    (A / "satra-logo-en.svg").write_text(lockup(False), encoding="utf-8")
    (A / "satra-logo-ar.svg").write_text(lockup(True), encoding="utf-8")
    favicon(128).save(A / "favicon.png")
    print("brand assets written to", A)
    return 0


if __name__ == "__main__":
    sys.exit(main())
