# Blocker: AumID / ApplicationId for PC builds

**Status:** Resolved for v1 (constant default); v1.1 follow-up tracked
**Owners:** Melanie Chen (xPlaytest) · Timi Bolaji (confirmed telemetry-only)

## Problem
The xCloud `StoreAsset` validator rejects a null **`AumID`** for PC games. `AumID` is `{PackageFamilyName}!{ApplicationId}`, but the real `ApplicationId` is **not currently propagated** into the xPlaytest publish path (it would come from the AppX manifest), so we have no real value to send.

## Current direction
- **v1:** ship a **constant default** `AumID`. Timi confirmed it is **telemetry-only server-side** for the streaming path, so a placeholder is acceptable and won't affect functionality.
- **v1.1:** plumb the real `ApplicationId` from the AppX manifest and build the true `{PackageFamilyName}!{ApplicationId}`.

## Next actions
1. Define and document the constant default `AumID` used in v1.
2. Open a v1.1 work item to source the real `ApplicationId` from the AppX manifest and remove the constant.

## References
- `SPEC.md` §5 StoreAsset field map (`AumID`), §7/§8.
- Outdated spec §7 ("AumID for PC").
