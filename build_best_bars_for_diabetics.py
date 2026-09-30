#!/usr/bin/env python3
"""Rebuild best-bars-for-diabetics.html from bars.js. GUIDE PAGE v2 ("Best 10").

Run from the repo root:  python3 build_best_bars_for_diabetics.py

Layout and every rule: claude/GUIDE_PAGE_SPEC_V2.md (locked 2026-09-29) and
the v2 section of kyb_guide_lib.py, built the same way as the other v2 guides
(closest reference: build_clean_protein_bars.py, a multi-condition screen). The
first run migrated the live v1 page to the v2 body (head, nav and footer kept
as deployed) and added the ItemList JSON-LD marker to the head; later runs
rewrite only the <!-- kyb:NAME --> regions. Every number, pick and brand row
comes from bars.js. Copy that depends on a fact is checked; if one stops being
true the build stops and lists it. Ingredient quality is shown and ranked as a
GRADE only.

Screen: GUIDE_FILTERS['best-bars-for-diabetics'] = sugar <= 5, net carbs <= 10
(carbs - fiber - sugar alcohol), fiber >= 5, protein >= 10, A or B grade, no
maltitol family. Keeps the required "We are not doctors or dietitians" line.
Bar Finder: /bar-finder?grade=A,B&protein=10&sugar=5&fiber=5&netcarbs=10&excl=
maltitol,polyglycitol,hydrogenated starch hydrolysate. No preset matches; the
slider params (app.js readURLParams) plus grade and excl reproduce the guide
set key for key. Checked below on every build.

Guide slots (locked with Jeff 2026-09-30): Lowest net carbs, Lowest sugar (no
sugar alcohol), Best whey protein, Best soy-free. Fallbacks: Best gluten-free,
then Highest fiber. Chosen so none of the four guide picks repeat a pick from
the five earlier v2 guides.
"""
import re
from kyb_guide_lib import *

PAGE = 'best-bars-for-diabetics.html'
URL = 'https://knowyourbar.com/best-bars-for-diabetics'
PUBLISHED = '2026-04-29'
set_tie_seed('best-bars-for-diabetics')   # per-guide shuffle for exact ties (kyb_guide_lib, 2026-09-30)

ALL = load_bars()
QF = GUIDE_FILTERS['best-bars-for-diabetics']
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

SCREEN = Screen(ALL, [
    ('sugar', 'sugar', lambda b: SUG(b) > 5),
    ('nc', 'net carbs', lambda b: NC(b) is None or NC(b) > 10),
    ('fiber', 'fiber', lambda b: FIB(b) < 5),
    ('protein', 'protein', lambda b: P(b) < 10),
    ('grade', 'ingredient grade', lambda b: b.get('score_band') not in ('A', 'B')),
    ('maltitol', 'maltitol or a related sweetener', has_maltitol_family),
])
FAIL = {k: SCREEN.count(k) for k, _, _ in SCREEN.checks}
FAIL_BARS = {k: [b for b in ALL if k in SCREEN.fails[b['Key']]] for k, _, _ in SCREEN.checks}
MULTI = SCREEN.multi(D)
SINGLE = ND - MULTI
C.check(all(SCREEN.fails[b['Key']] for b in D) and not any(SCREEN.fails[b['Key']] for b in Q), 'the six checks match the diabetics filter')
C.check(GR['A'] + GR['B'] == N, 'every qualifying bar is A or B')
LOWS = [b for b in ALL if SUG(b) <= 1]
LOWS_M = pct0(sum(1 for b in LOWS if has_maltitol_family(b)), len(LOWS))
AVG_FIB = avg(Q, 'Dietary Fiber (g)')
C.check(AVG_FIB > 7, 'qualifying fiber average is well above 5g')
C.check(FAIL['nc'] > FAIL['sugar'], 'net carbs catches more bars than sugar')
C.check(MULTI > SINGLE, 'most disqualified bars fail more than one check')
C.check(FAIL['nc'] == max(FAIL.values()), 'net carbs stops more bars than any other check')

