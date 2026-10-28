# 02 — Canvas contract

The fixed agreement between the plan, the pen.dev canvas and the ikas port. Scripts (`gen_plan.py`, `lint_plan.py`, `pendev_checks.js`, `build_manifest.py`) and the downstream ikas port depend on these names; **do not rename anything in this file per project**. Only values change.

`P` below stands for the project's prefix letter (A–Z, chosen in intake, unique on the canvas). Contract 2 is the default for new projects; contract 1 is the legacy ornek form (37 variables, no `textClass`, no Imagery frame) and is only read, never produced.

## Contents

1. Canvas bands and layout
2. Naming ↔ code
3. Core variables (41) · 3b. Spacing system · 3c. Section overlap
4. Type-style mapping
5. Metadata schema
6. Tree notation
7. ID scheme
8. Design-system frames
9. Required subs, overlays and states
10. Contrast gate
11. Theme name and brand placements

---

## 1. Canvas bands and layout

Everything is a **separate root frame**. Root names follow a fixed pattern; the port reads the component list from them.

| Band (top → bottom) | Root frame name | Content | Size |
|---|---|---|---|
| 00 | `P/DS/Colors`, `P/DS/Typography`, `P/DS/Spacing`, `P/DS/Icons`, `P/DS/Motion`, `P/DS/Imagery` | design-system pages | free |
| 01 | `P/Sub/<Name>` (reusable) and `P/Sub/<Name> — <state>` | components and their states | by content |
| 02 | `P/Section/<Name>@desktop`, `P/Section/<Name>@mobile` (both reusable) | sections | 1440 / 390 wide |
| 03 | `P/Page/<Name>@desktop`, `P/Page/<Name>@mobile`; a plandata row with `expand` uses `P/Page/<Row> — <Name>@<device>` (e.g. `Auth — Login@desktop`) | pages (section instances only) | 1440 / 390 |
| 04 | `P/Overlay/<Name>@desktop — <state>`, `P/Overlay/<Name>@mobile — <state>` | menu, cart, search, panels | 1440×900 / 390×844 |
| 05 | `P/Motion/<recipe> <section>` | animation frames (start / mid / end) | by content |

Layout rules:
- One horizontal band per row; 800 between bands, 200 between frames. A section's desktop and mobile frames sit **side by side**. Place new roots with `FindEmptySpace`.
- Nothing loose at root level (no text, icon or shape). Explanations are `note` nodes beside the frame.
- No other root kinds. A piece used inside one section (gallery, buy box, list toolbar, facet filter) is a layer of that section's root, never a root of its own; `role: "block"` does not exist. A piece used by several sections or overlays is a Sub: `SearchField` (ProductList, SearchOverlay), `NewsletterForm` (Footer, Newsletter), `AddressForm` (Account, AddressModal), placed as an instance in each host.
- Desktop roots `theme: {device: "desktop"}`, mobile roots `theme: {device: "mobile"}`; a section that uses a non-default colour scheme adds `mode: "<scheme slug>"` (the default scheme needs none). Sized variables switch automatically; never type a mobile number.
- Section frames use `layout: "vertical"` or `"horizontal"` with `clip: true`. `layout: "none"` only for truly stacked layers (slides, image + gradient + text, hotspots).
- Everything repeated is a `ref` instance of a reusable (ProductCard, Button, ArrowLink…). Pages contain **only** section refs.
- A Sub sizes from its instance. A Sub placed at different widths (PriceRange in the filter column, the drawer and QuickBuy; progress and shipping bars; tab underlines; sliders) has no fixed inner width: rails and rows are `fill_container`, handles and markers are placed by layout (spacers with fill weights), never by absolute `x` inside a `layout: "none"` frame. CHK `subfit` warns on a fixed-width child (≥ 120 px) that spans half or more of its Sub inside a `layout: "none"` frame.
- The root being worked on has `placeholder: true`; remove it when the unit passes its checks.
- Values are variables, never numbers: colour, font, font size, spacing are all `$…` (exceptions: §3 "Allowed raw values").
- Reference imports on the canvas are for looking only: never copy layers from them, never edit or delete them.

## 2. Naming ↔ code

