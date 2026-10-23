#!/usr/bin/env python3
"""build_manifest.py - build the port package (docs/port/) from plandata, plan and canvas dump.

Usage:
  python3 build_manifest.py --plandata <dir|plandata.json> --plan <plan.md>
                            [--dump docs/port/canvas-dump.txt] -o <outdir> [--json]

Inputs:
  --plandata  plandata directory (theme.json + sections/) or a single JSON file
              (schema: templates/plandata/README.md). Gives sections, components,
              pages and variables.
  --plan      the rendered plan (gen_plan.py output). Its anim-targets YAML blocks
              give animTargets (subset parser from lint_plan.py; PyYAML optional).
  --dump      optional canvas dump: the `ROOT|<rootName>|<nodeId>|device=..|props=..|
              data=..|code=..|anims=..` lines printed by
              `extract_targets.py <plan> --js manifest` in pen.dev. Other lines are ignored.
              Gives frame node ids and the canvas-side prop/data/code/anim sets, which are
              diffed against the plan per section.

Outputs (in <outdir>): port-manifest.json (schema 1, references/09-handoff.md §1),
port-manifest.md, globals-runbook.md and seed-checklist.md (Turkish, §2, §3 and
references/10-port-behaviour.md). The behaviour criteria and seed entries of
data/port-behaviour.json whose scope matches the plan go into the manifest as `behaviour`
and `seed`.

Stdout: one `Q|<id>|<kind>|<where>|<text>` line per open question, one `FILE|<path>` line
per written file, then the summary line
  MANIFEST|sections=N|overlays=N|subs=N|pages=N|anims=N|behaviour=N|seed=N|open=N|blocking=N
With --json, a single JSON object (counts, openQuestions, files) replaces those lines.

openQuestions kinds: missing-section, missing-frame, prop-mismatch, anim-missing-on-canvas,
anim-extra-on-canvas, data-unmarked, other. Entries with "blocking": true make the exit code 1.

Exit codes: 0 ok; 1 a plan section/overlay/page, or a plan anim id, is absent from the
canvas dump (only with --dump); 2 usage, IO or plandata/plan errors.
Python 3.9+, stdlib only.
"""
import argparse
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
BEHAVIOUR = os.path.join(HERE, 'data', 'port-behaviour.json')
import gen_plan as G  # noqa: E402  plandata loader + validator + target ids
import lint_plan as L  # noqa: E402  anim-targets YAML subset parser + impl vocabulary

# ---- fixed tables (references/02-contract.md §3, 04-ikas-constraints.md §1-2, 09-handoff.md) ----

MERCHANT_TYPES = {'IMAGE', 'IMAGE_LIST', 'VIDEO', 'PRODUCT', 'PRODUCT_LIST', 'PRODUCT_ATTRIBUTE',
                  'PRODUCT_ATTRIBUTE_LIST', 'BRAND', 'BRAND_LIST', 'CATEGORY', 'CATEGORY_LIST', 'BLOG',
                  'BLOG_LIST', 'BLOG_CATEGORY', 'BLOG_CATEGORY_LIST'}
# prop types that live on a visible layer; only these are diffed plan <-> canvas
LAYER_TYPES = {'TEXT', 'RICH_TEXT', 'IMAGE', 'IMAGE_LIST', 'VIDEO', 'SVG', 'SVG_LIST'}

SCHEME_SLOTS = collections.OrderedDict([
    ('color-bg', 'Background'), ('color-text', 'Text'),
    ('color-inverse-bg', 'PrimaryButton/Background'), ('color-inverse-text', 'PrimaryButton/Text')])
COLOR_DEST = {'color-muted': 'Muted', 'color-line': 'Line', 'color-surface': 'Surface', 'color-accent': 'Accent',
              'color-accent-text': 'AccentText', 'color-danger': 'Danger', 'color-success': 'Success'}
CSS_COLORS = {'color-scrim', 'color-transparent'}
COLOR_TR = {'color-bg': 'Zemin', 'color-text': 'Metin', 'color-muted': 'Soluk Metin', 'color-line': 'Çizgi',
            'color-surface': 'Yüzey', 'color-inverse-bg': 'Ters Zemin', 'color-inverse-text': 'Ters Metin',
            'color-accent': 'Vurgu', 'color-accent-text': 'Vurgu Üstü Metin', 'color-scrim': 'Perde',
            'color-transparent': 'Şeffaf', 'color-danger': 'Hata', 'color-success': 'Başarı'}
TYPE_TR = {'text-display': 'Display', 'text-h2': 'Başlık H2', 'text-h3': 'Başlık H3', 'text-h4': 'Başlık H4',
           'text-title': 'Ürün Adı', 'text-ui': 'Arayüz', 'text-ui-sm': 'Arayüz Küçük', 'text-badge': 'Rozet',
           'text-label': 'Etiket', 'text-body': 'Gövde', 'text-price': 'Fiyat'}
MODE_TR = {'light': 'Açık', 'dark': 'Koyu'}
BREAKPOINTS = [('laptop', 'Kırılım / Laptop', 1199), ('tablet', 'Kırılım / Tablet', 991),
               ('mobile', 'Kırılım / Mobil', 767)]  # globals.md §4 defaults
DEFAULT_PAGE_TYPES = ['INDEX', 'CATEGORY', 'PRODUCT_DETAIL', 'CART', 'ACCOUNT', 'LOGIN', 'REGISTER',
                      'FORGOT_PASSWORD', 'RECOVER_PASSWORD', 'NOT_FOUND', 'SEARCH', 'FAVORITES']  # 06 §2 ✓
GROUP_TR = [({'TEXT', 'RICH_TEXT'}, 'Metinler'), ({'IMAGE', 'IMAGE_LIST', 'VIDEO'}, 'Görseller'),
            ({'SVG', 'SVG_LIST'}, 'Marka'), ({'LINK', 'LIST_OF_LINK'}, 'Bağlantılar'), ({'COLOR'}, 'Renkler'),
            ({'COMPONENT', 'COMPONENT_LIST'}, 'Bileşenler')]
STYLE_PREFIX = ('text-', 'font-', 'color-', 'space-', 'size-', 'opacity-')
MARKER = re.compile(r'\{([A-Za-z_]\w*):([^}\s]+)\}')
TREE_PREFIX = re.compile(r'^[\s│├└─]*')
IDENT = re.compile(r'[A-Za-z][\w-]*')
ROOT_RE = re.compile(r'^([A-Z])/(DS|Sub|Section|Overlay|Page|Motion)/(.+)$')
STATE_SPLIT = re.compile(r'\s+(?:—|–|-{1,2})\s+')
VAR_REF = re.compile(r'\$?\b((?:color|font|text|space|size|opacity)-[a-z0-9]+(?:-[a-z0-9]+)*)\b')


class ManifestError(Exception):
    pass


def text_of(v):
    return '\n'.join(v) if isinstance(v, list) else (v or '')


def group_of(t):
    for types, g in GROUP_TR:
        if t in types:
            return g
    return 'İçerik' if t in MERCHANT_TYPES else 'Ayarlar'


def fmt_num(v):
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    return str(v)


def px(v):
    return fmt_num(v) + 'px'


# ---- plandata parsing --------------------------------------------------------------------

def parse_props_line(s):
    """Props prose -> ([(name, type)], [child slot dicts]). Names without a type are dropped."""
    top, children = [], []
    for seg in (s or '').split(' · '):
        pending = []
        for m in re.finditer(r'`([A-Za-z_]\w*)`|\b([A-Z][A-Z_]+)\b(?:\s*\(([^)]*)\))?', seg):
            if m.group(1):
                pending.append(m.group(1))
                continue
            t = m.group(2)
            if t not in G.PROP_TYPES or not pending:
                continue
            for n in pending:
                top.append((n, t))
            if t in ('COMPONENT', 'COMPONENT_LIST') and m.group(3):
                cm = re.match(r'\s*([A-Z]\w*)\s*(?::\s*(.*))?$', m.group(3))
                if cm:
                    cprops = []
                    for part in (cm.group(2) or '').split(','):
                        pm = re.match(r'\s*([A-Za-z_]\w*)\s+([A-Z_]+)\s*$', part)
                        if pm and pm.group(2) in G.PROP_TYPES:
                            cprops.append((pm.group(1), pm.group(2)))
                    children.append(dict(slot=pending[-1], type=t, components=[cm.group(1)], props=cprops))
            pending = []
    return top, children


def tree_data_marks(tree, sub_names):
    """-> [{kind: data|code, value, layer, subs}] for every {data:} / {code:} marker; subs = the Sub names
    the same tree line mentions (the data may live inside one of those Subs on the canvas)."""
    marks = [m for m in parse_tree(tree)]
    out, i = [], 0
    for line in tree:
        body = TREE_PREFIX.sub('', line)
        subs = [w for w in IDENT.findall(body) if w in sub_names]
        for m in MARKER.finditer(body):
            mk = marks[i]
            i += 1
            if mk['kind'] in ('data', 'code'):
                out.append(dict(kind=mk['kind'], value=mk['source'] if mk['kind'] == 'data' else mk['name'],
                                layer=mk['layer'], subs=subs))
    return out


def tree_layers(tree):
    known = set()
    for line in tree:
        body = TREE_PREFIX.sub('', line)
        m = IDENT.match(body)
        if m:
            known.add(m.group(0))
        for a in re.finditer(r'→\s*([A-Za-z][\w-]*)', body):
            known.add(a.group(1))
    return known


def parse_tree(tree):
    """-> list of markers {kind: prop|data|code, name, type|source, layer, default}."""
    known = tree_layers(tree)
    out = []
    for line in tree:
        body = TREE_PREFIX.sub('', line)
        first = IDENT.match(body)
        marks = list(MARKER.finditer(body))
        for i, m in enumerate(marks):
            layer = None
            for w in IDENT.finditer(body[:m.start()]):
                tok = w.group(0)
                if tok in known and not tok.startswith(STYLE_PREFIX) and tok not in ('clip', 'sticky'):
                    layer = tok
            if layer is None and first:
                layer = first.group(0)
            name, val = m.group(1), m.group(2)
            if name == 'data':
                out.append(dict(kind='data', source=val, layer=layer))
            elif name == 'code':
                out.append(dict(kind='code', name=val, layer=layer))
            else:
                after = body[m.end():marks[i + 1].start() if i + 1 < len(marks) else len(body)]
                before = body[marks[i - 1].end() if i else 0:m.start()]
                q = re.search(r'"([^"]*)"', after)
                if not q:
                    q = re.search(r'"([^"]*)"[\s,;:]*$', before)
                out.append(dict(kind='prop', name=name, type=val, layer=layer, default=q.group(1) if q else None))
    return out


