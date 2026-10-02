#!/usr/bin/env python3
"""Build high-protein-bars.html from bars.js. GUIDE PAGE v2 ("Best 10").

Run from the repo root:  python3 build_high_protein_bars.py

New guide (2026-10-02). Layout and every rule: claude/GUIDE_PAGE_SPEC_V2.md and
the v2 section of kyb_guide_lib.py. The page was started from a copy of
glp1-protein-bars.html (head, nav and footer as deployed, canonical changed,
GLP-1 page styles removed); every region below is generated. Every number,
pick and brand row comes from bars.js. Copy that depends on a fact is
checked; if one stops being true the build stops and lists it. Ingredient
quality is shown and ranked as a GRADE only.

Screen: GUIDE_FILTERS['high-protein-bars'] = protein >= 20g. No grade gate
(the Best 10 and its rules use A/B only).
Bar Finder: /bar-finder?protein=20 (Min Protein slider; checked key for key).

Guide slots (picked 2026-10-02, no approval round per Jeff): Best whey
protein, Best plant-based, Lowest sugar (no sugar alcohol), Best gluten-free.
Fallbacks: Highest fiber, then Best dairy-free.
"""
import re
from kyb_guide_lib import *

PAGE = 'high-protein-bars.html'
URL = 'https://knowyourbar.com/high-protein-bars'
PUBLISHED = '2026-10-02'
set_tie_seed('high-protein-bars')

ALL = load_bars()
QF = GUIDE_FILTERS['high-protein-bars']
Q = [b for b in ALL if QF(b)]
D = [b for b in ALL if not QF(b)]
N, ND, NT = len(Q), len(D), len(ALL)
GR = {g: sum(1 for b in Q if b.get('score_band') == g) for g in BAND_ORDER}
AB = GR['A'] + GR['B']
LOW = N - AB
DB_AB = sum(1 for b in ALL if b['score_band'] in ('A', 'B'))
C = Claims()
def sa_any(b): return SA(b) > 0 or has_sugar_alcohol(b)

C.check(200 <= N <= 450, f'qualifying count in the expected range ({N})')
C.check(not any(num(b.get('Protein (g)')) is None for b in ALL), 'every bar has a protein value')
C.check(pct0(AB, N) < pct0(DB_AB, NT), 'high protein bars grade A/B less often than the database')
AVG_CAL_Q, AVG_CAL_D = avg(Q, 'Calories'), avg(D, 'Calories')
C.check(AVG_CAL_Q > AVG_CAL_D + 20, 'high protein bars average clearly more calories')
OVER250 = [b for b in Q if CAL(b) > 250]
Q_SA = [b for b in Q if sa_any(b)]
Q_ART = [b for b in Q if has_tag(b, 'Artificial Sweeteners')]
DB_ART = [b for b in ALL if has_tag(b, 'Artificial Sweeteners')]
C.check(len(Q_SA) * 2 > N, 'most high protein bars use a sugar alcohol')
C.check(all('sucralose' in ingr(b).lower() for b in Q_ART), 'every artificial-sweetener bar here has sucralose')
C.check(pct0(len(Q_ART), N) > 2 * pct0(len(DB_ART), NT), 'artificial sweeteners at least twice as common as in the database')
PROTEINS = [('Milk protein or casein', r'milk protein|casein|caseinate'), ('Whey', r'\bwhey\b'), ('Soy protein', r'soy protein'),
            ('Nuts or nut butter', r'peanut|almond|cashew'), ('Collagen', r'collagen|gelatin'), ('Pea protein', r'pea protein'),
            ('Rice protein', r'rice protein'), ('Egg whites', r'egg white')]
def lead_protein(b):
    t, best = ingr(b).lower(), None
    for name, rx in PROTEINS:
        m = re.search(rx, t)
        if m and (best is None or m.start() < best[1]):
            best = (name, m.start())
    return best[0] if best else None
