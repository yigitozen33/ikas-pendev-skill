#!/usr/bin/env bash
# Regression tests for the ikas-pendev skill scripts. Stdlib Python only.
# Usage: bash tests/run.sh
#   The contract-1 plan regression is byte-exact against tests/expected/plan-C.sha256 (examples/ornek).
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
SK="$(cd "$HERE/.." && pwd)"
S="$SK/scripts"; EX="$SK/examples/ornek"; FX="$HERE/fixtures"; EXP="$HERE/expected"
OUT="$HERE/out"; mkdir -p "$OUT"
pass=0; fail=0
ok()   { pass=$((pass+1)); echo "PASS  $1"; }
bad()  { fail=$((fail+1)); echo "FAIL  $1"; [ -n "${2:-}" ] && echo "      $2"; }

# 1. gen_plan: contract-1 reproduction of plan-C (byte-exact)
python3 "$S/gen_plan.py" "$EX/plandata.json" --stdout > "$OUT/plan-C.md" 2>"$OUT/gen-C.log" || bad "gen_plan C renders" "$(cat "$OUT/gen-C.log")"
want="$(cat "$EXP/plan-C.sha256" | cut -d' ' -f1)"; got="$(shasum -a 256 "$OUT/plan-C.md" | cut -d' ' -f1)"
[ "$want" = "$got" ] && ok "gen_plan C sha256" || bad "gen_plan C sha256" "want $want got $got"
grep -q "ikas-pendev contract" "$OUT/plan-C.md" && bad "contract-1 output has no marker" || ok "contract-1 output has no marker"

# 3. gen_plan: contract-2 mini dataset renders with marker
python3 "$S/gen_plan.py" "$FX/mini-plandata" --stdout > "$OUT/plan-mini.md" 2>"$OUT/gen-mini.log" && ok "gen_plan mini renders" || bad "gen_plan mini renders" "$(cat "$OUT/gen-mini.log")"
sed -n 2p "$OUT/plan-mini.md" | grep -q "ikas-pendev contract:2" && ok "mini has contract-2 marker on line 2" || bad "mini has contract-2 marker on line 2"
grep -q '^- \*\*Yalnız masaüstü katmanlar:\*\* `filter-button`' "$OUT/plan-mini.md" && ok "mini renders desktopOnly line" || bad "mini renders desktopOnly line"

# 4. lint: plan-C passes with globals; mini passes; broken fails with snapshot
python3 "$S/lint_plan.py" "$OUT/plan-C.md" --globals "$EX/globals.md" > "$OUT/lint-C.txt" 2>&1 && ok "lint plan-C OK" || bad "lint plan-C OK" "$(tail -3 "$OUT/lint-C.txt")"
grep -q "LINT OK (115 targets)" "$OUT/lint-C.txt" && ok "lint plan-C counts 115 targets" || bad "lint plan-C counts 115 targets" "$(tail -1 "$OUT/lint-C.txt")"
python3 "$S/lint_plan.py" "$OUT/plan-mini.md" > "$OUT/lint-mini.txt" 2>&1 && ok "lint mini OK" || bad "lint mini OK" "$(grep ERROR "$OUT/lint-mini.txt" | head -5)"
sed 's/→ hero-title /→ newsletter-field /' "$OUT/plan-mini.md" > "$OUT/plan-mini-newsletter.md"
python3 "$S/lint_plan.py" "$OUT/plan-mini-newsletter.md" 2>&1 | grep -q 'L21 newsletter form without `newsletter-consent`' && ok "lint: a newsletter form needs newsletter-consent (06 §3c)" || bad "lint: a newsletter form needs newsletter-consent (06 §3c)"
python3 "$S/lint_plan.py" "$FX/broken-plan.md" > "$OUT/lint-broken.txt" 2>&1 && bad "lint broken-plan fails" || ok "lint broken-plan fails"
if [ -f "$EXP/lint-broken.txt" ]; then diff -q "$OUT/lint-broken.txt" "$EXP/lint-broken.txt" >/dev/null && ok "lint broken snapshot" || bad "lint broken snapshot" "$(diff "$OUT/lint-broken.txt" "$EXP/lint-broken.txt" | head -5)"; fi
python3 "$S/lint_plan.py" --globals "$EX/globals.md" --components "$EX/components.md" > "$OUT/lint-phase1.txt" 2>&1 && ok "lint phase-1 gate on ornek docs" || bad "lint phase-1 gate on ornek docs" "$(grep ERROR "$OUT/lint-phase1.txt" | head -5)"
python3 "$S/lint_plan.py" --globals "$FX/broken-globals.md" --components "$FX/broken-components.md" > "$OUT/lint-broken-phase1.txt" 2>&1 && bad "lint broken phase-1 fails" || ok "lint broken phase-1 fails"
if [ -f "$EXP/lint-broken-phase1.txt" ]; then diff -q "$OUT/lint-broken-phase1.txt" "$EXP/lint-broken-phase1.txt" >/dev/null && ok "lint broken phase-1 snapshot" || bad "lint broken phase-1 snapshot" "$(diff "$OUT/lint-broken-phase1.txt" "$EXP/lint-broken-phase1.txt" | head -5)"; fi

