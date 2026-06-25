# Repo: Xbox.Xbet.Service

**Role:** xPlaytest publish workflow: builds the ingestion payload, calls SAGE, polls for `StreamingReady`, crafts launch URL.

**Base used for git evidence:** `origin/main` (found before `origin/master`, `main`, `master`).

## Changes made (per branch/PR)

### `t-melanichen/playtest-ingestion-contracts` — local + pushed

- **Evidence:** `git log origin/main..t-melanichen/playtest-ingestion-contracts` = `850b31de0fb Add PlaytestIngestionJobParameters + StoreAsset contracts`.
- **Merge-base:** `79d29bdedc1feb2e091df38522d15e7ef75e0db4`.
- **Diff stat:** 3 files, 163 insertions:
  - `src/PlayTest/PlayTest.Shared/Contracts/PlaytestIngestionJobParameters.cs` (+70)
  - `src/PlayTest/PlayTest.Shared/Contracts/StoreAsset.cs` (+54)
  - `src/PlayTest/PlayTest.Shared/Contracts/StoreEntry.cs` (+39)
- **Change summary:** adds xPlaytest-local DTOs for the initial SAGE/xCloud ingestion JSON shape: job parameters, `StoreAsset`, and `StoreEntry`.

### `t-melanichen/playtest-ingestion-workflow-wiring` — local only

- **Evidence:** no `origin/t-melanichen/playtest-ingestion-workflow-wiring` remote ref exists. `git log origin/main..t-melanichen/playtest-ingestion-workflow-wiring` has 3 commits:
  - `43058225609 Add PlaytestIngestionPayloadBuilder for streaming ingestion payload`
  - `18ddf551351 Merge branch 't-melanichen/playtest-ingestion-contracts' into t-melanichen/playtest-ingestion-payload-builder`
  - `850b31de0fb Add PlaytestIngestionJobParameters + StoreAsset contracts`
- **Merge-base:** `a1a258721690e1a4e5c2b542de3a73912585f403`.
- **Diff stat:** 5 files, 549 insertions:
  - contract DTOs under `src/PlayTest/PlayTest.Shared/Contracts/`
  - `src/XPackage/XPackageWorkflow/XPackageWorkflow/Workflows/Playtest/PlaytestIngestionPayloadBuilder.cs` (+210)
  - `src/XPackage/XPackageWorkflow/XPackageWorkflow.Tests/UnitTests/Workflows/PlaytestIngestionPayloadBuilderTests.cs` (+161)
- **Change summary:** early workflow-side payload-builder branch. It builds a validated playtest ingestion payload from publish job parameters, playtest response, and package lifecycle state, backed by unit tests. It does not yet wire SAGE POST or polling.

### `t-melanichen/playtest-xboxtitleid-resolver` — local only

- **Evidence:** no `origin/t-melanichen/playtest-xboxtitleid-resolver` remote ref exists. `git log origin/main..t-melanichen/playtest-xboxtitleid-resolver` is the same 3-commit payload-builder stack as `playtest-ingestion-workflow-wiring`.
- **Merge-base:** `a1a258721690e1a4e5c2b542de3a73912585f403`.
- **Diff stat:** same 5 files, 549 insertions.
- **Change summary:** branch currently contains the early payload-builder/contract work only; the later XORc Xbox Live title-id resolver changes are on `playtest-ingestion-payload-builder`.

### `origin/t-melanichen/xbet-sage-ingestion-payload` — remote-only, has commits vs base

- **Evidence:** `git log origin/main..origin/t-melanichen/xbet-sage-ingestion-payload` = `f182137fcfa Add bare-minimum xCloud playtest ingestion payload assembly`.
- **Merge-base:** `22c40ce7a2b8a50b8490c3881ac93d5fc52f757c`.
- **Diff stat:** 4 files, 675 insertions:
  - `src/XPackage/XPackageWorkflow/XPackageWorkflow.Shared/Constants/PlaytestIngestionConstants.cs` (+70)
  - `src/XPackage/XPackageWorkflow/XPackageWorkflow.Shared/Workflows/PlaytestIngestion/PlaytestIngestionJobParameters.cs` (+232)
  - `src/XPackage/XPackageWorkflow/XPackageWorkflow/Workflows/Playtest/PlaytestIngestionPayloadBuilder.cs` (+98)
  - `src/XPackage/XPackageWorkflow/XPackageWorkflow.Tests/UnitTests/Workflows/PlaytestIngestionPayloadBuilderTests.cs` (+275)
- **Change summary:** remote-only precursor for SAGE ingestion payload assembly. The builder maps playtest publish data into `PlaytestIngestionJobParameters` with `PartnerId`, `PlaytestProductId`, `AllowedDnaGroups`, expiration, sandbox, green-signing, and `StoreAsset` fields. This branch still used placeholders for `XboxTitleId` and `AumId` and documented them as P0 blockers.

