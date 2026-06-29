# XBET PR 15834601 — Review responses (fixes + replies)

Per-comment record for the second review pass on **PR 15834601** (*Playtest Ingestion Payload Builder*,
`Xbox.Xbet.Service`, branch `t-melanichen/playtest-ingestion-payload-builder`). For each active thread:
the **status**, the **commit** that addresses it, and a **paste-ready reply**.

> As of this writing nothing is resolved on the PR — replies are pasted by hand. Of 32 active threads:
> **24 fixed in code**, **8 are replies** (5 intentional no-change, 3 covered by follow-up ADO tasks).

## Commit legend
| Tag | Commit | What it did |
|-----|--------|-------------|
| A | `c081326` | Resolve title id via `IProductsBusinessLogic`; gate on `includeStreaming` high in the publish path |
| B | `686de65` | Builder/validation tidy (up-front `ValidatePlaytestPublishJobParameters`, `Validate` internal) |
| C | `1fa6488` | Drop the gateway route from the publish-workflow log + remove the route constant |
| D | `146672b` | Explicit `IncludeStreaming` flag on job params; workflow gates on the flag, not title-id presence |
| E | `58184c4` | Own `SchedulingStreamingIngestion` state, fail-fast resolution, `IOptionsMonitor`, builder cleanup |

## Follow-up ADO tasks referenced in replies
- **AB#62878234** — replace the temporary pilot seller-id gate with the persisted/UX-driven `IncludeStreaming` flag.
- **AB#62893742** — support multiple market groups (distinct servicing content ids).
- **AB#62893743** — derive the streaming platform from the published package format instead of hardcoding PC.
- **AB#62881045** — add Console (Xbox) platform support.

---

## PlaytestBusinessLogic.cs

### #1007 — "Always try to find the title ID, no conditional" — ✅ Fixed (A, D)
**Fix:** Moved the decision to a named `includeStreaming` at the top of the publish path; resolve only when true.
**Reply:** Reworked — moved the decision to a named `includeStreaming` at the top of the publish path and resolve only when it's true. Streaming is now driven by an explicit `IncludeStreaming` flag, not a buried conditional.

### #1013 — "Add a job param to enable streaming; don't use TitleId presence; consider a class" — ✅ Fixed (D)
**Fix:** Added `IncludeStreaming` to `PlaytestPublishJobParameters`; workflow gates on it.
**Reply:** Added `IncludeStreaming` to `PlaytestPublishJobParameters` and the workflow gates on that. Right now `XboxLiveTitleId` is the only input SAGE needs, so I kept it a single field; if we add more streaming inputs I'll wrap them in a dedicated class.

### #1105 / #1093 — "Don't return null; fail the publish if not XBL-configured" — ✅ Fixed (E)
**Fix:** Resolution throws a validation error when opted in but not Xbox Live configured; XORc errors bubble.
**Reply:** Done — when streaming is opted in but the product isn't Xbox Live configured, the publish now fails with a validation error instead of silently returning null. This protects the service path too (not just the UX), per your Fiddler point.

## ProductsBusinessLogic.cs

### #79 — "If IsConfigured is true there will be a title ID" — ✅ Ack (no change requested)
**Reply:** Agreed — kept the separate `TitleId` property as you said you were fine with; it's populated whenever `IsConfigured` is true.

## XCloudPlaytestTitleIngestionBuilder.cs

### #45 — "Console constant — remove for now / comment?" (+ package-format→platform) — ✅ Fixed (B, E)
**Fix:** Removed the platform mapping entirely, hardcoded PC for v1.
**Reply:** Removed the platform mapping entirely and hardcoded PC for v1. Deriving `ServerPlatform` from the package format (MSIXVC/XVC) is tracked in AB#62893743; Console support in AB#62881045.

### #115 / #194 — "Validate all args up front in one function" — ✅ Fixed (B)
**Fix:** Consolidated DNA-group + end-date (UTC + future) checks into `ValidatePlaytestPublishJobParameters`.
**Reply:** Done — consolidated DNA-group and end-date (UTC + future) checks into one up-front `ValidatePlaytestPublishJobParameters`; the post-assembly `Validate` is now just required-field sanity.

### #183 — "Limit visibility" — ✅ Fixed (B)
**Fix:** Made `Validate` `internal` (`InternalsVisibleTo("XPackageWorkflow.Tests")` already present).
**Reply:** Made `Validate` `internal` (the project already has `InternalsVisibleTo("XPackageWorkflow.Tests")`).

