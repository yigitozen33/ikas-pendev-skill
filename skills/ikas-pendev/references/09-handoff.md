# 09 · Handoff — the port package (`docs/port/`)

Phase 5 turns plan + canvas into a package a later port (human or an `ikas-port` skill) can execute without reading the canvas. It writes no ikas code and creates no theme globals: it prepares the runbook and stops at the user-approval step.

Inputs: `docs/pendev/plandata/`, the rendered plan, `docs/port/canvas-dump.txt` (the `ROOT|…` lines from `extract_targets.py <plan> --js manifest`). Command: `python3 ${CLAUDE_SKILL_DIR}/scripts/build_manifest.py --plandata docs/pendev/plandata --plan <plan> --dump docs/port/canvas-dump.txt --globals docs/referans/globals.md -o docs/port/`. `--globals` makes the runbook use the final colour schemes (§1a, one scheme per column, the first is the default) and the breakpoint text styles (§2a: family, weight, line height, letter spacing, and laptop/tablet/mobile sizes as `breakpoints` overrides; an uppercase style becomes a runbook note, never `text_transform`) instead of the plandata estimates. Outputs: `port-manifest.json`, `port-manifest.md`, `globals-runbook.md`, `seed-checklist.md` (the store data the behaviour criteria need, `10-port-behaviour.md`). On a large canvas the manifest `execute` can time out (`InternalError: interrupted`): render it as `--js manifest --part 1/N` … `N/N`, run each, and concatenate every `ROOT|…` line into one `canvas-dump.txt` (drop the per-part `SUMMARY` lines). A section's `frames.<device>` is always its component root (`@desktop`, `@mobile`), never a state frame; state frames are listed under `frames.<device>.states` with their node ids. Sections and overlays carry `desktopOnly` / `desktopOnlyStates` from plandata; the port hides those layers below the mobile breakpoint. Exit 1 when a plan section, page or anim target is missing on the canvas.

## Contents
1. `port-manifest.json` schema (schema 1)
2. `port-manifest.md` layout
3. Globals runbook
4. Live token table (filled by the port)
5. Coverage audit
6. What a future `ikas-port` skill may rely on

## 1. `port-manifest.json` schema (schema 1)

Top-level keys are fixed; unknown keys are ignored by readers; `schema` bumps only on a breaking change.

```json
{
  "schema": 1,
  "theme": { "slug": "ornek", "name": "Örnek", "prefix": "C", "contract": 1,
             "reference": "https://referans.example/", "canvas": "ornek-C.pen",
             "plan": "docs/pendev/plan-C-serbest-yorum.md",
             "devices": { "desktop": 1440, "mobile": 390 }, "modes": ["light", "dark"] },
  "globals": {
    "colors":      [{ "var": "color-bg", "name": "Renk / Zemin", "values": { "light": "#EFEBE2", "dark": "#0D0D0D" },
                      "ikas": { "kind": "colorScheme", "slot": "Background" } }],
    "typography":  [{ "var": "text-display", "name": "Tipografi / Display", "family": "Sofia Sans Extra Condensed",
                      "weight": "800", "lineHeight": "0.9", "sizes": { "desktop": 168, "mobile": 72 } }],
    "breakpoints": [{ "name": "Kırılım / Mobil", "width": 767 }],
    "keyframes":   [{ "name": "Animasyon / Marquee", "points": [], "usedBy": ["C-HDR-01"] }],
    "globalCss":   [{ "var": "space-page", "css": "--space-page", "values": { "desktop": 32, "mobile": 16 } }]
  },
  "subComponents": [{ "name": "ProductCard", "root": "C/Sub/ProductCard", "nodeId": "…",
                      "states": ["hover", "stok yok", "indirimli"], "props": [], "anims": ["C-CMP-01"] }],
  "sections": [{
    "key": "Header", "template": "header-section", "flags": { "isHeader": true },
    "props":    [{ "name": "logo", "type": "SVG", "default": null, "group": "Marka", "layer": "header-logo", "from": "both" }],
    "children": [{ "slot": "announcements", "type": "COMPONENT_LIST", "components": ["AnnouncementItem"] }],
    "dataBound": [{ "layer": "cart-count", "source": "cart.itemCount" }],
    "codeText":  [{ "layer": "digit" }],
    "anims":    ["C-HDR-01", "C-HDR-02"],
    "frames":   { "desktop": { "root": "C/Section/Header@desktop", "nodeId": "…" },
                  "mobile":  { "root": "C/Section/Header@mobile",  "nodeId": "…" } },
    "overlays": [{ "name": "CartDrawer", "states": ["boş", "dolu", "yükleniyor"], "frames": ["…"] }]
  }],
  "pages": [{ "name": "Home", "pageType": "INDEX", "sections": ["Header", "HeroSplit", "Footer"],
              "frames": { "desktop": "…", "mobile": "…" } }],
  "animTargets": [{ "id": "C-HDR-01", "section": "Header", "layer": "marquee-track", "via": "Marquee",
                    "recipe": "M-14", "trigger": "auto-loop", "impl": "css-keyframes", "done": false }],
  "behaviour": [{ "id": "PB-01", "title": "Odak çerçevesi yalnızca klavyede", "rule": "…", "test": "…", "done": false }],
  "seed":      [{ "id": "S-05", "title": "Blog içerikleri", "what": "…", "for": ["PB-09"], "done": false }],
  "openQuestions": [{ "id": "Q1", "kind": "prop-mismatch", "where": "Header.cartText",
                      "text": "Planda TEXT, canvas'ta prop yok" }]
}
```

