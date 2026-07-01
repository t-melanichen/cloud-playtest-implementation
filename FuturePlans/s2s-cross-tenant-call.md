# Future plan: S2S cross-tenant call — implementation steps

**Why it matters:** The Playtest publish workflow cannot mark a cloud-streaming playtest ready until xPackage, running in the **MSFTGreen** tenant, can call the xCloud content-ingestion workflow in Corp through SAGE and then observe the workflow to terminal state. This plan is the authoritative home for the cross-tenant S2S / SAGE-integration task list.

## PR / branch
- **Flow:** xPackage (MSFTGreen) → **SAGE** (`services.serviceapigateway`, pass-through) → **services.contentingestion (CTIN)** in Corp.
- **SAGE external route:** `POST /v3/playtest/playtesttitleingestion` (alias `ctin`, path key `playtest`) forwards to CTIN `POST /v3/workflows/playtesttitleingestion` with `AuthPassThroughEnabled: true`.
- **CTIN authorization:** `[Authorize(AuthPolicyExtension.CrossTenantS2S)]` gates the playtest title ingestion endpoints.
- **Receiver auth:** services.contentingestion PR **15715445** (Lakshey, infra) plus PR **15905881** (gating the playtest endpoints, merged).
- **SAGE route:** services.serviceapigateway branch `t-melanichen/sage-playtest-ingestion-routes`, PR **15829639**.
- **xPackage payload builder:** Xbox.Xbet.Service branch `t-melanichen/playtest-ingestion-payload-builder` (commit `d64d116415e`).

## What this delivers
1. xPackage builds the `XCloudPlaytestTitleIngestionBuilder` payload.
2. xPackage acquires a Green-tenant token for CTIN's Green app-registration audience.
3. xPackage sends the token to SAGE; SAGE forwards the `Authorization` header unchanged.
4. CTIN selects the cross-tenant bearer scheme by JWT `aud`, validates the token against the Green tenant, checks the caller `appid` allowlist, starts `PlaytestTitleIngestionWorkflow`, and returns a workflow id.
5. xPackage stores/polls workflow status until terminal, following the existing Start*/Poll* retry state-machine pattern in `XPackagePlaytestPublishWorkflow`.

### Receiver scheduling semantics (confirmed 2026-06-30)

CTIN's `PlaytestTitleIngestion` is **not** caller-id idempotent (unlike the Greenbelt blade-leasing service). `WorkflowsProcessor.ScheduleJobAsync` creates each job with a server-generated `Id.NewGuid()`; the caller does not supply the job id, and `PlaytestId` is used only as `GetLockId()` — a concurrency lock that blocks *simultaneous* duplicate workflows. Implications for the caller (B1–B3):

- **Persist the returned workflow id and guard re-scheduling on it** (B3): a re-POST creates a *new* instance rather than returning the existing one, so without the guard a workflow re-entry after a failure/restart would orphan the first job.
- **Do not retry POST at the HTTP layer** — only GET (status) is safe to retry; a POST retry can spin up a second workflow.
- The returned `OperationStatus.Id` is always populated (the fresh GUID), so caller-side null-id handling is defensive only.

Source: services.contentingestion `WorkflowsProcessor.cs` (`CreateRequest(Id.NewGuid(), …)`), `PlaytestTitleIngestionWorkflow.CreateRequest` (`… parameters.GetLockId()`), contracts `IIngestionParameters.GetLockId` ("prevent multiple concurrent workflows with the same parameters").

---

## Steps

### A. Done — receiver + gateway foundations
- [x] **A1 — CTIN receiver auth is in place.** `ConfigureCrossTenantAuth` in services.contentingestion `Startup.cs` routes by JWT `aud`: Green app id → CrossTenantBearer validated against the Green tenant; otherwise HomeBearer. `CrossTenantS2S` then runs `ApplicationAuthorizationRequirement(AuthorizedClientIds, useStrictEnforcement:true)` and checks caller `appid` against the allowlist. `AllowWebApiToBeAuthorizedByACL = true`, so this is ACL/appid-based and does **not** need an app-role grant. — **PR 15715445** (Lakshey).
- [x] **A2 — Playtest endpoints are gated.** The two playtest title ingestion endpoints were gated with `[Authorize(AuthPolicyExtension.CrossTenantS2S)]`; the same PR changed the policy constant from `static readonly` to `const`. — **services.contentingestion PR 15905881** (merged, merge commit `52fab53`).
- [x] **A3 — SAGE pass-through route is ready.** The route uses alias `ctin`, path key `playtest`, and `AuthPassThroughEnabled: true`; SAGE's `DelegatedAuth` policy is `RequireAssertion` always-true and `ProxyController` forwards the caller `Authorization` header unchanged. — **services.serviceapigateway** branch `t-melanichen/sage-playtest-ingestion-routes`, **PR 15829639**.
- [x] **A4 — xPackage payload builder is ready.** `XCloudPlaytestTitleIngestionBuilder` builds the CTIN contract payload and adds the contracts package + Azure.Identity wiring. — **Xbox.Xbet.Service** branch `t-melanichen/playtest-ingestion-payload-builder`, commit `d64d116415e`.

