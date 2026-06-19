# [PTNR] PR 15821813 — Centralize playtest offering id on PlaytestRequest.GetOfferingId

- **Pull Request:** 15821813
- **Repo:** services.partnerregistry (Xbox.Streaming)
- **Source branch:** `t-melanichen/playtest-offering-id-on-request` → `main`
- **Status:** Merged
- **Opened:** 2026-06-08  |  **Closed:** 2026-06-09
- **Merge commit:** `09087e64f4e6aedf1687c316533d18a44eb090cf`
- **Link:** https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.partnerregistry/pullrequest/15821813

## Summary
Refactor to centralize playtest offering-id generation. Moves the id logic out of `PlaytestProcessor` and
onto the `PlaytestRequest` contract class so producers and consumers derive the same `xpt{XProductBigId}`
offering id consistently.

- `PlaytestRequest.cs`: adds a `GetOfferingId()` method and a private prefix constant; callers use it
  instead of re-deriving the id locally.

## Context
- Board deliverable **[PT3] Build offering configuration from Playtest audience data** (62492560).
- Precedes the fully-qualified title-id refactor (**PR 15860243**, "Refactor playtest title ID").
