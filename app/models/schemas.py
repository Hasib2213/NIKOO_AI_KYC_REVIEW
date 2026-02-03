# app/models/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class VerificationStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"


class StartKYCRequest(BaseModel):
    user_id: str

class StartKYCResponse(BaseModel):
    kyc_session_id: str
    status: str




class ScanDocumentRequest(BaseModel):
    kyc_session_id: str
    doc_type: str = "PASSPORT"
    country: str = "USA"
    image_base64: Optional[str] = None

class ScanDocumentResponse(BaseModel):
    image_id: str
    document_detected: bool
    message: str
    sumsub_data: Optional[dict] = None  # Complete Sumsub response

class VerifySelfieRequest(BaseModel):
    kyc_session_id: str
    image_base64: Optional[str] = None

class VerifySelfieResponse(BaseModel):
    image_id: str
    matches_document: bool
    face_match_score: float
    message: str
    sumsub_data: Optional[dict] = None  # Complete Sumsub response

class CheckStatusResponse(BaseModel):
    # status: str
    # progress: int
    # message: str
    sumsub_data: Optional[dict] = None  # Complete Sumsub response

class CompleteKYCResponse(BaseModel):
    message: str
    status: str
    sumsub_data: Optional[dict] = None  # Complete Sumsub response
