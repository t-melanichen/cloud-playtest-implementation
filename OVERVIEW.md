# Instantly Shareable Playtest

**Owner:** Melanie Chen (xPlaytest)
**Status:** Spec v1 — ready for implementation
**Companion docs:** [`SPEC.md`](./SPEC.md) (long form), [`ARCHITECTURE.md`](./ARCHITECTURE.md), [`openapi/playtest-ingestion.yaml`](./openapi/playtest-ingestion.yaml), [`ado/ado-tasks.md`](./ado/ado-tasks.md)

---

## 1. What we are building

Today xPlaytest distributes private pre-release builds to testers as downloadable installs. Modern games are hundreds of gigabytes — downloads are slow and hardware does not scale.

**This project adds a streaming option.** When a creator publishes a playtest with **Enable Cloud Streaming** checked, the build is ingested into xCloud and becomes streamable through a shareable link, *in addition to* the existing download flow. The behavior is purely additive: creators who opt out are unaffected.

## 2. End-to-end flow

| # | Phase | What happens | Owner |
|---|---|---|---|
| 1 | **Publish** | Creator hits Publish in Partner Center. The publish workflow runs as today and gains a new final state, `XCloudIngestionTrigger`. | xPlaytest |
| 2 | **Handoff** | The new state POSTs a `PlaytestIngestionJobParameters` payload to SAGE and stores the returned `jobId`. Failure is non-fatal — download still publishes. | xPlaytest → xCloud |
| 3 | **Ingestion** | A new `PlaytestTitleIngestionWorkflow` chains asset ingestion, creates a private offering `xpt-{id}`, attaches the title, and waits for install readiness. | xCloud |
| 4 | **Streamable** | xPlaytest polls SAGE for terminal state, sets `PlaytestStatus = StreamingReady`, and surfaces the launch URL. | xCloud → xPlaytest |

A code-grounded sequence diagram lives in `ARCHITECTURE.md`.

## 3. Design decisions

| # | Decision | Why |
|---|---|---|
| 1 | **Streaming is opt-in, additive** to the download flow | Avoids surprising the existing creator base; keeps the new path low-risk. |
| 2 | **One playtest = one title = one offering** | Each playtest can target a distinct audience, so the auth boundary stays 1:1. Clustering is a v1.1 concern. |
| 3 | **PC only in v1** (Xbox console deferred) | The existing publish path already targets `WINDOWS.DESKTOP`. Console adds Xbox-only allocator and title-id handling. |
| 4 | **Auth gated at the offering level**, not per title | A single DNA-group check at offering entry; matches the pattern TestX already uses. |
| 5 | **Bespoke `POST /playtest/ingestion`**, not a generic `CreateOfferingFromStoreData` | Keeps the contract small. Lets us encode playtest defaults (RETAIL sandbox, private audience) server-side. A generic surface is the future direction but out of summer scope. |
| 6 | **Polling for terminal state**, not callbacks | SAGE is a request/response proxy today; cross-tenant callbacks need a message bus that does not yet exist. Polling reuses the publish workflow's existing primitives. |
| 7 | **Single flight id for install lookup** = lex-smallest DNA-group GUID | The install pipeline expects one flight id. All groups in a playtest point to the same build, so the choice is deterministic and re-run-stable. Audience check (XC5) still uses the full set. |
| 8 | **Opaque offering id** (`xpt-{shortId}`); title id is name-derived for readability | Offering id has a 32-char cap and is auth-critical. Title id is more user-visible, so we strip the playtest name to alphanumeric and append the product id for uniqueness. |
| 9 | **Short-term cross-tenant auth: Green → Corp** via SAGE | Rides an in-flight SAGE PR. The long-term PME story is owned by the GSS platform team and is out of scope. |
| 10 | **Delete = tombstone + 7-day GC**, not synchronous hard delete | SFI requires manual PR approval for Partner Registry writes, so a true hard delete is not achievable in v1. Tombstoning clears `AllowedDnaGroups` immediately so testers lose access, and the offering disappears from the DevApi listing. *Needs explicit sign-off from xCloud reviewers.* |
| 11 | **Streaming-enabled playtests must carry an explicit expiration** | xCloud needs a bounded end date. Download-only playtests are unaffected. UI default = 90 days; soft warning above 180. |
| 12 | **Bundle offering write + title attach into a single PR** | Cuts the manual SFI approval cost in half (1 PR per publish instead of 2). |
| 13 | **External API unversioned today; internal `/v3/...`** | Matches existing SAGE and `WorkflowsControllerV3` conventions. Future breaking changes bump to `/v2/playtest/ingestion`. Additive optional fields do not require a bump. |

## 4. Work breakdown

Full task-level breakdown with acceptance criteria is in [`ado/ado-tasks.md`](./ado/ado-tasks.md). The roll-up below uses SWAGs in developer-days.

### xPlaytest (25d)

| ID | Deliverable | SWAG |
|---|---|---|
| **PT1** | Insert `XCloudIngestionTrigger` state in `XPackagePlaytestPublishWorkflow`; add publish-time validators (streaming requires expiration; seller allow-list) | 6 |
| **PT2** | Build `StoreAsset` from playtest product / package data; resolve `XboxTitleId` from XProduct `alternateIds`; ship `AumID` default | 4 |
| **PT3** | Project resolved DNA-group IDs into the offering config | 1 |
| **PT4** | New `XCloudIngestionClient` (cross-tenant S2S, retries, `202`/`409` handling, `jobId` persistence) | 3 |
| **PT5** | Polling loop (exponential backoff) + background reconciliation job for slow ingestions; `StreamingReady` state + launch URL | 6 |
| **PT6** | Lifecycle updates: audience / expiry change → re-trigger; delete → call `DELETE …/by-playtest/{id}` | 5 |

### xCloud (27d, plus 2d demo prep)

| ID | Service | Deliverable | SWAG |
|---|---|---|---|
| **XC1** | SAGE | New routes: `POST /playtest/ingestion`, `GET …/{jobId}`, `DELETE …/by-playtest/{id}` | 3 |
| **XC2** | SAGE | Allow-list the xPlaytest S2S identity (cross-tenant) | 1 |
| **XC3** | `services.contentingestion` | `PlaytestTitleIngestionWorkflow`, contract types, controller routes | 9 |
| **XC4** | `services.partnerregistry` | `AllowedDnaGroups` + `AllowedSandboxId` on `OfferingV2`; bulk-edit for offering + title in one PR | 5 |
| **XC5** | User-login / offering auth | `GsToken.DnaGroups` check at offering entry; skip per-title entitlement for playtest titles | 5 |
| **XC6** | Install pipeline | Pick lex-smallest flight id; branch `ServerFilter` so PC playtests skip the Xbox-only allocator parameters | 4 |

**Execution order (2 devs in parallel):**

```
Phase A (wk 1–2)   XC4, XC5, XC2, PT3       → no inter-dependencies
Phase B (wk 2–4)   XC1, XC3, XC6, PT2       → A must land first
Phase C (wk 4–6)   PT1, PT4, PT5            → B must land first
Phase D (wk 6–7)   PT6                      → C must land first
Soak  (wk 7–10)    end-to-end stabilization, OpenAPI publish, runbooks
```

## 5. Contracts

| Surface | Where |
|---|---|
| External REST (xPlaytest ↔ SAGE) | [`openapi/playtest-ingestion.yaml`](./openapi/playtest-ingestion.yaml) |
| Internal contract types & code references | [`ARCHITECTURE.md`](./ARCHITECTURE.md) |
| Long-form spec (rationale, alternatives, code citations) | [`SPEC.md`](./SPEC.md) |

The single most important payload is `PlaytestIngestionJobParameters`. Required fields: `PlaytestId`, `AllowedDnaGroups` (min 1), `ExpirationTime`, `StoreAsset`. Optional with server defaults: `AllowedSandboxId` (→ `RETAIL`), `IsGreenSigned` (→ `true`). Reserved for future: `CallbackUrl`, `CorrelationId`.

## 6. Milestones

