#!/usr/bin/env python3
"""Rebuild vegan-protein-bars.html from bars.js. GUIDE PAGE v2 ("Best 10").

Run from the repo root:  python3 build_vegan_protein_bars.py

Layout and every rule: claude/GUIDE_PAGE_SPEC_V2.md (locked 2026-09-29) and
the v2 section of kyb_guide_lib.py, built the same way as the other v2 guides
(closest reference: build_gluten_free_protein_bars.py, a certification guide).
The first run migrated the live v1 page to the v2 body (head, nav and footer
kept as deployed); later runs rewrite only the <!-- kyb:NAME --> regions. Every
number, pick and brand row comes from bars.js. Copy that depends on a fact is
checked; if one stops being true the build stops and lists it. Ingredient
quality is shown and ranked as a GRADE only.

Screen: GUIDE_FILTERS['vegan-protein-bars'] = `Vegan (Y/N)` is Yes (the bars.js
flag, same pattern as Gluten Free / Dairy Free). The seven animal-ingredient
cards are counted by ingredient text over the bars that are not flagged vegan.
Any flagged-vegan bar whose label names one of the seven is printed as a
WARNING: a data gap to fix in bars.js, never patched here.
Bar Finder: /bar-finder?certs=Vegan (checked key for key below).

Guide slots (picked 2026-09-30; Jeff asked for the best picks delivered without
an approval round): Highest fiber, Best gluten-free, Best soy-free, Lowest net
carbs. Fallbacks: Best non-GMO, then Lowest sugar. Best plant-based and Best
dairy-free don't apply here (every bar is plant-based); whey is impossible.
"""
import re
from collections import Counter
from kyb_guide_lib import *

PAGE = 'vegan-protein-bars.html'
URL = 'https://knowyourbar.com/vegan-protein-bars'
PUBLISHED = '2026-08-26'
set_tie_seed('vegan-protein-bars')   # per-guide shuffle for exact ties (kyb_guide_lib, 2026-09-30)

ALL = load_bars()
QF = GUIDE_FILTERS['vegan-protein-bars']
Q = [b for b in ALL if QF(b)]
D = [b for b in ALL if not QF(b)]
N, ND, NT = len(Q), len(D), len(ALL)
BRANDS_Q = len({b['Brand Name'] for b in Q})
GR = {g: sum(1 for b in Q if b.get('score_band') == g) for g in BAND_ORDER}
C = Claims()
NC = net_carbs
C.check(not any(b.get('Vegan (Y/N)') not in ('Yes', None) for b in ALL), 'Vegan field is only Yes or blank')

NOT_PLANT_MILK = r'(?<!coconut )(?<!almond )(?<!oat )(?<!rice )(?<!soy )(?<!cashew )(?<!hemp )'
ANIMAL = [  # label, regex, card description
    ('Whey protein', r'whey', 'The default protein source in most mainstream bars, usually listed as whey protein isolate or concentrate near the top of the ingredient list.'),
    ('Milk protein', NOT_PLANT_MILK + r'\bmilk\b|milkfat|dairy(?![- ]free)|butterfat|lactose|\bcheese|yogurt|\bghee\b|\bcream\b(?! of tartar)',
     'Shows up as milk protein isolate, nonfat milk, milkfat, or a milk chocolate coating, sometimes with no other obvious dairy tell.'),
    ('Honey', r'\bhoney\b', 'A sweetener made by bees rather than a plant, often paired with nut butter or dates in otherwise simple ingredient lists.'),
    ('Collagen peptides', r'collagen', 'An animal-derived protein additive marketed for joint or skin support, common in newer supplement-style bars.'),
    ('Casein', r'casein', 'A slow-digesting dairy protein, usually paired with whey in a protein blend. Includes caseinate forms (calcium caseinate, sodium caseinate).'),
    ('Egg whites', r'\beggs?\b|egg white', 'A whole-food protein source, most associated with RXBAR-style bars built on eggs, dates, and nuts.'),
    ('Gelatin', r'gelatin', 'A gelling and texture agent made from animal collagen, most common in chewy or gummy-textured bars.'),
]
RX = {l: r for l, r, _ in ANIMAL}
DESC_A = {l: d for l, _, d in ANIMAL}
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
C.check(len(NAMED) > ND / 2, 'most non-vegan bars name one of the seven animal ingredients')

