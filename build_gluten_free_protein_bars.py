#!/usr/bin/env python3
"""Rebuild gluten-free-protein-bars.html from bars.js.

Run from the repo root:  python3 build_gluten_free_protein_bars.py

Replaces the older full-page generator. Opens the LIVE page and rewrites only
the <!-- kyb:NAME --> regions (nav, footer, fonts, CSS and JS stay as
deployed). Every number, pick, brand row and bar row comes from bars.js. Copy
that depends on a fact is checked; if one stops being true the build stops and
lists it.

Screen: GUIDE_FILTERS['gluten-free-protein-bars'] = `Gluten Free (Y/N)` is Yes
(certification field, no macro or grade gate). Wheat and barley/malt are
counted by ingredient text over the bars that are not labeled gluten free,
ignoring "may contain" / shared-facility statements. A gluten-free-labeled bar
whose own ingredients name wheat or barley is printed as a WARNING.
"""
import re
from kyb_guide_lib import *

PAGE = 'gluten-free-protein-bars.html'
URL = 'https://knowyourbar.com/gluten-free-protein-bars'
PUBLISHED = '2026-08-26'

ALL = load_bars()
QF = GUIDE_FILTERS['gluten-free-protein-bars']
Q = [b for b in ALL if QF(b)]
D = [b for b in ALL if not QF(b)]
N, ND, NT = len(Q), len(D), len(ALL)
BRANDS_Q = len({b['Brand Name'] for b in Q})
GR = {g: sum(1 for b in Q if b.get('score_band') == g) for g in BAND_ORDER}
C = Claims()

GLUTEN = {'wheat': r'(?<!buck)wheat', 'barley': r'barley|\bmalt(?:ed)?\b(?!odextrin|itol|ose)|malt extract|malt syrup', 'rye': r'\brye\b'}
def label_text(b):
    return re.split(r'may contain|manufactured (?:in|on)|processed (?:in|on)|produced (?:in|on)|made in a facility|in a facility', ingr(b), flags=re.I)[0]
def has_g(b, k): return bool(re.search(GLUTEN[k], label_text(b), re.I))
WHEAT = [b for b in D if has_g(b, 'wheat')]
BARLEY = [b for b in D if has_g(b, 'barley')]
NAMED = [b for b in D if any(has_g(b, k) for k in GLUTEN)]
UNLABELED = [b for b in D if b not in NAMED]
for b in Q:
    if any(has_g(b, k) for k in GLUTEN):
        print(f'WARNING: {full(b)} is labeled gluten free in bars.js but its ingredients name '
              f'{", ".join(k for k in GLUTEN if has_g(b, k))}. Check the label; the page follows bars.js.')
C.check(len(WHEAT) > len(BARLEY), 'wheat is named more often than barley or malt')

