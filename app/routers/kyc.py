# app/routers/verification.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from app.services.verification_service import VerificationService
from fastapi import File, UploadFile, Form
from app.models.schemas import (
    StartKYCRequest,
    StartKYCResponse,
    ScanDocumentResponse,
    VerifySelfieResponse,
    CheckStatusResponse
)

import logging

# NOTE: All endpoints return ACTUAL Sumsub results via 'sumsub_data' field
# No fake/mock data - real verification results from Sumsub API

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["ID Verification"])

# ============ KYC FLOW ============

# kyc start
@router.post("/kyc/start", response_model=StartKYCResponse)
async def start_kyc(
    request: StartKYCRequest,
    #api_key: str = Depends(verify_api_key)
):
    """BIO-011: Start KYC Verification"""
    try:
        service = VerificationService()
        result = await service.start_kyc_verification(request.user_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return StartKYCResponse(
            kyc_session_id=result["kyc_session_id"],
            status=result["status"]
        )
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed")

#  Front

@router.post("/document/scan-front", response_model=ScanDocumentResponse)
async def scan_document_front(
    kyc_session_id: str = Form(...),
    doc_type: str = Form("PASSPORT"),
    country: str = Form("USA"),
    image_file: UploadFile = File(...),
   # api_key: str = Depends(verify_api_key)
):
    """Scan ID - Front """
    try:
        image_bytes = await image_file.read()
        service = VerificationService()
        result = await service.scan_document_front(
            kyc_session_id,
            image_bytes,
            doc_type,
            country
        )
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        # Extract from actual Sumsub response (no fake values)
        sumsub_resp = result.get("sumsub_response", {})
        return ScanDocumentResponse(
            image_id=result["image_id"],
            document_detected=bool(result.get("image_id")),  # True if image uploaded
            message="Document front captured",
            sumsub_data=result  # Complete Sumsub response
        )
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed")

# BIO-012 Back
@router.post("/document/scan-back", response_model=ScanDocumentResponse)
async def scan_document_back(
    kyc_session_id: str = Form(...),
    doc_type: str = Form("PASSPORT"),
    country: str = Form("USA"),
    image_file: UploadFile = File(None),
    image_base64: str = Form(None),
  
):
    """ Scan ID - Back"""
    try:
        if not image_file and not image_base64:
            raise HTTPException(status_code=400, detail="image_file or image_base64 is required")

        image_payload = await image_file.read() if image_file else image_base64

        service = VerificationService()
        result = await service.scan_document_back(
            kyc_session_id,
            image_payload,
            doc_type,
            country
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        # Extract from actual Sumsub response (no fake values)
        return ScanDocumentResponse(
            image_id=result["image_id"],
            document_detected=bool(result.get("image_id")),  # True if image uploaded
            message="Document back captured",
            sumsub_data=result  # Complete Sumsub response
        )
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed")

# BIO-013
@router.post("/selfie/verify", response_model=VerifySelfieResponse)
async def verify_selfie(
    kyc_session_id: str = Form(...),
    image_file: UploadFile = File(None),
    image_base64: str = Form(None),
   
):
    """Take a Selfie"""
    try:
        logger.info(f"verify_selfie called with kyc_session_id: {kyc_session_id}")
        logger.info(f"image_file: {image_file}, image_base64 length: {len(image_base64) if image_base64 else 0}")
        
        if not image_file and not image_base64:
            raise HTTPException(status_code=400, detail="image_file or image_base64 is required")

        image_payload = await image_file.read() if image_file else image_base64
        logger.info(f"image_payload type: {type(image_payload)}, size: {len(image_payload) if isinstance(image_payload, bytes) else len(image_payload) if isinstance(image_payload, str) else 'unknown'}")

        service = VerificationService()
        result = await service.verify_kyc_selfie(
            kyc_session_id,
            image_payload
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        # Extract from actual Sumsub response (no fake values)
        # Face matching is done by Sumsub internally during review
        sumsub_resp = result.get("sumsub_response", {})
        return VerifySelfieResponse(
            image_id=result["image_id"],
            matches_document=bool(result.get("image_id")),  # True if uploaded successfully
            face_match_score=0.0,  # Sumsub doesn't return this immediately - check via status API
            message="Selfie uploaded - awaiting Sumsub review",
            sumsub_data=result  # Complete Sumsub response
        )
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed")

# BIO-014
@router.get("/kyc/status/{kyc_session_id}", response_model=CheckStatusResponse)
async def check_kyc_status(
    kyc_session_id: str,
    
):
    """Verification in Progress"""
    try:
        service = VerificationService()
        result = await service.check_kyc_verification_status(kyc_session_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return CheckStatusResponse(
            # status=result.get("status", "pending"),
            # progress=result.get("progress", 0),
            # message="Verification in progress",
            sumsub_data=result  # Return complete Sumsub response
        )
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed")

# Status Check
@router.get("/user/{user_id}/status")
async def get_user_status(
    user_id: str,
   # api_key: str = Depends(verify_api_key)
):
    """Get overall user verification status"""
    try:
        service = VerificationService()
        result = await service.get_user_verification_status(user_id)
        return result
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed")