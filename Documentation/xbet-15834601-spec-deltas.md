# PR 15834601 — As-built spec deltas (Playtest streaming ingestion)

How the **as-merged** implementation of PR 15834601 (*Playtest Ingestion Payload Builder*) refines or
defers items from the original implementation spec
(`../Context/PlaytestImplementationSpecwithComments.pdf`; Desktop master:
*Instantly Shareable Playtest — Updated Implementation Spec (polished).docx*). The rationale lives in
[`../Explanations/xbet-15834601-design-decisions.md`](../Explanations/xbet-15834601-design-decisions.md).

| Area | As-built | Status |
|---|---|---|
| **Streaming enablement** | Explicit `EnableStreaming` flag decided in `PlaytestBusinessLogic`; interim value = pilot seller `65050620`. | **Refinement** — first-class flag, not inferred from title-id presence. Persisted flag + UX checkbox deferred (ADO#62878234); ECS allowlist (ADO#62684638). |
| **Title-id resolution** | Resolved at publish time via `IProductsBusinessLogic.GetXboxServicesConfigAsync`, only when `EnableStreaming`; fail-fast if not XBL-configured. | **Refinement** — moved to the API boundary (not inside the workflow); download-only publishes never call XORc. |
| **Workflow** | Pure function of inputs; no seller logic / no lookups; optional `SchedulingStreamingIngestion` → `PollingStreamingIngestion` states gated on `EnableStreaming`. | **As-built** — keeps the workflow narrow and replayable. |
| **SAGE wait model** | Download publish (SUCU / xProduct) completes first; SAGE polled on a bounded 5-min / 24-hr self-delay loop; never blocks or fails the publish; idempotent reschedule. | **Refinement** — streaming readiness decoupled from the download publish. |
| **Streaming inputs** | `PlaytestStreamingParameters` record (`XboxLiveTitleId` today; `ApplicationId` = `"App"`, `Platform` = `PC` defaults). | **As-built** — extensible container for upcoming inputs. |
| **Validation** | Synchronous `IPlaytestRule`s on Publish returning structured (UI-surfaceable) errors. | **As-built**. |
| **End-date in future** | `PlaytestEndDateMustBeInFutureRule` enforced for **all** playtests (ADO#62908755). | **Broadened** — started as a streaming-only rule; now applies to every publish. |
| **Market groups** | Default / first market group taken deterministically; single servicing content id. | **Deferred** — multi-market-group (ADO#62893742). |
| **Platform** | Hardcoded `ServerPlatform.PC`. | **Deferred** — derive from package format (ADO#62893743); Console later. |
| **Region routing** | Not sent. | **Deferred** — ADO#62907370. |
| **Expiration cap** | Builder clamps to **7 days**. | **Open** — agreed cap is **30 days** (storage / region constraints); see [`../FuturePlans/expiration-cap-30-days.md`](../FuturePlans/expiration-cap-30-days.md). |
| **Cross-tenant (Green) S2S** | Keyed-singleton confidential-client helper (xPackage cert/app, Green authority); injected via `[FromKeyedServices]`. | **As-built** — mirrors the Xkms / Mkms pattern. |
| **Partner / sandbox** | `PartnerId` = fixed `MICROSOFT`; `AllowedSandboxId` = retail (RETAIL-only, enforced at the validation gate). | **As-built**. |

## See also

- Decisions & rationale: [`../Explanations/xbet-15834601-design-decisions.md`](../Explanations/xbet-15834601-design-decisions.md)
- Per-comment review responses: [`../Explanations/xbet-15834601-review-responses.md`](../Explanations/xbet-15834601-review-responses.md)
- PR ledger: [`../PRProgress/07-XBET-15834601-playtest-ingestion-payload-builder.md`](../PRProgress/07-XBET-15834601-playtest-ingestion-payload-builder.md)

---

## Deployment & operational learnings (added 2026-07-02)

Things discovered while bringing the streaming publish up in **prod**. These aren't design deltas — they're
environment/operational facts the next engineer needs to reproduce or debug an E2E.

### Environment → SAGE routing (which env calls which xCloud env)
A single publish is handled by **one** Xbet instance, and that instance's `ASPNETCORE_ENVIRONMENT` (set per Helm
values file) decides the **one** SAGE host it calls — it does **not** fan out across test/int/prod.

| Xbet chart | `aspNetCoreEnvironment` | Loads | Calls SAGE host | App ids (caller / CTIN aud) |
|---|---|---|---|---|
| `staging-wus.yaml` | **Staging** | `appsettings.Staging.json` | `gssv-sage-test.xboxlive.com` (**xCloud test**) | `bf3fb5e5` / `893629d4` |
| `prod-wus2.yaml` (+ other prod-*) | **Production** (values.yaml default) | base `appsettings.json` | `gssv-sage.xboxlive.com` (**xCloud prod**) | `d60e3360` / `33a17a2a` |

- **Publishing from prod Partner Center (`partner.microsoft.com`) → the Production Xbet env → prod SAGE → prod CTIN** with **prod** app ids. `WUS2` = `prod-wus2` = Production (Staging is `staging-wus`, in *WestUS*, not WUS2).
- The `gssv-sage(.../-test)` hostnames are global endpoints; the call resolves to whichever SAGE **region** is deployed/healthy, so SAGE's own regions (eau/eus2/seau/eus) don't need to match Xbet's region.
- CTIN prod authorizes the prod caller: `appsettings.Prod.json` → `AppId 33a17a2a`, `AuthorizedClientIds:[d60e3360]` (verified). Test is `893629d4`/`[bf3fb5e5]`.

### XORc title-id is a hard prod dependency with a separate deploy path
- Streaming publish calls `IProductsBusinessLogic.GetXboxServicesConfigAsync` → **XORc**; `ResolveXboxLiveTitleIdAsync` **throws** if `TitleId is null or 0`. The TitleId field is exposed by **XORc PR 15894506**, which merged to **`develop`** (06/16), and XORc **deploys to devnet from develop/PR builds but requires a *separate* PROD deployment** (via `deployment.ini`, run/watched from a SAW; typically not done end-of-day).
- **Consequence:** even a correctly Xbox-Live-configured product returns a null TitleId in prod until XORc's prod deploy carries 15894506 → the pilot publish fails. (Confirmed root cause of the first prod publish failures; Anthony queued the prod XORc deploy on 2026-07-02.)
- Also required: the product itself (e.g. `9NPMGXTRGW9H`) must actually **have** an Xbox Live title id assigned — XORc exposing the field only helps if one exists.

### Diagnosability gap — everything looks like `PlaytestUnknown`
- The prod publish 400 surfaced as `{"code":"PlaytestUnknown","debugMessage":null}`. Root cause: **three** distinct publish throws in `QueuePublishJobAsync` all raise a generic `ServiceErrorHelper.CreateValidationError("ValidationError", …)`, which ProductConfigurationFD's mapper can't map to a specific code → falls back to `PlaytestUnknownError` **and strips the debug message**. In code order they are:
  1. **Empty market-group packages** (no package selected),
  2. **Streaming title-id gate** (no XBL TitleId — the XORc dependency above),
  3. **Private + empty flights** (no audience selected).
- **Debugging:** the real message is only in the **PlayTest service logs** (Geneva) for the PlaytestId — the UI/FD hides it. **Follow-up worth filing:** give these three throws distinct, FD-mapped error codes (and stop stripping `debugMessage`) so the creator sees *why* a publish failed.

### Prod rollout status (as of 2026-07-02 ~10:00 PT)
- **PlayTest + XPackageWorkflow**: deployed to prod incl. WUS2 (the streaming caller is live).
- **CTIN** (`services.contentcatalog-CICD`): prod **Ring 1 ✅**, Ring 2 rolling.
- **SAGE** (`services.serviceapigateway-cicd`): prod **Ring 1 gated/stuck** — the route is **not live in any prod region yet** (the `prod-eau` region deploy is pending behind a "Gated Prod Ring 1" checkpoint).
- **XORc** title-id: prod deploy **queued** 2026-07-02.
- Net: a prod publish can't complete streaming E2E until **XORc prod lands** (clears the 400) **and SAGE prod Ring 1 clears** (so the ingestion POST doesn't 404). Because streaming is non-blocking, until SAGE is live the publish will *look* successful while silently skipping streaming.
