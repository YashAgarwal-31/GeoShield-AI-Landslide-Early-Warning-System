"""Reproducible, district-grouped evaluation for the GeoShield prototype data.

This module deliberately evaluates the binary ``landslide`` label. The runtime
demo also derives multi-level risk categories from feature-based severity rules;
those derived categories are not independent ground truth and are therefore not
used as evaluation targets here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import sklearn
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import (
    GroupShuffleSplit,
    StratifiedGroupKFold,
    cross_validate,
)


RANDOM_SEED = 42
FEATURES = [
    "slope",
    "elevation",
    "aspect",
    "rainfall_daily",
    "rainfall_7day",
    "ndvi",
    "soil_moisture",
    "distance_to_road",
    "month",
]
TARGET = "landslide"
GROUP = "district"
REQUIRED_COLUMNS = FEATURES + [TARGET, GROUP]


def file_sha256(path: Path) -> str:
    """Return the SHA-256 digest of a file without loading it all into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _distribution(values: pd.Series) -> dict[str, int]:
    return {
        str(key): int(value)
        for key, value in values.value_counts().sort_index().items()
    }


def validate_dataset(frame: pd.DataFrame) -> dict[str, Any]:
    """Validate schema and record data-quality issues without hiding them."""
    missing_columns = sorted(set(REQUIRED_COLUMNS) - set(frame.columns))
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

    missing_values = {
        column: int(frame[column].isna().sum())
        for column in REQUIRED_COLUMNS
        if frame[column].isna().any()
    }
    invalid_targets = int((~frame[TARGET].isin([0, 1])).sum())
    range_issues = {
        "ndvi_outside_0_1": int((~frame["ndvi"].between(0, 1)).sum()),
        "soil_moisture_outside_0_1": int(
            (~frame["soil_moisture"].between(0, 1)).sum()
        ),
        "slope_outside_0_90": int((~frame["slope"].between(0, 90)).sum()),
        "month_outside_1_12": int((~frame["month"].between(1, 12)).sum()),
    }
    warnings = [
        f"{name}: {count} row(s)"
        for name, count in range_issues.items()
        if count
    ]
    errors = []
    if missing_values:
        errors.append(f"Missing values in required columns: {missing_values}")
    if invalid_targets:
        errors.append(f"Invalid binary target rows: {invalid_targets}")
    if frame[GROUP].nunique() < 2:
        errors.append("At least two districts are required for grouped evaluation")
    if frame[TARGET].nunique() < 2:
        errors.append("Both target classes are required for evaluation")

    return {
        "rows": int(len(frame)),
        "columns": int(len(frame.columns)),
        "districts": int(frame[GROUP].nunique()),
        "target_distribution": _distribution(frame[TARGET]),
        "positive_rate": round(float(frame[TARGET].mean()), 6),
        "exact_duplicate_rows": int(frame.duplicated().sum()),
        "missing_values": missing_values,
        "range_issues": range_issues,
        "warnings": warnings,
        "errors": errors,
        "valid_for_evaluation": not errors,
    }


