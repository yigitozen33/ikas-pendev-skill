# 03 — Motion

pen.dev draws still frames; ikas runs the motion. This file defines how a still design must be built so that every animation can be added later without rebuilding layers, and the shared vocabulary (tokens, implementation paths, recipe catalogue, target schema) used by the plan, the lint and the port.

## Contents

1. The 12 animation-ready rules
2. Motion tokens
3. Implementation paths, SSR and reduced motion
4. Recipe catalogue M-01 … M-28 (+ defaults)
5. Motion-state frames
6. Local recipe template
7. `anim-targets` schema
8. Shared utilities

---

## 1. The 12 animation-ready rules

Layer names stay as written (kebab-case, they become CSS classes).

1. **Draw the end state.** Section and page frames show the view *after* the animation has finished. Start and intermediate states exist only in `P/Motion/…` frames.
2. **Mask = `clip: true` frame.** Every text line that slides in sits inside its own `…-mask` frame of the same size. A multi-line heading has one text node and one mask per line.
3. **Rolling elements are double copies.** Buttons, nav links and arrow icons draw a `top` (visible) and a `bottom` (waiting outside the mask) copy together; the container is `clip: true`.
4. **Infinite scrollers are track + copies.** The `marquee` / `ticker` container is `clip: true`; its `…-track` holds the content set at least twice and overflows the container.
5. **Swapping content is sibling frames.** Slides, tab panels, front/back product images are stacked in the same parent (`layout: "none"`); hidden ones stay at `opacity: 0`, never deleted.
6. **Progress indicators are their own layer.** The `progress-bar` fill is a separate rectangle from its track, drawn half full.
7. **Sticky areas are drawn at real height.** The container of a sticky element is as tall as the distance it travels while scrolling (e.g. one detail column beside a 4-image gallery).
8. **Overlays are separate roots.** Menu, drawer, search: `scrim` + panel in their own root frame, not on a copy of a page; open and empty/filled states are separate roots.
9. **Scroll-driven elements are free layers.** Rotating/sliding images and parallax backgrounds are out of flow (`layoutPosition: "absolute"`) and drawn larger than their container.
10. **Hover states are separate frames.** Each interactive component's hover state is drawn once as `P/Sub/<Name> — hover`, never again inside sections.
11. **Every target is marked.** Every `layer` named in an `anim-targets` block exists in the design with exactly that name and carries `metadata.anim` (plus the id in `context`).
12. **The mobile state is decided.** When a target's `mobile` field says off or different, the mobile frame is drawn that way (e.g. no sticky → normal flow). Touch has no hover: content a hover or expand recipe reveals on desktop is drawn open on `@mobile`, with the whole card as the tap target, and the target's `mobile` field says so (`açık; kartın tamamı bağlantı`). See `SKILL.md` rule 14 and `06-page-coverage.md` §3d.

## 2. Motion tokens

Token names are fixed (recipes reference them); values come from the reference measurement in `globals.md` §7.1 and may be re-measured per theme. Defaults below are the ornek reference values.

| Token | Default value | Use |
|---|---|---|
| `ease-standard` | `cubic-bezier(.4, 0, .2, 1)` | load, general tween |
| `ease-inout` | `cubic-bezier(.44, 0, .56, 1)` | progress bar, section entrance |
| `ease-nav` | `cubic-bezier(.68, 0, .22, .83)` | header / megamenu |
| `spring-snappy` | spring bounce 0, 0.3s | small hover |
| `spring-soft` | spring bounce 0.2, 0.4s | most common: arrow, label, small state change |
| `spring-hover` | spring bounce 0.2, 0.6s | nav fill, menu item |
| `spring-smooth` | spring bounce 0, 0.6s | image hover, thumbnail |
| `spring-card` | spring bounce 0.2, 0.8s | category card |
| `spring-hero` | spring bounce 0, 1.5s | slider mask + zoom |
| `spring-text` | spring bounce 0.2, 1.5–2s | word reveal |
| `spring-drawer` | stiffness 300, damping 40, mass 1 | drawer |
| `spring-search` | stiffness 600 / 800, damping 40 / 60 | search panel / field |
| `spring-ui` | stiffness 500, damping 60, mass 1 | general UI |
| `dur-autoplay` | 4s | hero slide duration |
| `dur-press` | 3s | press slider interval |

