#!/usr/bin/env python3
"""Rebuild soy-free-protein-bars.html from bars.js. GUIDE PAGE v2 ("Best 10").

Run from the repo root:  python3 build_soy_free_protein_bars.py

Layout and every rule: claude/GUIDE_PAGE_SPEC_V2.md (locked 2026-09-29) and
the v2 section of kyb_guide_lib.py, built the same way as the other v2 guides
(closest reference: build_dairy_free_protein_bars.py, a certification guide).
The first run migrated the live v1 page (built by kyb_cert_guide.CertGuide) to
the v2 body (head, nav and footer kept as deployed); later runs rewrite only the
<!-- kyb:NAME --> regions. Every number, pick and brand row comes from bars.js.
Copy that depends on a fact is checked; if one stops being true the build stops
and lists it. Ingredient quality is shown and ranked as a GRADE only.

Screen: GUIDE_FILTERS['soy-free-protein-bars'] = `Soy Free (Y/N)` is Yes (the
brand's label). The three named soy sources use the GUIDE_CRITERIA.md patterns.
Per that doc, soy protein and soy lecithin are NOT concern ingredients in our
scoring, so the grade gap is described as correlation (artificial sweeteners /
processed oils), never as a soy penalty.
Bar Finder: /bar-finder?certs=Soy%20Free (checked key for key below).

Guide slots (picked 2026-09-30; Jeff asked for the best picks delivered without
an approval round): Best dairy-free, Best gluten-free, Best plant-based, Best
non-GMO. Fallbacks: Best whey protein, then Highest fiber. Soy-free shoppers are
mostly allergy shoppers, so the other big allergen labels come first; lowest
sugar / net carbs / fiber would repeat bars already on 3-4 guides.
"""
import re
from collections import Counter
from kyb_guide_lib import *

PAGE = 'soy-free-protein-bars.html'
URL = 'https://knowyourbar.com/soy-free-protein-bars'
PUBLISHED = '2026-09-17'
set_tie_seed('soy-free-protein-bars')   # per-guide shuffle for exact ties (kyb_guide_lib, 2026-09-30)

ALL = load_bars()
QF = GUIDE_FILTERS['soy-free-protein-bars']
Q = [b for b in ALL if QF(b)]
D = [b for b in ALL if not QF(b)]
N, ND, NT = len(Q), len(D), len(ALL)
BRANDS_Q = len({b['Brand Name'] for b in Q})
GR = {g: sum(1 for b in Q if b.get('score_band') == g) for g in BAND_ORDER}
C = Claims()
C.check(not any(b.get('Soy Free (Y/N)') not in ('Yes', None) for b in ALL), 'Soy Free field is only Yes or blank')

SOURCES = [  # label, regex (GUIDE_CRITERIA.md), card description
    ('Soy lecithin', r'soy lecithin|lecithins?\s*\(soy\)',
     'An emulsifier that keeps the bar from separating, usually low in the ingredient list. Imported and European-formatted '
     'bars often reverse the label to "lecithin (soy)".'),
    ('Soy protein', r'soy protein|textured soy|soy flour|isolated soy protein|proteins?\s*\(soy\b|\(soy,',
     'Soy protein isolate, concentrate or flour, often to boost the protein count, sometimes inside a multi-source "plant '
     'protein" blend.'),
    ('Soybean oil', r'soybean oil|soy oil',
     'Used as a coating fat or moisture binder, most often in chocolate or peanut-butter-style coatings.'),
]
RX = {l: r for l, r, _ in SOURCES}
DESC_S = {l: d for l, _, d in SOURCES}
def label_text(b):
    return re.split(r'may contain|manufactured (?:in|on)|processed (?:in|on)|produced (?:in|on)|made in a facility|in a facility', ingr(b), flags=re.I)[0]
def has_s(b, l): return bool(re.search(RX[l], label_text(b), re.I))
def any_s(b): return any(has_s(b, l) for l in RX)
HIT = {l: [b for b in D if has_s(b, l)] for l in RX}
ORDER = sorted(RX, key=lambda l: -len(HIT[l]))
NAMED = [b for b in D if any_s(b)]
UNLAB = [b for b in D if not any_s(b)]
for b in Q:
    if any_s(b) and not reviewed_ok(b, 'soy free'):
        print(f'WARNING: {full(b)} is labeled soy free in bars.js but its ingredients name '
              f'{", ".join(l.lower() for l in RX if has_s(b, l))}. Check the label; the page follows bars.js.')