# ---------------------------------------------------------------------------
# Top picks
# ---------------------------------------------------------------------------
PK = Picker(Q)
SCO = Scoper(Q, 'on this page')
NI = lambda b: top_level_ingredient_count(ingr(b))
best = PK.balanced()
low_s = PK.pick(lambda b: (SUG(b), -P(b)))
top_f = PK.pick(lambda b: (-FIB(b), -P(b)))
top_p = PK.pick(lambda b: (-P(b), CAL(b)))
low_cal = PK.pick(lambda b: (CAL(b), -P(b)))
simple = PK.pick(lambda b: (NI(b), -P(b)))
C.check(all([best, top_p, low_s, top_f, low_cal, simple]), 'six distinct top picks available')
_lab = ', '.join(re.sub(r'\s*[\(\[].*$', '', it).strip().lower() for it in top_level_items(ingr(simple).strip().rstrip('.')))
PICKS = [
    ['Best overall', best,
     f"{fnum(P(best))}g protein, {fnum(FIB(best))}g fiber, and just {fnum(SUG(best))}g sugar in one gluten free bar. "
     "Solid across the board rather than an extreme on one metric."],
    ['Highest protein', top_p, f"{fnum(P(top_p))}g protein at {fnum(CAL(top_p))} calories, {SCO(P, top_p, 'most')}."],
    ['Lowest sugar', low_s, f"{fnum(SUG(low_s))}g of sugar with {fnum(P(low_s))}g protein, {SCO(SUG, low_s, 'lowest', False)}."],
    ['Most fiber', top_f, f"{fnum(FIB(top_f))}g of fiber alongside {fnum(P(top_f))}g protein, {SCO(FIB, top_f, 'most')}."],
    ['Lowest calorie', low_cal,
     f"{fnum(CAL(low_cal))} calories with {fnum(P(low_cal))}g protein, {SCO(CAL, low_cal, 'lowest', False)}."],
    ['Simplest ingredient list', simple,
     f"{num_word(NI(simple)).capitalize()} ingredients: {_lab}." if NI(simple) <= 6 else
     f"{NI(simple)} ingredients, the shortest label of any {simple['score_band']}-grade gluten free bar left after the picks above."],
]
C.check(P(best) >= 15 and FIB(best) >= 5 and SUG(best) <= 5, 'best overall meets the balanced bar')
add_sugar_tradeoff(PICKS)
if P(simple) < 10:
    PICKS[5][2] += f" The tradeoff is protein: just {fnum(P(simple))}g, closer to a whole-food snack than a protein bar."
PICKS_INTRO = ("Everyone has their own reason for wanting a protein bar, but if you're on this page, you already know you want "
               "one that's gluten free. Here are the best bars for what people typically look for, all gluten free. Grades "
               "below reflect ingredient quality only, not an overall bar rating.")

# ---------------------------------------------------------------------------
# What disqualifies a bar
# ---------------------------------------------------------------------------
def card(label, bars_hit, desc, found=True):
    return (f'''<div class="score-card">
  <div class="score-card-label">{esc(label)}</div>
  <div class="score-card-val">{len(bars_hit)} bars<span class="oil-card-pct">{g1(100 * len(bars_hit) / NT)}%</span></div>
  <div class="score-card-desc">{esc(desc)}</div>''' + (f'\n  {found_in_html(bars_hit)}' if found else '') + '\n</div>')
DISQ = f'''
    <div class="section-inner">
      <h2 class="section-title">What disqualifies a protein bar from being gluten free</h2>
      <div class="section-body">
        <p>We check the Gluten Free (Y/N) label on file for every bar, then cross-check ingredient lists ourselves for wheat and barley or malt, the two gluten sources that show up by name in our data. {comma(N)} of {comma(NT)} bars, about {pct0(N, NT)}%, carry a gluten free label. The other {comma(ND)}, about {pct0(ND, NT)}%, don't.</p>
        <p>Wheat is the most common named culprit at {len(WHEAT)} bars ({g1(100 * len(WHEAT) / NT)}% of the full database), followed by barley or malt at {len(BARLEY)} bars ({g1(100 * len(BARLEY) / NT)}%). The remaining {len(UNLABELED)} bars, {g1(100 * len(UNLABELED) / NT)}% of the full database, show no wheat or barley in their own ingredient list at all. They just aren't labeled gluten free, which is a different claim from actually containing gluten.</p>
      </div>
      <div class="score-grid" style="margin-top:1.5rem;">
{card('Wheat', WHEAT, 'The most common named gluten source, usually as wheat flour, a wheat-based crisp, or a graham/cookie piece mixed into the bar.')}
{card('Barley / Malt', BARLEY, 'Shows up as barley malt extract or malt syrup, usually a flavoring or sweetener rather than a structural ingredient.')}
{card('Not labeled gluten free', UNLABELED, "No wheat or barley shows up anywhere in the ingredient list we can find, but the brand hasn't labeled or certified the bar gluten free either. That is a labeling gap, not proof the bar contains gluten.", found=False)}
      </div>
    </div>
'''

# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------
CONSIDER, MIXED, AVOID = brand_split(ALL, QF)
ALLGF = sorted((r for r in CONSIDER if r['d'] == 0), key=lambda r: (-r['total'], r['brand'].lower()))
CLIF = [b for b in ALL if b['Brand Name'] == 'CLIF Bar']
CLIF_W = [b for b in CLIF if has_g(b, 'wheat')]
CLIF_MAY = [b for b in CLIF if not has_g(b, 'wheat') and re.search(r'wheat', ingr(b), re.I)]
C.check(CLIF and not any(QF(b) for b in CLIF), 'no CLIF Bar flavor is labeled gluten free')
def clif_detail():
    parts = [f"None of CLIF Bar's {len(CLIF)} flavors carry a gluten free label."]
    if CLIF_W:
        parts.append(f'{len(CLIF_W)} list wheat as an ingredient.')
    clif_b = [b for b in CLIF if has_g(b, 'barley')]
    if clif_b:
        parts.append(f'{len(clif_b)} list barley or malt as an ingredient.')
    if CLIF_MAY:
        parts.append(f"{len(CLIF_MAY)} carry a \"may contain wheat\" warning" + (' on top of that.' if (CLIF_W or any(has_g(b, 'barley') for b in CLIF)) else ' without listing it as an ingredient.'))
    return ' '.join(parts)
SPLIT_EX = min((r for r in CONSIDER + MIXED + AVOID if r['q'] and r['d'] and r['total'] >= 10),
               key=lambda r: (abs(r['q'] / r['total'] - 0.5), -r['total'], r['brand']))
def ab(bars): return pct(sum(1 for b in bars if b.get('score_band') in ('A', 'B')), len(bars))
fq, fa = avg(Q, 'Dietary Fiber (g)'), avg(ALL, 'Dietary Fiber (g)')
fib_word = 'about the same fiber' if abs(fq - fa) < 0.3 else ('more fiber' if fq > fa else 'less fiber')
C.check(avg(Q, 'Protein (g)') < avg(ALL, 'Protein (g)'), 'gluten free bars average less protein')
better = ab(Q) > ab(ALL)
LEADERS = [f"{r['brand']} ({r['total']})" for r in ALLGF[:4]]
INSIGHTS = [
    ('Wheat is the clearest single gluten source.',
     f'{len(WHEAT)} bars ({g1(100 * len(WHEAT) / NT)}% of the database) name wheat directly'
     + (', more than double the barley/malt count.' if len(WHEAT) >= 2 * len(BARLEY) else ', more than the barley/malt count.')),
    ('CLIF Bar is not a gluten free brand.', clif_detail()),
    (f'{len(ALLGF)} brands are gluten free across their entire lineup.',
     f"Led by {names_and(LEADERS)}, "
     'these brands never reach for wheat or barley in the first place, rather than swapping it out flavor by flavor.'),
    ('Gluten free bars grade ' + ('slightly better than' if better else 'about the same as') + ' the database average.',
     f'{ab(Q)}% of gluten free bars grade A or B, against {ab(ALL)}% database-wide.'),
    (f'Gluten free bars average less protein, {fib_word}.',
     f"Gluten free bars average {fnum(round(avg(Q, 'Protein (g)'), 1))}g of protein against a database-wide average of "
     f"{fnum(round(avg(ALL, 'Protein (g)'), 1))}g, and {g1(fq)}g of fiber vs. {g1(fa)}g."),
    (f"{SPLIT_EX['brand']} splits closer to even than any other large lineup.",
     f"{SPLIT_EX['q']} of the {SPLIT_EX['total']} {SPLIT_EX['brand']} flavors are gluten free, the rest are not."),
]
FINDINGS = findings_html(
    f'What we found screening {comma(NT)} bars', f'{g1(100 * len(UNLABELED) / NT)}%',
    "of all protein bars show no wheat or barley, yet still aren't labeled gluten free",
    f"{len(UNLABELED)} of the {comma(NT)} bars we track have no wheat or barley anywhere in their own ingredient list, but "
    "the brand hasn't labeled or certified them gluten free. Not being labeled gluten free is not the same as containing gluten.",
    INSIGHTS)

