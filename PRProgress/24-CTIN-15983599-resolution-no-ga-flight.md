# [CTIN] PR 15983599 — Don't scope playtest resolution package search to the GA flight

- **Pull Request:** 15983599
- **Repo:** services.contentingestion (Xbox.Streaming)
- **Source branch:** `t-melanichen/resolution-playtest-no-ga-flight` → `main`
- **Status:** Active
- **Opened:** 2026-06-24
- **Link:** https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.contentingestion/pullrequest/15983599

## Summary
A playtest package is only ever ingested into its dedicated playtest flight, never the GA flight, but
`QueryResolutionDataAsync` scoped the asset-version search to the package's mapped flights
(`mappedFlightIds.Contains(av.FlightId)`, which always folds in the platform GA flight). For a playtest
title that scoping can drop the playtest's own ingested versions whenever its flight set changes (e.g. its
DNA groups). This PR stops flight-scoping the asset-version search for playtest resolution while leaving
non-playtest resolution byte-for-byte unchanged. Split out from the CTIN install-readiness polling work
(PR 15896502, #17) into its own PR, and a prerequisite for removing the GA flight from that PR's
resolution query.

- Detects a playtest from the Title id prefix (`xpt`) via a local `bool isPlaytest` inside
  `QueryResolutionDataAsync` — no new query/context/contract field.
- `CosmosContentCatalog` and `InMemoryContentCatalog` `QueryResolutionDataAsync`: change only the
  asset-version filter to `isPlaytest || mappedFlightIds.Contains(av.FlightId)`, kept in lockstep.
- Flight-mapping and `InstallId` generation are left untouched, so a playtest's `InstallId` stays stable
  even if its DNA-group / flight set changes.

## Context
- Prerequisite for **PR 15896502** (#17 — PC install-readiness polling) dropping the GA flight from its
  resolution query.
- Playtest detection by Title-id prefix is an interim signal; longer term it should be an explicit Asset
  property set at ingestion (swappable without touching callers).

## Validation
- `ContentCatalog.Core.UnitTests` pass, including 3 new `PlaytestFlightScopingTests` run against both
  catalog implementations (6 tests: InMemory + Cosmos): non-playtest scopes to mapped (input + GA) flights,
  playtest surfaces every ingested version (including one in an otherwise-unmapped flight), and playtest
  detection does not change the resolved InstallId.
