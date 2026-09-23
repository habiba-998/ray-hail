# data/

This prototype does not ship any satellite files: real imagery is streamed from
Google Earth Engine on demand, and demo data is generated in memory by
`src/demo_data.py`.

## ground_truth/

The supervised Random Forest is **only** trained if you add real field labels:

1. Copy `labels_template.csv` to `labels.csv`.
2. Add one row per field observation: date, location, the satellite features for
   that date/location (e.g. exported from the RAY zone table in Earth Engine mode)
   and a `label` from real observation, e.g. `stressed` / `not_stressed`
   (soil-moisture probe, agronomist visual score, irrigation fault log …).
3. Describe how each label was obtained in `source_notes`.

Training code in `src/ml.py` needs ≥ 30 rows, ≥ 2 classes and ≥ 5 rows per class.
In this prototype the app does **not** train the Random Forest or report any
performance metric. It is reserved for future supervised calibration once real,
independently collected field observations exist.

Do **not** create labels from RAY's own rule output: the model would only learn to
copy the rules and its "accuracy" would be meaningless.
