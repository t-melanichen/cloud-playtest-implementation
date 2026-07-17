# Future plan: Launch-link return + status accuracy

**Why it matters:** The end goal is a one-click shareable streaming link. We need (a) the launch URL to get back to Partner Center / the creator, and (b) the playtest status to be accurate enough that a tester who clicks the link doesn't hit a 404 because the title isn't actually live yet.

## Current understanding (Sync 3 — Anthony)
- Launch URL shape: `https://play.xbox.com/play/launch/{productId}?offering.id=xpt{PlaytestProductId}`.
- Today playtest status is only **~85–90% accurate** because **XProduct is async** — it's the long pole. xPlaytest writes the contract, XProduct writes to Azure storage, queues a service bus message, a transformer picks it up and writes to its DB. There's currently no signal back from XProduct that it's done.
- Consequence: if a deep link is clicked **right away**, the tester can see a **404 / "doesn't exist"** because the status said live before it truly was.
- xCloud wants to tighten this and also measure the update latency (alert if it grows).
- Cross-tenant S2S / SAGE caller and ingestion-poll tasks now consolidated in [`FuturePlans/s2s-cross-tenant-call.md`](./s2s-cross-tenant-call.md).

## Status — backend link surfacing implemented (2026-07-04)

**Done (backend, `Xbox.Xbet.Service` PlayTest):** the launch link is now returned on the playtest API
response, so it gets back to the creator / Partner Center automatically.
- New field `PlaytestResponse.StreamingLaunchUrl` (`PlayTest.Shared/Contracts/PlaytestResponse.cs`,
  protobuf tag 19 — backward-compatible).
- New pure helper `PlaytestStreamingLink.TryBuildLaunchUrl(sellerId, productId, status)`
  (`PlayTest/Streaming/PlaytestStreamingLink.cs`) building
  `https://play.xbox.com/play/launch/{PartnerCenterProductId}?offering.id=xpt{PartnerCenterProductId}`.
- Both `PlaytestMappers` methods wired. **Status-accuracy gate baked in:** the link is populated **only**
  when the playtest is streaming-eligible (pilot seller `65050620`) **and** `Status == Published` (live),
  so a tester never receives a link before the title is streamable. Draft / Publishing / non-pilot → `null`.
- Tests: 4 added in `PlaytestMappersTests.cs` (pilot+Published→link, non-pilot→null, pilot+not-Published→null,
  published-entity→link); full mapper suite green (56/56).

**Remaining:**
- **Front-end (Partner Center, `Xbox.Gpx.PartnerCenter.Client`):** display / copy the new
  `StreamingLaunchUrl` field on the playtest view — small FE change (repo not cloned locally).
- **Confirm the launch-path id with Anthony:** the path uses `PartnerCenterProductId`; if Bayside expects the
  XProduct big id there instead, it's a one-line change in the helper.
- The deeper XProduct post-back / offering-liveness signal (below) further tightens the 404 window; the
  `Published` gate is the first-order guard.

## Follow-up plan: gate the link on a persisted `StreamingStatus` (streaming-ready)

**Why:** the shipped gate is `Status == Published`, but streaming is **non-blocking**, so `Published`
reflects the *download* publish — it does not prove CTIN finished ingesting + configured the
`xpt{productId}` offering. To truly avoid a 404, gate the link on a real streaming-ready signal.

**Signal source:** `XPackagePlaytestPublishWorkflow.PollingStreamingIngestionJobStateHandlerAsync`
(~L581–596) — when the ingestion job reaches terminal success (`operationStatus.IsComplete &&
IsSuccess == true`). That's the moment the streaming offering is live.

**Plumbing that already exists:** the worker can't write the PlayTest DB directly — it emits status via
`PublishJobStatusAsync(...)` → `XPackagePlaytestPublishWorkflowJobStatusMessage` (service bus) →
`XPackagePlaytestPublishWorkflowJobStatusTopicProcessor` → `UpdatePlaytestStatusAsync` → `PlaytestEntity`.
A streaming-ready signal rides that same pipeline.

**Steps:**
1. New `StreamingStatus` enum `{ None, Scheduled, Ready, Failed }` (mirror `PlaytestStatus` in
   `PlayTest.Constants` + `PlayTest.Shared.Constants`).
2. Persist it — add a `StreamingStatus` column to `PlaytestEntity` (+ EF migration). Independent of
   `PlaytestStatus` (the playtest is still `Published` regardless — streaming is non-blocking).
3. Carry it on the write-back — add `StreamingStatus?` to the job-status message; the worker sets
   `Scheduled` after `SchedulingStreamingIngestionJob` returns a job id, `Ready` on the terminal-success
   above, and `Failed` in the non-blocking `catch` / `MaxStreamingIngestionWait` timeout paths. The topic
   processor + `UpdatePlaytestStatusAsync` persist it.
4. Surface it — add `StreamingStatus` to `PlaytestResponse`.
5. Gate the link — change `PlaytestStreamingLink.TryBuildLaunchUrl(sellerId, productId, streamingStatus)`
   to return the URL only when `streamingStatus == Ready` (instead of `Status == Published`); update the
   4 mapper tests + add worker tests for the three transitions.

**Lighter variant:** a single nullable `StreamingReadyOn` (DateTime?) set on terminal success; gate on
`!= null`. Same plumbing, smaller surface, and a "ready at" timestamp for free.

**Scope / sequencing:** cross-cutting (worker + message contract + topic processor + BL + entity +
**EF migration** + mapper) and **can't be E2E-verified until the Green SP unblocks ingestion** (the
`Ready` transition never fires today). Keep the `Published` gate as the interim guard; land
`StreamingStatus` once ingestion works so it can be tested end to end.

## Options
- Tie the `StreamingReady` transition to terminal ingestion status and offering completion before surfacing the launch link; the SAGE/CTIN caller and poll implementation is tracked in [`FuturePlans/s2s-cross-tenant-call.md`](./s2s-cross-tenant-call.md).
- Pursue an XProduct **post-back "done"** signal so status reflects true liveness.
- Add latency telemetry on the XProduct update.

## Open questions
- Can XProduct post back a completion signal in this timeframe, or do we gate on the ingestion/offer completion signals we own?
- What's the acceptable 404 window for the demo vs GA?

## Owners
Melanie Chen · Anthony Keller (XProduct status pipeline).
