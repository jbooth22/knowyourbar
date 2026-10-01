#!/usr/bin/env python3
"""Rebuild caffeine-protein-bars.html from bars.js. GUIDE PAGE v2 ("Best" list).

Run from the repo root:  python3 build_caffeine_protein_bars.py

Layout and every rule: claude/GUIDE_PAGE_SPEC_V2.md (locked 2026-09-29) and
the v2 section of kyb_guide_lib.py. The first run migrated the live v1 page to
the v2 body (head, nav and footer kept as deployed); later runs rewrite only
the <!-- kyb:NAME --> regions. Every number, pick and brand row comes from
bars.js. Copy that depends on a fact is checked; if one stops being true the
build stops and lists it. Ingredient quality is shown and ranked as a GRADE only.

Screen: GUIDE_FILTERS['caffeine-protein-bars'] = Caffeine (mg) > 0 (any declared
amount, no dose minimum, no grade gate). Zones are measured against a ~95mg
8oz cup of coffee: Light < 50, Moderate 50-94, High 95-149, Very High 150+.

Best list (2026-09-30; Jeff asked for the best picks delivered without an
approval round): only 13 caffeinated bars pass the pick rules (A/B grade, 10g+
protein) and they come from 6 brands, so with the 2-per-brand cap the list
holds 8, not 10 (N_PICKS; the criteria section says why). Guide slots: Most
caffeine, Closest to a cup of coffee (50-94mg), Caffeine from coffee or tea,
Lowest sugar (no sugar alcohol). The dose slots pick right after Best overall
(PICK_ORDER) so they get first claim on the bars they're about; the cards
still show the six core slots first.
Bar Finder: it has no caffeine filter, so the CTA opens the Bar Finder and
says so; the page itself lists every caffeinated bar (the "All N" table).
"""
import re
from collections import Counter
from kyb_guide_lib import *

PAGE = 'caffeine-protein-bars.html'
URL = 'https://knowyourbar.com/caffeine-protein-bars'
PUBLISHED = '2026-04-10'
set_tie_seed('caffeine-protein-bars')   # per-guide shuffle for exact ties (kyb_guide_lib, 2026-09-30)

ALL = load_bars()
QF = GUIDE_FILTERS['caffeine-protein-bars']
Q = [b for b in ALL if QF(b)]
N, NT = len(Q), len(ALL)
BRANDS_Q = sorted({b['Brand Name'].strip() for b in Q}, key=str.lower)
GR = {g: sum(1 for b in Q if b.get('score_band') == g) for g in BAND_ORDER}
N_AB = GR['A'] + GR['B']
C = Claims()
def CF(b): return num(b.get('Caffeine (mg)')) or 0
def mg(v): return f'{fnum(round(v, 1))}mg'
MAXB = max(Q, key=lambda b: (CF(b), -len(nm(b))))
MAXC, MINC = CF(MAXB), min(CF(b) for b in Q)
E = v2_eligible(Q)
C.check(20 <= N <= 80, 'caffeine is still a small category (20 to 80 bars)')
C.check(not any(QF(b) for b in ALL if b['Brand Name'] in ('Quest', 'Barebells')), 'Quest and Barebells make no caffeinated bar')

ZONES = [('Light', 0, 50, 'under 50mg', 'A fraction of a cup of brewed coffee.'),
         ('Moderate', 50, 95, '50 to 94mg', 'Roughly a standard 8oz cup of coffee.'),
         ('High', 95, 150, '95 to 149mg', 'More than a cup, less than two.'),
         ('Very High', 150, 10 ** 6, '150mg or more', 'Energy-drink territory.')]
ZB = {z: [b for b in Q if lo <= CF(b) < hi] for z, lo, hi, _r, _d in ZONES}
def zone_of(b): return next(z for z, lo, hi, _r, _d in ZONES if lo <= CF(b) < hi)

SRC = [('coffee', r'\bcoffee\b(?! fruit)'), ('espresso', r'espresso'), ('matcha', r'matcha'), ('green tea', r'green tea'),
       ('yerba mate', r'yerba'), ('guarana', r'guarana'), ('guayusa', r'guayusa')]
def added_caffeine(b): return bool(re.search(r'\bcaffeine\b', ingr(b), re.I))
def src_names(b): return [n for n, rx in SRC if re.search(rx, ingr(b), re.I)]
def from_coffee_tea(b): return bool(src_names(b)) and not added_caffeine(b)
ADDED = [b for b in Q if added_caffeine(b)]
NATURAL = [b for b in Q if from_coffee_tea(b)]
UNNAMED = [b for b in Q if not added_caffeine(b) and not from_coffee_tea(b)]

