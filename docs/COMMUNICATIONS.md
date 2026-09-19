# GeoShield Emergency Communications — ACT Layer

GeoShield's communication layer is designed as a multi-channel early-warning
path rather than a UI-only notification feature.

## Channels

1. **Realtime WebSocket** — authenticated in-app alert stream with district
   subscriptions.
2. **SMS (Twilio)** — emergency text messages to global and/or district-specific
   recipient lists.
3. **Topic Push (ntfy)** — app/topic based push delivery with priority mapped
   from landslide severity.
4. **Standards-based Web Push (VAPID)** — browser/PWA subscriptions stored in
   PostgreSQL/SQLite. Alerts can arrive through the service worker even when the
   GeoShield tab is not open.

## District-aware routing

Global SMS recipients are configured with:

```env
ALERT_SMS_RECIPIENTS=+911234567890,+919876543210
```

A district can override/add recipients with an uppercase underscore suffix:

```env
ALERT_SMS_RECIPIENTS_EAST_KHASI_HILLS=+911111111111
```

Web Push subscriptions also carry a district. A risk alert is delivered only to
subscriptions for that district plus subscriptions configured for `all`.

## Web Push setup

Generate a VAPID P-256 key pair locally:

```bash
cd backend
python ../tools/generate_vapid_keys.py
```

Copy the generated values into your local/deployment secret environment and set
a real contact address in `VAPID_SUBJECT`. Do not commit the private key.

After login, use **Enable Emergency Push** in GeoShield settings. The browser
registers its PushManager subscription with the authenticated backend.

## SMS setup

Create/configure a Twilio project and set:

```env
SMS_NOTIFICATIONS_ENABLED=true
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_FROM_NUMBER=...
ALERT_SMS_RECIPIENTS=...
```

Twilio trial accounts can only message destinations allowed by the trial
account. Production use is subject to provider and telecom/recipient-consent
requirements.

## Communication Center

Admin and district-admin operational screens show:

- SMS provider state
- ntfy state
- VAPID Web Push state and active subscriber count
- test SMS / test Push controls
- recent delivery records

Delivery logs store channel/provider/status metadata without storing provider
credentials.

## Fail-soft behavior

External communication providers are intentionally isolated from the core alert
transaction. An SMS/push outage is recorded but does not prevent:

- alert persistence
- WebSocket delivery
- dashboard updates
- acknowledgement/resolution workflows

This separation is important for emergency communication systems because one
failed transport must not disable all warning paths.
