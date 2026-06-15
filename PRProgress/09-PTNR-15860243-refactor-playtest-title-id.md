# [PTNR] PR 15860243 — Refactor playtest title ID

- **Pull Request:** 15860243
- **Repo:** services.partnerregistry (Xbox.Streaming)
- **Source branch:** `t-melanichen/refactor-title-id` → `main`
- **Status:** Merged
- **Opened:** 2026-06-11  |  **Closed:** 2026-06-12
- **Link:** https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.partnerregistry/pullrequest/15860243

## Summary
Refactors the playtest title id to use the fully-qualified format coming from Ingestion
(`xpt{PlaytestProductId}-{titleId}`). Partner Registry now uses `requestTitle.TitleId` verbatim to avoid
double-prefixing. Updates `PlaytestProcessor.cs` handling plus test data, assertions, and comments to
reflect that Ingestion sends the fully-qualified title id.
