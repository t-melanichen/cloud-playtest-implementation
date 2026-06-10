# Future plan: Region configuration + routing

**Why it matters:** A streaming offering only installs content in the regions it's configured for, and there's no automatic DNS-based routing for these playtest offerings yet — so getting a tester to the right data center needs explicit handling.

## Current understanding (Sync 3 — Brian, Timi)
- The **offering must be configured for the right regions**; that's what indicates which data centers get the content installed. We don't install everywhere by default.
- Because there's **no DNS lookup** for these offerings, when the player goes to stream, the client must **supply a region query parameter** to say where to route — unless we can do automatic DNS/IP lookup for these special playtest offerings.
- **Timi (v1 simplification):** for the testing phase, assume everyone streams from roughly **West US2**. We can have a single PC server, make a separate SOG (PC LAN sense), install on that one server, and use **offering conflict** to ensure login to that offering routes to it — so **no region parameters needed in v1**.

## Options
- **v1:** single West US2 PC server + offering conflict routing; no region params.
- **Later:** Partner Center UI for the creator to select allowed regions (offering configured accordingly); investigate automatic DNS/IP routing to avoid client-supplied region params.
- **Long-term (Brian):** multiple PC "flavors" (low/med/high GPU) coordinated with PC-server folks.

## Open questions
- Is automatic DNS/IP routing feasible for playtest offerings, or do we require a region query param?
- Where does region selection live in Partner Center vs the streaming client?

## Owners
Melanie Chen · Brian Bowman · Timi Bolaji · PC-server team (Nate).
