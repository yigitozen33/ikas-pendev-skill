#!/usr/bin/env python3
"""sample_catalog.py - the one sample catalogue a theme's canvas shows (plandata theme.json `sampleCatalog`).

Every product the canvas shows (cards, PDP, QuickBuy, cart drawer, cart page, account) takes its name,
brand, image, prices and option limits from this catalogue, and the sample cart's totals are computed
here once. gen_plan.py validates it and renders plan §6.6 with a machine-readable block; CHK `seed`
compares the canvas with it; build_manifest.py lists it in seed-checklist.md so the port seeds the
same products.

Schema (theme.json):
  "sampleCatalog": {
    "currency": "TL",                                   # optional, default TL
    "products": [{"key": "vitc", "name": "C Vitamini 1000 mg", "brand": "Sevgi",
                  "images": ["product-vitamin-c-glass.png"],
                  "variants": [{"name": "30 tablet", "price": 249.9, "compare": 299.9}],
                  "tiers": [{"qty": 2, "price": 229.9}],                       # optional, unit price from qty
                  "options": [{"name": "Hediye notu", "type": "textarea", "limit": 120}]}],   # optional
    "cart": {"lines": [{"product": "vitc", "variant": "30 tablet", "qty": 3}],
             "campaigns": [{"label": "3 al 2 öde", "amount": 229.9}],              # optional
             "coupon": {"code": "SEVGI10", "amount": 50},                          # optional
             "shipping": 0}                                                       # optional
  }

Usage:
  python3 -I sample_catalog.py <plandata dir|file>      prints the catalogue and the cart totals
Exit: 0 valid (or no catalogue), 1 invalid. Stdlib only, Python 3.9+.
"""

import json
import os
import sys


def load(src):
    """sampleCatalog of a plandata directory or single file, or None."""
    path = os.path.join(src, "theme.json") if os.path.isdir(src) else src
    with open(path, encoding="utf-8") as f:
        return json.load(f).get("sampleCatalog")


def money(x, currency="TL"):
    """249.9 → '249,90 TL'; 1234.5 → '1.234,50 TL' (Turkish grouping)."""
    whole, frac = ("%.2f" % round(x + 1e-9, 2)).split(".")
    grouped = "{:,}".format(int(whole)).replace(",", ".")
    return "%s,%s %s" % (grouped, frac, currency) if currency else "%s,%s" % (grouped, frac)


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0


