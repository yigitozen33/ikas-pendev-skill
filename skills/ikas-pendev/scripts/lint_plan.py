#!/usr/bin/env python3
"""Lint an ikas-pendev build plan (and/or the phase-1 reference docs).

Usage:
  python3 lint_plan.py <plan.md> [--globals G.md] [--components C.md]
                       [--catalogue 03-motion.md|motion-catalogue.json]
                       [--contract 1|2] [--prefix P] [--json]
  python3 lint_plan.py --globals G.md [--components C.md]      # phase-1 gate

Output: one finding per line, `§|SEV|loc|msg` (SEV = ERROR|WARN|INFO; msg starts
with the check id L01..L20), then `LINT OK (n targets)` or
`LINT FAIL (e errors, w warnings)`. Exit code 1 when any ERROR is reported.

The contract is auto-detected from the `<!-- ikas-pendev contract:2 -->` marker
(absent -> contract 1, the legacy format of examples/ornek). `--contract` overrides it.

Checks
  L01 code fences balanced, anim-targets markers paired, no leftover placeholders
  L02 anim-targets YAML: 13 required keys (+ optional via), done is a bool
  L03 target id unique and matches ^<P>-(CMP|[A-Z]{2,5})-\\d\\d$
  L04 recipe exists (catalogue M-xx or the plan's own §5.1 <P>-M-xx); M-17 forbidden
  L05 target section exists (§6.2 heading or Sub/<§6.1 component>)
  L06 target layer appears (word boundary) in its own tree / §6.1 row
  L07 via names a §6.1 component
  L08 impl vocabulary (gsap / lenis / framer-motion are errors)
  L09 §7 totals, per-section counts, recipe lists, id ranges, recipe usage
  L10 §6.5 Motion States coverage (WARN)
  L11 §3 core variable set (37 contract 1 / 41 contract 2), radius roles and variable types
  L12 §3 theme axes: device on text-*/space-*/size-logo, mode on colours, #RRGGBBAA
  L13 fonts: a family on the pen.dev deny list (INVALID_FONTS) -> ERROR
  L14 WCAG contrast >= 4.5 (contract 2 ERROR, contract 1 WARN)
  L15 {name:TYPE} notation: camelCase name, TYPE in the 30 ikas prop types
  L16 contract 2: quoted literal on a tree line without {name:TYPE}/{data:}/{code:}
  L17 contract 2: every Section's Prop'lar line has backgroundColor COLOR
  L18 §6.3 pages reference Sections only
  L19 contract 2 required extras: DS/Imagery, Button eklendi + stok yok, FilterDrawer, QuickBuy
  L22 contract 2 with --globals: globals.md has colour schemes (§1a), ikas text styles with four breakpoints (§2a) and in-between breakpoint behaviour (§4a)
  L21 contract 2 ikas merchant blocks and storefront completeness (06-page-coverage §3b, §3c) for full store plans
  L20 --globals / --components integrity (tables, catalogue, prop types, defaults)

Stdlib only; PyYAML is used, when installed, as an extra YAML syntax check.
"""
import argparse
import collections
import json
import os
import re
import sys

try:  # optional
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- constants
CORE37 = [
    "color-bg", "color-text", "color-muted", "color-line", "color-surface", "color-inverse-bg",
    "color-inverse-text", "color-accent", "color-accent-text", "color-scrim",
    "font-display", "font-ui", "font-body", "font-price", "font-mono",
    "text-display", "text-h2", "text-h3", "text-h4", "text-title", "text-ui", "text-ui-sm",
    "text-badge", "text-label", "text-body", "text-price",
    "space-page", "space-grid", "space-card", "space-panel", "space-xs", "space-sm", "space-md",
    "space-section", "size-header", "size-line", "opacity-inactive",
]
EXTRA_C2 = ["color-transparent", "size-logo", "color-danger", "color-success"]
ALPHA_OK = {"color-scrim", "color-transparent"}
RADIUS_ROLES = ["radius-control", "radius-card", "radius-media", "radius-pill"]  # 02 §3 radius roles

PROP_TYPES = [
    "TEXT", "RICH_TEXT", "NUMBER", "NUMBER_RANGE", "BOOLEAN", "IMAGE", "IMAGE_LIST", "VIDEO", "SVG",
    "SVG_LIST", "DATE", "LINK", "LIST_OF_LINK", "COLOR", "PRODUCT", "PRODUCT_LIST",
    "PRODUCT_ATTRIBUTE", "PRODUCT_ATTRIBUTE_LIST", "CATEGORY", "CATEGORY_LIST", "BRAND",
    "BRAND_LIST", "BLOG", "BLOG_LIST", "BLOG_CATEGORY", "BLOG_CATEGORY_LIST", "TYPE", "ENUM",
    "COMPONENT", "COMPONENT_LIST",
]
MERCHANT_TYPES = {
    "IMAGE", "IMAGE_LIST", "VIDEO", "PRODUCT", "PRODUCT_LIST", "PRODUCT_ATTRIBUTE",
    "PRODUCT_ATTRIBUTE_LIST", "CATEGORY", "CATEGORY_LIST", "BRAND", "BRAND_LIST", "BLOG",
    "BLOG_LIST", "BLOG_CATEGORY", "BLOG_CATEGORY_LIST",
}
PAGE_TYPES = {
    "INDEX", "CATEGORY", "PRODUCT_DETAIL", "CART", "ACCOUNT", "LOGIN", "REGISTER",
    "FORGOT_PASSWORD", "RECOVER_PASSWORD", "NOT_FOUND", "BLOG", "BLOG_POST", "SEARCH",
    "FAVORITES", "CUSTOMER_EMAIL_VERIFICATION", "COLLECTION", "CUSTOM",
    # remaining IkasThemePageType values
    "PRODUCT", "BRAND", "ADDRESSES", "ORDERS", "ORDER_DETAIL", "FAVORITE_PRODUCTS", "BLOG_INDEX",
    "BLOG_CATEGORY", "CHECKOUT", "RAFFLE", "RAFFLE_DETAIL", "RAFFLE_ACCOUNT", "ACTIVATE_CUSTOMER",
}
REQ_KEYS = ["id", "section", "layer", "recipe", "trigger", "what", "from", "to", "timing",
            "impl", "mobile", "reducedMotion", "done"]
OPT_KEYS = ["via"]
IMPL_VOCAB = {"css-transition", "css-keyframes", "theme-keyframe", "io-hook", "animejs",
              "scroll-scrub", "layout", "setInterval", "pointermove", "rAF"}
IMPL_FORBIDDEN = {"gsap", "lenis", "framer-motion", "framer", "motion-one", "locomotive"}
IMPL_FILLER = {"ya", "da", "veya", "ile", "benzeri", "or", "and", "opsiyonel", "optional",
               "stagger", "timeline", "spring", "+"}
TRIGGERS = {"load", "inview", "hover", "click", "drag", "auto", "auto-loop", "scroll-scrub",
            "sticky", "state-change", "focus", "scroll"}
# Families pen.dev rejects ("Font family … is invalid" in an execute response). Grow this list whenever a
# build hits that warning; any family not listed is allowed and proven by the DS step's first Insert.
INVALID_FONTS = {"Mona Sans Condensed", "Big Shoulders Display"}
STATE_RECIPES_DEFAULT = {"M-03", "M-05", "M-06", "M-07", "M-09", "M-11", "M-12", "M-20", "M-21",
                         "M-22", "M-23", "M-24"}
# (foreground, ground, minimum, contract-2 severity); references/02-contract.md §10.
# Contract 1 reports every failing pair as WARN. "color-scrim>color-bg" = scrim composited over bg.
CONTRAST_PAIRS = [
    ("color-text", "color-bg", 4.5, "ERROR"),
    ("color-muted", "color-bg", 4.5, "ERROR"),
    ("color-inverse-text", "color-inverse-bg", 4.5, "ERROR"),
    ("color-accent-text", "color-accent", 4.5, "ERROR"),
    ("color-danger", "color-bg", 4.5, "ERROR"),
    ("color-text", "color-surface", 4.5, "WARN"),
    ("color-muted", "color-surface", 4.5, "WARN"),
    ("color-success", "color-bg", 3.0, "WARN"),
    ("color-line", "color-bg", 3.0, "WARN"),
    ("color-accent", "color-bg", 3.0, "WARN"),
    ("color-inverse-text|color-text", "color-scrim>color-bg", 4.5, "WARN"),
]
# "a|b" as foreground = the better of a and b (text on a scrim is whichever of inverse-text /
# text is light in that mode; a literal inverse-text-on-scrim pair always fails in dark mode).
DS_C1 = ["Colors", "Typography", "Spacing", "Icons", "Motion"]
DS_C2 = DS_C1 + ["Imagery"]
CONTRACT_RE = re.compile(r"<!--\s*ikas-pendev\s+contract:(\d+)\s*-->")
CAMEL_RE = re.compile(r"^[a-z][A-Za-z0-9]*$")
DATA_SRC_RE = re.compile(r"^[a-z][A-Za-z0-9]*(\.[A-Za-z0-9]+)+$")
CODE_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9-]*$")
NOTATION_RE = re.compile(r"\{([^{}\s:]+):([^{}\s]+)\}")
QUOTED_RE = re.compile(r"\"[^\"]+\"|“[^”]+”")


