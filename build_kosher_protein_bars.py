#!/usr/bin/env python3
"""Rebuild kosher-protein-bars.html from bars.js. GUIDE PAGE v2 ("Best 10").

Run from the repo root:  python3 build_kosher_protein_bars.py

Layout and every rule: claude/GUIDE_PAGE_SPEC_V2.md (locked 2026-09-29) and
the v2 section of kyb_guide_lib.py, built the same way as the other v2 guides
(closest reference: build_soy_free_protein_bars.py, a certification guide).
The first run migrated the live v1 page (built by kyb_cert_guide.CertGuide) to
the v2 body (head, nav and footer kept as deployed); later runs rewrite only the
<!-- kyb:NAME --> regions. Every number, pick and brand row comes from bars.js.
Copy that depends on a fact is checked; if one stops being true the build stops
and lists it. Ingredient quality is shown and ranked as a GRADE only.

Screen: GUIDE_FILTERS['kosher-protein-bars'] = `Kosher (Y/N)` is Yes. Kosher is
a supervised-process certification, not an ingredient screen, so the three
flagged ingredients (gelatin, confectioner's glaze/shellac, carmine/rennet) are
context only. A kosher-labeled bar can legitimately list certified gelatin, so
those are not warned about. No grade gate: the Best 10 uses A/B bars only.
Bar Finder: /bar-finder?certs=Kosher (checked key for key below).

Guide slots (picked 2026-09-30; Jeff asked for the best picks delivered without
an approval round): Best whey protein, Lowest sugar (no sugar alcohol), Best
gluten-free, Best non-GMO. Fallbacks: Highest fiber, then Lowest net carbs.
No A/B kosher bar with 10g+ protein is labeled dairy free, soy free or vegan, so
those slots are empty here. Every pick has an Amazon link.
"""
import re
from collections import Counter
from kyb_guide_lib import *

PAGE = 'kosher-protein-bars.html'
URL = 'https://knowyourbar.com/kosher-protein-bars'
PUBLISHED = '2026-09-17'
set_tie_seed('kosher-protein-bars')   # per-guide shuffle for exact ties (kyb_guide_lib, 2026-09-30)

ALL = load_bars()
QF = GUIDE_FILTERS['kosher-protein-bars']
Q = [b for b in ALL if QF(b)]
D = [b for b in ALL if not QF(b)]
N, ND, NT = len(Q), len(D), len(ALL)
BRANDS_Q = len({b['Brand Name'] for b in Q})
GR = {g: sum(1 for b in Q if b.get('score_band') == g) for g in BAND_ORDER}
N_AB = GR['A'] + GR['B']
C = Claims()
C.check(not any(b.get('Kosher (Y/N)') not in ('Yes', None) for b in ALL), 'Kosher field is only Yes or blank')

FLAGGED = "gelatin, confectioner's glaze, carmine, or rennet"
SOURCES = [  # label, regex (GUIDE_CRITERIA.md), card description
    ('Gelatin', r'\bgelatin\b',
     'Usually from pork or from animals not slaughtered under kosher rules, used in the puff or crisp layer of several bars. '
     'Fish and certified-kosher beef gelatin exist, but plain "gelatin" on a US label usually isn\'t kosher.'),
    ("Confectioner's glaze / shellac", r'shellac|confectioner.?s glaze',
     'A resin made by the lac insect, used as a shiny coating on candy pieces and drizzles. Not kosher without its own certification.'),
    ('Carmine or rennet', r'\bcarmine\b|cochineal|\brennet\b',
     'Carmine (an insect-derived red color) and rennet (traditionally animal-derived, used in some dairy blends). The rarest of the three.'),
]
RX = {l: r for l, r, _ in SOURCES}
DESC_S = {l: d for l, _, d in SOURCES}
def label_text(b):
    return re.split(r'may contain|manufactured (?:in|on)|processed (?:in|on)|produced (?:in|on)|made in a facility|in a facility', ingr(b), flags=re.I)[0]
