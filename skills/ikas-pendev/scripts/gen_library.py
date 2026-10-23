#!/usr/bin/env python3
"""gen_library.py - build the structure library ikas-ecommerce.lib.pen from library/inventory.json.

The library is a skeleton (references/12-library.md): every component is a grey
anatomy frame whose children are its parts, in inventory order. Required parts are
enabled, optional parts are present with enabled:false. Every state after the first is
a ref of the component named "<root> — <state>". Nothing carries a design value: all
fills, fonts, sizes and gaps are token references, and the token values are neutral
placeholders that each theme replaces with its own (globals.md).

Node ids are derived from the component and part names, so the output is byte-stable:
the same inventory always gives the same file, and a diff of the .pen shows only what
the inventory changed.

Usage:
  python3 -I gen_library.py [--inventory library/inventory.json] [-o library/ikas-ecommerce.lib.pen]
  python3 -I gen_library.py --check     (exit 1 when the committed .pen is not what the inventory gives)

Stdlib only, Python 3.9+.
"""

import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(os.path.dirname(HERE), "library")
TAG = "ikas-lib"

# Placeholder values only. Names follow 02-contract.md §3 (41 core variables + radius roles);
# a theme never keeps these values.
GREY = {"color-bg": "#F4F4F4", "color-text": "#1E1E1E", "color-muted": "#7A7A7A", "color-line": "#C8C8C8",
        "color-surface": "#E6E6E6", "color-inverse-bg": "#1E1E1E", "color-inverse-text": "#F4F4F4",
        "color-accent": "#5A5A5A", "color-accent-text": "#F4F4F4", "color-scrim": "#1E1E1E99",
        "color-transparent": "#F4F4F400", "color-danger": "#5A5A5A", "color-success": "#5A5A5A"}
FONTS = ["font-display", "font-ui", "font-body", "font-price", "font-mono"]
SIZES = {"text-display": 40, "text-h2": 32, "text-h3": 24, "text-h4": 20, "text-title": 16, "text-ui": 14,
         "text-ui-sm": 13, "text-badge": 11, "text-label": 11, "text-body": 14, "text-price": 16,
         "space-page": 24, "space-grid": 16, "space-card": 8, "space-panel": 16, "space-xs": 4, "space-sm": 8,
         "space-md": 12, "space-section": 48, "size-header": 64, "size-line": 1, "size-logo": 20,
         "opacity-inactive": 0.4, "radius-control": 0, "radius-card": 0, "radius-media": 0}
PLACEHOLDER_FONT = "Space Mono"

BANDS = [("primitive", "sub", "Primitives"), ("element", "sub", "Commerce elements"),
         ("component", "sub", "Commerce components"), ("component", "block", "Blocks (copied into a section)"),
         ("shell", "section", "Shells"), ("overlay", "overlay", "Overlays")]
ROOT = {"sub": "P/Sub/{}", "block": "P/Block/{}", "section": "P/Section/{}", "overlay": "P/Overlay/{}"}
WIDTH = {"sub": 280, "block": 360, "section": 720, "overlay": 360}


def nid(*names):
    return "L" + hashlib.sha1("/".join(names).encode("utf-8")).hexdigest()[:10]


def variables():
    v = {k: {"type": "color", "value": c} for k, c in GREY.items()}
    v.update({k: {"type": "string", "value": PLACEHOLDER_FONT} for k in FONTS})
    v.update({k: {"type": "number", "value": n} for k, n in SIZES.items()})
    return v


def label(owner, text, color="$color-muted"):
    return {"type": "text", "id": nid(owner, "label"), "name": "lib-label", "content": text,
            "fontFamily": "$font-mono", "fontSize": "$text-label", "fill": color,
            "metadata": {"type": TAG, "textClass": "code", "code": "lib"}}


