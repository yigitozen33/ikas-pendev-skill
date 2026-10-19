// mock_pen.js — runs a pendev_checks.js snippet against a JSON canvas without pen.dev.
// Usage: node tests/tools/mock_pen.js <checks.js> <canvas.json>
// canvas.json: {"children": [root nodes]}; a node is {id, name, type, x, y, width, height, children?, ...}.
// Implements the subset of the execute API the checks use: Get (visitor / depth forms), GetVariables, Print.
// Instances are not resolved (fixtures use plain frames), so resolveInstances is ignored.
const fs = require("fs");
const [, , jsPath, canvasPath] = process.argv;
const doc = JSON.parse(fs.readFileSync(canvasPath, "utf8"));
const byId = {};
const index = n => { byId[n.id] = n; (n.children || []).forEach(index); };
doc.children.forEach(index);
const strip = n => { const o = Object.assign({}, n); delete o.children; return o; };
function visit(node, fn, parentCtx, depth, i, out) {
  let skip = false;
  const ctx = { node: strip(node), parentCtx, depth, index: i, bounds: { x: node.x || 0, y: node.y || 0, width: node.width || 0, height: node.height || 0 }, skipChildren() { skip = true; } };
  const r = fn(ctx.node, ctx);
  if (r !== undefined) out.push(r);
  if (!skip) (node.children || []).forEach((c, k) => visit(c, fn, ctx, depth + 1, k, out));
}
function Get(a, b) {
  const out = [];
  if (typeof a === "function") { doc.children.forEach((n, k) => visit(n, a, undefined, 0, k, out)); return out; }
  if (a === "document") return { id: "document", children: doc.children.map(strip) };
  const node = byId[a];
  if (!node) throw new Error("no node " + a);
  if (typeof b === "function") { visit(node, b, undefined, 0, 0, out); return out; }
  return Object.assign(strip(node), { children: (node.children || []).map(strip) });
}
const GetVariables = () => ({ variables: doc.variables || {} });
const Print = (...v) => console.log(v.map(x => (typeof x === "string" ? x : JSON.stringify(x))).join(" "));
new Function("Get", "GetVariables", "Print", "document", fs.readFileSync(jsPath, "utf8"))(Get, GetVariables, Print, "document");
