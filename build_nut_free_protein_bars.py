#!/usr/bin/env python3
"""Build nut-free-protein-bars.html from bars.js. GUIDE PAGE v2 ("Best" list).

Run from the repo root:  python3 build_nut_free_protein_bars.py

New guide (2026-10-23, Jeff). Layout and every rule: claude/GUIDE_PAGE_SPEC_V2.md
and the v2 section of kyb_guide_lib.py. The page was started from a copy of
gluten-free-protein-bars.html (head, nav and footer as deployed, canonical and
og:url changed); every region below is generated. Every number, pick and brand
row comes from bars.js. Copy that depends on a fact is checked; if one stops
being true the build stops and lists it. Ingredient quality is shown and ranked
as a GRADE only.

Screen: GUIDE_FILTERS['nut-free-protein-bars'] = `Nut Free (Y/N)` is Yes
(certification field, no macro or grade gate). Bar Finder:
/bar-finder?certs=Nut%20Free (same field). Peanuts and tree nuts are counted by
ingredient text over the bars that are not labeled nut free, ignoring "may
contain" / shared-facility statements. A nut-free-labeled bar whose own
ingredients name a peanut or tree nut is a build failure. Coconut is not
counted as a tree nut (FDA dropped it from the tree nut list in January 2025).

Small guide: only a few brands make nut-free bars, so with the grade, protein
and two-per-brand rules the list holds N_PICKS picks (10 at most) and says so.
Guide slots: Best plant-based, Best gluten-free, Best dairy-free, Highest fiber.
Fallbacks: Lowest sugar (no sugar alcohol), then Best soy-free.
Health-adjacent guide: keeps the "We are not doctors or dietitians" line.
"""
import re
from kyb_guide_lib import *

PAGE = 'nut-free-protein-bars.html'
URL = 'https://knowyourbar.com/nut-free-protein-bars'
PUBLISHED = '2026-10-23'
set_tie_seed('nut-free-protein-bars')

ALL = load_bars()
QF = GUIDE_FILTERS['nut-free-protein-bars']
Q = [b for b in ALL if QF(b)]
D = [b for b in ALL if not QF(b)]
N, ND, NT = len(Q), len(D), len(ALL)
BRANDS_Q = len({b['Brand Name'] for b in Q})
GR_Q = {g: sum(1 for b in Q if b.get('score_band') == g) for g in BAND_ORDER}
C = Claims()
C.check(not any(b.get('Nut Free (Y/N)') not in ('Yes', None) for b in ALL), 'Nut Free field is only Yes or blank')
DISCLAIMER = ("We are not doctors or dietitians. These are the qualities we know people look for, so that's what we "
              "factored in.")

PEANUT = r'\bpeanuts?\b|peanut (?:butter|flour|oil|protein)'
TREE = r'almond|cashew|hazelnut|filbert|walnut|pecan|pistachio|macadamia|brazil nut|pine nut|\btree nuts?\b'
def label_text(b):
    return re.split(r'may contain|manufactured (?:in|on)|processed (?:in|on)|produced (?:in|on)|made in a facility|in a facility',
                    ingr(b), flags=re.I)[0]
def has_peanut(b): return bool(re.search(PEANUT, label_text(b), re.I))
def has_tree(b): return bool(re.search(TREE, label_text(b), re.I))
def has_nut(b): return has_peanut(b) or has_tree(b)
for b in Q:
    C.check(not has_nut(b), f'{full(b)} is labeled nut free and names no peanut or tree nut')
PEANUTS = [b for b in D if has_peanut(b)]
TREES = [b for b in D if has_tree(b)]
NAMED = [b for b in D if has_nut(b)]
UNLABELED = [b for b in D if not has_nut(b)]
COCONUT = [b for b in Q if re.search(r'coconut', ingr(b), re.I)]
SUNBUTTER = [b for b in Q if re.search(r'sunflower (?:seed )?butter|sunbutter', ingr(b), re.I)]
SEED = [b for b in Q if re.search(r'pumpkin seed|sunflower seed|chia|flax|hemp|watermelon seed|sesame', ingr(b), re.I)]
C.check(len(TREES) > len(PEANUTS), 'tree nuts are named more often than peanuts')
C.check(len(NAMED) > len(UNLABELED), 'most bars without the label name a peanut or tree nut')
C.check(len(SEED) * 2 > N, 'most nut free bars use seeds')
def link(href, text): return f'<a href="{href}">{text}</a>'

