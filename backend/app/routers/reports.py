import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_role
from app.database import get_db
from app.models import CitizenReport, RoadStatus, Village


router = APIRouter(prefix="/api", tags=["reports"])

_ALLOWED_ATTACHMENTS = {
    "image/jpeg": (".jpg", lambda data: data.startswith(b"\xff\xd8\xff")),
    "image/png": (".png", lambda data: data.startswith(b"\x89PNG\r\n\x1a\n")),
    "image/webp": (
        ".webp",
        lambda data: len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP",
    ),
    "video/mp4": (
        ".mp4",
        lambda data: len(data) >= 12 and data[4:8] == b"ftyp",
    ),
    "video/webm": (
        ".webm",
        lambda data: data.startswith(b"\x1a\x45\xdf\xa3"),
    ),
}


def _upload_dir() -> Path:
    configured = os.getenv("REPORT_UPLOAD_DIR", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return (Path(__file__).resolve().parent.parent / "uploads" / "reports").resolve()


def _max_upload_bytes() -> int:
    try:
        configured = int(os.getenv("REPORT_UPLOAD_MAX_BYTES", str(10 * 1024 * 1024)))
    except ValueError:
        configured = 10 * 1024 * 1024
    return max(1024, min(configured, 50 * 1024 * 1024))


async def _save_attachment(attachment: UploadFile | None) -> str | None:
    if attachment is None or not attachment.filename:
        return None

    rule = _ALLOWED_ATTACHMENTS.get((attachment.content_type or "").lower())
    if rule is None:
        raise HTTPException(
            status_code=415,
            detail="Attachment must be JPEG, PNG, WebP, MP4, or WebM.",
        )

    max_bytes = _max_upload_bytes()
    data = await attachment.read(max_bytes + 1)
    await attachment.close()

    if not data:
        raise HTTPException(status_code=422, detail="Attachment is empty.")
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Attachment exceeds the {max_bytes // (1024 * 1024)} MB limit.",
        )

    extension, validator = rule
    if not validator(data):
        raise HTTPException(
            status_code=422,
            detail="Attachment content does not match its declared media type.",
        )

    upload_dir = _upload_dir()
    upload_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4().hex}{extension}"
    target = (upload_dir / filename).resolve()
    if target.parent != upload_dir:
        raise HTTPException(status_code=500, detail="Attachment path validation failed.")

    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_bytes(data)
    temporary.replace(target)
    return filename


def _attachment_response(report: CitizenReport) -> dict:
    return {
        "id": report.id,
        "report_type": report.report_type,
        "description": report.description,
        "latitude": report.latitude,
        "longitude": report.longitude,
        "reporter_name": report.reporter_name,
        "reporter_language": report.reporter_language,
        "status": report.status,
        "attachment_filename": report.attachment_filename,
        "created_at": report.created_at.isoformat() if report.created_at else None,
    }


# ---- Citizen Reports ----

@router.post("/reports", status_code=201)
async def create_report(
    report_type: str = Form(..., pattern=r"^(crack|slope_movement|blocked_road|flooding|other)$"),
    description: str = Form(..., min_length=10, max_length=2000),
    latitude: float = Form(..., ge=21.0, le=30.0),
    longitude: float = Form(..., ge=88.0, le=98.0),
    reporter_name: Optional[str] = Form(None, max_length=100),
    reporter_phone: Optional[str] = Form(None, pattern=r"^\+?[\d\s-]{7,15}$"),
    reporter_language: str = Form("en", pattern=r"^(en|hi|bn|as|ne)$"),
    attachment: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    attachment_filename = await _save_attachment(attachment)

    report = CitizenReport(
        report_type=report_type,
        description=description.strip(),
        latitude=latitude,
        longitude=longitude,
        reporter_name=reporter_name.strip() if reporter_name else None,
        reporter_phone=reporter_phone.strip() if reporter_phone else None,
        reporter_language=reporter_language,
        status="pending",
        attachment_filename=attachment_filename,
    )
    try:
        db.add(report)
        db.commit()
        db.refresh(report)
    except Exception:
        db.rollback()
        if attachment_filename:
            (_upload_dir() / attachment_filename).unlink(missing_ok=True)
        raise

    return {
        "status": "success",
        "message": "Report submitted successfully. Thank you for your contribution!",
        "report": _attachment_response(report),
    }


@router.get("/reports")
def get_reports(
    status: str | None = Query(None, pattern=r"^(pending|verified|dismissed)$"),
    report_type: str | None = Query(
        None,
        pattern=r"^(crack|slope_movement|blocked_road|flooding|other)$",
    ),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    query = db.query(CitizenReport)
    if status:
        query = query.filter(CitizenReport.status == status)
    if report_type:
        query = query.filter(CitizenReport.report_type == report_type)

    reports = query.order_by(desc(CitizenReport.created_at)).limit(limit).all()
    return [_attachment_response(report) for report in reports]


@router.get("/reports/{report_id}/attachment")
def get_report_attachment(
    report_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    report = db.query(CitizenReport).filter(CitizenReport.id == report_id).first()
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    if not report.attachment_filename:
        raise HTTPException(status_code=404, detail="Report has no attachment")

    upload_dir = _upload_dir()
    target = (upload_dir / Path(report.attachment_filename).name).resolve()
    if target.parent != upload_dir or not target.is_file():
        raise HTTPException(status_code=404, detail="Attachment file not found")

    media_type = {
        ".jpg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".mp4": "video/mp4",
        ".webm": "video/webm",
    }.get(target.suffix.lower(), "application/octet-stream")

    return FileResponse(
        target,
        media_type=media_type,
        filename=target.name,
    )


@router.put("/reports/{report_id}/verify")
def verify_report(
    report_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin")),
):
    report = db.query(CitizenReport).filter(CitizenReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    report.status = "verified"
    report.verified_by = str(user.get("sub") or user.get("name") or "admin")
    db.commit()
    return {
        "message": "Report verified",
        "id": report_id,
        "verified_by": report.verified_by,
    }


@router.put("/reports/{report_id}/dismiss")
def dismiss_report(
    report_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin", "field_officer", "district_admin")),
):
    report = db.query(CitizenReport).filter(CitizenReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    report.status = "dismissed"
    db.commit()
    return {"message": "Report dismissed", "id": report_id}


# ---- Road Status ----

@router.get("/roads")
def get_roads(db: Session = Depends(get_db)):
    roads = db.query(RoadStatus).all()
    return [{
        "id": r.id,
        "road_name": r.road_name,
        "road_type": r.road_type,
        "start_lat": r.start_lat,
        "start_lng": r.start_lng,
        "end_lat": r.end_lat,
        "end_lng": r.end_lng,
        "status": r.status,
        "blockage_reason": r.blockage_reason,
        "alternative_route": r.alternative_route,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
    } for r in roads]


# ---- Villages ----

@router.get("/villages")
def get_villages(
    risk_zone: str = None,
    db: Session = Depends(get_db),
):
    query = db.query(Village)
    if risk_zone:
        query = query.filter(Village.risk_zone == risk_zone)

    villages = query.all()
    return [{
        "id": v.id,
        "name": v.name,
        "state": v.state,
        "district": v.district,
        "latitude": v.latitude,
        "longitude": v.longitude,
        "population": v.population,
        "risk_zone": v.risk_zone,
        "nearest_hospital_km": v.nearest_hospital_km,
        "nearest_police_km": v.nearest_police_km,
    } for v in villages]
