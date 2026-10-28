# 08 — Quality

What separates a designed theme from a generated one. Read before writing plan §1 (identity) and before declaring any section done.

## 1. Brief wins

`docs/00-brief.md` overrides every default in this file. If the brief asks for rounded cards, a centred hero or a purple gradient, build it and do not argue; the anti-patterns below are defaults to avoid when nobody asked, not rules against the user.

## 2. Named anti-patterns

| Name | Tell | Instead |
|---|---|---|
| **Card-around-everything** | every block sits in a rounded, padded, shadowed box | let sections sit on the ground; use lines, gutters or full-bleed media to separate |
| **Default chrome** | radius 8–16, soft `0 4px 20px` shadow, 135° two-colour gradient on hero/buttons | radius, shadow and gradient are decisions from `globals.md`; "yok" is a valid answer |
| **Drifting radius** | the same thing has different corners in different places: the product image is rounder in QuickBuy than on the card, a field is softer than the button beside it, one panel is square and the next rounded | one `$radius-*` role per kind of surface (`02-contract.md` §3); CHK `radius` and `hardcoded` |
| **Hero + three features** | centred headline, sub-line, two buttons, then three icon cards | a hero built from the brand's material (product, type, motion) and a section order from the brief |
| **Safe fonts** | Inter / Roboto / Open Sans because they are there | pick from the identity: a display face with character + a working UI face + optional mono; Google Fonts with `latin-ext` only |
| **Eyebrow labels** (hard rule, `SKILL.md` rule 11 — not overridable by the reference) | a small mono/uppercase line above a title: `01 / YENİ GELENLER`, `04 / BÜLTEN`, `KOLEKSİYON · 24 ÜRÜN`, `HESAP`, a coordinate over a name | let the heading open the section; carry the technical tone in the heading itself, in meta rows *below* or beside content, or in the signature motion. Do not add `index`/`eyebrow` props to SectionHeading or hero trees |
| **Emoji and doodles** | emoji as icons, hand-drawn squiggles, generic 3D blobs | one icon set (lucide/phosphor) at one size and stroke; logo via `Generate("svg")` |
| **Stock ikas widgets** | merchant blocks (option fields, offers, filters, reviews, account panels) drawn as generic browser-default forms or in a different visual language from the rest of the theme | build them from the theme's Subs and tokens; the same field height, radius, stroke and label style as every other form (`06-page-coverage.md` §3b) |
| **Filler copy** | English or lorem ipsum, "Welcome to our store" | Turkish copy in the brand's voice (§6) |
| **Fake proof** | invented stats ("10k+ happy customers"), testimonials with stock faces, fake press logos | only what the brief supplies; otherwise leave the section out or make it a prop with an empty default |
| **Identical rhythm** | every section = title, subtitle, 4-column grid, same padding | vary density and scale: one full-bleed, one tight list, one oversized type moment |
| **Guessed gaps** | the Hero touches the Header, the last section touches the Footer, the mobile Header sits 16 from the edge while every band sits 8, two-column splits at 24 / 40 / 48 / 64 / 80 | one spacing rule (`02-contract.md` §3b): page edge, header → first, section → section, last → footer, splits and grids each come from one token; CHK `spacing` |
| **Stock team** | smiling people around a laptop, handshake, office | imagery from the art direction in `P/DS/Imagery` |
| **Purple default** | violet-to-blue gradients, glassmorphism | colours from the reference analysis and the brief |
| **Soft hero** | a full-bleed photo that is blurry or pixelated on a large screen, or text on a busy photo with no veil | §9: files at 2× the frame, a `*-veil` layer with an opacity prop |
| **Line noise** | a rule under every heading, between every list row, around every panel and filter group, in full-strength `$color-line` | group with spacing first; keep a line only where it separates two things that would otherwise read as one, in the footer's style (§8). CHK `dividers` warns |

## 3. Identity = MASTER + per-section overrides

- **MASTER** is plan §1 ("Yön ve kimlik"): one concept word, the palette logic, the three type roles, the image language, the signature motion, and an explicit "differences from the reference" list. Every section inherits it.
- **Overrides** live only in each section's `**Desktop:**` and `**Mobil:**` lines in plan §6.2 (sizes, column split, what is hidden or reordered on mobile). A section never introduces a new colour, font or radius; if it needs one, change the MASTER and the variables.
- Colour schemes are declared once (`globals.md` §1a, `11-color.md`); a section in a non-default scheme is marked with `mode: "<scheme slug>"`.

Example (ornek plan C, condensed):

```
MASTER  Konsept "ŞİFRE": sokak fanzini; kağıt zemin, 2px siyah çizgi, bitişik kartlar (gutter 0),
        dar dev başlık + mono etiketler, tek vurgu turuncu-kırmızı; imza hareket = şifre çözme.
        Ters palet: Manifesto, Footer, MenuOverlay, TickerStrip.
Header  Desktop: iki satır; üstte vurgu zeminli şerit (32), altta 64'lük ana satır.
        Mobil:   şerit aynı; MENU solda, logo ortada, sepet sağda.
```

