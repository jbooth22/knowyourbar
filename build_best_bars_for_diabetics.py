#!/usr/bin/env python3
"""Rebuild best-bars-for-diabetics.html from bars.js.

Run from the repo root:  python3 build_best_bars_for_diabetics.py

Opens the LIVE page and rewrites only the <!-- kyb:NAME --> regions (nav,
footer, fonts, CSS and JS stay as deployed). Every number, pick, brand row and
bar row comes from bars.js. Copy that depends on a fact is checked; if one
stops being true the build stops and lists it.

Screen: GUIDE_FILTERS['best-bars-for-diabetics'] = sugar <= 5, net carbs <= 10
(carbs - fiber - sugar alcohol), fiber >= 5, protein >= 10, A or B grade, no
maltitol family. Keeps the required "we are not doctors or dietitians" copy.
"""
from kyb_guide_lib import *

PAGE = 'best-bars-for-diabetics.html'
URL = 'https://knowyourbar.com/best-bars-for-diabetics'
PUBLISHED = '2026-04-29'

ALL = load_bars()
QF = GUIDE_FILTERS['best-bars-for-diabetics']
Q = [b for b in ALL if QF(b)]
D = [b for b in ALL if not QF(b)]
N, ND, NT = len(Q), len(D), len(ALL)
BRANDS_ALL = len({b['Brand Name'] for b in ALL})
BRANDS_Q = len({b['Brand Name'] for b in Q})
GR = {g: sum(1 for b in Q if b.get('score_band') == g) for g in BAND_ORDER}
C = Claims()
NC = net_carbs

SCREEN = Screen(ALL, [
    ('sugar', 'sugar', lambda b: SUG(b) > 5),
    ('nc', 'net carbs', lambda b: NC(b) > 10),
    ('fiber', 'fiber', lambda b: FIB(b) < 5),
    ('protein', 'protein', lambda b: P(b) < 10),
    ('grade', 'ingredient grade', lambda b: b.get('score_band') not in ('A', 'B')),
    ('maltitol', 'maltitol or a related sweetener', has_maltitol_family),
])
FAIL = {k: SCREEN.count(k) for k, _, _ in SCREEN.checks}
MULTI = SCREEN.multi(D)
SINGLE = ND - MULTI
C.check(all(SCREEN.fails[b['Key']] for b in D) and not any(SCREEN.fails[b['Key']] for b in Q), 'the six checks match the diabetics filter')
LOWS = [b for b in ALL if SUG(b) <= 1]
LOWS_M = pct(sum(1 for b in LOWS if has_maltitol_family(b)), len(LOWS))
AVG_FIB = avg(Q, 'Dietary Fiber (g)')
C.check(GR['A'] + GR['B'] == N, 'every qualifying bar is A or B')

# ---------------------------------------------------------------------------
# Top picks
# ---------------------------------------------------------------------------
PK = Picker(Q)
SCO = Scoper(Q, 'that clears the diabetic screen')
def no_sa(b): return SA(b) == 0 and not has_tag(b, 'Sugar Alcohols')
best = PK.rank_sum([(SUG, False), (NC, False), (FIB, True)])
low_s = PK.pick(lambda b: (SUG(b), NC(b)))
low_nc = PK.pick(lambda b: (NC(b), SUG(b)))
top_f = PK.pick(lambda b: (-FIB(b), SUG(b)))
clean_nc = PK.pick(lambda b: (NC(b), SUG(b)), no_sa)
top_p = PK.pick(lambda b: (-P(b), CAL(b)))
C.check(all([best, low_s, low_nc, top_f, clean_nc, top_p]), 'six distinct top picks available')
def sa_note(b):
    if SA(b):
        return f" That number leans on {fnum(SA(b))}g of sugar alcohol being subtracted, so it is a low-net-carb pick, not a low-sugar-alcohol one."
    if has_tag(b, 'Sugar Alcohols'):
        return ' The label lists 0g sugar alcohol, though the ingredient list does include one.'
    return ''
