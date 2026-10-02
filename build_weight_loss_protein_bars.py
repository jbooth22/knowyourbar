#!/usr/bin/env python3
"""Build weight-loss-protein-bars.html from bars.js. GUIDE PAGE v2 ("Best 10").

Run from the repo root:  python3 build_weight_loss_protein_bars.py

New guide (2026-10-02). Layout and every rule: claude/GUIDE_PAGE_SPEC_V2.md and
the v2 section of kyb_guide_lib.py. The page was started from a copy of
glp1-protein-bars.html (head, nav and footer as deployed, canonical changed,
GLP-1 page styles removed); every region below is generated. Every number,
pick and brand row comes from bars.js. Copy that depends on a fact is
checked; if one stops being true the build stops and lists it. Ingredient
quality is shown and ranked as a GRADE only.

Screen: GUIDE_FILTERS['weight-loss-protein-bars'] = protein >= 15, calories
<= 200, sugar <= 5, fiber >= 3. No grade gate (the Best 10 and its rules use
A/B only) and sugar alcohols are allowed (the page says how many use one; the
Lowest sugar slot skips them). Keeps the "We are not doctors or dietitians"
line.
Bar Finder: /bar-finder?protein=15&cal=200&sugar=5&fiber=3 (sliders; checked
key for key below on every build).

Guide slots (picked 2026-10-02, Jeff asked for the best picks delivered
without an approval round): Best whey protein, Lowest sugar (no sugar
alcohol), Best dairy-free, Best non-GMO. Fallbacks: Highest fiber, then Lowest
net carbs. The core six overlap the GLP-1 guide (the screens are close); the
dairy-free and non-GMO slots add two picks that are on no other guide, both
with an Amazon link.
"""
import re
from kyb_guide_lib import *

PAGE = 'weight-loss-protein-bars.html'
URL = 'https://knowyourbar.com/weight-loss-protein-bars'
PUBLISHED = '2026-10-02'
set_tie_seed('weight-loss-protein-bars')

ALL = load_bars()
QF = GUIDE_FILTERS['weight-loss-protein-bars']
Q = [b for b in ALL if QF(b)]
D = [b for b in ALL if not QF(b)]
N, ND, NT = len(Q), len(D), len(ALL)
BRANDS_ALL = len({b['Brand Name'] for b in ALL})
BRANDS_Q = len({b['Brand Name'] for b in Q})
GR = {g: sum(1 for b in Q if b.get('score_band') == g) for g in BAND_ORDER}
AB = GR['A'] + GR['B']
LOW = N - AB
C = Claims()
NC = net_carbs
DISCLAIMER = ("We are not doctors or dietitians. These are the qualities we know people look for, so that's what we "
              "factored in.")
def sa_any(b): return SA(b) > 0 or has_sugar_alcohol(b)

SCREEN = Screen(ALL, [
    ('cal', 'calories', lambda b: num(b.get('Calories')) is None or CAL(b) > 200),
    ('protein', 'protein', lambda b: P(b) < 15),
    ('sugar', 'sugar', lambda b: num(b.get('Sugars (g)')) is None or SUG(b) > 5),
    ('fiber', 'fiber', lambda b: FIB(b) < 3),
])
FAIL = {k: SCREEN.count(k) for k, _, _ in SCREEN.checks}
FAIL_BARS = {k: [b for b in ALL if k in SCREEN.fails[b['Key']]] for k, _, _ in SCREEN.checks}
C.check(all(SCREEN.fails[b['Key']] for b in D) and not any(SCREEN.fails[b['Key']] for b in Q), 'the four checks match the weight loss filter')
C.check(60 <= N <= 300, f'qualifying count in the expected range ({N})')
C.check(AB >= 20, 'at least 20 A/B bars, enough for a Best 10')
C.check(FAIL['sugar'] > max(FAIL['protein'], FAIL['cal'], FAIL['fiber']), 'sugar is the check that catches the most bars')
C.check(FAIL['cal'] * 3 > NT, 'more than a third of bars are over 200 calories')
MULTI = SCREEN.multi(D)
C.check(MULTI * 2 > ND, 'most bars that fail miss more than one check')
AVG_CAL, AVG_P, AVG_FIB, AVG_SUG = avg(Q, 'Calories'), avg(Q, 'Protein (g)'), avg(Q, 'Dietary Fiber (g)'), avg(Q, 'Sugars (g)')
AVG_P100 = sum(p100(b) or 0 for b in Q) / N
DB_AVG_CAL = avg(ALL, 'Calories')

