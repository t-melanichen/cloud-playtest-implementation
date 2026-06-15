# [PTNR] PR 15732852 — Add AllowedDnaGroups to PlayerAuthorizationOptions

- **Pull Request:** 15732852
- **Repo:** services.partnerregistry (Xbox.Streaming)
- **Source branch:** `t-melanichen/add-allowed-dna-groups` → `main`
- **Status:** Merged
- **Opened:** 2026-06-01  |  **Closed:** 2026-06-01
- **Link:** https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.partnerregistry/pullrequest/15732852

## Summary
Adds an `AllowedDnaGroups` property (`ICollection<string>`) to the `PlayerAuthorizationOptions`
contract so offerings can authorize users by DNA-group membership: a user with at least one matching
group is granted access. DNA group IDs are GUIDs serialized in the hyphenated "D" format; matching is
case-insensitive on the hex letters but format-sensitive (hyphenless/braced/parenthesized forms will
not match). This is the foundational contract change for DNA-group gating of Instantly Shareable
Playtest streaming offerings.
