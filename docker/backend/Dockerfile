FROM python:3.10-slim as builder

WORKDIR /app

RUN pip install --no-cache-dir poetry==1.5.1

COPY pyproject.toml poetry.lock* /app/

RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/venv /app/venv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/venv/bin:$PATH"

COPY . /app/

RUN adduser --disabled-password --gecos "" appuser && \
    chown -R appuser:appuser /app

RUN mkdir -p /app/uploads && \
    chown -R appuser:appuser /app/uploads

USER appuser

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
