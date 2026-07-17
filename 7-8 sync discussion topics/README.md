# 7/8 Sync — Discussion Topics

Agenda and open questions for the 2026-07-08 playtest sync. The headline topic is **UI: Bayside — showing a real photo and game details on playtest tiles** (detailed below); the remaining bullets are status updates and decisions to lock with Anthony Keller and the CAS team.

## Agenda at a glance

- **UI: Bayside — real photo + details for playtest titles** (main topic; needs the CAS playtest contract + xToken claim).
- **CAS playtest contract (proto)** — where the new `.proto` lives and which fields carry display metadata.
- **xToken playtest user claim** — how it gets issued and whether Bayside's token already carries it.
- **PDP `?offeringId=` gap** — the product-detail page ignores the offering param today (client-only fix, unblocked).
- **Library "My playtests" tab** — status update: signed-out and not-invited states are done and verified.
- **Console (Garrison) parity** — the new CAS console contract endpoint and the flash-card surface.
- **Feature-flag gating** — ship the playtest surfaces dark.
- **Playtest ingestion region routing (SAGE→CTIN)** — ingestion is flaky (500s + poll 404s) because CTIN is Americas-only; interim Americas-core pin (done) + durable SAGE-route fix (needs CTIN endpoint).
- **PC playtest offering missing streaming config (SUG + allocation pool)** — the auto-created offering comes out with empty `DefaultAllocationPools`, no `PC_PLAYTEST` SUG/weights, and the Xbox region, so launch 400s; root cause is the prod partner-registry deploy of PR 15949594 stuck at Ring 1 (+ a new pool fix). Status update + deploy ask.

## UI: Bayside — real photo + details for playtest titles

**Goal:** when a tester opens the **My playtests** tab (or a shared playtest link), each game shows its real box art, title, and details — the same as any retail game — instead of the current placeholder.

**Where this lives:** `Xbox.JS` → `packages/@play-xbox/-route/library/src/components/PlaytestSection/PlaytestSection.tsx` (the library section-at-top decided in [`../FuturePlans/library-playtest-discovery.md`](../FuturePlans/library-playtest-discovery.md)), and the launch/stream path in [`../FuturePlans/bayside-playxbox-playtest-modifications.md`](../FuturePlans/bayside-playxbox-playtest-modifications.md).

