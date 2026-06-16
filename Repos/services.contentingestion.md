# Repo: services.contentingestion

**Role:** CTIN is the xCloud content-ingestion service side of Instantly Shareable Playtest. In this repo the work adds V3 workflow receiver/client routes, the Playtest title ingestion workflow (validate → asset ingest → package/version → ConfigurePlaytest), PC first-install readiness polling, and local cross-tenant S2S authorization wiring.

**Base used for git comparisons:** `origin/main` (selected because `origin/main` exists; `origin/master` also exists). All branch commit lists are `git -C "C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\services.contentingestion" --no-pager log --oneline origin/main..<branch>`. All diff stats use `merge-base origin/main <branch>` then `diff --stat <mergebase>..<branch>`.

## Changes made

### Branch: `t-melanichen/playtest-title-ingestion-workflow` — pushed; PR 15800964, merged

> PRProgress quote: `# [CTIN] PR 15800964 — Playtest Title Ingestion Workflow`; `- **Status:** Merged`; `- **Source branch:** t-melanichen/playtest-title-ingestion-workflow → main`.

- Added the end-to-end V3 `PlaytestTitleIngestionWorkflow` for Instantly Shareable Playtest: validates playtest/title parameters, schedules one child `AssetIngestion` job, polls that child job instead of waiting on completion notifications, creates/reuses one neutral streaming package and version, calls Partner Registry `ConfigurePlaytestAsync`, and concludes based on workflow state.
- Added V3 service/client endpoints for `POST /v3/workflows/playtesttitleingestion` and `GET /v3/workflows/playtesttitleingestion/{jobId}`.
- Added the `PlaytestTitleIngestion` contract/state, telemetry conversion, workflow processor extensions, settings, dependency/package updates, and unit tests for job state and workflow behavior.
- Branch history also contains first-install readiness gating work; the tracked PRProgress document still calls PC polling the open follow-up, which is now separated into `t-melanichen/playtest-pc-install-polling`.

**Key files:**
- `src/Product/ContentCatalog.Ingestion.Core/Workflows/PlaytestTitleIngestionWorkflow.cs`
- `src/Product/ContentCatalog.Common.Contracts/Workflows/PlaytestTitleIngestion.cs`
- `src/Product/ContentCatalog.Ingestion.Service/Controllers/WorkflowsControllerV3.cs`
- `src/Product/ContentCatalog.Ingestion.Client/ContentIngestionClient.PlaytestWorkflows.cs`
- `src/Tests/Unit/ContentCatalog.Ingestion.Core.UnitTests/PlaytestTitleIngestionWorkflowTests.cs`

**Merge base:** `ad5fd36c6aac6ac07fc38195b8227d594287df0b`

**Diff stat:**
```text
Directory.Packages.props                           |   2 +-
 .../Workflows/PlaytestTitleIngestion.cs            | 141 +++++++
 .../Telemetry/TelemetryContext.Workflows.cs        |  10 +
 .../ContentIngestionClient.PlaytestWorkflows.cs    |  28 ++
 .../IContentIngestionClient.cs                     |  19 +
 .../Configuration/IngestionWorkflowSettings.cs     |   4 +
 .../ContentCatalog.Ingestion.Core.csproj           |   2 +
 .../Extensions/WorkflowProcessorExtensions.cs      |  16 +-
 .../Processors/IWorkflowsProcessor.cs              |   2 +-
 .../Implementations/WorkflowsProcessor.cs          |  11 +-
 .../Workflows/AssetIngestionWorkflow.cs            |   1 +
 .../Workflows/PlaytestTitleIngestionWorkflow.cs    | 407 +++++++++++++++++++++
 .../Controllers/WorkflowsControllerV3.cs           |  15 +
 .../appsettings.Test.json                          |   3 +
 .../appsettings.json                               |   5 +
 .../PlaytestTitleIngestionJobStateTests.cs         |  80 ++++
 .../PlaytestTitleIngestionWorkflowTests.cs         | 210 +++++++++++
 .../StartupTests.cs                                |   6 -
 .../TestAssemblyInitializer.cs                     |  23 ++
 19 files changed, 974 insertions(+), 11 deletions(-)
```

