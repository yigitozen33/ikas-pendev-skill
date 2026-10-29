#!/usr/bin/env python3
"""spacing.py - a theme's spacing system: which token carries each gap role (02-contract.md §3b).

The roles are fixed, so every theme answers the same questions (page edge, header → first section,
section → section, last section → Footer, column split, card grid). The token behind each role is the
theme's choice (plandata theme.json `spacing`), and so is its value: a theme with floating bands can
set pageEdge to its own `space-band` while content keeps `space-page`. A role the theme does not set
falls back to the default below.

A theme rarely has one inset and one gap everywhere: floating bands sit closer to the edge than plain
sections, a list that continues the hero above it starts closer than an unrelated section. Two maps
say so, so the design is declared rather than forced onto a default:
  edges  "Section" or "Section@device" → token for that section's left/right padding (or "0")
  seams  "Prev>Section", "*>Section", optionally "@device" → token for Section's top padding when it
         follows Prev on a page ("Header>Hero" is the first section; "0" under a transparent Header)

CHK `spacing` does not compare the canvas with any of this. It reads the system from the canvas
(raw numbers and double gaps fail; a token used once where one token dominates warns) and treats an
entry in edges / seams as a documented, intended outlier. The roles are the port's map: which CSS
spacing variable each gap uses.

gen_plan.py validates and renders the system in plan §3b with a machine-readable block; CHK `spacing`
checks the canvas against it; copy_library.py writes it into the copied section skeletons.
Stdlib only, Python 3.9+.
"""

import collections
import json
import re

ROLES = collections.OrderedDict([
    ("pageEdge", ("space-page", "Sayfa kenarı: her bandın yan boşluğu (bölüm, header şeridi ya da kapsülü, hero, footer, paneller)")),
    ("headerGap", ("space-page", "Header → ilk bölüm: ilk bölümün üst iç boşluğu (şeffaf header altında 0)")),
    ("sectionGap", ("space-section", "Bölüm → bölüm: alttaki bölümün üst iç boşluğu; alt iç boşluk 0")),
    ("footerGap", ("space-section", "Son bölüm → footer: footer kökünün üst iç boşluğu (kök şeffaf)")),
    ("split", ("space-page", "Sütun bölmesi: galeri ↔ satın alma, filtre ↔ ızgara, satırlar ↔ özet, menü ↔ panel")),
    ("grid", ("space-grid", "Kart ızgarası ve ray: kartlar, karolar")),
])


MAPS = ("edges", "seams")
DEV = r"(@(desktop|mobile))?"
KEY_RE = {"edges": re.compile(r"^[A-Z][A-Za-z0-9]*" + DEV + "$"),
          "seams": re.compile(r"^(\*|[A-Z][A-Za-z0-9]*)>[A-Z][A-Za-z0-9]*" + DEV + "$")}


def resolve(spacing):
    """Role → token name (no `$`), defaults filled in."""
    spacing = spacing or {}
    return collections.OrderedDict((r, spacing.get(r, d)) for r, (d, _) in ROLES.items())


def declared(spacing):
    """The roles the theme names itself (the rest fall back to the default and are not checked)."""
    return [r for r in ROLES if r in (spacing or {})]


def _val(v):
    return 0 if v == "0" else "$" + v


def validate(spacing, numbers, path="$.spacing"):
    """Problems as '<path>: <message>'. numbers: the plandata number variables (dict)."""
    if spacing is None:
        return []
    if not isinstance(spacing, dict):
        return [path + ": expected object"]
    errs = []
    for m in MAPS:
        mp = spacing.get(m)
        if mp is None:
            continue
        if not isinstance(mp, dict):
            errs.append("%s.%s: expected object" % (path, m))
            continue
        for k, v in mp.items():
            if not KEY_RE[m].match(k):
                errs.append('%s.%s: bad key "%s" (%s)' % (path, m, k, "Section or Section@device" if m == "edges"
                                                           else "Prev>Section, *>Section, optional @device"))
            elif not (v == "0" or (isinstance(v, str) and re.match(r"^[a-z][a-z0-9-]*$", v))):
                errs.append('%s.%s.%s: a number variable name without "$", or "0"' % (path, m, k))
            elif v != "0" and v not in numbers:
                errs.append('%s.%s.%s: "%s" is not in $.variables.numbers' % (path, m, k, v))
    for k, v in spacing.items():
        if k in MAPS:
            continue
        if k not in ROLES:
            errs.append('%s: unknown role "%s" (roles: %s)' % (path, k, ", ".join(ROLES)))
        elif not (isinstance(v, str) and re.match(r"^[a-z][a-z0-9-]*$", v)):
            errs.append('%s.%s: a number variable name without "$"' % (path, k))
        elif v not in numbers:
            errs.append('%s.%s: "%s" is not in $.variables.numbers' % (path, k, v))
    return errs


def markdown(spacing):
    spacing = spacing or {}
    dec = declared(spacing)
    rows = ["| Rol | Token | Nerede |", "|---|---|---|"]
    for r, tok in resolve(spacing).items():
        rows.append("| `%s` | %s | %s |" % (r, "`$%s`" % tok if r in dec else "tanımlanmadı (varsayılan `$%s`)" % tok,
                                             ROLES[r][1]))
    out = "\n".join(rows) + "\n"
    for m, head, what in (("edges", "Bölüm", "yan iç boşluk"), ("seams", "Dikiş", "üst iç boşluk")):
        mp = spacing.get(m) or {}
        if mp:
            out += "\n| %s | Token | |\n|---|---|---|\n" % head
            out += "".join("| `%s` | %s | %s |\n" % (k, "`0`" if v == "0" else "`$%s`" % v, what) for k, v in sorted(mp.items()))
    return out


def block(spacing):
    """The plan block CHK `spacing` reads (extract_targets.py)."""
    spacing = spacing or {}
    data = {"roles": {r: "$" + t for r, t in resolve(spacing).items()}, "declared": declared(spacing)}
    for m in MAPS:
        data[m] = {k: _val(v) for k, v in (spacing.get(m) or {}).items()}
    return "<!-- spacing:start -->\n```json\n" + json.dumps(data, sort_keys=True, ensure_ascii=False) + "\n```\n<!-- spacing:end -->\n"


def from_plan(text):
    """What CHK `spacing` compares: {roles, declared, edges, seams}. A plan without a block declares
    nothing (`none`); an older block (role → token only) counts every role as declared."""
    m = re.search(r"<!-- spacing:start -->\s*```json\n(.*?)\n```\s*<!-- spacing:end -->", text, re.S)
    if not m:
        return {"roles": {r: "$" + t for r, t in resolve(None).items()}, "declared": [], "edges": {}, "seams": {}, "none": True}
    data = json.loads(m.group(1))
    if "roles" not in data:
        data = {"roles": data, "declared": list(data), "edges": {}, "seams": {}}
    return data