PICKS = [
    ['Best overall', best,
     f"{fnum(SUG(best))}g sugar, {fnum(NC(best))}g net carbs, {fnum(FIB(best))}g fiber, and {fnum(P(best))}g protein. "
     "Strong on sugar, net carbs, and fiber together rather than an extreme on one."],
    ['Lowest sugar', low_s,
     f"{fnum(SUG(low_s))}g of sugar, {SCO(SUG, low_s, 'lowest', False)}, with {fnum(NC(low_s))}g net carbs and {fnum(FIB(low_s))}g fiber."],
    ['Lowest net carbs', low_nc,
     f"{fnum(NC(low_nc))}g net carbs, {SCO(NC, low_nc, 'lowest', False)}." + sa_note(low_nc)],
    ['Most fiber', top_f,
     f"{fnum(FIB(top_f))}g of fiber, {SCO(FIB, top_f, 'most')}, which slows how fast the rest of its carbs hit your blood sugar."],
    ['No sugar alcohol', clean_nc,
     f"{fnum(NC(clean_nc))}g net carbs with no sugar alcohol on the label or in the ingredients, so nothing is being subtracted "
     f"to get there. {fnum(SUG(clean_nc))}g sugar and {fnum(FIB(clean_nc))}g fiber."],
    ['Highest protein', top_p,
     f"{fnum(P(top_p))}g protein at {fnum(CAL(top_p))} calories, {SCO(P, top_p, 'most protein')}."],
]
_mx = max(SUG(p[1]) for p in PICKS)
for p in PICKS:
    if SUG(p[1]) == _mx and _mx >= 4 and p[0] != 'Best overall':
        p[2] += f" It also carries {fnum(_mx)}g of sugar, the highest of these six picks, though still under the 5g screen."
        break
PICKS_EXTRA = '''
      <div class="callout-box"><strong>Heads up:</strong> We are not doctors or dietitians. These are the qualities we see people managing diabetes look for, so that is what we filtered on. This page is not medical advice. Talk to your doctor or a registered dietitian about what actually fits your treatment plan.</div>'''
PICKS_INTRO = ("Everyone managing blood sugar has their own priorities, but if you are on this page you probably already know "
               "you want low sugar, low net carbs, and enough fiber to slow things down. Here are the standouts for what "
               "people typically look for, all clearing the full six-criteria screen. Grades below reflect ingredient quality "
               "only, not a diabetic-specific rating.")

# ---------------------------------------------------------------------------
# What we screened for / what to look for
# ---------------------------------------------------------------------------
SCREENED = f'''
    <div class="section-inner">
      <h2 class="section-title">What we screened for on this page</h2>
      <div class="section-body">
        <p>Diabetics managing blood sugar with a protein bar usually care about three things above all else:</p>
        <ul class="diab-criteria-list">
          <li><strong>Sugar</strong>: how much sugar it has</li>
          <li><strong>Net carbs</strong>: how many net carbs it delivers once fiber and sugar alcohols are subtracted</li>
          <li><strong>Fiber</strong>: how much fiber it has to slow that carb load down</li>
        </ul>
        <p>We added three more filters on top:</p>
        <ul class="diab-criteria-list">
          <li><strong>Protein</strong>: enough to make it worth eating</li>
          <li><strong>Ingredient grade</strong>: an A or B ingredient quality grade</li>
          <li><strong>No maltitol</strong>: or its close relatives (maltitol syrup, polyglycitol, hydrogenated starch hydrolysates), sugar alcohols that raise blood glucose more than most others and more than labels suggest</li>
        </ul>
        <p>{N} of {comma(NT)} bars, {pct(N, NT)}% of the database, clear all six.</p>
      </div>
      <div class="score-grid" style="margin-top:1.5rem;">
{simple_card_html('Sugar Over 5g', FAIL['sugar'], NT, 'Sugar hits the bloodstream fast. We capped it at 5g, tighter than most "low sugar" marketing claims.')}
{simple_card_html('Net Carbs Over 10g', FAIL['nc'], NT, 'Net carbs (total carbs minus fiber minus sugar alcohols) is the number that actually predicts blood sugar impact, and it is rarely printed on the label.')}
{simple_card_html('Fiber Under 5g', FAIL['fiber'], NT, 'Fiber slows digestion, which flattens the glucose spike from whatever carbs remain. We required at least 5g.')}
{simple_card_html('Contains Maltitol or Similar', FAIL['maltitol'], NT, f'Maltitol and its syrupy relatives (maltitol syrup, polyglycitol, hydrogenated starch hydrolysates) have a glycemic index close to half of table sugar, well above most other sugar alcohols, but labeling rules let brands leave them off the sugar line entirely. {LOWS_M}% of bars with 1g or less listed sugar still contain one of these.')}
</div>
    </div>
'''
LOOK_FOR = '''
    <div class="section-inner">
      <h2 class="section-title">What actually makes a protein bar good for diabetes</h2>
      <div class="section-body">
        <p>Search for the best protein bars for diabetics and most answers start and end with the sugar line on the label. That number matters, but it is not the one that predicts what happens to your blood sugar an hour after eating. Total carbs, fiber, and how much protein and fat come along for the ride matter just as much, and a bar built around whole food ingredients tends to behave differently in your body than one built around syrups and isolates, even at the same sugar gram count.</p>
        <p>Net carbs (total carbs minus fiber minus sugar alcohols) is a better predictor of glucose impact than sugar alone, because it accounts for the carbs a sugar-free label does not have to mention. A bar with 2g of sugar but 22g of net carbs still delivers a real glucose load. Fiber slows how fast that load hits your bloodstream, and protein does the same by slowing gastric emptying. That is why our screen requires 5g or more fiber and 10g or more protein on top of the sugar and net carb caps, not just a low sugar number by itself.</p>
        <p>The maltitol trap covered above is one specific version of a broader pattern: "sugar-free" and "diabetic-friendly" marketing claims describe what a bar's label is allowed to say, not what your blood sugar actually does. The only way to know is to read the full nutrition panel, not the front of the package.</p>
        <div class="callout-box">
          <strong>Four questions worth asking before you buy a bar for blood sugar management:</strong>
          <ul class="diab-criteria-list" style="margin-top:0.5rem;">
            <li><strong>What are the net carbs,</strong> not just the sugar grams on the front of the label?</li>
            <li><strong>How much fiber and protein</strong> does it actually have per serving, and is that enough to slow the carb load down?</li>
            <li><strong>Does it use maltitol, polyglycitol, or hydrogenated starch hydrolysates</strong> instead of sugar, rather than a lower-glycemic sugar alcohol or no sweetener at all?</li>
            <li><strong>Is it a snack or a meal replacement</strong> in your plan, since portion and timing change how any bar affects you?</li>
          </ul>
        </div>
        <p>Diabetes management is individual. Two people can eat the same bar and see different glucose responses depending on medication, activity, and what else they ate that day. Everything on this page is a starting filter built from label data, not a substitute for a conversation with your doctor or a registered dietitian about what fits your treatment plan.</p>
      </div>
    </div>
'''

# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------
SPLIT = brand_split(ALL, QF)
HALF = sum(1 for r in SPLIT[0] + SPLIT[1] + SPLIT[2] if r['q'] and r['q'] >= r['total'] / 2)
C.check(FAIL['nc'] > FAIL['sugar'], 'net carbs catches more bars than sugar')
C.check(AVG_FIB > 7, 'qualifying fiber average is well above 5g')
most_multi = MULTI > SINGLE
INSIGHTS = [
    ('The maltitol trap is real.',
     f'{LOWS_M}% of bars with 1g or less of listed sugar still contain maltitol or a close relative. A bar can say almost no '
     'sugar on the front while quietly delivering a sugar alcohol that still moves blood glucose.'),
    ('Net carbs catches more bars than sugar alone.',
     f"{comma(FAIL['nc'])} bars ({pct(FAIL['nc'], NT)}%) fail on net carbs versus {comma(FAIL['sugar'])} ({pct(FAIL['sugar'], NT)}%) "
     'on sugar. Total carbs and fiber matter as much as the sugar line on the label.'),
    ('Most disqualified bars fail more than one check.' if most_multi else 'Most disqualified bars miss on a single check.',
     f'{comma(MULTI)} of {comma(ND)} disqualified bars fail two or more of the six criteria at once. Only {comma(SINGLE)} miss on a single count.'),
    (f'{BRANDS_Q} brands have at least one qualifying flavor.',
     f'Out of {BRANDS_ALL} tracked brands, {BRANDS_Q} have at least one flavor that clears all six checks. {HALF} brands clear '
     'it on half or more of their lineup.'),
    (f'Qualifying bars average {fnum(round(AVG_FIB, 1))}g of fiber.',
     'That is well above the 5g minimum we required, and reflects how heavily fiber-forward formulas dominate this list.'),
    (f"Only {GR['A']} of {N} qualifying bars earn an A on ingredient quality.",
     f"Meeting the macro thresholds and having a clean ingredient list are two different things. {GR['B']} qualifying bars "
     'land at a B, still solid but built with more processed ingredients.'),
]
C.check(GR['A'] < GR['B'], 'fewer A than B among qualifying bars')
FINDINGS = findings_html(f'What we found screening {comma(NT)} bars for diabetic-friendly criteria', f'{pct(ND, NT)}%',
                         'of bars fail at least one of our six checks',
                         f'{comma(ND)} of {comma(NT)} bars fail on sugar, net carbs, fiber, protein, grade, maltitol, or some '
                         f'combination. {comma(MULTI)} of those fail more than one check at once.', INSIGHTS)

# ---------------------------------------------------------------------------
# Brand tables
# ---------------------------------------------------------------------------
def avg_nc(r): return sum(NC(b) for b in r['bars']) / len(r['bars'])
def g(x): return f'{fnum(round(x, 1))}g'
def uses_sa(r): return any(SA(b) > 0 or has_tag(b, 'Sugar Alcohols') for b in r['bars'])
def pick_of(r):
    band = next(x for x in BAND_ORDER if any(b.get('score_band') == x for b in r['qual']))
    return min((b for b in r['qual'] if b.get('score_band') == band), key=lambda b: (SUG(b), NC(b), name_key(b)))
def main_miss(r):
    s, nc_, f = avg(r['bars'], 'Sugars (g)'), avg_nc(r), avg(r['bars'], 'Dietary Fiber (g)')
    if s > 5:
        return f"Sugar averages {g(s)} per bar, {'well ' if s >= 8 else ''}above our 5g cutoff."
    if nc_ > 10:
        return f'Net carbs average {g(nc_)} per bar, above our 10g cutoff.'
    if f < 5:
        return f'Fiber averages just {g(f)} per bar, below our 5g minimum.'
    return f"It misses mainly on {names_and(SCREEN.misses_mainly(r['disq']))}."
def note(r, kind):
    b = r['brand']
    if kind == 'consider':
        lead = (f"Every tracked {b} flavor clears" if r['d'] == 0 else f"{r['q']} of {r['total']} {b} flavors clear")
        return f"{lead} our full screen. Averages {g(avg(r['bars'], 'Sugars (g)'))} sugar and {g(avg(r['bars'], 'Dietary Fiber (g)'))} fiber per bar."
    if kind == 'mixed':
        return (f"Only {r['q']} of {r['total']} {b} flavors clear our full screen. {pick_of(r)['Flavor Name']} is the clean pick, "
                "so the right flavor matters here.")
    lead = (f"None of {r['total']} tracked {b} flavors clear our screen." if r['q'] == 0 else
            f"Only {r['q']} of {r['total']} tracked {b} flavors clear{'s' if r['q'] == 1 else ''} our screen.")
    return f'{lead} {main_miss(r)}'
