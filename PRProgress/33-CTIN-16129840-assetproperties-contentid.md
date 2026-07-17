# [CTIN] PR 16129840 — Add ContentId to AssetProperties; support explicit ServicingContentId for Playtests

- **Pull Request:** 16129840
- **Repo:** services.contentingestion (Xbox.Streaming)
- **Source branch:** `timi/servicing_content_Id` → `main`
- **Status:** Active (merge succeeded; in review)
- **Author:** Timi Bolaji
- **Link:** https://microsoft.visualstudio.com/Xbox.Streaming/_git/services.contentingestion/pullrequest/16129840

## Summary
The ingestion side of the 4-PR ContentId fix. Adds a real `ContentId` to the asset's stored metadata and separates
it from the asset **SourceId** (which, for playtests, is actually the `servicingContentId`).

- `AssetProperties.cs`: new `ContentId` member. Doc: _"only relevant for Playtest Ingestions, where the Asset SourceId is actually a ServicingContentId."_
- `AssetIngestionExtensions.cs:37`: `AssetProperties.ContentId = storeAsset.ContentId` (stores the real content id on the asset).
- `PlaytestTitleIngestionWorkflow.cs:88,145`: ingest/resolve the asset under `storeAsset.SourceId` (= `ServicingContentId ?? ContentId` = the servicing id) — preserves today's sourcing behavior.
- `InstallExtensions.cs:74`: `ContentId = asset.Properties.ContentId ?? asset.SourceId` — the install carries the real content id when present.

## Role in the fix
Sourcing (fetching the asset) stays keyed on the servicing id; the real `contentId` is now carried on the asset so
the distribution/install side (CTDR 16137972) can install the MSIXVC by the correct id.
