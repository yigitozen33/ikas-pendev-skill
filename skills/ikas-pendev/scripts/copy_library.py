#!/usr/bin/env python3
"""copy_library.py - start a theme's canvas from the structure library (references/12-library.md).

Copies the library components a theme needs into the theme's .pen file and gives every
token the theme's own value from plandata. The library is a template, never an import:
after the copy the theme owns the nodes, and no library value survives.

What is copied:
  * every library component whose name is in plandata `components` (Subs) or is a
    plandata section / overlay `key`;
  * every block whose host section is in plandata (ProductGallery for ProductDetail …);
  * for a plandata section with `archetype: "<family>:<variant>"` and no library component of
    its own name, the content-section skeleton of that family (Hero, ProductShelf, MediaText …),
    copied under the theme's section key;
  * the optional overlays named with --with (Toast, ConfirmModal …) when plandata does not
    already list them.
What changes on the way:
  * root names take the theme prefix (P/Sub/Button → K/Sub/Button); sections and overlays
    get one root per device (@desktop / @mobile); every extra state stays a ref named
    "<root> — <state>";
  * metadata.type becomes the theme slug, and roots carry variant / contract / device
    (02-contract.md §5);
  * node ids are re-derived from the theme slug, so two themes never share an id;
  * variables are written from plandata (`colors` per mode, `type` and paired `numbers`
    per device). A token the copied nodes use but plandata lacks is an error.

Library components that plandata does not name are reported: a WARN for those the skill
already requires (02 §9, 06 §3), an INFO for those the library adds (Price, CartCount …),
which a plan may build inline instead.

Close the theme file in pen.dev before running: the app keeps its own copy in memory
and would overwrite this script's output on its next save.

Usage:
  python3 -I copy_library.py <plandata dir|file> -o docs/pendev/<theme>.pen [--with Toast,ConfirmModal]
                             [--library library/ikas-ecommerce.lib.pen] [--dry-run]

Exit: 0 copied (gaps are warnings), 1 error (missing token, unreadable input, target not empty), 2 bad arguments.
Stdlib only, Python 3.9+.
"""

import argparse
import copy
import glob
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(os.path.dirname(HERE), "library", "ikas-ecommerce.lib.pen")
INV = os.path.join(os.path.dirname(HERE), "library", "inventory.json")
TAG = "ikas-lib"
DEVICES = ("desktop", "mobile")
GAP = 120


def die(msg, code=1):
    print("ERROR " + msg, file=sys.stderr)
    sys.exit(code)


def load_plandata(src):
    if os.path.isdir(src):
        with open(os.path.join(src, "theme.json"), encoding="utf-8") as f:
            data = json.load(f)
        data["sections"] = []
        for p in sorted(glob.glob(os.path.join(src, "sections", "*.json"))):
            with open(p, encoding="utf-8") as f:
                data["sections"].append(json.load(f))
        return data
    with open(src, encoding="utf-8") as f:
        return json.load(f)


def theme_variables(pd):
    """plandata variables → .pen variables with mode / device axes."""
    modes = pd.get("modes") or None
    var, themes = {}, {}
    v = pd["variables"]
    for name, val in v.get("colors", {}).items():
        if modes and isinstance(val, list):
            var[name] = {"type": "color", "value": [{"value": c, "theme": {"mode": m}} for c, m in zip(val, modes)]}
            themes["mode"] = list(modes)
        else:
            var[name] = {"type": "color", "value": val}
    for name, val in v.get("fonts", {}).items():
        var[name] = {"type": "string", "value": val}
    for group in ("type", "numbers"):
        for name, val in v.get(group, {}).items():
            if isinstance(val, list):
                var[name] = {"type": "number", "value": [{"value": n, "theme": {"device": d}} for n, d in zip(val, DEVICES)]}
                themes["device"] = list(DEVICES)
            else:
                var[name] = {"type": "number", "value": val}
    return var, themes


def library_roots(lib):
    roots = {}

    def walk(n):
        if n.get("reusable"):
            roots[n["metadata"]["ikas"]] = n
        for ch in n.get("children", []):
            walk(ch)

    for n in lib["children"]:
        walk(n)
    return roots


def library_states(lib):
    """component name → list of state refs (from the generator's columns)."""
    out = {}

    def walk(n):
        kids = n.get("children", [])
        root = next((k for k in kids if k.get("reusable")), None)
        if root:
            out[root["metadata"]["ikas"]] = [k for k in kids if k.get("type") == "ref"]
        for ch in kids:
            walk(ch)

    for n in lib["children"]:
        walk(n)
    return out


class Copier:
    def __init__(self, slug, prefix):
        self.slug, self.prefix = slug, prefix

    def nid(self, *parts):
        return "T" + hashlib.sha1("/".join((self.slug,) + parts).encode("utf-8")).hexdigest()[:10]

    def retag(self, node, scope):
        """Deep copy with theme ids and theme metadata.type."""
        n = copy.deepcopy(node)

        def fix(x):
            x["id"] = self.nid(scope, x["id"])
            if isinstance(x.get("metadata"), dict) and x["metadata"].get("type") == TAG:
                x["metadata"]["type"] = self.slug
            for ch in x.get("children", []):
                fix(ch)

        fix(n)
        return n