def clean_states(s):
    out = []
    for st in text_of(s).split(' · '):
        st = re.sub(r'\s*\([^)]*\)', '', st).strip()
        if st and st not in ('—', '-') and ':' not in st:
            out.append(st)
    return out


def template_of(ikas):
    tpls = re.findall(r'\b([a-z][a-z-]*-section)\b', ikas or '')
    return (tpls[0] if tpls else None), tpls


def page_rows(d):
    rows = []
    for p in d['pages']:
        secs = G.page_sections(p['sections'])
        secs += re.findall(r'\(\s*\+\s*([A-Z]\w*)[^)]*\)', p['sections'])  # "(+ AnchorNav sabit)"
        for e in (p.get('expand') or [dict(name=p['name'], pageType=p.get('pageType'))]):
            name = e['name']
            if not re.match(r'^[A-Za-z]\w*$', name):
                name = L.expand_page(name)[0]
            rows.append(dict(name=name, pageType=e.get('pageType') or p.get('pageType') or 'CUSTOM',
                             sections=secs, row=p['name']))
    return rows


# ---- canvas dump ----------------------------------------------------------------------------

def parse_dump(path, P):
    roots = []
    with open(path, encoding='utf-8') as f:
        for ln, raw in enumerate(f, 1):
            line = raw.rstrip('\n')
            if not line.startswith('ROOT|'):
                continue
            parts = line.split('|')
            if len(parts) < 3:
                raise ManifestError('%s:%d: malformed ROOT line' % (path, ln))
            r = dict(name=parts[1], nodeId=parts[2] or None, device='-', props=[], data=[], code=[], anims=[])
            for kv in parts[3:]:
                k, _, v = kv.partition('=')
                items = [x for x in v.split(';') if x]
                if k == 'device':
                    r['device'] = v or '-'
                elif k == 'props':
                    for x in items:
                        n, _, t = x.rpartition(':')
                        r['props'].append((n or t, t if n else '?'))
                elif k == 'data':
                    for x in items:
                        lay, _, src = x.partition('=')
                        r['data'].append((lay, src))
                elif k == 'code':
                    r['code'] = items
                elif k == 'anims':
                    r['anims'] = items
            m = ROOT_RE.match(r['name'])
            if not m or m.group(1) != P:
                continue
            band, rest = m.group(2), m.group(3)
            parts2 = STATE_SPLIT.split(rest, 1)
            head, state = parts2[0].strip(), (parts2[1].strip() if len(parts2) > 1 else None)
            dm = re.match(r'^(.*?)@(desktop|mobile)$', head)
            key = dm.group(1) if dm else head
            dev = dm.group(2) if dm else (r['device'] if r['device'] in ('desktop', 'mobile') else None)
            sm = re.match(r'^(.*?)@(desktop|mobile)$', state or '') if band == 'Page' else None
            if sm:  # page variant of an expanded row: `P/Page/Auth — Login@desktop` is page `Login`
                r['row'] = key.strip()
                key, dev, state = sm.group(1), sm.group(2), None
            r.update(band=band, key=key.strip(), dev=dev, state=state, line=ln)
            roots.append(r)
    return roots


# ---- globals.md §1a / §2a (final colour schemes and breakpoint text styles) -----------------

SLOT_STD = {'background': 'Background', 'text': 'Text', 'button-bg': 'PrimaryButton/Background',
            'button-text': 'PrimaryButton/Text'}


def _md_section(lines, prefix):
    out, on = [], False
    for l in lines:
        if l.startswith('### ') or l.startswith('## '):
            if on:
                break
            on = l.startswith('### ' + prefix)
            continue
        if on:
            out.append(l)
    return out


def _md_table(lines):
    rows = [l for l in lines if l.startswith('|')]
    if len(rows) < 3:
        return None, []
    cells = lambda l: [c.strip() for c in l.strip().strip('|').split('|')]
    return cells(rows[0]), [cells(l) for l in rows[2:]]


def _tick(s):
    m = re.search(r'`([^`]+)`', s or '')
    return m.group(1) if m else (s or '').strip()


def parse_globals_md(path):
    """Final colour schemes (§1a) and text styles (§2a) from docs/referans/globals.md; {} when absent."""
    with open(path, encoding='utf-8') as f:
        lines = f.read().split('\n')
    res = {}
    sec = _md_section(lines, '1a.')
    head, rows = _md_table(sec)
    if head and len(head) > 2 and rows:
        names = [re.sub(r'\s*\(.*?\)\s*', '', h).strip() for h in head[2:]]
        schemes = [collections.OrderedDict([('label', n), ('note', (re.search(r'\((.*?)\)', h) or [None, ''])[1]),
                                            ('slots', [])]) for n, h in zip(names, head[2:])]
        for r in rows:
            slot, var = r[0].strip(), _tick(r[1])
            std = SLOT_STD.get(slot) or ''.join(w.capitalize() for w in slot.split('-'))
            for i, s in enumerate(schemes):
                if 2 + i < len(r):
                    s['slots'].append(collections.OrderedDict([('slot', std), ('var', var), ('value', _tick(r[2 + i]))]))
        defaults = [l[2:].strip() for l in sec if l.startswith('- **') and any(('**%s:**' % n) in l for n in names)]
        res['schemes'] = schemes
        res['schemeDefaults'] = defaults
    head, rows = _md_table(_md_section(lines, '2a.'))
    if head and rows:
        typo = {}
        for r in rows:
            if len(r) < 9:
                continue
            fam = [x.strip() for x in r[2].split('·')]
            num = lambda x: float(x) if re.match(r'^[\d.]+$', x) else None
            sizes = [num(x) for x in r[3:7]]
            ls = r[8].replace('−', '-').replace('+', '')
            typo[_tick(r[1])] = dict(label=r[0], family=fam[0], weight=next((x for x in fam[1:] if re.match(r'^\d00$', x)), None),
                                     transform='uppercase' if any('BÜYÜK' in x.upper() for x in fam[2:]) else None,
                                     sizes=sizes, lineHeight=r[7], letterSpacing=None if ls in ('0', '') else ls)
        res['typography'] = typo
    return res


# ---- keyframes -----------------------------------------------------------------------------

def ascii_slug(s):
    tr = str.maketrans('çğıöşüÇĞİÖŞÜâÂ', 'cgiosuCGIOSUaA')
    return re.sub(r'[^a-z0-9]+', '-', s.translate(tr).lower()).strip('-') or 'scheme'


def split_flow(s):
    s = (s or '').strip()
    if not (s.startswith('{') and s.endswith('}')):
        return None
    body, out, cur, depth, q = s[1:-1], [], '', 0, False
    for ch in body:
        if ch == '"':
            q = not q
        elif not q and ch in '[{(':
            depth += 1
        elif not q and ch in ']})':
            depth -= 1
        if ch == ',' and depth == 0 and not q:
            out.append(cur)
            cur = ''
        else:
            cur += ch
    if cur.strip():
        out.append(cur)
    pairs = []
    for item in out:
        k, sep, v = item.partition(':')
        if not sep:
            return None
        pairs.append((k.strip(), v.strip().strip('"')))
    return pairs


def css_styles(flow):
    pairs = split_flow(flow)
    if pairs is None:
        return None
    tf, styles = [], []
    for k, v in pairs:
        num = re.match(r'^-?\d+(\.\d+)?$', v)
        if k == 'opacity' and num:
            styles.append(dict(property='opacity', value=v))
        elif k in ('x', 'y') and re.match(r'^-?\d+(\.\d+)?%?$', v):
            tf.append('translate%s(%s)' % (k.upper(), v if v.endswith('%') else v + 'px'))
        elif k == 'scale' and num:
            tf.append('scale(%s)' % v)
        elif k in ('rotate', 'rotateX', 'skewX', 'skewY') and num:
            tf.append('%s(%sdeg)' % (k, v))
        elif k == 'clip' and v.startswith('inset('):
            styles.append(dict(property='clip-path', value=v))
        else:
            return None
    if tf:
        styles.insert(0, dict(property='transform', value=' '.join(tf)))
    return styles or None


# ---- builder -------------------------------------------------------------------------------

