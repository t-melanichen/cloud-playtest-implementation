# XBET PR 15834601 — Review responses (fixes + replies)

Per-comment record for **PR 15834601** (*Playtest Ingestion Payload Builder*, `Xbox.Xbet.Service`,
branch `t-melanichen/playtest-ingestion-payload-builder`). For each of the **24 active threads**: the
**status**, the **change** that addresses it (by file/method — the work lands in the next commit on the
branch), and a **paste-ready reply**.

> Nothing is resolved on the PR yet and replies are pasted by hand — these are drafts, not posted.

## Final design (settled 25–26 June)
Streaming is **optional**, driven by an explicit **`IncludeStreaming`** flag instead of inferring it from
the title id. The flag and the resolved title id are computed at **publish time** (PlayTest) and passed to
the workflow as job parameters, so the workflow stays a *pure function of its inputs*:

- `PlaytestBusinessLogic.QueuePublishJobAsync` sets `IncludeStreaming` (pilot **seller gate** today, the
  persisted flag / ECS allowlist later) and, when it's true, resolves the Xbox Live title id via
  `IProductsBusinessLogic`. If the title isn't Xbox Live configured the publish **fails fast** with a clear
  error — it no longer returns null / silently skips. Download-only publishes never touch XORc.
- The workflow gates on the flag (not on title-id presence). A dedicated **`SchedulingStreamingIngestion`**
  state builds + POSTs the SAGE payload and is only transitioned to when `IncludeStreaming` is true, so a
  SAGE failure retries in isolation without re-running product creation. Streaming never blocks the
  download publish.

This supersedes the earlier "resolve inside the workflow, best-effort null" shape.

## Changes by file
| File | What changed |
|------|--------------|
| `PlayTest.Shared/Contracts/XboxServicesConfigResponse.cs` | Added `TitleId` (`[ProtoMember(4)]`). |
| `PlayTest/BusinessLogic/ProductsBusinessLogic.cs` | Populate `TitleId` from XORc when configured. |
| `PlayTest/BusinessLogic/PlaytestBusinessLogic.cs` | Inject `IProductsBusinessLogic`; pilot seller gate sets `IncludeStreaming`; resolve title id + fail-fast at publish time. |
| `XPackageWorkflow.Shared/.../PlaytestPublishJobParameters.cs` | Added `IncludeStreaming` + `XboxLiveTitleId`. |
| `XPackageWorkflow/.../XCloudPlaytestTitleIngestionBuilder.cs` | Up-front `ValidatePlaytestPublishJobParameters`; `Validate` → `internal`; PC hardcoded (platform map + throwing mapper removed); `DefaultPartnerId` → `MicrosoftPartnerId`; content-id comment; end-date null/`ToUniversalTime` cleanup; async XORc path removed. |
| `XPackageWorkflow/.../XPackagePlaytestPublishWorkflow.cs` | New `SchedulingStreamingIngestion` state; gate on `IncludeStreaming`; seller-id list + route constant + XORc dependency removed; success logs warning → info. |
| `XPackageWorkflow/ServiceClients/XCloudPlaytestIngestion/` | New `XCloudPlaytestIngestionOptions`; client + auth helper take `IOptionsMonitor<T>`; temp token-claims diagnostic removed. |
| `Startup.cs` | `Configure<XCloudPlaytestIngestionOptions>`. |
| Tests | Builder/workflow/PlayTest tests updated + new streaming coverage. |

## Follow-up ADO tasks referenced in replies
- **AB#62684638** — replace the pilot seller-id gate with the persisted `IncludeStreaming` flag / ECS allowlist.
- **AB#62893742** — support multiple market groups (distinct servicing content ids).
- **AB#62893743** — derive `ServerPlatform` from the published package format (MSIXVC/XVC).
- **AB#62881045** — add Console (Xbox) platform support.

---

## PlaytestBusinessLogic.cs

### #1007 — "Always try to find the title ID; no conditional" — ✅ Fixed
**Change:** Streaming is now an explicit `IncludeStreaming` decision rather than a buried conditional; when
a publish opts in, the title id is always resolved at publish time (`QueuePublishJobAsync`).
**Reply:** Reworked — streaming is an explicit decision now (the `IncludeStreaming` flag), not a buried
conditional. When a publish opts in we always resolve the title id; download-only publishes never touch
XORc.

