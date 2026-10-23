# 06 · Page coverage — which pages, sections, overlays and states a theme must design

A reference site rarely shows every page an ikas store needs (the reference behind `examples/ornek` had no cart page, auth, account or 404). This file is the floor: intake pre-ticks the default scope, the plan's §6.3 lists every page in scope, and CHK `pages` / `overlays` compare the canvas against it.

## Contents
1. Global rules
2. Coverage matrix
3. Required overlays (3a QuickBuy · 3b merchant blocks · 3c storefront completeness · 3d cards, menu and search)
4. States
5. Sections the reference does not have
6. Custom pages

## 1. Global rules

- **Header + Footer on every page.** In ikas they are global (`isHeader` / `isFooter`) and render automatically; on the canvas every `P/Page/<Name>@device` still starts with a Header instance and ends with a Footer instance so the page reads complete.
- Pages contain **only Section instances** (`ref` to `P/Section/<Key>@<same device>`), in order, nothing loose (CHK `pages`).
- Each page exists at both widths: `P/Page/<Name>@desktop` (1440) and `@mobile` (390).
- One section per concern (product detail, reviews and carousels are separate sections); the same Section may appear on several pages (ProductList on Category, Collection, Search, Favorites).
- Page names on the canvas are English PascalCase (`Home`, `Category`, `Product`, `Cart`, `Account`, `Auth`, `NotFound`, `Search`, `Favorites`…); page-type ids are ikas enum names.

## 2. Coverage matrix

✓ = default in scope (pre-ticked in intake) · ○ = optional (asked in intake) · Templates: `04-ikas-constraints.md` §8.

