# InternSync4 summary — 2026-06-18

**Why it matters:** InternSync4 resolved the main conceptual questions around streaming playtest expiration, future start dates, and whether changes require content re-ingestion.

## Meeting scope

Participants were Melanie Chen, Anthony Keller, Jack Heuberger, Timi Bolaji, and Emma Park. The meeting focused on the maximum expiration date for streaming playtests, how future start dates interact with xCloud provisioning, and where date configuration belongs. *(InternSync4 — meeting summary; Jack Heuberger, Timi Bolaji, Anthony Keller, Emma Park)*

## Decisions

- **Use a 30-day expiration cap for streaming playtests.** The prior implementation and UI work used a 7-day number, but Jack said one week was acceptable and "30 days ... would also be fine"; Anthony and Emma agreed on 30 days. Region constraints still matter because capacity differs by geography, for example Japan versus West US 3. *(InternSync4 — Jack Heuberger ~23:54)*
- **Configure dates on the title, not the offering.** Jack clarified that availability/expiration should be configured "on the individual title and not the offering." Timi clarified that xCloud creates one title construct per playtest, so each playtest has a distinct title ID. *(InternSync4 — Jack Heuberger ~14:43; Timi Bolaji ~15:42)*
- **Provisioning is decoupled from go-live.** For future start dates, xCloud can install before the live date so capacity exists when the date hits. The start date gates player-facing availability, not installation. *(InternSync4 — Jack Heuberger ~16:30; Timi Bolaji ~16:59)*
- **Changing expiration is metadata, not content re-ingest.** Jack clarified that changing expiry is title-configuration / xCloud metadata, while content metadata is stored separately. The existing title can be updated in place. *(InternSync4 — Jack Heuberger ~23:02)*
- **The UX should enforce the same cap.** Anthony called out that if the platform has a cap, Partner Center should cap the user experience as well. *(InternSync4 — Anthony Keller ~18:00)*
- **Follow-up remains with Kush.** Melanie planned a follow-up meeting with Kush for remaining questions. *(InternSync4 — meeting close / follow-up)*

## Implementation implications

- Backend and Partner Center still reference 7 days in current work: `XCloudPlaytestTitleIngestionBuilder` clamps to `DateTime.UtcNow + 7 days`, and the GPX branch caps the cloud-streaming end date to no more than 7 days after start. Those are stale against the 30-day decision and are tracked in [`../FuturePlans/expiration-cap-30-days.md`](../FuturePlans/expiration-cap-30-days.md). See also [`../Repos/Xbox.Xbet.Service.md`](../Repos/Xbox.Xbet.Service.md), [`../Repos/Xbox.Gpx.PartnerCenter.Client.md`](../Repos/Xbox.Gpx.PartnerCenter.Client.md), and [XBET PR 15834601](../PRProgress/07-XBET-15834601-playtest-ingestion-payload-builder.md).
- Future start dates do not need a new wake-up job or go-live trigger in xPackage. xCloud's title configuration and install logic can handle the future availability window while provisioning happens earlier.

## Sources

- `Transcripts/InternSync4.docx`
- [`../FuturePlans/expiration-cap-30-days.md`](../FuturePlans/expiration-cap-30-days.md)
- [`../Repos/Xbox.Xbet.Service.md`](../Repos/Xbox.Xbet.Service.md)
- [`../Repos/Xbox.Gpx.PartnerCenter.Client.md`](../Repos/Xbox.Gpx.PartnerCenter.Client.md)
- [`../PRProgress/07-XBET-15834601-playtest-ingestion-payload-builder.md`](../PRProgress/07-XBET-15834601-playtest-ingestion-payload-builder.md)
