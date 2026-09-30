#!/usr/bin/env python3
"""Rebuild no-seed-oils.html from bars.js. GUIDE PAGE v2 ("Best 10").

Run from the repo root:  python3 build_no_seed_oils.py

Layout and every rule: claude/GUIDE_PAGE_SPEC_V2.md (locked 2026-09-29) and
the v2 section of kyb_guide_lib.py, built the same way as the pilot
(build_no_sugar_alcohols.py). The first run migrated the live v1 page to the v2
body (head, nav and footer kept as deployed); later runs rewrite only the
<!-- kyb:NAME --> regions. Every number, pick and brand row comes from bars.js.
Copy that depends on a fact is checked; if one stops being true the build
stops and lists it. Ingredient quality is shown and ranked as a GRADE only.

Screen: GUIDE_FILTERS['no-seed-oils'] (no 'Processed Oils' concern tag).
Bar Finder: /bar-finder?preset=no_seed_oil (app.js hasSeedOil(); the same set
key for key, checked below). Oil cards are counted by ingredient text over the
bars the screen flags. High-oleic sunflower/safflower are permitted. Any
qualifying bar whose label still names a screened oil is printed as a WARNING:
a tagging gap in bars.js to fix upstream, never patched here.

Guide slots (locked with Jeff 2026-09-29): No added oil at all, Lowest sugar
(among bars with no sugar alcohol), Best date-sweetened, Best snack size.
Fallbacks: Best plant-based (15g+), then Highest fiber.
"""
import re
from collections import Counter
from kyb_guide_lib import *

PAGE = 'no-seed-oils.html'
URL = 'https://knowyourbar.com/no-seed-oils'
PUBLISHED = '2026-04-08'

ALL = load_bars()
QF = GUIDE_FILTERS['no-seed-oils']
Q = [b for b in ALL if QF(b)]
D = [b for b in ALL if not QF(b)]
N, ND, NT = len(Q), len(D), len(ALL)
BRANDS_Q = len({b['Brand Name'] for b in Q})
PCT_D, PCT_Q = pct0(ND, NT), pct0(N, NT)
C = Claims()

OILS = {  # card label -> regex (run on the label with high-oleic oils masked)
    'Palm kernel oil': r'palm kernel',
    'Palm oil': r'palm (?:oil|fat)|\bpalm\b(?! kernel| fruit| sugar)',
    'Sunflower oil': r'sunflower (?:seed )?oil',
    'Vegetable oil': r'vegetable (?:oil|fat)',
    'Soybean oil': r'soybean oil|soy oil',
    'Canola oil': r'canola oil|oils? \([^)]*canola',
    'Palm fruit oil': r'palm fruit',
    'Safflower oil': r'safflower',
    'Rapeseed oil': r'rapeseed',
    'Cottonseed oil': r'cottonseed',
    'Rice bran oil': r'rice bran oil',
    'Corn oil': r'corn oil',
    'Grapeseed oil': r'grape ?seed oil',
}
HYDRO = r'hydrogenated'
def masked(b): return re.sub(r'high[- ]oleic (sunflower|safflower)', r'HOSO', ingr(b), flags=re.I)
def has_oil(b, label): return bool(re.search(OILS[label], masked(b), re.I))
def any_oil(b): return any(has_oil(b, l) for l in OILS) or bool(re.search(HYDRO, ingr(b), re.I))
HIT = {l: [b for b in D if has_oil(b, l)] for l in OILS}
ORDER = [l for l in sorted(OILS, key=lambda l: (-len(HIT[l]), l)) if HIT[l]]
TOP, SECOND, THIRD = ORDER[0], ORDER[1], ORDER[2]

for b in Q:
    if any_oil(b):
        print(f'WARNING: {full(b)} names a screened oil on its label but has no Processed Oils tag in bars.js '
              f'({", ".join(l for l in OILS if has_oil(b, l)) or "hydrogenated"}). Fix upstream in scoring; the page follows bars.js.')
C.check(all(any_oil(b) for b in D), 'every flagged bar names a screened oil')

# Bar Finder parity: app.js hasSeedOil() (SEED_OIL_KEYWORDS + 20-char high-oleic lookback)
FINDER_KW = ['palm oil', 'palm kernel oil', 'canola oil', 'soybean oil', 'hydrogenated', 'partially hydrogenated',
             'palm fruit oil', 'sunflower oil', 'safflower oil', 'vegetable oil', 'rapeseed oil', 'cottonseed oil',
             'corn oil', 'grapeseed oil', 'rice bran oil', 'palm fat']