CSS equivalents where AnimeJS is not used: bounce 0 → `cubic-bezier(.22, 1, .36, 1)`; bounce 0.2 → `cubic-bezier(.34, 1.3, .64, 1)`. For a real spring: `AnimeJS.createSpring({ stiffness, damping, mass })`. Tokens become `--ease-*` / `--dur-*` custom properties in `src/global.css`.

## 3. Implementation paths, SSR and reduced motion

| `impl` | What | When |
|---|---|---|
| `css-transition` | `:hover` / state class + `transition` | hover, open/close, colour |
| `css-keyframes` | `@keyframes` in the component's `styles.css` | infinite loops (marquee, pulse). Names are renamed per component → **each component defines its own keyframes** |
| `theme-keyframe` | `create_theme_global` kind `keyframe`, `animation-name: <ref>` | keyframes shared by several components |
| `io-hook` | `IntersectionObserver` in `useEffect` → `is-inview` class | entrance triggered once on visibility |
| `animejs` | `import { AnimeJS } from "@ikas/bp-storefront"` (v4), inside `useEffect` | stagger, timeline, spring, word splitting |
| `scroll-scrub` | scroll listener + `requestAnimationFrame` → CSS variable, in `useEffect` | progress bound to scroll |
| `layout` | `position: sticky` | layout behaviour, not animation |
| `setInterval` | timer in `useEffect` (cleared on unmount) | countdowns, timed text swaps |
| `pointermove` | pointer listener in `useEffect` | cursor-follow effects |
| `rAF` | `requestAnimationFrame` loop | smoothing (lerp) for pointer/scroll effects |

Combine with ` + ` (`animejs + io-hook`, `layout + scroll-scrub`). `gsap`, `lenis`, `framer-motion` (and any other package) are **errors**: allowed packages are `preact`, `mobx`, `@ikas/bp-storefront*`, `@ikas/component-utils`, `animejs`, `three`.

Shared rules:
- Browser APIs (`window`, `document`, observers, timers) only inside `useEffect` — the storefront renders on the server.
- SSR output shows the **end state**; the start state is applied by a class added once JS has loaded. Otherwise content stays invisible without JS.
- `prefers-reduced-motion: reduce`: loops stop, entrances are instant, scroll-scrub is off; the target's `reducedMotion` field says exactly what happens.
- The target's `mobile` field becomes a `@media (max-width: bp(<mobileId>))` block.

## 4. Recipe catalogue M-01 … M-28

The "Required layer structure" column is **mandatory** in the pen.dev design whenever the recipe is used.

