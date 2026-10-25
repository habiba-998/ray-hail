# رَيّ | RAYY — satellite screening of irrigated farms in Hail

RAYY is an Arabic-first **decision-support prototype**. It answers one question:

> **Which farm zones should be inspected first, what evidence makes them a priority, and what should be checked next?**

It analyses Sentinel-2 vegetation indices, Landsat land-surface temperature and ERA5-Land weather context over a
regular grid of zones, and ranks the zones for **field inspection**.

> RAYY is a **screening and prioritisation tool**. It is **not** a plant-disease diagnostic system, **not** a
> soil-moisture sensor, **not** an irrigation controller and has **no proven water savings**. All thresholds are
> provisional and uncalibrated. No accuracy, precision, recall, water-saving or lead-time figures exist.
> The project has no endorsement from the Ministry of Environment, Water and Agriculture (MEWA) or any other body.

**Intended users:** farm managers, agronomists and irrigation teams on irrigated (mostly centre-pivot) farms in Hail.

---

## 1. Primary use case (decision recorded in this revision)

| Option | Supported by current code / data? | Decision |
|---|---|---|
| **Agricultural water-stress screening & inspection prioritisation** | Yes: the whole pipeline (Sentinel-2 NDMI/NDRE/NDVI, Landsat LST, ERA5-Land, zone grid, rules) is built for it | **Primary use case (kept)** |
| Vegetation-cover monitoring (afforestation / restoration) | Partly: NDVI is computed, but there are no restoration sites, no multi-year baselines, no land-cover validation | Not adopted. Would need defined sites, long baselines and validation data |
| Greywater treatment, food-loss reduction | No related data or code | Out of scope |

This decision is **provisional**: it follows the existing code, not validated evidence of impact.

## 2. What the app shows (Arabic-first interface)

| Page | Content |
|---|---|
| Header (all pages) | Brand, farm picker, data-status chip (REAL / DEMO / UNAVAILABLE), latest valid observation date and its age, analysis period; one navigation bar (no duplicate sidebar menu) |
| 🏠 الرئيسية | Four status tiles: zones that **need inspection / need follow-up / show no clear abnormal signal / have insufficient data**; no-crop zones; the next action (highest-priority zone card + button) |
| 🗺️ خريطة المزرعة | Sentinel-2 true-colour image with coloured, icon-labelled zones; tap a zone to select it; legend; note that the grid is an analysis grid, not field or pivot boundaries |
| 📍 المناطق | Why the zone was flagged, current indicator values, data quality (clear-pixel %, crop cover, indicators evaluated), the reference used, same-zone temporal comparison (or "insufficient data"), alternative explanations (hypotheses), recommended field checks, crop-specific common problems (sourced) |
| 💧 الري | Irrigation-check workflow: highest-priority zone, hedged "possible water stress" wording, possible causes, grouped checklists. No volumes, no automatic control |
| 📋 سجل الفحص الميداني | Non-photographic inspection log: date, zone, what was found, irrigation issue yes/no, alternative causes, optional measured soil moisture, inspector, notes; plus a count-only comparison of satellite flags with inspections |
| 🔬 التفاصيل التقنية | Indices, bands, resolutions, masks, thresholds (marked provisional), priority-index formula, temporal rule, Isolation Forest and Random Forest status, limitations, values used in this run |
| ℹ️ عن رَيّ | What RAYY does and does not do, privacy |

**Removed in this revision:** the plant-photography workflow (photo upload, colour screening of photos, photo-based
"first suspicion" of a disease, photo storage, related navigation, help text and tests). Satellite imagery, maps,
indices, temporal analysis and the inspection history were kept.

## 3. Evidence categories (never mixed)

1. **Satellite observations** – Sentinel-2 L2A reflectance, Landsat ST_B10, ERA5-Land values.
2. **Calculated indicators** – NDVI, NDRE, NDMI, LST anomaly, NDVI change, relative NDVI.
3. **Rule-based screening results** – zone classes from provisional thresholds.
4. **ML anomaly output** – Isolation Forest share of unusual pixels (secondary hint only).
5. **Hypotheses** – "possible water stress", "possible heat", … (always labelled as needing field verification).
6. **Field records** – typed inspection notes; user-entered, **not verified ground truth**.

