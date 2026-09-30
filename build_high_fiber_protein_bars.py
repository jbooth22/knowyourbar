#!/usr/bin/env python3
"""Rebuild high-fiber-protein-bars.html from bars.js. GUIDE PAGE v2 ("Best 10").

Run from the repo root:  python3 build_high_fiber_protein_bars.py

Layout and every rule: claude/GUIDE_PAGE_SPEC_V2.md (locked 2026-09-29) and
the v2 section of kyb_guide_lib.py, built the same way as the other v2 guides
(closest reference: build_best_bars_for_diabetics.py, a macro screen). The first
run migrated the live v1 page to the v2 body (head, nav and footer kept as
deployed); later runs rewrite only the <!-- kyb:NAME --> regions. Every number,
pick and brand row comes from bars.js. Copy that depends on a fact is checked;
if one stops being true the build stops and lists it. Ingredient quality is
shown and ranked as a GRADE only.

Screen (GUIDE_CRITERIA.md, three cumulative tiers on Dietary Fiber (g)):
High 5g+, Very High 8g+, Extreme 11g+. The page ranks the Extreme tier
(GUIDE_FILTERS['high-fiber-protein-bars']). "The Extreme Fiber 100" is the
tier's name, not a count. No grade gate: the Best 10 uses A/B bars only.
Bar Finder: /bar-finder?fiber=11 (Min Fiber slider; checked key for key below).

Guide slots (picked 2026-09-30; Jeff asked for the best picks delivered without
an approval round): Highest fiber, Lowest net carbs, Best whey protein, Best
plant-based. Fallbacks: Most fiber per calorie (takes the empty "Best from a big
brand" slot: Quest Oatmeal Chocolate Chip is the only A/B big-brand bar here
and it's already Highest protein), then Best gluten-free.
"""
import re
from collections import Counter
from kyb_guide_lib import *

PAGE = 'high-fiber-protein-bars.html'
URL = 'https://knowyourbar.com/high-fiber-protein-bars'
PUBLISHED = '2026-09-06'
set_tie_seed('high-fiber-protein-bars')   # per-guide shuffle for exact ties (kyb_guide_lib, 2026-09-30)

ALL = load_bars()
QF = GUIDE_FILTERS['high-fiber-protein-bars']
Q = [b for b in ALL if QF(b)]
D = [b for b in ALL if not QF(b)]
N, ND, NT = len(Q), len(D), len(ALL)
BRANDS_Q = len({b['Brand Name'] for b in Q})
GR = {g: sum(1 for b in Q if b.get('score_band') == g) for g in BAND_ORDER}
N_AB = GR['A'] + GR['B']
N_CF = N - N_AB
C = Claims()
NC = net_carbs
C.check(90 <= N <= 115, 'the Extreme tier is still roughly 100 bars (the "Extreme Fiber 100" name)')

TIERS = [(5, 'High Fiber'), (8, 'Very High Fiber'), (11, 'Extreme Fiber')]
TIER = {t: [b for b in ALL if FIB(b) >= t] for t, _ in TIERS}
def tier_brands(t): return len({b['Brand Name'] for b in TIER[t]})
C.check(len(TIER[8]) < len(TIER[5]) / 2 and len(TIER[11]) < len(TIER[8]) / 2, 'each step up the fiber ladder cuts the pool by more than half')

# Bar Finder parity: ?fiber=N (Min Fiber slider; app.js skips the slider when the field is empty)
def finder_fiber(t):
    return {b['Key'] for b in ALL if num(b.get('Dietary Fiber (g)')) is None or num(b.get('Dietary Fiber (g)')) >= t}
C.check(finder_fiber(11) == {b['Key'] for b in Q}, 'Bar Finder fiber=11 returns exactly the guide set')
C.check(finder_fiber(5) == {b['Key'] for b in TIER[5]}, 'Bar Finder fiber=5 returns exactly the 5g+ tier')
FINDER_HREF = '/bar-finder?fiber=11'

