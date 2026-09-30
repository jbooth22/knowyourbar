#!/usr/bin/env python3
"""Rebuild keto-protein-bars.html from bars.js. GUIDE PAGE v2 ("Best 10").

Run from the repo root:  python3 build_keto_protein_bars.py

Layout and every rule: claude/GUIDE_PAGE_SPEC_V2.md (locked 2026-09-29) and
the v2 section of kyb_guide_lib.py, built the same way as the other v2 guides
(closest reference: build_best_bars_for_diabetics.py, a macro screen). The
first run migrated the live v1 page to the v2 body (head, nav and footer kept
as deployed) and added the ItemList JSON-LD marker to the head; later runs
rewrite only the <!-- kyb:NAME --> regions. Every number, pick and brand row
comes from bars.js. Copy that depends on a fact is checked; if one stops being
true the build stops and lists it. Ingredient quality is shown and ranked as a
GRADE only.

Screen: GUIDE_FILTERS['keto-protein-bars'] = net carbs <= 8 (carbs - fiber -
sugar alcohol, full subtraction), protein >= 10, fat >= 8, no maltitol family.
No grade gate: C/D/F bars count as qualifying, but the Best 10 and the Top 50
only use A and B bars (v2 guardrail / grade-first order).

Bar Finder (Jeff, 2026-09-30): no link matches the guide exactly, because the
Bar Finder has no minimum-fat slider. The button opens the closest screen
(protein 10+, net carbs 8 or less, maltitol family excluded, sorted by fat) and
says plainly that it shows N_FINDER bars, including the ones under 8g fat. The
build checks that the link returns the guide set plus only bars under 8g fat.
A Min Fat slider is parked for a later session.

Guide slots (Jeff, 2026-09-30): Lowest net carbs, Best whey protein, Highest
fiber, Best dairy-free. Fallbacks: Best soy-free, then Best gluten-free.
"""
import re
from kyb_guide_lib import *

PAGE = 'keto-protein-bars.html'
URL = 'https://knowyourbar.com/keto-protein-bars'
PUBLISHED = '2026-04-29'
set_tie_seed('keto-protein-bars')   # per-guide shuffle for exact ties (kyb_guide_lib, 2026-09-30)

ALL = load_bars()
QF = GUIDE_FILTERS['keto-protein-bars']
Q = [b for b in ALL if QF(b)]
D = [b for b in ALL if not QF(b)]
N, ND, NT = len(Q), len(D), len(ALL)
GR = {g: sum(1 for b in Q if b.get('score_band') == g) for g in BAND_ORDER}
N_AB = GR['A'] + GR['B']
N_CF = N - N_AB
C = Claims()
NC = net_carbs
def FAT(b): return num(b.get('Total Fat (g)')) or 0
DISCLAIMER = ("We are not doctors or dietitians. These are the qualities we know people look for, so that's what we "
              "factored in.")

SCREEN = Screen(ALL, [
    ('nc', 'net carbs', lambda b: NC(b) is None or NC(b) > 8),
    ('protein', 'protein', lambda b: P(b) < 10),
    ('fat', 'fat', lambda b: FAT(b) < 8),
    ('maltitol', 'maltitol or a related sweetener', has_maltitol_family),
])
FAIL = {k: SCREEN.count(k) for k, _, _ in SCREEN.checks}
FAIL_BARS = {k: [b for b in ALL if k in SCREEN.fails[b['Key']]] for k, _, _ in SCREEN.checks}
MULTI = SCREEN.multi(D)
C.check(all(SCREEN.fails[b['Key']] for b in D) and not any(SCREEN.fails[b['Key']] for b in Q), 'the four checks match the keto filter')
C.check(N_CF > 0 and N_AB > 50, 'some qualifying bars grade C or below, and more than 50 grade A or B')
LOWS = [b for b in ALL if SUG(b) <= 1]
LOWS_M = pct0(sum(1 for b in LOWS if has_maltitol_family(b)), len(LOWS))
AVG_FAT, AVG_NC = avg(Q, 'Total Fat (g)'), sum(NC(b) for b in Q) / N
C.check(FAIL['nc'] == max(FAIL.values()), 'net carbs is the toughest single check')
C.check(AVG_FAT > 9 and AVG_NC < 7, 'qualifying averages sit comfortably inside the thresholds')

