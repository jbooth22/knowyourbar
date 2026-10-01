#!/usr/bin/env python3
"""Rebuild creatine-protein-bars.html from bars.js. GUIDE PAGE v2 ("Best" list).

Run from the repo root:  python3 build_creatine_protein_bars.py

Layout and every rule: claude/GUIDE_PAGE_SPEC_V2.md (locked 2026-09-29) and
the v2 section of kyb_guide_lib.py. The first run migrated the live v1 page to
the v2 body (head, nav and footer kept as deployed); later runs rewrite only
the <!-- kyb:NAME --> regions. Every number, pick and brand row comes from
bars.js. Copy that depends on a fact is checked; if one stops being true the
build stops and lists it. Ingredient quality is shown and ranked as a GRADE only.

Screen: GUIDE_FILTERS['creatine-protein-bars'] = Creatine (g) > 0 (any declared
amount). Tiers: Clinical 3g+ (the 3-5g daily dose most creatine research uses)
and Trace under 3g.

Best list (2026-09-30; Jeff asked for the best picks delivered without an
approval round): only 6 creatine bars pass the pick rules (A/B grade, 10g+
protein) and they come from 3 brands, so with the 2-per-brand cap the list
holds 6 (N_PICKS; the criteria section says why). Guide slot: Highest creatine
dose, which picks right after Best overall (PICK_ORDER) so the 5g bar gets it;
the cards still show the core slots first. No big brand makes a creatine bar,
so "Best from a big brand" is empty and the big-brands section is one line.
Brands section: every creatine brand, not only brands with 3+ bars (the usual
rule would drop Rello and Daily Bar, the only A/B brands besides JiMMYBAR!).
Bar Finder: it has no creatine filter, so the CTA opens the Bar Finder and
says so; the page itself lists every creatine bar (the "All N" table).
"""
import re
from collections import Counter
from kyb_guide_lib import *

PAGE = 'creatine-protein-bars.html'
URL = 'https://knowyourbar.com/creatine-protein-bars'
PUBLISHED = '2026-09-06'
set_tie_seed('creatine-protein-bars')   # per-guide shuffle for exact ties (kyb_guide_lib, 2026-09-30)

ALL = load_bars()
QF = GUIDE_FILTERS['creatine-protein-bars']
Q = [b for b in ALL if QF(b)]
N, NT = len(Q), len(ALL)
GR = {g: sum(1 for b in Q if b.get('score_band') == g) for g in BAND_ORDER}
N_AB = GR['A'] + GR['B']
C = Claims()
def CR(b): return num(b.get('Creatine (g)')) or 0
def gstr(v): return f'{fnum(v)}g'
BRANDS = sorted({b['Brand Name'] for b in Q}, key=lambda x: (-sum(1 for b in Q if b['Brand Name'] == x), x.lower()))
NB = len(BRANDS)
CLIN = [b for b in Q if CR(b) >= 3]
TRACE = [b for b in Q if CR(b) < 3]
E = v2_eligible(Q)
MX, MN = max(CR(b) for b in Q), min(CR(b) for b in Q)
def doses(bars):
    v = sorted({CR(b) for b in bars})
    return gstr(v[0]) if len(v) == 1 else f'{gstr(v[0])} to {gstr(v[-1])}'
def glr(bars):
    lo, hi = grade_range(bars)
    return lo if lo == hi else f'{lo} to {hi}'
C.check(8 <= N <= 40, 'creatine is still a small category')
C.check(CLIN and TRACE, 'both a clinical and a trace tier exist')
C.check(not any(is_big(b) for b in Q), 'no big brand makes a creatine bar')
C.check(not any(QF(b) for b in ALL if b['Brand Name'] in ('Quest', 'Barebells')), 'Quest and Barebells make no creatine bar')

# ---------------------------------------------------------------------------
# Best list (spec v2)
# ---------------------------------------------------------------------------
def sa_note(b):
    rx = [w for w in ('maltitol', 'erythritol', 'sorbitol', 'xylitol') if re.search(w, ingr(b), re.I)]
    return f" It's sweetened partly with {names_and(rx)}." if rx else ''
MOST_CR = Slot('Highest creatine dose', 'The most creatine per bar, grade B or better, 10g+ protein.',
               lambda E: E, lambda b: (-CR(b),) + tie_chain(b),
               lambda b, c: (f"{gstr(CR(b))} of creatine, {c['tied']}the most of any bar here with an A or B grade and 10g+ "
                             f"protein, and inside the 3 to 5g daily dose most creatine research uses." + sa_note(b)),
               metric=CR)