# Bar Finder parity: grade=A,B + sliders protein/sugar/fiber/netcarbs + excl (app.js applyFilters)
FINDER_EXCL = ['maltitol', 'polyglycitol', 'hydrogenated starch hydrolysate']
def finder_match(b):
    if b.get('score_band') not in ('A', 'B'):
        return False
    for field, lim, d in (('Protein (g)', 10, 'min'), ('Sugars (g)', 5, 'max'), ('Dietary Fiber (g)', 5, 'min')):
        v = num(b.get(field))
        if v is None:
            continue   # app.js skips a slider when the field is empty
        if (d == 'max' and v > lim) or (d == 'min' and v < lim):
            return False
    nc = (num(b.get('Total Carbohydrates (g)')) or 0) - (num(b.get('Dietary Fiber (g)')) or 0) - (num(b.get('Sugar Alcohol (g)')) or 0)
    if nc > 10:
        return False
    t = (b.get('Ingredients') or '').lower()
    return not any(e in t for e in FINDER_EXCL)
C.check({b['Key'] for b in ALL if finder_match(b)} == {b['Key'] for b in Q},
        'Bar Finder grade + protein/sugar/fiber/netcarbs sliders + maltitol-family excl returns exactly the guide set')
FINDER_HREF = ('/bar-finder?grade=A,B&protein=10&sugar=5&fiber=5&netcarbs=10'
               '&excl=maltitol,polyglycitol,hydrogenated%20starch%20hydrolysate')

def link(href, text): return f'<a href="{href}">{text}</a>'
def by_brand(brand, bars=ALL): return [b for b in bars if b['Brand Name'] == brand]
def yes(field): return lambda b: b.get(field) == 'Yes'
def g(x): return f'{fnum(round(x, 1))}g'
def imo(b): return bool(IMO_RX.search(ingr(b)))

# ---------------------------------------------------------------------------
# Best 10 (spec v2; guide slots locked with Jeff 2026-09-30)
# ---------------------------------------------------------------------------
WHEY_RX = re.compile(r'\bwhey\b[^,;()\[\]]*', re.I)
def whey(b): return bool(WHEY_RX.search(ingr(b)))
def whey_name(b): return WHEY_RX.search(ingr(b)).group(0).strip().lower()
SOY_RX = re.compile(r'\bsoy|soybean', re.I)
def nc_why(b, c):
    sa = SA(b)
    parts = f"{fnum(num(b.get('Total Carbohydrates (g)')))}g carbs minus {fnum(FIB(b))}g fiber" + (f" and {fnum(sa)}g sugar alcohol" if sa else '')
    return (f"{fnum(NC(b))}g net carbs ({parts}), {c['tied']}the lowest of any bar here, with {fnum(P(b))}g protein"
            + (f", and it wins the tie on {c['tie_on']}." if c['tied'] and c['tie_on'] != 'name' else "."))
LOW_NET = Slot('Lowest net carbs', 'The fewest net carbs (total carbs minus fiber minus sugar alcohol), grade B or better, 10g+ protein.',
               lambda E: [b for b in E if NC(b) is not None], lambda b: (NC(b),) + tie_chain(b), nc_why, metric=NC)
LOW_SUGAR = Slot('Lowest sugar', 'The least sugar among bars with no sugar alcohol, grade B or better, 10g+ protein.',
                 lambda E: [b for b in E if not has_sugar_alcohol(b)], lambda b: (SUG(b),) + tie_chain(b),
                 lambda b, c: (f"{fnum(SUG(b))}g sugar with {fnum(P(b))}g protein and no sugar alcohol, {c['tied']}the lowest "
                               "sugar of any bar here without one" + (f", and it wins the tie on {c['tie_on']}." if c['tied'] and c['tie_on'] != 'name' else ".")),
                 metric=SUG)
