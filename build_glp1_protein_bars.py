#!/usr/bin/env python3
"""Rebuild glp1-protein-bars.html from bars.js. GUIDE PAGE v2 ("Best 10").

Run from the repo root:  python3 build_glp1_protein_bars.py

Layout and every rule: claude/GUIDE_PAGE_SPEC_V2.md (locked 2026-09-29) and
the v2 section of kyb_guide_lib.py, built the same way as the other v2 guides
(closest reference: build_best_bars_for_diabetics.py, a macro screen with a
grade gate). The first run migrated the live v1 page to the v2 body (head, nav
and footer kept as deployed) and added the ItemList JSON-LD marker to the head;
later runs rewrite only the <!-- kyb:NAME --> regions. Every number, pick and
brand row comes from bars.js. Copy that depends on a fact is checked; if one
stops being true the build stops and lists it. Ingredient quality is shown and
ranked as a GRADE only.

Screen: GUIDE_FILTERS['glp1-protein-bars'] = protein >= 15, calories <= 200,
sugar <= 4, fiber >= 3, no sugar alcohol (0g on the label AND none named in
the ingredients, kyb_guide_lib.has_sugar_alcohol; decided 2026-09-24), A or B
grade. Keeps the required "We are not doctors or dietitians" line.
Bar Finder: /bar-finder?preset=glp1 (app.js PRESETS.glp1 is the same screen;
checked key for key below on every build).

Guide slots (picked 2026-09-30, Jeff asked for the best picks delivered without
a separate approval round): Best whey protein, Highest fiber, Lowest sugar,
Best plant-based. Fallbacks: Lowest net carbs, then Best gluten-free. Only 21
bars qualify, so every option for fiber runs through Julian Bakery Peanut
Butter (also on no-artificial-sweeteners and gluten-free); it stays because 17g
of fiber is the standout number for this audience.
"""
import re
from kyb_guide_lib import *

PAGE = 'glp1-protein-bars.html'
URL = 'https://knowyourbar.com/glp1-protein-bars'
PUBLISHED = '2026-07-23'
set_tie_seed('glp1-protein-bars')   # per-guide shuffle for exact ties (kyb_guide_lib, 2026-09-30)

ALL = load_bars()
QF = GUIDE_FILTERS['glp1-protein-bars']
Q = [b for b in ALL if QF(b)]
D = [b for b in ALL if not QF(b)]
N, ND, NT = len(Q), len(D), len(ALL)
BRANDS_ALL = len({b['Brand Name'] for b in ALL})
BRANDS_Q = len({b['Brand Name'] for b in Q})
GR = {g: sum(1 for b in Q if b.get('score_band') == g) for g in BAND_ORDER}
C = Claims()
NC = net_carbs
DISCLAIMER = ("We are not doctors or dietitians. These are the qualities we know people look for, so that's what we "
              "factored in.")
def sa_any(b): return SA(b) > 0 or has_sugar_alcohol(b)

SCREEN = Screen(ALL, [
    ('protein', 'protein', lambda b: P(b) < 15),
    ('cal', 'calories', lambda b: CAL(b) > 200),
    ('sugar', 'sugar', lambda b: SUG(b) > 4),
    ('fiber', 'fiber', lambda b: FIB(b) < 3),
    ('sa', 'sugar alcohol', sa_any),
    ('grade', 'ingredient grade', lambda b: b.get('score_band') not in ('A', 'B')),
])
FAIL = {k: SCREEN.count(k) for k, _, _ in SCREEN.checks}
FAIL_BARS = {k: [b for b in ALL if k in SCREEN.fails[b['Key']]] for k, _, _ in SCREEN.checks}
C.check(all(SCREEN.fails[b['Key']] for b in D) and not any(SCREEN.fails[b['Key']] for b in Q), 'the six checks match the GLP-1 filter')
C.check(GR['A'] + GR['B'] == N, 'every qualifying bar is A or B')
AVG_CAL, AVG_FIB, AVG_P = avg(Q, 'Calories'), avg(Q, 'Dietary Fiber (g)'), avg(Q, 'Protein (g)')
AVG_P100 = sum(p100(b) or 0 for b in Q) / N
C.check(AVG_FIB > 5, 'qualifying fiber average comfortably above 3g')
C.check(FAIL['sugar'] > max(FAIL['protein'], FAIL['cal'], FAIL['fiber']), 'sugar is the toughest macro check')
MACRO = [b for b in ALL if not ({'protein', 'cal', 'sugar', 'fiber'} & set(SCREEN.fails[b['Key']]))]
MACRO_SA = sum(1 for b in MACRO if sa_any(b))
MACRO_LOW = sum(1 for b in MACRO if b.get('score_band') not in ('A', 'B'))
C.check(len(MACRO) > 4 * N and MACRO_SA > len(MACRO) / 2 and MACRO_LOW > len(MACRO) / 2,
        'many bars meet the four macro checks, and most of those have a sugar alcohol or a C-or-below grade')