LEAD = Counter_(lead_protein(b) for b in Q)
TOP2 = [n for n, _c in LEAD.most_common(2)]
C.check(set(TOP2) == {'Milk protein or casein', 'Whey'}, 'milk proteins and whey lead the protein sources')
COLLAGEN = [b for b in Q if lead_protein(b) == 'Collagen']
MOST = sorted(Q, key=lambda b: (-P(b),) + tie_chain(b))[0]
P30 = [b for b in Q if P(b) >= 30]
C.check(all(b['score_band'] not in ('A', 'B') for b in P30), 'every 30g+ bar grades C or below')
C.check(MOST['score_band'] not in ('A', 'B'), 'the single highest protein bar grades C or below')
TOP_AB = sorted([b for b in Q if b['score_band'] in ('A', 'B')], key=lambda b: (-P(b),) + tie_chain(b))[0]
SHARE = [(gr, sum(1 for b in Q if b['score_band'] == gr), sum(1 for b in ALL if b['score_band'] == gr)) for gr in BAND_ORDER]
SR = {gr: round(100 * h / t) for gr, h, t in SHARE}
C.check(SR['A'] <= SR['B'] <= SR['C'] <= SR['D'] <= SR['F'], 'share with 20g+ protein never falls with a step down in grade')
MED_P = sorted(P(b) for b in ALL)[NT // 2]

# Bar Finder parity: ?protein=20 (Min Protein slider; skipped on an empty field, none are empty)
def finder_match(b):
    v = num(b.get('Protein (g)'))
    return v is None or v >= 20
C.check({b['Key'] for b in ALL if finder_match(b)} == {b['Key'] for b in Q}, 'Bar Finder protein=20 returns exactly the guide set')
FINDER_HREF = '/bar-finder?protein=20'

def by_brand(brand, bars=ALL): return [b for b in bars if b['Brand Name'] == brand]
def yes(field): return lambda b: b.get(field) == 'Yes'

# ---------------------------------------------------------------------------
# Best 10
# ---------------------------------------------------------------------------
WHEY_RX = re.compile(r'\bwhey\b[^,;()\[\]]*', re.I)
def whey(b): return bool(WHEY_RX.search(ingr(b)))
def whey_name(b): return WHEY_RX.search(ingr(b)).group(0).strip().lower()
def tie_tail(c): return f", and it wins the tie on {c['tie_on']}." if c['tied'] and c['tie_on'] != 'name' else "."
LOW_SUGAR = Slot('Lowest sugar', 'The least sugar among bars with no sugar alcohol (none in the ingredients and 0g on the '
                 'label), grade B or better.',
                 lambda E: [b for b in E if not sa_any(b)], lambda b: (SUG(b),) + tie_chain(b),
                 lambda b, c: (f"{fnum(SUG(b))}g sugar and no sugar alcohol, with {fnum(P(b))}g protein in {fnum(CAL(b))} "
                               f"calories, {c['tied']}the lowest sugar of any bar here without a sugar alcohol" + tie_tail(c)),
                 metric=SUG)
FIBER = Slot('Highest fiber', 'The most fiber, grade B or better.', lambda E: E,
             lambda b: (-FIB(b),) + tie_chain(b),
             lambda b, c: (f"{fnum(FIB(b))}g fiber, {c['tied']}the most of any bar here, with {fnum(P(b))}g protein in "
                           f"{fnum(CAL(b))} calories."),
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
                             else "one of the protein sources our scoring rates near the top."), floor=20),
    slot_subset('Best plant-based', 'Labeled vegan by the brand.', yes('Vegan (Y/N)'),
                lambda b: 'Labeled vegan, so all of the protein comes from plants.', floor=20),
    LOW_SUGAR,
    slot_subset('Best gluten-free', 'Labeled gluten free by the brand.', yes('Gluten Free (Y/N)'),
                lambda b: 'Labeled gluten free by the brand.', floor=20),
]
FALLBACKS = [FIBER, slot_subset('Best dairy-free', 'Labeled dairy free by the brand.', yes('Dairy Free (Y/N)'),
                                lambda b: 'Labeled dairy free by the brand.', floor=20)]
