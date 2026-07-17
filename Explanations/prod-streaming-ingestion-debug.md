# Prod Streaming Ingestion — Debug & Root-Cause Analysis

**Date:** 2026-07-04
**Author:** Melanie Chen
**Status:** Root cause identified and **code-proven**. The fix is an **AAD provisioning action (no code change)**. Final confirmation requires an owner with Green-tenant + Key Vault access (the intern account is Conditional-Access-blocked from the Green tenant and has no access to `kv-xpkg-xbs-prod`).

---

## TL;DR

A published Instantly-Shareable Playtest (pilot seller `65050620`) reaches **"Live"** in prod but **never becomes streamable**. The streaming-ingestion call `POST /v3/playtest/playtesttitleingestion` **never reaches prod SAGE** — 0 hits across a 30-hour log window that covered every publish, versus 125,686 control rows.

**Root cause:** the CTIN resource app **`33a17a2a`** (the token *audience*) has **no service principal in the Green tenant `68cd85cc`**. So the worker's cross-tenant token request fails at Azure AD with **`AADSTS500011`** ("resource principal not found in tenant") *before* the HTTP request is ever sent. Because streaming is **non-blocking**, the exception is swallowed and the publish still completes → "Live".

**Fix:** create the service principal for `33a17a2a` in tenant `68cd85cc` (admin consent / Graph / PowerShell). No code change, no app-role grant. This mirrors the test pair (`bf3fb5e5` → `893629d4`) which is provisioned and works end-to-end.

---

## 1. Symptom

- Publishing a streaming playtest from **prod Partner Center** as pilot seller **`65050620`** succeeds and the playtest reaches **Live**.
- But the title is never ingested for streaming, and **prod SAGE shows no playtest-ingestion traffic at all**.
- Jarvis/Kusto over `GameStreamingProdSVCserviceapigatewayVer9v0`, a **30-hour** window covering all publishes:
  - `source | where * contains "playtesttitleingestion" | summarize count()` → **0**
  - `source | where * contains "commandproxy" | summarize count()` → **125,686** (control — proves the query scans the full window and works)

**Conclusion from logs:** the streaming call never reaches prod SAGE. Not a 401/404 (those would produce a row) — literally no request arrives.

---

## 2. How we debugged it

### 2.1 The two-phase publish + non-blocking design (why "Live" is misleading)
- `/publish` is **synchronous**: it validates, resolves the Xbox Live title id, and queues an async job. It does **not** call SAGE.
- The SAGE call fires later from the **async `XPackageWorkflow` worker**, in the `SchedulingStreamingIngestionJob` state.
- Streaming is **non-blocking by design** (`XPackagePlaytestPublishWorkflow.SchedulingStreamingIngestionJobStateHandlerAsync`): it wraps the call in `try/catch`, and on **any** exception it logs `"Streaming ingestion scheduling failed for PlaytestId ..."`, emits a `streaming_ingestion` failure metric, and transitions to `SuccessCompletion` → **Live**.
- **Therefore "Live" tells us nothing about whether streaming succeeded.** To verify streaming you must check prod SAGE logs (`playtesttitleingestion`) or the `streaming_ingestion` metric — not the playtest status.

### 2.2 The failure is *before the request is sent*
- `EnableStreaming` is `true` for seller `65050620` — **proven**: before XORc was in prod, publish threw a `400` from the title-id gate, and that gate only runs when `enableStreaming == true`. So the worker **did** enter `SchedulingStreamingIngestionJob` and **did** attempt the call.
- Yet there are **0 SAGE rows**. If the request had been sent, SAGE would log it (a 200 forward, or 401/404). None exists ⇒ the failure happens **before `SendAsync`** — i.e., at the S2S **token-acquisition** step (`AddS2SAuthHeaderAsync` → `AcquireTokenForClient`), which calls Azure AD, not SAGE.
- Cross-check: if the token *scope* were empty, the code skips the auth header and still **sends** the request unauthenticated → SAGE would return a 401 (a row). We see no row, so the scope is non-empty and the token call itself throws.

