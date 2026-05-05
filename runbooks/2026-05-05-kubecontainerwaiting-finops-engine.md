# Runbook: KubeContainerWaiting

**Date:** 2026-05-05
**Severity:** warning
**Namespace:** finops-engine
**Pod:** finops-engine-695fcf85bc-k9bp6
**Alert fired at:** 2026-05-05T08:30:00Z

> ⚠️ This runbook was generated automatically by Agentic AIOps.
> Review and edit before treating as authoritative.

---

### Alert: KubeContainerWaiting

**Severity:** warning
**Affects:** finops-engine/finops-engine-695fcf85bc-k9bp6

### What happened
The finops-engine container is waiting because it cannot pull the image due to authentication issues.

### Root cause
The root cause is an authentication failure when pulling the devopsplatformacr.azurecr.io/finops-engine:latest image. The logs indicate unauthorized access and back-off while trying to pull the image.

### How to fix it

#### Step 1 — Verify the issue
```bash
kubectl get pods -n finops-engine
kubectl describe pod finops-engine-695fcf85bc-k9bp6 -n finops-engine
kubectl logs finops-engine-695fcf85bc-k9bp6 -n finops-engine --tail=50
```

#### Step 2 — Retrieve ACR credentials and check them against the pull secret
```bash
az acr credential show --name devopsplatformacr --resource-group RESOURCEGROUPNAME --output json
kubectl get secret finops-engine-pull-secret -n finops-engine -o json
```

#### Step 3 — Manually test image pull
```bash
kubectl run -n finops-engine --image devopsplatformacr.azurecr.io/finops-engine:latest debug-test-pod
kubectl logs -f debug-test-pod
```

### How to verify it is fixed
Verify the finops-engine container is up and running, the image is correctly pulled, and the pod is stable.

### Prevention
Ensure proper configuration of Azure Container Registry (ACR) credentials and authentication in pull secrets for the finops-engine namespace, and regularly check registry credentials for any issues.

### Related alerts
- KubePodNotRunning
- KubeDeploymentNotReady
