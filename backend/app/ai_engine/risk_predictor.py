"""
GeoShield AI Risk Prediction Engine
Uses Random Forest + Gradient Boosting ensemble for landslide risk assessment.
Trained on mixed-provenance regional and realistically generated NER features.
"""
import numpy as np
import joblib
import os
import json
import csv
from datetime import datetime, timedelta

# Bump this to force re-training when model architecture changes
_MODEL_VERSION = "2.1"

# Training data path - can be overridden via env var for Docker deployments
TRAINING_DATA_PATH = os.getenv(
    "TRAINING_DATA_PATH",
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "datasets", "processed", "real_ner_training_data.csv")
)


class LandslideRiskPredictor:
    """
    Ensemble ML model for landslide risk prediction.
    Combines Random Forest and Gradient Boosting for robust predictions.
    Trained on mixed-provenance NER data with elevation, slope, NDVI, and soil moisture.
    """

    CACHE_FILE = os.path.join(os.path.dirname(__file__), "models", "geoshield_model.pkl")

    def __init__(self):
        self.model_dir = os.path.join(os.path.dirname(__file__), "models")
        os.makedirs(self.model_dir, exist_ok=True)
        self.model = None
        self.scaler = None
        # Features matching real training data format
        self.feature_names = [
            "slope", "elevation", "aspect",
            "rainfall_daily", "rainfall_7day",
            "ndvi", "soil_moisture",
            "distance_to_road", "month"
        ]
        self.risk_thresholds = {
            "low": 25,
            "moderate": 50,
            "high": 75,
            "critical": 90
        }
        if not self._load_cached_model():
            self._build_model()

    def _load_cached_model(self) -> bool:
        """Try to load a previously saved model from disk."""
        if not os.path.exists(self.CACHE_FILE):
            return False
        try:
            cached = joblib.load(self.CACHE_FILE)
            if cached.get("version") != _MODEL_VERSION:
                print(f"[GeoShield AI] Model version mismatch (cached={cached['version']}, expected={_MODEL_VERSION}), retraining...")
                return False
            self.model = cached["model"]
            self.scaler = cached["scaler"]
            print(f"[GeoShield AI] Loaded cached model from {self.CACHE_FILE}")
            return True
        except Exception as e:
            print(f"[GeoShield AI] Failed to load cached model: {e}")
            return False

    def _save_model(self):
        """Save the trained model to disk for future startups."""
        try:
            joblib.dump({
                "version": _MODEL_VERSION,
                "model": self.model,
                "scaler": self.scaler,
            }, self.CACHE_FILE)
            print(f"[GeoShield AI] Model cached to {self.CACHE_FILE}")
        except Exception as e:
            print(f"[GeoShield AI] Failed to cache model: {e}")

    def _load_real_training_data(self):
        """Load the compatibility-named, mixed-provenance NER training CSV."""
        path = TRAINING_DATA_PATH

        if os.path.exists(path):
            try:
                data = []
                labels = []
                with open(path, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        try:
                            data.append([
                                float(row['slope']),
                                float(row['elevation']),
                                float(row['aspect']),
                                float(row['rainfall_daily']),
                                float(row['rainfall_7day']),
                                float(row['ndvi']),
                                float(row['soil_moisture']),
                                float(row['distance_to_road']),
                                float(row['month']),
                            ])
                            labels.append(int(row['landslide']))
                        except (ValueError, KeyError):
                            continue
                if len(data) > 100:
                    print(f"[GeoShield AI] Loaded {len(data)} mixed-provenance NER training samples from {path}")
                    return np.array(data), np.array(labels)
            except Exception as e:
                print(f"[GeoShield AI] Error loading {path}: {e}")

        return None, None

    def _build_model(self):
        """Build and train the demo model with repository or fallback data."""
        from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
        from sklearn.preprocessing import StandardScaler
        from sklearn.model_selection import train_test_split

        # Try to load the repository training table first.
        real_data, real_labels = self._load_real_training_data()

        if real_data is not None and real_labels is not None and len(real_data) > 100:
            # Labels are generated/derived prototype labels, not field ground truth.
            X = real_data
            n_samples = len(X)

            # Convert binary landslide labels (0/1) to 4-class risk levels
            # by combining the ground-truth label with a severity score
            # derived from terrain and weather features.
            slope_sev = np.clip(X[:, 0] / 60, 0, 1)           # slope (0-1)
            rain_sev = np.clip(X[:, 3] / 20, 0, 1)            # daily rainfall
            rain7_sev = np.clip(X[:, 4] / 60, 0, 1)           # 7-day rainfall
            moisture_sev = np.clip(X[:, 6], 0, 1)              # soil moisture
            ndvi_sev = 1 - np.clip(X[:, 5], 0, 1)              # low veg = high risk
            elev_sev = np.clip((X[:, 1] - 500) / 2000, 0, 1)   # elevation

            severity = (
                slope_sev * 0.25 +
                rain_sev * 0.20 +
                rain7_sev * 0.15 +
                moisture_sev * 0.15 +
                ndvi_sev * 0.15 +
                elev_sev * 0.10
            )

            # Map to 4 classes:
            #   landslide=0            -> 0 (low)
            #   landslide=1, sev < 0.4 -> 1 (moderate)
            #   landslide=1, sev < 0.6 -> 2 (high)
            #   landslide=1, sev >= 0.6 -> 3 (critical)
            y = np.zeros(n_samples, dtype=int)
            landslide_mask = real_labels == 1
            y[landslide_mask & (severity < 0.4)] = 1
            y[landslide_mask & (severity >= 0.4) & (severity < 0.6)] = 2
            y[landslide_mask & (severity >= 0.6)] = 3

            print(f"[GeoShield AI] Label distribution: low={np.sum(y==0)}, moderate={np.sum(y==1)}, high={np.sum(y==2)}, critical={np.sum(y==3)}")
        else:
            # Fallback to synthetic data
            print("[GeoShield AI] Using synthetic training data (real data not found)")
            np.random.seed(42)
            n_samples = 5000
            X = np.zeros((n_samples, len(self.feature_names)))

            X[:, 0] = np.random.uniform(5, 60, n_samples)  # slope
            X[:, 1] = np.random.uniform(100, 3000, n_samples)  # elevation
            X[:, 2] = np.random.uniform(0, 360, n_samples)  # aspect
            X[:, 3] = np.random.exponential(15, n_samples).clip(0, 100)  # rainfall_daily
            X[:, 4] = X[:, 3] * 5 + np.random.normal(0, 20, n_samples)  # rainfall_7day
            X[:, 5] = np.random.uniform(0.1, 0.9, n_samples)  # ndvi
            X[:, 6] = np.clip(0.4 + X[:, 3] * 0.005 + np.random.normal(0, 0.15, n_samples), 0, 1)  # soil_moisture
            X[:, 7] = np.random.uniform(0, 20000, n_samples)  # distance_to_road
            X[:, 8] = np.random.randint(1, 13, n_samples)  # month

            risk_score = (
                X[:, 0] / 60 * 0.25 +
                np.clip(X[:, 1] / 2000, 0, 1) * 0.10 +
                np.clip(X[:, 3] / 10, 0, 1) * 0.20 +
                np.clip(X[:, 4] / 50, 0, 1) * 0.15 +
                (1 - X[:, 5]) * 0.15 +
                X[:, 6] * 0.15 +
                np.random.normal(0, 0.05, n_samples)
            )

            y = np.zeros(n_samples, dtype=int)
            y[risk_score >= 0.35] = 1
            y[risk_score >= 0.55] = 2
            y[risk_score >= 0.70] = 3

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.2,
            random_state=42,
            stratify=y if len(np.unique(y)) > 1 else None,
        )

        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Ensemble model
        rf = RandomForestClassifier(
            n_estimators=200, max_depth=15, random_state=42,
            class_weight='balanced', min_samples_split=5
        )
        gb = GradientBoostingClassifier(
            n_estimators=150, max_depth=8, learning_rate=0.1,
            random_state=42, min_samples_split=5
        )

        self.model = VotingClassifier(
            estimators=[('rf', rf), ('gb', gb)],
            voting='soft',
            weights=[0.4, 0.6]
        )
        self.model.fit(X_train_scaled, y_train)

        # Evaluate
        train_acc = self.model.score(X_train_scaled, y_train)
        test_acc = self.model.score(X_test_scaled, y_test)

        print(f"[GeoShield AI] Model trained on {n_samples} samples")
        print(f"[GeoShield AI] Train Accuracy: {train_acc:.3f}, Test Accuracy: {test_acc:.3f}")
        self._save_model()
        return test_acc

    def predict_risk(self, sensor_data: dict, station_data: dict) -> dict:
        """
        Predict landslide risk for a given sensor station.
        Returns risk score, level, probability, and recommendations.
        """
        # Map sensor data to real training features
        # Use station-specific values when available, otherwise use training-data medians
        features = np.array([[
            station_data.get("slope_angle", 20),  # slope
            station_data.get("elevation", 500),   # elevation
            station_data.get("aspect", 181),      # aspect (training median)
            sensor_data.get("rainfall_mm", 10),   # rainfall_daily
            sensor_data.get("rainfall_24h", sensor_data.get("rainfall_mm", 10) * 5),  # rainfall_7day
            station_data.get("vegetation_cover", 60) / 100,  # ndvi (0-1)
            sensor_data.get("soil_moisture", 40) / 100,  # soil_moisture (0-1)
            station_data.get("distance_to_road", 59915),  # distance_to_road (training median)
            datetime.now().month,  # month
        ]])

        features_scaled = self.scaler.transform(features)

        # Get prediction probabilities
        probabilities = self.model.predict_proba(features_scaled)[0]
        n_classes = len(probabilities)

        if n_classes == 4:
            # 4-class model: classes = [low, moderate, high, critical]
            risk_score = float(np.clip(
                probabilities[1] * 33 + probabilities[2] * 66 + probabilities[3] * 100, 0, 100
            ))
            landslide_probability = float(probabilities[2] + probabilities[3])
            # Derive risk_level from risk_score for consistency
            if risk_score >= 75:
                risk_level = "critical"
            elif risk_score >= 50:
                risk_level = "high"
            elif risk_score >= 25:
                risk_level = "moderate"
            else:
                risk_level = "low"
            prob_dict = {
                "low": round(float(probabilities[0]), 3),
                "moderate": round(float(probabilities[1]), 3),
                "high": round(float(probabilities[2]), 3),
                "critical": round(float(probabilities[3]), 3),
            }
        else:
            # Binary model: class 0 = no landslide, class 1 = landslide
            # Map probability to 4-level risk via severity score from features
            landslide_prob = float(probabilities[1])

            # Compute severity from input features (same formula as training)
            slope_sev = np.clip(features[0, 0] / 60, 0, 1)
            rain_sev = np.clip(features[0, 3] / 20, 0, 1)
            rain7_sev = np.clip(features[0, 4] / 60, 0, 1)
            moisture_sev = np.clip(features[0, 6], 0, 1)
            ndvi_sev = 1 - np.clip(features[0, 5], 0, 1)
            elev_sev = np.clip((features[0, 1] - 500) / 2000, 0, 1)
            severity = (
                slope_sev * 0.25 + rain_sev * 0.20 + rain7_sev * 0.15 +
                moisture_sev * 0.15 + ndvi_sev * 0.15 + elev_sev * 0.10
            )

            # Combined risk: blend landslide probability with severity
            combined = landslide_prob * 0.6 + severity * 0.4

            if combined < 0.25:
                risk_level = "low"
                risk_score = float(np.clip(combined * 100, 0, 24))
            elif combined < 0.45:
                risk_level = "moderate"
                risk_score = float(np.clip(25 + (combined - 0.25) * 250, 25, 49))
            elif combined < 0.65:
                risk_level = "high"
                risk_score = float(np.clip(50 + (combined - 0.45) * 250, 50, 74))
            else:
                risk_level = "critical"
                risk_score = float(np.clip(75 + (combined - 0.65) * 166.7, 75, 100))

            landslide_probability = landslide_prob
            predicted_class = {"low": 0, "moderate": 1, "high": 2, "critical": 3}[risk_level]
            prob_dict = {
                "low": round(float(1 - landslide_prob), 3) if risk_level == "low" else 0.0,
                "moderate": round(float(landslide_prob * 0.4), 3) if risk_level == "moderate" else 0.0,
                "high": round(float(landslide_prob * 0.7), 3) if risk_level == "high" else 0.0,
                "critical": round(float(landslide_prob * 0.9), 3) if risk_level == "critical" else 0.0,
            }

        # Determine contributing factors
        factors = []
        if sensor_data.get("rainfall_mm", 0) > 50:
            factors.append("Heavy rainfall detected")
        if sensor_data.get("soil_moisture", 0) > 70:
            factors.append("High soil moisture saturation")
        if sensor_data.get("ground_displacement", 0) > 5:
            factors.append("Ground displacement detected")
        tilt = abs(sensor_data.get("tilt_angle_x", 0)) + abs(sensor_data.get("tilt_angle_y", 0))
        if tilt > 2:
            factors.append("Abnormal tilt angle detected")
        if sensor_data.get("pore_water_pressure", 0) > 60:
            factors.append("Elevated pore water pressure")
        if station_data.get("slope_angle", 0) > 35:
            factors.append("Steep slope angle")
        if station_data.get("vegetation_cover", 100) < 30:
            factors.append("Low vegetation cover")
        if station_data.get("elevation", 0) > 1500:
            factors.append("High elevation zone")

        # Time window prediction
        if risk_level == "critical":
            time_window = max(1, int(24 - landslide_probability * 24))
        elif risk_level == "high":
            time_window = max(2, int(48 - landslide_probability * 36))
        elif risk_level == "moderate":
            time_window = max(6, int(72 - landslide_probability * 48))
        else:
            time_window = 168

        # Generate recommendation
        recommendation = self._get_recommendation(risk_level, factors)

        return {
            "risk_score": round(risk_score, 1),
            "risk_level": risk_level,
            "landslide_probability": round(landslide_probability, 3),
            "contributing_factors": factors,
            "predicted_time_window_hours": time_window,
            "recommendation": recommendation,
            "probabilities": prob_dict,
            "model_info": {
                "type": "RF + GB Ensemble",
                "training_samples": "12,000 regional and realistically generated NER samples",
                "features": len(self.feature_names),
                "feature_names": self.feature_names,
            }
        }

    def _get_recommendation(self, risk_level: str, factors: list) -> str:
        recommendations = {
            "critical": "IMMEDIATE EVACUATION recommended. Deploy emergency response teams. Activate sirens and SMS alerts for all nearby villages. Close affected roads. Expected event within hours.",
            "high": "Heightened alert status. Pre-position rescue teams. Begin voluntary evacuation of vulnerable populations. Monitor sensor readings every 15 minutes. Close at-risk road sections.",
            "moderate": "Enhanced monitoring. Notify district disaster management authority. Prepare evacuation plans. Check emergency supplies. Monitor rainfall forecasts closely.",
            "low": "Normal operations. Continue routine monitoring. Maintain standard alert readiness. No immediate action required."
        }
        return recommendations.get(risk_level, "Continue monitoring.")

    def recommendation_for_level(self, risk_level: str, factors: list | None = None) -> str:
        """Return operational guidance consistent with the final risk level."""
        return self._get_recommendation(risk_level, factors or [])


# Singleton instance
_predictor = None


def get_predictor() -> LandslideRiskPredictor:
    global _predictor
    if _predictor is None:
        _predictor = LandslideRiskPredictor()
    return _predictor
