
## 2. Canvas organizasyonu

Her şey **ayrı kök frame**. Kök frame adları sabit kalıpta; ikas'a aktarımda bu adlardan bileşen listesi çıkarılır.

| Sıra (yukarıdan aşağı) | Kök frame adı | İçerik | Boyut |
|---|---|---|---|
| 00 | `{{prefix}}/DS/Colors`, `{{prefix}}/DS/Typography`, `{{prefix}}/DS/Spacing`, `{{prefix}}/DS/Icons`, `{{prefix}}/DS/Motion`{{#c2}}, `{{prefix}}/DS/Imagery`{{/c2}} | Design system sayfaları | serbest |
| 01 | `{{prefix}}/Sub/<Ad>` (reusable) ve `{{prefix}}/Sub/<Ad> — <durum>` | Bileşenler ve durumları | içeriğe göre |
| 02 | `{{prefix}}/Section/<Ad>@desktop` ve `{{prefix}}/Section/<Ad>@mobile` (ikisi de reusable) | Bölümler | {{dw}} / {{mw}} genişlik |
| 03 | `{{prefix}}/Page/<Ad>@desktop` ve `{{prefix}}/Page/<Ad>@mobile` | Sayfalar (section instance'ları) | {{dw}} / {{mw}} |
| 04 | `{{prefix}}/Overlay/<Ad>@desktop — <durum>` ve `…@mobile — <durum>` | Menü, sepet, arama, paneller | {{dw}}×{{dh}} / {{mw}}×{{mh}} |
| 05 | `{{prefix}}/Motion/<tarif> <bölüm>` | Animasyon kareleri (başlangıç / ara / bitiş) | içeriğe göre |

Yerleşim: her sıra bir yatay bant; bantlar arası 800, frame'ler arası 200 boşluk. Bir bölümün desktop ve mobil frame'i **yan yana**. Kök seviyede metin, ikon ya da serbest şekil bırakılmaz; açıklamalar `note` node'u olarak ilgili frame'in yanına konur.

Kurallar:
- Desktop kök frame'lerinde `theme: {device: "desktop"}`, mobil olanlarda `theme: {device: "mobile"}`{{#modes}}; {{mode_rule}}{{/modes}}. Boyut değişkenleri buna göre kendiliğinden değişir; mobil frame'de ayrıca sayı yazılmaz.
- Bölüm frame'leri `layout: "vertical"` ya da `"horizontal"`, `clip: true`. `layout: "none"` sadece gerçekten üst üste binen katmanlarda (slaytlar, görsel + gradyan + metin, hotspot).
- Tekrarlanan her şey `reusable` bileşenin `ref` instance'ıdır (ProductCard, Button, ArrowLink…). Sayfalar yalnızca section `ref`'lerinden oluşur.
- Çalışılan kök frame `placeholder: true`; bitince kaldırılır.
- Değer yazarken sayı yerine değişken: renk, font, yazı boyutu, boşluk hep `$…`.
{{#c2}}
- Görsel ve logo `Generate("ai" | "stock" | "svg")` ile üretilir; referansın görsel adresleri hiçbir `fill`'de kullanılmaz.
- Kök frame `metadata`'sı **oluşturulurken** yazılır (sonradan eklenen metadata kaybolabilir); ayrıntı 4. bölümde.
{{/c2}}

