#!/usr/bin/env python3
"""Extract animation targets from an ikas-pendev plan, or render the pen.dev check snippet.

Usage:
  python3 extract_targets.py <plan.md> [--format tsv|json|ids]
  python3 extract_targets.py <plan.md> --js all|section:<Key>|manifest [--mode-only]

--format tsv   one target per line: id<TAB>section<TAB>layer<TAB>recipe<TAB>impl (plan §8 step 1)
--format json  every target with all YAML keys
--format ids   one id per line

--js MODE      fills scripts/pendev_checks.js (__PREFIX__, __SLUG__, __CONTRACT__, __EXP__,
               __MODE__), strips its whole-line comments and prints a single snippet to paste
               into one read-only `mcp__pencil__execute` call.
               MODE: all | section:<Key> | manifest. <Key> is a §6.2 Section/Overlay key, or a
               build-unit band: DS | Sub | Page | Overlays | Motion (aliases ds, subs, pages,
               overlays, motion). A band or key also works alone: `--js motion` is
               `--js section:Motion`, `--js Hero` is `--js section:Hero`.
--mode-only    embed only the expectations the chosen mode needs (smaller snippet).
--checks IDS   comma list of CHK ids to run (default: all of the mode). Use when one execute
               call times out on a large canvas, e.g. --checks anim, then --checks parity. Only the
               expectations those checks read are embedded, so the snippet stays small.
--part K/N     node-walk checks (hardcoded, textclass, clip, refassets) visit only every N-th
               root starting at K; run K=1..N and add the counts. With --js manifest it prints
               the ROOT lines of that slice; concatenate the N outputs into canvas-dump.txt.

Everything is derived from the plan: variables from the §3 SetVariables keys, sections and
overlays from the §6.2 `#### Section/X` / `#### Overlay/X` headings, pages from the §6.3 table
(`Auth (×4)` expands to Login/Register/ForgotPassword/RecoverPassword unless names are given as
`Auth (×4: A, B, C, D)`), slug from the §4 metadata example (`type:"<slug>"`), prefix from the
ids, reference host from the URL in the header lines, DS frame count 5 (contract 1) / 6 (contract 2),
parity exceptions from the §6.2 `- **Yalnız masaüstü katmanlar:**` / `- **Yalnız masaüstü durumlar:**` lines.
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lint_plan as L  # noqa: E402

CHK_IDS = ("vars", "ds", "sections", "overlays", "pages", "spacing", "subfit", "temp", "seed", "anim", "hardcoded", "textclass", "clip",
           "rootmeta", "bgprop", "parity", "props", "data", "placeholder", "refassets", "storefront", "dividers", "radius")


def plan_data(plan):
    """{key: {"need": [[kind, value, layer, [subs]], ...], "known": ["data:src" | "code:name", ...]}} from the
    {data:} / {code:} markers of each Section/Overlay tree; subs = Sub names on the same tree line."""
    import build_manifest as B
    subs = set(plan.components.keys())
    out = {}
    for key, e in plan.entries.items():
        tree = [t for f in e["trees"] for _ln, t in f["body"]]
        rows = [[m["kind"], m["value"], m["layer"] or "", m["subs"]] for m in B.tree_data_marks(tree, subs)]
        if rows:
            out[key] = {"need": rows, "known": sorted({r[0] + ":" + r[1] for r in rows})}
    return out
CHECK_EXP = {"vars": ("vars",), "ds": ("ds",), "overlays": ("overlayDevices",), "pages": ("pages", "pageExpand"),
             "anim": ("ids", "idOwner"), "parity": ("parity", "overlayDevices"), "props": ("props",),
             "data": ("data",), "refassets": ("referenceHost",), "seed": ("seed",)}
LAYER_TYPES = ("TEXT", "RICH_TEXT", "IMAGE", "IMAGE_LIST", "VIDEO", "SVG", "SVG_LIST")


def plan_props(plan):
    """{key: {"need": [[name, type, layer], ...], "known": [name, ...]}}. need: layer-type props a Section/Overlay
    places in its §6.2 tree (a canvas root must carry them as metadata.prop or a context mark); child-component
    props are excluded. known: every prop name the plan gives the key (props line, child components, tree)."""
    import build_manifest as B
    out = {}
    for key, e in plan.entries.items():
        line = e["props"][1] if e.get("props") else ""
        _top, children = B.parse_props_line(re.sub(r"^- \*\*Prop'lar:\*\*\s*", "", line))
        child = {n for c in children for n, _ in c["props"]}
        tree = [t for f in e["trees"] for _ln, t in f["body"]]
        seen, rows = set(), []
        marks = B.parse_tree(tree)
        for m in marks:
            if m["kind"] == "prop" and m["type"] in LAYER_TYPES and m["name"] not in child and m["name"] not in seen:
                seen.add(m["name"])
                rows.append([m["name"], m["type"], m["layer"] or ""])
        known = sorted({n for n, _ in _top} | child | {m["name"] for m in marks if m["kind"] == "prop"} | {"backgroundColor"})
        out[key] = {"need": rows, "known": known}
    return out
BANDS = {"DS": "DS", "ds": "DS", "Sub": "Sub", "sub": "Sub", "subs": "Sub", "Page": "Page",
         "page": "Page", "pages": "Page", "Overlays": "Overlays", "overlays": "Overlays",
         "Motion": "Motion", "motion": "Motion"}


def clean(v):
    if isinstance(v, bool):
        return v
    return "" if v is None else str(v)


def target_rows(plan):
    out = []
    for t in plan.targets:
        d = {k: clean(v) for k, v in t.items() if not k.startswith("_")}
        out.append(d)
    return out


def build_exp(plan, mode, mode_only):
    contract = plan.marker_contract or 1
    P = plan.prefix_guess() or "X"
    slug = plan.slug_guess() or "theme"
    data, _lines, _err = L.parse_setvariables(plan.md)
    variables = list(data.keys()) if data else []
    sections = [k for k, e in plan.entries.items() if e["kind"] == "Section"]
    overlays = [k for k, e in plan.entries.items() if e["kind"] == "Overlay"]
    pages, page_expand = {}, {}
    for _ln, name, secs, expanded in plan.pages():
        base = re.split(r"\s*\(", name, 1)[0].strip()
        pages[base] = list(secs)
        page_expand[base] = max(1, len(expanded))
    ids = [t.get("id") for t in plan.targets if isinstance(t.get("id"), str)]
    odev = overlay_devices(plan, P, overlays)
    parity = {k: dict(layers=e.get("desktop_only") or [], states=e.get("desktop_only_states") or [])
              for k, e in plan.entries.items() if e.get("desktop_only") or e.get("desktop_only_states")}
    exp = dict(prefix=P, slug=slug, contract=contract, referenceHost=plan.reference_host() or "",
               vars=variables, ds=list(L.DS_C2 if contract >= 2 else L.DS_C1),
               sections=sections, overlays=overlays, overlayDevices=odev, pages=pages, pageExpand=page_expand, ids=ids,
               parity=parity, props=plan_props(plan) if contract >= 2 else {},
               data=plan_data(plan) if contract >= 2 else {},
               idOwner={t["id"]: t.get("section") for t in plan.targets if isinstance(t.get("id"), str)
                        and t.get("section") and not str(t.get("section")).startswith("Sub/")})
    exp["seed"] = sample_catalog(plan)
    if mode.startswith("section:"):
        key = mode.split(":", 1)[1]
        band = BANDS.get(key)
        if band == "Sub":
            uids = [t["id"] for t in plan.targets if str(t.get("section", "")).startswith("Sub/")]
        elif band == "Overlays":
            keys = set(overlays)
            uids = unit_ids(plan, keys)
        elif band:
            uids = []
        else:
            if key not in plan.entries:
                raise SystemExit("unknown unit key %r (not a §6.2 Section/Overlay or a band)" % key)
            uids = unit_ids(plan, {key})
        exp["unit"] = dict(key=band or key, ids=uids)
        if mode_only:
            keep = dict(prefix=P, slug=slug, contract=contract, referenceHost=exp["referenceHost"], unit=exp["unit"],
                        idOwner=exp["idOwner"], seed=exp["seed"])
            if band == "DS":
                keep.update(vars=variables, ds=exp["ds"])
            elif band == "Page":
                keep.update(pages=pages)
            elif band == "Overlays":
                keep.update(overlays=overlays, overlayDevices=odev, parity={k: v for k, v in parity.items() if k in overlays},
                            props={k: v for k, v in exp["props"].items() if k in overlays},
                            data={k: v for k, v in exp["data"].items() if k in overlays})
            elif not band:
                keep.update(sections=[key] if key in sections else [], overlays=[key] if key in overlays else [],
                            overlayDevices={key: odev[key]} if key in odev else {},
                            parity={key: parity[key]} if key in parity else {},
                            props={key: exp["props"][key]} if key in exp["props"] else {},
                            data={key: exp["data"][key]} if key in exp["data"] else {})
            exp = keep
    elif mode == "manifest" and mode_only:
        exp = dict(prefix=P, slug=slug, contract=contract)
    return exp, P, slug, contract


def sample_catalog(plan):
    """The plan §6.6 sample-catalogue block (gen_plan renders it from plandata `sampleCatalog`), or None."""
    m = re.search(r"<!-- sample-catalog:start -->\s*```json\n(.*?)\n```\s*<!-- sample-catalog:end -->", plan.md.text, re.S)
    return json.loads(m.group(1)) if m else None


def overlay_devices(plan, P, overlays):
    """Devices each overlay is drawn for: the §6.4 list (`P/Overlay/X@mobile — …`) when the plan
    has one, otherwise desktop + mobile."""
    rng = plan.md.section("6.4", 3)
    txt = plan.md.text_range(rng) if rng else ""
    listed = {}
    for key, dev in re.findall(r"`%s/Overlay/([A-Za-z]\w*)@(desktop|mobile)" % re.escape(P), txt):
        listed.setdefault(key, [])
        if dev not in listed[key]:
            listed[key].append(dev)
    return {k: (listed.get(k) or ["desktop", "mobile"]) for k in overlays}


def unit_ids(plan, keys):
    """Ids of the given sections plus the CMP ids of the components they name in `via`."""
    own = [t for t in plan.targets if t.get("section") in keys]
    vias = {t.get("via") for t in own if t.get("via")}
    cmp_ids = [t["id"] for t in plan.targets if str(t.get("section", "")).startswith("Sub/")
               and t["section"][4:] in vias]
    return [t["id"] for t in own] + cmp_ids


def render_js(exp, P, slug, contract, mode):
    src = open(os.path.join(HERE, "pendev_checks.js"), encoding="utf-8").read()
    lines = [l.strip() for l in src.split("\n") if l.strip() and not l.lstrip().startswith("//")]
    js = "\n".join(lines).strip() + "\n"
    exp_json = json.dumps(exp, ensure_ascii=False, separators=(",", ":"))
    for k, v in (("__PREFIX__", P), ("__SLUG__", slug), ("__CONTRACT__", str(int(contract))),
                 ("__MODE__", mode), ("__EXP__", exp_json)):
        js = js.replace(k, v)
    left = re.findall(r"__[A-Z]+__", js)
    if left:
        raise SystemExit("unfilled placeholders: %s" % ", ".join(sorted(set(left))))
    return js


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("plan")
    ap.add_argument("--format", choices=["tsv", "json", "ids"], default="tsv",
                    help="target list format (default tsv)")
    ap.add_argument("--js", metavar="MODE",
                    help="render the check snippet. MODE: all | manifest | section:<Key> | <band>. "
                         "<Key> is a §6.2 Section/Overlay key; <band> is DS, Sub, Page, Overlays or Motion "
                         "(also ds, subs, pages, overlays, motion), alone or as section:<band>")
    ap.add_argument("--mode-only", action="store_true", help="embed only what the mode needs")
    ap.add_argument("--checks", metavar="IDS", help="comma list of CHK ids: " + " ".join(CHK_IDS))
    ap.add_argument("--part", metavar="K/N", help="walk every N-th root starting at K")
    args = ap.parse_args(argv)
    plan = L.Plan(args.plan, open(args.plan, encoding="utf-8").read())
    if args.js:
        mode = args.js
        if mode in BANDS or mode in plan.entries:
            mode = "section:" + mode
        if not (mode in ("all", "manifest") or re.match(r"^section:[A-Za-z][A-Za-z0-9]*$", mode)):
            ap.error("--js must be all, manifest, section:<Key> or a band (%s)" % ", ".join(sorted(set(BANDS.values()))))
        exp, P, slug, contract = build_exp(plan, mode, args.mode_only)
        if args.checks:
            ids = [x.strip() for x in args.checks.split(",") if x.strip()]
            unknown = [x for x in ids if x not in CHK_IDS]
            if unknown:
                ap.error("unknown CHK ids: %s (known: %s)" % (", ".join(unknown), " ".join(CHK_IDS)))
            exp["only"] = ids
            need = {"prefix", "slug", "contract", "unit", "sections", "overlays", "only"}
            for c in ids:
                need.update(CHECK_EXP.get(c, ()))
            exp = {k: v for k, v in exp.items() if k in need}
        if args.part:
            mm = re.match(r"^(\d+)/(\d+)$", args.part)
            if not mm or not (1 <= int(mm.group(1)) <= int(mm.group(2))):
                ap.error("--part must be K/N with 1 <= K <= N")
            exp["part"] = [int(mm.group(1)), int(mm.group(2))]
        sys.stdout.write(render_js(exp, P, slug, contract, mode))
        return 0
    rows = target_rows(plan)
    if args.format == "ids":
        for r in rows:
            print(r.get("id", ""))
    elif args.format == "json":
        print(json.dumps(rows, ensure_ascii=False, indent=1))
    else:
        for r in rows:
            print("\t".join(r.get(k, "") for k in ("id", "section", "layer", "recipe", "impl")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
