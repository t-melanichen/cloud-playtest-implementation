# Demo script — XPD / XBOX Developer Demos (recording plan)

**Instantly Shareable Playtest** · Melanie Chen · target length **~3 min**.
This is the plan for the *pre-recorded* demo that plays on slide 8. `[bracketed]` = confirm/fill before recording.

---

## ⚠️ Reality check — record only what actually works
Per [`../testing/e2e-2026-07-06-pc-playtest-streaming.md`](../testing/e2e-2026-07-06-pc-playtest-streaming.md):

- **Works today (prod):** trigger ingestion → the `PlaytestTitleIngestionWorkflow` runs → **offering + title are
  created and resolve in prod**, and the **product page renders with a "Get Ready To Stream" CTA**.
- **Not working yet (prod):** the final **live PC stream** — launch fails at allocation (pool 400 / no
  `PC_PLAYTEST` lane in prod). The two **front ends** (creator toggle, tester landing) aren't built.

So this is a **recorded, leadership-visible** session — don't show a stream "starting in seconds" that then
dead-ends. Use **Option A** (backend spine — fully honest and real). Use **Option B** only if you have a
genuinely working stream (INT, a local harness, or after the prod lane lands). Either way, see the note at the
bottom about softening slide 8's wording.

---

## Setup (before you hit record)
- **Seller:** pilot seller **`65050620`** (streaming is gated to this seller id).
- **Test product:** XSTH "Xbox Stream Test" (`2SDT4X91KMWM`) *or* your current test product — confirm it's
  **Xbox-Live-configured** (resolves a TitleId in XORc), else opt-in publish fails fast.
- **Payload:** [`../testing/README.md`](../testing/README.md) + `../testing/devapi-xsth-pc-polling.json`.
  Before each run: **new `PlaytestId`** (`p2-test-<guid>`), **future `ExpirationTime`** (≤30 days), sandbox `RETAIL`,
  `AllowedDnaGroups=["4611686019004512103"]` (or your test group).
- **Recorder:** Xbox Game Bar or OBS, **1080p**, cursor highlight on. Keep it to ~3 min — you can trim/speed dead
  time (job polling) in post.
- **Scrub:** nothing here is confidential per your call, but avoid lingering on tokens/`Authorization` headers.

---

## Option A — Backend spine (recommended, ~3 min)
> Story: "a publish fires one cross-cloud call that stands up a private, invite-scoped streaming offering in prod."

### Beat 1 — "Creator publishes" (~40s)
1. Open the **DevApi ingestion page** (the Blazor "trigger ingestion" page in `services.devapi`).
2. Paste `devapi-xsth-pc-polling.json`; call out **Platform=PC**, **AllowedDnaGroups** (invited testers only),
   **AllowedSandboxId=RETAIL**, **ExpirationTime** (bounded).
3. Submit → capture the returned **job id**.
   - **Narrate:** "The creator-facing toggle isn't built yet, so I'm firing the exact same publish signal the
     front end will send. One call — watch what it sets in motion."

### Beat 2 — "The backend threads it across two clouds" (~90s)
4. Use the page's status check to walk the job through its stages:
   `ValidateParameters → TriggerAssetIngestion → PollAssetIngestion → CreatePackage → ConfigureOffering →
   PollFirstPCInstall → ConcludeWorkflow`.
   - **Narrate over the stages:** payload built from the publish snapshot → **cross-tenant token** minted →
     sent **Green→Corp via SAGE** → **ingested** (offering + title bound) → **readiness poll** waits for a PC
     server to stage the exact build. (Speed this up in post.)
5. Show the **cross-tenant auth working** — the worker→CTIN call authenticates (the bare-GUID audience fix).
   If you have it, flash the CTIN log line / a green job stage; **don't** dwell on token contents.

### Beat 3 — "The result is real in prod" (~40s)
6. Show the **offering exists**: dev-tools offering browser
   `play.xbox.com/_internal/dev-tools/offering/XPT2SDT4X91KRQS` — the title tile is listed.
7. Show the **product page renders**:
   `play.xbox.com/products/2SDT4X91KRQS/...` with the **"Get Ready To Stream"** CTA, entitlement + XGP tiers
   resolved.
   - **Narrate (honest payoff):** "That one publish produced a **private, invite-scoped streaming offering,
     live and resolvable in prod** — opt-in and non-blocking. The last mile — the tester clicking *Get Ready to
     Stream* and it playing — is the front-end + prod-lane work that's next."

---

## Option B — Live visible stream (only if it genuinely works)
> Use the **ATG VideoTexturePC12** package (~10 MB MSIXVC, already built — see
> [`../testing/pc-video-graphics-stream-test.md`](../testing/pc-video-graphics-stream-test.md)) so the stream is
> *obviously* live (spinning video quad), not a frozen frame.

1. In the env where the `PC_PLAYTEST` lane exists (INT, or prod once provisioned), publish/ingest the
   video-texture package as the pilot seller via the **Xbox Stream harness**.
2. Open the **share link / deep link** as an **invited** test account (e.g. XGP Ultimate).
3. Show it **stream in seconds** — the spinning/bouncing video renders over the cloud stream. Let it run ~10s so
   motion is unmistakable.
   - **Narrate:** the three beats collapse into one tester experience — no install, no devkit.
4. **Backup:** keep the raw clip in `Demo/` and hand organizers a standalone copy.

> If Option B isn't reliably reproducible yet, **do Option A** and narrate the stream as the vision. Don't fake it.

---

## After recording
1. Save the file into **`XPD-Demo\Demo\`** (`.mp4` preferred).
2. Re-run `python build_deck.py` — it auto-embeds the recording on slide 8.
3. Keep the standalone copy as the Teams backup (embedded video + screen-share both, per plan).

## Note on slide 8 wording (reconciled)
Slide 8 has been reframed to match reality: the demo shows **publish → cross-cloud ingest → a private streaming
offering live in prod** (the "Get Ready to Stream" CTA), and **"stream in seconds" is stated as the goal**, not
something the recording proves. Record **Option A** and this lines up exactly. If you later capture a genuinely
working stream (Option B), tell me and I'll flip slide 8's payoff to the live stream.
