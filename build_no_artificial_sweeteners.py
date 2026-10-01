#!/usr/bin/env python3
"""Rebuild no-artificial-sweeteners.html from bars.js. GUIDE PAGE v2 ("Best 10").

Run from the repo root:  python3 build_no_artificial_sweeteners.py

Layout and every rule: claude/GUIDE_PAGE_SPEC_V2.md (locked 2026-09-29) and
the v2 section of kyb_guide_lib.py. Built the same way as the pilot,
build_no_sugar_alcohols.py. The first run migrated the live v1 page to the v2
body (head, nav and footer kept as deployed); later runs rewrite only the
<!-- kyb:NAME --> regions. Every number, pick and brand row comes from bars.js.
Copy that depends on a fact is checked; if one stops being true the build
stops and lists it. Ingredient quality is shown and ranked as a GRADE only.

Screen: GUIDE_FILTERS['no-artificial-sweeteners'] (no 'Artificial Sweeteners'
concern tag). The four sweeteners in the copy are counted by ingredient text.
Every artificial-sweetener bar in bars.js contains sucralose, so the Bar Finder
link is /bar-finder?excl=sucralose (same set, checked below).

Guide slots (locked with Jeff 2026-09-29): Best stevia or monk fruit (the only
sweetener: no allulose, no sugar alcohol, no added sugar or syrup), Lowest
sugar (among bars that also have no sugar alcohol), Best plant-based (15g+),
Highest fiber (replaces Best date-sweetened to cut overlap with the No Sugar
Alcohols guide). Fallbacks: Best allulose-sweetened, then Best snack size.
"""
import re
from collections import defaultdict
from kyb_guide_lib import *

PAGE = 'no-artificial-sweeteners.html'
URL = 'https://knowyourbar.com/no-artificial-sweeteners'
PUBLISHED = '2026-04-08'
set_tie_seed('no-artificial-sweeteners')   # per-guide shuffle for exact ties (kyb_guide_lib, 2026-09-30)

ALL = load_bars()
QF = GUIDE_FILTERS['no-artificial-sweeteners']
Q = [b for b in ALL if QF(b)]
# Bars with neither an artificial sweetener nor a sugar alcohol. Bar Finder:
# ?preset=no_sugar_alcohol&excl=sucralose (app.js hasSugarAlcohol mirrors has_sugar_alcohol;
# every artificial-sweetener bar contains sucralose, checked below).
NEITHER = [b for b in ALL if not has_sugar_alcohol(b) and 'sucralose' not in (b.get('Ingredients') or '').lower()]
D = [b for b in ALL if not QF(b)]
N, ND, NT = len(Q), len(D), len(ALL)
BRANDS_Q = len({b['Brand Name'] for b in Q})
C = Claims()

SWEETENERS = [  # label, ingredient keywords
    ('Sucralose', ['sucralose']),
    ('Acesulfame Potassium', ['acesulfame', 'ace-k']),
    ('Aspartame', ['aspartame']),
    ('Saccharin', ['saccharin']),
]
def has_sw(b, label):
    t = ingr(b).lower()
    return any(w in t for w in dict(SWEETENERS)[label])
HIT = {label: [b for b in ALL if has_sw(b, label)] for label, _ in SWEETENERS}
SUC = HIT['Sucralose']
ACE = HIT['Acesulfame Potassium']
NON_SUC = [b for lbl in ('Acesulfame Potassium', 'Aspartame', 'Saccharin') for b in HIT[lbl]]
SUC_FREE = [b for b in ALL if not has_sw(b, 'Sucralose')]
PCT_D = pct0(ND, NT)
ONE_IN = round(NT / len(SUC)) if SUC else 0
ACE_BRANDS = sorted({b['Brand Name'] for b in ACE})

C.check(all(any(has_sw(b, l) for l, _ in SWEETENERS) for b in D) and not any(any(has_sw(b, l) for l, _ in SWEETENERS) for b in Q),
        'the four named sweeteners match the Artificial Sweeteners screen exactly')
