# Future start dates and provisioning

**Why it matters:** A future start date should not create a new xPackage "wake up and provision" path. xCloud can provision before the title becomes player-visible.

## Dates live on the title

Jack clarified that future availability and expiry should be configured on the individual title, not on the offering. Timi clarified that the title construct is one per playtest, so each playtest has a distinct title ID and can carry its own dates. *(InternSync4 — Jack Heuberger ~14:43; Timi Bolaji ~15:42)*

## Provisioning is decoupled from go-live

Anthony asked whether provisioning happens when the live date arrives. Jack answered no: xCloud installs beforehand so that when the date hits, titles are already available. Timi added that current logic starts installs as long as the title is not expired, even if the start date is in the future. *(InternSync4 — Anthony Keller / Jack Heuberger ~16:30; Timi Bolaji ~16:59)*

The implication is simple: xPackage should send the title/date metadata, then xCloud provisioning can begin immediately. The future start date gates player-facing availability; it does not need a separate go-live trigger in the publish workflow.

## Minimal install set

For Xbox, xCloud installs a minimal number of copies before launch. Timi described the default as region-dependent and roughly the smaller of 60 servers or about 2–5% of available servers. For playtests, xCloud can dial the minimum lower if needed. *(InternSync4 — Timi Bolaji ~16:59)*

This is capacity-sensitive. Jack called out that regions differ materially: Japan is much more constrained than West US 3. *(InternSync4 — Jack Heuberger ~23:54)* Region-specific routing/configuration work is tracked in [`../FuturePlans/region-configuration-routing.md`](../FuturePlans/region-configuration-routing.md).

## What xPackage should not add

- Do not add a separate "wait until start date, then call xCloud" state.
- Do not model the future start date as an offering-level setting.
- Do not re-ingest content just because a start date changes; date fields are title configuration unless the content version itself changed.

Readiness still has platform-specific behavior: Xbox can use allocator-style readiness, while PC needs PC Orchestrator/version-hash polling or an explicit MVP decision to skip PC polling. See [`../Blockers/pc-install-readiness-poll.md`](../Blockers/pc-install-readiness-poll.md) and [`../FuturePlans/pc-install-readiness-polling-implementation.md`](../FuturePlans/pc-install-readiness-polling-implementation.md).

## Sources

- `Transcripts/InternSync4.docx`
- `Transcripts/XCloudIngestion.docx`
- [`../Blockers/pc-install-readiness-poll.md`](../Blockers/pc-install-readiness-poll.md)
- [`../FuturePlans/pc-install-readiness-polling-implementation.md`](../FuturePlans/pc-install-readiness-polling-implementation.md)
- [`../FuturePlans/region-configuration-routing.md`](../FuturePlans/region-configuration-routing.md)
