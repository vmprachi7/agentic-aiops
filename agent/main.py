"""
Agentic AIOps — Main Agent Loop

Runs continuously in AKS as a pod.
Every POLL_INTERVAL_SECONDS:
  1. Query Prometheus for firing alerts
  2. For each NEW alert (not seen within ALERT_EXPIRY_HOURS):
     a. Query Loki for related logs
     b. Send alert + logs to Groq AI for analysis
     c. Create GitHub Issue with AI runbook as comment
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
    print("\n[INFO] Shutdown signal received — stopping agent")
    running = False

signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT,  handle_shutdown)


def validate_config():
    missing = config.validate()
    if missing:
        print(f"[ERROR] Missing required config: {', '.join(missing)}")
        sys.exit(1)


def process_alert(alert):
    """Process a single firing alert end to end."""
    print(f"\n  {'─' * 50}")
    print(f"  🚨 New alert: {alert.name}")
    print(f"     Severity:  {alert.severity}")
    print(f"     Namespace: {alert.namespace}")
    print(f"     Pod:       {alert.pod}")
    print(f"     Summary:   {alert.summary[:80]}")

    # Fetch logs
    print(f"\n  📋 Fetching logs from Loki...")
    logs     = get_logs(namespace=alert.namespace, pod=alert.pod)
    log_lines = len([l for l in logs.split("\n") if l.strip()])
    print(f"     Got {log_lines} log lines")

    # AI analysis
    print(f"\n  🤖 Asking Groq AI for root cause analysis...")
    analysis = analyze(alert=alert, logs=logs)
    print(f"     Root cause: {analysis.root_cause[:80]}...")
    print(f"     Confidence: {analysis.confidence}")

    # Create GitHub Issue + comment
    print(f"\n  📌 Creating GitHub Issue with AI runbook comment...")
    issue_url = create_alert_issue(alert=alert, analysis=analysis)

    # Mark as processed with timestamp
    alert_tracker.mark_seen(alert.fingerprint)

    print(f"\n  ✅ Done — {issue_url}")


def run_cycle():
    """Single poll cycle."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"\n[{now}] Polling Prometheus...")

    # Show tracker status
    tracked = alert_tracker.count()
    if tracked > 0:
        print(f"  Tracker: {tracked} alert(s) suppressed "
              f"(expiry: {config.ALERT_EXPIRY_HOURS}h)")
        for s in alert_tracker.get_status():
            print(f"    · {s['fingerprint'][:50]} "
                  f"— seen {s['age_hours']:.1f}h ago, "
                  f"expires in {s['expires_in']:.1f}h")

    alerts = get_firing_alerts()

    if not alerts:
        print(f"  ✅ No actionable alerts")
        return

    new_count = 0
    for alert in alerts:
        if alert_tracker.is_seen(alert.fingerprint):
            print(f"  ⏭️  Suppressed (seen within {config.ALERT_EXPIRY_HOURS}h): "
                  f"{alert.name} ({alert.namespace})")
            continue

        new_count += 1
        try:
            process_alert(alert)
        except Exception as e:
            print(f"  [ERROR] Failed to process {alert.name}: {e}")

    if new_count == 0:
        print(f"  ✅ All {len(alerts)} alert(s) already processed")


def main():
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  Agentic AIOps — Starting")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  Prometheus:    {config.PROMETHEUS_URL}")
    print(f"  Loki:          {config.LOKI_URL}")
    print(f"  GitHub:        {config.GITHUB_REPO}")
    print(f"  Poll interval: {config.POLL_INTERVAL_SECONDS}s")
    print(f"  Alert expiry:  {config.ALERT_EXPIRY_HOURS}h")
    print(f"  Excluded:      {', '.join(config.EXCLUDE_ALERTS)}")
    print(f"  Mock data:     {config.USE_MOCK_DATA}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    validate_config()
    print("\n[INFO] Configuration valid — agent running\n")

    while running:
        try:
            run_cycle()
        except Exception as e:
            print(f"[ERROR] Unexpected error: {e}")

        if running:
            print(f"\n  Sleeping {config.POLL_INTERVAL_SECONDS}s...")
            time.sleep(config.POLL_INTERVAL_SECONDS)

    print("\n[INFO] Agent stopped")


if __name__ == "__main__":
    main()