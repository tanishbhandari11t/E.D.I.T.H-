# Azure Deployment Plan

> **Status:** Approved (user executed plan) | Executing

Generated: 2026-08-21

---

## 1. Project Overview

**Goal:** Host Jimmy (Hermes fork) on Azure with exactly 4 password logins. Each login maps to an isolated Hermes profile (sessions, Telegram, memory). All four share one Azure OpenAI endpoint/API key and can chat simultaneously without chat overlap.

**Path:** Modernize Existing

---

## 2. Requirements

| Attribute | Value |
|-----------|-------|
| Classification | Production-ready POC |
| Scale | Small (4 concurrent users) |
| Budget | Cost-Optimized |
| **Subscription** | Azure subscription 1 (`ef27ac90-4a8e-4d2d-8de0-22d1924f023e`) |
| **Location** | eastus |

---

## 3. Components Detected

| Component | Type | Technology | Path |
|-----------|------|------------|------|
| Jimmy dashboard + agent | API + UI | Python FastAPI + React (web/) | repo root / Dockerfile |
| Azure OpenAI | External model | azure-foundry / gpt-5.6-sol | existing resource |
| Multi-user basic auth | Auth | plugins/dashboard_auth/basic | plugins/dashboard_auth/basic |

---

## 4. Recipe Selection

**Selected:** AZD + Bicep

**Rationale:** Existing multi-stage Dockerfile; Container Apps is the fit for long-lived agent + PTY + gateway multiplex. azd + Bicep matches Azure best practices.

---

## 5. Architecture

**Stack:** Containers (Azure Container Apps)

### Service Mapping

| Component | Azure Service | SKU |
|-----------|---------------|-----|
| Jimmy runtime | Container Apps | Consumption / 1 CPU 2Gi |
| Image | Azure Container Registry | Basic |
| Secrets | Key Vault | Standard |
| HERMES_HOME data | Container local disk (ephemeral) | — |

> **Note (2026-08-21):** Azure Files was removed from the Jimmy Container App.
> SQLite session DBs hang on SMB even with `journal_mode=delete`, which showed up
> as `/api/sessions` → `{"detail":"Internal server error"}`. Profiles are re-seeded
> on every boot (`JIMMY_SEED_PROFILES=1`). For durable storage later, use Azure Disk
> or an external DB — not Azure Files.

| Logs | Log Analytics | PerGB |

### Supporting Services

| Service | Purpose |
|---------|---------|
| Log Analytics | Centralized logging |
| Key Vault | API key, 4 passwords, auth HMAC secret |
| Managed Identity | ACR pull + Key Vault secrets |

### Multi-tenant model

- Profiles: `jimmy1` … `jimmy4` under `/opt/data/profiles/`
- Auth: `dashboard.basic_auth.users[]` with username → profile binding
- `gateway.multiplex_profiles: true`
- Shared `AZURE_OPENAI_*` from Key Vault

---

## 6. Provisioning Limit Checklist

### Phase 1: Resource Inventory

| Resource Type | Number to Deploy | Total After Deployment | Limit/Quota | Notes |
|---------------|------------------|------------------------|-------------|-------|
| Microsoft.App/managedEnvironments | 1 | 1 | OK | eastus |
| Microsoft.App/containerApps | 1 | 1 | OK | |
| Microsoft.ContainerRegistry/registries | 1 | 1 | OK | Basic |
| Microsoft.KeyVault/vaults | 1 | 1 | OK | |
| Microsoft.Storage/storageAccounts | 1 | 1 | OK | Files share |
| Microsoft.OperationalInsights/workspaces | 1 | 1 | OK | |

### Phase 2: Quota

Assumed sufficient on subscription 1 / eastus for single small ACA. Validate with `azd provision --preview` before apply.

---

## 7. Isolation contract

- Separate profile directories / state.db
- Session JWT/HMAC claim includes `profile`
- Middleware forces `?profile=` to bound profile; mismatch → 403
- UI hides profile switcher when bound
- Anti-overlap tests required

---

## 8. Execution steps

1. Multi-user basic auth + Session.profile + middleware bind
2. Jimmy UI (brand, chat home, lock profile)
3. Seed script for 4 profiles + azure/docker compose entry
4. infra/ Bicep + azure.yaml
5. Tests
6. azd up + smoke verify

---

## 9. Secrets (Key Vault)

- `azure-openai-api-key`
- `jimmy-basic-auth-secret`
- `jimmy1-password` … `jimmy4-password` (or precomputed hashes)
- Optional: `jimmyN-telegram-bot-token`
