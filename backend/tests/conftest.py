"""Deterministic test defaults for external integrations.

Individual tests can opt providers back in explicitly. Keeping networked providers
off by default makes the full test suite repeatable on CI and offline developer
machines.
"""
import os

os.environ.setdefault("WEATHER_LIVE_ENABLED", "false")
os.environ.setdefault("SRTM_LIVE_ENABLED", "false")
os.environ.setdefault("SENTINEL2_LIVE_ENABLED", "false")
os.environ.setdefault("IMD_LIVE_ENABLED", "false")
os.environ.setdefault("FLOOD_LIVE_ENABLED", "false")
os.environ.setdefault("SMS_NOTIFICATIONS_ENABLED", "false")
os.environ.setdefault("PUSH_NOTIFICATIONS_ENABLED", "false")
