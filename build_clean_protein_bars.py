#!/usr/bin/env python3
"""
Rebuild the data on clean-protein-bars.html from live bars.js.

    python3 build_clean_protein_bars.py

Filter (GUIDE_CRITERIA.md): score_band in (A, B) AND no `Artificial
Sweeteners` tag AND no `Processed Oils` tag.

How it works: opens the live page and rewrites only the regions between
<!-- kyb:NAME --> ... <!-- /kyb:NAME --> markers (see kyb_guide_lib.py).
Nav, footer, fonts, canonical URL, static copy and inline JS are never
touched. Every number, grade, bar name and list inside a region is computed
here from bars.js. Ends with the grade-sync QA check and exits non-zero on
any mismatch.

Top picks (GUIDE_CRITERIA.md "Top Picks Selection"): all six come from the
best grade band present in the qualifying set, never ranked by raw
ingredient score, no bar repeats. Every pick also needs 10g+ protein (this is
a protein bar guide); a tile falls back to the whole band only if nothing
clears that floor.
"""
import json, re, sys
from kyb_guide_lib import *

PAGE = 'clean-protein-bars.html'
SLUG = 'clean-protein-bars'
URL = f'https://knowyourbar.com/{SLUG}'
PICK_PROTEIN_FLOOR = 10

BARS = load_bars()
TOTAL = len(BARS)
qualifies = GUIDE_FILTERS[SLUG]
Q = [b for b in BARS if qualifies(b)]
D = [b for b in BARS if not qualifies(b)]
QN, DN = len(Q), len(D)
ALL_BRANDS = sorted({b['Brand Name'] for b in BARS})
Q_BRANDS = sorted({b['Brand Name'] for b in Q})

# ---------------------------------------------------------------------------
# Screen stats
# ---------------------------------------------------------------------------
def low_grade(b): return b.get('score_band') in ('C', 'D', 'F')
def art_sw(b): return has_tag(b, 'Artificial Sweeteners')
def proc_oil(b): return has_tag(b, 'Processed Oils')
def fails(b): return (low_grade(b), art_sw(b), proc_oil(b))

LOW = [b for b in BARS if low_grade(b)]
AS = [b for b in BARS if art_sw(b)]
PO = [b for b in BARS if proc_oil(b)]
MULTI = sum(1 for b in D if sum(fails(b)) > 1)
ONLY_GRADE = sum(1 for b in D if fails(b) == (True, False, False))
ONLY_OIL = sum(1 for b in D if fails(b) == (False, False, True))
ONLY_AS = sum(1 for b in D if fails(b) == (False, True, False))
PCT_FAIL = pct(DN, TOTAL)
PCT_PASS = pct(QN, TOTAL)
A_IN_Q = sum(1 for b in Q if b.get('score_band') == 'A')
AVG_P_Q = avg(Q, 'Protein (g)')
AVG_P_D = avg(D, 'Protein (g)')

# ---------------------------------------------------------------------------
# Top picks
# ---------------------------------------------------------------------------
BEST_BAND = next(g for g in BAND_ORDER if any(b.get('score_band') == g for b in Q))
BAND = [b for b in Q if b.get('score_band') == BEST_BAND]
_used = set()

def P(b): return num(b.get('Protein (g)')) or 0
def S(b): return num(b.get('Sugars (g)')) if num(b.get('Sugars (g)')) is not None else 99
def F(b): return num(b.get('Dietary Fiber (g)')) or 0
def CAL(b): return num(b.get('Calories')) or 9999
def N(b): return top_level_ingredient_count(ingr(b))
def name_key(b): return (b['Brand Name'].lower(), b['Flavor Name'].lower())

def pick(sort_key, eligible=lambda b: True):
    """Best unused bar in BAND by sort_key (ascending), 10g+ protein first."""
    for floor in (PICK_PROTEIN_FLOOR, 0):
        c = [b for b in BAND if b['Key'] not in _used and eligible(b) and P(b) >= floor]
        if c:
            b = min(c, key=lambda x: (sort_key(x), name_key(x)))
            _used.add(b['Key'])
            return b
    raise SystemExit('ERROR: no bar available for a top-pick tile')

# 1. Best overall: hits 15g+ protein, 5g+ fiber, 5g or less sugar; among those,
#    the best combined rank on the three (balanced, not extreme on one).
def balanced(b): return P(b) >= 15 and F(b) >= 5 and S(b) <= 5
BAL = [b for b in BAND if balanced(b)]
def _rank(vals, v, higher_better):
    return 1 + sum(1 for x in vals if (x > v if higher_better else x < v))
def balance_score(b):
    return (_rank([P(x) for x in BAL], P(b), True) + _rank([F(x) for x in BAL], F(b), True)
            + _rank([S(x) for x in BAL], S(b), False))
best_overall = pick(lambda b: (balance_score(b), -P(b)), balanced) if BAL else pick(lambda b: (S(b), -P(b)))
# 2. Highest protein (tie: fewer calories)
top_protein = pick(lambda b: (-P(b), CAL(b)))
# 3. Best protein per calorie (tie: more protein)
top_p100 = pick(lambda b: (-(p100(b) or 0), -P(b)))
# 4. Lowest sugar (tie: more protein)
low_sugar = pick(lambda b: (S(b), -P(b)))
# 5. Most fiber (tie: more protein)
top_fiber = pick(lambda b: (-F(b), -P(b)))
# 6. No added oil, no added sweetener (tie: fewest ingredients, more protein)
SWEETENER_WORDS = re.compile(
    r'sugar|syrup|honey|nectar|agave|molasses|maple|stevia|monk ?fruit|luo han|allulose|erythritol|'
    r'xylitol|sorbitol|maltitol|isomalt|sucralose|acesulfame|aspartame|saccharin|dextrose|dextrin|'
    r'sweeten|juice|cane|fructose|glucose|tagatose|inulin|chicory|oligo', re.I)
def no_oil_no_sweetener(b):
    t = ingr(b).lower()
    return 'oil' not in t and not SWEETENER_WORDS.search(t)
NOOIL_COUNT = sum(1 for b in Q if no_oil_no_sweetener(b))
plain = pick(lambda b: (N(b), -P(b)), no_oil_no_sweetener)

PICKS = [
    ['Best overall', best_overall,
     f"{fnum(P(best_overall))}g protein, {fnum(F(best_overall))}g fiber, and just {fnum(S(best_overall))}g sugar, "
     f"all on {'an' if BEST_BAND == 'A' else 'a'} {BEST_BAND} grade with no artificial sweeteners or processed oils. "
     "Balanced rather than an extreme on one metric."],
    ['Highest protein', top_protein,
     f"{fnum(P(top_protein))}g protein, the most of any bar that clears the clean screen."],
    ['Best protein per calorie', top_p100,
     f"{fnum(P(top_p100))}g protein at just {fnum(CAL(top_p100))} calories, {fnum(p100(top_p100))}g protein per 100 calories, "
     "the best ratio of any bar that clears the clean screen."],
    ['Lowest sugar', low_sugar, None],
    ['Most fiber', top_fiber,
     f"{fnum(F(top_fiber))}g of fiber, the most of any {BEST_BAND}-grade bar with {PICK_PROTEIN_FLOOR}g+ protein that clears the clean screen, "
     f"alongside {fnum(P(top_fiber))}g of protein."],
    ['No added oil, no added sweetener', plain,
     f"{ingr(plain).rstrip('.')[:1].upper() + ingr(plain).rstrip('.')[1:]}. That's the whole label: {N(plain)} ingredients, no oil of any kind, "
     "and no sweetener beyond whole fruit."],
]
_min_sugar = min(S(b) for b in BAND if P(b) >= PICK_PROTEIN_FLOOR)
_tied = sum(1 for b in BAND if P(b) >= PICK_PROTEIN_FLOOR and S(b) == _min_sugar)
PICKS[3][2] = (f"{fnum(S(low_sugar))}g of sugar, {'tied for ' if _tied > 1 else ''}the lowest of any "
               f"{BEST_BAND}-grade bar with {PICK_PROTEIN_FLOOR}g+ protein that clears the clean screen, "
               f"alongside {fnum(P(low_sugar))}g of protein.")
# One computed tradeoff per tile, at most: highest sugar of the six (if over
# 5g), otherwise a long label (15+ ingredients).
_max_s = max(S(p[1]) for p in PICKS)
for p in PICKS:
    b = p[1]
    if S(b) == _max_s and S(b) > 5:
        p[2] += f" The tradeoff is sugar: {fnum(S(b))}g, the highest of these six picks"
        p[2] += ", all from whole fruit." if p[0].startswith('No added') else "."
    elif N(b) >= 15 and not p[0].startswith('No added'):
        p[2] += f" The tradeoff is a long label: {N(b)} ingredients."

def pick_tile(label, b, reason):
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

# ---------------------------------------------------------------------------
# Brand tables
# ---------------------------------------------------------------------------
CONSIDER, MIXED, AVOID = brand_split(BARS, qualifies)

def fail_note(disq):
    reasons = [('processed oils', sum(1 for b in disq if proc_oil(b))),
               ('artificial sweeteners', sum(1 for b in disq if art_sw(b))),
               ('grade C or below', sum(1 for b in disq if low_grade(b)))]
    reasons.sort(key=lambda r: -r[1])
    main = [r[0] for r in reasons if r[1] >= len(disq) / 2] or [reasons[0][0]]
    txt = ', '.join(main[:-1]) + (' and ' if len(main) > 1 else '') + main[-1]
    return txt[0].upper() + txt[1:]

def clean_pick(r):
    band = next(g for g in BAND_ORDER if any(b.get('score_band') == g for b in r['qual']))
    return min((b for b in r['qual'] if b.get('score_band') == band), key=lambda b: (-P(b), name_key(b)))

def brand_cells(r):
    best, worst = grade_range(r['bars'])
    return (f'<td>{r["q"]}/{r["total"]}</td><td>{grade_range_html(best, worst)}</td>'
            f'<td>{fnum(avg(r["bars"], "Protein (g)"))}g</td><td>{fnum(avg(r["bars"], "Sugars (g)"))}g</td>')

def jump(brand):
    return f'<button type="button" class="brand-jump" data-brand="{esc(brand)}">{esc(brand)}</button>'

consider_rows = '\n'.join(
    f'<tr><td>{jump(r["brand"])}</td>{brand_cells(r)}<td>'
    + ('Clean across its whole lineup' if r['d'] == 0 else f'{r["q"]} of {r["total"]} flavors clear the screen')
    + '</td></tr>' for r in CONSIDER)
avoid_rows = '\n'.join(
    (f'<tr class="avoid-row brand-row-hidden" style="display:none;">' if i >= 15 else '<tr class="avoid-row">')
    + f'<td><span class="brand-name-static">{esc(r["brand"])}</span></td>{brand_cells(r)}<td>{esc(fail_note(r["disq"]))}</td></tr>'
    for i, r in enumerate(AVOID))
mixed_rows = '\n'.join(
    f'<tr><td>{jump(r["brand"])}</td>{brand_cells(r)}<td>{esc(clean_pick(r)["Flavor Name"])} is the clean pick</td></tr>'
    for r in MIXED)
hidden_avoid = max(0, len(AVOID) - 15)
avoid_more = '' if not hidden_avoid else f'''
        <button type="button" class="brand-table-show-more" id="clean-avoid-show-more">Show {hidden_avoid} more brands</button>
        <script>
        (function() {{
          var btn = document.getElementById('clean-avoid-show-more');
          var table = document.getElementById('clean-avoid-table');
          if (!btn || !table) return;
          btn.addEventListener('click', function() {{
            table.querySelectorAll('.brand-row-hidden').forEach(function(row) {{ row.style.display = ''; row.classList.remove('brand-row-hidden'); }});
            btn.classList.add('is-hidden');
          }});
        }})();
        </script>'''
HEAD = '<thead><tr><th>Brand</th><th>Clean / Total</th><th>Ingredient Quality</th><th>Avg Protein</th><th>Avg Sugar</th><th>{}</th></tr></thead>'
BRAND_TABLES = f'''      <div class="brand-table-block">
        <div class="brand-table-label pro">Brands to Consider</div>
        <div class="brand-table-note">Every flavor from these brands clears the full clean screen, or all but one or two do: A or B grade, no artificial sweeteners, no processed oils.</div>
        <div class="table-scroll">
          <table class="brand-table">
            {HEAD.format('Note')}
            <tbody>
{consider_rows}
</tbody>
          </table>
        </div>
      </div>

      <div class="brand-table-block">
        <div class="brand-table-label con">Brands to Avoid</div>
        <div class="brand-table-note">At least 80% of these brands' flavors fail the clean screen, and no more than two pass. The last column shows what disqualifies most of their lineup.</div>
        <div class="table-scroll">
          <table class="brand-table" id="clean-avoid-table">
            {HEAD.format('Main Issue')}
            <tbody>
{avoid_rows}
</tbody>
          </table>
        </div>{avoid_more}
      </div>

      <div class="brand-table-block">
        <div class="brand-table-label mixed">Mixed Lineups, Check the Flavor</div>
        <div class="brand-table-note">At least three flavors pass and at least three fail. Check the specific flavor before buying.</div>
        <div class="table-scroll">
          <table class="brand-table">
            {HEAD.format('Clean Pick')}
            <tbody>
{mixed_rows}
</tbody>
          </table>
        </div>
      </div>'''

# ---------------------------------------------------------------------------
# Findings facts (each sentence is only written if the data supports it)
# ---------------------------------------------------------------------------
def brand_bars(name): return [b for b in BARS if b['Brand Name'] == name]

def names_and(xs):
    return xs[0] if len(xs) == 1 else ', '.join(xs[:-1]) + (',' if len(xs) > 2 else '') + ' and ' + xs[-1]

# Whole-food leaders: 8+ flavors, 90%+ qualify, most clean flavors tagged Whole Food Forward
WHOLE_FOOD = [r for r in CONSIDER + MIXED if r['total'] >= 8 and r['q'] / r['total'] >= 0.9
              and sum(1 for b in r['qual'] if has_tag(b, 'Whole Food Forward')) >= r['q'] / 2]
WHOLE_FOOD.sort(key=lambda r: (-r['total'], r['brand'].lower()))
WF_NAMES = [r['brand'] for r in WHOLE_FOOD[:6]]

# Big mainstream brands with zero clean flavors
def big_brand_fact():
    names = [n for n in ('Barebells', 'Quest') if brand_bars(n)]
    bb = [b for n in names for b in brand_bars(n)]
    if not names or any(qualifies(b) for b in bb):
        return None
    tot = len(bb)
    n_as, n_po, n_low = sum(map(art_sw, bb)), sum(map(proc_oil, bb)), sum(map(low_grade, bb))
    parts = []
    if n_as == tot:
        parts.append('every flavor from both brands contains an artificial sweetener')
    if n_po:
        parts.append(f'{n_po} of {tot} also contain a processed oil')
    if n_low:
        parts.append(f'{n_low} of {tot} score C or below')
    counts = ' or '.join(f"{len(brand_bars(n))} {n} flavors" for n in names)
    detail = f"None of the {counts} clear the clean screen. " + (names_and(parts)[0].upper() + names_and(parts)[1:] + '.' if parts else '')
    return f"{' and '.join(names)} fail completely.", detail

BIG = big_brand_fact()
MIX_EX = sorted(MIXED, key=lambda r: (-r['total'], r['brand'].lower()))[:2]
def mix_sentence():
    a, b = MIX_EX
    return (f"{a['brand']} qualifies at {round(100 * a['q'] / a['total'])}% ({a['q']} of {a['total']} flavors), "
            f"{b['brand']} at {round(100 * b['q'] / b['total'])}% ({b['q']} of {b['total']}).")

if len(PO) > len(LOW):
    oil_head = 'Processed oils disqualify more bars than low grades do.'
    oil_rel = f'ahead of the {len(LOW)} bars ({pct(len(LOW), TOTAL)}%) that score a C grade or below'
elif len(LOW) - len(PO) <= 0.1 * len(LOW):
    oil_head = 'Processed oils disqualify almost as many bars as low grades.'
    oil_rel = f'close behind the {len(LOW)} bars ({pct(len(LOW), TOTAL)}%) that score a C grade or below'
else:
    oil_head = 'Low grades disqualify the most bars.'
    oil_rel = f'behind the {len(LOW)} bars ({pct(len(LOW), TOTAL)}%) that score a C grade or below'
oil_tail = (' Between the two, ingredient-list quality problems outnumber sweetener problems by a wide margin.'
            if min(len(PO), len(LOW)) > 1.5 * len(AS) else '')

INSIGHTS = [
    (oil_head, f'{len(PO)} bars ({pct(len(PO), TOTAL)}%) contain a processed oil, {oil_rel}.{oil_tail}'),
    ('Most disqualified bars fail more than one screen.' if MULTI > DN / 2 else 'Most disqualified bars fail just one screen.',
     f'{MULTI} of the {DN} disqualified bars fail two or all three criteria at once. '
     f'Only {ONLY_GRADE} fail on grade alone, {ONLY_OIL} on processed oils alone, and {ONLY_AS} on artificial sweeteners alone.'),
]
if BIG:
    INSIGHTS.append(BIG)
if len(WF_NAMES) >= 3:
    INSIGHTS.append(('Whole-food brands dominate the qualifying pool.',
                     f'{names_and(WF_NAMES)} all qualify at or near 100%, and most of their clean flavors carry our '
                     'Whole Food Forward tag: built around whole foods instead of processed protein blends.'))
if len(MIX_EX) == 2:
    INSIGHTS.append(('A mixed lineup is common.',
                     mix_sentence() + ' Even well-known brands rarely clear the bar across their entire lineup.'))
if AVG_P_D > AVG_P_Q:
    INSIGHTS.append(('Disqualified bars average more protein than qualifying ones.',
                     f'Bars that fail the clean screen average {fnum(AVG_P_D)}g protein versus {fnum(AVG_P_Q)}g for bars that pass, '
                     'a reminder that higher protein numbers often come from processed protein blends and synthetic sweeteners doing the work.'))
else:
    INSIGHTS.append(('Clean bars hold their own on protein.',
                     f'Bars that pass the clean screen average {fnum(AVG_P_Q)}g protein versus {fnum(AVG_P_D)}g for bars that fail.'))
INSIGHTS.append((f'{len(Q_BRANDS)} of {len(ALL_BRANDS)} brands still clear at least one flavor.',
                 f'Even with {PCT_FAIL}% of the database disqualified, '
                 + ('more than half' if len(Q_BRANDS) > len(ALL_BRANDS) / 2 else 'a real share')
                 + ' of the brands we track have at least one bar that passes all three clean criteria.'))

FINDINGS = f'''<h2 class="findings-title">What we found screening {TOTAL} bars for clean criteria</h2>
      <div class="big-stat">
        <div class="big-stat-num">{PCT_FAIL}%</div>
        <div>
          <div class="big-stat-head">of bars fail at least one clean criterion</div>
          <div class="big-stat-detail">{DN} of {TOTAL} bars fail the ingredient grade, the artificial sweetener screen, the processed oil screen, or some combination of the three. {MULTI} of those fail more than one screen at once.</div>
        </div>
      </div>
      <div class="insights-grid">''' + ''.join(
    f'<div class="insight-item"><div class="insight-dot"></div><div class="insight-head">{esc(h)}</div><div class="insight-detail">{esc(d)}</div></div>'
    for h, d in INSIGHTS) + '</div>'

# ---------------------------------------------------------------------------
# Screen cards
# ---------------------------------------------------------------------------
def brand_list_html(bars_hit, label):
    names = sorted({b['Brand Name'] for b in bars_hit})
    first, rest = names[:4], names[4:]
    out = f'<div class="oil-card-brands"><span class="oil-card-brands-label">{label}</span> {esc(", ".join(first))}'
    if rest:
        out += (f' <details class="oil-card-more"><summary><span class="oil-card-more-text">and {len(rest)} more</span>'
                f'<span class="oil-card-less-text">Hide</span></summary><span class="oil-card-more-list">, {esc(", ".join(rest))}</span></details>')
    return out + '</div>'

SCREENS_INTRO = f'''        <p>Clean is three separate screens stacked together, not one soft label. A bar has to clear all three to make this list: an A or B ingredient quality grade, no artificial sweeteners, and no processed oils.</p>
        <p>{PCT_FAIL}% of the {TOTAL} bars in our database fail at least one of these. Here&#x27;s how often each screen catches a bar, and where it usually shows up.</p>'''

