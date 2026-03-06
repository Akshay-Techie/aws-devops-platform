# ============================================================
# Dockerfile — Future MLOps Architect | Project-04
# Location: docker/app/Dockerfile
#
# MULTI-STAGE BUILD
#   Stage 1 (builder) → installs all dependencies
#   Stage 2 (runtime) → copies only what is needed to run
# ============================================================


# ══════════════════════════════════════════════════════════
#  STAGE 1 — BUILDER
# ══════════════════════════════════════════════════════════

FROM python:3.11-slim AS builder

WORKDIR /build

# Copy requirements first — Docker cache optimization
# If requirements.txt unchanged, pip install is skipped on rebuild
COPY requirements.txt .

RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ══════════════════════════════════════════════════════════
#  STAGE 2 — RUNTIME
# ══════════════════════════════════════════════════════════

FROM python:3.11-slim AS runtime

# Security: non-root user
RUN useradd --no-create-home --shell /bin/false appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application files
# Both app.py and index.html must be in the same directory
# Flask's send_from_directory('.', 'index.html') looks here
COPY app.py .
COPY index.html .

# Switch to non-root user
USER appuser

EXPOSE 5000

ENV PORT=5000 \
    APP_ENV=production \
    APP_VERSION=1.0.0 \
    MODEL_NAME=mlops-demo-model \
    MODEL_VERSION=v1.0 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=15s \
    CMD python -c \
    "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')"

CMD ["gunicorn", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "2", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "app:app"]