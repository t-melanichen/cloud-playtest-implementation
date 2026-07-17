# [SESSIONS] PR 16140301 — Separate ContentId from SourceId (use explicit ContentId for most cases)

- **Pull Request:** 16140301
- **Repo:** services.sessions (Xbox.Streaming)
- **Source branch:** → `main`
- **Status:** Active (merge succeeded; in review / rolling out for test)
- **Author:** Timi Bolaji
- **Link:** https://microsoft.visualstudio.com/Xbox.Streaming/_git/services.sessions/pullrequest/16140301

## Summary
The **provisioning** side of the ContentId fix. After the distribution/install fix (CTDR 16137972) let the build
install, provisioning then failed for the same underlying reason — the provisioning command was using the servicing
`SourceId` instead of the real `ContentId`. This PR separates the two in Sessions so provisioning uses the
explicitly-provided real `ContentId`.

- Separates `ContentId` from `SourceId`; uses the explicitly-provided `ContentId` for most cases (provisioning
  commands), while sourcing continues to use `SourceId` (servicing).

## Role in the fix
Fifth PR in the ContentId separation. Sourcing → servicing id; content/install/provisioning commands → real
`contentId`. With this, **install + provisioning both succeed** and the build reaches a launchable state on the
server. The remaining failure (launch timeout) is a separate GRTS server-build issue — see
[`../Blockers/pc-playtest-launch-timeout-grts.md`](../Blockers/pc-playtest-launch-timeout-grts.md).
