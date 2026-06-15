# [PTNR-DATA] PR 15751527 — Updated OfferingV2.json (DNATEST allowed DNA group)

- **Pull Request:** 15751527
- **Repo:** services.data.partnerregistry (Xbox.Streaming)
- **Source branch:** `update-dnagroup` → `master`
- **Status:** Merged
- **Opened:** 2026-06-02  |  **Closed:** 2026-06-02
- **Link:** https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.data.partnerregistry/pullrequest/15751527

## Summary
Configuration/data update that exercises the new DNA-group gating end to end. Changes the `DNATEST`
offering in the TEST environment from allowing all groups to a single allowed group: `OfferingV2.json`
sets `AllowedDnaGroups` from `null` to `["4611686019004512103"]`, restricting offering access to that
specific DNA group for validation of the Instantly Shareable Playtest auth path.
