# Instantly Shareable Playtest — End-to-End Flow & xCloud Ingestion Deep Dive

A full walkthrough of the Instantly Shareable Playtest project: what each repository does, how a build
travels from a creator's "Enable Cloud Streaming" toggle all the way to a tester streaming it, and a
stage-by-stage dissection of the xCloud ingestion workflow (`PlaytestTitleIngestionWorkflow` in
`services.contentingestion`).

> **One-line summary:** a creator flips *Enable Cloud Streaming* on an xPlaytest, and instead of testers
> downloading a hundreds-of-GB build, the RETAIL-signed build is ingested into Xbox Cloud Gaming as a
> private, DNA-group-gated offering that approved testers stream from a shareable link — no install.

---

## 1. The cast of repositories

| Repo | ADO project | Role in the flow |
|---|---|---|
| **Xbox.Gpx.PartnerCenter.Client** | microsoft/Xbox | Partner Center **creator UI** (GPM). The *Enable Cloud Streaming* toggle, the 30-day max-duration cap for streaming playtests, and the Xbox-Live-ID-only audience restriction. *(front-end, in progress)* |
| **Xbox.Xbet.Service** | microsoft/Xbox | **xPlaytest / xPackage** — the publish workflow (`XPackagePlaytestPublishWorkflow`). Resolves the Xbox Live Title ID, builds the `StoreAsset` + `PlaytestIngestionJobParameters`, fires the xCloud trigger, calls SAGE, and polls for status. **This is the caller.** |
| **xorc** | microsoft/Xbox.Services | **XORc** service-config read API. Exposes the numeric **Xbox Live Title ID** on `GET /products/{id}/xboxliveconfig` so xPlaytest can thread it onto `StoreAsset.XboxTitleId`. |
| **services.serviceapigateway** | microsoft/Xbox.Streaming | **SAGE** — the gateway. Proxies the cross-tenant (MSFTGreen → Corp) `POST/GET /v3/playtest/playtesttitleingestion[/{jobId}]` routes from xPlaytest to content ingestion, forwarding the caller token. |
| **services.contentingestion** | microsoft/Xbox.Streaming | **GSSV ingestion** — receives the request (gated by `CrossTenantS2S`), runs the **`PlaytestTitleIngestionWorkflow`**, and tracks the job. **This is the receiver / the deep dive below.** |
| **services.partnerregistry** | microsoft/Xbox.Streaming | **Offering + title** store. `ConfigurePlaytestAsync` writes the DNA-group-gated private **offering and attaches the title in a single Partner Registry PR**. Owns the `xpt{PlaytestProductId}` offering-id convention and `AllowedDnaGroups`. |
| **services.auth** | microsoft/Xbox.Streaming | Enforces `AllowedDnaGroups` + the gamertag claim during offering **login** (`/v2/login/user/delegated`) so DNA-group auth surfaces in a user's `/offerings` response (and non-members see nothing). |
| **services.devapi** | microsoft/Xbox.Streaming | **DevApi Reader portal** — the Allowed-DNA-Groups offering UI and the playtest-ingestion **testing** UI (trigger + poll the workflow by hand). |
| **services.data.partnerregistry** | microsoft/Xbox.Streaming | Test data (`OfferingV2.json`, the `DNATEST` allowed group). |
| **services.pcservices** (PC Orchestrator) | microsoft/Xbox.Streaming | The **PC server orchestrator** the ingestion workflow queries to confirm a PC server has staged the exact ingested version. *(dependency, not modified)* |
| **Xbox.JS** | microsoft/Xbox | **Bayside** player-side cloud-gaming client — the shareable link lands here; login-first, then the private offering streams. *(front-end, planned)* |

---

## 2. The end-to-end flow (creator → tester)

Each hop names the repo doing the work.

1. **Enable streaming (Partner Center · `Xbox.Gpx.PartnerCenter.Client`).** The creator creates a playtest
   and toggles **Enable Cloud Streaming**. Streaming playtests are capped at a 30-day duration and the
   audience is restricted to Xbox-Live-backed DNA groups. *(Behavior is purely additive — the existing
   download playtest flow is unchanged.)*
2. **Publish a build (xPlaytest · `Xbox.Xbet.Service`).** When a build is published to a cloud-enabled
   playtest, `XPackagePlaytestPublishWorkflow` runs. After it creates the XProduct, it:
   - resolves the numeric **Xbox Live Title ID** from **XORc** (`xorc`), and
   - (gated on the pilot seller — see `StreamingIngestionPilotSellerId`) calls
     `TrySchedulePlaytestStreamingIngestionAsync`.
