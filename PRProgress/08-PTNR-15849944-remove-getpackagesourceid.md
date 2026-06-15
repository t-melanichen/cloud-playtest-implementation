# [PTNR] PR 15849944 — Remove GetPackageSourceId from Playtest contract

- **Pull Request:** 15849944
- **Repo:** services.partnerregistry (Xbox.Streaming)
- **Source branch:** `t-melanichen/remove-getpackagesourceid` → `main`
- **Status:** Merged
- **Opened:** 2026-06-11  |  **Closed:** 2026-06-11
- **Link:** https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.partnerregistry/pullrequest/15849944

## Summary
Cleanup/refactor that uses `PlaytestTitle.TitleId` directly as the Partner Registry title id.
- `PlaytestRequest.cs`: removes the `GetPackageSourceId` method that previously constructed a composite
  id from offering id + title id.
- `PlaytestProcessor.cs`: assigns the title id from `requestTitle.TitleId` directly instead of the
  removed helper.
