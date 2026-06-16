# ── Gridlock 2.0 ML inference service ──
# For GPU: use nvidia/cuda base + install torch with CUDA. CPU image by default.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

# OpenCV / video runtime deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ml/ ./ml/
COPY configs/ ./configs/

EXPOSE 8001
CMD ["uvicorn", "ml.server:app", "--host", "0.0.0.0", "--port", "8001"]
