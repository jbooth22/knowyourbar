#!/usr/bin/env python3
"""
Rebuild the data on clif-bar-review.html from live bars.js.

    python3 build_clif_bar_review.py

Opens the live page and rewrites only the <!-- kyb:NAME --> regions (see
kyb_guide_lib.py / kyb_brand_lib.py). Nav, footer, fonts, canonical URL, the
Explore CTA and the brand-link pills are never touched.

Clif is three Brand Name values in bars.js: Clif Builders, CLIF Bar and
Clif ZBar. The flavor table is grouped by line because two flavor names
(Vanilla Almond, Chocolate Chip) exist in more than one line.

Amazon links: any ASIN that bars.js assigns to more than one bar is not
linked on this page (block_shared_asins), because it can't be trusted to
land on the right flavor. Brand-site links are used instead.

Structural claims go through claims.check(); the build stops if one fails.
"""
from kyb_brand_lib import *

PAGE = 'clif-bar-review.html'
URL = 'https://knowyourbar.com/clif-bar-review'
LINES = ['Clif Builders', 'CLIF Bar', 'Clif ZBar']
COMPARE = ['Quest', 'RXBAR', 'Barebells', 'KIND']
OTHER_REVIEWS = ['Barebells', 'Quest', 'RXBAR', 'KIND']

ALL = load_bars()
BLOCKED = block_shared_asins(ALL)
LB = {n: sort_for_list([b for b in ALL if b['Brand Name'] == n]) for n in LINES}
BU, CB, ZB = LB['Clif Builders'], LB['CLIF Bar'], LB['Clif ZBar']
FAM = sort_for_list(BU + CB + ZB)
N = len(FAM)
C = Claims()
for n in LINES:
    C.check(len(LB[n]) > 0, f'{n} exists in bars.js')
def line(b): return b['Brand Name']
def full(b): return f"{line(b)} {nm(b)}"
def lab(b): return f"{line(b)} &middot; {nm(b)}"

MACRO_GRID, ST = macro_grid_html(FAM, ALL)
PRO, SUGS, NCS = ST['protein'], ST['sugar'], ST['nc']
BEST, WORST = FAM[0], FAM[-1]
GR = range_words(FAM)
best_g, worst_g = grade_range(FAM)
def gs(bars): return grade_range(bars)
def pavg(bars): return avg(bars, 'Protein (g)')
def spread(bars): return max(map(score, bars)) - min(map(score, bars))
def cnt(bars, g): return sum(1 for b in bars if b['score_band'] == g)
C.check(no_as_sa(FAM), 'no Clif flavor has artificial sweeteners or sugar alcohols')
C.check(pavg(BU) > pavg(CB) > pavg(ZB), 'protein runs Builders > CLIF Bar > ZBar')
C.check(best_g in {b['score_band'] for b in BU} and gs(CB)[0] not in ('A', 'B') and gs(ZB)[0] not in ('A', 'B', 'C'),
        'only Builders reaches the top grade; CLIF Bar tops out at C or lower; ZBar tops out at D or lower')
BU_TOP = [b for b in BU if b['score_band'] == best_g]
BU_F = [b for b in BU if b['score_band'] == 'F']
FAM_F = [b for b in FAM if b['score_band'] == 'F']
SUGAR3 = ('cane syrup', 'cane sugar', 'brown rice syrup')
def three_sugars(b): return all(has_ing(b, s) for s in SUGAR3)
def protein_first(b): return ingr(b).lower().startswith('soy protein isolate')
C.check(all(three_sugars(b) and protein_first(b) for b in BU_F), 'every F-grade Builders flavor leads with soy protein isolate and stacks cane syrup, cane sugar and brown rice syrup')
C.check(all(protein_first(b) and has_ing(b, 'whey protein concentrate') and not three_sugars(b) for b in BU_TOP),
        'the top Builders flavors lead with soy protein isolate and whey protein concentrate without the three-sugar stack')
C.check(all(ingr(b).lower().startswith(('organic rolled oats', 'rolled oats')) for b in CB), 'every CLIF Bar flavor leads with rolled oats')
C.check(all(has_ing(b, 'brown rice syrup') for b in CB), 'every CLIF Bar flavor has brown rice syrup')
reviewed_spreads = {n: spread([b for b in ALL if b['Brand Name'] == n]) for n in OTHER_REVIEWS}
widest = spread(BU) > max(reviewed_spreads.values())

