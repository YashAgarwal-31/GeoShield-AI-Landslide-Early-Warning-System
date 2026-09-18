"""
GeoShield Enhanced AI Risk Prediction Engine
Merges XGBoost from winning reference repo with existing RF+GB ensemble.
Features:
- XGBoost model with feature importance breakdown
- Nearest-neighbor terrain data enrichment
- Risk grid generation across NER
- District-level risk assessment
- Batch prediction for multiple locations
- Multi-level risk classification (low/moderate/high/very_high/critical)
"""
import os
import numpy as np
import json
from datetime import datetime
from typing import Dict, List, Optional

# Try to import ML libraries
import pandas as pd

try:
    import xgboost as xgb
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import accuracy_score, classification_report
    from sklearn.preprocessing import LabelEncoder, StandardScaler
    import joblib
    HAS_ML = True
except ImportError:
    HAS_ML = False
    print("[Enhanced Predictor] scikit-learn/xgboost not installed — using rule-based fallback")

from app.ai_engine.terrain_lookup import terrain_lookup


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _synthetic_fallback_allowed() -> bool:
    app_env = os.getenv("APP_ENV", "demo").strip().lower()
    production = app_env in {"prod", "production"}
    return _env_bool("ALLOW_SYNTHETIC_MODEL_FALLBACK", default=not production)


TRAINING_DATA_PATH = os.getenv(
    "TRAINING_DATA_PATH",
    os.path.join(
        os.path.dirname(__file__), "..", "..", "..",
        "datasets", "processed", "real_ner_training_data.csv"
    ),
)

MODEL_DIR = os.getenv(
    "MODEL_CACHE_DIR",
    os.path.join(os.path.dirname(__file__), "models"),
)
MODEL_PATH = os.path.join(MODEL_DIR, "enhanced_xgb_model.pkl")
ENCODER_PATH = os.path.join(MODEL_DIR, "label_encoder.pkl")
_ENHANCED_MODEL_VERSION = "1.1"


