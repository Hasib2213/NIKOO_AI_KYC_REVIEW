# app/services/verification_service.py
"""
Verification Service following Design Flow:
BIO-008 to BIO-010: Liveness Detection
BIO-011 to BIO-015: KYC Verification
"""

from app.database.KYCdatabase import MongoDB
from app.services.sumsub_service import SumsubService
from app.models.schemas import VerificationStatus
from datetime import datetime
import logging
from typing import Optional, Union
import uuid
import base64

logger = logging.getLogger(__name__)

class VerificationService:
    """
    Main service following complete design flow
    """
    
    def __init__(self):
        self.sumsub = SumsubService()
       # self.liveness_sessions = MongoDB.get_collection("liveness_sessions")
        self.kyc_sessions = MongoDB.get_collection("kyc_sessions")
        self.users_collection = MongoDB.get_collection("users")
    
    # ==================== LIVENESS FLOW (BIO-008 to BIO-010) ====================
    
    # async def start_liveness_detection(self, user_id: str) -> dict:
    #     """BIO-008: Start Face Liveness Detection"""
    #     try:
    #         result = await self.sumsub.start_liveness_session(user_id)
            
    #         if result.get("success"):
    #             session_doc = {
    #                 "session_id": result["session_id"],
    #                 "user_id": user_id,
    #                 "external_user_id": result["external_user_id"],
    #                 "verification_type": "liveness",
    #                 "status": "initiated",
    #                 "created_at": datetime.utcnow(),
    #                 "updated_at": datetime.utcnow()
    #             }
    #             await self.liveness_sessions.insert_one(session_doc)
                
    #             return {
    #                 "success": True,
    #                 "session_id": result["session_id"],
    #                 "status": "initiated"
    #             }
            
    #         return result
    #     except Exception as e:
    #         logger.error(f"Start liveness error: {str(e)}")
    #         raise
    
    # async def process_liveness_selfie(
    #     self, 
    #     session_id: str,
    #     image_base64: str
    # ) -> dict:
    #     """BIO-009: Process Face Liveness Check (Look left, Blink, Look right)"""
    #     try:
    #         # Get session
    #         session = await self.liveness_sessions.find_one({"session_id": session_id})
    #         if not session:
    #             return {"success": False, "error": "Session not found"}
            
    #         applicant_id = session["session_id"]
            
    #         # Decode base64 with proper padding
    #         try:
    #             missing_padding = len(image_base64) % 4
    #             if missing_padding:
    #                 image_base64 += '=' * (4 - missing_padding)
    #             image_bytes = base64.b64decode(image_base64)
    #         except Exception as decode_error:
    #             logger.error(f"Base64 decode error: {str(decode_error)}")
    #             return {"success": False, "error": f"Invalid base64 image: {str(decode_error)}"}
            
    #         result = await self.sumsub.add_liveness_selfie(applicant_id, image_bytes)
            
    #         if result.get("success"):
    #             await self.liveness_sessions.update_one(
    #                 {"session_id": session_id},
    #                 {"$set": {
    #                     "selfie_added": True,
    #                     "is_live": result.get("is_live"),
    #                     "confidence": result.get("confidence"),
    #                     "image_id": result.get("image_id"),
    #                     "status": "submitted_for_review",
    #                     "updated_at": datetime.utcnow()
    #                 }}
    #             )
    #             logger.info(f"Liveness selfie submitted. Status: {result.get('message', 'In progress')}")
    #         else:
    #             logger.error(f"Liveness selfie upload failed: {result.get('error', 'Unknown error')}")
            
    #         return result
    #     except Exception as e:
    #         logger.error(f"Process liveness error: {str(e)}")
    #         raise
    
    # async def complete_liveness_enrollment(
    #     self,
    #     session_id: str,
    #     user_id: str
    # ) -> dict:
    #     """BIO-010: Complete Liveness Enrollment → 'Liveness Enrolled Successfully'"""
    #     try:
    #         session = await self.liveness_sessions.find_one({"session_id": session_id})
    #         if not session:
    #             return {"success": False, "error": "Session not found"}
            
    #         applicant_id = session["session_id"]
    #         result = await self.sumsub.complete_liveness_verification(applicant_id)
            
    #         if result.get("success"):
    #             await self.liveness_sessions.update_one(
    #                 {"session_id": session_id},
    #                 {"$set": {
    #                     "status": "completed",
    #                     "is_live": True,
    #                     "updated_at": datetime.utcnow()
    #                 }}
    #             )
                
    #             # Update user
    #             await self.users_collection.update_one(
    #                 {"user_id": user_id},
    #                 {"$set": {
    #                     "liveness_completed": True,
    #                     "liveness_session_id": session_id,
    #                     "updated_at": datetime.utcnow()
    #                 }},
    #                 upsert=True
    #             )
            
    #         return result
    #     except Exception as e:
    #         logger.error(f"Complete liveness error: {str(e)}")
    #         raise
    
    # async def check_liveness_status(self, session_id: str) -> dict:
    #     """
    #     Check advanced liveness verification status from Sumsub
    #     Retrieves face liveness analysis results (advanced/active liveness)
    #     """
    #     try:
    #         session = await self.liveness_sessions.find_one({"session_id": session_id})
    #         if not session:
    #             return {"success": False, "error": "Session not found"}
            
    #         applicant_id = session["session_id"]
            
    #         # Get applicant status from Sumsub (includes face liveness result)
    #         result = await self.sumsub.get_applicant_status(applicant_id)
            
    #         if result.get("success"):
    #             status_data = result.get("status", {})
                
    #             # Extract face liveness check result
    #             reviews = result.get("reviews", [])
    #             liveness_result = None
    #             for review in reviews:
    #                 if review.get("reviewType") == "FACE_LIVELINESS":
    #                     liveness_result = review
    #                     break
                
    #             review_status = liveness_result.get("reviewStatus") if liveness_result else "pending"
                
    #             # Update session with latest result
    #             await self.liveness_sessions.update_one(
    #                 {"session_id": session_id},
    #                 {"$set": {
    #                     "review_status": review_status,
    #                     "liveness_result": liveness_result,
    #                     "is_live": review_status == "approved",
    #                     "updated_at": datetime.utcnow()
    #                 }}
    #             )
                
    #             return {
    #                 "success": True,
    #                 "session_id": session_id,
    #                 "status": review_status,
    #                 "is_live": review_status == "approved",
    #                 "liveness_result": liveness_result,
    #                 "message": f"Face liveness check: {review_status}"
    #             }
            
    #         return result
    #     except Exception as e:
    #         logger.error(f"Check liveness status error: {str(e)}")
    #         raise
    
    # ==================== KYC FLOW (BIO-011 to BIO-015) ====================
    
    async def start_kyc_verification(self, user_id: str) -> dict:
        """BIO-011: Start KYC Verification"""
        try:
            logger.info(f"Starting KYC verification for user_id: {user_id}")
            result = await self.sumsub.create_kyc_applicant(user_id)
            logger.info(f"Sumsub result: {result}")
            
            if result.get("success"):
                kyc_session_id_from_sumsub = result["kyc_session_id"]
                logger.info(f" Sumsub applicant created successfully")
                logger.info(f"   Sumsub applicant ID: {kyc_session_id_from_sumsub}")
                logger.info(f"   IMPORTANT: Use this ID for all future requests: {kyc_session_id_from_sumsub}")
                
                session_doc = {
                    "kyc_session_id": kyc_session_id_from_sumsub,
                    "user_id": user_id,
                    "external_user_id": result["external_user_id"],
                    "verification_type": "kyc",
                    "status": "initiated",
                    "steps_completed": [],
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                await self.kyc_sessions.insert_one(session_doc)
                logger.info(f"Session stored in MongoDB")
                
                return {
                    "success": True,
                    "kyc_session_id": kyc_session_id_from_sumsub,
                    "status": "initiated"
                }
            
            return result
        except Exception as e:
            logger.error(f"Start KYC error: {str(e)}")
            raise
    
    async def scan_document_front(
        self,
        kyc_session_id: str,
        image: Union[bytes, bytearray, str],
        doc_type: str = "PASSPORT",
        country: str = "USA"
    ) -> dict:
        """BIO-012: Scan ID - Front (accepts bytes or base64)"""
        try:
            session = await self.kyc_sessions.find_one({"kyc_session_id": kyc_session_id})
            if not session:
                return {"success": False, "error": "KYC session not found"}

            # Normalize payload to bytes
            try:
                if isinstance(image, str):
                    missing_padding = len(image) % 4
                    if missing_padding:
                        image += "=" * (4 - missing_padding)
                    image_bytes = base64.b64decode(image)
                elif isinstance(image, (bytes, bytearray)):
                    image_bytes = bytes(image)
                else:
                    return {"success": False, "error": "Invalid image payload"}
            except Exception as decode_error:
                logger.error(f"Base64 decode error: {str(decode_error)}")
                return {"success": False, "error": f"Invalid image data: {str(decode_error)}"}

            # Use kyc_session_id as applicant_id (Sumsub-assigned ID from data['id'])
            applicant_id = kyc_session_id
            result = await self.sumsub.scan_document_front(
                applicant_id,
                image_bytes,
                doc_type,
                country
            )

            if result.get("success"):
                await self.kyc_sessions.update_one(
                    {"kyc_session_id": kyc_session_id},
                    {"$set": {
                        "document_front_added": True,
                        "document_type": doc_type,
                        "country": country,
                        "updated_at": datetime.utcnow()
                    },
                    "$push": {"steps_completed": "document_front"}}
                )

            return result
        except Exception as e:
            logger.error(f"Scan document front error: {str(e)}", exc_info=True)
            raise
    
    
    async def verify_kyc_selfie(
        self,
        kyc_session_id: str,
        image: Union[bytes, bytearray, str]
    ) -> dict:
        """BIO-013: Take a Selfie and match with document"""
        try:
            session = await self.kyc_sessions.find_one({"kyc_session_id": kyc_session_id})
            if not session:
                logger.error(f"KYC session not found for kyc_session_id: {kyc_session_id}")
                return {"success": False, "error": "KYC session not found"}
            
            logger.info(f"KYC session found: {session}")
            logger.info(f"Session keys: {session.keys()}")
            logger.info(f"kyc_session_id from request: {kyc_session_id}")
            logger.info(f"kyc_session_id in DB: {session.get('kyc_session_id')}")
            
            # The applicant_id parameter passed to us IS the Sumsub applicant ID
            # Use it directly (the kyc_session_id from request is what Sumsub returned)
            applicant_id = kyc_session_id
            logger.info(f"Using applicant_id (Sumsub ID): {applicant_id}")

            try:
                if isinstance(image, str):
                    missing_padding = len(image) % 4
                    if missing_padding:
                        image += '=' * (4 - missing_padding)
                    image_bytes = base64.b64decode(image)
                elif isinstance(image, (bytes, bytearray)):
                    image_bytes = bytes(image)
                else:
                    return {"success": False, "error": "Invalid image payload"}
            except Exception as decode_error:
                logger.error(f"Base64 decode error: {str(decode_error)}")
                return {"success": False, "error": f"Invalid image data: {str(decode_error)}"}

            logger.info(f"Calling sumsub.verify_kyc_selfie with applicant_id: {applicant_id}, image size: {len(image_bytes)}")
            result = await self.sumsub.verify_kyc_selfie(applicant_id, image_bytes)
            logger.info(f"Sumsub result: {result}")
            
            if result.get("success"):
                await self.kyc_sessions.update_one(
                    {"kyc_session_id": kyc_session_id},
                    {"$set": {
                        "selfie_added": True,
                        "matches_document": result.get("matches_document"),
                        "face_match_score": result.get("face_match_score"),
                        "updated_at": datetime.utcnow()
                    },
                    "$push": {"steps_completed": "selfie"}}
                )
            
            return result
        except Exception as e:
            logger.error(f"Verify selfie error: {str(e)}")
            raise
    
    async def check_kyc_verification_status(self, kyc_session_id: str) -> dict:
        """BIO-014: Verification in Progress - Check status and persist to DB"""
        try:
            session = await self.kyc_sessions.find_one({"kyc_session_id": kyc_session_id})
            if not session:
                logger.warning(f"KYC session NOT FOUND in DB: {kyc_session_id[:10]}...")
                # Check if ANY session exists for debugging
                all_sessions = await self.kyc_sessions.find({}).to_list(5)
                logger.warning(f"Total sessions in DB: {await self.kyc_sessions.count_documents({})}")
                logger.warning(f"Sample sessions: {[s.get('kyc_session_id')[:10] for s in all_sessions]}")
                return {"success": False, "error": "KYC session not found"}
            
            # Get latest status from Sumsub
            result = await self.sumsub.check_kyc_status(kyc_session_id)
            
            if not result.get("success"):
                logger.warning(f"Sumsub check_kyc_status failed: {result.get('error')}")
                return result
            
            # Extract normalized status from result
            normalized_status = result.get("status", "pending")  # approved, rejected, processing, pending, pending_review
            review_status = result.get("review_status", "init")
            review_answer = result.get("review_answer", "PENDING")
            
            # Map normalized status to session status
            session_status_map = {
                "approved": "verified",
                "rejected": "failed",
                "processing": "in_progress",
                "pending": "in_progress",
                "pending_review": "in_progress",
                "init": "in_progress",
                "awaiting_service": "in_progress",
                "awaiting_user": "in_progress",
                "on_hold": "in_progress",
                "resubmission_requested": "in_progress"
            }
            session_status = session_status_map.get(normalized_status, "in_progress")
            is_verified = normalized_status == "approved"
            
            # Persist to database
            await self.kyc_sessions.update_one(
                {"kyc_session_id": kyc_session_id},
                {"$set": {
                    "status": session_status,
                    "verified": is_verified,
                    "review_status": review_status,
                    "review_answer": review_answer,
                    "sumsub_normalized_status": normalized_status,
                    "last_status_check": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }}
            )
            
            # Update user collection with latest status
            user_id = session.get("user_id")
            if user_id:
                await self.users_collection.update_one(
                    {"user_id": user_id},
                    {"$set": {
                        "kyc_status": normalized_status,
                        "kyc_verified": is_verified,
                        "kyc_review_status": review_status,
                        "kyc_review_answer": review_answer,
                        "kyc_session_id": kyc_session_id,
                        "updated_at": datetime.utcnow()
                    }},
                    upsert=True
                )
            
            logger.info(f"KYC status persisted: {kyc_session_id[:10]}... -> {normalized_status}")
            
            # Return response with normalized status + raw payload
            return {
                "success": True,
                "status": normalized_status,  # Normalized: approved, rejected, pending, processing, pending_review, on_hold
                "review_status": review_status,  # Sumsub status: init, pending, completed, onHold
                "review_answer": review_answer,  # GREEN, RED, YELLOW, PENDING
                "verified": is_verified,
                "sumsub_data": result  # Full Sumsub response for debugging
            }
        except Exception as e:
            logger.error(f"Check KYC status error: {type(e).__name__}")
            logger.debug(f"Error details: {str(e)}", exc_info=True)
            raise
    
    async def complete_kyc_verification(self, kyc_session_id: str, user_id: str) -> dict:
        """BIO-015: KYC Approved - Complete verification"""
        try:
            session = await self.kyc_sessions.find_one({"kyc_session_id": kyc_session_id})
            if not session:
                return {"success": False, "error": "KYC session not found"}
            
            # Use kyc_session_id as applicant_id (Sumsub-assigned ID from data['id'])
            applicant_id = kyc_session_id
            result = await self.sumsub.complete_kyc_verification(applicant_id)
            
            if result.get("success"):
                await self.kyc_sessions.update_one(
                    {"kyc_session_id": kyc_session_id},
                    {"$set": {
                        "status": "completed",
                        "verified": True,
                        "updated_at": datetime.utcnow()
                    },
                    "$push": {"steps_completed": "kyc_complete"}}
                )
                
                # Update user
                await self.users_collection.update_one(
                    {"user_id": user_id},
                    {"$set": {
                        "kyc_completed": True,
                        "verified": True,
                        "kyc_session_id": kyc_session_id,
                        "updated_at": datetime.utcnow()
                    }},
                    upsert=True
                )
            
            return result
        except Exception as e:
            logger.error(f"Complete KYC error: {str(e)}")
            raise
    
    async def scan_document_back(
        self,
        kyc_session_id: str,
        image: Union[bytes, bytearray, str],
        doc_type: str = "PASSPORT",
        country: str = "USA"
    ) -> dict:
        """BIO-012: Scan ID - Back (accepts bytes or base64)"""
        try:
            session = await self.kyc_sessions.find_one({"kyc_session_id": kyc_session_id})
            if not session:
                return {"success": False, "error": "KYC session not found"}

            try:
                if isinstance(image, str):
                    missing_padding = len(image) % 4
                    if missing_padding:
                        image += "=" * (4 - missing_padding)
                    image_bytes = base64.b64decode(image)
                elif isinstance(image, (bytes, bytearray)):
                    image_bytes = bytes(image)
                else:
                    return {"success": False, "error": "Invalid image payload"}
            except Exception as decode_error:
                logger.error(f"Base64 decode error: {str(decode_error)}")
                return {"success": False, "error": f"Invalid image data: {str(decode_error)}"}

            # Use kyc_session_id as applicant_id (Sumsub-assigned ID from data['id'])
            applicant_id = kyc_session_id
            result = await self.sumsub.scan_document_back(
                applicant_id,
                image_bytes,
                doc_type,
                country
            )

            if result.get("success"):
                await self.kyc_sessions.update_one(
                    {"kyc_session_id": kyc_session_id},
                    {"$set": {
                        "document_back_added": True,
                        "document_type": doc_type,
                        "country": country,
                        "updated_at": datetime.utcnow()
                    },
                    "$push": {"steps_completed": "document_back"}}
                )

            return result
        except Exception as e:
            logger.error(f"Scan document back error: {str(e)}")
            raise
    
    async def get_user_verification_status(self, user_id: str) -> dict:
        """Get overall verification status from database - actual Sumsub status"""
        try:
            # Get latest user record
            user = await self.users_collection.find_one({"user_id": user_id})
            
            if not user:
                return {
                    "user_id": user_id,
                    "overall_status": "not_started",  # No KYC started yet
                    "verified": False,
                    "kyc": {
                        "status": "not_started",
                        "verified": False,
                        "kyc_status": None,
                        "review_status": None,
                        "review_answer": None,
                        "completed_at": None,
                        "message": None
                    }
                }
            
            # Get latest KYC session
            kyc_session = await self.kyc_sessions.find_one(
                {"user_id": user_id},
                sort=[("created_at", -1)]
            )
            
            # Get ACTUAL Sumsub status from database (set by status check)
            kyc_status = user.get("kyc_status", "not_started")  # approved, rejected, pending, processing, on_hold, not_started
            kyc_verified = user.get("kyc_verified", False)
            
            # overall_status = Sumsub from actual status
            overall_status = kyc_status if kyc_status else "not_started"
            
            return {
                "user_id": user_id,
                "overall_status": overall_status,  # ← ACTUAL Sumsub status: approved/rejected/pending/processing/on_hold
                "verified": kyc_verified,
                "kyc": {
                    "status": overall_status,  # Same as overall_status - Sumsub normalized status
                    "verified": kyc_verified,
                    "kyc_status": kyc_status,  # Raw Sumsub normalized status
                    "review_status": user.get("kyc_review_status"),  # init, pending, completed, onHold
                    "review_answer": user.get("kyc_review_answer"),  # GREEN, RED, YELLOW, PENDING
                    "session_id": kyc_session.get("kyc_session_id") if kyc_session else user.get("kyc_session_id"),
                    "completed_at": user.get("updated_at"),
                    "message": self._get_status_message(overall_status, kyc_verified)
                }
            }
        except Exception as e:
            logger.error(f"Get user verification status error: {type(e).__name__}")
            logger.debug(f"Error details: {str(e)}", exc_info=True)
            raise
    
    def _get_status_message(self, status: str, verified: bool) -> str:
        """Get user-friendly message based on status - maps to UI messages from KYC table"""
        messages = {
    "init": "Start your KYC now ,please upload the required documents",
    "processing": "Your documents are being verified... Please wait",
    "pending": "Your documents are being verified... Please wait",
    "awaiting_service": "Verification in progress , waiting for additional external checks",
    "on_hold": "There is an issue with your KYC ,our team is reviewing it",
    "awaiting_user": "Additional information/action required ,please complete it",
    "approved": "Your KYC has been successfully completed!",
    "resubmission_requested": "Verification failed ,please upload better quality documents again",
    "rejected": "Sorry, your KYC has been rejected",
    "pending_review": "Your documents are being verified... Please wait"
}
        return messages.get(status, "Verification pending")
    
    # ==================== WEBHOOK HANDLERS ====================
    
    # async def update_liveness_webhook_result(
    #     self,
    #     external_user_id: str,
    #     applicant_id: str,
    #     review_status: str,
    #     webhook_data: dict
    # ) -> dict:
    #     """Handle webhook response from SumSub for liveness verification"""
    #     try:
    #         # Find session by external_user_id
    #         session = await self.liveness_sessions.find_one(
    #             {"external_user_id": external_user_id}
    #         )
            
    #         if not session:
    #             logger.warning(f"Liveness session not found for {external_user_id}")
                
    #             # Try fallback: search by session_id (applicant_id)
    #             session = await self.liveness_sessions.find_one(
    #                 {"session_id": applicant_id}
    #             )
                
    #             if session:
    #                 logger.info(f"✅ Found liveness session by applicant_id fallback: {applicant_id}")
    #             else:
    #                 # Log all available sessions for debugging
    #                 all_sessions = await self.liveness_sessions.find({}).to_list(None)
    #                 logger.warning(f"Available liveness sessions in DB: {len(all_sessions)}")
    #                 for s in all_sessions[:5]:  # Log first 5
    #                     logger.warning(f"  - Session external_user_id: {s.get('external_user_id')}, status: {s.get('status')}")
    #                 logger.error(f"Liveness session not found by external_user_id ({external_user_id}) or session_id ({applicant_id})")
    #                 return {"success": False, "error": "Session not found"}
            
    #         # Update session based on review status
    #         status_map = {
    #             "approved": "completed",
    #             "rejected": "failed",
    #             "pending": "pending"
    #         }
            
    #         session_status = status_map.get(review_status, "pending")
    #         is_live = review_status == "approved"
            
    #         await self.liveness_sessions.update_one(
    #             {"_id": session["_id"]},
    #             {"$set": {
    #                 "status": session_status,
    #                 "is_live": is_live,
    #                 "review_status": review_status,
    #                 "webhook_data": webhook_data,
    #                 "updated_at": datetime.utcnow()
    #             }}
    #         )
            
    #         # Update user
    #         user_id = session.get("user_id")
    #         if user_id:
    #             await self.users_collection.update_one(
    #                 {"user_id": user_id},
    #                 {"$set": {
    #                     "liveness_completed": session_status == "completed",
    #                     "liveness_verified": is_live,
    #                     "liveness_review_status": review_status,
    #                     "updated_at": datetime.utcnow()
    #                 }},
    #                 upsert=True
    #             )
            
    #         logger.info(f"Liveness webhook processed: {external_user_id} - {review_status}")
    #         return {
    #             "success": True,
    #             "message": f"Liveness verification {review_status}"
    #         }
            
    #     except Exception as e:
    #         logger.error(f"Liveness webhook error: {str(e)}")
    #         return {"success": False, "error": str(e)}
    
    async def update_kyc_webhook_result(
        self,
        external_user_id: str,
        applicant_id: str,
        review_status: str,
        webhook_data: dict
    ) -> dict:
        """Handle webhook response from SumSub for KYC verification"""
        try:
            # Find session by external_user_id (without the liveness prefix)
            session = await self.kyc_sessions.find_one(
                {"external_user_id": external_user_id}
            )
            
            if not session:
                # Log all available sessions for debugging
                logger.warning(f"KYC session not found for {external_user_id}")
                all_sessions = await self.kyc_sessions.find({}).to_list(None)
                logger.warning(f"Available KYC sessions in DB: {len(all_sessions)}")
                for s in all_sessions[:5]:  # Log first 5
                    logger.warning(f"  - Session external_user_id: {s.get('external_user_id')}, status: {s.get('status')}")
                
                # Try fallback: search by applicant_id (kyc_session_id)
                session = await self.kyc_sessions.find_one(
                    {"kyc_session_id": applicant_id}
                )
                
                if session:
                    logger.info(f" Found session by applicant_id fallback: {applicant_id}")
                else:
                    logger.error(f"KYC session not found by external_user_id ({external_user_id}) or applicant_id ({applicant_id})")
                    return {"success": False, "error": "KYC session not found"}
            
            # Extract review answer and reject type from webhook payload
            review_answer = webhook_data.get("reviewResult", {}).get("reviewAnswer", "PENDING")
            review_reject_type = webhook_data.get("reviewResult", {}).get("reviewRejectType", None)
            
            # Map review_answer + reject_type to session status
            if review_answer == "GREEN":
                session_status = "completed"
                is_verified = True
            elif review_answer == "RED" and review_reject_type == "FINAL":
                session_status = "failed"
                is_verified = False
            else:
                # PENDING, YELLOW, RED+RETRY, onHold, awaitingService, awaitingUser = pending
                session_status = "pending"
                is_verified = False
            
            await self.kyc_sessions.update_one(
                {"_id": session["_id"]},
                {"$set": {
                    "status": session_status,
                    "verified": is_verified,
                    "review_status": review_status,
                    "review_answer": review_answer,
                    "review_reject_type": review_reject_type,
                    "webhook_data": webhook_data,
                    "updated_at": datetime.utcnow()
                }}
            )
            
            # Update user
            user_id = session.get("user_id")
            if user_id:
                await self.users_collection.update_one(
                    {"user_id": user_id},
                    {"$set": {
                        "kyc_completed": session_status == "completed",
                        "verified": is_verified,
                        "kyc_review_status": review_status,
                        "kyc_review_answer": review_answer,
                        "kyc_review_reject_type": review_reject_type,
                        "updated_at": datetime.utcnow()
                    }},
                    upsert=True
                )
            
            logger.info(f"KYC webhook processed: {external_user_id} - {review_status}")
            return {
                "success": True,
                "message": f"KYC verification {review_status}"
            }
            
        except Exception as e:
            logger.error(f"KYC webhook error: {str(e)}")
            return {"success": False, "error": str(e)}