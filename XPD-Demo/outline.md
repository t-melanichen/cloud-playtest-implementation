# XPD / XBOX Developer Demos — Outline & Speaker Notes

**Instantly Shareable Playtest** · Xbox / Juno · Melanie Chen

**10 slides · sub-10 minutes.** Same "asked → built → delivered" arc as the end-of-internship demo
(`../Presentation`), trimmed, with a **recorded end-to-end demo** as the payoff.

> This file is the content source of truth. `build_deck.py` renders it to `XPD-Developer-Demo.pptx`
> and auto-embeds a recording placed in `Demo/`. Keep on-slide text and speaker notes in sync.
> `[bracketed]` items are placeholders to fill in.

---

## 1 · Title

**Instantly Shareable Playtest**
Stream a pre-release build from the cloud — in seconds. No install, no devkit.

Melanie Chen — Software Engineering Intern · Xbox / Juno

**Speaker notes:** Hi everyone — I'm Melanie, an SWE intern on Xbox Juno. In under 10 minutes I'll show
Instantly Shareable Playtest: a creator can share an unreleased build that a tester streams from the cloud in
seconds — no download, no install, no devkit. I'll frame the problem, walk the architecture and the two
hardest pieces, then play a recorded end-to-end demo.

---

## 2 · About me

- [University · Degree · Expected year]
- Team **Juno** (Xbox) — reducing friction for game creators
- Manager **Brian Bowman** · Mentor **Emma Park**
- My summer: backend across **~13 services**, **two orgs**
- [One line — an interest or something fun about you]

**Speaker notes:** A quick bit about me. [Fill in your school and background.] I joined Juno, whose mission is
to lower the barrier for game creators. My project lived almost entirely in the backend, threading a build
across about thirteen services — which meant ramping up fast. Big thanks to my manager Brian and my mentor Emma.

---

## 3 · The problem — testing shouldn't mean shipping the whole game

xPlaytest already shares **RETAIL-signed private builds** — no cert, no store page. But barriers remain:

- Games are **hundreds of GB** — every tester waits on a slow install
- Creators must **provision many hardware profiles** for compatibility
- Physical devices **risk leaking** locally-inspectable game code

**Speaker notes:** Where did this start? The xPlaytest team had already made testing easier — a creator can
share a retail-signed private build without certification or a store page. But three barriers remained. Modern
games are hundreds of gigabytes, so every tester sits through a huge install. Creators have to buy and set up
lots of hardware to test compatibility. And physical devices are a security risk — a lost devkit means the
unreleased code is right there. We wanted to remove all three.

---

## 4 · The vision — Instantly Shareable Playtest

**xPlaytest × Xbox Cloud Gaming**

- The creator flips on **"allow cloud streaming"** and shares a link
- An invited tester **streams the private RETAIL build in seconds**
- **No install. No download. No devkit.**
- **Not aware of another platform** that does this — beta channels download; cloud gaming streams published titles

**Speaker notes:** The idea is to combine xPlaytest with Xbox Cloud Gaming. The creator just opts in to cloud
streaming and shares a link. An invited tester clicks it and — instead of downloading anything — streams the
build straight from the cloud, in seconds. It's still a real retail build; it just runs in xCloud instead of
on the tester's own hardware. That's the north star. Worth noting the differentiation: we're not aware of
another platform where a tester streams a private, unreleased build with no install — the beta channels (Steam
playtests, TestFlight) are download-based, and cloud gaming services stream published titles you already own.
This combines the two.

---

## 5 · How it works — the backend spine

*(Native flow diagram, drawn on-slide, grouped into the **two systems** it spans — verified against the code:
**Xbet** (`Xbox.Xbet.Service` — the caller) and **xCloud** (`services.contentingestion` CTIN + `services.partnerregistry`
PTNR — the receiver), bridged by **SAGE**. The detailed `../Documentation/xPlayTestDiagram.png` is kept as the
**Appendix** slide.)*

- **Xbet · xPlaytest / xPackage:** Audience (invited DNA groups) → Build (xPackage publish) → Payload (asset + audience)
- **→ SAGE →** (cross-tenant gateway)
- **xCloud · GSSV:** Ingest (CTIN) → Offering (PTNR · gated + title) → Readiness (poll until staged) → Share link

Takeaway: **one publish → one cross-cloud call → a private, invite-scoped stream.**

> Accuracy note: the **offering is configured on the xCloud side** — CTIN's `ConfigureOfferingAsync` calls
> `partnerRegistryClient.ConfigurePlaytestAsync` — not up-front on the Xbet side.

**Speaker notes:** One slide for the whole flow, grouped by the two systems it spans. On the left, Xbet — that's
xPlaytest and the xPackage publish workflow, the caller: it resolves the audience (the invited DNA groups), the
build publishes, and I assemble the payload of everything xCloud needs. That crosses to xCloud through SAGE, the
cross-tenant gateway. On the right, xCloud — Game Streaming Services: content ingestion (CTIN) ingests the build,
configures the private offering and attaches the title in Partner Registry, polls until a server has staged the
exact version, and the share link streams it. I touched every hop across both systems; the next two slides zoom
into the pieces I'm proudest of.

---