# ---------------------------------------------------------------------------
# Line comparison
# ---------------------------------------------------------------------------
def line_row(n, bars):
    return compare_row_html(n, bars, True)
LINES_NOTE = []
LINES_NOTE.append(f"Clif Builders is the only line that reaches {best_g}, with {num_word(len(BU_TOP))} {best_g}-grade flavor{'s' if len(BU_TOP) != 1 else ''}"
                  + (f", but it also carries {len(BU_F)} of the family's {len(FAM_F)} F grades." if BU_F else '.'))
LINES_NOTE.append(f"CLIF Bar is more consistent ({range_words(CB)}) and Clif ZBar sits at the bottom ({range_words(ZB)}).")
LINES_NOTE.append("None of the three lines use artificial sweeteners or sugar alcohols in any flavor.")
LINES_HTML = f'''<h2 class="brand-compare-title">How the three Clif lines compare to each other</h2>
      <div class="brand-compare-sub">All figures are per-line averages across every flavor we've scored in that line, and grade ranges show the full spread from that line's best flavor to its worst.</div>
      <div class="brand-compare-table-wrap">
        <table class="brand-compare-table">
          <thead>
            <tr><th>Line</th><th class="ctr">Grade range</th><th class="ctr" title="Protein per 100 calories">Protein/100cal</th><th class="ctr col-hide-mobile">Fiber avg</th><th class="ctr col-hide-mobile">Sugar avg</th><th>Sweetener</th></tr>
          </thead>
          <tbody>
{chr(10).join(line_row(n, LB[n]) for n in LINES)}
          </tbody>
        </table>
      </div>
      <div class="brand-compare-note">
        <div class="brand-compare-note-text">{esc(' '.join(LINES_NOTE))}</div>
      </div>'''

# ---------------------------------------------------------------------------
# Picks
# ---------------------------------------------------------------------------
top = BEST
safe = min([b for b in FAM if amazon_url(b)], key=lambda b: (band_rank(b), -(score(b) or 0), full(b)))
cb_top = CB[0]
MAXP = max(map(P, FAM))
maxp_worst = min([b for b in FAM if P(b) == MAXP], key=lambda b: (score(b), full(b)))
n_maxp = sum(1 for b in FAM if P(b) == MAXP)
tiles = []
t_top = (f"Score {g1(score(top))}, grade {top['score_band']}. Leads with soy protein isolate and whey protein concentrate before any sweetener shows up.")
if not amazon_url(top) and top.get('Amazon Affiliate'):
    t_top += (" Its Amazon listing is shared with a different flavor in our data, so buy this one through the Clif site link, not Amazon.")
tiles.append(brand_pick_tile('Best overall ingredient quality', [top], t_top, names=[full(top)]))
if safe is not top:
    t_safe = (f"Score {g1(score(safe))}, grade {safe['score_band']}"
              + (f", right behind the top flavor" if safe['score_band'] == top['score_band'] else '')
              + f": {fnum(CAL(safe))} calories and {fnum(FIB(safe))}g fiber versus {fnum(CAL(top))} calories and {fnum(FIB(top))}g fiber. "
              "Its Amazon listing isn't shared with any other flavor, so the Amazon link is safe to use.")
    tiles.append(brand_pick_tile('Best pick you can safely buy on Amazon', [safe], t_safe, names=[full(safe)]))
cb_fib_max = FIB(cb_top) == max(map(FIB, CB))
t_cb = (f"Score {g1(score(cb_top))}, the top flavor in the CLIF Bar line, which tops out at grade {gs(CB)[0]}. {fnum(P(cb_top))}g protein and "
        f"{fnum(FIB(cb_top))}g fiber" + (", tied for the most fiber in the CLIF Bar line." if cb_fib_max else '.'))
tiles.append(brand_pick_tile('Best classic CLIF Bar (lower protein, energy-bar style)', [cb_top], t_cb, names=[full(cb_top)]))
t_mp = (f"{fnum(MAXP)}g protein, tied with {num_word(n_maxp - 1)} other flavors for the most of any Clif flavor. It's also among the family's "
        f"lowest-scoring flavors at {g1(score(maxp_worst))}, grade {maxp_worst['score_band']}"
        + (": right behind the soy protein isolate come three sugar sources (cane syrup, cane sugar, brown rice syrup) and palm kernel oil."
           if three_sugars(maxp_worst) and has_ing(maxp_worst, 'palm kernel oil') else '.'))