# Bar Finder parity: ?certs=Vegan (app.js CERT_MAP 'Vegan' -> 'Vegan (Y/N)', value 'yes' case-insensitive)
C.check({b['Key'] for b in ALL if (b.get('Vegan (Y/N)') or '').strip().lower() == 'yes'} == {b['Key'] for b in Q},
        'Bar Finder certs=Vegan returns exactly the guide set')
FINDER_HREF = '/bar-finder?certs=Vegan'

def link(href, text): return f'<a href="{href}">{text}</a>'
def yes(field): return lambda b: b.get(field) == 'Yes'
def by_brand(brand, bars=ALL): return [b for b in bars if b['Brand Name'] == brand]
def ab(bars): return pct0(sum(1 for b in bars if b.get('score_band') in ('A', 'B')), len(bars))

# ---------------------------------------------------------------------------
# Best 10 (spec v2)
# ---------------------------------------------------------------------------
SOY_RX = re.compile(r'\bsoy|soybean', re.I)
def nc_why(b, c):
    sa = SA(b)
    parts = f"{fnum(num(b.get('Total Carbohydrates (g)')))}g carbs minus {fnum(FIB(b))}g fiber" + (f" and {fnum(sa)}g sugar alcohol" if sa else '')
    return (f"{fnum(NC(b))}g net carbs ({parts}), {c['tied']}the lowest of any vegan bar here, with {fnum(P(b))}g protein"
            + (f", and it wins the tie on {c['tie_on']}." if c['tied'] and c['tie_on'] != 'name' else "."))
LOW_NET = Slot('Lowest net carbs', 'The fewest net carbs (total carbs minus fiber minus sugar alcohol), grade B or better, 10g+ protein.',
               lambda E: [b for b in E if NC(b) is not None], lambda b: (NC(b),) + tie_chain(b), nc_why, metric=NC)
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
    slot_highest_fiber(),
    slot_subset('Best gluten-free', 'Labeled gluten free by the brand.', yes('Gluten Free (Y/N)'),
                lambda b: 'Vegan and labeled gluten free.'),
    slot_subset('Best soy-free', 'Labeled soy free by the brand.', yes('Soy Free (Y/N)'),
                lambda b: 'Vegan and labeled soy free, for anyone who wants plant protein without soy.'),
    LOW_NET,
]
FALLBACKS = [
    slot_subset('Best non-GMO', 'Labeled Non-GMO by the brand.', yes('Non-GMO (Y/N)'),
                lambda b: 'Vegan and labeled Non-GMO.'),
    LOW_SUGAR,
]
PICKS = pick_best10(Q, SLOTS, FALLBACKS)
C.check(len(PICKS) == 10, 'ten Best 10 picks available')
C.check([s.label for s, *_ in PICKS] == [s.label for s in SLOTS], 'all ten planned slots filled without fallbacks')
C.check(not any(re.search(r'score \d|scored? \d', w) for _s, _b, w, _n in PICKS), 'no ingredient score printed in a pick')
PK = {s.label: b for s, b, _w, _n in PICKS}
C.check(not SOY_RX.search(ingr(PK['Best soy-free'])), 'the soy-free pick names no soy ingredient')
C.check(not any(any_a(b) for _s, b, _w, _n in PICKS), 'no Best 10 pick names an animal ingredient')
B10_INTRO = ("Ten vegan bars, each the winner of one thing people shop for. Every pick is labeled vegan, has an A or B "
             "ingredient grade and at least 10g of protein, and no bar appears twice.")

