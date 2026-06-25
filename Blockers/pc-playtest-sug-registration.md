# Blocker: PC playtest SUG (`PC_PLAYTEST`) must be registered at the platform level

**Status:** Mostly unblocked (2026-06-22) — the `PC_PLAYTEST` SUG is **registered (merged) in Test + Int** and the
dynamic-config quota is **applied (merged) in Int**. One open item remains: confirm Int actually has
`STANDARD_NC64AS_T4_V3` (NC64) GPU capacity in WESTUS2. The two code PRs (15896502, 15949594) are Active with all review
threads resolved. The SUG parent is left as `PC_GA`, which the user confirmed is acceptable for Test/Int.
**Owners:** Melanie Chen (SUG definition + offering/poll PRs) · Timi Bolaji (GPU capacity / `IncludePredictions` confirm) ·
Jack Heuberger (resolution walkthroughs)
Timi Bolaji (dynamic-config quota / GPU capacity / `SystemUpdateGroup` Ids recognition)

## Problem
The whole PC playtest install/readiness chain references a **distinct PC playtest System Update Group (SUG)** — a named
pool of streaming servers. Nothing works until that SUG is **registered** in two places:

1. **OS Targets manifest (required).** Content Targets only builds a PC server set for SUGs present in the OS Targets
   manifest (`ServerSetsProcessor.UpdatePCServerSetsAsync` reads `IOSTargetsClient.GetOSTargetsManifestAsync`). Without an
   entry for `PC_PLAYTEST` + `STANDARD_NC64AS_T4_V3` + `WESTUS2`, no server set is created and no PC server runs in the
   SUG, so the install can never happen.
2. **`SystemUpdateGroup` Ids registry (recognition).** Partner-registry offering validation calls
   `SystemUpdateGroup.GetId(sug, env)` (`ValidationProcessorUtilities.cs:421`). The recognized SUGs are a **hardcoded list**
   in `Microsoft.GameStreaming.Services.Common.Ids` (GA, Canary, Selfhost, …) — `PC_PLAYTEST` is **not** in it. An unknown
   SUG only produces a **non-critical validation warning** (`Critical = false`), not a hard block, but it should be added
   for cleanliness (or confirmed to have a dynamic path).

Timi described enabling this as a **dynamic-config flip he'd do** ("we will have a distinct PC underscore play test SUG …
I have things set up that way already"), which doesn't match the hardcoded Ids list — so the exact mechanism + name need
confirming with him.

## SUG setup — the two parts (per Timi)
Setting up `PC_PLAYTEST` is **two** steps:

1. **Quota** — the dynamic-config line in `SERVERSETSCONFIGURATION` (see question 4). This says "the PC_PLAYTEST lane is
   *allowed* N servers."
2. **SUG definition** — register the SUG itself on the **PC SUG Definitions** page
   (`https://americas.gssv-dev-prod.xboxlive.com/PcSugDefinitions`). A SUG definition (`PCSystemUpdateGroup` in OS Targets)
   assigns the **OS image versions** (the Windows/OS build the GPU servers run) per SKU via *flighting configs*.
   **Jack's recommendation (2026-06-22): create `PC_PLAYTEST` to *inherit from* a stable release SUG — `PC_TAKEHOME`
   (currently the most solid) — and NOT `PC_GA`.** On the page: **Add PC Sug Definition** → `Sug Id = PC_PLAYTEST`,
   `Inherits From = PC_TAKEHOME`, then **Link to Parent** for Developer Settings *and* Flighting Configs so it inherits
   PC_TAKEHOME's known-good OS images for the SKU instead of hand-picking image versions. (If you don't inherit, the page
   demands a manual Flighting Config row with a non-empty Version — "At least one Flighting Config is required when configs
   are not inherited" — which is exactly what inheriting avoids.) This page writes the OS Targets SUG entry.
   **Owner: Melanie can self-serve this** — Jack: *"you need to go to the PC SUG configuration page and set up the SUG."*
   Step-by-step: [`../FuturePlans/pc-playtest-dynamic-config-and-sug-setup.md`](../FuturePlans/pc-playtest-dynamic-config-and-sug-setup.md) §3.

