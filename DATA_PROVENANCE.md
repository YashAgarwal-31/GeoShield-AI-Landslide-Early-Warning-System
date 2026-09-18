# Data provenance and model-claim policy

GeoShield is currently a demonstration and research prototype. Its datasets do
not all have the same evidentiary status.

## Current data categories

| Category | Current status | Permitted presentation claim |
|---|---|---|
| Historical landslide records | Small regional catalog files are included | Historical/reference records |
| Terrain and station features | Regional values plus generated/interpolated samples | Regional and realistically generated features |
| Sensor readings | Seeded and simulated in the default build | Simulated sensor stream |
| NDVI/vegetation | Cached values with simulated fallback | Satellite-derived/cached prototype inputs |
| Weather | Demo data with optional external integration | Weather-integration-ready prototype |
| Model labels | Binary labels and severity-derived multiclass labels | Experimental labels, not field-certified ground truth |

## Claims that must not be made

- The application is not a government-certified warning system.
- The default installation is not connected to live physical IoT sensors.
- The 12,000-row training table must not be described as 12,000 independently
  verified historical landslide events.
- A model accuracy value must not be quoted without the dataset version,
  train/test split, class distribution, metrics, and reproducible evaluation.

## Validation roadmap

1. Record a source URL, retrieval date, license, checksum, and transformation
   log for each new external dataset. **In progress.**
2. Separate observed records from augmented or generated rows. **The current
   manifest now labels mixed provenance; row-level separation remains pending.**
3. Use spatially grouped and time-aware validation to reduce location leakage.
   **District-grouped validation is implemented; time-aware validation requires
   independently time-indexed outcomes.**
4. Report precision, recall, F1, ROC-AUC/PR-AUC, confusion matrix, and class
   balance in addition to accuracy. **Implemented for the prototype binary
   label in `datasets/evaluation/evaluation_report.json`.**
5. Calibrate probability outputs before treating them as operational risk.
6. Obtain domain-expert review before using recommendations in the field.

## Current training-table audit

- Dataset SHA-256: `67d618bc1808a8e38bf43af359f5f14240e60bd675c915b9f09cd25b001552a7`
- Rows: 12,000 across 19 district groups
- Binary class balance: 10,800 negative and 1,200 positive rows
- Exact duplicates: 0
- Required-field missing values: 0
- Range warnings: 1 NDVI and 28 soil-moisture values exceed 1; the evaluation
  pipeline reports and clips these values using a fixed rule.

The grouped metrics describe generated/derived prototype labels only. They are
not field accuracy and must always be presented with this limitation.
