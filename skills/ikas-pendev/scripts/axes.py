#!/usr/bin/env python3
"""axes.py - structural identity of a theme and the similarity gate (references/12-library.md §6–§7).

A theme's axis choices live in `globals.md` §0 "Yapısal kimlik", one row per field:

  | Eksen | Alan | Seçim | Gerekçe |
  |---|---|---|---|
  | A2 | desktop_cols | `3` | … |

`check` validates the table against library/axes.json and compares it with every theme
recorded earlier on this machine:
  ERROR  a field is missing, or a value is not in the axis vocabulary
  ERROR  the theme differs from an earlier theme on fewer than 4 of the 6 structural axes,
         or fewer than 5 of the 9 token axes, or not on typography (B7) and colour strategy (B12)
  WARN   3 or more axes sit on their generic default
  WARN   a forbidden generic font family appears in globals.md
With --plandata (plan phase), it also builds the home page's layout fingerprint: the
sequence of section archetypes (`archetype: "hero:split"` on each plandata section) of
the INDEX page, Header and Footer left out:
  ERROR  an archetype is not in the vocabulary (axes.json `archetypes`)
  ERROR  the normalised edit distance to an earlier theme's home page is below 0.5
  WARN   a home-page section has no archetype (it is left out of the comparison)
`shot` (verify phase) fingerprints the first desktop viewport of the home page from a PNG
export: grey, blurred, an edge-strength grid, so a light and a dark version of one layout
look alike while two different layouts do not. It warns when the picture is closer than
the threshold to an earlier theme's (WARN only: the threshold is not calibrated) and stores
the fingerprint with --record.
`record` stores the theme's choices (and, with --plandata, its home-page fingerprint)
after its plan gate passed, so the next theme is compared with it. An axis differs when
any of its fields differs.

The store holds only slugs, dates and axis values. It lives outside the skill repo
(default ~/.claude/ikas-pendev/fingerprints.json; override with --store or
IKAS_PENDEV_FINGERPRINTS) and is never committed.

Usage:
  python3 -I axes.py check  docs/referans/globals.md --slug <theme-slug> [--plandata docs/pendev/plandata] [--store PATH]
  python3 -I axes.py record docs/referans/globals.md --slug <theme-slug> [--plandata docs/pendev/plandata] [--store PATH]
  python3 -I axes.py shot   docs/pendev/shots/home-desktop.png --slug <theme-slug> [--record] [--store PATH]
  python3 -I axes.py list [--store PATH]

Exit: 0 pass (warnings allowed), 1 errors, 2 bad arguments. Stdlib only, Python 3.9+.
"""

import argparse
import datetime
import glob
import json
import os
import re
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
AXES = os.path.join(os.path.dirname(HERE), "library", "axes.json")
DEFAULT_STORE = os.path.join(os.path.expanduser("~"), ".claude", "ikas-pendev", "fingerprints.json")
ROW = re.compile(r"^\|\s*([AB]\d{1,2})\b[^|]*\|\s*([a-z_]+)\s*\|\s*`([^`]+)`\s*\|")


def load_axes():
    with open(AXES, encoding="utf-8") as f:
        return json.load(f)


def parse_globals(path):
    """§0 table → {axis: {field: value}}; also returns the whole text for the font check."""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    m = re.search(r"^##+\s*0\.?\s.*?$(.*?)(?=^##+\s*\d)", text, re.S | re.M)
    body = m.group(1) if m else ""
    choice = {}
    for line in body.splitlines():
        r = ROW.match(line.strip())
        if r:
            choice.setdefault(r.group(1), {})[r.group(2)] = r.group(3).strip()
    return choice, text, bool(m)


def validate(choice, ax):
    errs = []
    for aid, spec in ax["axes"].items():
        for field, f in spec["fields"].items():
            v = choice.get(aid, {}).get(field)
            if v is None:
                errs.append(f"§0|{aid}.{field} missing ({spec['name']})")
            elif v not in f["values"]:
                errs.append(f"§0|{aid}.{field} `{v}` not in {', '.join(f['values'])}")
    for aid in choice:
        if aid not in ax["axes"]:
            errs.append(f"§0|unknown axis {aid}")
    return errs


def generic_axes(choice, ax):
    out = []
    for aid, spec in ax["axes"].items():
        fields = spec["fields"]
        on = sum(1 for k, f in fields.items() if choice.get(aid, {}).get(k) == f["median"])
        if on * 2 > len(fields) or (len(fields) == 1 and on == 1):
            out.append(aid)
    return out


def differing(a, b, ax, tier):
    return [aid for aid, spec in ax["axes"].items() if spec["tier"] == tier and a.get(aid) != b.get(aid)]


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


