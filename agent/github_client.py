"""
GitHub client.
Creates a GitHub Issue for each firing alert.
Adds AI root cause + draft runbook as a comment on the same Issue.

No PRs — this is the production standard approach.
Runbooks are available inline, not cluttering the repo with branches.
"""
from datetime import datetime, timezone
from github import Github, GithubException
from agent import config
from agent.prometheus_client import Alert
from agent.ai_analyzer import Analysis


def create_alert_issue(alert: Alert, analysis: Analysis) -> str:
    """
    Create a GitHub Issue for the firing alert.
    Adds AI analysis + draft runbook as a comment.
    Returns the Issue URL.
    """
    gh   = Github(config.GITHUB_TOKEN)
    repo = gh.get_repo(config.GITHUB_REPO)

    severity_emoji   = {"critical": "🔴", "warning": "🟡"}.get(alert.severity, "🔵")
    confidence_emoji = {"high": "✅", "medium": "⚠️", "low": "❓"}.get(
        analysis.confidence, "⚠️"
    )

    # ── Create the Issue ──────────────────────────────────────
    title = (
        f"{severity_emoji} {alert.name} — "
        f"{alert.namespace}/{alert.pod}"
    )

    issue_body = f"""## {severity_emoji} Alert: {alert.name}

| Field | Value |
|---|---|
| **Severity** | `{alert.severity}` |
| **Namespace** | `{alert.namespace}` |
| **Pod** | `{alert.pod}` |
| **Started at** | {alert.starts_at} |

### Summary
{alert.summary}

### Description
{alert.description}

---
*Detected by [Agentic AIOps](https://github.com/{config.GITHUB_REPO}) · \
{datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}*
"""

    _ensure_labels(repo)
    issue = repo.create_issue(
        title=title,
        body=issue_body,
        labels=["alert", "automated"],
    )
    print(f"  ✅ Issue created: {issue.html_url}")

    # ── Add AI analysis + runbook as a comment ────────────────
    immediate = "\n".join(
        f"{i+1}. `{step}`"
        for i, step in enumerate(analysis.immediate_steps)
    )

    comment_body = f"""## 🤖 AI Analysis {confidence_emoji}

**Root cause:** {analysis.root_cause}
**Confidence:** `{analysis.confidence}`

### ⚡ Immediate Actions

{immediate}

---

<details>
<summary>📋 Draft Runbook — click to expand</summary>

{analysis.runbook_markdown}

</details>

---

> ⚠️ This analysis was generated automatically by Groq AI (Llama 3.1).
> Review before treating as authoritative — AI can be wrong.
> Edit and close this issue once resolved.
"""

    issue.create_comment(comment_body)
    print(f"  ✅ AI runbook added as comment")

    return issue.html_url


def _ensure_labels(repo):
    """Create labels if they don't exist."""
    existing = {l.name for l in repo.get_labels()}
    needed = [
        ("alert",     "e53e3e", "Firing Prometheus alert"),
        ("automated", "0075ca", "Created automatically by AIOps agent"),
    ]
    for name, color, desc in needed:
        if name not in existing:
            try:
                repo.create_label(name=name, color=color, description=desc)
            except GithubException:
                pass