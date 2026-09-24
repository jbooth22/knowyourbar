#!/usr/bin/env python3
"""
Rebuild the data on barebells-review.html from live bars.js.

    python3 build_barebells_review.py

Opens the live page and rewrites only the <!-- kyb:NAME --> regions (see
kyb_guide_lib.py / kyb_brand_lib.py). Nav, footer, fonts, canonical URL, the
Discover CTA buttons and the brand-link pills are never touched.

Every number, grade and flavor name comes from bars.js. Copy that depends on
the data is written as templates, and any sentence that makes a structural
claim (e.g. "all four vegan flavors grade D or F") is either generated from
the data or guarded by check(): if a future bars.js update makes a claim
false, the build stops and names the claim instead of publishing it.

"Lines": Barebells doesn't split into sub-brands in bars.js. The dairy line
is every flavor with Vegan (Y/N) != Yes, the vegan line is Vegan (Y/N) = Yes.
"""
import re, sys, json
from kyb_brand_lib import *

PAGE = 'barebells-review.html'
BRAND = 'Barebells'
URL = 'https://knowyourbar.com/barebells-review'
COMPARE = ['Quest', 'RXBAR', 'Clif Builders', 'KIND']   # brand-compare table rows after Barebells

ALL = load_bars()
BB = sort_for_list([b for b in ALL if b['Brand Name'] == BRAND])
N = len(BB)
VEG = [b for b in BB if b.get('Vegan (Y/N)') == 'Yes']
DAI = [b for b in BB if b not in VEG]

PROBLEMS = []
def check(ok, claim):
    if not ok:
        PROBLEMS.append(claim)
    return ok

def P(b): return num(b.get('Protein (g)')) or 0
def CAL(b): return num(b.get('Calories')) or 0
def FIB(b): return num(b.get('Dietary Fiber (g)')) or 0
def g1(x): return f'{x:.1f}'
def nm(b): return b['Flavor Name']
def names_and(xs):
    xs = list(xs)
    return xs[0] if len(xs) == 1 else ', '.join(xs[:-1]) + (',' if len(xs) > 2 else '') + ' and ' + xs[-1]
def num_word(n):
    words = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve',
             'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen', 'twenty']
    return words[n] if n < len(words) else str(n)
def has(b, word): return word in ingr(b).lower()
def stacks(b): return has(b, 'maltitol syrup')   # second sugar-alcohol source on top of maltitol

# ---------------------------------------------------------------------------
# Facts
# ---------------------------------------------------------------------------
MACRO_HTML, ST = macro_grid_html(BB, ALL)
BEST, WORST = BB[0], BB[-1]
GR_ALL, GR_DAI, GR_VEG = range_words(BB), range_words(DAI), range_words(VEG)
best_all, worst_all = grade_range(BB)
dai_best, dai_worst = grade_range(DAI)
veg_best, veg_worst = grade_range(VEG)
veg_grades = sorted({b['score_band'] for b in VEG}, key=BAND_ORDER.index)
VEG_GRADES_OR = ' or '.join(veg_grades)
P_DAI_LO, P_DAI_HI, P_DAI_AVG = min(map(P, DAI)), max(map(P, DAI)), avg(DAI, 'Protein (g)')
P_VEG = sorted(set(map(P, VEG)))
P_DROP = round(100 * (P_DAI_AVG - avg(VEG, 'Protein (g)')) / P_DAI_AVG)
DAI_PROT_TOP, _ = top_pct(ALL, field('Protein (g)'), P_DAI_AVG, 'high')
SA_ST, SUG_ST, PRO_ST, P100_ST = ST['sa'], ST['sugar'], ST['protein'], ST['p100']
SA_MORE_THAN = 100 - SA_ST['beats']          # share of bars with less sugar alcohol
all_sucralose = all(has(b, 'sucralose') for b in BB)
all_maltitol = all(has(b, 'maltitol') for b in BB)
check(all_sucralose and all_maltitol, 'every flavor contains sucralose and maltitol')
check(len(VEG) >= 2 and len(DAI) >= 2, 'Barebells still has both a dairy and a vegan line')

# Sweetener stacking
DAI_STACK = [b for b in DAI if stacks(b)]
VEG_STACK = [b for b in VEG if stacks(b)]
VEG_NOSTACK = [b for b in VEG if not stacks(b)]
SA_VEG_STACK = sum(map(sa, VEG_STACK)) / len(VEG_STACK) if VEG_STACK else 0
SA_DAI = sum(map(sa, DAI)) / len(DAI)
veg_pick = min(VEG, key=lambda b: (band_rank(b), sa(b), -P(b), nm(b)))
# The vegan story only holds while the non-stacking vegan flavor out-grades the stackers
VEG_STORY = check(len(VEG_NOSTACK) == 1 and len(VEG_STACK) == len(VEG) - 1 and veg_pick is VEG_NOSTACK[0]
                  and all(band_rank(veg_pick) < band_rank(b) for b in VEG_STACK),
                  'exactly one vegan flavor skips maltitol syrup and it grades above the other vegan flavors')
