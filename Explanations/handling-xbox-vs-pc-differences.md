# Handling Xbox vs PC differences

**Why it matters:** The xPackage/xPlaytest implementation should isolate true platform differences instead of forking the whole publish flow.

## 1. Bump expiration cap from 7 to 30 days

Update both backend and UX clamps from 7 days to 30 days. The current backend `XCloudPlaytestTitleIngestionBuilder` clamp and the GPX cloud-streaming end-date validation are stale against the InternSync4 decision. *(InternSync4 — Jack Heuberger ~23:54; Anthony Keller ~18:00; `XCloudPlaytestTitleIngestionBuilder`)*

Implementation tracking: [`../FuturePlans/expiration-cap-30-days.md`](../FuturePlans/expiration-cap-30-days.md), [`../Repos/Xbox.Xbet.Service.md`](../Repos/Xbox.Xbet.Service.md), [`../Repos/Xbox.Gpx.PartnerCenter.Client.md`](../Repos/Xbox.Gpx.PartnerCenter.Client.md), and [XBET PR 15834601](../PRProgress/07-XBET-15834601-playtest-ingestion-payload-builder.md).

## 2. Put dates on the title, not the offering

Configure start/end/expiry on the individual xCloud title. Each playtest has its own distinct title construct, so title-level dates avoid coupling unrelated playtests through offering configuration. *(InternSync4 — Jack Heuberger ~14:43; Timi Bolaji ~15:42)*

## 3. Branch readiness polling by platform

Keep Xbox on allocator-style readiness. For PC, use PC Orchestrator plus version-aware filtering:

- Resolve install metadata to get the target install id and hash.
- Query PC Orchestrator with `ContentFileFilter { Id = <install id>, Version = <hash> }`.
- Treat "server found with that content file" as ready.

This prevents marking an old PC version ready after a republish. The current PC readiness work is tracked in [`../Blockers/pc-install-readiness-poll.md`](../Blockers/pc-install-readiness-poll.md) and [`../FuturePlans/pc-install-readiness-polling-implementation.md`](../FuturePlans/pc-install-readiness-polling-implementation.md). Related PC input gaps include [`../Blockers/aumid-pc.md`](../Blockers/aumid-pc.md). *(XCloudIngestion — Timi Bolaji ~16:52–17:31; `PollFirstInstallAsync` / `PollPcFirstInstallAsync`)*

For MVP, PC polling can be skipped if the product accepts notifying ready before the first install and letting the first tester retry until the content lands. That trades status accuracy for implementation speed. *(XCloudIngestion — Timi Bolaji ~18:37)* Launch/status accuracy follow-up belongs in [`../FuturePlans/launch-link-and-status-accuracy.md`](../FuturePlans/launch-link-and-status-accuracy.md).

## 4. Future start dates need no special handling

Do not add go-live trigger logic. xCloud installs while the title is not expired, even if the start date is in the future; the start date gates player-facing availability. *(InternSync4 — Jack Heuberger ~16:30; Timi Bolaji ~16:59)*

Region-specific capacity and routing are still real concerns, especially for constrained regions. Track those in [`../FuturePlans/region-configuration-routing.md`](../FuturePlans/region-configuration-routing.md).

## 5. Expiry changes are metadata updates; content versions re-ingest

Changing expiration should update title configuration in place. It is not a content re-ingest. Only new package/content versions should flow through ingestion again. *(InternSync4 — Jack Heuberger ~23:02)*

When a new version does re-ingest, remember the exclusive workflow behavior: `PlaytestTitleIngestionWorkflow` locks by playtest id with default queue depth 1, so concurrent same-playtest ingestion conflicts unless the queue depth is raised. *(XCloudIngestion — Timi Bolaji ~19:39–20:22)*

## Related blockers and future plans

- [`../Blockers/xbox-live-title-id.md`](../Blockers/xbox-live-title-id.md) — required nonzero `StoreAsset.XboxTitleId`.
- [`../Blockers/pc-install-readiness-poll.md`](../Blockers/pc-install-readiness-poll.md) — PC Orchestrator readiness polling.
- [`../Blockers/manual-pr-polling.md`](../Blockers/manual-pr-polling.md) — manual Partner Registry PR/operation polling gap.
- [`../Blockers/aumid-pc.md`](../Blockers/aumid-pc.md) — PC AUMID input gap.
- [`../Blockers/cross-tenant-s2s.md`](../Blockers/cross-tenant-s2s.md) and [`../FuturePlans/s2s-cross-tenant-call.md`](../FuturePlans/s2s-cross-tenant-call.md) — xPackage → SAGE → CTIN call path.
- [`../FuturePlans/delete-tombstone-lifecycle.md`](../FuturePlans/delete-tombstone-lifecycle.md) — deletion/GC lifecycle.

## Sources

- `Transcripts/InternSync4.docx`
- `Transcripts/XCloudIngestion.docx`
- `Transcripts/InternSync3.docx`
- [`../Repos/services.contentingestion.md`](../Repos/services.contentingestion.md)
- [`../Repos/Xbox.Xbet.Service.md`](../Repos/Xbox.Xbet.Service.md)
- [`../Repos/Xbox.Gpx.PartnerCenter.Client.md`](../Repos/Xbox.Gpx.PartnerCenter.Client.md)
- [`../Blockers/pc-install-readiness-poll.md`](../Blockers/pc-install-readiness-poll.md)
- [`../FuturePlans/pc-install-readiness-polling-implementation.md`](../FuturePlans/pc-install-readiness-polling-implementation.md)
- [`../FuturePlans/expiration-cap-30-days.md`](../FuturePlans/expiration-cap-30-days.md)
