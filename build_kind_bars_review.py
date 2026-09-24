#!/usr/bin/env python3
"""
Rebuild the data on kind-bars-review.html from live bars.js.

    python3 build_kind_bars_review.py

Opens the live page and rewrites only the <!-- kyb:NAME --> regions (see
kyb_guide_lib.py / kyb_brand_lib.py). Nav, footer, fonts, canonical URL, the
Discover CTA and the brand-link pills are never touched.

KIND's three formulas are defined from ingredient text, never from labels:
  - allulose bars:  ingredients contain "allulose" (the four 62g 20g-protein
    bars that used to be sold as KIND Protein Max, plus the 35g Nuts and Sea
    Salt minis)
  - breakfast bars: no allulose, ingredients contain oats AND soy protein
  - classic bars:   everything else (nut-and-fruit bars sweetened with honey,
    cane sugar and glucose syrup)
Structural claims go through claims.check(); the build stops if one fails.
"""
from kyb_brand_lib import *

PAGE = 'kind-bars-review.html'
BRAND = 'KIND'
URL = 'https://knowyourbar.com/kind-bars-review'
COMPARE = ['Quest', 'Barebells', 'RXBAR']
ALT_KEYWORD = 'chocolate'
REVIEWED = {'Quest': ['Quest'], 'Barebells': ['Barebells'], 'RXBAR': ['RXBAR'], 'Clif': ['CLIF Bar', 'Clif Builders', 'Clif ZBar']}   # other brand-review pages

ALL = load_bars()
KB = sort_for_list([b for b in ALL if b['Brand Name'] == BRAND])
N = len(KB)
C = Claims()

AL = [b for b in KB if has_ing(b, 'allulose')]
BR = [b for b in KB if b not in AL and has_ing(b, 'oat') and has_ing(b, 'soy protein')]
CL = [b for b in KB if b not in AL and b not in BR]
MAXP = max(map(P, KB))
AL_BIG = [b for b in AL if P(b) == MAXP]
AL_MINI = [b for b in AL if b not in AL_BIG]
C.check(len(AL_BIG) == 4 and all(num(b.get('Serving Size (g)')) == 62 for b in AL_BIG),
        'the four 20g allulose bars (former Protein Max) are the 62g bars and hold the lineup protein max')
C.check(all(num(b.get('Serving Size (g)')) == 35 for b in AL_MINI), 'the other allulose bars are the 35g minis')
C.check(len(BR) > 0 and len(CL) > 0, 'KIND still has breakfast and classic bars')

MACRO_GRID, ST = macro_grid_html(KB, ALL)
PRO, P100S, FIBS = ST['protein'], ST['p100'], ST['fiber']
BEST, WORST = KB[0], KB[-1]
GR = range_words(KB)
GC = grade_counts(KB)
GRADES_PRESENT = [g for g in BAND_ORDER if GC[g]]
GR_OR = ' or '.join(GRADES_PRESENT)
best_g, worst_g = grade_range(KB)
no_as = not any(has_tag(b, 'Artificial Sweeteners') for b in KB)
no_sa = all(sa(b) == 0 for b in KB) and not any(has_tag(b, 'Sugar Alcohols') for b in KB)
C.check(no_as and no_sa, 'KIND has zero artificial sweeteners and zero sugar alcohols')
C.check(not any(has_ing(b, 'whey') or has_ing(b, 'casein') for b in KB), 'no KIND flavor uses whey or casein')
also_clean = [n for n, names in REVIEWED.items() if no_as_sa([b for b in ALL if b['Brand Name'] in names])]
def cert_n(field): return sum(1 for b in KB if b.get(field) == 'Yes')
GF, NG, KO = cert_n('Gluten Free (Y/N)'), cert_n('Non-GMO (Y/N)'), cert_n('Kosher (Y/N)')
no_gf = [b for b in KB if b.get('Gluten Free (Y/N)') != 'Yes']

def gstats(g):
    return dict(n=len(g), rng=range_words(g), sc=avg(g, 'ingredient_score'), p=avg(g, 'Protein (g)'),
                palm=sum(1 for b in g if has_ing(b, 'palm')), po=sum(1 for b in g if has_tag(b, 'Processed Oils')),
                sh=sum(1 for b in g if has_tag(b, 'Sweetener Heavy')), wff=sum(1 for b in g if has_tag(b, 'Whole Food Forward')))
