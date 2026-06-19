# 2026-06-18 as-built spec delta

Target: `C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\Instantly Shareable Playtest - Updated Implementation Spec (polished).docx`
Backup: `C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\cloud-playtest-implementation\Documentation\spec-updates\Instantly Shareable Playtest - Updated Implementation Spec (polished) BACKUP 2026-06-18.docx`
Save status: applied to AS-BUILT copy and verified; original target remains locked by Word (PID 1848) and was not modified.
AS-BUILT copy: `C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\Instantly Shareable Playtest - Updated Implementation Spec (polished) AS-BUILT 2026-06-18.docx`
Error / caveat: Original target remains locked by Word; edits were applied to the AS-BUILT copy instead.

## Edited in place in AS-BUILT copy
- **Paragraph 23** — Align executive summary with live 17-PR snapshot: 13 merged, 1 active, 3 draft.
  - Old: The backend is wired end-to-end today — publish resolves the Xbox Title ID, hands off cross-tenant through SAGE to content ingestion, and a private offering is created in Partner Registry with the audience allow-list. The remaining work is the user-facing surface (Partner Center toggle, Bayside launch path) and the status/launch-link loop, plus enabling Xbox console (the xCloud receiver is already console-ready). Streaming rides the broader xPlaytest rollout: allow-listed private preview now, seller-eligibility at GA.
  - New: As-built status is mixed: the core content-ingestion workflow, AllowedDnaGroups audience enforcement, Partner Registry playtest offering endpoint/configuration (endpoint, regions, id naming), XORc title-id source, and content-ingestion cross-tenant S2S gate are merged. The remaining active/draft backend work is the SAGE proxy route, the xPlaytest payload builder/status caller, and PC install-readiness polling, plus the user-facing Partner Center toggle and Bayside launch path. Streaming rides the broader xPlaytest rollout: allow-listed private preview now, seller-eligibility at GA.
- **Paragraph 24** — Avoid overstating the hard cross-team plumbing as fully done while draft PRs remain.
  - Old: Bottom line: the hard cross-team plumbing is done and proven; what is left is mostly UI and the completion/launch experience — well-scoped and low-risk.
  - New: Bottom line: the core design decisions are settled and the receiver/Partner Registry foundations are merged; the remaining work is well-scoped integration, UI, and completion/launch experience.
- **Paragraph 35** — Clarify stage status versus as-built PR reality.
  - Old: As-built: stages 1–4 are wired end-to-end (offering creation works). Stage 5 — the status poll, the StreamingReady transition, and surfacing the launch link — is designed but not yet built; today the publish schedules ingestion and stores the job id. See §8.
  - New: As-built: the core content-ingestion workflow and Partner Registry offering/title writes are merged, including the playtest endpoint, regions, offering-id convention, AllowedDnaGroups, authentication options, and cross-tenant gate. SAGE proxy routes, the xPlaytest ingestion payload builder/caller, PC install-readiness polling, the StreamingReady transition, and surfacing the launch link are still active/draft/planned; today publish work stores the job id but the status loop is not complete. See §8 and the addendum.
- **Paragraph 48** — Replace stale one-audience-per-DNA-group convention.
  - Old: 3.4 Audience model: one audience per DNA group
  - New: 3.4 Audience model: single ingestion audience, full offering auth set
- **Paragraph 49** — Match authoritative convention: single XusAudience for ingestion, full set for offering auth.
  - Old: Decision: the full AllowedDnaGroups set is carried through end-to-end. The ingestion workflow creates one SUCU audience per DNA group, and the same complete set is written onto the offering and used for the install poll; login checks the user against the full set.
  - New: Decision: the full AllowedDnaGroups set is carried through end-to-end for authorization, but asset ingestion uses a single XusAudience derived from AllowedDnaGroups.First(). The complete set is written onto the offering and enforced at login; only the ingestion/package path narrows to one representative audience.
