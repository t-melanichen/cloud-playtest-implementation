# Blocker: SAGE → CTIN region routing (playtest ingestion 500s + poll 404s)

**Status:** ✅ **Pinned — merged (2026-07-09).** Xbet
[PR 16102792](https://microsoft.visualstudio.com/Xbox/_git/Xbox.Xbet.Service/pullrequest/16102792) (merged 2026-07-09)
pins the worker to `americas.gssv-sage-prod.xboxlive.com`. Timi confirmed Americas is the target core;
eastus2/northcentralus sub-clusters rotate and must not be pinned. Pending prod deploy (paused until Monday). Durable
fix tracked by [ADO Task 63013710](https://microsoft.visualstudio.com/Xbox/_workitems/edit/63013710).
**Owners:** Melanie Chen (worker pin) · Timi Bolaji / GameStreaming-CTIN (SAGE routing + CTIN topology).

## What happened (root cause)
The xPackage worker POSTs playtest title-ingestion to SAGE (`POST /v3/playtest/playtesttitleingestion` on the global
`gssv-sage-prod.xboxlive.com`). SAGE forwards the `playtest`/`ctin` route to **same-cluster**
`http://contentingestion-svc.contentingestion`. Two failures result because the global host is a Traffic Manager that
resolves **per request**:

1. **Ingestion 500 (Europe/APAC).** When the TM routes the POST to a Europe/APAC SAGE cluster, that cluster has **no
   CTIN**, so SAGE fails to resolve `contentingestion-svc.contentingestion` (`Name or service not known`) → HTTP 500.
   *(07-06 log: northeurope → `UnexpectedFailure` 500.)*
2. **Status-poll 404 (never-created job after failed submit).** Submit (POST) and poll (GET `/{jobId}`) use the
   **same client/Host**, and `americas.gssv-sage-prod` is a **nested Traffic Manager** over `eastus2` (20.41.13.162) +
   `northcentralus` (20.241.33.111). Each request resolves independently, but CTIN jobs are **not** cluster-local: the
   ingestion job store is a single shared Cosmos account per environment, so a poll can find a job created by any
   Americas sub-cluster. The prior eastus2 `GET .../{jobId}` → NotFound 702 ms was most likely for a submit that had
   500'd in Europe/APAC and never created the job.

## Evidence (from logs — verbatim)
- **Ingest 500 — Europe.** Diagnostic `93c7…` CSV, all 3 rows `2026-07-06T22:49:00Z`,
  `Tenant=xcld-prod-europe-control-neu-aks`, `ControlPlane=northeurope`, cV `lk4L9yNLQkO2kgA%2B.1.57`:
  - `POST - http://gssv-sage-prod.xboxlive.com/v3/playtest/playtesttitleingestion - 500 [44ms]`
  - `POST http://contentingestion-svc.contentingestion/v3/workflows/playtesttitleingestion : UnexpectedFailure (43 ms)`
  - `System.Net.Http.HttpRequestException: Name or service not known (contentingestion-svc.contentingestion:80)`
- **Poll 404 — eastus2.** Prod SAGE Geneva log row `2026-07-07T00:38:02Z`,
  `Tenant=xcld-prod-americas-control-eus2-aks`, `ControlPlane=eastus2`, `data_RequestStatus=CallerError`:
  - `GET http://contentingestion-svc.contentingestion/v3/workflows/playtesttitleingestion/5232FA04-59C9-44ED-90C6-BE2FEACF3A86 : NotFound (702 ms)`
  - **Verified:** CTIN was reached in eastus2 (real HTTP 404 after 702 ms, not a DNS `Name or service not known`).
    **Inference:** because CTIN uses a single shared Cosmos job store per environment, this was most likely a poll for a
    job whose submit had 500'd in Europe/APAC and was never created.
- **Co-location proof — commandproxy.** Diagnostic `725f…` CSV, `2026-07-04`: the session service resolved in **both**
  Americas sub-clusters with `data_Succeeded=True` and **0** `Name or service not known` across 255 rows:
  - `POST http://commandproxy-svc.commandproxy/v1/commandrequest/forward : NotFound (34 ms)` — `ControlPlane=eastus2`, `succeeded=True`
  - `POST http://commandproxy-svc.commandproxy/v1/commandrequest/forward : NotFound (5 ms)` — `ControlPlane=northcentralus`, `succeeded=True`
  - The 404 here is app-level ("no session"), not a routing failure — the same-cluster proxy works when the backend is
    co-located, which CTIN isn't.

## Interim fix (PR 16102792)
Pin `XCloudPlaytestIngestionServiceClient.Host` to `americas.gssv-sage-prod.xboxlive.com` — the Americas SAGE core. Per
Timi, Americas is the only core with Content ingestion; `eastus2` and `northcentralus` are rotating sub-clusters and must
not be pinned directly. Both submit + poll stay on the Americas core, so SAGE can reach CTIN and polls can read the
shared job store → fixes the 500 and prevents false 404s from sub-cluster rotation. Trade-off: caller-side core pin until
the SAGE route can reach CTIN from every core.

---

## Where the routing goes (traced in the repos)

The exact hop chain, with the code that drives each step:

```
[1] xPackage worker (Xbet)
      POST https://gssv-sage-prod.xboxlive.com/v3/playtest/playtesttitleingestion
      client: XCloudPlaytestIngestionServiceClient.cs — submit + poll BOTH use SendForOperationStatusAsync (same Host)
        │  gssv-sage-prod = global Azure Traffic Manager → resolves to a regional SAGE per request
        ▼
[2] SAGE ProxyController.ProxyAsync  (services.serviceapigateway/Controllers/ProxyController.cs:82)
      route match: ServiceRouteName="playtest" in appsettings.xcloud.json
        backendUri = service.ServiceBaseUri  (ProxyController.cs:186)
                   = "http://contentingestion-svc.contentingestion"   ← SAME-CLUSTER K8s DNS name
      path rewrite: /v3/playtest/playtesttitleingestion → /v3/workflows/playtesttitleingestion
        ▼
[3] SAGE → CTIN  (same cluster only)
      POST http://contentingestion-svc.contentingestion/v3/workflows/playtesttitleingestion
      CTIN K8s Service = headless: clusterIP: None, type: ClusterIP (commonservice chart service.yaml)
      → resolvable ONLY inside a cluster where CTIN ingestion is deployed (Americas)
        ▼
[4] CTIN WorkflowsProcessor.ScheduleWorkflowAsync → job persisted in the environment's shared Ingestion Cosmos WorkflowsDB
      (ContentCatalog.Ingestion.Core: WorkflowsProcessor.cs:40, IngestionCosmosConfig.WorkflowsDB; one AccountResourceId
       via IngestionCosmosConfig.Account, with ApplicationRegion = AzureRegionName)
```

**The single decisive line:** `ProxyController.cs:186` uses `service.ServiceBaseUri`, and for the playtest route that's
the same-cluster `http://contentingestion-svc.contentingestion`. Every SAGE region loads the **same**
`appsettings.xcloud.json` (+ env overlay) — there is **no region dimension** in the backend-services config — so every
region tries its own local CTIN. Only Americas has one.

**Design confirms the asymmetry:** `services.contentingestion/DESIGN.md:54` — *"Content Resolution … is an always on
active regional service … deployed in each region with a read-only replica of the Ingestion database."* i.e.
**Resolution is regional; Ingestion is not.** Infra owns one CosmosDB account in the CTIN envr layer; regional Content
Resolution reads read-only replicas from that account. The ingestion worker even hard-pins `Region = IsProd() ? WestUs2 :
WestEurope` (`TitleIngestionWorker.cs:220`).

## Proof from the two logs: routing WORKED vs. FAILED
The two diagnostic zips are the same request pattern through **two different backend services** — and the contrast
isolates the cause to CTIN co-location, not the proxy mechanism.

| | **725f (07-04)** — POST worked | **93c7 (07-06)** — POST failed |
|---|---|---|
| Backend service | `commandproxy-svc.commandproxy` (session control) | `contentingestion-svc.contentingestion` (CTIN ingestion) |
| SAGE→backend DNS resolve | ✅ resolved (0 `Name or service not known`) | ❌ `Name or service not known (…:80)` |
| `data_Succeeded` on the hop | **True** (SAGE forwarded fine) | False (`UnexpectedFailure`) |
| Clusters observed | eastus2 **and** northcentralus (both resolved) | europe / northeurope |
| Backend answer | 404 `NotFound` = *app-level* "no session" | never reached → SAGE 500 |

**Reading it:** in 725f the POST *routing* succeeded (SAGE resolved + forwarded to a co-located backend in **both**
Americas sub-clusters; the 404 is the app saying "no such session" — a different layer). In 93c7 the *routing itself*
broke (europe SAGE couldn't resolve CTIN → 500). Same SAGE same-cluster proxy pattern for both — the only difference is
**footprint**: `commandproxy` is deployed in every cluster, CTIN ingestion is not. Bonus: 725f proves the Americas
sub-clusters have commandproxy too, so the Americas-core ingestion pin doesn't strand the session layer.

## How to fix it to always work (options, grounded)
Because CTIN ingestion physically runs in **one** region (Americas), "always works" means "always reach that one CTIN".
Every option below is a variant of that (except the last, which makes CTIN truly multi-region).

| # | Fix | Where the change is | Removes caller pin? | Owner | Effort |
|---|---|---|---|---|---|
| **A (done)** | Worker `Host` → `americas.gssv-sage-prod` (Americas core) | Xbet appsettings (PR 16102792) | No (it *is* the pin) | You | 1 line |
| **B** | Point the SAGE **playtest route `ServiceBaseUri`** at a **stable cross-region CTIN endpoint** instead of same-cluster `contentingestion-svc.contentingestion` | `appsettings.xcloud.json` (SAGE) + CTIN must expose that endpoint | ✅ (worker keeps global host) | SAGE + CTIN | Med |
| **C** | **SAGE-to-SAGE**: non-Americas SAGE forwards the `playtest` route to the Americas core / `americas.gssv-sage-prod` (which then does the same-cluster hop) | `appsettings.xcloud.json` (SAGE) | ✅ | SAGE | Med (double hop, auth) |
| **D** | Deploy CTIN **ingestion in every region** sharing the existing environment job store so any cluster can serve submit+poll | CTIN infra + data | ✅ (true regional) | CTIN team | High |

**Precedent for B:** CTIN is *already* exposed via a gateway path — the ingestion clients use
`https://americas.gssv-dev-prod.xboxlive.com/api/contentingestion/` (Development) and `gssv-dev-int/test/api/contentingestion`
(Int/Test) (`ContentCatalog.Ingestion.Client/appsettings*.json`, `ContentCatalog.Ingestion.Service/appsettings.{Int,Test}.json`).
So a **stable Americas CTIN URL already exists** — a prod equivalent of that (or an internal private-DNS endpoint) is what
SAGE's playtest route would target in Option B. Note it's still **Americas-pinned** (because CTIN lives there), so B makes
routing *region-independent from the caller* but does not make CTIN multi-region — only D does that.

**Both submit + poll are covered** by A/B/C because they use the same client `Host` (verified:
`XCloudPlaytestIngestionServiceClient` routes both POST and GET through `SendForOperationStatusAsync`), so pinning/redirecting
the route makes the submit reliably create the job. Because the job store is already shared per environment, the poll can
then find that created job from any Americas sub-cluster.

**Recommendation:** ship **A** now (done, interim). Pursue **B** as the durable no-pin fix with SAGE + CTIN (stable Americas
CTIN endpoint the playtest route targets; tracked by [ADO Task 63013710](https://microsoft.visualstudio.com/Xbox/_workitems/edit/63013710)). Treat **D** as the ideal long-term (real regional CTIN using the shared job store) — biggest lift.

---

## ✉️ Message to Timi (copy/paste)

> Hey Timi — quick one on playtest streaming **ingestion** routing.
>
> **What's happening:** when the xPackage worker POSTs a playtest title-ingestion job to SAGE
> (`/v3/playtest/playtesttitleingestion` on `gssv-sage-prod`), it's flaky:
> - **Sometimes 500s** — SAGE forwards to same-cluster `contentingestion-svc.contentingestion`, but when the Traffic
>   Manager routes the POST to a **Europe/APAC** SAGE cluster (no CTIN there), it fails with `Name or service not known`.
> - **When it lands in Americas**, the follow-up **status GET** sometimes **404s** — `americas.gssv-sage-prod` is a
>   nested TM over **eastus2 + northcentralus**, so the submit and the poll (same client) can hit different sub-clusters,
>   and the job looks **cluster-local** (created in one CTIN, not visible from the other).
>
> **Interim fix I put up (PR 16102792):** pinned the worker's ingestion `Host` to
> `eastus2.americas.gssv-sage-prod.xboxlive.com` — the one cluster I confirmed reaches CTIN (~702 ms) — so submit + poll
> always hit the same CTIN. That should clear both the 500 and the 404.
>
> **Questions:**
> 1. Is pinning to **eastus2** OK as an interim, or is there a better/more-stable host I should target?
> 2. Which Americas cluster(s) is CTIN **ingestion** actually deployed in — **eastus2 only**, or also **northcentralus**?
>    (I could only confirm eastus2.)
> 3. Is the ingestion **job store cluster-local by design** (hence the cross-cluster poll 404), or should it be shared?
> 4. Longer term — any plan for CTIN ingestion to be **cross-region reachable** (a stable endpoint SAGE can route to from
>    any region), so we can drop the pin? Otherwise Europe/APAC publishes keep failing unless pinned.
>
> Thanks!

(Answered after this was sent: pin to the Americas core, not eastus2; the ingestion job store is a single shared Cosmos
account per environment, not cluster-local.)

---

## References
- Xbet PR 16102792 (worker pin to americas).
- Evidence: `../testing/logs-2026-07-06-e2e/` (northeurope 500 ingestion; 07-04 session commandproxy 404s).
- Deep dive: `../testing/e2e-2026-07-06-pc-playtest-streaming.md` (What didn't work #3 + Next steps #4).
- Related: `../Explanations/prod-streaming-ingestion-debug.md` (the earlier 0-SAGE-rows S2S/auth root cause — distinct).