SA_, SB_, SC_ = gstats(AL), gstats(BR), gstats(CL)
PALM = sum(1 for b in KB if has_ing(b, 'palm'))
PO_ALL = sum(1 for b in KB if has_tag(b, 'Processed Oils'))
PO_NONPALM = [b for b in KB if has_tag(b, 'Processed Oils') and not has_ing(b, 'palm')]
C.check(SB_['palm'] == 0 and all(has_ing(b, 'canola') for b in BR), 'the breakfast bars skip palm kernel oil and use canola')
C.check(set(map(nm, PO_NONPALM)) <= set(map(nm, BR)), 'every non-palm Processed Oils flag is a breakfast bar (canola)')
spread = max(SA_['sc'], SB_['sc'], SC_['sc']) - min(SA_['sc'], SB_['sc'], SC_['sc'])

# ---------------------------------------------------------------------------
# Picks
# ---------------------------------------------------------------------------
pick_best = BEST
pick_big = min(AL_BIG, key=lambda b: (band_rank(b), -(score(b) or 0), nm(b)))
pick_br = min(BR, key=lambda b: (band_rank(b), -(score(b) or 0), nm(b)))
skip = [KB[-1], KB[-2]]
def pos_chips(b): return [c[0] for c in chip_list(b) if c[1] == 'positive']
def lead3(b):
    parts = [x.strip() for x in re.split(r',(?![^()]*\))', ingr(b))][:3]
    return names_and(p.split('(')[0].strip().lower() for p in parts)
big_cal = sorted(set(map(CAL, AL_BIG)))
big_cal_txt = f'{fnum(big_cal[0])}' if len(big_cal) == 1 else f'{fnum(big_cal[0])}-{fnum(big_cal[-1])}'
t1 = (f"Grades {pick_best['score_band']} at {g1(score(pick_best))}, the highest score in the lineup, built on {lead3(pick_best)}"
      + (" with allulose instead of honey or cane sugar." if pick_best in AL else f", one of the {SC_['n']} classic nut-and-fruit bars." if pick_best in CL else '.'))
t2 = (f"All {num_word(len(AL_BIG))} of the former Protein Max flavors carry {fnum(MAXP)}g protein at {big_cal_txt} calories. "
      f"{nm(pick_big)} grades highest of that group at {pick_big['score_band']} ({g1(score(pick_big))}), the one to start with if you want the full protein-bar format.")
t3 = (f"The top of the {num_word(len(BR))} oat-and-soy breakfast bars at {pick_br['score_band']} ({g1(score(pick_br))}), with "
      f"{fnum(P(pick_br))}g protein and no palm kernel oil.")
w0, w1 = skip
t4 = (f"{nm(w0)} is the lineup's lowest score at {w0['score_band']} ({g1(score(w0))})"
      + (", with no positive chip at all." if not pos_chips(w0) else '.')
      + f" {nm(w1)} isn't far behind at {w1['score_band']} ({g1(score(w1))})"
      + (f", sweetened with {'honey, cane sugar and glucose syrup' if all(has_ing(w1, x) for x in ('honey', 'sugar', 'glucose')) else 'several sweeteners'}." ))
PICK_TILES = '\n'.join([
    brand_pick_tile('Best overall ingredient quality', [pick_best], t1),
    brand_pick_tile(f'Full {fnum(MAXP)}g protein, best grade', [pick_big], t2),
    brand_pick_tile('Best breakfast bar', [pick_br], t3),
    brand_pick_tile('Skip regardless of format', skip, t4, buy=False),
])
C.check(len({nm(pick_best), nm(pick_big), nm(pick_br)}) == 3, 'the three buy picks are different flavors')

