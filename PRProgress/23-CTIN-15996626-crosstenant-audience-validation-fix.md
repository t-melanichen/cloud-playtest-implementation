# [CTIN] PR 15996626 — Accept bare-GUID audience for cross-tenant v1.0 tokens

- **Pull Request:** 15996626
- **Repo:** services.contentingestion (Xbox.Streaming)
- **Source branch:** `t-melanichen/fix-crosstenant-audience-validation` → `main`
- **Status:** Active
- **Opened:** 2026-06-24
- **Link:** https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.contentingestion/pullrequest/15996626

## Summary
Fixes a 401 (`"The audience '(null)' is invalid"`) that blocked the playtest title ingestion path
(xPackage → SAGE → contentingestion) after the cross-tenant auth from PR 15715445 was wired up.

Root cause: the caller (xPackage, in MSFTGreen) acquires its S2S token for contentingestion's Green app
registration, but that app has **no `api://` Application ID URI** (requesting `api://{appId}/.default` returns
`AADSTS500011`). So the only mintable token is a **v1.0** token whose `aud` is the **bare app-id GUID**.
`CrossTenantBearer` (registered via `AddMicrosoftIdentityWebApi` with empty `jwtOptions`) uses
Microsoft.Identity.Web's default audience validation, which for a **v1.0** token expects `aud =
api://{ClientId}` — so it rejected the bare-GUID audience. (`appid=null` in logs is the cascade after
authentication fails.)

- `ContentCatalog.Ingestion.Service/Startup.cs` (`ConfigureCrossTenantAuth`): added a
  `PostConfigure<JwtBearerOptions>(AuthSchemeExtension.CrossTenantBearer, …)` that overrides the scheme's
  `AudienceValidator` to accept the configured `MultiTenantAuthConfig.AppId` (bare GUID) directly. Runs after
  Microsoft.Identity.Web's own setup so it wins. Issuer/tenant validation and the `CrossTenantS2S`
  authorization allow-list (`AuthorizedClientIds`) are unchanged — auth is not weakened.

## Context
- Builds on / fixes **PR 15715445** (Lakshey Hooda — Corp↔Green dual bearer schemes + `CrossTenantS2S`
  policy) and **PR 15905881** (#17 — gates the V3 playtest ingestion endpoints with that policy).
- Caller side is the xPackage payload builder + SAGE client in **PR 15834601** (#10).
- No-code alternative considered: set the Green app registration `accessTokenAcceptedVersion = 2` so tokens
  issue as v2.0 (bare-GUID `aud` accepted by default). This PR is the code-side fix needing no AAD change.
- Reviewer: Lakshey Hooda (added as required reviewer).

## Validation
- `ContentCatalog.Ingestion.Service` builds clean locally (0 warnings / 0 errors; analyzers + StyleCop).
- Deployed to **test** and validated end-to-end from a local xPackage container: the 401 is gone (empty body
  now returns `400 InvalidPlaytestId`, i.e. past auth), and a real playtest title ingestion payload was
  accepted and the contentingestion ingestion workflow ran to `IsSuccess: true` ("PC title ingested").
- **Not** validated: the full publish state machine (upstream producer / PlayTest service / XORc /
  XProductAggregator are not in the local docker env). The build-StoreAsset + SAGE slice was exercised
  directly. The true end-to-end publish flow can be run once PR 15834601 reaches prod.
