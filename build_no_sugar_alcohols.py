#!/usr/bin/env python3
"""Rebuild no-sugar-alcohols.html from bars.js. GUIDE PAGE v2 ("Best 10") PILOT.

Run from the repo root:  python3 build_no_sugar_alcohols.py

Layout and every rule: claude/GUIDE_PAGE_SPEC_V2.md (locked 2026-09-29) and
the v2 section of kyb_guide_lib.py. The first run migrates the live v1 page
to the v2 body (head, nav and footer kept as deployed); later runs rewrite only
the <!-- kyb:NAME --> regions. Every number, pick and brand row comes from
bars.js. Copy that depends on a fact is checked; if one stops being true the
build stops and lists it. Ingredient quality is shown and ranked as a GRADE
only, never as a score.

Screen: GUIDE_FILTERS['no-sugar-alcohols'] = kyb_guide_lib.has_sugar_alcohol():
the scorer's 'Sugar Alcohols' tag OR IMO named in the ingredients (IMO is a
fiber, not a sugar alcohol, so the scorer doesn't tag it, but this guide
screens it). The six sweeteners in the copy are counted by ingredient text over
the bars the screen flags. Any qualifying bar whose label still names one of
the six is printed as a WARNING: a tagging gap to fix upstream, never patched
here.
"""
import html as _html
import re
from collections import defaultdict
from kyb_guide_lib import *

PAGE = 'no-sugar-alcohols.html'
URL = 'https://knowyourbar.com/no-sugar-alcohols'
PUBLISHED = '2026-04-08'
set_tie_seed('no-sugar-alcohols')   # per-guide shuffle for exact ties (kyb_guide_lib, 2026-09-30)

ALL = load_bars()
QF = GUIDE_FILTERS['no-sugar-alcohols']
Q = [b for b in ALL if QF(b)]
D = [b for b in ALL if not QF(b)]
N, ND, NT = len(Q), len(D), len(ALL)
BRANDS_Q = len({b['Brand Name'] for b in Q})
A_Q = sum(1 for b in Q if b.get('score_band') == 'A')
C = Claims()

SA_RX = {  # label -> regex over the ingredient string
    'Maltitol': r'maltitol',
    'Erythritol': r'erythritol',
    'Isomalto-oligosaccharides (IMO)': r'isomalto|\bimo\b(?!\s+free)',
    'Sorbitol': r'sorbitol',
    'Xylitol': r'xylitol',
    'Isomalt': r'isomalt(?!o)',
}
SHORT = {'Isomalto-oligosaccharides (IMO)': 'IMO'}
def has_sa(b, label): return bool(re.search(SA_RX[label], ingr(b), re.I))
def any_sa(b): return any(has_sa(b, l) for l in SA_RX)
HIT = {l: [b for b in D if has_sa(b, l)] for l in SA_RX}
ORDER = sorted(SA_RX, key=lambda l: -len(HIT[l]))
MAL = HIT['Maltitol']
PCT_D = pct0(ND, NT)

GAPS = [b for b in Q if any_sa(b)]
for b in GAPS:
    print(f'WARNING: {full(b)} names a sugar alcohol on its label but has no Sugar Alcohols tag in bars.js '
          f'({", ".join(l for l in SA_RX if has_sa(b, l))}). Fix upstream in scoring; the page follows bars.js.')
C.check(all(any_sa(b) for b in D), 'every flagged bar names one of the six sweeteners')
C.check(ORDER[0] == 'Maltitol', 'maltitol is the most common sugar alcohol')
SECOND, THIRD = ORDER[1], ORDER[2]

def link(href, text): return f'<a href="{href}">{text}</a>'
def by_brand(brand, bars=ALL): return [b for b in bars if b['Brand Name'] == brand]
def sa_names(bars, lower=True):
    found = [l for l in ORDER if any(has_sa(b, l) for b in bars)]
    return names_and([SHORT.get(l, l.lower() if lower else l) for l in found])

# ---------------------------------------------------------------------------
# Best 10 (spec v2, picks locked with Jeff 2026-09-29)
# ---------------------------------------------------------------------------
SUBSTITUTE = re.compile(r'allulose|monk ?fruit|luo han|stevia|reb ?a\b|rebaudioside|sucralose|acesulfame|aspartame|'
                        r'saccharin|erythritol|xylitol|sorbitol|maltitol|isomalt|tagatose', re.I)
ADDED_SUGAR = re.compile(r'cane sugar|\bsugar\b|honey|syrup|agave|coconut sugar|molasses|nectar|dextrose|fructose|'
                         r'sucrose|juice concentrate|tapioca', re.I)
def date_sweetened(b):
    """Dates on the label and nothing else sweetening it: no added sugar or
    syrup, no sugar substitute (allulose, stevia, monk fruit, ...)."""
    t = ingr(b)
    return bool(re.search(r'\bdates?\b|date paste', t, re.I)) and not SUBSTITUTE.search(t) and not ADDED_SUGAR.search(t)
def allulose(b): return 'allulose' in ingr(b).lower()
def plant_based(b): return b.get('Vegan (Y/N)') == 'Yes'