def validate(cat, path="$.sampleCatalog"):
    """List of '<path>: <message>' problems; empty when the catalogue is usable."""
    errs = []
    err = lambda p, m: errs.append("%s: %s" % (p, m))
    if not isinstance(cat, dict):
        return ["%s: expected object" % path]
    prods = cat.get("products")
    if not isinstance(prods, list) or not prods:
        err(path + ".products", "required non-empty array")
        prods = []
    keys, names = set(), set()
    for i, p in enumerate(prods):
        pp = "%s.products[%d]" % (path, i)
        if not isinstance(p, dict):
            err(pp, "expected object")
            continue
        for k in ("key", "name", "brand"):
            if not (isinstance(p.get(k), str) and p[k].strip()):
                err(pp + "." + k, "required string")
        if p.get("key") in keys:
            err(pp + ".key", 'duplicate key "%s"' % p.get("key"))
        if p.get("name") in names:
            err(pp + ".name", 'two products named "%s": one product, one name everywhere' % p.get("name"))
        keys.add(p.get("key"))
        names.add(p.get("name"))
        imgs = p.get("images")
        if not (isinstance(imgs, list) and imgs and all(isinstance(x, str) and x for x in imgs)):
            err(pp + ".images", "required non-empty array of file names")
        vs = p.get("variants")
        if not (isinstance(vs, list) and vs):
            err(pp + ".variants", "required non-empty array")
            vs = []
        for j, v in enumerate(vs):
            vp = "%s.variants[%d]" % (pp, j)
            if not (isinstance(v, dict) and isinstance(v.get("name"), str) and _num(v.get("price"))):
                err(vp, "needs name and a price >= 0")
            elif "compare" in v and not (_num(v["compare"]) and v["compare"] > v["price"]):
                err(vp + ".compare", "must be above price")
        for j, t in enumerate(p.get("tiers") or []):
            if not (isinstance(t, dict) and isinstance(t.get("qty"), int) and t["qty"] >= 2 and _num(t.get("price"))):
                err("%s.tiers[%d]" % (pp, j), "needs qty >= 2 and a price")
        for j, o in enumerate(p.get("options") or []):
            if not (isinstance(o, dict) and isinstance(o.get("name"), str) and isinstance(o.get("type"), str)):
                err("%s.options[%d]" % (pp, j), "needs name and type")
            elif "limit" in o and not (isinstance(o["limit"], int) and o["limit"] > 0):
                err("%s.options[%d].limit" % (pp, j), "must be a positive integer")
    by_key = {p.get("key"): p for p in prods if isinstance(p, dict)}
    cart = cat.get("cart")
    if cart is None:
        return errs
    if not isinstance(cart, dict):
        return errs + [path + ".cart: expected object"]
    lines = cart.get("lines")
    if not (isinstance(lines, list) and lines):
        err(path + ".cart.lines", "required non-empty array")
        lines = []
    for i, ln in enumerate(lines):
        lp = "%s.cart.lines[%d]" % (path, i)
        p = by_key.get(ln.get("product")) if isinstance(ln, dict) else None
        if not p:
            err(lp + ".product", "unknown product key")
            continue
        if not any(isinstance(v, dict) and v.get("name") == ln.get("variant") for v in p.get("variants") or []):
            err(lp + ".variant", 'product "%s" has no variant "%s"' % (p["key"], ln.get("variant")))
        if not (isinstance(ln.get("qty"), int) and ln["qty"] >= 1):
            err(lp + ".qty", "integer >= 1")
    for i, c in enumerate(cart.get("campaigns") or []):
        if not (isinstance(c, dict) and isinstance(c.get("label"), str) and _num(c.get("amount"))):
            err("%s.cart.campaigns[%d]" % (path, i), "needs label and amount >= 0")
    cp = cart.get("coupon")
    if cp is not None and not (isinstance(cp, dict) and isinstance(cp.get("code"), str) and _num(cp.get("amount"))):
        err(path + ".cart.coupon", "needs code and amount >= 0, or null")
    if "shipping" in cart and not _num(cart["shipping"]):
        err(path + ".cart.shipping", "number >= 0")
    if not errs:
        t = totals(cat)
        if t["total"] < 0 or t["totalWithCoupon"] < 0:
            err(path + ".cart", "discounts exceed the subtotal")
    return errs


def unit_price(p, variant, qty):
    v = next(v for v in p["variants"] if v["name"] == variant)
    price = v["price"]
    for t in sorted(p.get("tiers") or [], key=lambda t: t["qty"]):
        if qty >= t["qty"]:
            price = t["price"]
    return price


def totals(cat):
    """Cart arithmetic, computed once: lines × qty (tier prices), − campaigns, − coupon, + shipping.
    `total` is the cart without the coupon, `totalWithCoupon` with it (equal when there is none)."""
    by_key = {p["key"]: p for p in cat["products"]}
    cart = cat.get("cart") or {}
    lines = []
    for ln in cart.get("lines") or []:
        u = unit_price(by_key[ln["product"]], ln["variant"], ln["qty"])
        lines.append(dict(ln, unit=u, amount=round(u * ln["qty"], 2)))
    sub = round(sum(x["amount"] for x in lines), 2)
    camp = round(sum(c["amount"] for c in cart.get("campaigns") or []), 2)
    coupon = round((cart.get("coupon") or {}).get("amount", 0), 2)
    ship = round(cart.get("shipping", 0), 2)
    total = round(sub - camp + ship, 2)
    return dict(lines=lines, subtotal=sub, campaigns=camp, coupon=coupon, shipping=ship, total=total,
                totalWithCoupon=round(total - coupon, 2), items=sum(x["qty"] for x in lines))