def has_k(b, l): return bool(re.search(RX[l], label_text(b), re.I))
def any_k(b): return any(has_k(b, l) for l in RX)
HIT = {l: [b for b in D if has_k(b, l)] for l in RX}
ORDER = sorted(RX, key=lambda l: -len(HIT[l]))
NAMED = [b for b in D if any_k(b)]
UNLAB = [b for b in D if not any_k(b)]
C.check(ORDER[0] == 'Gelatin', 'gelatin is the most common flagged ingredient')
C.check(len(UNLAB) > 0.75 * ND, 'most non-kosher bars show none of the flagged ingredients')

# Bar Finder parity: ?certs=Kosher (app.js CERT_MAP 'Kosher' -> 'Kosher (Y/N)')
C.check({b['Key'] for b in ALL if (b.get('Kosher (Y/N)') or '').strip().lower() == 'yes'} == {b['Key'] for b in Q},
        'Bar Finder certs=Kosher returns exactly the guide set')
FINDER_HREF = '/bar-finder?certs=Kosher'

def yes(field): return lambda b: b.get(field) == 'Yes'
def by_brand(brand, bars=ALL): return [b for b in bars if b['Brand Name'] == brand]
def ab(bars): return pct0(sum(1 for b in bars if b.get('score_band') in ('A', 'B')), len(bars))

# ---------------------------------------------------------------------------
# Best 10 (spec v2)
# ---------------------------------------------------------------------------
WHEY_RX = re.compile(r'\bwhey\b[^,;()\[\]]*', re.I)
def whey(b): return bool(WHEY_RX.search(ingr(b)))
def whey_name(b): return WHEY_RX.search(ingr(b)).group(0).strip().lower()
NC = net_carbs
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
    slot_subset('Best whey protein', 'Whey protein on the label.', whey,
                lambda b: f"Built on {whey_name(b)}, a complete dairy protein and "
                          + ("one of the protein sources our scoring rates highest." if 'isolate' in whey_name(b)
                             else "one of the protein sources our scoring rates near the top.")),
    LOW_SUGAR,
    slot_subset('Best gluten-free', 'Labeled gluten free by the brand.', yes('Gluten Free (Y/N)'),
                lambda b: 'Certified kosher and labeled gluten free.'),
    slot_subset('Best non-GMO', 'Labeled Non-GMO by the brand.', yes('Non-GMO (Y/N)'),
                lambda b: 'Certified kosher and labeled Non-GMO.'),
]
FALLBACKS = [slot_highest_fiber(), LOW_NET]
PICKS = pick_best10(Q, SLOTS, FALLBACKS)
C.check(len(PICKS) == 10, 'ten Best 10 picks available')
C.check([s.label for s, *_ in PICKS] == [s.label for s in SLOTS], 'all ten planned slots filled without fallbacks')
C.check(not any(re.search(r'score \d|scored? \d', w) for _s, _b, w, _n in PICKS), 'no ingredient score printed in a pick')
PK = {s.label: b for s, b, _w, _n in PICKS}
C.check(has_tag(PK['Best whey protein'], 'Quality Protein Source'), 'the whey pick carries the Quality Protein Source tag')
C.check(N_AB < N and N_AB > 50, 'some kosher bars grade C or below, and more than 50 grade A or B')
B10_INTRO = ("Ten kosher bars, each the winner of one thing people shop for. Every pick is certified kosher, has an A or B "
             "ingredient grade and at least 10g of protein, and no bar appears twice.")

