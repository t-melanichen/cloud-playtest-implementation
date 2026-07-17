# PR Progress — Instantly Shareable Playtest

Tracker for every meaningful pull request @t-melanichen has started or completed on the Instantly Shareable
Playtest project (xPlaytest × xCloud streaming). One file per PR, all titled with the same format:

`# [<AREA>] PR <id> — <PR title>`

Each file records: Pull Request id, Repo (project), source → target branch, Status, open/close dates,
a direct link, and a Summary.

**Ordering:** The table below is listed in **chronological order (by PR creation)**. The numeric prefix on
each file (e.g. `13-…`) reflects the order the PR was *added to this tracker*, not its chronological slot —
so the on-disk file numbers are not strictly ascending in the table. Click a title to open its file.

| # | PR | Area | Repo | Status | Title |
|---|----|------|------|--------|-------|
| 01 | 15732852 | PTNR | services.partnerregistry | Merged | [Add AllowedDnaGroups to PlayerAuthorizationOptions](./01-PTNR-15732852-add-allowed-dna-groups.md) |
| 02 | 15738761 | AUTH | services.auth | Merged | [XC5.a: Enforce AllowedDnaGroups in user login authorization](./02-AUTH-15738761-enforce-allowed-dna-groups-login.md) |
| 03 | 15739964 | DEVAPI | services.devapi | Merged | [Add Allowed DNA Groups field to Offering edit page](./03-DEVAPI-15739964-allowed-dna-groups-offering-edit.md) |
| 04 | 15751527 | PTNR-DATA | services.data.partnerregistry | Merged | [Updated OfferingV2.json (DNATEST allowed DNA group)](./04-PTNR-DATA-15751527-offeringv2-dnatest-allowed-group.md) |
| 05 | 15773366 | PTNR | services.partnerregistry | Merged | [New Playtest Endpoint](./13-PTNR-15773366-new-playtest-endpoint.md) |
| 06 | 15800964 | CTIN | services.contentingestion | Merged | [Playtest Title Ingestion Workflow](./05-CTIN-15800964-playtest-title-ingestion-workflow.md) |
| 07 | 15815668 | PTNR | services.partnerregistry | Merged | [Configure playtest offering regions and id naming](./14-PTNR-15815668-configure-offering-regions-id-naming.md) |
| 08 | 15821813 | PTNR | services.partnerregistry | Merged | [Centralize playtest offering id on PlaytestRequest.GetOfferingId](./15-PTNR-15821813-centralize-offering-id-on-request.md) |
| 09 | 15829639 | SAGE | services.serviceapigateway | Merged | [Register Playtest ingestion proxy routes for services.contentingestion](./06-SAGE-15829639-register-playtest-ingestion-routes.md) |
| 10 | 15834601 | XBET | Xbox.Xbet.Service | Merged | [Playtest Ingestion Payload Builder](./07-XBET-15834601-playtest-ingestion-payload-builder.md) |
| 11 | 15849944 | PTNR | services.partnerregistry | Merged | [Remove GetPackageSourceId from Playtest contract](./08-PTNR-15849944-remove-getpackagesourceid.md) |
| 12 | 15860243 | PTNR | services.partnerregistry | Merged | [Refactor playtest title ID](./09-PTNR-15860243-refactor-playtest-title-id.md) |
| 13 | 15876080 | DEVAPI | services.devapi | Active | [Testing workflow ingestion (Playtest Title Ingestion UI/client)](./10-DEVAPI-15876080-testing-workflow-ingestion.md) |
| 14 | 15892276 | PTNR | services.partnerregistry | Merged | [Set Xbox AuthenticationOptions on playtest offerings](./11-PTNR-15892276-playtest-offering-authentication-type.md) |
| 15 | 15894506 | XORC | xorc | Merged | [Expose Xbox Live TitleId on the product Xbox Live config response](./16-XORC-15894506-expose-xbox-live-title-id.md) |
| 16 | 15896502 | CTIN | services.contentingestion | Merged | [Implement PC install-readiness polling in PlaytestTitleIngestionWorkflow](./17-CTIN-15896502-pc-install-readiness-polling.md) |
| 17 | 15905881 | CTIN | services.contentingestion | Merged | [Gate playtest title ingestion endpoints with CrossTenantS2S policy](./12-CTIN-15905881-gate-playtest-ingestion-crosstenant-s2s.md) |
| 18 | 15949594 | PTNR | services.partnerregistry | Merged | [Set PC_PLAYTEST SUG on the playtest offering](./19-PTNR-15949594-playtest-offering-sug.md) |
| 19 | 15965750 | PTNR-DATA | services.data.partnerregistry | Merged | [Add PCSystemUpdateGroup /PCSystemUpdateGroups/PC_PLAYTEST (Test)](./20-PTNR-DATA-15965750-add-pc-playtest-sug-test.md) |
| 20 | 15965763 | PTNR-DATA | services.data.partnerregistry | Merged | [Add PCSystemUpdateGroup /PCSystemUpdateGroups/PC_PLAYTEST (Int)](./21-PTNR-DATA-15965763-add-pc-playtest-sug-int.md) |
| 21 | 15966616 | DCFG | services.data.partnerregistry | Merged | [Update CONTENTTARGETS/DEFAULT/SERVERSETSCONFIGURATION — PC_PLAYTEST quota (Int)](./22-DCFG-15966616-contenttargets-pc-playtest-quota.md) |
| 22 | 15996626 | CTIN | services.contentingestion | Merged | [Accept bare-GUID audience for cross-tenant v1.0 tokens](./23-CTIN-15996626-crosstenant-audience-validation-fix.md) |
| 23 | 15983599 | CTIN | services.contentingestion | Merged | [Don't scope playtest resolution package search to the GA flight](./24-CTIN-15983599-resolution-no-ga-flight.md) |
| 24 | 15946761 | GPM | Xbox.Gpx.PartnerCenter.Client | Draft | [Enable Playtest Cloud Streaming (Partner Center form toggle)](./25-GPM-15946761-enable-cloud-streaming-toggle.md) |
| 25 | 16103484 | PTNR-DATA | services.data.partnerregistry | Merged | [Add PCSystemUpdateGroup /PCSystemUpdateGroups/PC_PLAYTEST (Prod)](./26-PTNR-DATA-16103484-add-pc-playtest-sug-prod.md) |
| 26 | 16103771 | DCFG | services.data.partnerregistry | Merged | [Update CONTENTTARGETS/DEFAULT/SERVERSETSCONFIGURATION — PC_PLAYTEST quota (Prod)](./27-DCFG-16103771-contenttargets-pc-playtest-quota-prod.md) |
| 27 | 16114214 | DCFG | services.data.partnerregistry | Merged | [Add CONTENTTARGETS/DEFAULT/RESOLUTIONCONFIGURATION — IncludePredictions PC_PLAYTEST (Prod)](./28-DCFG-16114214-contenttargets-includepredictions-prod.md) |
| 28 | 16114118 | DCFG | services.data.partnerregistry | Merged | [Update CONTENTDISTRIBUTION/DEFAULT/ORCHESTRATIONCONFIG — IncludePredictedTargets PC_PLAYTEST (Prod)](./29-DCFG-16114118-contentdistribution-includepredictedtargets-prod.md) |
| 29 | 16112987 | PTNR | services.partnerregistry | Merged | [Set DefaultAllocationPools on PC playtest offering](./30-PTNR-16112987-playtest-default-allocation-pools.md) |
| 30 | 16102792 | XBET | Xbox.Xbet.Service | Active | [Pin playtest ingestion to Americas SAGE](./31-XBET-16102792-pin-playtest-ingestion-americas.md) |
| 31 | 16130422 | XBET | Xbox.Xbet.Service | Merged | [Send playtest ContentId to streaming ingestion (fixes install ERROR_NOT_FOUND)](./32-XBET-16130422-playtest-real-contentid.md) |
| 32 | 16129840 | CTIN | services.contentingestion | Merged | [Add ContentId to AssetProperties; ingest under SourceId (part of ContentId fix)](./33-CTIN-16129840-assetproperties-contentid.md) |
| 33 | 16137972 | CTDR | services.contentdistribution | Merged | [Separate SourceId from ContentId — SourceId for Sourcing, real ContentId for Distribution commands](./34-CTDR-16137972-separate-sourceid-contentid.md) |
| 34 | 16139815 | PTNR-DATA | services.data.partnerregistry | Merged | [Set DefaultAllocationPools PC=PC_MAIN on offering XPT2SDT4X91KRR7](./35-PTNR-DATA-16139815-offering-default-allocation-pools.md) |
| 35 | 16140301 | SESSIONS | services.sessions | Active | [Separate ContentId from SourceId — use explicit ContentId for provisioning (part of ContentId fix)](./36-SESSIONS-16140301-separate-contentid-sourceid.md) |
| 36 | 16158158 | XORC | xorc | Active | [Add populated XboxLiveTitleConfig branch coverage (ProductXboxLiveConfigurationHandler)](./37-XORC-16158158-populated-titleconfig-coverage.md) |

**Totals (live-verified 2026-07-13):** 36 tracked PRs — **31 merged**, **4 active** (DEVAPI 15876080, XBET pin 16102792, SESSIONS 16140301, XORC 16158158), **1 draft** (GPM 15946761). The **ContentId fix** (playtest streaming sent the SUCU servicing id where the real content id was needed) spans 5 PRs: STORECLIENT 16128230, XBET 16130422, CTIN 16129840, CTDR 16137972 (all merged) and SESSIONS 16140301 (active). With those, the build **installs + provisions** on the PC server (the `ERROR_NOT_FOUND` install blocker is resolved — see [install blocker](../Blockers/pc-playtest-msixvc-install-error-not-found.md)). The current blocker is now a **server-side GRTS build issue** causing the cloud launch to time out — see [launch-timeout blocker](../Blockers/pc-playtest-launch-timeout-grts.md). Xbet pin 16102792 (Americas SAGE routing) is still active; deploys otherwise paused until the Monday window.

**Status legend:** Merged = completed/merged · Active = open and in review · Draft = open draft.

**Area legend:** PTNR = services.partnerregistry · PTNR-DATA = services.data.partnerregistry (offering / SUG-definition data) ·
AUTH = services.auth · DEVAPI = services.devapi · CTIN = services.contentingestion ·
SAGE = services.serviceapigateway · XBET = Xbox.Xbet.Service · XORC = xorc (Xbox.Services) ·
CTGT = services.contenttargets · DCFG = services.data.partnerregistry (dynamic config — CONTENTTARGETS ServerSetsConfiguration / ResolutionConfiguration, CONTENTDISTRIBUTION OrchestrationConfig) ·
CTDR = services.contentdistribution (content distribution — server install/distribution commands) ·
SESSIONS = services.sessions (streaming session provisioning) ·
GPM = Xbox.Gpx.PartnerCenter.Client (Partner Center creator UI) · JS = Xbox.JS (Bayside player client).

## Superseded / abandoned PRs

Earlier exploratory PRs that were abandoned once a better approach landed, kept here for a complete record.
Most have no individual file; where a PR carried substantial design/test context (e.g. 15946980) its file is
retained and linked. (Trivial throwaway PRs — `g`, `Remove Hyphen`, `Unused PR` — are omitted.)

| PR | Area | Repo | Closed | Title & why superseded |
|----|------|------|--------|------------------------|
| 15680234 | XBET | Xbox.Xbet.Service | 2026-05-31 | *feat(PlayTest): add Partner Registry offering publish (Path B / AllowedFlights)* — early in-PlayTest scaffold using **Path B** (`AuthorizationOptions.AllowedFlights`); superseded by the **AllowedDnaGroups (Path A)** audience model (PRs 15732852 / 15738761 / 15739964). |
| 15733268 | XBET | Xbox.Xbet.Service | 2026-06-02 | *Add PlaytestIngestionJobParameters + StoreAsset contracts* — early hand-written local wire contracts; superseded by PR 15834601 (payload builder) and the move to consume the published GSSV contract (board task 62696974). |
| 15737351 | SAGE | services.serviceapigateway | 2026-06-16 | *Register Playtest ingestion proxy routes* — first attempt at the SAGE proxy routes; superseded by PR 15829639 (the live routes PR, #09 above). |
| 15946980 | CTGT | services.contenttargets | 2026-06-22 | *[Tests-only: PC playtest enable + quota moved to dynamic config](./18-CTGT-15946980-pc-playtest-install-on-attach.md)* — checked-in `appsettings` quota was reverted per Timi; superseded by the **dynamic-config** quota PR 15966616 (Int, #21 above). File retained for its 3 regression tests. |
| 15946666 | JS | Xbox.JS | 2026-06-19 | *feat(play-xbox/game-stream): apply launch-link offeringId to the active offering* — Bayside "C1" wire that set the shared-link `offeringId=xpt{ProductId}` as the active offering before streaming (so a playtest link streams the private DNA-gated offering, not retail). Draft, later abandoned; the Bayside player-flow work is tracked in [`../FuturePlans/bayside-playxbox-playtest-modifications.md`](../FuturePlans/bayside-playxbox-playtest-modifications.md). |
