# ikas-pendev

Ekran görüntüsünden ya da canlı bir referans siteden, **ikas Code Components**'a aktarılmaya hazır, eksiksiz bir e-ticaret teması tasarımını **pen.dev** canvas'ında üreten Claude Code skill'i.

Her projede aynı düzeni kurar: design system frame'leri → alt bileşenler → section'lar (desktop + mobil) → sayfalar → overlay'ler → motion kareleri. Tasarımdaki her katman, ikas'a aktarımda neye dönüşeceğini üstünde taşır (kök frame = ikas bileşeni, katman adı = CSS sınıfı, `metadata.prop` / `metadata.anim` / `metadata.textClass` = prop / animasyon hedefi / metin sınıfı). Skill kod yazmaz; tasarım ve aktarım paketiyle biter.

## Kurulum

```bash
npx skills add Bwonk/ikas-pendev-skill -g
```

Elle kurulum: bu depoyu klonla ve `skills/ikas-pendev` klasörünü `~/.claude/skills/ikas-pendev` olarak bağla.

Gerekenler: Claude Code, pen.dev uygulaması ve pencil MCP sunucusu (`mcp__pencil__*`), Python 3.9+. ikas MCP yalnızca aktarım aşamasında (ayrı iş) gerekir. Renk şemaları için önerilen: qrco MCP (`claude mcp add --transport http qrco https://qrco.ca/mcp`, anahtar gerekmez); Huemint API'ye `scripts/huemint.py` bağlanır. İkisi de yoksa skill AI + kontrast lint ile devam eder.

## Kullanım

```
/ikas-pendev intake            # soru-cevapla brief → docs/00-brief.md
/ikas-pendev analyze           # ss/URL → docs/referans/globals.md + components.md
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
| 1 analyze | `docs/referans/globals.md`, `components.md` | `lint_plan.py --globals --components` |
| 2 plan | `docs/pendev/plandata/`, `plan-<P>-<slug>.md` | `lint_plan.py` + kontrast |
| 3 build | canvas, `docs/pendev/build-log.md` | birim başına CHK |
| 4 verify | `docs/pendev/verify-report.md` | tüm CHK PASS |
| 5 handoff | `docs/port/…` (manifest, globals runbook, davranış kriterleri, test verisi listesi) | `build_manifest.py` |

## Depo düzeni

```
skills/ikas-pendev/
├── SKILL.md            talimatlar (İngilizce; üretilen dokümanlar Türkçe)
├── references/         sözleşme, motion kataloğu, ikas sınırları, pen.dev tuzakları, sayfa kapsamı, kontrol listeleri, kalite, aktarım, port davranış kriterleri
├── templates/          brief, globals, components, verify-report, port-manifest şablonları; plan prose parçaları; plandata şeması
├── scripts/            gen_plan · lint_plan · extract_targets · pendev_checks.js · analyze_site · build_manifest
├── examples/ornek/     anonim örnek tema, contract 1 (brief, plandata, globals, components, verify-report)
├── evals/evals.json    tetikleme senaryoları
└── tests/run.sh        regresyon: gen_plan byte-exact, lint, extract, analyze_site fixture
```

## Testler

```bash
bash skills/ikas-pendev/tests/run.sh
```

## Lisans

MIT