# ---------------------------------------------------------------------------
# What disqualifies a bar (carried over from v1, trimmed)
# ---------------------------------------------------------------------------
N_CF = N - N_AB
DISQ = f'''
    <div class="section-inner">
      <h2 class="section-title">What keeps a protein bar from being kosher</h2>
      <div class="section-body">
        <p>Kosher is different from vegan, gluten free, dairy free or soy free. It's a supervised-process certification, not an ingredient screen: whey, milk, soy, wheat, sugar and nuts can all be kosher when they're produced and supervised correctly. So we use the kosher label on file for every bar. {of_db(N, NT)} bars, about {pct0(N, NT)}%, carry it. The other {comma(ND)} don't.</p>
        <p>We do check ingredient lists for three ingredients that are almost never kosher without their own certification. Together they show up in only {comma(len(NAMED))} of the {comma(ND)} bars without the label. The other {comma(len(UNLAB))} ({pct0(len(UNLAB), ND)}%) name none of them: the brand just hasn't sought certification.</p>
      </div>
      <div class="score-grid" style="margin-top:1.5rem;">
{chr(10).join(v2_count_card_html(l, HIT[l], NT, DESC_S[l]) for l in ORDER)}
{v2_count_card_html('Not kosher-certified', UNLAB, NT, f"No {FLAGGED} anywhere in the ingredient list we can find. The brand simply hasn't pursued kosher certification, which is a claim about how a bar is made and supervised, not just what's in it.", names=[])}
      </div>
      <h3 class="kt-h3">Kosher doesn't screen on ingredient grade</h3>
      <div class="section-body">
        <p>Kosher says nothing about ingredient quality, so {N_CF} of the {comma(N)} kosher bars here grade C or below. Every Best 10 pick is an A or B, and our Top 50 lists A and B bars first.</p>
      </div>
    </div>
'''

# ---------------------------------------------------------------------------
# Findings: three data findings + one chart
# ---------------------------------------------------------------------------
BUILT = by_brand('Built')
BUILT_G = [b for b in BUILT if has_k(b, 'Gelatin')]
C.check(BUILT and len(BUILT_G) == len(BUILT) and not any(QF(b) for b in BUILT), 'every Built flavor lists gelatin and none is labeled kosher')
AB_Q, AB_ALL = ab(Q), ab(ALL)
C.check(abs(int(AB_Q) - int(AB_ALL)) <= 5, 'kosher bars grade A or B at about the database rate')
C.check(avg(Q, 'Protein (g)') < avg(ALL, 'Protein (g)') - 3, 'kosher bars average much less protein')
INSIGHTS = [
    ('Not being kosher is almost always about certification, not ingredients.',
     f"Only {pct0(len(NAMED), ND)}% of bars without the kosher label contain {FLAGGED}. The other {pct0(len(UNLAB), ND)}% just "
     "haven't sought certification."),
    ('Gelatin is the clearest non-kosher ingredient.',
     f"{len(HIT['Gelatin'])} bars list plain gelatin, more than the other flagged ingredients combined. Built is the example: "
     f"all {len(BUILT)} flavors use it and none are kosher."),
    ('Kosher bars grade about average but carry less protein.',
     f"{AB_Q}% of kosher bars grade A or B, against {AB_ALL}% database-wide. They average "
     f"{fnum(round(avg(Q, 'Protein (g)'), 1))}g of protein against {fnum(round(avg(ALL, 'Protein (g)'), 1))}g, because the "
     'kosher-certified set leans toward snack-style bars like Larabar and Bobo\'s.'),
]
C.check(len(HIT['Gelatin']) > sum(len(HIT[l]) for l in RX if l != 'Gelatin'), 'gelatin outnumbers the other flagged ingredients combined')
LB = Counter(b['Brand Name'] for b in Q).most_common(2)
C.check({br for br, _n in LB} == {'Larabar', "Bobo's"}, "Larabar and Bobo's are the largest kosher lineups")
GRADE_ROWS = [(g, sum(1 for b in Q if b['score_band'] == g), sum(1 for b in ALL if b['score_band'] == g)) for g in BAND_ORDER]
FINDINGS = findings_v2_html(f'What we found screening {DB_PUBLIC} bars', INSIGHTS,
                            grade_share_chart_html(GRADE_ROWS, title='Share of bars certified kosher, by ingredient grade',
                                                   note=f'Out of the {DB_PUBLIC} bars in our database.'))

