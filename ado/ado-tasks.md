# ADO Task Breakdown — Instantly Shareable Playtest

> Companion to [`SPEC.md`](../SPEC.md) and [`ARCHITECTURE.md`](../ARCHITECTURE.md).
> Every task is sized **≤ 5 days**. Larger spec items (XC3 = 7d, PT6 = 5d but
> fan-out heavy) are split into independently assignable tasks.
> SWAGs are intentional "stupid wild *** guesses" — they exist to baseline
> capacity & timeline, not to be a commitment.

---

## Conventions

- **ID** — stable string used in references (`PT1.a`, `XC3.b`, …). The leading
  segment (`PT1`, `XC3`) maps to the deliverable in SPEC.md §4.
- **Type** — Epic / Feature / Task. ADO hierarchy: Epic → Feature → Task.
- **Owner** — the role / area that should pick this up. Names to be filled in
  once intern↔mentor pairings are set.
- **SWAG** — best-guess working days (one engineer, focused). Includes design,
  implementation, tests, code review wait. Does **not** include cross-team
  review SLAs that gate merge (those are tracked as dependencies).
- **Depends on** — must be merged before this task can start. Sibling tasks
  inside the same feature are otherwise parallelizable.
- **Acceptance** — concrete checkable criteria.

---

## Milestone-1 demo task (standalone)

| ID | Title | Owner | SWAG | Depends on | Acceptance |
|----|-------|-------|------|------------|------------|
| **M1.demo** | Foundational-demo harness: manual offering + Partner Center group flip | xCloud dev (with xPlaytest pair) | 2 | XC4.a, XC4.b, XC5.a | Operator script (PowerShell or a small console app) that (a) creates a new test offering via Partner Registry write path with one `AllowedDnaGroups` GUID; (b) attaches a known-good test title to it; (c) returns the launch URL. Manual test pass: a tester whose DNA-group membership is changed in Partner Center sees the offering become accessible / inaccessible within the GsToken refresh window. Validates the entire auth model end-to-end *before* any ingestion plumbing exists (SPEC.md §11 Milestone 1). |

---

## Epic

| ID | Title | SWAG (days) |
|----|-------|-------------|
| **EPIC** | Instantly Shareable Playtest — streaming opt-in for xPlaytest via xCloud | **54 dev-days across 2 teams** (xCloud core 27 + M1.demo 2 + xPlaytest 25 = 54) |

The Epic is delivered across 5 milestones (SPEC.md §11) and 4 phases
(SPEC.md §4.3). Phase A and B contain the foundational demo (Milestone 1)
and the first end-to-end ingestion (Milestone 2) respectively.

---

## Features (rolling up the deliverables)

| ID | Feature | Team | Rolls up | SWAG |
|----|---------|------|----------|------|
| **F-XCLOUD-PR** | xCloud — Partner Registry offering shape supports DNA-group gating | services.partnerregistry | XC4 | 5 |
| **F-XCLOUD-AUTH** | xCloud — User auth path enforces DNA-group membership | streaming-token / Bayside | XC5 | 5 |
| **F-XCLOUD-SAGE** | xCloud — SAGE exposes playtest ingestion routes to xPlaytest | services.serviceapigateway | XC1, XC2 | 4 |
| **F-XCLOUD-CI**   | xCloud — Content Ingestion runs the PlaytestTitleIngestionWorkflow | services.contentingestion | XC3 | 9 |
| **F-XCLOUD-INSTALL** | xCloud — Install pipeline tolerates DNA-group as flight id + PC fork | install / SUCU | XC6 | 4 |
| **F-XPT-CONTRACT**   | xPlaytest — Build the StoreAsset + ingestion payload | Xbox.Xbet.Service | PT2, PT3 | 5 |
| **F-XPT-WORKFLOW**   | xPlaytest — Workflow integration + status polling | Xbox.Xbet.Service | PT1, PT4, PT5 | 15 |
| **F-XPT-LIFECYCLE**  | xPlaytest — Lifecycle propagation (republish, audience, delete) | Xbox.Xbet.Service | PT6 | 5 |

