"""Map (Folium) and chart (Plotly) builders."""
from __future__ import annotations

import base64
import io

import folium
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from PIL import Image

from .config import CLASS_COLORS, CLASS_LABELS
from .indices import PALETTES, VIS_RANGES
from .preprocessing import zone_geojson

ESRI_URL = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
FONT = dict(family="Inter, Segoe UI, Tahoma, sans-serif", size=13, color="#0B2530")
INDEX_COLORS = {"NDVI": "#2E9E5B", "NDRE": "#0F766E", "NDMI": "#2563EB", "LST": "#D64541"}


def rgba_to_data_uri(rgba: np.ndarray) -> str:
    buf = io.BytesIO()
    Image.fromarray(rgba, "RGBA").save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def build_map(
    bounds: tuple,
    zones: pd.DataFrame,
    selected: str | None,
    tile_url: str | None = None,
    image_rgba: np.ndarray | None = None,
    layer_name: str = "",
    zone_fill: float = 0.05,
    attribution: str = "",
    labels: dict[str, str] | None = None,
    label_px: int = 11,
    tooltip_aliases: tuple[str, str, str] = ("Zone", "Status", "Stress score %"),
    class_labels: dict[str, str] | None = None,
) -> folium.Map:
    """Folium map of the AOI with coloured zones.

    `labels` optionally replaces the zone-ID text drawn on each zone (e.g. "A4 ⚠ Inspect") so status is readable
    without relying on colour; `class_labels` / `tooltip_aliases` allow translated tooltips. Defaults keep the
    original technical-mode appearance.
    """
    min_lon, min_lat, max_lon, max_lat = bounds
    m = folium.Map(location=[(min_lat + max_lat) / 2, (min_lon + max_lon) / 2], zoom_start=14, tiles=None, control_scale=True)
    folium.TileLayer(tiles=ESRI_URL, attr="Basemap: Esri World Imagery", name="Basemap", max_zoom=19).add_to(m)
    if tile_url:
        folium.TileLayer(tiles=tile_url, attr=attribution, name=layer_name, overlay=True, max_zoom=19).add_to(m)
    elif image_rgba is not None:
        folium.raster_layers.ImageOverlay(
            image=rgba_to_data_uri(image_rgba),
            bounds=[[min_lat, min_lon], [max_lat, max_lon]],
            name=layer_name,
            opacity=1.0,
            attribution=attribution,
        ).add_to(m)

    gj = zone_geojson(zones.assign(label=zones.cls.map(class_labels or CLASS_LABELS), score_pct=(zones.score * 100).round(0)),
                      ["cls", "label", "score_pct"])

    def style(feat):
        p = feat["properties"]
        sel = p["zone_id"] == selected
        return {
            "color": "#FFFFFF" if sel else CLASS_COLORS.get(p["cls"], "#888"),
            "weight": 4 if sel else 1.6,
            "fillColor": CLASS_COLORS.get(p["cls"], "#888"),
            "fillOpacity": zone_fill,
        }

    folium.GeoJson(
        gj,
        name="Zones",
        style_function=style,
        highlight_function=lambda f: {"weight": 3, "color": "#FFFFFF"},
        tooltip=folium.GeoJsonTooltip(fields=["zone_id", "label", "score_pct"], aliases=list(tooltip_aliases)),
    ).add_to(m)
    for z in zones.itertuples(index=False):
        text = (labels or {}).get(z.zone_id, z.zone_id)
        folium.Marker(
            [(z.min_lat + z.max_lat) / 2, (z.min_lon + z.max_lon) / 2],
            # interactive=False + pointer-events:none so a tap on the label selects the zone underneath
            interactive=False,
            icon=folium.DivIcon(
                html=f'<div style="font:700 {label_px}px Inter,Tajawal,sans-serif;color:#fff;text-shadow:0 0 3px #000,0 0 6px #000;'
                f'transform:translate(-50%,-50%);white-space:nowrap;pointer-events:none">{text}</div>'
            ),
        ).add_to(m)
    m.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]])
    return m