C.check(all(has_sw(b, 'Sucralose') for b in NON_SUC), 'every ace-K / aspartame / saccharin bar also contains sucralose')
C.check({b['Key'] for b in SUC_FREE} == {b['Key'] for b in Q}, 'sucralose-free set == no-artificial-sweetener set (Bar Finder excl=sucralose)')
C.check({b['Key'] for b in NEITHER} == {b['Key'] for b in Q if not has_sugar_alcohol(b)}, 'no_sugar_alcohol + excl=sucralose == bars with neither')
C.check(len(SUC) == ND, 'sucralose is in every disqualified bar')
C.check(not HIT['Aspartame'] and not HIT['Saccharin'], 'no aspartame or saccharin bars in the database')
C.check(len(ACE_BRANDS) == 2, 'exactly two brands use acesulfame potassium')

def link(href, text): return f'<a href="{href}">{text}</a>'
def by_brand(brand, bars=ALL): return [b for b in bars if b['Brand Name'] == brand]

# ---------------------------------------------------------------------------
# Best 10 (spec v2; guide slots locked with Jeff 2026-09-29)
# ---------------------------------------------------------------------------
STEVIA_RX = r'stevia|reb ?a\b|rebaudioside|monk ?fruit|luo han'
OTHER_SUB = re.compile(r'allulose|erythritol|xylitol|sorbitol|maltitol|isomalt|tagatose', re.I)
ADDED_SUGAR = re.compile(r'cane sugar|\bsugar\b|honey|syrup|agave|coconut sugar|molasses|nectar|dextrose|fructose|'
                         r'sucrose|juice concentrate', re.I)
def stevia_mf(b): return bool(re.search(STEVIA_RX, ingr(b), re.I))
def stevia_only(b):
    """Stevia or monk fruit is the only sweetener added: no allulose, no sugar
    alcohol, no added sugar or syrup (fruit and dates in the recipe are fine)."""
    t = ingr(b)
    return stevia_mf(b) and not OTHER_SUB.search(t) and not ADDED_SUGAR.search(t) and not has_tag(b, 'Sugar Alcohols')
def no_sa(b): return not has_sugar_alcohol(b)
def plant_based(b): return b.get('Vegan (Y/N)') == 'Yes'
def allulose(b): return 'allulose' in ingr(b).lower()
def sm_word(b):
    t = ingr(b).lower()
    s, m = bool(re.search(r'stevia|reb ?a\b|rebaudioside', t)), bool(re.search(r'monk ?fruit|luo han', t))
    return 'stevia and monk fruit' if s and m else 'stevia' if s else 'monk fruit'

LOW_SUGAR = Slot('Lowest sugar', 'The least sugar among bars that also have no sugar alcohol, grade B or better, 10g+ protein.',
                 lambda E: [b for b in E if no_sa(b)], lambda b: (SUG(b),) + tie_chain(b),
                 lambda b, c: (f"{fnum(SUG(b))}g sugar with {fnum(P(b))}g protein and no sugar alcohol either, {c['tied']}the "
                               "lowest sugar of any bar here that skips both" + (f", and it wins the tie on {c['tie_on']}." if c['tied'] and c['tie_on'] != 'name' else ".")),
                 metric=SUG)