def finder_has_seed_oil(b):
    t = (b.get('Ingredients') or '').lower()
    for kw in FINDER_KW:
        i = t.find(kw)
        if i == -1:
            continue
        if 'high oleic' in t[max(0, i - 20):i + len(kw)]:
            continue
        return True
    return False
C.check({b['Key'] for b in ALL if not finder_has_seed_oil(b)} == {b['Key'] for b in Q},
        'Bar Finder no_seed_oil preset returns exactly the guide set')

def link(href, text): return f'<a href="{href}">{text}</a>'
def by_brand(brand, bars=ALL): return [b for b in bars if b['Brand Name'] == brand]
def oil_counts(bars):
    c = Counter(l for b in bars for l in OILS if has_oil(b, l))
    return sorted(c.items(), key=lambda kv: (-kv[1], ORDER.index(kv[0]) if kv[0] in ORDER else 99))
def lc(label): return label[0].lower() + label[1:]
NI = lambda b: top_level_ingredient_count(ingr(b))

# ---------------------------------------------------------------------------
# Best 10 (spec v2; guide slots locked with Jeff 2026-09-29)
# ---------------------------------------------------------------------------
def no_added_oil(b): return not re.search(r'\boils?\b|\bfat\b|shortening|\bmct\b|margarine', ingr(b), re.I)
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
    slot_subset('No added oil at all', 'No oil, fat, shortening or MCT of any kind on the label, seed or otherwise.', no_added_oil,
                lambda b: 'No added oil of any kind on the label. The fat comes from whole foods like nut or seed butters.'),
    LOW_SUGAR,
    slot_subset('Best date-sweetened', 'Dates on the label, and no added sugar, syrup or sugar substitute.', date_sweetened,
                lambda b: f"Sweetened only with dates, in {NI(b)} ingredients. Its {fnum(SUG(b))}g of sugar all comes from fruit."),
    slot_subset('Best snack size', 'Under 150 calories.', lambda b: CAL(b) < 150,
                lambda b: 'The top pick under 150 calories (best grade, then most protein per calorie), for when you want a snack, not a meal.'),
]
FALLBACKS = [
    slot_subset('Best plant-based', 'Vegan-labeled bars.', plant_based,
                lambda b: 'Vegan, and free of every seed oil we screen for.', floor=15),
    slot_highest_fiber(),
]
PICKS = pick_best10(Q, SLOTS, FALLBACKS)
C.check(len(PICKS) == 10, 'ten Best 10 picks available')
C.check([s.label for s, *_ in PICKS] == [s.label for s in SLOTS], 'all ten planned slots filled without fallbacks')
C.check(not any(re.search(r'score \d|scored? \d', w) for _s, _b, w, _n in PICKS), 'no ingredient score printed in a pick')
C.check(all(not any_oil(b) for _s, b, _w, _n in PICKS), 'no pick names a screened oil')
NO_OIL_PICK = next(b for s, b, _w, _n in PICKS if s.label == 'No added oil at all')
C.check(re.search(r'butter', ingr(NO_OIL_PICK), re.I), 'the no-added-oil pick gets its fat from a nut, seed or cocoa butter')
B10_INTRO = ("Ten bars with no seed oils, each the winner of one thing people shop for. Every pick has an A or B ingredient "
             "grade and at least 10g of protein, and no bar appears twice.")

