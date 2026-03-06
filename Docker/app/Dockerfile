# ── Stage 1: Builder ──────────────────────────────────────
# Full image — install everything needed to compile/install deps
FROM python:3.11-slim AS builder
WORKDIR /build
COPY requirements.txt .

# Install into /install so we can copy only this folder to stage 2
# Result: stage 2 doesn't need pip, gcc, or any build tools
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: Runtime ──────────────────────────────────────
# Fresh minimal image — no build tools, no cache, smaller attack surface
FROM python:3.11-slim AS runtime

# Security: never run as root inside a container
RUN useradd --no-create-home --shell /bin/false appuser

WORKDIR /app

# Copy only the installed dependencies and the app code
COPY --from=builder /install /usr/local    
COPY app.py .

USER appuser
EXPOSE 5000

ENV PORT=5000 APP_ENV=production APP_VERSION=1.0.0

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')"

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]