#!/usr/bin/env python3
"""
Build soy-free-protein-bars.html from live bars.js.
Filter: `Soy Free (Y/N)` = Yes (certification field, no macro/ingredient-
quality gate) -- see GUIDE_CRITERIA.md.

Reference pattern: gluten-free-protein-bars.html / vegan-protein-bars.html
(same filter shape: a pure certification field, not a computed macro/
ingredient screen). Nav/footer spliced from gluten-free-protein-bars.html
since it is the most recently shipped guide and carries the full 11-guide
nav/footer link set.
"""
import json, re, html as html_mod
from collections import defaultdict

REPO = '.'
OUT = './soy-free-protein-bars.html'

with open(f'{REPO}/bars.js') as f:
    content = f.read()
BARS = json.loads(content[content.index('['):content.rindex(']')+1])
TOTAL = len(BARS)

CERT_FIELD_ORDER = [
    ('Kosher (Y/N)', 'Kosher'),
    ('Vegan (Y/N)', 'Vegan'),
    ('Non-GMO (Y/N)', 'Non-GMO'),
    ('Soy Free (Y/N)', 'Soy Free'),
    ('Soy Free (Y/N)', 'Soy Free'),
    ('Gluten Free (Y/N)', 'Gluten Free'),
    ('Nut Free (Y/N)', 'Nut Free'),
]

def is_yes(v):
    return v == 'Yes'

def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None

def fnum(n):
    if n is None:
        return ''
    if abs(n - round(n)) < 1e-9:
        return str(int(round(n)))
    return f'{n:.1f}'

def esc(s):
    if s is None:
        return ''
    return html_mod.escape(str(s), quote=True)

QUALIFY = [b for b in BARS if is_yes(b.get('Soy Free (Y/N)'))]
DISQUALIFY = [b for b in BARS if not is_yes(b.get('Soy Free (Y/N)'))]
QN, DN = len(QUALIFY), len(DISQUALIFY)
assert QN + DN == TOTAL

# ---------------------------------------------------------------------------
# Snapshot stats
# ---------------------------------------------------------------------------
A_GRADE_Q = sum(1 for b in QUALIFY if b.get('score_band') == 'A')
BRANDS_Q = sorted(set(b['Brand Name'] for b in QUALIFY))
AVG_PROTEIN_Q = sum(num(b.get('Protein (g)')) or 0 for b in QUALIFY) / QN
AVG_PROTEIN_ALL = sum(num(b.get('Protein (g)')) or 0 for b in BARS) / TOTAL
AVG_FIBER_Q = sum(num(b.get('Dietary Fiber (g)')) or 0 for b in QUALIFY) / QN
AVG_FIBER_ALL = sum(num(b.get('Dietary Fiber (g)')) or 0 for b in BARS) / TOTAL
AVG_SCORE_Q = sum(num(b.get('ingredient_score')) or 0 for b in QUALIFY) / QN
AVG_SCORE_ALL = sum(num(b.get('ingredient_score')) or 0 for b in BARS) / TOTAL
AB_RATE_Q = round(100 * sum(1 for b in QUALIFY if b.get('score_band') in ('A', 'B')) / QN, 1)
AB_RATE_ALL = round(100 * sum(1 for b in BARS if b.get('score_band') in ('A', 'B')) / TOTAL, 1)
PCT_QUALIFY = round(100 * QN / TOTAL, 1)
PCT_DISQUALIFY = round(100 * DN / TOTAL, 1)

# ---------------------------------------------------------------------------
# Soy-source category explainer (informational only, computed against the
# disqualified set -- mirrors GUIDE_CRITERIA.md's note on the Vegan/Gluten
# Free/Dairy Free guides' category explainers: this does not affect who
# qualifies, `Soy Free (Y/N) = Yes` is the only qualification filter).
#
# Three named soy sources, same shape as Dairy Free's Whey/Milk/Casein split:
# Soy Protein (isolate/concentrate/flour, or "plant protein(s) (soy, ...)"
# blend labels), Soy Lecithin (incl. "lecithin (soy)" / "lecithins (soy)"
# reversed-order labeling, common on imported/European-formatted bars), and
# Soybean Oil. A bare `\bsoy\b` catch-all was tested and dropped as a fourth
# factor: it only ever fires on top of the three named ones above, except for
# a single "may contain ... wheat, and soy" cross-contact allergen disclaimer
# (Honey Stinger Chocolate Chocolate Chip) -- that is not an actual soy
# ingredient, so it correctly falls into the unlabeled bucket, same call the
# site made on oats for the Gluten Free guide and "may contain" statements
# generally.
# ---------------------------------------------------------------------------
def ingr(b):
    return b.get('Ingredients') or ''

SOY_PROTEIN_PAT = re.compile(r'soy protein|textured soy|soy flour|isolated soy protein|proteins?\s*\(soy\b|\(soy,')
SOY_LECITHIN_PAT = re.compile(r'soy lecithin|lecithins?\s*\(soy\)')
SOYBEAN_OIL_PAT = re.compile(r'soybean oil|soy oil')

def matches_disq(pat):
    out = []
    for b in DISQUALIFY:
        text = ingr(b).lower()
        if pat.search(text):
            out.append(b)
    return out

WHEY_HITS = matches_disq(SOY_PROTEIN_PAT)
MILK_HITS = matches_disq(SOY_LECITHIN_PAT)
CASEIN_HITS = matches_disq(SOYBEAN_OIL_PAT)
UNION_KEYS = set(b['Key'] for b in WHEY_HITS) | set(b['Key'] for b in MILK_HITS) | set(b['Key'] for b in CASEIN_HITS)
UNLABELED_HITS = [b for b in DISQUALIFY if b['Key'] not in UNION_KEYS]

def brand_split(hits, n=4):
    brands = sorted(set(b['Brand Name'] for b in hits))
    return brands[:n], brands[n:]

WHEY_BRANDS_SHOWN, WHEY_BRANDS_MORE = brand_split(WHEY_HITS)
MILK_BRANDS_SHOWN, MILK_BRANDS_MORE = brand_split(MILK_HITS)
CASEIN_BRANDS_SHOWN, CASEIN_BRANDS_MORE = brand_split(CASEIN_HITS)

# ---------------------------------------------------------------------------
# Top picks (6) -- every one a real computed max/min over the qualifying set
# ---------------------------------------------------------------------------
def top_level_ingredient_count(text):
    if not text:
        return None
    if text.count('(') != text.count(')') or text.count('[') != text.count(']'):
        return None
    depth, count = 0, 1
    for ch in text:
        if ch in '([':
            depth += 1
        elif ch in ')]':
            depth = max(0, depth - 1)
        elif ch == ',' and depth == 0:
            count += 1
    return count

def net_carbs(b):
    c = num(b.get('Total Carbohydrates (g)'))
    if c is None:
        return None
    return c - (num(b.get('Dietary Fiber (g)')) or 0) - (num(b.get('Sugar Alcohol (g)')) or 0)

MALTITOL_FAMILY = ['maltitol', 'polyglycitol', 'hydrogenated starch hydrolysate']
def has_maltitol_family(b):
    return any(m in ingr(b).lower() for m in MALTITOL_FAMILY)

def p100(b):
    p, c = num(b.get('Protein (g)')), num(b.get('Calories'))
    if not p or not c:
        return None
    return round(p / c * 100, 1)

# Top Picks Selection rule (GUIDE_CRITERIA.md, "Top Picks Selection"): band,
# not raw ingredient_score, is the quality signal. Find the best score_band
# actually present in the qualifying set and restrict every tile except
# "Best overall" to that band, tiebreaking on the guide-specific stat, and
# never repeat a bar across the 6 tiles. Only "Best overall" is allowed to be
# purely quality-anchored.
BAND_ORDER = ['A', 'B', 'C', 'D', 'F']
_bands_present = set(b.get('score_band') for b in QUALIFY)
BEST_BAND = next(b for b in BAND_ORDER if b in _bands_present)
BAND_POOL = [b for b in QUALIFY if b.get('score_band') == BEST_BAND]
print(f"\nTop Picks band restriction: best band present = {BEST_BAND} ({len(BAND_POOL)} of {QN} qualifying bars)")

_used_keys = set()
def claim(bar):
    _used_keys.add(bar['Key'])
    return bar

def best_in_band(metric_fn, pool=None, fallback_pool=None):
    pool = pool if pool is not None else BAND_POOL
    candidates = [b for b in pool if b['Key'] not in _used_keys and metric_fn(b) is not None]
    if not candidates and fallback_pool is not None:
        candidates = [b for b in fallback_pool if b['Key'] not in _used_keys and metric_fn(b) is not None]
    return claim(max(candidates, key=metric_fn))

