# رَيّ | RAY — Smarter Irrigation from Space

**University of Hail Space Innovation Hackathon 2026 · Track: AI & Space Data Science**

RAY is a hackathon prototype that uses satellite Earth-observation data to show where irrigated fields in the Hail region show signs of **potential** water stress, so farm teams can **inspect the right places first** and make better-informed irrigation decisions.

```
Satellite Data  →  AI Analysis  →  Water Stress Detection  →  Irrigation Decision Support
```

> **This is a prototype, not a production or agronomic diagnostic system.** Stress classes come from transparent rules with uncalibrated thresholds. RAY does not calculate irrigation volumes, and no water savings or detection lead time have been measured.

---

## 1. Why this matters

Saudi Arabia is highly water-scarce and agriculture is its largest water user. Hail is an important farming region with centre-pivot irrigation in a hot, dry climate. There, over-irrigating wastes groundwater and under-irrigating (for example from a blocked nozzle or pressure loss) damages crops. Satellites observe every field every few days at no cost. RAY turns those observations into a simple map of where to look.

## 2. What the app does

> **Current interface: farmer-only (Arabic).** The app opens directly on the farmer pages (الرئيسية، خريطة المزرعة، المناطق، فحص النبات، الري، سجل المزرعة، عن رَيّ). No technical settings, data-source names or indices are shown. The technical dashboard described below (`src/ui/technical.py`) is kept in the code for developers and judges reading the code, but it is not reachable from the interface. The farmer map image is produced with `ee.data.computePixels`, so it does not need the `earthengine.maps.create` permission. Data-loading errors are logged on the server and shown to the farmer only as a plain message.

RAY has two modes that share the **same results**; switching mode never recomputes the analysis. There is a language switch (**العربية | English**) at the top, and a data badge that always says whether you are seeing **real Google Earth Engine data** or **DEMO DATA**.

### 👨‍🌾 Farmer mode (default, Arabic first)
One screen → one decision, in plain language, green + white, large touch targets, works on phones. The farmer journey: **Where is the problem? → What could the cause be? → What do I photograph? → What do I check? → What is the better decision?**

| Page | Question it answers | Content |
|---|---|---|
| **🏠 الرئيسية / Home** | What needs my attention today? | Farm status, 🟢/🟡/🔴 zone counts, the most important zone (e.g. 📍 A4 · "تحتاج فحص — تغير غير طبيعي محتمل") with **افحص المنطقة**, anomaly-only notes (e.g. B4), crop selection |
| **🗺️ خريطة المزرعة / Map** | Where? | Real Sentinel-2 image, zones coloured + icon-labelled; tap a zone → status + **عرض التفاصيل** |
| **📍 المناطق / Zones** | What could the cause be? | Six possible causes (💧 water, ☀️ heat, 🦠 disease, 🐛 pest, 🧪 nutrient, 🌱 other) ranked by *fit with the evidence* (strong/moderate/weak/none) with "why?", recent weather, the selected crop's common diseases & pests (sourced, with licensed reference images), technical values in an expander |
| **📷 فحص النبات / Plant check** | What do I photograph and check? | Zone + crop → photo upload/preview → symptom checklist, soil, spread → **حلّل**: colour screening of the photo, possible causes, "symptoms match…" crop problems, what to check → save observation → record the **field result** (ground truth) |
| **💧 الري / Irrigation** | What is the better decision? | Per-zone checklist (soil moisture, water reaching, plants, disease/pest, weather), "don't add water before you know the cause", crop seasonal water need (FAO), no-crop zones. No automatic irrigation, no volumes |
| **ℹ️ عن رَيّ / About** | — | Concept, data sources, privacy, where observations are stored, all limitations |

Farm status is derived from the existing classes (any HIGH → "an area needs inspection"; any MODERATE → "follow-up"; else "normal"). Possible causes come from `src/fusion.py` — transparent, rule-based evidence points (satellite rules, Isolation-Forest share, weather, farmer answers, photo colours). **They are not probabilities and not a diagnosis.**

### 🔬 Technical mode (AI & Technical Analysis)
The full expert dashboard for judges and specialists:

| Tab | Content |
|---|---|
| **Overview** | Farm location, analysis date, status counts, zone grid, key findings, data provenance |
| **Satellite Map** | **True Color, NDVI, NDRE, NDMI, LST, Water Stress** layers; click a zone for its indicators |
| **Analytics** | Zone comparison chart (stress score, NDVI, NDRE, NDMI, LST, unusual pixels) for the selected zone, NDVI/NDRE/NDMI time series (zone vs farm) with sudden-drop markers, trend slopes, Landsat LST + ERA5-Land weather, zone table, CSV export, Isolation Forest scatter |
| **Water Intelligence** | Zone status, bilingual recommendation, per-rule points breakdown, zone-vs-farm indicators, inspection list |
| **AI & Method** | 8-step live pipeline (imagery → preprocessing → spectral features → thermal → anomaly detection → stress assessment → priority zones → field inspection), Isolation Forest details, transparent rules, priority zones, Random Forest (NOT TRAINED), indices, real-vs-demo table |
| **Sources & Fusion** | Evaluated sources (integrated / context / not used and why), Sentinel-1 SAR per zone, weather connectors (ERA5-Land active, NCM not connected), the fusion rule table and live causes for the selected zone |
| **Crops & Knowledge** | Crop database, diseases & pests with scientific names and source links, image licences, all sources |
| **Data & IoT** | Storage backend and counts (no individual records shown), database architecture, IoT readiness |
| **Limitations** | The full limitations list |

Settings (data source, Earth Engine project, area, zone grid, dates, analysis date, rule thresholds) are in the collapsible sidebar (**»** at the top left).

## 3. Architecture

```
ray/
├── app.py                    # settings sidebar + unchanged pipeline calls + mode/language switch
├── requirements.txt          # core dependencies
├── requirements-optional.txt # rasterio (GeoTIFF export), geemap
├── .streamlit/
│   ├── config.toml           # theme
│   └── secrets.toml.example  # EE project / service account template
├── assets/logo.svg
├── data/
│   ├── README.md
│   ├── knowledge/            # crops.json, problems.json, images.json, sources.json (sourced, versioned)
│   ├── user_data/            # local SQLite + farmer photos – git-ignored, never committed
│   └── ground_truth/labels_template.csv   # format for real field labels
├── db/schema.sql             # full PostgreSQL / Supabase schema (active + ready tables)
├── src/
│   ├── config.py             # AOIs, dataset IDs, ALL thresholds, colours
│   ├── data_acquisition.py   # REAL data: Earth Engine auth + Sentinel-2 / Landsat / ERA5 queries
│   ├── demo_data.py          # DEMO DATA: synthetic farm (clearly labelled)
│   ├── preprocessing.py      # zone grid, S2 SCL cloud mask, scaling, Landsat LST conversion
│   ├── indices.py            # NDVI / NDRE / NDMI formulas (numpy + EE), palettes, explanations
│   ├── analysis.py           # rule-based stress scoring, anomalies, trends, recommendations
│   ├── ml.py                 # Isolation Forest (unsupervised) + Random Forest (only with real labels)
│   ├── visualization.py      # Folium map, Plotly charts
│   ├── raster_io.py          # optional GeoTIFF export (rasterio)
│   ├── knowledge.py          # loads + validates data/knowledge/*.json
│   ├── fusion.py             # evidence fusion → possible causes (rule-based, traceable)
│   ├── image_analysis.py     # farmer photo: quality checks + colour screening (pluggable; not a classifier)
│   ├── weather.py            # weather connectors: ERA5-Land (active), NCM (slot, not connected)
│   ├── storage.py            # observations/photos/validations: Supabase or local SQLite
│   └── ui/                   # presentation only – no scientific logic
│       ├── farmer.py         # Farmer mode pages
│       ├── technical.py      # Technical mode (original dashboard tabs + Limitations)
│       ├── common.py         # cached Earth Engine calls, shared map, zone picker, limitations
│       ├── i18n.py           # English / Arabic text
│       └── styles.py         # CSS (large touch targets, mobile, right-to-left)
└── tests/
    ├── smoke_test.py         # end-to-end check of the demo pipeline without the UI
    ├── ee_check.py           # real Earth Engine data check
    ├── core_test.py          # knowledge base, fusion, photo screening, storage, weather
    └── ui_test.py            # headless test of every mode / page / language (Streamlit AppTest)
```

The flow is **acquisition → preprocessing → indices → zone statistics → rule scoring + ML → visualisation**. Earth Engine mode and demo mode return the same tables (one row per zone), so the analysis and UI code is identical for both.

## 4. Data sources