SCREENS_CARDS = f'''<div class="score-card">
  <div class="score-card-label">Ingredient Quality Grade C or Below</div>
  <div class="score-card-val">{len(LOW)} bars<span class="oil-card-pct">{pct(len(LOW), TOTAL)}%</span></div>
  <div class="score-card-desc">The most common reason a bar fails the clean screen. Scoring C, D, or F usually means synthetic additives, excess added sugar, or ultra-processed protein blends outweighing the ingredient list&#x27;s strengths.</div>
  <div class="oil-card-brands"><span class="oil-card-brands-label">Affects:</span> at least one flavor from {len({b['Brand Name'] for b in LOW})} of {len(ALL_BRANDS)} brands we track</div>
</div>
<div class="score-card">
  <div class="score-card-label">Artificial Sweeteners</div>
  <div class="score-card-val">{len(AS)} bars<span class="oil-card-pct">{pct(len(AS), TOTAL)}%</span></div>
  <div class="score-card-desc">Usually shows up as a flavor-rounding sweetener in low-sugar or high-fiber bars, often alongside allulose or fiber syrups to hit a specific sugar number on the label.</div>
  {brand_list_html(AS, 'Found in:')}
</div>
<div class="score-card">
  <div class="score-card-label">Processed Oils</div>
  <div class="score-card-val">{len(PO)} bars<span class="oil-card-pct">{pct(len(PO), TOTAL)}%</span></div>
  <div class="score-card-desc">Usually a refined oil like canola, soybean, palm, or a hydrogenated fat used for shelf stability or texture, not nutrition.</div>
  {brand_list_html(PO, 'Found in:')}
</div>'''
# The first card claims "most common reason": keep it true.
if len(LOW) < max(len(AS), len(PO)):
    SCREENS_CARDS = SCREENS_CARDS.replace('The most common reason a bar fails the clean screen. ', 'One of the two most common reasons a bar fails the clean screen. ', 1)

# ---------------------------------------------------------------------------
# Head, hero, snapshot, FAQ, explore cards
# ---------------------------------------------------------------------------
TITLE = f'Best Clean Protein Bars - Ranking {QN} Bars by Ingredient Quality'
DESC = f'We screened {TOTAL} bars for A/B grade, no artificial sweeteners, and no processed oils. {QN} passed all three. See the cleanest bars, ranked.'
assert len(DESC) <= 160, len(DESC)

HEAD_META = f'''  <title>{esc(TITLE)}</title>
  <meta name="description" content="{esc(DESC)}">'''

ARTICLE = f'''<script type="application/ld+json">
  {{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": {json.dumps(TITLE)},
  "description": {json.dumps(DESC)},
  "url": "{URL}",
  "image": "https://knowyourbar.com/bar_hero.png",
  "datePublished": "2026-04-01",
  "dateModified": "{today_iso()}",
  "author": {{
    "@type": "Organization",
    "name": "Know Your Bar",
    "url": "https://knowyourbar.com"
  }},
  "publisher": {{
    "@type": "Organization",
    "name": "Know Your Bar",
    "url": "https://knowyourbar.com"
  }},
  "mainEntityOfPage": {{
    "@type": "WebPage",
    "@id": "{URL}"
  }},
  "about": {{
    "@type": "Thing",
    "name": "Clean Eating Guide"
  }}
}}
  </script>'''

BREADCRUMB = '<script type="application/ld+json">\n  ' + json.dumps({
    '@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': 1, 'name': 'Know Your Bar', 'item': 'https://knowyourbar.com'},
        {'@type': 'ListItem', 'position': 2, 'name': 'Lifestyle Guides', 'item': 'https://knowyourbar.com'},
        {'@type': 'ListItem', 'position': 3, 'name': TITLE, 'item': URL}]}, indent=2) + '\n  </script>'

ITEMLIST = '<script type="application/ld+json">\n  ' + json.dumps({
    '@context': 'https://schema.org', '@type': 'ItemList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i + 1, 'name': f"{p[1]['Brand Name']} {p[1]['Flavor Name']}"}
        for i, p in enumerate(PICKS)]}, ensure_ascii=False, separators=(',', ':')) + '\n  </script>'

