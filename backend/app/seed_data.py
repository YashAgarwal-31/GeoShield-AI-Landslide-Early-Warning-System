"""
Seed realistic demo data for North Eastern Region landslide monitoring.
Uses actual NER locations: Sikkim, Assam, Manipur, Mizoram, Meghalaya, Nagaland, Tripura, Arunachal Pradesh.
"""
import json
import random
import math
import numpy as np
from datetime import datetime, timedelta, timezone
from app.database import SessionLocal, engine, Base
from app.models import (
    SensorStation, SensorReading, RiskAssessment, Alert,
    CitizenReport, WeatherData, RoadStatus, Village
)

# Real NER locations for sensor stations
NER_STATIONS = [
    {"station_id": "NER-001", "name": "Gangtok North Slope", "lat": 27.3389, "lng": 88.6065, "state": "Sikkim", "district": "Gangtok", "village": "Tadong", "elevation": 1650, "slope_angle": 38, "soil_type": "silty_clay", "veg": 45},
    {"station_id": "NER-002", "name": "Mangan Hill Monitor", "lat": 27.5124, "lng": 88.5281, "state": "Sikkim", "district": "Mangan", "village": "Mangan", "elevation": 950, "slope_angle": 42, "soil_type": "weathered_rock", "veg": 35},
    {"station_id": "NER-003", "name": "Namchi Valley Watch", "lat": 27.1684, "lng": 88.5510, "state": "Sikkim", "district": "Namchi", "village": "Namchi", "elevation": 1315, "slope_angle": 35, "soil_type": "residual_soil", "veg": 55},
    {"station_id": "NER-004", "name": "Guwahati Foothills", "lat": 26.1445, "lng": 91.7362, "state": "Assam", "district": "Kamrup", "village": "Chandrapur", "elevation": 550, "slope_angle": 28, "soil_type": "alluvial", "veg": 40},
    {"station_id": "NER-005", "name": "Karbi Anglong Slope", "lat": 26.1000, "lng": 93.2000, "state": "Assam", "district": "Karbi Anglong", "village": "Diphu", "elevation": 680, "slope_angle": 32, "soil_type": "sandy_clay", "veg": 50},
    {"station_id": "NER-006", "name": "Imphal Valley Edge", "lat": 24.8170, "lng": 93.9368, "state": "Manipur", "district": "Imphal East", "village": "Porompat", "elevation": 786, "slope_angle": 36, "soil_type": "loam", "veg": 42},
    {"station_id": "NER-007", "name": "Churachandpur Hills", "lat": 24.3322, "lng": 93.6825, "state": "Manipur", "district": "Churachandpur", "village": "Lamka", "elevation": 915, "slope_angle": 40, "soil_type": "shale_residue", "veg": 30},
    {"station_id": "NER-008", "name": "Aizawl Ridge Monitor", "lat": 23.7271, "lng": 92.7176, "state": "Mizoram", "district": "Aizawl", "village": "Aizawl", "elevation": 1080, "slope_angle": 44, "soil_type": "sandstone_weathered", "veg": 38},
    {"station_id": "NER-009", "name": "Lunglei Slope Watch", "lat": 22.9000, "lng": 92.7500, "state": "Mizoram", "district": "Lunglei", "village": "Lunglei", "elevation": 720, "slope_angle": 38, "soil_type": "laterite", "veg": 48},
    {"station_id": "NER-010", "name": "Shillong Plateau Edge", "lat": 25.5788, "lng": 91.8933, "state": "Meghalaya", "district": "East Khasi Hills", "village": "Mawlynnong", "elevation": 1490, "slope_angle": 30, "soil_type": "limestone_residue", "veg": 65},
    {"station_id": "NER-011", "name": "Cherrapunji Monitor", "lat": 25.2838, "lng": 91.7344, "state": "Meghalaya", "district": "East Khasi Hills", "village": "Cherrapunji", "elevation": 1430, "slope_angle": 33, "soil_type": "sandstone", "veg": 52},
    {"station_id": "NER-012", "name": "Tura Hills Watch", "lat": 25.5140, "lng": 90.2200, "state": "Meghalaya", "district": "West Garo Hills", "village": "Tura", "elevation": 650, "slope_angle": 29, "soil_type": "alluvial_clay", "veg": 58},
    {"station_id": "NER-013", "name": "Kohima Ridge", "lat": 25.6586, "lng": 94.1086, "state": "Nagaland", "district": "Kohima", "village": "Kohima", "elevation": 1444, "slope_angle": 37, "soil_type": "weathered_gneiss", "veg": 44},
    {"station_id": "NER-014", "name": "Dimapur Lowlands", "lat": 25.9000, "lng": 93.7266, "state": "Nagaland", "district": "Dimapur", "village": "Dimapur", "elevation": 196, "slope_angle": 12, "soil_type": "alluvial", "veg": 35},
    {"station_id": "NER-015", "name": "Agartala Slope Monitor", "lat": 23.8315, "lng": 91.2868, "state": "Tripura", "district": "West Tripura", "village": "Agartala", "elevation": 120, "slope_angle": 15, "soil_type": "tertiary_sediment", "veg": 55},
    {"station_id": "NER-016", "name": "Itanagar Foothills", "lat": 27.0844, "lng": 93.6920, "state": "Arunachal Pradesh", "district": "Papum Pare", "village": "Itanagar", "elevation": 320, "slope_angle": 25, "soil_type": "silty_loam", "veg": 62},
    {"station_id": "NER-017", "name": "Ziro Valley Watch", "lat": 27.5887, "lng": 93.8492, "state": "Arunachal Pradesh", "district": "Lower Subansiri", "village": "Ziro", "elevation": 1688, "slope_angle": 30, "soil_type": "forest_loam", "veg": 78},
    {"station_id": "NER-018", "name": "Pasighat Monitor", "lat": 28.0700, "lng": 95.3300, "state": "Arunachal Pradesh", "district": "East Siang", "village": "Pasighat", "elevation": 155, "slope_angle": 18, "soil_type": "alluvial", "veg": 70},
    {"station_id": "NER-019", "name": "Tawang Ridge", "lat": 27.5860, "lng": 91.8800, "state": "Arunachal Pradesh", "district": "Tawang", "village": "Tawang", "elevation": 3048, "slope_angle": 48, "soil_type": "glacial_till", "veg": 25},
    {"station_id": "NER-020", "name": "Dima Hasao Watch", "lat": 25.4500, "lng": 93.1800, "state": "Assam", "district": "Dima Hasao", "village": "Haflong", "elevation": 680, "slope_angle": 41, "soil_type": "sandstone_residue", "veg": 42},
]

