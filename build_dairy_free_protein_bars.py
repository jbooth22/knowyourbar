#!/usr/bin/env python3
"""Rebuild dairy-free-protein-bars.html from bars.js. GUIDE PAGE v2 ("Best 10").

Run from the repo root:  python3 build_dairy_free_protein_bars.py

Layout and every rule: claude/GUIDE_PAGE_SPEC_V2.md (locked 2026-09-29) and
the v2 section of kyb_guide_lib.py, built the same way as the other v2 guides
(closest reference: build_vegan_protein_bars.py, a certification guide). The
first run migrated the live v1 page (built by kyb_cert_guide.CertGuide) to the
v2 body (head, nav and footer kept as deployed); later runs rewrite only the
<!-- kyb:NAME --> regions. Every number, pick and brand row comes from bars.js.
Copy that depends on a fact is checked; if one stops being true the build stops
and lists it. Ingredient quality is shown and ranked as a GRADE only.

Screen: GUIDE_FILTERS['dairy-free-protein-bars'] = `Dairy Free (Y/N)` is Yes
(the brand's label). Whey, milk and casein are counted by ingredient text over
the bars without the label. A dairy-free-labeled bar whose ingredients name one
is printed as a WARNING (fix upstream in bars.js). Vegan-labeled bars without
the dairy free label are NOT counted (label-based screen, same reasoning as
CLIF Bar on the vegan guide); the page says how many there are.
Bar Finder: /bar-finder?certs=Dairy%20Free (checked key for key below).

Guide slots (picked 2026-09-30; Jeff asked for the best picks delivered without
an approval round): Best soy-free, Best non-GMO, Best gluten-free, Highest
fiber. Fallbacks: Lowest sugar, then Lowest net carbs. Whey is impossible here;
lowest sugar / net carbs would repeat IQ Bar Chocolate Mint Chip (on 3 guides).
"""
import re
from collections import Counter
from kyb_guide_lib import *

PAGE = 'dairy-free-protein-bars.html'
URL = 'https://knowyourbar.com/dairy-free-protein-bars'
PUBLISHED = '2026-09-04'
set_tie_seed('dairy-free-protein-bars')   # per-guide shuffle for exact ties (kyb_guide_lib, 2026-09-30)

ALL = load_bars()
QF = GUIDE_FILTERS['dairy-free-protein-bars']
Q = [b for b in ALL if QF(b)]
D = [b for b in ALL if not QF(b)]
N, ND, NT = len(Q), len(D), len(ALL)
BRANDS_Q = len({b['Brand Name'] for b in Q})
GR = {g: sum(1 for b in Q if b.get('score_band') == g) for g in BAND_ORDER}
C = Claims()
NC = net_carbs
C.check(not any(b.get('Dairy Free (Y/N)') not in ('Yes', None) for b in ALL), 'Dairy Free field is only Yes or blank')

NOT_PLANT_MILK = r'(?<!coconut )(?<!almond )(?<!oat )(?<!rice )(?<!soy )(?<!cashew )(?<!hemp )'
SOURCES = [  # label, regex, card description
    ('Whey', r'\bwhey\b', 'The most common dairy protein source, usually whey protein concentrate or isolate leading the ingredient list.'),
    ('Milk', NOT_PLANT_MILK + r'\bmilk\b|milkfat|butterfat|lactose|\bcheese|yogurt|\bghee\b|\bcream\b(?! of tartar)',
     'Shows up as nonfat milk, milk powder, or a milk chocolate coating, usually a moisture or flavor component rather than the main protein source.'),
    ('Casein', r'casein', 'Usually sodium or calcium caseinate, a slow-digesting milk protein added alongside or instead of whey.'),
]
RX = {l: r for l, r, _ in SOURCES}
DESC_S = {l: d for l, _, d in SOURCES}
def label_text(b):
    return re.split(r'may contain|manufactured (?:in|on)|processed (?:in|on)|produced (?:in|on)|made in a facility|in a facility', ingr(b), flags=re.I)[0]