C.check(ORDER[0] == 'Soy lecithin', 'soy lecithin is the most common named soy source')

# Bar Finder parity: ?certs=Soy%20Free (app.js CERT_MAP 'Soy Free' -> 'Soy Free (Y/N)')
C.check({b['Key'] for b in ALL if (b.get('Soy Free (Y/N)') or '').strip().lower() == 'yes'} == {b['Key'] for b in Q},
        'Bar Finder certs=Soy Free returns exactly the guide set')
FINDER_HREF = '/bar-finder?certs=Soy%20Free'

def yes(field): return lambda b: b.get(field) == 'Yes'
def by_brand(brand, bars=ALL): return [b for b in bars if b['Brand Name'] == brand]
def ab(bars): return pct0(sum(1 for b in bars if b.get('score_band') in ('A', 'B')), len(bars))
def rate(bars, tag): return pct0(sum(1 for b in bars if has_tag(b, tag)), len(bars))

# ---------------------------------------------------------------------------
# Best 10 (spec v2)
# ---------------------------------------------------------------------------
WHEY_RX = re.compile(r'\bwhey\b[^,;()\[\]]*', re.I)
def whey(b): return bool(WHEY_RX.search(ingr(b)))
def whey_name(b): return WHEY_RX.search(ingr(b)).group(0).strip().lower()
SLOTS = [
    slot_best_overall(15),
    slot_cleanest(),
    slot_highest_protein(300),
    slot_protein_per_cal(12),
    slot_lowest_calorie(),
    slot_big_brand(),
    slot_subset('Best dairy-free', 'Labeled dairy free by the brand.', yes('Dairy Free (Y/N)'),
                lambda b: 'Labeled soy free and dairy free, the two allergens most protein bars lean on.'),
    slot_subset('Best gluten-free', 'Labeled gluten free by the brand.', yes('Gluten Free (Y/N)'),
                lambda b: 'Labeled soy free and gluten free, for anyone avoiding both.'),
    slot_subset('Best plant-based', 'Labeled vegan by the brand.', yes('Vegan (Y/N)'),
                lambda b: 'Labeled vegan, so the protein comes from plants other than soy.', floor=15),
    slot_subset('Best non-GMO', 'Labeled Non-GMO by the brand.', yes('Non-GMO (Y/N)'),
                lambda b: 'Labeled soy free and Non-GMO.'),
]
FALLBACKS = [
    slot_subset('Best whey protein', 'Whey protein on the label.', whey,
                lambda b: f"Built on {whey_name(b)}, a complete dairy protein and one of the protein sources our scoring rates highly."),
    slot_highest_fiber(),
]
PICKS = pick_best10(Q, SLOTS, FALLBACKS)
C.check(len(PICKS) == 10, 'ten Best 10 picks available')
C.check([s.label for s, *_ in PICKS] == [s.label for s in SLOTS], 'all ten planned slots filled without fallbacks')
C.check(not any(re.search(r'score \d|scored? \d', w) for _s, _b, w, _n in PICKS), 'no ingredient score printed in a pick')
PK = {s.label: b for s, b, _w, _n in PICKS}
C.check(not any(any_s(b) or re.search(r'\bsoy', ingr(b), re.I) for _s, b, _w, _n in PICKS), 'no Best 10 pick names any soy ingredient')
B10_INTRO = ("Ten soy free bars, each the winner of one thing people shop for. Every pick is labeled soy free, has an A or B "
             "ingredient grade and at least 10g of protein, and no bar appears twice.")

