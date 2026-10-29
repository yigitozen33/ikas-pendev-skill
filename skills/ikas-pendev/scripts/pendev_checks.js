// pendev_checks.js — read-only verification snippet for the pen.dev `execute` tool.
// Template: extract_targets.py --js <mode> fills the five placeholders and strips these
// whole-line comments (the official execute.md asks for comment-free snippets).
// Uses only Get / GetVariables / Print. Never mutates the document.
//
// Modes (__MODE__):
//   all              every CHK over every root frame whose name starts with "<P>/"
//   section:<Key>    one build unit: a Section/Overlay key, or DS | Sub | Page | Overlays | Motion
//   manifest         one ROOT line per root frame (port dump, docs/port/canvas-dump.txt)
//
// Output: CHK|<id>|PASS|FAIL|WARN|<n>|<detail<=200>  ...  SUMMARY|pass=..|fail=..|warn=..|mode=..
// CHK ids: vars ds sections overlays pages spacing seed temp subfit anim hardcoded textclass clip rootmeta
//          bgprop parity props data placeholder refassets storefront dividers radius
// seed (plan §6.6): a node whose context has "seed <key>" shows that catalogue product; inside it (instances
// resolved, disabled layers skipped) data texts for the name, brand, prices, option names and line quantity, any
// "N / M" or "En fazla N" limit, and image-fill urls must match the product. Cart total and subtotal texts
// anywhere must equal the computed cart; a state root named with "kupon"/"coupon" expects the total with the
// coupon. No catalogue in the plan: WARN skip (contract 1: PASS).
// temp (07 §7): every "(geçici)" top-level frame other than the one "Öneriler (geçici)" container fails; the
// container must sit below every <P>/ root (WARN). Runs in full mode only.
// subfit (02 §1): a non-text child with a fixed width of half the Sub or more (and at least 120px, so icons in a
// layout:none stack pass), directly inside a layout:none frame of a Sub root (PriceRange rail, progress bar),
// warns: the Sub must size from its instance.
// spacing (02 §3b): the theme's spacing roles come from the plan §3b block (EXP.spacing; defaults when the plan
// has none). On every Page, in order (Header skipped): the first section's top padding is headerGap (0 or another
// variable = WARN, a raw number FAIL), each next one's is a variable (sectionGap, another variable WARN, a raw
// number FAIL), every section's bottom padding is 0, the Footer's top is footerGap (instance overrides count).
// A section whose root context has "overlap $<var>" rides over the one above (02 §3c): the page ref before it
// must have clip:false and a numeric (shortened) height, else FAIL; its own top may be any variable.
// Section components: side padding pageEdge or 0 (WARN); a horizontal row of refs to one component is a grid with
// gap `grid`, a wide row with two or more wide columns is a split with gap `split` (WARN).
// storefront (06 §3d): P/Sub/ProductCard has card-media, card-fav, card-swatches, card-cart, card-customize and the
// states "renk seçili", "ayrık varyant", "kişiselleştirme"; every card-fav (Sub roots plus the unit's Section
// components and Overlay roots, instances resolved) sits in the same corner of its card-media, whatever corner;
// QuickBuy has "renk karttan", "kişiselleştirme" and "set ürün" at both devices, each "set ürün" root with qb-bundle; the controls of every qb-actions / pdp-actions
// row (QuickBuy and ProductDetail roots; a vertical one is checked per horizontal child row) share one height; a mobile MenuOverlay has menu-mega-title
// when a desktop Header/MenuOverlay/Megamenu layer is named *mega*; ProductList has "— arama" at both devices
// and a search-field (popular searches and the all-products state are optional). Each part runs only when its
// key exists. Contract 1: WARN instead of FAIL.
// radius (02 §3): every product media layer (card-media, pdp-media, pdp-thumb, qb-media, cline-media, offer-media,
// bundle-media, iprev-thumb; Sub roots, Section components, Overlay roots, instances resolved) has the same
// cornerRadius (missing = 0) -> FAIL when they differ; the control Subs (Button, FormField, VariantChip,
// QuantitySelector) whose root sets a cornerRadius share one value -> WARN when they differ. PASS with a note
// when neither group is on the canvas.
// dividers (08 §8): no divider between rows or list items. A visible line (at most 2px thick) named *divider*,
// *separator*, *hairline* or *rule in a Section component, Sub root or Overlay root fails (a wrapper that only
// keeps the name, e.g. social-divider holding "ya da", passes) (contract 1: WARN) unless it is a
// structural edge named *-edge (sticky bar top, group boundary in a small panel, article end); a thin unnamed
// rectangle/line (<= 2px, >= 24px long) that is not an underline, indicator, progress, track, rail, bar or
// strike warns. DS frames and temp frames are out of scope.
// data: every {data:<source>} / {code:<name>} of a key's §6.2 tree is found on its component roots (overlay: any
// root) as textClass data+source / code (code also by layer name), as a context mark "data <source>" /
// "code <name>", or inside a Sub the same tree line names; a context mark the plan does not know fails.
// props: every plan prop of a layer type (TEXT, RICH_TEXT, IMAGE, IMAGE_LIST, VIDEO, SVG, SVG_LIST) that the
// plan places in a Section/Overlay tree is found on that key's component roots (Overlay: every root) as
// metadata.prop or as a context mark "prop <name> <TYPE>" / "props <a>, <b> <TYPE>" (one "·" segment;
// an untyped name takes the next type). Marks on refs and descendant overrides count: instances drop metadata.
// A marked name the plan does not know for that key (props line, child components, tree) fails as not-in-plan.
// parity: every kebab-case layer name of the @desktop component also exists in @mobile, and every
// "@desktop — <state>" root has its "@mobile — <state>" twin. Exempt: wrappers named *-row,
// *-column, *-wrap, *-body, *-main; states containing "hover"; the plan's "Yalnız masaüstü" lists
// (EXP.parity[<Key>] = {layers, states}; a listed layer exempts its whole subtree).
// textclass skips text inside <P>/DS/* and <P>/Motion/* roots (legend/specimen text).
// One execute call = one scope: the whole file is a single snippet; nothing persists.
// Backdrop instances: a ref to ANOTHER key's Section component inside a Section/Overlay root (e.g. the Header
// drawn behind a megamenu) is context only; manifest, anim and props skip it and everything inside it. With
// resolveInstances the instance comes back as a plain frame with the same id, so its id is found first.
// anim: an id the plan gives to another Section/Overlay found in a root (copied layers) fails as foreign.
// anim scans Section/Sub component roots and every Overlay root (Section state frames only hold refs);
// the resolveInstances pass runs only when ids are still missing.
// Large canvases: EXP.only (list of CHK ids) runs a subset; EXP.part = [k, n] limits the node walk
// of hardcoded/textclass/clip/refassets to every n-th root starting at k (counts add up over parts);
// in manifest mode it prints ROOT lines for that slice only (concatenate the parts).
const P = "__PREFIX__", SLUG = "__SLUG__", CONTRACT = __CONTRACT__, EXP = __EXP__, MODE = "__MODE__";
let pass = 0, fail = 0, warn = 0;
const cut = s => { s = String(s).replace(/[|\n]/g, "/"); return s.length > 200 ? s.slice(0, 197) + "..." : s; };
const chk = (id, st, n, d) => { if (st === "PASS") pass++; else if (st === "FAIL") fail++; else warn++; Print("CHK|" + id + "|" + st + "|" + n + "|" + cut(d || "")); };
const esc = s => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
const idRe = new RegExp(esc(P) + "-(?:CMP|[A-Z]{2,5})-\\d\\d", "g");
const lite = n => ({ id: n.id, name: n.name || "", type: n.type, reusable: !!n.reusable, placeholder: !!n.placeholder, metadata: n.metadata || null, theme: n.theme || null, ref: n.ref || null });
let top = Get((n, c) => { c.skipChildren(); return lite(n); });
if (top.length <= 1 && !top.some(r => r.name.indexOf(P + "/") === 0)) {
  const d = Get(document, { depth: 1 });
  top = (d && Array.isArray(d.children) ? d.children : []).filter(x => x && typeof x === "object").map(lite);
}
const roots = top.filter(r => r.name.indexOf(P + "/") === 0);
const byId = {}; top.forEach(r => { byId[r.id] = r; });
const rest = r => r.name.slice(P.length + 1);
const band = r => rest(r).split("/")[0];
const devOf = s => { const m = /@(desktop|mobile)\b/.exec(s); return m ? m[1] : "-"; };
const keyOf = r => { const m = /^[A-Za-z]+\/([A-Za-z0-9]+)/.exec(rest(r)); return m ? m[1] : ""; };
const ROLE = { DS: "ds", Sub: "sub", Section: "section", Overlay: "overlay", Page: "page", Motion: "motion" };
const ALIAS = { ds: "DS", subs: "Sub", sub: "Sub", pages: "Page", page: "Page", overlays: "Overlays", motion: "Motion" };
const anims = (m, ctx) => { const s = new Set(); if (m && typeof m.anim === "string") m.anim.split(",").forEach(x => { x = x.trim(); if (x) s.add(x); }); if (typeof ctx === "string") (ctx.match(idRe) || []).forEach(x => s.add(x)); return s; };
const propMarks = s => { const out = []; if (typeof s !== "string") return out; s.split("\u00b7").forEach(seg => { const m = /^\s*props?\s+(.+)$/.exec(seg.trim()); if (!m) return; let pend = []; m[1].split(",").forEach(it => { const w = it.trim().split(/\s+/), nm = w[0], ty = w[1] && /^[A-Z_]+$/.test(w[1]) ? w[1] : null; if (!/^[a-z][A-Za-z0-9]*$/.test(nm || "")) return; pend.push(nm); if (ty) { pend.forEach(p => out.push([p, ty])); pend = []; } }); pend.forEach(p => out.push([p, "?"])); }); return out; };
const nodeProps = n => { const out = []; const m = n.metadata || {}; if (m.prop) out.push([m.prop, m.propType || "?"]); propMarks(n.context).forEach(x => out.push(x)); const d = n.descendants; if (d && typeof d === "object") Object.keys(d).forEach(k => { const o = d[k] || {}; if (o.metadata && o.metadata.prop) out.push([o.metadata.prop, o.metadata.propType || "?"]); propMarks(o.context).forEach(x => out.push(x)); }); return out; };
const dataMarks = s => { const out = []; if (typeof s !== "string") return out; s.split("\u00b7").forEach(seg => { const m = /^\s*(data|code)\s+(.+)$/.exec(seg.trim()); if (!m) return; m[2].split(",").forEach(v => { v = v.trim().split(/\s+/)[0]; if (/^[A-Za-z][\w.-]*$/.test(v || "")) out.push([m[1], v]); }); }); return out; };
const nodeData = n => { const out = []; const m = n.metadata || {}; if (m.textClass === "data" && m.source) out.push(["data", m.source, 0]); if (m.textClass === "code") { out.push(["code", n.name || "?", 0]); if (m.code) out.push(["code", m.code, 0]); } dataMarks(n.context).forEach(x => out.push([x[0], x[1], 1])); const d = n.descendants; if (d && typeof d === "object") Object.keys(d).forEach(k => { dataMarks((d[k] || {}).context).forEach(x => out.push([x[0], x[1], 1])); }); return out; };
const scanNode = (n, into) => { anims(n.metadata, n.context).forEach(x => into.add(x)); const d = n.descendants; if (d && typeof d === "object") Object.keys(d).forEach(k => { const o = d[k] || {}; anims(o.metadata, o.context).forEach(x => into.add(x)); }); };