SLOTS = [
    slot_best_overall(15),
    slot_cleanest(),
    slot_highest_protein(300),
    slot_protein_per_cal(12),
    slot_lowest_calorie(),
    slot_big_brand(),
    LOW_NET,
    LOW_SUGAR,
    slot_subset('Best whey protein', 'Whey protein on the label.', whey,
                lambda b: f"Built on {whey_name(b)}, a complete dairy protein and "
                          + ("one of the protein sources our scoring rates highest." if 'isolate' in whey_name(b)
                             else "one of the protein sources our scoring rates near the top.")),
    slot_subset('Best soy-free', 'Labeled soy free by the brand.', yes('Soy Free (Y/N)'),
                lambda b: 'Labeled soy free, with no soy protein, soy lecithin or soybean oil on the label.'),
]
FALLBACKS = [
    slot_subset('Best gluten-free', 'Labeled gluten free by the brand.', yes('Gluten Free (Y/N)'),
                lambda b: 'Labeled gluten free by the brand.'),
    slot_highest_fiber(),
]
PICKS = pick_best10(Q, SLOTS, FALLBACKS)
C.check(len(PICKS) == 10, 'ten Best 10 picks available')
C.check([s.label for s, *_ in PICKS] == [s.label for s in SLOTS], 'all ten planned slots filled without fallbacks')
C.check(not any(re.search(r'score \d|scored? \d', w) for _s, _b, w, _n in PICKS), 'no ingredient score printed in a pick')
PK = {s.label: b for s, b, _w, _n in PICKS}
C.check(has_tag(PK['Best whey protein'], 'Quality Protein Source'), 'the whey pick carries the Quality Protein Source tag')
C.check(not SOY_RX.search(ingr(PK['Best soy-free'])), 'the soy-free pick names no soy ingredient')
C.check(not has_sugar_alcohol(PK['Lowest sugar']), 'the lowest-sugar pick has no sugar alcohol')
B10_INTRO = ("Ten bars that clear our full blood sugar screen, each the winner of one thing people shop for. Every pick has "
             "5g or less sugar, 10g or less net carbs, 5g+ fiber, 10g+ protein, an A or B ingredient grade and no maltitol, "
             "and no bar appears twice.")
CARD_MACROS = [('Protein', lambda b: f'{fnum(P(b))}g'), ('Sugar', lambda b: f'{fnum(SUG(b))}g'),
               ('Net carbs', lambda b: f'{fnum(NC(b))}g'), ('Fiber', lambda b: f'{fnum(FIB(b))}g')]

# ---------------------------------------------------------------------------
# What we screened for (carried over from v1, trimmed) + gotchas
# ---------------------------------------------------------------------------
IMO_Q = [b for b in Q if imo(b)]
IMO_PICKS = [b for _s, b, _w, _n in PICKS if imo(b)]
IMO_BRANDS = sorted({b['Brand Name'] for b in IMO_Q}, key=str.lower)
C.check(IMO_Q and IMO_PICKS, 'some qualifying bars and Best 10 picks list IMO')
MALT_BRANDS = sorted({b['Brand Name'] for b in FAIL_BARS['maltitol']}, key=str.lower)
CARDS = '\n'.join([
    v2_count_card_html('Sugar over 5g', FAIL_BARS['sugar'], NT,
                       'Sugar hits the bloodstream fast. We capped it at 5g, tighter than most "low sugar" marketing claims.', names=[]),
    v2_count_card_html('Net carbs over 10g', FAIL_BARS['nc'], NT,
                       'Net carbs (total carbs minus fiber minus sugar alcohols) is the number that best predicts blood sugar '
                       'impact, and it is rarely printed on the label.', names=[]),
    v2_count_card_html('Fiber under 5g', FAIL_BARS['fiber'], NT,
                       'Fiber slows digestion, which flattens the glucose spike from whatever carbs remain. We required at '
                       'least 5g.', names=[]),
    v2_count_card_html('Contains maltitol or similar', FAIL_BARS['maltitol'], NT,
                       'Maltitol and its syrupy relatives (maltitol syrup, polyglycitol, hydrogenated starch hydrolysates) '
                       'have a glycemic index close to half of table sugar, but labeling rules let brands leave them off the '
                       f'sugar line. {LOWS_M}% of bars with 1g or less of listed sugar still contain one.', names=MALT_BRANDS),
])
def imo_list():
    ps = [full(b) for b in IMO_PICKS]
    return (f"{num_word(len(ps)).capitalize()} of our Best 10 picks list it ({names_and(ps)})" if len(ps) > 1
            else f"One of our Best 10 picks lists it ({ps[0]})")