# ---------------------------------------------------------------------------
# Best list (spec v2)
# ---------------------------------------------------------------------------
MOST_CAF = Slot('Most caffeine', 'The most caffeine per bar, grade B or better, 10g+ protein.',
                lambda E: E, lambda b: (-CF(b),) + tie_chain(b),
                lambda b, c: (f"{mg(CF(b))} of caffeine, {c['tied']}the most of any bar here with an A or B grade and 10g+ "
                              f"protein. That's about a cup of brewed coffee."),
                metric=CF)
CUP = slot_subset('Closest to a cup of coffee', '50 to 94mg of caffeine, about one 8oz cup of brewed coffee.',
                  lambda b: 50 <= CF(b) < 95, lambda b: f"{mg(CF(b))} of caffeine, about one cup of brewed coffee.")
NAT = slot_subset('Caffeine from coffee or tea',
                  'The caffeine comes from coffee, espresso, matcha or tea in the recipe, with no isolated caffeine added.',
                  from_coffee_tea,
                  lambda b: f"Its {mg(CF(b))} of caffeine comes from the {names_and(src_names(b))} in the recipe, not added caffeine.")
NOSA_SUGAR = Slot('Lowest sugar', 'The least sugar among bars with no sugar alcohol, grade B or better, 10g+ protein.',
                  lambda E: [b for b in E if not has_sugar_alcohol(b)], lambda b: (SUG(b),) + tie_chain(b),
                  lambda b, c: (f"{fnum(SUG(b))}g sugar, {c['tied']}the lowest of any bar here without sugar alcohols, with "
                                f"{fnum(P(b))}g protein and {mg(CF(b))} of caffeine."),
                  metric=SUG)
CORE = [slot_best_overall(15), slot_cleanest(), slot_highest_protein(300), slot_protein_per_cal(12), slot_lowest_calorie(),
        slot_big_brand()]
GUIDE = [MOST_CAF, CUP, NAT, NOSA_SUGAR]
PICK_ORDER = [CORE[0]] + GUIDE[:3] + CORE[1:] + GUIDE[3:]
DISPLAY = CORE + GUIDE
RAW = pick_best10(Q, PICK_ORDER, [])
PICKS = sorted(RAW, key=lambda p: DISPLAY.index(p[0]))
N_PICKS = len(PICKS)
max_possible = sum(min(V2_BRAND_CAP, n) for n in Counter(b['Brand Name'] for b in E).values())
C.check(N_PICKS == max_possible, f'the list holds as many picks as the rules allow ({max_possible})')
C.check(N_PICKS < 10, 'fewer than 10 picks (the page says why)')
C.check(not any(re.search(r'score \d|scored? \d', w) for _s, _b, w, _n in PICKS), 'no ingredient score printed in a pick')
PK = {s.label: b for s, b, _w, _n in PICKS}
EMPTY = [s.label for s in DISPLAY if s.label not in PK]
EMPTY_OTHER = [l for l in EMPTY if l != 'Best from a big brand']
C.check('Best from a big brand' in EMPTY, 'no big-brand caffeinated bar passes the pick rules')
C.check(all(k in PK for k in ('Best overall', 'Most caffeine', 'Closest to a cup of coffee', 'Caffeine from coffee or tea')),
        'the overall and dose slots all filled')
C.check(CF(PK['Most caffeine']) == max(CF(b) for b in E), 'Most caffeine holds the top dose among eligible bars')
B10_INTRO = (f"Only {len(E)} caffeinated bars have an A or B ingredient grade and 10g+ protein, and they come from "
             f"{len({b['Brand Name'] for b in E})} brands. With at most {V2_BRAND_CAP} per brand, that makes {num_word(N_PICKS)} "
             "picks, each the winner of one thing people shop for. No bar appears twice.")

# ---------------------------------------------------------------------------
# What it means: four zones + where the caffeine comes from (v1 editorial, trimmed)
# ---------------------------------------------------------------------------
def zone_desc(z, rng, lead):
    bs = ZB[z]
    if not bs:
        return f'{lead} No bar in our database lands here right now.'
    brands = [br.strip() for br, _n in Counter(b['Brand Name'] for b in bs).most_common()]
    lo, hi = grade_range(bs)
    grades = f'grade {lo}' if lo == hi else f'grades {lo} to {hi}'
    who = f'All {brands[0]}' if len(brands) == 1 else f'Led by {names_and(brands[:2])}'
    return f'{rng}. {lead} {who}; {grades}.'
