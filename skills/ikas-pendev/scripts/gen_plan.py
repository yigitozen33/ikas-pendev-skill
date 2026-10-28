#!/usr/bin/env python3
"""gen_plan.py - render an ikas-pendev design plan (Markdown) from plandata.

Usage:
  python3 gen_plan.py <plandata-dir | plandata.json> [-o OUTDIR] [--stdout] [--validate-only]

Input:
  * a directory holding `theme.json` + `sections/NN-<Key>.json` (one section or
    overlay object per file, rendered in file-name order), or
  * a single JSON file with `sections` inlined.
  Schema: templates/plandata/README.md (schema 1, contract 1|2).

Output:
  OUTDIR/<theme.file> (default OUTDIR: parent of a plandata dir, or the JSON
  file's own directory). Prose comes from templates/plan/*.md; recipe defaults
  from scripts/data/motion-catalogue.json.

  One summary line: `<file> | lines N | targets N | sections N | overlays N | pages N`
  (stdout; stderr when --stdout is used so the plan can be piped).

Exit codes: 0 ok, 1 schema/validation error (messages carry a JSON path), 2 usage/IO error.
Python 3.9+, stdlib only.
"""
import argparse
import collections
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
SKILL = os.path.dirname(HERE)
TPL_DIR = os.path.join(SKILL, 'templates', 'plan')
CATALOGUE = os.path.join(HERE, 'data', 'motion-catalogue.json')

CONTRACT_MARKER = '<!-- ikas-pendev contract:2 -->'

# ---- fixed contract (references/02-contract.md) ---------------------------------
CORE_COLORS = ['color-bg', 'color-text', 'color-muted', 'color-line', 'color-surface', 'color-inverse-bg',
               'color-inverse-text', 'color-accent', 'color-accent-text', 'color-scrim']
CORE_FONTS = ['font-display', 'font-ui', 'font-body', 'font-price', 'font-mono']
CORE_TYPE = ['text-display', 'text-h2', 'text-h3', 'text-h4', 'text-title', 'text-ui', 'text-ui-sm', 'text-badge',
             'text-label', 'text-body', 'text-price']
CORE_NUMBERS = ['space-page', 'space-grid', 'space-card', 'space-panel', 'space-xs', 'space-sm', 'space-md',
                'space-section', 'size-header', 'size-line', 'opacity-inactive']
C2_COLORS = ['color-transparent', 'color-danger', 'color-success']
C2_NUMBERS = ['size-logo']

PROP_TYPES = {'TEXT', 'RICH_TEXT', 'NUMBER', 'NUMBER_RANGE', 'BOOLEAN', 'IMAGE', 'IMAGE_LIST', 'VIDEO', 'SVG',
              'SVG_LIST', 'DATE', 'LINK', 'LIST_OF_LINK', 'COLOR', 'PRODUCT', 'PRODUCT_LIST', 'PRODUCT_ATTRIBUTE',
              'PRODUCT_ATTRIBUTE_LIST', 'CATEGORY', 'CATEGORY_LIST', 'BRAND', 'BRAND_LIST', 'BLOG', 'BLOG_LIST',
              'BLOG_CATEGORY', 'BLOG_CATEGORY_LIST', 'TYPE', 'ENUM', 'COMPONENT', 'COMPONENT_LIST'}
PAGE_TYPES = {'INDEX', 'CATEGORY', 'PRODUCT_DETAIL', 'CART', 'ACCOUNT', 'LOGIN', 'REGISTER', 'FORGOT_PASSWORD',
              'RECOVER_PASSWORD', 'NOT_FOUND', 'BLOG', 'BLOG_POST', 'SEARCH', 'FAVORITES',
              'CUSTOMER_EMAIL_VERIFICATION', 'COLLECTION', 'CUSTOM',
              # remaining IkasThemePageType values
              'PRODUCT', 'BRAND', 'ADDRESSES', 'ORDERS', 'ORDER_DETAIL', 'FAVORITE_PRODUCTS', 'BLOG_INDEX',
              'BLOG_CATEGORY', 'CHECKOUT', 'RAFFLE', 'RAFFLE_DETAIL', 'RAFFLE_ACCOUNT', 'ACTIVATE_CUSTOMER'}
ANIM_KEYS = {'layer', 'recipe', 'trigger', 'what', 'frm', 'to', 'timing', 'impl', 'mobile', 'rm', 'via'}
RECIPE_FIELDS = ('frm', 'to', 'timing', 'impl', 'mobile', 'rm')
FORBIDDEN_IMPL = re.compile(r'\b(gsap|lenis|framer-motion)\b', re.I)
HEX = re.compile(r'^#[0-9A-Fa-f]{6}([0-9A-Fa-f]{2})?$')
PASCAL = re.compile(r'^[A-Z][A-Za-z0-9]*$')
KEBAB = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$')
MODE = re.compile(r'^[a-z][a-z0-9-]*$')  # colour-scheme slug on the pen.dev `mode` axis


class PlanError(Exception):
    pass


# ---- loading ---------------------------------------------------------------------