def has_d(b, l): return bool(re.search(RX[l], label_text(b), re.I))
def any_d(b): return any(has_d(b, l) for l in RX)
HIT = {l: [b for b in D if has_d(b, l)] for l in RX}
ORDER = sorted(RX, key=lambda l: -len(HIT[l]))
NAMED = [b for b in D if any_d(b)]
UNLAB = [b for b in D if not any_d(b)]
for b in Q:
    if any_d(b) and not reviewed_ok(b, 'dairy free'):
        print(f'WARNING: {full(b)} is labeled dairy free in bars.js but its ingredients name '
              f'{", ".join(l.lower() for l in RX if has_d(b, l))}. Check the label; the page follows bars.js.')
C.check(ORDER[0] == 'Whey', 'whey is the most common named dairy source')
VEGAN_UNLAB = [b for b in D if b.get('Vegan (Y/N)') == 'Yes']
VEGAN_UNLAB_BRANDS = Counter(b['Brand Name'] for b in VEGAN_UNLAB).most_common()
C.check(len(VEGAN_UNLAB) > 50 and all(b in UNLAB for b in VEGAN_UNLAB),
        'many vegan-labeled bars lack the dairy free label, and none of them name whey, milk or casein')

# Bar Finder parity: ?certs=Dairy%20Free (app.js CERT_MAP 'Dairy Free' -> 'Dairy Free (Y/N)')
C.check({b['Key'] for b in ALL if (b.get('Dairy Free (Y/N)') or '').strip().lower() == 'yes'} == {b['Key'] for b in Q},
        'Bar Finder certs=Dairy Free returns exactly the guide set')
FINDER_HREF = '/bar-finder?certs=Dairy%20Free'

def yes(field): return lambda b: b.get(field) == 'Yes'
def by_brand(brand, bars=ALL): return [b for b in bars if b['Brand Name'] == brand]
def ab(bars): return pct0(sum(1 for b in bars if b.get('score_band') in ('A', 'B')), len(bars))

# ---------------------------------------------------------------------------
# Best 10 (spec v2)
# ---------------------------------------------------------------------------
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
    slot_subset('Best soy-free', 'Labeled soy free by the brand.', yes('Soy Free (Y/N)'),
                lambda b: 'Labeled dairy free and soy free, the two allergens most protein bars lean on.'),
    slot_subset('Best non-GMO', 'Labeled Non-GMO by the brand.', yes('Non-GMO (Y/N)'),
                lambda b: 'Labeled dairy free and Non-GMO.'),
    slot_subset('Best gluten-free', 'Labeled gluten free by the brand.', yes('Gluten Free (Y/N)'),
                lambda b: 'Labeled dairy free and gluten free, for anyone avoiding both.'),
    slot_highest_fiber(),
]
FALLBACKS = [LOW_SUGAR, LOW_NET]
PICKS = pick_best10(Q, SLOTS, FALLBACKS)
C.check(len(PICKS) == 10, 'ten Best 10 picks available')
C.check([s.label for s, *_ in PICKS] == [s.label for s in SLOTS], 'all ten planned slots filled without fallbacks')
C.check(not any(re.search(r'score \d|scored? \d', w) for _s, _b, w, _n in PICKS), 'no ingredient score printed in a pick')
PK = {s.label: b for s, b, _w, _n in PICKS}
C.check(not SOY_RX.search(ingr(PK['Best soy-free'])), 'the soy-free pick names no soy ingredient')
C.check(not any(any_d(b) for _s, b, _w, _n in PICKS), 'no Best 10 pick names whey, milk or casein')
B10_INTRO = ("Ten dairy free bars, each the winner of one thing people shop for. Every pick is labeled dairy free, has an A "
             "or B ingredient grade and at least 10g of protein, and no bar appears twice.")

