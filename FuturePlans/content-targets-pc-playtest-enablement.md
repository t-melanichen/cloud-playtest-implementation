# Future plan: Content Targets — PC playtest install-on-attach + quota

**Why it matters:** CTIN's PC readiness poll (`PollPcFirstInstallAsync`) can only succeed once a PC server has actually
staged the playtest build. That first install is driven by the **Content Targets** service (`services.contenttargets`),
which tells the PC Orchestrator how many servers to provision per *server set* and which installs map to them. This is
Timi's C1 (enable install-on-attach) + C2 (server quota), now scoped and partially implemented.

## PR / branch
- **Repo:** services.contenttargets (Xbox.Streaming)
- **Branch:** `t-melanichen/pc-playtest-install-on-attach`
- **PR:** [15946980](https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.contenttargets/pullrequest/15946980) (Draft) — see [`../PRProgress/18-CTGT-15946980-pc-playtest-install-on-attach.md`](../PRProgress/18-CTGT-15946980-pc-playtest-install-on-attach.md) and [`../Repos/services.contenttargets.md`](../Repos/services.contenttargets.md).

## As-built mechanism (verified in code)
The chain that turns "title attached to a playtest offering" into "≥1 PC server installs the build":
1. **Server set must exist with quota.** `ServerSetsProcessor.UpdatePCServerSetsAsync` creates a PC server set
   `ServerSetId.CreatePC(region, sug, sku)` only when the SUG is **both** in the **OS Targets** manifest **and** has a
   quota in `ServerSetsConfiguration.SkuConfigs[sku].QuotasBySugByRegion[region][sug]`. That quota = `ServerQuota`. **(C2)**
2. **Offering → install ids.** `UpdateInstallIdsByServerSetAsync` reads MICROSOFT-partner `OfferingV2`s and maps each
   active title's install ids to the PC server sets the offering targets via
   `Title.EnumeratePCServerSets(offering, regions, sugs)`. Offering SUGs come from
   `OfferingV2.SystemUpdateGroupWeights`/`SelectableSystemUpdateGroups`.
3. **Concurrency = Predictions (1 per install id) for PC.** `ResolutionProcessor` has **no implemented BaseTargets**
   path; PC concurrency comes from `PredictionsProcessor.CalculatePCPredictions` (1 per install id, synthetic), included
   only when `ResolutionConfiguration.IncludePredictions.GetValue(serverSet)` is **true** (default false; only XBOX is
   overridden on). Enabling it for the PC playtest SUG is Timi's "it's implemented but disabled — conditionally enable it." **(C1)**
4. **Orchestrator provisions + installs.** PC Orchestrator `ConfigManifestProvider` calls
   `ResolveTargetsAsync` with `TargetsQuery.Create()` → `DistributionTargets` (includes the `Predictions` flag), so the
   override is honored; it provisions up to `ServerQuota` servers and installs the server set's install ids. CTIN then polls and sees the server.

## Implemented in the PR (Int)
- `appsettings.ContentTargets.Int.json`: a `STANDARD_NC64AS_T4_V3` SkuConfig with
  `QuotasBySugByRegion.WESTUS2.PC_PLAYTEST = 1` (one T4) **(C2)**, and a `ResolutionConfiguration.IncludePredictions`
  override (`ServerType=PC`, `Sugs=[PC_PLAYTEST]`, `Value=true`) **(C1)**.
- `ResolutionConfigurationBindingTests` proves the override binds (`Sugs` HashSet<Id>) and matches only the
  PC_PLAYTEST PC server set. Core.UnitTests suite **22/22**.
- SKU + region match the offering created by partner registry `PlaytestProcessor`
  (`PcServerSku = STANDARD_NC64AS_T4_V3`; non-prod regions WestUS2/WestEurope).

## Remaining work
- [ ] **BLOCKING — Partner Registry must set the SUG on the playtest offering.** `PlaytestProcessor` sets Regions +
  `TargetServerSkus` but **not** `SystemUpdateGroupWeights`/`SelectableSystemUpdateGroups`, so the offering carries no
  SUG and the title maps to **no** PC_PLAYTEST server set. Separate partner-registry PR to add `PC_PLAYTEST` (no GA fallback).
- [ ] **OS Targets** must provision `PC_PLAYTEST` under `STANDARD_NC64AS_T4_V3` in WESTUS2, or `UpdatePCServerSetsAsync` skips it.
- [ ] **Confirm the SKU + SUG name with Timi.** `PlaytestProcessor.PcServerSku` is a documented temporary stand-in;
  the SKU must stay identical across partner registry, this config, OS Targets, and CTIN. `PC_PLAYTEST` is the proposed SUG name.
- [ ] **CTIN deployment config.** Set `IngestionWorkflowSettings:PlaytestPcReadinessQuery`
  (`SystemUpdateGroup=PC_PLAYTEST`, `Regions=[WESTUS2]`, `Skus=[STANDARD_NC64AS_T4_V3]`) in the CTIN **worker** env
  appsettings (or via Savant). Note env-name mismatch: content-targets has `Int`; the CTIN worker has only
  `Development/Test/Prod` — map the CTIN env to the content-targets `Int` deployment.
- [ ] **Test** deferred: its configured fleet region is WESTUS3, which the offering (WestUS2/WestEurope) doesn't target.
- [ ] **Prod** deferred: `IncludePredictions` allows a single `Override`, already used by `ServerType=XBOX`. Needs the
  config model extended to support **multiple overrides**; prod region is `NorthCentralUs`.
- [ ] Deploy via **CI/CICD** (not the PR pipeline), then validate end-to-end (attach title → server provisioned → CTIN poll → ready).

## Owners
Melanie Chen (CTGT config + CTIN config) · Timi Bolaji (OS Targets SUG/quota, SKU confirmation) · Partner Registry owner (offering SUG).

## Sources
- services.contenttargets: `Processors/Implementations/{ResolutionProcessor,ServerSetsProcessor,PredictionsProcessor}.cs`,
  `Configuration/{ConfigItem,ResolutionConfiguration,SkuConfiguration}.cs`, `Extensions/{OfferingExtensions,TitleExtensions}.cs`,
  `Contracts/{TargetsQuery,TargetsCalculationMode}.cs`.
- services.pcservices: `Orchestrator.Core/Manifests/ConfigManifestProvider.cs`.
- services.partnerregistry: `Processors/PlaytestProcessor.cs`.
- [`./pc-install-readiness-polling-implementation.md`](./pc-install-readiness-polling-implementation.md) C1/C2.
