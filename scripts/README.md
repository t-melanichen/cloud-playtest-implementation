# Scripts

## `sync-pr-progress.ps1`

Read-only helper for the `pr-progress-sync` agent. It queries Azure DevOps PRs
created by `t-melanichen@microsoft.com` across `Xbox`, `Xbox.Streaming`, and
`Xbox.Services`, compares them with `PRProgress/README.md`, and reports tracked,
missing meaningful, junk, and status-drift PRs.

Run from the repo root:

```powershell
pwsh -File scripts\sync-pr-progress.ps1
```

Prerequisites: Azure CLI with the Azure DevOps extension, plus either `az login`
or `AZURE_DEVOPS_EXT_PAT` set to a PAT with PR read access. The script does not
edit repo files; it writes a CSV copy of the report to `$env:TEMP`.
