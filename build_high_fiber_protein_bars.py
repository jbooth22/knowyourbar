#!/usr/bin/env python3
"""Rebuild high-fiber-protein-bars.html from bars.js.

Run from the repo root:  python3 build_high_fiber_protein_bars.py

Replaces the older full-page generator. Opens the LIVE page and rewrites only
the <!-- kyb:NAME --> regions (nav, footer, fonts, CSS and JS stay as
deployed). Every number, pick, brand row and bar row comes from bars.js; copy
that depends on a fact is checked and the build stops if it stops being true.

Screen (GUIDE_CRITERIA.md, three cumulative tiers on Dietary Fiber (g)):
High 5g+, Very High 8g+, Extreme 11g+. The page ranks the Extreme tier
(GUIDE_FILTERS['high-fiber-protein-bars']). "The Extreme Fiber 100" is the
tier's name, not a count. Bar list uses this page's columns (FIBR, no SGR ALC).
"""
import re
from collections import Counter
from kyb_guide_lib import *

PAGE = 'high-fiber-protein-bars.html'
URL = 'https://knowyourbar.com/high-fiber-protein-bars'
PUBLISHED = '2026-09-06'

ALL = load_bars()
QF = GUIDE_FILTERS['high-fiber-protein-bars']
Q = [b for b in ALL if QF(b)]
D = [b for b in ALL if not QF(b)]
N, ND, NT = len(Q), len(D), len(ALL)
BRANDS_Q = len({b['Brand Name'] for b in Q})
GR = {g: sum(1 for b in Q if b.get('score_band') == g) for g in BAND_ORDER}
C = Claims()
C.check(N >= 90, 'the Extreme tier is still roughly 100 bars (the "Extreme Fiber 100" name)')

TIERS = [(5, 'High Fiber'), (8, 'Very High Fiber'), (11, 'Extreme Fiber')]
TIER = {t: [b for b in ALL if FIB(b) >= t] for t, _ in TIERS}
def tier_brands(t): return len({b['Brand Name'] for b in TIER[t]})

ADDED = [
    ('Tapioca Fiber', r'tapioca fiber|soluble tapioca|prebiotic tapioca|tapioca (?:resistant )?dextrin',
     'A resistant-starch fiber made from cassava root, added specifically to boost the fiber count without changing texture much.'),
    ('Polydextrose', r'polydextrose', 'A synthetic soluble fiber used as a bulking agent, common in bars that also carry a sugar-alcohol-heavy sweetener system.'),
    ('Chicory Root / Inulin', r'chicory|inulin', 'A naturally-occurring soluble fiber extracted from chicory root, one of the most common added-fiber sources in the industry.'),
    ('Soluble Corn Fiber', r'corn fiber|soluble corn', 'A corn-derived resistant dextrin used the same way as tapioca or chicory fiber, mainly to raise the fiber line on the label.'),
    ('Isomalto-oligosaccharide (IMO)', r'isomalto|\bimo\b(?!\s+free)',
     'A glucose-oligomer prebiotic fiber, chemically distinct from the sugar alcohol isomalt despite the similar name.'),
]
AHIT = {l: [b for b in Q if re.search(rx, ingr(b), re.I)] for l, rx, _ in ADDED}
WHOLE = [b for b in Q if not any(b in AHIT[l] for l, _, _ in ADDED)]
AORDER = sorted(AHIT, key=lambda l: -len(AHIT[l]))
ANY_ADDED = N - len(WHOLE)

# ---------------------------------------------------------------------------
# Top picks
# ---------------------------------------------------------------------------
PK = Picker(Q, diverse=True)
SCO = Scoper(Q, 'on this page')
best = PK.balanced()
top_f = PK.pick(lambda b: (-FIB(b), -P(b)))
top_p = PK.pick(lambda b: (-P(b), -FIB(b)))
low_s = PK.pick(lambda b: (SUG(b), -FIB(b)))
top_r = PK.pick(lambda b: (-(p100(b) or 0), -FIB(b)))
low_c = PK.pick(lambda b: (CAL(b), -FIB(b)))
C.check(all([best, top_f, top_p, low_s, top_r, low_c]), 'six distinct top picks available')
PICKS = [
    ['Best overall', best,
     f"{fnum(P(best))}g protein, {fnum(FIB(best))}g fiber, and just {fnum(SUG(best))}g sugar in one bar. "
     "Solid across the board rather than an extreme on one metric."],
    ['Highest fiber', top_f, f"{fnum(FIB(top_f))}g fiber, {SCO(FIB, top_f, 'most')}, alongside {fnum(P(top_f))}g protein."],
    ['Highest protein', top_p, f"{fnum(P(top_p))}g protein and {fnum(FIB(top_p))}g fiber, {SCO(P, top_p, 'most protein')}."],
    ['Lowest sugar', low_s, f"{fnum(SUG(low_s))}g sugar with {fnum(P(low_s))}g protein and {fnum(FIB(low_s))}g fiber, {SCO(SUG, low_s, 'lowest sugar', False)}."],
    ['Best protein per calorie', top_r,
     f"{fnum(P(top_r))}g protein at {fnum(CAL(top_r))} calories, {fnum(p100(top_r))}g of protein per 100 calories, "
     f"{SCO(lambda b: p100(b) or 0, top_r, 'best ratio')}."],
    ['Lowest calorie', low_c, f"{fnum(FIB(low_c))}g fiber at just {fnum(CAL(low_c))} calories, {SCO(CAL, low_c, 'fewest calories', False)}."],
]
C.check(P(best) >= 15 and FIB(best) >= 5 and SUG(best) <= 5, 'best overall meets the balanced bar')
add_sugar_tradeoff(PICKS)
for p in PICKS:
    if P(p[1]) < 10 and 'tradeoff' not in p[2]:
        p[2] += f" The tradeoff is protein: just {fnum(P(p[1]))}g, closer to a fiber snack than a protein bar."

# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------
def card(label, bars_hit, total, desc, found=True):
    return (f'''<div class="score-card">
  <div class="score-card-label">{esc(label)}</div>
  <div class="score-card-val">{len(bars_hit)} bars<span class="oil-card-pct">{g1(100 * len(bars_hit) / total)}%</span></div>
  <div class="score-card-desc">{esc(desc)}</div>''' + (f'\n  {found_in_html(bars_hit)}' if found else '') + '\n</div>')
DESC = {l: d for l, _, d in ADDED}
PUSH = f'''
    <div class="section-inner">
      <h2 class="section-title">What actually pushes a bar past 11g of fiber</h2>
      <div class="section-body">
        <p>Fiber on a protein bar label comes from one of two places: whole-food ingredients (nuts, seeds, legumes, whole grains) or an isolated fiber additive blended in specifically to raise the number. Among the {N} bars that clear our 11g Extreme Fiber cutoff, {pct(ANY_ADDED, N)}% contain at least one of the five named added-fiber ingredients we checked for.</p>
        <p>{AORDER[0]} is the single most common source, showing up in {len(AHIT[AORDER[0]])} of the {N} Extreme Fiber bars ({pct(len(AHIT[AORDER[0]]), N)}%). {names_and(AORDER[1:])} follow, often two or three stacked together in the same bar. None of these are red flags on their own, they're standard, well-tolerated ways to add fiber, but they're worth knowing about if a bar's ingredient list otherwise reads short and simple except for one long fiber name.</p>
      </div>
      <div class="score-grid" style="margin-top:1.5rem;">
{chr(10).join(card(l, AHIT[l], N, DESC[l]) for l in AORDER)}
{card('Whole-food fiber, no named additive', WHOLE, N, 'No tapioca fiber, polydextrose, chicory root/inulin, soluble corn fiber, or IMO in the ingredient list. These bars get to 11g+ through whole-food ingredients like nuts, seeds, and legumes instead of an added isolate.', found=False)}
      </div>
    </div>
'''
C.check(ANY_ADDED > N / 2, 'most Extreme Fiber bars use an added fiber ingredient')