# Bar Finder: closest link (no min-fat slider). protein=10 & netcarbs=8 & excl maltitol family (app.js applyFilters)
FINDER_EXCL = ['maltitol', 'polyglycitol', 'hydrogenated starch hydrolysate']
def finder_match(b):
    v = num(b.get('Protein (g)'))
    if v is not None and v < 10:
        return False   # app.js skips a slider when the field is empty
    nc = (num(b.get('Total Carbohydrates (g)')) or 0) - (num(b.get('Dietary Fiber (g)')) or 0) - (num(b.get('Sugar Alcohol (g)')) or 0)
    if nc > 8:
        return False
    t = (b.get('Ingredients') or '').lower()
    return not any(e in t for e in FINDER_EXCL)
F_SET = [b for b in ALL if finder_match(b)]
F_KEYS, Q_KEYS = {b['Key'] for b in F_SET}, {b['Key'] for b in Q}
F_EXTRA = [b for b in F_SET if b['Key'] not in Q_KEYS]
N_FINDER = len(F_SET)
C.check(Q_KEYS <= F_KEYS and all(FAT(b) < 8 for b in F_EXTRA),
        'the Bar Finder link returns every keto bar plus only bars under 8g fat')
FINDER_HREF = ('/bar-finder?protein=10&netcarbs=8&excl=maltitol,polyglycitol,hydrogenated%20starch%20hydrolysate'
               '&sort=fat:desc')

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
DAIRY_RX = re.compile(r'\bwhey\b|\bmilk\b|\bcasein|\bcheese|\byogurt|\bbutter(?:milk|fat)\b|\bghee\b|(?<!peanut )(?<!cocoa )(?<!cacao )(?<!almond )(?<!cashew )\bbutter\b', re.I)
def nc_why(b, c):
    sa = SA(b)
    parts = f"{fnum(num(b.get('Total Carbohydrates (g)')))}g carbs minus {fnum(FIB(b))}g fiber" + (f" and {fnum(sa)}g sugar alcohol" if sa else '')
    return (f"{fnum(NC(b))}g net carbs ({parts}), {c['tied']}the lowest of any bar here, with {fnum(FAT(b))}g fat and "
            f"{fnum(P(b))}g protein" + (f", and it wins the tie on {c['tie_on']}." if c['tied'] and c['tie_on'] != 'name' else "."))
LOW_NET = Slot('Lowest net carbs', 'The fewest net carbs (total carbs minus fiber minus sugar alcohol), grade B or better, 10g+ protein.',
               lambda E: [b for b in E if NC(b) is not None], lambda b: (NC(b),) + tie_chain(b), nc_why, metric=NC)
SLOTS = [
    slot_best_overall(15),
    slot_cleanest(),
    slot_highest_protein(300),
    slot_protein_per_cal(12),
    slot_lowest_calorie(),
    slot_big_brand(),
    LOW_NET,
    slot_subset('Best whey protein', 'Whey protein on the label.', whey,
                lambda b: f"Built on {whey_name(b)}, a complete dairy protein and "
                          + ("one of the protein sources our scoring rates highest." if 'isolate' in whey_name(b)
                             else "one of the protein sources our scoring rates near the top.")),
    slot_highest_fiber(),
    slot_subset('Best dairy-free', 'Labeled dairy free by the brand.', yes('Dairy Free (Y/N)'),
                lambda b: 'Labeled dairy free, so no whey, milk protein or other dairy on the label.'),
]
FALLBACKS = [
    slot_subset('Best soy-free', 'Labeled soy free by the brand.', yes('Soy Free (Y/N)'),
                lambda b: 'Labeled soy free, with no soy protein, soy lecithin or soybean oil on the label.'),
    slot_subset('Best gluten-free', 'Labeled gluten free by the brand.', yes('Gluten Free (Y/N)'),
                lambda b: 'Labeled gluten free by the brand.'),
]
PICKS = pick_best10(Q, SLOTS, FALLBACKS)
C.check(len(PICKS) == 10, 'ten Best 10 picks available')
C.check([s.label for s, *_ in PICKS] == [s.label for s in SLOTS], 'all ten planned slots filled without fallbacks')
C.check(not any(re.search(r'score \d|scored? \d', w) for _s, _b, w, _n in PICKS), 'no ingredient score printed in a pick')
PK = {s.label: b for s, b, _w, _n in PICKS}
C.check(has_tag(PK['Best whey protein'], 'Quality Protein Source'), 'the whey pick carries the Quality Protein Source tag')
C.check(not DAIRY_RX.search(ingr(PK['Best dairy-free'])), 'the dairy-free pick names no dairy ingredient')
B10_INTRO = ("Ten keto bars, each the winner of one thing people shop for. Every pick has 8g or less net carbs, 8g+ fat, "
             "10g+ protein, no maltitol and an A or B ingredient grade, and no bar appears twice.")