# ---------------------------------------------------------------------------
# Brands that do it well + big brands
# ---------------------------------------------------------------------------
WELL = brands_well_rows(ALL, QF, n=8)
C.check(sum(r['big'] for r in WELL) >= 2 and sum(not r['big'] for r in WELL) >= 2, 'brands-well has 2+ big and 2+ small brands')
def well_why(r):
    lead = (f"All {r['total']} flavors are kosher" if r['q'] == r['total'] else
            f"{r['q']} of {r['total']} flavors {'is' if r['q'] == 1 else 'are'} kosher")
    gm = r['grades']
    grades = (f"graded {next(iter(gm))}" if r['q'] == 1 else
              f"all {next(iter(gm))} grade" if len(gm) == 1 else grade_mix_text(gm) + ' grade')
    bp = best_pick(r['qual'])
    return f"{lead}, {grades}. Best pick: {bp['Flavor Name']} ({bp['score_band']}, {fnum(P(bp))}g protein, {fnum(CAL(bp))} cal)."
BRANDS_WELL = brands_well_html(WELL, well_why, h2='Brands that do it well',
                               intro='Brands with at least 3 bars in our database, ranked by how much of their lineup is certified '
                                     'kosher and how well those bars grade. We made sure to include both brands you can find at '
                                     'most grocery stores and smaller independents.')

def flag_top(disq):
    c = Counter(l for b in disq for l in RX if has_k(b, l))
    return sorted(c.items(), key=lambda kv: (-kv[1], ORDER.index(kv[0])))
def big_verdict(r):
    disq = [b for b in r['bars'] if not QF(b)]
    bp = best_pick(r['qual'])
    pick = f" Best pick: {bp['Flavor Name']} ({bp['score_band']}, {fnum(P(bp))}g protein)." if bp else ''
    low_n = sum(1 for b in r['qual'] if b['score_band'] in ('C', 'D', 'F'))
    low_txt = ('' if low_n * 2 <= r['q'] else
               f" {'All' if low_n == r['q'] else 'Most'} of the kosher ones grade C or below, so check the label.")
    if r['q'] == r['total']:
        return 'Every flavor is kosher.' + (low_txt.replace(' of the kosher ones', '') if low_txt else pick)
    top = flag_top(disq)
    if not top:
        why = "none name a flagged ingredient, they just aren't certified"
    elif top[0][1] == len(disq):
        why = f'every one lists {top[0][0].lower()}'
    elif top[0][1] * 2 > len(disq):
        why = f'most list {top[0][0].lower()}'
    else:
        why = f"most name no flagged ingredient and just aren't certified"
    if r['q'] == 0:
        return f"None are kosher: {why}."
    verb = 'is' if r['q'] == 1 else 'are'
    return (f"{'Only ' if r['q'] * 2 < r['total'] else ''}{r['q']} of {r['total']} {verb} kosher. Of the rest, {why}."
            + (low_txt or pick))
BIG_HTML, BIG_ROWS = big_brands_html(
    ALL, QF, big_verdict, h2='How do the big brands fare on kosher?',
    intro=('Every brand with national grocery, big-box or Costco distribution, with how many of its bars are certified kosher. '
           'Brand names link to our full reviews where we have one.'))

# ---------------------------------------------------------------------------
# Top 50 + Bar Finder CTA + criteria
# ---------------------------------------------------------------------------
T50 = top50_rows(Q, 50)
C.check(all(b['score_band'] in ('A', 'B') for b in T50), 'every Top 50 bar grades A or B')
TOP50 = top50_html(T50, h2='Top 50 kosher protein bars',
                   intro='Ranked by ingredient grade first, then by protein per calorie. Tap any row for nutrition facts and '
                         'the full ingredient list.')
