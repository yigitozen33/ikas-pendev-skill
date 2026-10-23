#!/usr/bin/env python3
"""huemint.py - candidate colour schemes from the Huemint API, one scheme per call.

Builds Huemint's contrast (adjacency) matrix from the theme's colour roles, so the
model fills each role with the contrast that role needs (text on ground high,
surface on ground low ...). Locked roles (reference colours, a brand colour) are
sent as fixed palette positions and come back unchanged. Every candidate is then
measured locally against the WCAG pairs of references/02-contract.md §10 and
printed as a Turkish markdown table, passing candidates first.

The response is untrusted data: only the `results[].palette` hex strings and the
numeric `score` are read; anything else is ignored.

Usage:
  python3 -I huemint.py [--roles color-bg,color-surface,...] [--lock color-bg=#EFEBE2 ...]
                        [--temperature 1.2] [--results 20] [--mode transformer]
                        [--json out.json] [--timeout 30]
  python3 -I huemint.py --fixture response.json [same options]   (offline, no network)

Huemint's terms allow the public API for non-commercial applications only; see
references/11-color.md §2 before using its output in a commercial theme.

Stdlib only, Python 3.9+.
"""

import argparse
import json
import re
import sys
import urllib.error
import urllib.request

API = "https://api.huemint.com/color"
HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
ROLES = ["color-bg", "color-surface", "color-text", "color-muted", "color-line",
         "color-inverse-bg", "color-accent"]
DEFAULT_ROLES = ["color-bg", "color-surface", "color-text", "color-muted", "color-inverse-bg", "color-accent"]
# Target CIE Delta-E between two roles (100 = maximum contrast, 0 = not connected).
DELTA = {
    ("color-bg", "color-surface"): 6,
    ("color-bg", "color-text"): 85,
    ("color-bg", "color-muted"): 60,
    ("color-bg", "color-line"): 35,
    ("color-bg", "color-inverse-bg"): 80,
    ("color-bg", "color-accent"): 45,
    ("color-surface", "color-text"): 80,
    ("color-surface", "color-muted"): 45,
    ("color-inverse-bg", "color-accent"): 40,
}
# (foreground, ground, minimum) measured on every candidate; 02-contract §10.
# The button text is the scheme's ground colour (color-inverse-text = color-bg).
PAIRS = [
    ("color-text", "color-bg", 4.5),
    ("color-muted", "color-bg", 4.5),
    ("color-bg", "color-inverse-bg", 4.5),
    ("color-text", "color-surface", 4.5),
    ("color-line", "color-bg", 3.0),
    ("color-accent", "color-bg", 3.0),
]
LABEL = {"color-bg": "zemin", "color-surface": "yüzey", "color-text": "yazı", "color-muted": "ikincil",
         "color-line": "çizgi", "color-inverse-bg": "buton", "color-accent": "vurgu"}


