# Explanations

Conceptual companion docs for the Instantly Shareable Playtest project: how xPlaytest publishes into xCloud, where xPackage fits, and which platform differences drive the implementation plan.

## Index

| Doc | Description |
|---|---|
| **▶ [End-to-end flow & xCloud ingestion deep dive](./end-to-end-flow-and-xcloud-ingestion.md)** | **Start here.** Full creator→tester walkthrough, the role of every repo, and a stage-by-stage dissection of `PlaytestTitleIngestionWorkflow`. |
| [Transcript decisions ledger](./transcript-decisions.md) | Key design decisions/considerations distilled from the 9 cross-team meeting transcripts, each linked to the doc that reflects it. |
| [InternSync4 summary](./internsync4-summary.md) | Summarizes the 2026-06-18 meeting decisions on expiration, future dates, title-level configuration, and follow-ups. |
| [xCloud vs xPlaytest vs xPackage](./xcloud-xplaytest-xpackage.md) | Defines the three layers, where each lives in code, and the end-to-end xPackage → xPlaytest → xCloud flow. |
| [Ingestion creates new things](./ingestion-creates-new-things.md) | Explains how ingestion mints per-playtest title IDs, attaches content to offerings, triggers installs, and handles PC version hashes. |
| [Future start dates and provisioning](./future-start-dates-and-provisioning.md) | Explains why future start dates do not require go-live trigger logic: provisioning starts before player-facing availability. |
| [Expiration cap and storage](./expiration-cap-and-storage.md) | Explains the storage reason for the 30-day cap and why expiry changes are title metadata updates, not content re-ingests. |
| [Handling Xbox vs PC differences](./handling-xbox-vs-pc-differences.md) | Actionable guide for implementing the known platform differences: expiration, dates, polling, future starts, and metadata updates. |
| **▶ [XBET PR 15834601 — design decisions](./xbet-15834601-design-decisions.md)** | The settled streaming opt-in / workflow-purity decisions for PR 15834601, the rationale, and how they address Anthony's & Brian's review feedback. Reflects the final as-merged shape. |
| [XBET PR 15834601 — review responses](./xbet-15834601-review-responses.md) | Per-comment record for the PR 15834601 review: the fix (with commit) and a paste-ready reply for every active thread. |

## Relationship to the rest of the repo

- [`../Blockers/`](../Blockers/) tracks open problems and decisions still blocking the v1 flow, such as [Xbox Live Title ID resolution](../Blockers/xbox-live-title-id.md), [PC install readiness polling](../Blockers/pc-install-readiness-poll.md), and [cross-tenant S2S](../Blockers/cross-tenant-s2s.md).
- [`../FuturePlans/`](../FuturePlans/) tracks concrete forward work, including [the 30-day expiration cap](../FuturePlans/expiration-cap-30-days.md), [PC polling implementation](../FuturePlans/pc-install-readiness-polling-implementation.md), [S2S calls](../FuturePlans/s2s-cross-tenant-call.md), and related lifecycle work.
- [`../Repos/`](../Repos/README.md) is the per-repo change log for branches and PRs across xCloud, xPlaytest, Partner Center, and player surfaces.
- [`../PRProgress/`](../PRProgress/) remains the live PR-status ledger, including [XBET PR 15834601](../PRProgress/07-XBET-15834601-playtest-ingestion-payload-builder.md).
- [`../Documentation/`](../Documentation/) holds as-built spec deltas, including [PR 15834601 spec deltas](../Documentation/xbet-15834601-spec-deltas.md).

## Sources

- `Transcripts/InternSync4.docx`
- `Transcripts/XCloudIngestion.docx`
- `Transcripts/InternSync3.docx`
- [`../Repos/README.md`](../Repos/README.md)
- [`../Repos/services.contentingestion.md`](../Repos/services.contentingestion.md)
- [`../Repos/Xbox.Xbet.Service.md`](../Repos/Xbox.Xbet.Service.md)
- [`../Repos/Xbox.Gpx.PartnerCenter.Client.md`](../Repos/Xbox.Gpx.PartnerCenter.Client.md)