| # | Milestone | Target | Definition of done |
|---|---|---|---|
| **M1** | **Foundational demo** — manual offering with a fixed DNA group; Partner Center group membership changes flip tester access live | end of wk 2 (≤ 6/20) | XC4 + XC5 shipped; operator script provable end-to-end |
| **M2** | **Ingestion** — manual `curl` against SAGE drives the full ingestion to a streamable offering | end of wk 4 (≤ 6/30, **Midpoint Connect**) | XC1, XC2, XC3, XC6, PT2 shipped |
| **M3** | **xPlaytest integration** — Publish in Partner Center end-to-end produces a launch URL | end of wk 6 (≤ 7/14) | PT1, PT4, PT5 shipped |
| **M4** | **Lifecycle** — audience / expiry / republish / delete reflect in xCloud | end of wk 7 (≤ 7/21) | PT6 shipped |
| **M5** | **Soak + handoff** — real studio build; OpenAPI + runbooks published | end of wk 10 (≤ 7/28, **Final Connect**) | End-to-end test passes; docs live |
| — | **Presentation** | wk 11–12 | Intern presentation |

## 7. Success criteria (P0)

A v1 release passes when **all** of the following hold:

1. Publishing a streaming-enabled playtest submits the xCloud ingestion within seconds and becomes live within one approver round-trip.
2. The offering exists in Partner Registry with the audience's DNA groups and a non-null expiration.
3. The offering contains exactly one title corresponding to the playtest.
4. An authorized tester can stream the playtest through xCloud via the launch URL.
5. An unauthorized user opening the launch URL is denied with no metadata leakage.
6. Audience, expiration, and build-republish changes after publish all re-propagate to xCloud.
7. Deleting the playtest removes tester access within the GsToken refresh window and removes the offering from DevApi.
8. Streaming-enabled publish is gated behind a seller / title allow-list feature flag during private preview.
9. xCloud ingestion failure does **not** block the download playtest from publishing.

**P1 (deferred):** Bayside login flow on the launch URL; GSSV `/offerings` returns the user's accessible playtest offerings for in-client discovery.
**P3 (out of scope):** Xbox console support, region / touch-control configuration, in-stream feedback collection.

## 8. Known risks and open items

| Item | Status | Plan |
|---|---|---|
| Cross-tenant S2S long-term (PME) | Open | GSS platform team owns the PME story. xPlaytest rides the short-term Green → Corp PR; the call site is marked for revisit. |
| Manual PR approval on Partner Registry writes | Mitigated | One bundled PR per publish instead of two; xCloud reviewers approve out-of-band for the internship. |
| `XboxTitleId` resolver | Open (P0 in PT2) | Read `alternateIds[XboxTitleId]` from XProduct; replaces today's empty hardcode. |
| `AumID` for PC | Decided | Ship a constant default for v1 (telemetry-only on server side); v1.1 plumbs the real `ApplicationId` from the AppX manifest. |
| PC install poll path | Open (audit in XC6) | Today's allocator parameters are Xbox-only. XC6 audits and branches `ServerFilter` on `Platform`. |
| Stable playtest identity for offering id | Open | xPlaytest confirms whether `PartnerCenterProductId` is stable across republishes (recommended); otherwise we use the equivalent stable upstream id. Materially changes the offering-proliferation story on nightly republishes. |
| Delete model (tombstone vs hard delete) | Decision pending sign-off | v1 ships tombstone + 7d GC. User-visible behavior matches the P0 wording. Needs explicit xCloud sign-off. |

## Glossary

- **DNA group** — GMS audience grouping; resolves to the GUIDs in `AllowedDnaGroups`.
- **GMS** — Group Management Service.
- **GsToken** — Game Streaming token; carries `DnaGroups` claims.
- **SAGE** — Service API Gateway; cross-tenant ingress proxy for xCloud.
- **SUCU** — Streaming Update Catalog; xCloud's package-version resolution.
- **SFI** — Secure Future Initiative; the policy regime that forbids self-approving PRs.
- **xpt-{id}** — Offering id prefix for playtest-derived offerings.
