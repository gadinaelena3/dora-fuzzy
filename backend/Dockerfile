# Backend image — slim Python with the fuzzy DSS service.
FROM python:3.11-slim

WORKDIR /app

# System deps for numpy/pandas wheels (most are already there in slim-bookworm,
# but build-essential helps if a wheel falls back to source)
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY scripts ./scripts
COPY tests ./tests
COPY config ./config
COPY data ./data

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
