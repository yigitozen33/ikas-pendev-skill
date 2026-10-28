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
  grep -q '^CHK|dividers|FAIL|13|row dividers (08 §8; spacing, or \*-edge): HeroBanner@desktop>heading-divider,HeroBanner@desktop>list-separator,HeroBanner@desktop>stat-rule,HeroBanner@desktop>row-divider,Footer@desktop>col-divider' "$OUT/storefront.txt" && ok "dividers: row/item dividers fail, hidden ones pass, thin lines are listed to check (08 §8)" || bad "dividers: row/item dividers fail, hidden ones pass, thin lines are listed to check (08 §8)" "$(grep dividers "$OUT/storefront.txt")"
  sed 's/"col-divider-\([0-9]\)"/"col-\1-edge"/; s/"heading-divider"/"bar-edge"/; s/"list-separator"/"group-edge"/; s/"stat-rule"/"share-edge"/; s/"row-divider"/"sheet-edge"/; s/"panel-line"/"panel-edge"/' "$FX/storefront-canvas.json" | python3 -c 'import json,sys; d=json.load(sys.stdin); [r.__setitem__("children",[c for c in r.get("children",[]) if c.get("name")!="rectangle"]) for r in d["children"]]; [r.__setitem__("children",[c for c in r.get("children",[]) if not c.get("name","").startswith("col-divider")]) for r in d["children"]]; json.dump(d,open(sys.argv[1],"w"))' "$OUT/dividers-edge.json"
  node "$HERE/tools/mock_pen.js" "$OUT/checks-storefront.js" "$OUT/dividers-edge.json" > "$OUT/dividers-edge.txt" 2>&1
  python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); r=[x for x in d["children"] if x["name"]=="K/Section/Footer@desktop"][0]; r["children"].append({"id": "sd", "name": "social-divider", "type": "frame", "layout": "horizontal", "x": 0, "y": 300, "width": 480, "height": 17, "children": [{"id": "sdt", "name": "social-or", "type": "text", "content": "ya da", "x": 0, "y": 0, "width": 40, "height": 17}]}); json.dump(d,open(sys.argv[1],"w"))' "$OUT/dividers-edge.json"
  node "$HERE/tools/mock_pen.js" "$OUT/checks-storefront.js" "$OUT/dividers-edge.json" > "$OUT/dividers-wrap.txt" 2>&1
  grep -q '^CHK|dividers|PASS|0|' "$OUT/dividers-wrap.txt" && ok "dividers: a wrapper named *-divider holding only text is not a line" || bad "dividers: a wrapper named *-divider holding only text is not a line" "$(grep dividers "$OUT/dividers-wrap.txt")"
  grep -q '^CHK|dividers|PASS|0|no row or item dividers' "$OUT/dividers-edge.txt" && ok "dividers: structural edges named *-edge pass (08 §8)" || bad "dividers: structural edges named *-edge pass (08 §8)" "$(grep dividers "$OUT/dividers-edge.txt")"
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
  SPD="$OUT/sproles"; rm -rf "$SPD"; mkdir -p "$SPD"; cp -R "$FX/mini-plandata" "$SPD/pd"
  python3 -c 'import json,sys; t=json.load(open(sys.argv[1])); t["variables"]["numbers"]["space-band"]=[20,8]; t["spacing"]={"pageEdge":"space-band","headerGap":"space-band"}; json.dump(t,open(sys.argv[1],"w"),ensure_ascii=False)' "$SPD/pd/theme.json"
  python3 -I "$S/gen_plan.py" "$SPD/pd" --stdout > "$SPD/plan.md" 2>"$SPD/gen.log" && grep -q '^### 3b. Boşluk sistemi' "$SPD/plan.md" && grep -q '| `pageEdge` | `$space-band` |' "$SPD/plan.md" && python3 "$S/lint_plan.py" "$SPD/plan.md" >/dev/null 2>&1 && ok "gen_plan renders the theme's spacing roles (plan §3b)" || bad "gen_plan renders the theme's spacing roles (plan §3b)" "$(cat "$SPD/gen.log")"
  python3 "$S/extract_targets.py" "$SPD/plan.md" --js all --checks spacing > "$SPD/checks.js"
  python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); r={n["id"]:n for n in d["children"]}; r["s1"]["padding"]=[0,"$space-band",0,"$space-band"]; r["s2"]["padding"]=["$space-band","$space-band",0,"$space-band"]; [r[k].__setitem__("padding",[r[k]["padding"][0],"$space-band",r[k]["padding"][2],"$space-band"]) for k in ("s3","s4","s5")]; d["children"]=[n for n in d["children"] if n["id"]!="p2"]; json.dump(d,open(sys.argv[2],"w"))' "$FX/spacing-canvas.json" "$SPD/band.json"
  node "$HERE/tools/mock_pen.js" "$SPD/checks.js" "$SPD/band.json" > "$SPD/theme.txt" 2>&1
  node "$HERE/tools/mock_pen.js" "$OUT/checks-spacing.js" "$SPD/band.json" > "$SPD/default.txt" 2>&1
  grep -q '^CHK|spacing|PASS|4|' "$SPD/theme.txt" && grep -q '^CHK|spacing|WARN|4|.*Hero-first-top=\$space-band.*Header@desktop:side=\$space-band' "$SPD/default.txt" && ok "spacing: a 20/8 band edge passes when the theme names it, warns against the default roles" || bad "spacing: a 20/8 band edge passes when the theme names it, warns against the default roles" "$(cat "$SPD/theme.txt" "$SPD/default.txt" | grep spacing)"
  python3 -c 'import json,sys; t=json.load(open(sys.argv[1])); t["spacing"]={"pageEdge":"space-nope","gutter":"space-grid"}; json.dump(t,open(sys.argv[1],"w"),ensure_ascii=False)' "$SPD/pd/theme.json"
  python3 -I "$S/gen_plan.py" "$SPD/pd" --validate-only > "$SPD/invalid.log" 2>&1; [ $? = 1 ] && grep -q 'spacing.pageEdge: "space-nope" is not in' "$SPD/invalid.log" && grep -q 'unknown role "gutter"' "$SPD/invalid.log" && ok "gen_plan rejects an unknown spacing role or token" || bad "gen_plan rejects an unknown spacing role or token" "$(cat "$SPD/invalid.log")"
  python3 "$S/extract_targets.py" "$OUT/plan-mini.md" --js all --checks temp > "$OUT/checks-temp.js"
  python3 -c 'import json,sys
