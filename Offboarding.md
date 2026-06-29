# Offboarding / handoff of this hub

**Owner:** Melanie Chen (@t-melanichen) · **Status:** Planning — do **before** corp account deactivation.

## Why
This repo is the single source of truth for the streamable-playtest work: PRs, sync decisions, bug fixes,
blockers, future plans, and the agent fleet. It currently lives under my **personal corp GitHub account**
(`github.com/t-melanichen/cloud-playtest-implementation`), so it would be lost to the team when I offboard.
It needs a permanent, team-owned home.

## Guidance (from Brian Bowman)
- Eventually **push it to GitHub EMU** (Microsoft's managed GitHub Enterprise) somewhere team-owned.
- **Permission it to the Juno team + others** (xCloud / xPlaytest stakeholders).
- Reference: GitHub inside Microsoft — <https://eng.ms/docs/more/github-inside-microsoft/overview>

## Plan
1. **Pick the target EMU org/owner.** Identify the right GitHub EMU org for Juno/xPlaytest and a long-term
   owner who stays after I leave (confirm with Brian / Kush). Per the eng.ms "GitHub inside Microsoft" guide.
2. **Create the repo in EMU** (or have the owner create it) under that org.
3. **Migrate full history** before my account is deactivated:
   ```bash
   git remote add emu <emu-repo-url>
   git push emu --mirror        # all branches + tags + history
   ```
   (Default branch in EMU = `main`; consolidate the current `feature/...` branch into `main` first.)
4. **Permission the Juno team + others** (Brian, Timi, Anthony, Kush, xCloud/xPlaytest) with appropriate
   read/write access via the EMU team, not individual grants where possible.
5. **Update pointers:** set the EMU repo as canonical in `README` / `AGENTS.md`; note the old personal repo
   is archived/read-only and redirect contributors.
6. **Re-verify the agent fleet + scripts** (`.github/agents/`, `scripts/sync-pr-progress.ps1`) work for a new
   owner — they need `az` login + ADO access (Code:Read, Work Items:Read). Flag that ADO/eng.ms links in the
   docs require corp access.
7. **Hand off ownership** of the open ADO follow-ups (e.g. AB#62907255, AB#62907370) and the FuturePlans
   backlog to the long-term owner.

## Open questions
- Which **EMU org** is correct for this, and **who creates/owns** it after I leave?
- Do we want **history preserved** (mirror push) or a clean import?
- Any content that must be scrubbed before it leaves the personal account (none expected — no secrets stored).

## Timing
Must complete **before corp account deactivation** at end of internship. Treat as a hard deadline.

## Owners
Melanie Chen (migrate) · Brian Bowman / David Kushmerick (target org + long-term owner) · Juno team (recipients).