NER_VILLAGES = [
    {"name": "Mawlynnong", "state": "Meghalaya", "district": "East Khasi Hills", "lat": 25.2592, "lng": 91.7276, "pop": 800, "risk": "high_risk", "hosp_km": 12, "police_km": 8},
    {"name": "Gangtok", "state": "Sikkim", "district": "Gangtok", "lat": 27.3389, "lng": 88.6065, "pop": 100000, "risk": "medium_risk", "hosp_km": 2, "police_km": 1},
    {"name": "Tawang", "state": "Arunachal Pradesh", "district": "Tawang", "lat": 27.5860, "lng": 91.8800, "pop": 12000, "risk": "high_risk", "hosp_km": 15, "police_km": 5},
    {"name": "Lamka", "state": "Manipur", "district": "Churachandpur", "lat": 24.3322, "lng": 93.6825, "pop": 35000, "risk": "high_risk", "hosp_km": 8, "police_km": 3},
    {"name": "Haflong", "state": "Assam", "district": "Dima Hasao", "lat": 25.4500, "lng": 93.1800, "pop": 15000, "risk": "high_risk", "hosp_km": 10, "police_km": 5},
    {"name": "Aizawl", "state": "Mizoram", "district": "Aizawl", "lat": 23.7271, "lng": 92.7176, "pop": 300000, "risk": "medium_risk", "hosp_km": 1, "police_km": 1},
    {"name": "Kohima", "state": "Nagaland", "district": "Kohima", "lat": 25.6586, "lng": 94.1086, "pop": 100000, "risk": "medium_risk", "hosp_km": 2, "police_km": 1},
    {"name": "Ziro", "state": "Arunachal Pradesh", "district": "Lower Subansiri", "lat": 27.5887, "lng": 93.8492, "pop": 8000, "risk": "medium_risk", "hosp_km": 18, "police_km": 10},
    {"name": "Mangan", "state": "Sikkim", "district": "Mangan", "lat": 27.5124, "lng": 88.5281, "pop": 5000, "risk": "high_risk", "hosp_km": 12, "police_km": 8},
    {"name": "Tura", "state": "Meghalaya", "district": "West Garo Hills", "lat": 25.5140, "lng": 90.2200, "pop": 30000, "risk": "low_risk", "hosp_km": 5, "police_km": 3},
    {"name": "Lunglei", "state": "Mizoram", "district": "Lunglei", "lat": 22.9000, "lng": 92.7500, "pop": 25000, "risk": "medium_risk", "hosp_km": 6, "police_km": 4},
    {"name": "Dimapur", "state": "Nagaland", "district": "Dimapur", "lat": 25.9000, "lng": 93.7266, "pop": 120000, "risk": "low_risk", "hosp_km": 2, "police_km": 1},
    {"name": "Cherrapunji", "state": "Meghalaya", "district": "East Khasi Hills", "lat": 25.2838, "lng": 91.7344, "pop": 14000, "risk": "high_risk", "hosp_km": 10, "police_km": 6},
    {"name": "Pasighat", "state": "Arunachal Pradesh", "district": "East Siang", "lat": 28.0700, "lng": 95.3300, "pop": 25000, "risk": "low_risk", "hosp_km": 4, "police_km": 2},
    {"name": "Agartala", "state": "Tripura", "district": "West Tripura", "lat": 23.8315, "lng": 91.2868, "pop": 400000, "risk": "low_risk", "hosp_km": 1, "police_km": 1},
    {"name": "Diphu", "state": "Assam", "district": "Karbi Anglong", "lat": 25.8440, "lng": 93.4300, "pop": 60000, "risk": "medium_risk", "hosp_km": 3, "police_km": 2},
    {"name": "Namchi", "state": "Sikkim", "district": "Namchi", "lat": 27.1684, "lng": 88.5510, "pop": 10000, "risk": "medium_risk", "hosp_km": 8, "police_km": 5},
    {"name": "Itanagar", "state": "Arunachal Pradesh", "district": "Papum Pare", "lat": 27.0844, "lng": 93.6920, "pop": 65000, "risk": "low_risk", "hosp_km": 3, "police_km": 2},
]