def expectations(cat):
    """What CHK `seed` compares, with every price already formatted as the canvas writes it."""
    cur = cat.get("currency", "TL")
    prods = {}
    for p in cat["products"]:
        prices = set()
        for v in p["variants"]:
            prices.add(money(v["price"], cur))
            if "compare" in v:
                prices.add(money(v["compare"], cur))
        for t in p.get("tiers") or []:
            prices.add(money(t["price"], cur))
        prods[p["key"]] = dict(name=p["name"], brand=p["brand"], images=[os.path.basename(x) for x in p["images"]],
                               limits=sorted({o["limit"] for o in p.get("options") or [] if "limit" in o}),
                               options=[o["name"] for o in p.get("options") or []])
        if cat.get("cart"):
            for ln in totals(cat)["lines"]:
                if ln["product"] == p["key"]:
                    prices.add(money(ln["amount"], cur))
                    prices.add(money(ln["unit"], cur))
        prods[p["key"]]["prices"] = sorted(prices)
    out = dict(currency=cur, products=prods)
    if cat.get("cart"):
        t = totals(cat)
        out["cart"] = dict(subtotal=money(t["subtotal"], cur), total=money(t["total"], cur),
                           totalWithCoupon=money(t["totalWithCoupon"], cur), items=t["items"],
                           qty={ln["product"]: ln["qty"] for ln in t["lines"]},
                           coupon=(cat["cart"].get("coupon") or {}).get("code"))
    return out


def markdown(cat):
    """Turkish table for plan §6.6 and seed-checklist.md."""
    cur = cat.get("currency", "TL")
    rows = ["| Anahtar | Ürün | Marka | Görsel | Varyant · fiyat | Kademe | Seçenek sınırı |", "|---|---|---|---|---|---|---|"]
    for p in cat["products"]:
        vs = "; ".join("%s · %s%s" % (v["name"], money(v["price"], cur), " (eski %s)" % money(v["compare"], cur) if "compare" in v else "")
                       for v in p["variants"])
        tiers = "; ".join("%d+ · %s" % (t["qty"], money(t["price"], cur)) for t in p.get("tiers") or []) or "—"
        opts = "; ".join("%s%s" % (o["name"], " ≤ %d" % o["limit"] if "limit" in o else "") for o in p.get("options") or []) or "—"
        rows.append("| `%s` | %s | %s | %s | %s | %s | %s |" % (p["key"], p["name"], p["brand"], ", ".join("`%s`" % x for x in p["images"]), vs, tiers, opts))
    if not cat.get("cart"):
        return "\n".join(rows) + "\n"
    t = totals(cat)
    by_key = {p["key"]: p for p in cat["products"]}
    rows += ["", "Örnek sepet (her yerde aynı: CartDrawer, CartPage, ödeme çubuğu, sipariş özeti):", "",
             "| Satır | Adet | Birim | Tutar |", "|---|---|---|---|"]
    for ln in t["lines"]:
        rows.append("| %s · %s | %d | %s | %s |" % (by_key[ln["product"]]["name"], ln["variant"], ln["qty"], money(ln["unit"], cur), money(ln["amount"], cur)))
    rows.append("")
    rows.append("- Ara toplam: %s · %d ürün" % (money(t["subtotal"], cur), t["items"]))
    for c in cat["cart"].get("campaigns") or []:
        rows.append("- Kampanya %s: −%s" % (c["label"], money(c["amount"], cur)))
    if t["shipping"]:
        rows.append("- Kargo: %s" % money(t["shipping"], cur))
    rows.append("- Toplam (kuponsuz): %s" % money(t["total"], cur))
    cp = cat["cart"].get("coupon")
    if cp:
        rows.append("- Kupon `%s` uygulanınca: −%s → %s (yalnız kupon durumlarında)" % (cp["code"], money(cp["amount"], cur), money(t["totalWithCoupon"], cur)))
    return "\n".join(rows) + "\n"


def main(argv=None):
    a = argv if argv is not None else sys.argv[1:]
    if len(a) != 1:
        print(__doc__.strip().split("\n\n")[-2], file=sys.stderr)
        return 2
    cat = load(a[0])
    if cat is None:
        print("no sampleCatalog in plandata")
        return 0
    errs = validate(cat)
    if errs:
        print("\n".join("ERROR " + e for e in errs))
        return 1
    sys.stdout.write(markdown(cat))
    return 0


if __name__ == "__main__":
    sys.exit(main())
