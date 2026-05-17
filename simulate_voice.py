import sys
sys.path.insert(0, '.')
import asyncio
from app.services.voice_service import generate_embedding
import wave, struct, math, io

# Create simple 16khz mono wav
sr = 16000
duration = 1.0
freq = 440.0
n_samples = int(sr * duration)
buf = io.BytesIO()
with wave.open(buf, 'wb') as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(sr)
    for i in range(n_samples):
        t = i / sr
        val = int(32767.0 * 0.5 * math.sin(2.0 * math.pi * freq * t))
        wf.writeframes(struct.pack('<h', val))
wav_bytesValue = buf.getvalue()
try:
    emb = generate_embedding(wav_bytesValue)
    print(f'success: embedding_len={len(emb)}')
except Exception as e:
    print(f'error: {type(e).__name__}: {e}')