# ---------------------------------------------------------------- findings
class Report:
    def __init__(self):
        self.items = []

    def add(self, sect, sev, loc, check, msg):
        self.items.append(dict(sect=sect, sev=sev, loc=loc, check=check, msg=msg))

    def count(self, sev):
        return sum(1 for i in self.items if i["sev"] == sev)


def loc_of(name, line):
    if line:
        return "%s:L%d" % (name, line) if name else "L%d" % line
    return name or "-"


# ---------------------------------------------------------------- markdown helpers
def split_cells(row):
    """Split a markdown table row on | outside backticks."""
    row = row.strip()
    if row.startswith("|"):
        row = row[1:]
    if row.endswith("|") and not row.endswith("\\|"):
        row = row[:-1]
    cells, cur, tick = [], [], False
    i = 0
    while i < len(row):
        ch = row[i]
        if ch == "\\" and i + 1 < len(row) and row[i + 1] == "|":
            cur.append("|")
            i += 2
            continue
        if ch == "`":
            tick = not tick
        if ch == "|" and not tick:
            cells.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
        i += 1
    cells.append("".join(cur).strip())
    return cells


class MD:
    """Line-oriented markdown model: headings, fences, tables."""

    def __init__(self, text):
        self.text = text
        self.lines = text.split("\n")
        self.heads = []      # (line, level, text)
        self.fences = []     # dict(start, end, lang, body=[(line, text)])
        self.unclosed = None
        cur = None
        for i, l in enumerate(self.lines, 1):
            m = re.match(r"^\s{0,3}(```+|~~~+)\s*(.*)$", l)
            if cur is None:
                if m:
                    cur = dict(start=i, end=None, lang=m.group(2).strip(), body=[], mark=m.group(1)[0])
                    continue
                h = re.match(r"^(#{1,6})\s+(.*?)\s*$", l)
                if h:
                    self.heads.append((i, len(h.group(1)), h.group(2)))
            else:
                if m and m.group(1)[0] == cur["mark"] and not m.group(2).strip():
                    cur["end"] = i
                    self.fences.append(cur)
                    cur = None
                else:
                    cur["body"].append((i, l))
        if cur is not None:
            self.unclosed = cur
            cur["end"] = len(self.lines) + 1
            self.fences.append(cur)
        self.in_fence = set()
        for f in self.fences:
            for ln in range(f["start"], f["end"] + 1):
                self.in_fence.add(ln)

    def section(self, num, level=None):
        """(start, end) line range of the heading whose text starts with `num` (e.g. '3.', '6.1')."""
        pat = re.compile(r"^%s(?:\.|\s|$)" % re.escape(num.rstrip(".")))
        for idx, (ln, lv, tx) in enumerate(self.heads):
            if (level is None or lv == level) and pat.match(tx):
                end = len(self.lines) + 1
                for ln2, lv2, _ in self.heads[idx + 1:]:
                    if lv2 <= lv:
                        end = ln2
                        break
                return ln, end
        return None

    def heading_range(self, idx):
        ln, lv, _ = self.heads[idx]
        end = len(self.lines) + 1
        for ln2, lv2, _ in self.heads[idx + 1:]:
            if lv2 <= lv:
                end = ln2
                break
        return ln, end

    def tables(self, rng=None):
        """Yield tables as dict(start, header, sep_ok, rows=[(line, cells)])."""
        a, b = rng if rng else (1, len(self.lines) + 1)
        out, cur = [], None
        for ln in range(a, min(b, len(self.lines) + 1)):
            l = self.lines[ln - 1]
            if ln in self.in_fence:
                if cur:
                    out.append(cur)
                    cur = None
                continue
            if l.lstrip().startswith("|"):
                cells = split_cells(l)
                if cur is None:
                    cur = dict(start=ln, header=cells, sep_ok=False, rows=[], sep_line=None)
                elif cur["sep_line"] is None and all(re.match(r"^:?-{3,}:?$", c) for c in cells if c) and cells:
                    cur["sep_ok"] = True
                    cur["sep_line"] = ln
                    cur["sep_cells"] = len(cells)
                else:
                    cur["rows"].append((ln, cells))
            else:
                if cur:
                    out.append(cur)
                    cur = None
        if cur:
            out.append(cur)
        return out

    def text_range(self, rng):
        a, b = rng
        return "\n".join(self.lines[a - 1:b - 1])


# ---------------------------------------------------------------- YAML subset parser
def parse_scalar(v):
    """Return (value, error|None) for the YAML subset used in anim-targets."""
    v = v.strip()
    if v == "":
        return None, "empty value"
    if v.startswith('"'):
        m = re.match(r'^"((?:[^"\\]|\\.)*)"$', v)
        if not m:
            return v, "invalid double-quoted scalar (unescaped quote or trailing text)"
        return m.group(1).replace('\\"', '"').replace("\\\\", "\\"), None
    if v.startswith("'"):
        m = re.match(r"^'((?:[^']|'')*)'$", v)
        if not m:
            return v, "invalid single-quoted scalar"
        return m.group(1).replace("''", "'"), None
    if v.startswith("{"):
        depth, q = 0, False
        i = 0
        while i < len(v):
            ch = v[i]
            if q:
                if ch == "\\":
                    i += 2
                    continue
                if ch == '"':
                    q = False
            elif ch == '"':
                q = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0 and i != len(v) - 1:
                    return v, "text after closing brace of flow mapping"
            i += 1
        if depth != 0 or q:
            return v, "unbalanced flow mapping"
        return v, None
    if v in ("true", "false"):
        return v == "true", None
    if v[0] in "[&*!|>%@`":
        return v, "plain scalar starts with reserved indicator %r" % v[0]
    if ": " in v:
        return v, "plain scalar contains ': ' (quote it)"
    if " #" in v:
        return v, "plain scalar contains ' #' (YAML comment; quote it)"
    return v, None


def parse_targets_block(body):
    items, errs = [], []
    cur = None
    for ln, t in body:
        if not t.strip() or t.strip().startswith("#"):
            continue
        m = re.match(r"^- ([A-Za-z_]\w*):(?:\s(.*))?$", t)
        if m:
            cur = {"_line": ln, "_lines": {}}
            items.append(cur)
        else:
            m = re.match(r"^  ([A-Za-z_]\w*):(?:\s(.*))?$", t)
            if not m or cur is None:
                errs.append((ln, "unparseable YAML line: %s" % t.strip()[:60]))
                continue
        k, v = m.group(1), m.group(2) or ""
        if k in cur:
            errs.append((ln, "duplicate key '%s'" % k))
        val, e = parse_scalar(v)
        if e:
            errs.append((ln, "%s: %s" % (k, e)))
        cur[k] = val
        cur["_lines"][k] = ln
    return items, errs


# ---------------------------------------------------------------- JS object literal -> JSON
def js_to_json(src):
    out, i, n = [], 0, len(src)
    while i < n:
        ch = src[i]
        if ch in "\"'":
            j = i + 1
            buf = []
            while j < n and src[j] != ch:
                if src[j] == "\\":
                    buf.append(src[j:j + 2])
                    j += 2
                    continue
                buf.append(src[j])
                j += 1
            s = "".join(buf)
            if ch == "'":
                s = s.replace('"', '\\"')
            out.append('"' + s + '"')
            i = j + 1
            continue
        m = re.match(r"[A-Za-z_$][\w$]*", src[i:])
        if m and (not out or not re.match(r"[\w$]", out[-1][-1:] or " ")):
            word = m.group(0)
            k = i + len(word)
            while k < n and src[k] in " \t":
                k += 1
            if k < n and src[k] == ":" and word not in ("true", "false", "null"):
                out.append('"%s"' % word)
            else:
                out.append(word)
            i += len(word)
            continue
        out.append(ch)
        i += 1
    s = "".join(out)
    s = re.sub(r",(\s*[}\]])", r"\1", s)
    return json.loads(s)


