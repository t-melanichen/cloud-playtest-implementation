# UI implementation steps — DevApi Reader portal (internal admin)

**Repo (frontend):** `services.devapi` → `DevApiGateway` (Blazor/Razor pages, e.g.
`src/Product/DevApiGateway/Pages/...`). Internal operator/reader portal for offerings.
**Scope:** the DevApi UI pieces from `Context/InternProjectDocument.pdf` not yet in a PR, with
frontend + backend (per service) steps. Effort: 🟢 easy · 🟡 medium · 🔴 hard.

**Already in a PR / done (reference):**
- "Offering is visible and manageable in the DevApi Reader portal" (P0): offerings already render in
  DevApi; the **Allowed DNA Groups** field on the Offering edit page → PR #15739964 (merged).
- Playtest **ingestion testing** UI/client (trigger + poll ingestion) → PR #15876080.

Service legend: **DevApi** = `services.devapi` · **PTNR** = `services.partnerregistry` ·
**CAS/GSSV** = Content Access / Game Streaming Services.

---

## #10 — Browse / filter "playtest offerings" separately  ·  P2 (stretch)  ·  🟡

**Goal:** "There is some way in the DevApi Reader Portal to easily browse 'playtest offerings'
separately from our existing offerings and filter by studio / seller / title etc."

**Status:** not started.

### Frontend (`services.devapi` → `DevApiGateway/Pages`)
1. Add a **Playtest Offerings** view (or a filter/toggle on the existing offerings list page) that
   shows only playtest offerings.
2. Identify playtest offerings by the id convention **`xpt{PlaytestProductId}`** (prefix match) or a
   dedicated offering attribute (preferred — see backend).
3. Add filter controls: **studio / seller / title** (text + dropdown), wired to the offerings query.
4. Surface playtest-relevant columns (seller, title id `{OfferingId}-{neutralTitleId}`, DNA groups,
   expiration). Reuse the existing offerings table components.

### Backend (per service)
- **DevApi backend** (`services.devapi`): extend the offerings query/controller to accept a
  **playtest filter** (by `xpt` prefix and/or by seller/title) and return the filtered set.
- **PTNR / CAS/GSSV**: offerings must be **queryable/filterable** by a playtest marker. Cleanest is a
  first-class offering attribute (e.g., `IsPlaytest` / a tag) rather than relying on the `xpt` id
  prefix; if added, DevApi filters on it.

### Dependencies
- A reliable way to mark/identify playtest offerings at the offering store level (id convention works
  today; an explicit attribute is more robust).

### Acceptance
An operator opens DevApi, switches to the Playtest Offerings view, filters by a seller/title, and sees
only that seller's playtest offerings with their DNA groups + expiration.

---

## Sequencing (DevApi)
1. **#10** is a standalone P2 stretch — do it after the P0/P1 creator + player pieces land. Start with
   the `xpt`-prefix filter (no backend change), then upgrade to an explicit `IsPlaytest` attribute if
   the offering store adds one.

## References
- `Context/InternProjectDocument.pdf` (P0 "manageable in the DevApi Reader portal"; P2 browse/filter).
- `Repos/services.devapi.md`, `PRProgress/03-DEVAPI-15739964-allowed-dna-groups-offering-edit.md`,
  `PRProgress/10-DEVAPI-15876080-testing-workflow-ingestion.md`.
- Companion plans: `FuturePlans/ui-steps-partnercenter.md`, `FuturePlans/ui-steps-bayside.md`.
