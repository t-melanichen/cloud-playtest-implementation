# [XBET] PR 16130422 — Send playtest ContentId to streaming ingestion

- **Pull Request:** 16130422
- **Repo:** Xbox.Xbet.Service (Xbox)
- **Source branch:** `t-melanichen/playtest-real-contentid` → `main`
- **Status:** Merged (Completed)
- **Opened:** 2026-07-09  |  **Closed:** 2026-07-09
- **Merge commit:** d81af6a3167c075d762cd1a05b4faa4ca97bfd0a
- **Link:** https://microsoft.visualstudio.com/Xbox/_git/Xbox.Xbet.Service/pullrequest/16130422

## Summary
Fixes the PC playtest streaming **install failure** (`ERROR_NOT_FOUND` / `-2147023728`). The streaming `StoreAsset`
was sending the SUCU **`servicingContentId`** as `ContentId`, but the PC MSIXVC is keyed on the **real `contentId`**,
so the server install looked it up by the wrong id and failed. See
[`../Blockers/pc-playtest-msixvc-install-error-not-found.md`](../Blockers/pc-playtest-msixvc-install-error-not-found.md).

- `StreamingPlaytestTitleIngestionBuilder.cs`: `StoreAsset.ContentId ← lifecycleState.PlaytestContentId` (the real
  content id the MSIXVC is keyed on) and new `StoreAsset.ServicingContentId ← lifecycleState.ServicingContentId` (SUCU).
- `XPackageWorkflow.csproj`: bump `Microsoft.GameStreaming.Services.Common.Content.Ids` → **3.1.2607.901** (the
  released package that adds `ServicingContentId` + computed `SourceId => ServicingContentId ?? ContentId`).
- `StreamingPlaytestTitleIngestionBuilderTests.cs`: assert `ContentId == PlaytestContentId` and
  `ServicingContentId == ServicingContentId`.

## Part of the 3-PR ContentId fix
1. **STORECLIENT 16128230** (services.common.content, merged) — adds `ServicingContentId` to `StoreAsset`; `SourceId => ServicingContentId ?? ContentId`.
2. **CTIN 16129840** (services.contentingestion) — adds `AssetProperties.ContentId`; ingest/resolve under `StoreAsset.SourceId`; install uses `Properties.ContentId ?? SourceId`.
3. **XBET 16130422** (this PR) — send `PlaytestContentId` as `ContentId` + `ServicingContentId`.

## ⚠️ Deploy ordering
CTIN 16129840 must reach prod **before (or with)** this Xbet change. Pre-16129840 CTIN uses `storeAsset.ContentId`
directly as the asset SourceId; if Xbet ships first the asset SourceId flips servicing→real and breaks the
currently-working asset resolution. Order: **StoreClient → CTIN → Xbet.** (Deployments paused until Monday.)

## Verification
Mapping verified against Timi's actual PR branches (not `main`): `StoreAsset.SourceId` IL-confirmed as
`ServicingContentId ?? ContentId`; CTIN `AssetIngestionExtensions.cs:37` sets `AssetProperties.ContentId = storeAsset.ContentId`;
`InstallExtensions.cs:74` install uses `Properties.ContentId ?? SourceId`. Build clean, 11/11 builder unit tests pass.