MEANS = f'''
    <div class="section-inner">
      <h2 class="section-title">Four caffeine zones, measured against a cup of coffee</h2>
      <div class="section-body">
        <p>Every bar on this page lists its caffeine on the label. We grouped all {N} by how that dose compares to an 8oz cup of brewed coffee, which runs roughly 95mg. Most people buying a caffeinated bar want it to stand in for that cup, so the Moderate zone is where most of our picks sit.</p>
      </div>
      <div class="score-grid" style="margin-top:1.5rem;">
{chr(10).join(v2_count_card_html(f'{z} caffeine', ZB[z], N, zone_desc(z, rng, lead)) for z, _lo, _hi, rng, lead in ZONES)}
      </div>
      <h3 class="kt-h3">Where the caffeine comes from</h3>
      <div class="section-body">
        <p>Some bars get their caffeine from real coffee, espresso, matcha or tea in the recipe, which brings other plant compounds along with it. Others add caffeine directly, listed as "caffeine" (often "green tea caffeine" or "caffeine from green coffee"). Both count the same on the label; the ingredient list tells you which route a bar took. Of the {N} bars here, {len(ADDED)} add caffeine directly and {len(NATURAL)} get it from coffee or tea alone.{f" {len(UNNAMED)} list caffeine on the nutrition panel without naming a source in the ingredients." if UNNAMED else ""}</p>
        <p>The FDA cites 400mg a day as an amount not generally linked to negative effects in healthy adults. A light or moderate bar is a small part of that; a Very High bar can be most of it on its own, before your morning coffee.</p>
      </div>
      <div class="callout-box"><strong>Heads up:</strong> We are not doctors or dietitians, and this page is not medical advice. Talk to your doctor if you have questions about caffeine and your health, especially if you are pregnant, sensitive to stimulants, or stack these with other caffeinated drinks.</div>
    </div>
'''

# ---------------------------------------------------------------------------
# Findings: three data findings + one chart
# ---------------------------------------------------------------------------
VH = ZB['Very High']
VH_BRANDS = sorted({b['Brand Name'].strip() for b in VH})
C.check(VH and all(b['score_band'] in ('D', 'F') for b in VH), 'every Very High bar grades D or F')
C.check(VH and all(P(b) < 10 for b in VH), 'every Very High bar has under 10g protein')
C.check(MAXC >= 200, 'the highest-dose bar is a large share of the daily 400mg guidance')
LOWP = [b for b in Q if P(b) < 10]
C.check(len(LOWP) > N / 3, 'more than a third of caffeinated bars have under 10g protein')
VERB = [b for b in Q if b['Brand Name'] == 'Verb']
VERB_LOWP = [b for b in VERB if P(b) < 10]
C.check(len(VERB) == max(Counter(b['Brand Name'] for b in Q).values()), 'Verb is the largest caffeinated lineup')
C.check(len({CF(b) for b in VERB}) == 1, 'every Verb flavor has the same caffeine dose')
INSIGHTS = [
    ('Only about 3% of protein bars have any caffeine.',
     f"{N} of the {DB_PUBLIC} bars we track list caffeine, from {len(BRANDS_Q)} brands. Most big brands, including Quest and "
     "Barebells, skip it entirely."),
    ('The biggest doses come with the worst ingredients.',
     f"All {len(VH)} bars at 150mg or more come from {names_and(VH_BRANDS)}, grade {names_and(sorted({b['score_band'] for b in VH}))}, "
     f"and have under {fnum(max(P(b) for b in VH) + 1)}g of protein. The top one carries {mg(MAXC)}, about "
     f"{round(100 * MAXC / 400)}% of the FDA's 400mg daily figure."),
    ('Plenty of caffeinated bars are light on protein.',
     f"{len(LOWP)} of the {N} have under 10g of protein, including {len(VERB_LOWP)} of Verb's {len(VERB)} flavors (all "
     f"{mg(CF(VERB[0]))}). That's why only {len(E)} bars could make our list."),
]
C.check(round(100 * N / NT) == 3, 'caffeinated bars are about 3% of the database')
GRADE_ROWS = [(g, GR[g], N) for g in BAND_ORDER]
C.check(GR['B'] == max(GR.values()), 'B is the most common grade among caffeinated bars')
FINDINGS = findings_v2_html(f'What we found screening {DB_PUBLIC} bars for caffeine', INSIGHTS,
                            grade_share_chart_html(GRADE_ROWS, title=f'How the {N} caffeinated bars grade on ingredients',
                                                   note=f'Share of the {N} bars with caffeine in each ingredient grade. '
                                                        f'{N_AB} of {N} grade A or B.'))