def _read_json(path):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f, object_pairs_hook=collections.OrderedDict)
    except json.JSONDecodeError as e:
        raise PlanError('%s: invalid JSON: %s' % (path, e))


def load_plandata(src):
    """Return (data, origins). origins[i] names the file section i came from."""
    if os.path.isdir(src):
        theme_path = os.path.join(src, 'theme.json')
        if not os.path.isfile(theme_path):
            raise PlanError('%s: theme.json not found' % src)
        data = _read_json(theme_path)
        if 'sections' in data:
            raise PlanError('%s: $.sections must not be inlined when sections/ is used' % theme_path)
        files = sorted(glob.glob(os.path.join(src, 'sections', '*.json')))
        data['sections'] = []
        origins = []
        for p in files:
            obj = _read_json(p)
            rel = os.path.relpath(p, src)
            m = re.match(r'^\d+-(.+)\.json$', os.path.basename(p))
            if not m:
                raise PlanError('%s: file name must be NN-<Key>.json' % rel)
            if isinstance(obj, dict) and obj.get('key') != m.group(1):
                raise PlanError('%s: $.key %r does not match file name key %r' % (rel, obj.get('key'), m.group(1)))
            data['sections'].append(obj)
            origins.append(rel)
        return data, origins
    data = _read_json(src)
    return data, [None] * len(data.get('sections') or [])


def load_catalogue():
    return _read_json(CATALOGUE)['recipes']


# ---- tiny template engine ----------------------------------------------------------
# {{name}} value · {{#name}}..{{/name}} if truthy · {{^name}}..{{/name}} if falsy.
# A line holding only a section tag is removed together with its newline.

_TPL_CACHE = {}
_STANDALONE = re.compile(r'^[ \t]*(\{\{[#^/]\w+\}\})[ \t]*\n', re.M)
_SECTION = re.compile(r'\{\{([#^])(\w+)\}\}(.*?)\{\{/\2\}\}', re.S)
_VAR = re.compile(r'\{\{(\w+)\}\}')


def template(name):
    if name not in _TPL_CACHE:
        with open(os.path.join(TPL_DIR, name), encoding='utf-8') as f:
            s = f.read()
        if not s.endswith('\n'):
            raise PlanError('template %s must end with a newline' % name)
        _TPL_CACHE[name] = _STANDALONE.sub(r'\1', s[:-1])  # files carry one extra trailing newline
    return _TPL_CACHE[name]


def fill(name, ctx):
    def sections(s):
        def repl(m):
            on = bool(ctx.get(m.group(2)))
            keep = on if m.group(1) == '#' else not on
            return sections(m.group(3)) if keep else ''
        return _SECTION.sub(repl, s)

    def var(m):
        k = m.group(1)
        if k not in ctx:
            raise PlanError('template %s: unknown placeholder {{%s}}' % (name, k))
        v = ctx[k]
        return '' if v is None else str(v)

    return _VAR.sub(var, sections(template(name)))


# ---- validation ------------------------------------------------------------------

def text_of(v):
    """Strings may be given as a string or an array of lines."""
    if isinstance(v, list):
        return '\n'.join(v)
    return v


def word_in(layer, text):
    return re.search(r'(?<![\w-])' + re.escape(layer) + r'(?![\w-])', text) is not None


