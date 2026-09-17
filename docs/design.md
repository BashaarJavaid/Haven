# Design

Design is a quarter of the hackathon score and, in a video-judged event, it means exactly what is on screen: the cards on the Echo Show, the phone screens, the simulator frame, and the spoken lines. This file is the spec for all four. It follows Amazon's add-on design guide verbatim, because the project's convention is "real API contracts, verbatim" and the design guide is part of the contract.

Sources (fetched 2026-09-16; re-read when the cards are built, and cite the page in the code): [visual foundations](https://developer.amazon.com/docs/alexaplus/add-ons/mcp-addon-visual-foundations.html), [display modes](https://developer.amazon.com/docs/alexaplus/add-ons/mcp-addon-display-modes.html), and the guide's other pages linked from the [MCP Toolkit overview](https://developer.amazon.com/docs/alexaplus/add-ons/mcp-toolkit-overview.html) (layout and rendering, components and patterns, brand expression, accessibility, tools/schema/data design).

---

## 1. Tokens (Amazon's, verbatim)

Defined once as CSS custom properties in `apps/mcp-app` and used by every card. No component library inside the cards: they load in a sandboxed iframe, so the bundle stays small and dependency-free.

| Token group | Values |
|---|---|
| Base canvas | 768×480; scaled by 1.667 on Echo Show 8 and 15 (the simulator's Echo Show frame renders at 1280×800) |
| Type scale (px at base) | Display1 48, Display2 40, Display3 32, Display4 28, Display5 24; Headline1 20, Headline2 18; Body1 16, Body2 14, Body3 12; Label1 10, Label2 8 |
| Spacing (px) | 2, 6, 8, 12, 16, 20, 24 |
| Corner radius (px) | 4, 8, 12, 16; circle 9999 |
| Icons (px) | 16, 20, 24 |
| Dark mode | background `#14181E`, nested inner `#1B2028`, primary button `#2D415E` |
| Light mode | background `#FFFFFF`, nested outer `#FAF9FB` |

Principles taken from the guide: reduced content density (fewer metadata fields, less per card); readable at arm's length, about 3 feet, with essential information legible from about 10 feet; light and dark supported natively; bold color reserved for buttons that complete a final action.

## 2. Display modes (Amazon's, verbatim)

- **Voice-only** is the always-on baseline. Every tool output is complete in `speakable`, with no formatting artefacts (no pipes, no markdown).
- **Inline** is the default for a card: it complements the spoken reply.
- **Fullscreen** is for dense content (the plan timeline, the decision list). It is entered through a control the customer operates, never spontaneously.
- **Hydrated**: when no UI payload is sent, Alexa renders the data natively, so `data` stays clean.
- Tools declare the modes they support. The declaration syntax is taken from the guide when the tools are built, not guessed here. The old custom `presentation` hint survives only as the simulator's Echo Show / Echo Dot switch.

## 3. Card rules

1. **One job per card.** Inline: one headline figure or sentence, at most three rows, one primary action.
2. **Anything denser goes to fullscreen**, behind a control.
3. **The accent color appears only on the final-action button** (Approve, Activate, Check with Malik).
4. **Two badge states on cards: `live` and `simulated`.** `real` observations are live; `twin` and `real API, demo devices` both show as simulated, the more conservative reading. A published rate table is labeled *published ComEd rate*. The full three-way `source` stays in the data, the companion app's detail view, and the audit trail.
5. **No internal IDs, class names, or JSON** on any card.
6. **Three motions, all CSS transitions, no animation library:** the EV bar moves when the plan changes by voice; the verification card goes from *pending* to the result; the door goes locked → unlocked → relocked.

## 4. The seven hand-designed screens

These appear on camera, so they are designed by hand. Every other companion page (Household, Audit, Twin, the YAML view, settings) uses Tailwind + shadcn/ui defaults with no custom design work.

| # | Screen | Surface | Inline content | Fullscreen |
|---|---|---|---|---|
| 1 | Plan card | Echo Show | Dollars saved tonight (Display size); three rows (battery through the peak, pre-warm for Mom, car after 9); Approve | Timeline, all actions, alternatives, the annualized figure |
| 2 | Verification card | Echo Show | One headline ("That number isn't one of Malik's"); up to three signals; status chip (*checking with Malik* → *Malik is fine*) | none |
| 3 | Doorbell card | Echo Show | Snapshot; one context line ("Nobody is expected right now" / "A vehicle arrived at 6:58. Mom is expected at 7:00"); request-unlock button; for `security.*` the approval state reads *approve on your phone* and there is no Approve button | none |
| 4 | Scorecard | Echo Show | Dollars saved, annualized figure, peak kWh avoided | Counts (autonomous, asked, blocked, verified) and the decision list |
| 5 | Rule diff and Activate | Phone | The English sentence; a before-and-after line ("Unexpected visitor: ask on phone → never"); a collapsed line with the compiled Cedar; Activate (passkey) | n/a |
| 6 | Check-in | Phone | "Your mom is checking it's really you. Someone called her claiming to be you."; two buttons: **It was me** / **It wasn't me. I'm fine.** | n/a |
| 7 | Unlock approval | Phone | "Unlock the front door for Mom, 10 minutes"; the rule and band in one line; Approve (passkey) / Deny | n/a |

## 5. Identity

Minimal: a wordmark, one accent color, one typeface. No logo project. Following Amazon's tokens makes the cards look native to Alexa rather than like their own brand, which is the right trade for this audience; a startup deck will want more identity later.

## 6. The simulator frame

The Echo Show frame is the hero; the tool-call transcript is a slim rail beside it, not a second pane of equal weight. An honesty banner names the emulation and the model in use. A switch selects whose Echo it is ("Mom's Echo", "Malik's Echo"). Echo Dot mode hides cards entirely.

## 7. Spoken lines

Conversation design is design. `speakable.headline` is about 20 words or fewer and at most two sentences; `details` at most three; `options` at most five; a whole spoken turn stays under 30 seconds. The UX conformance test enforces the headline length with the speech-length estimate it already computes. The README and demo dialogue obey the same limit.

## 8. Acceptance checks

- Playwright snapshots of the five cards at 768×480, light and dark (`ROADMAP.md` item 27).
- Density: an inline card has at most three rows and one primary action.
- Contrast and focus order checked on the seven screens; every action has a voice equivalent through Alexa (`ARCHITECTURE.md` §5.14).
- The three hand-designed phone screens match this spec (`ROADMAP.md` item 28).
