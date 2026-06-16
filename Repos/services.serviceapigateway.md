# Repo: services.serviceapigateway

**Role:** SAGE gateway — proxies playtest ingestion calls cross-tenant from Green to `services.contentingestion` in Corp, using auth pass-through so the caller token reaches contentingestion unchanged.

## Changes made (per branch/PR)

### Base used
- Git base selected: `origin/main`.

### Branch: `t-melanichen/playtest-ingestion-gateway-route`
- Remote/tracking: `origin/t-melanichen/playtest-ingestion-gateway-route` contains local commit.
- Log from base: `71cb531 Register Playtest ingestion proxy routes for services.contentingestion`.
- Merge-base: `6c421becba5a9cd31ac5ae334b7d52bedf9f0ac4`.
- Diff stat: `src/Product/ServiceApiGateway/appsettings.xcloud.json | 33 ++++++++++++++++++++++` (1 file changed, 33 insertions).
- Added a `playtest` service route in `appsettings.xcloud.json`:
  - `ServiceRouteName`: `playtest`
  - `Alias`: `ctin`
  - `Version`: `v3`
  - `ServiceBaseUri`: `http://contentingestion-svc.contentingestion`
  - `POST /v3/playtest/playtestingestion` -> backend `POST /v3/workflows/playtestingestion`
  - `GET /v3/playtest/playtestingestion/{jobId}` -> backend `GET /v3/workflows/playtestingestion/{jobId}`
  - Restricted SAGE-side to xPlaytest SPI `d60e3360-830b-4a09-b4bb-0f759ca83e06` and MSI `97a28a30-87b4-45e9-a6c6-c23a183a72ba` via `AuthorizedClientAppIds`.
- This was the earlier route-registration version. It did not set `AuthPassThroughEnabled` on the new playtest APIs.

### Branch / PR source: `t-melanichen/sage-playtest-ingestion-routes`
- Remote/tracking: current local branch tracks `origin/t-melanichen/sage-playtest-ingestion-routes`; remote contains local head `e3ba9fb`.
- Log from base:
  - `e3ba9fb Use auth pass-through on SAGE playtest ingestion route`
  - `dc9de24 Update playtest proxy routes to playtesttitleingestion endpoints`
  - `36e1c34 Register Playtest ingestion proxy routes for services.contentingestion`
- Merge-base: `59dd9d2a3c531e06e46eb2bf2939a639442f5725`.
- Diff stat: `src/Product/ServiceApiGateway/appsettings.xcloud.json | 32 ++++++++++++++++++++++` (1 file changed, 32 insertions).
- Final pushed route shape in `appsettings.xcloud.json`:
  - `ServiceRouteName`: `playtest`
  - `Alias`: `ctin` (the contentingestion service's established alias in SAGE's ServiceIdentitySettings; under pass-through SAGE does not mint a backend token, so the alias is informational but matches the real service)
  - `Version`: `v3`
  - `ServiceBaseUri`: `http://contentingestion-svc.contentingestion`
  - `POST /v3/playtest/playtesttitleingestion` -> backend `POST /v3/workflows/playtesttitleingestion`
  - `GET /v3/playtest/playtesttitleingestion/{jobId}` -> backend `GET /v3/workflows/playtesttitleingestion/{jobId}`
  - Both APIs set `"AuthPassThroughEnabled": true`.
  - Comment documents that xPackage runs in MSFTGreen, acquires a token for contentingestion's Green app registration, and SAGE forwards that token unchanged; contentingestion enforces auth and authorizes xPackage app ids.
- Relationship between branches: `sage-playtest-ingestion-routes` supersedes `playtest-ingestion-gateway-route`. The older branch registered the initial `playtestingestion` paths with SAGE-side `AuthorizedClientAppIds`; the PR branch renamed to `playtesttitleingestion` and replaced SAGE auth/minting with `AuthPassThroughEnabled: true` on both POST and GET. The branches are not a simple fast-forward pair because they were based on different `origin/main` points, but the PR branch carries the intended final SAGE change.

### PR cross-reference
Quoted PR progress record (`PRProgress\06-SAGE-15829639-register-playtest-ingestion-routes.md`):
- `# [SAGE] PR 15829639 — Register Playtest ingestion proxy routes for services.contentingestion`
- `Pull Request: 15829639`
- `Source branch: t-melanichen/sage-playtest-ingestion-routes -> main`
- `Status: Draft`
- Summary quoted routes still name the older `playtestingestion` contract, but the pushed branch now contains `playtesttitleingestion` and `AuthPassThroughEnabled: true`.
- The progress note says the auth-pass-through fix was "local, not pushed"; git output now shows that commit `e3ba9fb Use auth pass-through on SAGE playtest ingestion route` is pushed to `origin/t-melanichen/sage-playtest-ingestion-routes`.

## Planned / remaining changes

- Cross-tenant S2S / SAGE integration tasks now consolidated in [`FuturePlans/s2s-cross-tenant-call.md`](../FuturePlans/s2s-cross-tenant-call.md), including PR 15829639 deployment, auth pass-through validation, xPackage token acquisition, and long-term PME follow-up.
- Delete/tombstone lifecycle remains tracked in [`FuturePlans/delete-tombstone-lifecycle.md`](../FuturePlans/delete-tombstone-lifecycle.md); any shared SAGE integration assumptions should point back to the consolidated S2S deliverable.

## References

- Git repo: `C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\services.serviceapigateway`
- Changed file: `src/Product/ServiceApiGateway/appsettings.xcloud.json`
- Branches inspected: `t-melanichen/playtest-ingestion-gateway-route`, `t-melanichen/sage-playtest-ingestion-routes`
- PR progress: `C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\cloud-playtest-implementation\PRProgress\06-SAGE-15829639-register-playtest-ingestion-routes.md`
- Consolidated S2S deliverable: `C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\cloud-playtest-implementation\FuturePlans\s2s-cross-tenant-call.md`
- Future plan: `C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\cloud-playtest-implementation\FuturePlans\delete-tombstone-lifecycle.md`
