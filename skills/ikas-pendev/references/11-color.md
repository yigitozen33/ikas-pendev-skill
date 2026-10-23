# 11 · Colour schemes — sources, colour psychology, selection

How the analyze phase turns the brief's colour answers into the theme's ikas colour schemes. Output: `globals.md` §1a (the schemes) and §1b (the rationale). Lint gate: L22.

## Contents
1. What a scheme is
2. Sources
3. Workflow
4. Recording
5. Sector → effect
6. Area roles

## 1. What a scheme is

An ikas `colorScheme` is one complete colour combination (Background, Text, PrimaryButton/Background, …). The merchant picks one per section in the editor, so a theme ships **2–4 schemes**: the first is the default, the others give sections a different mood (a dark editorial band, a warm campaign block).

On the canvas each scheme is one value of the `mode` axis (`02-contract.md` §3). The value is the scheme's name folded to ASCII (`Kağıt` → `kagit`). Every colour variable has one value per scheme, and a section root carries `mode: "<slug>"` when it uses a non-default scheme. `color-danger` and `color-success` keep their hue family in every scheme; only their lightness changes to pass contrast.

## 2. Sources

Use both palette sources when they are reachable. Never block the phase on a source.

| Source | How | Strength |
|---|---|---|
| **Reference** | measured or estimated colours from 01 §2–§3 | the brand the user showed; tag `[referans]` |
| **qrco MCP** | remote MCP at `https://qrco.ca/mcp`, no key. Setup, once: `claude mcp add --transport http qrco https://qrco.ca/mcp` | curated palette catalogue, semantic roles with measured contrast, comparisons; tag `[qrco]` |
| **Huemint API** | `python3 -I ${CLAUDE_SKILL_DIR}/scripts/huemint.py` | ML model trained on brand and web palettes; fills each role with the contrast the role needs; tag `[huemint]` |
| **AI** | your own choice, checked by lint L14 | fallback and gap filler; tag `[ai]` |

**qrco tools used** (unknown arguments are rejected; if a call fails on its schema, read `get_capabilities` once):
- `search_explore`: curated catalogue first. Pass `query`, `temperature` (warm/cool/neutral/mixed), `lightness`, `chroma` (muted/balanced/vivid), `colorCount`, `minTextContrast: 4.5`.
- `generate_palette_set`: up to 5 options per call. Pass `colorsPerPalette`, one of `inspiration` / `style` / `baseColor`, and `lockedColors: [{index, hex}]`.
- `build_brand_system`: one palette → semantic roles with measured contrast. Pass `colors`, `primaryIndex`, `accentIndex`, `mode` (`light` / `dark`), `textContrast: 4.5`, `uiContrast: 3`.
- `generate_state_colors`: hover, pressed, disabled and focus colours for the button on its actual surface.
- `compare_palettes` / `audit_palettes`: ΔE2000 between schemes and the contrast pairs of `02-contract.md` §10.
- Locks are exact. Carry `lockedColors` into every call and never unlock a colour to meet contrast. If a locked reference pair fails contrast, tell the user instead of changing the colour silently.

**Huemint script:** `huemint.py --lock color-bg=#RRGGBB [--lock …] --temperature <t> --results 20 --json docs/referans/huemint-<şema>.json`. Default roles: bg, surface, text, muted, inverse-bg (button), accent. Temperature follows the tone:
- 0.6–0.9: calm, premium, classic
- 1.0–1.3: balanced
- 1.4–1.8: playful, bold

The script measures every candidate against the contrast pairs and lists the passing ones first.

**Huemint licence:** Huemint allows its public API for non-commercial applications only. Hex values themselves are not protected, but an ikas theme is commercial work. Note in brief §7 that Huemint was used. If the user wants to avoid the risk, skip Huemint and use qrco + AI.

**Fallbacks:**
- qrco not connected: Huemint + AI.
- Huemint unreachable: qrco + AI.
- Both down: AI + lint L14, every generated value tagged `[ai]`.

## 3. Workflow

Run this in analyze, after the palette → roles step of `01-analysis.md`.

**A · Inputs**
- brief §7: the reference-colour decision (aynen / ana renkler / yeni palet) and the number of schemes
- brief §2: sector and the three tone adjectives
- `globals.md` §1: the reference colours
- `components.md`: the section list

**B · Rationale first.** Write §1b before generating anything. Think as the store's customer: what should they feel on the hero, the product grid, the product page, the cart, a campaign band? For each scheme write:
- its purpose: which sections and why
- the psychological goal (§5)
- the hue families it favours and avoids
- the temperature, lightness and chroma it targets
- where the accent appears (§6)

**C · Locks from the brief:**

