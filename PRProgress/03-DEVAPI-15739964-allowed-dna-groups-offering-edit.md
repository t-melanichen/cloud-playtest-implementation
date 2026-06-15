# [DEVAPI] PR 15739964 — Add Allowed DNA Groups field to Offering edit page

- **Pull Request:** 15739964
- **Repo:** services.devapi (Xbox.Streaming)
- **Source branch:** `t-melanichen/devapi-add-allowed-dna-groups-ui` → `main`
- **Status:** Merged
- **Opened:** 2026-06-01  |  **Closed:** 2026-06-03
- **Link:** https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.devapi/pullrequest/15739964

## Summary
Adds UI support for configuring Allowed DNA Groups on the DevApi Offering edit page so admins can
specify which DNA-group IDs may access an offering. `Offering.razor` adds an "Allowed DNA Groups"
text-area field with a hint describing the GUID format and case-insensitive matching;
`Offering.razor.cs` adds an `allowedDnaGroupsText` field, parses the comma-separated input into an
array in `SyncFormFieldsToOfferingInfo()`, and syncs `AuthorizationOptions.AllowedDnaGroups` back into
the form in `SyncOfferingInfoToFormFields()`. Verified in test (DEVAPI in test).