def example(lo, hi):
    pool = [b for b in ALL if lo <= FIB(b) < hi]
    return sort_for_list(pool)[0]
EX5, EX8 = example(5, 8), example(8, 11)
TIERS_HTML = f'''
    <div class="section-inner">
      <h2 class="section-title">The three tiers of high fiber</h2>
      <div class="section-body">
        <p>11g of fiber is a real jump, not every bar needs to clear it. The FDA's own labeling rule sets 5g as the cutoff for an "excellent source of fiber" claim, and most people looking for a higher-fiber bar are better served starting there rather than at the Extreme tier above. We track three cutoffs on the same field (Dietary Fiber (g) per bar), cumulative, not separate lists: every Extreme Fiber bar also counts as Very High Fiber and High Fiber.</p>
        <div class="callout-box">
          <strong>Where the cutoffs land, recomputed fresh against the live database:</strong>
          <ul class="criteria-list" style="margin-top:0.5rem;">
            <li><strong>High Fiber, 5g+:</strong> {len(TIER[5])} bars ({pct(len(TIER[5]), NT)}% of the database), {tier_brands(5)} brands. The FDA's "excellent source of fiber" line. A gentle, easy starting point if you're new to eating more fiber.</li>
            <li><strong>Very High Fiber, 8g+:</strong> {len(TIER[8])} bars ({pct(len(TIER[8]), NT)}% of the database), {tier_brands(8)} brands. Roughly a third of a typical daily fiber target in one bar.</li>
            <li><strong>Extreme Fiber, 11g+:</strong> {N} bars ({pct(N, NT)}% of the database), {BRANDS_Q} brands. The tier ranked in full below. Most bars at this level lean on at least one added fiber ingredient to get there (see the category breakdown above).</li>
          </ul>
        </div>
        <p>A good High Fiber example that isn't also Very High or Extreme: {esc(full(EX5))}, {fnum(FIB(EX5))}g fiber, grade {EX5['score_band']}.</p>
        <p>A good Very High Fiber example that doesn't reach Extreme: {esc(full(EX8))}, {fnum(FIB(EX8))}g fiber, grade {EX8['score_band']}.</p>
        <p>Want a specific cutoff instead of the full Extreme Fiber list? The <a href="/bar-finder?fiber=5">Bar Finder's Min Fiber slider</a> lets you set any threshold from 0g up, not just these three, and stack it with protein, sugar, or ingredient grade filters at the same time.</p>
      </div>
    </div>
'''

# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------
CONSIDER, MIXED, AVOID = brand_split(ALL, QF)
FULL = sorted((r for r in CONSIDER if r['d'] == 0), key=lambda r: (-r['total'], r['brand'].lower()))
C.check(len(FULL) >= 4, 'at least four brands clear 11g on every flavor')
QUEST = next(r for r in CONSIDER + MIXED + AVOID if r['brand'] == 'Quest')
C.check(QUEST['q'] >= QUEST['total'] / 2, 'most Quest flavors clear 11g of fiber')
top5 = Counter(b['Brand Name'] for b in Q).most_common(5)
TOP5_N = sum(n for _, n in top5)
def ab(bars): return pct(sum(1 for b in bars if b.get('score_band') in ('A', 'B')), len(bars))
abq, aba = ab(Q), ab(ALL)
gword = 'about the same as' if abs(abq - aba) <= 5 else ('better than' if abq > aba else 'below')
pq, pa = avg(Q, 'Protein (g)'), avg(ALL, 'Protein (g)')
halves = len(TIER[8]) < len(TIER[5]) / 2 and len(TIER[11]) < len(TIER[8]) / 2
SPLIT_EX = max((r for r in MIXED + AVOID + CONSIDER if r['q'] and r['d'] and r['total'] >= 15),
               key=lambda r: (r['total'], -abs(r['q'] / r['total'] - 0.5)))
