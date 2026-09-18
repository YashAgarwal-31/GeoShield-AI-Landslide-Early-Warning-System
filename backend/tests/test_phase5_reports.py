"""Phase 5 regression tests for operational citizen evidence reports."""
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from app.auth import create_token
from app.database import SessionLocal
from app.main import app
from app.models import CitizenReport


client = TestClient(app)


def _token(role: str, suffix: str = "reports") -> str:
    return create_token(
        {
            "email": f"{role}-{suffix}@phase5.test",
            "name": f"Phase 5 {role}",
            "role": role,
        }
    )


def test_report_feed_requires_authentication():
    response = client.get("/api/reports")
    assert response.status_code == 401


def test_citizen_report_evidence_persists_and_can_be_reviewed(monkeypatch, tmp_path):
    monkeypatch.setenv("REPORT_UPLOAD_DIR", str(tmp_path))
    citizen_token = _token("citizen")
    admin_token = _token("admin")
    marker = uuid.uuid4().hex

    response = client.post(
        "/api/reports",
        data={
            "report_type": "crack",
            "description": f"Fresh slope crack observed near retaining wall {marker}",
            "latitude": "25.58",
            "longitude": "91.89",
            "reporter_name": "Phase Five Reporter",
            "reporter_language": "en",
        },
        files={
            "attachment": (
                "evidence.png",
                b"\x89PNG\r\n\x1a\nphase-five-test-evidence",
                "image/png",
            ),
        },
        headers={"Authorization": f"Bearer {citizen_token}"},
    )
    assert response.status_code == 201, response.text
    report = response.json()["report"]
    report_id = report["id"]
    filename = report["attachment_filename"]
    assert filename.endswith(".png")
    assert (tmp_path / filename).is_file()

    feed = client.get(
        "/api/reports",
        headers={"Authorization": f"Bearer {citizen_token}"},
    )
    assert feed.status_code == 200
    assert any(item["id"] == report_id and item["attachment_filename"] == filename for item in feed.json())

    attachment = client.get(
        f"/api/reports/{report_id}/attachment",
        headers={"Authorization": f"Bearer {citizen_token}"},
    )
    assert attachment.status_code == 200
    assert attachment.content.startswith(b"\x89PNG\r\n\x1a\n")

    verified = client.put(
        f"/api/reports/{report_id}/verify",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert verified.status_code == 200
    assert verified.json()["verified_by"] == "admin-reports@phase5.test"

    db = SessionLocal()
    try:
        row = db.query(CitizenReport).filter(CitizenReport.id == report_id).first()
        if row:
            db.delete(row)
            db.commit()
    finally:
        db.close()
    (tmp_path / filename).unlink(missing_ok=True)


def test_report_rejects_spoofed_attachment_content(monkeypatch, tmp_path):
    monkeypatch.setenv("REPORT_UPLOAD_DIR", str(tmp_path))
    token = _token("citizen", suffix=uuid.uuid4().hex[:8])

    response = client.post(
        "/api/reports",
        data={
            "report_type": "slope_movement",
            "description": "Visible slope movement with displaced loose material.",
            "latitude": "25.58",
            "longitude": "91.89",
            "reporter_language": "en",
        },
        files={
            "attachment": (
                "fake.png",
                b"this-is-not-a-png",
                "image/png",
            ),
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422
    assert list(Path(tmp_path).glob("*")) == []
