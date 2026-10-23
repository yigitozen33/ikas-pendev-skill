# ikas-pendev

Ekran görüntüsünden ya da canlı bir referans siteden, **ikas Code Components**'a aktarılmaya hazır, eksiksiz bir e-ticaret teması tasarımını **pen.dev** canvas'ında üreten Claude Code skill'i.

Her projede aynı düzeni kurar: design system frame'leri → alt bileşenler → section'lar (desktop + mobil) → sayfalar → overlay'ler → motion kareleri. Tasarımdaki her katman, ikas'a aktarımda neye dönüşeceğini üstünde taşır (kök frame = ikas bileşeni, katman adı = CSS sınıfı, `metadata.prop` / `metadata.anim` / `metadata.textClass` = prop / animasyon hedefi / metin sınıfı). Skill kod yazmaz; tasarım ve aktarım paketiyle biter.

## Ne yapar

- **Brief'i soru-cevapla çıkarır.** Önce tema adını (marka adı) sorar, sonra gerektiği kadar turda girdileri, sektörü ve tonu, sayfa kapsamını, referans renklerinin aktarılıp aktarılmayacağını, renk şeması sayısını, ikas hazır sayfalarını (üyelik, hesap) ve koşullu özellikleri sorar. Dil (`tr-TR`), fiyat biçimi ve büyük harf kullanımını sormaz, kendisi belirler.
- **Referansı ölçer.** URL verilirse CSS'ten token'ları okur (`[ölçüldü]`), ekran görüntüsünden tahmin eder (`[tahmini]`). Referansın görseli, metni, logosu ve marka adı tasarıma girmez.
- **ikas renk şemalarını kurar.** 2–4 renk şeması üretir; mağaza sahibi editörde her bölüm için birini seçer. Renkler iki palet kaynağından gelir: **qrco MCP** (küratörlü katalog, anlamsal roller, kontrast ölçümü) ve **Huemint API** (marka ve web paletleriyle eğitilmiş model). Skill önce sektörün renk psikolojisine ve alanların rolüne göre bir gerekçe yazar, istenirse referans renklerini kilitler, adayları uyum, kontrast ve ayrışmaya göre seçer.
- **Her temayı ortak bir iskeletten, ama birbirine benzemeden kurar.** Yapı kütüphanesi (`library/`) her bileşenin parçalarını, durumlarını ve ikas aktarım işaretlerini verir, görünüm vermez. Tema 15 eksende (hero tipi, kart anatomisi, menü, ızgara, tipografi, renk stratejisi …) kendi seçimini yapar; bir benzerlik kapısı bu seçimleri bu bilgisayarda daha önce tasarlanan temalarla karşılaştırır.
- **Planı üretir ve denetler.** Plan veriden üretilir, lint ile kontrol edilir (WCAG kontrastı her şemada ayrı ölçülür).
- **Canvas'ı kurar ve doğrular.** Her birim okuma amaçlı kontrollerle (CHK) ve ekran görüntüsüyle kapanır.
- **Aktarım paketini hazırlar.** Port manifest'i, ikas global'leri için runbook (renk şemaları, tipografi, kırılımlar), davranış kabul kriterleri ve test verisi listesi.

## Kurulum

### 1. Gerekenler

| Gerekli | Neden | Kontrol |
|---|---|---|
| Claude Code | skill'i çalıştırır | `claude --version` |
| pen.dev uygulaması + pencil MCP | canvas'a çizer (`mcp__pencil__*`) | uygulama açıkken Claude Code'da `/mcp` listesinde `pencil` görünür |
| Python 3.9+ | plan, lint, analiz ve Huemint script'leri (yalnız standart kütüphane) | `python3 --version` |
| Node.js | yalnız `npx` ile kurulum için | `node --version` |

ikas MCP yalnızca aktarım aşamasında (ayrı iş, tema klasöründe) gerekir.

### 2. Skill'i kur

```bash
npx skills add yigitozen33/ikas-pendev-skill -g
```

Elle kurulum:

```bash
git clone https://github.com/yigitozen33/ikas-pendev-skill.git
ln -s "$PWD/ikas-pendev-skill/skills/ikas-pendev" ~/.claude/skills/ikas-pendev
```

### 3. Renk kaynaklarını bağla

**qrco MCP** (önerilen; anahtar ya da hesap gerekmez). Tüm projelerde çalışması için kullanıcı kapsamına ekle:

```bash
claude mcp add --scope user --transport http qrco https://qrco.ca/mcp
claude mcp get qrco        # Scope: User config · Status: ✔ Connected
```