## 4. Analytical workflow

```
Sentinel-2 dates over the farm (≥50 % clear)  →  latest clear date + clear date ≥10 days earlier
   → cloud mask (SCL) → NDVI / NDRE / NDMI  →  crop mask (NDVI > 0.25)
   → Landsat 8/9 LST (±12-day median, QA-masked)
   → zone statistics on a 4×4 grid (20 m)  →  rules (0/1/2 points per indicator)  →  class + priority index
   → Isolation Forest on sampled crop pixels (secondary)  →  same-zone temporal comparison  →  UI
```

### Data sources

| Data | Earth Engine ID | Resolution | Role |
|---|---|---|---|
| Sentinel-2 MSI L2A | `COPERNICUS/S2_SR_HARMONIZED` | 10 m (B2,B3,B4,B8), 20 m (B5,B11,SCL); ~5-day revisit | Indices, true colour, cloud mask |
| Landsat 8/9 C2 L2 | `LANDSAT/LC08/C02/T1_L2`, `LANDSAT/LC09/C02/T1_L2` | ST_B10 100 m native (served at 30 m) | Land-surface temperature |
| ERA5-Land daily | `ECMWF/ERA5_LAND/DAILY_AGGR` | ~11 km reanalysis, published days late | Weather **context only**; not field soil moisture |
| Sentinel-1 GRD | `COPERNICUS/S1_GRD` | — | Code kept (`s1_zone_stats`), not used by the UI or scoring |
| Esri World Imagery | basemap | — | Visual reference only |
| NCM (Saudi met. centre) | — | — | **Not connected** (licence required); slot in `src/weather.py` |

### Index formulas

| Index | Formula | Bands / native resolution |
|---|---|---|
| NDVI | (B8 − B4)/(B8 + B4) | B8 10 m, B4 10 m |
| NDRE | (B8 − B5)/(B8 + B5) | B8 10 m, B5 20 m |
| NDMI (Gao NDWI) | (B8 − B11)/(B8 + B11) | B8 10 m, B11 20 m |
| LST (°C) | ST_B10 × 0.00341802 + 149.0 − 273.15 | 100 m native |

Reflectance = DN / 10000. Zone statistics are reduced at 20 m, so the 10 m bands are aggregated and the 20 m bands are
used at their native scale. The indices are proxies for canopy condition; they do **not** measure root-zone soil
moisture or delivered irrigation volume.

### Data-quality rules

- Sentinel-2 SCL classes masked: 0 no data, 1 saturated, 3 cloud shadow, 8/9 medium/high cloud, 10 thin cirrus, 11 snow.
- A date is used only if the farm rectangle is ≥ 50 % clear (measured on SCL over the farm, not the granule).
- Landsat QA_PIXEL bits masked: dilated cloud (1), **cirrus (2, added in this revision)**, cloud (3), cloud shadow (4); scene cloud cover < 60 %.
- A zone with < 50 % clear pixels → **Insufficient data**. A zone with < 10 % crop pixels → **No active crop**.
- A zone with fewer than **3 evaluable indicators → Insufficient data** (added: one indicator never decides a class).
- The LST composite is not simultaneous with the Sentinel-2 date and is 100 m; it is compared only within the farm.
- Earth Engine results are cached for 1 hour; the header always shows the image date and its age, with a warning when the latest valid image is older than 20 days.

### Zone geometry

A regular 4×4 grid over a ~4 × 4 km square. It is an **analysis grid**, not field, parcel or pivot boundaries.

### Rules and priority index (provisional, uncalibrated)