# ---------------------------------------------------------------------------
# Best list
# ---------------------------------------------------------------------------
def plant_based(b): return b.get('Vegan (Y/N)') == 'Yes'
def gluten_free(b): return b.get('Gluten Free (Y/N)') == 'Yes'
def dairy_free(b): return b.get('Dairy Free (Y/N)') == 'Yes'
def soy_free(b): return b.get('Soy Free (Y/N)') == 'Yes'
LOW_SUGAR = Slot('Lowest sugar', 'The least sugar among bars with no sugar alcohol, grade B or better, 10g+ protein.',
                 lambda E: [b for b in E if not has_sugar_alcohol(b)], lambda b: (SUG(b),) + tie_chain(b),
                 lambda b, c: (f"{fnum(SUG(b))}g sugar with {fnum(P(b))}g protein and no sugar alcohol, {c['tied']}the lowest "
                               "sugar of any bar here without one."),
                 metric=SUG)
SLOTS = [
    slot_best_overall(15),
    slot_cleanest(),
    slot_highest_protein(300),
    slot_protein_per_cal(12),
    slot_lowest_calorie(),
    slot_big_brand(),
    slot_subset('Best plant-based', 'Vegan-labeled bars.', plant_based, lambda b: 'Vegan and labeled nut free.'),
    slot_subset('Best gluten-free', 'Bars also labeled gluten free.', gluten_free,
                lambda b: 'Labeled both nut free and gluten free.'),
    slot_subset('Best dairy-free', 'Bars also labeled dairy free.', dairy_free,
                lambda b: 'Labeled both nut free and dairy free.'),
    slot_highest_fiber(),
]
FALLBACKS = [
    LOW_SUGAR,
    slot_subset('Best soy-free', 'Bars also labeled soy free.', soy_free, lambda b: 'Labeled both nut free and soy free.'),
]
PICKS = pick_best10(Q, SLOTS, FALLBACKS)
N_PICKS = len(PICKS)
E = v2_eligible(Q, 10)
max_possible = sum(min(V2_BRAND_CAP, n) for n in Counter_(b['Brand Name'] for b in E).values())
C.check(N_PICKS == min(10, max_possible), f'the list holds as many picks as the rules allow ({min(10, max_possible)})')
C.check(not any(re.search(r'score \d|scored? \d', w) for _s, _b, w, _n in PICKS), 'no ingredient score printed in a pick')
PK = {s.label: b for s, b, _w, _n in PICKS}
BEST = PK['Best overall']
NB = num_word(N_PICKS) if N_PICKS < 10 else 'Ten'
B10_INTRO = (f"{NB.capitalize()} nut free bars, each the winner of one thing people shop for. Every pick is labeled nut free, has "
             "an A or B ingredient grade and at least 10g of protein, and no bar appears twice."
             + ('' if N_PICKS == 10 else f" Only {BRANDS_Q} brands make nut free bars, so the rules allow {N_PICKS} picks, not 10."))

# ---------------------------------------------------------------------------
# What it means
# ---------------------------------------------------------------------------
MEANS = f'''
    <div class="section-inner">
      <h2 class="section-title">What makes a protein bar nut free</h2>
      <div class="section-body">
        <p>We use the Nut Free (Y/N) label on file for every bar: the brand says the bar is free of peanuts and tree nuts. Then we read every ingredient list ourselves. {of_db(N, NT)} bars, about {pct0(N, NT)}%, carry the label, and none of those {comma(N)} names a peanut or a tree nut in its ingredients.</p>
        <p>Of the {comma(ND)} bars without the label, {len(TREES)} name a tree nut (almonds, cashews, hazelnuts and the like) and {len(PEANUTS)} name peanuts. Nuts are the default protein-and-fat base for bars, which is why so few are nut free. The other {len(UNLABELED)} don't name a nut at all, but they aren't labeled either, and a label is what tells you a brand has checked for cross-contact.</p>
      </div>
      <div class="score-grid" style="margin-top:1.5rem;">
{v2_count_card_html('Tree nuts', TREES, NT, 'Almonds, cashews, hazelnuts, walnuts, pecans, pistachios, macadamias: whole, as a butter or flour, or in a coating.')}
{v2_count_card_html('Peanuts', PEANUTS, NT, 'Peanuts are legumes, not tree nuts, but they are a major allergen and the most common single nut in bars, usually as peanut butter or peanut flour.')}
{v2_count_card_html('No nut named, not labeled', UNLABELED, NT, "No peanut or tree nut shows up in the ingredient list, but the brand hasn't labeled the bar nut free. Without the label you don't know about shared equipment.", names=[])}
      </div>
      <h3 class="kt-h3">What about coconut?</h3>
      <div class="section-body">
        <p>Coconut is a fruit. The FDA dropped it from its list of tree nuts for allergen labeling in January 2025, and most people with a tree nut allergy can eat it. {len(COCONUT)} of the {comma(N)} nut free bars here contain coconut, so check the label if coconut is a problem for you.</p>
      </div>
      <div class="callout-box">{DISCLAIMER} If you have a severe allergy, check the package and the brand's allergen statement every time you buy.</div>
    </div>
'''

# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------
def ab_share(bars): return pct0(sum(1 for b in bars if b.get('score_band') in ('A', 'B')), len(bars))
C.check(sum(1 for b in Q if b['score_band'] in 'AB') / N > sum(1 for b in ALL if b['score_band'] in 'AB') / NT,
        'nut free bars grade A or B more often than the database')
C.check(avg(Q, 'Protein (g)') < avg(ALL, 'Protein (g)'), 'nut free bars average less protein')
TOPB = Counter_(b['Brand Name'] for b in Q).most_common(1)[0]
INSIGHTS = [
    ('Nut free is rare.',
     f'Only {of_db(N, NT)} bars ({pct0(N, NT)}%) carry a nut free label, from {BRANDS_Q} brands. {TOPB[0]} alone makes '
     f'{TOPB[1]} of them.'),
    ('Seeds do the work nuts usually do.',
     f'{len(SEED)} of the {comma(N)} nut free bars use seeds such as sunflower, pumpkin, chia or flax in place of nuts'
     + (f', and {len(SUNBUTTER)} use sunflower seed butter instead of a nut butter.' if SUNBUTTER else '.')),
    ('They grade better, with a little less protein.',
     f"{ab_share(Q)}% of nut free bars grade A or B, against {ab_share(ALL)}% database-wide. They average "
     f"{fnum(round(avg(Q, 'Protein (g)'), 1))}g of protein against {fnum(round(avg(ALL, 'Protein (g)'), 1))}g."),
]
GRADE_ROWS = [(g, sum(1 for b in Q if b['score_band'] == g), sum(1 for b in ALL if b['score_band'] == g)) for g in BAND_ORDER]
FINDINGS = findings_v2_html(f'What we found screening {DB_PUBLIC} bars', INSIGHTS,
                            grade_share_chart_html(GRADE_ROWS, title='Share of bars labeled nut free, by ingredient grade',
                                                   note=f'Out of the {DB_PUBLIC} bars in our database.'))

# ---------------------------------------------------------------------------
# Brands that do it well + big brands
# ---------------------------------------------------------------------------
WELL = brands_well_rows(ALL, QF, n=8)
C.check(len(WELL) >= 4, 'at least four brands for the brands-well table')
def well_why(r):
    lead = f"All {r['total']} flavors are nut free" if r['q'] == r['total'] else f"{r['q']} of {r['total']} flavors are nut free"
    g = r['grades']
    grades = f"all {next(iter(g))} grade" if len(g) == 1 else grade_mix_text(g) + ' grade'
    bp = best_pick(r['qual'])
    return (f"{lead}, {grades}." + (f" Best pick: {bp['Flavor Name']} ({bp['score_band']}, {fnum(P(bp))}g protein, "
                                    f"{fnum(CAL(bp))} cal)." if bp else ''))
BRANDS_WELL = brands_well_html(WELL, well_why, h2='Brands that do it well',
                               intro='Brands with at least 3 bars in our database, ranked by how much of their lineup is labeled '
                                     'nut free and how well those bars grade. No brand with national grocery distribution makes '
                                     'the list, so these are all smaller independents.')
C.check(not any(r['big'] for r in WELL), 'no big brand is in the brands-well table')

