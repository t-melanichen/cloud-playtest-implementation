# Blocker: PC streaming-package readiness polling

**Status:** In progress — version-aware poll implemented in PR `t-melanichen/playtest-pc-install-polling`; upstream install enablement (Timi) still pending
**Owners:** Melanie Chen (xPlaytest) · Timi Bolaji (content/install)

## Update (2026-06-15)
The version-aware PC poll is implemented in branch `t-melanichen/playtest-pc-install-polling`
(services.contentingestion): `PollFirstInstallAsync` now resolves the ingested version (install id +
hash) and queries the PC server pool by `LocalPackageId` + `LocalPackageHash`. Full step list, the
remaining repo work (PC-playtest SUG constant, region config), and Timi's upstream prerequisites
(enable install-on-attach + set the PC server quota) are tracked in
[`FuturePlans/pc-install-readiness-polling-implementation.md`](../FuturePlans/pc-install-readiness-polling-implementation.md).

## Problem
Before a streaming playtest can be marked ready, we need to know that the streaming package has been **installed and is ready on a PC server**. The existing install-poll path is console-only: `TitleIngestionWorker.PollFirstInstallAsync` hardcodes Xbox allocator parameters (e.g. `ServerType.XboxV3SeriesS`, `XBOX_*` pool ids), so PC playtests fall into Xbox-only logic and the PC readiness signal isn't available today.

## Current direction (Sync 3, 2026-06-10 — Timi)
- A usable API already exists for PC: *"similar to the Xbox polling where we have some entity that owns servers… you check the servers and see if the game you want is already one of them."* — *"Such an API already exists today. We just need to plug it in."*
- **Ordering clarification:** you don't have to wait for install before creating the offering. *Adding the title to the offering is what triggers the install* — the service notices a title in the offering, performs the install(s), and **then** you can poll for completion. So the sequence is: configure offering + attach title → poll the PC server-query API for readiness.
- **Confirmed API (2026-06-18):** `IPCOrchestratorClient.QueryServersPagedAsync(new FilteredQuery<GameStreamingServerFilter>(filter))` in `services.pcservices` (`Orchestrator.Client`). Timi's "content file filter" = `filter.Content = [ new ContentFileFilter { Id = <install id>, Version = <hash> } ]` (remark: when multiple are specified, ALL must be present on the server). SUG → `filter.SystemUpdateGroups`, region → `filter.Regions`, SKU → `filter.Skus`. The current PR instead calls the Allocation Manager (`IServerAllocatorClient`), which is the **wrong surface for PC** and must be swapped.

## Next actions
1. ~~Identify the exact PC server-query API~~ **Done (2026-06-18):** `IPCOrchestratorClient.QueryServersPagedAsync` with `GameStreamingServerFilter.Content = [ContentFileFilter{Id, Version}]` (see Confirmed API above).
2. ~~Swap the PC branch of `PollFirstInstallAsync` from `IServerAllocatorClient` to `IPCOrchestratorClient`~~ **Done (2026-06-18):** package refs added, `AddGSHttpClient<IPCOrchestratorClient, PCOrchestratorClient>()` registered in the Worker, `IPCOrchestratorClient` injected, PC branch rebuilt on `GameStreamingServerFilter.Content`. Solution builds clean; 14/14 workflow unit tests pass. Xbox branch unchanged.
3. ~~Pair the per-version `targetVersion.InstallId` with `targetVersion.Hash`~~ **Done (2026-06-18).**
4. Validate that polling after title-attach correctly observes install completion (needs Timi's upstream install-on-attach + quota; see FuturePlans C1/C2).

## References
- `Transcripts/Sync3.docx` — Timi on PC polling + install-on-attach ordering.
- `SPEC.md` §3.6 (PC fork of install poll), XC6.
- `Files/TitleIngestionWorker.cs` (`PollFirstInstallAsync`).
