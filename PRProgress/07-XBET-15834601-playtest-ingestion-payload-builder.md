# [XBET] PR 15834601 — Playtest Ingestion Payload Builder

- **Pull Request:** 15834601
- **Repo:** Xbox.Xbet.Service (Xbox)
- **Source branch:** `t-melanichen/playtest-ingestion-payload-builder` → `main`
- **Status:** Draft
- **Opened:** 2026-06-09  |  **Closed:** —
- **Link:** https://microsoft.visualstudio.com/Xbox/_git/Xbox.Xbet.Service/pullrequest/15834601

## Summary
Adds the xPlaytest-side payload builder and contract types that enable streaming-enabled playtest
ingestion into the xCloud pipeline via services.contentingestion.
> **Note (2026-06-18):** The 7-day clamp described below is superseded by the 30-day cap decided in InternSync4; forward work is tracked in [`FuturePlans/expiration-cap-30-days.md`](../FuturePlans/expiration-cap-30-days.md).

- `PlaytestIngestionPayloadBuilder.cs`: builds and validates `PlaytestIngestionJobParameters` from the
  playtest publish state — offering creation with DNA-group gating, 7-day expiration clamping, and
  StoreAsset configuration with Xbox Live title-id requirements.
- `PlaytestIngestionJobParameters.cs`: JSON-wire-compatible DTO contract (partner id, DNA groups,
  StoreAsset, expiration time).
- `PlaytestIngestionPayloadBuilderTests.cs`: unit tests for validation, expiration clamping, required
  field enforcement, and PC-specific requirements (PackageFamilyName, AumID).