class EnhancedLandslidePredictor:
    """XGBoost-based landslide susceptibility prediction with terrain enrichment."""

    def __init__(self):
        self.model = None
        self.label_encoder = None
        self.scaler = None
        self.model_loaded = False
        self.training_source = "unknown"
        self.feature_names = [
            "latitude", "longitude", "slope", "aspect", "elevation",
            "rainfall_7day", "ndvi", "soil_moisture", "distance_to_road"
        ]
        os.makedirs(MODEL_DIR, exist_ok=True)
        self._try_load_model()
        if not HAS_ML and not _synthetic_fallback_allowed():
            raise RuntimeError(
                "GeoShield enhanced ML dependencies are unavailable and rule-based "
                "fallback is disabled for this operational runtime."
            )
        if not self.model_loaded and HAS_ML:
            print("[Enhanced Predictor] No cached model found, training on startup...")
            self.train()

    def _try_load_model(self):
        """Attempt to load a pre-trained model from disk."""
        if not HAS_ML:
            print("[Enhanced Predictor] ML libs not available — using rule-based fallback")
            return
        if os.path.exists(MODEL_PATH):
            try:
                cached = joblib.load(MODEL_PATH)
                if isinstance(cached, dict):
                    if cached.get("version") != _ENHANCED_MODEL_VERSION:
                        print(
                            "[Enhanced Predictor] Cached model version mismatch; "
                            "retraining with the current contract."
                        )
                        return
                    self.model = cached.get("model")
                    self.scaler = cached.get("scaler")
                    self.label_encoder = cached.get("encoder")
                    self.training_source = cached.get("training_source", "unknown")
                else:
                    print("[Enhanced Predictor] Legacy unversioned cache ignored.")
                    return
                if os.path.exists(ENCODER_PATH):
                    self.label_encoder = joblib.load(ENCODER_PATH)
                self.model_loaded = True
                print("[Enhanced Predictor] ✅ XGBoost model loaded successfully")
            except Exception as e:
                print(f"[Enhanced Predictor] Failed to load model: {e}")

    def train(self, csv_path: str = None) -> Dict:
        """Train XGBoost model on NER data."""
        if not HAS_ML:
            return {"error": "scikit-learn/xgboost not installed"}

        selected_path = csv_path or TRAINING_DATA_PATH
        if selected_path and os.path.exists(selected_path):
            df = pd.read_csv(selected_path)
            self.training_source = (
                "controlled_training_file" if csv_path else "mixed_provenance_dataset"
            )
            print(
                f"[Enhanced Predictor] Loaded {self.training_source}: "
                f"{len(df)} samples"
            )
        else:
            if not _synthetic_fallback_allowed():
                raise RuntimeError(
                    "GeoShield enhanced ML training data is unavailable and "
                    "synthetic fallback is disabled for this runtime. Restore "
                    "datasets/processed/real_ner_training_data.csv or configure "
                    "TRAINING_DATA_PATH explicitly."
                )
            self.training_source = "synthetic_demo_fallback"
            df = self._generate_demo_data(2000)
            print("[Enhanced Predictor] Using explicit synthetic demo training fallback")

        return self._train_on_dataframe(df)

    def _train_on_dataframe(self, df: pd.DataFrame) -> Dict:
        """Train model on a DataFrame."""
        # Map column names
        col_map = {
            "rainfall_daily": "rainfall_24hr",
            "rainfall_7day": "rainfall_7days",
            "rainfall_24hr": "rainfall_24hr",
        }
        df = df.rename(columns=col_map)

        # Ensure all feature columns exist
        for feat in self.feature_names:
            if feat not in df.columns:
                # Try to create from available data
                if feat == "rainfall_7day" and "rainfall_7days" in df.columns:
                    df["rainfall_7day"] = df["rainfall_7days"]
                elif feat == "rainfall_7day" and "rainfall_24hr" in df.columns:
                    df["rainfall_7day"] = df["rainfall_24hr"] * 5
                else:
                    df[feat] = 0

        # Fill NaN
        for feat in self.feature_names:
            if feat in df.columns:
                df[feat] = df[feat].fillna(df[feat].median() if df[feat].notna().any() else 0)

        X = df[self.feature_names].values

        # Determine target column
        if "landslide" in df.columns:
            y = df["landslide"].values.astype(int)
        elif "label" in df.columns:
            y = df["label"].values.astype(int)
        else:
            y = self._create_synthetic_labels(df)

        # Encode labels if needed
        if y.dtype == object or len(np.unique(y)) > 5:
            self.label_encoder = LabelEncoder()
            y = self.label_encoder.fit_transform(y)
            joblib.dump(self.label_encoder, ENCODER_PATH)

        # Split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42,
            stratify=y if len(np.unique(y)) > 1 else None
        )

        # Train XGBoost
        print(f"[Enhanced Predictor] Training XGBoost on {len(X_train)} samples...")
        self.model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            eval_metric="logloss",
            random_state=42,

        )
        self.model.fit(X_train, y_train)

        # Evaluate
        y_pred = self.model.predict(X_test)
        accuracy = float(accuracy_score(y_test, y_pred))

        # Cross-validation
        cv_mean, cv_std = 0.0, 0.0
        if HAS_ML and len(X) > 100:
            try:
                cv_scores = cross_val_score(self.model, X, y, cv=min(5, len(np.unique(y))), scoring="accuracy")
                cv_mean = float(cv_scores.mean())
                cv_std = float(cv_scores.std())
            except Exception:
                pass

        # Save model
        joblib.dump({
            "version": _ENHANCED_MODEL_VERSION,
            "model": self.model,
            "scaler": self.scaler,
            "encoder": self.label_encoder,
            "training_source": self.training_source,
        }, MODEL_PATH)
        self.model_loaded = True

        print(f"[Enhanced Predictor] ✅ Model trained — Accuracy: {accuracy:.3f}, CV: {cv_mean:.3f} (+/- {cv_std:.3f})")

        return {
            "accuracy": accuracy,
            "cv_mean": cv_mean,
            "cv_std": cv_std,
            "training_samples": len(X_train),
            "test_samples": len(X_test),
            "features": self.feature_names,
            "training_source": self.training_source,
        }

    def predict(self, lat: float, lng: float, provided_features: Dict = None) -> Dict:
        """Predict landslide risk with terrain enrichment."""
        # Enrich with real terrain data
        enriched = terrain_lookup.enrich_features(lat, lng, provided_features)

        if self.model_loaded and self.model is not None:
            return self._ml_predict(enriched)
        return self._rule_based_predict(enriched)

    def _ml_predict(self, features: Dict) -> Dict:
        """Use XGBoost model for prediction."""
        feature_vector = np.array([[
            features.get("latitude", 0),
            features.get("longitude", 0),
            features.get("slope", 20),
            features.get("aspect", 180),
            features.get("elevation", 500),
            features.get("rainfall_7days", features.get("rainfall_24hr", 0)),
            features.get("ndvi", 0.5),
            features.get("soil_moisture", 0.3),
            features.get("distance_to_road", 1000),
        ]])

        prediction = self.model.predict(feature_vector)[0]
        probabilities = self.model.predict_proba(feature_vector)[0]

        risk_score = float(probabilities[1] * 100) if len(probabilities) > 1 else float(prediction * 100)
        confidence = float(np.max(probabilities))

        # Feature importance
        feature_importance = {}
        if hasattr(self.model, "feature_importances_"):
            importance_values = self.model.feature_importances_
            for i, name in enumerate(self.feature_names):
                feature_importance[name] = round(float(importance_values[i]) * 100, 1)
            feature_importance = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True))

        return {
            "risk_score": round(min(100, max(0, risk_score)), 1),
            "risk_level": self._score_to_level(risk_score),
            "confidence": round(confidence, 3),
            "source": "xgboost_model",
            "factors": self._explain_factors(features),
            "feature_importance": feature_importance if feature_importance else None,
            "terrain_data": {
                "slope": round(features.get("slope", 0), 1),
                "elevation": round(features.get("elevation", 0), 0),
                "ndvi": round(features.get("ndvi", 0), 3),
                "soil_moisture": round(features.get("soil_moisture", 0), 3),
                "distance_to_road": round(features.get("distance_to_road", 0), 0),
                "source": features.get("_terrain_source", "unknown"),
            },
            "latitude": features.get("latitude", 0),
            "longitude": features.get("longitude", 0),
        }

    def _rule_based_predict(self, features: Dict) -> Dict:
        """Rule-based fallback when ML model is not available."""
        score = 0.0

        # Rainfall (0-35)
        rainfall = features.get("rainfall_24hr", 0) or features.get("rainfall_current", 0) or 0
        if rainfall > 100:
            score += 35
        elif rainfall > 60:
            score += 25
        elif rainfall > 30:
            score += 15
        elif rainfall > 10:
            score += 5

        # Cumulative rainfall (0-10)
        rain_7d = features.get("rainfall_7days", 0) or 0
        if rain_7d > 300:
            score += 10
        elif rain_7d > 150:
            score += 5

        # Slope (0-25)
        slope = features.get("slope", 25) or 25
        if slope > 45:
            score += 25
        elif slope > 30:
            score += 18
        elif slope > 15:
            score += 10
        else:
            score += 3

        # Vegetation — low NDVI = high risk (0-20)
        ndvi = features.get("ndvi", 0.5)
        if ndvi is not None:
            score += max(0, (1 - max(0, ndvi)) * 20)
        else:
            score += 8

        # Soil moisture (0-10)
        moisture = features.get("soil_moisture", 0.3)
        if moisture is not None:
            score += moisture * 10

        # Base terrain risk for NER (0-10)
        score += 8

        score = min(100, max(0, score))
        confidence = 0.55

        return {
            "risk_score": round(score, 1),
            "risk_level": self._score_to_level(score),
            "confidence": confidence,
            "source": "rule_based",
            "factors": self._explain_factors(features),
            "feature_importance": None,
            "terrain_data": {
                "slope": round(features.get("slope", 0), 1),
                "elevation": round(features.get("elevation", 0), 0),
                "ndvi": round(features.get("ndvi", 0), 3),
                "soil_moisture": round(features.get("soil_moisture", 0), 3),
                "distance_to_road": round(features.get("distance_to_road", 0), 0),
                "source": features.get("_terrain_source", "unknown"),
            },
            "latitude": features.get("latitude", 0),
            "longitude": features.get("longitude", 0),
        }

    def _score_to_level(self, score: float) -> str:
        """Map risk score to level (5-level classification from reference repo)."""
        if score >= 80:
            return "critical"
        elif score >= 60:
            return "very_high"
        elif score >= 40:
            return "high"
        elif score >= 20:
            return "moderate"
        return "low"

    def _explain_factors(self, features: Dict) -> Dict:
        """Return human-readable factor contributions."""
        factors = {}
        rainfall = features.get("rainfall_24hr", 0) or features.get("rainfall_current", 0) or 0
        factors["rainfall_risk"] = "high" if rainfall > 60 else "moderate" if rainfall > 30 else "low"
        slope = features.get("slope", 25) or 25
        factors["slope_risk"] = "high" if slope > 35 else "moderate" if slope > 15 else "low"
        ndvi = features.get("ndvi", 0.5)
        factors["vegetation_risk"] = "high" if ndvi is not None and ndvi < 0.3 else "moderate" if ndvi is not None and ndvi < 0.6 else "low"
        return factors

    def _create_synthetic_labels(self, df) -> np.ndarray:
        """Create binary labels from feature thresholds."""
        labels = np.zeros(len(df))
        for i, row in df.iterrows():
            risk = 0
            if row.get("rainfall_24hr", row.get("rainfall_daily", 0)) > 50:
                risk += 1
            if row.get("slope", 0) > 30:
                risk += 1
            if row.get("ndvi", 1) < 0.4:
                risk += 1
            labels[i] = 1 if risk >= 2 else 0
        return labels.astype(int)

    def _generate_demo_data(self, n_samples: int = 1000) -> "pd.DataFrame":
        """Generate synthetic NER demo data for training."""
        np.random.seed(42)
        districts = {
            "Guwahati": (26.14, 91.74),
            "Dibrugarh": (27.47, 94.91),
            "Jorhat": (26.75, 94.22),
            "Tezpur": (26.65, 92.80),
            "Shillong": (25.58, 91.89),
            "Imphal": (24.81, 93.94),
            "Aizawl": (23.73, 92.72),
            "Kohima": (25.66, 94.11),
            "Itanagar": (27.10, 93.62),
            "Agartala": (23.83, 91.28),
        }
        data = []
        for _ in range(n_samples):
            district = np.random.choice(list(districts.keys()))
            base_lat, base_lng = districts[district]
            lat = base_lat + np.random.normal(0, 0.3)
            lng = base_lng + np.random.normal(0, 0.3)
            elevation = np.random.uniform(100, 2500)
            slope = np.clip(np.random.beta(2, 5) * 60, 0, 70)
            aspect = np.random.uniform(0, 360)
            month = np.random.choice(range(6, 10))
            base_rainfall = {6: 200, 7: 350, 8: 300, 9: 200}[month]
            rainfall_24hr = np.random.exponential(base_rainfall / 30)
            rainfall_7days = rainfall_24hr * np.random.uniform(3, 10)
            ndvi = np.clip(np.random.normal(0.55, 0.2), 0.05, 0.95)
            soil_moisture = np.clip(np.random.beta(3, 2), 0, 1)
            distance_to_road = np.random.exponential(2000)
            landslide_prob = (
                0.1 * (rainfall_24hr > 100) +
                0.15 * (slope > 35) +
                0.1 * (ndvi < 0.3) +
                0.1 * (soil_moisture > 0.7) +
                0.05 * (rainfall_7days > 500) +
                0.05 * (distance_to_road < 500)
            )
            is_landslide = int(np.random.random() < min(landslide_prob, 0.8))
            data.append({
                "latitude": round(lat, 4),
                "longitude": round(lng, 4),
                "district": district,
                "state": "NER",
                "elevation": round(elevation, 1),
                "slope": round(slope, 1),
                "aspect": round(aspect, 1),
                "rainfall_24hr": round(rainfall_24hr, 1),
                "rainfall_7days": round(rainfall_7days, 1),
                "ndvi": round(ndvi, 3),
                "soil_moisture": round(soil_moisture, 3),
                "distance_to_road": round(distance_to_road, 1),
                "month": month,
                "landslide": is_landslide,
            })

        df = pd.DataFrame(data)
        return df

    def generate_risk_grid(
        self,
        lat_min: float = 21.0,
        lat_max: float = 30.0,
        lon_min: float = 88.0,
        lon_max: float = 98.0,
        resolution: int = 20,
    ) -> Dict:
        """Generate a risk grid across the NER region using real terrain data."""
        lats = np.linspace(lat_min, lat_max, resolution)
        lons = np.linspace(lon_min, lon_max, resolution)
        grid_points = []
        for lat in lats:
            for lon in lons:
                result = self.predict(float(lat), float(lon))
                grid_points.append({
                    "lat": round(float(lat), 4),
                    "lng": round(float(lon), 4),
                    "risk_score": result["risk_score"],
                    "risk_level": result["risk_level"],
                })
        return {
            "grid": grid_points,
            "bounds": {"lat_min": lat_min, "lat_max": lat_max, "lon_min": lon_min, "lon_max": lon_max},
            "resolution": resolution,
            "count": len(grid_points),
        }

    def get_district_risk(self, district: str) -> Dict:
        """Get aggregated risk assessment for a NER district."""
        district_centers = {
            "guwahati": (26.14, 91.74),
            "dibrugarh": (27.47, 94.91),
            "jorhat": (26.75, 94.22),
            "tezpur": (26.65, 92.80),
            "shillong": (25.58, 91.89),
            "imphal": (24.81, 93.94),
            "aizawl": (23.73, 92.72),
            "kohima": (25.66, 94.11),
            "itanagar": (27.10, 93.62),
            "agartala": (23.83, 91.28),
            "gangtok": (27.34, 88.61),
            "dimapur": (25.91, 93.72),
            "tura": (25.52, 90.22),
            "silchar": (24.83, 92.80),
            "kohima": (25.66, 94.11),
        }
        center = district_centers.get(district.lower())
        if not center:
            return {"error": f"District '{district}' not found", "available": list(district_centers.keys())}

        lat, lng = center
        offsets = [-0.15, -0.075, 0, 0.075, 0.15]
        sample_points = []
        for dlat in offsets:
            for dlng in offsets:
                result = self.predict(lat + dlat, lng + dlng, {"rainfall_24hr": 40})
                sample_points.append(result)

        scores = [p["risk_score"] for p in sample_points]
        avg_score = sum(scores) / len(scores)
        critical_count = sum(1 for p in sample_points if p["risk_level"] == "critical")
        high_count = sum(1 for p in sample_points if p["risk_level"] in ("high", "very_high"))

        return {
            "district": district.title(),
            "risk_level": self._score_to_level(avg_score),
            "risk_score": round(avg_score, 1),
            "zone_count": len(sample_points),
            "critical_count": critical_count,
            "high_count": high_count,
            "predictions": sample_points,
        }


# Singleton
_enhanced_predictor = None


def get_enhanced_predictor() -> EnhancedLandslidePredictor:
    global _enhanced_predictor
    if _enhanced_predictor is None:
        _enhanced_predictor = EnhancedLandslidePredictor()
    return _enhanced_predictor
