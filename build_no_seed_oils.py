#!/usr/bin/env python3
"""Rebuild no-seed-oils.html from bars.js.

Run from the repo root:  python3 build_no_seed_oils.py

Opens the LIVE page and rewrites only the <!-- kyb:NAME --> regions (nav,
footer, fonts, CSS and JS stay as deployed). Every number, pick, brand row and
bar row comes from bars.js. Copy that depends on a fact is checked; if one
stops being true the build stops and lists it.

Screen: GUIDE_FILTERS['no-seed-oils'] (no 'Processed Oils' concern tag).
Oil cards are counted by ingredient text over the bars the screen flags.
High-oleic sunflower/safflower are permitted. Any qualifying bar whose label
still names a screened oil is printed as a WARNING: a tagging gap in bars.js to
fix upstream, never patched here.
"""
import html as _html
import re
from collections import Counter
from kyb_guide_lib import *

PAGE = 'no-seed-oils.html'
URL = 'https://knowyourbar.com/no-seed-oils'
PUBLISHED = '2026-04-08'

ALL = load_bars()
QF = GUIDE_FILTERS['no-seed-oils']
Q = [b for b in ALL if QF(b)]
D = [b for b in ALL if not QF(b)]
N, ND, NT = len(Q), len(D), len(ALL)
BRANDS_Q = len({b['Brand Name'] for b in Q})
A_Q = sum(1 for b in Q if b.get('score_band') == 'A')
PCT_D, PCT_Q = pct0(ND, NT), pct0(N, NT)
C = Claims()

OILS = {  # card label -> regex (run on the label with high-oleic oils masked)
    'Palm kernel oil': r'palm kernel',
    'Palm oil': r'palm (?:oil|fat)|\bpalm\b(?! kernel| fruit| sugar)',
    'Sunflower oil': r'sunflower (?:seed )?oil',
    'Vegetable oil': r'vegetable (?:oil|fat)',
    'Soybean oil': r'soybean oil|soy oil',
    'Canola oil': r'canola oil|oils? \([^)]*canola',
    'Palm fruit oil': r'palm fruit',
    'Safflower oil': r'safflower',
    'Rapeseed oil': r'rapeseed',
    'Cottonseed oil': r'cottonseed',
    'Rice bran oil': r'rice bran oil',
    'Corn oil': r'corn oil',
    'Grapeseed oil': r'grape ?seed oil',
}
HYDRO = r'hydrogenated'
def masked(b): return re.sub(r'high[- ]oleic (sunflower|safflower)', r'HOSO', ingr(b), flags=re.I)
def has_oil(b, label): return bool(re.search(OILS[label], masked(b), re.I))
def any_oil(b): return any(has_oil(b, l) for l in OILS) or bool(re.search(HYDRO, ingr(b), re.I))
HIT = {l: [b for b in D if has_oil(b, l)] for l in OILS}
ORDER = [l for l in sorted(OILS, key=lambda l: (-len(HIT[l]), l)) if HIT[l]]
TOP, SECOND, THIRD = ORDER[0], ORDER[1], ORDER[2]

for b in Q:
    if any_oil(b):
        print(f'WARNING: {full(b)} names a screened oil on its label but has no Processed Oils tag in bars.js '
              f'({", ".join(l for l in OILS if has_oil(b, l)) or "hydrogenated"}). Fix upstream in scoring; the page follows bars.js.')
C.check(all(any_oil(b) for b in D), 'every flagged bar names a screened oil')

def link(href, text): return f'<a href="{href}">{text}</a>'
def by_brand(brand, bars=ALL): return [b for b in bars if b['Brand Name'] == brand]
def oil_counts(bars):
    c = Counter(l for b in bars for l in OILS if has_oil(b, l))
    return sorted(c.items(), key=lambda kv: (-kv[1], ORDER.index(kv[0]) if kv[0] in ORDER else 99))
def lc(label): return label[0].lower() + label[1:]

# ---------------------------------------------------------------------------
# Top picks
# ---------------------------------------------------------------------------
PK = Picker(Q)
G = PK.band_grade
CALK = lambda b: num(b.get('Calories')) or 9999
def scope(fn, b, higher=True):
    best = (max if higher else min)
    if fn(b) == best(fn(x) for x in Q):
        return 'of any bar with no seed oils'
    if fn(b) == best(fn(x) for x in PK.band):
        return f'of any {G}-grade bar with no seed oils'
    return f'of any {G}-grade bar with {PK.floor}g+ protein and no seed oils'
