# 01 — Analysis (Phase 1)

Turns screenshots and/or a live URL into two files: `docs/referans/globals.md` (tokens + motion) and `docs/referans/components.md` (inventory + ikas mapping). Everything downstream (plan, canvas, port) reads these two files, so every value must carry its provenance tag.

## Contents

1. Inputs and modes
2. Screenshot mode protocol
3. URL mode
4. Measurement checklist
5. `globals.md` spec
6. `components.md` spec
7. Coverage audit
8. Phase-1 gate

Fill-in skeletons: `templates/globals.md`, `templates/components.md`. Worked example: `examples/ornek/{globals,components}.md` (an anonymised contract 1 theme; where it differs from the current templates and references, those win).

---

## 1. Inputs and modes

| Mode | Input | Value tag | Tools |
|---|---|---|---|
| **Screenshot** | 1+ images in `docs/referans/girdi/` | always `[tahmini]` | vision only (no script) |
| **URL** | live site URL (+ optional extra paths) | `[ölçüldü]` for what the CSS source or the rendered page yields; `[tahmini]` for the rest | `scripts/analyze_site.py` (source) + `scripts/browse_site.py` (rendered, agent-browser) |
| **Hybrid** | both | per value | URL first, screenshots fill gaps |

- **URL wins.** In hybrid mode a measured value overrides any screenshot estimate. Screenshots only contribute what the URL cannot show (logged-in pages, states the browser did not reach, cart with items). In URL mode `browse_site.py` writes its own full-page screenshots at known widths, so the viewport question of §2 does not arise for them.
- Copy every input image to `docs/referans/girdi/` (the folder is gitignored; add it to `.gitignore` if missing). Name images `NN-<page>-<width>.png` (`01-home-1440.png`).
- The reference is inspiration only. Never copy its images, logo, copy or brand name into globals/components; record only measurements and structure.

## 2. Screenshot mode protocol

Prompt-only: no script parses images. Work image by image.

1. **Ask the viewport width for every image** you were not told (one question listing all images). Without it no px value is trustworthy. Compute `scale = viewport_css_width / image_px_width` (2× retina screenshots give 0.5). Every measurement below is `image_px × scale`.
2. Tag **every** value `[tahmini]`, including colours (compression and colour profiles shift hex).
3. Estimate in this order:

| What | How |
|---|---|
| **Palette → roles** | List the 6–12 dominant flat colours (backgrounds, text, lines, fills). Merge near-duplicates (ΔE < 3 by eye). Assign each to a role: bg, text, muted, line, surface, inverse-bg/text, accent, accent-text, scrim, danger, success. A role nobody shows stays empty → note "referansta yok". The colour schemes are built from these roles afterwards (`11-color.md`). |
| **Type scale** | Measure cap height of each distinct text size; `font-size ≈ cap_height / 0.70` (condensed grotesks ≈ 0.72, serifs ≈ 0.66). Group into the 11 presets (display … price). Record ratios between steps (e.g. display/h2 = 1.5); keep ratios when snapping to integers. Weight: light/regular/bold/black by stroke. Case: uppercase or not. Letter-spacing: tight/normal/wide. |
| **Font family** | Classify (condensed grotesk, geometric sans, serif, mono). Propose 1–2 Google Fonts candidates per role that are valid in pen.dev (see `05-pendev-pitfalls.md`). Never claim the exact face. |
| **Spacing rhythm** | Measure page margin, gutter between cards, card padding, panel padding, gap label↔title, section top spacing. Find the base unit (4 or 5 or 8) and snap to it. Then fill the spacing-system roles (`02-contract.md` §3b): band edge vs content edge (one value or two?), header → first section, section → section, last section → footer, column split, grid. Each role gets one token; a second edge becomes a theme extra (`space-band`). |
| **Grid** | Count columns per row type (product grid, category tiles, footer). Record column width, gutter, aspect ratios of media (3:4, 4:5, 16:9). |
| **Lines, radius, depth** | Line thickness (1 / 2 px), where lines sit (cell, row bottom, header top+bottom), corner radius, shadow yes/no, gradient overlays on images. |
| **Component inventory** | Every repeated unit (card, button, chip, badge, field, tab, accordion row) and every section band top to bottom. |
| **States visible** | Only states an image actually shows (hover, open menu, filled cart, error). Everything else goes to the "ölçülemeyenler" list, never invented as measured. |
| **Motion** | Not visible in stills. Infer only from cues (progress bars, dots, marquee overflow, sticky headers) and tag `[tahmini]`; pick catalogue recipes in `03-motion.md`. |

