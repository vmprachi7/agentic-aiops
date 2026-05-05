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
The pod `sample-app-1-7d5f886b6-pfx7g` in namespace `sample-app-1` is crash looping due to a configuration error.

### Root cause
The application is unable to start because it requires an environment variable `APP_SECRET` to be set. This is a configuration error that can be resolved by setting the correct environment variable.

### How to fix it

#### Step 1 — Verify the issue
```bash
kubectl get pods -n sample-app-1
kubectl describe pod sample-app-1-7d5f886b6-pfx7g -n sample-app-1
kubectl logs sample-app-1-7d5f886b6-pfx7g -n sample-app-1 --tail=50
```

#### Step 2 — Set the APP_SECRET environment variable
```bash
kubectl set env pod sample-app-1-7d5f886b6-pfx7g APP_SECRET=<secret_value> -n sample-app-1
```

#### Step 3 — Check if the pod is running and healthy
```bash
kubectl get pod sample-app-1-7d5f886b6-pfx7g -n sample-app-1 -w
```

### How to verify it is fixed
After setting the `APP_SECRET` environment variable, verify that the pod is no longer crash looping and is running and healthy.

### Prevention
To prevent this issue in the future, ensure that all required environment variables are set in the pod's configuration. Use a `preStart` hook to validate that the environment variables are set before starting the container.

### Related alerts
- None reported.