def tied(fn, b):
    return sum(1 for x in PK.band if P(x) >= PK.floor and fn(x) == fn(b)) > 1
def no_added_oil(b): return not re.search(r'\boils?\b|\bfat\b|shortening|\bmct\b|margarine', ingr(b), re.I)
NI = lambda b: top_level_ingredient_count(ingr(b))

best = PK.balanced()
top_p = PK.pick(lambda b: (-P(b), CALK(b)))
top_r = PK.pick(lambda b: (-(p100(b) or 0), -P(b)))
low_s = PK.pick(lambda b: (SUG(b), -P(b)))
top_f = PK.pick(lambda b: (-FIB(b), -P(b)))
no_oil = PK.pick(lambda b: (NI(b), -P(b)), no_added_oil)
PICKS = [
    ['Best overall', best,
     f"{fnum(P(best))}g protein, {fnum(FIB(best))}g fiber, and just {fnum(SUG(best))}g sugar with no seed oil on the label. "
     "Solid across the board rather than an extreme on one metric."],
    ['Highest protein', top_p, f"{fnum(P(top_p))}g protein, the most {scope(P, top_p)}."],
    ['Best protein per calorie', top_r,
     f"{fnum(P(top_r))}g protein at just {fnum(CAL(top_r))} calories, {fnum(p100(top_r))}g protein per 100 calories, "
     f"the best ratio {scope(lambda b: p100(b) or 0, top_r)}."],
    ['Lowest sugar', low_s,
     f"{fnum(SUG(low_s))}g of sugar, {'tied for ' if tied(SUG, low_s) else ''}the lowest {scope(SUG, low_s, False)}, "
     f"alongside {fnum(P(low_s))}g of protein and {fnum(FIB(low_s))}g of fiber."],
    ['Most fiber', top_f,
     f"{fnum(FIB(top_f))}g of fiber, {'tied for ' if tied(FIB, top_f) else ''}the most {scope(FIB, top_f)}, "
     f"alongside {fnum(P(top_f))}g of protein."],
    ['No added oil at all', no_oil,
     "No oil of any kind anywhere on the label. Not just free of seed oil, free of any added oil, seed or otherwise."],
]
C.check(all(p[1] for p in PICKS), 'six distinct top picks available')
C.check(P(best) >= 15 and FIB(best) >= 5 and SUG(best) <= 5, 'best overall meets the balanced bar')
add_sugar_tradeoff(PICKS)
if P(no_oil) < 10:
    PICKS[5][2] += f" The tradeoff is protein: just {fnum(P(no_oil))}g, closer to a whole-food snack than a protein bar."
PICKS_INTRO = ("Everyone has their own reason for wanting a protein bar, but if you're on this page, you already know you want "
               "one without seed oils. Here are the best bars for what people typically look for, all without seed oils. "
               "Grades below reflect ingredient quality only, not an overall bar rating.")

# ---------------------------------------------------------------------------
# What it means: one card per oil that shows up
# ---------------------------------------------------------------------------
OIL_DESC = {
    'Palm kernel oil': 'Common in chocolate coatings and crisp layers, prized for a solid melt-in-your-mouth snap.',
    'Palm oil': 'Used for shelf-stable texture and moisture retention in the base recipe.',
    'Sunflower oil': 'A cheap binding fat in protein crisps or coatings, unless labeled high-oleic.',
    'Vegetable oil': 'A generic catch-all fat, usually a blend of soy, corn, or canola.',
    'Soybean oil': 'A cheap, high-omega-6 fat common in coatings and fillings.',
    'Canola oil': 'A moisture retainer that hides mid-list in crispy layers or fillings.',
    'Palm fruit oil': 'A less-refined form of palm oil, same shelf-stability role.',
    'Safflower oil': 'Occasional coating or moisture ingredient, unless high-oleic.',
    'Rapeseed oil': "Canola's parent crop, occasionally listed under this name directly.",
    'Cottonseed oil': 'Usually part of a generic vegetable oil blend rather than listed on its own.',
    'Rice bran oil': 'Rare, usually a specialty coating fat.',
    'Corn oil': 'Rare in bars, usually part of a vegetable oil blend.',
    'Grapeseed oil': 'Rare in bars, occasionally used in baked-style formats.',
}
def card(label, bars_hit, total, desc):
    n = len(bars_hit)
    return f'''<div class="score-card">
          <div class="score-card-label">{esc(label)}</div>
          <div class="score-card-val">{n} bar{"" if n == 1 else "s"}<span class="oil-card-pct">{esc(pct0(n, total))}%</span></div>
          <div class="score-card-desc">{esc(desc)}</div>
          {found_in_html(bars_hit)}
        </div>'''
