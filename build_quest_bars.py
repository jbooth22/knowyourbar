#!/usr/bin/env python3
"""
Rebuild the data on quest-bars.html from live bars.js.

    python3 build_quest_bars.py

Opens the live page and rewrites only the <!-- kyb:NAME --> regions (see
kyb_guide_lib.py / kyb_brand_lib.py). Nav, footer, fonts, canonical URL, the
Explore CTA and the brand-link pills are never touched.

Every number, grade and flavor name comes from bars.js. Copy that depends on
the data is a template; structural claims ("every flavor contains
sucralose") go through claims.check(), and the build stops with the failed
claim listed if a future bars.js makes one false.
"""
from kyb_brand_lib import *

PAGE = 'quest-bars.html'
BRAND = 'Quest'
URL = 'https://knowyourbar.com/quest-bars'
COMPARE = ['Barebells', 'Clif Builders', 'RXBAR', 'KIND']
ALT_KEYWORD = 'chocolate chip'          # cross-brand alternatives are other brands' chocolate chip flavors

ALL = load_bars()
QB = sort_for_list([b for b in ALL if b['Brand Name'] == BRAND])
N = len(QB)
C = Claims()

MACRO_HTML, ST = macro_grid_html(QB, ALL)
PRO, P100S, SUGS, SAS, FIBS = ST['protein'], ST['p100'], ST['sugar'], ST['sa'], ST['fiber']
BEST, WORST, SECOND, THIRD = QB[0], QB[-1], QB[1], QB[2]
GC = grade_counts(QB)
best_g, worst_g = grade_range(QB)
GRADES_PRESENT = [g for g in BAND_ORDER if GC[g]]
GR_OR = ' or '.join(GRADES_PRESENT)
NO_A = GC['A'] == 0
def po(b): return has_tag(b, 'Processed Oils')
def lil(b): return has_tag(b, 'Long Ingredient List')
PO_BARS = [b for b in QB if po(b)]
TOP_BAND = [b for b in QB if b['score_band'] == best_g]
REST = [b for b in QB if b['score_band'] != best_g]
SA_MIN, SA_MAX = min(map(sa, QB)), max(map(sa, QB))
sa_sev = {'minor': 0, 'elevated': 0}
for b in QB:
    for name, typ, sev in chip_list(b):
        if name == 'Sugar Alcohols' and sev in sa_sev:
            sa_sev[sev] += 1
n_stevia = sum(1 for b in QB if has_ing(b, 'stevia'))

C.check(all(has_tag(b, 'Artificial Sweeteners') for b in QB), 'every Quest flavor has the Artificial Sweeteners tag')
C.check(all(has_tag(b, 'Sugar Alcohols') for b in QB), 'every Quest flavor has the Sugar Alcohols tag')
C.check(all(has_ing(b, 'sucralose') for b in QB), 'every Quest flavor contains sucralose')
C.check(all(has_ing(b, 'erythritol') for b in QB), 'every Quest flavor contains erythritol')
C.check(all(has_ing(b, 'milk protein isolate') and has_ing(b, 'whey protein isolate') for b in QB),
        'every Quest flavor uses the milk protein isolate + whey protein isolate blend')
C.check(all(has_tag(b, 'Quality Protein Source') for b in QB), 'every Quest flavor carries Quality Protein Source')
C.check(len(REST) > 0, 'Quest has more than one grade tier')
C.check(not any(po(b) for b in TOP_BAND), f'none of the {best_g}-grade Quest flavors carries a processed oil')
C.check(all(has_ing(b, 'palm') for b in PO_BARS), "Quest's processed oil is palm kernel oil")

# ---------------------------------------------------------------------------
# Which flavor to buy
# ---------------------------------------------------------------------------
low_sa_all = [b for b in QB if sa(b) == SA_MIN]
low_sa = sorted([b for b in low_sa_all if not po(b)], key=lambda b: (band_rank(b), nm(b)))
low_sa_skipped = [b for b in low_sa_all if po(b)]
C.check(len(low_sa) >= 1, 'at least one lowest-sugar-alcohol flavor skips processed oils')
if len(low_sa) == 1:
    t_sa = f"The lowest sugar alcohol in the lineup at {fnum(SA_MIN)}g"
