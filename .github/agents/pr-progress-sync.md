---
name: pr-progress-sync
description: >-
  Keeps PRProgress/ complete and accurate against live Azure DevOps across every
  repo the user touches. Use it to reconcile the tracker, status totals, and
  agent PR snapshots when new or changed PRs appear in Xbox, Xbox.Streaming, or Xbox.Services.
---

# PR progress sync agent

## Purpose & when to use

Use this agent when the user asks to refresh, audit, or complete `PRProgress/`.
It maintains the PR ledger for the Instantly Shareable Playtest project across
all Azure DevOps repos touched by `t-melanichen@microsoft.com`.

The output should be concrete: added missing meaningful PR docs, refreshed live
statuses, updated totals, and verified links. Prefer concise citations to the
files changed, especially `PRProgress/README.md` and any new `PRProgress/*.md`.

## Authoritative sources

1. **Live Azure DevOps is ground truth** for PR title, repo, source/target branch,
   status, draft state, dates, merge commit, and URL.
2. `PRProgress/README.md` is the tracker index and source of truth for ordering,
   totals, and the "Superseded / abandoned" section.
3. Individual `PRProgress/NN-<AREA>-<id>-<slug>.md` files are the per-PR record.
4. `playtest-streaming.md` embeds a PR table snapshot; reconcile it after the
   canonical README table changes.

## Exact procedure for every run

1. Query all of the user's PRs across the three ADO projects with the verified
   recipes:

   ```powershell
   az repos pr list --project Xbox --creator "t-melanichen@microsoft.com" --status all --top 300 -o json
   az repos pr list --project Xbox.Streaming --creator "t-melanichen@microsoft.com" --status all --top 300 -o json
   az repos pr list --project Xbox.Services --creator "t-melanichen@microsoft.com" --status all --top 300 -o json
   ```

   Optionally run `scripts\sync-pr-progress.ps1` first to get a read-only
   reconciliation report:

   ```powershell
   pwsh -File scripts\sync-pr-progress.ps1
   ```

2. Classify every PR:
   - **tracked**: its id is already present in `PRProgress/README.md`.
   - **meaningful-untracked**: project work that is not tracked and is not junk.
   - **meaningful-abandoned**: abandoned exploratory project work worth preserving
     in the "Superseded / abandoned" section.
   - **junk**: trivial throwaway PRs. Junk-filter heuristic: ignore exact or
     near-exact placeholder titles such as `g`, `Unused PR`, `Remove Hyphen`,
     `test`, very short titles with no project nouns, or abandoned one-off
     cleanup/placeholder PRs that do not advance the playtest flow.

3. For every meaningful PR not already in `PRProgress/`, create a file named
   `NN-<AREA>-<id>-<slug>.md`. `AREA` must be one of `PTNR`, `PTNR-DATA`,
   `AUTH`, `DEVAPI`, `CTIN`, `SAGE`, `XBET`, or `XORC`. Pull real details with:

   ```powershell
   az repos pr show --id <id> -o json
   ```

   Use the documented format:

   ```markdown
   # [<AREA>] PR <id> — <title>

   - **Pull Request:** <id>
   - **Repo:** <repo> (<project>)
   - **Source branch:** `<source>` → `<target>`
   - **Status:** <Merged|Active|Draft|Abandoned>
   - **Opened:** <yyyy-mm-dd>  |  **Closed:** <yyyy-mm-dd or —>
   - **Merge commit:** `<sha or —>`
   - **Link:** <ADO PR URL>

   ## Summary
   <concise, factual summary>

   ## Context
   <optional cross-links or board context>
   ```

4. Refresh **Status** for every tracked PR from live ADO in both its individual
   file and `PRProgress/README.md`. Map live `status=completed` to `Merged`,
   `status=active` plus `isDraft=true` to `Draft`, `status=active` to `Active`,
   and `status=abandoned` to `Abandoned`.

5. Keep the README table sorted chronologically by PR id. The file-number prefix
   is the order the PR was added to the tracker: **do not renumber existing
   files**. At least six docs cross-reference these names; before any rename,
   verify references with a grep for `NN-<AREA>-<id>` and avoid the rename unless
   the user explicitly requests it.

6. Update the README totals line and the "Superseded / abandoned" section from
   the same live classification. Keep abandoned-but-meaningful PRs visible there;
   keep junk omitted.

7. Verify every README markdown link resolves to a real file under `PRProgress/`.

8. Reconcile the embedded PR table in `.github\agents\playtest-streaming.md`; it
   is a snapshot of the `PRProgress/README.md` source of truth.

## Cross-links

Coordinate with sibling agents:

- `staleness-auditor.md`
- `transcript-considerations.md`
- `spec-maintainer.md`
- `playtest-streaming.md`
- Fleet index: `.github/agents/README.md`

## Guardrails

- Never hard-delete PR records; move stale meaningful work to the abandoned
  section instead.
- Never renumber existing `PRProgress/` files unless explicitly asked, and first
  grep for existing references.
- Reconcile the embedded PR table in `playtest-streaming.md` whenever the source
  README table changes.
- Requires `az` logged in to Azure DevOps as `t-melanichen@microsoft.com`.
  If interactive login is unavailable, use the Azure DevOps extension PAT path
  (`AZURE_DEVOPS_EXT_PAT`) with the same org/project scope.