INSIGHTS = [
    (f"{len(FULL)} brands clear 11g of fiber on every flavor they make.",
     'Led by ' + names_and([f"{r['brand']} ({r['total']})" for r in FULL[:4]])
     + ', these brands build fiber into the base recipe rather than adding it to a handful of flavors.'),
    ("Quest shows fiber and mainstream availability aren't mutually exclusive.",
     f"{QUEST['q']} of Quest's {QUEST['total']} flavors clear 11g of fiber, all while staying one of the most widely available bars in the database."),
    (f'Extreme Fiber bars grade {gword} the database average.',
     f"{abq}% of Extreme Fiber bars grade A or B, against {aba}% database-wide."
     + (' High fiber does not come at the cost of ingredient quality.' if abq >= aba - 5 else '')),
    ('Extreme Fiber bars carry more protein on average, not less.' if pq > pa else 'Extreme Fiber bars carry a little less protein on average.',
     f"Extreme Fiber bars average {fnum(round(pq, 1))}g of protein against a database-wide average of {fnum(round(pa, 1))}g."),
    ('Fiber content drops off fast once you leave the top tier.',
     f"{len(TIER[5])} bars ({pct(len(TIER[5]), NT)}%) clear 5g of fiber, but only {len(TIER[8])} ({pct(len(TIER[8]), NT)}%) clear 8g, "
     f"and just {N} ({pct(N, NT)}%) clear 11g." + (' Each step up the fiber ladder cuts the qualifying pool by more than half.' if halves else '')),
    (f"{SPLIT_EX['brand']} shows how uneven fiber can be within one brand's own lineup.",
     f"{SPLIT_EX['q']} of the {SPLIT_EX['total']} {SPLIT_EX['brand']} flavors clear 11g of fiber, the rest fall short. "
     'Fiber varies flavor to flavor more than most other screens on this site.'),
]
FINDINGS = findings_html(f'What we found screening {comma(NT)} bars for fiber', f'{pct(N, NT)}%',
                         'of all protein bars clear 11g of fiber, our Extreme Fiber cutoff',
                         f"{N} of the {comma(NT)} bars we track carry 11g of fiber or more per bar, {TOP5_N} of them from just five "
                         f"brands. The rest of the database averages {fnum(round(avg(D, 'Dietary Fiber (g)'), 1))}g of fiber per bar.", INSIGHTS)

BRANDS = brand_tables_html(
    (CONSIDER, MIXED, AVOID), QF,
    h2='Best Brands for Extreme Fiber Protein Bars',
    intro='Some brands build fiber into every flavor, others clear 11g on only a bar or two. Grade columns below show ingredient '
          'quality only, not an overall bar rating. Click any brand name to jump to its flavors in the table below.',
    table_id='hf',
    consider_note=(f'Every flavor from these {len(CONSIDER)} brands clears 11g of fiber.' if all(r['d'] == 0 for r in CONSIDER)
                   else f'Every flavor, or nearly every flavor, from these {len(CONSIDER)} brands clears 11g of fiber.'),
    avoid_note="These brands clear 11g of fiber on few or none of their flavors. That's not a knock on the brand, most protein bars simply aren't built around fiber.",
    mixed_note='Some flavors clear 11g of fiber, some fall well short. Check the specific flavor before buying.',
    avoid_head='Flavors Under 11g Fiber', avoid_last_head='Why', avoid_last=lambda r: 'Under 11g fiber',
    mixed_head='Extreme Fiber Flavors', pick_word='Extreme Fiber pick', pick_head='Extreme Fiber Pick',
    consider_all='11g+ fiber across the whole lineup', consider_some='{q} of {total} flavors clear 11g',
    second_avg=('Avg Fiber', 'Dietary Fiber (g)'), avoid_label='Brands to Avoid (for this screen)')