SOCIAL = f'''<meta property="og:type" content="article">
  <meta property="og:title" content="{esc(TITLE)}">
  <meta property="og:description" content="{esc(DESC)}">
  <meta property="og:url" content="{URL}">
  <meta property="og:image" content="https://knowyourbar.com/bar_hero.png">

  <!-- Twitter card -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(TITLE)} | Know Your Bar">
  <meta name="twitter:description" content="{esc(DESC)}">
  <meta name="twitter:image" content="https://knowyourbar.com/bar_hero.png">'''

HERO = f'''<h1 class="hero-title">{esc(TITLE)}</h1>
    <p class="hero-sub" style="color:#e8e4dc;">We reviewed {TOTAL} protein bars against three criteria: an A or B ingredient quality grade, no artificial sweeteners (sucralose, acesulfame potassium, aspartame, saccharin), and no processed oils (canola, soybean, palm, or hydrogenated). {PCT_PASS}% clear all three. We rank the cleanest protein bars by category, brand, and macros. Not just us telling you the flavors we like.</p>'''

SNAPSHOT = f'''    <div class="snap-item"><div class="snap-value">{QN}</div><div class="snap-label">Bars qualify</div></div>
    <div class="snap-item"><div class="snap-value">{DN}</div><div class="snap-label">Bars disqualified</div></div>
    <div class="snap-item"><div class="snap-value">{A_IN_Q}</div><div class="snap-label">A-grade bars</div></div>
    <div class="snap-item"><div class="snap-value">{len(Q_BRANDS)}</div><div class="snap-label">Brands represented</div></div>
    <div class="snap-item"><div class="snap-value">{fnum(AVG_P_Q)}g</div><div class="snap-label">Avg protein</div></div>'''

LEADERS = names_and(WF_NAMES[:3]) if len(WF_NAMES) >= 3 else None
FAQS = [
    ('What makes a protein bar "clean" on this page?',
     'For this guide, clean means three things at once: an A or B ingredient quality grade, no artificial sweeteners '
     '(sucralose, acesulfame potassium, aspartame, saccharin), and no processed oils (canola, soybean, palm, or hydrogenated oils). '
     f'{QN} of {TOTAL} bars in our database meet all three criteria.'),
    ('Are clean protein bars better for you?',
     'Cleaner ingredients generally means fewer synthetic additives, more whole-food protein sources, and less dependence on '
     'ultra-processed fats and sweeteners. That said, macros still matter. A clean bar can still be high in calories or sugar '
     'even if the ingredient list is excellent.'),
    ('Why do so many protein bars fail the clean screen?',
     f'{MULTI} of the {DN} disqualified bars fail more than one criterion at once, usually a processed oil and a below-B grade together. '
     'Manufacturers reach for cheap refined oils and synthetic sweeteners to hit specific price, shelf-life, or macro targets, '
     'and those same shortcuts tend to drag the ingredient score down too.'),
]
if BIG:
    FAQS.append(('Does Barebells or Quest have any clean bars?', 'No. ' + BIG[1]))
FAQS.append(('What protein bars are clean bars?',
             f'{QN} bars across {len(Q_BRANDS)} brands clear our clean screen'
             + (f', led by whole-food brands like {LEADERS} that qualify at or near 100%.' if LEADERS else '.')
             + ' The full ranked list is in the table below, sorted by ingredient quality.'))
FAQS += [
    ('Is erythritol considered a clean ingredient?',
     "It depends on your standard. Erythritol is a naturally occurring sugar alcohol, but commercially it's derived through "
     'fermentation of glucose, often from corn. We score it as a neutral-to-minor concern rather than an automatic disqualifier, '
     'so bars with erythritol can still earn A or B grades and appear on this list if the rest of the ingredient list is strong.'),
    ('What protein sources score best?',
     'Egg whites, whey protein concentrate, and whole-food sources like nuts and seeds score highest. Whey isolate and pea protein '
     'score slightly lower but are still solid. Collagen protein scores as a concern because it lacks the essential amino acids '
     'needed for muscle protein synthesis.'),
]
if len(MIX_EX) == 2:
    FAQS.append(('Can a brand have some clean flavors and some not?',
                 "Yes, and it's common. " + mix_sentence() + " Check the Mixed Lineups table above before assuming a brand's "
                 'whole lineup is clean just because one flavor is.'))
