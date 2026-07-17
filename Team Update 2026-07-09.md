# Playtest Streaming — Progress Update (2026-07-09)

**From:** Melanie Chen · **Area:** Instantly Shareable Playtest → xCloud streaming (Bayside/PC)

## TL;DR

Production ingestion works end to end under my seller ID: I can create a playtest, the Xbet builder resolves the Xbox title from XORc, assembles the payload, and the request flows SAGE → CTIN → a successful ingestion workflow → an auto-PR I approve → on to PC. Two known bugs remain: (1) ingestion needs to be pinned to the Americas cluster — PR is up and needs a reviewer, but it won't reach prod until Monday because deployments are paused; (2) the PC build streams-through path fails at install — I debugged this with Timi and root-caused it to the build landing as a stub plus likely leftover-server state. On the client, I built the new Bayside "My playtests" tab, but it can't show game art/name yet — that's blocked on a metadata source (details below). I also built a small "collect the stars" game package to use as a real (non-stub) demo title.

## 1. Production ingestion — working end to end

Under my pilot seller id (`65050620`), the full publish path runs in production:

1. Create a new playtest under my seller id.
2. The Xbet playtest builder resolves the **Xbox title id from XORc**.
3. It gathers the necessary inputs — DNA group, store asset — and builds the payload.
4. It POSTs to **SAGE**, which routes to **CTIN** (content ingestion).
5. CTIN runs the ingestion **workflow in production** and ingests the asset correctly.
6. CTIN opens a **PR**, which I approve, and the offering/title flow on toward PC.

This is the milestone: a playtest created in Partner Center reaches Live and ingests into xCloud in prod, no manual steps beyond approving the auto-PR.

## 2. Bug — ingestion must be pinned to Americas (PR up, lands Monday)

The ingestion call works, but it routes through a global gateway while **CTIN ingestion lives only in the Americas** and ingestion jobs are **cluster-local**. So a request can land on a region with no CTIN (fails) or the submit and the status-poll can hit different Americas sub-clusters (the poll then can't find the job the submit created). The result is intermittent 500s and 404s depending on which cluster the load balancer picks.

- **Fix (interim):** pin the ingestion worker to the single stable Americas cluster (eastus2) so submit and poll always agree. **My PR is up — Xbet PR 16102792 — and needs a reviewer.**
- **Timing:** it will not reach production until **Monday** because deployments are currently paused.
- **Durable follow-up:** point the SAGE route at a stable cross-region CTIN endpoint so we can drop the pin (a CTIN-side dependency).

## 3. Bug — PC build not streaming (debugged with Timi)

I met with Timi Bolaji to trace why the PC playtest doesn't stream. The game isn't streaming because the **PC build isn't installing correctly on a server**. What we found:

- **The build is landing as a stub.** The server shows a ~10 MB placeholder instead of the real ~461 MB playable build, so the install fails. (Timi: a real build "is clearly bigger and it will actually play"; the stub "is just 10 MB.")
- **The service loops.** Content distribution retries install every ~5 minutes and deletes/retries on failure, which is why the dashboards show rows of red failed attempts.
- **Multiple playtests contend for one server.** Distribution thinks it must install several playtests (test 1 / test 2 / test 100) on the same server and shuffles them one at a time, so my target title may not get picked on a given attempt.
- **Even after publishing a real (non-stub) build, the install still failed** with a server error code. Timi's working theory: a **prior attempt to install a stub left leftover state on the server (reused VHD)** that corrupts the later real-build install.
- **Mitigation Timi ran:** force a **fresh server** via PC Orchestrator (check the server out so a brand-new one is created, then check it back in so the old one is deleted) to clear leftover state, then retry the install. We hit **server-creation quota/region constraints** while waiting for the new server.

Context worth noting: for PC, installs are handled by the **content distribution** service (separate from the Xbox install path), and **resolution** decides what version a server should install.

**Next steps on this bug:**
- Confirm the real "collect the stars" build installs cleanly on a freshly created server (removes the stub + leftover-state variables).
- If the "stub install corrupts later real installs" theory holds, raise it with the **server team**.
- Make sure the demo playtests point at real builds, not stubs.

## 4. Bayside UI — new playtest tab built; game metadata blocked

I built the new **"My playtests" tab** in Bayside (the play.xbox.com web client), separate from the normal library, gated so it only appears for a user who has an `xpt` playtest offering. It also handles the signed-out and not-invited states. It lists the playtest(s) — but each tile is a **placeholder with no game art or friendly name yet.**

Why the tile has no game info, and what it will take:

- **Private playtests are not in BigCat.** The normal client hydration (catalog/DCAT by product id) returns nothing for a private playtest product, so there's no art or title to pull the usual way.
- **CAS carries access, not display metadata.** CAS deployed playtest as a standard access type this week — it checks the xToken for the new playtest claim (DNA-group based) and returns playtest data, with no CAS service work needed, only the new proto. But I verified their latest proto has only access flags — **no image, title, or publisher fields** — and since the products aren't in BigCat, CAS has no catalog to source art from either. So CAS alone will not deliver the picture.
- **What's available today:** the friendly playtest **name** already reaches the client (the offering name), so I can surface a real name on the tile as an interim while art is unresolved.

The open question for the team (esp. Anthony / CAS): since private playtests aren't in BigCat and CAS has no display fields, **where does a playtest's developer-provided tile art and display name live (authoring/sandbox catalog? the playtest pipeline? the build package?), and what would expose it to Bayside?** That determines whether art is a sandbox-catalog client call or a new upstream metadata contract.

## 5. Demo asset — "collect the stars" game package

I built a new game package — a simple **collect-the-stars** game — to use as a real, playable playtest title for the demo, so we're testing streaming against an actual build rather than a stub.

## Asks / next steps

- **Review my Americas-pin PR (Xbet 16102792).** It's the interim fix for the ingestion routing bug; it lands Monday once deployments resume.
- **PC streaming:** verify the real build installs on a clean server; if the stub-corrupts-real-install theory holds, loop in the server team.
- **UI / CAS:** ~30 min with Anthony on the playtest metadata source — where developer-provided art and display name live, given it's not in BigCat and not in CAS's contract — so we can decide the path to real game art on the tile.

## References

- Timi debugging session: `Call with Timi Bolaji` (2026-07-09) — PC install/stub root cause.
- Ingestion routing detail: [`7-8 sync discussion topics/README.md`](./7-8%20sync%20discussion%20topics/README.md), [`Explanations/sage-ctin-routing-error-and-options.md`](./Explanations/sage-ctin-routing-error-and-options.md).
- UI + CAS detail: [`UI Bayside/README.md`](./UI%20Bayside/README.md), [`UI Bayside/cas-playtest-metadata.md`](./UI%20Bayside/cas-playtest-metadata.md).
