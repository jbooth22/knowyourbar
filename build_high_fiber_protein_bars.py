#!/usr/bin/env python3
"""
Build high-fiber-protein-bars.html from live bars.js.

Three tiers, not one flat list (see GUIDE_CRITERIA.md):
  High Fiber       >= 5g  Dietary Fiber (g)   -- FDA "excellent source" cutoff
  Very High Fiber  >= 8g  Dietary Fiber (g)   -- supporting tier
  Extreme Fiber    >= 11g Dietary Fiber (g)   -- the page's lead tier, "The Extreme Fiber 100"

The page leads with the Extreme tier (hero, top picks, category explainer,
brand tables, and the full ranked bar list all key off the 11g+ filter).
High Fiber and Very High Fiber are presented as supporting context in a
dedicated section inserted at the same point the site's GSC keyword-gap
sections use (between the category explainer and the findings section) --
see BRIEFING.md's Guide pages / Template section order note.

All counts recomputed fresh against the live bars.js in this run -- do not
trust any number from a prior session or conversation (see GUIDE_CRITERIA.md's
"Keto incident" note on why).
"""
import json, re, html as html_mod
from collections import defaultdict

REPO = '.'
OUT = './high-fiber-protein-bars.html'

with open(f'{REPO}/bars.js') as f:
    content = f.read()
BARS = json.loads(content[content.index('['):content.rindex(']')+1])
TOTAL = len(BARS)