class Builder:
    def __init__(self, data, contract, cat, plan, plan_path, roots, gmd=None):
        self.gmd = gmd or {}
        self.d, self.c2, self.cat, self.plan = data, contract == 2, cat, plan
        self.contract = contract
        self.th = data['theme']
        self.P = self.th['prefix']
        self.modes = data.get('modes')
        self.plan_path = plan_path
        self.roots = roots  # None when no dump
        self.questions = []
        self.orphans = []
        self.local = (data.get('recipes') or {}).get('local') or {}
        self.targets = [{k: v for k, v in t.items() if not k.startswith('_')} for t in plan.targets]
        self.canvas_ids = set()
        if roots is not None:
            for r in roots:
                self.canvas_ids.update(r['anims'])
        self.plan_ids = [t.get('id') for t in self.targets]
        self.cmp_ids = {t['id'] for t in self.targets if str(t.get('section', '')).startswith('Sub/')}

    # questions
    def q(self, kind, where, text, blocking=False):
        e = collections.OrderedDict([('id', 'Q%d' % (len(self.questions) + 1)), ('kind', kind),
                                     ('where', where), ('text', text)])
        if blocking:
            e['blocking'] = True
        self.questions.append(e)

    def roots_of(self, band, key):
        return [r for r in (self.roots or []) if r['band'] == band and r['key'] == key]

    def rname(self, band, key, dev=None, state=None):
        n = '%s/%s/%s' % (self.P, band, key)
        if dev:
            n += '@' + dev
        if state:
            n += ' — ' + state
        return n

    # ---- globals
    def globals(self):
        v = self.d['variables']
        modes = self.modes
        name = self.th['name']
        colors, css, schemes = [], [], []
        scheme_names = [('%s / %s' % (name, MODE_TR.get(m, m.capitalize())), m) for m in (modes or ['default'])]
        if not modes:
            scheme_names = [('%s / Varsayılan' % name, 'default')]
        slots = []
        for var, val in v['colors'].items():
            vals = collections.OrderedDict(zip(modes, val)) if modes else collections.OrderedDict(default=val)
            label = COLOR_TR.get(var) or var.replace('color-', '').replace('-', ' ').title()
            e = collections.OrderedDict([('var', var), ('name', 'Renk / ' + label), ('values', vals)])
            varies = len(set(vals.values())) > 1
            hexes = list(vals.values())
            if var in CSS_COLORS or any(len(h) == 9 for h in hexes):
                e['ikas'] = dict(kind='globalCss', css='--' + var)
                css.append(collections.OrderedDict([('var', var), ('css', '--' + var), ('values', vals)]))
            elif var in SCHEME_SLOTS or varies:
                slot = SCHEME_SLOTS.get(var) or COLOR_DEST.get(var) or label.replace(' ', '')
                e['ikas'] = dict(kind='colorScheme', slot=slot)
                slots.append((slot, var, vals))
            else:
                e['ikas'] = dict(kind='color', name=COLOR_DEST.get(var) or label.replace(' ', ''))
            colors.append(e)
        for sname, m in scheme_names:
            schemes.append(collections.OrderedDict([
                ('name', sname), ('mode', m),
                ('slots', [collections.OrderedDict([('slot', s), ('var', var), ('value', vals[m])])
                           for s, var, vals in slots])]))
        # typography
        fonts = v['fonts']
        spec = {}
        for g in self.d['typeStyles']['map']:
            for s in g['styles']:
                spec[s] = g['spec']
        typo = []
        for var, (dsz, msz) in v['type'].items():
            sp = spec.get(var, '')
            fm = re.search(r'\$?(font-[a-z]+)', sp)
            wm = re.search(r'(?<![\d.])([1-9]00)(?![\d.])', sp)
            lm = re.search(r'satır(?:\s+yüksekliği)?\s*([\d.]+)', sp)
            fvar = fm.group(1) if fm else None
            typo.append(collections.OrderedDict([
                ('var', var), ('name', 'Tipografi / ' + (TYPE_TR.get(var) or var.replace('text-', '').title())),
                ('fontVar', fvar), ('family', fonts.get(fvar) if fvar else None),
                ('weight', wm.group(1) if wm else None), ('lineHeight', lm.group(1) if lm else None),
                ('sizes', collections.OrderedDict([('desktop', dsz), ('mobile', msz)]))]))
        # numbers -> global.css
        for var, val in v['numbers'].items():
            dv, mv = (val if isinstance(val, list) else [val, val])
            css.append(collections.OrderedDict([('var', var), ('css', '--' + var),
                                                ('values', collections.OrderedDict([('desktop', dv), ('mobile', mv)]))]))
        gvars = []
        line, lcol = v['numbers'].get('size-line'), v['colors'].get('color-line')
        if line is not None and lcol is not None:
            w = line[0] if isinstance(line, list) else line
            c = lcol[0] if isinstance(lcol, list) else lcol
            gvars.append(collections.OrderedDict([
                ('name', 'Çizgi / Varsayılan'), ('type', 'BORDER'), ('vars', ['size-line', 'color-line']),
                ('value', collections.OrderedDict([('width', dict(value=w, unit='px')), ('style', 'solid'),
                                                   ('color', c)]))]))
        bps = [collections.OrderedDict([('id', i), ('name', n), ('width', w)]) for i, n, w in BREAKPOINTS]
        # keyframes from css-keyframes / theme-keyframe targets, one per recipe
        kf = collections.OrderedDict()
        for t in self.targets:
            impl = str(t.get('impl', ''))
            if 'css-keyframes' not in impl and 'theme-keyframe' not in impl:
                continue
            rid = t.get('recipe')
            if rid not in kf:
                rec = self.local.get(rid) or self.cat.get(rid) or {}
                a, b = css_styles(t.get('from')), css_styles(t.get('to'))
                pts = []
                if a and b:
                    pts = [dict(point='0%', styles=a), dict(point='100%', styles=b)]
                kf[rid] = collections.OrderedDict([
                    ('name', 'Animasyon / %s' % (rec.get('name') or rid)), ('recipe', rid),
                    ('from', t.get('from')), ('to', t.get('to')), ('points', pts), ('usedBy', [])])
            kf[rid]['usedBy'].append(t['id'])
        if self.gmd.get('schemes'):
            in_scheme = {x['var']: x['slot'] for x in self.gmd['schemes'][0]['slots']}
            schemes = []
            for i, s in enumerate(self.gmd['schemes']):
                schemes.append(collections.OrderedDict([
                    ('name', '%s / %s' % (name, s['label'])), ('mode', ascii_slug(s['label'])), ('note', s['note']),
                    ('default', i == 0), ('slots', s['slots'])]))
            for c in colors:
                if c['var'] in in_scheme:
                    c['ikas'] = dict(kind='colorScheme', slot=in_scheme[c['var']])
            css = [c for c in css if c['var'] not in in_scheme]
        for t in typo:
            g2 = (self.gmd.get('typography') or {}).get(t['var'])
            if not g2:
                continue
            sz = g2['sizes']
            t.update([('family', g2['family'] or t['family']), ('weight', g2['weight'] or t['weight']),
                      ('lineHeight', g2['lineHeight'] or t['lineHeight']), ('letterSpacing', g2['letterSpacing']),
                      ('transform', g2['transform']), ('source', 'globals.md §2a')])
            if all(x is not None for x in sz):
                t['sizes'] = collections.OrderedDict([('desktop', sz[0]), ('laptop', sz[1]), ('tablet', sz[2]), ('mobile', sz[3])])
        return collections.OrderedDict([
            ('colors', colors), ('colorSchemes', schemes), ('typography', typo), ('breakpoints', bps),
            ('keyframes', list(kf.values())), ('globalCss', css), ('globalVariables', gvars)]
            + ([('schemeDefaults', self.gmd['schemeDefaults'])] if self.gmd.get('schemeDefaults') else []))

    # ---- props / markers for one section or overlay
    def plan_props(self, sec):
        top, children = parse_props_line(text_of(sec.get('props')))
        marks = parse_tree(sec.get('tree') or [])
        child_names = {n for c in children for n, _ in c['props']}
        tree_props = [m for m in marks if m['kind'] == 'prop']
        props = collections.OrderedDict()
        for n, t in top:
            if n not in props:
                props[n] = dict(name=n, type=t, layer=None, default=None, inLine=True, inTree=False)
        for m in tree_props:
            if m['name'] in child_names and m['name'] not in props:
                for c in children:
                    for i, (cn, ct) in enumerate(c['props']):
                        if cn == m['name'] and not isinstance(ct, dict):
                            c['props'][i] = (cn, dict(type=ct, layer=m['layer'], default=m['default']))
                continue
            e = props.setdefault(m['name'], dict(name=m['name'], type=m['type'], layer=None, default=None,
                                                 inLine=False, inTree=True))
            e['inTree'] = True
            e['layer'] = e['layer'] or m['layer']
            if e['default'] is None:
                e['default'] = m['default']
            if e['type'] != m['type']:
                e['treeType'] = m['type']
        return props, children, marks

    def section_entry(self, sec, frames_band):
        key = sec['key']
        props, children, marks = self.plan_props(sec)
        roots = self.roots_of(frames_band, key) if self.roots is not None else None
        canvas_props, canvas_data, canvas_code, canvas_anims = collections.OrderedDict(), [], set(), set()
        for r in roots or []:
            for n, t in r['props']:
                canvas_props.setdefault(n, t)
            for lay, src in r['data']:
                if (lay, src) not in canvas_data:
                    canvas_data.append((lay, src))
            canvas_code.update(r['code'])
            canvas_anims.update(r['anims'])
        has_canvas = bool(roots)
        where = key
        out_props = []
        for n, p in props.items():
            t = p['type']
            cmp_t = canvas_props.get(n) if has_canvas else (t if p['inTree'] else None)
            on_canvas = cmp_t is not None
            src = ('both' if on_canvas else 'plan') if self.roots is not None else 'plan'
            e = collections.OrderedDict([('name', n), ('type', t)])
            if t in MERCHANT_TYPES:
                e['default'] = None
                e['merchantData'] = True
            else:
                e['default'] = p['default'] if t in ('TEXT', 'RICH_TEXT') else None
            e['group'] = group_of(t)
            e['layer'] = p['layer']
            e['from'] = src
            out_props.append(e)
            # backgroundColor sits on the root frame (contract 2), never in the tree: canvas-only check
            comparable = t in LAYER_TYPES or (self.c2 and has_canvas and t == 'COLOR' and n == 'backgroundColor')
            if has_canvas or self.roots is None:
                if comparable and not on_canvas:
                    side = "canvas'ta" if self.roots is not None else "ağaçta (tree)"
                    self.q('prop-mismatch', '%s.%s' % (where, n), "Planda %s, %s prop yok" % (t, side))
                elif on_canvas and cmp_t != t and cmp_t != '?':
                    self.q('prop-mismatch', '%s.%s' % (where, n), 'Planda %s, canvas\'ta %s' % (t, cmp_t))
        child_names = {cn for c in children for cn, _ in c['props']}
        for n, t in canvas_props.items():
            if n not in props and n not in child_names:
                out_props.append(collections.OrderedDict([
                    ('name', n), ('type', t), ('default', None)] + ([('merchantData', True)] if t in MERCHANT_TYPES else [])
                    + [('group', group_of(t)), ('layer', None), ('from', 'canvas')]))
                self.q('prop-mismatch', '%s.%s' % (where, n), "Canvas'ta %s prop, planda yok" % t)
        out_children = []
        for c in children:
            cp = []
            for cn, ct in c['props']:
                info = ct if isinstance(ct, dict) else dict(type=ct, layer=None, default=None)
                ce = collections.OrderedDict([('name', cn), ('type', info['type'])])
                if info['type'] in MERCHANT_TYPES:
                    ce['default'] = None
                    ce['merchantData'] = True
                else:
                    ce['default'] = info['default'] if info['type'] in ('TEXT', 'RICH_TEXT') else None
                ce['layer'] = info['layer']
                cp.append(ce)
            out_children.append(collections.OrderedDict([('slot', c['slot']), ('type', c['type']),
                                                         ('components', c['components']), ('props', cp)]))
        # data / code text (found on the key's roots, as a context mark, or inside a Sub the tree line names)
        data_bound, code_text = [], []
        sub_names = {c['name'] for c in self.d['components']}
        canvas_sources = {s for _, s in canvas_data}
        line_subs = {(dm['kind'], dm['value']): dm['subs'] for dm in tree_data_marks(sec.get('tree') or [], sub_names)}
        for m in marks:
            if m['kind'] == 'data':
                data_bound.append(collections.OrderedDict([('layer', m['layer']), ('source', m['source'])]))
                via = [s for s in line_subs.get(('data', m['source']), []) if any(
                    m['source'] in {x for _, x in r['data']} for r in (self.roots_of('Sub', s) if self.roots is not None else []))]
                if via:
                    data_bound[-1]['via'] = via[0]
                if has_canvas and m['source'] not in canvas_sources and not via:
                    self.q('data-unmarked', '%s.%s' % (where, m['layer']),
                           "Planda {data:%s}, canvas'ta textClass:\"data\" / source yok" % m['source'])
            elif m['kind'] == 'code':
                code_text.append(collections.OrderedDict([('layer', m['layer']), ('code', m['name'])]))
                via = [s for s in line_subs.get(('code', m['name']), []) if any(
                    r['code'] for r in (self.roots_of('Sub', s) if self.roots is not None else []))]
                if via:
                    code_text[-1]['via'] = via[0]
                if has_canvas and m['layer'] not in canvas_code and m['name'] not in canvas_code and not via:
                    self.q('data-unmarked', '%s.%s' % (where, m['layer']),
                           "Planda {code:%s}, canvas'ta textClass:\"code\" yok" % m['name'])
        for lay, src in canvas_data:
            if not any(x['source'] == src for x in data_bound):
                data_bound.append(collections.OrderedDict([('layer', lay), ('source', src), ('from', 'canvas')]))
        for lay in sorted(canvas_code):
            if not any(x['layer'] == lay for x in code_text):
                code_text.append(collections.OrderedDict([('layer', lay), ('code', None), ('from', 'canvas')]))
        # anims
        plan_ids = [t['id'] for t in self.targets if t.get('section') == key]
        anims = list(plan_ids)
        if has_canvas:
            for i in sorted(canvas_anims):
                if i in self.cmp_ids:
                    continue  # sub-component instances carry their own ids
                if i not in self.plan_ids:
                    self.q('anim-extra-on-canvas', '%s.%s' % (where, i), "Canvas'ta var, planda yok")
                    anims.append(i)
                elif i not in plan_ids:
                    owner = next((t['section'] for t in self.targets if t['id'] == i), '?')
                    self.q('anim-extra-on-canvas', '%s.%s' % (where, i),
                           "Hedef planda %s bölümüne ait, canvas'ta bu frame'de duruyor" % owner)
            for i in plan_ids:
                if i in self.canvas_ids and i not in canvas_anims:
                    found = [r['name'] for r in self.roots if i in r['anims']]
                    self.q('anim-missing-on-canvas', '%s.%s' % (where, i),
                           "Hedef bu bölümün frame'lerinde yok; yalnızca: %s" % ', '.join(found[:3]))
        return out_props, out_children, data_bound, code_text, anims, roots

    def frames_for(self, band, key, devices, where_label):
        frames = collections.OrderedDict()
        roots = self.roots_of(band, key) if self.roots is not None else []
        for dev in devices:
            rs = [r for r in roots if r['dev'] == dev]
            if band == 'Overlay':
                frames[dev] = [collections.OrderedDict([('root', r['name']), ('state', r['state']),
                                                        ('nodeId', r['nodeId'])]) for r in rs]
            else:
                r = next((x for x in rs if not x['state']), None)  # the component, never a state frame
                frames[dev] = collections.OrderedDict([('root', r['name'] if r else self.rname(band, key, dev)),
                                                       ('nodeId', r['nodeId'] if r else None)])
                sts = [collections.OrderedDict([('state', x['state']), ('nodeId', x['nodeId'])]) for x in rs if x['state']]
                if sts:
                    frames[dev]['states'] = sts
        if self.roots is not None:
            have = {r['dev'] for r in roots if band == 'Overlay' or not r['state']}
            missing = [dv for dv in devices if dv not in have]
            if len(missing) == len(devices):
                ids = [t['id'] for t in self.targets if t.get('section') == key]
                self.q('missing-section', key, "Planda var, canvas'ta %s kök frame'i yok%s" % (
                    ' / '.join('`%s`' % self.rname(band, key, dv) for dv in devices),
                    (' (anim hedefleri: %s)' % ', '.join(ids)) if ids else ''), blocking=True)
            else:
                for dv in missing:
                    self.q('missing-frame', '%s@%s' % (key, dv), "`%s` kök frame'i canvas'ta yok" % self.rname(band, key, dv))
        return frames

    def build(self):
        d, P = self.d, self.P
        devices_all = ['desktop', 'mobile']
        secs = [s for s in d['sections'] if s['kind'] == 'section']
        ovls = [s for s in d['sections'] if s['kind'] == 'overlay']
        sec_keys = [s['key'] for s in secs]
        missing_secs = set()

        if not self.c2:
            self.q('data-unmarked', 'contract',
                   'Contract 1: metinlerde textClass yok; dataBound ve codeText boş. Veri bağlı ve kodla '
                   'üretilen metinler aktarımda elle belirlenmeli.')

        sections = []
        for s in secs:
            frames = self.frames_for('Section', s['key'], devices_all, s['key'])
            if self.roots is not None and not self.roots_of('Section', s['key']):
                missing_secs.add(s['key'])
            props, children, data_bound, code_text, anims, _ = self.section_entry(s, 'Section')
            tpl, tpls = template_of(s.get('ikas'))
            ikas = s.get('ikas') or ''
            flags = collections.OrderedDict([
                ('isHeader', '--isHeader' in ikas or s['key'] == 'Header'),
                ('isFooter', '--isFooter' in ikas or s['key'] == 'Footer'),
                ('container', any(c['type'] == 'COMPONENT_LIST' for c in children)),
                ('custom', '(özel' in ikas)])
            e = collections.OrderedDict([
                ('key', s['key']), ('code', s['code']), ('template', tpl)])
            if len(tpls) > 1:
                e['templates'] = tpls
            e.update([('ikas', ikas), ('flags', flags), ('props', props), ('children', children),
                      ('dataBound', data_bound), ('codeText', code_text), ('anims', anims), ('frames', frames),
                      ('overlays', [])])
            if s.get('mode'):
                e['mode'] = s['mode']
            for f in ('desktopOnly', 'desktopOnlyStates'):
                if s.get(f):
                    e[f] = list(s[f])
            sections.append(e)
        by_key = {e['key']: e for e in sections}

        for o in ovls:
            devs = o.get('devices') or devices_all
            frames = self.frames_for('Overlay', o['key'], devs, o['key'])
            if self.roots is not None and not self.roots_of('Overlay', o['key']):
                missing_secs.add(o['key'])
            props, children, data_bound, code_text, anims, roots = self.section_entry(o, 'Overlay')
            states = []
            for r in roots or []:
                if r['state'] and r['state'] not in states:
                    states.append(r['state'])
            owner = None
            m = re.match(r'^\s*([A-Z]\w*)\s+sub-component', o.get('ikas') or '')
            cands = ([m.group(1)] if m else []) + re.findall(r'\b([A-Z]\w*)\b', o.get('pages') or '')
            for c in cands:
                if c in by_key:
                    owner = c
                    break
            oe = collections.OrderedDict([
                ('name', o['key']), ('code', o['code']), ('owner', owner), ('devices', devs), ('states', states),
                ('props', props), ('children', children), ('dataBound', data_bound), ('codeText', code_text),
                ('anims', anims), ('frames', frames)])
            for f in ('desktopOnly', 'desktopOnlyStates'):
                if o.get(f):
                    oe[f] = list(o[f])
            if owner:
                by_key[owner]['overlays'].append(oe)
            else:
                self.q('other', o['key'], 'Overlay için sahip section bulunamadı (`ikas` ya da `pages` alanında section adı yok)')
                self.orphans.append(oe)

        subs = []
        for c in d['components']:
            n = c['name']
            roots = self.roots_of('Sub', n) if self.roots is not None else None
            base = next((r for r in roots or [] if not r['state']), None)
            plan_states = clean_states(c.get('states'))
            if roots is not None:
                states = []
                for r in roots:
                    if r['state'] and r['state'] not in states:
                        states.append(r['state'])
                if not roots:
                    self.q('missing-frame', 'Sub/' + n, "`%s` kök frame'i canvas'ta yok" % self.rname('Sub', n))
                else:
                    miss = [st for st in plan_states[1:] if st not in states]
                    if miss:
                        self.q('missing-frame', 'Sub/' + n, "Durum frame'leri canvas'ta yok: %s" % ', '.join(
                            '`%s`' % self.rname('Sub', n, state=st) for st in miss))
            else:
                states = plan_states[1:]
            props = []
            for r in roots or []:
                for pn, pt in r['props']:
                    if not any(p['name'] == pn for p in props):
                        e = collections.OrderedDict([('name', pn), ('type', pt), ('default', None)])
                        if pt in MERCHANT_TYPES:
                            e['merchantData'] = True
                        props.append(e)
            ids = [t['id'] for t in self.targets if t.get('section') == 'Sub/' + n]
            if roots:
                canvas = set()
                for r in roots:
                    canvas.update(r['anims'])
                for i in ids:
                    if i in self.canvas_ids and i not in canvas:
                        self.q('anim-missing-on-canvas', 'Sub/%s.%s' % (n, i), "Hedef `%s` frame'lerinde yok" % self.rname('Sub', n))
            subs.append(collections.OrderedDict([
                ('name', n), ('root', self.rname('Sub', n)), ('nodeId', base['nodeId'] if base else None),
                ('states', states), ('props', props), ('anims', ids)]))

        pages = []
        for p in page_rows(d):
            frames = collections.OrderedDict()
            roots = self.roots_of('Page', p['name']) if self.roots is not None else []
            for dv in devices_all:
                r = next((r for r in roots if r['dev'] == dv), None)
                frames[dv] = r['nodeId'] if r else None
            if self.roots is not None:
                miss = [dv for dv in devices_all if not any(r['dev'] == dv for r in roots)]
                if len(miss) == 2:
                    self.q('missing-frame', 'Page/' + p['name'], "Sayfa canvas'ta yok: `%s`" % self.rname('Page', p['name'], 'desktop|mobile'),
                           blocking=True)
                for dv in (miss if len(miss) == 1 else []):
                    self.q('missing-frame', 'Page/%s@%s' % (p['name'], dv), "`%s` kök frame'i canvas'ta yok" % self.rname('Page', p['name'], dv))
            pages.append(collections.OrderedDict([('name', p['name']), ('pageType', p['pageType']),
                                                  ('sections', p['sections']), ('frames', frames)]))

        # DS frames, unknown roots, global anim diff
        if self.roots is not None:
            ds = L.DS_C2 if self.c2 else L.DS_C1
            for k in ds:
                if not self.roots_of('DS', k):
                    self.q('missing-frame', 'DS/' + k, "`%s` kök frame'i canvas'ta yok" % self.rname('DS', k))
            plan_secs = {s['key']: s['kind'] for s in d['sections']}
            seen = set()
            for r in self.roots:
                tag = (r['band'], r['key'])
                if tag in seen:
                    continue
                seen.add(tag)
                if r['band'] == 'Section' and plan_secs.get(r['key']) != 'section' or \
                        r['band'] == 'Overlay' and plan_secs.get(r['key']) != 'overlay' or \
                        r['band'] == 'Sub' and r['key'] not in {c['name'] for c in d['components']}:
                    self.q('other', r['name'], "Canvas'ta kök frame var, planda karşılığı yok")
            for i in sorted(self.canvas_ids - set(self.plan_ids)):
                if not any(q['kind'] == 'anim-extra-on-canvas' and q['where'].endswith('.' + i) for q in self.questions):
                    roots_with = [r['name'] for r in self.roots if i in r['anims']]
                    self.q('anim-extra-on-canvas', i, "Canvas'ta var, planda yok (%s)" % ', '.join(roots_with[:3]))
            for t in self.targets:
                i = t['id']
                if i in self.canvas_ids:
                    continue
                if t.get('section') in missing_secs:
                    continue  # reported with its missing section (blocking)
                self.q('anim-missing-on-canvas', i, "Plandaki hedef (%s · %s) canvas'ta hiçbir kök frame'de yok "
                       "(metadata.anim / context)" % (t.get('section'), t.get('layer')), blocking=True)

        anim_targets = []
        for t in self.targets:
            e = collections.OrderedDict((k, t[k]) for k in L.REQ_KEYS[:3] if k in t)
            if t.get('via'):
                e['via'] = t['via']
            for k in L.REQ_KEYS[3:]:
                if k in t:
                    e[k] = t[k]
            if self.roots is not None:
                e['onCanvas'] = t['id'] in self.canvas_ids
            anim_targets.append(e)

        ref = self.th.get('reference') or {}
        devs = d['devices']
        theme = collections.OrderedDict([
            ('slug', self.th['slug']), ('name', self.th['name']), ('prefix', P), ('contract', self.contract),
            ('reference', ref.get('url') or None), ('canvas', self.th.get('penFile')), ('plan', self.plan_path),
            ('devices', collections.OrderedDict([('desktop', devs['desktop']['width']), ('mobile', devs['mobile']['width'])])),
            ('modes', self.modes)])
        m = collections.OrderedDict([
            ('schema', 1), ('theme', theme), ('globals', self.globals()), ('subComponents', subs),
            ('sections', sections), ('pages', pages), ('animTargets', anim_targets),
            ('openQuestions', self.questions)])
        return m


