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
The container in the finops-engine pod has been in a waiting state due to an ImagePullBackOff error, causing the pod to be unable to start.

### Root cause
The root cause of this incident is a failed image pull operation due to an unauthorized authentication error when connecting to the Azure Container Registry (ACR).

### How to fix it

#### Step 1 — Verify the issue
```bash
kubectl get pods -n finops-engine
kubectl describe pod finops-engine-695fcf85bc-k9bp6 -n finops-engine
kubectl logs finops-engine-695fcf85bc-k9bp6 -n finops-engine --tail=50
```

#### Step 2 — Update ACR credentials
```bash
az acr login --name devopsplatformacr
kubectl config set-credentials --local azure-devops-platformacr --username $(az identity get-access-token --resource=https://vsrm.dev.azure.com | jq -r '.token')
kubectl config set-cluster --local azure-devops-platformacr-cluster --server=$(az aks get-credentials --name finops-engine-aks --resource-group finops-group --output json | jq -r '.server')
```

#### Step 3 — Verify image existence and configuration
```bash
az acr repository show --name devopsplatformacr --image finops-engine
kubectl get imagepullsecrets -n finops-engine
kubectl get deployment finops-engine -n finops-engine -o yaml | grep registry
```

### How to verify it is fixed
Check that the finops-engine pod is successfully running and the image is being pulled correctly. Verify that there are no more ImagePullBackOff errors or warnings in the logs.

### Prevention
To prevent this issue in the future, ensure that ACR credentials are updated regularly and that the image pull process has the necessary permissions and configuration to access the Azure Container Registry.

### Related alerts
- KubeDeploymentConfigError
