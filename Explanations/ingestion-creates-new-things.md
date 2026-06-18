# Ingestion creates new things

**Why it matters:** xCloud playtest ingestion is not just "mark this existing product streamable." It creates and connects streaming-side title/package state, then install services react to that state.

## Per-playtest title IDs

xCloud mints its own per-playtest IDs on demand. Timi described the title construct as one per playtest, and Jack confirmed xCloud is creating its own IDs on demand. That means playtest date/expiry configuration belongs on the distinct xCloud title for that playtest, not on a shared offering. *(InternSync4 — Timi Bolaji ~15:42; Jack Heuberger ~16:02)*

This is separate from the required numeric Xbox Live Title ID on `StoreAsset.XboxTitleId`, which xPlaytest must resolve before calling xCloud. That blocker is tracked in [`../Blockers/xbox-live-title-id.md`](../Blockers/xbox-live-title-id.md).

## Offering-to-install chain

The ingestion/configuration chain discussed with Timi is:

1. Add the content/title to an offering.
2. Configure the offering with the target service queue, SUG, and SKU.
3. Use one shared SKU and one shared SUG for playtests unless/until the platform exposes more specific routing.
4. The content-targets service reads offering config, notices "this title is in this offering," and determines that the title needs at least one install in that server set.
5. The distribution service performs the install if a server exists.
6. Distribution updates the PC Orchestrator manifest.
7. Readiness polling sees the content available. *(XCloudIngestion — Timi Bolaji ~11:21–13:43; InternSync3 — Timi Bolaji ~5:54)*

For PC, the server quota config caps how many servers a SUG can consume. The MVP direction was to set the PC playtest quota to 1 because one T4 is expensive. *(XCloudIngestion — Timi Bolaji ~12:42–13:03)*

## Xbox pre-pull vs PC on-demand

Xbox content is pre-installed on a fixed pool and can be made available before players arrive. PC is more on-demand: content may land only when a streaming session is requested, so the first tester can pay the wait. Timi said skipping PC polling can be acceptable for an MVP if the user is told to keep trying until it works, because the waiting time is still paid somewhere. *(InternSync4 — Jack Heuberger / Timi Bolaji on Xbox vs PC provisioning; XCloudIngestion — Timi Bolaji ~18:37)*

The planned PC polling work is tracked in [`../Blockers/pc-install-readiness-poll.md`](../Blockers/pc-install-readiness-poll.md) and [`../FuturePlans/pc-install-readiness-polling-implementation.md`](../FuturePlans/pc-install-readiness-polling-implementation.md).

## PC versioning by hash

Every republish creates a new version. On PC, polling "installed somewhere" is insufficient; the poll must prove the exact version is installed. Timi described the PC version as the content hash: a SHA-256 over concatenated game and DLC versions. The workflow should call resolution to get install id + hash, then query PC Orchestrator with a content-file filter containing both values. *(XCloudIngestion — Timi Bolaji ~16:52–17:31; `PollFirstInstallAsync` / `PollPcFirstInstallAsync`)*

The confirmed PC Orchestrator surface is `IPCOrchestratorClient.QueryServersPagedAsync(new FilteredQuery<GameStreamingServerFilter>(filter))` with `ContentFileFilter { Id = <install id>, Version = <hash> }`. See [`../Blockers/pc-install-readiness-poll.md`](../Blockers/pc-install-readiness-poll.md).

## Exclusive workflow behavior

`PlaytestTitleIngestionWorkflow` is an exclusive workflow keyed by playtest id. With the current default queue depth of 1, a second ingestion for the same playtest conflicts while the first is in flight. Timi called out the product choice: keep a conflict experience or raise queue depth so version 1.1 waits behind version 1.0. *(XCloudIngestion — Timi Bolaji ~19:39–20:22; services.contentingestion — `PlaytestTitleIngestionWorkflow`)*

## Sources

- `Transcripts/XCloudIngestion.docx`
- `Transcripts/InternSync4.docx`
- `Transcripts/InternSync3.docx`
- [`../Repos/services.contentingestion.md`](../Repos/services.contentingestion.md)
- [`../Blockers/xbox-live-title-id.md`](../Blockers/xbox-live-title-id.md)
- [`../Blockers/pc-install-readiness-poll.md`](../Blockers/pc-install-readiness-poll.md)
- [`../FuturePlans/pc-install-readiness-polling-implementation.md`](../FuturePlans/pc-install-readiness-polling-implementation.md)
