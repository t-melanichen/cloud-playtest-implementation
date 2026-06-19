# Repository maintenance guide

This repo is the tracking hub for Instantly Shareable Playtest: xPlaytest publishing into xCloud streaming, plus
supporting Partner Registry, content ingestion, SAGE, auth, DevApi, XORc, Partner Center, and player-surface work.

## Source-of-truth order

1. Live ADO PRs and the Juno board.
2. `PRProgress\` — one file per meaningful PR, indexed by `PRProgress\README.md`.
3. `Repos\` — per-repo branch/change logs and forward work.
4. `Blockers\` and `FuturePlans\` — unresolved and deferred work.
5. `Connect\` — internship Connect docs; `02-midpoint-connect.md` is current.
6. Desktop spec: `C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\Instantly Shareable Playtest - Updated Implementation Spec (polished).docx`.

## Agent fleet

See `.github\agents\README.md` for the custom-agent index, repo-access manifest, `/add-dir` recipe, workflow cadence,
and prerequisites. Agent files do not grant cross-repo access by themselves.

## Juno board facts

- ADO project: `microsoft/Xbox`.
- Area path: `Xbox\Developer\Juno`.
- Scenario 62490517: `[Internship] Instant Playtest`.
- Deliverables: PT1-PT6 and XC1-XC4.
- Cancel state is `Cut`, not `Removed`.

## Branch convention

Use `t-melanichen/...` for feature branches.