SLOTS = [
    slot_best_overall(15),
    slot_cleanest(),
    slot_highest_protein(300),
    slot_protein_per_cal(12),
    slot_lowest_calorie(),
    slot_big_brand(),
    slot_subset('Best stevia or monk fruit',
                'Stevia or monk fruit is the only sweetener added: no allulose, no sugar alcohol, no added sugar or syrup.',
                stevia_only, lambda b: f"Sweetened only with {sm_word(b)}, plant-derived and zero-calorie, with no allulose, "
                                       "sugar alcohol or added sugar."),
    LOW_SUGAR,
    slot_subset('Best plant-based', 'Vegan-labeled bars.', plant_based,
                lambda b: 'Vegan, and free of every artificial sweetener we screen for.', floor=15),
    slot_highest_fiber(),
]
FALLBACKS = [
    slot_subset('Best allulose-sweetened', 'Allulose on the label.', allulose,
                lambda b: "Sweetened with allulose, a rare sugar that doesn't count toward the Sugars line."),
    slot_subset('Best snack size', 'Under 150 calories.', lambda b: CAL(b) < 150, lambda b: f'Under 150 calories ({fnum(CAL(b))}).'),
]
PICKS = pick_best10(Q, SLOTS, FALLBACKS)
C.check(len(PICKS) == 10, 'ten Best 10 picks available')
C.check([s.label for s, *_ in PICKS] == [s.label for s in SLOTS], 'all ten planned slots filled without fallbacks')
C.check(not any(re.search(r'score \d|scored? \d', w) for _s, _b, w, _n in PICKS), 'no ingredient score printed in a pick')
B10_INTRO = ("Ten bars with no artificial sweeteners, each the winner of one thing people shop for. Every pick has an A or B "
             "ingredient grade and at least 10g of protein, and no bar appears twice.")

# ---------------------------------------------------------------------------
# What it means: one card per sweetener
# ---------------------------------------------------------------------------
DESC = {
    'Sucralose': 'Usually shows up as a flavor-rounding sweetener in low-sugar or high-fiber bars, often alongside allulose '
                 'or fiber syrups to hit a specific sugar number on the label.',
    'Acesulfame Potassium': 'Always paired with sucralose in the bars we track, never used on its own, adding a sweetness '
                            'boost on top of the primary sweetener.',
    'Aspartame': 'Once common in diet foods generally, it has largely fallen out of favor in the protein bar category.',
    'Saccharin': 'The oldest artificial sweetener on this screen, now rare in this category.',
}
def sw_desc(label):
    n = len(HIT[label])
    if n == 0:
        return 'Not currently used in any bar we track. ' + DESC[label]
    return DESC[label]
CARDS = '\n'.join(v2_count_card_html(l, HIT[l], NT, sw_desc(l)) for l, _ in SWEETENERS)
MEANS = f'''
    <div class="section-inner">
      <h2 class="section-title">What "no artificial sweeteners" actually means</h2>
      <div class="section-body">
        <p>Artificial sweeteners are the synthetic, zero-calorie sweeteners bar makers reach for when they want sweetness without sugar on the label. This guide screens every bar for four of them: sucralose, acesulfame potassium, aspartame, and saccharin.</p>
        <p>{PCT_D}% of the {DB_PUBLIC} bars in our database still have one on the label. Here is how often each one shows up, and where it usually hides.</p>
      </div>
      <div class="score-grid" style="margin-top:1.5rem;">
{CARDS}
      </div>
      <h3 class="kt-h3">Stevia and monk fruit are not on this screen</h3>
      <div class="section-body">
        <p>Stevia leaf extract and monk fruit (luo han guo) extract are plant-derived, not synthetic, so they don't count against a bar here. {len([b for b in Q if stevia_mf(b)])} of the {comma(N)} qualifying bars use one of them. If you want to avoid every non-sugar sweetener, including plant-derived ones, check the ingredient list yourself.</p>
        <p>Artificial sweeteners are not the same thing as sugar alcohols either. Erythritol, maltitol, and xylitol are sugar alcohols, a different category with their own digestive tradeoffs, and they show up on a different screen. {len([b for b in Q if not no_sa(b)])} bars on this page skip artificial sweeteners but still contain a sugar alcohol. If that's what you want to avoid, see our {link('/no-sugar-alcohols', 'protein bars without sugar alcohols guide')}. {comma(len(NEITHER))} bars in our database have neither.</p>
      </div>
      {section_cta_html('/bar-finder?preset=no_sugar_alcohol&excl=sucralose', f'See all {comma(len(NEITHER))} bars with neither &rarr;',
                        'Opens the Bar Finder with the No Sugar Alcohols filter on and sucralose excluded (every artificial-sweetener bar we track contains it).')}
    </div>
'''