---

## Tasks (≤ 5 days each)

### F-XCLOUD-PR — Partner Registry shape (XC4)

| ID | Title | Owner | SWAG | Depends on | Acceptance |
|----|-------|-------|------|------------|------------|
| **XC4.a** | Extend `PlayerAuthorizationOptions` schema | partner-registry dev | 2 | — | `AllowedDnaGroups: List<Guid>` and `AllowedSandboxId: string` added to `PlayerAuthorizationOptions`. JSON schema in `Schemas/` updated. Existing `OfferingV2` documents continue to deserialize (backfill on read: missing fields → empty list / `"RETAIL"`). Round-trip serialization test added. |
| **XC4.b** | Bulk-edit support for two-write playtest upsert + content-ingestion SPN allow-list | partner-registry dev | 2 | XC4.a | `RegistryProvider.BulkEditAsync` exposes a path that combines (create offering, attach title) into one PR to satisfy SFI manual-approval policy (SPEC.md §3.10). Unit test confirms a single commit / single PR is produced when both edits are queued together. Additionally, the `services.contentingestion` service identity is added to Partner Registry's write-route allow-list (per ARCHITECTURE.md §3.4 item 5). Verified by integration test from content-ingestion INT. |
| **XC4.c** | `OfferingV2.ToShortId()` helper (≤ 32 chars) | partner-registry dev | 1 | XC4.a | New static helper produces a deterministic ≤ 32-char id from an input GUID (e.g., 12-hex-char prefix). Collision probability documented. Used by the workflow's `xpt-{shortId}` derivation. Unit tests cover round-trip + collision behaviour. |
| **XC4.d** | Surface `AllowedDnaGroups` + `AllowedSandboxId` in the DevAPI Edit Offering admin UI | DevAPI UI dev (repo: `services.devapi`) | 2 | XC4.a, XC5.a | The internal admin UI at `americas.gssv-dev-prod.xboxlive.com/Partners/MICROSOFT` shows `AllowedDnaGroups` (multi-select of GUIDs) and `AllowedSandboxId` (defaults to `RETAIL`) on the **Edit Offering / offering-details page surfaced after the Add Offering "Save" action** — not on the initial Add Offering modal. Values round-trip correctly via the existing Partner Registry write path (XC4.a + XC4.b). Auth enforcement (XC5.a) MUST land first so the field's behavior matches what's enforced server-side. **Not on the M1 critical path** — M1.demo and the production ingestion flow (xPlaytest → SAGE → content-ingestion) both write these fields programmatically. This task only unblocks operator/ops inspection and hand-editing of playtest offerings in the admin UI; can ship after M2. |

Feature SWAG total: **7 days**. XC4.a is the critical sub-task for Milestone 1. XC4.d is off the critical path, depends on XC5.a (auth) shipping first, and can ship after M2.

---

### F-XCLOUD-AUTH — DNA-group enforcement (XC5)

| ID | Title | Owner | SWAG | Depends on | Acceptance |
|----|-------|-------|------|------------|------------|
| **XC5.a** | Streaming-token DNA-group intersection check | streaming-token dev | 3 | XC4.a (schema only) | At offering-entry the streaming-token / Bayside path checks `GsToken.DnaGroups ∩ offering.PlayerAuthorizationOptions.AllowedDnaGroups ≠ ∅`. If empty → 403 with no playtest metadata in the response. Integration test verifies allow + deny paths. |
| **XC5.b** | Per-title entitlement bypass for playtest offerings | streaming-token dev | 1 | XC5.a | When the offering's `Title.IsPlaytest` flag is set, skip the existing per-title entitlement check (since playtest titles have no Store entitlement). Behind a feature flag for safe rollout. Test covers both flag states. |
| **XC5.c** | Telemetry + denial reason codes | streaming-token dev | 1 | XC5.a | Denial emits `Reason=PlaytestNotInDnaGroup` for diagnosability without leaking offering metadata. Counter dashboard widget added. |

Feature SWAG total: **5 days**. Required for Milestone 1.

---

