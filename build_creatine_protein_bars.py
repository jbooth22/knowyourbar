#!/usr/bin/env python3
"""Rebuild creatine-protein-bars.html from bars.js.

Run from the repo root:  python3 build_creatine_protein_bars.py

Opens the LIVE page and rewrites only the <!-- kyb:NAME --> regions (nav,
footer, fonts, CSS and JS stay as deployed). Every number, pick, tier, brand
note and bar row comes from bars.js; copy that depends on a fact is checked
and the build stops if one stops being true.

Screen: GUIDE_FILTERS['creatine-protein-bars'] = Creatine (g) > 0 (any declared
amount, the live page's own definition; GUIDE_CRITERIA.md has no row for it
yet). Tiers: Clinical 3g+ (the 3-5g maintenance range most creatine research
uses) and Trace under 3g. The set is small, so brands get a written rundown
instead of Consider / Mixed / Avoid tables, all generated from bars.js.
"""
from collections import Counter
from kyb_guide_lib import *
from kyb_dose_guide import dose_list_regions

PAGE = 'creatine-protein-bars.html'
URL = 'https://knowyourbar.com/creatine-protein-bars'
PUBLISHED = '2026-09-06'

ALL = load_bars()
QF = GUIDE_FILTERS['creatine-protein-bars']
Q = [b for b in ALL if QF(b)]
N, NT = len(Q), len(ALL)
C = Claims()
def CR(b): return num(b.get('Creatine (g)')) or 0
def gstr(v): return f'{fnum(v)}g'
BRANDS = sorted({b['Brand Name'] for b in Q}, key=lambda x: (-sum(1 for b in Q if b['Brand Name'] == x), x.lower()))
NB = len(BRANDS)
CLIN = [b for b in Q if CR(b) >= 3]
TRACE = [b for b in Q if CR(b) < 3]
GR = {g: [b for b in Q if b.get('score_band') == g] for g in BAND_ORDER}
def avg_score(bars): return sum(score(b) or 0 for b in bars) / len(bars) if bars else 0
def tier(b): return 'Clinical dose' if CR(b) >= 3 else 'Trace dose'
def doses(bars): return names_and([gstr(v) for v in sorted({CR(b) for b in bars})])
def doses_or(bars):
    v = [gstr(x) for x in sorted({CR(b) for b in bars})]
    return v[0] if len(v) == 1 else ', '.join(v[:-1]) + ' or ' + v[-1]
def gl(bars):
    lo, hi = grade_range(bars)
    return lo if lo == hi else f'{lo} to {hi}'
C.check(CLIN and TRACE, 'both a clinical and a trace tier exist')

# ---------------------------------------------------------------------------
# Top picks
# ---------------------------------------------------------------------------
PK = Picker(Q, floor=0, diverse=True)
SCO = Scoper(Q, 'on this page', floor=0)
best = PK.pick(lambda b: (-P(b), -CR(b)))
top_dose = PK.pick(lambda b: (-CR(b), -P(b)), lambda b: CR(b) >= 3 and b.get('score_band') in ('A', 'B'))
gentle = PK.pick(lambda b: (CR(b), -P(b)), lambda b: CR(b) == min(CR(x) for x in Q))
top_f = PK.pick(lambda b: (-FIB(b), -P(b)), lambda b: FIB(b) >= 8)
low_s = PK.pick(lambda b: (SUG(b), -P(b)), lambda b: SUG(b) == min(SUG(x) for x in Q))
low_p = min(Q, key=lambda b: (P(b), name_key(b)))
C.check(all([best, top_dose, gentle, top_f, low_s]), 'five distinct top picks available')
def sa_note(b):
    rx = [w for w in ('maltitol', 'erythritol', 'sorbitol', 'xylitol') if w in ingr(b).lower()]
    return f" The catch: that low sugar number leans on {names_and(rx)}, not on cutting sweetener out." if rx else ''
