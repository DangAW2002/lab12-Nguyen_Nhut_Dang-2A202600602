# ============================================================
# Dockerfile — Stateless Agent with Redis Session (Scaling Demo)
# ============================================================

FROM python:3.11-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt


FROM python:3.11-slim AS runtime

RUN groupadd -r agent && useradd -r -g agent -d /app agent

WORKDIR /app

COPY --from=builder /root/.local /home/agent/.local

COPY app.py .
COPY utils/ ./utils/

RUN chown -R agent:agent /app

USER agent

ENV PATH=/home/agent/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Ensure user-installed packages are found
ENV PYTHONUSERBASE=/home/agent/.local

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c \
    "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" \
    || exit 1

CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