| pen.dev | ikas / code |
|---|---|
| Root `P/Section/HeroSlider@desktop` | section component **HeroSlider** (`src/components/HeroSlider/`) |
| Root `P/Sub/ProductCard` | sub-component **ProductCard** (`src/sub-components/ProductCard/`) |
| Root `P/Overlay/CartDrawer…` | sub-component of the section that opens it (usually Header) |
| Root `P/Page/Home@desktop` | ikas page (INDEX…) composed in the editor |
| Layer name `hero-title` (kebab-case) | CSS class `.hero-title` |
| `ref` instance name = component name (`ProductCard`) | JSX `<ProductCard />` |
| Text layer + `textClass:"prop"` + `prop` | TEXT prop (no literal text in JSX) |
| Text layer + `textClass:"data"` + `source` | storefront data binding (`product.name` …) |
| Text layer + `textClass:"code"` | string computed in code (counter, digits, separators) |
| Image-filled frame + `prop` | IMAGE / PRODUCT / CATEGORY prop |
| Repeated child group + `prop` | COMPONENT_LIST or `*_LIST` prop |
| Section root `prop:"backgroundColor"` | mandatory `backgroundColor` COLOR prop |
| `metadata.anim` (+ ids in `context`) | animation target in the plan's `anim-targets` |

## 3. Core variables (41)

Types: `color`, `string`, `number`. Axes: `mode: <scheme slugs>` (colours; 2–4 values, one per ikas colour scheme, the default first, each the ASCII-folded scheme name from `globals.md` §1a, e.g. `kagit | murekkep | kil`; `light | dark` stays valid; a single-scheme theme declares scalar colours; `11-color.md`) and `device: desktop | mobile` (sizes). Fonts and the scalar sizes marked "—" have no axis. Example values are the ornek plan-C values (light / dark, desktop / mobile); the four contract-2 additions show suggested values.

| # | Variable | Role | Type | Axis | Example | ikas destination |
|---|---|---|---|---|---|---|
| 1 | `color-bg` | page/section background | color | mode | `#EFEBE2` / `#0D0D0D` | colorScheme slot `Background` |
| 2 | `color-text` | primary text, icons | color | mode | `#0D0D0D` / `#EFEBE2` | slot `Text` |
| 3 | `color-muted` | secondary text, inactive labels | color | mode | `#6B675F` / `#8F8B82` | color `Muted` |
| 4 | `color-line` | borders, dividers | color | mode | `#0D0D0D` / `#EFEBE2` | color `Line` |
| 5 | `color-surface` | raised panels, fields, chips | color | mode | `#E3DED2` / `#1A1A1A` | color `Surface` |
| 6 | `color-inverse-bg` | filled button, hover fill | color | mode | `#0D0D0D` / `#EFEBE2` | slot `PrimaryButton/Background` |
| 7 | `color-inverse-text` | text on inverse fill | color | mode | `#EFEBE2` / `#0D0D0D` | slot `PrimaryButton/Text` |
| 8 | `color-accent` | the one accent (badge, ticker, focus) | color | mode | `#FF3B1F` / `#FF3B1F` | color `Accent` |
| 9 | `color-accent-text` | text on accent | color | mode | `#0D0D0D` / `#0D0D0D` | color `AccentText` |
| 10 | `color-scrim` | overlay backdrop (alpha) | color | mode | `#0D0D0D99` / `#0D0D0DB3` | `global.css` `--color-scrim` |
| 11 | `color-transparent` | gradient start stop (`#RRGGBB00` of bg) | color | mode | `#EFEBE200` / `#0D0D0D00` | `global.css` `--color-transparent` |
| 12 | `color-danger` | errors, field error message | color | mode | `#B3261E` / `#FF6B5E` | color `Danger` |
| 13 | `color-success` | confirmations, "eklendi" | color | mode | `#1E6B3A` / `#4CC27A` | color `Success` |
| 14 | `font-display` | display + h2–h4 | string | — | `Sofia Sans Extra Condensed` | typography `font_family` |
| 15 | `font-ui` | nav, buttons, titles, badges | string | — | `Archivo Narrow` | typography `font_family` |
| 16 | `font-body` | running text | string | — | `Archivo Narrow` | typography `font_family` |
| 17 | `font-price` | prices | string | — | `Archivo Narrow` | typography `font_family` |
| 18 | `font-mono` | labels, codes, counters | string | — | `Space Mono` | typography `font_family` |
| 19 | `text-display` | h1 / hero | number | device | 168 / 72 | typography `Display` |
| 20 | `text-h2` | section title | number | device | 112 / 52 | typography `H2` |
| 21 | `text-h3` | menu item, feature title | number | device | 64 / 40 | typography `H3` |
| 22 | `text-h4` | card / panel title | number | device | 36 / 26 | typography `H4` |
| 23 | `text-title` | product name | number | device | 22 / 18 | typography `Title` |
| 24 | `text-ui` | nav, button, link | number | device | 18 / 16 | typography `UI` |
| 25 | `text-ui-sm` | footer link, sub-label | number | device | 15 / 14 | typography `UISmall` |
| 26 | `text-badge` | badge text | number | device | 12 / 11 | typography `Badge` |
| 27 | `text-label` | category, date, breadcrumb | number | device | 12 / 11 | typography `Label` |
| 28 | `text-body` | running text | number | device | 16 / 15 | typography `Body` |
| 29 | `text-price` | price | number | device | 22 / 18 | typography `Price` |
| 30 | `space-page` | page side margin | number | device | 32 / 16 | `--space-page` |
| 31 | `space-grid` | gutter between cells | number | — or device | 0 | `--space-grid` |
| 32 | `space-card` | card inner padding | number | device | 12 / 10 | `--space-card` |
| 33 | `space-panel` | panel inner padding | number | device | 24 / 16 | `--space-panel` |
| 34 | `space-xs` | tight pairs (name ↔ price, title ↔ meta below) | number | device | 6 / 4 | `--space-xs` |
| 35 | `space-sm` | small gap | number | device | 12 / 10 | `--space-sm` |
| 36 | `space-md` | medium gap | number | device | 16 / 12 | `--space-md` |
| 37 | `space-section` | section vertical spacing | number | device | 120 / 64 | `--space-section` |
| 38 | `size-header` | header height | number | device | 96 / 88 | `--size-header` |
| 39 | `size-line` | line thickness | number | — | 2 | `--size-line` |
| 40 | `size-logo` | logo height | number | device | 28 / 22 | `--size-logo` (Header may expose a NUMBER prop) |
| 41 | `opacity-inactive` | inactive thumbnails/tabs | number | — | 0.3 | `--opacity-inactive` |

