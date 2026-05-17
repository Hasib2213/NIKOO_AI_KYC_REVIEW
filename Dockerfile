# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install CPU-only PyTorch stack first to avoid GPU/CUDA wheels
RUN pip install --user --no-warn-script-location \
    --index-url https://download.pytorch.org/whl/cpu \
    torch torchaudio

# Install the rest of the Python dependencies after torch is already present
RUN pip install --upgrade pip && \
    pip install --user --no-warn-script-location -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH=/root/.local/bin:$PATH
ENV HF_HOME=/cache/huggingface
ENV HUGGINGFACE_HUB_CACHE=/cache/huggingface/hub
ENV TORCH_HOME=/cache/torch

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Create writable cache directories for model downloads
RUN mkdir -p /cache/huggingface/hub /cache/torch

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
