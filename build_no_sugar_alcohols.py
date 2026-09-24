#!/usr/bin/env python3
"""Rebuild no-sugar-alcohols.html from bars.js.

Run from the repo root:  python3 build_no_sugar_alcohols.py

Opens the LIVE page and rewrites only the <!-- kyb:NAME --> regions (nav,
footer, fonts, CSS and JS stay as deployed). Every number, pick, brand row and
bar row comes from bars.js. Copy that depends on a fact is checked; if one
stops being true the build stops and lists it.

Screen: GUIDE_FILTERS['no-sugar-alcohols'] (no 'Sugar Alcohols' concern tag).
The six sweeteners in the copy are counted by ingredient text over the bars
the screen flags. Any qualifying bar whose label still names one of the six is
printed as a WARNING: that is a tagging gap in bars.js to fix upstream, never
patched here.
"""
import html as _html
import re
from collections import defaultdict
from kyb_guide_lib import *

PAGE = 'no-sugar-alcohols.html'
URL = 'https://knowyourbar.com/no-sugar-alcohols'
PUBLISHED = '2026-04-08'

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
# Top picks
# ---------------------------------------------------------------------------
PK = Picker(Q)
G = PK.band_grade
CALK = lambda b: num(b.get('Calories')) or 9999

def scope(fn, b, higher=True):
    best = (max if higher else min)
    if fn(b) == best(fn(x) for x in Q):
        return 'of any bar with no sugar alcohols'
    if fn(b) == best(fn(x) for x in PK.band):
        return f'of any {G}-grade bar with no sugar alcohols'
    return f'of any {G}-grade bar with {PK.floor}g+ protein and no sugar alcohols'
def tied(fn, b):
    return sum(1 for x in PK.band if P(x) >= PK.floor and fn(x) == fn(b)) > 1

SUBSTITUTE = re.compile(r'allulose|monk ?fruit|luo han|stevia|reb ?a\b|rebaudioside|sucralose|acesulfame|aspartame|'
                        r'saccharin|erythritol|xylitol|sorbitol|maltitol|isomalt|tagatose|glycerin|glycerol', re.I)
NATURAL = [('honey', r'\bhoney\b'), ('dates', r'\bdates?\b'), ('maple syrup', r'maple syrup'), ('cane sugar', r'cane sugar'),
           ('coconut sugar', r'coconut sugar'), ('brown rice syrup', r'brown rice syrup'), ('agave', r'agave'),
           ('molasses', r'molasses'), ('fruit', r'\b(?:raisins?|figs?|apricots?|cherries|cranberries|apples?|bananas?)\b')]
def naturals(b): return [n for n, rx in NATURAL if re.search(rx, ingr(b), re.I)]
def naturally_sweet(b): return not SUBSTITUTE.search(ingr(b)) and bool(naturals(b))

best = PK.balanced()
top_p = PK.pick(lambda b: (-P(b), CALK(b)))
top_r = PK.pick(lambda b: (-(p100(b) or 0), -P(b)))
top_f = PK.pick(lambda b: (-FIB(b), -P(b)))
natural = PK.pick(lambda b: (-P(b), SUG(b)), naturally_sweet)
low_s = PK.pick(lambda b: (SUG(b), -P(b)))

