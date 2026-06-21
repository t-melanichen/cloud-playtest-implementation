# PC playtest streaming readiness — a complete, plain‑English guide

> **If you're new to this, start at sections 0–4.** They explain the whole thing with no assumed knowledge.
> Sections 5+ are the detailed engineering record (the three PRs, the test plan, and what's left).

**Status (2026-06-21):** All three code/config changes are done, built, and tested, and are open as **draft PRs**.
The only remaining step is **registering the `PC_PLAYTEST` SUG** (a server "lane" — explained below) at the platform
level, which is owned by Timi. Everything is pinned to three values: **`PC_PLAYTEST`** (the lane), **`STANDARD_NC64AS_T4_V3`**
(the server type), and **`WESTUS2`** (the datacenter region).

---

## 0. The 60‑second version (no jargon)

A "playtest" is when a game creator shares an early build so testers can try it. We want testers to **stream** it from
the cloud (play it instantly over the internet, like Netflix) instead of downloading it.

For streaming to work, the game has to be **installed on a real machine in a datacenter** before the tester clicks play.
On Xbox that happens automatically; on **PC it does not** — we have to (1) tell the system to install it, and (2) check
that it finished, before we say "ready."

This work does exactly that, across three services:
1. **Tell the system to set aside one PC machine and install the build** (the `content-targets` service).
2. **Label the playtest so the install goes to the right group of machines** (the `partner-registry` service).
3. **Keep checking until the machine actually has the build, then mark it ready** (the `content-ingestion` service).

The only thing left is for the platform team (Timi) to **create the dedicated group of machines** ("the `PC_PLAYTEST`
lane") that all three pieces point at.

---

## 1. Plain‑English glossary (read this — the rest uses these words)

| Term | What it actually means |
|---|---|
| **Streaming / xCloud / cloud gaming** | The game runs on a server in a datacenter; the tester's device just shows the video and sends button presses. No download. |
| **Build** | One specific compiled version of the game (the actual files). |
| **Server / GPU server / "T4"** | A physical machine in a datacenter with a graphics card that runs the game. "T4" is the type of machine (an NVIDIA T4 GPU). Its exact name here is the **SKU** `STANDARD_NC64AS_T4_V3`. These are expensive, so we only want one. |
| **SKU** | The *type/size* of the server machine (e.g. `STANDARD_NC64AS_T4_V3` = a T4‑GPU VM). |
| **Region** | The datacenter location, e.g. `WESTUS2` (West US 2), `WestEurope`, `NorthCentralUs`. |
| **SUG (System Update Group)** | A **named group ("lane") of servers** that share the same OS/update settings. Think of it as a labeled shelf of machines. Examples that already exist: `GA` (the big public one), `Canary`. We want a brand‑new, dedicated lane called **`PC_PLAYTEST`** just for playtests, so they're isolated and easy to control. |
| **Server set** | One specific bucket of servers, identified by **region × SUG × SKU**. Example: `WESTUS2 / PC_PLAYTEST / STANDARD_NC64AS_T4_V3` is one server set. This is the unit everything is counted/configured in. |
| **Offering** | The "listing" that makes a game streamable — it says *this game is available to stream, to these testers, in these regions, on these kinds of servers/lanes*. Stored in Partner Registry. |
| **Title** | The game record itself, which gets **attached** to an offering. |
| **Install id** | A unique id for a specific installable chunk of content. |
| **Hash (content hash)** | A **fingerprint** (a long unique string) of the **exact** game+DLC version. Different build → different hash. On a PC server, "what version is installed?" is answered by the hash. |
| **content-targets** (service) | The xCloud service that decides **how many** servers to keep for each server set and **which** content to install on them. Think "warehouse stock manager." |
| **PC Orchestrator** (service) | The xCloud service that actually runs/tracks the PC servers and knows what's installed on each. The source of truth for PC server state. |
| **OS Targets** | The platform list that says **which SUGs (lanes) exist** and which servers belong to them. To create the `PC_PLAYTEST` lane, it has to be added here. |
| **content-ingestion / CTIN** (service) | The xCloud service that runs the **publish workflow**: takes a build, gets it into the system, creates the offering, and waits for the server to be ready. |
| **Partner Registry** | The service that stores offerings and titles (the catalog/listings database). |
| **Install‑on‑attach** | The behavior where simply **adding the title to the offering** causes the system to install it on a server. It exists already but is **turned off by default**; we turn it on just for the playtest lane. |
| **Quota** | The **max number of servers** allowed in a server set. We set it to **1**. |
| **Predictions** | content-targets' way of estimating how many servers a piece of content needs. For PC it's just hard‑coded to **1 per install** — we only want one server. |
| **Readiness poll** | CTIN **repeatedly checking** ("polling") whether the server has the build yet, before declaring the playtest "ready." |

---

## 2. The big picture, with an analogy

Imagine a **warehouse of game‑server machines**:
- The machines are organized into labeled **shelves** = **SUGs** (lanes). `GA` is the giant public shelf. We want a small
  new shelf labeled **`PC_PLAYTEST`** just for playtests.
- A **server set** is "this many machines of this type, on this shelf, in this warehouse (region)."
- The **offering** is the game's storefront listing. It says which shelf the game should live on.
- **content-targets** is the stock manager: it reads the listings, and for anything that should be on the `PC_PLAYTEST`
  shelf, it says "put one machine on that shelf and install this game on it."
- **PC Orchestrator** is the floor that actually has the machines and knows what's installed where.
- **CTIN** is the clerk who placed the order and now keeps walking to the shelf to check "is the game installed yet?"
  before telling the tester "you can play."

The work in this doc: put the game's listing on the `PC_PLAYTEST` shelf, turn on "auto‑stock one machine," and have the
clerk check until it's done. The platform team still has to **physically create the `PC_PLAYTEST` shelf** (register the SUG).

---

## 3. Why PC is special (Xbox vs PC)

- **Xbox** servers **pre‑pull** content (they download games ahead of time on their own) and report what they have. So
  "is it installed?" is already answered.
- **PC** servers **don't** pre‑pull. Content only lands **on demand**, and only when something explicitly triggers an
  install. And because each playtest publish can be a **new build**, "is this game installed somewhere?" isn't enough —
  we must confirm **the exact version** (the hash) is installed.

That's why PC needs this extra work and Xbox doesn't.

---

## 4. The end‑to‑end flow, step by step

Heads‑up: the word "install" is used for **two different things**, and the order matters:
- **Install #1 — content ingestion:** getting the build *into xCloud's content system* (so it's a known, resolvable
  package). This happens **first**.
- **Install #2 — PC‑server install:** putting that build *onto an actual GPU server* so it can be streamed. This happens
  **later, and is triggered by attaching the title to the offering**.

The publish workflow (`PlaytestTitleIngestionWorkflow` in CTIN) runs these stages in order:
1. **Validate** the request.
2. **Ingest the build** (Install #1) and wait for it to finish.
3. **Create the package + version 1.0** (a tidy record of the build).
4. **Create the offering and attach the title** — this is the step that says "this game is streamable, on the
   `PC_PLAYTEST` lane."
5. **That attach triggers Install #2** — content-targets notices the title is on the `PC_PLAYTEST` lane and tells PC
   Orchestrator to set aside one machine and install the build. CTIN **polls** here until a server reports it.
6. **Mark it ready** — the tester gets a working launch link.

In one sentence: **ingest the build → package it → put it on the `PC_PLAYTEST` lane (attach to offering) → that triggers
one PC server to install the exact build → keep checking until that server has it → ready.**

---

## 5. The three PRs — what each does and why (in depth)

There are three small changes, one per service. Each is a **draft PR** (a proposed change not yet merged).

### PR‑A · `services.contenttargets` · PR #15946980
**Plain English:** "For the `PC_PLAYTEST` lane, automatically keep **one** machine and install the playtest build on it."

This is the piece that makes the PC‑server install (Install #2) actually happen. It's two small config settings in
`appsettings.ContentTargets.Int.json`:
- **Quota = 1 (one machine):** under a `STANDARD_NC64AS_T4_V3` server type, `QuotasBySugByRegion.WESTUS2.PC_PLAYTEST = 1`.
  This both **creates** the `PC_PLAYTEST` server set and caps it at one machine.
- **Turn on install‑on‑attach for this lane:** a `ResolutionConfiguration.IncludePredictions` override
  (`ServerType = PC`, `Sugs = [PC_PLAYTEST]`, `Value = true`).

**Why both are needed (the mechanism):** on PC, the "how many servers should have this content" number comes only from
**predictions**, which the system hard‑codes to **1 per install**. But predictions are **off by default** — they're only
counted when `IncludePredictions` is turned **on** for that server set. So:
- The **quota** creates the lane and gives it capacity (1 machine), but on its own the "needed count" is 0 → nothing installs.
- The **override** turns the needed count into 1 → PC Orchestrator provisions one machine and installs the build.
- You need **both**.

**Tests:** the content-targets unit test suite passes **24/24**. The key test (`ResolutionProcessorTests`) proves that
with the override **on**, the lane's target becomes **1** (install happens); with it **off**, the target is **0**
(nothing installs). A second test proves the override only matches PC servers on the `PC_PLAYTEST` lane (not Xbox, not `GA`).

### PR‑B · `services.partnerregistry` · PR #15949594
**Plain English:** "Put the playtest game's listing **on the `PC_PLAYTEST` lane**, so content-targets knows where to send it."

In `PlaytestProcessor.cs`, when a playtest is a PC title, the offering now records the lane:
`OfferingV2.SelectableSystemUpdateGroups = [PC_PLAYTEST]` (it already recorded the server type
`TargetServerSkus = [STANDARD_NC64AS_T4_V3]`).

**Why it's needed:** content-targets looks at each offering and reads which lane(s) it targets, then maps the game's
installs to `region / SUG / SKU`. Before this change the offering listed a region and a server type but **no lane**, so
the game mapped to **no** server set and Install #2 had nowhere to go. This is the missing link between PR‑A and PR‑C.

**Tests:** the partner-registry test passes **12/12** (it checks the offering now carries `PC_PLAYTEST`).

### PR‑C · `services.contentingestion` (CTIN) · PR #15896502
**Plain English:** "After we ask for the install, keep checking the servers until one actually has **this exact build**,
then say ready."

This is the **readiness poll** (step 5). The method `PollPcFirstInstallAsync`:
1. **Resolves** the just‑ingested build to get its **install id** and its **hash** (the exact‑version fingerprint).
2. Asks **PC Orchestrator**: "do you have any server reporting this exact `install id` + `hash`?" (plus the lane, region,
   and server type, so it only looks at the right machines).
3. **No server yet → wait and try again** (retry). **A server has it → mark ready.**

It also adds a small config block, `PlaytestPcReadinessQuery` (lane / regions / server types), so the poll looks at the
right place. The values are set for both non‑prod environments (**Int** and **Test**): `PC_PLAYTEST` / `WESTUS2` /
`STANDARD_NC64AS_T4_V3`. Prod is intentionally left unset for now.

**Tests:** the CTIN test passes **11/11** (including that the configured lane/region/server‑type are sent in the query).

**One known limitation (already tracked):** when picking which version to wait for, the code currently picks the
"currently available" version, which is *almost always* the just‑published one — but on a quick **republish** it could
in theory pick the previous build's hash. First‑publish is correct; the fix (pin to the exact just‑ingested version) is
tracked as work item 62521491.

---

## 6. Verified against what the platform owner (Timi) described

This was designed in a meeting with Timi Bolaji (who owns the PC server side). His words map to the three PRs:

| What Timi said (verbatim) | Which PR it became |
|---|---|
| "we should have one SKU … one SUG and we use that for every play test" / "a distinct PC underscore play test SUG" | the single `PC_PLAYTEST` lane + single `STANDARD_NC64AS_T4_V3` server type used by all three PRs |
| "content targets will notice that the title is in this offering … if it's in this offering, then I should install at least one … we already have that implemented today. I just have it disabled … for playtest we can conditionally enable it" | **PR‑A** (turn the behavior on for this lane) + **PR‑B** (put the title on the lane) |
| "we now have a quota configuration … the max number of servers a sug can have … set that to one. It's one T4 … it's a dynamic config" | **PR‑A** quota = 1 |
| "once you merge … the offering config, distribution service should start doing one installation … once that installation is done … this content is now available on this server. So then, while you're doing your polling, eventually should magically just show up … ready to play" | the attach→install→poll sequence; **PR‑C** marks ready |
| "the version … on a PC server is actually the hash … the install ID is install ID and the version is the hash … put that in the content file filter … query for servers and wait until something shows up" | **PR‑C** asks PC Orchestrator for the exact `install id` + `hash` |

**One nuance:** Timi described turning the enable + quota on as a **runtime "dynamic config" flip he would do himself**,
"not … done programmatically." PR‑A is the **checked‑in** version of the same settings. content-targets can read either
the file or a runtime override, so both work — we just need to confirm with him whether he flips it live or merges PR‑A
(see §10).

---

## 7. The one thing left — "registering the `PC_PLAYTEST` SUG" (what that even means)

"Registering the SUG" means **actually creating the `PC_PLAYTEST` lane** so the platform knows it exists and real
machines belong to it. Until that happens, all three PRs point at a lane that isn't there yet. It has to be done in two
places, both owned by the platform team (Timi):

1. **OS Targets (the required one):** add `PC_PLAYTEST` for the `STANDARD_NC64AS_T4_V3` server type in `WESTUS2`. This is
   what makes real PC machines run in that lane. Without it, content-targets won't even create the server set, so nothing
   can install.
2. **The recognized‑lane list in code (`Services.Common.Ids`):** the set of valid SUG names is a fixed list in a shared
   library (it currently has `GA`, `Canary`, etc., but **not** `PC_PLAYTEST`). The Partner Registry only *warns* (it
   doesn't hard‑block) if an offering uses an unlisted lane, but `PC_PLAYTEST` should be added there for cleanliness — or
   confirmed to have a dynamic path.

Why this is someone else's job: creating a server lane + assigning machines is platform/infrastructure work. Timi said in
the meeting "we **will have** a distinct PC_playtest SUG … I have things set up that way already," so he owns it — we just
need the exact name and confirmation it's been done.

This is also tracked as a blocker: [`../Blockers/pc-playtest-sug-registration.md`](../Blockers/pc-playtest-sug-registration.md).

---

## 8. How to test that this works

### A. Right now — unit tests (already green)
Each PR has automated tests proving its piece in isolation:
- content-targets: `dotnet test src/Tests/Unit/ContentTargets.Core.UnitTests -p:StaticWebAssetsEnabled=false` → **24/24**.
- partner-registry: `dotnet test …/PartnerRegistryService.UnitTests --filter PlaytestProcessorTests -p:StaticWebAssetsEnabled=false` → **12/12**.
- CTIN: `dotnet test …/ContentCatalog.Ingestion.Core.UnitTests --filter PlaytestTitleIngestionWorkflowTests` → **11/11**.
  *(The `-p:StaticWebAssetsEnabled=false` flag avoids a flaky OneDrive file‑lock during the web‑project build.)*

### B. After the lane is registered + the 3 changes deploy — check each layer in order
1. **Is the lane real?** Confirm `PC_PLAYTEST` is in OS Targets for the server type/region, and recognized in the Ids list.
2. **Did the listing land on the lane?** Publish a PC playtest, then look at the offering and confirm it carries
   `SelectableSystemUpdateGroups = ["PC_PLAYTEST"]`. *(Proves PR‑B.)*
3. **Did content-targets stock the lane?** content-targets has a built‑in diagnostic console ("Savant" — the dashboard
   Timi used in the demo). For the server set id `WESTUS2/PC_PLAYTEST/STANDARD_NC64AS_T4_V3`:
   - `sst sugs=PC_PLAYTEST` → the `PC_PLAYTEST` server set exists *(quota + OS Targets worked)*.
   - `sstm WESTUS2/PC_PLAYTEST/STANDARD_NC64AS_T4_V3` → `ServerQuota = 1`.
   - `ssti …` → the playtest's install id is mapped to the lane *(PR‑B worked)*.
   - `sstt …` → the lane's target is **1** *(PR‑A's enable worked)*.
4. **Did a machine actually install it?** Ask PC Orchestrator for a server reporting the content (install id + hash) — it
   appears once the install finishes.
5. **Did the poll mark it ready?** Check the publish job status (`GET /v3/workflows/playtesttitleingestion/{jobId}`) — it
   should flip to success, and the worker log shows "PC install successful." *(Proves PR‑C.)*

### C. End‑to‑end (the real proof)
Publish a PC playtest for the pilot creator → walk through B2–B5 → open the launch link
(`https://play.xbox.com/play/launch/{productId}?offeringId=xpt{PlaytestProductId}`) and confirm the game streams. Then
**republish a new build** and confirm the poll waits for the **new** hash (exercises the limitation noted in PR‑C).

---

## 9. Code‑review (rubber‑duck) findings + resolutions (2026-06-20)
A review of all three PRs raised these; each is resolved or flagged:
- **PR‑B "which offering field" — resolved, no change.** `services.auth` (`UserLoginProcessor.cs:739`) reads
  `offering.SelectableSystemUpdateGroups` to tell the client which lanes are available, and content-targets reads both
  lane fields, so `SelectableSystemUpdateGroups = [PC_PLAYTEST]` is correct. (If live allocation testing ever shows the
  tester's machine isn't picked from the lane, also set `SystemUpdateGroupWeights = { PC_PLAYTEST: 100 }`.)
- **PR‑A override scope — intentional.** The enable is keyed on the lane only (`Sugs=[PC_PLAYTEST]`), not region/SKU, so it
  works wherever the dedicated playtest lane exists. (Locking it to one region/SKU would silently break if capacity is
  added elsewhere.)
- **Region capitalization — fine.** content-targets uses `WESTUS2`, the offering uses `WestUS2`; the id type compares
  case‑insensitively, so they match.
- **Timeout vs approval — flag.** CTIN starts polling right after creating the offering, but the offering can require a
  human approval that may take up to ~48h, while the poll currently gives up after **6h**. Raise that timeout (or wait
  for the offering to be live) before relying on it. *(Tracked with [`../Blockers/manual-pr-polling.md`](../Blockers/manual-pr-polling.md).)*
- **CTIN environment — resolved.** The CTIN worker **does** have an `Int` environment (helm `values.en-int.yaml`,
  `aspNetEnv: Int`); it just had no `appsettings.Int.json` file before. The poll config is now set in **both**
  `appsettings.Int.json` and `appsettings.Test.json`, matching the content-targets Int+Test enablement.
- **Republish version pick — known item 62521491** (see PR‑C limitation).
- **Lane set for all PC playtests — note.** Fine because this code path only creates PC streaming playtests; if
  non‑streaming PC playtests ever share it, gate it on a streaming flag.

---

## 10. Open questions for the platform owner (Timi)
1. **Exact lane name** — we assumed `PC_PLAYTEST`; must match OS Targets, the Ids list, content-targets, the offering, and CTIN.
2. **Is the lane already created** (OS Targets + Ids) for `STANDARD_NC64AS_T4_V3` in `WESTUS2`?
3. **Who turns on enable + quota** — Timi via live "dynamic config," or by merging PR‑A?
4. **Server type** — `STANDARD_NC64AS_T4_V3` is a hardcoded placeholder (a `const` with a "resolve dynamically" TODO,
   and validation only checks it is non‑empty). The existing non‑prod content-targets fleet uses a *different* T4 SKU
   (`STANDARD_NC8AS_T4_V3`), so this needs confirming. Is `STANDARD_NC64AS_T4_V3` the right SKU, and should we config‑drive it?
5. **Test provisioning** — does Test OS Targets actually have `STANDARD_NC64AS_T4_V3` in `WESTUS2`? If not the Test
   config is a harmless no‑op until that infra exists. (Both Int and Test now carry the config.)
6. **Production** — the enable mechanism currently allows only one override, already used by Xbox; production needs that
   extended (and a different region, `NorthCentralUs`).

### Ready‑to‑send message to Timi

> **Subject: PC playtest streaming — need the `PC_PLAYTEST` SUG registered/provisioned**
>
> Hi Timi — following up on the PC playtest install-on-attach work from the xCloud ingestion sync. The three
> code/config changes are done and tested, all pinned to **SUG `PC_PLAYTEST`**, **SKU `STANDARD_NC64AS_T4_V3`**,
> **region `WESTUS2`** (Int):
>
> - Content Targets (enable install-on-attach + quota=1): PR 15946980
> - Partner Registry (sets the SUG on the playtest offering): PR 15949594
> - Content Ingestion (readiness poll by install-id + version hash): PR 15896502
>
> The only thing blocking end-to-end is the SUG itself. You mentioned you'd have a distinct PC_playtest SUG and
> "have things set up that way already," so a few quick questions:
>
> 1. **Exact SUG name** — is it `PC_PLAYTEST`, or something else? (I'll match it across all three PRs.)
> 2. **OS Targets** — is `PC_PLAYTEST` already provisioned for `STANDARD_NC64AS_T4_V3` in `WESTUS2` (Int), or does
>    that still need doing? (Content Targets only builds the server set for SUGs in the OS Targets manifest.)
> 3. **Recognition** — `PC_PLAYTEST` isn't in the `SystemUpdateGroup` list in `Services.Common.Ids` today, so the
>    offering hits a (non-critical) validation warning. Does it need adding there, or is there a dynamic path?
> 4. **Enable + quota** — flip via dynamic config (as you described), or land the Content Targets PR as the
>    checked-in source? If dynamic, the keys are:
>    `ServerSetsConfiguration:SkuConfigs:STANDARD_NC64AS_T4_V3:QuotasBySugByRegion:WESTUS2:PC_PLAYTEST = 1` and
>    `ResolutionConfiguration:IncludePredictions:Override = { Value: true, ServerType: PC, Sugs: [PC_PLAYTEST] }`.
> 5. **SKU** — `STANDARD_NC64AS_T4_V3` is currently a hardcoded stand-in on the offering; is that the right T4 SKU?
>
> Once I have the exact name + confirmation the SUG is provisioned, everything else is already wired. Thanks!

---

## 11. Owners
Melanie Chen (the three code/config changes) · Timi Bolaji (creating the `PC_PLAYTEST` lane in OS Targets + Ids, SKU
confirmation, and the dynamic-config flip).

## 12. Sources (where to look in the code)
- services.contentingestion: `Workflows/PlaytestTitleIngestionWorkflow.cs` (the stage order and `PollPcFirstInstallAsync`).
- services.contenttargets: `Processors/Implementations/{ResolutionProcessor,ServerSetsProcessor,PredictionsProcessor}.cs`,
  `Configuration/{ConfigItem,ResolutionConfiguration,SkuConfiguration}.cs`, `Extensions/{OfferingExtensions,TitleExtensions}.cs`,
  `Contracts/{TargetsQuery,TargetsCalculationMode}.cs`, `Savant/DefaultSavantProvider.cs` (the diagnostic console).
- services.pcservices: `Orchestrator.Core/Manifests/ConfigManifestProvider.cs`.
- services.partnerregistry: `Processors/PlaytestProcessor.cs`, `Processors/Validation/ValidationProcessorUtilities.cs`,
  `Controllers/SystemUpdateGroupConfigController.cs`.
- `Transcripts/XCloudIngestion.docx` (the design meeting with Timi Bolaji).
- [`./pc-install-readiness-polling-implementation.md`](./pc-install-readiness-polling-implementation.md) and
  [`../Blockers/pc-playtest-sug-registration.md`](../Blockers/pc-playtest-sug-registration.md).
