from pydantic import BaseModel
from typing import Optional, Dict, Any

class DocumentParseResponse(BaseModel):
    success: bool
    tamper_warning: Optional[bool] = False
    parsed_data: Dict[str, Any]
    underwriting: Dict[str, Any]
    cam_report: Dict[str, Any]