# ---------------------------------------------------------------------------
# What disqualifies a bar (carried over from v1, trimmed)
# ---------------------------------------------------------------------------
DISQ = f'''
    <div class="section-inner">
      <h2 class="section-title">What disqualifies a protein bar from being soy free</h2>
      <div class="section-body">
        <p>We check the Soy Free (Y/N) label on file for every bar, then cross-check ingredient lists ourselves for soy lecithin, soy protein and soybean oil, the three named soy sources that show up most in the data. {of_db(N, NT)} bars, about {pct0(N, NT)}%, carry a soy free label. The other {comma(ND)}, about {pct0(ND, NT)}%, don't.</p>
        <p>{comma(len(NAMED))} of those {comma(ND)} name at least one of the three. Soy lecithin leads, because it's a cheap emulsifier that shows up even in bars that don't use soy for protein. The remaining {comma(len(UNLAB))} name none of them. They just aren't labeled soy free, which is a different claim from actually containing soy.</p>
      </div>
      <div class="score-grid" style="margin-top:1.5rem;">
{chr(10).join(v2_count_card_html(l, HIT[l], NT, DESC_S[l]) for l in ORDER)}
{v2_count_card_html('Not labeled soy free', UNLAB, NT, "No soy protein, soy lecithin or soybean oil shows up anywhere in the ingredient list we can find, but the brand hasn't labeled the bar soy free either. That is a labeling gap, not proof the bar contains soy.", names=[])}
      </div>
      <h3 class="kt-h3">Is soy bad for you?</h3>
      <div class="section-body">
        <p>Not in our scoring. Soy protein isolate rates as a solid protein source and soy lecithin is neutral, so skipping soy doesn't raise a bar's grade by itself. This guide is for people who avoid soy, usually for an allergy, not a verdict on soy as an ingredient.</p>
      </div>
    </div>
'''

# ---------------------------------------------------------------------------
# Findings: three data findings + one chart
# ---------------------------------------------------------------------------
CLIF = by_brand('CLIF Bar')
CLIF_SP = [b for b in CLIF if has_s(b, 'Soy protein')]
C.check(CLIF and len(CLIF_SP) == len(CLIF) and not any(QF(b) for b in CLIF), 'every CLIF Bar flavor uses soy protein and none is labeled soy free')
ASQ, ASA = rate(Q, 'Artificial Sweeteners'), rate(ALL, 'Artificial Sweeteners')
POQ, POA = rate(Q, 'Processed Oils'), rate(ALL, 'Processed Oils')
C.check(int(ASQ) < int(ASA) and int(POQ) < int(POA), 'soy free bars carry artificial sweeteners and processed oils less often')
C.check(sum(1 for b in Q if b['score_band'] in 'AB') / N > sum(1 for b in ALL if b['score_band'] in 'AB') / NT,
        'soy free bars grade A or B more often than the database')
LEC = len(HIT['Soy lecithin'])
INSIGHTS = [
    ('Soy lecithin is the most common soy source, not soy protein.',
     f"{comma(LEC)} bars ({pct0(LEC, NT)}% of the database) name soy lecithin, against {comma(len(HIT['Soy protein']))} with soy "
     f"protein. CLIF Bar is the soy-protein example: all {len(CLIF)} flavors use it."),
    ('Soy free bars grade better, but not because of the soy.',
     f"{ab(Q)}% of soy free bars grade A or B, against {ab(ALL)}% database-wide. Soy isn't penalized in our scoring. Brands that "
     f"skip soy also tend to skip artificial sweeteners ({ASQ}% vs. {ASA}%) and processed oils ({POQ}% vs. {POA}%)."),
    ('Many bars without the label have no soy we can find.',
     f"{comma(len(UNLAB))} of the {comma(ND)} bars without a soy free label name no soy protein, soy lecithin or soybean oil."),
]
GRADE_ROWS = [(g, sum(1 for b in Q if b['score_band'] == g), sum(1 for b in ALL if b['score_band'] == g)) for g in BAND_ORDER]
GRV = {g: round(100 * h / t) for g, h, t in GRADE_ROWS}
C.check(min(GRV['A'], GRV['B']) > max(GRV['D'], GRV['F']), 'A and B bars are labeled soy free more often than D and F bars')
FINDINGS = findings_v2_html(f'What we found screening {DB_PUBLIC} bars', INSIGHTS,
                            grade_share_chart_html(GRADE_ROWS, title='Share of bars labeled soy free, by ingredient grade',
                                                   note=f'Out of the {DB_PUBLIC} bars in our database.'))

