# 07 · Checklists — phase gates, the per-unit loop, CHK ids, final list, report formats

## Contents
1. Phase gates 0–5 (with the intake questionnaire)
2. Per-unit build loop
3. CHK table
4. Final checklist (plan §9)
5. verify-report format
6. build-log format
7. Options workflow (temp frame → real design)

## 1. Phase gates 0–5

A phase starts only when the previous gate passed; after each gate update the `Durum` row in `docs/00-brief.md` (`Faz | Durum | Dosya | Tarih | Not`; Durum ∈ `bekliyor`, `sürüyor`, `tamam`, `istisna`).

**Phase 0 · intake** — `AskUserQuestion`, Turkish. First the precondition, then rounds of ≤ 4 questions in the order below. There is no round limit: when an answer leaves open something the theme needs to stay consistent (a page whose role is unclear, a feature that changes a shared Sub, two answers that conflict), ask a follow-up round before writing the brief.
- Precondition (its own question, before anything else): **theme name** — "Temanın adı ne olsun? (Marka adı olarak logoda, header/footer'da, telif satırında ve iletişim metinlerinde kullanılacak.)" Offer "Benim için 3 isim öner" as an option. From the answer derive: brief title, slug `^[a-z0-9-]+$` (fold İ→i, ı→i, ş→s, ğ→g, ü→u, ö→o, ç→c; spaces → `-`), suggested prefix letter (first letter, unless `get_app_state` shows a collision), plan file `plan-<P>-<slug>.md`, e-mail/domain examples (`destek@<slug>.com.tr`). Confirm the name in the brief; every brand placement on the canvas uses it (`02-contract.md` §11).
- Round 1: (1) inputs — screenshots (each with its viewport width) and/or live URL + paths; (2) sector and three tone adjectives; (3) interpretation strategy (aynı iskelet / yakın klon / serbest yorum) and prefix letter A–Z — check `get_app_state` / root frame names for a collision; (4) reference policy: look-only, no reference images, copy, logo or brand name on the canvas — confirm.
- Round 2: (5) pages in scope — `06-page-coverage.md` defaults pre-ticked (including the Contact page, which the reference often lacks), optional ones offered; (6) reference colours ("Referansın renkleri aynen aktarılsın mı?"): aynen aktar (the measured colours are locked and the schemes are built around them) · ana renkleri koru (brand colour and accent locked, the rest generated) · yeni palet (the reference only informs the mood). Skip it and record "yeni palet" when there is no reference or it has no usable colour (grey wireframe); (7) canvas file + devices (default 1440 / 390) and motion appetite (sade / orta / yoğun).
- Round 3: (8) number of colour schemes (ikas colorScheme; `11-color.md` §3F), with options shaped by answer (6): after "aynen aktar" offer "Referanstaki kadar (analyze sayar)" (recommended) · "Referanstakiler + 1 vurgu şeması" · "Tek şema"; otherwise "AI önersin, 2–4" (recommended) · 2 · 3 · 4. One line of context: the merchant picks one scheme per section in the editor. (9) ikas ready-made pages — for each group ask "ikas'ın hazır sayfaları mı, özel tasarım mı?": **üyelik** (LOGIN, REGISTER, FORGOT_PASSWORD, RECOVER_PASSWORD, CUSTOMER_EMAIL_VERIFICATION) and **hesap** (ACCOUNT, orders, order detail, addresses, FAVORITES). Explain the trade-off: hazır = rendered by ikas, no section to design, the port only binds logo/palette/labels with `update_ready_made_page_prop` and enables the group with `enable_ready_made_pages`; özel = designed on the canvas like any section (AuthForms, Account) and ported as code. Record the answer per group in the brief (06 §2a). Membership "özel" makes every membership and e-mail page custom and in scope, e-mail verification included; it is not optional. The Contact page is never ready-made in ikas and is always custom (06 Contact row).
- Round 4: (10) conditional features (06 §3c, multi-select "Bu mağazada hangileri olacak?"): bildirim (toast) · onay penceresi · adres penceresi · hesap menüsü (header'da açılır) · sadakat programı · çekiliş · marka sayfası · teknik özellik tablosu · kayıtta ek müşteri alanları · blog etiket ve yazar · ürün listesinde sütun seçimi. Record the answers in the brief; only the ticked ones are drawn. (11) where a cart line is edited ("Sepetteki ürünü düzenle nerede açılsın?"): ürün sayfası (default; the shopper leaves the cart) · QuickBuy (opens over the cart with the line's variant, options and quantity) · inside the cart drawer. Explain the trade-off in one line: the product page is the least work but takes the shopper away; QuickBuy and the drawer keep them in the cart.
- Not asked; the skill decides and records them in brief §6: **locale** is always `tr-TR` (rule 10). **Price format** is one example format used on every price layer (default `1.850 TL`); it is a placeholder, because in ikas the live format comes from the merchant's currency settings through `get*FormattedPrice` / `formatCurrency`. **Uppercase** is a type decision made in analyze from the reference and the tone, recorded per text style in `globals.md` §2a (`BÜYÜK` in the family cell) and shown with the plan §1 identity.
- Gate: `templates/00-brief.md` fully filled (no `…` left), the user says the brief is right; Durum row 0 → `tamam`.

