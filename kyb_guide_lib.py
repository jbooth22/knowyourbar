#!/usr/bin/env python3
"""
Shared helpers for KnowYourBar guide-page build scripts.

HOW GUIDE BUILDS WORK (since 2026-09-23)
----------------------------------------
A build script does NOT regenerate the whole page. It opens the LIVE page
(e.g. clean-protein-bars.html), and rewrites only the regions wrapped in
marker comments:

    <!-- kyb:NAME -->  ...generated content...  <!-- /kyb:NAME -->

Everything outside the markers (nav, footer, fonts, canonical link, static
copy, inline JS) is left exactly as it is on the live page, so hand fixes to
the page shell survive every rebuild. Everything inside the markers comes
from bars.js. A missing marker is a hard error, never a silent skip.

Also rewritten outside markers (targeted, one pattern each):
  - every JSON-LD "dateModified" value (set to the build date)
  - the footer "Updated YYYY-MM-DD" stamp

Row, expand-panel and lazy-load JSON formats match the live guide pages
(the compact one-line expand panel used on clean-protein-bars.html).
"""
import json, re, datetime, html as html_mod
from collections import defaultdict

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
def load_bars(path='bars.js'):
    with open(path, encoding='utf-8') as f:
        content = f.read()
    return json.loads(content[content.index('['):content.rindex(']') + 1])

def num(v):
    try:
        if v is None or v == '':
            return None
        return float(v)
    except (TypeError, ValueError):
        return None

def fnum(n):
    """12.0 -> '12', 12.5 -> '12.5', None -> ''."""
    if n is None:
        return ''
    n = round(n, 1)
    if abs(n - round(n)) < 1e-9:
        return str(int(round(n)))
    return f'{n:.1f}'

def esc(s):
    if s is None:
        return ''
    return html_mod.escape(str(s), quote=True)

def ingr(b):
    return (b.get('Ingredients') or '').strip()

def tags(b):
    si = b.get('score_insights') or ''
    return set(p.split(':')[0].strip() for p in si.split('|') if p.strip())

def has_tag(b, tag):
    return tag in tags(b)

def net_carbs(b):
    c = num(b.get('Total Carbohydrates (g)'))
    if c is None:
        return None
    return c - (num(b.get('Dietary Fiber (g)')) or 0) - (num(b.get('Sugar Alcohol (g)')) or 0)

MALTITOL_FAMILY = ['maltitol', 'polyglycitol', 'hydrogenated starch hydrolysate']
def has_maltitol_family(b):
    t = ingr(b).lower()
    return any(k in t for k in MALTITOL_FAMILY)

def p100(b):
    p, c = num(b.get('Protein (g)')), num(b.get('Calories'))
    if not p or not c:
        return None
    return round(p / c * 100, 1)

def score(b):
    return num(b.get('ingredient_score'))

def pct(n, d):
    return round(100 * n / d, 1) if d else 0.0

def top_level_ingredient_count(text):
    """Count comma-separated ingredients at parenthesis/bracket depth 0."""
    if not text:
        return 0
    depth, count, seen = 0, 1, False
    for ch in text:
        if ch in '([':
            depth += 1
        elif ch in ')]':
            depth = max(0, depth - 1)
        elif ch == ',' and depth == 0:
            count += 1
        if not ch.isspace():
            seen = True
    return count if seen else 0

# ---------------------------------------------------------------------------
# Canonical guide filters (GUIDE_CRITERIA.md). Used for a page's own
# qualifying set AND for cross-link counts on other guides' cards, so a
# count quoted on one page always matches the page it links to.
# ---------------------------------------------------------------------------
def _yes(field):
    return lambda b: b.get(field) == 'Yes'

# Sugar alcohol screen used by No Sugar Alcohols and GLP-1 (2026-09-24): reads the
# INGREDIENT LIST, not the Sugar Alcohol (g) line, because many labels list a sugar
# alcohol but declare 0g or leave the line off. A bar counts as containing one if
# the scorer tagged it (maltitol, erythritol, sorbitol, xylitol, isomalt, ...) or
# its label names isomalto-oligosaccharides (IMO), which the No Sugar Alcohols
# guide screens alongside true sugar alcohols.
IMO_RX = re.compile(r'isomalto|\bimo\b(?!\s+free)', re.I)

def has_sugar_alcohol(b):
    return has_tag(b, 'Sugar Alcohols') or bool(IMO_RX.search(ingr(b)))

# Label checks Jeff has reviewed and confirmed (KYB_data_worklist, 2026-09-24).
# The guide builds skip their ingredient-vs-flag WARNING for these, so a
# confirmed bar doesn't keep showing up as a problem. Key: (brand, flavor, flag).
REVIEWED_OK = {
    ('FITCRUNCH', 'Chocolate Peanut Butter', 'gluten free'),   # "The Gluten Free label is correct"
    ('Fro Pro', 'Sweet Coconut', 'dairy free'),                 # "No change needed"
    # ('Fro Pro', 'Cookies and Cream', 'soy free') removed 2026-09-30: Jeff took the Soy Free label off in the database.
}

def reviewed_ok(b, flag):
    return (b['Brand Name'], b['Flavor Name'], flag) in REVIEWED_OK

GUIDE_FILTERS = {
    'no-sugar-alcohols': lambda b: not has_sugar_alcohol(b),
    'no-artificial-sweeteners': lambda b: not has_tag(b, 'Artificial Sweeteners'),
    'no-seed-oils': lambda b: not has_tag(b, 'Processed Oils'),
    'clean-protein-bars': lambda b: b.get('score_band') in ('A', 'B')
        and not has_tag(b, 'Artificial Sweeteners') and not has_tag(b, 'Processed Oils'),
    'low-sugar-high-protein': lambda b: (num(b.get('Sugars (g)')) is not None and num(b.get('Sugars (g)')) <= 5
        and (num(b.get('Protein (g)')) or 0) >= 15),
    'best-bars-for-diabetics': lambda b: (num(b.get('Sugars (g)')) is not None and num(b.get('Sugars (g)')) <= 5
        and net_carbs(b) is not None and net_carbs(b) <= 10
        and (num(b.get('Dietary Fiber (g)')) or 0) >= 5 and (num(b.get('Protein (g)')) or 0) >= 10
        and b.get('score_band') in ('A', 'B') and not has_maltitol_family(b)),
    'glp1-protein-bars': lambda b: ((num(b.get('Protein (g)')) or 0) >= 15
        and num(b.get('Calories')) is not None and num(b.get('Calories')) <= 200
        and num(b.get('Sugars (g)')) is not None and num(b.get('Sugars (g)')) <= 4
        and (num(b.get('Dietary Fiber (g)')) or 0) >= 3
        and (num(b.get('Sugar Alcohol (g)')) or 0) == 0 and not has_sugar_alcohol(b)
        and b.get('score_band') in ('A', 'B')),
    'keto-protein-bars': lambda b: (net_carbs(b) is not None and net_carbs(b) <= 8
        and (num(b.get('Protein (g)')) or 0) >= 10 and (num(b.get('Total Fat (g)')) or 0) >= 8
        and not has_maltitol_family(b)),
    'caffeine-protein-bars': lambda b: (num(b.get('Caffeine (mg)')) or 0) > 0,
    'creatine-protein-bars': lambda b: (num(b.get('Creatine (g)')) or 0) > 0,   # any declared amount (live page definition)
    'vegan-protein-bars': _yes('Vegan (Y/N)'),
    'gluten-free-protein-bars': _yes('Gluten Free (Y/N)'),
    'dairy-free-protein-bars': _yes('Dairy Free (Y/N)'),
    'soy-free-protein-bars': _yes('Soy Free (Y/N)'),
    'kosher-protein-bars': _yes('Kosher (Y/N)'),
    'high-fiber-protein-bars': lambda b: (num(b.get('Dietary Fiber (g)')) or 0) >= 11,
}

def guide_count(bars, slug):
    f = GUIDE_FILTERS[slug]
    return sum(1 for b in bars if f(b))

# ---------------------------------------------------------------------------
# Grades, certs, links
# ---------------------------------------------------------------------------
BAND_ORDER = ['A', 'B', 'C', 'D', 'F']
GRADE_WORD = {'A': 'Clean', 'B': 'Good', 'C': 'Okay', 'D': 'Poor', 'F': 'Avoid'}

def grade_word(band):
    return GRADE_WORD.get(band, '')

def grade_badge(band):
    return f'<span class="table-grade-badge grade-{band}">{band}</span>'

def grade_range(bars):
    """(best, worst) band present, e.g. ('A', 'C')."""
    present = [g for g in BAND_ORDER if any(b.get('score_band') == g for b in bars)]
    if not present:
        return None, None
    return present[0], present[-1]

def grade_range_html(best, worst):
    """Always best-to-worst (BRIEFING locked convention)."""
    if best is None:
        return ''
    if best == worst:
        return grade_badge(best)
    return f'{grade_badge(best)}<span class="grade-range-sep">&ndash;</span>{grade_badge(worst)}'

CERT_ORDER = [
    ('Kosher (Y/N)', 'Kosher'),
    ('Vegan (Y/N)', 'Vegan'),
    ('Non-GMO (Y/N)', 'Non-GMO'),
    ('Soy Free (Y/N)', 'Soy Free'),
    ('Dairy Free (Y/N)', 'Dairy Free'),
    ('Gluten Free (Y/N)', 'Gluten Free'),
    ('Nut Free (Y/N)', 'Nut Free'),
]

def cert_list(b):
    return [label for field, label in CERT_ORDER if b.get(field) == 'Yes']

def cert_badges_html(b):
    certs = cert_list(b)
    out = ''.join(f'<span class="cert-badge">{esc(c)}</span>' for c in certs[:2])
    if len(certs) > 2:
        out += f'<span class="cert-badge-more">+{len(certs) - 2}</span>'
    return out

def _url(v):
    """A real outbound URL or ''. Guards against Y/N flags leaking into
    link slots (QA.md 2026-08-19 incident)."""
    if isinstance(v, str) and v.startswith('http'):
        return v
    return ''

AMAZON_BLOCK = set()   # ASINs a page build has chosen not to link (see block_shared_asins)

def _asin(u):
    m = re.search(r'/dp/([A-Z0-9]{10})', u or '')
    return m.group(1) if m else None

def block_shared_asins(all_bars):
    """Opt-in per page: stop linking any Amazon ASIN that bars.js assigns to
    more than one bar, since it can't be trusted to land on the right flavor.
    Returns the set of blocked ASINs."""
    from collections import Counter
    c = Counter(_asin(b.get('Amazon Affiliate')) for b in all_bars)
    AMAZON_BLOCK.update(a for a, n in c.items() if a and n > 1)
    return set(AMAZON_BLOCK)

def amazon_url(b):
    u = _url(b.get('Amazon Affiliate'))
    return '' if u and _asin(u) in AMAZON_BLOCK else u

def website_url(b):
    # Never Custom Referral Link: it is a Y/N flag, not a URL.
    return _url(b.get('Website'))

def buy_links_html(b):
    out = ''
    az, ws = amazon_url(b), website_url(b)
    if az:
        out += f'<a href="{esc(az)}" target="_blank" rel="noopener sponsored" class="amazon-link">Shop on Amazon</a>'
    if ws:
        out += f'<a href="{esc(ws)}" target="_blank" rel="noopener" class="visit-link">Shop on Brand Site</a>'
    return out

# ---------------------------------------------------------------------------
# Macro-rank grid (ranked against the FULL database at build time)
# ---------------------------------------------------------------------------
RANK_METRICS = [  # key, field, label, unit, direction
    ('p', 'Protein (g)', 'Protein', 'g', 'highest'),
    ('c', 'Calories', 'Calories', '', 'highest'),
    ('s', 'Sugars (g)', 'Sugar', 'g', 'lowest'),
    ('f', 'Dietary Fiber (g)', 'Fiber', 'g', 'highest'),
    ('ft', 'Total Fat (g)', 'Fat', 'g', None),
]

class Ranker:
    def __init__(self, bars):
        self.total = len(bars)
        self._cache = {}
        self.bars = bars

    def rank(self, b, field, direction):
        v = num(b.get(field))
        if v is None:
            return None
        key = (field, direction)
        if key not in self._cache:
            vals = [num(x.get(field)) for x in self.bars if num(x.get(field)) is not None]
            self._cache[key] = vals
        vals = self._cache[key]
        if direction == 'lowest':
            return 1 + sum(1 for x in vals if x < v)
        return 1 + sum(1 for x in vals if x > v)

    def tag(self, b, field, direction):
        r = self.rank(b, field, direction or 'highest')
        if r is None:
            return ['N/A', 'rank-gray']
        if direction is None:
            return [f'#{r} of {self.total}', 'rank-gray']
        share = r / self.total
        if share <= 0.10:
            cls = 'rank-green'
        elif share <= 0.25:
            cls = 'rank-amber'
        else:
            return [f'#{r} of {self.total}', 'rank-gray']
        return [f'#{r} {direction}', cls]

# ---------------------------------------------------------------------------
# Bar list rows (live guide format)
# ---------------------------------------------------------------------------
NUTR_FIELDS = [
    ('Calories', 'Calories', ''),
    ('Protein (g)', 'Protein', 'g'),
    ('Total Fat (g)', 'Total Fat', 'g'),
    ('Saturated Fat (g)', 'Saturated Fat', 'g'),
    ('Trans Fat (g)', 'Trans Fat', 'g'),
    ('Cholesterol (mg)', 'Cholesterol', 'mg'),
    ('Sodium (mg)', 'Sodium', 'mg'),
    ('Total Carbohydrates (g)', 'Total Carbs', 'g'),
    ('Dietary Fiber (g)', 'Dietary Fiber', 'g'),
    ('Sugars (g)', 'Sugars', 'g'),
    ('Sugar Alcohol (g)', 'Sugar Alcohol', 'g'),
    ('Potassium (mg)', 'Potassium', 'mg'),
    ('Calcium (mg)', 'Calcium', 'mg'),
    ('Iron (mg)', 'Iron', 'mg'),
]

def nutr_pairs(b):
    out = []
    for field, label, unit in NUTR_FIELDS:
        v = num(b.get(field))
        # Live format: a missing value shows as 0 (matches the live pages).
        out.append([label, f'{fnum(v) if v is not None else "0"}{unit}'])
    return out

