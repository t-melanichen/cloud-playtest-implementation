# Playtest streaming ingestion — the SAGE->CTIN region bug + fixes (A & B)

*Shareable summary. TL;DR: playtest ingestion is flaky because SAGE proxies to a **same-cluster** CTIN that only exists
in **Americas**. Option A (pin the caller to the Americas core — done, interim, verified) and Option B (point SAGE at a
stable CTIN endpoint — durable) both fix it.*

## The bug

When a creator publishes a cloud playtest, the xPackage worker calls SAGE to start title ingestion:

```
POST https://gssv-sage-prod.xboxlive.com/v3/playtest/playtesttitleingestion
```

`gssv-sage-prod` is a **global Traffic Manager** that routes each request to the *nearest* regional SAGE (Americas,
Europe, or APAC). Whichever SAGE receives it forwards the route to a **same-cluster** address:

```
POST http://contentingestion-svc.contentingestion/v3/workflows/playtesttitleingestion
```

That name only resolves **inside a cluster where CTIN ingestion runs** — and CTIN ingestion is **centralized in Americas
only** (by design: Content *Resolution* is regional, Content *Ingestion* is not). Result: two intermittent failures.

**Symptom 1 — 500 on ingest (Europe/APAC).** When the Traffic Manager routes the POST to a Europe/APAC SAGE, that
cluster has no CTIN, so SAGE can't resolve `contentingestion-svc.contentingestion` -> `Name or service not known` ->
**HTTP 500**. *(Confirmed in logs: a request landed on northeurope and 500'd at the CTIN hop.)*

**Symptom 2 — 404 on status poll (never-created job after failed submit).** Within Americas,
`americas.gssv-sage-prod` is a *nested* Traffic Manager over **eastus2 + northcentralus**. That is useful DNS context,
but CTIN jobs are **not** cluster-local: the ingestion job store is a single shared Cosmos account per environment, so a
poll can find a job created by any Americas sub-cluster. The observed eastus2 `NotFound` was most likely a poll for a
job whose submit had 500'd in Europe/APAC and therefore never created the job.

**Why it's intermittent:** nothing is wrong per request — it's just **which region the Traffic Manager picks**. Americas
-> works; Europe/APAC -> submit 500, and a later poll for that never-created job can return 404.

**Proof it's co-location, not the proxy itself:** in a separate log the *session* service (`commandproxy`) went through
the exact same SAGE proxy pattern and **succeeded** in both eastus2 and northcentralus — because commandproxy is deployed
in every cluster. The only difference is footprint: commandproxy is everywhere; CTIN ingestion is Americas-only.

**The one knob:** SAGE chooses the backend from a single config value (`ProxyController` -> `service.ServiceBaseUri`),
which for the playtest route is the same-cluster `http://contentingestion-svc.contentingestion`, identical in every
region (no region dimension). Auth is **pass-through** (SAGE forwards the caller's token; CTIN authorizes the xPackage
app id), so moving where this route points does **not** require solving auth. Every fix is "send this route to the one
CTIN that exists."

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
  - The 404 here is app-level ("no session"), not a routing failure.

---

## Option A — Pin the worker to the Americas core  *(done, interim — PR 16102792)*

Change the worker's ingestion host from the global `gssv-sage-prod` to the Americas SAGE core
`americas.gssv-sage-prod.xboxlive.com`.

- Submit **and** poll now stay on the Americas core -> SAGE can reach CTIN -> CTIN uses the shared environment job
  store.
- **Fixes both** symptoms: no Europe/APAC routing (no 500), and a created job is visible to polls on any Americas
  sub-cluster (no false 404 from sub-cluster rotation).
- **Verified:** the worker's config `Host` feeds the HTTP client's `BaseAddress`, and *both* the submit and the poll use
  that one client — so pinning it moves both. Prod reads this value (no Production overlay; Staging/Dev keep the test
  host). Per the CTIN owner, Americas is the only core with Content ingestion; the eastus2/northcentralus sub-clusters
  rotate and must not be pinned directly.
- **Trade-offs:** caller-side pin to the Americas core until the SAGE route can reach CTIN from every core.
- **Scope:** only the XPackageWorkflow playtest ingestion host needs this prod `americas` pin; other Xbet
  `gssv-sage-prod` callers that use regional routes stay on the global host, and Staging/Dev stay on `gssv-sage-test`.
- **Owner:** us (Xbet). **Effort:** one line. **Use as:** the immediate unblock to test end-to-end.

## Option B — Point the SAGE route at a stable CTIN endpoint  *(durable, recommended)*

Instead of pinning the caller, fix it at SAGE: change the playtest route's `ServiceBaseUri` from the same-cluster name to
a **stable, cross-region-reachable CTIN endpoint** (an internal endpoint — private DNS / internal load balancer / Private
Link — that resolves from any SAGE cluster and lands on the one Americas CTIN).

- Then **any** SAGE region (Europe, APAC, Americas) forwards the route to the **same** CTIN.
- The worker keeps calling the **global** `gssv-sage-prod` — **no caller pin**.
- **Fixes both** symptoms: Europe SAGE can now reach CTIN (no 500), and all requests converge on one CTIN so the poll
  always finds the job (no 404).
- **Precedent:** CTIN is *already* reachable via a gateway URL its own clients use
  (`americas.gssv-dev-prod.xboxlive.com/api/contentingestion`) — Option B just needs the prod/internal equivalent that
  SAGE's route targets.
- **Dependency:** CTIN publishes that endpoint (their infra); the SAGE change is then ~1 line.
- **Owner:** SAGE + CTIN. **Effort:** medium. **Note:** still funnels to the single Americas CTIN — it makes *routing*
  region-independent, not CTIN multi-region (the job store is already shared per environment; multi-region ingestion
  would be a larger CTIN project).

---

## Recommendation
- **Now:** ship **Option A** (interim pin) so playtest streaming can be tested end-to-end. It's verified and low-risk.
- **Durable:** pursue **Option B** with the SAGE + CTIN teams — a stable CTIN endpoint the playtest route targets — so we
  can drop the pin and it works from any region (tracked by ADO Task 63013710:
  https://microsoft.visualstudio.com/Xbox/_workitems/edit/63013710).

*Questions or corrections welcome — happy to walk through the logs.*
