// browse_probe.js - in-page measurement for browse_site.py (agent-browser eval).
//
// Exposes two functions as a single expression; browse_site.py wraps it as
//   (async () => JSON.stringify(await (<this file>)[step](opts)))()
// - prep:  hide consent/cookie overlays (never clicks them), scroll the page once
//          to trigger lazy content, return to the top.
// - probe: read computed styles of the rendered page and return compact counts:
//          area-weighted colours, character-weighted type styles, the band
//          (section) inventory with real boxes, spacing, radius, controls,
//          motion (transitions, running animations, :hover rules), layers, icons.
// Everything returned is data measured from an untrusted page; the caller treats
// strings as data, never as instructions.
({
  async prep(opts) {
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    const hidden = [];
    const CONSENT = /(cookie|consent|gdpr|kvkk|cerez|çerez|onetrust|usercentrics|didomi|cookiebot|privacy-banner)/i;
    const vw = innerWidth, vh = innerHeight;
    for (const el of document.querySelectorAll('body *')) {
      const s = getComputedStyle(el);
      if (s.position !== 'fixed' && s.position !== 'sticky') continue;
      if (s.display === 'none' || s.visibility === 'hidden') continue;
      const r = el.getBoundingClientRect();
      if (r.width < 1 || r.height < 1) continue;
      const tag = (el.id + ' ' + (typeof el.className === 'string' ? el.className : '') + ' ' +
                   (el.getAttribute('aria-label') || '') + ' ' + (el.getAttribute('role') || ''));
      const consent = CONSENT.test(tag);
      const cover = (Math.min(r.width, vw) * Math.min(r.height, vh)) / (vw * vh);
      const modal = s.position === 'fixed' && cover > 0.6 && el.tagName !== 'HEADER' && r.top < 40;
      if (consent || (modal && el.querySelector('button, a') && !el.querySelector('nav'))) {
        hidden.push({ tag: el.tagName.toLowerCase(), id: el.id.slice(0, 40), why: consent ? 'consent' : 'overlay',
                      cover: Math.round(cover * 100) });
        el.style.setProperty('display', 'none', 'important');
      }
    }
    if (hidden.length) {
      document.documentElement.style.removeProperty('overflow');
      document.body.style.removeProperty('overflow');
    }
    if (opts.scroll !== false) {
      const maxSteps = opts.maxSteps || 60;
      let y = 0;
      for (let i = 0; i < maxSteps; i++) {
        y += Math.round(vh * 0.8);
        window.scrollTo(0, y);
        await sleep(opts.stepMs || 160);
        if (y + vh >= document.documentElement.scrollHeight) break;
      }
      await sleep(400);
      window.scrollTo(0, 0);
      await sleep(opts.settleMs || 700);
    }
    return { hidden, docH: document.documentElement.scrollHeight };
  },

  async probe(opts) {
    const errors = [];
    const vw = innerWidth, vh = innerHeight;
    const docW = Math.max(document.documentElement.scrollWidth, vw);
    const docH = Math.max(document.documentElement.scrollHeight, document.body ? document.body.scrollHeight : 0, vh);
    const sx = scrollX, sy = scrollY;
    const MAX_EL = opts.maxElements || 20000;
    const cut = (t, n) => { t = String(t == null ? '' : t).replace(/\s+/g, ' ').trim(); return t.length > n ? t.slice(0, n - 1) + '…' : t; };
    const r1 = (x) => Math.round(x * 10) / 10;
    const inc = (m, k, w = 1) => { m[k] = (m[k] || 0) + w; };
    const top = (m, n) => Object.entries(m).sort((a, b) => b[1] - a[1]).slice(0, n).map(([k, v]) => [k, r1(v)]);

    // --- colour normalisation through a 1x1 canvas (handles rgb/oklch/color()/named)
    const cv = document.createElement('canvas'); cv.width = cv.height = 1;
    const cx = cv.getContext('2d', { willReadFrequently: true });
    const ccache = new Map();
    const hex = (c) => {
      if (!c || c === 'transparent' || c === 'rgba(0, 0, 0, 0)') return null;
      if (ccache.has(c)) return ccache.get(c);
      let out = null;
      try {
        cx.clearRect(0, 0, 1, 1); cx.fillStyle = '#000'; cx.fillStyle = c; cx.fillRect(0, 0, 1, 1);
        const [r, g, b, a] = cx.getImageData(0, 0, 1, 1).data;
        if (a > 0) {
          const h = (v) => v.toString(16).padStart(2, '0').toUpperCase();
          out = '#' + h(r) + h(g) + h(b) + (a < 250 ? h(a) : '');
        }
      } catch (e) { out = null; }
      ccache.set(c, out); return out;
    };

    const all = [...document.querySelectorAll('body, body *')].slice(0, MAX_EL);
    if (all.length >= MAX_EL) errors.push('element cap ' + MAX_EL + ' reached');
    const info = new Map();
    const SKIP = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE', 'LINK', 'META', 'BR', 'HEAD']);
    for (const el of all) {
      if (SKIP.has(el.tagName)) continue;
      const s = getComputedStyle(el);
      if (s.display === 'none') continue;
      const r = el.getBoundingClientRect();
      const vis = r.width > 0.5 && r.height > 0.5 && s.visibility !== 'hidden' && parseFloat(s.opacity) > 0.02;
      info.set(el, { s, r, vis, x: r.left + sx, y: r.top + sy, w: r.width, h: r.height });
    }
    const visible = (el) => { const i = info.get(el); return i && i.vis; };
    const area = (i) => {
      const x0 = Math.max(0, i.x), x1 = Math.min(docW, i.x + i.w), y0 = Math.max(0, i.y), y1 = Math.min(docH, i.y + i.h);
      return Math.max(0, x1 - x0) * Math.max(0, y1 - y0);
    };
    const directText = (el) => {
      let t = '';
      for (const n of el.childNodes) if (n.nodeType === 3) t += n.nodeValue;
      return t.replace(/\s+/g, ' ').trim();
    };
    const kindOf = (el, i) => {
      const t = el.tagName;
      if (t === 'BUTTON' || el.getAttribute('role') === 'button' || (t === 'A' && (hex(i.s.backgroundColor) || parseFloat(i.s.borderTopWidth) > 0) && i.h < 90)) return 'control';
      if (t === 'INPUT' || t === 'SELECT' || t === 'TEXTAREA') return 'field';
      if (t === 'IMG' || t === 'VIDEO' || t === 'PICTURE' || t === 'CANVAS' || /url\(/.test(i.s.backgroundImage)) return 'media';
      if ((hex(i.s.backgroundColor) || parseFloat(i.s.borderTopWidth) > 0 || i.s.boxShadow !== 'none') && i.w >= 120 && i.h >= 80 && i.w < vw * 0.9) return 'card';
      return 'other';
    };

    const res = { w: vw, vh, docW, docH, dpr: devicePixelRatio, errors };

    // --- colours -------------------------------------------------------------
    try {
      const bgPaint = {}, bgArea = {}, textChars = {}, textOn = {}, borderLen = {}, borderOn = {}, gradients = {};
      let mediaArea = 0;
      const opaque = new Set();
      const MEDIA = /^(IMG|VIDEO|CANVAS|PICTURE|IFRAME)$/;
      for (const [el, i] of info) if (i.vis && hex(i.s.backgroundColor) && !MEDIA.test(el.tagName)) opaque.add(el);
      const sub = new Map();
      for (const el of opaque) {
        let p = el.parentElement;
        while (p && !opaque.has(p)) p = p.parentElement;
        if (p) sub.set(p, (sub.get(p) || 0) + area(info.get(el)));
      }
      const pageArea = docW * docH;
      let painted = 0;
      for (const el of opaque) {
        const i = info.get(el), a = area(i), own = Math.max(0, a - (sub.get(el) || 0));
        const c = hex(i.s.backgroundColor);
        inc(bgPaint, c, own); inc(bgArea, c, a); painted += own;
      }
      // canvas colour: html background, else white (browser default)
      const rootBg = hex(getComputedStyle(document.documentElement).backgroundColor);
      const canvasBg = rootBg || (document.body && hex(getComputedStyle(document.body).backgroundColor)) || '#FFFFFF';
      inc(bgPaint, canvasBg, Math.max(0, pageArea - painted));
      for (const [el, i] of info) {
        if (!i.vis) continue;
        const t = directText(el);
        if (t) {
          const tc = hex(i.s.color) || 'transparent', n = Math.min(t.length, 600);
          inc(textChars, tc, n);
          let p = el;
          while (p && !opaque.has(p)) p = p.parentElement;
          const under = p ? hex(info.get(p).s.backgroundColor) : canvasBg;
          inc(textOn, tc + '@' + under, n);
        }
        for (const side of ['Top', 'Right', 'Bottom', 'Left']) {
          const bw = parseFloat(i.s['border' + side + 'Width']);
          if (bw > 0 && i.s['border' + side + 'Style'] !== 'none') {
            const c = hex(i.s['border' + side + 'Color']);
            if (c) {
              const len = side === 'Top' || side === 'Bottom' ? i.w : i.h;
              inc(borderLen, c + ' ' + r1(bw) + 'px', len);
              let p = el.parentElement;
              while (p && !opaque.has(p)) p = p.parentElement;
              inc(borderOn, c + '@' + (opaque.has(el) ? hex(i.s.backgroundColor) : p ? hex(info.get(p).s.backgroundColor) : canvasBg), len);
            }
          }
        }
        const bi = i.s.backgroundImage;
        if (bi && bi !== 'none') {
          if (/gradient\(/.test(bi)) inc(gradients, cut(bi.match(/[a-z-]*gradient\([^]*/)[0], 140), area(i));
          if (/url\(/.test(bi)) mediaArea += area(i);
        }
        if (el.tagName === 'IMG' || el.tagName === 'VIDEO' || el.tagName === 'CANVAS') mediaArea += area(i);
      }
      const pct = (m, tot) => Object.entries(m).sort((a, b) => b[1] - a[1]).slice(0, 16)
        .map(([k, v]) => [k, r1((v / tot) * 100)]);
      const totChars = Object.values(textChars).reduce((a, b) => a + b, 0) || 1;
      const totBorder = Object.values(borderLen).reduce((a, b) => a + b, 0) || 1;
      res.colors = {
        canvas: canvasBg, canvasDefault: !rootBg && !(document.body && hex(getComputedStyle(document.body).backgroundColor)),
        bgPaintPct: pct(bgPaint, pageArea), textPct: pct(textChars, totChars), textOnPct: Object.entries(textOn).sort((a, b) => b[1] - a[1]).slice(0, 30).map(([k, v]) => [k, r1((v / totChars) * 100)]), borderPct: pct(borderLen, totBorder), borderOnPct: Object.entries(borderOn).sort((a, b) => b[1] - a[1]).slice(0, 30).map(([k, v]) => [k, r1((v / totBorder) * 100)]),
        gradients: pct(gradients, pageArea).slice(0, 6), mediaPct: r1(Math.min(100, (mediaArea / pageArea) * 100)),
      };
    } catch (e) { errors.push('colors: ' + e.message); }

    // --- typography ----------------------------------------------------------
    try {
      const styles = {};
      let tot = 0;
      for (const [el, i] of info) {
        if (!i.vis) continue;
        const t = directText(el);
        if (!t) continue;
        const s = i.s, n = Math.min(t.length, 600);
        const fam = s.fontFamily.split(',')[0].replace(/["']/g, '').trim();
        const lh = s.lineHeight === 'normal' ? 'normal' : Math.round(parseFloat(s.lineHeight) / parseFloat(s.fontSize) * 100) / 100 + '';
        const ls = s.letterSpacing === 'normal' ? '0' : r1(parseFloat(s.letterSpacing) / parseFloat(s.fontSize) * 100) / 100 + 'em';
        const k = [fam, r1(parseFloat(s.fontSize)), s.fontWeight, lh, ls, s.textTransform === 'none' ? '' : s.textTransform, s.fontStyle === 'normal' ? '' : s.fontStyle].join('|');
        const st = styles[k] || (styles[k] = { k, chars: 0, els: 0, tags: {}, color: {}, sample: '' });
        st.chars += n; st.els += 1; tot += n;
        inc(st.tags, el.tagName.toLowerCase());
        inc(st.color, hex(s.color) || '?', n);
        if (!st.sample) st.sample = cut(t, 36);
      }
      res.type = Object.values(styles).sort((a, b) => b.chars - a.chars).slice(0, opts.topType || 28).map((st) => {
        const [fam, size, weight, lh, ls, tr, fs] = st.k.split('|');
        return { fam, size: +size, weight: +weight, lh, ls, tr, fs, chars: st.chars, pct: r1((st.chars / (tot || 1)) * 100),
                 els: st.els, tags: top(st.tags, 4), color: top(st.color, 1)[0]?.[0], sample: st.sample };
      });
      const faces = [];
      try { document.fonts.forEach((f) => { if (f.status === 'loaded') faces.push(f.family.replace(/["']/g, '') + ' ' + f.weight + (f.style !== 'normal' ? ' ' + f.style : '')); }); } catch (e) {}
      res.fonts = [...new Set(faces)].slice(0, 40);
    } catch (e) { errors.push('type: ' + e.message); }

    // --- bands (section inventory) ------------------------------------------
    try {
      const kids = (el) => [...el.children].filter((c) => visible(c) && info.get(c).s.position !== 'fixed');
      const wide = (c) => info.get(c).w >= vw * 0.6;
      let root = document.body;
      for (let d = 0; d < 10; d++) {
        const k = kids(root).filter((c) => info.get(c).h >= 8);
        if (k.length === 1 && info.get(k[0]).h >= 0.8 * (info.get(root)?.h || docH)) root = k[0]; else break;
      }
      let bands = kids(root).filter((c) => info.get(c).h >= 24);
      const LAND = (c) => c.tagName === 'HEADER' || c.tagName === 'FOOTER' || c.tagName === 'NAV' || /banner|contentinfo/.test(c.getAttribute('role') || '');
      for (let pass = 0; pass < 4; pass++) {
        const next = [];
        let changed = false;
        for (const b of bands) {
          const i = info.get(b);
          const wk = kids(b).filter((c) => wide(c) && info.get(c).h >= 24);
          const cov = wk.reduce((a, c) => a + info.get(c).h, 0);
          if (!LAND(b) && (b.tagName === 'MAIN' || (i.h > 1.5 * vh && wk.length >= 2 && cov >= 0.8 * i.h))) {
            next.push(...wk); changed = true;
          } else next.push(b);
        }
        bands = next;
        if (!changed) break;
      }
      const NAMEA = ['data-framer-name', 'data-name', 'data-section', 'data-section-type', 'data-component', 'data-testid', 'aria-label', 'id'];
      const effBg = (el) => {
        const i = info.get(el), own = hex(i.s.backgroundColor);
        if (own && own.length === 7) return own;
        let best = null, bestA = 0;
        for (const d of el.querySelectorAll('*')) {
          const di = info.get(d);
          if (!di || !di.vis) continue;
          const c = hex(di.s.backgroundColor);
          if (c && c.length === 7) { const a = area(di); if (a > bestA) { bestA = a; best = c; } }
        }
        if (best && bestA >= 0.7 * area(i)) return best;
        for (let p = el.parentElement; p; p = p.parentElement) {
          const pi = info.get(p) || { s: getComputedStyle(p) };
          const c = hex(pi.s.backgroundColor); if (c && c.length === 7) return c;
        }
        return res.colors?.canvas || '#FFFFFF';
      };
      const ratio = (w, h) => {
        const r = w / h, known = [[1, '1:1'], [4 / 5, '4:5'], [3 / 4, '3:4'], [2 / 3, '2:3'], [9 / 16, '9:16'], [16 / 9, '16:9'], [3 / 2, '3:2'], [4 / 3, '4:3'], [21 / 9, '21:9'], [5 / 4, '5:4']];
        for (const [v, n] of known) if (Math.abs(r - v) / v < 0.04) return n;
        return r1(r) + '';
      };
      res.bands = bands.slice(0, 60).map((b, idx) => {
        const i = info.get(b);
        let name = '';
        const clean = (v) => v.replace(/^shopify-section-/, '').replace(/^(template|sections)--\d+__/, '').replace(/[0-9a-f]{6,}|\d{4,}/gi, '#');
        for (const a of NAMEA) { const v = b.getAttribute(a); if (v && clean(v).replace(/[#_-]/g, '').length >= 3) { name = a + '=' + cut(clean(v), 40); break; } }
        const cls = typeof b.className === 'string' ? cut(b.className.split(/\s+/).filter((c) => c && !/[0-9a-f]{6,}|\d{4,}|^(js|is|has)-/i.test(c)).slice(0, 3).join('.'), 60) : '';
        let cT = Infinity, cB = -Infinity, cL = Infinity, cR = -Infinity, nText = 0, maxFs = 0, head = null;
        const media = {}, rad = {};
        let nMedia = 0, n = 0, slider = false, grid = null, maxMediaA = 0;
        for (const d of [b, ...b.querySelectorAll('*')]) {
          if (++n > 4000) break;
          const di = info.get(d);
          if (!di || !di.vis || di.w < 2 || di.h < 2) continue;
          const t = d === b ? '' : directText(d);
          const isMedia = /^(IMG|VIDEO|CANVAS|SVG|PICTURE|svg)$/.test(d.tagName) || /url\(/.test(di.s.backgroundImage);
          const isBox = d !== b && !!hex(di.s.backgroundColor) && area(di) < 0.9 * area(i);
          if (t || isMedia || isBox || /^(INPUT|BUTTON|SELECT|TEXTAREA)$/.test(d.tagName)) {
            cT = Math.min(cT, Math.max(i.y, di.y)); cB = Math.max(cB, Math.min(i.y + i.h, di.y + di.h));
            cL = Math.min(cL, Math.max(i.x, di.x)); cR = Math.max(cR, Math.min(i.x + i.w, di.x + di.w));
          }
          if (t) {
            nText++;
            const fs = parseFloat(di.s.fontSize);
            if (fs > maxFs) { maxFs = fs; head = { size: r1(fs), weight: +di.s.fontWeight, fam: di.s.fontFamily.split(',')[0].replace(/["']/g, '').trim(), tag: d.tagName.toLowerCase(), text: cut(t, 40) }; }
          }
          if ((d.tagName === 'IMG' || d.tagName === 'VIDEO' || /url\(/.test(di.s.backgroundImage)) && di.w >= 40 && di.h >= 40) {
            nMedia++; inc(media, ratio(di.w, di.h)); maxMediaA = Math.max(maxMediaA, area(di));
            const rr = di.s.borderTopLeftRadius; if (rr && rr !== '0px') inc(rad, rr);
          }
          const ox = di.s.overflowX;
          if ((ox === 'auto' || ox === 'scroll' || ox === 'hidden') && d.scrollWidth > d.clientWidth + 8 && d.children.length >= 3 && di.w >= vw * 0.5) slider = true;
          if (d.children.length >= 2) {
            const ch = [...d.children].filter((c) => visible(c) && info.get(c).w >= 60 && info.get(c).h >= 40);
            if (ch.length >= 2) {
              const y0 = info.get(ch[0]).y;
              const row = ch.filter((c) => Math.abs(info.get(c).y - y0) < 4);
              const w0 = info.get(row[0]).w;
              const g = row.length >= 2 ? info.get(row[1]).x - (info.get(row[0]).x + w0) : -1;
              if (row.length >= 2 && g >= 0 && row.every((c) => Math.abs(info.get(c).w - w0) < 4)) {
                const cand = { cols: row.length, rows: Math.ceil(ch.length / row.length), colW: Math.round(w0), gap: Math.round(g),
                               display: di.s.display, items: ch.length, scroll: d.scrollWidth > d.clientWidth + 8 };
                if (!grid || cand.items > grid.items) grid = cand;
              }
            }
          }
        }
        const has = cT !== Infinity;
        return {
          i: idx + 1, tag: b.tagName.toLowerCase(), name, cls, y: Math.round(i.y), h: Math.round(i.h), w: Math.round(i.w),
          pos: i.s.position === 'static' || i.s.position === 'relative' ? '' : i.s.position, z: i.s.zIndex === 'auto' ? '' : i.s.zIndex,
          bg: effBg(b), mediaCover: Math.round((Math.max(maxMediaA, /url\(/.test(i.s.backgroundImage) ? area(i) : 0) / (area(i) || 1)) * 100),
          padT: has ? Math.round(cT - i.y) : null, padB: has ? Math.round(i.y + i.h - cB) : null,
          marL: has ? Math.round(cL - i.x) : null, marR: has ? Math.round(i.x + i.w - cR) : null, contentW: has ? Math.round(cR - cL) : null,
          text: nText, head, media: top(media, 3), nMedia, mediaRadius: top(rad, 2), grid, slider,
        };
      });
    } catch (e) { errors.push('bands: ' + e.message); }

    // --- spacing, radius, shadow, controls -----------------------------------
    try {
      const gaps = {}, pads = {}, radius = {}, shadow = {}, controls = {}, fields = {};
      for (const [el, i] of info) {
        if (!i.vis) continue;
        const s = i.s;
        if ((s.display.includes('flex') || s.display.includes('grid')) && el.children.length >= 2) {
          for (const g of [s.rowGap, s.columnGap]) if (g && g !== 'normal' && g !== '0px') inc(gaps, g);
        }
        const k = kindOf(el, i);
        if (k === 'card' || k === 'control' || k === 'field') {
          const p = [s.paddingTop, s.paddingRight, s.paddingBottom, s.paddingLeft].map((v) => Math.round(parseFloat(v)));
          if (p.some((v) => v > 0)) inc(pads, k + ' ' + (p[0] === p[2] && p[1] === p[3] ? (p[0] === p[1] ? p[0] : p[0] + ' ' + p[1]) : p.join(' ')));
        }
        if (k !== 'other') {
          const rr = [s.borderTopLeftRadius, s.borderTopRightRadius, s.borderBottomRightRadius, s.borderBottomLeftRadius];
          const v = rr.every((x) => x === rr[0]) ? rr[0] : 'karışık ' + rr.join(' ');
          inc(radius, k + ' ' + (parseFloat(v) >= Math.min(i.w, i.h) / 2 - 1 && v !== '0px' ? 'pill' : v));
          if (s.boxShadow !== 'none') inc(shadow, k + ' ' + cut(s.boxShadow, 90));
        }
        if (k === 'control' && i.h >= 16 && i.h <= 90) {
          const sig = [Math.round(i.h) + 'px h', hex(s.backgroundColor) || 'şeffaf', hex(s.color), (parseFloat(s.borderTopWidth) > 0 ? r1(parseFloat(s.borderTopWidth)) + 'px ' + hex(s.borderTopColor) : 'çizgisiz'),
                       s.borderTopLeftRadius, r1(parseFloat(s.fontSize)) + '/' + s.fontWeight, s.textTransform === 'uppercase' ? 'BÜYÜK' : ''].join(' · ');
          inc(controls, sig);
        }
        if (k === 'field' && el.type !== 'hidden' && el.type !== 'checkbox' && el.type !== 'radio') {
          const sig = [Math.round(i.h) + 'px h', hex(s.backgroundColor) || 'şeffaf', (parseFloat(s.borderTopWidth) > 0 ? r1(parseFloat(s.borderTopWidth)) + 'px ' + hex(s.borderTopColor) : 'çizgisiz'),
                       parseFloat(s.borderBottomWidth) > 0 && parseFloat(s.borderTopWidth) === 0 ? 'alt çizgi' : '', s.borderTopLeftRadius, r1(parseFloat(s.fontSize)) + 'px'].filter(Boolean).join(' · ');
          inc(fields, sig);
        }
      }
      res.spacing = { gaps: top(gaps, 14), pads: top(pads, 14) };
      res.radius = top(radius, 16); res.shadow = top(shadow, 8);
      res.controls = top(controls, 10); res.fields = top(fields, 6);
    } catch (e) { errors.push('spacing: ' + e.message); }

    // --- layers (fixed / sticky) ----------------------------------------------
    try {
      const layers = [];
      for (const [el, i] of info) {
        if (!i.vis) continue;
        const p = i.s.position;
        if (p !== 'fixed' && p !== 'sticky') continue;
        if (el.parentElement && info.get(el.parentElement) && ['fixed', 'sticky'].includes(info.get(el.parentElement).s.position)) continue;
        layers.push({ tag: el.tagName.toLowerCase(), cls: typeof el.className === 'string' ? cut(el.className.split(/\s+/)[0] || '', 30) : '',
                      pos: p, top: i.s.top, h: Math.round(i.h), w: Math.round(i.w), z: i.s.zIndex, bg: hex(i.s.backgroundColor) || '',
                      blur: i.s.backdropFilter && i.s.backdropFilter !== 'none' ? i.s.backdropFilter : '' });
      }
      res.layers = layers.slice(0, 16);
    } catch (e) { errors.push('layers: ' + e.message); }

    // --- motion: transitions, running animations ------------------------------
    try {
      const tr = {};
      for (const [el, i] of info) {
        if (!i.vis) continue;
        const d = i.s.transitionDuration;
        if (!d || /^0s(, 0s)*$/.test(d)) continue;
        const props = i.s.transitionProperty.split(',').map((x) => x.trim());
        const durs = d.split(',').map((x) => x.trim()), fns = i.s.transitionTimingFunction.split(/,(?![^(]*\))/).map((x) => x.trim());
        const dels = i.s.transitionDelay.split(',').map((x) => x.trim());
        props.forEach((p, j) => {
          const du = durs[j % durs.length]; if (du === '0s') return;
          const de = dels[j % dels.length];
          inc(tr, p + ' ' + du + ' ' + fns[j % fns.length] + (de && de !== '0s' ? ' gecikme ' + de : ''));
        });
      }
      res.transitions = top(tr, 18);
      const anims = {};
      for (const a of document.getAnimations ? document.getAnimations() : []) {
        try {
          const t = a.effect && a.effect.getTiming ? a.effect.getTiming() : {};
          const tg = a.effect && a.effect.target;
          const nm = a.animationName || (a.constructor && a.constructor.name === 'CSSTransition' ? 'transition:' + a.transitionProperty : 'waapi');
          const k = [nm, (t.duration === 'auto' ? 'auto' : Math.round(t.duration)) + 'ms', t.easing, t.iterations === Infinity ? '∞' : t.iterations,
                     t.delay ? 'gecikme ' + Math.round(t.delay) + 'ms' : '', tg ? tg.tagName.toLowerCase() : ''].filter((x) => x !== '').join(' · ');
          inc(anims, k);
        } catch (e) {}
      }
      res.animations = top(anims, 16);
    } catch (e) { errors.push('motion: ' + e.message); }

    // --- stylesheets: :hover rules that match on-page elements, @media, :root vars
    try {
      const hov = [], mq = {}, varNames = new Set();
      let blocked = 0;
      const walk = (rules, cond) => {
        for (const r of rules) {
          if (r.cssRules && r.media) { walk(r.cssRules, (r.media.mediaText || r.conditionText || ''));
            const t = r.media.mediaText || '';
            for (const m of t.matchAll(/(min|max)-width:\s*([\d.]+)(px|em|rem)/g)) inc(mq, m[1] + '-width ' + (m[3] === 'px' ? m[2] + 'px' : r1(parseFloat(m[2]) * 16) + 'px (' + m[2] + m[3] + ')'));
            continue; }
          if (r.cssRules && !r.selectorText) { walk(r.cssRules, cond); continue; }
          if (!r.selectorText) continue;
          if (/(^|,)\s*(:root|html)\s*(,|$)/.test(r.selectorText)) for (const p of r.style) if (p.startsWith('--')) varNames.add(p);
          if (r.selectorText.includes(':hover') && hov.length < 400) {
            const decl = cut(r.style.cssText, 160);
            if (!decl) continue;
            for (const part of r.selectorText.split(',')) {
              if (!part.includes(':hover')) continue;
              const base = part.replace(/:hover/g, '').replace(/\s+>/g, ' >').trim() || '*';
              let nm = 0;
              try { for (const e of document.querySelectorAll(base)) if (visible(e)) nm++; } catch (e) { continue; }
              if (nm) { hov.push({ sel: cut(part.trim(), 90), decl, n: nm, media: cut(cond, 40) }); break; }
            }
          }
        }
      };
      for (const sh of document.styleSheets) {
        let rules = null;
        try { rules = sh.cssRules; } catch (e) { blocked++; continue; }
        if (rules) walk(rules, '');
      }
      hov.sort((a, b) => b.n - a.n);
      res.hover = hov.slice(0, opts.topHover || 30);
      res.mediaQueries = top(mq, 20);
      const rs = getComputedStyle(document.documentElement);
      res.vars = [...varNames].slice(0, 220).map((n) => [n, cut(rs.getPropertyValue(n), 80)]);
      res.blockedSheets = blocked;
    } catch (e) { errors.push('sheets: ' + e.message); }

    // --- icons -------------------------------------------------------------------
    try {
      const sizes = {}, style = { çizgi: 0, dolgu: 0 };
      for (const svg of document.querySelectorAll('svg')) {
        const i = info.get(svg);
        if (!i || !i.vis || i.w > 64 || i.h > 64 || i.w < 8) continue;
        inc(sizes, Math.round(i.w) + '×' + Math.round(i.h));
        const shp = svg.querySelector('path, circle, rect, line, polyline, polygon');
        if (!shp) continue;
        const ss = getComputedStyle(shp);
        if (ss.stroke && ss.stroke !== 'none' && (ss.fill === 'none' || ss.fill === 'rgba(0, 0, 0, 0)')) style.çizgi++; else style.dolgu++;
      }
      res.icons = { sizes: top(sizes, 8), style };
    } catch (e) { errors.push('icons: ' + e.message); }

    return res;
  },
})