# ---------------------------------------------------------------------------
# What disqualifies a bar (carried over from v1, trimmed)
# ---------------------------------------------------------------------------
VB = names_and(br for br, _n in VEGAN_UNLAB_BRANDS[:3])
DISQ = f'''
    <div class="section-inner">
      <h2 class="section-title">What disqualifies a protein bar from being dairy free</h2>
      <div class="section-body">
        <p>We check the Dairy Free (Y/N) label on file for every bar, then cross-check ingredient lists ourselves for whey, milk and casein, the three named dairy sources that show up most in the data. {of_db(N, NT)} bars, about {pct0(N, NT)}%, carry a dairy free label. The other {comma(ND)}, about {pct0(ND, NT)}%, don't.</p>
        <p>{comma(len(NAMED))} of those {comma(ND)} name whey, milk or casein. The remaining {comma(len(UNLAB))} show none of the three in their own ingredient list. They just aren't labeled dairy free, which is a different claim from actually containing dairy.</p>
      </div>
      <div class="score-grid" style="margin-top:1.5rem;">
{chr(10).join(v2_count_card_html(l, HIT[l], NT, DESC_S[l]) for l in ORDER)}
{v2_count_card_html('Not labeled dairy free', UNLAB, NT, "No whey, milk or casein shows up anywhere in the ingredient list we can find, but the brand hasn't labeled the bar dairy free either. That is a labeling gap, not proof the bar contains dairy.", names=[])}
      </div>
      <h3 class="kt-h3">What about vegan bars?</h3>
      <div class="section-body">
        <p>A vegan bar has no dairy ingredients, but {len(VEGAN_UNLAB)} vegan-labeled bars don't carry a dairy free label, including flavors from {VB}. A brand may skip the dairy free claim because of shared equipment, so we only count the label here. If you avoid dairy as an ingredient rather than for an allergy, our <a href="/vegan-protein-bars">vegan protein bars guide</a> adds those.</p>
      </div>
      <h3 class="kt-h3">Is dairy free the same as vegan?</h3>
      <div class="section-body">
        <p>No. A dairy free bar just has no whey, milk or casein. It can still contain honey, egg white protein, collagen or gelatin, none of which are vegan.</p>
      </div>
    </div>
'''

# ---------------------------------------------------------------------------
# Findings: three data findings + one chart
# ---------------------------------------------------------------------------
QU = by_brand('Quest')
QU_W = [b for b in QU if has_d(b, 'Whey')]
C.check(QU and len(QU_W) == len(QU) and not any(QF(b) for b in QU), 'every Quest flavor uses whey and none is labeled dairy free')
C.check(sum(1 for b in Q if b['score_band'] in 'AB') / N > sum(1 for b in ALL if b['score_band'] in 'AB') / NT,
        'dairy free bars grade A or B more often than the database')
C.check(avg(Q, 'Protein (g)') < avg(ALL, 'Protein (g)'), 'dairy free bars average less protein')
W = len(HIT['Whey'])
INSIGHTS = [
    ('Whey is the clearest single dairy source.',
     f"{comma(W)} bars ({pct0(W, NT)}% of the database) name whey directly"
     + (', more than milk or casein on its own.' if W > max(len(HIT['Milk']), len(HIT['Casein'])) else '.')
     + f" Quest is the pattern: all {len(QU)} flavors use whey."),
    ('Many bars without the label have no dairy we can find.',
     f"{comma(len(UNLAB))} of the {comma(ND)} bars without a dairy free label name no whey, milk or casein, and "
     f"{len(VEGAN_UNLAB)} of those are labeled vegan."),
    ('Dairy free bars grade better but carry less protein.',
     f"{ab(Q)}% of dairy free bars grade A or B, against {ab(ALL)}% database-wide. They average "
     f"{fnum(round(avg(Q, 'Protein (g)'), 1))}g of protein against {fnum(round(avg(ALL, 'Protein (g)'), 1))}g, since most "
     'whey-based bars are built to maximize protein per calorie.'),
]
GRADE_ROWS = [(g, sum(1 for b in Q if b['score_band'] == g), sum(1 for b in ALL if b['score_band'] == g)) for g in BAND_ORDER]
GRV = {g: round(100 * h / t) for g, h, t in GRADE_ROWS}
C.check(GRV['A'] > GRV['C'] and GRV['A'] > GRV['F'], 'A-grade bars are labeled dairy free more often than C and F bars')
FINDINGS = findings_v2_html(f'What we found screening {DB_PUBLIC} bars', INSIGHTS,
                            grade_share_chart_html(GRADE_ROWS, title='Share of bars labeled dairy free, by ingredient grade',
                                                   note=f'Out of the {DB_PUBLIC} bars in our database.'))