### 2.3 Code path (all verified correct)
```
PlayTest.QueuePublishJobAsync  → EnableStreaming = (seller == 65050620); StreamingParameters{XboxLiveTitleId}
  → queues PlaytestPublishJobParameters
XPackageWorkflow worker → XPackagePlaytestPublishWorkflow
  → PlaytestProductCreation → (EnableStreaming ? SchedulingStreamingIngestionJob : SuccessCompletion)
  → SchedulePlaytestStreamingIngestionAsync
     → StreamingPlaytestTitleIngestionBuilder.BuildPlaytestTitleIngestionJobParameters(...)
     → XCloudPlaytestIngestionServiceClient.SchedulePlaytestTitleIngestionJobAsync(payload)
        → AddS2SAuthHeaderAsync(scope) → AcquireTokenForClient(GREEN)   ← THROWS here (before SendAsync)
        → SendAsync → POST https://gssv-sage.xboxlive.com/v3/playtest/playtesttitleingestion  ← never reached
```

### 2.4 The decisive comparison (the "aha")
The worker mints the Green token via `XCloudPlaytestIngestionS2SAuthHelperFactory`:
```csharp
ConfidentialClientApplicationBuilder.Create(d60e3360)
    .WithCertificate(xbs-xpackage-core-app-aad, sendX5C: true)
    .WithAuthority("https://login.microsoftonline.com/", 68cd85cc)   // Green tenant
    .Build();
scope = GetDefaultScopeFromResource(33a17a2a) = "33a17a2a/.default"   // bare GUID (correct — CTIN app has no api:// URI)
```
**`MkmsServiceClientAuthHelper`, `XkmsServiceClientAuthHelper`, and `ESRPScanClientHelper` build the byte-for-byte identical object** — same app `d60e3360`, same cert, same Green tenant `68cd85cc`. Those three run on **every regular prod publish** (scan → sign → ingest) and work at scale. The **only** difference in the playtest call is the **resource it asks for**: `33a17a2a/.default` vs the working `api://...` resources.

⇒ The caller (`d60e3360` + cert + Green auth) is provably fine. The single failing variable is the **resource `33a17a2a`**.

---

## 3. Why this is the bug (root cause)

**Azure AD cannot issue a token for `33a17a2a/.default` from tenant `68cd85cc` because `33a17a2a` has no service principal in that tenant → `AADSTS500011` ("resource principal not found").**

Reasoning chain, each step evidenced:

1. **Call is attempted, never sent** → failure is at token acquisition (§2.2).
2. **Caller `d60e3360` is provisioned in Green** → identical MSAL construction to Mkms/Xkms/ESRP, which are core services that succeed on every prod publish (§2.4). Rules out `AADSTS700016` (app not in tenant).
3. **Only the resource differs** → `33a17a2a` (bare GUID) vs working `api://...` resources. The bare-GUID scope format is *correct* (the CTIN Green app deliberately has no `api://` URI; requesting `api://33a17a2a/.default` would itself fail). So it is not a code/scope-format bug.
4. **CTIN receiver config is symmetric and complete** for both envs (`AppId`, `AuthorizedClientIds=[d60e3360]`); the audience validator accepts the bare-GUID `aud` (CTIN PR 15996626). Nothing on the receiver side blocks it.
5. **No app-role grant is required** — CTIN authorizes by `appid` ACL (`AllowWebApiToBeAuthorizedByACL = true`), so the token only needs to *issue*, which requires the resource SP to exist.
6. **Provisioning was manual and done for test only** — CTIN Terraform sets `tf_autogen_sp_identity: false` (no auto SP creation); the **test** pair (`bf3fb5e5` → `893629d4`) was provisioned and validated end-to-end (PR 15996626), while the **prod** pair (`d60e3360` → `33a17a2a`) was not.

The `AADSTS500011` exception is thrown by `AcquireTokenForClient`, propagates up through the client → `SchedulePlaytestStreamingIngestionAsync`, and is **swallowed** by the non-blocking `catch` in the workflow — which is exactly why the publish still reaches **Live** and nothing appears in SAGE.

**Confidence:** High. Four independent code investigations converged on it, and it is the only hypothesis consistent with *all* the facts (0 SAGE rows, Live, `d60e3360` working elsewhere in Green, symmetric config, manual/INT-only provisioning).