# ---- behaviour criteria and seed data (references/10-port-behaviour.md) ------------------------

def load_behaviour(path=BEHAVIOUR):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def in_scope(e, keys, page_types):
    """An entry applies when it names no scope, or one of its keys / page types is in the plan."""
    ks, pts = e.get('keys') or [], e.get('pageTypes') or []
    return (not ks and not pts) or bool(set(ks) & keys) or bool(set(pts) & page_types)


def apply_behaviour(m, data):
    """Add the criteria and seed entries that apply to this plan as m['behaviour'] / m['seed'].
    A seed entry is kept only when at least one criterion it serves is kept."""
    keys = ({s['key'] for s in m['sections']} | {o['name'] for s in m['sections'] for o in s['overlays']}
            | {c['name'] for c in m['subComponents']})
    page_types = {p['pageType'] for p in m['pages']}
    beh = [collections.OrderedDict([('id', e['id']), ('title', e['title']), ('rule', e['rule']), ('test', e['test']),
                                    ('done', False)])
           for e in data.get('behaviour', []) if in_scope(e, keys, page_types)]
    ids = {b['id'] for b in beh}
    seed = []
    for e in data.get('seed', []):
        serves = [i for i in e.get('for', []) if i in ids]
        if serves and in_scope(e, keys, page_types):
            seed.append(collections.OrderedDict([('id', e['id']), ('title', e['title']), ('what', e['what']),
                                                 ('for', serves), ('done', False)]))
    m['behaviour'], m['seed'] = beh, seed
    m.move_to_end('openQuestions')
    return m


