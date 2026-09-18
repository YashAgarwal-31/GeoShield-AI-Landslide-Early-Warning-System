"""
Enhanced Prediction API — Risk Grid, Batch Predict, District Risk, Model Training.

Model retraining is an administrative maintenance operation and is disabled by
default. Enable it explicitly with MODEL_TRAINING_ENABLED=true.
"""
import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional

from app.ai_engine.enhanced_predictor import get_enhanced_predictor
from app.auth import require_role

router = APIRouter(prefix="/api/ml", tags=["ML Enhanced"])


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _resolve_training_path(csv_path: Optional[str]) -> Optional[str]:
    if not csv_path:
        return None

    datasets_root = Path(
        os.getenv(
            "MODEL_TRAINING_DATA_DIR",
            str(Path(__file__).resolve().parents[3] / "datasets"),
        )
    ).expanduser().resolve()

    requested = Path(csv_path).expanduser()
    if not requested.is_absolute():
        requested = datasets_root / requested
    requested = requested.resolve()

    try:
        requested.relative_to(datasets_root)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="Training data path must stay inside MODEL_TRAINING_DATA_DIR.",
        ) from exc

    if not requested.is_file() or requested.suffix.lower() != ".csv":
        raise HTTPException(status_code=400, detail="Training CSV not found.")

    return str(requested)


class MLBatchRequest(BaseModel):
    """Batch prediction for multiple locations."""

    locations: List[dict]


@router.get("/health")
async def ml_health():
    """ML service health check."""
    predictor = get_enhanced_predictor()
    return {
        "status": "ok",
        "model_loaded": predictor.model_loaded,
        "model_type": "xgboost" if predictor.model_loaded else "rule_based",
        "terrain_lookup": True,
        "version": "2.1-operational",
        "training_source": predictor.training_source,
        "training_samples": predictor.training_samples,
        "training_enabled": _env_bool("MODEL_TRAINING_ENABLED", False),
    }


@router.get("/risk/grid")
async def get_risk_grid(
    lat_min: float = Query(21.0, ge=-90, le=90),
    lat_max: float = Query(30.0, ge=-90, le=90),
    lon_min: float = Query(88.0, ge=-180, le=180),
    lon_max: float = Query(98.0, ge=-180, le=180),
    resolution: int = Query(10, ge=5, le=30),
):
    """Generate a risk grid across the NER region."""
    if lat_min >= lat_max or lon_min >= lon_max:
        raise HTTPException(status_code=422, detail="Minimum bounds must be lower than maximum bounds.")

    predictor = get_enhanced_predictor()
    return predictor.generate_risk_grid(lat_min, lat_max, lon_min, lon_max, resolution)


@router.get("/risk/district/{district}")
async def get_district_risk(district: str):
    """Get aggregated risk assessment for a NER district."""
    predictor = get_enhanced_predictor()
    result = predictor.get_district_risk(district)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/predict")
async def ml_predict(request: dict):
    """Predict landslide risk for a single location with terrain enrichment."""
    lat = request.get("latitude", request.get("lat"))
    lng = request.get("longitude", request.get("lng"))

    if lat is None or lng is None:
        raise HTTPException(status_code=422, detail="latitude and longitude are required")
    if not (-90 <= float(lat) <= 90 and -180 <= float(lng) <= 180):
        raise HTTPException(status_code=422, detail="Invalid latitude or longitude")

    features = {
        key: value
        for key, value in request.items()
        if key not in ("latitude", "longitude", "lat", "lng")
    }
    predictor = get_enhanced_predictor()
    return predictor.predict(float(lat), float(lng), features)


@router.post("/predict/batch")
async def ml_predict_batch(request: MLBatchRequest):
    """Predict risk for multiple locations."""
    if not request.locations:
        raise HTTPException(status_code=422, detail="At least one location is required")
    if len(request.locations) > 100:
        raise HTTPException(status_code=422, detail="Batch size cannot exceed 100 locations")

    predictor = get_enhanced_predictor()
    predictions = []

    for loc in request.locations:
        lat = loc.get("latitude", loc.get("lat"))
        lng = loc.get("longitude", loc.get("lng"))
        if lat is None or lng is None:
            raise HTTPException(status_code=422, detail="Each location needs latitude and longitude")
        if not (-90 <= float(lat) <= 90 and -180 <= float(lng) <= 180):
            raise HTTPException(status_code=422, detail="Invalid latitude or longitude in batch")

        features = {
            key: value
            for key, value in loc.items()
            if key not in ("latitude", "longitude", "lat", "lng")
        }
        predictions.append(predictor.predict(float(lat), float(lng), features))

    return {"predictions": predictions, "count": len(predictions)}


@router.post("/train")
async def train_model(
    csv_path: Optional[str] = None,
    user: dict = Depends(require_role("admin")),
):
    """
    Train/retrain the enhanced model.

    Security controls:
    - admin role required
    - MODEL_TRAINING_ENABLED must be explicitly true
    - a caller-supplied CSV must remain inside MODEL_TRAINING_DATA_DIR
    """
    if not _env_bool("MODEL_TRAINING_ENABLED", False):
        raise HTTPException(
            status_code=403,
            detail="Model retraining is disabled. Set MODEL_TRAINING_ENABLED=true for a controlled maintenance session.",
        )

    predictor = get_enhanced_predictor()
    safe_csv_path = _resolve_training_path(csv_path)
    result = predictor.train(safe_csv_path)

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return {"message": "Model trained successfully", "details": result}
