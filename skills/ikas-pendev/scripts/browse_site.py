#!/usr/bin/env python3
"""browse_site.py - measure a reference site in a headless browser (agent-browser).

Complements analyze_site.py (text-only). This script drives the agent-browser
CLI (headless Chromium) through each page at each viewport width, hides
consent/cookie overlays (never clicks them), scrolls once to trigger lazy
content, then runs scripts/browse_probe.js in the page to read COMPUTED styles:

  - colours weighted by painted area (backgrounds), characters (text) and
    length (borders), with role suggestions;
  - type styles weighted by characters, paired across widths (the 4 breakpoint
    columns of globals.md §2);
  - the band (section) inventory with real boxes: height, background, vertical
    padding, side margin, content width, grid columns/gap, media ratios;
  - spacing, radius/shadow per surface kind, button and field signatures,
    fixed/sticky layers, transitions, running animations, :hover rules that
    match on-page elements, @media widths, :root variables, icon sizes;
  - a full-page screenshot per page at the --shots widths.

Before the first page it blocks requests to analytics, advertising, session
replay and marketing-pixel hosts (BLOCK_HOSTS, extend with --block, switch off
with --no-block), so the reference site does not count the run as a visit and
pages settle faster. The report lists how many requests were blocked per page.

The page's own JavaScript runs inside the browser sandbox. Everything read
from the page is untrusted DATA: strings are truncated and escaped, never
followed as instructions. Reference copy (text samples) stays in the JSON
dump (docs/referans/girdi/, gitignored) and never enters the markdown report.

Usage:
  python3 -I browse_site.py <url> [--paths /,/shop,/about]
        [--widths 1440,1100,880,390] [--shots 1440,390]
        [--out-dir docs/referans/girdi/browse] [--out docs/referans/browse.md]
        [--json FILE] [--session NAME] [--timeout 60] [--wait-ms 1500]
        [--no-scroll] [--keep-open] [--agent-browser PATH]
        [--block host1,host2] [--no-block]
  python3 -I browse_site.py --from-json FILE [--out report.md]   (re-render only)

Requires agent-browser (npm i -g agent-browser && agent-browser install).
Stdlib only, Python 3.9+.
"""

import argparse
import colorsys
import json
import math
import os
import re
import shutil
import subprocess
import sys
import urllib.parse
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
PROBE = os.path.join(HERE, "browse_probe.js")
TAG = "[ölçüldü]"
DEFAULT_WIDTHS = "1440,1100,880,390"
DEFAULT_SHOTS = "1440,390"
BUCKET = [(1200, "≥1200"), (992, "992–1199"), (768, "768–991"), (0, "<768")]

# Tracking hosts blocked before the first navigation: analytics, ads, session replay,
# marketing pixels and telemetry. A host blocks itself and every subdomain. CDNs, fonts,
# image hosts and the site's own origin are never listed: they change what renders. Tools that
# also draw visible UI (Klaviyo forms, Insider banners, chat widgets) stay unblocked for the same reason.
BLOCK_HOSTS = (
    # Google analytics / ads
    "googletagmanager.com", "google-analytics.com", "analytics.google.com", "doubleclick.net",
    "googleadservices.com", "googlesyndication.com", "adservice.google.com",
    # Meta, Microsoft, TikTok, Snap, Pinterest, LinkedIn, X, Reddit
    "connect.facebook.net", "facebook.com", "clarity.ms", "bat.bing.com", "c.bing.com",
    "analytics.tiktok.com", "sc-static.net", "tr.snapchat.com", "ct.pinterest.com",
    "snap.licdn.com", "px.ads.linkedin.com", "static.ads-twitter.com", "analytics.twitter.com",
    "ads-api.twitter.com", "redditstatic.com", "alb.reddit.com",
    # session replay / product analytics
    "hotjar.com", "hotjar.io", "fullstory.com", "mouseflow.com", "crazyegg.com", "smartlook.com",
    "luckyorange.com", "inspectlet.com", "logrocket.io", "lr-ingest.io", "heapanalytics.com",
    "mixpanel.com", "amplitude.com", "cdn.segment.com", "api.segment.io", "posthog.com",
    "mc.yandex.ru", "mc.yandex.com",
    # marketing pixels, affiliates, retargeting, personalisation popups
    "criteo.com", "criteo.net", "taboola.com", "outbrain.com", "adroll.com", "impactcdn.com",
    "pxf.io", "attn.tv",
    "js.hs-scripts.com", "js.hs-analytics.net", "js.hsadspixel.net",
    # telemetry
    "otlp-http-production.shopifysvc.com", "monorail-edge.shopifysvc.com", "sentry.io",
    "ingest.sentry.io", "js-agent.newrelic.com", "bam.nr-data.net", "browser-intake-datadoghq.com",
    "static.cloudflareinsights.com",
)
# Google serves ad/conversion endpoints from www.google.<tld>; only these paths are blocked.
BLOCK_GOOGLE_PATHS = ("/pagead/", "/ccm/", "/rmkt/", "/ads/", "/adsid/")


class BrowseError(RuntimeError):
    pass


# --------------------------------------------------------------------------- agent-browser

