# Diagrams — Instantly Shareable Playtest

Visual companions to [`SPEC.md`](./SPEC.md). All diagrams are GitHub-flavored Mermaid (renders natively in ADO, GitHub, and most Markdown previewers).

Each diagram cites the SPEC section it visualizes so it stays auditable when the spec changes.

---

## 1. System Context — who talks to whom (SPEC §2, §3.1, §3.7, §6)

Shows the four services involved and the *direction* of each call. xPlaytest never speaks to anything inside xCloud directly — every cross-tenant hop goes through SAGE.

```mermaid
flowchart LR
    PC["Partner Center UI<br/>(creator)"]
    XPT["xPlaytest<br/>(MSFTGreen tenant)"]
    SAGE["SAGE<br/>(cross-tenant proxy)"]
    CI["services.contentingestion<br/>(xCloud)"]
    PR["services.partnerregistry<br/>(xCloud)"]
    SUCU["SUCU / install pipeline<br/>(xCloud)"]

    PC -->|Publish<br/>(Enable Cloud Streaming ✓)| XPT
    XPT -->|POST /playtest/ingestion<br/>(S2S bearer)| SAGE
    XPT -->|GET /playtest/ingestion/{jobId}<br/>poll, exp backoff| SAGE
    XPT -->|DELETE /playtest/ingestion/by-playtest/{id}<br/>on playtest delete| SAGE
    SAGE -->|/v3/workflows/playtestingestion| CI
    CI -->|BulkEditAsync<br/>(offering write + title attach<br/>in one ADO PR)| PR
    CI -->|PollFirstInstall<br/>(flight = lex-smallest DNA group)| SUCU

    classDef green fill:#dff2d8,stroke:#3a7d2c,color:#000
    classDef corp fill:#dde6f5,stroke:#2a4a7a,color:#000
    classDef edge fill:#fff6d8,stroke:#a07a00,color:#000
    class XPT green
    class CI,PR,SUCU corp
    class SAGE edge
```

**Tenant boundary:** xPlaytest (green) is in the MSFTGreen tenant; xCloud services (blue) are in Corp/PME. SAGE (yellow) is the only cross-tenant hop and is the auth gate (`AuthorizedClientAppIds` allow-list per route, SPEC §3.7 / Known Blockers §7).

---

## 2. End-to-End Happy Path — sequence (SPEC §2 phases 1–4)

The four phases the user sees from "click Publish" to "playtest is streamable."

```mermaid
sequenceDiagram
    autonumber
    actor Creator
    participant XPT as xPlaytest<br/>(XPackagePlaytestPublishWorkflow)
    participant SAGE
    participant CI as services.contentingestion<br/>(PlaytestTitleIngestionWorkflow)
    participant PR as services.partnerregistry
    participant SUCU as Install pipeline

    Creator->>XPT: Publish (Enable Cloud Streaming = true,<br/>PlaytestEndDate = required)
    Note over XPT: existing states:<br/>FetchingContentIds → StartingContentSubmissionJob<br/>→ PollingContentSubmissionJob → PlaytestProductCreation
    Note over XPT: NEW state: XCloudIngestionTrigger

    XPT->>XPT: Build StoreAsset<br/>(XboxTitleId from XProduct alternateIds)
    XPT->>SAGE: POST /playtest/ingestion<br/>(PlaytestIngestionJobParameters)
    SAGE->>CI: forward /v3/workflows/playtestingestion
    CI-->>SAGE: 202 Accepted { jobId, statusUrl }
    SAGE-->>XPT: 202 Accepted

    XPT->>XPT: persist XCloudIngestionJobId<br/>on PublishedPlaytestEntity
    Note over XPT: download-only path completes here<br/>(streaming is best-effort)

    par xCloud ingestion (async)
        CI->>CI: validate PlaytestIngestionJobParameters
        CI->>CI: AssetIngestionWorkflow<br/>(no BigCat lookup; uses StoreAsset)
        CI->>PR: BulkEditAsync<br/>(offering xpt-{shortId} + title attach,<br/>AllowedDnaGroups, ExpirationTime, RETAIL sandbox)
        PR-->>CI: PR merged (manual SFI approval)
        CI->>SUCU: PollFirstInstall<br/>(flight = lex-smallest DNA group GUID)
        SUCU-->>CI: install available
    and xPlaytest polling (exp backoff)
        loop until terminal or 60 min foreground
            XPT->>SAGE: GET /playtest/ingestion/{jobId}
            SAGE->>CI: forward
            CI-->>SAGE: { status: Running | Streamable | Failed | InstallNotFound }
            SAGE-->>XPT: status
        end
    end

    XPT->>XPT: PlaytestStatus = StreamingReady<br/>(new enum value)
    XPT-->>Creator: launch URL<br/>https://play.xbox.com/play/launch/{productId}?offeringId=xpt-{id}
```

