# Final Intern Presentation — Outline & Speaker Notes

**Instantly Shareable Playtest** · Xbox / Juno · Summer 2026 · Melanie Chen

12 slides, ~15 minutes, broad-audience shareout. Styled after `../Context/PlaytestIntroDeck.pdf`,
structured around `../Context/InternProjectDocument.pdf` (asked → built → delivered).

> This file is the content source of truth. `build_deck.py` renders it to `Final-Intern-Presentation.pptx`.
> On-slide text and speaker notes are kept in sync between the two. `[bracketed]` items are placeholders to fill in.

---

## 1 · Title

**Instantly Shareable Playtest**
Streaming pre-release builds from the cloud — in seconds, no install.

Melanie Chen · Software Engineering Intern
Xbox / Juno · Summer 2026

**Speaker notes:** Hi, I'm Melanie — a software engineering intern on the Xbox Juno team. This summer I
worked on *Instantly Shareable Playtest*: letting a game creator share an unreleased build that a tester can
**stream from the cloud in seconds**, with no download and no install. Here's the story of what it is, what I
built, and what shipped.

---

## 2 · About me

- [University · Degree · Expected year]
- Team: **Juno** (Xbox) — creator-facing platform, reducing friction to build, test, and ship on Xbox.
- Intern manager: **Brian Bowman** · Mentor: **Emma Park**
- My summer: backend work across **~8 services spanning two orgs**.
- [One line: an interest / something fun about you]

**Speaker notes:** A quick bit about me. [Fill in school/background.] I joined Juno, whose whole mission is to
lower the barrier for game creators. My project lived almost entirely in the backend, threading a build across
about eight different services — which meant a lot of ramping up fast. Huge thanks to my manager Brian and my
mentor Emma for the support.

---

## 3 · The problem — testing shouldn't mean shipping the whole game

xPlaytest already lets creators share **RETAIL-signed private builds** — no cert, no store page, no entitlement.
But real barriers remain:

- Modern games are **hundreds of GB** — every tester waits through a slow download and install.
- Creators must **acquire and provision many hardware profiles** for broad compatibility.
- **Physical devices are a security risk** — a lost devkit means the game's code is locally inspectable.

**Speaker notes:** So where did this start? The xPlaytest team had already made testing much easier — a creator can
share a retail-signed private build without going through certification or a store page. That's great. But three
barriers were left. Modern games are *hundreds of gigabytes*, so every tester sits through a huge download. Creators
have to buy and set up lots of different hardware to test compatibility. And physical devices are a security risk —
if a devkit is lost, the unreleased game code is right there to inspect. We wanted to remove all three.

---

## 4 · The vision — Instantly Shareable Playtest

**xPlaytest × Xbox Cloud Gaming.**

- The creator flips on **"allow cloud streaming"** and shares a link.
- An invited tester **streams the private (still RETAIL) build in seconds**.
- No install. No download. No devkit.

**Speaker notes:** The idea is to combine xPlaytest with Xbox Cloud Gaming. The creator just opts in to cloud
streaming and shares a link. An invited tester clicks it and — instead of downloading anything — *streams* the
build straight from the cloud, in seconds. It's still a real retail build; it just runs in xCloud instead of on the
tester's own hardware. That's the north star.

---

## 5 · What I was asked to build — connect two clouds

To make that link work, the backend had to:

- Stand up a new **service-to-service** relationship between **xPlaytest / publishing** and **Xbox Game Streaming Services**.
- On publish, create a **private streaming offering** unique to the playtest.
- Scope access to **only invited testers** (DNA groups).
- **Ingest each new build** into streaming and point the offering at it.
- Produce a **shareable link** that streams the game.

**Speaker notes:** Under the hood, that link needs a lot to happen. My project goals — the P0s from the project
doc — were: create a brand-new service-to-service connection between the publishing side and Xbox Game Streaming
Services; when a creator publishes, spin up a *private streaming offering* just for that playtest; make sure only
invited testers can see it; ingest every new build into streaming and point the offering at it; and finally hand
back a link that actually streams. That's the checklist I was measured against.

---

## 6 · How it works — the backend spine

*(Architecture diagram — `../Documentation/xPlayTestDiagram.png`)*

**audience** → **offering** → **payload** → **cross-tenant send (Green → Corp via SAGE)** →
**ingest (bind title + offering)** → **PC/Xbox readiness poll** → **share link**

**Speaker notes:** Here's the whole flow on one slide. Reading left to right: we resolve *who's allowed in* (the
audience), publish an *offering*, assemble a *payload* of everything xCloud needs, send it **across an
organizational boundary** — from the MSFT Green cloud to Corp — through a gateway called SAGE, *ingest* the build
while binding its title and offering together, *poll* until the servers are ready to stream, and then the *share
link* works. I touched every hop in this chain; the next few slides zoom into the two I'm proudest of.

---

## 7 · My headline contribution — the payload builder

**PR 15834601** — assembling everything xCloud needs to stream a build.

- Builds the ingestion payload from the publish snapshot: **StoreAsset** (package family name, AumID, platform,
  servicing content id), **allowed DNA groups** resolved from the playtest's audience, retail sandbox, bounded expiration.
