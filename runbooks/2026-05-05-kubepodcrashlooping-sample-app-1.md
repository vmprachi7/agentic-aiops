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
The "sample-app-1-7d5f886b6-pfx7g" pod in namespace "sample-app-1" encountered a continuous restart loop.

### Root cause
The pod is restarting frequently due to a configuration error when initializing the application. Specifically, the required environment variable "APP_SECRET" is not set, causing the application to exit and loop infinitely.

### How to fix it

#### Step 1 — Verify the issue
```bash
kubectl get pods -n sample-app-1
kubectl describe pod sample-app-1-7d5f886b6-pfx7g -n sample-app-1
kubectl logs sample-app-1-7d5f886b6-pfx7g -n sample-app-1 --tail=50
```

#### Step 2 — Check configuration and environment variables
```bash
kubectl get configmap <configmap-name> -n sample-app-1 -o yaml
kubectl get secret <secret-name> -n sample-app-1 -o yaml
```
Check that the deployment YAML file and the corresponding Kubernetes Secret are properly configured and contain the required environment variable "APP_SECRET".

#### Step 3 — Correct configuration and environment variables
Update the deployment YAML file and the corresponding Kubernetes Secret to include the correct configuration and environment variable settings.

### How to verify it is fixed
Check the pod is running without crashing and the logs no longer show the "ConfigError: Required environment variable APP_SECRET not set" error.

### Prevention
To prevent this issue in the future, ensure the environment variables required by the application are properly set in the deployment YAML file and the corresponding Kubernetes Secret. Regularly review and update the configuration to avoid missing environment variables.

### Related alerts
- None.