**Commits:**
```text
574d5a61 Fix comment
e11fb147 Rename serverAllocatorClient to xboxAllocatorClient in PlaytestTitleIngestionWorkflow
d921dc08 Fix playtest title ingestion hang: poll asset ingestion instead of suspending on a completion-notification callback
af1f56e3 Set AssetType in CreateAssetAsync from ingested asset
32842b1e Revert Service/Resolution test changes; keep Worker AssemblyInitialize fix
61f34207 Unit tests
7d8c4837 Replace asset ingestion polling policy with timeout; add playtest workflow tests
57ede6f6 Notifications from Test env
5af822af Addressing comments
56f2e9ae Addressing comments and remove notifs from prof
83b79349 rm references to pc polling; will implement in v2
07d709ef Change to schedule
4d29e0cd Addressing two comments
7ab7f8cd Gate playtest workflow success on confirmed first-install readiness
ba8eb20e Add PC first-install readiness probe (Phase 1, log-only, flag-gated)
7d8cade6 Resolving comments
5f789801 Comments
265c9c7b Branch PollFirstInstall by platform and add V3 playtest client methods
b7d17449 Comments
a369b835 Hard-fail no-package case in PollFirstInstall; align with TitleIngestion
6deb2984 Gate playtest first-install poll with notify stages; PC-only support
77cae02f Comment updates
aaa5444d Use shared GetPackageSourceId and simplify asset lookup in CreatePackageAsync
33488d59 Add PollFirstInstall stage to PlaytestIngestionWorkflow
667fe036 Comments
c63fdde1 Consume PlaytestRequest.GetOfferingId in playtest workflow
62fbc376 Suspend on child Asset Ingestion notification instead of polling
9a15998e Use canonical GenerateTitleId helper and [] collection expression
281c935a Make package creation idempotent in playtest workflow
357f23e5 Validate XboxTitleId and ExpirationTime at playtest submission
738952ae Fix stale doc comment after single-flight-id change
f51513f2 Use a single SUCU flight id for playtest ingestion
1e1ce61d Update title to match in partner reg
15b4676b Tighten PlaytestIngestion.JobParameters contract
b4036141 Pin Partners to stable 1.0.2606.501 (drop prerelease)
f3dadad1 Merge remote-tracking branch 'origin/main' into t-melanichen/playtest-title-ingestion-workflow
e722b620 Update comments
1ae76bfd Remove unused CorrelationId from Playtest ingestion contract
ec167de7 Validate Playtest StoreAsset is a game and DNA groups are non-empty
969a352a Use new workflow for playtestingestio and update nuget
749256c8 Add PlaytestTitleIngestionWorker (trimmed ProductIngestion copy)
8fb63e91 Add V3 Playtest ingestion receiver scaffold
```

### Branch: `t-melanichen/playtest-ingestion-receiver` — pushed

- Added the earlier V3 Playtest ingestion receiver scaffold: `POST /v3/workflows/playtestingestion` and `GET /v3/workflows/playtestingestion/{jobId}` in `WorkflowsControllerV3`.
- Added `PlaytestIngestion.JobParameters` / `JobStateV3`, validation, lock/partition-key helpers, workflow processor extension methods, telemetry conversion, and a stub workflow that validates parameters then returns an explicit not-yet-implemented status.
- This was foundational receiver plumbing; the later title-ingestion branch added the fuller `playtesttitleingestion` workflow shape.

**Key files:**
- `src/Product/ContentCatalog.Common.Contracts/Workflows/PlaytestIngestion.cs`
- `src/Product/ContentCatalog.Ingestion.Core/Workflows/PlaytestIngestionWorkflow.cs`
- `src/Product/ContentCatalog.Ingestion.Service/Controllers/WorkflowsControllerV3.cs`
- `src/Product/ContentCatalog.Ingestion.Core/Extensions/WorkflowProcessorExtensions.cs`

**Merge base:** `c58c6b2a360e2924a98d5c0d1fa44cb55e2c489e`

**Diff stat:**
```text
.../Workflows/PlaytestIngestion.cs                 | 139 +++++++++++++++++++++
 .../Telemetry/TelemetryContext.Workflows.cs        |  10 ++
 .../Extensions/WorkflowProcessorExtensions.cs      |  12 ++
 .../Workflows/PlaytestIngestionWorkflow.cs         |  70 +++++++++++
 .../Controllers/WorkflowsControllerV3.cs           |  17 +++
 5 files changed, 248 insertions(+)
```

**Commits:**
```text
8fb63e91 Add V3 Playtest ingestion receiver scaffold
```

### Branch: `t-melanichen/playtest-pc-install-polling` — pushed; PR not created yet in tracking docs

- Implemented version-aware PC first-install readiness polling in `PlaytestTitleIngestionWorkflow`.
- `PollFirstInstallAsync` now forks PC requests to `PollPcFirstInstallAsync`; that resolves the ingested package via `IResolutionProcessor.ResolveContentInstallMetadataAsync`, selects the PC version hash, and queries allocator/server state with `ServerPlatform.PC`, `ServerType.PC`, `LocalPackageId`, and `LocalPackageHash`.
- Empty server results retry using `FirstInstallPollingPolicy` with `NotifyInstallNotFoundAsync` fallback; matching servers transition to `NotifyReadyAsync`.
- Added/reworked unit tests for PC installed → ready, PC not installed → retry, unresolved PC version → retry, and no package → fail.

