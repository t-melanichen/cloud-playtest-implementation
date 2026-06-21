# PC playtest streaming readiness — install-on-attach, quota, offering SUG, and the readiness poll

**Status (2026-06-20):** All three code/config changes are made, built, and tested, and are open as **draft PRs**.
The only remaining step is **registering the distinct `PC_PLAYTEST` SUG** at the platform level (Timi). Everything is
pinned to **`PC_PLAYTEST`** / **`STANDARD_NC64AS_T4_V3`** / **`WESTUS2`**; if the real SUG string differs, it's a single
literal to update in the three PRs.

---

## 1. Why this is needed (high level)

Instantly Shareable Playtest lets testers **stream** a playtest from the cloud instead of downloading it. For that to
work, the game build must be **physically installed on a cloud GPU server**, and we must **know it's ready** before we
hand the tester a launch link (else they click and get a broken/404 experience).

Xbox vs PC: Xbox servers pre‑pull content and self‑report. **PC servers do not** — content lands **on demand** only when
something tells the system to install it. So for PC we must (a) **trigger** the server‑side install and (b) **confirm**
it landed, for the **exact version** just published (a PC version = the content **hash**).

## 2. The two "installs" and the end‑to‑end order

There are two different things called "install"; the order matters (verified in `PlaytestTitleIngestionWorkflow`):

- **Install #1 — content ingestion** (build → xCloud's content catalog/SUCU). Happens **first**.
- **Install #2 — PC‑server install** (build → an actual GPU server, for streaming). Happens **later, triggered by
  attaching the title to the offering**.

CTIN `PlaytestTitleIngestionWorkflow` stage order:
1. `ValidateParameters`
2. `TriggerAssetIngestionAsync` → `PollAssetIngestionAsync` — **Install #1** (ingest the build, wait for it)
3. `CreatePackageAsync` — create the streaming package + version 1.0
4. `ConfigureOfferingAsync` — create the offering + **attach the title** (`ConfigurePlaytestAsync`)
5. `PollFirstInstallAsync` — **Install #2 happens here**: the attach triggers the PC‑server staging; this stage polls for it
6. `NotifyReadyAsync` → ready

So: **ingest the build → package it → attach the title to the offering → that attach triggers the PC‑server staging →
poll by exact version‑hash until a server reports it → ready.**

## 3. The three PRs — what each does, in depth

### PR-A · services.contenttargets · #15946980 · draft · `t-melanichen/pc-playtest-install-on-attach`
**Title:** [CTGT] Enable PC playtest install-on-attach + quota (PC_PLAYTEST SUG, Int)

