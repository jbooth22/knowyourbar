#!/usr/bin/env python3
"""Rebuild glp1-protein-bars.html from bars.js.

Run from the repo root:  python3 build_glp1_protein_bars.py

Opens the LIVE page and rewrites only the <!-- kyb:NAME --> regions (nav,
footer, fonts, CSS and JS stay as deployed). Every number, pick, brand row and
bar row comes from bars.js. Copy that depends on a fact is checked; if one
stops being true the build stops and lists it.

Screen: GUIDE_FILTERS['glp1-protein-bars'] = protein >= 15, calories <= 200,
sugar <= 4, fiber >= 3, no sugar alcohol, A or B grade. The sugar alcohol check
reads both the label gram line (must be 0) and the ingredient list
(kyb_guide_lib.has_sugar_alcohol), because many labels name a sugar alcohol but
declare 0g (decided 2026-09-24).
"""
from kyb_guide_lib import *

PAGE = 'glp1-protein-bars.html'
URL = 'https://knowyourbar.com/glp1-protein-bars'
PUBLISHED = '2026-07-23'

ALL = load_bars()
QF = GUIDE_FILTERS['glp1-protein-bars']
Q = [b for b in ALL if QF(b)]
D = [b for b in ALL if not QF(b)]
N, ND, NT = len(Q), len(D), len(ALL)
BRANDS_ALL = len({b['Brand Name'] for b in ALL})
BRANDS_Q = len({b['Brand Name'] for b in Q})
GR = {g: sum(1 for b in Q if b.get('score_band') == g) for g in BAND_ORDER}
C = Claims()

SCREEN = Screen(ALL, [
    ('protein', 'protein', lambda b: P(b) < 15),
    ('cal', 'calories', lambda b: CAL(b) > 200),
    ('sugar', 'sugar', lambda b: SUG(b) > 4),
    ('fiber', 'fiber', lambda b: FIB(b) < 3),
    ('sa', 'sugar alcohol', lambda b: SA(b) > 0 or has_sugar_alcohol(b)),
    ('grade', 'ingredient grade', lambda b: b.get('score_band') not in ('A', 'B')),
])
FAIL = {k: SCREEN.count(k) for k, _, _ in SCREEN.checks}
MULTI = SCREEN.multi(D)
C.check(all(SCREEN.fails[b['Key']] for b in D) and not any(SCREEN.fails[b['Key']] for b in Q), 'the six checks match the GLP-1 filter')
AVG_CAL, AVG_FIB, AVG_P = avg(Q, 'Calories'), avg(Q, 'Dietary Fiber (g)'), avg(Q, 'Protein (g)')
AVG_P100 = sum(p100(b) or 0 for b in Q) / N

# ---------------------------------------------------------------------------
# Top picks (best band first; this set is small, so later tiles can fall
# back to the next band, per GUIDE_CRITERIA)
# ---------------------------------------------------------------------------
PK = Picker(Q, floor=15)
SCO = Scoper(Q, 'that clears the GLP-1 screen', floor=15)
P100 = lambda b: p100(b) or 0
best = PK.rank_sum([(P100, True), (FIB, True), (SUG, False)])
top_r = PK.pick(lambda b: (-P100(b), CAL(b)))
low_s = PK.pick(lambda b: (SUG(b), CAL(b)))
top_f = PK.pick(lambda b: (-FIB(b), CAL(b)))
# The best band here is small and sits right at the 15g floor, so these two
# tiles only take a bar that actually stands out on their number; when the
# band has none left, Picker falls back to the next band (GUIDE_CRITERIA).
top_p = PK.pick(lambda b: (-P(b), CAL(b)), lambda b: P(b) > 15)
low_cal = PK.pick(lambda b: (CAL(b), -P(b)), lambda b: CAL(b) <= 160)
C.check(all([best, low_cal, low_s, top_f, top_r, top_p]), 'six distinct top picks available')
PICKS = [
    ['Best overall', best,
     f"{fnum(P(best))}g protein, {fnum(CAL(best))} calories, {fnum(SUG(best))}g sugar, and {fnum(FIB(best))}g fiber, with no "
     "sugar alcohol in the ingredients. It clears all six screening criteria without leaning hard on any single one."],
    ['Best protein per calorie', top_r,
     f"{fnum(P(top_r))}g protein at {fnum(CAL(top_r))} calories, {fnum(P100(top_r))}g protein per 100 calories, "
     f"{SCO(P100, top_r, 'best ratio')}."],
    ['Lowest sugar', low_s,
     f"{fnum(SUG(low_s))}g of sugar, {SCO(SUG, low_s, 'lowest', False)}, at {fnum(CAL(low_s))} calories."],
    ['Most fiber', top_f,
     f"{fnum(FIB(top_f))}g of fiber, {SCO(FIB, top_f, 'most')}, which helps slow digestion and extend fullness."],
    ['Highest protein', top_p,
     f"{fnum(P(top_p))}g protein at {fnum(CAL(top_p))} calories, {SCO(P, top_p, 'most protein')}."],
    ['Lowest calorie', low_cal,
     f"{fnum(CAL(low_cal))} calories, {SCO(CAL, low_cal, 'lowest', False)}, without dropping under 15g of protein."],
]
PICKS_EXTRA = '''
      <div class="callout-box"><strong>Heads up:</strong> We are not doctors or dietitians. These are the qualities we see people on GLP-1 medications look for, so that is what we filtered on. This page is not medical advice. Talk to your doctor or a registered dietitian about what actually fits your treatment plan.</div>'''
PICKS_INTRO = ("Everyone on GLP-1 medications has different tolerances, but if you are on this page you probably already know "
               "you want dense protein, a manageable calorie count, and low sugar. Here are the standouts for what people "
               "typically look for, all clearing the full six-criteria screen. Grades below reflect ingredient quality only, "
               "not a GLP-1-specific rating.")

# ---------------------------------------------------------------------------
# What we screened for
# ---------------------------------------------------------------------------
SCREENED = f'''
    <div class="section-inner">
      <h2 class="section-title">What we screened for on this page</h2>
      <div class="section-body">
        <p>People on GLP-1 medications managing a smaller appetite usually care about three things above all else:</p>
        <ul class="diab-criteria-list">
          <li><strong>Protein</strong>: enough to make a small amount of food count</li>
          <li><strong>Calories</strong>: low enough to fit a reduced appetite without crowding out real meals</li>
          <li><strong>Sugar</strong>: kept low since blood sugar swings can compound GI discomfort</li>
        </ul>
        <p>We added three more filters on top:</p>
        <ul class="diab-criteria-list">
          <li><strong>Fiber</strong>: enough to support satiety and slow digestion</li>
          <li><strong>No sugar alcohols</strong>: none in the ingredient list and 0g on the label, since GI tolerance is a common concern on GLP-1 medications</li>
          <li><strong>Ingredient grade</strong>: an A or B ingredient quality grade</li>
        </ul>
        <p>{N} of {comma(NT)} bars, {pct(N, NT)}% of the database, clear all six.</p>
      </div>
      <div class="score-grid" style="margin-top:1.5rem;">
{simple_card_html('Protein Under 15g', FAIL['protein'], NT, 'Less food volume means every bite needs to work harder. We required at least 15g of protein per bar.')}
{simple_card_html('Calories Over 200', FAIL['cal'], NT, 'A reduced appetite means a smaller calorie budget overall. We capped this list at 200 calories.')}
{simple_card_html('Sugar Over 4g', FAIL['sugar'], NT, 'Sugar spikes can compound the nausea and GI discomfort some people already experience on GLP-1 medications.')}
{simple_card_html('Contains Sugar Alcohols', FAIL['sa'], NT, 'Sugar alcohols are a frequent trigger for bloating and GI discomfort, a common concern on GLP-1 medications, so we excluded every bar that lists a sugar alcohol, whether in the ingredients or as grams on its label.')}
</div>
    </div>
'''

# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------
SPLIT = brand_split(ALL, QF)
C.check(FAIL['sugar'] > max(FAIL['protein'], FAIL['cal']), 'sugar is the toughest single filter')
narrowest = all(len({b['Brand Name'] for b in ALL if f(b)}) >= BRANDS_Q for f in GUIDE_FILTERS.values())
INSIGHTS = [
    ('Sugar is the toughest single filter.',
     f"{comma(FAIL['sugar'])} bars ({pct(FAIL['sugar'], NT)}%) fail on sugar, more than fail on protein ({pct(FAIL['protein'], NT)}%) "
     f"or calories ({pct(FAIL['cal'], NT)}%). Most protein bars are simply not formulated with a 4g sugar ceiling in mind."),
    ('Zero tolerance for sugar alcohols cuts deep.',
     f"{comma(FAIL['sa'])} bars ({pct(FAIL['sa'], NT)}%) contain a sugar alcohol. Unlike our keto and diabetics guides, we "
     'exclude all of them here, not just the higher-glycemic ones, because GI tolerance is the priority on this list.'),
    ('Most disqualified bars fail more than one check.' if MULTI > ND - MULTI else 'Most disqualified bars miss on a single check.',
     f'{comma(MULTI)} of {comma(ND)} disqualified bars fail two or more of the six criteria at once.'),
    (f'{BRANDS_Q} brands have at least one qualifying flavor.',
     f'Out of {BRANDS_ALL} tracked brands, {BRANDS_Q} have at least one flavor that clears all six checks.'
     + (' This is the narrowest brand spread of any guide on the site.' if narrowest else '')),
    (f'Qualifying bars average {fnum(round(AVG_FIB, 1))}g of fiber.',
     'Comfortably above the 3g minimum we required, which supports the satiety effect people on GLP-1 medications are already '
     'getting from the medication itself.'),
    (f"Only {GR['A']} of {N} qualifying bars earn an A on ingredient quality.",
     f"Meeting the macro thresholds and having a clean ingredient list are two different things. {GR['B']} qualifying bars "
     'land at a B, still solid but built with more processed ingredients.'),
]
C.check(AVG_FIB > 5, 'qualifying fiber average comfortably above 3g')
FINDINGS = findings_html(f'What we found screening {comma(NT)} bars for GLP-1 friendly criteria', f'{pct(ND, NT)}%',
                         'of bars fail at least one of our six checks',
                         f'{comma(ND)} of {comma(NT)} bars fail on protein, calories, sugar, fiber, grade, sugar alcohols, or '
                         f'some combination. {comma(MULTI)} of those fail more than one check at once.', INSIGHTS)

# ---------------------------------------------------------------------------
# Brand tables
# ---------------------------------------------------------------------------
def g(x): return f'{fnum(round(x, 1))}g'
def cals(x): return fnum(round(x))
def pick_of(r):
    band = next(x for x in BAND_ORDER if any(b.get('score_band') == x for b in r['qual']))
    return min((b for b in r['qual'] if b.get('score_band') == band), key=lambda b: (-P100(b), name_key(b)))
def note(r, kind):
    avgs = f"{g(avg(r['bars'], 'Protein (g)'))} protein and {cals(avg(r['bars'], 'Calories'))} calories"
    if kind == 'consider':
        lead = f"{all_n_flavors(r['total'])} clear" if r['d'] == 0 else f"{r['q']} of {r['total']} flavors clear"
        return f"{lead} the full GLP-1 screen, averaging {avgs} across the whole lineup."
    if kind == 'mixed':
        return f"{r['q']} of {r['total']} flavors clear the full screen. {pick_of(r)['Flavor Name']} is the clean pick."
    lead = f"Only {pick_of(r)['Flavor Name']} clears it. " if r['q'] == 1 else (f"{r['q']} flavors clear it. " if r['q'] else '')
    return f"{lead}Misses mainly on {names_and(SCREEN.misses_mainly(r['disq']))}. Averages {avgs}."
BRANDS = macro_brand_tables_html(
    SPLIT, h2='Best Brands for GLP-1', table_id='glp1', table_class='glp1-brand-table',
    intro_html='''        <p>We are not doctors or dietitians, and this is not medical advice. For every brand we track, we checked what share of its flavors clear the protein, calorie, sugar, fiber, grade, and sugar alcohol screen used above, then averaged protein and calories across its whole lineup. Grade columns show ingredient quality only, not a GLP-1-specific rating. Click any brand name to jump to its flavors in the table below.</p>
        <p><strong>Consider</strong> means at least 75% of the brand's tracked flavors clear our full screen (allowing at most 2 misses). <strong>Mixed</strong> means some flavors clear it and some do not, so the specific flavor matters. <strong>Avoid</strong> means at least 80% of the brand's tracked flavors miss it and fewer than 3 clear it.</p>''',
    before_tables=f'''
      <div class="guide-jump-row">
        <a href="#bar-list" class="guide-jump-link">Jump straight to all {comma(N)} bars &darr;</a>
      </div>''',
    cols=[('Flavors That Qualify', lambda r: f"{r['q']}/{r['total']}"),
          ('Ingredient Quality', lambda r: grade_range_html(*grade_range(r['bars']))),
          ('Avg Protein', lambda r: g(avg(r['bars'], 'Protein (g)'))),
          ('Avg Calories', lambda r: cals(avg(r['bars'], 'Calories')))],
    notes={'consider': "Most or all tracked flavors from these brands clear the full GLP-1 screen.",
           'mixed': 'Some flavors from these brands clear the screen and some do not, so the specific flavor matters.',
           'avoid': "Few or none of these brands' tracked flavors clear the protein, calorie, sugar, fiber, grade, and sugar alcohol screen."},
    row_note=note)

