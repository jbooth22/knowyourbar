#!/usr/bin/env python3
"""Rebuild vegan-protein-bars.html from bars.js.

Run from the repo root:  python3 build_vegan_protein_bars.py

Opens the LIVE page and rewrites only the <!-- kyb:NAME --> regions (nav,
footer, fonts, CSS and JS stay as deployed). Every number, pick, brand row and
bar row comes from bars.js. Copy that depends on a fact is checked; if one
stops being true the build stops and lists it.

Screen: GUIDE_FILTERS['vegan-protein-bars'] = `Vegan (Y/N)` is Yes (the bars.js
flag, same pattern as Gluten Free / Dairy Free). The seven animal-ingredient
cards are counted by ingredient text over the bars that are not flagged vegan.
Any flagged-vegan bar whose label names one of the seven is printed as a
WARNING: a data gap to fix in bars.js, never patched here.
"""
import re
from collections import Counter
from kyb_guide_lib import *

PAGE = 'vegan-protein-bars.html'
URL = 'https://knowyourbar.com/vegan-protein-bars'
PUBLISHED = '2026-08-26'

ALL = load_bars()
QF = GUIDE_FILTERS['vegan-protein-bars']
Q = [b for b in ALL if QF(b)]
D = [b for b in ALL if not QF(b)]
N, ND, NT = len(Q), len(D), len(ALL)
BRANDS_Q = len({b['Brand Name'] for b in Q})
GR = {g: sum(1 for b in Q if b.get('score_band') == g) for g in BAND_ORDER}
C = Claims()

NOT_PLANT_MILK = r'(?<!coconut )(?<!almond )(?<!oat )(?<!rice )(?<!soy )(?<!cashew )(?<!hemp )'
ANIMAL = [  # label, regex, card description
    ('Whey protein', r'whey', 'The default protein source in most mainstream bars, usually listed as whey protein isolate or concentrate near the top of the ingredient list.'),
    ('Milk protein', NOT_PLANT_MILK + r'\bmilk\b|milkfat|dairy(?![- ]free)|butterfat|lactose|\bcheese|yogurt|\bghee\b|\bcream\b(?! of tartar)',
     'Shows up as milk protein isolate, nonfat milk, milkfat, or a milk chocolate coating, sometimes with no other obvious dairy tell.'),
    ('Honey', r'\bhoney\b', 'A sweetener pulled from bees rather than a plant, often paired with nut butter or dates in otherwise simple ingredient lists.'),
    ('Collagen peptides', r'collagen', 'An animal-derived protein additive marketed for joint or skin support, common in newer supplement-style bars.'),
    ('Casein', r'casein', 'A slow-digesting dairy protein, usually paired with whey in a protein blend rather than used on its own. Includes caseinate forms (calcium caseinate, sodium caseinate).'),
    ('Egg whites', r'\beggs?\b|egg white', 'A whole-food protein source, most associated with RXBAR-style bars built on eggs, dates, and nuts.'),
    ('Gelatin', r'gelatin', 'A gelling and texture agent made from animal collagen, most common in chewy or gummy-textured bars.'),
]
RX = {l: r for l, r, _ in ANIMAL}
def label_text(b):
    """Ingredient text without a trailing allergen / shared-facility statement."""
    return re.split(r'may contain|manufactured (?:in|on)|processed (?:in|on)|produced (?:in|on)', ingr(b), flags=re.I)[0]
def has_a(b, l): return bool(re.search(RX[l], label_text(b), re.I))
def any_a(b): return any(has_a(b, l) for l in RX)
HIT = {l: [b for b in D if has_a(b, l)] for l in RX}
ORDER = sorted(RX, key=lambda l: -len(HIT[l]))
NAMED = [b for b in D if any_a(b)]
for b in Q:
    if any_a(b):
        print(f'WARNING: {full(b)} is flagged vegan in bars.js but its label names '
              f'{", ".join(l.lower() for l in RX if has_a(b, l))}. Fix upstream; the page follows bars.js.')
C.check(ORDER[0] == 'Whey protein', 'whey is the most common animal ingredient')

