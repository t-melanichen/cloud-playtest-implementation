# Speaker script — XPD / XBOX Developer Demos

**Instantly Shareable Playtest** · Melanie Chen · Xbox / Juno
Target: **sub-10 min** (≈6 min talk + ≈3 min demo). `[bracketed]` = fill in / your call.

> Delivery tips: pause on each slide's first line, let the **bold** words land, keep the demo to ~3 min.
> `//` lines are stage directions, not spoken.

---

## 1 · Title  — ~20s
Hi everyone, I'm Melanie, a software engineering intern on the Xbox Juno team. Today I want to show you
**Instantly Shareable Playtest** — a way for a game creator to share an unreleased build that a tester can
**stream from the cloud in seconds**: no download, no install, no devkit. I'll frame the problem, walk the
architecture and the two hardest pieces, and then play a short end-to-end demo.

## 2 · About me  — ~25s
Quick bit about me first. [I'm a student at **[school]**, studying **[degree]**, graduating **[year]**.] I spent
the summer on **Juno**, whose whole mission is lowering the barrier for game creators. My project lived almost
entirely in the **backend** — threading a build across about **thirteen services in two orgs** — so I ramped up
fast. Big thanks to my manager Brian Bowman and my mentor Emma Park. [Optional fun line.]

## 3 · The problem  — ~45s
So where does this start? The xPlaytest team had already made testing a lot easier — a creator can share a
**retail-signed private build** without going through certification or a store page. That's great. But three
barriers were left. First, modern games are **hundreds of gigabytes**, so every tester sits through a huge
download and install. Second, creators have to **buy and provision a lot of different hardware** to test
compatibility. And third, a physical devkit is a **security risk** — if it's lost, the unreleased game code is
right there to inspect. We wanted to remove all three.

## 4 · The vision  — ~35s
The idea is to combine xPlaytest with **Xbox Cloud Gaming**. The creator just flips on "allow cloud streaming"
and shares a link. An invited tester clicks it and — instead of downloading anything — **streams** the build
straight from the cloud, in seconds. It's still a real retail build; it just runs in xCloud instead of on the
tester's own hardware. That's the north star. And worth a beat: we're **not aware of another platform** that does
this — beta channels like Steam playtests and TestFlight are download-based, and cloud gaming streams *published*
titles you own. This combines the two: a private, unreleased build, streamed.

## 5 · How it works  — ~50s
// Point along the diagram left to right.
Here's the whole flow on one slide. We resolve **who's allowed in** — the audience. We publish a private
**offering**. We assemble a **payload** of everything xCloud needs to stream. We send it **across an org
boundary** — from the MSFT **Green** cloud to **Corp** — through a gateway called **SAGE**. On the other side
we **ingest** the build, binding its title and offering together. We **poll** until servers are ready to
stream. And then the **share link** works. I touched every hop here — let me zoom into the two I'm proudest of.

## 6 · The payload builder  — ~45s
The headline piece is the **payload builder**. When a creator publishes, I take a snapshot of
that publish and assemble everything Game Streaming Services needs: the **store asset** details, the list of
**allowed audience groups**, the sandbox, and a bounded expiration. Then it mints a **cross-tenant token** and
fires the ingestion. Two design choices I care about: it's **opt-in**, gated to a pilot seller so we could roll
out safely — and it's **non-blocking**, so if streaming ingestion ever fails, the normal download publish still
succeeds. We never degrade the existing product to add the new one.

## 7 · The hard problem  — ~50s
The hardest part was **authentication across that org boundary**. The caller lives in the Green tenant, the
receiver in Corp — two separate trust domains. The Green side mints an older-style token whose **audience** is
just a **bare GUID**, and the receiver kept rejecting it — *"audience null is invalid."* I had to trace the
token through **both** services to find that mismatch, then fix the receiver to **accept the bare-GUID
audience**. When that clicked, the request finally authenticated *and* authorized end to end. It's the kind of
bug that's invisible until you understand both sides — and it's the thing I learned the most from.

## 8 · DEMO  — ~3 min
// Switch to the recording (embedded) or share the standalone file. Narrate lightly only if playing silently.
Alright — you've seen the pieces, let's watch it work. Three beats: the creator **publishes** with cloud
streaming on; the backend **threads the build across the two clouds**; and out the other side we get a
**private streaming offering, live in prod** — here's the "Get Ready to Stream" CTA. The **goal is the tester
clicking that and streaming in seconds** — that last mile is what's next. [Play recording.]
// If it doesn't autoplay, click the video. Stay quiet and let the recording's own narration carry it.

## 9 · What I delivered  — ~40s
So what shipped? Every P0 goal: a **private offering per playtest**, **audience scoped** to invited groups,
**build ingestion on publish**, **seller flighting** to limit blast radius, and the **shareable-stream
backend**. That spans about **thirteen services across two orgs**. The whole backend spine is in
**main and deployed to prod** — today a publish by our pilot seller fires the entire cross-cloud call for real.
And why it matters: no multi-hundred-GB install for the tester, and because the build only ever runs in the
cloud, an unreleased game never leaves on someone's hardware — no leaked-devkit risk. What's left is the two
front ends.

## 10 · Thanks / Q&A  — ~20s
That's it. Huge thanks to my mentor Emma and manager Brian, to David and Bec on the feature side, and the Juno,
xPlaytest, and Game Streaming teams. On **what's next**, straight from the project's north star: the two **front
ends** — the creator's **share link** and the **Bayside tester experience** that logs the tester in first so
nothing leaks, then shows the playtest's details and art and lets them stream. After that, rounding out
self-serve — **deleting** a playtest cleans up its offering, and funneling **playtester feedback** to the studio
— plus the stretch goals: **launch args** (jump to a level or a dev mode), **streaming region / touch controls**,
and **console** support. All documented in the Juno repo. Happy to take any questions.

---

### Timing cheat-sheet
| # | Slide | Target |
|---|-------|--------|
| 1 | Title | 0:20 |
| 2 | About me | 0:25 |
| 3 | Problem | 0:45 |
| 4 | Vision | 0:35 |
| 5 | How it works | 0:50 |
| 6 | Payload builder | 0:45 |
| 7 | Hard problem | 0:50 |
| 8 | **Demo** | 3:00 |
| 9 | Delivered | 0:40 |
| 10 | Thanks | 0:20 |
| | **Total** | **≈8:30** (+Q&A) |