# ---------------------------------------------------------------------------
# Alternatives keyed to the best-overall flavor
# ---------------------------------------------------------------------------
FLAG = pick_best
FB = band_rank(FLAG)
ALTS = pick_alternatives(ALL, FLAG, {BRAND}, ALT_KEYWORD, [
    ('Most protein',
     lambda b: band_rank(b) <= FB and not has_tag(b, 'Artificial Sweeteners') and sa(b) == 0,
     lambda b: (-P(b), band_rank(b), CAL(b)),
     lambda b: (f"{fnum(P(b))}g protein vs. {fnum(P(FLAG))}g here for {cal_delta(FLAG, b)}, with no artificial sweeteners or sugar alcohol. {grade_vs(FLAG, b)}")),
    ('Most fiber, real protein',
     lambda b: band_rank(b) <= FB and FIB(b) >= FIB(FLAG) + 4 and P(b) >= 12 and not has_tag(b, 'Artificial Sweeteners'),
     lambda b: (band_rank(b), -FIB(b), -P(b)),
     lambda b: (f"{fnum(FIB(b))}g fiber vs. {fnum(FIB(FLAG))}g here, with {fnum(P(b))}g protein vs. {fnum(P(FLAG))}g, for {cal_delta(FLAG, b)}. {grade_vs(FLAG, b)}"
                + (f" It does add {fnum(sa(b))}g of sugar alcohol where this flavor has none." if sa(b) else ''))),
    (lambda b: 'More protein, fewer calories' if CAL(b) < CAL(FLAG) else 'Smallest calorie cost',
     lambda b: band_rank(b) <= FB and P(b) >= P(FLAG) + 8 and not has_tag(b, 'Artificial Sweeteners'),
     lambda b: (CAL(b) - CAL(FLAG), band_rank(b), -P(b)),
     lambda b: (f"{fnum(P(b))}g protein vs. {fnum(P(FLAG))}g here for {cal_delta(FLAG, b)}. {grade_vs(FLAG, b)}"
                + (f" It does add {fnum(sa(b))}g of sugar alcohol where this flavor has none." if sa(b) else ''))),
], cal_window=100)
ALTS_HTML = f'''<h2>Like {esc(nm(FLAG))}? These are worth a look too</h2>
    <p>This is KIND's top ingredient-quality flavor, but at {fnum(P(FLAG))}g protein it's closer to a snack bar than a protein bar. {num_word(len(ALTS)).capitalize()} ways to trade up depending on what matters most to you.</p>
    <div class="macro-grid pick-tile-grid">
{chr(10).join(alt_tile(*a) for a in ALTS)}
    </div>'''

# ---------------------------------------------------------------------------
# Comparison + related
# ---------------------------------------------------------------------------
GROUPS = [(BRAND, KB)] + [(n, [b for b in ALL if b['Brand Name'] == n]) for n in COMPARE]
for n, g in GROUPS:
    C.check(len(g) > 0, f'{n} exists in bars.js for the comparison table')
COMPARE_HTML = compare_section_html(BRAND, GROUPS, compare_note(BRAND, GROUPS))
RX, BB = dict(GROUPS)['RXBAR'], dict(GROUPS)['Barebells']
C.check(no_as_sa(RX) and avg(RX, 'Protein (g)') > PRO['avg'], 'RXBAR skips AS/SA and averages more protein than KIND')
C.check(band_rank(min(RX, key=band_rank)) <= band_rank(min(KB, key=band_rank)), "RXBAR's best grade is at least as good as KIND's")
C.check(all(has_tag(b, 'Sugar Alcohols') for b in BB) and avg(BB, 'Protein (g)') > PRO['avg'] * 1.5,
        'Barebells has sugar alcohol in every flavor and much higher protein')
RELATED = f'''
        <a href="/rxbar-review" class="explore-more-card">
          <div class="explore-more-title">RXBAR Review</div>
          <div class="explore-more-desc">Another brand that skips artificial sweeteners and sugar alcohol, but leans on dates and egg whites instead of nuts. Higher protein, and every flavor grades {esc(range_words(RX))}.</div>
        </a>
        <a href="/barebells-review" class="explore-more-card">
          <div class="explore-more-title">Barebells Review</div>
          <div class="explore-more-desc">The opposite tradeoff: much higher protein and sugar alcohol in every flavor. See how a whey-based lineup compares to KIND's nut-based one.</div>
        </a>
        <a href="/gluten-free-protein-bars" class="explore-more-card">
          <div class="explore-more-title">Gluten Free Protein Bars Guide</div>
          <div class="explore-more-desc">{GF} of KIND's {N} flavors are labeled Gluten Free. See how the full lineup stacks up against every other gluten free bar we've scored.</div>
        </a>'''

