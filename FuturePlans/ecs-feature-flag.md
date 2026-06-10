# Future plan: ECS feature-flag gating

**Why it matters:** During private preview we want streaming-enabled publish enabled only for a controlled set of sellers so any hiccups don't affect existing playtest customers. Playtest itself is already enabled on a limited basis by seller today, so this follows an established pattern.

## Current understanding (Sync 3 — Anthony, David K)
- Use the **ECS** config system (portal: `ecs.skype.com`) to gate the feature by **seller ID** (Brian: seller id is probably sufficient; product id optional).
- A deployment is required to change/update ECS values.
- David K is creating ECS configs for playtest and noted **two** configurations: one that shows the left-nav element (made available broadly), and a fallback "welcome to playtest / join the preview" intro page when the second config isn't present.
- ECS requires the right permissions and approval — David K said it took weeks to get approved; he offered to sync offline / create the config since editing the ECS file is gated.

## Options
- Reuse/duplicate an existing playtest ECS template that allows specifying seller IDs (and optionally product IDs).
- Gate the new ingestion endpoint/workflow so it only runs for allow-listed sellers; for early testing, hardcode Melanie's own seller id, then move to ECS.

## Open questions
- Who is the approving audience for the new ECS config?
- Seller-only vs seller+product granularity for v1.
- Is ECS reachable from the workflow yet, or only the front-end today?

## Owners
Melanie Chen · David Kushmerick (ECS setup/permissions) · Anthony Keller.