PICKS = pick_best10(Q, SLOTS, FALLBACKS, floor=20)
C.check(len(PICKS) == 10, 'ten Best 10 picks available')
C.check([s.label for s, *_ in PICKS] == [s.label for s in SLOTS], 'all ten planned slots filled without fallbacks')
C.check(not any(re.search(r'score \d|scored? \d', w) for _s, _b, w, _n in PICKS), 'no ingredient score printed in a pick')
PK = {s.label: b for s, b, _w, _n in PICKS}
C.check(not WHEY_RX.search(ingr(PK['Best plant-based'])) and 'milk' not in ingr(PK['Best plant-based']).lower(),
        'the plant-based pick names no whey or milk')
B10_INTRO = ("Ten bars with 20g or more protein, each the winner of one thing people shop for. Every pick has an A or B "
             "ingredient grade, and no bar appears twice.")

# ---------------------------------------------------------------------------
# What it means
# ---------------------------------------------------------------------------
CARDS = '\n'.join([
    v2_count_card_html('Over 250 calories', OVER250, N,
                       'More protein often comes with a bigger bar. Past 250 calories, a bar is closer to a small meal.'),
    v2_count_card_html('Contains a sugar alcohol', Q_SA, N,
                       'The usual way a high protein bar keeps its sugar line low. Some people get bloating or stomach upset from them.'),
    v2_count_card_html('Contains an artificial sweetener', Q_ART, N,
                       'Sucralose in every case, sometimes with acesulfame potassium.'),
    v2_count_card_html('Collagen is the main protein', COLLAGEN, N,
                       'Collagen counts toward the protein number on the label, but it is missing an essential amino acid.'),
])
SRC_ROWS = '\n'.join(f'          <li><strong>{esc(n)}:</strong> {c} bars</li>' for n, c in LEAD.most_common() if n)
MEANS = f'''
    <div class="section-inner">
      <h2 class="section-title">What counts as a high protein bar</h2>
      <div class="section-body">
        <p>We draw the line at 20g of protein per bar. Most bars don't get there: the middle bar in our database has {fnum(MED_P)}g. At 20g a bar carries about as much protein as a small meal, which is what most people mean when they shop for a high protein bar.</p>
        <p>Getting to 20g usually takes a concentrated protein (whey, milk protein, soy) and something to make it taste good without sugar. That is where these bars run into trouble. Here is how often the {comma(N)} high protein bars carry the things people try to avoid.</p>
      </div>
      <div class="score-grid" style="margin-top:1.5rem;">
{CARDS}
      </div>
      <h3 class="kt-h3">Where the protein comes from</h3>
      <div class="section-body">
        <p>The first protein named on the label, across the {comma(N)} bars with 20g or more:</p>
        <ul class="criteria-list">
{SRC_ROWS}
        </ul>
        <p>Whey, milk protein, soy and egg whites are complete proteins. Pea and rice protein are often paired to round each other out. Collagen is the exception: it raises the protein number but lacks tryptophan, an essential amino acid, so our scoring rates it the weakest of the positive protein sources. Whey isolate and egg whites rate highest.</p>
      </div>
      <h3 class="kt-h3">High protein doesn't screen on ingredient grade</h3>
      <div class="section-body">
        <p>This list is about one number, so {LOW} of the {N} bars that qualify grade C or below. Every bar in the Best 10 grades A or B, and the list further down puts A and B bars first.</p>
      </div>
    </div>
'''

# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------
INSIGHTS = [
    ('More protein, lower grades.',
     f"Only {pct0(AB, N)}% of bars with 20g+ protein grade A or B, against {pct0(DB_AB, NT)}% of the whole database. "
     f"{pct0(len(Q_ART), N)}% use an artificial sweetener ({pct0(len(DB_ART), NT)}% across all bars) and "
     f"{pct0(len(Q_SA), N)}% a sugar alcohol."),
    ('The extra protein brings extra calories.',
     f"Bars with 20g+ protein average {fnum(round(AVG_CAL_Q))} calories, against {fnum(round(AVG_CAL_D))} for the rest. "
     f"{len(OVER250)} of the {N} are over 250 calories."),
    ('The biggest numbers come with the worst grades.',
     f"The most protein in any bar we track is {fnum(P(MOST))}g ({full(MOST)}, {fnum(CAL(MOST))} calories, grade "
     f"{MOST['score_band']}). All {len(P30)} bars with 30g or more grade C or below. The most protein in an A or B bar is "
     f"{fnum(P(TOP_AB))}g."),
]
FINDINGS = findings_v2_html(f'What we found screening {DB_PUBLIC} bars', INSIGHTS,
                            grade_share_chart_html(SHARE, title='Share of bars with 20g+ protein, by ingredient grade',
                                                   note=f'Out of the {DB_PUBLIC} bars in our database.'))

# ---------------------------------------------------------------------------
# Brands that do it well + big brands
# ---------------------------------------------------------------------------
WELL = brands_well_rows(ALL, QF, n=8)
C.check(sum(r['big'] for r in WELL) >= 1 and sum(not r['big'] for r in WELL) >= 2, 'brands-well has a big and 2+ small brands')
def well_why(r):
    lead = (f"All {r['total']} flavors have 20g+" if r['q'] == r['total'] else
            f"{r['q']} of {r['total']} flavors {'has' if r['q'] == 1 else 'have'} 20g+")
    gm = r['grades']
    grades = (f"graded {next(iter(gm))}" if r['q'] == 1 else
              f"all {next(iter(gm))} grade" if len(gm) == 1 else grade_mix_text(gm) + ' grade')
    bp = best_pick(r['qual'])
    return f"{lead}, {grades}. Best pick: {bp['Flavor Name']} ({bp['score_band']}, {fnum(P(bp))}g protein, {fnum(CAL(bp))} cal)."
BRANDS_WELL = brands_well_html(WELL, well_why, h2='Brands that do it well',
                               intro='Brands with at least 3 bars in our database, ranked by how much of their lineup has 20g+ '
                                     'protein and how well those bars grade.')

def big_verdict(r):
    bp = best_pick(r['qual'])
    pick = f" Best pick: {bp['Flavor Name']} ({bp['score_band']}, {fnum(P(bp))}g protein, {fnum(CAL(bp))} cal)." if bp else ''
    if r['q'] == r['total']:
        return 'Every flavor has 20g+.' + pick
    if r['q'] == 0:
        top = max(r['bars'], key=P)
        return f"None reach 20g. The most is {fnum(P(top))}g ({top['Flavor Name']})."
    verb = 'has' if r['q'] == 1 else 'have'
    return f"{'Only ' if r['q'] * 2 < r['total'] else ''}{r['q']} of {r['total']} {verb} 20g+." + pick
BIG_HTML, BIG_ROWS = big_brands_html(
    ALL, QF, big_verdict, h2='How do the big brands fare on protein?',
    intro=('Every brand with national grocery, big-box or Costco distribution, with how many of its bars have 20g or more '
           'protein. Brand names link to our full reviews where we have one.'))

# ---------------------------------------------------------------------------
# Top 50 + Bar Finder CTA + criteria
# ---------------------------------------------------------------------------
T50 = top50_rows(Q, 50)
C.check(len(T50) == 50 and all(b['score_band'] in ('A', 'B') for b in T50), 'Top 50 is all A/B')
TOP50 = top50_html(T50, h2='Top 50 high protein bars',
                   intro='Ranked by ingredient grade first, then by protein per calorie. Tap any row for nutrition facts and '
                         'the full ingredient list.')