CARD_MACROS = [('Protein', lambda b: f'{fnum(P(b))}g'), ('Net carbs', lambda b: f'{fnum(NC(b))}g'),
               ('Fat', lambda b: f'{fnum(FAT(b))}g'), ('Fiber', lambda b: f'{fnum(FIB(b))}g')]

# ---------------------------------------------------------------------------
# What keto means on this page (carried over from v1, trimmed) + gotchas
# ---------------------------------------------------------------------------
IMO_Q = [b for b in Q if imo(b)]
IMO_PICKS = [b for _s, b, _w, _n in PICKS if imo(b)]
IMO_BRANDS = sorted({b['Brand Name'] for b in IMO_Q}, key=str.lower)
C.check(IMO_Q and IMO_PICKS, 'some qualifying bars and Best 10 picks list IMO')
MALT_BRANDS = sorted({b['Brand Name'] for b in FAIL_BARS['maltitol']}, key=str.lower)
CARDS = '\n'.join([
    v2_count_card_html('Net carbs over 8g', FAIL_BARS['nc'], NT,
                       'Net carbs (total carbs minus fiber minus sugar alcohols) decides whether a bar fits a ketogenic day, '
                       'and it is rarely printed on the label.', names=[]),
    v2_count_card_html('Fat under 8g', FAIL_BARS['fat'], NT,
                       'Keto runs on fat for fuel. A bar can be low-carb and still not have enough fat to fit the pattern. We '
                       'required at least 8g.', names=[]),
    v2_count_card_html('Protein under 10g', FAIL_BARS['protein'], NT,
                       'Below 10g, a bar stops working as a protein bar. We required at least 10g.', names=[]),
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
      <h2 class="section-title">What "keto friendly" means on this page</h2>
      <div class="section-body">
        <p>Search for the best keto protein bars and most lists rank by sugar grams alone. Keto is a macro game, not a low-sugar game: it works by keeping carbs low enough that you burn fat for fuel, so net carbs and fat both have to be part of the screen. A bar can say 1g sugar and still carry 20g of net carbs, and a low-carb bar with almost no fat doesn't fit the pattern either.</p>
        <p>So every bar here has to pass four checks: 8g or less net carbs, 8g or more fat, 10g or more protein, and no maltitol or its close relatives. {of_db(N, NT)} bars pass all four. Here is how often each check catches a bar.</p>
      </div>
      <div class="callout-box">{DISCLAIMER}</div>
      <div class="score-grid" style="margin-top:1.5rem;">
{CARDS}
      </div>
      <h3 class="kt-h3">Why we exclude maltitol instead of adjusting for it</h3>
      <div class="section-body">
        <p>Most sugar alcohols (erythritol, xylitol, sorbitol, isomalt, lactitol, mannitol) have a glycemic index under 15, low enough that the standard net carbs formula treats them fairly. Maltitol and its relatives sit around 35, roughly half of table sugar. Rather than build a formula with different fractions for eight molecules, we exclude bars that use these specific ones. "Keto friendly" and "sugar free" on a wrapper describe what the label is allowed to say, not what the macro panel adds up to, so read the full nutrition panel and ingredient list.</p>
      </div>
      <h3 class="kt-h3">Keto doesn't screen on ingredient grade</h3>
      <div class="section-body">
        <p>The four checks are all about macros and maltitol, so a bar can qualify with a C, D or F ingredient grade. {N_CF} of the {comma(N)} keto bars here do. Every Best 10 pick and every bar in our Top 50 is an A or B, so the lists below skip those.</p>
      </div>
      <h3 class="kt-h3">One more gotcha: IMO counted as fiber</h3>
      <div class="section-body">
        <p>{len(IMO_Q)} of the {comma(N)} keto bars here list isomalto-oligosaccharides (IMO), a syrup sold as a prebiotic fiber, all from {names_and(IMO_BRANDS)}. {imo_list()}. Our scoring treats IMO as a fiber, so it comes off the net carb count like any other fiber. Some research suggests your body digests much of it like a sugar, so a bar whose fiber comes partly from IMO may carry more usable carbs than its net carbs suggest. Check the label if you're counting closely.</p>
        <p><strong>Four questions worth asking before you buy a bar for keto:</strong></p>
        <ul class="criteria-list">
          <li>What are the net carbs, not just the sugar grams on the front of the label?</li>
          <li>Does it have enough fat to fit a ketogenic day, or is it just low-carb?</li>
          <li>Does it use maltitol, polyglycitol or hydrogenated starch hydrolysates instead of a lower-glycemic sweetener?</li>
          <li>Does the ingredient list hold up on its own, separate from whether the macros fit?</li>
        </ul>
        <p>How strict keto needs to be varies by person and by which version you follow. Everything on this page is a starting filter built from label data, not a substitute for tracking your own carb budget or a conversation with a doctor or dietitian about what fits your goals.</p>
      </div>
    </div>
'''

# ---------------------------------------------------------------------------
# Findings: three data findings + one chart
# ---------------------------------------------------------------------------
PASS_ROWS = [(gr, sum(1 for b in ALL if b['score_band'] == gr and QF(b)), sum(1 for b in ALL if b['score_band'] == gr))
             for gr in BAND_ORDER]
PR = {gr: round(100 * h / t) for gr, h, t in PASS_ROWS}
C.check(max(PR.values()) <= 15, 'no grade has more than 15% of its bars clearing the keto screen')
C.check(PR['A'] < PR['B'], 'A-grade bars clear the keto screen less often than B-grade bars')
INSIGHTS = [
    ('Net carbs is the toughest check.',
     f"{comma(FAIL['nc'])} bars ({pct0(FAIL['nc'], NT)}%) fail on net carbs, far more than on fat ({pct0(FAIL['fat'], NT)}%) "
     f"or protein ({pct0(FAIL['protein'], NT)}%). Most protein bars aren't built with keto-level carbs in mind."),
    ('The maltitol trap is real here too.',
     f'{LOWS_M}% of bars with 1g or less of listed sugar still contain maltitol or a close relative. A bar can market itself '
     'as keto friendly on the front while delivering a sugar alcohol that still moves blood glucose.'),
    ('A clean grade and keto macros rarely line up.',
     f"Only {PR['A']}% of A-grade bars clear the keto screen, against {PR['B']}% of B-grade bars. Clean bars tend to use "
     f"dates, oats and honey, which push net carbs up. {N_CF} of the {comma(N)} keto bars grade C or below."),
]
FINDINGS = findings_v2_html(f'What we found screening {DB_PUBLIC} bars', INSIGHTS,
                            grade_share_chart_html(PASS_ROWS, title='Share of bars that clear the keto screen, by ingredient grade',
                                                   note=f'Out of the {DB_PUBLIC} bars in our database. Keto: 8g or less net carbs, '
                                                        '8g+ fat, 10g+ protein, no maltitol.'))
CLEAN_SWEET = [b for b in ALL if b['score_band'] == 'A' and not QF(b)
               and re.search(r'\bdates?\b|\boats?\b|\bhoney\b', ingr(b), re.I)]
C.check(len(CLEAN_SWEET) > sum(1 for b in ALL if b['score_band'] == 'A' and not QF(b)) / 2,
        'most A-grade bars that miss keto contain dates, oats or honey')

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
    return (f"{lead}, {grades}, averaging {g(sum(NC(b) for b in r['qual']) / r['q'])} net carbs and "
            f"{g(avg(r['qual'], 'Total Fat (g)'))} fat. Best pick: {bp['Flavor Name']} ({bp['score_band']}, "
            f"{fnum(P(bp))}g protein, {fnum(NC(bp))}g net carbs).")
BRANDS_WELL = brands_well_html(WELL, well_why, h2='Brands that do it well',
                               intro='Brands with at least 3 bars in our database, ranked by how much of their lineup clears '
                                     'all four keto checks and how well those bars grade. We made sure to include both brands '
                                     'you can find at most grocery stores and smaller independents.')

MISS_PHRASE = {'nc': 'more than 8g net carbs', 'protein': 'less than 10g protein', 'fat': 'less than 8g fat',
               'maltitol': 'maltitol or a relative'}
def fail_reasons(disq):
    rs = [(MISS_PHRASE[k], sum(1 for b in disq if k in SCREEN.fails[b['Key']])) for k, _, _ in SCREEN.checks]
    rs.sort(key=lambda r: -r[1])
    return rs
def big_verdict(r):
    disq = [b for b in r['bars'] if not QF(b)]
    bp = best_pick(r['qual'])
    pick = f" Best pick: {bp['Flavor Name']} ({bp['score_band']}, {fnum(P(bp))}g protein, {fnum(NC(bp))}g net carbs)." if bp else ''
    low = sum(1 for b in r['qual'] if b['score_band'] in ('C', 'D', 'F'))
    check = (f" {'All' if low == r['q'] else f'{low} of those'} grade C or below, so check the label." if low * 2 > r['q'] else '')
    if r['q'] == r['total']:
        return 'Every flavor qualifies.' + (check or pick)
    rs = fail_reasons(disq)
    every = [n for n, c in rs if c == len(disq)]
    main = every[0] if every else rs[0][0]
    if r['q'] == 0:
        return f"None qualify: every flavor has {main}." if every else f"None qualify. Most flavors have {main}."
    rest = (f"The other one has {main}." if len(disq) == 1 else f"The rest {'all' if every else 'mostly'} have {main}.")
    verb = 'qualifies' if r['q'] == 1 else 'qualify'
    return f"{'Only ' if r['q'] * 2 < r['total'] else ''}{r['q']} of {r['total']} {verb}. {rest}" + (check or pick)
BIG_HTML, BIG_ROWS = big_brands_html(
    ALL, QF, big_verdict, h2='How do the big brands fare on keto?',
    intro=('Every brand with national grocery, big-box or Costco distribution, with how many of its bars pass all four '
           'keto checks. Brand names link to our full reviews where we have one.'))

# ---------------------------------------------------------------------------
# Top 50 + Bar Finder CTA + criteria
# ---------------------------------------------------------------------------
T50 = top50_rows(Q, 50)
C.check(all(b['score_band'] in ('A', 'B') for b in T50), 'every Top 50 bar grades A or B')
TOP50 = top50_html(T50, h2='Top 50 keto protein bars',
                   intro='Ranked by ingredient grade first, then by protein per calorie. Tap any row for nutrition facts and '
                         'the full ingredient list.',
                   cols=('grade', 'protein', 'netcarbs', 'fat', 'cal', 'fiber'), hide_mobile=('fat', 'cal', 'fiber'))
FINDER = finder_cta_html(N_FINDER, FINDER_HREF, desc=(
    f'The Bar Finder can\'t filter by a minimum amount of fat yet, so this link shows {comma(N_FINDER)} bars: all '
    f'{comma(N)} keto bars on this page plus {len(F_EXTRA)} that pass every other check but have less than 8g fat. It opens '
    'with 10g+ protein, 8g or less net carbs and maltitol, polyglycitol and hydrogenated starch hydrolysates excluded, '
    'sorted by fat so the bars with 8g or more come first.'))
# The lib heading says "See all N"; here N is the Bar Finder's count, not the guide's, so say what the link opens.
_see_all = f'See all {comma(N_FINDER)} in the Bar Finder &rarr;'
C.check(FINDER.count(_see_all) == 2, 'finder CTA heading and button found')
FINDER = FINDER.replace(f'<h2 class="explore-cta-main-heading">{_see_all}</h2>',
                        '<h2 class="explore-cta-main-heading">Find keto bars in the Bar Finder &rarr;</h2>', 1)
FINDER = FINDER.replace(_see_all, f'Open {comma(N_FINDER)} low-carb bars in the Bar Finder &rarr;', 1)
CRITERIA = criteria_html(
    qualify_rule=('8g or less net carbs (total carbs minus fiber minus sugar alcohol, straight off the nutrition panel), 8g '
                  'or more fat, 10g or more protein, and no maltitol, maltitol syrup, polyglycitol or hydrogenated starch '
                  'hydrolysates. Other sugar alcohols, stevia and monk fruit do not count against a bar. Ingredient grade '
                  f'is not part of the keto screen. {comma(N)} of the {DB_PUBLIC} bars we track qualify, {N_AB} of them with '
                  'an A or B grade.'),
    picks=PICKS)

# ---------------------------------------------------------------------------
# FAQ (answers may hold links; JSON-LD gets the plain text)
# ---------------------------------------------------------------------------
def brand_faq(name):
    bars = by_brand(name)
    C.check(bars, f'{name} is in bars.js')
    q = [b for b in bars if QF(b)]
    disq = [b for b in bars if not QF(b)]
    tail = (f"averaging {g(sum(NC(b) for b in bars) / len(bars))} net carbs and {g(avg(bars, 'Total Fat (g)'))} fat per bar")
    if not disq:
        return f"By our screen, yes: all {len(bars)} tracked {name} flavors clear our net carb, protein, fat and maltitol criteria, {tail}."
    miss = names_and(SCREEN.misses_mainly(disq))
    if not q:
        return f"Not by our screen: none of the {len(bars)} tracked {name} flavors clear all four criteria. They miss mainly on {miss}."
    low = [b for b in q if b['score_band'] in ('C', 'D', 'F')]
    verb = 'clears' if len(q) == 1 else 'clear'
    grade = ('' if not low else
             f" {'All of them' if len(low) == len(q) else f'{len(low)} of them'} grade C or below on ingredient quality, "
             "so they fit the macros but not our Best 10.")
    return (f"Partly, by our screen: {len(q)} of {len(bars)} tracked {name} flavors {verb} all four criteria. The rest miss "
            f"mainly on {miss}.{grade}")
BEST, LOWNC = PK['Best overall'], PK['Lowest net carbs']
FAQS = [
    ('What should I look for in a keto protein bar?',
     'We are not doctors, but here is what we filtered on: net carbs, protein, fat, and zero maltitol. Net carbs (total carbs '
     'minus fiber minus sugar alcohols) is the number that determines whether a bar actually fits a ketogenic diet, not the '
     'sugar line alone. We required 8g or less net carbs, 10g or more protein, 8g or more fat, and no maltitol or its close '
     'relatives for every bar on this list.'),
    ('What is the best keto protein bar?',
     f"By our rules, {full(BEST)}: {BEST['score_band']}-grade ingredients, {fnum(P(BEST))}g protein, {fnum(NC(BEST))}g net "
     f"carbs and {fnum(FAT(BEST))}g fat" + (", though part of its fiber comes from IMO (see our note on IMO above)." if imo(BEST) else ".")
     + f" For the fewest net carbs, {full(LOWNC)} has {fnum(NC(LOWNC))}g with {fnum(FAT(LOWNC))}g fat. Every bar in our "
       "Best 10 clears all four checks with an A or B grade."),
    ('How do you calculate net carbs?',
     "Net carbs = total carbohydrates minus dietary fiber minus sugar alcohols. We use the values straight off each bar's "
     'nutrition facts panel. Most sugar alcohols have a low enough glycemic impact that this formula treats them fairly. The '
     'exception, maltitol and its syrupy relatives, is excluded from this list entirely rather than adjusted for. See the next '
     'question for why.'),
    ('Why do you exclude maltitol instead of adjusting the math for it?',
     'We looked at doing per-molecule math instead of a flat formula, and decided against it. Most sugar alcohols (erythritol, '
     'xylitol, sorbitol, isomalt, lactitol, mannitol) have a glycemic index under 15, close enough to negligible that our '
     'standard net carbs formula already treats them fairly without any adjustment. Maltitol and its syrupy relatives '
     '(maltitol syrup, polyglycitol, hydrogenated starch hydrolysates) sit at a meaningfully higher glycemic index, roughly '
     '35, about half of table sugar. Rather than build a formula with different fractions for eight different molecules, we '
     'exclude bars that use these specific ones. A hard exclude is something we can state with confidence. A per-molecule '
     'formula is not, and we would rather be clear about what we are and are not confident in.'),
    ('What is the maltitol trap in keto-marketed protein bars?',
     "Maltitol is a sugar alcohol with a glycemic index around 35, well above erythritol's near-zero impact and closer to half "
     'of table sugar. Labeling rules let brands leave sugar alcohols off the sugar line, so a bar can say 0g or 1g sugar and '
     f'market itself as keto-friendly while still containing maltitol. In our database, {LOWS_M}% of bars with 1g or less '
     'listed sugar still contain it or a close relative. Every bar on this list has been checked and confirmed free of '
     'maltitol, maltitol syrup, polyglycitol, and hydrogenated starch hydrolysates.'),
    ('Why does fat matter for a keto protein bar?',
     'A ketogenic diet runs on fat for fuel instead of carbohydrates, so a bar needs meaningful fat to fit the macro pattern, '
     f'not just low carbs. We required at least 8g of fat for every bar on this list, and qualifying bars average {fnum(round(AVG_FAT, 1))}g.'),
    ('What does the ingredient quality grade mean on this page?',
     "Our A through F grade rates how clean and minimally processed a bar's ingredients are. It is a separate measurement "
     'from keto suitability. A bar can earn an A on ingredient quality and still be a poor macro fit for keto, or vice versa. '
     f'Grade is not part of the keto screen, so {N_CF} of the {comma(N)} bars that qualify grade C or below, but every Best 10 '
     'pick and every Top 50 bar on this page is an A or B.'),
    ('Are sugar alcohols keto-friendly?',
     'It depends which one. Erythritol, xylitol, sorbitol, isomalt, lactitol, and mannitol all have a low enough glycemic '
     "impact that they get folded into our standard net carbs calculation and don't count against a bar here. Maltitol and its "
     'syrupy relatives raise blood sugar meaningfully despite being marketed as sugar free, so those are a hard exclude from '
     'this list regardless of amount.'),
    ('Is IQ Bar good for keto?', brand_faq('IQ Bar')),
    ('Is Quest good for keto?', brand_faq('Quest')),
    ('How many protein bars in your database qualify for this list?',
     f'Out of {DB_PUBLIC} bars in our database, {N} meet all four criteria: 8g or less net carbs, 10g or more protein, 8g or '
     f'more fat, and no maltitol. That is about {pct0(N, NT)}% of the full database.'),
]

# ---------------------------------------------------------------------------
# Regions
# ---------------------------------------------------------------------------
H1 = 'The 10 Best Keto Protein Bars'
TITLE = f'10 Best Keto Protein Bars ({DB_PUBLIC} Checked)'
DESC = (f'{pct0(FAIL["nc"], NT)}% of protein bars have too many net carbs for keto. We screened {DB_PUBLIC} for net carbs, '
        f'fat, protein and maltitol. Our 10 best.')
OG_DESC = (f'We screened {DB_PUBLIC} protein bars for net carbs, fat, protein and maltitol. {comma(N)} pass all four. '
           'Here are the 10 best, each picked by a published rule.')
C.check(len(DESC) <= 155, f'meta description under 155 characters ({len(DESC)})')
FAQS_PLAIN = [(q, plain_text(a)) for q, a in FAQS]
REGIONS = v2_head_regions(title=TITLE, h1=H1, desc=DESC, og_desc=OG_DESC, url=URL, about='Keto Diet Eating Guide',
                          published=PUBLISHED, faqs=FAQS_PLAIN, picks=PICKS)
EDITORIAL = f'  <section class="section off" id="what-it-means">{MEANS}  </section>'
HERO = (f'<h1 class="hero-title">{esc(H1)}</h1>\n'
        f'    <p class="hero-sub">Keto is a macro game, not just a low-sugar game. A keto bar needs few net carbs once fiber '
        f'and sugar alcohols come off, enough fat to fit the pattern, and real protein, without maltitol, a sugar alcohol that '
        f'raises blood sugar more than most. We screened every bar for exactly that: 8g or less net carbs, 8g+ fat, 10g+ '
        f'protein, and no maltitol or its close relatives.</p>\n'
        f'    <p class="hero-sub">Of the {DB_PUBLIC} bars we track, {comma(N)} pass all four. Net carbs stops '
        f'{pct0(FAIL["nc"], NT)}% of bars on its own, and {N_CF} of the bars that pass grade C or below on ingredients, so our '
        f'picks only use A and B bars. {esc(DISCLAIMER)}</p>')
REGIONS += [
    ('hero', HERO),
    ('best10', best10_html(PICKS, h2='Best 10 keto protein bars', intro=B10_INTRO, macros=CARD_MACROS)),
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
        ('/no-sugar-alcohols', 'No Sugar Alcohols', 'Bars that skip maltitol, erythritol, and other sugar alcohols entirely.'),
        ('/no-seed-oils', 'No Seed Oils', 'Bars that skip processed seed and vegetable oils entirely.'),
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
    print(f'{PAGE}: {N} qualify ({N_AB} A/B), {ND} disqualified, finder link {N_FINDER}, {size:,} bytes, FAQ at byte {faq_at:,}')
    for i, (s_, b, why, n) in enumerate(PICKS, 1):
        print(f'  {i:2d}. {s_.label}: {full(b)} ({b["score_band"]}) [pool {n}]')
        print(f'      {why}')
