# Instantly Shareable Playtest — Architecture

**Status:** Draft, grounded in actual code in the four backing services as of May 2026.
**Scope:** End-to-end design for routing a published Playtest into Xbox Cloud Gaming's streaming pipeline so authorized testers can stream a private build through a shareable link, with no install.

This document is **architecture-first**. Every claim about an existing service is anchored to a file path and line number in the relevant repo. Where the spec idealizes something that doesn't match reality, this document follows the code.

---

## 1. System Context

Four services participate. None of them owns the whole flow.

```
┌─────────────────────────┐                                ┌──────────────────────────────┐
│   xPlaytest (XBET)      │                                │   xCloud (Game Streaming)    │
│   MSFTGreen tenant      │                                │   Corp → PME tenant          │
│                         │                                │                              │
│   Xbox.Xbet.Service     │     ┌──────────────────┐       │  ┌─────────────────────┐   │
│                         │     │                  │       │  │ services.            │   │
│   PlaytestsController   │     │     SAGE         │       │  │ serviceapigateway   │   │
│        │                ├─────►  (Service API    ├───────┼──►  (HTTP proxy +       │   │
│        ▼                │ S2S │   Gateway)       │ S2S   │  │  route allow-list)   │   │
│   PlaytestBusinessLogic │     │                  │       │  └─────────┬───────────┘   │
│        │                │     │  Green→PME       │       │            │               │
│        ▼                │     │  cross-tenant    │       │            ▼               │
│   XPackagePlaytestPub-  │     │  auth required   │       │  ┌─────────────────────┐   │
│   lishWorkflow          │     └──────────────────┘       │  │ services.            │   │
│        │                │                                │  │ contentingestion    │   │
│        ▼                │                                │  │                      │   │
│   [Insert xCloud step]  │                                │  │ PlaytestTitle-       │   │
│                         │                                │  │ IngestionWorkflow    │   │
│                         │                                │  │  (new orchestrator)  │   │
│                         │                                │  │        │             │   │
│                         │                                │  │        │ chains      │   │
│                         │                                │  │        ▼             │   │
│                         │                                │  │ AssetIngestion-      │   │
│                         │                                │  │ Workflow             │   │
│                         │                                │  │ TitleIngestionWorker │   │
│                         │                                │  └─────────┬───────────┘   │
│                         │                                │            │ HTTP          │
│                         │                                │            ▼               │
│                         │                                │  ┌─────────────────────┐   │
│                         │                                │  │ services.            │   │
│                         │                                │  │ partnerregistry     │   │
│                         │                                │  │                      │   │
│                         │                                │  │ Offering write =     │   │
│                         │                                │  │ ADO PR               │   │
│                         │                                │  └─────────────────────┘   │
└─────────────────────────┘                                └──────────────────────────────┘
```

| Service | Repo | Role |
|---|---|---|
| xPlaytest | `Xbox.Xbet.Service` | Authoring + publish orchestration; sole originator of the cross-tenant trigger |
| SAGE | `services.serviceapigateway` | Ingress gateway for cross-tenant calls into xCloud; route + auth policy enforcement |
| Content Ingestion | `services.contentingestion` | New `PlaytestTitleIngestionWorkflow` that wraps existing ingestion + offering attach |
| Partner Registry | `services.partnerregistry` | Source of truth for `Offering` and title-attach state; writes go through ADO PRs |

---

## 2. End-to-End Flow