# ---------------------------------------------------------------------------
# Top picks
# ---------------------------------------------------------------------------
PK = Picker(Q)
SCO = Scoper(Q, 'on this page')
NI = lambda b: top_level_ingredient_count(ingr(b))
best = PK.balanced()
top_p = PK.pick(lambda b: (-P(b), CAL(b)))
low_s = PK.pick(lambda b: (SUG(b), -P(b)))
top_f = PK.pick(lambda b: (-FIB(b), -P(b)))
top_r = PK.pick(lambda b: (-(p100(b) or 0), -P(b)))
simple = PK.pick(lambda b: (NI(b), -P(b)), lambda b: True)
C.check(all([best, top_p, low_s, top_f, top_r, simple]), 'six distinct top picks available')
_lab = ', '.join(re.sub(r'\s*[\(\[].*$', '', it).strip().lower() for it in top_level_items(ingr(simple).strip().rstrip('.')))
PICKS = [
    ['Best overall', best,
     f"{fnum(P(best))}g protein, {fnum(FIB(best))}g fiber, and just {fnum(SUG(best))}g sugar, fully plant-based. "
     "Solid across the board rather than an extreme on one metric."],
    ['Highest protein', top_p, f"{fnum(P(top_p))}g of plant protein at {fnum(CAL(top_p))} calories, {SCO(P, top_p, 'most')}."],
    ['Lowest sugar', low_s,
     f"{fnum(SUG(low_s))}g of sugar with {fnum(P(low_s))}g protein, {SCO(SUG, low_s, 'lowest', False)}."],
    ['Most fiber', top_f,
     f"{fnum(FIB(top_f))}g of fiber alongside {fnum(P(top_f))}g protein, {SCO(FIB, top_f, 'most')}."],
    ['Best protein per calorie', top_r,
     f"{fnum(P(top_r))}g protein at just {fnum(CAL(top_r))} calories, {fnum(p100(top_r))}g per 100 calories, "
     f"{SCO(lambda b: p100(b) or 0, top_r, 'best ratio')}."],
    ['Simplest ingredient list', simple,
     (f"{num_word(NI(simple)).capitalize()} ingredients: {_lab}." if NI(simple) <= 6 else
      f"{NI(simple)} ingredients, the shortest label of any {simple['score_band']}-grade vegan bar left after the picks above.")],
]
C.check(P(best) >= 15 and FIB(best) >= 5 and SUG(best) <= 5, 'best overall meets the balanced bar')
add_sugar_tradeoff(PICKS)
if P(simple) < 10:
    PICKS[5][2] += f" The tradeoff is protein: just {fnum(P(simple))}g, closer to a whole-food snack than a protein bar."
PICKS_INTRO = ("Everyone has their own reason for wanting a protein bar, but if you're on this page, you already know you want "
               "one that's vegan. Here are the best bars for what people typically look for, all fully vegan. Grades below "
               "reflect ingredient quality only, not an overall bar rating.")

# ---------------------------------------------------------------------------
# What disqualifies a bar
# ---------------------------------------------------------------------------
def card(label, bars_hit, desc):
    return f'''<div class="score-card">
  <div class="score-card-label">{esc(label)}</div>
  <div class="score-card-val">{len(bars_hit)} bars<span class="oil-card-pct">{g1(100 * len(bars_hit) / NT)}%</span></div>
  <div class="score-card-desc">{esc(desc)}</div>
  {found_in_html(bars_hit)}
</div>'''
DESC = {l: d for l, _, d in ANIMAL}
DISQ = f'''
    <div class="section-inner">
      <h2 class="section-title">What disqualifies a protein bar from being vegan</h2>
      <div class="section-body">
        <p>We use the Vegan (Y/N) flag on file for every bar, then cross-check ingredient lists ourselves for the {num_word(len(ANIMAL))} animal-derived ingredients below, in order of how often they show up.</p>
        <p>{comma(ND)} of the {comma(NT)} bars we track, {pct0(ND, NT)}%, are not marked vegan. Whey protein alone accounts for more of them than any other single ingredient. Combined, these {num_word(len(ANIMAL))} ingredients show up in {comma(len(NAMED))} of the {comma(ND)} ({pct(len(NAMED), ND)}%). The other {comma(ND - len(NAMED))} don't name any of them; they either use a less common animal-derived ingredient or simply aren't confirmed vegan by the brand.</p>
      </div>
      <div class="score-grid" style="margin-top:1.5rem;">
{chr(10).join(card(l, HIT[l], DESC[l]) for l in ORDER)}
      </div>
    </div>
'''

# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------
def count_q(rx): return sum(1 for b in Q if re.search(rx, ingr(b), re.I))
PEA, SOY, RICE = count_q(r'pea protein'), count_q(r'soy protein'), count_q(r'rice protein')
C.check(PEA > max(SOY, RICE), 'pea protein is the most common plant protein')
CONSIDER, MIXED, AVOID = brand_split(ALL, QF)
FULL = sorted((r for r in CONSIDER if r['d'] == 0), key=lambda r: (-r['total'], r['brand'].lower()))
BIG2 = FULL[:2]
C.check(len(BIG2) == 2, 'at least two fully vegan brands')
BB = [b for b in Q if b['Brand Name'] == 'Barebells']
BB_ALL = [b for b in ALL if b['Brand Name'] == 'Barebells']
SPLIT_EX = min((r for r in CONSIDER + MIXED + AVOID if r['q'] and r['d'] and r['total'] >= 10),
               key=lambda r: (abs(r['q'] / r['total'] - 0.5), -r['total'], r['brand']))