**Phase 1 · analyze** — gate: `lint_plan.py --globals docs/referans/globals.md --components docs/referans/components.md` prints `LINT OK`; every value tagged `[ölçüldü]` or `[tahmini]`; inputs copied to `docs/referans/girdi/` and that folder listed in the project `.gitignore`.

**Phase 2 · plan** — gate: `lint_plan.py docs/pendev/plan-<P>-<slug>.md --globals docs/referans/globals.md` prints `LINT OK (n targets)`; WCAG contrast passes for every text/background pair (contract 2: ERROR); plan §1 (identity) and §6.2 (section list) shown to the user.

**Phase 3 · build** — gate per unit: the unit's CHK lines all `PASS` (or `WARN` allowed by §3), one screenshot taken, one build-log line appended. Phase gate: every unit in plan order (ds → subs → sections → pages → overlays → motion) has a build-log line.

**Phase 4 · verify** — gate: `docs/pendev/verify-report.md` written from `--js all`; every `FAIL` fixed or listed as an exception the user accepted in writing; manual checks (Turkish glyphs, contrast) done.

**Phase 5 · handoff** — gate: `build_manifest.py` exits 0 (no plan section or anim target missing on the canvas); `docs/port/port-manifest.{json,md}` and `globals-runbook.md` written; open questions listed to the user.

## 2. Per-unit build loop

A unit is one root pair (`@desktop` + `@mobile`), one Sub with its state frames, one overlay with its states, or the DS / pages / motion batch.

1. **Read** the unit's block in the plan (§6.0–§6.5) and the tail of `docs/pendev/build-log.md` (resume: re-read listed node ids, `05-pendev-pitfalls.md` §12).
2. **Placeholder:** `FindEmptySpace` in the right band → `Insert` the root with `placeholder: true`, final name and root metadata.
3. **Build** the whole tree in that `execute` (one call per root frame): every node named as in the plan tree, flat metadata, `textClass` on every text, anim ids also in `context`, a prop mark (`props a, b TEXT`, 02 §5a) on every Sub instance, override, state alternative or layerless prop and a data mark (`data <source>` / `code <name>`, 02 §5c) on image data, state alternatives and renamed code text in the same `Insert`, values only `$variables`. Polish with `Update` in a follow-up call if needed.
   DS unit: the first `Insert` that uses each `font-*` variable proves the family. A "Font family … is invalid" warning in that response means change the variable now and add the family to the deny list (`05-pendev-pitfalls.md` §4).
