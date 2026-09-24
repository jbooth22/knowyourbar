#!/usr/bin/env python3
"""Rebuild keto-protein-bars.html from bars.js.

Run from the repo root:  python3 build_keto_protein_bars.py

Opens the LIVE page and rewrites only the <!-- kyb:NAME --> regions (nav,
footer, fonts, CSS and JS stay as deployed). Every number, pick, brand row and
bar row comes from bars.js. Copy that depends on a fact is checked; if one
stops being true the build stops and lists it.

Screen: GUIDE_FILTERS['keto-protein-bars'] = net carbs <= 8 (carbs - fiber -
sugar alcohol, full subtraction), protein >= 10, fat >= 8, no maltitol family.
The bar list uses the Keto column set (FAT + NET CARB instead of CAL + SGR).
"""
from kyb_guide_lib import *

PAGE = 'keto-protein-bars.html'
URL = 'https://knowyourbar.com/keto-protein-bars'
PUBLISHED = '2026-04-29'

ALL = load_bars()
QF = GUIDE_FILTERS['keto-protein-bars']
Q = [b for b in ALL if QF(b)]
D = [b for b in ALL if not QF(b)]
N, ND, NT = len(Q), len(D), len(ALL)
BRANDS_ALL = len({b['Brand Name'] for b in ALL})
BRANDS_Q = len({b['Brand Name'] for b in Q})
GR = {g: sum(1 for b in Q if b.get('score_band') == g) for g in BAND_ORDER}
C = Claims()

NC = net_carbs
def FAT(b): return num(b.get('Total Fat (g)')) or 0
def CARB(b): return num(b.get('Total Carbohydrates (g)')) or 0
def FATPCT(b): return 900 * FAT(b) / CAL(b) if CAL(b) else 0

SCREEN = Screen(ALL, [
    ('nc', 'net carbs', lambda b: NC(b) > 8),
    ('protein', 'protein', lambda b: P(b) < 10),
    ('fat', 'fat', lambda b: FAT(b) < 8),
    ('maltitol', 'maltitol or a related sweetener', has_maltitol_family),
])
FAIL = {k: SCREEN.count(k) for k in ('nc', 'protein', 'fat', 'maltitol')}
MULTI = SCREEN.multi(D)
SINGLE = ND - MULTI
C.check(all(SCREEN.fails[b['Key']] for b in D) and not any(SCREEN.fails[b['Key']] for b in Q), 'the four checks match the keto filter')
LOWS = [b for b in ALL if SUG(b) <= 1]
LOWS_M = pct(sum(1 for b in LOWS if has_maltitol_family(b)), len(LOWS))
AVG_FAT, AVG_NC = avg(Q, 'Total Fat (g)'), sum(NC(b) for b in Q) / N

