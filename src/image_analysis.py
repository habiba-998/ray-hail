"""Farmer photo analysis – modular, transparent, and NOT a trained disease classifier.

Pipeline:  farmer image → quality checks → colour screening → symptom signals → (fusion) → field validation

The current analyser (`ColorScreening`) measures the share of green, yellow and brown tissue colours and of very dark
spots in the photo. It cannot identify a disease; it only adds weak evidence (e.g. "much yellow tissue") to the
cause ranking. A trained computer-vision model can be plugged in later by implementing the same `analyze` interface
– it must not be enabled, nor any accuracy claimed, until it has been validated on local field data.
"""
from __future__ import annotations

import io

import numpy as np
from PIL import Image, ImageOps

MAX_SIDE_ANALYSIS = 512
MAX_SIDE_STORAGE = 1280

# Prototype thresholds (shares of leaf-coloured pixels) – not calibrated
YELLOW_SHARE = 0.15
BROWN_SHARE = 0.15
DARK_SPOT_SHARE = 0.05
MIN_TISSUE_SHARE = 0.10


def load(image_bytes: bytes) -> Image.Image:
    img = Image.open(io.BytesIO(image_bytes))
    img = ImageOps.exif_transpose(img)  # respect phone orientation
    return img.convert("RGB")


def prepare_for_storage(image_bytes: bytes) -> bytes:
    """Re-encode as JPEG (max 1280 px) WITHOUT metadata – removes EXIF such as GPS position and device info."""
    img = load(image_bytes)
    img.thumbnail((MAX_SIDE_STORAGE, MAX_SIDE_STORAGE))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85, optimize=True)  # no exif= argument → metadata dropped
    return buf.getvalue()


class ColorScreening:
    name = "Colour screening (rule-based, not a trained model)"
    name_ar = "فحص ألوان مبسّط (قواعد، وليس نموذجًا مدرّبًا)"

    def analyze(self, image_bytes: bytes) -> dict:
        try:
            img = load(image_bytes)
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "reason": "unreadable", "detail": str(exc), "method": self.name}
        w, h = img.size
        if min(w, h) < 200:
            return {"ok": False, "reason": "too_small", "method": self.name}
        img.thumbnail((MAX_SIDE_ANALYSIS, MAX_SIDE_ANALYSIS))
        hsv = np.asarray(img.convert("HSV"), dtype="float32") / 255.0
        hue, sat, val = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
        if val.mean() < 0.18:
            return {"ok": False, "reason": "too_dark", "method": self.name}

        green = (hue >= 70) & (hue < 170) & (sat > 0.18) & (val > 0.15)
        yellow = (hue >= 45) & (hue < 70) & (sat > 0.25) & (val > 0.35)
        brown = (hue >= 10) & (hue < 45) & (sat > 0.25) & (val > 0.12) & (val < 0.65)
        tissue = green | yellow | brown
        n = tissue.sum()
        share_tissue = float(n / tissue.size)
        if share_tissue < MIN_TISSUE_SHARE:
            return {"ok": False, "reason": "no_leaf", "method": self.name, "tissue_share": share_tissue}
        dark = (val < 0.22) & ~tissue
        res = {
            "ok": True, "method": self.name, "width": w, "height": h,
            "tissue_share": share_tissue,
            "green_share": float(green.sum() / n),
            "yellow_share": float(yellow.sum() / n),
            "brown_share": float(brown.sum() / n),
            "dark_spot_share": float(dark.sum() / tissue.size),
        }
        res["signals"] = [s for s, on in (
            ("photo_yellow", res["yellow_share"] >= YELLOW_SHARE),
            ("photo_brown", res["brown_share"] >= BROWN_SHARE),
            ("photo_dark_spots", res["dark_spot_share"] >= DARK_SPOT_SHARE),
        ) if on]
        res["overlay"] = _overlay(img, yellow, brown)
        return res


def _overlay(img: Image.Image, yellow: np.ndarray, brown: np.ndarray) -> Image.Image:
    """Highlight yellow (amber) and brown (red) tissue on a dimmed copy of the photo."""
    arr = np.asarray(img, dtype="float32") * 0.55
    arr[yellow] = [242, 176, 30]
    arr[brown] = [214, 69, 65]
    return Image.fromarray(arr.clip(0, 255).astype("uint8"))


ANALYZER = ColorScreening()
