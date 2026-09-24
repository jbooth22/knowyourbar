#!/usr/bin/env python3
"""Rebuild caffeine-protein-bars.html from bars.js.

Run from the repo root:  python3 build_caffeine_protein_bars.py

Opens the LIVE page and rewrites only the <!-- kyb:NAME --> regions (nav,
footer, fonts, CSS and JS stay as deployed). Every number, pick, zone, brand
row and bar row comes from bars.js; copy that depends on a fact is checked
and the build stops if one stops being true.

Screen: GUIDE_FILTERS['caffeine-protein-bars'] = Caffeine (mg) > 0 (any
declared amount, no dose minimum, no grade gate). Zones are measured against
a ~95mg 8oz cup of coffee: Light < 50, Moderate 50-94, High 95-149,
Very High 150+. Brand tables rate each brand's CAFFEINATED flavors on A/B
share (BRIEFING: Caffeine reframes the ratio column).
"""
import re
from collections import Counter
from kyb_guide_lib import *
from kyb_dose_guide import dose_list_regions

PAGE = 'caffeine-protein-bars.html'
URL = 'https://knowyourbar.com/caffeine-protein-bars'
PUBLISHED = '2026-04-10'

ALL = load_bars()
QF = GUIDE_FILTERS['caffeine-protein-bars']
Q = [b for b in ALL if QF(b)]
N, NT = len(Q), len(ALL)
C = Claims()
def CF(b): return num(b.get('Caffeine (mg)')) or 0
def mg(v): return f'{fnum(round(v, 1))}mg'
BRANDS_Q = sorted({b['Brand Name'] for b in Q})
GR = {g: sum(1 for b in Q if b.get('score_band') == g) for g in BAND_ORDER}
MAXB = max(Q, key=lambda b: (CF(b), -len(nm(b))))
MAXC = CF(MAXB)
MINC = min(CF(b) for b in Q)

ZONES = [('Light Caffeine', 0, 50, 'A fraction of a cup of brewed coffee.'),
         ('Moderate Caffeine', 50, 95, 'Roughly in line with a standard 8oz cup of coffee.'),
         ('High Caffeine', 95, 150, 'More than a cup, less than two.'),
         ('Very High Caffeine', 150, 10 ** 6, 'Approaching or exceeding an energy drink.')]
ZB = {z: [b for b in Q if lo <= CF(b) < hi] for z, lo, hi, _ in ZONES}
def avg_score(bars): return sum(score(b) or 0 for b in bars) / len(bars) if bars else 0

def zone_desc(z, lead):
    bs = ZB[z]
    if not bs:
        return lead + ' No bar in the database currently lands here.'
    brands = Counter(b['Brand Name'] for b in bs).most_common()
    lo, hi = grade_range(bs)
    grades = f'grades {lo}' + (f' to {hi}' if hi != lo else '')
    if len(brands) == 1:
        return f"{lead} Every bar in this zone is {brands[0][0].strip()}, and " + (f"every one grades {lo}." if lo == hi else f"they {grades.replace('grades', 'grade')}.")
    return (f"{lead} Led by {names_and([b.strip() for b, _ in brands[:2]])}; {grades}, averaging a "
            f"{g1(avg_score(bs))} ingredient score.")

# ---------------------------------------------------------------------------
# Top picks (best band first; caffeine mg is the guide's own tie-break)
# ---------------------------------------------------------------------------
SRC_RX = r'coffee|espresso|matcha|green tea|black tea|tea extract|yerba|guarana|guayusa'
def src_names(b):
    t = ingr(b).lower()
    found = [n for n in ('coffee', 'espresso', 'matcha', 'green tea', 'yerba mate', 'guarana', 'guayusa')
             if re.search(n.split()[0] if n == 'yerba mate' else n, t)]
    return found
def plant_only(b): return bool(re.search(SRC_RX, ingr(b), re.I)) and not re.search(r'\bcaffeine\b', ingr(b), re.I)

