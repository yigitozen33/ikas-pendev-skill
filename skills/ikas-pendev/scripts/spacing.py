#!/usr/bin/env python3
"""spacing.py - a theme's spacing system: which token carries each gap role (02-contract.md §3b).

The roles are fixed, so every theme answers the same questions (page edge, header → first section,
section → section, last section → Footer, column split, card grid). The token behind each role is the
theme's choice (plandata theme.json `spacing`), and so is its value: a theme with floating bands can
set pageEdge to its own `space-band` while content keeps `space-page`. A role the theme does not set
falls back to the default below.

gen_plan.py validates and renders the system in plan §3b with a machine-readable block; CHK `spacing`
checks the canvas against it.
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


def resolve(spacing):
    """Role → token name (no `$`), defaults filled in."""
    spacing = spacing or {}
    return collections.OrderedDict((r, spacing.get(r, d)) for r, (d, _) in ROLES.items())


def validate(spacing, numbers, path="$.spacing"):
    """Problems as '<path>: <message>'. numbers: the plandata number variables (dict)."""
    if spacing is None:
        return []
    if not isinstance(spacing, dict):
        return [path + ": expected object"]
    errs = []
    for k, v in spacing.items():
        if k not in ROLES:
            errs.append('%s: unknown role "%s" (roles: %s)' % (path, k, ", ".join(ROLES)))
        elif not (isinstance(v, str) and re.match(r"^[a-z][a-z0-9-]*$", v)):
            errs.append('%s.%s: a number variable name without "$"' % (path, k))
        elif v not in numbers:
            errs.append('%s.%s: "%s" is not in $.variables.numbers' % (path, k, v))
    return errs


def markdown(spacing):
    rows = ["| Rol | Token | Nerede |", "|---|---|---|"]
    for r, tok in resolve(spacing).items():
        rows.append("| `%s` | `$%s` | %s |" % (r, tok, ROLES[r][1]))
    return "\n".join(rows) + "\n"


def block(spacing):
    """The plan block CHK `spacing` reads (extract_targets.py)."""
    roles = {r: "$" + t for r, t in resolve(spacing).items()}
    return "<!-- spacing:start -->\n```json\n" + json.dumps(roles, sort_keys=True) + "\n```\n<!-- spacing:end -->\n"


def from_plan(text):
    """Role → `$token` from a rendered plan, or the defaults when the plan has no block."""
    m = re.search(r"<!-- spacing:start -->\s*```json\n(.*?)\n```\s*<!-- spacing:end -->", text, re.S)
    if m:
        return json.loads(m.group(1))
    return {r: "$" + t for r, t in resolve(None).items()}
