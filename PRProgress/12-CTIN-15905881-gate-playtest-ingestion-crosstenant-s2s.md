# [CTIN] PR 15905881 — Gate playtest title ingestion endpoints with CrossTenantS2S policy

- **Pull Request:** 15905881
- **Repo:** services.contentingestion (Xbox.Streaming)
- **Source branch:** `t-melanichen/playtest-ingestion-crosstenant-authorize` → `main`
- **Status:** Merged
- **Opened:** 2026-06-16  |  **Closed:** 2026-06-16
- **Merge commit:** `52fab532615dc2065c6c6785222ef4088d940f42`
- **Link:** https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.contentingestion/pullrequest/15905881

## Summary
Activates the cross-tenant S2S authorization that PR 15715445 added (which was a no-op until the policy
attribute is applied to an endpoint). Gates the two V3 playtest title ingestion endpoints with the
`CrossTenantS2S` policy so the Content Catalog Ingestion Service authorizes the forwarded xPackage caller
token against `MultiTenantAuthConfig.AuthorizedClientIds`.

- `WorkflowsControllerV3.cs`: Added `[Authorize(AuthPolicyExtension.CrossTenantS2S)]` to both
  `POST /v3/workflows/playtesttitleingestion` and `GET /v3/workflows/playtesttitleingestion/{jobId}`,
  plus the `using Microsoft.AspNetCore.Authorization;` import. Documents the auth-pass-through flow:
  xPackage (in MSFTGreen) acquires a token for this service's Green app registration and reaches it
  through SAGE, which forwards the caller token unchanged; the cross-tenant S2S policy authorizes that
  caller against `MultiTenantAuthConfig.AuthorizedClientIds`.
- `AuthPolicyExtension.cs`: Changed `CrossTenantS2S` from `public static readonly string` to
  `public const string`. Attribute arguments must be compile-time constants, so
  `[Authorize(AuthPolicyExtension.CrossTenantS2S)]` fails against a `static readonly` field.

## Context
- Builds on the merged cross-tenant auth infrastructure in **PR 15715445** (Corp↔Green dual bearer
  schemes + `CrossTenantS2S` policy).
- Receiver side of the S2S call documented in [`FuturePlans/s2s-cross-tenant-call.md`](../FuturePlans/s2s-cross-tenant-call.md);
  the SAGE pass-through route is **PR 15829639** (alias `ctin`, path key `playtest`).

## Open follow-up
- The caller side (xPackage POST to SAGE + cross-tenant token acquisition) is still unimplemented —
  see [`FuturePlans/s2s-cross-tenant-call.md`](../FuturePlans/s2s-cross-tenant-call.md) sections B/C and
  ADO work items 62745766 / 62492628.
