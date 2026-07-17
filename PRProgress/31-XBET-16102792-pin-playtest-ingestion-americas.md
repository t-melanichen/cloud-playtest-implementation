# [XBET] PR 16102792 — Pin playtest ingestion to Americas SAGE

- **Pull Request:** 16102792
- **Repo:** Xbox.Xbet.Service (Xbox)
- **Source branch:** `t-melanichen/pin-playtest-ingestion-to-americas` → `main`
- **Status:** Merged (merging 2026-07-09; merge succeeded — verify completion)
- **Opened:** 2026-07-07
- **Merge commit:** (staged `d5919b38fba`; confirm final merge commit on completion)
- **Link:** https://microsoft.visualstudio.com/Xbox/_git/Xbox.Xbet.Service/pullrequest/16102792

## Summary
Pins the XPackageWorkflow playtest streaming-ingestion host from the global `gssv-sage-prod.xboxlive.com` to
**`americas.gssv-sage-prod.xboxlive.com`**. CTIN (content ingestion) is only reachable from the **Americas** core;
the global host let submit POSTs land on Europe/APAC SAGE, which 500'd (CTIN unresolvable there) and left status
polls 404ing on a job that was never created. See
[`../Blockers/sage-ctin-region-routing.md`](../Blockers/sage-ctin-region-routing.md).

- `XPackageWorkflow.appsettings.json`: Host → `americas.gssv-sage-prod.xboxlive.com` (1 line).
- TODO comment above the Host: hard-coded Americas is temporary; move to non-hardcoded region routing once CTIN
  ingestion is reachable from all cores — tracked in [ADO Task 63013710](https://microsoft.visualstudio.com/Xbox/_workitems/edit/63013710).

## Notes
- Timi confirmed: always use **Americas** SAGE — do **not** pin `eastus2`; the eastus2/northcentralus sub-clusters
  rotate. Cross-cluster is safe because the CTIN ingestion job store is a single shared Cosmos account per env
  (submit + poll hit the same store regardless of which Americas cluster they land on).
- Durable fix (CTIN reachable from all cores) tracked by ADO Task 63013710.
