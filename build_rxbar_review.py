#!/usr/bin/env python3
"""
Rebuild the data on rxbar-review.html from live bars.js.

    python3 build_rxbar_review.py

Opens the live page and rewrites only the <!-- kyb:NAME --> regions (see
kyb_guide_lib.py / kyb_brand_lib.py). Nav, footer, fonts, canonical URL, the
Explore CTA and the brand-link pills are never touched.

RXBAR's three flavor groups are defined from ingredient text, never labels:
  - high-protein pair: contains pea protein (agave nectar sweetened)
  - oats-and-honey:    no pea protein, contains oats
  - original:          everything else (dates first, egg whites)
Structural claims go through claims.check(); the build stops if one fails.
"""
from collections import defaultdict
from kyb_brand_lib import *

PAGE = 'rxbar-review.html'
BRAND = 'RXBAR'
URL = 'https://knowyourbar.com/rxbar-review'
COMPARE = ['Quest', 'Barebells', 'Clif Builders', 'KIND']

ALL = load_bars()
RB = sort_for_list([b for b in ALL if b['Brand Name'] == BRAND])
N = len(RB)
C = Claims()

HP = [b for b in RB if has_ing(b, 'pea protein')]
OH = [b for b in RB if b not in HP and has_ing(b, 'oat')]
OR = [b for b in RB if b not in HP and b not in OH]
C.check(len(HP) and len(OH) and len(OR), 'RXBAR still has all three flavor groups')
C.check(all(ingr(b).lower().startswith('date') and has_ing(b, 'egg white') for b in OR), 'original bars lead with dates and use egg whites')
C.check(all(has_ing(b, 'agave') for b in HP), 'high-protein pair uses agave nectar')
C.check(all(has_ing(b, 'honey') for b in OH), 'oats group uses honey')
C.check(all(has_ing(b, 'date') or has_ing(b, 'honey') or has_ing(b, 'agave') for b in RB), 'every flavor is sweetened with dates, honey or agave')
C.check(no_as_sa(RB) and all(sa(b) == 0 for b in RB), 'RXBAR has zero artificial sweeteners and sugar alcohols')

MACRO_GRID, ST = macro_grid_html(RB, ALL)
PRO, SUGS, FIBS, P100S = ST['protein'], ST['sugar'], ST['fiber'], ST['p100']
BEST, WORST = RB[0], RB[-1]
GC = grade_counts(RB)
GRADES_PRESENT = [g for g in BAND_ORDER if GC[g]]
best_g, worst_g = grade_range(RB)
GR = range_words(RB)
C.check(best_g == 'A', 'RXBAR still has A-grade flavors')

by = defaultdict(list)
for b in ALL:
    by[b['Brand Name']].append(b)