| ID | Name | Motion & values | Required layer structure | Impl | Mobile / reduced motion |
|---|---|---|---|---|---|
| M-01 | Load fade-up | `y 40→0`, `opacity 0→1`; 0.5s `ease-standard`; delay 0.2–0.4s | target is one layer | css-keyframes | same / instant |
| M-02 | Load fade | `opacity 0→1`; spring 1.2s, delay | one layer | css-keyframes | same / instant |
| M-03 | Word-by-word heading reveal | per word `opacity 0→1`, `y 50→0`, `rotateX 20→0`, `skewX 10→0`, `skewY 5→0`; `spring-text`; stagger 0.05s; threshold 0.5; once | each heading line in its own `clip` mask; one text node per line | animejs + io-hook | y + opacity only / instant |
| M-04 | Announcement rotation | texts swap by sliding vertically, ~3s, `spring-hover` | `announcement-mask` (clip) with all texts stacked, only the first visible | css-keyframes or animejs timeline | inside mobile menu / first text fixed |
| M-05 | Nav hover fill + label roll | inverse layer slides `y 100%→0`, label rolls up; `spring-hover` | `nav-link` (clip) with `top` (normal) and `bottom` (inverse bg + text) copies | css-transition | off on mobile |
| M-06 | Megamenu open/close | panel opens downward (height/clip), caret turns 180°; `spring-soft` + `ease-nav` 0.4s | `megamenu` as its own overlay root: links + cards (image + `gradient-mask` + text) | css-transition | accordion / instant |
| M-07 | Hero slide transition | new slide opens with a **mask wipe** (width `0→100%`, `spring-hero`); image `scale 1.2→1`; text swaps with delay | `hero-slides` with every slide as a sibling: `hero-slide-mask` (clip) → `hero-slide-image` → `gradient-mask`; text block separate `hero-text` | animejs timeline | crossfade / instant swap |
| M-08 | Thumbnail progress | active bar `0→100%` over `dur-autoplay`, `ease-inout`; reset 0.6s; inactive `opacity-inactive` | separate `progress-bar` layer inside `hero-thumb` | css-transition | one thin line / bar hidden |
| M-09 | Product card hover | front → back image ~0.4s; arrow diagonal roll `spring-soft` | `card-images` (clip) with stacked `image-front` + `image-back`; `card-arrow` (clip) with `arrow-top` + `arrow-bottom` | css-transition | off on touch / instant |
| M-10 | Arrow link hover | arrow rolls diagonally + underline `0→100%`, 0.4s | `link`: text + `link-line` (1px) + `link-arrow` (clip, two arrows) | css-transition | off |
| M-11 | Button hover fill | as M-05; spring bounce 0.3, 0.4s | `button` (clip) with `top` + `bottom` copies | css-transition | off / instant colour change |
| M-12 | Hotspot pulse + card | outer ring `scale 1→2.2`, `opacity 1→0`, loop 1–1.5s; tap/hover opens mini card `spring-soft` | `hotspot` with `hotspot-outer` + `hotspot-inner`; `hotspot-card` hidden when closed, open state in Motion frames | css-keyframes + css-transition | opens on tap / pulse stops |
| M-13 | Sticky panel | panel stays at `top: size-header` while neighbour scrolls | sticky element and its tall container drawn at **real height** | layout | no sticky on mobile |
| M-14 | Text marquee | infinite horizontal slide ~60px/s; card hover `muted→text` | `marquee` (clip) → `marquee-track` with ≥2 copies, overflowing | css-keyframes | same / stops |
| M-15 | Image ticker | images slide infinitely, draggable, slow on hover | `ticker` (clip) → `ticker-track` → images ×2 sets | css-keyframes (+ optional drag) | same / stops, horizontal scroll |
| M-16 | Footer reveal | footer sticky behind content, revealed at the end; wordmark parallax | `footer` own section, drawn in normal flow; `footer-wordmark` separate layer | layout + scroll-scrub | normal flow |
| M-17 | Smooth scroll | **FORBIDDEN** — Lenis is not an allowed package; never plan, lint rejects it | — | — | — |
| M-18 | Filter bar | sticky `top: header`; tab colour `muted→text` 0.3s; short fade on grid change | `filter-bar` separate layer; active/inactive tab styles separate | layout + css-transition | horizontal scroll |
| M-19 | PDP gallery scrollspy | detail column sticky; active thumbnail border follows scroll; mini buy bar slides in after gallery | `pdp-details` (sticky), `pdp-gallery` (images stacked, real height), `pdp-thumbs`, `mini-buy-bar` as overlay | layout + io-hook | horizontal gallery + dots |
| M-20 | Drawer | panel slides in from edge (`x 100%→0`), `spring-drawer`; scrim fade + blur 0.4s; rows stagger 0.2–0.5s | own overlay root: `scrim` + `drawer` (header, body, footer as separate layers) | css-transition + animejs | full width / instant |
| M-21 | Search | panel opens with `spring-search`; results list | own overlay root: `search-panel` (field + result grid), empty and filled separate | css-transition | full screen / instant |
| M-22 | Accordion | height `0→auto`, plus icon rotates; spring bounce 0, 0.5s | `faq-item`: `faq-question` row + `faq-answer`; open and closed separate | css-transition (grid-rows) | same / instant |
| M-23 | Scroll-scrub image | `rotate 10°→0°`, `y 0→-1200` bound to scroll | sticky stack: each `value-panel` full viewport; `value-image` absolute, drawn at **end (0°)** | scroll-scrub | no rotation, normal flow / off |
| M-24 | Scroll-scrub text | title `opacity 1→0`, `scale 1→1.2`; paragraph `y 0→-200` | title and paragraph separate layers | scroll-scrub | off / off |
| M-25 | Scrollspy nav | fixed bar; visible section name `muted→text` | `anchor-nav` separate layer; active/inactive styles separate | io-hook + css-transition | horizontal scroll |
| M-26 | Quote slider | auto 3s, draggable; centre opaque, sides 0.4 | `press-track` with all quotes side by side; centre active | animejs or CSS scroll-snap | scroll-snap / autoplay stops |
| M-27 | Hero parallax | background moves slower than content | `hero-bg` separate layer, 10–20% taller than container | scroll-scrub | off |
| M-28 | State colour | `muted→text` 0.3s (tab, footer link, variant chip) | active/inactive/hover styles separate | css-transition | same |

