# 04 · ikas constraints — what a design may contain so the port stays mechanical

Source of truth: the ikas Code Components MCP (`@ikas/code-components-mcp` 2.9.8, offline data `framework.json` topics `prop-types`, `theme-globals`, `sections-vs-components`, `page-composition`, `css-scoping`, `global-css`, `image-handling`, `common-pitfalls`, `real-world-architecture`; `section-templates/`). Where the MCP is silent, rules come from the ornek and geeny theme projects and are marked *(project rule)*. If the live MCP disagrees with this file, the MCP wins — re-check with `get_framework_guide("<topic>")`.

## Contents
1. Prop types (30)
2. Theme-global kinds × types and value formats
3. Runtime binding
4. Fonts
5. Packages, SSR and code rules
6. Tiers and the container pattern
7. Responsive
8. Section templates (28) and the `(özel)` convention

## 1. Prop types (30)

A layer becomes a prop when it carries `metadata.prop` + `metadata.propType` (tree notation `{name:TYPE}`). Only these 30 `propType` values exist; anything else is a lint ERROR.

| Type | Runtime shape in the component | Default? | Design-side carrier / notes |
|---|---|---|---|
| `TEXT` | `string` | yes | text layer; every visible literal is a TEXT prop (no hardcoded JSX text); loading labels need a second prop (`submitText` + `submittingText`) |
| `RICH_TEXT` | HTML `string` | yes | multi-paragraph text block |
| `NUMBER` | `number` | yes (finite number only) | counts, columns, intervals |
| `NUMBER_RANGE` | `IkasNumberRange` → `.value`, `.unit` | yes `{value, unit}` | needs `numberRangeData {min,max,interval?,unit?}` |
| `BOOLEAN` | `boolean` | yes | show/hide toggles |
| `IMAGE` | `IkasImage \| null` → `getDefaultSrc()` | **no** | frame with image fill |
| `IMAGE_LIST` | `IkasImageList` | **no** | repeated image frames |
| `VIDEO` | `IkasVideo \| null` | **no** | frame with poster-like fill; note "video" in `context` |
| `SVG` | raw `<svg>` string → `normalizeSvg()` | yes (≤64 KB, visible shape) | logos/marks that the merchant swaps; vector, CSS-colourable |
| `SVG_LIST` | `string[]` | yes | partner logos, icon rows |
| `DATE` | `Date \| string` | yes | countdown target, event date |
| `LINK` | `IkasNavigationLink \| null` → `.href`, `.label`, `.subLinks` | yes (typed `{linkType,…}`) | CTA, arrow link |
| `LIST_OF_LINK` | `IkasNavigationLinkList` | yes `{links:[…]}` | nav, footer columns |
| `COLOR` | CSS colour `string` | yes | `backgroundColor` on every section; optional `textColor` |
| `PRODUCT` | `IkasProduct \| null` | **no** | single featured product |
| `PRODUCT_LIST` | `IkasProductList` → `.data` | **no** | grids, carousels |
| `PRODUCT_ATTRIBUTE` | wrapper `{product, attributePropValue}` → `getAttributeDetailValues()` | **no** | custom field row on PDP |
| `PRODUCT_ATTRIBUTE_LIST` | single wrapper object (not an array) → `getAttributeListValues()` | **no** | spec table |
| `CATEGORY` | `IkasCategory \| null` | **no** | category card |
| `CATEGORY_LIST` | `IkasCategoryList` | **no** | category mosaic |
| `BRAND` / `BRAND_LIST` | `IkasBrand \| null` / `IkasBrandList` | **no** | brand strip |
| `BLOG` / `BLOG_LIST` | `IkasBlog \| null` / `IkasBlogList` → `.data` | **no** | journal rows |
| `BLOG_CATEGORY` / `BLOG_CATEGORY_LIST` | `IkasBlogCategory \| null` / list | **no** | journal filter tabs |
| `TYPE` | structured style value (`typeId`, e.g. PaddingStyleType) | yes `{value, unit}` | spacing knobs; sections get a whitelist only |
| `ENUM` | `string` (`enumTypeId`; custom enum created first; `__patternElementEnum__` = typography picker) | yes | layout variants, aspect ratio, font-style picker |
| `COMPONENT` | child slot → `<IkasComponentRenderer>` | yes | single slot |
| `COMPONENT_LIST` | child list → `<IkasComponentRenderer>` | yes | repeated child group (announcements, slides, columns) |

The table rows above that pair two types (`BRAND` / `BRAND_LIST` …) still count as two types each: 30 in total.