## What's already done (all pinned to `PC_PLAYTEST`)
- **services.data.partnerregistry SUG definitions — MERGED:** [PR 15965750](https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.data.partnerregistry/pullrequest/15965750) (Test) + [PR 15965763](https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.data.partnerregistry/pullrequest/15965763) (Int) register `PCSystemUpdateGroup/PC_PLAYTEST`. The as-built definitions inherit from `"PC_GA"` (with null flighting configs); the user confirmed that `PC_GA` is acceptable for Test/Int, so no parent change is needed.
- **services.data.partnerregistry dynamic-config quota — MERGED (Int):** [PR 15966616](https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.data.partnerregistry/pullrequest/15966616) adds `STANDARD_NC64AS_T4_V3 → WESTUS2 → PC_PLAYTEST = 1` under `CONTENTTARGETS/DEFAULT/SERVERSETSCONFIGURATION` (Option A; live NC8/D4S blocks untouched). Test got the SUG def but **no quota** (WESTUS2/WESTUS3 mismatch — defer per setup doc).
- **services.contenttargets** [PR 15946980](https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.contenttargets/pullrequest/15946980) — superseded by dynamic config PR 15966616; abandoned.
- **services.partnerregistry** [PR 15949594](https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.partnerregistry/pullrequest/15949594) — sets the SUG + weights on the playtest offering (all review threads resolved).
- **services.contentingestion** [PR 15896502](https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.contentingestion/pullrequest/15896502) — the readiness poll + pin it to the SUG/SKU (all review threads resolved).

## Questions for Timi (the unblockers)
1. **Exact SUG name** — `PC_PLAYTEST`, or something else? (Will be matched across all three PRs.)
2. **OS Targets** — is `PC_PLAYTEST` already provisioned for `STANDARD_NC64AS_T4_V3` in `WESTUS2` (Int), or still pending?
3. **Recognition** — does `PC_PLAYTEST` need adding to `Services.Common.Ids` `SystemUpdateGroup`, or is there a dynamic path?
4. **Enable + quota — dynamic config.** Timi decided the Content Targets enable + quota settings should live in dynamic
   config, not checked-in `appsettings`. In ConfigSection `CONTENTTARGETS/DEFAULT/SERVERSETSCONFIGURATION` (portal path
   `DynamicConfigPartnerRegistry/ConfigSections/CONTENTTARGETS/DEFAULT/SERVERSETSCONFIGURATION`), add only
   `SkuConfigs:STANDARD_NC64AS_T4_V3:QuotasBySugByRegion:WESTUS2:PC_PLAYTEST = 1`. The live SKU block already exists
   (`GameplaySlotsPerServer = 4`, `DefaultMaxLocalSpaceInMB = 2000000`); do not replace it with the reverted PR values
   (`1` / `360445`).
5. **IncludePredictions open question** — if PC playtest still needs an enable override, it belongs in
   `CONTENTTARGETS/DEFAULT/RESOLUTIONCONFIGURATION` as
   `IncludePredictions:Override = { Value:true, ServerType:PC, Sugs:[PC_PLAYTEST] }`. Ask Timi to confirm whether this is
   required in Int/Test, since existing non-prod PC SUGs such as `PC_TAKEHOME` already have working quotas without an
   obvious per-SUG override.
6. **SKU** — `STANDARD_NC64AS_T4_V3` is a hardcoded stand-in on the offering; is that the right T4 SKU?

## Next actions
- Send Timi the questions above; get the exact SUG name + confirmation it's provisioned in OS Targets (+ recognized in Ids),
  and ask him to apply the `SERVERSETSCONFIGURATION` dynamic-config quota.
- Update the SUG literal in all three PRs if the name differs; then deploy via CI/CICD and validate (see the test plan in
  [`../FuturePlans/content-targets-pc-playtest-enablement.md`](../FuturePlans/content-targets-pc-playtest-enablement.md)).

## References
- **PC SUG Definitions page:** `https://americas.gssv-dev-prod.xboxlive.com/PcSugDefinitions` — register `PC_PLAYTEST`
  inheriting from `PC_TAKEHOME`. Backed by `services.devapi` `DevApiGateway/Pages/PcSugDefinitions/`
  (`PcSugDefinitionInfo.cs`: `InheritsFrom` / `InheritsConfigs`; `PcSugFlightingConfigInfo.cs`: per-SKU OS image versions).
- `Transcripts/XCloudIngestion.docx` (Timi on the PC_playtest SUG, quota, dynamic config).
- [`../FuturePlans/content-targets-pc-playtest-enablement.md`](../FuturePlans/content-targets-pc-playtest-enablement.md) — full design + test plan.
- [`./pc-install-readiness-poll.md`](./pc-install-readiness-poll.md) — the original readiness-poll blocker (now implemented).