# ---------------------------------------------------------------------------
# What disqualifies a bar (carried over from v1, trimmed)
# ---------------------------------------------------------------------------
UNNAMED = ND - len(NAMED)
DISQ = f'''
    <div class="section-inner">
      <h2 class="section-title">What disqualifies a protein bar from being vegan</h2>
      <div class="section-body">
        <p>We use the Vegan (Y/N) flag on file for every bar, then cross-check ingredient lists ourselves for the {num_word(len(ANIMAL))} animal-derived ingredients below, in order of how often they show up.</p>
        <p>{pct0(ND, NT)}% of the {DB_PUBLIC} bars we track are not marked vegan. Combined, these {num_word(len(ANIMAL))} ingredients show up in {comma(len(NAMED))} of those {comma(ND)} bars ({pct0(len(NAMED), ND)}%). The other {comma(UNNAMED)} don't name any of them: they use a less common animal-derived ingredient or simply aren't confirmed vegan by the brand.</p>
      </div>
      <div class="score-grid" style="margin-top:1.5rem;">
{chr(10).join(v2_count_card_html(l, HIT[l], NT, DESC_A[l]) for l in ORDER)}
      </div>
    </div>
'''

# ---------------------------------------------------------------------------
# Findings: three data findings + one chart
# ---------------------------------------------------------------------------
def count_q(rx): return sum(1 for b in Q if re.search(rx, ingr(b), re.I))
PEA, SOY, RICE = count_q(r'pea protein'), count_q(r'soy protein'), count_q(r'rice protein')
C.check(PEA > max(SOY, RICE), 'pea protein is the most common plant protein')
C.check(sum(1 for b in Q if b['score_band'] in 'AB') / N > sum(1 for b in ALL if b['score_band'] in 'AB') / NT,
        'vegan bars grade A or B more often than the database')
C.check(avg(Q, 'Protein (g)') < avg(ALL, 'Protein (g)'), 'vegan bars average less protein')
BB = [b for b in Q if b['Brand Name'] == 'Barebells']
BB_ALL = by_brand('Barebells')
BB_NV = [b for b in BB_ALL if not QF(b)]
if BB:
    bb_lo, bb_hi = grade_range(BB)
    C.check(BAND_ORDER.index(bb_hi) > BAND_ORDER.index(grade_range(BB_NV)[0]), "Barebells' vegan flavors grade worse than its best non-vegan ones")
INSIGHTS = [
    ('Pea protein is the plant-protein default.',
     f'{PEA} of the {N} vegan bars use pea protein'
     + (f', more than soy protein ({SOY}) and brown rice protein ({RICE}) combined.' if PEA > SOY + RICE else
        f', ahead of brown rice protein ({RICE}) and soy protein ({SOY}).')),
    ('Vegan bars grade better but carry less protein.',
     f"{ab(Q)}% of vegan bars grade A or B, against {ab(ALL)}% database-wide. They average "
     f"{fnum(round(avg(Q, 'Protein (g)'), 1))}g of protein against {fnum(round(avg(ALL, 'Protein (g)'), 1))}g, since whey and "
     'milk protein are easier to pack into a bar than plant protein.'),
]
if BB:
    INSIGHTS.append(('Vegan and clean are different questions.',
                     f"Barebells' {num_word(len(BB))} vegan flavors grade {bb_lo}" + (f' to {bb_hi}' if bb_hi != bb_lo else '')
                     + ", worse than its dairy-based lineup. A vegan label doesn't guarantee a clean ingredient list."))
GRADE_ROWS = [(g, sum(1 for b in Q if b['score_band'] == g), sum(1 for b in ALL if b['score_band'] == g)) for g in BAND_ORDER]
GRV = {g: round(100 * h / t) for g, h, t in GRADE_ROWS}
C.check(GRV['A'] > GRV['F'] and GRV['D'] > GRV['F'] and GRV['C'] > GRV['D'], 'vegan share falls from C down to F and A is above F')
FINDINGS = findings_v2_html(f'What we found screening {DB_PUBLIC} bars', INSIGHTS,
                            grade_share_chart_html(GRADE_ROWS, title='Share of bars labeled vegan, by ingredient grade',
                                                   note=f'Out of the {DB_PUBLIC} bars in our database.'))