CORE = [slot_best_overall(15), slot_cleanest(), slot_highest_protein(300), slot_protein_per_cal(12), slot_lowest_calorie(),
        slot_big_brand()]
GUIDE = [MOST_CR]
PICK_ORDER = [CORE[0]] + GUIDE + CORE[1:]
DISPLAY = CORE + GUIDE
RAW = pick_best10(Q, PICK_ORDER, [])
PICKS = sorted(RAW, key=lambda p: DISPLAY.index(p[0]))
N_PICKS = len(PICKS)
C.check(N_PICKS == len(E), 'every bar that passes the pick rules is on the list (the category is that small)')
C.check(N_PICKS < 10, 'fewer than 10 picks (the page says why)')
C.check(not any(re.search(r'score \d|scored? \d', w) for _s, _b, w, _n in PICKS), 'no ingredient score printed in a pick')
PK = {s.label: b for s, b, _w, _n in PICKS}
EMPTY_OTHER = [s.label for s in DISPLAY if s.label not in PK and s.label != 'Best from a big brand']
C.check('Highest creatine dose' in PK and CR(PK['Highest creatine dose']) == max(CR(b) for b in E),
        'the dose pick holds the top dose among eligible bars')
C.check(CR(PK['Highest creatine dose']) <= 5, 'the top dose is inside the 3 to 5g research range')
BEST = PK['Best overall']
B10_INTRO = (f"Only {len(E)} of the {N} creatine bars have an A or B ingredient grade and 10g+ protein, from "
             f"{len({b['Brand Name'] for b in E})} brands, so every one of them is here, each as the winner of one thing "
             "people shop for. Check the creatine dose on each card: it runs from a trace amount to a full daily dose.")

# ---------------------------------------------------------------------------
# What it means: two dose tiers (v1 editorial, trimmed)
# ---------------------------------------------------------------------------
def tier_desc(bars, lead):
    by = Counter(b['Brand Name'] for b in bars)
    parts = ', '.join(f"{br} at {doses([b for b in bars if b['Brand Name'] == br])}" for br, _n in by.most_common())
    return f"{lead} {parts}. Grades {glr(bars)}."
A_BARS = [b for b in Q if b['score_band'] == 'A']
C.check(A_BARS and all(CR(b) < 3 for b in A_BARS), 'every A-grade creatine bar carries a trace dose')
MONO = [b for b in Q if re.search(r'creatine', ingr(b), re.I)]
C.check(all(re.search(r'monohydrate', ingr(b), re.I) for b in MONO), 'bars that name their creatine list monohydrate')
MEANS = f'''
    <div class="section-inner">
      <h2 class="section-title">Two dose tiers, not one creatine category</h2>
      <div class="section-body">
        <p>Most creatine research on strength and training uses 3 to 5 grams a day, taken consistently. The bars on this page don't spread evenly around that number; they fall into two groups. One carries a full daily dose. The other carries a gram or so, well under what studies use.</p>
      </div>
      <div class="score-grid" style="margin-top:1.5rem;">
{v2_count_card_html('Clinical dose (3g or more)', CLIN, N, tier_desc(CLIN, 'In line with the daily dose most research uses.'))}
{v2_count_card_html('Trace dose (under 3g)', TRACE, N, tier_desc(TRACE, 'Well under a research dose.'))}
      </div>
      <div class="section-body">
        <p>Dose and ingredient quality don't line up here. The only A-grade creatine bars, from {names_and(sorted({b['Brand Name'] for b in A_BARS}))}, carry {doses(A_BARS)}. If you want a full dose from a bar, look at the clinical tier and check the grade. If you already take creatine powder, the dose in a bar matters less.</p>
        <p>The form matters more than the delivery. {'Every bar here' if len(MONO) == N else f'All {len(MONO)} bars'} that name their creatine in the ingredients use creatine monohydrate, the same form used in most creatine research and sold as powder.</p>
      </div>
      <div class="callout-box"><strong>Heads up:</strong> We are not doctors or dietitians, and this page is not medical advice. Talk to your doctor before adding a supplement to your routine, especially if you are pregnant, have a kidney condition, or take other medications.</div>
    </div>
'''