# ---------------------------------------------------------------------------
# Top picks (band first, keto numbers break ties)
# ---------------------------------------------------------------------------
PK = Picker(Q)
SC = Scoper(Q, 'that clears the keto screen')
best = PK.rank_sum([(NC, False), (FAT, True), (P, True)])
low_nc = PK.pick(lambda b: (NC(b), -FAT(b)))
fatty = PK.pick(lambda b: (-FATPCT(b), NC(b)))
top_p = PK.pick(lambda b: (-P(b), NC(b)))
no_sa = PK.pick(lambda b: (NC(b), -FAT(b)), lambda b: SA(b) == 0 and not has_tag(b, 'Sugar Alcohols'))
low_carb = PK.pick(lambda b: (CARB(b), NC(b)))
C.check(all([best, low_nc, fatty, top_p, no_sa, low_carb]), 'six distinct top picks available')
PICKS = [
    ['Best overall', best,
     f"{fnum(NC(best))}g net carbs, {fnum(P(best))}g protein, and {fnum(FAT(best))}g fat on {a_an(best['score_band'])} "
     f"{best['score_band']}-grade label. Balanced across all three keto numbers rather than an extreme on one."],
    ['Lowest net carbs', low_nc,
     f"{fnum(NC(low_nc))}g net carbs, {SC(NC, low_nc, 'lowest', False)}."
     + (f" It gets there partly by subtracting {fnum(SA(low_nc))}g of sugar alcohol." if SA(low_nc) else
        f" No sugar alcohol involved: that is {fnum(CARB(low_nc))}g of carbs minus {fnum(FIB(low_nc))}g of fiber.")],
    ['Most fat-forward', fatty,
     f"{fnum(FAT(fatty))}g fat, {round(FATPCT(fatty))}% of its {fnum(CAL(fatty))} calories, "
     f"{SC(FATPCT, fatty, 'highest fat share')}. Closest to a classic high-fat keto split."],
    ['Highest protein', top_p,
     f"{fnum(P(top_p))}g protein with {fnum(NC(top_p))}g net carbs, {SC(P, top_p, 'most protein')}."],
    ['No sugar alcohol', no_sa,
     f"{fnum(NC(no_sa))}g net carbs with 0g sugar alcohol, so the number doesn't lean on subtracting a sweetener. "
     f"{fnum(FAT(no_sa))}g fat and {fnum(P(no_sa))}g protein."],
    ['Lowest total carbs', low_carb,
     f"{fnum(CARB(low_carb))}g total carbohydrates before anything is subtracted, {SC(CARB, low_carb, 'lowest', False)}. "
     "Useful if you count total carbs instead of net."],
]
PICKS_EXTRA = f'''
      <div class="callout-box"><strong>Heads up:</strong> We are not doctors or dietitians. These are the qualities we see people following keto look for, so that is what we filtered on. This page is not medical advice. Talk to your doctor or a registered dietitian about what actually fits your goals.</div>
      <div class="guide-jump-row">
        <a href="#full-bar-list" class="guide-jump-link">Jump straight to all {comma(N)} bars &darr;</a>
      </div>'''
PICKS_INTRO = ("Everyone doing keto has their own priorities, but if you are on this page you probably already know you want "
               "low net carbs and real fat, not just a low sugar number on the label. Here are the standouts for what people "
               "typically look for, all clearing the full four-criteria screen. Grades below reflect ingredient quality only, "
               "not a keto-specific rating.")

# ---------------------------------------------------------------------------
# What we screened for
# ---------------------------------------------------------------------------
SCREENED = f'''
    <div class="section-inner">
      <h2 class="section-title">What we screened for on this page</h2>
      <div class="section-body">
        <p>People following keto usually care about two things above everything else on a protein bar: how many net carbs it actually delivers once fiber and sugar alcohols are subtracted, and whether it has enough fat to fit the macro pattern instead of just being low-carb. We added two more filters on top: enough protein to be worth eating, and no maltitol or its close relatives (maltitol syrup, polyglycitol, hydrogenated starch hydrolysates), a sugar alcohol that raises blood glucose more than most others and more than labels suggest. {N} of {comma(NT)} bars, {pct(N, NT)}% of the database, clear all four.</p>
      </div>
      <div class="score-grid" style="margin-top:1.5rem;">
{simple_card_html('Net Carbs Over 8g', FAIL['nc'], NT, 'Net carbs (total carbs minus fiber minus sugar alcohols) is the number that actually determines whether a bar fits a ketogenic diet, and it is rarely printed on the label.')}
{simple_card_html('Fat Under 8g', FAIL['fat'], NT, 'A ketogenic diet runs on fat for fuel. A bar can be low-carb and still not have enough fat to fit the pattern. We required at least 8g.')}
{simple_card_html('Protein Under 10g', FAIL['protein'], NT, 'Low enough protein and a bar stops functioning as a protein bar. We required at least 10g.')}
{simple_card_html('Contains Maltitol or Similar', FAIL['maltitol'], NT, f'Maltitol and its syrupy relatives (maltitol syrup, polyglycitol, hydrogenated starch hydrolysates) have a glycemic index close to half of table sugar, well above most other sugar alcohols, but labeling rules let brands leave them off the sugar line entirely. {LOWS_M}% of bars with 1g or less listed sugar still contain one of these.')}
</div>
    </div>
'''