**Note on parallelism:** the xCloud ingestion and xPlaytest polling run concurrently (the `par … and …` block). xCloud is not waiting for xPlaytest to poll — it's making progress independently and xPlaytest is just observing.

---

## 3. xPlaytest Publish State Machine — where the new state slots in (SPEC §2 phase 1)

Visualizes the existing state machine and the **single insertion point** for streaming. Everything before `PlaytestProductCreation` is unchanged.

```mermaid
stateDiagram-v2
    [*] --> FetchingContentIds
    FetchingContentIds --> StartingContentSubmissionJob
    StartingContentSubmissionJob --> PollingContentSubmissionJob
    PollingContentSubmissionJob --> PlaytestProductCreation

    state if_streaming <<choice>>
    PlaytestProductCreation --> if_streaming

    if_streaming --> XCloudIngestionTrigger : IsStreamingEnabled = true
    if_streaming --> SuccessCompletion : IsStreamingEnabled = false

    XCloudIngestionTrigger --> SuccessCompletion : 202 Accepted<br/>(jobId persisted, polling kicks off async)
    XCloudIngestionTrigger --> SuccessCompletion : SAGE 5xx<br/>(best-effort, download still succeeds)

    SuccessCompletion --> [*]

    note right of XCloudIngestionTrigger
        NEW state.
        Builds StoreAsset, calls
        POST /playtest/ingestion.
        Ingestion failure does NOT
        block the download playtest
        from publishing (SPEC §2).
    end note
```

---

## 4. Polling Backoff Timeline (SPEC §3.1)

What "poll until terminal" actually looks like over wall-clock time. The handoff at 60 min from foreground polling to the background reconciliation job is the key reliability mechanism — without it, slow ingestion ( >60 min) silently drops the offering.

```mermaid
sequenceDiagram
    participant W as Publish Workflow<br/>(foreground)
    participant SAGE
    participant R as Reconciliation Job<br/>(background singleton)

    Note over W: t = 0:  POST /playtest/ingestion → jobId
    W->>SAGE: GET (t = 0:30)
    SAGE-->>W: Running
    W->>SAGE: GET (t = 1:30)
    SAGE-->>W: Running
    W->>SAGE: GET (t = 3:30)
    SAGE-->>W: Running
    W->>SAGE: GET (t = 8:30)
    SAGE-->>W: Running
    Note over W: cap reached → every 5 min after this
    W->>SAGE: GET (t = 13:30 ... 58:30)
    SAGE-->>W: Running

    Note over W,R: t = 60 min — foreground deadline.<br/>jobId already persisted on<br/>PublishedPlaytestEntity.

    R->>SAGE: GET (t = 75 min, interval 15 min)
    SAGE-->>R: Running
    R->>SAGE: GET (t = 90 min)
    SAGE-->>R: Streamable
    R->>R: set PlaytestStatus = StreamingReady,<br/>surface launch URL

    Note over R: hard cap = 24 h.<br/>If still non-terminal, operator alert fires.
```

| Window | Source | Interval | Cap |
|---|---|---|---|
| 0 → 60 min | foreground publish workflow | 30s → 60s → 2m → 5m (cap) | 60 min wall clock |
| 60 min → 24 h | background reconciliation job | 15 min | 24 h, then alert |

---

## 5. StoreAsset Construction — where each field comes from (SPEC §5.2)

