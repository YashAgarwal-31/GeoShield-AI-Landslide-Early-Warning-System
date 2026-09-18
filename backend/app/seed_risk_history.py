"""Generate historical risk assessments to populate trend charts."""
import json
import random
import math
from datetime import datetime, timedelta, timezone
from app.database import SessionLocal, engine, Base
from app.models import RiskAssessment, SensorStation


def seed_risk_history():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        existing = db.query(RiskAssessment).count()
        if existing > 30:
            print("[Seed] Risk history already populated, skipping.")
            return

        stations = db.query(SensorStation).all()
        print(f"[Seed] Generating 48h risk history for {len(stations)} stations...")

        for station in stations:
            for hours_ago in range(48, 0, -1):
                ts = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=hours_ago)

                # Simulate varying risk over time
                hour_factor = math.sin((ts.hour / 24) * math.pi) * 10
                random_noise = random.gauss(0, 5)
                base_risk = random.uniform(15, 60)
                risk_score = max(0, min(100, base_risk + hour_factor + random_noise))

                if risk_score >= 75:
                    level = "critical"
                elif risk_score >= 50:
                    level = "high"
                elif risk_score >= 25:
                    level = "moderate"
                else:
                    level = "low"

                prob = min(1.0, risk_score / 120)
                factors = []
                if risk_score > 40:
                    factors.append("Elevated rainfall detected")
                if risk_score > 55:
                    factors.append("High soil moisture")
                if risk_score > 65:
                    factors.append("Ground displacement trending upward")

                recs = {
                    "critical": "IMMEDIATE EVACUATION recommended.",
                    "high": "Heightened alert. Pre-position rescue teams.",
                    "moderate": "Enhanced monitoring. Prepare evacuation plans.",
                    "low": "Normal operations. Continue routine monitoring.",
                }

                assessment = RiskAssessment(
                    station_id=station.station_id,
                    risk_level=level,
                    risk_score=round(risk_score, 1),
                    landslide_probability=round(prob, 3),
                    contributing_factors=json.dumps(factors),
                    predicted_time_window=max(1, int((100 - risk_score) / 4)),
                    recommendation=recs.get(level, "Continue monitoring."),
                    model_version="v1.0",
                    timestamp=ts,
                )
                db.add(assessment)

        db.commit()
        print(f"[Seed] Generated {len(stations) * 48} historical risk assessments")

    except Exception as e:
        db.rollback()
        print(f"[Seed] Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_risk_history()