CHIP_CLASS = {'positive': 'chip-positive', 'concern': 'chip-concern', 'neutral': 'chip-neutral'}

def chips(b):
    out = []
    for part in (b.get('score_insights') or '').split('|'):
        part = part.strip()
        if not part:
            continue
        bits = part.split(':')
        out.append([bits[0].strip(), CHIP_CLASS.get(bits[1].strip() if len(bits) > 1 else 'neutral', 'chip-neutral')])
    return out

def ingr_items(raw):
    items = [x.strip().title() for x in (raw or '').split(',') if x.strip()]
    return items or ['None flagged']

def score_split(b):
    pos = num(b.get('score_pos')) or 0
    neg = num(b.get('score_neg')) or 0
    tot = pos + abs(neg)
    pp = round(100 * pos / tot) if tot else 100
    return pos, neg, pp, 100 - pp

def bar_row_html(b, idx):
    grade = b.get('score_band')
    sc = score(b) or 0
    prot, cal = num(b.get('Protein (g)')), num(b.get('Calories'))
    p = p100(b) or 0
    search = f"{b['Brand Name']} {b['Flavor Name']}".lower()
    return f'''<tr class="bar-row" data-idx="{idx}" data-score="{fnum(sc)}" data-grade="{grade}" data-protein="{fnum(prot or 0)}" data-cal="{fnum(cal or 0)}" data-sugar="{fnum(num(b.get('Sugars (g)')) or 0)}" data-p100="{fnum(p)}" data-search="{esc(search)}" onclick="toggleIngr({idx}, this)">
  <td class="col-bar">
    <div class="bar-brand">{esc(b['Brand Name'])}</div>
    <div class="bar-flavor">{esc(b['Flavor Name'])}</div>
    <svg class="row-expand-icon" width="7" height="12" viewBox="0 0 7 12" fill="none"><path d="M1 1L6 6L1 11" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
  </td>
  <td class="col-num col-hide-mobile">{fnum(cal)}</td>
  <td class="col-num">{fnum(prot)}</td>
  <td class="col-num col-hide-mobile">{fnum(p)}</td>
  <td class="col-num">{fnum(num(b.get('Total Fat (g)')))}</td>
  <td class="col-num col-hide-mobile">{fnum(num(b.get('Total Carbohydrates (g)')))}</td>
  <td class="col-num">{fnum(num(b.get('Dietary Fiber (g)')))}</td>
  <td class="col-num">{fnum(num(b.get('Sugars (g)')))}</td>
  <td class="col-num col-hide-mobile">{fnum(num(b.get('Sugar Alcohol (g)')) or 0)}</td>
<td class="col-certs col-hide-mobile"><div class="cert-badges">{cert_badges_html(b)}</div></td>
  <td class="col-grade"><span class="table-grade-badge grade-{grade}" title="{grade_word(grade)} &middot; score {fnum(sc)}">{grade}</span></td>
</tr>'''

def lazy_record(b, idx, ranker):
    pos, neg, pp, npc = score_split(b)
    return {
        'i': idx,
        'sz': b.get('Size') or 'Standard',
        'ty': b.get('Type') or 'Bar',
        'sv': fnum(num(b.get('Serving Size (g)'))),
        'ct': cert_list(b),
        'az': amazon_url(b),
        'ws': website_url(b),
        'rk': {k: ranker.tag(b, field, d) for k, field, _l, _u, d in RANK_METRICS},
        'pv': num(b.get('Protein (g)')) or 0,
        'cv': fnum(num(b.get('Calories'))),
        'sv2': fnum(num(b.get('Sugars (g)'))),
        'fv': fnum(num(b.get('Dietary Fiber (g)'))),
        'ftv': num(b.get('Total Fat (g)')) or 0,
        'nu': nutr_pairs(b),
        'gr': b.get('score_band'),
        'gl': grade_word(b.get('score_band')),
        'sc': fnum(score(b) or 0),
        'pp': pp,
        'np': npc,
        'ps': fnum(pos),
        'ns': fnum(neg),
        'ch': chips(b),
        'pi': ingr_items(b.get('positive_ingredients')),
        'ni': ingr_items(b.get('concern_ingredients')),
        'ing': ingr(b),
    }

def expand_html(r):
    """Server-rendered expand panel. Mirrors buildLazyExpand() in the page's
    inline JS exactly, from the same record, so eager and lazy rows match."""
    buy = ''
    if r['az']:
        buy += f'<a href="{esc(r["az"])}" target="_blank" rel="noopener sponsored" class="amazon-link">Shop on Amazon</a>'
    if r['ws']:
        buy += f'<a href="{esc(r["ws"])}" target="_blank" rel="noopener" class="visit-link">Shop on Brand Site</a>'
    rk = r['rk']
    def cell(lbl, val, pair):
        return (f'<div class="macro-rank-cell"><span class="macro-rank-lbl">{lbl}</span>'
                f'<span class="macro-rank-val">{val}</span><span class="macro-rank-tag {pair[1]}">{pair[0]}</span></div>')
    ranks = (cell('Protein', f'{fnum(r["pv"])}g', rk['p']) + cell('Calories', r['cv'], rk['c'])
             + cell('Sugar', f'{r["sv2"]}g', rk['s']) + cell('Fiber', f'{r["fv"]}g', rk['f'])
             + cell('Fat', f'{fnum(r["ftv"])}g', rk['ft']))
    nutr = ''.join(f'<div class="nutr-row"><span class="nutr-label">{a}</span><span class="nutr-val">{v}</span></div>' for a, v in r['nu'])
    chip_html = ''.join(f'<span class="insight-chip {c}">{esc(n)}</span>' for n, c in r['ch'])
    pos_i = ''.join(f'<div class="ingr-col-item">{esc(x)}</div>' for x in r['pi'])
    neg_i = ''.join(f'<div class="ingr-col-item">{esc(x)}</div>' for x in r['ni'])
    certs = f'<div class="expand-certs-line">Certifications: {esc(", ".join(r["ct"]))}</div>' if r['ct'] else ''
    return (f'<div class="expand-meta">{esc(r["sz"])} &middot; {esc(r["ty"])} &middot; {r["sv"]}g serving</div>'
            f'{certs}<div class="expand-buy-row">{buy}</div><div class="macro-rank-grid">{ranks}</div>'
            f'<div class="expand-columns"><div class="nutr-panel"><div class="nutr-panel-title">Nutrition Facts</div>{nutr}</div>'
            f'<div class="expand-right"><div class="score-tile score-band-{r["gr"]}"><div class="score-tile-header">'
            f'<div class="score-grade-block"><div class="score-header-label">Ingredient Quality Grade</div>'
            f'<div class="score-grade-row"><span class="score-band-badge">{r["gr"]}</span><span class="score-band-label">{r["gl"]}</span></div></div>'
            f'<div class="score-num-block"><div class="score-header-label">Ingredient Quality Score</div><div class="score-number">{r["sc"]}</div></div></div>'
            f'<div class="score-breakdown"><div class="score-breakdown-bar"><div class="sbd-pos" style="width:{r["pp"]}%"></div><div class="sbd-neg" style="width:{r["np"]}%"></div></div>'
            f'<div class="score-breakdown-labels"><span class="sbd-label-pos">+{r["ps"]} positive</span><span class="sbd-label-neg">{r["ns"]} concerns</span></div></div>'
            f'<div class="score-chips">{chip_html}</div><div class="score-ingr-cols">'
            f'<div class="ingr-col"><div class="ingr-col-label ingr-col-pos">Positive Ingredients</div>{pos_i}</div>'
            f'<div class="ingr-col"><div class="ingr-col-label ingr-col-neg">Concern Ingredients</div>{neg_i}</div></div></div>'
            f'<div class="ingr-block"><div class="ingr-label">Ingredients</div><div class="ingr-text">{esc(r["ing"])}</div></div></div></div>')

def sort_for_list(bars):
    # score 0.0 is a real score: never use `score(b) or -999` here (0.0 is falsy)
    return sorted(bars, key=lambda b: (-(score(b) if score(b) is not None else -999), b['Brand Name'].lower(), b['Flavor Name'].lower()))

def bar_table(bars, all_bars, eager=30, variant=None):
    """Returns (tbody_inner_html, lazy_json_text) for a guide's bar list.
    First `eager` rows get a server-rendered expand panel, the rest load
    from the gd-bar-data JSON block on first click. variant='keto' uses the
    Keto page's columns (FAT + NET CARB instead of CAL + SGR) and its
    Fat / Protein / Net Carbs / Fiber rank grid, matching that page's JS."""
    ranker = Ranker(all_bars)
    row_fn, exp_fn, span = bar_row_html, expand_html, 11
    if variant == 'keto':
        ncv = [net_carbs(x) for x in all_bars if net_carbs(x) is not None]
        row_fn, exp_fn, span = keto_row_html, keto_expand_html, 10
    elif variant == 'fiber':
        row_fn, span = fiber_row_html, 10
    rows, lazy = [], []
    for idx, b in enumerate(sort_for_list(bars)):
        rec = lazy_record(b, idx, ranker)
        if variant == 'keto':
            nc = net_carbs(b)
            r_ = 1 + sum(1 for x in ncv if x < nc)
            share = r_ / ranker.total
            rec['ncv'] = fnum(nc)
            rec['rk']['nc'] = ([f'#{r_} lowest', 'rank-green'] if share <= 0.10 else
                               [f'#{r_} lowest', 'rank-amber'] if share <= 0.25 else [f'#{r_} of {ranker.total}', 'rank-gray'])
        rows.append(row_fn(b, idx))
        if idx < eager:
            rows.append(f'<tr class="ingr-row" id="ingr-{idx}"><td colspan="{span}" class="ingr-cell"><div class="expand-content">{exp_fn(rec)}</div></td></tr>')
        else:
            rows.append(f'<tr class="ingr-row" id="ingr-{idx}" style="display:none;"><td colspan="{span}" class="ingr-cell"><div class="expand-content" data-pending="1"></div></td></tr>')
            lazy.append(rec)
    js = json.dumps(lazy, separators=(',', ':')).replace('</', '<\\/')
    return '\n'.join(rows), js

# ---------------------------------------------------------------------------
# Brand tables: Consider / Mixed / Avoid (BRIEFING, locked 2026-08-19)
# ---------------------------------------------------------------------------
def brand_split(all_bars, qualifies):
    by = defaultdict(list)
    for b in all_bars:
        by[b['Brand Name']].append(b)
    rows = []
    for brand, bars in by.items():
        qual = [b for b in bars if qualifies(b)]
        disq = [b for b in bars if not qualifies(b)]
        rows.append(dict(brand=brand, bars=bars, qual=qual, disq=disq,
                         total=len(bars), q=len(qual), d=len(disq)))
    consider = [r for r in rows if r['q'] / r['total'] >= 0.75 and r['d'] <= 2]
    avoid = [r for r in rows if r['d'] / r['total'] >= 0.80 and r['q'] < 3]
    taken = {r['brand'] for r in consider} | {r['brand'] for r in avoid}
    mixed = [r for r in rows if r['q'] >= 3 and r['d'] >= 3 and r['brand'] not in taken]
    consider.sort(key=lambda r: (-r['q'], r['brand'].lower()))
    avoid.sort(key=lambda r: (-r['d'], r['brand'].lower()))
    mixed.sort(key=lambda r: (-r['total'], r['brand'].lower()))
    return consider, mixed, avoid

def avg(bars, field):
    vals = [num(b.get(field)) or 0 for b in bars]
    return sum(vals) / len(vals) if vals else 0

# ---------------------------------------------------------------------------
# Page regions
# ---------------------------------------------------------------------------
def replace_region(page, name, content):
    start, end = f'<!-- kyb:{name} -->', f'<!-- /kyb:{name} -->'
    i, j = page.find(start), page.find(end)
    if i == -1 or j == -1 or j < i or page.count(start) != 1 or page.count(end) != 1:
        raise SystemExit(f'ERROR: marker kyb:{name} missing or duplicated in page. Not writing.')
    return page[:i + len(start)] + '\n' + content + '\n' + page[j:]

def stamp_dates(page, today):
    page, n = re.subn(r'"dateModified":\s*"\d{4}-\d{2}-\d{2}"', f'"dateModified": "{today}"', page)
    page = re.sub(r'(Updated )\d{4}-\d{2}-\d{2}(</div>)', rf'\g<1>{today}\g<2>', page)
    return page

def today_iso():
    return datetime.date.today().isoformat()

def month_year():
    return datetime.date.today().strftime('%B %Y')

def faq_jsonld(faqs):
    """faqs: list of (question_text, answer_text) plain text."""
    data = {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
        {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in faqs]}
    return '  <script type="application/ld+json">\n  ' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + '\n  </script>'

def faq_html(faqs):
    return '\n'.join(f'<div class="faq-item">\n  <button class="faq-q">{esc(q)}</button>\n  <div class="faq-a">{esc(a)}</div>\n</div>' for q, a in faqs)

