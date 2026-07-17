# Transcript decisions ledger

Built from `Transcripts\*.docx` using Python `python-docx` paragraph extraction
plus table-cell extraction. Extraction succeeded for all 9 transcripts; none had
tables. `Aditya1.docx` extracted but contained only a short room/transcription
setup, so no substantive design decision was captured from it.

## Cross-cutting decisions and considerations

### Product shape and launch behavior

- **Streaming is additive to the existing downloadable playtest flow.** Source:
  `InternSync1.docx` — David Kushmerick/Anthony Keller around the publish-flow
  walkthrough agreed this is a download playtest with an opt-in streaming toggle,
  not an either/or choice. Reflected in `.github\agents\playtest-streaming.md`
  and `Repos\Xbox.Gpx.PartnerCenter.Client.md`.
- **The creator launch link can be known from the offering id, but readiness must
  still be verified.** Source: `InternSync1.docx` — Anthony asked whether the
  streaming URL could be known; Jack said it is known from the offering id, while
  Timi cautioned the link may not be good if ingestion fails mid-flow. Reflected
  in `FuturePlans\launch-link-and-status-accuracy.md`.
- **Bayside is the future web client, but custom-offering launch support was not
  available in the Jack2 discussion.** Source: `Jack2.docx` — Jack distinguished
  Edgewater, Garrison, and Bayside, then said Bayside does not support custom
  offerings yet. Reflected in `FuturePlans\bayside-playxbox-playtest-modifications.md`
  and `Repos\Xbox.JS.md`.

### Offering, title, audience, and IDs

- **Offering and title setup belongs in xCloud/Partner Registry after content
  ingestion, not as a Partner Center-only blob.** Source: `Timi.docx` — Timi
  separated catalog ingestion from availability/audience, then said availability
  and audience are configured in Partner Registry. Reflected in
  `Explanations\xcloud-xplaytest-xpackage.md`, `Repos\services.partnerregistry.md`,
  and `PRProgress\13-PTNR-15773366-new-playtest-endpoint.md`.
- **Use one playtest-specific offering id shaped as `xpt{PlaytestProductId}`;
  title ids may append the neutral/base title component.** Source:
  `XCloudIngestion.docx` — Timi discussed `XPT-product ID` as the offering id and
  a title id formed from that plus another title component; later PR/docs settled
  the no-hyphen offering convention. Reflected in `.github\agents\playtest-streaming.md`,
  `PRProgress\15-PTNR-15821813-centralize-offering-id-on-request.md`, and
  `Repos\services.partnerregistry.md`.
- **Use Xbox Live account-backed identity for access; DNA groups are the offering
  auth input.** Source: `Jack2.docx` — Jack explained gamertag vs ZUID/PUID and
  asked for contract/auth changes so DNA groups are recognized in the GS token.
  Reflected in `PRProgress\01-PTNR-15732852-add-allowed-dna-groups.md`,
  `PRProgress\02-AUTH-15738761-enforce-allowed-dna-groups-login.md`, and
  `Repos\services.auth.md`.
- **The full `AllowedDnaGroups` set is used for offering authorization, while
  the as-built ingestion path uses one representative `XusAudience`.** Source:
  `InternSync1.docx`/`Jack2.docx` established DNA-group auth; the exact single
  `XusAudience` convention is reflected in the as-built spec delta rather than
  explicitly stated in transcript text extracted here. Reflected in
  `Documentation\spec-updates\2026-06-18-as-built-delta.md` and
  `.github\agents\playtest-streaming.md`.
- **Xbox Live title id should come from the service-config/XORc path, not a
  placeholder.** Source: `InternSync2.docx` — David/Aditya discussed looking up
  the title id by product id and having the service expose application family,
  title id, and related fields. Reflected in `Blockers\xbox-live-title-id.md`,
  `Repos\xorc.md`, and `Repos\Xbox.Xbet.Service.md`.

### PC-first ingestion and polling

- **V1 is PC-first; console differences are acknowledged but not blocking the PC
  path.** Source: `InternSync1.docx` — Timi clarified the discussed ARM/MSI/CC
  issue only affects PC and does not block Xbox content; `XCloudIngestion.docx`
  separately discusses different PC vs console install behavior. Reflected in
  `.github\agents\playtest-streaming.md` and
  `Explanations\handling-xbox-vs-pc-differences.md`.
- **Adding the title to the offering is what triggers PC install work; readiness
  polling happens after attach.** Source: `XCloudIngestion.docx` — Timi described
  content targets reading offering config, enabling the PC playtest SUG, and
  distribution installing once the title is in the offering. Reflected in
  `Blockers\pc-install-readiness-poll.md` and
  `FuturePlans\pc-install-readiness-polling-implementation.md`.
- **The PC readiness query should use PC Orchestrator/content filters, not the
  Xbox allocator surface.** Source: `XCloudIngestion.docx` — Jack asked whether
  to query orchestrator until a VM with the content appears; later docs identify
  the exact `IPCOrchestratorClient.QueryServersPagedAsync` surface. Reflected in
  `Blockers\pc-install-readiness-poll.md` and
  `Explanations\ingestion-creates-new-things.md`.