FINDER = finder_cta_html(N, FINDER_HREF, desc=('The Bar Finder opens with the Kosher filter already on, the same label this '
                                               'guide uses. Add your own filters for protein, sugar, calories, grade, brand, '
                                               'other certifications, or ingredients to exclude.'))
CRITERIA = criteria_html(
    qualify_rule=("The bar carries a kosher label (the Kosher field in our database). Kosher is a supervised-process "
                  "certification, so we can't verify it from the ingredient list; we also flag gelatin, confectioner's glaze "
                  "and carmine or rennet to explain why some bars miss. Ingredient grade is not part of the kosher screen. "
                  f"{comma(N)} of the {DB_PUBLIC} bars we track qualify, {N_AB} of them with an A or B grade."),
    picks=PICKS)

# ---------------------------------------------------------------------------
# FAQ (answers may hold links; JSON-LD gets the plain text)
# ---------------------------------------------------------------------------
CONSIDER, MIXED, AVOID = brand_split(ALL, QF)
ALLK = sorted((r for r in CONSIDER if r['d'] == 0), key=lambda r: (-r['total'], r['brand'].lower()))
C.check(len(ALLK) >= 2, 'at least two fully kosher brands')
SPLIT_EX = min((r for r in CONSIDER + MIXED + AVOID if r['q'] and r['d'] and r['total'] >= 10),
               key=lambda r: (abs(r['q'] / r['total'] - 0.5), -r['total'], r['brand']))
BEST = PK['Best overall']
FAQS = [
    ('What makes a protein bar kosher on this site?',
     f'We use the Kosher (Y/N) label on file for each bar. {of_db(N, NT, True)} bars we track carry that label. Kosher is a '
     "supervised-process certification, not just an ingredient list, so we can't fully verify it ourselves the way we can "
     'with an ingredient-based screen. We do flag three ingredients that are almost never kosher without their own '
     "certification: gelatin, confectioner's glaze or shellac, and carmine or rennet."),
    ('What is the best kosher protein bar?',
     f"By our rules, {full(BEST)}: {BEST['score_band']}-grade ingredients, {fnum(P(BEST))}g protein and {fnum(CAL(BEST))} "
     f"calories. Every bar in our Best 10 is certified kosher with an A or B grade."),
    ('How many kosher protein bars are in your database?',
     f"{of_db(N, NT, True)} bars we track are certified kosher, spanning {BRANDS_Q} brands. {GR['A']} of those {comma(N)} bars "
     'grade A for ingredient quality.'),
    ('Is Built Bar kosher?',
     f"No. All {len(BUILT)} Built flavors we track list gelatin, and none carry a kosher label."),
    ('What ingredient most often keeps a bar from being kosher?',
     f"Gelatin. It shows up in {of_db(len(HIT['Gelatin']), NT, True)} bars we track, usually in a puff or crisp layer. But it's "
     "the exception, not the rule: most bars without a kosher label don't contain any of the ingredients we flag."),
    ('Does not being labeled kosher mean a bar contains a non-kosher ingredient?',
     f"Not necessarily, and usually not. {comma(len(UNLAB))} of the {comma(ND)} bars without a kosher label show no {FLAGGED} "
     "anywhere in their own ingredient list. For most brands, not being kosher-certified just means they haven't pursued "
     'the certification.'),
    ("Can a brand have some kosher flavors and some that aren't?",
     f"Yes. {SPLIT_EX['brand']} splits closest to even of any large lineup we checked: {SPLIT_EX['q']} of {SPLIT_EX['total']} "
     'flavors are labeled kosher. Always check the specific flavor, not just the brand.'),
    ('What protein bars are kosher?',
     f"{comma(N)} bars across {BRANDS_Q} brands carry a kosher label, led by brands like {ALLK[0]['brand']} and "
     f"{ALLK[1]['brand']} that are kosher across their entire lineup. Our Best 10 picks are at the top of this page, the Top "
     '50 is further down, and the Bar Finder has all of them.'),
    ('Are kosher protein bars lower or higher quality than regular bars?',
     f"About the same. {AB_Q}% of kosher bars grade A or B, against {AB_ALL}% database-wide. Kosher certification is a separate "
     'claim from ingredient quality. What kosher bars do give up on average is protein: they average '
     f"{fnum(round(avg(Q, 'Protein (g)'), 1))}g against a database-wide average of {fnum(round(avg(ALL, 'Protein (g)'), 1))}g, "
     'since the kosher-certified set leans toward smaller, snack-style bars.'),
    ('How often is this list updated?',
     'We update the database whenever new bars are added or a brand reformulates. Manufacturers do change their ingredient '
     'lists and certifications over time, so always confirm against the packaging in front of you.'),
]

