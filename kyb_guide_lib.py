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

def amazon_url(b):
    return _url(b.get('Amazon Affiliate'))

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
    return sorted(bars, key=lambda b: (-(score(b) or -999), b['Brand Name'].lower(), b['Flavor Name'].lower()))

def bar_table(bars, all_bars, eager=30):
    """Returns (tbody_inner_html, lazy_json_text) for a guide's bar list.
    First `eager` rows get a server-rendered expand panel, the rest load
    from the gd-bar-data JSON block on first click."""
    ranker = Ranker(all_bars)
    rows, lazy = [], []
    for idx, b in enumerate(sort_for_list(bars)):
        rec = lazy_record(b, idx, ranker)
        rows.append(bar_row_html(b, idx))
        if idx < eager:
            rows.append(f'<tr class="ingr-row" id="ingr-{idx}"><td colspan="11" class="ingr-cell"><div class="expand-content">{expand_html(rec)}</div></td></tr>')
        else:
            rows.append(f'<tr class="ingr-row" id="ingr-{idx}" style="display:none;"><td colspan="11" class="ingr-cell"><div class="expand-content" data-pending="1"></div></td></tr>')
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
                      r'<div class="bar-brand">(.*?)</div>\s*<div class="bar-flavor">(.*?)</div>.*?'
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
