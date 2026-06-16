# Future plan: PC install-readiness polling — implementation steps

**Why it matters:** For PC (WINDOWS.DESKTOP) streaming playtests, content is *not* pre-pulled the way
Xbox content is. The `PlaytestTitleIngestionWorkflow` must confirm the **exact ingested version** is
installed on a PC server before it declares the title ready. This plan tracks the actual steps to land
that, what is already implemented, and the upstream prerequisites Timi Bolaji called out.

## PR / branch
- **Repo:** services.contentingestion (Xbox.Streaming)
- **Branch:** `t-melanichen/playtest-pc-install-polling` (commit `b2e3a9e3`)
- **Create PR:** https://microsoft.visualstudio.com/Xbox.Streaming/_git/services.contentingestion/pullrequestcreate?sourceRef=t-melanichen%2Fplaytest-pc-install-polling&targetRef=main
- **ADO:** task *Implement PC Polling* under work item **62492680** *[XC3] Implement PlaytestTitleIngestionWorkflow*; in-code TODO link **62521491**.
- **Source:** `Transcripts/XCloudIngestion.docx` (Melanie · Timi Bolaji · Jack Heuberger, 2026-06-11). See also [`Blockers/pc-install-readiness-poll.md`](../Blockers/pc-install-readiness-poll.md).

## What "PC polling" does (Timi's design)
PC content lands on demand, so:
1. Adding the title to the offering **triggers** the distribution service to install at least one copy on a PC server.
2. Because every playtest ingestion can be a **new version**, "is this game installed somewhere" is not enough — we must confirm the **latest** version. On a PC server the version is the **content hash** (SHA-256 over concatenated game + DLC versions).
3. To get that hash you do a **resolution** call (resolution API in ingestion) → install id + hash.
4. Then query the **PC Orchestrator** server pool with a content-file filter (install id + hash) and wait until a server reports it. When it shows up, it's ready to play on that version.

---

## Steps

### A. Already implemented in the PR
- [x] **A1 — Resolve the ingested version.** `PollPcFirstInstallAsync` calls `IResolutionProcessor.ResolveContentInstallMetadataAsync` to get the install id + per-version **hash**, scoped to the playtest sandbox + DNA-group flights + `ServerType.PC`. *(Timi: "you need to do a resolution call … now you have your install ID and you have your hash.")* — **PR** `t-melanichen/playtest-pc-install-polling`.
- [x] **A2 — Version-aware PC server query.** `IServerAllocatorClient.QueryServersAsync` with `ServerPlatform.PC` / `ServerType.PC` / `LocalPackageId` + `LocalPackageHash` (the content-file filter). *(Timi: "put that in the game Streaming Server filter and query for servers and wait until something shows up.")* — **PR**.
- [x] **A3 — Retry / terminal wiring.** Empty result → `Retry` on `FirstInstallPollingPolicy` with `NotifyInstallNotFoundAsync` fallback; server found → `NotifyReadyAsync`. Mirrors the Xbox branch. — **PR**.
- [x] **A4 — DI + tests.** Injected `IResolutionProcessor`; 3 PC unit tests (installed→ready, not-installed→retry, version-unresolved→retry) + replaced the old skip test. Build clean, 14/14 pass. — **PR**.

### B. Remaining in this repo (finish the PR)
- [ ] **B1 — PC-playtest SUG.** The poll filter's `SystemUpdateGroup` is left unconstrained (in-code TODO 62521491). Once a `PC_playtest` SUG constant is exposed in `Services.Common.Ids`, set it on the PC `ServerFilter`. *(Timi: "we will have a distinct PC underscore playtest SUG.")* — **PR**.
- [ ] **B2 — Env-specific region.** Replace the interim `IsProd() ? WestUs2 : WestEurope` with real region config: test/int = WestUs2 + WestEurope; prod = NorthCentralUs. (Shared TODO; affects Xbox + PC branches.) See [`FuturePlans/region-configuration-routing.md`](./region-configuration-routing.md).
- [ ] **B3 — Latest-version correctness.** Confirm resolution returns the *newest* ingested version's hash on a republish (version bump), not a stale one — this is the whole reason PC keys on the hash.

### C. Upstream prerequisites (owned by Timi / content-install — required for the poll to ever succeed)
- [ ] **C1 — Enable install-on-attach for the PC_playtest SUG.** content-targets/distribution already notices a title in an offering and installs ≥1, but it is **disabled** today. Conditionally enable it for the PC playtest SUG so attaching the title triggers the install. *(Timi: "we already have that implemented today. I just have it disabled … for playtest we can conditionally enable it.")*
- [ ] **C2 — Set PC server quota ≥ 1 for that SUG.** Dynamic quota config = max servers per SUG; set to 1 (one T4) wherever we want installs to happen, so distribution actually has a server. *(Timi: "we have a quota configuration … we can just set that to one. It's one T4.")*

### D. Concurrency / queue experience (Timi's separate callout)
- [ ] **D1 — Decide conflict vs. queue for concurrent same-playtest ingestion.** `PlaytestTitleIngestionWorkflow` is `[ExclusiveWorkflow]` with lock id = playtest id and default queue depth **1**, so a second ingestion for the same playtest (new version while one is in flight) currently **conflicts**. Decide whether to keep the conflict experience or raise the queue depth to serialize 1.0 → 1.1. *(Timi: "do you want a conflict experience … or do you want it queued.")* Stretch goal — not required for MVP.

### E. Validation & ship
- [ ] **E1 — End-to-end test:** PC playtest ingest → offering+title attach → distribution installs → resolution returns hash → poll observes the server → workflow reaches `NotifyReadyAsync`. Then republish a new version and confirm it waits for the **new** hash.
- [ ] **E2 — Timeout path:** confirm `NotifyInstallNotFoundAsync` fires if the install never appears within the policy window.
- [ ] **E3 — PR review + merge** (loop in Timi / Jack); add a PRProgress entry.
- [ ] **E4 — Deploy via CI/CICD** (not the PR pipeline) and verify in test.

### F. Optional follow-up
- [ ] **F1 — Worker parity.** `TitleIngestionWorker.cs` still uses Xbox-style polling; give it the same PC treatment if that path is also exercised.

## Owners
Melanie Chen (xPlaytest / ingestion workflow) · Timi Bolaji (content-install: C1, C2) · Jack Heuberger.