# ---------------------------------------------------------------------------
# Regions
# ---------------------------------------------------------------------------
H1 = 'The 10 Best Kosher Protein Bars'
TITLE = f'10 Best Kosher Protein Bars ({DB_PUBLIC} Checked)'
DESC = (f'Only {pct0(N, NT)}% of protein bars are certified kosher. We checked {DB_PUBLIC} and picked the 10 best of the '
        f'{comma(N)} that are.')
OG_DESC = (f'{comma(N)} kosher-certified protein bars, and why most of the rest simply aren\'t certified. Here are the 10 '
           'best, each picked by a published rule.')
C.check(len(DESC) <= 155, f'meta description under 155 characters ({len(DESC)})')
FAQS_PLAIN = [(q, plain_text(a)) for q, a in FAQS]
REGIONS = v2_head_regions(title=TITLE, h1=H1, desc=DESC, og_desc=OG_DESC, url=URL, about='Kosher Protein Bars',
                          published=PUBLISHED, faqs=FAQS_PLAIN, picks=PICKS)
EDITORIAL = f'  <section class="section off" id="what-disqualifies">{DISQ}  </section>'
HERO = (f'<h1 class="hero-title">{esc(H1)}</h1>\n'
        f'    <p class="hero-sub">A kosher protein bar is certified by a supervising agency, usually with a symbol like OU or '
        f'Star-K on the wrapper. It\'s a claim about how the bar is made and supervised, not just what\'s in it. We use the '
        f'kosher label on every bar, then flag the few ingredients that are almost never kosher on their own.</p>\n'
        f'    <p class="hero-sub">Of the {DB_PUBLIC} bars we track, {comma(N)} are certified kosher, about {pct0(N, NT)}%. Most '
        f'of the rest aren\'t certified rather than made with something non-kosher: only {pct0(len(NAMED), ND)}% contain '
        f'{FLAGGED}.</p>')
REGIONS += [
    ('hero', HERO),
    ('best10', best10_html(PICKS, h2='Best 10 kosher protein bars', intro=B10_INTRO)),
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
        ('/dairy-free-protein-bars', 'Dairy Free Protein Bars', 'Bars labeled dairy free, checked for whey, milk and casein.'),
        ('/vegan-protein-bars', 'Vegan Protein Bars', 'Bars with no whey, milk, honey, egg, or gelatin.'),
        ('/clean-protein-bars', 'Clean Protein Bars', 'A or B grade bars with no artificial sweeteners and no processed oils.'),
    ])),
]

if __name__ == '__main__':
    page = build_guide_page_v2(PAGE, REGIONS, ALL, C, picks=PICKS)
    size = len(page.encode('utf-8'))
    faq_at = len(page[:page.find('<section class="guide-faq"')].encode('utf-8'))
    print(f'{PAGE}: {N} qualify ({N_AB} A/B), {ND} disqualified, {size:,} bytes, FAQ at byte {faq_at:,}')
    for i, (s_, b, why, n) in enumerate(PICKS, 1):
        print(f'  {i:2d}. {s_.label}: {full(b)} ({b["score_band"]}) [pool {n}]')
        print(f'      {why}')
