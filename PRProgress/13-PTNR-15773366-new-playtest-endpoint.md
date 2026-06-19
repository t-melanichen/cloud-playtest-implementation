# [PTNR] PR 15773366 — New Playtest Endpoint

- **Pull Request:** 15773366
- **Repo:** services.partnerregistry (Xbox.Streaming)
- **Source branch:** `t-melanichen/configure-playtest-endpoint` → `main`
- **Status:** Merged
- **Opened:** 2026-06-03  |  **Closed:** 2026-06-05
- **Merge commit:** `9c597de3ecfd81e0ef265f70a3fdb362cea6d2b8`
- **Link:** https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.partnerregistry/pullrequest/15773366

## Summary
Adds a new `POST /v1/playtests` endpoint that creates (or updates) a playtest streaming offering and
attaches a title to it in a single Partner Registry call. The offering id is derived from the playtest's
XProduct BigId, so re-sending the same request updates the same offering rather than creating a new one
(idempotent upsert).

- `PlaytestProcessor.cs`: builds the offering from the playtest request, derives the offering id from the
  XProduct BigId, and attaches the title in one operation.

## Context
- Foundation for the xCloud offering-configuration path — board deliverables **[PT3] Build offering
  configuration from Playtest audience data** (62492560) and **[XC3] PlaytestTitleIngestionWorkflow** (62492680).
- Later refined by **PR 15815668** (offering regions + `xpt` id naming) and **PR 15821813** (centralized
  offering id on `PlaytestRequest.GetOfferingId`).
