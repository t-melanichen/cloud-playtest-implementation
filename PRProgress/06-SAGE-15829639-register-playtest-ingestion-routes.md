# [SAGE] PR 15829639 — Register Playtest ingestion proxy routes for services.contentingestion

- **Pull Request:** 15829639
- **Repo:** services.serviceapigateway (Xbox.Streaming)
- **Source branch:** `t-melanichen/sage-playtest-ingestion-routes` → `main`
- **Status:** Draft
- **Opened:** 2026-06-09  |  **Closed:** —
- **Link:** https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.serviceapigateway/pullrequest/15829639

## Summary
Registers the SAGE gateway proxy routes for the V3 playtest ingestion workflow:
- `POST /v3/playtest/playtestingestion` → `WorkflowsControllerV3.SchedulePlaytestIngestionJobAsync`
- `GET  /v3/playtest/playtestingestion/{jobId}` → `WorkflowsControllerV3.GetPlaytestIngestionJobStatusAsync`

The backend lives in services.contentingestion (`BackendPathPrefix v3/workflows`). Routes are restricted
to the xPlaytest SPI and MSI client app ids.

## Blocker
- Alias `cing` requires SRE to provision the contentingestion AppId in the K8s
  `ServiceIdentitySettings` ConfigMap before this route can be exercised.