others_sa = sorted(set(map(sa, VEG_STACK)))
others_sa_txt = f'{fnum(others_sa[0])}g' if len(others_sa) == 1 else f'{fnum(others_sa[0])} to {fnum(others_sa[-1])}g'

# Lowest-scoring flavors: which line are they from?
n_bottom_veg = 0
for b in reversed(BB):
    if b in VEG:
        n_bottom_veg += 1
    else:
        break
DAI_BELOW_C = [b for b in DAI if b['score_band'] in ('D', 'F')]

# Chips
FREQ = chip_freq(BB)
def cnt(chip, bars=BB): return sum(1 for b in bars if has_tag(b, chip))
COLL_D, COLL_V = cnt('Collagen Protein', DAI), cnt('Collagen Protein', VEG)
PO_ALL, PO_D, PO_V = cnt('Processed Oils'), cnt('Processed Oils', DAI), cnt('Processed Oils', VEG)
SH_ALL, LIL_ALL, QPS_ALL = cnt('Sweetener Heavy'), cnt('Long Ingredient List'), cnt('Quality Protein Source')

# ---------------------------------------------------------------------------
# Which flavor to buy
# ---------------------------------------------------------------------------
MAXP = max(map(P, BB))
top_p = [b for b in BB if P(b) == MAXP]
top_p_band = min(band_rank(b) for b in top_p)
top_p_best = [b for b in top_p if band_rank(b) == top_p_band]
pick_protein = min(top_p_best, key=lambda b: (sa(b), nm(b)))
rank_overall = BB.index(pick_protein) + 1
MINSA = min(map(sa, BB))
low_sa = sorted([b for b in BB if sa(b) == MINSA], key=lambda b: (band_rank(b), nm(b)))
MINP = min(map(P, BB))
skip = [b for b in BB if stacks(b) and P(b) == MINP and b['score_band'] in ('D', 'F')]

def grade_list(bars):
    gs = sorted({b['score_band'] for b in bars}, key=BAND_ORDER.index)
    return 'all grade ' + gs[0] if len(gs) == 1 else 'grade ' + ' or '.join(gs)

t1 = (f"{num_word(len(top_p)).capitalize()} flavors tie at {fnum(MAXP)}g protein, the top of the lineup. "
      if len(top_p) > 1 else f"{fnum(MAXP)}g protein, the most in the lineup. ")
if len(top_p) > 1:
    others = [b for b in top_p if b is not pick_protein]
    if len(top_p_best) == 1:
        t1 += (f"{nm(pick_protein)} is the only one of them with {'an' if pick_protein['score_band'] in 'AF' else 'a'} "
               f"{pick_protein['score_band']} grade (#{rank_overall} flavor overall), so it's the one to start with if protein per bar is the deciding factor.")
    else:
        t1 += (f"{nm(pick_protein)} grades {pick_protein['score_band']} with the least sugar alcohol of that group ({fnum(sa(pick_protein))}g), "
               "so it's the one to start with if protein per bar is the deciding factor.")
t2 = (f"{'All ' + num_word(len(low_sa)) + ' tie' if len(low_sa) > 1 else 'It sits'} at {fnum(MINSA)}g, the lowest any Barebells flavor gets"
      f"{', and ' + grade_list(low_sa) if len(low_sa) > 1 else ', grade ' + low_sa[0]['score_band']}. "
      "That's about as good a floor for sugar alcohol as this brand offers.")
t3 = (f"{'Still a' if veg_pick['score_band'] in 'DF' else 'A'} {veg_pick['score_band']} grade, but the only one of the {num_word(len(VEG))} vegan flavors "
      f"that skips the second sugar alcohol source (maltitol syrup on top of maltitol), keeping it at {fnum(sa(veg_pick))}g against "
      f"{others_sa_txt} for the other {num_word(len(VEG_STACK))}.") if VEG_STORY else ''
t4 = (f"Stack two separate sugar alcohol sources, carry the lowest protein in the lineup at {fnum(MINP)}g, and "
      f"{grade_list(skip)}. The only flavors that combine all three weaknesses at once.")
check(len(skip) >= 1, 'at least one flavor stacks sugar alcohols, has the lowest protein and grades D or F')

PICK_TILES = [brand_pick_tile('Highest protein', [pick_protein], t1),
              brand_pick_tile('Least sugar alcohol', low_sa, t2)]
if VEG_STORY:
    PICK_TILES.append(brand_pick_tile('Need the vegan line', [veg_pick], t3))
if skip:
    PICK_TILES.append(brand_pick_tile('Skip regardless of diet', skip, t4, buy=False))

