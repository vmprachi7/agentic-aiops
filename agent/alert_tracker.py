"""
Alert tracker — prevents duplicate GitHub Issues and PRs.
Keeps an in-memory set of alert fingerprints already processed.
Resets when the pod restarts (acceptable — Issues/PRs will show as duplicates
but this is better than losing alerts on restart).
"""
import json
import os
from pathlib import Path

# File-based persistence so tracker survives pod restarts within a session
TRACKER_FILE = Path("/tmp/seen_alerts.json")


def _load() -> set:
    try:
        if TRACKER_FILE.exists():
            return set(json.loads(TRACKER_FILE.read_text()))
    except Exception:
        pass
    return set()


def _save(seen: set):
    try:
        TRACKER_FILE.write_text(json.dumps(list(seen)))
    except Exception:
        pass


def is_seen(fingerprint: str) -> bool:
    """Returns True if this alert has already been processed."""
    return fingerprint in _load()


def mark_seen(fingerprint: str):
    """Mark an alert fingerprint as processed."""
    seen = _load()
    seen.add(fingerprint)
    _save(seen)


def clear():
    """Clear all tracked alerts (for testing)."""
    _save(set())


def count() -> int:
    """Return number of tracked alerts."""
    return len(_load())