- **Paragraph 50** — Remove obsolete SUCU fan-out claim.
  - Old: Correction: an earlier draft said the install pipeline used a single “lexicographically-smallest DNA group” as the effective flight. The code does not do that — every DNA group becomes its own audience/flight. All groups point to the same build version, so the fan-out is harmless.
  - New: Correction: an earlier draft said the install/ingestion pipeline created one SUCU audience per DNA group. The as-built convention is narrower: use AllowedDnaGroups.First() for the single ingestion XusAudience, while retaining every AllowedDnaGroup on the offering authorization allow-list.
- **Paragraph 59** — Reflect PC Orchestrator path and draft status.
  - Old: Adding the title to the offering is what triggers the install, so the workflow attaches first, then polls. PC readiness must be version-aware (keyed off the resolved install id + content hash for the latest version). For the MVP it is acceptable to skip the full readiness wait: the link is handed over with a “keep retrying until it works” contract rather than a guarantee it streams instantly.
  - New: Adding the title to the offering is what triggers the install, so the workflow attaches first, then polls. PC readiness must fork away from the Xbox allocator path and query PC Orchestrator with the resolved install id + content hash for the latest version; that version-aware PC poll is in draft PR 15896502. Xbox allocator-style readiness remains a separate console path.
- **Paragraph 65** — Add missing offering-config endpoint/regions/id reality.
  - Old: Endpoint. Bespoke route (not a generic CreateOfferingFromStoreData) so playtest defaults live server-side and the contract stays small.
  - New: Endpoint. Bespoke playtest ingestion routes via SAGE keep playtest defaults server-side and the contract small; the Partner Registry playtest offering-configuration endpoint, region handling, and offering-id naming are merged.
- **Paragraph 91** — Clarify status polling remains unfinished even though the contract exists.
  - Old: Polls workflow state. The status method exists on the client and controller, but nothing polls it yet (§8). Response 200 returns OperationStatus; 404 for an unknown job id.
  - New: Polls workflow state. The status method exists on the client and controller, but the xPlaytest polling loop is still in draft/planned work (§8). Response 200 returns OperationStatus; 404 for an unknown job id.
- **Table 2 row 1 col 1** — Update backend PR reality.
  - Old: ● Built — works end-to-end in code
  - New: ● Partly merged — CTIN workflow + Partner Registry offering/title pieces merged; SAGE routes and xPlaytest payload/caller still draft
- **Table 2 row 2 col 1** — Cross-tenant gating merged but send path not fully merged.
  - Old: ● Built (in review) — token/credential config being finalized
  - New: ● Mixed — CTIN CrossTenantS2S gate merged; SAGE proxy route and xPlaytest caller/token wiring still draft/finalizing
- **Table 2 row 6 col 1** — Keep 30-day decision with current code caveat.
  - Old: ● Decided — code at interim 7 days; wiring pending
  - New: ● Decided — 30-day cap; code still at interim 7-day clamp pending backend + UX update
- **Table 4 row 1 col 2** — XBET payload builder is draft.
  - Old: ● Built (in review) · AB#62492594 · PR 15834601
  - New: ● Draft · AB#62492594 · PR 15834601
- **Table 4 row 2 col 2** — XORc title-id field is merged but xbet consumption still draft.
  - Old: ● Built (in review) · AB#62492534 · PR 15834601, 15894506
  - New: ● Partly merged / partly draft · AB#62492534 · XORc PR 15894506 merged; xPlaytest consumption in PR 15834601 draft
- **Table 4 row 3 col 2** — xPlaytest audience/offering payload builder is draft.
  - Old: ● Built (in review) · AB#62492560 · PR 15834601
  - New: ● Draft · AB#62492560 · PR 15834601
- **Table 4 row 4 col 2** — XBET payload builder draft.
  - Old: ● Built (in review) · AB#62492606 · PR 15834601
  - New: ● Draft · AB#62492606 · PR 15834601