SLOTS = [
    slot_best_overall(15),
    slot_cleanest(),
    slot_highest_protein(300),
    slot_protein_per_cal(12),
    slot_lowest_calorie(),
    slot_big_brand(),
    # guide-specific (locked 2026-09-29): lowest sugar, allulose, date-sweetened, plant-based
    slot_lowest_sugar(),
    slot_subset('Best allulose-sweetened', 'Allulose on the label.', allulose,
                lambda b: "Sweetened with allulose, a rare sugar that isn't a sugar alcohol and doesn't count toward the Sugars line."),
    slot_subset('Best date-sweetened', 'Dates on the label, and no added sugar, syrup or sugar substitute.', date_sweetened,
                lambda b: f"Sweetened only with dates, in {top_level_ingredient_count(ingr(b))} ingredients. Its "
                          f"{fnum(SUG(b))}g of sugar all comes from fruit."),
    slot_subset('Best plant-based', 'Vegan-labeled bars.', plant_based,
                lambda b: 'Vegan, and free of every sugar alcohol we screen for.', floor=15),
]
FALLBACKS = [
    Slot('Highest fiber', 'The most fiber, grade B or better, 10g+ protein.', lambda E: E,
         lambda b: (-FIB(b),) + tie_chain(b),
         lambda b, c: f"{fnum(FIB(b))}g fiber, {c['tied']}the most of any bar here, with {fnum(P(b))}g protein.", metric=FIB),
    slot_subset('Best snack size', 'Under 150 calories.', lambda b: CAL(b) < 150,
                lambda b: f'Under 150 calories ({fnum(CAL(b))}).'),
]
PICKS = pick_best10(Q, SLOTS, FALLBACKS)
C.check(len(PICKS) == 10, 'ten Best 10 picks available')
C.check([s.label for s, *_ in PICKS] == [s.label for s in SLOTS], 'all ten planned slots filled without fallbacks')
BEST = PICKS[0][1]
G = BEST['score_band']
C.check(not any(re.search(r'score \d|scored? \d', w) for _s, _b, w, _n in PICKS), 'no ingredient score printed in a pick')
B10_INTRO = ("Ten bars with no sugar alcohols, each the winner of one thing people shop for. Every pick has an A or B "
             "ingredient grade and at least 10g of protein, and no bar appears twice.")

# ---------------------------------------------------------------------------
# What it means: one card per sugar alcohol (flagged bars only)
# ---------------------------------------------------------------------------
def card(label, bars_hit, total, desc, found=True):
    n = len(bars_hit)
    return f'''<div class="score-card">
          <div class="score-card-label">{esc(label)}</div>
          <div class="score-card-val">{n} bar{"" if n == 1 else "s"}<span class="oil-card-pct">{esc(pct0(n, total))}%</span></div>
          <div class="score-card-desc">{esc(desc)}</div>''' + (f'''
          {more_list_html(sorted({b['Brand Name'] for b in bars_hit}, key=str.lower))}''' if found else '') + '''
        </div>'''
SA_DESC = {
    'Maltitol': 'The most common sugar alcohol on the list, used for bulk and sweetness in low-sugar bars. Well known for causing GI distress at typical serving sizes.',
    'Erythritol': 'A fermented sugar alcohol with a smaller GI-distress footprint than maltitol, usually paired with stevia or monk fruit in "clean" low-sugar formulas.',
    'Isomalto-oligosaccharides (IMO)': 'A prebiotic fiber syrup that also sweetens, common in bars marketing a low net-carb count. Scored here alongside true sugar alcohols since it behaves the same way on a label.',
    'Sorbitol': 'A sugar alcohol with a strong laxative effect at moderate doses, most common in hard candy-style coatings and confectionery-style layers.',
    'Xylitol': 'A sugar alcohol close to sucrose in sweetness, common in chocolate coatings; tolerated well by most people but a known GI trigger at higher doses.',
    'Isomalt': 'A low-glycemic bulk sweetener often used in chocolate-style coatings, similar mouthfeel to sugar with about half the calories.',
}
if ORDER[0] != 'Maltitol':
    SA_DESC['Maltitol'] = SA_DESC['Maltitol'].replace('The most common sugar alcohol on the list, used', 'Used')
MEANS = f'''
    <div class="section-inner">
      <h2 class="section-title">What "no sugar alcohols" actually means</h2>
      <div class="section-body">
        <p>Sugar alcohols are the sweeteners bar makers reach for when they want a low sugar number on the label without giving up sweetness. This guide screens every bar for six of them: maltitol, erythritol, sorbitol, xylitol, isomalt, and isomalto-oligosaccharides (IMO), a prebiotic fiber syrup that behaves the same way on a label even though it isn't technically a sugar alcohol.</p>
        <p>{PCT_D}% of the {DB_PUBLIC} bars in our database still have a sugar alcohol on the label. Here is how often each one shows up, and where it usually hides.</p>
      </div>
      <div class="score-grid" style="margin-top:1.5rem;">
{chr(10).join(card(l, HIT[l], NT, SA_DESC[l]) for l in ORDER)}
      </div>
    </div>
'''