4. **Check:** `python3 ${CLAUDE_SKILL_DIR}/scripts/extract_targets.py <plan> --js section:<Key>` → run the printed read-only snippet with `execute`. (DS, Subs, pages: run `--js all` and read the relevant CHK lines.)
5. **Screenshot:** one `TakeScreenshot` of the finished unit (smallest meaningful node).
6. **Fix** every FAIL in place — never delete-and-rebuild; metadata fixes use `05-pendev-pitfalls.md` §2. Re-run step 4.
7. **Parity:** every layer added to `@desktop` (visible or hidden) also exists in `@mobile`, sized for 390; layout-changing states get `@mobile — <state>` frames (06 §3c "Both devices, always").
8. **Close:** `Update(root, {placeholder: false})`, append the build-log line (§6). Next unit.

## 3. CHK table

Emitted by `pendev_checks.js` as `CHK|<id>|PASS|FAIL|WARN|<n>|<detail≤200>`, closed by `SUMMARY|pass=..|fail=..|warn=..`. On a large canvas one `execute` can time out (`InternalError: interrupted`): split the run with `extract_targets.py … --checks <ids>` and run the node-walk checks (`hardcoded,textclass,clip,refassets`) as `--part 1/3`, `2/3`, `3/3`; add the counts. `n` = offending count (or `found/expected`). Contract 1 = legacy ornek canvas (37 variables, no `textClass`); contract 2 = all new projects.

