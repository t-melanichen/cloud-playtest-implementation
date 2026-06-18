# xCloud vs xPlaytest vs xPackage

**Why it matters:** Most implementation confusion comes from treating xPackage, xPlaytest, and xCloud as peers. They are different layers in one publish-to-streaming flow.

## Comparison

| Layer | What it is | Code home | Main responsibility |
|---|---|---|---|
| xPackage | Publish-workflow engine | `Xbox.Xbet.Service`, under `src/XPackage/XPackageWorkflow/...` | Runs the state-machine workflow, including `XPackagePlaytestPublishWorkflow`, Start*/Poll* states, retries, and job status transitions. |
| xPlaytest | Playtest domain/business logic | `Xbox.Xbet.Service`, under `src/PlayTest/...` plus Playtest publish workflow integration | Defines what a playtest is, resolves required domain data, builds the xCloud ingestion payload, and supplies fields like Xbox Live Title ID. |
| xCloud | Streaming platform | Separate xCloud repos such as [`services.contentingestion`](../Repos/services.contentingestion.md), `services.serviceapigateway`, PC Orchestrator, content-targets, distribution, allocator | Receives ingestion requests, creates/configures streaming-side title/package state, attaches content to offerings, installs content, and reports readiness. |

## Common confusion

xPackage and xPlaytest both live in [`Xbox.Xbet.Service`](../Repos/Xbox.Xbet.Service.md), often called "xbet" in planning notes. xPackage is the workflow engine; xPlaytest is the business/domain layer being published. xCloud is separate: it is the Green/streaming platform surface called through SAGE and content ingestion. *(Repos/Xbox.Xbet.Service.md; Repos/services.contentingestion.md; FuturePlans/s2s-cross-tenant-call.md)*

## End-to-end flow

1. A creator publishes a Playtest package.
2. `XPackagePlaytestPublishWorkflow` drives the xPackage publish state machine.
3. xPlaytest code gathers playtest/package data, resolves required IDs such as `StoreAsset.XboxTitleId`, and builds the `XCloudPlaytestTitleIngestionBuilder` payload. The nonzero Xbox Live Title ID requirement is tracked in [`../Blockers/xbox-live-title-id.md`](../Blockers/xbox-live-title-id.md).
4. xPackage calls xCloud through SAGE: xPackage → `services.serviceapigateway` → [`services.contentingestion`](../Repos/services.contentingestion.md). The cross-tenant S2S work is tracked in [`../FuturePlans/s2s-cross-tenant-call.md`](../FuturePlans/s2s-cross-tenant-call.md) and [`../Blockers/cross-tenant-s2s.md`](../Blockers/cross-tenant-s2s.md).
5. xCloud's `PlaytestTitleIngestionWorkflow` validates the request, ingests the asset/package/version, configures the playtest title/offering state, then readiness polling decides when xPackage can surface streaming-ready status. *(services.contentingestion — `PlaytestTitleIngestionWorkflow`; Xbox.Xbet.Service — `XCloudPlaytestTitleIngestionBuilder`)*

## Sources

- [`../Repos/README.md`](../Repos/README.md)
- [`../Repos/Xbox.Xbet.Service.md`](../Repos/Xbox.Xbet.Service.md)
- [`../Repos/services.contentingestion.md`](../Repos/services.contentingestion.md)
- [`../FuturePlans/s2s-cross-tenant-call.md`](../FuturePlans/s2s-cross-tenant-call.md)
- [`../Blockers/xbox-live-title-id.md`](../Blockers/xbox-live-title-id.md)
- [`../Blockers/cross-tenant-s2s.md`](../Blockers/cross-tenant-s2s.md)
