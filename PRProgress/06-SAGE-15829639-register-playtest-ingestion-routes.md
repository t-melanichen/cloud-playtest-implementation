# [SAGE] PR 15829639 — Register Playtest ingestion proxy routes for services.contentingestion

- **Pull Request:** 15829639
- **Repo:** services.serviceapigateway (Xbox.Streaming)
- **Source branch:** `t-melanichen/sage-playtest-ingestion-routes` → `main`
- **Status:** Merged
- **Opened:** 2026-06-09  |  **Closed:** 2026-07-01  |  **Merge commit:** d4b0808a42
- **Link:** https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.serviceapigateway/pullrequest/15829639

## Summary
Registers the SAGE gateway proxy routes for the V3 playtest ingestion workflow:
- `POST /v3/playtest/playtestingestion` → `WorkflowsControllerV3.SchedulePlaytestIngestionJobAsync`
- `GET  /v3/playtest/playtestingestion/{jobId}` → `WorkflowsControllerV3.GetPlaytestIngestionJobStatusAsync`

The backend lives in services.contentingestion (`BackendPathPrefix v3/workflows`). Routes are restricted
to the xPlaytest SPI and MSI client app ids.

## Cross-tenant ingress (Green → Corp)
The Playtest Service / Partner Center workflow (xPackage) runs in **MSFTGreen**; SAGE and
contentingestion (CTIN) run in **Corp**. CTIN is registered as a multi-tenant app **in the Green
tenant** (`MultiTenantAuthConfig.AppId` = `xcloud-contentingestion-<env>` Green app reg) and validates
incoming Green tokens via Lakshey's cross-tenant bearer scheme, authorizing the **xPackage** client id.

Because CTIN authorizes the xPackage identity directly, the xPackage token must reach CTIN **unchanged**.
SAGE therefore uses **pass-through** for the playtest route (`"AuthPassThroughEnabled": true`) — it does
**not** mint a backend token for the `ctin` alias. SAGE's controller gate `[Authorize("DelegatedAuth")]`
is a no-op (`RequireAssertion(context => true)` in `ServiceConfiguration.cs`), and the pass-through branch
(`ProxyController.cs:115`) forwards the request and Authorization header with no checks. Auth is enforced
entirely at CTIN.

**Fix applied (local, not pushed):** Set `"AuthPassThroughEnabled": true` on both playtest APIs in
`appsettings.xcloud.json` (replacing an earlier `UseCrossTenantAuth` attempt — that would have made SAGE
mint its own token, which breaks the Green xPackage → CTIN identity chain).

### xPackage app ids (the client CTIN authorizes)
| Env | xPackage App Id | CTIN `AuthorizedClientIds` |
|-----|-----------------|----------------------------|
| Prod | `d60e3360-830b-4a09-b4bb-0f759ca83e06` | matches (Prod) |
| Staging/Test/Int | `bf3fb5e5-6f18-40ef-b0e5-1403d2b9ac6d` | matches (Test/Int) |

## Blocker
- Alias `ctin` is **no longer required** for this route under pass-through (SAGE does not mint a token),
  but the route still proxies to `contentingestion-svc.contentingestion`.
- The xPackage caller must acquire its token with **audience = CTIN's Green app registration**
  (`893629d4` Test / `41db6237` Int / `33a17a2a` Prod), not SAGE, for CTIN's cross-tenant scheme to validate it.