# ---------------------------------------------------------------------------
# Copy
# ---------------------------------------------------------------------------
H1_TEXT = f'Are KIND Bars Healthy? We Ranked All {N} Flavors'
H1_HTML = f'Are <em>KIND</em> Bars Healthy? We Ranked All {N} Flavors'
TITLE = f'Are KIND Bars Healthy? {N} Flavors Ranked | Know Your Bar'
OG_TITLE = f'Are KIND Bars Healthy? {N} Flavors Ranked'
DESC = (f"KIND grades {GR} across {N} flavors with zero artificial sweeteners or sugar alcohols, but protein averages just "
        f"{g1(PRO['avg'])}g. Every flavor ranked.")
OG_DESC = (f"KIND scored A-F by ingredient quality: {GR} across {N} flavors, no artificial sweeteners, no sugar alcohols. "
           f"Only {num_word(len(AL_BIG))} flavors reach {fnum(MAXP)}g protein.")
C.check(len(DESC) <= 155, f'meta description length {len(DESC)}')
C.check(sum(1 for b in KB if P(b) >= MAXP) == len(AL_BIG), 'only the 62g allulose bars reach the protein max')

formulas = (f"{SA_['n']} allulose-sweetened bars (the {num_word(len(AL_BIG))} {fnum(MAXP)}g-protein bars that used to carry the "
            f"\"Protein Max\" name, plus {num_word(len(AL_MINI))} Nuts and Sea Salt minis), {SB_['n']} oat-and-soy breakfast bars, "
            f"and {SC_['n']} classic nut-and-fruit bars sweetened with honey, cane sugar, and glucose syrup")
HERO_SUB = (f"KIND doesn't market this as sub-brands, but the ingredients show three distinct formulas under one label: {formulas}. "
            f"Every flavor grades {GR_OR}, with no A and nothing lower. Protein swings from {fnum(PRO['lo'])}g in a snack-sized bar to "
            f"{fnum(PRO['hi'])}g in the allulose bars, which drags the lineup average down to {g1(PRO['avg'])}g, bottom {PRO['beats']}% of every "
            f"bar we track. Sugar alcohol and artificial sweeteners are a non-issue: zero across all {N} flavors. Here is the full breakdown, flavor by flavor.")
C.check(GRADES_PRESENT[0] != 'A' and len(GRADES_PRESENT) <= 2, 'KIND has no A and at most two grade tiers')

CERT_ROW = '    <div class="cert-badge-icon-row">\n' + '\n'.join(
    f'      <span class="cert-badge-icon"><svg viewBox="0 0 16 16" fill="none"><path d="M3 8.5L6.5 12L13 4.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>{lbl} ({n}/{N})</span>'
    for lbl, n in [('Gluten Free', GF), ('Non-GMO', NG), ('Kosher', KO)] if n) + '\n    </div>'
others_clean = [n for n in also_clean]
MACRO = f'''<h2>How KIND ranks on macros</h2>
    <p>Rather than labeling macros good or bad, we rank KIND against every bar in our database so you can see where they stand in the full market.</p>
{MACRO_GRID}
    <p class="macro-summary-text">{esc(f"KIND's clearest strength is what it skips: zero sugar alcohol and zero artificial sweeteners across all {N} flavors. The tradeoff shows up in protein. At {g1(PRO['avg'])}g average, KIND lands in the bottom {PRO['beats']}% of every bar we track, but that single number hides a real split: the {SA_['n']} allulose flavors average {g1(SA_['p'])}g protein, the {SB_['n']} breakfast bars {g1(SB_['p'])}g, and the {SC_['n']} classic nut bars just {g1(SC_['p'])}g.")}</p>
{CERT_ROW}'''

