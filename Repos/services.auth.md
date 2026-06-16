# Repo: services.auth
**Role:** auth service — enforces `AllowedDnaGroups` + Xbox gamertag claim in the offering login (`/v2/login/user[/delegated]`)

## Changes made
### PR 15738761 — XC5.a: Enforce AllowedDnaGroups in user login authorization — branch `t-melanichen/xc5a-enforce-allowed-dna-groups` (Status: Merged)
- PRProgress quotes: "Pull Request: 15738761", "Status: Merged", and title "[AUTH] PR 15738761 — XC5.a: Enforce AllowedDnaGroups in user login authorization".
- Base branch: `origin/main`; merge-base: `6c7d20295d602cc6a275e6acf585279537c90892`.
- Net diff from merge-base: 3 files changed, 185 insertions(+), 2 deletions(-).
- Implements authorization enforcement of offering `AllowedDnaGroups` during user login. `UserLoginProcessor` now authorizes when the user's `GsToken.DnaGroups` contains a non-empty allowed group, using case-insensitive string comparison while preserving GUID format sensitivity.
- Records successful DNA allow-list authorization as `AuthorizedBy = "DnaGroupAllowList"` and logs the user's DNA groups for the authorization event.
- Updates `Microsoft.GameStreaming.Partners` from `1.0.2604.2001` to `1.0.2606.101` so the auth service can consume the `AllowedDnaGroups` contract.
- Adds/extends unit coverage for successful DNA-group authorization, case-insensitive matches, format-sensitive denial, unmatched groups, empty user groups, and empty/whitespace allow-list entries that must not authorize empty token groups.

**Key files**
- `src\Product\AuthService\Processors\UserLoginProcessor.cs` — runtime `AllowedDnaGroups` authorization check.
- `src\Tests\Unit\AuthService.UnitTests\UserLoginProcessorTests.cs` — authorization and denial test cases.
- `src\Product\AuthService\AuthService.csproj` — partner contract package bump.

**Commits**
- `df49342` XC5.a: Enforce AllowedDnaGroups in user login authorization
- `d1bf3ab` XC5.a: Bump Microsoft.GameStreaming.Partners to 1.0.2606.101 for AllowedDnaGroups
- `8d1922c` XC5.a: Bump Microsoft.GameStreaming.Services.Common stack + Identity for Partners 1.0.2606.101
- `54de324` Pin System.Net.Http 4.3.4 to remediate CVE-2018-8292
- `7db9985` Pin System.Net.Http 4.3.4 in RoutingService to remediate CVE-2018-8292
- `8454b9f` Guard DNA-group allow-list match against empty/whitespace entries
- `537f6d0` logging
- `9fd4e7c` Fix
- `a247fb3` Merge remote-tracking branch `origin/main` into `t-melanichen/xc5a-enforce-allowed-dna-groups`
- `0594239` Remove duplicate System.Net.Http PackageReference in RoutingService
- `ba1281d` Restore RoutingService.csproj to match main (revert unrelated reorder)

## Planned / remaining changes
- None tracked for `services.auth` itself after PR 15738761 merged.
- Cross-repo auth follow-up: cross-tenant S2S call tasks now consolidated in [`FuturePlans/s2s-cross-tenant-call.md`](../FuturePlans/s2s-cross-tenant-call.md).
- Related client validation: `FuturePlans\bayside-playxbox-playtest-modifications.md` says Bayside must thread `offeringId` into offering-scoped login and confirm the `/v2/login/user[/delegated]` path honors the auth service's DNA-group + Xbox-gamertag eligibility gate.

## References
- Git: `git -C "C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\services.auth" --no-pager log --oneline origin/main..t-melanichen/xc5a-enforce-allowed-dna-groups`
- Git: `git -C "C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\services.auth" --no-pager diff --stat 6c7d20295d602cc6a275e6acf585279537c90892..t-melanichen/xc5a-enforce-allowed-dna-groups`
- `PRProgress\02-AUTH-15738761-enforce-allowed-dna-groups-login.md`
- [`FuturePlans/s2s-cross-tenant-call.md`](../FuturePlans/s2s-cross-tenant-call.md)
- `FuturePlans\bayside-playxbox-playtest-modifications.md`