NER_ROADS = [
    # ═══ SIKKIM ═══
    {"name": "NH-10 (Siliguri-Gangtok)", "type": "national_highway", "slat": 26.72, "slng": 88.39, "elat": 27.34, "elng": 88.61, "status": "open"},
    {"name": "NH-10 (Rangpo-Gangtok)", "type": "national_highway", "slat": 27.12, "slng": 88.54, "elat": 27.34, "elng": 88.61, "status": "open"},
    {"name": "NH-510 (Singtam-Mangan)", "type": "national_highway", "slat": 27.22, "slng": 88.51, "elat": 27.51, "elng": 88.53, "status": "partially_blocked"},
    {"name": "SH-4 (Namchi-Jorethang)", "type": "state_highway", "slat": 27.17, "slng": 88.55, "elat": 27.07, "elng": 88.42, "status": "open"},
    {"name": "NH-710 (Gangtok-Tsingaling)", "type": "national_highway", "slat": 27.34, "slng": 88.61, "elat": 27.45, "elng": 88.72, "status": "open"},
    # ═══ ARUNACHAL PRADESH ═══
    {"name": "NH-415 (Itanagar-Bomdila)", "type": "national_highway", "slat": 27.08, "slng": 93.69, "elat": 27.25, "elng": 92.42, "status": "open"},
    {"name": "NH-13 (Bomdila-Tawang)", "type": "national_highway", "slat": 27.25, "slng": 92.42, "elat": 27.59, "elng": 91.88, "status": "partially_blocked"},
    {"name": "NH-415 (Naharlagun-Itanagar)", "type": "national_highway", "slat": 27.10, "slng": 93.72, "elat": 27.08, "elng": 93.69, "status": "open"},
    {"name": "NH-229 (Ziro-Itanagar)", "type": "national_highway", "slat": 27.59, "slng": 93.85, "elat": 27.08, "elng": 93.69, "status": "open"},
    {"name": "NH-13 (Pasighat-Jerigaon)", "type": "national_highway", "slat": 28.07, "slng": 95.33, "elat": 27.85, "elng": 94.90, "status": "open"},
    {"name": "NH-52 (Along-Pasighat)", "type": "national_highway", "slat": 27.60, "slng": 94.70, "elat": 28.07, "elng": 95.33, "status": "open"},
    # ═══ ASSAM ═══
    {"name": "NH-37 (Guwahati-Jorhat)", "type": "national_highway", "slat": 26.14, "slng": 91.74, "elat": 26.75, "elng": 94.20, "status": "partially_blocked"},
    {"name": "NH-29 (Guwahati-Shillong)", "type": "national_highway", "slat": 26.14, "slng": 91.74, "elat": 25.58, "elng": 91.89, "status": "open"},
    {"name": "NH-31 (Guwahati-Tezpur)", "type": "national_highway", "slat": 26.14, "slng": 91.74, "elat": 26.65, "elng": 92.79, "status": "open"},
    {"name": "NH-2 (Dimapur-Dhubri)", "type": "national_highway", "slat": 25.90, "slng": 93.73, "elat": 26.02, "elng": 90.00, "status": "open"},
    {"name": "NH-44 (Silchar-Sonamura)", "type": "national_highway", "slat": 24.82, "slng": 92.80, "elat": 23.84, "elng": 91.29, "status": "open"},
    {"name": "NH-54 (Haflong-Silchar)", "type": "national_highway", "slat": 25.45, "slng": 93.18, "elat": 24.82, "elng": 92.80, "status": "partially_blocked"},
    {"name": "NH-36 (Lumding-Haflong)", "type": "national_highway", "slat": 25.85, "slng": 93.10, "elat": 25.45, "elng": 93.18, "status": "blocked"},
    {"name": "NH-62 (Tura-Guwahati)", "type": "national_highway", "slat": 25.51, "slng": 90.22, "elat": 26.14, "elng": 91.74, "status": "open"},
    {"name": "SH-3 (Jorhat-Majuli)", "type": "state_highway", "slat": 26.75, "slng": 94.20, "elat": 26.95, "elng": 94.12, "status": "open"},
    # ═══ MEGHALAYA ═══
    {"name": "NH-6 (Shillong-Tura)", "type": "national_highway", "slat": 25.58, "slng": 91.89, "elat": 25.51, "elng": 90.22, "status": "open"},
    {"name": "NH-40 (Shillong-Dawki)", "type": "national_highway", "slat": 25.58, "slng": 91.89, "elat": 25.18, "elng": 92.03, "status": "open"},
    {"name": "NH-44 (Shillong-Dimapur)", "type": "national_highway", "slat": 25.58, "slng": 91.89, "elat": 25.90, "elng": 93.73, "status": "open"},
    {"name": "NH-51 (Jowai-Shillong)", "type": "national_highway", "slat": 25.45, "slng": 92.19, "elat": 25.58, "elng": 91.89, "status": "open"},
    {"name": "SH-5 (Cherrapunji-Dawki)", "type": "state_highway", "slat": 25.28, "slng": 91.73, "elat": 25.18, "elng": 92.03, "status": "partially_blocked"},
    # ═══ NAGALAND ═══
    {"name": "NH-2 (Dimapur-Kohima)", "type": "national_highway", "slat": 25.90, "slng": 93.73, "elat": 25.66, "elng": 94.11, "status": "open"},
    {"name": "NH-2 (Kohima-Mokokchung)", "type": "national_highway", "slat": 25.66, "slng": 94.11, "elat": 26.32, "elng": 94.52, "status": "open"},
    {"name": "NH-61 (Mokokchung-Mon)", "type": "national_highway", "slat": 26.32, "slng": 94.52, "elat": 26.72, "elng": 94.87, "status": "partially_blocked"},
    {"name": "NH-129 (Tuensang-Kiphire)", "type": "national_highway", "slat": 26.27, "slng": 94.82, "elat": 25.92, "elng": 94.95, "status": "open"},
    # ═══ MANIPUR ═══
    {"name": "NH-2 (Imphal-Dimapur)", "type": "national_highway", "slat": 24.82, "slng": 93.94, "elat": 25.90, "elng": 93.73, "status": "open"},
    {"name": "NH-37 (Imphal-Jiribam)", "type": "national_highway", "slat": 24.82, "slng": 93.94, "elat": 24.80, "elng": 93.10, "status": "open"},
    {"name": "NH-102 (Imphal-Moreh)", "type": "national_highway", "slat": 24.82, "slng": 93.94, "elat": 24.48, "elng": 94.00, "status": "open"},
    {"name": "NH-129A (Churachandpur-Imphal)", "type": "national_highway", "slat": 24.33, "slng": 93.68, "elat": 24.82, "elng": 93.94, "status": "partially_blocked"},
    {"name": "SH-20 (Senapati-Imphal)", "type": "state_highway", "slat": 25.40, "slng": 94.00, "elat": 24.82, "elng": 93.94, "status": "open"},
    # ═══ MIZORAM ═══
    {"name": "NH-54 (Aizawl-Lunglei)", "type": "national_highway", "slat": 23.73, "slng": 92.72, "elat": 22.90, "elng": 92.75, "status": "blocked"},
    {"name": "NH-54 (Aizawl-Silchar)", "type": "national_highway", "slat": 23.73, "slng": 92.72, "elat": 24.82, "elng": 92.80, "status": "open"},
    {"name": "NH-306 (Sairang-Kolasib)", "type": "national_highway", "slat": 23.82, "slng": 92.67, "elat": 24.22, "elng": 92.68, "status": "open"},
    {"name": "SH-2 (Aizawl-Champhai)", "type": "state_highway", "slat": 23.73, "slng": 92.72, "elat": 23.47, "elng": 93.38, "status": "open"},
    {"name": "SH-6 (Lunglei-Saiha)", "type": "state_highway", "slat": 22.90, "slng": 92.75, "elat": 22.48, "elng": 93.00, "status": "partially_blocked"},
    # ═══ TRIPURA ═══
    {"name": "NH-8 (Agartala-Udaipur)", "type": "national_highway", "slat": 23.83, "slng": 91.29, "elat": 23.53, "elng": 91.49, "status": "open"},
    {"name": "NH-44 (Agartala-Silchar)", "type": "national_highway", "slat": 23.83, "slng": 91.29, "elat": 24.82, "elng": 92.80, "status": "open"},
    {"name": "NH-8 (Agartala-Dharmanagar)", "type": "national_highway", "slat": 23.83, "slng": 91.29, "elat": 24.37, "elng": 92.17, "status": "open"},
    {"name": "SH-3 (Kailashahar-Udaipur)", "type": "state_highway", "slat": 24.33, "slng": 92.02, "elat": 23.53, "elng": 91.49, "status": "open"},
    # ═══ CROSS-STATE ═══
    {"name": "NH-31A (Siliguri-Gelephu)", "type": "national_highway", "slat": 26.72, "slng": 88.39, "elat": 26.87, "elng": 89.85, "status": "open"},
    {"name": "NH-127B (Goalpara-Tura)", "type": "national_highway", "slat": 26.17, "slng": 90.62, "elat": 25.51, "elng": 90.22, "status": "open"},
    {"name": "NH-29A (Byrnihat-Guwahati)", "type": "national_highway", "slat": 26.10, "slng": 91.85, "elat": 26.14, "elng": 91.74, "status": "open"},
    {"name": "NH-62A (Tura-Baghmara)", "type": "national_highway", "slat": 25.51, "slng": 90.22, "elat": 25.30, "elng": 90.05, "status": "partially_blocked"},
    {"name": "NH-154 (Patharkandi-Karimganj)", "type": "national_highway", "slat": 24.85, "slng": 92.55, "elat": 24.87, "elng": 92.38, "status": "open"},
]