# ---------------------------------------------------------------------------
# What it means: one card per oil that shows up
# ---------------------------------------------------------------------------
OIL_DESC = {
    'Palm kernel oil': 'Common in chocolate coatings and crisp layers, prized for a solid melt-in-your-mouth snap.',
    'Palm oil': 'Used for shelf-stable texture and moisture retention in the base recipe.',
    'Sunflower oil': 'A cheap binding fat in protein crisps or coatings, unless labeled high-oleic.',
    'Vegetable oil': 'A generic catch-all fat, usually a blend of soy, corn, or canola.',
    'Soybean oil': 'A cheap, high-omega-6 fat common in coatings and fillings.',
    'Canola oil': 'A moisture retainer that hides mid-list in crispy layers or fillings.',
    'Palm fruit oil': 'A less-refined form of palm oil, same shelf-stability role.',
    'Safflower oil': 'Occasional coating or moisture ingredient, unless high-oleic.',
    'Rapeseed oil': "Canola's parent crop, occasionally listed under this name directly.",
    'Cottonseed oil': 'Usually part of a generic vegetable oil blend rather than listed on its own.',
    'Rice bran oil': 'Rare, usually a specialty coating fat.',
    'Corn oil': 'Rare in bars, usually part of a vegetable oil blend.',
    'Grapeseed oil': 'Rare in bars, occasionally used in baked-style formats.',
}
COCO_Q = [b for b in Q if re.search(r'coconut oil|coconut butter', ingr(b), re.I)]
HO_Q = [b for b in Q if re.search(r'high[- ]oleic', ingr(b), re.I)]
C.check(COCO_Q and HO_Q, 'some qualifying bars use coconut oil and some use a high-oleic oil')
MEANS = f'''
    <div class="section-inner">
      <h2 class="section-title">What "no seed oils" actually means</h2>
      <div class="section-body">
        <p>Seed and vegetable oils are some of the most common additives in processed food, and protein bars are no exception. This guide screens every bar for thirteen of them: canola, rapeseed, soybean, palm, palm kernel, palm fruit, sunflower, safflower, cottonseed, corn, grapeseed, and rice bran oil, plus any bar listing generic "vegetable oil" or "hydrogenated"/"partially hydrogenated" fat. High-oleic sunflower and safflower oil are permitted, since their fatty acid profile runs closer to olive oil than to the standard refined version of the same seed.</p>
        <p>{PCT_D}% of the {DB_PUBLIC} bars in our database still have a seed oil on the label. Here is how often each one shows up, and where it usually hides.</p>
      </div>
      <div class="score-grid" style="margin-top:1.5rem;">
{chr(10).join(v2_count_card_html(l, HIT[l], NT, OIL_DESC[l]) for l in ORDER)}
      </div>
      <h3 class="kt-h3">What still counts as no seed oil</h3>
      <div class="section-body">
        <p>Coconut oil comes from coconut flesh, not a seed, so it doesn't count against a bar here. {len(COCO_Q)} of the {comma(N)} bars on this page use coconut oil or coconut butter, and {len(HO_Q)} use a high-oleic oil. Nut and seed butters, like peanut, almond or sunflower butter, are whole foods, not refined oils, so they don't count either.</p>
      </div>
    </div>
'''

# ---------------------------------------------------------------------------
# Do Pure Protein, Perfect Bar, Built Bar, and IQBAR use seed oils? (anchor #brand-seed-oil-check)
# ---------------------------------------------------------------------------
BRAND4 = [('Pure Protein', 'Pure Protein'), ('Perfect Bar', 'Perfect Bar'), ('Built', 'Built Bar'), ('IQ Bar', 'IQBAR')]
C.check(all(by_brand(k) for k, _ in BRAND4), 'Pure Protein, Perfect Bar, Built and IQ Bar are all in bars.js')
def brand4(key, name):
    bs = by_brand(key)
    oily = [b for b in bs if not QF(b)]
    return dict(key=key, name=name, bars=bs, t=len(bs), d=len(oily), q=len(bs) - len(oily), oc=oil_counts(oily))
B4 = [brand4(k, n) for k, n in BRAND4]
def b4_para(r):
    if r['d'] == 0:
        return (f"None of the {r['t']} flavors use canola oil, sunflower oil, or any other seed or vegetable oil. The fat comes "
                "from nuts, seeds, and nut butters used as whole-food ingredients, not an added refined oil.")
    (top, n), rest = r['oc'][0], r['oc'][1:]
    s = f"{n} of {r['t']} flavors list {lc(top)}"
    if rest:
        s += (f", and {num_word(len(rest))} other oil{'s' if len(rest) > 1 else ''} also show{'' if len(rest) > 1 else 's'} up on "
              f"some flavors: " + ', '.join(f'{lc(l)} ({c})' for l, c in rest))
    s += '. No flavor clears this guide.' if r['q'] == 0 else f". {r['q']} of {r['t']} flavors do clear it."
    return s
