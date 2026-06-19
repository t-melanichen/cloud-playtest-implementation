# Copilot agent fleet

This repo is a documentation and tracking hub for Instantly Shareable Playtest. A small fleet of Copilot CLI agents
keeps PR status, repo notes, transcript decisions, and the external spec fresh.

## Agents

| Agent | Purpose | Owns | Invoke when |
|---|---|---|---|
| `playtest-streaming` | Domain expert for xPlaytest × xCloud streaming. | Cross-repo design, implementation guidance, conventions. | You need project context or code/design help across repos. |
| `pr-progress-sync` | Keeps the PR ledger aligned with live ADO. | `PRProgress\`, PR summaries, merged/active/draft status. | After opening, updating, merging, or abandoning PRs. |
| `staleness-auditor` | Finds stale docs and drift. | Freshness checks across hub docs. | Weekly, or before sharing status. |
| `transcript-considerations` | Converts sync-meeting transcripts into decisions and follow-ups. | `Explanations\transcript-decisions.md` and related notes. | After each sync meeting transcript lands. |
| `spec-maintainer` | Reconciles the external implementation spec with as-built reality. | Desktop `.docx` spec and `Documentation\spec-updates\` changelogs. | Before milestones or after major PRs merge. |

## Repo-access manifest

Agent files do **not** grant cross-repo access. The user must `/add-dir` the needed repos, or run from a session that
already has them.

| Repo | ADO project | Local clone path (Desktop\...) | Feature branch | PRs | Role |
|---|---|---|---|---|---|
| services.partnerregistry | Xbox.Streaming | `services.partnerregistry` | `t-melanichen/refactor-title-id` | 8 | Offering+title config, AllowedDnaGroups, ConfigurePlaytestAsync, title id, regions |
| Xbox.Xbet.Service | Xbox | `Xbox.Xbet.Service` | `t-melanichen/playtest-ingestion-payload-builder` | 6 | xPlaytest publish workflow, StoreAsset + payload builder, SAGE call, polling, title-id resolver |
| services.contentingestion | Xbox.Streaming | `services.contentingestion` | `t-melanichen/playtest-pc-install-polling` | 3 | PlaytestTitleIngestionWorkflow, V3 routes, PC install polling, cross-tenant S2S |
| services.contenttargets | Xbox.Streaming | `services.contenttargets` | `t-melanichen/pc-playtest-install-on-attach` | 1 (draft) | PC playtest install-on-attach + server quota: PC_PLAYTEST SUG enablement (IncludePredictions override + QuotasBySugByRegion) so attaching the title triggers the install CTIN polls for |
| services.devapi | Xbox.Streaming | `services.devapi` | `t-melanichen/testing-workflow-ingestion` | 2 | DevApi Reader portal: DNA-groups UI + ingestion testing UI |
| services.serviceapigateway | Xbox.Streaming | `services.serviceapigateway` | `t-melanichen/sage-playtest-ingestion-routes` | 2 | SAGE proxy routes (cross-tenant Green→Corp) |
| services.auth | Xbox.Streaming | `services.auth` | `t-melanichen/xc5a-enforce-allowed-dna-groups` | 1 | Enforce AllowedDnaGroups in offering login |
| services.data.partnerregistry | Xbox.Streaming | _(no local clone)_ | — | 1 | OfferingV2.json DNATEST allowed group |
| xorc | Xbox.Services | `xorc-1` (feature branch); `xorc` is on `develop` | `t-melanichen/playtest-xbox-live-title-id` | 1 | Xbox Live service-config read API → numeric XboxTitleId |
| Xbox.Gpx.PartnerCenter.Client | Xbox | `Xbox.Gpx.PartnerCenter.Client` | `t-melanichen/pc-s2s-cing-token` | 0 (planned) | Partner Center creator UI: streaming toggle, duration cap, audience restriction |
| Xbox.JS | Xbox | `Xbox.JS` | `main` (no branch yet) | 0 (planned) | Player-side Bayside launch surface |

Reference-only clones: `services.pcservices`, `services.pcservices-1`, `services.permissions`, and
`streamable-xplaytest`.

Full `/add-dir` recipe:

```text
/add-dir "C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\Xbox.Xbet.Service"
/add-dir "C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\services.contentingestion"
/add-dir "C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\services.contenttargets"
/add-dir "C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\services.serviceapigateway"
/add-dir "C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\services.partnerregistry"
/add-dir "C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\services.auth"
/add-dir "C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\services.devapi"
/add-dir "C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\Xbox.Gpx.PartnerCenter.Client"
/add-dir "C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\Xbox.JS"
/add-dir "C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\xorc-1"
```

## Keeping the hub fresh

- Run `pr-progress-sync` after opening, merging, drafting, or abandoning PRs. Use `scripts\sync-pr-progress.ps1` for
  the scripted PRProgress sync path.
- Run `staleness-auditor` weekly and before status reviews.
- Run `transcript-considerations` after each sync meeting.
- Run `spec-maintainer` before milestones and after major merged PR batches.

## Prerequisites

- `az` logged in as `t-melanichen@microsoft.com`, or an ADO PAT with Code:Read and Work Items:Read, for live ADO.
- `python-docx` for the external implementation spec.