# 5. extract_targets
n="$(python3 "$S/extract_targets.py" "$OUT/plan-C.md" --format ids | sort -u | wc -l | tr -d ' ')"
[ "$n" = "115" ] && ok "extract ids = 115" || bad "extract ids = 115" "got $n"
python3 "$S/extract_targets.py" "$OUT/plan-C.md" --format tsv > "$OUT/targets-C.tsv"
diff -q "$OUT/targets-C.tsv" "$EXP/targets-C.tsv" >/dev/null && ok "extract tsv snapshot" || bad "extract tsv snapshot"
python3 "$S/extract_targets.py" "$OUT/plan-C.md" --js all > "$OUT/checks-all.js" && ok "extract --js all renders" || bad "extract --js all renders"
grep -q "__" "$OUT/checks-all.js" && bad "checks js has no unfilled placeholders" "$(grep -o '__[A-Z]*__' "$OUT/checks-all.js" | sort -u | tr '\n' ' ')" || ok "checks js has no unfilled placeholders"
if command -v node >/dev/null; then node --check "$OUT/checks-all.js" 2>"$OUT/node.log" && ok "checks js parses (node --check)" || bad "checks js parses (node --check)" "$(head -3 "$OUT/node.log")"; fi
python3 "$S/extract_targets.py" "$OUT/plan-mini.md" --js all --checks parity,clip --part 2/3 > "$OUT/checks-mini-split.js" 2>"$OUT/split.log" && ok "extract --checks/--part renders" || bad "extract --checks/--part renders" "$(cat "$OUT/split.log")"
grep -q '"parity":{"ProductGrid":{"layers":\["filter-button"\]' "$OUT/checks-mini-split.js" && grep -q '"only":\["parity","clip"\],"part":\[2,3\]' "$OUT/checks-mini-split.js" && ok "checks js carries parity, only and part" || bad "checks js carries parity, only and part"
if command -v node >/dev/null; then node --check "$OUT/checks-mini-split.js" 2>"$OUT/node2.log" && ok "split checks js parses" || bad "split checks js parses" "$(head -3 "$OUT/node2.log")"; fi
python3 "$S/extract_targets.py" "$OUT/plan-mini.md" --js manifest --part 1/2 > "$OUT/manifest-part.js" && grep -q '"part":\[1,2\]' "$OUT/manifest-part.js" && ok "extract --js manifest --part renders" || bad "extract --js manifest --part renders"
python3 "$S/extract_targets.py" "$OUT/plan-mini.md" --js all --checks props > "$OUT/checks-mini-props.js" && grep -q '"props":{"HeroBanner":{"need":\[\["image","IMAGE"' "$OUT/checks-mini-props.js" && grep -q 'not-in-plan' "$OUT/checks-mini-props.js" && ok "checks js carries plan props (need/known)" || bad "checks js carries plan props (need/known)" "$(grep -o '"props":{[^]]*' "$OUT/checks-mini-props.js" | head -c 200)"
if command -v node >/dev/null; then cat > "$OUT/propmarks.js" <<'JS'
JS
  sed -n '/^const propMarks/p' "$OUT/checks-mini-props.js" >> "$OUT/propmarks.js"
  echo 'const r = propMarks("I-PDP-04 · M-11 · not · props addToCartText, addingText TEXT, image IMAGE · prop closeAriaLabel TEXT"); if (JSON.stringify(r) !== JSON.stringify([["addToCartText","TEXT"],["addingText","TEXT"],["image","IMAGE"],["closeAriaLabel","TEXT"]])) { console.error(JSON.stringify(r)); process.exit(1); }' >> "$OUT/propmarks.js"
  node "$OUT/propmarks.js" 2>"$OUT/propmarks.log" && ok "prop mark grammar parses" || bad "prop mark grammar parses" "$(cat "$OUT/propmarks.log")"
