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
The pod finops-engine-695fcf85bc-k9bp6 in the finops-engine namespace is experiencing a warning due to a container that has been in a waiting state for over an hour.

### Root cause
The container cannot pull the image 'devopsplatformacr.azurecr.io/finops-engine:latest' due to 'ImagePullBackOff' caused by authentication issues with Azure Container Registry.

### How to fix it

#### Step 1 — Verify the issue
```bash
kubectl get pods -n finops-engine
kubectl describe pod finops-engine-695fcf85bc-k9bp6 -n finops-engine
kubectl logs finops-engine-695fcf85bc-k9bp6 -n finops-engine --tail=50
```

#### Step 2 — Validate Azure ACR credentials
```bash
az acr login --name devopsplatformacr
az account show | grep clientId
az acr show --name devopsplatformacr --resource-group <resource_group> --query registryAccessToken
```

#### Step 3 — Update Kubernetes cluster credentials with Azure ACR credentials

### How to verify it is fixed
Verify the container in the pod finops-engine-695fcf85bc-k9bp6 can successfully pull the image and the pod status is 'Running'.

### Prevention
To prevent similar incidents, ensure that Azure ACR credentials are up-to-date and Kubernetes cluster credentials are synced with ACR credentials.

### Related alerts
- KubeContainerCrash
- KubePodUnhealthy
