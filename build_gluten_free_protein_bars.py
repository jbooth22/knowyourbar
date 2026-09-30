#!/usr/bin/env python3
"""Rebuild gluten-free-protein-bars.html from bars.js. GUIDE PAGE v2 ("Best 10").

Run from the repo root:  python3 build_gluten_free_protein_bars.py

Layout and every rule: claude/GUIDE_PAGE_SPEC_V2.md (locked 2026-09-29) and
the v2 section of kyb_guide_lib.py, built the same way as the pilot
(build_no_sugar_alcohols.py). The first run migrated the live v1 page to the v2
body (head, nav and footer kept as deployed); later runs rewrite only the
<!-- kyb:NAME --> regions. Every number, pick and brand row comes from bars.js.
Copy that depends on a fact is checked; if one stops being true the build
stops and lists it. Ingredient quality is shown and ranked as a GRADE only.

Screen: GUIDE_FILTERS['gluten-free-protein-bars'] = `Gluten Free (Y/N)` is Yes
(certification field, no macro or grade gate). Bar Finder: /bar-finder?certs=GF
(same field). Wheat and barley/malt are counted by ingredient text over the
bars that are not labeled gluten free, ignoring "may contain" / shared-facility
statements. A gluten-free-labeled bar whose own ingredients name wheat or
barley is printed as a WARNING.

Guide slots (locked with Jeff 2026-09-29): Lowest sugar (among bars with no
sugar alcohol), Best plant-based (15g+), Highest fiber, Best oat-free.
Fallbacks: Best snack size, then Best date-sweetened.

HOLD (Jeff, 2026-09-29): bars kept out of the Best 10 and Top 50 on this page
while their grade is rechecked upstream. They still count as qualifying (the
Bar Finder count must match). Remove a key once the bar is rescored.
"""
import re
from kyb_guide_lib import *

PAGE = 'gluten-free-protein-bars.html'
URL = 'https://knowyourbar.com/gluten-free-protein-bars'
PUBLISHED = '2026-08-26'
set_tie_seed('gluten-free-protein-bars')   # per-guide shuffle for exact ties (kyb_guide_lib, 2026-09-30)

ALL = load_bars()
QF = GUIDE_FILTERS['gluten-free-protein-bars']
Q = [b for b in ALL if QF(b)]
D = [b for b in ALL if not QF(b)]
N, ND, NT = len(Q), len(D), len(ALL)
BRANDS_Q = len({b['Brand Name'] for b in Q})
GR_Q = {g: sum(1 for b in Q if b.get('score_band') == g) for g in BAND_ORDER}
C = Claims()

HOLD = set()
# 2026-09-29: 'Pure Protein | Cookies and Cream' was held here (graded A, 10.8, with
# sucralose, erythritol and palm oils). Scoring v13 fixed the cause (protein blends
# weren't stack-discounted) and it now grades C (1.5), so the hold was removed.
# Audit: claude/SCORING_BLEND_AUDIT_2026-09-29.md.
C.check(not any(b.get('Gluten Free (Y/N)') not in ('Yes', None) for b in ALL), 'Gluten Free field is only Yes or blank')
Q_SHOW = [b for b in Q if b['Key'] not in HOLD]

GLUTEN = {'wheat': r'(?<!buck)wheat', 'barley': r'barley|\bmalt(?:ed)?\b(?!odextrin|itol|ose)|malt extract|malt syrup', 'rye': r'\brye\b'}
def label_text(b):
    return re.split(r'may contain|manufactured (?:in|on)|processed (?:in|on)|produced (?:in|on)|made in a facility|in a facility', ingr(b), flags=re.I)[0]
def has_g(b, k): return bool(re.search(GLUTEN[k], label_text(b), re.I))
WHEAT = [b for b in D if has_g(b, 'wheat')]
BARLEY = [b for b in D if has_g(b, 'barley')]
NAMED = [b for b in D if any(has_g(b, k) for k in GLUTEN)]
UNLABELED = [b for b in D if b not in NAMED]
for b in Q:
    if any(has_g(b, k) for k in GLUTEN) and not reviewed_ok(b, 'gluten free'):
        print(f'WARNING: {full(b)} is labeled gluten free in bars.js but its ingredients name '
              f'{", ".join(k for k in GLUTEN if has_g(b, k))}. Check the label; the page follows bars.js.')