# ---------------------------------------------------------------------------
# QA: grade-sync check (SCORING_V12_SPEC Part E)
# ---------------------------------------------------------------------------
def grade_sync_check(page, all_bars):
    """Every bar row's grade and score on the page must match bars.js.
    Checks bar rows (data-grade/data-score/title), server-rendered expand
    panels, and the lazy gd-bar-data JSON records. Returns a list of
    mismatch strings (empty = pass)."""
    by_name = {}
    for b in all_bars:
        by_name[(esc(b['Brand Name']), esc(b['Flavor Name']))] = b
    problems = []
    rows = re.findall(r'<tr class="bar-row" data-idx="(\d+)" data-score="([^"]*)" data-grade="([^"]*)".*?'
                      r'<div class="(?:bar-brand|bar-flavor)">(.*?)</div>\s*<div class="(?:bar-flavor|bar-flavor-name)">(.*?)</div>.*?'
                      r'title="(\w+) &middot; score ([^"]*)">(\w)</span>', page, re.S)
    idx_to_bar = {}
    for idx, dsc, dgr, brand, flavor, word, tsc, badge in rows:
        b = by_name.get((brand, flavor))
        if b is None:
            problems.append(f'row {idx}: {brand} | {flavor} not found in bars.js')
            continue
        idx_to_bar[int(idx)] = b
        want_g, want_s = b.get('score_band'), fnum(score(b))
        if not (dgr == badge == want_g and word == grade_word(want_g)):
            problems.append(f'row {idx}: {brand} | {flavor} grade {dgr}/{badge} vs bars.js {want_g}')
        if not (dsc == tsc == want_s):
            problems.append(f'row {idx}: {brand} | {flavor} score {dsc}/{tsc} vs bars.js {want_s}')
    # server-rendered expand panels
    for idx, gr, sc in re.findall(r'<tr class="ingr-row" id="ingr-(\d+)"><td[^>]*><div class="expand-content">.*?score-band-badge">(\w)</span>.*?score-number">([^<]*)<', page):
        b = idx_to_bar.get(int(idx))
        if b and (gr != b.get('score_band') or sc != fnum(score(b))):
            problems.append(f'expand {idx}: {gr} {sc} vs bars.js {b.get("score_band")} {fnum(score(b))}')
    # lazy JSON
    m = re.search(r'<script id="gd-bar-data" type="application/json">(.*?)</script>', page, re.S)
    if m:
        for r in json.loads(m.group(1)):
            b = idx_to_bar.get(r['i'])
            if b is None:
                problems.append(f'lazy {r["i"]}: no matching bar row')
            elif r['gr'] != b.get('score_band') or r['sc'] != fnum(score(b)):
                problems.append(f'lazy {r["i"]}: {r["gr"]} {r["sc"]} vs bars.js {b.get("score_band")} {fnum(score(b))}')
    # pick tiles: brand + flavor + badge
    for brand, flavor, gr in re.findall(r'<div class="pick-tile-brand">(.*?)</div>\s*<div class="pick-tile-flavor-name">(.*?)</div>.*?table-grade-badge grade-(\w)"', page, re.S):
        b = by_name.get((brand, flavor))
        if b is None:
            problems.append(f'pick tile: {brand} | {flavor} not found in bars.js')
        elif b.get('score_band') != gr:
            problems.append(f'pick tile: {brand} | {flavor} grade {gr} vs bars.js {b.get("score_band")}')
    return problems, len(rows)


# ===========================================================================
# Guide page kit (added 2026-09-23 for the free-from guides). Shared pieces
# every TEMPLATE_GUIDE page build uses, so each page script only holds its
# own copy and page-specific sections.
# ===========================================================================
import sys as _sys

class Claims:
    """Collects copy claims that no longer hold. check() returns the bool so
    a sentence can be dropped or reworded instead of failing, when safe."""
    def __init__(self):
        self.failed = []
    def check(self, ok, claim):
        if not ok:
            self.failed.append(claim)
        return bool(ok)
    def stop_if_failed(self):
        if self.failed:
            print('COPY NEEDS REVIEW, page not written. These claims are no longer true in bars.js:')
            for c in self.failed:
                print('  -', c)
            _sys.exit(1)

def names_and(xs):
    xs = list(xs)
    if not xs:
        return ''
    return xs[0] if len(xs) == 1 else ', '.join(xs[:-1]) + (',' if len(xs) > 2 else '') + ' and ' + xs[-1]

_NUM_WORDS = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten']
def num_word(n):
    return _NUM_WORDS[n] if 0 <= n < len(_NUM_WORDS) else str(n)

def P(b): return num(b.get('Protein (g)')) or 0
def CAL(b): return num(b.get('Calories')) or 0
def FIB(b): return num(b.get('Dietary Fiber (g)')) or 0
def SUG(b): return num(b.get('Sugars (g)')) if num(b.get('Sugars (g)')) is not None else 99
def SA(b): return num(b.get('Sugar Alcohol (g)')) or 0
def nm(b): return b['Flavor Name']
def full(b): return f"{b['Brand Name']} {b['Flavor Name']}"
def has_ing(b, word): return word in ingr(b).lower()
def g1(x): return '0.0' if round(x, 1) == 0 else f'{x:.1f}'
def comma(n): return f'{n:,}'
# Public copy never states the exact database size (BRIEFING: always "1,000+"),
# so it can't go stale or disagree between pages after a monthly bars.js update.
# Exact counts are still used for every percentage and every sub-count.
DB_PUBLIC = '1,000+'
def of_db(n, total, the=False):
    """'613 of 1,000+' or '613 of the 1,000+'. When n is 1,000 or more,
    '1,205 of 1,000+' reads wrong, so it becomes a share: '92% of 1,000+'."""
    lead = f'{round(100 * n / total)}%' if n >= 1000 else comma(n)
    return f"{lead} of {'the ' if the else ''}{DB_PUBLIC}"
def a_an(grade): return 'an' if grade in ('A', 'F') else 'a'
def name_key(b): return (b['Brand Name'].lower(), b['Flavor Name'].lower())

class Picker:
    """Top-pick selection per GUIDE_CRITERIA.md 'Top Picks Selection': every
    tile comes from the best grade band present in the qualifying set, ties
    broken on a real guide-specific number (never raw ingredient score), no
    bar repeats. A protein floor (default 10g) applies unless nothing in the
    band clears it."""
    def __init__(self, qualify, floor=10, diverse=False):
        self.qualify = qualify
        self.diverse, self.used_brands = diverse, set()
        self.band_grade = next(g for g in BAND_ORDER if any(b.get('score_band') == g for b in qualify))
        self.band = [b for b in qualify if b.get('score_band') == self.band_grade]
        self.floor, self.used = floor, set()

    def pick(self, sort_key, eligible=lambda b: True):
        # best band first; only when it has nothing eligible left, fall back
        # to the next band down (GUIDE_CRITERIA: tiny qualifying sets)
        bands = [self.band] + [[b for b in self.qualify if b.get('score_band') == g]
                               for g in BAND_ORDER[BAND_ORDER.index(self.band_grade) + 1:]]
        for pool in bands:
            for floor in (self.floor, 0):
                c = [b for b in pool if b['Key'] not in self.used and eligible(b) and P(b) >= floor]
                if c and self.diverse:
                    # optional: among bars tied on the tile's own number, prefer a
                    # brand not already shown (never trades away a better value)
                    k0 = min(tuple(sort_key(x))[0] for x in c)
                    tied = [b for b in c if tuple(sort_key(b))[0] == k0]
                    fresh = [b for b in tied if b['Brand Name'] not in self.used_brands]
                    c = fresh or c
                if c:
                    b = min(c, key=lambda x: (tuple(sort_key(x)), name_key(x)))
                    self.used.add(b['Key'])
                    self.used_brands.add(b['Brand Name'])
                    return b
        return None

    def rank_sum(self, metrics, eligible=lambda b: True, tiebreak=lambda b: -P(b)):
        """Balanced pick: lowest summed rank across metrics [(fn, higher_is_better)]
        within the band's eligible bars."""
        pool = [b for b in self.band if eligible(b) and b['Key'] not in self.used]
        def rank(fn, hi, b): return 1 + sum(1 for x in pool if (fn(x) > fn(b) if hi else fn(x) < fn(b)))
        return self.pick(lambda b: (sum(rank(fn, hi, b) for fn, hi in metrics), tiebreak(b)),
                         lambda b: b in pool)

    def balanced(self):
        """15g+ protein, 5g+ fiber, 5g or less sugar; best combined rank."""
        ok = lambda b: P(b) >= 15 and FIB(b) >= 5 and SUG(b) <= 5
        pool = [b for b in self.band if ok(b)]
        if not pool:
            return self.pick(lambda b: (SUG(b), -P(b)))
        def rank(vals, v, hi): return 1 + sum(1 for x in vals if (x > v if hi else x < v))
        key = lambda b: (rank([P(x) for x in pool], P(b), True) + rank([FIB(x) for x in pool], FIB(b), True)
                         + rank([SUG(x) for x in pool], SUG(b), False), -P(b))
        return self.pick(key, ok)

    def min_in_band(self, fn):
        vals = [fn(b) for b in self.band if P(b) >= self.floor]
        return min(vals) if vals else None

def add_sugar_tradeoff(picks, whole_fruit_label=None):
    """picks: list of [label, bar, reason]. Appends one tradeoff sentence to
    the pick with the most sugar (if over 5g), else notes a 15+ ingredient label."""
    mx = max(SUG(p[1]) for p in picks)
    for p in picks:
        b = p[1]
        n = top_level_ingredient_count(ingr(b))
        if SUG(b) == mx and SUG(b) > 5:
            p[2] += f" The tradeoff is sugar: {fnum(SUG(b))}g, the highest of these {num_word(len(picks))} picks" + \
                    (", all from whole fruit." if whole_fruit_label and p[0] == whole_fruit_label else ".")
        elif n >= 15:
            p[2] += f" The tradeoff is a long label: {n} ingredients."
    return picks

def pick_tile_html(label, b, reason):
    g = b.get('score_band')
    return f'''<div class="macro-card pick-tile">
  <div class="pick-tile-body">
    <div class="pick-tile-category">{esc(label)}</div>
    <div class="pick-tile-brand">{esc(b['Brand Name'])}</div>
    <div class="pick-tile-flavor-name">{esc(b['Flavor Name'])}</div>
    <p class="pick-tile-reason">{esc(reason)}</p>
  </div>
  <div class="pick-tile-footer">
    <div class="pick-tile-quality">
      <span class="pick-tile-quality-label">Ingredient Quality</span>
      <span class="table-grade-badge grade-{g}">{g}</span>
      <span class="pick-tile-quality-word">{grade_word(g)}</span>
    </div>
    <div class="bar-links">{buy_links_html(b)}</div>
  </div>
</div>'''

def picks_section_html(h2, intro, picks):
    tiles = '\n'.join(pick_tile_html(*p) for p in picks)
    return f'''<div class="section-inner">
      <h2 class="section-title">{esc(h2)}</h2>
      <p class="section-body">{esc(intro)}</p>
      <div class="macro-grid pick-tile-grid top-picks-6">
{tiles}
</div>
    </div>'''

def found_in_html(bars_hit, label='Found in:', empty='No bars in the current database'):
    names = sorted({b['Brand Name'] for b in bars_hit})
    if not names:
        return f'<div class="oil-card-brands"><span class="oil-card-brands-label">{label}</span> {esc(empty)}</div>'
    first, rest = names[:4], names[4:]
    out = f'<div class="oil-card-brands"><span class="oil-card-brands-label">{label}</span> {esc(", ".join(first))}'
    if rest:
        out += (f' <details class="oil-card-more"><summary><span class="oil-card-more-text">and {len(rest)} more</span>'
                f'<span class="oil-card-less-text">Hide</span></summary><span class="oil-card-more-list">, {esc(", ".join(rest))}</span></details>')
    return out + '</div>'

def score_card_html(label, bars_hit, total, desc, found_label='Found in:'):
    return f'''<div class="score-card">
          <div class="score-card-label">{esc(label)}</div>
          <div class="score-card-val">{len(bars_hit)} bars<span class="oil-card-pct">{pct(len(bars_hit), total)}%</span></div>
          <div class="score-card-desc">{esc(desc)}</div>
          {found_in_html(bars_hit, found_label)}
        </div>'''

def findings_html(h2, big_num, big_head, big_detail, insights):
    items = ''.join(f'<div class="insight-item"><div class="insight-dot"></div><div class="insight-head">{esc(h)}</div>'
                    f'<div class="insight-detail">{esc(d)}</div></div>' for h, d in insights)
    return f'''<div class="findings-inner">
      <h2 class="findings-title">{esc(h2)}</h2>
      <div class="big-stat">
        <div class="big-stat-num">{esc(big_num)}</div>
        <div>
          <div class="big-stat-head">{esc(big_head)}</div>
          <div class="big-stat-detail">{esc(big_detail)}</div>
        </div>
      </div>
      <div class="insights-grid">
        {items}
      </div>
    </div>'''

def brand_tables_html(split, qualifies, *, h2, intro, table_id, consider_note, avoid_note, mixed_note,
                      avoid_head, avoid_last_head, avoid_last, mixed_head, pick_word='clean pick',
                      consider_all='Clean across its whole lineup',
                      consider_some='{q} of {total} flavors qualify, close enough to call clean',
                      pick_head='Clean Pick', second_avg=('Avg Sugar', 'Sugars (g)'), avoid_label='Brands to Avoid'):
    """Consider / Avoid / Mixed tables (BRIEFING locked rule, see brand_split).
    Consider shows total flavors; Avoid shows disqualified/total with a
    per-brand 'what disqualifies it' cell; Mixed shows qualifying/total and the
    best qualifying flavor (best band, then most protein)."""
    consider, mixed, avoid = split
    def gcell(r):
        best, worst = grade_range(r['bars'])
        return grade_range_html(best, worst)
    def cells(r, count):
        return (f'<td>{count}</td><td>{gcell(r)}</td><td>{fnum(avg(r["bars"], "Protein (g)"))}g</td>'
                f'<td>{fnum(avg(r["bars"], second_avg[1]))}g</td>')
    def jump(brand):
        return f'<button type="button" class="brand-jump" data-brand="{esc(brand)}">{esc(brand)}</button>'
    def cpick(r):
        band = next(g for g in BAND_ORDER if any(b.get('score_band') == g for b in r['qual']))
        return min((b for b in r['qual'] if b.get('score_band') == band), key=lambda b: (-P(b), name_key(b)))
    c_rows = '\n'.join(
        f'<tr><td>{jump(r["brand"])}</td>{cells(r, r["total"])}<td>'
        + (consider_all if r['d'] == 0 else consider_some.format(q=r['q'], total=r['total'])) + '</td></tr>'
        for r in consider)
    a_rows = '\n'.join(
        (f'<tr class="avoid-row brand-row-hidden" style="display:none;">' if i >= 15 else '<tr class="avoid-row">')
        + f'<td><span class="brand-name-static">{esc(r["brand"])}</span></td>' + cells(r, str(r['d']) + '/' + str(r['total']))
        + f'<td>{esc(avoid_last(r))}</td></tr>' for i, r in enumerate(avoid))
    m_rows = '\n'.join(
        f'<tr><td>{jump(r["brand"])}</td>' + cells(r, str(r['q']) + '/' + str(r['total']))
        + f'<td>{esc(cpick(r)["Flavor Name"])} is the {pick_word}</td></tr>' for r in mixed)
    hidden = max(0, len(avoid) - 15)
    more = '' if not hidden else f'''
        <button type="button" class="brand-table-show-more" id="{table_id}-avoid-show-more" data-hidden-count="{hidden}">Show {hidden} more brands</button>
        <script>
        (function() {{
          var btn = document.getElementById('{table_id}-avoid-show-more');
          var table = document.getElementById('{table_id}-avoid-table');
          if (!btn || !table) return;
          btn.addEventListener('click', function() {{
            table.querySelectorAll('.brand-row-hidden').forEach(function(row) {{ row.style.display = ''; row.classList.remove('brand-row-hidden'); }});
            btn.classList.add('is-hidden');
          }});
        }})();
        </script>'''
    head = ('<thead><tr><th>Brand</th><th>{}</th><th>Ingredient Quality</th><th>Avg Protein</th><th>'
            + esc(second_avg[0]) + '</th><th>{}</th></tr></thead>')
    def block(cls, label, note, thead, rows, tid='', extra=''):
        return f'''      <div class="brand-table-block">
        <div class="brand-table-label {cls}">{label}</div>
        <div class="brand-table-note">{esc(note)}</div>
        <div class="table-scroll">
          <table class="brand-table"{tid}>
            {thead}
            <tbody>
{rows}
</tbody>
          </table>
        </div>{extra}
      </div>'''
    return f'''<div class="section-inner">
      <h2 class="section-title">{esc(h2)}</h2>
      <div class="section-body">
        <p>{esc(intro)}</p>
      </div>

{block('pro', 'Brands to Consider', consider_note, head.format('Total Flavors', 'Note'), c_rows)}

{block('con', esc(avoid_label), avoid_note, head.format(esc(avoid_head), esc(avoid_last_head)), a_rows, f' id="{table_id}-avoid-table"', more)}

{block('mixed', 'Mixed Lineups, Check the Flavor', mixed_note, head.format(esc(mixed_head), esc(pick_head)), m_rows)}
    </div>'''