# ---------------------------------------------------------------------------
# Cross-brand alternatives to the highest-protein pick
# ---------------------------------------------------------------------------
FLAG = pick_protein
KEY = FLAG['Flavor Name'].lower()
FP, FC, FF, FS, FB = P(FLAG), CAL(FLAG), FIB(FLAG), sa(FLAG), band_rank(FLAG)
POOL = [b for b in ALL if b['Brand Name'] != BRAND and KEY in b['Flavor Name'].lower()
        and CAL(b) and CAL(b) <= FC + 30 and (amazon_url(b) or website_url(b))]
_used = set()
def alt(cands, key):
    c = [b for b in cands if b['Key'] not in _used]
    if not c:
        return None
    b = min(c, key=lambda x: key(x) + (x['Brand Name'].lower(), nm(x).lower()))
    _used.add(b['Key'])
    return b

def cal_delta(b):
    d = FC - CAL(b)
    return f'{fnum(abs(d))} fewer calories' if d > 0 else (f'{fnum(-d)} more calories' if d < 0 else 'the same calories')

def grade_vs(b):
    if b['score_band'] == FLAG['score_band']:
        return f"Same {b['score_band']} grade as {nm(FLAG)}."
    return f"Grades {b['score_band']} instead of {FLAG['score_band']}."

ALTS = []
a1 = alt([b for b in POOL if sa(b) == 0 and P(b) >= FP and band_rank(b) <= FB], lambda b: (band_rank(b), -P(b), CAL(b)))
if a1:
    ALTS.append(('Cut the sugar alcohol', a1,
                 f"{'Same' if P(a1) == FP else fnum(P(a1)) + 'g vs.'} {fnum(FP)}g protein, {cal_delta(a1)}, and zero sugar alcohol vs. {fnum(FS)}g here. {grade_vs(a1)}"
                 .replace('Same 20g protein', f'Same {fnum(FP)}g protein')))
a2 = alt([b for b in POOL if band_rank(b) < FB and FIB(b) >= FF + 3 and not has_tag(b, 'Artificial Sweeteners')],
         lambda b: (band_rank(b), -FIB(b), -P(b)))
if a2:
    trade = (f" Trade-off: protein drops to {fnum(P(a2))}g from {fnum(FP)}g" + (f", for {cal_delta(a2)}." if CAL(a2) != FC else '.')) if P(a2) < FP else ''
    ALTS.append(('Better quality, more fiber', a2,
                 f"Grades {a2['score_band']} instead of {FLAG['score_band']} with {fnum(FIB(a2))}g fiber vs. {fnum(FF)}g here, no artificial sweeteners, "
                 f"and sugar alcohol {'at zero' if sa(a2) == 0 else 'down to ' + fnum(sa(a2)) + 'g'}.{trade}"))
a3 = alt([b for b in POOL if P(b) >= FP and CAL(b) < FC and band_rank(b) <= FB], lambda b: (CAL(b), -P(b)))
if a3:
    extra = f" with more fiber ({fnum(FIB(a3))}g vs. {fnum(FF)}g)" if FIB(a3) > FF else ''
    sa3 = ('and no sugar alcohol' if sa(a3) == 0 else
           f"and sugar alcohol is still present at {fnum(sa(a3))}g" + (f", down from {fnum(FS)}g" if sa(a3) < FS else ''))
    ALTS.append(('Same protein, fewer calories' if P(a3) == FP else 'More protein, fewer calories', a3,
                 f"{'Identical' if P(a3) == FP else fnum(P(a3)) + 'g vs.'} {fnum(FP)}g protein at {cal_delta(a3)}{extra}, {sa3}. {grade_vs(a3)}"))

# ---------------------------------------------------------------------------
# Brand comparison
# ---------------------------------------------------------------------------
GROUPS = [(BRAND, BB)] + [(n, [b for b in ALL if b['Brand Name'] == n]) for n in COMPARE]
for n, g in GROUPS:
    check(len(g) > 0, f'{n} exists in bars.js for the comparison table')
def p100avg(bars): return avg([dict(x=p100(b)) for b in bars], 'x')
def no_as_sa(bars): return not any(has_tag(b, 'Artificial Sweeteners') or has_tag(b, 'Sugar Alcohols') for b in bars)
by_p100 = sorted(GROUPS, key=lambda g: -p100avg(g[1]))
bb_rank = [n for n, _ in by_p100].index(BRAND) + 1
f_swing = [n for n, g in GROUPS if grade_range(g)[1] == 'F']
clean_brands = [n for n, g in GROUPS if no_as_sa(g)]
narrowest = [n for n, g in GROUPS if grade_range(g)[0] == 'A' and grade_range(g)[1] in ('A', 'B')]
note = []
if len(f_swing) >= 2:
    note.append(f"{names_and(f_swing)} both swing down to F depending on flavor, so neither brand's best flavor represents the full lineup.")
lead = by_p100[0][0]
note.append(f"Barebells {'leads this group' if bb_rank == 1 else 'ranks ' + ['', 'first', 'second', 'third', 'fourth', 'fifth'][bb_rank] + ' in this group'} "
            f"on protein efficiency at {g1(p100avg(BB))}g per 100 calories" + ('' if bb_rank == 1 else f", behind {names_and([n for n, _ in by_p100[:bb_rank - 1]])}") +
            ".")
