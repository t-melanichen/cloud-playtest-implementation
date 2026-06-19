# Future plan / tracker: Replace streaming-ingestion polling with a push (callback) completion

**Why it matters:** v1 polls xCloud for streaming-ingestion completion from the xPlaytest publish
workflow. A code review of PR 15834601 (branch `t-melanichen/playtest-ingestion-payload-builder`)
found the current poll is **not** the intended "infinite retry" and can **break an already-successful
publish**. Polling is a stopgap; the durable design is an event/callback from xCloud. This tracker
captures the immediate fix + the replacement. Complements
[`polling-strategy-refinement.md`](./polling-strategy-refinement.md) (which tunes the poll) — this one
**removes** it.

## Current state (verified in code — 2026-06-19)
- `XPackagePlaytestPublishWorkflow.PollingStreamingIngestionStateHandlerAsync`
  (`XPackagePlaytestPublishWorkflow.cs:513-558`) polls
  `IXCloudPlaytestIngestionServiceClient.GetPlaytestTitleIngestionJobStatusAsync(jobId)` and returns
  `StateMachineResult.RetryWith(_generalRetryPolicy)` while non-terminal.
- **`RetryWith` is NOT infinite.** `_generalRetryPolicy` has `RetryFailAfter = 2 days` /
  `MaxRetryDelay = 10 min`, yielding a finite `MaxRetryCount` (`RetryPolicy.cs:95-118`). On exhaustion
  the worker returns `StateMachineResult.Fail` (`StateMachineWorker.cs:202-212`), and `WorkerRunner`
  marks the job **Failed** and deletes the message (`WorkerRunner.cs:265-270`).
- **Impact:** for a streaming-eligible playtest whose ingestion stays non-terminal for ~2 days
  (stuck upstream job, or a persistently failing/404 status endpoint), the **download publish already
  succeeded** (XProduct created in `PlaytestProductCreation`), yet the whole job is marked Failed.
  `SuccessCompletion` (emits `Published`, line 600) is never reached, and `FailedCompletion`
  (emits `PublishFailed`, line 627) is **also** bypassed (framework `Fail` ≠ `TransitionTo`). The
  playtest is stranded showing `Publishing` with no automatic re-run.
- Asymmetry: a *fast-failed* job (`IsComplete=true, IsSuccess=false`) lets publish succeed; a merely
  *slow/stuck* job fails the whole publish — the worse outcome for the less-severe condition.

## Target design (push / event-driven)
- xCloud already "emits notifications for long-running jobs" (Anthony); xPlaytest already has a
  Service Bus job-status pattern (`XPackagePlaytestPublishWorkflowJobStatusTopicProcessor`). Replace
  the poll with: persist the ingestion operation id → **subscribe to an xCloud completion
  notification** (Service Bus topic / callback) → resume the workflow on terminal. No polling.

## Todo tracker
- [ ] **P0 — Stop streaming from failing publish (immediate, even before the callback lands).**
      On poll-retry exhaustion, do **not** `Fail` the job — transition to `SuccessCompletion`
      (or a dedicated non-failing terminal) so streaming never blocks the already-completed download
      publish. If genuine infinite polling is wanted instead, implement it explicitly (self-delay
      loop) — `RetryWith` has a hard 2-day cap. *(Review Finding 1, High.)*
- [ ] **Confirm the xCloud completion signal** (Service Bus topic name + message contract, or a
      callback endpoint) and the exact id to correlate on — with Anthony / Jack.
- [ ] **Subscribe + resume:** add a topic processor (reuse the
      `XPackagePlaytestPublishWorkflowJobStatusTopicProcessor` pattern) that resumes the workflow on
      the streaming-ingestion terminal event; key off the persisted `StreamingIngestionJobId`.
- [ ] **Telemetry:** emit a distinct success/failure metric on the terminal branch keyed on
      `OperationStatus.IsSuccess` (today success vs. failure is indistinguishable in metrics).
      *(Review Finding 2, Medium.)*
- [ ] **Idempotency:** guard `TrySchedulePlaytestStreamingIngestionAsync` against an already-present
      `StreamingIngestionJobId` so a re-run can't schedule a duplicate job / orphan the id.
      *(Review Finding 3, Low–Med.)*
- [ ] **Tests:** cover the scheduling branch (eligible seller → schedules + persists id + transitions
      to polling), suppressed-scheduling-failure → completion, terminal-but-failed, null status, and
      the timeout/exhaustion behavior. *(Review Finding 4, Medium.)*
- [ ] **Retire the poll state** once the push path is proven end-to-end; fold any remaining
      foreground wait into the backoff/reconciliation design in `polling-strategy-refinement.md`.

## Open questions
- Does xCloud expose a per-playtest completion topic/event today, or only generic long-running-job
  notifications? What's the message schema + auth?
- Where does the resume/reconciliation live, and what is the alerting threshold for a never-terminal
  ingestion?

## Owners
Melanie Chen · Anthony Keller · Jack.

## References / sources
- Code review (2026-06-19): `XPackagePlaytestPublishWorkflow.cs:513-558, 600, 627`;
  `StateMachineWorker.cs:202-212`; `RetryPolicy.cs:95-118`; `WorkerRunner.cs:265-270`.
- [`polling-strategy-refinement.md`](./polling-strategy-refinement.md) ·
  [`Blockers/manual-pr-polling.md`](../Blockers/manual-pr-polling.md)
- [`Repos/Xbox.Xbet.Service.md`](../Repos/Xbox.Xbet.Service.md) ·
  [`PRProgress/07-XBET-15834601-playtest-ingestion-payload-builder.md`](../PRProgress/07-XBET-15834601-playtest-ingestion-payload-builder.md)