# ---------------------------------------------------------------------------
# If not sugar alcohols, then what?
# ---------------------------------------------------------------------------
NAT_CARDS = [
    ('Dates', r'\bdates?\b', "A whole fruit, counts fully toward the Sugars line, but comes with fiber and micronutrients maltitol doesn't."),
    ('Cane Sugar', r'cane sugar', "Straightforward table sugar. Counts as sugar and added sugar, no different from what's in a candy bar."),
    ('Honey', r'\bhoney\b', 'Counts fully as sugar on the label, same as cane sugar, just from a different source.'),
    ('Brown Rice Syrup', r'brown rice syrup', 'A glucose-heavy syrup used for texture and sweetness. Counts as sugar, higher glycemic impact than most alternatives here.'),
    ('Agave', r'agave', 'Higher in fructose than table sugar. Still counts fully as sugar on the label.'),
    ('Maple Syrup', r'maple syrup', "Counts as sugar, brings trace minerals table sugar doesn't."),
]
ZERO_CARDS = [
    ('Monk Fruit', r'monk ?fruit|luo han', "Zero calories, zero grams of sugar. Sweetness comes from mogrosides, not a sugar molecule, so it doesn't touch the sugar line or the sugar alcohol line."),
    ('Stevia', r'stevia|reb ?a\b|rebaudioside', 'Zero calories, zero sugar. Plant-derived, extracted from the stevia leaf rather than manufactured from a sugar molecule the way maltitol is.'),
    ('Allulose', r'allulose', "A rare sugar that occurs naturally in small amounts in foods like figs. The FDA doesn't require it to be counted as sugar or added sugar, and it's not a sugar alcohol either."),
]
def q_hits(rx): return [b for b in Q if re.search(rx, ingr(b), re.I)]
def cards_sorted(spec): return '\n'.join(card(l, q_hits(rx), N, d, found=False) for l, rx, d in sorted(spec, key=lambda s: -len(q_hits(s[1]))))

GLY = [b for b in Q if re.search(r'glycerin|glycerol', ingr(b), re.I)]
GLY_BRANDS = len({b['Brand Name'] for b in GLY})
qby = defaultdict(list)
for b in Q:
    qby[b['Brand Name']].append(b)
GLY_ALL = sorted((k.strip() for k, v in qby.items() if all(re.search(r'glycerin|glycerol', ingr(b), re.I) for b in v)), key=str.lower)
C.check(len(GLY) > max(len(HIT[l]) for l in SA_RX), 'glycerin appears in more qualifying bars than any single screened sugar alcohol shows up in')
C.check(len(GLY_ALL) > 4, 'more than four brands use glycerin across their whole qualifying lineup')
H3 = 'style="font-family:var(--bs-font-display); font-weight:700; font-size:1.15rem; color:var(--bs-ink); margin:{m};"'
THEN_WHAT = f'''
    <div class="section-inner">
      <h2 class="section-title">If not sugar alcohols, then what?</h2>
      <div class="section-body">
        <p>Cutting sugar alcohols doesn't mean cutting sweetness. The {comma(N)} bars in this guide get their sweetness from two different places, and they show up very differently on the label.</p>
      </div>

      <h3 {H3.format(m='1.5rem 0 .5rem')}>Natural sugars, count fully toward the Sugars line</h3>
      <p class="section-body">These are real sugar. They add grams to the Sugars and Added Sugars lines just like the sugar in a candy bar would, they just come from a whole-food or less processed source instead of a lab.</p>
      <div class="score-grid" style="margin-top:1rem;">
{cards_sorted(NAT_CARDS)}
      </div>

      <h3 {H3.format(m='2rem 0 .5rem')}>Zero-calorie alternatives, won't trigger this screen either</h3>
      <p class="section-body">These sweeteners are not sugar alcohols and don't get counted as sugar. They're the closest thing to a free pass: sweetness with no calories, no grams on the Sugars line, and none of the digestive baggage sugar alcohols carry.</p>
      <div class="score-grid" style="margin-top:1rem;">
{cards_sorted(ZERO_CARDS)}
      </div>

      <div style="margin-top:2rem; background:var(--bs-cream); border:1.5px solid var(--bs-ink); border-radius:var(--bs-radius); padding:1.25rem 1.5rem;">
        <div style="font-family:var(--bs-font-display); font-weight:700; font-size:1.05rem; color:var(--bs-ink);">Glycerin is a sugar alcohol gray area</div>
        <ul style="margin:.6rem 0 0; padding-left:1.1rem; color:var(--bs-text-dim);">
          <li>Glycerin (glycerol) shows up in {len(GLY)} of the {comma(N)} "no sugar alcohol" bars on this page ({pct0(len(GLY), N)}%)</li>
          <li>More than any single sugar alcohol we screen for</li>
          <li>Glycerin is chemically a sugar alcohol, but we don't count it against a bar here</li>
        </ul>
      </div>

      <h3 {H3.format(m='2rem 0 .5rem')}>Here's why we don't include glycerin as a sugar alcohol</h3>
      <div class="section-body">
        <p>Glycerin (also listed as glycerol) is chemically a sugar alcohol and belongs to the same family as maltitol, erythritol, and xylitol. Using a chemistry definition, it belongs on this screen. (At least to the best of our understanding, as definitely NOT chemists.) However, we don't use it as a factor on our No Sugar Alcohols page. We'll do our best to show our work and explain why.</p>
        <p>It's important to note that ingredients can serve more than one function. Maltitol is typically added as a sugar substitute, providing sweetness while keeping labeled sugar low. Glycerin is also a sugar alcohol and mildly sweet, but protein bars often use it as a humectant to keep the bar moist and soft. If you're like us and had no clue what humectant means, it's an ingredient that attracts and holds on to water or moisture. So an ingredient list doesn't necessarily tell us why an ingredient was added or which function matters most in the recipe, but its chemistry doesn't change based on intent.</p>
        <p>We chose to use our best interpretation of FDA guidelines. The FDA's nutrition labeling rules treat glycerin differently from the sugar alcohols typically reported on Nutrition Facts labels. The regulations specifically address sugar alcohols such as sorbitol, mannitol, xylitol, maltitol, and erythritol. Glycerin is regulated separately, and the FDA recognizes it serves several functions. So for that reason, we're treating it differently too.</p>
        <p>So what does that mean for glycerin on this No Sugar Alcohols page? Well, there are {GLY_BRANDS} brands we have listed on this page as not having sugar alcohols that have glycerin present. This includes several brands we think have very strong ingredient label quality. However, we understand if you have a different point of view and prefer to avoid glycerin. We've included a list of brands below that have glycerin used in all of their flavors and formulations.</p>
      </div>

      <div class="score-card" style="margin-top:1rem;">
        <div class="score-card-label">Brands using glycerin across their entire qualifying lineup</div>
        <div style="margin-top:.5rem;">{more_list_html(GLY_ALL)}</div>
      </div>
    </div>
'''
C.check('<li>' in THEN_WHAT, 'then-what section built')