best_overall = claim(max(BAND_POOL, key=lambda b: num(b.get('ingredient_score')) or -999))
best_p100 = best_in_band(p100, fallback_pool=QUALIFY)
best_protein = best_in_band(lambda b: num(b.get('Protein (g)')) or -1, fallback_pool=QUALIFY)

def neg_ingredient_count(b):
    c = top_level_ingredient_count(ingr(b))
    return -c if c is not None else None
cleanest = best_in_band(neg_ingredient_count, fallback_pool=QUALIFY)
cleanest_count = top_level_ingredient_count(ingr(cleanest))

most_fiber = best_in_band(lambda b: num(b.get('Dietary Fiber (g)')) or -1, fallback_pool=QUALIFY)

def keto_metric(b):
    nc = net_carbs(b)
    if nc is None or nc > 8 or (num(b.get('Protein (g)')) or 0) < 10 or (num(b.get('Total Fat (g)')) or 0) < 8 or has_maltitol_family(b):
        return None
    return num(b.get('ingredient_score')) or -999
keto_candidates = [b for b in QUALIFY if keto_metric(b) is not None]
KETO_COUNT = len(keto_candidates)
best_keto = best_in_band(keto_metric, fallback_pool=QUALIFY)

PICKS = [
    dict(label='Best overall', bar=best_overall,
         reason=f"{fnum(num(best_overall.get('Protein (g)')))}g protein at {fnum(num(best_overall.get('Calories')))} calories on a short, mostly whole-food list. Highest ingredient quality score of any soy free bar in the database."),
    dict(label='Best protein/calorie ratio', bar=best_p100,
         reason=f"{fnum(num(best_p100.get('Protein (g)')))}g protein at just {fnum(num(best_p100.get('Calories')))} calories, {p100(best_p100)}g of protein per 100 calories, the most efficient split among all {QN} soy free bars."),
    dict(label='Best total protein', bar=best_protein,
         reason=f"{fnum(num(best_protein.get('Protein (g)')))}g protein, the highest raw protein count of any soy free bar we track. Most high-protein bars lean on soy protein isolate to get there, so a soy free bar hitting this number is worth knowing about."),
    dict(label='Cleanest ingredient list', bar=cleanest,
         reason=f"Just {cleanest_count} ingredients: {ingr(cleanest)}."),
    dict(label='Most fiber', bar=most_fiber,
         reason=f"{fnum(num(most_fiber.get('Dietary Fiber (g)')))}g fiber and {fnum(num(most_fiber.get('Protein (g)')))}g protein in one bar, the most fiber of any soy free bar in the database."),
    dict(label='Best for keto', bar=best_keto,
         reason=f"{fnum(net_carbs(best_keto))}g net carbs ({fnum(num(best_keto.get('Total Carbohydrates (g)')))}g total carbs minus {fnum(num(best_keto.get('Dietary Fiber (g)')))}g fiber), {fnum(num(best_keto.get('Protein (g)')))}g protein, {fnum(num(best_keto.get('Total Fat (g)')))}g fat. One of {KETO_COUNT} soy free bars that also clears a keto-level carb screen."),
]

for p in PICKS:
    b = p['bar']
    if b.get('score_band') not in ('A', 'B'):
        p['reason'] += f" The tradeoff: a {b.get('score_band')} grade."

print("=== TOP PICKS ===")
for p in PICKS:
    b = p['bar']
    print(p['label'], '->', b['Brand Name'], '|', b['Flavor Name'], b.get('score_band'))

# ---------------------------------------------------------------------------
# Findings section data
# ---------------------------------------------------------------------------
RECOGNIZABLE = ['Quest', 'CLIF Bar', 'Barebells', 'KIND', 'RXBAR', 'Built', 'Power Crunch', 'Atkins', 'Pure Protein', 'ONE Bar']
whey_brand_set = set(b['Brand Name'] for b in WHEY_HITS)
featured_whey_brand = next((br for br in RECOGNIZABLE if br in whey_brand_set), sorted(whey_brand_set)[0])
featured_whey_count = sum(1 for b in WHEY_HITS if b['Brand Name'] == featured_whey_brand)
featured_whey_total = sum(1 for b in BARS if b['Brand Name'] == featured_whey_brand)

print("\nFeatured soy-protein brand:", featured_whey_brand, featured_whey_count, "/", featured_whey_total)
print("Soy protein:", len(WHEY_HITS), round(100*len(WHEY_HITS)/TOTAL, 1), "%")
print("Soy lecithin:", len(MILK_HITS), round(100*len(MILK_HITS)/TOTAL, 1), "%")
print("Soybean oil:", len(CASEIN_HITS), round(100*len(CASEIN_HITS)/TOTAL, 1), "%")
print("Unlabeled/no-visible-soy disqualified:", len(UNLABELED_HITS), round(100*len(UNLABELED_HITS)/TOTAL, 1), "%")

# ---------------------------------------------------------------------------
# Brand tables: Consider / Avoid / Mixed
# ---------------------------------------------------------------------------
BY_BRAND = defaultdict(list)
for b in BARS:
    BY_BRAND[b['Brand Name']].append(b)

WHEY_KEYS = set(b['Key'] for b in WHEY_HITS)
MILK_KEYS = set(b['Key'] for b in MILK_HITS)
CASEIN_KEYS = set(b['Key'] for b in CASEIN_HITS)

def grade_range(bars):
    grades = sorted(set(b['score_band'] for b in bars if b.get('score_band')))
    if not grades:
        return None, None
    return min(grades), max(grades)

def culprit_for(disq_bars):
    has_whey = any(b['Key'] in WHEY_KEYS for b in disq_bars)
    has_milk = any(b['Key'] in MILK_KEYS for b in disq_bars)
    has_casein = any(b['Key'] in CASEIN_KEYS for b in disq_bars)
    parts = []
    if has_whey:
        parts.append('Soy Protein')
    if has_milk:
        parts.append('Soy Lecithin')
    if has_casein:
        parts.append('Soybean Oil')
    if parts:
        return ' and '.join(parts)
    return 'Not labeled soy free'

brand_rows = []
for brand, bars in BY_BRAND.items():
    total = len(bars)
    qual = [b for b in bars if b in QUALIFY]
    disq = [b for b in bars if b in DISQUALIFY]
    q, d = len(qual), len(disq)
    grade_pool = qual if qual else bars
    gmin, gmax = grade_range(grade_pool)
    avg_p = sum(num(b.get('Protein (g)')) or 0 for b in grade_pool) / len(grade_pool)
    avg_s = sum(num(b.get('Sugars (g)')) or 0 for b in grade_pool) / len(grade_pool)
    brand_rows.append(dict(brand=brand, total=total, q=q, d=d, gmin=gmin, gmax=gmax,
                            avg_p=avg_p, avg_s=avg_s, qual=qual, disq=disq))

CONSIDER = [r for r in brand_rows if r['total'] > 0 and r['q'] / r['total'] >= 0.75 and (r['total'] - r['q']) <= 2]
AVOID = [r for r in brand_rows if r['total'] > 0 and r['d'] / r['total'] >= 0.80 and r['q'] < 3]
_consider_names = set(r['brand'] for r in CONSIDER)
_avoid_names = set(r['brand'] for r in AVOID)
MIXED = [r for r in brand_rows if r['q'] >= 3 and r['d'] >= 3
         and r['brand'] not in _consider_names and r['brand'] not in _avoid_names]

CONSIDER.sort(key=lambda r: (-r['q'], r['brand']))
AVOID.sort(key=lambda r: (-r['d'], r['brand']))
MIXED.sort(key=lambda r: (-(r['q'] + r['d']), r['brand']))

for r in AVOID:
    r['culprit'] = culprit_for(r['disq'])

for r in MIXED:
    best = max(r['qual'], key=lambda b: num(b.get('ingredient_score')) or -999)
    r['clean_pick'] = best['Flavor Name']

print(f"\nConsider: {len(CONSIDER)} brands, Avoid: {len(AVOID)} brands, Mixed: {len(MIXED)} brands")

# ---------------------------------------------------------------------------
# Macro-rank percentiles against the FULL database (for expand panels)
# ---------------------------------------------------------------------------
RANK_METRICS = [
    ('p', 'Protein (g)', 'highest'),
    ('c', 'Calories', 'lowest'),
    ('s', 'Sugars (g)', 'lowest'),
    ('f', 'Dietary Fiber (g)', 'highest'),
    ('ft', 'Total Fat (g)', None),
]

_sorted_cache = {}
def rank_of(bar, field, direction):
    key = field
    if key not in _sorted_cache:
        vals = [(b['Key'], num(b.get(field))) for b in BARS if num(b.get(field)) is not None]
        vals.sort(key=lambda x: x[1], reverse=(direction == 'highest'))
        _sorted_cache[key] = {k: i + 1 for i, (k, v) in enumerate(vals)}
    return _sorted_cache[key].get(bar['Key'])