4. If two images disagree (different widths, A/B variants), ask once; otherwise prefer the widest desktop image for desktop values and the narrowest for mobile.

## 3. URL mode

Two passes over the same pages, because each sees what the other cannot:

| | `analyze_site.py` — source pass | `browse_site.py` — rendered pass |
|---|---|---|
| How | downloads HTML/CSS/JS as text, parses with regex; nothing runs | agent-browser (headless Chromium) renders the page, scrolls once, reads `getComputedStyle` |
| Strong at | every breakpoint, `@keyframes`, cubic-beziers and spring params in JS bundles, `@font-face` files, the full `:root` set, cross-origin CSS | what is actually on screen: colours by painted area, type by characters, section boxes, real px for `clamp()`/`vw`, JS-rendered sites, running animations, screenshots |
| Blind to | which value is used where and how much (dead CSS counts the same as the page background), JS-rendered styles | values that exist only in source (unused breakpoints, keyframes not running at measure time, springs), cross-origin stylesheets (`:hover`/`@media` from those) |

1. **Source pass** (stdlib, isolated interpreter, reads remote text only):

   ```bash
   python3 -I ${CLAUDE_SKILL_DIR}/scripts/analyze_site.py https://example.com --paths /,/shop,/about --json docs/referans/girdi/analyze.json --out docs/referans/analyze.md
   ```

   Options: `--paths` extra pages, `--json` machine output, `--max-css` cap on stylesheets, `--timeout` seconds. Pages are capped at 5 MB and parsed as text (never executed). Each line carries its source (file/selector) and `[ölçüldü]`. Sections: fonts (`@font-face`, families), colours (by declaration frequency), font-size presets × media query, breakpoints, durations + cubic-beziers, springs, `@keyframes`, border-radius, gap/padding values, Framer/Webflow layer names.