fi
python3 "$S/extract_targets.py" "$OUT/plan-mini.md" --js all --checks data > "$OUT/checks-mini-data.js" && grep -q '"data":{"[A-Za-z]*":{"need":\[\["\(data\|code\)"' "$OUT/checks-mini-data.js" && ok "checks js carries plan data marks (need/known)" || bad "checks js carries plan data marks (need/known)" "$(grep -o '"data":{[^]]*' "$OUT/checks-mini-data.js" | head -c 200)"
if command -v node >/dev/null; then sed -n '/^const dataMarks/p' "$OUT/checks-mini-data.js" > "$OUT/datamarks.js"
  echo 'const r = dataMarks("I-PDP-02 · M-02 · not · data product.image, product.video · code index · props title TEXT"); if (JSON.stringify(r) !== JSON.stringify([["data","product.image"],["data","product.video"],["code","index"]])) { console.error(JSON.stringify(r)); process.exit(1); }' >> "$OUT/datamarks.js"
  node "$OUT/datamarks.js" 2>"$OUT/datamarks.log" && ok "data mark grammar parses" || bad "data mark grammar parses" "$(cat "$OUT/datamarks.log")"
fi
python3 "$S/extract_targets.py" "$OUT/plan-mini.md" --js motion > "$OUT/checks-motion.js" 2>"$OUT/motion.log" && grep -q '"unit":{"key":"Motion"' "$OUT/checks-motion.js" && ok "extract --js motion is the Motion band" || bad "extract --js motion is the Motion band" "$(cat "$OUT/motion.log")"
python3 "$S/extract_targets.py" --help | tr -s " \n" " " | grep -q "Overlays or Motion" && ok "extract --help lists the bands" || bad "extract --help lists the bands"
python3 "$S/extract_targets.py" "$OUT/plan-mini.md" --js all --checks bogus >/dev/null 2>&1 && bad "extract rejects unknown CHK id" || ok "extract rejects unknown CHK id"
python3 "$S/extract_targets.py" "$OUT/plan-mini.md" --js all --checks storefront,dividers > "$OUT/checks-storefront.js" && ok "extract --checks storefront,dividers renders" || bad "extract --checks storefront,dividers renders"
if command -v node >/dev/null; then
  node "$HERE/tools/mock_pen.js" "$OUT/checks-storefront.js" "$FX/storefront-canvas.json" > "$OUT/storefront.txt" 2>&1
  grep -q '^CHK|storefront|FAIL|1|missing:ProductCard — kişiselleştirme$' "$OUT/storefront.txt" && ok "storefront: missing ProductCard state fails, the rest passes (06 §3d)" || bad "storefront: missing ProductCard state fails, the rest passes (06 §3d)" "$(head -3 "$OUT/storefront.txt")"
  grep -q '^CHK|dividers|WARN|2|divider style differs from the Footer.s (08 §8): HeroBanner@desktop>rectangle,HeroBanner@desktop>row-divider$' "$OUT/storefront.txt" && ok "dividers: styles unlike the Footer's warn, matching and hidden ones pass, no count limit (08 §8)" || bad "dividers: styles unlike the Footer's warn, matching and hidden ones pass, no count limit (08 §8)" "$(grep dividers "$OUT/storefront.txt")"
  sed 's/"x": 150,/"x": 4,/' "$FX/storefront-canvas.json" > "$OUT/storefront-favmixed.json"
  node "$HERE/tools/mock_pen.js" "$OUT/checks-storefront.js" "$OUT/storefront-favmixed.json" > "$OUT/storefront-favmixed.txt" 2>&1
  grep -q 'card-fav corners differ: top-right×1 (Sub/ProductCard); top-left×1 (Sub/ProductCardSmall)' "$OUT/storefront-favmixed.txt" && ok "storefront: card-fav in different corners on two card types fails" || bad "storefront: card-fav in different corners on two card types fails" "$(head -2 "$OUT/storefront-favmixed.txt")"
  sed 's/"x": 260,/"x": 4,/; s/"x": 150,/"x": 4,/' "$FX/storefront-canvas.json" > "$OUT/storefront-favleft.json"
  node "$HERE/tools/mock_pen.js" "$OUT/checks-storefront.js" "$OUT/storefront-favleft.json" > "$OUT/storefront-favleft.txt" 2>&1
  ! grep -q 'card-fav corners differ' "$OUT/storefront-favleft.txt" && ok "storefront: card-fav top-left on every card type passes (any corner, one corner)" || bad "storefront: card-fav top-left on every card type passes (any corner, one corner)" "$(head -2 "$OUT/storefront-favleft.txt")"
  sed 's/"name": "qb-bundle"/"name": "qb-list"/' "$FX/storefront-canvas.json" > "$OUT/storefront-nobundle.json"
  node "$HERE/tools/mock_pen.js" "$OUT/checks-storefront.js" "$OUT/storefront-nobundle.json" > "$OUT/storefront-nobundle.txt" 2>&1
  grep -q 'QuickBuy@desktop — set ürün>qb-bundle,QuickBuy@mobile — set ürün>qb-bundle' "$OUT/storefront-nobundle.txt" && ok "storefront: QuickBuy set ürün without qb-bundle fails (06 §3a)" || bad "storefront: QuickBuy set ürün without qb-bundle fails (06 §3a)" "$(head -2 "$OUT/storefront-nobundle.txt")"
  python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); q=[r for r in d["children"] if r["name"]=="K/Overlay/QuickBuy@desktop"][0]; q["children"][-1]["children"][2]["height"]=40; json.dump(d,open(sys.argv[2],"w"))' "$FX/storefront-canvas.json" "$OUT/storefront-favbox.json"
  node "$HERE/tools/mock_pen.js" "$OUT/checks-storefront.js" "$OUT/storefront-favbox.json" > "$OUT/storefront-favbox.txt" 2>&1
  grep -q 'QuickBuy>qb-actions heights 48/40' "$OUT/storefront-favbox.txt" && ! grep -q 'qb-actions heights' "$OUT/storefront.txt" && ok "storefront: a smaller favourite in the QuickBuy action row fails (06 §3a)" || bad "storefront: a smaller favourite in the QuickBuy action row fails (06 §3a)" "$(grep storefront "$OUT/storefront-favbox.txt")"
  python3 "$S/extract_targets.py" "$OUT/plan-mini.md" --js all --checks radius,hardcoded > "$OUT/checks-radius.js"
  node "$HERE/tools/mock_pen.js" "$OUT/checks-radius.js" "$FX/storefront-canvas.json" > "$OUT/radius.txt" 2>&1
  grep -q '^CHK|radius|PASS|' "$OUT/radius.txt" && ok "radius: product media and controls on one variable pass (02 §3)" || bad "radius: product media and controls on one variable pass (02 §3)" "$(grep radius "$OUT/radius.txt")"
  python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); d["children"][-3]["children"][0]["cornerRadius"]="$radius-control"; json.dump(d,open(sys.argv[2],"w"))' "$FX/storefront-canvas.json" "$OUT/radius-mixed.json"
  node "$HERE/tools/mock_pen.js" "$OUT/checks-radius.js" "$OUT/radius-mixed.json" > "$OUT/radius-mixed.txt" 2>&1
  grep -q '^CHK|radius|FAIL|2|product media radius differs (02 §3): .*QuickBuy>qb-media' "$OUT/radius-mixed.txt" && ok "radius: QuickBuy media rounder than the card fails" || bad "radius: QuickBuy media rounder than the card fails" "$(grep radius "$OUT/radius-mixed.txt")"
  python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); d["children"][-1]["cornerRadius"]=4; json.dump(d,open(sys.argv[2],"w"))' "$FX/storefront-canvas.json" "$OUT/radius-raw.json"
  node "$HERE/tools/mock_pen.js" "$OUT/checks-radius.js" "$OUT/radius-raw.json" > "$OUT/radius-raw.txt" 2>&1
  grep -q '^CHK|hardcoded|FAIL|1|.*cornerRadius=1' "$OUT/radius-raw.txt" && grep -q '^CHK|radius|WARN|2|control Subs radius differs' "$OUT/radius-raw.txt" && ok "radius: raw cornerRadius is hardcoded, controls on two values warn" || bad "radius: raw cornerRadius is hardcoded, controls on two values warn" "$(grep 'hardcoded\|radius' "$OUT/radius-raw.txt")"
  python3 "$S/extract_targets.py" "$OUT/plan-mini.md" --js all --checks spacing > "$OUT/checks-spacing.js"
  node "$HERE/tools/mock_pen.js" "$OUT/checks-spacing.js" "$FX/spacing-canvas.json" > "$OUT/spacing.txt" 2>&1
  grep -q '^CHK|spacing|PASS|7|7/7 page seams$' "$OUT/spacing.txt" && ok "spacing: page seams, Footer top, a first-section override, grid and split gaps pass (02 §3b)" || bad "spacing: page seams, Footer top, a first-section override, grid and split gaps pass (02 §3b)" "$(grep spacing "$OUT/spacing.txt")"
  python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); r={n["id"]:n for n in d["children"]}; r["s5"]["padding"]=[0,"$space-page","$space-page","$space-page"]; r["s3"]["padding"]=[48,"$space-page","$space-section","$space-page"]; d["children"]=[n for n in d["children"] if n["id"]!="p2"]; json.dump(d,open(sys.argv[2],"w"))' "$FX/spacing-canvas.json" "$OUT/spacing-bad.json"
  node "$HERE/tools/mock_pen.js" "$OUT/checks-spacing.js" "$OUT/spacing-bad.json" > "$OUT/spacing-bad.txt" 2>&1
  grep -q '^CHK|spacing|FAIL|2|2/4 page seams bad:Home@desktop:Shelf-bottom=\$space-section,Home@desktop:Shelf-top=48,Home@desktop:Footer-top=0$' "$OUT/spacing-bad.txt" && ok "spacing: Footer on the last section, double gaps and raw tops fail (02 §3b)" || bad "spacing: Footer on the last section, double gaps and raw tops fail (02 §3b)" "$(grep spacing "$OUT/spacing-bad.txt")"
  python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); r={n["id"]:n for n in d["children"]}; r["s1"]["padding"]=[0,16,0,16]; r["s4"]["children"][0]["gap"]=40; r["s3"]["children"][0]["gap"]=24; d["children"]=[n for n in d["children"] if n["id"]!="p2"]; json.dump(d,open(sys.argv[2],"w"))' "$FX/spacing-canvas.json" "$OUT/spacing-warn.json"
  node "$HERE/tools/mock_pen.js" "$OUT/checks-spacing.js" "$OUT/spacing-warn.json" > "$OUT/spacing-warn.txt" 2>&1
  grep -q '^CHK|spacing|WARN|4|4/4 page seams check:Section/Header@desktop:side=16,Section/Shelf@desktop>shelf-grid:grid-gap=24,Section/ProductDetail@desktop>pdp-main:split-gap=40$' "$OUT/spacing-warn.txt" && ok "spacing: an off-token page edge, grid gap or column split warns (02 §3b)" || bad "spacing: an off-token page edge, grid gap or column split warns (02 §3b)" "$(grep spacing "$OUT/spacing-warn.txt")"
  python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); r={n["id"]:n for n in d["children"]}; r["s3"]["context"]="overlap $size-overlap"; r["s3"]["padding"][0]="$space-md"; d["children"]=[n for n in d["children"] if n["id"]!="p2"]; json.dump(d,open(sys.argv[2],"w")); r["p1"]["children"][1].update({"clip": False, "height": 552}); json.dump(d,open(sys.argv[3],"w"))' "$FX/spacing-canvas.json" "$OUT/overlap-bad.json" "$OUT/overlap-ok.json"
  node "$HERE/tools/mock_pen.js" "$OUT/checks-spacing.js" "$OUT/overlap-bad.json" > "$OUT/overlap-bad.txt" 2>&1
  node "$HERE/tools/mock_pen.js" "$OUT/checks-spacing.js" "$OUT/overlap-ok.json" > "$OUT/overlap-ok.txt" 2>&1
  grep -q '^CHK|spacing|FAIL|.*Shelf-overlap=prev ref needs clip:false' "$OUT/overlap-bad.txt" && grep -q '^CHK|spacing|PASS|4|' "$OUT/overlap-ok.txt" && ok "spacing: a riding section needs the ref above shortened with clip off (02 §3c)" || bad "spacing: a riding section needs the ref above shortened with clip off (02 §3c)" "$(cat "$OUT/overlap-bad.txt" "$OUT/overlap-ok.txt")"
  python3 "$S/extract_targets.py" "$OUT/plan-mini.md" --js all --checks subfit > "$OUT/checks-subfit.js"
  python3 -c 'import json,sys