# ---------------------------------------------------------------------------
# Protein bars without sucralose (anchor #no-sucralose, linked from no-sugar-alcohols)
# ---------------------------------------------------------------------------
SUC_HREF = '/bar-finder?excl=sucralose'
SUCRALOSE = f'''
    <div class="section-inner">
      <h2 class="section-title">Protein bars without sucralose</h2>
      <div class="section-body">
        <p>Sucralose, sold under the brand name Splenda, is the artificial sweetener actually driving this guide. It is a chlorinated sugar substitute, roughly 600 times sweeter than table sugar, with zero calories and no effect on blood sugar. People skip it for different reasons: reported digestive discomfort, an aftertaste they don't like, gut microbiome research they've read, or just a preference to avoid synthetic sweeteners entirely.</p>
        <p>{of_db(len(SUC), NT, True)} bars we track, about 1 in {ONE_IN}, contain sucralose. We checked whether screening for sucralose on its own produces a different list than screening for all four artificial sweeteners this guide covers. It doesn't. Every bar in our database that contains acesulfame potassium also contains sucralose, and none contain aspartame or saccharin, so protein bars without sucralose and protein bars without artificial sweeteners are the exact same {comma(N)} bars across {BRANDS_Q} brands. The <a href="#best-10">Best 10</a> and <a href="#top-50">Top 50</a> on this page are all sucralose-free.</p>
      </div>
      {section_cta_html(SUC_HREF, f'See all {comma(len(SUC_FREE))} sucralose-free bars in the Bar Finder &rarr;',
                        'Opens the Bar Finder with sucralose excluded. Add your own filters for protein, sugar, calories, grade, or brand.')}
      <p class="section-body" style="margin-top:1.25rem;">Looking for a bar that also skips sugar alcohols like erythritol and maltitol? See our {link('/no-sugar-alcohols#no-erythritol', 'protein bars without erythritol')} section, or the {link('/clean-protein-bars', 'Clean Protein Bars guide')}, which requires an A or B ingredient grade with no artificial sweeteners and no processed oils. Net carbs matter more than the sweetener itself? Our {link('/keto-protein-bars', 'Keto')} and {link('/best-bars-for-diabetics', 'Best Bars for Diabetics')} guides both allow sucralose, since it doesn't affect net carbs or blood sugar, but they exclude the maltitol family specifically.</p>
    </div>
'''
C.check(not any(has_maltitol_family(b) for b in ALL if GUIDE_FILTERS['keto-protein-bars'](b)), 'keto guide excludes the maltitol family')
C.check(not any(has_maltitol_family(b) for b in ALL if GUIDE_FILTERS['best-bars-for-diabetics'](b)), 'diabetics guide excludes the maltitol family')
C.check(any(has_sw(b, 'Sucralose') for b in ALL if GUIDE_FILTERS['keto-protein-bars'](b)), 'keto allows sucralose')
C.check(any(has_sw(b, 'Sucralose') for b in ALL if GUIDE_FILTERS['best-bars-for-diabetics'](b)), 'diabetics allows sucralose')

# ---------------------------------------------------------------------------
# Findings: three data findings + one chart (spec v2 section 5)
# ---------------------------------------------------------------------------
def tucked(b):
    t = ingr(b).lower()
    m = re.search(r'\d\s*%\s*or\s*less|less than\s*\d\s*%', t)
    return bool(m) and t.find('sucralose') > m.start()
TUCKED = [b for b in SUC if tucked(b)]
NAMED = [b for b in SUC if not tucked(b)]
EXAMPLES = [b for key in [('Pure Protein', 'Chocolate Deluxe'), ('FITCRUNCH', 'Chocolate Peanut Butter')]
            for b in NAMED if (b['Brand Name'], b['Flavor Name']) == key]