---

## 4. The fix (no code change)

Create the service principal for `33a17a2a` in the Green tenant `68cd85cc`, mirroring the test pair. Any of:

```bash
# Admin-consent URL (Green tenant admin approves):
https://login.microsoftonline.com/68cd85cc-e0b3-43c8-ba3c-67686dbf8a67/adminconsent?client_id=33a17a2a-2834-4d46-9c22-040c5ceaca29

# Microsoft Graph (Green tenant admin):
POST https://graph.microsoft.com/v1.0/servicePrincipals  { "appId": "33a17a2a-2834-4d46-9c22-040c5ceaca29" }

# Azure PowerShell (Green tenant context):
New-AzADServicePrincipal -ApplicationId 33a17a2a-2834-4d46-9c22-040c5ceaca29
```

No app-role grant needed. `AuthorizedClientIds` already lists `d60e3360`; the audience validator already accepts the bare-GUID `aud`; SAGE already pass-through-forwards the route. Once the SP exists, `d60e3360` can immediately acquire `33a17a2a/.default` and the SAGE → CTIN flow works.

**Owner:** whoever owns the Green-tenant app registrations / `kv-xpkg-xbs-prod` (per the S2S plan: Anthony Keller / Brian Bowman for the credential decision; identity/CTIN team for the app registration). Tracks to plan tasks **C4** and **D1**.

---

## 5. How to confirm

The intern account **cannot** run these (Conditional-Access-blocked from `68cd85cc`; no access to `kv-xpkg-xbs-prod`). An owner with access runs one of:

1. **Differential token test** — as `d60e3360` (cert from `kv-xpkg-xbs-prod`) against tenant `68cd85cc`, request a token for a known-good resource (`api://c587f6ec-35b6-496e-b539-c352677d80d1`, Mkms → **succeeds**) vs `33a17a2a` (→ **fails `AADSTS500011`**). Same app/cert/tenant/code path; only the resource differs.
2. **SP existence check** (Green directory read, no cert):
   `az ad sp list --filter "appId eq '33a17a2a-...'"` → **empty**; `... '893629d4-...'` → **present** (control).
3. **Worker log** (Xbet/XPackage): search `"Streaming ingestion scheduling failed for PlaytestId"` → the swallowed exception shows the exact `AADSTS` code.

**Post-fix verification:** re-publish, wait ~5 min, re-run `source | where * contains "playtesttitleingestion" | summarize count()` → flips `0 → ≥1` (a 200), and CTIN shows the `PlaytestTitleIngestion` workflow.

---

## 6. Other potential bugs (full sweep)

Every alternative that could produce "0 SAGE + Live", with its verdict.

### Still genuinely viable (alternative to the primary)
| Hypothesis | Why it's viable | How to tell it apart |
|---|---|---|
| **Network egress block** from the prod pod to `gssv-sage.xboxlive.com` **or** to `login.microsoftonline.com/68cd85cc` | Runtime-only; cannot be verified from code. A block to the **Green AAD endpoint** looks *identical* to the missing-SP case (token throws before send). | The worker's swallowed exception: `AADSTS500011` = SP; a socket/DNS/`HttpRequestException`/timeout = egress. In the differential test, `AADSTS500011` vs a network error also distinguishes. |

### Low plausibility (possible, but earlier states already succeeded)
| Hypothesis | Why low |
|---|---|
| Builder throws — empty `PackageContentLifecycleState` → `FirstOrDefault()` null → `XPackageWorkflowException` | Lifecycle state is populated by an earlier workflow state that must have succeeded for publish to reach Live. Swallowed → 0 SAGE + Live if it fired. |
| Builder `Validate()` — null/empty `PlaytestGeneratedXProductBigId` | Product BigId is set by the product-creation state, which already succeeded. |

