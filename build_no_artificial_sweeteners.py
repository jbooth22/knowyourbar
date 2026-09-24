#!/usr/bin/env python3
"""Rebuild no-artificial-sweeteners.html from bars.js.

Run from the repo root:  python3 build_no_artificial_sweeteners.py

Opens the LIVE page and rewrites only the <!-- kyb:NAME --> regions, so nav,
footer, fonts, CSS and JS stay exactly as deployed. Every number, pick, brand
table row and bar row comes from bars.js. Sentences that depend on a fact
(e.g. "every ace-K bar also has sucralose") are checked; if one stops being
true the build stops and lists it instead of publishing a false claim.

Screen: GUIDE_FILTERS['no-artificial-sweeteners'] (no 'Artificial Sweeteners'
concern tag). The four sweeteners in the copy are counted by ingredient text.
"""
import html as _html
import re
from kyb_guide_lib import *

PAGE = 'no-artificial-sweeteners.html'
URL = 'https://knowyourbar.com/no-artificial-sweeteners'
PUBLISHED = '2026-04-08'

ALL = load_bars()
QF = GUIDE_FILTERS['no-artificial-sweeteners']
Q = [b for b in ALL if QF(b)]
D = [b for b in ALL if not QF(b)]
N, ND, NT = len(Q), len(D), len(ALL)
BRANDS_Q = len({b['Brand Name'] for b in Q})
A_Q = sum(1 for b in Q if b.get('score_band') == 'A')
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
PCT_D = pct(ND, NT)
ONE_IN = round(NT / len(SUC)) if SUC else 0

C.check(all(any(has_sw(b, l) for l, _ in SWEETENERS) for b in D) and not any(any(has_sw(b, l) for l, _ in SWEETENERS) for b in Q),
        'the four named sweeteners match the Artificial Sweeteners screen exactly')
C.check(all(has_sw(b, 'Sucralose') for b in NON_SUC), 'every ace-K / aspartame / saccharin bar also contains sucralose')
C.check({b['Key'] for b in SUC_FREE} == {b['Key'] for b in Q}, 'sucralose-free set == no-artificial-sweetener set')
C.check(len(SUC) / ND >= 0.9, 'sucralose accounts for nearly all disqualified bars')

def link(href, text): return f'<a href="{href}">{text}</a>'
def by_brand(brand, bars=ALL): return [b for b in bars if b['Brand Name'] == brand]

# ---------------------------------------------------------------------------
# Top picks
# ---------------------------------------------------------------------------
PK = Picker(Q)
G = PK.band_grade
CALK = lambda b: num(b.get('Calories')) or 9999

def scope(fn, b, higher=True):
    """Widest honest scope for 'the most/lowest X of any ...'."""
    best = (max if higher else min)
    if fn(b) == best(fn(x) for x in Q):
        return 'of any bar with no artificial sweeteners'
    if fn(b) == best(fn(x) for x in PK.band):
        return f'of any {G}-grade bar with no artificial sweeteners'
    return f'of any {G}-grade bar with {PK.floor}g+ protein and no artificial sweeteners'

def tied(fn, b):
    pool = [x for x in PK.band if P(x) >= PK.floor]
    return sum(1 for x in pool if fn(x) == fn(b)) > 1

best = PK.balanced()
top_p = PK.pick(lambda b: (-P(b), CALK(b)))
top_r = PK.pick(lambda b: (-(p100(b) or 0), -P(b)))
low_s = PK.pick(lambda b: (SUG(b), -P(b)))
top_f = PK.pick(lambda b: (-FIB(b), -P(b)))
sa_free = PK.pick(lambda b: (-P(b), CALK(b)), lambda b: SA(b) == 0 and not has_tag(b, 'Sugar Alcohols'))

PICKS = [
    ['Best overall', best,
     f"{fnum(P(best))}g protein, {fnum(FIB(best))}g fiber, and just {fnum(SUG(best))}g sugar with no artificial sweetener "
     "on the label. Solid across the board rather than an extreme on one metric."],
    ['Highest protein', top_p,
     f"{fnum(P(top_p))}g protein, the most {scope(P, top_p)}."
     + (f" It does use {fnum(SA(top_p))}g of sugar alcohol, which this screen allows." if SA(top_p) > 0 else '')],
    ['Best protein per calorie', top_r,
     f"{fnum(P(top_r))}g protein at just {fnum(CAL(top_r))} calories, {fnum(p100(top_r))}g protein per 100 calories, "
     f"the best ratio {scope(lambda b: p100(b) or 0, top_r)}."],
    ['Lowest sugar', low_s,
     f"{fnum(SUG(low_s))}g of sugar, {'tied for ' if tied(SUG, low_s) else ''}the lowest {scope(SUG, low_s, False)}, "
     f"alongside {fnum(P(low_s))}g of protein and {fnum(FIB(low_s))}g of fiber."],
    ['Most fiber', top_f,
     f"{fnum(FIB(top_f))}g of fiber, {'tied for ' if tied(FIB, top_f) else ''}the most {scope(FIB, top_f)}, "
     f"alongside {fnum(P(top_f))}g of protein."],
    ['Also sugar-alcohol-free', sa_free,
     f"Zero sugar alcohol on top of zero artificial sweetener, with {fnum(P(sa_free))}g of protein, the most of any "
     f"{G}-grade bar that clears both screens."],
]
C.check(best is not None and all(p[1] for p in PICKS), 'six distinct top picks available')
C.check(P(best) >= 15 and FIB(best) >= 5 and SUG(best) <= 5, 'best overall meets the balanced bar (15g+/5g+/5g or less)')
add_sugar_tradeoff(PICKS)

PICKS_INTRO = ("Everyone has their own reason for wanting a protein bar, but if you're on this page, you already know you want "
               "one without artificial sweeteners. Here are the best bars for what people typically look for, all free of "
               "sucralose, acesulfame potassium, aspartame, and saccharin. Grades below reflect ingredient quality only, "
               "not an overall bar rating.")

# ---------------------------------------------------------------------------
# What it means: one score card per sweetener
# ---------------------------------------------------------------------------
DESC = {
    'Sucralose': 'Usually shows up as a flavor-rounding sweetener in low-sugar or high-fiber bars, often alongside allulose '
                 'or fiber syrups to hit a specific sugar number on the label.',
    'Acesulfame Potassium': ('Always paired with sucralose in the bars we track, never used on its own, adding a sweetness '
                             'boost on top of the primary sweetener.' if all(has_sw(b, 'Sucralose') for b in ACE) else
                             'Usually paired with sucralose, adding a sweetness boost on top of the primary sweetener.'),
    'Aspartame': 'Once common in diet foods generally, it has largely fallen out of favor in the protein bar category.',
    'Saccharin': 'The oldest artificial sweetener on this screen, now rare in this category.',
}
def sw_desc(label):
    n = len(HIT[label])
    if n == 0:
        return 'Not currently used in any bar we track. ' + DESC[label]
    if label in ('Aspartame', 'Saccharin'):
        return f'Rare: only {n} bar{"s" if n != 1 else ""} we track use{"s" if n == 1 else ""} it. ' + DESC[label]
    return DESC[label]
cards = '\n'.join(score_card_html(l, HIT[l], NT, sw_desc(l)) for l, _ in SWEETENERS)
MEANS = f'''
    <div class="section-inner">
      <h2 class="section-title">What "no artificial sweeteners" actually means</h2>
      <div class="section-body">
        <p>Artificial sweeteners are the non-nutritive, synthetic sweeteners brand makers reach for when they want zero-sugar sweetness without giving up flavor. This guide screens every bar for four of them: sucralose, acesulfame potassium, aspartame, and saccharin.</p>
        <p>{PCT_D}% of the bars in our database still have one on the label. Here is how often each one shows up, and where it usually hides.</p>
        <p>Artificial sweeteners are not the same thing as sugar alcohols. Erythritol, maltitol, and xylitol are sugar alcohols, a different category with their own digestive tradeoffs, and they show up on a different screen entirely. If erythritol or maltitol is what you are actually trying to avoid, check our {link('/no-sugar-alcohols', 'protein bars without sugar alcohols guide')} instead. Want both screens applied at once? Use the Bar Finder's {link('/bar-finder?preset=clean', 'Clean Ingredients filter')}, which excludes artificial sweeteners and sugar alcohols together.</p>
      </div>
      <div class="score-grid" style="margin-top:1.5rem;">
{cards}
      </div>
    </div>
'''