def guide_head_regions(*, title, h1, desc, og_desc, url, about, published, faqs, picks):
    article = {'@context': 'https://schema.org', '@type': 'Article', 'headline': h1, 'description': desc, 'url': url,
               'image': 'https://knowyourbar.com/bar_hero.png', 'datePublished': published, 'dateModified': today_iso(),
               'author': {'@type': 'Organization', 'name': 'Know Your Bar', 'url': 'https://knowyourbar.com'},
               'publisher': {'@type': 'Organization', 'name': 'Know Your Bar', 'url': 'https://knowyourbar.com'},
               'mainEntityOfPage': {'@type': 'WebPage', '@id': url}, 'about': {'@type': 'Thing', 'name': about}}
    crumbs = {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': 1, 'name': 'Know Your Bar', 'item': 'https://knowyourbar.com'},
        {'@type': 'ListItem', 'position': 2, 'name': 'Lifestyle Guides', 'item': 'https://knowyourbar.com'},
        {'@type': 'ListItem', 'position': 3, 'name': h1, 'item': url}]}
    items = {'@context': 'https://schema.org', '@type': 'ItemList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i + 1, 'name': full(p[1])} for i, p in enumerate(picks)]}
    def ld(d, indent=2):
        return ('<script type="application/ld+json">\n  ' + json.dumps(d, indent=indent, ensure_ascii=False).replace('\n', '\n  ')
                + '\n  </script>') if indent else ('<script type="application/ld+json">\n  ' + json.dumps(d, ensure_ascii=False, separators=(',', ':')) + '\n  </script>')
    social = f'''<meta property="og:type" content="article">
  <meta property="og:site_name" content="Know Your Bar">
  <meta property="og:title" content="{esc(h1)}">
  <meta property="og:description" content="{esc(og_desc)}">
  <meta property="og:url" content="{url}">
  <meta property="og:image" content="https://knowyourbar.com/bar_hero.png">

  <!-- Twitter card -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(h1)} | Know Your Bar">
  <meta name="twitter:description" content="{esc(og_desc)}">
  <meta name="twitter:image" content="https://knowyourbar.com/bar_hero.png">'''
    return [('head-meta', f'  <title>{esc(title)}</title>\n  <meta name="description" content="{esc(desc)}">'),
            ('jsonld-article', ld(article)), ('jsonld-breadcrumb', ld(crumbs)), ('jsonld-faq', faq_jsonld(faqs).strip()),
            ('jsonld-itemlist', ld(items, None)), ('social', social)]

def guide_list_regions(qualify, all_bars, *, heading, eager=30, lazy_attr=False, variant=None):
    rows, js = bar_table(qualify, all_bars, eager=eager, variant=variant)
    if lazy_attr:
        rows = re.sub(r' style="display:none;"><td colspan="(\d+)" class="ingr-cell"><div class="expand-content" data-pending="1">',
                      r' style="display:none;" data-lazy="1"><td colspan="\1" class="ingr-cell"><div class="expand-content" data-pending="1">', rows)
    n = len(qualify)
    return [('list-heading', f'<h2 class="section-title">{esc(heading)}</h2>'),
            ('result-count', f'<div class="gd-result-count" id="gd-result-count">Showing {min(30, n)} of {comma(n)} bars</div>'),
            ('bar-rows', rows),
            ('bar-data', f'<script id="gd-bar-data" type="application/json">{js}</script>')]

def build_guide_page(page_path, regions, qualify, all_bars, claims):
    claims.stop_if_failed()
    page = open(page_path, encoding='utf-8').read()
    for name, content in regions:
        page = replace_region(page, name, content)
    page = stamp_dates(page, today_iso())
    problems, n_rows = grade_sync_check(page, all_bars)
    if n_rows != len(qualify):
        problems.append(f'bar rows on page {n_rows} != qualifying bars {len(qualify)}')
    for bad in ['href="Yes"', 'href="None"', '"ws":"Yes"', '"ws":"None"', '"az":"None"', '"az":"Yes"', '—']:
        if bad in page:
            problems.append(f'forbidden: {bad!r}')
    if problems:
        print('GRADE-SYNC / QA FAILED, page not written:')
        for p in problems[:40]:
            print('  ', p)
        _sys.exit(1)
    open(page_path, 'w', encoding='utf-8').write(page)
    return n_rows

def top_level_items(text):
    """Comma-separated ingredients at parenthesis/bracket depth 0, each with
    its own sub-ingredient list attached (same split as top_level_ingredient_count)."""
    out, depth, cur = [], 0, ''
    for ch in text or '':
        if ch in '([':
            depth += 1
        elif ch in ')]':
            depth = max(0, depth - 1)
        if ch == ',' and depth == 0:
            out.append(cur.strip()); cur = ''
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out

def pct0(n, d):
    """Whole-number percent for guide copy; '<1' for a nonzero share under 0.5%."""
    if not d or not n:
        return '0'
    v = 100 * n / d
    return '<1' if v < 0.5 else str(round(v))


class Scoper:
    """Honest 'the most X of any ...' wording for a top-pick tile. Tries the
    widest claim first (every qualifying bar), then the pick's own grade band,
    then that band with the protein floor; if a bar already used on another
    tile beats it even there, says 'remaining'. Adds 'tied for' when tied."""
    def __init__(self, qualify, suffix, floor=10):
        self.q, self.suffix, self.floor = qualify, suffix, floor
    def __call__(self, fn, b, word, higher=True):
        g = b.get('score_band')
        band = [x for x in self.q if x.get('score_band') == g]
        levels = [(self.q, f'of any bar {self.suffix}'),
                  (band, f'of any {g}-grade bar {self.suffix}'),
                  ([x for x in band if P(x) >= self.floor], f'of any {g}-grade bar with {self.floor}g+ protein '
                   + (f'and {self.suffix[5:]}' if self.suffix.startswith('with ') else self.suffix))]
        best = max if higher else min
        for pool, phrase in levels:
            if pool and fn(b) == best(fn(x) for x in pool):
                tied = sum(1 for x in pool if fn(x) == fn(b)) > 1
                return f"{'tied for ' if tied else ''}the {word} {phrase}"
        return f'the {word} of any {g}-grade bar {self.suffix} not already picked above'

def faq_items_html(faqs):
    """Live guide FAQ markup. Answers may carry <a> links (then passed through as-is)."""
    return ''.join(f'''
        <div class="faq-item">
          <button class="faq-q">{esc(q)}</button>
          <div class="faq-a">{a if '<a ' in a else esc(a)}</div>
        </div>''' for q, a in faqs) + '\n      '

def plain_text(s):
    import html as _h
    return _h.unescape(re.sub(r'<[^>]+>', '', s))

def simple_card_html(label, n, total, desc):
    return f'''<div class="score-card">
  <div class="score-card-label">{esc(label)}</div>
  <div class="score-card-val">{comma(n)} bars<span class="oil-card-pct">{g1(100 * n / total)}%</span></div>
  <div class="score-card-desc">{esc(desc)}</div>
</div>'''

def picks_with_extra_html(h2, intro, picks, extra):
    """picks_section_html plus page-specific blocks (disclaimer callout, jump
    link) after the tile grid, inside the same section-inner."""
    h = picks_section_html(h2, intro, picks)
    i = h.rfind('</div>')
    return h[:i] + extra + '\n    </div>'

class Screen:
    """A macro guide's criteria as named checks, for fail counts and the
    per-brand 'misses mainly on ...' notes. checks: [(key, label, fails_fn)]."""
    def __init__(self, all_bars, checks):
        self.all, self.checks = all_bars, checks
        self.fails = {b['Key']: [k for k, _, fn in checks if fn(b)] for b in all_bars}
        self.label = {k: l for k, l, _ in checks}
    def count(self, key):
        return sum(1 for f in self.fails.values() if key in f)
    def multi(self, bars):
        return sum(1 for b in bars if len(self.fails[b['Key']]) >= 2)
    def misses_mainly(self, disq, share=0.5):
        from collections import Counter
        c = Counter(k for b in disq for k in self.fails[b['Key']])
        top = [k for k, n in sorted(c.items(), key=lambda kv: (-kv[1], [x[0] for x in self.checks].index(kv[0])))
               if n >= share * len(disq)]
        if not top and c:
            top = [max(c, key=c.get)]
        return [self.label[k] for k in top]

def macro_brand_tables_html(split, *, h2, intro_html, table_id, table_class, cols, notes, row_note, note_head='Note',
                            before_tables='', after_tables=''):
    """Consider / Mixed / Avoid for the macro guides (keto, diabetics, GLP-1),
    which show guide-specific averages instead of protein/sugar. cols:
    [(header, fn(row)->html)]; row_note(row, kind)->plain text."""
    consider, mixed, avoid = split
    head = '<thead><tr><th>Brand</th>' + ''.join(f'<th>{esc(h)}</th>' for h, _ in cols) + f'<th>{esc(note_head)}</th></tr></thead>'
    def cell(r):
        if r['q']:
            return f'<button type="button" class="brand-jump" data-brand="{esc(r["brand"])}">{esc(r["brand"])}</button>'
        return f'<span class="brand-name-static">{esc(r["brand"])}</span>'
    def row(r, kind, i=0):
        tr = '<tr>' if kind != 'avoid' else ('<tr class="avoid-row brand-row-hidden" style="display:none;">' if i >= 15 else '<tr class="avoid-row">')
        return (tr + f'<td>{cell(r)}</td>' + ''.join(f'<td>{fn(r)}</td>' for _, fn in cols)
                + f'<td class="diab-reason">{esc(row_note(r, kind))}</td></tr>')
    def block(cls, label, note, rows, tid='', extra=''):
        return f'''      <div class="brand-table-block">
        <div class="brand-table-label {cls}">{label}</div>
        <div class="brand-table-note">{esc(note)}</div>
        <div class="table-scroll">
          <table class="brand-table {table_class}"{tid}>
            {head}
            <tbody>
{rows}
            </tbody>
          </table>
        </div>{extra}
      </div>'''
    hidden = max(0, len(avoid) - 15)
    more = '' if not hidden else f'''
        <button type="button" class="brand-table-show-more" id="{table_id}-avoid-show-more" data-hidden-count="{hidden}">Show {hidden} more brands</button>
        <script>
        (function() {{
          var btn = document.getElementById('{table_id}-avoid-show-more');
          var table = document.getElementById('{table_id}-avoid-table');
          if (!btn || !table) return;
          btn.addEventListener('click', function() {{
            table.querySelectorAll('.brand-row-hidden').forEach(function(row) {{ row.style.display = ''; row.classList.remove('brand-row-hidden'); }});
            btn.classList.add('is-hidden');
          }});
        }})();
        </script>'''
    blocks = [block('pro', 'Brands to Consider', notes['consider'], '\n'.join(row(r, 'consider') for r in consider))]
    if mixed:
        blocks.append(block('mixed', 'Mixed Lineups, Check the Flavor', notes['mixed'], '\n'.join(row(r, 'mixed') for r in mixed)))
    blocks.append(block('con', 'Brands to Avoid', notes['avoid'], '\n'.join(row(r, 'avoid', i) for i, r in enumerate(avoid)),
                        f' id="{table_id}-avoid-table"', more))
    return f'''
    <div class="section-inner">
      <h2 class="section-title">{esc(h2)}</h2>
      <div class="section-body">
{intro_html}
      </div>{before_tables}

''' + '\n\n'.join(blocks) + f'''{after_tables}
    </div>
'''


def keto_row_html(b, idx):
    grade = b.get('score_band')
    sc = score(b) or 0
    prot, fat, nc = num(b.get('Protein (g)')), num(b.get('Total Fat (g)')), net_carbs(b)
    p = p100(b) or 0
    search = f"{b['Brand Name']} {b['Flavor Name']}".lower()
    return f'''<tr class="bar-row" data-idx="{idx}" data-score="{fnum(sc)}" data-grade="{grade}" data-protein="{fnum(prot or 0)}" data-fat="{fnum(fat or 0)}" data-netcarb="{fnum(nc)}" data-p100="{fnum(p)}" data-search="{esc(search)}" onclick="toggleIngr({idx}, this)">
  <td class="col-bar"><div class="bar-flavor">{esc(b['Brand Name'])}</div><div class="bar-flavor-name">{esc(b['Flavor Name'])}</div></td>
  <td class="col-num">{fnum(fat)}</td>
  <td class="col-num">{fnum(prot)}</td>
  <td class="col-num col-hide-mobile">{fnum(p)}</td>
  <td class="col-num">{fnum(nc)}</td>
  <td class="col-num col-hide-mobile">{fnum(num(b.get('Total Carbohydrates (g)')))}</td>
  <td class="col-num">{fnum(num(b.get('Dietary Fiber (g)')))}</td>
  <td class="col-num col-hide-mobile">{fnum(num(b.get('Sugar Alcohol (g)')) or 0)}</td>
  <td class="col-certs col-hide-mobile"><div class="cert-badges">{cert_badges_html(b)}</div></td>
  <td class="col-grade"><span class="table-grade-badge grade-{grade}" title="{grade_word(grade)} &middot; score {fnum(sc)}">{grade}</span></td>
</tr>'''

def keto_expand_html(r):
    """expand_html with the Keto page's rank grid (mirrors its buildLazyExpand)."""
    h = expand_html(r)
    def cell(lbl, val, pair):
        return (f'<div class="macro-rank-cell"><span class="macro-rank-lbl">{lbl}</span>'
                f'<span class="macro-rank-val">{val}</span><span class="macro-rank-tag {pair[1]}">{pair[0]}</span></div>')
    rk = r['rk']
    grid = (cell('Fat', f'{fnum(r["ftv"])}g', rk['ft']) + cell('Protein', f'{fnum(r["pv"])}g', rk['p'])
            + cell('Net Carbs', f'{r["ncv"]}g', rk['nc']) + cell('Fiber', f'{r["fv"]}g', rk['f']))
    i = h.index('<div class="macro-rank-grid">') + len('<div class="macro-rank-grid">')
    j = h.index('</div><div class="expand-columns">')
    return h[:i] + grid + h[j:]

def all_n_flavors(t):
    """'All 5 flavors' / 'Both flavors' / 'Its one flavor' for brand-table notes."""
    return 'Its one flavor' if t == 1 else ('Both flavors' if t == 2 else f'All {t} flavors')


def social_title_html(og_title, og_desc, url):
    """OG/Twitter block for guides whose share title is the <title> (not the H1)."""
    return f'''<meta property="og:type" content="article">
  <meta property="og:site_name" content="Know Your Bar">
  <meta property="og:title" content="{esc(og_title)}">
  <meta property="og:description" content="{esc(og_desc)}">
  <meta property="og:url" content="{url}">
  <meta property="og:image" content="https://knowyourbar.com/bar_hero.png">

  <!-- Twitter card -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(og_title)}">
  <meta name="twitter:description" content="{esc(og_desc)}">
  <meta name="twitter:image" content="https://knowyourbar.com/bar_hero.png">'''


def fiber_row_html(b, idx):
    """High Fiber page columns: CAL, PROT, P/100, FIBR, FAT, CARB, SGR (no SGR ALC)."""
    grade = b.get('score_band')
    sc = score(b) or 0
    prot, cal = num(b.get('Protein (g)')), num(b.get('Calories'))
    p = p100(b) or 0
    search = f"{b['Brand Name']} {b['Flavor Name']}".lower()
    return f'''<tr class="bar-row" data-idx="{idx}" data-score="{fnum(sc)}" data-grade="{grade}" data-protein="{fnum(prot or 0)}" data-cal="{fnum(cal or 0)}" data-sugar="{fnum(num(b.get('Sugars (g)')) or 0)}" data-p100="{fnum(p)}" data-fiber="{fnum(FIB(b))}" data-search="{esc(search)}" onclick="toggleIngr({idx}, this)">
  <td class="col-bar">
    <div class="bar-brand">{esc(b['Brand Name'])}</div>
    <div class="bar-flavor">{esc(b['Flavor Name'])}</div>
    <svg class="row-expand-icon" width="7" height="12" viewBox="0 0 7 12" fill="none"><path d="M1 1L6 6L1 11" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
  </td>
  <td class="col-num col-hide-mobile">{fnum(cal)}</td>
  <td class="col-num">{fnum(prot)}</td>
  <td class="col-num col-hide-mobile">{fnum(p)}</td>
  <td class="col-num">{fnum(FIB(b))}</td>
  <td class="col-num col-hide-mobile">{fnum(num(b.get('Total Fat (g)')))}</td>
  <td class="col-num col-hide-mobile">{fnum(num(b.get('Total Carbohydrates (g)')))}</td>
  <td class="col-num">{fnum(num(b.get('Sugars (g)')))}</td>
  <td class="col-certs col-hide-mobile"><div class="cert-badges">{cert_badges_html(b)}</div></td>
  <td class="col-grade"><span class="table-grade-badge grade-{grade}" title="{grade_word(grade)} &middot; score {fnum(sc)}">{grade}</span></td>
</tr>'''


# ===========================================================================
# GUIDE PAGE v2 ("Best 10" layout) -- added 2026-09-29.
# Spec: claude/GUIDE_PAGE_SPEC_V2.md (all decisions there are LOCKED).
# Pilot: build_no_sugar_alcohols.py. Other guides still use the v1 helpers
# above until they are migrated one page per session.
#
# Locked rules implemented here:
#   * Ingredient quality is used as a GRADE (A-F) only. Bars in the same grade
#     are treated as tied. The raw ingredient score is never used to rank a
#     pick, never printed on a v2 page, and never shown in an expand panel.
#   * Tie chain inside a slot: better grade, buy link (brand referral, then
#     Amazon, then brand site only; 2026-09-30), more protein, less sugar, more
#     fiber, fewer calories, a per-guide shuffle (set_tie_seed), then
#     brand/flavor name (only so builds are stable).
#   * Best overall: best grade present, then most protein per 100 calories,
#     15g+ protein. "Best [subset]" slots use the same rule inside the subset.
#   * No bar appears twice on one guide (repeats are allowed ACROSS guides).
#     At most 3 slots per brand. A slot with no eligible bar is replaced by the
#     guide's next fallback slot, so the list is always 10.
# ===========================================================================
import hashlib as _hashlib

BIG_BRANDS = ['Quest', 'Barebells', 'RXBAR', 'KIND', 'CLIF Bar', 'Clif Builders', 'One', 'Pure Protein', 'Built',
              'Nature Valley', 'Atkins', 'think!', 'Larabar', 'Kirkland', 'David', 'Power Crunch', 'FITCRUNCH',
              "Lenny & Larry's", 'Perfect Bar', 'IQ Bar', 'Aloha', 'GoMacro', 'NuGo']   # LOCKED 2026-09-29
BRAND_REVIEW_PAGES = {'Quest': '/quest-bars', 'RXBAR': '/rxbar-review', 'CLIF Bar': '/clif-bar-review',
                      'Clif Builders': '/clif-bar-review', 'Barebells': '/barebells-review', 'KIND': '/kind-bars-review'}
GRADE_POINTS = {'A': 4, 'B': 3, 'C': 2, 'D': 1, 'F': 0}
AUTHOR_NAME = 'Jeff Booth'
ABOUT_URL = 'https://knowyourbar.com/about'
V2_MAX_BYTES = 400_000        # hard target (spec: under ~400KB, ceiling 1MB)
V2_FAQ_MAX_OFFSET = 300_000   # FAQ and footer must start inside the first ~300KB

def is_big(b):
    return b['Brand Name'] in BIG_BRANDS

def gp(b):
    return GRADE_POINTS.get(b.get('score_band'), -1)

# Buy-link tiebreak (Jeff, 2026-09-30): right after grade, a bar with one of
# our brand referral links (Custom Referral Link = Yes, URL in Website) wins,
# then a bar with an Amazon link, then a bar with a brand site only. It only
# decides between bars already tied on the slot's own number and on grade.
def buy_rank(b):
    if b.get('Custom Referral Link') == 'Yes' and website_url(b):
        return 0
    return 1 if amazon_url(b) else 2

# Per-guide shuffle for exact ties (Jeff, 2026-09-30). Bars tied on every step
# of the chain (e.g. three Fello flavors with identical macros) used to fall to
# alphabetical order, so the same flavor won on every guide. Each v2 builder
# calls set_tie_seed(<page slug>) before picking: the last step is then a
# stable hash of (slug, bar key), different per guide, identical on every
# rebuild. Name stays as the final step so the order is always total.
TIE_SEED = ''
def set_tie_seed(seed):
    global TIE_SEED
    TIE_SEED = seed or ''
def tie_shuffle(b):
    if not TIE_SEED:
        return ''
    return _hashlib.md5(f'{TIE_SEED}|{b["Key"]}'.encode('utf-8')).hexdigest()

def tie_chain(b):
    return (-gp(b), buy_rank(b), -P(b), SUG(b), -FIB(b), CAL(b), tie_shuffle(b), name_key(b))

def overall_key(b):
    return (-gp(b), -(p100(b) or 0)) + tie_chain(b)

def v2_eligible(qualify, floor=10):
    """Guardrails for every slot: qualifies, grade B or better, protein floor."""
    return [b for b in qualify if b.get('score_band') in ('A', 'B') and P(b) >= floor]

class Slot:
    """One Best 10 slot. pool(eligible_bars) -> candidates; key(b) sorts best
    first; metric(b) is the headline number the slot is about (for tie
    wording); why(b, ctx) returns the card sentence; rule is the plain-English
    rule printed in "How we picked these"."""
    def __init__(self, label, rule, pool, key, why, metric=None, floor=10):
        self.label, self.rule, self.pool, self.key, self.why = label, rule, pool, key, why
        self.metric, self.floor = metric, floor

def slot_best_overall(floor=15):
    return Slot('Best overall',
                f'The best ingredient grade on the list, then the most protein per 100 calories, with {floor}g+ protein.',
                lambda E: [b for b in E if P(b) >= floor], overall_key,
                lambda b, c: (f"{fnum(P(b))}g protein for {fnum(CAL(b))} calories ({fnum(p100(b))}g per 100 calories), "
                              f"{c['tied']}the most protein per calorie of any {b['score_band']}-grade bar here with {floor}g+ protein."),
                metric=lambda b: (gp(b), p100(b)), floor=floor)

def slot_cleanest():
    return Slot('Cleanest ingredients',
                'An A-grade bar (B if no A qualifies) with the shortest ingredient list. Every bar in the same grade is '
                'treated as equal on ingredient quality, so the tiebreak is a label you can count.',
                lambda E: [b for b in E if b['score_band'] == min((x['score_band'] for x in E), default='A')],
                lambda b: (top_level_ingredient_count(ingr(b)),) + tie_chain(b),
                lambda b, c: (f"Just {top_level_ingredient_count(ingr(b))} ingredients, {c['tied']}the shortest label of any "
                              f"{b['score_band']}-grade bar here, with {fnum(P(b))}g protein."),
                metric=lambda b: top_level_ingredient_count(ingr(b)))

def slot_highest_protein(cal_cap=300):
    return Slot('Highest protein',
                f'The most protein per bar, grade B or better, capped at {cal_cap} calories so a large candy-style bar '
                'cannot win on size alone.',
                lambda E: [b for b in E if CAL(b) <= cal_cap], lambda b: (-P(b),) + tie_chain(b),
                lambda b, c: (f"{fnum(P(b))}g protein in {fnum(CAL(b))} calories, {c['tied']}the most of any bar here "
                              f"at {cal_cap} calories or less. We cap this pick at {cal_cap} calories so a bigger, sugarier "
                              "bar can't win on size alone."),
                metric=P)

def slot_protein_per_cal(floor=12):
    return Slot('Most protein per calorie', f'The most protein per 100 calories, grade B or better, {floor}g+ protein.',
                lambda E: [b for b in E if P(b) >= floor], lambda b: (-(p100(b) or 0),) + tie_chain(b),
                lambda b, c: (f"{fnum(p100(b))}g protein per 100 calories ({fnum(P(b))}g in {fnum(CAL(b))} calories), "
                              f"{c['tied']}the best ratio of any bar here with {floor}g+ protein."),
                metric=p100)

def slot_lowest_calorie():
    # Best grade first, then fewest calories (Jeff, 2026-09-29: a B-grade bar
    # was winning this slot on every guide because calories came before grade).
    return Slot('Lowest calorie', 'The best ingredient grade on the list, then the fewest calories, 10g+ protein.',
                lambda E: E, lambda b: (-gp(b), CAL(b)) + tie_chain(b),
                lambda b, c: (f"{fnum(CAL(b))} calories with {fnum(P(b))}g protein, {c['tied']}the fewest calories of any "
                              f"{b['score_band']}-grade bar here with 10g+ protein."),
                metric=lambda b: (gp(b), CAL(b)))

def slot_big_brand():
    return Slot('Best from a big brand',
                'The Best overall rule (best grade, then most protein per 100 calories), limited to brands with national '
                'grocery, big-box or Costco distribution. 10g+ protein.',
                lambda E: [b for b in E if is_big(b)], overall_key,
                lambda b, c: (f"The top pick from a brand you can find in most grocery stores: {b['score_band']}-grade "
                              f"ingredients, {fnum(P(b))}g protein, {fnum(CAL(b))} calories."),
                metric=lambda b: (gp(b), p100(b)))

def slot_lowest_sugar():
    return Slot('Lowest sugar', 'The least sugar, grade B or better, 10g+ protein.',
                lambda E: E, lambda b: (SUG(b),) + tie_chain(b),
                lambda b, c: (f"{fnum(SUG(b))}g sugar with {fnum(P(b))}g protein, {c['tied']}the lowest sugar of any bar "
                              "here with 10g+ protein" + (f", and it wins the tie on {c['tie_on']}." if c['tied'] and c['tie_on'] != 'name' else ".")),
                metric=SUG)

def slot_subset(label, rule_subset, test, why_lead, floor=10):
    """'Best [subset]': the Best overall rule inside a subset of the list."""
    return Slot(label, f'{rule_subset} Ranked with the Best overall rule (best grade, then most protein per 100 calories), '
                       f'{floor}g+ protein.',
                lambda E: [b for b in E if test(b) and P(b) >= floor], overall_key,
                lambda b, c: why_lead(b) + f" {b['score_band']}-grade ingredients, {fnum(P(b))}g protein, {fnum(CAL(b))} calories.",
                metric=lambda b: (gp(b), p100(b)), floor=floor)

def _tie_context(slot, pool, b):
    """'tied for ' when another bar in the slot's pool shares the pick's
    headline number, plus which tiebreak decided it."""
    if slot.metric is None:
        return {'tied': '', 'tie_on': ''}
    m = slot.metric(b)
    others = [x for x in pool if x is not b and slot.metric(x) == m]
    if not others:
        return {'tied': '', 'tie_on': ''}
    # which link of the tie chain separated the pick from the nearest tied bar
    nearest = min(others, key=slot.key)
    # 'buy link' and the per-guide shuffle print no "wins the tie on" clause
    # (treated like the name step): the card just says "tied for".
    names = ['grade', 'name', 'protein', 'sugar', 'fiber', 'calories']
    tc_b, tc_x = tie_chain(b), tie_chain(nearest)
    on = next((names[i] for i in range(6) if tc_b[i] != tc_x[i]), 'name')
    return {'tied': 'tied for ', 'tie_on': on}

def _why_honest(slot, pool, b, cand, used, brands, brand_cap):
    """Card sentence for a pick. If a bar that ranks above it in this slot was
    skipped (already on the list, or its brand is at the cap), the superlative
    is scoped to the remaining bars and the card says who ranked higher, so a
    card never claims 'the fewest calories of any bar here' when an earlier
    card holds a bar with fewer (2026-09-29)."""
    why = slot.why(b, _tie_context(slot, cand, b))
    top = min(pool, key=slot.key)
    if top is b or slot.key(top) == slot.key(b):
        return why
    why = re.sub(r'(the (?:most|fewest|lowest|best|shortest|highest)\b[^.]*?) of any ', r'\1 of any remaining ', why, count=1)
    if top['Key'] in used:
        return why + f" {full(top)} ranks higher but is already on this list."
    return why + f" {full(top)} ranks higher, but {top['Brand Name']} already has {brand_cap} picks here."

V2_BRAND_CAP = 2   # max Best 10 slots per brand (Jeff, 2026-09-29: was 3; Fello took 3 near-identical cards)

def pick_best10(qualify, slots, fallbacks=(), floor=10, brand_cap=V2_BRAND_CAP):
    """Returns [(slot, bar, why, pool_size)]. No bar repeats on the page, at
    most brand_cap slots per brand, empty slots replaced from fallbacks."""
    E = v2_eligible(qualify, floor)
    used, brands, out = set(), defaultdict(int), []
    queue, fb = list(slots), list(fallbacks)
    while queue and len(out) < 10:
        s = queue.pop(0)
        pool = s.pool(E)
        cand = [b for b in sorted(pool, key=s.key) if b['Key'] not in used and brands[b['Brand Name']] < brand_cap]
        if not cand:
            if fb:
                queue.insert(0, fb.pop(0))
            continue
        b = cand[0]
        # tie wording is judged against bars still available to this slot
        out.append((s, b, _why_honest(s, pool, b, cand, used, brands, brand_cap), len(pool)))
        used.add(b['Key']); brands[b['Brand Name']] += 1
    while len(out) < 10 and fb:
        s = fb.pop(0)
        pool = s.pool(E)
        cand = [b for b in sorted(pool, key=s.key) if b['Key'] not in used and brands[b['Brand Name']] < brand_cap]
        if cand:
            b = cand[0]
            out.append((s, b, _why_honest(s, pool, b, cand, used, brands, brand_cap), len(pool)))
            used.add(b['Key']); brands[b['Brand Name']] += 1
    return out

# ---- v2 markup -------------------------------------------------------------
DEFAULT_CARD_MACROS = [('Protein', lambda b: f'{fnum(P(b))}g'), ('Calories', lambda b: fnum(CAL(b))),
                       ('Sugar', lambda b: f'{fnum(SUG(b))}g'), ('Fiber', lambda b: f'{fnum(FIB(b))}g')]

def v2_buy_html(b):
    """Brand link + Amazon, same two button styles as the rest of the site."""
    out = ''
    az, ws = amazon_url(b), website_url(b)
    if ws:
        out += f'<a href="{esc(ws)}" target="_blank" rel="noopener" class="visit-link">Brand Site</a>'
    if az:
        out += f'<a href="{esc(az)}" target="_blank" rel="noopener sponsored" class="amazon-link">Amazon</a>'
    return out

def best10_html(picks, *, h2, intro, macros=DEFAULT_CARD_MACROS):
    cards = []
    for i, (s, b, why, _n) in enumerate(picks, 1):
        g = b['score_band']
        mac = ''.join(f'<div class="b10-macro"><span class="b10-macro-val">{f(b)}</span>'
                      f'<span class="b10-macro-lbl">{esc(l)}</span></div>' for l, f in macros)
        cards.append(f'''<div class="macro-card pick-tile b10-card" id="pick-{i}">
  <div class="pick-tile-body">
    <div class="pick-tile-category"><span class="b10-rank">{i}</span>{esc(s.label)}</div>
    <div class="pick-tile-brand">{esc(b['Brand Name'])}</div>
    <div class="pick-tile-flavor-name">{esc(b['Flavor Name'])}</div>
    <div class="pick-tile-quality"><span class="pick-tile-quality-label">Ingredient Quality</span><span class="table-grade-badge grade-{g}">{g}</span><span class="pick-tile-quality-word">{grade_word(g)}</span></div>
    <div class="b10-macros">{mac}</div>
    <p class="pick-tile-reason">{esc(why)}</p>
  </div>
  <div class="pick-tile-footer"><div class="bar-links">{v2_buy_html(b)}</div></div>
</div>''')
    return f'''<div class="section-inner">
      <h2 class="section-title">{esc(h2)}</h2>
      <p class="section-body">{esc(intro)} <a href="#how-we-picked" class="b10-how">How we picked these &rarr;</a></p>
      <div class="b10-grid">
{chr(10).join(cards)}
      </div>
    </div>'''

def glance_html(picks, *, h2='Best 10 at a glance', cols=None):
    cols = cols or [('Protein', lambda b: f'{fnum(P(b))}g'), ('Cal', lambda b: fnum(CAL(b))),
                    ('Sugar', lambda b: f'{fnum(SUG(b))}g'), ('Fiber', lambda b: f'{fnum(FIB(b))}g')]
    head = ''.join(f'<th>{esc(h)}</th>' for h, _ in cols)
    rows = '\n'.join(
        f'<tr><td>{esc(b["Brand Name"])}</td><td>{esc(b["Flavor Name"])}</td><td><a href="#pick-{i}">{esc(s.label)}</a></td>'
        f'<td>{grade_badge(b["score_band"])}</td>' + ''.join(f'<td>{f(b)}</td>' for _, f in cols) + '</tr>'
        for i, (s, b, _w, _n) in enumerate(picks, 1))
    return f'''<div class="section-inner">
      <h2 class="section-title">{esc(h2)}</h2>
      <div class="table-scroll">
        <table class="brand-table b10-v2 b10-glance">
          <thead><tr><th>Brand</th><th>Flavor</th><th>Pick</th><th>Grade</th>{head}</tr></thead>
          <tbody>
{rows}
          </tbody>
        </table>
      </div>
    </div>'''

def brands_well_rows(all_bars, qualifies, n=8, min_big=2, min_small=2):
    """Eligible: 3+ bars in the DB and at least one qualifying. Rank: share of
    the brand's bars that qualify x average grade points of its qualifying
    bars (A=4 ... F=0, grades only, never raw scores); ties -> bigger lineup.
    Top n, then swap in big / small brands until the minimums are met."""
    by = defaultdict(list)
    for b in all_bars:
        by[b['Brand Name']].append(b)
    rows = []
    for brand, bars in by.items():
        if len(bars) < 3:
            continue
        q = [b for b in bars if qualifies(b)]
        if not q:
            continue
        share = len(q) / len(bars)
        avg_gp = sum(gp(b) for b in q) / len(q)
        rows.append(dict(brand=brand, bars=bars, qual=q, total=len(bars), q=len(q), share=share,
                         rank=share * avg_gp / 4, big=brand in BIG_BRANDS,
                         grades=Counter_(b['score_band'] for b in q)))
    rows.sort(key=lambda r: (-r['rank'], -r['total'], r['brand'].lower()))
    top = rows[:n]
    for need_big in (True, False):
        need = min_big if need_big else min_small
        have = [r for r in top if r['big'] == need_big]
        extra = [r for r in rows if r['big'] == need_big and r not in top]
        while len(have) < need and extra:
            drop = next(r for r in reversed(top) if r['big'] != need_big)
            top.remove(drop); add = extra.pop(0); top.append(add); have.append(add)
    top.sort(key=lambda r: (-r['rank'], -r['total'], r['brand'].lower()))
    return top

from collections import Counter as Counter_

def grade_mix_text(counter):
    parts = [f"{counter[g]} {g}" for g in BAND_ORDER if counter.get(g)]
    return names_and(parts)

def best_pick(bars):
    """Best bar in a list by the Best overall rule (grade, then protein per calorie)."""
    return min(bars, key=overall_key) if bars else None

def brands_well_html(rows, why, *, h2, intro):
    items = '\n'.join(
        f'<tr><td class="kt-brand">{esc(r["brand"])}</td><td class="kt-num">{r["q"]}/{r["total"]}</td>'
        f'<td class="kt-num">{grade_range_html(*grade_range(r["qual"]))}</td>'
        f'<td class="kt-num">{fnum(avg(r["qual"], "Protein (g)"))}g</td><td class="kt-num">{fnum(avg(r["qual"], "Sugars (g)"))}g</td>'
        f'<td class="kt-text">{esc(why(r))}</td></tr>' for r in rows)
    return ('<div class="section-inner">\n      <h2 class="section-title">' + esc(h2) + '</h2>\n'
            '      <p class="section-body">' + esc(intro) + '</p>\n      <div class="kt-wrap">\n        <table class="kt-table kt-brands">\n'
            '          <thead><tr><th class="kt-brand">Brand</th><th class="kt-num">Qualify</th><th class="kt-num">Grades</th>'
            '<th class="kt-num">Avg protein</th><th class="kt-num">Avg sugar</th><th class="kt-text">Why</th></tr></thead>\n'
            '          <tbody>\n' + items + '\n          </tbody>\n        </table>\n      </div>\n    </div>')

def more_list_html(names, label='Found in:', first=4, empty='No bars in the current database'):
    """v2 'Found in' list. Collapsed: 'A, B, C, D and 25 more'. Expanded, the
    rest of the list appears inline and the toggle moves to the END of the list
    as 'Show less' (the v1 <details> version left 'Hide' stuck mid-list)."""
    names = list(names)
    if not names:
        return f'<div class="oil-card-brands"><span class="oil-card-brands-label">{label}</span> {esc(empty)}</div>'
    head, rest = names[:first], names[first:]
    out = f'<div class="oil-card-brands more-list"><span class="oil-card-brands-label">{label}</span> {esc(", ".join(head))}'
    if rest:
        out += (f'<span class="more-rest" hidden>, {esc(", ".join(rest))}</span> '
                f'<button type="button" class="more-toggle" aria-expanded="false" data-more="and {len(rest)} more">and {len(rest)} more</button>')
    return out + '</div>'

def avg_grade(bars):
    """Average grade as a letter (mean of grade points, rounded)."""
    if not bars:
        return None
    m = sum(gp(b) for b in bars) / len(bars)
    return {4: 'A', 3: 'B', 2: 'C', 1: 'D', 0: 'F'}[int(m + 0.5)]

def big_brands_html(all_bars, qualifies, verdict, *, h2, intro, qual_word='qualify'):
    by = defaultdict(list)
    for b in all_bars:
        by[b['Brand Name']].append(b)
    rows = []
    for brand in BIG_BRANDS:
        bars = by.get(brand)
        if not bars:
            continue
        q = [b for b in bars if qualifies(b)]
        rows.append(dict(brand=brand, bars=bars, qual=q, total=len(bars), q=len(q)))
    rows.sort(key=lambda r: (-r['q'] / r['total'], -r['q'], r['brand'].lower()))
    def name(r):
        u = BRAND_REVIEW_PAGES.get(r['brand'])
        return f'<a href="{u}">{esc(r["brand"])}</a>' if u else esc(r['brand'])
    def gcell(r):
        return grade_badge(avg_grade(r['qual'])) if r['qual'] else '<span class="kt-sub">n/a</span>'
    body = '\n'.join(
        f'<tr><td class="kt-brand">{name(r)}</td>'
        f'<td class="kt-num"><span class="kt-strong">{r["q"]}/{r["total"]}</span><span class="kt-sub">{round(100 * r["q"] / r["total"])}%</span></td>'
        f'<td class="kt-num">{gcell(r)}</td><td class="kt-text">{esc(verdict(r))}</td></tr>' for r in rows)
    html = ('<div class="section-inner">\n      <h2 class="section-title">' + esc(h2) + '</h2>\n'
            '      <p class="section-body">' + intro + '</p>\n      <div class="kt-wrap">\n        <table class="kt-table kt-big">\n'
            '          <thead><tr><th class="kt-brand">Brand</th><th class="kt-num">' + esc(qual_word.capitalize()) + '</th>'
            '<th class="kt-num">Avg grade</th><th class="kt-text">Verdict</th></tr></thead>\n'
            '          <tbody>\n' + body + '\n          </tbody>\n        </table>\n      </div>\n    </div>')
    return html, rows

def top50_rows(qualify, n=50):
    """Top 50 order: best grade, then most protein per 100 calories, then the
    tie chain. Grades only, never raw score."""
    return sorted(qualify, key=overall_key)[:n]

def buy_pair_html(b, cls='kt-buy'):
    """Both buy links, short labels, side by side: Amazon (outlined) + Brand (solid)."""
    out = ''
    az, ws = amazon_url(b), website_url(b)
    if az:
        out += f'<a href="{esc(az)}" target="_blank" rel="noopener sponsored" class="amazon-link {cls}">Amazon</a>'
    if ws:
        out += f'<a href="{esc(ws)}" target="_blank" rel="noopener" class="visit-link {cls}">Brand</a>'
    return out

KT_COLS = {  # key -> (header, fn)
    'grade': ('Grade', lambda b: f'<span class="table-grade-badge grade-{b["score_band"]}" title="{grade_word(b["score_band"])}">{b["score_band"]}</span>'),
    'protein': ('Protein', lambda b: f'{fnum(P(b))}g'),
    'cal': ('Cal', lambda b: fnum(CAL(b))),
    'sugar': ('Sugar', lambda b: f'{fnum(SUG(b))}g'),
    'fiber': ('Fiber', lambda b: f'{fnum(FIB(b))}g'),
    'netcarbs': ('Net carbs', lambda b: f'{fnum(net_carbs(b))}g'),   # diabetics v2 (2026-09-30)
    'fat': ('Fat', lambda b: f'{fnum(num(b.get("Total Fat (g)")) or 0)}g'),   # keto v2 (2026-09-30)
}

def compact_bar_table_html(bars, *, cols=('grade', 'protein', 'cal', 'sugar', 'fiber'), extra=None, hide_mobile=('fiber',)):
    """Compact bar list used by v2 guides (Top 50 and any short bar table).
    One Bar cell (brand over flavor), centered numbers, both buy links.
    extra=(header, fn(b)->html) adds a text column after Bar. Rows expand
    on tap (nutrition + ingredients, loaded from /bars.js). On phones the
    buy links move under the flavor name."""
    heads = ['<th class="kt-bar">Bar</th>']
    if extra:
        heads.append(f'<th class="kt-extra kt-hide-m">{esc(extra[0])}</th>')
    for c in cols:
        heads.append(f'<th class="kt-num{" kt-hide-m" if c in hide_mobile else ""}">{KT_COLS[c][0]}</th>')
    heads.append('<th class="kt-buy-col kt-hide-m">Buy</th>')
    span = len(heads)
    rows = []
    for b in bars:
        buy = buy_pair_html(b)
        cells = [f'<td class="kt-bar"><div class="bar-brand">{esc(b["Brand Name"])}</div><div class="bar-flavor">{esc(b["Flavor Name"])}</div>'
                 + (f'<div class="kt-extra-inline">{esc(extra[0])}: {extra[1](b)}</div>' if extra else '')
                 + (f'<div class="kt-buy-inline">{buy}</div>' if buy else '') + '</td>']
        if extra:
            cells.append(f'<td class="kt-extra kt-hide-m">{extra[1](b)}</td>')
        for c in cols:
            cells.append(f'<td class="kt-num{" kt-hide-m" if c in hide_mobile else ""}">{KT_COLS[c][1](b)}</td>')
        cells.append(f'<td class="kt-buy-col kt-hide-m"><div class="kt-buy-pair">{buy}</div></td>')
        rows.append(f'<tr class="bar-row t50-row" data-key="{esc(b["Key"])}" data-grade="{b["score_band"]}" tabindex="0" aria-expanded="false">'
                    + ''.join(cells) + '</tr>'
                    + f'<tr class="t50-exp" hidden><td colspan="{span}"><div class="expand-content"></div></td></tr>')
    return ('<div class="kt-wrap">\n        <table class="kt-table">\n          <thead><tr>' + ''.join(heads) + '</tr></thead>\n'
            '          <tbody class="kt-body">\n' + '\n'.join(rows) + '\n          </tbody>\n        </table>\n      </div>')

def top50_html(bars, *, h2, intro, cols=('grade', 'protein', 'cal', 'sugar', 'fiber'), hide_mobile=('fiber', 'cal')):
    return ('<div class="section-inner">\n      <h2 class="section-title">' + esc(h2) + '</h2>\n'
            '      <p class="section-body">' + esc(intro) + '</p>\n      ' + compact_bar_table_html(bars, cols=cols, hide_mobile=hide_mobile) + '\n    </div>')

def finder_cta_html(n, href, *, desc):
    return f'''<div class="explore-cta-grid">
      <div class="explore-cta-main">
        <h2 class="explore-cta-main-heading">See all {comma(n)} in the Bar Finder &rarr;</h2>
        <p class="explore-cta-main-desc">{esc(desc)}</p>
        <a href="{esc(href)}" class="finder-cta-btn b10-finder-btn">See all {comma(n)} in the Bar Finder &rarr;</a>
      </div>
      <div class="explore-cta-side">
        <a href="/ingredient_scoring" class="explore-cta-side-link">How we score &rarr;</a>
        <ul class="explore-cta-side-list">
          <li>Every ingredient is scored individually against a canonical database, not just flagged good or bad</li>
          <li>Position in the ingredient list matters, earlier ingredients carry more weight</li>
          <li>Each bar's total becomes a single letter grade, A through F</li>
        </ul>
      </div>
    </div>'''

def criteria_html(*, qualify_rule, picks, extra_rules=()):
    slot_rules = '\n'.join(f'<li><strong>{esc(s.label)}:</strong> {esc(s.rule)}</li>' for s, _b, _w, _n in picks)
    extras = ''.join(f'<li>{esc(x)}</li>' for x in extra_rules)
    return f'''<div class="section-inner">
      <h2 class="section-title">How we picked these</h2>
      <div class="section-body">
        <p><strong>What qualifies:</strong> {qualify_rule}</p>
        <p><strong>Rules for every pick:</strong></p>
        <ul class="criteria-list">
          <li>The bar has to qualify for this guide, carry an A or B ingredient grade, and have at least 10g of protein.</li>
          <li>We rank ingredient quality by grade only. Two bars with the same grade count as equal, because our scoring isn't precise enough to split them. When two bars tie on a pick's own number and grade, the one you can buy through a link on this page goes first (a brand's own partner link, then Amazon). After that, ties go to more protein, then less sugar, then more fiber, then fewer calories.</li>
          <li>No bar appears twice in the Best 10, and no brand gets more than {V2_BRAND_CAP} of the 10 spots.</li>
          <li>If a pick's rule finds no eligible bar, that spot goes to the next rule on this guide's backup list, so there are always 10.</li>
          <li>Nobody pays for a spot. Every bar goes through the same rules. Buy links may earn us a commission. A link only ever decides between bars that are already tied, and never lifts a bar over one with a better grade or a better number.</li>{extras}
        </ul>
        <p><strong>How each pick was chosen:</strong></p>
        <ul class="criteria-list">
{slot_rules}
        </ul>
        <p>How the A to F grades themselves are calculated: <a href="/ingredient_scoring">our scoring methodology</a>. Who built this and why: <a href="/about">About Know Your Bar</a>.</p>
      </div>
    </div>'''

def byline_html():
    """Quiet author line at the very bottom of the page (Jeff, 2026-09-29: not
    in the hero). Article schema still names Jeff Booth as author."""
    return (f'<p class="guide-author">Know Your Bar is built by <a href="/about" rel="author">{AUTHOR_NAME}</a>. '
            f'<a href="/about">About us</a> &middot; <a href="/ingredient_scoring">How we rate bars</a></p>')

def related_html(cards):
    return '\n'.join(f'''        <a href="{h}" class="explore-more-card">
          <div class="explore-more-title">{esc(t)}</div>
          <div class="explore-more-desc">{esc(d)}</div>
        </a>''' for h, t, d in cards)

def grade_share_chart_html(rows, *, title, note):
    """Horizontal bar chart, one bar per grade (grade colors = identity), each
    labeled with its value in text ink. rows: [(grade, hit, total)]."""
    bars = ''.join(
        f'<div class="gchart-row" title="{g} grade: {h} of {t} bars ({round(100 * h / t)}%)">'
        f'<span class="table-grade-badge grade-{g}">{g}</span>'
        f'<span class="gchart-track"><span class="gchart-fill grade-{g}" style="width:{max(1, round(100 * h / t))}%"></span></span>'
        f'<span class="gchart-val">{round(100 * h / t)}%</span></div>' for g, h, t in rows)
    return (f'<figure class="gchart"><figcaption class="gchart-title">{esc(title)}</figcaption>{bars}'
            f'<div class="gchart-note">{esc(note)}</div></figure>')

def findings_v2_html(h2, insights, chart_html):
    items = ''.join(f'<div class="insight-item"><div class="insight-dot"></div><div class="insight-head">{esc(h)}</div>'
                    f'<div class="insight-detail">{esc(d)}</div></div>' for h, d in insights)
    return f'''<div class="findings-inner">
      <h2 class="findings-title">{esc(h2)}</h2>
      <div class="insights-grid">
        {items}
      </div>
      {chart_html}
    </div>'''

def article_jsonld_v2(*, h1, desc, url, about, published, date_modified):
    d = {'@context': 'https://schema.org', '@type': 'Article', 'headline': h1, 'description': desc, 'url': url,
         'image': 'https://knowyourbar.com/bar_hero.png', 'datePublished': published, 'dateModified': date_modified,
         'author': {'@type': 'Person', 'name': AUTHOR_NAME, 'url': ABOUT_URL},
         'publisher': {'@type': 'Organization', 'name': 'Know Your Bar', 'url': 'https://knowyourbar.com'},
         'mainEntityOfPage': {'@type': 'WebPage', '@id': url}, 'about': {'@type': 'Thing', 'name': about}}
    return '<script type="application/ld+json">\n  ' + json.dumps(d, indent=2, ensure_ascii=False).replace('\n', '\n  ') + '\n  </script>'

def v2_head_regions(*, title, h1, desc, og_desc, url, about, published, faqs, picks):
    """Same regions as guide_head_regions (Article, Breadcrumb, FAQPage,
    ItemList, social); Article gets a Person author and a placeholder
    dateModified that build_guide_page_v2 fills. ItemList = the Best 10."""
    regs = guide_head_regions(title=title, h1=h1, desc=desc, og_desc=og_desc, url=url, about=about,
                              published=published, faqs=faqs, picks=[(s.label, b) for s, b, _w, _n in picks])
    regs = [(n, c) for n, c in regs if n != 'jsonld-article']
    items = {'@context': 'https://schema.org', '@type': 'ItemList', 'name': h1, 'itemListOrder': 'https://schema.org/ItemListOrderAscending',
             'numberOfItems': len(picks), 'itemListElement': [
                 {'@type': 'ListItem', 'position': i + 1, 'name': f'{s.label}: {full(b)}', 'url': f'{url}#pick-{i + 1}'}
                 for i, (s, b, _w, _n) in enumerate(picks)]}
    regs = [(n, c) if n != 'jsonld-itemlist' else
            (n, '<script type="application/ld+json">\n  ' + json.dumps(items, ensure_ascii=False, separators=(',', ':')) + '\n  </script>')
            for n, c in regs]
    regs.insert(1, ('jsonld-article', article_jsonld_v2(h1=h1, desc=desc, url=url, about=about, published=published,
                                                        date_modified='__KYB_DATE_MODIFIED__')))
    return regs

# ---- v2 page shell ------------------------------------------------------------
V2_BODY = '''<section class="hero page-guide">
  <div class="hero-inner">
    <!-- kyb:hero -->
<!-- /kyb:hero -->
  </div>
</section>

<main class="content guide-v2">
  <section class="section" id="best-10">
<!-- kyb:best10 -->
<!-- /kyb:best10 -->
  </section>
<!-- kyb:editorial -->
<!-- /kyb:editorial -->
  <section class="findings" id="what-we-found">
<!-- kyb:findings -->
<!-- /kyb:findings -->
  </section>
  <section class="section" id="brands-that-do-it-well">
<!-- kyb:brands-well -->
<!-- /kyb:brands-well -->
  </section>
  <section class="section off" id="big-brands">
<!-- kyb:big-brands -->
<!-- /kyb:big-brands -->
  </section>
  <section class="section" id="top-50">
<!-- kyb:top50 -->
<!-- /kyb:top50 -->
  </section>
  <section class="section guide-finder-cta">
<!-- kyb:finder-cta -->
<!-- /kyb:finder-cta -->
  </section>
  <section class="section off" id="how-we-picked">
<!-- kyb:criteria -->
<!-- /kyb:criteria -->
  </section>
  <section class="guide-faq" id="faq">
    <div class="guide-faq-inner">
      <h2 class="section-title">Frequently asked questions</h2>
      <div class="faq-items"><!-- kyb:faq -->
<!-- /kyb:faq --></div>
    </div>
  </section>
  <section class="section">
    <div class="section-inner">
      <div class="explore-more-label">Related guides</div>
      <div class="explore-more-grid"><!-- kyb:explore-more -->
<!-- /kyb:explore-more --></div>
    </div>
  </section>
  <section class="section guide-author-section">
    <div class="section-inner"><!-- kyb:author -->
<!-- /kyb:author --></div>
  </section>
</main><!-- /content -->
'''

V2_SCRIPT = r'''<script>
/* Guide v2 (kyb_guide_lib.py). Top 50 rows expand on tap; the detail comes
   from /bars.js, loaded once on the first tap (the Bar Finder caches the same
   file). Ingredient quality shows as a grade only, never a score. */
(function () {
  var bodies = document.querySelectorAll('.kt-body');
  var loading = null, byKey = null;
  function loadBars() {
    if (byKey) return Promise.resolve(byKey);
    if (loading) return loading;
    loading = new Promise(function (resolve, reject) {
      var s = document.createElement('script');
      s.src = '/bars.js';
      s.onload = function () {
        byKey = {};
        try { BARS.forEach(function (b) { byKey[b.Key] = b; }); } catch (e) {}
        resolve(byKey);
      };
      s.onerror = function () { loading = null; reject(); };
      document.head.appendChild(s);
    });
    return loading;
  }
  function esc(v) {
    return String(v == null ? '' : v).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function n(v) {
    if (v === null || v === undefined || v === '') return null;
    var x = parseFloat(v); if (isNaN(x)) return null;
    return Math.round(x * 10) / 10;
  }
  var WORD = { A: 'Clean', B: 'Good', C: 'Okay', D: 'Poor', F: 'Avoid' };
  var CHIP = { positive: 'chip-positive', concern: 'chip-concern', neutral: 'chip-neutral' };
  var NUTR = [['Calories', 'Calories', ''], ['Protein (g)', 'Protein', 'g'], ['Total Fat (g)', 'Total Fat', 'g'],
    ['Saturated Fat (g)', 'Saturated Fat', 'g'], ['Sodium (mg)', 'Sodium', 'mg'], ['Total Carbohydrates (g)', 'Total Carbs', 'g'],
    ['Dietary Fiber (g)', 'Dietary Fiber', 'g'], ['Sugars (g)', 'Sugars', 'g'], ['Sugar Alcohol (g)', 'Sugar Alcohol', 'g']];
  function url(v) { return (typeof v === 'string' && v.indexOf('http') === 0) ? v : ''; }
  function panel(b) {
    var buy = '';
    if (url(b['Website'])) buy += '<a href="' + esc(b['Website']) + '" target="_blank" rel="noopener" class="visit-link">Shop on Brand Site</a>';
    if (url(b['Amazon Affiliate'])) buy += '<a href="' + esc(b['Amazon Affiliate']) + '" target="_blank" rel="noopener sponsored" class="amazon-link">Shop on Amazon</a>';
    var nutr = NUTR.map(function (f) {
      var v = n(b[f[0]]);
      return '<div class="nutr-row"><span class="nutr-label">' + f[1] + '</span><span class="nutr-val">' + (v === null ? 'n/a' : v + f[2]) + '</span></div>';
    }).join('');
    var chips = String(b['score_insights'] || '').split('|').filter(function (p) { return p.trim(); }).map(function (p) {
      var bits = p.split(':');
      return '<span class="insight-chip ' + (CHIP[(bits[1] || '').trim()] || 'chip-neutral') + '">' + esc(bits[0].trim()) + '</span>';
    }).join('');
    var g = b['score_band'];
    var sv = n(b['Serving Size (g)']);
    return '<div class="expand-meta">' + esc(b['Size'] || 'Standard') + ' &middot; ' + esc(b['Type'] || 'Bar') + (sv ? ' &middot; ' + sv + 'g serving' : '') + '</div>' +
      '<div class="expand-buy-row">' + buy + '</div>' +
      '<div class="expand-columns">' +
        '<div class="nutr-panel"><div class="nutr-panel-title">Nutrition Facts</div>' + nutr + '</div>' +
        '<div class="expand-right">' +
          '<div class="score-tile score-band-' + esc(g) + '"><div class="score-tile-header"><div class="score-grade-block">' +
            '<div class="score-header-label">Ingredient Quality Grade</div>' +
            '<div class="score-grade-row"><span class="score-band-badge">' + esc(g) + '</span><span class="score-band-label">' + (WORD[g] || '') + '</span></div>' +
          '</div></div>' + (chips ? '<div class="score-chips">' + chips + '</div>' : '') + '</div>' +
          '<div class="ingr-block"><div class="ingr-label">Ingredients</div><div class="ingr-text">' + esc(b['Ingredients']) + '</div></div>' +
        '</div>' +
      '</div>';
  }
  function toggle(row) {
    var exp = row.nextElementSibling;
    if (!exp) return;
    var open = !exp.hidden;
    if (open) { exp.hidden = true; row.classList.remove('row-open'); row.setAttribute('aria-expanded', 'false'); return; }
    exp.hidden = false; row.classList.add('row-open'); row.setAttribute('aria-expanded', 'true');
    var box = exp.querySelector('.expand-content');
    if (box.getAttribute('data-done')) return;
    box.innerHTML = '<div class="expand-meta">Loading&hellip;</div>';
    loadBars().then(function (m) {
      var b = m[row.getAttribute('data-key')];
      box.innerHTML = b ? panel(b) : '<div class="expand-meta">Details are in the <a href="/bar-finder">Bar Finder</a>.</div>';
      if (b) box.setAttribute('data-done', '1');
    }, function () {
      box.innerHTML = '<div class="expand-meta">Could not load details. Try the <a href="/bar-finder">Bar Finder</a>.</div>';
    });
  }
  Array.prototype.forEach.call(bodies, function (body) {
    body.addEventListener('click', function (e) {
      if (e.target.closest('a')) return;
      var row = e.target.closest('tr.t50-row');
      if (row) toggle(row);
    });
    body.addEventListener('keydown', function (e) {
      if (e.key !== 'Enter' && e.key !== ' ') return;
      if (e.target.closest('a')) return;
      var row = e.target.closest('tr.t50-row');
      if (row) { e.preventDefault(); toggle(row); }
    });
  });
  /* "and 25 more" lists: reveal the rest inline; the button sits after the
     list, so it ends up at the END of the list as "Show less". */
  document.querySelectorAll('.more-toggle').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var rest = btn.previousElementSibling;
      if (!rest) return;
      var open = rest.hidden;
      rest.hidden = !open;
      btn.textContent = open ? 'Show less' : btn.getAttribute('data-more');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  });
  document.querySelectorAll('.faq-q').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var item = btn.closest('.faq-item');
      var isOpen = item.classList.contains('open');
      document.querySelectorAll('.faq-item').forEach(function (i) { i.classList.remove('open'); });
      if (!isOpen) item.classList.add('open');
    });
  });
})();
</script>'''

def v2_shell(page):
    """One-time migration of a v1 guide page to the v2 body. Keeps the <head>
    (and its kyb regions), the nav, and the footer exactly as deployed.
    Drops the v1 body (snapshot, v1 tables, gd-bar-data JSON, v1 inline JS)
    and the visible footer 'Updated' date (spec: no visible date).
    Idempotent: a page that already has the v2 marker is returned unchanged."""
    if '<!-- kyb:v2 -->' in page:
        return page
    a = page.index('<section class="hero page-guide">')
    f0 = page.index('<footer class="site-footer">')
    f1 = page.index('</footer>', f0) + len('</footer>')
    footer = page[f0:f1]
    footer = re.sub(r'<div class="site-footer-copy">knowyourbar\.com\s*&nbsp;&middot;&nbsp;\s*Updated \d{4}-\d{2}-\d{2}</div>',
                    '<div class="site-footer-copy">knowyourbar.com &nbsp;&middot;&nbsp; <a href="/about">About</a></div>', footer)
    tail = page[f1:]
    k = tail.find('<script src="analytics.js"')
    if k == -1:
        raise SystemExit('ERROR: analytics.js tag not found after footer')
    tail = tail[k:]
    head = page[:a].replace('<head>', '<head>\n  <!-- kyb:v2 -->', 1)
    return (head + V2_BODY + footer + '\n<!-- kyb:v2-script -->\n<!-- /kyb:v2-script -->\n\n' + tail)

def v2_shell_upgrade(page):
    """Bring an already-migrated v2 page up to the current V2_BODY (2026-09-29
    QA pass): drop the 'Best 10 at a glance' section, add the bottom author
    region. Idempotent."""
    page = re.sub(r'  <section class="section off" id="at-a-glance">\n<!-- kyb:glance -->.*?<!-- /kyb:glance -->\n  </section>\n',
                  '', page, flags=re.S)
    if '<!-- kyb:author -->' not in page:
        page = page.replace('</main><!-- /content -->', AUTHOR_SECTION + '</main><!-- /content -->', 1)
    return page

AUTHOR_SECTION = '''  <section class="section guide-author-section">
    <div class="section-inner"><!-- kyb:author -->
<!-- /kyb:author --></div>
  </section>
'''

def v2_qa(page, *, n_faq=None):
    """File-size and FAQ-position checks (QA.md section 1b) plus v2 invariants.
    Returns a list of problems (empty = pass)."""
    problems = []
    raw = page.encode('utf-8')
    size = len(raw)
    if size >= V2_MAX_BYTES:
        problems.append(f'HTML is {size:,} bytes, limit {V2_MAX_BYTES:,}')
    for label, needle in (('FAQ', '<section class="guide-faq"'), ('footer', '<footer class="site-footer"')):
        i = page.find(needle)
        off = len(page[:i].encode('utf-8')) if i != -1 else None
        if off is None:
            problems.append(f'{label} section missing')
        elif off >= V2_FAQ_MAX_OFFSET:
            problems.append(f'{label} starts at byte {off:,}, must be under {V2_FAQ_MAX_OFFSET:,}')
    if 'gd-bar-data' in page:
        problems.append('v1 gd-bar-data JSON blob still present')
    types = re.findall(r'"@type":\s*"(Article|Dataset|BreadcrumbList|FAQPage|ItemList)"', page)
    for t in ('Article', 'Dataset', 'BreadcrumbList', 'FAQPage', 'ItemList'):
        if t not in types:
            problems.append(f'missing {t} schema')
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', page, re.S):
        try:
            json.loads(m.group(1))
        except ValueError as e:
            problems.append(f'invalid JSON-LD: {e}')
    if 'Ingredient Quality Score' in page or 'score-number' in page or re.search(r'data-score="', page):
        problems.append('an ingredient quality SCORE is printed on a v2 page (grades only)')
    if re.search(r'Updated \d{4}-\d{2}-\d{2}', re.sub(r'<script.*?</script>', '', page, flags=re.S)):
        problems.append('visible "Updated" date on a v2 page')
    # FAQPage JSON-LD must match the visible FAQ word for word
    m = re.search(r'"@type":"FAQPage","mainEntity":(\[.*?\])\}\s*</script>', page, re.S)
    vis = [(plain_text(q), plain_text(a)) for q, a in re.findall(
        r'<button class="faq-q">(.*?)</button>\s*<div class="faq-a">(.*?)</div>', page, re.S)]
    if m:
        ld = [(x['name'], x['acceptedAnswer']['text']) for x in json.loads(m.group(1))]
        if ld != vis:
            problems.append('FAQPage JSON-LD does not match visible FAQ text')
    else:
        problems.append('FAQPage JSON-LD not found')
    return problems

def build_guide_page_v2(page_path, regions, all_bars, claims, *, picks):
    """Migrate (first run) then fill the v2 regions. dateModified only moves
    when the generated content actually changes (content hash), never
    artificially on a rebuild."""
    claims.stop_if_failed()
    page = v2_shell_upgrade(v2_shell(open(page_path, encoding='utf-8').read()))
    regions = list(regions) + [('v2-script', V2_SCRIPT)]
    digest = _hashlib.sha256('\n'.join(f'{n}\n{c}' for n, c in regions).encode('utf-8')).hexdigest()[:16]
    old = re.search(r'<!-- kyb:content-hash ([0-9a-f]+) -->', page)
    old_mod = re.search(r'"@type": "Article".*?"dateModified": "(\d{4}-\d{2}-\d{2})"', page, re.S)
    if old and old.group(1) == digest and old_mod:
        date_mod = old_mod.group(1)
    else:
        date_mod = today_iso()
    for name, content in regions:
        page = replace_region(page, name, content.replace('__KYB_DATE_MODIFIED__', date_mod))
    page = re.sub(r'[ \t]*<!-- kyb:content-hash [0-9a-f]+ -->\n', '', page)
    page = page.replace('<!-- kyb:v2 -->', f'<!-- kyb:v2 -->\n  <!-- kyb:content-hash {digest} -->', 1)
    problems = v2_qa(page)
    # Best 10 cards: grade badges must match bars.js
    by_name = {(esc(b['Brand Name']), esc(b['Flavor Name'])): b for b in all_bars}
    for brand, flavor, gr in re.findall(r'<div class="pick-tile-brand">(.*?)</div>\s*<div class="pick-tile-flavor-name">(.*?)</div>.*?table-grade-badge grade-(\w)"', page, re.S):
        b = by_name.get((brand, flavor))
        if b is None or b.get('score_band') != gr:
            problems.append(f'pick card grade mismatch: {brand} | {flavor}')
    for bad in ['href="Yes"', 'href="None"', '—', '&mdash;']:
        if bad in page:
            problems.append(f'forbidden: {bad!r}')
    if len(picks) != 10 or len({b['Key'] for _s, b, _w, _n in picks}) != 10:
        problems.append('Best 10 is not 10 distinct bars')
    if problems:
        print('V2 QA FAILED, page not written:')
        for p in problems:
            print('  ', p)
        _sys.exit(1)
    open(page_path, 'w', encoding='utf-8').write(page)
    return page

# ---- v2 shared helpers added with the 2026-09-29 rollout (no-artificial-
# sweeteners, gluten-free, no-seed-oils). Page structure is unchanged; these
# only factor out pieces the pilot builder wrote inline. ----------------------
V2_SWEETENERS = [('dates', r'\bdates?\b'), ('honey', r'\bhoney\b'), ('maple syrup', r'maple syrup'),
                 ('cane sugar', r'cane sugar'), ('coconut sugar', r'coconut sugar'), ('allulose', r'allulose'),
                 ('monk fruit', r'monk ?fruit|luo han'), ('stevia', r'stevia|reb ?a\b|rebaudioside'),
                 ('brown rice syrup', r'brown rice syrup'), ('agave', r'agave'), ('tapioca syrup', r'tapioca syrup'),
                 ('sucralose', r'sucralose'), ('erythritol', r'erythritol'), ('maltitol', r'maltitol'),
                 ('fruit', r'\b(?:raisins?|figs?|apricots?|cherries|cranberries|apples?|bananas?)\b')]

def lead_sweetener(b, sweeteners=V2_SWEETENERS):
    """The sweetener named earliest on the label (None if none of the list)."""
    t, best = ingr(b), None
    for name, rx in sweeteners:
        m = re.search(rx, t, re.I)
        if m and (best is None or m.start() < best[1]):
            best = (name, m.start())
    return best[0] if best else None

def brand_sweetener(bars, sweeteners=V2_SWEETENERS):
    """Most common lead sweetener across a brand's bars."""
    c = Counter_(x for x in (lead_sweetener(b, sweeteners) for b in bars) if x)
    return c.most_common(1)[0][0] if c else None

def section_cta_html(href, label, note):
    """Big Bar Finder button inside a section (spec v2: never an inline text link)."""
    return (f'<div class="section-cta">\n        <a href="{esc(href)}" class="finder-cta-btn section-cta-btn">{label}</a>\n'
            f'        <p class="section-cta-note">{esc(note)}</p>\n      </div>')

def v2_count_card_html(label, bars_hit, total, desc, names=None):
    """Editorial count card (N bars, share of total, description, optional
    'Found in' brand list that expands inline)."""
    n = len(bars_hit)
    names = sorted({b['Brand Name'] for b in bars_hit}, key=str.lower) if names is None else names
    return (f'<div class="score-card">\n          <div class="score-card-label">{esc(label)}</div>\n'
            f'          <div class="score-card-val">{comma(n)} bar{"" if n == 1 else "s"}<span class="oil-card-pct">{esc(pct0(n, total))}%</span></div>\n'
            f'          <div class="score-card-desc">{esc(desc)}</div>'
            + (f'\n          {more_list_html(names)}' if names else '') + '\n        </div>')

def slot_highest_fiber():
    return Slot('Highest fiber', 'The most fiber, grade B or better, 10g+ protein.', lambda E: E,
                lambda b: (-FIB(b),) + tie_chain(b),
                lambda b, c: f"{fnum(FIB(b))}g fiber, {c['tied']}the most of any bar here, with {fnum(P(b))}g protein.",
                metric=FIB)