# ---------------------------------------------------------------------------
# Brands that do it well + big brands
# ---------------------------------------------------------------------------
WELL = brands_well_rows(ALL, QF, n=8)
C.check(sum(r['big'] for r in WELL) >= 2 and sum(not r['big'] for r in WELL) >= 2, 'brands-well has 2+ big and 2+ small brands')
def well_why(r):
    lead = (f"All {r['total']} flavors are soy free" if r['q'] == r['total'] else
            f"{r['q']} of {r['total']} flavors {'is' if r['q'] == 1 else 'are'} soy free")
    gm = r['grades']
    grades = (f"graded {next(iter(gm))}" if r['q'] == 1 else
              f"all {next(iter(gm))} grade" if len(gm) == 1 else grade_mix_text(gm) + ' grade')
    bp = best_pick(r['qual'])
    return f"{lead}, {grades}. Best pick: {bp['Flavor Name']} ({bp['score_band']}, {fnum(P(bp))}g protein, {fnum(CAL(bp))} cal)."
BRANDS_WELL = brands_well_html(WELL, well_why, h2='Brands that do it well',
                               intro='Brands with at least 3 bars in our database, ranked by how much of their lineup is labeled '
                                     'soy free and how well those bars grade. We made sure to include both brands you can find '
                                     'at most grocery stores and smaller independents.')

def soy_top(disq):
    c = Counter(l for b in disq for l in RX if has_s(b, l))
    return sorted(c.items(), key=lambda kv: (-kv[1], ORDER.index(kv[0])))
def big_verdict(r):
    disq = [b for b in r['bars'] if not QF(b)]
    bp = best_pick(r['qual'])
    pick = f" Best pick: {bp['Flavor Name']} ({bp['score_band']}, {fnum(P(bp))}g protein)." if bp else ''
    low_n = sum(1 for b in r['qual'] if b['score_band'] in ('C', 'D', 'F'))
    low_txt = ('' if low_n * 2 <= r['q'] else
               f" {'All' if low_n == r['q'] else 'Most'} of the soy free ones grade C or below, so check the label.")
    if r['q'] == r['total']:
        return 'Every flavor is labeled soy free.' + (low_txt.replace(' of the soy free ones', '') if low_txt else pick)
    top = soy_top(disq)
    if not top:
        why = "none name soy protein, soy lecithin or soybean oil, they just aren't labeled soy free"
    elif top[0][1] == len(disq):
        why = f'every one has {top[0][0].lower()}'
    else:
        why = f'most have {top[0][0].lower()}' if top[0][1] * 2 > len(disq) else f'{top[0][0].lower()} is the most common reason'
    if r['q'] == 0:
        return f"None are labeled soy free: {why}."
    verb = 'is' if r['q'] == 1 else 'are'
    return (f"{'Only ' if r['q'] * 2 < r['total'] else ''}{r['q']} of {r['total']} {verb} labeled soy free. Of the rest, {why}."
            + (low_txt or pick))
BIG_HTML, BIG_ROWS = big_brands_html(
    ALL, QF, big_verdict, h2='How do the big brands fare on soy free?',
    intro=('Every brand with national grocery, big-box or Costco distribution, with how many of its bars are labeled soy free. '
           'Brand names link to our full reviews where we have one.'))

# ---------------------------------------------------------------------------
# Top 50 + Bar Finder CTA + criteria
# ---------------------------------------------------------------------------
T50 = top50_rows(Q, 50)
C.check(not any(any_s(b) and not reviewed_ok(b, 'soy free') for b in T50), 'no Top 50 bar names a soy source (a mislabeled bar would need a HOLD)')
TOP50 = top50_html(T50, h2='Top 50 soy free protein bars',
                   intro='Ranked by ingredient grade first, then by protein per calorie. Tap any row for nutrition facts and '
                         'the full ingredient list.')
FINDER = finder_cta_html(N, FINDER_HREF, desc=('The Bar Finder opens with the Soy Free filter already on, the same label this '
                                               'guide uses. Add your own filters for protein, sugar, calories, grade, brand, '
                                               'other certifications, or ingredients to exclude.'))
