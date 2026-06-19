# [CTGT] PR 15946980 — Enable PC playtest install-on-attach + quota (PC_PLAYTEST SUG)

- **Pull Request:** 15946980
- **Repo:** services.contenttargets (Xbox.Streaming)
- **Source branch:** `t-melanichen/pc-playtest-install-on-attach` → `main`
- **Status:** Draft
- **Opened:** 2026-06-19  |  **Closed:** —
- **Link:** https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.contenttargets/pullrequest/15946980

## Summary
Config-only change that enables PC playtest **install-on-attach** and sets the **server quota** for the
`PC_PLAYTEST` SUG, scoped to **Int**. This is the upstream prerequisite (Timi's C1 + C2) that lets CTIN's
`PlaytestTitleIngestionWorkflow.PollPcFirstInstallAsync` actually observe a PC server staging the build.

Two coupled config edits in `appsettings.ContentTargets.Int.json`:
1. **Quota (C2):** add a `STANDARD_NC64AS_T4_V3` SkuConfig with `QuotasBySugByRegion.WESTUS2.PC_PLAYTEST = 1`
   (one T4) so `UpdatePCServerSetsAsync` creates the server set.
2. **Enable install-on-attach (C1):** add `ResolutionConfiguration.IncludePredictions.Override`
   (`ServerType=PC`, `Sugs=[PC_PLAYTEST]`, `Value=true`) so PC predictions (1 per install id) are included for that
   SUG — PC has no BaseTargets path, and predictions are disabled by default (only XBOX is on).

SKU + region match the playtest offering created by partner registry `PlaytestProcessor`
(`PcServerSku = STANDARD_NC64AS_T4_V3`; non-prod regions WestUS2/WestEurope); Int's WESTUS2 fleet matches.
Adds `ResolutionConfigurationBindingTests` proving the override binds (`Sugs` HashSet<Id>) and matches only the
PC_PLAYTEST PC server set. Full Core.UnitTests suite: **22/22 pass.**

## Context
- Tracks [`../FuturePlans/pc-install-readiness-polling-implementation.md`](../FuturePlans/pc-install-readiness-polling-implementation.md) **C1/C2** and [`../Blockers/pc-install-readiness-poll.md`](../Blockers/pc-install-readiness-poll.md).
- Pairs with CTIN PR [17](./17-CTIN-15896502-pc-install-readiness-polling.md) (the poll) and its `PlaytestPcReadinessQuery` config (SUG must match).
- Per-repo detail: [`../Repos/services.contenttargets.md`](../Repos/services.contenttargets.md).

## Deferred / dependencies
- **BLOCKING — Partner Registry must set the SUG on the offering.** `PlaytestProcessor` sets Regions + SKU but not
  `SystemUpdateGroupWeights`/`SelectableSystemUpdateGroups`, so the offering carries no SUG and the title maps to no
  PC_PLAYTEST server set. Needs a separate partner-registry change to add `PC_PLAYTEST`.
- **OS Targets** must provision the `PC_PLAYTEST` SUG under `STANDARD_NC64AS_T4_V3` in WESTUS2, or no server set is created.
- **SKU coupling:** `PcServerSku = STANDARD_NC64AS_T4_V3` is a documented temporary stand-in in partner registry; this
  config, OS Targets, and CTIN must stay on the same SKU.
- The SUG string + region must be identical across partner registry, OS Targets, this config, and CTIN
  `PlaytestPcReadinessQuery`. `PC_PLAYTEST` is proposed — confirm with Timi.
- **Test** deferred (its WESTUS3 fleet doesn't match the offering's WestUS2/WestEurope). **Prod** deferred
  (`IncludePredictions` allows one `Override`, taken by `ServerType=XBOX`; prod region NorthCentralUs).
- Deploy via CI/CICD, not the PR pipeline.