**Merchant-data props carry no `defaultValue`** (the CLI rejects it): `IMAGE`, `IMAGE_LIST`, `VIDEO`, `PRODUCT`, `PRODUCT_LIST`, `PRODUCT_ATTRIBUTE`, `PRODUCT_ATTRIBUTE_LIST`, `BRAND`, `BRAND_LIST`, `CATEGORY`, `CATEGORY_LIST`, `BLOG`, `BLOG_LIST`, `BLOG_CATEGORY`, `BLOG_CATEGORY_LIST` (the MCP list also names `RAFFLE`, `RAFFLE_LIST`, which are not in the 30 and are never used). Consequence for the design: placeholder imagery and sample product data on the canvas are **sample content**, not defaults — the plan's prop table shows `—` in the default column for these.

## 2. Theme-global kinds × types and value formats

Created with `create_theme_global` (MCP) after `list_theme_globals`. Display names are Turkish and grouped with ` / ` *(project rule)*.

| `kind` | `type` | Value format | Example |
|---|---|---|---|
| `globalVariable` | `TEXT` | string | `"1.25rem"`, `"transform 0.4s cubic-bezier(.16,1,.3,1)"` |
| `globalVariable` | `RICH_TEXT` | HTML string | `"<p>Hoş geldiniz</p>"` |
| `globalVariable` | `IMAGE` | object | MCP: `{ url }` (geeny notes `{ id }`; trust `list_theme_globals` output) |
| `globalVariable` | `COLOR` | string | `"#0D0D0D"`, `"rgba(13,13,13,0.6)"` |
| `globalVariable` | `NUMBER` | number | `0.3` |
| `globalVariable` | `BOOLEAN` | JSON boolean | `true` (string `"true"` fails) |
| `globalVariable` | `BORDER` | object | `{ "width": {"value":2,"unit":"px"}, "style":"solid", "color":"#0D0D0D" }` |
| `globalVariable` | `SHADOW` | object | `{ "x":0, "y":4, "blur":20, "spread":0, "color":"rgba(0,0,0,0.08)", "position":"outside" }` |
| `color` | — | concrete hex/rgb string | `"#FF3B1F"`; cannot alias another colour with `var(...)` |
| `typography` | — | fields `font_family`, `font_size`, `font_weight`, `line_height`, `letter_spacing` (strings) | `font_family:"Archivo Narrow", font_size:"18px", font_weight:"700", line_height:"1.1"`; no `text-transform` |
| `breakpoint` | — | `name` + integer `width` (px) | `width: 767` |
| `keyframe` | — | `name` + `points: [{ point, styles?: [{property, value}] }]` | `points:[{point:"0%",styles:[{property:"opacity",value:"0"}]},{point:"100%",…}]`; timing is set where it is applied |
| `colorScheme` | — | `name` + `colors: [{ slotId? \| newSlotName?, value }]` (exactly one key per entry) | slots `Background`, `Text`, `PrimaryButton/Background`, `PrimaryButton/Text`…; geeny binds slot values to global colours with `var(--<colorCssVar>)` |

There is no `spacing` or `radius` kind: spacing, radius and transition strings are `globalVariable TEXT` or `src/global.css` custom properties.

## 3. Runtime binding

All getters come from `@ikas/bp-storefront` and work in SSR, hydration and the editor canvas.

| Token | Getter / field | Use in component | Live on editor edit? |
|---|---|---|---|
| colour | `getThemeColors()` → `cssVar` | `color: var(--…)` — copy the exact `cssVar`; its casing can differ from the id, never build it from the id | yes |
| typography | `getThemeTypography()` → `className` (`_<id>`) | `className={t.className}`; do not spread `resolved` inline | yes |
| global variable | `getThemeSetting("<variableName>")?.value` | push into an inline CSS custom property (`style={{"--pad": v}}`) | on refresh only |
| breakpoint | `getThemeBreakpoints()` → `width`; in CSS the `bp(<id>)` token | `@media (max-width: bp(<id>))`; non-overlapping upper range `@media (min-width: calc(bp(<id>) + 1px))`, px arithmetic only. **`var()` is not allowed in a media condition** (fails silently) | yes (rewritten at render) |
| keyframe | `getThemeKeyframes()` → `ref` (`_<id>`) | `animation-name: <ref>` + duration/iteration where applied | on refresh |
| colour scheme | `getThemeColorSchemes()` → `{schemes, values}`; `values[i].colorsByScheme[slotId].cssVar`, `values[i].className` | unwrapped slot vars inherit the section's scheme; wrap in a palette `className` only to force one palette. Reference slots **by id, never by name** | yes |

