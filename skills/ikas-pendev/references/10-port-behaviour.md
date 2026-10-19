# 10 · Port behaviour — acceptance criteria and seed data the handoff carries

The canvas fixes how the theme looks; it cannot fix how it behaves. Each criterion below is a defect that a finished theme shipped with on its first build and that only showed up when a reviewer clicked through the live store. The skill writes no code, so the handoff carries these criteria to the port as a checklist, together with the store data needed to test them.

## Contents
1. Where the list lives
2. Criteria
3. Seed data
4. Testing protocol

## 1. Where the list lives

`scripts/data/port-behaviour.json` is the single list. Each entry has an id (`PB-nn` for behaviour, `S-nn` for seed), a Turkish title, rule and test text, and its scope: `keys` (Section, Overlay or Sub names) and `pageTypes` (ikas page types). An entry with both empty always applies. `build_manifest.py` copies every entry whose scope matches the plan into `port-manifest.json` (`behaviour`, `seed`), renders the criteria in `port-manifest.md` under **Davranış kabul kriterleri** and writes `seed-checklist.md`. The port ticks every criterion before the handoff counts as done.

Add a criterion when a review finds a behaviour defect that the canvas could not have prevented. Write the rule so it can be checked by clicking, give it the narrowest scope that still catches it, and, if it needs store data to reproduce, add or extend a seed entry and list the criterion in that entry's `for`.

## 2. Criteria

| Id | Scope | Why it exists |
|---|---|---|
| PB-01 | always | Focus rings appeared after every mouse click on header items and overlay buttons. Keyboard users need them; mouse users read them as a bug. |
| PB-02 | always | The ikas Router follows `<a>` clicks even after `preventDefault`, so in-page chips and swatch links navigated away. |
| PB-03 | ProductCard | Section CSS loads in chunks in varying order; a Section rule that loaded later overrode the card's favourite position in some lists only. |
| PB-04 | ProductCard; CATEGORY, SEARCH | With "show variant values separately" on, cards shared one key and one link, so lists flickered and every card opened the same colour. |
| PB-05 | ProductCard, QuickBuy | Colours could only be explored inside QuickBuy, and QuickBuy opened with no colour chosen and the size group already in its error style. |
| PB-06 | ProductCard, QuickBuy | A personalised product's card looked like a one-click add but led to the product page; shoppers skimming the button missed why. Only a required field sends the shopper there. |
| PB-07 | MenuOverlay, Header | The mobile menu dropped the mega menu column titles, so links from different groups ran together with uneven gaps. |
| PB-08 | always | Activity cards that open on hover stayed closed on touch, where there is no hover, and only a small link inside them navigated. |
| PB-09 | BLOG, BLOG_CATEGORY | The blog category page listed every post and marked no tab, and a low list limit cut posts off. |
| PB-10 | SearchOverlay, Header | Popular search chips linked to the bare search page instead of searching for their label. |
| PB-11 | ProductList; SEARCH | The search page had no field of its own; once added, the URL sync overwrote what was being typed. |
| PB-12 | always | A fold that started open in unstyled HTML played its close animation on page load when the CSS arrived late. |
| PB-13 | ProductList; CATEGORY, SEARCH | The result count showed twice on one layout and nowhere on another after the search field moved it. |
| PB-14 | always | Category page, mobile menu and account panels used more and harsher dividers than the footer (`08-quality.md` §8). |
| PB-15 | QuickBuy | QuickBuy sent every product with an option set or a bundle to the product page, because list data carries neither and add-to-cart rejects a product whose set is not loaded. |
| PB-16 | ProductDetail, QuickBuy, CartPage, CartDrawer | Every personalisation upload failed with "Dosya yüklenemedi": the upload set the multipart header by hand and storage rejected it. Once fixed, the cart line printed the file's full storage URL. |
| PB-17 | CartPage, CartDrawer, QuickBuy | Editing a cart line always opened the product page with an update button that shoppers missed; replacing a line by remove-then-add made the cart flash empty. |
| PB-18 | ProductDetail; PRODUCT_DETAIL | The thumbnail rail was stretched to the gallery's height, so the wheel over its empty lower part tried to scroll the rail and the page stopped. |
| PB-19 | ProductReviews; PRODUCT_DETAIL | The form always said the review would appear after approval, while the store auto-approved and showed it at once; the summary then counted the new review twice. |
| PB-20 | ProductReviews; PRODUCT_DETAIL | Clicking a star never selected it in Chrome: focusing the button reset the hover fill under the pointer, the press target vanished between mousedown and mouseup and no click fired. |
| PB-21 | always | The footer's marquee images loaded with the page and a pixelated footer photo carried text with no veil; both hurt first load (LCP) and legibility. |
| PB-22 | Footer | The footer newsletter had no consent checkbox, so stores that need explicit permission (KVKK / commercial messages) could not use it. |
| PB-23 | StoreLocator, ContactForm | The store list rebuilt itself in a loop, so hovering one store made the first one jump and the feature image went blank. |
| PB-24 | ProductList, FilterDrawer; CATEGORY, SEARCH | The price slider could not be held and dragged: the list refetched on every step, so the handle jumped back. |

The design-side counterpart of PB-03 to PB-11 and PB-13 is `06-page-coverage.md` §3d; of PB-14, `08-quality.md` §8; of PB-08, `SKILL.md` rule 14.

## 3. Seed data

The criteria cannot be tested on an empty store. `seed-checklist.md` lists the products, blog posts, menu and links the port creates before testing: a split multi-variant product with a sold-out value (S-01), a product with a required personalisation field (S-02), a product with no variants (S-03), a multi-colour product shown normally (S-04), two blog categories with three posts (S-05), a mega menu with three column titles (S-06) and four popular searches that point at the search page (S-07).
- Added for QuickBuy: a product whose option set is entirely optional (S-08) and a bundle (S-09).
- Added for personalisation uploads: a product with a file-upload option (S-10).
- Added for reviews: the review approval setting, tested on and off (S-11).
- Added for the contact page: three stores, one without a photo (S-12).

- Seed data is created in the ikas admin panel (for example through Claude in Chrome, in the merchant's signed-in session) or through the ikas admin API. The agent never types the merchant's password; the merchant signs in.
- Seed content follows the theme's copy rules (`08-quality.md` §6): Turkish, the brand's voice, real-length names. Images come from the theme's imagery direction, never from the reference.
- Seed data lives in the merchant's dev store. Nothing from it goes into this skill's repository or examples.

## 4. Testing protocol

- **One page at a time, in one tab.** Test pages in sequence in a single browser tab; never open every page at once in parallel tabs or agents. The merchant's browser is shared.
- **Bypass the cache.** The storefront caches HTML; add a cache-busting query (`?cb=<n>`) and confirm the served build before judging a fix.
- **Both widths.** Every criterion is checked at desktop width and at a phone width (390). A resize that does not take effect is retried before the result is trusted.
- **Report per criterion.** The port's report lists each `PB-nn` as geçti / kaldı with what was clicked; a criterion with no store data to test it is reported as untested, not as passed.