**Defaults** used by `gen_plan.py` when a target gives no override (strings in `mobile`/`reducedMotion` are Turkish because they are copied into the plan verbatim). These must stay identical to `RECIPES` in `scripts/gen_plan.py`.

| ID | from | to | timing | impl | mobile | reducedMotion |
|---|---|---|---|---|---|---|
| M-01 | `{ y: 40, opacity: 0 }` | `{ y: 0, opacity: 1 }` | `{ duration: 0.5, ease: ease-standard, delay: 0.2 }` | css-keyframes | aynı | anında |
| M-02 | `{ opacity: 0 }` | `{ opacity: 1 }` | `{ spring: "bounce 0, 1.2s", delay: 0.3 }` | css-keyframes | aynı | anında |
| M-03 | `{ opacity: 0, y: 50, rotateX: 20, skewX: 10, skewY: 5 }` | `{ opacity: 1, y: 0, rotateX: 0, skewX: 0, skewY: 0 }` | `{ spring: spring-text, stagger: 0.05, threshold: 0.5, once: true }` | animejs + io-hook | sadece y + opacity | anında |
| M-04 | `{ y: 100% }` | `{ y: 0 }` | `{ interval: 3, spring: spring-hover }` | css-keyframes | mobil menü içinde | ilk metin sabit |
| M-05 | `{ bottom.y: 100% }` | `{ bottom.y: 0, top.y: -100% }` | `{ spring: spring-hover }` | css-transition | kapalı | anında renk değişimi |
| M-06 | `{ clipHeight: 0, caret.rotate: 0 }` | `{ clipHeight: 100%, caret.rotate: 180 }` | `{ spring: spring-soft, ease: ease-nav, duration: 0.4 }` | css-transition | akordeon | anında |
| M-07 | `{ mask.width: 0%, image.scale: 1.2 }` | `{ mask.width: 100%, image.scale: 1 }` | `{ spring: spring-hero, text.delay: 1, text.spring: "bounce 0, 1.2s" }` | animejs | çapraz geçiş 0.6s | anında değişim |
| M-08 | `{ width: 0% }` | `{ width: 100% }` | `{ duration: 4, ease: ease-inout, reset: 0.6 }` | css-transition | tek ince çizgi | çubuk gizli |
| M-09 | `{ front.opacity: 1, back.opacity: 0 }` | `{ front.opacity: 0, back.opacity: 1 }` | `{ duration: 0.4, ease: ease-standard, arrow.spring: spring-soft }` | css-transition | kapalı (dokunmatik) | anında |
| M-10 | `{ line.width: 0%, arrow: top }` | `{ line.width: 100%, arrow: bottom }` | `{ duration: 0.4, spring: spring-soft }` | css-transition | kapalı | anında |
| M-11 | `{ bottom.y: 100% }` | `{ bottom.y: 0, top.y: -100% }` | `{ spring: "bounce 0.3, 0.4s" }` | css-transition | kapalı | anında renk değişimi |
| M-12 | `{ outer.scale: 1, outer.opacity: 1 }` | `{ outer.scale: 2.2, outer.opacity: 0 }` | `{ duration: 1.5, loop: true, card.spring: spring-soft }` | css-keyframes + css-transition | dokunmayla açılır | pulse durur |
| M-13 | `{}` | `{ position: sticky, top: size-header }` | `{}` | layout | sticky yok | aynı |
| M-14 | `{ x: 0 }` | `{ x: -50% }` | `{ speed: "60px/s", ease: linear, loop: true }` | css-keyframes | aynı | durur |
| M-15 | `{ x: 0 }` | `{ x: -50% }` | `{ speed: "40px/s", ease: linear, loop: true, hoverSlow: true }` | css-keyframes | yatay kaydırma | durur |
| M-16 | `{ wordmark.y: -80 }` | `{ wordmark.y: 0 }` | `{ scrub: true }` | layout + scroll-scrub | normal akış | normal akış |
| M-18 | `{ color: color-muted }` | `{ color: color-text }` | `{ duration: 0.3 }` | layout + css-transition | yatay kaydırma | anında |
| M-19 | `{ thumb.border: none, bar.y: 100% }` | `{ thumb.border: color-text, bar.y: 0 }` | `{ duration: 0.3, bar.spring: spring-soft }` | layout + io-hook | yatay galeri + noktalar | anında |
| M-20 | `{ x: 100%, scrim.opacity: 0 }` | `{ x: 0, scrim.opacity: 1 }` | `{ spring: spring-drawer, scrim.duration: 0.4, rows.stagger: [0.2, 0.3, 0.4, 0.5] }` | css-transition + animejs | tam genişlik | anında |
| M-21 | `{ y: -100%, opacity: 0 }` | `{ y: 0, opacity: 1 }` | `{ spring: spring-search }` | css-transition | tam ekran | anında |
| M-22 | `{ height: 0, icon.rotate: 0 }` | `{ height: auto, icon.rotate: 45 }` | `{ spring: "bounce 0, 0.5s" }` | css-transition | aynı | anında |
| M-23 | `{ rotate: 10, y: 0 }` | `{ rotate: 0, y: -1200 }` | `{ scrub: true }` | scroll-scrub | kapalı, normal akış | kapalı |
| M-24 | `{ opacity: 1, scale: 1, text.y: 0 }` | `{ opacity: 0, scale: 1.2, text.y: -200 }` | `{ scrub: true }` | scroll-scrub | kapalı | kapalı |
| M-25 | `{ color: color-muted }` | `{ color: color-text }` | `{ duration: 0.3 }` | io-hook + css-transition | yatay kaydırma | anında |
| M-26 | `{ side.opacity: 0.4 }` | `{ center.opacity: 1 }` | `{ interval: 3, spring: spring-smooth, drag: true }` | animejs | scroll-snap | otomatik durur |
| M-27 | `{ bg.y: 0 }` | `{ bg.y: 20% }` | `{ scrub: true }` | scroll-scrub | kapalı | kapalı |
| M-28 | `{ color: color-muted }` | `{ color: color-text }` | `{ duration: 0.3 }` | css-transition | aynı | anında |

