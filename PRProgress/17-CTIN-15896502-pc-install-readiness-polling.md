# [CTIN] PR 15896502 — Implement PC install-readiness polling in PlaytestTitleIngestionWorkflow

- **Pull Request:** 15896502
- **Repo:** services.contentingestion (Xbox.Streaming)
- **Source branch:** `t-melanichen/playtest-pc-install-polling` → `main`
- **Status:** Draft
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
- **Timi (resolution business logic) — OPEN.** Timi: *"Resolution code needs some special business logic for playtests.
  Jack can probably walk you through it."* Not yet specified — needs a walkthrough with Jack before implementing. Likely
  related to how the resolver flags the just-ingested playtest version (ties into the version-pick item **62521491**).
- **Version-pick hardening** — the poll now requires exactly one *current* PC version (zero/multiple → retry) so a
  republish can't confirm readiness against a stale build; the full explicit-version pin stays tracked as **62521491**.
- **Tests:** 21 Core + 38 Worker passing (added `ConfigureOfferingAsync` routing tests, per-stage guard tests, and the
  Id config-binding test).

## Context
- Board deliverable **[XC3] Implement PlaytestTitleIngestionWorkflow** (62492680), task **62521491
  "Implement PC Polling"**.
- Polling design and follow-ups: [`../FuturePlans/pc-install-readiness-polling-implementation.md`](../FuturePlans/pc-install-readiness-polling-implementation.md)
  and [`../FuturePlans/polling-strategy-refinement.md`](../FuturePlans/polling-strategy-refinement.md).
- Uses PC Orchestrator (`IPCOrchestratorClient.QueryServersPagedAsync`) for the version-hash readiness
  check rather than the Xbox-only allocator path.