split_lines = [n for n, g in GROUPS[1:] if 0 < sum(1 for b in g if b.get('Vegan (Y/N)') == 'Yes') < len(g)]
if not split_lines:
    note[-1] = note[-1][:-1] + ", and it is the only brand here that splits into a dairy line and a separate vegan line with a different protein system."
if clean_brands:
    note.append(f"{names_and(clean_brands)} skip{'s' if len(clean_brands) == 1 else ''} both artificial sweeteners and sugar alcohols across every flavor.")
if narrowest:
    note.append(f"{names_and(narrowest)} {'is' if len(narrowest) == 1 else 'are'} the most consistent, A down to B with nothing lower.")
COMPARE_NAMES = names_and(COMPARE)
COMPARE_HTML = f'''<h2 class="brand-compare-title">How Barebells compares to {esc(COMPARE_NAMES)}</h2>
      <div class="brand-compare-sub">All figures are per-brand averages across every flavor we've scored, not a single cherry-picked bar, and grade ranges show the full spread from that brand's best flavor to its worst.</div>
      <div class="brand-compare-table-wrap">
        <table class="brand-compare-table">
          <thead>
            <tr><th>Bar</th><th class="ctr">Grade range</th><th class="ctr" title="Protein per 100 calories">Protein/100cal</th><th class="ctr col-hide-mobile">Fiber avg</th><th class="ctr col-hide-mobile">Sugar avg</th><th>Sweetener</th></tr>
          </thead>
          <tbody>
{compare_rows(BRAND, GROUPS)}
          </tbody>
        </table>
      </div>
      <div class="brand-compare-note">
        <div class="brand-compare-note-text">{esc(' '.join(note))}</div>
      </div>'''

# ---------------------------------------------------------------------------
# Copy
# ---------------------------------------------------------------------------
H1_TEXT = f'Are Barebells Bars Healthy? We Ranked All {N} Flavors'
H1_HTML = f'Are <em>Barebells</em> Bars Healthy? We Ranked All {N} Flavors'
TITLE = f'Are Barebells Protein Bars Healthy? {N} Flavors Ranked | Know Your Bar'
OG_TITLE = f'Are Barebells Protein Bars Healthy? {N} Flavors Ranked'
veg_worst_line = check(worst_all in veg_grades and worst_all not in {b['score_band'] for b in DAI},
                       "the vegan line holds the lineup's worst grade")
DESC = (f"Barebells grades {GR_ALL} across {N} flavors. Bottom {SA_ST['beats']}% for sugar alcohol despite top "
        f"{SUG_ST['top']}% lowest sugar." + (' The vegan line grades worst of all.' if veg_worst_line else ''))
OG_DESC = (f"Barebells scored A-F by ingredient quality. Top {SUG_ST['top']}% for lowest sugar, but bottom {SA_ST['beats']}% "
           f"for sugar alcohol. All {N} flavors ranked.")
check(len(DESC) <= 155, f'meta description under 155 chars ({len(DESC)})')

HERO_SUB = (f"Barebells doesn't officially split into sub-brands, but the data shows two distinct formulas hiding under one label, "
            f"with different protein sources and very different ingredient quality. The core dairy-protein lineup ({len(DAI)} of {N} flavors) "
            f"grades {GR_DAI} and ranks in the top {DAI_PROT_TOP}% for protein across 1,000+ bars we track. The {len(VEG)}-flavor vegan line "
            f"grades {VEG_GRADES_OR}" + (', the worst in the lineup,' if veg_worst_line else ',') +
            f" built around a lower-protein formula with heavier sweetener stacking. Sugar stays low across both lines, top {SUG_ST['top']}% lowest "
            f"in our database, but it's offset by a heavy dose of sugar alcohol: Barebells lands in the bottom {SA_ST['beats']}% of every bar we've "
            "scored. Here is the full breakdown, flavor by flavor.")
check(len(VEG_STACK) > len(DAI_STACK) * len(VEG) / len(DAI) and max(P_VEG) < P_DAI_AVG,
      'vegan line has lower protein and more sweetener stacking than the dairy line')

MACRO = f'''<h2>How Barebells protein bars rank on macros</h2>
    <p>Instead of labeling macros good or bad, we rank Barebells against every other protein bar in our database so you can see how they stack up against the market.</p>
{MACRO_HTML}
    <p class="macro-summary-text">Barebells' standout numbers are protein and sugar: {g1(PRO_ST['avg'])}g of protein puts it in the top {PRO_ST['top']}% of bars we track, and {g1(SUG_ST['avg'])}g of sugar puts it in the top {SUG_ST['top']}% lowest. The tradeoff is sugar alcohol. At {g1(SA_ST['avg'])}g average, Barebells carries more sugar alcohol than {SA_MORE_THAN}% of the bars in our database.</p>'''