def _random_sensor_reading(station, hours_ago=0):
    """Generate realistic sensor readings with weather correlation."""
    now = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=hours_ago)

    # Weather patterns - monsoon season simulation
    hour_of_day = now.hour
    base_rain = max(0, 20 * math.sin((hour_of_day / 24) * math.pi - math.pi/2) + random.gauss(15, 10))
    if random.random() < 0.3:
        base_rain = random.uniform(60, 180)  # Heavy rain event

    rainfall = round(max(0, base_rain), 1)
    soil_moisture = round(min(100, 40 + rainfall * 0.4 + random.gauss(0, 5)), 1)
    ground_disp = round(abs(random.gauss(0, 1 + rainfall * 0.03)), 2)
    tilt_x = round(random.gauss(0, 0.5 + rainfall * 0.01), 2)
    tilt_y = round(random.gauss(0, 0.5 + rainfall * 0.01), 2)
    pore_pressure = round(min(100, rainfall * 0.5 + random.gauss(20, 5)), 1)
    vibration = round(abs(random.gauss(5, 8)), 1)

    return {
        "station_id": station["station_id"],
        "rainfall_mm": rainfall,
        "soil_moisture": soil_moisture,
        "soil_temperature": round(random.uniform(18, 32), 1),
        "ground_displacement": ground_disp,
        "tilt_angle_x": tilt_x,
        "tilt_angle_y": tilt_y,
        "pore_water_pressure": pore_pressure,
        "vibration_level": vibration,
        "source": "seeded_reference",
        "timestamp": now,
    }