FINDER = finder_cta_html(N, FINDER_HREF, desc=('The Bar Finder opens with Min Protein set to 20g, the same line as this page. '
                                               'Add your own filters for grade, calories, sugar, certifications, or ingredients '
                                               'to exclude.'))
CRITERIA = criteria_html(qualify_rule=(f'20g or more protein per bar. No grade check on the list itself. {comma(N)} of the '
                                       f'{DB_PUBLIC} bars we track qualify.'), picks=PICKS)

# ---------------------------------------------------------------------------
# FAQ
# ---------------------------------------------------------------------------
def brand_faq(name):
    bars = by_brand(name)
    C.check(bars, f'{name} is in bars.js')
    q = [b for b in bars if QF(b)]
    if not q:
        top = max(bars, key=P)
        return f"Not by our line: none of the {len(bars)} tracked {name} flavors have 20g of protein. The most is {fnum(P(top))}g ({top['Flavor Name']})."
    grades = grade_mix_text(Counter_(b['score_band'] for b in q))
    if len(q) == len(bars):
        return f"Yes: all {len(bars)} tracked {name} flavors have 20g or more protein. They grade {grades} on ingredients."
    verb = 'has' if len(q) == 1 else 'have'
    lo = min(P(b) for b in bars if not QF(b))
    return (f"Mostly: {len(q)} of {len(bars)} tracked {name} flavors {verb} 20g or more protein ({grades} grade). The rest "
            f"have {fnum(lo)}g to {fnum(max(P(b) for b in bars if not QF(b)))}g.") if len(q) * 2 >= len(bars) else (
            f"Only {len(q)} of {len(bars)} tracked {name} flavors {verb} 20g or more protein ({grades} grade).")
BEST = PK['Best overall']
HPK = PK['Highest protein']
FAQS = [
    ('How much protein should a protein bar have?',
     f'It depends on what the bar is for. As a snack, 10g to 15g is common; the middle bar in our database has {fnum(MED_P)}g. '
     'We call 20g or more high protein, about what a small meal gives you. '
     f'{of_db(N, NT)} bars reach it.'),
    ('What is the best high protein bar?',
     f"By our rules, {full(BEST)}: {BEST['score_band']}-grade ingredients, {fnum(P(BEST))}g protein in {fnum(CAL(BEST))} "
     f"calories. For the most protein at 300 calories or less with an A or B grade, {full(HPK)} has {fnum(P(HPK))}g in "
     f"{fnum(CAL(HPK))} calories."),
    ('Which protein bar has the most protein?',
     f"Of the bars we track, {full(MOST)} with {fnum(P(MOST))}g in {fnum(CAL(MOST))} calories. It grades {MOST['score_band']} "
     f"on ingredients, and every bar with 30g or more grades C or below. The most protein in an A or B bar is "
     f"{fnum(P(TOP_AB))}g ({full(TOP_AB)}, {fnum(CAL(TOP_AB))} calories)."),
    ('Are high protein bars healthy?',
     f"Many aren't, by ingredients. Only {pct0(AB, N)}% of bars with 20g+ protein grade A or B, against {pct0(DB_AB, NT)}% of "
     f"all bars, and {pct0(len(Q_SA), N)}% use a sugar alcohol to keep sugar down. The protein itself is fine. Check the "
     "grade and the calories, not just the protein number."),
    ('Do high protein bars have more calories?',
     f"On average, yes: {fnum(round(AVG_CAL_Q))} calories for bars with 20g+ protein, against {fnum(round(AVG_CAL_D))} for "
     f"the rest. Protein per 100 calories is the fairer comparison; our Most protein per calorie pick, "
     f"{full(PK['Most protein per calorie'])}, has {fnum(p100(PK['Most protein per calorie']))}g per 100 calories."),
    ('Is collagen protein as good as whey?',
     'Not for building muscle. Collagen is missing tryptophan, an essential amino acid, so it is an incomplete protein. It '
     f'still counts toward the protein number on the label. {len(COLLAGEN)} of the {N} high protein bars use collagen as their '
     'main protein. Our scoring rates whey isolate and egg whites highest and collagen the weakest of the positive sources.'),
    ('Are Quest bars high protein?', brand_faq('Quest')),
    ('Are Barebells high protein?', brand_faq('Barebells')),
    ('Are David protein bars high protein?', brand_faq('David')),
    ('How many protein bars in your database have 20g of protein or more?',
     f'Out of {DB_PUBLIC} bars, {N} have 20g or more, about {pct0(N, NT)}%. {AB} of them grade A or B on ingredients.'),
]