### F-XCLOUD-SAGE — SAGE routes (XC1 + XC2)

| ID | Title | Owner | SWAG | Depends on | Acceptance |
|----|-------|-------|------|------------|------------|
| **XC2.a** | Allow-list Playtest Service SPN cross-tenant | SAGE dev | 1 | Lakshmi PR #15715445 merged | `appsettings.xcloud.json` has `UseCrossTenantAuth: true` and the xPlaytest SPN added to `AuthorizedClientAppIds` for the three new routes. Deployment to INT verified. |
| **XC1.a** | Add `POST /playtest/ingestion` route | SAGE dev | 1 | XC2.a, XC3.a (downstream contract stable) | Config-only addition forwarding to `services.contentingestion`'s `POST /v3/workflows/playtestingestion`. Response bodies forwarded unchanged (do NOT strip into `x-Proxy-Error`). Smoke test from a test SPN succeeds. |
| **XC1.b** | Add `GET /playtest/ingestion/{jobId}` route | SAGE dev | 1 | XC2.a, XC3.c | Config-only. Same forwarding behaviour, forwarding to `GET /v3/workflows/playtestingestion/{jobId}`. Smoke test polls and reads JSON status. |
| **XC1.c** | Add `DELETE /playtest/ingestion/by-playtest/{playtestId}` route | SAGE dev | 1 | XC2.a, XC3.d | Config-only. Forwards to `DELETE /v3/workflows/playtestingestion/by-playtest/{playtestId}`. Smoke test deletes a test playtest and verifies tombstone response. |

Feature SWAG total: **4 days**.

---

### F-XCLOUD-CI — PlaytestTitleIngestionWorkflow (XC3 — split)

XC3 is the largest single piece. Split into four sub-tasks.

| ID | Title | Owner | SWAG | Depends on | Acceptance |
|----|-------|-------|------|------------|------------|
| **XC3.a** | Define `PlaytestIngestionJobParameters` contract + controller route | content-ingestion dev | 2 | XC4.a | New DTO in the public contracts assembly matching [`openapi/playtest-ingestion.yaml`](../openapi/playtest-ingestion.yaml). New route `WorkflowsControllerV3.PlaytestIngestion` accepts the payload, validates, schedules the workflow, returns `202` with `jobId`. 409 returns a `JobConflict`-shape body with the in-flight `jobId` and `statusUrl` when a non-terminal job already exists for the same `playtestId`. |
| **XC3.b** | Implement workflow state machine | content-ingestion dev | 5 | XC3.a, XC4.b, XC4.c, content-ingestion service identity allow-listed on Partner Registry write routes (per ARCHITECTURE.md §3.4 item 5) | New sealed `PlaytestTitleIngestionWorkflow` with stages: validate → schedule asset ingestion → poll asset ingestion → upsert offering (bulk-edit) → attach title → poll install readiness → emit terminal state. Reuses existing retry + idempotency patterns from `TitleIngestionWorker`. State transitions emit telemetry events. Unit tests cover happy path + each failure branch. Integration test confirms a published playtest with a *slow* asset ingestion (> 60 min) still reaches `Streamable`. |
| **XC3.c** | `GET /v3/workflows/playtestingestion/{jobId}` polling endpoint | content-ingestion dev | 1 | XC3.b | Returns current `JobStatus`. Terminal states populate `terminalState`, `offeringId`, `titleId`, `errors[]` per the OpenAPI schema. 404 for unknown `jobId`. Integration test verifies all four terminal states (`Streamable`, `Failed`, `InstallNotFound`, plus `Running` while in flight). |
| **XC3.d** | `DELETE /v3/workflows/playtestingestion/by-playtest/{playtestId}` tombstone endpoint | content-ingestion dev | 1 | XC3.b, XC4.b | New route sets `offering.PlayerAuthorizationOptions.AllowedDnaGroups = []` via the bulk-edit path, schedules a GC pass for 7 days out. Idempotent. Returns 200 with `{ playtestId, offeringId, tombstoneTime }`. 404 if no offering for `playtestId`. Integration test confirms subsequent stream attempts denied by XC5. |