### B. Caller client — actual outbound call
- [ ] **B1 — Add the content-ingestion/SAGE client.** The live `XPackagePlaytestPublishWorkflowJobStatusTopicProcessor.cs` only updates status today; it does not POST to SAGE or poll CTIN. Add a client that POSTs the `XCloudPlaytestTitleIngestionBuilder` payload to the SAGE route (`/.../v3/playtest/playtesttitleingestion`, alias `ctin`, path key `playtest`) and captures the returned workflow id.
- [ ] **B2 — Poll workflow status to terminal.** Add GET polling through the SAGE status route for the returned workflow id, and keep the playtest in waiting-for-ingestion until terminal. Follow the existing Start*/Poll* state-machine retry pattern used elsewhere in `XPackagePlaytestPublishWorkflow`.
- [ ] **B3 — Persist the operation id.** Store the CTIN/SAGE workflow id on `PublishedPlaytestEntity` so retries, long waits, and reconciliation can resume without starting duplicate ingestion.

### C. Token acquisition & caller credential
- [ ] **C1 — Acquire the CTIN-audience token from Green.** Authority: `https://login.microsoftonline.com/68cd85cc-e0b3-43c8-ba3c-67686dbf8a67`; scope: `<CTIN Green app id>/.default`.
- [ ] **C2 — Use the correct CTIN Green app ids.** Prod `33a17a2a-2834-4d46-9c22-040c5ceaca29`; Int `41db6237-8b6c-43b6-903e-b9e6ae5f3e09`; Test `893629d4-8f51-48d2-bdfc-16241481af3a`.
- [ ] **C3 — Use the xPackage Green caller app.** Prod `d60e3360-830b-4a09-b4bb-0f759ca83e06`; Int/Test `bf3fb5e5-6f18-40ef-b0e5-1403d2b9ac6d`. These are already in CTIN's `AuthorizedClientIds`.
- [ ] **C4 — Close the credential decision.** Anthony Keller / Brian Bowman are deciding certificate-in-Key-Vault vs MSI / workload-identity-federation. CTIN does **not** need Key Vault for receiving; only the xPackage caller needs a credential to mint the token.

### D. App-registration & config
- [ ] **D1 — Confirm caller app registrations in every env.** Verify the xPackage Green app exists in Test, Int, and Prod and that the chosen certificate or federated credential is registered on it.
- [ ] **D2 — Configure SAGE base URL and route names per env.** Add xPackage configuration for the SAGE base URL, route path, CTIN audience app id, caller app id, tenant id, and credential settings.
- [ ] **D3 — Verify the `aud` format gotcha.** CTIN's CombinedBearer selector literally compares `aud == AppId` (bare GUID). If AAD issues `aud = api://<guid>`, CTIN falls back to HomeBearer and returns 401. Request scope `<guid>/.default` and verify the token's `aud` is the bare GUID.

### E. Validation & ship
- [ ] **E1 — Deploy already-merged/branch PRs through CI/CICD.** Use CI/CICD deployments, not PR pipelines, for CTIN and SAGE before end-to-end validation.
- [ ] **E2 — Validate in Test end-to-end.** xPackage publishes → obtains Green token → POSTs through SAGE → CTIN authorizes with `CrossTenantS2S` → workflow starts → xPackage polls terminal status → playtest transitions correctly.
- [ ] **E3 — Validate Int, then Prod.** Repeat with env-specific CTIN app ids, caller app ids, SAGE URLs, and credentials.
- [ ] **E4 — Add failure-path validation.** Cover missing credential, wrong caller app id, wrong `aud`, SAGE 401/403/5xx, CTIN non-terminal/failed workflow status, and retry/resume behavior.

### F. Long-term / PME
- [ ] **F1 — Track the PME migration.** Green→Corp cross-tenant is interim. Long term, xCloud migrates to **PME**; ownership sits with the GSS platform team.
- [ ] **F2 — Revisit the caller auth model after PME.** Remove or simplify interim Green→Corp S2S configuration once the platform-owned PME path is ready.

## Owners
Melanie Chen (route wiring & xPackage caller) · Anthony Keller / Brian Bowman (cert-vs-MSI decision) · GSS platform team (long-term PME).

## References
- `SPEC.md` §6.1 and §7.
- `ARCHITECTURE.md` §3.2 and §6.1.
- services.contentingestion PR **15715445**.
- services.contentingestion PR **15905881**.
- services.serviceapigateway PR **15829639**.
- Source docs trimmed: [`Blockers/cross-tenant-s2s.md`](../Blockers/cross-tenant-s2s.md), [`Blockers/manual-pr-polling.md`](../Blockers/manual-pr-polling.md), [`FuturePlans/delete-tombstone-lifecycle.md`](./delete-tombstone-lifecycle.md), [`FuturePlans/launch-link-and-status-accuracy.md`](./launch-link-and-status-accuracy.md), [`Repos/services.serviceapigateway.md`](../Repos/services.serviceapigateway.md), [`Repos/services.contentingestion.md`](../Repos/services.contentingestion.md), [`Repos/Xbox.Xbet.Service.md`](../Repos/Xbox.Xbet.Service.md), [`Repos/services.auth.md`](../Repos/services.auth.md), [`Repos/services.devapi.md`](../Repos/services.devapi.md), [`Repos/services.partnerregistry.md`](../Repos/services.partnerregistry.md), [`Repos/README.md`](../Repos/README.md).