LOOK_FOR = f'''
    <div class="section-inner">
      <h2 class="section-title">What actually makes a protein bar keto-friendly</h2>
      <div class="section-body">
        <p>Search for the best keto protein bars and most lists rank by sugar grams alone. That number is not nothing, but it is not what your body runs on either. A ketogenic diet works by keeping carbs low enough that you burn fat for fuel instead of glucose, and that means net carbs and fat both have to be part of the screen, not just a low number on the sugar line.</p>
        <p>Net carbs (total carbs minus fiber minus sugar alcohols) is the number that actually determines whether a bar fits a ketogenic macro pattern, and brands rarely print it directly. A bar can say 1g sugar and still carry 20g of net carbs once you subtract the right things, or fail to subtract anything at all. Fat matters just as much on the other side: a bar can clear a low net carb bar and still not have enough fat to function as fuel on keto, which is why we require 8g or more on top of the carb ceiling, not a low-carb number by itself.</p>
        <p>The maltitol trap covered above is one version of a wider pattern. "Keto-friendly" and "sugar-free" describe what a label is allowed to say, not what the macro panel actually adds up to. {LOWS_M}% of bars with 1g or less of listed sugar in our database still contain maltitol or a close relative, a sugar alcohol with a glycemic index around half of table sugar. The only way to know is to read the full nutrition panel and ingredient list, not the front of the package.</p>
        <div class="callout-box">
          <strong>Four questions worth asking before you buy a bar for keto:</strong>
          <ul class="kt-criteria-list" style="margin-top:0.5rem;">
            <li><strong>What are the net carbs,</strong> not just the sugar grams on the front of the label?</li>
            <li><strong>Does it actually have enough fat</strong> to fit a ketogenic macro pattern, or is it just low-carb?</li>
            <li><strong>Does it use maltitol, polyglycitol, or hydrogenated starch hydrolysates</strong> instead of sugar, rather than a lower-glycemic sugar alcohol or no sweetener at all?</li>
            <li><strong>Does the protein source and ingredient list</strong> hold up on its own, separate from whether the macros fit keto?</li>
          </ul>
        </div>
        <p>How strict "keto" needs to be varies by person and by which version of the diet you are following. Everything on this page is a starting filter built from label data, not a substitute for tracking your own carb budget or a conversation with a doctor or dietitian about what fits your goals.</p>
      </div>
    </div>
'''

# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------
C.check(FAIL['nc'] > max(FAIL['fat'], FAIL['protein'], FAIL['maltitol']), 'net carbs is the toughest single check')
C.check(GR['A'] < N / 2, 'fewer than half the qualifying bars are A grade')
most_multi = MULTI > SINGLE
INSIGHTS = [
    ('Net carbs is the single toughest filter.',
     f"{comma(FAIL['nc'])} bars ({pct(FAIL['nc'], NT)}%) fail the net carb check, far more than fail on fat ({pct(FAIL['fat'], NT)}%) "
     f"or protein ({pct(FAIL['protein'], NT)}%). Most protein bars are simply not built with keto-level carb counts in mind."),
    ('The maltitol trap is real here too.',
     f'{LOWS_M}% of bars with 1g or less of listed sugar still contain maltitol or a close relative. A bar can market itself '
     'as keto-friendly on the front while quietly delivering a sugar alcohol that still moves blood glucose.'),
    ('Meeting the macros does not guarantee a clean label.',
     f"Only {GR['A']} of {N} qualifying bars earn an A on ingredient quality. {GR['B']} land at a B, and "
     f"{N - GR['A'] - GR['B']} at C or below, hitting the keto macros with a more processed ingredient list."),
    ('Most disqualified bars fail more than one check.' if most_multi else 'Most disqualified bars miss on a single check.',
     f'{comma(MULTI)} of {comma(ND)} disqualified bars fail two or more of the four criteria at once. {comma(SINGLE)} miss on a single count.'),
    (f'{BRANDS_Q} brands have at least one qualifying flavor.',
     f'Out of {BRANDS_ALL} tracked brands, {BRANDS_Q} have at least one flavor that clears all four checks.'),
    (f'Qualifying bars average {fnum(round(AVG_FAT, 1))}g of fat.',
     f'Comfortably above the 8g minimum we required, and qualifying bars average just {fnum(round(AVG_NC, 1))}g net carbs '
     'against our 8g ceiling.'),
]
C.check(AVG_FAT > 9 and AVG_NC < 7, 'qualifying averages sit comfortably inside the thresholds')
FINDINGS = findings_html(f'What we found screening {comma(NT)} bars for keto-friendly criteria', f'{pct(ND, NT)}%',
                         'of bars fail at least one of our four checks',
                         f'{comma(ND)} of {comma(NT)} bars fail on net carbs, protein, fat, maltitol, or some combination. '
                         f'{comma(MULTI)} of those fail more than one check at once.', INSIGHTS)