# ---------------------------------------------------------------------------
# Protein bars without erythritol
# ---------------------------------------------------------------------------
ERY = [b for b in ALL if has_sa(b, 'Erythritol')]
EF = [b for b in ALL if not has_sa(b, 'Erythritol')]
EF_BRANDS = len({b['Brand Name'] for b in EF})
EF_D = [b for b in EF if not QF(b)]
GAP = len(EF) - N
gap_counts = sorted(((sum(1 for b in EF_D if has_sa(b, l)), l) for l in SA_RX if l != 'Erythritol'), reverse=True)
C.check(GAP == len(EF_D), 'erythritol-free minus qualifying equals erythritol-free bars the screen flags')
C.check({gap_counts[0][1], gap_counts[1][1]} == {'Maltitol', 'Isomalto-oligosaccharides (IMO)'}, 'the erythritol-free gap is mostly maltitol and IMO')
C.check(not any(has_maltitol_family(b) for b in ALL if GUIDE_FILTERS['keto-protein-bars'](b) or GUIDE_FILTERS['best-bars-for-diabetics'](b)),
        'keto and diabetics exclude the maltitol family')
C.check(any(has_sa(b, 'Erythritol') for b in ALL if GUIDE_FILTERS['keto-protein-bars'](b) or GUIDE_FILTERS['best-bars-for-diabetics'](b)),
        'an erythritol bar can still qualify for keto or diabetics')

OTHERS, _seen = [], set()
for b in sorted(EF_D, key=overall_key):  # best bar (grade, then protein per calorie) from each of 8 brands
    if b['Brand Name'] not in _seen and len(OTHERS) < 8:
        OTHERS.append(b); _seen.add(b['Brand Name'])
OTHERS_A = sum(1 for b in EF_D if b['score_band'] == 'A')
C.check(OTHERS_A >= 3, 'several erythritol-free-but-flagged bars are A grade')
OTHERS_TABLE = compact_bar_table_html(OTHERS, cols=('grade', 'protein', 'cal', 'sugar'),
                                      extra=('Uses instead', lambda b: esc(sa_names([b], lower=False))), hide_mobile=('cal',))
