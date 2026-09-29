# Backend FastAPI + SQLite (products/be/). Build từ gốc repo:
#   docker build -f products/docker/be/Dockerfile -t flood-rescue/be .
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    RESCUE_DB_FILE=/var/lib/rescue/rescue_reports.db \
    RESCUE_UPLOADS_DIR=/var/lib/rescue/uploads \
    RESCUE_BACKUP_DIR=/var/lib/rescue/backups \
    RESCUE_GOLD_DIR=/app/gold

WORKDIR /app/be
COPY products/be/requirements.txt ./
RUN pip install -r requirements.txt

COPY products/be/ ./
# Chỉ algorithm_input.json của từng run được phép làm đầu vào suy luận (thucnghiem/data/README.md).
COPY thucnghiem/data/gold/ /app/gold/
COPY --chmod=755 products/docker/be/entrypoint.sh /usr/local/bin/entrypoint.sh

RUN useradd --system --uid 10001 --home-dir /app app \
    && mkdir -p /var/lib/rescue/uploads \
    && chown -R app:app /var/lib/rescue /app/be
USER app
VOLUME ["/var/lib/rescue"]

EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=5s --start-period=20s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=4)"
ENTRYPOINT ["entrypoint.sh"]