tiles.append(brand_pick_tile("Highest protein in the family isn't the safest pick", [maxp_worst], t_mp, buy=False, names=[full(maxp_worst)]))
zb_g = sorted({b['score_band'] for b in ZB}, key=BAND_ORDER.index)
t_zb = (f"ZBar is marketed as Clif Kid ZBar, a children's snack bar, not an adult protein bar. It averages just {g1(pavg(ZB))}g protein per bar, "
        f"and all {num_word(len(ZB))} flavors grade {' or '.join(zb_g)}.")
tiles.append(brand_pick_tile('Skip Clif Kid ZBar for protein-bar purposes', [], t_zb, buy=False,
                             names=[f'{full(cb_top)} or Clif Builders flavors instead']))

# ---------------------------------------------------------------------------
# Alternatives keyed to the safe-to-buy pick
# ---------------------------------------------------------------------------
FLAG = safe
FB = band_rank(FLAG)
KEY = 'almond' if 'almond' in nm(FLAG).lower() else nm(FLAG).lower().split()[-1]
def noart(b): return not has_tag(b, 'Artificial Sweeteners') and sa(b) == 0
ALTS = pick_alternatives(ALL, FLAG, set(LINES), KEY, [
    (lambda b: 'More protein, fewer calories' if CAL(b) < CAL(FLAG) else 'More protein',
     lambda b: band_rank(b) < FB and noart(b) and P(b) >= P(FLAG) + 6,
     lambda b: (-P(b), CAL(b)),
     lambda b: f"{fnum(P(b))}g protein vs. {fnum(P(FLAG))}g here, for {cal_delta(FLAG, b)}. {grade_vs(FLAG, b)}"),
    ('Better quality, more protein',
     lambda b: band_rank(b) < FB and noart(b) and P(b) > P(FLAG),
     lambda b: (band_rank(b), CAL(b), -P(b)),
     lambda b: f"{fnum(P(b))}g protein vs. {fnum(P(FLAG))}g here, for {cal_delta(FLAG, b)}. {grade_vs(FLAG, b)}"),
    ('Fewest calories',
     lambda b: band_rank(b) < FB and noart(b) and P(b) >= 10 and CAL(b) < CAL(FLAG),
     lambda b: (CAL(b), -P(b)),
     lambda b: (f"Only {fnum(CAL(b))} calories, {fnum(CAL(FLAG) - CAL(b))} fewer than here. {grade_vs(FLAG, b)}"
                + (f" Protein drops to {fnum(P(b))}g from {fnum(P(FLAG))}g, a real tradeoff for the lighter bar." if P(b) < P(FLAG) else ''))),
], cal_window=60)
ALTS_HTML = f'''<h2>Like {esc(nm(FLAG))}? These are worth a look too</h2>
    <p>This is the Clif Builders flavor with a working Amazon link, but it's still only {'an' if FLAG['score_band'] in 'AF' else 'a'} {FLAG['score_band']}. {num_word(len(ALTS)).capitalize()} ways to trade up depending on what matters most to you, all with no artificial sweeteners or sugar alcohol.</p>
    <div class="macro-grid pick-tile-grid">
{chr(10).join(alt_tile(*a) for a in ALTS)}
    </div>'''
C.check(line(FLAG) == 'Clif Builders', 'the safe-to-buy pick is a Clif Builders flavor')

# ---------------------------------------------------------------------------
# Brand comparison (Clif Builders vs other brands)
# ---------------------------------------------------------------------------
GROUPS = [('Clif Builders', BU)] + [(n, [b for b in ALL if b['Brand Name'] == n]) for n in COMPARE]
for n, gg in GROUPS:
    C.check(len(gg) > 0, f'{n} exists in bars.js for the comparison table')
cnote = compare_note('Clif Builders', GROUPS)
cnote.append("CLIF Bar and Clif ZBar don't compete with any of these brands on protein per calorie; see the line comparison above.")
COMPARE_HTML = compare_section_html('Clif Builders', GROUPS, cnote).replace(
    "grade ranges show the full spread from that brand's best flavor to its worst.</div>",
    "grade ranges show the full spread from that brand's best flavor to its worst. CLIF Bar and Clif ZBar are shown separately above since they're different product lines, not competing protein bars.</div>")