C.check(len(WHEAT) > len(BARLEY), 'wheat is named more often than barley or malt')
C.check(not any(has_g(b, 'rye') for b in D), 'no bar names rye (copy covers wheat and barley only)')
def link(href, text): return f'<a href="{href}">{text}</a>'

# ---------------------------------------------------------------------------
# Best 10 (spec v2; guide slots locked with Jeff 2026-09-29)
# ---------------------------------------------------------------------------
OAT_RX = r'\boats?\b|oat flour|oatmeal'
def oat_free(b): return not re.search(OAT_RX, ingr(b), re.I)
def plant_based(b): return b.get('Vegan (Y/N)') == 'Yes'
SUBSTITUTE = re.compile(r'allulose|monk ?fruit|luo han|stevia|reb ?a\b|rebaudioside|sucralose|acesulfame|aspartame|'
                        r'saccharin|erythritol|xylitol|sorbitol|maltitol|isomalt|tagatose', re.I)
ADDED_SUGAR = re.compile(r'cane sugar|\bsugar\b|honey|syrup|agave|coconut sugar|molasses|nectar|dextrose|fructose|'
                         r'sucrose|juice concentrate|tapioca', re.I)
def date_sweetened(b):
    t = ingr(b)
    return bool(re.search(r'\bdates?\b|date paste', t, re.I)) and not SUBSTITUTE.search(t) and not ADDED_SUGAR.search(t)

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
    LOW_SUGAR,
    slot_subset('Best plant-based', 'Vegan-labeled bars.', plant_based,
                lambda b: 'Vegan and labeled gluten free.', floor=15),
    slot_highest_fiber(),
    slot_subset('Best oat-free', 'No oats anywhere on the label.', oat_free,
                lambda b: "No oats on the label, for anyone who avoids oats even when they're labeled gluten free."),
]
FALLBACKS = [
    slot_subset('Best snack size', 'Under 150 calories.', lambda b: CAL(b) < 150, lambda b: f'Under 150 calories ({fnum(CAL(b))}).'),
    slot_subset('Best date-sweetened', 'Dates on the label, and no added sugar, syrup or sugar substitute.', date_sweetened,
                lambda b: f"Sweetened only with dates, in {top_level_ingredient_count(ingr(b))} ingredients."),
]
PICKS = pick_best10(Q_SHOW, SLOTS, FALLBACKS)
C.check(len(PICKS) == 10, 'ten Best 10 picks available')
C.check([s.label for s, *_ in PICKS] == [s.label for s in SLOTS], 'all ten planned slots filled without fallbacks')
C.check(not any(re.search(r'score \d|scored? \d', w) for _s, _b, w, _n in PICKS), 'no ingredient score printed in a pick')
B10_INTRO = ("Ten gluten free bars, each the winner of one thing people shop for. Every pick is labeled gluten free, has an A "
             "or B ingredient grade and at least 10g of protein, and no bar appears twice.")
OATS_Q = [b for b in Q if not oat_free(b)]