TOPBAR = sort_for_list(Q)[0]
MOSTFIB = max(ALL, key=lambda b: (FIB(b), -len(b['Brand Name'])))
n_most = sum(1 for b in ALL if FIB(b) == FIB(MOSTFIB))
FAQS = [
    ('How much fiber counts as high fiber in a protein bar?',
     f'We use three tiers. High Fiber is 5g or more, the same cutoff the FDA uses for an "excellent source of fiber" claim '
     f'({len(TIER[5])} of {comma(NT)} bars, {pct(len(TIER[5]), NT)}%). Very High Fiber is 8g or more ({len(TIER[8])} bars, '
     f'{pct(len(TIER[8]), NT)}%). Extreme Fiber, the tier this page ranks, is 11g or more ({N} bars, {pct(N, NT)}%).'),
    ('What is the Extreme Fiber 100?',
     f"It's our name for the protein bars in the database that carry 11g or more of dietary fiber per bar, currently {N} of them. "
     f"That's about {pct(N, NT)}% of the {comma(NT)} bars we track, spanning {BRANDS_Q} brands."),
    ('What protein bar has the most fiber?',
     f"{full(MOSTFIB)}, at {fnum(FIB(MOSTFIB))}g of fiber per bar, "
     + ('the most of any bar in our database.' if n_most == 1 else f'tied for the most of any bar in our database.')),
    ('What ingredients make protein bars high in fiber?',
     'Mostly one of five added-fiber ingredients: tapioca fiber, polydextrose, chicory root fiber or inulin, soluble corn fiber, '
     f'or isomalto-oligosaccharide (IMO). {pct(ANY_ADDED, N)}% of Extreme Fiber bars contain at least one. The rest, '
     f'{pct(len(WHOLE), N)}%, get there through whole-food ingredients like nuts, seeds, and legumes with no added fiber isolate.'),
    ('Is more fiber always better in a protein bar?',
     "Not automatically. Fiber above roughly 10-15g in one sitting can cause bloating or digestive discomfort for people not used "
     "to it, especially from added isolates like polydextrose or IMO rather than whole-food fiber. If you're new to high fiber "
     'bars, the 5g or 8g tier is usually a gentler starting point than jumping straight to Extreme Fiber.'),
    ('Do high fiber protein bars grade lower on ingredient quality?',
     ('No. ' if abq >= aba - 5 else 'Somewhat. ') + f"Extreme Fiber bars grade A or B at {abq}%, against {aba}% database-wide. "
     f"They also average {fnum(round(pq, 1))}g of protein against {fnum(round(pa, 1))}g database-wide."),
    ("What's the difference between High Fiber, Very High Fiber, and Extreme Fiber on this site?",
     f"They're the same measurement (Dietary Fiber (g) per bar) at three different cutoffs: 5g+ ({len(TIER[5])} bars), 8g+ "
     f"({len(TIER[8])} bars), and 11g+ ({N} bars). Every Extreme Fiber bar also counts toward the other two tiers, since the "
     'cutoffs are cumulative, not separate categories.'),
    (f"Is {full(TOPBAR)} a good high fiber option?",
     f"Yes. It carries {fnum(FIB(TOPBAR))}g of fiber and {fnum(P(TOPBAR))}g of protein at {fnum(CAL(TOPBAR))} calories, and has the "
     'highest ingredient quality score of any Extreme Fiber bar we track.'),
    ('Can a brand have some high fiber flavors and some that aren\'t?',
     f"Yes. {SPLIT_EX['brand']} is a good example: {SPLIT_EX['q']} of {SPLIT_EX['total']} flavors clear 11g of fiber, the rest fall "
     'short. Fiber content varies flavor to flavor more than most other screens on this site, so check the specific flavor, not just the brand.'),
    ('How often is this list updated?',
     'We update the database whenever new bars are added or a brand reformulates. Manufacturers do change their recipes over '
     f'time, so always confirm against the packaging in front of you. This page reflects the database as of {today_iso()}.'),
]

TITLE = 'The Extreme Fiber 100: Protein Bars With 11g+ Fiber, Ranked'
H1 = 'The Extreme Fiber 100 - Protein Bars With 11g or More Fiber'
DESC = (f'We checked {comma(NT)} protein bars for fiber. {N} clear 11g per bar, our Extreme Fiber cutoff. See every one, plus '
        'the High Fiber and Very High Fiber tiers below it.')