ERY_HREF = '/bar-finder?excl=erythritol'
ERYTHRITOL = f'''
    <div class="section-inner">
      <h2 class="section-title">Protein bars without erythritol</h2>
      <div class="section-body">
        <p>Erythritol is a fermented sugar alcohol made by fermenting glucose with a yeast-like fungus, roughly 70% as sweet as table sugar with close to zero calories. It has a glycemic index of 0, the lowest of any sugar alcohol on this page's screen, and is generally well tolerated at typical serving sizes, though some people still report bloating or a cooling aftertaste at higher doses.</p>
        <p>{of_db(len(ERY), NT, True)} bars we track, about {g1(100 * len(ERY) / NT)}%, contain erythritol. Screen for erythritol on its own, ignoring the other five sugar alcohols this page screens for, and the qualifying list gets bigger: {comma(len(EF))} bars across {EF_BRANDS} brands, {GAP} more than the {comma(N)} bars that clear this guide's full six-way sugar alcohol screen. The gap is bars that skip erythritol specifically but still contain something else on this list, most often maltitol or isomalto-oligosaccharides (IMO).</p>
        <p><strong>Erythritol and maltitol are not the same thing, and our Keto and Diabetics guides don't treat them the same way.</strong> Both guides exclude the maltitol family (maltitol, polyglycitol, hydrogenated starch hydrolysates) for its meaningfully higher glycemic index, around 35 versus sucrose's 65. Neither guide excludes erythritol, since its glycemic index of 0 already behaves the way their net-carbs formula assumes. A bar with erythritol can still qualify for {link('/keto-protein-bars', 'Keto')} or {link('/best-bars-for-diabetics', 'Best Bars for Diabetics')}. A bar with maltitol cannot, even if that same bar happens to be erythritol-free.</p>
        <p>Every bar in our <a href="#best-10">Best 10</a> and <a href="#top-50">Top 50</a> is erythritol-free, since they clear all six.</p>
      </div>
      <h3 class="kt-h3">Only avoiding erythritol? These bars skip it but use a different sugar alcohol</h3>
      <p class="section-body">{len(EF_D)} bars are erythritol-free but still contain maltitol, sorbitol, xylitol, isomalt, or IMO. {OTHERS_A} of them are A grade. Here is the best one from each of {num_word(len(OTHERS))} brands, and what it uses instead. Tap a row for the full label.</p>
      {OTHERS_TABLE}
      <div class="section-cta">
        <a href="{ERY_HREF}" class="finder-cta-btn section-cta-btn">See all {comma(len(EF))} erythritol-free bars in the Bar Finder &rarr;</a>
        <p class="section-cta-note">Opens the Bar Finder with erythritol excluded. Add your own filters for protein, sugar, calories, grade, or brand.</p>
      </div>
      <p class="section-body" style="margin-top:1.25rem;">Avoiding sucralose and other artificial sweeteners too? See our {link('/no-artificial-sweeteners#no-sucralose', 'protein bars without sucralose')}.</p>
    </div>
'''

# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------
def tucked(b, w):
    t = ingr(b).lower()
    m = re.search(r'\d\s*%\s*or\s*less|less than\s*\d\s*%', t)
    return bool(m) and t.find(w) > m.start()
def in_first5(b, w): return any(w in i.lower() for i in top_level_items(ingr(b))[:5])
MAL_T = [b for b in MAL if tucked(b, 'maltitol')]
MAL_5 = [b for b in MAL if in_first5(b, 'maltitol')]
def pick_examples(pool, prefer, k=2):
    keys = {(b['Brand Name'], b['Flavor Name']) for b in pool}
    ex = [f'{br} {fl}' for br, fl in prefer if (br, fl) in keys]
    for b in pool:
        if len(ex) >= k:
            break
        if full(b) not in ex:
            ex.append(full(b))
    return ex[:k]
T_EX = pick_examples(MAL_T, [('think!', 'Oatmeal Chocolate Chunk'), ('FITCRUNCH', 'Loaded Cookie')])
F5_EX = pick_examples(MAL_5, [('Alani', 'Munchies'), ('Barebells', 'Fudge Brownie')])
C.check(len(MAL_T) / len(MAL) < 0.05, 'under 5% of maltitol bars tuck it in a 2%-or-less clause')
C.check(len(MAL_5) / len(MAL) >= 0.5, 'maltitol sits in the first five ingredients in most maltitol bars')

ZERO = [b for b in D if not (num(b.get('Sugar Alcohol (g)')) or 0)]
Z_EX = pick_examples(ZERO, [('Alani', 'Munchies'), ('Alani', 'Rocky Road')])
BB = by_brand('Barebells')
BB_D = [b for b in BB if not QF(b)]
BB_MX = sum(1 for b in BB_D if has_sa(b, 'Maltitol') or has_sa(b, 'Xylitol'))
C.check(BB_MX / max(len(BB_D), 1) >= 0.8, 'Barebells flagged flavors mostly use maltitol or xylitol')
bb_head = 'Barebells disqualifies entirely.' if len(BB_D) == len(BB) else 'Barebells disqualifies almost entirely.'
WHOLE = ['KIND', 'Larabar', "Bobo's", 'Aloha', 'GoMacro']
C.check(all(by_brand(w) and len(by_brand(w, Q)) / len(by_brand(w)) >= 0.9 for w in WHOLE), 'whole-food brands qualify at 90%+')

CONSIDER, MIXED, AVOID = brand_split(ALL, QF)
C.check(len(MIXED) >= 3, 'at least three mixed-lineup brands')
SPLIT_EX = min(MIXED, key=lambda r: (abs(r['q'] / r['total'] - 0.5), -r['total'], r['brand']))
def clean_pick(r):
    band = next(g for g in BAND_ORDER if any(b.get('score_band') == g for b in r['qual']))
    return min((b for b in r['qual'] if b.get('score_band') == band), key=lambda b: (-P(b), name_key(b)))
twice = len(MAL) >= 2 * len(HIT[SECOND])
C.check(len(MAL) > len(HIT[SECOND]), 'maltitol leads the next sugar alcohol')

