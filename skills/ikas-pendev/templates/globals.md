# Globals — referans token'ları ve motion tarifleri

Kaynak: <referans URL / ekran görüntüleri>, … ve … genişlikte ölçüldü.
Bu dosya referansın **ölçülen** değerlerini verir. <Marka>'nın kendi kimlik değerleri pen.dev planının "Değişkenler" bölümündedir; buradaki **token adları** sabittir, sadece değerler değişir.

Etiketler: **[ölçüldü]** = siteden/CSS'ten/Framer modülünden okundu · **[tahmini]** = gözlemle kestirildi, aktarımda ayarlanacak.

Sütunlar: referans değeri → pen.dev değişkeni (`$ad`) → ikas karşılığı.

---

## 0. Yapısal kimlik

Temanın iskeleti hangi yapısal ve stil seçimleriyle kurulacak (`references/12-library.md` §6). Her satıra `library/axes.json`'daki değerlerden biri yazılır; varsayılan yoktur. Seçimler referansın ölçümünden ve brief'in yorum stratejisinden gelir. Gerekçe bir cümledir. Kapı: `axes.py check` (önceki temalardan yeterince ayrışıyor mu, kaç eksen jenerik varsayılanda).

| Eksen | Alan | Seçim | Gerekçe |
|---|---|---|---|
| A1 Section düzen varyantları | collection | `…` | … |
| A1 Section düzen varyantları | story | `…` | … |
| A2 Grid ve sütunlar | desktop_cols | `…` | … |
| A2 Grid ve sütunlar | mobile_cols | `…` | … |
| A2 Grid ve sütunlar | gutter | `…` | … |
| A2 Grid ve sütunlar | container | `…` | … |
| A3 Navigasyon kalıbı | logo | `…` | … |
| A3 Navigasyon kalıbı | menu | `…` | … |
| A3 Navigasyon kalıbı | mega | `…` | … |
| A3 Navigasyon kalıbı | behaviour | `…` | … |
| A3 Navigasyon kalıbı | announcement | `…` | … |
| A4 Hero arketipi | type | `…` | … |
| A4 Hero arketipi | height | `…` | … |
| A4 Hero arketipi | text | `…` | … |
| A5 Ürün kartı anatomisi | info | `…` | … |
| A5 Ürün kartı anatomisi | price | `…` | … |
| A5 Ürün kartı anatomisi | hover_image | `…` | … |
| A5 Ürün kartı anatomisi | quick_add | `…` | … |
| A5 Ürün kartı anatomisi | badge | `…` | … |
| A5 Ürün kartı anatomisi | swatch | `…` | … |
| A5 Ürün kartı anatomisi | shell | `…` | … |
| A6 Görsel oranı ve işlemesi | product_ratio | `…` | … |
| A6 Görsel oranı ve işlemesi | hero_ratio | `…` | … |
| A6 Görsel oranı ve işlemesi | treatment | `…` | … |
| B7 Tipografi eşleşmesi | display | `…` | … |
| B7 Tipografi eşleşmesi | body | `…` | … |
| B8 Tip ölçeği | ratio | `…` | … |
| B8 Tip ölçeği | heading_weight | `…` | … |
| B9 Harf durumu ve aralığı | headings | `…` | … |
| B9 Harf durumu ve aralığı | tracking | `…` | … |
| B9 Harf durumu ve aralığı | labels | `…` | … |
| B10 Köşe yarıçapı | radius | `…` | … |
| B11 Çizgi, yüzey ya da gölge | surface | `…` | … |
| B12 Renk stratejisi | strategy | `…` | … |
| B12 Renk stratejisi | temperature | `…` | … |
| B12 Renk stratejisi | ground | `…` | … |
| B13 Yoğunluk ve boşluk | base | `…` | … |
| B13 Yoğunluk ve boşluk | section | `…` | … |
| B13 Yoğunluk ve boşluk | rhythm | `…` | … |
| B14 İkonografi | style | `…` | … |
| B15 Hareket kişiliği | personality | `…` | … |
| B15 Hareket kişiliği | hover | `…` | … |

---

## 1. Renk

| Token | Referans | pen.dev | ikas |
|---|---|---|---|
| Zemin | … | `color-bg` | … |
| Metin | … | `color-text` | … |
| İkincil metin + çizgi | … | `color-muted`, `color-line` | … |
| Yüzey | … | `color-surface` | … |
| Ters zemin (buton, hover dolgu) | … | `color-inverse-bg` | … |
| Ters metin | … | `color-inverse-text` | … |
| Pasif öğe opaklığı | … | `opacity-inactive` | … |
| Overlay karartma | … | `color-scrim` | … |
| Vurgu | … | `color-accent` | … |
| Vurgu üstü metin | … | `color-accent-text` | … |
| Gradyan başlangıcı (saydam zemin) | … | `color-transparent` | … |
| Hata | … | `color-danger` | … |
| Başarı | … | `color-success` | … |

Kurallar:
- …

ikas notu: …

