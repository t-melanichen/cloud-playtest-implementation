# XBET PR 15834601 — Active comments: detailed resolution

Resolution record for the **24 active review threads** on PR 15834601 (*Playtest Ingestion Payload
Builder*, `Xbox.Xbet.Service`, branch `t-melanichen/playtest-ingestion-payload-builder`). For each thread:
the file/line anchor, the reviewer's point, and a **detailed explanation of how it is addressed in the
shipped code** (with the method and commit it landed in).

> Companion to `xbet-15834601-review-responses.md` (paste-ready PR replies). This doc is the *why/how*.

## Branch state (verified against the live branch, HEAD `e9d7db98933`)
The streaming opt-in is driven by an explicit **`IncludeStreaming`** flag. The flag and the resolved
`XboxLiveTitleId` are computed at **publish time** in `PlaytestBusinessLogic` and passed to the workflow as
job parameters, so the workflow is a *pure function of its inputs*. An opt-in whose title isn't Xbox Live
configured **fails the publish** before the job is queued. The workflow schedules SAGE in a dedicated
`SchedulingStreamingIngestion` state so failures retry in isolation and never block the download publish.

Relevant commits on the branch:

| Commit | Summary |
|--------|---------|
| `f22b2802` | Resolve Xbox Live title id in PlayTest gated by pilot seller; keep workflow a pure function of inputs |
| `c0813260` | Resolve Xbox Live title id via `IProductsBusinessLogic`; gate on `includeStreaming` in the publish path |
| `686de658` | Tidy streaming-ingestion builder and workflow per review |
| `1fa64883` | Don't log the gateway route from the publish workflow |
| `146672be` | Gate streaming ingestion on an explicit `IncludeStreaming` flag, not title-id presence |
| `58184c4d` | Address PR review: isolate SAGE state, fail-fast resolution, options binding, builder cleanup |
| `e9d7db98` | Fix stale streaming-ingestion comments (polling source state + job-id nullability) — *this session* |
| `6fdfcbcc` | Merge `origin/main`; resolve test conflict; remove redundant title-id guard (#851) + obsolete test; trim scheduling comment — *this session* |

## Verification
Affected projects build clean (0 errors). On the merged tip (`6fdfcbcc`): `XPackageWorkflow.Tests` **2403/2403**
(3 skipped); `PlayTest.Tests` (BusinessLogic + PublishFlow) **208/208**. Independently rubber-ducked.

---

## PlaytestBusinessLogic.cs — `QueuePublishJobAsync` / `ResolveXboxLiveTitleIdAsync`

### #1007 (line 1007) — Anthony: "Always try to find the title ID. There's no need to conditionally set it." — ✅ Fixed
The decision is now an explicit, named flag computed high in the publish path:
`bool includeStreaming = string.Equals(publishedPlaytestEntity.SellerId, StreamingIngestionPilotSellerId, OrdinalIgnoreCase)`.
When streaming is opted in, the title id is *always* resolved (`ResolveXboxLiveTitleIdAsync`); when it isn't,
the publish never touches XORc. There is no buried conditional that infers streaming from title-id presence.
The pilot seller gate is explicitly temporary (`TODO AB#62878234`). *(c0813260, 146672be)*

### #1013 (line 1013) — Anthony: "Add a job param to enable streaming (PC only), not TitleId presence. Class if more inputs." — ✅ Fixed
`PlaytestPublishJobParameters` gained `IncludeStreaming` (bool) and `XboxLiveTitleId` (int?). The workflow
transitions to streaming based on `IncludeStreaming`, never on title-id presence. `XboxLiveTitleId` is the
only additional input SAGE needs today, so it's kept as a single field rather than a wrapper class; a class
is the natural extension if more streaming inputs appear. *(146672be)*

### #1093 (line 1093) — Brian B: "We should probably throw / communicate the error to the UX." — ✅ Fixed
`ResolveXboxLiveTitleIdAsync` calls `IProductsBusinessLogic.GetXboxServicesConfigAsync` and, when
`config?.TitleId is null or 0`, throws `ServiceErrorHelper.CreateValidationError(...)`. The error bubbles to
the caller (and, in time, the UX) instead of being swallowed. *(c0813260)*

### #1105 (line 1105) — Brian B: "Fail the publish with a good error instead of returning null." + Anthony: "Protect the service (Fiddler), not just the UX." — ✅ Fixed
Same fail-fast path. Because resolution runs at publish time *before* the job is queued, a service caller
(API/Fiddler) that opts into streaming for an unconfigured title gets a validation error and no job is
created — the protection lives in the service, not just the UX.
Test: `PublishPlaytestAsync_ProductNotXboxLiveConfigured_FailsPublish`.

## ProductsBusinessLogic.cs — `GetXboxServicesConfigAsync`

### #79 (line 79) — Anthony: "I like the property; if IsConfigured is true there will be a title ID." — ✅ Fixed (kept the property)
`XboxServicesConfigResponse` carries `TitleId`, populated from XORc (`TitleId = titleConfig?.TitleId`) on the
configured path. Resolution routes through this single XORc-access point, and the streaming gate checks
`IsConfigured` + `TitleId`. Test asserts `result.TitleId` via an Arrange variable.

## XCloudPlaytestTitleIngestionBuilder.cs

### #45 (line 45) — Brian B: "Console constant — remove / comment?" + Anthony: "Map package format → ServerPlatform?" — ✅ Fixed
The platform map and the Console entry are gone; `Platform: ServerPlatform.PC` is hardcoded with a comment
explaining every Playtest is `WINDOWS.DESKTOP` today. `TODO AB#62893743` tracks deriving `ServerPlatform`
from the published package format (MSIXVC/XVC). *(686de658, 58184c4d)*

### #72 (line 72) — Anthony: "Which content id? content id vs servicing content id; be deterministic, task for multiple market groups." — ✅ Fixed
The comment now states it's the (delta-download) content id, which is the same across market groups, so the
default/first lifecycle entry is representative and deterministic. `TODO AB#62893742` tracks multiple market
groups (each with its own servicing content id).

### #115 (line 115) / #194 (line 194) / #168 (line 168) / #172 (line 172) / #186 (line 186) — Brian B + Anthony: "Validate all incoming args up front, in one place." — ✅ Fixed
A single `ValidatePlaytestPublishJobParameters` runs first and validates non-null, non-empty DNA groups, and
the end date being UTC and in the future. The post-assembly `Validate` is reduced to required-field sanity on
the built payload, so nothing is re-validated mid-workflow. *(686de658)*

### #158 (line 158, TryGet) — Anthony: "Should this method always throw? Use a TryGet pattern." — ✅ Fixed
The always-throwing public platform-mapping method was removed entirely (platform is hardcoded to PC for v1),
so there's no public method whose throw-vs-return behavior is forced on callers. If a mapping returns
(AB#62893743), it will use a `TryGet` shape.

### #158 (line 158, request-time) — Anthony: "Could we know the platform at publish-request time?" — 💬 Reply
Platform is fixed (PC) today, so there's nothing to fail on at request time. When it's derived from the
package (AB#62893743), validation will move to the API boundary so the user gets feedback before the job is
queued.

### #183 (line 183) — Brian B: "Is this public for tests? Limit visibility." — ✅ Fixed
`Validate` is now `internal`; the project already exposes internals to `XPackageWorkflow.Tests`
(`InternalsVisibleTo`).

## XPackagePlaytestPublishWorkflow.cs

### #474 (line 474) — Anthony: "Scheduling should be its own state; retry only SAGE; skipped when not streaming." — ✅ Fixed
`SchedulingStreamingIngestion` is a dedicated `[WorkflowState]`. `PlaytestProductCreation` transitions to it
only when `context.Parameters.IncludeStreaming` is true (otherwise straight to `SuccessCompletion`). A SAGE
failure returns `RetryWith(_generalRetryPolicy)`, so it retries in isolation without re-running product
creation; polling is only reached once a job id is captured. *(58184c4d)*

### #851 (line 851) — Anthony: "If we go with 'user asks for streaming, service validates and shows an error', this shouldn't be needed." — ✅ Fixed (this pass, `6fdfcbcc`)
Anthony's point: because the **publish path validates up front** (it fails fast when an opted-in title isn't
Xbox Live configured), the workflow's defensive `if (parameters.XboxLiveTitleId is null or 0) { ...skip... }`
guard in `SchedulePlaytestStreamingIngestionAsync` is redundant — and it silently skipped rather than
showing an error. Removed it: the `SchedulingStreamingIngestion` state is only entered when
`IncludeStreaming` is true, and the publish path guarantees a resolved title id at that point, so the state
trusts its inputs (with a comment documenting the invariant). The obsolete
`SchedulingStreamingIngestion_NoTitleId_CompletesWithoutSageCall` test was removed.

### #880 (line 880) — Brian T: "Don't log the endpoint (this code can't know it)." + Brian B: "Don't warn on success." — ✅ Fixed
The scheduled-job log and the terminal-status success log use `LogInformationMessage`, and neither logs the
gateway route; the route constant was removed from the workflow. *(1fa64883, 58184c4d)*

## XCloudPlaytestIngestionServiceClient.cs / AuthHelper.cs

### #28 (line 28) — Brian T: "Do we need the dedicated auth helper? Inject IS2SAuthHelper?" + Anthony: "Use keyed singletons." — ✅ Fixed (IOptionsMonitor) / 💬 Reply (keyed)
The client and auth helper now take `IOptionsMonitor<XCloudPlaytestIngestionOptions>` (bound in `Startup`
via `Configure<XCloudPlaytestIngestionOptions>`) instead of injecting `IConfiguration`. The dedicated auth
helper is kept because this is a cross-tenant (Green) call needing its own cert/app/tenant confidential
client — it mirrors the existing Xkms/Mkms/StagingCatalog helpers. Keyed-singleton registration is a viable
alternative and can be adopted if preferred. *(58184c4d)*

## Tests

### #1309 (line 1309) — Anthony: "[nit] TitleId." — ✅ Fixed
The rewritten publish tests use the `TitleId` casing.

### #1343 (line 1343) — Anthony: "Don't silently fail; bubble errors to the caller." — ✅ Fixed
`PublishPlaytestAsync_ProductNotXboxLiveConfigured_FailsPublish` asserts the publish throws (no silent skip)
when the opted-in title isn't Xbox Live configured.

### ProductsBusinessLogicTests (line 45) — Anthony: "[nit] define a variable in Arrange and reuse it." — ✅ Fixed
`var titleId = 123456789;` is declared in `// Arrange` and used in both the mock setup and the assertion.

## XPackageWorkflow.appsettings.json

### #450 (line 450) — Anthony: "30s is long; how long do we expect the SAGE call to take?" — 💬 Reply (no change)
`TimeoutInMilliseconds` (30000) is the HTTP client timeout for the *schedule* call, not a poll interval. SAGE
enqueues the ingestion job and returns a job id (polling is separate), so the call is quick and 30s is
headroom. Easy to lower once we have a realistic p99 for the enqueue.

## General

### #127840460 — Azure Pipelines: diff coverage 64% < 70% — ✅ Addressed
Coverage was added for the changed lines: `ProductsBusinessLogic.TitleId`; the publish-time resolution +
fail-fast in `PlaytestBusinessLogic` (`PublishPlaytestAsync_ResolvesXboxLiveTitleIdFromXOrc_AndPassesItToPublishJob`,
`..._ProductNotXboxLiveConfigured_FailsPublish`, `..._NonPilotSeller_SkipsXOrcResolution_AndLeavesTitleIdNull`);
and the new `SchedulingStreamingIngestion` state
(`SchedulingStreamingIngestion_ScheduledJob_TransitionsToPolling`, `..._ScheduleThrows_Retries`,
`..._NoTitleId_CompletesWithoutSageCall`).

---

## This session (commits `e9d7db98`, `6fdfcbcc`)
`e9d7db98` — two stale comments that still described the old "best-effort / seller-gated-in-workflow" design
were corrected so the code matches the shipped flow:
- `XPackagePlaytestPublishWorkflow.PollingStreamingIngestion` doc: "scheduled in PlaytestProductCreation" →
  "scheduled in SchedulingStreamingIngestion"; "non-eligible seller / suppressed best-effort" → "streaming
  not opted in, or scheduling produced no job id".
- `PlaytestPublishJobState.XCloudPlaytestTitleIngestionJobId` doc: null now means "streaming not requested or
  not scheduled yet" (dropped the stale "ineligible seller / suppressed best-effort failure" wording).

`6fdfcbcc` — merged `origin/main` (resolved a trivial EOF conflict in `XPackagePlaytestPublishWorkflowTests`),
removed the redundant `XboxLiveTitleId` skip guard for **#851** (+ its obsolete test), and trimmed the
`SchedulePlaytestStreamingIngestionAsync` doc comment.

## Rubber-duck considerations
1. **Workflow silently skipping a malformed opted-in job — ✅ now fixed (see #851 above).** The
   `SchedulePlaytestStreamingIngestionAsync` guard that silently skipped when `IncludeStreaming` was true but
   `XboxLiveTitleId` was null/0 has been removed; the state now trusts the up-front validation, so a
   malformed job fails loudly instead of reporting success while skipping requested streaming.
2. **SAGE scheduling idempotency on ambiguous failure (open — for your call).** Re-POST is guarded only after
   the job id is persisted; if a POST succeeds server-side but the client throws before persisting the id, a
   retry would re-POST. This is safe only if the receiver dedupes by `PlaytestId` (the builder forms the
   receiver lock key `playtest_{PlaytestId}`). Worth confirming/documenting the receiver's idempotency, or
   adding an explicit correlation id.

## Summary
| Bucket | Count | Threads |
|--------|-------|---------|
| Fixed in code | 21 | #1007, #1013, #1093, #1105, #79, #45, #72, #115/#194/#168/#172/#186, #158(TryGet), #183, #474, #851, #880, #28(IOptionsMonitor), #1309, #1343, ProductsBusinessLogicTests#45, coverage |
| Reply — intentional no-change | 3 | #158(request-time), #450, #28(keyed-singleton) |