MEANS = f'''
    <div class="section-inner">
      <h2 class="section-title">What "good for diabetics" means on this page</h2>
      <div class="section-body">
        <p>Search for the best protein bars for diabetics and most answers start and end with the sugar line on the label. That number matters, but it isn't the one that best predicts what happens to your blood sugar an hour later. Net carbs (total carbs minus fiber minus sugar alcohols) accounts for the carbs a sugar-free label doesn't have to mention: a bar with 2g of sugar but 22g of net carbs still delivers a real glucose load. Fiber slows how fast that load hits your bloodstream, and protein does the same by slowing digestion.</p>
        <p>So every bar here has to pass six checks: 5g or less sugar, 10g or less net carbs, 5g or more fiber, 10g or more protein, an A or B ingredient grade, and no maltitol or its close relatives. {of_db(N, NT)} bars pass all six. Here is how often the four blood sugar checks catch a bar.</p>
      </div>
      <div class="callout-box">{DISCLAIMER}</div>
      <div class="score-grid" style="margin-top:1.5rem;">
{CARDS}
      </div>
      <h3 class="kt-h3">Why we exclude maltitol instead of adjusting for it</h3>
      <div class="section-body">
        <p>Most sugar alcohols (erythritol, xylitol, sorbitol, isomalt, lactitol, mannitol) have a glycemic index under 15, low enough that the standard net carbs formula treats them fairly. Maltitol and its relatives sit around 35, roughly half of table sugar. Rather than build a formula with different fractions for eight molecules, we exclude bars that use these specific ones. "Sugar free" and "diabetic friendly" on a wrapper describe what the label is allowed to say, not what your blood sugar does, so read the full nutrition panel, not the front of the package.</p>
      </div>
      <h3 class="kt-h3">One more gotcha: IMO counted as fiber</h3>
      <div class="section-body">
        <p>{len(IMO_Q)} of the {comma(N)} bars here list isomalto-oligosaccharides (IMO), a syrup sold as a prebiotic fiber, all from {names_and(IMO_BRANDS)}. {imo_list()}. Our scoring treats IMO as a fiber, so it comes off the net carb count like any other fiber. Some research suggests your body digests much of it like a sugar, so a bar whose fiber comes partly from IMO may affect your blood sugar more than its net carbs suggest. Check the label if that matters to you.</p>
        <p><strong>Four questions worth asking before you buy a bar for blood sugar management:</strong></p>
        <ul class="criteria-list">
          <li>What are the net carbs, not just the sugar grams on the front of the label?</li>
          <li>How much fiber and protein does it have per serving, and is that enough to slow the carb load down?</li>
          <li>Does it use maltitol, polyglycitol or hydrogenated starch hydrolysates instead of a lower-glycemic sweetener?</li>
          <li>Is it a snack or a meal replacement in your plan, since portion and timing change how any bar affects you?</li>
        </ul>
        <p>Diabetes management is individual. Two people can eat the same bar and see different glucose responses depending on medication, activity, and what else they ate that day. Everything on this page is a starting filter built from label data, not a substitute for a conversation with your doctor or a registered dietitian about what fits your treatment plan.</p>
      </div>
    </div>
'''

# ---------------------------------------------------------------------------
# Findings: three data findings + one chart
# ---------------------------------------------------------------------------
def macro_miss(b): return any(k in SCREEN.fails[b['Key']] for k in ('sugar', 'nc', 'fiber'))
MISS = {gr: (sum(1 for b in ALL if b['score_band'] == gr and macro_miss(b)), sum(1 for b in ALL if b['score_band'] == gr))
        for gr in BAND_ORDER}
MISS_PCT = {gr: round(100 * h / t) for gr, (h, t) in MISS.items()}
C.check(MISS_PCT['A'] >= MISS_PCT['C'], 'A-grade bars miss the blood sugar macro cutoffs at least as often as C-grade bars')
QU = by_brand('Quest')
QU_Q = [b for b in QU if QF(b)]
QU_GRADE_ONLY = [b for b in QU if SCREEN.fails[b['Key']] == ['grade']]
C.check(len(QU_Q) + len(QU_GRADE_ONLY) == len(QU), 'every Quest flavor that fails, fails on grade alone')
MALT_ROWS = [(gr, sum(1 for b in ALL if b['score_band'] == gr and has_maltitol_family(b)),
              sum(1 for b in ALL if b['score_band'] == gr)) for gr in BAND_ORDER]
MR = {gr: round(100 * h / t) for gr, h, t in MALT_ROWS}
C.check(MR['A'] <= MR['B'] <= MR['C'] <= MR['D'] <= MR['F'] and MR['A'] < MR['F'],
        'maltitol share never falls with a step down in grade, and F is well above A')
INSIGHTS = [
    ('The maltitol trap is real.',
     f'{LOWS_M}% of bars with 1g or less of listed sugar still contain maltitol or a close relative. A bar can say almost no '
     'sugar on the front while delivering a sugar alcohol that still moves blood glucose.'),
    ('Net carbs catches more bars than sugar.',
     f"{comma(FAIL['nc'])} bars ({pct0(FAIL['nc'], NT)}%) fail on net carbs versus {comma(FAIL['sugar'])} "
     f"({pct0(FAIL['sugar'], NT)}%) on sugar. Total carbs and fiber matter as much as the sugar line on the label."),
    ('A clean grade doesn\'t make a bar blood sugar friendly.',
     f"{MISS_PCT['A']}% of A-grade bars miss at least one of the sugar, net carb or fiber cutoffs. Quest is the flip side: "
     f"every Quest flavor meets those cutoffs, but {len(QU_GRADE_ONLY)} of {len(QU)} grade C or below."),
]
FINDINGS = findings_v2_html(f'What we found screening {DB_PUBLIC} bars', INSIGHTS,
                            grade_share_chart_html(MALT_ROWS, title='Share of bars with maltitol or a close relative, by ingredient grade',
                                                   note=f'Out of the {DB_PUBLIC} bars in our database. Maltitol, maltitol syrup, '
                                                        'polyglycitol and hydrogenated starch hydrolysates.'))

# ---------------------------------------------------------------------------
# Brands that do it well + big brands
# ---------------------------------------------------------------------------
WELL = brands_well_rows(ALL, QF, n=8)
C.check(sum(r['big'] for r in WELL) >= 2 and sum(not r['big'] for r in WELL) >= 2, 'brands-well has 2+ big and 2+ small brands')
def well_why(r):
    lead = (f"All {r['total']} flavors qualify" if r['q'] == r['total'] else
            f"{r['q']} of {r['total']} flavors {'qualifies' if r['q'] == 1 else 'qualify'}")
    gm = r['grades']
    grades = f"all {next(iter(gm))} grade" if len(gm) == 1 else grade_mix_text(gm) + ' grade'
    bp = best_pick(r['qual'])
    return (f"{lead}, {grades}, averaging {g(sum(NC(b) for b in r['qual']) / r['q'])} net carbs. Best pick: "
            f"{bp['Flavor Name']} ({bp['score_band']}, {fnum(P(bp))}g protein, {fnum(NC(bp))}g net carbs).")
BRANDS_WELL = brands_well_html(WELL, well_why, h2='Brands that do it well',
                               intro='Brands with at least 3 bars in our database, ranked by how much of their lineup clears '
                                     'all six checks and how well those bars grade. We made sure to include both brands you '
                                     'can find at most grocery stores and smaller independents.')

