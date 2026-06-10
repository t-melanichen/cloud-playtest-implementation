# Future plan: Polling strategy refinement

**Why it matters:** v1 ships with infinite-retry polling and no real timeout (see [`Blockers/manual-pr-polling.md`](../Blockers/manual-pr-polling.md)). Once the end-to-end flow works, we need a more robust strategy that handles slow ingestion, the manual-PR-approval gap, and dead jobs.

## Current understanding
- **Brian:** *"assume infinite retry of polling for now and we can figure out a better system once you get that end-to-end working."*
- **Anthony:** the xCloud workflow can retry effectively forever and emits notifications for long-running jobs; *"we just need to know what to poll"* — capture a job/operation id.
- **David K:** model it like playtest's existing "waiting for ingestion to complete" state; note there are **multiple workflows** being tracked (asset ingest + offering create), so it's a multi-poll coordination.

## Options / design to finalize
- **Foreground** poll with exponential backoff (e.g. 30s → 60s → 2m → 5m cap, ~60 min foreground wall clock).
- **Background reconciliation** job that takes over past the foreground deadline (re-reads the persisted `jobId`), polling at a fixed interval up to a **24h cap** (above the server's ~14h max), then fires an operator alert and leaves the entry for manual triage.
- Decide exactly which **id** to poll and the status contract.

## Open questions
- What signal/id does xCloud expose to poll (confirm with Jack/Anthony)?
- Alerting thresholds + where the background reconciliation job lives.

## Owners
Melanie Chen · Anthony Keller · Jack.