C.check(BRANDS_Q * 10 < BRANDS_ALL, 'fewer than 1 in 10 tracked brands has a qualifying flavor')

# Bar Finder parity: ?preset=glp1 (port of app.js PRESETS.glp1.apply + hasSugarAlcohol)
def finder_match(b):
    prot, cal, sug, fib, sa = (num(b.get(k)) for k in ('Protein (g)', 'Calories', 'Sugars (g)', 'Dietary Fiber (g)', 'Sugar Alcohol (g)'))
    if not prot or not cal or sug is None or fib is None:
        return False
    if sa is not None and sa > 0:
        return False
    if has_sugar_alcohol(b):
        return False
    return prot >= 15 and cal <= 200 and sug <= 4 and fib >= 3 and b.get('score_band') in ('A', 'B')
C.check({b['Key'] for b in ALL if finder_match(b)} == {b['Key'] for b in Q}, 'Bar Finder preset=glp1 returns exactly the guide set')
FINDER_HREF = '/bar-finder?preset=glp1'

def link(href, text): return f'<a href="{href}">{text}</a>'
def by_brand(brand, bars=ALL): return [b for b in bars if b['Brand Name'] == brand]
def yes(field): return lambda b: b.get(field) == 'Yes'
def g(x): return f'{fnum(round(x, 1))}g'

# ---------------------------------------------------------------------------
# Best 10 (spec v2)
# ---------------------------------------------------------------------------
WHEY_RX = re.compile(r'\bwhey\b[^,;()\[\]]*', re.I)
def whey(b): return bool(WHEY_RX.search(ingr(b)))
def whey_name(b): return WHEY_RX.search(ingr(b)).group(0).strip().lower()
def nc_why(b, c):
    sa = SA(b)
    parts = f"{fnum(num(b.get('Total Carbohydrates (g)')))}g carbs minus {fnum(FIB(b))}g fiber" + (f" and {fnum(sa)}g sugar alcohol" if sa else '')
    return (f"{fnum(NC(b))}g net carbs ({parts}), {c['tied']}the lowest of any bar here, with {fnum(P(b))}g protein"
            + (f", and it wins the tie on {c['tie_on']}." if c['tied'] and c['tie_on'] != 'name' else "."))
LOW_NET = Slot('Lowest net carbs', 'The fewest net carbs (total carbs minus fiber minus sugar alcohol), grade B or better, 15g+ protein.',
               lambda E: [b for b in E if NC(b) is not None], lambda b: (NC(b),) + tie_chain(b), nc_why, metric=NC)
LOW_SUGAR = Slot('Lowest sugar', 'The least sugar, grade B or better, 15g+ protein (no bar here has a sugar alcohol).',
                 lambda E: E, lambda b: (SUG(b),) + tie_chain(b),
                 lambda b, c: (f"{fnum(SUG(b))}g sugar with {fnum(P(b))}g protein in {fnum(CAL(b))} calories, {c['tied']}the "
                               "lowest sugar of any bar here" + (f", and it wins the tie on {c['tie_on']}." if c['tied'] and c['tie_on'] != 'name' else ".")),
                 metric=SUG)