def render_seed_md(m):
    th = m['theme']
    out = ['# Test verisi — %s (%s)' % (th['name'], th['prefix']), '',
           'Port testlerinden önce dev mağazada oluşturulur: admin panelinde (mağaza sahibinin açtığı oturumda) ya da '
           'admin API ile. Ajan mağaza şifresi yazmaz. İçerik temanın Türkçe metin kurallarına uyar; görseller temanın '
           'görsel yönünden gelir. Testler tek sekmede, sayfa sayfa yapılır; önbellek için adrese `?cb=<n>` eklenir '
           '(`references/10-port-behaviour.md` §3–§4).', '']
    if not m.get('seed'):
        return '\n'.join(out + ['Bu plan için test verisi gerekmiyor.']) + '\n'
    for e in m['seed']:
        out.append('- [ ] **%s · %s** — %s Kriterler: %s.' % (e['id'], e['title'], e['what'], ', '.join(e['for'])))
    return '\n'.join(out) + '\n'


# ---- coverage audit ---------------------------------------------------------------------------

def var_names(d):
    v = d['variables']
    return set(v['colors']) | set(v['fonts']) | set(v['type']) | set(v['numbers'])


def used_vars(text, known):
    return [x for x in dict.fromkeys(VAR_REF.findall(text)) if x in known]


def coverage(d, m):
    known = var_names(d)
    gname = {}
    for c in m['globals']['colors']:
        k = c['ikas']['kind']
        gname[c['var']] = c['name'] + {'colorScheme': ' (şema slotu %s)' % c['ikas'].get('slot'),
                                       'globalCss': ' (global.css)'}.get(k, '')
    for t in m['globals']['typography']:
        gname[t['var']] = t['name']
    for c in m['globals']['globalCss']:
        gname.setdefault(c['var'], '`%s`' % c['css'])
    for f, fam in d['variables']['fonts'].items():
        gname[f] = '`%s` (%s)' % (f, fam)
    bullets, used = [], set()
    units = []
    for s in d['sections']:
        units.append((s['key'], '\n'.join([text_of(s.get('tree')), text_of(s.get('desktop')), text_of(s.get('mobile'))])))
    for c in d['components']:
        units.append(('Sub/' + c['name'], text_of(c.get('structure'))))
    raw_refs = set()
    for name, txt in units:
        u = used_vars(txt, known)
        used.update(u)
        raw_refs.update(re.findall(r'\$([a-z][a-z0-9-]*[a-z0-9])', txt))
        bullets.append('- **%s** → kullanılan token\'lar: %s' % (name, ', '.join(gname.get(x, x) for x in u) or '—'))
    # typography in use pulls in its font; scheme base slots are used by every section
    for t in m['globals']['typography']:
        if t['var'] in used and t['fontVar']:
            used.add(t['fontVar'])
    used.update(['color-bg', 'color-text'])
    unused = [x for x in (list(d['variables']['colors']) + list(d['variables']['fonts']) + list(d['variables']['type'])
                          + list(d['variables']['numbers'])) if x not in used]
    unknown = sorted(x for x in raw_refs if x not in known)
    page_types = {p['pageType'] for p in m['pages']}
    miss_pages = [x for x in DEFAULT_PAGE_TYPES if x not in page_types]
    bad_impl, kf_missing = [], []
    kf_by = {}
    for k in m['globals']['keyframes']:
        for i in k['usedBy']:
            kf_by[i] = k
    for t in m['animTargets']:
        known_t, forb, unk = L.impl_terms(str(t.get('impl', '')))
        if forb or unk or not known_t:
            bad_impl.append('%s (`%s`)' % (t['id'], t.get('impl')))
        impl = str(t.get('impl', ''))
        if ('css-keyframes' in impl or 'theme-keyframe' in impl) and not (kf_by.get(t['id']) or {}).get('points'):
            kf_missing.append(t['id'])
    checks = [
        ('Her global en az bir bileşende kullanılıyor', not unused,
         ('kullanılmayan: ' + ', '.join('`%s`' % x for x in unused)) if unused else 'tümü kullanılıyor'),
        ("Canvas'taki her `$değişken` bir global'e ya da `global.css`'e eşleniyor", not unknown,
         ('eşlenmeyen: ' + ', '.join('`$%s`' % x for x in unknown)) if unknown else
         "plan ağacı üzerinden denetlendi (canvas dump'ı değişken taşımaz)"),
        ('Kapsamdaki her sayfa tipinin sayfası ve section\'ı var', not miss_pages,
         ('sayfası olmayan: ' + ', '.join('`%s`' % x for x in miss_pages) if miss_pages else 'varsayılan kapsam tam')
         + " (brief okunmadı; 06-page-coverage §2 varsayılan kapsamı)"),
        ("Her anim hedefinin izinli bir `impl`'i (ve gerekiyorsa keyframe'i) var", not bad_impl and not kf_missing,
         '; '.join(x for x in [
             ('impl dışı: ' + ', '.join(bad_impl)) if bad_impl else '',
             ('keyframe noktaları elle doldurulacak: ' + ', '.join(kf_missing)) if kf_missing else '']
             if x) or 'tümü uygun'),
    ]
    return bullets, checks


