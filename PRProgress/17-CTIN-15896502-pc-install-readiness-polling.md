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

## Context
- Board deliverable **[XC3] Implement PlaytestTitleIngestionWorkflow** (62492680), task **62521491
  "Implement PC Polling"**.
- Polling design and follow-ups: [`../FuturePlans/pc-install-readiness-polling-implementation.md`](../FuturePlans/pc-install-readiness-polling-implementation.md)
  and [`../FuturePlans/polling-strategy-refinement.md`](../FuturePlans/polling-strategy-refinement.md).
- Uses PC Orchestrator (`IPCOrchestratorClient.QueryServersPagedAsync`) for the version-hash readiness
  check rather than the Xbox-only allocator path.
