# [PTNR] PR 16112987 — Set DefaultAllocationPools on PC playtest offering

- **Pull Request:** 16112987
- **Repo:** services.partnerregistry (Xbox.Streaming)
- **Source branch:** `t-melanichen/playtest-default-allocation-pool` → `main` (squash; source branch deleted)
- **Status:** Merged (completed 2026-07-08, iteration 4)
- **Merge commit:** `7ecede80`
- **Approvals:** Timi Bolaji · Xbox Cloud Streaming Services Dev (required) · Xbox.Streaming Services Team
- **Link:** https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.partnerregistry/pullrequest/16112987

## Summary
The **durable code fix** for the original streaming 400 (*"Offering does not specify any default allocation pools for the
selected content platform: PC"*). Makes `PlaytestProcessor.ConfigurePlaytestAsync` set the PC allocation pool on every PC
playtest offering, so future playtests auto-configure it (no hand-patching). Four files:

- **`PlaytestProcessor.cs:105`** — PC branch now sets
  `offering.DefaultAllocationPools = new Dictionary<Id, Id> { { ServerPlatform.PC, settings.PCAllocationPool } };`
- **`PlaytestSettings.cs:17`** — adds `public Id PCAllocationPool { get; init; } = "PC_MAIN";` (config-driven, alongside
  `PCServerSku` / `PCSystemUpdateGroup`).
- **`appsettings.json:96`** — `"PCAllocationPool": "PC_MAIN"` in the PlaytestSettings block.
- **`PlaytestProcessorTests.cs`** — asserts `DefaultAllocationPools = {PC: PC_MAIN}` for PC titles, empty for non-PC,
  plus a `CUSTOM_PC_POOL` config-override case.

## Context
- Completes **Path B** of [`../Blockers/pc-playtest-default-allocation-pools.md`](../Blockers/pc-playtest-default-allocation-pools.md).
  The pilot offering `XPT2SDT4X91KRQS` only had the pool because it was **hand-patched** (PR 16097829); this makes it
  automatic for all future playtests.
- Pairs with [PR 15949594](https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.partnerregistry/pullrequest/15949594)
  (SUG + weights + WestUs2 region) — together the PC branch of `PlaytestProcessor` now writes **all four** streaming
  fields (`DefaultAllocationPools`, `SelectableSystemUpdateGroups`, `SystemUpdateGroupWeights`, region) + Title
  `TargetServerSkus`.
- **Remaining = prod deploy only.** Merged ≠ deployed; `main` must roll out to prod `services.partnerregistry` past the
  Ring gates before auto-created prod offerings pick it up. Env-level predictions/quota already cover all playtests
  (see [`../Explanations/pc-playtest-streaming-allocation-e2e.md`](../Explanations/pc-playtest-streaming-allocation-e2e.md)).