# Big protein, big calories: bars with 20g+ protein and how many go over 200 calories
P20 = [b for b in ALL if P(b) >= 20]
P20_OVER = [b for b in P20 if CAL(b) > 200]
C.check(len(P20_OVER) * 2 > len(P20), 'most 20g+ protein bars are over 200 calories')
# Sugar alcohols inside the qualifying set
Q_SA = [b for b in Q if sa_any(b)]
C.check(0 < len(Q_SA) < N, 'some but not all qualifying bars use a sugar alcohol')
SA_SHARE = pct0(len(Q_SA), N)
# Grade share that clears the screen
CLR = [(gr, sum(1 for b in Q if b['score_band'] == gr), sum(1 for b in ALL if b['score_band'] == gr)) for gr in BAND_ORDER]
CR = {gr: round(100 * h / t) for gr, h, t in CLR}
A_ALL = sum(1 for b in ALL if b['score_band'] == 'A')
A_MISS_CAL = sum(1 for b in ALL if b['score_band'] == 'A' and 'cal' in SCREEN.fails[b['Key']])
A_MISS_P = sum(1 for b in ALL if b['score_band'] == 'A' and 'protein' in SCREEN.fails[b['Key']])
C.check(CR['A'] < 15, 'only a small share of A-grade bars clear the weight loss screen')
C.check(A_MISS_P > A_MISS_CAL, 'A-grade bars miss mostly on protein, not calories')

# Bar Finder parity: ?protein=15&cal=200&sugar=5&fiber=3 (port of app.js applyFilters sliders:
# a slider is skipped when the bar's field is empty)
FINDER_SLIDERS = (('Protein (g)', 15, 'min'), ('Calories', 200, 'max'), ('Sugars (g)', 5, 'max'), ('Dietary Fiber (g)', 3, 'min'))
def finder_match(b):
    for field, lim, d in FINDER_SLIDERS:
        v = num(b.get(field))
        if v is None:
            continue
        if (d == 'max' and v > lim) or (d == 'min' and v < lim):
            return False
    return True
C.check({b['Key'] for b in ALL if finder_match(b)} == {b['Key'] for b in Q},
        'Bar Finder protein/cal/sugar/fiber sliders return exactly the guide set')
FINDER_HREF = '/bar-finder?protein=15&cal=200&sugar=5&fiber=3'

def by_brand(brand, bars=ALL): return [b for b in bars if b['Brand Name'] == brand]
def yes(field): return lambda b: b.get(field) == 'Yes'

# ---------------------------------------------------------------------------
# Best 10 (spec v2)
# ---------------------------------------------------------------------------
WHEY_RX = re.compile(r'\bwhey\b[^,;()\[\]]*', re.I)
def whey(b): return bool(WHEY_RX.search(ingr(b)))
def whey_name(b): return WHEY_RX.search(ingr(b)).group(0).strip().lower()
def tie_tail(c): return f", and it wins the tie on {c['tie_on']}." if c['tied'] and c['tie_on'] != 'name' else "."
LOW_SUGAR = Slot('Lowest sugar', 'The least sugar among bars with no sugar alcohol (none in the ingredients and 0g on the '
                 'label), grade B or better, 10g+ protein. Skipping sugar alcohols keeps a bar from winning on a low sugar '
                 'line it reached with one.',
                 lambda E: [b for b in E if not sa_any(b)], lambda b: (SUG(b),) + tie_chain(b),
                 lambda b, c: (f"{fnum(SUG(b))}g sugar and no sugar alcohol, with {fnum(P(b))}g protein in {fnum(CAL(b))} "
                               f"calories, {c['tied']}the lowest sugar of any bar here without a sugar alcohol" + tie_tail(c)),
                 metric=SUG)
FIBER = Slot('Highest fiber', 'The most fiber, grade B or better, 10g+ protein.', lambda E: E,
             lambda b: (-FIB(b),) + tie_chain(b),
             lambda b, c: (f"{fnum(FIB(b))}g fiber, {c['tied']}the most of any bar here, with {fnum(P(b))}g protein in "
                           f"{fnum(CAL(b))} calories."),
             metric=FIB)
LOW_NET = Slot('Lowest net carbs', 'The fewest net carbs (total carbs minus fiber minus sugar alcohol), grade B or better, 10g+ protein.',
               lambda E: [b for b in E if NC(b) is not None], lambda b: (NC(b),) + tie_chain(b),
               lambda b, c: (f"{fnum(NC(b))}g net carbs, {c['tied']}the lowest of any bar here, with {fnum(P(b))}g protein" + tie_tail(c)),
               metric=NC)
SLOTS = [
    slot_best_overall(15),
    slot_cleanest(),
    slot_highest_protein(300),
    slot_protein_per_cal(12),
    slot_lowest_calorie(),
    slot_big_brand(),
    slot_subset('Best whey protein', 'Whey protein on the label.', whey,
                lambda b: f"Built on {whey_name(b)}, a complete dairy protein and "
                          + ("one of the protein sources our scoring rates highest." if 'isolate' in whey_name(b)
                             else "one of the protein sources our scoring rates near the top."), floor=15),
    LOW_SUGAR,
    slot_subset('Best dairy-free', 'Labeled dairy free by the brand.', yes('Dairy Free (Y/N)'),
                lambda b: 'Labeled dairy free by the brand.', floor=15),
    slot_subset('Best non-GMO', 'Labeled non-GMO by the brand.', yes('Non-GMO (Y/N)'),
                lambda b: 'Labeled non-GMO by the brand.', floor=15),
]
FALLBACKS = [FIBER, LOW_NET]
PICKS = pick_best10(Q, SLOTS, FALLBACKS, floor=10)
C.check(len(PICKS) == 10, 'ten Best 10 picks available')
C.check([s.label for s, *_ in PICKS] == [s.label for s in SLOTS], 'all ten planned slots filled without fallbacks')
C.check(not any(re.search(r'score \d|scored? \d', w) for _s, _b, w, _n in PICKS), 'no ingredient score printed in a pick')
PK = {s.label: b for s, b, _w, _n in PICKS}
C.check(not sa_any(PK['Lowest sugar']), 'the lowest sugar pick has no sugar alcohol')
PICKS_SA = [b for _s, b, _w, _n in PICKS if sa_any(b)]
B10_INTRO = ("Ten bars that clear all four weight loss checks, each the winner of one thing people shop for. Every pick has "
             "15g+ protein, 200 calories or less, 5g or less sugar, 3g+ fiber and an A or B ingredient grade, and no bar "
             "appears twice.")

# ---------------------------------------------------------------------------
# What it means
# ---------------------------------------------------------------------------
SA_Q_BRANDS = sorted({b['Brand Name'] for b in Q_SA}, key=str.lower)
CARDS = '\n'.join([
    v2_count_card_html('Over 200 calories', FAIL_BARS['cal'], NT,
                       'Plenty of bars sold as protein bars carry 250 to 400 calories, which is a small meal, not a snack.',
                       names=[]),
    v2_count_card_html('Under 15g protein', FAIL_BARS['protein'], NT,
                       'Protein is the most filling of the three macros. Under 15g, a bar is mostly carbs and fat.', names=[]),
    v2_count_card_html('Over 5g sugar', FAIL_BARS['sugar'], NT,
                       'Sugar adds calories without keeping you full. We set the line at 5g per bar.', names=[]),
    v2_count_card_html('Under 3g fiber', FAIL_BARS['fiber'], NT,
                       'Fiber slows digestion and helps a snack hold you over until the next meal.', names=[]),
])
MEANS = f'''
    <div class="section-inner">
      <h2 class="section-title">What makes a protein bar good for weight loss</h2>
      <div class="section-body">
        <p>Losing weight comes down to eating fewer calories than you burn, so a protein bar only helps if it replaces something heavier or keeps you from reaching for something else. That makes the useful question simple: how filling is it for its calories? We screened every bar for four things: 15g or more protein, 200 calories or less, 5g of sugar or less, and at least 3g of fiber.</p>
        <p>{of_db(N, NT)} bars pass all four. Here is how often each check catches a bar.</p>
      </div>
      <div class="callout-box">{DISCLAIMER}</div>
      <div class="score-grid" style="margin-top:1.5rem;">
{CARDS}
      </div>
      <h3 class="kt-h3">Sugar alcohols are allowed here</h3>
      <div class="section-body">
        <p>We don't exclude sugar alcohols on this page. They add few calories, and that is the point of this screen. But {len(Q_SA)} of the {N} bars that pass ({SA_SHARE}%) reach their low sugar number with one, and erythritol, maltitol and the like upset some people's stomachs. If they bother you, check the label or start from our <a href="/no-sugar-alcohols">no sugar alcohols guide</a>. Our Lowest sugar pick only considers bars without one.</p>
      </div>
      <h3 class="kt-h3">Weight loss doesn't screen on ingredient grade</h3>
      <div class="section-body">
        <p>The four checks are about calories and fullness, not what the bar is made of, so {LOW} of the {N} bars that pass grade C or below. Our A to F grade measures ingredient quality and is a separate question. Every bar in the Best 10 below grades A or B, and the list further down puts A and B bars first.</p>
      </div>
      <h3 class="kt-h3">A bar is still food</h3>
      <div class="section-body">
        <p>A 190-calorie bar that replaces a 400-calorie pastry helps. The same bar eaten on top of everything else doesn't. Bars here average {fnum(round(AVG_CAL))} calories, {fnum(round(AVG_P, 1))}g of protein and {fnum(round(AVG_FIB, 1))}g of fiber. Everyone's needs are different, and nothing on this page replaces advice from your doctor or a registered dietitian.</p>
      </div>
    </div>
'''

# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------
INSIGHTS = [
    ('Sugar is the most common miss.',
     f"{comma(FAIL['sugar'])} bars ({pct0(FAIL['sugar'], NT)}%) have more than 5g of sugar, ahead of protein "
     f"({pct0(FAIL['protein'], NT)}% under 15g), calories ({pct0(FAIL['cal'], NT)}% over 200) and fiber "
     f"({pct0(FAIL['fiber'], NT)}% under 3g). {comma(MULTI)} of the {comma(ND)} bars that fail miss more than one check."),
    ('Big protein usually means big calories.',
     f'{len(P20_OVER)} of the {len(P20)} bars with 20g+ protein ({pct0(len(P20_OVER), len(P20))}%) are over 200 calories. '
     'A high protein number on the wrapper says nothing about the calories it came with, so check both.'),
    ('Clean bars rarely fit the numbers.',
     f"Only {CR['A']}% of A-grade bars pass all four checks, and most of them miss on protein: {A_MISS_P} of the "
     f"{A_ALL} A-grade bars have under 15g. Ingredient quality and weight loss numbers are separate questions."),
]
FINDINGS = findings_v2_html(f'What we found screening {DB_PUBLIC} bars', INSIGHTS,
                            grade_share_chart_html(CLR, title='Share of bars that pass the weight loss screen, by ingredient grade',
                                                   note=f'Out of the {DB_PUBLIC} bars in our database. Passing means 15g+ protein, '
                                                        '200 calories or less, 5g or less sugar and 3g+ fiber.'))

# ---------------------------------------------------------------------------
# Brands that do it well + big brands
# ---------------------------------------------------------------------------
WELL = brands_well_rows(ALL, QF, n=8)
C.check(sum(r['big'] for r in WELL) >= 1 and sum(not r['big'] for r in WELL) >= 2, 'brands-well has a big and 2+ small brands')
def well_why(r):
    lead = (f"All {r['total']} flavors qualify" if r['q'] == r['total'] else
            f"{r['q']} of {r['total']} flavors {'qualifies' if r['q'] == 1 else 'qualify'}")
    gm = r['grades']
    grades = (f"graded {next(iter(gm))}" if r['q'] == 1 else
              f"all {next(iter(gm))} grade" if len(gm) == 1 else grade_mix_text(gm) + ' grade')
    bp = best_pick(r['qual'])
    return f"{lead}, {grades}. Best pick: {bp['Flavor Name']} ({bp['score_band']}, {fnum(P(bp))}g protein, {fnum(CAL(bp))} cal)."
BRANDS_WELL = brands_well_html(WELL, well_why, h2='Brands that do it well',
                               intro='Brands with at least 3 bars in our database, ranked by how much of their lineup passes '
                                     'all four checks and how well those bars grade.')

MISS_PHRASE = {'protein': 'less than 15g protein', 'cal': 'more than 200 calories', 'sugar': 'more than 5g sugar',
               'fiber': 'less than 3g fiber'}
def fail_reasons(disq):
    rs = [(MISS_PHRASE[k], sum(1 for b in disq if k in SCREEN.fails[b['Key']])) for k, _, _ in SCREEN.checks]
    rs.sort(key=lambda r: -r[1])
    return rs
def big_verdict(r):
    disq = [b for b in r['bars'] if not QF(b)]
    bp = best_pick(r['qual'])
    pick = f" Best pick: {bp['Flavor Name']} ({bp['score_band']}, {fnum(P(bp))}g protein, {fnum(CAL(bp))} cal)." if bp else ''
    if r['q'] == r['total']:
        return 'Every flavor qualifies.' + pick
    rs = fail_reasons(disq)
    every = [n for n, c in rs if c == len(disq)]
    main = every[0] if every else rs[0][0]
    if r['q'] == 0:
        return f"None qualify: every flavor has {main}." if every else f"None qualify. Most flavors have {main}."
    rest = (f"The other one has {main}." if len(disq) == 1 else f"The rest {'all' if every else 'mostly'} have {main}.")
    verb = 'qualifies' if r['q'] == 1 else 'qualify'
    return f"{'Only ' if r['q'] * 2 < r['total'] else ''}{r['q']} of {r['total']} {verb}. {rest}" + pick
BIG_HTML, BIG_ROWS = big_brands_html(
    ALL, QF, big_verdict, h2='How do the big brands fare for weight loss?',
    intro=('Every brand with national grocery, big-box or Costco distribution, with how many of its bars pass all four '
           'checks. Brand names link to our full reviews where we have one.'))

# ---------------------------------------------------------------------------
# Top 50 + Bar Finder CTA + criteria
# ---------------------------------------------------------------------------
T50 = top50_rows(Q, 50)
C.check(len(T50) == min(50, N), 'Top 50 length')
C.check([b['score_band'] for b in T50] == sorted((b['score_band'] for b in T50), key=BAND_ORDER.index), 'Top 50 is grade-first')
TOP50 = top50_html(T50, h2='Top 50 protein bars for weight loss',
                   intro='Ranked by ingredient grade first, then by protein per calorie. Tap any row for nutrition facts and '
                         'the full ingredient list.')
FINDER = finder_cta_html(N, FINDER_HREF, desc=('The Bar Finder opens with the same four limits as this page: 15g+ protein, 200 '
                                               'calories or less, 5g or less sugar, 3g+ fiber. Add your own filters for grade, '
                                               'brand, certifications, or ingredients to exclude.'))
CRITERIA = criteria_html(
    qualify_rule=('15g or more protein, 200 calories or less, 5g or less sugar, and 3g or more fiber. No grade check and no '
                  f'sugar alcohol check on the list itself. {comma(N)} of the {DB_PUBLIC} bars we track qualify.'),
    picks=PICKS)

# ---------------------------------------------------------------------------
# FAQ
# ---------------------------------------------------------------------------
def brand_faq(name):
    bars = by_brand(name)
    C.check(bars, f'{name} is in bars.js')
    q = [b for b in bars if QF(b)]
    disq = [b for b in bars if not QF(b)]
    miss = names_and(SCREEN.misses_mainly(disq)) if disq else ''
    if not disq:
        return f"By our screen, yes: all {len(bars)} tracked {name} flavors pass all four checks."
    if not q:
        return f"Not by our screen: none of the {len(bars)} tracked {name} flavors pass all four checks. They miss mainly on {miss}."
    verb = 'passes' if len(q) == 1 else 'pass'
    lead = 'Only' if len(q) * 2 < len(bars) else 'Mostly, by our screen:'
    grades = grade_mix_text(Counter_(b['score_band'] for b in q))
    return (f"{lead} {len(q)} of {len(bars)} tracked {name} flavors {verb} all four checks ({grades} grade): "
            f"{names_and(b['Flavor Name'] for b in q)}. The rest miss mainly on {miss}.")
BEST = PK['Best overall']
HP = PK['Highest protein']
FAQS = [
    ('What should I look for in a protein bar for weight loss?',
     'We are not doctors, but here is what we filtered on: at least 15g of protein, 200 calories or less, 5g of sugar or less, '
     'and at least 3g of fiber. Protein and fiber help a bar keep you full, and the calorie cap keeps it snack-sized. '
     f'{of_db(N, NT)} bars pass all four. For our Best 10 we also require an A or B ingredient grade.'),
    ('What is the best protein bar for weight loss?',
     f"By our rules, {full(BEST)}: {BEST['score_band']}-grade ingredients, {fnum(P(BEST))}g protein, {fnum(CAL(BEST))} calories, "
     f"{fnum(SUG(BEST))}g sugar and {fnum(FIB(BEST))}g fiber"
     + (f" (it uses a sugar alcohol, {fnum(SA(BEST))}g on the label)" if sa_any(BEST) else '') + '. '
     f"For the most protein, {full(HP)} has {fnum(P(HP))}g in {fnum(CAL(HP))} calories. Every bar in our Best 10 passes all "
     "four checks with an A or B grade."),
    ('Are protein bars good for weight loss?',
     'They can be, when a bar replaces a snack or a meal you would have eaten anyway and it is filling for its calories. Many '
     f"are not: {pct0(FAIL['cal'], NT)}% of the bars we track are over 200 calories, and the average bar has "
     f"{fnum(round(DB_AVG_CAL))}. A protein bar eaten on top of your usual meals adds calories like any other food."),
    ('Why did you set the limit at 200 calories?',
     'It keeps a bar in snack territory. At 250 to 400 calories a bar is closer to a small meal, which is fine when it '
     f'replaces one but not as an in-between snack. Bars on this list average {fnum(round(AVG_CAL))} calories.'),
    ('Why does fiber matter for weight loss?',
     'Fiber slows digestion, so a bar with protein and fiber keeps you full longer than one with the same calories from '
     f'sugar. We required at least 3g. Bars on this list average {fnum(round(AVG_FIB, 1))}g, and the top pick for fiber '
     f'in our database has 17g.'),
    ('Do sugar alcohols matter for weight loss?',
     'They add few calories, so we allow them here. But they can cause bloating and stomach upset in some people, and '
     f'{len(Q_SA)} of the {N} bars on this list ({SA_SHARE}%) use one. If they bother you, see our '
     '<a href="/no-sugar-alcohols">no sugar alcohols guide</a>.'),
    ('What does the ingredient grade mean on this page?',
     "Our A to F grade rates what a bar is made of: whole foods and quality protein at the top, heavily processed "
     "ingredients at the bottom. It isn't part of the weight loss screen, so "
     f"{LOW} of the {N} bars that pass grade C or below. Every bar in our Best 10 grades A or B."),
    ('Are Quest bars good for weight loss?', brand_faq('Quest')),
    ('Are Barebells good for weight loss?', brand_faq('Barebells')),
    ('How many protein bars in your database pass this screen?',
     f'Out of {DB_PUBLIC} bars in our database, {N} pass all four checks: 15g or more protein, 200 calories or less, 5g or '
     f'less sugar, and 3g or more fiber. That is about {pct0(N, NT)}% of the database, and {AB} of them grade A or B.'),
]