# ---------------------------------------------------------------------------
# Brands that do it well + big brands
# ---------------------------------------------------------------------------
WELL = brands_well_rows(ALL, QF, n=8)
C.check(sum(r['big'] for r in WELL) >= 2 and sum(not r['big'] for r in WELL) >= 2, 'brands-well has 2+ big and 2+ small brands')
def well_why(r):
    lead = (f"All {r['total']} flavors are dairy free" if r['q'] == r['total'] else
            f"{r['q']} of {r['total']} flavors {'is' if r['q'] == 1 else 'are'} dairy free")
    gm = r['grades']
    grades = (f"graded {next(iter(gm))}" if r['q'] == 1 else
              f"all {next(iter(gm))} grade" if len(gm) == 1 else grade_mix_text(gm) + ' grade')
    bp = best_pick(r['qual'])
    return f"{lead}, {grades}. Best pick: {bp['Flavor Name']} ({bp['score_band']}, {fnum(P(bp))}g protein, {fnum(CAL(bp))} cal)."
BRANDS_WELL = brands_well_html(WELL, well_why, h2='Brands that do it well',
                               intro='Brands with at least 3 bars in our database, ranked by how much of their lineup is labeled '
                                     'dairy free and how well those bars grade. We made sure to include both brands you can find '
                                     'at most grocery stores and smaller independents.')

def dairy_top(disq):
    c = Counter(l for b in disq for l in RX if has_d(b, l))
    return sorted(c.items(), key=lambda kv: (-kv[1], ORDER.index(kv[0])))
def big_verdict(r):
    disq = [b for b in r['bars'] if not QF(b)]
    bp = best_pick(r['qual'])
    pick = f" Best pick: {bp['Flavor Name']} ({bp['score_band']}, {fnum(P(bp))}g protein)." if bp else ''
    low_n = sum(1 for b in r['qual'] if b['score_band'] in ('C', 'D', 'F'))
    low_txt = ('' if low_n * 2 <= r['q'] else
               f" {'All' if low_n == r['q'] else 'Most'} of the dairy free ones grade C or below, so check the label.")
    if r['q'] == r['total']:
        return 'Every flavor is labeled dairy free.' + (low_txt.replace(' of the dairy free ones', '') if low_txt else pick)
    top = dairy_top(disq)
    vg = sum(1 for b in disq if b.get('Vegan (Y/N)') == 'Yes')
    if not top:
        why = ('none name whey, milk or casein, and they are labeled vegan, just not dairy free' if vg == len(disq) else
               "none name whey, milk or casein, they just aren't labeled dairy free")
    elif top[0][1] == len(disq):
        why = f'every one has {top[0][0].lower()}'
    else:
        why = f'most have {top[0][0].lower()}' if top[0][1] * 2 > len(disq) else f'{top[0][0].lower()} is the most common reason'
    if r['q'] == 0:
        return f"None are labeled dairy free: {why}."
    verb = 'is' if r['q'] == 1 else 'are'
    return (f"{'Only ' if r['q'] * 2 < r['total'] else ''}{r['q']} of {r['total']} {verb} labeled dairy free. Of the rest, {why}."
            + (low_txt or pick))
BIG_HTML, BIG_ROWS = big_brands_html(
    ALL, QF, big_verdict, h2='How do the big brands fare on dairy free?',
    intro=('Every brand with national grocery, big-box or Costco distribution, with how many of its bars are labeled dairy '
           'free. Brand names link to our full reviews where we have one.'))

# ---------------------------------------------------------------------------
# Top 50 + Bar Finder CTA + criteria
# ---------------------------------------------------------------------------
T50 = top50_rows(Q, 50)
C.check(not any(any_d(b) and not reviewed_ok(b, 'dairy free') for b in T50), 'no Top 50 bar names whey, milk or casein (a mislabeled bar would need a HOLD)')
TOP50 = top50_html(T50, h2='Top 50 dairy free protein bars',
                   intro='Ranked by ingredient grade first, then by protein per calorie. Tap any row for nutrition facts and '
                         'the full ingredient list.')
