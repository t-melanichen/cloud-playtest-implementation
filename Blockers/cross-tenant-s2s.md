# Blocker: Cross-tenant S2S (MSFTGreen → xCloud)

**Status:** Consolidated into a dedicated deliverable
**Owners:** Melanie Chen (route wiring & caller) · Anthony Keller / Brian Bowman (credential decision) · GSS platform team (long-term PME)

## Current blocker
The cross-tenant xPackage (MSFTGreen) → SAGE → services.contentingestion (Corp) call still needs the xPackage caller client, Green-tenant token acquisition, caller credential/app-registration confirmation, and CI/CICD validation.

Cross-tenant S2S call tasks now consolidated in [`FuturePlans/s2s-cross-tenant-call.md`](../FuturePlans/s2s-cross-tenant-call.md).

## References
- `SPEC.md` §7 Known Blockers, §6.1 cross-tenant.
- `ARCHITECTURE.md` §3.2 / §6.1.
- [`FuturePlans/s2s-cross-tenant-call.md`](../FuturePlans/s2s-cross-tenant-call.md).