Rules:
- Every colour has a value for each declared mode, even when equal (accent). Theme-specific extras (e.g. `size-hero`) are allowed but go after the 41 and are listed in plan §3.
- With the `mode` axis, ikas gets one colour scheme per mode value (e.g. `Kağıt`, `Mürekkep`, `Kil`); the slots above are their slot names.
- Exact typography global names are set in the globals runbook (`09-handoff.md`); the column shows the default.

**Radius roles.** Corner radius is a design-system decision, not a per-layer one: the same kind of surface has the same radius everywhere, on every page and device. Every non-zero `cornerRadius` is a `$radius-*` variable (number, `—` axis or `device`), declared after the 41 and listed in plan §3; `globals-runbook.md` carries them to `global.css` as `--radius-*`.

| Variable | Used by | Required |
|---|---|---|
| `radius-control` | every control: Button, FormField, VariantChip, QuantitySelector, the favourite box beside add-to-cart, search and coupon fields, filter chips | yes, when any control is rounded |
| `radius-card` | cards, panels, overlay windows and sheets, OfferCard, BundleItem, ReviewCard, account panels | yes, when any card is rounded |
| `radius-media` | product images: `card-media`, `pdp-media`, `pdp-thumb`, `qb-media`, `cline-media`, `offer-media`, `bundle-media`, `iprev-thumb`. Without it they use `radius-card` | optional |
| `radius-pill` | fully rounded chips or buttons, when the design has them | optional |

- A theme with square corners declares none and uses `0`. A role is one value: a section never introduces its own radius (`08-quality.md` §3).
- **Product media share one radius.** The layers in the `radius-media` row are the same product image in different places; they all carry the same `cornerRadius` variable, so an image never looks rounder in QuickBuy than on the card or the product page. A selection ring on a thumbnail is a separate layer drawn on top of the image, never a border that shows the surface around it.
- Image files carry no corners: a generated or uploaded product image is a full-bleed rectangle with no baked radius, border or white margin; the corner comes only from the layer's `cornerRadius` (and from CSS in the port).
- CHK `hardcoded` flags a raw non-zero `cornerRadius`; CHK `radius` fails when the product media layers differ and warns when the control Subs differ.

**Allowed raw values** (everything else is a variable; `pendev_checks.js` CHK `hardcoded` flags raw fill/stroke/fontSize/fontFamily/cornerRadius):
- `#RRGGBBAA` gradient stops, where pen.dev will not take a variable in a stop. The RGB part must equal a core colour (`color-bg`, `color-text`, `color-scrim`).
- `0` (zero gap/padding, `opacity: 0` for stacked hidden siblings, radius 0).
- Structural `1` px hairlines (form-field border, `link-line`) when `size-line` is thicker.
- Geometry (width, height, x, y, rotation) is never tokenised.
- `opacity` equal to the `opacity-inactive` value: the canvas does not render a `$variable` on `opacity` (05 §15). Write the number and add `opacity: $opacity-inactive` to the node's `context` so the port uses the token.

