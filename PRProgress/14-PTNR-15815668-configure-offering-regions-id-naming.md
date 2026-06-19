# [PTNR] PR 15815668 — Configure playtest offering regions and id naming

- **Pull Request:** 15815668
- **Repo:** services.partnerregistry (Xbox.Streaming)
- **Source branch:** `t-melanichen/playtest-studio-regions-main` → `main`
- **Status:** Merged
- **Opened:** 2026-06-08  |  **Closed:** 2026-06-08
- **Merge commit:** `371b5f9ece06dfbf79de950c2b967b3d59d56f4c`
- **Link:** https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.partnerregistry/pullrequest/15815668

## Summary
Tunes the playtest offering created by the new playtest endpoint (PR 15773366) for the xCloud streaming flow:

- Sets the offering **Available Regions** to `WestUS2` and `WestEurope`.
- Drops the hyphen from the offering id prefix (now `xpt` instead of `xpt-`).

## Context
- Board deliverable **[PT3] Build offering configuration from Playtest audience data** (62492560).
- Region selection rationale is captured in [`../FuturePlans/region-configuration-routing.md`](../FuturePlans/region-configuration-routing.md).
- The id-prefix change is consolidated by the follow-up **PR 15821813** (`PlaytestRequest.GetOfferingId`).