def rng(w, fixed):
    rail = {"id": "rail", "name": "range-rail", "type": "rectangle", "x": 0, "y": 8, "width": 320 if fixed else "fill_container", "height": 4}
    return {"children": [{"id": "pr", "name": "K/Sub/PriceRange", "type": "frame", "reusable": True, "x": 0, "y": 0, "width": w, "height": 80,
            "children": [{"id": "trk", "name": "range-track", "type": "frame", "layout": "none" if fixed else "horizontal", "x": 0, "y": 0, "width": "fill_container", "height": 20, "children": [rail]}]}]}
json.dump(rng(276, True), open(sys.argv[1], "w")); json.dump(rng(276, False), open(sys.argv[2], "w"))' "$OUT/subfit-bad.json" "$OUT/subfit-ok.json"
  node "$HERE/tools/mock_pen.js" "$OUT/checks-subfit.js" "$OUT/subfit-bad.json" > "$OUT/subfit-bad.txt" 2>&1
  node "$HERE/tools/mock_pen.js" "$OUT/checks-subfit.js" "$OUT/subfit-ok.json" > "$OUT/subfit-ok.txt" 2>&1
  grep -q '^CHK|subfit|WARN|1|.*Sub/PriceRange>range-rail=320' "$OUT/subfit-bad.txt" && grep -q '^CHK|subfit|PASS' "$OUT/subfit-ok.txt" && ok "subfit: a fixed 320 rail in a 276 PriceRange warns, a fill rail passes (02 §1)" || bad "subfit: a fixed 320 rail in a 276 PriceRange warns, a fill rail passes (02 §1)" "$(cat "$OUT/subfit-bad.txt" "$OUT/subfit-ok.txt")"
