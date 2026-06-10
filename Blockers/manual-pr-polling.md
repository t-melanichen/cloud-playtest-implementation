# Blocker: Polling blocked on manual Partner Registry PR approval

**Status:** Open — accepted as a known gap for v1
**Owners:** Melanie Chen (xPlaytest) · xCloud reviewers (PR approval)

## Problem
Creating the offering (and attaching the title) in Partner Registry is an **ADO PR**, and SFI forbids self-approval. The offering therefore is not live until a **human approves and merges the PR**. The ingestion workflow must wait for that before the playtest can be marked streamable, and a human could take a long time (up to ~48h) — or, in the worst case, never approve.

Open questions raised in Sync 3:
- How does the polling work, how long do we wait, and when does it time out?
- What happens if the PR is never approved?

## Current direction (Sync 3, 2026-06-10)
- **David Kushmerick:** a human approval could take 48 hours; that's acceptable for now. *"We should just document the heck out of the fact that this is a known gap and that there's a human approval required."* It's by design.
- **Brian Bowman:** *"Assume infinite retry of polling for now and we can figure out a better system once you get that end-to-end working."*
- **Anthony Keller:** the workflow can retry effectively forever and emits notifications for long-running jobs; *"we just need to know what to poll"* — i.e. **capture a job/operation id** so xPlaytest can make the status call.

## v1 decision
- Persist the returned **`jobId`** on `PublishedPlaytestEntity`.
- Poll the SAGE status endpoint with **infinite retry** (no hard timeout in v1).
- Hold the playtest in a "waiting for ingestion" state until the workflow reaches a terminal state *and* the offering is complete (mirrors how playtest handles waiting-for-ingestion today, per David K).
- **Document the human-approval requirement** prominently as a known gap.

## Next actions
- Confirm the precise id to poll and the status contract with xCloud (Jack/Anthony).
- Refinement (timeouts, background reconciliation, 24h cap, operator alerts) is deferred to [`FuturePlans/polling-strategy-refinement.md`](../FuturePlans/polling-strategy-refinement.md).

## References
- `Transcripts/Sync3.docx` — polling / PR-approval discussion.
- `SPEC.md` §6.2 (one-PR offering+title via `BulkEditAsync`), §3.1 (polling strategy).
- Outdated spec §3.10 "Polling vs Callback" was marked *FINALIZE THIS SECTION* — this file + the FuturePlans item supersede it.