MEANS = f'''
    <div class="section-inner">
      <h2 class="section-title">What "no seed oils" actually means</h2>
      <div class="section-body">
        <p>Seed and vegetable oils are some of the most common additives in processed food, and protein bars are no exception. This guide screens every bar for thirteen of them: canola, rapeseed, soybean, palm, palm kernel, palm fruit, sunflower, safflower, cottonseed, corn, grapeseed, and rice bran oil, plus any bar listing generic "vegetable oil" or "hydrogenated"/"partially hydrogenated" fat. High-oleic sunflower and safflower oil are permitted, since their fatty acid profile runs closer to olive oil than to the standard refined version of the same seed.</p>
        <p>{PCT_D}% of the {comma(NT)} bars in our database still have a seed oil on the label. Here is how often each one shows up, and where it usually hides.</p>
      </div>

      <div class="score-grid" style="margin-top:1.5rem;">
{chr(10).join(card(l, HIT[l], NT, OIL_DESC[l]) for l in ORDER)}
      </div>
    </div>
'''

# ---------------------------------------------------------------------------
# Do Pure Protein, Perfect Bar, Built Bar, and IQBAR use seed oils?
# ---------------------------------------------------------------------------
BRAND4 = [('Pure Protein', 'Pure Protein'), ('Perfect Bar', 'Perfect Bar'), ('Built', 'Built Bar'), ('IQ Bar', 'IQBAR')]
C.check(all(by_brand(k) for k, _ in BRAND4), 'Pure Protein, Perfect Bar, Built and IQ Bar are all in bars.js')
def brand4(key, name):
    bs = by_brand(key)
    oily = [b for b in bs if not QF(b)]
    oc = oil_counts(oily)
    return dict(key=key, name=name, bars=bs, t=len(bs), d=len(oily), q=len(bs) - len(oily), oc=oc)
B4 = [brand4(k, n) for k, n in BRAND4]
def b4_cell(r):
    if r['q']:
        return f'<button type="button" class="brand-jump" data-brand="{esc(r["key"])}">{esc(r["name"])}</button>'
    return f'<span class="brand-name-static">{esc(r["name"])}</span>'
def b4_para(r):
    if r['d'] == 0:
        return (f"None of the {r['t']} flavors use canola oil, sunflower oil, or any other seed or vegetable oil. The fat comes "
                "from nuts, seeds, and nut butters used as whole-food ingredients, not an added refined oil.")
    (top, n), rest = r['oc'][0], r['oc'][1:]
    s = f"{n} of {r['t']} flavors list {lc(top)}"
    if rest:
        s += (f", and {num_word(len(rest))} other oil{'s' if len(rest) > 1 else ''} also show{'' if len(rest) > 1 else 's'} up on "
              f"some flavors: " + ', '.join(f'{lc(l)} ({c})' for l, c in rest))
    s += '. No flavor clears this guide.' if r['q'] == 0 else f". {r['q']} of {r['t']} flavors do clear it."
    return s
every = [r['name'] for r in B4 if r['d'] == r['t']]
none = [r['name'] for r in B4 if r['d'] == 0]
some = [r for r in B4 if 0 < r['d'] < r['t']]
intro = []
if every:
    intro.append(f"{names_and(every)} use{'s' if len(every) == 1 else ''} a seed or vegetable oil in every flavor we checked.")
if none:
    intro.append(f"{names_and(none)} use{'s' if len(none) == 1 else ''} none.")
for r in some:
    intro.append(f"{r['name']} uses one in {r['d']} of {r['t']} flavors.")
b4_rows = '\n'.join(
    f"<tr><td>{b4_cell(r)}</td><td>{r['t']}</td><td>{r['d']}/{r['t']}</td>"
    f"<td>{esc(', '.join(f'{l} ({c})' for l, c in r['oc']) or 'None')}</td>"
    f"<td>{grade_range_html(*grade_range(r['bars']))}</td></tr>" for r in B4)