| Brief decision | Locks |
|---|---|
| Aynen aktar | every measured reference role is locked in the scheme it came from; the reference's other grounds become further schemes |
| Ana renkleri koru | the brand colour and the accent are locked (plus the ground when it is distinctive); everything else is generated |
| Yeni palet, or no usable reference colours | nothing is locked; the reference only informs the mood |

**D · Candidates.** For each scheme gather at least three candidates from at least two sources when they are reachable:
1. qrco `search_explore` with the rationale's query and filters
2. qrco `generate_palette_set` with the locks
3. `huemint.py` with the same locks

**E · Selection.** Score every candidate:
- **Fit:** it serves the scheme's psychological goal (B).
- **Contrast:** all `02-contract.md` §10 pairs pass.
- **Distinct:** its ground differs clearly from the other schemes' grounds (`compare_palettes`, ΔE2000 ≥ 20).
- **One brand:** the accent stays in one hue family across schemes.
- **Not a copy:** under "yeni palet" it is not the reference's palette.

Complete the winner to all colour roles of `02-contract.md` §3 with `build_brand_system` (plus `generate_state_colors` for buttons). Fill any role still empty yourself and tag it `[ai]`.

**F · Scheme count.**
- **"Referanstaki kadar":** count the distinct grounds that carry at least one full-width section in the reference.
- **"AI önersin":** 2 schemes (default + one contrasting); 3 when the theme has an editorial or campaign band that needs its own mood. Never more than 4.

**G · Show.** Plan §1 shows the schemes and their one-line rationale before the build.

## 4. Recording

**`globals.md` §1a:** one column per scheme, the default first.
- Header cells hold Turkish evocative names (`Kağıt (varsayılan)`, `Mürekkep`, `Kil`; 01 §5 naming rule).
- Each value cell is `` `#HEX` [kaynak] [ölçüldü|tahmini] ``, with `[kaynak]` ∈ `[referans]` `[huemint]` `[qrco]` `[ai]`.
- The plan's `modes` are the folded names in the same order (`["kagit","murekkep","kil"]`). Lint L22 errors when they differ.

**`globals.md` §1b "Renk kurgusu":**
- a table `Şema | Psikolojik hedef | Kaynak | Bölümler`
- one or two bullets of reasoning per scheme
- a source note (which tools ran, Huemint licence acknowledged or skipped)

The section → default scheme bullets stay under §1a, because `build_manifest.py` reads them there.

## 5. Sector → effect

These are starting points, not rules. Every theme argues its own choice in §1b, and the tone adjectives can override a row.

| Sector | Customer should feel | Favour | Use with care |
|---|---|---|---|
| Fashion, apparel | taste, confidence | neutral grounds that let photos lead; one decisive accent | many saturated hues competing with product photos |
| Cosmetics, care | care, purity, softness | warm off-whites, powder tones, muted rose or sage | clinical cold blue-white (reads pharmacy) |
| Food, delicatessen | appetite, freshness, warmth | warm grounds; tomato, olive, mustard, crust browns | blue and purple as dominant grounds (suppress appetite) |
| Home, furniture | calm, belonging | earth, clay, linen, wood neutrals; deep green or ink | neon and high-chroma accents |
| Outdoor, sport | energy, nature, endurance | forest, stone and slate; a signal orange or lime accent | pastel grounds |
| Electronics, tech | precision, trust | cool neutrals, graphite, one electric accent | warm beige grounds (read dated) |
| Kids, toys | joy, safety | bright but soft primaries on clean grounds | dark full-bleed schemes |
| Jewellery, luxury | exclusivity, calm | deep ink, black, ivory; gold or champagne used sparingly | busy multi-colour accents, discount-red everywhere |
| Health, pharmacy | trust, cleanliness | clean white, calm blue or green | aggressive red or orange as ground |
| Books, stationery | curiosity, focus | paper tones, ink, one editorial accent | glossy gradients |
| Pets | warmth, playfulness | warm neutrals, friendly mid-saturation accents | cold clinical palettes |

**Cultural notes (Turkey):**
- Red reads as campaign and discount: strong for sale bands, tiring as a ground.
- Green reads as natural and healthy.
- The accent and `color-danger` must stay distinguishable (ΔE2000 ≥ 15), or a CTA looks like an error.

## 6. Area roles

| Area | Colour job |
|---|---|
| Header, footer | calm frame; default scheme; accent only on the cart count or the active link |
| Hero | the mood carrier; it may use the most expressive scheme |
| Product grid, listing | quiet, low-chroma ground so product photos lead; accent on badges and price emphasis only |
| Product page, cart, checkout steps | trust and clarity: default scheme, high contrast, accent reserved for the primary CTA |
| Campaign band, announcement | attention; accent-led or the warmest scheme, kept short |
| Editorial, newsletter, story blocks | rhythm; the contrasting scheme, so the page reads light, light, **dark**, light |

One primary accent action per view. When everything is accent, nothing is.