# ---------------------------------------------------------------------------
# Protein bars without sucralose
# ---------------------------------------------------------------------------
def shop_cell(b):
    az, ws = amazon_url(b), website_url(b)
    if az:
        return f'<a href="{esc(az)}" target="_blank" rel="noopener sponsored" class="amazon-link">Shop</a>'
    if ws:
        return f'<a href="{esc(ws)}" target="_blank" rel="noopener" class="visit-link">Shop</a>'
    return ''
TOP10 = sort_for_list(SUC_FREE)[:10]
top_rows = '\n'.join(
    f'          <tr><td>{esc(b["Brand Name"])}</td><td>{esc(b["Flavor Name"])}</td><td>{fnum(P(b))}g</td>'
    f'<td>{fnum(SUG(b))}g</td><td>{grade_badge(b["score_band"])}</td><td>{shop_cell(b)}</td></tr>' for b in TOP10)
SUCRALOSE = f'''
    <div class="section-inner">
      <h2 class="section-title">Protein bars without sucralose</h2>
      <div class="section-body">
        <p>Sucralose, sold under the brand name Splenda, is the artificial sweetener actually driving this guide. It is a chlorinated sugar substitute, roughly 600 times sweeter than table sugar, with zero calories and no effect on blood sugar. People skip it for different reasons: reported digestive discomfort, an aftertaste they don't like, gut microbiome research they've read, or just a preference to avoid synthetic sweeteners entirely.</p>
        <p>{len(SUC)} of the {comma(NT)} bars we track, about 1 in {ONE_IN}, contain sucralose. We checked whether screening for sucralose on its own produces a different list than screening for all four artificial sweeteners this guide covers. It doesn't. Every bar in our database that contains acesulfame potassium, aspartame, or saccharin also contains sucralose, so protein bars without sucralose and protein bars without artificial sweeteners are the exact same {comma(N)} bars across {BRANDS_Q} brands, already ranked in the full table below.</p>
        <p>Here are 10 of the highest ingredient-quality sucralose-free bars to start with. The complete list, filterable by grade and searchable by brand, is further down this page.</p>
      </div>
      <div class="table-scroll">
        <table class="brand-table">
          <thead><tr><th>Brand</th><th>Flavor</th><th>Protein</th><th>Sugar</th><th>Ingredient Quality</th><th>Shop</th></tr></thead>
          <tbody>
{top_rows}
          </tbody>
        </table>
      </div>
      <p class="section-body" style="margin-top:1rem;">Looking for a bar that also skips sugar alcohols like erythritol and maltitol? See our {link('/no-sugar-alcohols#no-erythritol', 'protein bars without erythritol')} section, or the {link('/clean-protein-bars', 'Clean Protein Bars guide')}, which requires an A or B ingredient grade with no artificial sweeteners and no processed oils. Net carbs matter more than the sweetener itself? Our {link('/keto-protein-bars', 'Keto')} and {link('/best-bars-for-diabetics', 'Best Bars for Diabetics')} guides both allow sucralose, since it doesn't affect net carbs or blood sugar, but they exclude the maltitol family specifically.</p>
    </div>
'''
C.check(not any(has_maltitol_family(b) for b in ALL if GUIDE_FILTERS['keto-protein-bars'](b)), 'keto guide excludes the maltitol family')
C.check(not any(has_maltitol_family(b) for b in ALL if GUIDE_FILTERS['best-bars-for-diabetics'](b)), 'diabetics guide excludes the maltitol family')

# ---------------------------------------------------------------------------
# Findings
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

def all_disq(brand):
    bs = by_brand(brand)
    return bool(bs) and all(not QF(b) and has_sw(b, 'Sucralose') for b in bs)
QUEST, BAREBELLS = by_brand('Quest'), by_brand('Barebells')
C.check(all_disq('Quest'), 'every Quest flavor contains sucralose')
C.check(all_disq('Barebells'), 'every Barebells flavor contains sucralose')

WHOLE = ['KIND', 'Larabar', "Bobo's", 'Aloha', 'GoMacro']
C.check(all(by_brand(w) and len(by_brand(w, Q)) / len(by_brand(w)) >= 0.9 for w in WHOLE), 'KIND, Larabar, Bobo\'s, Aloha, GoMacro all qualify at 90%+')