| id | What | Pass rule (contract 2) | Contract 1 behaviour |
|---|---|---|---|
| `vars` | core variables | `GetVariables()` has all 41 core names; themed ones carry axes `device` and/or `mode` as in `02-contract.md` | expects the 37 ornek names |
| `hardcoded` | raw values | no node under `P/` roots has a literal `#hex` fill/stroke, numeric `fontSize`, literal `fontFamily` or non-zero numeric `cornerRadius` (allowlist in `02-contract.md` §3) | same rule |
| `sections` | section frames | every plan §6.2 Section key has `P/Section/<Key>@desktop` and `@mobile`, both `reusable: true` | same |
| `pages` | page composition | every plan §6.3 page exists at both devices; children are only `ref`s to `P/Section/*` of the same device | same |
| `overlays` | overlay frames | every plan overlay × listed state × device has a root `P/Overlay/<Name>@device — <state>` | same |
| `spacing` | spacing rule (`02-contract.md` §3b) | on every Page, in order: first section top `$space-page` (0 → WARN, transparent Header), each next top a `$space-*` token (`$space-section`, other tokens WARN), every bottom 0, Footer top `$space-section`; Section components: side padding `$space-page` or 0, grid rows gap `$space-grid`, wide column splits gap `$space-page` (WARN); before a section marked `overlap $size-overlap` the page ref has `clip: false` and a shortened height (§3c) | `WARN` instead of FAIL |
| `subfit` | Subs size from the instance (`02-contract.md` §1) | `WARN` when a non-text child of a Sub's `layout: "none"` frame has a fixed width of half the Sub or more (PriceRange rail, progress bar) | same |
| `temp` | options box (§7) | no top-level frame named `… (geçici)` other than the one `Öneriler (geçici)` container (FAIL); the container sits below every `P/` root (WARN) | same |
| `anim` | animation targets | set of ids from `metadata.anim` ∪ `context` regex over Section/Sub components and every Overlay root (a `resolveInstances: true` pass only while ids are missing) equals the plan's id set, both directions; no Section/Overlay root carries an id the plan gives another key (`foreign`); backdrop refs to other Sections are skipped (02 §5b) | regex `C-[A-Z]{2,}-\d\d` style (prefix-specific), same equality |
| `textclass` | text classification | 0 text nodes without `textClass`; `prop` has `prop`+`propType` (one of the 30); `data` has `source` | `WARN` with the unmarked count (ornek baseline ≈ 350); never FAIL |
| `clip` | clipped content | 0 nodes with `ctx.problems`, excluding descendants of layers named `*mask*`, `*track*`, `marquee`, `ticker`, `*pin*`, `*stage*`, `*curtain*` | same |
| `rootmeta` | root metadata | every `P/` root has `type`=slug, `role`, `ikas` (section/overlay/sub), `device` (section/page/overlay), `variant`=P, `contract`=2 | `contract` key not required |
| `bgprop` | section background prop | every Section root has `prop:"backgroundColor", propType:"COLOR"` | skipped → `WARN` "contract 1" |
| `parity` | desktop/mobile parity | every kebab-case layer name in `@desktop` also exists in `@mobile`, and every `@desktop — <state>` root has its `@mobile — <state>` twin. Exempt: wrappers `*-row`, `*-column`, `*-wrap`, `*-body`, `*-main`; states containing `hover`; the plan's `Yalnız masaüstü katmanlar` / `Yalnız masaüstü durumlar` lines (plandata `desktopOnly` / `desktopOnlyStates`; a listed layer exempts its subtree). Overlays without component roots compare their first common state pair | same |
| `props` | prop placement | every layer-type prop (TEXT, RICH_TEXT, IMAGE, IMAGE_LIST, VIDEO, SVG, SVG_LIST) a key's §6.2 tree places is found on that key's component roots (overlay: any state root) as `metadata.prop` or a context mark (02 §5a), with the same type; no mark names a prop the plan does not give that key (`not-in-plan`) | `WARN` |
| `data` | data and code text | every `{data:}` / `{code:}` of a key's tree is found on its roots (textClass + source / code, code also by layer name), inside a Sub named on the same tree line, or as a context mark (02 §5c); no mark names a source the plan does not give that key | `WARN` |
| `placeholder` | unfinished roots | no `P/` root has `placeholder: true` (during build: only the current unit may) | same |
| `refassets` | reference leakage | no image-fill `url` and no text content contains the reference host or brand name from the brief | same |
| `ds` | design-system frames | `P/DS/{Colors,Typography,Spacing,Icons,Motion,Imagery}` present (6/6) | 5/5, `Imagery` not required |
| `storefront` | cards, menu and search (`06-page-coverage.md` §3d) | `P/Sub/ProductCard` has `card-media`, `card-fav`, `card-swatches`, `card-cart`, `card-customize` and the states `renk seçili`, `ayrık varyant`, `kişiselleştirme`; every `card-fav` on the canvas (all Sub roots, Section components and Overlays, instances resolved) sits inside a `card-media` and in the **same corner** of it, whichever corner the design chose; QuickBuy has `renk karttan`, `kişiselleştirme` and `set ürün` at both devices, and its `set ürün` state has `qb-bundle`; the controls of each `qb-actions` / `pdp-actions` row (quantity, add, favourite) share one height; mobile MenuOverlay has `menu-mega-title` when a desktop layer is named `*mega*`; ProductList has `— arama` at both devices and `search-field` (in that state or the component). Popular searches and the all-products state are optional. Each part runs only when its key is in the plan | `WARN` |
| `radius` | radius roles (`02-contract.md` §3) | every product media layer (`card-media`, `pdp-media`, `pdp-thumb`, `qb-media`, `cline-media`, `offer-media`, `bundle-media`, `iprev-thumb`) on Sub roots, Section components and Overlays (instances resolved) has the same `cornerRadius`, else FAIL; the control Subs (Button, FormField, VariantChip, QuantitySelector) that set a radius share one value, else WARN; PASS with a note when neither is on the canvas | `WARN` |
| `dividers` | no row dividers (`08-quality.md` §8) | FAIL when a visible layer named `*divider*`, `*separator*`, `*hairline*` or `*rule` in a Section component, Sub or Overlay is not a structural edge named `*-edge`; WARN on thin unnamed lines (≤ 2 px, ≥ 24 px long) that are not underlines, indicators, progress, tracks, rails, bars or strikes. DS and temp frames are skipped | `WARN` instead of FAIL |

## 4. Final checklist (plan §9)