Field rules:
- `behaviour` / `seed` are the entries of `scripts/data/port-behaviour.json` whose scope (`keys`, `pageTypes`) matches the plan; a seed entry stays only when a kept criterion needs it. The port sets `done` after the click-through (`10-port-behaviour.md` §4).
- `props[].from`: `plan`, `canvas` or `both`. A prop on one side only becomes an `openQuestions` entry (`kind: "prop-mismatch"`). `default` is `null` for every merchant-data type (`04-ikas-constraints.md` §1).
- `dataBound` / `codeText` come from `textClass: data|code` (contract 2). Contract 1 has no text classes: both arrays are empty and one open question says so.
- `anims` and `animTargets` are the union of `metadata.anim` and `context` ids; a plan id missing on the canvas is an error, not an open question.
- `flags`: `isHeader`, `isFooter`, `container` (true when the section has a `COMPONENT_LIST` slot with children).
- Node ids are informational (they change when a layer is recreated); names are the join key.
- `openQuestions[].kind` ∈ `missing-section`, `missing-frame`, `missing-page`, `prop-mismatch`, `anim-missing-on-canvas`, `anim-extra-on-canvas`, `data-unmarked`, `font`, `missing-template`, `data-source`, `contract`, `other`. Entries that stop the port carry `"blocking": true` (`build_manifest.py` exits 1 when any exists: a plan section, page or anim id absent from the canvas dump).
- `globals` also holds `colorSchemes` (colour variables whose light/dark values differ become scheme slots, since an ikas `color` global holds one value; alpha colours go to `globalCss`) and `globalVariables` (BORDER/SHADOW/TEXT tokens).
- Overlays live under the owning section's `overlays`; `animTargets` entries keep every anim-targets YAML key plus `onCanvas: true|false`.

## 2. `port-manifest.md` layout

Turkish, generated from the JSON; headings fixed:

```
# Port manifest — <Ad> (<P>, contract <n>)
## Özet                      sayılar: section · sub · sayfa · overlay · anim hedefi · açık soru
## Tema global'leri
### Renkler                  | Ad | pen.dev | Açık | Koyu | ikas |
### Tipografi                | Ad | pen.dev | Aile | Ağırlık | Satır | Masaüstü | Mobil |
### Kırılımlar               | Ad | Genişlik |
### Keyframe'ler             | Ad | Kullanan hedefler |
### global.css               | Custom property | Masaüstü | Mobil |
## Sub-component'ler         | Ad | Durumlar | Prop'lar | Animasyonlar |
## Section'lar
### <Key>                    şablon · bayraklar · prop tablosu | Prop | Tip | Varsayılan | Grup | Katman |
                             çocuklar · veri bağlı metinler · kod metinleri · animasyonlar · frame'ler · overlay'ler
## Sayfalar                  | Sayfa | ikas sayfa tipi | Section'lar (sırayla) |
## Animasyon hedefleri       impl'e göre sayılar; tam liste JSON'da
## Kapsama denetimi          (§5)
## Davranış kabul kriterleri  - [ ] **PB-nn · başlık** — kural *Test:* adımlar   (10-port-behaviour.md)
## Açık sorular              numaralı liste
```

## 3. Globals runbook (`globals-runbook.md`)

Follows the geeny `prompts/00-globals.md` pattern: read → table → **user approval** → create → re-list. Turkish. Preconditions: `ikas theme dev` running, editor connected, the session started from the theme folder that holds `.mcp.json` (otherwise the MCP tools are absent).