# ---------------------------------------------------------------------------
# Brand tables
# ---------------------------------------------------------------------------
SPLIT = brand_split(ALL, QF)
def avg_nc(r): return sum(NC(b) for b in r['bars']) / len(r['bars'])
def avg_fat(r): return avg(r['bars'], 'Total Fat (g)')
def pick_of(r):
    band = next(g for g in BAND_ORDER if any(b.get('score_band') == g for b in r['qual']))
    return min((b for b in r['qual'] if b.get('score_band') == band), key=lambda b: (NC(b), -FAT(b), name_key(b)))
def note(r, kind):
    if kind == 'consider':
        if r['d'] == 0:
            return f"{all_n_flavors(r['total'])} clear the net carb, protein, and fat screen with no maltitol."
        return (f"{r['q']} of {r['total']} flavors clear the full keto screen, averaging {fnum(round(avg_nc(r), 1))}g net carbs "
                f"and {fnum(round(avg_fat(r), 1))}g fat across the whole lineup.")
    if kind == 'mixed':
        return f"{r['q']} of {r['total']} flavors clear the full screen. {pick_of(r)['Flavor Name']} is the clean pick."
    lead = f"Only {pick_of(r)['Flavor Name']} clears it. " if r['q'] == 1 else (f"{r['q']} flavors clear it. " if r['q'] else '')
    return (f"{lead}Misses mainly on {names_and(SCREEN.misses_mainly(r['disq']))}. Averages {fnum(round(avg_nc(r), 1))}g net "
            f"carbs and {fnum(round(avg_fat(r), 1))}g fat.")
BRANDS = macro_brand_tables_html(
    SPLIT, h2='Best Brands for Keto Protein Bars', table_id='kt', table_class='kt-brand-table',
    intro_html='''        <p>We are not doctors or dietitians, and this is not medical advice. For every brand we track, we checked what share of its flavors clear the net carb, protein, fat, and maltitol screen used above, then averaged net carbs and fat across its whole lineup. Grade columns show ingredient quality only, not a keto-specific rating. Click any brand name to jump to its flavors in the table below.</p>
        <p><strong>Consider</strong> means at least 75% of the brand's tracked flavors clear our full screen (allowing at most 2 misses). <strong>Mixed</strong> means some flavors clear it and some do not, so the specific flavor matters. <strong>Avoid</strong> means at least 80% of the brand's tracked flavors miss it and fewer than 3 clear it.</p>''',
    cols=[('Flavors That Qualify', lambda r: f"{r['q']}/{r['total']}"),
          ('Ingredient Quality', lambda r: grade_range_html(*grade_range(r['bars']))),
          ('Avg Net Carbs', lambda r: f'{fnum(round(avg_nc(r), 1))}g'),
          ('Avg Fat', lambda r: f'{fnum(round(avg_fat(r), 1))}g')],
    notes={'consider': "At least 75% of these brands' tracked flavors clear our net carb, protein, fat, and maltitol screen (allowing at most 2 misses).",
           'mixed': 'Some flavors from these brands clear the screen, some do not. The specific flavor matters more than the brand name.',
           'avoid': "Most or all of these brands' tracked flavors miss the net carb, protein, fat, and maltitol screen."},
    row_note=note)

# ---------------------------------------------------------------------------
# FAQ
# ---------------------------------------------------------------------------
def brand_row(name): return next((r for r in SPLIT[0] + SPLIT[1] + SPLIT[2] if r['brand'] == name), None)
def brand_faq(name):
    r = brand_row(name)
    C.check(r is not None, f'{name} is in bars.js')
    tail = f"averaging {fnum(round(avg_nc(r), 1))}g net carbs and {fnum(round(avg_fat(r), 1))}g fat per bar"
    if r['d'] == 0:
        return f"By our screen, yes: all {r['total']} tracked {name} flavors clear our net carb, protein, fat, and maltitol criteria, {tail}."
    if r['q'] == 0:
        return (f"Not by our screen: none of the {r['total']} tracked {name} flavors clear all four criteria. They miss mainly on "
                f"{names_and(SCREEN.misses_mainly(r['disq']))}.")
    return (f"Mixed by our screen: {r['q']} of {r['total']} tracked {name} flavors clear all four criteria. The specific flavor "
            f"matters more than the brand name here, so check the flavor table above before assuming the whole lineup qualifies.")