# Findings: three data findings + one chart (spec v2 section 5)
GRADE_ROWS = [(g, sum(1 for b in D if b['score_band'] == g), sum(1 for b in ALL if b['score_band'] == g)) for g in BAND_ORDER]
GR = {g: round(100 * h / t) for g, h, t in GRADE_ROWS}
C.check(GR['A'] <= GR['B'] <= GR['C'] <= GR['D'] <= GR['F'] and GR['A'] < GR['F'], 'sugar alcohol share never falls with a step down in grade, and F is well above A')
INSIGHTS = [
    (f'{len(ZERO)} of {ND} flagged bars show 0g sugar alcohol on the label anyway.',
     f'They list a sugar alcohol in the ingredients but declare 0g, or leave the line blank, on the Nutrition Facts panel, '
     f'including {names_and(Z_EX)}. We check the ingredient list, not just the number.'),
    ('Maltitol is the biggest driver, and it is rarely a trace ingredient.',
     f"It shows up in {len(MAL)} bars, " + (f"more than twice as many as {SHORT.get(SECOND, SECOND.lower())}, the next most common. "
                                            if twice else f"more than {SHORT.get(SECOND, SECOND.lower())}, the next most common. ")
     + f'In {len(MAL_5)} of them it sits in the first five ingredients. Only {len(MAL_T)} tuck it into a "2% or less" clause.'),
    ('Sugar alcohols cluster in lower-graded bars.',
     f"{GR['A']}% of A-grade bars contain one, against {GR['F']}% of F-grade bars. Skipping sugar alcohols tends to "
     'land you on a cleaner label overall.'),
]
FINDINGS = findings_v2_html(f'What we found screening {DB_PUBLIC} bars', INSIGHTS,
                            grade_share_chart_html(GRADE_ROWS, title='Share of bars with a sugar alcohol, by ingredient grade',
                                                   note=f'Out of the {DB_PUBLIC} bars in our database.'))

# ---------------------------------------------------------------------------
# Brands that do it well (spec v2 section 6)
# ---------------------------------------------------------------------------
SWEETENERS = [('dates', r'\bdates?\b'), ('honey', r'\bhoney\b'), ('maple syrup', r'maple syrup'), ('cane sugar', r'cane sugar'),
              ('coconut sugar', r'coconut sugar'), ('allulose', r'allulose'), ('monk fruit', r'monk ?fruit|luo han'),
              ('stevia', r'stevia|reb ?a\b|rebaudioside'), ('brown rice syrup', r'brown rice syrup'), ('agave', r'agave'),
              ('tapioca syrup', r'tapioca syrup'), ('fruit', r'\b(?:raisins?|figs?|apricots?|cherries|cranberries|apples?|bananas?)\b')]
def lead_sweetener(b):
    t, best = ingr(b), None
    for name, rx in SWEETENERS:
        m = re.search(rx, t, re.I)
        if m and (best is None or m.start() < best[1]):
            best = (name, m.start())
    return best[0] if best else None
def brand_sweetener(bars):
    from collections import Counter
    c = Counter(x for x in (lead_sweetener(b) for b in bars) if x)
    return c.most_common(1)[0][0] if c else None
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
        return ('Every flavor is free of sugar alcohols' + (f', mostly sweetened with {sw}.' if sw else '.')
                + (f' Most grade {ag} on ingredients, so check the label.' if ag in ('C', 'D', 'F') else '') + pick)
    found = [l for l in ORDER if any(has_sa(b, l) for b in disq)]
    every = [l for l in found if all(has_sa(b, l) for b in disq)]
    main = every[0] if every else max(found, key=lambda l: sum(1 for b in disq if has_sa(b, l))) if found else None
    main_s = SHORT.get(main, main.lower()) if main else 'a sugar alcohol'
    if r['q'] == 0:
        return (f"None qualify: every flavor has {main_s}." if every
                else f"None qualify. Most flavors use {main_s}.")
    return f"Only {r['q']} of {r['total']} qualify. The rest mostly use {main_s}." + pick
BIG_HTML, BIG_ROWS = big_brands_html(
    ALL, QF, big_verdict, h2='How do the big brands fare on sugar alcohols?',
    intro=('Every brand with national grocery, big-box or Costco distribution, with how many of its bars skip sugar '
           'alcohols entirely. Brand names link to our full reviews where we have one.'))
C.check(any(r['q'] == 0 for r in BIG_ROWS if r['brand'] == 'Quest'), 'Quest has no qualifying bar')

# ---------------------------------------------------------------------------
# Top 50 + Bar Finder CTA + criteria
# ---------------------------------------------------------------------------
T50 = top50_rows(Q, 50)
TOP50 = top50_html(T50, h2='Top 50 protein bars without sugar alcohols',
                   intro='Ranked by ingredient grade first, then by protein per calorie. Tap any row for nutrition facts and '
                         'the full ingredient list.')
FINDER_HREF = '/bar-finder?preset=no_sugar_alcohol'
FINDER = finder_cta_html(N, FINDER_HREF, desc=('The Bar Finder opens with this same screen already applied: no sugar alcohol '
                                               'anywhere in the ingredient list. Add your own filters for protein, sugar, '
                                               'calories, grade, brand, certifications, or ingredients to exclude.'))
CRITERIA = criteria_html(
    qualify_rule=(f'No maltitol, erythritol, sorbitol, xylitol, isomalt, or isomalto-oligosaccharides (IMO) anywhere in the '
                  f'ingredient list. We read the ingredient list itself, not just the Sugar Alcohol line on the label, because '
                  f'{len(ZERO)} bars name one and still show 0g. Glycerin does not count against a bar (see '
                  '<a href="#if-not-sugar-alcohols">why</a>). ' + f'{comma(N)} of the {DB_PUBLIC} bars we track qualify.'),
    picks=PICKS)