C.check(len(EXAMPLES) == 2, 'Pure Protein Chocolate Deluxe and FITCRUNCH Chocolate Peanut Butter list sucralose outside a 2%-or-less clause')
C.check(len(NAMED) > len(TUCKED), 'most sucralose bars list it outside a 2%-or-less clause')

GRADE_ROWS = [(g, sum(1 for b in D if b['score_band'] == g), sum(1 for b in ALL if b['score_band'] == g)) for g in BAND_ORDER]
GR = {g: round(100 * h / t) for g, h, t in GRADE_ROWS}
C.check(GR['A'] <= GR['B'] <= GR['C'] <= GR['D'] <= GR['F'] and GR['A'] < GR['F'], 'artificial sweetener share never falls with a step down in grade, and F is well above A')
INSIGHTS = [
    ('Sucralose is behind every one of them.',
     f'All {ND} bars that fail this screen contain sucralose. The {len(ACE)} bars with acesulfame potassium, from just '
     f'{names_and(ACE_BRANDS)}, stack it on top of sucralose, never on its own, and no bar we track uses aspartame or saccharin.'),
    ('It is usually a named ingredient, not a trace.',
     f'Only {len(TUCKED)} of the {len(SUC)} sucralose bars tuck it into a "contains 2% or less" clause near the end of the '
     f'label. The other {len(NAMED)}, including {full(EXAMPLES[0])} and {full(EXAMPLES[1])}, list it without that qualifier.'),
    ('Artificial sweeteners cluster in lower-graded bars.',
     f"{GR['A']}% of A-grade bars contain one, against {GR['F']}% of F-grade bars. Skipping artificial sweeteners tends to "
     'land you on a cleaner label overall.'),
]
FINDINGS = findings_v2_html(f'What we found screening {DB_PUBLIC} bars', INSIGHTS,
                            grade_share_chart_html(GRADE_ROWS, title='Share of bars with an artificial sweetener, by ingredient grade',
                                                   note=f'Out of the {DB_PUBLIC} bars in our database.'))

# ---------------------------------------------------------------------------
# Brands that do it well (spec v2 section 6)
# ---------------------------------------------------------------------------
WELL = brands_well_rows(ALL, QF, n=8)
C.check(sum(r['big'] for r in WELL) >= 2 and sum(not r['big'] for r in WELL) >= 2, 'brands-well has 2+ big and 2+ small brands')
def well_why(r):
    lead = f"All {r['total']} flavors qualify" if r['q'] == r['total'] else f"{r['q']} of {r['total']} flavors qualify"
    g = r['grades']
    grades = f"all {next(iter(g))} grade" if len(g) == 1 else grade_mix_text(g) + ' grade'
    sw = brand_sweetener(r['qual'])
    bp = best_pick(r['qual'])
    return (f"{lead}, {grades}." + (f" Mostly sweetened with {sw}." if sw else '')
            + f" Best pick: {bp['Flavor Name']} ({bp['score_band']}, {fnum(P(bp))}g protein, {fnum(CAL(bp))} cal).")
BRANDS_WELL = brands_well_html(WELL, well_why, h2='Brands that do it well',
                               intro='Brands with at least 3 bars in our database, ranked by how much of their lineup qualifies '
                                     'and how well those bars grade. We made sure to include both brands you can find at most '
                                     'grocery stores and smaller independents.')