# ---------------------------------------------------------------------------
# Regions
# ---------------------------------------------------------------------------
H1 = 'The 10 Best High Protein Bars'
TITLE = f'10 Best High Protein Bars, 20g+ ({DB_PUBLIC} Checked)'
DESC = (f'{N} of {DB_PUBLIC} protein bars have 20g+ protein, but only {AB} grade A or B on ingredients. Our 10 best high '
        'protein bars, picked by published rules.')
OG_DESC = (f'We checked {DB_PUBLIC} protein bars. {comma(N)} have 20g or more protein, and most of those grade C or below. '
           'Here are the 10 best, each picked by a published rule.')
C.check(len(DESC) <= 155, f'meta description under 155 characters ({len(DESC)})')
FAQS_PLAIN = [(q, plain_text(a)) for q, a in FAQS]
REGIONS = v2_head_regions(title=TITLE, h1=H1, desc=DESC, og_desc=OG_DESC, url=URL, about='High Protein Snacks',
                          published=PUBLISHED, faqs=FAQS_PLAIN, picks=PICKS)
EDITORIAL = f'  <section class="section off" id="what-it-means">{MEANS}  </section>'
HERO = (f'<h1 class="hero-title">{esc(H1)}</h1>\n'
        f'    <p class="hero-sub">A high protein bar here means 20g of protein or more per bar, about what a small meal gives '
        f'you. Most bars fall short: the middle bar in our database has {fnum(MED_P)}g.</p>\n'
        f'    <p class="hero-sub">Of the {DB_PUBLIC} bars we track, {comma(N)} reach 20g, but only {AB} of those grade A or B '
        f'on ingredients. Getting to 20g usually takes a sugar alcohol or an artificial sweetener, and more calories. '
        f'These are the 10 best by our rules.</p>')
REGIONS += [
    ('hero', HERO),
    ('best10', best10_html(PICKS, h2='Best 10 high protein bars', intro=B10_INTRO)),
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
        ('/weight-loss-protein-bars', 'Protein Bars for Weight Loss', '15g+ protein in 200 calories or less, with low sugar and real fiber.'),
        ('/clean-protein-bars', 'Clean Protein Bars', 'A or B grade, no artificial sweeteners, no processed oils.'),
        ('/no-artificial-sweeteners', 'No Artificial Sweeteners', 'Bars without sucralose or acesulfame potassium.'),
    ])),
]

if __name__ == '__main__':
    C.stop_if_failed()
    page = build_guide_page_v2(PAGE, REGIONS, ALL, C, picks=PICKS)
    size = len(page.encode('utf-8'))
    faq_at = len(page[:page.find('<section class="guide-faq"')].encode('utf-8'))
    print(f'{PAGE}: {N} qualify ({AB} A/B), {ND} under 20g, {size:,} bytes, FAQ at byte {faq_at:,}')
    print(f'  share by grade {SR}; lead {LEAD.most_common()}; most {full(MOST)} {P(MOST)}; top A/B {full(TOP_AB)} {P(TOP_AB)}')
    for i, (s_, b, why, n) in enumerate(PICKS, 1):
        print(f'  {i:2d}. {s_.label}: {full(b)} ({b["score_band"]}) [pool {n}]')
        print(f'      {why}')
