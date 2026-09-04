FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LAVC_JOB_ROOT=/data/jobs

RUN apt-get update \
    && apt-get install -y --no-install-recommends chromium ffmpeg fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir . \
    && groupadd --system laka \
    && useradd --system --gid laka --home-dir /app laka \
    && mkdir -p /data/jobs \
    && chown -R laka:laka /app /data/jobs

USER laka
EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/healthz', timeout=3)"

# One process owns the in-memory job queue; threads keep status/download requests responsive.
CMD ["gunicorn", "--bind", "0.0.0.0:8765", "--workers", "1", "--threads", "4", "--timeout", "0", "--access-logfile", "-", "laka_video.web:create_app()"]