| Page type | ikas template | Required sections (between Header and Footer) | Overlays | States to draw | Default |
|---|---|---|---|---|---|
| `INDEX` | `hero-slider-section`, `product-slider-section`, `category-images-section`, `features-section` or `(özel)` | hero · ≥1 product row (carousel or grid) · category entry · ≥1 brand/editorial block | Cart, Search, Menu, QuickBuy | hero slide n of N; product card states via Subs | ✓ |
| `CATEGORY` | `category-list-section` | ProductList (title, filter/sort bar, grid, pagination or load-more) | Cart, Search, Menu, QuickBuy, **FilterDrawer@mobile** | empty (no products), loading (skeleton / load-more spinner), filter applied | ✓ |
| `PRODUCT_DETAIL` | `product-detail-section` (+ `variant-selection`, `add-to-cart`, `product-pricing`, `image-handling`, `bundle-products`), `product-reviews-section`, `product-slider-section` | ProductDetail (gallery, name, rating, price, campaign message, variants, add-to-cart, Pay with ikas, **the merchant blocks of §3b**, description) · **ProductReviews** · ≥1 ProductCarousel/Grid (purchased together or related) · a second rail (last viewed) | Cart (after add), QuickBuy, size guide / info drawer if designed | variant selected / unavailable / out of stock (+ back-in-stock form) · add-to-cart loading / added · discounted price · **set ürün · kişiselleştirme · kademeli indirim · ürün grubu · haber ver kaydedildi · haber ver giriş gerekli** | ✓ |
| `CART` | `cart-section` | CartPage (lines, quantity, remove, coupon + applied coupon, **campaign / coupon / gift-card adjustment rows**, summary, checkout, **recommendation rail**) | — | empty (rail stays) · filled (one discounted line, one gift line) · line updating (loading) · coupon error · coupon not applied (the code exists but gives this cart no discount) | ✓ |
| `ACCOUNT` | `account-info-section` | Account (tabs: info, orders, addresses, favorites, order detail) | ConfirmModal (delete address) ○ | each tab · orders empty · form saving / success / error | ✓ |
| `LOGIN` | `login-section` | AuthForms (login variant) | — | default · field error · submitting | ✓ |
| `REGISTER` | `register-section` | AuthForms (register variant) | — | default · field error · submitting | ✓ |
| `FORGOT_PASSWORD` | `forgot-password-section` | AuthForms (forgot variant) | — | default · success (mail sent) · error | ✓ |
| `RECOVER_PASSWORD` | `recover-password-section` | AuthForms (recover variant) | — | default · success · invalid/expired token | ✓ |
| `NOT_FOUND` | `not-found-section` | NotFound (big title, text, link home) | — | — | ✓ |
| `SEARCH` | `category-list-section` (search mode) | ProductList in search mode with its **own in-page search field** (§3d) | Search | searching (keyword in the field, count) · no results · loading · plus an all-products state when the design changes the layout without a keyword | ✓ |
| `FAVORITES` | `favorites` pattern + ProductList grid | ProductList (favorites heading) | — | empty (logged in) · logged-out prompt · filled | ✓ |
| `BLOG` | `blog-home-section` | blog listing (cards or rows, category tabs, pagination) | — | empty category | ○ |
| `BLOG_POST` | `blog-post-section` | BlogPost (title, date, image, rich text) · related posts | — | — | ○ |
| `COLLECTION` | `category-list-section` or custom page | CollectionHero `(özel)` · ProductList | as CATEGORY | as CATEGORY | ○ |
| `CUSTOMER_EMAIL_VERIFICATION` | `email-verification-section` | EmailVerification | — | verifying (loading) · success · error | ○ |
| Contact (custom page, `CUSTOM`) — **always custom, full-width, never a narrow form** | `(özel)` + ikas contact form API: `getContactForm` / `initContactForm`, `setContactFormFirstName` · `LastName` · `Email` · `Phone` · `Message`, `submitContactForm(form) → Promise<boolean>` (model `IkasContactForm`) | Composed of several sections, not one cramped block: **ContactForm** (oversized heading + intro + response-time note; wide form card with topic chips, first/last name, email, optional phone, optional order number, message, consent, submit, result message; beside it a column of channel cards: e-mail, phone, a dark chat/WhatsApp card, social) · **StoreLocator** (featured store image with info card + selectable store list with open status; hover, focus or tap selects a store and swaps the image with a crossfade; a store without a photo shows a placeholder in the theme's style, state `— görselsiz mağaza`, never an empty box) · **FaqList** (title column + accordion) | — | default · sending · success · field error + submit error | ✓ |
| custom page | `rich-text-section` or `(özel)` sections | About, Contact, Support/policy, landing pages — whatever the reference shows | — | form: default · sending · success · error | ○ |

Auth pages may share one Section (`AuthForms`) with four variants drawn as separate frames or states; the plan's §6.3 then lists them as `Auth (×4)` (ornek convention). Header and Footer are counted once each in the section total, not per page.

## 2a. ikas ready-made pages (asked in intake)

ikas renders two page groups with its own components when the merchant enables them (`list_ready_made_pages`, `enable_ready_made_pages`, `update_ready_made_page_prop`):

| Group | Page types | If "ikas hazır" | If "özel" |
|---|---|---|---|
| membership | LOGIN, REGISTER, FORGOT_PASSWORD, RECOVER_PASSWORD, CUSTOMER_EMAIL_VERIFICATION | no AuthForms / EmailVerification section and no page frames for these types; plan §6.3 lists them as `ikas hazır`; the handoff tells the port to enable the group and bind logo + palette (theme globals) + labels via `update_ready_made_page_prop` | design AuthForms (4 variants) + EmailVerification as in §2 |
| account | ACCOUNT, orders, order detail, addresses, FAVORITES | no Account section and no Favorites page frame; same port steps | design Account (tabs) + Favorites (ProductList mode) as in §2 |

The answer is recorded per group in `docs/00-brief.md` §5. A ready-made page still follows the theme's palette and logo, so DS colours and the wordmark must be ready before the port binds them.

## 3. Required overlays

Every theme designs these five, each as its own root frame per state (`P/Overlay/<Name>@desktop — <state>` 1440×900, `@mobile — <state>` 390×844), panel on a flat `$color-scrim` background, never on a copy of a page:

| Overlay | Owner section | States (minimum) |
|---|---|---|
| `CartDrawer` (mini cart) | Header | empty · filled · loading |
| `SearchOverlay` | Header | open empty · typing with results · no results |
| `MenuOverlay` / `MobileMenu` | Header | open (desktop may be a mega menu; mobile is required and keeps the mega menu column titles, §3d) |
| `FilterDrawer` | ProductList | `@mobile` open (desktop only if filters are a drawer there too) |
| `QuickBuy` (hızlı al) | Header (global host; opened by every `ProductCard` cart button and any list row cart button) | açık (varyant seçili) · renk karttan · seçim eksik · ekleniyor · kişiselleştirme · set ürün — `@desktop` and `@mobile` (§3d) |

Optional, when the reference or brief has them: Megamenu, InfoDrawer / size guide (ProductDetail), ConfirmModal, Toast, cookie bar (Header child), newsletter popup. Overlays port as sub-components rendered by the owner section (`04-ikas-constraints.md` §6).

### 3a. QuickBuy — the standard quick-buy popup

QuickBuy is designed on every canvas, whether or not the reference has one. It is the popup that opens when a shopper presses the cart button on a product card, so they can pick a variant and add to cart without leaving the list. The ikas MCP has no ready-made QuickBuy component; it is built from the storefront APIs the product detail page already uses (`get_section_template("variant-selection")`, `("add-to-cart")`, `("product-pricing")`, `("image-handling")`).

| Part | Layer | ikas source |
|---|---|---|
| Image (4:5 on desktop; small thumbnail on mobile), badge, image counter + arrows | `qb-media` | `getProductVariantMainImage` / variant images; `{code:index}` |
| Name, price, compare price | `qb-head`, `qb-price` | `product.name`, `getProductVariantFormattedFinalPrice` + `getProductVariantFormattedSellPrice` (compare) |
| One group per variant type: label + values. Colour/image types use `qb-variant-swatches` → `VariantSwatch`; text types (size) use `qb-variant-row` → `VariantChip`. Never colour chips. A sold-out value uses the `stok yok` state | `qb-variant-group` | `getDisplayedProductVariantTypes`, `selectVariantValue`, `hasProductVariantStock` |
| Validation message when a required option is missing (`$color-danger`) | `qb-variant-error` | TEXT prop (`chooseOptionText`) |
| **Set içeriği** (bundle only): a title with the part count, then `BundleItem` ×N, the same Sub as the product page's `pdp-bundle` (variant, editable or fixed quantity, added price or "Sete dahil", sold out). Parts are grouped by spacing first (`08-quality.md` §8) | `qb-bundle` | `getBundleProductsOfVariant`, `initBundleProducts`, `isBundleProductQuantityEditable`, `shouldDisplayBundleProductPrice`; TEXT props for the title, count (`{n}`), "Sete dahil" and sold-out labels |
| `QuantitySelector` + `Button` (Sepete ekle · Ekleniyor… · Tükendi) + `FavoriteButton`, one row of equal controls (see below) | `qb-actions` | `addItemToCart(variant, product, qty)`, `isAddToCartEnabled`, min/max per cart (`add-to-cart` template's `utils/cartLimits.ts`) |
| "Hızlı Öde" slot, drawn as a neutral 48 px frame because ikas renders the iframe | `qb-pay` | `PayWithIkas` (renders nothing when the merchant has not enabled it); BOOLEAN prop `showPayWithIkas` |
| Stock note + `ArrowLink` to the product page | `qb-foot` | `variant.stockCount`, `getProductHref` |

Layout:
- **`@desktop`:** a centred window of about 960 × 600 on `$color-scrim`, `radius-card`, clipped. The image is on the left (half the width). The details column on the right is padded with `$space-panel`, and the actions are pinned to its bottom.
- **`@mobile`:** a bottom sheet with a grabber and top corners `radius-card`. The thumbnail, name, price and close button share one row, followed by the colour swatches, size chips, set contents, actions, pay slot and footer.
- **The longest state fits.** The window is sized for its longest content, not only for a plain product: the `set ürün` state is drawn with at least three parts at the same window size, and everything down to the footer link is visible with no scrollbar inside the window. When it does not fit, the design chooses how it fits (more compact set rows in QuickBuy, a window that grows with its content up to the viewport, or both) and applies that choice at both devices. The image column follows the window's height and never sets it. Content taller than the viewport scrolls without a visible scrollbar.
- **Nothing navigates under the window.** A link inside QuickBuy either closes the window and then opens its page, or is not a link (set parts are shown, not linked).

**One row, one control language.** The quantity selector, the add button and the favourite button in `qb-actions` (and in the product page's `pdp-actions`) are one row of controls: the same height, the same stroke and the same `radius-control`. The favourite button fills its box: never a round, bordered button inside a square, bordered frame, and never a size of its own. Its hover fill follows the box's corners. CHK `storefront` fails when the controls of `qb-actions` / `pdp-actions` differ in height.

Behaviour:
- After a successful add the popup closes and `CartDrawer` opens in its `dolu` state.
- Motion: the panel uses `M-20`. On desktop the window scales in from 0.96 with opacity; on mobile the sheet slides up with `y 100% → 0`. Swatches and chips use `M-28`, the button `M-11` and the link `M-10`.
- Every label is a TEXT prop with a Turkish default: `addText`, `addingText`, `soldOutText`, `chooseOptionText`, `detailLinkText`, `closeAriaLabel`.

Do not add an eyebrow above the name.

### 3b. ikas merchant blocks on the product page and in the cart (required)

The merchant switches these on in ikas admin (campaigns, campaign offers, bundles, option sets, back-in-stock, reviews), but ikas renders none of them inside a theme section.

**Always in the theme's own style.** Every ikas-driven block (including the address form, the edit / delete / default address actions, the delete-address and delete-account confirmations and their danger buttons) (this section and §3c) is built from the theme's Subs (Button, FormField, VariantChip, VariantSwatch, Checkbox, Badge), tokens (`$color-*`, `$radius-*`, `$space-*`, `$text-*`, `$font-*`) and spacing rhythm. Fields share one height, radius and stroke; labels use the theme's label style; prices use `$font-price`. A block that looks like a stock form or a default widget fails review (`08-quality.md` §2).

**Both devices, always.** Every block and panel in §3b and §3c exists in the `@desktop` **and** the `@mobile` component (hidden ones too), laid out for 390. This covers address actions and form, delete confirmations, account settings, order detail, return form, error and loading panels, option fields, filters and back-in-stock. A panel that only exists on desktop is a gap. Account, ProductDetail and AuthForms states that change the mobile layout get their own `@mobile — <state>` frames: account settings, delete confirmations, return, error, loading, SMS steps. The theme must draw every one, so each design includes them even when the reference shows none. CHK `parity` enforces this: a layer name or state frame that exists only on desktop fails unless the plan declares it (`desktopOnly` / `desktopOnlyStates` in plandata, with the reason in the section's `mobile` text). Draw the blocks in the section component; blocks that depend on store data stay hidden (`enabled:false`, with a `fill_container(<column width>)` fallback width) and are switched on in their own state frames.

**Product detail (`ProductDetail`), layer names fixed:**

| Layer | What the shopper sees | ikas API | Shown by default | State frame |
|---|---|---|---|---|
| `pdp-rating` | RatingStars + score + review count + link to reviews | `product.stars`, `product.reviewCount` | yes | — |
| `pdp-campaign` | campaign message ("2 al, ikincisi %50"), badge on ProductCard too | `getProductCampaigns`, `getProductVariantAppliedCampaignAmount` | yes | — |
| `pdp-offers` | **Birlikte al**: title + OfferCard ×N (toggle, variant select, discounted price, % badge) + summary (old total, new total, saving) + "Birlikte sepete ekle (N)" | `product.offers`, `acceptProductOffer` / `rejectProductOffer`, `isAcceptedProductOffer`, `getProductVariantFormattedFinalPriceWithCampaignOffers`, `addItemToCart(…, offers)` | yes | OfferCard states: seçili değil · seçili · sepette · tükendi |
| `pdp-pay` | Pay with ikas ("Hızlı Öde") slot, neutral 48 px frame (ikas draws the iframe) | `PayWithIkas` | yes | — |
| `pdp-bundle` | **Set içeriği**: BundleItem ×N (variant, editable or fixed quantity, added price, sold out) | `hasBundleSettings`, `initBundleProducts`, `isBundleProductQuantityEditable`, `getBundleProductFormattedFinalPrice` | no | `— set ürün` |
| `pdp-tiers` | **Kademeli indirim** table: quantity range → unit price, current tier highlighted | `getProductVariantTieredDiscountProducts` | no | `— kademeli indirim` |
| `pdp-options` | **Kişiselleştirme**: every `IkasProductOptionType`, drawn in the theme style.<br>Layers:<br>• `option-text` (short text)<br>• `option-textarea` (long text + counter)<br>• `option-select` (dropdown)<br>• `option-box` (VariantChip boxes)<br>• `option-swatch` (VariantSwatch)<br>• `option-image` (image tiles)<br>• `option-checkbox` (+ price)<br>• `option-color` (colour picker)<br>• `option-date` (date picker)<br>• `option-file` (upload: empty, uploading, uploaded file name with remove, upload error)<br>• `option-child` (a dependent option revealed by its parent)<br>• `option-limit` (min/max selection hint)<br>Each label carries its price. | `getProductOptionSet`, `initIkasProductOptionSet`, `getDisplayedOptions`, `getDisplayedChildOptions`, `isChoiceOptionSwatchType` / `…BoxType` / `…SelectType`, `productOptionFileUpload` | no | `— kişiselleştirme` |
| `pdp-group` | **Ürün grubu**: sibling products as image swatches (replaces the colour chips) | `product.productGroup` | no | `— ürün grubu` |
| `pdp-back-in-stock` | **Gelince haber ver**: e-mail field + button, saved message, login-required branch | `getProductVariantIsBackInStockEnabled`, `initBackInStockNotificationForm`, `submitBackInStockNotificationForm`, `variant.isBackInStockReminderSaved` | in `— stok yok` | `— haber ver kaydedildi` · `— haber ver giriş gerekli` |

**Reviews (`ProductReviews` section, placed right after ProductDetail):** `reviews-summary` (score, RatingStars, count, 5→1 distribution bars, "Yorum yaz"), `reviews-list` (ReviewCard ×N + "Daha fazla yorum"), `reviews-empty`, `review-form` (rating input, title, comment, submit, login-required note). States: yorumlu · `— boş` · `— yorum formu` · `— onay bekliyor` (sent; the store approves reviews first) · `— yayınlandı` (sent and already in the list). The form itself carries no approval note: what the shopper reads after sending depends on the store's setting, so each result is its own TEXT prop. The rating input is RatingStars in its input mode (hover preview, selected, keyboard). API: `product-reviews-section` template, `IkasCustomerReviewList`, `customerReviewSettings`.

**Cart page (`CartPage`) and drawer (`CartDrawer`):**

| Layer | What | ikas API |
|---|---|---|
| `cart-adjustments` / `drawer-adjustments` | rows between subtotal and total: campaign, coupon, gift card (name + −amount) | `getIkasOrderDisplayedAdjustments`, `getOrderAdjustmentDisplayName`, `getOrderAdjustmentFormattedAmount`, `cart.giftCardLines` |
| `coupon-applied` (page) / `coupon-toggle` (drawer) | applied coupon chip with remove; collapsed coupon entry in the drawer. States: uygulandı (chip + the coupon row in `cart-adjustments`) · geçersiz (field error) · `— kupon uygulanmadı` (a code the cart stopped qualifying for: chip struck through and muted, the error text, Kaldır). An automatic campaign row never looks like a coupon chip | `getCouponCodeForm`, `submitCouponCodeForm`, `removeCouponCodeForm` |
| `cart-recommendations` / `drawer-recommend` | product rail (stays in the empty cart) from a `PRODUCT_LIST` prop | product list types `PURCHASED_TOGETHER`, `RECOMMENDED`, `LAST_VIEWED`, `RELATED_PRODUCTS` |
| CartLineItem states | `indirimli` (struck old price) · `hediye` (HEDİYE badge, fixed ×N, no remove) · `set` (bundle sub-list) · `kişiselleştirilmiş` (option values + Düzenle; an uploaded file shows as its file name, never as its storage URL) | `hasOrderLineItemDiscount`, `isOrderLineItemAutoCreated`, `item.variant.bundleProducts`, `item.options`, `editOrderLineItem` |

**Editing a cart line.** Düzenle on a `kişiselleştirilmiş` or multi-variant line opens the place chosen in intake (07 §1 question 11), and that place gets a `— sepeti güncelle` state at both devices: the product page (`ProductDetail — sepeti güncelle`, default), QuickBuy (`QuickBuy — sepeti güncelle`: the line's variant, options and quantity pre-filled, the add button reads "Sepeti güncelle") or the cart drawer (an inline edit panel on the line). The update replaces the line in place (PB-17).

**Required subs:** `OfferCard`, `BundleItem`, `RatingStars`, `ReviewCard` (plus the CartLineItem states above).

**Product page composition:** Header · ProductDetail · ProductReviews · ProductGrid (purchased together / related) · ProductGrid (last viewed) · Footer.

**Not in ikas, so do not design as data-driven:** size-chart API, product compare, pre-order, free-shipping progress bar, installment table, offer countdown. Size guide is a link to merchant content. "Son N ürün" uses a theme-defined threshold on `variant.stock`.

Do not put an eyebrow above any of these titles. Discount amounts use `$color-text` when the accent fails 4.5:1 on the summary ground.

### 3c. Storefront completeness: required on every canvas

The ikas MCP expects these pieces in every custom theme (templates, child components, storefront functions). ikas renders none of them inside a section, so the theme draws all of them. Blocks that depend on store data or settings are drawn but hidden (`enabled:false`, wrapped in a `…-stage` frame when the panel is taller than its parent) and shown in their own `— <state>` frame.

| Where | Required layers / roots | States | ikas source |
|---|---|---|---|
| ProductList + FilterDrawer | `filter-category-list`, `filter-swatch-values` (VariantSwatch), `filter-box-values` (VariantChip), `filter-range` (PriceRange: two handles and two number fields; the labels follow while dragging and the list filters once on release), `filter-range-list`, Checkbox list, `filter-clear-all` | — | `IkasProductFilterDisplayType` (SWATCH, BOX, NUMBER_RANGE, NUMBER_RANGE_LIST, LIST), FilterSwatch/Box/Range values |
| ProductDetail | `pdp-thumbs` (the thumbnail rail is as tall as its thumbnails, not as tall as the gallery; it scrolls inside only when the thumbnails overflow), `pdp-video` (a product video among the images plays muted and looped by default, in the gallery, in its thumbnail and in ImagePreview; a play glyph appears only in the paused state `— video duraklatıldı`, and a sound toggle sits on the playing video; click-to-play only when the brief asks for it), `pdp-variant-swatches` (colour/image swatches, text types stay chips), `pdp-stock-locations` (hidden) | `— sepeti güncelle` (editLineID), `— yükleniyor` (skeleton), `— mağazada stok` | `img.isVideo`, VariantBadge colour/image, `getProductAvailableStockLocations`, `editOrderLineItem` |
| ProductCard / QuickBuy | `card-swatches` colour dots + `+N`; QuickBuy colour row uses VariantSwatch | — | CardProductVariants |
| ProductReviews / ReviewCard | `review-images`, `merchant-reply`, `reviews-pagination` | ReviewCard `görselli`, `mağaza yanıtlı` | `review.images`, merchant reply, Pagination |
| CartPage / CartLineItem / QuantitySelector | `cart-skeleton`; line `cart-line-limit` | CartPage `— yükleniyor`; CartLineItem `adet sınırı`; QuantitySelector `üst sınır` | `maxQuantityPerCart`, `MAX_QUANTITY_PER_CART_LIMIT_REACHED` |
| Header | `announcement-pager` (more than one announcement) | `— yapışkan`, `— duyurular` | `stickyEnabled`, Announcements COMPONENT_LIST |
| Footer | `locale-button` in the bottom row (globe icon + current language/currency + caret). It is always the LocaleSwitcher trigger; the header never carries one. Every newsletter form (Footer, popup or section) has `newsletter-consent`: a Checkbox with a consent text and a link (KVKK / ileti izni), hidden by default, optional or required by prop | `— bülten onay hatası` (required consent left empty) · `— tek dil` (the store has one language and one currency: `locale-button` shows the current value as plain text, no caret, not a button) | `showConsentCheckbox`, `consentRequired`, `consentText`, `consentLink`, `consentErrorText` | `baseStore.localeOptions`, `setLocalization` |
| MenuOverlay (mobile) | `menu-auth` (login / register, or name + logout) | — | customer auth state |
| AuthForms | `social-login` (SocialLoginButton ×2 + divider + phone-login link), `sms-login` (phone → code + resend), `register-consents` (two separate checkboxes: marketing, agreement/KVKK) | `— SMS telefon`, `— SMS kod`; the register state shows both consents | `showGoogleLogin`/`showFacebookLogin`, `submitSmsLoginForm`, `marketingConsentText`/`agreementConsentText` |
| EmailVerification | `resend-form` | error state shows it; `— tekrar gönderildi` | `resendTitle`, `resendCustomerActivationMail` |
| Account (when custom) | `order-detail` (packages, cargo + tracking with copy, items, addresses, payment, summary), `return-form`, `account-settings` (phone, marketing toggle, data export, delete account), `orders-error`, `account-skeleton`; on every address card `address-card-actions` (Düzenle · Sil · Varsayılan yap + VARSAYILAN badge); `address-form` (add/edit: name, phone, ID no, country → city → district, postcode, address, corporate invoice, default; save / cancel) inline in the addresses panel, or in AddressModal when chosen; `address-delete-confirm` and `account-delete-confirm` (password + cancel / danger button) inline, or ConfirmModal when chosen | `— sipariş detayı`, `— iade talebi`, `— hesap ayarları`, `— yükleniyor`, `— hata`, `— adres ekle`, `— adres sil onayı`, `— hesap silme onayı` | AccountOrderDetail, `refundOrder`, `DeactivateCustomerForm`, `exportCustomerPersonalData` |

**Required overlays in addition to §3:** `CookieBar` (açık; KVKK), `ImagePreview` (açık; gallery zoom and review images), `LocaleSwitcher` (açık; opens from the Footer `locale-button`, desktop panel above the footer, mobile bottom sheet).

**Conditional overlays, asked in intake:**
- **`Toast`** (başarılı · hata · bilgi). Without it, feedback comes from the Button `eklendi` state and the CartDrawer opening.
- **`ConfirmModal`** (açık). Without it, destructive actions (delete address, delete account) use an inline confirmation row.
- **`AddressModal`** (ekle · yükleniyor · hata; country → city → district cascade, corporate invoice fields). Without it, the address form opens inline in the Account addresses panel.
- **`AccountMenu`** (desktop: misafir · üye). Without it, the header account button links to the account or login page.

**Required sections and pages:** `RichText` (about, KVKK and policy pages; page `Policy`, type `CUSTOM`) and `OrderTracking` (guest order lookup with result and not-found states; page `OrderTracking`, type `CUSTOM`). With a custom Account, also page `OrderDetail` (type `ORDER_DETAIL`).

**Required subs:** `VariantSwatch` (varsayılan · seçili · hover · stok yok), `PriceRange`, `SocialLoginButton` (Google · Facebook · hover), `Skeleton`.

**Conditional: asked in intake (07 §1), drawn only on "evet":** Toast, ConfirmModal, AddressModal, AccountMenu (fallbacks above), loyalty program (points in account and cart), raffle pages, brand page, technical spec table, extra customer fields at register, blog tags and author, product-list column toggle (3/4 desktop, 1/2 mobile).

**Not designed (decided in code):** search inside a category list (the search page field of §3d is required), "load previous page", numbered pagination as well as load-more (pick one), unit price.

### 3d. Product cards, mobile menu and search: required behaviour

Each rule below comes from a review of a finished theme where the first build missed it. They hold on every canvas, whatever the reference shows. CHK `storefront` checks the layer names and state frames; CHK `dividers` warns about line noise (`08-quality.md` §2). The code side of each rule is in `10-port-behaviour.md`.

**ProductCard (`P/Sub/ProductCard`), layer names fixed:**

| Layer | Rule |
|---|---|
| `card-media` | The image frame. Every overlay control below sits inside it. |
| `card-fav` | The favourite button sits inside `card-media`. **The design picks its place once** (a corner, its offset, its size and whether it is revealed on hover) and that place is the same **everywhere a card shows a favourite**: every card type (ProductCard, ProductCardSmall, list rows, rail cards), every list and page (home rails, category, search, favourites, cart rail, related products) and both devices. Sections never move or restyle it; a card type that needs a smaller button keeps the same corner. A hover-revealed button is always visible on touch (rule 14). The product page's own favourite button beside add-to-cart is a separate layer (`pdp-fav`, inside the `pdp-actions` row) and is the only exception; it follows the action-row rule of §3a. |
| `card-swatches` | Colour dots + `+N`. They are **interactive**: hovering previews that colour's image and clicking selects it, without leaving the list. The selected dot has its own style. |
| `card-cart` | Opens QuickBuy. QuickBuy opens with the colour chosen on the card. |
| `card-customize` | Replaces `card-cart` when the product needs a personalisation before it can be added (an option set with a required field). It uses a **different icon** (pen, sliders) from the cart button, so the shopper sees before clicking that this product needs a choice on the product page, and it links straight to the product page. Hidden on the default card. |

ProductCard states, each a `P/Sub/ProductCard — <state>` frame:
- `renk seçili`: a swatch other than the first is selected and the image shows that colour.
- `ayrık varyant`: the merchant has enabled "show variant values separately on category pages", so every colour is its own card. The card shows that colour's image and name and has **no** `card-swatches`.
- `kişiselleştirme`: `card-customize` is visible and `card-cart` is hidden.

**QuickBuy additions (§3a):**
- `renk karttan`: QuickBuy opens with the card's colour selected and no size selected. The size group is **not** in its error style until the shopper presses add.
- `set ürün`: a bundle with at least three parts, its `qb-bundle` list (§3a) visible before the shopper adds, one part with an editable quantity and one with a fixed one. It is drawn at the window size of the other states and fits it (§3a layout).
- `kişiselleştirme`: shown only when the product has a **required** personalisation field. A product whose option set is entirely optional, and a bundle (set ürün), add to cart from QuickBuy; QuickBuy shows their option fields or bundle contents in the theme style and loads them itself, so its add button has a loading state while they load. The add button becomes an outline button with an arrow, labelled to go to the product page, with a short note above it explaining why. Its style differs from the solid add button, so a shopper who skims does not mistake it for "add to cart". Both labels are TEXT props.

**MenuOverlay `@mobile`:** when the desktop navigation has a mega menu, the mobile menu keeps every column title (`menu-mega-title`) above its links. The vertical rhythm is one scale: the same gap between a title and its links everywhere, and a larger gap between groups. A mobile menu that drops the column titles and runs all links together is a gap.

**Touch behaviour (rule 14):** content a desktop layout reveals on hover or by expanding (activity cards, collection tiles, image hover text) is drawn **open** on the `@mobile` component, and the whole card is the tap target (no separate small link). Draw it that way rather than describing it.

**Popular searches (optional):** a theme may show popular search chips in SearchOverlay (`search-suggestions`) and on the search page (`search-popular`), each a LIST_OF_LINK prop. They are not required. When they exist, a chip that points at the search page searches for its own label (it opens the search page with that keyword, or searches in place on the search page); it is never a plain link to an empty search page.

**Search page (`ProductList` in search mode):**
- **Required: an in-page search field.** The search page draws its own search field (`search-field`: search icon, input, clear button), so a shopper can change the keyword without going back to the header. Typing searches the list. The result count appears exactly once, in a place the design picks (inside the field, `search-count`, or in the filter bar).
- **The design decides the rest, and applies it consistently:** whether the field is always open or folds away when there is no keyword (the "all products" page), what opens a folded field, where that control sits, and whether popular searches appear. If the field folds, the page itself has a visible control that opens it; the header is not the only way in.
- **The header behaves the same on every page.** Its search opens SearchOverlay on the search page too; the page's own field is a second entry, not a replacement.
- **States:** `P/Section/ProductList@desktop — arama` and `@mobile — arama` (keyword in the field, count shown). When the layout without a keyword differs (folded field, another title), also `— tüm ürünler` at both devices.
- Every string is a TEXT prop: page title, placeholder, clear label and, when used, the toggle and popular-searches labels.

## 4. States

- **Where states live:** interactive component states (hover, disabled, loading, selected, out of stock, error) are drawn once on `P/Sub/<Name> — <state>` frames, never repeated inside sections. Page-level states (empty cart, no results, empty orders) are separate Section frames named `P/Section/<Key>@device — <state>` only when the layout changes; otherwise a Sub state is enough.
- **Empty:** every list that can be empty (cart, search, category, favorites, orders, addresses, blog category) has an empty state with a TEXT title, TEXT body and a LINK action.
- **Loading:** buttons (spinner + `…ingText` prop), product grids (skeleton cards or load-more spinner), cart line updates.
- **Error / success:** every form (auth, newsletter, contact, address, coupon, review) has field error and submit error, and a success message where the flow ends on the same page. Copy for each is a TEXT prop (two props for button loading labels).
- **Commerce states:** discounted price (compare-at struck through), out of stock (badge + disabled add-to-cart + back-in-stock option), variant unavailable, free-shipping progress if designed.

## 5. Sections the reference does not have

When the reference lacks a required page (common: cart, auth, account, 404, search, favorites), design it in the same visual language and record it in `components.md` §1 under "Referansta olmayan ama ikas'ta gereken sayfalar" with its template. Do not mark these values `[ölçüldü]`; their structure comes from the ikas template, their look from the theme tokens.

## 6. Custom pages

Custom pages (About, Contact, Support, campaign landing) are created by the merchant with `create_page`. **Contact is in scope by default** (pre-ticked in intake, even when the reference has no contact page): ikas has no `CONTACT` page type, contact section template or ready-made contact page, but the storefront ships a full contact form API, so every theme designs a custom `Contact` page (`pageType: CUSTOM`) that is sent to the ikas editor (studio) through the MCP. Design it as a full page, never a narrow centred form or a small two-column block: ContactForm + StoreLocator + FaqList (see the Contact row). API limits to respect: `submitContactForm` sends only first name, last name, email, phone, message (+ referer) and takes no files — a topic selector and an order-number field are allowed (the code prepends them to `message`), a file-upload field is not designed unless the brief names an external upload link. Channel cards follow rule 11: the value is the title (e-mail address, phone number), the hint goes below it, no small label above. Other custom pages are in scope only when the brief lists them. Each still uses Header + Footer and only Sections. Content-heavy policy pages use one rich-text Section rather than bespoke layouts.
