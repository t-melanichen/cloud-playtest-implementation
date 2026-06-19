# Repos — per-repository change log (Instantly Shareable Playtest)

One file per repository that @t-melanichen has modified or will modify for the **Instantly Shareable
Playtest** project (xPlaytest × xCloud streaming). Each file lists **changes made** (reconstructed from
local git history + branches, cross-referenced with `../PRProgress/`) and **planned / remaining
changes** (from `../Blockers/` and `../FuturePlans/`).

> Source of truth for live PR status remains [`../PRProgress/`](../PRProgress/README.md). These files
> add the per-repo git/branch detail and the forward-looking work.

| Repo | Area | Role | Doc |
|---|---|---|---|
| services.partnerregistry | PTNR | Offering + title config; `AllowedDnaGroups`/`AllowedSandboxId`, `ConfigurePlaytestAsync`, playtest title id, studio regions | [services.partnerregistry.md](./services.partnerregistry.md) |
| services.auth | AUTH | Enforces `AllowedDnaGroups` + gamertag claim in offering login (`/v2/login/user/delegated`) | [services.auth.md](./services.auth.md) |
| services.contentingestion | CTIN | `PlaytestTitleIngestionWorkflow`, V3 routes, PC install polling, cross-tenant auth | [services.contentingestion.md](./services.contentingestion.md) |
| services.contenttargets | CTGT | PC playtest install-on-attach + server quota (PC_PLAYTEST SUG) — the upstream that makes CTIN's PC readiness poll succeed | [services.contenttargets.md](./services.contenttargets.md) |
| services.devapi | DEVAPI | DevApi Reader portal: Allowed DNA Groups UI + playtest ingestion testing UI | [services.devapi.md](./services.devapi.md) |
| services.serviceapigateway | SAGE | Gateway proxy routes (cross-tenant Green→Corp, auth pass-through) for ingestion | [services.serviceapigateway.md](./services.serviceapigateway.md) |
| Xbox.Xbet.Service | XBET | xPlaytest publish workflow: payload builder, SAGE call, status polling, title-id resolver | [Xbox.Xbet.Service.md](./Xbox.Xbet.Service.md) |
| Xbox.Gpx.PartnerCenter.Client | GPX | Partner Center creator UI on `t-melanichen/pc-s2s-cing-token`: streaming-enable toggle, duration cap, audience restriction | [Xbox.Gpx.PartnerCenter.Client.md](./Xbox.Gpx.PartnerCenter.Client.md) |
| xorc (xorc-1) | XORC | Xbox Live service-config read API — resolves numeric `XboxTitleId` | [xorc.md](./xorc.md) |
| Xbox.JS | BAYSIDE | Player-side cloud-gaming client (play-xbox); launch-link → offering streaming (**planned, no branch yet**) | [Xbox.JS.md](./Xbox.JS.md) |

## Notes
- **Refreshed 2026-06-18** from local clones on the Desktop + the `PRProgress/`, `Blockers/`, and
  `FuturePlans/` docs, with live Azure DevOps PR status reconciled via `az`.
- Branch naming convention: all feature branches are prefixed `t-melanichen/`.
- "Changes made" claims are based on actual `git log`/`git diff --stat` against each repo's base branch.
- `services.data.partnerregistry` (PR 04, OfferingV2 DNATEST group) had no separate local clone; its PR
  is tracked in [`../PRProgress/04-PTNR-DATA-15751527-offeringv2-dnatest-allowed-group.md`](../PRProgress/04-PTNR-DATA-15751527-offeringv2-dnatest-allowed-group.md).
- **Open code TODOs / FIXMEs** were scanned from each branch's diff (added `+` lines containing
  `TODO`/`FIXME`/`HACK`/`XXX`) and added as an "Open code TODOs / FIXMEs (in-branch)" section in the
  repos that have them: **services.contentingestion**, **Xbox.Xbet.Service**, **services.partnerregistry**.
  No in-branch TODOs were found in services.auth, services.devapi, services.serviceapigateway,
  Xbox.Gpx.PartnerCenter.Client, or xorc.
- **ADO / Juno board linkage** comes from work-item numbers embedded in those TODO comments
  (xbet cites `AB#62492628`, `AB#62521457`, `AB#62684638`, `AB#62696974`; contentingestion references
  `62492680`, `62521491`, `62688258`). Live PR status and Juno work items can be refreshed with the
  current `az` Azure DevOps login.
