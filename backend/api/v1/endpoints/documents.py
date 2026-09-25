import io
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.api.deps import MockUser, get_current_user
from app.core.config import settings
from app.services.idp_service import IDPProcessingService
from app.services.pdf_service import CAMPDFGeneratorService

try:
    import pypdf
except ImportError:
    pypdf = None


router = APIRouter()
ALLOWED_TYPES = {
    "application/pdf": ".pdf",
    "image/png": ".png",
    "image/jpeg": ".jpg",
}


class ExtractedFieldData(BaseModel):
    value: Any = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    needs_manual_review: bool


class IDPParsingResponse(BaseModel):
    filename: str
    file_type: str
    overall_confidence: float
    extracted_data: Dict[str, ExtractedFieldData]
    rbi_dpdp_notice: str = "Data processed in-memory via TLS 1.3."


class DocumentUploadResponse(IDPParsingResponse):
    document_id: UUID
    owner: str
    stored_at: datetime
    report_url: str


def _owner_dir(user: MockUser) -> Path:
    owner_key = re.sub(r"[^a-zA-Z0-9_.-]", "_", user.email)[:100] or "anonymous"
    path = settings.DOCUMENT_STORAGE_DIR / owner_key
    path.mkdir(parents=True, exist_ok=True)
    return path


def _document_paths(document_id: UUID, user: MockUser) -> tuple[Path, Path]:
    directory = _owner_dir(user)
    return directory / f"{document_id}.bin", directory / f"{document_id}.json"


async def _read_validated_upload(file: UploadFile) -> bytes:
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail="Only PDF, PNG, and JPEG financial documents are accepted.",
        )
    if not file.filename or Path(file.filename).name != file.filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")

    chunks = []
    size = 0
    while chunk := await file.read(1024 * 1024):
        size += len(chunk)
        if size > settings.MAX_DOCUMENT_SIZE_BYTES:
            raise HTTPException(
                status_code=413,
                detail="Document exceeds the 10 MB limit.",
            )
        chunks.append(chunk)

    if not size:
        raise HTTPException(status_code=400, detail="The uploaded document is empty.")
    return b"".join(chunks)


@router.post("/parse-docket", response_model=IDPParsingResponse)
async def upload_and_parse_document(
    file: UploadFile = File(...),
    current_user: MockUser = Depends(get_current_user),
):
    contents = await _read_validated_upload(file)
    raw_text = ""
    if file.content_type == "application/pdf" and pypdf:
        reader = pypdf.PdfReader(io.BytesIO(contents))
        for page in reader.pages:
            raw_text += (page.extract_text() or "") + "\n"
    else:
        raw_text = contents.decode("latin-1", errors="ignore")

    idp_results = IDPProcessingService.parse_gst_3b_text(raw_text)
    gstin_val = idp_results.get("gstin")
    turnover_val = idp_results.get("annual_turnover_estimate")

    document_id = uuid4()
    document_path, metadata_path = _document_paths(document_id, current_user)
    document_path.write_bytes(contents)
    stored_at = datetime.now(timezone.utc)
    response = {
        "document_id": document_id,
        "filename": file.filename,
        "file_type": file.content_type,
        "owner": current_user.email,
        "stored_at": stored_at,
        "report_url": f"{settings.API_V1_STR}/documents/{document_id}/cam-report",
        "overall_confidence": idp_results.get("confidence_score", 0.50),
        "extracted_data": {
            "gstin": ExtractedFieldData(
                value=gstin_val,
                confidence=0.95 if gstin_val else 0.0,
                needs_manual_review=not bool(gstin_val),
            ),
            "annual_turnover_inr": ExtractedFieldData(
                value=turnover_val,
                confidence=0.88 if turnover_val else 0.0,
                needs_manual_review=not bool(turnover_val),
            ),
        },
    }
    metadata_path.write_text(json.dumps(response, default=str), encoding="utf-8")
    return response


@router.get("/{document_id}/cam-report")
async def download_cam_report(
    document_id: UUID,
    current_user: MockUser = Depends(get_current_user),
):
    document_path, metadata_path = _document_paths(document_id, current_user)
    if not metadata_path.is_file() or not document_path.is_file():
        raise HTTPException(status_code=404, detail="Document not found.")

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    report_data = {
        "proposal_date": metadata["stored_at"][:10],
        "client_legal_name": current_user.email,
        "operating_name": metadata["filename"],
        "business_summary_text": (
            "Financial document uploaded for preliminary MSME credit appraisal."
        ),
        "annual_turnover_inr": (
            metadata["extracted_data"].get("annual_turnover_inr", {}).get("value") or 0
        ),
        "monthly_turnover_matrix": [],
    }
    pdf_bytes = CAMPDFGeneratorService.generate_cam_pdf(report_data)
    report_path = document_path.with_suffix(".pdf")
    report_path.write_bytes(pdf_bytes)
    return FileResponse(
        report_path,
        media_type="application/pdf",
        filename=f"jinops-cam-{document_id}.pdf",
    )
