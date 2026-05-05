"""
Prometheus API client.
Queries the Prometheus AlertManager API for currently firing alerts.
"""
import requests
from dataclasses import dataclass
from agent import config


@dataclass
class Alert:
    name:        str
    severity:    str
    namespace:   str
    pod:         str
    summary:     str
    description: str
    labels:      dict
    starts_at:   str

    @property
    def fingerprint(self) -> str:
        """Unique ID for this alert — used to avoid duplicate Issues/PRs."""
        return f"{self.name}-{self.namespace}-{self.pod}"


def get_firing_alerts() -> list[Alert]:
    """
    Returns list of currently firing alerts from Prometheus.
    Filters by configured severity levels.
    """
    if config.USE_MOCK_DATA:
        return _mock_alerts()

    try:
        resp = requests.get(
            f"{config.PROMETHEUS_URL}/api/v1/alerts",
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        alerts = []
        for a in data.get("data", {}).get("alerts", []):
            if a.get("state") != "firing":
                continue

            labels   = a.get("labels", {})
            anns     = a.get("annotations", {})
            severity = labels.get("severity", "unknown")

            if severity not in config.ALERT_SEVERITIES:
                continue

            # Skip AKS false positives and heartbeat alerts
            alert_name = labels.get("alertname", "")
            if alert_name in config.EXCLUDE_ALERTS:
                continue

            alerts.append(Alert(
                name=labels.get("alertname", "UnknownAlert"),
                severity=severity,
                namespace=labels.get("namespace", "unknown"),
                pod=labels.get("pod", labels.get("deployment", "unknown")),
                summary=anns.get("summary", "No summary available"),
                description=anns.get("description", "No description available"),
                labels=labels,
                starts_at=a.get("activeAt", "unknown"),
            ))

        return alerts

    except requests.exceptions.ConnectionError:
        print(f"  [WARN] Cannot reach Prometheus at {config.PROMETHEUS_URL}")
        return []
    except Exception as e:
        print(f"  [WARN] Prometheus query failed: {e}")
        return []


def _mock_alerts() -> list[Alert]:
    """Mock alerts for local testing."""
    return [
        Alert(
            name="KubePodCrashLooping",
            severity="critical",
            namespace="sample-app-1",
            pod="sample-app-1-7d5f886b6-pfx7g",
            summary="Pod is crash looping",
            description="Pod sample-app-1-7d5f886b6-pfx7g in namespace sample-app-1 "
                        "is restarting frequently (5 times in the last 10 minutes).",
            labels={
                "alertname": "KubePodCrashLooping",
                "severity":  "critical",
                "namespace": "sample-app-1",
                "pod":       "sample-app-1-7d5f886b6-pfx7g",
            },
            starts_at="2026-05-05T09:00:00Z",
        ),
        Alert(
            name="KubeContainerWaiting",
            severity="warning",
            namespace="finops-engine",
            pod="finops-engine-695fcf85bc-k9bp6",
            summary="Container is waiting",
            description="Container finops-engine in pod finops-engine-695fcf85bc-k9bp6 "
                        "has been in waiting state for more than 1 hour. "
                        "Reason: ImagePullBackOff.",
            labels={
                "alertname": "KubeContainerWaiting",
                "severity":  "warning",
                "namespace": "finops-engine",
                "pod":       "finops-engine-695fcf85bc-k9bp6",
            },
            starts_at="2026-05-05T08:30:00Z",
        ),
    ]