The dependency map for the StoreAsset the xPlaytest workflow has to build. The **red boxes are the P0 blockers** that don't have a source today.

```mermaid
flowchart LR
    subgraph xPlaytest_inputs ["xPlaytest already has"]
        PJP["PlaytestPublishJobParameters"]
        PR["PlaytestResponse"]
        PPE["PublishedPlaytestEntity"]
        PLS["PlaytestLifecycleState"]
    end

    subgraph XProduct_doc ["XProduct document (NEW fetch)"]
        XPALT["alternateIds[idType=XboxTitleId].value"]
        XPPFN["properties.packageFamilyName"]
    end

    subgraph StoreAsset ["StoreAsset (output)"]
        SE_PID["StoreEntry.ProductId"]
        SE_NAME["StoreEntry.Name"]
        SE_DESC["StoreEntry.Description"]
        SE_PUB["StoreEntry.PublisherId"]
        SE_FLAGS["StoreEntry.Flags = 'GAME' (const)"]
        SE_PRIV["StoreEntry.IsPrivateAudience = true (const)"]
        MKT["Markets = ['US'] (const v1)"]
        PLAT["Platform = 'WINDOWS.DESKTOP' (const v1)"]
        CID["ContentId"]
        XTID["XboxTitleId<br/>P0 BLOCKER"]
        PFN["PackageFamilyName<br/>P0 BLOCKER"]
        AUM["AumID<br/>v1: constant default<br/>v1.1: real plumb"]
    end

    PJP -- PlaytestGeneratedXProductBigId --> SE_PID
    PR -- Name --> SE_NAME
    PR -- Description --> SE_DESC
    PPE -- SellerId --> SE_PUB
    PLS -- PlaytestContentId<br/>(filtered + fallback to servicingContentId) --> CID
    PLS -- PackageFamilyName<br/>(already surfaced) --> PFN
    XPALT --> XTID
    XPPFN -. fallback when PLS missing .-> PFN

    classDef blocker fill:#fde2e2,stroke:#a01818,color:#000
    classDef const fill:#eee,stroke:#666,color:#000
    class XTID,PFN blocker
    class SE_FLAGS,SE_PRIV,MKT,PLAT const
```

> **PR2 in `Xbox.Xbet.Service` resolves the red `XboxTitleId` blocker.** Today `PlaytestProductDocumentBuilder.cs:53-70` hardcodes empty; the new `XboxTitleIdResolver` pulls from `alternateIds[idType=XboxTitleId]`. See SPEC §5.2 row "XboxTitleId" and Known Blockers §7.

---

## 6. Identifier Lattice — `OfferingId` vs `TitleId` vs `XboxTitleId` (SPEC §5.3)

Three values that all sound similar and are NOT interchangeable. This is the most common confusion when reading the spec.

```mermaid
flowchart TB
    PID["PlaytestId<br/>(stable, e.g. PartnerCenterProductId,<br/>see §9 Q1)"]
    PNAME["StoreEntry.Name<br/>(e.g. 'Example Game Playtest')"]
    BIG["PlaytestGeneratedXProductBigId<br/>(e.g. 9NXYZ12345PT)"]
    XPRODUCT["XProduct.alternateIds<br/>[idType=XboxTitleId]"]

    OID["OfferingId = xpt-{shortId(PlaytestId)}<br/>opaque ≤32 chars<br/>catalog/auth key"]
    TID["TitleId = alphanumOnly(Name) + BigId<br/>user-readable<br/>install/streaming key"]
    XTID["XboxTitleId (uint)<br/>Xbox Live game identity<br/>StoreAsset.XboxTitleId<br/>=> validator requires non-0"]

    PID --> OID
    PNAME --> TID
    BIG --> TID
    XPRODUCT --> XTID

    OID -.persisted on.-> ENT["PublishedPlaytestEntity.XCloudOfferingId"]
    TID -.persisted on.-> ENT2["PublishedPlaytestEntity.XCloudTitleId"]

    classDef k fill:#dde6f5,stroke:#2a4a7a,color:#000
    class OID,TID,XTID k
```