every = [r['name'] for r in B4 if r['d'] == r['t']]
none = [r['name'] for r in B4 if r['d'] == 0]
some = [r for r in B4 if 0 < r['d'] < r['t']]
intro = []
if every:
    intro.append(f"{names_and(every)} use{'s' if len(every) == 1 else ''} a seed or vegetable oil in every flavor we checked.")
if none:
    intro.append(f"{names_and(none)} use{'s' if len(none) == 1 else ''} none.")
for r in some:
    intro.append(f"{r['name']} uses one in {r['d']} of {r['t']} flavors.")
BRAND4_HTML = f'''
    <div class="section-inner">
      <h2 class="section-title">Do Pure Protein, Perfect Bar, Built Bar, and IQBAR use seed oils?</h2>
      <div class="section-body">
        <p>{esc(' '.join(intro))} Here is exactly which oils each brand lists, pulled straight from the ingredient label of every flavor in our database. Every other big brand is in the <a href="#big-brands">big brands table</a> below.</p>
{chr(10).join(f'        <p><strong>{esc(r["name"])}:</strong> {esc(b4_para(r))}</p>' for r in B4)}
      </div>
    </div>
'''

# ---------------------------------------------------------------------------
# Findings: three data findings + one chart
# ---------------------------------------------------------------------------
TOPB = HIT[TOP]
def tucked(b, rx):
    t = masked(b)
    m = re.search(r'\d\s*%\s*or\s*less|less than\s*\d\s*%', t, re.I)
    h = re.search(rx, t, re.I)
    return bool(m and h) and h.start() > m.start()
TUCK = [b for b in TOPB if tucked(b, OILS[TOP])]
COAT = re.compile(r'coating|chocolate|compound|crisp|drizzle|layer|icing|confection|chips?\b', re.I)
def in_coating(b):
    return any(re.search(OILS[TOP], it, re.I) and COAT.search(it) for it in top_level_items(masked(b)))
coat_share = sum(1 for b in TOPB if in_coating(b)) / len(TOPB)
C.check(len(TUCK) / len(TOPB) < 0.05, f'under 5% of {TOP} bars list it as a trace amount')
BB = by_brand('Barebells'); BB_D = [b for b in BB if not QF(b)]
C.check(len(BB_D) / len(BB) >= 0.8, 'Barebells fails the seed oil screen in 80%+ of flavors')
GRADE_ROWS = [(g, sum(1 for b in D if b['score_band'] == g), sum(1 for b in ALL if b['score_band'] == g)) for g in BAND_ORDER]
GR = {g: round(100 * h / t) for g, h, t in GRADE_ROWS}
C.check(GR['A'] < GR['B'] < GR['C'] < GR['D'] < GR['F'], 'seed oil share rises with every step down in grade')
INSIGHTS = [
    (f'{TOP} is the most common offender, and rarely a trace.',
     f'{len(TOPB)} bars ({g1(100 * len(TOPB) / NT)}% of the database) list it'
     + (', most often in a coating or crisp layer. ' if coat_share >= 0.5 else '. ')
     + f'Only {len(TUCK)} of them tuck it into a "contains 2% or less" clause.'),
    ('Barebells disqualifies entirely.' if len(BB_D) == len(BB) else 'Barebells disqualifies almost entirely.',
     f'{len(BB_D)} of {len(BB)} Barebells flavors contain a seed oil, most often {lc(oil_counts(BB_D)[0][0])}.'),
    ('Seed oils cluster in lower-graded bars.',
     f"{GR['A']}% of A-grade bars contain one, against {GR['F']}% of F-grade bars. Skipping seed oils tends to land you on "
     'a cleaner label overall.'),
]
FINDINGS = findings_v2_html(f'What we found screening {DB_PUBLIC} bars', INSIGHTS,
                            grade_share_chart_html(GRADE_ROWS, title='Share of bars with a seed oil, by ingredient grade',
                                                   note=f'Out of the {DB_PUBLIC} bars in our database.'))