ranked = sorted([(avg(v, 'ingredient_score'), k) for k, v in by.items() if len(v) >= 5], reverse=True)
BRAND_RANK, BRAND_POOL = [k for _, k in ranked].index(BRAND) + 1, len(ranked)
top_brand = BRAND_RANK <= max(10, BRAND_POOL // 10)

def g(bars):
    sc = [score(b) for b in bars]
    ps = sorted(set(map(P, bars)))
    return dict(n=len(bars), lo=min(sc), hi=max(sc), rng=range_words(bars), p=ps,
                ptxt=f'{fnum(ps[0])}g' if len(ps) == 1 else f'{fnum(ps[0])} to {fnum(ps[-1])}g',
                sh=sum(1 for b in bars if has_tag(b, 'Sweetener Heavy')))
GO, GH, GOH = g(OR), g(HP), g(OH)
strongest = max([('original', GO), ('oats', GOH), ('hp', GH)], key=lambda x: x[1]['hi'])[0]
C.check(GO['sh'] == 0 and GH['sh'] == GH['n'] and GOH['sh'] == GOH['n'],
        'Sweetener Heavy hits every high-protein and oats flavor and none of the originals')
C.check(max(GH['p']) > max(GO['p']) >= max(GOH['p']), 'high-protein pair carries the most protein, oats group the least')

def sc_rng(x): return f"{g1(x['lo'])} to {g1(x['hi'])}" if x['lo'] != x['hi'] else g1(x['lo'])
def names3(bars):
    names = [nm(b) for b in bars]
    return names_and(names) if len(names) <= 3 else f"{', '.join(names[:3])}, and {num_word(len(names) - 3)} others"

# ---------------------------------------------------------------------------
# Picks
# ---------------------------------------------------------------------------
N_ING = top_level_ingredient_count
min_n = min(N_ING(ingr(b)) for b in RB if b['score_band'] == best_g)
# Among the flavors tied for the shortest list, prefer one that isn't already another tile's pick
_other_picks = {nm(b) for b in RB if CAL(b) == min(map(CAL, RB)) or FIB(b) == max(map(FIB, RB)) or P(b) == max(map(P, RB))}
clean = min([b for b in RB if b['score_band'] == best_g],
            key=lambda b: (N_ING(ingr(b)), nm(b) in _other_picks, -(score(b) or 0), nm(b)))
tied_n = [b for b in RB if N_ING(ingr(b)) == N_ING(ingr(clean))]
t_clean = (f"{N_ING(ingr(clean))} ingredients, dates first, no pea protein or agave. "
           + ("Tied for the shortest list in the lineup" if len(tied_n) > 1 else "The shortest list in the lineup")
           + f" and it grades {clean['score_band']}.")
C.check(clean in OR, 'the cleanest pick is an original date-based bar')
MAXP = max(map(P, RB))
top_p = sorted([b for b in RB if P(b) == MAXP], key=lambda b: (band_rank(b), nm(b)))
second_p = max(P(b) for b in RB if P(b) < MAXP)
gf_k = [b for b in RB if b.get('Gluten Free (Y/N)') == 'Yes' and b.get('Kosher (Y/N)') == 'Yes']
t_p = (f"{fnum(MAXP)}g protein, the highest in the lineup by {fnum(MAXP - second_p)}g, from pea protein plus peanuts. "
       + (f"Both grade {top_p[0]['score_band']}" if len(top_p) == 2 and top_p[0]['score_band'] == top_p[1]['score_band'] else f"They grade {' and '.join(b['score_band'] for b in top_p)}")
       + " because agave nectar shows up early"
       + (", but they're the only two flavors certified gluten-free and kosher." if set(map(nm, gf_k)) == set(map(nm, top_p)) else '.'))
MINC = min(map(CAL, RB))
low_c = sorted([b for b in RB if CAL(b) == MINC], key=lambda b: (band_rank(b), nm(b)))
lc = low_c[0]
t_c = (f"{fnum(MINC)} calories with {fnum(P(lc))}g protein and {fnum(FIB(lc))}g fiber, the lowest calorie count in the lineup"
       + (" without giving up protein or fiber" if P(lc) >= PRO['avg'] - 1 and FIB(lc) >= FIBS['avg'] else '') + f". Grades {lc['score_band']}.")
MAXF = max(map(FIB, RB))
top_f = sorted([b for b in RB if FIB(b) == MAXF], key=lambda b: (band_rank(b), nm(b)))
fg = sorted({b['score_band'] for b in top_f}, key=BAND_ORDER.index)
t_f = ((f"{'Both hit' if len(top_f) == 2 else 'All ' + num_word(len(top_f)) + ' hit'} {fnum(MAXF)}g fiber, tied for the highest in the lineup"
        if len(top_f) > 1 else f"{fnum(MAXF)}g fiber, the highest in the lineup")
       + f", at {'/'.join(sorted({fnum(P(b)) + 'g' for b in top_f}))} protein and {' and '.join(fg)} grade{'s' if len(top_f) > 1 else ''}.")
PICK_TILES = '\n'.join([
    brand_pick_tile('Cleanest ingredients', [clean], t_clean),
    brand_pick_tile('Most protein per bar', top_p, t_p),
    brand_pick_tile('Fewest calories', [lc], t_c),
    brand_pick_tile('Most fiber', top_f, t_f),
])

# ---------------------------------------------------------------------------
# Alternatives keyed to the cleanest-ingredients pick
# ---------------------------------------------------------------------------
FLAG = clean
FB = band_rank(FLAG)
KEY = FLAG['Flavor Name'].lower().split()[0]   # e.g. 'peanut' for Peanut Butter
def noart(b): return not has_tag(b, 'Artificial Sweeteners') and sa(b) == 0
ALTS = pick_alternatives(ALL, FLAG, {BRAND}, KEY, [
    ('More protein',
     lambda b: band_rank(b) <= FB and noart(b) and P(b) >= P(FLAG) + 5,
     lambda b: (-P(b), CAL(b)),
     lambda b: f"{fnum(P(b))}g protein vs. {fnum(P(FLAG))}g here, for {cal_delta(FLAG, b)}. {grade_vs(FLAG, b)}"),
    ('Less sugar',
     lambda b: band_rank(b) <= FB and noart(b) and SUG(b) <= SUG(FLAG) - 8 and P(b) >= P(FLAG) - 2,
     lambda b: (SUG(b), -P(b)),
     lambda b: f"{fnum(SUG(b))}g sugar vs. {fnum(SUG(FLAG))}g here, with {fnum(P(b))}g protein and {cal_delta(FLAG, b)}. {grade_vs(FLAG, b)}"),
    ('More fiber',
     lambda b: band_rank(b) <= FB and noart(b) and FIB(b) >= FIB(FLAG) + 4 and P(b) >= P(FLAG) - 2,
     lambda b: (-FIB(b), -P(b)),
     lambda b: f"{fnum(FIB(b))}g fiber vs. {fnum(FIB(FLAG))}g here, at {fnum(P(b))}g protein and {cal_delta(FLAG, b)}. {grade_vs(FLAG, b)}"),
], cal_window=60)
ALTS_HTML = f'''<h2>Like {esc(nm(FLAG))}? These are worth a look too</h2>
    <p>{esc(nm(FLAG))} is our cleanest-ingredients pick in the RXBAR lineup, but it's not the only clean {esc(KEY)} bar in the database. {num_word(len(ALTS)).capitalize()} ways to trade up depending on what matters most to you, all with no artificial sweeteners or sugar alcohol.</p>
    <div class="macro-grid pick-tile-grid">
{chr(10).join(alt_tile(*a) for a in ALTS)}
    </div>'''

# ---------------------------------------------------------------------------
# Comparison + related
# ---------------------------------------------------------------------------
GROUPS = [(BRAND, RB)] + [(n, [b for b in ALL if b['Brand Name'] == n]) for n in COMPARE]
for n, gg in GROUPS:
    C.check(len(gg) > 0, f'{n} exists in bars.js for the comparison table')
COMPARE_HTML = compare_section_html(BRAND, GROUPS, compare_note(BRAND, GROUPS))
QU, BB = dict(GROUPS)['Quest'], dict(GROUPS)['Barebells']
C.check(avg(QU, 'Protein (g)') > PRO['avg'] and avg(QU, 'Dietary Fiber (g)') > FIBS['avg'], 'Quest has more protein and fiber than RXBAR')
C.check(all(has_ing(b, 'sucralose') and has_ing(b, 'erythritol') for b in QU), 'every Quest flavor uses sucralose and erythritol')
C.check(all(has_tag(b, 'Artificial Sweeteners') or has_tag(b, 'Sugar Alcohols') for b in QU + BB), 'every Quest and Barebells flavor has sucralose or a sugar alcohol')
clean_peers = [n for n, gg in GROUPS if no_as_sa(gg)]
RELATED = '''
      <a href="/quest-bars" class="explore-more-card">
        <div class="explore-more-title">Quest Bars Review</div>
        <div class="explore-more-desc">Higher protein and fiber, but every flavor uses sucralose and erythritol. See how the full lineup scores head-to-head.</div>
      </a>
      <a href="/quest-vs-rxbar" class="explore-more-card">
        <div class="explore-more-title">Quest vs. RXBAR</div>
        <div class="explore-more-desc">Head-to-head comparison of ingredient quality, macros, and value. Which one actually wins for your goals?</div>
      </a>
      <a href="/no-artificial-sweeteners" class="explore-more-card">
        <div class="explore-more-title">No Artificial Sweeteners Guide</div>
        <div class="explore-more-desc">RXBAR is one of the cleanest brands on this list. See how it stacks up against every other bar that skips synthetic sweeteners.</div>
      </a>
    '''

# ---------------------------------------------------------------------------
# Copy
# ---------------------------------------------------------------------------
H1_TEXT = f'Are RXBAR Bars Actually Healthy? We Checked All {N} Flavors'
H1_HTML = f'Are <em>RXBAR</em> Bars Actually Healthy? We Checked All {N} Flavors'
DESC = ("We checked the ingredient label on every RXBAR flavor. Most come back an A, real food, no artificial sweeteners or "
        "sugar alcohol. See how each one scores.")
C.check(GC['A'] > N / 2, 'most RXBAR flavors grade A')

grade_line = f"{GC['A']} of {N} flavors earn an A" + (f", and the other {N - GC['A']} land at {' or '.join(g for g in GRADES_PRESENT if g != 'A')}" if N > GC['A'] else '')
HERO_SUB = ((f"RXBAR's average ingredient score ranks #{BRAND_RANK} of the {BRAND_POOL} brands we track with five or more flavors: " if top_brand
             else "RXBAR grades well on ingredient quality: ")
            + f"{grade_line}, for a full {GR} range. Every flavor skips artificial sweeteners and sugar alcohols entirely, leaning on "
            f"dates, honey, or agave nectar instead. The tradeoff shows up in the macros, not the ingredients: protein and fiber land in the "
            f"middle of the pack, and average sugar runs higher than {100 - SUGS['beats']}% of bars we've scored. The data below shows exactly "
            "where RXBAR stands, flavor by flavor.")
C.check(SUGS['beats'] <= 25 and 25 < PRO['beats'] < 75 and 25 < FIBS['beats'] < 75, 'RXBAR protein/fiber mid-pack and sugar in the bottom quarter')

MACRO = f'''<h2>How RXBAR ranks on macros</h2>
    <p>Rather than labeling macros good or bad, we rank RXBAR against every bar in our database so you can judge relative to the full market.</p>
{MACRO_GRID}
    <p class="macro-summary-text">{esc(f"RXBAR's standout number is what's absent: zero grams of sugar alcohol and zero artificial sweeteners across every flavor, a combination only {names_and(clean_peers)} manage in our brand comparison below. The tradeoff is average sugar at {g1(SUGS['avg'])}g per bar, all from whole-food sources, which still ranks in the bottom {SUGS['beats']}% of the database since most bars use sugar alcohols or artificial sweeteners to keep sugar low. Protein ({g1(PRO['avg'])}g avg) and fiber ({g1(FIBS['avg'])}g avg) both land close to the database median.")}</p>'''

ov1 = (f"RXBAR's lineup is built around whole-food protein and natural sweeteners instead of protein isolates and sugar alcohols. "
       f"None of the {N} flavors contain sucralose, erythritol, or any other artificial sweetener or sugar alcohol, and that consistency "
       f"shows up in the grades: {GC['A']} flavors land at A" + (f", the other {N - GC['A']} at {' or '.join(g for g in GRADES_PRESENT if g != 'A')}" if N > GC['A'] else '')
       + ", and nothing scores lower.")
ov2 = (f"The lineup splits into three groups by protein source, even though RXBAR doesn't label them as separate lines. "
       f"{GO['n']} original whole-food bars ({names3(OR)}) lead with dates and egg whites, carry {GO['ptxt']} protein, and score {sc_rng(GO)}"
       + (", the strongest range in the lineup" if strongest == 'original' else '') + ". None of them trips the Sweetener Heavy flag. "
       f"A higher-protein pair ({names_and(nm(b) for b in HP)}) swaps in pea protein and agave nectar to push protein up to {GH['ptxt']}, "
       f"the highest in the lineup, but that agave shows up early enough in the ingredient list to trip our Sweetener Heavy check, and both grade "
       f"{GH['rng']}. A third group of {GOH['n']} oats-and-honey flavors ({names_and(nm(b) for b in OH)}) carries the least protein at "
       f"{GOH['ptxt']} and also trips Sweetener Heavy, this time on honey, yet scores {sc_rng(GOH)}"
       + (", the highest in the lineup." if strongest == 'oats' else ", right alongside the original bars."))
OVERVIEW = f'''<h2>What the data shows across all {N} RXBAR flavors</h2>
    <p>{esc(ov1)}</p>
    <p>{esc(ov2)}</p>'''

GRADES = f'''<h2>Ingredient quality grade distribution across all {N} flavors</h2>
    <p>Here is how RXBAR's full lineup grades out. This is every flavor we've scored, not a hand-picked few.</p>
{grade_dist_html(RB)}'''

BESTWORST = f'''<h2>Best and worst flavors by ingredient quality</h2>
    <div class="bestworst">
{bw_card_html(BEST, True)}
{bw_card_html(WORST, False)}
    </div>'''

SH = sum(1 for b in RB if has_tag(b, 'Sweetener Heavy'))
pat = (f"Sweetener Heavy is the only concern chip in the lineup, flagging {SH} of {N} flavors: both high-protein flavors (agave nectar) and all "
       f"{num_word(GOH['n'])} oats-and-honey flavors (honey). None of the {GO['n']} date-sweetened originals carries it. "
       "Nothing in the RXBAR lineup contains an artificial sweetener or a sugar alcohol, which is the main reason the grades run as high as they do.")
C.check([k for k, v in chip_freq(RB).items() if v[1] == 'concern'] == ['Sweetener Heavy'], 'Sweetener Heavy is the only RXBAR concern chip')
PATTERNS = f'''<h2>Ingredient quality patterns across the lineup</h2>
    <p>RXBAR's flavors share a whole-food ingredient base, with variation in which natural sweetener leads the list. Here is what the data shows across all {N} flavors, grouped by whether it helps or hurts the score.</p>

{chip_patterns_html(RB)}

    <p style="margin-top:1.25rem;">{esc(pat)}</p>'''

TABLE_HEADING = f'''<h2>All {N} RXBAR flavors ranked by ingredient quality</h2>
    <p>Every flavor, every grade, every key macro. Sorted from cleanest to most processed. Tap any row to see the full ingredient list, macros, and buy links.</p>'''

bl1 = (f"RXBAR earns its reputation as one of the cleanest lineups we score. Zero artificial sweeteners, zero sugar alcohols, and {GC['A']} of "
       f"{N} flavors land at A. Compare that to Quest or Barebells, where every flavor carries sucralose or a sugar alcohol, and RXBAR's "
       "ingredient list advantage is real, not marketing.")
bl2 = (f"The tradeoff is macros, not ingredients. At {g1(PRO['avg'])}g protein and {g1(FIBS['avg'])}g fiber per bar on average, RXBAR sits in "
       f"the middle of our database on both, well behind protein-forward brands like Quest. Sugar averages {g1(SUGS['avg'])}g per bar, mostly "
       f"from dates, honey, or agave, which ranks in the bottom {SUGS['beats']}% of bars we track for sugar content. Which flavor makes sense for "
       "you depends more on which of RXBAR's three flavor groups fits your goal than on any single \"best\" bar. See the picks below.")
BOTTOM = f'''<h2>Bottom line on RXBAR</h2>
    <p>{esc(bl1)}</p>
    <p>{esc(bl2)}</p>'''

PICKS = f'''<h2>Which RXBAR flavor should you actually buy</h2>
    <p>Since the {N} flavors split across three flavor groups, "best" depends on what you're optimizing for. Here's how the data points by goal.</p>
    <div class="macro-grid pick-tile-grid">
{PICK_TILES}
    </div>'''

second, third = RB[1], RB[2]
qp, qf = avg(QU, 'Protein (g)'), avg(QU, 'Dietary Fiber (g)')
FAQS = [
    ('Are RXBAR bars healthy?',
     f"RXBAR grades {' or '.join(GRADES_PRESENT)} on ingredient quality across all {N} flavors, and {GC['A']} of the {N} land at A. Every flavor "
     f"skips artificial sweeteners and sugar alcohols, relying on dates, honey, or agave nectar instead. The tradeoff is average protein "
     f"({g1(PRO['avg'])}g) and fiber ({g1(FIBS['avg'])}g) that land in the middle of our database, and sugar that runs higher than most bars "
     "because it comes from whole-food sources rather than sugar alcohols."),
    ('Which RXBAR flavor is the healthiest?',
     f"{nm(BEST)} scores highest at {g1(score(BEST))}, followed by {nm(second)} at {g1(score(second))} and {nm(third)} at {g1(score(third))}"
     + (f", all three from the oats-and-honey group, built around oats, honey, and egg whites rather than dates."
        if all(b in OH for b in (BEST, second, third)) else '.')
     + f" The two lowest-graded flavors, {names_and(nm(b) for b in RB[-2:])}, land at {' and '.join(sorted({b['score_band'] for b in RB[-2:]}))} "
     "because agave nectar appears early in their ingredient lists, even though neither contains anything artificial. They also carry the most "
     "protein in the lineup, so the healthiest pick depends on whether you're optimizing for ingredient quality or protein."),
    ('Do RXBAR bars have artificial sweeteners?',
     f"No. None of the {N} RXBAR flavors we've scored contain artificial sweeteners. RXBAR sweetens every flavor with dates, honey, or agave "
     "nectar instead of sucralose, aspartame, or acesulfame potassium. This is one of the biggest reasons RXBAR grades as well as it does in our system."),
    ('Do RXBAR bars have sugar alcohols?',
     f"No. Zero of the {N} flavors contain sugar alcohols like erythritol, maltitol, or xylitol. That's part of why RXBAR's sugar counts run "
     f"higher than brands like Quest, which uses sugar alcohols to keep sugar near zero. RXBAR's sugar averages {g1(SUGS['avg'])}g per bar, "
     "mostly from dates, honey, or agave."),
    ('How much protein do RXBAR bars have?',
     f"RXBAR bars contain {fnum(PRO['lo'])} to {fnum(PRO['hi'])}g of protein per bar, averaging {g1(PRO['avg'])}g, which lands in the middle "
     f"of the 1,000+ bars we track. Protein depends on which of RXBAR's three flavor groups a bar belongs to: the original whole-food lineup "
     f"uses egg whites and carries {GO['ptxt']}, the oats-and-honey group runs lower at {GOH['ptxt']}, and the high-protein pair "
     f"({names_and(nm(b) for b in HP)}) adds pea protein and reaches {GH['ptxt']}."),
    ('How do RXBAR bars compare to other protein bars?',
     f"RXBAR ranks near the top of our database on ingredient quality, with {GC['A']} of {N} flavors grading A and zero artificial sweeteners "
     f"or sugar alcohols anywhere in the lineup. The tradeoff versus protein-forward brands like Quest is macros: RXBAR's protein "
     f"({g1(PRO['avg'])}g avg) and fiber ({g1(FIBS['avg'])}g avg) trail Quest's {g1(qp)}g protein and {g1(qf)}g fiber by a wide margin, "
     f"and RXBAR's sugar runs higher than {100 - SUGS['beats']}% of bars we track."),
    ('Does RXBAR have different product lines?',
     f"Not officially, but the ingredient data splits the {N} flavors into three clear groups. {GO['n']} flavors ({names3(OR)}) are the "
     f"original whole-food bars: dates, egg whites, a short ingredient list, and scores of {sc_rng(GO)}. {GH['n']} flavors "
     f"({names_and(nm(b) for b in HP)}) are a high-protein pair built around pea protein and agave nectar, trading a grade step down to "
     f"{GH['rng']} for {fnum(max(GH['p']) - max(GO['p']))}g more protein per bar. The remaining {GOH['n']} flavors are an oats-and-honey group "
     f"with the lowest protein in the lineup at {GOH['ptxt']}, but they score {sc_rng(GOH)}"
     + (", the highest in the lineup." if strongest == 'oats' else ", right alongside the original bars.")),
]
C.check(all(b in HP for b in RB[-2:]), 'the two lowest-graded flavors are the high-protein pair')

regions = [
    ('head-meta', head_meta_html(H1_TEXT, DESC)),
    ('jsonld-article', article_jsonld(H1_TEXT, DESC, URL, 'RXBAR', 'https://www.rxbar.com', published=None)),
    ('jsonld-faq', faq_jsonld_brand(FAQS)),
    ('social', social_html(H1_TEXT, DESC, URL)),
    ('hero', f'<h1 class="hero-title">{H1_HTML}</h1>\n    <p class="hero-sub">{esc(HERO_SUB)}</p>'),
    ('macro', MACRO), ('overview', OVERVIEW), ('grades', GRADES), ('bestworst', BESTWORST), ('patterns', PATTERNS),
    ('table-heading', TABLE_HEADING), ('table-rows', brand_table_html(RB, ALL)), ('bottom', BOTTOM), ('picks', PICKS),
    ('alts', ALTS_HTML), ('related', RELATED), ('compare', COMPARE_HTML), ('faq', faq_items_brand(FAQS)),
]
n_rows = build_brand_page(PAGE, regions, RB, ALL, C)
print(f'{PAGE}: {N} flavors, grades {GR} ({grade_counts_txt(RB, " ")}), brand rank #{BRAND_RANK} of {BRAND_POOL}')
print(f'Best {nm(BEST)} {BEST["score_band"]} {g1(score(BEST))} | Worst {nm(WORST)} {WORST["score_band"]} {g1(score(WORST))}')
print('Picks:', nm(clean), '|', ', '.join(map(nm, top_p)), '|', nm(lc), '|', ', '.join(map(nm, top_f)))
print('Alternatives:', ' | '.join(f"{a[0]}: {a[1]['Brand Name']} {a[1]['Flavor Name']} ({a[1]['score_band']})" for a in ALTS))
print(f'Grade-sync: {n_rows} flavor rows, best/worst cards and alternative tiles checked against bars.js, 0 mismatches')