d = json.load(open(sys.argv[1]))
box = {"id": "box", "name": "Öneriler (geçici)", "type": "frame", "layout": "horizontal", "x": 0, "y": 9000, "width": 2000, "height": 900,
       "children": [{"id": "t1", "name": "Sepet önerileri (geçici)", "type": "frame", "x": 0, "y": 0, "width": 900, "height": 900}]}
d["children"].append(box); json.dump(d, open(sys.argv[2], "w"))
d["children"].append({"id": "t2", "name": "PDP önerileri (geçici)", "type": "frame", "x": 51030, "y": -20000, "width": 900, "height": 900}); json.dump(d, open(sys.argv[3], "w"))' "$FX/spacing-canvas.json" "$OUT/temp-ok.json" "$OUT/temp-bad.json"
  node "$HERE/tools/mock_pen.js" "$OUT/checks-temp.js" "$OUT/temp-ok.json" > "$OUT/temp-ok.txt" 2>&1
  node "$HERE/tools/mock_pen.js" "$OUT/checks-temp.js" "$OUT/temp-bad.json" > "$OUT/temp-bad.txt" 2>&1
  grep -q '^CHK|temp|PASS|0|one options box below the design' "$OUT/temp-ok.txt" && grep -q '^CHK|temp|FAIL|1|.*PDP önerileri (geçici)$' "$OUT/temp-bad.txt" && ok "temp: topic frames live in the one options box below the design (07 §7)" || bad "temp: topic frames live in the one options box below the design (07 §7)" "$(cat "$OUT/temp-ok.txt" "$OUT/temp-bad.txt")"
  SD="$OUT/seed"; rm -rf "$SD"; mkdir -p "$SD"; cp -R "$FX/mini-plandata" "$SD/pd"
  python3 -c 'import json,sys; t=json.load(open(sys.argv[1])); t["sampleCatalog"]=json.load(open(sys.argv[2])); json.dump(t,open(sys.argv[1],"w"),ensure_ascii=False)' "$SD/pd/theme.json" "$FX/seed/catalog.json"
  python3 -I "$S/gen_plan.py" "$SD/pd" --stdout > "$SD/plan.md" 2>"$SD/gen.log" && grep -q '^### 6.6 Örnek katalog' "$SD/plan.md" && grep -q -- '- Toplam (kuponsuz): 799,60 TL' "$SD/plan.md" && python3 "$S/lint_plan.py" "$SD/plan.md" >/dev/null 2>&1 && ok "gen_plan renders the sample catalogue with computed cart totals (plan §6.6)" || bad "gen_plan renders the sample catalogue with computed cart totals (plan §6.6)" "$(cat "$SD/gen.log")"
  python3 "$S/extract_targets.py" "$SD/plan.md" --js all --checks seed > "$SD/checks.js"
  node "$HERE/tools/mock_pen.js" "$SD/checks.js" "$FX/seed/canvas.json" > "$SD/ok.txt" 2>&1
  grep -q '^CHK|seed|PASS|' "$SD/ok.txt" && ok "seed: names, prices, images, limits, quantities and totals match the catalogue" || bad "seed: names, prices, images, limits, quantities and totals match the catalogue" "$(grep seed "$SD/ok.txt")"
  sed 's/"189,90 TL"/"520,00 TL"/; s/"0 \/ 120"/"0 \/ 500"/; s/"content": "799,60 TL"/"content": "759,60 TL"/; s/product-baby-care-set.png/product-sunscreen.png/; s/"content": "C Vitamini 1000 mg",/"content": "C Vitamini",/' "$FX/seed/canvas.json" > "$SD/bad.json"
  node "$HERE/tools/mock_pen.js" "$SD/checks.js" "$SD/bad.json" > "$SD/bad.txt" 2>&1
  grep -q '^CHK|seed|FAIL|7|≠ catalogue: ProductGrid>card-title:vitc.name=C Vitamini,QuickBuy>cline-title:vitc.name=C Vitamini,QuickBuy>note-counter:vitc.limit=500,QuickBuy>cline-total:box.price=520,00 TL,QuickBuy>drawer-tota' "$SD/bad.txt" && ok "seed: a renamed product, another limit, a different price and a coupon total without a coupon fail" || bad "seed: a renamed product, another limit, a different price and a coupon total without a coupon fail" "$(grep seed "$SD/bad.txt")"
  python3 "$S/build_manifest.py" --plandata "$SD/pd" --plan "$SD/plan.md" -o "$SD/port" > "$SD/manifest.log" 2>&1; grep -q '^## Örnek katalog (canvas ile aynı)' "$SD/port/seed-checklist.md" && grep -q -- '- Toplam (kuponsuz): 799,60 TL' "$SD/port/seed-checklist.md" && ok "seed-checklist carries the same sample catalogue and cart" || bad "seed-checklist carries the same sample catalogue and cart" "$(tail -3 "$SD/manifest.log")"
  python3 -c 'import json,sys; t=json.load(open(sys.argv[1])); t["sampleCatalog"]["cart"]["lines"][0]["product"]="nope"; json.dump(t,open(sys.argv[1],"w"),ensure_ascii=False)' "$SD/pd/theme.json"
  python3 -I "$S/gen_plan.py" "$SD/pd" --validate-only > "$SD/invalid.log" 2>&1; [ $? = 1 ] && grep -q 'sampleCatalog.cart.lines\[0\].product: unknown product key' "$SD/invalid.log" && ok "gen_plan rejects a sample cart line with an unknown product" || bad "gen_plan rejects a sample cart line with an unknown product" "$(cat "$SD/invalid.log")"
  python3 "$S/extract_targets.py" "$OUT/plan-mini.md" --js all --checks subfit > "$OUT/checks-subfit.js"
  python3 -c 'import json,sys