# ---------------------------------------------------------------------------
# Brands that do it well + big brands
# ---------------------------------------------------------------------------
WELL = brands_well_rows(ALL, QF, n=8)
C.check(sum(r['big'] for r in WELL) >= 2 and sum(not r['big'] for r in WELL) >= 2, 'brands-well has 2+ big and 2+ small brands')
def well_why(r):
    lead = (f"All {r['total']} flavors are vegan" if r['q'] == r['total'] else
            f"{r['q']} of {r['total']} flavors {'is' if r['q'] == 1 else 'are'} vegan")
    gm = r['grades']
    grades = (f"graded {next(iter(gm))}" if r['q'] == 1 else
              f"all {next(iter(gm))} grade" if len(gm) == 1 else grade_mix_text(gm) + ' grade')
    bp = best_pick(r['qual'])
    return f"{lead}, {grades}. Best pick: {bp['Flavor Name']} ({bp['score_band']}, {fnum(P(bp))}g protein, {fnum(CAL(bp))} cal)."
BRANDS_WELL = brands_well_html(WELL, well_why, h2='Brands that do it well',
                               intro='Brands with at least 3 bars in our database, ranked by how much of their lineup is vegan '
                                     'and how well those bars grade. We made sure to include both brands you can find at most '
                                     'grocery stores and smaller independents.')

# CLIF Bar (Jeff, 2026-09-30): no flavor names an animal ingredient, but Clif doesn't
# call its bars vegan: it calls most of its foods plant-based because they may be
# made in a bakery that uses dairy-based ingredients (Clif's own page, CLIF_URL,
# checked 2026-09-30). Said plainly instead of "not marked vegan in our data".
CLIF_URL = 'https://www.clifbar.com/stories/are-clif-bar-energy-bars-vegan-our-philosophy'
CLIF = by_brand('CLIF Bar')
CLIF_NOTE = (not any(QF(b) for b in CLIF)) and not any(any_a(b) for b in CLIF)
C.check(CLIF_NOTE, 'no CLIF Bar flavor is marked vegan and none names an animal ingredient')
CLIF_WHY = ("none name an animal ingredient, but Clif calls its bars plant-based, not vegan, because they may be made in "
            "a bakery that uses dairy-based ingredients")
def animal_top(disq):
    c = Counter(l for b in disq for l in RX if has_a(b, l))
    return sorted(c.items(), key=lambda kv: (-kv[1], ORDER.index(kv[0])))
def big_verdict(r):
    disq = [b for b in r['bars'] if not QF(b)]
    bp = best_pick(r['qual'])
    pick = f" Best pick: {bp['Flavor Name']} ({bp['score_band']}, {fnum(P(bp))}g protein)." if bp else ''
    low_n = sum(1 for b in r['qual'] if b['score_band'] in ('C', 'D', 'F'))
    low_txt = ('' if low_n * 2 <= r['q'] else
               f" {'All' if low_n == r['q'] else 'Most'} of the vegan ones grade C or below, so check the label.")
    if r['q'] == r['total']:
        return 'Every flavor is vegan.' + (low_txt.replace(' of the vegan ones', '') if low_txt else pick)
    top = animal_top(disq)
    if r['brand'] == 'CLIF Bar' and CLIF_NOTE:
        why = CLIF_WHY
    elif not top:
        why = "none name an animal ingredient, they just aren't marked vegan in our data"
    elif top[0][1] == len(disq):
        why = f'every one has {top[0][0].lower()}'
    else:
        why = f'most have {top[0][0].lower()}' if top[0][1] * 2 > len(disq) else f'{top[0][0].lower()} is the most common reason'
    if r['q'] == 0:
        return f"None are vegan: {why}."
    verb = 'is' if r['q'] == 1 else 'are'
    return (f"{'Only ' if r['q'] * 2 < r['total'] else ''}{r['q']} of {r['total']} {verb} vegan. Of the rest, {why}."
            + (low_txt or pick))