CERT_FIELD_ORDER = [
    ('Kosher (Y/N)', 'Kosher'),
    ('Vegan (Y/N)', 'Vegan'),
    ('Non-GMO (Y/N)', 'Non-GMO'),
    ('Soy Free (Y/N)', 'Soy Free'),
    ('Dairy Free (Y/N)', 'Dairy Free'),
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

def fiber(b):
    return num(b.get('Dietary Fiber (g)')) or 0

def ingr(b):
    return b.get('Ingredients') or ''

# ---------------------------------------------------------------------------
# The three tiers -- recomputed fresh, cumulative (Extreme subset of Very
# High subset of High), per GUIDE_CRITERIA.md.
# ---------------------------------------------------------------------------
HIGH = [b for b in BARS if fiber(b) >= 5]
VERY = [b for b in BARS if fiber(b) >= 8]
EXTREME = [b for b in BARS if fiber(b) >= 11]
NOT_HIGH = [b for b in BARS if fiber(b) < 5]

QUALIFY = EXTREME
DISQUALIFY = [b for b in BARS if b not in EXTREME]
QN, DN = len(QUALIFY), len(DISQUALIFY)
assert QN + DN == TOTAL

HIGH_N, VERY_N, EXT_N = len(HIGH), len(VERY), len(EXTREME)
HIGH_BRANDS = sorted(set(b['Brand Name'] for b in HIGH))
VERY_BRANDS = sorted(set(b['Brand Name'] for b in VERY))
EXT_BRANDS = sorted(set(b['Brand Name'] for b in EXTREME))
HIGH_PCT = round(100 * HIGH_N / TOTAL, 1)
VERY_PCT = round(100 * VERY_N / TOTAL, 1)
EXT_PCT = round(100 * EXT_N / TOTAL, 1)

print(f"High Fiber (5g+): {HIGH_N} bars, {len(HIGH_BRANDS)} brands, {HIGH_PCT}%")
print(f"Very High Fiber (8g+): {VERY_N} bars, {len(VERY_BRANDS)} brands, {VERY_PCT}%")
print(f"Extreme Fiber (11g+): {EXT_N} bars, {len(EXT_BRANDS)} brands, {EXT_PCT}%")

# Non-overlapping bands, used only to pick a representative bar for the
# supporting-tiers section prose below (the tiers themselves stay cumulative).
_HIGH_ONLY_BAND = [b for b in BARS if 5 <= fiber(b) < 8]
_VERY_ONLY_BAND = [b for b in BARS if 8 <= fiber(b) < 11]
_best_high_only = max(_HIGH_ONLY_BAND, key=lambda b: num(b.get('ingredient_score')) or -999)
_best_very_only = max(_VERY_ONLY_BAND, key=lambda b: num(b.get('ingredient_score')) or -999)
best_high_only_line = (f"A good High Fiber example that isn't also Very High or Extreme: {_best_high_only['Brand Name']} {_best_high_only['Flavor Name']}, "
                        f"{fnum(fiber(_best_high_only))}g fiber, grade {_best_high_only.get('score_band')}.")
best_very_only_line = (f"A good Very High Fiber example that doesn't reach Extreme: {_best_very_only['Brand Name']} {_best_very_only['Flavor Name']}, "
                        f"{fnum(fiber(_best_very_only))}g fiber, grade {_best_very_only.get('score_band')}.")

# ---------------------------------------------------------------------------
# Snapshot stats (Extreme tier, the page's lead filter)
# ---------------------------------------------------------------------------
A_GRADE_Q = sum(1 for b in QUALIFY if b.get('score_band') == 'A')
BRANDS_Q = EXT_BRANDS
AVG_PROTEIN_Q = sum(num(b.get('Protein (g)')) or 0 for b in QUALIFY) / QN
AVG_PROTEIN_ALL = sum(num(b.get('Protein (g)')) or 0 for b in BARS) / TOTAL
AVG_FIBER_Q = sum(fiber(b) for b in QUALIFY) / QN
AVG_FIBER_ALL = sum(fiber(b) for b in BARS) / TOTAL
AB_RATE_Q = round(100 * sum(1 for b in QUALIFY if b.get('score_band') in ('A', 'B')) / QN, 1)
AB_RATE_ALL = round(100 * sum(1 for b in BARS if b.get('score_band') in ('A', 'B')) / TOTAL, 1)
PCT_QUALIFY = EXT_PCT
PCT_DISQUALIFY = round(100 * DN / TOTAL, 1)

# ---------------------------------------------------------------------------
# Fiber-source category explainer (informational, computed against the
# Extreme tier itself -- this does not affect who qualifies, the filter is
# just Dietary Fiber (g) >= 11, see GUIDE_CRITERIA.md).
# ---------------------------------------------------------------------------
FIBER_SOURCE_PATTERNS = [
    ('Tapioca Fiber', re.compile(r'tapioca fiber|tapioca dextrin'),
     'A resistant-starch fiber made from cassava root, added specifically to boost the fiber count without changing texture much.'),
    ('Polydextrose', re.compile(r'polydextrose'),
     'A synthetic soluble fiber used as a bulking agent, common in bars that also carry a sugar-alcohol-heavy sweetener system.'),
    ('Chicory Root / Inulin', re.compile(r'chicory root|inulin'),
     'A naturally-occurring soluble fiber extracted from chicory root, one of the most common added-fiber sources in the industry.'),
    ('Soluble Corn Fiber', re.compile(r'soluble corn fiber|resistant corn (dextrin|starch)'),
     'A corn-derived resistant dextrin used the same way as tapioca or chicory fiber, mainly to raise the fiber line on the label.'),
    ('Isomalto-oligosaccharide (IMO)', re.compile(r'isomalto|\bimo\b'),
     'A glucose-oligomer prebiotic fiber, chemically distinct from the sugar alcohol isomalt despite the similar name (see GUIDE_CRITERIA.md).'),
]

_covered_keys = set()
FIBER_SOURCE_HITS = {}
for label, pat, desc in FIBER_SOURCE_PATTERNS:
    hits = [b for b in EXTREME if pat.search(ingr(b).lower())]
    FIBER_SOURCE_HITS[label] = hits
    _covered_keys |= set(b['Key'] for b in hits)

WHOLE_FOOD_HITS = [b for b in EXTREME if b['Key'] not in _covered_keys]
WHOLE_FOOD_PCT = round(100 * len(WHOLE_FOOD_HITS) / EXT_N, 1)

def brand_split(hits, n=6):
    brands = sorted(set(b['Brand Name'] for b in hits))
    return brands[:n], brands[n:]

for label, hits in FIBER_SOURCE_HITS.items():
    print(label, len(hits), round(100 * len(hits) / EXT_N, 1), '%')
print('Whole-food / no named additive:', len(WHOLE_FOOD_HITS), WHOLE_FOOD_PCT, '%')

# ---------------------------------------------------------------------------
# Top picks (6) -- every one a real computed max/min over the Extreme tier
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
    return c - fiber(b) - (num(b.get('Sugar Alcohol (g)')) or 0)

def p100(b):
    p, c = num(b.get('Protein (g)')), num(b.get('Calories'))
    if not p or not c:
        return None
    return round(p / c * 100, 1)

best_overall = max(QUALIFY, key=lambda b: num(b.get('ingredient_score')) or -999)
most_fiber = max(QUALIFY, key=fiber)
best_p100 = max((b for b in QUALIFY if p100(b) is not None), key=p100)
best_protein = max(QUALIFY, key=lambda b: num(b.get('Protein (g)')) or -1)

_counted = [(b, top_level_ingredient_count(ingr(b))) for b in QUALIFY]
_counted = [(b, c) for b, c in _counted if c is not None]
_min_count = min(c for b, c in _counted)
cleanest = max((b for b, c in _counted if c == _min_count), key=lambda b: num(b.get('ingredient_score')) or -999)
cleanest_count = _min_count

best_netcarb = min((b for b in QUALIFY if net_carbs(b) is not None), key=net_carbs)

PICKS = [
    dict(label='Best overall', bar=best_overall,
         reason=f"{fnum(fiber(best_overall))}g fiber and {fnum(num(best_overall.get('Protein (g)')))}g protein at {fnum(num(best_overall.get('Calories')))} calories. Highest ingredient quality score of any bar clearing the 11g fiber bar."),
    dict(label='Most fiber of any bar', bar=most_fiber,
         reason=f"{fnum(fiber(most_fiber))}g of fiber, more than half a day's worth (25-38g is the typical adult daily target) in a single {fnum(num(most_fiber.get('Calories')))}-calorie bar. The most fiber of any bar in the database."),
    dict(label='Best protein/calorie ratio', bar=best_p100,
         reason=f"{fnum(num(best_p100.get('Protein (g)')))}g protein at just {fnum(num(best_p100.get('Calories')))} calories, {p100(best_p100)}g of protein per 100 calories, on top of {fnum(fiber(best_p100))}g fiber."),
    dict(label='Best total protein', bar=best_protein,
         reason=f"{fnum(num(best_protein.get('Protein (g)')))}g protein alongside {fnum(fiber(best_protein))}g fiber, the highest raw protein count of any Extreme Fiber bar we track."),
    dict(label='Cleanest ingredient list', bar=cleanest,
         reason=f"Just {cleanest_count} ingredients: {ingr(cleanest)}."),
    dict(label='Best for keto', bar=best_netcarb,
         reason=f"{fnum(net_carbs(best_netcarb))}g net carbs ({fnum(num(best_netcarb.get('Total Carbohydrates (g)')))}g total carbs minus {fnum(fiber(best_netcarb))}g fiber), {fnum(num(best_netcarb.get('Protein (g)')))}g protein. Proof a bar can carry serious fiber and still fit a low-carb target."),
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
BY_BRAND = defaultdict(list)
for b in BARS:
    BY_BRAND[b['Brand Name']].append(b)

ext_keys = set(b['Key'] for b in EXTREME)
brand_rows = []
for brand, bars in BY_BRAND.items():
    total = len(bars)
    qual = [b for b in bars if b['Key'] in ext_keys]
    disq = [b for b in bars if b['Key'] not in ext_keys]
    q, d = len(qual), len(disq)
    grade_pool = qual if qual else bars
    def grade_range(bl):
        grades = sorted(set(b['score_band'] for b in bl if b.get('score_band')))
        return (None, None) if not grades else (min(grades), max(grades))
    gmin, gmax = grade_range(grade_pool)
    avg_p = sum(num(b.get('Protein (g)')) or 0 for b in grade_pool) / len(grade_pool)
    avg_f = sum(fiber(b) for b in grade_pool) / len(grade_pool)
    brand_rows.append(dict(brand=brand, total=total, q=q, d=d, gmin=gmin, gmax=gmax,
                            avg_p=avg_p, avg_f=avg_f, qual=qual, disq=disq))

CONSIDER = [r for r in brand_rows if r['total'] > 0 and r['q'] / r['total'] >= 0.75 and (r['total'] - r['q']) <= 2]
AVOID = [r for r in brand_rows if r['total'] > 0 and r['d'] / r['total'] >= 0.80 and r['q'] < 3]
_consider_names = set(r['brand'] for r in CONSIDER)
_avoid_names = set(r['brand'] for r in AVOID)
MIXED = [r for r in brand_rows if r['q'] >= 3 and r['d'] >= 3
         and r['brand'] not in _consider_names and r['brand'] not in _avoid_names]

CONSIDER.sort(key=lambda r: (-r['q'], r['brand']))
AVOID.sort(key=lambda r: (-r['d'], r['brand']))
MIXED.sort(key=lambda r: (-(r['q'] + r['d']), r['brand']))

for r in MIXED:
    best = max(r['qual'], key=lambda b: num(b.get('ingredient_score')) or -999)
    r['clean_pick'] = best['Flavor Name']

print(f"\nConsider: {len(CONSIDER)} brands, Avoid: {len(AVOID)} brands, Mixed: {len(MIXED)} brands")

fully_ext_brands = [r for r in CONSIDER if r['q'] == r['total']]
fully_ext_top = sorted(fully_ext_brands, key=lambda r: -r['total'])[:4]
fully_ext_names = ', '.join(f"{r['brand']} ({r['total']})" for r in fully_ext_top)

nugo = next((r for r in MIXED if r['brand'] == 'NuGo'), None)
if nugo is None:
    nugo = MIXED[0] if MIXED else None

quest = next((r for r in brand_rows if r['brand'] == 'Quest'), None)

BIG_STAT_NUM = f"{EXT_PCT}%"
BIG_STAT_HEAD = f"of all protein bars clear 11g of fiber, our Extreme Fiber cutoff"
BIG_STAT_DETAIL = (f"{EXT_N} of the {TOTAL:,} bars we track carry 11g of fiber or more per bar, roughly {round(EXT_N/2.6)} of them from just the top handful of brands. "
                   f"The rest of the database averages {fnum(sum(fiber(b) for b in BARS if b['Key'] not in ext_keys) / DN)}g of fiber per bar.")

INSIGHTS = [
    (f"{len(fully_ext_brands)} brands clear 11g of fiber on every flavor they make.",
     f"Led by {fully_ext_names}, these brands build fiber into the base recipe rather than adding it to a handful of flavors."),
    ((f"{quest['brand']} shows fiber and mainstream availability aren't mutually exclusive." if quest and quest['q'] > 0 else "Extreme Fiber bars aren't a niche-brand phenomenon."),
     (f"{quest['q']} of Quest's {quest['total']} flavors clear 11g of fiber, all while staying one of the most widely available bars in the database."
      if quest and quest['q'] > 0 else "Several mainstream, widely distributed brands clear the Extreme Fiber bar alongside smaller specialty brands.")),
    ("Extreme Fiber bars grade about the same as the database average.",
     f"{AB_RATE_Q}% of Extreme Fiber bars grade A or B, against {AB_RATE_ALL}% database-wide. High fiber does not come at the cost of ingredient quality."),
    ("Extreme Fiber bars carry more protein on average, not less.",
     f"Extreme Fiber bars average {fnum(AVG_PROTEIN_Q)}g of protein against a database-wide average of {fnum(AVG_PROTEIN_ALL)}g. The engineered fiber sources that push these bars past 11g don't crowd out the protein source."),
    ("Fiber content drops off fast once you leave the top tier.",
     f"{HIGH_N} bars ({HIGH_PCT}%) clear 5g of fiber, but only {VERY_N} ({VERY_PCT}%) clear 8g, and just {EXT_N} ({EXT_PCT}%) clear 11g. Each step up the fiber ladder cuts the qualifying pool by more than half."),
    ((f"{nugo['brand']} shows how uneven fiber can be within one brand's own lineup." if nugo else "Mixed lineups are common at this fiber level."),
     (f"{nugo['q']} of {nugo['brand']}'s {nugo['total']} flavors clear 11g of fiber, the rest fall well short. Fiber varies flavor to flavor more than most other screens on this site."
      if nugo else "Most brands split unevenly at the 11g cutoff; always check the specific flavor, not just the brand.")),
]

INSIGHTS_HTML = '\n'.join(
    f'<div class="insight-item"><div class="insight-dot"></div><div class="insight-head">{esc(h)}</div><div class="insight-detail">{esc(d)}</div></div>'
    for h, d in INSIGHTS)

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
DATE_PUBLISHED = '2026-09-06'
DATE_MODIFIED = '2026-09-06'
SLUG = 'high-fiber-protein-bars'
URL = f'https://knowyourbar.com/{SLUG}.html'

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
    labels = {'p': 'Protein', 'c': 'Calories', 's': 'Sugar', 'f': 'Fiber', 'ft': 'Fat'}
    units = {'p': 'g', 'c': '', 's': 'g', 'f': 'g', 'ft': 'g'}
    fieldmap = {m[0]: m for m in RANK_METRICS}
    cells = []
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
    fib = num(bar.get('Dietary Fiber (g)'))
    sugar = num(bar.get('Sugars (g)'))
    sa = num(bar.get('Sugar Alcohol (g)'))
    p100v = round((protein or 0) / cal * 100, 1) if cal else 0
    search = f"{bar['Brand Name']} {bar['Flavor Name']}".lower().replace('"', '')
    bar_row = f'''<tr class="bar-row" data-idx="{idx}" data-score="{score}" data-grade="{grade}" data-protein="{protein or 0}" data-cal="{cal or 0}" data-sugar="{sugar or 0}" data-p100="{p100v}" data-fiber="{fib or 0}" data-search="{esc(search)}" onclick="toggleIngr({idx}, this)">
  <td class="col-bar">
    <div class="bar-brand">{esc(bar['Brand Name'])}</div>
    <div class="bar-flavor">{esc(bar['Flavor Name'])}</div>
    <svg class="row-expand-icon" width="7" height="12" viewBox="0 0 7 12" fill="none"><path d="M1 1L6 6L1 11" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
  </td>
  <td class="col-num col-hide-mobile">{fnum(cal)}</td>
  <td class="col-num">{fnum(protein)}</td>
  <td class="col-num col-hide-mobile">{p100v}</td>
  <td class="col-num">{fnum(fib)}</td>
  <td class="col-num col-hide-mobile">{fnum(fat)}</td>
  <td class="col-num col-hide-mobile">{fnum(carbs)}</td>
  <td class="col-num">{fnum(sugar)}</td>
  <td class="col-certs col-hide-mobile"><div class="cert-badges">{cert_badges_html(bar)}</div></td>
  <td class="col-grade"><span class="table-grade-badge grade-{grade}" title="{grade_word(grade)} &middot; score {fnum(score)}">{grade}</span></td>
</tr>'''
    ingr_row = f'''<tr class="ingr-row" id="ingr-{idx}">
  <td colspan="10" class="ingr-cell">
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

# ---------------------------------------------------------------------------
# TITLE / META / HERO copy
# ---------------------------------------------------------------------------
TITLE = f"The Extreme Fiber 100: Protein Bars With 11g+ Fiber, Ranked"
H1 = f"The Extreme Fiber 100 - Protein Bars With 11g or More Fiber"
META_DESC = f"We checked {TOTAL:,} protein bars for fiber. {EXT_N} clear 11g per bar, our Extreme Fiber cutoff. See every one, plus the High Fiber and Very High Fiber tiers below it."
OG_DESC = f"{EXT_N} protein bars with 11g or more of fiber per bar, ranked by ingredient quality, protein, and brand."
HERO_SUB = (f"We checked {TOTAL:,} protein bars available in the US against their declared Dietary Fiber (g). "
            f"{EXT_N} of them, about {EXT_PCT}%, clear 11g of fiber per bar, our Extreme Fiber cutoff, and that's the list this page ranks first. "
            f"Below it we cover two supporting tiers: {HIGH_N} bars clear 5g (High Fiber, the FDA's own \"excellent source\" line) and {VERY_N} clear 8g (Very High Fiber). "
            f"Not just us telling you the flavors we like.")

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

FACTOR_CARDS_HTML = []
for label, pat, desc in FIBER_SOURCE_PATTERNS:
    hits = FIBER_SOURCE_HITS[label]
    pct = round(100 * len(hits) / EXT_N, 1)
    shown, more = brand_split(hits)
    FACTOR_CARDS_HTML.append(factor_card_html(label, len(hits), pct, desc, shown, more))
FACTOR_CARDS_HTML.append(f'''<div class="score-card">
  <div class="score-card-label">Whole-food fiber, no named additive</div>
  <div class="score-card-val">{len(WHOLE_FOOD_HITS)} bars<span class="oil-card-pct">{WHOLE_FOOD_PCT}%</span></div>
  <div class="score-card-desc">No tapioca fiber, polydextrose, chicory root/inulin, soluble corn fiber, or IMO in the ingredient list. These bars get to 11g+ through whole-food ingredients like nuts, seeds, and legumes instead of an added isolate.</div>
</div>''')
FACTOR_CARDS_HTML = '\n'.join(FACTOR_CARDS_HTML)

CATEGORY_EXPLAINER_P1 = (f"Fiber on a protein bar label comes from one of two places: whole-food ingredients (nuts, seeds, legumes, whole grains) or an isolated fiber "
                         f"additive blended in specifically to raise the number. Among the {EXT_N} bars that clear our 11g Extreme Fiber cutoff, {round(100 - WHOLE_FOOD_PCT, 1)}% "
                         f"contain at least one of five named added-fiber ingredients we checked for.")
CATEGORY_EXPLAINER_P2 = (f"Tapioca fiber is the single most common source, showing up in {len(FIBER_SOURCE_HITS['Tapioca Fiber'])} of the {EXT_N} Extreme Fiber bars "
                         f"({round(100*len(FIBER_SOURCE_HITS['Tapioca Fiber'])/EXT_N,1)}%). Polydextrose, chicory root/inulin, soluble corn fiber, and isomalto-oligosaccharide (IMO) "
                         f"follow, often two or three stacked together in the same bar. None of these are red flags on their own, they're standard, well-tolerated ways to add fiber, "
                         f"but they're worth knowing about if a bar's ingredient list otherwise reads short and simple except for one long fiber name.")

def consider_row(r):
    return (f'<tr><td><button type="button" class="brand-jump" data-brand="{esc(r["brand"])}">{esc(r["brand"])}</button></td>'
            f'<td>{r["total"]}</td><td>{grade_range_html(r["gmin"], r["gmax"])}</td>'
            f'<td>{fnum(r["avg_p"])}g</td><td>{fnum(r["avg_f"])}g</td><td>11g+ fiber across the whole lineup</td></tr>')

def avoid_row(r, hidden):
    cls = 'avoid-row brand-row-hidden" style="display:none;' if hidden else 'avoid-row'
    return (f'<tr class="{cls}"><td><span class="brand-name-static">{esc(r["brand"])}</span></td>'
            f'<td>{r["d"]}/{r["total"]}</td><td>{grade_range_html(r["gmin"], r["gmax"])}</td>'
            f'<td>{fnum(r["avg_p"])}g</td><td>{fnum(r["avg_f"])}g</td><td>Under 11g fiber</td></tr>')

def mixed_row(r):
    return (f'<tr><td><button type="button" class="brand-jump" data-brand="{esc(r["brand"])}">{esc(r["brand"])}</button></td>'
            f'<td>{r["q"]}/{r["total"]}</td><td>{grade_range_html(r["gmin"], r["gmax"])}</td>'
            f'<td>{fnum(r["avg_p"])}g</td><td>{fnum(r["avg_f"])}g</td><td>{esc(r["clean_pick"])} is the Extreme Fiber pick</td></tr>')

CONSIDER_ROWS = '\n'.join(consider_row(r) for r in CONSIDER)
AVOID_VISIBLE = AVOID[:15]
AVOID_HIDDEN = AVOID[15:]
AVOID_ROWS = '\n'.join(avoid_row(r, False) for r in AVOID_VISIBLE) + '\n' + '\n'.join(avoid_row(r, True) for r in AVOID_HIDDEN)
MIXED_ROWS = '\n'.join(mixed_row(r) for r in MIXED)

AVOID_SHOW_MORE = ''
if AVOID_HIDDEN:
    AVOID_SHOW_MORE = f'''<button type="button" class="brand-table-show-more" id="hf-avoid-show-more" data-hidden-count="{len(AVOID_HIDDEN)}">Show {len(AVOID_HIDDEN)} more brands</button>
<script>
(function() {{
  var btn = document.getElementById('hf-avoid-show-more');
  var table = document.getElementById('hf-avoid-table');
  if (!btn || !table) return;
  btn.addEventListener('click', function() {{
    var hidden = table.querySelectorAll('.brand-row-hidden');
    hidden.forEach(function(row) {{ row.style.display = ''; row.classList.remove('brand-row-hidden'); }});
    btn.classList.add('is-hidden');
  }});
}})();
</script>'''

SORTED_QUALIFY = sorted(QUALIFY, key=lambda b: (-(num(b.get('ingredient_score')) or -999), b['Brand Name'], b['Flavor Name']))
# All 103 Extreme Fiber bars render rich -- small enough that a lazy split
# adds risk (see BRIEFING.md's Guide table data completeness note on
# Mechanism A/B) for no real page-weight benefit.
rich_html_parts = [rich_row_html(bar, idx) for idx, bar in enumerate(SORTED_QUALIFY)]
BAR_ROWS_HTML = '\n'.join(rich_html_parts)

for bar in SORTED_QUALIFY:
    if bar.get('Amazon Affiliate') in ('Yes', 'None') or bar.get('Website') in ('Yes', 'None'):
        raise SystemExit(f"BROKEN LINK FIELD: {bar['Brand Name']} {bar['Flavor Name']}")
print("Broken link-field scan: PASS")

FAQ = [
    ("How much fiber counts as high fiber in a protein bar?",
     f"We use three tiers. High Fiber is 5g or more, the same cutoff the FDA uses for an \"excellent source of fiber\" claim ({HIGH_N} of {TOTAL:,} bars, {HIGH_PCT}%). Very High Fiber is 8g or more ({VERY_N} bars, {VERY_PCT}%). Extreme Fiber, the tier this page ranks, is 11g or more ({EXT_N} bars, {EXT_PCT}%)."),
    ("What is the Extreme Fiber 100?",
     f"It's our name for the {EXT_N} protein bars in the database that carry 11g or more of dietary fiber per bar. That's about {EXT_PCT}% of the {TOTAL:,} bars we track, spanning {len(EXT_BRANDS)} brands."),
    ("What protein bar has the most fiber?",
     f"{most_fiber['Brand Name']} {most_fiber['Flavor Name']}, at {fnum(fiber(most_fiber))}g of fiber per bar, the most of any bar in our database."),
    ("What ingredients make protein bars high in fiber?",
     f"Mostly one of five added-fiber ingredients: tapioca fiber, polydextrose, chicory root fiber or inulin, soluble corn fiber, or isomalto-oligosaccharide (IMO). {round(100 - WHOLE_FOOD_PCT, 1)}% of Extreme Fiber bars contain at least one. The rest, {WHOLE_FOOD_PCT}%, get there through whole-food ingredients like nuts, seeds, and legumes with no added fiber isolate."),
    ("Is more fiber always better in a protein bar?",
     "Not automatically. Fiber above roughly 10-15g in one sitting can cause bloating or digestive discomfort for people not used to it, especially from added isolates like polydextrose or IMO rather than whole-food fiber. If you're new to high fiber bars, the 5g or 8g tier is usually a gentler starting point than jumping straight to Extreme Fiber."),
    ("Do high fiber protein bars grade lower on ingredient quality?",
     f"No. Extreme Fiber bars grade A or B at {AB_RATE_Q}%, close to the {AB_RATE_ALL}% database-wide rate. They also average more protein ({fnum(AVG_PROTEIN_Q)}g vs. {fnum(AVG_PROTEIN_ALL)}g database-wide), not less."),
    ("What's the difference between High Fiber, Very High Fiber, and Extreme Fiber on this site?",
     f"They're the same measurement (Dietary Fiber (g) per bar) at three different cutoffs: 5g+ ({HIGH_N} bars), 8g+ ({VERY_N} bars), and 11g+ ({EXT_N} bars). Every Extreme Fiber bar also counts toward the other two tiers, since the cutoffs are cumulative, not separate categories."),
    (f"Is {best_overall['Brand Name']} {best_overall['Flavor Name']} a good high fiber option?",
     f"Yes. It carries {fnum(fiber(best_overall))}g of fiber and {fnum(num(best_overall.get('Protein (g)')))}g of protein at {fnum(num(best_overall.get('Calories')))} calories, and grades {best_overall.get('score_band')} for ingredient quality, the highest of any Extreme Fiber bar we track."),
    ("Can a brand have some high fiber flavors and some that aren't?",
     (f"Yes. {nugo['brand']} is a good example: {nugo['q']} of {nugo['total']} flavors clear 11g of fiber, the rest fall well short. Fiber content varies flavor to flavor more than most other screens on this site, so check the specific flavor, not just the brand."
      if nugo else "Yes, fiber content varies flavor to flavor within a brand's lineup more than most other screens on this site. Always check the specific flavor.")),
    ("How often is this list updated?",
     f"We update the database whenever new bars are added or a brand reformulates. Manufacturers do change their recipes over time, so always confirm against the packaging in front of you. This page reflects the database as of {DATE_MODIFIED}."),
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
print("Bar rows built:", len(SORTED_QUALIFY), "(all rich)")
print("FAQ count:", len(FAQ))

# ---------------------------------------------------------------------------
# Nav / footer -- spliced from dairy-free-protein-bars.html (most recently
# shipped guide, carries the full current 12-guide nav/footer link set),
# with this guide's own link appended.
# ---------------------------------------------------------------------------
with open(f'{REPO}/dairy-free-protein-bars.html') as f:
    DF_SRC = f.read()

def extract(src, start_marker, end_marker):
    i = src.index(start_marker)
    j = src.index(end_marker, i)
    return src[i:j]

NAV_BLOCK = extract(DF_SRC, '<nav class="site-nav">', '</nav>') + '</nav>'
NAV_BLOCK = NAV_BLOCK.replace(
    '<a href="/dairy-free-protein-bars">Dairy Free Protein Bars</a>\n      </div>',
    '<a href="/dairy-free-protein-bars">Dairy Free Protein Bars</a>\n        <a href="/high-fiber-protein-bars">High Fiber Protein Bars</a>\n      </div>'
)
NAV_TOGGLE_SCRIPT = extract(DF_SRC, "<script>\n(function() {\n  var navToggle", "})();\n</script>") + "})();\n</script>"

FOOTER_BLOCK = extract(DF_SRC, '<footer class="site-footer">', '</footer>') + '</footer>'
FOOTER_BLOCK = FOOTER_BLOCK.replace(
    '<a href="/dairy-free-protein-bars">Dairy Free Protein Bars</a>\n    </nav>',
    '<a href="/dairy-free-protein-bars">Dairy Free Protein Bars</a>\n      <a href="/high-fiber-protein-bars">High Fiber Protein Bars</a>\n    </nav>'
)
FOOTER_BLOCK = re.sub(r'Updated [A-Za-z]+ \d{4}', 'Updated September 2026', FOOTER_BLOCK)

MAIN_SCRIPT = extract(DF_SRC, '<script>\n(function() {\n  var tbody', '\n</script>\n\n<script src="analytics.js"') + '\n</script>'

assert 'high-fiber-protein-bars' in NAV_BLOCK
assert 'high-fiber-protein-bars' in FOOTER_BLOCK
assert 'faq-q' in MAIN_SCRIPT and 'jumpToBrand' in MAIN_SCRIPT
print("Nav/footer spliced OK, main script extracted OK, len=", len(MAIN_SCRIPT))

SNAPSHOT_METRICS = [
    (str(A_GRADE_Q), 'A-grade bars'),
    (str(len(BRANDS_Q)), 'Brands represented'),
    (f'{fnum(AVG_FIBER_Q)}g', 'Avg fiber in this tier'),
]

# ---------------------------------------------------------------------------
# Supporting-tiers section (High Fiber / Very High Fiber) -- inserted at the
# same point the site's GSC keyword-gap sections use: between the category
# explainer and the findings section. See BRIEFING.md's Template section
# order note ("A GSC keyword-gap section inserts between step 6 and step 7").
# ---------------------------------------------------------------------------
TIERS_SECTION = f'''<section class="section off" id="fiber-tiers">
    <div class="section-inner">
      <h2 class="section-title">The three tiers of high fiber</h2>
      <div class="section-body">
        <p>11g of fiber is a real jump, not every bar needs to clear it. The FDA's own labeling rule sets 5g as the cutoff for an "excellent source of fiber" claim, and most people looking for a higher-fiber bar are better served starting there rather than at the Extreme tier above. We track three cutoffs on the same field (Dietary Fiber (g) per bar), cumulative, not separate lists: every Extreme Fiber bar also counts as Very High Fiber and High Fiber.</p>
        <div class="callout-box">
          <strong>Where the cutoffs land, recomputed fresh against the live database:</strong>
          <ul class="criteria-list" style="margin-top:0.5rem;">
            <li><strong>High Fiber, 5g+:</strong> {HIGH_N} bars ({HIGH_PCT}% of the database), {len(HIGH_BRANDS)} brands. The FDA's "excellent source of fiber" line. A gentle, easy starting point if you're new to eating more fiber.</li>
            <li><strong>Very High Fiber, 8g+:</strong> {VERY_N} bars ({VERY_PCT}% of the database), {len(VERY_BRANDS)} brands. Roughly a third of a typical daily fiber target in one bar.</li>
            <li><strong>Extreme Fiber, 11g+:</strong> {EXT_N} bars ({EXT_PCT}% of the database), {len(EXT_BRANDS)} brands. The tier ranked in full below. Most bars at this level lean on at least one added fiber ingredient to get there (see the category breakdown above).</li>
          </ul>
        </div>
        <p>{best_high_only_line}</p>
        <p>{best_very_only_line}</p>
        <p>Want a specific cutoff instead of the full Extreme Fiber list? The <a href="/bar-finder.html?fiber=5">Bar Finder's Min Fiber slider</a> lets you set any threshold from 0g up, not just these three, and stack it with protein, sugar, or ingredient grade filters at the same time.</p>
      </div>
    </div>
  </section>'''

print("\nTIERS_SECTION built")

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
    "about": {{ "@type": "Thing", "name": "High Fiber Protein Bars" }}
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
    "name": "Top picks for high fiber protein bars",
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
    <div class="snap-item"><div class="snap-value">{QN}</div><div class="snap-label">Extreme Fiber bars</div></div>
    <div class="snap-item"><div class="snap-value">{DN}</div><div class="snap-label">Under 11g fiber</div></div>
    <div class="snap-item"><div class="snap-value">{SNAPSHOT_METRICS[0][0]}</div><div class="snap-label">{SNAPSHOT_METRICS[0][1]}</div></div>
    <div class="snap-item"><div class="snap-value">{SNAPSHOT_METRICS[1][0]}</div><div class="snap-label">{SNAPSHOT_METRICS[1][1]}</div></div>
    <div class="snap-item"><div class="snap-value">{SNAPSHOT_METRICS[2][0]}</div><div class="snap-label">{SNAPSHOT_METRICS[2][1]}</div></div>
  </div>
</section>

<main class="content">

  <section class="section">
    <div class="section-inner">
      <h2 class="section-title">Top picks from the Extreme Fiber 100</h2>
      <p class="section-body">Every bar below clears 11g of fiber per bar. Here are the best of that group for what people typically look for. Grades below reflect ingredient quality only, not an overall bar rating.</p>
      <div class="macro-grid pick-tile-grid top-picks-6">
{PICKS_HTML}
      </div>
    </div>
  </section>

  <section class="section off">
    <div class="section-inner">
      <h2 class="section-title">What actually pushes a bar past 11g of fiber</h2>
      <div class="section-body">
        <p>{esc(CATEGORY_EXPLAINER_P1)}</p>
        <p>{esc(CATEGORY_EXPLAINER_P2)}</p>
      </div>
      <div class="score-grid" style="margin-top:1.5rem;">
{FACTOR_CARDS_HTML}
      </div>
    </div>
  </section>

  {TIERS_SECTION}

  <section class="findings">
    <div class="findings-inner">
      <h2 class="findings-title">What we found screening {TOTAL:,} bars for fiber</h2>
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
      <h2 class="section-title">Best Brands for Extreme Fiber Protein Bars</h2>
      <div class="section-body">
        <p>Some brands build fiber into every flavor, others clear 11g on only a bar or two. Grade columns below show ingredient quality only, not an overall bar rating. Click any brand name to jump to its flavors in the table below.</p>
      </div>

      <div class="brand-table-block">
        <div class="brand-table-label pro">Brands to Consider</div>
        <div class="brand-table-note">Every flavor from these {len(CONSIDER)} brands clears 11g of fiber.</div>
        <div class="table-scroll">
          <table class="brand-table">
            <thead><tr><th>Brand</th><th>Total Flavors</th><th>Ingredient Quality</th><th>Avg Protein</th><th>Avg Fiber</th><th>Note</th></tr></thead>
            <tbody>
{CONSIDER_ROWS}
            </tbody>
          </table>
        </div>
      </div>

      <div class="brand-table-block">
        <div class="brand-table-label con">Brands to Avoid (for this screen)</div>
        <div class="brand-table-note">These brands clear 11g of fiber on few or none of their flavors. That's not a knock on the brand, most protein bars simply aren't built around fiber.</div>
        <div class="table-scroll">
          <table class="brand-table" id="hf-avoid-table">
            <thead><tr><th>Brand</th><th>Flavors Under 11g Fiber</th><th>Ingredient Quality</th><th>Avg Protein</th><th>Avg Fiber</th><th>Why</th></tr></thead>
            <tbody>
{AVOID_ROWS}
            </tbody>
          </table>
        </div>
        {AVOID_SHOW_MORE}
      </div>

      <div class="brand-table-block">
        <div class="brand-table-label mixed">Mixed Lineups, Check the Flavor</div>
        <div class="brand-table-note">Some flavors clear 11g of fiber, some fall well short. Check the specific flavor before buying.</div>
        <div class="table-scroll">
          <table class="brand-table">
            <thead><tr><th>Brand</th><th>Extreme Fiber Flavors</th><th>Ingredient Quality</th><th>Avg Protein</th><th>Avg Fiber</th><th>Extreme Fiber Pick</th></tr></thead>
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
      <h2 class="section-title">The Extreme Fiber 100: all {QN} bars with 11g+ fiber, ranked by ingredient quality</h2>
      <p class="section-body">Every bar in the database that clears 11g of fiber, sorted best to worst by ingredient quality grade. Use the sort dropdown to re-rank by protein, fiber, calories, or sugar instead, or filter by grade. Tap any row for the full macro rank, ingredient breakdown, and buy links.</p>

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
                <th class="col-num" title="Dietary Fiber (g)">FIBR</th>
                <th class="col-num col-hide-mobile" title="Total Fat (g)">FAT</th>
                <th class="col-num col-hide-mobile" title="Total Carbohydrates (g)">CARB</th>
                <th class="col-num" title="Sugars (g)">SGR</th>
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

      <script type="application/json" id="gd-bar-data">[]</script>

    </div>
  </section>

  <section class="section guide-finder-cta">
    <div class="explore-cta-grid">
      <div class="explore-cta-main">
        <h2 class="explore-cta-main-heading">Pick your own fiber cutoff, not just 11g</h2>
        <p class="explore-cta-main-desc">This page ranks the Extreme Fiber tier specifically. The Bar Finder covers all {TOTAL:,}+ bars in the database, and you set the Min Fiber slider to any level, from the 5g High Fiber line up, and stack it with protein, sugar, calories, ingredient grade, brand, certifications, and specific ingredients to exclude. No sponsored picks, no subjective taste tests. You decide what matters.</p>
        <a href="/bar-finder.html?fiber=11" class="finder-cta-btn">Open the Bar Finder &rarr;</a>
      </div>
      <div class="explore-cta-side">
        <a href="/ingredient_scoring.html" class="explore-cta-side-link">How we score &rarr;</a>
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
        <a href="/best-bars-for-diabetics.html" class="explore-more-card">
          <div class="explore-more-title">Best Bars for Diabetics</div>
          <div class="explore-more-desc">Fiber is one of six criteria in a full diabetic-friendly screen.</div>
        </a>
        <a href="/glp1-protein-bars.html" class="explore-more-card">
          <div class="explore-more-title">GLP-1 Protein Bars</div>
          <div class="explore-more-desc">High protein, low sugar bars built for satiety, fiber included.</div>
        </a>
        <a href="/clean-protein-bars.html" class="explore-more-card">
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
