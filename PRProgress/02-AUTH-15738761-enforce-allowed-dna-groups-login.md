# [AUTH] PR 15738761 — XC5.a: Enforce AllowedDnaGroups in user login authorization

- **Pull Request:** 15738761
- **Repo:** services.auth (Xbox.Streaming)
- **Source branch:** `t-melanichen/xc5a-enforce-allowed-dna-groups` → `main`
- **Status:** Merged
- **Opened:** 2026-06-01  |  **Closed:** 2026-06-03
- **Link:** https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.auth/pullrequest/15738761

## Summary
Implements authorization enforcement of `AllowedDnaGroups` at user login. `UserLoginProcessor.cs`
now validates the user's DNA groups against the offering's `AllowedDnaGroups` with case-insensitive
(format-sensitive) GUID comparison, restricting access to members of the allowed groups. Adds
comprehensive `UserLoginProcessorTests.cs` coverage: successful authorization, case-insensitive
matching, format sensitivity, and forbidden scenarios (unmatched groups, empty groups). This is the
runtime enforcement counterpart to the `AllowedDnaGroups` contract added in PR 15732852.