ov1 = (f"Barebells doesn't market this as two sub-brands, but the split shows up clearly in the numbers, not just the vegan label. "
       f"The core dairy line, {len(DAI)} of {N} flavors, leads with a milk protein blend of whey protein and casein, and it delivers real protein: "
       f"{fnum(P_DAI_LO)} to {fnum(P_DAI_HI)}g per bar, averaging {fnum(P_DAI_AVG)}g. The vegan line, {len(VEG)} flavors, leads with a plant protein blend instead, "
       + (f"and every one of those {num_word(len(VEG))} flavors sits flat at {fnum(P_VEG[0])}g of protein, no exceptions. "
          if len(P_VEG) == 1 else f"at {fnum(P_VEG[0])} to {fnum(P_VEG[-1])}g of protein. ")
       + f"That's a {P_DROP}% drop in average protein between the two lines, not just an ingredient-quality gap.")
ov2 = (f"The sweetener load tells the same story from a different angle. Only {num_word(len(DAI_STACK))} of the {len(DAI)} dairy-line flavors "
       f"stack{'s' if len(DAI_STACK) == 1 else ''} a second sugar alcohol source (maltitol plus maltitol syrup) on top of its base sweetening"
       + (f" ({names_and(nm(b) for b in DAI_STACK)})" if 0 < len(DAI_STACK) <= 2 else '') + ". "
       f"In the vegan line, {len(VEG_STACK)} of {len(VEG)} flavors do exactly that, and it shows: those {num_word(len(VEG_STACK))} average "
       f"{g1(SA_VEG_STACK)}g of sugar alcohol per bar against a dairy-line average of {g1(SA_DAI)}g.")
if VEG_STORY:
    ov2 += (f" {nm(veg_pick)} is the one vegan flavor that skips the second sugar alcohol source, and it's also the highest-graded of the "
            f"{num_word(len(VEG))} ({veg_pick['score_band']}, against {' and '.join(sorted({b['score_band'] for b in VEG_STACK}, key=BAND_ORDER.index))} for the rest).")
ov3 = ("Practically, this means the two lines aren't interchangeable. If you're buying Barebells for its protein numbers, "
       "the dairy line is where that reputation comes from, not the vegan line.")
if VEG_STORY:
    stk_sa = SA_VEG_STACK - sa(veg_pick)
    stk_f = FIB(veg_pick) - sum(map(FIB, VEG_STACK)) / len(VEG_STACK)
    stk_c = CAL(veg_pick) - sum(map(CAL, VEG_STACK)) / len(VEG_STACK)
    ov3 += (f" If you need the vegan line specifically, {nm(veg_pick)} is the one to reach for over the other {num_word(len(VEG_STACK))}: "
            + (f"it costs {fnum(round(stk_c))} more calories, but it " if round(stk_c) > 0 else 'it ')
            + f"carries roughly {fnum(round(stk_sa))}g less sugar alcohol"
            + (f" and {fnum(round(stk_f))}g more fiber" if round(stk_f) > 0 else '') + ".")
OVERVIEW = f'''<h2>What the data shows across all {N} Barebells flavors</h2>
    <p>{esc(ov1)}</p>
    <p>{esc(ov2)}</p>
    <p>{esc(ov3)}</p>'''

if n_bottom_veg == len(VEG) and not DAI_BELOW_C:
    gd_note = (f"The {' and '.join(veg_grades)} grades belong entirely to the vegan line: all {num_word(len(VEG))} vegan flavors land there, "
               f"while the entire {len(DAI)}-flavor dairy line grades {GR_DAI}.")
else:
    gd_note = (f"All {num_word(len(VEG))} vegan flavors grade {VEG_GRADES_OR}, and they include "
               + (f"the {num_word(n_bottom_veg)} lowest scores in the lineup. " if n_bottom_veg > 1 else "the lowest score in the lineup. ")
               + f"The {len(DAI)}-flavor dairy line grades {GR_DAI}"
               + (f", with {names_and(nm(b) for b in DAI_BELOW_C)} the only dairy flavor{'s' if len(DAI_BELOW_C) > 1 else ''} below C." if DAI_BELOW_C else '.'))
GRADES = f'''<h2>Ingredient quality grade distribution across all {N} flavors</h2>
    <p>Here is how Barebells' full lineup grades out. This is every flavor we've scored, not a hand-picked few. {esc(gd_note)}</p>
{grade_dist_html(BB)}'''

BESTWORST = f'''<h2>Best and worst flavors by ingredient quality</h2>
    <div class="bestworst">
{bw_card_html(BEST, True)}
{bw_card_html(WORST, False)}
    </div>'''

pat = []
pat.append(f"Quality Protein Source shows up in {'every flavor' if QPS_ALL == N else f'{QPS_ALL} of {N} flavors'}, dairy and vegan alike, "
           "since both protein systems clear the bar for a genuine protein source, even though the grams of actual protein differ sharply between the two lines.")
if COLL_V == 0 and COLL_D == len(DAI):
    pat.append(f"Collagen Protein is present in {COLL_D} of {N} flavors (the entire dairy line) but absent from all {num_word(len(VEG))} vegan flavors, since collagen is animal-derived.")
else:
    pat.append(f"Collagen Protein shows up in {COLL_D + COLL_V} of {N} flavors.")
if PO_ALL:
    pat.append(f"Processed Oils shows up in {PO_ALL} of {N} flavors"
               + (f" ({PO_D} of {len(DAI)} dairy, {PO_V} of {len(VEG)} vegan)" if PO_D and PO_V else '') + ".")
if SH_ALL:
    pat.append(f"Sweetener Heavy flags {SH_ALL} of {N} flavors for stacking multiple sweetening agents on top of the base maltitol"
               + (f", and a Long Ingredient List shows up in {LIL_ALL} of {N}." if LIL_ALL else '.'))
PATTERNS = f'''<h2>Ingredient quality patterns across the Barebells lineup</h2>
    <p>Every Barebells flavor shares a core ingredient profile, but the two formulas underneath diverge more than the label lets on. Here's what shows up across all {N} flavors, split by whether it counts in the bar's favor or against it.</p>

{chip_patterns_html(BB)}

    <p style="margin-top:1.25rem;">{esc(' '.join(pat))}</p>'''

TABLE_HEADING = f'''<h2>All {N} Barebells flavors ranked by ingredient quality</h2>
    <p>Every flavor, every macro, every ingredient grade. Sorted from cleanest to most processed. Tap any row to see the full ingredient list, macros, and where to buy it.</p>'''

second = BB[1]
bl1 = (f"Barebells earns its reputation as a high-protein, low-sugar option, most of all in its {len(DAI)}-flavor dairy line. "
       f"Averaging {g1(PRO_ST['avg'])}g of protein and just {g1(SUG_ST['avg'])}g of sugar per bar is a genuinely strong combination, and the dairy line's "
       f"milk protein blend is a quality source that scores well in our system. But the ingredient story has a real asterisk: sugar alcohol content "
       f"lands in the bottom {SA_ST['beats']}% of every bar we track, and every flavor, dairy and vegan alike, contains both sucralose and maltitol.")
bl2 = (f"The bigger decision is which line you're buying. The vegan flavors, {names_and(nm(b) for b in VEG)}, grade {VEG_GRADES_OR} and are "
       "meaningfully different products from an ingredient standpoint, built around a plant protein blend instead of dairy protein. "
       f"If you want Barebells' protein numbers without that gap, start with {nm(BEST)} or {nm(second)}. {nm(BEST)} leads the lineup at "
       f"{BEST['score_band']} grade, and {nm(second)} follows{', also at ' + second['score_band'] if second['score_band'] == BEST['score_band'] else ' at ' + second['score_band']}.")
check(BEST in DAI and second in DAI, 'the two best flavors are both from the dairy line')
BOTTOM = f'''<h2>Bottom line on Barebells</h2>
    <p>{esc(bl1)}</p>
    <p>{esc(bl2)}</p>'''

PICKS = f'''<h2>Which Barebells flavor should you actually buy</h2>
    <p>With a {N}-flavor lineup spanning {best_all} to {worst_all}, there isn't one answer to "which Barebells bar." Here's how we'd sort it depending on your goals, based on what's actually in the data above rather than the best- or worst-flavor snapshot alone.</p>
    <div class="macro-grid pick-tile-grid">
{chr(10).join(PICK_TILES)}
    </div>'''

ALTS_HTML = f'''<h2>Like {esc(nm(FLAG))}? These are worth a look too</h2>
    <p>{esc(nm(FLAG))} is Barebells' highest-protein pick, but it also carries {fnum(FS)}g of sugar alcohol. {num_word(len(ALTS)).capitalize()} ways to trade up depending on what matters most to you.</p>
    <div class="macro-grid pick-tile-grid">
{chr(10).join(alt_tile(*a) for a in ALTS)}
    </div>'''

RX = [b for b in ALL if b['Brand Name'] == 'RXBAR']
QU = [b for b in ALL if b['Brand Name'] == 'Quest']
check(no_as_sa(RX), 'RXBAR has no artificial sweeteners or sugar alcohols')
check(avg(RX, 'Protein (g)') < avg(BB, 'Protein (g)'), 'RXBAR averages less protein than Barebells')
check(all(has_tag(b, 'Artificial Sweeteners') for b in QU), 'Quest leans on artificial sweeteners in every flavor')
qb, qw = grade_range(QU)
RELATED = f'''
        <a href="/rxbar-review" class="explore-more-card">
          <div class="explore-more-title">RXBAR Review</div>
          <div class="explore-more-desc">No artificial sweeteners or sugar alcohols anywhere in the lineup. Lower protein than Barebells, but every flavor grades {esc(range_words(RX))}.</div>
        </a>
        <a href="/quest-bars" class="explore-more-card">
          <div class="explore-more-title">Quest Review</div>
          <div class="explore-more-desc">Another high-protein, low-sugar brand that leans on artificial sweeteners. See how its all-{qb}-{'or-' + qw + ' ' if qb != qw else ''}lineup compares to Barebells' wider spread.</div>
        </a>
        <a href="/no-sugar-alcohols" class="explore-more-card">
          <div class="explore-more-title">No Sugar Alcohols Guide</div>
          <div class="explore-more-desc">If maltitol is where Barebells loses you, here are high-protein bars that skip sugar alcohols entirely.</div>
        </a>'''

QU_P = avg(QU, 'Protein (g)')
RX_best, RX_worst = grade_range(RX)
cmp_q = (f"Compared to Quest, Barebells has {'higher' if PRO_ST['avg'] > QU_P else 'lower' if PRO_ST['avg'] < QU_P else 'the same'} average protein "
         f"({g1(PRO_ST['avg'])}g vs. {g1(QU_P)}g) and a wider grade spread ({GR_ALL} vs. {range_words(QU)})"
         + (', with every F coming from its vegan line.' if 'F' in {b['score_band'] for b in BB} and not any(b['score_band'] == 'F' for b in DAI) else '.'))
cmp_r = (f"Compared to RXBAR, Barebells wins on protein and loses on ingredient consistency, since RXBAR's full lineup stays {RX_worst} or above."
         if RX_worst in ('A', 'B') else '')
veg_desc = f"The {num_word(len(VEG))} vegan flavors ({names_and(nm(b) for b in VEG)}) "
veg_desc += (f"are the {num_word(len(VEG))} lowest-scoring flavors in the entire lineup" if n_bottom_veg == len(VEG)
             else f"include the {num_word(n_bottom_veg)} lowest-scoring flavors in the lineup" if n_bottom_veg > 1 else "include the lowest-scoring flavor in the lineup")
veg_desc += f", grading {VEG_GRADES_OR}."
FAQS = [
    ('Are Barebells bars healthy?',
     f"It depends which flavor. Barebells grades range from {GR_ALL} across {N} flavors we've scored. The core dairy-protein lineup "
     f"({len(DAI)} of {N} flavors) grades {GR_DAI} and has a genuinely solid protein source. The vegan line ({len(VEG)} flavors) grades {VEG_GRADES_OR}. "
     "Every flavor, regardless of line, contains sucralose and maltitol."),
    ('Which Barebells flavor is the healthiest?',
     f"{nm(BEST)} scores highest at {fnum(score(BEST))} ({BEST['score_band']}, {grade_word(BEST['score_band'])}), followed by {nm(second)} at "
     f"{fnum(score(second))} ({second['score_band']}, {grade_word(second['score_band'])}). Both lead with Barebells' milk protein blend of whey and casein."),
    ('How much protein do Barebells bars have?',
     f"Barebells bars contain {fnum(PRO_ST['lo'])} to {fnum(PRO_ST['hi'])}g of protein, averaging {g1(PRO_ST['avg'])}g. That puts the brand in the "
     f"top {PRO_ST['top']}% for protein across 1,000+ bars we track. Protein per 100 calories averages {g1(P100_ST['avg'])}g, a top-{P100_ST['top']}% result."),
    ('Do Barebells bars have artificial sweeteners?',
     f"Yes. Every one of the {N} Barebells flavors we've scored contains sucralose. There is no Barebells flavor, in either the dairy or vegan line, "
     "that skips artificial sweeteners."),
    ('Do Barebells bars have sugar alcohols?',
     f"Yes, and this is where Barebells falls furthest behind the field. Every flavor contains maltitol, averaging {g1(SA_ST['avg'])}g per bar and "
     f"ranging up to {fnum(SA_ST['hi'])}g. That average lands in the bottom {SA_ST['beats']}% of every bar in our database, meaning {SA_MORE_THAN}% of bars "
     "we track carry less sugar alcohol than Barebells does."),
    ('How do Barebells bars compare to other protein bars?',
     f"Barebells beats most bars on protein (top {PRO_ST['top']}%) and total sugar (top {SUG_ST['top']}% lowest), which is a genuinely strong combination. "
     f"The tradeoff is sugar alcohol, where it ranks in the bottom {SA_ST['beats']}% of the database. {cmp_q} {cmp_r}".strip()),
    ('What type of protein is in Barebells bars?',
     f"The core lineup ({len(DAI)} of {N} flavors) uses a milk protein blend built from whey protein and casein, all quality dairy-based sources. "
     f"The {num_word(len(VEG))} vegan flavors swap this for a plant protein blend, mostly hydrolyzed wheat gluten and soy protein isolate, "
     "a more processed combination that scores noticeably worse in our system."),
    ('Are Barebells vegan bars different from the regular bars?',
     "Significantly. " + veg_desc + " They swap the milk protein blend for a plant protein blend and lose the Collagen Protein ingredient entirely, "
     "but the loss of that one concern chip isn't enough to offset the rest of the formula. If you're buying Barebells specifically for ingredient "
     "quality, stick to the core dairy line."),
]
wg = sum(1 for b in VEG if has(b, 'wheat gluten'))
check(wg > len(VEG) / 2 and all(has(b, 'soy protein isolate') for b in VEG), 'vegan blend is mostly hydrolyzed wheat gluten and soy protein isolate')
check(all(has(b, 'milk protein blend') for b in DAI), 'every dairy flavor leads with a milk protein blend')