const backdrop = (r, n) => { if (n.type !== "ref" || band(r) === "Page") return false; const t = byId[n.ref]; return !!t && band(t) === "Section" && keyOf(t) !== keyOf(r); };
const bdCache = {};
const bdIds = r => { if (!bdCache[r.id]) { const s = new Set(); Get(r.id, (n, c) => { if (backdrop(r, n)) { s.add(n.id); c.skipChildren(); } return undefined; }); bdCache[r.id] = s; } return bdCache[r.id]; };
const walk = (r, fn, opt) => { const bd = bdIds(r); return Get(r.id, (n, c) => { if (bd.has(n.id) || backdrop(r, n)) { c.skipChildren(); return undefined; } fn(n, c); return undefined; }, opt); };
if (MODE === "manifest") {
  roots.filter((r, i) => !EXP.part || i % EXP.part[1] === EXP.part[0] - 1).forEach(r => {
    const props = [], data = [], code = [], ids = new Set();
    const add = (a, v) => { if (a.indexOf(v) < 0) a.push(v); };
    walk(r, n => {
      const m = n.metadata || {};
      nodeProps(n).forEach(x => add(props, x[0] + ":" + x[1]));
      if (m.textClass === "data") add(data, (n.name || "?") + "=" + (m.source || "?"));
      nodeData(n).forEach(x => { if (x[0] === "data" && x[2]) add(data, (n.name || "?") + "=" + x[1]); if (x[0] === "code") add(code, x[1]); });
      scanNode(n, ids);
    });
    if (band(r) !== "Page") walk(r, n => { scanNode(n, ids); }, { resolveInstances: true });
    const dev = devOf(r.name) !== "-" ? devOf(r.name) : ((r.metadata && r.metadata.device) || "-");
    Print(["ROOT", r.name.replace(/\|/g, "/"), r.id, "device=" + dev, "props=" + props.join(";"), "data=" + data.join(";"), "code=" + code.join(";"), "anims=" + Array.from(ids).sort().join(";")].join("|"));
  });
  Print("SUMMARY|roots=" + roots.length + "|mode=manifest" + (EXP.part ? "|part=" + EXP.part.join("/") : ""));
} else {
  let unit = MODE.indexOf("section:") === 0 ? MODE.slice(8) : null;
  if (unit && ALIAS[unit]) unit = ALIAS[unit];
  const isBand = unit === "DS" || unit === "Sub" || unit === "Page" || unit === "Motion" || unit === "Overlays";
  const inUnit = r => {
    if (!unit) return true;
    const b = band(r);
    if (unit === "Overlays") return b === "Overlay";
    if (isBand) return b === unit;
    return (b === "Section" || b === "Overlay") && keyOf(r) === unit;
  };
  const U = roots.filter(inUnit);
  if (unit && !isBand && (EXP.sections || []).indexOf(unit) < 0 && (EXP.overlays || []).indexOf(unit) < 0) chk("sections", "FAIL", 0, "unknown unit key " + unit + " (not a plan Section/Overlay)");
  const run = id => { if (EXP.only && EXP.only.indexOf(id) < 0) return false; if (!unit) return true; if (unit === "DS") return ["vars", "ds", "hardcoded", "textclass", "clip", "rootmeta", "placeholder", "refassets"].indexOf(id) >= 0; if (unit === "Page") return ["pages", "spacing", "rootmeta", "placeholder"].indexOf(id) >= 0; if (unit === "Motion") return ["hardcoded", "clip", "rootmeta", "placeholder", "refassets"].indexOf(id) >= 0; if (unit === "Sub") return ["subfit", "anim", "hardcoded", "textclass", "clip", "rootmeta", "placeholder", "refassets", "storefront", "radius"].indexOf(id) >= 0; if (unit === "Overlays") return ["overlays", "seed", "anim", "hardcoded", "textclass", "clip", "rootmeta", "parity", "props", "data", "placeholder", "refassets", "storefront", "radius"].indexOf(id) >= 0; return ["sections", "overlays", "spacing", "subfit", "temp", "seed", "anim", "hardcoded", "textclass", "clip", "rootmeta", "bgprop", "parity", "props", "data", "placeholder", "refassets", "storefront", "dividers", "radius"].indexOf(id) >= 0; };
  const find = nm => roots.find(r => r.name === nm);
  const findPre = pre => roots.filter(r => r.name === pre || r.name.indexOf(pre + " ") === 0);

  if (run("vars")) {
    const gv = GetVariables(), have = Object.keys((gv && gv.variables) || {});
    const miss = (EXP.vars || []).filter(v => have.indexOf(v) < 0), extra = have.filter(v => (EXP.vars || []).indexOf(v) < 0);
    chk("vars", miss.length ? "FAIL" : "PASS", (EXP.vars || []).length - miss.length, (EXP.vars || []).length - miss.length + "/" + (EXP.vars || []).length + (miss.length ? " missing:" + miss.join(",") : "") + (extra.length ? " extra:" + extra.join(",") : ""));
  }
  if (run("ds")) {
    const want = EXP.ds || [], got = want.filter(d => roots.some(r => rest(r) === "DS/" + d));
    const miss = want.filter(d => got.indexOf(d) < 0);
    chk("ds", miss.length ? "FAIL" : "PASS", got.length, got.length + "/" + want.length + (miss.length ? " missing:" + miss.join(",") : ""));
  }
  if (run("sections")) {
    const keys = unit && !isBand ? (EXP.sections || []).filter(k => k === unit) : (EXP.sections || []);
    if (keys.length || !unit) {
      const bad = [];
      keys.forEach(k => ["desktop", "mobile"].forEach(d => { const r = find(P + "/Section/" + k + "@" + d); if (!r) bad.push(k + "@" + d + ":missing"); else if (!r.reusable) bad.push(k + "@" + d + ":not-reusable"); }));
      const ok = keys.filter(k => !bad.some(b => b.indexOf(k + "@") === 0)).length;
      chk("sections", bad.length ? "FAIL" : "PASS", ok, ok + "/" + keys.length + (bad.length ? " " + bad.join(",") : ""));
    }
  }
  if (run("overlays")) {
    const keys = unit && !isBand ? (EXP.overlays || []).filter(k => k === unit) : (EXP.overlays || []);
    if (keys.length || !unit || unit === "Overlays") {
      const bad = [];
      keys.forEach(k => ((EXP.overlayDevices || {})[k] || ["desktop", "mobile"]).forEach(d => { if (!findPre(P + "/Overlay/" + k + "@" + d).length) bad.push(k + "@" + d); }));
      const ok = keys.filter(k => !bad.some(b => b.indexOf(k + "@") === 0)).length;
      chk("overlays", bad.length ? "FAIL" : "PASS", ok, ok + "/" + keys.length + (bad.length ? " missing:" + bad.join(",") : ""));
    }
  }
  if (run("pages")) {
    const pages = EXP.pages || {}, names = Object.keys(pages), bad = [], diff = [];
    const expand = EXP.pageExpand || {};
    names.forEach(pg => ["desktop", "mobile"].forEach(d => {
      const cands = U.filter(r => rest(r) === "Page/" + pg + "@" + d || (rest(r).indexOf("Page/" + pg + " \u2014 ") === 0 && rest(r).slice(-("@" + d).length) === "@" + d));
      if (!cands.length) { bad.push(pg + "@" + d + ":missing"); return; }
      if (cands.length < (expand[pg] || 1)) diff.push(pg + "@" + d + ":variants " + cands.length + "/" + expand[pg]);
      cands.forEach(r => {
      const node = Get(r.id, { depth: 1 }), kids = (node && Array.isArray(node.children)) ? node.children : [];
      const seq = [];
      kids.forEach(k => {
        const t = k && k.ref ? byId[k.ref] : null;
        if (!k || k.type !== "ref" || !t || rest(t).indexOf("Section/") !== 0) bad.push(pg + "@" + d + ":non-section:" + ((k && k.name) || "?"));
        else { if (devOf(t.name) !== d) bad.push(pg + "@" + d + ":device:" + keyOf(t)); seq.push(keyOf(t)); }
      });
      if (seq.join(",") !== (pages[pg] || []).join(",")) diff.push(pg + "@" + d);
      });
    }));
    const ok = names.filter(pg => !bad.some(b => b.indexOf(pg + "@") === 0)).length;
    chk("pages", bad.length ? "FAIL" : (diff.length ? "WARN" : "PASS"), ok, ok + "/" + names.length + (bad.length ? " " + bad.join(",") : "") + (diff.length ? " order/composition differs:" + diff.join(",") : ""));
  }
  if (run("spacing")) {
    const pad4 = p => { if (p === undefined || p === null) return [0, 0, 0, 0]; if (!Array.isArray(p)) return [p, p, p, p]; if (p.length === 2) return [p[0], p[1], p[0], p[1]]; if (p.length === 4) return p; return [0, 0, 0, 0]; };
    const zero = v => v === 0 || v === "0" || v === undefined;
    const tok = v => typeof v === "string" && /^\$[a-z]/.test(v);
    const SP = EXP.spacing || {}, EDG = SP.edges || {}, SEM = SP.seams || {};
    const pick = (m, k, d) => (k + "@" + d) in m ? m[k + "@" + d] : (k in m ? m[k] : undefined);
    const same = (a, b) => (zero(a) && zero(b)) || a === b;
    const master = {}, info = id => { if (!(id in master)) { const n = Get(id, { depth: 0 }) || {}; master[id] = { padding: n.padding, overlap: /(^|·)\s*overlap\s+\$[a-z-]+/.test(n.context || "") }; } return master[id]; };
    const padOf = id => info(id).padding;
    // The theme's own system is read from the canvas, not from declared targets (02 §3b): a token used once
    // where one token dominates is an outlier; `edges` / `seams` in the plan document intended outliers.
    const rare = (items, val, keyOf2, note) => {
      const by = {}; items.forEach(it => { const d = it.dv; (by[d] = by[d] || []).push(it); });
      Object.keys(by).forEach(d => {
        const L = by[d], cnt = {}; L.forEach(it => { cnt[val(it)] = (cnt[val(it)] || 0) + 1; });
        const top = Object.keys(cnt).sort((x, y) => cnt[y] - cnt[x])[0];
        if (L.length < 6 || cnt[top] / L.length < 0.5) return;
        L.forEach(it => { if (cnt[val(it)] === 1 && val(it) !== top && !it.doc) soft.push(keyOf2(it) + " (" + note + " " + top + ")"); });
      });
    };
    const bad = [], soft = [], mid = []; let seams = 0;
    U.filter(r => band(r) === "Page").forEach(r => {
      const kids = [];
      Get(r.id, (n, c) => { if (c.depth === 1) { kids.push(n); c.skipChildren(); } return undefined; });
      const secs = kids.map(k => ({ k, t: k && k.ref ? byId[k.ref] : null })).filter(x => x.t && rest(x.t).indexOf("Section/") === 0);
      const pg = rest(r).slice(5), dv = devOf(r.name);
      let first = true;
      secs.forEach(({ k, t }, i) => {
        const key = keyOf(t);
        if (key === "Header") return;
        const ride = info(t.id).overlap, prev = i > 0 ? secs[i - 1].k : null, prevKey = i > 0 ? keyOf(secs[i - 1].t) : "";
        if (ride && prev && !(prev.clip === false && typeof prev.height === "number")) bad.push(pg + ":" + key + "-overlap=prev ref needs clip:false + shortened height");
        const p = pad4(k.padding !== undefined ? k.padding : padOf(t.id)), top = p[0];
        let doc = pick(SEM, prevKey + ">" + key, dv);
        if (doc === undefined) doc = pick(SEM, "*>" + key, dv);
        const raw = !zero(top) && !tok(top), lab = pg + ":" + key + (first ? "-first-top=" : "-top=") + top;
        seams++;
        if (key === "Footer") { if (zero(top) || raw) bad.push(pg + ":Footer-top=" + top); return; }
        if (!zero(p[2])) bad.push(pg + ":" + key + "-bottom=" + p[2]);
        if (raw) bad.push(lab);
        else if (first) { if (zero(top) && !(doc !== undefined && same(top, doc))) soft.push(lab + " (touches the Header; fine under a transparent Header, note it in plan spacing.seams)"); }
        else if (zero(top) && !ride) bad.push(lab);
        else if (!ride) mid.push({ dv, top, lab, doc: doc !== undefined && same(top, doc) });
        first = false;
      });
    });
    rare(mid, it => it.top, it => it.lab, "rare seam; most seams use");
    const sides = [], grids = [], splits = [];
    U.filter(r => band(r) === "Section" && r.name.indexOf(" — ") < 0).forEach(r => {
      const rn = Get(r.id, { depth: 0 }) || {}, rp = pad4(rn.padding), dv = devOf(r.name), doc = pick(EDG, keyOf(r), dv);
      const rawS = [rp[1], rp[3]].filter(v => !zero(v) && !tok(v));
      if (rawS.length) bad.push(rest(r) + ":side=" + rawS[0]);
      else if (!zero(rp[1]) && !zero(rp[3]) && rp[1] !== rp[3]) soft.push(rest(r) + ":side=" + rp[3] + "/" + rp[1] + " (left and right differ)");
      else if (!zero(rp[1]) && rp[1] === rp[3]) sides.push({ dv, top: rp[1], lab: rest(r) + ":side=" + rp[1], doc: doc !== undefined && same(rp[1], doc) });
      let W = 0;
      Get(r.id, (n, c) => {
        if (n.id === r.id) { W = c.bounds.width || 0; return undefined; }
        if (n.type !== "frame" || (n.layout || "horizontal") !== "horizontal" || n.enabled === false || !W) return undefined;
        const kids = Get(n.id, { depth: 1 }).children || [], vis = kids.filter(x => x.enabled !== false && x.layoutPosition !== "absolute");
        if (vis.length < 2) return undefined;
        const refs = vis.filter(x => x.type === "ref"), same2 = refs.length === vis.length && refs.every(x => x.ref === refs[0].ref);
        const wide = vis.filter(x => typeof x.width === "number" ? x.width >= W * 0.15 : x.width === "fill_container").length;
        const lab = rest(r) + ">" + (n.name || n.id), g = n.gap;
        if (same2 && wide >= 2) { if (zero(g)) { } else if (!tok(g)) soft.push(lab + ":grid-gap=" + g); else grids.push({ dv, top: g, lab: lab + ":grid-gap=" + g }); }
        else if (wide >= 2 && (c.bounds.width || 0) >= W * 0.6) { if (zero(g)) { } else if (!tok(g)) soft.push(lab + ":split-gap=" + g); else splits.push({ dv, top: g, lab: lab + ":split-gap=" + g }); }
        return undefined;
      });
    });
    rare(sides, it => it.top, it => it.lab, "rare side inset; most sections use");
    rare(grids, it => it.top, it => it.lab, "rare grid gap; most grids use");
    rare(splits, it => it.top, it => it.lab, "rare column split; most splits use");
    const warnL = soft;
    const badSeams = new Set(bad.filter(b => b.indexOf("Section/") !== 0).map(b => b.replace(/-[a-z-]+=.*$/, ""))).size;
    chk("spacing", bad.length ? (CONTRACT < 2 ? "WARN" : "FAIL") : (warnL.length ? "WARN" : "PASS"), seams - badSeams,
      (seams - badSeams) + "/" + seams + " page seams" + (bad.length ? " bad:" + bad.join(",") : "") + (warnL.length ? " check:" + warnL.join(",") : ""));
  }
  if (run("seed")) {
    const SD = EXP.seed;
    if (!SD) chk("seed", CONTRACT < 2 ? "PASS" : "WARN", 0, "skip: the plan has no sample catalogue (plandata sampleCatalog, plan \u00a76.6)");
    else {
      const PR = SD.products || {}, C = SD.cart || null, bad = [], unknown = new Set(); let marked = 0, cmp = 0;
      const seedRe = /(?:^|\u00b7)\s*seed\s+([A-Za-z0-9-]+)/, NAME = /^(product\.name|product\.title|cart\.line\.title|order\.line\.title)$/;
      const PRICE = /^(product|variant|cart\.line|order\.line)\.(finalPrice|sellPrice|price|discountPrice|buyPrice|unitPrice|total|finalPriceWithQuantity)$/;
      const TOTAL = /^(cart|order)\.(totalFinalPrice|totalPrice|total)$/, SUB = /^(cart|order)\.(subtotal|totalPrice\.sub|itemsPrice)$/;
      const urls = f => { const a = Array.isArray(f) ? f : (f ? [f] : []); return a.filter(x => x && typeof x === "object" && typeof x.url === "string").map(x => x.url); };
      const scope = U.filter(r => ["Section", "Overlay", "Sub"].indexOf(band(r)) >= 0);
      scope.forEach(r => {
        const st = (r.name.split(" \u2014 ")[1] || "").toLowerCase(), withCoupon = /kupon|coupon/.test(st), lab = keyOf(r);
        const keyAt = {};
        walk(r, (n, c) => {
          if (n.enabled === false) { c.skipChildren(); return; }
          const par = c.parentCtx && c.parentCtx.node, own = seedRe.exec(n.context || "");
          const k = own ? own[1] : (par ? keyAt[par.id] : undefined);
          if (k) keyAt[n.id] = k;
          if (own) { marked++; if (!PR[k]) unknown.add(k); }
          const p = k ? PR[k] : null, m = n.metadata || {}, src = m.textClass === "data" ? (m.source || "") : "", txt = typeof n.content === "string" ? n.content.trim() : "";
          const miss = (what, got) => bad.push(lab + ">" + (n.name || n.id) + ":" + what + "=" + got);
          if (p && n.type === "text" && txt) {
            if (NAME.test(src)) { cmp++; if (txt !== p.name) miss(k + ".name", txt); }
            else if (src === "product.brand.name") { cmp++; if (txt !== p.brand) miss(k + ".brand", txt); }
            else if (PRICE.test(src)) { cmp++; if (p.prices.indexOf(txt) < 0) miss(k + ".price", txt); }
            else if (/^option\.(name|label)$/.test(src) && p.options.length) { cmp++; if (p.options.indexOf(txt) < 0) miss(k + ".option", txt); }
            else if (/^(cart|order)\.line\.quantity$/.test(src) && C && C.qty && C.qty[k] !== undefined) { cmp++; if (txt.replace(/\D/g, "") !== String(C.qty[k])) miss(k + ".qty", txt); }
            if (p.limits.length) { const lm = /(\d+)\s*\/\s*(\d+)/.exec(txt) || /en fazla\s+(\d+)/i.exec(txt); const lim = lm ? +(lm[2] || lm[1]) : null; if (lim !== null) { cmp++; if (p.limits.indexOf(lim) < 0) miss(k + ".limit", lim); } }
          }
          if (p && n.type !== "text") urls(n.fill).forEach(u => { cmp++; if (!p.images.some(b => u.indexOf(b) >= 0)) miss(k + ".image", u.split("/").pop()); });
          if (C && n.type === "text" && txt && (TOTAL.test(src) || SUB.test(src))) {
            cmp++;
            const want = SUB.test(src) ? C.subtotal : (withCoupon ? C.totalWithCoupon : C.total);
            if (txt !== want) miss(SUB.test(src) ? "cart.subtotal" : (withCoupon ? "cart.totalWithCoupon" : "cart.total"), txt + "\u2260" + want);
          }
        }, { resolveInstances: true });
      });
      unknown.forEach(k => bad.unshift("unknown seed " + k));
      const list = bad.slice(0, 6).join(",") + (bad.length > 6 ? ",+" + (bad.length - 6) : "");
      chk("seed", bad.length ? (CONTRACT < 2 ? "WARN" : "FAIL") : (marked ? "PASS" : "WARN"), cmp - bad.length,
        bad.length ? "\u2260 catalogue: " + list : (marked ? cmp + " values match the sample catalogue (" + marked + " seed marks)" : "no `seed <key>` marks on the canvas (02 \u00a75c)"));
    }
  }
  if (run("temp")) {
    const BOX = "\u00d6neriler (ge\u00e7ici)", tmp = /\(ge\u00e7ici\)\s*$/;
    const tb = Get((n, c) => { c.skipChildren(); return { name: n.name || "", y: c.bounds.y || 0, h: c.bounds.height || 0 }; });
    const loose = tb.filter(r => tmp.test(r.name) && r.name !== BOX).map(r => r.name);
    const boxes = tb.filter(r => r.name === BOX), low = Math.max.apply(null, [0].concat(tb.filter(r => r.name.indexOf(P + "/") === 0).map(r => r.y + r.h)));
    const above = boxes.filter(b => b.y < low).length;
    if (boxes.length > 1) loose.push(boxes.length + "\u00d7 " + BOX);
    chk("temp", loose.length ? "FAIL" : (above ? "WARN" : "PASS"), loose.length, loose.length ? "temp frames outside the options box (07 \u00a77): " + loose.join(",") : (above ? "options box overlaps the design rows; move it below every root" : (boxes.length ? "one options box below the design" : "no temp frames")));
  }
  if (run("subfit")) {
    const hits = [];
    U.filter(r => band(r) === "Sub" && r.name.indexOf(" \u2014 ") < 0).forEach(r => {
      let W = 0; const stage = new Set();
      Get(r.id, (n, c) => {
        if (n.id === r.id) { W = c.bounds.width || 0; }
        if (n.layout === "none" && n.id !== r.id) stage.add(n.id);
        const par = c.parentCtx && c.parentCtx.node;
        if (par && stage.has(par.id) && n.type !== "text" && typeof n.width === "number" && W && n.width >= Math.max(120, W * 0.5)) hits.push(rest(r) + ">" + (n.name || n.id) + "=" + n.width);
        return undefined;
      });
    });
    chk("subfit", hits.length ? "WARN" : "PASS", hits.length, hits.length ? "fixed inner width in a layout:none frame of a Sub, size it from the instance (02 §1): " + hits.join(",") : "no fixed rails in Subs");
  }
  if (run("anim")) {
    const want = unit ? ((EXP.unit && EXP.unit.ids) || []) : (EXP.ids || []);
    const found = new Set(), owner = EXP.idOwner || {}, foreign = [];
    const scope = U.filter(r => ["Section", "Overlay", "Sub"].indexOf(band(r)) >= 0 && !(band(r) === "Section" && r.name.indexOf(" \u2014 ") >= 0));
    const scanRoot = (r, opt) => { const ids = new Set(); walk(r, n => { scanNode(n, ids); }, opt); ids.forEach(x => { found.add(x); if (owner[x] && owner[x] !== keyOf(r) && foreign.indexOf(keyOf(r) + ">" + x) < 0) foreign.push(keyOf(r) + ">" + x); }); };
    scope.forEach(r => scanRoot(r));
    if (want.some(x => !found.has(x))) scope.filter(r => r.name.indexOf(" \u2014 ") < 0).forEach(r => scanRoot(r, { resolveInstances: true }));
    const miss = want.filter(x => !found.has(x)), extra = Array.from(found).filter(x => want.indexOf(x) < 0);
    const ok = want.length - miss.length;
    chk("anim", miss.length || foreign.length ? "FAIL" : (extra.length && !unit ? "WARN" : "PASS"), ok, ok + "/" + want.length + (miss.length ? " missing:" + miss.join(",") : "") + (foreign.length ? " foreign:" + foreign.join(",") : "") + (extra.length ? " extra:" + extra.join(",") : ""));
  }
  const W = { hc: { fill: 0, stroke: 0, fontSize: 0, fontFamily: 0, cornerRadius: 0 }, hcx: [], texts: 0, tcMiss: 0, tcBad: 0, tcx: [], noProp: 0, clip: 0, clipx: [], ref: 0, refx: [] };
  const lit = f => { if (typeof f === "string") return f[0] === "#"; if (Array.isArray(f)) return f.some(lit); if (f && typeof f === "object") { if (f.type === "color") return typeof f.color === "string" && f.color[0] === "#"; if (f.type === "gradient") return (f.colors || []).some(x => x && typeof x.color === "string" && x.color[0] === "#"); if (f.type === "mesh_gradient") return (f.colors || []).some(x => typeof x === "string" && x[0] === "#"); } return false; };
  const imgs = f => Array.isArray(f) ? f.reduce((a, x) => a.concat(imgs(x)), []) : (f && typeof f === "object" && f.type === "image" && typeof f.url === "string" ? [f.url] : []);
  const host = EXP.referenceHost || "";
  const excl = /mask|track|marquee|ticker|pin|stage|curtain|hover|scroll|(^|-)(top|bottom|next|prev)$/i;
  if (["hardcoded", "textclass", "clip", "refassets"].some(run)) {
    U.filter((r, i) => !EXP.part || i % EXP.part[1] === EXP.part[0] - 1).forEach(r => Get(r.id, (n, c) => {
      const k = [];
      if (lit(n.fill)) k.push("fill");
      if (lit(n.stroke)) k.push("stroke");
      if ([].concat(n.cornerRadius === undefined ? [] : n.cornerRadius).some(v => typeof v === "number" && v !== 0)) k.push("cornerRadius");
      if (n.type === "text") {
        if (typeof n.fontSize === "number") k.push("fontSize");
        if (typeof n.fontFamily === "string" && n.fontFamily[0] !== "$") k.push("fontFamily");
        const m = n.metadata || {};
        if (band(r) !== "DS" && band(r) !== "Motion") {
          W.texts++;
          if (!m.prop) W.noProp++;
          if (!m.textClass) { W.tcMiss++; if (W.tcx.length < 6) W.tcx.push(n.name); }
          else if ((m.textClass === "prop" && !(m.prop && m.propType)) || (m.textClass === "data" && !m.source) || ["prop", "data", "code"].indexOf(m.textClass) < 0) { W.tcBad++; if (W.tcx.length < 6) W.tcx.push(n.name + ":" + m.textClass); }
        }
      }
      k.forEach(x => { W.hc[x]++; });
      if (k.length && W.hcx.length < 6) W.hcx.push((n.name || n.id) + ":" + k.join("+"));
      if (c.problems) {
        let e = false, p = c;
        while (p && !e) { if (excl.test((p.node && p.node.name) || "")) e = true; p = p.parentCtx; }
        if (!e) { W.clip++; if (W.clipx.length < 6) W.clipx.push(keyOf(r) + ">" + (n.name || n.id)); }
      }
      imgs(n.fill).forEach(u => { if ((host && u.indexOf(host) >= 0) || /framerusercontent\.com/.test(u)) { W.ref++; if (W.refx.length < 4) W.refx.push(n.name || n.id); } });
      return undefined;
    }));
  }
  if (run("hardcoded")) {
    const t = W.hc.fill + W.hc.stroke + W.hc.fontSize + W.hc.fontFamily + W.hc.cornerRadius;
    chk("hardcoded", t ? (CONTRACT < 2 ? "WARN" : "FAIL") : "PASS", t, "fill=" + W.hc.fill + " stroke=" + W.hc.stroke + " fontSize=" + W.hc.fontSize + " fontFamily=" + W.hc.fontFamily + " cornerRadius=" + W.hc.cornerRadius + (W.hcx.length ? " e.g. " + W.hcx.join(",") : ""));
  }
  if (run("textclass")) {
    if (CONTRACT >= 2) chk("textclass", W.tcMiss + W.tcBad ? "FAIL" : "PASS", W.tcMiss + W.tcBad, "texts=" + W.texts + " none=" + W.tcMiss + " invalid=" + W.tcBad + (W.tcx.length ? " e.g. " + W.tcx.join(",") : ""));
    else chk("textclass", W.noProp ? "WARN" : "PASS", W.noProp, "contract 1 baseline: texts=" + W.texts + " without metadata.prop=" + W.noProp);
  }
  if (run("clip")) chk("clip", W.clip ? "WARN" : "PASS", W.clip, W.clip ? "clipped (excl. mask/track/marquee/ticker/pin/stage/curtain): " + W.clipx.join(",") : "no clipped content");
  if (run("rootmeta")) {
    const bad = [];
    U.forEach(r => {
      const m = r.metadata || {}, b = band(r), why = [];
      const isState = r.name.indexOf(" \u2014 ") >= 0;
      if (isState && CONTRACT < 2) return;
      if (m.type !== SLUG) why.push("type");
      if (m.role !== ROLE[b]) why.push("role");
      if (isState) { if (why.length) bad.push(rest(r) + ":" + why.join("+")); return; }
      if (m.variant !== P) why.push("variant");
      const d = devOf(r.name);
      if (d !== "-" && m.device !== d) why.push("device");
      if (d !== "-" && (!r.theme || r.theme.device !== d)) why.push("theme");
      if ((b === "Section" || b === "Sub" || b === "Overlay") && !m.ikas) why.push("ikas");
      if (CONTRACT >= 2 && m.contract !== CONTRACT && String(m.contract) !== String(CONTRACT)) why.push("contract");
      if (why.length) bad.push(rest(r) + ":" + why.join("+"));
    });
    chk("rootmeta", bad.length ? "FAIL" : "PASS", U.length - bad.length, (U.length - bad.length) + "/" + U.length + (bad.length ? " " + bad.join(",") : ""));
  }
  if (run("bgprop")) {
    const secs = U.filter(r => band(r) === "Section");
    if (CONTRACT < 2) chk("bgprop", "PASS", 0, "skip: contract 1 roots carry no backgroundColor");
    else {
      const bad = secs.filter(r => !(r.metadata && r.metadata.prop === "backgroundColor" && r.metadata.propType === "COLOR")).map(rest);
      chk("bgprop", bad.length ? "FAIL" : "PASS", secs.length - bad.length, (secs.length - bad.length) + "/" + secs.length + (bad.length ? " missing:" + bad.join(",") : ""));
    }
  }
  if (run("parity")) {
    const PAR = EXP.parity || {}, kebab = /^[a-z][a-z0-9-]*$/, STRUCT = /-(row|column|wrap|body|main)$/;
    const keys = unit === "Overlays" ? (EXP.overlays || []) : (unit && !isBand ? [unit] : (EXP.sections || []).concat(EXP.overlays || []));
    const names = (id, allow) => { const s = new Set(); Get(id, (n, c) => { const nm = n.name || ""; if (n.id !== id && kebab.test(nm)) { if (allow.indexOf(nm) >= 0) { c.skipChildren(); return undefined; } if (!STRUCT.test(nm)) s.add(nm); } return undefined; }); return s; };
    const badL = [], badS = [], badK = new Set(); let checked = 0;
    keys.forEach(k => {
      const kind = (EXP.sections || []).indexOf(k) >= 0 ? "Section" : "Overlay";
      if (kind === "Overlay" && ((EXP.overlayDevices || {})[k] || ["desktop", "mobile"]).length < 2) return;
      const al = (PAR[k] && PAR[k].layers) || [], as = (PAR[k] && PAR[k].states) || [];
      const pre = P + "/" + kind + "/" + k + "@", dsk = roots.filter(r => r.name.indexOf(pre + "desktop \u2014 ") === 0);
      let d = find(pre + "desktop"), m = find(pre + "mobile");
      if (!(d && m)) { const tw = dsk.map(r => [r, find(r.name.replace("@desktop \u2014 ", "@mobile \u2014 "))]).find(x => x[1]); if (tw) { d = tw[0]; m = tw[1]; } }
      if (!(d && m)) return;
      checked++;
      const M = names(m.id, []);
      names(d.id, al).forEach(x => { if (!M.has(x)) { badK.add(k); badL.push(k + ">" + x); } });
      dsk.forEach(r => { const st = r.name.slice((pre + "desktop \u2014 ").length); if (/hover/i.test(st) || as.indexOf(st) >= 0) return; if (!find(pre + "mobile \u2014 " + st)) { badK.add(k); badS.push(k + " \u2014 " + st); } });
    });
    const okK = checked - badK.size;
    chk("parity", badK.size ? "FAIL" : "PASS", okK, okK + "/" + checked + (badS.length ? " mobile state missing:" + badS.join(",") : "") + (badL.length ? " desktop-only layers:" + badL.join(",") : ""));
  }
  if (run("props")) {
    const PE = EXP.props || {}, keys = unit === "Overlays" ? Object.keys(PE).filter(k => (EXP.overlays || []).indexOf(k) >= 0) : (unit ? (PE[unit] ? [unit] : []) : Object.keys(PE));
    const miss = [], wrong = [], stale = []; let want = 0;
    keys.forEach(k => {
      const kind = (EXP.sections || []).indexOf(k) >= 0 ? "Section" : "Overlay", pre = P + "/" + kind + "/" + k + "@";
      const rs = roots.filter(r => r.name.indexOf(pre) === 0 && (kind === "Overlay" || r.name.indexOf(" \u2014 ") < 0));
      const got = {};
      rs.forEach(r => walk(r, n => { nodeProps(n).forEach(x => { if (!got[x[0]] || got[x[0]] === "?") got[x[0]] = x[1]; }); }));
      PE[k].need.forEach(e => { want++; if (!got[e[0]]) miss.push(k + "." + e[0]); else if (got[e[0]] !== "?" && got[e[0]] !== e[1]) wrong.push(k + "." + e[0] + ":" + got[e[0]] + "\u2260" + e[1]); });
      Object.keys(got).forEach(g => { if (PE[k].known.indexOf(g) < 0) stale.push(k + "." + g); });
    });
    const bad = miss.length + wrong.length + stale.length;
    chk("props", bad ? (CONTRACT < 2 ? "WARN" : "FAIL") : "PASS", want - miss.length - wrong.length, (want - miss.length - wrong.length) + "/" + want + (miss.length ? " unmarked:" + miss.join(",") : "") + (wrong.length ? " type:" + wrong.join(",") : "") + (stale.length ? " not-in-plan:" + stale.join(",") : ""));
  }
  if (run("data")) {
    const DE = EXP.data || {}, keys = unit === "Overlays" ? Object.keys(DE).filter(k => (EXP.overlays || []).indexOf(k) >= 0) : (unit ? (DE[unit] ? [unit] : []) : Object.keys(DE));
    const subIdx = {};
    roots.filter(r => band(r) === "Sub").forEach(r => { const s = subIdx[keyOf(r)] = subIdx[keyOf(r)] || new Set(); Get(r.id, n => { nodeData(n).forEach(x => s.add(x[0] + ":" + x[1])); return undefined; }); });
    const miss = [], stale = []; let want = 0;
    keys.forEach(k => {
      const kind = (EXP.sections || []).indexOf(k) >= 0 ? "Section" : "Overlay", pre = P + "/" + kind + "/" + k + "@";
      const rs = roots.filter(r => r.name.indexOf(pre) === 0 && (kind === "Overlay" || r.name.indexOf(" \u2014 ") < 0));
      const got = new Set(), marks = new Set();
      rs.forEach(r => walk(r, n => { nodeData(n).forEach(x => { got.add(x[0] + ":" + x[1]); if (x[2]) marks.add(x[0] + ":" + x[1]); }); }));
      DE[k].need.forEach(e => { want++; const key = e[0] + ":" + e[1]; const ok = got.has(key) || (e[0] === "code" && got.has("code:" + e[2])) || e[3].some(s => subIdx[s] && (subIdx[s].has(key) || (e[0] === "code" && Array.from(subIdx[s]).some(v => v.indexOf("code:") === 0)))); if (!ok) miss.push(k + "." + e[2] + ":" + key); });
      marks.forEach(v => { if (DE[k].known.indexOf(v) < 0) stale.push(k + "." + v); });
    });
    const bad = miss.length + stale.length;
    chk("data", bad ? (CONTRACT < 2 ? "WARN" : "FAIL") : "PASS", want - miss.length, (want - miss.length) + "/" + want + (miss.length ? " unmarked:" + miss.join(",") : "") + (stale.length ? " not-in-plan:" + stale.join(",") : ""));
  }
  if (run("storefront")) {
    const ovKeys = EXP.overlays || [], allKeys = (EXP.sections || []).concat(ovKeys);
    const want = k => !unit || unit === k || (unit === "Sub" && k === "ProductCard") || (unit === "Overlays" && ovKeys.indexOf(k) >= 0);
    const keyRoots = k => roots.filter(r => (band(r) === "Section" || band(r) === "Overlay") && keyOf(r) === k);
    const named = (r, re) => Get(r.id, n => (re.test(n.name || "") ? n.name : undefined), { resolveInstances: true });
    const has = (rs, nm) => rs.some(r => named(r, new RegExp("^" + esc(nm) + "$")).length > 0);
    const stateRoot = (pre, st) => find(pre + " — " + st);
    const miss = []; let parts = 0;
    const card = find(P + "/Sub/ProductCard");
    if (card && want("ProductCard")) {
      parts++;
      ["card-media", "card-fav", "card-swatches", "card-cart", "card-customize"].forEach(nm => { if (!has([card], nm)) miss.push("ProductCard>" + nm); });
      ["renk seçili", "ayrık varyant", "kişiselleştirme"].forEach(st => { if (!stateRoot(P + "/Sub/ProductCard", st)) miss.push("ProductCard — " + st); });
    }
    if (want("ProductCard") || !unit || (EXP.sections || []).indexOf(unit) >= 0 || unit === "Overlays") {
      const abs = c => { let x = 0, y = 0, p = c; while (p) { x += p.bounds.x; y += p.bounds.y; p = p.parentCtx; } return { x: x, y: y, w: c.bounds.width, h: c.bounds.height }; };
      const scan = roots.filter(r => band(r) === "Sub").concat(U.filter(r => (band(r) === "Section" && r.name.indexOf(" — ") < 0) || band(r) === "Overlay"));
      const corners = {};
      scan.filter((r, i) => scan.indexOf(r) === i).forEach(r => walk(r, (n, c) => {
        if (n.name !== "card-fav") return;
        let p = c.parentCtx;
        while (p && p.node.name !== "card-media") p = p.parentCtx;
        const k = !p ? "outside card-media" : (() => { const m = abs(p), f = abs(c); return (f.y - m.y <= m.y + m.h - (f.y + f.h) ? "top" : "bottom") + "-" + (f.x - m.x <= m.x + m.w - (f.x + f.w) ? "left" : "right"); })();
        (corners[k] = corners[k] || []).push(rest(r));
      }, { resolveInstances: true }));
      const ks = Object.keys(corners);
      if (ks.length) parts++;
      if (ks.length > 1 || corners["outside card-media"]) miss.push("card-fav corners differ: " + ks.map(k => k + "×" + corners[k].length + " (" + corners[k].filter((v, i, a) => a.indexOf(v) === i).slice(0, 3).join(" / ") + ")").join("; "));
    }
    if (allKeys.indexOf("QuickBuy") >= 0 && want("QuickBuy")) {
      parts++;
      ["renk karttan", "kişiselleştirme", "set ürün"].forEach(st => ["desktop", "mobile"].forEach(d => {
        const sr = roots.filter(r => keyOf(r) === "QuickBuy" && r.name.indexOf("@" + d + " — " + st) > 0);
        if (!sr.length) miss.push("QuickBuy@" + d + " — " + st);
        else if (st === "set ürün" && !has(sr, "qb-bundle")) miss.push("QuickBuy@" + d + " — set ürün>qb-bundle");
      }));
    }
    if ((allKeys.indexOf("QuickBuy") >= 0 && want("QuickBuy")) || (allKeys.indexOf("ProductDetail") >= 0 && want("ProductDetail"))) {
      const nodes = {};
      keyRoots("QuickBuy").concat(keyRoots("ProductDetail")).forEach(r => walk(r, (n, c) => { nodes[n.id] = { name: n.name || "", layout: n.layout, on: n.enabled !== false, h: Math.round(c.bounds.height), up: c.parentCtx ? c.parentCtx.node.id : null, root: keyOf(r) }; }, { resolveInstances: true }));
      const kids = id => Object.keys(nodes).filter(k => nodes[k].up === id && nodes[k].on);
      Object.keys(nodes).filter(k => /^(qb|pdp)-actions$/.test(nodes[k].name)).forEach(k => {
        const rows = nodes[k].layout !== "vertical" ? [k] : kids(k).filter(x => nodes[x].layout !== "vertical" && kids(x).length > 1);
        rows.forEach(rw => { const hs = kids(rw).map(x => nodes[x].h).filter((v, i, a) => a.indexOf(v) === i); if (hs.length > 1) miss.push(nodes[k].root + ">" + nodes[k].name + " heights " + hs.join("/")); });
      });
    }
    if (allKeys.indexOf("MenuOverlay") >= 0 && want("MenuOverlay")) {
      const desk = roots.filter(r => ["Header", "MenuOverlay", "Megamenu"].indexOf(keyOf(r)) >= 0 && devOf(r.name) === "desktop");
      if (desk.some(r => named(r, /mega/i).length > 0)) {
        parts++;
        const mob = keyRoots("MenuOverlay").filter(r => devOf(r.name) === "mobile");
        if (!has(mob, "menu-mega-title")) miss.push("MenuOverlay@mobile>menu-mega-title");
      }
    }
    if (allKeys.indexOf("ProductList") >= 0 && want("ProductList")) {
      parts++;
      const pre = P + "/Section/ProductList@";
      ["desktop", "mobile"].forEach(d => { if (!stateRoot(pre + d, "arama")) miss.push("ProductList@" + d + " — arama"); });
      if (!has(keyRoots("ProductList"), "search-field")) miss.push("ProductList>search-field");
    }
    chk("storefront", miss.length ? (CONTRACT < 2 ? "WARN" : "FAIL") : "PASS", miss.length, parts ? (miss.length ? "missing:" + miss.join(",") : parts + " part(s) complete") : "no ProductCard/QuickBuy/MenuOverlay/ProductList in scope");
  }
  if (run("radius")) {
    const MEDIA = /^(card-media|pdp-media|pdp-thumb|qb-media|cline-media|offer-media|bundle-media|iprev-thumb)$/;
    const norm = v => { const a = [].concat(v === undefined ? 0 : v); return String(a.every(x => x === a[0]) ? a[0] : a.join(" ")); };
    const scan = roots.filter(r => band(r) === "Sub" || band(r) === "Overlay" || (band(r) === "Section" && r.name.indexOf(" \u2014 ") < 0));
    const media = {};
    scan.forEach(r => walk(r, n => { if (MEDIA.test(n.name || "")) (media[norm(n.cornerRadius)] = media[norm(n.cornerRadius)] || []).push(keyOf(r) + ">" + n.name); }, { resolveInstances: true }));
    const ctl = {};
    ["Button", "FormField", "VariantChip", "QuantitySelector"].forEach(nm => { const r = find(P + "/Sub/" + nm); if (r) { const n = Get(r.id, { depth: 1 }); if (n && n.cornerRadius !== undefined) (ctl[norm(n.cornerRadius)] = ctl[norm(n.cornerRadius)] || []).push(nm); } });
    const fmt = o => Object.keys(o).map(k => k + "×" + o[k].length + " (" + o[k].filter((v, i, a) => a.indexOf(v) === i).slice(0, 3).join(" / ") + ")").join("; ");
    const mk = Object.keys(media), ck = Object.keys(ctl);
    if (mk.length > 1) chk("radius", CONTRACT < 2 ? "WARN" : "FAIL", mk.length, "product media radius differs (02 \u00a73): " + fmt(media));
    else if (ck.length > 1) chk("radius", "WARN", ck.length, "control Subs radius differs (02 \u00a73): " + fmt(ctl));
    else chk("radius", "PASS", mk.length + ck.length, mk.length || ck.length ? "product media " + (mk[0] || "-") + ", controls " + (ck[0] || "-") : "no product media or control Subs on the canvas");
  }
  if (run("dividers")) {
    const NAMED = /divider|separator|hairline|(^|-)rule$/i, EDGE = /-edge$/i, KEEP = /edge|underline|indicator|progress|track|rail|bar|strike|link-line|cursor|caret|swatch|star|dot/i;
    const scope = U.filter(r => (band(r) === "Overlay") || ((band(r) === "Section" || band(r) === "Sub") && r.name.indexOf(" \u2014 ") < 0));
    const named = [], thin = [];
    scope.forEach(r => { const seen = new Set(), lab = rest(r).replace(/^(Section|Sub|Overlay)\//, ""); walk(r, (n, c) => {
      if (n.enabled === false) { c.skipChildren(); return; }
      const nm = n.name || n.type, t = Math.min(c.bounds.width, c.bounds.height), isThin = (n.type === "rectangle" || n.type === "line") && t <= 2 && Math.max(c.bounds.width, c.bounds.height) >= 24;
      if (seen.has(nm) || EDGE.test(nm)) return;
      if (NAMED.test(nm) && t <= 2) { seen.add(nm); named.push(lab + ">" + nm); }
      else if (isThin && !KEEP.test(nm)) { seen.add(nm); thin.push(lab + ">" + nm); }
    }); });
    const list = a => a.slice(0, 8).join(",") + (a.length > 8 ? ",+" + (a.length - 8) : "");
    chk("dividers", named.length ? (CONTRACT < 2 ? "WARN" : "FAIL") : (thin.length ? "WARN" : "PASS"), named.length + thin.length,
      named.length ? "row dividers (08 \u00a78; spacing, or *-edge): " + list(named) + (thin.length ? " · check:" + list(thin) : "")
        : (thin.length ? "thin lines, a row divider? (08 \u00a78): " + list(thin) : "no row or item dividers"));
  }
  if (run("placeholder")) {
    const ph = U.filter(r => r.placeholder).map(rest);
    chk("placeholder", ph.length ? "FAIL" : "PASS", ph.length, ph.length ? "still placeholder:" + ph.join(",") : "none");
  }
  if (run("refassets")) chk("refassets", W.ref ? "FAIL" : "PASS", W.ref, W.ref ? "reference-host image fills: " + W.refx.join(",") : "no reference-host image fills" + (host ? " (" + host + ")" : ""));
  Print("SUMMARY|pass=" + pass + "|fail=" + fail + "|warn=" + warn + "|mode=" + MODE + "|roots=" + U.length + (EXP.only ? "|only=" + EXP.only.join(",") : "") + (EXP.part ? "|part=" + EXP.part.join("/") : ""));
}