FINDER = finder_cta_html(N, FINDER_HREF, desc=('The Bar Finder opens with the Dairy Free filter already on, the same label '
                                               'this guide uses. Add your own filters for protein, sugar, calories, grade, '
                                               'brand, other certifications, or ingredients to exclude.'))
CRITERIA = criteria_html(
    qualify_rule=('The brand labels the bar dairy free (the Dairy Free field in our database). We also read every ingredient '
                  'list for whey, milk and casein, to explain why the rest miss. Vegan-labeled bars without a dairy free '
                  f'label are not counted. {comma(N)} of the {DB_PUBLIC} bars we track qualify.'),
    picks=PICKS)

# ---------------------------------------------------------------------------
# FAQ (answers may hold links; JSON-LD gets the plain text)
# ---------------------------------------------------------------------------
CONSIDER, MIXED, AVOID = brand_split(ALL, QF)
ALLDF = sorted((r for r in CONSIDER if r['d'] == 0), key=lambda r: (-r['total'], r['brand'].lower()))
C.check(len(ALLDF) >= 2, 'at least two fully dairy free brands')
SPLIT_EX = min((r for r in CONSIDER + MIXED + AVOID if r['q'] and r['d'] and r['total'] >= 10),
               key=lambda r: (abs(r['q'] / r['total'] - 0.5), -r['total'], r['brand']))
BEST = PK['Best overall']
FAQS = [
    ('What makes a protein bar dairy free on this site?',
     f'We use the Dairy Free (Y/N) label on file for each bar. {of_db(N, NT, True)} bars we track carry that label. We also '
     'cross-check ingredient lists ourselves for whey, milk, and casein, the three named dairy sources that show up most in the data.'),
    ('What is the best dairy free protein bar?',
     f"By our rules, {full(BEST)}: {BEST['score_band']}-grade ingredients, {fnum(P(BEST))}g protein and {fnum(CAL(BEST))} "
     f"calories. For the most protein, {full(PK['Highest protein'])} has {fnum(P(PK['Highest protein']))}g. Every bar in our "
     "Best 10 is labeled dairy free with an A or B grade."),
    ('How many dairy free protein bars are in your database?',
     f"{of_db(N, NT, True)} bars we track are labeled dairy free, spanning {BRANDS_Q} brands. {GR['A']} of those {comma(N)} "
     'bars grade A for ingredient quality.'),
    ('Is Quest dairy free?',
     f"No. All {len(QU)} of Quest's flavors use whey, and none carry a dairy free label."),
    ('What is the most common dairy ingredient in protein bars?',
     f"Whey. It shows up by name in {of_db(W, NT, True)} bars we track, more than milk or casein on its own. Most brands use "
     "it as the bar's main protein source, not a minor add-in."),
    ('Does not being labeled dairy free mean a bar contains dairy?',
     f"Not necessarily. {comma(len(UNLAB))} of the {comma(ND)} bars that don't carry a dairy free label show no whey, milk, or "
     f"casein anywhere in their own ingredient list, and {len(VEGAN_UNLAB)} of them are labeled vegan. The brand just hasn't "
     'labeled the bar dairy free, which is a different claim from it containing dairy.'),
    ('Are vegan protein bars dairy free?',
     'By ingredients, yes: a vegan bar has no whey, milk, or casein. But we only count a bar as dairy free when the brand '
     f'labels it that way, and {len(VEGAN_UNLAB)} vegan-labeled bars in our database don\'t carry a dairy free label. If you '
     'avoid dairy as an ingredient rather than for an allergy, our vegan guide covers those bars too.'),
    ("Can a brand have some dairy free flavors and some that aren't?",
     f"Yes. {SPLIT_EX['brand']} splits closest to even of any large lineup we checked: {SPLIT_EX['q']} of {SPLIT_EX['total']} "
     'flavors are labeled dairy free. Always check the specific flavor, not just the brand.'),
    ('What protein bars are dairy free?',
     f"{comma(N)} bars across {BRANDS_Q} brands carry a dairy free label, led by brands like {ALLDF[0]['brand']} and "
     f"{ALLDF[1]['brand']} that qualify across their entire lineup. Our Best 10 picks are at the top of this page, the Top 50 "
     'is further down, and the Bar Finder has all of them.'),
    ('Are dairy free protein bars lower quality than regular bars?',
     f"No. {ab(Q)}% of dairy free bars in our database grade A or B, against {ab(ALL)}% database-wide. What they give up on "
     f"average is protein: dairy free bars average {fnum(round(avg(Q, 'Protein (g)'), 1))}g against a database-wide average "
     f"of {fnum(round(avg(ALL, 'Protein (g)'), 1))}g, since most whey-based bars are built to maximize protein per calorie."),
    ('Is dairy free the same as vegan?',
     'No. A dairy free bar just has no whey, milk, or casein. It can still contain honey, egg white protein, collagen, or '
     "gelatin, none of which are vegan. Check our Vegan Protein Bars guide separately if that's what you need."),
    ('How often is this list updated?',
     'We update the database whenever new bars are added or a brand reformulates. Manufacturers do change their ingredient '
     'lists over time, so always confirm against the packaging in front of you.'),
]