class AB:
    def __init__(self, exe, session, timeout):
        self.exe, self.session, self.timeout = exe, session, timeout

    def run(self, *args, stdin=None, timeout=None):
        cmd = [self.exe, "--session", self.session] + list(args) + ["--json"]
        try:
            p = subprocess.run(cmd, input=stdin, capture_output=True, text=True,
                               timeout=timeout or self.timeout)
        except subprocess.TimeoutExpired:
            raise BrowseError("zaman aşımı (%ss): agent-browser %s" % (timeout or self.timeout, args[0]))
        out = (p.stdout or "").strip()
        try:
            d = json.loads(out.splitlines()[-1]) if out else {}
        except (ValueError, IndexError):
            raise BrowseError("agent-browser %s: JSON olmayan çıktı: %s" % (args[0], short(out or p.stderr, 200)))
        if not d.get("success"):
            err = d.get("error") or p.stderr or out
            if isinstance(err, dict):
                err = err.get("message") or json.dumps(err)[:200]
            raise BrowseError("agent-browser %s: %s" % (args[0], short(str(err), 240)))
        return d.get("data") or {}

    def batch(self, commands, timeout=None):
        """Run [["network", "route", ...], ...] in one call; raise on the first failure."""
        cmd = [self.exe, "--session", self.session, "batch", "--bail", "--json"]
        try:
            p = subprocess.run(cmd, input=json.dumps(commands), capture_output=True, text=True,
                               timeout=timeout or self.timeout)
        except subprocess.TimeoutExpired:
            raise BrowseError("zaman aşımı: agent-browser batch")
        try:
            res = json.loads((p.stdout or "").strip() or "null")
        except ValueError:
            raise BrowseError("agent-browser batch: JSON olmayan çıktı: %s" % short(p.stdout or p.stderr, 200))
        if not isinstance(res, list):
            raise BrowseError("agent-browser batch: %s" % short(json.dumps(res), 200))
        bad = [r for r in res if r.get("error")]
        if bad or len(res) != len(commands):
            raise BrowseError("agent-browser batch: %s" % short(str(bad[0]["error"]) if bad else "eksik sonuç", 200))
        return res

    def js(self, step, opts, probe_src, timeout=None):
        src = "(async () => JSON.stringify(await (%s).%s(%s)))()" % (probe_src, step, json.dumps(opts))
        data = self.run("eval", "--stdin", stdin=src, timeout=timeout)
        res = data.get("result")
        if not isinstance(res, str):
            raise BrowseError("probe %s sonuç döndürmedi" % step)
        return json.loads(res)


# --------------------------------------------------------------------------- helpers

def block_patterns(hosts):
    pats = []
    for h in hosts:
        pats += ["*://%s/*" % h, "*://*.%s/*" % h]
    pats += ["*://www.google.*%s*" % p for p in BLOCK_GOOGLE_PATHS]
    return pats


def is_blocked(url, hosts):
    sp = urllib.parse.urlsplit(url)
    host = (sp.hostname or "").lower()
    if any(host == h or host.endswith("." + h) for h in hosts):
        return host
    if host.startswith("www.google.") and any(sp.path.startswith(p) for p in BLOCK_GOOGLE_PATHS):
        return host
    return None


def short(text, n=70):
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    return text if len(text) <= n else text[: n - 1] + "…"


def cell(x):
    s = re.sub(r"[\x00-\x1f\x7f]", " ", str(x if x is not None else "—"))
    return s.replace("`", "'").replace("|", "\\|").replace("<", "‹").replace(">", "›").strip() or "—"


def code(x):
    return "`%s`" % cell(x) if x not in (None, "", "—") else "—"


def table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    for r in rows:
        out.append("| " + " | ".join(r) + " |")
    return "\n".join(out)


def page_label(path):
    p = urllib.parse.urlsplit(path).path.strip("/")
    return re.sub(r"[^a-z0-9]+", "-", p.lower()).strip("-") or "home"


def bucket(w):
    for lo, name in BUCKET:
        if w >= lo:
            return name
    return "<768"


def hex_rgb(h):
    h = h.lstrip("#")
    if len(h) < 6:
        return None
    try:
        return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    except ValueError:
        return None


def lum(h):
    rgb = hex_rgb(h)
    if not rgb:
        return None
    f = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (f(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = lum(a), lum(b)
    if la is None or lb is None:
        return None
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def sat(h):
    rgb = hex_rgb(h)
    if not rgb:
        return 0, 0
    hh, l, s = colorsys.rgb_to_hls(*rgb)
    return s, l


def dist(a, b):
    ra, rb = hex_rgb(a), hex_rgb(b)
    if not ra or not rb:
        return 1
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(ra, rb)))


def num(v):
    try:
        return float(re.match(r"-?[\d.]+", str(v)).group(0))
    except (AttributeError, ValueError):
        return None


