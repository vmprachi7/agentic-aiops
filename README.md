# Agentic AIOps

An autonomous AI agent that watches Kubernetes alerts, fetches related logs,
and creates GitHub Issues with AI-generated root cause analysis and a draft runbook —
all without human intervention.

**The problem it solves:** When a pod crashes at 3am, someone gets paged.
They open the alert, dig through Prometheus, search Loki for logs, figure out
what's wrong, and write up an incident ticket. This agent does all of that automatically
the moment the alert fires — so when the on-call engineer wakes up, the Issue is already
there with root cause and remediation steps.

---

## How it works

```
Prometheus fires an alert (e.g. KubePodNotReady)
              ↓
Agent detects it on the next poll (every 60s)
              ↓
Queries Loki for the last 50 log lines from the affected pod
              ↓
Sends alert details + logs to Groq AI (Llama 3.1):
  "Here is the alert. Here are the logs.
   What is the root cause? What should the engineer do?"
              ↓
Creates a GitHub Issue:
  Title:   🔴 KubePodNotReady — sample-app-1/pod-abc123
  Body:    Alert details — severity, namespace, pod, started at

  Comment: 🤖 AI Analysis
           Root cause: Pod crashing due to missing env var APP_SECRET
           Confidence: high
           Immediate actions: ...
           📋 Draft Runbook (collapsible)
```

The runbook is in a collapsible `<details>` block — available without cluttering the Issue.
The engineer reads it, edits if needed, closes the Issue when resolved.


---

## Technology stack

