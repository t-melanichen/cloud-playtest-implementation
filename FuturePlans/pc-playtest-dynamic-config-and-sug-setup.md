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

**Option A — keep the code's NC64 SKU (needs NC64 capacity in Int):** add a new SKU block.
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

> ⚠️ **Region mismatch in Test.** Test's fleet is in **`WESTUS3`**, but the offering targets `WESTUS2` / `WestEurope`. So
> a `PC_PLAYTEST` quota in `WESTUS3` won't be reached by the offering, and one in `WESTUS2` has no Test capacity behind it.
> **Recommend validating in Int first** and resolving Test region/capacity with Timi before adding it here.

---

## 3. SUG definition — the PC SUG Definitions page

Page: <https://americas.gssv-dev-prod.xboxlive.com/PcSugDefinitions> (sign in).

A SUG definition assigns the **OS image versions** (the Windows/OS build the GPU servers run) per SKU. Rather than
hand-pick image versions, **create `PC_PLAYTEST` to inherit from a stable release SUG — `PC_TAKEHOME`** (Timi: "currently
our most solid"). On the page:

- **New SUG** → `Id = PC_PLAYTEST`
- `InheritsFrom = PC_TAKEHOME`
- inherit configs + dev options (so it picks up PC_TAKEHOME's known-good OS images / flighting configs automatically)

This writes the OS Targets SUG entry. Backed by `services.devapi` `DevApiGateway/Pages/PcSugDefinitions/`
(`PcSugDefinitionInfo.cs` → `InheritsFrom` / `InheritsConfigs`; `PcSugFlightingConfigInfo.cs` → per-SKU OS image versions).

> Owner: likely **Timi** (or whoever has edit access to that page / the dynamic config) — it controls real GPU capacity.

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

## 5. Open questions for Timi
1. **SKU** — Option A (NC64, matches code) or Option B (NC8, matches the existing non-prod fleet)? Is `STANDARD_NC64AS_T4_V3`
   actually provisioned in Int/Test, or should the code move to `STANDARD_NC8AS_T4_V3`?
2. **Test region** — Test runs in `WESTUS3` but the offering targets `WESTUS2`/`WestEurope`; how should Test be wired?
3. **Quota apply** — Timi applies the `PC_PLAYTEST` quota line, or grants access so it can be set here.
4. **SUG definition** — confirm `PC_PLAYTEST` inheriting from `PC_TAKEHOME` is the intended setup.
5. **IncludePredictions** — does Int/Test need the `RESOLUTIONCONFIGURATION` `IncludePredictions` override for `PC_PLAYTEST`,
   or are non-prod predictions already on (existing PC SUGs have quotas without an obvious per-SUG override)?