def rng(w, fixed):
    rail = {"id": "rail", "name": "range-rail", "type": "rectangle", "x": 0, "y": 8, "width": 320 if fixed else "fill_container", "height": 4}
    return {"children": [{"id": "pr", "name": "K/Sub/PriceRange", "type": "frame", "reusable": True, "x": 0, "y": 0, "width": w, "height": 80,
            "children": [{"id": "trk", "name": "range-track", "type": "frame", "layout": "none" if fixed else "horizontal", "x": 0, "y": 0, "width": "fill_container", "height": 20, "children": [rail]}]}]}
json.dump(rng(276, True), open(sys.argv[1], "w")); json.dump(rng(276, False), open(sys.argv[2], "w"))' "$OUT/subfit-bad.json" "$OUT/subfit-ok.json"
  python3 -c 'import json,sys; json.dump({"children": [{"id": "fb", "name": "K/Sub/FavoriteButton", "type": "frame", "reusable": True, "x": 0, "y": 0, "width": 40, "height": 40, "layout": "none", "children": [{"id": "st", "name": "fav-stage", "type": "frame", "layout": "none", "x": 0, "y": 0, "width": 40, "height": 40, "children": [{"id": "hh", "name": "fav-heart", "type": "icon", "x": 10, "y": 10, "width": 20, "height": 20}]}]}]}, open(sys.argv[1], "w"))' "$OUT/subfit-icon.json"
  node "$HERE/tools/mock_pen.js" "$OUT/checks-subfit.js" "$OUT/subfit-icon.json" > "$OUT/subfit-icon.txt" 2>&1
  grep -q '^CHK|subfit|PASS' "$OUT/subfit-icon.txt" && ok "subfit: a 20 px icon in a small Sub's layout:none stage passes" || bad "subfit: a 20 px icon in a small Sub's layout:none stage passes" "$(cat "$OUT/subfit-icon.txt")"
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

