# GeoShield dataset manifest

This manifest describes the files currently present in the repository. It does
not treat generated rows as observed events or cached values as live feeds.

## Tracked datasets

| File | Rows/items | Provenance category | Current use |
|---|---:|---|---|
| `processed/real_ner_training_data.csv` | 12,000 rows | Regional features mixed with realistically generated rows and generated binary labels | Prototype training and reproducible methodology evaluation |
| `raw/ner_historical_landslides.csv` | Small regional catalog | Historical/reference records | Demonstration context |
| `raw/nasa_landslide_catalog.csv` | Repository extract | External historical catalog extract | Reference and preprocessing experiments |
| `raw/india_district_rainfall.csv` | Repository extract | Historical rainfall table | Reference and preprocessing experiments |
| `processed/real_satellite_data.json` | 20 station profiles | Cached API-derived and estimated values | Satellite demonstration page |
| `processed/ner_roads.json` | Road features | OpenStreetMap-derived snapshot | GIS demonstration |
| Seeded database records | Runtime-generated | Simulated station, sensor, alert, report, and infrastructure state | Default local demo |

Some processed files retain their upstream filenames for compatibility. A name
containing `real` does not mean that every value or label in the file is an
independently observed measurement.

## Training-table audit

The reproducible validator currently records:

| Check | Result |
|---|---:|
| Rows | 12,000 |
| District groups | 19 |
| Negative labels | 10,800 |
| Positive labels | 1,200 |
| Exact duplicate rows | 0 |
| Missing required values | 0 |
| NDVI values above 1 | 1 |
| Soil-moisture values above 1 | 28 |

The evaluation pipeline reports the out-of-range values and applies a fixed
`[0, 1]` clip to NDVI and soil moisture. It does not silently describe the table
as clean field data.

## Reproducible evaluation

```bash
python datasets/evaluate_model.py
```

The generated report is stored at
[`evaluation/evaluation_report.json`](evaluation/evaluation_report.json), with
methodology and interpretation guidance in [`evaluation/README.md`](evaluation/README.md).

## External sources and planned integrations

The scripts in this directory contain adapters or preparation code for sources
such as Open-Meteo, OpenStreetMap, NASA GLC, SRTM, Sentinel-2, and IMD. Their
presence does not mean that every source is live or fully integrated in the
default build. Before adding an external dataset, record:

1. canonical source URL and publisher;
2. retrieval date and license/terms;
3. raw-file checksum;
4. transformation script and parameters;
5. observed, derived, interpolated, or generated status for every field;
6. geographic and temporal coverage;
7. known missingness, imbalance, and measurement limitations.

See [`../DATA_PROVENANCE.md`](../DATA_PROVENANCE.md) for the project-wide claim
policy.