Feature SWAG total: **9 days**.

---

### F-XCLOUD-INSTALL — DNA-group as flight id (XC6)

| ID | Title | Owner | SWAG | Depends on | Acceptance |
|----|-------|-------|------|------------|------------|
| **XC6.a** | Audit install pipeline tolerance for non-GA flight id + PC fork | install dev | 2 | XC3.b (something to test against) | Documented walk of `TitleIngestionWorker.cs:197-225` and SUCU client confirms (a) the path tolerates a non-GA flight id, and (b) the PC code path for `ServerType` + pool id (today the code hardcodes `ServerType.XboxV3SeriesS` and `XBOX_*` pools — see SPEC.md §3.6 risk callout). Audit posted as ADO comment. If a PC server type / pool id exists in the allocator client today, document its values; if not, file a follow-up task for the PC pipeline owner. |
| **XC6.b** | Wire deterministic "smallest GUID" selection + platform-aware filter | install dev | 2 | XC6.a | When resolving package version for a playtest title, pick the lexicographically smallest GUID **of the current `AllowedDnaGroups` set at resolve time** as the flight identifier (per SPEC.md §3.3). **Branch the `ServerFilter` build on `Platform`** so PC playtests pick the PC pool id + PC `ServerType` (audit findings from XC6.a). Behind feature flag. Unit + integration tests confirm: (a) same `AllowedDnaGroups` set always resolves to the same flight id, and therefore the same package version (deterministic); (b) **adding a GUID that sorts *higher* than the current smallest** does not change the selected flight id or resolved package; (c) **adding a GUID that sorts *lower* than the current smallest** *does* flip the selection — this is acceptable v1 behavior because flights are addressable by GUID alone and there is no notion of "first-chosen flight," but the flip emits a `XCloudFlightSelectionFlipped` telemetry event with both old and new GUIDs so the install team can detect churn; (d) removing the previously-smallest GUID flips selection to the next-smallest and likewise emits telemetry; (e) a PC playtest does not hit Xbox-only allocator parameters (no `ServerType.XboxV3SeriesS` or `XBOX_*` pool ids on the resolved request). *Design note: a sticky "first-chosen flight" model was considered but rejected for v1 because it requires extra per-playtest state in the install pipeline that doesn't exist today — see SPEC.md §3.3.* |

Feature SWAG total: **4 days**.

---

### F-XPT-CONTRACT — StoreAsset & offering payload (PT2 + PT3)

| ID | Title | Owner | SWAG | Depends on | Acceptance |
|----|-------|-------|------|------------|------------|
| **PT2.a** | `XboxTitleId` resolver from XProduct | xPlaytest dev | 3 | — | New service that reads `alternateIds[XboxTitleId]` from the XProduct response and surfaces it on `PlaytestProductDocumentBuilder`. Replaces the current `XboxLiveTitleId = string.Empty` hardcode at `PlaytestProductDocumentBuilder.cs:53-70`. Validator now passes a non-zero `XboxTitleId` for a PC game. **P0 blocker — must land before XC3.b can be integration-tested end-to-end.** |
| **PT2.b** | `AumID` default-or-resolver | xPlaytest dev | 1 | — | For v1, a constant default `"{packageFamilyName}!App"` is acceptable (server-side use is telemetry-only per Timi). Document this in code comments and link to SPEC.md §3.6 / §5.2. v1.1 task tracked separately to plumb the real ApplicationId from the AppX manifest. |
| **PT3.a** | Package allowed-audience DNA groups into payload | xPlaytest dev | 1 | — | `PlaytestPublishJobParameters.FlightIds` (already GMS-resolved DNA group GUIDs) flow into `PlaytestIngestionJobParameters.AllowedDnaGroups`. Unit test asserts pass-through. |

Feature SWAG total: **5 days**. PT2.a + PT3.a are independent and can run in parallel with PT2.b.

---

### F-XPT-WORKFLOW — Workflow integration + send + poll (PT1 + PT4 + PT5)

