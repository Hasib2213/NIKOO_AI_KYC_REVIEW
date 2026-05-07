# app/services/sumsub_service.py

import hashlib
import hmac
import json
import logging
import time
import uuid
import base64
from typing import Dict, Any, Optional
import requests
from io import BytesIO

from config import settings

logger = logging.getLogger(__name__)

class SumsubService:
    """
    Sumsub API Integration following design flow
    """
    
    def __init__(self):
        self.base_url = settings.SUMSUB_BASE_URL.rstrip('/')  # Ensure no trailing slash
        self.app_token = settings.SUMSUB_APP_TOKEN
        self.level_name = settings.SUMSUB_LEVEL_NAME
        self.timeout = settings.REQUEST_TIMEOUT
        
        # Handle secret key - may be base64 encoded
        self.secret_key = self._decode_secret_key(settings.SUMSUB_SECRET_KEY)
    
    def _decode_secret_key(self, secret_key: str) -> str:
        """
        Decode secret key if it's base64 encoded
        SumSub sometimes provides keys in base64 format
        """
        try:
            # Try to decode as base64
            decoded = base64.b64decode(secret_key).decode('utf-8')
            # If successful and different from original, use decoded version
            if decoded != secret_key:
                logger.info("Secret key decoded from base64 format")
                return decoded
            return secret_key
        except Exception as e:
            # If decode fails, assume it's plain text
            logger.debug(f"Secret key is not base64 encoded (or already plain): {str(e)}")
            return secret_key
    
    def _sign_request(self, method: str, path_url: str, body: bytes = b'', is_multipart: bool = False) -> Dict[str, str]:
        """Sign request with Sumsub HMAC-SHA256"""
        now = int(time.time())
        
        if isinstance(body, str):
            body = body.encode('utf-8')
        
        data_to_sign = (
            str(now).encode('utf-8') + 
            method.upper().encode('utf-8') + 
            path_url.encode('utf-8') + 
            body
        )
        
        # Log signature details for debugging (sanitized)
        logger.debug(f"Signature calculation:")
        logger.debug(f"  Timestamp: {now}")
        logger.debug(f"  Method: {method.upper()}")
        logger.debug(f"  Path: {path_url}")
        logger.debug(f"  Body length: {len(body)}")
        logger.debug(f"  Data to sign length: {len(data_to_sign)}")
        
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            data_to_sign,
            digestmod=hashlib.sha256
        ).hexdigest()
        
        # SECURITY: Only log partial signature (never log full signature or secret key)
        logger.debug(f"  Signature prefix: {signature[:8]}...")
        
        headers = {
            'X-App-Token': self.app_token,
            'X-App-Access-Ts': str(now),
            'X-App-Access-Sig': signature,
            'Accept': 'application/json',
            'X-Return-Doc-Warnings': 'true',
        }
        
        if not is_multipart:
            headers['Content-Type'] = 'application/json'
        
        return headers
    
    # ==================== LIVENESS FLOW (BIO-008 to BIO-010) ====================
    
    # async def start_liveness_session(self, user_id: str) -> Dict[str, Any]:
    #     """
    #     BIO-008: Start Face Liveness Detection
    #     Create applicant for liveness verification
    #     """
    #     try:
    #         external_user_id = f"liveness_{user_id}_{int(time.time())}"
    #         body = json.dumps({'externalUserId': external_user_id})
    #         path = f'/resources/applicants?levelName={self.level_name}'
    #         headers = self._sign_request('POST', path, body.encode('utf-8'))
            
    #         logger.info(f"Starting liveness session for user: {user_id}")
    #         logger.info(f"Base URL: {self.base_url}")
    #         logger.info(f"Path: {path}")
    #         logger.info(f"External User ID: {external_user_id}")
            
    #         response = requests.post(
    #             f"{self.base_url}{path}",
    #             headers=headers,
    #             data=body,
    #             timeout=self.timeout
    #         )
            
    #         logger.info(f"Sumsub Response Status: {response.status_code}")
    #         logger.info(f"Sumsub Response Body: {response.text}")
            
    #         if response.status_code == 201:
    #             data = response.json()
    #             logger.info(f"Liveness session created: {data['id']}")
    #             return {
    #                 "success": True,
    #                 "session_id": data['id'],
    #                 "external_user_id": external_user_id,
    #                 "status": "initiated"
    #             }
    #         else:
    #             error_msg = f"Sumsub API Error: Status {response.status_code} - {response.text}"
    #             logger.error(error_msg)
    #             return {"success": False, "error": error_msg}
    #     except requests.exceptions.ConnectionError as e:
    #         error_msg = f"Connection Error: Cannot reach Sumsub API at {self.base_url}"
    #         logger.error(f"{error_msg} - {str(e)}")
    #         return {"success": False, "error": error_msg}
    #     except requests.exceptions.Timeout as e:
    #         error_msg = f"Timeout: Sumsub API request took too long"
    #         logger.error(f"{error_msg} - {str(e)}")
    #         return {"success": False, "error": error_msg}
    #     except Exception as e:
    #         error_msg = f"Unexpected Error in start_liveness_session: {str(e)}"
    #         logger.error(error_msg)
    #         import traceback
    #         logger.error(traceback.format_exc())
    #         return {"success": False, "error": error_msg}
    
    # async def add_liveness_selfie(
    #     self, 
    #     applicant_id: str,
    #     selfie_image_bytes: bytes
    # ) -> Dict[str, Any]:
    #     """
    #     BIO-009: Process Face Liveness Check with Active Liveness Verification
    #     Upload selfie for liveness detection using /info/idDoc endpoint (not /info/selfie)
    #     Sumsub automatically performs advanced face liveness check (look left, blink, look right)
    #     when using idDocType: "SELFIE" per official API docs
    #     """
    #     try:
    #         # Per Sumsub official API: use /info/idDoc endpoint with metadata idDocType: "SELFIE"
    #         metadata = json.dumps({
    #             "idDocType": "SELFIE",
    #             "country": "BGD"  # Bangladesh (adjust if needed per user locale)
    #         })
            
    #         path = f'/resources/applicants/{applicant_id}/info/idDoc'
    #         full_url = f"{self.base_url}{path}"

    #         logger.info("Uploading liveness selfie to correct Sumsub endpoint for active liveness")
    #         logger.info(f"  Applicant ID: {applicant_id}")
    #         logger.info(f"  Path: {path}")
    #         logger.info(f"  Full URL: {full_url}")
    #         logger.info(f"  Selfie size: {len(selfie_image_bytes)} bytes")
    #         logger.info(f"  Metadata: {metadata}")

    #         # Prepare multipart request with metadata (required for SELFIE type)
    #         files = {'content': ('selfie.jpg', BytesIO(selfie_image_bytes), 'image/jpeg')}
    #         data = {'metadata': metadata}
            
    #         req = requests.Request('POST', full_url, files=files, data=data)
    #         prepared = req.prepare()

    #         # Sign using actual prepared multipart body (includes boundary)
    #         now = int(time.time())
    #         path_url = prepared.path_url
    #         data_to_sign = (
    #             str(now).encode('utf-8') +
    #             b'POST' +
    #             path_url.encode('utf-8') +
    #             prepared.body
    #         )
    #         signature = hmac.new(
    #             self.secret_key.encode('utf-8'),
    #             data_to_sign,
    #             digestmod=hashlib.sha256
    #         ).hexdigest()

    #         logger.info(f"  Timestamp: {now}")
    #         logger.info(f"  Multipart body size: {len(prepared.body)} bytes")
    #         logger.info(f"  X-App-Access-Sig: {signature[:30]}...")

    #         headers = {
    #             'X-App-Token': self.app_token,
    #             'X-App-Access-Ts': str(now),
    #             'X-App-Access-Sig': signature,
    #             'Accept': 'application/json',
    #             'X-Return-Doc-Warnings': 'true',
    #         }
    #         # Copy Content-Type (with boundary) from prepared
    #         if 'Content-Type' in prepared.headers:
    #             headers['Content-Type'] = prepared.headers['Content-Type']

    #         session = requests.Session()
    #         prepared.headers.update(headers)
    #         response = session.send(prepared, timeout=self.timeout)

    #         logger.info(f"Response Status: {response.status_code}")
            
    #         if response.status_code not in [200, 201]:
    #             logger.error(f"Response Headers: {dict(response.headers)}")
    #             logger.error(f"Response Body: {response.text}")
                
    #             if response.status_code == 401:
    #                 logger.error("⚠️ 401 SIGNATURE MISMATCH")
    #                 logger.error("   Verify SUMSUB_SECRET_KEY in .env")
    #                 logger.error("   Check system clock sync: w32tm /resync")
    #             elif response.status_code == 404:
    #                 logger.error("⚠️ 404 NOT FOUND - Applicant ID does not exist or expired")
    #                 logger.error("   Ensure applicant was created with /liveness/start")

    #         if response.status_code in [200, 201]:
    #             image_id = response.headers.get('X-Image-Id', '')
    #             if not image_id and response.headers.get('Content-Type', '').startswith('application/json'):
    #                 response_data = response.json()
    #                 image_id = response_data.get('id', '')
                
    #             logger.info(f"✅ Liveness selfie uploaded successfully: {image_id}")
    #             logger.info("   Sumsub will now perform active liveness verification (advanced face analysis)")
    #             logger.info("   Result will be available via webhook or GET /applicants/{id}/status")
                
    #             # Return actual Sumsub response (no fake values)
    #             return {
    #                 "success": True,
    #                 "image_id": image_id,
    #                 "message": "Liveness selfie submitted. Advanced liveness check in progress...",
    #                 "sumsub_response": response_data if 'response_data' in locals() else {},
    #                 "sumsub_headers": dict(response.headers)
    #             }
    #         else:
    #             error_msg = f"Sumsub API Error: Status {response.status_code}"
    #             try:
    #                 error_data = response.json()
    #                 if 'description' in error_data:
    #                     error_msg += f" - {error_data['description']}"
    #                 if 'errorCode' in error_data:
    #                     error_msg += f" (Code: {error_data['errorCode']})"
    #             except:
    #                 error_msg += f" - {response.text}"
                
    #             logger.error(f"❌ Failed to upload liveness selfie: {error_msg}")
    #             return {
    #                 "success": False, 
    #                 "error": error_msg, 
    #                 "is_live": False, 
    #                 "status_code": response.status_code
    #             }
    #     except Exception as e:
    #         error_msg = f"Exception in add_liveness_selfie: {str(e)}"
    #         logger.error(error_msg, exc_info=True)
    #         return {"success": False, "error": error_msg, "is_live": False}
    
    # async def get_applicant_status(self, applicant_id: str) -> Dict[str, Any]:
    #     """
    #     Get applicant status including advanced face liveness verification result
    #     Returns face liveness check status (approved/rejected/pending)
    #     """
    #     try:
    #         path = f'/resources/applicants/{applicant_id}'
    #         headers = self._sign_request('GET', path)
            
    #         response = requests.get(
    #             f"{self.base_url}{path}",
    #             headers=headers,
    #             timeout=self.timeout
    #         )
            
    #         if response.status_code == 200:
    #             data = response.json()
                
    #             # Extract reviews including face liveness
    #             reviews = data.get('reviews', [])
    #             liveness_review = None
    #             for review in reviews:
    #                 if review.get('reviewType') == 'FACE_LIVELINESS':
    #                     liveness_review = review
    #                     break
                
    #             logger.info(f"✅ Applicant status retrieved")
    #             logger.info(f"   Applicant ID: {applicant_id}")
    #             logger.info(f"   Face liveness status: {liveness_review.get('reviewStatus') if liveness_review else 'pending'}")
                
    #             return {
    #                 "success": True,
    #                 "applicant_id": applicant_id,
    #                 "status": data.get('status'),
    #                 "reviews": reviews,
    #                 "liveness_review": liveness_review,
    #                 "message": "Applicant status retrieved successfully"
    #             }
    #         else:
    #             logger.error(f"Failed to get applicant status: {response.status_code} - {response.text}")
    #             return {
    #                 "success": False,
    #                 "error": f"Sumsub API Error: Status {response.status_code}",
    #                 "status_code": response.status_code
    #             }
    #     except Exception as e:
    #         logger.error(f"Exception in get_applicant_status: {str(e)}")
    #         return {"success": False, "error": str(e)}
    
    # async def complete_liveness_verification(
    #     self, 
    #     applicant_id: str
    # ) -> Dict[str, Any]:
    #     """
    #     BIO-010: Complete Liveness Enrollment
    #     Returns: "Liveness Enrolled Successfully"
    #     """
    #     try:
    #         # Get applicant status
    #         path = f'/resources/applicants/{applicant_id}'
    #         headers = self._sign_request('GET', path)
            
    #         response = requests.get(
    #             f"{self.base_url}{path}",
    #             headers=headers,
    #             timeout=self.timeout
    #         )
            
    #         if response.status_code == 200:
    #             data = response.json()
    #             logger.info("Liveness verification completed")
                
    #             # Return actual Sumsub response (no fake values)
    #             return {
    #                 "success": True,
    #                 "message": "Liveness Enrolled Successfully",
    #                 "status": "completed",
    #                 "sumsub_response": data,
    #                 "sumsub_headers": dict(response.headers)
    #             }
    #         else:
    #             logger.error(f"Failed to complete liveness: {response.text}")
    #             return {"success": False, "error": response.text}
    #     except Exception as e:
    #         logger.error(f"Exception in complete_liveness: {str(e)}")
    #         return {"success": False, "error": str(e)}
    
    # ==================== KYC FLOW (BIO-011 to BIO-015) ====================
    
    async def create_kyc_applicant(self, user_id: str) -> Dict[str, Any]:
        """
        BIO-011: Start KYC Verification
        Create applicant for KYC
        """
        try:
            external_user_id = f"kyc_{user_id}_{int(time.time())}"
            body = json.dumps({'externalUserId': external_user_id})
            path = f'/resources/applicants?levelName={self.level_name}'
            headers = self._sign_request('POST', path, body.encode('utf-8'))
            
            response = requests.post(
                f"{self.base_url}{path}",
                headers=headers,
                data=body,
                timeout=self.timeout
            )
            
            logger.info(f"Sumsub create applicant response status: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            logger.info(f"Response text: {response.text[:500]}")  # First 500 chars
            
            if response.status_code == 201:
                data = response.json()
                logger.info(f"KYC applicant created successfully")
                logger.info(f"Full response: {json.dumps(data, indent=2)}")
                logger.info(f"Sumsub applicant ID (data['id']): {data.get('id', 'NOT_FOUND')}")
                logger.info(f"ID type: {type(data.get('id'))}")
                logger.info(f"External user ID: {external_user_id}")
                
                if 'id' not in data:
                    logger.error("CRITICAL: Sumsub response missing 'id' field!")
                    return {"success": False, "error": "Sumsub response missing applicant ID"}
                
                return {
                    "success": True,
                    "kyc_session_id": data['id'],
                    "external_user_id": external_user_id,
                    "status": "initiated"
                }
            else:
                logger.error(f"Failed to create KYC applicant: {response.text}")
                return {"success": False, "error": response.text}
        except Exception as e:
            logger.error(f"Exception in create_kyc_applicant: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def scan_document_front(
        self, 
        applicant_id: str,
        document_image_bytes: bytes,
        doc_type: str = "PASSPORT",
        country: str = "DEU"
    ) -> Dict[str, Any]:
        """
        BIO-012: Scan ID - Front
        Add document front side
        
        FIX: Sign with ACTUAL multipart body (not empty) following Sumsub official pattern
        The signature must match the exact bytes being sent, including boundary markers
        """
        try:
            # PASSPORT is single-sided, no idDocSubType needed
            # ID_CARD, DRIVERS, etc. need FRONT_SIDE/BACK_SIDE
            if doc_type == "PASSPORT":
                metadata = json.dumps({
                    "idDocType": doc_type,
                    "country": country
                })
            else:
                metadata = json.dumps({
                    "idDocType": doc_type,
                    "country": country,
                    "idDocSubType": "FRONT_SIDE"
                })
            
            path = f'/resources/applicants/{applicant_id}/info/idDoc'
            full_url = f"{self.base_url}{path}"
            
            logger.info(f"Document Upload - {'PASSPORT (single-sided)' if doc_type == 'PASSPORT' else 'Front Side'}")
            logger.info(f"  Applicant ID: {applicant_id[:10]}...")
            logger.info(f"  Path: {path}")
            logger.info(f"  Document size: {len(document_image_bytes)} bytes")
            logger.info(f"  Document type: {doc_type}")
            logger.info(f"  Country: {country}")
            
            # Step 1: Prepare multipart request to get ACTUAL body with boundary
            files = {'content': ('front.jpg', BytesIO(document_image_bytes), 'image/jpeg')}
            data = {'metadata': metadata}
            
            req = requests.Request('POST', full_url, files=files, data=data)
            prepared = req.prepare()
            
            # Step 2: Sign using ACTUAL prepared body (with boundary)
            now = int(time.time())
            
            # Extract path_url with query params if any
            path_url = prepared.path_url
            
            data_to_sign = (
                str(now).encode('utf-8') +
                b'POST' +
                path_url.encode('utf-8') +
                prepared.body  # ← THIS is the KEY! actual multipart bytes
            )
            
            signature = hmac.new(
                self.secret_key.encode('utf-8'),
                data_to_sign,
                digestmod=hashlib.sha256
            ).hexdigest()
            
            logger.info(f"  Timestamp: {now}")
            logger.info(f"  Multipart body size: {len(prepared.body)} bytes")
            logger.debug(f"  Signature prefix: {signature[:8]}...")
            logger.debug(f"  Content-Type prefix: {prepared.headers.get('Content-Type', 'MISSING')[:30]}...")
            
            # Step 3: Build headers with signature
            headers = {
                'X-App-Token': self.app_token,
                'X-App-Access-Ts': str(now),
                'X-App-Access-Sig': signature,
                'Accept': 'application/json',
                'X-Return-Doc-Warnings': 'true',
            }
            
            # Step 4: Copy Content-Type from prepared (includes boundary)
            if 'Content-Type' in prepared.headers:
                headers['Content-Type'] = prepared.headers['Content-Type']
            
            # Step 5: Send using Session with prepared request
            session = requests.Session()
            prepared.headers.update(headers)
            
            response = session.send(prepared, timeout=self.timeout)
            
            logger.info(f"Response Status: {response.status_code}")
            
            if response.status_code not in [200, 201]:
                logger.error(f"Upload failed with status {response.status_code}")
                
                if response.status_code == 401:
                    logger.error("401 AUTHENTICATION FAILED")
                    logger.error("   - Verify SUMSUB_SECRET_KEY and SUMSUB_APP_TOKEN in .env")
                    logger.error("   - Check system clock sync")
                elif response.status_code == 404:
                    logger.error("404 NOT FOUND - Applicant may not exist")
            
            if response.status_code in [200, 201]:
                image_id = response.headers.get('X-Image-Id', '')
                logger.info(f" Document front uploaded successfully: {image_id}")
                
                # Return actual Sumsub response data (no fake values)
                response_data = response.json() if response.text else {}
                return {
                    "success": True,
                    "image_id": image_id,
                    "document_type": doc_type,
                    "sumsub_response": response_data,
                    "sumsub_headers": dict(response.headers)
                }
            else:
                error_msg = f"Sumsub API Error: Status {response.status_code}"
                try:
                    error_data = response.json()
                    if 'description' in error_data:
                        error_msg += f" - {error_data['description'][:100]}"  # Limit length
                    if 'errorCode' in error_data:
                        error_msg += f" (Code: {error_data['errorCode']})"
                except:
                    error_msg += " - Invalid response format"
                
                logger.error(f"Failed to scan document front: Status {response.status_code}")
                return {
                    "success": False,
                    "error": "Document upload failed",  # Generic error for client
                    "document_detected": False,
                    "status_code": response.status_code
                }
        except Exception as e:
            logger.error(f"Exception in scan_document_front: {type(e).__name__}")
            logger.debug(f"Exception details: {str(e)}", exc_info=True)  # Full error only in debug
            return {"success": False, "error": "Document upload failed", "document_detected": False}
    
    async def scan_document_back(
        self, 
        applicant_id: str,
        document_image_bytes: bytes,
        doc_type: str = "PASSPORT",
        country: str = "DEU"
    ) -> Dict[str, Any]:
        """
        BIO-012: Scan ID - Back (OPTIONAL for PASSPORT)
        Add document back side
        
        - PASSPORT: Back is optional (some countries have 2-sided passports)
        - ID_CARD/DRIVERS: Back is typically required
        
        FIX: Sign with ACTUAL multipart body (not empty) following Sumsub official pattern
        """
        try:
            # PASSPORT back is added as additional document (no BACK_SIDE subtype)
            # ID_CARD, DRIVERS need BACK_SIDE to match with FRONT_SIDE
            if doc_type == "PASSPORT":
                metadata = json.dumps({
                    "idDocType": doc_type,
                    "country": country
                })
            else:
                metadata = json.dumps({
                    "idDocType": doc_type,
                    "country": country,
                    "idDocSubType": "BACK_SIDE"
                })
            
            path = f'/resources/applicants/{applicant_id}/info/idDoc'
            full_url = f"{self.base_url}{path}"
            
            logger.info(f"Document Upload - Back Side {'(optional for PASSPORT)' if doc_type == 'PASSPORT' else ''}")
            logger.info(f"  Applicant ID: {applicant_id[:10]}...")
            logger.info(f"  Path: {path}")
            logger.info(f"  Document size: {len(document_image_bytes)} bytes")
            logger.info(f"  Document type: {doc_type}")
            logger.info(f"  Country: {country}")
            
            # Step 1: Prepare multipart request to get ACTUAL body with boundary
            files = {'content': ('back.jpg', BytesIO(document_image_bytes), 'image/jpeg')}
            data = {'metadata': metadata}
            
            req = requests.Request('POST', full_url, files=files, data=data)
            prepared = req.prepare()
            
            # Step 2: Sign using ACTUAL prepared body (with boundary)
            now = int(time.time())
            path_url = prepared.path_url
            
            data_to_sign = (
                str(now).encode('utf-8') +
                b'POST' +
                path_url.encode('utf-8') +
                prepared.body  # ← ACTUAL multipart bytes
            )
            
            signature = hmac.new(
                self.secret_key.encode('utf-8'),
                data_to_sign,
                digestmod=hashlib.sha256
            ).hexdigest()
            
            logger.info(f"  Timestamp: {now}")
            logger.info(f"  Multipart body size: {len(prepared.body)} bytes")
            logger.debug(f"  Signature prefix: {signature[:8]}...")
            
            # Step 3: Build headers with signature
            headers = {
                'X-App-Token': self.app_token,
                'X-App-Access-Ts': str(now),
                'X-App-Access-Sig': signature,
                'Accept': 'application/json',
                'X-Return-Doc-Warnings': 'true',
            }
            
            # Step 4: Copy Content-Type from prepared (includes boundary)
            if 'Content-Type' in prepared.headers:
                headers['Content-Type'] = prepared.headers['Content-Type']
            
            # Step 5: Send using Session with prepared request
            session = requests.Session()
            prepared.headers.update(headers)
            
            response = session.send(prepared, timeout=self.timeout)
            
            logger.info(f"Response Status: {response.status_code}")
            
            if response.status_code not in [200, 201]:
                logger.error(f"Response Headers: {dict(response.headers)}")
                logger.error(f"Response Body: {response.text}")
            
            if response.status_code in [200, 201]:
                image_id = response.headers.get('X-Image-Id', '')
                logger.info(f"Document back uploaded successfully: {image_id}")
                
                # Return actual Sumsub response data (no fake values)
                response_data = response.json() if response.text else {}
                return {
                    "success": True,
                    "image_id": image_id,
                    "sumsub_response": response_data,
                    "sumsub_headers": dict(response.headers)
                }
            else:
                error_msg = f"Sumsub API Error: Status {response.status_code}"
                try:
                    error_data = response.json()
                    if 'description' in error_data:
                        error_msg += f" - {error_data['description'][:100]}"  # Limit length
                    if 'errorCode' in error_data:
                        error_msg += f" (Code: {error_data['errorCode']})"
                except:
                    error_msg += " - Invalid response format"
                
                logger.error(f"Failed to scan document back: Status {response.status_code}")
                return {
                    "success": False,
                    "error": "Document upload failed",  # Generic error for client
                    "document_detected": False,
                    "status_code": response.status_code
                }
        except Exception as e:
            logger.error(f"Exception in scan_document_back: {type(e).__name__}")
            logger.debug(f"Exception details: {str(e)}", exc_info=True)  # Full error only in debug
            return {"success": False, "error": "Document upload failed", "document_detected": False}
    
    async def verify_kyc_selfie(
        self,
        applicant_id: str,
        selfie_image_bytes: bytes
    ) -> Dict[str, Any]:
        """
        BIO-013: Take a Selfie
        Add selfie and match with document
        
        FIX: Sign with ACTUAL multipart body (not empty) following Sumsub official pattern
        Uses same endpoint as document upload with idDocType: SELFIE
        """
        try:
            # Metadata for SELFIE type (mandatory)
            metadata = json.dumps({
                "idDocType": "SELFIE",
                "country": "DEU"  # Optional but recommended
            })
            
            path = f'/resources/applicants/{applicant_id}/info/idDoc'
            full_url = f"{self.base_url}{path}"
            
            logger.info(f"Selfie Upload for KYC")
            logger.info(f"  Applicant ID: {applicant_id[:10]}...")
            logger.info(f"  Path: {path}")
            logger.info(f"  Selfie size: {len(selfie_image_bytes)} bytes")
            
            # Step 1: Prepare multipart request to get ACTUAL body with boundary
            files = {'content': ('selfie.jpg', BytesIO(selfie_image_bytes), 'image/jpeg')}
            data = {'metadata': metadata}
            
            req = requests.Request('POST', full_url, files=files, data=data)
            prepared = req.prepare()
            
            # Step 2: Sign using ACTUAL prepared body (with boundary)
            now = int(time.time())
            path_url = prepared.path_url
            
            data_to_sign = (
                str(now).encode('utf-8') +
                b'POST' +
                path_url.encode('utf-8') +
                prepared.body  # ACTUAL multipart bytes including boundary
            )
            
            signature = hmac.new(
                self.secret_key.encode('utf-8'),
                data_to_sign,
                digestmod=hashlib.sha256
            ).hexdigest()
            
            logger.info(f"  Timestamp: {now}")
            logger.info(f"  Multipart body size: {len(prepared.body)} bytes")
            logger.debug(f"  Signature prefix: {signature[:8]}...")
            
            # Step 3: Build headers with signature
            headers = {
                'X-App-Token': self.app_token,
                'X-App-Access-Ts': str(now),
                'X-App-Access-Sig': signature,
                'Accept': 'application/json',
                'X-Return-Doc-Warnings': 'true',
            }
            
            # Step 4: Copy Content-Type from prepared (includes boundary)
            if 'Content-Type' in prepared.headers:
                headers['Content-Type'] = prepared.headers['Content-Type']
            
            # Step 5: Send using Session with prepared request
            session = requests.Session()
            prepared.headers.update(headers)
            
            response = session.send(prepared, timeout=self.timeout)
            
            logger.info(f"Response Status: {response.status_code}")
            
            if response.status_code not in [200, 201]:
                logger.error(f"Response Headers: {dict(response.headers)}")
                logger.error(f"Response Body: {response.text}")
                
                if response.status_code == 401:
                    logger.error("401 SIGNATURE MISMATCH")
                    logger.error(f"   - Verify SUMSUB_SECRET_KEY in .env")
                    logger.error(f"   - Check system clock sync: w32tm /resync")
                elif response.status_code == 404:
                    logger.error("404 NOT FOUND - Check applicant_id exists")
            
            if response.status_code in [200, 201]:
                # Return actual Sumsub response data (no fake values)
                response_data = response.json() if response.text else {}
                image_id = response.headers.get('X-Image-Id', '') or response_data.get('id', '')
                logger.info(f"KYC selfie added successfully: {image_id}")
                return {
                    "success": True,
                    "image_id": image_id,
                    "sumsub_response": response_data,
                    "sumsub_headers": dict(response.headers)
                }
            else:
                error_msg = f"Sumsub API Error: Status {response.status_code}"
                try:
                    error_data = response.json()
                    if 'description' in error_data:
                        error_msg += f" - {error_data['description']}"
                    if 'errorCode' in error_data:
                        error_msg += f" (Code: {error_data['errorCode']})"
                except:
                    error_msg += f" - {response.text}"
                
                logger.error(f"Failed to add KYC selfie: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "matches_document": False,
                    "status_code": response.status_code
                }
        except Exception as e:
            error_msg = f"Exception in verify_kyc_selfie: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"success": False, "error": error_msg, "matches_document": False}
    
    async def check_kyc_status(self, applicant_id: str) -> Dict[str, Any]:
        """
        BIO-014: Verification in Progress
        Check verification status from Sumsub review
        """
        try:
            path = f'/resources/applicants/{applicant_id}'
            headers = self._sign_request('GET', path)
            
            response = requests.get(
                f"{self.base_url}{path}",
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Handle list response format (Sumsub returns list with items)
                if 'list' in data and 'items' in data['list'] and len(data['list']['items']) > 0:
                    applicant_data = data['list']['items'][0]
                else:
                    applicant_data = data
                
                # Extract review data (nested in 'review' key)
                review = applicant_data.get('review', {})
                review_status = review.get('reviewStatus', 'init')  # init, pending, completed, onHold, awaitingService, awaitingUser
                review_result = review.get('reviewResult', {})
                review_answer = review_result.get('reviewAnswer', 'PENDING')  # GREEN, RED, YELLOW
                review_reject_type = review_result.get('reviewRejectType', None)  # RETRY or FINAL
                
                # Map Sumsub status to our status - all 8 cases from KYC table
                if review_status == 'init':
                    status = 'init'  # Documents requested / Init
                elif review_answer == 'GREEN' and review_status == 'completed':
                    status = 'approved'  # Approved
                elif review_answer == 'GREEN' and review_status == 'awaitingService':
                    status = 'awaiting_service'  # Awaiting service checks
                elif review_answer == 'GREEN' and review_status == 'awaitingUser':
                    status = 'awaiting_user'  # Awaiting user action (e.g. UBO)
                elif review_answer == 'RED' and review_status == 'completed':
                    # Resubmission requested vs Rejected (permanent)
                    if review_reject_type == 'RETRY':
                        status = 'resubmission_requested'  # Failed but can retry
                    elif review_reject_type == 'FINAL':
                        status = 'rejected'  # Permanently rejected
                    else:
                        status = 'rejected'  # Default to permanent if type unknown
                elif review_status == 'onHold':
                    status = 'on_hold'  # Under manual review / requires action
                elif review_status == 'pending':
                    status = 'processing'  # Pending review
                elif review_status == 'completed' and review_answer == 'YELLOW':
                    status = 'pending_review'  # Ambiguous - treat as processing
                else:
                    status = 'processing'  # Default fallback
                
                logger.info(f"KYC status checked: reviewStatus={review_status}, reviewAnswer={review_answer}, mapped={status}")
                
                return {
                    "success": True,
                    "status": status,
                    "review_status": review_status,
                    "review_answer": review_answer,
                    "checks": {
                        "validating_documents": review_status in ['init', 'pending'],
                        "verifying_identity": review_status == 'pending',
                        "running_security_checks": review_status == 'pending'
                    },
                    "progress": 100 if status == 'approved' else 75 if status == 'processing' else 50,
                    "full_response": data  # Include full Sumsub response for debugging
                }
            else:
                logger.error(f"Failed to check status: {response.text}")
                return {"success": False, "error": response.text}
        except Exception as e:
            logger.error(f"Exception in check_kyc_status: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def complete_kyc_verification(self, applicant_id: str) -> Dict[str, Any]:
        """
        BIO-015: KYC Approved
        Complete KYC verification
        """
        try:
            path = f'/resources/applicants/{applicant_id}'
            headers = self._sign_request('GET', path)
            
            response = requests.get(
                f"{self.base_url}{path}",
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info("KYC verification completed")
                return {
                    "success": True,
                    "message": "KYC Approved",
                    "status": "approved",
                    "verification_status": "Verified",
                    "kyc_id": data.get('id', applicant_id)
                }
            else:
                logger.error(f"Failed to complete KYC: {response.text}")
                return {"success": False, "error": response.text}
        except Exception as e:
            logger.error(f"Exception in complete_kyc: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_access_token(self, external_user_id: str) -> Dict[str, Any]:
        """
        Generate SDK access token
        """
        try:
            body = json.dumps({
                'userId': external_user_id,
                'levelName': self.level_name
            })
            
            path = '/resources/accessTokens/sdk'
            headers = self._sign_request('POST', path, body.encode('utf-8'))
            
            response = requests.post(
                f"{self.base_url}{path}",
                headers=headers,
                data=body,
                timeout=self.timeout
            )
            
            if response.status_code == 201:
                data = response.json()
                token = data['token']
                logger.info("Access token generated")
                return {
                    "success": True,
                    "token": token
                }
            else:
                logger.error(f"Failed to generate token: {response.text}")
                return {"success": False, "error": response.text}
        except Exception as e:
            logger.error(f"Exception in get_access_token: {str(e)}")
            return {"success": False, "error": str(e)}