def rank_tag(bar, field, direction):
    r = rank_of(bar, field, direction)
    if r is None:
        return ('N/A', 'rank-gray')
    if direction is None:
        return (f'#{r} of {TOTAL}', 'rank-gray')
    pct = r / TOTAL
    cls = 'rank-green' if pct <= 0.25 else ('rank-amber' if pct <= 0.5 else 'rank-gray')
    word = 'lowest' if direction == 'lowest' else 'highest'
    if cls == 'rank-gray':
        return (f'#{r} of {TOTAL}', 'rank-gray')
    return (f'#{r} {word}', cls)


# ======================================================================
# render / assemble
# ======================================================================
DATE_PUBLISHED = '2026-09-17'
DATE_MODIFIED = '2026-09-17'
SLUG = 'soy-free-protein-bars'
URL = f'https://knowyourbar.com/{SLUG}'
N_ROUND = (QN // 10) * 10

def grade_word(band):
    return {'A': 'Clean', 'B': 'Good', 'C': 'Okay', 'D': 'Poor', 'F': 'Avoid'}.get(band, '')

def grade_badge(band):
    return f'<span class="table-grade-badge grade-{band}">{band}</span>'

def grade_range_html(gmin, gmax):
    if gmin is None:
        return ''
    if gmin == gmax:
        return grade_badge(gmin)
    return f'{grade_badge(gmin)}<span class="grade-range-sep">&ndash;</span>{grade_badge(gmax)}'

def buy_links_html(bar, cls_a='amazon-link', cls_v='visit-link'):
    out = ''
    az = bar.get('Amazon Affiliate')
    ws = bar.get('Website')
    if az:
        out += f'<a href="{esc(az)}" target="_blank" rel="noopener sponsored" class="{cls_a}">Shop on Amazon</a>'
    if ws:
        out += f'<a href="{esc(ws)}" target="_blank" rel="noopener" class="{cls_v}">Shop on Brand Site</a>'
    return out

def cert_list(bar):
    return [label for field, label in CERT_FIELD_ORDER if is_yes(bar.get(field))]

def cert_badges_html(bar):
    certs = cert_list(bar)
    shown = certs[:2]
    extra = len(certs) - len(shown)
    out = ''.join(f'<span class="cert-badge">{esc(c)}</span>' for c in shown)
    if extra > 0:
        out += f'<span class="cert-badge-more">+{extra}</span>'
    return out

def expand_certs_line(bar):
    certs = cert_list(bar)
    if not certs:
        return ''
    return f'<div class="expand-certs-line">Certifications: {esc(", ".join(certs))}</div>'

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

def nutr_rows_html(bar):
    out = ''
    for field, label, unit in NUTR_FIELDS:
        v = num(bar.get(field))
        val = f'{fnum(v)}{unit}' if v is not None else '0' + unit
        out += f'<div class="nutr-row"><span class="nutr-label">{label}</span><span class="nutr-val">{val}</span></div>'
    return out

def chip_class(kind):
    return {'positive': 'chip-positive', 'concern': 'chip-concern', 'neutral': 'chip-neutral'}.get(kind, 'chip-neutral')

def parse_chips(bar):
    raw = bar.get('score_insights') or ''
    out = []
    for part in raw.split('|'):
        part = part.strip()
        if not part:
            continue
        pieces = part.split(':')
        name = pieces[0].strip()
        kind = pieces[1].strip() if len(pieces) > 1 else 'neutral'
        out.append((name, kind))
    return out

def ingr_col_items(raw):
    if not raw:
        return ['None flagged']
    items = [x.strip().title() for x in raw.split(',') if x.strip()]
    return items if items else ['None flagged']

def macro_rank_grid_html(bar):
    cells = []
    labels = {'p': 'Protein', 'c': 'Calories', 's': 'Sugar', 'f': 'Fiber', 'ft': 'Fat'}
    units = {'p': 'g', 'c': '', 's': 'g', 'f': 'g', 'ft': 'g'}
    fieldmap = {m[0]: m for m in RANK_METRICS}
    for key in ['p', 'c', 's', 'f', 'ft']:
        _, field, direction = fieldmap[key]
        v = num(bar.get(field))
        vtxt = fnum(v) if v is not None else '0'
        text, cls = rank_tag(bar, field, direction)
        cells.append(f'<div class="macro-rank-cell"><span class="macro-rank-lbl">{labels[key]}</span><span class="macro-rank-val">{vtxt}{units[key]}</span><span class="macro-rank-tag {cls}">{text}</span></div>')
    return ''.join(cells)

def score_tile_html(bar):
    band = bar.get('score_band')
    score = num(bar.get('ingredient_score')) or 0
    pos = num(bar.get('score_pos')) or 0
    neg = num(bar.get('score_neg')) or 0
    total_abs = pos + abs(neg)
    pp = round(100 * pos / total_abs) if total_abs else 100
    npc = 100 - pp
    chips = parse_chips(bar)
    chips_html = ''.join(f'<span class="insight-chip {chip_class(k)}">{esc(n)}</span>' for n, k in chips)
    pos_items = ingr_col_items(bar.get('positive_ingredients'))
    neg_items = ingr_col_items(bar.get('concern_ingredients'))
    pos_html = ''.join(f'<div class="ingr-col-item">{esc(x)}</div>' for x in pos_items)
    neg_html = ''.join(f'<div class="ingr-col-item">{esc(x)}</div>' for x in neg_items)
    return f'''<div class="score-tile score-band-{band}">
  <div class="score-tile-header">
    <div class="score-grade-block"><div class="score-header-label">Ingredient Quality Grade</div>
      <div class="score-grade-row"><span class="score-band-badge">{band}</span><span class="score-band-label">{grade_word(band)}</span></div></div>
    <div class="score-num-block"><div class="score-header-label">Ingredient Quality Score</div><div class="score-number">{fnum(score)}</div></div>
  </div>
  <div class="score-breakdown"><div class="score-breakdown-bar">
    <div class="sbd-pos" style="width:{pp}%" title="Positive contributions: +{fnum(pos)}"></div><div class="sbd-neg" style="width:{npc}%" title="Concern contributions: {fnum(neg)}"></div></div>
    <div class="score-breakdown-labels"><span class="sbd-label-pos">+{fnum(pos)} positive</span><span class="sbd-label-neg">{fnum(neg)} concerns</span></div></div>
  <div class="score-chips">{chips_html}</div>
  <div class="score-ingr-cols">
    <div class="ingr-col"><div class="ingr-col-label ingr-col-pos">Positive Ingredients</div>{pos_html}</div>
    <div class="ingr-col"><div class="ingr-col-label ingr-col-neg">Concern Ingredients</div>{neg_html}</div>
  </div>
</div>'''

def rich_row_html(bar, idx):
    grade = bar.get('score_band')
    score = num(bar.get('ingredient_score')) or 0
    protein = num(bar.get('Protein (g)'))
    cal = num(bar.get('Calories'))
    fat = num(bar.get('Total Fat (g)'))
    carbs = num(bar.get('Total Carbohydrates (g)'))
    fiber = num(bar.get('Dietary Fiber (g)'))
    sugar = num(bar.get('Sugars (g)'))
    sa = num(bar.get('Sugar Alcohol (g)'))
    p100v = round((protein or 0) / cal * 100, 1) if cal else 0
    search = f"{bar['Brand Name']} {bar['Flavor Name']}".lower().replace('"', '')
    bar_row = f'''<tr class="bar-row" data-idx="{idx}" data-score="{score}" data-grade="{grade}" data-protein="{protein or 0}" data-cal="{cal or 0}" data-sugar="{sugar or 0}" data-p100="{p100v}" data-search="{esc(search)}" onclick="toggleIngr({idx}, this)">
  <td class="col-bar">
    <div class="bar-brand">{esc(bar['Brand Name'])}</div>
    <div class="bar-flavor">{esc(bar['Flavor Name'])}</div>
    <svg class="row-expand-icon" width="7" height="12" viewBox="0 0 7 12" fill="none"><path d="M1 1L6 6L1 11" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
  </td>
  <td class="col-num col-hide-mobile">{fnum(cal)}</td>
  <td class="col-num">{fnum(protein)}</td>
  <td class="col-num col-hide-mobile">{p100v}</td>
  <td class="col-num">{fnum(fat)}</td>
  <td class="col-num col-hide-mobile">{fnum(carbs)}</td>
  <td class="col-num">{fnum(fiber)}</td>
  <td class="col-num">{fnum(sugar)}</td>
  <td class="col-num col-hide-mobile">{fnum(sa)}</td>
  <td class="col-certs col-hide-mobile"><div class="cert-badges">{cert_badges_html(bar)}</div></td>
  <td class="col-grade"><span class="table-grade-badge grade-{grade}" title="{grade_word(grade)} &middot; score {fnum(score)}">{grade}</span></td>
</tr>'''
    ingr_row = f'''<tr class="ingr-row" id="ingr-{idx}">
  <td colspan="11" class="ingr-cell">
    <div class="expand-content">
      <div class="expand-meta">{esc(bar.get("Size") or "Standard")} &middot; {esc(bar.get("Type") or "Bar")} &middot; {fnum(num(bar.get("Serving Size (g)")))}g serving</div>
      {expand_certs_line(bar)}
      <div class="expand-buy-row">{buy_links_html(bar)}</div>
      <div class="macro-rank-grid">{macro_rank_grid_html(bar)}</div>
      <div class="expand-columns">
        <div class="nutr-panel">
          <div class="nutr-panel-title">Nutrition Facts</div>
          {nutr_rows_html(bar)}
        </div>
        <div class="expand-right">
          {score_tile_html(bar)}
          <div class="ingr-block">
            <div class="ingr-label">Ingredients</div>
            <div class="ingr-text">{esc(ingr(bar))}</div>
          </div>
        </div>
      </div>
    </div>
  </td>
</tr>'''
    return bar_row + '\n' + ingr_row

def lazy_row_and_record(bar, idx):
    grade = bar.get('score_band')
    score = num(bar.get('ingredient_score')) or 0
    protein = num(bar.get('Protein (g)'))
    cal = num(bar.get('Calories'))
    fat = num(bar.get('Total Fat (g)'))
    carbs = num(bar.get('Total Carbohydrates (g)'))
    fiber = num(bar.get('Dietary Fiber (g)'))
    sugar = num(bar.get('Sugars (g)'))
    sa = num(bar.get('Sugar Alcohol (g)'))
    p100v = round((protein or 0) / cal * 100, 1) if cal else 0
    search = f"{bar['Brand Name']} {bar['Flavor Name']}".lower().replace('"', '')
    bar_row = f'''<tr class="bar-row" data-idx="{idx}" data-score="{score}" data-grade="{grade}" data-protein="{protein or 0}" data-cal="{cal or 0}" data-sugar="{sugar or 0}" data-p100="{p100v}" data-search="{esc(search)}" onclick="toggleIngr({idx}, this)">
  <td class="col-bar">
    <div class="bar-brand">{esc(bar['Brand Name'])}</div>
    <div class="bar-flavor">{esc(bar['Flavor Name'])}</div>
    <svg class="row-expand-icon" width="7" height="12" viewBox="0 0 7 12" fill="none"><path d="M1 1L6 6L1 11" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
  </td>
  <td class="col-num col-hide-mobile">{fnum(cal)}</td>
  <td class="col-num">{fnum(protein)}</td>
  <td class="col-num col-hide-mobile">{p100v}</td>
  <td class="col-num">{fnum(fat)}</td>
  <td class="col-num col-hide-mobile">{fnum(carbs)}</td>
  <td class="col-num">{fnum(fiber)}</td>
  <td class="col-num">{fnum(sugar)}</td>
  <td class="col-num col-hide-mobile">{fnum(sa)}</td>
  <td class="col-certs col-hide-mobile"><div class="cert-badges">{cert_badges_html(bar)}</div></td>
  <td class="col-grade"><span class="table-grade-badge grade-{grade}" title="{grade_word(grade)} &middot; score {fnum(score)}">{grade}</span></td>
</tr>'''
    ingr_row = f'<tr class="ingr-row" id="ingr-{idx}" data-lazy="1"><td colspan="11" class="ingr-cell"><div class="expand-content" data-pending="1"></div></td></tr>'

    rk = {}
    fieldmap = {m[0]: m for m in RANK_METRICS}
    for key in ['p', 'c', 's', 'f', 'ft']:
        _, field, direction = fieldmap[key]
        text, cls = rank_tag(bar, field, direction)
        rk[key] = [text, cls]

    chips = parse_chips(bar)
    pos = num(bar.get('score_pos')) or 0
    neg = num(bar.get('score_neg')) or 0
    total_abs = pos + abs(neg)
    pp = round(100 * pos / total_abs) if total_abs else 100
    npc = 100 - pp

    record = {
        'i': idx,
        'sz': bar.get('Size') or 'Standard',
        'ty': bar.get('Type') or 'Bar',
        'sv': fnum(num(bar.get('Serving Size (g)'))),
        'ct': cert_list(bar),
        'az': bar.get('Amazon Affiliate'),
        'ws': bar.get('Website'),
        'rk': rk,
        'pv': protein or 0,
        'cv': fnum(cal),
        'sv2': fnum(sugar),
        'fv': fnum(fiber),
        'ftv': fat or 0,
        'nu': [[label, (f'{fnum(num(bar.get(field)))}{unit}' if num(bar.get(field)) is not None else f'0{unit}')] for field, label, unit in NUTR_FIELDS],
        'gr': grade,
        'gl': grade_word(grade),
        'sc': score,
        'pp': pp,
        'np': npc,
        'ps': pos,
        'ns': neg,
        'ch': [[n, chip_class(k)] for n, k in chips],
        'pi': ingr_col_items(bar.get('positive_ingredients')),
        'ni': ingr_col_items(bar.get('concern_ingredients')),
        'ing': ingr(bar),
    }
    return bar_row + '\n' + ingr_row, record

# ---------------------------------------------------------------------------
# TITLE / META / HERO copy
# ---------------------------------------------------------------------------
TITLE = f"{PCT_QUALIFY:.0f}% of Protein Bars Are Soy Free. See All {QN}."
H1 = f"Best Soy Free Protein Bars - Ranking {N_ROUND}+ Qualified Bars"
META_DESC = f"We checked {TOTAL:,} protein bars against their soy free label. {QN} qualify. See every one, ranked by ingredient quality, brand, and macros."
OG_DESC = f"{QN} soy free protein bars with no soy protein, soy lecithin, or soybean oil in the recipe. Ranked by ingredient quality score."
HERO_SUB = (f"We checked {TOTAL:,} protein bars available in the US against their Soy Free (Y/N) label. "
            f"The result: {QN} bars, about {PCT_QUALIFY:.0f}%, are labeled soy free. Most of the rest carry soy lecithin as an emulsifier or soy protein to boost the protein count. "
            f"We rank the best soy free protein bars by ingredient quality, brand, and macros. Not just us telling you the flavors we like.")

def pick_tile_html(p):
    b = p['bar']
    grade = b.get('score_band')
    return f'''<div class="macro-card pick-tile">
  <div class="pick-tile-body">
    <div class="pick-tile-category">{esc(p['label'])}</div>
    <div class="pick-tile-brand">{esc(b['Brand Name'])}</div>
    <div class="pick-tile-flavor-name">{esc(b['Flavor Name'])}</div>
    <p class="pick-tile-reason">{esc(p['reason'])}</p>
  </div>
  <div class="pick-tile-footer">
    <div class="pick-tile-quality">
      <span class="pick-tile-quality-label">Ingredient Quality</span>
      <span class="table-grade-badge grade-{grade}">{grade}</span>
      <span class="pick-tile-quality-word">{grade_word(grade)}</span>
    </div>
    <div class="bar-links">{buy_links_html(b)}</div>
  </div>
</div>'''

PICKS_HTML = '\n'.join(pick_tile_html(p) for p in PICKS)
PICKS_ITEMLIST = ',\n'.join(
    f'      {{\n            "@type": "ListItem",\n            "position": {i+1},\n            "name": {json.dumps(p["bar"]["Brand Name"] + " " + p["bar"]["Flavor Name"])}\n      }}'
    for i, p in enumerate(PICKS))

def factor_card_html(label, count, pct, desc, brands_shown, brands_more):
    brands_line = ', '.join(esc(b) for b in brands_shown)
    details = ''
    if brands_more:
        more_csv = ', '.join(esc(b) for b in brands_more)
        details = f'''<details class="oil-card-more"><summary><span class="oil-card-more-text">and {len(brands_more)} more</span><span class="oil-card-less-text">Hide</span></summary><span class="oil-card-more-list">, {more_csv}</span></details>'''
    return f'''<div class="score-card">
  <div class="score-card-label">{esc(label)}</div>
  <div class="score-card-val">{count} bars<span class="oil-card-pct">{pct}%</span></div>
  <div class="score-card-desc">{esc(desc)}</div>
  <div class="oil-card-brands"><span class="oil-card-brands-label">Found in:</span> {brands_line}{details}</div>
</div>'''

WHEY_PCT = round(100 * len(WHEY_HITS) / TOTAL, 1)
MILK_PCT = round(100 * len(MILK_HITS) / TOTAL, 1)
CASEIN_PCT = round(100 * len(CASEIN_HITS) / TOTAL, 1)
UNLABELED_PCT = round(100 * len(UNLABELED_HITS) / TOTAL, 1)

FACTOR_WHEY = factor_card_html(
    'Soy Protein', len(WHEY_HITS), WHEY_PCT,
    'Soy protein isolate, concentrate, or flour, usually added as a cheap way to boost the protein count, sometimes as part of a multi-source "plant protein" blend.',
    WHEY_BRANDS_SHOWN, WHEY_BRANDS_MORE)
FACTOR_MILK = factor_card_html(
    'Soy Lecithin', len(MILK_HITS), MILK_PCT,
    'An emulsifier that keeps the bar from separating, usually appearing low in the ingredient list. Imported and European-formatted bars often reverse the label to "lecithin (soy)".',
    MILK_BRANDS_SHOWN, MILK_BRANDS_MORE)
FACTOR_CASEIN = factor_card_html(
    'Soybean Oil', len(CASEIN_HITS), CASEIN_PCT,
    'Used as a coating fat or moisture binder, most often in chocolate or peanut-butter-style coatings. The least common of the three named soy sources.',
    CASEIN_BRANDS_SHOWN, CASEIN_BRANDS_MORE)
FACTOR_UNLABELED = f'''<div class="score-card">
  <div class="score-card-label">Not labeled soy free</div>
  <div class="score-card-val">{len(UNLABELED_HITS)} bars<span class="oil-card-pct">{UNLABELED_PCT}%</span></div>
  <div class="score-card-desc">No soy protein, soy lecithin, or soybean oil shows up anywhere in the ingredient list we can find, but the brand hasn't labeled or certified the bar soy free either. That is a labeling gap, not proof the bar contains soy.</div>
</div>'''

CATEGORY_EXPLAINER_P1 = (f"We check the Soy Free (Y/N) label on file for every bar, then cross-check ingredient lists ourselves for soy protein, soy lecithin, and soybean oil, "
                         f"the three named soy sources that show up most in the data. {QN} of {TOTAL:,} bars, about {PCT_QUALIFY:.0f}%, carry a soy free label. "
                         f"The other {DN}, about {PCT_DISQUALIFY:.0f}%, don't.")
CATEGORY_EXPLAINER_P2 = (f"Soy lecithin is the most common named source at {len(MILK_HITS)} bars ({MILK_PCT}% of the full database), added as an emulsifier rather than a protein source, "
                         f"which is why it shows up even in bars that don't lean on soy for protein. Soy protein (isolate, concentrate, or flour) appears in {len(WHEY_HITS)} bars ({WHEY_PCT}%), "
                         f"and soybean oil in {len(CASEIN_HITS)} bars ({CASEIN_PCT}%). "
                         f"The remaining {len(UNLABELED_HITS)} bars, {UNLABELED_PCT}% of the full database, show no soy protein, soy lecithin, or soybean oil in their own ingredient list at all. "
                         f"They just aren't labeled soy free, which is a different claim from actually containing soy.")

fully_df_brands = [r for r in CONSIDER if r['q'] == r['total']]
fully_df_top = sorted(fully_df_brands, key=lambda r: -r['total'])[:4]
fully_df_names = ', '.join(f"{r['brand']} ({r['total']})" for r in fully_df_top)

nugo = next((r for r in MIXED if r['brand'] == 'Larabar'), None)
if nugo is None:
    nugo = MIXED[0] if MIXED else None

# Why do soy free bars grade higher on average? NOT because soy protein or soy
# lecithin are themselves penalized -- checked against the scoring schema
# (knowyourbar_scoring_schema_v11.xlsx, Canonical_Ingredients sheet): soy
# protein isolate scores +3, soy protein +2, soy protein concentrate +2 (all
# positive, protein/plant_protein), soy lecithin scores 0 (neutral,
# emulsifier), only soybean oil scores -1 (fat_oil/refined_or_seed_oil,
# same bucket as other seed oils). So soy itself is mostly neutral-to-positive
# in this scoring system. The real driver is correlation, not causation: soy
# free bars in this database co-occur heavily with two real concern tags.
def has_tag(b, tag):
    return tag in (b.get('score_insights') or '')

ARTIFICIAL_SW_PCT_Q = round(100 * sum(1 for b in QUALIFY if has_tag(b, 'Artificial Sweeteners')) / QN, 1)
ARTIFICIAL_SW_PCT_ALL = round(100 * sum(1 for b in BARS if has_tag(b, 'Artificial Sweeteners')) / TOTAL, 1)
PROCESSED_OILS_PCT_Q = round(100 * sum(1 for b in QUALIFY if has_tag(b, 'Processed Oils')) / QN, 1)
PROCESSED_OILS_PCT_ALL = round(100 * sum(1 for b in BARS if has_tag(b, 'Processed Oils')) / TOTAL, 1)

BIG_STAT_NUM = f"{AB_RATE_Q}%"
BIG_STAT_HEAD = "of soy free protein bars grade A or B for ingredient quality, well above the database average"
BIG_STAT_DETAIL = (f"Soy free bars grade A or B {AB_RATE_Q}% of the time, against {AB_RATE_ALL}% database-wide. "
                   f"That's not because soy itself is penalized. Soy protein isolate actually scores well in our system, and soy lecithin is neutral. "
                   f"The real pattern: soy free bars carry artificial sweeteners in just {ARTIFICIAL_SW_PCT_Q}% of cases, versus {ARTIFICIAL_SW_PCT_ALL}% database-wide, and processed oils in {PROCESSED_OILS_PCT_Q}% versus {PROCESSED_OILS_PCT_ALL}%. "
                   f"Brands that skip soy tend to skip those two ingredient categories as well.")

INSIGHTS = [
    ("Soy lecithin is the clearest single soy source, not soy protein.",
     f"{len(MILK_HITS)} bars ({MILK_PCT}% of the database) name soy lecithin directly, more than the soy protein and soybean oil counts combined. It's an emulsifier, not a protein play, so it shows up even in bars that aren't trying to add soy."),
    (f"{featured_whey_brand} shows the soy-protein pattern clearly.",
     f"{featured_whey_count} of {featured_whey_brand}'s {featured_whey_total} flavors use soy protein directly. None of {featured_whey_brand}'s flavors are labeled soy free."),
    (f"{len(fully_df_brands)} brands are soy free across their entire lineup.",
     f"Led by {fully_df_names}, these brands build around a protein and emulsifier system that never touches soy in any form, rather than swapping it out flavor by flavor."),
    ("Soy free bars grade higher, but not because of the soy itself.",
     f"Soy protein isolate scores well in our system and soy lecithin is neutral, so cutting soy doesn't directly raise a bar's grade. What correlates is cleaner sweeteners and fats: soy free bars carry artificial sweeteners {ARTIFICIAL_SW_PCT_Q}% of the time versus {ARTIFICIAL_SW_PCT_ALL}% database-wide, and processed oils {PROCESSED_OILS_PCT_Q}% versus {PROCESSED_OILS_PCT_ALL}%."),
    ("Soy free bars average less protein, more fiber.",
     f"Soy free bars average {fnum(AVG_PROTEIN_Q)}g of protein against a database-wide average of {fnum(AVG_PROTEIN_ALL)}g, since soy protein isolate is a common way brands hit high protein numbers and soy free bars can't use it. They average more fiber instead ({fnum(AVG_FIBER_Q)}g vs. {fnum(AVG_FIBER_ALL)}g), typically from nuts, oats, or dates instead of an isolated protein powder."),
    ((f"{nugo['brand']} splits closer to even than most brands." if nugo else "Mixed lineups are rare."),
     (f"{nugo['q']} of {nugo['brand']}'s {nugo['total']} flavors are soy free, the rest are not. Always check the specific flavor, not just the brand."
      if nugo else "Most brands are either fully soy free or not soy free at all; very few split their lineup.")),
]

INSIGHTS_HTML = '\n'.join(
    f'<div class="insight-item"><div class="insight-dot"></div><div class="insight-head">{esc(h)}</div><div class="insight-detail">{esc(d)}</div></div>'
    for h, d in INSIGHTS)

def consider_row(r):
    return (f'<tr><td><button type="button" class="brand-jump" data-brand="{esc(r["brand"])}">{esc(r["brand"])}</button></td>'
            f'<td>{r["total"]}</td><td>{grade_range_html(r["gmin"], r["gmax"])}</td>'
            f'<td>{fnum(r["avg_p"])}g</td><td>{fnum(r["avg_s"])}g</td><td>Soy free across the whole lineup</td></tr>')

def avoid_row(r, hidden):
    cls = 'avoid-row brand-row-hidden" style="display:none;' if hidden else 'avoid-row'
    return (f'<tr class="{cls}"><td><span class="brand-name-static">{esc(r["brand"])}</span></td>'
            f'<td>{r["d"]}/{r["total"]}</td><td>{grade_range_html(r["gmin"], r["gmax"])}</td>'
            f'<td>{fnum(r["avg_p"])}g</td><td>{fnum(r["avg_s"])}g</td><td>{esc(r["culprit"])}</td></tr>')

def mixed_row(r):
    return (f'<tr><td><button type="button" class="brand-jump" data-brand="{esc(r["brand"])}">{esc(r["brand"])}</button></td>'
            f'<td>{r["q"]}/{r["total"]}</td><td>{grade_range_html(r["gmin"], r["gmax"])}</td>'
            f'<td>{fnum(r["avg_p"])}g</td><td>{fnum(r["avg_s"])}g</td><td>{esc(r["clean_pick"])} is the soy free pick</td></tr>')

CONSIDER_ROWS = '\n'.join(consider_row(r) for r in CONSIDER)
AVOID_VISIBLE = AVOID[:15]
AVOID_HIDDEN = AVOID[15:]
AVOID_ROWS = '\n'.join(avoid_row(r, False) for r in AVOID_VISIBLE) + '\n' + '\n'.join(avoid_row(r, True) for r in AVOID_HIDDEN)
MIXED_ROWS = '\n'.join(mixed_row(r) for r in MIXED)

AVOID_SHOW_MORE = ''
if AVOID_HIDDEN:
    AVOID_SHOW_MORE = f'''<button type="button" class="brand-table-show-more" id="sf-avoid-show-more" data-hidden-count="{len(AVOID_HIDDEN)}">Show {len(AVOID_HIDDEN)} more brands</button>
<script>
(function() {{
  var btn = document.getElementById('sf-avoid-show-more');
  var table = document.getElementById('sf-avoid-table');
  if (!btn || !table) return;
  btn.addEventListener('click', function() {{
    var hidden = table.querySelectorAll('.brand-row-hidden');
    hidden.forEach(function(row) {{ row.style.display = ''; row.classList.remove('brand-row-hidden'); }});
    btn.classList.add('is-hidden');
  }});
}})();
</script>'''

SORTED_QUALIFY = sorted(QUALIFY, key=lambda b: (-(num(b.get('ingredient_score')) or -999), b['Brand Name'], b['Flavor Name']))
RICH_BATCH = 60

rich_html_parts = []
lazy_html_parts = []
lazy_records = []
for idx, bar in enumerate(SORTED_QUALIFY):
    if idx < RICH_BATCH:
        rich_html_parts.append(rich_row_html(bar, idx))
    else:
        row_html, record = lazy_row_and_record(bar, idx)
        lazy_html_parts.append(row_html)
        lazy_records.append(record)

BAR_ROWS_HTML = '\n'.join(rich_html_parts) + '\n' + '\n'.join(lazy_html_parts)
GD_BAR_DATA_JSON = json.dumps(lazy_records, separators=(',', ':'))

for rec in lazy_records:
    if rec.get('az') in ('Yes', 'None') or rec.get('ws') in ('Yes', 'None'):
        raise SystemExit(f"BROKEN LINK FIELD in lazy record {rec['i']}: az={rec.get('az')} ws={rec.get('ws')}")
for bar in SORTED_QUALIFY[:RICH_BATCH]:
    if bar.get('Amazon Affiliate') in ('Yes', 'None') or bar.get('Website') in ('Yes', 'None'):
        raise SystemExit(f"BROKEN LINK FIELD in rich row: {bar['Brand Name']} {bar['Flavor Name']}")
print("Broken link-field scan: PASS")

FAQ = [
    ("What makes a protein bar soy free on this site?",
     f"We use the Soy Free (Y/N) label on file for each bar. {QN} of the {TOTAL:,} bars we track carry that label. We also cross-check ingredient lists ourselves for soy protein, soy lecithin, and soybean oil, the three named soy sources that show up most in the data."),
    ("How many soy free protein bars are in your database?",
     f"{QN} of the {TOTAL:,} bars we track are labeled soy free, spanning {len(BRANDS_Q)} brands. {A_GRADE_Q} of those {QN} bars grade A for ingredient quality."),
    (f"Is {featured_whey_brand} soy free?",
     f"No. {featured_whey_count} of {featured_whey_brand}'s {featured_whey_total} flavors use soy protein directly, and none of {featured_whey_brand}'s flavors carry a soy free label."),
    ("What is the most common soy ingredient in protein bars?",
     f"Soy lecithin, not soy protein. It shows up by name in {len(MILK_HITS)} of the {TOTAL:,} bars we track, more than soy protein and soybean oil combined, since it's used as a cheap emulsifier in all kinds of bars, not just ones built around a soy protein source."),
    ("Does not being labeled soy free mean a bar contains soy?",
     f"Not necessarily. {len(UNLABELED_HITS)} of the {DN} bars that don't carry our soy free label show no soy protein, soy lecithin, or soybean oil anywhere in their own ingredient list. The brand just hasn't labeled or certified the bar, which is a different claim from it containing soy."),
    ("Can a brand have some soy free flavors and some that aren't?",
     (f"Yes. {nugo['brand']} is a good example: {nugo['q']} of {nugo['total']} flavors are soy free, the rest are not. Always check the specific flavor, not just the brand."
      if nugo else "Yes, though it's uncommon in this database. Always check the specific flavor, not just the brand.")),
    ("What protein bars are soy free?",
     f"{QN} bars across {len(BRANDS_Q)} brands carry a soy free label. The full ranked list is in the table below, sorted by ingredient quality."),
    ("What protein bars are not soy free?",
     f"{DN} of the {TOTAL:,} bars we track don't carry a soy free label. Soy lecithin is the most common named reason, followed by soy protein and soybean oil. Most of the remaining bars simply haven't been labeled, without an identifiable soy ingredient in the list."),
    ("Are soy free protein bars lower quality than regular bars?",
     f"No, the opposite. Soy free bars in our database grade A or B {AB_RATE_Q}% of the time, well above the {AB_RATE_ALL}% database-wide rate. That's not because soy itself is penalized, soy protein isolate actually scores well in our system and soy lecithin is neutral. It's correlation: brands that skip soy also tend to skip artificial sweeteners ({ARTIFICIAL_SW_PCT_Q}% of soy free bars vs. {ARTIFICIAL_SW_PCT_ALL}% database-wide) and processed oils ({PROCESSED_OILS_PCT_Q}% vs. {PROCESSED_OILS_PCT_ALL}%). What soy free bars give up on average is protein: they average {fnum(AVG_PROTEIN_Q)}g against a database-wide average of {fnum(AVG_PROTEIN_ALL)}g, since soy protein isolate is a common way brands hit high protein numbers."),
    ("Is soy free the same as vegan?",
     "No. A soy free bar just has no soy protein, soy lecithin, or soybean oil. It can still contain whey, milk, honey, egg white protein, collagen, or gelatin, none of which are vegan. Check our Vegan Protein Bars guide separately if that's what you need."),
    ("How often is this list updated?",
     f"We update the database whenever new bars are added or a brand reformulates. Manufacturers do change their ingredient lists over time, so always confirm against the packaging in front of you. This page reflects the database as of {DATE_MODIFIED}."),
]

FAQ_HTML = '\n'.join(
    f'<div class="faq-item">\n  <button class="faq-q">{esc(q)}</button>\n  <div class="faq-a">{esc(a)}</div>\n</div>'
    for q, a in FAQ)
FAQ_JSONLD = ',\n'.join(
    f'      {{\n            "@type": "Question",\n            "name": {json.dumps(q)},\n            "acceptedAnswer": {{\n                  "@type": "Answer",\n                  "text": {json.dumps(a)}\n            }}\n      }}'
    for q, a in FAQ)

print("Assembled copy + tables OK")
print("TITLE:", TITLE, len(TITLE))
print("H1:", H1)
print("META_DESC:", META_DESC, len(META_DESC))
print("Bar rows built:", len(SORTED_QUALIFY), "rich:", min(RICH_BATCH, len(SORTED_QUALIFY)), "lazy:", max(0, len(SORTED_QUALIFY)-RICH_BATCH))
print("FAQ count:", len(FAQ))

# ---------------------------------------------------------------------------
# Nav / footer -- spliced from creatine-protein-bars.html (most recently
# shipped guide, carries the full current 14-guide nav/footer link set),
# with this guide's own link appended after High Fiber (the last guide link
# in that set).
# ---------------------------------------------------------------------------
with open(f'{REPO}/high-fiber-protein-bars.html') as f:
    GF_SRC = f.read()

def extract(src, start_marker, end_marker):
    i = src.index(start_marker)
    j = src.index(end_marker, i)
    return src[i:j]

NAV_BLOCK = extract(GF_SRC, '<nav class="site-nav">', '</nav>') + '</nav>'
NAV_BLOCK = NAV_BLOCK.replace(
    '<a href="/creatine-protein-bars">Creatine Protein Bars</a>\n      </div>',
    '<a href="/creatine-protein-bars">Creatine Protein Bars</a>\n        <a href="/soy-free-protein-bars">Soy Free Protein Bars</a>\n      </div>'
)
NAV_TOGGLE_SCRIPT = extract(GF_SRC, "<script>\n(function() {\n  var navToggle", "})();\n</script>") + "})();\n</script>"

FOOTER_BLOCK = extract(GF_SRC, '<footer class="site-footer">', '</footer>') + '</footer>'
FOOTER_BLOCK = FOOTER_BLOCK.replace(
    '<a href="/creatine-protein-bars">Creatine Protein Bars</a>\n    </nav>',
    '<a href="/creatine-protein-bars">Creatine Protein Bars</a>\n      <a href="/soy-free-protein-bars">Soy Free Protein Bars</a>\n    </nav>'
)
FOOTER_BLOCK = re.sub(r'Updated \d{4}-\d{2}-\d{2}', f'Updated {DATE_MODIFIED}', FOOTER_BLOCK)

_ms_start = GF_SRC.index('<script>\n(function() {\n  var tbody')
_ms_analytics = GF_SRC.index('<script src="analytics.js"', _ms_start)
_ms_close = GF_SRC.rindex('</script>', _ms_start, _ms_analytics)
MAIN_SCRIPT = GF_SRC[_ms_start:_ms_close] + '</script>'

assert 'soy-free-protein-bars' in NAV_BLOCK
assert 'soy-free-protein-bars' in FOOTER_BLOCK
assert 'buildLazyExpand' in MAIN_SCRIPT and 'faq-q' in MAIN_SCRIPT and 'jumpToBrand' in MAIN_SCRIPT
print("Nav/footer spliced OK, main script extracted OK, len=", len(MAIN_SCRIPT))

SNAPSHOT_METRICS = [
    (str(A_GRADE_Q), 'A-grade bars'),
    (str(len(BRANDS_Q)), 'Brands represented'),
    (f'{fnum(AVG_PROTEIN_Q)}g', 'Avg protein'),
]

PAGE = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <!-- Analytics -->
  <script>
window.dataLayer = window.dataLayer || [];
function gtag(){{dataLayer.push(arguments);}}
gtag('js', new Date());
gtag('config', 'G-SW4MNP5W7J');
(function(){{
  var loaded = false;
  function loadGtag(){{
    if (loaded) return;
    loaded = true;
    var s = document.createElement('script');
    s.async = true;
    s.src = 'https://www.googletagmanager.com/gtag/js?id=G-SW4MNP5W7J';
    document.head.appendChild(s);
  }}
  if (document.readyState === 'complete') {{
    loadGtag();
  }} else {{
    window.addEventListener('load', loadGtag);
  }}
  setTimeout(loadGtag, 4000);
}})();
</script>

  <!-- Core meta -->
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc(TITLE)}</title>
  <meta name="description" content="{esc(META_DESC)}">
  <link rel="canonical" href="{URL}">

  <!-- Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&family=Barlow+Condensed:wght@500;600;700;800;900&family=IBM+Plex+Mono:wght@400;500;600&display=swap">
  <link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&family=Barlow+Condensed:wght@500;600;700;800;900&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet" media="print" onload="this.media='all'; this.onload=null;">
  <noscript><link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&family=Barlow+Condensed:wght@500;600;700;800;900&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet"></noscript>

  <!-- Shared styles -->
  <link rel="stylesheet" href="/style.css">

  <!-- JSON-LD: Article -->
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": {json.dumps(H1)},
    "description": {json.dumps(META_DESC)},
    "url": "{URL}",
    "image": "https://knowyourbar.com/bar_hero.png",
    "datePublished": "{DATE_PUBLISHED}",
    "dateModified": "{DATE_MODIFIED}",
    "author": {{ "@type": "Organization", "name": "Know Your Bar", "url": "https://knowyourbar.com" }},
    "publisher": {{ "@type": "Organization", "name": "Know Your Bar", "url": "https://knowyourbar.com" }},
    "mainEntityOfPage": {{ "@type": "WebPage", "@id": "{URL}" }},
    "about": {{ "@type": "Thing", "name": "Soy Free Protein Bars" }}
  }}
  </script>

  <!-- JSON-LD: Dataset -->
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "Know Your Bar Protein Bar Ingredient Quality Database",
    "description": "1,000+ protein bars across 150+ brands scored A through F for ingredient quality. Each bar is parsed ingredient by ingredient against a canonical scoring schema. Data includes macros, certifications, ingredient scores, and insight chips for every bar.",
    "url": "https://knowyourbar.com",
    "creator": {{ "@type": "Organization", "name": "Know Your Bar", "url": "https://knowyourbar.com" }},
    "dateModified": "{DATE_MODIFIED}",
    "license": "https://creativecommons.org/licenses/by-nc/4.0/",
    "variableMeasured": ["Ingredient quality grade (A through F)", "Ingredient quality score", "Macronutrients", "Dietary certifications"],
    "measurementTechnique": "Proprietary ingredient scoring algorithm mapping each ingredient to a canonical base score weighted by position in ingredient list",
    "spatialCoverage": "United States",
    "temporalCoverage": "2026"
  }}
  </script>

  <!-- JSON-LD: BreadcrumbList -->
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
      {{ "@type": "ListItem", "position": 1, "name": "Know Your Bar", "item": "https://knowyourbar.com" }},
      {{ "@type": "ListItem", "position": 2, "name": "Lifestyle Guides", "item": "https://knowyourbar.com" }},
      {{ "@type": "ListItem", "position": 3, "name": {json.dumps(H1)}, "item": "{URL}" }}
    ]
  }}
  </script>

  <!-- JSON-LD: ItemList (top picks) -->
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "ItemList",
    "name": "Top picks for soy free protein bars",
    "itemListElement": [

{PICKS_ITEMLIST}

    ]
  }}
  </script>

  <!-- JSON-LD: FAQPage -->
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
{FAQ_JSONLD}
]
  }}
  </script>

  <!-- Open Graph -->
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="Know Your Bar">
  <meta property="og:title" content="{esc(TITLE)}">
  <meta property="og:description" content="{esc(OG_DESC)}">
  <meta property="og:url" content="{URL}">
  <meta property="og:image" content="https://knowyourbar.com/bar_hero.png">

  <!-- Twitter card -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(TITLE)}">
  <meta name="twitter:description" content="{esc(OG_DESC)}">
  <meta name="twitter:image" content="https://knowyourbar.com/bar_hero.png">