BRAND4_HTML = f'''
    <div class="section-inner">
      <h2 class="section-title">Do Pure Protein, Perfect Bar, Built Bar, and IQBAR use seed oils?</h2>
      <div class="section-body">
        <p>{esc(' '.join(intro))} Here is exactly which oils each brand lists, pulled straight from the ingredient label of every flavor in our database.</p>
      </div>

      <div class="table-scroll">
        <table class="brand-table">
          <thead><tr><th>Brand</th><th>Flavors Checked</th><th>Use a Seed Oil</th><th>Oils Found</th><th>Ingredient Quality</th></tr></thead>
          <tbody>
{b4_rows}
          </tbody>
        </table>
      </div>

      <div class="section-body" style="margin-top:1.5rem;">
{chr(10).join(f'        <p><strong>{esc(r["name"])}:</strong> {esc(b4_para(r))}</p>' for r in B4)}
      </div>
    </div>
'''

# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------
TOPB = HIT[TOP]
def tucked(b, rx):
    t = masked(b)
    m = re.search(r'\d\s*%\s*or\s*less|less than\s*\d\s*%', t, re.I)
    h = re.search(rx, t, re.I)
    return bool(m and h) and h.start() > m.start()
TUCK = [b for b in TOPB if tucked(b, OILS[TOP])]
COAT = re.compile(r'coating|chocolate|compound|crisp|drizzle|layer|icing|confection|chips?\b', re.I)
def in_coating(b):
    return any(re.search(OILS[TOP], it, re.I) and COAT.search(it) for it in top_level_items(masked(b)))
coat_share = sum(1 for b in TOPB if in_coating(b)) / len(TOPB)
BB = by_brand('Barebells'); BB_D = [b for b in BB if not QF(b)]
C.check(len(BB_D) / len(BB) >= 0.8, 'Barebells fails the seed oil screen in 80%+ of flavors')
bb_head = 'Barebells disqualifies entirely.' if len(BB_D) == len(BB) else 'Barebells disqualifies almost entirely.'
WHOLE = ['RXBAR', 'Larabar', 'Thunderbird', 'Off the Farm', 'Healthy Eating on the Go']
C.check(all(by_brand(w) and len(by_brand(w, Q)) / len(by_brand(w)) >= 0.85 for w in WHOLE), 'whole-food brands qualify at 85%+')

CONSIDER, MIXED, AVOID = brand_split(ALL, QF)
BIG_MIX = MIXED[0]  # most flavors
SPLIT_EX = min(MIXED, key=lambda r: (abs(r['q'] / r['total'] - 0.5), -r['total'], r['brand']))
def clean_pick(r):
    band = next(g for g in BAND_ORDER if any(b.get('score_band') == g for b in r['qual']))
    return min((b for b in r['qual'] if b.get('score_band') == band), key=lambda b: (-P(b), name_key(b)))

INSIGHTS = [
    (f'{TOP} is the single most common offender.',
     f'{len(TOPB)} bars ({g1(100 * len(TOPB) / NT)}% of the database) list it'
     + (', most often in a coating or crisp layer.' if coat_share >= 0.5 else '.')),
    (f'Only {g1(100 * len(TUCK) / len(TOPB))}% list it as a trace amount.',
     f'Just {len(TUCK)} of the {len(TOPB)} bars containing {lc(TOP)} list it inside a "contains 2% or less" clause. In the '
     'rest, it\'s a real component of the recipe, not a rounding error.'),
    (bb_head, f'{len(BB_D)} of {len(BB)} flavors fail.'),
    ('Whole-food bars dominate the qualifying pool.',
     f'{names_and(WHOLE)} all qualify at or near 100%. Their fat comes from nuts, seeds, dates, or coconut rather than a refined oil.'),
    ('A mixed lineup is common, not rare.',
     f"{len(MIXED)} brands we checked split meaningfully between qualifying and disqualified flavors within the same lineup. "
     f"{BIG_MIX['brand']} is the biggest example: {BIG_MIX['q']} of {BIG_MIX['total']} flavors qualify."),
    (f'{BRANDS_Q} brands still represented.',
     f'Even with {PCT_D}% of the database disqualified, the qualifying pool covers a wide range of protein levels, price '
     'points, and grades.'),
]
C.check(len(TUCK) / len(TOPB) < 0.05, f'under 5% of {TOP} bars list it as a trace amount')
FINDINGS = findings_html(
    f'What we found screening {comma(NT)} bars', f'{PCT_D}%', 'of bars contain a seed or vegetable oil',
    f'{ND} of {comma(NT)} bars contain at least one of the oils we screen for. {TOP} is the most common, ahead of '
    f'{lc(SECOND)} and {lc(THIRD)}. It shows up in coatings, crisp layers, and as a base fat across brands.', INSIGHTS)