**Key files:**
- `src/Product/ContentCatalog.Ingestion.Core/Workflows/PlaytestTitleIngestionWorkflow.cs`
- `src/Tests/Unit/ContentCatalog.Ingestion.Core.UnitTests/PlaytestTitleIngestionWorkflowTests.cs`

**Merge base:** `4cc15d4fc17df9ea494cd7f979a479a78b45249b`

**Diff stat:**
```text
.../Workflows/PlaytestTitleIngestionWorkflow.cs    |  89 ++++++++++++--
 .../PlaytestTitleIngestionWorkflowTests.cs         | 129 +++++++++++++++++++--
 2 files changed, 200 insertions(+), 18 deletions(-)
```

**Commits:**
```text
b2e3a9e3 Implement PC install-readiness polling in PlaytestTitleIngestionWorkflow
```

### Branch: `t-melanichen/playtest-crosstenant-auth` — LOCAL ONLY; not pushed

- Added local-only CrossTenantS2S auth wiring based on Lakshey's cross-tenant approach: new auth scheme/policy constants, `MultiTenantAuthConfig`, Startup authentication/authorization setup, and policy-scheme selection between home and cross-tenant bearer auth.
- Gated the playtest ingestion endpoints in `WorkflowsControllerV3` with `[Authorize(AuthPolicyExtension.CrossTenantS2S)]`. **This gating (the two `[Authorize]` attributes + changing `AuthPolicyExtension.CrossTenantS2S` from `static readonly` to `const`) was merged separately via PR [15905881](https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.contentingestion/pullrequest/15905881) (branch `t-melanichen/playtest-ingestion-crosstenant-authorize`, merge commit `52fab53`); see [PRProgress/12-CTIN-15905881](../PRProgress/12-CTIN-15905881-gate-playtest-ingestion-crosstenant-s2s.md).**
- Added environment config sections for Green-tenant app registration and authorized client IDs in Test/Int/Prod settings. Do not treat this branch as pushed; git found no `origin/t-melanichen/playtest-crosstenant-auth` ref.

**Key files:**
- `src/Product/ContentCatalog.Ingestion.Core/Configuration/MultiTenantAuthConfig.cs`
- `src/Product/ContentCatalog.Ingestion.Core/Extensions/AuthPolicyExtension.cs`
- `src/Product/ContentCatalog.Ingestion.Core/Extensions/AuthSchemeExtension.cs`
- `src/Product/ContentCatalog.Ingestion.Service/Startup.cs`
- `src/Product/ContentCatalog.Ingestion.Service/Controllers/WorkflowsControllerV3.cs`
- `src/Product/ContentCatalog.Ingestion.Service/appsettings.Test.json`, `appsettings.Int.json`, `appsettings.Prod.json`

**Merge base:** `4cc15d4fc17df9ea494cd7f979a479a78b45249b`

**Diff stat:**
```text
.../Configuration/MultiTenantAuthConfig.cs         |  19 ++++
 .../Extensions/AuthPolicyExtension.cs              |  13 +++
 .../Extensions/AuthSchemeExtension.cs              |  15 +++
 .../Controllers/WorkflowsControllerV3.cs           |   6 ++
 .../ContentCatalog.Ingestion.Service/Startup.cs    | 119 +++++++++++++++++++++
 .../appsettings.Int.json                           |   5 +
 .../appsettings.Prod.json                          |   8 ++
 .../appsettings.Test.json                          |   9 +-
 8 files changed, 190 insertions(+), 4 deletions(-)
```

**Commits:**
```text
c468edfe Correct CTIN Prod AuthorizedClientIds note: xPackage id is the right layer
af08f095 Gate playtest ingestion endpoints with CrossTenantS2S policy
71ffdfb1 Merge remote-tracking branch 'origin/main' into t-melanichen/playtest-crosstenant-auth
f687ad80 Add Authorized client ids
b8a7d8c7 resolving comments
e7b56da5 Fix the misconfiged auth scheme
dd3f5d3d Adding CrossTenant Auth support for Corp->Green requests
```

## Planned / remaining changes