</head>
<body class="page-guide brand-v1">

{NAV_BLOCK}
{NAV_TOGGLE_SCRIPT}

<section class="hero page-guide">
  <div class="hero-inner">
    <h1 class="hero-title">{esc(H1)}</h1>
    <p class="hero-sub" style="color:#e8e4dc;">{esc(HERO_SUB)}</p>
  </div>
</section>

<section class="snapshot">
  <div class="snapshot-inner">
    <div class="snap-item"><div class="snap-value">{QN}</div><div class="snap-label">Bars qualify</div></div>
    <div class="snap-item"><div class="snap-value">{DN}</div><div class="snap-label">Bars disqualified</div></div>
    <div class="snap-item"><div class="snap-value">{SNAPSHOT_METRICS[0][0]}</div><div class="snap-label">{SNAPSHOT_METRICS[0][1]}</div></div>
    <div class="snap-item"><div class="snap-value">{SNAPSHOT_METRICS[1][0]}</div><div class="snap-label">{SNAPSHOT_METRICS[1][1]}</div></div>
    <div class="snap-item"><div class="snap-value">{SNAPSHOT_METRICS[2][0]}</div><div class="snap-label">{SNAPSHOT_METRICS[2][1]}</div></div>
  </div>
</section>

<main class="content">

  <section class="section">
    <div class="section-inner">
      <h2 class="section-title">Top picks for soy free protein bars</h2>
      <p class="section-body">Everyone has their own reason for wanting a protein bar, but if you're on this page, you already know you want one that's soy free. Here are the best bars for what people typically look for, all soy free. Grades below reflect ingredient quality only, not an overall bar rating.</p>
      <div class="macro-grid pick-tile-grid top-picks-6">
{PICKS_HTML}
      </div>
    </div>
  </section>

  <section class="section off">
    <div class="section-inner">
      <h2 class="section-title">What disqualifies a protein bar from being soy free</h2>
      <div class="section-body">
        <p>{esc(CATEGORY_EXPLAINER_P1)}</p>
        <p>{esc(CATEGORY_EXPLAINER_P2)}</p>
      </div>
      <div class="score-grid" style="margin-top:1.5rem;">
{FACTOR_WHEY}
{FACTOR_MILK}
{FACTOR_CASEIN}
{FACTOR_UNLABELED}
      </div>
    </div>
  </section>

  <section class="findings">
    <div class="findings-inner">
      <h2 class="findings-title">What we found screening {TOTAL:,} bars</h2>
      <div class="big-stat">
        <div class="big-stat-num">{BIG_STAT_NUM}</div>
        <div>
          <div class="big-stat-head">{esc(BIG_STAT_HEAD)}</div>
          <div class="big-stat-detail">{esc(BIG_STAT_DETAIL)}</div>
        </div>
      </div>
      <div class="insights-grid">
{INSIGHTS_HTML}
      </div>
    </div>
  </section>

  <section class="section">
    <div class="section-inner">
      <h2 class="section-title">Best Brands of Soy Free Protein Bars</h2>
      <div class="section-body">
        <p>Some brands build their whole lineup without soy protein, soy lecithin, or soybean oil, others lean on it across the board. Grade columns below show ingredient quality only, not an overall bar rating. Click any brand name to jump to its flavors in the table below.</p>
      </div>

      <div class="brand-table-block">
        <div class="brand-table-label pro">Brands to Consider</div>
        <div class="brand-table-note">Every flavor from these {len(CONSIDER)} brands is soy free.</div>
        <div class="table-scroll">
          <table class="brand-table">
            <thead><tr><th>Brand</th><th>Total Flavors</th><th>Ingredient Quality</th><th>Avg Protein</th><th>Avg Sugar</th><th>Note</th></tr></thead>
            <tbody>
{CONSIDER_ROWS}
            </tbody>
          </table>
        </div>
      </div>

      <div class="brand-table-block">
        <div class="brand-table-label con">Brands to Avoid</div>
        <div class="brand-table-note">These brands lean on soy protein, soy lecithin, soybean oil, or an unlabeled formula across most or all of their lineup.</div>
        <div class="table-scroll">
          <table class="brand-table" id="sf-avoid-table">
            <thead><tr><th>Brand</th><th>Flavors Without Soy Free Label</th><th>Ingredient Quality</th><th>Avg Protein</th><th>Avg Sugar</th><th>Soy Source Found</th></tr></thead>
            <tbody>
{AVOID_ROWS}
            </tbody>
          </table>
        </div>
        {AVOID_SHOW_MORE}
      </div>

      <div class="brand-table-block">
        <div class="brand-table-label mixed">Mixed Lineups, Check the Flavor</div>
        <div class="brand-table-note">Some flavors are soy free, some aren't. Check the specific flavor before buying.</div>
        <div class="table-scroll">
          <table class="brand-table">
            <thead><tr><th>Brand</th><th>Soy Free Flavors</th><th>Ingredient Quality</th><th>Avg Protein</th><th>Avg Sugar</th><th>Soy Free Pick</th></tr></thead>
            <tbody>
{MIXED_ROWS}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </section>

  <section class="bars-section">
    <div class="bars-section-inner">
      <h2 class="section-title">{QN} soy free protein bars, ranked by ingredient quality</h2>
      <p class="section-body">Every soy free bar in the database, sorted best to worst by ingredient quality grade. Use the sort dropdown to re-rank by protein, calories, or sugar instead, or filter by grade. Tap any row for the full macro rank, ingredient breakdown, and buy links.</p>

      <div class="gd-filter-bar">
        <div class="gd-filter-chips" id="gd-grade-chips">
          <button class="gd-chip" data-grade="all" aria-pressed="true">All grades</button>
          <button class="gd-chip" data-grade="A" aria-pressed="false">A</button>
          <button class="gd-chip" data-grade="B" aria-pressed="false">B</button>
          <button class="gd-chip" data-grade="C" aria-pressed="false">C</button>
          <button class="gd-chip" data-grade="D" aria-pressed="false">D</button>
          <button class="gd-chip" data-grade="F" aria-pressed="false">F</button>
        </div>
        <div class="gd-filter-controls">
          <input type="text" id="gd-search" class="gd-search" placeholder="Search brand or flavor">
          <select id="gd-sort" class="gd-sort">
            <option value="score-desc">Sort: Best ingredient score</option>
            <option value="protein-desc">Sort: Most protein</option>
            <option value="cal-asc">Sort: Fewest calories</option>
            <option value="sugar-asc">Sort: Lowest sugar</option>
            <option value="p100-desc">Sort: Best protein per 100 cal</option>
          </select>
        </div>
      </div>
      <div class="gd-result-count" id="gd-result-count">Showing 30 of {QN} bars</div>

      <div class="bar-table-wrap">
        <div class="table-scroll">
          <table>
            <thead>
              <tr>
                <th class="col-bar">BAR</th>
                <th class="col-num col-hide-mobile" title="Calories">CAL</th>
                <th class="col-num" title="Protein (g)">PROT</th>
                <th class="col-num col-hide-mobile" title="Protein per 100 calories">P/100</th>
                <th class="col-num" title="Total Fat (g)">FAT</th>
                <th class="col-num col-hide-mobile" title="Total Carbohydrates (g)">CARB</th>
                <th class="col-num" title="Dietary Fiber (g)">FIBR</th>
                <th class="col-num" title="Sugars (g)">SGR</th>
                <th class="col-num col-hide-mobile" title="Sugar Alcohol (g)">SGR ALC</th>
                <th class="col-certs col-hide-mobile">CERTS</th>
                <th class="col-grade" title="Ingredient Quality Grade">GRADE</th>
              </tr>
            </thead>
            <tbody id="gd-tbody">
{BAR_ROWS_HTML}
            </tbody>
          </table>
        </div>
      </div>

      <div class="show-more-wrap" id="show-more-wrap">
        <button class="gd-show-more-btn show-more-btn" id="gd-show-more">Show more bars</button>
      </div>

      <script type="application/json" id="gd-bar-data">{GD_BAR_DATA_JSON}</script>

    </div>
  </section>

  <section class="section guide-finder-cta">
    <div class="explore-cta-grid">
      <div class="explore-cta-main">
        <h2 class="explore-cta-main-heading">See every bar that fits, not just the {QN} on this page</h2>
        <p class="explore-cta-main-desc">This guide covers soy free bars specifically. The Bar Finder covers all {TOTAL:,}+ bars in the database, and you set the filters: protein, sugar, fiber, calories, ingredient grade, brand, certifications, and specific ingredients to exclude. No sponsored picks, no subjective taste tests. You decide what matters.</p>
        <a href="/bar-finder?certs=Soy%20Free" class="finder-cta-btn">Open the Bar Finder &rarr;</a>
      </div>
      <div class="explore-cta-side">
        <a href="/ingredient_scoring" class="explore-cta-side-link">How we score &rarr;</a>
        <ul class="explore-cta-side-list">
          <li>Every ingredient is scored individually against a canonical database, not just flagged good or bad</li>
          <li>Position in the ingredient list matters, earlier ingredients carry more weight</li>
          <li>Each bar's total becomes a single letter grade, A through F</li>
        </ul>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="section-inner">
      <div class="explore-more-label">Explore more</div>
      <div class="explore-more-grid">
        <a href="/dairy-free-protein-bars" class="explore-more-card">
          <div class="explore-more-title">Dairy Free Protein Bars</div>
          <div class="explore-more-desc">Bars with no whey, milk, or casein in the recipe.</div>
        </a>
        <a href="/vegan-protein-bars" class="explore-more-card">
          <div class="explore-more-title">Vegan Protein Bars</div>
          <div class="explore-more-desc">Bars with no whey, milk, honey, egg, or gelatin.</div>
        </a>
        <a href="/clean-protein-bars" class="explore-more-card">
          <div class="explore-more-title">Clean Protein Bars</div>
          <div class="explore-more-desc">A/B graded bars with no artificial sweeteners or seed oils.</div>
        </a>
      </div>
    </div>
  </section>

  <section class="guide-faq">
    <div class="guide-faq-inner">
      <h2 class="section-title">Frequently asked questions</h2>
      <div class="faq-items">
{FAQ_HTML}
      </div>
    </div>
  </section>

</main><!-- /content -->

{FOOTER_BLOCK}

{MAIN_SCRIPT}

<script src="analytics.js" defer></script>
</body>
</html>
'''

with open(OUT, 'w') as f:
    f.write(PAGE)

print(f"\nWrote {OUT}, {len(PAGE):,} bytes")
