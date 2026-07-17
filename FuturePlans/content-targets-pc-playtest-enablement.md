# PC playtest streaming readiness — a complete, plain‑English guide

> **If you're new to this, start at sections 0–4.** They explain the whole thing with no assumed knowledge.
> Sections 5+ are the detailed engineering record (the three PRs, the test plan, and what's left).

**Status (2026-06-22):** The partner-registry and content-ingestion code changes remain draft PRs. Per Timi, the
content-targets enable + quota change is **dynamic config**, not checked-in `appsettings`; PR 15946980 is superseded and
should be abandoned once Timi applies the dynamic-config change. Everything is pinned to three values: **`PC_PLAYTEST`**
(the lane), **`STANDARD_NC64AS_T4_V3`** (the server type), and **`WESTUS2`** (the datacenter region).

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

There are three small changes, one per service. The partner-registry and content-ingestion changes are draft PRs; the
content-targets PR is now superseded by dynamic config.

### PR‑A · `services.contenttargets` · PR #15946980 — superseded by dynamic config
**Plain English:** "For the `PC_PLAYTEST` lane, automatically keep **one** machine and install the playtest build on it."

Per Timi's review, this must be done with **dynamic config**, not checked into `appsettings`. PR 15946980's `appsettings`
changes have been reverted and the PR should be abandoned once the dynamic-config change is live.

**Dynamic-config payload (quota):** in ConfigSection `CONTENTTARGETS/DEFAULT/SERVERSETSCONFIGURATION`
(portal path `DynamicConfigPartnerRegistry/ConfigSections/CONTENTTARGETS/DEFAULT/SERVERSETSCONFIGURATION`), update the
existing `SkuConfigs -> STANDARD_NC64AS_T4_V3 -> QuotasBySugByRegion -> WESTUS2` block by adding only this SUG entry:

```json
"PC_PLAYTEST": 1
```

The `STANDARD_NC64AS_T4_V3` SKU block already exists in live dynamic config with `GameplaySlotsPerServer = 4` and
`DefaultMaxLocalSpaceInMB = 2000000`; do **not** restate or replace those values. The checked-in PR attempted to add a new
SKU block with `GameplaySlotsPerServer = 1` and `DefaultMaxLocalSpaceInMB = 360445`, which disagrees with live config and
would clobber the real SKU settings. That value discrepancy is the concrete reason the appsettings approach was wrong.

**Dynamic-config payload (enable / open question):** if PC playtest still needs the install-on-attach enable override, it
belongs in ConfigSection `CONTENTTARGETS/DEFAULT/RESOLUTIONCONFIGURATION`, as:

```json
{
  "IncludePredictions": {
    "Override": {
      "Value": true,
      "ServerType": "PC",
      "Sugs": [ "PC_PLAYTEST" ]
    }
  }
}
```

**Open question for Timi:** confirm whether this `IncludePredictions` override is needed at all in Int/Test. Existing PC
test SUGs such as `PC_TAKEHOME` already have working quotas in dynamic config without an obvious per-SUG
`IncludePredictions` override, so non-prod may already have predictions enabled through another path.

> **✅ RESOLVED (2026-07-08) — the override IS required, and prod is now enabled.** Without it, content-targets never
> computes a predicted target for the SUG, so nothing installs → `ContentOffline`/`NOMATCHINGSERVER`. Timi applied it in
> **prod** via [PR 16114214](https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.data.partnerregistry/pullrequest/16114214),
> **inverting** the shape above because `ConfigItem.Override` allows only one override and XBOX already held it:
> `IncludePredictions.DefaultValue = true` + a single PC override setting `Value: false` for a **deny-list of internal PC
> test SUGs** that excludes `PC_PLAYTEST` (so it stays true). This is also why the existing PC test SUGs work "without an
> obvious override" — they inherit the default. The content-distribution twin `IncludePredictedTargets` had to be enabled
> too ([PR 16114118](https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.data.partnerregistry/pullrequest/16114118)).
> Full chain: [`../Explanations/pc-playtest-streaming-allocation-e2e.md`](../Explanations/pc-playtest-streaming-allocation-e2e.md).

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
2. Asks **PC Orchestrator**: "do you have any server reporting this exact `install id` + `hash`?" (plus the lane and
   server type, so it only looks at the right machines).
3. **No server yet → wait and try again** (retry). **A server has it → mark ready.**

It also adds a small config block, `PlaytestPcReadinessQuery` (lane / server types), so the poll looks at the right
place. The values are set for both non‑prod environments (**Int** and **Test**): `PC_PLAYTEST` / `STANDARD_NC64AS_T4_V3`.
Prod is intentionally left unset for now.

**Region — not filtered (Timi review, commit `0fab4be6`).** Per platform guidance the poll uses a **"first region"
assumption**: a server in *any* region reporting the exact ingested version is sufficient, so the query no longer sets
`Regions` (the `PlaytestPcReadinessQuery.Regions` config + its appsettings entries + the env‑provider region fallback
were removed). Region targeting is deferred until we steer developers to specific regions for performance.

**Tests:** CTIN unit tests green (Core + Worker), including assertions that the configured lane/server‑type are sent in
the query and the `ConfigureOfferingAsync` routing / per‑stage guards.

**Open — resolution business logic for playtests (needs Jack walkthrough).** A PR‑C reviewer flagged: *"Resolution code needs some special business
logic for playtests. Jack can probably walk you through it."* The poll selects the target build via `version.IsCurrent`
(where `IsCurrent => AvailableFrom == null`), and the resolver marks a version "current" only once its asset versions
satisfy `AvailableFrom <= now < AvailableUntil` (`CosmosDALManager`). For a freshly‑published playtest build that needs
confirming — immediate availability for the playtest's flights + sandbox, exactly one current version, and republish
ordering. **Needs a walkthrough with Jack before implementing** (do not speculatively change the shared resolver). See
§10 Q7 and [PRProgress 17](../PRProgress/17-CTIN-15896502-pc-install-readiness-polling.md).

**One known limitation (already tracked, related to the above):** when picking which version to wait for, the code
filters to the *current* PC version and requires **exactly one** (zero/multiple → retry, so a republish can't confirm
against a stale build). The full fix — pin to the exact just‑ingested version rather than inferring via `IsCurrent` — is
tracked as work item 62521491 and is intertwined with the resolution business logic above.

---

## 6. Verified against what the platform owner (Timi) described

This was designed in a meeting with Timi Bolaji (who owns the PC server side). His words map to the three PRs:

| What Timi said (verbatim) | Which PR it became |
|---|---|
| "we should have one SKU … one SUG and we use that for every play test" / "a distinct PC underscore play test SUG" | the single `PC_PLAYTEST` lane + single `STANDARD_NC64AS_T4_V3` server type used by all three PRs |
| "content targets will notice that the title is in this offering … if it's in this offering, then I should install at least one … we already have that implemented today. I just have it disabled … for playtest we can conditionally enable it" | dynamic config (turn the behavior on for this lane, if needed) + **PR‑B** (put the title on the lane) |
| "we now have a quota configuration … the max number of servers a sug can have … set that to one. It's one T4 … it's a dynamic config" | `SERVERSETSCONFIGURATION` dynamic-config quota = 1 |
| "once you merge … the offering config, distribution service should start doing one installation … once that installation is done … this content is now available on this server. So then, while you're doing your polling, eventually should magically just show up … ready to play" | the attach→install→poll sequence; **PR‑C** marks ready |
| "the version … on a PC server is actually the hash … the install ID is install ID and the version is the hash … put that in the content file filter … query for servers and wait until something shows up" | **PR‑C** asks PC Orchestrator for the exact `install id` + `hash` |

**Dynamic-config pivot (2026-06-22):** Timi confirmed the enable + quota settings should live in dynamic config, not
checked-in `appsettings`. PR‑A is now superseded: its `appsettings` additions were reverted, and it should be abandoned
once Timi applies the dynamic config described in §5.

---

## 7. The one thing left — registering the `PC_PLAYTEST` SUG (you can self‑serve this)

"Registering the SUG" means **actually creating the `PC_PLAYTEST` lane** so the platform knows it exists and real
machines run the right OS image in it. Until that happens, all three PRs point at a lane that isn't there yet.

**Update (Jack, 2026‑06‑22): this is no longer blocked on Timi — you can set the SUG up yourself.** Jack: *"you need
quota (covered in your first PR) then you need to go to the PC SUG configuration page and set up the SUG … I'll recommend
inheriting from a 'production'/release SUG. PC_TAKEHOME is currently our most solid."* So it's two parts:

1. **Quota (dynamic config):** add the `PC_PLAYTEST` quota under `CONTENTTARGETS/DEFAULT/SERVERSETSCONFIGURATION` (see §5
   PR‑A and the copy/paste values in
   [`./pc-playtest-dynamic-config-and-sug-setup.md`](./pc-playtest-dynamic-config-and-sug-setup.md)). This says the lane is
   *allowed* a server.
2. **SUG definition (PC SUG Definitions page):** at <https://americas.gssv-dev-prod.xboxlive.com/PcSugDefinitions> →
   **Add PC Sug Definition** → `Sug Id = PC_PLAYTEST`, **`Inherits From = PC_GA`** (accepted for Test/Int per user
   guidance), then **Link to Parent** for Developer Settings *and* Flighting Configs so it inherits the parent SUG's
   known‑good OS images. ⚠️ If you *don't* link/inherit, the page demands a manual Flighting Config row with a non‑empty
   **Version** ("At least one Flighting Config is required when configs are not inherited") — inheriting from PC_TAKEHOME is
   exactly how you avoid hand‑picking image versions. Writing this entry satisfies the OS Targets requirement below.

Still platform‑owned (confirm with Timi): the **recognized‑lane list in code (`Services.Common.Ids`)** is a fixed list
(`GA`, `Canary`, … but **not** `PC_PLAYTEST`). Partner Registry only *warns* (it doesn't hard‑block) on an unlisted lane,
but `PC_PLAYTEST` should be added for cleanliness — or confirmed to have a dynamic path. And confirm real GPU capacity for
the chosen SKU exists in the target region (the NC64 vs NC8 decision in §10 Q4 / the setup doc).

This is also tracked as a blocker: [`../Blockers/pc-playtest-sug-registration.md`](../Blockers/pc-playtest-sug-registration.md).

---

## 8. How to test that this works

### A. Right now — unit tests (already green)
Each code PR has automated tests proving its piece in isolation; content-targets dynamic config must be verified live:
- content-targets: `dotnet build src/Product/ContentTargets.Core/ContentTargets.Core.csproj -v minimal` after reverting appsettings; live validation through Savant after Timi's dynamic-config flip.
- partner-registry: `dotnet test …/PartnerRegistryService.UnitTests --filter PlaytestProcessorTests -p:StaticWebAssetsEnabled=false` → **12/12** (verified 2026‑06‑22).
- CTIN: `dotnet test …/ContentCatalog.Ingestion.Core.UnitTests --filter PlaytestTitleIngestionWorkflowTests -p:StaticWebAssetsEnabled=false` → **16/16** (verified 2026‑06‑22).
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
   - `sstt …` → the lane's target is **1** *(dynamic-config enable worked, if an explicit override is needed)*.
4. **Did a machine actually install it?** Ask PC Orchestrator for a server reporting the content (install id + hash) — it
   appears once the install finishes.
5. **Did the poll mark it ready?** Check the publish job status (`GET /v3/workflows/playtesttitleingestion/{jobId}`) — it
   should flip to success, and the worker log shows "PC install successful." *(Proves PR‑C.)*

### C. End‑to‑end (the real proof)
Publish a PC playtest for the pilot creator → walk through B2–B5 → open the launch link
(`https://play.xbox.com/play/launch/{productId}?offering.id=xpt{PlaytestProductId}`) and confirm the game streams. Then
**republish a new build** and confirm the poll waits for the **new** hash (exercises the limitation noted in PR‑C).

---

## 9. Code‑review (rubber‑duck) findings + resolutions (2026-06-20)
A review of all three PRs raised these; each is resolved or flagged:
- **PR‑B "which offering field" — resolved, no change.** `services.auth` (`UserLoginProcessor.cs:739`) reads
  `offering.SelectableSystemUpdateGroups` to tell the client which lanes are available, and content-targets reads both
  lane fields, so `SelectableSystemUpdateGroups = [PC_PLAYTEST]` is correct. **Update (Timi review):** `SystemUpdateGroupWeights
  = { PC_PLAYTEST: 100 }` is now also set on the offering (PTNR commit `4f0d329a`) — `SelectableSystemUpdateGroups` only
  lets a client *request* a lane, but a tester just clicks a link, so default allocation needs the SUG **weighted** to land
  launched sessions on PC_PLAYTEST servers.
- **IncludePredictions override scope — if needed, keep it lane-scoped.** The enable is keyed on the lane only
  (`Sugs=[PC_PLAYTEST]`), not region/SKU, so it works wherever the dedicated playtest lane exists. (Locking it to one
  region/SKU would silently break if capacity is added elsewhere.)
- **Region capitalization — fine.** content-targets uses `WESTUS2`, the offering uses `WestUS2`; the id type compares
  case‑insensitively, so they match.
- **Timeout vs approval — flag.** CTIN starts polling right after creating the offering, but the offering can require a
  human approval that may take up to ~48h, while the poll currently gives up after **6h**. Raise that timeout (or wait
  for the offering to be live) before relying on it. *(Tracked with [`../Blockers/manual-pr-polling.md`](../Blockers/manual-pr-polling.md).)*
- **CTIN environment — resolved.** The CTIN worker **does** have an `Int` environment (helm `values.en-int.yaml`,
  `aspNetEnv: Int`); it just had no `appsettings.Int.json` file before. The poll config is now set in **both**
  `appsettings.Int.json` and `appsettings.Test.json`, matching the intended non-prod content-targets dynamic config.
- **Republish version pick — interim hardening landed; full fix tracked as 62521491.** The poll picks the just‑ingested
  build by its content hash. It now filters to the *current* PC version and requires **exactly one** — zero or multiple
  current versions route to retry rather than risk confirming readiness against a stale/wrong build (commit `3ae1dccc`,
  with a unit test for the multiple‑current case). The full fix (pin to the exact ingested version instead of inferring
  via `IsCurrent`) still needs the resolver contract and stays tracked as **62521491**.
- **Resolution business logic for playtests — OPEN (needs Jack walkthrough).** PR‑C review: *"Resolution code needs some
  special business logic for playtests. Jack can probably walk you through it."* The poll keys on `version.IsCurrent`
  (`IsCurrent => AvailableFrom == null`), and the resolver derives "current" purely from availability windows
  (`CosmosDALManager`: current = `AvailableFrom < resolveTime`, ordered desc). For a freshly‑published *playtest* build,
  unconfirmed: (a) is it marked current/resolvable immediately under the playtest's flights + sandbox, or does it need a
  playtest‑specific availability rule; (b) can two versions be "current" at once (→ the exactly‑one guard retries
  forever); (c) does the special logic live in the shared `ResolutionProcessor` (Common.Core) or the
  `ContentCatalog.Resolution.Service` resolver. **Do not change the shared resolver speculatively** — sync with Jack
  first. This is the last open code item on PR‑C; it overlaps with 62521491 (resolving by explicit install id would
  sidestep the `IsCurrent` inference entirely).
- **Xbox readiness path still hardcoded — flag.** The non‑PC branch hardcodes region (`WestEurope` non‑prod), `SUG = GA`,
  and `ServerType = XboxV3SeriesS`, unlike the now config‑driven PC path. Pre‑existing, but if Xbox playtests share this
  workflow and their servers aren't in that region/SUG, that poll would false‑timeout. Decide whether to config‑drive it too.
- **Lane set for all PC playtests — note.** Fine because this code path only creates PC streaming playtests; if
  non‑streaming PC playtests ever share it, gate it on a streaming flag.

---

## 10. Open questions for the platform owners (Timi / Jack)
1. **Exact lane name** — we assumed `PC_PLAYTEST`; must match OS Targets, the Ids list, content-targets, the offering, and CTIN.
2. **Lane creation** — the SUG definition is now **self‑serve** via the PC SUG Definitions page (§7: `PC_PLAYTEST` inheriting
   `PC_GA`). Confirm with Timi only that (a) `PC_PLAYTEST` should be added to `Services.Common.Ids` (recognition), and
   (b) GPU capacity exists for the chosen SKU/region.
3. **Enable + quota** — Timi owns / grants the live dynamic-config change: add `PC_PLAYTEST = 1` under
   `CONTENTTARGETS/DEFAULT/SERVERSETSCONFIGURATION` for the chosen SKU / `WESTUS2`. Open: does Int/Test also need
   `CONTENTTARGETS/DEFAULT/RESOLUTIONCONFIGURATION` `IncludePredictions.Override` for `PC_PLAYTEST`, or are PC predictions
   already enabled for existing non-prod PC SUGs?
   > **✅ RESOLVED (2026-07-08):** the quota (16103771) **and** the predictions enable are both required and now live in
   > prod. Predictions enabled via `IncludePredictions` (16114214) + `IncludePredictedTargets` (16114118).
4. **Server type** — `STANDARD_NC64AS_T4_V3` is a hardcoded placeholder (a `const` with a "resolve dynamically" TODO,
   and validation only checks it is non‑empty). The existing non‑prod content-targets fleet uses a *different* T4 SKU
   (`STANDARD_NC8AS_T4_V3`), so this needs confirming. Is `STANDARD_NC64AS_T4_V3` the right SKU, and should we config‑drive it?
5. **Test provisioning** — the offering targets `WestUS2`/`WestEurope` in **both** Int and Test (the existing `WESTUS3`/`GA`
   entry in the Test fleet is a *separate, unrelated* fleet), and the playtest config matches it on `WESTUS2`. The only
   remaining unknown is infra: does Test OS Targets actually have the SKU provisioned in `WESTUS2` for the
   `PC_PLAYTEST` lane? If not, the Test config is a harmless no‑op until that infra exists.
6. **Production** — the enable mechanism currently allows only one override, already used by Xbox; production needs that
   extended (and a different region, `NorthCentralUs`).
   > **✅ RESOLVED (2026-07-08):** correct prediction — the single-override limit was the real prod snag. Rather than
   > extending `Override` to a list, Timi **inverted** to `DefaultValue: true` + a PC deny-list that excludes
   > `PC_PLAYTEST`, enabling both XBOX and PC_PLAYTEST through one override (PR 16114214). Region for playtest is
   > `WESTUS2` (the prod `PC_MAIN` pool is WESTUS2-only), not `NorthCentralUs`.
7. **Resolution business logic for playtests (needs Jack walkthrough).** PR‑C review: *"Resolution code needs some special business
   logic for playtests."* Schedule the walkthrough. Concrete questions to bring: does the resolver mark a just‑ingested
   playtest version `IsCurrent` (`AvailableFrom == null`) immediately under the playtest's flights + sandbox? Can multiple
   versions be current at once? Should the poll resolve by explicit install id (ties to 62521491) instead of inferring via
   `IsCurrent`? Which resolver owns the change — `ResolutionProcessor` (Common.Core) or `ContentCatalog.Resolution.Service`?

### Ready‑to‑send message to Timi

> **Subject: PC playtest streaming — need the `PC_PLAYTEST` SUG registered/provisioned**
>
> Hi Timi — following up on the PC playtest install-on-attach work from the xCloud ingestion sync. The three
> code/config changes are done and tested, all pinned to **SUG `PC_PLAYTEST`**, **SKU `STANDARD_NC64AS_T4_V3`**,
> **region `WESTUS2`** (Int):
>
> - Content Targets (quota=1 via dynamic config; PR 15946980 is superseded): `CONTENTTARGETS/DEFAULT/SERVERSETSCONFIGURATION`
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
> 4. **Enable + quota** — per your review, I'll abandon the checked-in Content Targets PR after you apply dynamic config.
>    For `CONTENTTARGETS/DEFAULT/SERVERSETSCONFIGURATION`, please add only
>    `SkuConfigs:STANDARD_NC64AS_T4_V3:QuotasBySugByRegion:WESTUS2:PC_PLAYTEST = 1`; the live SKU block already has
>    `GameplaySlotsPerServer = 4` and `DefaultMaxLocalSpaceInMB = 2000000`, so we should not replace it with the stale
>    checked-in values (`1` / `360445`). Open question: does Int/Test also need
>    `CONTENTTARGETS/DEFAULT/RESOLUTIONCONFIGURATION` `IncludePredictions.Override = { Value: true, ServerType: PC, Sugs: [PC_PLAYTEST] }`,
>    or are predictions already enabled for the existing non-prod PC SUGs?
> 5. **SKU** — `STANDARD_NC64AS_T4_V3` is currently a hardcoded stand-in on the offering; is that the right T4 SKU?
>
> Once I have the exact name + confirmation the SUG is provisioned, everything else is already wired. Thanks!

---

## 11. Owners
Melanie Chen (partner-registry + CTIN code changes) · Timi Bolaji (creating the `PC_PLAYTEST` lane in OS Targets + Ids,
SKU confirmation, and the content-targets dynamic-config flip).

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
