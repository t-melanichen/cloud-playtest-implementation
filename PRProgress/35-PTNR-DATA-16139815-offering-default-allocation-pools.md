# [PTNR-DATA] PR 16139815 — Set DefaultAllocationPools PC=PC_MAIN on offering XPT2SDT4X91KRR7

- **Pull Request:** 16139815
- **Repo:** services.data.partnerregistry (Xbox.Streaming)
- **Source branch:** `t-melanichen/xpt2sdt4x91krr7-default-allocation-pools` → `master`
- **Status:** Merged (Completed 2026-07-10; Timi signed off)
- **Merge commit:** e3a47af3c9aa1099beb92fa3a2bc88916ea2795b (source commit)
- **Link:** https://microsoft.visualstudio.com/Xbox.Streaming/_git/services.data.partnerregistry/pullrequest/16139815

## Summary
Manually sets `DefaultAllocationPools = { "PC": "PC_MAIN" }` on the prod PC playtest offering **XPT2SDT4X91KRR7**
(Melanie PlayTest 100). PC playtest offerings 400 on streaming session creation without this pool.

- `OfferingV2.json`: `"DefaultAllocationPools": {}` → `{ "PC": "PC_MAIN" }` (one field).

## Context
Companion to the durable PTNR code fix (PR 16112987) that auto-stamps `DefaultAllocationPools = PC_MAIN` on every new
PC playtest offering — but that fix **wasn't deployed yet**, so this offering (created before the deploy) needed the
pool patched by hand. Once 16112987 rolls out, new offerings get it automatically. See
[`../Blockers/pc-playtest-default-allocation-pools.md`](../Blockers/pc-playtest-default-allocation-pools.md).
