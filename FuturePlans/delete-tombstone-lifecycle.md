# Future plan: Delete / tombstone lifecycle

**Why it matters:** When a playtest is deleted (or expires), testers must lose access and the offering should disappear from listings. A true synchronous hard delete isn't achievable in v1 because Partner Registry writes are manual-approval ADO PRs (SFI).

## Current understanding
- v1 model: **tombstone + 7-day GC**.
  - Set `offering.PlayerAuthorizationOptions.AllowedDnaGroups = []` immediately → denies everyone, so testers lose access right away and the offering drops out of the DevApi listing.
  - Schedule a follow-up **GC pass** to fully delete the offering and its asset entries after a grace period (default 7 days).
  - Idempotent: deleting an already-tombstoned offering returns 200.
- The `DELETE /v3/playtest/playtestingestion/by-playtest/{playtestId}` route is **documented in the contract but not yet implemented** (receiver returns 404 today); the SAGE gateway route for it also isn't provisioned yet.

## Open questions / dependencies
- **Needs explicit xCloud sign-off** — tombstone deviates from a literal "hard delete".
- Provision the DELETE SAGE route so xPlaytest's PT6 delete workflow can be written against the final shape.
- Confirm GC grace period (7 days) and ownership of the GC pass.

## Owners
Melanie Chen · xCloud reviewers (sign-off).

## References
`SPEC.md` (delete model), `OpenAPI/playtest-ingestion.yaml` (DELETE by-playtest route), `ARCHITECTURE.md` §6.2.
