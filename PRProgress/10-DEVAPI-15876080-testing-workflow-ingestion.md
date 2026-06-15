# [DEVAPI] PR 15876080 — Testing workflow ingestion (Playtest Title Ingestion UI/client)

- **Pull Request:** 15876080
- **Repo:** services.devapi (Xbox.Streaming)
- **Source branch:** `t-melanichen/testing-workflow-ingestion` → `main`
- **Status:** Active (in review)
- **Opened:** 2026-06-13  |  **Closed:** —
- **Link:** https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.devapi/pullrequest/15876080

## Summary
Adds a DevApiGateway feature to trigger and monitor Playtest title ingestion jobs against the
ContentIngestion workflow API (`v3/workflows/playtesttitleingestion`).
- `Index.razor`: new Blazor page to trigger ingestion jobs and check job status via JSON input.
- `PlaytestIngestionClient.cs` / `IPlaytestIngestionClient.cs`: HTTP client for the ContentIngestion
  endpoints.
- `PlaytestIngestionProcessor.cs`: parses JSON parameters, invokes the client, and formats responses.
- `IServiceCollectionExtensions.cs`: registers the client and processor with DI, including fakes for dev.
- `appsettings.json`: configures `PlaytestIngestionClient` pointing at ContentIngestion (40s timeout).
