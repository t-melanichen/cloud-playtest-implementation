# Blocker: PC streaming-package readiness polling

**Status:** In progress — version-aware poll implemented in PR `t-melanichen/playtest-pc-install-polling`; upstream install enablement (Timi) still pending
**Owners:** Melanie Chen (xPlaytest) · Timi Bolaji (content/install)

## Update (2026-06-15)
The version-aware PC poll is implemented in branch `t-melanichen/playtest-pc-install-polling`
(services.contentingestion): `PollFirstInstallAsync` now resolves the ingested version (install id +
hash) and queries the PC server pool by `LocalPackageId` + `LocalPackageHash`. Full step list, the
remaining repo work (PC-playtest SUG constant, region config), and Timi's upstream prerequisites
(enable install-on-attach + set the PC server quota) are tracked in
[`FuturePlans/pc-install-readiness-polling-implementation.md`](../FuturePlans/pc-install-readiness-polling-implementation.md).

## Problem
Before a streaming playtest can be marked ready, we need to know that the streaming package has been **installed and is ready on a PC server**. The existing install-poll path is console-only: `TitleIngestionWorker.PollFirstInstallAsync` hardcodes Xbox allocator parameters (e.g. `ServerType.XboxV3SeriesS`, `XBOX_*` pool ids), so PC playtests fall into Xbox-only logic and the PC readiness signal isn't available today.

## Current direction (Sync 3, 2026-06-10 — Timi)
- A usable API already exists for PC: *"similar to the Xbox polling where we have some entity that owns servers… you check the servers and see if the game you want is already one of them."* — *"Such an API already exists today. We just need to plug it in."*
- **Ordering clarification:** you don't have to wait for install before creating the offering. *Adding the title to the offering is what triggers the install* — the service notices a title in the offering, performs the install(s), and **then** you can poll for completion. So the sequence is: configure offering + attach title → poll the PC server-query API for readiness.
- Likely lives in `services.pcservices`.

## Next actions
1. Identify the exact PC server-query API (Melanie was about to share a candidate link with Timi) and confirm the inputs it needs.
2. Implement the **PC fork** of the install-poll path (branch `ServerFilter` / poll logic on `Platform == WINDOWS.DESKTOP`) so PC playtests use the PC server pool and the PC readiness query instead of the Xbox allocator path.
3. Validate that polling after title-attach correctly observes install completion.

## References
- `Transcripts/Sync3.docx` — Timi on PC polling + install-on-attach ordering.
- `SPEC.md` §3.6 (PC fork of install poll), XC6.
- `Files/TitleIngestionWorker.cs` (`PollFirstInstallAsync`).