def home_layout(pd, ax):
    """INDEX page → (archetype sequence, errors, keys without archetype)."""
    fam = ax["archetypes"]["families"]
    by_key = {s["key"]: s for s in pd.get("sections", [])}
    page = next((p for p in pd.get("pages", []) if p.get("pageType") == "INDEX"), None)
    if not page:
        return [], ["plandata has no INDEX page"], []
    seq, errs, bare = [], [], []
    for tok in page["sections"].split("·"):
        key = re.sub(r"\(.*?\)", "", tok).strip()
        sec = by_key.get(key)
        if not sec or key in ("Header", "Footer") or sec.get("kind") != "section":
            continue
        arch = sec.get("archetype")
        if not arch:
            bare.append(key)
            continue
        f, _, v = arch.partition(":")
        if f not in fam or (fam[f] != ["*"] and v not in fam[f]):
            errs.append(f"{key}: archetype `{arch}` not in the vocabulary")
        seq.append(arch)
    return seq, errs, bare


def edit_distance(a, b):
    if not a and not b:
        return 0.0
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1] / max(len(a), len(b))


def read_png(path):
    """8-bit greyscale/RGB(A) non-interlaced PNG → (width, height, rows of grey values 0–255)."""
    with open(path, "rb") as f:
        data = f.read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path}: not a PNG")
    pos, idat, w = 8, b"", 0
    while pos < len(data):
        n, kind = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + n]
        if kind == b"IHDR":
            w, h, depth, ctype, _, _, inter = struct.unpack(">IIBBBBB", body)
            if depth != 8 or inter or ctype not in (0, 2, 4, 6):
                raise ValueError(f"{path}: only 8-bit non-interlaced PNG is supported")
            bpp = {0: 1, 2: 3, 4: 2, 6: 4}[ctype]
        elif kind == b"IDAT":
            idat += body
        pos += 12 + n
    raw, stride = zlib.decompress(idat), w * bpp
    rows, prev, i = [], bytearray(stride), 0
    for _ in range(h):
        ft, line = raw[i], bytearray(raw[i + 1:i + 1 + stride])
        i += 1 + stride
        for x in range(stride):
            a = line[x - bpp] if x >= bpp else 0
            b = prev[x]
            c = prev[x - bpp] if x >= bpp else 0
            if ft == 1:
                line[x] = (line[x] + a) & 255
            elif ft == 2:
                line[x] = (line[x] + b) & 255
            elif ft == 3:
                line[x] = (line[x] + (a + b) // 2) & 255
            elif ft == 4:
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        prev = line
        if bpp >= 3:
            rows.append([(line[k] * 299 + line[k + 1] * 587 + line[k + 2] * 114) // 1000 for k in range(0, stride, bpp)])
        else:
            rows.append([line[k] for k in range(0, stride, bpp)])
    return w, h, rows


GRID = 24


def shot_hash(path):
    """First viewport (16:10 of the width), area-averaged to GRID×GRID+1, edge strength vs median."""
    w, h, rows = read_png(path)
    vh = min(h, w * 10 // 16)
    cells = [[0.0] * (GRID + 1) for _ in range(GRID)]
    for gy in range(GRID):
        y0, y1 = gy * vh // GRID, max(gy * vh // GRID + 1, (gy + 1) * vh // GRID)
        for gx in range(GRID + 1):
            x0, x1 = gx * w // (GRID + 1), max(gx * w // (GRID + 1) + 1, (gx + 1) * w // (GRID + 1))
            tot = sum(sum(rows[y][x0:x1]) for y in range(y0, y1))
            cells[gy][gx] = tot / ((y1 - y0) * (x1 - x0))
    edges = [abs(r[x + 1] - r[x]) for r in cells for x in range(GRID)]
    for gx in range(GRID + 1):
        edges += [abs(cells[y + 1][gx] - cells[y][gx]) for y in range(GRID - 1)]
    med = sorted(edges)[len(edges) // 2]
    bits = "".join("1" if e > med else "0" for e in edges)
    return "%0*x" % ((len(bits) + 3) // 4, int(bits, 2)), len(bits)


def hash_distance(a, b, n=None):
    """Share of edge cells that differ among the cells either picture has an edge in (Jaccard)."""
    x, y = int(a, 16), int(b, 16)
    union = bin(x | y).count("1")
    return bin(x ^ y).count("1") / union if union else 0.0


def cmd_shot(a, ax):
    try:
        h, n = shot_hash(a.png)
    except (OSError, ValueError, zlib.error) as e:
        print(f"ERROR|shot|{e}")
        return 1
    limit = ax["gate"]["shot_min_distance"]
    close = []
    for slug, rec in sorted(load_store(a.store).items()):
        if slug != a.slug and rec.get("shot") and len(rec["shot"]) == len(h):
            d = hash_distance(h, rec["shot"], n)
            if d < limit:
                close.append(f"'{slug}' {d:.2f}")
    for c in close:
        print(f"WARN|shot|L23 first viewport looks like {c} (need {limit}); change structure, not colour")
    if a.record:
        store = load_store(a.store)
        store.setdefault(a.slug, {"date": datetime.date.today().isoformat(), "axes": {}})["shot"] = h
        os.makedirs(os.path.dirname(os.path.abspath(a.store)), exist_ok=True)
        with open(a.store, "w", encoding="utf-8") as f:
            json.dump(store, f, ensure_ascii=False, indent=2, sort_keys=True)
    print("SHOT OK" if not close else f"SHOT WARN ({len(close)})")
    return 0


def load_store(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def cmd_check(a, ax):
    choice, text, found = parse_globals(a.globals)
    if not found:
        print(f"ERROR|§0|L23 no 'Yapısal kimlik' section in {a.globals}")
        return 1
    errs = validate(choice, ax)
    warns = []
    gen = generic_axes(choice, ax)
    if len(gen) >= ax["gate"]["generic_warn_at"]:
        warns.append(f"§0|L23 {len(gen)} axes on the generic default: {', '.join(gen)}")
    fonts = [f for f in ax["forbidden_fonts"] if re.search(r"\b" + re.escape(f) + r"\b", text)]
    if fonts:
        warns.append(f"§2|L23 generic font family in globals: {', '.join(fonts)}")
    layout = None
    if a.plandata:
        layout, lerrs, bare = home_layout(load_plandata(a.plandata), ax)
        errs += ["§6.3|L23 " + e for e in lerrs]
        if bare:
            warns.append("§6.3|L23 home-page sections without archetype (not compared): " + ", ".join(bare))
    if not errs:
        g = ax["gate"]
        for slug, rec in sorted(load_store(a.store).items()):
            if slug == a.slug:
                continue
            s = differing(choice, rec["axes"], ax, "structural")
            t = differing(choice, rec["axes"], ax, "token")
            why = []
            if len(s) < g["structural_min_diff"]:
                why.append(f"{len(s)}/6 structural axes differ (need {g['structural_min_diff']})")
            if len(t) < g["token_min_diff"]:
                why.append(f"{len(t)}/9 token axes differ (need {g['token_min_diff']})")
            same = [x for x in g["token_must_differ"] if x not in t]
            if same:
                why.append("same " + ", ".join(same))
            prev = rec.get("layout")
            if layout and prev:
                d = edit_distance(layout, prev)
                if d < g["layout_min_distance"]:
                    why.append(f"home page composition distance {d:.2f} (need {g['layout_min_distance']})")
            if why:
                errs.append(f"§0|L23 too close to '{slug}': " + "; ".join(why))
    for e in errs:
        print("ERROR|" + e)
    for w in warns:
        print("WARN|" + w)
    print("AXES OK" if not errs else f"AXES FAIL ({len(errs)} error)")
    return 1 if errs else 0


def cmd_record(a, ax):
    choice, _, found = parse_globals(a.globals)
    errs = validate(choice, ax) if found else ["§0 missing"]
    if errs:
        print("ERROR|" + errs[0] + " (run check first)")
        return 1
    store = load_store(a.store)
    old = store.get(a.slug, {})
    store[a.slug] = {"date": datetime.date.today().isoformat(), "axes": choice}
    if old.get("shot"):
        store[a.slug]["shot"] = old["shot"]
    if a.plandata:
        layout, lerrs, _ = home_layout(load_plandata(a.plandata), ax)
        if lerrs:
            print("ERROR|" + lerrs[0] + " (run check first)")
            return 1
        store[a.slug]["layout"] = layout
    os.makedirs(os.path.dirname(os.path.abspath(a.store)), exist_ok=True)
    with open(a.store, "w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False, indent=2, sort_keys=True)
    print(f"recorded {a.slug} in {a.store} ({len(store)} themes)")
    return 0


def cmd_list(a, ax):
    for slug, rec in sorted(load_store(a.store).items()):
        print(f"{slug}\t{rec.get('date', '')}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("check", "record"):
        p = sub.add_parser(name)
        p.add_argument("globals")
        p.add_argument("--slug", required=True)
        p.add_argument("--plandata", help="plandata dir or file: adds the home-page layout fingerprint")
    p = sub.add_parser("shot")
    p.add_argument("png")
    p.add_argument("--slug", required=True)
    p.add_argument("--record", action="store_true")
    sub.add_parser("list")
    for p in sub.choices.values():
        p.add_argument("--store", default=os.environ.get("IKAS_PENDEV_FINGERPRINTS", DEFAULT_STORE))
    a = ap.parse_args()
    ax = load_axes()
    return {"check": cmd_check, "record": cmd_record, "shot": cmd_shot, "list": cmd_list}[a.cmd](a, ax)


if __name__ == "__main__":
    sys.exit(main())