counts = {n: len([b for b in ALL if b['Brand Name'] == n]) for n in ('Barebells', 'Quest')}
RELATED = f'''
        <a href="/barebells-review" class="explore-more-card">
          <div class="explore-more-title">Full Barebells Review</div>
          <div class="explore-more-desc">All {counts['Barebells']} flavors scored with full ingredient breakdowns and macro data.</div>
        </a>
        <a href="/quest-bars" class="explore-more-card">
          <div class="explore-more-title">Full Quest Review</div>
          <div class="explore-more-desc">All {counts['Quest']} flavors scored with full ingredient breakdowns and macro data.</div>
        </a>
        <a href="/low-sugar-high-protein" class="explore-more-card">
          <div class="explore-more-title">Low Sugar + High Protein Bars</div>
          <div class="explore-more-desc">Bars ranked for the best protein-to-sugar ratio across our full database.</div>
        </a>
      '''

# ---------------------------------------------------------------------------
# Copy
# ---------------------------------------------------------------------------
H1_TEXT = f'Are Clif Bars Healthy? We Ranked All {N} Flavors Across 3 Product Lines'
H1_HTML = f'Are <em>Clif</em> Bars Healthy? We Ranked All {N} Flavors Across 3 Product Lines'
TITLE = f'Are Clif Bars Healthy? {N} Flavors Across 3 Lines Ranked | Know Your Bar'
OG_TITLE = f'Are Clif Bars Healthy? {N} Flavors Across 3 Lines Ranked'
DESC = (f"Clif Builders swings {range_words(BU)}, CLIF Bar tops out at {gs(CB)[0]}, and Kid ZBar never breaks {gs(ZB)[0]}. "
        f"We scored all {N} Clif flavors by ingredient quality.")
OG_DESC = (f"Clif is 3 different product lines under one name. We scored all {N} flavors across CLIF Bar, Builders, and Kid ZBar by ingredient quality.")
ART_DESC = (f"Clif protein bars scored A to F by ingredient quality across all {N} flavors spanning CLIF Bar, Clif Builders, and Clif ZBar. "
            "Full macro breakdown, grade distribution, and best vs. worst flavor callouts.")
C.check(len(DESC) <= 155, f'meta description length {len(DESC)}')

HERO_SUB = (f"Clif isn't one bar, it's three separate product lines wearing the same name. Clif Builders is the actual protein bar and ranges "
            f"from grade {gs(BU)[0]} to {gs(BU)[1]} depending on flavor. CLIF Bar is a lower-protein energy bar that never breaks {gs(CB)[0]}, "
            f"and Clif Kid ZBar is a children's snack bar that never breaks {gs(ZB)[0]}.")

MACRO = f'''<h2>How Clif ranks on macros</h2>
    <p>Rather than labeling macros good or bad, we rank Clif against every bar in our database so you can see where they stand in the full market. These figures are averaged across all {N} flavors from all three Clif lines; see the line-by-line breakdown below for how CLIF Bar, Clif Builders, and Clif ZBar differ from each other.</p>
{MACRO_GRID}
    <p class="macro-summary-text">{esc(f"Averaged across all three lines, Clif runs {g1(PRO['avg'])}g of protein and {g1(SUGS['avg'])}g of sugar per bar, numbers pulled down by CLIF Bar and Clif ZBar. Judged on Clif Builders alone, the picture is very different: {g1(pavg(BU))}g protein average, with the family's only {best_g}-grade flavors.")}</p>'''

ov1 = (f"Clif sells three distinctly different bars under one brand name, and they don't perform anywhere near the same. Clif Builders averages "
       f"{g1(pavg(BU))}g of protein per bar, {fnum(round(pavg(BU) - pavg(CB)))}g more per serving than CLIF Bar's average of {g1(pavg(CB))}g and "
       f"nearly {fnum(round(pavg(BU) / pavg(ZB)))} times Clif ZBar's {g1(pavg(ZB))}g. Only Builders is really built as a protein bar. CLIF Bar is "
       "closer to a classic energy bar, and Clif ZBar is marketed as Clif Kid ZBar, a children's snack, not an adult protein product.")
