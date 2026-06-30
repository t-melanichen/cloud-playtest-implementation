# PR 15834601 — As-built spec deltas (Playtest streaming ingestion)

How the **as-merged** implementation of PR 15834601 (*Playtest Ingestion Payload Builder*) refines or
defers items from the original implementation spec
(`../Context/PlaytestImplementationSpecwithComments.pdf`; Desktop master:
*Instantly Shareable Playtest — Updated Implementation Spec (polished).docx*). The rationale lives in
[`../Explanations/xbet-15834601-design-decisions.md`](../Explanations/xbet-15834601-design-decisions.md).

| Area | As-built | Status |
|---|---|---|
| **Streaming enablement** | Explicit `EnableStreaming` flag decided in `PlaytestBusinessLogic`; interim value = pilot seller `65050620`. | **Refinement** — first-class flag, not inferred from title-id presence. Persisted flag + UX checkbox deferred (AB#62878234); ECS allowlist (AB#62684638). |
| **Title-id resolution** | Resolved at publish time via `IProductsBusinessLogic.GetXboxServicesConfigAsync`, only when `EnableStreaming`; fail-fast if not XBL-configured. | **Refinement** — moved to the API boundary (not inside the workflow); download-only publishes never call XORc. |
| **Workflow** | Pure function of inputs; no seller logic / no lookups; optional `SchedulingStreamingIngestion` → `PollingStreamingIngestion` states gated on `EnableStreaming`. | **As-built** — keeps the workflow narrow and replayable. |
| **SAGE wait model** | Download publish (SUCU / xProduct) completes first; SAGE polled on a bounded 5-min / 24-hr self-delay loop; never blocks or fails the publish; idempotent reschedule. | **Refinement** — streaming readiness decoupled from the download publish. |
| **Streaming inputs** | `PlaytestStreamingParameters` record (`XboxLiveTitleId` today; `ApplicationId` = `"App"`, `Platform` = `PC` defaults). | **As-built** — extensible container for upcoming inputs. |
| **Validation** | Synchronous `IPlaytestRule`s on Publish returning structured (UI-surfaceable) errors. | **As-built**. |
| **End-date in future** | `PlaytestEndDateMustBeInFutureRule` enforced for **all** playtests (AB#62908755). | **Broadened** — started as a streaming-only rule; now applies to every publish. |
| **Market groups** | Default / first market group taken deterministically; single servicing content id. | **Deferred** — multi-market-group (AB#62893742). |
| **Platform** | Hardcoded `ServerPlatform.PC`. | **Deferred** — derive from package format (AB#62893743); Console later. |
| **Region routing** | Not sent. | **Deferred** — AB#62907370. |
| **Expiration cap** | Builder clamps to **7 days**. | **Open** — agreed cap is **30 days** (storage / region constraints); see [`../FuturePlans/expiration-cap-30-days.md`](../FuturePlans/expiration-cap-30-days.md). |
| **Cross-tenant (Green) S2S** | Keyed-singleton confidential-client helper (xPackage cert/app, Green authority); injected via `[FromKeyedServices]`. | **As-built** — mirrors the Xkms / Mkms pattern. |
| **Partner / sandbox** | `PartnerId` = fixed `MICROSOFT`; `AllowedSandboxId` = retail (RETAIL-only, enforced at the validation gate). | **As-built**. |

## See also

- Decisions & rationale: [`../Explanations/xbet-15834601-design-decisions.md`](../Explanations/xbet-15834601-design-decisions.md)
- Per-comment review responses: [`../Explanations/xbet-15834601-review-responses.md`](../Explanations/xbet-15834601-review-responses.md)
- PR ledger: [`../PRProgress/07-XBET-15834601-playtest-ingestion-payload-builder.md`](../PRProgress/07-XBET-15834601-playtest-ingestion-payload-builder.md)