# ---------------------------------------------------------------------------
# Regions
# ---------------------------------------------------------------------------
H1 = 'The 10 Best Dairy Free Protein Bars'
TITLE = f'10 Best Dairy Free Protein Bars ({DB_PUBLIC} Checked)'
DESC = (f'Only {pct0(N, NT)}% of protein bars are labeled dairy free. We checked {DB_PUBLIC} for whey, milk and casein and '
        f'picked the 10 best of {comma(N)}.')
OG_DESC = (f'{comma(N)} dairy free protein bars, checked against the label and the ingredient list. Here are the 10 best, '
           'each picked by a published rule.')
C.check(len(DESC) <= 155, f'meta description under 155 characters ({len(DESC)})')
FAQS_PLAIN = [(q, plain_text(a)) for q, a in FAQS]
REGIONS = v2_head_regions(title=TITLE, h1=H1, desc=DESC, og_desc=OG_DESC, url=URL, about='Dairy Free Protein Bars',
                          published=PUBLISHED, faqs=FAQS_PLAIN, picks=PICKS)
EDITORIAL = f'  <section class="section off" id="what-disqualifies">{DISQ}  </section>'
HERO = (f'<h1 class="hero-title">{esc(H1)}</h1>\n'
        f'    <p class="hero-sub">Most protein bars are built on dairy: whey or milk protein as the main ingredient, casein for '
        f'texture, milk chocolate on the coating. People with a milk allergy or lactose intolerance skip all of it. We use the '
        f'dairy free label on every bar, then read the ingredient list ourselves for whey, milk and casein.</p>\n'
        f'    <p class="hero-sub">Of the {DB_PUBLIC} bars we track, {comma(N)} are labeled dairy free, about {pct0(N, NT)}%. '
        f'Whey alone shows up in {comma(W)}. Another {comma(len(UNLAB))} bars name no dairy at all but aren\'t labeled dairy '
        f'free, so we leave them out.</p>')
REGIONS += [
    ('hero', HERO),
    ('best10', best10_html(PICKS, h2='Best 10 dairy free protein bars', intro=B10_INTRO)),
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
        ('/vegan-protein-bars', 'Vegan Protein Bars', 'Bars with no whey, milk, honey, egg, or gelatin.'),
        ('/gluten-free-protein-bars', 'Gluten Free Protein Bars', 'Bars labeled gluten free, checked against the ingredient list.'),
        ('/clean-protein-bars', 'Clean Protein Bars', 'A or B grade bars with no artificial sweeteners and no processed oils.'),
    ])),
]

if __name__ == '__main__':
    page = build_guide_page_v2(PAGE, REGIONS, ALL, C, picks=PICKS)
    size = len(page.encode('utf-8'))
    faq_at = len(page[:page.find('<section class="guide-faq"')].encode('utf-8'))
    print(f'{PAGE}: {N} qualify, {ND} disqualified, {size:,} bytes, FAQ at byte {faq_at:,}')
    for i, (s_, b, why, n) in enumerate(PICKS, 1):
        print(f'  {i:2d}. {s_.label}: {full(b)} ({b["score_band"]}) [pool {n}]')
        print(f'      {why}')