ADDED = [
    ('Tapioca fiber', r'tapioca fiber|soluble tapioca|prebiotic tapioca|tapioca (?:resistant )?dextrin',
     'A resistant-starch fiber made from cassava root, added to boost the fiber count without changing texture much.'),
    ('Polydextrose', r'polydextrose', 'A synthetic soluble fiber used as a bulking agent, common in bars that also use a sugar alcohol.'),
    ('Chicory root / inulin', r'chicory|inulin', 'A soluble fiber extracted from chicory root, one of the most common added-fiber sources.'),
    ('Soluble corn fiber', r'corn fiber|soluble corn', 'A corn-derived resistant dextrin used the same way as tapioca or chicory fiber, mainly to raise the fiber line.'),
    ('Isomalto-oligosaccharide (IMO)', r'isomalto|\bimo\b(?!\s+free)',
     'A syrup sold as a prebiotic fiber. Not the sugar alcohol isomalt despite the similar name. Some research suggests the body digests much of it like a sugar.'),
]
AHIT = {l: [b for b in Q if re.search(rx, ingr(b), re.I)] for l, rx, _ in ADDED}
WHOLE = [b for b in Q if not any(b in AHIT[l] for l, _, _ in ADDED)]
AORDER = sorted(AHIT, key=lambda l: -len(AHIT[l]))
ANY_ADDED = N - len(WHOLE)
DESC_A = {l: d for l, _, d in ADDED}
C.check(ANY_ADDED > N / 2, 'most Extreme Fiber bars use an added fiber ingredient')

def yes(field): return lambda b: b.get(field) == 'Yes'
def by_brand(brand, bars=ALL): return [b for b in bars if b['Brand Name'] == brand]
def ab(bars): return pct0(sum(1 for b in bars if b.get('score_band') in ('A', 'B')), len(bars))
def imo(b): return bool(IMO_RX.search(ingr(b)))

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
LOW_NET = Slot('Lowest net carbs', 'The fewest net carbs (total carbs minus fiber minus sugar alcohol), grade B or better, 10g+ protein.',
               lambda E: [b for b in E if NC(b) is not None], lambda b: (NC(b),) + tie_chain(b), nc_why, metric=NC)
def fpc(b): return FIB(b) / CAL(b) * 100 if CAL(b) else 0
FIBER_PER_CAL = Slot('Most fiber per calorie', 'The most fiber per 100 calories, grade B or better, 10g+ protein.',
                     lambda E: E, lambda b: (-fpc(b),) + tie_chain(b),
                     lambda b, c: (f"{fnum(round(fpc(b), 1))}g fiber per 100 calories ({fnum(FIB(b))}g in {fnum(CAL(b))} calories), "
                                   f"{c['tied']}the best ratio of any bar here, with {fnum(P(b))}g protein."),
                     metric=lambda b: round(fpc(b), 1))
SLOTS = [
    slot_best_overall(15),
    slot_cleanest(),
    slot_highest_protein(300),
    slot_protein_per_cal(12),
    slot_lowest_calorie(),
    slot_highest_fiber(),
    LOW_NET,
    slot_subset('Best whey protein', 'Whey protein on the label.', whey,
                lambda b: f"Built on {whey_name(b)}, a complete dairy protein and "
                          + ("one of the protein sources our scoring rates highest." if 'isolate' in whey_name(b)
                             else "one of the protein sources our scoring rates near the top.")),
    slot_subset('Best plant-based', 'Labeled vegan by the brand.', yes('Vegan (Y/N)'),
                lambda b: 'Labeled vegan, with all its fiber from plants.', floor=15),
    slot_big_brand(),   # last here: it's empty on this guide, and its fallback should pick after the fiber slots
]
FALLBACKS = [
    FIBER_PER_CAL,
    slot_subset('Best gluten-free', 'Labeled gluten free by the brand.', yes('Gluten Free (Y/N)'),
                lambda b: 'Labeled gluten free by the brand.'),
]
PICKS = pick_best10(Q, SLOTS, FALLBACKS)
C.check(len(PICKS) == 10, 'ten Best 10 picks available')
C.check([s.label for s, *_ in PICKS] == [s.label if s.label != 'Best from a big brand' else 'Most fiber per calorie' for s in SLOTS],
        'the planned slots filled, with Most fiber per calorie replacing the empty big-brand slot')
C.check(not any(re.search(r'score \d|scored? \d', w) for _s, _b, w, _n in PICKS), 'no ingredient score printed in a pick')
PK = {s.label: b for s, b, _w, _n in PICKS}
C.check(FIB(PK['Highest fiber']) == max(FIB(b) for b in v2_eligible(Q)), 'the Highest fiber pick has the most fiber of any eligible bar')
IMO_PICKS = [b for _s, b, _w, _n in PICKS if imo(b)]
B10_INTRO = ("Ten bars with 11g or more of fiber, each the winner of one thing people shop for. Every pick has an A or B "
             "ingredient grade and at least 10g of protein, and no bar appears twice.")

