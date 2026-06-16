# [PTNR] PR 15892276 — Set Xbox AuthenticationOptions on playtest offerings

- **Pull Request:** 15892276
- **Repo:** services.partnerregistry (Xbox.Streaming)
- **Source branch:** `t-melanichen/playtest-offering-authentication-type` → `main`
- **Status:** Merged
- **Opened:** 2026-06-15  |  **Closed:** 2026-06-15
- **Link:** https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.partnerregistry/pullrequest/15892276

## Summary
Fixes playtest offering login, which was failing in TEST with `InvalidAuthenticationScheme: Unsupported
authentication scheme` (auth service `UserLoginProcessor.cs` threw on a null scheme) followed by a wrapped
`OfferingAccessDeniedException` 403 on `POST /v2/login/user/delegated`. `PlaytestProcessor` built the
`OfferingV2` with `AuthorizationOptions.AllowedDnaGroups` but never set `AuthenticationOptions`, so the
offering had no authentication scheme. This PR adds:

```csharp
AuthenticationOptions = new PlayerAuthenticationOptions
{
    AuthenticationType = PlayerAuthenticationType.Xbox,
    UserIdClaimType = XboxGamerTagClaimType, // http://schemas.microsoft.com/xbox/2011/07/claims/user/gamertag
},
```

`AuthenticationType = Xbox` is required for two reasons: (1) it is the only scheme the auth service's
`AuthenticateUserAsync` switch accepts for this flow (otherwise it throws `InvalidAuthSchemeException`), and
(2) DNA groups are only populated on the Xbox login path (`GetUserDnaGroupsAsync(puid)`), which is what the
DNA-group authorization (PR 02 / `AllowedDnaGroups`) depends on. `UserIdClaimType` is set to the gamertag
claim; the URI exactly matches `AuthClaimTypes.Gamertag` in `Microsoft.XboxLive.Claims`. DNA-group
authorization keys off the PUID (not the UserId claim), so the gamertag choice does not affect DNA gating.

## Notes / follow-ups
- DNA-group authorization is the second gate: the values in the offering's `AllowedDnaGroups` must match the
  exact string format the AppFlighting DNA source returns by PUID (the comparison is a case-insensitive string
  match). Confirm the configured group ID format matches, otherwise login still returns a genuine
  `OfferingAccessDenied`.
- Gamertag claim must be present on the delegated playtest xtoken, or the resolved `UserId` is null. Normal
  user xtokens include it; leaving `UserIdClaimType` null (default PUID) would be the lower-risk choice if
  gamertag-as-UserId is not required.
