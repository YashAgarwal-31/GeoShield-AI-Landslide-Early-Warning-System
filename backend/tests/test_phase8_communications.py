"""Phase 8 emergency communications regression tests."""
import os

from fastapi.testclient import TestClient

from app.auth import create_token
from app.main import app
from app.services.notifications import NotificationDispatcher


client = TestClient(app)


def _headers(role: str = "admin") -> dict[str, str]:
    token = create_token(
        {
            "email": f"{role}@communications.test",
            "name": f"Communications {role}",
            "role": role,
        }
    )
    return {"Authorization": f"Bearer {token}"}


def test_district_specific_sms_recipients(monkeypatch):
    monkeypatch.setenv("ALERT_SMS_RECIPIENTS", "+911111111111")
    monkeypatch.setenv(
        "ALERT_SMS_RECIPIENTS_EAST_KHASI_HILLS",
        "+922222222222,+911111111111",
    )
    recipients = NotificationDispatcher._sms_recipients(
        {"district": "East Khasi Hills"}
    )
    assert recipients == ["+911111111111", "+922222222222"]


def test_communications_status_never_exposes_secrets(monkeypatch):
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "AC-secret")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "super-secret-token")
    monkeypatch.setenv("TWILIO_FROM_NUMBER", "+911234567890")
    monkeypatch.setenv("ALERT_SMS_RECIPIENTS", "+919876543210")
    response = client.get("/api/communications/status", headers=_headers())
    assert response.status_code == 200
    text = response.text
    assert "super-secret-token" not in text
    assert "+919876543210" not in text
    assert "AC-secret" not in text


def test_webpush_subscription_lifecycle():
    headers = _headers("citizen")
    payload = {
        "endpoint": "https://push.example.test/subscriptions/geoshield-phase8",
        "keys": {
            "p256dh": "B" * 87,
            "auth": "A" * 22,
        },
        "district": "East Khasi Hills",
    }
    subscribe = client.post(
        "/api/communications/webpush/subscribe",
        json=payload,
        headers=headers,
    )
    assert subscribe.status_code == 200
    assert subscribe.json()["status"] == "subscribed"
    assert subscribe.json()["district"] == "East Khasi Hills"

    unsubscribe = client.request(
        "DELETE",
        "/api/communications/webpush/subscribe",
        json={"endpoint": payload["endpoint"]},
        headers=headers,
    )
    assert unsubscribe.status_code == 200
    assert unsubscribe.json()["status"] == "unsubscribed"


def test_webpush_public_key_fails_cleanly_when_disabled(monkeypatch):
    monkeypatch.setenv("WEB_PUSH_ENABLED", "false")
    response = client.get(
        "/api/communications/webpush/public-key",
        headers=_headers("citizen"),
    )
    assert response.status_code == 503


def test_push_dispatch_disabled_is_nonfatal(monkeypatch):
    monkeypatch.setenv("PUSH_NOTIFICATIONS_ENABLED", "false")
    monkeypatch.setenv("WEB_PUSH_ENABLED", "false")
    dispatcher = NotificationDispatcher()
    import asyncio

    result = asyncio.run(
        dispatcher.send_push(
            {
                "risk_level": "critical",
                "title": "Phase 8 test",
                "message": "No external provider should be contacted.",
                "district": "all",
            }
        )
    )
    assert result["enabled"] is False
    assert result["sent"] == 0