FIBER = Slot('Highest fiber', 'The most fiber, grade B or better, 15g+ protein.', lambda E: E,
             lambda b: (-FIB(b),) + tie_chain(b),
             lambda b, c: (f"{fnum(FIB(b))}g fiber, {c['tied']}the most of any bar here, with {fnum(P(b))}g protein in "
                           f"{fnum(CAL(b))} calories. Fiber slows digestion and helps a small snack keep you full."),
             metric=FIB)
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
    FIBER,
    LOW_SUGAR,
    slot_subset('Best plant-based', 'Labeled vegan by the brand.', yes('Vegan (Y/N)'),
                lambda b: 'Labeled vegan, so the protein comes from plants, not whey, milk or egg.', floor=15),
]
FALLBACKS = [
    LOW_NET,
    slot_subset('Best gluten-free', 'Labeled gluten free by the brand.', yes('Gluten Free (Y/N)'),
                lambda b: 'Labeled gluten free by the brand.', floor=15),
]
PICKS = pick_best10(Q, SLOTS, FALLBACKS, floor=15)
C.check(len(PICKS) == 10, 'ten Best 10 picks available')
C.check([s.label for s, *_ in PICKS] == [s.label for s in SLOTS], 'all ten planned slots filled without fallbacks')
C.check(not any(re.search(r'score \d|scored? \d', w) for _s, _b, w, _n in PICKS), 'no ingredient score printed in a pick')
PK = {s.label: b for s, b, _w, _n in PICKS}
C.check(has_tag(PK['Best whey protein'], 'Quality Protein Source'), 'the whey pick carries the Quality Protein Source tag')
C.check(not WHEY_RX.search(ingr(PK['Best plant-based'])) and 'milk' not in ingr(PK['Best plant-based']).lower(),
        'the plant-based pick names no whey or milk')
B10_INTRO = ("Ten bars that clear our full GLP-1 screen, each the winner of one thing people shop for. Every pick has 15g+ "
             "protein, 200 calories or less, 4g or less sugar, 3g+ fiber, no sugar alcohol and an A or B ingredient grade, "
             "and no bar appears twice.")

# ---------------------------------------------------------------------------
# What we screened for (carried over from v1, trimmed)
# ---------------------------------------------------------------------------
SA_BRANDS = sorted({b['Brand Name'] for b in FAIL_BARS['sa']}, key=str.lower)
CARDS = '\n'.join([
    v2_count_card_html('Protein under 15g', FAIL_BARS['protein'], NT,
                       'Less food volume means every bite needs to work harder. We required at least 15g of protein per bar.', names=[]),
    v2_count_card_html('Calories over 200', FAIL_BARS['cal'], NT,
                       'A reduced appetite means a smaller calorie budget overall. We capped this list at 200 calories.', names=[]),
    v2_count_card_html('Sugar over 4g', FAIL_BARS['sugar'], NT,
                       'Sugar spikes can add to the nausea and GI discomfort some people already feel on GLP-1 medications.', names=[]),
    v2_count_card_html('Contains a sugar alcohol', FAIL_BARS['sa'], NT,
                       'Sugar alcohols are a frequent trigger for bloating and GI discomfort, so we excluded every bar that lists '
                       'one, in the ingredients or as grams on the label.', names=SA_BRANDS),
])
MEANS = f'''
    <div class="section-inner">
      <h2 class="section-title">What "GLP-1 friendly" means on this page</h2>
      <div class="section-body">
        <p>People on GLP-1 medications usually care about three things first: enough protein to make a small amount of food count, calories low enough to fit a reduced appetite without crowding out real meals, and low sugar. We added three more checks on top: at least 3g of fiber for fullness, no sugar alcohols at all (GI tolerance is a common concern on these medications), and an A or B ingredient grade.</p>
        <p>{of_db(N, NT)} bars pass all six. Here is how often the checks catch a bar.</p>
      </div>
      <div class="callout-box">{DISCLAIMER}</div>
      <div class="score-grid" style="margin-top:1.5rem;">
{CARDS}
      </div>
      <h3 class="kt-h3">Why no sugar alcohols at all</h3>
      <div class="section-body">
        <p>Our keto and diabetics guides allow low-glycemic sugar alcohols like erythritol and only exclude maltitol. This guide is stricter because the question here is digestive comfort, not just blood sugar. We check the ingredient list as well as the gram line, since many labels name a sugar alcohol but declare 0g. IMO (isomalto-oligosaccharides) counts too.</p>
      </div>
      <h3 class="kt-h3">Why protein per calorie matters here</h3>
      <div class="section-body">
        <p>Protein per 100 calories lets you compare bars of different sizes on equal footing. A bar with 20g of protein at 250 calories is less efficient than one with 15g at 150 calories, even though the first has more total protein. Bars here average {fnum(round(AVG_P100, 1))}g of protein per 100 calories and {fnum(round(AVG_CAL))} calories.</p>
        <p>Everyone on these medications has different tolerances. Everything on this page is a starting filter built from label data, not a substitute for a conversation with your doctor or a registered dietitian about what fits your treatment plan.</p>
      </div>
    </div>
'''