| Indicator | 2 points | 1 point |
|---|---|---|
| NDMI | < 0.05 | < 0.18 |
| NDRE | < 0.20 | < 0.30 |
| NDVI ÷ farm median of cropped zones (same date) | < 0.75 | < 0.90 |
| LST − farm mean of cropped zones (°C) | > +3.0 | > +1.5 |
| NDVI change vs clear date ≥ 10 days earlier | < −0.10 | < −0.05 |

**Priority index = points ÷ maximum possible points of the evaluable indicators** (0–1). It is a heuristic ordering,
**not a probability**, and is never shown with a % sign. Index ≥ 0.50 → *needs inspection*; ≥ 0.25 → *needs follow-up*;
otherwise *no clear abnormal signal*. Raw index values are never summed; each indicator is first converted to points
by its own threshold. Thresholds live in `src/config.py`.

### Temporal analysis

For the selected zone: the latest NDVI is compared with the median of the up-to-3 preceding clear observations of the
same zone. ≥ 4 clear observations are required, otherwise **"insufficient data"** is shown. A drop > 0.08 (provisional)
is a *decline*; if the previous observation also dropped it is a *repeated decline*. No seasonal baseline, crop type or
growth stage is modelled, so harvest, cutting, planting and phenology also appear as change. The temporal result is
shown as evidence; it does not change the zone class.

### Machine learning

- **Isolation Forest – retained as a secondary hint.** Features: NDVI, NDRE, NDMI (+LST when ≥ 90 % available) of up to
  ~3–4k sampled crop pixels; reference population = the same farm on the same date; needs ≥ 50 samples.
  `contamination = 0.05` means ~5 % of pixels are flagged *by construction*; a zone is mentioned only when its share is
  ≥ 2× that and it has ≥ 30 sampled pixels. It is not a probability of stress, does not identify a cause and is not
  part of the priority index. Retained because it can point at zones whose combination of indices is unusual even
  when no single threshold is crossed; it is shown only as a note.
- **Random Forest – not trained, not active.** No verified labels exist. The dormant training code in `src/ml.py`
  runs only with `data/ground_truth/labels.csv` (real, independently collected labels). No metrics are reported.
- **LSTM / CNN – not added.** There is no defined prediction task with sufficient labelled data and a baseline to beat.

### Validation framework

`src/validation.py` counts, from real-data inspection records: flagged zones inspected and confirmed
(*confirmation rate*, a precision proxy), and zones classed "no clear abnormal signal" that were inspected and had a
problem (*missed rate*, biased unless such zones are inspected at random). Demo records are excluded. Below 30
inspections of flagged zones the app states that nothing reliable can be concluded. When records are later used to
train or tune anything, split by farm/zone **and** by date (never by random row) to avoid spatial and temporal leakage.

Outcome measures that can be collected later (no values exist today): share of flagged zones confirmed in the field;
zones assessable with valid observations; time to prioritise inspections; agreement with verified observations;
false-alert frequency; change in inspection workload against a **defined** baseline.

## 5. Real, demo and unavailable data

| State | When | What the user sees |
|---|---|---|
| **REAL** | Earth Engine credentials configured and retrieval succeeded | "بيانات فضائية حقيقية" + latest valid observation date and age |
| **DEMO** | **No** Earth Engine credentials configured at all | Yellow banner on every page: simulated data, not a real farm. Simulated dates are labelled as such |
| **UNAVAILABLE** | Credentials configured but connection/retrieval failed, or no clear image | Red status + category message (credentials / network / no clear image / other) and a retry button. **No results are shown and demo data is never substituted** |

## 6. Installation and running