### #1013 — "Add a job param to enable streaming; don't use TitleId presence; consider a class" — ✅ Fixed
**Change:** Added `IncludeStreaming` to `PlaytestPublishJobParameters`; the workflow gates on it.
**Reply:** Added `IncludeStreaming` to `PlaytestPublishJobParameters` and the workflow gates on that
instead of TitleId presence. `XboxLiveTitleId` is the only extra input SAGE needs today so I kept it a
single field; if we add more streaming inputs I'll wrap them in a dedicated class.

### #1105 — "Don't return null; fail the publish if not XBL-configured" — ✅ Fixed
**Change:** Resolution moved to `QueuePublishJobAsync`; when opted in but not Xbox Live configured it
throws `ServiceErrorHelper.CreateValidationError`.
**Reply:** Done — resolution happens at publish time now, and when a publish opts into streaming but the
title isn't Xbox Live configured it fails with a validation error instead of returning null. That protects
the service path too, not just the UX (your Fiddler point).

### #1093 — "Same here … throw" — ✅ Fixed
**Reply:** Same fix — it throws now (see above), so the error surfaces to the caller rather than silently
dropping streaming.

## ProductsBusinessLogic.cs

### #79 — "If IsConfigured is true there will be a title ID" — ✅ Fixed (kept the property)
**Change:** Added `TitleId` to `XboxServicesConfigResponse`, populated from XORc whenever the title is
configured.
**Reply:** Kept the property as you said you were fine with — added `TitleId` to the response and populate
it whenever the title's configured. `PlaytestBusinessLogic` gates streaming on `IsConfigured` + `TitleId`.

## XCloudPlaytestTitleIngestionBuilder.cs

### #45 — "Console constant — remove / comment?" (+ Anthony: map package format → ServerPlatform) — ✅ Fixed
**Change:** Removed the platform map and the Console entry; `Platform` is hardcoded to `ServerPlatform.PC`
with a comment + task refs.
**Reply:** Removed the map and the Console entry — platform is hardcoded to PC for v1 with a comment.
Deriving `ServerPlatform` from the package format (MSIXVC/XVC) is AB#62893743; Console support is
AB#62881045.

### #72 — "Which content id? multiple market groups" — ✅ Fixed
**Change:** Clarified the comment (it's the delta-download content id, shared across market groups; default
market group taken deterministically) + AB#62893742.
**Reply:** It's the content id (delta-download), not the servicing content id, so it's the same across
market groups — clarified the comment and made it explicit we take the default/first market group
deterministically. Multiple market groups (distinct servicing content ids) is AB#62893742.

### #115 / #194 / #168 / #172 / #186 — "Validate incoming args up front, in one place" — ✅ Fixed
**Change:** Consolidated null/DNA-group/end-date (UTC + future) checks into one up-front
`ValidatePlaytestPublishJobParameters`; the post-assembly `Validate` is now just required-field sanity.
**Reply:** Done — pulled all the incoming-argument checks (non-null, DNA groups, end date UTC + future)
into one up-front `ValidatePlaytestPublishJobParameters`. The post-assembly `Validate` is now just
required-field sanity on the built payload, so the layers below don't re-validate.