# ---------------------------------------------------------------------------
# Brands that do it well + big brands
# ---------------------------------------------------------------------------
WELL = brands_well_rows(ALL, QF, n=8)
def well_why(r):
    lead = (f"All {r['total']} flavors have caffeine" if r['q'] == r['total'] else
            f"{r['q']} of {r['total']} flavors {'has' if r['q'] == 1 else 'have'} caffeine")
    doses = sorted({CF(b) for b in r['qual']})
    dose = mg(doses[0]) if len(doses) == 1 else f'{mg(doses[0])} to {mg(doses[-1])}'
    bp = best_pick(r['qual'])
    return (f"{lead}, at {dose}. Best pick: {bp['Flavor Name']} ({bp['score_band']}, {mg(CF(bp))}, "
            f"{fnum(P(bp))}g protein).")
BRANDS_WELL = brands_well_html(WELL, well_why, h2='Brands that do it well',
                               intro='Brands with at least 3 bars in our database, ranked by how much of their lineup has '
                                     'caffeine and how well those bars grade.')
CAF_BRANDS = {b['Brand Name'] for b in Q}
def big_verdict(r):
    bs = sorted(r['qual'], key=lambda b: -CF(b))
    doses = sorted({CF(b) for b in bs})
    dose = mg(doses[0]) if len(doses) == 1 else f'{mg(doses[0])} to {mg(doses[-1])}'
    lo, hi = grade_range(bs)
    low = all(b['score_band'] in ('C', 'D', 'F') for b in bs)
    return (f"{'Only ' if r['q'] * 2 < r['total'] else ''}{r['q']} of {r['total']} {'has' if r['q'] == 1 else 'have'} caffeine, "
            f"at {dose}" + (f", grading {lo if lo == hi else f'{lo} to {hi}'}, so check the label." if low else '.'))
BIG_HTML, BIG_ROWS = big_brands_html(
    [b for b in ALL if b['Brand Name'] in CAF_BRANDS], QF, big_verdict, h2='How do the big brands fare on caffeine?',
    intro='Big brands with national grocery, big-box or Costco distribution that make a caffeinated bar. '
          'Brand names link to our full reviews where we have one.', qual_word='Have caffeine')
NONE_BIG = [br for br in BIG_BRANDS if br not in CAF_BRANDS and any(b['Brand Name'] == br for b in ALL)]
C.check(BIG_ROWS and all(r['q'] for r in BIG_ROWS), 'the big-brands table lists only big brands that make a caffeinated bar')
BIG_HTML = BIG_HTML.replace('\n    </div>', f'\n      <p class="section-body">The other {len(NONE_BIG)} big brands we track '
                            f'({esc(names_and(NONE_BIG[:4]))} and {len(NONE_BIG) - 4} more) make no caffeinated bar.</p>\n    </div>', 1) \
    if BIG_HTML.endswith('\n    </div>') else BIG_HTML
C.check(f'The other {len(NONE_BIG)} big brands' in BIG_HTML, 'big-brands note added')

# ---------------------------------------------------------------------------
# All N + Bar Finder CTA + criteria
# ---------------------------------------------------------------------------
TOP = top50_rows(Q, 50)
C.check(len(TOP) == N, 'the list below shows every caffeinated bar')
ALL_LIST = top50_html(TOP, h2=f'All {N} protein bars with caffeine',
                      intro='Every bar in our database that lists caffeine. Ranked by ingredient grade first, then by protein '
                            'per calorie. Tap any row for nutrition facts and the full ingredient list.',
                      cols=('grade', 'caffeine', 'protein', 'cal', 'sugar'), hide_mobile=('cal', 'sugar'))
FINDER = finder_cta_html(NT, '/bar-finder', desc=(
    f"The Bar Finder can't filter by caffeine yet, so every caffeinated bar is listed on this page. Open the Bar Finder to "
    "compare any bar's nutrition and ingredients, or filter the full database by protein, sugar, grade and ingredients to avoid."))