def part_node(comp, p):
    opt = bool(p.get("opt"))
    node = {"type": "frame", "id": nid(comp["name"], p["layer"]), "name": p["layer"],
            "width": "fill_container", "layout": "horizontal", "padding": "$space-xs",
            "fill": "$color-bg", "children": [label(comp["name"] + "/" + p["layer"], p["layer"] + (" · opt" if opt else ""))],
            "metadata": {"type": TAG, "lib": "opt" if opt else "req"}}
    if opt:
        node["enabled"] = False
        node["metadata"]["ikas"] = p.get("ikas", "")
    if p.get("note"):
        node["context"] = p["note"]
    return node


def root_context(comp):
    seg = ["states " + ", ".join(comp["states"])]
    seg += ["must " + m["rule"] + (f" ({m['figure']})" if m.get("figure") else "") for m in comp.get("must", [])]
    if comp.get("note"):
        seg.append(comp["note"])
    return " · ".join(seg)


def component_column(comp):
    name = ROOT[comp["kind"]].format(comp["name"])
    meta = {"type": TAG, "role": comp["kind"], "ikas": comp["name"], "layer": comp["layer"], "lib": 1}
    if comp.get("host"):
        meta["host"] = comp["host"]
    if comp.get("optional"):
        meta["optional"] = True
    root = {"type": "frame", "id": nid(comp["name"]), "name": name, "reusable": True,
            "width": WIDTH[comp["kind"]], "layout": "vertical", "gap": "$space-xs", "padding": "$space-sm",
            "fill": "$color-surface", "stroke": "$color-line", "strokeWidth": 1, "strokeAlignment": "inner",
            "metadata": meta, "context": root_context(comp),
            "children": [part_node(comp, p) for p in comp["parts"]]}
    states = [{"type": "ref", "id": nid(comp["name"], "state", s), "ref": root["id"], "name": f"{name} — {s}",
               "context": "state " + s} for s in comp["states"][1:]]
    return {"type": "frame", "id": nid(comp["name"], "column"), "name": comp["name"], "layout": "vertical",
            "gap": "$space-md", "children": [root] + states}


def build(inv):
    bands = []
    for layer, kind, title in BANDS:
        comps = [c for c in inv["components"] if c["layer"] == layer and c["kind"] == kind]
        if not comps:
            continue
        row = {"type": "frame", "id": nid("band", title, "row"), "name": "row", "layout": "horizontal",
               "gap": "$space-section", "children": [component_column(c) for c in comps]}
        head = {"type": "text", "id": nid("band", title, "title"), "name": "band-title", "content": title,
                "fontFamily": "$font-mono", "fontSize": "$text-h3", "fill": "$color-text",
                "metadata": {"type": TAG, "textClass": "code", "code": "lib"}}
        bands.append({"type": "frame", "id": nid("band", title), "name": "Band/" + title, "layout": "vertical",
                      "gap": "$space-panel", "children": [head, row]})
    page = {"type": "frame", "id": nid("library"), "name": "ikas-ecommerce library · structure only",
            "x": 0, "y": 0, "layout": "vertical", "gap": "$space-section", "padding": "$space-section",
            "fill": "$color-bg", "children": bands,
            "context": "skeleton: parts, states and port marks; no design values (references/12-library.md)"}
    return {"version": "2.21", "variables": variables(), "children": [page]}


def render(inv):
    return json.dumps(build(inv), ensure_ascii=False, indent=2) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--inventory", default=os.path.join(LIB, "inventory.json"))
    ap.add_argument("-o", "--out", default=os.path.join(LIB, "ikas-ecommerce.lib.pen"))
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    with open(a.inventory, encoding="utf-8") as f:
        text = render(json.load(f))
    if a.check:
        try:
            with open(a.out, encoding="utf-8") as f:
                same = f.read() == text
        except FileNotFoundError:
            same = False
        print("library up to date" if same else f"{a.out} differs from the inventory; run gen_library.py")
        return 0 if same else 1
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"wrote {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