# ---------------------------------------------------------------------------
# Findings: three data findings + one chart
# ---------------------------------------------------------------------------
SA_ROWS = [(gr, sum(1 for b in ALL if b['score_band'] == gr and sa_any(b)), sum(1 for b in ALL if b['score_band'] == gr))
           for gr in BAND_ORDER]
SR = {gr: round(100 * h / t) for gr, h, t in SA_ROWS}
C.check(SR['A'] <= SR['B'] <= SR['C'] <= SR['D'] <= SR['F'] and SR['A'] < SR['F'],
        'sugar alcohol share never falls with a step down in grade, and F is well above A')
INSIGHTS = [
    ('The macros aren\'t the hard part.',
     f'{comma(len(MACRO))} bars meet the protein, calorie, sugar and fiber checks. {MACRO_SA} of those contain a sugar alcohol '
     f'and {MACRO_LOW} grade C or below, which leaves {N}.'),
    ('Sugar is the toughest macro check.',
     f"{comma(FAIL['sugar'])} bars ({pct0(FAIL['sugar'], NT)}%) fail on sugar, more than on protein ({pct0(FAIL['protein'], NT)}%), "
     f"calories ({pct0(FAIL['cal'], NT)}%) or fiber ({pct0(FAIL['fiber'], NT)}%)."),
    ('Few brands make the cut.',
     f'Only {BRANDS_Q} of the {BRANDS_ALL} brands we track have a flavor that clears all six checks, so the brand on the '
     'wrapper tells you little. Check the specific flavor.'),
]
FINDINGS = findings_v2_html(f'What we found screening {DB_PUBLIC} bars', INSIGHTS,
                            grade_share_chart_html(SA_ROWS, title='Share of bars with a sugar alcohol, by ingredient grade',
                                                   note=f'Out of the {DB_PUBLIC} bars in our database. Counts a sugar alcohol in '
                                                        'the ingredients (including IMO) or on the label.'))

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
                               intro='Brands with at least 3 bars in our database, ranked by how much of their lineup clears '
                                     'all six checks and how well those bars grade.')

MISS_PHRASE = {'protein': 'less than 15g protein', 'cal': 'more than 200 calories', 'sugar': 'more than 4g sugar',
               'fiber': 'less than 3g fiber', 'sa': 'a sugar alcohol', 'grade': 'a C-or-below grade'}
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
    ALL, QF, big_verdict, h2='How do the big brands fare for GLP-1?',
    intro=('Every brand with national grocery, big-box or Costco distribution, with how many of its bars pass all six '
           'checks. Brand names link to our full reviews where we have one.'))

# ---------------------------------------------------------------------------
# All qualifying bars (fewer than 50) + Bar Finder CTA + criteria
# ---------------------------------------------------------------------------
T50 = top50_rows(Q, 50)
C.check(len(T50) == N and N < 50, 'fewer than 50 bars qualify, so the list shows all of them')
TOP50 = top50_html(T50, h2=f'All {comma(N)} GLP-1 friendly protein bars',
                   intro='Ranked by ingredient grade first, then by protein per calorie. Tap any row for nutrition facts and '
                         'the full ingredient list.')
