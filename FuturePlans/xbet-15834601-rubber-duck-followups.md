# Future plan: PR 15834601 follow-ups (rubber-duck findings)

**Why it matters:** PR 15834601 (Playtest streaming ingestion payload builder + workflow states) **merged** with the streaming path gated to the pilot seller `65050620`, so these findings only execute on the pilot seller's streaming publishes — none can break another seller's (non-streaming) publish. They're "make the pilot/E2E path robust and extensible," not "production incident." Captured from a pre-merge rubber-duck review so they aren't lost.

## Scope reminder (why this is safe to have merged)
- Streaming is opt-in via `EnableStreaming`, set only when `IsStreamingEnabled(sellerId)` matches pilot seller `65050620` (`PlaytestBusinessLogic.QueuePublishJobAsync`). Every finding below is on a streaming-only code path.
- The one change that touches **all** sellers is `PlaytestEndDateMustBeInFutureRule` — fail-closed, only rejects publishing an already-expired playtest; `DateTime.MaxValue` (open-ended) trivially passes. Net-positive guard, not a follow-up.

## Follow-ups (priority order)

### 1. Streaming preflight can fail the standard publish (design decision)
- **Where:** `PlayTest/BusinessLogic/PlaytestBusinessLogic.cs` — `ResolveXboxLiveTitleIdAsync` (~L1086-1096) is called at enqueue (~L1006-1010) **before** `CreateJobAsync`.
- **Issue:** It throws on XORc failure or missing/zero `TitleId`, so the whole publish is never queued. For a *misconfigured* title this is intentional (fail fast with a clear validation error). For a *transient* XORc 5xx it means a flaky dependency fails the pilot seller's publish.
- **Decision needed:** keep fail-fast for "not Xbox-Live-configured", but treat **transient** XORc errors as non-blocking (log + metric, queue with `EnableStreaming=false`), OR keep fully blocking. Only affects pilot seller today, but will matter more as streaming opens up.
- **Tests to update:** the ones asserting publish failure on XORc error.

### 2. Polling timeout measured from the wrong start (real, low severity)
- **Where:** `XPackageWorkflow/Workflows/Playtest/XPackagePlaytestPublishWorkflow.cs` — `ContinueOrTimeoutStreamingIngestionPoll` (~L623): `DateTime.UtcNow - context.CreatedOn > MaxStreamingIngestionWait`.
- **Issue:** `context.CreatedOn` is **overall publish job** creation, not when streaming was scheduled. If content submission + product creation took hours, the 24h streaming poll window is already partly/fully consumed — streaming can be abandoned early.
- **Fix:** persist `StreamingIngestionScheduledOn` in `PlaytestPublishJobState` when the job id is stored; measure the timeout from that timestamp.

### 3. Scheduling idempotency is not crash-safe (inherent to receiver)
- **Where:** `XPackagePlaytestPublishWorkflow.cs` schedule guard (~L914-948).
- **Issue:** The persisted-`XCloudPlaytestTitleIngestionJobId` guard prevents re-scheduling **only after** the id is persisted. If the worker crashes after the SAGE POST succeeds but before persisting state, a retry creates a **second** receiver workflow. Content-ingestion is **not** caller-id idempotent (`WorkflowsProcessor.ScheduleJobAsync` uses server-side `Id.NewGuid()`; `PlaytestId` is only a `GetLockId()` lock).
- **Fix (needs receiver support):** caller-supplied operation id / receiver idempotency, or a durable outbox/reservation + reconciliation. Document the remaining unknown-outcome window until then. (See `s2s-cross-tenant-call.md` "Receiver scheduling semantics".)

### 4. Lifecycle/package selection under-specified for multiple packages
- **Where:** `StreamingPlaytestTitleIngestionBuilder.cs` (~L74-77) — picks the "default" market group then the first state entry.
- **Issue:** With multiple packages in a group, selection depends on dictionary insertion order → could ingest the wrong package family / content id as platform/package support grows.
- **Fix:** for v1 explicitly validate exactly one streaming package (assert), or carry the selected package/platform/application id through the job parameters/state. Ties into multi-market-group work item **62893742** and localization work item **62926053**.

### 5. Builder `Validate` misses receiver-critical fields (cheap hardening — do before E2E)
- **Where:** `StreamingPlaytestTitleIngestionBuilder.cs` `Validate` (~L95, L120-122, L166-169); nullable source `PlaytestBusinessLogic.cs` `BuildMarketGroupPackages` (~L1223-1225 — `ServicingContentId` can be null).
- **Issue:** `Validate` checks only top-level ids, not `StoreEntry.Name`, `StoreAsset.ContentId`, `PackageFamilyName`, `Platform`, or a positive `XboxTitleId`. A bad payload reaches SAGE and fails opaquely (harder E2E debugging).
- **Fix:** extend `Validate` (require non-empty name, servicing content id, package family name; positive title id) + add tests. **This one pays for itself the moment E2E starts** — clear local failure instead of an opaque SAGE 400.

## Confirmed solid (no action)
- `StreamingParameters == null` invariant is **outside** the catch and fails loudly (`XPackagePlaytestPublishWorkflow.cs:514-518`).
- Scheduling/polling exceptions **after** product creation transition to success — streaming never fails the download publish.
- `PlaytestName`/`PlaytestDescription` come from the enqueue snapshot (no mid-workflow reload); tagged for localization (WI **62926053**).
- Targeted tests green pre-merge: XPackage workflow/builder 83, PlayTest business/rule 153 (full suites 87 / 169).

## Source
Pre-merge rubber-duck review of PR 15834601 (branch `t-melanichen/playtest-ingestion-payload-builder`), 2026-06-30.