grp_rank = sorted([('allulose flavors', SA_), ('breakfast bars', SB_), ('classic nut bars', SC_)], key=lambda x: -x[1]['sc'])
ov1 = (f"KIND's lineup splits into three formulas, and the split is mostly about protein and oil, not grade. "
       + ("Grade barely follows the formula: " if spread < 1.0 else f"The {grp_rank[0][0]} score best on average: ")
       + f"the {SA_['n']} allulose flavors average a score of {g1(SA_['sc'])} ({SA_['rng']}), the {SB_['n']} breakfast bars {g1(SB_['sc'])} "
       f"({SB_['rng']}), and the {SC_['n']} classic nut bars {g1(SC_['sc'])} ({SC_['rng']}). Protein is where the formulas really differ: "
       f"{g1(SA_['p'])}g, {g1(SB_['p'])}g, and {g1(SC_['p'])}g on average.")
ov2 = (f"Each formula carries a different concern. All {SA_['n']} allulose flavors use palm kernel oil and stack sweetening agents "
       f"(Sweetener Heavy on {SA_['sh']} of {SA_['n']}). The breakfast bars skip palm kernel oil but use canola, and all {SB_['sh'] if SB_['sh'] == SB_['n'] else str(SB_['sh']) + ' of ' + str(SB_['n'])} stack sweeteners. "
       f"The classic nut bars are the most whole-food of the three, with Whole Food Forward on {SC_['wff']} of {SC_['n']}, "
       f"but palm kernel oil shows up in {SC_['palm']} of them.")
C.check(SA_['palm'] == SA_['n'] and SC_['wff'] > SA_['wff'] and SC_['wff'] > SB_['wff'], 'allulose bars all use palm; classic bars lead on Whole Food Forward')
ov3 = (f"What KIND does consistently, across every one of the {N} flavors, is skip artificial sweeteners and sugar alcohol entirely. "
       f"Certifications are common too: {GF} of {N} flavors are Gluten Free, {NG} are Non-GMO, and {KO} are Kosher.")
OVERVIEW = f'''<h2>What the data shows across all {N} KIND flavors</h2>
    <p>{esc(ov1)}</p>
    <p>{esc(ov2)}</p>
    <p>{esc(ov3)}</p>'''

GRADES = f'''<h2>Ingredient quality grade distribution across all {N} flavors</h2>
    <p>Here is how KIND's full lineup grades out. This is every flavor we've scored, not a hand-picked few. {esc(f"Every flavor lands at {GR_OR}: {grade_counts_txt(KB, ' and ', False).replace(' B', ' B').replace(' C', ' C')}. No flavor reaches an A, and none falls below {worst_g}.")}</p>
{grade_dist_html(KB)}'''

BESTWORST = f'''<h2>Best and worst flavors by ingredient quality</h2>
    <div class="bestworst">
{bw_card_html(BEST, True)}
{bw_card_html(WORST, False)}
    </div>'''

def tagn(t): return sum(1 for b in KB if has_tag(b, t))
pat = (f"Processed Oils is the most common concern, flagging {PO_ALL} of {N} flavors. Palm kernel oil specifically shows up in {PALM} of {N}: "
       f"all {SA_['n']} allulose flavors and {SC_['palm']} of the {SC_['n']} classic nut bars. The chip also catches canola in the {len(PO_NONPALM)} "
       f"breakfast bars that skip palm. Sweetener Heavy hits {tagn('Sweetener Heavy')} of {N} for stacking multiple sweetening agents. "
       f"On the positive side, Whole Food Forward credits {tagn('Whole Food Forward')} flavors for leading with real nuts, seeds, or fruit, and "
       f"Quality Protein Source recognizes {tagn('Quality Protein Source')} flavors for a genuine protein source. Fortified, a neutral chip "
       f"noting added vitamins, shows up in {tagn('Fortified')} flavors.")
C.check(max(chip_freq(KB).items(), key=lambda kv: kv[1][0])[0] == 'Processed Oils', 'Processed Oils is the most common KIND chip')
PATTERNS = f'''<h2>Ingredient quality patterns across the KIND lineup</h2>
    <p>KIND's ingredient profile leans on whole nuts and seeds more than most brands we've reviewed, but two concerns still show up across most of the lineup. Here's what shows up across all {N} flavors, split by whether it counts in the bar's favor or against it.</p>

{chip_patterns_html(KB)}

    <p style="margin-top:1.25rem;">{esc(pat)}</p>'''

