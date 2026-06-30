# Instantly Shareable Playtest — Tracking Hub

A documentation and tracking hub for the **Instantly Shareable Playtest** feature
(**xPlaytest × xCloud streaming**). It is the single source of truth for the work: every pull request,
cross-team decision, bug, blocker, and plan for what comes next — kept current with a small fleet of
automation agents so the next engineer can pick up exactly where the project left off.

> Maintained by Melanie Chen (@t-melanichen) during the Instant Playtest internship.
> For long-term ownership and migration, see **[`Offboarding.md`](./Offboarding.md)**.

---

## What the feature is

Instant Playtest lets a **game creator share an unreleased build** that an **invited tester streams from
the cloud in seconds** — no multi-gigabyte install. The backend threads a build through five stages:

> **audience** (who may see it) → **offering** (publish it) → **ingestion** (load it into xCloud) →
> **PC server lane** (give it machines) → **readiness** (confirm it can stream) → **share link**.

For a plain-English walkthrough of every PR in that chain, see
**[`PC-Polling-Status.md`](./PC-Polling-Status.md)** and **[`Explanations/`](./Explanations/)**.

---

## Start here

| If you want to… | Go to |
|-----------------|-------|
| Understand the current state of the project | **[`PC-Polling-Status.md`](./PC-Polling-Status.md)** — consolidated status |
| See how the system works end to end | **[`Explanations/`](./Explanations/)** |
| Find what a specific PR did | **[`PRProgress/README.md`](./PRProgress/README.md)** — one file per PR |
| See per-repo changes | **[`Repos/README.md`](./Repos/README.md)** |
| Pick up the remaining work | **[`FuturePlans/`](./FuturePlans/)** + **[`Blockers/`](./Blockers/)** |
| Read the original project brief | **[`Context/`](./Context/)** (intern project doc, spec, intro deck) |
| Hand the repo off to the team | **[`Offboarding.md`](./Offboarding.md)** |

---

## Repository map

| Path | Contents |
|------|----------|
| **[`PC-Polling-Status.md`](./PC-Polling-Status.md)** | Consolidated, current status of the PC streaming-readiness work: every PR, what's done, open items, and what's next. The best single starting point. |
| **[`PRProgress/`](./PRProgress/README.md)** | One file per meaningful pull request (id, repo, branch, status, summary), indexed by its README. |
| **[`Repos/`](./Repos/README.md)** | Per-repo change logs: the role each repo plays, branches, PRs, and forward work. |
| **[`Explanations/`](./Explanations/)** | How the system works — end-to-end flow, cross-team decision ledger distilled from sync transcripts, and design rationale. |
| **[`FuturePlans/`](./FuturePlans/)** | Scoped, forward-looking plans for remaining and deferred work (UI steps, console migration, region routing, expiration cap, feature flags, and more). |
| **[`Blockers/`](./Blockers/)** | Known blockers and open dependencies with context and owners. |
| **[`Documentation/`](./Documentation/)** | As-built spec deltas (how the implementation diverged from the original spec). |
| **[`Context/`](./Context/)** | Source project materials: the intern project document, implementation spec, and intro deck. |
| **[`Playtest-UI-Meeting-Karla-Kush.md`](./Playtest-UI-Meeting-Karla-Kush.md)** | Prep for the playtest UI design/scope meeting: planned changes to both front ends + discussion topics. |
| **[`Offboarding.md`](./Offboarding.md)** | Plan to migrate this hub to GitHub EMU and permission it to the Juno team. |
| **[`AGENTS.md`](./AGENTS.md)** | Maintenance guide: source-of-truth order, the agent fleet, Juno board facts, and conventions. |
| **[`.github/agents/`](./.github/agents/README.md)** | The Copilot agent fleet that keeps this hub current, plus the repo-access manifest. |
| **[`scripts/`](./scripts/README.md)** | Automation, incl. `sync-pr-progress.ps1` which reconciles the PR ledger against live Azure DevOps. |

---

## Status snapshot

- **PRs:** 24 tracked — **19 merged, 2 active, 3 draft** (see [`PRProgress/README.md`](./PRProgress/README.md) for the live ledger).
- **Spine merged to `main`:** audience model, offering + title-id, the ingestion workflow, the PC server lane, the readiness poll, and the resolution fix.
- **Remaining:** the SAGE send/poll loop, the Partner Center creator toggle, the Bayside launch surface, and the UI work tracked in [`FuturePlans/`](./FuturePlans/).

---

## How this hub stays current

The hub is largely self-maintaining:

- **`scripts/sync-pr-progress.ps1`** queries live Azure DevOps PRs and reconciles them against the
  `PRProgress/` ledger, flagging anything missing or out of date.
- A **fleet of Copilot agents** under [`.github/agents/`](./.github/agents/README.md) keeps PR status, repo
  notes, transcript decisions, and the spec deltas fresh.

Run them per the cadence in [`AGENTS.md`](./AGENTS.md). They require `az` login with Azure DevOps access
(Code: Read, Work Items: Read).

---

## Conventions

- **Branches:** `t-melanichen/<topic>`.
- **Work items:** referenced as `ADO#<id>`; the project lives on the ADO **Juno** board
  (`microsoft/Xbox`, area path `Xbox\Developer\Juno`, scenario `62490517`). Cancel state is `Cut`.
- **Local-only content:** `Connect/` (internship Connect docs) and `Transcripts/` (meeting recordings) are
  **git-ignored** — they contain personal/sensitive material and are kept locally, not pushed.

---

## Handoff

This repo currently lives under a personal corp GitHub account. Before offboarding it should move to
**GitHub EMU** and be permissioned to the **Juno team** and stakeholders. The full plan, steps, and open
questions are in **[`Offboarding.md`](./Offboarding.md)**.