**What it does:** turns on the **PC‑server install (Install #2)** for the playtest lane. Content Targets tells the PC
Orchestrator how many servers to provision per *server set* (region × SUG × SKU) and which installs map to them. Two
config edits in `appsettings.ContentTargets.Int.json`:
- **Quota (Timi's C2):** a `STANDARD_NC64AS_T4_V3` SkuConfig with `QuotasBySugByRegion.WESTUS2.PC_PLAYTEST = 1` — so
  `ServerSetsProcessor.UpdatePCServerSetsAsync` **creates the server set** with `ServerQuota = 1` (one T4).
- **Enable install-on-attach (Timi's C1):** a `ResolutionConfiguration.IncludePredictions.Override`
  (`ServerType=PC`, `Sugs=[PC_PLAYTEST]`, `Value=true`).

**Why that enables the install:** PC has **no BaseTargets** path; PC concurrency comes from `PredictionsProcessor`
which synthesizes **1 per install id**, and that's only included when `IncludePredictions.GetValue(serverSet)` is true
(off by default; only XBOX is overridden on). The PC Orchestrator calls `ResolveTargetsAsync` with
`TargetsQuery.Create()` → `DistributionTargets` (includes the `Predictions` flag), so the override is honored → the
server set gets a concurrency target of **1** → it provisions one T4 and installs the title's build.

**Files:** `appsettings.ContentTargets.Int.json`; tests `Configuration/ResolutionConfigurationBindingTests.cs`,
`Processors/ResolutionProcessorTests.cs`.
**Tests:** Core.UnitTests **24/24**. `ResolutionProcessorTests` proves: override **on** → `ConcurrenciesByInstallId = 1`;
**off** → no target.

### PR-B · services.partnerregistry · #15949594 · draft · `t-melanichen/playtest-offering-sug`
**Title:** [PTNR] Set PC_PLAYTEST SUG on the playtest offering

**What it does:** names the `PC_PLAYTEST` lane **on the offering** so Content Targets maps the title's installs to it.
`PlaytestProcessor` now sets `OfferingV2.SelectableSystemUpdateGroups = [PC_PLAYTEST]` for PC playtest titles (alongside
the existing `TargetServerSkus = [STANDARD_NC64AS_T4_V3]`).

**Why it's needed:** Content Targets' `UpdateInstallIdsByServerSetAsync` reads `offering.GetSystemUpdateGroups()` and
maps the title's installs to `ServerSetId.CreatePC(region, sug, sku)`. Before this, the offering set Regions + SKU but
**no SUG**, so the title mapped to **no** server set and Install #2 never had anywhere to land.

**Files:** `Processors/PlaytestProcessor.cs`; test `Processors/PlaytestProcessorTests.cs`.
**Tests:** PlaytestProcessorTests **12/12** (asserts the offering carries `SelectableSystemUpdateGroups = [PC_PLAYTEST]`).

### PR-C · services.contentingestion · #15896502 · draft · `t-melanichen/playtest-pc-install-polling`
**Title:** Implement PC install-readiness polling in PlaytestTitleIngestionWorkflow

**What it does:** the **readiness poll (step 5)** — how CTIN *knows* Install #2 finished, pinned to the exact version.
`PollPcFirstInstallAsync`:
1. **Resolve** the just‑ingested content → `install id` + `hash` (`ResolveContentInstallMetadataAsync`).
2. Build `GameStreamingServerFilter.Content = [ ContentFileFilter { Id = installId, Version = hash } ]` (plus the
   configurable SUG / Regions / SKUs).
3. Query **PC Orchestrator** `QueryServersPagedAsync`. Empty → **retry**; a server reporting that exact install id +
   hash → `NotifyReadyAsync`.

It also adds `IngestionWorkflowSettings.PlaytestPcReadinessQuery` (SystemUpdateGroup / Regions / Skus) so the poll is
pinned to the same lane, and sets the **Test (non‑prod)** values to `PC_PLAYTEST` / `WESTUS2` / `STANDARD_NC64AS_T4_V3`.

**Files:** `Configuration/IngestionWorkflowSettings.cs`, `Workflows/PlaytestTitleIngestionWorkflow.cs`,
`Worker/appsettings.json`, `Worker/appsettings.Test.json`; test `PlaytestTitleIngestionWorkflowTests.cs`.
**Tests:** PlaytestTitleIngestionWorkflowTests **11/11** (incl. configured‑SUG/region/SKU flows into the filter).

**Known caveat:** version selection uses `OrderByDescending(v => v.IsCurrent)`, where `IsCurrent` = "available now," not
strictly "just‑ingested," so a republish/version‑bump could select a stale hash (TODO 62521491). First‑publish is correct.

## 4. Verified against what Timi said (XCloudIngestion mtg)

| Timi (verbatim) | Maps to |
|---|---|
| "we should have one SKU … one SUG and we use that for every play test" / "a distinct PC underscore play test SUG" | the `PC_PLAYTEST` SUG + single `STANDARD_NC64AS_T4_V3` SKU used by all three PRs |
| "content targets will notice that the title is in this offering … if it's in this offering, then I should install at least one … we already have that implemented today. I just have it disabled … for playtest we can conditionally enable it" | **PR‑A** (IncludePredictions override = conditionally enable) + **PR‑B** (title in the offering, with the SUG) |
| "we now have a quota configuration that defines … the max number of servers a sug can have … we can just set that to one. It's one T4 … it's a dynamic config" | **PR‑A** `QuotasBySugByRegion.WESTUS2.PC_PLAYTEST = 1` |
| "once you merge … the offering config, distribution service should start doing one installation … once that installation is done … the PC orchestrator manifests saying … this content is now available on this server. So then, while you're doing your polling, eventually should magically just show up … ready to play" | the attach→install→poll sequence; **PR‑C** poll → `NotifyReady` |
| "the version for a content file on a PC server is actually the hash … the install ID is install ID and the version is the hash … put that in the content file filter … query for servers and wait until something shows up" | **PR‑C** `ContentFileFilter { Id = installId, Version = hash }` → `QueryServersPagedAsync` |
| "the offering stuff that's already been done by Melanie" | the offering creation in CTIN `ConfigureOfferingAsync` + **PR‑B** (the SUG on it) |

**One nuance vs Timi:** he framed the enable + quota as a **dynamic‑config flip he'd do**, "not … done programmatically."
PR‑A is the **checked‑in** equivalent (same keys); content‑targets loads config via `CreateGameStreamingBuilder` →
`SetupDefaultConfigSources`, so the dynamic layer can override the same keys at runtime. Confirm with Timi whether he
flips dynamic config or merges PR‑A (see open questions).

## 5. The one remaining step — register the `PC_PLAYTEST` SUG

The lane must **exist** before any of the above fires. Two places, both platform/infra (Timi):

1. **SUG Ids registry** — `PC_PLAYTEST` must resolve via `SystemUpdateGroup.GetId("PC_PLAYTEST", env)` (where `GA`,
   `CANARY` live). Partner‑registry validation rejects unknown SUGs (`ValidationProcessorUtilities.cs:421`), so the
   offering PR (PR‑B) won't validate until this exists.
2. **OS Targets manifest** — add `PC_PLAYTEST` for `STANDARD_NC64AS_T4_V3` in `WESTUS2`, so PC servers run in that SUG.
   Content Targets `UpdatePCServerSetsAsync` only builds the server set for SUGs present in the OS Targets manifest.

(The Partner Registry `SystemUpdateGroupConfigV2` pools at `/SystemUpdateGroups/Pools` are for Xbox pool→SUG quota
mappings; the PC quota is handled in PR‑A, so you don't need that for PC.)

## 6. How to test that this works

### A. Unit level — already green (run locally)
- content-targets: `dotnet test src/Tests/Unit/ContentTargets.Core.UnitTests -p:StaticWebAssetsEnabled=false` → **24/24** (`ResolutionProcessorTests`: enable→1, off→0).
- partner-registry: `dotnet test …/PartnerRegistryService.UnitTests --filter PlaytestProcessorTests -p:StaticWebAssetsEnabled=false` → **12/12** (offering carries the SUG).
- CTIN: `dotnet test …/ContentCatalog.Ingestion.Core.UnitTests --filter PlaytestTitleIngestionWorkflowTests` → **11/11** (SUG/region/SKU + hash flow into the PC Orchestrator filter).

### B. After the SUG is registered + the 3 changes deploy (CI/CICD, Int/Test) — verify each layer
1. **SUG registered?** Partner Registry `GET /v1/systemupdategroup/configs` (or confirm `SystemUpdateGroup.GetId("PC_PLAYTEST", int)` ≠ null). OS Targets manifest lists `PC_PLAYTEST` for the SKU/region.
2. **Offering carries the SUG?** Publish a PC playtest, then GET the offering and confirm `SelectableSystemUpdateGroups = ["PC_PLAYTEST"]`.
3. **Content Targets built the lane + target?** Use the content-targets **Savant** console (the dashboard Timi used), server‑set id format `WESTUS2/PC_PLAYTEST/STANDARD_NC64AS_T4_V3`:
   - `sst sugs=PC_PLAYTEST` (GetServerSets) → the PC_PLAYTEST server set exists ⇒ quota config + OS Targets worked.
   - `sstm WESTUS2/PC_PLAYTEST/STANDARD_NC64AS_T4_V3` (GetServerSetMetadata) → `ServerQuota = 1`.
   - `ssti …` (GetServerSetInstallIds) → the playtest's install id is mapped ⇒ offering SUG (PR‑B) worked.
   - `sstt …` (GetServerSetTargets / ResolveTargets) → `ConcurrenciesByInstallId` has the install at **1** ⇒ enable (PR‑A) worked.
4. **Server provisioned + installed?** Query **PC Orchestrator** for a server matching the content file (install id + hash) — it should appear once distribution finishes.
5. **CTIN poll reaches ready?** `GET /v3/workflows/playtesttitleingestion/{jobId}` → `OperationStatus` flips terminal/success; worker logs show "PC install successful" → `NotifyReadyAsync`.

### C. End-to-end (the real proof)
Publish a PC playtest for the pilot seller → walk steps B2–B5 → get the launch link
(`https://play.xbox.com/play/launch/{productId}?offeringId=xpt{PlaytestProductId}`) and confirm it streams. Then
**republish a new build** and confirm the poll waits for the **new** hash (covers the version caveat in PR‑C).

## 7. Rubber-duck review (2026-06-20) — findings + resolutions
- **PR-B field (`SelectableSystemUpdateGroups` vs `SystemUpdateGroupWeights`) — resolved, no change.** `services.auth`
  `UserLoginProcessor.cs:739` builds each `OfferingRegion` with `SystemUpdateGroups = offering.SelectableSystemUpdateGroups`,
  so auth exposes the offering's `SelectableSystemUpdateGroups` to the client as the available SUGs, and content-targets
  unions both fields. `SelectableSystemUpdateGroups = [PC_PLAYTEST]` is correct for both install-mapping and allocation.
  (If end-to-end allocation testing ever shows the server isn't picked, also set `SystemUpdateGroupWeights = { PC_PLAYTEST: 100 }`.)
- **PR-A override scope — intentional, no change.** The `IncludePredictions` override is keyed on `Sugs=[PC_PLAYTEST]` only
  (no Regions/Skus). Deliberate: enable install-on-attach wherever the dedicated PC_PLAYTEST lane exists. Constraining to
  WESTUS2/NC64AS would silently break if PC_PLAYTEST capacity is later added in another region/SKU.
- **Region casing — OK.** Content-targets uses `WESTUS2`, the offering uses `WestUS2`; `Id` comparison is case-insensitive
  (per `PlaytestProcessorTests`: "Offering.Id is an Id (case-insensitive)"), so they match.
- **Timing / first-install timeout — flag.** CTIN starts `PollFirstInstallAsync` right after `ConfigureOfferingAsync`. The
  offering is a Partner Registry ADO PR that can need human approval (up to ~48h, per `Blockers/manual-pr-polling.md`), but
  `FirstInstallPollingPolicy` times out at **6h**. If approval/provisioning exceeds the window, the poll routes to
  `NotifyInstallNotFound`. Raise the timeout (or gate the poll on the offering being live) before relying on it.
- **CTIN env config — flag.** The poll values live in the Worker `appsettings.Test.json`. Confirm the CTIN env that pairs
  with content-targets `Int` loads that file; otherwise the poll falls back to `WestEurope`/unconstrained and times out (open question 5).
- **Version republish — known TODO 62521491.** On republish the `IsCurrent` selection can false-ready against a stale hash. First publish is correct.
- **SUG gating — note.** The SUG is set for all PC playtest titles in `PlaytestProcessor`; correct since that path only
  creates PC streaming playtests. If non-streaming PC playtests ever share it, gate on the streaming/instant-playtest flag.

## 8. Open questions for Timi
1. **Exact SUG string** (assumed `PC_PLAYTEST`) — must match OS Targets, the SUG Ids registry, content-targets, the offering, and CTIN.
2. **Is the SUG already registered/provisioned** (OS Targets + Ids) for `STANDARD_NC64AS_T4_V3` in `WESTUS2`?
3. **Who flips enable + quota** — Timi via dynamic config, or merge PR‑A? Dynamic keys:
   `ServerSetsConfiguration:SkuConfigs:STANDARD_NC64AS_T4_V3:QuotasBySugByRegion:WESTUS2:PC_PLAYTEST = 1` and
   `ResolutionConfiguration:IncludePredictions:Override = { Value:true, ServerType:PC, Sugs:[PC_PLAYTEST] }`.
4. **SKU** — `PcServerSku = STANDARD_NC64AS_T4_V3` is a documented stand-in; right T4 SKU?
5. **CTIN env mapping** — content-targets has `Int`; the CTIN worker has only `Test/Prod` — which CTIN env pairs with content-targets `Int`?
6. **Prod** — `IncludePredictions` allows a single `Override`, already used by `ServerType=XBOX`; needs multi-override support; prod region `NorthCentralUs`.

### Ready-to-send message to Timi

> **Subject: PC playtest streaming — need the `PC_PLAYTEST` SUG registered/provisioned**
>
> Hi Timi — following up on the PC playtest install-on-attach work from the xCloud ingestion sync. The three
> code/config changes are done and tested, all pinned to **SUG `PC_PLAYTEST`**, **SKU `STANDARD_NC64AS_T4_V3`**,
> **region `WESTUS2`** (Int):
>
> - Content Targets (enable install-on-attach + quota=1): PR 15946980
> - Partner Registry (sets the SUG on the playtest offering): PR 15949594
> - Content Ingestion (readiness poll by install-id + version hash): PR 15896502
>
> The only thing blocking end-to-end is the SUG itself. You mentioned you'd have a distinct PC_playtest SUG and
> "have things set up that way already," so a few quick questions:
>
> 1. **Exact SUG name** — is it `PC_PLAYTEST`, or something else? (I'll match it across all three PRs.)
> 2. **OS Targets** — is `PC_PLAYTEST` already provisioned for `STANDARD_NC64AS_T4_V3` in `WESTUS2` (Int), or does
>    that still need doing? (Content Targets only builds the server set for SUGs in the OS Targets manifest.)
> 3. **Recognition** — `PC_PLAYTEST` isn't in the `SystemUpdateGroup` list in `Services.Common.Ids` today, so the
>    offering hits a (non-critical) validation warning. Does it need adding there, or is there a dynamic path?
> 4. **Enable + quota** — flip via dynamic config (as you described), or land the Content Targets PR as the
>    checked-in source? If dynamic, the keys are:
>    `ServerSetsConfiguration:SkuConfigs:STANDARD_NC64AS_T4_V3:QuotasBySugByRegion:WESTUS2:PC_PLAYTEST = 1` and
>    `ResolutionConfiguration:IncludePredictions:Override = { Value: true, ServerType: PC, Sugs: [PC_PLAYTEST] }`.
> 5. **SKU** — `STANDARD_NC64AS_T4_V3` is currently a hardcoded stand-in on the offering; is that the right T4 SKU?
>
> Once I have the exact name + confirmation the SUG is provisioned, everything else is already wired. Thanks!

## 9. Owners
Melanie Chen (CTGT/CTIN/PTNR changes) · Timi Bolaji (SUG registration in OS Targets + Ids, SKU confirmation, dynamic-config flip).

## 10. Sources
- services.contentingestion: `Workflows/PlaytestTitleIngestionWorkflow.cs` (stage order; `PollPcFirstInstallAsync`).
- services.contenttargets: `Processors/Implementations/{ResolutionProcessor,ServerSetsProcessor,PredictionsProcessor}.cs`,
  `Configuration/{ConfigItem,ResolutionConfiguration,SkuConfiguration}.cs`, `Extensions/{OfferingExtensions,TitleExtensions}.cs`,
  `Contracts/{TargetsQuery,TargetsCalculationMode}.cs`, `Savant/DefaultSavantProvider.cs`.
- services.pcservices: `Orchestrator.Core/Manifests/ConfigManifestProvider.cs`.
- services.partnerregistry: `Processors/PlaytestProcessor.cs`, `Processors/Validation/ValidationProcessorUtilities.cs`, `Controllers/SystemUpdateGroupConfigController.cs`.
- `Transcripts/XCloudIngestion.docx` (Timi Bolaji).
- [`./pc-install-readiness-polling-implementation.md`](./pc-install-readiness-polling-implementation.md) C1/C2.