- **MVP can temporarily skip PC polling if the product accepts early-ready links
  and user retry until install completes.** Source: `XCloudIngestion.docx` — Timi
  said that is fair for MVP because it only means the link is provided without a
  guarantee it works immediately. Reflected in
  `Explanations\handling-xbox-vs-pc-differences.md` and
  `FuturePlans\launch-link-and-status-accuracy.md`.
- **Polling/retry starts simple and can be refined after end-to-end works.**
  Source: `InternSync1.docx` — David said to use existing workflow orchestration
  and retry behavior and that xCloud trigger failures should not block publish;
  `InternSync3.docx` discussed waiting for async states to complete. Reflected in
  `FuturePlans\polling-strategy-refinement.md`.

### API, status, and S2S

- **The xPlaytest call into xCloud should be one POST through SAGE plus a status
  GET.** Source: `Timi.docx` — Timi said the cross-SAGE call is the request to
  ingest and that the endpoint should be an HTTP POST with a GET for status.
  Reflected in `Repos\services.serviceapigateway.md`,
  `Repos\services.contentingestion.md`, and `Repos\Xbox.Xbet.Service.md`.
- **Docs specify `200 OK` with framework `OperationStatus`, but the exact status
  envelope is not explicitly present in the extracted transcript text.** Source:
  transcript support is the Timi POST/GET-status discussion in `Timi.docx`; the
  exact `200 OK`/`OperationStatus` convention is documented in
  `.github\agents\playtest-streaming.md` and
  `Documentation\spec-updates\2026-06-18-as-built-delta.md`. Reflected there;
  verify against live code before changing the contract.
- **Cross-tenant S2S remains a dedicated blocker/future-plan item.** Source:
  `InternSync1.docx` — Timi tied completion callbacks/events to the still-open
  cross-tenant communication conversation; `InternSync2.docx` captured broader
  Green/SUKU/PME concerns. Reflected in `Blockers\cross-tenant-s2s.md` and
  `FuturePlans\s2s-cross-tenant-call.md`.

### Partner Center UX and gating

- **Partner Center should expose streaming as an opt-in toggle.** Source:
  `InternSync1.docx` — Anthony described it as a toggle to enable streaming,
  likely opt-in. Reflected in `Repos\Xbox.Gpx.PartnerCenter.Client.md`.
- **Streaming-enabled playtests should be gated by ECS/private-preview config,
  likely seller id first, with product id optional.** Source: `InternSync3.docx`
  — Anthony proposed a per-seller or seller+product feature flag; David discussed
  ECS configs, preview gating, and seller/product shape. Reflected in
  `FuturePlans\ecs-feature-flag.md` and `Repos\Xbox.Gpx.PartnerCenter.Client.md`.
- **Partner Center should restrict streaming audiences to Xbox Live-capable
  groups.** Source: `InternSync2.docx` — David/Melanie/Timi discussed the need
  to obtain the group/DNA id used elsewhere and the lag in group propagation;
  `Jack2.docx` explains Xbox-account-backed auth. Reflected as planned work in
  `.github\agents\playtest-streaming.md` and
  `Repos\Xbox.Gpx.PartnerCenter.Client.md`.

### Expiration, dates, and storage

- **InternSync4 changed the streaming expiration cap decision from 7 days to 30
  days and clarified the storage/cap rationale.** Source: `InternSync4.docx` —
  Jack said one week was fine or 30 days would also be fine, Anthony/Emma agreed,
  and region capacity constraints were called out. Reflected in
  `Explanations\internsync4-summary.md` and
  `FuturePlans\expiration-cap-30-days.md`; see those docs instead of duplicating
  the full meeting summary here.
- **Expiration/start dates are title-level configuration for each playtest, not a
  shared offering-level setting.** Source: `InternSync4.docx` — Jack said dates
  are configured on the individual title; Timi said xCloud has one title
  construct per playtest. Reflected in `Explanations\internsync4-summary.md`,
  `Explanations\expiration-cap-and-storage.md`, and
  `Explanations\ingestion-creates-new-things.md`.
- **Future start dates do not require a go-live ingestion trigger; xCloud can
  install before the live date.** Source: `InternSync4.docx` — Jack and Timi said
  install/provisioning can happen before the date as long as the title is not
  expired. Reflected in `Explanations\future-start-dates-and-provisioning.md` and
  `Explanations\internsync4-summary.md`.
- **Changing expiration is metadata/title configuration, not content re-ingest.**
  Source: `InternSync4.docx` — Jack said changing expiry is title configuration /
  xCloud metadata and content metadata is stored separately. Reflected in
  `Explanations\expiration-cap-and-storage.md` and
  `Explanations\internsync4-summary.md`.

### Player-facing UI decisions (Design Brainstorm — Playtest UX, 2026-06-30)