# ---- markdown ---------------------------------------------------------------------------------

def cell(v):
    if v is None or v == '' or v == []:
        return '—'
    return str(v).replace('|', '\\|').replace('\n', ' ')


def render_manifest_md(d, m):
    th, g = m['theme'], m['globals']
    P = th['prefix']
    modes = th['modes']
    secs, subs, pages = m['sections'], m['subComponents'], m['pages']
    ovls = [o for s in secs for o in s['overlays']]
    oq = m['openQuestions']
    out = ['# Port manifest — %s (%s, contract %d)' % (th['name'], P, th['contract']), '',
           "Kaynak: `port-manifest.json` (schema 1). Bu dosya ondan üretilir; elle düzenlenmez. Canlı token "
           "eşleşmeleri `globals-runbook.md` sonundaki tablodadır.", '',
           '## Özet', '',
           '| Section | Sub | Sayfa | Overlay | Anim hedefi | Açık soru |', '|---|---|---|---|---|---|',
           '| %d | %d | %d | %d | %d | %d |' % (len(secs), len(subs), len(pages), len(ovls), len(m['animTargets']), len(oq)),
           '']
    nblock = sum(1 for q in oq if q.get('blocking'))
    if nblock:
        out += ['**Engelleyici %d açık soru var**: canvas plana yetişmeden port başlamaz.' % nblock, '']
    out += ["## Tema global'leri", '', '### Renkler', '']
    if modes:
        out += ['| Ad | pen.dev | %s | ikas |' % ' | '.join(MODE_TR.get(x, x) for x in modes),
                '|---|---|' + '---|' * len(modes) + '---|']
    else:
        out += ['| Ad | pen.dev | Değer | ikas |', '|---|---|---|---|']
    for c in g['colors']:
        ik = c['ikas']
        dest = {'colorScheme': 'colorScheme slot `%s`' % ik.get('slot'), 'color': 'color `%s`' % ik.get('name'),
                'globalCss': '`global.css` `%s`' % ik.get('css')}[ik['kind']]
        out.append('| %s | `%s` | %s | %s |' % (c['name'], c['var'], ' | '.join('`%s`' % x for x in c['values'].values()), dest))
    four = any('laptop' in t['sizes'] for t in g['typography'])
    out += ['', '### Tipografi', '', '| Ad | pen.dev | Aile | Ağırlık | Satır | Masaüstü | %sMobil |' % ('Laptop | Tablet | ' if four else ''),
            '|---|---|---|---|---|---|---|' + ('---|---|' if four else '')]
    for t in g['typography']:
        sz = t['sizes']
        mid = ('%s | %s | ' % (fmt_num(sz.get('laptop', sz['desktop'])), fmt_num(sz.get('tablet', sz['mobile'])))) if four else ''
        out.append('| %s | `%s` | %s | %s | %s | %s | %s%s |' % (
            t['name'], t['var'], cell(t['family']), cell(t['weight']), cell(t['lineHeight']),
            fmt_num(sz['desktop']), mid, fmt_num(sz['mobile'])))
    if g['colorSchemes'] and g['colorSchemes'][0].get('slots') and 'default' in g['colorSchemes'][0]:
        out += ['', '### Renk şemaları (`globals.md` §1a)', '',
                '| Slot | pen.dev | ' + ' | '.join(s['name'] for s in g['colorSchemes']) + ' |',
                '|---|---|' + '---|' * len(g['colorSchemes'])]
        for i, x in enumerate(g['colorSchemes'][0]['slots']):
            out.append('| `%s` | `%s` | %s |' % (x['slot'], x['var'], ' | '.join('`%s`' % s['slots'][i]['value'] for s in g['colorSchemes'])))
    out += ['', '### Kırılımlar', '', '| Ad | Genişlik |', '|---|---|']
    out += ['| %s | %d |' % (b['name'], b['width']) for b in g['breakpoints']]
    out += ['', "### Keyframe'ler", '', '| Ad | Kullanan hedefler |', '|---|---|']
    out += ['| %s%s | %s |' % (k['name'], '' if k['points'] else ' (noktalar elle)', ', '.join(k['usedBy']))
            for k in g['keyframes']] or ['| — | — |']
    out += ['', '### global.css', '', '| Custom property | Masaüstü | Mobil |', '|---|---|---|']
    for c in g['globalCss']:
        vals = c['values']
        if 'desktop' in vals:
            out.append('| `%s` | %s | %s |' % (c['css'], fmt_num(vals['desktop']), fmt_num(vals['mobile'])))
        else:
            out.append('| `%s` | %s | (mod: %s) |' % (c['css'], ' / '.join('`%s`' % x for x in vals.values()),
                                                     ' / '.join(vals.keys())))
    if g['globalVariables']:
        out += ['', '### Global değişkenler', '', '| Ad | Tip | Değer |', '|---|---|---|']
        for v in g['globalVariables']:
            out.append('| %s | %s | `%s` |' % (v['name'], v['type'], json.dumps(v['value'], ensure_ascii=False)))
    out += ['', "## Sub-component'ler", '', "| Ad | Durumlar | Prop'lar | Animasyonlar |", '|---|---|---|---|']
    for s in subs:
        out.append('| `%s` | %s | %s | %s |' % (s['name'], cell(' · '.join(s['states'])),
                                               cell(', '.join('`%s` %s' % (p['name'], p['type']) for p in s['props'])),
                                               cell(', '.join(s['anims']))))
    out += ['', "## Section'lar", '']

    def prop_table(props):
        L2 = ["| Prop | Tip | Varsayılan | Grup | Katman |", '|---|---|---|---|---|']
        for p in props:
            dflt = '— (merchant verisi)' if p.get('merchantData') else (
                '"%s"' % p['default'] if p.get('default') is not None else '—')
            src = {'plan': ' _(yalnız plan)_', 'canvas': " _(yalnız canvas)_"}.get(p.get('from'), '')
            if p.get('from') == 'plan' and p['type'] not in LAYER_TYPES:
                src = ''  # lists, links, settings have no layer on the canvas by design
            L2.append('| `%s`%s | %s | %s | %s | %s |' % (p['name'], src, p['type'], cell(dflt), p.get('group', '—'),
                                                       '`%s`' % p['layer'] if p.get('layer') else '—'))
        return L2

    def frame_list(fr):
        parts = []
        for dv, f in fr.items():
            if isinstance(f, list):
                parts += ['`%s` (%s)' % (x['root'], x['nodeId'] or '—') for x in f] or ['`%s/Overlay/…@%s` (—)' % (P, dv)]
            else:
                parts.append('`%s` (%s)' % (f['root'], f['nodeId'] or '—'))
        return ' · '.join(parts)

    def desktop_only(e):
        L3 = []
        if e.get('desktopOnly'):
            L3.append('- **Yalnız masaüstü katmanlar:** %s — mobilde render edilmez ya da `@media (max-width: bp(<mobile id>))` '
                      'altında `display: none`' % ', '.join('`.%s`' % x for x in e['desktopOnly']))
        if e.get('desktopOnlyStates'):
            L3.append('- **Yalnız masaüstü durumlar:** %s' % ', '.join('`%s`' % x for x in e['desktopOnlyStates']))
        return L3

    for s in secs:
        fl = [k for k, v in s['flags'].items() if v]
        out += ['### %s' % s['key'], '',
                '- **Şablon:** %s · **Bayraklar:** %s' % (
                    ('`%s`' % s['template']) if s['template'] else ('(özel)' if s['flags']['custom'] else cell(s['ikas'])),
                    ', '.join('`%s`' % x for x in fl) or '—'),
                "- **Frame'ler:** " + frame_list(s['frames']), '']
        out += prop_table(s['props']) if s['props'] else ["_Prop yok (planda tanımlı değil)._"]
        out += ['',
                '- **Çocuklar:** ' + (', '.join('`%s` %s → %s%s' % (
                    c['slot'], c['type'], ', '.join(c['components']),
                    (' (%s)' % ', '.join('`%s` %s' % (p['name'], p['type']) for p in c['props'])) if c['props'] else '')
                    for c in s['children']) or '—'),
                '- **Veri bağlı metinler:** ' + (', '.join('`%s` = `%s`' % (x['layer'], x['source']) for x in s['dataBound']) or '—'),
                '- **Kod metinleri:** ' + (', '.join('`%s`%s' % (x['layer'], (' (%s)' % x['code']) if x.get('code') else '')
                                                   for x in s['codeText']) or '—'),
                '- **Animasyonlar:** ' + (', '.join(s['anims']) or '—'),
                "- **Overlay'ler:** " + (', '.join('`%s` (%s)' % (o['name'], ' · '.join(o['states']) or 'durum yok')
                                                   for o in s['overlays']) or '—')]
        out += desktop_only(s) + ['']
        for o in s['overlays']:
            out += ['#### %s › Overlay %s' % (s['key'], o['name']), '',
                    "- **Cihazlar:** %s · **Frame'ler:** %s" % (', '.join(o['devices']), frame_list(o['frames'])),
                    '- **Animasyonlar:** ' + (', '.join(o['anims']) or '—')] + desktop_only(o) + ['']
            out += (prop_table(o['props']) if o['props'] else ['_Prop yok._']) + ['']
    out += ['## Sayfalar', '', "| Sayfa | ikas sayfa tipi | Section'lar (sırayla) |", '|---|---|---|']
    for p in pages:
        out.append('| `%s` | `%s` | %s |' % (p['name'], p['pageType'], ' · '.join(p['sections'])))
    out += ['', '## Animasyon hedefleri', '', '| impl | Hedef |', '|---|---|']
    cnt = collections.Counter(str(t.get('impl')) for t in m['animTargets'])
    for impl, n in sorted(cnt.items(), key=lambda x: (-x[1], x[0])):
        out.append('| `%s` | %d |' % (cell(impl), n))
    out += ['', 'Tam liste `port-manifest.json` → `animTargets`.', '', '## Kapsama denetimi', '']
    bullets, checks = coverage(d, m)
    out += bullets
    out += ['', '| Kontrol | Sonuç | Not |', '|---|---|---|']
    for name, ok, note in checks:
        out.append('| %s | %s | %s |' % (name, 'geçti' if ok else 'kaldı', cell(note)))
    out += ['', '## Davranış kabul kriterleri', '',
            "Canvas görünüşü sabitler, davranışı sabitleyemez. Port her maddeyi canlı mağazada masaüstü ve 390 "
            "genişlikte tıklayarak dener ve işaretler (`references/10-port-behaviour.md`). Gereken test verisi: "
            "`seed-checklist.md`.", '']
    if m.get('behaviour'):
        for b in m['behaviour']:
            out.append('- [ ] **%s · %s** — %s *Test:* %s' % (b['id'], b['title'], b['rule'], b['test']))
    else:
        out.append('Bu plan için kriter yok.')
    out += ['', '## Açık sorular', '']
    if oq:
        for i, q in enumerate(oq, 1):
            out.append('%d. **%s** `%s` — %s%s' % (i, q['kind'], q['where'], q['text'],
                                                 ' **(engelleyici)**' if q.get('blocking') else ''))
    else:
        out.append('Açık soru yok.')
    return '\n'.join(out) + '\n'


