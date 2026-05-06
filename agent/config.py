"""
Central configuration — reads from environment variables.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── AI ────────────────────────────────────────────────────────
GROQ_API_KEY  = os.getenv("GROQ_API_KEY", "")
AI_MODEL      = "llama-3.1-8b-instant"
AI_MAX_TOKENS = 2048

# ── Prometheus ────────────────────────────────────────────────
PROMETHEUS_URL = os.getenv(
    "PROMETHEUS_URL",
    "http://kube-prometheus-stack-prometheus.monitoring.svc.cluster.local:9090"
)

# ── Loki ─────────────────────────────────────────────────────
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

# How long before the same alert can create a new Issue (hours)
# Set to 0 to always create a new Issue for every firing alert
ALERT_EXPIRY_HOURS = float(os.getenv("ALERT_EXPIRY_HOURS", "6"))

# Alert severities to include — all by default
ALERT_SEVERITIES = os.getenv(
    "ALERT_SEVERITIES", "critical,warning,info,none"
).split(",")

# AKS false positives + heartbeat — always exclude these
EXCLUDE_ALERTS = os.getenv(
    "EXCLUDE_ALERTS",
    "KubeSchedulerDown,KubeControllerManagerDown,KubeProxyDown,Watchdog,KubeClientCertificateExpiration"
).split(",")

USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "false").lower() == "true"


def validate() -> list[str]:
    missing = []
    if not GROQ_API_KEY:
        missing.append("GROQ_API_KEY")
    if not GITHUB_TOKEN:
        missing.append("GITHUB_TOKEN")
    return missing