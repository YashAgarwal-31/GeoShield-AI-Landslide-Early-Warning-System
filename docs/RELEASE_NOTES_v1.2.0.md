# GeoShield v1.2.0 — ACT Emergency Communications

GeoShield v1.2.0 strengthens the communication-engineering side of the major
project with a redundant, district-aware early-warning delivery layer.

## New communication capabilities

- **Twilio SMS** for real emergency text delivery when deployment credentials
  and recipient numbers are configured.
- Global plus **district-specific SMS recipient routing**.
- **ntfy push** retained as an independent topic/mobile push transport.
- **Standards-based Web Push (VAPID)** with persistent browser/PWA
  subscriptions stored in SQLite/PostgreSQL.
- Service-worker push notifications that can be displayed when the application
  tab is not active.
- Automatic multi-channel fan-out when GeoShield creates a landslide alert.
- Persistent notification delivery records for SMS and push attempts.
- **Emergency Communication Center** for admin/district-admin channel status,
  subscriber count, test SMS/test Push, and recent delivery results.
- VAPID key-generation utility plus production configuration documentation.

## Reliability design

SMS, Web Push, ntfy, and the existing authenticated district WebSocket operate
as separate transports. External-provider failure is fail-soft: a failed SMS or
push attempt is logged and does not prevent alert persistence or the remaining
warning channels.

## Security

No Twilio tokens, phone numbers, VAPID private keys, or other provider secrets
are committed. Web Push subscriptions require authenticated users. Test sending
is restricted to admin and district-admin roles.

## Deployment activation

Real external delivery needs deployment-owned configuration:

- Twilio account SID, auth token, sender number and approved recipients for SMS.
- VAPID public/private key pair and contact subject for browser/PWA Web Push.
- ntfy topic/token if the ntfy transport is enabled.

Use `tools/generate_vapid_keys.py` for a compatible VAPID key pair and see
`docs/COMMUNICATIONS.md` for setup and architecture.