else:
    t_sa = f"{'Both' if len(low_sa) == 2 else 'All ' + num_word(len(low_sa))} tie for the lowest sugar alcohol in the lineup at {fnum(SA_MIN)}g"
if low_sa_skipped:
    t_sa += (f". {names_and(nm(b) for b in low_sa_skipped)} also sit{'s' if len(low_sa_skipped) == 1 else ''} at {fnum(SA_MIN)}g but "
             f"carr{'ies' if len(low_sa_skipped) == 1 else 'y'} the Processed Oils flag that {'this one skips' if len(low_sa) == 1 else 'these skip'}, "
             f"so {'it is' if len(low_sa_skipped) == 1 else 'they are'} left off this pick.")
else:
    t_sa += '.'

MAXP = max(map(P, QB))
top_p = [b for b in QB if P(b) == MAXP]
pick_p = min(top_p, key=lambda b: (band_rank(b), po(b), lil(b), nm(b)))
others_p = [b for b in top_p if b is not pick_p]
if others_p:
    extra_flags = [f for f, fn in [('Processed Oils', po), ('Long Ingredient List', lil)]
                   if all(fn(b) for b in others_p) and not fn(pick_p)]
    t_p = f"Ties the lineup's protein ceiling at {fnum(MAXP)}g along with {names_and(nm(b) for b in others_p)}"
    if extra_flags:
        t_p += (f", and it's the only one of the {num_word(len(top_p))} without "
                + ' or '.join(f'a {f} flag' for f in extra_flags) + '.')
    else:
        t_p += f", and it grades {pick_p['score_band']}."
else:
    t_p = f"The most protein in the lineup at {fnum(MAXP)}g, grade {pick_p['score_band']}."

MAXF = max(map(FIB, QB)); MINF = min(map(FIB, QB))
top_f = sorted([b for b in QB if FIB(b) == MAXF], key=lambda b: (band_rank(b), sa(b), nm(b)))
pick_f = top_f[0]
t_f = f"Leads the lineup at {fnum(MAXF)}g of fiber, {fnum(MAXF - MINF)}g above the lineup's low of {fnum(MINF)}g"
t_f += (f", while carrying the lineup's lowest sugar alcohol ({fnum(SA_MIN)}g)." if sa(pick_f) == SA_MIN else '.')

skip = WORST
sa_ties = [b for b in QB if sa(b) == SA_MAX and b is not skip]
t_s = f"The lowest-scoring flavor in the lineup at {fnum(score(skip))}"
if sa(skip) == SA_MAX:
    t_s += (f", and it ties {names_and(nm(b) for b in sa_ties)} for the most sugar alcohol at {fnum(SA_MAX)}g." if sa_ties
            else f", and it carries the most sugar alcohol in the lineup at {fnum(SA_MAX)}g.")
    better = [b for b in sa_ties if band_rank(b) < band_rank(skip) and not po(b)]
    if better and po(skip):
        t_s += (f" Unlike {names_and(nm(b) for b in better)}, which grade{'s' if len(better) == 1 else ''} {better[0]['score_band']}, "
                f"{nm(skip)} also carries the Processed Oils flag.")
else:
    t_s += '.'

PICK_TILES = '\n'.join([
    brand_pick_tile('Lowest sugar alcohol', low_sa, t_sa),
    brand_pick_tile('Most protein per bar', [pick_p], t_p),
    brand_pick_tile('Most fiber', [pick_f], t_f),
    brand_pick_tile('What to skip', [skip], t_s, buy=False),
])

# ---------------------------------------------------------------------------
# Cross-brand alternatives to the protein pick
# ---------------------------------------------------------------------------
FLAG = pick_p
FB = band_rank(FLAG)
def sa_txt(b):
    return 'zero' if sa(b) == 0 else f'{fnum(sa(b))}g'
ALTS = pick_alternatives(ALL, FLAG, {BRAND}, ALT_KEYWORD, [
    ('Same flavor, cleaner label',
     lambda b: nm(b).lower() == nm(FLAG).lower() and band_rank(b) < FB and P(b) >= 10 and not has_tag(b, 'Artificial Sweeteners'),
     lambda b: (band_rank(b), -P(b)),
     lambda b: (f"The exact same flavor name. {grade_vs(FLAG, b)} Sugar alcohol drops to {sa_txt(b)} (from {fnum(sa(FLAG))}g), "
                "with no artificial sweeteners. "
                + (f"Same {fnum(P(b))}g protein" if P(b) == P(FLAG) else f"{fnum(P(b))}g protein vs. {fnum(P(FLAG))}g")
                + (" at the same calories." if CAL(b) == CAL(FLAG) else f", at {cal_delta(FLAG, b)}."))),
    ('No sugar alcohol, similar protein',
     lambda b: sa(b) == 0 and P(b) >= P(FLAG) - 1 and CAL(b) <= CAL(FLAG) + 30 and band_rank(b) <= FB and not has_tag(b, 'Artificial Sweeteners'),
     lambda b: (CAL(b), -P(b)),
     lambda b: (f"{fnum(P(b))}g protein vs. {fnum(P(FLAG))}g at {cal_delta(FLAG, b)}, with zero sugar alcohol (from {fnum(sa(FLAG))}g) "
                f"and no artificial sweeteners. {grade_vs(FLAG, b)}")),
    ('Fewest calories',
     lambda b: band_rank(b) < FB and sa(b) == 0 and P(b) >= 10 and CAL(b) < CAL(FLAG),
     lambda b: (CAL(b), -P(b)),
     lambda b: (f"Only {fnum(CAL(b))} calories, {fnum(CAL(FLAG) - CAL(b))} fewer than {nm(FLAG)}, with zero sugar alcohol. {grade_vs(FLAG, b)}"
                + (f" Protein drops to {fnum(P(b))}g from {fnum(P(FLAG))}g." if P(b) < P(FLAG) else ''))),
], cal_window=60)
ALTS_HTML = f'''<h2>Like {esc(nm(FLAG))}? These are worth a look too</h2>
    <p>{esc(nm(FLAG))} is Quest's top protein pick, but it grades {FLAG['score_band']} with {fnum(sa(FLAG))}g of sugar alcohol. {num_word(len(ALTS)).capitalize()} ways to trade up depending on what matters most to you.</p>
    <div class="macro-grid pick-tile-grid">
{chr(10).join(alt_tile(*a) for a in ALTS)}
    </div>'''

# ---------------------------------------------------------------------------
# Comparison, related reading
# ---------------------------------------------------------------------------
GROUPS = [(BRAND, QB)] + [(n, [b for b in ALL if b['Brand Name'] == n]) for n in COMPARE]
for n, g in GROUPS:
    C.check(len(g) > 0, f'{n} exists in bars.js for the comparison table')
COMPARE_HTML = compare_section_html(BRAND, GROUPS, compare_note(BRAND, GROUPS))
RX = dict(GROUPS)['RXBAR']
BB = dict(GROUPS)['Barebells']
C.check(not any(has_tag(b, 'Artificial Sweeteners') for b in RX), 'RXBAR has no artificial sweeteners')
C.check(avg(RX, 'Protein (g)') < PRO['avg'], 'RXBAR averages less protein than Quest')
RELATED = '''
      <a href="/rxbar-review" class="explore-more-card">
        <div class="explore-more-title">RXBAR Review</div>
        <div class="explore-more-desc">Cleaner ingredients with no artificial sweeteners, but lower protein than Quest. See how the full lineup scores.</div>
      </a>
      <a href="/quest-vs-rxbar" class="explore-more-card">
        <div class="explore-more-title">Quest vs. RXBAR</div>
        <div class="explore-more-desc">Head-to-head comparison of ingredient quality, macros, and value. Which one actually wins for your goals?</div>
      </a>
      <a href="/no-artificial-sweeteners" class="explore-more-card">
        <div class="explore-more-title">No Artificial Sweeteners Guide</div>
        <div class="explore-more-desc">If sucralose is a dealbreaker, here are the best high-protein bars that use only natural sweeteners.</div>
      </a>
    '''

# ---------------------------------------------------------------------------
# Copy
# ---------------------------------------------------------------------------
H1_TEXT = f"Are Quest Bars Healthy? What's Really In All {N} Flavors"
H1_HTML = f"Are <em>Quest</em> Bars Healthy? What's Really In All {N} Flavors"
DESC = ("Quest bars beat most bars on protein and fiber, but every flavor has sucralose and erythritol. "
        "See how each flavor scores and what that means for you.")