ov2 = (f"Ingredient quality tracks the same split. Clif Builders holds the only {best_g} grades in the entire family, {names_and(nm(b) for b in BU_TOP)}, "
       "and both lead with soy protein isolate and whey protein concentrate without the heavy sugar stack. "
       + (f"The rest of the Builders line falls off a cliff: its {num_word(len(BU_F))} F-grade flavors put three separate sugar sources, cane syrup, "
          "cane sugar, and brown rice syrup, right behind the protein, plus palm kernel oil. " if BU_F else '')
       + f"CLIF Bar never reaches that low, but it never reaches higher than a {gs(CB)[0]} either, topping out with {nm(cb_top)} at a modest "
       f"{g1(score(cb_top))} score. None of the {N} flavors across any line use artificial sweeteners or sugar alcohols.")
C.check(len(BU_TOP) == 2, 'Builders has exactly two top-grade flavors (copy says "both")')
OVERVIEW = f'''<h2>What the data shows across all {N} Clif flavors</h2>
    <p>{esc(ov1)}</p>
    <p>{esc(ov2)}</p>'''

GRADES = f'''<h2>Ingredient quality grade distribution across all {N} flavors</h2>
    <p>Here is how Clif's full lineup, all three lines combined, grades out. This is every flavor we've scored, not a hand-picked few.</p>
{grade_dist_html(FAM)}'''

BESTWORST = f'''<h2>Best and worst flavors by ingredient quality</h2>
    <div class="bestworst">
{bw_card_html(BEST, True, prefix=line(BEST))}
{bw_card_html(WORST, False, prefix=line(WORST))}
    </div>'''

PL = [b for b in FAM if has_tag(b, 'Protein Leads')]
SH_ALL = sum(1 for b in FAM if has_tag(b, 'Sweetener Heavy'))
PO_ALL = sum(1 for b in FAM if has_tag(b, 'Processed Oils'))
pl_bu = sum(1 for b in PL if line(b) == 'Clif Builders')
PATTERNS = f'''<h2>Ingredient quality patterns across the Clif lineup</h2>
    <p>{esc(f"These patterns hold across all {N} flavors from all three lines combined. Every single Clif flavor gets credit for a quality protein source, but that's true broadly across the category. " + (f"Protein Leads, meaning protein shows up before sweeteners in the ingredient list, happens in {len(PL)} of {N} flavors, " + ("every one of them a Clif Builders flavor." if pl_bu == len(PL) else f"{pl_bu} of them in Clif Builders.") if PL else ''))}</p>

{chip_patterns_html(FAM)}

    <p style="margin-top:1.25rem;">{esc(f"{SH_ALL} of {N} flavors carry the Sweetener Heavy concern, and {PO_ALL} of {N} carry Processed Oils. Both show up in all three lines. In CLIF Bar and Clif ZBar, sweeteners appear before any protein source; in Clif Builders, protein leads, but the F-grade flavors stack three sugars right behind it.")}</p>'''
C.check(all(sum(1 for b in LB[n] if has_tag(b, 'Sweetener Heavy')) and sum(1 for b in LB[n] if has_tag(b, 'Processed Oils')) for n in LINES),
        'Sweetener Heavy and Processed Oils appear in all three lines')
C.check(not any(has_tag(b, 'Protein Leads') for b in CB + ZB), 'CLIF Bar and ZBar never get Protein Leads')

TABLE_ROWS, ORDER = brand_table_grouped_html([(f'{n}, {len(LB[n])} flavors', LB[n]) for n in LINES], ALL)
TABLE_HEADING = f'''<h2>All {N} Clif flavors ranked by ingredient quality</h2>
    <p>Every flavor, every grade, every key macro, grouped by line: Clif Builders, then CLIF Bar, then Clif ZBar. Sorted from cleanest to most processed within each line. Tap any row to see the full ingredient list, macros, and buy links.</p>'''

bl1 = (f"Clif isn't one product to judge, it's three. Clif Builders is the only line worth buying for a genuine protein bar, and even then only "
       f"{num_word(len(BU_TOP))} of its {len(BU)} flavors grade {best_g}: those lead with soy and whey protein without the heavy sugar stack, while its "
       f"{num_word(len(BU_F))} F-grade flavors pile three sugar sources in right behind the protein. CLIF Bar is a middling energy bar, never bad "
       f"enough to avoid outright but never good enough to recommend over a dedicated protein bar. Clif ZBar isn't really part of this conversation at "
       "all, it's a kids' snack bar sold under the Clif name, and by ingredient quality it's the weakest of the three lines.")
