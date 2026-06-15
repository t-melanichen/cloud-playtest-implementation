# PR Progress — Instantly Shareable Playtest

Tracker for every pull request @t-melanichen has started or completed on the Instantly Shareable
Playtest project (xPlaytest × xCloud streaming). One file per PR, all titled with the same format:

`# [<AREA>] PR <id> — <PR title>`

Each file records: Pull Request id, Repo (project), source → target branch, Status, open/close dates,
a direct link, and a Summary. Files are numbered in chronological order of creation.

| # | PR | Area | Repo | Status | Title |
|---|----|------|------|--------|-------|
| 01 | 15732852 | PTNR | services.partnerregistry | Merged | Add AllowedDnaGroups to PlayerAuthorizationOptions |
| 02 | 15738761 | AUTH | services.auth | Merged | XC5.a: Enforce AllowedDnaGroups in user login authorization |
| 03 | 15739964 | DEVAPI | services.devapi | Merged | Add Allowed DNA Groups field to Offering edit page |
| 04 | 15751527 | PTNR-DATA | services.data.partnerregistry | Merged | Updated OfferingV2.json (DNATEST allowed DNA group) |
| 05 | 15800964 | CING | services.contentingestion | Active | Playtest Title Ingestion Workflow |
| 06 | 15829639 | SAGE | services.serviceapigateway | Draft | Register Playtest ingestion proxy routes for services.contentingestion |
| 07 | 15834601 | XBET | Xbox.Xbet.Service | Draft | Playtest Ingestion Payload Builder |
| 08 | 15849944 | PTNR | services.partnerregistry | Merged | Remove GetPackageSourceId from Playtest contract |
| 09 | 15860243 | PTNR | services.partnerregistry | Merged | Refactor playtest title ID |
| 10 | 15876080 | DEVAPI | services.devapi | Active | Testing workflow ingestion (Playtest Title Ingestion UI/client) |

**Status legend:** Merged = completed/merged · Active = open and in review · Draft = open draft.

**Area legend:** PTNR = services.partnerregistry · PTNR-DATA = services.data.partnerregistry ·
AUTH = services.auth · DEVAPI = services.devapi · CING = services.contentingestion ·
SAGE = services.serviceapigateway · XBET = Xbox.Xbet.Service.
