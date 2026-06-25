# [CTGT] PR 15946980 — Tests-only: PC playtest enable + quota moved to dynamic config

- **Pull Request:** 15946980
- **Repo:** services.contenttargets (Xbox.Streaming)
- **Source branch:** `t-melanichen/pc-playtest-install-on-attach` → `main`
- **Status:** Abandoned (2026-06-22) — superseded by the dynamic-config quota (PR [22](./22-DCFG-15966616-contenttargets-pc-playtest-quota.md), Int); the 3 regression tests were its only remaining value
- **Opened:** 2026-06-19  |  **Closed:** 2026-06-22
- **Link:** https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.contenttargets/pullrequest/15946980

## Summary
Per Timi's review feedback, the PC playtest **enable + quota** settings must be applied through Content Targets dynamic
config, not checked into `appsettings`. The PR's `appsettings.ContentTargets.Int.json` and
`appsettings.ContentTargets.Test.json` additions were reverted in commit `04ac32c`; the remaining branch diff is tests only.

**Decision — abandoned (2026-06-22).** The PR was abandoned on ADO once the dynamic-config quota landed via PR [22](./22-DCFG-15966616-contenttargets-pc-playtest-quota.md) (Int), superseding its reverted appsettings. It had been retitled *"[CTGT] Add tests for PC_PLAYTEST SUG resolution/enablement"*
because the 3 remaining tests are valuable regression coverage for the behavior the dynamic config produces:
`IncludePredictions_WithPlaytestSugOverride_EnablesOnlyPlaytestPcServerSet` (override scoped to PC_PLAYTEST only),
`ResolveTargets_WithPlaytestSugEnabled_ProducesConcurrencyOfOne` (enabled → exactly one server), and
`ResolveTargets_WithPlaytestSugDisabled_ProducesNoTarget` (disabled → none). Tests 24/24. With the PR abandoned, that coverage now lives only on the abandoned branch — if it's still wanted, Timi can
re-home it in his repo. Both prerequisites this PR waited on are now done: the SUG is registered (PRs
[20](./20-PTNR-DATA-15965750-add-pc-playtest-sug-test.md) / [21](./21-PTNR-DATA-15965763-add-pc-playtest-sug-int.md)) and the
quota is applied in Int (PR [22](./22-DCFG-15966616-contenttargets-pc-playtest-quota.md)).

Dynamic-config quota to apply instead:
`CONTENTTARGETS/DEFAULT/SERVERSETSCONFIGURATION` →
`SkuConfigs:STANDARD_NC64AS_T4_V3:QuotasBySugByRegion:WESTUS2:PC_PLAYTEST = 1`.

Do not restate/replace the existing live `STANDARD_NC64AS_T4_V3` SKU block: live config already has
`GameplaySlotsPerServer = 4` and `DefaultMaxLocalSpaceInMB = 2000000`. The reverted appsettings attempted to check in
`1` / `360445`, which would clobber those live values.

Open question for Timi: if PC playtest still needs the install-on-attach enable override, should he add
`CONTENTTARGETS/DEFAULT/RESOLUTIONCONFIGURATION` `IncludePredictions.Override = { Value:true, ServerType:PC, Sugs:[PC_PLAYTEST] }`,
or are predictions already enabled in non-prod for existing PC SUGs?

## Context
- Tracks [`../FuturePlans/pc-install-readiness-polling-implementation.md`](../FuturePlans/pc-install-readiness-polling-implementation.md) **C1/C2** and [`../Blockers/pc-install-readiness-poll.md`](../Blockers/pc-install-readiness-poll.md).
- Pairs with CTIN PR [17](./17-CTIN-15896502-pc-install-readiness-polling.md) (the poll) and its `PlaytestPcReadinessQuery` config (SUG must match).
- Per-repo detail: [`../Repos/services.contenttargets.md`](../Repos/services.contenttargets.md).

## Deferred / dependencies
- **BLOCKING — Partner Registry must set the SUG on the offering.** `PlaytestProcessor` sets Regions + SKU but not
  `SystemUpdateGroupWeights`/`SelectableSystemUpdateGroups`, so the offering carries no SUG and the title maps to no
  PC_PLAYTEST server set. Needs a separate partner-registry change to add `PC_PLAYTEST`.
- **OS Targets** must provision the `PC_PLAYTEST` SUG under `STANDARD_NC64AS_T4_V3` in WESTUS2, or no server set is created.
- **Dynamic config** must add the `PC_PLAYTEST` quota under the existing live `STANDARD_NC64AS_T4_V3`/WESTUS2 block.
- **SKU coupling:** `PcServerSku = STANDARD_NC64AS_T4_V3` is a documented temporary stand-in in partner registry; this
  config, OS Targets, and CTIN must stay on the same SKU.
- The SUG string + region must be identical across partner registry, OS Targets, this config, and CTIN
  `PlaytestPcReadinessQuery`. `PC_PLAYTEST` is proposed — confirm with Timi.
- **Test/Int IncludePredictions** is an open question for Timi: existing non-prod PC SUGs have quotas without an obvious
  per-SUG override, so `PC_PLAYTEST` may not need one. **Prod** deferred (`IncludePredictions` allows one `Override`, taken
  by `ServerType=XBOX`; prod region NorthCentralUs).
- Deploy via CI/CICD, not the PR pipeline.
