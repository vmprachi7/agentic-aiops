# ARM64 — matches Standard_B2ps_v2 AKS node
FROM --platform=linux/arm64 python:3.11-slim

WORKDIR /app

# PYTHONPATH so 'from agent import config' resolves correctly
ENV PYTHONPATH=/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agent/ ./agent/
COPY runbooks/ ./runbooks/

RUN adduser --disabled-password --gecos "" appuser && \
    chown -R appuser:appuser /app
USER appuser

# Health check — verify the agent process is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD pgrep -f "python.*main.py" || exit 1

CMD ["python", "agent/main.py"]