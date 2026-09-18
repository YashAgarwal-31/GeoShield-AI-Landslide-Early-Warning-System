"""Tests for the reproducible, district-grouped ML evaluation pipeline."""

from pathlib import Path
import sys

import pandas as pd
import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from datasets.evaluate_model import evaluate_dataset, validate_dataset  # noqa: E402


DATASET_PATH = REPO_ROOT / "datasets" / "processed" / "real_ner_training_data.csv"


@pytest.fixture(scope="module")
def training_frame() -> pd.DataFrame:
    return pd.read_csv(DATASET_PATH)


def test_dataset_quality_profile_is_explicit(training_frame: pd.DataFrame):
    quality = validate_dataset(training_frame)

    assert quality["rows"] == 12_000
    assert quality["districts"] == 19
    assert quality["target_distribution"] == {"0": 10_800, "1": 1_200}
    assert quality["valid_for_evaluation"] is True
    assert quality["range_issues"]["soil_moisture_outside_0_1"] > 0


def test_missing_required_column_is_rejected(training_frame: pd.DataFrame):
    with pytest.raises(ValueError, match="Missing required columns: district"):
        validate_dataset(training_frame.drop(columns=["district"]))


def test_evaluation_keeps_districts_disjoint(training_frame: pd.DataFrame):
    compact = training_frame.groupby("district", group_keys=False).head(120)
    report = evaluate_dataset(compact, n_estimators=10, cv_splits=3)

    train_districts = set(report["holdout"]["train_districts"])
    test_districts = set(report["holdout"]["test_districts"])
    assert train_districts.isdisjoint(test_districts)
    assert report["cross_validation"]["district_disjoint"] is True
    assert 0 <= report["holdout"]["model"]["balanced_accuracy"] <= 1
    assert "field accuracy" in report["claim_policy"]