## 4. Distance from the reference

Set in intake (yorum stratejisi) and stated at the top of plan §1:

| Strategy | Keeps | Changes | Note |
|---|---|---|---|
| Aynı iskelet, yeni kimlik | grid, section order, motion language | palette, type, imagery, copy | default when the reference structure is good |
| Yakın klon | structure and measurements | imagery, copy, logo, name | warn: risky if the reference is a paid template and the theme will be sold |
| Serbest yorum | quality bar, one or two ideas | section composition, palette, signature motion | most original; needs a strong MASTER |

In every strategy the reference's images, logo, brand name and text are never used; `pendev_checks.js` CHK `refassets` flags fills from the reference host.

## 5. One place to spend boldness

Choose **one** signature and make it unmistakable: a single motion recipe (ornek: scramble text), or an extreme type scale, or one structural idea (adjacent cells with 0 gutter). Everything else stays quiet so the signature reads. Two signatures compete; three are noise. Record the choice in MASTER and in `P/DS/Motion`.

## 6. Turkish copy rules

- Uppercase with the Turkish alphabet: `İ` (not `I`) for `i`, `I` for `ı`: `İNDİRİM`, `KIŞ`, `ÇIKIŞ`. Test `İ Ş Ğ Ü Ö Ç ı` in every font on `P/DS/Typography`; replace a font that drops a glyph.
- Prices: thousands dot, no decimals unless needed, space + `TL`: `1.850 TL`, `850 TL`, `12.499,90 TL`. Old price struck through in `$color-muted`.
- Percent before the number: `%30 İNDİRİM`. Dates: `12 ŞUBAT 2026`, times `20:00`.
- Product names follow the pattern **evocative word + fit/material + garment (or product type)**, in the theme's sector: `GECE OVERSIZE HOODIE — 1.850 TL`, `SİS KARGO PANTOLON — 1.650 TL`. Write 8–12 per theme so grids do not repeat.
- Copy is the brand's voice, short and concrete; buttons are verbs (`SEPETE EKLE`, `HEPSİNİ GÖR`).
- Never reuse the reference's brand name, tagline, product names or any of its text.
- Every visible string is a prop, a data field or code (`02-contract.md` §6); sample copy is only the default value.

## 7. Self-critique gate

Before marking a section (or sub) done in `build-log.md`, take one screenshot and answer all four in the log line. Any "no" → fix first.

1. **Brief:** would the user recognise their brief and MASTER here, without being told which theme it is?
2. **Slop:** does it avoid every anti-pattern in §2 (unless the brief asked for it)?
3. **Rhythm:** is it visibly different in density or scale from the section above and below it?
4. **Real content:** with Turkish copy, real-length product names, prices and both devices, does anything clip, wrap badly or fall back to a default font?

## 8. Dividers

Lines are the cheapest way to separate things, so they multiply. A theme reads calmer when spacing does most of the grouping:

- **Spacing first.** A heading and its content, a filter group and its values, a menu title and its links are grouped by a smaller gap, not by a line.
- **One line per boundary.** A boundary gets one line, never a border on both neighbours. No line directly above or below a panel edge, a sticky bar's own border or a full-bleed image.
- **Soft colour.** Dividers inside content (list rows, filter groups, menu groups, account panels) use `$color-line` at about half strength: a softer variable in the palette, or the port's `color-mix(in srgb, var(--line) 50%, transparent)`. Full-strength `$color-line` is kept for structural edges (the header bottom, the footer top) and for inputs.
- **The footer's language everywhere.** There is no count limit. What matters is that every divider speaks one language: the same colour, thickness and spacing as the footer's dividers, on the category page, the mobile menu, the cart, the account panels and the blog. Review them together, not one by one.

## 9. Images

- **Sharp at its largest size.** An image is generated (or upscaled) to at least 2× the widest frame it fills at any device: a full-bleed 1440 frame needs a ≥ 2880 px wide file, a 720 card ≥ 1440 px. A soft or pixelated image is upscaled before the handoff, not after the merchant notices. The handoff lists every image with its frame size so the port uploads the full-resolution file.
- **Text over an image gets a veil.** Wherever text or controls sit on a photo (hero, footer banner, category tile, campaign card) a separate `*-veil` layer between them darkens or lightens the image, so the contrast gate (02 §10) passes on any photo the merchant uploads later. Its strength is a NUMBER prop (`overlayOpacity`, 0–100) with a sensible default; a veil that only covers the text's area (a centre or edge gradient) is fine.
- **No baked frames.** The file is a plain rectangle: no rounded corners, border, white margin or shadow inside the image (02 §3, radius roles).
- **Loading is part of the design.** Only the first large image of a page (usually the hero or the product's main image) loads at once; everything below the fold, and images that only appear on hover or inside a marquee, load when they come near the viewport (PB-21). Draw hover images as a separate hidden layer, so the port sees that they are not part of the first paint.

