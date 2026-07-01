# [XBET] PR 15834601 — Playtest Ingestion Payload Builder

- **Pull Request:** 15834601
- **Repo:** Xbox.Xbet.Service (Xbox)
- **Source branch:** `t-melanichen/playtest-ingestion-payload-builder` → `main`
- **Status:** Merged (Completed)
- **Opened:** 2026-06-09  |  **Closed:** 2026-07-01
- **Merge commit:** 9b0e1c51e7f14213192a24434935b122bde67897
- **Link:** https://microsoft.visualstudio.com/Xbox/_git/Xbox.Xbet.Service/pullrequest/15834601

## Summary
Adds the xPlaytest-side payload builder, cross-tenant S2S client, and publish-workflow states that ingest a
streaming-enabled playtest's title into the xCloud pipeline via services.contentingestion (Green → SAGE → CTIN).
Streaming is opt-in (`EnableStreaming`) and **non-blocking** — a streaming failure never fails the download publish.
Gated to the pilot seller `65050620`.
> **Note (2026-06-18):** The 7-day clamp is superseded by the 30-day cap decided in InternSync4; forward work is tracked in [`FuturePlans/expiration-cap-30-days.md`](../FuturePlans/expiration-cap-30-days.md). Code still clamps 7 days.

- `StreamingPlaytestTitleIngestionBuilder.cs` (renamed from `XCloudPlaytestTitleIngestionBuilder`): builds and
  validates the receiver's `PlaytestTitleIngestion.JobParameters` from the publish job params + state —
  per-market-group servicing content id, deterministic market-group selection, retail-only sandbox, PC platform
  (persisted as `Id`), 7-day expiration clamp, required Name / optional Description, empty `ParentProductIds`.
- `XCloudPlaytestIngestionServiceClient.cs` + `XCloudPlaytestIngestionS2SAuthHelperFactory.cs`: POSTs to SAGE with a
  cross-tenant (MSFTGreen) S2S token; `IS2SAuthHelper` injected as a keyed singleton via `[FromKeyedServices]`.
- `XPackagePlaytestPublishWorkflow.cs`: new `SchedulingStreamingIngestionJob` + `PollingStreamingIngestionJob`
  states; `StreamingParameters`-null invariant fails loudly outside the non-blocking catch; re-schedule guarded on the
  persisted job id. `PlaytestName`/`PlaytestDescription` carried on the job params (no mid-workflow reload).
- `PlaytestEndDateMustBeInFutureRule.cs`: synchronous `IPlaytestRule` on Publish; structured `PlaytestEndDateNotInFuture`
  (mirrored in ProductConfigurationFD `PlaytestErrorCodes` + `PlaytestErrorMapper`); applies to all publishes.
- `PlaytestBusinessLogic.cs`: resolves the Xbox Live title id from XORc at enqueue (`ResolveXboxLiveTitleIdAsync`),
  pilot-seller gate (`IsStreamingEnabled`), builds `PlaytestStreamingParameters`.
- Pinned `Azure.Identity` 1.21.0 (avoids a CS0433 credential-type collision once the GSSV contracts package pulls
  Azure.Core 1.57.0).

## Post-merge
- **ADO:** delivered tasks 62521498/500/501/504/505/507/508 → Completed; deliverable **PT1** (62492594) → Completed;
  **PT4** (62492606) kept Started (E2E validation 62521509 + deferred follow-ups remain).
- **Follow-ups (pre-merge rubber-duck):** [`FuturePlans/xbet-15834601-rubber-duck-followups.md`](../FuturePlans/xbet-15834601-rubber-duck-followups.md)
  — transient-XORc non-blocking, poll-timeout basis, crash-safe scheduling, multi-package selection, extend `Validate`.
- **New work items:** localization 62926053 (`PlaytestLocalization`); end-date-rule generalization 62908755.