---


### 1a. Renk şemaları (ikas colorScheme)

| ikas slot | pen.dev token | <Şema 1 adı> (varsayılan) | <Şema 2 adı> | <Şema 3 adı> |
|---|---|---|---|---|
| background | `color-bg` | … | … | … |
| text | `color-text` | … | … | … |
| muted | `color-muted` | … | … | … |
| line | `color-line` | … | … | … |
| surface | `color-surface` | … | … | … |
| button-bg | `color-inverse-bg` | … | … | … |
| button-text | `color-inverse-text` | … | … | … |
| accent | `color-accent` | … | … | … |

Hücre biçimi: `` `#HEX` [kaynak] [ölçüldü|tahmini] ``; kaynak ∈ `[referans]` `[huemint]` `[qrco]` `[ai]`. Sütun sayısı = brief §7'deki şema sayısı (2–4); plandaki `modes`, şema adlarının ASCII hâlidir (`Kağıt` → `kagit`).

Varsayılan şema eşleşmesi: her şemayı varsayılan olarak kullanan bölümler.

- **<Şema 1 adı>:** …

### 1b. Renk kurgusu

| Şema | Psikolojik hedef | Kaynak | Bölümler |
|---|---|---|---|
| … | … | … | … |

- Gerekçe (şema başına 1–2 madde): sektör, ton, alanın rolü, tercih edilen ve kaçınılan ton aileleri (11-color §5–§6).
- Kaynak notu: hangi araçlar çalıştı, hangileri ulaşılamadı.

## 2. Tipografi

Referans font: …

**pen.dev kısıtı:** …

### Preset'ler

| Token | Kullanım | ≥1200 | 992–1199 | 768–991 | <768 | Ağırlık | Satır |
|---|---|---|---|---|---|---|---|
| `text-display` | … | … | … | … | … | … | … |
| `text-h2` | … | … | … | … | … | … | … |
| `text-h3` | … | … | … | … | … | … | … |
| `text-h4` | … | … | … | … | … | … | … |
| `text-title` | … | … | … | … | … | … | … |
| `text-ui` | … | … | … | … | … | … | … |
| `text-ui-sm` | … | … | … | … | … | … | … |
| `text-badge` | … | … | … | … | … | … | … |
| `text-label` | … | … | … | … | … | … | … |
| `text-body` | … | … | … | … | … | … | … |
| `text-price` | … | … | … | … | … | … | … |

Notlar:
- …

| | pen.dev | ikas |
|---|---|---|
| Boyutlar | … | … |
| Aile | … | … |
| Ara kırılımlar | … | … |

**Açık soru (font yükleme):** …

---


### 2a. ikas metin stilleri (kırılım değerleri)

| ikas stil | Token | Aile · ağırlık | ≥1200 | 992–1199 | 768–991 | <768 | Satır | Harf |
|---|---|---|---|---|---|---|---|---|
| … | `text-display` | … | … | … | … | … | … | … |

## 3. Boşluk, grid, ölçü

| Token | Referans | pen.dev | ikas |
|---|---|---|---|
| Sayfa kenar boşluğu | … | `space-page` | … |
| Grid aralığı | … | `space-grid` | … |
| Kart iç boşluğu | … | `space-card` | … |
| Panel iç boşluğu | … | `space-panel` | … |
| Küçük aralık | … | `space-xs` | … |
| Orta aralık | … | `space-sm`, `space-md` | … |
| Bölüm üst boşluğu | … | `space-section` | … |
| Header yüksekliği | … | `size-header` | … |
| Logo boyutu | … | `size-logo` | … |
| Çizgi kalınlığı | … | `size-line` | … |
| İçerik genişliği | … | — | … |

Boşluk sistemi (`02-contract.md` §3b; plandata `spacing`, sayfada CHK `spacing`). Roller sabit; her rolün token'ı ve değeri referanstan ölçülür. Temaya özgü token gerekiyorsa (ör. yüzen bantlar için `space-band`) değişkenlere eklenir. Roldan farklı duran bölümler (yüzen bantlar, hero'nun devamı olan liste, şeffaf header altındaki hero) tablonun altında "Bölüm istisnaları" olarak yazılır; plandata'da `spacing.edges` / `spacing.seams` olur.

| Rol | Ne | Token | Masaüstü / mobil | Referans |
|---|---|---|---|---|
| `pageEdge` | her bandın yan boşluğu (bölüm, header, hero, footer, paneller) | … | … | … |
| `headerGap` | header → ilk bölüm | … | … | … |
| `sectionGap` | bölüm → bölüm (alttakinin üst iç boşluğu, alt iç boşluk 0) | … | … | … |
| `footerGap` | son bölüm → footer (footer kökünün üst iç boşluğu, kök şeffaf) | … | … | … |
| `split` | sütun bölmesi (galeri ↔ satın alma, filtre ↔ ızgara, satırlar ↔ özet) | … | … | … |
| `grid` | kart ızgarası ve ray | … | … | … |