MISS_PHRASE = {'sugar': 'more than 5g sugar', 'nc': 'more than 10g net carbs', 'fiber': 'less than 5g fiber',
               'protein': 'less than 10g protein', 'grade': 'a C-or-below grade', 'maltitol': 'maltitol or a relative'}
def fail_reasons(disq):
    rs = [(MISS_PHRASE[k], sum(1 for b in disq if k in SCREEN.fails[b['Key']])) for k, _, _ in SCREEN.checks]
    rs.sort(key=lambda r: -r[1])
    return rs
def big_verdict(r):
    disq = [b for b in r['bars'] if not QF(b)]
    bp = best_pick(r['qual'])
    pick = f" Best pick: {bp['Flavor Name']} ({bp['score_band']}, {fnum(P(bp))}g protein, {fnum(NC(bp))}g net carbs)." if bp else ''
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
    ALL, QF, big_verdict, h2='How do the big brands fare for blood sugar?',
    intro=('Every brand with national grocery, big-box or Costco distribution, with how many of its bars pass all six '
           'checks. Brand names link to our full reviews where we have one.'))

# ---------------------------------------------------------------------------
# Top 50 + Bar Finder CTA + criteria
# ---------------------------------------------------------------------------
T50 = top50_rows(Q, 50)
TOP50 = top50_html(T50, h2='Top 50 protein bars for diabetics',
                   intro='Ranked by ingredient grade first, then by protein per calorie. Tap any row for nutrition facts and '
                         'the full ingredient list.',
                   cols=('grade', 'protein', 'sugar', 'netcarbs', 'cal', 'fiber'), hide_mobile=('sugar', 'cal', 'fiber'))
FINDER = finder_cta_html(N, FINDER_HREF, desc=('The Bar Finder opens with this same screen applied: A or B grade, 10g+ '
                                               'protein, 5g or less sugar, 5g+ fiber, 10g or less net carbs, and maltitol, '
                                               'polyglycitol and hydrogenated starch hydrolysates excluded. Add your own '
                                               'filters for calories, brand, certifications, or ingredients to exclude.'))
CRITERIA = criteria_html(
    qualify_rule=('5g or less sugar, 10g or less net carbs (total carbs minus fiber minus sugar alcohol, straight off the '
                  'nutrition panel), 5g or more fiber, 10g or more protein, an A or B ingredient grade, and no maltitol, '
                  'maltitol syrup, polyglycitol or hydrogenated starch hydrolysates. Other sugar alcohols, stevia and monk '
                  f'fruit do not count against a bar. {comma(N)} of the {DB_PUBLIC} bars we track qualify.'),
    picks=PICKS)

# ---------------------------------------------------------------------------
# FAQ (answers may hold links; JSON-LD gets the plain text)
# ---------------------------------------------------------------------------
def brand_faq(name):
    bars = by_brand(name)
    C.check(bars, f'{name} is in bars.js')
    q = [b for b in bars if QF(b)]
    disq = [b for b in bars if not QF(b)]
    tail = f"averaging {g(avg(bars, 'Sugars (g)'))} sugar and {g(sum(NC(b) for b in bars) / len(bars))} net carbs per bar"
    if not disq:
        return f"By our screen, yes: all {len(bars)} tracked {name} flavors clear all six criteria, {tail}."
    miss = names_and(SCREEN.misses_mainly(disq))
    if not q:
        return f"Not by our screen: none of the {len(bars)} tracked {name} flavors clear all six criteria. They miss mainly on {miss}."
    verb = 'clears' if len(q) == 1 else 'clear'
    if len(q) * 2 >= len(bars):
        others = names_and(b['Flavor Name'] for b in disq)
        return (f"Mostly, by our screen: {len(q)} of {len(bars)} tracked {name} flavors {verb} all six criteria, {tail} "
                f"across the lineup. The {'one that misses is' if len(disq) == 1 else 'ones that miss are'} {others}, on {miss}.")
    ok = names_and(b['Flavor Name'] for b in q)
    return (f"Only {len(q)} of {len(bars)} tracked {name} flavors {verb} all six criteria: {ok}. The rest miss mainly on "
            f"{miss}, even though the lineup averages {g(avg(bars, 'Sugars (g)'))} sugar and "
            f"{g(sum(NC(b) for b in bars) / len(bars))} net carbs per bar.")