Design side — every item maps to a CHK or a manual check:
- [ ] `GetVariables()` contains all plan §3 variables; no hardcoded hex / font size / font family (`vars`, `hardcoded`).
- [ ] Every §6.2 section has reusable `@desktop` and `@mobile` roots (`sections`).
- [ ] Every §6.3 page consists only of Section instances (`pages`); every overlay state exists at both devices (`overlays`).
- [ ] Gaps follow the spacing rule (`spacing`): no section touches the Header or the Footer, no double gaps, page edges and column splits on one token; checked again on a full-resolution export of every page (manual).
- [ ] The **union** of `metadata.anim` and the `context` scan (plan §8 step 2) equals the §7 id list exactly (`anim`).
- [ ] Every text layer has `textClass`; `prop` texts carry `prop`+`propType`, `data` texts carry `source` (`textclass`).
- [ ] No clipped-content warning on any frame, masks and tracks excepted (`clip`).
- [ ] Turkish characters (`İ Ş Ğ Ü Ö Ç ı`) render correctly in every chosen font — screenshot of `P/DS/Typography` (manual).
- [ ] No reference images, copy or logo used; no fill URL from the reference host (`refassets` + manual look).
- [ ] `P/DS/Colors` shows the colour-scheme cards and `P/DS/Typography` the ikas text-style table with four breakpoints; `globals.md` §1a, §2a and §4a match them; §1b gives each scheme's colour rationale and sources (`11-color.md` §4).
- [ ] Every plan prop is on the canvas as metadata or a context mark, and no mark is stale (`props`).
- [ ] Every plan data source and code text is on the canvas, in a named Sub or as a context mark (`data`).
- [ ] Desktop/mobile parity (`parity`): every ikas block, account panel and confirmation exists in both device components; every desktop state frame has its mobile twin; intended desktop-only layers are declared in plandata `desktopOnly`.
- [ ] The theme name from the brief sits in every brand placement (`02-contract.md` §11): logo/mark in `P/DS/Icons`, Header and Footer logos, copyright, contact e-mail, legal/e-mail texts. No placeholder brand text (`Marka`, `Logo`, `Brand`) and no other brand name on the canvas.
- [ ] `P/DS/Imagery` exists with the generated photography direction (`ds`).
- [ ] Every text/background pair passes WCAG AA (`02-contract.md` §10; manual on the `P/DS/Colors` pairs).
- [ ] Every Section root carries the `backgroundColor` COLOR prop (`bgprop`); root metadata complete (`rootmeta`).
- [ ] No root left with `placeholder: true` (`placeholder`).
- [ ] Product card, QuickBuy, mobile menu, SearchOverlay and the search page carry the §3d layers and states (`storefront`); content revealed on hover is drawn open on `@mobile` (rule 14, manual).
- [ ] Every corner radius is a `$radius-*` role and product images have the same radius on card, product page, QuickBuy and cart (`radius`, `hardcoded`).
- [ ] No divider between rows or list items; the only lines are structural edges named `*-edge` (`dividers` + manual look at summaries, menus, filters and account panels).

Port side (done later by the port, listed so the handoff carries it): theme globals created and re-listed with `list_theme_globals`; every section passes `check` and `build`; every anim target `done: true`; the seed data of `seed-checklist.md` exists in the dev store and every behaviour criterion in `port-manifest.md` is ticked after a click-through, one page at a time (`10-port-behaviour.md`).

## 5. verify-report format

`docs/pendev/verify-report.md` (Turkish; skeleton in `templates/verify-report.md`):
1. Header: date, canvas file, plan path, prefix, contract, `--js all` run date.
2. `## CHK sonuçları` table `| CHK | Sonuç | n | Ayrıntı |` — one row per CHK line, copied verbatim, then the `SUMMARY|…` line quoted.
3. `## Elle kontroller` — Turkish glyph check, contrast pairs, reference look-through: each `geçti` / `kaldı` + note.
4. `## İstisnalar` table `| CHK | Node / kök | Gerekçe | Kullanıcı onayı |` — one line of reasoning each; empty table if none.
5. `## Ekran görüntüleri` — list of screenshots taken (unit, node id, what it shows).
6. `## Sonuç` — one sentence: ready for handoff or not.

