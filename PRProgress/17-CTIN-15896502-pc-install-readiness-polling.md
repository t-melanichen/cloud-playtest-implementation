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
- **Version-pick hardening** — the poll now requires exactly one *current* PC version (zero/multiple → retry) so a
  republish can't confirm readiness against a stale build; the full explicit-version pin stays tracked as **62521491**.
- **Tests:** 20 Core + 38 Worker passing (added `ConfigureOfferingAsync` routing tests and per-stage guard tests).

## Context
- Board deliverable **[XC3] Implement PlaytestTitleIngestionWorkflow** (62492680), task **62521491
  "Implement PC Polling"**.
- Polling design and follow-ups: [`../FuturePlans/pc-install-readiness-polling-implementation.md`](../FuturePlans/pc-install-readiness-polling-implementation.md)
  and [`../FuturePlans/polling-strategy-refinement.md`](../FuturePlans/polling-strategy-refinement.md).
- Uses PC Orchestrator (`IPCOrchestratorClient.QueryServersPagedAsync`) for the version-hash readiness
  check rather than the Xbox-only allocator path.