# ---------------------------------------------------------------------------
# Regions
# ---------------------------------------------------------------------------
H1 = 'The 10 Best Protein Bars for Weight Loss'
TITLE = f'10 Best Protein Bars for Weight Loss ({DB_PUBLIC} Checked)'
DESC = (f'Only {N} of {DB_PUBLIC} protein bars have 15g+ protein in 200 calories or less with low sugar and real fiber. '
        'Our 10 best for weight loss.')
OG_DESC = (f'We screened {DB_PUBLIC} protein bars for protein, calories, sugar and fiber. {comma(N)} pass all four. Here are '
           'the 10 best for weight loss, each picked by a published rule.')
C.check(len(DESC) <= 155, f'meta description under 155 characters ({len(DESC)})')
FAQS_PLAIN = [(q, plain_text(a)) for q, a in FAQS]
REGIONS = v2_head_regions(title=TITLE, h1=H1, desc=DESC, og_desc=OG_DESC, url=URL, about='Weight Loss',
                          published=PUBLISHED, faqs=FAQS_PLAIN, picks=PICKS)
EDITORIAL = f'  <section class="section off" id="what-it-means">{MEANS}  </section>'
HERO = (f'<h1 class="hero-title">{esc(H1)}</h1>\n'
        f'    <p class="hero-sub">A protein bar helps with weight loss when it is filling for its calories: enough protein and '
        f'fiber to hold you over, little sugar, and a size that fits a snack. We screened every bar for four things: 15g+ '
        f'protein, 200 calories or less, 5g or less sugar, and 3g+ fiber.</p>\n'
        f'    <p class="hero-sub">Of the {DB_PUBLIC} bars we track, {comma(N)} pass all four, about {pct0(N, NT)}%. Sugar '
        f'knocks out the most, and big protein usually comes with big calories: {pct0(len(P20_OVER), len(P20))}% of bars '
        f'with 20g+ protein are over 200 calories. {esc(DISCLAIMER)}</p>')
REGIONS += [
    ('hero', HERO),
    ('best10', best10_html(PICKS, h2='Best 10 protein bars for weight loss', intro=B10_INTRO)),
    ('editorial', EDITORIAL),
    ('findings', FINDINGS),
    ('brands-well', BRANDS_WELL),
    ('big-brands', BIG_HTML),
    ('top50', TOP50),
    ('finder-cta', FINDER),
    ('criteria', CRITERIA),
    ('faq', faq_items_html(FAQS)),
    ('author', byline_html()),
    ('explore-more', related_html([
        ('/high-protein-bars', 'High Protein Bars', 'The best bars with 20g or more protein, and the calories that come with it.'),
        ('/glp1-protein-bars', 'GLP-1 Protein Bars', 'A stricter screen for people on GLP-1 medications: no sugar alcohols, A or B grade.'),
        ('/no-sugar-alcohols', 'No Sugar Alcohols', 'Bars that skip maltitol, erythritol, and other sugar alcohols entirely.'),
    ])),
]

if __name__ == '__main__':
    C.stop_if_failed()
    page = build_guide_page_v2(PAGE, REGIONS, ALL, C, picks=PICKS)
    size = len(page.encode('utf-8'))
    faq_at = len(page[:page.find('<section class="guide-faq"')].encode('utf-8'))
    print(f'{PAGE}: {N} qualify ({AB} A/B), {ND} disqualified, {size:,} bytes, FAQ at byte {faq_at:,}')
    print(f'  fails: {FAIL}; P20 {len(P20)} over200 {len(P20_OVER)}; Q_SA {len(Q_SA)}; clear by grade {CR}; A miss P {A_MISS_P} cal {A_MISS_CAL} of {A_ALL}')
    for i, (s_, b, why, n) in enumerate(PICKS, 1):
        print(f'  {i:2d}. {s_.label}: {full(b)} ({b["score_band"]}) [pool {n}]')
        print(f'      {why}')
