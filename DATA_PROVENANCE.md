# Data provenance and model-claim policy

GeoShield is currently a demonstration and research prototype. Its datasets do
not all have the same evidentiary status.

## Current data categories

| Category | Current status | Permitted presentation claim |
|---|---|---|
| Historical landslide records | Small regional catalog files are included | Historical/reference records |
| Terrain and station features | Regional values plus generated/interpolated samples | Regional and realistically generated features |
| Sensor readings | Seeded by default; authenticated HTTP gateway accepts real device observations when enabled | Seeded/simulated by default; gateway-ingested rows are source-labelled |
| NDVI/vegetation | Live Sentinel-2 L2A point sampling with cached/estimated fallback | Live or explicitly fallback-labelled remote-sensing input |
| Elevation/slope | Live SRTM point sampling with station fallback | Live or explicitly fallback-labelled terrain input |
| Weather | IMD preferred current observation, Open-Meteo fallback, seeded database final fallback | Provider-labelled live/cached/fallback weather |
| Flood discharge | Live GloFAS/Open-Meteo guidance plus historical district baseline | Live river-discharge guidance + historical baseline |
| Model labels | Binary labels and severity-derived multiclass labels | Experimental labels, not field-certified ground truth |

## Claims that must not be made

- The application is not a government-certified warning system.
- The default installation does not include physical IoT hardware. The authenticated sensor-gateway API is implemented, but a real field device must still be configured with the deployment URL and sensor key.
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

## Runtime source status

Weather, flood, terrain, and satellite APIs expose provider/freshness metadata.
Current weather prefers IMD and falls back to Open-Meteo, then to the seeded
database. On-demand terrain enrichment uses SRTM; NDVI uses recent Sentinel-2
L2A scenes discovered via Earth Search. Flood guidance uses GloFAS through
Open-Meteo. All external adapters use bounded timeouts and fall back without
making the operational API unavailable. The repository satellite file remains
available as a deterministic cached fallback and is never presented as a live
satellite stream.
