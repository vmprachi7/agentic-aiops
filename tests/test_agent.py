"""
Tests for Agentic AIOps
Run with: pytest tests/ -v
"""
import pytest
from unittest.mock import MagicMock, patch
from agent.prometheus_client import Alert, _mock_alerts
from agent.alert_tracker import is_seen, mark_seen, clear, count
from agent.ai_analyzer import _rule_based_analysis, Analysis


# ── Fixtures ──────────────────────────────────────────────────

def make_alert(name="KubePodCrashLooping", severity="critical",
               namespace="test-ns", pod="test-pod-abc"):
    return Alert(
        name=name,
        severity=severity,
        namespace=namespace,
        pod=pod,
        summary="Test alert summary",
        description="Test alert description",
        labels={"alertname": name, "severity": severity},
        starts_at="2026-05-05T09:00:00Z",
    )


# ── Alert fingerprint tests ───────────────────────────────────

def test_alert_fingerprint_unique_per_pod():
    a1 = make_alert(pod="pod-1")
    a2 = make_alert(pod="pod-2")
    assert a1.fingerprint != a2.fingerprint


def test_alert_fingerprint_same_alert():
    a1 = make_alert()
    a2 = make_alert()
    assert a1.fingerprint == a2.fingerprint


def test_alert_fingerprint_different_namespace():
    a1 = make_alert(namespace="ns-1")
    a2 = make_alert(namespace="ns-2")
    assert a1.fingerprint != a2.fingerprint


# ── Alert tracker tests ───────────────────────────────────────

def setup_function():
    """Clear tracker before each test."""
    clear()


def test_new_alert_not_seen():
    alert = make_alert()
    assert not is_seen(alert.fingerprint)


def test_mark_seen_persists():
    alert = make_alert()
    mark_seen(alert.fingerprint)
    assert is_seen(alert.fingerprint)


def test_different_alerts_tracked_independently():
    a1 = make_alert(pod="pod-1")
    a2 = make_alert(pod="pod-2")
    mark_seen(a1.fingerprint)
    assert is_seen(a1.fingerprint)
    assert not is_seen(a2.fingerprint)


def test_count_increases():
    assert count() == 0
    mark_seen("fp-1")
    mark_seen("fp-2")
    assert count() == 2


def test_clear_resets():
    mark_seen("fp-1")
    clear()
    assert count() == 0


# ── Mock alert tests ──────────────────────────────────────────

def test_mock_alerts_returns_list():
    alerts = _mock_alerts()
    assert isinstance(alerts, list)
    assert len(alerts) > 0


def test_mock_alerts_have_required_fields():
    for alert in _mock_alerts():
        assert alert.name
        assert alert.severity
        assert alert.namespace
        assert alert.pod
        assert alert.fingerprint


def test_mock_alerts_severities_valid():
    valid = {"critical", "warning", "info"}
    for alert in _mock_alerts():
        assert alert.severity in valid


# ── AI analyzer fallback tests ────────────────────────────────

def test_crash_loop_analysis():
    # Alert name contains "crash" → triggers crash runbook
    alert    = make_alert(name="KubePodCrashLooping")
    analysis = _rule_based_analysis(alert, "ERROR: exiting")
    assert isinstance(analysis, Analysis)
    assert analysis.root_cause
    assert len(analysis.immediate_steps) > 0
    assert "crash" in analysis.runbook_markdown.lower() or \
           "restart" in analysis.runbook_markdown.lower()


def test_imagepull_analysis():
    # Alert name contains "imagepull" → triggers imagepull runbook
    alert    = make_alert(name="KubeImagePullBackOff")
    analysis = _rule_based_analysis(alert, "unauthorized: authentication required")
    assert "image" in analysis.root_cause.lower() or \
           "pull" in analysis.root_cause.lower() or \
           "acr" in analysis.runbook_markdown.lower()


def test_waiting_container_gets_generic_analysis():
    # "KubeContainerWaiting" doesn't match crash/imagepull → generic fallback
    alert    = make_alert(name="KubeContainerWaiting")
    analysis = _rule_based_analysis(alert, "ImagePullBackOff logs")
    assert analysis.confidence == "low"
    assert analysis.runbook_markdown
    assert len(analysis.immediate_steps) > 0


def test_generic_analysis_fallback():
    alert    = make_alert(name="UnknownCustomAlert")
    analysis = _rule_based_analysis(alert, "some logs")
    assert analysis.confidence == "low"
    assert analysis.runbook_markdown


def test_runbook_contains_namespace():
    alert    = make_alert(namespace="my-namespace")
    analysis = _rule_based_analysis(alert, "logs")
    assert "my-namespace" in analysis.runbook_markdown


def test_runbook_contains_pod():
    alert    = make_alert(pod="my-pod-abc123")
    analysis = _rule_based_analysis(alert, "logs")
    assert "my-pod-abc123" in analysis.runbook_markdown


def test_analysis_has_all_fields():
    alert    = make_alert()
    analysis = _rule_based_analysis(alert, "logs")
    assert analysis.root_cause
    assert analysis.confidence in ("high", "medium", "low")
    assert isinstance(analysis.immediate_steps, list)
    assert analysis.runbook_markdown