# 9 · structure library inventory (12-library.md)
python3 -I - "$SK/library/inventory.json" > "$OUT/inventory.txt" 2>&1 <<'PY' && ok "library inventory: unique names, kebab layers, every part req or opt, opt parts ikas-checked" || bad "library inventory: unique names, kebab layers, every part req or opt, opt parts ikas-checked" "$(cat "$OUT/inventory.txt")"
import json, re, sys
d = json.load(open(sys.argv[1])); errs = []
names = [c["name"] for c in d["components"]]
errs += [f"duplicate {n}" for n in set(names) if names.count(n) > 1]
for c in d["components"]:
    if c["kind"] not in d["kinds"]: errs.append(f"{c['name']}: kind {c['kind']}")
    if not c.get("states"): errs.append(f"{c['name']}: no states")
    for b in c["basis"] + [m["basis"] for m in c.get("must", [])]:
        if b not in d["basis"]: errs.append(f"{c['name']}: basis {b}")
    for p in c["parts"]:
        if not re.fullmatch(r"[a-z][a-z0-9-]*", p["layer"]): errs.append(f"{c['name']}: layer {p['layer']}")
        if bool(p.get("req")) == bool(p.get("opt")): errs.append(f"{c['name']}.{p['layer']}: req xor opt")
        if p.get("opt") and p.get("ikas") not in ("yes", "check"): errs.append(f"{c['name']}.{p['layer']}: opt part needs ikas yes|check")
print("\n".join(errs)); sys.exit(1 if errs else 0)
PY

python3 -I "$S/gen_library.py" --check > "$OUT/library.txt" 2>&1 && ok "library .pen is what the inventory gives (gen_library --check)" || bad "library .pen is what the inventory gives (gen_library --check)" "$(cat "$OUT/library.txt")"
python3 -I - "$SK/library/inventory.json" "$SK/library/ikas-ecommerce.lib.pen" > "$OUT/library-parts.txt" 2>&1 <<'PY' && ok "library: every component is a reusable root, every part a named layer, optional parts disabled" || bad "library: every component is a reusable root, every part a named layer, optional parts disabled" "$(cat "$OUT/library-parts.txt")"
import json, sys
inv = json.load(open(sys.argv[1])); pen = json.load(open(sys.argv[2])); errs = []
roots = {}
def walk(n):
    if n.get("reusable"): roots[n["metadata"]["ikas"]] = n
    for ch in n.get("children", []): walk(ch)
for ch in pen["children"]: walk(ch)
for c in inv["components"]:
    r = roots.get(c["name"])
    if not r: errs.append(f"{c['name']}: no reusable root"); continue
    layers = {ch["name"]: ch for ch in r["children"]}
    for p in c["parts"]:
        n = layers.get(p["layer"])
        if not n: errs.append(f"{c['name']}.{p['layer']}: missing")
        elif bool(p.get("opt")) != (n.get("enabled") is False): errs.append(f"{c['name']}.{p['layer']}: enabled flag")
import re
used = {v[1:] for v in re.findall(r'"(\$[a-z0-9-]+)"', json.dumps(pen["children"]))}
errs += [f"undefined token {t}" for t in sorted(used - set(pen["variables"]))]
print("\n".join(errs)); sys.exit(1 if errs else 0)
PY