- Mints a **cross-tenant token** and fires the streaming ingest.
- **Opt-in** (gated to a pilot seller) and **non-blocking** — a streaming hiccup **never breaks** the normal download publish.

**Speaker notes:** My headline piece is the payload builder. When a creator publishes, I take a snapshot of that
publish and assemble everything Game Streaming Services needs: the store asset details, the list of allowed audience
groups, the sandbox, and a bounded expiration date. Then it mints a cross-tenant token and fires off the ingestion.
Two design choices I care about: it's **opt-in**, gated to a pilot seller so we could roll it out safely; and it's
**non-blocking** — if streaming ingestion ever fails, the normal download-based publish still succeeds. We never
degrade the existing product to add the new one.

---

## 8 · The hard problem — making two clouds trust each other

The send crosses an org boundary: **MSFT Green → Corp**.

- The Green caller mints a **v1.0 token whose audience is a bare app-id GUID**.
- The receiver rejected it — *"audience (null) is invalid."*
- I traced it end-to-end and made content-ingestion **accept the bare-GUID audience** — auth **and** authz finally passed.

**Speaker notes:** The hardest problem was authentication across that org boundary. The caller lives in the MSFT
Green tenant and the receiver lives in Corp — two separate trust domains. The Green side mints an older-style token
whose *audience* claim is just a bare GUID, and the receiver kept rejecting it with "audience null is invalid." I
had to trace the token all the way through both services to find that mismatch, then fix the receiver to accept the
bare-GUID audience. When that clicked, the request finally authenticated and authorized end to end. It's the kind of
bug that's invisible until you understand both sides — and a highlight of what I learned.

---

## 9 · What I delivered

Against the P0 goals:

- Private offering created per playtest — **done**
- Audience scoped to invited DNA groups — **done**
- New build ingested into streaming on publish — **done**
- Seller flighting to limit blast radius — **done**
- Shareable-stream **backend** — **done**

- **~22 merged PRs across ~8 services**, spanning two orgs.
- The **entire backend spine is in `main` and deployed to prod** — a pilot-seller publish now fires the full
  Green → SAGE → ingest call.
- **Next:** the two front ends (creator toggle + tester landing).

**Speaker notes:** So what actually shipped? Going down the P0 list: private offering per playtest — done; audience
scoping — done; build ingestion on publish — done; seller flighting so we limit blast radius — done; and the
shareable-stream backend — done. All told that's about 22 merged pull requests across roughly eight services and two
organizations. The entire backend spine is merged to main and deployed to production — today, a publish by our pilot
seller fires the whole cross-cloud call for real. What's left is the two front ends, which I'll cover next.

---

## 10 · What I grew in

- **Ramping fast with AI** across many unfamiliar repos and services.
- **Microservice & systems design in .NET** — building each hop to stay resilient (opt-in, non-blocking).
- **Cross-team & cross-functional collaboration** — GSSV × xPlaytest × PM; driving reviews and decisions.
- **Working through ambiguity** — reverse-engineering an undocumented cross-org flow.
- **Detail-oriented problem solving** — the edge cases and the trust boundary.

**Speaker notes:** On the growth side — these map to the skills my project set out to build. I got a lot faster at
ramping into unfamiliar codebases, using AI to understand many repos and services quickly. I learned real
microservice and systems design in .NET, especially designing each hop to fail safely. I collaborated across the
Game Streaming, xPlaytest, and PM teams to get decisions made and code reviewed. And a huge amount of the work was
navigating ambiguity — reverse-engineering a flow nobody had fully documented — and then handling the edge cases
carefully, like that cross-tenant trust boundary.

---

## 11 · What's next

- **Two front ends:** Partner Center creator toggle + share link; Bayside tester landing that **logs in first and
  doesn't leak** any playtest details.
- **End-to-end validation** once the front ends land.
- **Roadmap:** Library integration, invite tokens, console (Gen8/9) support.

**Speaker notes:** The backend is ready and waiting for two front ends. On the creator side, Partner Center needs a
toggle to enable streaming and surface the share link. On the tester side, the Bayside landing page needs to log the
user in *before* revealing anything, so a playtest never leaks to people who aren't invited. Once those land we can
run the full end-to-end flow. Beyond that, the roadmap has Library integration, invite tokens, and console support.
I've documented all of this so the next engineer can pick up exactly where I left off.

---

## 12 · Thank you

- Mentor **Emma Park** · Manager **Brian Bowman**
- Feature leads **David Kushmerick** & **Bec Lyons**
- Engineering experts **Anthony Keller · Timi Bolaji · Ashton Summer · Chuy Galvan**
- The **Juno**, **xPlaytest**, and **GSSV** teams

**Questions?**

**Speaker notes:** Thank you — especially to my mentor Emma and my manager Brian, to David and Bec on the feature
side, and to Anthony, Timi, Ashton, and Chuy, who answered endless questions about services I'd never seen before.
And thanks to the whole Juno, xPlaytest, and Game Streaming teams. I'd love to take any questions.