FINDER = finder_cta_html(N, FINDER_HREF, desc=('The Bar Finder opens with its GLP-1 Friendly filter, the same six checks as this '
                                               'page. Add your own filters for brand, certifications, or ingredients to exclude.'))
CRITERIA = criteria_html(
    qualify_rule=('15g or more protein, 200 calories or less, 4g or less sugar, 3g or more fiber, no sugar alcohol (0g on the '
                  'label and none named in the ingredients, IMO included), and an A or B ingredient grade. '
                  f'{comma(N)} of the {DB_PUBLIC} bars we track qualify.'),
    picks=PICKS)

# ---------------------------------------------------------------------------
# FAQ (answers may hold links; JSON-LD gets the plain text)
# ---------------------------------------------------------------------------
def brand_faq(name):
    bars = by_brand(name)
    C.check(bars, f'{name} is in bars.js')
    q = [b for b in bars if QF(b)]
    disq = [b for b in bars if not QF(b)]
    if not disq:
        return f"By our screen, yes: all {len(bars)} tracked {name} flavors clear all six criteria."
    miss = names_and(SCREEN.misses_mainly(disq))
    if not q:
        return f"Not by our screen: none of the {len(bars)} tracked {name} flavors clear all six criteria. They miss mainly on {miss}."
    verb = 'clears' if len(q) == 1 else 'clear'
    lead = 'Only' if len(q) * 2 < len(bars) else 'Mostly, by our screen:'
    return (f"{lead} {len(q)} of {len(bars)} tracked {name} flavors {verb} all six criteria: {names_and(b['Flavor Name'] for b in q)}. "
            f"The rest miss mainly on {miss}.")
BEST = PK['Best overall']
FAQS = [
    ("What should I look for in a protein bar if I'm on a GLP-1 medication?",
     'We are not doctors, but here is what we filtered on: at least 15g of protein, 200 calories or less, 4g of sugar or less, '
     'at least 3g of fiber, no sugar alcohol, and an A or B ingredient quality grade. Appetite suppression from '
     'GLP-1 medications means less food volume overall, so every bite needs to carry more protein relative to its size. '
     f'{of_db(N, NT)} bars clear all six.'),
    ('What is the best protein bar for GLP-1?',
     f"By our rules, {full(BEST)}: {BEST['score_band']}-grade ingredients, {fnum(P(BEST))}g protein, {fnum(CAL(BEST))} calories, "
     f"{fnum(SUG(BEST))}g sugar and {fnum(FIB(BEST))}g fiber. For the most protein, {full(PK['Highest protein'])} has "
     f"{fnum(P(PK['Highest protein']))}g in {fnum(CAL(PK['Highest protein']))} calories. Every bar in our Best 10 clears all six "
     "checks, and the right one depends on what you tolerate best."),
    ('Why does calorie count matter more on GLP-1 medications?',
     "Reduced appetite means a smaller daily calorie budget, so a snack that eats up 300 to 400 calories can crowd out an entire "
     "meal's worth of nutrition. We capped this list at 200 calories per bar so the protein-to-calorie ratio stays favorable "
     f'even when you can only manage a small amount of food. Qualifying bars average {fnum(round(AVG_CAL))} calories.'),
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
     'GLP-1 suitability. A bar can earn an A on ingredient quality and still not fit the macro profile people on GLP-1 '
     'medications look for, or vice versa. We use it as one of the six filters here, requiring an A or B, but the core of the '
     'screen is protein, calories, sugar, fiber, and the sugar alcohol exclusion.'),
    ('Is NuGo good for GLP-1?', brand_faq('NuGo')),
    ('Is Promix good for GLP-1?', brand_faq('Promix')),
    ('How many protein bars in your database qualify for this list?',
     f'Out of {DB_PUBLIC} bars in our database, {N} meet all six criteria: 15g or more protein, 200 calories or less, 4g or '
     'less sugar, 3g or more fiber, no sugar alcohol, and an A or B ingredient grade. That is about '
     f'{pct0(N, NT)}% of the full database.'),
]

