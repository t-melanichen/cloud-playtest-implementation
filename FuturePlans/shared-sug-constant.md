# Future plan: Extract PC_PLAYTEST SUG to a shared constant

**Why it matters:** The `"PC_PLAYTEST"` System Update Group string is currently hardcoded independently in several
components. The producer (the offering tag) and the consumer (the readiness poll) must match exactly, so a typo or a
future rename in any one place silently breaks the flow with no compile-time check.

## Where it's duplicated today
- **PTNR** — `PlaytestSettings.cs`: `PCSystemUpdateGroup = "PC_PLAYTEST"` (sets the SUG on the offering).
- **CTIN** — `IngestionWorkflowSettings.cs`: `PlaytestPcReadinessQuery.SystemUpdateGroup = (Id)"PC_PLAYTEST"` (the poll filters on it).
- **services.data.partnerregistry** — the `PC_PLAYTEST` SUG definition (Test + Int).
- **content-targets** — the dynamic-config server quota keyed on `PC_PLAYTEST`.

## Plan (Brian's suggestion, PR 15949594)
1. Add `PC_PLAYTEST` as a named `SystemUpdateGroup` constant in the shared `Microsoft.GameStreaming.Services.Common.Ids`
   package, alongside the existing `SystemUpdateGroup.GA` (which is already consumed this way in CTIN).
2. Publish a new package version.
3. Migrate PTNR and CTIN to reference the shared constant instead of the raw string.

## Caveat
Touches a shared NuGet package + republish + two consumer repos, so it's a follow-up rather than part of the offering-SUG PR.

## ADO tracking
**AB#62907255** — "[Playtest] Extract PC_PLAYTEST SUG to shared Services.Common.Ids constant" (Proposed), under the
Instant Playtest scenario `62490517`.

## Owners
Melanie Chen · Brian Bowman · Timi Bolaji.