# ---------------------------------------------------------------------------
# Findings: three data findings + one chart
# ---------------------------------------------------------------------------
SA_CLIN = [b for b in CLIN if CR(b) >= 5]
C.check(SA_CLIN and all(has_sugar_alcohol(b) for b in SA_CLIN), 'every 5g creatine bar uses a sugar alcohol')
BIGB = Counter(b['Brand Name'] for b in Q).most_common(1)[0]
C.check(round(100 * N / NT) == 1, 'creatine bars are about 1% of the database')
INSIGHTS = [
    ('About 1% of protein bars have creatine.',
     f"{N} of the {DB_PUBLIC} bars we track list creatine, from just {NB} brands. None of the big grocery brands make one, "
     "including Quest and Barebells."),
    ('The cleanest creatine bars carry the least creatine.',
     f"The {len(A_BARS)} A-grade bars carry {doses(A_BARS)}. The {len(CLIN)} bars with a full 3g+ dose grade {glr(CLIN)}."),
    ('Every 5g bar uses a sugar alcohol.',
     f"All {len(SA_CLIN)} bars at {gstr(5)} of creatine ({names_and(sorted({b['Brand Name'] for b in SA_CLIN}))}) use a sugar "
     "alcohol like maltitol to keep the sugar line low."),
]
GRADE_ROWS = [(g, GR[g], N) for g in BAND_ORDER]
FINDINGS = findings_v2_html(f'What we found screening {DB_PUBLIC} bars for creatine', INSIGHTS,
                            grade_share_chart_html(GRADE_ROWS, title=f'How the {N} creatine bars grade on ingredients',
                                                   note=f'Share of the {N} bars with creatine in each ingredient grade. '
                                                        f'{N_AB} of {N} grade A or B.'))

# ---------------------------------------------------------------------------
# The creatine brands (every one) + big brands (one line)
# ---------------------------------------------------------------------------
def brand_rows():
    rows = []
    for br in BRANDS:
        bars = [b for b in ALL if b['Brand Name'] == br]
        q = [b for b in bars if QF(b)]
        rows.append(dict(brand=br, bars=bars, qual=q, total=len(bars), q=len(q), share=len(q) / len(bars),
                         rank=len(q) / len(bars) * sum(gp(b) for b in q) / len(q) / 4, big=False,
                         grades=Counter(b['score_band'] for b in q)))
    rows.sort(key=lambda r: (-r['rank'], -r['total'], r['brand'].lower()))
    return rows
WELL = brand_rows()
def well_why(r):
    lead = (f"All {r['total']} flavors have creatine" if r['q'] == r['total'] else
            f"{r['q']} of {r['total']} flavors {'has' if r['q'] == 1 else 'have'} creatine")
    bp = best_pick(r['qual'])
    tail = (f" Just {fnum(P(bp))}g of protein." if P(bp) < 10 else '')
    return f"{lead}, at {doses(r['qual'])}. Best pick: {bp['Flavor Name']} ({bp['score_band']}, {gstr(CR(bp))} creatine).{tail}"
BRANDS_WELL = brands_well_html(WELL, well_why, h2=f'The {NB} brands making creatine bars',
                               intro=f'Every brand in our database with a creatine bar, ranked by how much of their lineup has '
                                     'creatine and how well those bars grade.')
NBIG = sum(1 for br in BIG_BRANDS if any(b['Brand Name'] == br for b in ALL))
BIG_HTML = f'''<div class="section-inner">
      <h2 class="section-title">How do the big brands fare on creatine?</h2>
      <p class="section-body">None of them make a creatine bar. We track {NBIG} brands with national grocery, big-box or Costco distribution, including Quest, Barebells, RXBAR and KIND, and not one of their bars lists creatine. For now, creatine bars come from smaller brands you'll mostly find online.</p>
    </div>'''

# ---------------------------------------------------------------------------
# All N + Bar Finder CTA + criteria
# ---------------------------------------------------------------------------
TOP = top50_rows(Q, 50)
C.check(len(TOP) == N, 'the list below shows every creatine bar')
ALL_LIST = top50_html(TOP, h2=f'All {N} protein bars with creatine',
                      intro='Every bar in our database that lists creatine. Ranked by ingredient grade first, then by protein '
                            'per calorie. Tap any row for nutrition facts and the full ingredient list.',
                      cols=('grade', 'creatine', 'protein', 'cal', 'sugar'), hide_mobile=('cal', 'sugar'))
FINDER = finder_cta_html(NT, '/bar-finder', desc=(
    "The Bar Finder can't filter by creatine yet, so every creatine bar is listed on this page. Open the Bar Finder to "
    "compare any bar's nutrition and ingredients, or filter the full database by protein, sugar, grade and ingredients to avoid."))