BIG_HTML, BIG_ROWS = big_brands_html(
    ALL, QF, big_verdict, h2='How do the big brands fare on vegan?',
    intro=('Every brand with national grocery, big-box or Costco distribution, with how many of its bars are labeled vegan. '
           'Brand names link to our full reviews where we have one.'))

# ---------------------------------------------------------------------------
# Top 50 + Bar Finder CTA + criteria
# ---------------------------------------------------------------------------
T50 = top50_rows(Q, 50)
TOP50 = top50_html(T50, h2='Top 50 vegan protein bars',
                   intro='Ranked by ingredient grade first, then by protein per calorie. Tap any row for nutrition facts and '
                         'the full ingredient list.')
FINDER = finder_cta_html(N, FINDER_HREF, desc=('The Bar Finder opens with the Vegan filter already on, the same label this '
                                               'guide uses. Add your own filters for protein, sugar, calories, grade, brand, '
                                               'other certifications, or ingredients to exclude.'))
CRITERIA = criteria_html(
    qualify_rule=('The bar is marked vegan (the Vegan field in our database). We also read every ingredient list for whey, milk '
                  'protein, honey, collagen, casein, egg whites and gelatin, to explain why the rest miss. '
                  f'{comma(N)} of the {DB_PUBLIC} bars we track qualify.'),
    picks=PICKS)

# ---------------------------------------------------------------------------
# FAQ (answers may hold links; JSON-LD gets the plain text)
# ---------------------------------------------------------------------------
CONSIDER, MIXED, AVOID = brand_split(ALL, QF)
def brand_rec(name): return next((r for r in CONSIDER + MIXED + AVOID if r['brand'] == name), None)
LARA, GOM = brand_rec('Larabar'), brand_rec('GoMacro')
C.check(LARA and LARA['d'] == 0 and GOM and GOM['d'] == 0, 'Larabar and GoMacro are fully vegan')
C.check(sum(1 for b in GOM['bars'] if re.search(r'rice protein|pea protein', ingr(b), re.I)) >= 0.8 * GOM['total'], 'most GoMacro flavors use brown rice or pea protein')
SPLIT_EX = min((r for r in CONSIDER + MIXED + AVOID if r['q'] and r['d'] and r['total'] >= 10),
               key=lambda r: (abs(r['q'] / r['total'] - 0.5), -r['total'], r['brand']))
BEST = PK['Best overall']
FAQS = [
    ('What makes a protein bar vegan on this site?',
     'We use the Vegan (Y/N) flag on file for each bar and cross-check the full ingredient list for animal-derived ingredients, '
     'not just a package claim. That means no whey, milk protein, honey, egg whites, collagen peptides, casein, or gelatin '
     'anywhere in the formula.'),
    ('What is the best vegan protein bar?',
     f"By our rules, {full(BEST)}: {BEST['score_band']}-grade ingredients, {fnum(P(BEST))}g protein and {fnum(CAL(BEST))} "
     f"calories. For the most protein, {full(PK['Highest protein'])} has {fnum(P(PK['Highest protein']))}g. Every bar in our "
     "Best 10 is vegan with an A or B grade."),
    ('How many vegan protein bars are in your database?',
     f"{of_db(N, NT, True)} bars we track are vegan, spanning {BRANDS_Q} brands. {GR['A']} of those {N} bars grade A for ingredient quality."),
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
    ('Are CLIF Bars vegan?',
     f"Not by our screen. None of the {len(CLIF)} CLIF Bar flavors we track name an animal ingredient, but Clif calls its "
     "bars plant-based rather than vegan, because they may be made in a bakery that uses dairy-based ingredients "
     f'(<a href="{CLIF_URL}" target="_blank" rel="noopener">Clif explains its position here</a>). We only count a bar as '
     "vegan when it's marked vegan, so CLIF Bar isn't on this list."),
    ('What is the most common non-vegan ingredient in protein bars?',
     f"Whey protein. It shows up in {of_db(len(HIT['Whey protein']), NT, True)} bars we track, more than milk protein, honey, "
     'collagen, casein, egg whites, and gelatin individually. It is the default protein source for most mainstream bars.'),
    ('Is honey vegan?',
     'No. Honey is produced by bees, not a plant, so any bar listing honey as an ingredient does not qualify as vegan on this '
     'site, even if every other ingredient is plant-based.'),
    ("Can a brand have some vegan flavors and some that aren't?",
     f"Yes, and it is common. {SPLIT_EX['brand']} splits closest to even of any large lineup we checked: {SPLIT_EX['q']} of "
     f"{SPLIT_EX['total']} flavors are vegan. Always check the specific flavor, not just the brand."),
    ('What protein bars are vegan?',
     f'{N} bars across {BRANDS_Q} brands clear our vegan screen, led by whole-food brands like Larabar and GoMacro that '
     'qualify 100% of the time. Our Best 10 picks are at the top of this page, the Top 50 is further down, and the Bar '
     'Finder has all of them.'),
    ('Are vegan protein bars lower quality than whey-based bars?',
     f"No. {ab(Q)}% of vegan bars in our database grade A or B, against {ab(ALL)}% database-wide. What they give up on average "
     f"is protein: vegan bars average {fnum(round(avg(Q, 'Protein (g)'), 1))}g against a database-wide average of "
     f"{fnum(round(avg(ALL, 'Protein (g)'), 1))}g, since whey and milk protein are easier to pack into a bar than plant protein."),
    ('How often is this list updated?',
     'We update the database whenever new bars are added or a brand reformulates. Manufacturers do change their ingredient '
     'lists over time, so always confirm against the packaging in front of you.'),
]

