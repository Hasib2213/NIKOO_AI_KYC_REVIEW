import asyncio
import io
import logging
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from pydub import AudioSegment

from app.database.KYCdatabase import MongoDB
from config import settings

logger = logging.getLogger(__name__)

def normalize_audio(audio_bytes: bytes) -> bytes:
    """
    Normalizes audio to WAV, 16kHz, 16-bit, mono (required by Azure Speaker Recognition).
    """
    try:
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
        # Azure requirements: 16kHz, 16-bit, mono
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        
        buffer = io.BytesIO()
        audio.export(buffer, format="wav")
        return buffer.getvalue()
    except Exception as e:
        logger.error(f"Error normalizing audio: {str(e)}")
        # Fallback to original bytes if pydub fails
        return audio_bytes

class VoiceVerificationService:
    def __init__(self):
        self.voice_profiles = MongoDB.get_collection("voice_profiles")
        self.api_key = settings.AZURE_SPEECH_KEY
        self.region = settings.AZURE_SPEECH_REGION
        self.base_url = settings.AZURE_SPEECH_ENDPOINT.rstrip('/')
        self.api_version = "2021-09-05"
        
        self.headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
        }

    async def _create_azure_profile(self) -> str:
        """Creates a new speaker profile in Azure and returns the profileId."""
        url = f"{self.base_url}/speaker-recognition/verification/text-independent/profiles?api-version={self.api_version}"
        payload = {"locale": "en-US"}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=self.headers, json=payload, timeout=30.0)
            if response.status_code != 201:
                error_body = response.text
                try:
                    error_json = response.json()
                    error_msg = error_json.get("error", {}).get("message", error_body)
                except:
                    error_msg = error_body
                
                raise Exception(f"Azure Profile Creation Error ({response.status_code}): {error_msg}")
            
            data = response.json()
            return data["profileId"]

    async def enroll_voice(self, user_id: str, samples: List[bytes]) -> Dict[str, Any]:
        """
        Enrolls voice samples for a user in Azure Speaker Recognition.
        """
        try:
            # 1. Get or create Azure Profile ID
            profile = await self.voice_profiles.find_one({"user_id": user_id})
            azure_profile_id = profile.get("azure_profile_id") if profile else None
            
            if not azure_profile_id:
                try:
                    azure_profile_id = await self._create_azure_profile()
                    logger.info(f"Created new Azure profile {azure_profile_id} for user {user_id}")
                except Exception as e:
                    return {"success": False, "error": str(e)}

            # 2. Enroll each sample
            enrollment_results = []
            async with httpx.AsyncClient() as client:
                for idx, audio_bytes in enumerate(samples):
                    normalized_wav = await asyncio.to_thread(normalize_audio, audio_bytes)
                    
                    enroll_url = f"{self.base_url}/speaker-recognition/verification/text-independent/profiles/{azure_profile_id}/enrollments?api-version={self.api_version}&ignoreMinLength=true"
                    headers = {**self.headers, "Content-Type": "audio/wav"}
                    
                    response = await client.post(enroll_url, headers=headers, content=normalized_wav, timeout=60.0)
                    
                    if response.status_code not in [200, 201]:
                        error_body = response.text
                        try:
                            error_json = response.json()
                            error_msg = error_json.get("error", {}).get("message", error_body)
                        except:
                            error_msg = error_body
                        return {"success": False, "error": f"Azure Enrollment Error (Sample {idx+1}, Status {response.status_code}): {error_msg}"}
                    
                    enrollment_results.append(response.json())

            # 3. Update MongoDB
            last_result = enrollment_results[-1] if enrollment_results else {}
            payload = {
                "user_id": user_id,
                "azure_profile_id": azure_profile_id,
                "updated_at": datetime.utcnow(),
                "enrollment_status": last_result.get("enrollmentStatus", "Unknown"),
                "remaining_enrollment_speech_time": last_result.get("remainingEnrollmentSpeechTime", 0)
            }

            if profile:
                await self.voice_profiles.update_one({"user_id": user_id}, {"$set": payload})
            else:
                payload["created_at"] = datetime.utcnow()
                await self.voice_profiles.insert_one(payload)

            return {
                "success": True, 
                "azure_profile_id": azure_profile_id,
                "total_samples": len(samples),
                "enrollment_status": payload["enrollment_status"],
                "remaining_time": payload["remaining_enrollment_speech_time"]
            }

        except Exception as e:
            logger.error(f"Unexpected error in enroll_voice: {str(e)}")
            return {"success": False, "error": f"Internal Error: {str(e)}"}

    async def verify_voice(self, user_id: str, verification_audio: bytes) -> Dict[str, Any]:
        """
        Verifies a voice sample against an enrolled Azure speaker profile.
        """
        try:
            profile = await self.voice_profiles.find_one({"user_id": user_id})
            if not profile or not profile.get("azure_profile_id"):
                return {"success": False, "error": "Voice profile not found or not enrolled in Azure"}

            azure_profile_id = profile["azure_profile_id"]
            normalized_wav = await asyncio.to_thread(normalize_audio, verification_audio)

            verify_url = f"{self.base_url}/speaker-recognition/verification/text-independent/profiles/{azure_profile_id}/verify?api-version={self.api_version}"
            headers = {**self.headers, "Content-Type": "audio/wav"}

            async with httpx.AsyncClient() as client:
                response = await client.post(verify_url, headers=headers, content=normalized_wav, timeout=60.0)
                
                if response.status_code != 200:
                    error_body = response.text
                    try:
                        error_json = response.json()
                        error_msg = error_json.get("error", {}).get("message", error_body)
                    except:
                        error_msg = error_body
                    return {"success": False, "error": f"Azure Verification Error ({response.status_code}): {error_msg}"}
                
                result = response.json()

            # result contains: recognitionResult (Accept/Reject), score (0 to 1)
            recognition_result = result.get("recognitionResult", "Reject")
            score = result.get("score", 0.0)
            
            voice_match = recognition_result == "Accept"

            return {
                "success": True,
                "voice_match": voice_match,
                "voice_match_result": f"{round(score * 100, 2)}%",
                "confidence_score": score,
                "recognition_result": recognition_result,
                "azure_details": result
            }

        except Exception as e:
            logger.error(f"Unexpected error in verify_voice: {str(e)}")
            return {"success": False, "error": f"Internal Error: {str(e)}"}