# ---------------------------------------------------------------------------
# FAQ
# ---------------------------------------------------------------------------
def brand_row(name): return next((r for r in SPLIT[0] + SPLIT[1] + SPLIT[2] if r['brand'] == name), None)
def brand_faq(name):
    r = brand_row(name)
    C.check(r is not None, f'{name} is in bars.js')
    tail = f"averaging {g(avg(r['bars'], 'Protein (g)'))} protein and {cals(avg(r['bars'], 'Calories'))} calories across the lineup"
    if r['d'] == 0:
        return f"By our screen, yes: all {r['total']} tracked {name} flavors clear all six criteria, {tail}."
    if r['q'] == 0:
        return (f"Not by our screen: none of the {r['total']} tracked {name} flavors clear all six criteria. They miss mainly on "
                f"{names_and(SCREEN.misses_mainly(r['disq']))}.")
    return (f"Mixed by our screen: {r['q']} of {r['total']} tracked {name} flavors clear all six criteria, {tail}. "
            f"{pick_of(r)['Flavor Name']} is the clean pick; check the flavor table above before assuming the whole lineup qualifies.")
FAQS = [
    ("What should I look for in a protein bar if I'm on a GLP-1 medication?",
     'We are not doctors, but here is what we filtered on: at least 15g of protein, 200 calories or less, 4g of sugar or less, '
     'at least 3g of fiber, no sugar alcohol, and an A or B ingredient quality grade. Appetite suppression from '
     'GLP-1 medications means less food volume overall, so every bite needs to carry more protein relative to its size. '
     f'{N} of {comma(NT)} bars clear all six.'),
    ('Why does calorie count matter more on GLP-1 medications?',
     "Reduced appetite means a smaller daily calorie budget, so a snack that eats up 300 to 400 calories can crowd out an entire "
     "meal's worth of nutrition. We capped this list at 200 calories per bar so the protein-to-calorie ratio stays favorable "
     f'even when you can only manage a small amount of food. Qualifying bars average {fnum(round(AVG_CAL, 1))} calories.'),
    ('Why exclude sugar alcohols entirely instead of just capping net carbs?',
     'GI tolerance is a common concern on GLP-1 medications, and sugar alcohols are a frequent culprit behind bloating, gas, '
     'and digestive discomfort. Rather than trying to weigh which sugar alcohols are better or worse tolerated, we excluded any '
     'bar that lists a sugar alcohol, checking the ingredient list as well as the gram line, since many labels name one but '
     'declare 0g. This is a stricter rule than our keto and diabetics guides, which allow '
     'low-glycemic sugar alcohols like erythritol; here we treat the digestive-tolerance question, not just the blood-sugar '
     'question, as the priority.'),
    ('What does protein per 100 calories mean and why does it matter here?',
     'It is protein divided by calories, scaled to a 100-calorie basis, so you can compare bars of different sizes on equal '
     'footing. A bar with 20g of protein at 250 calories is less efficient than one with 15g at 150 calories, even though the '
     f'first has more total protein. Qualifying bars average {fnum(round(AVG_P100, 1))}g of protein per 100 calories.'),
    ('Why does fiber matter on this list?',
     'Fiber slows digestion and supports satiety, which reinforces the effect GLP-1 medications already have on appetite and '
     'helps you feel satisfied on a smaller amount of food. We required at least 3g of fiber for every bar on this list, and '
     f'qualifying bars average {fnum(round(AVG_FIB, 1))}g.'),
    ('What does the ingredient quality grade mean on this page?',
     "Our A through F grade rates how clean and minimally processed a bar's ingredients are. It is a separate measurement from "
     'GLP-1 suitability. A bar can score an A on ingredient quality and still not fit the macro profile people on GLP-1 '
     'medications look for, or vice versa. We use it as one of the six filters here, requiring an A or B, but the core of the '
     'screen is protein, calories, sugar, fiber, and the sugar alcohol exclusion.'),
    ('Is NuGo good for GLP-1?', brand_faq('NuGo')),
    ('Is Promix good for GLP-1?', brand_faq('Promix')),
    ('How is the brand table below different from the ranked bar list above?',
     'The ranked list at the top of this page covers individual flavors that pass all six criteria. The brand table further '
     "down rolls that up to the brand level: what share of each brand's tracked flavors qualify, plus average protein and "
     'calories across the whole lineup. Use the bar list to find a specific flavor, and the brand table to get a quick read on '
     'a brand before you go looking.'),
    ('How many protein bars in your database qualify for this list?',
     f'Out of {comma(NT)} bars in our database, {N} meet all six criteria: 15g or more protein, 200 calories or less, 4g or '
     'less sugar, 3g or more fiber, no sugar alcohol, and an A or B ingredient grade. That is about '
     f'{pct(N, NT)}% of the full database.'),
]

