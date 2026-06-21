# Blocker: PC playtest SUG (`PC_PLAYTEST`) must be registered at the platform level

**Status:** Open — blocks end-to-end PC playtest streaming. All three dependent PRs are drafts, pinned to
`PC_PLAYTEST` / `STANDARD_NC64AS_T4_V3` / `WESTUS2`, and ready once the SUG exists.
**Owners:** Timi Bolaji (OS Targets + `SystemUpdateGroup` Ids registration) · Melanie Chen (matches the name across the 3 PRs)

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

## What's already done (the 3 PRs, all draft, all pinned to `PC_PLAYTEST`)
- **services.contenttargets** [PR 15946980](https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.contenttargets/pullrequest/15946980) — enable install-on-attach + quota=1 for the SUG (Int).
- **services.partnerregistry** [PR 15949594](https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.partnerregistry/pullrequest/15949594) — set the SUG on the playtest offering.
- **services.contentingestion** [PR 15896502](https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.contentingestion/pullrequest/15896502) — the readiness poll + pin it to the SUG/region/SKU.

## Questions for Timi (the unblockers)
1. **Exact SUG name** — `PC_PLAYTEST`, or something else? (Will be matched across all three PRs.)
2. **OS Targets** — is `PC_PLAYTEST` already provisioned for `STANDARD_NC64AS_T4_V3` in `WESTUS2` (Int), or still pending?
3. **Recognition** — does `PC_PLAYTEST` need adding to `Services.Common.Ids` `SystemUpdateGroup`, or is there a dynamic path?
4. **Enable + quota** — flip via dynamic config, or land the content-targets PR as the checked-in source? Dynamic keys:
   `ServerSetsConfiguration:SkuConfigs:STANDARD_NC64AS_T4_V3:QuotasBySugByRegion:WESTUS2:PC_PLAYTEST = 1` and
   `ResolutionConfiguration:IncludePredictions:Override = { Value:true, ServerType:PC, Sugs:[PC_PLAYTEST] }`.
5. **SKU** — `STANDARD_NC64AS_T4_V3` is a hardcoded stand-in on the offering; is that the right T4 SKU?

## Next actions
- Send Timi the questions above; get the exact SUG name + confirmation it's provisioned in OS Targets (+ recognized in Ids).
- Update the SUG literal in all three PRs if the name differs; then deploy via CI/CICD and validate (see the test plan in
  [`../FuturePlans/content-targets-pc-playtest-enablement.md`](../FuturePlans/content-targets-pc-playtest-enablement.md)).

## References
- `Transcripts/XCloudIngestion.docx` (Timi on the PC_playtest SUG, quota, dynamic config).
- [`../FuturePlans/content-targets-pc-playtest-enablement.md`](../FuturePlans/content-targets-pc-playtest-enablement.md) — full design + test plan.
- [`./pc-install-readiness-poll.md`](./pc-install-readiness-poll.md) — the original readiness-poll blocker (now implemented).