fi

# 6. analyze_site on offline fixture
if [ -f "$FX/site/site-snapshot.html" ]; then
  python3 -I "$S/analyze_site.py" --fixture "$FX/site" > "$OUT/analyze-site.txt" 2>"$OUT/analyze.log" && ok "analyze_site fixture runs" || bad "analyze_site fixture runs" "$(tail -3 "$OUT/analyze.log")"
  for v in "#7A7A7A" "#1C1C1C"; do grep -qi "$v" "$OUT/analyze-site.txt" && ok "analyze finds $v" || bad "analyze finds $v"; done
  diff -q "$OUT/analyze-site.txt" "$EXP/analyze-site.txt" >/dev/null && ok "analyze snapshot" || bad "analyze snapshot" "$(diff "$OUT/analyze-site.txt" "$EXP/analyze-site.txt" | head -5)"
else
  echo "SKIP  analyze_site fixture (site-snapshot.html not in git; run tests/tools/fetch_fixture.sh to enable)"
fi

# 7. build_manifest on the synthetic ornek canvas dump
python3 "$S/build_manifest.py" --plandata "$EX/plandata.json" --plan "$OUT/plan-C.md" --dump "$FX/ornek-canvas-dump.txt" -o "$OUT/port" > "$OUT/manifest.log" 2>&1 && ok "build_manifest ornek exit 0" || bad "build_manifest ornek exit 0" "$(tail -3 "$OUT/manifest.log")"
tail -1 "$OUT/manifest.log" | diff -q - "$EXP/manifest-ornek.txt" >/dev/null && ok "build_manifest summary snapshot" || bad "build_manifest summary snapshot" "$(tail -1 "$OUT/manifest.log")"
grep -v '^ROOT|C/Section/Timeline@' "$FX/ornek-canvas-dump.txt" | sed -E 's/C-PDP-03;?//' > "$OUT/ornek-canvas-dump-broken.txt"
python3 "$S/build_manifest.py" --plandata "$EX/plandata.json" --plan "$OUT/plan-C.md" --dump "$OUT/ornek-canvas-dump-broken.txt" -o "$OUT/port-broken" > "$OUT/manifest-broken.log" 2>&1 && bad "build_manifest broken dump exits 1" || ok "build_manifest broken dump exits 1"
nb="$(grep -c '|BLOCKING$' "$OUT/manifest-broken.log" | tr -d ' ')"; [ "$nb" = "2" ] && ok "build_manifest broken dump has 2 blocking" || bad "build_manifest broken dump has 2 blocking" "got $nb"