# ---------------------------------------------------------------------------
# What disqualifies a bar
# ---------------------------------------------------------------------------
DISQ = f'''
    <div class="section-inner">
      <h2 class="section-title">What disqualifies a protein bar from being gluten free</h2>
      <div class="section-body">
        <p>We check the Gluten Free (Y/N) label on file for every bar, then cross-check ingredient lists ourselves for wheat and barley or malt, the two gluten sources that show up by name in our data. {of_db(N, NT)} bars, about {pct0(N, NT)}%, carry a gluten free label. The other {comma(ND)}, about {pct0(ND, NT)}%, don't.</p>
        <p>Wheat is the most common named culprit at {len(WHEAT)} bars ({g1(100 * len(WHEAT) / NT)}% of the full database), followed by barley or malt at {len(BARLEY)} bars ({g1(100 * len(BARLEY) / NT)}%). The remaining {len(UNLABELED)} bars, {g1(100 * len(UNLABELED) / NT)}% of the full database, show no wheat or barley in their own ingredient list at all. They just aren't labeled gluten free, which is a different claim from actually containing gluten.</p>
      </div>
      <div class="score-grid" style="margin-top:1.5rem;">
{v2_count_card_html('Wheat', WHEAT, NT, 'The most common named gluten source, usually as wheat flour, a wheat-based crisp, or a graham/cookie piece mixed into the bar.')}
{v2_count_card_html('Barley / Malt', BARLEY, NT, 'Shows up as barley malt extract or malt syrup, usually a flavoring or sweetener rather than a structural ingredient.')}
{v2_count_card_html('Not labeled gluten free', UNLABELED, NT, "No wheat or barley shows up anywhere in the ingredient list we can find, but the brand hasn't labeled or certified the bar gluten free either. That is a labeling gap, not proof the bar contains gluten.", names=[])}
      </div>
      <h3 class="kt-h3">What about oats?</h3>
      <div class="section-body">
        <p>Oats don't contain gluten themselves, but they are often grown and milled alongside wheat, so cross-contact is common. We don't count oats against a bar: if the brand labels it gluten free, it qualifies. {len(OATS_Q)} of the {comma(N)} gluten free bars here contain oats. If you avoid oats too, the Best oat-free pick in our Best 10 has none.</p>
      </div>
    </div>
'''

# ---------------------------------------------------------------------------
# Findings: three data findings + one chart
# ---------------------------------------------------------------------------
def ab(bars): return pct0(sum(1 for b in bars if b.get('score_band') in ('A', 'B')), len(bars))
C.check(sum(1 for b in Q if b['score_band'] in 'AB') / N > sum(1 for b in ALL if b['score_band'] in 'AB') / NT,
        'gluten free bars grade A or B more often than the database')
C.check(avg(Q, 'Protein (g)') < avg(ALL, 'Protein (g)'), 'gluten free bars average less protein')
C.check(len(UNLABELED) > len(WHEAT), 'unlabeled bars outnumber the wheat bars')
INSIGHTS = [
    ('Most bars without the label have no gluten ingredient we can find.',
     f'{len(UNLABELED)} of the {comma(ND)} bars without a gluten free label show no wheat or barley in their own ingredient '
     "list. The brand just hasn't labeled or certified them, which is not the same as containing gluten."),
    ('Wheat is the clearest single gluten source.',
     f'{len(WHEAT)} bars ({g1(100 * len(WHEAT) / NT)}% of the database) name wheat directly'
     + (', more than double the barley/malt count.' if len(WHEAT) >= 2 * len(BARLEY) else ', more than the barley/malt count.')),
    ('Gluten free bars grade a little better, but carry less protein.',
     f"{ab(Q)}% of gluten free bars grade A or B, against {ab(ALL)}% database-wide. They average "
     f"{fnum(round(avg(Q, 'Protein (g)'), 1))}g of protein against {fnum(round(avg(ALL, 'Protein (g)'), 1))}g."),
]
GRADE_ROWS = [(g, sum(1 for b in Q if b['score_band'] == g), sum(1 for b in ALL if b['score_band'] == g)) for g in BAND_ORDER]
FINDINGS = findings_v2_html(f'What we found screening {DB_PUBLIC} bars', INSIGHTS,
                            grade_share_chart_html(GRADE_ROWS, title='Share of bars labeled gluten free, by ingredient grade',
                                                   note=f'Out of the {DB_PUBLIC} bars in our database.'))

# ---------------------------------------------------------------------------
# Brands that do it well + big brands
# ---------------------------------------------------------------------------
def pickable(bars): return [b for b in bars if b['Key'] not in HOLD]
WELL = brands_well_rows(ALL, QF, n=8)
C.check(sum(r['big'] for r in WELL) >= 2 and sum(not r['big'] for r in WELL) >= 2, 'brands-well has 2+ big and 2+ small brands')
def well_why(r):
    lead = f"All {r['total']} flavors are gluten free" if r['q'] == r['total'] else f"{r['q']} of {r['total']} flavors are gluten free"
    g = r['grades']
    grades = f"all {next(iter(g))} grade" if len(g) == 1 else grade_mix_text(g) + ' grade'
    bp = best_pick(pickable(r['qual']))
    return (f"{lead}, {grades}." + (f" Best pick: {bp['Flavor Name']} ({bp['score_band']}, {fnum(P(bp))}g protein, "
                                    f"{fnum(CAL(bp))} cal)." if bp else ''))