_see_all = f'See all {comma(NT)} in the Bar Finder &rarr;'
C.check(FINDER.count(_see_all) == 2, 'finder CTA heading and button found')
FINDER = FINDER.replace(f'<h2 class="explore-cta-main-heading">{_see_all}</h2>',
                        '<h2 class="explore-cta-main-heading">Compare bars in the Bar Finder &rarr;</h2>', 1)
FINDER = FINDER.replace(_see_all, 'Open the Bar Finder &rarr;', 1)
CRITERIA = criteria_html(
    qualify_rule=(f'Any creatine listed on the label, no minimum dose. No macro or ingredient-grade gate beyond that. {N} of '
                  f'the {DB_PUBLIC} bars we track qualify, {N_AB} of them with an A or B grade.'),
    picks=PICKS, n_spots=N_PICKS,
    extra_rules=['No national grocery or big-box brand makes a creatine bar, so there is no "Best from a big brand" pick.'] +
                ([f'{names_and(EMPTY_OTHER)} had no eligible bar left once the other picks were made, so '
                  f'{"it is" if len(EMPTY_OTHER) == 1 else "they are"} not on the list.'] if EMPTY_OTHER else []))

# ---------------------------------------------------------------------------
# FAQ (answers may hold links; JSON-LD gets the plain text)
# ---------------------------------------------------------------------------
def brand_faq(name, verdict):
    bs = sorted([b for b in Q if b['Brand Name'] == name], key=overall_key)
    C.check(bs, f'{name} still makes a creatine bar')
    return (f"{verdict} {num_word(len(bs)).capitalize()} {name} flavors list creatine, at {doses(bs)}, grading {glr(bs)}: "
            + ', '.join(f"{b['Flavor Name']} ({b['score_band']})" for b in bs) + '.')
DOSE = PK['Highest creatine dose']
FAQS = [
    ('What is the best protein bar with creatine?',
     f"By our rules, {full(BEST)}: {BEST['score_band']}-grade ingredients and {fnum(P(BEST))}g protein, but only "
     f"{gstr(CR(BEST))} of creatine. For a full dose, {full(DOSE)} has {gstr(CR(DOSE))} with {DOSE['score_band']}-grade "
     "ingredients." if CR(BEST) < 3 else
     f"By our rules, {full(BEST)}: {BEST['score_band']}-grade ingredients, {fnum(P(BEST))}g protein and {gstr(CR(BEST))} of creatine."),
    ('How much creatine is actually in these protein bars?',
     f"It varies a lot. {len(TRACE)} of the {N} carry a trace {doses(TRACE)}, and {len(CLIN)} carry {doses(CLIN)}, in line "
     'with the daily dose most creatine research uses. Check the dose before assuming a bar with creatine gives you a '
     'meaningful amount.'),
    ('Is 1g of creatine enough to do anything?',
     'Probably not much on its own. Most creatine research on strength and muscle performance uses 3 to 5 grams a day. A 1g '
     "dose is well under that. It's not nothing, but it's closer to a token amount than a working one."),
    ('What is a clinically effective dose of creatine?',
     'The research most commonly uses 3 to 5 grams a day, taken consistently, and some protocols start with a short loading '
     f'phase of up to 20g a day split into smaller doses. {len(CLIN)} of the {N} bars on this page have 3g or more. This page '
     'is not medical advice; talk to your doctor before adding a supplement to your routine.'),
    ('Does creatine in a protein bar work the same as creatine powder?',
     'The form matters more than the delivery. Bars that name their creatine use creatine monohydrate, the same form used in '
     'most creatine research and sold as powder. A bar just packs the dose into a snack instead of a scoop.'),
    ('Why do so few protein bars contain creatine?',
     'A brand has to build a bar around creatine on purpose, for a training-focused customer. Only '
     f'{N} of the {DB_PUBLIC} bars in our database list any creatine, from {NB} brands. Quest and Barebells skip it entirely.'),
    ('Is JiMMYBAR! good for creatine?', brand_faq('JiMMYBAR!', 'For the dose, yes; for ingredients, it depends on the flavor.')),
    ('Is Rello good for creatine?', brand_faq('Rello', 'On ingredients, yes; on dose, not really.')),
    ('How many protein bars in your database contain creatine?',
     f'{N} of the {DB_PUBLIC} bars in our database list creatine, about {pct0(N, NT)}%, from {NB} brands. Any listed amount counts.'),
]
JB = [b for b in Q if b['Brand Name'] == 'JiMMYBAR!']
C.check(JB and all(CR(b) >= 3 for b in JB) and len({b['score_band'] for b in JB}) > 1, 'JiMMYBAR! is full-dose with mixed grades')
RELLO = [b for b in Q if b['Brand Name'] == 'Rello']
C.check(RELLO and all(b['score_band'] in ('A', 'B') and CR(b) < 3 for b in RELLO), 'Rello is A/B with a trace dose')