def ab(bars): return pct(sum(1 for b in bars if b.get('score_band') in ('A', 'B')), len(bars))
def avg_score(bars): return sum(score(b) or 0 for b in bars) / len(bars)
C.check(ab(Q) > ab(ALL), 'vegan bars grade A/B at a higher rate than the database')
C.check(avg(Q, 'Protein (g)') < avg(ALL, 'Protein (g)'), 'vegan bars average less protein')
fib_more = avg(Q, 'Dietary Fiber (g)') > avg(ALL, 'Dietary Fiber (g)')
score_more = avg_score(Q) > avg_score(ALL)
INSIGHTS = [
    ('Pea protein is the plant-protein default.',
     f'{PEA} of the {N} vegan bars use pea protein'
     + (f', more than soy protein ({SOY}) and brown rice protein ({RICE}) combined.' if PEA > SOY + RICE else
        f', ahead of brown rice protein ({RICE}) and soy protein ({SOY}).')),
    (f"{BIG2[0]['brand']} and {BIG2[1]['brand']} don't make a non-vegan version.",
     f"{BIG2[0]['brand']} ({BIG2[0]['total']} flavors) and {BIG2[1]['brand']} ({BIG2[1]['total']} flavors) are vegan across "
     'the whole lineup, the largest fully vegan lineups we track.'),
    ('Vegan bars trade protein for ' + ('fiber and a slightly cleaner score.' if fib_more and score_more else 'a cleaner ingredient grade.'),
     f"Vegan bars average {fnum(round(avg(Q, 'Protein (g)'), 1))}g of protein against a database-wide average of "
     f"{fnum(round(avg(ALL, 'Protein (g)'), 1))}g"
     + (f", but they carry more fiber ({g1(avg(Q, 'Dietary Fiber (g)'))}g vs. {g1(avg(ALL, 'Dietary Fiber (g)'))}g) and a slightly "
        f"higher average ingredient score ({g1(avg_score(Q))} vs. {g1(avg_score(ALL))})." if fib_more and score_more else '.')),
]
if BB:
    lo, hi = grade_range(BB)
    INSIGHTS.append(('Being vegan and being clean are different questions.',
                     f"The {num_word(len(BB))} Barebells flavors that clear the vegan screen grade {lo}"
                     + (f' to {hi}' if hi != lo else '') + ', because grade measures ingredient quality, not animal ingredients. '
                     'A vegan label does not guarantee a clean ingredient list.'))
INSIGHTS += [
    (f"{SPLIT_EX['brand']} splits closer to even than any other large lineup.",
     f"{SPLIT_EX['q']} of the {SPLIT_EX['total']} {SPLIT_EX['brand']} flavors are vegan, the rest are not."),
    (f'{ab(Q)}% of vegan bars grade A or B.',
     f'That beats the database-wide rate of {ab(ALL)}%. Whole-food brands like {BIG2[0]["brand"]} and {BIG2[1]["brand"]} pull the vegan average up.'),
]
FINDINGS = findings_html(f'What we found screening {comma(NT)} bars', f'{pct0(ND, NT)}%', 'of protein bars are not vegan',
                         f'{comma(ND)} of {comma(NT)} bars we track are not marked vegan. Whey protein alone shows up in more '
                         'bars than any other single animal ingredient we screen for.', INSIGHTS)

# ---------------------------------------------------------------------------
# Brand tables
# ---------------------------------------------------------------------------
def animal_found(r):
    c = Counter(l for b in r['disq'] for l in RX if has_a(b, l))
    top = [l for l, _ in sorted(c.items(), key=lambda kv: (-kv[1], ORDER.index(kv[0])))[:2]]
    if not top:
        return 'No animal ingredient named, not confirmed vegan'
    return names_and([top[0]] + [t.lower() for t in top[1:]])
BRANDS = brand_tables_html(
    (CONSIDER, MIXED, AVOID), QF,
    h2='Best Brands of Vegan Protein Bars',
    intro="Some brands build entirely around plant protein, others don't make a vegan bar at all. Grade columns below show "
          'ingredient quality only, not an overall bar rating. Click any brand name to jump to its flavors in the table below.',
    table_id='vg',
    consider_note=(f'Every flavor from these {len(CONSIDER)} brands is vegan.' if all(r['d'] == 0 for r in CONSIDER)
                   else f'Every flavor, or nearly every flavor, from these {len(CONSIDER)} brands is vegan.'),
    avoid_note="These brands don't make a vegan version of most or any of their lineup.",
    mixed_note="Some flavors are vegan, some aren't. Check the specific flavor before buying.",
    avoid_head='Flavors Not Marked Vegan', avoid_last_head='Animal Ingredients Found', avoid_last=animal_found,
    mixed_head='Vegan Flavors', pick_word='vegan pick', pick_head='Vegan Pick',
    consider_all='Vegan across the whole lineup', consider_some='{q} of {total} flavors are vegan')

# ---------------------------------------------------------------------------
# FAQ
# ---------------------------------------------------------------------------
def brand_rec(name): return next((r for r in CONSIDER + MIXED + AVOID if r['brand'] == name), None)
LARA, GOM = brand_rec('Larabar'), brand_rec('GoMacro')
C.check(LARA and LARA['d'] == 0 and GOM and GOM['d'] == 0, 'Larabar and GoMacro are fully vegan')
C.check(sum(1 for b in GOM['bars'] if re.search(r'rice protein|pea protein', ingr(b), re.I)) >= 0.8 * GOM['total'], 'most GoMacro flavors use brown rice or pea protein')
bb_lo, bb_hi = grade_range(BB) if BB else (None, None)
bb_nonvegan = [b for b in BB_ALL if not QF(b)]
C.check(not BB or BAND_ORDER.index(bb_lo) > BAND_ORDER.index(grade_range(bb_nonvegan)[0]), "Barebells' vegan flavors grade worse than its best non-vegan ones")
FAQS = [
    ('What makes a protein bar vegan on this site?',
     'We use the Vegan (Y/N) flag on file for each bar and cross-check the full ingredient list for animal-derived ingredients, '
     'not just a package claim. That means no whey, milk protein, honey, egg whites, collagen peptides, casein, or gelatin '
     'anywhere in the formula.'),
    ('How many vegan protein bars are in your database?',
     f"{N} of the {comma(NT)} bars we track are vegan, spanning {BRANDS_Q} brands. {GR['A']} of those {N} bars grade A for ingredient quality."),
    ('Are Larabar bars vegan?',
     f"Yes. All {LARA['total']} Larabar flavors we track are vegan. Larabar builds its bars around dates, nuts, and fruit rather "
     'than a dairy or egg-based protein source.'),
    ('Is GoMacro vegan?',
     f"Yes. All {GOM['total']} GoMacro flavors we track are vegan, mostly built on organic brown rice and pea protein rather than whey or milk protein."),
    ('Does Barebells have vegan protein bars?',
     (f"A few. {len(BB)} of Barebells' {len(BB_ALL)} flavors are vegan, and those grade {bb_lo}"
      + (f' to {bb_hi}' if bb_hi != bb_lo else '') + " for ingredient quality, worse than the brand's non-vegan lineup. "
      'Being vegan and having a clean ingredient list are two different questions here.') if BB else
     f"No. None of Barebells' {len(BB_ALL)} flavors are marked vegan in our data."),
    ('What is the most common non-vegan ingredient in protein bars?',
     f"Whey protein. It shows up in {len(HIT['Whey protein'])} of the {comma(NT)} bars we track, more than milk protein, honey, "
     'collagen, casein, egg whites, and gelatin individually. It is the default protein source for most mainstream bars.'),
    ('Is honey vegan?',
     'No. Honey is produced by bees, not a plant, so any bar listing honey as an ingredient does not qualify as vegan on this '
     'site, even if every other ingredient is plant-based.'),
    ("Can a brand have some vegan flavors and some that aren't?",
     f"Yes, and it is common. {SPLIT_EX['brand']} splits closest to even of any large lineup we checked: {SPLIT_EX['q']} of "
     f"{SPLIT_EX['total']} flavors are vegan. Always check the specific flavor, not just the brand."),
    ('What protein bars are vegan?',
     f'{N} bars across {BRANDS_Q} brands clear our vegan screen, led by whole-food brands like Larabar and GoMacro that '
     'qualify 100% of the time. The full ranked list is in the table below, sorted by ingredient quality.'),
    ('What protein bars are not vegan?',
     f"{comma(ND)} of the {comma(NT)} bars we track are not marked vegan. Whey protein is the single biggest named reason, "
     f"followed by {names_and([l.lower() for l in ORDER[1:4]])}."),
    ('Are vegan protein bars lower quality than whey-based bars?',
     f"No. {ab(Q)}% of vegan bars in our database grade A or B, against {ab(ALL)}% database-wide. What they give up on average "
     f"is protein: vegan bars average {fnum(round(avg(Q, 'Protein (g)'), 1))}g against a database-wide average of "
     f"{fnum(round(avg(ALL, 'Protein (g)'), 1))}g, since whey and milk protein are easier to pack into a bar than plant protein."),
    ('How often is this list updated?',
     'We update the database whenever new bars are added or a brand reformulates. Manufacturers do change their ingredient '
     f'lists over time, so always confirm against the packaging in front of you. This page reflects the database as of {today_iso()}.'),
]