# ---------------------------------------------------------------------------
# Regions
# ---------------------------------------------------------------------------
H1 = 'The 10 Best Vegan Protein Bars'
TITLE = f'10 Best Vegan Protein Bars ({DB_PUBLIC} Checked)'
DESC = (f"{pct0(ND, NT)}% of protein bars aren't vegan. We checked {DB_PUBLIC} for whey, milk, honey, egg and gelatin and "
        f"picked the 10 best of the {comma(N)} that are.")
OG_DESC = (f'{comma(N)} vegan protein bars with no whey, milk, honey, egg, or gelatin. Here are the 10 best, each picked by a '
           'published rule.')
C.check(len(DESC) <= 155, f'meta description under 155 characters ({len(DESC)})')
FAQS_PLAIN = [(q, plain_text(a)) for q, a in FAQS]
REGIONS = v2_head_regions(title=TITLE, h1=H1, desc=DESC, og_desc=OG_DESC, url=URL, about='Vegan Protein Bars',
                          published=PUBLISHED, faqs=FAQS_PLAIN, picks=PICKS)
EDITORIAL = f'  <section class="section off" id="what-disqualifies">{DISQ}  </section>'
HERO = (f'<h1 class="hero-title">{esc(H1)}</h1>\n'
        f'    <p class="hero-sub">A vegan protein bar has no animal ingredients at all: no whey, milk, honey, eggs, collagen, '
        f'casein or gelatin. Most mainstream bars are built on whey or milk protein, so going vegan usually means pea, rice or '
        f'soy protein instead. We use the vegan label on every bar, then read the ingredient list ourselves.</p>\n'
        f'    <p class="hero-sub">Of the {DB_PUBLIC} bars we track, {comma(N)} are vegan, about {pct0(N, NT)}%. They grade A or B '
        f'more often than the average bar ({ab(Q)}% vs. {ab(ALL)}%), but carry less protein on average.</p>')
REGIONS += [
    ('hero', HERO),
    ('best10', best10_html(PICKS, h2='Best 10 vegan protein bars', intro=B10_INTRO)),
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
        ('/gluten-free-protein-bars', 'Gluten Free Protein Bars', 'Bars labeled gluten free, checked against the ingredient list.'),
        ('/dairy-free-protein-bars', 'Dairy Free Protein Bars', 'Bars with no whey, milk protein, or other dairy.'),
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