# ---------------------------------------------------------------------------
# How do the big brands fare? (spec v2 section 7)
# ---------------------------------------------------------------------------
def big_verdict(r):
    disq = [b for b in r['bars'] if not QF(b)]
    bp = best_pick(r['qual'])
    pick = f" Best pick: {bp['Flavor Name']} ({bp['score_band']}, {fnum(P(bp))}g protein)." if bp else ''
    if r['q'] == r['total']:
        ag = avg_grade(r['qual'])
        sw = brand_sweetener(r['qual'])
        return ('Every flavor is free of artificial sweeteners' + (f', mostly sweetened with {sw}.' if sw else '.')
                + (f' Most grade {ag} on ingredients, so check the label.' if ag in ('C', 'D', 'F') else '') + pick)
    ace = sum(1 for b in disq if has_sw(b, 'Acesulfame Potassium'))
    extra = (' plus acesulfame potassium' if ace == len(disq) else f', {ace} with acesulfame potassium too' if ace else '')
    if r['q'] == 0:
        return f"None qualify: every flavor has sucralose{extra}."
    return f"{'Only ' if r['q'] * 2 < r['total'] else ''}{r['q']} of {r['total']} qualify. The rest use sucralose{extra}." + pick
BIG_HTML, BIG_ROWS = big_brands_html(
    ALL, QF, big_verdict, h2='How do the big brands fare on artificial sweeteners?',
    intro=('Every brand with national grocery, big-box or Costco distribution, with how many of its bars skip artificial '
           'sweeteners entirely. Brand names link to our full reviews where we have one.'))
QUEST, BAREBELLS = by_brand('Quest'), by_brand('Barebells')
C.check(any(r['q'] == 0 for r in BIG_ROWS if r['brand'] == 'Quest'), 'Quest has no qualifying bar')
C.check(all(has_sw(b, 'Sucralose') for b in QUEST + BAREBELLS), 'every Quest and Barebells flavor contains sucralose')

# ---------------------------------------------------------------------------
# Top 50 + Bar Finder CTA + criteria
# ---------------------------------------------------------------------------
T50 = top50_rows(Q, 50)
TOP50 = top50_html(T50, h2='Top 50 protein bars without artificial sweeteners',
                   intro='Ranked by ingredient grade first, then by protein per calorie. Tap any row for nutrition facts and '
                         'the full ingredient list.')
FINDER = finder_cta_html(N, SUC_HREF, desc=('The Bar Finder opens with sucralose excluded, which gives the same list as this '
                                            'guide, since every artificial-sweetener bar we track contains sucralose. Add your '
                                            'own filters for protein, sugar, calories, grade, brand, certifications, or '
                                            'ingredients to exclude.'))
CRITERIA = criteria_html(
    qualify_rule=('No sucralose, acesulfame potassium, aspartame, or saccharin anywhere in the ingredient list. Plant-derived '
                  'sweeteners like stevia and monk fruit, allulose, and sugar alcohols do not count against a bar here. '
                  f'{comma(N)} of the {DB_PUBLIC} bars we track qualify.'),
    picks=PICKS)

# ---------------------------------------------------------------------------
# FAQ (answers may hold links; JSON-LD gets the plain text)
# ---------------------------------------------------------------------------
STEVIA = [b for b in Q if stevia_mf(b)]
C.check(len(STEVIA) >= 50, 'stevia / monk fruit show up widely in qualifying bars')
bybrand_suc = defaultdict(list)
for b in SUC:
    bybrand_suc[b['Brand Name']].append(b)
TOP_SUC = sorted(bybrand_suc, key=lambda k: (-len(bybrand_suc[k]), -len(bybrand_suc[k]) / len(by_brand(k)), k.lower()))[:5]
C.check(all(len(bybrand_suc[k]) / len(by_brand(k)) >= 0.75 for k in TOP_SUC), 'top 5 sucralose brands use it in 75%+ of their lineup')

CONSIDER, MIXED, AVOID = brand_split(ALL, QF)
SPLIT = [r for r in CONSIDER + MIXED + AVOID if r['total'] >= 10 and r['q'] and r['d']]
MOSTLY_CLEAN = max(SPLIT, key=lambda r: (r['q'] / r['total'], r['total'], r['brand']))
MOSTLY_DISQ = min(SPLIT, key=lambda r: (r['q'] / r['total'], -r['total'], r['brand']))
C.check(MOSTLY_CLEAN['q'] > MOSTLY_CLEAN['d'] and MOSTLY_DISQ['d'] > MOSTLY_DISQ['q'], 'split examples go opposite ways')
WHOLE = ['KIND', 'Larabar', "Bobo's", 'Aloha', 'GoMacro']
C.check(all(by_brand(w) and len(by_brand(w, Q)) / len(by_brand(w)) >= 0.9 for w in WHOLE), "KIND, Larabar, Bobo's, Aloha, GoMacro all qualify at 90%+")