TABLE_HEADING = f'''<h2>All {N} KIND flavors ranked by ingredient quality</h2>
    <p>Every flavor, every grade, every key macro. Sorted from cleanest to most processed. Tap any row to see the full ingredient list, macros, and buy links.</p>'''

bl1 = (f"KIND's real strength is what it leaves out. Every one of the {N} flavors we've scored skips artificial sweeteners and sugar alcohol"
       + (f", something only {names_and(also_clean)} also manage among the brands we've reviewed." if also_clean else ", which no other brand we've reviewed matches.")
       + f" But \"KIND bars\" isn't one product. The {num_word(len(AL_BIG))} {fnum(MAXP)}g-protein allulose bars carry real protein; the "
       f"{SC_['n']} classic nut bars average {g1(SC_['p'])}g and are closer to a snack bar than a protein bar.")
bl2 = (f"If you're buying KIND for protein, the {fnum(MAXP)}g allulose bars are where that case actually holds up. Start with {nm(pick_best)} if "
       f"ingredient quality is the deciding factor, or {nm(pick_big)} if you want the full {fnum(MAXP)}g protein format at the best available grade.")
BOTTOM = f'''<h2>Bottom line on KIND</h2>
    <p>{esc(bl1)}</p>
    <p>{esc(bl2)}</p>'''

PICKS = f'''<h2>Which KIND flavor should you actually buy</h2>
    <p>With a {N}-flavor lineup spanning three different formulas, there isn't one answer to "which KIND bar." Here's how we'd sort it depending on your goals, based on what's actually in the data above rather than the best- or worst-flavor snapshot alone.</p>
    <div class="macro-grid pick-tile-grid">
{PICK_TILES}
    </div>'''

cmp_groups = GROUPS[1:]
p100_rank = sorted(GROUPS, key=lambda g: -p100avg(g[1]))
fib_rank = [n for n, _ in sorted(GROUPS, key=lambda g: -avg(g[1], 'Dietary Fiber (g)'))].index(BRAND) + 1
ordinal = ['', 'highest', 'second-highest', 'third-highest', 'lowest']
FAQS = [
    ('Are KIND bars healthy?',
     f"KIND grades {GR} across all {N} flavors we've scored, with no A's and nothing below {worst_g}. The lineup splits into three formulas: "
     f"{formulas}. Every flavor skips artificial sweeteners and sugar alcohol entirely, but protein is low outside the {fnum(MAXP)}g bars."),
    ('Which KIND flavor is the healthiest?',
     f"{nm(BEST)} grades highest at {BEST['score_band']} (score {g1(score(BEST))}), built on {lead3(BEST)}."),
    ('How much protein do KIND bars have?',
     f"Protein ranges from {fnum(PRO['lo'])}g to {fnum(PRO['hi'])}g per bar, averaging {g1(PRO['avg'])}g, which lands in the bottom "
     f"{PRO['beats']}% of every bar we track. That average is misleading on its own: the {SA_['n']} allulose flavors average {g1(SA_['p'])}g, "
     f"the {SB_['n']} breakfast bars {g1(SB_['p'])}g, and the {SC_['n']} classic nut bars just {g1(SC_['p'])}g."),
    ('Do KIND bars have artificial sweeteners?',
     f"No. Zero of the {N} KIND flavors we've scored use an artificial sweetener."),
    ('Do KIND bars have sugar alcohols?',
     "No. Every KIND flavor has 0g sugar alcohol."),
    ('How do KIND bars compare to other protein bars?',
     f"KIND's protein per 100 calories, {g1(p100avg(KB))}g, is "
     + ('the lowest' if p100_rank[-1][0] == BRAND else 'not the lowest')
     + f" of the brands we compare it against, behind {names_and(f'{n} ({g1(p100avg(g))}g)' for n, g in p100_rank if n != BRAND)}. "
     f"Its fiber average, {g1(FIBS['avg'])}g, is the {ordinal[fib_rank] if fib_rank < len(GROUPS) else 'lowest'} of that group, and "
     + (f"it shares zero sugar alcohol and zero artificial sweeteners with {names_and(n for n, g in cmp_groups if no_as_sa(g))}."
        if any(no_as_sa(g) for n, g in cmp_groups) else "it's the only brand in the comparison with zero sugar alcohol and zero artificial sweeteners.")),
    ('What type of protein is in KIND bars?',
     f"KIND relies on nuts, seeds, and soy protein isolate rather than whey or casein. The {fnum(MAXP)}g allulose bars lead with peanuts and "
     "soy protein isolate, and the breakfast bars add soy protein isolate alongside oats."),
    ("What's the difference between KIND's old Protein Max line and its classic bars?",
     f"The {num_word(len(AL_BIG))} flavors that used to carry the separate \"KIND Protein Max\" name ({names_and(nm(b) for b in AL_BIG)}) are now "
     f"folded into the main KIND lineup in our database. They're still a distinct formula on the shelf: 62g bars built around allulose with "
     f"{fnum(MAXP)}g of protein, versus the 35-50g classic and breakfast bars that run {fnum(min(map(P, BR + CL)))}-{fnum(max(map(P, BR + CL)))}g of protein."),
    ('Do KIND bars contain palm oil?',
     f"{PALM} of {N} flavors list palm kernel oil directly: all {SA_['n']} allulose flavors and {SC_['palm']} of the {SC_['n']} classic nut bars. "
     f"The broader Processed Oils concern chip covers {PO_ALL} of {N}, since it also flags the canola oil in the breakfast bars that skip palm."),
    ('Are KIND bars gluten free?',
     f"{GF} of the {N} KIND flavors we've scored are labeled Gluten Free."
     + (f" {names_and(nm(b) for b in no_gf)} {'is' if len(no_gf) == 1 else 'are'} the only flavor{'s' if len(no_gf) > 1 else ''} without that label in our data, "
        "though that reflects a missing certification flag rather than a confirmed gluten-containing ingredient." if no_gf else '')),
]
C.check(not any(has_ing(b, 'wheat') or has_ing(b, 'barley') for b in no_gf), 'no gluten ingredient in the non-GF KIND flavors')