```
[Creator clicks Publish in Partner Center]
            │
            ▼
[Phase 1] xPlaytest                       PlaytestsController.cs:353-381
   POST /playtests/{id}/publish           (HTTP entry point)
            │
            ▼
   PlaytestBusinessLogic.PublishPlaytestAsync
   ├─ snapshot → PublishedPlaytestEntity
   ├─ resolve DNA groups via GMS → FlightIds
   └─ enqueue PlaytestPublishWorkflowType
            │
            ▼
   XPackagePlaytestPublishWorkflow        XPackagePlaytestPublishWorkflow.cs:59-67
   state machine:
     FetchingContentIds
       → populates PlaytestLifecycleState.ContentId, PackageFamilyName
     StartingContentSubmissionJob
     PollingContentSubmissionJob
       → populates streaming-ready version ids
     PlaytestProductCreation
       → writes to XProduct
     [NEW] XCloudIngestionTrigger          ← we insert here
     SuccessCompletion

[Phase 2] xPlaytest → SAGE → contentingestion
   POST {sage}/playtest/ingestion        (single cross-tenant call)
     body: PlaytestIngestionJobParameters
     auth: S2S, Playtest Service SPN from MSFTGreen
     →  202 Accepted { jobId }
            │
            ▼
[Phase 3] services.contentingestion
   PlaytestTitleIngestionWorkflow         (new — wraps existing primitives)
     1. validate inbound parameters + StoreAsset
     2. derive workflow fields
          PartnerId        = "PLAYTEST"
          OfferingId       = "xpt-{ToShortId(PlaytestId)}"   (≤ 32 chars)
          TitleId          = alphanumOnly(StoreAsset.Name) + PlaytestGeneratedXProductBigId   (see §5.3)
          Audiences        = AllowedDnaGroups → XusAudience(g, RetailSandboxId)
     3. chain AssetIngestionWorkflow
          uses pre-built StoreAsset (no xProduct call)
          generates AssetId, queues child AssetVersionIngestion jobs
     4. upsert Offering via partnerregistry HTTP API
          PUT v1/Offerings/{xpt-id}
          (creates ADO PR)
     5. attach Title via partnerregistry
          PUT v1/offerings/{id}/titles/{titleId}
          (creates ADO PR)
     6. poll install pipeline for capacity
            │
            ▼
[Phase 4] xCloud → xPlaytest
   xCloud reaches terminal state: Streamable | Failed | InstallNotFound
   xPlaytest polls SAGE status endpoint with jobId
     (callback is not viable — SAGE has no callback framework today)
   xPlaytest sets PlaytestStatus = StreamingReady (new enum value)
   Partner Center surfaces launch URL:
     play.xbox.com/play/launch/{productId}?offeringId=xpt-{id}
```

---

## 3. Service Responsibilities

### 3.1 xPlaytest — `Xbox.Xbet.Service`

**Owns:** publish trigger, payload assembly, status reconciliation, lifecycle re-triggering.

**Key existing primitives we plug into:**

| Concept | File | Notes |
|---|---|---|
| Publish HTTP endpoint | `src\PlayTest\PlayTest\Controllers\PlaytestsController.cs:353-381` | `[HttpPost("{playtestId}/publish")]` |
| Publish queueing | `src\PlayTest\PlayTest\BusinessLogic\PlaytestBusinessLogic.cs:994-1057` | `CreateJobAsync<PlaytestPublishJobParameters, ...>` |
| Workflow class | `src\XPackage\XPackageWorkflow\XPackageWorkflow\Workflows\Playtest\XPackagePlaytestPublishWorkflow.cs:74-85` | Exponential retry policy |
| State machine | same file, `:59-67` | `FetchingContentIds → StartingContentSubmissionJob → PollingContentSubmissionJob → PlaytestProductCreation → SuccessCompletion` |
| Job parameters | `src\XPackage\XPackageWorkflow\XPackageWorkflow.Shared\Workflows\PlaytestPublish\PlaytestPublishJobParameters.cs:10-36` | Has `FlightIds`, `PlaytestEndDate`, `IsGreenSigned`, `PlaytestGeneratedXProductBigId` |
| Lifecycle state | `src\XPackage\XPackageWorkflow\XPackageWorkflow.Shared\Models\Playtest\PlaytestLifecycleState.cs:5-20` | Has `PlaytestContentId`, `PackageFamilyName` |
| Status enum | `src\PlayTest\PlayTest.Shared\Constants\PlaytestStatus.cs:5-54` | **Does NOT include `StreamingReady` today** |
| Sandbox constant | `src\PlayTest\PlayTest\Constants\PackageConstants.cs:5-10` | `RetailSandbox = "RETAIL"` |
| Default platform constant | `src\XProduct\XProduct.Shared\Models\Playtest\PlaytestConstants.cs:7-15` | Lives in XProduct, **not** PlayTest |
| Product document builder | `src\XPackage\XPackageWorkflow\XPackageWorkflow\Workflows\Playtest\PlaytestProductDocumentBuilder.cs:53-70` | Currently hardcodes `XboxLiveTitleId = string.Empty` |

