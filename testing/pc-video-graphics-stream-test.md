# Testing the stream with the new PC video graphics

Notes from the **2026-06-30 Design Brainstorm** (`Transcripts/Design Brainstorm - Playtest UX.docx`, local-only)
on validating the end-to-end PC playtest stream with an obviously-moving image, so you can *see* the stream is
actually rendering (not a frozen/black frame).

## Test content — ATG PC "VideoTexture12" sample

Use the Microsoft **ATG (Advanced Technology Group) PC sample "video texture"** as the streamed content:

- Find it on GitHub: search **"ATG PC samples video texture"** (a.k.a. "ATG/ATC samples PC graphics video
  texture"). Clone the whole samples repo and open the **VideoTexture12** solution (the DirectX 12 video-texture
  sample for PC / `.sln`).
- Out of the box it renders a **spinning rectangle with a video mapped onto it** — an obvious, continuously
  moving image that makes it immediately clear the stream is live.
- Optional (more engaging): with a small amount of AI-assisted tweaking, make **multiple balls bounce around**,
  each playing video — more motion across the frame, easier to eyeball latency/jank.

## Harness & accounts

- **Test harness:** the **Xbox Stream harness** drives the stream.
- **Test publisher:** **"X cloud test publisher 1."**
- **Pilot seller gate:** streaming is only enabled for the **pilot seller id `65050620`** (confirmed in the
  meeting: *"streaming's only enabled if it's my seller id"*). Run e2e as that seller.
- **PC to stream from:** you need a **provisioned PC server** with the build installed/streamable (the brainstorm
  explicitly asked *"what kind of PC are you getting to stream this off of?"*). Tie-in with PC install-readiness
  polling — see [`../FuturePlans/pc-install-readiness-polling-implementation.md`](../FuturePlans/pc-install-readiness-polling-implementation.md).

## Pre-reqs for a clean e2e (from the Xbet publish/XORc flow)

- The pilot seller's **test product must be Xbox-Live-configured** (resolves a `TitleId` in XORc) — otherwise
  publish **fails fast** when streaming is opted in.
- Give the test playtest a **future end date** (`PlaytestEndDateMustBeInFutureRule` now blocks already-expired
  playtests for all sellers).
- XORc must be reachable from PlayTest in the target env (a transient XORc 5xx fails the pilot-seller publish).

## What this validates

Configuring a playtest → publishing (PlayTest → XORc title-id resolution → workflow → SAGE ingestion) →
launching the deep link → **seeing the spinning/bouncing video render** over the cloud stream end to end.

## Build & packaging log — DONE (2026-07-05)

The plan above was executed: the ATG VideoTexture sample was built and packaged into an
xCloud-ingestible **MSIXVC** (a **test** package with placeholder identity — see "Next steps").

### Exact sample
`microsoft/Xbox-ATG-Samples` → **`PCSamples/Graphics/VideoTexturePC12`** (`VideoTexturePC12.sln`).
Plain Win32 **DirectX 12** app; uses Media Foundation (`MediaEnginePlayer`) to play
`Media/Videos/SampleVideo.mp4` onto a texture. It is **not** a GDK project — it builds to a plain `.exe`.

### Machine / environment (verified 2026-07-05)
- Visual Studio **Community 2026 (18.6.3)**, MSVC 14.44 (`v143`) / 14.51 (`v145`), Windows SDK **10.0.26100**.
- **Microsoft GDK not installed** and the account is **not local admin** → used a **BWOI** extract of the GDK.
- ⚠️ Machine has **`NoDefaultCurrentDirectoryInExePath`** set: cmd will not run a `.cmd`/`.bat` by bare name from
  the current dir — invoke via explicit `.\name.cmd`. This otherwise breaks DirectXTK's shader pre-build step.