BRANDS_WELL = brands_well_html(WELL, well_why, h2='Brands that do it well',
                               intro='Brands with at least 3 bars in our database, ranked by how much of their lineup is labeled '
                                     'gluten free and how well those bars grade. We made sure to include both brands you can find '
                                     'at most grocery stores and smaller independents.')

def big_verdict(r):
    disq = [b for b in r['bars'] if not QF(b)]
    bp = best_pick(pickable(r['qual']))
    pick = f" Best pick: {bp['Flavor Name']} ({bp['score_band']}, {fnum(P(bp))}g protein)." if bp else ''
    w = sum(1 for b in disq if has_g(b, 'wheat'))
    ba = sum(1 for b in disq if has_g(b, 'barley') and not has_g(b, 'wheat'))
    named = w + ba
    if r['q'] == r['total']:
        ag = avg_grade(r['qual'])
        return ('Every flavor is labeled gluten free.' + (f' Most grade {ag} on ingredients, so check the label.'
                                                          if ag in ('C', 'D', 'F') else '') + pick)
    other = len(disq) - named
    ISNT, ARENT = "isn't", "aren't"
    def n_list(n, what): return f"{n} list{'s' if n == 1 else ''} {what}"
    if named == 0:
        why = "none name wheat or barley, so it's a labeling gap"
    elif w == len(disq):
        why = 'every one lists wheat'
    elif ba == len(disq):
        why = 'every one lists barley or malt'
    else:
        parts = ([n_list(w, 'wheat')] if w else []) + ([n_list(ba, 'barley or malt')] if ba else [])
        if other:
            parts.append(f"{other} {'names' if other == 1 else 'name'} neither and just {ISNT if other == 1 else ARENT} labeled")
        why = names_and(parts)
    if r['q'] == 0:
        if named == 0:
            return "None are labeled gluten free, but none name wheat or barley either, so it's a labeling gap."
        return f"None are labeled gluten free: {why}."
    return f"{'Only ' if r['q'] * 2 < r['total'] else ''}{r['q']} of {r['total']} are labeled gluten free. Of the rest, {why}." + pick
BIG_HTML, BIG_ROWS = big_brands_html(
    ALL, QF, big_verdict, h2='How do the big brands fare on gluten free?',
    intro=('Every brand with national grocery, big-box or Costco distribution, with how many of its bars are labeled gluten '
           'free. Brand names link to our full reviews where we have one.'))
CLIF = [b for b in ALL if b['Brand Name'] == 'CLIF Bar']
C.check(CLIF and not any(QF(b) for b in CLIF), 'no CLIF Bar flavor is labeled gluten free')

# ---------------------------------------------------------------------------
# Top 50 + Bar Finder CTA + criteria
# ---------------------------------------------------------------------------
T50 = top50_rows(Q_SHOW, 50)
TOP50 = top50_html(T50, h2='Top 50 gluten free protein bars',
                   intro='Ranked by ingredient grade first, then by protein per calorie. Tap any row for nutrition facts and '
                         'the full ingredient list.')
FINDER_HREF = '/bar-finder?certs=GF'
FINDER = finder_cta_html(N, FINDER_HREF, desc=('The Bar Finder opens with the Gluten Free filter already on, the same label '
                                               'this guide uses. Add your own filters for protein, sugar, calories, grade, '
                                               'brand, other certifications, or ingredients to exclude.'))
CRITERIA = criteria_html(
    qualify_rule=('The brand labels the bar gluten free (the Gluten Free field in our database). We also read every ingredient '
                  'list for wheat and barley or malt, to explain why the rest miss. Oats do not count against a bar. '
                  f'{comma(N)} of the {DB_PUBLIC} bars we track qualify.'),
    picks=PICKS,
    extra_rules=(['One bar is held out of the Best 10 and Top 50 while we recheck its ingredient grade. It is still in the Bar Finder.']
                 if any(b['Key'] in HOLD for b in Q) else []))