`--scope user` olmadan eklenirse yalnız komutun çalıştırıldığı klasörde görünür. Ekledikten sonra yeni bir Claude Code oturumu aç; araçlar (`mcp__qrco__*`) oturum başında yüklenir.

**Huemint API**: kurulum gerekmez, `scripts/huemint.py` doğrudan bağlanır. Denemek için:

```bash
python3 -I ~/.claude/skills/ikas-pendev/scripts/huemint.py --lock color-bg=#EFEBE2 --results 5
```

Kaynaklardan biri ulaşılamazsa skill diğeriyle, ikisi de yoksa kendi seçimi ve kontrast lint'iyle devam eder; hangi kaynağın çalıştığı `globals.md` §1b'ye yazılır.

### 4. Doğrula

```bash
bash ~/.claude/skills/ikas-pendev/tests/run.sh    # passed=… failed=0
```

Claude Code'da `/mcp`: `pencil` ve `qrco` bağlı görünmeli.

## Kullanım

Tema reposunda (ya da `docs/` klasörü olan herhangi bir klasörde) Claude Code'u aç ve şöyle başla: "bu ekran görüntülerinden ikas teması tasarla", "şu siteyi analiz et" ya da doğrudan:

```
/ikas-pendev intake            # soru-cevapla brief → docs/00-brief.md
/ikas-pendev analyze           # ss/URL → docs/referans/globals.md (renk şemaları dahil) + components.md
/ikas-pendev plan              # plandata → docs/pendev/plan-<P>-<slug>.md
/ikas-pendev build             # canvas: ds → subs → section'lar → pages → overlays → motion
/ikas-pendev build ProductList # tek bölüm
/ikas-pendev verify            # docs/pendev/verify-report.md
/ikas-pendev handoff           # docs/port/port-manifest.{json,md} + globals-runbook.md
/ikas-pendev                   # brief'teki Durum tablosundan kaldığı yerden devam
```

Her faz bir dosya bırakır ve bir kapıdan geçmeden sonraki faz başlamaz. Fazlar ayrı oturumlarda koşabilir.

| Faz | Çıktı | Kapı |
|---|---|---|
| 0 intake | `docs/00-brief.md` | kullanıcı onayı |
| 1 analyze | `docs/referans/globals.md` (§1a renk şemaları, §1b renk kurgusu), `components.md` | `lint_plan.py --globals --components` |
| 2 plan | `docs/pendev/plandata/`, `plan-<P>-<slug>.md` | `lint_plan.py` + kontrast (her şemada) |
| 3 build | canvas, `docs/pendev/build-log.md` | birim başına CHK |
| 4 verify | `docs/pendev/verify-report.md` | tüm CHK PASS |
| 5 handoff | `docs/port/…` (manifest, globals runbook, davranış kriterleri, test verisi listesi) | `build_manifest.py` |

## Depo düzeni

```
skills/ikas-pendev/
├── SKILL.md            talimatlar (İngilizce; üretilen dokümanlar Türkçe)
├── references/         sözleşme, motion kataloğu, ikas sınırları, pen.dev tuzakları, sayfa kapsamı, kontrol listeleri,
│                       kalite, aktarım, port davranış kriterleri, renk şemaları (11-color: kaynaklar, renk psikolojisi),
│                       yapı kütüphanesi ve farklılaşma (12-library)
├── templates/          brief, globals, components, verify-report, port-manifest şablonları; plan prose parçaları; plandata şeması
├── library/            yapı kütüphanesi: inventory.json (parçalar, durumlar), axes.json (15 eksen), ikas-ecommerce.lib.pen (üretilir)
├── scripts/            gen_plan · lint_plan · extract_targets · pendev_checks.js · analyze_site · build_manifest · huemint ·
│                       gen_library · copy_library · axes
├── examples/ornek/     anonim örnek tema, contract 1 (brief, plandata, globals, components, verify-report)
├── evals/evals.json    tetikleme senaryoları
└── tests/run.sh        regresyon: gen_plan byte-exact, lint, extract, analyze_site fixture, renk şemaları, Huemint (çevrimdışı)
```

## Testler

```bash
bash skills/ikas-pendev/tests/run.sh
```

Testler ağa çıkmaz; Huemint ve referans site kayıtlı cevaplarla (fixture) denenir.

## Lisans

MIT. Skill ücretsiz ve ticari olmayan bir tasarım aracıdır. Huemint'in herkese açık API'si ticari olmayan kullanıma açıktır; qrco'nun genel bağlantısı hesap istemez.