## 3b. Spacing system

Every theme has its own spacing structure: a floating-band theme keeps its bands 20 / 8 from the edge and its content 80 / 16, a full-bleed theme has one edge. What is fixed is that the structure is **declared once and followed everywhere**, never guessed per section.

**Roles (fixed).** Each theme answers the same six questions in plandata `theme.json` → `spacing` (role → number variable). A role it leaves out uses the default.

| Role | Gap | Carried by | Default |
|---|---|---|---|
| `pageEdge` | the side inset of every band (section content, Header bar or capsule, Hero band, Footer, panels), both devices | each Section root's left/right padding; a full-bleed band has 0 and keeps its content inside | `space-page` |
| `headerGap` | Header → first section | the first section's top padding (0 only under a transparent Header state) | `space-page` |
| `sectionGap` | section → section | the **lower** section's top padding; every section's bottom padding is 0, so gaps never add up | `space-section` |
| `footerGap` | last section → Footer | the Footer root's top padding; the Footer root stays transparent and its colour sits on an inner band | `space-section` |
| `split` | column split: gallery ↔ buy box, filters ↔ grid, lines ↔ summary, account nav ↔ panel, form ↔ channels | the gap of the row that holds the columns | `space-page` |
| `grid` | card grid and rail | the gap of the grid row | `space-grid` |