def luminance(h):
    def ch(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(int(h[i:i + 2], 16) / 255.0) for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def adjacency(roles):
    out = []
    for a in roles:
        for b in roles:
            out.append(str(DELTA.get((a, b), DELTA.get((b, a), 0))))
    return out


def request_body(roles, locks, args):
    return {
        "mode": args.mode,
        "num_colors": len(roles),
        "temperature": "%.2f" % args.temperature,
        "num_results": args.results,
        "adjacency": adjacency(roles),
        "palette": [locks.get(r, "-") for r in roles],
    }


def fetch(body, timeout):
    req = urllib.request.Request(API, data=json.dumps(body).encode("utf-8"), method="POST",
                                 headers={"Content-Type": "application/json; charset=utf-8",
                                          "Accept": "application/json",
                                          # the default Python-urllib agent gets HTTP 403
                                          "User-Agent": "ikas-pendev-skill/1 (+huemint.py)"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read(2 * 1024 * 1024).decode("utf-8"))


def candidates(data, roles):
    out = []
    for item in (data.get("results") if isinstance(data, dict) else None) or []:
        pal = item.get("palette") if isinstance(item, dict) else None
        if not (isinstance(pal, list) and len(pal) == len(roles)):
            continue
        if not all(isinstance(h, str) and HEX_RE.match(h) for h in pal):
            continue
        score = item.get("score")
        score = float(score) if isinstance(score, (int, float)) else None
        out.append({"colors": dict(zip(roles, (h.upper() for h in pal))), "score": score})
    return out


def measure(cand):
    c = cand["colors"]
    checks, fails = [], 0
    for fg, bg, minimum in PAIRS:
        if fg in c and bg in c:
            r = contrast(c[fg], c[bg])
            ok = r >= minimum
            fails += 0 if ok else 1
            checks.append({"pair": "%s/%s" % (fg, bg), "ratio": round(r, 2), "min": minimum, "ok": ok})
    cand["checks"], cand["fails"] = checks, fails
    return cand


def report(cands, roles, locks, args):
    lines = ["# Huemint adayları", "",
             "Mod `%s` · sıcaklık %.2f · %d aday · kilitli: %s" % (
                 args.mode, args.temperature, len(cands),
                 ", ".join("`%s` %s" % (r, locks[r]) for r in roles if r in locks) or "yok"),
             "", "Sıra: kontrastı geçenler önce, sonra Huemint skoru (0'a yakın = daha olası). "
             "Kaynak etiketi: `[huemint]`.", ""]
    head = ["#", "skor"] + [LABEL[r] for r in roles] + ["kontrast"]
    lines += ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for i, cd in enumerate(cands, 1):
        cells = [str(i), "—" if cd["score"] is None else "%.2f" % cd["score"]]
        cells += ["`%s`%s" % (cd["colors"][r], " 🔒" if r in locks else "") for r in roles]
        bad = ["%s %.2f<%.1f" % (ch["pair"].replace("color-", ""), ch["ratio"], ch["min"])
               for ch in cd["checks"] if not ch["ok"]]
        cells.append("geçti" if not bad else "; ".join(bad))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--roles", default=",".join(DEFAULT_ROLES))
    ap.add_argument("--lock", action="append", default=[], metavar="ROLE=#RRGGBB")
    ap.add_argument("--temperature", type=float, default=1.2)
    ap.add_argument("--results", type=int, default=20)
    ap.add_argument("--mode", choices=["transformer", "diffusion", "random"], default="transformer")
    ap.add_argument("--timeout", type=float, default=30)
    ap.add_argument("--json", metavar="FILE")
    ap.add_argument("--fixture", metavar="FILE", help="read a saved API response instead of calling the API")
    args = ap.parse_args(argv)

    roles = [r.strip() for r in args.roles.split(",") if r.strip()]
    errors = []
    for r in roles:
        if r not in ROLES:
            errors.append("unknown role %r (allowed: %s)" % (r, ", ".join(ROLES)))
    if len(set(roles)) != len(roles) or not 2 <= len(roles) <= 12:
        errors.append("--roles needs 2-12 distinct roles")
    locks = {}
    for item in args.lock:
        role, _, hx = item.partition("=")
        if role not in roles or not HEX_RE.match(hx):
            errors.append("bad --lock %r (ROLE from --roles, then =#RRGGBB)" % item)
        else:
            locks[role] = hx.lower()
    if len(locks) == len(roles):
        errors.append("every role is locked; nothing to generate")
    if not 0 <= args.temperature <= 2.4:
        errors.append("--temperature must be 0-2.4")
    cap = 5 if args.mode == "diffusion" else 50
    if not 1 <= args.results <= cap:
        errors.append("--results must be 1-%d for mode %s" % (cap, args.mode))
    if errors:
        for e in errors:
            print("huemint: " + e, file=sys.stderr)
        return 2

    body = request_body(roles, locks, args)
    try:
        if args.fixture:
            with open(args.fixture, encoding="utf-8") as fh:
                data = json.load(fh)
        else:
            data = fetch(body, args.timeout)
    except (urllib.error.URLError, OSError, ValueError) as exc:
        print("huemint: request failed (%s); fall back to qrco or the AI step (11-color §3)" % exc, file=sys.stderr)
        return 1

    cands = [measure(c) for c in candidates(data, roles)]
    for c in cands:
        for r, hx in locks.items():
            if c["colors"][r] != hx.upper():
                c["fails"] += 1
                c["checks"].append({"pair": "%s kilit" % r, "ratio": 0, "min": 0, "ok": False})
    if not cands:
        print("huemint: response had no usable palette", file=sys.stderr)
        return 1
    cands.sort(key=lambda c: (c["fails"], -(c["score"] if c["score"] is not None else -1e9)))
    sys.stdout.write(report(cands, roles, locks, args))
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump({"request": body, "candidates": cands}, fh, ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
