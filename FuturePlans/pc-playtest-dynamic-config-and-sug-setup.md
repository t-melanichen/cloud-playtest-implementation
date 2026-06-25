# PC playtest — dynamic config + SUG setup (copy/paste reference)

Practical reference for **standing up the `PC_PLAYTEST` lane** in content-targets. Two things have to be true before a
PC playtest can stream: (1) the lane has a **quota** (a server is allowed to exist) and (2) the lane is **defined** (the
GPU servers know which OS image to run). This file has the exact values to paste plus the open decisions for Timi.

---

## 1. The two parts of SUG setup (per Timi)

> *"For the SUG setup, you need quota (covered in your first PR) then you need to go to the PC SUG configuration page and
> set up the SUG. SUGs usually mean they get image versions (think OS builds) assigned to them. I'll recommend inheriting
> from a 'production'/release SUG. PC_TAKEHOME is currently our most solid."*

1. **Quota** — a dynamic-config line that says "the `PC_PLAYTEST` lane is *allowed* N servers." (Section 2 below.)
2. **SUG definition** — register the SUG itself so its servers get an **OS image version**. Done on the **PC SUG
   Definitions** page: <https://americas.gssv-dev-prod.xboxlive.com/PcSugDefinitions>. (Section 3 below.)

---

## 2. Dynamic config — `CONTENTTARGETS / DEFAULT / SERVERSETSCONFIGURATION` (copy/replace)

Portal: `DynamicConfigPartnerRegistry/ConfigSections/CONTENTTARGETS/DEFAULT/SERVERSETSCONFIGURATION` (per environment).
The only change is adding the `PC_PLAYTEST` quota; everything else is the current live value, left untouched.

> ⚠️ **SKU decision (confirm with Timi).** The code currently hardcodes SKU **`STANDARD_NC64AS_T4_V3`** (NC64), but the
> live Int/Test configs only have **`STANDARD_NC8AS_T4_V3`** (NC8) and (Int) `STANDARD_D4S_V3`. So either Int/Test has
> NC64 GPU capacity we add a block for (**Option A**), or the playtest should ride the existing NC8 fleet and the code SKU
> changes to match (**Option B**). Pick one with Timi.

### Int

**Current:**
```json
{
  "SkuConfigs": {
    "STANDARD_NC8AS_T4_V3": {
      "GameplaySlotsPerServer": 1,
      "DefaultMaxLocalSpaceInMB": 360445,
      "QuotasBySugByRegion": { "WESTUS2": { "GA": 1 } }
    },
    "STANDARD_D4S_V3": {
      "GameplaySlotsPerServer": 1,
      "DefaultMaxLocalSpaceInMB": 25000,
      "QuotasBySugByRegion": { "WESTUS2": { "PC_INTEGRATION_TESTING": 0 } }
    }
  }
}
```

**Option A — keep the code's NC64 SKU (needs NC64 capacity in Int):** add a new SKU block. ✅ **APPLIED in Int (merged) — PR 15966616** added exactly this NC64 block (`PC_PLAYTEST: 1`, slots=4) and left the live NC8/D4S blocks intact. Remaining open: confirm Int actually has NC64 GPU capacity in WESTUS2 (else the server set is a no-op until it exists).
```json
{
  "SkuConfigs": {
    "STANDARD_NC8AS_T4_V3": {
      "GameplaySlotsPerServer": 1,
      "DefaultMaxLocalSpaceInMB": 360445,
      "QuotasBySugByRegion": { "WESTUS2": { "GA": 1 } }
    },
    "STANDARD_D4S_V3": {
      "GameplaySlotsPerServer": 1,
      "DefaultMaxLocalSpaceInMB": 25000,
      "QuotasBySugByRegion": { "WESTUS2": { "PC_INTEGRATION_TESTING": 0 } }
    },
    "STANDARD_NC64AS_T4_V3": {
      "GameplaySlotsPerServer": 4,
      "DefaultMaxLocalSpaceInMB": 2000000,
      "QuotasBySugByRegion": { "WESTUS2": { "PC_PLAYTEST": 1 } }
    }
  }
}
```
(`GameplaySlotsPerServer: 4` / `DefaultMaxLocalSpaceInMB: 2000000` are the NC64 values from the live prod config.)