FAQS = [
    ('What should I look for in a keto protein bar?',
     'We are not doctors, but here is what we filtered on: net carbs, protein, fat, and zero maltitol. Net carbs (total carbs '
     'minus fiber minus sugar alcohols) is the number that determines whether a bar actually fits a ketogenic diet, not the '
     'sugar line alone. We required 8g or less net carbs, 10g or more protein, 8g or more fat, and no maltitol or its close '
     'relatives for every bar on this list.'),
    ('How do you calculate net carbs?',
     "Net carbs = total carbohydrates minus dietary fiber minus sugar alcohols. We use the values straight off each bar's "
     'nutrition facts panel. Most sugar alcohols have a low enough glycemic impact that this formula treats them fairly. The '
     'exception, maltitol and its syrupy relatives, is excluded from this list entirely rather than adjusted for. See the next '
     'question for why.'),
    ('Why do you exclude maltitol instead of adjusting the math for it?',
     'We looked at doing per-molecule math instead of a flat formula, and decided against it. Most sugar alcohols (erythritol, '
     'xylitol, sorbitol, isomalt, lactitol, mannitol) have a glycemic index under 15, close enough to negligible that our '
     'standard net carbs formula already treats them fairly without any adjustment. Maltitol and its syrupy relatives '
     '(maltitol syrup, polyglycitol, hydrogenated starch hydrolysates) sit at a meaningfully higher glycemic index, roughly '
     '35, about half of table sugar. Rather than build a formula with different fractions for eight different molecules, we '
     'exclude bars that use these specific ones. A hard exclude is something we can state with confidence. A per-molecule '
     'formula is not, and we would rather be clear about what we are and are not confident in.'),
    ('What is the maltitol trap in keto-marketed protein bars?',
     "Maltitol is a sugar alcohol with a glycemic index around 35, well above erythritol's near-zero impact and closer to half "
     'of table sugar. Labeling rules let brands leave sugar alcohols off the sugar line, so a bar can say 0g or 1g sugar and '
     f'market itself as keto-friendly while still containing maltitol. In our database, {LOWS_M}% of bars with 1g or less '
     'listed sugar still contain it or a close relative. Every bar on this list has been checked and confirmed free of '
     'maltitol, maltitol syrup, polyglycitol, and hydrogenated starch hydrolysates.'),
    ('Why does fat matter for a keto protein bar?',
     'A ketogenic diet runs on fat for fuel instead of carbohydrates, so a bar needs meaningful fat to fit the macro pattern, '
     f'not just low carbs. We required at least 8g of fat for every bar on this list, and qualifying bars average {fnum(round(AVG_FAT, 1))}g.'),
    ('What does the ingredient quality grade mean on this page?',
     "Our A through F grade rates how clean and minimally processed a bar's ingredients are. It is a separate measurement "
     'from keto suitability. A bar can score an A on ingredient quality and still be a poor macro fit for keto, or vice versa. '
     'We show it here as extra context, but the primary filter for this list is net carbs, protein, fat, and the maltitol exclusion.'),
    ('Are sugar alcohols keto-friendly?',
     'It depends which one. Erythritol, xylitol, sorbitol, isomalt, lactitol, and mannitol all have a low enough glycemic '
     "impact that they get folded into our standard net carbs calculation and don't count against a bar here. Maltitol and its "
     'syrupy relatives raise blood sugar meaningfully despite being marketed as sugar free, so those are a hard exclude from '
     'this list regardless of amount.'),
    ('Is IQ Bar good for keto?', brand_faq('IQ Bar')),
    ('Is Quest good for keto?', brand_faq('Quest')),
    ('How is the brand table below different from the ranked bar list above?',
     'The ranked list at the top of this page covers individual flavors that pass all four criteria. The brand table further '
     "down rolls that up to the brand level: what share of each brand's tracked flavors qualify, plus average net carbs and fat "
     'across the whole lineup. Use the bar list to find a specific flavor, and the brand table to get a quick read on a brand '
     'before you go looking.'),
    ('How many protein bars in your database qualify for this list?',
     f'Out of {comma(NT)} bars in our database, {N} meet all four criteria: 8g or less net carbs, 10g or more protein, 8g or '
     f'more fat, and no maltitol. That is about {pct(N, NT)}% of the full database.'),
]

