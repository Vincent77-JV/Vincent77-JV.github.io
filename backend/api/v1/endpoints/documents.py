import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

PROJECT_ROOT = Path(__file__).resolve().parents[5]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from app.jinops_engine import JinOpsUnderwritingEngine
except ImportError:
    JinOpsUnderwritingEngine = None

try:
    from app.services.pdf_service import CAMPDFGeneratorService
except ImportError:
    CAMPDFGeneratorService = None

router = APIRouter()

UPLOAD_DIR = PROJECT_ROOT / "uploads" / "documents"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_BYTES = 50 * 1024 * 1024

ALLOWED_MIME_TYPES = {
    "application/pdf": ".pdf",
    "image/png": ".png",
    "image/jpeg": ".jpg",
}

class DocumentUploadResponse(BaseModel):
    status: str
    message: str
    data: Dict[str, Any]


# ==================== STEP 2: HIGH-PERFORMANCE MULTI-STEP FILE UPLOAD & UNDERWRITING ====================
@router.post("/upload-msme-docs", response_model=DocumentUploadResponse)
async def upload_msme_documents(
    applicant_name: str = Form(...),
    business_name: str = Form("JinOps Client"),
    cibil_score: int = Form(710),
    monthly_income: float = Form(250000.0),
    existing_emi: float = Form(40000.0),
    requested_loan: float = Form(2000000.0),
    tenure_months: int = Form(36),
    interest_rate: float = Form(14.0),
    bank_statement: UploadFile = File(...),
    gst_file: UploadFile = File(...)
):
    """Store two financial documents and run the underwriting engine."""
    try:
        if bank_statement.content_type not in ALLOWED_MIME_TYPES or gst_file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail="à°…à°¨à±à°®à°¤à°¿à°‚à°šà°¬à°¡à°¿à°¨ à°«à±ˆà°²à± à°°à°•à°¾à°²à± à°•à±‡à°µà°²à°‚ PDF, PNG, à°²à±‡à°¦à°¾ JPG à°®à°¾à°¤à±à°°à°®à±‡."
            )

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        unique_id = uuid4().hex[:8]

        bank_filename = f"bank_{timestamp}_{unique_id}_{Path(bank_statement.filename or 'upload').name}"
        bank_path = UPLOAD_DIR / bank_filename

        with open(bank_path, "wb") as buffer:
            shutil.copyfileobj(bank_statement.file, buffer)

        gst_filename = f"gst_{timestamp}_{unique_id}_{Path(gst_file.filename or 'upload').name}"
        gst_path = UPLOAD_DIR / gst_filename

        with open(gst_path, "wb") as buffer:
            shutil.copyfileobj(gst_file.file, buffer)

        if bank_path.stat().st_size > MAX_BYTES or gst_path.stat().st_size > MAX_BYTES:
            bank_path.unlink(missing_ok=True)
            gst_path.unlink(missing_ok=True)
            raise HTTPException(status_code=413, detail="à°«à±ˆà°²à± à°ªà°°à°¿à°®à°¾à°£à°‚ 50MB à°•à°‚à°Ÿà±‡ à°¤à°•à±à°•à±à°µà°—à°¾ à°‰à°‚à°¡à°¾à°²à°¿.")

        underwriting_result = {}
        if JinOpsUnderwritingEngine is not None:
            engine = JinOpsUnderwritingEngine()
            underwriting_result = engine.process_underwriting(
                applicant_name=applicant_name,
                cibil_score=cibil_score,
                monthly_income=monthly_income,
                existing_emi=existing_emi,
                annual_gst_turnover=monthly_income * 12 * 0.95,
                annual_banking_turnover=monthly_income * 12,
                net_profit_annual=monthly_income * 12 * 0.18,
                depreciation_annual=50000.0,
                interest_annual=60000.0,
                requested_loan=requested_loan,
                tenure_months=tenure_months,
                interest_rate=interest_rate
            )

        return DocumentUploadResponse(
            status="SUCCESS",
            message="à°¡à°¾à°•à±à°¯à±à°®à±†à°‚à°Ÿà±à°²à± à°µà°¿à°œà°¯à°µà°‚à°¤à°‚à°—à°¾ à°…à°ªà±â€Œà°²à±‹à°¡à± à°…à°¯à±à°¯à°¾à°¯à°¿ à°®à°°à°¿à°¯à± à°ªà±à°°à°¾à°¸à±†à°¸à°¿à°‚à°—à± à°ªà±‚à°°à±à°¤à°¯à°¿à°‚à°¦à°¿!",
            data={
                "applicant": applicant_name,
                "business": business_name,
                "saved_bank_statement": bank_filename,
                "saved_gst_file": gst_filename,
                "total_file_size_bytes": bank_path.stat().st_size + gst_path.stat().st_size,
                "upload_timestamp": datetime.now(timezone.utc).isoformat(),
                "underwriting_summary": underwriting_result
            }
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"à°…à°ªà±â€Œà°²à±‹à°¡à± à°²à±‡à°¦à°¾ à°…à°‚à°¡à°°à±â€Œà°°à±ˆà°Ÿà°¿à°‚à°—à± à°µà°¿à°«à°²à°®à±ˆà°‚à°¦à°¿: {str(e)}")