BRANDS = macro_brand_tables_html(
    SPLIT, h2='Is your brand good for diabetics?', table_id='diab', table_class='diab-brand-table', note_head='Why',
    intro_html='''        <p>We are not doctors or dietitians, and this is not medical advice. What follows is our own read of the numbers: for every brand we track, we checked what share of its flavors clear the same six-criteria screen used above, then averaged the sugar, net carbs, and fiber across its whole lineup. A brand can average well and still have one bad flavor, or average poorly and still have one good one, so the table below is a starting point for your own label-reading, not a verdict. Click any brand name to jump to its flavors in the table below.</p>
        <p><strong>Consider</strong> means at least 75% of the brand's tracked flavors clear our full screen (allowing at most 2 misses). <strong>Mixed</strong> means some flavors clear it and some do not, so the specific flavor matters. <strong>Avoid</strong> means at least 80% of the brand's tracked flavors miss it and fewer than 3 clear it, usually on sugar, net carbs, or fiber rather than any one thing.</p>''',
    before_tables=f'''
      <div class="guide-jump-row">
        <a href="#bar-list" class="guide-jump-link">Jump straight to all {comma(N)} bars &darr;</a>
      </div>''',
    after_tables='''

      <div class="callout-box">We are not doctors or dietitians. These are the qualities we see people managing diabetes look for, so that is what we filtered on. This page is not medical advice. Talk to your doctor or a registered dietitian about what actually fits your treatment plan.</div>''',
    cols=[('Flavors That Qualify', lambda r: f"{r['q']}/{r['total']}"),
          ('Avg Sugar', lambda r: g(avg(r['bars'], 'Sugars (g)'))),
          ('Avg Net Carbs', lambda r: g(avg_nc(r))),
          ('Avg Fiber', lambda r: g(avg(r['bars'], 'Dietary Fiber (g)'))),
          ('Sugar Alcohol?', lambda r: '<span class="sa-yes">Yes</span>' if uses_sa(r) else '<span class="sa-no">No</span>')],
    notes={'consider': "At least 75% of these brands' tracked flavors clear our full sugar, net carb, fiber, protein, grade, and maltitol screen (allowing at most 2 misses).",
           'mixed': 'Some flavors from these brands clear the screen, some do not. The specific flavor matters more than the brand name.',
           'avoid': "Most or all of these brands' tracked flavors miss our full sugar, net carb, fiber, protein, grade, and maltitol screen."},
    row_note=note)

# ---------------------------------------------------------------------------
# FAQ
# ---------------------------------------------------------------------------
def brand_row(name): return next((r for r in SPLIT[0] + SPLIT[1] + SPLIT[2] if r['brand'] == name), None)
def brand_faq(name):
    r = brand_row(name)
    C.check(r is not None, f'{name} is in bars.js')
    tail = f"averaging {g(avg(r['bars'], 'Sugars (g)'))} sugar and {g(avg_nc(r))} net carbs per bar"
    if r['d'] == 0:
        return (f"By our screen, yes: all {r['total']} tracked {name} flavors clear our sugar, net carb, fiber, protein, grade, "
                f"and maltitol criteria, {tail}.")
    if r['q'] == 0:
        return f"Not by our screen: none of the {r['total']} tracked {name} flavors clear all six criteria. {main_miss(r)}"
    return (f"Mixed by our screen: {r['q']} of {r['total']} tracked {name} flavors clear all six criteria, {tail} across the "
            "lineup. The specific flavor matters more than the brand name here, so check the flavor table above before assuming "
            "the whole lineup qualifies.")