## 6 · My headline contribution — the payload builder

**Assembling everything xCloud needs** to stream a build, from the publish snapshot.

- Builds the payload from the publish snapshot: **StoreAsset**, **allowed DNA groups**, sandbox, bounded expiration
- Mints a **cross-tenant token** and fires the streaming ingest
- **Opt-in** (pilot seller) and **non-blocking** — never breaks the normal download publish

**Speaker notes:** My headline piece is the payload builder. When a creator publishes, I take a snapshot of
that publish and assemble everything Game Streaming Services needs: the store asset details, the allowed
audience groups, the sandbox, and a bounded expiration. Then it mints a cross-tenant token and fires the
ingestion. Two design choices I care about: it's opt-in, gated to a pilot seller so we could roll out safely;
and it's non-blocking — if streaming ever fails, the normal download publish still succeeds.

---

## 7 · The hard problem — making two clouds trust each other

The send crosses an org boundary: **MSFT Green → Corp**.

- Green mints a **v1.0 token** whose audience is a **bare app-id GUID**
- The receiver rejected it — *"audience (null) is invalid"*
- I traced it end-to-end and made ingestion **accept the bare-GUID audience** — auth **and** authz passed

**Speaker notes:** The hardest problem was authentication across that org boundary. The caller lives in the
MSFT Green tenant and the receiver lives in Corp — two separate trust domains. The Green side mints an
older-style token whose audience claim is just a bare GUID, and the receiver kept rejecting it with "audience
null is invalid." I traced the token through both services to find that mismatch, then fixed the receiver to
accept the bare-GUID audience. When that clicked, the request finally authenticated and authorized end to end.

---

## 8 · DEMO — publish → cross-cloud ingest → live offering

*(Recorded demo embeds here from `Demo/`; styled ▶ placeholder until one exists.)*

**1** opt in & publish · **2** backend threads it across two clouds (Green→Corp) · **3** a private streaming
offering, **live in prod** — *goal: stream in seconds*

**Speaker notes:** You've seen the architecture and the two hard parts — now watch it work. Beat one: a creator
publishes a playtest with cloud streaming on — opt-in. (The creator toggle front end isn't built yet, so I fire
the exact same publish signal it will send.) Beat two: on publish, the backend assembles the payload, mints the
cross-tenant token, sends Green→Corp through SAGE, ingests the build, and polls for a server. Beat three: that
one publish produces a **private, invite-scoped streaming offering that's live and resolvable in prod** — here's
the product page with the "Get Ready to Stream" CTA. The **goal is the tester clicking that and streaming in
seconds** — that last mile, the front ends and the prod streaming lane, is what's next. [Play recording. ~3 min.]

---

## 9 · What I delivered

Against the P0 goals:

- Private streaming offering created per playtest — **done**
- Audience scoped to invited DNA groups — **done**
- New build ingested into streaming on publish — **done**
- Seller flighting to limit blast radius — **done**
- Shareable-stream backend — **done**

- Shipped across **~13 services**, two orgs
- Backend spine in **main** and **deployed to prod** — a pilot-seller publish fires the full Green→SAGE→ingest call
- Next: the two **front ends** (creator toggle + tester landing)

**Speaker notes:** So what actually shipped? Going down the P0 list: private offering per playtest — done;
audience scoping — done; build ingestion on publish — done; seller flighting to limit blast radius — done; and
the shareable-stream backend — done. It spans roughly thirteen services across two
orgs. The backend spine is in main and deployed to prod — today a publish by our pilot seller fires the whole
cross-cloud call for real. Why it matters: it removes the two barriers testing had — there's no
multi-hundred-GB install for the tester, and because the build only ever runs in the cloud, an unreleased game
never leaves on someone's hardware, so there's no leaked-devkit risk. What's left is the two front ends.

---

## 10 · Thanks — questions?

- Mentor **Emma Park** · Manager **Brian Bowman**
- Feature leads **David Kushmerick** & **Bec Lyons** · the **Juno**, **xPlaytest** & **GSSV** teams
- **What's next:** the two front ends — the creator's **share link** + the **Bayside tester experience** (log in first, then metadata + stream)
- **Then:** playtester **feedback** to the studio · **launch args**, **streaming region / touch controls**, **console** support

**Questions?**

**Speaker notes:** That's the demo. Huge thanks to my mentor Emma and manager Brian, to David and Bec on the
feature side, and the Juno, xPlaytest, and Game Streaming teams. On what's next — straight from the project's
north star: the two front ends are the big ones, the creator's shareable link in the xPlaytest portal and the
Bayside tester experience, which logs the tester in first so nothing leaks, then shows the playtest's details
and art and lets them stream. After that, rounding out self-serve — deleting a playtest cleans up its offering,
and funneling playtester feedback back to the studio — and the stretch goals: launch args so a nightly test can
jump to a level or a dev mode, streaming region and touch controls, and console support. It's all documented in
the Juno repo. Happy to take questions.

---

## Appendix · Detailed architecture

*(Backup slide after "Questions?" — the full `../Documentation/xPlayTestDiagram.png` end-to-end flow &
readiness polling, for deep-dive Q&A. Marked "APPENDIX" and excluded from the 10-dot progress count.)*