def big_verdict(r):
    disq = [b for b in r['bars'] if not QF(b)]
    t = sum(1 for b in disq if has_tree(b))
    p = sum(1 for b in disq if has_peanut(b))
    none = sum(1 for b in disq if not has_nut(b))
    if r['q'] == r['total']:
        return 'Every flavor is labeled nut free.'
    parts = []
    if t:
        parts.append(f"{t} list{'s' if t == 1 else ''} a tree nut")
    if p:
        parts.append(f"{p} list{'s' if p == 1 else ''} peanuts")
    if none:
        parts.append(f"{none} name{'s' if none == 1 else ''} no nut but {'isn' if none == 1 else 'aren'}'t labeled")
    lead = 'None are labeled nut free' if r['q'] == 0 else f"{r['q']} of {r['total']} are labeled nut free"
    return f"{lead}: {names_and(parts)}." if parts else f'{lead}.'
BIG_HTML, BIG_ROWS = big_brands_html(
    ALL, QF, big_verdict, h2='How do the big brands fare on nut free?',
    intro=('Every brand with national grocery, big-box or Costco distribution, with how many of its bars are labeled nut free. '
           'Brand names link to our full reviews where we have one.'))
BIG_Q = sum(1 for b in Q if is_big(b))
C.check(BIG_Q == 0, 'no big-brand bar is labeled nut free')
BB = [b for b in ALL if b['Brand Name'] == 'Barebells']
BB_NUT = [b for b in BB if has_nut(b)]
C.check(BB and not any(QF(b) for b in BB), 'no Barebells flavor is labeled nut free')

# ---------------------------------------------------------------------------
# All bars list + Bar Finder CTA + criteria
# ---------------------------------------------------------------------------
T50 = top50_rows(Q, min(N, 50))
TOP50 = top50_html(T50, h2=(f'All {N} nut free protein bars' if N <= 50 else 'Top 50 nut free protein bars'),
                   intro='Ranked by ingredient grade first, then by protein per calorie. Tap any row for nutrition facts and '
                         'the full ingredient list.')
FINDER_HREF = '/bar-finder?certs=Nut%20Free'
FINDER = finder_cta_html(N, FINDER_HREF, desc=('The Bar Finder opens with the Nut Free filter already on, the same label this '
                                               'guide uses. Add your own filters for protein, sugar, calories, grade, brand, '
                                               'other certifications, or ingredients to exclude.'))
CRITERIA = criteria_html(
    qualify_rule=('The brand labels the bar nut free (the Nut Free field in our database). We also read every ingredient list for '
                  'peanuts and tree nuts, to explain why the rest miss. Coconut does not count as a tree nut. '
                  f'{comma(N)} of the {DB_PUBLIC} bars we track qualify.'),
    picks=PICKS, n_spots=N_PICKS)

# ---------------------------------------------------------------------------
# FAQ
# ---------------------------------------------------------------------------
HP = max((b for b in Q if b['score_band'] in 'AB'), key=lambda b: (P(b), -CAL(b)))
FAQS = [
    ('What makes a protein bar nut free on this site?',
     f'We use the Nut Free (Y/N) label on file for each bar, which means the brand says it is free of peanuts and tree nuts. '
     f'{of_db(N, NT, True)} bars we track carry that label, and none of them names a peanut or tree nut in its ingredients.'),
    ('What is the best nut free protein bar?',
     f"By our rules, {full(BEST)}: {BEST['score_band']}-grade ingredients, {fnum(P(BEST))}g protein, {fnum(CAL(BEST))} calories "
     f"and {fnum(SUG(BEST))}g sugar. For the most protein, {full(HP)} has {fnum(P(HP))}g in {fnum(CAL(HP))} calories."),
    ('How many nut free protein bars are there?',
     f"{of_db(N, NT, True)} bars we track are labeled nut free, about {pct0(N, NT)}%, from {BRANDS_Q} brands. "
     f"{GR_Q['A']} of them grade A for ingredient quality."),
    ('Is coconut a tree nut?',
     f"Not for labeling. The FDA removed coconut from its list of tree nuts in January 2025. {len(COCONUT)} of the {comma(N)} "
     "nut free bars here contain coconut, so check the label if you avoid it."),
    ('Are peanuts tree nuts?',
     f"No, peanuts are legumes. They are still a major allergen, and the nut free labels we track cover them: none of the "
     f"{comma(N)} nut free bars lists peanuts. {len(PEANUTS)} of the bars without the label do."),
    ('Are Barebells nut free?',
     f"No. None of the {len(BB)} Barebells flavors we track is labeled nut free, and {len(BB_NUT)} list peanuts or tree nuts "
     "in their ingredients."),
    ("If a bar's ingredients don't list nuts, is it safe for a nut allergy?",
     f"Not necessarily. {len(UNLABELED)} bars we track name no peanut or tree nut but aren't labeled nut free, which usually "
     f"means the brand hasn't ruled out shared equipment. {DISCLAIMER} With an allergy, check the package and the brand's "
     "allergen statement every time you buy."),
    ('Do nut free protein bars have less protein?',
     f"A little. Nut free bars average {fnum(round(avg(Q, 'Protein (g)'), 1))}g of protein against "
     f"{fnum(round(avg(ALL, 'Protein (g)'), 1))}g database-wide, but they grade A or B more often ({ab_share(Q)}% vs. "
     f"{ab_share(ALL)}%)."),
    ('How often is this list updated?',
     'We update the database whenever new bars are added or a brand reformulates. Manufacturers do change their ingredient '
     'lists and allergen statements over time, so always confirm against the packaging in front of you.'),
]