CL="$OUT/copylib"; rm -rf "$CL"; mkdir -p "$CL"
python3 -I "$S/copy_library.py" "$FX/mini-plandata" -o "$CL/kaya.pen" --with Toast > "$CL/copy.log" 2>&1 && python3 -I - "$CL/kaya.pen" "$SK/library/ikas-ecommerce.lib.pen" > "$CL/check.txt" 2>&1 <<'PY' && ok "copy_library: planned components copied with theme prefix, ids, metadata and plandata tokens" || bad "copy_library: planned components copied with theme prefix, ids, metadata and plandata tokens" "$(cat "$CL/copy.log" "$CL/check.txt")"
import json, sys
t = json.load(open(sys.argv[1])); lib = json.dumps(json.load(open(sys.argv[2]))); errs = []
roots = {n["name"]: n for n in t["children"] if n["type"] == "frame"}
want = ["K/Sub/Button", "K/Sub/ArrowLink", "K/Sub/ProductCard", "K/Overlay/FilterDrawer@desktop", "K/Overlay/QuickBuy@mobile", "K/Overlay/Toast@desktop"]
errs += [f"missing root {w}" for w in want if w not in roots]
errs += [f"unexpected {n}" for n in roots if "Header" in n or "ConfirmModal" in n]
ids = {n["id"] for n in t["children"]}
errs += [f"ref to missing root {n['name']}" for n in t["children"] for k in [n] + n.get("children", []) if k["type"] == "ref" and k["ref"] not in ids]
st = next((n for n in t["children"] if n["name"] == "K/Sub/ProductCard — sepette"), None)
if not st: errs.append("state root missing")
elif st["type"] != "frame" or st.get("metadata", {}).get("state") != "sepette" or st["metadata"].get("role") != "sub" \
        or st["metadata"].get("type") != "kaya" or [k["type"] for k in st["children"]] != ["ref"] \
        or st["children"][0]["ref"] != roots["K/Sub/ProductCard"]["id"]:
    errs.append(f"state root is not a metadata wrapper around a ref: {st}")
mst = next((n for n in t["children"] if n["name"].startswith("K/Overlay/QuickBuy@mobile — ")), None)
if mst and mst["metadata"].get("device") != "mobile": errs.append("device state wrapper lacks device")
ids |= {k["id"] for n in t["children"] for k in n.get("children", []) if k["type"] == "ref"}
errs += [f"library id reused {i}" for i in ids if f'"{i}"' in lib]
pc = roots.get("K/Sub/ProductCard", {}).get("metadata", {})
if pc.get("type") != "kaya" or pc.get("variant") != "K" or pc.get("contract") != 2: errs.append(f"root metadata {pc}")
if "ikas-lib" in json.dumps(t): errs.append("library tag left in theme")
if t.get("themes", {}).get("mode") != ["light", "dark"] or t["variables"]["color-bg"]["value"][0]["value"] != "#E9E7E2": errs.append("plandata tokens not written")
if "#F4F4F4" in json.dumps(t["variables"]): errs.append("library placeholder value survived")
print("\n".join(errs)); sys.exit(1 if errs else 0)
PY
python3 -I "$S/copy_library.py" "$FX/mini-plandata" -o "$CL/kaya.pen" > "$CL/again.log" 2>&1; [ $? = 1 ] && grep -q 'copy runs once per theme' "$CL/again.log" && ok "copy_library refuses a second copy into the same theme" || bad "copy_library refuses a second copy into the same theme" "$(cat "$CL/again.log")"
python3 -I - "$FX/mini-plandata" "$CL/pd" <<'PY'
import json, shutil, sys
shutil.copytree(sys.argv[1], sys.argv[2]); p = sys.argv[2] + "/theme.json"
t = json.load(open(p)); del t["variables"]["numbers"]["space-xs"]; json.dump(t, open(p, "w"))
PY
python3 -I "$S/copy_library.py" "$CL/pd" -o "$CL/broken.pen" > "$CL/missing.log" 2>&1; [ $? = 1 ] && grep -q 'not in plandata variables: space-xs' "$CL/missing.log" && [ ! -e "$CL/broken.pen" ] && ok "copy_library stops when plandata lacks a token the library uses" || bad "copy_library stops when plandata lacks a token the library uses" "$(cat "$CL/missing.log")"
python3 -I "$S/copy_library.py" "$FX/mini-plandata" -o "$CL/x.pen" --with Nope >/dev/null 2>&1; [ $? = 2 ] && ok "copy_library rejects an unknown --with name" || bad "copy_library rejects an unknown --with name"