| Component | Tool | Version | Why |
|---|---|---|---|
| **Alert source** | [Prometheus](https://prometheus.io) | kube-prometheus-stack | Industry standard Kubernetes monitoring — 200+ built-in alerting rules |
| **Log source** | [Loki](https://grafana.com/oss/loki/) | Grafana Loki | Log aggregation native to the kube-prometheus-stack, LogQL query language |
| **AI analysis** | [Groq](https://console.groq.com) + Llama 3.1 | llama-3.1-8b-instant | Free tier, <2s response time, provider-agnostic (swap to Azure OpenAI for prod) |
| **Issue management** | [PyGithub](https://github.com/PyGithub/PyGithub) | 2.1.1 | GitHub Issues as structured incident trail — searchable, linkable, closeable |
| **Runtime** | Python | 3.11 | Async-compatible, rich Azure + GitHub SDK ecosystem |
| **Container** | Docker | linux/arm64 | Matches Standard_B2ps_v2 AKS node (ARM processor — `p` in name) |
| **Orchestration** | Kubernetes (AKS) | 1.34 | Runs as a single-replica pod — prevents duplicate Issue creation |
| **GitOps** | ArgoCD | latest | Watches this repo, syncs changes to cluster automatically |
| **CI/CD** | GitHub Actions + OIDC | — | Passwordless auth, builds ARM image, updates manifest, triggers ArgoCD sync |
| **Deduplication** | File-based JSON tracker | — | Timestamp-based expiry — same alert doesn't spam Issues within 6h window |

---

## Screenshots

### Alert fired — GitHub Issue created automatically
![GitHub Issue created by agent](.github/screenshots/issue-created.png)

### AI root cause analysis + collapsible runbook
![AI analysis comment with runbook](.github/screenshots/ai-analysis-comment.png)

### Prometheus alerts page — KubePodNotReady firing
![Prometheus alerts](.github/screenshots/prometheus-alerts.png)

### Grafana alert rules — firing state
![Grafana firing alerts](.github/screenshots/grafana-alerts.png)

### Agent logs — processing alert in real time
![Agent processing alert](.github/screenshots/agent-logs.png)


---

## Architecture

```
AKS Cluster
    │
    ├── Prometheus  → scrapes metrics, fires alerts
    ├── Loki        → stores pod logs
    │
    └── agentic-aiops pod (always running, 1 replica)
              │
              every 60 seconds:
              │
              ├── GET /api/v1/alerts from Prometheus
              │     Filters out: system namespaces, AKS false positives,
              │     already-seen alerts (6h expiry window)
              │
              ├── For each NEW alert:
              │     ├── Query Loki → last 50 log lines for affected pod
              │     ├── Groq AI → root cause + confidence + runbook
              │     ├── Create GitHub Issue (alert notification)
              │     └── Add AI analysis as comment (runbook in collapsible)
              │
              └── Mark alert as seen → no duplicate Issues
```

---

## Repository structure

```
agentic-aiops/
├── agent/
│   ├── config.py            All settings — reads from env vars
│   ├── prometheus_client.py Queries Prometheus API for firing alerts
│   ├── loki_client.py       Fetches pod logs from Loki
│   ├── ai_analyzer.py       Groq AI root cause + rule-based fallback
│   ├── alert_tracker.py     Timestamp-based dedup — prevents duplicate Issues
│   ├── github_client.py     Creates Issue + adds AI runbook as comment
│   └── main.py              Main loop — polls every POLL_INTERVAL_SECONDS
├── k8s/manifests.yaml       AKS deployment + ArgoCD Application CRD
├── tests/test_agent.py      Unit tests
├── .github/workflows/
│   └── aiops-ci-cd.yml      Build linux/arm64 → push ACR → ArgoCD deploy
├── Dockerfile               linux/arm64 — matches Standard_B2ps_v2 node
├── one-time-setup.sh        Cluster setup — namespace, secrets, ArgoCD
├── requirements.txt
└── .env.example
```

---

## Quick start — run locally with mock data

No Kubernetes or Azure account needed. Mock alerts simulate
`CrashLoopBackOff` and `ImagePullBackOff` scenarios.

```bash
git clone https://github.com/vmprachi7/agentic-aiops.git
cd agentic-aiops

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env:
# GROQ_API_KEY=gsk_your-key-from-console.groq.com
# GITHUB_TOKEN=ghp_your-pat-with-repo-scope
# GITHUB_REPO=vmprachi7/agentic-aiops
# USE_MOCK_DATA=true

PYTHONPATH=. python agent/main.py
```

The agent will:
1. Detect two mock alerts — `KubePodCrashLooping` and `KubeContainerWaiting`
2. Fetch mock logs (simulated crash logs with real error messages)
3. Ask Groq AI for root cause
4. Create a real GitHub Issue in your repo with the AI runbook as a comment

Check your GitHub Issues tab — two Issues should appear within seconds.

---

## Run tests

```bash
USE_MOCK_DATA=true pytest tests/ -v
```

Covers: alert fingerprinting, dedup tracker, mock alerts, rule-based AI fallback,
runbook content validation.

---

## Deploy to AKS

### Prerequisites

- AKS cluster running (from [devops-platform-foundation](https://github.com/vmprachi7/devops-platform-foundation))
- Prometheus + Loki installed in `monitoring` namespace
- GitHub PAT with `repo` + `issues` scope

### Step 1 — One-time cluster setup

```bash
# Set required env vars first
export GROQ_API_KEY=gsk_your-key
export AIOPS_GITHUB_TOKEN=ghp_your-pat

bash one-time-setup.sh
```

This creates:
- `agentic-aiops` namespace
- `acr-secret` — allows AKS to pull from Azure Container Registry
- `aiops-secrets` — Groq key + GitHub token
- ArgoCD Application pointing at `k8s/` folder in this repo
- OIDC federated credentials for passwordless CI/CD

### Step 2 — Add GitHub Secrets

In `vmprachi7/agentic-aiops` → Settings → Secrets:

| Secret | How to get |
|---|---|
| `ARM_CLIENT_ID` | `az ad sp show --display-name terraform-sp --query appId -o tsv` |
| `ARM_CLIENT_SECRET` | Saved when SP was created |
| `ARM_TENANT_ID` | `az account show --query tenantId -o tsv` |
| `ARM_SUBSCRIPTION_ID` | `az account show --query id -o tsv` |
| `GROQ_API_KEY` | From [console.groq.com](https://console.groq.com) |
| `AIOPS_GITHUB_TOKEN` | GitHub PAT — `repo` + `issues` scope |

> **Why `AIOPS_GITHUB_TOKEN` and not `GITHUB_TOKEN`?**
> The built-in `GITHUB_TOKEN` in Actions cannot trigger other workflows.
> A separate PAT is required for the agent to create Issues.

### Step 3 — Add OIDC federated credentials

**portal.azure.com → App registrations → terraform-sp →
Certificates & secrets → Federated credentials**

| Name | Entity | Value |
|---|---|---|
| `github-aiops-main` | Branch | `main` |
| `github-aiops-pr` | Pull request | — |
| `github-aiops-production` | Environment | `production` |

### Step 4 — Push to deploy

```bash
git push origin main
```

Pipeline: test → build `linux/arm64` → push ACR → update manifest → ArgoCD sync → pod running.

### Step 5 — Verify

```bash
kubectl get pods -n agentic-aiops
# agentic-aiops-xxx   1/1   Running ✅

# Watch live logs
kubectl logs -n agentic-aiops -l app=agentic-aiops -f
```

---

## Test it — break something on purpose

The easiest way to trigger a real alert:

```bash
# Suspend ArgoCD selfHeal so it doesn't revert your change
argocd app set sample-app-1 --self-heal=false

# Break the image — triggers ImagePullBackOff
kubectl set image deployment/sample-app-1 \
  -n sample-app-1 \
  app=nginx:this-tag-does-not-exist

# Watch the pod fail
kubectl get pods -n sample-app-1 -w
```

Wait 5-10 minutes for Prometheus to fire `KubePodNotReady`.
The agent picks it up on the next poll and creates a GitHub Issue.

**Restore after testing:**
```bash
kubectl set image deployment/sample-app-1 \
  -n sample-app-1 \
  app=nginx:1.25-alpine

argocd app set sample-app-1 --self-heal=true
```

---

## Configuration reference

All settings via environment variables or `.env` file:

| Variable | Default | Description |
|---|---|---|
| `GROQ_API_KEY` | — | Required. From console.groq.com |
| `GITHUB_TOKEN` | — | Required. PAT with `repo` + `issues` scope |
| `GITHUB_REPO` | `vmprachi7/agentic-aiops` | Repo where Issues are created |
| `PROMETHEUS_URL` | In-cluster URL | Prometheus API endpoint |
| `LOKI_URL` | In-cluster URL | Loki API endpoint |
| `POLL_INTERVAL_SECONDS` | `60` | How often to check for new alerts |
| `ALERT_EXPIRY_HOURS` | `6` | Same alert won't create a new Issue within this window |
| `LOKI_LOG_LINES` | `50` | Log lines to fetch per alert |
| `LOKI_LOOKBACK_SECONDS` | `300` | How far back to look for logs (5 min) |
| `ALERT_SEVERITIES` | `critical,warning,info,none` | Which severities to process |
| `EXCLUDE_ALERTS` | AKS false positives | Comma-separated alert names to always skip |
| `USE_MOCK_DATA` | `false` | `true` = use simulated alerts + logs |

### Excluded alerts (AKS false positives)

These fire on every AKS cluster because Azure manages the control plane
components internally — the metrics are simply not exposed:

```
KubeSchedulerDown, KubeControllerManagerDown, KubeProxyDown,
Watchdog, KubeClientCertificateExpiration
```

They're excluded by default. Any genuine workload alert
(`KubePodNotReady`, `KubePodCrashLooping`, `KubeContainerWaiting` etc.)
passes through to create an Issue.

---

## Alert deduplication

The same alert firing continuously would spam GitHub Issues without deduplication.

The tracker stores `{fingerprint: timestamp}` in `/tmp/seen_alerts.json`:

```
fingerprint = alert_name + namespace + pod

KubePodCrashLooping-sample-app-1-pod-abc123 → seen at 09:00
```

If the same alert fires again within `ALERT_EXPIRY_HOURS` (default 6h),
it's suppressed — no new Issue. After 6 hours, a new Issue is created
(the alert is likely a different incident by then).

If the pod is fixed and the alert resolves, the 6h window doesn't matter —
the next time that pod crashes, it's a different fingerprint
(pod name changes on restart) so a new Issue is created immediately.

---

## GitHub Issue structure

```
Issue title:
  🔴 KubePodNotReady — sample-app-1/sample-app-1-8455c5c7bc-k8wvm

Issue body:
  | Field | Value |
  | Severity | warning |
  | Namespace | sample-app-1 |
  | Pod | sample-app-1-8455c5c7bc-k8wvm |
  | Started at | 2026-05-06T09:15:00Z |

  Summary: Pod has been in non-ready state for more than 15 minutes.

AI comment:
  🤖 AI Analysis ✅
  Root cause: Pod is stuck in ImagePullBackOff. The container image
  nginx:this-tag-does-not-exist does not exist in the registry.
  Confidence: high

  ⚡ Immediate Actions
  1. kubectl describe pod ... -n sample-app-1
  2. kubectl get events -n sample-app-1
  3. Fix the image tag and rollout restart

  📋 Draft Runbook (click to expand)
    ### Alert: KubePodNotReady
    ...full step-by-step runbook...
```

---

## ⚠️ Security notice — Groq AI in production

Alert titles, pod names, namespace names, and log lines are sent to Groq's API.

For most teams this is acceptable — Kubernetes alert names are not sensitive data.

For compliance-sensitive environments (SOC 2, ISO 27001):

**Option 1 — Azure OpenAI** (data stays in your tenant):
```python
# In agent/ai_analyzer.py — replace the Groq client:
client = OpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    base_url=f"{os.getenv('AZURE_OPENAI_ENDPOINT')}/openai/deployments/gpt-4o",
    default_headers={"api-key": os.getenv("AZURE_OPENAI_KEY")},
)
```

**Option 2 — Disable AI, use rule-based fallback:**
```bash
GROQ_API_KEY=   # leave empty — rule-based runbooks still work
```

---

## Why one replica matters

The agent runs as a single pod (`replicas: 1`). Running two replicas would
cause the same alert to be processed twice — two GitHub Issues for one incident.

The alert tracker is file-based (`/tmp/seen_alerts.json`) — it's local to
the pod and not shared across replicas. If you need high availability,
the tracker would need to be moved to Redis or another shared store first.

For a portfolio project and most production setups, a single replica with
Kubernetes restart policy is sufficient.

---

## Why GitHub Issues instead of PagerDuty / Opsgenie

In production, this agent would feed into PagerDuty or Opsgenie via webhook.
GitHub Issues were chosen for this portfolio because:

- Zero cost — no PagerDuty subscription needed
- Visible — anyone can see the Issues tab and understand what the agent does
- Durable — Issues build an incident history over time
- Linkable — PRs can reference Issues for traceability

The architecture supports swapping GitHub Issues for any ticketing system —
the `github_client.py` module is the only thing that would change.

---

## Related projects

Part of a DevOps + AI portfolio:

| Repo | What it does |
|---|---|
| [devops-platform-foundation](https://github.com/vmprachi7/devops-platform-foundation) | AKS + ArgoCD + Prometheus + Loki — the cluster this agent runs on |
| [finops-intelligence-engine](https://github.com/vmprachi7/finops-intelligence-engine) | Azure cost anomaly detection + AI recommendations |
| [security-auditor](https://github.com/vmprachi7/security-auditor) | Shift-left IaC scanning + Azure Policy enforcement |
| **agentic-aiops** (this repo) | Autonomous alert → AI root cause → GitHub runbook |

---

*Prachi · Senior DevOps & Platform Engineer · Gurugram, India*
*[LinkedIn](https://www.linkedin.com/in/prachi-v/) · [GitHub](https://github.com/vmprachi7)*