CRITERIA = criteria_html(
    qualify_rule=('The brand labels the bar soy free (the Soy Free field in our database). We also read every ingredient list '
                  'for soy lecithin, soy protein and soybean oil, to explain why the rest miss. '
                  f'{comma(N)} of the {DB_PUBLIC} bars we track qualify.'),
    picks=PICKS)

# ---------------------------------------------------------------------------
# FAQ (answers may hold links; JSON-LD gets the plain text)
# ---------------------------------------------------------------------------
CONSIDER, MIXED, AVOID = brand_split(ALL, QF)
ALLSF = sorted((r for r in CONSIDER if r['d'] == 0), key=lambda r: (-r['total'], r['brand'].lower()))
C.check(len(ALLSF) >= 2, 'at least two fully soy free brands')
SPLIT_EX = min((r for r in CONSIDER + MIXED + AVOID if r['q'] and r['d'] and r['total'] >= 10),
               key=lambda r: (abs(r['q'] / r['total'] - 0.5), -r['total'], r['brand']))
BEST = PK['Best overall']
FAQS = [
    ('What makes a protein bar soy free on this site?',
     f'We use the Soy Free (Y/N) label on file for each bar. {of_db(N, NT, True)} bars we track carry that label. We also '
     'cross-check ingredient lists ourselves for soy protein, soy lecithin, and soybean oil, the three named soy sources that '
     'show up most in the data.'),
    ('What is the best soy free protein bar?',
     f"By our rules, {full(BEST)}: {BEST['score_band']}-grade ingredients, {fnum(P(BEST))}g protein and {fnum(CAL(BEST))} "
     f"calories. For the most protein, {full(PK['Highest protein'])} has {fnum(P(PK['Highest protein']))}g. Every bar in our "
     "Best 10 is labeled soy free with an A or B grade."),
    ('How many soy free protein bars are in your database?',
     f"{of_db(N, NT, True)} bars we track are labeled soy free, spanning {BRANDS_Q} brands. {GR['A']} of those {comma(N)} bars "
     'grade A for ingredient quality.'),
    ('Is CLIF Bar soy free?',
     f"No. All {len(CLIF)} CLIF Bar flavors we track use soy protein, and none carry a soy free label."),
    ('What is the most common soy ingredient in protein bars?',
     f"Soy lecithin. It shows up by name in {of_db(LEC, NT, True)} bars we track, more than soy protein or soybean oil. It's "
     'used as a cheap emulsifier in all kinds of bars, not just ones built around a soy protein source.'),
    ('Does not being labeled soy free mean a bar contains soy?',
     f"Not necessarily. {comma(len(UNLAB))} of the {comma(ND)} bars that don't carry a soy free label show no soy protein, soy "
     "lecithin, or soybean oil anywhere in their own ingredient list. The brand just hasn't labeled the bar soy free, which is "
     'a different claim from it containing soy.'),
    ("Can a brand have some soy free flavors and some that aren't?",
     f"Yes. {SPLIT_EX['brand']} splits closest to even of any large lineup we checked: {SPLIT_EX['q']} of {SPLIT_EX['total']} "
     'flavors are labeled soy free. Always check the specific flavor, not just the brand.'),
    ('What protein bars are soy free?',
     f"{comma(N)} bars across {BRANDS_Q} brands carry a soy free label, led by brands like {ALLSF[0]['brand']} and "
     f"{ALLSF[1]['brand']} that qualify across their entire lineup. Our Best 10 picks are at the top of this page, the Top 50 "
     'is further down, and the Bar Finder has all of them.'),
    ('Are soy free protein bars lower quality than regular bars?',
     f"No, the opposite: {ab(Q)}% of soy free bars grade A or B, against {ab(ALL)}% database-wide. That's not because soy itself "
     'is penalized: soy protein isolate scores well in our system and soy lecithin is neutral. Brands that skip soy also tend '
     f'to skip artificial sweeteners ({ASQ}% of soy free bars vs. {ASA}% database-wide) and processed oils ({POQ}% vs. {POA}%). '
     f"What soy free bars give up on average is protein: {fnum(round(avg(Q, 'Protein (g)'), 1))}g against "
     f"{fnum(round(avg(ALL, 'Protein (g)'), 1))}g."),
    ('Is soy free the same as vegan?',
     'No. A soy free bar just has no soy protein, soy lecithin, or soybean oil. It can still contain whey, milk, honey, egg, or '
     "collagen. Check our Vegan Protein Bars guide separately if that's what you need."),
    ('How often is this list updated?',
     'We update the database whenever new bars are added or a brand reformulates. Manufacturers do change their ingredient '
     'lists over time, so always confirm against the packaging in front of you.'),
]
C.check(avg(Q, 'Protein (g)') < avg(ALL, 'Protein (g)'), 'soy free bars average less protein')

