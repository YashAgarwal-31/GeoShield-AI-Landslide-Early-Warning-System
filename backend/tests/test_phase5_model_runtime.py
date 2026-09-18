"""Phase 5 tests for deterministic ML runtime safety and provenance."""
from __future__ import annotations

import os
import subprocess
import sys


def _run_python(code: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    merged.update(env)
    return subprocess.run(
        [sys.executable, "-c", code],
        env=merged,
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_primary_predictor_fails_closed_without_training_data_in_production(tmp_path):
    result = _run_python(
        "from app.ai_engine.risk_predictor import LandslideRiskPredictor; "
        "LandslideRiskPredictor()",
        {
            "APP_ENV": "production",
            "ALLOW_SYNTHETIC_MODEL_FALLBACK": "false",
            "TRAINING_DATA_PATH": str(tmp_path / "missing.csv"),
            "MODEL_CACHE_DIR": str(tmp_path / "primary-cache"),
        },
    )
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "synthetic fallback is disabled" in combined


def test_enhanced_predictor_fails_closed_without_training_data_in_production(tmp_path):
    result = _run_python(
        "from app.ai_engine.enhanced_predictor import EnhancedLandslidePredictor; "
        "EnhancedLandslidePredictor()",
        {
            "APP_ENV": "production",
            "ALLOW_SYNTHETIC_MODEL_FALLBACK": "false",
            "TRAINING_DATA_PATH": str(tmp_path / "missing.csv"),
            "MODEL_CACHE_DIR": str(tmp_path / "enhanced-cache"),
        },
    )
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "synthetic fallback is disabled" in combined


def test_prediction_api_exposes_training_provenance():
    os.environ.setdefault("RATE_LIMIT_ENABLED", "false")

    from fastapi.testclient import TestClient
    from app.main import app

    response = TestClient(app).post(
        "/api/predict",
        json={"latitude": 25.58, "longitude": 91.89},
    )
    assert response.status_code == 200, response.text
    model_info = response.json()["model_info"]
    assert isinstance(model_info["training_samples"], int)
    assert model_info["training_samples"] > 0
    assert model_info["training_source"] in {
        "mixed_provenance_dataset",
        "controlled_training_file",
        "synthetic_demo_fallback",
    }