BEST, LOWNC = PK['Best overall'], PK['Lowest net carbs']
FAQS = [
    ('What should diabetics look for in a protein bar?',
     'We are not doctors, but here is what we filtered on: sugar, net carbs, and fiber, plus enough protein to be worth eating, '
     'an A or B ingredient quality grade, and zero maltitol. Sugar raises blood glucose directly. Net carbs (total carbs minus '
     'fiber minus sugar alcohols) is a better read on glycemic impact than the sugar line alone. Fiber slows digestion and '
     'blunts the spike. We required 5g or less sugar, 10g or less net carbs, and 5g or more fiber for every bar on this list.'),
    ('What is the best protein bar for diabetics?',
     f"By our rules, {full(BEST)}: {BEST['score_band']}-grade ingredients, {fnum(P(BEST))}g protein, {fnum(SUG(BEST))}g sugar, "
     f"{fnum(NC(BEST))}g net carbs and {fnum(FIB(BEST))}g fiber"
     + (", though part of its fiber comes from IMO (see our note on IMO above)." if imo(BEST) else ".")
     + f" For the fewest net carbs, {full(LOWNC)} has {fnum(NC(LOWNC))}g. Every bar in our Best 10 clears all six checks, "
       "and the right one depends on what you're managing."),
    ('How do you calculate net carbs?',
     "Net carbs = total carbohydrates minus dietary fiber minus sugar alcohols. We use the values straight off each bar's "
     'nutrition facts panel. Most sugar alcohols have a low enough glycemic impact that this formula treats them fairly. The '
     'exceptions, maltitol and its syrupy relatives, are excluded from this list entirely rather than adjusted for. See the '
     'next question for why.'),
    ('Why do you exclude maltitol instead of adjusting the math for it?',
     'We looked at doing per-molecule math instead of a flat formula, and decided against it. Most sugar alcohols (erythritol, '
     'xylitol, sorbitol, isomalt, lactitol, mannitol) have a glycemic index under 15, close enough to negligible that our '
     'standard net carbs formula already treats them fairly without any adjustment. Maltitol and its syrupy relatives '
     '(maltitol syrup, polyglycitol, hydrogenated starch hydrolysates) sit at a meaningfully higher glycemic index, roughly '
     '35, about half of table sugar. Rather than build a formula with different fractions for eight different molecules, we '
     'exclude bars that use these specific ones. A hard exclude is something we can state with confidence. A per-molecule '
     'formula is not, and we would rather be clear about what we are and are not confident in.'),
    ('What is the maltitol trap in sugar free protein bars?',
     "Maltitol is a sugar alcohol with a glycemic index around 35, well above erythritol's near-zero impact and closer to half "
     'of table sugar. Labeling rules let brands leave sugar alcohols off the sugar line, so a bar can say 0g or 1g sugar while '
     f'still containing maltitol. In our database, {LOWS_M}% of bars with 1g or less listed sugar still contain it or a close '
     'relative. Every bar on this list has been checked and confirmed free of maltitol, maltitol syrup, polyglycitol, and '
     'hydrogenated starch hydrolysates.'),
    ('Why does fiber matter for diabetics choosing a protein bar?',
     'Fiber slows gastric emptying, so glucose reaches the bloodstream more gradually after eating. We required at least 5g '
     f'of fiber for every bar on this list, and qualifying bars average {fnum(round(AVG_FIB, 1))}g.'),
    ('What does the ingredient quality grade mean on this page?',
     "Our A through F grade rates how clean and minimally processed a bar's ingredients are. It is a separate measurement from "
     'diabetic suitability. A bar can earn an A on ingredient quality and still be a poor fit for blood sugar management, or '
     'vice versa. We use it as one of the six filters here, requiring an A or B, but the core of the screen is sugar, net '
     'carbs, fiber, protein, and the maltitol exclusion.'),
    ('Are sugar alcohols safe for diabetics?',
     'It depends which one. Erythritol, xylitol, sorbitol, isomalt, lactitol, and mannitol all have a low enough glycemic '
     'impact that they get folded into our standard net carbs calculation. Maltitol and its syrupy relatives raise blood sugar '
     'meaningfully despite being marketed as sugar free, so those are a hard exclude from this list regardless of amount.'),
    ('Is IQ Bar good for diabetics?', brand_faq('IQ Bar')),
    ('Is Quest good for diabetics?', brand_faq('Quest')),
    ('How many protein bars in your database qualify for this list?',
     f'Out of {DB_PUBLIC} bars in our database, {N} meet all six criteria: 5g or less sugar, 10g or less net carbs, 5g or more '
     f'fiber, 10g or more protein, an A or B ingredient grade, and no maltitol. That is about {pct0(N, NT)}% of the full '
     'database.'),
]