# ---------------------------------------------------------------------------
# What pushes a bar past 11g + the three tiers (carried over from v1, trimmed)
# ---------------------------------------------------------------------------
def example(lo, hi):
    pool = [b for b in v2_eligible(ALL) if lo <= FIB(b) < hi]
    return min(pool, key=overall_key)
EX5, EX8 = example(5, 8), example(8, 11)
def imo_sentence():
    if not IMO_PICKS:
        return ''
    ps = [full(b) for b in IMO_PICKS]
    return (f" {num_word(len(ps)).capitalize() if len(ps) > 1 else 'One'} of our Best 10 picks "
            f"({names_and(ps)}) {'get' if len(ps) > 1 else 'gets'} part of {'their' if len(ps) > 1 else 'its'} fiber from IMO.")
MEANS = f'''
    <div class="section-inner">
      <h2 class="section-title">What actually pushes a bar past 11g of fiber</h2>
      <div class="section-body">
        <p>Fiber on a protein bar label comes from one of two places: whole-food ingredients (nuts, seeds, legumes, whole grains) or an isolated fiber added to raise the number. Of the {N} bars that clear our 11g Extreme Fiber cutoff, {pct0(ANY_ADDED, N)}% contain at least one of the five added fibers below, often two or three stacked together. None of these are red flags on their own; they're standard ways to add fiber.{imo_sentence()}</p>
      </div>
      <div class="score-grid" style="margin-top:1.5rem;">
{chr(10).join(v2_count_card_html(l, AHIT[l], N, DESC_A[l]) for l in AORDER)}
{v2_count_card_html('Whole-food fiber, no named additive', WHOLE, N, 'None of the five added fibers on the label. These bars reach 11g+ through nuts, seeds, legumes and whole grains.', names=[])}
      </div>
      <h3 class="kt-h3">The three tiers of high fiber</h3>
      <div class="section-body">
        <p>11g is a real jump, and not every bar needs to clear it. The FDA's labeling rule sets 5g as the cutoff for an "excellent source of fiber" claim, and most people looking for a higher-fiber bar are better served starting there. We track three cumulative cutoffs on the same number: every Extreme Fiber bar also counts as Very High and High Fiber.</p>
        <ul class="criteria-list">
          <li><strong>High Fiber, 5g+:</strong> {comma(len(TIER[5]))} bars ({pct0(len(TIER[5]), NT)}% of the database), {tier_brands(5)} brands. A good example that doesn't reach 8g: {esc(full(EX5))} ({EX5['score_band']}, {fnum(FIB(EX5))}g fiber, {fnum(P(EX5))}g protein).</li>
          <li><strong>Very High Fiber, 8g+:</strong> {len(TIER[8])} bars ({pct0(len(TIER[8]), NT)}%), {tier_brands(8)} brands. A good example that doesn't reach 11g: {esc(full(EX8))} ({EX8['score_band']}, {fnum(FIB(EX8))}g fiber, {fnum(P(EX8))}g protein).</li>
          <li><strong>Extreme Fiber, 11g+:</strong> {N} bars ({pct0(N, NT)}%), {BRANDS_Q} brands. The tier this page ranks.</li>
        </ul>
        <p>Fiber above roughly 10 to 15g in one sitting can cause bloating if you're not used to it, especially from added fibers like polydextrose or IMO. If you're new to high-fiber bars, the 5g or 8g tier is a gentler start.</p>
      </div>
      {section_cta_html('/bar-finder?fiber=5', f'See all {comma(len(TIER[5]))} bars with 5g+ fiber &rarr;',
                        'Opens the Bar Finder with the Min Fiber slider at 5g. Move it to any cutoff and stack it with protein, sugar or grade filters.')}
    </div>
'''

