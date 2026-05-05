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
The pod 'sample-app-1-7d5f886b6-pfx7g' in namespace 'sample-app-1' is crash looping due to missing configuration.

### Root cause
The pod is crash looping due to a missing configuration, specifically the environment variable APP_SECRET, which is required to initialise the application.

### How to fix it

#### Step 1 — Verify the issue
```bash
kubectl get pods -n sample-app-1
kubectl describe pod sample-app-1-7d5f886b6-pfx7g -n sample-app-1
kubectl logs sample-app-1-7d5f886b6-pfx7g -n sample-app-1 --tail=50
```

#### Step 2 — Update the deployment configuration to include the environment variable APP_SECRET
```bash
kubectl annotate deployment sample-app-1 -n sample-app-1 --set='env[APP_SECRET]=your-secret-value'
```

#### Step 3 — Verify the pod has been restarted and is running successfully
```bash
kubectl get pods -n sample-app-1
kubectl logs sample-app-1-7d5f886b6-pfx7g -n sample-app-1
```

### How to verify it is fixed
Check the pod status and logs to ensure it is running successfully and not crashing.

### Prevention
To prevent this in the future, ensure the environment variable APP_SECRET is set in the deployment configuration before deploying the application.

### Related alerts
- None.
