# GeoShield data workspace

GeoShield currently uses a mixture of historical extracts, cached API-derived
values, seeded runtime records, and realistically generated training rows. The
default repository is suitable for software demonstrations and evaluation-method
development, not for claims of live field monitoring.

## Start here

- [`DATASETS.md`](DATASETS.md) — current file-level manifest and provenance
- [`../DATA_PROVENANCE.md`](../DATA_PROVENANCE.md) — allowed claims and validation policy
- [`evaluation/README.md`](evaluation/README.md) — grouped ML methodology and current results
- [`evaluation/evaluation_report.json`](evaluation/evaluation_report.json) — machine-readable report tied to the dataset checksum

## Reproduce the data audit and ML evaluation

From the repository root, with backend dependencies installed:

```bash
python datasets/evaluate_model.py
```

The evaluator checks schema, class balance, duplicates, missing values, and
physical ranges. It then compares a class-prior baseline with a balanced random
forest using a district-disjoint holdout and five-fold grouped cross-validation.

## Integration scripts

The downloader and preparation scripts are research utilities. Network access,
source availability, licenses, and credentials vary by provider. Running a
script does not automatically convert generated features into observed ground
truth. Preserve raw checksums and transformation logs whenever data are updated.

Planned higher-quality inputs include independently sourced event/non-event
records, time-indexed rainfall, calibrated soil-moisture measurements, SRTM/DEM
terrain features, and Sentinel-derived vegetation indices.