def legend_html(layer: str) -> str:
    if layer == "Water Stress":
        items = "".join(
            f'<div class="lg-item"><span style="background:{CLASS_COLORS[k]}"></span>{CLASS_LABELS[k]}</div>'
            for k in ("HEALTHY", "MODERATE", "HIGH", "NO_CROP", "NO_DATA")
        )
        return f'<div class="legend"><b>Water-stress classes</b>{items}</div>'
    if layer in PALETTES and layer in VIS_RANGES:
        lo, hi = VIS_RANGES[layer]
        grad = ",".join(PALETTES[layer])
        unit = " °C" if layer == "LST" else ""
        return (
            f'<div class="legend"><b>{layer}</b><div class="lg-bar" style="background:linear-gradient(90deg,{grad})"></div>'
            f'<div class="lg-ticks"><span>{lo}{unit}</span><span>{hi}{unit}</span></div></div>'
        )
    return '<div class="legend"><b>True Color</b><div>Natural-colour composite (B4 / B3 / B2)</div></div>'


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
def _layout(fig: go.Figure, height: int = 360, title: str | None = None) -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        height=height,
        font=FONT,
        title=dict(text=title, x=0, font=dict(size=15)) if title else None,
        margin=dict(l=10, r=10, t=40 if title else 10, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def class_donut(zones: pd.DataFrame) -> go.Figure:
    counts = zones.cls.value_counts()
    order = [k for k in ("HEALTHY", "MODERATE", "HIGH", "NO_CROP", "NO_DATA") if k in counts]
    fig = go.Figure(
        go.Pie(
            labels=[CLASS_LABELS[k] for k in order],
            values=[counts[k] for k in order],
            marker=dict(colors=[CLASS_COLORS[k] for k in order]),
            hole=0.62,
            sort=False,
            textinfo="value",
        )
    )
    return _layout(fig, 300)


def zone_grid_heatmap(zones: pd.DataFrame) -> go.Figure:
    rows, cols = zones.row.max() + 1, zones.col.max() + 1
    code = {"HEALTHY": 0, "MODERATE": 1, "HIGH": 2, "NO_CROP": 3, "NO_DATA": 4}
    z = np.full((rows, cols), np.nan)
    txt = np.full((rows, cols), "", dtype=object)
    for r in zones.itertuples(index=False):
        z[r.row, r.col] = code[r.cls]
        txt[r.row, r.col] = r.zone_id
    keys = list(code)
    scale = []
    for i, k in enumerate(keys):
        scale += [[i / len(keys), CLASS_COLORS[k]], [(i + 1) / len(keys), CLASS_COLORS[k]]]
    fig = go.Figure(
        go.Heatmap(
            z=z, text=txt, texttemplate="%{text}", colorscale=scale, zmin=-0.5, zmax=len(keys) - 0.5,
            showscale=False, xgap=3, ygap=3, hoverinfo="text",
        )
    )
    fig.update_yaxes(autorange="reversed", showticklabels=False)
    fig.update_xaxes(showticklabels=False)
    return _layout(fig, 300)


def timeseries_chart(zone_ts: pd.DataFrame, farm_ts: pd.DataFrame | None, date: str, zone_id: str, anomalies: pd.DataFrame | None) -> go.Figure:
    fig = go.Figure()
    for k in ("NDVI", "NDRE", "NDMI"):
        if k in zone_ts and zone_ts[k].notna().any():
            fig.add_trace(go.Scatter(x=zone_ts.date, y=zone_ts[k], name=f"{k} · zone {zone_id}", mode="lines+markers",
                                     line=dict(color=INDEX_COLORS[k], width=2.5), marker=dict(size=5)))
        if farm_ts is not None and k in farm_ts and farm_ts[k].notna().any():
            fig.add_trace(go.Scatter(x=farm_ts.date, y=farm_ts[k], name=f"{k} · whole farm", mode="lines",
                                     line=dict(color=INDEX_COLORS[k], width=1.3, dash="dot"), opacity=0.7))
    for k in ("NDVI", "NDMI"):
        if anomalies is not None and f"{k}_anomaly" in anomalies:
            a = anomalies[anomalies[f"{k}_anomaly"]]
            if len(a):
                fig.add_trace(go.Scatter(x=a.date, y=a[k], mode="markers", name=f"{k} anomaly (sudden drop)",
                                         marker=dict(symbol="x", size=13, color="#D64541", line=dict(width=2))))
    fig.add_shape(type="line", x0=date, x1=date, y0=0, y1=1, yref="paper", line=dict(color="#0B2530", dash="dash", width=1))
    fig.update_yaxes(title="Index value")
    return _layout(fig, 400)


def lst_weather_chart(lst_ts: pd.DataFrame | None, wx: pd.DataFrame | None, date: str) -> go.Figure:
    fig = go.Figure()
    if lst_ts is not None and not lst_ts.empty:
        fig.add_trace(go.Scatter(x=lst_ts.date, y=lst_ts.LST, name="Land surface temp. (Landsat / zone)",
                                 mode="lines+markers", line=dict(color="#D64541", width=2.5)))
    if wx is not None and not wx.empty:
        fig.add_trace(go.Scatter(x=wx.date, y=wx.air_temp_max_c, name="Air temp. max (ERA5-Land)",
                                 mode="lines", line=dict(color="#F2B01E", width=1.4)))
        fig.add_trace(go.Bar(x=wx.date, y=wx.precip_mm, name="Precipitation mm (ERA5-Land)", yaxis="y2",
                             marker_color="#2563EB", opacity=0.6))
        fig.update_layout(yaxis2=dict(title="mm", overlaying="y", side="right", showgrid=False, rangemode="tozero"))
    fig.add_shape(type="line", x0=date, x1=date, y0=0, y1=1, yref="paper", line=dict(color="#0B2530", dash="dash", width=1))
    fig.update_yaxes(title="°C")
    return _layout(fig, 340)


def zone_indicator_bars(zone: dict, farm_zones: pd.DataFrame) -> go.Figure:
    ok = farm_zones[farm_zones.cls.isin(["HEALTHY", "MODERATE", "HIGH"])]
    names = ["NDVI", "NDRE", "NDMI"]
    zv = [zone.get(n.lower()) for n in names]
    fv = [ok[n.lower()].median() if len(ok) else np.nan for n in names]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=names, y=zv, name=f"Zone {zone['zone_id']}", marker_color=CLASS_COLORS[zone["cls"]]))
    fig.add_trace(go.Bar(x=names, y=fv, name="Farm median (cropped zones)", marker_color="#9AA3A8"))
    fig.update_layout(barmode="group")
    return _layout(fig, 280)