# 10 · structural identity and similarity gate (12-library.md §6–§7)
AX="$OUT/axes"; rm -rf "$AX"; mkdir -p "$AX"; export IKAS_PENDEV_FINGERPRINTS="$AX/store.json"
python3 -I - "$SK/library/axes.json" "$AX" <<'PY'
import json, sys
ax = json.load(open(sys.argv[1])); out = sys.argv[2]
def write(name, pick, extra=""):
    rows = [f"| {a} | {k} | `{pick(a, k, f)}` | gerekçe |" for a, s in ax["axes"].items() for k, f in s["fields"].items()]
    open(f"{out}/{name}.md", "w").write("# Globals\n\n## 0. Yapısal kimlik\n\n| Eksen | Alan | Seçim | Gerekçe |\n|---|---|---|---|\n" + "\n".join(rows) + "\n\n## 1. Renk\n" + extra)
last = lambda a, k, f: f["values"][-1]
write("a", last)
write("b", lambda a, k, f: f["values"][0] if a in ("A2", "A3") else f["values"][-1])
write("c", lambda a, k, f: f["values"][0])
write("generic", lambda a, k, f: f["median"], "font-body: Inter\n")
PY
python3 -I "$S/axes.py" check "$SK/templates/globals.md" --slug tpl > "$AX/tpl.txt" 2>&1; [ $? = 1 ] && grep -q 'A1.collection `…` not in' "$AX/tpl.txt" && ok "axes: the unfilled template fails (no defaults)" || bad "axes: the unfilled template fails (no defaults)" "$(head -3 "$AX/tpl.txt")"
python3 -I "$S/axes.py" check "$AX/a.md" --slug a > "$AX/a.txt" 2>&1 && grep -q 'AXES OK' "$AX/a.txt" && python3 -I "$S/axes.py" record "$AX/a.md" --slug a >/dev/null && ok "axes: a valid theme passes and is recorded" || bad "axes: a valid theme passes and is recorded" "$(cat "$AX/a.txt")"
python3 -I "$S/axes.py" check "$AX/b.md" --slug b > "$AX/b.txt" 2>&1; [ $? = 1 ] && grep -q "too close to 'a': 2/6 structural axes differ (need 4); 0/9 token axes differ (need 5); same B7, B12" "$AX/b.txt" && ok "axes: a theme that only changes two structural axes is too close" || bad "axes: a theme that only changes two structural axes is too close" "$(cat "$AX/b.txt")"
python3 -I "$S/axes.py" check "$AX/c.md" --slug c > "$AX/c.txt" 2>&1 && ok "axes: a theme that differs on every axis passes" || bad "axes: a theme that differs on every axis passes" "$(cat "$AX/c.txt")"
python3 -I "$S/axes.py" check "$AX/a.md" --slug a > "$AX/self.txt" 2>&1 && ok "axes: a theme is not compared with its own record" || bad "axes: a theme is not compared with its own record" "$(cat "$AX/self.txt")"
IKAS_PENDEV_FINGERPRINTS="$AX/empty.json" python3 -I "$S/axes.py" check "$AX/generic.md" --slug g > "$AX/g.txt" 2>&1 && grep -q 'WARN|§0|L23 15 axes on the generic default' "$AX/g.txt" && grep -q 'WARN|§2|L23 generic font family in globals: Inter' "$AX/g.txt" && ok "axes: generic defaults and generic fonts warn" || bad "axes: generic defaults and generic fonts warn" "$(cat "$AX/g.txt")"
unset IKAS_PENDEV_FINGERPRINTS

python3 -I - "$FX/mini-plandata" "$AX" <<'PY'
import json, shutil, sys
src, out = sys.argv[1], sys.argv[2]
for name, arch in (("pa", ["hero:split", "collection:grid"]), ("pb", ["hero:split", "collection:grid"]),
                   ("pc", ["hero:collage", "collection:lookbook"]), ("px", ["hero:nope", "collection:grid"])):
    shutil.copytree(src, f"{out}/{name}")
    for f, a in zip(("01-HeroBanner", "02-ProductGrid"), arch):
        p = f"{out}/{name}/sections/{f}.json"; d = json.load(open(p)); d["archetype"] = a; json.dump(d, open(p, "w"))
