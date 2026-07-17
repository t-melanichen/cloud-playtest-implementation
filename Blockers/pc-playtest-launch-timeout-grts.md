# Blocker: PC playtest cloud launch times out (`LaunchByContentIdV1` — GRTS build)

**Status:** 🔴 **ROOT CAUSE CONFIRMED 2026-07-16 (auto-filed Bug 63132145, Nate): PROVISION fails because the in-VM pre-launch license acquisition fails — `XboxLicenseManager` returns `0x87E10BC6` ("not retrying") with `callerId: "noIdentity"` → game never launches → `LaunchByContentIdV1` times out after 90 s (`0x80131505`/COR_E_TIMEOUT).** The GRTS `gstracegamingonly.005.etl` is attached to the bug and shows this directly. It's a **title-licensing/entitlement failure, not server infra** — the license request goes out with **no identity/token** (open-licensing gap), so licensing refuses. Candidate sub-causes: playtest sandbox/account not entitled for XSTH, and/or a **race** (WAM MSA account cached only ~1 s before the license call). This is the concrete confirmation of the **open-licensing** root cause. **Earlier (07-15 sync) framing — V7-vs-V10:** the cloud-server licensing request hits **V7** (DCAT/BigCat) instead of **V10** (XProduct/SUCU), so playtest content is never open-licensed/decrypted; V7 fallback likely tied to GRTS build (V10 flag on-by-default only in 2608; this repro ran on **2607.09**, image `1.2607.1010`). Supersedes the GRTS deprovision-bug (63080510) theory. See the **Bug 63132145** and **2026-07-15 sync** sections below.

## 🎯 The three problems to fix (definitive breakdown, 2026-07-16)

Playtest PC cloud streaming needs **all three** addressed — they span GRTS (install + provisioning) *and* the Licensing service:

1. **Kolari VM isn't hitting the licensing V10 endpoint at INSTALL-time.**
   - `IsPlaytestLicensed` registry key is **`false`** at install-time.
   - `ServicingContentId` registry key **isn't set by GRTS** at install-time.
   *(→ GRTS doesn't recognize it as a playtest, so it doesn't take the V10 path.)*

2. **Kolari VM isn't hitting the licensing V10 endpoint at PROVISIONING-time.**
   - The playtest-related registry keys **aren't carried over** to the provisioning-time VM (Anthony's ephemeral-VM/VHD finding — registry lives in the VM OS, not on the content VHD that's moved over).

3. **The V10 Licensing endpoint for playtest products doesn't support open licensing.**
   - So even when V10 *is* reached, the Kolari VM **can't decrypt** the installed content (no open license issued for playtests).

**Owners:** #1 & #2 = GRTS/server side (Nate/Anthony — set `IsPlaytestLicensed`/`ServicingContentId` at install, re-establish the keys at provisioning via `Package::Register`/`Unlock`); #3 = Licensing service (Anthony — add open-licensing support on the V10 playtest path). All three are required; fixing only one won't unblock streaming.

### Anthony's live registry experiment (07-16) — isolates problem #3