1. **Read.** `list_theme_globals` → note every existing colour, typography, breakpoint, keyframe, scheme and global variable.
2. **Token table.** One row per manifest global: `| Tür | Ad | Değer | pen.dev kaynağı | Durum |`, Durum ∈ `yeni`, `var (aynı)`, `çakışma`. Reuse existing tokens; a `çakışma` row is an open question, not an overwrite.
3. **Approval.** Show the count per kind and the table; **wait for the user**. Nothing is created before an explicit yes.
4. **Create** with `create_theme_global`, in this order, Turkish display names `Grup / Ad`:
   ```json
   {"kind":"breakpoint","name":"Kırılım / Mobil","width":767}
   {"kind":"color","name":"Renk / Vurgu","value":"#FF3B1F"}
   {"kind":"colorScheme","name":"Örnek / Kağıt","colors":[{"newSlotName":"Background","value":"#EFEBE2"},{"newSlotName":"Text","value":"#0D0D0D"}]}
   {"kind":"typography","name":"Tipografi / Display","font_family":"Sofia Sans Extra Condensed","font_size":"168px","font_weight":"800","line_height":"0.9"}
   {"kind":"globalVariable","display_name":"Çizgi / Varsayılan","type":"BORDER","value":{"width":{"value":2,"unit":"px"},"style":"solid","color":"#0D0D0D"}}
   {"kind":"keyframe","name":"Animasyon / Marquee","points":[{"point":"0%","styles":[{"property":"transform","value":"translateX(0)"}]},{"point":"100%","styles":[{"property":"transform","value":"translateX(-50%)"}]}]}
   ```
   - Breakpoints first (laptop/tablet/mobile from `globals.md` §4), so CSS can use `bp(<id>)`.
   - `mode` axis → one colour scheme per palette; the second palette targets the slots created by the first via `slotId` (re-list in between).
   - Colour schemes from `globals.md` §1a: slots first (names), then one palette per scheme; record each section's default scheme.
   - Typography tokens carry the desktop size; the laptop / tablet / mobile values of `globals.md` §2a are applied with `update_text_style` + `breakpoint_id`. No `text-transform`.
   - Layout at 992–1199 and 768–991 follows `globals.md` §4a, written in component CSS under `@media (max-width: bp(<id>))`.
   - Spacing, sizes, opacity and transition strings go to `src/global.css` (listed in the runbook as a code block) or `globalVariable TEXT`; there is no spacing/radius kind.
5. **Verify.** `list_theme_globals` again; every row is present once; fill the live table (§4). The runbook is consumed once — re-running it duplicates tokens.

## 4. Live token table (filled by the port)

The runbook ends with an empty table per kind, filled from the second `list_theme_globals` (geeny `prompts/TOKENS.md` shape). Code reads live ids only from here, never from display names.

```
### Renkler (kind: color)            | Token adı | ID | cssVar |
### Tipografi (kind: typography)     | Token adı | ID | className |
### Global değişkenler               | Token adı | variableName | Tip |
### Kırılımlar (kind: breakpoint)    | Token adı | ID | Genişlik | Kullanım |   (@media (max-width: bp(<id>)))
### Renk şemaları (kind: colorScheme)| Palet | ID | className |  +  | Slot | slotId | cssVar |
### Keyframe'ler (kind: keyframe)    | Token adı | ID | ref (animation-name) |
```

Every row starts as `| <ad> | _doldurulacak_ | _doldurulacak_ |`. Use the exact `cssVar` string (its casing can differ from the id).

## 5. Coverage audit

`port-manifest.md` §Kapsama denetimi (geeny `GLOBALS.md` coverage pattern), one bullet per Section and Sub: `**<Key>** → kullanılan token'lar: <names>` from the `$variable` references in its plan tree and style lines, mapped to manifest global names. Then four checks, each `geçti` / `kaldı` with the offending items:
1. Every manifest global is used by at least one component (unused → drop or justify).
2. Every `$variable` used on the canvas maps to a manifest global or a `global.css` property.
3. Every page type in scope (`docs/00-brief.md`) has a page with a template or `(özel)` section (`06-page-coverage.md` §2).
4. Every anim target has an `impl` from the allowed vocabulary and, if it needs a shared keyframe, a matching `keyframes[]` entry.

## 6. What a future `ikas-port` skill may rely on

Stable (changing any of these is a breaking change → `schema` 2):
- `port-manifest.json` keys and meanings in §1.
- The 41 core variable names and their axes (`02-contract.md`); prefix + root-name grammar (`P/Sub/<Name>`, `P/Section/<Key>@device`, `P/Overlay/<Name>@device — <state>`, `P/Page/<Name>@device`).
- Root name → component name; layer name (kebab-case) → CSS class; `metadata.prop` + `propType` → config prop; `textClass` `data` + `source` vocabulary → store binding; `code` → generated text.
- Anim id grammar, anim-targets YAML keys and the `impl` vocabulary (`03-motion.md`).
- The globals runbook order and the approval step.
- `behaviour` ids (`PB-nn`) and `seed` ids (`S-nn`): an id keeps its meaning; a retired criterion leaves its id unused.

Not stable: node ids, canvas coordinates, sample copy and imagery on the canvas (sample content, never defaults), anything under `openQuestions`.