FAQS = [
    ('What should diabetics look for in a protein bar?',
     'We are not doctors, but here is what we filtered on: sugar, net carbs, and fiber, plus enough protein to be worth eating, '
     'an A or B ingredient quality grade, and zero maltitol. Sugar raises blood glucose directly. Net carbs (total carbs minus '
     'fiber minus sugar alcohols) is a better read on glycemic impact than the sugar line alone. Fiber slows digestion and '
     'blunts the spike. We required 5g or less sugar, 10g or less net carbs, and 5g or more fiber for every bar on this list.'),
    ('How do you calculate net carbs?',
     "Net carbs = total carbohydrates minus dietary fiber minus sugar alcohols. We use the values straight off each bar's "
     'nutrition facts panel. Most sugar alcohols have a low enough glycemic impact that this formula treats them fairly. The '
     'exceptions, maltitol and its syrupy relatives, are excluded from this list entirely rather than adjusted for. See the '
     'next question for why.'),
    ('Why do you exclude maltitol instead of adjusting the math for it?',
     'We looked at doing per-molecule math instead of a flat formula, and decided against it. Most sugar alcohols (erythritol, '
     'xylitol, sorbitol, isomalt, lactitol, mannitol) have a glycemic index under 15, close enough to negligible that our '
     'standard net carbs formula already treats them fairly without any adjustment. Maltitol and its syrupy relatives '
     '(maltitol syrup, polyglycitol, hydrogenated starch hydrolysates) sit at a meaningfully higher glycemic index, roughly '
     '35, about half of table sugar. Rather than build a formula with different fractions for eight different molecules, we '
     'exclude bars that use these specific ones. A hard exclude is something we can state with confidence. A per-molecule '
     'formula is not, and we would rather be clear about what we are and are not confident in.'),
    ('What is the maltitol trap in sugar free protein bars?',
     "Maltitol is a sugar alcohol with a glycemic index around 35, well above erythritol's near-zero impact and closer to half "
     'of table sugar. Labeling rules let brands leave sugar alcohols off the sugar line, so a bar can say 0g or 1g sugar while '
     f'still containing maltitol. In our database, {LOWS_M}% of bars with 1g or less listed sugar still contain it or a close '
     'relative. Every bar on this list has been checked and confirmed free of maltitol, maltitol syrup, polyglycitol, and '
     'hydrogenated starch hydrolysates.'),
    ('Why does fiber matter for diabetics choosing a protein bar?',
     'Fiber slows gastric emptying, so glucose reaches the bloodstream more gradually after eating. We required at least 5g '
     f'of fiber for every bar on this list, and qualifying bars average {fnum(round(AVG_FIB, 1))}g.'),
    ('What does the ingredient quality grade mean on this page?',
     "Our A through F grade rates how clean and minimally processed a bar's ingredients are. It is a separate measurement from "
     'diabetic suitability. A bar can score an A on ingredient quality and still be a poor fit for blood sugar management, or '
     'vice versa. We use it as one of the six filters here, requiring an A or B, but the core of the screen is sugar, net '
     'carbs, fiber, protein, and the maltitol exclusion.'),
    ('Are sugar alcohols safe for diabetics?',
     'It depends which one. Erythritol, xylitol, sorbitol, isomalt, lactitol, and mannitol all have a low enough glycemic '
     'impact that they get folded into our standard net carbs calculation. Maltitol and its syrupy relatives raise blood sugar '
     'meaningfully despite being marketed as sugar free, so those are a hard exclude from this list regardless of amount.'),
    ('Is IQ Bar good for diabetics?', brand_faq('IQ Bar')),
    ('Is Quest good for diabetics?', brand_faq('Quest')),
    ('How is the brand table below different from the ranked bar list above?',
     'The ranked list at the top of this page covers individual flavors that pass all six criteria. The brand table further '
     "down rolls that up to the brand level: what share of each brand's tracked flavors qualify, plus average sugar, net carbs, "
     'and fiber across the whole lineup. Use the bar list to find a specific flavor, and the brand table to get a quick read '
     'on a brand before you go looking.'),
    ('How many protein bars in your database qualify for this list?',
     f'Out of {comma(NT)} bars in our database, {N} meet all six criteria: 5g or less sugar, 10g or less net carbs, 5g or more '
     'fiber, 10g or more protein, an A or B ingredient grade, and no maltitol. That is about '
     f'{pct(N, NT)}% of the full database.'),
]