**Why this is on the agenda:** David Kushmerick surfaced that CAS already returns extra playtest info for testers in the right DNA groups, and the CAS team confirmed the same path is open to Bayside with no service-side work (full thread in [Evidence](#evidence--what-people-said)).

> "We heard from David Kushmerick today that you all have a contract with Garrison to send back extra playtest info when you detect the user is in DNA groups associated with one or more playtests? Is there any way this can be easily added to Bayside as well? We are happy to handle the client side of changes that may be needed but would love to understand what it would take service side!" — the ask to the CAS team (Teams thread, 2026-07-07)

### What renders today (and why it's a placeholder)

A playtest tile shows a placeholder — a square with a beaker glyph and the raw `productId` — because a real photo and name are not available to the client for a private playtest build:

1. **The retail catalog does not serve private playtest builds.** `GameTile` hydrates art and name from the catalog system (`packages/@play-xbox/-system/catalog`), which calls the retail catalog (DCAT) keyed by `productId`. A DNA-gated playtest product returns nothing there.
2. **The private-offering fallback carries no art.** The catalog system has a private-offering path (`CatalogSystem.ts:235-371`) that augments a product with GameStream `TitleInfo`. But `TitleInfo` carries only IDs and input/program metadata — no image and no display name. The fallback builders prove this: `createDetailedProductInfoFromTitleInfo` (`CatalogSystem.ts:777-845`) sets `Image_Tile/Image_Poster/Image_Hero = null`, uses `titleId` as the `ProductTitle`, and stuffs `JSON.stringify(titleInfo)` into the description as a debug aid.
3. **That fallback only runs for the *active* offering.** The augmentation is gated on `activeOfferingInfo.isPrivate`. In the library tab the app's active offering is the tester's default (public) offering, so even the art-less fallback does not fire for the listed products. That is why the tile is an explicit placeholder rather than a broken `GameTile`.

### What CAS provides right now (grounded in the repo)

The Content Access Service (CAS) is the intended source of playtest display metadata, but the contract in the repo does not carry it yet:

- **The proto is access-only.** `packages/@xbox-js/-protobuf/content-access/proto/ContentAccessMessage.proto` has the access flag `OPTIONAL_ACCESS_TYPE_XPLAYTEST` and a `StaticProductMetadata` message limited to `supportedPlatforms` and `productKind`. There is **no** image URL, title, publisher, or description field.
- **The SDK returns access data, not art.** `packages/@xbox-js/-service-sdk/content-access/src/ContentAccessService.ts:144-153` exposes `fetchAllContentAccess(market, offeringId)`, which decodes access records keyed by `productId` (`productsByProductId`). No display metadata comes back.
- **Nothing in the client hydrates game art from CAS today.** CAS is consumed only for entitlement/access, never for tile or PDP display.

**Net:** the "new contract proto file" the CAS team referred to is **not in `Xbox.JS` yet**, and CAS as wired today tells the client *whether* a tester has playtest access — not *what the game looks like*.

> "CAS has no client specific contracts or endpoints. It is enabled right now - you just need to snag the new contract proto file. There is no service work from CAS to enable this for you!" — CAS team (Teams thread, 2026-07-07)

### The chain needed to show photo + details

1. **Pull the CAS playtest contract proto** into `packages/@xbox-js/-protobuf/content-access` and regenerate the TypeScript. This is the unblocking dependency — confirm which message and fields carry the image URL(s), title, publisher, and description.
2. **Confirm the xToken playtest claim** (DNA-group based) is present so CAS returns playtest data. This is server-side and owned by the playtest team.
3. **Extend the CAS SDK** (`fetchAllContentAccess`) to surface the new display fields off `productsByProductId`.
4. **Add a hydration seam keyed by an explicit `offeringId`.** Either a new content-access system or an extension of the catalog private-offering augmentation, reading image/title/publisher from CAS for a *given* playtest offering rather than the app's active offering — so the library tab hydrates without switching the whole app into the playtest offering.
5. **Swap the placeholder tile** for a real tile bound to the hydrated product info.
6. **Wire the PDP to honor `?offeringId=`** (see the PDP gap below) so the details page and its hydration switch to the playtest offering for shared links.

### Decisions and questions for this sync

- **Is CAS the art source, or should the catalog serve private products under an offering context?** Confirm the intended data source so the hydration seam (step 4) targets the right system.
- **Which CAS fields carry display metadata**, and are they returned per `productId` and per offering?
- **Client-side ownership.** The CAS team said client owns the consuming changes — confirm the split so the intern work (steps 3–6) is scoped correctly.

## CAS playtest contract (proto)

**Context:** CAS deployed playtest as a standard access type this week; the client "snags the new contract proto file," and no CAS service work is required. The repo's current proto is access-only (see above).

> "Yes, we have actually just deployed the CAS code this week to enable Playtests as a standard access type (was optional before - weve removed that concept)." — CAS team (Teams thread, 2026-07-07)

**Ask:**
- Where is the new `ContentAccessMessage.proto` published, and what is the pull/regeneration path into `@xbox-js/-protobuf/content-access`?
- Does the new contract carry product display metadata (image, title, publisher, description), or only richer access data?

## xToken playtest user claim

**Context:** CAS returns playtest data only when the xToken carries the new playtest user claim, which is based on the tester's DNA-group membership. The playtest team created the claim, and the CAS team pointed to Anthony Keller for how it gets issued.

> "It worked by checking the xToken for a new user claim that the playtest folks created. If we see the playtest user claim in the token, we will call for playtest data." — CAS team (Teams thread, 2026-07-07)
>
> "I would suggest talking to Anthony Keller about it more in depth - he has been heading up the playtest project, and may have more info about how to get those user claims added and any other gotchas that may be encountered around this!" — CAS team (Teams thread, 2026-07-07)

**Ask (Anthony):**
- How and when does the playtest claim get added to the token — automatically once the tester is in the DNA group?
- Does Bayside's existing token acquisition already include this claim, or is a token-scope change needed on the client?
- Any gotchas around claim propagation timing versus playtest publish?

## PDP `?offeringId=` gap (client-only, unblocked)

**Context:** playtest tiles deep-link to `https://play.xbox.com/products/{productId}/{slug}?offeringId=xpt{PlaytestProductId}`, and the URL contract documents that the param should switch the page to the playtest offering. The product-detail page does not read it today — it resolves offering context from `activeOfferingInfo` only (`packages/@play-xbox/-route/product-detail/.../AdditionalInformation.tsx:298`). So a shared playtest link opens the details page under the wrong (retail) offering.

**Proposal:** wire the PDP to consume `?offeringId=` and set the active/target offering for its hydration. This is pure client work with no CAS dependency and can start now.

**Ask:** confirm the PDP should switch offering context from the param (versus a gate/redirect), and whether this ships behind the feature flag.

## Library "My playtests" tab — status update

Built and verified in `PlaytestSection.tsx`:

- **Tab visibility** is gated on the tester having at least one `xpt` offering (`TabsHeader.tsx` via `usePlaytestOfferings`).
- **Signed out** shows a "Sign in to see your playtests" banner with a sign-in action, instead of a misleading empty state.
- **Not invited** vets real access per offering with `gameStream.authentication.queries.additionalOfferingAccess`; a `denied` result shows "You are not invited to this playtest," and the title fetch is gated on an `accessible` result.
- **Verification:** `nx typecheck play-xbox/route-library` passes across its dependency graph; lint is clean (a pre-existing missing `my_playtests_tab` string was added).

The section-at-top layout (rather than a filter or a separate tab) is the agreed v1 from the design brainstorm:

> Section-within-the-library was called "totally acceptable" once filtering was ruled out; "if you can do library filtering, then do that" is the nicer end state if it fits the timeline. — 2026-06-30 Design Brainstorm, via [`../FuturePlans/library-playtest-discovery.md`](../FuturePlans/library-playtest-discovery.md)

**Ask:** confirm this matches the agreed discovery UX, and that the placeholder tile is acceptable until the CAS art chain lands.

## Console (Garrison) parity

**Context:** the discovery decision ([`../FuturePlans/library-playtest-discovery.md`](../FuturePlans/library-playtest-discovery.md)) calls for a console **flash card** (stats ↔ product metadata, with Install and Play) and notes console needs a **new CAS contract endpoint** ("console normal" versus "console playtest") that must not break existing console test support.

> "CAS decides whether to return playtest content. Web calls a specific CAS endpoint ...; console needs a new CAS contract endpoint ('console normal' vs 'console playtest'). Must not break existing console test support." — 2026-06-30 Design Brainstorm, via [`../FuturePlans/library-playtest-discovery.md`](../FuturePlans/library-playtest-discovery.md)

**Ask:** is console parity in scope for this milestone, and who owns the console CAS contract endpoint? The same photo+details dependency applies.

## Feature-flag gating

**Context:** the launch-link work ships behind a flag so the retail path is unchanged when off ([`../FuturePlans/bayside-playxbox-playtest-modifications.md`](../FuturePlans/bayside-playxbox-playtest-modifications.md), W7).

**Ask:** confirm the library section, the PDP offering param, and the tester landing all sit behind the same flag, and which flag system (ECS, preview-gate config, or env flag) is the source of truth.

## Playtest ingestion region routing (SAGE→CTIN)

**The bug:** when a creator publishes a cloud playtest, the xPackage worker POSTs to SAGE
(`POST gssv-sage-prod.xboxlive.com/v3/playtest/playtesttitleingestion`). `gssv-sage-prod` is a **global Traffic Manager**
that routes each request to the nearest regional SAGE (Americas / Europe / APAC), and that SAGE forwards the route to a
**same-cluster** address `http://contentingestion-svc.contentingestion`. But **CTIN ingestion is centralized in Americas
only** (by design: Content *Resolution* is regional, Content *Ingestion* is not). Two intermittent failures result:

- **500 on ingest (Europe/APAC):** the TM routes the POST to a Europe/APAC SAGE with no CTIN → SAGE can't resolve
  `contentingestion-svc.contentingestion` → `Name or service not known` → HTTP 500. *(Seen in a northeurope log.)*
- **404 on status poll:** even in Americas, `americas.gssv-sage-prod` is a nested TM over **eastus2 + northcentralus**;
  submit (POST) and poll (GET) resolve DNS independently, but CTIN jobs are **not** cluster-local: the ingestion job
  store is a single shared Cosmos account per environment, so polls can find jobs created by any Americas sub-cluster.
  The observed eastus2 poll → `NotFound` in 702 ms was most likely for a submit that had 500'd in Europe/APAC and never
  created the job.

It's intermittent purely because of **which region the TM picks**. Proof it's co-location (not the proxy): the session
service `commandproxy` uses the same SAGE proxy pattern and succeeds in every Americas sub-cluster — because it's
deployed everywhere; CTIN isn't. Auth is **pass-through** (SAGE forwards the caller's token; CTIN authorizes the xPackage
app id), so moving where the route points needs no auth work.

**Evidence (from logs — verbatim):**

- **Ingest 500 — Europe.** Attached diagnostic `93c7…` (all 3 rows: `2026-07-06T22:49:00Z`,
  `Tenant=xcld-prod-europe-control-neu-aks`, `ControlPlane=northeurope`, same correlation vector
  `lk4L9yNLQkO2kgA%2B.1.57`):
  - `POST - http://gssv-sage-prod.xboxlive.com/v3/playtest/playtesttitleingestion - 500 [44ms]`
  - `POST http://contentingestion-svc.contentingestion/v3/workflows/playtesttitleingestion : UnexpectedFailure (43 ms)`
  - `System.Net.Http.HttpRequestException: Name or service not known (contentingestion-svc.contentingestion:80)`
- **Poll 404 — eastus2.** Prod SAGE Geneva log row (`2026-07-07T00:38:02Z`,
  `Tenant=xcld-prod-americas-control-eus2-aks`, `ControlPlane=eastus2`, `data_RequestStatus=CallerError`):
  - `GET http://contentingestion-svc.contentingestion/v3/workflows/playtesttitleingestion/5232FA04-59C9-44ED-90C6-BE2FEACF3A86 : NotFound (702 ms)`
  - **Verified from the row:** CTIN *was* reached in eastus2 — a real HTTP 404 after 702 ms, **not** a DNS `Name or
    service not known`. **Inference:** because CTIN uses a single shared Cosmos job store per environment, this was most
    likely a poll for a job whose submit had 500'd in Europe/APAC and was never created.
- **Co-location proof — commandproxy.** Attached diagnostic `725f…` (`2026-07-04`): the session service resolved in
  **both** Americas sub-clusters with `data_Succeeded=True` and **zero** `Name or service not known` across 255 rows:
  - `POST http://commandproxy-svc.commandproxy/v1/commandrequest/forward : NotFound (34 ms)` — `ControlPlane=eastus2`, `succeeded=True`
  - `POST http://commandproxy-svc.commandproxy/v1/commandrequest/forward : NotFound (5 ms)` — `ControlPlane=northcentralus`, `succeeded=True`
  - Here the 404 is app-level ("no session"), not a routing failure — the same-cluster proxy works when the backend is
    co-located, which CTIN isn't.

**Option A — pin the worker to the Americas core *(done, interim — Xbet PR 16102792)*.** Change the worker's ingestion
`Host` from the global `gssv-sage-prod` to `americas.gssv-sage-prod.xboxlive.com`. Submit + poll then stay on the
Americas core → SAGE can reach CTIN → CTIN uses the shared environment job store, fixing the Europe/APAC 500 and
preventing false 404s from failed submits. Verified: config `Host` feeds the client `BaseAddress` used by both methods;
the `00:38` eastus2 GET proves an Americas sub-cluster reaches CTIN (a real 404 from CTIN, not a DNS failure), and the
ingestion path already ran end-to-end in prod (offering `XPT2SDT4X91KRQS` was created). Per the CTIN owner, Americas is
the only core with Content ingestion; eastus2/northcentralus sub-clusters rotate and must not be pinned directly.
Trade-off: caller-side core pin until the durable route fix lands. Only the XPackageWorkflow playtest ingestion host
needs this `americas` pin; other prod Xbet SAGE callers stay on the global host, and Staging/Dev stay on
`gssv-sage-test`.

**Option B — point the SAGE route at a stable CTIN endpoint *(durable, recommended)*.** Change the SAGE playtest route's
`ServiceBaseUri` from the same-cluster name to a **stable cross-region-reachable CTIN endpoint** (internal private-DNS /
internal LB / Private Link). Then any SAGE region forwards to the same CTIN, the worker keeps the global host (**no
pin**), and both symptoms are fixed. Precedent: CTIN is already reachable via a gateway URL its clients use
(`americas.gssv-dev-prod.xboxlive.com/api/contentingestion`) — B needs the prod/internal equivalent. Dependency: CTIN
publishes that endpoint; the SAGE change is then ~1 line. Still funnels to the single Americas CTIN (makes routing
region-independent, not CTIN multi-region — the job store is already shared per environment; multi-region ingestion
would be a bigger CTIN project).

**What I want to do:** ship **Option A now** (verified, low-risk, unblocks end-to-end testing today), then pursue
**Option B** with the SAGE + CTIN teams as the durable fix so we can drop the pin (ADO Task 63013710:
https://microsoft.visualstudio.com/Xbox/_workitems/edit/63013710). Confirm B's owner and whether CTIN can publish a
stable cross-region endpoint.

**Ask (Anthony / Brian / CTIN):**
- Confirm the interim `americas.gssv-sage-prod.xboxlive.com` pin is the right short-term target now that Timi clarified
  Americas is the only core with Content ingestion and the sub-clusters rotate.
- For Option B: can CTIN expose a stable cross-region-reachable endpoint the SAGE playtest route can target?
- Confirm the shared Cosmos job-store understanding: `WorkflowsDB` lives in one environment Cosmos account, so the
  remaining durable work is routing reachability, not a cross-cluster job-store split.

Detail: [`../Explanations/sage-ctin-routing-error-and-options.md`](../Explanations/sage-ctin-routing-error-and-options.md),
[`../Blockers/sage-ctin-region-routing.md`](../Blockers/sage-ctin-region-routing.md).

## PC playtest offering missing streaming config (SUG + allocation pool)

**The bug:** once ingestion succeeds, `PlaytestProcessor.ConfigurePlaytestAsync` (services.partnerregistry) writes the
playtest `OfferingV2.json` **without the fields the streaming allocator needs**. A published PC playtest therefore
produces an offering that resolves and shows the tile (the tester can see it in their DNA group) but **cannot start a
session**.

**Why it won't stream — two layers:**

1. **Empty `DefaultAllocationPools` → hard 400.** With no `[PC] → pool` mapping, the allocator has no server pool to draw
   from and rejects session creation outright:
   ```json
   { "code": "Unknown", "statusCode": 400,
     "message": "Offering does not specify any default allocation pools for the selected content platform: PC" }
   ```
   The front end surfaces this as *"Couldn't start your game streaming session — Unable to communicate with servers."*
2. **No `PC_PLAYTEST` SUG + wrong region → nothing to allocate even past the 400.** The offering has
   `SelectableSystemUpdateGroups: null`, `SystemUpdateGroupWeights: {}`, and `Regions: ["NorthCentralUs"]` (the **Xbox**
   region). Without the SUG, Content Targets can't match the title to the `PC_PLAYTEST` quota, so **no T4 is ever
   provisioned**; and `PC_MAIN` / the quota only exist in **WestUs2**, so even the pool wouldn't resolve in
   NorthCentralUs. The title itself is fine (`Platform: PC`, `TargetServerSkus: [STANDARD_NC64AS_T4_V3]`, `XboxTitleId`
   resolved) — the gap is entirely offering-side.

**Root cause — a deploy gap, not a logic gap.** The fields split across two sources, and neither is live on the ring that
created the offering:

- `SelectableSystemUpdateGroups`, `SystemUpdateGroupWeights`, and the `WestUs2` PC region were all added by **PR 15949594**
  (merged 2026-06-29). That PR's prod rollout is **stuck**: the run that built its commit `5f5ee23a` reached **prod Ring 1
  (succeeded) but failed at Ring 2** (Ring 3 skipped), and the latest `main` build is **gated at prod Ring 1**. So the
  partner-registry instance that created the offering is a **Ring 2/3 instance still on pre-15949594 code** — which is
  exactly why the offering has no SUG, no weights, and `NorthCentralUs`.
- `DefaultAllocationPools` was **never set in code at all** — it's a new one-line addition (see fix below).

The proof it's a stale-ring issue: PR 15949594 sets the SUG **and** the region in the same change, and the offering is
missing **both** together.

**Evidence — the actual prod offering `XPT2SDT4X91KRQS`** (`.../Environments/PROD/Partners/MICROSOFT/Offerings/
XPT2SDT4X91KRQS/OfferingV2.json`):

```jsonc
"DefaultAllocationPools": {},          // ← empty → the 400
"SelectableSystemUpdateGroups": null,  // ← no PC_PLAYTEST SUG (from PR 15949594, not on this ring)
"SystemUpdateGroupWeights": {},        // ← no weights (from PR 15949594)
"Regions": ["NorthCentralUs"],         // ← Xbox region; PC playtest should be WestUs2 (from PR 15949594)
"AuthorizationOptions": { "AllowedDnaGroups": ["4611686019004512103"], ... }
```

**What a fully-configured PC playtest offering must have** (all four line up with the live prod infra — `PC_MAIN` pool +
`PC_PLAYTEST` SUG + quota, all in WestUs2):

| Field | Broken (current) | Correct | Source |
|---|---|---|---|
| `DefaultAllocationPools` | `{}` | `{ "PC": "PC_MAIN" }` | new fix (branch `t-melanichen/playtest-default-allocation-pool`) |
| `SelectableSystemUpdateGroups` | `null` | `[ "PC_PLAYTEST" ]` | PR 15949594 |
| `SystemUpdateGroupWeights` | `{}` | `{ "PC_PLAYTEST": 100 }` | PR 15949594 |
| `Regions` | `["NorthCentralUs"]` | `[ "WestUs2" ]` | PR 15949594 |

**Fixes (status):**

- **Existing offering — manual data patch (unblocks *this* playtest now):** added all four fields to
  `XPT2SDT4X91KRQS` directly. **[PR 16097829](https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.data.partnerregistry/pullrequest/16097829)** — needs proof-of-presence to complete. `FilesystemRegistry` reloads from git, so no service redeploy.
- **Durable code fix — `PlaytestProcessor` sets the pool for all future offerings:** adds
  `DefaultAllocationPools = { PC: PC_MAIN }` (hardcoded `PC_MAIN` const + TODO, matching the existing `PcServerSku`
  pattern). Branch **[`t-melanichen/playtest-default-allocation-pool`](https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.partnerregistry?version=GBt-melanichen%2Fplaytest-default-allocation-pool)** (services.partnerregistry), pushed and green (14/14 tests) — PR to follow.
- **Prod infra prerequisites — DONE:** `PC_PLAYTEST` SUG definition
  ([16103484](https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.data.partnerregistry/pullrequest/16103484))
  and Content Targets quota `PC_PLAYTEST=1 @ STANDARD_NC64AS_T4_V3 / WESTUS2`
  ([16103771](https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.data.partnerregistry/pullrequest/16103771))
  — both approved by Timi and merged (proof-of-presence) on 2026-07-07.
- **Deploy — the real blocker:** PR 15949594 (and then the pool fix) must roll through **prod Ring 1 gate → Ring 2 →
  Ring 3** so every partner-registry instance produces the full config. Re-running the failed prod deploy jobs now.

**Ask (Timi / partner-registry release owner):**
- Can we push the partner-registry prod deploy past the **Ring 1 gate / Ring 2 failure** so PR 15949594 (SUG + WestUs2
  region) reaches all rings? Right now offerings created on Ring 2/3 come out unstreamable.
- Review the `DefaultAllocationPools` code fix (branch [`t-melanichen/playtest-default-allocation-pool`](https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.partnerregistry?version=GBt-melanichen%2Fplaytest-default-allocation-pool)) — is hardcoding `PC_MAIN` (const + TODO, like `PcServerSku`) fine, or do you want it in `PlaytestSettings` dynamic config?
- Confirm the offering should set `DefaultAllocationPools = { PC: PC_MAIN }` (mirroring your `KOLARITESTXNEW` example),
  versus the Content Targets server-sets config supplying the pool.

Detail: [`../Blockers/pc-playtest-default-allocation-pools.md`](../Blockers/pc-playtest-default-allocation-pools.md),
[`../PRProgress/26-PTNR-DATA-16103484-add-pc-playtest-sug-prod.md`](../PRProgress/26-PTNR-DATA-16103484-add-pc-playtest-sug-prod.md),
[`../PRProgress/27-DCFG-16103771-contenttargets-pc-playtest-quota-prod.md`](../PRProgress/27-DCFG-16103771-contenttargets-pc-playtest-quota-prod.md).

## Consolidated open questions (for Anthony / CAS)

1. Where is the new CAS playtest proto, and which fields carry image/title/publisher/description?
2. How does the xToken playtest claim get issued, and does Bayside's token already carry it?
3. Is CAS the art source for playtests, or should the catalog serve private products under an offering context?
4. Console CAS contract endpoint — owner and timeline.
5. Which feature flag gates the playtest surfaces?
6. Ingestion routing: confirm the Americas-core interim pin and whether CTIN can publish a stable cross-region endpoint (Option B / ADO Task 63013710).
7. PC offering: can the partner-registry prod deploy get past the Ring 1 gate / Ring 2 failure so PR 15949594 reaches all rings?

## Evidence — what people said

### CAS enablement thread (Teams, 2026-07-07)

The exchange that opened the Bayside playtest-data path. Quoted verbatim.

**The ask to the CAS team:**

> "we have an intern this summer, Melanie (just added here), who is working on adding game streaming as a capability to the PlayTest service. We heard from David Kushmerick today that you all have a contract with Garrison to send back extra playtest info when you detect the user is in DNA groups associated with one or more playtests? Is there any way this can be easily added to Bayside as well? We are happy to handle the client side of changes that may be needed but would love to understand what it would take service side!"

**CAS team reply:**

> "Yes, we have actually just deployed the CAS code this week to enable Playtests as a standard access type (was optional before - weve removed that concept). It worked by checking the xToken for a new user claim that the playtest folks created. If we see the playtest user claim in the token, we will call for playtest data."

> "CAS has no client specific contracts or endpoints. It is enabled right now - you just need to snag the new contract proto file. There is no service work from CAS to enable this for you!"

> "I would suggest talking to Anthony Keller about it more in depth - he has been heading up the playtest project, and may have more info about how to get those user claims added and any other gotchas that may be encountered around this!"

**What the thread establishes:**
- CAS returns playtest metadata only when the xToken carries the new **playtest user claim** (DNA-group based, created by the playtest team).
- There is **no CAS service work** and **no client-specific endpoint** — the client pulls the **new contract proto file**.
- **Anthony Keller** owns how the user claim gets added and knows the gotchas.

### PC streaming config — XCloudIngestion sync (Timi Bolaji)

Supports the PC playtest offering fix (`PC_MAIN` allocation pool + `PC_PLAYTEST` SUG). From `../Transcripts/XCloudIngestion.docx` (local-only):

> "The same way for Xbox, there's always Xbox Main and thousands of servers." — Timi Bolaji (~13:03)

> "distinct PC_PLAYTEST SUG ... enable it for the PC play test SUG." — Timi Bolaji (~12:23)

Timi also approved and merged the prod SUG definition and the Content Targets `PC_PLAYTEST` quota on 2026-07-07 (proof-of-presence), confirming the intended PC streaming shape.

### Design brainstorm (2026-06-30)

Captured in [`../FuturePlans/library-playtest-discovery.md`](../FuturePlans/library-playtest-discovery.md) (transcript is local-only):
- Discovery surface: section-at-top was "totally acceptable"; library filtering is the nicer end state — "if you can do library filtering, then do that."
- CAS gates discovery content; console needs a **new CAS contract endpoint** and must not break existing console test support.

## References

- [`../FuturePlans/bayside-playxbox-playtest-modifications.md`](../FuturePlans/bayside-playxbox-playtest-modifications.md) — launch-link / stream-start / denial UX.
- [`../FuturePlans/library-playtest-discovery.md`](../FuturePlans/library-playtest-discovery.md) — discovery surface decision (section-at-top, console flash card, CAS hydration).
- [`../FuturePlans/ui-steps-bayside.md`](../FuturePlans/ui-steps-bayside.md) — launch-link / denial / metadata / install-vs-stream steps.
- [`../Explanations/sage-ctin-routing-error-and-options.md`](../Explanations/sage-ctin-routing-error-and-options.md), [`../Blockers/sage-ctin-region-routing.md`](../Blockers/sage-ctin-region-routing.md) — ingestion region routing.
- [`../Blockers/pc-playtest-default-allocation-pools.md`](../Blockers/pc-playtest-default-allocation-pools.md) — PC offering streaming config.
- Code anchors: `packages/@play-xbox/-route/library/src/components/PlaytestSection/PlaytestSection.tsx`; `packages/@play-xbox/-system/catalog/src/CatalogSystem.ts:235-371,777-845`; `packages/@xbox-js/-protobuf/content-access/proto/ContentAccessMessage.proto`; `packages/@xbox-js/-service-sdk/content-access/src/ContentAccessService.ts:144-153`.