| ID | Title | Owner | SWAG | Depends on | Acceptance |
|----|-------|-------|------|------------|------------|
| **PT1.a** | Insert `XCloudIngestionTriggerState` into `XPackagePlaytestPublishWorkflow` | xPlaytest dev | 3 | PT2.a, PT2.b, PT3.a | New state inserted between `PlaytestProductCreation` and `SuccessCompletion`. Gated on `IsStreamingEnabled` flag (false by default). Failure of the new state does NOT block publish — it logs + emits telemetry. Workflow unit tests cover both flag states + xCloud-down failure. |
| **PT1.b** | Add `IsStreamingEnabled` opt-in field + streaming-expiration validation to publish request | xPlaytest dev | 1 | — | New boolean `IsStreamingEnabled` on the publish API surface, defaulting to `false`. When `true`, validate that `PlaytestEndDate` is non-null and in the future, returning `400` with a clear message otherwise (SPEC.md §9 Q3 + §7 blocker row). Documented in the public Playtest API contract. Unit tests cover both flag states and the new validation. |
| **PT1.c** | Seller / title allow-list gate for streaming publish | xPlaytest dev | 2 | PT1.b | New publish-side validator: when `IsStreamingEnabled = true`, reject publish unless the publisher's `SellerId` (and optionally `ProductId`) is on a configurable allow-list. Allow-list is read from xPlaytest config (initially an in-config hardcoded list; future task tracks moving to a dynamic config service). Returns `403 StreamingNotEnabledForSeller` with a clear error code. SPEC.md §10 P0 — "Creation of a private offering can be limited to a specific title / allow list of sellers." Unit tests cover allowed-seller, denied-seller, allowed-seller + denied-title, and missing-config (fail-closed) cases. |
| **PT4.a** | `XCloudIngestionClient` (HTTP client) | xPlaytest dev | 2 | XC1.a, XC2.a | New typed HTTP client wrapping SAGE's `POST /playtest/ingestion`. Cross-tenant S2S token acquisition. Returns `(jobId, statusUrl)`. Polly-style retry on 5xx. Integration test against INT SAGE. |
| **PT4.b** | Persist `jobId` on `PublishedPlaytestEntity` | xPlaytest dev | 1 | PT4.a | Schema migration adds `XCloudIngestionJobId`, `XCloudOfferingId`, `XCloudTitleId`, `XCloudStatus`. Backfill = nullable. Persisted at end of `PT1.a`'s state. |
| **PT5.a** | Polling loop with exponential backoff | xPlaytest dev | 2 | XC1.b, XC3.c, PT4.b | Backoff per SPEC.md §3.1: 30s → 60s → 2min → 5min cap, 60min wall-clock. On terminal `Streamable` → set `PlaytestStatus = StreamingReady` + persist `OfferingId` / `TitleId`. On `Failed` / `InstallNotFound` → set `StreamingFailed` and persist error. Integration test asserts state transitions. |
| **PT5.b** | New `StreamingReady` value in `PlaytestStatus` enum + launch URL builder | xPlaytest dev | 1 | PT5.a | Enum value added (with migration safe-defaults). New `BuildStreamingLaunchUrl(playtest)` method on `PlaytestBusinessLogic`. Unit tests cover both. |
| **PT5.c** | Surface launch URL on Playtest GET API | xPlaytest dev | 1 | PT5.b | `PlaytestResponse.StreamingLaunchUrl` populated when status is `StreamingReady`. API contract bump (additive, non-breaking, still on v3). |
| **PT5.d** | Background reconciliation job for stuck ingestions | xPlaytest dev | 2 | PT5.a, PT4.b | New singleton timer service polls `XCloudIngestionJobId` from `PublishedPlaytestEntity` for any playtest stuck in `WaitingForXCloud` past the 60-min foreground deadline. Polls at 15-min intervals indefinitely up to 24 h, then alerts an on-call alias for manual triage (SPEC.md §3.1). On terminal state, transitions to `StreamingReady` / `StreamingFailed` exactly as PT5.a does. Integration test simulates a slow ingestion crossing the deadline and confirms eventual `StreamingReady`. |