2. **Rendered pass** (needs `agent-browser`; install once with `npm i -g agent-browser && agent-browser install`):

   ```bash
   python3 -I ${CLAUDE_SKILL_DIR}/scripts/browse_site.py https://example.com --paths /,/shop,/about --out docs/referans/browse.md
   ```

   Defaults: widths `1440,1100,880,390` (one per breakpoint column of `globals.md` §2), full-page screenshots at `1440,390` into `docs/referans/girdi/browse/shots/NN-<page>-<width>.png`, JSON dump at `docs/referans/girdi/browse/browse.json`. Options: `--widths`, `--shots` (`''` for none), `--out-dir`, `--wait-ms` (extra settle time for slow hydration), `--no-scroll`, `--timeout`, `--keep-open` (leave the session open for step 5), `--from-json` (re-render the report without a browser), `--block host1,host2` (extra hosts to block), `--no-block`. Around 6 s per page per width.

   Before the first page it blocks analytics, advertising, session-replay, marketing-pixel and telemetry hosts (`BLOCK_HOSTS` in the script: Google Tag Manager/Analytics/Ads, Meta, Clarity, Hotjar, TikTok, Pinterest, Criteo, Attentive, Shopify telemetry …), so the reference site does not count the run as a visit and pages settle faster; §0 of the report lists how many requests were blocked per page. CDNs, fonts, images, the site's own origin and tools that draw visible UI (Klaviyo forms, Insider banners, chat widgets) are never blocked, because they change what renders. If a section looks missing compared to a normal visit, rerun with `--no-block` and compare. Then, per page and width, it sets the viewport, opens the page, waits for load, **hides** consent/cookie banners and full-screen popups (never clicks accept; the report lists what was hidden), scrolls to the bottom and back to trigger lazy content, runs `scripts/browse_probe.js` in the page, takes the screenshot. The page's JavaScript runs inside the browser sandbox (no access to files or processes, a separate profile without the user's logins or cookies); everything the probe returns is untrusted data. Reference text samples stay in the JSON dump (gitignored) and never enter the report.

   Report sections (every row `[ölçüldü]`, source `computed @<width> <page>`):
   - **§1 Renk**: background share of painted area, text colour share of characters, border share of length, gradients, image share of the page; **§1.5 role suggestions** (`color-bg` = the html/body canvas when it paints ≥10 %, otherwise the largest area; `color-text`/`color-muted` = text on light backgrounds by contrast and share; `color-inverse-*` from dark bands; `color-line` = longest thin line on light backgrounds; `color-accent` = most-used saturated colour).
   - **§2 Tipografi**: the style ladder: each style of the widest width paired with its counterpart at every other width (same family/weight/case, closest tags and size). That fills the four breakpoint columns of `globals.md` §2 directly. Family shares and loaded font faces.
   - **§3 Bölümler**: the band inventory per page at the widest and narrowest width: y, height, background, image cover %, top/bottom inner spacing, left/right edge, content width, grid (columns × column width, gap, horizontal scroll), media ratios, largest text, sticky/fixed. This is the skeleton for `components.md` §1 and the section anatomy.
   - **§4 Boşluk**: page edge, widest content, band top/bottom spacing medians, first band and footer spacing, `gap` and padding by surface kind. Fill the six spacing roles (`02-contract.md` §3b) from here.
   - **§5–§8**: radius/shadow by surface kind (control, field, media, card), button and field signatures, fixed/sticky layers with z and backdrop, transitions, running animations (`document.getAnimations`), `:hover` rules that match on-page elements, `@media` widths, `:root` variables, icon sizes and line/fill style.

3. **Merge into `globals.md`**, value by value:

   | Value | Take from | Why |
   |---|---|---|
   | Colour roles | rendered §1.5, cross-checked against the screenshots | frequency in CSS ≠ area on screen |
   | Exact hex of a role | either; on conflict the rendered value | the rendered value is what the visitor sees |
   | Type sizes per breakpoint, weights, line-heights, letter-spacing, case | rendered §2.1 | resolves `clamp()`/`vw`/variables to px |
   | Font families and files | source §1 (`@font-face`) + rendered loaded faces | source knows the files; rendered knows what is used |
   | Breakpoints | source | rendered only sees the widths it was given |
   | Spacing roles, grids, header height, content width | rendered §3–§4 | real boxes, not declarations |
   | Radius, shadow | rendered §5 by surface kind | ties a value to buttons, cards or media |
   | Durations, easings | rendered §7 when present, else source | running values beat declared ones |
   | Springs, `@keyframes`, JS-only motion | source | not visible as computed style |
   | Section inventory and order | rendered §3 + screenshots | |

   When the two disagree on something the table does not cover, the rendered value wins and the source value is noted in the cell (`#1C1C1C [ölçüldü] (kaynakta #222)`). A role the rendered page does not show stays "referansta yok".

4. **Look at the screenshots** (`Read` the PNGs; downscale long pages first, e.g. `sips -Z 1400`) to name the sections, check the role suggestions and see what the numbers cannot tell (image style, composition, hierarchy). Their width is known, so values read from them are still `[tahmini]` but need no viewport question.

5. **States** (hover, open menu, drawer, add to cart): run step 2 with `--keep-open --session ref`, then drive the same session by hand and read computed styles before and after (the tracking blocks stay active in that session):

   ```bash
   agent-browser --session ref open https://example.com
   agent-browser --session ref snapshot -i                 # refs for the menu button, product card …
   P='^(color|background-color|border[a-z-]*-color|opacity|transform|box-shadow|text-decoration-line|width|height):'
   agent-browser --session ref get styles @e12 | grep -E "$P"     # before (get styles prints every property)
   agent-browser --session ref hover @e12                         # or: click @e7 (menu), set viewport 390 844
   agent-browser --session ref wait 600                           # let the transition finish
   agent-browser --session ref get styles @e12 | grep -E "$P"     # after
   agent-browser --session ref screenshot docs/referans/girdi/browse/shots/state-menu-390.png
   agent-browser --session ref close
   ```

   Values read this way are `[ölçüldü]` (source `computed @<width> <path> <state>`); values read off a state screenshot are `[tahmini]`. Never submit forms, log in, or accept cookies on the reference site.

6. **No agent-browser?** Last resort only (it uses the user's own Chrome): load the Claude-in-Chrome skill, resize to 1440 then 390 wide, and run this snippet per page and width. The JS tool truncates long returns (~1000 chars), so it returns compact counts:

   ```js
   (() => {
     const cnt = (m, k) => (m[k] = (m[k] || 0) + 1, m);
     const top = (m, n = 12) => Object.entries(m).sort((a, b) => b[1] - a[1]).slice(0, n);
     const col = {}, fs = {}, fam = {}, gap = {}, tr = {};
     document.querySelectorAll('[data-framer-name],[data-testid],[data-section],[class]').forEach(el => {
       const s = getComputedStyle(el);
       cnt(col, s.color); cnt(col, s.backgroundColor); cnt(col, s.borderTopColor);
       cnt(fs, s.fontSize + '/' + s.fontWeight + '/' + s.lineHeight + '/' + s.letterSpacing);
       cnt(fam, s.fontFamily.split(',')[0]); cnt(gap, s.gap + '|' + s.padding);
       if (s.transitionDuration !== '0s') cnt(tr, s.transitionDuration + ' ' + s.transitionTimingFunction);
     });
     const vars = [...document.styleSheets].flatMap(sh => { try { return [...sh.cssRules]; } catch (e) { return []; } })
       .filter(r => r.selectorText === ':root').map(r => r.cssText.slice(0, 300));
     const faces = [...document.fonts].map(f => f.family + ' ' + f.weight).filter((v, i, a) => a.indexOf(v) === i);
     return JSON.stringify({ w: innerWidth, col: top(col), fs: top(fs), fam: top(fam, 5), gap: top(gap, 8), tr: top(tr, 6), vars, faces });
   })()
   ```

   Values from this snippet are `[ölçüldü]`; note the source as `computed @1440 /path`. Its colour counts are per element, not per area: map roles from the screenshots, not from the counts.

7. **Blocked or empty** (bot protection, login wall, the report says "Hiçbir sayfa ölçülemedi"): say so to the user, keep the source pass, and ask for screenshots (hybrid mode).

## 4. Measurement checklist

Measure at desktop (≥1200, ideally 1440) **and** mobile (<768, ideally 390). Tick every row or move it to "ölçülemeyenler".

- [ ] Colours: bg, text, muted, line, surface, inverse bg/text, accent (+ text on accent), scrim (alpha + blur), danger, success.
- [ ] Fonts: families per role (display, ui, body, price, mono), weights, uppercase usage, letter-spacing.
- [ ] 11 type presets × 4 breakpoint columns (≥1200 · 992–1199 · 768–991 · <768) with weight and line-height.
- [ ] Spacing: page margin, grid gap, card padding, panel padding, xs/sm/md gaps, section spacing; the six spacing-system roles in `globals.md` §3, each bound to one token.
- [ ] Sizes: header height, line thickness, logo height, hero height rule, content max-width.
- [ ] Radius and shadow (usually one value each or "yok").
- [ ] Grid layouts per section type (columns × width, gutter, media aspect ratio).
- [ ] Breakpoints (exact media query values).
- [ ] Layer order (header, sticky bars, drawers, scrim, footer reveal).
- [ ] Icon style (line/filled), size, arrow and caret glyphs.
- [ ] Motion: durations, easings (cubic-bezier / spring params), delays, staggers, autoplay intervals, marquee speed.
- [ ] Mobile deltas: header layout, grids that become horizontal scroll, sticky elements that become flow.

## 5. `globals.md` spec

Written in Turkish. Header block: source (URL or "ekran görüntüleri: N adet"), widths measured, the tag legend, and the column rule "referans değeri → pen.dev değişkeni (`$ad`) → ikas karşılığı".

**Tag legend (verbatim):** `**[ölçüldü]** = siteden/CSS'ten/modülden okundu · **[tahmini]** = gözlemle kestirildi, aktarımda ayarlanacak.` Every value cell or every row carries one tag; a table may carry a tag in its header (`Referans [ölçüldü]`) when the whole column shares it.

**Stitch-style token rows.** The Referans cell of each colour is `**<evocative Turkish name>** \`#HEX\` [tag]` and the Token cell states the role, e.g. `| Zemin | **Kağıt** \`#EFEBE2\` [tahmini] | \`color-bg\` | colorScheme slot \`Background\` |`. Names describe the material or mood ("Gece Mürekkebi", "Beton Grisi", "Sinyal Turuncusu"), never generic ("Grey 2").

| § | Heading | Required table columns (exact) | Notes |
|---|---|---|---|
| 1 | `## 1. Renk` | `Token \| Referans \| pen.dev \| ikas` | one row per core colour role (see `02-contract.md` §3); "Kurallar" bullets: line usage, radius, shadow/depth |
| 1a | `### 1a. Renk şemaları` | `ikas slot \| pen.dev token \| <şema adı> (varsayılan) \| <şema adı> …` | one column per scheme (2–4); each value `` `#HEX` [kaynak] [tag] ``; section → default scheme bullets (`11-color.md` §4) |
| 1b | `### 1b. Renk kurgusu` | `Şema \| Psikolojik hedef \| Kaynak \| Bölümler` | rationale bullets + source note (`11-color.md` §3B, §4) |
| 2 | `## 2. Tipografi` | presets: `Token \| Kullanım \| ≥1200 \| 992–1199 \| 768–991 \| <768 \| Ağırlık \| Satır`; mapping: ` \| pen.dev \| ikas` with rows Boyutlar / Aile / Ara kırılımlar | font paragraph with pen.dev substitute when the real font is invalid there |
| 3 | `## 3. Boşluk, grid, ölçü` | `Token \| Referans [ölçüldü] \| pen.dev \| ikas` | then "Grid düzenleri" bullets (desktop) and "Mobil (<768)" bullets |
| 4 | `## 4. Kırılımlar` | `Ad \| Aralık [ölçüldü] \| pen.dev \| ikas` | desktop / laptop / tablet / mobile; only desktop and mobile are designed |
| 5 | `## 5. Katman sırası` | `Katman \| z \| Not` | |
| 6 | `## 6. İkonlar` | prose | style, size, glyphs; logo via `Generate("svg")` |
| 7 | `## 7. Motion` | 7.1 `Token \| Değer [ölçüldü] \| Kullanım`; 7.2 `Kısa ad \| Ne \| Ne zaman`; 7.3 `ID \| Ad \| Hareket ve değerler \| Katman yapısı \| Uygulama \| Mobil / azaltılmış hareket`; 7.4 bullets "Referansta ölçülemeyenler" | 7.3 lists only the catalogue recipes this reference shows; IDs and structures come from `03-motion.md` §4 |
| 8 | `## 8. Kapsama denetimi` | see §7 below | |

Token names in the pen.dev column are fixed (`02-contract.md` §3); only values change per theme.

## 6. `components.md` spec

Written in Turkish. Opening: source, link to `globals.md`, the three tiers (Section = ikas `type: section`; Component = child in a `COMPONENT_LIST` slot; Sub = code-only helper in `src/sub-components/`), and "prop tabloları öneridir".

1. `## 1. Sayfa → section bileşimi` — table `Sayfa (ikas sayfa tipi) | Referans URL | Section'lar (sırayla)`, plus rows "Her sayfa" (Header/Footer) and "Overlay'ler". Then a second table `Sayfa | ikas şablonu | Not` for ikas pages the reference lacks (cart, auth ×4, account, favorites, 404, email verification, search). Scope comes from `06-page-coverage.md`.
2. One `###` block per section, grouped `## 2. Global section'lar`, `## 3. Ana sayfa…`, `## 4. Mağaza…`, `## 5. İçerik…`:

   ```
   ### <Name>  [--isHeader | --isFooter]
   Referans: <where + measured size>. ikas şablonu: `<template>-section` | (özel).
   <anatomy tree in a code fence: kebab-case layer names, sizes, ← M-xx markers>
   Durumlar: varsayılan · hover · açık · boş · dolu · yükleniyor …
   Mobil: <what changes at <768>
   | Prop | Tip | Varsayılan | Grup |
   Çocuk component'ler: <Name> (field TYPE, …)
   Sub: <Sub names>
   Motion: M-xx, …
   ```

   - Tip is one of the 30 ikas prop types (`04-ikas-constraints.md`); lists name the child: `COMPONENT_LIST (\`FooterColumn\`)`.
   - Every section has a `backgroundColor | COLOR` row. Merchant-data props (IMAGE, PRODUCT_LIST, CATEGORY …) have `—` as default.
   - Every visible string is a TEXT prop (button loading text is its own prop) or a storefront data field; note data fields in the tree as `{data:product.name}`.
   - Write **(özel)** in place of the template when none of the 28 ikas section templates fits.
3. `## 6. Sub-component'ler` — table of shared subs with structure and states.
4. `## 7. ikas'a aktarım kuralları` — copy the short rule list from `04-ikas-constraints.md` (CLI order, no hand-edited config, SSR, allowed packages, keyframe/font-face renaming, no default on merchant data).

## 7. Coverage audit

Append `## 8. Kapsama denetimi` to `globals.md` (pattern: one line per component listing the tokens it consumes):

```
- **ProductCard** → `color-line`, `color-muted`, `text-title`, `text-label`, `text-price`, `space-card`, `size-line`, M-09
```

Then check and fix before the gate:

| Check | Fix |
|---|---|
| Every section/sub in `components.md` has a coverage line | add the line |
| Every token in globals §1–§3 is used by ≥1 line | drop it, or justify in one sentence |
| Every colour/size mentioned in `components.md` resolves to a token | add a token or reuse the nearest |
| Every motion observed (or inferred) maps to an M-xx or a local recipe | add to §7.3 / mark "plan'da yerel tarif" |
| Every reference page appears in the composition table; every in-scope ikas page has a row | add rows |
| Every section prop table has `backgroundColor` | add it |

## 8. Phase-1 gate

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/lint_plan.py --globals docs/referans/globals.md --components docs/referans/components.md
```

Pass = 0 ERROR (WARNs are reported to the user). The gate checks: the 7 (+8) headings, the exact column headers above, a tag on every value row, every core variable name present in the pen.dev column, prop types within the 30, `backgroundColor` per section, and the composition table. Then update the Durum table in `docs/00-brief.md` and stop for user review.
