# Weather and satellite source adapters

Phase 3 adds a common provenance contract to every weather and satellite
response. The application no longer labels seeded or old snapshot values as
live.

## Source metadata contract

Each response includes:

| Field | Meaning |
|---|---|
| `mode` | `live`, `cached`, `fallback`, or `unavailable` |
| `provider` | Service or local source that produced the value |
| `observed_at` | UTC observation/snapshot timestamp, when known |
| `served_at` | UTC API response timestamp |
| `age_seconds` | Age at response time |
| `max_age_seconds` | Configured freshness threshold |
| `is_stale` | Whether age exceeds the threshold or is unknown |
| `fallback_reason` | Machine-readable reason for degraded mode |
| `detail` | Human-readable provenance explanation |

## Weather behavior

Live Open-Meteo weather is enabled by default. Weather endpoints use a bounded
timeout and automatically serve seeded demonstration rows with `mode=fallback`
when the network/provider is unavailable, making degraded status unambiguous.

To configure current model-derived weather explicitly:

```bash
export WEATHER_LIVE_ENABLED=true
export WEATHER_REQUEST_TIMEOUT_SECONDS=5
export WEATHER_CACHE_TTL_SECONDS=900
```

For a deterministic offline-only run, set `WEATHER_LIVE_ENABLED=false` or use
`start-offline.bat`.

The Open-Meteo adapter uses a bounded timeout and a successful-response cache.
If the provider fails after a prior success, the stale cached result is returned
with the failure reason. If no live cache exists, the API uses seeded demo data.

The `/api/weather/{station_id}/forecast` response now includes `series_kind`:

- `forecast` for an external model forecast;
- `demo_history` for the seeded offline series.

Open-Meteo documents its forecast endpoint, current variables, hourly variables,
and `past_hours`/`forecast_hours` parameters at
<https://open-meteo.com/en/docs>.

## Satellite behavior

The included JSON file is a cached snapshot, not a live satellite connection.
The adapter reloads it when the file modification time changes and calculates
freshness from the oldest station timestamp. The default stale threshold is six
hours:

```bash
export SATELLITE_MAX_AGE_SECONDS=21600
```

Responses from `/api/satellite/data`, `/api/satellite/summary`, and
`/api/satellite/risk-zones` share the same source metadata. NDVI remains an
estimate in the current snapshot.

## Frontend behavior

The Satellite and Station pages display source badges instead of unconditional
green “live” indicators. Badges distinguish live, cached, seeded fallback, stale,
and unavailable states and show the source age.
