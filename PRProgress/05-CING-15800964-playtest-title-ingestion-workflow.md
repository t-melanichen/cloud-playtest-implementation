# [CING] PR 15800964 — Playtest Title Ingestion Workflow

- **Pull Request:** 15800964
- **Repo:** services.contentingestion (Xbox.Streaming)
- **Source branch:** `t-melanichen/playtest-title-ingestion-workflow` → `main`
- **Status:** Active (in review)
- **Opened:** 2026-06-05  |  **Closed:** —
- **Link:** https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.contentingestion/pullrequest/15800964

## Summary
Adds the end-to-end V3 `PlaytestTitleIngestionWorkflow` to the new "Workflows" stack so xPlaytest can
publish Instantly Shareable Playtests for cloud streaming. Flow: xPlaytest → SAGE →
`POST /v3/workflows/playtesttitleingestion`. Stages: **ValidateParameters** (StoreAsset + Offering/Title
info) → **TriggerAssetIngestion** (one child AssetIngestion V3 job, one audience per allowed DNA group)
→ **PollAssetIngestion** (bounded by the existing 8h `AssetIngestionJobPollingPolicy`) → **CreatePackage**
(one neutral streaming package + a single `1.0` version) → **ConfigureOffering** (Partner Registry
`ConfigurePlaytestAsync` creates offering `xpt{PlaytestProductId}` and attaches the title in one PR) →
**ConcludeWorkflow**. A playtest is always one StoreAsset → one package → one `1.0` version (no
store/BigCat lookup, DWOBs, asset filtering, or DLC/market fan-out).

## Open follow-up
- Implement PC polling — ADO work item 62521491
  (https://microsoft.visualstudio.com/Xbox/_workitems/edit/62521491).