Feature SWAG total: **15 days**. PT1.c gates PT4.a (no point making the SAGE call if the publish is denied). PT4.* and PT5.* can pipeline against PT1.a once PT1.a is unblocked.

---

### F-XPT-LIFECYCLE — Lifecycle propagation (PT6 — split)

| ID | Title | Owner | SWAG | Depends on | Acceptance |
|----|-------|-------|------|------------|------------|
| **PT6.a** | Re-trigger ingestion on audience change | xPlaytest dev | 1 | PT1.a, PT4.a | Hook into `PlaytestBusinessLogic.UpdatePlaytestAsync` (`PlaytestBusinessLogic.cs:408-553`). On audience delta, re-call `XCloudIngestionClient` with the updated `AllowedDnaGroups`. xCloud's idempotent upsert (keyed on `playtestId`) handles the update. Integration test: add tester, confirm new offering write within 60s. |
| **PT6.b** | Re-trigger on expiration change | xPlaytest dev | 1 | PT6.a | Same hook, expiry delta path. Integration test. |
| **PT6.c** | Re-trigger on build republish | xPlaytest dev | 2 | PT6.a, PT2.a | When a new package is uploaded, re-send `StoreAsset` with the new `ContentId`. xCloud upsert produces a new asset version under the same offering. Integration test: republish, confirm streaming session picks up the new build. |
| **PT6.d** | Teardown on playtest delete | xPlaytest dev | 1 | PT6.a, XC3.d, XC1.c | Wire into the existing delete workflow. Call `DELETE /playtest/ingestion/by-playtest/{playtestId}` on SAGE. Integration test: delete playtest, confirm tombstone response 200, confirm any subsequent stream attempt is denied by XC5. |

Feature SWAG total: **5 days**.

---

## Roll-up

| Phase | Milestone | Tasks in scope | SWAG (days) |
|-------|-----------|----------------|-------------|
| A | M1 — Foundational demo | XC4.a, XC4.b, XC4.c, XC5.a, XC5.b, XC5.c, XC2.a, PT3.a, **M1.demo** | 14 (parallel across teams) |
| B | M2 — End-to-end ingestion | XC3.a, XC3.b, XC3.c, XC3.d, XC1.a, XC1.b, XC1.c, XC6.a, XC6.b, PT2.a, PT2.b | 20 |
| C | M3 — xPlaytest integration | PT1.a, PT1.b, PT1.c, PT4.a, PT4.b, PT5.a, PT5.b, PT5.c, PT5.d | 15 |
| D | M4 — Lifecycle | PT6.a, PT6.b, PT6.c, PT6.d | 5 |
| — | M5 — Soak + handoff | (no new tasks; bug-fix + documentation) | 0 |
| Off-critical-path | Operator UI (post-M2) | XC4.d | 2 |

Grand total dev-days: **~54 days of focused work** (xCloud core 27 + M1.demo 2 + xPlaytest 25 = 54),
parallelizable across the 2 teams into roughly **7–8 calendar weeks** with
1 engineer per team (matching the ~10-week internship including ramp + buffer).

> SWAG accounting note (reconciles SPEC.md §4.2): SPEC.md lists *xCloud feature subtotal = 27* and *xPlaytest feature subtotal = 25 (after PT1.c)*. This roll-up adds **M1.demo (2 days)** to the xCloud column because the foundational demo is run primarily by the xCloud engineer. Cross-team totals therefore reconcile as `xCloud (27 core + 2 demo) + xPlaytest 25 = 54`.

---

## Cross-task notes for the ADO board

- Use **tags**: `playtest-streaming`, plus one of `team:xpt` or `team:xcloud`,
  plus the deliverable id (`PT1`, `XC3`, …).
- Use **iteration paths** aligned to milestones M1–M5.
- Acceptance criteria on each task should be copy-pasted into the ADO
  description so a reviewer can stamp by checking against them.
- Open Questions Q1, Q4, Q5 from SPEC.md §9 should be filed as **discussion**
  work items, not tasks (decisions, not deliverables), and stamped before
  M2 starts.