PICKS = [
    ['Best overall', best,
     f"The top-graded creatine bar on this page, with {fnum(P(best))}g protein."
     + (f" The tradeoff: its {gstr(CR(best))} dose is trace, not clinical, so don't buy it expecting a performance dose." if CR(best) < 3 else '')],
    ['Highest dose, still solid', top_dose,
     f"A full {gstr(CR(top_dose))} clinical dose that still grades {top_dose['score_band']}."
     + (lambda sib: f" Its own siblings at the same dose range down to {max(sib, key=lambda b: BAND_ORDER.index(b['score_band']))['score_band']}, so the dose alone tells you nothing about quality."
        if sib and max(BAND_ORDER.index(b['score_band']) for b in sib) > BAND_ORDER.index(top_dose['score_band']) else '')(
         [b for b in Q if b['Brand Name'] == top_dose['Brand Name'] and CR(b) == CR(top_dose) and b is not top_dose])],
    ['Gentlest dose', gentle,
     f"{gstr(CR(gentle))}, {SCO(CR, gentle, 'lightest declared dose', False)}, and it grades {gentle['score_band']} with "
     f"{fnum(P(gentle))}g of protein at {fnum(CAL(gentle))} calories."],
    ['Most fiber', top_f, f"{fnum(FIB(top_f))}g of fiber, {SCO(FIB, top_f, 'most')}, alongside a {gstr(CR(top_f))} dose."],
    ['Lowest sugar, read the label anyway', low_s,
     f"Just {fnum(SUG(low_s))}g of sugar, {SCO(SUG, low_s, 'lowest', False)}, at a {gstr(CR(low_s))} dose." + sa_note(low_s)],
]
if P(low_p) < 10 and low_p['Key'] not in PK.used:
    others = [P(b) for b in Q if b is not low_p]
    PICKS.append(['Not actually a protein bar', low_p,
                  f"Only {fnum(P(low_p))}g of protein, far below every other bar on this page (the rest run {fnum(min(others))}g to "
                  f"{fnum(max(others))}g). It's built around creatine, not a protein number, so know what you're buying."])
else:
    PICKS.append(['Highest protein', PK.pick(lambda b: (-P(b), -CR(b))), 'The most protein left among the creatine bars on this page.'])
for p in PICKS:
    if p[1]['score_band'] in ('C', 'D', 'F') and 'grades' not in p[2]:
        p[2] += f" It grades {p[1]['score_band']} on ingredient quality."
PICKS_EXTRA = '''
      <div class="callout-box"><strong>Heads up:</strong> This page is not medical advice. Talk to your doctor before adding a supplement to your routine, especially if you are pregnant, have a kidney condition, or take other medications.</div>'''

# ---------------------------------------------------------------------------
# Tiers
# ---------------------------------------------------------------------------
def tier_card(label, bars):
    by = Counter(b['Brand Name'] for b in bars)
    brand_doses = '; '.join(f"{br} at {doses([b for b in bars if b['Brand Name'] == br])}" for br, _ in by.most_common())
    a = [b for b in bars if b.get('score_band') == 'A']
    f = [b for b in bars if b.get('score_band') == 'F']
    extra = ''
    if a and len(a) == len(GR['A']):
        extra += f" {'Every' if len(a) > 1 else 'The only'} A-grade bar on the page sits in this tier."
    if f:
        extra += f" The page's {'F-grade bars sit' if len(f) > 1 else 'single F-grade bar sits'} in this tier."
    return f'''<div class="score-card">
  <div class="score-card-label">{esc(label)}</div>
  <div class="score-card-val">{len(bars)} bars<span class="oil-card-pct">{g1(100 * len(bars) / N)}% of creatine bars</span></div>
  <div class="score-card-desc">{esc(f"{num_word(len(by)).capitalize()} brand{'s' if len(by) > 1 else ''}: {brand_doses}. Averages a {g1(avg_score(bars))} ingredient score, grades {gl(bars)}.{extra}")}</div>
</div>'''
TIERS_HTML = f'''
    <div class="section-inner">
      <h2 class="section-title">Two dose tiers, not one creatine category</h2>
      <div class="section-body">
        <p>Every bar on this page states a creatine amount on the label, and those amounts cluster into two distinct tiers rather than a smooth range. We split all {N} bars accordingly: a clinical tier matching the 3 to 5 gram maintenance dose most creatine research studies, and a trace tier well under it.</p>
      </div>
      <div class="score-grid" style="margin-top:1.5rem;">
{tier_card(f'Clinical Dose ({doses(CLIN).replace(" and ", "-")})' if len({CR(b) for b in CLIN}) == 2 else 'Clinical Dose (3g+)', CLIN)}
{tier_card('Trace Dose (under 3g)', TRACE)}

      </div>
    </div>
'''

# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------
trace_better = avg_score(TRACE) > avg_score(CLIN)
A_TIERS = {tier(b) for b in GR['A']}
worst = min(Q, key=lambda b: (score(b) if score(b) is not None else 0))
same_dose = [(br, v) for br in BRANDS for v in {CR(b) for b in Q if b['Brand Name'] == br}
             if len([b for b in Q if b['Brand Name'] == br and CR(b) == v]) >= 3]