# ---------------------------------------------------------------------------
# Regions
# ---------------------------------------------------------------------------
TITLE = f'Keto Protein Bars - {N} Bars Ranked by Ingredient Quality'
H1 = f'Best Keto Protein Bars - We Screened {comma(NT)} Bars, {N} Passed'
DESC = f'We screened {comma(NT)} bars for net carbs, protein, fat, and maltitol. {N} pass. {LOWS_M}% of low-sugar bars still hide maltitol.'
REGIONS = [r for r in guide_head_regions(title=TITLE, h1=H1, desc=DESC, og_desc=DESC, url=URL, about='Keto Diet Eating Guide',
                                         published=PUBLISHED, faqs=[(q, plain_text(a)) for q, a in FAQS], picks=PICKS)
           if r[0] != 'jsonld-itemlist']   # this page carries a static Dataset block instead
REGIONS += [
    ('hero', f'''<h1 class="hero-title">{esc(H1)}</h1>
    <p class="hero-sub" style="color:#e8e4dc;">Keto is a macro game, not just a low-sugar game. Here is what we did: we screened every bar in our database against four thresholds people following keto commonly look for: 8g or less net carbs, 10g or more protein, 8g or more fat, and zero maltitol or its high-impact relatives. {N} of {comma(NT)} bars pass all four. See exactly how each bar stacks up, then check the brand table below for a quick read on your favorite brand.</p>'''),
    ('snapshot', f'''
    <div class="snap-item"><div class="snap-value">{comma(N)}</div><div class="snap-label">Bars qualify</div></div>
    <div class="snap-item"><div class="snap-value">{comma(ND)}</div><div class="snap-label">Bars disqualified</div></div>
    <div class="snap-item"><div class="snap-value">{GR['A']}</div><div class="snap-label">A-grade bars</div></div>
    <div class="snap-item"><div class="snap-value">{BRANDS_Q}</div><div class="snap-label">Brands represented</div></div>
    <div class="snap-item"><div class="snap-value">{AVG_FAT:.1f}g</div><div class="snap-label">Avg fat</div></div>
  '''),
    ('picks', picks_with_extra_html('Top picks for keto', PICKS_INTRO, PICKS, PICKS_EXTRA)),
    ('screened', SCREENED),
    ('what-to-look-for', LOOK_FOR),
    ('findings', FINDINGS),
    ('brands', BRANDS),
    ('cta-heading', f'<h2 class="explore-cta-main-heading">See every bar that fits, not just the {comma(N)} on this page</h2>'),
    ('explore-more', '''
<a href="/no-sugar-alcohols" class="explore-more-card">
  <div class="explore-more-title">No Sugar Alcohols</div>
  <div class="explore-more-desc">Bars that skip maltitol, erythritol, and other sugar alcohols entirely.</div>
</a>
<a href="/best-bars-for-diabetics" class="explore-more-card">
  <div class="explore-more-title">Best Bars for Diabetics</div>
  <div class="explore-more-desc">Screened for sugar, net carbs, fiber, protein, grade, and maltitol.</div>
</a>
<a href="/no-seed-oils" class="explore-more-card">
  <div class="explore-more-title">No Seed Oils</div>
  <div class="explore-more-desc">Bars that skip processed seed and vegetable oils entirely.</div>
</a>
      '''),
    ('faq', faq_items_html(FAQS)),
]
REGIONS += guide_list_regions(Q, ALL, heading=f'{comma(N)} keto protein bars, ranked by ingredient quality', variant='keto')

if __name__ == '__main__':
    n = build_guide_page(PAGE, REGIONS, Q, ALL, C)
    print(f'{PAGE}: {N} qualify, {ND} disqualified, {n} rows, grade-sync 0 mismatches')
    for label, b, why in PICKS:
        print(f'  {label}: {full(b)} ({b["score_band"]})')