# ---------------------------------------------------------------------------
# Regions
# ---------------------------------------------------------------------------
H1 = f'The {N_PICKS} Best Protein Bars with Creatine'
TITLE = f'{N_PICKS} Best Protein Bars with Creatine ({DB_PUBLIC} Checked)'
DESC = (f'Only {N} of {DB_PUBLIC} protein bars have creatine, from {gstr(MN)} to {gstr(MX)}. Here are the {N_PICKS} best, '
        'and which ones carry a real dose.')
OG_DESC = (f'{N} protein bars list creatine. Here are the {N_PICKS} best, each picked by a published rule, with every dose '
           'checked against the 3 to 5g research range.')
C.check(len(DESC) <= 155, f'meta description under 155 characters ({len(DESC)})')
FAQS_PLAIN = [(q, plain_text(a)) for q, a in FAQS]
REGIONS = v2_head_regions(title=TITLE, h1=H1, desc=DESC, og_desc=OG_DESC, url=URL, about='Creatine Protein Bars',
                          published=PUBLISHED, faqs=FAQS_PLAIN, picks=PICKS)
EDITORIAL = f'  <section class="section off" id="what-it-means">{MEANS}  </section>'
HERO = (f'<h1 class="hero-title">{esc(H1)}</h1>\n'
        f'    <p class="hero-sub">Creatine is one of the most studied supplements for strength training, and a few brands now '
        f'put it in a protein bar. It only does much at the dose research uses, 3 to 5 grams a day, so the number on the '
        f'label matters as much as the protein.</p>\n'
        f'    <p class="hero-sub">Only {N} of the {DB_PUBLIC} bars we track list creatine, from {NB} brands. {len(CLIN)} carry '
        f'a full {doses(CLIN)}; {len(TRACE)} carry a trace {doses(TRACE)}. Just {len(E)} have an A or B ingredient grade and '
        f'10g+ protein, so our list has {N_PICKS} picks, not 10.</p>')
REGIONS += [
    ('hero', HERO),
    ('best10', best10_html(PICKS, h2=f'Best {N_PICKS} protein bars with creatine', intro=B10_INTRO,
                           macros=[('Creatine', lambda b: gstr(CR(b))), ('Protein', lambda b: f'{fnum(P(b))}g'),
                                   ('Calories', lambda b: fnum(CAL(b))), ('Sugar', lambda b: f'{fnum(SUG(b))}g')])),
    ('editorial', EDITORIAL),
    ('findings', FINDINGS),
    ('brands-well', BRANDS_WELL),
    ('big-brands', BIG_HTML),
    ('top50', ALL_LIST),
    ('finder-cta', FINDER),
    ('criteria', CRITERIA),
    ('faq', faq_items_html(FAQS)),
    ('author', byline_html()),
    ('explore-more', related_html([
        ('/caffeine-protein-bars', 'Caffeine Protein Bars', 'The other supplement-style bar: every dose compared to a cup of coffee.'),
        ('/clean-protein-bars', 'Clean Protein Bars', 'A or B grade bars with no artificial sweeteners and no seed oils.'),
        ('/no-sugar-alcohols', 'No Sugar Alcohols', 'Bars without maltitol, erythritol or other sugar alcohols.'),
    ])),
]

if __name__ == '__main__':
    page = build_guide_page_v2(PAGE, REGIONS, ALL, C, picks=PICKS, n_picks=N_PICKS)
    size = len(page.encode('utf-8'))
    faq_at = len(page[:page.find('<section class="guide-faq"')].encode('utf-8'))
    print(f'{PAGE}: {N} qualify ({N_AB} A/B, {len(E)} eligible), {size:,} bytes, FAQ at byte {faq_at:,}')
    for i, (s_, b, why, n) in enumerate(PICKS, 1):
        print(f'  {i:2d}. {s_.label}: {full(b)} ({b["score_band"]}) [pool {n}]')
        print(f'      {why}')