C.check(PRO['top'] <= 33 and FIBS['top'] <= 33, 'Quest beats most bars on protein and fiber')
C.check(len(DESC) <= 160, 'meta description length')

a_line = ' and no flavor currently reaching an A' if NO_A else ''
HERO_SUB = (f"Quest bars rank in the top {FIBS['top']}% for fiber and top {PRO['top']}% for protein across 1,000+ bars we've scored. "
            f"Every flavor earns {'a' if GRADES_PRESENT[0] != 'A' else 'an'} {GR_OR} ingredient grade, with scores ranging from "
            f"{fnum(score(WORST))} to {fnum(score(BEST))}{a_line}. The catch: every single flavor also contains artificial sweeteners "
            "and sugar alcohols, no exceptions. The data below shows exactly where Quest stands, flavor by flavor.")

MACRO = f'''<h2>How Quest ranks on macros</h2>
    <p>Rather than labeling macros good or bad, we rank Quest against every bar in our database so you can judge relative to the full market.</p>
{MACRO_HTML}
    <p class="macro-summary-text">Quest's standout numbers are fiber and protein efficiency: averaging {g1(FIBS['avg'])}g of fiber and {g1(P100S['avg'])}g of protein per 100 calories puts it in the top {FIBS['top']}% and top {P100S['top']}% of all bars we track, respectively. The tradeoff is sugar alcohol: at {g1(SAS['avg'])}g average, Quest carries more sugar alcohol than {100 - SAS['beats']}% of bars in the database, which keeps sugar low but can affect digestion for some people.</p>'''

def rng(fn, unit=''):
    lo, hi = min(map(fn, QB)), max(map(fn, QB))
    return f'{fnum(lo)}{unit}' if lo == hi else f'{fnum(lo)} to {fnum(hi)}{unit}'
ov1 = (f"Quest's lineup is one of the most consistent we've scored. All {N} flavors lead with the same milk protein isolate and whey "
       f"protein isolate blend, all {N} use erythritol as the primary sweetener, and every flavor contains sucralose. Macros barely move "
       f"flavor to flavor: {rng(P, 'g')} of protein, {rng(SUG, 'g')} of sugar, {rng(CAL)} calories. Every flavor also clears our bar "
       "for a genuine protein source.")
po_c = [b for b in REST if po(b)]
nopo_rest = [b for b in REST if not po(b)]
ov2 = (f"Where flavors actually differ is additive load, not protein or sweetener choice. {len(PO_BARS)} of {N} flavors add palm kernel oil, "
       f"which trips our Processed Oils flag, and none of them grades above {REST[0]['score_band']}. {names_and(nm(b) for b in TOP_BAND)} "
       f"skip it and land at the top of the lineup."
       + (f" {names_and(nm(b) for b in nopo_rest)} skip{'s' if len(nopo_rest) == 1 else ''} it too but still grade{'s' if len(nopo_rest) == 1 else ''} "
          f"{nopo_rest[0]['score_band']}." if nopo_rest else '')
       + f" That split shows up in the grade distribution: {GC[best_g]} flavors grade {best_g}, the other {len(REST)} sit at "
       f"{' or '.join(g for g in GRADES_PRESENT if g != best_g)}" + (', and none currently reach an A.' if NO_A else '.'))
C.check(all(band_rank(b) >= band_rank(REST[0]) for b in PO_BARS), 'every processed-oil flavor grades below the top tier')
OVERVIEW = f'''<h2>What the data shows across all {N} Quest flavors</h2>
    <p>{esc(ov1)}</p>
    <p>{esc(ov2)}</p>'''

GRADES = f'''<h2>Ingredient quality grade distribution across all {N} flavors</h2>
    <p>Here is how Quest's full lineup grades out. This is every flavor we've scored, not a hand-picked few.</p>
{grade_dist_html(QB)}'''

BESTWORST = f'''<h2>Best and worst flavors by ingredient quality</h2>
    <div class="bestworst">
{bw_card_html(BEST, True)}
{bw_card_html(WORST, False)}
    </div>'''

pat = ["Quality Protein Source shows up in all {N} flavors, since the milk protein isolate and whey protein isolate blend never changes.".format(N=N),
       f"On the concern side, Artificial Sweeteners and Sugar Alcohols hit every flavor, though sugar alcohol severity varies: "
       f"{sa_sev['minor']} flavors carry it at a minor level and {sa_sev['elevated']} at elevated."]
pat.append(f"Processed Oils flags {len(PO_BARS)} of {N} flavors, all of them "
           f"{' or '.join(sorted({b['score_band'] for b in PO_BARS}, key=BAND_ORDER.index))}-grade, and none of the {len(TOP_BAND)} {best_g}-grade flavors carries it.")
lil_bars = [b for b in QB if lil(b)]
if lil_bars:
    lil_g = sorted({b['score_band'] for b in lil_bars}, key=BAND_ORDER.index)
    pat.append(f"A Long Ingredient List flags {len(lil_bars)} of {N} flavors" + (f", all of them in the {lil_g[0]} tier" if len(lil_g) == 1 else '')
               + (", tracking with the same more complex recipes that trip the Processed Oils flag." if all(po(b) for b in lil_bars) else '.'))
PATTERNS = f'''<h2>Ingredient quality patterns across the Quest lineup</h2>
    <p>Every Quest flavor shares a core ingredient profile, with additive load the main thing that changes flavor to flavor. Here is what the data shows across all {N} flavors, split by whether it counts in a bar's favor or against it.</p>

{chip_patterns_html(QB)}

    <p style="margin-top:1.25rem;">{esc(' '.join(pat))}</p>'''

TABLE_HEADING = f'''<h2>All {N} Quest flavors ranked by ingredient quality</h2>
    <p>Every flavor, every grade, every key macro. Sorted from cleanest to most processed. Tap any row to see the full ingredient list, macros, and buy links.</p>'''

bl1 = (f"Quest earns its reputation as a high-protein, low-sugar bar. Averaging {g1(FIBS['avg'])}g of fiber per bar is a genuine standout "
       f"in any category, ranking in the top {FIBS['top']}% of bars we track. But the ingredient quality grades tell a more mixed story than "
       f"the marketing suggests: {GC[best_g]} of {N} flavors land at {best_g}, the other {len(REST)} at "
       f"{' or '.join(g for g in GRADES_PRESENT if g != best_g)}" + (', and none currently reach an A.' if NO_A else '.'))
bl2 = ("The limitation is just as consistent: artificial sweeteners and sugar alcohols in every flavor, no exceptions. If those ingredients "
       "are a dealbreaker, Quest is not your bar regardless of which flavor you pick. If you are fine with sucralose and erythritol and you "
       "are prioritizing protein and fiber per calorie, Quest is still one of the more macro-efficient options in our database. "
       f"Start with {names_and(nm(b) for b in TOP_BAND)}. {'These ' + num_word(len(TOP_BAND)) + ' score' if len(TOP_BAND) > 1 else 'It scores'} "
       f"highest in the lineup, and none of them carries a processed oil.")
BOTTOM = f'''<h2>Bottom line on Quest</h2>
    <p>{esc(bl1)}</p>
    <p>{esc(bl2)}</p>'''

PICKS = f'''<h2>Which Quest flavor should you actually buy</h2>
    <p>Every flavor here clears the bar for a genuine protein source and shares the same {GR_OR} ceiling, so these picks come down to secondary tradeoffs: sugar alcohol load, protein ceiling, fiber, and what to skip outright.</p>
    <div class="macro-grid pick-tile-grid">
{PICK_TILES}
    </div>'''

bb_as = all(has_tag(b, 'Artificial Sweeteners') for b in BB)
FAQS = [
    ('Are Quest bars healthy?',
     f"Quest bars score {GR_OR} on ingredient quality across all {N} flavors, with scores ranging from {fnum(score(WORST))} to {fnum(score(BEST))}. "
     f"They rank in the top {FIBS['top']}% for fiber and top {PRO['top']}% for protein across 1,000+ bars we track. Every flavor contains an "
     f"artificial sweetener (sucralose) and a sugar alcohol (erythritol). Whether that matters depends on your dietary goals."),
    ('Which Quest flavor is the healthiest?',
     f"{nm(BEST)} scores highest at {fnum(score(BEST))} ({BEST['score_band']}, {grade_word(BEST['score_band'])}), followed by {nm(SECOND)} at "
     f"{fnum(score(SECOND))} and {nm(THIRD)} at {fnum(score(THIRD))}."
     + (" None of the three carries a processed oil." if not any(po(b) for b in (BEST, SECOND, THIRD)) else '')
     + f" The lowest scorer, {nm(WORST)} at {fnum(score(WORST))} ({WORST['score_band']}, {grade_word(WORST['score_band'])})"
     + (", adds palm kernel oil" if has_ing(WORST, 'palm kernel oil') else '')
     + (f" and {'ties for' if sa_ties else 'carries'} the most sugar alcohol in the lineup." if sa(WORST) == SA_MAX else '.')),
    ('Do Quest bars have artificial sweeteners?',
     f"Yes. Every Quest bar contains sucralose, and {n_stevia} of {N} flavors also use stevia, a plant-based sweetener. There are no Quest "
     "flavors without artificial sweeteners. Quest uses them to keep sugar very low, which is the main reason some people avoid the brand."),
    ('How much protein do Quest bars have?',
     f"Quest bars contain {rng(P)}g of protein per bar, averaging {g1(PRO['avg'])}g. That puts them in the top {PRO['top']}% for protein across "
     "all bars in our database. The protein source is a blend of milk protein isolate and whey protein isolate, both complete animal-based proteins."),
    ('Do Quest bars have sugar alcohols?',
     f"Yes. Every Quest bar contains erythritol, {rng(sa)}g per bar. Erythritol is generally better tolerated than other sugar alcohols but can "
     f"still cause digestive discomfort in some people. It's what allows Quest to keep total sugar at just {rng(SUG)}g per bar."),
    ('How do Quest bars compare to other protein bars?',
     f"Quest ranks in the top {FIBS['top']}% for fiber and top {PRO['top']}% for protein across 1,000+ bars. Every flavor scores {GR_OR}"
     + (', with no A grades currently in the lineup.' if NO_A else '.')
     + " The main tradeoff versus RXBAR is sucralose in every flavor, since RXBAR uses no artificial sweeteners."
     + (" Barebells shares the same tradeoff: sucralose in every flavor, with maltitol instead of erythritol." if bb_as and all(has_ing(b, 'maltitol') for b in BB) else '')),
    ('What type of protein is in Quest bars?',
     "Quest uses a blend of milk protein isolate and whey protein isolate. Both come from dairy, are complete proteins, and have strong amino "
     "acid profiles. Quality protein sources like these score well in our ingredient scoring system, which is why every Quest flavor carries "
     "the Quality Protein Source chip."),
]

regions = [
    ('head-meta', head_meta_html(H1_TEXT, DESC)),
    ('jsonld-article', article_jsonld(H1_TEXT, DESC, URL, 'Quest Nutrition', 'https://www.questnutrition.com')),
    ('jsonld-faq', faq_jsonld_brand(FAQS)),
    ('social', social_html(H1_TEXT, DESC, URL)),
    ('hero', f'<h1 class="hero-title">{H1_HTML}</h1>\n    <p class="hero-sub">{esc(HERO_SUB)}</p>'),
    ('macro', MACRO), ('overview', OVERVIEW), ('grades', GRADES), ('bestworst', BESTWORST), ('patterns', PATTERNS),
    ('table-heading', TABLE_HEADING), ('table-rows', brand_table_html(QB, ALL)), ('bottom', BOTTOM), ('picks', PICKS),
    ('alts', ALTS_HTML), ('related', RELATED), ('compare', COMPARE_HTML), ('faq', faq_items_brand(FAQS)),
]
n_rows = build_brand_page(PAGE, regions, QB, ALL, C)
print(f'{PAGE}: {N} flavors, grades {range_words(QB)} ({grade_counts_txt(QB, " ")})')
print(f'Best {nm(BEST)} {BEST["score_band"]} {fnum(score(BEST))} | Worst {nm(WORST)} {WORST["score_band"]} {fnum(score(WORST))}')
print('Picks:', ', '.join(map(nm, low_sa)), '|', nm(pick_p), '|', nm(pick_f), '| skip', nm(skip))
print('Alternatives:', ' | '.join(f"{a[0]}: {a[1]['Brand Name']} {a[1]['Flavor Name']} ({a[1]['score_band']})" for a in ALTS))
print(f'Grade-sync: {n_rows} flavor rows, best/worst cards and alternative tiles checked against bars.js, 0 mismatches')
