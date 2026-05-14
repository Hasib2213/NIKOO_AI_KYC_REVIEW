import sys
import os
import wave
import struct
import math
import io

# Ensure project root is on sys.path so `app` package imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.voice_service import generate_embedding

# generate 2s 16000Hz mono 440Hz sine wave PCM16
sr = 16000
duration = 2.0
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

wav_bytes = buf.getvalue()

print('Generated WAV bytes:', len(wav_bytes))

try:
    print('Calling generate_embedding...')
    emb = generate_embedding(wav_bytes)
    print('Embedding length:', len(emb))
    print('Embedding sample (first 8):', [round(x, 6) for x in emb[:8]])
except Exception as e:
    import traceback
    print('generate_embedding raised exception:')
    traceback.print_exc()