# ---------------------------------------------------------------------------
# FAQ
# ---------------------------------------------------------------------------
ery_by = defaultdict(int)
for b in ERY:
    ery_by[b['Brand Name']] += 1
ERY_TOP = sorted(ery_by, key=lambda k: (-ery_by[k], k.lower()))[:3]
C.check(bool(MAL_T), 'at least one maltitol bar tucks it in a 2%-or-less clause')
FAQS = [
    ('What counts as a sugar alcohol in this guide?',
     f"We screen for {names_and(ORDER)}. These are the sugar alcohols and sugar-alcohol-adjacent sweeteners that actually "
     "show up in protein bar ingredient lists, not a generic definition. Any bar listing one of these gets flagged, "
     "regardless of how small the amount looks on the label."),
    ('Do sugar alcohols cause digestive issues?',
     "Maltitol, sorbitol, and xylitol are well known for causing gas, bloating, or a laxative effect in some people, "
     "especially at the multi-gram doses common in low-sugar protein bars. Erythritol is usually better tolerated at typical "
     "serving sizes, but individual sensitivity varies a lot. This guide screens for presence on the label, not tolerance, "
     "since that's the part we can measure."),
    ('Is Maltitol the most common sugar alcohol in protein bars?',
     f"Yes. Maltitol shows up in {of_db(len(MAL), NT, True)} bars we track ({pct0(len(MAL), NT)}%), more than any other "
     f"sugar alcohol on our screen. {SECOND} and {THIRD} are next, well behind."),
    ('Is isomalto-oligosaccharide (IMO) a sugar alcohol?',
     "Not technically. IMO is a prebiotic fiber syrup, not a true sugar alcohol, but it behaves the same way on a label and "
     "shows up in a lot of the same low-net-carb bars, so we screen for it alongside maltitol, erythritol, sorbitol, xylitol, "
     "and isomalt rather than giving it a pass."),
    ('Does Barebells use sugar alcohols?',
     ('Yes, across the entire lineup. ' if len(BB_D) == len(BB) else 'Almost entirely. ')
     + f"{len(BB_D)} of {len(BB)} Barebells flavors contain a sugar alcohol, most often maltitol or xylitol, part of how the "
     "brand hits its low-sugar numbers."),
    ('Does sugar alcohol count toward net carbs?',
     "Not on this site. Our net-carb formula is total carbohydrates minus fiber minus sugar alcohol, a full subtraction, so a "
     "bar loaded with maltitol or erythritol can post a low net-carb number on the label while still containing a real amount "
     "of the ingredient itself. A low net-carb count doesn't mean a bar is sugar-alcohol-free."),
    ('What sugar alcohols hide in a "contains 2% or less" ingredient list?',
     f"Almost none of them, at least for maltitol. Only {len(MAL_T)} of the {len(MAL)} bars containing maltitol list it inside "
     f'a "contains 2% or less" clause. In {len(MAL_5)} of them, including {names_and(F5_EX)}, it shows up in the first five '
     "ingredients, meaning it's a real component of the recipe, not a rounding error."),
    ('Can a brand have some flavors with sugar alcohols and some without?',
     f"Yes, and it's common. {SPLIT_EX['brand']} splits close to the middle: {SPLIT_EX['q']} of {SPLIT_EX['total']} flavors "
     f"qualify. {clean_pick(SPLIT_EX)['Flavor Name']} is the clean pick from that lineup."),
    ("What protein bars don't have sugar alcohols?",
     f"{comma(N)} bars across {BRANDS_Q} brands clear our sugar alcohol screen, led by whole-food brands like KIND, Larabar, "
     "and Bobo's that qualify at or near 100%. Our Best 10 picks are at the top of this page, the Top 50 is further down, "
     "and the Bar Finder has all of them."),
    ('What protein bars have sugar alcohols?',
     f"{of_db(ND, NT, True)} bars we track contain at least one sugar alcohol. Barebells "
     + ('disqualifies entirely' if len(BB_D) == len(BB) else 'disqualifies almost entirely')
     + ", usually through maltitol or xylitol used to hit a low-sugar number on the label."),
    ('Why do protein bars use sugar alcohols in the first place?',
     'Sugar alcohols add sweetness and bulk with fewer usable calories and a smaller blood-sugar impact than regular sugar, '
     'which is why they show up so often in bars marketed as "low sugar" or "keto friendly." The tradeoff is digestive '
     'tolerance and, for some people, an artificial aftertaste.'),
    ('Is glycerin a sugar alcohol?',
     "Chemically, yes. But the FDA's own nutrition-labeling rule (21 CFR 101.9) doesn't include glycerin in the sugar alcohol "
     "list used for Nutrition Facts calculations the way it does maltitol, xylitol, sorbitol, erythritol, and isomalt. It's "
     "GRAS-listed separately as a food additive and shows up in bars mostly as a humectant that keeps the bar soft, not as the "
     "primary sweetener. We follow the FDA's own distinction here rather than guess at intent, so it doesn't count against a "
     f"bar on this page. It appears in {len(GLY)} of the {comma(N)} qualifying bars, so check the ingredient list yourself if "
     "you want to avoid it specifically."),
    ('Can a nutrition label say 0g sugar alcohol even if one is in the ingredients?',
     f"Yes, and it's common. {len(ZERO)} of the {ND} bars that fail this screen list a sugar alcohol on the ingredient line but "
     "show 0g, or leave the line blank, on the Nutrition Facts panel. That's part of why this guide is built by scanning the "
     "actual ingredient list for every bar rather than trusting the sugar alcohol gram count on the label."),
    ("What protein bars don't have erythritol?",
     f"{comma(len(EF))} bars across {EF_BRANDS} brands are erythritol-free, screening for erythritol alone rather than all six "
     f"sugar alcohols this guide tracks. That's {GAP} more than the {comma(N)} bars that clear the full screen, since those "
     "extra bars still contain something else on this list, usually maltitol or isomalto-oligosaccharides (IMO)."),
    ('Are there erythritol-free protein bars?',
     f"Yes, plenty. {sum(1 for b in EF if b['score_band'] == 'A')} of the {comma(len(EF))} erythritol-free bars carry an A "
     "ingredient grade, led by whole-food brands that never needed a sugar alcohol to hit a low-sugar number in the first place."),
    ('Which protein bars have erythritol?',
     f"{of_db(len(ERY), NT, True)} bars we track contain erythritol. {ERY_TOP[0]} ({ery_by[ERY_TOP[0]]} flavors), "
     f"{ERY_TOP[1]} ({ery_by[ERY_TOP[1]]}), and {ERY_TOP[2]} ({ery_by[ERY_TOP[2]]}) use it most, usually paired with stevia or "
     "monk fruit to hit a low-sugar, high-fiber number without a maltitol-style GI hit."),
    ('Is erythritol the same as maltitol?',
     "No. Both are sugar alcohols, but they behave differently. Erythritol has a glycemic index of 0 and is excluded from this "
     "guide's full sugar-alcohol screen but not from our Keto or Diabetics guides. Maltitol has a meaningfully higher glycemic "
     "index, around 35, and both Keto and Diabetics exclude it specifically. A bar with erythritol can still qualify for Keto "
     "or Diabetics. A bar with maltitol cannot."),
]