spread = None
if same_dose:
    br, v = max(same_dose, key=lambda x: len([b for b in Q if b['Brand Name'] == x[0] and CR(b) == x[1]]))
    grp = [b for b in Q if b['Brand Name'] == br and CR(b) == v]
    spread = (br, v, grp, max(score(b) for b in grp) - min(score(b) for b in grp))
BIG = Counter(b['Brand Name'] for b in Q).most_common(1)[0]
INSIGHTS = [
    ('The trace-dose tier scores better than the clinical-dose tier.' if trace_better else 'The clinical-dose tier scores better than the trace tier.',
     f"Bars carrying under 3g average a {g1(avg_score(TRACE))} ingredient score. Bars carrying 3g or more average "
     f"{g1(avg_score(CLIN))}." + (' A bigger creatine number did not buy cleaner ingredients here.' if trace_better else '')),
]
if GR['A']:
    INSIGHTS.append((f"{'Both' if len(GR['A']) == 2 else 'All' if len(GR['A']) > 2 else 'The only'} A-grade "
                     f"bar{'s' if len(GR['A']) > 1 else ''} carr{'y' if len(GR['A']) > 1 else 'ies'} a "
                     + ('trace dose.' if A_TIERS == {'Trace dose'} else 'clinical dose.' if A_TIERS == {'Clinical dose'} else 'mix of doses.'),
                     f"{names_and(full(b) for b in GR['A'])} grade{'' if len(GR['A']) > 1 else 's'} A, at "
                     f"{doses(GR['A'])}."))
if GR['F']:
    INSIGHTS.append((f"The worst-scoring bar carries a {tier(worst).split()[0].lower()} dose.",
                     f"{full(worst)}, at {gstr(CR(worst))}, is the lowest-scoring creatine bar we track, weighed down by "
                     f"{names_and([n.lower() for n, c in chips(worst) if 'concern' in c][:2]) or 'its ingredient list'}."))
if spread:
    br, v, grp, sp = spread
    INSIGHTS.append(('Same brand, same dose, different outcomes.',
                     f"{br}'s {num_word(len(grp))} {gstr(v)} flavors span grades {gl(grp)}. Identical creatine content, a "
                     f"{g1(sp)}-point spread in ingredient score."))
INSIGHTS += [
    (f"{BIG[0]} is the largest creatine lineup we track.",
     f"{BIG[1]} of the {N} creatine bars come from {BIG[0]}, at {doses([b for b in Q if b['Brand Name'] == BIG[0]])}."),
    (f"Only {NB} brands make a creatine bar at all.",
     f"Out of {len({b['Brand Name'] for b in ALL})} brands in our database, creatine remains a niche, training-focused "
     'formulation choice. Most major bar brands skip it entirely.'),
]
FINDINGS = findings_html(f'What we found screening {comma(NT)} bars for creatine', f'{pct(NT - N, NT)}%',
                         'of protein bars carry zero creatine',
                         f'Only {N} of {comma(NT)} bars in our database declare any creatine at all, from just {NB} brands. '
                         'This is a narrow, deliberate formulation choice most brands never touch, not a spectrum.', INSIGHTS)

# ---------------------------------------------------------------------------
# Brand rundown (generated)
# ---------------------------------------------------------------------------
def brand_para(br):
    bs = sort_for_list([b for b in Q if b['Brand Name'] == br])
    n = len(bs)
    top = bs[0]
    grades = [b['score_band'] for b in bs]
    same = len(set(grades)) == 1
    ds = {CR(b) for b in bs}
    dose_txt = (f"{'both' if n == 2 else 'all' if n > 2 else ''} at {'a clinical' if min(ds) >= 3 else 'a trace'} {gstr(min(ds))} dose"
                if len(ds) == 1 else f"at {doses(bs)}").strip()
    s = f"<strong>{esc(br)}</strong> makes {num_word(n)} flavor{'s' if n > 1 else ''}, {dose_txt}"
    s += (f", {'both' if n == 2 else 'all'} grading {grades[0]}." if same and n > 1 else f", grading {names_and(grades)}." if n > 1 else f", grading {grades[0]}.")
    if n > 1 and not same:
        s += f" {esc(nm(top))} is the pick here."
    if P(top) < 10:
        s += f" Just {fnum(P(top))}g of protein, far below the rest of this page."
    return f'        <p>{s}</p>'
BRAND_HTML = f'''
    <div class="section-inner">
      <h2 class="section-title">The {NB} brands making creatine bars right now</h2>
      <div class="section-body creat-brand-notes">
        <p>This category is small enough, {N} bars from {NB} brands, that a Consider/Mixed/Avoid table would mostly be telling you about single flavors dressed up as a brand verdict. Here's the rundown instead. Grades reflect ingredient quality only, not a creatine-specific rating.</p>
{chr(10).join(brand_para(br) for br in BRANDS)}
      </div>
    </div>
'''