def seed_database():
    """Populate database with realistic demo data."""
    random.seed(42)
    np.random.seed(42)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if already seeded
        if db.query(SensorStation).count() > 0:
            print("[Seed] Database already seeded, skipping.")
            return

        print("[Seed] Seeding NER sensor stations...")
        for s in NER_STATIONS:
            station = SensorStation(
                station_id=s["station_id"],
                name=s["name"],
                latitude=s["lat"],
                longitude=s["lng"],
                state=s["state"],
                district=s["district"],
                village=s["village"],
                elevation=s["elevation"],
                slope_angle=s["slope_angle"],
                soil_type=s["soil_type"],
                vegetation_cover=s["veg"],
                is_active=True,
            )
            db.add(station)

        print("[Seed] Seeding villages...")
        for v in NER_VILLAGES:
            village = Village(
                name=v["name"], state=v["state"], district=v["district"],
                latitude=v["lat"], longitude=v["lng"], population=v["pop"],
                risk_zone=v["risk"], nearest_hospital_km=v["hosp_km"],
                nearest_police_km=v["police_km"],
                evacuation_route=f"Route via {v['district']} main road",
            )
            db.add(village)

        print("[Seed] Seeding roads...")
        for r in NER_ROADS:
            road = RoadStatus(
                road_name=r["name"], road_type=r["type"],
                start_lat=r["slat"], start_lng=r["slng"],
                end_lat=r["elat"], end_lng=r["elng"],
                status=r["status"],
                blockage_reason="Landslide debris" if r["status"] == "blocked" else ("Partial debris" if r["status"] == "partially_blocked" else None),
            )
            db.add(road)

        print("[Seed] Seeding sensor readings (7 days history)...")
        for s in NER_STATIONS:
            for hours_ago in range(0, 168):  # 7 days, hourly
                reading = _random_sensor_reading(s, hours_ago)
                db.add(SensorReading(**reading))

        print("[Seed] Seeding weather data...")
        for s in NER_STATIONS:
            for hours_ago in range(0, 168, 3):  # Every 3 hours
                now = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=hours_ago)
                rainfall_1h = round(max(0, random.gauss(15, 12)), 1)
                weather = WeatherData(
                    station_id=s["station_id"],
                    temperature=round(random.uniform(18, 35), 1),
                    humidity=round(random.uniform(60, 98), 1),
                    rainfall_1h=rainfall_1h,
                    rainfall_24h=round(rainfall_1h * 8 + random.gauss(0, 10), 1),
                    rainfall_7d=round(rainfall_1h * 40 + random.gauss(0, 30), 1),
                    wind_speed=round(random.uniform(0, 25), 1),
                    wind_direction=round(random.uniform(0, 360), 1),
                    pressure=round(random.uniform(1005, 1015), 1),
                    visibility=round(random.uniform(2, 15), 1),
                    forecast_rainfall_24h=round(max(0, random.gauss(20, 15)), 1),
                    forecast_rainfall_48h=round(max(0, random.gauss(25, 20)), 1),
                    timestamp=now,
                )
                db.add(weather)

        print("[Seed] Seeding risk assessments...")
        from app.ai_engine.risk_predictor import get_predictor
        predictor = get_predictor()

        for s in NER_STATIONS:
            latest_reading = _random_sensor_reading(s, 0)
            station_data = {
                "slope_angle": s["slope_angle"],
                "elevation": s["elevation"],
                "vegetation_cover": s["veg"],
            }
            result = predictor.predict_risk(latest_reading, station_data)
            assessment = RiskAssessment(
                station_id=s["station_id"],
                risk_level=result["risk_level"],
                risk_score=result["risk_score"],
                landslide_probability=result["landslide_probability"],
                contributing_factors=json.dumps(result["contributing_factors"]),
                predicted_time_window=result["predicted_time_window_hours"],
                recommendation=result["recommendation"],
                model_version="v1.0",
            )
            db.add(assessment)

        # Seed alerts spread across 30 days for history chart
        print("[Seed] Seeding alerts (30-day history)...")
        alert_stations = [s for s in NER_STATIONS if s["slope_angle"] > 35 or s["elevation"] > 1500]
        risk_levels = ["low", "moderate", "high", "high", "critical", "moderate", "low", "high"]
        statuses = ["active", "acknowledged", "resolved"]
        for day_offset in range(30):
            # 2-4 alerts per day
            num_alerts = random.randint(2, 4)
            for _ in range(num_alerts):
                s = random.choice(alert_stations)
                rl = random.choice(risk_levels)
                alert_time = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=day_offset, hours=random.randint(0, 23))
                pop_map = {"low": 100, "moderate": 800, "high": 3000, "critical": 12000}
                alert = Alert(
                    station_id=s["station_id"],
                    risk_level=rl,
                    title=f"{rl.upper()} Risk - {s['name']}",
                    message=f"{rl.title()} landslide risk detected at {s['name']}, {s['village']}, {s['district']}.",
                    status=random.choice(statuses) if day_offset > 0 else "active",
                    affected_population=pop_map[rl] + random.randint(-200, 500),
                    nearby_villages=json.dumps([s["village"]]),
                    latitude=s["lat"],
                    longitude=s["lng"],
                    created_at=alert_time,
                )
                db.add(alert)

        # Also add 5 active alerts for the current dashboard
        for s in alert_stations[:5]:
            alert = Alert(
                station_id=s["station_id"],
                risk_level="high",
                title=f"Active Landslide Risk - {s['name']}",
                message=f"High landslide risk detected at {s['name']}, {s['village']}, {s['district']}. Heavy rainfall and steep slope conditions.",
                status="active",
                affected_population=random.randint(500, 5000),
                nearby_villages=json.dumps([s["village"]]),
                latitude=s["lat"],
                longitude=s["lng"],
            )
            db.add(alert)

        # Seed citizen reports
        print("[Seed] Seeding citizen reports...")
        report_types = ["crack", "slope_movement", "blocked_road", "flooding"]
        for _ in range(15):
            s = random.choice(NER_STATIONS)
            report = CitizenReport(
                report_type=random.choice(report_types),
                description=f"Observed {random.choice(['visible cracks on hillside', 'ground shifting noticeable', 'road blocked by debris', 'waterlogging near slope'])} near {s['village']}",
                latitude=s["lat"] + random.uniform(-0.05, 0.05),
                longitude=s["lng"] + random.uniform(-0.05, 0.05),
                reporter_name=random.choice(["Local Resident", "Field Officer", "Village Head", "PWD Worker"]),
                reporter_phone=f"+91{random.randint(6000000000, 9999999999)}",
                reporter_language=random.choice(["en", "hi", "bn", "as"]),
                status=random.choice(["pending", "verified", "verified", "pending"]),
            )
            db.add(report)

        db.commit()
        print("[Seed] ✅ Database seeded successfully with NER data!")

    except Exception as e:
        db.rollback()
        print(f"[Seed] ❌ Error: {e}")
        raise
    finally:
        db.close()

    # Generate 48h risk history so the Risk Trend chart has data on first boot
    from app.seed_risk_history import seed_risk_history
    seed_risk_history()


if __name__ == "__main__":
    seed_database()
