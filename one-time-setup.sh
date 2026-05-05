#!/bin/bash
# ═══════════════════════════════════════════════════════════
# AGENTIC AIOPS — ONE-TIME CLUSTER SETUP
# Passwordless — reads from environment variables
# Run: bash one-time-setup.sh
# ═══════════════════════════════════════════════════════════
set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Agentic AIOps — One-time cluster setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ── Validate env vars ─────────────────────────────────────────
MISSING=()
[[ -z "$ARM_CLIENT_ID" ]]       && MISSING+=("ARM_CLIENT_ID")
[[ -z "$ARM_CLIENT_SECRET" ]]   && MISSING+=("ARM_CLIENT_SECRET")
[[ -z "$ARM_TENANT_ID" ]]       && MISSING+=("ARM_TENANT_ID")
[[ -z "$ARM_SUBSCRIPTION_ID" ]] && MISSING+=("ARM_SUBSCRIPTION_ID")
[[ -z "$GROQ_API_KEY" ]]        && MISSING+=("GROQ_API_KEY")
[[ -z "$AIOPS_GITHUB_TOKEN" ]]  && MISSING+=("AIOPS_GITHUB_TOKEN")

if [ ${#MISSING[@]} -gt 0 ]; then
  echo "❌ Missing environment variables:"
  for v in "${MISSING[@]}"; do echo "   $v"; done
  echo ""
  echo "Add them to ~/.zshrc then: source ~/.zshrc"
  exit 1
fi
echo "✅ All environment variables present"
echo ""

# ── Connect to AKS ────────────────────────────────────────────
echo "Step 1 — Connecting to AKS..."
az aks get-credentials \
  --resource-group devops-platform-rg \
  --name devops-platform-aks \
  --overwrite-existing
kubectl get nodes
echo "✅ Cluster connected"
echo ""

# ── Create namespace ──────────────────────────────────────────
echo "Step 2 — Creating namespace..."
kubectl create namespace agentic-aiops \
  --dry-run=client -o yaml | kubectl apply -f -
echo "✅ Namespace ready"
echo ""

# ── Create ACR pull secret ────────────────────────────────────
echo "Step 3 — Creating ACR pull secret..."
ACR_PASSWORD=$(az acr credential show \
  --name devopsplatformacr \
  --query passwords[0].value -o tsv)
kubectl create secret docker-registry acr-secret \
  --namespace agentic-aiops \
  --docker-server=devopsplatformacr.azurecr.io \
  --docker-username=devopsplatformacr \
  --docker-password="$ACR_PASSWORD" \
  --dry-run=client -o yaml | kubectl apply -f -
echo "✅ ACR secret created"
echo ""

# ── Create app secrets ────────────────────────────────────────
echo "Step 4 — Creating app secrets..."
kubectl create secret generic aiops-secrets \
  --namespace agentic-aiops \
  --from-literal=GROQ_API_KEY="$GROQ_API_KEY" \
  --from-literal=GITHUB_TOKEN="$AIOPS_GITHUB_TOKEN" \
  --dry-run=client -o yaml | kubectl apply -f -
echo "✅ App secrets created"
echo ""

# ── Register repo in ArgoCD ───────────────────────────────────
echo "Step 5 — Registering repo in ArgoCD..."
ARGOCD_PASS=$(kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d)
kubectl port-forward svc/argocd-server -n argocd 8090:443 &
PF_PID=$!
sleep 8
argocd login localhost:8090 \
  --username admin --password "$ARGOCD_PASS" --insecure
argocd repo add https://github.com/vmprachi7/agentic-aiops || true
kubectl apply -f k8s/manifests.yaml
sleep 5
argocd app list
kill $PF_PID 2>/dev/null || true
echo "✅ ArgoCD registered"
echo ""

# ── Add OIDC federated credentials ───────────────────────────
echo "Step 6 — Adding OIDC federated credentials..."
SP_OBJECT_ID=$(az ad sp show --id "$ARM_CLIENT_ID" --query id -o tsv)

az ad app federated-credential create \
  --id "$SP_OBJECT_ID" \
  --parameters "{
    \"name\": \"github-aiops-main\",
    \"issuer\": \"https://token.actions.githubusercontent.com\",
    \"subject\": \"repo:vmprachi7/agentic-aiops:ref:refs/heads/main\",
    \"audiences\": [\"api://AzureADTokenExchange\"]
  }" 2>/dev/null || echo "ℹ️  github-aiops-main already exists"

az ad app federated-credential create \
  --id "$SP_OBJECT_ID" \
  --parameters "{
    \"name\": \"github-aiops-pr\",
    \"issuer\": \"https://token.actions.githubusercontent.com\",
    \"subject\": \"repo:vmprachi7/agentic-aiops:pull_request\",
    \"audiences\": [\"api://AzureADTokenExchange\"]
  }" 2>/dev/null || echo "ℹ️  github-aiops-pr already exists"

az ad app federated-credential create \
  --id "$SP_OBJECT_ID" \
  --parameters "{
    \"name\": \"github-aiops-production\",
    \"issuer\": \"https://token.actions.githubusercontent.com\",
    \"subject\": \"repo:vmprachi7/agentic-aiops:environment:production\",
    \"audiences\": [\"api://AzureADTokenExchange\"]
  }" 2>/dev/null || echo "ℹ️  github-aiops-production already exists"

echo "✅ OIDC credentials configured"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ One-time setup complete"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "GitHub Secrets to add:"
echo "  ARM_CLIENT_ID       = $ARM_CLIENT_ID"
echo "  ARM_TENANT_ID       = $ARM_TENANT_ID"
echo "  ARM_SUBSCRIPTION_ID = $ARM_SUBSCRIPTION_ID"
echo "  GROQ_API_KEY        = (from console.groq.com)"
echo "  AIOPS_GITHUB_TOKEN  = (your GitHub PAT)"
echo ""
echo "Also add production environment in Entra ID:"
echo "  portal.azure.com → App registrations → terraform-sp"
echo "  → Certificates & secrets → Federated credentials"
echo "  Name: github-aiops-production"
echo "  Entity: Environment → production"
echo ""
echo "Then: git push → pipeline deploys automatically"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"