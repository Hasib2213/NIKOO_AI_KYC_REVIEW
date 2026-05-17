import asyncio
import math
import os
import tempfile
from datetime import datetime
from typing import Any, Dict, List

import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly

from app.database.KYCdatabase import MongoDB


ECAPA_SOURCE = "speechbrain/spkrec-ecapa-voxceleb"
TARGET_SAMPLE_RATE = 16000
_classifier = None
_torch = None


def _get_torch():
    global _torch
    if _torch is None:
        import torch
        _torch = torch
    return _torch


def _get_classifier():
    global _classifier
    if _classifier is None:
        from speechbrain.inference import EncoderClassifier
        _classifier = EncoderClassifier.from_hparams(source=ECAPA_SOURCE)
    return _classifier


def _load_wav_mono_float(path: str) -> tuple[np.ndarray, int]:
    try:
        sample_rate, audio = wavfile.read(path)
    except Exception as e:
        raise ValueError(f"WAV format required. Error: {e}") from e

    if audio.ndim > 1:
        audio = np.mean(audio, axis=1)

    if np.issubdtype(audio.dtype, np.integer):
        info = np.iinfo(audio.dtype)
        if audio.dtype == np.uint8:
            audio = (audio.astype(np.float32) - 128.0) / 128.0
        else:
            audio = audio.astype(np.float32) / float(info.max)
    else:
        audio = audio.astype(np.float32)

    return audio, sample_rate


def cosine_similarity(emb1: List[float], emb2: List[float]) -> float:
    vec1 = np.array(emb1)
    vec2 = np.array(emb2)

    denominator = np.linalg.norm(vec1) * np.linalg.norm(vec2)
    if denominator == 0:
        return 0.0

    similarity = np.dot(vec1, vec2) / denominator
    return float(similarity)


def generate_embedding(audio_bytes: bytes) -> List[float]:
    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(audio_bytes)
            temp_path = temp_file.name

        audio, sample_rate = _load_wav_mono_float(temp_path)

        if audio.size == 0:
            raise ValueError("Empty audio received")

        if sample_rate != TARGET_SAMPLE_RATE:
            divisor = math.gcd(sample_rate, TARGET_SAMPLE_RATE)
            up = TARGET_SAMPLE_RATE // divisor
            down = sample_rate // divisor
            audio = resample_poly(audio, up=up, down=down).astype(np.float32)

        torch = _get_torch()
        signal = torch.from_numpy(audio).unsqueeze(0)

        classifier = _get_classifier()
        with torch.no_grad():
            embedding = classifier.encode_batch(signal).squeeze().cpu().numpy()

        return embedding.tolist()
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


class VoiceVerificationService:
    def __init__(self):
        self.voice_profiles = MongoDB.get_collection("voice_profiles")

    async def enroll_voice(self, user_id: str, samples: List[bytes]) -> Dict[str, Any]:
        embeddings = []

        for audio_bytes in samples:
            embedding = await asyncio.to_thread(generate_embedding, audio_bytes)
            embeddings.append(embedding)

        payload = {
            "user_id": user_id,
            "embeddings": embeddings,
            "updated_at": datetime.utcnow(),
        }

        existing = await self.voice_profiles.find_one({"user_id": user_id})
        if existing:
            await self.voice_profiles.update_one(
                {"user_id": user_id},
                {"$set": payload},
            )
        else:
            payload["created_at"] = datetime.utcnow()
            await self.voice_profiles.insert_one(payload)

        return {"success": True, "total_samples": len(embeddings)}

    async def verify_voice(self, user_id: str, verification_audio: bytes) -> Dict[str, Any]:
        profile = await self.voice_profiles.find_one({"user_id": user_id})
        if not profile:
            return {"success": False, "error": "Voice profile not found"}

        stored_embeddings = profile.get("embeddings", [])
        if len(stored_embeddings) == 0:
            return {"success": False, "error": "Voice profile is empty"}

        verification_embedding = await asyncio.to_thread(
            generate_embedding,
            verification_audio,
        )

        similarities = [
            cosine_similarity(stored_embedding, verification_embedding)
            for stored_embedding in stored_embeddings
        ]

        average_similarity = sum(similarities) / len(similarities)
        voice_match = average_similarity >= 0.5

        return {
            "success": True,
            "voice_match": voice_match,
            "voice_match_result": f"{round(average_similarity * 100, 2)}%",
            "average_similarity": average_similarity,
            "similarities": similarities,
        }