3. **Build the payload (`Xbox.Xbet.Service`).** `XCloudPlaytestTitleIngestionBuilder` assembles a
   `PlaytestIngestionJobParameters`: the `StoreAsset` (title/content ids, package refs, platform,
   `XboxTitleId`), the full `AllowedDnaGroups` set, the sandbox, and the expiration time.
4. **Send via SAGE (`services.serviceapigateway`).** The xbet ingestion client POSTs the payload to the
   SAGE route `v3/playtest/playtesttitleingestion`. SAGE proxies it **cross-tenant** (MSFTGreen → Corp),
   forwarding the caller token to `services.contentingestion`.
5. **Receive & schedule (`services.contentingestion`).** `WorkflowsControllerV3` accepts the POST
   (authorized by the `CrossTenantS2S` policy), schedules the `PlaytestTitleIngestionWorkflow`, and returns
   **`200 OK` carrying an `OperationStatus` whose `Id` is the `jobId`**.
6. **Ingest & configure (the workflow — §3).** The workflow ingests the build, creates one package + a
   `1.0` version, then calls **`services.partnerregistry`** `ConfigurePlaytestAsync` to write the
   DNA-group-gated offering **and** attach the title in one PR, then confirms the build is installed on a
   streaming server.
7. **Poll for status (`Xbox.Xbet.Service`).** Because there is no cross-tenant push channel yet, xPlaytest
   **polls** `GET /v3/playtest/playtesttitleingestion/{jobId}` (through SAGE) until the job is terminal,
   then sets the playtest's status to `StreamingReady` and surfaces the launch URL.
8. **Stream it (Bayside · `Xbox.JS`, + `services.auth`).** A tester clicks the shareable link → Bayside →
   **login first** (so non-members never see playtest details) → `services.auth` checks the user against
   the offering's `AllowedDnaGroups` → the private offering appears in `/offerings` → the tester streams.
9. **Teardown (planned — PT6).** Deleting a playtest will `DELETE` the by-playtest route to **tombstone**
   the offering (clear `AllowedDnaGroups`, denying all testers immediately), idempotently, then GC the
   offering/asset after a grace period.

```
Creator (Partner Center / Xbox.Gpx.PartnerCenter.Client)
   │  enable cloud streaming + publish build
   ▼
xPlaytest publish workflow (Xbox.Xbet.Service) ──resolve XboxTitleId──▶ XORc (xorc)
   │  build PlaytestIngestionJobParameters, POST
   ▼
SAGE gateway (services.serviceapigateway)  ──cross-tenant MSFTGreen→Corp──▶
   ▼
GSSV ingestion (services.contentingestion) — PlaytestTitleIngestionWorkflow  [§3]
   │  configure offering + title (one PR)
   ▼
Partner Registry (services.partnerregistry)
   │  confirm install on a server  ──▶ PC Orchestrator (services.pcservices) | Xbox allocator
   ▼
job terminal  ◀──poll GET {jobId}── xPlaytest (Xbox.Xbet.Service) ──set StreamingReady, share link──▶
   ▼
Tester ▶ Bayside (Xbox.JS) ▶ login (services.auth enforces AllowedDnaGroups) ▶ stream
```

---

## 3. Deep dive: `PlaytestTitleIngestionWorkflow` (xCloud ingestion)

**File:** `services.contentingestion/src/Product/ContentCatalog.Ingestion.Core/Workflows/PlaytestTitleIngestionWorkflow.cs`

