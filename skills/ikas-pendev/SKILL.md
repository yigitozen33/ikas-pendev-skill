---
name: ikas-pendev
description: Designs a complete, port-ready ikas e-commerce theme on the pen.dev canvas from screenshots and/or a live reference URL. Runs six gated phases — intake, design-system analysis, generated build plan, section-by-section canvas build under a fixed DS/Sub/Section/Page/Overlay/Motion contract, verification, and a port handoff package for ikas Code Components — and stops before writing ikas code. Colour schemes come from the qrco MCP and the Huemint API when reachable. Use when the user says "ikas teması tasarla", "pen.dev'de tema", "ekran görüntüsünden tema", "bu siteden ikas teması çıkar", "referans siteyi analiz et", "tema planı üret", "bölümü pen.dev'de kur", "tasarımı doğrula", "port paketi", "$ikas-pendev", or "design an ikas theme in pen.dev", "screenshot to ikas theme" — even when they ask for only one phase (analysis, plan, one section, verify, handoff). Requires the pencil (pen.dev) MCP.
argument-hint: "[intake | analyze | plan | build <ds|subs|Section|pages|overlays|motion> | verify | handoff] [project-path]"
allowed-tools: Read, Grep, Glob, Write(docs/**), Edit(docs/**), Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/gen_plan.py *), Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/lint_plan.py *), Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/extract_targets.py *), Bash(python3 -I ${CLAUDE_SKILL_DIR}/scripts/analyze_site.py *), Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/build_manifest.py *), Bash(python3 -I ${CLAUDE_SKILL_DIR}/scripts/huemint.py *), Bash(python3 -I ${CLAUDE_SKILL_DIR}/scripts/sample_catalog.py *), mcp__qrco__*, mcp__pencil__read_skill, mcp__pencil__get_app_state, mcp__pencil__get_style
effort: high
---

# ikas-pendev — screenshot/URL → port-ready pen.dev theme for ikas

Turns a reference (screenshots and/or a live site) into an original ikas theme design on the pen.dev canvas, built so the port to ikas Code Components is mechanical. The contract in three sentences: **a root frame is an ikas component; a layer name is a CSS class; `metadata.prop` / `metadata.anim` / `metadata.textClass` tell the port what each layer is** (a prop, an animation target, data-bound text or code-generated text).

## Rules (read these even if nothing else survives compaction)

1. **Phase gate.** Phases run 0→5. Never start phase N unless phase N−1's output file exists and its gate passed. Each phase may run in a new session, so start by reading `docs/00-brief.md` and the previous phase's file.
2. **Source of truth, in order:** the user's brief and reference → the live `.pen` file (`GetVariables()`, existing components) → `docs/` → this skill's defaults. On conflict, stop and report; do not silently pick one. The canvas is multiplayer: re-read it, never recreate from memory.
3. **Read the official pen.dev skill** at the start of every build or verify session: `mcp__pencil__read_skill()`, then `pen-schema.md` and `execute.md`; `generate.md` before any `Generate`; `guide/components.md` before `build subs`. This skill never paraphrases the pen.dev API; `references/05-pendev-pitfalls.md` only adds what the official docs do not say.
4. **The contract is fixed** (`references/02-contract.md`). No invented frame names, metadata keys, variable names or ID formats. New projects use contract 2; `contract: 1` exists only to reproduce legacy plans.
5. **Metadata at creation.** Every node gets its final `name` and flat `metadata` in the `Insert` that creates it — pen.dev does not keep metadata added later. Every text node gets `textClass` (`prop` needs `prop`+`propType`; `data` needs `source`; `code` for counters/digits). Anim IDs inside components and instances also go into `context`, because instances and overrides drop metadata; so do props that live in instances, overrides, state alternatives or have no visible layer (`props a, b TEXT`, 02 §5a, CHK `props`); image data, state alternatives and renamed code text get `data <source>` / `code <name>` (02 §5c, CHK `data`). Corrections use the insert-at-index → delete → re-point recipe in 05 §2.
6. **Values only through `$variables`** (colour, font, size, spacing, radius). Radius is one role per kind of surface (`radius-control`, `radius-card`, `radius-media`; 02 §3), so a product image or a control has the same corners everywhere. The only raw values allowed are listed in 02 §3. Text always gets an explicit `fill`. Gaps between bands, sections and columns come from one spacing rule (02 §3b, CHK `spacing`): page edge and header → first section `space-page`, section → section and last section → Footer `space-section` on the lower one's top, column splits `space-page`, grids `space-grid`.
7. **ikas-portable constructs only** (`references/04-ikas-constraints.md`): the 30 prop types; Google Fonts with Turkish glyphs and weights the font ships; animations achievable with CSS, `IkasThemeSlider` or AnimeJS (no Lenis/GSAP); every Section has a `backgroundColor` COLOR prop; merchant-data props carry no default.
8. **No reference assets.** No image, copy, logo or brand name from the reference enters the design. Imagery comes from `Generate("ai"|"stock")`, logos from `Generate("svg")`. Reference imports on the canvas are look-only. Keep reference screenshots in `docs/referans/girdi/` and add that folder to the project `.gitignore`.
9. **Verify every unit.** `placeholder: true` while a root frame is being built. When a root pair is done: run `extract_targets.py --js section:<Key>`, execute the printed read-only checks, take one `TakeScreenshot`, fix in place, append to `docs/pendev/build-log.md`, then move on. Never delete-and-rebuild a frame to fix it.
10. **Language.** These instructions are English. Every generated document and every string on the canvas is Turkish (check `İ Ş Ğ Ü Ö Ç` render in the chosen fonts). Identifiers — frame, layer, prop, variable names, CHK ids — stay English. Measured values are tagged `[ölçüldü]`, estimates `[tahmini]`.
11. **No eyebrow labels above headings.** Never put a small label, kicker, index or category line directly above a title (`01 / YENİ GELENLER`, `04 / BÜLTEN`, `KOLEKSİYON · 24 ÜRÜN`, `HESAP`, a coordinate over a store name). Headings open the block on their own. This holds in every design, for every strategy, even when the reference uses them; data that belongs with content (blog category and date, price, badges on media) is not an eyebrow.
12. **Options go to a temp frame first.** Whenever the user asks for options, alternatives, proposals or "what else could we do" (seçenek, opsiyon, öneri, alternatif, "nasıl olur"), draw them as numbered options in a temporary frame (`<Konu> önerileri (geçici)`, no `P/` prefix) inside the single `Öneriler (geçici)` container below the whole design (newest topic first, CHK `temp`), and leave the real design untouched. Only the option the user picks is transferred into the real unit (plan data → plan → lint → canvas → checks → build-log), and that option is then removed from the temp frame; an emptied topic frame is deleted, and the container goes only when the user says so before handoff. Follow `references/07-checklists.md` §7.
13. **ikas blocks in the theme's style.** Everything ikas expects the theme to draw is built from the theme's Subs and tokens and matches its forms, spacing and type: merchant blocks, option-set fields, filters, account panels, overlays. This applies to every type and state (`references/06-page-coverage.md` §3b–§3c).
14. **Touch has no hover.** Content a desktop layout reveals on hover or by expanding (activity cards, collection tiles, image hover text) is drawn open on `@mobile`, and the whole card is the tap target. Controls that appear on hover (the card's favourite button) are always visible on touch.
15. **The storefront floor is not optional.** Product cards (interactive colour dots, the favourite button in one place on every card type and list, personalisation button, split-variant state), QuickBuy's carried-over colour, personalisation and set-contents states, the mobile menu's mega menu titles and the search page's own search field are drawn on every canvas (`references/06-page-coverage.md` §3d, CHK `storefront`), and no divider line separates rows or list items: spacing does, and a line only marks a structural edge named `*-edge` (a sticky bar's top, a group boundary in a small panel, an article's end; `references/08-quality.md` §8, CHK `dividers`). Product media share one radius and every control row shares one control language (`references/02-contract.md` §3, CHK `radius`). The handoff carries the matching behaviour criteria and seed data to the port (`references/10-port-behaviour.md`).

## Arguments

| `$ARGUMENTS` | Phase | Notes |
|---|---|---|
| *(none)* | resume | Read the `Durum` table in `docs/00-brief.md`; continue at the first unfinished phase. |
| `intake` | 0 | Questionnaire → `docs/00-brief.md`. |
| `analyze` | 1 | Reference → `docs/referans/globals.md` + `components.md`. |
| `plan` | 2 | `docs/pendev/plandata/` → `gen_plan.py` → `docs/pendev/plan-<P>-<slug>.md`. |
| `build <unit>` | 3 | `ds`, `subs`, a Section/Overlay key, `pages`, `overlays`, `motion`; `build` alone follows plan order. |
| `verify` | 4 | Whole-canvas checks → `docs/pendev/verify-report.md`. |
| `handoff` | 5 | `docs/port/` package. |

If the last argument is a path, it is the project root; otherwise use the working directory. The project is the ikas theme repo (or any folder with `docs/`).

## Phases

| # | Phase | Reads | Writes | Gate |
|---|---|---|---|---|
| 0 | intake | screenshots / URL / brief | `docs/00-brief.md` | user approves the brief |
| 1 | analyze | brief, inputs | `docs/referans/globals.md`, `components.md` | `lint_plan.py --globals … --components …` → `LINT OK` |
| 2 | plan | 1's outputs | `docs/pendev/plandata/`, `plan-<P>-<slug>.md` | `lint_plan.py plan.md --globals …` → `LINT OK`, contrast pass |
| 3 | build | plan, official pen.dev skill | canvas, `docs/pendev/build-log.md` | per-unit `CHK` all PASS |
| 4 | verify | canvas | `docs/pendev/verify-report.md` | `CHK` all PASS, or each FAIL has a written, user-accepted exception |
| 5 | handoff | plan, canvas dump | `docs/port/port-manifest.{json,md}`, `globals-runbook.md`, `seed-checklist.md` | `build_manifest.py` exit 0 |

### 0 · intake
**Precondition, asked first and alone: the theme name** ("Temanın adı ne olsun?"). It is the brand name and fixes the brief title, the slug (Turkish letters folded: `Örnek Outdoor` → `ornek-outdoor`), the suggested prefix letter and the plan file. On the canvas it goes into every brand placement of `references/02-contract.md` §11 (logo wordmark, header, footer, copyright, contact, legal and e-mail texts). If the user has no name yet, offer three original ones (never the reference's). Then ask in Turkish with `AskUserQuestion`, at most four questions per round and as many rounds as a consistent theme needs (details and order: `references/07-checklists.md` §1): inputs and the viewport width of each screenshot; sector and three tone adjectives; interpretation strategy (same skeleton / near clone / free interpretation) and prefix letter (check `get_app_state` for a collision with existing root frames); reference policy confirmation; pages in scope (defaults from `references/06-page-coverage.md` pre-ticked, Contact always in); whether the reference colours carry over (as-is / keep the main colours / new palette; skipped when the reference has none); canvas and devices (1440 / 390 default); motion appetite; the number of colour schemes, with options shaped by the reference-colour answer (`references/11-color.md` §3F); for the ikas ready-made page groups (membership: login/register/password/email verification; account: my account/orders/addresses/favorites) whether to keep ikas's ready-made pages or design them custom (06 §2a; membership "özel" makes every membership and e-mail page custom and in scope, e-mail verification included); which conditional features the store has (multi-select, only the ticked ones are drawn: toast, confirm modal, address modal, account menu, loyalty program, raffle, brand page, spec table, extra registration fields, blog tags and author, product list column picker; 06 §3c); where a cart line is edited (product page by default / QuickBuy / inside the cart drawer; 06 §3b). Locale, price format and uppercase are not asked; the skill decides them (07 §1). Fill `templates/00-brief.md` (theme name in the title and §2). Gate: the user says the brief is right.

### 1 · analyze
Follow `references/01-analysis.md`. URL mode: `python3 -I ${CLAUDE_SKILL_DIR}/scripts/analyze_site.py <url> --paths … --out docs/referans/analyze.md`, then read it; fall back to the Chrome snippet in 01 §3 for JS-rendered sites. Screenshot mode: vision only, every value `[tahmini]`. Hybrid: URL values win. Build the colour schemes with `references/11-color.md`: rationale first (sector psychology, area roles), then candidates from the qrco MCP and `python3 -I ${CLAUDE_SKILL_DIR}/scripts/huemint.py`, locked to the reference colours the brief keeps, then selection by fit, contrast and distinctness. Write `globals.md` (tokens with pen.dev variable name + ikas destination; colour schemes §1a with a source tag per value and the rationale §1b; motion catalogue) and `components.md` (page → section composition, anatomy trees with `{name:TYPE}` / `{data:}` / `{code:}`, states, mobile, prop tables) from `templates/`. Run the gate; fix every ERROR.

### 2 · plan
Write `docs/pendev/plandata/theme.json` and `sections/NN-<Key>.json` per `templates/plandata/README.md` (contract 2; the 41 core variables; every text literal in a tree line marked). Render with `python3 ${CLAUDE_SKILL_DIR}/scripts/gen_plan.py docs/pendev/plandata -o docs/pendev/`. Lint with `--globals docs/referans/globals.md`. Read the rendered §1 and §6.2 once as a designer: if a section reads as a generic template, change the data, not the prose. Write one sample catalogue in `theme.json` → `sampleCatalog` (products with name, brand, images, variant prices, tiers, option limits, and the sample cart); gen_plan validates it, computes the cart totals and renders plan §6.6. Show the user the §1 identity and the §6.2 section list before building.

### 3 · build
Order: `ds` → `subs` → each Section in plan §6.2 order (desktop then mobile) → `pages` → `overlays` → `motion`. Before the first `execute` of the session, read the official skill (rule 3) and `references/05-pendev-pitfalls.md`. One `execute` per root frame; build the tree in one `Insert` with all names and metadata, then `Update` for polish. After each unit: checks → screenshot → fix → build-log line (`| <root> | <nodeId> | <CHK summary> | <note> |`). Product data on the canvas (names, brands, images, prices, tiers, option limits, cart lines and totals) is copied from plan §6.6 only, never invented per section; every container that shows a product (card, cart line, PDP, QuickBuy) writes `seed <key>` in its `context` (CHK `seed`). `C-M`-style local recipes get their `P/Motion/…` frames in the `motion` step. The canvas is the user's file: every `mcp__pencil__execute` is a prompted action — batch sensibly, never spam.

### 4 · verify
`python3 ${CLAUDE_SKILL_DIR}/scripts/extract_targets.py <plan> --js all` → execute → paste the `CHK|…` lines into `templates/verify-report.md` (if the call times out, split it with `--checks` / `--part`, see 07 §3). Add the two manual checks (Turkish glyph screenshot of `P/DS/Typography`; contrast pairs from 02 §10). Every FAIL either gets fixed or a one-line reasoned exception the user accepts.

### 5 · handoff
`extract_targets.py <plan> --js manifest` → execute → save the `ROOT|…` lines to `docs/port/canvas-dump.txt` (large canvas: `--part 1/N` … `N/N`, concatenated). Run `python3 ${CLAUDE_SKILL_DIR}/scripts/build_manifest.py --plandata docs/pendev/plandata --plan <plan> --dump docs/port/canvas-dump.txt --globals docs/referans/globals.md -o docs/port/`. Read `references/09-handoff.md` §3 for the globals runbook the port will follow, and `references/10-port-behaviour.md` for the behaviour criteria (`port-manifest.md` → Davranış kabul kriterleri) and the seed data (`seed-checklist.md`) the port must create and click through, one page at a time. Before starting, ask whether the temp options frame (rule 12) can be deleted; undecided options either go or become open questions. The handoff ends with the open questions list, not with code.

## When to read which reference

| Situation | Read |
|---|---|
| Extracting tokens or inventory from a screenshot/URL | `references/01-analysis.md` |
| Naming anything, choosing variables, writing metadata, text classes, IDs | `references/02-contract.md` |
| Deciding layer structure for something that will move; writing anim-targets | `references/03-motion.md` |
| Unsure whether a construct ports (prop type, font, package, responsive) | `references/04-ikas-constraints.md` |
| About to execute on the canvas; something went wrong on the canvas | `references/05-pendev-pitfalls.md` (+ official `execute.md`) |
| Deciding which pages, overlays and states are in scope; product card, menu and search rules | `references/06-page-coverage.md` |
| Intake questions, per-unit loop, CHK ids, verify-report format, options in a temp frame | `references/07-checklists.md` |
| The design looks generic; writing Turkish copy; self-critique before "done" | `references/08-quality.md` |
| Producing the port package or planning theme globals | `references/09-handoff.md` |
| Behaviour the canvas cannot fix; seed data; how the port tests | `references/10-port-behaviour.md` |
| Choosing colour schemes: sources (qrco, Huemint), sector psychology, area roles | `references/11-color.md` |
| Writing plandata | `templates/plandata/README.md` |

## Checklist (copy into the conversation and tick)

```
ikas-pendev:
- [ ] 0 intake   docs/00-brief.md yazıldı ve onaylandı
- [ ] 1 analyze  globals.md + components.md · lint --globals/--components → LINT OK
- [ ] 2 plan     plandata/ → plan-<P>-<slug>.md · lint → LINT OK · kontrast geçti · §1 ve §6.2 kullanıcıya gösterildi
- [ ] 3 build    ds · subs · sections n/N · pages · overlays · motion  (her birim: CHK PASS + 1 ekran görüntüsü + build-log satırı)
- [ ] 4 verify   verify-report.md · CHK all PASS ya da gerekçeli istisna
- [ ] 5 handoff  port-manifest.json/.md + globals-runbook.md + seed-checklist.md · davranış kriterleri ve açık sorular listelendi
```

## Anti-patterns (the brief always wins; see `references/08-quality.md`)

Card around everything · gradients, shadows and large radii as defaults · centred hero + three feature cards · Inter/Roboto because nothing was chosen · emoji or hand-drawn icons · English or lorem filler and fake stats · every section at the same rhythm · a line under every heading and row (08 §8) · eyebrow/index labels above headings (never, rule 11). Spend boldness in one place per page and name it in plan §1.

## Reporting

Report in Turkish. After each phase: what was written (paths), gate result (quote the `LINT`/`SUMMARY` line), exceptions, and the next command. Never claim a check passed without its output line.