# ---------------------------------------------------------------------------
# FAQ
# ---------------------------------------------------------------------------
CONSIDER, MIXED, AVOID = brand_split(ALL, QF)
ALLGF = sorted((r for r in CONSIDER if r['d'] == 0), key=lambda r: (-r['total'], r['brand'].lower()))
C.check(len(ALLGF) >= 4, 'at least four fully gluten free brands')
CLIF_W = [b for b in CLIF if has_g(b, 'wheat')]
CLIF_MAY = [b for b in CLIF if not has_g(b, 'wheat') and re.search(r'wheat', ingr(b), re.I)]
def clif_detail():
    parts = [f"None of CLIF Bar's {len(CLIF)} flavors carry a gluten free label."]
    if CLIF_W:
        parts.append(f'{len(CLIF_W)} list wheat as an ingredient.')
    clif_b = [b for b in CLIF if has_g(b, 'barley')]
    if clif_b:
        parts.append(f'{len(clif_b)} list barley or malt as an ingredient.')
    if CLIF_MAY:
        parts.append(f"{len(CLIF_MAY)} carry a \"may contain wheat\" warning" + (' on top of that.' if (CLIF_W or clif_b) else ' without listing it as an ingredient.'))
    return ' '.join(parts)
SPLIT_EX = min((r for r in CONSIDER + MIXED + AVOID if r['q'] and r['d'] and r['total'] >= 10),
               key=lambda r: (abs(r['q'] / r['total'] - 0.5), -r['total'], r['brand']))
LARA = next((r for r in CONSIDER + MIXED + AVOID if r['brand'] == 'Larabar'), None)
C.check(LARA and LARA['d'] == 0, 'every Larabar flavor is labeled gluten free')
FAQS = [
    ('What makes a protein bar gluten free on this site?',
     f'We use the Gluten Free (Y/N) label on file for each bar. {of_db(N, NT, True)} bars we track carry that label. '
     'We also cross-check ingredient lists ourselves for wheat and barley or malt, the two named gluten sources that show up most in the data.'),
    ('How many gluten free protein bars are in your database?',
     f"{of_db(N, NT, True)} bars we track are labeled gluten free, spanning {BRANDS_Q} brands. {GR_Q['A']} of those "
     f"{comma(N)} bars grade A for ingredient quality."),
    ('Is CLIF Bar gluten free?',
     'Not by label. ' + clif_detail() + ' If you need to avoid gluten, look elsewhere.'),
    ('Are Larabar bars gluten free?',
     f"Yes. All {LARA['total']} Larabar flavors we track are labeled gluten free. Larabar builds its bars around dates, nuts, "
     'and fruit rather than a wheat-based binder or crisp.'),
    ('What is the most common gluten ingredient in protein bars?',
     f'Wheat. It shows up by name in {of_db(len(WHEAT), NT, True)} bars we track'
     + (', more than double the count for barley or malt.' if len(WHEAT) >= 2 * len(BARLEY) else ', more than barley or malt.')
     + " Most other non-gluten-free bars simply aren't labeled, without a named gluten ingredient we can find."),
    ('Does not being labeled gluten free mean a bar contains gluten?',
     f"Not necessarily. {len(UNLABELED)} of the {comma(ND)} bars that don't carry our gluten free label show no wheat or barley "
     "anywhere in their own ingredient list. The brand just hasn't labeled or certified the bar, which is a different claim "
     'from it containing gluten.'),
    ("Can a brand have some gluten free flavors and some that aren't?",
     f"Yes. {SPLIT_EX['brand']} splits closest to even of any large lineup we checked: {SPLIT_EX['q']} of {SPLIT_EX['total']} "
     'flavors are gluten free. Always check the specific flavor, not just the brand.'),
    ('What protein bars are gluten free?',
     f"{comma(N)} bars across {BRANDS_Q} brands carry a gluten free label, led by brands like {ALLGF[0]['brand']} and "
     f"{ALLGF[1]['brand']} that qualify across their entire lineup. Our Best 10 picks are at the top of this page, the Top 50 "
     "is further down, and the Bar Finder has all of them."),
    ('What protein bars are not gluten free?',
     f"{of_db(ND, NT, True)} bars we track don't carry a gluten free label. Wheat is the most common named reason, "
     'followed by barley or malt. Most of the remaining bars simply haven\'t been labeled, without an identifiable gluten ingredient in the list.'),
    ('Are gluten free protein bars lower quality than regular bars?',
     f"No. Gluten free bars in our database grade A or B at a slightly higher rate than the database as a whole "
     f"({ab(Q)}% vs. {ab(ALL)}%). What they give up on average is protein: gluten free bars average "
     f"{fnum(round(avg(Q, 'Protein (g)'), 1))}g against a database-wide average of {fnum(round(avg(ALL, 'Protein (g)'), 1))}g."),
    ('How often is this list updated?',
     'We update the database whenever new bars are added or a brand reformulates. Manufacturers do change their ingredient '
     'lists over time, so always confirm against the packaging in front of you.'),
]