### `origin/t-melanichen/partner-registry-offering-service` — remote-only, has commits vs base

- **Evidence:** `git log origin/main..origin/t-melanichen/partner-registry-offering-service` has 2 commits:
  - `d65e1a0bd60 feat(XPackageWorkflow): add Partner Registry offering publish with SellerId gating`
  - `6b81e73f485 feat(PlayTest): add Partner Registry offering publish (Path B / AllowedFlights)`
- **Merge-base:** `028fa8bc2ebbacba0bfb1cc763bee13e138a2fff`.
- **Diff stat:** 18 files, 717 insertions, 1 deletion.
- **Key files:**
  - `src/XPackage/XPackageWorkflow/XPackageWorkflow/BusinessLogic/Playtest/OfferingPublishBusinessLogic.cs`
  - `src/XPackage/XPackageWorkflow/XPackageWorkflow/ServiceClients/PartnerRegistry/PartnerRegistryServiceClient.cs`
  - `src/XPackage/XPackageWorkflow/XPackageWorkflow/Workflows/Playtest/OfferingMapper.cs`
  - `src/XPackage/XPackageWorkflow/XPackageWorkflow/XPackageWorkflow.appsettings.json`
- **Change summary:** adds Partner Registry offering upsert support. `OfferingPublishBusinessLogic` builds an `OfferingV2` from resolved DNA group ids, writes them into `AuthorizationOptions.AllowedFlights`, and calls `IPartnerRegistryServiceClient`. The branch adds Partner Registry contracts/client/config/metrics, startup registration, mapper tests, and PlayTest business-logic test wiring. It notes full-replace/upsert semantics and that GMS/DNA resolution remains in PlayTest.

### `t-melanichen/playtest-ingestion-payload-builder` — local + pushed; PR 15834601

- **PR cross-reference:** `PRProgress\07-XBET-15834601-playtest-ingestion-payload-builder.md` says:
  - "**Pull Request:** 15834601"
  - "**Source branch:** `t-melanichen/playtest-ingestion-payload-builder` → `main`"
  - "**Status:** Draft"
  - Title: "[XBET] PR 15834601 — Playtest Ingestion Payload Builder"
- **Evidence:** `git log origin/main..t-melanichen/playtest-ingestion-payload-builder` has 18 commits, including:
  - `43058225609 Add PlaytestIngestionPayloadBuilder for streaming ingestion payload`
  - `23c4d9a228b feat(XPackageWorkflow): use MICROSOFT partner id and clamp Playtest expiration to 7 days`
  - `b02a23451bc feat(XPackageWorkflow): gate streaming ingestion to pilot seller in publish workflow`
  - `2ba6017e30d feat(PlayTest): add support for XORc Xbox Live title id resolution`
  - `ec15a400193 refactor(XPackageWorkflow): consume GSSV PlaytestTitleIngestion.JobParameters contract`
  - `5af5af505ad refactor(XPackageWorkflow): gate streaming ingestion at call site`
- **Merge-base:** `a1a258721690e1a4e5c2b542de3a73912585f403`.
- **Diff stat:** 12 files, 719 insertions, 4 deletions.
- **Key changes:**
  - Adds `XCloudPlaytestTitleIngestionBuilder`, consuming the GSSV `Microsoft.GameStreaming.Services.ContentCatalog.Common.Contracts.Workflows.PlaytestTitleIngestion.JobParameters` contract instead of a local mirror.
  - Builds a `StoreAsset` with game flag, default `RETAIL` sandbox, `MICROSOFT` partner id, default streaming platform `PC`, content id, package family name, AUMID default, parent product id, and nonzero `XboxTitleId`.
  - Validates required payload fields, non-empty DNA groups, future expiration, StoreAsset fields, `PackageFamilyName` for PC, nonzero `XboxTitleId`, and AUMID for game/PC.
  - Clamps expiration to `DateTime.UtcNow + 7 days`.
  - Adds `XboxLiveTitleId` to `PlaytestPublishJobParameters`.
  - Resolves Xbox Live title id in `PlaytestBusinessLogic` via XORc at publish time: BigId alternate-id lookup to XORc product, then Xbox Live config; best-effort null if missing/unavailable so standard publish is not blocked.
  - Gates streaming ingestion at the XPackage publish call site to pilot seller id `65050620`, with TODO to replace with ECS/creator opt-in.
  - Adds `XCloudPlaytestTitleIngestionGatewayRoute = "v3/playtest/playtesttitleingestion"`.
  - Current workflow builds and validates the SAGE payload and logs non-sensitive identifiers; it **does not yet POST** because there is no authenticated SAGE client/base URL/token in the repo.
  - Adds unit/integration test coverage for builder validation, expiration clamp, Xbox title id resolution plumbing, and publish workflow gating.