# ---------------------------------------------------------------------------
# Regions
# ---------------------------------------------------------------------------
TITLE = f'Best Protein Bars for Diabetics - {N} Bars Ranked by Ingredient Quality'
H1 = f'Best Protein Bars for Diabetics - We Screened {comma(NT)} Bars, {N} Passed'
DESC = (f'We screened {comma(NT)} bars for sugar, net carbs, fiber, protein, grade, and maltitol. {N} pass. '
        f'{LOWS_M}% of low-sugar bars still hide maltitol.')
REGIONS = [r for r in guide_head_regions(title=TITLE, h1=H1, desc=DESC, og_desc=DESC, url=URL,
                                         about='Diabetes-Friendly Eating Guide', published=PUBLISHED,
                                         faqs=[(q, plain_text(a)) for q, a in FAQS], picks=PICKS)
           if r[0] != 'jsonld-itemlist']
REGIONS += [
    ('hero', f'''<h1 class="hero-title">{esc(H1)}</h1>
    <p class="hero-sub" style="color:#e8e4dc;">Diabetes management is personal, and we are not doctors. Here is what we did instead: we screened every bar in our database against six thresholds people managing blood sugar commonly look for: 5g or less sugar, 10g or less net carbs, 5g or more fiber, 10g or more protein, an A or B ingredient quality grade, and zero maltitol or its high-impact relatives. {N} of {comma(NT)} bars pass all six. See exactly how each bar stacks up, then check the brand table below for a quick read on your favorite brand.</p>'''),
    ('snapshot', f'''
    <div class="snap-item"><div class="snap-value">{comma(N)}</div><div class="snap-label">Bars qualify</div></div>
    <div class="snap-item"><div class="snap-value">{comma(ND)}</div><div class="snap-label">Bars disqualified</div></div>
    <div class="snap-item"><div class="snap-value">{GR['A']}</div><div class="snap-label">A-grade bars</div></div>
    <div class="snap-item"><div class="snap-value">{BRANDS_Q}</div><div class="snap-label">Brands represented</div></div>
    <div class="snap-item"><div class="snap-value">{AVG_FIB:.1f}g</div><div class="snap-label">Avg fiber</div></div>
  '''),
    ('picks', picks_with_extra_html('Top picks for diabetics', PICKS_INTRO, PICKS, PICKS_EXTRA)),
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
<a href="/keto-protein-bars" class="explore-more-card">
  <div class="explore-more-title">Keto Protein Bars</div>
  <div class="explore-more-desc">Low net carb bars ranked by ingredient quality, not just macros.</div>
</a>
<a href="/glp1-protein-bars" class="explore-more-card">
  <div class="explore-more-title">GLP-1 Protein Bars</div>
  <div class="explore-more-desc">15g+ protein, 200 calories or less, low sugar, and 0g sugar alcohol.</div>
</a>
      '''),
    ('faq', faq_items_html(FAQS)),
]
REGIONS += guide_list_regions(Q, ALL, heading=f'{comma(N)} protein bars for diabetics, ranked by ingredient quality')

if __name__ == '__main__':
    n = build_guide_page(PAGE, REGIONS, Q, ALL, C)
    print(f'{PAGE}: {N} qualify, {ND} disqualified, {n} rows, grade-sync 0 mismatches')
    for label, b, why in PICKS:
        print(f'  {label}: {full(b)} ({b["score_band"]})')