**What we add:**

1. **`XCloudIngestionTriggerState`** — new state inserted after `PlaytestProductCreation` and before `SuccessCompletion`. Calls the xCloud SAGE endpoint via a new typed HTTP client.
2. **`XCloudIngestionClient`** — new outbound HTTP client. No equivalent infrastructure exists today; all current `*Client.cs` in `Xbox.Xbet.Service` target internal services. The client must be wired with cross-tenant S2S credentials (see §6.1).
3. **`StreamingReady` status** — append to `PlaytestStatus`.
4. **`StoreAsset` builder** — translates `PublishedPlaytestEntity` + `PlaytestLifecycleState` + `PlaytestResponse` into the exact `StoreAsset` record xCloud expects. See §4.2 for the field-level map.
5. **`XboxTitleId` resolver** — currently no source; we wire it from XProduct (`alternateIds[XboxTitleId]` or `dimTitleProperties.titleId`). This is a P0 blocker because the xCloud-side validator rejects null/zero values for games.
6. **`AumID` resolver (PC only)** — sources `ApplicationId` from XProduct, concatenates `{PackageFamilyName}!{ApplicationId}`. Required by xCloud validator for PC games.
7. **Status reconciliation** — polls the SAGE status endpoint (see §6.3) and updates the playtest status. We default to polling; callbacks are not feasible without new SAGE infra.
8. **Lifecycle re-trigger** — `PlaytestBusinessLogic.UpdatePlaytestAsync` (`:408-553`) currently only persists. We add requeue logic for audience / expiry / build changes. Delete already has its own workflow at `:573-649`.
9. **Launch URL builder** — net new; no `play.xbox.com/play/launch/...` code exists today.

### 3.2 SAGE — `services.serviceapigateway`

**Owns:** route registration, S2S auth allow-list, request forwarding to `services.contentingestion`.

**Key existing primitives:**

| Concept | File | Notes |
|---|---|---|
| Route table | `src\Product\ServiceApiGateway\appsettings.xcloud.json:2-456` | Config-driven `ApiProxyConfig.BackendServices[*].Apis[*]` |
| Proxy controller | `src\Product\ServiceApiGateway\Controllers\ProxyController.cs:73-81` | Catch-all `[Route("{version}/{serviceRouteName}/{**path}")]` |
| Auth selection | same file, `:123-155` | `UsePmeAuth → ApProxyPmeBearerScheme`; `UseCrossTenantAuth → CombinedBearer`; else `DefaultBearer` |
| Per-route SPN allow-list | same file, `:274-315` | `api.AuthorizedClientAppIds.Contains(appId, ...)` |
| Error response shape | same file, `:255-270` | Custom `x-Proxy-Error` header — no `ProblemDetails` |
| Existing 202 pattern | (none) | Zero hits for `Accepted(`, `StatusCode(202)` in repo |
| Callback framework | (none) | Routes named "callback"/"webhook" exist as proxy targets, but no async orchestration layer |

**What we add:**

1. **Two new route entries** in `appsettings.xcloud.json` (and other env variants):
   - `POST /playtest/ingestion` → `services.contentingestion`
   - `GET /playtest/ingestion/{jobId}` → `services.contentingestion`
   Both entries include `AuthorizedClientAppIds = [<Playtest Service SPN>]` and `UseCrossTenantAuth = true`.
2. **No C# code change is expected** in this repo for route registration; the proxy is config-driven.
3. **202 Accepted handling** must be implemented on the downstream service — SAGE will forward whatever status code `services.contentingestion` returns, so the 202 contract lives there.