It is an `[ExclusiveWorkflow]` state machine over `PlaytestTitleIngestion.JobParameters` (input) and
`PlaytestTitleIngestion.JobState` (persisted state). Each `[WorkflowStage]` returns a `WorkflowResult` that
either transitions to the next stage, retries on a delay (optionally with a *fallback* stage on timeout),
or concludes. It uses a **Trigger + Poll** pattern throughout (it does *not* suspend on engine
completion-callbacks, because this service doesn't host that channel).

**Collaborators injected into the workflow (ctor):** `assetsProcessor`, `packagesProcessor`,
`workflowProcessor`, `partnerRegistryClient`, `xboxAllocatorClient` (`IServerAllocatorClient`),
`pcOrchestratorClient` (`IPCOrchestratorClient`), `resolutionProcessor`, `mailerClient`, plus
`IOptionsMonitor<IngestionWorkflowSettings>` for the polling policies and the PC readiness query.

### Stage map

```
ValidateParameters (entry)
   └▶ TriggerAssetIngestionAsync
        └▶ PollAssetIngestionAsync ──not complete──▶ Retry ──timeout──▶ HandleAssetIngestionTimeout ─▶ Conclude
                 │ failed ─▶ Conclude
                 ▼ success
           CreatePackageAsync ──asset missing──▶ Conclude
                 ▼
           ConfigureOfferingAsync
                 ▼
           PollFirstInstallAsync ──PC?──▶ PollPcFirstInstallAsync
                 │ (Xbox: allocator)        │
                 ├──install found──▶ NotifyReadyAsync ─▶ Conclude
                 └──not found / timeout──▶ NotifyInstallNotFoundAsync ─▶ Conclude
```

### Stage-by-stage

**1. `ValidateParameters`** *(entry, ~L68).* Stamps `State.StartTime`, calls `context.Parameters.Validate()`
(this is where `XboxTitleId` must be non-null/nonzero and `ExpirationTime` must be a future UTC), then
transitions to `TriggerAssetIngestionAsync`.

**2. `TriggerAssetIngestionAsync`** *(~L79).* Builds the **audiences**: one `XusAudience(dnaGroup, AllowedSandboxId)`
per entry in `AllowedDnaGroups`. Constructs an `AssetIngestion.JobParameters` (`PartnerId`,
`StoreAsset.ContentId`, the `StoreAsset`, the audiences, and a `CreatedBy` stamp), then schedules the
**child Asset Ingestion job** via `workflowProcessor.ScheduleAssetIngestionJobAsync` and stores
`State.AssetIngestionJobId`. Transitions to `PollAssetIngestionAsync` after the configured poll interval.
*(All playtest DNA-group flights resolve to the same build, so this is a single asset-ingestion job /
single SUCU audience — not one job per group.)*

**3. `PollAssetIngestionAsync`** *(~L105).* Reads the child job's `OperationStatus`.
- not complete → `Retry(...)` on the `AssetIngestionJobPollingPolicy`, **with `.WithFallbackStage(HandleAssetIngestionTimeout)`** so an over-long job routes to the timeout handler instead of spinning forever.
- complete but not success → warn (`AssetIngestionFailed`) and `→ ConcludeWorkflow` (the whole operation can be retried).
- success → `→ CreatePackageAsync`.

**4. `HandleAssetIngestionTimeout`** *(~L133).* The fallback: records the timeout, warns
(`AssetIngestionTimeout`), `→ ConcludeWorkflow` (treated as a retryable failure).

**5. `CreatePackageAsync`** *(~L143).* Turns the ingested asset into a streaming package/version:
- Fetches the `WireAsset` (`assetsProcessor.GetAssetAsync`, `LatestIngestedVersion`); if null → warn
  (`AssetNotIngested`) and `→ ConcludeWorkflow`.
- Computes the **title id**: `xpt{PlaytestProductId}-{GenerateTitleId(StoreEntry.Name, Platform)}` — the
  exact value Partner Registry registers as `Title.Id`.
- **Idempotent by design** (the stage can re-run on nightly republishes / retries): it queries for an
  existing package by `PartnerId + titleId` and **reuses** it; only if none exists does it create **one
  neutral package** (no DLC, no market mix). Stores `State.StreamingPackageIds`.
- Creates a single **`1.0` version** (`AvailableFrom = now`, `AvailableUntil = max`) only if the package
  has no version yet (so a half-finished prior run doesn't duplicate). `→ ConfigureOfferingAsync`.

**6. `ConfigureOfferingAsync`** *(~L210).* Builds a `PlaytestRequest` (`CreatePlaytestRequest`: playtest
ids, name, partner, the full `AllowedDnaGroups`, `ExpirationTime`, and **one** `PlaytestTitle` carrying
`TitleId`, `Platform`, `ProductId`, `XboxTitleId`) and calls
**`partnerRegistryClient.ConfigurePlaytestAsync(request)`** — this writes the DNA-group-gated **offering
and attaches the title in a single Partner Registry PR**. Stores `State.OfferingId` (= `request.GetOfferingId()`
= `xpt{PlaytestProductId}`). `→ PollFirstInstallAsync`.

**7. `PollFirstInstallAsync`** *(~L223).* Gates the "ready" signal on a **confirmed install of the exact
version** (adding the title to the offering is what triggers distribution to install the build). If there
are no package ids → `FailWorkflow`. Then it **forks by platform**:

- **PC → `PollPcFirstInstallAsync`** *(~L278).* PC servers don't pre-pull content, and every ingestion can
  be a new version, so "installed somewhere" isn't enough — it confirms the *exact ingested version*:
  1. `resolutionProcessor.ResolveContentInstallMetadataAsync` (scoped to the playtest's flights/sandbox and
     `ServerType.PC`) yields the install id and per-version **content hash**.
  2. Requires **exactly one current PC version** (zero = not resolved yet / no PC build; many = ambiguous)
     — both retry rather than risk confirming a stale build.
  3. Builds a `GameStreamingServerFilter` — `Regions`, `SystemUpdateGroups`, `Skus` (from
     `IngestionWorkflowSettings.PlaytestPcReadinessQuery`, per-environment; falls back to an interim region
     when unset) plus a **`ContentFileFilter { Id = install id, Version = hash }` that pins the exact
     version** — and queries **PC Orchestrator** (`pcOrchestratorClient.QueryServersPagedAsync`).
  4. No server yet → `Retry(...)` with fallback `NotifyInstallNotFoundAsync`; server found →
     `→ NotifyReadyAsync`.

- **Xbox → (inline, ~L246).** Xbox servers pull content themselves and self-report to the allocator, so it
  generates a `ContentInstallId` from the package, builds a `ServerFilter` (`Region`, `SystemUpdateGroup.GA`,
  `ServerType.XboxV3SeriesS`, `ServerPlatform.Xbox`, `LocalPackageId`), and queries
  `xboxAllocatorClient.QueryServersAsync`. Empty → `Retry(...)` with fallback `NotifyInstallNotFoundAsync`;
  found → `→ NotifyReadyAsync`.

**8. `NotifyReadyAsync`** *(~L383).* Sets `State.FirstInstallReady = true` and (if
`MailerNotificationsEnabled`) sends an **interim Teams notification** via `mailerClient`. *(TODO: replace
with a programmatic cross-tenant push to xPlaytest — none exists today, so the partner polls the status
endpoint. Tracked as AB#62688258.)* `→ ConcludeWorkflow`.

**9. `NotifyInstallNotFoundAsync`** *(~L401).* The offering was created but no server reported the package
within the polling window — warns (`FirstInstallNotFound`), optionally sends a Teams "not found"
notification, `→ ConcludeWorkflow`. *(The offering still exists; the build just isn't confirmed-ready.)*

**10. `ConcludeWorkflow`** *(terminal, ~L444).* Sets the **final `OperationStatus` that xPlaytest observes
when it polls** — `Success` requires **both** the offering configured **and** first install confirmed
(`State.IsSuccess`); otherwise `FailWorkflow` with the summary reason.

**11. `HandleUncaughtExceptionAsync`** *(~L451).* Per-stage safety net: logs unexpected exceptions with the
failing stage id.

### Why it's shaped this way (key design decisions)
- **One offering = one title = one package = one `1.0` version** per playtest in v1; the `xpt{PlaytestProductId}`
  id and the `xpt{…}-{neutralTitleId}` title id are built identically on the xPlaytest and Partner Registry
  sides so they always agree.
- **Single `XusAudience` for ingestion**, but the **full `AllowedDnaGroups` set** is written onto the
  offering and enforced at login — ingestion only needs one representative audience.
- **PC vs Xbox install-readiness fork** — PC uses **PC Orchestrator** with an exact version-hash pin
  (`ContentFileFilter`), not the Xbox-only allocator's "installed anywhere" check.
- **Idempotent + retryable** — every stage can re-run (nightly republishes, retries) without creating
  duplicate packages/versions/offerings.
- **`200 OK` + `OperationStatus(jobId)`** is the whole contract; the partner **polls** for terminal state
  because there's no cross-tenant push channel yet.

---

## 4. Current status (where each piece really is — 2026-06-20)

- **Merged:** core ingestion workflow + V3 endpoints (`15800964`), cross-tenant S2S gate (`15905881`),
  Partner Registry offering/title/`AllowedDnaGroups`/regions/id (`15732852`, `15773366`, `15815668`,
  `15821813`, `15849944`, `15860243`, `15892276`), login enforcement (`15738761`), DevApi (`15739964`),
  XORc title id (`15894506`).
- **Draft (built, in review):** xPlaytest caller — trigger + payload + SAGE send + poll (`15834601`); SAGE
  routes (`15829639`); PC install-readiness polling (`15896502`); DevApi test page (`15876080`).
- **Not yet built:** playtest **teardown / DELETE offering** (PT6, P0-2); productionized **ECS seller
  gating** (a hardcoded pilot-seller gate exists today); the **shareable link from the portal** (P0-7); the
  **Bayside player flow** (P0-8 / P1-11 / P1-12).

## 5. See also
- PR ledger: [`../PRProgress/README.md`](../PRProgress/README.md)
- Per-repo change log: [`../Repos/README.md`](../Repos/README.md)
- Meeting decisions: [`./transcript-decisions.md`](./transcript-decisions.md)
- xCloud / xPlaytest / xPackage relationship: [`./xcloud-xplaytest-xpackage.md`](./xcloud-xplaytest-xpackage.md)
- Xbox vs PC handling: [`./handling-xbox-vs-pc-differences.md`](./handling-xbox-vs-pc-differences.md)
- Cross-tenant S2S: [`../Blockers/cross-tenant-s2s.md`](../Blockers/cross-tenant-s2s.md) · [`../FuturePlans/s2s-cross-tenant-call.md`](../FuturePlans/s2s-cross-tenant-call.md)
