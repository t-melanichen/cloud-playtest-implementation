# Repo: services.contenttargets

**Role (CTGT):** Computes how many game-streaming servers to provision per **server set** (region × SUG × SKU)
and which content installs map to them, so the **PC Orchestrator** (`services.pcservices`) provisions servers and
installs content. This is the **upstream** that makes CTIN's PC readiness poll (`PollPcFirstInstallAsync`) succeed:
without a PC server staging the build, the poll can only time out.

- **ADO:** `microsoft/Xbox.Streaming` — https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.contenttargets
- **Default branch:** `main`
- **Feature branch:** `t-melanichen/pc-playtest-install-on-attach`

## How PC install-on-attach actually works (as-built)

1. **Offering → install ids.** `ServerSetsProcessor.UpdateInstallIdsByServerSetAsync` reads MICROSOFT-partner
   `OfferingV2`s from the Partner Registry cache, and for each active title maps its install ids to the PC server
   sets the offering targets (`Title.EnumeratePCServerSets(offering, regions, sugs)` → `ServerSetId.CreatePC(region, sug, sku)`).
   The offering's SUGs come from `OfferingV2.SystemUpdateGroupWeights`/`SelectableSystemUpdateGroups`. **Gap:** the
   playtest offering is created by partner registry `PlaytestProcessor`, which currently does **not** set either, so
   the offering carries no SUG and the title maps to no PC_PLAYTEST server set until partner registry adds it.
2. **Server set must exist with quota.** `UpdatePCServerSetsAsync` only creates a PC server set when the SUG is **both**
   present in the **OS Targets manifest** (`IOSTargetsClient.GetOSTargetsManifestAsync`) **and** has a quota in
   `ServerSetsConfiguration.SkuConfigs[sku].QuotasBySugByRegion[region][sug]`. The quota becomes `ServerSetMetadata.ServerQuota`.
3. **Concurrency target = Predictions (1 per install id) for PC.** `ResolutionProcessor.ResolveTargetsAsync` has **no
   implemented BaseTargets** path; PC concurrency comes from `PredictionsProcessor.CalculatePCPredictions` which returns
   **1 per install id**. But it's only included when `ResolutionConfiguration.IncludePredictions.GetValue(serverSet)` is
   **true** — and the default is **false** (only `ServerType=XBOX` is overridden on in Prod). This is Timi's "it's
   implemented but **disabled**; for playtest we can conditionally enable it."
4. The PC Orchestrator calls `ResolveTargetsAsync` and provisions up to `ServerQuota` servers, installing the server
   set's install ids. CTIN then polls PC Orchestrator and sees the server.

## Changes made — `t-melanichen/pc-playtest-install-on-attach` (PR 15946980, draft)

Config-only, scoped to **Int**:

- `src/Product/ContentTargets.Core/appsettings.ContentTargets.Int.json` — add a `STANDARD_NC64AS_T4_V3` SkuConfig with
  `QuotasBySugByRegion.WESTUS2.PC_PLAYTEST = 1` (one T4), and add a
  `ResolutionConfiguration.IncludePredictions.Override { Value: true, ServerType: PC, Sugs: [PC_PLAYTEST] }`.
- `src/Tests/Unit/ContentTargets.Core.UnitTests/Configuration/ResolutionConfigurationBindingTests.cs` — proves the
  override binds (`Sugs` HashSet<Id>) and `GetValue` is true only for the PC_PLAYTEST PC server set. **Suite 22/22 passes.**

**SKU + region match the offering.** Partner registry `PlaytestProcessor` hardcodes the PC playtest title SKU to
`STANDARD_NC64AS_T4_V3` (a documented temporary stand-in) and non-prod offering regions to `WestUS2`/`WestEurope`.
Int's WESTUS2 fleet matches, so the change targets `STANDARD_NC64AS_T4_V3` + WESTUS2 (an earlier draft wrongly used the
`STANDARD_NC8AS_T4_V3` integration-testing SKU / WESTUS3 — caught in rubber-duck review).

**Deferred:** **Test** — its configured fleet region is WESTUS3, which the playtest offering (WestUS2/WestEurope)
doesn't target. **Prod** — `IncludePredictions` allows a single `Override`, already used by `ServerType=XBOX`; needs the
config model extended to support multiple overrides; prod region is `NorthCentralUs`.

## Dependencies / remaining (owned outside this repo)

- **BLOCKING — Partner Registry must set the SUG on the playtest offering.** `PlaytestProcessor.CreatePlaytestAsync`
  sets `Regions` + `TargetServerSkus` but does **not** set `SystemUpdateGroupWeights`/`SelectableSystemUpdateGroups`, so
  `offering.GetSystemUpdateGroups()` returns empty and `Title.EnumeratePCServerSets` maps the title to **no** PC_PLAYTEST
  server set. Partner registry must add `PC_PLAYTEST` to the offering (and not fall back to GA). Separate partner-registry PR.
- **OS Targets** must provision the `PC_PLAYTEST` SUG under `STANDARD_NC64AS_T4_V3` in WESTUS2, or
  `UpdatePCServerSetsAsync` skips it (it only considers SUGs present in the OS Targets manifest).
- **SKU coupling.** `PlaytestProcessor.PcServerSku = STANDARD_NC64AS_T4_V3` is a documented temporary stand-in. This
  config, OS Targets, and CTIN must all use the same SKU; if partner registry resolves the SKU differently, update here too.
- **SUG name + region must be identical** across: the Partner Registry offering, OS Targets, this config, and CTIN
  `IngestionWorkflowSettings.PlaytestPcReadinessQuery` (`SystemUpdateGroup` + `Regions`). Non-prod = WESTUS2/WestEurope;
  prod = NorthCentralUs. `PC_PLAYTEST` is the proposed SUG name — confirm with Timi.
- Deploy via **CI/CICD**, not the PR pipeline.

## Sources
- `services.contenttargets` Core: `Processors/Implementations/{ResolutionProcessor,ServerSetsProcessor,PredictionsProcessor}.cs`,
  `Configuration/{ConfigItem,ResolutionConfiguration,SkuConfiguration,ServerSetsConfiguration}.cs`, `Extensions/{OfferingExtensions,TitleExtensions}.cs`.
- [`../FuturePlans/pc-install-readiness-polling-implementation.md`](../FuturePlans/pc-install-readiness-polling-implementation.md) C1/C2.
- [`../Blockers/pc-install-readiness-poll.md`](../Blockers/pc-install-readiness-poll.md).