regions = [
    ('head-meta', head_meta_html(TITLE, DESC)),
    ('jsonld-article', article_jsonld(H1_TEXT, DESC, URL, 'KIND Snacks', 'https://www.kindsnacks.com')),
    ('jsonld-faq', faq_jsonld_brand(FAQS)),
    ('social', social_html(OG_TITLE, OG_DESC, URL)),
    ('hero', f'<h1 class="hero-title">{H1_HTML}</h1>\n    <p class="hero-sub">{esc(HERO_SUB)}</p>'),
    ('macro', MACRO), ('overview', OVERVIEW), ('grades', GRADES), ('bestworst', BESTWORST), ('patterns', PATTERNS),
    ('table-heading', TABLE_HEADING), ('table-rows', brand_table_html(KB, ALL)), ('bottom', BOTTOM), ('picks', PICKS),
    ('alts', ALTS_HTML), ('related', RELATED), ('compare', COMPARE_HTML), ('faq', faq_items_brand(FAQS)),
]
n_rows = build_brand_page(PAGE, regions, KB, ALL, C)
print(f'{PAGE}: {N} flavors, grades {GR} ({grade_counts_txt(KB, " ")})')
print(f'Groups: allulose {SA_["n"]}, breakfast {SB_["n"]}, classic {SC_["n"]}')
print(f'Best {nm(BEST)} {BEST["score_band"]} {g1(score(BEST))} | Worst {nm(WORST)} {WORST["score_band"]} {g1(score(WORST))}')
print('Picks:', nm(pick_best), '|', nm(pick_big), '|', nm(pick_br), '| skip', ', '.join(map(nm, skip)))
print('Alternatives:', ' | '.join(f"{a[0]}: {a[1]['Brand Name']} {a[1]['Flavor Name']} ({a[1]['score_band']})" for a in ALTS))
print(f'Grade-sync: {n_rows} flavor rows, best/worst cards and alternative tiles checked against bars.js, 0 mismatches')