# ---------------------------------------------------------------------------
# FAQ
# ---------------------------------------------------------------------------
def brand_faq(name):
    bs = [b for b in Q if b['Brand Name'] == name]
    C.check(bs, f'{name} still makes a creatine bar')
    ab = sum(1 for b in bs if b['score_band'] in ('A', 'B'))
    verdict = 'Yes on ingredient quality' if ab == len(bs) else 'Not on ingredient quality' if ab == 0 else 'Mixed'
    return (f"{verdict}. {num_word(len(bs)).capitalize()} tracked {name} creatine flavor{'s' if len(bs) > 1 else ''}, at {doses(bs)}, "
            f"grading {gl(bs)}: " + ', '.join(f"{nm(b)} ({b['score_band']})" for b in sort_for_list(bs)) + '.')
FAQS = [
    ('How much creatine is actually in these protein bars?',
     f"It varies a lot. Of the {N} bars in our database that declare creatine, {len(TRACE)} carry a trace {doses_or(TRACE)}, and "
     f"{len(CLIN)} carry {doses_or(CLIN)}, in line with the maintenance range most creatine research studies. Check the dose column "
     'before assuming a bar with a creatine badge gives you a meaningful amount.'),
    ('Is 1g of creatine enough to do anything?',
     'Probably not much on its own. Most creatine research on strength, power, and muscle performance uses a maintenance dose of '
     '3 to 5 grams per day, or a loading phase well above that. A 1g dose is well under that range. It\'s not nothing, but it\'s '
     'closer to a token amount than a functional one.'),
    ('What is a clinically effective dose of creatine?',
     'The sports-nutrition research most commonly cites 3 to 5 grams per day for maintenance, taken consistently, with some '
     f"protocols using a short loading phase of up to 20g per day split into smaller doses. {len(CLIN)} of the {N} bars on this "
     'page land at 3g or more. This page is not medical advice. Talk to your doctor or a sports dietitian before adding a '
     'supplement to your routine.'),
    ('Does creatine in a protein bar work the same as creatine powder?',
     'The form of creatine matters more than the delivery vehicle. Bars that name their source list creatine monohydrate, the '
     'same form used in most creatine research and the powder aisle. A bar just bundles the dose into a snack instead of a scoop.'),
    ('Why do so few protein bars contain creatine?',
     'Creatine is a deliberate supplement-style formulation choice aimed at a training-focused customer, not a byproduct of a '
     f'typical bar recipe. Only {N} of {comma(NT)} bars in our database declare any creatine at all, from just {NB} brands. '
     'Most major bar brands, including Quest and Barebells, skip it entirely.'),
    ('Is JiMMYBAR! good for creatine?', brand_faq('JiMMYBAR!')),
    ('Is Rello good for creatine?', brand_faq('Rello')),
    ('How many protein bars in your database contain creatine?',
     f'Out of {comma(NT)} bars in our database, {N} declare any creatine content at all, about {pct(N, NT)}% of the full '
     f'database, across just {NB} brands.'),
]
C.check(all('monohydrate' in ingr(b).lower() for b in Q if 'creatine' in ingr(b).lower()), 'bars that name their creatine list monohydrate')
C.check(not any(QF(b) for b in ALL if b['Brand Name'] in ('Quest', 'Barebells')), 'Quest and Barebells make no creatine bar')

# ---------------------------------------------------------------------------
# Regions
# ---------------------------------------------------------------------------
MX = max(CR(b) for b in Q)
MN = min(CR(b) for b in Q)
TITLE = f'Only {N} of {comma(NT)} Protein Bars Have Creatine, Ranked'
H1 = f'Protein Bars with Creatine - We Screened {comma(NT)} Bars, {N} Had Any'
DESC = (f'We screened {comma(NT)} bars for declared creatine. Only {N} qualify, from a trace {gstr(MN)} dose to a clinical '
        f'{gstr(MX)}, across {NB} brands, ranked by ingredient quality.')
OG = (f'Only {N} of {comma(NT)} bars declare creatine, from a trace {gstr(MN)} dose to a clinical {gstr(MX)}. Ranked by '
      'ingredient quality, not marketing claims.')
REGIONS = [r for r in guide_head_regions(title=TITLE, h1=H1, desc=DESC, og_desc=OG, url=URL, about='Creatine Protein Bars',
                                         published=PUBLISHED, faqs=FAQS, picks=PICKS) if r[0] not in ('social', 'jsonld-itemlist')]