# ---------------------------------------------------------------------------
# Findings: three data findings + one chart
# ---------------------------------------------------------------------------
QUEST = by_brand('Quest')
QUEST_Q = [b for b in QUEST if QF(b)]
C.check(len(QUEST_Q) >= len(QUEST) / 2, 'most Quest flavors clear 11g of fiber')
top5 = Counter(b['Brand Name'] for b in Q).most_common(5)
TOP5_N = sum(n for _, n in top5)
C.check(TOP5_N > N / 3, 'five brands make up more than a third of the Extreme Fiber bars')
INSIGHTS = [
    ('Fiber drops off fast once you leave the top tier.',
     f"{comma(len(TIER[5]))} bars ({pct0(len(TIER[5]), NT)}%) clear 5g of fiber, {len(TIER[8])} ({pct0(len(TIER[8]), NT)}%) clear "
     f"8g, and just {N} ({pct0(N, NT)}%) clear 11g. Each step up cuts the pool by more than half."),
    ('Most 11g+ bars get there with added fiber.',
     f"{pct0(ANY_ADDED, N)}% use at least one added fiber, led by {AORDER[0].lower()} ({len(AHIT[AORDER[0]])} bars). "
     f"Only {len(WHOLE)} reach 11g on whole-food ingredients alone."),
    ("High fiber isn't a niche-brand thing.",
     f"{len(QUEST_Q)} of Quest's {len(QUEST)} flavors clear 11g, and five brands ({names_and(br for br, _n in top5)}) make up "
     f"{TOP5_N} of the {N} Extreme Fiber bars. But {N_CF} of the {N} grade C or below, so check the ingredient grade too."),
]
C.check(N_CF > N / 3, 'more than a third of the Extreme Fiber bars grade C or below')
GRADE_ROWS = [(g, sum(1 for b in Q if b['score_band'] == g), sum(1 for b in ALL if b['score_band'] == g)) for g in BAND_ORDER]
GRV = {g: round(100 * h / t) for g, h, t in GRADE_ROWS}
C.check(GRV['A'] < GRV['B'] and GRV['A'] < GRV['C'], 'A-grade bars reach 11g of fiber less often than B and C bars')
FINDINGS = findings_v2_html(f'What we found screening {DB_PUBLIC} bars for fiber', INSIGHTS,
                            grade_share_chart_html(GRADE_ROWS, title='Share of bars with 11g or more of fiber, by ingredient grade',
                                                   note=f'Out of the {DB_PUBLIC} bars in our database. A-grade bars reach 11g less often than B or C bars.'))

# ---------------------------------------------------------------------------
# Brands that do it well + big brands
# ---------------------------------------------------------------------------
WELL = brands_well_rows(ALL, QF, n=8)
C.check(sum(r['big'] for r in WELL) >= 1 and sum(not r['big'] for r in WELL) >= 2, 'brands-well has a big and 2+ small brands')
def well_why(r):
    lead = (f"All {r['total']} flavors clear 11g" if r['q'] == r['total'] else
            f"{r['q']} of {r['total']} flavors {'clears' if r['q'] == 1 else 'clear'} 11g")
    gm = r['grades']
    grades = (f"graded {next(iter(gm))}" if r['q'] == 1 else
              f"all {next(iter(gm))} grade" if len(gm) == 1 else grade_mix_text(gm) + ' grade')
    bp = best_pick(r['qual'])
    return (f"{lead}, {grades}, averaging {fnum(round(avg(r['qual'], 'Dietary Fiber (g)'), 1))}g fiber. Best pick: "
            f"{bp['Flavor Name']} ({bp['score_band']}, {fnum(FIB(bp))}g fiber, {fnum(P(bp))}g protein).")
BRANDS_WELL = brands_well_html(WELL, well_why, h2='Brands that do it well',
                               intro='Brands with at least 3 bars in our database, ranked by how much of their lineup clears 11g '
                                     'of fiber and how well those bars grade.')
def big_verdict(r):
    bp = best_pick(r['qual'])
    avgf = avg(r['bars'], 'Dietary Fiber (g)')
    low_n = sum(1 for b in r['qual'] if b['score_band'] in ('C', 'D', 'F'))
    low_txt = ('' if low_n * 2 <= r['q'] else
               f" {'All' if low_n == r['q'] else 'Most'} of those grade C or below, so check the label.")
    pick = f" Best pick: {bp['Flavor Name']} ({bp['score_band']}, {fnum(FIB(bp))}g fiber)." if bp else ''
    if r['q'] == 0:
        return f"None clear 11g. The lineup averages {fnum(round(avgf, 1))}g of fiber per bar."
    verb = 'clears' if r['q'] == 1 else 'clear'
    lead = 'Every flavor clears 11g.' if r['q'] == r['total'] else f"{'Only ' if r['q'] * 2 < r['total'] else ''}{r['q']} of {r['total']} {verb} 11g."
    return lead + (low_txt or pick)