### 3.3 Content Ingestion — `services.contentingestion`

**Owns:** the new `PlaytestTitleIngestionWorkflow` and all xCloud-side ingestion + offering plumbing.

**Key existing primitives we wrap:**

| Concept | File | Notes |
|---|---|---|
| `StoreAsset` record | `src\Product\ContentIngestion.Contracts.External\Workflow\StoreAsset.cs:17` | `(StoreEntry, IReadOnlyCollection<Id> Markets, Id Platform, string ContentId, uint? XboxTitleId, string? PackageFamilyName, string? AumID)` |
| `StoreAsset.Validate()` | same file, `:25-61` | Throws if game and `XboxTitleId` null/zero; throws if PC game and `AumID` missing |
| `AssetIngestion.JobParameters` | `src\Product\ContentIngestion.Contracts.External\Workflow\AssetIngestion.cs:33-85` | Accepts `StoreAsset?` and `IReadOnlyCollection<XusAudience> Audiences` |
| `AssetIngestionWorkflow` | `src\Product\ContentCatalog.Ingestion.Core\Workflows\AssetIngestionWorkflow.cs:31-40` | Outer orchestration we chain into |
| Audience handling | same file, `:98-116` | Merges `Audiences` with managed flight IDs via `flightsProcessor.GetManagedFlightIdsAsync(...)` |
| Title attach worker | `src\Product\ContentCatalog.Ingestion.Worker\Core\TitleIngestionWorker.cs:165-195` | `[AsyncWorkflowState(AddTitleToCollectionState)]` calls `partnerRegistryClient.AddCollectionTitleAsync(...)` |
| Install ID resolution | same file, `:197-225` | `ContentInstallId.Generate(state.StreamingPackageIds.First())` |
| Workflow ingress | `src\Product\ContentCatalog.Ingestion.Service\Controllers\WorkflowsControllerV3.cs:17-46` | `POST v3/workflows/assetingestion`, `POST v3/workflows/assetversioningestion` |
| Partner registry integration | `src\Product\ContentCatalog.Ingestion.Service\Startup.cs:178-187` | `AddPartnerRegistryObjectTypeToCache<OfferingV2>()`, `AddPartnerRegistryHook<OfferingTitlesWithCollectionsHook>()` |
| Store change source | `src\Product\ContentCatalog.Ingestion.Core\Processors\Implementations\BigCatChangesEHProcessor.cs:24-75` | Only BigCat is wired; abstraction is `IStoreClient` |

**What we add:**