python3 "$S/build_manifest.py" --plandata "$EX/plandata.json" --plan "$OUT/plan-C.md" --dump "$FX/ornek-canvas-dump.txt" --globals "$FX/globals-c2.md" -o "$OUT/port-globals" > "$OUT/manifest-globals.log" 2>&1 && ok "build_manifest --globals exit 0" || bad "build_manifest --globals exit 0" "$(tail -3 "$OUT/manifest-globals.log")"
grep -q '"name": "Örnek / Gece"\|Gece' "$OUT/port-globals/globals-runbook.md" && grep -q '"breakpoints": \[{"breakpoint_id": "<Kırılım / Laptop id>", "font_size": "80px"}' "$OUT/port-globals/globals-runbook.md" && ok "runbook uses globals.md §1a schemes and §2a breakpoints" || bad "runbook uses globals.md §1a schemes and §2a breakpoints"
! grep -q '"text_transform"\|· uppercase' "$OUT/port-globals/globals-runbook.md" && grep -q 'Büyük harf stilleri' "$OUT/port-globals/globals-runbook.md" && ok "runbook: no text_transform on text styles, uppercase note instead (04 §4)" || bad "runbook: no text_transform on text styles, uppercase note instead (04 §4)"

# 8. colour schemes: 2-4 schemes on the `mode` axis, 11-color sources, Huemint offline
SC="$OUT/schemes"; rm -rf "$SC"; mkdir -p "$SC"; cp -R "$FX/mini-plandata" "$SC/pd"
python3 - "$SC/pd" <<'PY'
import glob, json, sys
d = sys.argv[1]
t = json.load(open(d + "/theme.json"))
t["modes"] = ["kagit", "murekkep", "kil"]
for k, v in t["variables"]["colors"].items():
    t["variables"]["colors"][k] = [v[0], v[1], {"color-bg": "#E4DCCF", "color-transparent": "#E4DCCF00"}.get(k, v[0])]