BIG_HTML, BIG_ROWS = big_brands_html(
    ALL, QF, big_verdict, h2='How do the big brands fare on fiber?',
    intro=('Every brand with national grocery, big-box or Costco distribution, with how many of its bars clear 11g of fiber. '
           'Brand names link to our full reviews where we have one.'), qual_word='11g+')

# ---------------------------------------------------------------------------
# Top 50 + Bar Finder CTA + criteria
# ---------------------------------------------------------------------------
T50 = top50_rows(Q, 50)
TOP50 = top50_html(T50, h2='Top 50 high fiber protein bars',
                   intro='Every bar here has 11g of fiber or more. Ranked by ingredient grade first, then by protein per '
                         'calorie. Tap any row for nutrition facts and the full ingredient list.',
                   cols=('grade', 'fiber', 'protein', 'cal', 'sugar'), hide_mobile=('cal', 'sugar'))
FINDER = finder_cta_html(N, FINDER_HREF, desc=('The Bar Finder opens with the Min Fiber slider at 11g, the same cutoff this '
                                               'page uses. Slide it down to 5g or 8g for the other tiers, or add filters for '
                                               'protein, sugar, calories, grade, or ingredients to exclude.'))
CRITERIA = criteria_html(
    qualify_rule=('11g or more of dietary fiber per bar, straight off the nutrition panel (our Extreme Fiber tier). No macro '
                  f'or ingredient-grade gate beyond that. {N} of the {DB_PUBLIC} bars we track qualify, {N_AB} of them with an A '
                  'or B grade.'),
    picks=PICKS,
    extra_rules=['No bar from a national grocery or big-box brand qualified for the "Best from a big brand" spot that wasn\'t '
                 'already picked, so Most fiber per calorie takes its place.'])

# ---------------------------------------------------------------------------
# FAQ (answers may hold links; JSON-LD gets the plain text)
# ---------------------------------------------------------------------------
MOSTFIB = max(ALL, key=lambda b: (FIB(b), -len(b['Brand Name'])))
n_most = sum(1 for b in ALL if FIB(b) == FIB(MOSTFIB))
BEST = PK['Best overall']
FAQS = [
    ('How much fiber counts as high fiber in a protein bar?',
     f'We use three tiers. High Fiber is 5g or more, the same cutoff the FDA uses for an "excellent source of fiber" claim '
     f'({of_db(len(TIER[5]), NT)} bars). Very High Fiber is 8g or more ({len(TIER[8])} bars). Extreme Fiber, the tier this page '
     f'ranks, is 11g or more ({N} bars).'),
    ('What is the best high fiber protein bar?',
     f"By our rules, {full(BEST)}: {BEST['score_band']}-grade ingredients, {fnum(FIB(BEST))}g fiber and {fnum(P(BEST))}g protein"
     + (", though part of its fiber comes from IMO." if imo(BEST) else ".")
     + f" For the most fiber, {full(PK['Highest fiber'])} has {fnum(FIB(PK['Highest fiber']))}g."),
    ('What is the Extreme Fiber 100?',
     f"It's our name for the protein bars that carry 11g or more of fiber per bar, currently {N} of them, about {pct0(N, NT)}% "
     f"of the {DB_PUBLIC} bars we track, from {BRANDS_Q} brands. Our Best 10 and Top 50 come from this group."),
    ('What protein bar has the most fiber?',
     f"{full(MOSTFIB)}, at {fnum(FIB(MOSTFIB))}g of fiber per bar, "
     + ('the most of any bar in our database.' if n_most == 1 else 'tied for the most of any bar in our database.')),
    ('What ingredients make protein bars high in fiber?',
     'Mostly one of five added fibers: tapioca fiber, polydextrose, chicory root fiber or inulin, soluble corn fiber, or '
     f'isomalto-oligosaccharide (IMO). {pct0(ANY_ADDED, N)}% of Extreme Fiber bars contain at least one. The rest, '
     f'{pct0(len(WHOLE), N)}%, get there through whole-food ingredients like nuts, seeds, and legumes.'),
    ('Is more fiber always better in a protein bar?',
     "Not automatically. Fiber above roughly 10-15g in one sitting can cause bloating or digestive discomfort for people not used "
     "to it, especially from added isolates like polydextrose or IMO rather than whole-food fiber. If you're new to high fiber "
     'bars, the 5g or 8g tier is usually a gentler starting point than jumping straight to Extreme Fiber.'),
    ('Do high fiber protein bars grade lower on ingredient quality?',
     f"A little. {ab(Q)}% of Extreme Fiber bars grade A or B, against {ab(ALL)}% database-wide, and {N_CF} of the {N} grade C "
     f"or below. They average {fnum(round(avg(Q, 'Protein (g)'), 1))}g of protein against "
     f"{fnum(round(avg(ALL, 'Protein (g)'), 1))}g database-wide."),
    ('Is Quest high in fiber?',
     f"Mostly. {len(QUEST_Q)} of Quest's {len(QUEST)} flavors carry 11g of fiber or more, but most of those grade C or below "
     'on ingredients, so check the specific flavor.'),
    ('How often is this list updated?',
     'We update the database whenever new bars are added or a brand reformulates. Manufacturers do change their recipes over '
     'time, so always confirm against the packaging in front of you.'),
]
C.check(int(ab(Q)) < int(ab(ALL)), 'Extreme Fiber bars grade A or B a little less often than the database')
C.check(sum(1 for b in QUEST_Q if b['score_band'] in ('C', 'D', 'F')) > len(QUEST_Q) / 2, 'most 11g+ Quest flavors grade C or below')