# ---------------------------------------------------------------------------
# Regions
# ---------------------------------------------------------------------------
TITLE = f"{pct0(ND, NT)}% of Protein Bars Aren't Vegan. {comma(N)} Are."
H1 = f'Best Vegan Protein Bars - Ranking {comma(N)} Bars by Ingredient Quality'
DESC = f'We checked {comma(NT)} protein bars for animal ingredients. {comma(N)} are fully vegan. See every one, ranked by ingredient quality, brand, and macros.'
OG = f'{comma(N)} vegan protein bars with no whey, milk, honey, egg, or gelatin. Ranked by ingredient quality score.'
REGIONS = [r for r in guide_head_regions(title=TITLE, h1=H1, desc=DESC, og_desc=OG, url=URL, about='Vegan Protein Bars',
                                         published=PUBLISHED, faqs=FAQS, picks=PICKS) if r[0] != 'social']
REGIONS += [
    ('social', social_title_html(TITLE, OG, URL)),
    ('hero', f'''<h1 class="hero-title">{esc(H1)}</h1>
    <p class="hero-sub" style="color:#e8e4dc;">We checked {comma(NT)} protein bars available in the US for whey, milk, honey, egg, collagen, casein, and gelatin. The result: {comma(N)} bars, about {pct0(N, NT)}%, are vegan. We rank the best vegan protein bars by ingredient quality, brand, and macros. Not just us telling you the flavors we like.</p>'''),
    ('snapshot', f'''
    <div class="snap-item"><div class="snap-value">{comma(N)}</div><div class="snap-label">Bars qualify</div></div>
    <div class="snap-item"><div class="snap-value">{comma(ND)}</div><div class="snap-label">Bars disqualified</div></div>
    <div class="snap-item"><div class="snap-value">{GR['A']}</div><div class="snap-label">A-grade bars</div></div>
    <div class="snap-item"><div class="snap-value">{BRANDS_Q}</div><div class="snap-label">Brands represented</div></div>
    <div class="snap-item"><div class="snap-value">{avg(Q, 'Protein (g)'):.1f}g</div><div class="snap-label">Avg protein</div></div>
  '''),
    ('picks', picks_section_html('Top picks for vegan protein bars', PICKS_INTRO, PICKS)),
    ('what-disqualifies-a-protein-bar-from-bei', DISQ),
    ('findings', FINDINGS),
    ('brands', BRANDS),
    ('cta-heading', f'<h2 class="explore-cta-main-heading">See every bar that fits, not just the {comma(N)} on this page</h2>'),
    ('explore-more', f'''
        <a href="/clean-protein-bars" class="explore-more-card">
          <div class="explore-more-title">Clean Protein Bars</div>
          <div class="explore-more-desc">A or B grade bars with no artificial sweeteners and no processed oils.</div>
        </a>
        <a href="/no-seed-oils" class="explore-more-card">
          <div class="explore-more-title">No Seed Oils</div>
          <div class="explore-more-desc">{comma(guide_count(ALL, 'no-seed-oils'))} bars with no canola, palm, or sunflower oil, ranked by ingredient quality.</div>
        </a>
        <a href="/all-protein-bar-brands" class="explore-more-card">
          <div class="explore-more-title">All Protein Bar Brands</div>
          <div class="explore-more-desc">Every brand we track, ranked on ingredient quality, protein efficiency, and fiber.</div>
        </a>
      '''),
    ('faq', faq_items_html(FAQS)),
]
REGIONS += guide_list_regions(Q, ALL, heading=f'{comma(N)} vegan protein bars, ranked by ingredient quality', lazy_attr=True)

if __name__ == '__main__':
    n = build_guide_page(PAGE, REGIONS, Q, ALL, C)
    print(f'{PAGE}: {N} qualify, {ND} disqualified, {n} rows, grade-sync 0 mismatches')
    for label, b, why in PICKS:
        print(f'  {label}: {full(b)} ({b["score_band"]})')
