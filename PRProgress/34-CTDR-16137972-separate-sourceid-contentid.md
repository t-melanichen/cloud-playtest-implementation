# [CTDR] PR 16137972 — Separate SourceId from ContentId (Sourcing vs Distribution commands)

- **Pull Request:** 16137972
- **Repo:** services.contentdistribution (Xbox.Streaming)
- **Source branch:** `rel/timi/playtest_contentid` → `main`
- **Status:** Active — hotfix test today (2026-07-10)
- **Author:** Timi Bolaji
- **Link:** https://microsoft.visualstudio.com/Xbox.Streaming/_git/services.contentdistribution/pullrequest/16137972

## Summary
The distribution/install side of the 4-PR ContentId fix — the piece that actually resolves the
`ERROR_NOT_FOUND` (-2147023728) at the PC server install (`CustomActionAppxPayload.cs:88`,
`InstallOrUpdateMsixvcContentByUrlV1`).

Separates the two identifiers so each side uses the right one:
- **Sourcing** (locating/fetching the asset in the catalog) → uses `SourceId` (= the servicing content id).
- **Distribution commands** (the actual MSIXVC install pushed to the PC server) → use the **real `ContentId`**.

Previously both used a single id (the servicing id), so the install command asked the server for content keyed on an
id the MSIXVC wasn't stored under → `ERROR_NOT_FOUND`.

## Test path (today)
Timi **manually patched the ingestion DB** record with the proper `contentId`, so this distribution fix can be
validated via **hotfix** today against the already-ingested playtest asset — without waiting for the full CTIN
(16129840) + Xbet (16130422) deploy. The manual patch is a one-off; once all four PRs ship, new playtests get the
correct `contentId` end-to-end automatically.