FAQS.append(('How often is this list updated?',
             'We update the database when new bars are added or when brands change their formulas. Grades on this page are '
             'rebuilt from the same database every time it changes, so they always match the Bar Finder. '
             f'The current data reflects {month_year()}.'))

EXPLORE = f'''<a href="/no-artificial-sweeteners" class="explore-more-card">
  <div class="explore-more-title">No Artificial Sweeteners</div>
  <div class="explore-more-desc">{guide_count(BARS, 'no-artificial-sweeteners')} bars with zero sucralose, aspartame, or acesulfame potassium. Scored by ingredient quality.</div>
</a>
<a href="/best-bars-for-diabetics" class="explore-more-card">
  <div class="explore-more-title">Best Bars for Diabetics</div>
  <div class="explore-more-desc">{guide_count(BARS, 'best-bars-for-diabetics')} bars screened for sugar, net carbs, fiber, protein, grade, and maltitol.</div>
</a>
<a href="/no-sugar-alcohols" class="explore-more-card">
  <div class="explore-more-title">No Sugar Alcohols</div>
  <div class="explore-more-desc">Bars that skip maltitol, erythritol, and other sugar alcohols entirely.</div>
</a>'''

ROWS, BAR_JSON = bar_table(Q, BARS, eager=30)

# ---------------------------------------------------------------------------
# Assemble
# ---------------------------------------------------------------------------
page = open(PAGE, encoding='utf-8').read()
for name, content in [
    ('head-meta', HEAD_META),
    ('jsonld-article', ARTICLE),
    ('jsonld-breadcrumb', BREADCRUMB),
    ('jsonld-faq', faq_jsonld(FAQS).strip()),
    ('jsonld-itemlist', ITEMLIST),
    ('social', SOCIAL),
    ('hero', HERO),
    ('snapshot', SNAPSHOT),
    ('top-picks', '\n'.join(pick_tile(*p) for p in PICKS)),
    ('screens-intro', SCREENS_INTRO),
    ('screens-cards', SCREENS_CARDS),
    ('findings', FINDINGS),
    ('brand-tables', BRAND_TABLES),
    ('list-heading', f'<h2 class="section-title">{QN} clean protein bars, ranked by ingredient quality</h2>'),
    ('result-count', f'<div class="gd-result-count" id="gd-result-count">Showing {min(30, QN)} of {QN} bars</div>'),
    ('bar-rows', ROWS),
    ('cta-heading', f'<h2 class="explore-cta-main-heading">See every bar that fits, not just the {QN} on this page</h2>'),
    ('explore-more', EXPLORE),
    ('faq', faq_html(FAQS)),
    ('bar-data', f'<script id="gd-bar-data" type="application/json">{BAR_JSON}</script>'),
]:
    page = replace_region(page, name, content)
page = stamp_dates(page, today_iso())

# ---------------------------------------------------------------------------
# QA before writing
# ---------------------------------------------------------------------------
problems, n_rows = grade_sync_check(page, BARS)
if n_rows != QN:
    problems.append(f'bar rows on page {n_rows} != qualifying bars {QN}')
for bad in ['href="Yes"', 'href="None"', '"ws":"Yes"', '"ws":"None"', '"az":"None"', '"az":"Yes"']:
    if bad in page:
        problems.append(f'broken link field: {bad}')
if problems:
    print('GRADE-SYNC / QA FAILED, page not written:')
    for p in problems[:50]:
        print('  ', p)
    sys.exit(1)

open(PAGE, 'w', encoding='utf-8').write(page)
print(f'{PAGE}: {QN} of {TOTAL} bars qualify, {A_IN_Q} A-grade, {len(Q_BRANDS)} brands')
print('Top picks:')
for label, b, _ in PICKS:
    print(f'   {label}: {b["Brand Name"]} | {b["Flavor Name"]} ({b["score_band"]})')
print(f'Brand tables: {len(CONSIDER)} consider, {len(MIXED)} mixed, {len(AVOID)} avoid')
print(f'Grade-sync: {n_rows} bar rows checked against bars.js, 0 mismatches')
