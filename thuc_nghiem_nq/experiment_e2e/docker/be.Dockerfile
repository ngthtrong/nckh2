# [BẢN SAO] Backend FastAPI. Đường dẫn COPY tính từ gốc repo (build context).
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
COPY thuc_nghiem_nq/experiment_e2e/backend_requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

COPY products/be/ ./
# [CHỈNH SỬA] Seed script dùng bản sao trong thư mục thực nghiệm.
COPY thuc_nghiem_nq/experiment_e2e/seed_demo.py ./seed_demo.py
# Chỉ algorithm_input.json của từng run được phép làm đầu vào suy luận (thucnghiem/data/README.md).
COPY thucnghiem/data/gold/ /app/gold/
COPY --chmod=755 thuc_nghiem_nq/experiment_e2e/entrypoint.sh /usr/local/bin/entrypoint.sh

RUN useradd --system --uid 10001 --home-dir /app app \
    && mkdir -p /var/lib/rescue/uploads \
    && chown -R app:app /var/lib/rescue /app/be
USER app
VOLUME ["/var/lib/rescue"]

EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=5s --start-period=20s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=4)"
ENTRYPOINT ["entrypoint.sh"]
