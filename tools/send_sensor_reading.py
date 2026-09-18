#!/usr/bin/env python3
"""Send one real/gateway sensor observation to a GeoShield station.

Uses only Python's standard library so it can run on a lightweight gateway.
"""
from __future__ import annotations

import argparse
import json
import sys
import uuid
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Send a sensor reading to GeoShield")
    parser.add_argument("--server", default="http://127.0.0.1:8000", help="GeoShield server base URL")
    parser.add_argument("--station", required=True, help="Station ID, e.g. NER-101")
    parser.add_argument("--api-key", required=True, help="SENSOR_INGEST_API_KEY configured on GeoShield")
    parser.add_argument("--external-id", default=None, help="Gateway message ID; auto-generated when omitted")
    parser.add_argument("--rainfall", type=float, default=0.0, help="Rainfall in mm")
    parser.add_argument("--soil-moisture", type=float, default=0.0, help="Soil moisture percentage")
    parser.add_argument("--soil-temperature", type=float, default=0.0, help="Soil temperature in Celsius")
    parser.add_argument("--displacement", type=float, default=0.0, help="Ground displacement in mm")
    parser.add_argument("--tilt-x", type=float, default=0.0, help="Tilt X in degrees")
    parser.add_argument("--tilt-y", type=float, default=0.0, help="Tilt Y in degrees")
    parser.add_argument("--pore-pressure", type=float, default=0.0, help="Pore water pressure")
    parser.add_argument("--vibration", type=float, default=0.0, help="Vibration level")
    parser.add_argument("--observed-at", default=None, help="Optional ISO-8601 timestamp")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    payload = {
        "external_id": args.external_id or f"gateway-{uuid.uuid4()}",
        "rainfall_mm": args.rainfall,
        "soil_moisture": args.soil_moisture,
        "soil_temperature": args.soil_temperature,
        "ground_displacement": args.displacement,
        "tilt_angle_x": args.tilt_x,
        "tilt_angle_y": args.tilt_y,
        "pore_water_pressure": args.pore_pressure,
        "vibration_level": args.vibration,
    }
    if args.observed_at:
        payload["observed_at"] = args.observed_at

    url = (
        args.server.rstrip("/")
        + f"/api/sensors/stations/{args.station}/readings"
    )
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-GeoShield-Sensor-Key": args.api_key,
        },
    )

    try:
        with urlopen(request, timeout=15) as response:
            body = json.loads(response.read().decode("utf-8"))
            print(json.dumps(body, indent=2))
            return 0
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"GeoShield rejected the reading (HTTP {exc.code}): {body}", file=sys.stderr)
        return 2
    except URLError as exc:
        print(f"Could not reach GeoShield: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