A plandata target may override any of `from`, `to`, `timing`, `impl`, `mobile`, `reducedMotion` (e.g. Header `cart-count` uses M-01 with `{ scale: 1.4 } → { scale: 1 }`, `spring-soft`).

## 5. Motion-state frames

Recipes whose motion cannot be read from the end state get one `P/Motion/<recipe> <section>` root on **one** example (2–3 frames left to right, a `note` under each with the % / moment). Other uses follow the same logic. The generator picks the first non-Sub target of the recipe, preferring one without a `from` override. Every local recipe (`P-M-NN`) also gets one.

| Recipe | Frames to draw (hint copied into plan §6.5) |
|---|---|
| M-03 | başlık: kelimeler maske altında (görünmez) → yarısı girmiş → hepsi yerinde |
| M-05 | nav-link: varsayılan → dolgu yarı yolda → tam ters dolgu |
| M-06 | megamenu: kapalı → yarı açık → açık |
| M-07 | slayt geçişi: eski slayt → maske %50 (iki görsel yan yana) → yeni slayt |
| M-09 | ürün kartı: ön görsel → arka görsel + dönmüş ok |
| M-11 | buton: varsayılan → dolgu yarı yolda → ters dolgu |
| M-12 | hotspot: halka küçük → halka büyük ve soluk; ayrıca mini kart açık |
| M-20 | çekmece: kapalı (sayfa) → yarı açık + scrim → açık |
| M-21 | arama: kapalı → açık boş → açık sonuçlu |
| M-22 | akordeon: kapalı → açık |
| M-23 | değer paneli: görsel 10° dönük ve aşağıda → 5° → 0° ve yerinde |
| M-24 | değer başlığı: tam opak → büyümüş ve yarı saydam → görünmez |

Local recipes supply their own hint in plandata (ornek examples: `metin: tamamen karışık karakterler → yarısı çözülmüş → gerçek metin`; `şerit: baş konum → orta → son kare`).

## 6. Local recipe template