ITEMS = {'@context': 'https://schema.org', '@type': 'ItemList', 'name': 'Protein bars with creatine ranked by ingredient quality',
         'numberOfItems': N, 'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'name': full(b)} for i, b in enumerate(sort_for_list(Q))]}
REGIONS += [
    ('jsonld-itemlist', '<script type="application/ld+json">\n  ' + json.dumps(ITEMS, ensure_ascii=False, separators=(',', ':')) + '</script>'),
    ('social', social_title_html(TITLE, OG, URL).replace('  <meta property="og:site_name" content="Know Your Bar">\n', '')),
    ('hero', f'''<h1 class="hero-title">{esc(H1)}</h1>
    <p class="hero-sub" style="color:#e8e4dc;">We pulled every bar in our {comma(NT)}-bar database with a declared creatine amount, no minimum required. Only {N} qualify, across just {NB} brands, small enough that this comes down to individual formulas, not a genre. The doses split into two real tiers: {len(CLIN)} bars carry {doses_or(CLIN)}, in line with the maintenance range most creatine research studies, while {len(TRACE)} carry a trace {doses_or(TRACE)}, well under that range. We ranked all {N} by ingredient quality{', and dose does not predict the winner: the best-scoring bars on this page carry a trace amount, not a clinical one' if A_TIERS == {'Trace dose'} else ''}.</p>'''),
    ('snapshot', f'''
    <div class="snap-item"><div class="snap-value">{N}</div><div class="snap-label">Bars with creatine</div></div>
    <div class="snap-item"><div class="snap-value">{NB}</div><div class="snap-label">Brands represented</div></div>
    <div class="snap-item"><div class="snap-value">{g1(sum(CR(b) for b in Q) / N)}g</div><div class="snap-label">Avg dose per bar</div></div>
    <div class="snap-item"><div class="snap-value">{gstr(MX)}</div><div class="snap-label">Highest declared dose</div></div>
    <div class="snap-item"><div class="snap-value">{pct(N, NT)}%</div><div class="snap-label">Of the full database</div></div>
  '''),
    ('picks', picks_with_extra_html('Top picks for creatine + quality',
                                    'Grades below reflect ingredient quality only, not a creatine-specific rating, and not a claim '
                                    'about whether a given dose does anything for you.', PICKS, PICKS_EXTRA)),
    ('two-dose-tiers-not-one-creatine-category', TIERS_HTML),
    ('findings', FINDINGS),
    ('the-6-brands-making-creatine-bars-right-', BRAND_HTML),
    ('explore-more', f'''
<a href="/caffeine-protein-bars" class="explore-more-card">
  <div class="explore-more-title">Caffeine Protein Bars</div>
  <div class="explore-more-desc">Only {guide_count(ALL, 'caffeine-protein-bars')} of {comma(NT)} bars declare caffeine, ranked by ingredient quality.</div>
</a>
<a href="/clean-protein-bars" class="explore-more-card">
  <div class="explore-more-title">Clean Protein Bars</div>
  <div class="explore-more-desc">A or B grade bars with no artificial sweeteners and no processed oils.</div>
</a>
<a href="/glp1-protein-bars" class="explore-more-card">
  <div class="explore-more-title">GLP-1 Protein Bars</div>
  <div class="explore-more-desc">High protein, low calorie, 0g sugar alcohol, A or B grade only.</div>
</a>
      '''),
    ('faq', faq_items_html(FAQS)),
]
def creatine_nutr(b, pairs):
    out = []
    for lab, v in pairs:
        out.append([lab, v])
        if lab == 'Sugar Alcohol':
            out.append(['Creatine', gstr(CR(b))])
    return out
REGIONS += dose_list_regions(Q, ALL, f'{N} protein bars with creatine, ranked by ingredient quality',
                             field='Creatine (g)', data_attr='creatine', fmt=gstr, grid_label='Creatine',
                             grid_tag=lambda b: [tier(b), 'rank-gray'],
                             extra_badges=lambda b: '\n    <div class="boost-badges"><span class="boost-badge" title="Creatine">Creatine</span></div>',
                             nutr_extra=creatine_nutr)

if __name__ == '__main__':
    n = build_guide_page(PAGE, REGIONS, Q, ALL, C)
    print(f'{PAGE}: {N} creatine bars, {n} rows, grade-sync 0 mismatches')
    for label, b, why in PICKS:
        print(f'  {label}: {full(b)} ({b["score_band"]})')