- [Blockers/pc-install-readiness-poll.md](../Blockers/pc-install-readiness-poll.md): PC polling is in progress in `t-melanichen/playtest-pc-install-polling`, but upstream install enablement is still pending. Remaining CTIN work includes finishing the PR, validating polling after title attach, and replacing interim assumptions.
- [FuturePlans/pc-install-readiness-polling-implementation.md](../FuturePlans/pc-install-readiness-polling-implementation.md): finish the pushed PC polling branch by adding the PC-playtest SUG constant when available, replacing interim region logic with env-specific config, confirming latest-version hash correctness, validating end-to-end install-on-attach, testing timeout behavior, creating/reviewing/merging the PR, deploying via CI/CD, and considering worker parity.
- [FuturePlans/s2s-cross-tenant-call.md](../FuturePlans/s2s-cross-tenant-call.md): cross-tenant S2S / SAGE integration tasks are consolidated there, including the verified CTIN receiver auth, SAGE pass-through route, xPackage caller client, token acquisition, credential decision, app-registration confirmation, and CI/CICD validation.
- [Blockers/aumid-pc.md](../Blockers/aumid-pc.md): v1 uses/needs a documented constant default AumID for PC; v1.1 should plumb the real ApplicationId from the AppX manifest and build `{PackageFamilyName}!{ApplicationId}`.
- [Blockers/manual-pr-polling.md](../Blockers/manual-pr-polling.md): Partner Registry offering/title attach is still a human-approved ADO PR. v1 should persist the returned job/operation id, poll status with effectively infinite retry, keep xPlaytest in waiting-for-ingestion until terminal, and document the manual approval gap.
- [FuturePlans/polling-strategy-refinement.md](../FuturePlans/polling-strategy-refinement.md): after end-to-end works, replace infinite retry with a designed foreground/background strategy, decide the exact poll id/status contract, add alerting thresholds, and determine the owner/location of reconciliation.
- [FuturePlans/delete-tombstone-lifecycle.md](../FuturePlans/delete-tombstone-lifecycle.md): implement the DELETE playtest ingestion path; get xCloud sign-off on tombstone + 7-day GC semantics; confirm GC grace period and ownership. Shared SAGE integration tracking points to [FuturePlans/s2s-cross-tenant-call.md](../FuturePlans/s2s-cross-tenant-call.md).

## Open code TODOs / FIXMEs (in-branch)

Added by these branches (scanned from each branch's diff vs `origin/main`). These are the in-code markers for the remaining PC-polling / ingestion work:

- `t-melanichen/playtest-title-ingestion-workflow` — `src/Product/ContentCatalog.Ingestion.Core/Workflows/PlaytestTitleIngestionWorkflow.cs`:
  - `// TODO: Enable PC playtest install readiness polling by ...` — the core PC-polling hook (continued in the polling branch). Tracks ADO WI [62492680 (Implement PC Polling)](https://microsoft.visualstudio.com/Xbox/_workitems/edit/62492680) and references [62688258](https://microsoft.visualstudio.com/Xbox/_workitems/edit/62688258).
  - `// TODO: replace the environment-provider region with env-specific config once available.`
  - `// TODO: Replace these interim Teams notifications with a programmatic completion` signal.
- `t-melanichen/playtest-pc-install-polling` — same file:
  - `// TODO: replace the environment-provider region with env-specific config once available.`
  - `// TODO: constrain to the PC playtest SUG once it is exposed as a SystemUpdateGroup constant.` References ADO WI [62521491](https://microsoft.visualstudio.com/Xbox/_workitems/edit/62521491).
- `t-melanichen/playtest-ingestion-receiver` — `src/Product/ContentCatalog.Ingestion.Core/Workflows/PlaytestIngestionWorkflow.cs`:
  - `// TODO (ADO XC3): Translate JobParameters.StoreAsset into the existing` ingestion contract.

These map directly to [`FuturePlans/pc-install-readiness-polling-implementation.md`](../FuturePlans/pc-install-readiness-polling-implementation.md) and [`FuturePlans/polling-strategy-refinement.md`](../FuturePlans/polling-strategy-refinement.md).

## References

- Git repo: `C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\services.contentingestion`
- Git commands used: base discovery (`rev-parse origin/main`, fallback `origin/master`/`main`), per-branch `log --oneline`, `merge-base`, `diff --stat`, `diff --name-only`, plus targeted `git grep`/`git show` on key changed files.
- PR tracking: [PRProgress/05-CTIN-15800964-playtest-title-ingestion-workflow.md](../PRProgress/05-CTIN-15800964-playtest-title-ingestion-workflow.md)
- Blockers: [pc-install-readiness-poll.md](../Blockers/pc-install-readiness-poll.md), [s2s-cross-tenant-call.md](../FuturePlans/s2s-cross-tenant-call.md), [aumid-pc.md](../Blockers/aumid-pc.md), [manual-pr-polling.md](../Blockers/manual-pr-polling.md)
- Future plans: [pc-install-readiness-polling-implementation.md](../FuturePlans/pc-install-readiness-polling-implementation.md), [polling-strategy-refinement.md](../FuturePlans/polling-strategy-refinement.md), [delete-tombstone-lifecycle.md](../FuturePlans/delete-tombstone-lifecycle.md)