# ---------------------------------------------------------------------------
# Head
# ---------------------------------------------------------------------------
HEAD_META = f'''  <title>{esc(TITLE)}</title>
  <meta name="description" content="{esc(DESC)}">'''
ARTICLE = f'''<script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": {json.dumps(H1_TEXT)},
    "description": {json.dumps(DESC)},
    "url": "{URL}",
    "image": "https://knowyourbar.com/bar_hero.png",
    "datePublished": "2026-04-01",
    "dateModified": "{today_iso()}",
    "author": {{"@type":"Organization","name":"Know Your Bar","url":"https://knowyourbar.com"}},
    "publisher": {{"@type":"Organization","name":"Know Your Bar","url":"https://knowyourbar.com"}},
    "mainEntityOfPage": {{"@type":"WebPage","@id":"{URL}"}},
    "about": {{"@type":"Brand","name":"Barebells","url":"https://www.barebells.com"}}
  }}
  </script>'''
FAQ_LD = '<script type="application/ld+json">\n  ' + json.dumps({
    '@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
        {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in FAQS]},
    indent=2, ensure_ascii=False).replace('\n', '\n  ') + '\n  </script>'
SOCIAL = f'''<meta property="og:type" content="article">
  <meta property="og:site_name" content="Know Your Bar">
  <meta property="og:title" content="{esc(OG_TITLE)}">
  <meta property="og:description" content="{esc(OG_DESC)}">
  <meta property="og:url" content="{URL}">
  <meta property="og:image" content="https://knowyourbar.com/bar_hero.png">
  <!-- Twitter card -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(OG_TITLE)}">
  <meta name="twitter:description" content="{esc(OG_DESC)}">
  <meta name="twitter:image" content="https://knowyourbar.com/bar_hero.png">'''
HERO = f'''<h1 class="hero-title">{H1_HTML}</h1>
    <p class="hero-sub">{esc(HERO_SUB)}</p>'''
FAQ_HTML = '\n'.join(f'''
      <div class="faq-item">
        <button class="faq-q">{esc(q)}</button>
        <div class="faq-a">{esc(a)}</div>
      </div>''' for q, a in FAQS) + '\n'

# ---------------------------------------------------------------------------
# Assemble, QA, write
# ---------------------------------------------------------------------------
if PROBLEMS:
    print('COPY NEEDS REVIEW, page not written. These claims are no longer true in bars.js:')
    for p in PROBLEMS:
        print('  -', p)
    sys.exit(1)

page = open(PAGE, encoding='utf-8').read()
for name, content in [
    ('head-meta', HEAD_META), ('jsonld-article', ARTICLE), ('jsonld-faq', FAQ_LD), ('social', SOCIAL),
    ('hero', HERO), ('macro', MACRO), ('overview', OVERVIEW), ('grades', GRADES), ('bestworst', BESTWORST),
    ('patterns', PATTERNS), ('table-heading', TABLE_HEADING), ('table-rows', brand_table_html(BB, ALL)),
    ('bottom', BOTTOM), ('picks', PICKS), ('alts', ALTS_HTML), ('related', RELATED), ('compare', COMPARE_HTML),
    ('faq', FAQ_HTML),
]:
    page = replace_region(page, name, content)
page = stamp_dates(page, today_iso())

problems, n_rows = brand_grade_sync(page, BB, ALL)
for bad in ['href="Yes"', 'href="None"']:
    if bad in page:
        problems.append(f'broken link field: {bad}')
if problems:
    print('GRADE-SYNC / QA FAILED, page not written:')
    for p in problems:
        print('  ', p)
    sys.exit(1)

open(PAGE, 'w', encoding='utf-8').write(page)
print(f'{PAGE}: {N} flavors, grades {GR_ALL} ({grade_counts_txt(BB, " ")})')
print(f'Best {nm(BEST)} {BEST["score_band"]} {fnum(score(BEST))} | Worst {nm(WORST)} {WORST["score_band"]} {fnum(score(WORST))}')
print('Picks:', ', '.join(nm(pick_protein) for _ in [0]), '|', ', '.join(map(nm, low_sa)), '|', nm(veg_pick) if VEG_STORY else '-', '|', ', '.join(map(nm, skip)))
print('Alternatives:', ' | '.join(f"{a[0]}: {a[1]['Brand Name']} {a[1]['Flavor Name']} ({a[1]['score_band']})" for a in ALTS))
print(f'Grade-sync: {n_rows} flavor rows, best/worst cards and alternative tiles checked against bars.js, 0 mismatches')