bl2 = ("If you're shopping the Clif lineup specifically for a protein bar, go straight to Clif Builders and check the flavor before you buy"
       + (", since the gap between its best and worst flavor is the widest of any brand we've reviewed." if widest else
          f", since its flavors run all the way from {gs(BU)[0]} to {gs(BU)[1]}.")
       + " Don't assume \"Clif\" on the label means the bar you're holding is anything like the others.")
BOTTOM = f'''<h2>Bottom line</h2>
    <p>{esc(bl1)}</p>
    <p>{esc(bl2)}</p>'''
C.check(gs(ZB)[1] == worst_g or band_rank(min(ZB, key=band_rank)) >= band_rank(min(CB, key=band_rank)), 'ZBar is the weakest line')

PICKS = f'''<h2>Which Clif flavor should you actually buy</h2>
    <p>These are situational picks grounded in the real per-flavor data above, not a repeat of the best/worst cards.</p>
    <div class="macro-grid pick-tile-grid">
{chr(10).join(tiles)}
    </div>'''

bu_prange = f"{fnum(min(map(P, BU)))}-{fnum(max(map(P, BU)))}g"
cb_prange = f"{fnum(min(map(P, CB)))}-{fnum(max(map(P, CB)))}g"
skip3 = sorted(BU_F, key=lambda b: (score(b), nm(b)))[:3]
cmp_line = sorted(GROUPS, key=lambda g: -p100avg(g[1]))
ahead = [n for n, g in cmp_line if p100avg(g) < p100avg(BU) and n != 'Clif Builders']
behind = [n for n, g in cmp_line if p100avg(g) > p100avg(BU)]
FAQS = [
    ('Are Clif bars healthy?',
     f"It depends entirely on which Clif line you mean. Across all {N} flavors we scored, grades run from {best_g} down to {worst_g}. Clif Builders has "
     f"the only {best_g}-grade flavors" + (f" but also {len(BU_F)} of the family's {len(FAM_F)} F grades" if BU_F else '') + f". CLIF Bar never scores "
     f"worse than {gs(CB)[1]} but also never scores better than {gs(CB)[0]}. Clif ZBar, marketed as Clif Kid ZBar, never breaks {gs(ZB)[0]} across its "
     f"{len(ZB)} flavors."),
    ('Which Clif flavor is the healthiest?',
     f"Clif Builders {nm(BU_TOP[0])} scores highest at {g1(score(BU_TOP[0]))}, grade {BU_TOP[0]['score_band']}"
     + (f", with Builders {nm(BU_TOP[1])} close behind at {g1(score(BU_TOP[1]))}. Both lead their ingredient lists with soy protein isolate and whey protein concentrate." if len(BU_TOP) > 1 else '.')),
    ('How much protein do Clif bars have?',
     f"Protein varies enormously by line. Clif Builders averages {g1(pavg(BU))}g per bar (range {bu_prange}), CLIF Bar averages {g1(pavg(CB))}g "
     f"(range {cb_prange}), and Clif ZBar averages just {g1(pavg(ZB))}g per bar. Across all three lines combined, the average is {g1(PRO['avg'])}g."),
    ('Do Clif bars have artificial sweeteners?',
     f"No. None of the {N} Clif flavors we scored across CLIF Bar, Clif Builders, or Clif ZBar use artificial sweeteners."),
    ('Do Clif bars have sugar alcohols?',
     f"No. None of the {N} Clif flavors across any of the three lines use sugar alcohols like maltitol or erythritol."),
    ('How do Clif bars compare to other protein bars?',
     f"Clif Builders averages {g1(p100avg(BU))}g of protein per 100 calories"
     + (f", ahead of {names_and(f'{n} ({g1(p100avg(g))}g)' for n, g in cmp_line if n in ahead)}" if ahead else '')
     + (f" but behind {names_and(f'{n} ({g1(p100avg(g))}g)' for n, g in cmp_line if n in behind)}" if behind else '')
     + f". CLIF Bar and Clif ZBar fall further behind at {g1(p100avg(CB))}g and {g1(p100avg(ZB))}g per 100 calories."),
    ('What type of protein is in Clif bars?',
     "Clif Builders and CLIF Bar are built on soy protein isolate, and Builders' top-graded flavors add whey protein concentrate. Clif ZBar uses "
     "whey protein concentrate instead. The bigger difference is where the protein sits in the ingredient list. Clif Builders puts soy protein "
     "isolate first in every flavor. CLIF Bar leads with rolled oats and brown rice syrup, and Clif ZBar with tapioca syrup, both ahead of the protein source."),
    ("What's the difference between CLIF Bar, Clif Builders, and Clif ZBar?",
     f"They're three separate product lines with different positioning. Clif Builders is the protein bar, averaging {g1(pavg(BU))}g of protein per "
     f"bar. CLIF Bar is Clif's original energy bar, lower in protein and never graded above {gs(CB)[0]}. Clif ZBar, sold as Clif Kid ZBar, is a "
     f"children's snack bar averaging just {fnum(round(pavg(ZB)))}g of protein and never grading above {gs(ZB)[0]}. bars.js lists them as three distinct "
     "Brand Name values, not flavors of one product."),
    ('Which Clif flavors should I avoid?',
     f"Skip Clif Builders {names_and(nm(b) for b in skip3)}, all grade F. All three pile cane syrup, cane sugar, and brown rice syrup in right "
     f"behind the soy protein isolate, plus palm kernel oil. None of the {num_word(len(ZB))} Clif ZBar flavors score better than {gs(ZB)[0]}, so if "
     "ingredient quality matters to you, that whole line is worth skipping regardless of flavor."),
]
C.check(all(has_ing(b, 'soy protein isolate') for b in BU + CB) and all(has_ing(b, 'whey protein concentrate') for b in BU_TOP + ZB)
        and not any(has_ing(b, 'soy protein isolate') for b in ZB),
        'soy protein isolate in Builders and CLIF Bar; whey protein concentrate in Builders top flavors and ZBar')