PICKS = [
    ['Best overall', best,
     f"{fnum(P(best))}g protein, {fnum(FIB(best))}g fiber, and just {fnum(SUG(best))}g sugar with no sugar alcohol, in a "
     f"{top_level_ingredient_count(ingr(best))}-ingredient list. Strong across the board rather than a single-metric standout."],
    ['Highest protein', top_p, f"{fnum(P(top_p))}g protein, the most {scope(P, top_p)}."],
    ['Best protein per calorie', top_r,
     f"{fnum(P(top_r))}g protein at just {fnum(CAL(top_r))} calories, {fnum(p100(top_r))}g protein per 100 calories, "
     f"the best ratio {scope(lambda b: p100(b) or 0, top_r)}."],
    ['Most fiber', top_f,
     f"{fnum(FIB(top_f))}g of fiber, {'tied for ' if tied(FIB, top_f) else ''}the most {scope(FIB, top_f)}, "
     f"alongside {fnum(P(top_f))}g of protein."],
    ['Naturally sweetened', natural,
     f"Sweetened with {names_and(naturals(natural))}, no allulose, monk fruit, stevia, or other sugar substitute standing "
     f"in for the sugar alcohol it also avoids, with {fnum(P(natural))}g of protein."],
    ['Lowest sugar', low_s,
     f"{fnum(SUG(low_s))}g of sugar, {'tied for ' if tied(SUG, low_s) else ''}the lowest {scope(SUG, low_s, False)}, "
     f"alongside {fnum(P(low_s))}g of protein and {fnum(FIB(low_s))}g of fiber."],
]
C.check(all(p[1] for p in PICKS), 'six distinct top picks available')
C.check(P(best) >= 15 and FIB(best) >= 5 and SUG(best) <= 5, 'best overall meets the balanced bar')
add_sugar_tradeoff(PICKS)
PICKS_INTRO = ("Everyone has their own reason for wanting a protein bar, but if you're on this page, you already know you want "
               "one without sugar alcohols. Here are the best bars for what people typically look for, all free of sugar "
               "alcohols. Grades below reflect ingredient quality only, not an overall bar rating.")

