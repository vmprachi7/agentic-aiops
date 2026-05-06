"""
Alert tracker — prevents duplicate GitHub Issues.
Stores alert fingerprints with timestamps.
Alerts expire after ALERT_EXPIRY_HOURS so re-firing alerts
after resolution create a new Issue.
"""
import json
import time
import os
from pathlib import Path

TRACKER_FILE       = Path("/tmp/seen_alerts.json")
ALERT_EXPIRY_HOURS = float(os.getenv("ALERT_EXPIRY_HOURS", "6"))


def _load() -> dict:
    """Load tracker — returns {fingerprint: timestamp}"""
    try:
        if TRACKER_FILE.exists():
            return json.loads(TRACKER_FILE.read_text())
    except Exception:
        pass
    return {}


def _save(data: dict):
    try:
        TRACKER_FILE.write_text(json.dumps(data, indent=2))
    except Exception:
        pass


def _purge_expired(data: dict) -> dict:
    """Remove alerts older than ALERT_EXPIRY_HOURS."""
    now     = time.time()
    cutoff  = ALERT_EXPIRY_HOURS * 3600
    return {
        fp: ts for fp, ts in data.items()
        if (now - ts) < cutoff
    }


def is_seen(fingerprint: str) -> bool:
    """Returns True if alert was processed recently (within expiry window)."""
    data = _purge_expired(_load())
    return fingerprint in data


def mark_seen(fingerprint: str):
    """Mark alert as processed with current timestamp."""
    data = _purge_expired(_load())
    data[fingerprint] = time.time()
    _save(data)


def clear():
    """Clear all tracked alerts (for testing)."""
    _save({})


def count() -> int:
    return len(_purge_expired(_load()))


def get_status() -> list[dict]:
    """Returns list of tracked alerts with human-readable expiry time."""
    data   = _purge_expired(_load())
    now    = time.time()
    result = []
    for fp, ts in data.items():
        age_hours   = (now - ts) / 3600
        expires_in  = ALERT_EXPIRY_HOURS - age_hours
        result.append({
            "fingerprint": fp,
            "age_hours":   round(age_hours, 2),
            "expires_in":  round(expires_in, 2),
        })
    return sorted(result, key=lambda x: x["age_hours"])