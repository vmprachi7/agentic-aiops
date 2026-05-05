"""
Agentic AIOps — Main Agent Loop

Runs continuously in AKS as a pod.
Every POLL_INTERVAL_SECONDS:
  1. Query Prometheus for firing alerts
  2. For each NEW alert:
     a. Query Loki for related logs
     b. Send alert + logs to Groq AI for analysis
     c. Create GitHub Issue (alert notification)
     d. Open GitHub PR (draft runbook)
  3. Sleep and repeat
"""
import sys
import time
import signal
from datetime import datetime, timezone

from agent import config
from agent import alert_tracker
from agent.prometheus_client import get_firing_alerts
from agent.loki_client import get_logs
from agent.ai_analyzer import analyze
from agent.github_client import create_alert_issue


# ── Graceful shutdown ─────────────────────────────────────────
running = True

def handle_shutdown(signum, frame):
    global running
    print("\n[INFO] Shutdown signal received — stopping agent gracefully")
    running = False

signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT,  handle_shutdown)


# ── Startup validation ────────────────────────────────────────

def validate_config():
    missing = config.validate()
    if missing:
        print(f"[ERROR] Missing required configuration: {', '.join(missing)}")
        print("        Set these as environment variables or in .env file")
        sys.exit(1)


# ── Main processing ───────────────────────────────────────────

def process_alert(alert):
    """Process a single firing alert end to end."""
    print(f"\n  {'─' * 50}")
    print(f"  🚨 New alert: {alert.name}")
    print(f"     Severity:  {alert.severity}")
    print(f"     Namespace: {alert.namespace}")
    print(f"     Pod:       {alert.pod}")
    print(f"     Summary:   {alert.summary}")

    # Step 1 — Fetch logs from Loki
    print(f"\n  📋 Fetching logs from Loki...")
    logs = get_logs(namespace=alert.namespace, pod=alert.pod)
    log_lines = len(logs.split("\n"))
    print(f"     Got {log_lines} log lines")

    # Step 2 — AI analysis
    print(f"\n  🤖 Asking Groq AI for root cause analysis...")
    analysis = analyze(alert=alert, logs=logs)
    print(f"     Root cause: {analysis.root_cause[:80]}...")
    print(f"     Confidence: {analysis.confidence}")
    print(f"     Immediate actions: {len(analysis.immediate_steps)}")

    # Step 3 — Create GitHub Issue + add AI runbook as comment
    print(f"\n  📌 Creating GitHub Issue with AI runbook comment...")
    issue_url = create_alert_issue(alert=alert, analysis=analysis)

    # Step 4 — Mark as processed
    alert_tracker.mark_seen(alert.fingerprint)

    print(f"\n  ✅ Done — {issue_url}")


def run_cycle():
    """Single poll cycle — check alerts and process new ones."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"\n[{now}] Checking Prometheus for firing alerts...")

    alerts = get_firing_alerts()

    if not alerts:
        print(f"  ✅ No firing alerts")
        return

    print(f"  Found {len(alerts)} firing alert(s)")

    new_count = 0
    for alert in alerts:
        if alert_tracker.is_seen(alert.fingerprint):
            print(f"  ⏭️  Skipping already-processed: {alert.name} ({alert.namespace})")
            continue

        new_count += 1
        try:
            process_alert(alert)
        except Exception as e:
            print(f"  [ERROR] Failed to process alert {alert.name}: {e}")
            # Don't mark as seen — retry on next cycle

    if new_count == 0:
        print(f"  ✅ All {len(alerts)} alert(s) already processed")


# ── Entry point ───────────────────────────────────────────────

def main():
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  Agentic AIOps — Starting")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  Prometheus: {config.PROMETHEUS_URL}")
    print(f"  Loki:       {config.LOKI_URL}")
    print(f"  GitHub:     {config.GITHUB_REPO}")
    print(f"  Poll every: {config.POLL_INTERVAL_SECONDS}s")
    print(f"  Mock data:  {config.USE_MOCK_DATA}")
    print(f"  Severities: {', '.join(config.ALERT_SEVERITIES)}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    validate_config()
    print("\n[INFO] Configuration valid — agent starting\n")

    while running:
        try:
            run_cycle()
        except Exception as e:
            print(f"[ERROR] Unexpected error in poll cycle: {e}")

        if running:
            print(f"\n  Sleeping {config.POLL_INTERVAL_SECONDS}s...")
            time.sleep(config.POLL_INTERVAL_SECONDS)

    print("\n[INFO] Agent stopped cleanly")


if __name__ == "__main__":
    main()