- **Table 4 row 5 col 2** — SAGE caller/routes draft.
  - Old: ● Built (in review) · AB#62492628 · PR 15834601
  - New: ● Draft · AB#62492628 · PR 15834601; SAGE route PR 15829639 also draft
- **Table 5 row 1 col 2** — SAGE routes still draft.
  - Old: ● Built (in review) · AB#62492655 · PR 15829639
  - New: ● Draft · AB#62492655 · PR 15829639
- **Table 5 row 2 col 2** — Cross-tenant S2S gating merged.
  - Old: ● Built (in review) · AB#62492665 · PR 15905881
  - New: ● Merged · AB#62492665 · PR 15905881
- **Table 5 row 3 col 2** — Core ingestion workflow merged; PC polling draft.
  - Old: ● Built · AB#62492680 · PR 15800964, 15876080; PC poll AB#62521491 · PR 15896502
  - New: ● Core merged; PC poll draft · AB#62492680 · PR 15800964 merged; PC poll AB#62521491 · PR 15896502 draft
- **Table 5 row 4 col 2** — Partner Registry/DevAPI pieces merged.
  - Old: ● Built · AB#62492689 · PR 15732852, 15773366, 15815668, 15821813, 15849944, 15860243, 15892276, 15739964
  - New: ● Merged · AB#62492689 · PRs 15732852, 15773366, 15815668, 15821813, 15849944, 15860243, 15892276, 15739964
- **Table 5 row 6 col 2** — PC polling still draft and PC Orchestrator based.
  - Old: ● In progress (PC built; Xbox poll/SKU config pending)
  - New: ● Draft / pending upstream — PC Orchestrator version-aware poll in PR 15896502; Xbox production SKU/filter config deferred
- **Table 6 row 3 col 4** — Correct audience-field notes.
  - Old: Full set written to the offering; one audience per group
  - New: Full set written to offering auth; AllowedDnaGroups.First() becomes the single ingestion XusAudience
- **Table 8 row 4 col 1** — Correct derived audience computation.
  - Old: One audience per DNA group (group + sandbox) — full set (§3.4)
  - New: Single XusAudience from AllowedDnaGroups.First() for ingestion; full AllowedDnaGroups set on offering authorization
- **Table 9 row 2 col 1** — Cross-tenant status reality.
  - Old: ● In progress — interim scheme in place; caller config being finalized; PME migration future
  - New: ● Mixed — CTIN gate merged; SAGE route + xPlaytest caller/token configuration still draft/finalizing
- **Table 9 row 4 col 1** — PC polling draft status.
  - Old: ● Built — depends on upstream PC install enablement (version-aware poll)
  - New: ● Draft — version-aware PC Orchestrator poll in PR 15896502; upstream install enablement still required
- **Table 9 row 8 col 1** — Confirm 30-day decision and stale code caveat.
  - Old: ● Decided — code currently clamps at an interim 7 days (§8)
  - New: ● Decided — 30-day cap; code currently clamps at an interim 7 days (§8)

## Added as addendum in AS-BUILT copy
- **End addendum** — Substantial reconciliation content is safer as an addendum than rewriting polished prose throughout.
  - Old: No as-built update addendum
  - New: Added 'As-built updates (2026-06-18)' with PR reality, 30-day decision, audience convention, endpoint/status conventions, and PC Orchestrator polling.

## Human-review / uncertainty list
- Confirm final wording for the Partner Center UI once the GPX branch lands; the spec now records the 30-day decision while noting current code still clamps/validates 7 days.
- Confirm whether the SAGE public route spelling should be documented as `playtesttitleingestion` or `playtestingestion`; source docs currently use both forms.
- Confirm final cross-tenant caller credential/token configuration once PR 15834601 and PR 15829639 leave draft.
- Confirm upstream PC install-on-attach/quota readiness with Timi before treating PC polling as production-complete.