# ---------------------------------------------------------------------------
# Regions
# ---------------------------------------------------------------------------
H1 = 'The 10 Best Gluten Free Protein Bars'
TITLE = f'10 Best Gluten Free Protein Bars ({DB_PUBLIC} Checked)'
DESC = (f'Only {pct0(N, NT)}% of protein bars are labeled gluten free. We checked {DB_PUBLIC} and picked the 10 best of the '
        f'{comma(N)} that qualify.')
OG_DESC = (f'{comma(N)} gluten free protein bars, checked against the label and the ingredient list. Here are the 10 best, '
           'each picked by a published rule.')
C.check(len(DESC) <= 155, f'meta description under 155 characters ({len(DESC)})')
FAQS_PLAIN = [(q, plain_text(a)) for q, a in FAQS]
REGIONS = v2_head_regions(title=TITLE, h1=H1, desc=DESC, og_desc=OG_DESC, url=URL, about='Gluten Free Protein Bars',
                          published=PUBLISHED, faqs=FAQS_PLAIN, picks=PICKS)
EDITORIAL = f'  <section class="section off" id="what-disqualifies">{DISQ}  </section>'
HERO = (f'<h1 class="hero-title">{esc(H1)}</h1>\n'
        f'    <p class="hero-sub">Gluten is a protein found in wheat, barley and rye. People with celiac disease or a gluten '
        f'sensitivity avoid it, and in protein bars it usually hides in a wheat-based crisp, a cookie piece or barley malt. We use '
        f'the gluten free label on every bar, then read the ingredient list ourselves for wheat and barley.</p>\n'
        f'    <p class="hero-sub">Of the {DB_PUBLIC} bars we track, {comma(N)} are labeled gluten free. Most of the other '
        f'{comma(ND)} don\'t name wheat or barley at all: {len(UNLABELED)} of them just aren\'t labeled, which is not the same '
        f'as containing gluten.</p>')
REGIONS += [
    ('hero', HERO),
    ('best10', best10_html(PICKS, h2='Best 10 gluten free protein bars', intro=B10_INTRO)),
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
        ('/vegan-protein-bars', 'Vegan Protein Bars',
         f"{comma(guide_count(ALL, 'vegan-protein-bars'))} bars with no whey, milk, honey, egg, or gelatin."),
        ('/no-seed-oils', 'No Seed Oils', 'Bars that skip canola, soybean, and sunflower oil.'),
        ('/clean-protein-bars', 'Clean Protein Bars', 'A or B grade bars with no artificial sweeteners and no processed oils.'),
    ])),
]
C.check(len(UNLABELED) > len(NAMED), 'most bars without the label name no wheat or barley')

if __name__ == '__main__':
    page = build_guide_page_v2(PAGE, REGIONS, ALL, C, picks=PICKS)
    size = len(page.encode('utf-8'))
    faq_at = len(page[:page.find('<section class="guide-faq"')].encode('utf-8'))
    print(f'{PAGE}: {N} qualify, {ND} disqualified, {size:,} bytes, FAQ at byte {faq_at:,}')
    for i, (s_, b, why, n) in enumerate(PICKS, 1):
        print(f'  {i:2d}. {s_.label}: {full(b)} ({b["score_band"]}) [pool {n}]')
        print(f'      {why}')