# ---------------------------------------------------------------------------
# Regions
# ---------------------------------------------------------------------------
H1 = 'The 10 Best Protein Bars Without Sugar Alcohols'
TITLE = f'10 Best Protein Bars Without Sugar Alcohols ({DB_PUBLIC} Checked)'
DESC = (f'{PCT_D}% of protein bars have a sugar alcohol, and {len(ZERO)} list one while showing 0g on the label. '
        f'Our 10 best without any, from {comma(N)} that qualify.')
OG_DESC = (f'We screened {DB_PUBLIC} protein bars for maltitol, erythritol, xylitol and more. {comma(N)} have none. '
           f'Here are the 10 best, each picked by a published rule.')
C.check(len(DESC) <= 155, f'meta description under 155 characters ({len(DESC)})')
FAQS_PLAIN = [(q, plain_text(a)) for q, a in FAQS]
REGIONS = v2_head_regions(title=TITLE, h1=H1, desc=DESC, og_desc=OG_DESC, url=URL, about='Sugar Alcohols',
                          published=PUBLISHED, faqs=FAQS_PLAIN, picks=PICKS)
EDITORIAL = (f'  <section class="section off" id="what-it-means">{MEANS}  </section>\n'
             f'  <section class="section off" id="if-not-sugar-alcohols">{THEN_WHAT}  </section>\n'
             f'  <section class="section" id="no-erythritol">{ERYTHRITOL}  </section>')
HERO = (f'<h1 class="hero-title">{esc(H1)}</h1>\n'
        f'    <p class="hero-sub">Sugar alcohols like maltitol, erythritol, sorbitol and xylitol are how most "low sugar" protein '
        f'bars keep the sugar number down. For some people, they also cause bloating and stomach trouble. We screen for five of them, '
        f'plus IMO, a fiber syrup that works the same way on a label.</p>\n'
        f'    <p class="hero-sub">Of the {DB_PUBLIC} bars we track, {comma(N)} have none of them anywhere in the ingredient list. '
        f'The other {PCT_D}% do, and {len(ZERO)} of those still show 0g sugar alcohol on the nutrition label. That is why we check '
        f'the ingredients, not just the label line.</p>')
REGIONS += [
    ('hero', HERO),
    ('best10', best10_html(PICKS, h2='Best 10 protein bars without sugar alcohols', intro=B10_INTRO)),
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
        ('/no-artificial-sweeteners', 'No Artificial Sweeteners', 'Bars that skip sucralose, ace-K, and other artificial sweeteners entirely.'),
        ('/keto-protein-bars', 'Keto Protein Bars', 'Ranked by net carbs, not just marketing claims on the wrapper.'),
        ('/clean-protein-bars', 'Clean Protein Bars', 'A and B grade bars with no artificial sweeteners and no processed oils.'),
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