def tokens_used(nodes):
    used = set()

    def walk(x):
        if isinstance(x, dict):
            for k, v in x.items():
                if k in ("context", "content", "name"):
                    continue
                if isinstance(v, str) and v.startswith("$"):
                    used.add(v[1:])
                else:
                    walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)

    walk(nodes)
    return used


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("plandata")
    ap.add_argument("-o", "--out", required=True, help="theme .pen file (new, or one without library roots)")
    ap.add_argument("--with", dest="extra", default="", help="comma list of optional components to add")
    ap.add_argument("--library", default=LIB)
    ap.add_argument("--inventory", default=INV)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    try:
        pd = load_plandata(a.plandata)
        with open(a.library, encoding="utf-8") as f:
            lib = json.load(f)
        with open(a.inventory, encoding="utf-8") as f:
            inv = json.load(f)
    except (OSError, ValueError) as e:
        die(str(e))

    slug, prefix = pd["theme"]["slug"], pd["theme"]["prefix"]
    sizes = pd.get("devices", {"desktop": {"width": 1440}, "mobile": {"width": 390}})
    by_name = {c["name"]: c for c in inv["components"]}
    roots, states = library_roots(lib), library_states(lib)

    planned = {c["name"] for c in pd.get("components", [])}
    planned |= {s["key"] for s in pd.get("sections", [])}
    extra = {x.strip() for x in a.extra.split(",") if x.strip()}
    unknown = sorted(extra - set(by_name))
    if unknown:
        die("--with names not in the library: " + ", ".join(unknown), 2)

    pick = []  # (library component, target name)
    for c in inv["components"]:
        name = c["name"]
        if name in planned or name in extra or (c["kind"] == "block" and c.get("host") in planned):
            pick.append((c, name))
    content = [c for c in inv["components"] if c.get("families")]
    unmatched = []
    for sec in pd.get("sections", []):
        if sec.get("kind") != "section" or sec["key"] in by_name or not sec.get("archetype"):
            continue
        arch = sec["archetype"]
        fam = arch.split(":", 1)[0]
        hit = next((c for c in content if arch in c["families"]), None) or \
            next((c for c in content if fam in c["families"]), None)
        if hit:
            pick.append((hit, sec["key"]))
        else:
            unmatched.append(f"{sec['key']} ({arch})")
    picked = {c["name"] for c, _ in pick}
    unplanned = [c for c in inv["components"]
                 if c["name"] not in picked and not c.get("optional") and c["kind"] != "block"]
    gaps = [c["name"] for c in unplanned if "contract" in c["basis"]]
    hints = [c["name"] for c in unplanned if "contract" not in c["basis"]]

    cp = Copier(slug, prefix)
    out_nodes, x, y_band, band_h = [], 0, 0, 0
    last_layer = None
    for c, target in pick:
        if c["layer"] != last_layer and last_layer is not None:
            x, y_band, band_h = 0, y_band + band_h + GAP * 2, 0
        last_layer = c["layer"]
        lib_root = roots[c["name"]]
        devs = DEVICES if c["kind"] in ("section", "overlay") else (None,)
        for dev in devs:
            suffix = "@" + dev if dev else ""
            root = cp.retag(lib_root, target + suffix)
            root["name"] = lib_root["name"].replace("P/", prefix + "/", 1).rsplit("/", 1)[0] + "/" + target + suffix
            if c["kind"] == "block":
                root.pop("reusable", None)
            meta = root["metadata"]
            meta.update({"variant": prefix, "contract": 2, "ikas": target})
            if target != c["name"]:
                meta["libComponent"] = c["name"]
            if dev:
                meta["device"] = dev
                if c["kind"] == "section":
                    root["width"] = sizes[dev]["width"]
            est_h = 48 + 44 * sum(1 for p in root["children"] if p.get("enabled", True))
            y = y_band
            root.update({"x": x, "y": y})
            out_nodes.append(root)
            y += est_h + GAP // 2
            if c["kind"] != "block":
                for ref in states.get(c["name"], []):
                    st = ref["name"].split(" — ", 1)[1]
                    out_nodes.append({"type": "ref", "id": cp.nid(target + suffix, "state", st), "ref": root["id"],
                                      "name": f"{root['name']} — {st}", "context": "state " + st, "x": x, "y": y})
                    y += est_h + GAP // 2
            band_h = max(band_h, y - y_band)
            w = root["width"] if isinstance(root.get("width"), (int, float)) else 360
            x += w + GAP

    var, themes = theme_variables(pd)
    missing = sorted(tokens_used(out_nodes) - set(var))
    print(f"theme {slug} ({prefix}) · {len(pick)} components → {len(out_nodes)} roots · {len(var)} variables")
    if gaps:
        print("WARN plan lacks components the skill requires (02 §9, 06 §3): " + ", ".join(gaps))
    if unmatched:
        print("INFO no library skeleton for these archetypes (built from the plan tree alone): " + ", ".join(unmatched))
    if hints:
        print("INFO library components the plan builds inline or skips: " + ", ".join(hints))
    if missing:
        die("tokens used by the library but not in plandata variables: " + ", ".join(missing))
    if a.dry_run:
        return 0

    doc = {"version": lib["version"], "children": []}
    if os.path.exists(a.out):
        try:
            with open(a.out, encoding="utf-8") as f:
                doc = json.load(f)
        except ValueError:
            die(f"{a.out} is not a plain .pen JSON file")
        taken = {n.get("name") for n in doc.get("children", [])}
        clash = sorted(taken & {n["name"] for n in out_nodes})
        if clash:
            die(f"{a.out} already has library roots ({clash[0]} …); the copy runs once per theme")
        top = max((n.get("y", 0) + (n.get("height") if isinstance(n.get("height"), (int, float)) else 0)
                   for n in doc.get("children", [])), default=0)
        for n in out_nodes:
            n["y"] += top + GAP * 4 if doc.get("children") else 0
    doc.setdefault("variables", {}).update(var)
    doc_themes = doc.setdefault("themes", {})
    for axis, values in themes.items():
        doc_themes[axis] = values
    doc["children"] = doc.get("children", []) + out_nodes
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"wrote {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