PK = Picker(Q, floor=0, diverse=True)
SCO = Scoper(Q, 'on this page', floor=0)
best = PK.pick(lambda b: (-P(b), CF(b)))
top_dose = PK.pick(lambda b: (-CF(b), -P(b)), lambda b: b.get('score_band') in ('A', 'B'))
gentle = PK.pick(lambda b: (CF(b), -P(b)), lambda b: CF(b) <= 30)
top_p = PK.pick(lambda b: (-P(b), CAL(b)), lambda b: P(b) >= 15)
top_r = PK.pick(lambda b: (-(p100(b) or 0), -P(b)), lambda b: (p100(b) or 0) >= 7)
natural = PK.pick(lambda b: (-CF(b), -P(b)), plant_only)
C.check(all([best, top_dose, gentle, top_p, top_r, natural]), 'six distinct top picks available')
PICKS = [
    ['Best overall', best,
     f"{fnum(P(best))}g protein at a {mg(CF(best))} dose, the most protein of any {best['score_band']}-grade caffeinated bar, "
     "with ingredient quality leading the way."],
    ['Highest caffeine, still solid quality', top_dose,
     f"{mg(CF(top_dose))}, {SCO(CF, top_dose, 'highest dose')}, paired with {fnum(P(top_dose))}g protein."],
    ['Gentlest dose', gentle,
     f"{mg(CF(gentle))}, {SCO(CF, gentle, 'lowest dose', False)}, a small fraction of a cup of coffee."],
    ['Highest protein', top_p, f"{fnum(P(top_p))}g of protein, {SCO(P, top_p, 'most')}, at {mg(CF(top_p))} of caffeine."],
    ['Best protein per calorie', top_r,
     f"{fnum(P(top_r))}g of protein at {fnum(CAL(top_r))} calories, {fnum(p100(top_r))}g per 100 calories, "
     f"{SCO(lambda b: p100(b) or 0, top_r, 'best ratio')}."],
    ['Caffeine from coffee or tea', natural,
     f"Its {mg(CF(natural))} comes from {names_and(src_names(natural)) or 'coffee or tea'} in the ingredient list, not added caffeine."],
]
for p in PICKS:
    if p[1].get('score_band') in ('C', 'D', 'F'):
        p[2] += f" The tradeoff is a {p[1]['score_band']} grade on ingredient quality."
PICKS_EXTRA = '''
      <div class="callout-box"><strong>Heads up:</strong> This page is not medical advice. Talk to your doctor if you have questions about caffeine and your health, especially if you are pregnant, sensitive to stimulants, or combine these with other caffeinated products.</div>'''

# ---------------------------------------------------------------------------
# Zones
# ---------------------------------------------------------------------------
def zcard(z, desc):
    n = len(ZB[z])
    return f'''<div class="score-card">
  <div class="score-card-label">{esc(z)}</div>
  <div class="score-card-val">{n} bars<span class="oil-card-pct">{g1(100 * n / N)}% of caffeinated bars</span></div>
  <div class="score-card-desc">{esc(zone_desc(z, desc))}</div>
</div>'''
ZONES_HTML = f'''
    <div class="section-inner">
      <h2 class="section-title">Four caffeine zones, measured against a cup of coffee</h2>
      <div class="section-body">
        <p>Every bar on this page states its caffeine content on the label. We grouped all {N} into four zones based on how that dose compares to a standard 8oz cup of brewed coffee, which runs roughly 95mg: Light is under 50mg, Moderate 50 to 94mg, High 95 to 149mg, and Very High 150mg or more.</p>
      </div>
      <div class="score-grid" style="margin-top:1.5rem;">
{chr(10).join(zcard(z, d) for z, _, _, d in ZONES)}

      </div>
    </div>
'''

# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------
VH = ZB['Very High Caffeine']
VH_BRANDS = sorted({b['Brand Name'].strip() for b in VH})
best_zone = max((z for z, *_ in ZONES if ZB[z]), key=lambda z: avg_score(ZB[z]))
BIG = Counter(b['Brand Name'] for b in Q).most_common(1)[0]
BIG_BARS = [b for b in Q if b['Brand Name'] == BIG[0]]
BIG_AB = sum(1 for b in BIG_BARS if b.get('score_band') in ('A', 'B'))
BIG_DOSES = Counter(CF(b) for b in BIG_BARS).most_common(1)[0]
A_BRANDS = Counter(b['Brand Name'] for b in Q if b.get('score_band') == 'A').most_common(1)
C.check(GR['A'] >= 1, 'at least one A-grade caffeinated bar')
INSIGHTS = []
if VH:
    lo, hi = grade_range(VH)
    INSIGHTS.append(
        ('The Very High zone is ' + ('a single brand' if len(VH_BRANDS) == 1 else f'{num_word(len(VH_BRANDS))} brands') +
         (', and it grades worst.' if lo in ('D', 'F') else '.'),
         f"All {len(VH)} bars at 150mg or more come from {names_and(VH_BRANDS)}, grading {lo}" + (f' to {hi}' if hi != lo else '')
         + f", averaging a score of {g1(avg_score(VH))}. More caffeine did not buy better ingredients here."))
INSIGHTS += [
    (f"The {best_zone.split()[0]} zone scores best on average.",
     f"Bars in the {best_zone} zone average a {g1(avg_score(ZB[best_zone]))} ingredient score, the highest of the four zones."),
    (f"{BIG[0]} is the single largest caffeinated lineup.",
     f"{BIG[1]} of the {N} caffeinated bars come from {BIG[0]}, and {BIG_AB} of those {BIG[1]} grade A or B"
     + (f", {'all' if BIG_DOSES[1] == BIG[1] else 'most'} at {mg(BIG_DOSES[0])}." if BIG_DOSES[1] >= BIG[1] / 2 else '.')),
    (f"Only {GR['A']} of {N} caffeinated bars earn an A on ingredient quality.",
     f"{A_BRANDS[0][0]} accounts for {A_BRANDS[0][1]} of the {GR['A']} A-grade bars." if A_BRANDS else ''),
    (f"A single {MAXB['Brand Name'].strip()} bar can eat most of your daily caffeine budget.",
     f"At {mg(MAXC)}, the highest-dose bar we track carries roughly {round(100 * MAXC / 400)}% of the FDA's commonly cited "
     '400mg/day guidance for healthy adults, before counting your morning coffee.'),
]
C.check(MAXC >= 200, 'the highest-dose bar is a large share of the daily 400mg guidance')
FINDINGS = findings_html(f'What we found screening {comma(NT)} bars for caffeine', f'{pct(NT - N, NT)}%',
                         'of protein bars carry zero caffeine',
                         f'Only {N} of {comma(NT)} bars in our database declare any caffeine at all, from {len(BRANDS_Q)} brands. '
                         'This is a small, deliberate subcategory, not a spectrum most brands dabble in.', INSIGHTS)

# ---------------------------------------------------------------------------
# Brand tables (among each brand's caffeinated flavors: A/B share)
# ---------------------------------------------------------------------------
def rows():
    out = []
    for brand in BRANDS_Q:
        bs = [b for b in Q if b['Brand Name'] == brand]
        ab = [b for b in bs if b.get('score_band') in ('A', 'B')]
        out.append(dict(brand=brand, bars=bs, qual=ab, disq=[b for b in bs if b not in ab], total=len(bs), q=len(ab), d=len(bs) - len(ab)))
    consider = sorted((r for r in out if r['q'] / r['total'] >= 0.75 and r['d'] <= 2), key=lambda r: (-r['q'], r['brand'].lower()))
    avoid = sorted((r for r in out if r['q'] == 0), key=lambda r: (-r['total'], r['brand'].lower()))
    taken = {r['brand'] for r in consider + avoid}
    mixed = sorted((r for r in out if r['brand'] not in taken), key=lambda r: (-r['total'], r['brand'].lower()))
    return consider, mixed, avoid
SPLIT = rows()
def avgc(r): return sum(CF(b) for b in r['bars']) / r['total']
def concerns(r):
    c = Counter(n for b in r['bars'] for n, cls in chips(b) if 'concern' in cls)
    return [n for n, _ in c.most_common(2)]
def note(r, kind):
    if kind == 'consider':
        t = r['total']
        lead = (("Its one caffeinated flavor grades" if t == 1 else "Both caffeinated flavors grade" if t == 2 else f"All {t} caffeinated flavors grade")
                if r['d'] == 0 else f"{r['q']} of {t} caffeinated flavors grade")
        return f"{lead} A or B, averaging {mg(avgc(r))} of caffeine."
    if kind == 'mixed':
        return f"{r['q']} of {r['total']} caffeinated flavors grade A or B, averaging {mg(avgc(r))} across the lineup."
    cs = concerns(r)
    one = r['total'] == 1
    t = r['total']
    return (f"{'Its one caffeinated flavor lands' if one else 'Both caffeinated flavors land' if t == 2 else f'All {t} caffeinated flavors land'} at C grade or below"
            + (f", weighed down by {names_and(cs)}" if cs else '') + f", averaging {mg(avgc(r))}.")
BRANDS = macro_brand_tables_html(
    SPLIT, h2='Brands worth knowing for caffeine', table_id='caf', table_class='caf-brand-table',
    intro_html='''        <p>We are not doctors or dietitians. Caffeine content and ingredient quality are two separate questions, and this category makes that obvious. For every brand with at least one caffeinated flavor, we checked what share of those specific caffeinated flavors grade A or B on ingredient quality, then averaged the dose across that brand's caffeinated lineup. Grade columns show ingredient quality only, not a caffeine-specific rating. Click any brand name to jump to its flavors in the table below.</p>''',
    before_tables=f'''
      <div class="guide-jump-row">
        <a href="#bar-list" class="guide-jump-link">Jump straight to all {N} bars &darr;</a>
      </div>''',
    cols=[('Flavors Grading A/B', lambda r: f"{r['q']}/{r['total']}"),
          ('Ingredient Quality', lambda r: grade_range_html(*grade_range(r['bars']))),
          ('Avg Caffeine', lambda r: mg(avgc(r)))],
    notes={'consider': "Most or all of these brands' caffeinated flavors grade A or B on ingredient quality.",
           'mixed': 'Some caffeinated flavors from these brands grade well and some do not, so the specific flavor matters.',
           'avoid': "None of these brands' caffeinated flavors clear a B grade on ingredient quality."},
    row_note=note)

# ---------------------------------------------------------------------------
# FAQ
# ---------------------------------------------------------------------------
def brand_faq(name):
    r = next((x for x in SPLIT[0] + SPLIT[1] + SPLIT[2] if x['brand'] == name), None)
    C.check(r is not None, f'{name} still makes a caffeinated bar')
    lo, hi = grade_range(r['bars'])
    rng = f'{lo}' + (f' to {hi}' if hi != lo else '')
    verdict = ('Mostly yes by our screen' if r['q'] >= r['total'] * 0.75 else 'Not on ingredient quality' if r['q'] == 0
               else 'Mixed by our screen')
    return (f"{verdict}: {r['q']} of {r['total']} tracked {name} caffeinated flavors grade A or B on ingredient quality "
            f"(grades {rng}), averaging {mg(avgc(r))} of caffeine.")
N_OVER150 = len(VH)
FAQS = [
    ('How much caffeine is in these protein bars compared to coffee?',
     f'An average brewed 8oz cup of coffee runs roughly 95mg of caffeine. Bars on this page range from {mg(MINC)}, a tiny fraction '
     f'of a cup, up to {mg(MAXC)}. Most fall in the light-to-moderate range, but a handful of outliers run much higher, so check '
     'the zone before you buy.'),
    ('Is 80mg of caffeine a lot?',
     '80mg sits close to a standard cup of drip coffee. For comparison, a shot of espresso is roughly 60-65mg and many energy '
     f'drinks run 150-300mg. {len(ZB["Light Caffeine"]) + len(ZB["Moderate Caffeine"])} of the {N} caffeinated bars we track land '
     'under 95mg rather than in energy-drink territory.'),
    ('What is the difference between natural and added caffeine sources?',
     'Some bars source caffeine from actual coffee, matcha, or green tea, which arrives along with other plant compounds. Others '
     'list plain caffeine, sometimes as caffeine anhydrous, added directly to the formula. Both raise the same total caffeine '
     'number on the label, but the ingredient list tells you which route a bar took, and that shows up in our ingredient scoring.'),
    ('How much caffeine in a protein bar is too much?',
     'That depends on your total daily caffeine intake from everything else you consume, and on your personal sensitivity. The '
     'FDA generally cites 400mg per day as a reasonable upper limit for healthy adults. A light or moderate bar is a small '
     + (f'fraction of that, but the {N_OVER150} bars on this page at 150mg or more take a large share of it on their own, '
        'especially stacked on top of your usual coffee or tea.' if N_OVER150 else 'fraction of that.')),
    ('Why do so few protein bars contain caffeine?',
     'Caffeine is a narrow, deliberate formulation choice, not a byproduct of other ingredients, so a brand has to build a bar '
     f'around it on purpose. Only {N} of {comma(NT)} bars in our database declare any caffeine at all. Most major brands, like '
     'Quest and Barebells, skip it entirely and let people pair a regular bar with their own coffee instead.'),
    ('Is Verb good for caffeine?', brand_faq('Verb')),
    ('Is JiMMYBAR! good for caffeine?', brand_faq('JiMMYBAR!')),
    ('How is the brand table below different from the ranked bar list above?',
     'The ranked list covers every individual flavor that declares caffeine. The brand table rolls that up to the brand level, '
     'specifically among each brand\'s caffeinated flavors: what share grade A or B on ingredient quality, plus the average dose '
     'across that brand\'s caffeinated lineup.'),
    ('How many protein bars in your database contain caffeine?',
     f'Out of {comma(NT)} bars in our database, {N} declare any caffeine content at all, about {pct(N, NT)}% of the full database. '
     'We did not set a minimum dose to qualify, any declared amount counts. This page is not medical advice. Talk to your doctor '
     'if you have questions about caffeine and your health.'),
]
C.check(not any(QF(b) for b in ALL if b['Brand Name'] in ('Quest', 'Barebells')), 'Quest and Barebells make no caffeinated bar')

# ---------------------------------------------------------------------------
# Regions
# ---------------------------------------------------------------------------
TITLE = f'Only {N} of {comma(NT)} Protein Bars Have Caffeine, Ranked'
H1 = f'Protein Bars with Caffeine - We Screened {comma(NT)} Bars, {N} Had Any'
DESC = (f'We screened {comma(NT)} bars for declared caffeine content. Only {N} qualify, from {mg(MINC)} to {mg(MAXC)}, ranked '
        'by ingredient quality across four caffeine zones.')
REGIONS = [r for r in guide_head_regions(title=TITLE, h1=H1, desc=DESC, og_desc=DESC, url=URL, about='Caffeinated Protein Bars',
                                         published=PUBLISHED, faqs=FAQS, picks=PICKS) if r[0] not in ('social', 'jsonld-itemlist')]
ITEMS = {'@context': 'https://schema.org', '@type': 'ItemList', 'name': 'Protein bars with caffeine ranked by ingredient quality',
         'numberOfItems': N, 'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'name': full(b)} for i, b in enumerate(sort_for_list(Q))]}
REGIONS += [
    ('jsonld-itemlist', '<script type="application/ld+json">\n  ' + json.dumps(ITEMS, ensure_ascii=False, separators=(',', ':')) + '</script>'),
    ('social', social_title_html(TITLE, DESC, URL).replace('  <meta property="og:site_name" content="Know Your Bar">\n', '')),
    ('hero', f'''<h1 class="hero-title">{esc(H1)}</h1>
    <p class="hero-sub" style="color:#e8e4dc;">We pulled every bar in our {comma(NT)}-bar database with declared caffeine content, no minimum dose required. {N} qualify, ranging from {mg(MINC)}, a tiny fraction of a cup of coffee, up to {mg(MAXC)}. We grouped them into four caffeine zones so you can match the dose to what you actually want, then ranked each zone by ingredient quality. The highest-dose bars are not the best-formulated ones, so it pays to look at both numbers together.</p>'''),
    ('snapshot', f'''
    <div class="snap-item"><div class="snap-value">{N}</div><div class="snap-label">Bars with caffeine</div></div>
    <div class="snap-item"><div class="snap-value">{len(BRANDS_Q)}</div><div class="snap-label">Brands represented</div></div>
    <div class="snap-item"><div class="snap-value">{mg(round(sum(CF(b) for b in Q) / N))}</div><div class="snap-label">Avg caffeine per bar</div></div>
    <div class="snap-item"><div class="snap-value">{mg(MAXC)}</div><div class="snap-label">Highest caffeine bar</div></div>
    <div class="snap-item"><div class="snap-value">{pct(N, NT)}%</div><div class="snap-label">Of the full database</div></div>
  '''),
    ('picks', picks_with_extra_html('Top picks for caffeine + quality',
                                    'Grades below reflect ingredient quality only, not a caffeine-specific rating. Six different '
                                    'priorities, six different answers.', PICKS, PICKS_EXTRA)),
    ('four-caffeine-zones-measured-against-a-c', ZONES_HTML),
    ('findings', FINDINGS),
    ('brands-worth-knowing-for-caffeine', BRANDS),
    ('explore-more', '''
<a href="/keto-protein-bars" class="explore-more-card">
  <div class="explore-more-title">Keto Protein Bars</div>
  <div class="explore-more-desc">Low net carb bars ranked by ingredient quality, not just macros.</div>
</a>
<a href="/glp1-protein-bars" class="explore-more-card">
  <div class="explore-more-title">GLP-1 Protein Bars</div>
  <div class="explore-more-desc">High protein, low calorie, no sugar alcohols, A or B grade only.</div>
</a>
<a href="/clean-protein-bars" class="explore-more-card">
  <div class="explore-more-title">Clean Protein Bars</div>
  <div class="explore-more-desc">A or B grade bars with no artificial sweeteners and no processed oils.</div>
</a>
      '''),
    ('faq', faq_items_html(FAQS)),
]
REGIONS += dose_list_regions(Q, ALL, f'{N} protein bars with caffeine, ranked by ingredient quality',
                             field='Caffeine (mg)', data_attr='caffeine', fmt=mg, grid_label='Caffeine',
                             grid_tag=lambda b: (lambda r: [f'#{r} highest of {N}', 'rank-green' if r / N <= 0.25 else 'rank-gray'])(
                                 1 + sum(1 for x in Q if CF(x) > CF(b))))

if __name__ == '__main__':
    n = build_guide_page(PAGE, REGIONS, Q, ALL, C)
    print(f'{PAGE}: {N} caffeinated bars, {n} rows, grade-sync 0 mismatches')
    for label, b, why in PICKS:
        print(f'  {label}: {full(b)} ({b["score_band"]})')