def prepare_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Apply only fixed, documented physical-range corrections."""
    features = frame[FEATURES].copy()
    features["ndvi"] = features["ndvi"].clip(0, 1)
    features["soil_moisture"] = features["soil_moisture"].clip(0, 1)
    return features


def _metrics(y_true: pd.Series, predictions: np.ndarray, scores: np.ndarray) -> dict[str, Any]:
    return {
        "balanced_accuracy": round(float(balanced_accuracy_score(y_true, predictions)), 6),
        "precision_positive": round(float(precision_score(y_true, predictions, zero_division=0)), 6),
        "recall_positive": round(float(recall_score(y_true, predictions, zero_division=0)), 6),
        "f1_positive": round(float(f1_score(y_true, predictions, zero_division=0)), 6),
        "roc_auc": round(float(roc_auc_score(y_true, scores)), 6),
        "pr_auc": round(float(average_precision_score(y_true, scores)), 6),
        "confusion_matrix": confusion_matrix(y_true, predictions, labels=[0, 1]).astype(int).tolist(),
    }


def _classifier(n_estimators: int) -> RandomForestClassifier:
    return RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=12,
        min_samples_leaf=5,
        class_weight="balanced",
        random_state=RANDOM_SEED,
        n_jobs=-1,
    )


def evaluate_dataset(
    frame: pd.DataFrame,
    *,
    dataset_sha256: str | None = None,
    n_estimators: int = 100,
    cv_splits: int = 5,
) -> dict[str, Any]:
    """Evaluate with district-disjoint holdout and grouped cross-validation."""
    quality = validate_dataset(frame)
    if not quality["valid_for_evaluation"]:
        raise ValueError("; ".join(quality["errors"]))
    if cv_splits > frame[GROUP].nunique():
        raise ValueError("cv_splits cannot exceed the number of districts")

    X = prepare_features(frame)
    y = frame[TARGET].astype(int)
    groups = frame[GROUP].astype(str)

    splitter = GroupShuffleSplit(
        n_splits=1,
        test_size=0.25,
        random_state=RANDOM_SEED,
    )
    train_index, test_index = next(splitter.split(X, y, groups=groups))
    X_train, X_test = X.iloc[train_index], X.iloc[test_index]
    y_train, y_test = y.iloc[train_index], y.iloc[test_index]
    train_groups = sorted(groups.iloc[train_index].unique().tolist())
    test_groups = sorted(groups.iloc[test_index].unique().tolist())

    if set(train_groups) & set(test_groups):
        raise RuntimeError("District leakage detected between train and test sets")
    if y_train.nunique() < 2 or y_test.nunique() < 2:
        raise ValueError("Grouped holdout must contain both target classes")

    baseline = DummyClassifier(strategy="prior", random_state=RANDOM_SEED)
    baseline.fit(X_train, y_train)
    baseline_predictions = baseline.predict(X_test)
    baseline_scores = baseline.predict_proba(X_test)[:, 1]

    model = _classifier(n_estimators)
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    scores = model.predict_proba(X_test)[:, 1]

    cv = StratifiedGroupKFold(
        n_splits=cv_splits,
        shuffle=True,
        random_state=RANDOM_SEED,
    )
    scoring = {
        "balanced_accuracy": "balanced_accuracy",
        "precision_positive": "precision",
        "recall_positive": "recall",
        "f1_positive": "f1",
        "roc_auc": "roc_auc",
        "pr_auc": "average_precision",
    }
    cv_result = cross_validate(
        _classifier(n_estimators),
        X,
        y,
        groups=groups,
        cv=cv,
        scoring=scoring,
        n_jobs=-1,
        error_score="raise",
    )
    cv_metrics = {
        name: {
            "mean": round(float(np.mean(cv_result[f"test_{name}"])), 6),
            "std": round(float(np.std(cv_result[f"test_{name}"])), 6),
        }
        for name in scoring
    }

    return {
        "report_version": 1,
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
        },
        "dataset": {
            "path": "datasets/processed/real_ner_training_data.csv",
            "sha256": dataset_sha256,
            "provenance": "mixed regional, derived, and realistically generated prototype data",
            "label_provenance": "generated binary labels; not independently observed field outcomes",
            "suitability": "software verification and methodology development only",
        },
        "quality": quality,
        "evaluation_design": {
            "target": TARGET,
            "features": FEATURES,
            "group": GROUP,
            "random_seed": RANDOM_SEED,
            "holdout": "25% of districts using GroupShuffleSplit",
            "cross_validation": f"{cv_splits}-fold StratifiedGroupKFold by district",
            "fixed_transformations": [
                "clip ndvi to [0, 1]",
                "clip soil_moisture to [0, 1]",
            ],
            "model": {
                "type": "RandomForestClassifier",
                "n_estimators": n_estimators,
                "max_depth": 12,
                "min_samples_leaf": 5,
                "class_weight": "balanced",
            },
        },
        "holdout": {
            "train_rows": int(len(train_index)),
            "test_rows": int(len(test_index)),
            "train_districts": train_groups,
            "test_districts": test_groups,
            "district_overlap": [],
            "train_target_distribution": _distribution(y_train),
            "test_target_distribution": _distribution(y_test),
            "baseline": _metrics(y_test, baseline_predictions, baseline_scores),
            "model": _metrics(y_test, predictions, scores),
        },
        "cross_validation": {
            "folds": cv_splits,
            "district_disjoint": True,
            "metrics": cv_metrics,
        },
        "claim_policy": (
            "These metrics characterize performance on generated/derived prototype "
            "labels only; they are not field accuracy or operational warning performance. "
            "Exact numeric reproduction requires the recorded dependency versions."
        ),
    }


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=repo_root / "datasets" / "processed" / "real_ner_training_data.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=repo_root / "datasets" / "evaluation" / "evaluation_report.json",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    frame = pd.read_csv(args.input)
    report = evaluate_dataset(frame, dataset_sha256=file_sha256(args.input))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote grouped evaluation report to {args.output}")
    print(json.dumps(report["holdout"]["model"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
