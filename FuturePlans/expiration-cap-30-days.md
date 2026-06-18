# Future plan: Streaming expiration cap — 30 days

**Why it matters:** InternSync4 raised the streaming playtest max expiration cap from 7 days to 30 days. The backend clamp in Xbox.Xbet.Service and the Partner Center creator UX currently hardcode 7 days, so both must move to 30 days. The cap is a title-level field, not an offering field, and should be enforced both by the authoritative backend guard and by the friendly creator UX.

## Current understanding (InternSync4 — 2026-06-18)

- Streaming playtest **max expiration cap = 30 days**. Jack Heuberger said the old "magic one week" limit was fine for now, "or like 30 days, honestly, would also be fine"; Anthony Keller and Emma Park agreed on 30 days.
- The rationale is xCloud capacity and storage hygiene: Xbox titles pre-install on a fixed server pool and hold region-constrained storage until they expire/uninstall. Jack called out that region matters because "Japan is a lot more constrained than like West US 3."
- The expiration cap belongs on the **individual title**, not the offering. Jack: "we would configure that on the individual title and not the offering."
- The cap should also be enforced in the UX. Anthony: "if there's a cap, maybe we want to cap in the UX as well."
- Changing an existing playtest's expiry is a title-configuration / xCloud metadata update, **not** a content re-ingest. Jack: "the commit would just be for like changing the expiry ... that's just like title configuration xCloud metadata stuff."

## Steps

- [ ] **Backend:** Change the clamp in `XCloudPlaytestTitleIngestionBuilder` from `DateTime.UtcNow + 7 days` to `DateTime.UtcNow + 30 days` in Xbox.Xbet.Service (PR 15834601 area). Keep the "expiration must be in the future" validation.
- [ ] **UX:** Change the Partner Center cap from "≤7 days after start" to "≤30 days after start" in `PlaytestCloudStreamingField.tsx`, `playtestFormSchema.ts` (`superRefine`), and the related localized error strings on branch `t-melanichen/playtest-streaming-enable-flag`. Still disallow `noEndDate` for streaming.
- [ ] Keep the cap a single source of truth where possible. The backend clamp is the authoritative guard; the UX cap is the friendly front line.
- [ ] Confirm the value with Kush in the planned follow-up (Melanie's action item from InternSync4) before shipping, in case the number is revisited.
- [ ] Validate that an expiration >30 days is rejected/clamped both in the UI and on the server, and that expiry sits on the title, not the offering.
- [ ] Note that changing an existing playtest's expiry is an in-place title-config / metadata update, **not** a content re-ingest, per Jack; the update path should not re-run asset ingestion.

## Owners

Melanie Chen (xPlaytest backend + Partner Center UI) · Jack Heuberger / Timi Bolaji (xCloud title config) · Kush (final number).

## References / Sources

- `Transcripts/InternSync4.docx`
- [`explanations/expiration-cap-and-storage.md`](../explanations/expiration-cap-and-storage.md)
- [`explanations/future-start-dates-and-provisioning.md`](../explanations/future-start-dates-and-provisioning.md)
- [`Repos/Xbox.Xbet.Service.md`](../Repos/Xbox.Xbet.Service.md)
- [`Repos/Xbox.Gpx.PartnerCenter.Client.md`](../Repos/Xbox.Gpx.PartnerCenter.Client.md)
- [`PRProgress/07-XBET-15834601-playtest-ingestion-payload-builder.md`](../PRProgress/07-XBET-15834601-playtest-ingestion-payload-builder.md)