# ---------------------------------------------------------------------------
# Regions
# ---------------------------------------------------------------------------
H1 = 'The 10 Best High Fiber Protein Bars'
TITLE = f'10 Best High Fiber Protein Bars ({DB_PUBLIC} Checked)'
DESC = (f'Only {pct0(N, NT)}% of protein bars have 11g+ fiber. We checked {DB_PUBLIC} and picked the 10 best of the {N} '
        'that do, plus the 5g and 8g tiers.')
OG_DESC = (f'{N} protein bars with 11g or more of fiber, the Extreme Fiber 100. Here are the 10 best, each picked by a '
           'published rule.')
C.check(len(DESC) <= 155, f'meta description under 155 characters ({len(DESC)})')
FAQS_PLAIN = [(q, plain_text(a)) for q, a in FAQS]
REGIONS = v2_head_regions(title=TITLE, h1=H1, desc=DESC, og_desc=OG_DESC, url=URL, about='High Fiber Protein Bars',
                          published=PUBLISHED, faqs=FAQS_PLAIN, picks=PICKS)
EDITORIAL = f'  <section class="section off" id="what-it-means">{MEANS}  </section>'
HERO = (f'<h1 class="hero-title">{esc(H1)}</h1>\n'
        f'    <p class="hero-sub">Fiber keeps you full and slows how fast a bar\'s carbs hit your bloodstream. The FDA calls 5g '
        f'an "excellent source," but the bars on this page go much further: 11g or more per bar, our Extreme Fiber tier, '
        f'also known as the Extreme Fiber 100.</p>\n'
        f'    <p class="hero-sub">Of the {DB_PUBLIC} bars we track, {N} clear 11g, about {pct0(N, NT)}%. Most get there with an '
        f'added fiber like tapioca fiber or chicory root, and {N_CF} of them grade C or below on ingredients, so our picks '
        f'only use A and B bars.</p>')
REGIONS += [
    ('hero', HERO),
    ('best10', best10_html(PICKS, h2='Best 10 high fiber protein bars', intro=B10_INTRO,
                           macros=[('Fiber', lambda b: f'{fnum(FIB(b))}g'), ('Protein', lambda b: f'{fnum(P(b))}g'),
                                   ('Calories', lambda b: fnum(CAL(b))), ('Sugar', lambda b: f'{fnum(SUG(b))}g')])),
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
        ('/best-bars-for-diabetics', 'Best Bars for Diabetics', 'Fiber is one of six checks in our blood sugar screen.'),
        ('/glp1-protein-bars', 'GLP-1 Protein Bars', 'High protein, low sugar bars built for fullness, fiber included.'),
        ('/keto-protein-bars', 'Keto Protein Bars', 'Low net carb bars with enough fat to fit a keto day.'),
    ])),
]

if __name__ == '__main__':
    page = build_guide_page_v2(PAGE, REGIONS, ALL, C, picks=PICKS)
    size = len(page.encode('utf-8'))
    faq_at = len(page[:page.find('<section class="guide-faq"')].encode('utf-8'))
    print(f'{PAGE}: {N} qualify ({N_AB} A/B), {ND} under 11g, {size:,} bytes, FAQ at byte {faq_at:,}')
    for i, (s_, b, why, n) in enumerate(PICKS, 1):
        print(f'  {i:2d}. {s_.label}: {full(b)} ({b["score_band"]}) [pool {n}]')
        print(f'      {why}')
