"""
Central configuration — reads from environment variables.
In AKS these come from Kubernetes ConfigMap and Secrets.
Locally they come from .env file.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── AI ────────────────────────────────────────────────────────
GROQ_API_KEY  = os.getenv("GROQ_API_KEY", "")
AI_MODEL      = "llama-3.1-8b-instant"
AI_MAX_TOKENS = 2048

# ── Prometheus ────────────────────────────────────────────────
# Local:   http://localhost:9090  (via port-forward)
# In AKS:  http://kube-prometheus-stack-prometheus.monitoring.svc.cluster.local:9090
PROMETHEUS_URL = os.getenv(
    "PROMETHEUS_URL",
    "http://kube-prometheus-stack-prometheus.monitoring.svc.cluster.local:9090"
)

# ── Loki ─────────────────────────────────────────────────────
# Local:   http://localhost:3100  (via port-forward)
# In AKS:  http://loki.monitoring.svc.cluster.local:3100
LOKI_URL = os.getenv(
    "LOKI_URL",
    "http://loki.monitoring.svc.cluster.local:3100"
)

# ── GitHub ────────────────────────────────────────────────────
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO  = os.getenv("GITHUB_REPO", "vmprachi7/agentic-aiops")

# ── Agent behaviour ───────────────────────────────────────────
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "60"))
LOKI_LOG_LINES        = int(os.getenv("LOKI_LOG_LINES", "50"))
LOKI_LOOKBACK_SECONDS = int(os.getenv("LOKI_LOOKBACK_SECONDS", "300"))

# Alert severities to act on
ALERT_SEVERITIES = os.getenv("ALERT_SEVERITIES", "critical,warning").split(",")

# Alerts to ignore — AKS false positives + heartbeat
EXCLUDE_ALERTS = os.getenv(
    "EXCLUDE_ALERTS",
    "KubeSchedulerDown,KubeControllerManagerDown,KubeProxyDown,Watchdog"
).split(",")

# Use mock data instead of real Prometheus/Loki
USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "false").lower() == "true"


def validate() -> list[str]:
    missing = []
    if not GROQ_API_KEY:
        missing.append("GROQ_API_KEY")
    if not GITHUB_TOKEN:
        missing.append("GITHUB_TOKEN")
    return missing