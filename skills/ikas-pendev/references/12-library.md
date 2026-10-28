# 12 · E-commerce structure library — design note

Status: **experimental** (branch `ecommerce-library`). Wired into SKILL.md: analyze writes `globals.md` §0 and runs `axes.py check`, plan runs `axes.py record`, build starts with `copy_library.py`.

## Contents
1. Principle
2. pen.dev import test
3. Library as a template, not an import
4. What the library gives, what each theme decides
5. Skeleton rules
6. Structural choices per theme
7. Similarity gate
8. Next steps

## 1. Principle

**Share the skeleton, never the look.** No two themes may resemble each other. The library makes every theme complete (no missing part, state or port mark); it never makes two themes alike.

Changing colour, font, spacing or corner radius alone is cosmetic: two themes that differ only there still read as the same theme. Themes must differ in structure: section layout, hero archetype, card anatomy, navigation pattern, grid, image ratio. A theme still has to read as a shop, so the prototypical parts stay recognisable: logo, navigation, cart, search, product grid, and gallery + buy box on the product page. Differentiation comes from the axes that do not define that prototype.

## 2. pen.dev import test *(observed)*

Test setup: a library file with two reusable components (a button and a cart line with a slot), flat `metadata` (`prop`, `anim`, `textClass`), `context`, and two-scheme colour variables. A theme file used them in two ways.

**Live import** (`imports: {lib: "lib.pen"}`, instances `ref: "lib:<id>"`, variables `$lib:<name>`):

| Result | Observation |
|---|---|
| works | Metadata and `context` reach every descendant, nested instances included, when read with `resolveInstances: true`. |
| works | Instance overrides: content, fill, replacing a slot frame with a local frame. Metadata on the new local frame persists. |
| blocks | Imported variables are read-only in the theme file: `Cannot change 'lib:radius-btn', because it's an imported variable`. The theme cannot give the library tokens its own values. |
| blocks | The library's theme axis arrives as a separate axis `lib:mode`. Setting the theme's own `mode` on an instance does not switch library colours. |
| blocks | A library component bound to a variable the library does not define is stored as `#000000`; it is not bound late by the importing file. |
| caution | Inserting into a slot inside an imported instance fails; only replacing the whole slot works. One `execute` lost the editor connection after the file was reopened. |
| caution | A metadata write on an instance descendant is not persisted (05 §1, §3). Metadata is inherited from the master only. |

**Copy** (a script copies the reusable nodes and variable names from the library JSON into the theme file, and the theme writes its own values): metadata, `context` and node ids stay intact; the same skeleton renders with a different palette, radius and scheme names; scheme switching works; the theme may change the structure of its own copy.

## 3. Library as a template, not an import

Because of §2, `ikas-ecommerce.lib.pen` is never imported live. It is a template that the build phase copies from, once per theme:

1. Copy only the components the theme's pages need.
2. Copy the token **names**. Their values come from the theme's own `globals.md` (§1a colour schemes, §2a type styles, spacing, radius). The library holds no colour, font or size value of its own.
3. Rebuild each copied component from the theme's reference and brief (§5). The copy supplies layer names, metadata, slots and state frames, not the drawing.

After the copy the theme owns everything. Library fixes do not flow into existing themes; that is intended, since flowing changes would pull themes back toward each other.

## 4. What the library gives, what each theme decides

| Library (same in every theme) | Theme (decided from zero every time) |
|---|---|
| The parts of each component (cart line: image, name, variant, price, quantity − / +, remove) | Order and placement of the parts |
| The states (empty, loading, error, out of stock, on sale, …) | Proportions: image ratio, column count, widths |
| Port marks: layer names, `metadata.prop` / `anim` / `textClass`, slots | Density, spacing rhythm, type scale |
| Evidence-backed must-haves (visible size buttons, − / + quantity, total cost near the CTA, …) | Hero archetype, card anatomy, navigation pattern, grid |
| | Colour schemes, fonts, radius, elevation, motion |

## 5. Skeleton rules

- Components are grey anatomy frames: neutral fill, one placeholder font, no shadow, no radius.
- Every size, gap, padding, radius, colour and font is a token reference. A literal value in a library component is a lint error.
- Layout is the minimum that keeps the parts visible (a vertical stack in anatomy order). It is not a layout proposal, and the build must not keep it unless the theme's own choice (§6) is the same.
- Section roots carry the spacing roles as padding (`02-contract.md` §3b), with the default tokens in the library: sides `pageEdge`; Header top 0; Hero families top `headerGap`; every other section top `sectionGap` and bottom 0; Footer top `footerGap`. `copy_library.py` swaps in the tokens the theme's plandata `spacing` names.
- Each component carries its parts list and states as named child frames, so the build can check completeness by name.
- No library component has a "default variant" of a structural axis. Every default pulls themes toward the median.

## 6. Structural choices per theme

The analyze phase records one value per axis field in `globals.md` §0 "Yapısal kimlik", from the reference measurement and the brief's interpretation strategy, with a one-line reason. The vocabulary is `library/axes.json`; the library and the template offer no defaults.

