# Future plan: Launch-link return + status accuracy

**Why it matters:** The end goal is a one-click shareable streaming link. We need (a) the launch URL to get back to Partner Center / the creator, and (b) the playtest status to be accurate enough that a tester who clicks the link doesn't hit a 404 because the title isn't actually live yet.

## Current understanding (Sync 3 — Anthony)
- Launch URL shape: `https://play.xbox.com/play/launch/{productId}?offeringId=xpt{PlaytestProductId}`.
- Today playtest status is only **~85–90% accurate** because **XProduct is async** — it's the long pole. xPlaytest writes the contract, XProduct writes to Azure storage, queues a service bus message, a transformer picks it up and writes to its DB. There's currently no signal back from XProduct that it's done.
- Consequence: if a deep link is clicked **right away**, the tester can see a **404 / "doesn't exist"** because the status said live before it truly was.
- xCloud wants to tighten this and also measure the update latency (alert if it grows).
- Cross-tenant S2S / SAGE caller and ingestion-poll tasks now consolidated in [`FuturePlans/s2s-cross-tenant-call.md`](./s2s-cross-tenant-call.md).

## Options
- Tie the `StreamingReady` transition to terminal ingestion status and offering completion before surfacing the launch link; the SAGE/CTIN caller and poll implementation is tracked in [`FuturePlans/s2s-cross-tenant-call.md`](./s2s-cross-tenant-call.md).
- Pursue an XProduct **post-back "done"** signal so status reflects true liveness.
- Add latency telemetry on the XProduct update.

## Open questions
- Can XProduct post back a completion signal in this timeframe, or do we gate on the ingestion/offer completion signals we own?
- What's the acceptable 404 window for the demo vs GA?

## Owners
Melanie Chen · Anthony Keller (XProduct status pipeline).