## 6. build-log format

`docs/pendev/build-log.md` is append-only and lets a new session resume. Header once:

```
# Build log — <slug> (<P>, contract <n>)

| Kök | Node | CHK | Ekran görüntüsü |
|---|---|---|---|
```

Then one line per finished root frame: `| <root> | <nodeId> | <CHK summary> | <screenshot note> |`, e.g.
`| P/Section/Hero@desktop | 4kT9x | sections PASS · anim 8/8 · textclass 0 · clip 0 | masaüstü hero, başlık maskeleri doğru |`.
Fixes after the fact get a new line with the same root and `düzeltme:` in the note; never edit old lines.

## 7. Options workflow (temp frame → real design)

Use this whenever the user asks for options, alternatives, proposals, motion ideas, or "what else could we do". It applies in every phase, including revisions after verify.

**1. Open the temp frame inside the options box.** All temp frames live in one place, away from the real design:
- One top-level container `Öneriler (geçici)`: horizontal layout, `gap: 200`, no fill, in its own row **below every root** of the canvas (x 0, y = bottom of the lowest root + 2000). Create it on first use; afterwards find it by name and reuse it. Never create a second one.
- Each topic is a child frame `<Konu> önerileri (geçici)` of the container, never a root. Reuse the topic's frame when it exists; a new topic goes first: `Insert` into the container, then `Move(id, box, 0)` (newest leftmost).
- The topic frame's first child is a `topic-title` text: topic, date and option numbers (`Sepet · 2026-10-28 · 1–4`); update the numbers when options are added or transferred.
- Do not give these frames the `P/` prefix: nothing in them is a contract node. Use `fill: $color-surface`, vertical layout, `gap: 56`, `padding: 64`.
- CHK `temp` fails on a `(geçici)` frame outside the container and warns when the container is not below every root.

**2. Draw numbered options.** Each option is:
- an `opt-label`, holding an `opt-title` ("N · Ad") and an `opt-desc`. For motion the description gives values, duration and easing, implementation (`css-transition` / `animejs` / `io-hook` …), mobile behaviour and reduced motion; for layout it gives sizes and what changes.
- the option itself: a full-width mock of the block, or a `motion-row` of 2–3 `motion-frame`s. Each motion frame is a `motion-stage` (a scaled replica built from real canvas images) plus a `note` (start → middle → end).
- Start the block with one `opt-label` that says which options can be combined (e.g. one entrance + one hover).

**3. Do not touch the real design while options are open.**
- No plan ids, no anim metadata, no root metadata in the temp frame.
- No reference assets, no eyebrows (rule 11).

**4. Iterate in the temp frame.** When the user asks for more ideas, a change, or a combination ("1 ile 4 bir olsun"), add a new numbered option to the temp frame. Do not edit the real unit.

**5. Transfer only on a pick**, e.g. "N asıl tasarıma aktar", "bunu kullan", "sadece bu olsun":
1. Plan data first: tree, props, anims; a local `<P>-M-NN` recipe for new motion. Then `gen_plan.py` and `lint_plan.py` → `LINT OK`.
2. Canvas: build the option inside the real Section/Sub. Put anim ids in `metadata` at creation, or in `context`. Add a `— <state>` frame if the layout changes.
3. Motion frames: `Move` the option's `motion-frame`s from the temp frame into a new `P/Motion/<recipe> <Section>` root, which carries motion metadata and is placed in the Motion band. Update their notes to the real values. Add a legend note to `P/DS/Motion`.
4. Delete the transferred option's label and row from the topic frame and leave the other options. When the topic frame has no option left, delete it.
5. Run the unit checks (`--js section:<Key>`), then a full `--js all` when bands moved. Then append to the build-log and verify-report, and update `globals.md` / `components.md`.

**6. Delete temp frames only when the user says so.** Before `handoff`, ask once whether the remaining options should go; on yes, delete the whole `Öneriler (geçici)` container. Phase 5 does not start while the container still holds undecided options, unless the user lists them as open questions.