**Tokens and values (the theme's).** A role may point at a core variable or at a theme extra declared after the 41 (e.g. `space-band`). The analyze phase records the system in `globals.md` §3 from the reference; the plan renders it in §3b. Values differ per device through the variable's device axis; never type a mobile number.

**Invariants (every theme):**
- Every gap is a variable; a raw number in a page seam is an error.
- One role, one token, everywhere: the mobile Header capsule sits at the same `pageEdge` as every other band.
- No section touches the Header or the Footer by accident; 0 only under a transparent Header or with the overlap convention (§3c).
- Gaps are carried on one side (top), so two sections never add their paddings.
- A section that needs a different top gap (a tighter strip under the Hero) uses another variable, and the plan's `**Desktop:**` / `**Mobil:**` line says why. On pages a section instance may override its top (first on one page, second on another); the master keeps `sectionGap`.

CHK `spacing` reads the plan §3b block: every Page in order (first section top, section → section, bottom 0, Footer top) and the side insets, column splits and grid gaps of Section components. `copy_library.py` writes the roles into the copied section skeletons. Confirm the seams on a full-resolution export of each page (05 §23a).

## 3c. Section overlap

A section that rides up over the one above it (category tiles over the Hero's bottom edge, a card row over a photo band) follows one convention, so the canvas shows it and the port can build it:

- **Prop:** the riding section has a BOOLEAN prop `overlapTop` (plan props line; default as designed). Off, it behaves like any section (§3b).
- **Amount:** one number variable, `size-overlap` (theme extra after the 41, device axis, listed in plan §3). The riding section's root `context` carries `overlap $size-overlap` (metadata cannot be added later, 05 §1).
- **Section frame:** drawn on its own, with its normal top padding. The section above keeps its content out of its bottom `size-overlap` (no dots, tabs or text there).
- **Pages:** the canvas has no negative margin. Shorten the **previous** section's ref on the page by `size-overlap` (`height` = its master height − the value) and set that ref's `clip: false`, so it runs under the riding section, which is drawn after it. Never move the riding section with `y`.
- **Port:** `margin-top: calc(-1 * var(--size-overlap))` and a higher `z-index` on the riding section while `overlapTop` is on; the section above adds nothing.
- CHK `spacing` reads the mark: on a page, the ref before a riding section must have `clip: false` and a fixed height, or it FAILs; the riding section's top may be any variable.

## 4. Type-style mapping

| Variables | Family | Weight | Line height | Case |
|---|---|---|---|---|
| `text-display`, `text-h2`, `text-h3`, `text-h4` | `$font-display` | theme (usually 700–900) | 0.9–1.0 | upper |
| `text-title`, `text-ui`, `text-ui-sm`, `text-badge` | `$font-ui` | 700 | 1.1 | upper |
| `text-label` | `$font-mono` | 400–700 | 1.1 | upper |
| `text-body` | `$font-body` | 500 | 1.35 | sentence |
| `text-price` | `$font-price` | 700 | 1.0–1.1 | as written (`1.850 TL`) |

Old price = `text-price` + `$color-muted` + strikethrough. Muted variants are not new styles: same preset + `$color-muted`. A plan may override weight/line-height per theme in plan §3; the variable names never change. Intermediate breakpoints (992–1199, 768–991) are not designed; they become component CSS `@media (max-width: bp(<id>))`.

## 5. Metadata schema

Flat keys only (no nested objects). Metadata can only be written **when the node is created**; instances and overrides drop it, so ids also go in `context`.

```js
// root frame
metadata: {type:"<slug>", role:"section", ikas:"HeroSlider", device:"desktop", variant:"P", contract:2,
           prop:"backgroundColor", propType:"COLOR"}            // prop/propType on section roots only
// role: "ds" | "sub" | "section" | "overlay" | "page" | "motion"

// state root "<root> — <state>": a frame around one ref of the root (a bare ref keeps no metadata, 05 §25)
metadata: {type:"<slug>", role:"sub", ikas:"ProductCard", state:"sepette"}   // + device on section/overlay states

// text bound to a prop
metadata: {type:"<slug>", role:"prop", textClass:"prop", prop:"title", propType:"TEXT"}
// text bound to storefront data
metadata: {type:"<slug>", textClass:"data", source:"product.name"}
// text produced by code
metadata: {type:"<slug>", textClass:"code", code:"slide-counter"}
// non-text layer bound to a prop
metadata: {type:"<slug>", role:"prop", prop:"image", propType:"IMAGE"}

// animated layer (prop/data keys may sit in the same object)
metadata: {type:"<slug>", role:"anim", anim:"P-HERO-02", recipe:"M-07", trigger:"state-change",
           textClass:"prop", prop:"title", propType:"TEXT"}
context: "P-HERO-02 · M-07 · başlık slaytla birlikte değişir"
```

- `role` precedence: `anim` > `prop`. Data/code text without animation carries no `role`.
- Contract 2: **every text node** has `textClass`; `prop` requires `prop` + `propType`; `data` requires `source`; `code` should name the routine in `code`. Text inside DS and Motion frames is `textClass:"code"`, `code:"ds"`.
- Multiple targets on one layer: `anim:"P-HERO-01,P-HERO-07"`.
- `context` is the human note **and** must contain every anim id of the layer.
- Metadata on a layer inside a reusable flows to its instances; do not re-write it per instance. Instance-level targets live only in `context`.

### 5c. Data and code marks in `context`

- **Sample product:** a container that shows one catalogue product (a ProductCard instance, a cart line, a PDP or QuickBuy root or state, an order line) carries `seed <key>` in its `context`, the key from plan §6.6. Everything inside it shows that product's name, brand, image, prices and option limits; CHK `seed` compares them with the catalogue, and cart totals anywhere with the computed cart.

Every `{data:<source>}` and `{code:<name>}` of a plan tree must be findable on the canvas. Any one of these counts:

1. **On the text node itself:** `textClass:"data"` + `source`, or `textClass:"code"` (+ `code:"<name>"`). A code text also matches by its layer name.
2. **Inside a Sub the same tree line names.** Example: `ProductCard ×8 · card-title {data:product.name}`, where ProductCard's own `card-title` carries `product.name`. Write the Sub name on the tree line (`Breadcrumbs`, `(VariantChip)`, `(ReviewCard)`); nothing is marked in the section.
3. **As a context mark** on the node the tree line names: one `·` segment, `data <source>[, <source>]` or `code <name>`. Use it where 1 and 2 cannot apply:
   - Image data, which has no `textClass`: `data product.image` on the media frame.
   - State alternatives: `data search.query` on a list title that shows the category name by default.
   - Composites: `data addressForm.fields` on a form.
   - Code text drawn under another name: `code index` on a counter.

CHK `data` checks all three. A context mark the plan does not know for that key fails as `not-in-plan`.

### 5b. Anim ids belong to one key; backdrop instances

- Every anim id has one owner: the Section/Overlay its plan target names, or a Sub for `CMP` ids. A Section or Overlay root never carries another key's id.
- Copying layers from another unit (e.g. QuickBuy variant swatches from ProductDetail) copies their `context` too. Re-key the ids to the target unit's own plan ids in the same call.
- A ref to another Section's component inside an Overlay or Section root is a **backdrop**, not content. Example: the Header drawn behind a megamenu or a search panel.
  - Name it after the section (`Header`). Never override anything inside it.
  - The tools skip it and everything inside it for anims, props and data.
- CHK `anim` fails a misplaced id as `foreign:<Key>><id>`.

### 5a. Prop marks in `context`

A prop whose text or image sits where metadata is not kept gets a **prop mark** in the `context` of the node that renders it. That covers:
- Sub instances: a button label, a FormField label or placeholder, a SectionHeading title.
- Descendant overrides.
- State alternatives of one layer: `addingText` next to `addToCartText`.
- Props without a visible layer: an `aria-label` on an icon button, an image `alt`.

Grammar: one `·`-separated segment of `context`, `prop <name> <TYPE>` or `props <a>, <b> <TYPE>[, <c> <TYPE>]`. An untyped name takes the next type.

```
context: "I-PDP-04 · M-11 · buton dolgusu ters döner · props addToCartText, addingText, addedText, outOfStockText TEXT"
context: "props closeAriaLabel TEXT"
```

- Put the mark on the node the plan tree line names: the ref, or the wrapper the line starts with.
  - Section: on the `@desktop` and the `@mobile` component.
  - Overlay: on every state root that contains the layer.
- Plain layers keep `metadata.prop`. The mark is for places metadata cannot reach, not a second copy.
- CHK `props` reads both:
  - Every layer-type prop the plan places in a key's tree must be found.
  - A marked name the plan does not know for that key fails as `not-in-plan`. Rename or remove a prop in plandata and on the canvas together.

**Starter `source` vocabulary** (format `group.field`, camelCase; extend with the same shape):

| Group | Sources |
|---|---|
| product | `product.name`, `product.brand`, `product.price`, `product.compareAtPrice`, `product.discountPercent`, `product.category`, `product.description`, `product.stockStatus`, `product.badge` |
| variant | `variant.name`, `variant.value`, `variant.sku`, `variant.stockCount` |
| cart | `cart.itemCount`, `cart.subtotal`, `cart.shipping`, `cart.total`, `cart.line.title`, `cart.line.variant`, `cart.line.quantity`, `cart.line.price` |
| order | `order.number`, `order.date`, `order.status`, `order.total`, `order.line.title` |
| customer | `customer.firstName`, `customer.lastName`, `customer.email`, `customer.address` |
| category | `category.name`, `category.productCount`, `category.path` |
| blog | `blog.title`, `blog.date`, `blog.author`, `blog.category`, `blog.summary` |
| search | `search.query`, `search.resultCount` |

## 6. Tree notation

Plan trees (plan §6.1–§6.2, `components.md`) annotate layers inline:

| Notation | Meaning | Metadata written |
|---|---|---|
| `{name:TYPE}` | prop `name` of ikas type `TYPE` (one of the 30) | `role:"prop", prop, propType` (+ `textClass:"prop"` on text) |
| `{data:source}` | storefront data field | `textClass:"data", source` |
| `{code:name}` | text computed in code | `textClass:"code", code` |

```
product-card
├─ card-images (clip)                {image:IMAGE} image-front + image-back
├─ card-badges                       {data:product.badge} text-badge
└─ card-info
    ├─ card-title                    {data:product.name} text-title
    ├─ price                         {data:product.price} text-price
    └─ card-count                    {code:card-index} font-mono "001"
hero-button (clip)                   {buttonText:TEXT}; top + bottom copy
```

Contract 2: `lint_plan.py` fails any quoted literal (`"SEARCH"`, `"01 / 03"`) on a tree line that has none of the three markers. Write `{searchText:TEXT}`, not `"SEARCH"`.

## 7. ID scheme

| Kind | Pattern | Example |
|---|---|---|
| Section/overlay target | `^P-[A-Z]{2,5}-\d\d$` | `P-HERO-01`, `P-PLP-06` |
| Sub (component) target | `^P-CMP-\d\d$` | `P-CMP-05` |
| Combined (lint) | `^P-(CMP\|[A-Z]{2,5})-\d\d$` | |
| Local recipe | `^P-M-\d\d$` | `P-M-01` |
| Catalogue recipe | `M-01` … `M-28` | `M-11` (`M-17` forbidden) |

- Each section gets a unique 2–5 letter code (`HDR`, `HERO`, `PLP`, `CRTP`); `CMP` is reserved for subs, numbered across all subs in §6.1 order.
- Numbers run 01… per section in plandata order. Once building has started, append new targets at the end so existing ids stay stable.
- Context scan regex: `/P-(?:CMP|[A-Z]{2,5})-\d\d/g` (local recipe ids like `P-M-01` do not match).

## 8. Design-system frames

| Root | Content |
|---|---|
| `P/DS/Colors` | swatch + name + hex for every colour variable, per mode; the contrast pairs of §10 rendered as text on fill with their ratio; **colour-scheme block**: one card per ikas colorScheme (e.g. light default, dark, transparent-over-image), each rendered in its own mode with a sample (heading, body, Button, Badge, muted price), the slot → token → hex table, and the sections that default to it (mirrors `globals.md` §1a) |
| `P/DS/Typography` | the 11 presets at desktop and mobile size, each with a Turkish sample line ("GÖLGE İÇİNDE ŞIK ÇÖZÜM 1.850 TL"); **ikas text-style table**: ikas style name, token, family · weight, size at ≥1200 / 992–1199 / 768–991 / <768, line height, letter spacing (mirrors `globals.md` §2a) |
| `P/DS/Spacing` | spacing scale bars; 1440 and 390 grid diagrams (margin, columns, gutter); line thickness |
| `P/DS/Icons` | every icon at 20×20 (search, account, cart, menu, close, arrow, caret, plus, minus, check) + logo and mark |
| `P/DS/Motion` | the legend: recipe ids used, one-line description, trigger symbol, as `note` nodes |
| `P/DS/Imagery` | (contract 2) art direction: 1–2 `Generate("ai"\|"stock")` samples per image role (hero, product on plain ground, lifestyle, category tile, blog), the aspect ratios used (3:4, 16:9 …), treatment notes (grain, frame, crop, colour temperature), logo/wordmark variants from `Generate("svg")` |

Contract 1 has five DS frames (no Imagery); `pendev_checks.js` CHK `ds` expects 5 or 6 by contract.

## 9. Required subs, overlays and states

Each sub is a reusable root; each state is its own root `P/Sub/<Name> — <state>`.

| Sub | States | When |
|---|---|---|
| `ProductCard` | varsayılan · hover · stok yok · indirimli · widths per grid; its cart button opens `QuickBuy` | always |
| `ProductCardSmall` | varsayılan · hover | search, cart, mini lists |
| `BlogCard` | varsayılan · hover | BLOG in scope |
| `Button` | varsayılan · hover · pasif · yükleniyor · **eklendi** · **stok yok** | always |
| `ArrowLink` | varsayılan · hover | always |
| `Badge` | one frame per type (YENİ · İNDİRİM · ÇOK SATAN …) | always |
| `Hotspot` | kapalı · açık | shoppable images |
| `Marquee` | — | any M-14 / ticker |
| `Breadcrumbs` | — | always |
| `Tabs` | aktif · pasif · hover | always |
| `VariantChip` | seçili · pasif · hover · stok yok | always |
| `FormField` | boş · dolu · odak · **hata (+ mesaj, `$color-danger`)** · pasif | always |
| `Checkbox` | işaretli · boş | always |
| `AccordionItem` | açık · kapalı | always |
| `QuantitySelector` | varsayılan · alt sınır · üst sınır | always |
| `SectionHeading` | açıklamalı · açıklamasız | always |
| `IconButton` | varsayılan · hover | always |
| `Spinner` | — | always |
| `CartLineItem` | varsayılan · güncelleniyor · **indirimli** · **hediye** · **set** · **kişiselleştirilmiş** · **adet sınırı** | always |
| `OfferCard` | seçili değil · seçili · sepette · tükendi | always (Birlikte al) |
| `BundleItem` | adet düzenlenebilir · adet sabit · tükendi | always (set ürün) |
| `RatingStars` | puanlı · yorumsuz | always |
| `ReviewCard` | doğrulanmış alıcı · doğrulanmamış · görselli · mağaza yanıtlı | always |
| `VariantSwatch` | varsayılan · seçili · hover · stok yok | always |
| `PriceRange` | varsayılan · değer girilmiş · sürükleniyor (labels follow the handle, the list has not changed yet) | always (price filter) |
| `SocialLoginButton` | Google · Facebook · hover | custom auth |
| `Skeleton` | — | always (loading states) |

Theme-specific subs (ornek: `Sticker`, `ScrambleText`) are added by the plan.

Required overlays (`P/Overlay/…`): mobile menu — açık; `CartDrawer` — boş · dolu · yükleniyor; `SearchOverlay` — boş · yazarken · sonuçsuz; **`FilterDrawer@mobile` — açık**; **`QuickBuy` — açık · seçim eksik · ekleniyor · set ürün** (`@desktop` centred window, `@mobile` bottom sheet; content in `06-page-coverage.md` §3a); plus any panel the plan defines (size guide, info drawer).

Required merchant blocks (`06-page-coverage.md` §3b, lint L21): ProductDetail layers `pdp-rating`, `pdp-campaign`, `pdp-offers`, `pdp-pay`, `pdp-bundle`, `pdp-tiers`, `pdp-options` (with every option type: `option-text`, `option-textarea`, `option-select`, `option-box`, `option-swatch`, `option-image`, `option-checkbox`, `option-color`, `option-date`, `option-file`, `option-child`, `option-limit`), `pdp-group`, `pdp-back-in-stock` (hidden ones get their own `— <state>` frames); a `ProductReviews` section; CartPage layers `cart-adjustments`, `coupon-applied`, `cart-recommendations`; CartDrawer layers `drawer-adjustments`, `coupon-toggle`, `drawer-recommend`.

Required storefront completeness (`06-page-coverage.md` §3c, lint L21): the overlays `CookieBar`, `ImagePreview`, `LocaleSwitcher` (Toast, ConfirmModal, AddressModal, AccountMenu are conditional, asked in intake); the sections `RichText` and `OrderTracking`; filter-type layers in ProductList; video, swatch and stock-location layers in ProductDetail; Header pager and sticky state; the Footer `locale-button`; social, SMS and consent layers in AuthForms; order-detail, return, settings and error panels in a custom Account.

## 10. Contrast gate

WCAG 2.1 ratios, computed on the variable values **in every declared mode**. `lint_plan.py` reports them; contract 2 fails on ERROR rows, contract 1 downgrades them to WARN.

| Pair (text on ground) | Min | Severity (c2) | If it fails, change |
|---|---|---|---|
| `color-text` on `color-bg` | 4.5 | ERROR | `color-text` |
| `color-muted` on `color-bg` | 4.5 | ERROR | `color-muted` (darker in light, lighter in dark) |
| `color-inverse-text` on `color-inverse-bg` | 4.5 | ERROR | `color-inverse-text` |
| `color-accent-text` on `color-accent` | 4.5 | ERROR | `color-accent-text` (swap to the other extreme first) |
| `color-danger` on `color-bg` | 4.5 | ERROR | `color-danger` |
| `color-text` on `color-surface` | 4.5 | WARN | `color-surface` |
| `color-muted` on `color-surface` | 4.5 | WARN | `color-surface`, then `color-muted` |
| `color-success` on `color-bg` | 3.0 | WARN | `color-success` |
| `color-line` on `color-bg` (non-text) | 3.0 | WARN | `color-line` |
| `color-accent` on `color-bg` (non-text) | 3.0 | WARN | `color-accent` only if it carries meaning alone |

Fix the foreground variable, keep hue, step lightness until it passes; never move `color-bg` to rescue one pair. Example: ornek muted light `#77736A` on `#EFEBE2` = 3.97 → `#6B675F` = 4.73.

## 11. Theme name and brand placements

The theme name is asked first in intake (07 §1 precondition) and recorded in `docs/00-brief.md` §2. It is the only brand name on the canvas. Every place below uses it exactly, with Turkish glyphs and the uppercase decision of its text style (`globals.md` §2a):

| Where | Layer / root | Port |
|---|---|---|
| Logo wordmark + mark | `P/DS/Icons` (`logo`, `logo-mark`), `Generate("svg")` with the exact name; check `İ Ş Ğ Ü Ö Ç` | `logo` SVG prop (Header, Footer, ready-made pages' logo scope) |
| Header (desktop, mobile, transparent state) and mobile menu | `logo` instance | Header `logo` SVG |
| Footer | `logo` instance + `copyright` (`© <yıl> <Tema adı>. Tüm hakları saklıdır.`) + about text if it names the brand | `logo` SVG · `copyrightText` TEXT |
| Contact, store and support texts | e-mail `destek@<slug>.com.tr`, store names (`<Tema adı> Kadıköy`), channel cards | TEXT props |
| Auth / account / e-mail verification copy that names the store | e.g. `<Tema adı> hesabına giriş yap` | TEXT props |
| Blog author, newsletter and campaign copy that names the store | `<Tema adı> Ekibi` | TEXT props / data |
| Plan §1 identity, DS frame titles | plan text, `P/DS/*` headers | — |

Never use placeholder brand text (`Marka`, `Logo`, `Brand`, `Store`), the reference's name, or a different name in copy. The slug and prefix follow from the name (lowercase ASCII slug; prefix letter = first letter unless taken). If the user renames the theme later: change the brief, regenerate the logo with `Generate("svg")`, update every placement above, and re-run `--js all`.

