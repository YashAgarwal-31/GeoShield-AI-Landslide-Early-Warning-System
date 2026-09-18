"""Phase 5 access-control tests for citizen reporting."""
from pathlib import Path
import uuid

from fastapi.testclient import TestClient

from app.auth import create_token
from app.database import SessionLocal
from app.main import app
from app.models import CitizenReport
from app.routers.reports import _upload_dir


client = TestClient(app)


def _headers(email: str, role: str) -> dict[str, str]:
    token = create_token(
        {
            "email": email,
            "name": email.split("@")[0],
            "role": role,
        }
    )
    return {"Authorization": f"Bearer {token}"}


def _submit_report(email: str, *, with_attachment: bool = False):
    suffix = uuid.uuid4().hex[:8]
    data = {
        "report_type": "crack",
        "description": f"Observed a fresh road-side slope crack {suffix}",
        "latitude": "25.58",
        "longitude": "91.89",
        "reporter_name": "Citizen Reporter",
        "reporter_language": "en",
    }
    files = None
    if with_attachment:
        files = {
            "attachment": (
                "evidence.png",
                b"\x89PNG\r\n\x1a\nphase5-evidence",
                "image/png",
            )
        }
    response = client.post(
        "/api/reports",
        data=data,
        files=files,
        headers=_headers(email, "citizen"),
    )
    assert response.status_code == 201, response.text
    return response.json()["report"]


def test_citizens_only_see_their_own_reports_and_evidence():
    citizen_a = f"citizen-a-{uuid.uuid4().hex[:8]}@test.invalid"
    citizen_b = f"citizen-b-{uuid.uuid4().hex[:8]}@test.invalid"
    report_a = _submit_report(citizen_a, with_attachment=True)
    report_b = _submit_report(citizen_b)

    try:
        list_a = client.get("/api/reports", headers=_headers(citizen_a, "citizen"))
        assert list_a.status_code == 200
        ids_a = {row["id"] for row in list_a.json()}
        assert report_a["id"] in ids_a
        assert report_b["id"] not in ids_a
        assert all(row["submitted_by"] == citizen_a for row in list_a.json())

        list_b = client.get("/api/reports", headers=_headers(citizen_b, "citizen"))
        assert list_b.status_code == 200
        ids_b = {row["id"] for row in list_b.json()}
        assert report_b["id"] in ids_b
        assert report_a["id"] not in ids_b

        own_attachment = client.get(
            f"/api/reports/{report_a['id']}/attachment",
            headers=_headers(citizen_a, "citizen"),
        )
        assert own_attachment.status_code == 200

        foreign_attachment = client.get(
            f"/api/reports/{report_a['id']}/attachment",
            headers=_headers(citizen_b, "citizen"),
        )
        assert foreign_attachment.status_code == 403

        staff_list = client.get(
            "/api/reports",
            headers=_headers("field-phase5@test.invalid", "field_officer"),
        )
        assert staff_list.status_code == 200
        staff_ids = {row["id"] for row in staff_list.json()}
        assert report_a["id"] in staff_ids
        assert report_b["id"] in staff_ids
    finally:
        db = SessionLocal()
        try:
            for report_id in (report_a["id"], report_b["id"]):
                row = db.query(CitizenReport).filter(CitizenReport.id == report_id).first()
                if row is not None:
                    if row.attachment_filename:
                        (_upload_dir() / Path(row.attachment_filename).name).unlink(missing_ok=True)
                    db.delete(row)
            db.commit()
        finally:
            db.close()