CONSIDER, MIXED, AVOID = brand_split(ALL, QF)
MIX4 = [r['brand'] for r in MIXED[:4]]
C.check(len(MIX4) >= 3, 'at least three mixed-lineup brands')
ACE_BRANDS = sorted({b['Brand Name'] for b in ACE})

big_detail = (f"{ND} bars, about 1 in {round(NT / ND)} in our database, contain sucralose, acesulfame potassium, aspartame, "
              "or saccharin. " + ("Sucralose is in every one of them" if len(SUC) == ND else "Sucralose alone accounts for nearly all of it")
              + ", showing up mostly in low-sugar and high-fiber bars.")
INSIGHTS = [
    ('Sucralose shows up as a named ingredient, not always a trace amount.',
     f'{len(TUCKED)} of the {len(SUC)} bars containing sucralose tuck it into a "contains 2% or less" catch-all clause near '
     f'the end of the label. The other {len(NAMED)}, including {full(EXAMPLES[0])} and {full(EXAMPLES[1])}, list it without that qualifier.'),
    ('Quest disqualifies completely.',
     f'All {len(QUEST)} tracked Quest flavors contain sucralose, part of how the brand hits its low-sugar, high-fiber macro '
     'targets across the entire lineup.'),
    ('Barebells disqualifies completely too.',
     f'{len(BAREBELLS)} of {len(BAREBELLS)} Barebells flavors contain sucralose, the same sweetener behind most of the '
     'disqualified bars on this list.'),
    ('Whole-food bars dominate the qualifying pool.',
     f'{names_and(WHOLE)} all qualify at or near 100%. Their sweetness comes from dates, fruit, or honey rather than a '
     'manufactured sweetener.'),
    ('A mixed lineup is common, not rare.',
     f'{names_and(MIX4)} are examples of brands that split meaningfully between qualifying and disqualified flavors within '
     'the same lineup.'),
    (f'{BRANDS_Q} brands still represented.',
     f'Even with {PCT_D}% of the database disqualified, the qualifying pool spans a wide range of protein levels, price '
     'points, and ingredient grades.'),
    ('Acesulfame potassium never shows up alone.',
     f'All {len(ACE)} bars containing acesulfame potassium also contain sucralose. '
     + (f'Neither {ACE_BRANDS[0]} nor {ACE_BRANDS[1]}, the only two brands using it, use it as a standalone sweetener.'
        if len(ACE_BRANDS) == 2 else f'None of the {len(ACE_BRANDS)} brands using it ({names_and(ACE_BRANDS)}) use it as a standalone sweetener.')),
]
C.check(bool(ACE) and all(has_sw(b, 'Sucralose') for b in ACE), 'acesulfame potassium never appears without sucralose')
FINDINGS = findings_html('What we found across our 1,000+ bar database', f'{PCT_D}%',
                         'of bars contain an artificial sweetener', big_detail, INSIGHTS)

# ---------------------------------------------------------------------------
# Brand tables
# ---------------------------------------------------------------------------
def sweeteners_found(r):
    found = sorted(l for l, _ in SWEETENERS if any(has_sw(b, l) for b in r['disq']))
    return names_and(found)
BRANDS = brand_tables_html(
    (CONSIDER, MIXED, AVOID), QF,
    h2='Best Brands of Protein Bars for No Artificial Sweeteners',
    intro='Artificial sweeteners cluster hard in a handful of brands and stay out of most whole-food ones entirely. Grade '
          'columns below show ingredient quality only, not an overall bar rating. Click any brand name to jump to its '
          'flavors in the table below.',
    table_id='nas',
    consider_note='Every flavor from these brands is free of artificial sweeteners.' if all(r['d'] == 0 for r in CONSIDER)
                  else 'Every flavor, or nearly every flavor, from these brands is free of artificial sweeteners.',
    avoid_note='These brands lean on artificial sweeteners across most or all of their lineup.',
    mixed_note="Some flavors qualify, some don't. Check the specific flavor before buying.",
    avoid_head='Flavors with Artificial Sweeteners', avoid_last_head='Sweeteners Found', avoid_last=sweeteners_found,
    mixed_head='Flavors without Artificial Sweeteners')