## Planned / remaining changes

- **SAGE/CTIN caller, token acquisition, operation-id persistence, and status polling.** Cross-tenant S2S call tasks now consolidated in [`FuturePlans/s2s-cross-tenant-call.md`](../FuturePlans/s2s-cross-tenant-call.md).
- **Manual PR approval remains a v1 known gap.** Partner Registry offering/title creation is an ADO PR that requires human approval; [`Blockers/manual-pr-polling.md`](../Blockers/manual-pr-polling.md) keeps that non-S2S gap documented.
- **Finalize Xbox Live title-id source.** `Blockers\xbox-live-title-id.md` says the xCloud contract requires nonzero `StoreAsset.XboxTitleId`; planned path is Playtest → XORc service-config API → Xbox Live service config from XCon. Remaining work is confirming endpoint/auth/inputs, adding Title ID to the service-config API response, wiring/removing placeholders, and ensuring `PlaytestProductDocumentBuilder` no longer emits empty `XboxLiveTitleId`.
- **Improve polling strategy after v1.** `FuturePlans\polling-strategy-refinement.md` keeps infinite retry for v1, then proposes foreground exponential backoff, background reconciliation, a possible 24h cap, alerting, and deciding the exact id/status contract.
- **Launch URL and status accuracy.** `FuturePlans\launch-link-and-status-accuracy.md` gives launch URL shape `https://play.xbox.com/play/launch/{productId}?offering.id=xpt{PlaytestProductId}`. Remaining work is returning/surfacing that URL and preventing early 404s by tying `StreamingReady` to terminal ingestion plus offering completion, and possibly an XProduct post-back/latency telemetry.
- **Replace pilot seller gate.** Current hardcoded seller `65050620` should become ECS-driven `enableInstantPlaytest` and creator opt-in gating.

## Open code TODOs / FIXMEs (in-branch)

Added by these branches (scanned from each branch's diff vs `origin/main`). The xbet branches carry the richest ADO work-item linkage — each TODO cites its Juno board item:

- `t-melanichen/playtest-ingestion-payload-builder` — `src/XPackage/XPackageWorkflow/XPackageWorkflow/Workflows/Playtest/XPackagePlaytestPublishWorkflow.cs`:
  - `TODO (AB#62684638)`: replace the hardcoded seller id `65050620` with ECS-driven `enableInstantPlaytest` / creator opt-in gating. → [AB#62684638](https://microsoft.visualstudio.com/Xbox/_workitems/edit/62684638)
  - `XboxLiveTitleId is resolved during publish by the producer (via XORc TODO (AB#62521457))` and passed in. → [AB#62521457](https://microsoft.visualstudio.com/Xbox/_workitems/edit/62521457)
  - `TODO (AB#62492628)`: send the payload to SAGE (`POST {XCloudPlaytestTitleIngestionGatewayRoute}`, JSON). SAGE/CTIN caller work is tracked in [`FuturePlans/s2s-cross-tenant-call.md`](../FuturePlans/s2s-cross-tenant-call.md). → [AB#62492628](https://microsoft.visualstudio.com/Xbox/_workitems/edit/62492628)
  - `XPackageWorkflow.csproj`: `TODO (AB#62696974)`: update `Version` to the first published version once the GSSV PR is published. → [AB#62696974](https://microsoft.visualstudio.com/Xbox/_workitems/edit/62696974)
- `t-melanichen/playtest-ingestion-workflow-wiring` and `t-melanichen/playtest-xboxtitleid-resolver` — `src/XPackage/XPackageWorkflow/XPackageWorkflow/Workflows/Playtest/PlaytestIngestionPayloadBuilder.cs`:
  - `// TODO: Confirm the partner identifier the receiver's Partner Registry expects. The seller` id mapping is still unverified (ties into [`Blockers/manual-pr-polling.md`](../Blockers/manual-pr-polling.md)).

## References

- Git branch/status commands run in `C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\Xbox.Xbet.Service` with `git -C "<path>" --no-pager ...`.
- Base: `origin/main`.
- Branch refs checked:
  - Local+pushed: `t-melanichen/playtest-ingestion-contracts`, `t-melanichen/playtest-ingestion-payload-builder`
  - Local only: `t-melanichen/playtest-ingestion-workflow-wiring`, `t-melanichen/playtest-xboxtitleid-resolver`
  - Remote only: `origin/t-melanichen/partner-registry-offering-service`, `origin/t-melanichen/xbet-sage-ingestion-payload`
- `PRProgress\07-XBET-15834601-playtest-ingestion-payload-builder.md`
- `Blockers\xbox-live-title-id.md`
- `Blockers\manual-pr-polling.md`
- `FuturePlans\launch-link-and-status-accuracy.md`
- `FuturePlans\polling-strategy-refinement.md`