1. **`PlaytestIngestionJobParameters`** — new external contract type in `ContentIngestion.Contracts.External\Workflow\`. Mirrors §4.1.
2. **`PlaytestTitleIngestionWorkflow`** — new sealed class following `IIngestionWorkflow<PlaytestIngestionJobParameters>`. Stages:
   - `ValidateInput` — call `StoreAsset.Validate()`
   - `ScheduleAssetIngestion` — create child `AssetIngestion.JobParameters` from the inbound `StoreAsset` and `AllowedDnaGroups → Audiences`; schedule via `WorkflowsProcessor`
   - `PollAssetIngestion` — wait for terminal state
   - `UpsertOffering` — call partner registry `PUT v1/Offerings/xpt-{id}` with `AllowedDnaGroups`, `AllowedSandboxId`, `ExpirationTime`
   - `AttachTitle` — call partner registry `PUT v1/offerings/{id}/titles/{titleId}`
   - `PollInstallReadiness` — wait for capacity provisioning
   - `EmitTerminalState` — record `Streamable | Failed | InstallNotFound` against `jobId`
3. **`v3/workflows/playtestingestion`** controller route — accepts the new job parameters, returns `202 Accepted { jobId }`.
4. **`v3/workflows/playtestingestion/{jobId}`** GET — returns job state from the workflow framework.
5. **`PlaytestId.ToShortId()`** helper — does not exist today; needs to be added so `xpt-{ToShortId(guid)}` stays ≤ 32 chars (Offering id cap per `OfferingV2.cs:20-23`).
6. **DNA-group-as-flight-ID adapter (XC6)** — for the install pipeline lookup at `TitleIngestionWorker.cs:197-225`, pick the lexicographically smallest DNA group GUID as the deterministic flight identifier. Add an audit pass against the SUCU/allocator client to confirm it tolerates non-GA flights.

### 3.4 Partner Registry — `services.partnerregistry`

**Owns:** offering schema, title attach, ADO-PR-backed storage, expiration.

**Key existing primitives:**

| Concept | File | Notes |
|---|---|---|
| `OfferingV2` contract | `src\Product\PartnerRegistryClient\Contracts\OfferingV2.cs:18-224` | Has `ExpirationTime`, `AuthorizationOptions`. No sandbox field, no DNA group field today. |
| Offering id constraint | same file, `:20-23` | Max length 32. **`xpt-{full Guid}` (40 chars) fails — must use shortened form** |
| Resource path | same file, `:215-223` | `/Partners/{partnerId}/Offerings/{offeringId}` |
| Create / upsert route | `src\Product\PartnerRegistryService\Controllers\OfferingsController.cs:52-63` | `PUT v1/Offerings/{id}` |
| Attach single title | same file, `:98-111` | `PUT v1/offerings/{offeringid}/titles/{titleid}` |
| Delete offering | same file, `:65-70` | Used for teardown |
| Storage backend | `src\Product\PartnerRegistryService\Registry\RegistryProcessor{T}.cs:47-67, 73-99` | Every write becomes an ADO PR via `CreateGitPullRequestAsync(...)` |
| Bulk edit (for combining writes) | same file, `:128-167` | `BulkEditAsync` produces a single PR for multiple changes |
| Runtime read model | `src\Product\PartnerRegistryService\Registry\RegistryProvider.cs:62-75, 81-108` | In-memory `IRegistry`, not branch-aware |
| Expiration | `src\Product\PartnerRegistryService\Processors\OfferingExpirationBackgroundService.cs:36-45` | Hourly sweep uses `OfferingV2.ExpirationTime` |
| Existing auth-options pattern | `src\Product\PartnerRegistryService\Processors\TitlesProcessor.cs:143-145` | Reads `offering.AuthorizationOptions.AllowedCountries` |

**What we add:**

1. **`AllowedDnaGroups`** field on `PlayerAuthorizationOptions` — `ICollection<Guid>` (matching collection convention of other auth-options fields). Recorded as net-new because no `DnaGroup`/`Flight`/`Audience` field exists on offerings today.
2. **`AllowedSandboxId`** field on `PlayerAuthorizationOptions` — `string`, mirrors `AllowedCountries` shape.
3. **JSON schema migration** for stored offering documents (storage is git/ADO, not a DB, so this is a contract change not a SQL migration).
4. **Combined PR helper** — call `BulkEditAsync` from the Playtest path so offering create + title attach land in one PR (mitigates SFI self-approval blocker). The "staging branch" alternative is not viable today — `RegistryProvider` reads are not branch-aware (`RegistryProvider.cs:81-143`), so a staging branch would not be picked up by the runtime without significant new infra.
5. **Allow-list update** for `services.contentingestion`'s identity on the offering write routes (current auth gate at `OfferingsController.cs:62, 68, 108, 118, 126, 135` uses user-context bearer auth; service identity allow-list is missing).
6. **(Out of repo)** The DNA-group authorization check itself (`GsToken.DnaGroups` vs `offering.AuthorizationOptions.AllowedDnaGroups`) is NOT located in this repo — partner registry does not handle `GsToken`. The enforcement lives in the offering-access path of the streaming service. Partner registry's responsibility is only the data field.

---

## 4. Data Contracts

### 4.1 `PlaytestIngestionJobParameters` — xPlaytest → xCloud

The single payload sent through SAGE. Defined in `ContentIngestion.Contracts.External`.

```csharp
public record PlaytestIngestionJobParameters(
    Guid     PlaytestId,            // PublishedPlaytestEntity.PublishedPlaytestId
    string[] AllowedDnaGroups,      // PlaytestPublishJobParameters.FlightIds (resolved via GMS)
    DateTime ExpirationTime,        // PlaytestPublishJobParameters.PlaytestEndDate
    string   AllowedSandboxId,      // PackageConstants.RetailSandbox = "RETAIL"
    StoreAsset StoreAsset,          // see §4.2
    bool     IsGreenSigned)         // PlaytestPublishJobParameters.IsGreenSigned
{
    public void Validate() { /* required-field checks + StoreAsset.Validate() */ }
}
```

### 4.2 `StoreAsset` — built by xPlaytest, consumed by xCloud

**This is the existing record at `StoreAsset.cs:17` — we do not redefine it.** xPlaytest must produce values that pass `StoreAsset.Validate()` (`StoreAsset.cs:25-61`).

| Field | Type (actual) | Source on xPlaytest side | Notes |
|---|---|---|---|
| `StoreEntry.ProductId` | `string` | `PlaytestPublishJobParameters.PlaytestGeneratedXProductBigId` | Use the playtest-generated product id, not the retail product id |
| `StoreEntry.Flags` | `StoreProductFlags` | Constant `GAME` | |
| `StoreEntry.Name` | `string` | `PlaytestResponse.Name` | `PlaytestResponse.cs:11-41` |
| `StoreEntry.Description` | `string` | `PlaytestResponse.Description` | |
| `StoreEntry.PublisherId` | `string` | `PublishedPlaytestEntity.SellerId` | |
| `StoreEntry.IsPrivateAudience` | `bool` | `true` | |
| `StoreEntry.ParentProductIds` | `string[]` | `[]` | |
| `Markets` | `IReadOnlyCollection<Id>` | `[Id.Parse("US")]` | At least 1 required by validator |
| `Platform` | `Id` | `XProduct.Shared.Models.Playtest.PlaytestConstants.DefaultPlatform = "WINDOWS.DESKTOP"` | Validator accepts only `ServerPlatform.PC` or `ServerPlatform.Xbox` |
| `ContentId` | `string` | `PlaytestLifecycleState.PlaytestContentId` | |
| `XboxTitleId` | `uint?` | **NEW SOURCE NEEDED** — XProduct `alternateIds[XboxTitleId]` or `dimTitleProperties.titleId` | **Validator throws if null or 0 for games.** Today `PlaytestProductDocumentBuilder.cs:53-70` hardcodes empty string. P0 blocker. |
| `PackageFamilyName` | `string?` | `PlaytestLifecycleState.PackageFamilyName` | Required for PC by validator |
| `AumID` | `string?` | **NEW SOURCE NEEDED** — `{PackageFamilyName}!{ApplicationId}` where `ApplicationId` comes from XProduct | **Validator throws if null for PC games.** No `ApplicationId` source exists in xPlaytest today. P0 blocker for PC. |

`StoreEntry` is a re-export: `using StoreEntry = Microsoft.GameStreaming.Services.Common.Content.Ids.StoreEntry;` (`StoreAsset.cs:15`). The fields above match its public contract.

### 4.3 Derived inside `PlaytestTitleIngestionWorkflow`

These fields are **never sent by xPlaytest** — the workflow computes them.

| Field | Computation |
|---|---|
| `PartnerId` | Constant `Id.Parse("PLAYTEST")` |
| `OfferingId` | `$"xpt-{ToShortId(PlaytestId)}"`, must be ≤ 32 chars |
| `TitleId` | `<alphanumOnly(StoreAsset.StoreEntry.Name)><PlaytestGeneratedXProductBigId>` (see SPEC.md §5.3 — `OfferingId` is the catalog/auth key, `TitleId` is the install/streaming key; the two are intentionally distinct). |
| `SourceId` | `StoreAsset.ContentId` |
| `PackageNameOverride` | `StoreAsset.StoreEntry.Name` |
| `Audiences` | `AllowedDnaGroups.Select(g => new XusAudience(g, XusAudience.RetailSandboxId))` |
| `AssetId` | Generated by `AssetIngestionWorkflow` (`AssetIngestionWorkflow.cs:62-90`) |
| `StreamingPackageIds` | Generated by child `AssetVersionIngestion` jobs and surfaced via `AssetIngestion.JobStateV3` (`AssetIngestion.cs:90-157`) |
| `ContentInstallId` | `ContentInstallId.Generate(StreamingPackageIds.First())` (`TitleIngestionWorker.cs:209`) |
| Effective flight ID for SUCU lookup | Lexicographically smallest `AllowedDnaGroups[i]` GUID (XC6 deterministic choice) |

---

## 5. State Model

### 5.1 xPlaytest `PlaytestStatus`

```
Draft → Publishing → WaitingOnIngestion → Published → [NEW] StreamingReady
                                                ↘
                                      PublishFailed