FAQS = [
    ('What counts as an artificial sweetener in this guide?',
     'We screen for Sucralose, Acesulfame Potassium, Aspartame, and Saccharin. These are the non-nutritive artificial '
     'sweeteners that actually show up in protein bar ingredient lists. Any bar listing one of these gets flagged, '
     'regardless of how small the amount looks on the label.'),
    ('Are stevia and monk fruit artificial sweeteners?',
     "No. Stevia leaf extract, Reb A, and monk fruit (luo han guo) extract are plant-derived sweeteners, not synthetic ones, "
     f"so they don't count against a bar on this page. {len(STEVIA)} of the qualifying bars use one of them. If you want to "
     "avoid all non-sugar sweeteners, including plant-derived ones, check the ingredient list yourself."),
    ('Is sucralose the most common artificial sweetener in protein bars?',
     f"Yes, by a wide margin. Sucralose shows up in {len(SUC)} bars, about {round(100 * len(SUC) / NT)}% of our database. "
     f"Acesulfame potassium is a distant second at {len(ACE)} bars, and we found zero bars in the current database containing "
     "aspartame or saccharin."),
    ('Does Quest use artificial sweeteners?',
     f"Yes, across the entire lineup. All {len(QUEST)} tracked Quest flavors contain sucralose, part of how the brand hits "
     "its low-sugar, high-fiber numbers."),
    ('Does Barebells use artificial sweeteners?',
     f"Yes. All {len(BAREBELLS)} Barebells flavors contain sucralose, the same sweetener driving most of the "
     "artificial-sweetener bars on this list."),
    ("What protein bars don't have artificial sweeteners?",
     f"{comma(N)} bars across {BRANDS_Q} brands clear our artificial sweetener screen, led by whole-food brands like KIND, "
     "Larabar, and Bobo's that qualify at or near 100%. Our Best 10 picks are at the top of this page, the Top 50 is further "
     "down, and the Bar Finder has all of them."),
    ('Is acesulfame potassium common in protein bars?',
     f"Not especially. It shows up in {len(ACE)} bars, about {g1(100 * len(ACE) / NT)}% of our database, concentrated in "
     f"just {num_word(len(ACE_BRANDS))} brands, {names_and(ACE_BRANDS)}, and always stacked alongside sucralose rather than used alone."),
    ('Can a brand have some flavors with artificial sweeteners and some without?',
     f"Yes, and it's common. {MOSTLY_CLEAN['brand']} splits mostly clean: {MOSTLY_CLEAN['q']} of {MOSTLY_CLEAN['total']} "
     f"flavors qualify. {MOSTLY_DISQ['brand']} splits the other way, with {MOSTLY_DISQ['d']} of its {MOSTLY_DISQ['total']} "
     "flavors landing on the disqualified side."),
    ('Why do protein bars use artificial sweeteners in the first place?',
     'Sucralose and acesulfame potassium add intense sweetness with zero sugar and negligible calories, which is why they '
     'show up so often in bars marketed as "low sugar," "keto friendly," or high-protein with a low calorie count. The '
     'tradeoff for some people is an artificial aftertaste or a personal preference to avoid non-nutritive sweeteners altogether.'),
    ('Are artificial sweeteners the same thing as sugar alcohols like erythritol?',
     'No, they are two different categories. Artificial sweeteners are synthetic, calorie-free sweeteners like sucralose '
     'and acesulfame potassium, the four screened on this page. Sugar alcohols, like erythritol, maltitol, and xylitol, are '
     'a separate category with their own digestive tradeoffs and a different scoring screen. If erythritol or maltitol is '
     f"what you actually want to avoid, see our {link('/no-sugar-alcohols', 'protein bars without sugar alcohols guide')}. "
     f"{comma(len(NEITHER))} bars in our database have neither."),
    ('Do protein bars have sucralose?',
     f"Yes. {of_db(len(SUC), NT, True)} bars we track, about 1 in {ONE_IN}, list sucralose on the ingredient label. It's "
     "the most common artificial sweetener in the category by a wide margin, see the breakdown above."),
    ("What protein bars don't have sucralose?",
     f"{comma(N)} bars across {BRANDS_Q} brands are sucralose-free. That's the exact same set as our full "
     "no-artificial-sweeteners list, since every bar in our database containing acesulfame potassium also contains "
     "sucralose, and none contain aspartame or saccharin. The Best 10 and Top 50 on this page are all sucralose-free."),
    ('Which brands use sucralose the most?',
     names_and([f"{k} ({len(bybrand_suc[k])} of {len(by_brand(k))} flavors)" for k in TOP_SUC])
     + " lead the list, all using it to hit a low-sugar or high-fiber number across most or all of their lineup."),
]
C.check(len(SUC) > 5 * max(len(ACE), 1), 'sucralose leads ace-K by a wide margin')