# ---------------------------------------------------------------------------
# FAQ (answers may hold links; JSON-LD gets the plain text)
# ---------------------------------------------------------------------------
STEVIA = [b for b in Q if re.search(r'stevia|reb a|rebaudioside|monk ?fruit|luo han', ingr(b), re.I)]
C.check(len(STEVIA) >= 50, 'stevia / monk fruit show up widely in qualifying bars')
bybrand_suc = {}
for b in SUC:
    bybrand_suc.setdefault(b['Brand Name'], []).append(b)
TOP_SUC = sorted(bybrand_suc, key=lambda k: (-len(bybrand_suc[k]), -len(bybrand_suc[k]) / len(by_brand(k)), k.lower()))[:5]
C.check(all(len(bybrand_suc[k]) / len(by_brand(k)) >= 0.75 for k in TOP_SUC), 'top 5 sucralose brands use it in 75%+ of their lineup')

# split examples: a mostly-clean brand and a mostly-disqualified brand, 10+ flavors, both sides present
SPLIT = [r for r in CONSIDER + MIXED + AVOID if r['total'] >= 10 and r['q'] and r['d']]
MOSTLY_CLEAN = max(SPLIT, key=lambda r: (r['q'] / r['total'], r['total'], r['brand']))
MOSTLY_DISQ = min(SPLIT, key=lambda r: (r['q'] / r['total'], -r['total'], r['brand']))
C.check(MOSTLY_CLEAN['q'] > MOSTLY_CLEAN['d'] and MOSTLY_DISQ['d'] > MOSTLY_DISQ['q'], 'split examples go opposite ways')

asp_sac_zero = not HIT['Aspartame'] and not HIT['Saccharin']
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
     f"Acesulfame potassium is a distant second at {len(ACE)} bars"
     + (", and we found zero bars in the current database containing aspartame or saccharin." if asp_sac_zero else
        f", and aspartame ({len(HIT['Aspartame'])}) and saccharin ({len(HIT['Saccharin'])}) are rarer still.")),
    ('Does Quest use artificial sweeteners?',
     f"Yes, across the entire lineup. All {len(QUEST)} tracked Quest flavors contain sucralose, part of how the brand hits "
     "its low-sugar, high-fiber numbers."),
    ('Does Barebells use artificial sweeteners?',
     f"Yes. All {len(BAREBELLS)} Barebells flavors contain sucralose, the same sweetener driving most of the "
     "artificial-sweetener bars on this list."),
    ('What protein bars don\'t have artificial sweeteners?',
     f"{comma(N)} bars across {BRANDS_Q} brands clear our artificial sweetener screen, led by whole-food brands like KIND, "
     "Larabar, and Bobo's that qualify at or near 100%. The full ranked list is in the table below, sorted by ingredient quality."),
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
     f"what you actually want to avoid, see our {link('/no-sugar-alcohols', 'protein bars without sugar alcohols guide')}, "
     f"or use the Bar Finder's {link('/bar-finder?preset=clean', 'Clean Ingredients filter')} to screen out both at once."),
    ('Do protein bars have sucralose?',
     f"Yes. {len(SUC)} of the {comma(NT)} bars we track, about 1 in {ONE_IN}, list sucralose on the ingredient label. It's "
     "the most common artificial sweetener in the category by a wide margin, see the breakdown above."),
    ('What protein bars don\'t have sucralose?',
     f"{comma(N)} bars across {BRANDS_Q} brands are sucralose-free. That's the exact same set as our full "
     "no-artificial-sweeteners list, since every bar in our database containing acesulfame potassium, aspartame, or "
     "saccharin also contains sucralose. See the sucralose-free picks above or the full ranked list below."),
    ('Which brands use sucralose the most?',
     names_and([f"{k} ({len(bybrand_suc[k])} of {len(by_brand(k))} flavors)" for k in TOP_SUC])
     + " lead the list, all using it to hit a low-sugar or high-fiber number across most or all of their lineup."),
]
C.check(len(ACE) and all(len(by_brand(k, ACE)) for k in ACE_BRANDS), 'ace-K brand list is non-empty')
C.check(len(SUC) > 5 * max(len(ACE), 1), 'sucralose leads ace-K by a wide margin')