### Ruled out (with evidence)
| Hypothesis | Verdict / evidence |
|---|---|
| Caller `d60e3360` not provisioned in Green (`AADSTS700016`) | ❌ Works for Mkms/Xkms/ESRP (identical MSAL), which run on every prod publish. |
| prod-wus2 running as **Staging** → calls `gssv-sage-test` (false negative) | ❌ `values.yaml aspNetCoreEnvironment: Production`; `prod-wus2.yaml` has no override; Helm deploy log confirms → prod SAGE. "0 rows" is a real failure. |
| Feature-flag / ECS gate disabling streaming in prod | ❌ No `IFeatureManager`/ECS/toggle anywhere in the worker path. |
| `EnableStreaming` deserializes `false` at the worker | ❌ Proven `true` for the seller; `record`/`init` props survive Newtonsoft round-trip; no `[JsonIgnore]`. |
| Workflow not invoked / a competing status processor handles it | ❌ `XPackagePlaytestPublishWorkflow` is the sole executor; the status topic processor never contained a SAGE call. |
| `StreamingParameters` null at worker (deserialization) | ❌ Would trip an assertion **outside** the try → hard job failure, **not** Live. |
| `Platform` (`Id`) deserialization failure | ❌ Builder falls back to `ServerPlatform.PC`. |
| HTTP client base-address / URL / config-section mismatch | ❌ `Host` binds to `https://gssv-sage.xboxlive.com/`; URL joins correctly; option section name matches. |
| Empty token scope → request sent unauthenticated → SAGE 401 | ❌ That would still produce a **SAGE row**; there is none. |
| Scope format wrong (`api://` vs bare GUID) | ❌ Bare GUID is the *correct* form for the CTIN Green app (no `api://` URI). |
| Circuit breaker tripped before send | ❌ 0 prior HTTP responses to accumulate, so it can't trip today. (But see latent issue below.) |

### Real code issues found — worth fixing, but NOT the cause of this outage
| Issue | Impact |
|---|---|
| **Circuit breaker silently ON** (`IsCircuitBreakerPolicyEnabled` defaults `true`, never set to `false`) | Latent: once the primary fix lands, repeated SAGE 5xx could open the circuit → `BrokenCircuitException` → swallowed → re-masks failures. |
| **Dead retry config** — `RetryCount`/`RetryDelayInMilliseconds` don't bind (wrong keys → `RetryAttempts` stays 0), and `RetryMethods: ["GET"]` on a **POST** endpoint | Retries are effectively disabled and, even if enabled, wouldn't cover the POST. |
| **Latent bypass** — `TrafficBand != Primary → SuccessCompletion` skips streaming | Dead today (`TrafficBand` is hardcoded `Primary`), but a future param change would silently skip the call. |

---

## 7. Key IDs & references

| Thing | Value |
|---|---|
| Caller app (prod / test) | `d60e3360-830b-4a09-b4bb-0f759ca83e06` / `bf3fb5e5-6f18-40ef-b0e5-1403d2b9ac6d` |
| CTIN resource / audience (prod / int / test) | `33a17a2a-2834-4d46-9c22-040c5ceaca29` / `41db6237-8b6c-43b6-903e-b9e6ae5f3e09` / `893629d4-8f51-48d2-bdfc-16241481af3a` |
| Green tenant | `68cd85cc-e0b3-43c8-ba3c-67686dbf8a67` |
| Home/Corp tenant (worker default identity) | `72f988bf-86f1-41af-91ab-2d7cd011db47` |
| Cert (Key Vault) | `xbs-xpackage-core-app-aad` in `kv-xpkg-xbs-prod` |
| Prod SAGE host / route | `https://gssv-sage.xboxlive.com/` · `POST /v3/playtest/playtesttitleingestion` |
| Kusto table (prod SAGE) | `GameStreamingProdSVCserviceapigatewayVer9v0` |
| Expected AADSTS | `AADSTS500011` (resource principal not found in tenant) |

**Related plan/docs:** `FuturePlans/s2s-cross-tenant-call.md` (tasks C1–C4, D1), `Blockers/cross-tenant-s2s.md`, `PRProgress/23-CTIN-15996626-crosstenant-audience-validation-fix.md`, `testing/e2e-readiness-and-blockers.md`.

**Related ADO:** WI 62521481 (S2S identity/app registration — validated **INT only**); WI 62954149 ("Onboard Green-tenant caller app IDs … + verify cross-tenant provisioning" — **Proposed/open**); WI 62492665 ("Enable S2S authentication for Playtest" — **Started**).