# ---------------------------------------------------------------------------
# Regions
# ---------------------------------------------------------------------------
H1 = 'The 10 Best Protein Bars Without Artificial Sweeteners'
TITLE = f'10 Best Protein Bars Without Artificial Sweeteners ({DB_PUBLIC} Checked)'
DESC = (f'{PCT_D}% of protein bars contain sucralose or another artificial sweetener. Our 10 best without any, '
        f'from {comma(N)} that qualify.')
OG_DESC = (f'We screened {DB_PUBLIC} protein bars for sucralose, ace-K, aspartame and saccharin. {comma(N)} have none. '
           f'Here are the 10 best, each picked by a published rule.')
C.check(len(DESC) <= 155, f'meta description under 155 characters ({len(DESC)})')
FAQS_PLAIN = [(q, plain_text(a)) for q, a in FAQS]
REGIONS = v2_head_regions(title=TITLE, h1=H1, desc=DESC, og_desc=OG_DESC, url=URL, about='Artificial Sweeteners',
                          published=PUBLISHED, faqs=FAQS_PLAIN, picks=PICKS)
EDITORIAL = (f'  <section class="section off" id="what-it-means">{MEANS}  </section>\n'
             f'  <section class="section" id="no-sucralose">{SUCRALOSE}  </section>')
HERO = (f'<h1 class="hero-title">{esc(H1)}</h1>\n'
        f'    <p class="hero-sub">Artificial sweeteners like sucralose (Splenda) and acesulfame potassium are how many "zero sugar" '
        f'protein bars stay sweet without sugar on the label. Some people avoid them for the aftertaste, for digestion, or just to '
        f'skip synthetic ingredients. We screen every bar for sucralose, acesulfame potassium, aspartame and saccharin.</p>\n'
        f'    <p class="hero-sub">Of the {DB_PUBLIC} bars we track, {comma(N)} have none of them anywhere in the ingredient list. '
        f'The other {PCT_D}% do, and every one of those contains sucralose. Plant-derived sweeteners like stevia and monk fruit '
        f'are not artificial, so they don\'t count against a bar here.</p>')
REGIONS += [
    ('hero', HERO),
    ('best10', best10_html(PICKS, h2='Best 10 protein bars without artificial sweeteners', intro=B10_INTRO)),
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
        ('/clean-protein-bars', 'Clean Protein Bars', 'A or B grade bars with no artificial sweeteners and no processed oils.'),
        ('/no-seed-oils', 'No Seed Oils', 'Every bar screened for canola, palm, soybean, and other refined oils.'),
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