_see_all = f'See all {comma(NT)} in the Bar Finder &rarr;'
C.check(FINDER.count(_see_all) == 2, 'finder CTA heading and button found')
FINDER = FINDER.replace(f'<h2 class="explore-cta-main-heading">{_see_all}</h2>',
                        '<h2 class="explore-cta-main-heading">Compare bars in the Bar Finder &rarr;</h2>', 1)
FINDER = FINDER.replace(_see_all, 'Open the Bar Finder &rarr;', 1)
CRITERIA = criteria_html(
    qualify_rule=(f'Any caffeine listed on the label, no minimum dose. No macro or ingredient-grade gate beyond that. {N} of '
                  f'the {DB_PUBLIC} bars we track qualify, {N_AB} of them with an A or B grade.'),
    picks=PICKS, n_spots=N_PICKS,
    extra_rules=[f'No caffeinated bar from a national grocery or big-box brand has an A or B grade and 10g+ protein, so there '
                 'is no "Best from a big brand" pick.'] +
                ([f'{names_and(EMPTY_OTHER)} had no eligible bar left once the other picks were made, so '
                  f'{"it is" if len(EMPTY_OTHER) == 1 else "they are"} not on the list.'] if EMPTY_OTHER else []))

# ---------------------------------------------------------------------------
# FAQ (answers may hold links; JSON-LD gets the plain text)
# ---------------------------------------------------------------------------
def brand_faq(name, verdict):
    bs = [b for b in Q if b['Brand Name'] == name]
    C.check(bs, f'{name} still makes a caffeinated bar')
    doses = sorted({CF(b) for b in bs})
    lo, hi = grade_range(bs)
    lowp = sum(1 for b in bs if P(b) < 10)
    return (f"{verdict} {len(bs)} {name} flavors list caffeine, "
            + (f"all at {mg(doses[0])}" if len(doses) == 1 else f"at {mg(doses[0])} to {mg(doses[-1])}")
            + f", grading {lo if lo == hi else f'{lo} to {hi}'} on ingredients"
            + (f". {lowp} of them have under 10g of protein, so pick the flavor carefully." if lowp else '.'))
BEST = PK['Best overall']
MOSTC = PK['Most caffeine']
N_UNDER95 = len(ZB['Light']) + len(ZB['Moderate'])
FAQS = [
    ('What is the best protein bar with caffeine?',
     f"By our rules, {full(BEST)}: {BEST['score_band']}-grade ingredients, {fnum(P(BEST))}g protein and {mg(CF(BEST))} of "
     f"caffeine. For more caffeine, {full(MOSTC)} has {mg(CF(MOSTC))} with {MOSTC['score_band']}-grade ingredients."),
    ('How much caffeine is in these protein bars compared to coffee?',
     f'An 8oz cup of brewed coffee runs roughly 95mg. Bars on this page range from {mg(MINC)} up to {mg(MAXC)}. '
     f'{N_UNDER95} of the {N} have less than a cup of coffee, and {len(VH)} are at 150mg or more.'),
    ('Is 80mg of caffeine a lot?',
     "80mg is a little under a standard cup of drip coffee. A shot of espresso is roughly 60 to 65mg and many energy drinks run "
     "150 to 300mg."),
    ('What is the difference between natural and added caffeine?',
     'Some bars get caffeine from coffee, espresso, matcha or tea in the recipe, which brings other plant compounds with it. '
     'Others add caffeine directly, often listed as green tea caffeine or caffeine from green coffee. The total on the label '
     f'counts the same either way. {len(NATURAL)} of the {N} bars here use coffee or tea alone, and {len(ADDED)} add caffeine.'),
    ('How much caffeine in a protein bar is too much?',
     'That depends on everything else you drink and on how sensitive you are. The FDA cites 400mg a day for healthy adults. '
     f'A light or moderate bar is a small part of that, but the {len(VH)} bars on this page at 150mg or more take a large share '
     'on their own. This page is not medical advice; talk to your doctor if you have questions about caffeine and your health.'),
    ('Why do so few protein bars contain caffeine?',
     'A brand has to build a bar around caffeine on purpose, and most don\'t. Only '
     f'{N} of the {DB_PUBLIC} bars in our database list any caffeine. Quest and Barebells skip it entirely.'),
    ('Is Verb good for caffeine?', brand_faq('Verb', 'For caffeine, yes. For protein, mostly not.')),
    ('Is Quantum good for caffeine?', brand_faq('Quantum', 'Yes, if you want a full cup\'s worth.')),
    ('How many protein bars in your database contain caffeine?',
     f'{N} of the {DB_PUBLIC} bars in our database list caffeine, about {pct0(N, NT)}%, from {len(BRANDS_Q)} brands. Any listed '
     'amount counts.'),
]
C.check(sum(1 for b in VERB if P(b) < 10) > len(VERB) / 2, 'most Verb flavors have under 10g protein')
QUANTUM = [b for b in Q if b['Brand Name'] == 'Quantum']
C.check(QUANTUM and all(b['score_band'] in ('A', 'B') and CF(b) >= 95 for b in QUANTUM), 'every Quantum flavor is A/B at 95mg+')