Grid düzenleri:
- …

Mobil (<768):
- …

---

## 4. Kırılımlar

| Ad | Aralık | pen.dev | ikas |
|---|---|---|---|
| desktop | … | frame 1440, `device: desktop` | … |
| laptop | … | tasarlanmaz | … |
| tablet | … | tasarlanmaz | … |
| mobile | … | frame 390, `device: mobile` | … |

CSS'te `@media (max-width: bp(<breakpointId>))` yazılır; `var()` medya sorgusunda çalışmaz.

---


### 4a. Ara kırılım davranışı

| Bölüm | ≥1200 (masaüstü) | 992–1199 (laptop) | 768–991 (tablet) | <768 (mobil) |
|---|---|---|---|---|
| … | … | … | … | … |

## 5. Katman sırası

| Katman | z | Not |
|---|---|---|
| … | … | … |

---

## 6. İkonlar

…

---

## 7. Motion

### 7.1 Token'lar

| Token | Değer | Kullanım |
|---|---|---|
| … | … | … |

CSS karşılıkları: …

### 7.2 Uygulama yolları (ikas)

| Kısa ad | Ne | Ne zaman |
|---|---|---|
| `css-transition` | `:hover` / durum sınıfı + `transition` | hover, aç/kapa, renk |
| `css-keyframes` | bileşen `styles.css` içinde `@keyframes` | sonsuz döngü (marquee, pulse). Ad bileşene göre yeniden adlandırılır → **her bileşen kendi keyframe'ini tanımlar** |
| `theme-keyframe` | `create_theme_global` kind `keyframe`, `animation-name: <ref>` | birden çok bileşenin paylaştığı keyframe |
| `io-hook` | `useEffect` içinde `IntersectionObserver` → `is-inview` sınıfı | görünürlükte bir kez tetiklenen giriş |
| `animejs` | `import { AnimeJS } from "@ikas/bp-storefront"`, `useEffect` içinde | stagger, timeline, spring, kelime bölme |
| `scroll-scrub` | `useEffect` içinde scroll dinleyici + `requestAnimationFrame` → CSS değişkeni | scroll'a bağlı ilerleme |
| `layout` | `position: sticky` | animasyon değil, düzen davranışı |

Ortak kurallar: tarayıcı API'si sadece `useEffect` içinde (SSR var); SSR çıktısı **bitiş halini** göstermeli, başlangıç hali JS yüklenince sınıfla verilir; `prefers-reduced-motion: reduce` altında döngüler durur, girişler anında olur; dışarıdan paket yok (sadece `animejs`, `three`).

### 7.3 Tarif kataloğu

Her tarif için "Katman yapısı" sütunu pen.dev tasarımında **zorunlu** olan yapıdır. ID'ler ve adlar sabittir (`references/03-motion.md`); referansta görülmeyen tarifin değer sütununa "referansta yok" yazılır.

| ID | Ad | Hareket ve değerler | Katman yapısı | Uygulama | Mobil / azaltılmış hareket |
|---|---|---|---|---|---|
| **M-01** | Yükleme fade-up | … | … | … | … |
| **M-02** | Yükleme fade | … | … | … | … |
| **M-03** | Kelime kelime başlık reveal | … | … | … | … |
| **M-04** | Duyuru metin döngüsü | … | … | … | … |
| **M-05** | Nav hover dolgu + etiket roll | … | … | … | … |
| **M-06** | Megamenu aç/kapa | … | … | … | … |
| **M-07** | Hero slayt geçişi | … | … | … | … |
| **M-08** | Thumbnail ilerleme | … | … | … | … |
| **M-09** | Ürün kartı hover | … | … | … | … |
| **M-10** | Oklu link hover | … | … | … | … |
| **M-11** | Buton hover dolgu | … | … | … | … |
| **M-12** | Hotspot pulse + kart | … | … | … | … |
| **M-13** | Sticky panel | … | … | … | … |
| **M-14** | Metin marquee | … | … | … | … |
| **M-15** | Görsel ticker | … | … | … | … |
| **M-16** | Footer reveal | … | … | … | … |
| **M-17** | Yumuşak kaydırma | … | — | ikas'ta Lenis **kullanılamaz** (paket izni yok). Varsayılan: uygulanmaz | — |
| **M-18** | Filtre barı | … | … | … | … |
| **M-19** | PDP galeri scrollspy | … | … | … | … |
| **M-20** | Çekmece | … | … | … | … |
| **M-21** | Arama | … | … | … | … |
| **M-22** | Akordeon | … | … | … | … |
| **M-23** | Scroll-scrub görsel | … | … | … | … |
| **M-24** | Scroll-scrub metin | … | … | … | … |
| **M-25** | Scrollspy gezinme | … | … | … | … |
| **M-26** | Alıntı slider | … | … | … | … |
| **M-27** | Hero parallax | … | … | … | … |
| **M-28** | Durum rengi | … | … | … | … |

### 7.4 Referansta ölçülemeyenler

- …