# ---------------------------------------------------------------------------
# Regions
# ---------------------------------------------------------------------------
H1 = 'The 10 Best Protein Bars for GLP-1'
TITLE = f'10 Best Protein Bars for GLP-1 ({DB_PUBLIC} Checked)'
DESC = (f'Only {N} of {DB_PUBLIC} protein bars pass our GLP-1 screen: 15g+ protein, 200 calories or less, low sugar, no '
        'sugar alcohol. Our 10 best.')
OG_DESC = (f'We screened {DB_PUBLIC} protein bars for protein, calories, sugar, fiber, sugar alcohols and ingredient grade. '
           f'{comma(N)} pass all six. Here are the 10 best, each picked by a published rule.')
C.check(len(DESC) <= 155, f'meta description under 155 characters ({len(DESC)})')
FAQS_PLAIN = [(q, plain_text(a)) for q, a in FAQS]
REGIONS = v2_head_regions(title=TITLE, h1=H1, desc=DESC, og_desc=OG_DESC, url=URL, about='GLP-1 Medication Eating Guide',
                          published=PUBLISHED, faqs=FAQS_PLAIN, picks=PICKS)
EDITORIAL = f'  <section class="section off" id="what-it-means">{MEANS}  </section>'
HERO = (f'<h1 class="hero-title">{esc(H1)}</h1>\n'
        f'    <p class="hero-sub">GLP-1 medications shrink your appetite, so a snack has to deliver real protein in a small, '
        f'easy-to-tolerate package. We screened every bar for six things people on these medications look for: 15g+ protein, '
        f'200 calories or less, 4g or less sugar, 3g+ fiber, no sugar alcohols, and an A or B ingredient grade.</p>\n'
        f'    <p class="hero-sub">Of the {DB_PUBLIC} bars we track, only {comma(N)} pass all six, about {pct0(N, NT)}%. '
        f'{comma(len(MACRO))} bars hit the protein, calorie, sugar and fiber numbers, but most of those use a sugar '
        f'alcohol or grade C or below. {esc(DISCLAIMER)}</p>')
REGIONS += [
    ('hero', HERO),
    ('best10', best10_html(PICKS, h2='Best 10 protein bars for GLP-1', intro=B10_INTRO)),
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
        ('/best-bars-for-diabetics', 'Best Bars for Diabetics', 'Screened for sugar, net carbs, fiber, protein, grade, and maltitol.'),
        ('/keto-protein-bars', 'Keto Protein Bars', 'Low net carb bars with enough fat to fit a keto day.'),
        ('/no-sugar-alcohols', 'No Sugar Alcohols', 'Bars that skip maltitol, erythritol, and other sugar alcohols entirely.'),
    ])),
]

# One-time head fix on migration: the v1 page had no ItemList region (the lib
# always emits one). Literal insert after the FAQPage region; idempotent.
ITEMLIST_MARK = ('<!-- /kyb:jsonld-faq -->\n  <!-- JSON-LD: ItemList (top picks) -->\n  <!-- kyb:jsonld-itemlist -->\n'
                 '<!-- /kyb:jsonld-itemlist -->\n')
def ensure_itemlist_marker(path):
    page = open(path, encoding='utf-8').read()
    if '<!-- kyb:jsonld-itemlist -->' in page:
        return
    if page.count('<!-- /kyb:jsonld-faq -->\n') != 1:
        raise SystemExit('ERROR: kyb:jsonld-faq end marker missing or duplicated')
    open(path, 'w', encoding='utf-8').write(page.replace('<!-- /kyb:jsonld-faq -->\n', ITEMLIST_MARK, 1))

if __name__ == '__main__':
    C.stop_if_failed()
    ensure_itemlist_marker(PAGE)
    page = build_guide_page_v2(PAGE, REGIONS, ALL, C, picks=PICKS)
    size = len(page.encode('utf-8'))
    faq_at = len(page[:page.find('<section class="guide-faq"')].encode('utf-8'))
    print(f'{PAGE}: {N} qualify, {ND} disqualified, {size:,} bytes, FAQ at byte {faq_at:,}')
    for i, (s_, b, why, n) in enumerate(PICKS, 1):
        print(f'  {i:2d}. {s_.label}: {full(b)} ({b["score_band"]}) [pool {n}]')
        print(f'      {why}')