# ---------------------------------------------------------------------------
# What it means: one card per sugar alcohol (flagged bars only)
# ---------------------------------------------------------------------------
def card(label, bars_hit, total, desc, found=True):
    n = len(bars_hit)
    return f'''<div class="score-card">
          <div class="score-card-label">{esc(label)}</div>
          <div class="score-card-val">{n} bar{"" if n == 1 else "s"}<span class="oil-card-pct">{esc(pct0(n, total))}%</span></div>
          <div class="score-card-desc">{esc(desc)}</div>''' + (f'''
          {found_in_html(bars_hit)}''' if found else '') + '''
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
        <p>{PCT_D}% of the {comma(NT)} bars in our database still have a sugar alcohol on the label. Here is how often each one shows up, and where it usually hides.</p>
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
gly_more = (f'<details class="oil-card-more"><summary><span class="oil-card-more-text">and {len(GLY_ALL) - 4} more</span></summary>'
            f'<span class="oil-card-more-list">, {esc(", ".join(GLY_ALL[4:]))}</span></span> <a href="#" class="oil-card-hide-link" '
            'style="font-weight:600; text-decoration:underline; text-decoration-color:var(--bs-line-soft); text-underline-offset:2px; '
            'color:var(--bs-ink); cursor:pointer;" onclick="this.closest(\'details\').open=false; return false;">Hide</a></details>')
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
        <div class="oil-card-brands" style="margin-top:.5rem;">
          <span class="oil-card-brands-label">Found in:</span> {esc(", ".join(GLY_ALL[:4]))}
          {gly_more}
        </div>
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

def shop_cell(b):
    az, ws = amazon_url(b), website_url(b)
    if az:
        return f'<a href="{esc(az)}" target="_blank" rel="noopener sponsored" class="amazon-link">Shop</a>'
    if ws:
        return f'<a href="{esc(ws)}" target="_blank" rel="noopener" class="visit-link">Shop</a>'
    return ''
def mini_row(b, note=''):
    tag = f' <span style="color:var(--muted);font-size:12px;">({esc(note)})</span>' if note else ''
    return (f'          <tr><td>{esc(b["Brand Name"])}</td><td>{esc(b["Flavor Name"])}{tag}</td><td>{fnum(P(b))}g</td>'
            f'<td>{fnum(SUG(b))}g</td><td>{grade_badge(b["score_band"])}</td><td>{shop_cell(b)}</td></tr>')
TOP10 = sort_for_list(Q)[:10]
OTHERS, _seen = [], set()
for b in sort_for_list(EF_D):  # best-graded flavor from each of 8 different brands
    if b['Brand Name'] not in _seen and len(OTHERS) < 8:
        OTHERS.append(b); _seen.add(b['Brand Name'])
OTHERS_A = sum(1 for b in EF_D if b['score_band'] == 'A')
C.check(OTHERS_A >= 3, 'several erythritol-free-but-flagged bars are A grade')
TABLE = '''      <div class="table-scroll">
        <table class="brand-table">
          <thead><tr><th>Brand</th><th>Flavor</th><th>Protein</th><th>Sugar</th><th>Ingredient Quality</th><th>Shop</th></tr></thead>
          <tbody>
{}
          </tbody>
        </table>
      </div>'''
ERYTHRITOL = f'''
    <div class="section-inner">
      <h2 class="section-title">Protein bars without erythritol</h2>
      <div class="section-body">
        <p>Erythritol is a fermented sugar alcohol made by fermenting glucose with a yeast-like fungus, roughly 70% as sweet as table sugar with close to zero calories. It has a glycemic index of 0, the lowest of any sugar alcohol on this page's screen, and is generally well tolerated at typical serving sizes, though some people still report bloating or a cooling aftertaste at higher doses.</p>
        <p>{len(ERY)} of the {comma(NT)} bars we track, about {g1(100 * len(ERY) / NT)}%, contain erythritol. Screen for erythritol on its own, ignoring the other five sugar alcohols this page screens for, and the qualifying list gets bigger: {comma(len(EF))} bars across {EF_BRANDS} brands, {GAP} more than the {comma(N)} bars that clear this guide's full six-way sugar alcohol screen. The gap is bars that skip erythritol specifically but still contain something else on this list, most often maltitol or isomalto-oligosaccharides (IMO).</p>
        <p><strong>Erythritol and maltitol are not the same thing, and our Keto and Diabetics guides don't treat them the same way.</strong> Both guides exclude the maltitol family (maltitol, polyglycitol, hydrogenated starch hydrolysates) for its meaningfully higher glycemic index, around 35 versus sucrose's 65. Neither guide excludes erythritol, since its glycemic index of 0 already behaves the way their net-carbs formula assumes. A bar with erythritol can still qualify for {link('/keto-protein-bars', 'Keto')} or {link('/best-bars-for-diabetics', 'Best Bars for Diabetics')}. A bar with maltitol cannot, even if that same bar happens to be erythritol-free.</p>
        <p>Here are 10 of the highest ingredient-quality bars that are erythritol-free and clear every sugar alcohol on this page's screen. The complete list of all {comma(N)}, filterable by grade and searchable by brand, is further down this page.</p>
      </div>
{TABLE.format(chr(10).join(mini_row(b) for b in TOP10))}
      <div class="section-body" style="margin-top:1.5rem;">
        <p>If erythritol is the only sugar alcohol you're avoiding and you don't mind maltitol, sorbitol, xylitol, isomalt, or IMO, these {len(EF_D)} bars are erythritol-free but do contain one of the others. {OTHERS_A} of them still rank as A-grade bars in their own right. Here is the best-graded flavor from {num_word(len(OTHERS))} of those brands.</p>
      </div>
{TABLE.format(chr(10).join(mini_row(b, 'contains ' + sa_names([b])) for b in OTHERS))}
      <p class="section-body" style="margin-top:1rem;">Want to skip every sugar alcohol on this page's screen, not just erythritol? The full ranked list of all {comma(N)} bars is further down this page. Prefer to check for sucralose and other artificial sweeteners too? See our {link('/no-artificial-sweeteners#no-sucralose', 'protein bars without sucralose')} section, or use the Bar Finder's {link('/bar-finder?preset=clean', 'Clean Ingredients filter')} to screen out both categories at once.</p>
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