def validate(d, origins, cat):
    errs = []

    def err(path, msg):
        errs.append('%s: %s' % (path, msg))

    def need(obj, key, path, typ=str, allow_empty=False):
        if not isinstance(obj, dict) or key not in obj or obj[key] is None:
            err(path + '.' + key, 'required')
            return None
        v = obj[key]
        if typ is str and isinstance(v, list) and all(isinstance(x, str) for x in v):
            v = '\n'.join(v)
        if not isinstance(v, typ) or isinstance(v, bool) and typ is not bool:
            err(path + '.' + key, 'expected %s' % typ.__name__)
            return None
        if not allow_empty and typ in (str, list, dict) and not v:
            err(path + '.' + key, 'must not be empty')
        return v

    if not isinstance(d, dict):
        raise PlanError('$: expected object')
    if d.get('schema') != 1:
        err('$.schema', 'must be 1')
    contract = d.get('contract')
    if contract not in (1, 2):
        err('$.contract', 'must be 1 or 2')
        contract = 2
    c2 = contract == 2

    th = need(d, 'theme', '$', dict) or {}
    for k in ('slug', 'name', 'sector', 'title', 'lead', 'codeDir', 'penFile'):
        need(th, k, '$.theme')
    P = need(th, 'prefix', '$.theme') or 'P'
    if not re.match(r'^[A-Z]$', P):
        err('$.theme.prefix', 'must be one letter A-Z')
    if th.get('slug') and not KEBAB.match(th['slug']):
        err('$.theme.slug', 'must be kebab-case')
    if 'file' in th and not re.match(r'^[\w.-]+\.md$', th['file'] or ''):
        err('$.theme.file', 'must be a bare *.md file name')
    ref = th.get('reference', {})
    if not isinstance(ref, dict):
        err('$.theme.reference', 'expected object')
    if c2:
        for k in ('locale', 'currency'):
            need(th, k, '$.theme')

    need(d, 'identity_md', '$')
    modes = d.get('modes')
    if modes is not None and not (isinstance(modes, list) and 2 <= len(modes) <= 4 and len(set(modes)) == len(modes)
                                  and all(isinstance(m, str) and MODE.match(m) for m in modes)):
        err('$.modes', 'must be null or 2-4 distinct colour-scheme slugs, default first (e.g. ["light","dark"])')
        modes = None
    devs = need(d, 'devices', '$', dict) or {}
    for dv in ('desktop', 'mobile'):
        o = devs.get(dv)
        if not isinstance(o, dict) or not all(isinstance(o.get(k), int) for k in ('width', 'height')):
            err('$.devices.' + dv, 'needs integer width and height')

    # variables
    vs = need(d, 'variables', '$', dict) or {}
    colors = vs.get('colors') or {}
    fonts = vs.get('fonts') or {}
    types = vs.get('type') or {}
    nums = vs.get('numbers') or {}
    for k, o in (('colors', colors), ('fonts', fonts), ('type', types), ('numbers', nums)):
        if not isinstance(o, dict) or not o:
            err('$.variables.' + k, 'required object')
    for name, val in colors.items():
        path = '$.variables.colors["%s"]' % name
        vals = val if modes else [val]
        if modes and not (isinstance(val, list) and len(val) == len(modes)):
            err(path, 'expected one value per mode [%s]' % ', '.join(modes))
            continue
        if not modes and not isinstance(val, str):
            err(path, 'expected one hex string (modes is null)')
            continue
        for x in vals:
            if not isinstance(x, str) or not HEX.match(x):
                err(path, 'invalid hex %r' % (x,))
        if c2 and name == 'color-transparent' and not all(isinstance(x, str) and x.upper().endswith('00') and len(x) == 9 for x in vals):
            err(path, 'must be #RRGGBB00')
    for name, val in fonts.items():
        if not isinstance(val, str) or not val:
            err('$.variables.fonts["%s"]' % name, 'expected font family name')
        elif c2 and val in ((d.get('fontCheck') or {}).get('invalid') or []):
            err('$.variables.fonts["%s"]' % name, '%r is listed as invalid in pen.dev' % val)
    for name, val in types.items():
        if not (isinstance(val, list) and len(val) == 2 and all(isinstance(x, (int, float)) for x in val)):
            err('$.variables.type["%s"]' % name, 'expected [desktop, mobile] numbers')
    for name, val in nums.items():
        ok = isinstance(val, (int, float)) and not isinstance(val, bool) or (
            isinstance(val, list) and len(val) == 2 and all(isinstance(x, (int, float)) for x in val))
        if not ok:
            err('$.variables.numbers["%s"]' % name, 'expected a number or [desktop, mobile]')
    required = [('colors', CORE_COLORS + (C2_COLORS if c2 else [])), ('fonts', CORE_FONTS), ('type', CORE_TYPE),
                ('numbers', CORE_NUMBERS + (C2_NUMBERS if c2 else []))]
    for grp, names in required:
        have = {'colors': colors, 'fonts': fonts, 'type': types, 'numbers': nums}[grp]
        for n in names:
            if isinstance(have, dict) and n not in have:
                err('$.variables.%s' % grp, 'missing core variable "%s"%s' % (n, ' (contract 2)' if n in C2_COLORS + C2_NUMBERS else ''))
    if c2 and isinstance(nums.get('size-logo'), (int, float)):
        err('$.variables.numbers["size-logo"]', 'must use the device axis: [desktop, mobile]')

    ts = need(d, 'typeStyles', '$', dict) or {}
    tmap = ts.get('map') if isinstance(ts, dict) else None
    if not isinstance(tmap, list) or not tmap:
        err('$.typeStyles.map', 'required non-empty array')
    else:
        for i, g in enumerate(tmap):
            if not (isinstance(g, dict) and isinstance(g.get('styles'), list) and g['styles'] and isinstance(g.get('spec'), str)):
                err('$.typeStyles.map[%d]' % i, 'needs styles[] and spec')
                continue
            for s in g['styles']:
                if s not in types:
                    err('$.typeStyles.map[%d].styles' % i, 'unknown type variable "%s"' % s)
    fc = need(d, 'fontCheck', '$', dict) or {}
    if not isinstance(fc.get('valid'), list) or not fc.get('valid'):
        err('$.fontCheck.valid', 'required non-empty array')
    if not isinstance(fc.get('invalid', []), list):
        err('$.fontCheck.invalid', 'expected array')
    ds = need(d, 'ds', '$', dict) or {}
    need(ds, 'sampleText', '$.ds')
    need(ds, 'icons', '$.ds')

    # recipes
    local = ((d.get('recipes') or {}).get('local')) or {}
    if not isinstance(local, dict):
        err('$.recipes.local', 'expected object')
        local = {}
    for rid, r in local.items():
        path = '$.recipes.local["%s"]' % rid
        if not re.match(r'^%s-M-\d\d$' % re.escape(P), rid):
            err(path, 'local recipe id must match %s-M-NN' % P)
        for k in ('name', 'what', 'struct') + RECIPE_FIELDS:
            need(r, k, path)
        if isinstance(r, dict) and isinstance(r.get('impl'), str) and FORBIDDEN_IMPL.search(r['impl']):
            err(path + '.impl', 'forbidden library (gsap/lenis/framer-motion)')
    for rid, h in (d.get('stateHints') or {}).items():
        if rid not in cat and rid not in local:
            err('$.stateHints["%s"]' % rid, 'unknown recipe')

    def check_recipe(rid, path):
        if rid in local:
            return
        if rid not in cat:
            err(path, 'unknown recipe "%s"' % rid)
        elif cat[rid].get('forbidden'):
            err(path, 'recipe %s is forbidden: %s' % (rid, cat[rid].get('reason', '')))

    via = d.get('via') or {}
    if not isinstance(via, dict):
        err('$.via', 'expected object {layer: Component}')
    for i, r in enumerate(d.get('viaRules') or []):
        if not (isinstance(r, dict) and all(isinstance(r.get(k), str) for k in ('recipe', 'layerContains', 'via'))):
            err('$.viaRules[%d]' % i, 'needs recipe, layerContains, via')

    def check_anims(anims, path, text):
        if not isinstance(anims, list):
            err(path, 'expected array')
            return
        for j, a in enumerate(anims):
            ap = '%s[%d]' % (path, j)
            a = norm_anim(a)
            if a is None:
                err(ap, 'expected object {layer, recipe, trigger, what, ...overrides} or [layer, recipe, trigger, what, {overrides}]')
                continue
            for k in ('layer', 'recipe', 'trigger', 'what'):
                if not isinstance(a.get(k), str) or not a.get(k):
                    err(ap + '.' + k, 'required string')
            extra = set(a) - ANIM_KEYS
            if extra:
                err(ap, 'unknown keys %s (overrides: frm, to, timing, impl, mobile, rm, via)' % sorted(extra))
            if isinstance(a.get('recipe'), str):
                check_recipe(a['recipe'], ap + '.recipe')
            if isinstance(a.get('layer'), str) and a['layer'] and not word_in(a['layer'], text):
                err(ap + '.layer', 'layer "%s" not found (word boundary) in its tree/structure' % a['layer'])
            if isinstance(a.get('impl'), str) and FORBIDDEN_IMPL.search(a['impl']):
                err(ap + '.impl', 'forbidden library (gsap/lenis/framer-motion)')
        if len(anims) > 99:
            err(path, 'more than 99 targets')

    comps = need(d, 'components', '$', list) or []
    cnames = set()
    for i, c in enumerate(comps):
        path = '$.components[%d]' % i
        if not isinstance(c, dict):
            err(path, 'expected object')
            continue
        n = need(c, 'name', path)
        if n and not PASCAL.match(n):
            err(path + '.name', 'must be PascalCase')
        if n in cnames:
            err(path + '.name', 'duplicate component "%s"' % n)
        cnames.add(n)
        st = need(c, 'structure', path) or ''
        need(c, 'states', path)
        check_anims(c.get('anims', []), path + '.anims', st)
    if c2:
        btn = [c for c in comps if isinstance(c, dict) and c.get('name') == 'Button']
        if not btn:
            err('$.components', 'contract 2 requires a Button component')
        else:
            for s in ('eklendi', 'stok yok'):
                if s not in (text_of(btn[0].get('states')) or ''):
                    err('$.components[Button].states', 'contract 2 requires state "%s"' % s)

    secs = need(d, 'sections', '$', list) or []
    keys, codes = {}, set()
    for i, s in enumerate(secs):
        path = '$.sections[%d]' % i + (' (%s)' % origins[i] if i < len(origins) and origins[i] else '')
        if not isinstance(s, dict):
            err(path, 'expected object')
            continue
        k = need(s, 'key', path)
        if k and not PASCAL.match(k):
            err(path + '.key', 'must be PascalCase')
        if k in keys:
            err(path + '.key', 'duplicate key "%s"' % k)
        code = need(s, 'code', path)
        if code and (not re.match(r'^[A-Z]{2,5}$', code) or code == 'CMP'):
            err(path + '.code', 'must be 2-5 capital letters and not CMP')
        if code in codes:
            err(path + '.code', 'duplicate code "%s"' % code)
        codes.add(code)
        kind = s.get('kind')
        if kind not in ('section', 'overlay'):
            err(path + '.kind', 'must be "section" or "overlay"')
        keys[k] = kind
        for f in ('pages', 'ikas', 'desktop', 'mobile'):
            need(s, f, path)
        if 'props' in s and not isinstance(text_of(s['props']), str):
            err(path + '.props', 'expected string')
        if 'mode' in s and (not modes or s['mode'] not in modes):
            err(path + '.mode', 'must be one of $.modes')
        if 'devices' in s and not (isinstance(s['devices'], list) and s['devices'] and set(s['devices']) <= {'desktop', 'mobile'}):
            err(path + '.devices', 'subset of ["desktop","mobile"]')
        for f in ('desktopOnly', 'desktopOnlyStates'):
            if f in s and not (isinstance(s[f], list) and all(isinstance(x, str) and x.strip() and '`' not in x for x in s[f])):
                err(path + '.' + f, 'expected a list of non-empty strings without backticks')
        for x in s.get('desktopOnly') or []:
            if isinstance(x, str) and not re.match(r'^[a-z][a-z0-9-]*$', x):
                err(path + '.desktopOnly', 'layer name "%s" must be kebab-case' % x)
        tree = s.get('tree')
        if not (isinstance(tree, list) and tree and all(isinstance(x, str) for x in tree)):
            err(path + '.tree', 'required array of lines')
            tree_text = ''
        else:
            tree_text = '\n'.join(tree)
        if not isinstance(s.get('checks', []), list):
            err(path + '.checks', 'expected array')
        check_anims(s.get('anims', []), path + '.anims', tree_text)
        if c2:
            for m in re.finditer(r'\{([A-Za-z_][\w]*):([^}\s]+)\}', tree_text):
                nm, tp = m.groups()
                if nm == 'data':
                    if not re.match(r'^[a-z][A-Za-z0-9]*(\.[A-Za-z0-9]+)+$', tp):
                        err(path + '.tree', '{data:%s}: source must look like product.name' % tp)
                elif nm == 'code':
                    pass
                elif tp not in PROP_TYPES:
                    err(path + '.tree', '{%s:%s}: unknown prop type' % (nm, tp))
            if kind == 'section' and 'backgroundColor' not in (text_of(s.get('props')) or ''):
                err(path + '.props', 'contract 2 sections must list the `backgroundColor` COLOR prop')
    if c2 and keys.get('FilterDrawer') != 'overlay':
        err('$.sections', 'contract 2 requires overlay "FilterDrawer" (P/Overlay/FilterDrawer@mobile)')
    if c2 and keys.get('QuickBuy') != 'overlay':
        err('$.sections', 'contract 2 requires overlay "QuickBuy" (P/Overlay/QuickBuy@desktop + @mobile, see 06-page-coverage.md §3a)')

    pages = need(d, 'pages', '$', list) or []
    for i, p in enumerate(pages):
        path = '$.pages[%d]' % i
        if not isinstance(p, dict):
            err(path, 'expected object')
            continue
        need(p, 'name', path)
        comp = need(p, 'sections', path) or ''
        for tok in page_sections(comp):
            if keys.get(tok) != 'section':
                err(path + '.sections', '"%s" is not a section key (pages hold Section instances only)' % tok)
        pt = p.get('pageType')
        if pt is not None and pt not in PAGE_TYPES:
            err(path + '.pageType', 'unknown ikas page type "%s"' % pt)
        if c2 and pt is None:
            err(path + '.pageType', 'required in contract 2')
        for j, e in enumerate(p.get('expand') or []):
            if not (isinstance(e, dict) and isinstance(e.get('name'), str) and e.get('pageType') in PAGE_TYPES):
                err('%s.expand[%d]' % (path, j), 'needs name and a valid pageType')
    if d.get('spacing') is not None:
        import spacing as SP
        errs.extend(SP.validate(d['spacing'], (d.get('variables') or {}).get('numbers') or {}))
    if d.get('sampleCatalog') is not None:
        import sample_catalog
        errs.extend(sample_catalog.validate(d['sampleCatalog']))
    if errs:
        raise PlanError('\n'.join(errs))
    return contract