**Structural axes (A):**
1. Section layout variants (hero, featured collection, …)
2. Grid and columns (desktop / mobile columns, gutter, container width)
3. Navigation pattern (header layout, mega menu, behaviour on scroll, announcement)
4. Hero archetype (layout, height, text over or beside the image)
5. Product card anatomy (info position, price line, hover image, quick add, badge, swatch, card shell)
6. Image ratio and treatment (product ratio, hero ratio, crop, treatment)

**Token axes (B):** typography pairing · type scale · case and tracking · corner radius · line vs surface vs elevation · colour strategy · density and spacing · iconography · motion personality.

The value ranges for each axis are proposals and are not calibrated yet; the first themes calibrate them.

## 7. Similarity gate

`scripts/axes.py check` compares the new theme's §0 with every earlier theme's (rule id L23); `axes.py record` stores a theme once its plan gate passed. An axis differs when any of its fields differs.

- **Fingerprint store:** the axis choices of earlier themes live on the user's machine, outside this public repo (default `~/.claude/ikas-pendev/fingerprints.json`, override `--store` or `IKAS_PENDEV_FINGERPRINTS`): slugs, dates and axis values only. They are never committed.
- **Minimum difference (proposal):** the new theme differs from each earlier theme in at least 4 of the 6 structural axes (a mirrored layout counts as the same) and in at least 5 of the 9 token axes. One of the token differences is in typography and one is in colour strategy, not just hue.
- **Generic-default warning (proposal):** warn when 3 or more axes sit on the median value (centred full-bleed hero with one button, 4-column grid of square cards with centred name and price, pill "Shop now" button, uniform section padding, trust-badge icon row, rounded corners everywhere).
- **Layout fingerprint:** every plandata section carries `archetype: "<family>:<variant>"`. The home page's sequence (Header and Footer left out) must have a normalised edit distance of at least 0.5 to every earlier theme's, so two themes with the same section order and the same section types fail even when every axis differs. `axes.py check --plandata` in the plan phase.
- **Picture check:** `axes.py shot` (verify phase) reads a PNG export of the home page's desktop root. It takes the first viewport (16:10 of the width), turns it grey, averages it into a 24×25 grid and marks the cells whose edge is stronger than the median. The fingerprint ignores polarity, so a light and a dark version of one layout look alike while two layouts do not; the distance is the Jaccard distance of the marked cells. Below 0.35 to an earlier theme it warns (not an error until calibrated) and `--record` stores it.

All thresholds are uncalibrated proposals.

## 8. Next steps

Each step is one revertable commit on `ecommerce-library`:

1. Pick the inventory with the user. Done: `library/inventory.json`. Scope: primitives, commerce elements and components, shells (Header, Footer) and overlays; sections and pages come later. Optional parts are present but `enabled:false`, and only parts the ikas storefront API supports are listed (`not_in_ikas` names the rest).
2. Build `ikas-ecommerce.lib.pen` as skeletons (§5). Done: `scripts/gen_library.py` writes it from the inventory with name-derived node ids, so the file is byte-stable and `--check` catches a stale copy. Never edit the `.pen` by hand or save it from pen.dev; change the inventory and regenerate.
3. The copy script plus its tests. Done: `scripts/copy_library.py <plandata> -o <theme>.pen [--with Toast,…]`.
   - It copies what the plan names (Subs, sections, overlays). A block is folded into each host part that names it (`block` in the inventory); a shared Sub (`hosts`) is copied when one host is planned and placed as an instance in each host part that names it (`sub`). No root ever has `role: "block"` (02 §1).
   - Roots take the theme prefix. Sections and overlays get `@desktop` / `@mobile` roots, and extra states stay refs.
   - Ids and `metadata.type` are re-derived from the theme slug.
   - Every token is written from plandata. A token the plan lacks stops the copy before anything is written.
   - It prints a WARN for components the skill already requires but the plan does not name, and an INFO for library-only ones (Price, CartCount …) a plan may build inline.
   - It runs once per theme file, with the file closed in pen.dev.
4. The axis table and the similarity gate. Done: `library/axes.json` (15 axes, their fields, allowed values and generic defaults), `templates/globals.md` §0, `scripts/axes.py` (check / record / list). The layout fingerprint and the picture check followed in later commits.
5. Wire the phases. Done: SKILL.md analyze (§0 + `axes.py check`), plan (`axes.py record` after approval), build (`copy_library.py` first, the skeleton arrangement replaced unit by unit).
6. Update 05 §3 with the §2 observation (inherited metadata is readable; instance-level metadata is not stored). Done.
7. Section skeletons. Done: page sections with fixed names from 06 §2 (ProductDetail, ProductReviews, ProductList, CollectionHero, BrandHero, CartPage, AuthForms, Account, EmailVerification, OrderTracking, RichText, Contact, StoreLocator, FaqList, NotFound, BlogList, BlogPost) and content sections (Hero, Slideshow, ProductShelf, FeaturedProduct, ShoppableImage, CollectionList, MediaText, TextBlock, FAQ, USP, Newsletter, LogoStrip, Testimonials, BlogPosts, Marquee, SocialFeed). A content section has no fixed name: `copy_library.py` matches a plandata section's `archetype` family to it and copies it under the theme's own key. Pages stay out of the library (06 §2 lists their composition). A plandata section or overlay with no skeleton (no library name, no archetype match) is a `copy_library.py` WARN.