### #72 — "Which content id? multi market group" — ✅ Fixed (E)
**Fix:** Clarified the comment + deterministic default entry; AB#62893742 for multiple market groups.
**Reply:** Clarified the comment (it's the playtest content id, shared across market groups) and made it deterministic on the default/first entry, with AB#62893742 to handle multiple market groups (distinct servicing content ids) later.

### #84 — "Empty parentProductIds — valid state?" — 💬 Reply (intentional, no change)
**Reply:** Yes — empty is valid; it just means no source product to trace back, which the receiver tolerates. Left the empty-array fallback rather than throwing.

### #106 — "Derive platform from package, not hardcoded" — ✅ Fixed (E)
**Fix:** Hardcoded PC for v1 with a comment; AB#62893743 to derive from package format.
**Reply:** Agreed — hardcoded PC for v1 with a comment, and entered AB#62893743 to derive it from the published package format.

### #120 — "Is empty/null end date really possible? MaxValue ToUniversalTime" — ✅ Fixed (E)
**Fix:** `PlaytestEndDate` is non-nullable; removed the null path and the `ToUniversalTime` call.
**Reply:** Good catch — `PlaytestEndDate` is non-nullable so the null path couldn't happen; removed it and now compare directly (no `ToUniversalTime`), so no MaxValue overflow risk.

### #121 — "ToUniversalTime needed again?" — ✅ Fixed (E)
**Reply:** No — since the end date is validated UTC up front, I dropped the redundant `ToUniversalTime()`.

### #130 — "Name it MicrosoftPartnerId" — ✅ Fixed (E)
**Reply:** Renamed `DefaultPartnerId` → `MicrosoftPartnerId`. It's always Microsoft for playtest offerings, so I kept it a constant rather than a parameter.

### #158 (TryGet) — "Should this always throw? TryGet pattern" — ✅ Fixed (E)
**Fix:** Removed the mapping method entirely (PC hardcoded).
**Reply:** Removed the method entirely — platform is hardcoded to PC for v1, so there's no public always-throwing mapping method anymore. If we reintroduce a mapping (AB#62893743) I'll use a `TryGet` shape.

### #158 (request-time) — "Could we know platform at publish-request time?" — 💬 Reply
**Reply:** Platform is fixed (PC) today, so there's nothing to fail on. When we derive it from the package (AB#62893743), I'll validate it at the API boundary so the user gets feedback before the job is queued.

### #168 / #172 / #186 — "Validate prior to creating the job, not in the workflow" — ✅ Fixed (B)
**Reply:** Agreed, and these are covered — argument validation is consolidated up front in `ValidatePlaytestPublishJobParameters`, and the throwing platform mapping is gone.

## XCloudPlaytestIngestionServiceClient.cs / AuthHelper.cs

### #27 / #16 — "Use IOptionsMonitor, don't inject IConfiguration" — ✅ Fixed (E)
**Fix:** Added `XCloudPlaytestIngestionOptions`, bound the section in `Startup`, both ctors take `IOptionsMonitor<T>`.
**Reply:** Done — added `XCloudPlaytestIngestionOptions`, bound the section in `Startup`, and both the client and auth helper now take `IOptionsMonitor<XCloudPlaytestIngestionOptions>`.

### #28 (Brian T) + keyed-singleton suggestion (Anthony) — 💬 Reply (IOptions done; keyed not done)
**Reply:** Switched both to `IOptionsMonitor<T>`. On keyed `IS2SAuthHelper` singletons — that works, but this is a cross-tenant (Green) call needing its own cert/app/tenant-built confidential client, and the dedicated helper mirrors the existing Xkms/Mkms/StagingCatalog pattern. Happy to move to keyed registration if you'd prefer it over the per-client helper.

## XPackagePlaytestPublishWorkflow.cs

### #474 — "Scheduling should be its own state, skipped when not streaming" — ✅ Fixed (E)
**Fix:** Extracted scheduling into `SchedulingStreamingIngestion`, only transitioned to when `IncludeStreaming`; failures propagate so retry is isolated (rubber-duck caught and fixed a swallowed-exception dead-retry).
**Reply:** Done — extracted scheduling into a dedicated `SchedulingStreamingIngestion` state that's only transitioned to when `IncludeStreaming` is true (skipped otherwise), so a SAGE failure retries in isolation without re-running product creation. Polling is likewise only reached when a job was scheduled.

### #851 — "Gate not needed if we validate enablement up front" — ✅ Addressed (D, E)
**Reply:** Right — with the fail-fast validation in PlayTest plus the `IncludeStreaming` flag, the scheduling state only runs when streaming is opted in; the title-id check is now just a defensive no-op.

### #872 — "Info, not warning" — ✅ Fixed (E)
**Reply:** Changed the scheduled-job and terminal-status success logs from warning to information.

### #880 — "Don't log the endpoint" + Brian B "don't warn on success" — ✅ Fixed (C, E)
**Reply:** Dropped the route from the log (and removed the unused route constant) since this code can't know the endpoint; also demoted the success log from warning to info.

## Tests

### #1343 — "Bubble errors, don't silently fail" — ✅ Fixed (E)
**Reply:** The resolution now bubbles/fails; updated the test to assert the publish throws when the product isn't configured (and a separate test that XORc errors bubble up).

### #1309 — "[nit] TitleId" — ✅ Fixed (E)
**Reply:** Addressed in the rewritten tests.

### ProductsBusinessLogicTests #45 — "[nit] define a variable in Arrange" — ✅ Fixed (E)
**Reply:** Done — extracted a `titleId` variable used in both the setup and the assertion.

## appsettings.json

### #450 — "30s is long; how long does SAGE take?" — 💬 Reply (not changed)
**Reply:** That's the HTTP client timeout for the schedule call, not a poll interval — SAGE just enqueues the ingestion job and returns a job id (we poll separately), so the call itself is quick and 30s is just headroom. Happy to lower it; what's a realistic p99 for the enqueue?

---

## Summary
| Bucket | Count | Threads |
|--------|-------|---------|
| Fixed in code | 24 | #1007, #1013, #1105/#1093, #45, #115/#194, #183, #72, #106, #120, #121, #130, #158(TryGet), #168/#172/#186, #27/#16, #474, #851, #872, #880, #1343, #1309, ProductsBusinessLogicTests#45 |
| Reply — intentional no-change | 5 | #84, #158(request-time), #450, #28/keyed-S2S, #79 |
| Reply — covered by follow-up task | 3 | platform/multi-market-group (AB#62893742/62893743/62881045) |

All four affected projects build clean; **37/37** workflow tests + **5/5** PlayTest publish tests pass. Pushed as `58184c4`.