- **Playtest metadata comes from CAS hydration, not the retail Display Catalog ("big cat").**
  Source: `Design Brainstorm - Playtest UX.docx` — a private playtest product will never be in big
  cat; CAS instead gates and returns playtest content only to authorized members (matches the
  signed-out no-leak requirement). Bayside already calls `catalog.gamepass.com` with a versioned,
  codenamed hydration "contract" (gemstones — web ≈ "Sapphire"; the Bayside contract shown in chat
  was "Topaz 0"); each surface (Bayside / Garrison / console) has its own contract. Action (superseded
  2026-07-02 — see "CAS shipped playtest hydration" below): originally "ask CAS to extend the
  contract"; CAS has since shipped it, gated on the xToken playtest claim. Reflected in
  `FuturePlans\ui-steps-bayside.md` #6.
- **Playtests are a separate tab/section, not a library filter.** Source: same — the team explicitly
  moved away from "playtests are just a filter on your library" to a dedicated playtest tab shown only
  when the user has been assigned a playtest; an offering can contain more than one title, organized by
  offering name.
- **Playtest badge = white beaker on a pink box, lower-left, overlaying the tile art; also on the PDP
  next to the title.** Source: same — designed by Chris and reviewed by the design team; beaker+pink is
  the agreed treatment across surfaces for consistency (less critical with a dedicated playtest tab, but
  kept for consistency). Reference asset: `Documentation\playtest-badge-beaker.png`.
- **Playtest details page offers Stream now + Install (deep-links to Garrison), with a non-public
  banner.** Source: same — streaming starts directly (no install button needed to stream), but an
  install option that deep-links to Garrison is also wanted; a custom flash/flip card (install/play,
  stats on one side, product metadata on the flip) was prototyped.
- **In-game feedback via TCUI / user-research overlay (stretch).** Source: same — a pause-and-survey
  API the game implements (title-callable UI), richer than thumbs-up/down on the PDP.
- **A signed-out content-leak bug exists on Garrison.** Source: same — flagged live during the meeting;
  reinforces the #5 no-leak work.
- **People to enlist:** CAS hydration contract — **Oscar** (sponsor/support, not the implementer) and
  the **CAS team** via the Juno-side relationship (a CAS alias was dropped in the meeting chat for
  Melanie to reach out); badge/visual — **Chris** (designer) + design team; ECS feature-flag gating —
  **David Kushmerick**; `cloudConnect` offering-id — game-stream/auth package owners; install-vs-stream
  — Garrison/Bastion team.

### CAS shipped playtest hydration (CAS email thread, 2026-07-02)

- **CAS has already deployed playtest hydration.** Melanie was introduced to the CAS team, who
  confirmed they deployed code "this week" that makes **Playtest a standard access type** (the previous
  "optional" concept was removed). CAS returns playtest data whenever it detects a **new xToken user
  claim** the playtest team created; if the claim is present in the token, CAS calls for playtest data.
- **No CAS service work is required for Bayside.** CAS has **no client-specific contracts or
  endpoints** — "it is enabled right now, you just need to snag the new contract proto file." This
  **supersedes** the 6/30 action item ("ask CAS to extend the contract").
- **Next step / owner:** talk to **Anthony Keller** (heading up the playtest project) about **how to
  get the xToken playtest user claim added** to test tokens and any gotchas.
- **Bayside impact (verified in code):** the client is essentially already wired — the PDP hydrates via
  `CatalogSystem` (`packages/@play-xbox/-system/catalog/src/CatalogSystem.ts`), which already
  special-cases private offerings (skeleton-from-title-info fallback + `augment*ForPrivateOffering`), and
  the vendored hydration contract `BaysideLowTopaz0`
  (`packages/@xbox-js/-service-sdk/catalog/src/hydration/baysideTypes.ts`) already carries `title`,
  `KeyArt` (art) and `Categories` (genre). Once the caller's token carries the playtest claim, the
  existing product detail page should render the metadata with little/no new FE code; only snag the new
  proto if CAS added fields.

## Transcript coverage notes

- `Aditya1.docx` — extracted, no substantive design content.
- `InternSync1.docx` — additive streaming model, launch-link readiness, retries,
  cross-tenant callback concern, initial DNA/title-id discussion.
- `InternSync2.docx` — Xbox Live title-id lookup, DNA/group-id propagation and
  debugging, cross-tenant/PME concern.
- `InternSync3.docx` — PC polling need, async workflow waiting, ECS/private
  preview gating.
- `InternSync4.docx` — summarized in `Explanations\internsync4-summary.md`.
- `Jack1.docx` — xCloud service map, SAGE routing, product/title ingestion, PR
  approval/rubber-stamp gap.
- `Jack2.docx` — auth identity model, DNA group contract, Edgewater/Garrison/
  Bayside distinction.
- `Timi.docx` — xCloud ingestion phases, StoreAsset fields, Partner Registry
  availability/audience, POST plus status GET.
- `XCloudIngestion.docx` — PC install/readiness behavior, PC playtest SUG/quota,
  Orchestrator polling direction, MVP skip-poll option, offering/title id shape.
- `Design Brainstorm - Playtest UX.docx` (2026-06-30) — player-facing UI: CAS
  hydration for playtest metadata (not big cat), separate playtest tab, beaker+pink
  badge, install-vs-stream, in-game surveys/TCUI, and a signed-out no-leak bug.
