# plandata schema (schema 1)

`plandata` is the single source for a design plan. `scripts/gen_plan.py` turns it into
`docs/pendev/plan-<P>-<slug>.md`; `lint_plan.py`, `extract_targets.py` and `build_manifest.py`
read the plan or the plandata, never a hand-edited copy. Edit plandata, then regenerate.

```
python3 scripts/gen_plan.py docs/pendev/plandata/            # writes docs/pendev/<theme.file>
python3 scripts/gen_plan.py plandata.json --stdout > plan.md   # summary line goes to stderr
python3 scripts/gen_plan.py docs/pendev/plandata/ --validate-only
```

Summary line: `<file> | lines N | targets N | sections N | overlays N | pages N`.
On a schema error, gen_plan exits 1 and prints one `<json-path>: <message>` per problem
(paths in a directory input name the file, e.g. `$.sections[2] (sections/03-Hero.json).anims[1].recipe`).

## Contents

- [Layout](#layout)
- [Top level](#top-level)
- [theme](#theme)
- [Variables](#variables)
- [Recipes and via](#recipes-and-via)
- [components](#components)
- [sections](#sections)
- [pages](#pages)
- [Contract 1 vs 2](#contract-1-vs-2)
- [Templates](#templates)
- [Minimal example](#minimal-example)

## Layout

Either form is accepted:

| Form | Files |
|---|---|
| Directory (default in projects) | `plandata/theme.json` (everything except sections) + `plandata/sections/NN-<Key>.json` (one section or overlay object per file; file-name order = plan order; `<Key>` must equal `key`) |
| Single file | one JSON object with `sections` inlined (used by `examples/ornek/plandata.json`) |

Default output directory: the parent of a plandata directory, or the directory of a single JSON file. Override with `-o`.

Any long text field (`identity_md`, `tree`, `desktop`, `mobile`, `props`, `structure`, `states`) may be a string or an array of lines. `tree` must be an array of lines.

## Top level

| Key | Type | Req. | Notes |
|---|---|---|---|
| `schema` | `1` | yes | |
| `contract` | `1` \| `2` | yes | 1 = Örnek legacy (byte-exact), 2 = all new projects |
| `contextScan` | bool | no (default `true`) | contract 1 only: render the `context` scan in §8 step 2 and the union wording in §9. Contract 2 always renders it |
| `theme` | object | yes | see below |
| `identity_md` | string \| lines | yes | §1 body, Markdown (Turkish) |
| `modes` | `null` \| `[default, …]` | yes | 2–4 colour-scheme slugs, default first, the ASCII-folded names of `globals.md` §1a (e.g. `["kagit","murekkep","kil"]`; `["light","dark"]` stays valid); `null` = single palette |
| `devices` | object | yes | `{"desktop":{"width":1440,"height":900},"mobile":{"width":390,"height":844}}` (height = overlay frame height) |
| `variables` | object | yes | see [Variables](#variables) |
| `typeStyles` | object | yes | `{"map":[{"styles":["text-display",…],"spec":"`$font-display`, satır 0.9–1.0"}…],"note":"…"}`; rendered as the §3 type mapping sentence |
| `fontCheck` | object | yes | `{"valid":[…],"invalid":[…]}` families tested in pen.dev. Contract 2 rejects a font variable listed in `invalid` |
| `ds` | object | yes | `sampleText` (Turkish glyph sample), `icons` (comma list), `imagery` (optional, contract 2 `DS/Imagery` row) |
| `recipes.local` | object | no | theme-specific motion recipes, see below |
| `stateHints` | object | no | `{recipeId: "frame → frame → frame"}` adds/overrides §6.5 Motion States hints |
| `via` | object | no | `{layer: SubComponent}`: targets on this layer are implemented inside that sub-component |
| `viaRules` | array | no | `[{"recipe":"M-11","layerContains":"button","via":"Button"}]` fallback when `via` has no entry |
| `utils` | object | no | `viaComponents` (list for the §8 via row; default = unique `via` values) and `extra` rows `[{part,path,targets}]` for the §8 util table |
| `components` | array | yes | §6.1 |
| `sections` | array | yes | §6.2 (inline form only) |
| `pages` | array | yes | §6.3 |
| `spacing` | object | no (contract 2) | the theme's spacing system, role → number variable name without `$`: `pageEdge`, `headerGap`, `sectionGap`, `footerGap`, `split`, `grid` (`02-contract.md` §3b). A role left out uses the default (`space-page`, `space-page`, `space-section`, `space-section`, `space-page`, `space-grid`); a token must exist in `variables.numbers` (theme extras such as `space-band` included). gen_plan renders plan §3b with the block CHK `spacing` reads |
| `sampleCatalog` | object | contract 2 | the one sample catalogue the canvas shows: `currency`, `products[]` (`key`, `name`, `brand`, `images[]`, `variants[]` {`name`, `price`, `compare`?}, `tiers[]` {`qty`, `price`}?, `options[]` {`name`, `type`, `limit`?}?) and `cart` {`lines[]` {`product`, `variant`, `qty`}, `campaigns[]` {`label`, `amount`}?, `coupon` {`code`, `amount`}?, `shipping`?}. Validated by `scripts/sample_catalog.py`; gen_plan computes the cart totals and renders §6.6 with the block CHK `seed` reads; `seed-checklist.md` lists the same data |

## theme

| Key | Req. | Example | Used in |
|---|---|---|---|
| `slug` | yes | `ornek` | `metadata.type` (kebab-case) |
| `name`, `sector` | yes | `Örnek`, `streetwear` | header line |
| `prefix` | yes | `C` | one letter A–Z; root frame prefix and anim ids `C-HERO-01` |
| `file` | no | `plan-C-serbest-yorum.md` | default `plan-<prefix>-<slug>.md` |
| `title`, `lead` | yes | | H1 and lead paragraph |
| `reference.url` | no | `https://referans.example/` | header line (omitted when empty) |
| `reference.canvasImportNote` | no | | §0 sentence about imported reference frames |
| `reference.policy` | no | | contract 2 §9 `CHK refassets` line |
| `penFile` | yes | `ornek-C.pen` | §0 |
| `codeDir` | yes | `ornek/src/` | §8 step 3 |
| `locale`, `currency` | c2 | `tr-TR`, `TRY` | contract 2 header line |

## Variables

`variables` = `{intro?, colors, fonts, type, numbers}`. Object key order is render order.

| Group | Value shape | Core names (fixed, must all exist) |
|---|---|---|
| `colors` | `"#RRGGBB[AA]"`, or one value per mode (same order as `modes`) when `modes` is set | `color-bg, color-text, color-muted, color-line, color-surface, color-inverse-bg, color-inverse-text, color-accent, color-accent-text, color-scrim` + c2: `color-transparent` (`#RRGGBB00`), `color-danger`, `color-success` |
| `fonts` | family name | `font-display, font-ui, font-body, font-price, font-mono` |
| `type` | `[desktop, mobile]` | `text-display, text-h2, text-h3, text-h4, text-title, text-ui, text-ui-sm, text-badge, text-label, text-body, text-price` |
| `numbers` | number or `[desktop, mobile]` (equal pair renders as one value) | `space-page, space-grid, space-card, space-panel, space-xs, space-sm, space-md, space-section, size-header, size-line, opacity-inactive` + c2: `size-logo` (must be `[desktop, mobile]`); radius roles `radius-control`, `radius-card`, optional `radius-media`, `radius-pill` (02 §3) |

Contract 1 = 37 core variables, contract 2 = 41. Extra variables are allowed and rendered. `intro` replaces the default §3 sentence.

## Recipes and via

Catalogue recipes `M-01…M-28` come from `scripts/data/motion-catalogue.json` (defaults for `frm, to, timing, impl, mobile, rm`, plus `name` and optional `stateHint`). `M-17` is forbidden.

`recipes.local` entries are keyed `<P>-M-NN` and need `name, what, struct, frm, to, timing, impl, mobile, rm` (+ optional `stateHint`). They render the §5.1 table and are sorted after catalogue recipes in §6.5/§7.

`impl` containing `gsap`, `lenis` or `framer-motion` is an error anywhere.

## components

```json
{"name": "Button", "structure": "`button` (clip) içinde `top` + `bottom` kopya …",
 "states": "varsayılan · hover · pasif · yükleniyor · eklendi · stok yok",
 "anims": [{"layer": "button", "recipe": "M-11", "trigger": "hover", "what": "Dolgu alttan kayar"}]}
```

Component targets get ids `<P>-CMP-NN` (numbered across all components) and section `Sub/<name>`. Each `layer` must appear in `structure` (word boundary: `link` does not match `link-line`).

## sections

```json
{"key": "HeroSplit", "code": "HERO", "kind": "section", "pages": "Ana sayfa",
 "ikas": "hero-slider-section (uyarlanır)", "props": "`title` TEXT · `backgroundColor` COLOR",
 "mode": "dark", "devices": ["desktop", "mobile"],
 "desktop": "1440 × 760 …", "mobile": "390 × 460 …",
 "tree": ["hero-split", "├─ hero-title    {title:TEXT} text-display"],
 "checks": ["başlık kabı sabit genişlikte"],
 "anims": [{"layer": "hero-title", "recipe": "M-03", "trigger": "load", "what": "Başlık açılır",
            "timing": "{ spring: spring-text }"}]}
```

| Key | Req. | Notes |
|---|---|---|
| `key` | yes | PascalCase, unique; root frames `P/Section/<key>@desktop` |
| `code` | yes | 2–5 capitals, unique, not `CMP`; anim ids `<P>-<code>-NN` |
| `kind` | yes | `section` \| `overlay` |
| `pages`, `ikas`, `desktop`, `mobile` | yes | prose |
| `props` | c2 sections | must mention `backgroundColor` in contract 2 |
| `mode` | no | one of `modes`; rendered (`- **Mod:**`) in contract 2 only |
| `devices` | no | overlays: which `@desktop`/`@mobile` frames exist (default both); used by the contract 2 §6.4 list |
| `tree` | yes | lines; notation `{name:TYPE}` (TYPE ∈ 30 ikas prop types), c2 also `{data:source}` (`product.name`) and `{code:name}` |
| `checks` | no | rendered as `Kontrol: a · b` |
| `desktopOnly` | no | kebab-case layer names drawn only in `@desktop` by design (nav, filter sidebar, hover labels, desktop gallery arrows); rendered as `- **Yalnız masaüstü katmanlar:**` and exempted by CHK `parity` (with their subtree) |
| `desktopOnlyStates` | no | state names that exist only as `@desktop — <state>` (states containing `hover` are exempt anyway); rendered as `- **Yalnız masaüstü durumlar:**` |
| `anims` | no | objects `{layer, recipe, trigger, what}` + optional overrides `frm, to, timing, impl, mobile, rm, via`; the compact array form `[layer, recipe, trigger, what, {overrides}]` is also accepted. `layer` must appear in `tree` (word boundary). `via` override `""` disables via |

## pages

```json
{"name": "Auth (×4)", "sections": "Header · AuthForms · Footer", "pageType": "LOGIN",
 "expand": [{"name": "Login", "pageType": "LOGIN"}, {"name": "Register", "pageType": "REGISTER"}]}
```

`sections` is a `·`-separated list; parenthetical notes (`Manifesto (koyu)`, `Footer (+ AnchorNav sabit)`) are ignored for checking, and every remaining token must be a `kind: section` key. `pageType` ∈ `INDEX, CATEGORY, PRODUCT_DETAIL, CART, ACCOUNT, LOGIN, REGISTER, FORGOT_PASSWORD, RECOVER_PASSWORD, NOT_FOUND, BLOG, BLOG_POST, SEARCH, FAVORITES, CUSTOMER_EMAIL_VERIFICATION, COLLECTION, CUSTOM` (required in contract 2). `expand` lists the page frames one row stands for; the summary `pages` count is the sum of `expand` lengths (or 1).

## Contract 1 vs 2

| | Contract 1 (Örnek legacy) | Contract 2 (new projects) |
|---|---|---|
| Marker | none (byte-exact with the Örnek plans) | `<!-- ikas-pendev contract:2 -->` on line 2, right after the H1 |
| Variables | 37 | 41 (`color-transparent`, `size-logo`, `color-danger`, `color-success`) |
| §4 | prop metadata | + `textClass` (`prop`/`data`/`code`), `source`, root `contract:2` + `backgroundColor` prop, `context` must carry anim ids, `{data:}`/`{code:}` legend |
| §6.0 | 5 DS frames | + `P/DS/Imagery` |
| §6.1 | | required: Button states `eklendi`, `stok yok`; overlays `FilterDrawer` (mobile) and `QuickBuy` (both devices); if `ProductDetail` / `CartPage` / `CartDrawer` exist, the merchant-block layers of 06-page-coverage §3b, a `ProductReviews` section and the subs `OfferCard`, `BundleItem`, `RatingStars`, `ReviewCard` (lint L21) |
| §6.3 | 2 columns | + ikas page type column |
| §9 | prose checklist | one line per CHK id: vars, hardcoded, sections, pages, overlays, anim, textclass, clip, rootmeta, bgprop, placeholder, refassets, ds |
| YAML `what:` | `"%s"` | JSON-escaped string |
| Extra validation | | font not in `fontCheck.invalid`; `{x:TYPE}` types; `{data:}` source shape; header shows locale/currency |

Contract 2 data that lacks the `FilterDrawer` or `QuickBuy` overlay or the Button states fails validation on purpose (the bare skeleton in this folder does).

## Templates

Prose lives in `templates/plan/*.md` (Turkish). Each file is one block of the plan; its last newline is dropped when loaded. Syntax: `{{name}}` value, `{{#name}}…{{/name}}` if truthy, `{{^name}}…{{/name}}` if falsy; a line holding only a section tag disappears with its newline. Context keys include `prefix, slug, name, file, penFile, codeDir, c1, c2, modes, mode_axis, mode_rule, dw, dh, mw, mh, contextScan, policy`. An unknown placeholder is an error. Change wording there, not in the script; then rerun `tests/run.sh` (the Örnek plan-C hash must still match for contract 1).

## Minimal example

`theme.json` + `sections/00-Example.json` in this folder are a fill-in skeleton (contract 2, Turkish placeholder text). A complete, valid contract 2 dataset is `tests/fixtures/mini-plandata/` (2 sections, 1 overlay, 2 pages, 41 variables, `{data:}`/`{code:}` notation). The full Örnek plan C (contract 1, 31 sections, 3 overlays, 16 pages, 115 targets) is `examples/ornek/plandata.json`.