### #158 (TryGet) — "Should this method always throw? TryGet pattern" — ✅ Fixed
**Change:** Removed the mapping method (PC hardcoded).
**Reply:** Removed the mapping method entirely — platform is hardcoded to PC for v1, so there's no
always-throwing public method anymore. If we reintroduce a mapping (AB#62893743) I'll use a `TryGet` shape.

### #158 (request-time) — "Could we know platform at publish-request time?" — 💬 Reply
**Reply:** Platform is fixed (PC) today, so there's nothing to fail on at request time. When we derive it
from the package (AB#62893743) I'll validate it at the API boundary so the user gets feedback before the
job is queued.

### #183 — "Limit visibility" — ✅ Fixed
**Change:** `Validate` is now `internal` (`InternalsVisibleTo("XPackageWorkflow.Tests")` already present).
**Reply:** Made `Validate` internal — the project already exposes internals to `XPackageWorkflow.Tests`.

## XPackagePlaytestPublishWorkflow.cs

### #474 — "Scheduling should be its own state, skipped when not streaming" — ✅ Fixed
**Change:** Added `SchedulingStreamingIngestion`; `PlaytestProductCreation` transitions to it only when
`IncludeStreaming`, otherwise straight to `SuccessCompletion`; failures `RetryWith(_generalRetryPolicy)`.
**Reply:** Done — `SchedulingStreamingIngestion` is its own state now, only transitioned to when
`IncludeStreaming` is true (skipped otherwise), so a SAGE failure retries in isolation without re-running
product creation. Polling is only reached once a job's been scheduled.

### #851 — "Gate not needed if we validate enablement up front" — ✅ Fixed
**Change:** The seller gate moved to publish time (it sets `IncludeStreaming`); the workflow keys off the
flag — the in-workflow title-id/seller gate is gone.
**Reply:** Right — the seller gate moved to publish time (it sets `IncludeStreaming`) and the workflow just
keys off the flag, so the redundant in-workflow gate is gone.

### #880 — "Don't log the endpoint" + Brian B "don't warn on success" — ✅ Fixed
**Change:** Dropped the route from the scheduled-job log and removed the unused route constant; demoted the
scheduled/terminal success logs from warning to info.
**Reply:** Dropped the route from the log (this code can't know the endpoint anyway) and removed the unused
route constant. Also demoted the scheduled/terminal success logs from warning to info.

## XCloudPlaytestIngestionServiceClient.cs / AuthHelper.cs

### #28 (Brian T: inject `IS2SAuthHelper`?) + Anthony (keyed singletons) — ✅ Fixed (IOptionsMonitor) / 💬 Reply (keyed)
**Change:** Added `XCloudPlaytestIngestionOptions`, bound the section in `Startup`; the client and auth
helper now take `IOptionsMonitor<XCloudPlaytestIngestionOptions>` instead of `IConfiguration`.
**Reply:** Switched both to `IOptionsMonitor<XCloudPlaytestIngestionOptions>` (bound in Startup). On keyed
`IS2SAuthHelper` — that works, but this is a cross-tenant (Green) call that needs its own cert/app/tenant
confidential client, so I kept the dedicated helper that mirrors the Xkms/Mkms/StagingCatalog pattern.
Happy to move to keyed registration if you'd prefer it over the per-client helper.

## Tests

### #1343 — "Bubble errors, don't silently fail" — ✅ Fixed
**Change:** New publish tests assert the publish throws when the title isn't configured
(`PublishPlaytestAsync_PilotSellerNotXblConfigured_ThrowsAndDoesNotQueueJob`).
**Reply:** Resolution bubbles/fails now — the new publish tests assert the publish throws (and never queues
the job) when the title isn't Xbox Live configured, instead of silently skipping.

### #1309 — "[nit] TitleId" — ✅ Fixed
**Reply:** Addressed in the rewritten tests (TitleId casing).

### ProductsBusinessLogicTests #45 — "[nit] define a variable in Arrange" — ✅ Fixed
**Change:** Extracted a `titleId` variable in `// Arrange`, used in both the mock setup and the assertion.
**Reply:** Done — pulled a `titleId` variable into Arrange and use it in both the setup and the assertion.

### #127840460 — Diff coverage 64% < 70% — ✅ Addressed
**Change:** Added coverage for the changed lines: `ProductsBusinessLogic.TitleId`; publish-time streaming
resolution (configured + fail-fast) in `PlaytestBusinessLogic`; and the `SchedulingStreamingIngestion`
state (schedule / idempotent / retry) in the workflow.
**Reply:** Added unit coverage for the changed lines — the title-id resolution + fail-fast in PlayTest and
the new scheduling state in the workflow — which should clear the 70% diff-coverage gate.

## appsettings.json

### #450 — "30s is long; how long does SAGE take?" — 💬 Reply (not changed)
**Reply:** That's `TimeoutInMilliseconds` (30000) — the HTTP client timeout for the schedule call, not a
poll interval. SAGE just enqueues the ingestion job and returns a job id (we poll separately), so the call
itself is quick and 30s is headroom. Happy to lower it — what's a realistic p99 for the enqueue?

---

## Housekeeping (not review threads)
- Removed the temporary outbound-token-claims diagnostic from `XCloudPlaytestIngestionServiceClient`
  (added to debug the CTIN audience failure, which is resolved) — it was marked *remove before merge*.

## Validation
All affected projects build clean (0 errors). Targeted unit tests pass:
- `XPackageWorkflow.Tests` (Playtest filter): **153/153**.
- `PlayTest.Tests` (BusinessLogic + PublishFlow): **206/206**.

## Summary
| Bucket | Count | Threads |
|--------|-------|---------|
| Fixed in code | 19 | #1007, #1013, #1105, #1093, #79, #45, #72, #115/#194/#168/#172/#186, #158(TryGet), #183, #474, #851, #880, #28(IOptionsMonitor), #1343, #1309, ProductsBusinessLogicTests#45, coverage |
| Reply — intentional no-change | 3 | #158(request-time), #450, #28(keyed-singleton) |