# ---------------------------------------------------------------------------
# Brands that do it well + big brands
# ---------------------------------------------------------------------------
WELL = brands_well_rows(ALL, QF, n=8)
C.check(sum(r['big'] for r in WELL) >= 2 and sum(not r['big'] for r in WELL) >= 2, 'brands-well has 2+ big and 2+ small brands')
def well_why(r):
    lead = f"All {r['total']} flavors qualify" if r['q'] == r['total'] else f"{r['q']} of {r['total']} flavors qualify"
    g = r['grades']
    grades = f"all {next(iter(g))} grade" if len(g) == 1 else grade_mix_text(g) + ' grade'
    bp = best_pick(r['qual'])
    return (f"{lead}, {grades}." + f" Best pick: {bp['Flavor Name']} ({bp['score_band']}, {fnum(P(bp))}g protein, "
                                   f"{fnum(CAL(bp))} cal).")
BRANDS_WELL = brands_well_html(WELL, well_why, h2='Brands that do it well',
                               intro='Brands with at least 3 bars in our database, ranked by how much of their lineup qualifies '
                                     'and how well those bars grade. We made sure to include both brands you can find at most '
                                     'grocery stores and smaller independents.')

def big_verdict(r):
    disq = [b for b in r['bars'] if not QF(b)]
    bp = best_pick(r['qual'])
    pick = f" Best pick: {bp['Flavor Name']} ({bp['score_band']}, {fnum(P(bp))}g protein)." if bp else ''
    if r['q'] == r['total']:
        ag = avg_grade(r['qual'])
        return ('Every flavor is free of seed oils.' + (f' Most grade {ag} on ingredients, so check the label.'
                                                        if ag in ('C', 'D', 'F') else '') + pick)
    oc = oil_counts(disq)
    every = [l for l, c in oc if c == len(disq)]
    main = lc(every[0] if every else oc[0][0]) if oc else 'a hydrogenated fat'
    if r['q'] == 0:
        return f"None qualify: every flavor has {main}." if every else f"None qualify. Most flavors use {main}."
    return f"{'Only ' if r['q'] * 2 < r['total'] else ''}{r['q']} of {r['total']} qualify. The rest mostly use {main}." + pick
BIG_HTML, BIG_ROWS = big_brands_html(
    ALL, QF, big_verdict, h2='How do the big brands fare on seed oils?',
    intro=('Every brand with national grocery, big-box or Costco distribution, with how many of its bars skip seed oils '
           'entirely. Brand names link to our full reviews where we have one.'))

# ---------------------------------------------------------------------------
# Top 50 + Bar Finder CTA + criteria
# ---------------------------------------------------------------------------
T50 = top50_rows(Q, 50)
TOP50 = top50_html(T50, h2='Top 50 protein bars without seed oils',
                   intro='Ranked by ingredient grade first, then by protein per calorie. Tap any row for nutrition facts and '
                         'the full ingredient list.')
FINDER_HREF = '/bar-finder?preset=no_seed_oil'
FINDER = finder_cta_html(N, FINDER_HREF, desc=('The Bar Finder opens with this same screen already applied: no seed or '
                                               'vegetable oil anywhere in the ingredient list. Add your own filters for '
                                               'protein, sugar, calories, grade, brand, certifications, or ingredients to exclude.'))
CRITERIA = criteria_html(
    qualify_rule=('No canola, rapeseed, soybean, palm, palm kernel, palm fruit, sunflower, safflower, cottonseed, corn, grapeseed, '
                  'rice bran or generic vegetable oil, and no hydrogenated fat, anywhere in the ingredient list. High-oleic '
                  'sunflower and safflower oil, coconut oil, and nut or seed butters do not count against a bar. '
                  f'{comma(N)} of the {DB_PUBLIC} bars we track qualify.'),
    picks=PICKS)

# ---------------------------------------------------------------------------
# FAQ
# ---------------------------------------------------------------------------
CONSIDER, MIXED, AVOID = brand_split(ALL, QF)
SPLIT_EX = min(MIXED, key=lambda r: (abs(r['q'] / r['total'] - 0.5), -r['total'], r['brand']))
def clean_pick(r):
    band = next(g for g in BAND_ORDER if any(b.get('score_band') == g for b in r['qual']))
    return min((b for b in r['qual'] if b.get('score_band') == band), key=lambda b: (-P(b), name_key(b)))
