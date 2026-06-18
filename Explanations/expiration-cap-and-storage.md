# Expiration cap and storage

**Why it matters:** Streaming playtests consume xCloud server storage differently from ordinary download playtests, especially on Xbox. The cap exists to make that storage bounded.

## Why a cap exists

Jack explained the storage problem: Xbox titles are pre-installed on a fixed pool of servers. Without expiry, playtest packages can keep extra storage space on xCloud servers forever. PC is more on-demand, but Xbox capacity needs a bounded uninstall point. *(InternSync4 — Jack Heuberger on expiration/storage; Jack Heuberger ~23:54)*

The cap is region-sensitive. Japan has much tighter capacity than West US 3, so even a global cap must be interpreted as a guardrail, not a promise of identical capacity everywhere. *(InternSync4 — Jack Heuberger ~23:54)*

## Decision: 30 days

The original backend and UI work used 7 days. In InternSync4, Jack said one week was fine but "30 days ... would also be fine"; Anthony and Emma agreed to use 30 days. *(InternSync4 — Jack Heuberger ~23:54; Anthony Keller / Emma Park agreement)*

The concrete 7→30 implementation work is tracked in [`../FuturePlans/expiration-cap-30-days.md`](../FuturePlans/expiration-cap-30-days.md).

## Where the cap belongs

Dates belong on the xCloud title, not the offering. Jack said expiry should be configured on the individual title, and Timi confirmed each playtest gets its own distinct title construct. *(InternSync4 — Jack Heuberger ~14:43; Timi Bolaji ~15:42)*

That means one offering can remain a routing/availability construct while each playtest title carries its own start/end/expiry metadata.

## Expiry updates are in-place metadata changes

Changing expiration does not require content re-ingestion. Jack clarified that an expiry commit changes title configuration / xCloud metadata; content metadata is stored separately except for the large ID linkage. *(InternSync4 — Jack Heuberger ~23:02)*

Therefore:

- Changing expiry should update existing title metadata in place.
- Re-ingestion is for new content versions, not date-only changes.
- Deletion/tombstone behavior is a separate lifecycle concern; see [`../FuturePlans/delete-tombstone-lifecycle.md`](../FuturePlans/delete-tombstone-lifecycle.md).

## UX enforcement

Anthony said the cap should also be enforced in the UX. The Partner Center GPX branch currently caps cloud-streaming end date to no more than 7 days after start, which is stale against the 30-day decision. *(InternSync4 — Anthony Keller ~18:00; Repos/Xbox.Gpx.PartnerCenter.Client.md)*

Current stale implementation references:

- Backend: `XCloudPlaytestTitleIngestionBuilder` clamps expiration to `DateTime.UtcNow + 7 days` in [`../Repos/Xbox.Xbet.Service.md`](../Repos/Xbox.Xbet.Service.md) / [XBET PR 15834601](../PRProgress/07-XBET-15834601-playtest-ingestion-payload-builder.md).
- UX: GPX branch `t-melanichen/playtest-streaming-enable-flag` validates no more than 7 days after start in [`../Repos/Xbox.Gpx.PartnerCenter.Client.md`](../Repos/Xbox.Gpx.PartnerCenter.Client.md).

## Sources

- `Transcripts/InternSync4.docx`
- [`../FuturePlans/expiration-cap-30-days.md`](../FuturePlans/expiration-cap-30-days.md)
- [`../Repos/Xbox.Xbet.Service.md`](../Repos/Xbox.Xbet.Service.md)
- [`../Repos/Xbox.Gpx.PartnerCenter.Client.md`](../Repos/Xbox.Gpx.PartnerCenter.Client.md)
- [`../PRProgress/07-XBET-15834601-playtest-ingestion-payload-builder.md`](../PRProgress/07-XBET-15834601-playtest-ingestion-payload-builder.md)
- [`../FuturePlans/delete-tombstone-lifecycle.md`](../FuturePlans/delete-tombstone-lifecycle.md)