### Build
Clone out of OneDrive, retarget the old `v141`/SDK-`19041` project to `v143`/`10.0.26100`, and (because of the
lockdown above) pre-compile DirectXTK's shaders with an explicit `.\` path — all inside `vcvars64`:
```bat
cd C:\Users\t-melanichen\source
git clone --depth 1 https://github.com/microsoft/Xbox-ATG-Samples.git
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat"
cd /d C:\Users\t-melanichen\source\Xbox-ATG-Samples\Kits\DirectXTK12\Src\Shaders
call ".\CompileShaders.cmd"
cd /d C:\Users\t-melanichen\source\Xbox-ATG-Samples\PCSamples\Graphics\VideoTexturePC12
msbuild VideoTexturePC12.sln /p:Configuration=Release /p:Platform=x64 /p:PlatformToolset=v143 /p:WindowsTargetPlatformVersion=10.0.26100.0
```
Ready-to-run helper: `C:\Users\t-melanichen\source\_build_vt.bat`.
**Output:** `...\PCSamples\Graphics\VideoTexturePC12\x64\Release\VideoTexturePC12.exe` (x64).

### Package into an MSIXVC (Gaming.Desktop)
1. **BWOI-extract the GDK** (no admin) — public GDK **April 2026 Update 2 (v2604.2.7849)** from
   `github.com/microsoft/GDK` releases; then
   `msiexec /a "<Installers>\Microsoft GRDK x86 Common-x86_en-us.msi" /qn TARGETDIR=<dir>` (+ GDK Common,
   PC Development). → `makepkg.exe` under `<dir>\Microsoft GDK\bin\`.
2. **Layout** (`...\_gdk\layout\`): the `.exe`, `Media\Videos\SampleVideo.mp4`, `Media\Fonts\*.spritefont`,
   placeholder logos, and `MicrosoftGame.config`.
3. **`MicrosoftGame.config`** essentials: `<Identity>`, `<ExecutableList><Executable Name="VideoTexturePC12.exe"/>`,
   `<ShellVisuals StoreLogo/Square150x150Logo/Square44x44Logo/SplashScreenImage>`, and
   `<DesktopRegistration><DependencyList><KnownDependency Name="VC14"/></DependencyList></DesktopRegistration>`
   (required — the Win32 exe depends on the VC++ runtime).
4. **Pack for PC:**
   ```bat
   set GameDKLatest=<dir>\Microsoft GDK\260402\
   set GRDKLatest=<dir>\Microsoft GDK\260402\windows\
   makepkg genmap /f chunks.xml /d layout
   makepkg pack   /f chunks.xml /d layout /pd out /pc
   ```
   Validator gotchas fixed: **StoreLogo must be 100×100** (not 50×50); binary needs the **`VC14`** KnownDependency.
**Output (all Submission Validator checks SUCCEEDED):**
`C:\Users\t-melanichen\source\_gdk\out\MelanieATG.VideoTexturePC12_1.0.0.0_x64__qfz1z4rvaj27y.msixvc` (~10 MB).

### Next steps (to make it a real ingest, not just a test package)
- Replace the placeholder **identity** (`MelanieATG.VideoTexturePC12` / `CN=MelanieATGTest`) and the "VT"
  placeholder **logos** with real assets, and re-pack with a real **ProductId**:
  `makepkg pack ... /pc /productid <id>` (current `ProductId` is all-zeros). Confirm identity/StoreId with Brian.
- To *see* it render (spinning video quad), run the `.exe` on a machine with a GPU/display; iterate on visuals
  (multiple shapes/spheres) from there.
- Ingest via the usual PC playtest flow (X1 test publisher, pilot seller `65050620`, PC install-readiness polling).
- **Upload → ingest runbook:** [`videotexture-upload-and-ingest-runbook.md`](./videotexture-upload-and-ingest-runbook.md)
  — step-by-step to get this package onto a PC server via **xPackage → DevApi → CTIN**.

## References

- `Transcripts/Design Brainstorm - Playtest UX.docx` (local-only) — the testing discussion.
- [`../Explanations/xbet-15834601-design-decisions.md`](../Explanations/xbet-15834601-design-decisions.md) — the publish→XORc→SAGE flow.
- [`../Playtest-UI-Meeting-Karla-Kush.md`](../Playtest-UI-Meeting-Karla-Kush.md) — meeting conclusions / e2e status.