RX = by_brand('RXBAR'); RX_Q = by_brand('RXBAR', Q)
RX_HO = [b for b in RX if re.search(r'high[- ]oleic', ingr(b), re.I)]
LARA = by_brand('Larabar'); LARA_Q = by_brand('Larabar', Q)
lara_med = sorted(NI(b) for b in LARA)[len(LARA) // 2]
KIND = next(r for r in CONSIDER + MIXED + AVOID if r['brand'] == 'KIND')
kind_oils = [lc(l) for l, _ in oil_counts(KIND['disq'])[:2]]
C.check(len(RX_Q) == len(RX), 'every RXBAR flavor qualifies')
C.check(LARA_Q and len(LARA_Q) < len(LARA), 'Larabar: most but not all flavors qualify')
C.check(KIND['q'] < KIND['d'], 'KIND: only some flavors qualify')
C.check(not any(has_tag(b, 'Artificial Sweeteners') for b in RX), 'RXBAR has no artificial sweeteners')
FAQ_WHOLE = ['RXBAR', 'Healthy Eating on the Go', 'Thunderbird']
C.check(all(len(by_brand(w, Q)) == len(by_brand(w)) for w in FAQ_WHOLE), 'RXBAR, Healthy Eating on the Go and Thunderbird qualify 100%')
AV3 = [r['brand'] for r in AVOID[:3]]
C.check(all(r['d'] / r['total'] >= 0.8 for r in AVOID[:3]), 'top three avoid brands disqualify 80%+')
b4 = {r['name']: r for r in B4}
def b4_q(name, oils): return f"Does {name} have {oils}?"
FAQS = [
    ('What counts as a seed oil in this guide?',
     'We screen for canola oil, rapeseed oil, soybean oil, palm oil, palm kernel oil, palm fruit oil, sunflower oil, safflower '
     'oil, cottonseed oil, corn oil, grapeseed oil, rice bran oil, and generic vegetable oil. High-oleic sunflower and '
     'safflower oil are permitted because their fatty acid profile is different from the standard refined versions.'),
    ('Do RXBAR bars have seed oils?',
     f"No. All {len(RX)} RXBAR flavors qualify. RXBAR is built on egg whites, dates, and nuts, so most of the fat comes from "
     "whole-food sources"
     + (f". {num_word(len(RX_HO)).capitalize()} flavors add avocado or high-oleic sunflower oil, which this guide permits." if RX_HO
        else " with nothing refined added.")),
    ('Does Larabar have seed oils?',
     f"Most, but not all. {len(LARA_Q)} of {len(LARA)} Larabar flavors qualify. A typical Larabar runs about {lara_med} "
     "ingredients, usually dates plus a nut or two, so there is little room for a seed oil to hide, but a few flavors do use one."),
    ('Do KIND bars have seed oils?',
     f"Some do. {KIND['q']} of {KIND['total']} KIND flavors qualify, including {clean_pick(KIND)['Flavor Name']}. The rest "
     f"mostly use {' or '.join(kind_oils)}, so check the specific flavor rather than assuming the whole line is clean."),
    (b4_q('Pure Protein', 'canola oil or sunflower oil'), b4_para(b4['Pure Protein'])),
    (b4_q('Perfect Bar', 'sunflower oil or canola oil'), b4_para(b4['Perfect Bar'])),
    (b4_q('Built Bar', 'palm kernel oil or sunflower oil'), b4_para(b4['Built Bar'])),
    (b4_q('IQBAR', 'sunflower oil or canola oil'), b4_para(b4['IQBAR'])),
    ('Which protein bars are most likely to contain palm or canola oil?',
     f"{TOP} is the single most frequent culprit across the database, in {len(TOPB)} bars, ahead of {lc(SECOND)} "
     f"({len(HIT[SECOND])}) and {lc(THIRD)} ({len(HIT[THIRD])})."
     + (' It is a go-to fat for chocolate-style coatings and crisp layers, and it often shows up as "palm kernel oil" rather '
        'than plain "palm oil," so it is easy to miss on a quick label scan.' if TOP == 'Palm kernel oil' else '')),
    ('Is coconut oil a seed oil?',
     'No. Coconut oil is not screened out by this guide. It comes from coconut flesh, not a seed, and has a different fatty '
     'acid makeup than the oils on our exclusion list. Bars using coconut oil or coconut butter qualify here.'),
    ('What about high-oleic sunflower or safflower oil?',
     'High-oleic sunflower and safflower oils are permitted. They are bred for a high monounsaturated fat content, closer in '
     'profile to olive oil than to the standard refined version of the same seed. They are not treated as the same '
     'ingredient for this screen.'),
    ('Can a brand have some flavors with seed oils and some without?',
     f"Yes, and it is more common than you would expect. {SPLIT_EX['brand']} splits close to the middle: {SPLIT_EX['q']} of "
     f"{SPLIT_EX['total']} flavors qualify, often because some flavors add a coating or crisp layer with a different fat "
     "source than the rest of the line. Always check the specific flavor, not just the brand."),
    ('How often is this list updated?',
     'We update the database whenever new bars are added or a brand reformulates. Manufacturers do change their ingredient '
     'lists over time, so always confirm against the packaging in front of you.'),
    ("What protein bars don't have seed oils?",
     f"{comma(N)} bars across {BRANDS_Q} brands clear our seed oil screen, led by whole-food brands like "
     f"{names_and(FAQ_WHOLE)} that qualify 100% of the time. Our Best 10 picks are at the top of this page, the Top 50 is "
     "further down, and the Bar Finder has all of them."),
    ('What protein bars have seed oils?',
     f"{of_db(ND, NT, True)} bars we track contain at least one seed or vegetable oil. {names_and(AV3)} disqualify almost "
     f"entirely, usually through {lc(TOP)}, {lc(SECOND)}, or {lc(THIRD)}."),
    ('Why does canola oil count as a seed oil to avoid here?',
     'Canola comes from rapeseed, which is a seed. We group it with the other refined seed and vegetable oils on this list '
     'for the same reason: a highly processed extraction method and a fatty acid profile heavier in omega-6 than whole-food '
     'fat sources like nuts, seeds, or dairy.'),
]

# ---------------------------------------------------------------------------
# Regions
# ---------------------------------------------------------------------------
H1 = 'The 10 Best Protein Bars Without Seed Oils'
TITLE = f'10 Best Protein Bars Without Seed Oils ({DB_PUBLIC} Checked)'
DESC = (f'{PCT_D}% of protein bars contain a seed oil like palm kernel, canola or sunflower. Our 10 best without any, from '
        f'{comma(N)} that qualify.')
OG_DESC = (f'We screened {DB_PUBLIC} protein bars for canola, soybean, palm, sunflower and other seed oils. {comma(N)} have none. '
           'Here are the 10 best, each picked by a published rule.')
C.check(len(DESC) <= 155, f'meta description under 155 characters ({len(DESC)})')
FAQS_PLAIN = [(q, plain_text(a)) for q, a in FAQS]
REGIONS = v2_head_regions(title=TITLE, h1=H1, desc=DESC, og_desc=OG_DESC, url=URL, about='Seed Oils',
                          published=PUBLISHED, faqs=FAQS_PLAIN, picks=PICKS)
EDITORIAL = (f'  <section class="section off" id="what-it-means">{MEANS}  </section>\n'
             f'  <section class="section" id="brand-seed-oil-check">{BRAND4_HTML}  </section>')
HERO = (f'<h1 class="hero-title">{esc(H1)}</h1>\n'
        f'    <p class="hero-sub">Seed oils are refined oils pressed from seeds, like canola, soybean, sunflower and palm kernel. '
        f'Protein bars use them in coatings, crisps and fillings because they are cheap and shelf-stable. Some people avoid them for '
        f'how heavily they are processed or for their omega-6 content. We screen every bar for thirteen of them.</p>\n'
        f'    <p class="hero-sub">Of the {DB_PUBLIC} bars we track, {comma(N)} have none anywhere in the ingredient list. The other '
        f'{PCT_D}% do, most often {lc(TOP)}. High-oleic oils, coconut oil and nut '
        f'butters don\'t count against a bar here.</p>')
REGIONS += [
    ('hero', HERO),
    ('best10', best10_html(PICKS, h2='Best 10 protein bars without seed oils', intro=B10_INTRO)),
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
        ('/clean-protein-bars', 'Clean Protein Bars', 'A or B grade bars with no artificial sweeteners and no processed oils.'),
        ('/no-artificial-sweeteners', 'No Artificial Sweeteners', 'Bars with zero sucralose, aspartame, or acesulfame potassium.'),
        ('/rxbar-review', 'RXBAR Review', f'All {len(RX)} RXBAR flavors checked. No seed oils, no artificial sweeteners, short ingredient lists.'),
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