# ---------------------------------------------------------------------------
# Regions
# ---------------------------------------------------------------------------
H1 = 'The 10 Best Protein Bars for Diabetics'
TITLE = f'10 Best Protein Bars for Diabetics ({DB_PUBLIC} Checked)'
DESC = (f'{LOWS_M}% of low-sugar protein bars still hide maltitol. We screened {DB_PUBLIC} for sugar, net carbs, fiber and '
        f'more. Our 10 best from {comma(N)} that pass.')
OG_DESC = (f'We screened {DB_PUBLIC} protein bars for sugar, net carbs, fiber, protein, ingredient grade and maltitol. '
           f'{comma(N)} pass all six. Here are the 10 best, each picked by a published rule.')
C.check(len(DESC) <= 155, f'meta description under 155 characters ({len(DESC)})')
FAQS_PLAIN = [(q, plain_text(a)) for q, a in FAQS]
REGIONS = v2_head_regions(title=TITLE, h1=H1, desc=DESC, og_desc=OG_DESC, url=URL, about='Diabetes-Friendly Eating Guide',
                          published=PUBLISHED, faqs=FAQS_PLAIN, picks=PICKS)
EDITORIAL = f'  <section class="section off" id="what-it-means">{MEANS}  </section>'
HERO = (f'<h1 class="hero-title">{esc(H1)}</h1>\n'
        f'    <p class="hero-sub">Plenty of protein bars say "sugar free" and still carry a real carb load, or sweeten with '
        f'maltitol, a sugar alcohol that raises blood sugar more than most. We screened every bar for six things people '
        f'managing blood sugar look for: 5g or less sugar, 10g or less net carbs, 5g+ fiber, 10g+ protein, an A or B '
        f'ingredient grade, and no maltitol or its close relatives.</p>\n'
        f'    <p class="hero-sub">Of the {DB_PUBLIC} bars we track, {comma(N)} pass all six. Net carbs stops more bars than '
        f'any other check, and {LOWS_M}% of bars with 1g or less of listed sugar still contain maltitol or a relative. '
        f'{esc(DISCLAIMER)}</p>')
REGIONS += [
    ('hero', HERO),
    ('best10', best10_html(PICKS, h2='Best 10 protein bars for diabetics', intro=B10_INTRO, macros=CARD_MACROS)),
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
        ('/no-sugar-alcohols', 'No Sugar Alcohols', 'Bars that skip maltitol, erythritol, and other sugar alcohols entirely.'),
        ('/keto-protein-bars', 'Keto Protein Bars', 'Low net carb bars with enough fat to fit a keto day.'),
        ('/glp1-protein-bars', 'GLP-1 Protein Bars', '15g+ protein, 200 calories or less, low sugar, and no sugar alcohols.'),
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