Python 3.11–3.12.

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1          # Windows PowerShell   (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
streamlit run app.py
```

Without credentials the app opens in DEMO mode.

### Environment variables / secrets (names only)

| Name | Where | Purpose |
|---|---|---|
| `EE_PROJECT` | env var or Streamlit secret | Earth Engine Cloud project ID |
| `EE_SERVICE_ACCOUNT_JSON` | env var or Streamlit secret | Service-account key JSON (string) |
| `[ee_service_account]` | Streamlit secrets table | Same key as individual fields (see `.streamlit/secrets.toml.example`) |
| `[supabase] url`, `service_key` | Streamlit secrets | Optional persistent storage of inspection records |
| `RAY_DATA_DIR` | env var | Optional local SQLite folder (used by tests) |

Never commit `.streamlit/secrets.toml` or key files (they are git-ignored).

### Deployment

Streamlit Community Cloud redeploys automatically when the connected branch is pushed (see [DEPLOYMENT.md](DEPLOYMENT.md)).
If you use Supabase and created the tables with an earlier schema, run `db/migrations/2026-10_inspection_log.sql` once.

## 7. Tests

**No credentials needed (demo / synthetic data):**

```bash
python -m pytest tests/test_rayy.py -q   # unit tests: indices, scoring, missing/cloudy data, temporal, IF, states, records
python -m tests.core_test                # knowledge base, fusion, storage, weather summary
python -m tests.smoke_test               # demo pipeline without UI
python -m tests.ui_test                  # headless UI in demo mode + a deliberately non-existent Earth Engine project
```

**Need real Google Earth Engine credentials** (`earthengine authenticate` or a service account, and a project):

```bash
python -m tests.ee_check YOUR_PROJECT_ID # real data path without UI: dates, zone statistics, Landsat, map tiles
python -m tests.ui_test YOUR_PROJECT_ID  # everything above + every page again on real data
```

On Windows set `PYTHONUTF8=1` so the Arabic test output prints.

## 8. Status of each part

**Implemented and tested (automated, demo/synthetic data):** index formulas; zone scoring incl. cloudy, no-crop and
too-few-indicator cases; temporal summary; Isolation Forest behaviour and per-zone minimum; REAL/DEMO/UNAVAILABLE
selection and failure classification; inspection-record validation and storage; validation counting; UI pages render
without errors, contain no photo workflow, and a failing Earth Engine project shows UNAVAILABLE without demo data.

**Run against real Earth Engine data (functional, not scientific validation):** `tests.ee_check` and `tests.ui_test PROJECT`
pass on this revision (real Sentinel-2/Landsat retrieval, zone statistics, map tiles, every page on real data).

**Implemented but not validated:** every threshold and the priority index; the cause-fit ranking in `src/fusion.py`;
Isolation Forest usefulness; LST comparability.

**Planned:** field-boundary detection to replace the grid; crop-type and growth-stage-aware baselines; seasonal
same-zone baselines from previous years; calibration with paired field measurements; ET-based water requirement.

## 9. Data needed before any scientific performance claim

Paired satellite/field observations per crop in Hail (soil-moisture probes, leaf water potential or standardised visual
scores), collected independently of RAYY's rules, with inspections of unflagged zones chosen at random; documented
inspection procedure; real field/pivot boundaries; crop calendars. Water-saving claims need a controlled comparison.

## 10. Repository layout

```
app.py                     entry point: settings, data-status handling, pipeline calls
src/config.py              AOIs, dataset IDs, ALL thresholds
src/data_acquisition.py    Earth Engine queries (Sentinel-2, Landsat, ERA5-Land, Sentinel-1)
src/demo_data.py           simulated farm (DEMO only)
src/preprocessing.py       grid, cloud masks, scaling
src/indices.py             index formulas
src/analysis.py            rules, priority index, temporal summary, recommendations
src/ml.py                  Isolation Forest (active), Random Forest (dormant)
src/fusion.py              rule-based fit of possible causes (not probabilities)
src/status.py              REAL / DEMO / UNAVAILABLE, failure categories, freshness
src/storage.py             inspection records (SQLite / Supabase)
src/validation.py          satellite-flag vs inspection counts
src/weather.py, knowledge.py, visualization.py, raster_io.py
src/ui/                    farmer.py (pages), details.py (technical page), common.py, i18n.py, styles.py
db/schema.sql, db/migrations/
tests/
```

---
*Contains modified Copernicus Sentinel data (Earth Engine mode). Landsat courtesy of USGS. ERA5-Land: Copernicus Climate Change Service. Basemap © Esri.*