def page_sections(comp):
    out = []
    for tok in comp.split(' · '):
        tok = re.sub(r'\s*\([^)]*\)', '', tok).strip()
        if tok:
            out.append(tok)
    return out


def norm_anim(a):
    if isinstance(a, dict):
        return dict(a)
    if isinstance(a, list) and 4 <= len(a) <= 5 and all(isinstance(x, str) for x in a[:4]):
        o = dict(zip(('layer', 'recipe', 'trigger', 'what'), a[:4]))
        if len(a) == 5:
            if not isinstance(a[4], dict):
                return None
            o.update(a[4])
        return o
    return None


# ---- rendering -------------------------------------------------------------------

class Plan:
    def __init__(self, d, cat, contract):
        self.d = d
        self.c2 = contract == 2
        self.th = d['theme']
        self.P = self.th['prefix']
        self.file = self.th.get('file') or 'plan-%s-%s.md' % (self.P, self.th['slug'])
        self.local = (d.get('recipes') or {}).get('local') or {}
        self.recipes = {k: v for k, v in cat.items() if not v.get('forbidden')}
        self.recipes.update(self.local)
        self.via = d.get('via') or {}
        self.via_rules = d.get('viaRules') or []
        self.modes = d.get('modes')
        self.devs = d['devices']

    def rkey(self, rid):
        return (rid in self.local, rid)

    def via_for(self, a):
        if 'via' in a:
            return a['via'] or None
        v = self.via.get(a['layer'])
        if v:
            return v
        for r in self.via_rules:
            if a['recipe'] == r['recipe'] and r['layerContains'] in a['layer']:
                return r['via']
        return None

    def targets(self):
        out = []
        for sec in self.d['sections']:
            for i, a in enumerate(sec.get('anims', []), 1):
                a = norm_anim(a)
                base = {k: self.recipes[a['recipe']][k] for k in RECIPE_FIELDS}
                base.update({k: a[k] for k in RECIPE_FIELDS if k in a})
                out.append(dict(id='%s-%s-%02d' % (self.P, sec['code'], i), section=sec['key'], layer=a['layer'],
                                via=self.via_for(a), recipe=a['recipe'], trigger=a['trigger'], what=a['what'], **base))
        n = 0
        for c in self.d['components']:
            for a in c.get('anims', []):
                n += 1
                a = norm_anim(a)
                base = {k: self.recipes[a['recipe']][k] for k in RECIPE_FIELDS}
                base.update({k: a[k] for k in RECIPE_FIELDS if k in a})
                out.append(dict(id='%s-CMP-%02d' % (self.P, n), section='Sub/' + c['name'], layer=a['layer'],
                                via=a.get('via') or None, recipe=a['recipe'], trigger=a['trigger'], what=a['what'], **base))
        return out

    def yaml_block(self, ts):
        L = ['<!-- anim-targets:start -->', '```yaml']
        for t in ts:
            L.append('- id: %s' % t['id'])
            L.append('  section: %s' % t['section'])
            L.append('  layer: %s' % t['layer'])
            if t['via']:
                L.append('  via: %s' % t['via'])
            L.append('  recipe: %s' % t['recipe'])
            L.append('  trigger: %s' % t['trigger'])
            if self.c2:
                L.append('  what: %s' % json.dumps(t['what'], ensure_ascii=False))
            else:
                L.append('  what: "%s"' % t['what'])
            L.append('  from: %s' % t['frm'])
            L.append('  to: %s' % t['to'])
            L.append('  timing: %s' % t['timing'])
            L.append('  impl: %s' % t['impl'])
            L.append('  mobile: %s' % t['mobile'])
            L.append('  reducedMotion: %s' % t['rm'])
            L.append('  done: false')
        L += ['```', '<!-- anim-targets:end -->']
        return '\n'.join(L)

    def mode_rule(self):
        """Canvas rule for the `mode` axis: which value a non-default colour scheme's root carries."""
        modes = self.modes
        if not modes:
            return ''
        if len(modes) == 2:
            label = {'dark': 'koyu', 'light': 'açık'}.get(modes[1], '`%s`' % modes[1])
            return '%s bölümlerde ayrıca `mode: "%s"` (varsayılan `mode: "%s"`)' % (label, modes[1], modes[0])
        alts = ' · '.join('`mode: "%s"`' % m for m in modes[1:])
        return 'diğer şemalardaki bölümlerde ayrıca kendi şemaları (%s) (varsayılan `mode: "%s"`)' % (alts, modes[0])

    def variables_js(self):
        v = self.d['variables']
        L = ['SetVariables({']
        for k, val in v['colors'].items():
            if self.modes:
                parts = ', '.join('{value:"%s", theme:{mode:"%s"}}' % (x, m) for x, m in zip(val, self.modes))
                L.append('  "%s": {type:"color", value:[%s]},' % (k, parts))
            else:
                L.append('  "%s": {type:"color", value:"%s"},' % (k, val))
        for k, val in v['fonts'].items():
            L.append('  "%s": {type:"string", value:"%s"},' % (k, val))
        dev = '  "%s": {type:"number", value:[{value:%s, theme:{device:"desktop"}}, {value:%s, theme:{device:"mobile"}}]},'
        for k, (dv, mv) in v['type'].items():
            L.append(dev % (k, dv, mv))
        for k, val in v['numbers'].items():
            if isinstance(val, list) and val[0] != val[1]:
                L.append(dev % (k, val[0], val[1]))
            else:
                L.append('  "%s": {type:"number", value:%s},' % (k, val[0] if isinstance(val, list) else val))
        L.append('})')
        return '\n'.join(L)

    def ctx(self, ts):
        th, d = self.th, self.d
        ref = th.get('reference') or {}
        ts_map = d['typeStyles']
        styles = ' · '.join(', '.join('`%s`' % s for s in g['styles']) + ' → ' + g['spec'] for g in ts_map['map'])
        note = ts_map.get('note')
        fc = d['fontCheck']
        ucomp = (d.get('utils') or {}).get('viaComponents')
        if not ucomp:
            seen = []
            for x in list(self.via.values()) + [r['via'] for r in self.via_rules]:
                if x not in seen:
                    seen.append(x)
            ucomp = seen
        extra = (d.get('utils') or {}).get('extra') or []
        overlays = []
        for s in d['sections']:
            if s['kind'] == 'overlay':
                for dv in s.get('devices') or ['desktop', 'mobile']:
                    overlays.append('- `%s/Overlay/%s@%s — <durum>`' % (self.P, s['key'], dv))
        modes = self.modes
        return {
            'c1': not self.c2, 'c2': self.c2,
            'prefix': self.P, 'slug': th['slug'], 'name': th['name'], 'sector': th['sector'], 'file': self.file,
            'penFile': th['penFile'], 'codeDir': th['codeDir'], 'locale': th.get('locale', ''),
            'currency': th.get('currency', ''), 'reference_url': ref.get('url', ''),
            'canvasImportNote': ref.get('canvasImportNote', ''), 'policy': ref.get('policy', ''),
            'identity_md': text_of(d['identity_md']).strip('\n'),
            'modes': bool(modes), 'mode_rule': self.mode_rule(), 'mode_axis': ' | '.join(modes or []),
            'dw': self.devs['desktop']['width'], 'dh': self.devs['desktop']['height'],
            'mw': self.devs['mobile']['width'], 'mh': self.devs['mobile']['height'],
            'vars_intro': d['variables'].get('intro', ''), 'variables_js': self.variables_js(),
            'font_valid': ', '.join('`%s`' % f for f in fc['valid']),
            'font_invalid': ', '.join('`%s`' % f for f in fc.get('invalid') or []),
            'type_styles': styles + '.' + (' ' + note if note else ''),
            'type_count': len(d['variables']['type']),
            'ds_sample': d['ds']['sampleText'], 'ds_icons': d['ds']['icons'], 'ds_imagery': d['ds'].get('imagery', ''),
            'via_components': ', '.join('`%s`' % x for x in ucomp),
            'utils_rows': ''.join('| %s | %s | %s |\n' % (r['part'], r['path'], r['targets']) for r in extra),
            'contextScan': True if self.c2 else d.get('contextScan', True),
            'target_count': len(ts),
            'overlay_list': '\n'.join(overlays),
        }

    def render(self):
        d, P = self.d, self.P
        ts = self.targets()
        by_sec = collections.OrderedDict()
        for t in ts:
            by_sec.setdefault(t['section'], []).append(t)
        c = self.ctx(ts)
        out = []
        out.append('# ' + self.th['title'] + ('\n' + CONTRACT_MARKER if self.c2 else '') + '\n')
        out.append(fill('00-baslik.md', c))
        out.append(self.th['lead'] + '\n')
        out.append(fill('00-kullanim.md', c))
        out.append(fill('01-kimlik.md', c))
        out.append(fill('02-canvas.md', c))
        out.append(fill('03-degiskenler.md', c))
        if self.c2 and d.get('spacing'):
            import spacing as SP
            out.append('### 3b. Boşluk sistemi\n')
            out.append('Roller sabit, her rolün token\'ı ve değeri bu temanın (`02-contract.md` §3b). Bölüm, sayfa ve sütun '
                       'aralıkları yalnız bu tablodan gelir; CHK `spacing` canvas\'ı bu blokla karşılaştırır.\n')
            out.append(SP.markdown(d['spacing']))
            out.append(SP.block(d['spacing']))
        out.append(fill('04-adlandirma.md', c))
        out.append(fill('05-anim-kurallari.md', c))
        if self.local:
            out.append(fill('05-1-tarifler.md', c))
            for rid, r in self.local.items():
                out.append('| **%s** | %s | %s `%s → %s`, `%s` | %s | %s | %s | %s |' % (
                    rid, r['name'], r['what'], r['frm'], r['to'], r['timing'], r['struct'], r['impl'], r['mobile'], r['rm']))
            out.append('')

        # 6
        out.append(fill('06-0-ds.md', c))
        out.append(fill('06-1-bilesenler.md', c))
        for comp in d['components']:
            out.append('| `%s` | %s | %s |' % (comp['name'], text_of(comp['structure']), text_of(comp['states'])))
        out.append('')
        if self.c2:
            out.append(fill('06-1-zorunlu.md', c))
        cmp_ts = [t for t in ts if t['section'].startswith('Sub/')]
        if cmp_ts:
            out.append(fill('06-1-hedefler.md', c))
            out.append(self.yaml_block(cmp_ts) + '\n')

        out.append(fill('06-2-bolumler.md', c))
        for sec in d['sections']:
            kind = {'section': 'Section', 'overlay': 'Overlay'}[sec['kind']]
            out.append('#### %s/%s' % (kind, sec['key']))
            out.append('- **Kullanıldığı yer:** %s' % sec['pages'])
            out.append('- **ikas:** %s' % sec['ikas'])
            if sec.get('props'):
                out.append("- **Prop'lar:** %s" % text_of(sec['props']))
            if self.c2 and sec.get('mode'):
                out.append('- **Mod:** `mode: "%s"`' % sec['mode'])
            out.append('- **Desktop:** %s' % text_of(sec['desktop']).strip())
            out.append('- **Mobil:** %s' % text_of(sec['mobile']).strip())
            if sec.get('desktopOnly'):
                out.append('- **Yalnız masaüstü katmanlar:** %s' % ', '.join('`%s`' % x for x in sec['desktopOnly']))
            if sec.get('desktopOnlyStates'):
                out.append('- **Yalnız masaüstü durumlar:** %s' % ', '.join('`%s`' % x for x in sec['desktopOnlyStates']))
            out.append('\n```\n' + '\n'.join(sec['tree']).strip('\n') + '\n```\n')
            if sec.get('checks'):
                out.append('Kontrol: ' + ' · '.join(sec['checks']) + '\n')
            st = by_sec.get(sec['key'], [])
            if st:
                out.append(self.yaml_block(st) + '\n')

        out.append(fill('06-3-sayfalar.md', c))
        for p in d['pages']:
            if self.c2:
                pts = [e['pageType'] for e in p.get('expand') or []] or [p['pageType']]
                out.append('| `%s` | %s | %s |' % (p['name'], p['sections'], ', '.join('`%s`' % x for x in pts)))
            else:
                out.append('| `%s` | %s |' % (p['name'], p['sections']))
        out.append('')
        out.append(fill('06-4-overlay.md', c))
        out.append(fill('06-5-motion-states.md', c))
        hints = {k: v['stateHint'] for k, v in self.recipes.items() if v.get('stateHint')}
        hints.update(d.get('stateHints') or {})
        order = sorted(k for k in hints if k not in self.local) + [k for k in self.local if k in hints]
        seen = set()
        for rec in order:
            for t in sorted(ts, key=lambda t: t['frm'] != self.recipes[t['recipe']]['frm']):
                if t['recipe'] == rec and rec not in seen and not t['section'].startswith('Sub/'):
                    seen.add(rec)
                    out.append('| %s | %s (`%s`) | %s |' % (rec, t['section'], t['layer'], hints[rec]))
        out.append('')

        if self.c2 and d.get('sampleCatalog'):
            import sample_catalog as SC
            cat = d['sampleCatalog']
            out.append('### 6.6 Örnek katalog\n')
            out.append('Canvas\'taki her ürün verisi (ad, marka, görsel, fiyat, kademe, seçenek sınırı) ve örnek sepet bu tablodan gelir; '
                       'bir ürün kartta, PDP\'de, QuickBuy\'da, sepette ve hesapta aynıdır. Ürünü gösteren her kap (kart, satır, PDP ve QuickBuy kökü) '
                       '`context`\'ine `seed <anahtar>` yazar; CHK `seed` bu blokla karşılaştırır (`02-contract.md` §5c).\n')
            out.append(SC.markdown(cat))
            out.append('<!-- sample-catalog:start -->\n```json\n' + json.dumps(SC.expectations(cat), ensure_ascii=False, sort_keys=True)
                       + '\n```\n<!-- sample-catalog:end -->\n')

        # 7
        out.append(fill('07-ozet.md', c))
        for k, v in by_sec.items():
            recs = sorted(set(t['recipe'] for t in v), key=self.rkey)
            out.append('| %s | %d | %s | `%s` … `%s` |' % (k, len(v), ', '.join(recs), v[0]['id'], v[-1]['id']))
        out.append('')
        out.append(fill('07-1-tarifler.md', c))
        cnt = collections.Counter(t['recipe'] for t in ts)
        for rec in sorted(cnt, key=self.rkey):
            out.append('| %s | %d | %s |' % (rec, cnt[rec], self.recipes[rec]['impl']))
        out.append('')
        out.append(fill('08-aktarim.md', c))
        out.append(fill('09-kontrol.md', c))
        text = '\n'.join(out).replace('\n\n\n', '\n\n') + '\n'
        n_sec = sum(1 for s in d['sections'] if s['kind'] == 'section')
        n_ovl = sum(1 for s in d['sections'] if s['kind'] == 'overlay')
        n_pages = sum(len(p.get('expand') or []) or 1 for p in d['pages'])
        stats = dict(lines=text.count('\n'), targets=len(ts), sections=n_sec, overlays=n_ovl, pages=n_pages)
        return text, stats


