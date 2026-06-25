# [CTIN] PR 15896502 — Implement PC install-readiness polling in PlaytestTitleIngestionWorkflow

- **Pull Request:** 15896502
- **Repo:** services.contentingestion (Xbox.Streaming)
- **Source branch:** `t-melanichen/playtest-pc-install-polling` → `main`
- **Status:** Active
- **Opened:** 2026-06-15  |  **Closed:** —
- **Link:** https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.contentingestion/pullrequest/15896502

## Summary
Implements PC install-readiness polling inside `PlaytestTitleIngestionWorkflow`. Replaces the PC
first-install *skip* with real readiness polling: PC servers do not pre-pull content the way Xbox does, so
the workflow resolves the exact ingested version and polls **PC Orchestrator** until the title is available
before reporting the job complete.

Also adds `IngestionWorkflowSettings.PlaytestPcReadinessQuery` (SystemUpdateGroup / Regions / Skus) so the poll's
`GameStreamingServerFilter` is pinned to the PC playtest lane, and sets the Test (non-prod) values to
`PC_PLAYTEST` / `WESTUS2` / `STANDARD_NC64AS_T4_V3` to match the content-targets enablement and the offering.
Full per-PR design + test plan: [`../FuturePlans/content-targets-pc-playtest-enablement.md`](../FuturePlans/content-targets-pc-playtest-enablement.md).

## Review updates (PR feedback)
- **Jack Heuberger** — split the PC readiness poll into its own stage: `ConfigureOfferingAsync` now transitions to
  `PollFirstInstallAsync` (Xbox) or `PollPcFirstInstallAsync` (PC) by content type, and `PollPcFirstInstallAsync` is its
  own `[WorkflowStage]` (with the same empty-package guard), so an inspected workflow shows a stage name that reflects
  the install path being verified. Commit `47c4800a`.
- **Jack Heuberger** — `PlaytestPcReadinessQuery` settings (SystemUpdateGroup / Skus) are now strongly-typed
  `Id` values instead of strings, removing the `(Id)` casts in the workflow; a config-binding test confirms they still
  bind from appsettings string values. Commit `0ad828ac`.
- **Timi (region filter)** — the PC Orchestrator query no longer filters by region; readiness uses a **"first region"
  assumption** (any region reporting the exact version is sufficient). Removed the now-unused `PlaytestPcReadinessQuery.Regions`
  config + its appsettings entries + the env-provider region fallback. Region targeting deferred until we steer developers
  to specific regions. Commit `0fab4be6`.
- **Timi (version selection)** — version selection no longer filters inline on `IsCurrent`; it now goes through a new
  shared **non-throwing** `TryGetCurrentVersion(serverType)` extension (sibling to `GetCurrentVersion` / `TryGetNextVersion`
  in `ContentInstallVersionCollectionExtensions`), so the poll resolves the current version the same way as the rest of the
  pipeline and a missing current version returns `false` instead of throwing. Commit `9975648d`.
- **Timi (resolution read delay)** — added a configurable `PlaytestPcReadinessQuery.ResolutionReadDelay` applied **before**
  the resolution query to absorb the Catalog DB's session-consistency (read-your-writes) lag, so a freshly-ingested version
  is visible before the poll resolves it. Set to **5s** in the Int + Test appsettings; **default none** (no delay) otherwise.
  Commit `9975648d`. This resolves the previously-open *"resolution code needs special business logic for playtests"* thread:
  the read delay handles the timing (a freshly-ingested playtest version being resolvable immediately) and
  `TryGetCurrentVersion` centralizes the version pick. Background: the poll picks the build via `IsCurrent`
  (`ContentInstallVersionMetadata.IsCurrent => AvailableFrom == null`), so it depends on the just-ingested version being visible.
- **Version-pick hardening** — the poll requires exactly one *current* PC version (zero/multiple → retry) so a republish
  can't confirm readiness against a stale build. The full explicit-version pin (resolve by install id, sidestepping the
  `IsCurrent` inference) stays tracked as a follow-up under **62521491**.
- **All earlier review threads resolved (status=fixed).** Both of Timi's live comments above are addressed in commit `9975648d`.
  **Tests:** 16/16 Core unit tests pass.
- **Jack Heuberger (2026-06-24 walkthrough — OPEN, comment pending; latest branch commit `688a2f6b` 2026-06-23 predates this):**
  1. **SUG (and PC-playtest filter values) should never be null → make them constants. ✅ DONE (commit `2bffc05c`).**
     Reviewing `PollPcFirstInstallAsync`, Jack flagged that `GameStreamingServerFilter.SystemUpdateGroups` could resolve
     to `null` (`pcQuery?.SystemUpdateGroup is { } x ? [x] : null`). The "distinct PC playtest SUG" is fixed for this lane —
     *"there's no reason we should ever pass in a null … these should be constant."* Fix: removed the nullable
     `PlaytestPcReadinessQuery.SystemUpdateGroup` config and now always scope the readiness query to a code constant
     `PcPlaytestSystemUpdateGroup = (Id)"PC_PLAYTEST"`. (The env-specific SKU — NC64 vs NC8 — stays config-driven, since
     Jack pointed only at the subgroups; confirm against his written comment.) Updated appsettings (Int/Test) + unit tests; 24/24 pass.
  2. **Keep the non-GA resolution scoping OUT of this PR (✅ already done).** Jack confirmed the *"don't scope playtest
     resolution package search"* change is out of scope for the polling PR and must be its own PR — it already is:
     branch `t-melanichen/resolution-playtest-no-ga-flight` (commit `bef7fe2b`). Timi owns the full picture there.
  - **Status: SUG-constant fix committed (`2bffc05c`, local — push + re-request review).** Jack's formal comment may still land; confirm the SKU treatment with it.

## Context
- Board deliverable **[XC3] Implement PlaytestTitleIngestionWorkflow** (62492680), task **62521491
  "Implement PC Polling"**.
- Polling design and follow-ups: [`../FuturePlans/pc-install-readiness-polling-implementation.md`](../FuturePlans/pc-install-readiness-polling-implementation.md)
  and [`../FuturePlans/polling-strategy-refinement.md`](../FuturePlans/polling-strategy-refinement.md).
- Uses PC Orchestrator (`IPCOrchestratorClient.QueryServersPagedAsync`) for the version-hash readiness
  check rather than the Xbox-only allocator path.