INSIGHTS = [
    ('Almost no maltitol is a trace ingredient.',
     f'Just {len(MAL_T)} of the {len(MAL)} bars containing maltitol list it inside a "contains 2% or less" clause, including '
     f'{names_and(T_EX)}. In {len(MAL_5)} of them, including {names_and(F5_EX)}, it shows up in the first five ingredients, '
     'a real component of the recipe, not a rounding error.'),
    (f'{pct0(len(ZERO), ND)}% of flagged bars show 0g sugar alcohol on the label anyway.',
     f'{len(ZERO)} of the {ND} bars that fail this screen list a sugar alcohol on the ingredient line but declare 0g (or leave '
     f'it blank) on the Nutrition Facts panel, including {names_and(Z_EX)}. The gram count on the label and the presence of '
     'the ingredient are two different things. We check the ingredient list, not just the number.'),
    (bb_head,
     f'{len(BB_D)} of {len(BB)} flavors fail the screen, mostly on maltitol or xylitol used to hit a low-sugar number on the label.'),
    ('Whole-food bars dominate the qualifying pool.',
     f'{names_and(WHOLE)} all qualify at or near 100%. Their sweetness comes from dates, honey, or fruit rather than a '
     'manufactured sugar alcohol.'),
    ('A mixed lineup is common, not rare.',
     f"{len(MIXED)} brands we checked split meaningfully between qualifying and disqualified flavors within the same lineup. "
     f"{SPLIT_EX['brand']} is a clear case: {SPLIT_EX['q']} of {SPLIT_EX['total']} flavors qualify."),
    (f'{BRANDS_Q} brands still represented.',
     f'Even with {PCT_D}% of the database disqualified, the qualifying pool covers a wide range of protein levels, price '
     'points, and grades.'),
    ('Maltitol is the single biggest driver.',
     f"It shows up in {len(MAL)} bars, " + (f"more than twice as many as {SHORT.get(SECOND, SECOND.lower())}, the next most common."
                                            if twice else f"more than {SHORT.get(SECOND, SECOND.lower())}, the next most common.")),
]
FINDINGS = findings_html(f'What we found screening {comma(NT)} bars', f'{PCT_D}%', 'of bars contain a sugar alcohol',
                         f'{ND} of {comma(NT)} bars contain at least one of the six sugar alcohols we screen for. Maltitol is '
                         'the most common, ahead of every other sweetener on the list. It shows up mostly in low-sugar and '
                         'keto-marketed bars.', INSIGHTS)

# ---------------------------------------------------------------------------
# Brand tables
# ---------------------------------------------------------------------------
BRANDS = brand_tables_html(
    (CONSIDER, MIXED, AVOID), QF,
    h2='Best Brands of Protein Bars for No Sugar Alcohols',
    intro='Sugar alcohols turn up in brands you would not expect, and stay out of a few you might not guess either. Grade '
          'columns below show ingredient quality only, not an overall bar rating. Click any brand name to jump to its '
          'flavors in the table below.',
    table_id='nsa',
    consider_note='Every flavor from these brands is free of sugar alcohols.' if all(r['d'] == 0 for r in CONSIDER)
                  else 'Every flavor, or nearly every flavor, from these brands is free of sugar alcohols.',
    avoid_note='These brands lean on sugar alcohols across most or all of their lineup.',
    mixed_note="Some flavors qualify, some don't. Check the specific flavor before buying.",
    avoid_head='Flavors with Sugar Alcohols', avoid_last_head='Sugar Alcohols Found',
    avoid_last=lambda r: sa_names(r['disq'], lower=False),
    mixed_head='Flavors without Sugar Alcohols')

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
     f"Yes. Maltitol shows up in {len(MAL)} of the {comma(NT)} bars we track ({pct0(len(MAL), NT)}%), more than any other "
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
     "and Bobo's that qualify at or near 100%. The full ranked list is in the table below, sorted by ingredient quality."),
    ('What protein bars have sugar alcohols?',
     f"{ND} of the {comma(NT)} bars we track contain at least one sugar alcohol. Barebells "
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
     f"{len(ERY)} of the {comma(NT)} bars we track contain erythritol. {ERY_TOP[0]} ({ery_by[ERY_TOP[0]]} flavors), "
     f"{ERY_TOP[1]} ({ery_by[ERY_TOP[1]]}), and {ERY_TOP[2]} ({ery_by[ERY_TOP[2]]}) use it most, usually paired with stevia or "
     "monk fruit to hit a low-sugar, high-fiber number without a maltitol-style GI hit."),
    ('Is erythritol the same as maltitol?',
     "No. Both are sugar alcohols, but they behave differently. Erythritol has a glycemic index of 0 and is excluded from this "
     "guide's full sugar-alcohol screen but not from our Keto or Diabetics guides. Maltitol has a meaningfully higher glycemic "
     "index, around 35, and both Keto and Diabetics exclude it specifically. A bar with erythritol can still qualify for Keto "
     "or Diabetics. A bar with maltitol cannot."),
]

