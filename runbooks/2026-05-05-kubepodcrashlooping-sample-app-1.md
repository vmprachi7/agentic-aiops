# Runbook: KubePodCrashLooping

**Date:** 2026-05-05
**Severity:** critical
**Namespace:** sample-app-1
**Pod:** sample-app-1-7d5f886b6-pfx7g
**Alert fired at:** 2026-05-05T09:00:00Z

> ⚠️ This runbook was generated automatically by Agentic AIOps.
> Review and edit before treating as authoritative.

---

### Alert: KubePodCrashLooping

**Severity:** critical
**Affects:** sample-app-1/sample-app-1-7d5f886b6-pfx7g

### What happened
The pod sample-app-1-7d5f886b6-pfx7g in namespace sample-app-1 is crash looping, restarting frequently due to an application initialization error.

### Root cause
The pod's application is failing to start because of a missing required environment variable APP_SECRET.

### How to fix it

#### Step 1 — Verify the issue
```bash
kubectl get pods -n sample-app-1
kubectl describe pod sample-app-1-7d5f886b6-pfx7g -n sample-app-1
kubectl logs sample-app-1-7d5f886b6-pfx7g -n sample-app-1 --tail=50
```

#### Step 2 — Create or update environment variable setting
Update the deployment or pod configuration to set the APP_SECRET environment variable. You can do this by adding the following configuration to your deployment YAML:
```yaml
env:
  - name: APP_SECRET
    value: YOUR_APP_SECRET_VALUE
```
Replace YOUR_APP_SECRET_VALUE with the actual value.

### How to verify it is fixed
Check that the pod is running without crash looping and that the application is successfully initialized and running.

### Prevention
To prevent this issue in the future, ensure that all required environment variables are properly set in the Kubernetes deployment or pod configuration.

### Related alerts
- None
