"""
Prometheus API client.
Queries the Prometheus API for currently firing alerts.

Filtering strategy:
- Include all severities by default (critical, warning, info, none)
- Exclude known AKS false positives by alert name
- Exclude system namespaces (kube-system, monitoring, argocd)
- Focus on user workload namespaces
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
        """Unique ID — alert name + namespace + pod."""
        return f"{self.name}-{self.namespace}-{self.pod}"


# Namespaces to ignore — system components, not user workloads
SYSTEM_NAMESPACES = {
    "kube-system", "monitoring", "argocd",
    "cert-manager", "ingress-nginx", ""
}


def get_firing_alerts() -> list[Alert]:
    """
    Returns list of currently firing alerts.
    Filters out AKS false positives and system namespace noise.
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

        alerts    = []
        all_alerts = data.get("data", {}).get("alerts", [])
        print(f"  Prometheus returned {len(all_alerts)} total alerts")

        for a in all_alerts:
            if a.get("state") != "firing":
                continue

            labels    = a.get("labels", {})
            anns      = a.get("annotations", {})
            name      = labels.get("alertname", "UnknownAlert")
            severity  = labels.get("severity", "none")
            namespace = labels.get("namespace", "")

            # Skip known AKS false positives
            if name in config.EXCLUDE_ALERTS:
                print(f"  ⏭️  Skipping excluded alert: {name}")
                continue

            # Skip system namespaces — too noisy, not user workloads
            if namespace in SYSTEM_NAMESPACES:
                print(f"  ⏭️  Skipping system namespace alert: {name} ({namespace})")
                continue

            # Skip cluster-wide alerts with no namespace
            # (KubeSchedulerDown, KubeProxyDown etc already caught above)
            # but allow through if it's a meaningful cluster alert
            if not namespace and name not in config.ALERT_SEVERITIES:
                pass  # let it through — we filter by EXCLUDE_ALERTS instead

            alerts.append(Alert(
                name=name,
                severity=severity,
                namespace=namespace or "cluster",
                pod=labels.get("pod", labels.get("deployment", "unknown")),
                summary=anns.get("summary", "No summary available"),
                description=anns.get("description", "No description available"),
                labels=labels,
                starts_at=a.get("activeAt", "unknown"),
            ))

        print(f"  After filtering: {len(alerts)} actionable alerts")
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
                        "has been in waiting state for more than 1 hour.",
            labels={
                "alertname": "KubeContainerWaiting",
                "severity":  "warning",
                "namespace": "finops-engine",
                "pod":       "finops-engine-695fcf85bc-k9bp6",
            },
            starts_at="2026-05-05T08:30:00Z",
        ),
    ]