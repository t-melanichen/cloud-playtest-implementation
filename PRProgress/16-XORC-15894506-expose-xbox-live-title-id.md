# [XORC] PR 15894506 — Expose Xbox Live TitleId on the product Xbox Live config response

- **Pull Request:** 15894506
- **Repo:** xorc (Xbox.Services)
- **Source branch:** `t-melanichen/playtest-xbox-live-title-id` → `develop`
- **Status:** Merged
- **Opened:** 2026-06-15  |  **Closed:** 2026-06-16
- **Merge commit:** `886a1c2a52ff916b5a039c9b2dcb5c7ad9503dc8`
- **Link:** https://dev.azure.com/microsoft/Xbox.Services/_git/xorc/pullrequest/15894506

## Summary
Adds the numeric Xbox Live **Title ID** to the `GET /products/{id}/xboxliveconfig` response so callers can
read it directly from the Xbox Live configuration. This is the **XORc-side enabler** for the Instantly
Shareable (cloud-streaming) Playtest flow: xPlaytest resolves a product's Xbox Live Title ID and threads it
onto `StoreAsset.XboxTitleId` for xCloud content ingestion. Previously the title id was not one of the
fields this endpoint returned.

- `ProductXboxLiveConfigurationHandler`: maps the Xbox Live `TitleId` (served as `int?`, no unsigned cast)
  into the `xboxliveconfig` response.
- Contract + unit tests covering the `TitleId` mapping.

## Context
- Closes the "no source for the Xbox Live title id" gap documented in
  [`../Blockers/xbox-live-title-id.md`](../Blockers/xbox-live-title-id.md).
- Consumed on the board by task **62521457 "Resolve real XboxTitleIds from XORc"** under deliverable
  **[PT2] Construct StoreAsset from Playtest Product/Package Data** (62492534).
- Note: `xorc` targets `develop` (not `main`).
