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

GUIDE_FILTERS = {
    'no-sugar-alcohols': lambda b: not has_tag(b, 'Sugar Alcohols'),
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
        and (num(b.get('Sugar Alcohol (g)')) or 0) == 0 and b.get('score_band') in ('A', 'B')),
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