def main(argv=None):
    ap = argparse.ArgumentParser(prog='gen_plan.py', description=__doc__.split('\n')[0],
                                 epilog='Schema: templates/plandata/README.md')
    ap.add_argument('plandata', help='plandata directory (theme.json + sections/) or a single plandata JSON file')
    ap.add_argument('-o', '--outdir', help='output directory (default: parent of a plandata dir / dir of the JSON file)')
    ap.add_argument('--stdout', action='store_true', help='write the plan to stdout (summary goes to stderr)')
    ap.add_argument('--validate-only', action='store_true', help='validate plandata and exit')
    a = ap.parse_args(argv)
    src = os.path.abspath(a.plandata)
    if not os.path.exists(src):
        print('gen_plan: %s: not found' % a.plandata, file=sys.stderr)
        return 2
    try:
        data, origins = load_plandata(src)
        cat = load_catalogue()
        contract = validate(data, origins, cat)
        if a.validate_only:
            print('VALID contract:%d sections:%d components:%d pages:%d' % (
                contract, len(data['sections']), len(data['components']), len(data['pages'])))
            return 0
        plan = Plan(data, cat, contract)
        text, st = plan.render()
    except PlanError as e:
        print(str(e), file=sys.stderr)
        print('gen_plan: plandata invalid', file=sys.stderr)
        return 1
    summary = '%s | lines %d | targets %d | sections %d | overlays %d | pages %d' % (
        '%s', st['lines'], st['targets'], st['sections'], st['overlays'], st['pages'])
    if a.stdout:
        sys.stdout.write(text)
        sys.stdout.flush()
        print(summary % plan.file, file=sys.stderr)
        return 0
    outdir = a.outdir or os.path.dirname(src)  # dir input: its parent; file input: its own dir
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, plan.file)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    print(summary % path)
    return 0


if __name__ == '__main__':
    sys.exit(main())