OG = f'{N} protein bars with 11g or more of fiber per bar, ranked by ingredient quality, protein, and brand.'
REGIONS = [r for r in guide_head_regions(title=TITLE, h1=H1, desc=DESC, og_desc=OG, url=URL, about='High Fiber Protein Bars',
                                         published=PUBLISHED, faqs=FAQS, picks=PICKS) if r[0] != 'social']
REGIONS += [
    ('social', social_title_html(TITLE, OG, URL)),
    ('hero', f'''<h1 class="hero-title">{esc(H1)}</h1>
    <p class="hero-sub" style="color:#e8e4dc;">We checked {comma(NT)} protein bars available in the US against their declared Dietary Fiber (g). {N} of them, about {pct(N, NT)}%, clear 11g of fiber per bar, our Extreme Fiber cutoff, and that's the list this page ranks first. Below it we cover two supporting tiers: {len(TIER[5])} bars clear 5g (High Fiber, the FDA's own "excellent source" line) and {len(TIER[8])} clear 8g (Very High Fiber). Not just us telling you the flavors we like.</p>'''),
    ('snapshot', f'''
    <div class="snap-item"><div class="snap-value">{N}</div><div class="snap-label">Extreme Fiber bars</div></div>
    <div class="snap-item"><div class="snap-value">{comma(ND)}</div><div class="snap-label">Under 11g fiber</div></div>
    <div class="snap-item"><div class="snap-value">{GR['A']}</div><div class="snap-label">A-grade bars</div></div>
    <div class="snap-item"><div class="snap-value">{BRANDS_Q}</div><div class="snap-label">Brands represented</div></div>
    <div class="snap-item"><div class="snap-value">{avg(Q, 'Dietary Fiber (g)'):.1f}g</div><div class="snap-label">Avg fiber in this tier</div></div>
  '''),
    ('picks', picks_section_html('Top picks from the Extreme Fiber 100',
                                 'Every bar below clears 11g of fiber per bar. Here are the best of that group for what people '
                                 'typically look for. Grades below reflect ingredient quality only, not an overall bar rating.', PICKS)),
    ('what-actually-pushes-a-bar-past-11g-of-f', PUSH),
    ('the-three-tiers-of-high-fiber', TIERS_HTML),
    ('findings', FINDINGS),
    ('brands', BRANDS),
    ('cta-heading', '<h2 class="explore-cta-main-heading">Pick your own fiber cutoff, not just 11g</h2>'),
    ('explore-more', '''
        <a href="/best-bars-for-diabetics" class="explore-more-card">
          <div class="explore-more-title">Best Bars for Diabetics</div>
          <div class="explore-more-desc">Fiber is one of six criteria in a full diabetic-friendly screen.</div>
        </a>
        <a href="/glp1-protein-bars" class="explore-more-card">
          <div class="explore-more-title">GLP-1 Protein Bars</div>
          <div class="explore-more-desc">High protein, low sugar bars built for satiety, fiber included.</div>
        </a>
        <a href="/clean-protein-bars" class="explore-more-card">
          <div class="explore-more-title">Clean Protein Bars</div>
          <div class="explore-more-desc">A or B grade bars with no artificial sweeteners and no processed oils.</div>
        </a>
      '''),
    ('faq', faq_items_html(FAQS)),
]
REGIONS += guide_list_regions(Q, ALL, heading=f'The Extreme Fiber 100: all {N} bars with 11g+ fiber, ranked by ingredient quality',
                              lazy_attr=True, variant='fiber')

if __name__ == '__main__':
    n = build_guide_page(PAGE, REGIONS, Q, ALL, C)
    print(f'{PAGE}: {N} qualify, {ND} under 11g, {n} rows, grade-sync 0 mismatches')
    for label, b, why in PICKS:
        print(f'  {label}: {full(b)} ({b["score_band"]})')
