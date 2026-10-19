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

echo "----"; echo "passed=$pass failed=$fail"
[ "$fail" = "0" ]