Deleting → DeleteRetry → Deleted
```

`StreamingReady` is added in `PlayTest.Shared\Constants\PlaytestStatus.cs`. It is **distinct from** `Published` to allow Partner Center UI to differentiate "playtest ready to share" from "build packaged and stored." A playtest can be `Published` (build went through xPackage) without being `StreamingReady` (xCloud hasn't finished ingestion).

### 5.2 xCloud `PlaytestTitleIngestionWorkflow` terminal states

```
Streamable      — happy path; capacity provisioned; URL is launch-ready
Failed          — workflow exhausted retries; xPlaytest surfaces error to creator
InstallNotFound — install pipeline could not provision title; usually means
                  SUCU/allocator did not accept the DNA-group-as-flight-id
                  (see XC6). Distinct from Failed so we can show a targeted
                  error.
```

These are surfaced through `GET /playtest/ingestion/{jobId}` on SAGE.

---

## 6. Cross-Cutting Concerns

### 6.1 Cross-tenant S2S — Green → PME

**Problem:** Playtest Service runs in MSFTGreen. xCloud SAGE expects callers in Corp or PME. Out of the box, Green cannot call SAGE.

**Current state in code:**
- SAGE has a `UseCrossTenantAuth` route flag (`ProxyController.cs:123-155`) that swaps in `AuthScheme.CombinedBearer`, but the actual cross-tenant validation lives in shared auth libraries outside the SAGE repo.
- No evidence of Green-tenant acceptance anywhere in the four repos.

**Plan:**
- Track the ADO PR adding cross-tenant Green support (spec cites PR 15715445, but the title direction "Corp→Green" is inverted relative to the need — verify the actual PR ID and direction before locking the spec).
- Add the Playtest Service SPN to `AuthorizedClientAppIds` on the two new SAGE routes once the cross-tenant scheme is live.
- xPlaytest acquires a token for the xCloud audience via the standard MSAL flow.

### 6.2 ADO PR per write (SFI self-approval block)

**Problem:** Each partner registry write produces an ADO PR (`RegistryProcessor{T}.cs:47-67, 73-99`). The caller cannot self-approve under SFI. The naïve Playtest flow makes 2 PRs (offering write + title attach), both blocking on manual approval.

**Plan:**
- Use `BulkEditAsync` (`RegistryProcessor{T}.cs:128-167`) from `PlaytestTitleIngestionWorkflow.UpsertOffering + AttachTitle` so both writes land in **one PR**.
- A second-order mitigation (auto-approve policy for the playtest-specific path) is out of scope here and needs an SFI exception.
- The "staging branch services opt into reading" alternative from the spec is **not viable** — runtime reads at `RegistryProvider.cs:81-143` are not branch-aware. Adding branch-awareness would touch the registry read path globally and is a much larger change than the bulk-edit approach.

### 6.3 Terminal-state delivery — poll vs callback

**Decision:** Poll.

**Why:** SAGE today is request/response proxy only (`ProxyController.cs:73-155`). Existing routes named "callback" / "webhook" are just proxied paths, not an orchestration framework. Adding a callback layer in SAGE is a non-trivial gateway change. Polling fits the existing primitives:
- xPlaytest already polls Content Submission inside its own workflow (`XPackagePlaytestPublishWorkflow.cs:329-383`).
- SAGE can forward a `GET /playtest/ingestion/{jobId}` straight to `services.contentingestion`'s workflow state endpoint.

### 6.4 Read-time leakage of playtest metadata

**Problem:** Partner registry's `GET v1/Offerings/{id}` (`OfferingsController.cs:33-50`) returns full offering objects with **no auth filtering**. The success criterion "unauthorized users do not learn anything about the playtest from the launch link" is **not** enforceable by partner registry alone.

**Plan:**
- Partner registry holds the `AllowedDnaGroups` field but does not enforce it.
- Enforcement happens in the Bayside/streaming-token path (XC5 in the spec), which is outside the four repos here. Document that requirement explicitly so it is not assumed solved by adding the data field.

### 6.5 Identity stability

**Problem:** The spec uses `xpt-{PlaytestId}` as a stable offering id, but `PublishedPlaytestId` is the snapshot/publish-time identity (`PlaytestBusinessLogic.cs:776-805`). It is unclear whether the same `PublishedPlaytestId` is reused on republish or a new one is minted per snapshot.

**Plan:**
- Treat this as an open question; confirm with the xPlaytest team before implementation.
- If `PublishedPlaytestId` changes per republish, use the parent `PlaytestId` (the draft entity id) for the offering key, and pass the snapshot id only for tracing.
- Whichever id is chosen, run it through `ToShortId()` so `xpt-{...}` stays ≤ 32 chars.

---

## 7. P0 Blocker Checklist

These must be resolved before the integration can pass an end-to-end smoke test:

- [ ] **`XboxTitleId` source** wired in xPlaytest (XProduct lookup); fix `PlaytestProductDocumentBuilder.cs:53-70` to populate a real nonzero `uint`.
- [ ] **`ApplicationId` source** wired for PC builds (or v1 scope locked to Xbox).
- [ ] **`StreamingReady`** added to `PlaytestStatus` enum.
- [ ] **PT6 lifecycle re-trigger** — `UpdatePlaytestAsync` (`PlaytestBusinessLogic.cs:408-553`) queues a republish on audience / expiry / build changes.
- [ ] **Cross-tenant Green→PME** auth verified end-to-end; correct PR cited in spec.
- [ ] **Offering id length** — `ToShortId()` defined; verify `xpt-{shortId}` ≤ 32 chars.
- [ ] **Combined PR via `BulkEditAsync`** wired into the workflow.
- [ ] **`AllowedDnaGroups`** and **`AllowedSandboxId`** added to `PlayerAuthorizationOptions`.
- [ ] **XC6 SUCU audit** completed — DNA-group GUID accepted by install pipeline; `TitleIngestionWorker.cs:197-225` path validated.
- [ ] **Launch URL builder** implemented in xPlaytest / Partner Center surface.

---

## 8. Out-of-Scope / Deferred

- **Callback delivery** of terminal state (poll instead — §6.3).
- **Staging-branch reads** in partner registry (BulkEdit instead — §6.2).
- **GsToken DNA-group enforcement** (lives in the streaming-token / offering-access layer outside the four repos).
- **PC-specific content/config differences** flagged in the spec's open questions — needs a separate spike before v1 PC support.
- **`XProduct` direct read from xCloud** — explicitly avoided; xPlaytest fills the `StoreAsset` so the BigCat-only ingestion path stays untouched.

---

## 9. References

| Repo | Path |
|---|---|
| xPlaytest | `C:\Users\t-melanichen\source\repos\Xbox.Xbet.Service` |
| Content Ingestion | `C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\services.contentingestion` |
| SAGE | `C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\services.serviceapigateway` |
| Partner Registry | `C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\services.partnerregistry` |