Anthony manually corrected the license-proxy registry keys to simulate the #1/#2 fix, then triggered an unlock. **Only `HKLM` matters — that's what the license proxy reads.** Findings + values:
- Before: `ProductId` present but **empty**, `VersionId` **correct**, `IsPlaytestLicensed` **wrong (false)**, `ServicingContentId` **missing**. The empty `ProductId` is an artifact of installing with a **URL source instead of a ProductId** (Timi confirmed a **non-playtest** install-by-ProductId populates `ProductId`).
- **Install-by-ProductId fails** with **`0x80070490: Element not found`** on `Package::QueryHeaders` (playtests aren't queryable in the standard catalog → URL-source is the only working install path → hence the empty ProductId key). **Install-by-URL "succeeds"** — the licensing error doesn't surface as an install failure.
- Anthony set: **`IsPlaytestLicensed = 1`**, **`ProductId = 2SDT4X91KRPC`**, **`ServicingContentId = b2c0497d-7dce-485e-b728-f74e42047f9b`** (left `VersionId`). Confirmed **`HKLM\Software\Microsoft\GamingServices\EnablePlaytestPackageLicensing = 1`** (the value lives directly under `…\GamingServices`).
- **Result (first read): unlock reached licensing but failed with `LM_E_SATISFACTION_CONTENTIDNOTINCATALOG`.** ⚠️ **CORRECTED by Timi (07-16):** the request actually went to the **V7.0 API**, not V10 — because **the unlock operation itself OVERWRITES/clobbers the registry keys** (resets `IsPlaytestLicensed`→false, `ProductId`→empty — **everything except `ServicingContentId`**) *before* making the licensing call. So it routed to **V7**, whose catalog (DCAT/BigCat) doesn't contain the playtest → `CONTENTIDNOTINCATALOG`. **This is a V7 error, NOT the V10 open-licensing gap (#3) — #3 hasn't actually been reached yet** because the keys get clobbered before any V10 request is made.
- **A registry key determines V7-vs-V10 routing** — Timi and Brian both confirmed this reading the code. Whichever key it is (likely `IsPlaytestLicensed`), the unlock resets it, so licensing always falls to V7.
- **Open question (Brian, end of thread): the registry is getting clobbered / set incorrectly once we run unlock.** That's the current leading hypothesis and refines **problem #1**: it's not just that GRTS fails to set the keys at install — **the unlock operation actively resets them to non-playtest values**, forcing V7.
- **Net (corrected):** the manual key edit did **not** survive the unlock, so V10 was never actually exercised. The chain now: install/unlock write the wrong registry keys → licensing routes to **V7** → V7 catalog lacks the playtest → `CONTENTIDNOTINCATALOG`. The fix must make GRTS **write and preserve** the playtest keys (`IsPlaytestLicensed=1`, `ProductId`, `ServicingContentId`) through install **and** unlock so the request routes to **V10**; only then can **#3 (does V10 support open licensing for playtests?)** actually be tested.
- **Log-share status:** after deleting `vmsetup.log` (MS Defender false-positive — "key in logs" heuristic, no real key), Ranjit shared `PcServerLogs 1.zip` / `2.zip` — but these are **L1 host logs only + L2 install activity** (no session ran on the current L2); the **live L2 session GRTS logs** still require connecting to the L2 explicitly (or the auto-filed bug 63132145, which already has them).

### GRTS install path + the store-lookup/access root cause (07-16, Anthony/Brian/Timi)

- **How the server installs (Anthony):** always **install-by-URL** (CRD path as source) — build a `PackageRequest` via **`PackageRequest::CreateForSource()`** → submit to **`PackageQueue::SubmitRequestAsync`**. **The Request needs a StoreId to be marked as a playtest**, but install-by-URL passes a **raw URL, not a StoreId** → the package is **never marked playtest** → licensing routes to **V7**. (Confirms Jon Caruana's earlier "raw URL instead of StoreId" hypothesis.)
- **Why install-by-ProductId fails (`0x80070490: Element not found`):** the server queries the package **header** (to get buildId for telemetry) and that **store lookup fails**. Timi's (unverified) code guess: a failed store lookup in **`PackageSourceResolver.cpp`** (os.2020, branch `official/xb_flt_2608ge`, ~L384-388). `InstallMsixvcWithProductId` (Brian) failed at the same header-query step.
- **🔑 Deeper root cause (Timi):** the **same error occurs for ANY non-publicly-visible product**, not just playtests — so it's a **store-lookup that fails when the caller's user context can't see the product**. **The code path that retrieves `ServicingContentId` *also* does a store lookup**, so even reaching it won't help: the install runs as a **local install user / `noIdentity`** that **doesn't have access to the private playtest product** → store lookup fails → can't mark as playtest, can't retrieve `ServicingContentId` → routes V7. **This reframes #1/#2 as fundamentally an identity/access problem** — the install (and provisioning) context lacks access to the private playtest product in the store, so it can't obtain the StoreId/ServicingContentId needed to route to V10. Fix direction: give the install/provisioning context access to the private playtest product (or supply the playtest StoreId/ServicingContentId without a product-access-gated store lookup). GRTS internals now owned by **Ranjit/Nate/Jon** (Brian deferred).


**Update — 2026-07-15 (later, GRTS-expert thread — Jon Caruana / Ranjit):** servers are actually on **`2610ge_flt` GRTS** (not ~2606 — corrects the sync guess), and Jon confirms a flag ON-by-default in 2608 **stays on in 2610** (changes are additive), so **"V10 flag not enabled" is unlikely.** **New leading theory (Jon):** GRTS writes a **registry recording at install** that tells it which licensing endpoint to hit, and that recording is **triggered by the playtest domain in the StoreId** — but an xCloud install passes a **raw URL instead of a StoreId**, so the recording is never made → GRTS falls back to V7. See the **GRTS-expert thread** subsection below.

A partial GRTS fix did land in `PC_TAKEHOME` (2026-07-13), which `PC_PLAYTEST` inherits automatically (no SUG change needed) — **but the retest above shows it did not fix the provisioning timeout, and two known caveats still apply:**

1. **The linked bug is about *deprovisioning*, not *provisioning*.** Bug [63080510](https://dev.azure.com/microsoft/Xbox/_workitems/edit/63080510) is a **deprovision** timeout (`WaitForConnectedStorageToBeIdle`) — non-fatal, save preserved. Timi flagged that **the failure we actually hit is on *provisioning***, so 63080510 may not be our root cause. The `LaunchByContentIdV1` timeout is still under investigation; **GRTS team meets Thursday.**
2. **The PC_TAKEHOME server is still on Friday's build**, and — more importantly — **the Xbet contentId change is merged but NOT yet deployed to prod** (see below), so **installs are still failing.** Timi is manually patching the DB record with the contentId again to test.

This is the next-stage issue after the install/provision `ERROR_NOT_FOUND` (see [`pc-playtest-msixvc-install-error-not-found.md`](./pc-playtest-msixvc-install-error-not-found.md)).

**⚠️ Deploy gap (verified 2026-07-14):** the Xbet contentId fix (PR 16130422) **merged 2026-07-09** (commit `d81af6a3`), but the last *completed* `XPackageWorkflow-K8S` deploy was **2026-07-06** — so no deployed build contains the fix. A new deploy (`20260713.1`, queued 07-13 20:47) is **in progress but still at the build stage**; all prod rings (SEA/WUS2/WEU/EUS) are **pending**. Until it reaches prod, playtest installs use the old (servicing-id) behavior and fail → Timi hand-patches the DB as a workaround. **Merged ≠ deployed.**

**Deprovision bug (per Nate, 2026-07-13) — related but likely NOT our provisioning root cause:** [63080510](https://dev.azure.com/microsoft/Xbox/_workitems/edit/63080510) — `[PCServer] StreamingChild - Deprovision non-fatal: WaitForConnectedStorageToBeIdle timed out 60s (ConnectedStorageActive)`, area `Xbox\Platform\Streaming\Server\PC`, State Resolved (dup of 62681432). Deprovision waits on Connected Storage (the save layer) to go idle; still active → wait times out — **non-fatal, save preserved.** Per Timi this is deprovision-side; our launch failure is provisioning-side, so the true fix is still TBD at the Thursday GRTS discussion.

**Owners:** Nate's server team (GRTS / PC server launch — owns the fix) · Melanie Chen (SUG config / playtest side + deploying the Xbet contentId change) · Timi Bolaji (xCloud; manual DB patch workaround).

## Update — 2026-07-15 (thread): root cause = playtest content isn't decrypted (no open license)

**The provisioning timeout is because the playtest MSIXVC is still encrypted after install.** xCloud PC streaming uses **open licensing** to decrypt content during install; here it never happens, so provisioning stalls (decryption is attempted/never completes) → the 90 s launch timeout.

**Mechanism (from the thread — Timi, Anthony, Nate, David, Brian):**
- Nate: after install, `EnumerateDisks` → `EnumerateContent` shows **`IsContentDecrypted` not set** on the playtest build (it should be). Kusto: `xcloudprodreadonly.westus` DB `xCloudServicesDebugEvents`, cV `PX48St7anUCoP7LJSEslTg.4.7`, ~2026-07-14T18:51Z.
- Timi: for open licensing, xCloud passes **GRTS a special token** in the licensing-request HTTP headers; the Licensing service validates it and enables the **`IsGameStreamingProviderWithOpenLicensing`** device claim. The exe stays encrypted on disk and is only **decrypted in memory at launch with the user's token** — so a decrypted XVC leaking is still unusable (removes the security objection to enabling this for private playtest builds).
- **Anthony (licensing codev): the Licensing service does NOT create an open license for playtests** — v10 docs show a **separate path**. `LicenseRequestBase.IsRequestFromCloudServer` is the key server-side signal most logic keys off.
- **What makes the token "special": it's an AAD token generated with a *clientId pre-registered/allowlisted* with the Licensing service** — PC open licensing only runs for allowlisted clientIds. GRTS calls the **v10** API with a slightly different contract (Anthony suspects the playtest path may be hitting **v7**). **Prod open-licensing clientId (Timi): `2ba05d2f-afa8-4e75-af45-4287d4be925f`.** This special token is **distinct from GRTS's regular authorization headers.**
- **Anthony's read after seeing the `IsRequestFromCloudServer` signal:** *"if there's a parameter like that, then we can make this work"* — i.e. it may be a **smaller** fix keyed off that flag, **not** the bigger change he first feared (adding a new **availability to the xproduct document**, which "would definitely take some time and touch 3+ services"). Encouraging — the fix may be much smaller than the fallback.

### Sync outcome — 2026-07-15 (33 min; Anthony, Timi, Nate, Brian, Emma)

**Confirmed: the playtest licensing request is hitting the V7 API, not V10 — and that's the core problem.**

- **Why V10 is required for playtests:** normal licensing (V7) verifies entitlement via **DCAT + CC entitlements** and reads licensing info from **BigCat**. Playtests are **not in DCAT/BigCat** — the playtest bigID only resolves in **XProduct**. **V10** hits XProduct via `catalog.gamepass.com` and reads from **SUCU** instead of entitlements. So playtests **must** use V10.
- **Evidence we're on V7:** the content id in the licensing request is the **basic ContentId, not the ServicingContentId** (V7 wouldn't know about servicing ids), and the failure shows *"Content ID not found in the catalog"* = it went to **DCAT instead of XProduct**.
- **Leading cause of the V7 fallback = GRTS version.** The V10 open-licensing code originally shipped in GRTS **2606**, with edge-case fixes in **2608**, and **in 2608 the enabling flag is ON by default**. Nate's servers pull GRTS from a daily pipeline; the version is baked into the server image (Nate's team owns it). Timi could **not** find any live server on 2608 — likely on ~2606/older → **"a whole lot of conversation"** to move the image.
- **Anthony's workaround:** even on older GRTS (missing some 2608 fixes), the V10 path can likely be **force-enabled via a registry key** — Anthony is sending Timi the reg key to check/set on the VM. If that key isn't written, GRTS goes down V7.
- **Two problems, in order:** (1) get onto **V10** (registry key / GRTS version), then (2) make V10 actually **return an open license for playtests** — Anthony "didn't touch anything," so a code path may already trigger when it sees `IsRequestFromCloudServer` + cloud-server request; if not, add it. Open q: use the **default game open license** or a playtest-specific one (for the demo, whatever works is fine).
- **Secondary concern (Timi):** installs run as a **local install user** not in the playtest audience; the method that writes service/content id to the registry does a **store lookup with the bigID + user context**, which could fail for a private playtest → cache mis-hydrated. Anthony was skeptical (you'd fail earlier without XProduct data). Adding the install user to every playtest group = a workaround everyone rejected as unsustainable (local user, Nate-owned; MSA install no longer supported).
- **Token:** GRTS needs an X token with the **Store relying party** (same kind Melanie uses in Bayside) to hit the hydration/licensing API; provisioning isn't in a user context but GRTS already fetches the right relying-party token for installs — so that path may already be set up.
- **Validation step (Timi):** first prove we're chasing the right thing — let provisioning run **long enough** to see if it eventually decrypts + succeeds. If yes → to get provisioning time back to normal we must decrypt **at install** → which **requires open licensing** ("no other solution would be acceptable").
- **Escalation contacts if needed:** John Caruana, Eric Doe (licensing manager), Paul Sly (Brian's manager). **Resourcing risk:** one GRTS expert impacted last week, another on vacation.

**Action items from the sync:**
- **Timi:** pin down the exact **GRTS version** on the servers (Anthony needs it before escalating); try launching the actual AppX bundle to confirm.
- **Anthony:** send Timi the **registry key** to force V10; review the licensing code for what it does today (BigCat vs XProduct, S2S auth, whether hydration works regardless of caller).
- **Melanie:** provide the **product IDs + timestamps** of failed attempts; stand by to repro.

**Demo timeline (Emma/Brian):** XPD demo-series dry-run **next Wednesday** (record the streaming part **separately** since it's blocked); real presentation **Aug 5**. Next sync moved **earlier to Tuesday** to review blockers pre-demo. **UI review:** send ECS-flag UI PRs to the **X-playtest PR alias** + drop the team a note (they'll add Melanie to their chat + PR-tracker dashboard).

### GRTS-expert thread — 2026-07-15 (later; Brian added Jon Caruana + Ranjit)

Brian escalated to the GRTS owners. New facts that **revise the sync theory**:

- **Actual GRTS build = `2610ge_flt`** (not ~2606/2608 as guessed in the sync). So "servers too old for V10" is likely **wrong**.
- **Jon: flags are additive** — anything ON-by-default in 2608 is still ON in 2610 unless someone explicitly turned it off. So the V10 open-licensing flag being unset is **unlikely** to be the cause.
- **New leading hypothesis (Jon Caruana):** GRTS writes a **registry recording during install** that tells it which licensing endpoint (V7 vs V10) to call. That recording is **triggered by the playtest domain in the StoreId**. An **xCloud install passes a raw URL instead of a StoreId**, so the recording is **never written** → GRTS defaults to V7. This lines up with Timi's earlier "store lookup / install-user context" concern and with the basic-ContentId/DCAT evidence.
- **Diagnostic reg keys (Anthony asked xCloud to export/screenshot on the server):** ContentId = **`a499f5fe-0096-44c9-95b5-f01db1c16cc6`** (servicingContentId, from `XPackagePlaytestPublishWorkflow_9NPMGXTRGW9H.json`; the *real* install content id may differ — that's the ContentId-fix separation, so check both if known):
  - `HKLM\Software\Microsoft\GamingServices\Store\ContentId\a499f5fe-0096-44c9-95b5-f01db1c16cc6`
  - `HKCU\Software\Microsoft\Windows\CurrentVersion\Store\ContentId\a499f5fe-0096-44c9-95b5-f01db1c16cc6`
  - (These **check** whether the ContentId→endpoint recording exists — not to "force V10" as first framed.)
- **Low-probability regression:** BrianT was fixing something in GRTS before going on vacation; unclear if checked into 2610. Jon/Anthony both think a playtest-related 2610 change is unlikely.
- **Fresh logs available:** Melanie re-ran the scenario at **4:23 PM**, then again at **6:06 PM** (latest) — Nate's server logs / the VM GRTS `.etl` should cover the 6:06 PM run.

**Now to verify (this thread):**
- Export the two `ContentId` reg keys from the server → is the recording present, and does it point at V7 or V10?
- Confirm from Jon/Ranjit whether the xCloud install path passes a **raw URL vs a StoreId with the playtest domain**, and whether that gates the registry recording.
- Pull the **6:06 PM** server logs / GRTS `.etl` to trace the actual licensing endpoint hit.
- If confirmed: fix is to make the xCloud install path carry the **playtest StoreId** (so GRTS records the V10 endpoint), rather than a GRTS version/flag change.

**Owners (this thread):** Jon Caruana + Ranjit (GRTS install/registry/licensing-endpoint path) · Anthony Keller (reg keys + licensing side) · Nate's team (server logs, VM reg export) · Melanie (repro at 4:23, product/ContentId).

**GRTS log-pull runbook (Ranjit — the VM is a Kolari VM):**
1. On your **dev box/laptop**, open **Command Prompt as Administrator** (elevated).
2. Create + cd into a tools folder: `mkdir c:\servertools` then `cd c:\servertools`.
3. Bootstrap the server-tools environment (converts this cmd prompt):
   `\\edge-svcs\release\GS\Server_Environment\Latest\latest.cmd -local --UseCopy`
4. `connect PCD8877C0D284370` (your Kolari VM, from the ServerId in the server-status output — the 6:06 PM repro). The output shows the server URL + **PC Image Version** (= the GRTS build on *your* VM — note it; Ranjit's example VM showed `1.2607.1304`).
5. `pscs GetLogs` — downloads logs to `c:\servertools\<PcServerlog_0 | _1 | …>`.
6. In the download, **`gstracegamingonly.00<NNN>.etl`** holds the GRTS logs (includes install activities) — hand that to Ranjit.
Ranjit offered to sync live and review the `.etl`. These GRTS logs (not just the reg-key export) should show which licensing endpoint (V7/V10) the install actually hit.
**VM name:** `PCD8877C0D284370` is the **L1 *host* VM — NOT** the L2 guest where the repro ran (Ranjit, 07-15). Its logs (`PcServerLogs_PCD8877C0D284370_L1Host.zip`) are host infra only: `hostvm_agents/kestrel/hyperv` ETLs (no readable strings without xCloud's internal TMF manifests — don't decode locally), setup logs, and no `gstracegamingonly.*.etl`. Grep for our content (`a499f5fe`, `9NPMG`) = nothing; the host doesn't reference the session. One salvaged data point: `Composition.json` → host image = **`release/takehome2606`, `1.2607.1010`** (host layer; the GRTS build that matters is on the L2 guest, which Jon said is `2610ge_flt`). `PrespecializationStatus.json` = 07-14T18:47Z (persistent host, unrelated to the 6:06 PM repro).
**Next:** ask **Timi** for the **L2 guest VM ("server name")** of the 6:06 PM repro → Ranjit pulls + reviews those logs (he has the tooling/manifests to decode the GRTS `.etl`). Ranjit can keep pulling logs until Melanie's `edge-svcs` share access is granted (Timi's team owns the security group).

**CTDR Server Overview (Grafana, 07-15) — content install on the host SUCCEEDED:** filtered to ServerId `PCD8877C0D284370` / Sku `STANDARD_NC64AS_T4_V3` / WESTUS2 / SUG `PC_PLAYTEST`, the **Installs** table shows the playtest content present on the host: **TitleId `XPT2SDT4X91KRPC-MELANIEPLAY…`**, **InstallId `f64fe401-f03f-4aad-a0f7-6b216693…`**, **InstallHash `EBCD70C6E0A521F7`**, **612 MiB** (Installs=1; server created 07-14T11:47:18, last seen ~1h ago). **This narrows the root cause:** content **distribution + install to the host works** — so the failure is downstream at **session provisioning / decryption on the L2 guest**, consistent with the open-licensing/no-decrypt theory (content lands but stays encrypted). ⚠️ **`InstallId` ≠ `sessionId`** — this is the content/host (CTDR) layer; the L2 guest sessionId is **not** on the PCOR/CTDR fleet dashboards.

**L2 VM Id = the sessionId (Timi, 07-15):** the **Services logs** provide the sessionId, and the batch-command logs show the actual VM Id passed to the L1. Confirmed the L1 host dump does **not** contain it (only host setup artifacts — setup scripts, firewall/ETW GUIDs, CimSession `cs7o3foyi4xwk`). Melanie found the host `PCD8877C0D284370` via **Grafana** — specifically the **"PCOR Server Status"** dashboard (`OrchestrationServerStats` panel: ServerId/GameplaySlots/AvailableSpace/Installs/MaxAllowedInstalls). **That dashboard is fleet/server-only** (tables `SVCcontentdistribution` + `SVCpcorchestrator`; filters Sku/SUG/ServerRegion; all keyed to **ServerId = L1 host**) — it has **no session/sessionId/guest data**, so it can't yield the L2 VM Id. The **sessionId lives in the session/`SVCvmcommunication` logs** (which Nate's original union query included but this dashboard omits). **Services logs = the Savant console** (`…/SavantFrame/…`), which exposes per-service log categories — *these* are what Timi means by "Services logs." Relevant categories to find the session/L2 VM: **`sessions`** (the sessionId), **`vmcommunication`** (the batch command → the actual VM Id passed to the L1 — Timi's exact phrase), **`vmcreation`** (the L2 guest VM Id at creation), **`pcallocator`** (maps session → host `PCD8877C0D284370` → guest VM). ⚠️ **Environment must match the repro:** the Savant Melanie opened was **`gssv-dev-test`**, but Ranjit's `connect` showed the server on **`gssv-dev-Prod`** (`AMERICAS.gssv-dev-Prod.xboxlive.com`) — use the **gssv-dev-Prod** Savant (matching the repro env) or the 6:06 PM session won't be there. Open `vmcommunication`/`pcallocator`, filter to host `PCD8877C0D284370` + the repro time, and read the **guest VM Id (= sessionId)**; cross-check it against content `a499f5fe` / InstallId `f64fe401` / TitleId `XPT2SDT4X91KRPC`.

Fallbacks if Savant is unclear: **Nate / the diagnostics bug**, or Kusto `SVCvmcommunication` filtered to host `PCD8877C0D284370` around the repro time. That sessionId is what Ranjit uses to pull GRTS logs off the L2 guest.

**Savant `sessions` console (07-15) — schema + gotcha:** the `sessions` service has `s|sessions [-userId] [-sessionId] [-state] [-includeTestSessions] [-count]`, `sd|sessionDetails [-sessionId] [-xuid]` (full session doc → server/rig), `grsp|getRigSessionParameters [-sessionId] [-xuid]` (the rig = the VM directly), `n|numSessions`. **Session row columns: `Id` (= sessionId), `ClientInstanceId`, `Xuid`, `UserId` (gamertag), `State`, `SessionCreateTime`, `SessionExpiryTime`, `ServerId`, `SessionParameters` (JSON w/ OfferingId/TitleId/ProductId).** ⚠️ **`s -count 20` returned only consumer XGPU sessions** (Fortnite/CoD/Starfield… `OfferingId: XGPUWEB/CONSOLE/PCAPP`) — the playtest session was **not** in it (aged out of the newest-20 in a busy env; none of `PCD8877C0D284370`/`XPT2SDT4X91KRPC`/`MELANIE` present). **To catch it: filter by xuid/gamertag** (`s -userId <gamertag>` or `sd -xuid <xuid>`), **or** re-run the repro and immediately `s -count 20` to grab the live row's `Id` (= sessionId) + `ServerId`. **Note:** a 2h-old L2 guest is likely already **ResourcesReleased/recycled**, so a **fresh repro + live log-pull** (Ranjit) is the most reliable way to get usable GRTS guest logs. Still run `comn-ei` to confirm the Savant env matches the repro (`gssv-dev-Prod` vs `gssv-dev-test`).

**✅ CONFIRMED (Timi, 07-16): L2 VM Id == SessionId** — his worked example: `SessionId = 74AB59A6-7976-442C-9D65-2627026346F5`, `L2 VM Id = 74AB59A6-7976-442C-9D65-2627026346F5` (identical GUIDs; Session cV `zwqKsuAoS0SNOtBLhx8LQW.84`, start `2026-07-16T16:05:03Z` — that's *Timi's* demo repro, not Melanie's). **So the `Id` column from Savant `s -userId enoughdaisy5498` IS the L2 VM Id — hand that straight to Ranjit; no cV trace needed.** Timi's manual method (if ever needed to confirm): search **sessions logs** (Geneva) for your **gamertag** around the repro timestamp → get the **session cV** (`<baseCv>.<number>`, drop the trailing sections) → search that cV → find the **"Allocate VM slot"** batch command → its args carry the **L2 VM Id**. Melanie's gamertag = **`enoughdaisy5498`**. Since yesterday's 6:06 PM guest is surely recycled, **do a fresh repro now**, read the `Id` from Savant, and give it to Ranjit while the session is live.

**⚠️ Savant `sessions` was a dead end — use GENEVA instead (Timi's actual method, 07-16):** `s -userId enoughdaisy5498` returned **empty even during a live launch** (wrong env and/or the playtest session's `UserId`/`Xuid` isn't the gamertag — recall the **local install user**). Timi's working method is in **Geneva** (`portal.microsoftgeneva.com`), not Savant:
1. Do a session (fresh repro); note the timestamp.
2. Search **sessions logs** for your **gamertag `enoughdaisy5498`** around that time → read the **session cV** (`<baseCv>.<number>` — keep base + first number, drop the rest).
3. Search sessions logs for that **cV** → find the lines generating the **batch command for provisioning**.
4. The **"Allocate VM slot"** command's args carry the **L2 VM Id** (= SessionId).
Timi's template query (his demo values — open it, swap in your gamertag + repro time): **`https://portal.microsoftgeneva.com/s/67FF522`** — SessionId `74AB59A6-7976-442C-9D65-2627026346F5`, cV `zwqKsuAoS0SNOtBLhx8LQW.84`, start `2026-07-16T16:05:03Z`. Give the resulting L2 VM Id (= SessionId) to Ranjit.

**✅✅ FOUND (07-16 fresh repro) — L2 VM Id = SessionId = `14D38502-9DDF-4D6E-8478-2322E5B134BB`.** From a Geneva `SessionCleanupEvent` (roleInstance `sessions-primary-…`, `AgentController.PcProvisionRequestResponseAsync`): `data_SessionState = ProvisioningFailed`, created `2026-07-16T17:36:11Z`, cleanup started `17:38:24Z` (failed after ~2 min → guest recycles fast, pull logs immediately). **Melanie's xuid = `2535468197147061`** (from provision path `/v1/agent/pc/provision/14D38502…/2535468197147061`) — the gamertag filter failed because the session is keyed on xuid; use `2535468197147061` next time. Session **cV base = `YL6BKYlAOqmk4V2WcTIN9U.0`** (search it for the "Allocate VM slot" batch command to confirm the exact L2 VM Id if needed). **`ProvisioningFailed` = the blocker reproduced** (provisioning-side, consistent with the no-decrypt/open-licensing root cause). Hand `14D38502-9DDF-4D6E-8478-2322E5B134BB` to Ranjit for the L2 guest GRTS log pull.

**⚠️ Ranjit constraint (07-16): the guest VM must be ALIVE to pull logs** — `ProvisioningFailed` state is fine, but once cleanup recycles the VM the logs are gone. Melanie's session cleans up **~2 min after creation** (created 17:36:11Z → `SessionCleanupEvent` 17:38:24Z), so this must be **coordinated live**. Playbook: Ranjit pre-positioned/ready → Melanie launches → she reads the fresh `data_SessionId` from Geneva (filter **xuid `2535468197147061`**) **as soon as it appears during provisioning** (not after failure) → sends it instantly → Ranjit connects + pulls while the VM is still alive. Open question for Ranjit: is there a way to **hold/keep the guest VM alive longer** (lock/keep-alive) to widen the window.

**Session trick (Timi, 07-16) + fresh-server plan:** to guarantee which server your session lands on, **check out the server with reason `Session-{gamertag}`** (e.g. `Session-EnoughDaisy5498`) — it pins your next session to that server. **Not needed here** because the offering's SUG (`PC_PLAYTEST`) has **only one VM** and only that SUG is wired to the offering, so the session lands there regardless. Access reality: Melanie has **no servertools access** (security group unknown — Timi's team to identify), so **Ranjit runs `pscs GetLogs`**. Since the existing install is >2 days old (noisy), **Timi spun up a fresh clean server `PCDADF20C7AB20F6`** — plan: **Melanie repros → session lands on `PCDADF20C7AB20F6` → Ranjit pulls GRTS logs**. (Mostly a clean-VM confirmation now that Bug 63132145 already has the GRTS `.etl` + root cause.) Melanie's MSA = `ychen.melanie@gmail.com`, gamertag `EnoughDaisy5498`, xuid `2535468197147061`.

**✅✅✅ ROOT CAUSE CONFIRMED — Bug 63132145 (auto-filed 07-16 16:09 UTC, assigned Nate, `Xbox\Platform\Streaming\Server\PC`).** Services auto-filed this from the repro (offering `XPT2SDT4X91KRPC`/XSTH, server `PCD8877C0D284370`, session `74AB59A6-7976-442C-9D65-2627026346F5`, cV `zwqKsuAoS0SNOtBLhx8LQW`). Title: *"[PCServer] StreamingChild - PROVISION failed: game pre-launch license acquisition failed (0x87E10BC6), LaunchByContentId timed out after 90s."*
- **Failure chain (from the actual logs):** VM provisioned fine (AllocateVmSlot/AttachDisk/StartVm all OK) → in-VM **pre-launch license acquisition FAILED: `XboxLicenseManager` returned `0x87E10BC6` ("not retrying")** → `gamelaunchhelper.exe` (pid 11444) showed a blocking *"Something went wrong launching your game"* dialog → game stuck in **Starting**, never Running → **`LaunchByContentIdV1` blocked the full 90 s then timed out** (`0x80131505`/COR_E_TIMEOUT) → provision failed.
- **Root cause = title-licensing/entitlement failure, NOT server infra** (Nate). **Smoking gun: the license call's `callerId = "noIdentity"`** — the request had **no identity/token**, so licensing refused with `0x87E10BC6`. This is the concrete manifestation of the open-licensing gap. Candidate sub-causes: (A2, med) missing/late identity token **or** the playtest sandbox/account isn't entitled for XSTH — WAM MSA account cached only **~1 s before** the license call (16:05:42) → possible **race**; (A3, low) transient XBL licensing error.
- **The GRTS `gstracegamingonly.005.etl` is ALREADY ATTACHED + analyzed** in this bug ([E4]: `XboxLicenseManager "Error 0x87e10bc6 ... not retrying" proxy.cpp:781` → `GameLaunch gameflt main.cpp:1973 hr 0x87E10BC6 callerId:"noIdentity"` package XboxStreamTestHarness). **So the live L2-VM log pull is likely unnecessary** — logs at `\\XFSBugDecoder.redmond.corp.microsoft.com\Decoded\Xbox\63132145` + `FindLogsFromCv.cmd $zwqKsuAoS0SNOtBLhx8LQW`.
- **Version reality (corrects the GRTS thread's "2610"):** this repro ran on **GRTS `1.0.2607.0903` (2607.09, branch main)**, image **`1.2607.1010`**, server.pc **`1.2607.1004` (release/takehome2606)**, agent `1.2607.1004.0`. So the failing servers are **2607-lineage, not 2610** — and if V10 open-licensing is on-by-default only in 2608, 2607 would fall back → consistent with the license failure.
- **Nate's next steps:** (1) verify entitlement/license for XSTH + offering XPT2SDT4X91KRPC in the provisioning sandbox; (2) investigate the `noIdentity`/WAM race (is identity expected at pre-launch); (3) check XBL licensing health for `0x87E10BC6` spikes; (4) fail-fast on unrecoverable license errors instead of the 90 s block.

**🔑 MECHANISM CONFIRMED — Anthony's registry finding (07-16): the `\Store\ContentId` registry keys are written at INSTALL-time but LOST at PROVISION-time because the VMs are ephemeral and different.** This confirms Jon Caruana's earlier "registry recording not written" hypothesis and explains the `noIdentity`/`0x87E10BC6` failure:
- xCloud uses **two different guest VMs**: **install-time** (runs as a **local install user**) and **provisioning-time** (runs as the **real user who owns the Title**).
- **Install-time:** both **HKLM** and **HKCU** have keys under `\Store\ContentId\<ContentId>` (the recording that tells the system how to license/decrypt that content).
- **Provisioning-time:** **nothing under `\Store\ContentId`** for HKCU (Anthony confirmed), and almost certainly nothing for HKLM either.
- **Why:** the install writes content to a **VHD → unmount → mount that VHD onto the provisioning VM**. **Registry keys live in the VM OS, not on the content VHD**, so the `\Store\ContentId` keys written at install **don't carry over** to the ephemeral provisioning VM.
- **Effect:** at launch the license manager looks up the ContentId in the (missing) registry keys → can't resolve identity/licensing → license call goes out as **`noIdentity`** → `0x87E10BC6` → content stays encrypted → 90 s `LaunchByContentIdV1` timeout.
- **Likely fix (Anthony's lead):** provisioning-time runs `Package::Register` + `Unlock`, but those apparently **don't set the `\Store\ContentId` registry keys** — so the fix is to make the provisioning step **re-establish those registry keys** (re-record the ContentId→licensing mapping on the provisioning VM). Server/GRTS-side change (Nate/Anthony), likely smaller than a licensing-service rewrite.

**Options (updated):**
1. **Confirm which licensing API/contract + clientId the playtest streaming path uses** — is GRTS calling v10 with an *allowlisted* clientId for playtests, or falling back to v7 / a non-allowlisted client? (Anthony can grep the licensing logs given the **product IDs + timestamps** we tried. Getting the **allowlisted clientId onto the playtest token** may be the smallest real fix.)
2. **Add open-licensing support on the playtest path in the Licensing service (v10).** Anthony implemented PC open licensing there a couple years ago and can make changes, **but the owning team was impacted last week**, and it needs design agreement + implement + merge + deploy → **not fast.** Anthony to have a rough cost summary after lunch (07-15).
3. **Accept longer provisioning** (only if the unlock actually happens but is just slow) — pending log validation.

**Open questions / next:**
- Validate the theory from the diagnostics logs (is the unlock failing outright, or slow?).
- Get Anthony the **product IDs + timestamps** of the failed licensing attempts so he can find them in the licensing logs.
- Identify the **clientId** used by the playtest streaming licensing token and whether it's on the allowlist.

**Boundary (verified vs external):** *Verified in our (Xbet) code* — the playtest publish attaches licensing data to SUCU (`PlaytestProductDocumentBuilder.BuildLicensingData`: a **playtest-specific** `PolicyCardId = playtest:7E9B3F2A…`, MSIXVC `DeriveSeed`, `SatisfyingEntitlementKey = sucu:{product}/{sku}/{servicingContentId}/{version}`), which is plausibly *why* licensing routes playtests down the "separate path." *External / not verifiable here* — the Licensing service v10/v7 behavior, the open-license token generation, and the allowlisted clientId all live in xCloud + Licensing repos (only `services.contentingestion` is cloned locally, and it has no open-licensing code). Those are Timi/Anthony-owned.

**Owners:** Anthony Keller (Licensing service / v10 open-licensing path) · Timi Bolaji (xCloud token + GRTS licensing call) · Nate's team (PC server install/decrypt, diagnostics logs) · Melanie Chen (playtest side; provide product IDs/timestamps, repro).

## Update — 2026-07-14 (Nate thread): provisioning still fails; diagnostics bugs next

Re-ran a playtest launch on the TAKEHOME-inherited build — **still failing, on the provisioning side.** Cleared up with Nate that the earlier bug thread ([63080510](https://dev.azure.com/microsoft/Xbox/_workitems/edit/63080510)) is about **deprovisioning**, whereas my failure is on **provisioning**:

```
SessionServerError : InternalCode -2146233083
WaitForCloudLaunchCompletion:158 Cloud launch did not complete within 90000 ms
```

- **Offering:** `XPT2SDT4X91KRPC` · **SUG:** `PC_PLAYTEST` (inherits `PC_TAKEHOME`) · **config PR:** 16158748 (`[PLAYTEST] Configure playtest offering XPT2SDT4X91KRPC`).
- I offered to **repoint the `PC_PLAYTEST` SUG** to any build that doesn't have the bug — Nate didn't have a known-good one to hand.
- **Plan (Nate owns, ~2026-07-15):** enable **diagnostics bugs** on the offering. These are **auto-filed by Services** whenever provisioning/deprovisioning fails and **contain all the logs**. Once enabled, Nate pings me to **repro the failure** so he can pull the logs and root-cause the provisioning timeout.
- **My action:** provided SUG + offering (done); stand by to repro on Nate's ping.

## What happens

Install + provisioning succeed, but the launch batch command times out:

```
Batch Command LaunchByContentIdV1 Failed - Error: -2146233083
  at Microsoft.GameStreaming.Server.Pc.UserAgent.TitleWrapper.WaitForCloudLaunchCompletion:158
  Cloud launch did not complete in an expected timeframe of 90000 ms
```

`-2146233083` = `0x80131505` = `COR_E_TIMEOUT` (`System.TimeoutException`). The launch command **fires** and the content is on the box (past install/provision), but the title never reaches "launched" within 90s.

## Root cause (per Nate, 2026-07-13)

A GRTS server-build issue on the PC streaming server, tracked as Bug [63080510](https://dev.azure.com/microsoft/Xbox/_workitems/edit/63080510) (dup of 62681432): `WaitForConnectedStorageToBeIdle` times out (60s) during **deprovision** because Connected Storage is still active (`ConnectedStorageActive`). It's flagged **non-fatal** and the **game save is preserved** — but it surfaces as the launch not completing cleanly. Not a contentId/not-found issue (that chain is fixed): `LaunchByContentIdV1` resolves and starts. The title is a small GDK desktop build (DX12, ~10 MB) that launches fine locally.

**A partial fix is in `PC_TAKEHOME` as of 2026-07-13** (PC_PLAYTEST inherits it automatically). The **full fix is pending a GRTS-team discussion on Thursday.**

## Options

1. **Wait** (chosen) — the fix landed in `PC_TAKEHOME` today and PC_PLAYTEST inherits it automatically, so no SUG change is needed. Full fix tracked to the Thursday GRTS discussion.
2. **Switch the build** by changing the `PC_PLAYTEST` SUG (`InheritsFrom` or an explicit `InitialVersion` pin) — not needed now that TAKEHOME carries the fix. Nate confirmed PC_BVT / PC_BVT_RELEASE are **pre-validation** lanes to avoid.

### SUG / build landscape (PROD, NC64 T4 = `STANDARD_NC64AS_T4_V3`, as of 2026-07-13)

`PC_PLAYTEST` has no build of its own — it `InheritsFrom: PC_TAKEHOME`.

| Lane | NC64 T4 build | Note |
| --- | --- | --- |
| **PC_PLAYTEST** | 1.2606.2604 (inherited) | current — **broken** |
| **PC_TAKEHOME** | 1.2606.2604 | PC_PLAYTEST's parent — broken |
| **PC_GA / GA** | 1.2606.2604 | same broken build — switching here would NOT help |
| PC_BVT | 1.2607.1301 | newer, but fast-moving dev lane |
| PC_BVT_RELEASE | 1.2607.1010 | newer "release" build |
| PC_TESTX_SHADER_GENERATION / PC_INTEGRATION_TESTING_ADFERNANDES | 1.2607.0902 | newer |

**Key catch:** PC_GA/GA are on the *same* broken 1.2606.2604, so re-pointing to GA changes nothing. The only newer NC64 T4 builds are on test/BVT lanes. `PC_PLAYTEST` sets `UseBackgroundInstall: false` directly, so that playtest override survives any inheritance change.

## Ask / next steps

- 🔴 **Not resolved** — the "wait for TAKEHOME" path did **not** fix it; launch still times out on **provisioning** (retested 2026-07-14).
- **Await (Nate, ~2026-07-15):** diagnostics bugs enabled on offering `XPT2SDT4X91KRPC`, then **repro on his ping** to capture the provisioning logs.
- **Repoint the SUG only if Nate identifies a known-good build.** Avoid PC_BVT / PC_BVT_RELEASE (pre-validation lanes, per Nate).
- **Thursday:** GRTS-team discussion on the full fix for Bug 63080510 (deprovision-side; related context).

## References

- Nate thread (2026-07-13) — GRTS build issue; fix in PC_TAKEHOME; game save preserved; Thursday GRTS meeting.
- Nate thread (2026-07-14) — provisioning (not deprovision) still failing; offering `XPT2SDT4X91KRPC`, config PR 16158748; Nate to enable **diagnostics bugs** (~07-15) then Melanie repros for logs.
- Bug [63080510](https://dev.azure.com/microsoft/Xbox/_workitems/edit/63080510) — `[PCServer] StreamingChild - Deprovision non-fatal: WaitForConnectedStorageToBeIdle timed out 60s` (dup of 62681432), `Xbox\Platform\Streaming\Server\PC`.
- [`pc-playtest-msixvc-install-error-not-found.md`](./pc-playtest-msixvc-install-error-not-found.md) — the prior (resolved) install/provision `ERROR_NOT_FOUND` blocker.
- [`pc-playtest-sug-registration.md`](./pc-playtest-sug-registration.md) — PC_PLAYTEST SUG definition + registration.