def anomaly_score_hist(pix: pd.DataFrame) -> go.Figure:
    """Distribution of Isolation Forest anomaly scores with the decision threshold."""
    fig = go.Figure()
    for flag, name, color in ((False, "Typical pixels", "#65A30D"), (True, "Unusual pixels", "#D64541")):
        fig.add_trace(go.Histogram(x=pix.loc[pix.anomaly == flag, "anomaly_score"], name=name,
                                   marker_color=color, opacity=0.8, nbinsx=40))
    thr = pix.loc[pix.anomaly, "anomaly_score"].min()
    fig.add_shape(type="line", x0=thr, x1=thr, y0=0, y1=1, yref="paper", line=dict(color="#0B2530", dash="dash"))
    fig.add_annotation(x=thr, y=0.9, yref="paper", text=" decision threshold", showarrow=False, xanchor="left")
    fig.update_layout(barmode="overlay")
    fig.update_xaxes(title="Anomaly score (higher = more unusual)")
    fig.update_yaxes(title="Pixels")
    return _layout(fig, 320)


def zone_anomaly_bars(zones: pd.DataFrame, expected: float) -> go.Figure:
    """Share of unusual pixels per zone, coloured by the rule-based class, with the model's expected share."""
    z = zones.dropna(subset=["anomaly_share"]).sort_values("zone_id")
    fig = go.Figure(go.Bar(x=z.zone_id, y=z.anomaly_share * 100, marker_color=[CLASS_COLORS[c] for c in z.cls],
                           customdata=[CLASS_LABELS[c] for c in z.cls],
                           hovertemplate="Zone %{x}<br>%{y:.1f}% unusual<br>Rule class: %{customdata}<extra></extra>"))
    fig.add_shape(type="line", x0=-0.5, x1=len(z) - 0.5, y0=expected * 100, y1=expected * 100,
                  line=dict(color="#0B2530", dash="dash"))
    fig.add_annotation(x=0, y=1.0, xref="paper", yref="paper", text=f"- - - farm-wide share set by model ({expected:.0%})",
                       showarrow=False, xanchor="left", yanchor="bottom", font=dict(size=11))
    fig.update_yaxes(title="Unusual pixels in zone (%)")
    return _layout(fig, 320)


def zone_comparison_chart(zones: pd.DataFrame, column: str, title: str, selected: str | None) -> go.Figure:
    """Bar chart of one existing per-zone value across all zones, coloured by rule class; selected zone outlined."""
    z = zones.sort_values("zone_id")
    fig = go.Figure(go.Bar(
        x=z.zone_id, y=z[column], marker_color=[CLASS_COLORS[c] for c in z.cls],
        marker_line=dict(color=["#0B2530" if zid == selected else "rgba(0,0,0,0)" for zid in z.zone_id], width=3),
        customdata=[CLASS_LABELS[c] for c in z.cls],
        hovertemplate="Zone %{x}<br>" + title + ": %{y:.3f}<br>%{customdata}<extra></extra>",
    ))
    fig.update_yaxes(title=title)
    return _layout(fig, 320)


def anomaly_scatter(pix: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for flag, name, color in ((False, "Typical pixels", "#65A30D"), (True, "Unusual pixels (Isolation Forest)", "#D64541")):
        d = pix[pix.anomaly == flag]
        fig.add_trace(go.Scattergl(x=d.NDVI, y=d.NDMI, mode="markers", name=name,
                                   marker=dict(size=5 if not flag else 7, color=color, opacity=0.55 if not flag else 0.9)))
    fig.update_xaxes(title="NDVI")
    fig.update_yaxes(title="NDMI")
    return _layout(fig, 380)
