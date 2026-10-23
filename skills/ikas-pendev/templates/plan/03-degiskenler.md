
## 3. Değişkenler

İlk iş olarak tanımlanır. {{#vars_intro}}{{vars_intro}}{{/vars_intro}}{{^vars_intro}}Adlar sözleşmede sabittir (`globals.md` ile eşleşir); değerler bu temaya özgüdür.{{/vars_intro}}

```js
{{variables_js}}
```
{{#c2}}

Çekirdek set **41 değişken**dir ve adları değişmez (aktarım bu adlara güvenir). Sözleşme 2 ekleri: `color-transparent` (gradyan başlangıcı, `#RRGGBB00`), `size-logo` (logo yüksekliği, `device` ekseni), `color-danger` ve `color-success` (form ve stok durumları). Eksenler: `device: desktop | mobile`{{#modes}}, `mode: {{mode_axis}}`{{/modes}}.
{{/c2}}

Font doğrulama: `execute` yanıtında "Font family … is invalid" uyarısı çıkarsa o değişkeni değiştir. Canvas üzerinde denenip geçerli çıkan aileler: {{font_valid}}.{{#font_invalid}} Geçersiz çıkanlar: {{font_invalid}}.{{/font_invalid}}{{#c2}} ikas yalnızca Google Fonts (latin-ext) yükler; seçilen her aile orada da bulunmalı.{{/c2}}

Yazı stili eşlemesi: {{type_styles}}