# ---------------------------------------------------------------------------
# Regions
# ---------------------------------------------------------------------------
TITLE = f'GLP-1 Protein Bars - {N} Bars Ranked by Ingredient Quality'
H1 = f'GLP-1 Friendly Protein Bars - We Screened {comma(NT)} Bars, {N} Passed'
DESC = f'We screened {comma(NT)} bars for protein, calories, sugar, and fiber. {N} pass with no sugar alcohol and an A or B grade.'
REGIONS = [r for r in guide_head_regions(title=TITLE, h1=H1, desc=DESC, og_desc=DESC, url=URL,
                                         about='GLP-1 Medication Eating Guide', published=PUBLISHED,
                                         faqs=[(q, plain_text(a)) for q, a in FAQS], picks=PICKS)
           if r[0] != 'jsonld-itemlist']
REGIONS += [
    ('hero', f'''<h1 class="hero-title">{esc(H1)}</h1>
    <p class="hero-sub" style="color:#e8e4dc;">Appetite suppression from GLP-1 medications means less food volume, so every bite needs to work harder for protein. We are not doctors, so instead of medical advice, here is what we did: we screened every bar in our database against six thresholds people on GLP-1 medications commonly look for: 15g or more protein, 200 calories or less, 4g or less sugar, 3g or more fiber, no sugar alcohol, and an A or B ingredient quality grade. {N} of {comma(NT)} bars pass all six. See exactly how each bar stacks up, then check the brand table below for a quick read on your favorite brand.</p>'''),
    ('snapshot', f'''
    <div class="snap-item"><div class="snap-value">{comma(N)}</div><div class="snap-label">Bars qualify</div></div>
    <div class="snap-item"><div class="snap-value">{comma(ND)}</div><div class="snap-label">Bars disqualified</div></div>
    <div class="snap-item"><div class="snap-value">{GR['A']}</div><div class="snap-label">A-grade bars</div></div>
    <div class="snap-item"><div class="snap-value">{BRANDS_Q}</div><div class="snap-label">Brands represented</div></div>
    <div class="snap-item"><div class="snap-value">{AVG_P:.1f}g</div><div class="snap-label">Avg protein</div></div>
  '''),
    ('picks', picks_with_extra_html('Top picks for GLP-1', PICKS_INTRO, PICKS, PICKS_EXTRA)),
    ('screened', SCREENED),
    ('findings', FINDINGS),
    ('brands', BRANDS),
    ('explore-more', '''
<a href="/keto-protein-bars" class="explore-more-card">
  <div class="explore-more-title">Keto Protein Bars</div>
  <div class="explore-more-desc">Low net carb bars ranked by ingredient quality, not just macros.</div>
</a>
<a href="/best-bars-for-diabetics" class="explore-more-card">
  <div class="explore-more-title">Best Bars for Diabetics</div>
  <div class="explore-more-desc">Bars screened for sugar, net carbs, fiber, and no maltitol.</div>
</a>
<a href="/no-sugar-alcohols" class="explore-more-card">
  <div class="explore-more-title">No Sugar Alcohols</div>
  <div class="explore-more-desc">Bars that skip maltitol, erythritol, and other sugar alcohols entirely.</div>
</a>
      '''),
    ('faq', faq_items_html(FAQS)),
]
REGIONS += guide_list_regions(Q, ALL, heading=f'{comma(N)} protein bars for GLP-1, ranked by ingredient quality')

if __name__ == '__main__':
    n = build_guide_page(PAGE, REGIONS, Q, ALL, C)
    print(f'{PAGE}: {N} qualify, {ND} disqualified, {n} rows, grade-sync 0 mismatches')
    for label, b, why in PICKS:
        print(f'  {label}: {full(b)} ({b["score_band"]})')