def plain(s): return _html.unescape(re.sub(r'<[^>]+>', '', s))
def faq_block(faqs):
    return ''.join(f'''
        <div class="faq-item">
          <button class="faq-q">{esc(q)}</button>
          <div class="faq-a">{a if '<a ' in a else esc(a)}</div>
        </div>''' for q, a in faqs) + '\n      '

# ---------------------------------------------------------------------------
# Regions
# ---------------------------------------------------------------------------
H1 = f'Best Protein Bars Without Sugar Alcohols - Ranking {comma(N)} Qualified Bars'
REGIONS = guide_head_regions(
    title=f'Best Protein Bars Without Sugar Alcohols - Ranking {comma(N)} Bars', h1=H1,
    desc=f'We checked {comma(NT)} bars for maltitol, erythritol, and other sugar alcohols. Some labels say 0g and still have one. See the {comma(N)} bars that are actually clear.',
    og_desc=f'We screened {comma(NT)} protein bars for sugar alcohols like maltitol, erythritol, and xylitol. About {pct0(N, NT)}% have none. See the {comma(N)} best, ranked by ingredient quality, brand, and macros.',
    url=URL, about='Sugar Alcohols', published=PUBLISHED, faqs=[(q, plain(a)) for q, a in FAQS], picks=PICKS)
REGIONS += [
    ('hero', f'''<h1 class="hero-title">{esc(H1)}</h1>
    <p class="hero-sub" style="color:#e8e4dc;">We reviewed {comma(NT)} protein bars available in the US for sugar alcohols like {names_and(ORDER)}. It feels like sugar alcohols are everywhere, but the good news is that only about {PCT_D}% of all protein bars have a sugar alcohol on their ingredient label. We break down and rank the best protein bars without sugar alcohols by category, brand, and macros. Not just us telling you the flavors we like.</p>'''),
    ('snapshot', f'''
    <div class="snap-item"><div class="snap-value">{comma(N)}</div><div class="snap-label">Bars qualify</div></div>
    <div class="snap-item"><div class="snap-value">{ND}</div><div class="snap-label">Bars disqualified</div></div>
    <div class="snap-item"><div class="snap-value">{A_Q}</div><div class="snap-label">A-grade bars</div></div>
    <div class="snap-item"><div class="snap-value">{BRANDS_Q}</div><div class="snap-label">Brands represented</div></div>
    <div class="snap-item"><div class="snap-value">{avg(Q, 'Protein (g)'):.1f}g</div><div class="snap-label">Avg protein</div></div>
  '''),
    ('picks', picks_section_html('Top picks for no sugar alcohols', PICKS_INTRO, PICKS)),
    ('means', MEANS),
    ('if-not-sugar-alcohols-then-what', THEN_WHAT),
    ('protein-bars-without-erythritol', ERYTHRITOL),
    ('findings', FINDINGS),
    ('brands', BRANDS),
    ('cta-heading', f'<h2 class="explore-cta-main-heading">See every bar that fits, not just the {comma(N)} on this page</h2>'),
    ('explore-more', '''
        <a href="/no-artificial-sweeteners" class="explore-more-card">
          <div class="explore-more-title">No Artificial Sweeteners</div>
          <div class="explore-more-desc">Bars that skip sucralose, ace-K, and other artificial sweeteners entirely.</div>
        </a>
        <a href="/keto-protein-bars" class="explore-more-card">
          <div class="explore-more-title">Keto Protein Bars</div>
          <div class="explore-more-desc">Ranked by net carbs, not just marketing claims on the wrapper.</div>
        </a>
        <a href="/no-seed-oils" class="explore-more-card">
          <div class="explore-more-title">No Seed Oils</div>
          <div class="explore-more-desc">Every bar screened for canola, palm, soybean, and other refined oils.</div>
        </a>
      '''),
    ('faq', faq_block(FAQS)),
]
REGIONS += guide_list_regions(Q, ALL, heading=f'{comma(N)} bars without sugar alcohols, ranked by ingredient quality', lazy_attr=True)

if __name__ == '__main__':
    n = build_guide_page(PAGE, REGIONS, Q, ALL, C)
    print(f'{PAGE}: {N} qualify, {ND} disqualified, {n} rows, grade-sync 0 mismatches')
    for label, b, why in PICKS:
        print(f'  {label}: {full(b)} ({b["score_band"]})')