def render_runbook(m):
    th, g = m['theme'], m['globals']
    name = th['name']
    modes = th['modes']
    rows = []  # (kind, name, value, source)
    for b in g['breakpoints']:
        rows.append(('breakpoint', b['name'], '%d px' % b['width'], 'globals.md §4 (`%s`)' % b['id']))
    for c in g['colors']:
        if c['ikas']['kind'] == 'color':
            rows.append(('color', c['name'], ' / '.join(dict.fromkeys(c['values'].values())), '`%s`' % c['var']))
    for s in g['colorSchemes']:
        rows.append(('colorScheme', s['name'], ', '.join('%s %s' % (x['slot'], x['value']) for x in s['slots']),
                     'mode `%s`: ' % s['mode'] + ', '.join('`%s`' % x['var'] for x in s['slots'])))
    for t in g['typography']:
        sz = t['sizes']
        sizes = (' / '.join(px(sz[k]) for k in ('desktop', 'laptop', 'tablet', 'mobile')) + ' (≥1200 / laptop / tablet / mobil)'
                 if 'laptop' in sz else '%s / %s (mobil CSS)' % (px(sz['desktop']), px(sz['mobile'])))
        extra = ' · harf %s' % t['letterSpacing'] if t.get('letterSpacing') else ''
        rows.append(('typography', t['name'], '%s · %s · %s · satır %s%s' % (
            t['family'] or '?', t['weight'] or 'ağırlık ?', sizes, t['lineHeight'] or '?', extra),
            '`%s` + `%s`%s' % (t['var'], t['fontVar'] or '?', ' · ' + t['source'] if t.get('source') else '')))
    for v in g['globalVariables']:
        rows.append(('globalVariable', v['name'], '%s `%s`' % (v['type'], json.dumps(v['value'], ensure_ascii=False)),
                     ', '.join('`%s`' % x for x in v['vars'])))
    for k in g['keyframes']:
        rows.append(('keyframe', k['name'], '%s → %s' % (k['from'], k['to']), '%s (%s)' % (k['recipe'], ', '.join(k['usedBy']))))
    cnt = collections.Counter(r[0] for r in rows)
    order = ['breakpoint', 'color', 'colorScheme', 'typography', 'globalVariable', 'keyframe']
    out = ['# Globals runbook — %s (%s)' % (name, th['prefix']), '',
           "`port-manifest.json` → `globals` için tek seferlik kurulum. Sıra: oku → tablo → **kullanıcı onayı** → "
           "oluştur → yeniden listele. Bu runbook bir kez çalıştırılır; tekrar çalıştırmak token'ları çoğaltır.", '',
           '## Ön koşullar', '',
           '- `ikas theme dev` çalışıyor ve editör bağlı.',
           "- Oturum `.mcp.json` dosyasını taşıyan tema klasöründen başlatıldı (yoksa ikas MCP araçları görünmez).",
           '- Kod yazılmaz, bileşen düzenlenmez; yalnızca tema global\'leri kurulur.', '',
           '## 1. Oku', '',
           "`list_theme_globals` çağrılır; mevcut her renk, tipografi, kırılım, keyframe, renk şeması ve global "
           "değişken not edilir. Aynı ad ve değerdeki token yeniden kullanılır (`var (aynı)`); aynı ad farklı değer "
           "`çakışma` olur ve açık soru olarak kullanıcıya sorulur, üzerine yazılmaz.", '',
           '## 2. Token tablosu', '',
           'Tür başına sayı: ' + ' · '.join('%s %d' % (k, cnt[k]) for k in order if cnt[k]) + ' · toplam %d.' % len(rows), '',
           '| Tür | Ad | Değer | pen.dev kaynağı | Durum |', '|---|---|---|---|---|']
    for k in order:
        for r in rows:
            if r[0] == k:
                out.append('| %s | %s | %s | %s | _doldurulacak_ |' % (r[0], cell(r[1]), cell(r[2]), cell(r[3])))
    out += ['', '`Durum` adım 1\'den sonra doldurulur: `yeni`, `var (aynı)` ya da `çakışma`.', '',
            '## 3. Onay', '',
            '**KULLANICI ONAYI BEKLE.** Tür başına sayılar ve yukarıdaki tablo kullanıcıya gösterilir. Açık bir '
            '"evet" gelmeden hiçbir `create_theme_global` çağrısı yapılmaz. `çakışma` satırları için karar '
            'kullanıcınındır.', '',
            '## 4. Oluştur', '',
            '`create_theme_global` aşağıdaki sırayla, her satır bir çağrı. Görünen adlar Türkçe `Grup / Ad`.', '']
    payloads = []
    for b in g['breakpoints']:
        payloads.append(('breakpoint', collections.OrderedDict([('kind', 'breakpoint'), ('name', b['name']), ('width', b['width'])])))
    for c in g['colors']:
        if c['ikas']['kind'] == 'color':
            payloads.append(('color', collections.OrderedDict([('kind', 'color'), ('name', c['name']),
                                                              ('value', list(c['values'].values())[0])])))
    for i, s in enumerate(g['colorSchemes']):
        if i == 0:
            cols = [collections.OrderedDict([('newSlotName', x['slot']), ('value', x['value'])]) for x in s['slots']]
        else:
            cols = [collections.OrderedDict([('slotId', '<%s slotId>' % x['slot']), ('value', x['value'])]) for x in s['slots']]
        payloads.append(('colorScheme', collections.OrderedDict([('kind', 'colorScheme'), ('name', s['name']), ('colors', cols)])))
        if i == 0 and len(g['colorSchemes']) > 1:
            payloads.append(('note', "Ara adım: `list_theme_globals` → ilk şemanın slot id'leri okunur; ikinci şema aynı slotlara `slotId` ile bağlanır."))
    for t in g['typography']:
        p = collections.OrderedDict([('kind', 'typography'), ('name', t['name']), ('font_family', t['family']),
                                     ('font_size', px(t['sizes']['desktop']))])
        if t['weight']:
            p['font_weight'] = t['weight']
        if t['lineHeight']:
            p['line_height'] = t['lineHeight']
        if t.get('letterSpacing'):
            p['letter_spacing'] = t['letterSpacing']
        if 'laptop' in t['sizes']:
            bpo = [collections.OrderedDict([('breakpoint_id', '<%s id>' % b['name']), ('font_size', px(t['sizes'][b['id']]))])
                   for b in g['breakpoints'] if b['id'] in t['sizes'] and t['sizes'][b['id']] != t['sizes']['desktop']]
            if bpo:
                p['breakpoints'] = bpo
        payloads.append(('typography', p))
    for v in g['globalVariables']:
        payloads.append(('globalVariable', collections.OrderedDict([('kind', 'globalVariable'), ('display_name', v['name']),
                                                                   ('type', v['type']), ('value', v['value'])])))
    manual = []
    for k in g['keyframes']:
        if k['points']:
            payloads.append(('keyframe', collections.OrderedDict([('kind', 'keyframe'), ('name', k['name']), ('points', k['points'])])))
        else:
            manual.append(k)
    out.append('```json')
    n = 0
    for kind, p in payloads:
        if kind == 'note':
            out += ['```', '', p, '', '```json']
            continue
        n += 1
        out.append(json.dumps(p, ensure_ascii=False))
    out.append('```')
    out += ['', 'Toplam %d çağrı.' % n]
    notes = ['- Kırılımlar ilk sırada: CSS `@media (max-width: bp(<id>))` bunlara dayanır (`var()` medya sorgusunda çalışmaz).']
    if modes and len(g['colorSchemes']) > 1:
        notes.append("- `mode` ekseni → palet başına bir renk şeması. İlk şemadan sonraki her şemadaki `<Slot slotId>` yer tutucuları, "
                     "ilk şemadan sonra yapılan `list_theme_globals` çıktısıyla değiştirilir.")
    if any('laptop' in t['sizes'] for t in g['typography']):
        notes.append('- Tipografi kırılım boyutları (`globals.md` §2a) `breakpoints` dizisiyle aynı çağrıda yazılır; '
                     '`<Kırılım / … id>` yer tutucuları kırılımlar oluşturulduktan sonra `list_theme_globals` çıktısıyla değiştirilir.')
    else:
        notes.append('- Tipografi token\'ları masaüstü boyutunu taşır; mobil boyutlar bileşen CSS\'inde '
                     '`@media (max-width: bp(<mobile id>))` ile verilir. `text-transform` token\'a yazılmaz.')
    dflt = next((s for s in g['colorSchemes'] if s.get('default')), None)
    if dflt:
        notes.append('- Varsayılan şema: `%s` → oluşturulduktan sonra `update_theme_color_scheme` `is_default: true`.' % dflt['name'])
    if g.get('schemeDefaults'):
        notes.append('- Bölümlerin varsayılan şeması (`globals.md` §1a):')
        notes += ['  - %s' % x for x in g['schemeDefaults']]
    upper = [t['name'] for t in g['typography'] if t.get('transform')]
    if upper:
        # 04-ikas-constraints §4: text styles never carry text-transform; the copy itself is upper-case (lang="tr").
        notes.append('- Büyük harf stilleri (' + ', '.join(upper) + '): metin stiline `text_transform` yazılmaz; '
                     'varsayılan metinler büyük harfle girilir, dinamik veri kodda `toLocaleUpperCase("tr-TR")` ile çevrilir.')
    missing_w = [t['name'] for t in g['typography'] if not t['weight']]
    if missing_w:
        notes.append('- Ağırlığı planda olmayan tipografiler (`font_weight` gönderilmez; kullanıcıya sorulur): ' + ', '.join(missing_w) + '.')
    if manual:
        notes.append('- Noktaları otomatik çıkarılamayan keyframe\'ler (alt öğe anahtarları ya da serbest metin); '
                     'noktalar elle yazılır ya da animasyon bileşen CSS\'inde kalır: ' +
                     ', '.join('%s (`%s` → `%s`)' % (k['name'], k['from'], k['to']) for k in manual) + '.')
    out += [''] + notes
    # global.css
    out += ['', '## 5. `src/global.css`', '',
            "Boşluk, ölçü, opaklık ve alfa renkler için ikas'ta tür yok; bunlar `src/global.css` içine yazılır "
            '(MCP çağrısı yapılmaz).', '', '```css', ':root {']
    dev_css, mob_css, alt_css = [], [], []
    for c in g['globalCss']:
        vals = c['values']
        if 'desktop' in vals:
            unit = '' if c['var'].startswith('opacity-') else 'px'
            dv = fmt_num(vals['desktop']) + (unit if vals['desktop'] != 0 else '')
            mv = fmt_num(vals['mobile']) + (unit if vals['mobile'] != 0 else '')
            dev_css.append('  %s: %s;' % (c['css'], dv))
            if mv != dv:
                mob_css.append('    %s: %s;' % (c['css'], mv))
        else:
            vv = list(vals.values())
            dev_css.append('  %s: %s;' % (c['css'], vv[0]))
            if len(vv) > 1 and vv[1] != vv[0]:
                alt_css.append('  %s: %s;' % (c['css'], vv[1]))
    out += dev_css + ['}']
    if mob_css:
        out += ['@media (max-width: bp(<mobile id>)) {', '  :root {'] + mob_css + ['  }', '}']
    if alt_css and len(g['colorSchemes']) > 1:
        out += ['/* %s şemasının className\'i ile */' % g['colorSchemes'][1]['name'], '.<%s className> {' % g['colorSchemes'][1]['mode']] + alt_css + ['}']
    out += ['```', '',
            '## 6. Doğrula', '',
            '`list_theme_globals` yeniden çağrılır; tablodaki her satır tam bir kez bulunmalı. Ardından aşağıdaki canlı '
            'tablo doldurulur. Kod canlı id\'leri yalnızca buradan okur, görünen adlardan değil; `cssVar` dizesi '
            'aynen kopyalanır (büyük/küçük harf id\'den farklı olabilir).', '',
            '## 7. Canlı token tablosu', '',
            '### Renkler (kind: color)', '', '| Token adı | ID | cssVar |', '|---|---|---|']
    out += ['| %s | _doldurulacak_ | _doldurulacak_ |' % c['name'] for c in g['colors'] if c['ikas']['kind'] == 'color'] or ['| — | — | — |']
    out += ['', '### Tipografi (kind: typography)', '', '| Token adı | ID | className |', '|---|---|---|']
    out += ['| %s | _doldurulacak_ | _doldurulacak_ |' % t['name'] for t in g['typography']]
    out += ['', '### Global değişkenler', '', '| Token adı | variableName | Tip |', '|---|---|---|']
    out += ['| %s | _doldurulacak_ | %s |' % (v['name'], v['type']) for v in g['globalVariables']] or ['| — | — | — |']
    out += ['', '### Kırılımlar (kind: breakpoint)', '', '| Token adı | ID | Genişlik | Kullanım |', '|---|---|---|---|']
    out += ['| %s | _doldurulacak_ | %d | `@media (max-width: bp(<id>))` |' % (b['name'], b['width']) for b in g['breakpoints']]
    out += ['', '### Renk şemaları (kind: colorScheme)', '', '| Palet | ID | className |', '|---|---|---|']
    out += ['| %s | _doldurulacak_ | _doldurulacak_ |' % s['name'] for s in g['colorSchemes']]
    out += ['', '| Slot | slotId | cssVar |', '|---|---|---|']
    slots = list(dict.fromkeys(x['slot'] for s in g['colorSchemes'] for x in s['slots']))
    out += ['| %s | _doldurulacak_ | _doldurulacak_ |' % s for s in slots]
    out += ['', "### Keyframe'ler (kind: keyframe)", '', '| Token adı | ID | ref (animation-name) |', '|---|---|---|']
    out += ['| %s | _doldurulacak_ | _doldurulacak_ |' % k['name'] for k in g['keyframes']] or ['| — | — | — |']
    return '\n'.join(out) + '\n'


