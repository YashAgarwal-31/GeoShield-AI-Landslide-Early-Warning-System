# Reproducible ML evaluation

Run the evaluation from the repository root:

```bash
python datasets/evaluate_model.py
```

The command validates the tracked training table and rewrites
`evaluation_report.json`. The report includes the dataset SHA-256, schema and
range checks, class balance, exact split membership, a majority-class baseline,
district-disjoint holdout results, and five-fold grouped cross-validation.

## Why the split is grouped

A random row split can place samples from the same district in both training and
test sets. The model can then benefit from location-specific patterns that would
not be available at a genuinely unseen district. This evaluation keeps entire
districts on one side of each split.

## Current reproducible result

For dataset SHA-256
`67d618bc1808a8e38bf43af359f5f14240e60bd675c915b9f09cd25b001552a7`:

| Metric | District holdout | 5-fold grouped mean ± std |
|---|---:|---:|
| Balanced accuracy | 0.762 | 0.773 ± 0.013 |
| Positive-class precision | 0.455 | 0.553 ± 0.054 |
| Positive-class recall | 0.592 | 0.601 ± 0.024 |
| Positive-class F1 | 0.515 | 0.574 ± 0.029 |
| ROC-AUC | 0.861 | 0.879 ± 0.024 |
| PR-AUC | 0.564 | 0.646 ± 0.038 |

The holdout confusion matrix is `[[2756, 201], [116, 168]]` in
`[[TN, FP], [FN, TP]]` order. The majority-class baseline has balanced accuracy
0.500 and positive-class F1 0.000.

## Interpretation boundary

These numbers measure how well the evaluation model reproduces generated or
derived prototype labels. They are not field accuracy, warning lead time,
probability calibration, or evidence of operational safety. Evaluation on
independently observed landslide and non-landslide outcomes is still required.
The JSON report records Python, NumPy, pandas, and scikit-learn versions because
model internals can change between dependency releases.