A plan may add recipes the catalogue lacks (the theme's signature motion). They go in plan §5.1, Turkish prose, ids `P-M-01`… in order. Columns:

| ID | Ad | Hareket | Zorunlu katman yapısı | Uygulama | Mobil | Azaltılmış hareket |
|---|---|---|---|---|---|---|
| **P-M-01** | Şifre çözme (scramble) | what moves + `{ from } → { to }`, `{ timing }` in one cell | the layers the designer must draw (masks, copies, fixed-width box) | impl vocabulary of §3 | off / simplified | instant / off |

Rules: one signature recipe is enough (see `08-quality.md`); every local recipe must be implementable with §3 paths only; its required structure obeys §1; it gets a Motion frame (§5) and, if it needs shared code, a row in §8.

## 7. `anim-targets` schema

Each section/sub in plan §6.1–§6.2 ends with a block between `<!-- anim-targets:start -->` and `<!-- anim-targets:end -->` containing a YAML list:

```yaml
- id: P-HERO-01          # §7 of 02-contract
  section: HeroSplit     # section key, or Sub/<Name> for component targets
  layer: curtain         # layer name present in this section's tree (word boundary)
  via: Button            # optional: the Sub that owns the motion code
  recipe: P-M-02         # catalogue M-xx (not M-17) or local P-M-NN
  trigger: auto | click
  what: "Yeni görsel alttan perdeyle açılır"
  from: { clip: "inset(100% 0 0 0)", image.y: 10% }
  to: { clip: "inset(0)", image.y: 0 }
  timing: { duration: 1.0, ease: ease-inout, interval: 5 }
  impl: animejs
  mobile: çapraz geçiş 0.5s
  reducedMotion: anında değişim
  done: false
```

| Key | Required | Vocabulary |
|---|---|---|
| `id`, `section`, `layer`, `recipe`, `trigger`, `what`, `from`, `to`, `timing`, `impl`, `mobile`, `reducedMotion`, `done` | yes (13) | `done` is `false` until the port implements it |
| `via` | no | Sub name that owns the motion |
| `trigger` | — | `load`, `inview`, `hover`, `click`, `drag`, `state-change`, `auto`, `auto-loop`, `scroll-scrub`, `sticky`; combine with ` \| ` (`hover \| click`, `auto \| drag`) |
| `impl` | — | §3 vocabulary joined with ` + ` |
| `mobile` | — | Turkish free text; `aynı` (same), `kapalı` (off) or the different behaviour |
| `reducedMotion` | — | Turkish free text; `anında`, `kapalı`, `durur` or the fallback |

`via` defaults the generator applies by layer name: `link`→ArrowLink, `hotspot`/`hotspot-outer`→Hotspot, `marquee-track`→Marquee, `section-title`→SectionHeading, `faq-answer`→AccordionItem, `filter-tab`→Tabs, `variant-chip`→VariantChip, `image-back`/`card-arrow`/`card-spec`→ProductCard, and any `*button*` layer with M-11→Button. A target with `via` is implemented once inside that Sub, not again in the section.

## 8. Shared utilities

Written once during the port (`src/`), listed in plan §8 step 3. Generic rows; the plan appends one row per local recipe that needs code.

| Piece | Location | Targets |
|---|---|---|
| Motion custom properties (`--ease-*`, `--dur-*`) | `src/global.css` | all |
| `useInView(ref, {threshold, once})` | `src/utils/motion/useInView.ts` | `impl` contains `io-hook` |
| `useScrollProgress(ref)` → CSS variable | `src/utils/motion/useScrollProgress.ts` | `impl` contains `scroll-scrub` |
| `splitWords(el)` + AnimeJS stagger | `src/utils/motion/revealWords.ts` | M-03 |
| `Marquee`, `Button`, `ArrowLink`, `Hotspot`, `AccordionItem`, `Drawer` | `src/sub-components/<Name>/` | targets with `via` |
| *(per local recipe)* e.g. `scrambleText(el, opts)` | `src/utils/motion/<name>.ts` | `P-M-NN` |

Port order per section: `layout` → `css-transition` → `css-keyframes` → `io-hook` → `animejs` → `scroll-scrub`. Overall: `via` subs → Header → home sections → listing/detail → overlays → content pages → scroll-scrub ones.