# ---------------------------------------------------------------------------
# Regions
# ---------------------------------------------------------------------------
H1 = 'The 10 Best Soy Free Protein Bars'
TITLE = f'10 Best Soy Free Protein Bars ({DB_PUBLIC} Checked)'
DESC = (f'Only {pct0(N, NT)}% of protein bars are labeled soy free. We checked {DB_PUBLIC} for soy protein, soy lecithin and '
        f'soybean oil. Our 10 best.')
OG_DESC = (f'{comma(N)} soy free protein bars, checked against the label and the ingredient list. Here are the 10 best, each '
           'picked by a published rule.')
C.check(len(DESC) <= 155, f'meta description under 155 characters ({len(DESC)})')
FAQS_PLAIN = [(q, plain_text(a)) for q, a in FAQS]
REGIONS = v2_head_regions(title=TITLE, h1=H1, desc=DESC, og_desc=OG_DESC, url=URL, about='Soy Free Protein Bars',
                          published=PUBLISHED, faqs=FAQS_PLAIN, picks=PICKS)
EDITORIAL = f'  <section class="section off" id="what-disqualifies">{DISQ}  </section>'
HERO = (f'<h1 class="hero-title">{esc(H1)}</h1>\n'
        f'    <p class="hero-sub">Soy is one of the most common food allergens, and it hides in protein bars in three forms: soy '
        f'protein to boost the protein count, soy lecithin as an emulsifier, and soybean oil in coatings. We use the soy free '
        f'label on every bar, then read the ingredient list ourselves for all three.</p>\n'
        f'    <p class="hero-sub">Of the {DB_PUBLIC} bars we track, {comma(N)} are labeled soy free, about {pct0(N, NT)}%. Soy '
        f'lecithin is the most common reason the rest miss, and {comma(len(UNLAB))} name no soy at all but aren\'t labeled soy '
        f'free, so we leave them out.</p>')
REGIONS += [
    ('hero', HERO),
    ('best10', best10_html(PICKS, h2='Best 10 soy free protein bars', intro=B10_INTRO)),
    ('editorial', EDITORIAL),
    ('findings', FINDINGS),
    ('brands-well', BRANDS_WELL),
    ('big-brands', BIG_HTML),
    ('top50', TOP50),
    ('finder-cta', FINDER),
    ('criteria', CRITERIA),
    ('faq', faq_items_html(FAQS)),
    ('author', byline_html()),
    ('explore-more', related_html([
        ('/dairy-free-protein-bars', 'Dairy Free Protein Bars', 'Bars labeled dairy free, checked for whey, milk and casein.'),
        ('/gluten-free-protein-bars', 'Gluten Free Protein Bars', 'Bars labeled gluten free, checked against the ingredient list.'),
        ('/vegan-protein-bars', 'Vegan Protein Bars', 'Bars with no whey, milk, honey, egg, or gelatin.'),
    ])),
]

if __name__ == '__main__':
    page = build_guide_page_v2(PAGE, REGIONS, ALL, C, picks=PICKS)
    size = len(page.encode('utf-8'))
    faq_at = len(page[:page.find('<section class="guide-faq"')].encode('utf-8'))
    print(f'{PAGE}: {N} qualify, {ND} disqualified, {size:,} bytes, FAQ at byte {faq_at:,}')
    for i, (s_, b, why, n) in enumerate(PICKS, 1):
        print(f'  {i:2d}. {s_.label}: {full(b)} ({b["score_band"]}) [pool {n}]')
        print(f'      {why}')