# ---- main -------------------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(prog='build_manifest.py', description=__doc__.split('\n')[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog='Schema: references/09-handoff.md')
    ap.add_argument('--plandata', required=True, help='plandata directory or single plandata JSON file')
    ap.add_argument('--plan', required=True, help='rendered plan (anim-targets YAML blocks)')
    ap.add_argument('--dump', help='canvas dump with ROOT|... lines (extract_targets.py --js manifest output)')
    ap.add_argument('--globals', help='docs/referans/globals.md: §1a colour schemes and §2a breakpoint text styles '
                                      'override the plandata-derived schemes and type sizes')
    ap.add_argument('-o', '--outdir', required=True, help='output directory (docs/port/)')
    ap.add_argument('--json', action='store_true', help='print one JSON summary object instead of text lines')
    a = ap.parse_args(argv)
    for p in [a.plandata, a.plan] + ([a.dump] if a.dump else []) + ([a.globals] if a.globals else []):
        if not os.path.exists(p):
            print('build_manifest: %s: not found' % p, file=sys.stderr)
            return 2
    try:
        data, origins = G.load_plandata(os.path.abspath(a.plandata))
        cat = G.load_catalogue()
        contract = G.validate(data, origins, cat)
    except G.PlanError as e:
        print(str(e), file=sys.stderr)
        print('build_manifest: plandata invalid', file=sys.stderr)
        return 2
    with open(a.plan, encoding='utf-8') as f:
        plan = L.Plan(a.plan, f.read())
    errs = [(b['line'], e) for b in plan.blocks for e in b.get('errs', [])]
    if errs:
        for ln, e in errs[:10]:
            print('%s: YAML block line %s: %s' % (a.plan, ln, e), file=sys.stderr)
        return 2
    expected = [t['id'] for t in G.Plan(data, cat, contract).targets()]
    got = [t.get('id') for t in plan.targets]
    if sorted(expected) != sorted(str(x) for x in got):
        print('WARN|plan|anim-targets in %s differ from plandata (%d vs %d ids); regenerate the plan with gen_plan.py'
              % (a.plan, len(got), len(expected)), file=sys.stderr)
    roots = None
    if a.dump:
        try:
            roots = parse_dump(a.dump, data['theme']['prefix'])
        except ManifestError as e:
            print(str(e), file=sys.stderr)
            return 2
        if not roots:
            print('build_manifest: %s: no ROOT|%s/... lines' % (a.dump, data['theme']['prefix']), file=sys.stderr)
            return 2
    gmd = parse_globals_md(a.globals) if a.globals else {}
    if a.globals and not gmd:
        print('WARN|globals|%s has no §1a / §2a tables; plandata values are used' % a.globals, file=sys.stderr)
    b = Builder(data, contract, cat, plan, a.plan, roots, gmd)
    m = apply_behaviour(b.build(), load_behaviour())
    os.makedirs(a.outdir, exist_ok=True)
    files = []
    for fn, text in (('port-manifest.json', json.dumps(m, ensure_ascii=False, indent=1) + '\n'),
                     ('port-manifest.md', render_manifest_md(data, m)),
                     ('globals-runbook.md', render_runbook(m)),
                     ('seed-checklist.md', render_seed_md(m))):
        path = os.path.join(a.outdir, fn)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)
        files.append(path)
    oq = m['openQuestions']
    nblock = sum(1 for q in oq if q.get('blocking'))
    counts = collections.OrderedDict([
        ('sections', len(m['sections'])), ('overlays', sum(len(s['overlays']) for s in m['sections']) + len(b.orphans)),
        ('subs', len(m['subComponents'])), ('pages', len(m['pages'])), ('anims', len(m['animTargets'])),
        ('behaviour', len(m['behaviour'])), ('seed', len(m['seed'])),
        ('open', len(oq)), ('blocking', nblock)])
    if a.json:
        print(json.dumps(collections.OrderedDict([('counts', counts), ('openQuestions', oq), ('files', files)]),
                         ensure_ascii=False, indent=1))
    else:
        for q in oq:
            print('Q|%s|%s|%s|%s%s' % (q['id'], q['kind'], q['where'], q['text'].replace('|', '/'),
                                       '|BLOCKING' if q.get('blocking') else ''))
        for p in files:
            print('FILE|%s' % p)
        print('MANIFEST|' + '|'.join('%s=%d' % kv for kv in counts.items()))
    return 1 if nblock else 0


if __name__ == '__main__':
    sys.exit(main())