| Data | Dataset (Earth Engine ID) | Resolution / revisit | Used for |
|---|---|---|---|
| Sentinel-2 MSI L2A surface reflectance | `COPERNICUS/S2_SR_HARMONIZED` | 10–20 m, ~5 days | True colour, NDVI, NDRE, NDMI, cloud mask (SCL) |
| Landsat 8 & 9 Collection-2 L2 | `LANDSAT/LC08/C02/T1_L2`, `LANDSAT/LC09/C02/T1_L2` | 100 m thermal (served at 30 m), ~8 days combined | Land surface temperature (ST_B10) |
| ERA5-Land daily aggregates | `ECMWF/ERA5_LAND/DAILY_AGGR` | ~11 km, daily reanalysis (published several days late) | Air temperature, humidity (from dew point), wind, precipitation (context) |
| Sentinel-1 GRD | `COPERNICUS/S1_GRD` (IW, VV+VH) | 10 m, 12 days over this farm | Backscatter per zone — context only, not scored |
| National Center for Meteorology (NCM) | — | — | **Not connected**: data access requires a licence for a legal entity ([service page](https://www.ncm.gov.sa/en/services/our-services/meteorological-data-publishing-or-utilization-service)); connector slot in `src/weather.py` |
| Crop / disease / pest knowledge | FAO, UC Statewide IPM, EPPO, peer-reviewed articles | — | `data/knowledge/` with source URL and retrieval date per record |
| Reference images | Wikimedia Commons | — | Licence + author recorded per image; shown only when opened |
| MODIS / VIIRS / Sentinel-3 | evaluated | 250 m – 1 km | **Not used**: coarser than the 1 km zones |
| Esri World Imagery | tile basemap | — | Visual reference only (never analysed) |

Processing details:
- **Cloud masking:** Sentinel-2 Scene Classification Layer. Removed: no-data, saturated, cloud shadow, medium/high-probability cloud, cirrus, snow. Scenes are pre-filtered by `CLOUDY_PIXEL_PERCENTAGE`. Zones with less than 50% clear pixels are marked *Insufficient data*.
- **Scaling:** reflectance = DN / 10000; LST (°C) = ST_B10 × 0.00341802 + 149.0 − 273.15; Landsat QA_PIXEL cloud, shadow and dilated-cloud bits are masked.
- **Thermal matching:** Landsat scenes within ±12 days of the Sentinel-2 date are median-composited. The dates used are shown in the Overview tab.

## 5. Indices

| Index | Formula (Sentinel-2) | Interpretation |
|---|---|---|
| **NDVI** | (B8 − B4)/(B8 + B4) | Vegetation amount and greenness. Desert soil is usually < 0.2 and dense irrigated crops > 0.6 |
| **NDRE** | (B8 − B5)/(B8 + B5) | Chlorophyll, sensitive in dense canopies. Low values can reflect nutrient or water stress |
| **NDMI** (= Gao NDWI) | (B8 − B11)/(B8 + B11) | Canopy water content. Watered canopies are typically > 0.2 |
| **LST** | Landsat ST_B10 | A canopy warmer than the rest of the farm may indicate reduced transpiration |

## 6. Water-stress model (prototype decision support)

A zone is **cropped** if ≥ 10% of its clear pixels have NDVI > 0.25. Only cropped pixels are averaged. Each available indicator adds 0, 1 or 2 points:

| Indicator | 2 points | 1 point |
|---|---|---|
| NDMI | < 0.05 | < 0.18 |
| NDRE | < 0.20 | < 0.30 |
| NDVI ÷ farm median (cropped zones) | < 0.75 | < 0.90 |
| LST − farm mean (°C) | > +3.0 | > +1.5 |
| NDVI change vs clear date ≥ 10 days earlier | < −0.10 | < −0.05 |

**Score = points / maximum possible points** (indicators without data are skipped).
🟢 **GREEN** < 25% ≤ 🟡 **YELLOW** < 50% ≤ 🔴 **RED**. ⚪ grey = no active crop, ⚫ = insufficient clear data.

All thresholds live in `src/config.py` and can be adjusted live in the sidebar. **They have not been calibrated against Hail field data.** Vegetation stress can also come from heat, disease, nutrient deficiency, salinity, pests, harvest or cutting, or growth stage.

**Recommendations**
- GREEN: *No significant vegetation stress detected. Continue monitoring.*
- YELLOW: *Moderate stress detected. Inspect irrigation and field conditions.*
- RED: *High potential water stress detected. Inspect irrigation before applying water.*
- GREY: *No active crop canopy detected. If this area is being irrigated, check whether that water is needed.*

## 7. AI / machine learning

- **Isolation Forest (active, unsupervised).** Fitted each time to up to ~4,000 cropped-pixel samples (NDVI, NDRE, NDMI, LST) from the selected date. It flags the ~5% most statistically unusual pixels, and the share per zone is shown as *Unusual pixels %*. It needs no labels and makes no claim about cause. It is **not** part of the stress score.
- **Random Forest (supervised): NOT TRAINED.** It is reserved for future supervised calibration once real field observations are available. No ground-truth labels exist for these fields, so the app does not train it and reports **no accuracy, precision, recall or F1**. We deliberately do not generate synthetic labels, including labels from our own rules, because the model would only learn to copy the rules. `src/ml.py` keeps the training code (≥ 30 rows, ≥ 2 classes, ≥ 5 per class) for when real labels exist.
- The **AI & Method** tab shows the live pipeline for the current date: satellite features → Isolation Forest → multi-indicator stress assessment → priority zones → field inspection. It includes the number of samples, unusual pixels and their share, the features used, the anomaly-score distribution, unusual-pixel share per zone, and typical-vs-unusual feature means. The farm-wide unusual share is fixed by `contamination = 0.05`; the informative output is *where* unusual pixels cluster.

## 8. Temporal analysis

For the selected zone and the whole farm, RAY extracts a mean index value for every clear Sentinel-2 acquisition. An observation is flagged as a **sudden-drop anomaly** when it falls more than 0.08 below the median of the previous three observations. A trend slope (per 10 days, last 6 observations) is also reported.

## 9. Installation

Requires **Python 3.11–3.12** (64-bit; tested on 3.12). Dependencies are pinned to the tested versions. On Windows, install it from python.org and tick *Add python.exe to PATH*.

```bash
cd ray
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS / Linux:
source .venv/bin/activate
pip install -r requirements.txt
# optional (GeoTIFF export):
pip install -r requirements-optional.txt
```

## 10. Run

```bash
streamlit run app.py
```

The app opens at http://localhost:8501 in **Farmer mode**. With no Earth Engine project configured it uses **Demo mode**, which needs no account or internet apart from the basemap tiles. With `EE_PROJECT` set, it loads real data.

Full UI test (every mode, page and language):

```bash
python -m tests.ui_test YOUR_PROJECT_ID
```

Pipeline self-test without the UI:

```bash
python -m tests.smoke_test
```

## 11. Connecting real data: Google Earth Engine

1. Sign up for Earth Engine at https://earthengine.google.com (noncommercial/academic use is free) and create or register a **Google Cloud project** for Earth Engine.
2. Authenticate once on the machine: `earthengine authenticate` (opens a browser and stores credentials locally).
3. Start the app, choose **Google Earth Engine (real satellite data)** in the sidebar and enter your **Cloud project ID**. Alternatively, set it beforehand:
   - environment variable `EE_PROJECT=your-project-id`, or
   - `.streamlit/secrets.toml` (copy `secrets.toml.example`).
4. For a hosted deployment, use a **service account**. Put `EE_PROJECT` and an `[ee_service_account]` table (the fields of the JSON key) in the platform's secret store; never put them in the repository. See **[DEPLOYMENT.md](DEPLOYMENT.md)** for Streamlit Community Cloud. `EE_SERVICE_ACCOUNT_JSON` (a JSON string, as an env var or secret) is also accepted. When a service account is configured, the project field in the sidebar is locked.

When an Earth Engine project is configured (`EE_PROJECT` in secrets or the environment), the app opens in Earth Engine mode. If initialisation fails, it **does not fall back silently**. The page says "Real satellite data could not be loaded", shows the exact error and connection steps, and offers *Retry connection* (sidebar) plus an explicit **Use Demo Mode** button. Demo results appear only after that click, and they are always labelled DEMO DATA.

Then pick an area preset. The preset centres were located from real Sentinel-2 data: 4 km cells ranked by their share of NDVI > 0.4 in a cloud-masked composite for 1–22 Sep 2026. Fields change between seasons, so confirm with the **True Color** layer and adjust latitude/longitude if needed.

Verify the real-data path without the UI: `python -m tests.ee_check YOUR_PROJECT_ID`.

## 12. Real data vs demo data

| | Earth Engine mode | Demo mode |
|---|---|---|
| Imagery and indices | **Real** Sentinel-2 | **Simulated** (`src/demo_data.py`) |
| LST | **Real** Landsat 8/9 | Simulated |
| Weather | **Real** ERA5-Land | not shown |
| Stress classes | Rules on real indices | Rules on simulated indices |
| Basemap | Esri imagery (reference) | Esri imagery (reference) |

In demo mode, a yellow **DEMO DATA – SIMULATED** banner appears on every screen, downloads carry a `_DEMO` suffix, and map attribution reads "DEMO DATA – simulated". The synthetic farm has four pivots: healthy, a sector with progressive stress, fallow, and mild stress. The "stress" there is **built into the simulation**, so the demo shows the workflow, not detection skill.

## 13. Suggested 2–3 minute demo

**Part 1: the farmer (≈1 min)**
1. Open RAY in **Farmer mode**. Point out the green "Real Satellite Data" badge, the **Farm Status** card and **Today's Priority** (A4).
2. Tap **العربية** to show the same screen in Arabic, then switch back.
3. **🗺️ View Farm Map**: real Sentinel-2 image, zones in status colours. Tap the red square to open its panel.
4. **View details**: plain-language signals, with the technical values tucked into the expander.
5. **💧 Irrigation**: "Inspect irrigation before applying additional water", the Why?, and the screening-signal note.
6. Show the **B4 note** on Home: the rules say healthy, the anomaly detector says unusual, so the two methods complement each other.

**Part 2: the judge (≈1.5 min)**
7. Switch to **🔬 Technical**. In **Satellite Map**, show True Color → NDVI → NDRE → NDMI → LST → Water Stress.
8. **Water Intelligence**: the rule breakdown shows exactly why A4 is red.
9. **Analytics**: zone comparison, historical trend and decline markers.
10. **AI & Method**: the 8-step live pipeline, Isolation Forest numbers, and Random Forest NOT TRAINED (no fake accuracy).
11. Close with "How RAY supports more efficient irrigation": inspect first, fix faults before adding water, and flag irrigation of non-cropped areas.

## 14. Limitations

The complete, current list is shown in the app (About page and Technical → Limitations; source: `LIMITATIONS` in `src/ui/common.py`). Key points:
- Possible causes are a rule-based fit with the evidence — not probabilities, not a diagnosis.
- The photo check measures colours only; it is not a trained disease classifier and has no measured accuracy.
- No supervised model is trained (not enough labelled field data). Field results are stored for future calibration; RAY does not learn automatically.
- NCM is not connected; no IoT sensors are connected.
- On the hosted demo without Supabase, observations are stored locally and are lost when the app restarts.


- Thresholds are not calibrated for specific crops, growth stages or Hail soils.
- Spectral indicators cannot distinguish water stress from other stressors.
- The rules raise false alarms during early crop growth: young canopies have low NDVI/NDRE and uneven cover. In the demo scene on 2026-04-03, 2 zones are RED and 6 YELLOW purely because of growth stage. Interpret results in the context of the crop calendar.
- Clouds, dust or haze can remove observations. Thermal data is coarse (100 m) and less frequent.
- Zones are a regular grid, not pivot or field boundaries.
- No evapotranspiration or soil-water balance is computed, so **no irrigation volumes** are given.
- No water-saving, early-detection or accuracy figures have been measured.

## 15. What still needs real ground-truth data

- **Threshold calibration:** paired satellite and field observations (soil-moisture probes, leaf water potential or visual stress scoring) per crop in Hail.
- **Supervised model training and validation:** labelled stressed / not-stressed samples collected independently of RAY's rules.
- **Separating causes:** labels distinguishing water stress from nutrient, disease, salinity and pest problems.
- **Irrigation volume advice:** crop type, planting date, soil properties, irrigation-system data and validated ET (for example FAO-56 with local weather).
- **Impact claims:** controlled comparison of water use with and without RAY before stating any saving.

## 16. Future improvements

- Pivot and field boundary detection (circle detection or segmentation) to replace grid zones
- FAO-56 / satellite ET (for example OpenET-style models) for water-requirement estimates
- Sentinel-1 radar for cloud- and dust-independent monitoring and soil moisture
- Crop-type mapping and crop-specific thresholds
- Alerts (SMS/WhatsApp) and a farmer-facing Arabic-first mobile view
- Integration with pivot controllers and flow meters to close the loop

---
*Contains modified Copernicus Sentinel data (when Earth Engine mode is used). Landsat data courtesy of USGS. ERA5-Land: Copernicus Climate Change Service. Basemap © Esri.*
