# Future plan: Console support migration (PC → console)

**Why it matters:** v1 is **PC-first**; Xbox console support is deferred. By demo time there may be the beginnings of console support, and a likely question is the **cost to migrate** the PC streaming playtest flow to console.

## Current understanding
- The existing publish path already targets `WINDOWS.DESKTOP`, and PC title-id/package handling is more directly sourceable, which is why PC is first.
- Console adds work that PC doesn't need:
  - Xbox-specific **Title ID** and **package handling**.
  - The install/allocator path is console-specific today (`PollFirstInstallAsync` uses `ServerType.XboxV3SeriesS` and `XBOX_*` pool ids) — see [`../Blockers/pc-install-readiness-poll.md`](../Blockers/pc-install-readiness-poll.md).
- David K flagged this as a demo Q: "theoretically by then we might have the beginnings of console support — what would be the cost to migrate this to console support?"

## Open questions
- Status of console streaming support at demo time.
- Delta in title-id/package handling and allocator pools for console vs the PC fork.

## Owners
Melanie Chen · David Kushmerick · xCloud content/allocator team (Timi/Nate).