| Identifier | Owner | Derived from | Locked? | Purpose |
|---|---|---|---|---|
| `OfferingId` | xCloud derives, xPlaytest persists | `xpt-{shortId(PlaytestId)}` | Yes, for the lifetime of the playtest | Catalog/auth — the key SAGE + PartnerRegistry use |
| `TitleId` | xCloud derives, xPlaytest persists | `alphanumOnly(Name)+PlaytestGeneratedXProductBigId` | Yes once created — rename only updates display (§9 Q4) | User-facing install/streaming key |
| `XboxTitleId` | xPlaytest reads from XProduct, passes through | XProduct `alternateIds[idType=XboxTitleId]` | n/a — game-level identity that long pre-dates the playtest | StoreAsset validator requirement for games |

---

## 7. Delete Flow — tombstone, not hard delete (SPEC §6.2.1, §7, §8)

```mermaid
sequenceDiagram
    actor Creator
    participant XPT as xPlaytest delete workflow<br/>(PT6.d)
    participant SAGE
    participant CI as services.contentingestion
    participant PR as services.partnerregistry

    Creator->>XPT: Delete playtest
    XPT->>SAGE: DELETE /playtest/ingestion/by-playtest/{id}
    SAGE->>CI: forward
    CI->>PR: BulkEdit<br/>offering.PlayerAuthorizationOptions.AllowedDnaGroups = []
    PR-->>CI: PR merged (manual SFI approval)
    CI-->>SAGE: 200 { playtestId, offeringId, tombstoneTime }
    SAGE-->>XPT: 200
    Note over XPT,CI: Testers blocked at next<br/>GsToken refresh.<br/>DevApi portal hides tombstoned offerings.

    Note over CI: GC pass scheduled<br/>(default 7 days later)
    CI->>PR: hard delete offering + asset rows
    PR-->>CI: PR merged
```

**Why tombstone not hard delete:** the formal project description says "delete = fully cleaned up." We deliver the user-visible behavior (offering disappears, testers blocked) immediately. The actual hard-delete PR runs 7 days later. This is a **scoped deviation** that needs explicit Anthony/Brian sign-off — see SPEC §7 row "Delete model = tombstone."

---

## 8. PR / Workstream Ownership Map (SPEC §4, ADO/ado-tasks.md)

```mermaid
flowchart LR
    subgraph xPlaytest_Xbet ["Xbox.Xbet.Service (xPlaytest)"]
        PT1["PT1<br/>publish-side validations<br/>(streaming flag, end-date)"]
        PT2["PT2<br/>StoreAsset builder<br/>+ XboxTitleId resolver<br/>← current PR2"]
        PT3["PT3<br/>PlaytestIngestionJobParameters"]
        PT4["PT4<br/>XCloudIngestionTrigger state<br/>+ POST to SAGE"]
        PT5["PT5<br/>polling + reconciliation"]
        PT6["PT6<br/>delete propagation"]
    end

    subgraph xCloud_CI ["services.contentingestion (xCloud)"]
        XC1["XC1<br/>SAGE routes"]
        XC2["XC2<br/>S2S allow-list"]
        XC3["XC3<br/>PlaytestTitleIngestionWorkflow"]
        XC6["XC6<br/>install poll PC fork<br/>+ flight = lex-smallest DNA"]
    end

    subgraph xCloud_PR ["services.partnerregistry (xCloud)"]
        XC4a["XC4.a<br/>AllowedDnaGroups field<br/>← PR1 shipped"]
        XC4b["XC4.b<br/>BulkEditAsync + SPN allow-list<br/>← in progress"]
    end

    subgraph xCloud_AUTH ["xCloud auth path"]
        XC5["XC5<br/>GsToken DNA-group check"]
    end

    PT2 --> PT3 --> PT4 --> PT5
    PT4 -->|POST| XC1 --> XC3
    XC3 --> XC4a
    XC3 --> XC4b
    XC3 --> XC6
    XC4a --> XC5
    PT6 -->|DELETE| XC1
```

The dependency chain visualizes why the small in-flight PRs are sequenced: PT2 (resolver) unblocks PT3 (payload), PT3 unblocks PT4 (trigger), PT4 + XC1 close the cross-tenant loop, and so on.