> **What `GameplaySlotsPerServer` means + the concurrency it implies.** It's the number of concurrent gameplay sessions a
> single server can host; content-targets computes `concurrencyQuota = ServerQuota × GameplaySlotsPerServer`
> (`ContentTargets.Core/Processors/Implementations/ResolutionProcessor.cs:196`, default `1` in `SkuConfiguration.cs:10`).
> The value tracks the SKU's **GPU count** — `STANDARD_NC64AS_T4_V3` (NC64as_T4_v3) has **4× NVIDIA T4 GPUs** (one stream
> per GPU) → `4`; `STANDARD_NC8AS_T4_V3` (NC8) has **1** → `1`. **Note:** only NC8 = `1` is checked into the repo
> appsettings; the NC64 = `4` block lives in live prod dynamic config, not source. **Implication:** with `PC_PLAYTEST`
> quota = **1** NC64 server, concurrency = `1 × 4 = 4` — one box can serve up to **4 concurrent testers**. (Sanity-check
> with Timi: his "it's one T4" phrasing reads like 1 GPU/session, but NC64as_T4_v3 is a 4-GPU box, so quota 1 there is 4
> slots, not 1 — Option B's NC8 fleet would be `1 × 1 = 1`.)

**Option B — ride the existing NC8 fleet (then change the code SKU to `STANDARD_NC8AS_T4_V3`):** add the SUG to the
existing block.
```json
{
  "SkuConfigs": {
    "STANDARD_NC8AS_T4_V3": {
      "GameplaySlotsPerServer": 1,
      "DefaultMaxLocalSpaceInMB": 360445,
      "QuotasBySugByRegion": { "WESTUS2": { "GA": 1, "PC_PLAYTEST": 1 } }
    },
    "STANDARD_D4S_V3": {
      "GameplaySlotsPerServer": 1,
      "DefaultMaxLocalSpaceInMB": 25000,
      "QuotasBySugByRegion": { "WESTUS2": { "PC_INTEGRATION_TESTING": 0 } }
    }
  }
}
```

> ✅ **Region:** Int runs in `WESTUS2`, which matches the offering's non-prod regions (`WestUS2` / `WestEurope`). Int is
> the cleanest place to validate first.

### Test

**Current:**
```json
{
  "SkuConfigs": {
    "STANDARD_NC8AS_T4_V3": {
      "GameplaySlotsPerServer": 1,
      "DefaultMaxLocalSpaceInMB": 352000,
      "QuotasBySugByRegion": { "WESTUS3": { "PC_GA": 1 } }
    }
  }
}
```

> ⚠️ **Region mismatch in Test — there is no clean "just paste this" value.** Verified: the offering targets
> **`WestUS2` / `WestEurope`** in non-prod (`PlaytestProcessor.cs:36`), but the Test content-targets fleet only has
> capacity in **`WESTUS3`** (SKU NC8). For a playtest to go ready, the quota must be in a region the offering targets **and**
> that has real GPU capacity — and in Test those don't overlap today:
> - `PC_PLAYTEST` under **`WESTUS3`** → quota exists but the offering never targets WESTUS3, so no install lands → never ready.
> - `PC_PLAYTEST` under **`WESTUS2`** → offering targets it, but Test has no GPU capacity there → no server appears → never ready.
>
> **Recommendation: validate in Int (WESTUS2 matches the offering) and leave Test until Timi aligns region/capacity.** Take
> the decision to Timi: does Test get WESTUS2 capacity for the playtest SKU (then add a WESTUS2 block like Int), or should
> the playtest ride the existing WESTUS3 NC8 fleet (then the offering's non-prod region + the code SKU must move to
> WESTUS3 / NC8)?
>
> If you nonetheless want the **internally-consistent** Test edit that matches the fleet that actually exists (WESTUS3 + NC8),
> add `PC_PLAYTEST` to the existing block — but know it's a **no-op for the playtest** until the offering reaches WESTUS3:
> ```json
> {
>   "SkuConfigs": {
>     "STANDARD_NC8AS_T4_V3": {
>       "GameplaySlotsPerServer": 1,
>       "DefaultMaxLocalSpaceInMB": 352000,
>       "QuotasBySugByRegion": { "WESTUS3": { "PC_GA": 1, "PC_PLAYTEST": 1 } }
>     }
>   }
> }
> ```

---

## 3. SUG definition — the PC SUG Definitions page

Page: <https://americas.gssv-dev-prod.xboxlive.com/PcSugDefinitions> (sign in).

A SUG definition assigns the **OS image versions** (the Windows/OS build the GPU servers run) per SKU. Rather than
hand-pick image versions, **create `PC_PLAYTEST` to inherit from a stable release SUG — `PC_TAKEHOME`** (Jack: "currently
our most solid"). Exact steps on the page → **Add PC Sug Definition**:

- **Sug Id** = `PC_PLAYTEST`
- **Inherits From** = **`PC_GA`** — the user confirmed this is acceptable for Test/Int, so no parent change is needed.
- **Link to Parent** for **Developer Settings** *and* **Flighting Configs** (the two "🔗 Link to Parent" buttons) so the
  definition **inherits** PC_TAKEHOME's flighting configs / dev options.
- **Save.**

> ⚠️ **The "At least one Flighting Config is required when configs are not inherited" error.** That validation (and the
> red, empty **Version** box on a manual Flighting Config row) appears only when you are **not** inheriting. The fix is to
> **Link to Parent** so configs are inherited from `PC_TAKEHOME` — you should **not** hand-add a Flighting Config row /
> type a Version. Inheriting is the whole point of choosing a parent SUG.

This writes the OS Targets SUG entry. Backed by `services.devapi` `DevApiGateway/Pages/PcSugDefinitions/`
(`PcSugDefinitionInfo.cs` → `InheritsFrom` / `InheritsConfigs`; `PcSugFlightingConfigInfo.cs` → per-SKU OS image versions).

> **Owner: you can self-serve this.** Jack (2026-06-22): *"you need to go to the PC SUG configuration page and set up the
> SUG."* So Melanie sets up the SUG definition directly on this page; Timi is still needed only for the dynamic-config
> quota (§2, if you lack edit access), confirming GPU capacity for the SKU, and `Services.Common.Ids` recognition.

---

## 4. Second PR (Partner Registry) — `SystemUpdateGroupWeights` (done)

> *"Second PR is mostly fine, just that I think you need to add the PC SUG to the SystemUpdateGroupWeights."*

Two related offering fields:
- **`SelectableSystemUpdateGroups`** — the SUGs a **client can request** (manual selection).
- **`SystemUpdateGroupWeights`** — `SUG → weight`; "servers in a SUG with a higher weight have a higher chance to be
  selected **during resource allocation**." This is what routes a **launched** session to a server by default.

A tester just clicks a link — they don't pick a SUG — so the default allocation needs `PC_PLAYTEST` in the **weights**.
`PlaytestProcessor` now sets `offering.SystemUpdateGroupWeights = { PC_PLAYTEST: 100 }` (only one SUG, so the weight is
relative — any positive value sends all allocation there) **in addition to** `SelectableSystemUpdateGroups`. Content
Targets' `GetSystemUpdateGroups()` already unions both, so install-mapping was fine; this fixes runtime allocation.
(Committed in the PTNR PR; tests 12/12.)

---

## 5. Open questions / next steps
**For Timi:**
1. **SKU** — Option A (NC64, matches code) or Option B (NC8, matches the existing non-prod fleet)? Is `STANDARD_NC64AS_T4_V3`
   actually provisioned in Int/Test, or should the code move to `STANDARD_NC8AS_T4_V3`?
2. **Test region** — Test runs in `WESTUS3` but the offering targets `WESTUS2`/`WestEurope`; how should Test be wired?
3. **Quota apply** — Timi applies the `PC_PLAYTEST` quota line, or grants access so it can be set here.
4. **SUG definition** — the SUG definition is in place; `PC_GA` is acceptable for Test/Int, so no parent change is needed.
5. **IncludePredictions** — does Int/Test need the `RESOLUTIONCONFIGURATION` `IncludePredictions` override for `PC_PLAYTEST`,
   or are non-prod predictions already on (existing PC SUGs have quotas without an obvious per-SUG override)?

**For Jack (CTIN PR‑C):**
6. **Resolution business logic for playtests** — PR‑C review: *"Resolution code needs some special business logic for playtests."*
   Book the walkthrough; the open code question is whether the resolver marks a freshly-ingested playtest version current
   immediately (`IsCurrent => AvailableFrom == null`) under the playtest's flights + sandbox. See
   [`./pc-install-readiness-polling-implementation.md`](./pc-install-readiness-polling-implementation.md) **B5** and
   [`../PRProgress/17-CTIN-15896502-pc-install-readiness-polling.md`](../PRProgress/17-CTIN-15896502-pc-install-readiness-polling.md).