# ---------------------------------------------------------------------------
# Regions
# ---------------------------------------------------------------------------
H1 = f'The {N_PICKS} Best Protein Bars with Caffeine'
TITLE = f'{N_PICKS} Best Protein Bars with Caffeine ({DB_PUBLIC} Checked)'
DESC = (f'Only {N} of {DB_PUBLIC} protein bars have caffeine, from {mg(MINC)} to {mg(MAXC)}. Here are the {N_PICKS} best, '
        'plus how each compares to a cup of coffee.')
OG_DESC = (f'{N} protein bars list caffeine. Here are the {N_PICKS} best, each picked by a published rule, with every dose '
           'compared to a cup of coffee.')
C.check(len(DESC) <= 155, f'meta description under 155 characters ({len(DESC)})')
FAQS_PLAIN = [(q, plain_text(a)) for q, a in FAQS]
REGIONS = v2_head_regions(title=TITLE, h1=H1, desc=DESC, og_desc=OG_DESC, url=URL, about='Caffeinated Protein Bars',
                          published=PUBLISHED, faqs=FAQS_PLAIN, picks=PICKS)
EDITORIAL = f'  <section class="section off" id="what-it-means">{MEANS}  </section>'
HERO = (f'<h1 class="hero-title">{esc(H1)}</h1>\n'
        f'    <p class="hero-sub">A caffeinated protein bar is meant to do two jobs at once: a snack and your coffee. The dose '
        f'is what matters, so we compare every bar to an 8oz cup of brewed coffee, about 95mg.</p>\n'
        f'    <p class="hero-sub">Only {N} of the {DB_PUBLIC} bars we track list any caffeine, from {mg(MINC)} to {mg(MAXC)}. '
        f'The highest doses come from the worst-graded bars, and {len(LOWP)} of the {N} have under 10g of protein, so our '
        f'picks use A and B bars with 10g or more.</p>')
REGIONS += [
    ('hero', HERO),
    ('best10', best10_html(PICKS, h2=f'Best {N_PICKS} protein bars with caffeine', intro=B10_INTRO,
                           macros=[('Caffeine', lambda b: mg(CF(b))), ('Protein', lambda b: f'{fnum(P(b))}g'),
                                   ('Calories', lambda b: fnum(CAL(b))), ('Sugar', lambda b: f'{fnum(SUG(b))}g')])),
    ('editorial', EDITORIAL),
    ('findings', FINDINGS),
    ('brands-well', BRANDS_WELL),
    ('big-brands', BIG_HTML),
    ('top50', ALL_LIST),
    ('finder-cta', FINDER),
    ('criteria', CRITERIA),
    ('faq', faq_items_html(FAQS)),
    ('author', byline_html()),
    ('explore-more', related_html([
        ('/creatine-protein-bars', 'Creatine Protein Bars', 'The other supplement-style bar: how much creatine each one really has.'),
        ('/clean-protein-bars', 'Clean Protein Bars', 'A or B grade bars with no artificial sweeteners and no seed oils.'),
        ('/no-artificial-sweeteners', 'No Artificial Sweeteners', 'Bars sweetened without sucralose or ace-K, ranked the same way.'),
    ])),
]

if __name__ == '__main__':
    page = build_guide_page_v2(PAGE, REGIONS, ALL, C, picks=PICKS, n_picks=N_PICKS)
    size = len(page.encode('utf-8'))
    faq_at = len(page[:page.find('<section class="guide-faq"')].encode('utf-8'))
    print(f'{PAGE}: {N} qualify ({N_AB} A/B, {len(E)} eligible), {size:,} bytes, FAQ at byte {faq_at:,}')
    for i, (s_, b, why, n) in enumerate(PICKS, 1):
        print(f'  {i:2d}. {s_.label}: {full(b)} ({b["score_band"]}) [pool {n}]')
        print(f'      {why}')
