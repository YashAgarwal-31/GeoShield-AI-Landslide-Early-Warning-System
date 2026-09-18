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
   log for each external dataset.
2. Separate observed records from augmented or generated rows.
3. Use spatially grouped and time-aware validation to reduce location leakage.
4. Report precision, recall, F1, ROC-AUC/PR-AUC, confusion matrix, and class
   balance in addition to accuracy.
5. Calibrate probability outputs before treating them as operational risk.
6. Obtain domain-expert review before using recommendations in the field.