def plain(s): return _html.unescape(re.sub(r'<[^>]+>', '', s))
def faq_block(faqs):
    items = ''.join(f'''
        <div class="faq-item">
          <button class="faq-q">{esc(q)}</button>
          <div class="faq-a">{a if '<a ' in a else esc(a)}</div>
        </div>''' for q, a in faqs)
    return items + '\n      '
FAQ_PLAIN = [(q, plain(a)) for q, a in FAQS]

# ---------------------------------------------------------------------------
# Regions
# ---------------------------------------------------------------------------
H1 = f'Best Protein Bars Without Artificial Sweeteners - Ranking {comma(N)} Qualified Bars'
REGIONS = guide_head_regions(
    title=f'Best Protein Bars Without Artificial Sweeteners - Ranking {comma(N)} Bars', h1=H1,
    desc=f'We checked 1,000+ bars for sucralose, ace-K, aspartame, and saccharin. {ND} still have one. See the {comma(N)} that are actually clear.',
    og_desc=f'We screened 1,000+ protein bars for artificial sweeteners. {pct(N, NT)}% have none. See the {comma(N)} best, ranked by ingredient quality.',
    url=URL, about='Artificial Sweeteners', published=PUBLISHED, faqs=FAQ_PLAIN, picks=PICKS)
REGIONS += [
    ('hero', f'''<h1 class="hero-title">{esc(H1)}</h1>
    <p class="hero-sub" style="color:#e8e4dc;">We reviewed every bar in our 1,000+ bar database for artificial sweeteners: sucralose, acesulfame potassium, aspartame, and saccharin. {PCT_D}% of bars still have one, almost always sucralose. If you're looking for protein bars with no artificial sweeteners, or specifically protein bars without sucralose, these are the {comma(N)} that clear every screen, broken down by category, brand, and macros. Not just us telling you the flavors we like.</p>'''),
    ('snapshot', f'''
    <div class="snap-item"><div class="snap-value">{comma(N)}</div><div class="snap-label">Bars qualify</div></div>
    <div class="snap-item"><div class="snap-value">{ND}</div><div class="snap-label">Bars disqualified</div></div>
    <div class="snap-item"><div class="snap-value">{A_Q}</div><div class="snap-label">A-grade bars</div></div>
    <div class="snap-item"><div class="snap-value">{BRANDS_Q}</div><div class="snap-label">Brands represented</div></div>
    <div class="snap-item"><div class="snap-value">{avg(Q, 'Protein (g)'):.1f}g</div><div class="snap-label">Avg protein</div></div>
  '''),
    ('picks', picks_section_html('Top picks for no artificial sweeteners', PICKS_INTRO, PICKS)),
    ('means', MEANS),
    ('protein-bars-without-sucralose', SUCRALOSE),
    ('findings', FINDINGS),
    ('brands', BRANDS),
    ('cta-heading', f'<h2 class="explore-cta-main-heading">See every bar that fits, not just the {comma(N)} on this page</h2>'),
    ('explore-more', '''
        <a href="/no-sugar-alcohols" class="explore-more-card">
          <div class="explore-more-title">No Sugar Alcohols</div>
          <div class="explore-more-desc">Bars that skip maltitol, erythritol, and other sugar alcohols entirely.</div>
        </a>
        <a href="/clean-protein-bars" class="explore-more-card">
          <div class="explore-more-title">Clean Protein Bars</div>
          <div class="explore-more-desc">A or B grade bars with no artificial sweeteners and no processed oils.</div>
        </a>
        <a href="/no-seed-oils" class="explore-more-card">
          <div class="explore-more-title">No Seed Oils</div>
          <div class="explore-more-desc">Every bar screened for canola, palm, soybean, and other refined oils.</div>
        </a>
      '''),
    ('faq', faq_block(FAQS)),
]
REGIONS += guide_list_regions(Q, ALL, heading=f'{comma(N)} bars without artificial sweeteners, ranked by ingredient quality')

if __name__ == '__main__':
    n = build_guide_page(PAGE, REGIONS, Q, ALL, C)
    print(f'{PAGE}: {N} qualify, {ND} disqualified, {n} rows, grade-sync 0 mismatches')
    for label, b, why in PICKS:
        print(f'  {label}: {full(b)} ({b["score_band"]})')
