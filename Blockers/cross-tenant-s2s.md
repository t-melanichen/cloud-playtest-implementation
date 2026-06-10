# Blocker: Cross-tenant S2S (MSFTGreen → xCloud)

**Status:** Deferred out of summer scope (per `SPEC.md` v3 §7) — demo runs in-tenant
**Owners:** GSS platform team (long-term PME) · Melanie Chen (route wiring)

## Problem
The Playtest Service runs in the **MSFTGreen** tenant. xCloud's SAGE gateway does not accept calls originating from MSFTGreen out of the box, so the cross-tenant `POST /v3/playtest/playtestingestion` handoff can't authenticate without additional auth setup.

## Current direction
- **Short term:** ride the in-flight PR adding **Green→Corp** cross-tenant auth — the outdated spec cites **PR #15715445**. *Verify the actual PR id and direction* (the cited title direction looked inverted relative to the need) before locking anything.
- **Long term:** xCloud migrates to **PME**; Green→Corp is not the end state. The PME story is owned by the GSS platform team.
- Per SPEC v3 §7 this item is **deferred out of summer scope**, so the foundational demo may run in-tenant rather than truly cross-tenant.

## Next actions
1. Confirm the correct cross-tenant PR id + direction.
2. When unblocked: add the Playtest Service SPN to the SAGE route `AuthorizedClientAppIds` and set the correct auth-scheme flag (the SAGE playtest routes currently set `AuthorizedClientAppIds` but no auth scheme — peers use `UsePmeAuth: true`).
3. Acquire a token for the xCloud audience via the standard MSAL flow on the xPlaytest side.

## References
- `SPEC.md` §7 Known Blockers (deferred), §6.1 cross-tenant.
- `ARCHITECTURE.md` §3.2 / §6.1.
- Outdated spec §7 (PR #15715445).
