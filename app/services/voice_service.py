import asyncio
import os
import tempfile
from datetime import datetime
from typing import Any, Dict, List

import numpy as np
from resemblyzer import VoiceEncoder, preprocess_wav

from app.database.KYCdatabase import MongoDB


encoder = VoiceEncoder()


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

        wav = preprocess_wav(temp_path)
        embedding = encoder.embed_utterance(wav)
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
        voice_match = average_similarity >= 0.75

        return {
            "success": True,
            "voice_match": voice_match,
            "voice_match_result": f"{round(average_similarity * 100, 2)}%",
            "average_similarity": average_similarity,
            "similarities": similarities,
        }