PY
export IKAS_PENDEV_FINGERPRINTS="$AX/layout-store.json"
python3 -I "$S/axes.py" record "$AX/a.md" --slug la --plandata "$AX/pa" >/dev/null && python3 -I "$S/axes.py" check "$AX/c.md" --slug lb --plandata "$AX/pb" > "$AX/lb.txt" 2>&1; [ $? = 1 ] && grep -q "too close to 'la': home page composition distance 0.00 (need 0.5)" "$AX/lb.txt" && ok "axes: same home-page composition fails even when every axis differs" || bad "axes: same home-page composition fails even when every axis differs" "$(cat "$AX/lb.txt")"
python3 -I "$S/axes.py" check "$AX/c.md" --slug lc --plandata "$AX/pc" > "$AX/lc.txt" 2>&1 && ok "axes: a different home-page composition passes" || bad "axes: a different home-page composition passes" "$(cat "$AX/lc.txt")"
python3 -I "$S/axes.py" check "$AX/c.md" --slug lx --plandata "$AX/px" > "$AX/lx.txt" 2>&1; [ $? = 1 ] && grep -q 'HeroBanner: archetype `hero:nope` not in the vocabulary' "$AX/lx.txt" && ok "axes: an unknown section archetype fails" || bad "axes: an unknown section archetype fails" "$(cat "$AX/lx.txt")"
python3 -I "$S/copy_library.py" "$AX/pa" -o "$AX/arch.pen" > "$AX/arch.log" 2>&1 && python3 -I - "$AX/arch.pen" > "$AX/arch.txt" 2>&1 <<'PY' && ok "copy_library: content sections matched by archetype, copied under the theme's key" || bad "copy_library: content sections matched by archetype, copied under the theme's key" "$(cat "$AX/arch.log" "$AX/arch.txt")"
import json, sys
t = json.load(open(sys.argv[1])); errs = []
roots = {n["name"]: n for n in t["children"] if n["type"] == "frame"}
for name, lib, part in (("K/Section/HeroBanner@desktop", "Hero", "hero-media-mobile"), ("K/Section/ProductGrid@mobile", "ProductShelf", "shelf-products")):
    r = roots.get(name)
    if not r: errs.append("missing " + name); continue
    if r["metadata"].get("libComponent") != lib or r["metadata"].get("ikas") != name.split("/")[2].split("@")[0]: errs.append(f"{name} metadata {r['metadata']}")
    if part not in {c["name"] for c in r["children"]}: errs.append(f"{name} lacks {part}")
if roots["K/Section/HeroBanner@mobile"]["width"] != 390: errs.append("mobile width")
print("\n".join(errs)); sys.exit(1 if errs else 0)
PY
unset IKAS_PENDEV_FINGERPRINTS

SH="$OUT/shots"; rm -rf "$SH"; mkdir -p "$SH"; export IKAS_PENDEV_FINGERPRINTS="$SH/store.json"
python3 -I "$FX/mkshots.py" "$SH"
python3 -I "$S/axes.py" shot "$SH/a.png" --slug sa --record > "$SH/a.txt" 2>&1 && python3 -I "$S/axes.py" shot "$SH/a-dark.png" --slug sd > "$SH/d.txt" 2>&1 && grep -q "WARN|shot|L23 first viewport looks like 'sa' 0.00" "$SH/d.txt" && ok "axes shot: the same layout in dark colours is flagged" || bad "axes shot: the same layout in dark colours is flagged" "$(cat "$SH/a.txt" "$SH/d.txt")"
python3 -I "$S/axes.py" shot "$SH/b.png" --slug sb > "$SH/b.txt" 2>&1 && grep -q 'SHOT OK' "$SH/b.txt" && ok "axes shot: a different layout passes" || bad "axes shot: a different layout passes" "$(cat "$SH/b.txt")"
python3 -I "$S/axes.py" record "$AX/a.md" --slug sa >/dev/null && python3 -c "import json,sys; sys.exit(0 if json.load(open('$SH/store.json'))['sa'].get('shot') else 1)" && ok "axes record keeps the stored screenshot fingerprint" || bad "axes record keeps the stored screenshot fingerprint"
python3 -I "$S/axes.py" shot "$AX/a.md" --slug sx >/dev/null 2>&1; [ $? = 1 ] && ok "axes shot rejects a file that is not a PNG" || bad "axes shot rejects a file that is not a PNG"
unset IKAS_PENDEV_FINGERPRINTS

echo "----"; echo "passed=$pass failed=$fail"
[ "$fail" = "0" ]