json.dump(t, open(d + "/theme.json", "w"), ensure_ascii=False, indent=1)
for f in glob.glob(d + "/sections/*.json"):
    s = json.load(open(f))
    if s.get("mode") == "dark":
        s["mode"] = "murekkep"
        json.dump(s, open(f, "w"), ensure_ascii=False, indent=1)
PY
python3 "$S/gen_plan.py" "$SC/pd" --stdout > "$SC/plan.md" 2>"$SC/gen.log" && grep -q '`mode: kagit | murekkep | kil`' "$SC/plan.md" && grep -q '`mode: "murekkep"` · `mode: "kil"`' "$SC/plan.md" && ok "gen_plan renders three colour schemes" || bad "gen_plan renders three colour schemes" "$(cat "$SC/gen.log")"
cat "$EX/globals.md" "$FX/globals-schemes-tail.md" > "$SC/globals.md"
python3 "$S/lint_plan.py" "$SC/plan.md" --globals "$SC/globals.md" > "$SC/lint.txt" 2>&1 && grep -q '@kil|L14' "$SC/lint.txt" && ok "lint: three schemes pass, contrast measured per scheme" || bad "lint: three schemes pass, contrast measured per scheme" "$(grep ERROR "$SC/lint.txt" | head -3)"
sed 's/| Kil |$/| Toprak |/; s/^| ikas slot | pen.dev token | Kağıt (varsayılan) | Mürekkep | Kil |/| ikas slot | pen.dev token | Kağıt (varsayılan) | Mürekkep | Toprak |/' "$SC/globals.md" > "$SC/globals-renamed.md"
python3 "$S/lint_plan.py" "$SC/plan.md" --globals "$SC/globals-renamed.md" 2>&1 | grep -q 'L22 plan mode values' && ok "lint: plan modes must be the §1a scheme slugs" || bad "lint: plan modes must be the §1a scheme slugs"
sed '/^### 1b\. Renk kurgusu/,/^### 2a\./{/^### 2a\./!d;}' "$SC/globals.md" > "$SC/globals-no1b.md"
python3 "$S/lint_plan.py" "$SC/plan.md" --globals "$SC/globals-no1b.md" 2>&1 | grep -q '§1b|L22 no colour rationale' && ok "lint: §1b colour rationale is required" || bad "lint: §1b colour rationale is required"
sed 's/ \[huemint\] \[tahmini\]/ [tahmini]/g' "$SC/globals.md" > "$SC/globals-untagged.md"
python3 "$S/lint_plan.py" "$SC/plan.md" --globals "$SC/globals-untagged.md" 2>&1 | grep -q 'WARN|§1a|L22 2 scheme value(s) without a source tag' && ok "lint: scheme values carry a source tag" || bad "lint: scheme values carry a source tag"
python3 - "$SC/pd/theme.json" "$SC/pd5.json" <<'PY'
import json, sys
t = json.load(open(sys.argv[1])); t["modes"] = ["a", "b", "c", "d", "e"]
json.dump(t, open(sys.argv[2], "w"))
PY
mkdir -p "$SC/pd5" && cp -R "$SC/pd/sections" "$SC/pd5/" && mv "$SC/pd5.json" "$SC/pd5/theme.json"
python3 "$S/gen_plan.py" "$SC/pd5" --stdout >/dev/null 2>"$SC/gen5.log" && bad "gen_plan rejects five schemes" || { grep -q '2-4 distinct colour-scheme slugs' "$SC/gen5.log" && ok "gen_plan rejects five schemes" || bad "gen_plan rejects five schemes" "$(head -3 "$SC/gen5.log")"; }
python3 "$S/build_manifest.py" --plandata "$EX/plandata.json" --plan "$OUT/plan-C.md" --dump "$FX/ornek-canvas-dump.txt" --globals "$SC/globals.md" -o "$SC/port" > "$SC/manifest.log" 2>&1 && grep -q 'Örnek / Kil' "$SC/port/globals-runbook.md" && grep -q 'İlk şemadan sonraki her şemadaki' "$SC/port/globals-runbook.md" && ok "runbook writes every §1a scheme" || bad "runbook writes every §1a scheme" "$(tail -3 "$SC/manifest.log")"
python3 -I "$S/huemint.py" --fixture "$FX/huemint-response.json" --lock 'color-bg=#EFEBE2' > "$SC/huemint.md" 2>&1 && [ "$(grep -c '^| [0-9]' "$SC/huemint.md")" = "4" ] && sed -n '/^| 1 /p' "$SC/huemint.md" | grep -q '🔒.*| geçti |$' && ok "huemint: offline candidates parsed, invalid ones dropped, passing first" || bad "huemint: offline candidates parsed, invalid ones dropped, passing first" "$(head -5 "$SC/huemint.md")"
python3 -I "$S/huemint.py" --fixture "$FX/huemint-response.json" --lock 'color-xx=#EFEBE2' >/dev/null 2>&1; [ $? = 2 ] && ok "huemint rejects an unknown role lock" || bad "huemint rejects an unknown role lock"

echo "----"; echo "passed=$pass failed=$fail"
[ "$fail" = "0" ]
