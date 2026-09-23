"""Preprocessing: zone grid construction, cloud masking and radiometric scaling."""
from __future__ import annotations

import pandas as pd

from .config import S2_BANDS, S2_SCL_INVALID, AOI


# ---------------------------------------------------------------------------
# Zones
# ---------------------------------------------------------------------------
def make_zone_grid(aoi: AOI, rows: int, cols: int) -> pd.DataFrame:
    """Split the AOI into rows x cols rectangular management zones.

    Zone IDs read like a spreadsheet: row letter + column number (A1 is top-left).
    """
    min_lon, min_lat, max_lon, max_lat = aoi.bounds
    dlon = (max_lon - min_lon) / cols
    dlat = (max_lat - min_lat) / rows
    recs = []
    for r in range(rows):
        for c in range(cols):
            top = max_lat - r * dlat
            recs.append(
                {
                    "zone_id": f"{chr(65 + r)}{c + 1}",
                    "row": r,
                    "col": c,
                    "min_lon": min_lon + c * dlon,
                    "max_lon": min_lon + (c + 1) * dlon,
                    "min_lat": top - dlat,
                    "max_lat": top,
                }
            )
    return pd.DataFrame(recs)


def zone_at(zones: pd.DataFrame, lat: float, lon: float) -> str | None:
    hit = zones[
        (zones.min_lon <= lon) & (zones.max_lon >= lon) & (zones.min_lat <= lat) & (zones.max_lat >= lat)
    ]
    return None if hit.empty else str(hit.iloc[0].zone_id)


def zone_geojson(zones: pd.DataFrame, props: list[str] | None = None) -> dict:
    props = props or []
    feats = []
    for z in zones.itertuples(index=False):
        ring = [
            [z.min_lon, z.min_lat],
            [z.max_lon, z.min_lat],
            [z.max_lon, z.max_lat],
            [z.min_lon, z.max_lat],
            [z.min_lon, z.min_lat],
        ]
        p = {"zone_id": z.zone_id}
        for k in props:
            v = getattr(z, k, None)
            p[k] = None if v is None or (isinstance(v, float) and v != v) else v
        feats.append({"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [ring]}, "properties": p})
    return {"type": "FeatureCollection", "features": feats}


# ---------------------------------------------------------------------------
# Earth Engine preprocessing (ee is imported lazily so demo mode never needs it)
# ---------------------------------------------------------------------------
def s2_clear_mask(img):
    """1 where the Sentinel-2 Scene Classification Layer marks a valid, cloud-free pixel."""
    scl = img.select("SCL")
    mask = scl.neq(S2_SCL_INVALID[0])
    for v in S2_SCL_INVALID[1:]:
        mask = mask.And(scl.neq(v))
    return mask


def s2_prepare(img):
    """Cloud-mask and scale a Sentinel-2 L2A image to 0-1 reflectance, add CLEAR band."""
    from .indices import add_indices_ee

    clear = s2_clear_mask(img)
    refl = img.select(S2_BANDS).divide(10000).updateMask(clear)
    out = add_indices_ee(refl)
    return out.addBands(clear.unmask(0).rename("CLEAR")).copyProperties(img, ["system:time_start"])


def landsat_lst_prepare(img):
    """Landsat C2 L2 surface temperature in deg C with cloud / shadow / dilated-cloud masked."""
    qa = img.select("QA_PIXEL")
    clear = (
        qa.bitwiseAnd(1 << 1).eq(0)  # dilated cloud
        .And(qa.bitwiseAnd(1 << 3).eq(0))  # cloud
        .And(qa.bitwiseAnd(1 << 4).eq(0))  # cloud shadow
    )
    lst = img.select("ST_B10").multiply(0.00341802).add(149.0).subtract(273.15).rename("LST")
    return (
        lst.updateMask(clear)
        .addBands(clear.unmask(0).rename("CLEAR"))
        .copyProperties(img, ["system:time_start"])
    )
