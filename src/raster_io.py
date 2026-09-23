"""Optional GeoTIFF export (requires rasterio; the app works without it)."""
from __future__ import annotations

import numpy as np


def rasterio_available() -> bool:
    try:
        import rasterio  # noqa: F401

        return True
    except ImportError:
        return False


def array_to_geotiff_bytes(arr: np.ndarray, bounds: tuple[float, float, float, float], description: str) -> bytes:
    """Write a single-band float32 array (row 0 = north) to an in-memory GeoTIFF in EPSG:4326."""
    from rasterio.io import MemoryFile
    from rasterio.transform import from_bounds

    h, w = arr.shape
    transform = from_bounds(*bounds, width=w, height=h)
    profile = dict(driver="GTiff", height=h, width=w, count=1, dtype="float32", crs="EPSG:4326",
                   transform=transform, nodata=np.nan, compress="deflate")
    with MemoryFile() as mem:
        with mem.open(**profile) as dst:
            dst.write(arr.astype("float32"), 1)
            dst.set_band_description(1, description)
            dst.update_tags(SOURCE="RAY hackathon prototype", NOTE=description)
        return mem.read()