Portability: literal keys/ids in code ship with the asset; mixing literal and computed keys drops the computed ones.

Design → ikas mapping *(project rule, see `02-contract.md` for names)*: `mode` colour variables (2–4 scheme values) → one `colorScheme` palette per scheme; `text-*` (device axis) → one `typography` per preset + intermediate sizes in component CSS; `space-*`, `size-*`, `opacity-*`, motion tokens → `src/global.css` custom properties or `globalVariable TEXT`; colours with alpha (`color-scrim`, `color-transparent`) → `globalVariable COLOR` (rgba) or `global.css`.

## 4. Fonts

- Google Fonts only; every family must include the **latin-ext** subset (Turkish `İ ı Ş ş Ğ ğ Ç ç Ö ö Ü ü`) *(project rule)*.
- Only weights the family actually ships are accepted (geeny: `Roboto Flex` → `supportedFontWeights: [400]`; any other weight is rejected) *(project rule)*. Pick weights from the family's Google Fonts page, not from the reference CSS.
- Typography tokens never carry `text-transform`; uppercase is written in the copy and the root needs `lang="tr"` for correct `i/İ` casing *(project rule, geeny)*.
- pen.dev: the official skill says all Google fonts are available, but in practice some names are rejected with "Font family … is invalid". Known invalid: `Mona Sans Condensed`, `Big Shoulders Display`. Tested valid: `Anton`, `Antonio`, `Archivo Narrow`, `Barlow`, `Barlow Condensed`, `Bebas Neue`, `JetBrains Mono`, `Mona Sans`, `Oswald`, `Sofia Sans Extra Condensed`, `Space Mono`. pen.dev cannot set variable-font axes (`wdth`), so a condensed cut must be its own family.
- Custom (non-Google) fonts: the only documented path is `font_family` on a typography token; component `@font-face` names are rescoped per component. Treat as an open question in the handoff.

## 5. Packages, SSR and code rules