def median(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    m = len(xs) // 2
    return xs[m] if len(xs) % 2 else (xs[m - 1] + xs[m]) / 2


def fmt(x):
    if x is None:
        return "—"
    if isinstance(x, float):
        return ("%.1f" % x).rstrip("0").rstrip(".")
    return str(x)


# --------------------------------------------------------------------------- collect

def collect(args, warnings):
    exe = args.agent_browser or shutil.which("agent-browser")
    if not exe:
        raise SystemExit("error: agent-browser bulunamadı. Kurulum: npm i -g agent-browser && agent-browser install")
    parts = urllib.parse.urlsplit(args.url)
    if parts.scheme not in ("http", "https", "file"):
        raise SystemExit("error: url http(s):// ya da file:// olmalı")
    if parts.scheme == "file":
        pages = [args.url]
    else:
        origin = "%s://%s" % (parts.scheme, parts.netloc)
        pages = []
        for p in ([x for x in args.paths.split(",") if x.strip()] if args.paths else [args.url]):
            u = urllib.parse.urljoin(origin + "/", p.strip()) if args.paths else p
            if urllib.parse.urlsplit(u).netloc != parts.netloc:
                warnings.append("farklı origin, atlandı: %s" % p)
                continue
            pages.append(u)
    widths = [int(w) for w in args.widths.split(",") if w.strip()]
    shots = {int(w) for w in args.shots.split(",") if w.strip()} if args.shots else set()
    probe_src = open(PROBE, encoding="utf-8").read().strip().rstrip(";")
    session = args.session or "ikas-pendev-%d" % os.getpid()
    ab = AB(exe, session, args.timeout)
    shot_dir = os.path.join(args.out_dir, "shots")
    if shots:
        os.makedirs(shot_dir, exist_ok=True)
    runs = []
    hosts = ()
    if not args.no_block:
        hosts = tuple(BLOCK_HOSTS) + tuple(h.strip().lower() for h in (args.block or "").split(",") if h.strip())
    try:
        if hosts:
            ab.run("open")  # launch on about:blank so the routes apply to the first real navigation
            ab.batch([["network", "route", pat, "--abort"] for pat in block_patterns(hosts)])
        for w in sorted(widths, reverse=True):
            h = 900 if w >= 768 else 844
            ab.run("set", "viewport", str(w), str(h))
            for idx, pu in enumerate(pages, 1):
                path = urllib.parse.urlsplit(pu).path or "/"
                if parts.scheme == "file":
                    path = "/" + os.path.basename(path)
                    label = os.path.splitext(path[1:])[0] or "page"
                else:
                    label = page_label(path)
                run = {"url": pu, "path": path, "label": label, "w": w, "errors": []}
                try:
                    ab.run("open", pu, timeout=args.timeout + 15)
                    try:
                        ab.run("wait", "--load", "load", timeout=args.timeout)
                    except BrowseError as exc:
                        run["errors"].append(str(exc))
                    ab.run("wait", str(args.wait_ms))
                    run["prep"] = ab.js("prep", {"scroll": not args.no_scroll}, probe_src, timeout=args.timeout + 60)
                    run["probe"] = ab.js("probe", {}, probe_src, timeout=args.timeout + 60)
                    if w in shots:
                        sp = os.path.join(shot_dir, "%02d-%s-%d.png" % (idx, label, w))
                        ab.run("screenshot", "--full", sp, timeout=args.timeout + 30)
                        run["shot"] = sp
                    if hosts:
                        run["blocked"] = blocked_requests(ab, hosts)
                    print("ok  %s @%d" % (path, w), file=sys.stderr)
                except BrowseError as exc:
                    run["errors"].append(str(exc))
                    warnings.append("%s @%d: %s" % (path, w, exc))
                    print("ERR %s @%d: %s" % (path, w, exc), file=sys.stderr)
                runs.append(run)
    finally:
        if not args.keep_open:
            try:
                ab.run("close", timeout=20)
            except BrowseError:
                pass
    return {"url": args.url, "session": session, "widths": widths, "pages": pages, "runs": runs,
            "blocking": bool(hosts)}


def blocked_requests(ab, hosts):
    """Count requests the routes aborted since the last call, then clear the log."""
    try:
        data = ab.run("network", "requests")
        ab.run("network", "requests", "--clear")
    except BrowseError:
        return None
    reqs = data.get("requests", []) if isinstance(data, dict) else data
    seen = defaultdict(int)
    for r in reqs or []:
        h = is_blocked(r.get("url", ""), hosts)
        if h:
            seen[h] += 1
    return {"n": sum(seen.values()), "hosts": sorted(seen, key=lambda k: -seen[k])}


# --------------------------------------------------------------------------- aggregate

def agg_pct(runs, key):
    """Mean percentage per value across pages, per width."""
    out = defaultdict(lambda: defaultdict(list))
    for r in runs:
        p = r.get("probe")
        if not p:
            continue
        for v, pc in (p.get("colors") or {}).get(key, []):
            out[v][r["w"]].append(pc)
    npages = defaultdict(int)
    for r in runs:
        if r.get("probe"):
            npages[r["w"]] += 1
    res = {}
    for v, byw in out.items():
        res[v] = {w: sum(xs) / npages[w] for w, xs in byw.items()}
    return res


def type_styles(runs, w):
    acc = {}
    tot = 0
    for r in runs:
        if r["w"] != w or not r.get("probe"):
            continue
        for st in r["probe"].get("type") or []:
            k = (st["fam"], st["size"], st["weight"], st["lh"], st["ls"], st["tr"], st.get("fs", ""))
            a = acc.setdefault(k, {"fam": st["fam"], "size": st["size"], "weight": st["weight"], "lh": st["lh"],
                                   "ls": st["ls"], "tr": st["tr"], "fs": st.get("fs", ""), "chars": 0,
                                   "tags": defaultdict(float), "color": defaultdict(float), "pages": set()})
            a["chars"] += st["chars"]
            tot += st["chars"]
            for t, n in st.get("tags") or []:
                a["tags"][t] += n
            if st.get("color"):
                a["color"][st["color"]] += st["chars"]
            a["pages"].add(r["label"])
    for a in acc.values():
        a["pct"] = a["chars"] / (tot or 1) * 100
    return sorted(acc.values(), key=lambda a: -a["chars"])


def tag_sim(a, b):
    ta, tb = a["tags"], b["tags"]
    keys = set(ta) | set(tb)
    sa, sb = sum(ta.values()) or 1, sum(tb.values()) or 1
    return sum(min(ta.get(k, 0) / sa, tb.get(k, 0) / sb) for k in keys)


def pair_type(runs, widths):
    """Pair the widest width's styles with the closest style at every other width."""
    widths = sorted(widths, reverse=True)
    base = [s for s in type_styles(runs, widths[0]) if s["pct"] >= 0.4][:18]
    others = {w: type_styles(runs, w) for w in widths[1:]}
    rows = []
    for s in sorted(base, key=lambda s: (-s["size"], -s["chars"])):
        row = {widths[0]: s}
        for w, cands in others.items():
            best, bs = None, -1
            for c in cands:
                if c["fam"] != s["fam"] or c["weight"] != s["weight"] or c["tr"] != s["tr"]:
                    continue
                if c["size"] > s["size"] * 1.2:
                    continue
                score = 2 * tag_sim(s, c) + (1 - min(1, abs(math.log(c["size"] / s["size"])))) + min(c["pct"], 10) / 20
                if score > bs:
                    best, bs = c, score
            row[w] = best
        rows.append(row)
    return rows


def text_roles(on, family):
    """From {text@bg: share}, pick (text, muted) among texts sitting on the given bg family."""
    m = defaultdict(float)
    for k, p in on.items():
        t, _, b = k.partition("@")
        if b[:7] in family and len(t) == 7:
            m[t] += p
    if not m:
        return None, None, 0
    tot = sum(m.values())
    ref = next(iter(family))
    cands = [(v, p) for v, p in m.items() if p >= 0.1 * tot]
    t0 = max(cands, key=lambda vp: (contrast(vp[0], ref) or 0))[0]
    muted = next(((v, p) for v, p in sorted(m.items(), key=lambda vp: -vp[1])
                  if v != t0 and p >= 0.02 * tot and dist(v, t0) > 0.05 and 2.5 <= (contrast(v, ref) or 0) < 7.5
                  and (contrast(v, ref) or 0) < 0.75 * (contrast(t0, ref) or 0)), None)
    return t0, muted, tot


def roles(bg, text, border, text_on, border_on, canvas):
    """Suggest colour roles from area/char/length shares (desktop)."""
    out = []
    bgs = sorted(((v, p) for v, p in bg.items() if len(v) == 7), key=lambda x: -x[1])
    brd = sorted(border.items(), key=lambda x: -x[1])
    if not bgs:
        return out
    cshare = bg.get(canvas, 0) if canvas else 0
    if canvas and len(canvas) == 7 and cshare >= 10:
        b0 = canvas
        out.append(("color-bg", b0, "sayfa zemini (html/body), boyanan alan %%%s" % fmt(round(cshare, 1))))
    else:
        b0 = bgs[0][0]
        out.append(("color-bg", b0, "en büyük boyanan alan %%%s" % fmt(round(bgs[0][1], 1))))
    light = {b0} | {v for v, p in bgs if (contrast(v, b0) or 9) < 2.2}
    inv = next(((v, p) for v, p in bgs if v != b0 and p >= 1 and (contrast(v, b0) or 0) >= 7), None)
    surf = next(((v, p) for v, p in bgs if v != b0 and p >= 1.5 and dist(v, b0) > 0.015 and (contrast(v, b0) or 9) < 2.2), None)
    if surf:
        out.append(("color-surface", surf[0], "zemine yakın ikinci ton, alan %%%s" % fmt(round(surf[1], 1))))
    if inv:
        out.append(("color-inverse-bg", inv[0], "zıt zemin, alan %%%s, kontrast %s" % (fmt(round(inv[1], 1)), fmt(round(contrast(inv[0], b0), 1)))))
    fam = [b0] + sorted(light - {b0})
    t0, muted, _ = text_roles(text_on, dict.fromkeys(fam))
    if t0:
        out.append(("color-text", t0, "açık zeminlerdeki en yüksek kontrastlı yaygın metin, kontrast %s" % fmt(round(contrast(t0, b0), 1))))
    if muted:
        out.append(("color-muted", muted[0], "açık zeminlerde ikincil metin, kontrast %s" % fmt(round(contrast(muted[0], b0), 1))))
    if inv:
        dark = [inv[0]] + [v for v, p in bgs if v != inv[0] and (contrast(v, inv[0]) or 9) < 2.2 and v not in light]
        it, _, _ = text_roles(text_on, dict.fromkeys(dark))
        if it:
            out.append(("color-inverse-text", it, "zıt zeminlerdeki metin, kontrast %s" % fmt(round(contrast(it, inv[0]), 1))))
    lines = sorted(((k.partition("@")[0], k.partition("@")[2][:7], p) for k, p in border_on.items()
                    if k.partition("@")[2][:7] in light and len(k.partition("@")[0]) == 7
                    and 1.1 <= (contrast(k.partition("@")[0], k.partition("@")[2][:7]) or 0) < 4.5), key=lambda x: -x[2])
    if lines:
        out.append(("color-line", lines[0][0], "açık zemindeki en uzun ince çizgi, uzunluk %%%s" % fmt(round(lines[0][2], 1))))
    elif brd:
        out.append(("color-line", brd[0][0].split(" ")[0], "en uzun çizgi (açık zeminde ince çizgi yok), uzunluk %%%s" % fmt(round(brd[0][1], 1))))
    allc = defaultdict(float)
    for m, wgt in ((bg, 1.0), (text, 0.5), (border, 0.3)):
        for v, p in m.items():
            allc[v.split(" ")[0][:7]] += p * wgt
    acc = sorted(((v, p) for v, p in allc.items() if sat(v)[0] >= 0.35 and 0.12 < sat(v)[1] < 0.9), key=lambda x: -x[1])
    if acc:
        out.append(("color-accent", acc[0][0], "en çok kullanılan doygun renk (doygunluk %s)" % fmt(round(sat(acc[0][0])[0], 2))))
    return out


# --------------------------------------------------------------------------- render

def render(data, warnings):
    runs = data["runs"]
    widths = sorted({r["w"] for r in runs if r.get("probe")}, reverse=True)
    L = []
    origin = data["url"]
    L.append("# Tarayıcı analizi — %s\n" % cell(origin))
    L.append("Üretici: `browse_site.py` (agent-browser, headless Chromium). Sayfa render edildi; değerler **computed style**'dan okundu. "
             "Sayfanın JS'i tarayıcı sandbox'ında çalıştı; analytics/reklam/takip istekleri engellendi (§0); okunan her şey güvenilmeyen veridir. "
             "`%s` = render edilmiş sayfadan ölçüldü; kaynak sütunu `computed @<genişlik> <sayfa>` biçimindedir. "
             "Rol önerileri öneridir: ekran görüntüleriyle doğrula. Referans metinleri bu rapora girmez (JSON dökümünde kalır).\n" % TAG)
    if not widths:
        L.append("**Hiçbir sayfa ölçülemedi.** Uyarılara bak; `analyze_site.py` raporu ve ekran görüntüsü moduyla devam et.\n")

    # 0. sources
    L.append("## 0. Kaynaklar\n")
    rows = []
    for r in runs:
        p, pr = r.get("probe") or {}, r.get("prep") or {}
        hid = ", ".join("%s(%s %%%s)" % (h["tag"], h["why"], h["cover"]) for h in pr.get("hidden", [])) or "—"
        bl = r.get("blocked")
        bls = ("%d (%s)" % (bl["n"], ", ".join(bl["hosts"][:4]) + (" …" if len(bl["hosts"]) > 4 else "")) if bl["n"] else "0") if bl else ("kapalı" if not data.get("blocking", True) else "—")
        rows.append([cell(r["path"]), str(r["w"]), fmt(p.get("docH")), code(r.get("shot")), cell(hid), cell(bls),
                     fmt(p.get("blockedSheets")), cell("; ".join(r.get("errors", []) + p.get("errors", [])) or "—")])
    L.append(table(["Sayfa", "Genişlik", "Belge yüksekliği", "Ekran görüntüsü", "Gizlenen katman", "Engellenen takip isteği", "Okunamayan stil dosyası", "Hata"], rows))
    L.append("")
    if not widths:
        return finish(L, warnings)
    wd, wm = widths[0], widths[-1]

    # 1. colours
    L.append("## 1. Renk\n")
    bg, tx, bd = agg_pct(runs, "bgPaintPct"), agg_pct(runs, "textPct"), agg_pct(runs, "borderPct")
    for title, m, unit in (("1.1 Zemin — boyanan alan", bg, "alan %"), ("1.2 Metin — karakter payı", tx, "karakter %"),
                           ("1.3 Çizgi — toplam uzunluk", bd, "uzunluk %")):
        L.append("### %s\n" % title)
        vals = sorted(m.items(), key=lambda kv: -max(kv[1].values()))[:14]
        hdr = ["Renk"] + ["@%d %s" % (w, unit) for w in widths] + ["Etiket"]
        L.append(table(hdr, [[code(v)] + [fmt(round(byw.get(w, 0), 1)) for w in widths] + [TAG] for v, byw in vals]))
        L.append("")
    grad = defaultdict(float)
    media = {}
    for r in runs:
        p = r.get("probe") or {}
        for g, pc in (p.get("colors") or {}).get("gradients", []):
            grad[g] = max(grad[g], pc)
        if r["w"] == wd and p.get("colors"):
            media[r["path"]] = p["colors"].get("mediaPct")
    L.append("### 1.4 Gradyan ve görsel alan\n")
    L.append("- Görsel (img/video/arka plan görseli) alan payı @%d: %s %s" % (wd, ", ".join("%s %%%s" % (cell(k), fmt(v)) for k, v in media.items()) or "—", TAG))
    if grad:
        for g, pc in sorted(grad.items(), key=lambda kv: -kv[1])[:6]:
            L.append("- %s — alan %%%s %s" % (code(g), fmt(round(pc, 1)), TAG))
    else:
        L.append("- Gradyan yok %s" % TAG)
    L.append("")
    L.append("### 1.5 Rol önerileri (@%d)\n" % wd)
    on = agg_pct(runs, "textOnPct")
    canv = defaultdict(int)
    for r in runs:
        c = ((r.get("probe") or {}).get("colors") or {})
        if r["w"] == wd and c.get("canvas"):
            canv[c["canvas"]] += 1
    canvas = max(canv, key=canv.get) if canv else None
    sugg = roles({v: byw.get(wd, 0) for v, byw in bg.items()}, {v: byw.get(wd, 0) for v, byw in tx.items()},
                 {v: byw.get(wd, 0) for v, byw in bd.items()}, {v: byw.get(wd, 0) for v, byw in on.items()},
                 {v: byw.get(wd, 0) for v, byw in agg_pct(runs, "borderOnPct").items()}, canvas)
    L.append(table(["Rol", "Değer", "Dayanak", "Etiket"], [[code(a), code(b), cell(c), TAG] for a, b, c in sugg]))
    L.append("\nBoş kalan rol (scrim, danger, success, accent-text) render edilmiş sayfada yoksa `globals.md`'de \"referansta yok\" yaz ya da durumu tarayıcıda tetikle (01 §3 adım 5).\n")

    # 2. typography
    L.append("## 2. Tipografi\n")
    L.append("### 2.1 Stil merdiveni (genişlikler arası eşleşme)\n")
    L.append("En geniş ölçümdeki her stil, diğer genişliklerde aynı aile/ağırlık/dönüşümdeki en yakın stile eşlendi (etiket benzerliği + boyut). "
             "`—` = o genişlikte eşi bulunamadı. Kırılım sütunları: %s.\n" % ", ".join("@%d = %s" % (w, bucket(w)) for w in widths))
    pairs = pair_type(runs, widths)
    rows = []
    for row in pairs:
        s = row[wd]
        tags = ", ".join("%s" % t for t, _ in sorted(s["tags"].items(), key=lambda kv: -kv[1])[:3])
        rows.append([cell(s["fam"])] + [("%spx" % fmt(row[w]["size"])) if row.get(w) else "—" for w in widths] +
                    [str(s["weight"]), cell(s["lh"]), cell(s["ls"]), cell((s["tr"] + " " + s["fs"]).strip() or "—"),
                     cell(tags), fmt(round(s["pct"], 1)), TAG])
    L.append(table(["Aile"] + ["@%d" % w for w in widths] + ["Ağırlık", "Satır (×boyut)", "Harf aralığı", "Dönüşüm", "Etiketler", "Pay %% @%d" % wd, "Etiket"], rows))
    L.append("")
    L.append("### 2.2 Aile kullanımı ve yüklenen yüzler\n")
    fam = defaultdict(float)
    for s in type_styles(runs, wd):
        fam[s["fam"]] += s["pct"]
    L.append(table(["Aile", "Karakter %% @%d" % wd, "Etiket"], [[cell(f), fmt(round(p, 1)), TAG] for f, p in sorted(fam.items(), key=lambda kv: -kv[1])[:8]]))
    faces = []
    for r in runs:
        for f in (r.get("probe") or {}).get("fonts") or []:
            if f not in faces:
                faces.append(f)
    L.append("\n- Yüklenen yüzler (document.fonts): %s %s\n" % (", ".join(code(f) for f in faces[:30]) or "—", TAG))

    # 3. bands
    L.append("## 3. Bölümler (render edilmiş band envanteri)\n")
    L.append("Bir band = sayfanın yukarıdan aşağı tam genişlik bloğu. Üst/alt = bandın kenarından ilk/son içeriğe; kenar = sol/sağ içerik boşluğu; "
             "grid = en çok öğeli düzenli satır (sütun × sütun genişliği, ara). Ekran görüntüsündeki konum için `y` sütununu kullan.\n")
    for w in (wd, wm) if wd != wm else (wd,):
        for r in runs:
            p = r.get("probe")
            if r["w"] != w or not p:
                continue
            L.append("### %s @%d\n" % (cell(r["path"]), w))
            rows = []
            for b in p.get("bands") or []:
                g = b.get("grid")
                gs = ("%d×%dpx ara %d%s" % (g["cols"], g["colW"], g["gap"], " kaydırma" if g.get("scroll") else "")) if g else "—"
                if b.get("slider") and g and not g.get("scroll"):
                    gs += " (kaydırma)"
                hd = b.get("head")
                hs = ("%spx/%s %s" % (fmt(hd["size"]), hd["weight"], hd["tag"])) if hd else "—"
                nm = b.get("name") or b.get("cls") or ""
                if nm.startswith("aria-label=") or nm.startswith("data-testid="):
                    nm = nm.split("=", 1)[0]
                rows.append([str(b["i"]), cell(("%s %s" % (b["tag"], nm)).strip()), str(b["y"]), str(b["h"]), code(b.get("bg")),
                             fmt(b.get("mediaCover")), "%s / %s" % (fmt(b.get("padT")), fmt(b.get("padB"))),
                             "%s / %s" % (fmt(b.get("marL")), fmt(b.get("marR"))), fmt(b.get("contentW")), cell(gs),
                             cell(", ".join(k for k, _ in b.get("media") or []) or "—"), cell(hs),
                             cell(" ".join(x for x in (b.get("pos"), ("z" + b["z"]) if b.get("z") else "") if x) or "—")])
            L.append(table(["#", "Band", "y", "Yükseklik", "Zemin", "Görsel %", "Üst / alt", "Kenar sol / sağ", "İçerik gen.", "Grid", "Görsel oranı", "En büyük metin", "Konum"], rows))
            L.append("")

    # 4. spacing
    L.append("## 4. Boşluk ve ölçü\n")
    rows = []
    for w in widths:
        bands = [b for r in runs if r["w"] == w and r.get("probe") for b in r["probe"].get("bands") or []]
        if not bands:
            continue
        inner = [b for b in bands if b["tag"] not in ("header", "footer", "nav")]
        marg = median([b["marL"] for b in inner if b.get("marL") is not None and b.get("mediaCover", 0) < 90])
        cw = max([b["contentW"] for b in inner if b.get("contentW") and b.get("mediaCover", 0) < 90 and b["contentW"] < w - 2] or [None], key=lambda x: x or 0)
        pt = median([b.get("padT") for b in inner]); pb = median([b.get("padB") for b in inner])
        hdr = next((b for b in bands if b["tag"] == "header" or (b["i"] == 1 and b["h"] < 200)), None)
        ft = next((b for b in reversed(bands) if b["tag"] == "footer"), None) or next((b for b in reversed(bands) if b["h"] >= 120), None)
        rows.append([str(w), fmt(marg), fmt(cw), fmt(pt), fmt(pb), fmt(hdr["h"]) if hdr else "—", fmt(ft["padT"]) if ft else "—",
                     "computed @%d (%d band)" % (w, len(bands)), TAG])
    L.append(table(["Genişlik", "Sayfa kenarı (sol, medyan)", "En geniş içerik", "Band üst boşluk (medyan)", "Band alt boşluk (medyan)", "İlk band yüksekliği", "Footer (son band) üst boşluk", "Kaynak", "Etiket"], rows))
    L.append("\nBand içi boşluk, iki band arasındaki görsel mesafeyi verir (ardışık iki bandın alt+üst toplamı = bölüm → bölüm rolü). "
             "Altı boşluk rolünü (`02-contract.md` §3b) bu tablodan ve bölüm tablosundan doldur.\n")
    for w in (wd, wm) if wd != wm else (wd,):
        gaps, pads = defaultdict(int), defaultdict(int)
        for r in runs:
            if r["w"] == w and r.get("probe"):
                for k, n in r["probe"].get("spacing", {}).get("gaps", []):
                    gaps[k] += n
                for k, n in r["probe"].get("spacing", {}).get("pads", []):
                    pads[k] += n
        L.append("### 4.%s Ara (gap) ve iç boşluk @%d\n" % ("1" if w == wd else "2", w))
        L.append(table(["gap", "Kullanım", "Etiket"], [[code(k), fmt(n), TAG] for k, n in sorted(gaps.items(), key=lambda kv: -kv[1])[:12]]))
        L.append("")
        L.append(table(["Yüzey · padding", "Kullanım", "Etiket"], [[code(k), fmt(n), TAG] for k, n in sorted(pads.items(), key=lambda kv: -kv[1])[:12]]))
        L.append("")

    # 5. radius, shadow, controls
    L.append("## 5. Köşe, gölge, kontroller (@%d)\n" % wd)
    def merged(key, w=wd, n=14):
        m = defaultdict(int)
        for r in runs:
            if r["w"] == w and r.get("probe"):
                for k, c in r["probe"].get(key) or []:
                    m[k] += c
        return sorted(m.items(), key=lambda kv: -kv[1])[:n]
    L.append("Yüzey türü: control = buton/buton gibi link, field = form alanı, media = görsel, card = zeminli/çizgili ≥120×80 kutu.\n")
    L.append(table(["Yüzey · radius", "Kullanım", "Etiket"], [[code(k), fmt(n), TAG] for k, n in merged("radius")]))
    L.append("")
    sh = merged("shadow", n=8)
    L.append(table(["Yüzey · gölge", "Kullanım", "Etiket"], [[code(k), fmt(n), TAG] for k, n in sh]) if sh else "- Gölge yok %s" % TAG)
    L.append("\n### 5.1 Buton imzaları\n")
    L.append(table(["yükseklik · zemin · metin · çizgi · radius · font · büyük harf", "Kullanım", "Etiket"], [[code(k), fmt(n), TAG] for k, n in merged("controls", n=10)]))
    L.append("\n### 5.2 Form alanı imzaları\n")
    fl = merged("fields", n=6)
    L.append(table(["imza", "Kullanım", "Etiket"], [[code(k), fmt(n), TAG] for k, n in fl]) if fl else "- Bu sayfalarda form alanı yok.")
    L.append("")

    # 6. layers
    L.append("## 6. Katmanlar (fixed / sticky)\n")
    rows, seen = [], set()
    for r in runs:
        for l in (r.get("probe") or {}).get("layers") or []:
            k = (r["w"], l["tag"], l["cls"], l["pos"])
            if k in seen:
                continue
            seen.add(k)
            rows.append([str(r["w"]), cell("%s %s" % (l["tag"], l["cls"])), cell(l["pos"]), cell(l["top"]), fmt(l["h"]), cell(l["z"]),
                         code(l["bg"]) if l["bg"] else "—", cell(l["blur"] or "—"), TAG])
    L.append(table(["Genişlik", "Öğe", "Konum", "top", "Yükseklik", "z", "Zemin", "backdrop", "Etiket"], rows[:24]) if rows else "- Sabit/yapışkan katman yok.")
    L.append("")

    # 7. motion
    L.append("## 7. Motion (@%d)\n" % wd)
    L.append("### 7.1 Geçişler (transition)\n")
    tr = merged("transitions", n=16)
    L.append(table(["özellik süre eğri", "Öğe", "Etiket"], [[code(k), fmt(n), TAG] for k, n in tr]) if tr else "- Geçiş yok.")
    L.append("\n### 7.2 Çalışan animasyonlar (document.getAnimations)\n")
    an = merged("animations", n=14)
    L.append(table(["ad · süre · eğri · tekrar · gecikme · hedef", "Adet", "Etiket"], [[code(k), fmt(n), TAG] for k, n in an]) if an else "- Ölçüm anında çalışan animasyon yok (kaydırmayla tetiklenenler bitmiş olabilir).")
    L.append("\n### 7.3 Sayfadaki öğelere uyan :hover kuralları\n")
    hv, seenh = [], set()
    for r in runs:
        if r["w"] != wd:
            continue
        for h in (r.get("probe") or {}).get("hover") or []:
            if h["sel"] in seenh:
                continue
            seenh.add(h["sel"])
            hv.append(h)
    hv.sort(key=lambda h: -h["n"])
    L.append(table(["Seçici", "Değişen", "Uyan öğe", "Koşul", "Etiket"], [[code(h["sel"]), code(h["decl"]), str(h["n"]), cell(h.get("media") or "—"), TAG] for h in hv[:24]]) if hv else
             "- Okunabilir stil dosyalarında :hover kuralı yok (çapraz kaynaklı dosyalar okunamaz; `analyze_site.py` raporuna bak).")
    L.append("")

    # 8. breakpoints, vars, icons
    L.append("## 8. Kırılımlar, değişkenler, ikonlar\n")
    mq = merged("mediaQueries", n=16)
    L.append(table(["@media", "Kural bloğu", "Etiket"], [[code(k), fmt(n), TAG] for k, n in mq]) if mq else "- Okunabilir @media kuralı yok.")
    vars_ = {}
    for r in runs:
        if r["w"] == wd:
            for k, v in (r.get("probe") or {}).get("vars") or []:
                vars_.setdefault(k, v)
    L.append("\n- `:root` değişkenleri: %d adet%s %s" % (len(vars_), (" — ilk 30: " + ", ".join("%s=%s" % (code(k), code(v)) for k, v in list(vars_.items())[:30])) if vars_ else "", TAG))
    isz, ist = defaultdict(int), defaultdict(int)
    for r in runs:
        if r["w"] == wd and r.get("probe"):
            ic = r["probe"].get("icons") or {}
            for k, n in ic.get("sizes", []):
                isz[k] += n
            for k, n in (ic.get("style") or {}).items():
                ist[k] += n
    L.append("- İkon boyutları: %s · stil: %s %s\n" % (", ".join("%s (%d)" % (k, n) for k, n in sorted(isz.items(), key=lambda kv: -kv[1])[:6]) or "—",
                                                     ", ".join("%s %d" % (k, n) for k, n in ist.items()) or "—", TAG))
    return finish(L, warnings)


def finish(L, warnings):
    L.append("## 9. Uyarılar\n")
    L.extend("- %s" % cell(w) for w in warnings) if warnings else L.append("- yok")
    L.append("")
    return "\n".join(L)


# --------------------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(description="Measure a reference site's rendered design tokens with agent-browser.")
    ap.add_argument("url", nargs="?", help="page URL (http/https, or file:// for a local fixture page)")
    ap.add_argument("--paths", help="comma-separated paths relative to the URL origin, e.g. /,/shop,/about")
    ap.add_argument("--widths", default=DEFAULT_WIDTHS, help="viewport widths (default %s)" % DEFAULT_WIDTHS)
    ap.add_argument("--shots", default=DEFAULT_SHOTS, help="widths that get a full-page screenshot (default %s; '' for none)" % DEFAULT_SHOTS)
    ap.add_argument("--out-dir", default="docs/referans/girdi/browse", help="screenshots + JSON dump (gitignored folder)")
    ap.add_argument("--out", metavar="FILE", help="write the markdown report here instead of stdout")
    ap.add_argument("--json", metavar="FILE", help="JSON dump path (default <out-dir>/browse.json)")
    ap.add_argument("--from-json", metavar="FILE", help="re-render a report from an earlier JSON dump; no browser")
    ap.add_argument("--session", help="agent-browser session name (default ikas-pendev-<pid>)")
    ap.add_argument("--timeout", type=int, default=60, help="per-command timeout in seconds (default 60)")
    ap.add_argument("--wait-ms", type=int, default=1500, help="extra settle time after load (default 1500)")
    ap.add_argument("--no-scroll", action="store_true", help="do not scroll through the page before measuring")
    ap.add_argument("--keep-open", action="store_true", help="leave the browser session open (for manual state checks)")
    ap.add_argument("--agent-browser", help="path to the agent-browser executable")
    ap.add_argument("--block", metavar="HOSTS", help="extra comma-separated hosts to block (with their subdomains)")
    ap.add_argument("--no-block", action="store_true", help="do not block analytics/ads/tracking requests")
    args = ap.parse_args(argv)
    warnings = []
    if args.from_json:
        data = json.load(open(args.from_json, encoding="utf-8"))
        warnings = data.get("warnings", [])
    else:
        if not args.url:
            ap.error("url is required (or --from-json)")
        data = collect(args, warnings)
        data["warnings"] = warnings
        os.makedirs(args.out_dir, exist_ok=True)
        jp = args.json or os.path.join(args.out_dir, "browse.json")
        with open(jp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=1)
        print("json: %s" % jp, file=sys.stderr)
    report = render(data, warnings)
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(report)
        print("rapor: %s" % args.out, file=sys.stderr)
    else:
        sys.stdout.write(report)
    ok = any(r.get("probe") for r in data["runs"])
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
