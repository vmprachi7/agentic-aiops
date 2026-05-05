"""
Loki API client.
Fetches recent log lines for a given namespace/pod.
"""
import time
import requests
from agent import config


def get_logs(namespace: str, pod: str) -> str:
    """
    Fetch recent log lines from Loki for a given namespace and pod.
    Returns formatted log string.
    """
    if config.USE_MOCK_DATA:
        return _mock_logs(namespace, pod)

    try:
        end_ns   = int(time.time() * 1e9)
        start_ns = end_ns - (config.LOKI_LOOKBACK_SECONDS * int(1e9))

        # LogQL query — filter by namespace and pod
        if pod and pod != "unknown":
            query = f'{{namespace="{namespace}", pod="{pod}"}}'
        else:
            query = f'{{namespace="{namespace}"}}'

        resp = requests.get(
            f"{config.LOKI_URL}/loki/api/v1/query_range",
            params={
                "query": query,
                "start": start_ns,
                "end":   end_ns,
                "limit": config.LOKI_LOG_LINES,
                "direction": "backward",
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        lines = []
        for stream in data.get("data", {}).get("result", []):
            for ts, line in stream.get("values", []):
                lines.append(line)

        if not lines:
            return f"No logs found for {namespace}/{pod} in the last {config.LOKI_LOOKBACK_SECONDS}s"

        # Most recent first
        lines.reverse()
        return "\n".join(lines[:config.LOKI_LOG_LINES])

    except requests.exceptions.ConnectionError:
        return f"[WARN] Cannot reach Loki at {config.LOKI_URL}"
    except Exception as e:
        return f"[WARN] Loki query failed: {e}"


def _mock_logs(namespace: str, pod: str) -> str:
    """Mock logs for local testing — simulates a CrashLoopBackOff."""
    if "sample-app-1" in namespace or "sample-app-1" in pod:
        return """2026-05-05T09:00:01Z INFO  Starting application...
2026-05-05T09:00:01Z INFO  Loading configuration from /etc/config/app.yaml
2026-05-05T09:00:01Z ERROR ConfigError: Required environment variable APP_SECRET not set
2026-05-05T09:00:01Z ERROR Failed to initialise application: missing configuration
2026-05-05T09:00:01Z FATAL Exiting with code 1
2026-05-05T08:59:01Z INFO  Starting application...
2026-05-05T08:59:01Z INFO  Loading configuration from /etc/config/app.yaml
2026-05-05T08:59:01Z ERROR ConfigError: Required environment variable APP_SECRET not set
2026-05-05T08:59:01Z ERROR Failed to initialise application: missing configuration
2026-05-05T08:59:01Z FATAL Exiting with code 1
2026-05-05T08:58:01Z INFO  Starting application...
2026-05-05T08:58:01Z ERROR ConfigError: Required environment variable APP_SECRET not set
2026-05-05T08:58:01Z FATAL Exiting with code 1"""

    elif "finops-engine" in namespace or "finops-engine" in pod:
        return """2026-05-05T08:30:01Z WARNING Failed to pull image: devopsplatformacr.azurecr.io/finops-engine:latest
2026-05-05T08:30:01Z ERROR  ImagePullBackOff: Back-off pulling image
2026-05-05T08:30:01Z ERROR  Failed to pull image: unauthorized: authentication required
2026-05-05T08:29:01Z WARNING Retrying image pull...
2026-05-05T08:28:01Z ERROR  Failed to pull image: unauthorized: authentication required"""

    return f"No relevant logs found for {namespace}/{pod}"