- **Package allowlist** (build fails otherwise): `preact` (+ `preact/hooks`, `preact/compat`, `preact/jsx-runtime`), `mobx`, `@ikas/bp-storefront`, `@ikas/bp-storefront-models`, `@ikas/bp-storefront-config`, `@ikas/bp-storefront-api`, `@ikas/component-utils`, `animejs`, `three` *(project rule, geeny IKAS.md; enforced by the CLI's external-package check)*. No `gsap`, `lenis`, `framer-motion`, `lodash`, `lucide-react`. AnimeJS is reached via `import { AnimeJS } from "@ikas/bp-storefront"`.
- Never deep-import (`@ikas/bp-storefront/dist/...`): bundles, then throws at runtime; build rejects it.
- **SSR:** a server bundle renders first (no browser APIs). `window`, `document`, `IntersectionObserver`, scroll listeners only inside `useEffect`. SSR output must show the **end state** of every animation; the start state is added by a class after hydration. Honour `prefers-reduced-motion`.
- CSS is scoped per component (`.cc_<id>` prefix): class selectors only; `@keyframes` and `@font-face` names are rescoped, so a keyframe shared by several components must be a theme `keyframe`. `src/global.css` is unscoped and loads first.
- Root component exports are not wrapped in `observer()`; sub-components reading stores are.
- Money via `get*FormattedPrice` / `formatCurrency`, never `Intl.NumberFormat`. Product images via `getSelectedProductVariant` → `getProductVariantMainImage` → `.image` → `getDefaultSrc` / `createMediaSrcset`; media lists may contain videos.

## 6. Tiers and the container pattern

| Tier | Registered in `ikas.config.json` | Canvas root | Notes |
|---|---|---|---|
| Section | yes, `type: "section"` | `P/Section/<Key>@desktop` + `@mobile` | full width; **must** have `backgroundColor` COLOR (default `#ffffff`); `isHeader` / `isFooter` on exactly one each; ≥5 props → prop groups |
| Child component | yes, no `type` | item layer of a `{slot:COMPONENT_LIST}` group (or `P/Sub/<Name>` if visually reused) | placed by the merchant into a section slot; product data passed via `privateVarMap` |
| Sub-component | no (`src/sub-components/`) | `P/Sub/<Name>` (+ `— <state>`) | Button, ProductCard, Drawer, Input…; code-only |

**Container sections** (Header, Footer, ProductDetail, AccountInfo) host children through a `COMPONENT_LIST` prop restricted by `filteredComponentIds` (opaque ids). Always three steps: create each child → create the parent section without the filter → `update-prop --filteredComponentIds`. In the plan, list the children per slot so the port can run the recipe; ids never appear in design docs.

Overlays (`P/Overlay/<Name>…`) are not a tier: they port as sub-components rendered inside the owning section (CartDrawer, SearchOverlay and QuickBuy inside Header, InfoDrawer inside ProductDetail). The merchant blocks of `06-page-coverage.md` §3b (Birlikte al, set, kademeli indirim, kişiselleştirme, haber ver, Hızlı Öde) are local components of ProductDetail that render only when the product carries that data; cart adjustment rows, gift lines and the recommendation rail belong to CartPage / CartDrawer. QuickBuy is opened from `ProductCard` through a shared UI store or window event and hands over to CartDrawer after a successful add.

## 7. Responsive

- Only two widths are designed: `@desktop` (1440) and `@mobile` (390). Laptop and tablet are **not** designed; their values come from the reference ladder (globals.md §2/§4) and are written in component CSS.
- Breakpoints are theme globals (ornek: `laptop` 1199, `tablet` 991, `mobile` 767). Every `@mobile` difference becomes `@media (max-width: bp(<mobileId>))` in the same component's `styles.css` — one component, two layouts.
- When the merchant must control the mobile variant independently (different image crop, column count, hidden block), add a duplicate prop with a `mobile` prefix (`mobileImage` IMAGE, `mobileColumns` NUMBER, `showOnMobile` BOOLEAN) and draw it on the `@mobile` frame with that prop name.
- Device-axis variables (`text-*`, `space-*`, `size-*`) resolve automatically on the `@mobile` frame; never type mobile numbers by hand.

## 8. Section templates (28) and the `(özel)` convention

`get_section_template("<name>")` returns a working recipe (config snippet, `index.tsx`, children, sub-components). Each plan section names its starting template in the `**ikas:**` line.

| Template | Use for |
|---|---|
| `header-section` | global header container (Navbar, Announcements, CookieBar; mini-cart, search modal) — `isHeader` |
| `footer-section` | global footer: link columns, social icons, newsletter, copyright — `isFooter` |
| `hero-slider-section` | full-width slider with HeroSliderItem children |
| `category-images-section` | category image grid (CategoryImageItem children) |
| `product-slider-section` | product carousel; card children via `privateVarMap` |
| `features-section` | icon + text feature grid |
| `rich-text-section` | free content / legal / support pages |
| `category-list-section` | PLP: grid, filters, sort, pagination; also search results |
| `product-detail-section` | PDP container: gallery + 12 children in 2 slots |
| `product-reviews-section` | review summary, cards, form |
| `cart-section` | full cart page: lines, coupon, summary, checkout |
| `account-info-section` | account dashboard tabs (info, orders, addresses, favorites, order detail) |
| `login-section` | login form |
| `register-section` | register form |
| `forgot-password-section` | request reset email |
| `recover-password-section` | set new password from token |
| `email-verification-section` | email verification status |
| `not-found-section` | 404 |
| `blog-home-section` | blog listing with categories and pagination |
| `blog-post-section` | single blog post |
| `add-to-cart` | pattern: stock check, quantity, add-to-cart (inside PDP/cards) |
| `bundle-products` | pattern: bundle selection and pricing |
| `component-renderer` | pattern: `IkasComponentRenderer` slots, `filteredComponentIds` |
| `favorites` | pattern: wishlist toggle; FAVORITES page grid |
| `image-handling` | pattern: gallery, srcset, zoom, preview modal |
| `navigation` | pattern: Router, mobile menu, nav links |
| `product-pricing` | pattern: discount detection, formatted prices |
| `variant-selection` | pattern: swatches, size buttons, availability |

The last eight are **patterns**, not sections: cite them next to a section's template (`product-detail-section + variant-selection`).

**`(özel)`**: when no template fits (marquee strip, manifesto, lookbook, timeline, sticker wall, contact form…), the `**ikas:**` line reads `(özel)` — "custom", built from scratch on the generic section skeleton — optionally with a hint after a semicolon: `(özel; SocialFeed yerine)`, `(özel; form-handling rehberi)`. A contact form section is `(özel; form-handling + getContactForm / submitContactForm)`: no section template exists, but the storefront contact form API does (`06-page-coverage.md` Contact row). Custom sections still obey §1–§7, including `backgroundColor`.