# ---------------------------------------------------------------------------
# Regions
# ---------------------------------------------------------------------------
H1 = f'The {N_PICKS} Best Nut Free Protein Bars'
TITLE = f'{N_PICKS} Best Nut Free Protein Bars (Peanut and Tree Nut Free)'
C.check(len(TITLE) <= 60, f'title under 60 characters ({len(TITLE)})')
DESC = (f'Only {N} of {DB_PUBLIC} protein bars are labeled nut free. We read every label for peanuts and tree nuts. '
        f'Here are the {N_PICKS} best.')
OG_DESC = (f'{comma(N)} nut free protein bars, checked against the label and the ingredient list. Here are the {N_PICKS} best, '
           'each picked by a published rule.')
C.check(len(DESC) <= 155, f'meta description under 155 characters ({len(DESC)})')
FAQS_PLAIN = [(q, plain_text(a)) for q, a in FAQS]
REGIONS = v2_head_regions(title=TITLE, h1=H1, desc=DESC, og_desc=OG_DESC, url=URL, about='Nut Free Protein Bars',
                          published=PUBLISHED, faqs=FAQS_PLAIN, picks=PICKS)
EDITORIAL = f'  <section class="section off" id="what-it-means">{MEANS}  </section>'
HERO = (f'<h1 class="hero-title">{esc(H1)}</h1>\n'
        f'    <p class="hero-sub">Most protein bars are built on nuts: almonds, cashews, peanut butter. If you or your kids avoid '
        f'peanuts and tree nuts, the choice gets small fast. We use the nut free label on every bar, then read the ingredient '
        f'list ourselves.</p>\n'
        f'    <p class="hero-sub">Of the {DB_PUBLIC} bars we track, only {comma(N)} are labeled nut free, from {BRANDS_Q} brands. '
        f'Here are the {N_PICKS} best, each picked by a published rule.</p>')
REGIONS += [
    ('hero', HERO),
    ('best10', best10_html(PICKS, h2=f'Best {N_PICKS} nut free protein bars', intro=B10_INTRO)),
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
        ('/gluten-free-protein-bars', 'Gluten Free Protein Bars',
         f"{comma(guide_count(ALL, 'gluten-free-protein-bars'))} bars labeled gluten free, checked for wheat and barley."),
        ('/dairy-free-protein-bars', 'Dairy Free Protein Bars', 'Bars labeled dairy free, checked for whey, casein and milk.'),
        ('/vegan-protein-bars', 'Vegan Protein Bars',
         f"{comma(guide_count(ALL, 'vegan-protein-bars'))} bars with no whey, milk, honey, egg, or gelatin."),
    ])),
]

if __name__ == '__main__':
    page = build_guide_page_v2(PAGE, REGIONS, ALL, C, picks=PICKS, n_picks=N_PICKS)
    size = len(page.encode('utf-8'))
    faq_at = len(page[:page.find('<section class="guide-faq"')].encode('utf-8'))
    print(f'{PAGE}: {N} qualify, {ND} disqualified, {size:,} bytes, FAQ at byte {faq_at:,}')
    for i, (s_, b, why, n) in enumerate(PICKS, 1):
        print(f'  {i:2d}. {s_.label}: {full(b)} ({b["score_band"]}) [pool {n}]')
        print(f'      {why}')