# ---------------------------------------------------------------------------
# Brand tables
# ---------------------------------------------------------------------------
def gluten_found(r):
    w = any(has_g(b, 'wheat') for b in r['disq'])
    ba = any(has_g(b, 'barley') for b in r['disq'])
    return 'Wheat and barley malt' if w and ba else 'Wheat' if w else 'Barley malt' if ba else 'Not labeled gluten free'
BRANDS = brand_tables_html(
    (CONSIDER, MIXED, AVOID), QF,
    h2='Best Brands of Gluten Free Protein Bars',
    intro='Some brands build their whole lineup without wheat or barley, others lean on it across the board. Grade columns '
          'below show ingredient quality only, not an overall bar rating. Click any brand name to jump to its flavors in the table below.',
    table_id='gf',
    consider_note=(f'Every flavor from these {len(CONSIDER)} brands is gluten free.' if all(r['d'] == 0 for r in CONSIDER)
                   else f'Every flavor, or nearly every flavor, from these {len(CONSIDER)} brands is gluten free.'),
    avoid_note='These brands lean on wheat, barley, or an unlabeled formula across most or all of their lineup.',
    mixed_note="Some flavors are gluten free, some aren't. Check the specific flavor before buying.",
    avoid_head='Flavors Without Gluten Free Label', avoid_last_head='Gluten Source Found', avoid_last=gluten_found,
    mixed_head='Gluten Free Flavors', pick_word='gluten free pick', pick_head='Gluten Free Pick',
    consider_all='Gluten free across the whole lineup', consider_some='{q} of {total} flavors are gluten free')

# ---------------------------------------------------------------------------
# FAQ
# ---------------------------------------------------------------------------
LARA = next((r for r in CONSIDER + MIXED + AVOID if r['brand'] == 'Larabar'), None)
C.check(LARA and LARA['d'] == 0, 'every Larabar flavor is labeled gluten free')
FAQS = [
    ('What makes a protein bar gluten free on this site?',
     f'We use the Gluten Free (Y/N) label on file for each bar. {comma(N)} of the {comma(NT)} bars we track carry that label. '
     'We also cross-check ingredient lists ourselves for wheat and barley or malt, the two named gluten sources that show up most in the data.'),
    ('How many gluten free protein bars are in your database?',
     f"{comma(N)} of the {comma(NT)} bars we track are labeled gluten free, spanning {BRANDS_Q} brands. {GR['A']} of those "
     f"{comma(N)} bars grade A for ingredient quality."),
    ('Is CLIF Bar gluten free?',
     'Not by label. ' + clif_detail() + ' If you need to avoid gluten, look elsewhere.'),
    ('Are Larabar bars gluten free?',
     f"Yes. All {LARA['total']} Larabar flavors we track are labeled gluten free. Larabar builds its bars around dates, nuts, "
     'and fruit rather than a wheat-based binder or crisp.'),
    ('What is the most common gluten ingredient in protein bars?',
     f'Wheat. It shows up by name in {len(WHEAT)} of the {comma(NT)} bars we track'
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
     f"{ALLGF[1]['brand']} that qualify across their entire lineup. The full ranked list is in the table below, sorted by ingredient quality."),
    ('What protein bars are not gluten free?',
     f"{comma(ND)} of the {comma(NT)} bars we track don't carry a gluten free label. Wheat is the most common named reason, "
     'followed by barley or malt. Most of the remaining bars simply haven\'t been labeled, without an identifiable gluten ingredient in the list.'),
    ('Are gluten free protein bars lower quality than regular bars?',
     f"No. Gluten free bars in our database grade A or B at {'a slightly higher rate than' if better else 'about the same rate as'} "
     f"the database as a whole ({ab(Q)}% vs. {ab(ALL)}%). What they give up on average is protein: gluten free bars average "
     f"{fnum(round(avg(Q, 'Protein (g)'), 1))}g against a database-wide average of {fnum(round(avg(ALL, 'Protein (g)'), 1))}g."),
    ('How often is this list updated?',
     'We update the database whenever new bars are added or a brand reformulates. Manufacturers do change their ingredient '
     f'lists over time, so always confirm against the packaging in front of you. This page reflects the database as of {today_iso()}.'),
]
C.check(len(ALLGF) >= 4, 'at least four fully gluten free brands')

