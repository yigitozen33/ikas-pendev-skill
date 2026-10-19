# Brief — <Marka>

Bu dosya tüm fazların başlangıç noktasıdır. Her oturum önce bunu okur; en alttaki **Durum** tablosu ilk açık fazı gösterir. Kaynak sırası: bu brief > canlı .pen dosyası > `docs/` > skill varsayılanları.

## 1. Girdiler

| Dosya / URL | Sayfa | Viewport genişliği | Not |
|---|---|---|---|
| … | … | … | … |

- Canlı referans: …
- Taranacak yollar: …
- Girdi klasörü: `docs/referans/girdi/` (git'e girmez; `.gitignore`'a eklendi: evet / hayır)

## 2. Marka

| Alan | Değer |
|---|---|
| Tema adı (marka adı, ilk soru) | … |
| Slug | … (tema adından: Türkçe harfler sadeleşir, boşluk → `-`) |
| Marka adının geçtiği yerler | logo + işaret (`P/DS/Icons`), header, footer + telif satırı, iletişim e-postası (`destek@<slug>.com.tr`), mağaza adları, giriş/hesap metinleri (02-contract §11) |
| Sektör | … |
| Ton (3 sıfat) | … · … · … |

## 3. Yorum stratejisi

| Alan | Değer |
|---|---|
| Strateji | aynı iskelet / yakın klon / serbest yorum |
| Prefix harfi | … (çakışma kontrolü: `get_app_state` → …) |
| Sözleşme | contract … |
| Plan dosyası | `docs/pendev/plan-<P>-<slug>.md` |

## 4. Referans politikası

- [ ] Referans sadece bakmak için: görseli, metni, logosu ve marka adı canvas'a girmez.
- [ ] Görseller `Generate("ai" | "stock")`, logo `Generate("svg")` ile özgün üretilir.
- Onay: …

## 5. Kapsamdaki sayfalar

| Sayfa tipi | Kapsamda | Not |
|---|---|---|
| `INDEX` | [x] | |
| `CATEGORY` | [x] | |
| `PRODUCT_DETAIL` | [x] | |
| `CART` | [x] | |
| `ACCOUNT` | [x] | |
| `LOGIN` · `REGISTER` · `FORGOT_PASSWORD` · `RECOVER_PASSWORD` | [x] | |
| `NOT_FOUND` | [x] | |
| `SEARCH` | [x] | |
| `FAVORITES` | [x] | |
| `BLOG` · `BLOG_POST` | [ ] | |
| `COLLECTION` | [ ] | |
| `CUSTOMER_EMAIL_VERIFICATION` | [ ] | |
| İletişim (özel sayfa, `CUSTOM`) | [x] | her zaman özel ve geniş: ContactForm + StoreLocator + FaqList; ikas iletişim formu API'si (`getContactForm`, `submitContactForm`) |

ikas hazır sayfalar (06 §2a):

| Grup | Sayfalar | Karar |
|---|---|---|
| üyelik | giriş, kayıt, şifremi unuttum, şifre yenile, e-posta doğrulama | ikas hazır / özel tasarım |
| hesap | hesabım, siparişler, sipariş detayı, adresler, favoriler | ikas hazır / özel tasarım |
| Özel sayfalar | [ ] | … |

Zorunlu overlay'ler: CartDrawer · SearchOverlay · MenuOverlay · QuickBuy (hızlı al) · FilterDrawer@mobile.
Koşullu özellikler (intake'te sorulur, yalnız işaretlenenler çizilir): [ ] bildirim (toast) · [ ] onay penceresi · [ ] adres penceresi · [ ] hesap menüsü · [ ] sadakat programı · [ ] çekiliş · [ ] marka sayfası · [ ] teknik özellik tablosu · [ ] kayıtta ek müşteri alanları · [ ] blog etiket ve yazar · [ ] ürün listesinde sütun seçimi.

Sepetteki ürünü düzenleme (06 §3b): [ ] ürün sayfası (varsayılan) · [ ] QuickBuy · [ ] sepet drawer'ı içinde.
Zorunlu tamamlama (06-page-coverage §3c): filtre tipleri, renk swatch'ları, galeride video, çerez çubuğu, görsel önizleme, footer'dan açılan dil/para birimi seçici, sosyal + SMS giriş, iki ayrı kayıt onayı, sipariş detayı + iade, hesap ayarları (veri dışa aktarma, hesap silme), sipariş takibi, metin sayfası, yükleniyor iskeletleri.
Zorunlu mağaza blokları (ikas hazır tasarım vermez, her temada özel çizilir): ürün detayda birlikte al · set içeriği · kademeli indirim · kişiselleştirme · ürün grubu · gelince haber ver · Hızlı Öde · puan; ProductReviews bölümü; sepette kampanya/kupon/hediye çeki satırları · uygulanan kupon · hediye satırı · öneri şeridi. Header ve Footer her sayfada.

## 6. Yerel ayarlar

| Alan | Değer |
|---|---|
| Dil / locale | … |
| Para biçimi | … |
| Büyük harf politikası | … |

## 7. Palet modları

- Seçim: tek palet / ters bölümler / tam koyu
- Koyu (`mode: dark`) bölümler: …

## 8. Canvas ve cihazlar

| Alan | Değer |
|---|---|
| .pen dosyası | … |
| Masaüstü genişliği | 1440 |
| Mobil genişliği | 390 |
| Overlay boyutları | 1440×900 · 390×844 |

## 9. Motion iştahı

- Seviye: sade / orta / yoğun
- Not: …

## 10. Durum

| Faz | Durum | Dosya | Tarih | Not |
|---|---|---|---|---|
| 0 intake | bekliyor | `docs/00-brief.md` | | |
| 1 analyze | bekliyor | `docs/referans/globals.md`, `docs/referans/components.md` | | |
| 2 plan | bekliyor | `docs/pendev/plan-<P>-<slug>.md` | | |
| 3 build | bekliyor | canvas + `docs/pendev/build-log.md` | | |
| 4 verify | bekliyor | `docs/pendev/verify-report.md` | | |
| 5 handoff | bekliyor | `docs/port/port-manifest.json`, `port-manifest.md`, `globals-runbook.md` | | |

Durum değerleri: `bekliyor` · `sürüyor` · `tamam` · `istisna`.
