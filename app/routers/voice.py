from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.voice_service import VoiceVerificationService


router = APIRouter(prefix="/voice", tags=["Voice Verification"])


@router.post("/enroll/{user_id}")
async def enroll_voice(
    user_id: str,
    voice_sample_1: UploadFile = File(...),
    voice_sample_2: UploadFile = File(...),
    voice_sample_3: UploadFile = File(...),
):
    samples = [
        await voice_sample_1.read(),
        await voice_sample_2.read(),
        await voice_sample_3.read(),
    ]

    service = VoiceVerificationService()
    result = await service.enroll_voice(user_id, samples)

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Voice enrollment failed"))

    return {"message": "Voice enrolled successfully"}


@router.post("/verify/{user_id}")
async def verify_voice(
    user_id: str,
    verification_voice: UploadFile = File(...),
):
    verification_audio = await verification_voice.read()

    service = VoiceVerificationService()
    result = await service.verify_voice(user_id, verification_audio)

    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Voice profile not found"))

    return {
        "voice_match": result["voice_match"],
        "voice_match_result": result["voice_match_result"],
    }