# ---------------------------------------------------------------------------
# Brand tables
# ---------------------------------------------------------------------------
def oils_found(r):
    oc = [l for l, _ in oil_counts(r['disq'])]
    oc = oc[:1] + [lc(l) for l in oc[1:]]
    if len(oc) <= 3:
        return names_and(oc)
    return f"{oc[0]}, {lc(oc[1])}, and {len(oc) - 2} others"
BRANDS = brand_tables_html(
    (CONSIDER, MIXED, AVOID), QF,
    h2='Best Brands of Protein Bars for No Seed Oils',
    intro='Seed oils turn up in brands you would not expect, and stay out of a few you might not guess either. Grade columns '
          'below show ingredient quality only, not an overall bar rating. Click any brand name to jump to its flavors in '
          'the table below.',
    table_id='nso',
    consider_note='These brands clear our seed oil screen almost or entirely across the board.',
    avoid_note='These brands lean on seed oils across most or all of their lineup.',
    mixed_note="Some flavors qualify, some don't. Check the specific flavor before buying.",
    avoid_head='Flavors with Seed Oils', avoid_last_head='Oils Found', avoid_last=oils_found,
    mixed_head='Flavors without Seed Oils')

# ---------------------------------------------------------------------------
# FAQ
# ---------------------------------------------------------------------------
RX = by_brand('RXBAR'); RX_Q = by_brand('RXBAR', Q)
RX_HO = [b for b in RX if re.search(r'high[- ]oleic', ingr(b), re.I)]
LARA = by_brand('Larabar'); LARA_Q = by_brand('Larabar', Q)
lara_med = sorted(NI(b) for b in LARA)[len(LARA) // 2]
KIND = next(r for r in CONSIDER + MIXED + AVOID if r['brand'] == 'KIND')
kind_oils = [lc(l) for l, _ in oil_counts(KIND['disq'])[:2]]
COCO_Q = [b for b in Q if re.search(r'coconut oil|coconut butter', ingr(b), re.I)]
C.check(len(COCO_Q) > 0, 'some qualifying bars use coconut oil or coconut butter')
C.check(len(RX_Q) == len(RX), 'every RXBAR flavor qualifies')
C.check(LARA_Q and len(LARA_Q) < len(LARA), 'Larabar: most but not all flavors qualify')
C.check(KIND['q'] < KIND['d'], 'KIND: only some flavors qualify')
FAQ_WHOLE = ['RXBAR', 'Healthy Eating on the Go', 'Thunderbird']
C.check(all(len(by_brand(w, Q)) == len(by_brand(w)) for w in FAQ_WHOLE), 'RXBAR, Healthy Eating on the Go and Thunderbird qualify 100%')
AV3 = [r['brand'] for r in AVOID[:3]]
b4 = {r['name']: r for r in B4}
def b4_q(name, oils):
    return f"Does {name} have {oils}?"
FAQS = [
    ('What counts as a seed oil in this guide?',
     'We screen for canola oil, rapeseed oil, soybean oil, palm oil, palm kernel oil, palm fruit oil, sunflower oil, safflower '
     'oil, cottonseed oil, corn oil, grapeseed oil, rice bran oil, and generic vegetable oil. High-oleic sunflower and '
     'safflower oil are permitted because their fatty acid profile is different from the standard refined versions.'),
    ('Do RXBAR bars have seed oils?',
     f"No. All {len(RX)} RXBAR flavors qualify. RXBAR is built on egg whites, dates, and nuts, so most of the fat comes from "
     "whole-food sources"
     + (f". {num_word(len(RX_HO)).capitalize()} flavors add avocado or high-oleic sunflower oil, which this guide permits." if RX_HO
        else " with nothing refined added.")),
    ('Does Larabar have seed oils?',
     f"Most, but not all. {len(LARA_Q)} of {len(LARA)} Larabar flavors qualify. A typical Larabar runs about {lara_med} "
     "ingredients, usually dates plus a nut or two, so there is little room for a seed oil to hide, but a few flavors do use one."),
    ('Do KIND bars have seed oils?',
     f"Some do. {KIND['q']} of {KIND['total']} KIND flavors qualify, including {clean_pick(KIND)['Flavor Name']}. The rest "
     f"mostly use {' or '.join(kind_oils)}, so check the specific flavor rather than assuming the whole line is clean."),
    (b4_q('Pure Protein', 'canola oil or sunflower oil'), b4_para(b4['Pure Protein'])),
    (b4_q('Perfect Bar', 'sunflower oil or canola oil'), b4_para(b4['Perfect Bar'])),
    (b4_q('Built Bar', 'palm kernel oil or sunflower oil'), b4_para(b4['Built Bar'])),
    (b4_q('IQBAR', 'sunflower oil or canola oil'), b4_para(b4['IQBAR'])),
    ('Which protein bars are most likely to contain palm or canola oil?',
     f"{TOP} is the single most frequent culprit across the database, in {len(TOPB)} bars, ahead of {lc(SECOND)} "
     f"({len(HIT[SECOND])}) and {lc(THIRD)} ({len(HIT[THIRD])})."
     + (' It is a go-to fat for chocolate-style coatings and crisp layers, and it often shows up as "palm kernel oil" rather '
        'than plain "palm oil," so it is easy to miss on a quick label scan.' if TOP == 'Palm kernel oil' else '')),
    ('Is coconut oil a seed oil?',
     'No. Coconut oil is not screened out by this guide. It comes from coconut flesh, not a seed, and has a different fatty '
     'acid makeup than the oils on our exclusion list. Bars using coconut oil or coconut butter qualify here.'),
    ('What about high-oleic sunflower or safflower oil?',
     'High-oleic sunflower and safflower oils are permitted. They are bred for a high monounsaturated fat content, closer in '
     'profile to olive oil than to the standard refined version of the same seed. They are not treated as the same '
     'ingredient for this screen.'),
    ('Can a brand have some flavors with seed oils and some without?',
     f"Yes, and it is more common than you would expect. {SPLIT_EX['brand']} splits close to the middle: {SPLIT_EX['q']} of "
     f"{SPLIT_EX['total']} flavors qualify, often because some flavors add a coating or crisp layer with a different fat "
     "source than the rest of the line. Always check the specific flavor, not just the brand."),
    ('How often is this list updated?',
     'We update the database whenever new bars are added or a brand reformulates. Manufacturers do change their ingredient '
     f'lists over time, so always confirm against the packaging in front of you. This page reflects the database as of {today_iso()}.'),
    ("What protein bars don't have seed oils?",
     f"{comma(N)} bars across {BRANDS_Q} brands clear our seed oil screen, led by whole-food brands like "
     f"{names_and(FAQ_WHOLE)} that qualify 100% of the time. The full ranked list is in the table below, sorted by ingredient quality."),
    ('What protein bars have seed oils?',
     f"{ND} of the {comma(NT)} bars we track contain at least one seed or vegetable oil. {names_and(AV3)} disqualify almost "
     f"entirely, usually through {lc(TOP)}, {lc(SECOND)}, or {lc(THIRD)}."),
    ('Why does canola oil count as a seed oil to avoid here?',
     'Canola comes from rapeseed, which is a seed. We group it with the other refined seed and vegetable oils on this list '
     'for the same reason: a highly processed extraction method and a fatty acid profile heavier in omega-6 than whole-food '
     'fat sources like nuts, seeds, or dairy.'),
]
C.check(all(r['d'] / r['total'] >= 0.8 for r in AVOID[:3]), 'top three avoid brands disqualify 80%+')

def plain(s): return _html.unescape(re.sub(r'<[^>]+>', '', s))
def faq_block(faqs):
    return ''.join(f'''
        <div class="faq-item">
          <button class="faq-q">{esc(q)}</button>
          <div class="faq-a">{esc(a)}</div>
        </div>''' for q, a in faqs) + '\n      '

# ---------------------------------------------------------------------------
# Regions
# ---------------------------------------------------------------------------
TITLE = f"{PCT_D}% of Protein Bars Have Seed Oils. {comma(N)} Don't."
H1 = f'Best Protein Bars Without Seed Oils - Ranking {comma(N)} Bars by Ingredient Quality'
OG_DESC = (f'{comma(N)} protein bars with no seed or vegetable oils. No canola, soybean, palm, or sunflower oil. Ranked by '
           'ingredient quality score.')
REGIONS = [r for r in guide_head_regions(
    title=TITLE, h1=H1,
    desc=f'We screened {comma(NT)} protein bars for seed oils. {PCT_Q}% have none. See the {comma(N)} best, ranked by ingredient quality, brand, and macros.',
    og_desc=OG_DESC, url=URL, about='Seed Oils', published=PUBLISHED, faqs=FAQS, picks=PICKS) if r[0] != 'social']
REGIONS += [
    ('social', f'''<meta property="og:type" content="article">
  <meta property="og:site_name" content="Know Your Bar">
  <meta property="og:title" content="{esc(TITLE)}">
  <meta property="og:description" content="{esc(OG_DESC)}">
  <meta property="og:url" content="{URL}">
  <meta property="og:image" content="https://knowyourbar.com/bar_hero.png">

  <!-- Twitter card -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(TITLE)}">
  <meta name="twitter:description" content="{esc(OG_DESC)}">
  <meta name="twitter:image" content="https://knowyourbar.com/bar_hero.png">'''),
    ('hero', f'''<h1 class="hero-title">{esc(H1)}</h1>
    <p class="hero-sub" style="color:#e8e4dc;">We screened {comma(NT)} protein bars available in the US for seed oils like canola, soybean, palm, sunflower, safflower, and several other seed and vegetable oils. The good news: {PCT_Q}% of protein bars do NOT have a seed oil on their ingredient label. We break down and rank the best protein bars without seed oils by category, brand, and macros. Not just us telling you the flavors we like.</p>'''),
    ('snapshot', f'''
    <div class="snap-item"><div class="snap-value">{comma(N)}</div><div class="snap-label">Bars qualify</div></div>
    <div class="snap-item"><div class="snap-value">{ND}</div><div class="snap-label">Bars disqualified</div></div>
    <div class="snap-item"><div class="snap-value">{A_Q}</div><div class="snap-label">A-grade bars</div></div>
    <div class="snap-item"><div class="snap-value">{BRANDS_Q}</div><div class="snap-label">Brands represented</div></div>
    <div class="snap-item"><div class="snap-value">{avg(Q, 'Protein (g)'):.1f}g</div><div class="snap-label">Avg protein</div></div>
  '''),
    ('picks', picks_section_html('Top picks for no seed oils', PICKS_INTRO, PICKS)),
    ('means', MEANS),
    ('do-pure-protein-perfect-bar-built-bar-an', BRAND4_HTML),
    ('findings', FINDINGS),
    ('brands', BRANDS),
    ('cta-heading', f'<h2 class="explore-cta-main-heading">See every bar that fits, not just the {comma(N)} on this page</h2>'),
    ('explore-more', f'''
        <a href="/clean-protein-bars" class="explore-more-card">
          <div class="explore-more-title">Clean Protein Bars</div>
          <div class="explore-more-desc">A or B grade bars with no artificial sweeteners and no processed oils.</div>
        </a>
        <a href="/no-artificial-sweeteners" class="explore-more-card">
          <div class="explore-more-title">No Artificial Sweeteners</div>
          <div class="explore-more-desc">Bars with zero sucralose, aspartame, or acesulfame potassium, ranked by ingredient quality.</div>
        </a>
        <a href="/rxbar-review" class="explore-more-card">
          <div class="explore-more-title">RXBAR Review</div>
          <div class="explore-more-desc">All {len(RX)} RXBAR flavors scored. No seed oils, no artificial sweeteners, short ingredient lists.</div>
        </a>
      '''),
    ('faq', faq_block(FAQS)),
]
C.check(not any(has_tag(b, 'Artificial Sweeteners') for b in RX), 'RXBAR has no artificial sweeteners')
REGIONS += guide_list_regions(Q, ALL, heading=f'{comma(N)} bars with no seed oils, ranked by ingredient quality', lazy_attr=True)

if __name__ == '__main__':
    n = build_guide_page(PAGE, REGIONS, Q, ALL, C)
    print(f'{PAGE}: {N} qualify, {ND} disqualified, {n} rows, grade-sync 0 mismatches')
    for label, b, why in PICKS:
        print(f'  {label}: {full(b)} ({b["score_band"]})')