C.check(all(ingr(b).lower().startswith(('tapioca syrup', 'organic tapioca syrup')) for b in ZB), 'ZBar leads with tapioca syrup')
C.check(len(skip3) == 3 and all(has_ing(b, 'palm kernel oil') for b in skip3), 'three F-grade Builders flavors with palm kernel oil')

bw_lookup = {f"{esc(line(b))} &middot; {esc(nm(b))}": b for b in FAM}
regions = [
    ('head-meta', head_meta_html(TITLE, DESC)),
    ('jsonld-article', article_jsonld(H1_TEXT, ART_DESC, URL, 'Clif Bar & Company', 'https://www.clifbar.com', published='2026-08-13')),
    ('jsonld-faq', faq_jsonld_brand(FAQS)),
    ('social', social_html(OG_TITLE, OG_DESC, URL)),
    ('hero', f'<h1 class="hero-title">{H1_HTML}</h1>\n    <p class="hero-sub">{esc(HERO_SUB)}</p>'),
    ('macro', MACRO), ('overview', OVERVIEW), ('lines', LINES_HTML), ('grades', GRADES), ('bestworst', BESTWORST), ('patterns', PATTERNS),
    ('table-heading', TABLE_HEADING), ('table-rows', TABLE_ROWS), ('bottom', BOTTOM), ('picks', PICKS),
    ('alts', ALTS_HTML), ('related', RELATED), ('compare', COMPARE_HTML), ('faq', faq_items_brand(FAQS)),
]
n_rows = build_brand_page(PAGE, regions, FAM, ALL, C, expected=ORDER, bw_lookup=bw_lookup)
print(f'{PAGE}: {N} flavors, family grades {GR} ({grade_counts_txt(FAM, " ")})')
for n in LINES:
    print(f'   {n}: {len(LB[n])} flavors, {range_words(LB[n])} ({grade_counts_txt(LB[n], " ")})')
print(f'Best {full(BEST)} {g1(score(BEST))} | Worst {full(WORST)} {g1(score(WORST))}')
print('Picks:', full(top), '|', full(safe), '|', full(cb_top), '| protein trap', full(maxp_worst))
print('Alternatives:', ' | '.join(f"{a[0]}: {a[1]['Brand Name']} {a[1]['Flavor Name']} ({a[1]['score_band']})" for a in ALTS))
print(f'Shared Amazon ASINs not linked on this page: {sum(1 for b in FAM if b.get("Amazon Affiliate") and not amazon_url(b))} Clif flavors')
print(f'Grade-sync: {n_rows} flavor rows (in line order), best/worst cards and alternative tiles checked against bars.js, 0 mismatches')