# ---------------------------------------------------------------------------
# Regions
# ---------------------------------------------------------------------------
TITLE = f'{pct0(N, NT)}% of Protein Bars Are Gluten Free. See All {comma(N)}.'
H1 = f'Best Gluten Free Protein Bars - Ranking {comma(N)} Qualified Bars'
DESC = f'We checked {comma(NT)} protein bars against their gluten free label. {comma(N)} qualify. See every one, ranked by ingredient quality, brand, and macros.'
OG = f'{comma(N)} gluten free protein bars, checked against the label and the ingredient list. Ranked by ingredient quality score.'
REGIONS = [r for r in guide_head_regions(title=TITLE, h1=H1, desc=DESC, og_desc=OG, url=URL, about='Gluten Free Protein Bars',
                                         published=PUBLISHED, faqs=FAQS, picks=PICKS) if r[0] != 'social']
REGIONS += [
    ('social', social_title_html(TITLE, OG, URL)),
    ('hero', f'''<h1 class="hero-title">{esc(H1)}</h1>
    <p class="hero-sub" style="color:#e8e4dc;">We checked {comma(NT)} protein bars available in the US against their Gluten Free (Y/N) label. The result: {comma(N)} bars, about {pct0(N, NT)}%, are labeled gluten free. We rank the best gluten free protein bars by ingredient quality, brand, and macros. Not just us telling you the flavors we like.</p>'''),
    ('snapshot', f'''
    <div class="snap-item"><div class="snap-value">{comma(N)}</div><div class="snap-label">Bars qualify</div></div>
    <div class="snap-item"><div class="snap-value">{comma(ND)}</div><div class="snap-label">Bars disqualified</div></div>
    <div class="snap-item"><div class="snap-value">{GR['A']}</div><div class="snap-label">A-grade bars</div></div>
    <div class="snap-item"><div class="snap-value">{BRANDS_Q}</div><div class="snap-label">Brands represented</div></div>
    <div class="snap-item"><div class="snap-value">{avg(Q, 'Protein (g)'):.1f}g</div><div class="snap-label">Avg protein</div></div>
  '''),
    ('picks', picks_section_html('Top picks for gluten free protein bars', PICKS_INTRO, PICKS)),
    ('what-disqualifies-a-protein-bar-from-bei', DISQ),
    ('findings', FINDINGS),
    ('brands', BRANDS),
    ('cta-heading', f'<h2 class="explore-cta-main-heading">See every bar that fits, not just the {comma(N)} on this page</h2>'),
    ('explore-more', f'''
        <a href="/vegan-protein-bars" class="explore-more-card">
          <div class="explore-more-title">Vegan Protein Bars</div>
          <div class="explore-more-desc">{comma(guide_count(ALL, 'vegan-protein-bars'))} bars with no whey, milk, honey, egg, or gelatin.</div>
        </a>
        <a href="/no-seed-oils" class="explore-more-card">
          <div class="explore-more-title">No Seed Oils</div>
          <div class="explore-more-desc">Bars that skip canola, soybean, and sunflower oil.</div>
        </a>
        <a href="/clean-protein-bars" class="explore-more-card">
          <div class="explore-more-title">Clean Protein Bars</div>
          <div class="explore-more-desc">A or B grade bars with no artificial sweeteners and no processed oils.</div>
        </a>
      '''),
    ('faq', faq_items_html(FAQS)),
]
REGIONS += guide_list_regions(Q, ALL, heading=f'{comma(N)} gluten free protein bars, ranked by ingredient quality', lazy_attr=True)

if __name__ == '__main__':
    n = build_guide_page(PAGE, REGIONS, Q, ALL, C)
    print(f'{PAGE}: {N} qualify, {ND} disqualified, {n} rows, grade-sync 0 mismatches')
    for label, b, why in PICKS:
        print(f'  {label}: {full(b)} ({b["score_band"]})')