def parse_setvariables(md):
    """Return (dict name -> {type, value}, line_of_name, error|None) from the §3 js fence."""
    rng = md.section("3", 2)
    if not rng:
        return None, {}, "§3 not found"
    for f in md.fences:
        if rng[0] <= f["start"] < rng[1] and "SetVariables" in "\n".join(t for _, t in f["body"]):
            body = "\n".join(t for _, t in f["body"])
            m = re.search(r"SetVariables\(\s*(\{.*\})\s*(?:,\s*(?:true|false)\s*)?\)", body, re.S)
            if not m:
                return None, {}, "SetVariables({...}) call not found in §3"
            lines = {}
            for ln, t in f["body"]:
                mm = re.match(r'^\s*"([^"]+)"\s*:', t)
                if mm:
                    lines.setdefault(mm.group(1), ln)
            try:
                data = js_to_json(m.group(1))
            except Exception as e:  # noqa
                return None, lines, "cannot parse SetVariables object: %s" % e
            return data, lines, None
    return None, {}, "no SetVariables js block in §3"


# ---------------------------------------------------------------- colour math
def hex_rgb(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    h = h[:6]
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def luminance(h):
    def ch(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(c) for c in hex_rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def var_by_mode(var):
    """{mode: value} for a colour variable ('*' when not themed)."""
    v = var.get("value")
    if isinstance(v, list):
        out = {}
        for e in v:
            th = e.get("theme") or {}
            out[th.get("mode", "*")] = e.get("value")
        return out
    return {"*": v}


# ---------------------------------------------------------------- catalogue
def load_catalogue(extra_paths):
    """Return (set of M-xx ids, forbidden set, state-recipe set, source label).

    Base: scripts/data/motion-catalogue.json (single source). --catalogue / --globals extend it
    with any **M-NN** (or `| M-NN |`) rows they define."""
    ids, forb, state, src = set(), {"M-17"}, set(), []
    base = os.path.join(HERE, "data", "motion-catalogue.json")
    if os.path.isfile(base):
        rec = json.load(open(base, encoding="utf-8")).get("recipes", {})
        ids |= {k for k in rec if re.match(r"^M-\d\d$", k)}
        forb |= {k for k, v in rec.items() if isinstance(v, dict) and v.get("forbidden")}
        state |= {k for k, v in rec.items() if isinstance(v, dict) and v.get("stateHint")}
        src.append("motion-catalogue.json")
    for p in extra_paths:
        if not p or not os.path.isfile(p):
            continue
        txt = open(p, encoding="utf-8").read()
        if p.endswith(".json"):
            d = json.loads(txt)
            rec = d.get("recipes", d)
            ids |= {k for k in rec if re.match(r"^M-\d\d$", k)}
            forb |= {k for k, v in rec.items() if isinstance(v, dict) and v.get("forbidden")}
            state |= {k for k, v in rec.items() if isinstance(v, dict) and v.get("stateHint")}
        else:
            ids |= set(re.findall(r"\*\*(M-\d\d)\*\*", txt))
            ids |= set(re.findall(r"^\|\s*`?(M-\d\d)`?\s*\|", txt, re.M))
        src.append(os.path.basename(p))
    if not ids:
        return {"M-%02d" % i for i in range(1, 29)}, forb, STATE_RECIPES_DEFAULT, "built-in M-01..M-28"
    return ids, forb, state or STATE_RECIPES_DEFAULT, "+".join(src)


# ---------------------------------------------------------------- plan model
class Plan:
    def __init__(self, path, text):
        self.path = path
        self.md = MD(text)
        m = CONTRACT_RE.search("\n".join(self.md.lines[:6]))
        self.marker_contract = int(m.group(1)) if m else None
        self.marker_line = None
        for i, l in enumerate(self.md.lines, 1):
            if CONTRACT_RE.search(l):
                self.marker_line = i
                break
        self.components = collections.OrderedDict()   # name -> (line, rowtext, states)
        self.entries = collections.OrderedDict()      # key -> dict(kind, line, end, props, tree_lines)
        self.targets = []
        self.blocks = []
        self._parse()

    def _parse(self):
        md = self.md
        r61 = md.section("6.1", 3)
        self.r61 = r61
        if r61:
            for t in md.tables(r61):
                if t["header"] and t["header"][0].lower().startswith(("bileşen", "component")):
                    for ln, cells in t["rows"]:
                        mm = re.match(r"^`([A-Za-z]\w*)`", cells[0]) if cells else None
                        if mm:
                            self.components[mm.group(1)] = (ln, md.lines[ln - 1], cells[2] if len(cells) > 2 else "")
        for idx, (ln, lv, tx) in enumerate(md.heads):
            mm = re.match(r"^(Section|Overlay)/([A-Za-z]\w*)$", tx)
            if lv == 4 and mm:
                a, b = md.heading_range(idx)
                props = None
                only, only_states = [], []
                for k in range(a, b):
                    if props is None and re.match(r"^- \*\*Prop", md.lines[k - 1]):
                        props = (k, md.lines[k - 1])
                    if md.lines[k - 1].startswith("- **Yalnız masaüstü katmanlar:**"):
                        only = re.findall(r"`([^`]+)`", md.lines[k - 1])
                    if md.lines[k - 1].startswith("- **Yalnız masaüstü durumlar:**"):
                        only_states = re.findall(r"`([^`]+)`", md.lines[k - 1])
                trees = [f for f in md.fences if a < f["start"] < b and f["lang"] == ""]
                self.entries[mm.group(2)] = dict(kind=mm.group(1), line=ln, end=b, props=props, trees=trees,
                                                 desktop_only=only, desktop_only_states=only_states)
        # anim-target blocks
        for i, l in enumerate(md.lines, 1):
            if "<!-- anim-targets:start -->" in l and i not in md.in_fence:
                f = next((f for f in md.fences if f["start"] > i), None)
                end_marker = next((j for j in range(i + 1, len(md.lines) + 1)
                                   if "<!-- anim-targets:end -->" in md.lines[j - 1] and j not in md.in_fence), None)
                ok = f is not None and f["lang"] == "yaml" and end_marker is not None and f["end"] < end_marker
                owner = None
                for key, e in self.entries.items():
                    if e["line"] < i < e["end"]:
                        owner = key
                in61 = bool(self.r61 and self.r61[0] < i < self.r61[1])
                blk = dict(line=i, fence=f if ok else None, owner=owner, in61=in61, end_marker=end_marker)
                self.blocks.append(blk)
                if ok:
                    items, errs = parse_targets_block(f["body"])
                    blk["errs"] = errs
                    blk["items"] = items
                    raw = "\n".join(t for _, t in f["body"])
                    blk["yaml_error"] = None
                    if yaml is not None and not errs:  # supplementary; subset errors win (stable output)
                        try:
                            yaml.safe_load(raw)
                        except Exception as e:  # noqa
                            blk["yaml_error"] = str(e).split("\n")[0]
                    for it in items:
                        it["_block"] = blk
                        self.targets.append(it)

    # helpers -----------------------------------------------------
    def prefix_guess(self):
        m = re.search(r"`([A-Z])/DS/Colors`", self.md.text)
        if m:
            return m.group(1)
        c = collections.Counter(str(t.get("id", ""))[:1] for t in self.targets if t.get("id"))
        return c.most_common(1)[0][0] if c else None

    def slug_guess(self):
        m = re.search(r'metadata:\s*\{type:"([a-z0-9-]+)"', self.md.text)
        return m.group(1) if m else None

    def reference_host(self):
        for l in self.md.lines[:8]:
            m = re.search(r"https?://([^/\s)`]+)", l)
            if m:
                return m.group(1)
        return None

    def local_recipes(self, P):
        rng = self.md.section("5.1", 3)
        txt = self.md.text_range(rng) if rng else ""
        return set(re.findall(r"\*\*(%s-M-\d\d)\*\*" % re.escape(P or "X"), txt)), set(
            re.findall(r"\*\*([A-Z]-M-\d\d)\*\*", txt))

    def pages(self):
        """[(line, page_name, [(section_name, raw)], expanded_names)]"""
        rng = self.md.section("6.3", 3)
        out = []
        if not rng:
            return out
        for t in self.md.tables(rng):
            for ln, cells in t["rows"]:
                if len(cells) < 2:
                    continue
                m = re.match(r"^`([^`]+)`", cells[0])
                name = m.group(1) if m else cells[0]
                secs = []
                body = cells[1]
                extras = re.findall(r"\(\s*\+\s*([A-Z]\w*)[^)]*\)", body)
                body = re.sub(r"\([^)]*\)", "", body)
                for part in body.split("·"):
                    p = part.strip().strip("`")
                    if p:
                        secs.append(p)
                secs += extras
                out.append((ln, name, secs, expand_page(name)))
        return out


AUTH_DEFAULT = ["Login", "Register", "ForgotPassword", "RecoverPassword"]


def expand_page(name):
    """'Auth (×4)' -> 4 page names; 'Auth (×2: Login, Register)' -> those names."""
    m = re.match(r"^\s*([A-Za-z]\w*)\s*\(\s*[×x](\d+)\s*(?::\s*([^)]*))?\)\s*$", name)
    if not m:
        return [name.strip()]
    base, n, names = m.group(1), int(m.group(2)), m.group(3)
    if names:
        lst = [x.strip() for x in re.split(r"[,·/]", names) if x.strip()]
        if lst:
            return lst
    if base.lower() == "auth" and n == 4:
        return list(AUTH_DEFAULT)
    return ["%s%d" % (base, i) for i in range(1, n + 1)]


def word_in(layer, text):
    return re.search(r"(?<![\w-])" + re.escape(layer) + r"(?![\w-])", text) is not None


def impl_terms(impl):
    """Split an impl string into (known, forbidden, unknown) term lists."""
    s = re.sub(r"[()]", " ", impl)
    words = [w for w in re.split(r"\s+|\s*\+\s*", s) if w]
    known, forb, unk = [], [], []
    for w in words:
        lw = w.lower()
        if w in IMPL_VOCAB:
            known.append(w)
        elif lw in IMPL_FORBIDDEN or lw.startswith("gsap") or lw.startswith("lenis"):
            forb.append(w)
        elif lw in IMPL_FILLER or not re.match(r"^[A-Za-z][\w-]*$", w) or re.search(r"[^\x00-\x7f]", w):
            continue
        else:
            unk.append(w)
    return known, forb, unk


# ---------------------------------------------------------------- plan checks
def lint_plan(plan, args, rep, cat):
    md = plan.md
    contract = args.contract or plan.marker_contract or 1
    P = args.prefix or plan.prefix_guess()
    cat_ids, cat_forbidden, state_recipes, _cat_src = cat

    # L01 ------------------------------------------------------------------
    if md.unclosed:
        rep.add("§-", "ERROR", loc_of("fence", md.unclosed["start"]), "L01", "unclosed code fence")
    for i, l in enumerate(md.lines, 1):
        for ph in re.findall(r"@@\w+@@|\{\{\s*\w+\s*\}\}|__[A-Z]+__|<TODO>|TODO:", l):
            rep.add("§-", "ERROR", loc_of(ph, i), "L01", "leftover placeholder %s" % ph)
    for b in plan.blocks:
        if b["fence"] is None:
            rep.add("§6", "ERROR", loc_of("anim-targets", b["line"]), "L01",
                    "anim-targets:start not followed by a ```yaml fence and a matching anim-targets:end")
    n_start = sum(1 for i, l in enumerate(md.lines, 1) if "<!-- anim-targets:start -->" in l and i not in md.in_fence)
    n_end = sum(1 for i, l in enumerate(md.lines, 1) if "<!-- anim-targets:end -->" in l and i not in md.in_fence)
    if n_start != n_end:
        rep.add("§6", "ERROR", "-", "L01", "anim-targets markers unpaired (%d start, %d end)" % (n_start, n_end))
    if plan.marker_line and plan.marker_line != 2:
        rep.add("§0", "WARN", loc_of("marker", plan.marker_line), "L01", "contract marker should be on line 2")
    if args.contract and plan.marker_contract and args.contract != plan.marker_contract:
        rep.add("§0", "WARN", "-", "L01", "--contract %d overrides marker contract:%d" % (args.contract, plan.marker_contract))

    # L02 ------------------------------------------------------------------
    for b in plan.blocks:
        for ln, e in b.get("errs", []):
            rep.add("§6", "ERROR", loc_of("yaml", ln), "L02", e)
        if b.get("yaml_error"):
            rep.add("§6", "ERROR", loc_of("yaml", b["fence"]["start"]), "L02", "PyYAML: %s" % b["yaml_error"])
    for t in plan.targets:
        tid = t.get("id") or "?"
        for k in REQ_KEYS:
            if k not in t:
                rep.add("§6", "ERROR", loc_of(tid, t["_line"]), "L02", "missing key '%s'" % k)
        for k in t:
            if not k.startswith("_") and k not in REQ_KEYS and k not in OPT_KEYS:
                rep.add("§6", "WARN", loc_of(tid, t["_lines"].get(k)), "L02", "unknown key '%s'" % k)
        if "done" in t and not isinstance(t["done"], bool):
            rep.add("§6", "ERROR", loc_of(tid, t["_lines"].get("done")), "L02", "done must be true|false, got %r" % t["done"])
        trig = t.get("trigger")
        if isinstance(trig, str):
            bad = [x.strip() for x in trig.split("|") if x.strip() not in TRIGGERS]
            if bad:
                rep.add("§6", "WARN", loc_of(tid, t["_lines"].get("trigger")), "L02", "unknown trigger %s" % ", ".join(bad))

    # L03 ------------------------------------------------------------------
    id_re = re.compile(r"^%s-(CMP|[A-Z]{2,5})-\d\d$" % re.escape(P or "[A-Z]"))
    seen = {}
    codes = collections.defaultdict(set)
    for t in plan.targets:
        tid = t.get("id")
        if not isinstance(tid, str):
            continue
        if tid in seen:
            rep.add("§6", "ERROR", loc_of(tid, t["_line"]), "L03", "duplicate id (first at L%d)" % seen[tid])
        else:
            seen[tid] = t["_line"]
        if not id_re.match(tid):
            rep.add("§6", "ERROR", loc_of(tid, t["_line"]), "L03",
                    "id does not match ^%s-(CMP|[A-Z]{2,5})-\\d\\d$" % (P or "<P>"))
        sec = t.get("section")
        if isinstance(sec, str) and not sec.startswith("Sub/"):
            codes[sec].add(tid.rsplit("-", 1)[0])
    for sec, cs in codes.items():
        if len(cs) > 1:
            rep.add("§6", "WARN", sec, "L03", "section uses several id codes: %s" % ", ".join(sorted(cs)))

    # L04 ------------------------------------------------------------------
    local, any_local = plan.local_recipes(P)
    for x in sorted(any_local - local):
        rep.add("§5.1", "ERROR", x, "L04", "local recipe id must use the plan prefix %s-M-NN" % P)
    for t in plan.targets:
        rec = t.get("recipe")
        tid = t.get("id") or "?"
        if not isinstance(rec, str):
            continue
        ln = t["_lines"].get("recipe")
        if rec in cat_forbidden:
            rep.add("§6", "ERROR", loc_of(tid, ln), "L04", "%s is forbidden (Lenis / not portable to ikas)" % rec)
        elif re.match(r"^M-\d\d$", rec):
            if rec not in cat_ids:
                rep.add("§6", "ERROR", loc_of(tid, ln), "L04", "recipe %s not in catalogue" % rec)
        elif re.match(r"^[A-Z]-M-\d\d$", rec):
            if rec not in local:
                rep.add("§6", "ERROR", loc_of(tid, ln), "L04", "local recipe %s not defined in §5.1" % rec)
        else:
            rep.add("§6", "ERROR", loc_of(tid, ln), "L04", "recipe %r is neither M-NN nor %s-M-NN" % (rec, P))

    # L05 / L06 / L07 ------------------------------------------------------
    for t in plan.targets:
        tid = t.get("id") or "?"
        sec, layer = t.get("section"), t.get("layer")
        if not isinstance(sec, str):
            continue
        if sec.startswith("Sub/"):
            name = sec[4:]
            if name not in plan.components:
                rep.add("§6.1", "ERROR", loc_of(tid, t["_line"]), "L05", "component %s not in §6.1 table" % name)
                continue
            if not t["_block"]["in61"]:
                rep.add("§6", "WARN", loc_of(tid, t["_line"]), "L05", "Sub/ target outside the §6.1 block")
            hay = plan.components[name][1]
            where = "§6.1 row %s" % name
        else:
            if sec not in plan.entries:
                rep.add("§6.2", "ERROR", loc_of(tid, t["_line"]), "L05", "section %s has no #### Section/ or Overlay/ heading" % sec)
                continue
            if t["_block"]["owner"] != sec:
                rep.add("§6.2", "ERROR", loc_of(tid, t["_line"]), "L05",
                        "target of %s sits in the block of %s" % (sec, t["_block"]["owner"]))
            hay = "\n".join(l for f in plan.entries[sec]["trees"] for _, l in f["body"])
            where = "%s/%s tree" % (plan.entries[sec]["kind"], sec)
        if isinstance(layer, str) and not word_in(layer, hay):
            rep.add("§6.2", "ERROR", loc_of(tid, t["_lines"].get("layer")), "L06", "layer '%s' not found in %s" % (layer, where))
        via = t.get("via")
        if via is not None and via not in plan.components:
            rep.add("§6.2", "ERROR", loc_of(tid, t["_lines"].get("via")), "L07", "via '%s' is not a §6.1 component" % via)

    # L08 ------------------------------------------------------------------
    for t in plan.targets:
        impl = t.get("impl")
        tid = t.get("id") or "?"
        if not isinstance(impl, str):
            continue
        known, forb, unk = impl_terms(impl)
        ln = t["_lines"].get("impl")
        if forb:
            rep.add("§6", "ERROR", loc_of(tid, ln), "L08", "forbidden library in impl: %s" % ", ".join(forb))
        if unk:
            rep.add("§6", "WARN", loc_of(tid, ln), "L08", "impl term not in vocabulary: %s" % ", ".join(unk))
        if not known and not forb and not unk:
            rep.add("§6", "ERROR", loc_of(tid, ln), "L08", "impl has no known term: %r" % impl)

    # L09 ------------------------------------------------------------------
    lint_section7(plan, rep)

    # L10 ------------------------------------------------------------------
    lint_section65(plan, rep, local | state_recipes)

    # L11-L14 --------------------------------------------------------------
    lint_variables(plan, rep, contract)

    # L15 / L16 / L17 ------------------------------------------------------
    for key, e in plan.entries.items():
        for f in e["trees"]:
            for ln, l in f["body"]:
                toks = NOTATION_RE.findall(l)
                for name, typ in toks:
                    if name == "data":
                        if not DATA_SRC_RE.match(typ):
                            rep.add("§6.2", "WARN", loc_of(key, ln), "L15", "{data:%s}: source should look like product.name" % typ)
                    elif name == "code":
                        if not CODE_NAME_RE.match(typ):
                            rep.add("§6.2", "ERROR", loc_of(key, ln), "L15", "{code:%s}: invalid name" % typ)
                    else:
                        if not CAMEL_RE.match(name):
                            rep.add("§6.2", "ERROR", loc_of(key, ln), "L15", "{%s:%s}: prop name must be camelCase" % (name, typ))
                        if typ not in PROP_TYPES:
                            rep.add("§6.2", "ERROR", loc_of(key, ln), "L15", "{%s:%s}: %s is not an ikas prop type" % (name, typ, typ))
                if contract >= 2 and QUOTED_RE.search(l) and not toks:
                    lit = QUOTED_RE.search(l).group(0)
                    rep.add("§6.2", "ERROR", loc_of(key, ln), "L16",
                            "unmarked literal %s: add {name:TYPE}, {data:source} or {code:name}" % lit[:40])
        if e["props"]:
            ln, l = e["props"]
            for typ in re.findall(r"`[A-Za-z]\w*`(?:\s*,\s*`[A-Za-z]\w*`)*\s+([A-Z][A-Z_]+)\b", l):
                if typ not in PROP_TYPES:
                    rep.add("§6.2", "ERROR", loc_of(key, ln), "L15", "Prop'lar: %s is not an ikas prop type" % typ)
            for nm in re.findall(r"`([^`]+)`(?=(?:\s*,\s*`[^`]+`)*\s+[A-Z][A-Z_]+\b)", l):
                if not CAMEL_RE.match(nm):
                    rep.add("§6.2", "WARN", loc_of(key, ln), "L15", "Prop'lar: prop name '%s' is not camelCase" % nm)
        if contract >= 2 and e["kind"] == "Section":
            if not e["props"]:
                rep.add("§6.2", "ERROR", loc_of("Section/" + key, e["line"]), "L17", "no Prop'lar line (backgroundColor COLOR required)")
            elif not re.search(r"`backgroundColor`\s+COLOR\b|`backgroundColor`[^·]*\bCOLOR\b", e["props"][1]):
                rep.add("§6.2", "ERROR", loc_of("Section/" + key, e["props"][0]), "L17", "Prop'lar line lacks `backgroundColor` COLOR")
        if contract >= 2 and not e["trees"]:
            rep.add("§6.2", "WARN", loc_of(e["kind"] + "/" + key, e["line"]), "L16", "no layer tree")

    # L18 ------------------------------------------------------------------
    pages = plan.pages()
    if not pages:
        rep.add("§6.3", "ERROR", "-", "L18", "no page table in §6.3")
    used = set()
    for ln, name, secs, _exp in pages:
        for s in secs:
            used.add(s)
            e = plan.entries.get(s)
            if e is None:
                rep.add("§6.3", "ERROR", loc_of(name, ln), "L18", "'%s' is not a §6.2 Section" % s)
            elif e["kind"] != "Section":
                rep.add("§6.3", "ERROR", loc_of(name, ln), "L18", "'%s' is an Overlay; pages hold Section refs only" % s)
    for key, e in plan.entries.items():
        if e["kind"] == "Section" and pages and key not in used:
            rep.add("§6.3", "WARN", loc_of("Section/" + key, e["line"]), "L18", "section not used on any page")

    # L19 ------------------------------------------------------------------
    if contract >= 2:
        r60 = md.section("6.0", 3)
        t60 = md.text_range(r60) if r60 else ""
        for ds in DS_C2:
            if "%s/DS/%s" % (P, ds) not in t60:
                rep.add("§6.0", "ERROR", "%s/DS/%s" % (P, ds), "L19", "DS frame missing from §6.0")
        if "Button" not in plan.components:
            rep.add("§6.1", "ERROR", "Button", "L19", "Button component missing")
        else:
            st = plan.components["Button"][2].lower()
            for w in ("eklendi", "stok yok"):
                if w not in st:
                    rep.add("§6.1", "ERROR", loc_of("Button", plan.components["Button"][0]), "L19", "Button states lack '%s'" % w)
        if "FilterDrawer" not in plan.entries or plan.entries["FilterDrawer"]["kind"] != "Overlay":
            rep.add("§6.2", "ERROR", "Overlay/FilterDrawer", "L19", "#### Overlay/FilterDrawer missing")
        if "QuickBuy" not in plan.entries or plan.entries["QuickBuy"]["kind"] != "Overlay":
            rep.add("§6.2", "ERROR", "Overlay/QuickBuy", "L19", "#### Overlay/QuickBuy missing")
        lint_merchant_blocks(plan, rep)
    return contract, P


MERCHANT_LAYERS = collections.OrderedDict([
    ("ProductDetail", ["pdp-rating", "pdp-campaign", "pdp-offers", "pdp-pay", "pdp-bundle", "pdp-tiers",
                       "pdp-options", "pdp-group", "pdp-back-in-stock"]),
    ("CartPage", ["cart-adjustments", "coupon-applied", "cart-recommendations"]),
    ("CartDrawer", ["drawer-adjustments", "coupon-toggle", "drawer-recommend"]),
    # storefront completeness (06-page-coverage §3c)
    ("ProductList", ["filter-category-list", "filter-swatch-values", "filter-box-values", "filter-range",
                     "filter-range-list", "filter-clear-all"]),
    ("Header", ["announcement-pager"]),
    ("Footer", ["locale-button"]),
    ("MenuOverlay", ["menu-auth"]),
    ("AuthForms", ["social-login", "sms-login", "register-consents"]),
    ("EmailVerification", ["resend-form"]),
    ("Account", ["order-detail", "order-packages", "return-form", "account-settings", "orders-error",
                 "address-card-actions"]),
    ("ProductReviews", ["merchant-reply", "reviews-pagination"]),
])
MERCHANT_LAYERS["ProductDetail"] += ["pdp-video", "pdp-variant-swatches", "pdp-stock-locations",
                                     "option-text", "option-textarea", "option-select", "option-box", "option-swatch",
                                     "option-image", "option-checkbox", "option-color", "option-date", "option-file",
                                     "option-child", "option-limit"]
COMPLETENESS_OVERLAYS = ["CookieBar", "ImagePreview", "LocaleSwitcher"]
ACCOUNT_OVERLAYS = []  # AddressModal, ConfirmModal, Toast, AccountMenu are conditional (asked in intake)
COMPLETENESS_SECTIONS = ["RichText", "OrderTracking"]
COMPLETENESS_SUBS = ["VariantSwatch", "PriceRange", "Skeleton"]
MERCHANT_SUBS = ["OfferCard", "BundleItem", "RatingStars", "ReviewCard"]
CARTLINE_STATES = ["indirimli", "hediye", "set", "kişiselleştirilmiş"]


def lint_merchant_blocks(plan, rep):
    """L21: ikas merchant blocks that every theme draws itself (06-page-coverage.md §3b)."""
    for sec, layers in MERCHANT_LAYERS.items():
        e = plan.entries.get(sec)
        if not e:
            continue
        hay = "\n".join(l for f in e["trees"] for _, l in f["body"])
        for name in layers:
            if not re.search(r"(?<![\w-])" + re.escape(name) + r"(?![\w-])", hay):
                rep.add("§6.2", "ERROR", "%s/%s" % (e["kind"], sec), "L21",
                        "tree lacks `%s` (ikas block, 06-page-coverage §3b/§3c)" % name)
    for sec, e in plan.entries.items():
        hay = "\n".join(l for f in e["trees"] for _, l in f["body"])
        if re.search(r"(?<![\w-])newsletter-[a-z-]+", hay) and not re.search(r"(?<![\w-])newsletter-consent(?![\w-])", hay):
            rep.add("§6.2", "ERROR", "%s/%s" % (e["kind"], sec), "L21",
                    "newsletter form without `newsletter-consent` (06-page-coverage §3c)")
    acc = plan.entries.get("Account")
    if acc:
        hay = "\n".join(l for f in acc["trees"] for _, l in f["body"])
        alt = {"address-form": "AddressModal", "address-delete-confirm": "ConfirmModal", "account-delete-confirm": "ConfirmModal"}
        for name, modal in alt.items():
            if not re.search(r"(?<![\w-])" + re.escape(name) + r"(?![\w-])", hay) and modal not in plan.entries:
                rep.add("§6.2", "ERROR", "Section/Account", "L21",
                        "tree lacks `%s` and there is no %s overlay (06-page-coverage §3c)" % (name, modal))
    if "ProductDetail" not in plan.entries:
        return
    for key in COMPLETENESS_OVERLAYS + (ACCOUNT_OVERLAYS if "Account" in plan.entries else []):
        if key not in plan.entries or plan.entries[key]["kind"] != "Overlay":
            rep.add("§6.2", "ERROR", "Overlay/" + key, "L21", "#### Overlay/%s missing (06-page-coverage §3c)" % key)
    for key in COMPLETENESS_SECTIONS:
        if key not in plan.entries or plan.entries[key]["kind"] != "Section":
            rep.add("§6.2", "ERROR", "Section/" + key, "L21", "#### Section/%s missing (06-page-coverage §3c)" % key)
    for name in COMPLETENESS_SUBS + (["SocialLoginButton"] if "AuthForms" in plan.entries else []):
        if name not in plan.components:
            rep.add("§6.1", "ERROR", name, "L21", "sub `%s` missing (06-page-coverage §3c)" % name)
    if "ProductReviews" not in plan.entries or plan.entries["ProductReviews"]["kind"] != "Section":
        rep.add("§6.2", "ERROR", "Section/ProductReviews", "L21", "#### Section/ProductReviews missing (required with ProductDetail)")
    for name in MERCHANT_SUBS:
        if name not in plan.components:
            rep.add("§6.1", "ERROR", name, "L21", "sub `%s` missing (required with ProductDetail)" % name)
    cli = plan.components.get("CartLineItem")
    if cli:
        st = cli[2].lower()
        for w in CARTLINE_STATES:
            if w not in st:
                rep.add("§6.1", "ERROR", "CartLineItem", "L21", "CartLineItem states lack '%s'" % w)


def lint_section7(plan, rep):
    md = plan.md
    rng = md.section("7", 2)
    if not rng:
        rep.add("§7", "ERROR", "-", "L09", "§7 summary not found")
        return
    txt = md.text_range(rng)
    n = len(plan.targets)
    m = re.search(r"\*\*(\d+)\s+(?:hedef|targets?)\*\*", txt)
    if not m:
        rep.add("§7", "ERROR", "-", "L09", "total line ('Toplam **N hedef**') not found")
    elif int(m.group(1)) != n:
        rep.add("§7", "ERROR", "total", "L09", "§7 says %s targets, blocks hold %d" % (m.group(1), n))
    by_sec = collections.OrderedDict()
    for t in plan.targets:
        by_sec.setdefault(t.get("section"), []).append(t)
    cnt = collections.Counter(t.get("recipe") for t in plan.targets)
    sec_rows, rec_rows = {}, {}
    for tb in md.tables(rng):
        h = [c.lower() for c in tb["header"]]
        if len(h) >= 4 and ("id" in h[3] or "aralı" in h[3] or "range" in h[3]):
            for ln, c in tb["rows"]:
                sec_rows[c[0]] = (ln, c)
        elif len(h) >= 2 and (h[0].startswith("tarif") or h[0].startswith("recipe")):
            for ln, c in tb["rows"]:
                rec_rows[c[0]] = (ln, c)
    for sec, ts in by_sec.items():
        if sec not in sec_rows:
            rep.add("§7", "ERROR", str(sec), "L09", "section missing from §7 table")
            continue
        ln, c = sec_rows[sec]
        if len(c) < 4:
            continue
        if c[1].strip() != str(len(ts)):
            rep.add("§7", "ERROR", loc_of(sec, ln), "L09", "count %s, blocks hold %d" % (c[1], len(ts)))
        recs = {x.strip() for x in c[2].split(",") if x.strip()}
        real = {t.get("recipe") for t in ts}
        if recs != real:
            rep.add("§7", "ERROR", loc_of(sec, ln), "L09", "recipes %s != blocks %s" % (",".join(sorted(recs)), ",".join(sorted(map(str, real)))))
        ids = re.findall(r"`([^`]+)`", c[3])
        if len(ids) == 2 and (ids[0] != ts[0].get("id") or ids[1] != ts[-1].get("id")):
            rep.add("§7", "ERROR", loc_of(sec, ln), "L09", "id range %s…%s != %s…%s" % (ids[0], ids[1], ts[0].get("id"), ts[-1].get("id")))
    for sec in sec_rows:
        if sec not in by_sec:
            rep.add("§7", "ERROR", loc_of(sec, sec_rows[sec][0]), "L09", "§7 row has no targets")
    for rec, k in cnt.items():
        if rec not in rec_rows:
            rep.add("§7", "ERROR", str(rec), "L09", "recipe missing from usage table")
        elif rec_rows[rec][1][1].strip() != str(k):
            rep.add("§7", "ERROR", loc_of(rec, rec_rows[rec][0]), "L09", "usage %s, blocks use %d" % (rec_rows[rec][1][1], k))
    for rec in rec_rows:
        if rec not in cnt:
            rep.add("§7", "ERROR", loc_of(rec, rec_rows[rec][0]), "L09", "usage row for unused recipe")


def lint_section65(plan, rep, state_recipes):
    md = plan.md
    rng = md.section("6.5", 3)
    rows = {}
    if rng:
        for tb in md.tables(rng):
            for ln, c in tb["rows"]:
                if len(c) >= 2:
                    rows[c[0].strip()] = (ln, c)
    else:
        rep.add("§6.5", "WARN", "-", "L10", "§6.5 Motion States not found")
    used_ns = collections.defaultdict(list)
    for t in plan.targets:
        if isinstance(t.get("section"), str) and not t["section"].startswith("Sub/"):
            used_ns[t.get("recipe")].append(t)
    for rec in sorted(r for r in used_ns if r in state_recipes):
        if rec not in rows:
            rep.add("§6.5", "WARN", str(rec), "L10", "state recipe used but no Motion States row")
    all_used = {t.get("recipe") for t in plan.targets}
    for rec, (ln, c) in rows.items():
        if rec not in all_used:
            rep.add("§6.5", "WARN", loc_of(rec, ln), "L10", "Motion States row for an unused recipe")
            continue
        m = re.match(r"^([A-Za-z]\w*)\s*\(`([^`]+)`\)", c[1])
        if not m:
            rep.add("§6.5", "WARN", loc_of(rec, ln), "L10", "example cell should read 'Section (`layer`)'")
            continue
        sec, layer = m.groups()
        if not any(t.get("section") == sec and t.get("layer") == layer and t.get("recipe") == rec for t in plan.targets):
            rep.add("§6.5", "WARN", loc_of(rec, ln), "L10", "no %s target on %s/%s" % (rec, sec, layer))


def lint_variables(plan, rep, contract):
    data, lines, err = parse_setvariables(plan.md)
    if err:
        rep.add("§3", "ERROR", "-", "L11", err)
        return
    core = CORE37 + (EXTRA_C2 if contract >= 2 else [])
    for name in core:
        if name not in data:
            rep.add("§3", "ERROR", name, "L11", "core variable missing (contract %d needs %d)" % (contract, len(core)))
    for name in data:
        if name not in core and not name.startswith("radius-"):
            rep.add("§3", "WARN", loc_of(name, lines.get(name)), "L11", "variable outside the core set")
        elif name.startswith("radius-") and name not in RADIUS_ROLES:
            rep.add("§3", "WARN", loc_of(name, lines.get(name)), "L11",
                    "radius variable outside the roles %s (02 §3)" % ", ".join(RADIUS_ROLES))
    for name, var in data.items():
        ln = lines.get(name)
        if not isinstance(var, dict) or "type" not in var or "value" not in var:
            rep.add("§3", "ERROR", loc_of(name, ln), "L11", "variable needs {type, value}")
            continue
        want = ("color" if name.startswith("color-") else "string" if name.startswith("font-")
                else "number" if re.match(r"^(text|space|size|opacity|radius)-", name) else None)
        if want and var["type"] != want:
            rep.add("§3", "ERROR", loc_of(name, ln), "L11", "type %s, expected %s" % (var["type"], want))
        val = var["value"]
        entries = val if isinstance(val, list) else [{"value": val}]
        axes = set()
        for e in entries:
            for ax, axv in (e.get("theme") or {}).items():
                axes.add(ax)
                if ax == "device" and axv not in ("desktop", "mobile"):
                    rep.add("§3", "ERROR", loc_of(name, ln), "L12", "device axis value %r" % axv)
                if ax == "mode" and axv not in ("light", "dark"):
                    rep.add("§3", "ERROR", loc_of(name, ln), "L12", "mode axis value %r" % axv)
            v = e.get("value")
            if var["type"] == "color" and isinstance(v, str) and not v.startswith("$"):
                if not re.match(r"^#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})$", v):
                    rep.add("§3", "ERROR", loc_of(name, ln), "L12", "invalid hex %r" % v)
                elif len(v) == 9 and name not in ALPHA_OK:
                    rep.add("§3", "ERROR", loc_of(name, ln), "L12", "#RRGGBBAA only allowed on color-scrim / color-transparent")
                if name == "color-transparent" and not (len(v) == 9 and v[-2:] == "00"):
                    rep.add("§3", "ERROR", loc_of(name, ln), "L12", "color-transparent must be #RRGGBB00")
        if re.match(r"^(text|space)-", name) or name == "size-logo":
            if "mode" in axes:
                rep.add("§3", "ERROR", loc_of(name, ln), "L12", "size variable themed by mode; use device")
            if not isinstance(val, list):
                rep.add("§3", "WARN", loc_of(name, ln), "L12", "no device axis (same value on desktop and mobile)")
            else:
                devs = {(e.get("theme") or {}).get("device") for e in val}
                if devs != {"desktop", "mobile"}:
                    rep.add("§3", "ERROR", loc_of(name, ln), "L12", "device axis needs desktop and mobile")
        if name.startswith("color-") and isinstance(val, list):
            if "device" in axes:
                rep.add("§3", "ERROR", loc_of(name, ln), "L12", "colour themed by device; use mode")
            modes = {(e.get("theme") or {}).get("mode") for e in val}
            if modes != {"light", "dark"}:
                rep.add("§3", "ERROR", loc_of(name, ln), "L12", "mode axis needs light and dark")
    themed = [n for n in data if n.startswith("color-") and isinstance(data[n].get("value"), list)]
    flat = [n for n in data if n.startswith("color-") and not isinstance(data[n].get("value"), list)]
    if themed and flat:
        rep.add("§3", "WARN", ",".join(flat)[:80], "L12", "some colours have no mode axis while others do")
    # L13 fonts
    for name, var in data.items():
        if name.startswith("font-") and isinstance(var, dict):
            vals = var["value"] if isinstance(var["value"], list) else [{"value": var["value"]}]
            for e in vals:
                f = e.get("value")
                if f in INVALID_FONTS:
                    rep.add("§3", "ERROR", loc_of(name, lines.get(name)), "L13",
                            "font '%s' is invalid in pen.dev (renders in a fallback face); pick another family" % f)
    # L14 contrast
    def colour_at(name, mo, against=None):
        if "|" in name:
            opts = [c for c in (colour_at(x, mo) for x in name.split("|")) if c]
            if not opts or not against:
                return opts[0] if opts else None
            return max(opts, key=lambda c: contrast(c, against))
        if ">" in name:  # translucent colour composited over an opaque ground
            top_n, ground = name.split(">")
            t, g = colour_at(top_n, mo), colour_at(ground, mo)
            if not (t and g):
                return None
            a = int(t[7:9], 16) / 255.0 if len(t) == 9 else 1.0
            tr, gr = hex_rgb(t), hex_rgb(g)
            return "#" + "".join("%02X" % int(round((a * x + (1 - a) * y) * 255)) for x, y in zip(tr, gr))
        if name not in data:
            return None
        m = var_by_mode(data[name])
        v = m.get(mo, m.get("*"))
        return v if isinstance(v, str) and v.startswith("#") else None

    def modes_of(name):
        out = set()
        for part in re.split(r"[>|]", name):
            if part in data:
                out |= set(var_by_mode(data[part]))
        return out

    for fg, bg, minimum, sev2 in CONTRAST_PAIRS:
        if any(p not in data for p in re.split(r"[>|]", fg + ">" + bg)):
            continue
        modes = sorted(modes_of(fg) | modes_of(bg))
        if len(modes) > 1 and "*" in modes:
            modes.remove("*")
        for mo in modes:
            b = colour_at(bg, mo)
            a = colour_at(fg, mo, b)
            if not (a and b):
                continue
            r = contrast(a, b)
            if r < minimum:
                sev = sev2 if contract >= 2 else "WARN"
                rep.add("§3", sev, "%s/%s%s" % (fg.replace("|", ","), bg, "" if mo == "*" else "@" + mo), "L14",
                        "contrast %.2f < %.1f (%s on %s)" % (r, minimum, a, b))


# ---------------------------------------------------------------- phase-1 docs
def lint_tables(md, rep, sect):
    for tb in md.tables():
        if not tb["sep_ok"]:
            rep.add(sect, "ERROR", loc_of("table", tb["start"]), "L20", "table has no |---| separator row")
            continue
        n = len(tb["header"])
        if tb.get("sep_cells") != n:
            rep.add(sect, "ERROR", loc_of("table", tb["sep_line"]), "L20", "separator has %d cells, header %d" % (tb["sep_cells"], n))
        for ln, c in tb["rows"]:
            if len(c) != n:
                rep.add(sect, "ERROR", loc_of("row", ln), "L20", "row has %d cells, header %d" % (len(c), n))


def lint_globals(path, rep):
    txt = open(path, encoding="utf-8").read()
    md = MD(txt)
    S = "globals"
    if md.unclosed:
        rep.add(S, "ERROR", loc_of("fence", md.unclosed["start"]), "L20", "unclosed code fence")
    lint_tables(md, rep, S)
    for i, l in enumerate(md.lines, 1):
        for ph in re.findall(r"@@\w+@@|\{\{\s*\w+\s*\}\}|__[A-Z]+__|TODO:", l):
            rep.add(S, "ERROR", loc_of(ph, i), "L20", "leftover placeholder")
        for hx in re.findall(r"`(#[0-9A-Fa-f]+)`", l):
            if len(hx) - 1 not in (3, 6, 8):
                rep.add(S, "ERROR", loc_of(hx, i), "L20", "invalid hex")
    h2 = " ".join(t.lower() for _, lv, t in md.heads if lv == 2)
    for topic, words in (("colour", ("renk", "color", "colour")), ("typography", ("tipografi", "typography")),
                         ("spacing", ("boşluk", "spacing")), ("breakpoints", ("kırılım", "breakpoint")),
                         ("motion", ("motion", "hareket"))):
        if not any(w in h2 for w in words):
            rep.add(S, "WARN", "-", "L20", "no H2 section for %s" % topic)
    ids = re.findall(r"\*\*(M-\d\d)\*\*", txt)
    if not ids:
        rep.add(S, "ERROR", "-", "L20", "no motion catalogue rows (**M-NN**)")
    else:
        dup = [k for k, v in collections.Counter(ids).items() if v > 1]
        for d in dup:
            rep.add(S, "ERROR", d, "L20", "catalogue id defined twice")
        nums = sorted(int(x[2:]) for x in set(ids))
        if nums != list(range(1, nums[-1] + 1)):
            rep.add(S, "WARN", "-", "L20", "catalogue ids not contiguous from M-01")
        m17 = re.search(r"^\|\s*\*\*M-17\*\*.*$", txt, re.M)
        if m17 and not re.search(r"lenis|kullanılamaz|forbidden|yasak", m17.group(0), re.I):
            rep.add(S, "WARN", "M-17", "L20", "M-17 row should state it is not usable (Lenis)")
    miss = [n for n in CORE37 if n not in txt]
    if miss:
        rep.add(S, "INFO", "-", "L20", "core names not mentioned: %s" % ", ".join(miss))
    return set(ids)


def lint_components(path, rep):
    txt = open(path, encoding="utf-8").read()
    md = MD(txt)
    S = "components"
    if md.unclosed:
        rep.add(S, "ERROR", loc_of("fence", md.unclosed["start"]), "L20", "unclosed code fence")
    lint_tables(md, rep, S)
    headings = {}
    for idx, (ln, lv, tx) in enumerate(md.heads):
        if lv == 3:
            m = re.match(r"^([A-Z]\w*)", tx)
            if m:
                headings[m.group(1)] = (idx, tx)
    # prop tables + inline Prop lines, per ### heading
    for name, (idx, tx) in headings.items():
        a, b = md.heading_range(idx)
        if re.search(r"overlay|sub-?component", tx, re.I):
            continue
        has_props, has_bg = False, False
        for tb in md.tables((a, b)):
            h = [c.lower() for c in tb["header"]]
            if not h or h[0] != "prop":
                continue
            has_props = True
            ti = next((i for i, c in enumerate(h) if c in ("tip", "type")), 1)
            di = next((i for i, c in enumerate(h) if c.startswith(("varsayılan", "default"))), None)
            for ln, c in tb["rows"]:
                if len(c) <= ti:
                    continue
                typ = re.match(r"^\s*([A-Z][A-Z_]*)", c[ti])
                names = re.findall(r"`([^`]+)`", c[0])
                if "backgroundColor" in names:
                    has_bg = True
                if not typ or typ.group(1) not in PROP_TYPES:
                    rep.add(S, "ERROR", loc_of(name, ln), "L20", "prop type %r not an ikas type" % c[ti][:30])
                    continue
                for nm in names:
                    if not CAMEL_RE.match(nm):
                        rep.add(S, "WARN", loc_of(name, ln), "L20", "prop name '%s' not camelCase" % nm)
                if di is not None and len(c) > di and typ.group(1) in MERCHANT_TYPES and c[di].strip() not in ("", "—", "-"):
                    rep.add(S, "ERROR", loc_of(name, ln), "L20", "merchant-data prop (%s) must not have a default" % typ.group(1))
        for k in range(a, b):
            l = md.lines[k - 1]
            if k in md.in_fence or not re.match(r"^(Prop|Props|Prop'lar)\s*:", l):
                continue
            has_props = True
            if "backgroundColor" in l:
                has_bg = True
            for typ in re.findall(r"`[A-Za-z]\w*`(?:\s*,\s*`[A-Za-z]\w*`)*\s+([A-Z][A-Z_]+)\b", l):
                if typ not in PROP_TYPES:
                    rep.add(S, "ERROR", loc_of(name, k), "L20", "prop type %s not an ikas type" % typ)
        if has_props and not has_bg:
            rep.add(S, "WARN", name, "L20", "section props lack backgroundColor COLOR")
    # §1 page composition
    r1 = md.section("1", 2)
    if r1:
        for tb in md.tables(r1):
            h = [c.lower() for c in tb["header"]]
            si = next((i for i, c in enumerate(h) if "section" in c), None)
            if si is None or si == 0:
                continue
            for ln, c in tb["rows"]:
                if len(c) <= si:
                    continue
                for pt in re.findall(r"\(([^)]*)\)", c[0]):
                    for tok in re.findall(r"\b[A-Z][A-Z_]{2,}\b", pt):
                        if tok not in PAGE_TYPES:
                            rep.add(S, "WARN", loc_of("page", ln), "L20", "unknown ikas page type %s" % tok)
                body = re.sub(r"\([^)]*\)", "", c[si])
                for part in re.split(r"[·,]", body):
                    p = part.strip().strip("`")
                    if re.match(r"^[A-Z][A-Za-z0-9]+$", p) and p not in headings:
                        rep.add(S, "WARN", loc_of(p, ln), "L20", "section in page table has no ### heading")
    else:
        rep.add(S, "WARN", "-", "L20", "§1 page composition not found")


def lint_globals_c2(path, rep):
    """L22: port-ready theme globals (contract 2)."""
    txt = open(path, encoding="utf-8").read()
    md = MD(txt)
    heads = [t.lower() for _, lv, t in md.heads]
    def has(*words):
        return any(any(w in h for w in words) for h in heads)
    if not has("renk şema", "colorscheme", "color scheme"):
        rep.add("globals", "ERROR", "§1a", "L22", "no colour-scheme section (ikas colorScheme: slot → token → value per scheme)")
    if not has("metin stil", "text style"):
        rep.add("globals", "ERROR", "§2a", "L22", "no ikas text-style section")
    elif not re.search(r"^\|.*≥\s?1200.*992.*768.*<\s?768.*\|\s*$", txt, re.M):
        rep.add("globals", "ERROR", "§2a", "L22", "text-style table lacks the four breakpoint columns (≥1200 · 992–1199 · 768–991 · <768)")
    if not has("ara kırılım", "in-between", "intermediate breakpoint"):
        rep.add("globals", "ERROR", "§4a", "L22", "no in-between breakpoint behaviour table (laptop, tablet per section)")


# ---------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("plan", nargs="?")
    ap.add_argument("--globals", dest="globals_md")
    ap.add_argument("--components")
    ap.add_argument("--catalogue")
    ap.add_argument("--contract", type=int, choices=[1, 2])
    ap.add_argument("--prefix")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    if not args.plan and not args.globals_md and not args.components:
        ap.error("give a plan and/or --globals/--components")
    rep = Report()
    if args.globals_md:
        lint_globals(args.globals_md, rep)
    if args.components:
        lint_components(args.components, rep)
    n = 0
    meta = {}
    if args.plan:
        cat = load_catalogue([args.catalogue, args.globals_md])
        if cat[3].startswith("built-in"):
            rep.add("§5", "INFO", "-", "L04", "no catalogue found; using built-in M-01..M-28")
        plan = Plan(args.plan, open(args.plan, encoding="utf-8").read())
        contract, P = lint_plan(plan, args, rep, cat)
        if contract >= 2 and args.globals_md:
            lint_globals_c2(args.globals_md, rep)
        n = len(plan.targets)
        meta = dict(contract=contract, prefix=P, catalogue=cat[3])
    e, w = rep.count("ERROR"), rep.count("WARN")
    final = "LINT OK (%d targets)" % n if e == 0 else "LINT FAIL (%d errors, %d warnings)" % (e, w)
    if args.json:
        print(json.dumps(dict(ok=e == 0, targets=n, errors=e, warnings=w, findings=rep.items,
                              result=final, **meta), ensure_ascii=False, indent=1))
    else:
        for i in rep.items:
            print("%s|%s|%s|%s %s" % (i["sect"], i["sev"], i["loc"], i["check"], i["msg"]))
        print(final)
    return 1 if e else 0


if __name__ == "__main__":
    sys.exit(main())
