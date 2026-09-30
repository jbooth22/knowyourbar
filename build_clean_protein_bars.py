#!/usr/bin/env python3
"""Rebuild clean-protein-bars.html from bars.js. GUIDE PAGE v2 ("Best 10").

Run from the repo root:  python3 build_clean_protein_bars.py

Layout and every rule: claude/GUIDE_PAGE_SPEC_V2.md (locked 2026-09-29) and
the v2 section of kyb_guide_lib.py, built the same way as the other v2 guides
(closest reference: build_no_seed_oils.py). The first run migrated the live v1
page to the v2 body (head, nav and footer kept as deployed); later runs rewrite
only the <!-- kyb:NAME --> regions. Every number, pick and brand row comes from
bars.js. Copy that depends on a fact is checked; if one stops being true the
build stops and lists it. Ingredient quality is shown and ranked as a GRADE only.

Screen: GUIDE_FILTERS['clean-protein-bars'] (A or B grade, no 'Artificial
Sweeteners' tag, no 'Processed Oils' tag).
Bar Finder: /bar-finder?preset=no_seed_oil&grade=A,B&excl=sucralose. No single
preset matches (the Clean Ingredients preset is A only, 12g+ protein, no sugar
alcohols). Sucralose-free is the no-artificial-sweetener set and the
no_seed_oil preset is the no-processed-oil set, key for key, so the three
together are exactly this guide. Checked below on every build.

Guide slots (locked with Jeff 2026-09-30): Best whey protein, Lowest net carbs,
Best non-GMO, Best soy-free. Fallbacks: Best dairy-free, then Highest fiber.
Chosen to keep this list distinct from the four other v2 guides (the six core
slots go to the same clean bars on every free-from guide).
"""
import re
from kyb_guide_lib import *

PAGE = 'clean-protein-bars.html'
URL = 'https://knowyourbar.com/clean-protein-bars'
PUBLISHED = '2026-04-01'
set_tie_seed('clean-protein-bars')   # per-guide shuffle for exact ties (kyb_guide_lib, 2026-09-30)

ALL = load_bars()
QF = GUIDE_FILTERS['clean-protein-bars']
Q = [b for b in ALL if QF(b)]
D = [b for b in ALL if not QF(b)]
N, ND, NT = len(Q), len(D), len(ALL)
BRANDS_ALL = {b['Brand Name'] for b in ALL}
BRANDS_Q = {b['Brand Name'] for b in Q}
PCT_D = pct0(ND, NT)
C = Claims()

def low_grade(b): return b.get('score_band') in ('C', 'D', 'F')
def art_sw(b): return has_tag(b, 'Artificial Sweeteners')
def proc_oil(b): return has_tag(b, 'Processed Oils')
def fails(b): return (low_grade(b), art_sw(b), proc_oil(b))
LOW = [b for b in ALL if low_grade(b)]
AS = [b for b in ALL if art_sw(b)]
PO = [b for b in ALL if proc_oil(b)]
MULTI = [b for b in D if sum(fails(b)) > 1]
OIL_AND_GRADE = [b for b in MULTI if low_grade(b) and proc_oil(b)]
ONLY_GRADE = sum(1 for b in D if fails(b) == (True, False, False))
ONLY_OIL = sum(1 for b in D if fails(b) == (False, False, True))
ONLY_AS = sum(1 for b in D if fails(b) == (False, True, False))
C.check(len(LOW) > max(len(PO), len(AS)), 'a C-or-below grade is the most common reason a bar fails')
C.check(len(MULTI) > ND / 2, 'most disqualified bars fail more than one screen')
C.check(len(OIL_AND_GRADE) > len(MULTI) / 2, 'most multi-screen failures are a processed oil plus a C-or-below grade')

# Bar Finder parity: preset=no_seed_oil (app.js hasSeedOil) + grade=A,B + excl=sucralose
FINDER_KW = ['palm oil', 'palm kernel oil', 'canola oil', 'soybean oil', 'hydrogenated', 'partially hydrogenated',
             'palm fruit oil', 'sunflower oil', 'safflower oil', 'vegetable oil', 'rapeseed oil', 'cottonseed oil',
             'corn oil', 'grapeseed oil', 'rice bran oil', 'palm fat']
def finder_has_seed_oil(b):
    t = (b.get('Ingredients') or '').lower()
    for kw in FINDER_KW:
        i = t.find(kw)
        if i == -1:
            continue
        if 'high oleic' in t[max(0, i - 20):i + len(kw)]:
            continue
        return True
    return False
def finder_match(b):
    return (not finder_has_seed_oil(b) and b.get('score_band') in ('A', 'B')
            and 'sucralose' not in (b.get('Ingredients') or '').lower())
C.check({b['Key'] for b in ALL if finder_match(b)} == {b['Key'] for b in Q},
        'Bar Finder no_seed_oil + grade A,B + excl=sucralose returns exactly the guide set')
FINDER_HREF = '/bar-finder?preset=no_seed_oil&grade=A,B&excl=sucralose'

# The Clean Ingredients preset (app.js PRESETS.clean), described honestly on the page
CLEAN_PRESET_BAD = ['sucralose', 'acesulfame', 'aspartame', 'saccharin', 'erythritol', 'maltitol', 'xylitol', 'sorbitol',
                    'mannitol', 'isomalt']
def clean_preset(b):
    t = ingr(b).lower()
    return b.get('score_band') == 'A' and P(b) >= 12 and not any(s in t for s in CLEAN_PRESET_BAD)
PRESET_SET = [b for b in ALL if clean_preset(b)]
C.check(len(PRESET_SET) < N, 'the Clean Ingredients preset is stricter (smaller) than this guide')

def link(href, text): return f'<a href="{href}">{text}</a>'
def by_brand(brand, bars=ALL): return [b for b in bars if b['Brand Name'] == brand]
def yes(field): return lambda b: b.get(field) == 'Yes'
NI = lambda b: top_level_ingredient_count(ingr(b))

# ---------------------------------------------------------------------------
# Best 10 (spec v2; guide slots locked with Jeff 2026-09-30)
# ---------------------------------------------------------------------------
WHEY_RX = re.compile(r'\bwhey\b[^,;()\[\]]*', re.I)
def whey(b): return bool(WHEY_RX.search(ingr(b)))
def whey_name(b): return WHEY_RX.search(ingr(b)).group(0).strip().lower()
def nc(b): return net_carbs(b)
def nc_why(b, c):
    sa = SA(b)
    parts = f"{fnum(num(b.get('Total Carbohydrates (g)')))}g carbs minus {fnum(FIB(b))}g fiber" + (f" and {fnum(sa)}g sugar alcohol" if sa else '')
    return (f"{fnum(nc(b))}g net carbs ({parts}), {c['tied']}the lowest of any bar here, with {fnum(P(b))}g protein"
            + (f", and it wins the tie on {c['tie_on']}." if c['tied'] and c['tie_on'] != 'name' else "."))
LOW_NET = Slot('Lowest net carbs', 'The fewest net carbs (total carbs minus fiber minus sugar alcohol), grade B or better, 10g+ protein.',
               lambda E: [b for b in E if nc(b) is not None], lambda b: (nc(b),) + tie_chain(b), nc_why, metric=nc)
SOY_RX = re.compile(r'\bsoy|soybean', re.I)
SLOTS = [
    slot_best_overall(15),
    slot_cleanest(),
    slot_highest_protein(300),
    slot_protein_per_cal(12),
    slot_lowest_calorie(),
    slot_big_brand(),
    slot_subset('Best whey protein', 'Whey protein on the label.', whey,
                lambda b: f"Built on {whey_name(b)}, a complete dairy protein and "
                          + ("one of the protein sources our scoring rates highest." if 'isolate' in whey_name(b)
                             else "one of the protein sources our scoring rates near the top.")),
    LOW_NET,
    slot_subset('Best non-GMO', 'Labeled Non-GMO by the brand.', yes('Non-GMO (Y/N)'),
                lambda b: 'Labeled Non-GMO by the brand, on top of clearing every clean screen.'),
    slot_subset('Best soy-free', 'Labeled soy free by the brand.', yes('Soy Free (Y/N)'),
                lambda b: 'Labeled soy free, with no soy protein, soy lecithin or soybean oil on the label.'),
]
FALLBACKS = [
    slot_subset('Best dairy-free', 'Labeled dairy free by the brand.', yes('Dairy Free (Y/N)'),
                lambda b: 'Labeled dairy free, so no whey, milk protein or other dairy on the label.'),
    slot_highest_fiber(),
]
PICKS = pick_best10(Q, SLOTS, FALLBACKS)
C.check(len(PICKS) == 10, 'ten Best 10 picks available')
C.check([s.label for s, *_ in PICKS] == [s.label for s in SLOTS], 'all ten planned slots filled without fallbacks')
C.check(not any(re.search(r'score \d|scored? \d', w) for _s, _b, w, _n in PICKS), 'no ingredient score printed in a pick')
PK = {s.label: b for s, b, _w, _n in PICKS}
C.check(has_tag(PK['Best whey protein'], 'Quality Protein Source'), 'the whey pick carries the Quality Protein Source tag')
C.check(re.search(r'whey protein (isolate|concentrate)|whey\b', whey_name(PK['Best whey protein'])), 'whey pick names a whey protein')
C.check(not SOY_RX.search(ingr(PK['Best soy-free'])), 'the soy-free pick names no soy ingredient')
B10_INTRO = ("Ten clean bars, each the winner of one thing people shop for. Every pick has an A or B ingredient grade, no "
             "artificial sweeteners, no processed oils and at least 10g of protein, and no bar appears twice.")

# ---------------------------------------------------------------------------
# What "clean" means: the three screens (carried over from v1, trimmed)
# ---------------------------------------------------------------------------
SA_Q = [b for b in Q if has_sugar_alcohol(b)]
ERY_Q = [b for b in Q if 'erythritol' in ingr(b).lower()]
C.check(SA_Q and ERY_Q, 'some clean bars contain a sugar alcohol / erythritol')
C.check(all(b['score_band'] == 'B' for b in ERY_Q), 'every clean bar with erythritol grades B')
LOW_BRANDS = {b['Brand Name'] for b in LOW}
CARDS = '\n'.join([
    v2_count_card_html('Ingredient grade C or below', LOW, NT,
                       'The most common reason a bar fails. A C, D or F usually means synthetic additives, a lot of added '
                       'sugar, or processed protein blends outweighing the good parts of the label.',
                       names=[]).replace('\n        </div>', f'\n          <div class="oil-card-brands"><span class="oil-card-brands-label">Affects:</span> '
                                                           f'at least one flavor from {len(LOW_BRANDS)} of the {len(BRANDS_ALL)} brands we track</div>\n        </div>', 1),
    v2_count_card_html('Artificial sweeteners', AS, NT,
                       'Sucralose and acesulfame potassium, usually there to hit a low sugar number, often alongside '
                       'allulose or fiber syrups.'),
    v2_count_card_html('Processed oils', PO, NT,
                       'A refined oil like canola, soybean, palm or palm kernel, or a hydrogenated fat, used for shelf life '
                       'or texture, not nutrition.'),
])
MEANS = f'''
    <div class="section-inner">
      <h2 class="section-title">What "clean" actually means on this page</h2>
      <div class="section-body">
        <p>Search for clean protein bars and most lists filter on a vibe: "real food," "no junk," a short ingredient list. We don't screen on a feeling. Clean here means three pass or fail checks stacked together: an A or B ingredient grade, no artificial sweeteners, and no processed oils. A bar has to pass all three, not just the one that's easiest to market.</p>
        <p>{PCT_D}% of the {DB_PUBLIC} bars in our database fail at least one of them. Here is how often each screen catches a bar.</p>
      </div>
      <div class="score-grid" style="margin-top:1.5rem;">
{CARDS}
      </div>
      <h3 class="kt-h3">Why these three checks</h3>
      <div class="section-body">
        <p>The two ingredient checks catch things a nutrition panel can't. Artificial sweeteners (sucralose, acesulfame potassium, aspartame, saccharin) show up in bars that already look great on paper, low sugar and high protein, because a synthetic sweetener is the cheapest way to hit those numbers. Processed oils (canola, soybean, palm, hydrogenated oils) do the same job for texture and shelf life. Neither shows up in the sugar or fat grams. You have to read the ingredient list to catch them.</p>
        <p>The A or B grade stops a bar from qualifying just by skipping those two. Our grade also weighs where the protein comes from and how far down the list each ingredient sits, so a bar that skips sweeteners and seed oils but leans on a low-quality protein blend or a long list of additives still won't make it.</p>
        <p><strong>Four questions worth asking before you call a bar clean:</strong></p>
        <ul class="criteria-list">
          <li>What's the sweetener: a natural sugar, a sugar alcohol, or one of the four synthetic ones we screen for?</li>
          <li>What's the main fat: a refined seed oil, or something less processed like nut butter or coconut oil?</li>
          <li>Where does the protein come from: a single quality source, or a stack of isolates and blends?</li>
          <li>Does the ingredient grade back it up, or is a clean-sounding brand still grading C or below?</li>
        </ul>
      </div>
      <h3 class="kt-h3">What clean doesn't cover</h3>
      <div class="section-body">
        <p>Clean and healthy aren't the same claim. None of the three checks look at macros, so a clean bar can still run high in calories or sugar. Clean also doesn't screen out sugar alcohols: {len(SA_Q)} of the {comma(N)} bars here contain one, like erythritol or IMO. If you want to skip those too, see our {link('/no-sugar-alcohols', 'protein bars without sugar alcohols guide')}. The Bar Finder's Clean Ingredients filter is stricter than this page: A grade only, 12g+ protein, and no sugar alcohols, which leaves {len(PRESET_SET)} bars.</p>
      </div>
      {section_cta_html('/bar-finder?preset=clean', 'Open the stricter Clean Ingredients filter &rarr;',
                        'Opens the Bar Finder with the Clean Ingredients preset: A grade, 12g+ protein, no artificial sweeteners and no sugar alcohols.')}
    </div>
'''

# ---------------------------------------------------------------------------
# Findings: three data findings + one chart
# ---------------------------------------------------------------------------
BB, QU = by_brand('Barebells'), by_brand('Quest')
BQ = BB + QU
C.check(not any(QF(b) for b in BQ), 'no Barebells or Quest flavor qualifies')
C.check(all(art_sw(b) for b in BQ), 'every Barebells and Quest flavor has an artificial sweetener')
BQ_PO, BQ_LOW = sum(map(proc_oil, BQ)), sum(map(low_grade, BQ))
AVG_P_Q, AVG_P_D = avg(Q, 'Protein (g)'), avg(D, 'Protein (g)')
C.check(AVG_P_D > AVG_P_Q, 'disqualified bars average more protein than clean bars')
GRADE_ROWS = [(g, sum(1 for b in ALL if b['score_band'] == g and (art_sw(b) or proc_oil(b))),
               sum(1 for b in ALL if b['score_band'] == g)) for g in BAND_ORDER]
GR = {g: round(100 * h / t) for g, h, t in GRADE_ROWS}
C.check(GR['A'] <= GR['B'] <= GR['C'] <= GR['D'] <= GR['F'] and GR['A'] < GR['F'],
        'sweetener-or-oil share never falls with a step down in grade, and F is well above A')
INSIGHTS = [
    ('Most failing bars fail more than one check.',
     f'Of the {ND} bars that fail, {len(MULTI)} fail two or all three checks at once, {len(OIL_AND_GRADE)} of them with a '
     f'processed oil and a C-or-below grade together. Only {ONLY_GRADE} fail on grade alone, {ONLY_OIL} on processed oils '
     f'alone, and {ONLY_AS} on artificial sweeteners alone.'),
    ('Barebells and Quest fail completely.',
     f'None of the {len(BB)} Barebells flavors or {len(QU)} Quest flavors qualify. Every one contains an artificial '
     f'sweetener, {BQ_PO} of {len(BQ)} also contain a processed oil, and {BQ_LOW} of {len(BQ)} grade C or below.'),
    ('Failing bars average more protein.',
     f'Bars that fail average {fnum(AVG_P_D)}g of protein against {fnum(AVG_P_Q)}g for clean bars. Big protein numbers often '
     'come from processed protein blends and synthetic sweeteners doing the work.'),
]
FINDINGS = findings_v2_html(f'What we found screening {DB_PUBLIC} bars', INSIGHTS,
                            grade_share_chart_html(GRADE_ROWS, title='Share of bars with an artificial sweetener or processed oil, by ingredient grade',
                                                   note=f'Out of the {DB_PUBLIC} bars in our database. Every C, D and F bar also fails on grade.'))

# ---------------------------------------------------------------------------
# Brands that do it well + big brands
# ---------------------------------------------------------------------------
WELL = brands_well_rows(ALL, QF, n=8)
C.check(sum(r['big'] for r in WELL) >= 2 and sum(not r['big'] for r in WELL) >= 2, 'brands-well has 2+ big and 2+ small brands')
def well_why(r):
    lead = f"All {r['total']} flavors qualify" if r['q'] == r['total'] else f"{r['q']} of {r['total']} flavors qualify"
    g = r['grades']
    grades = f"all {next(iter(g))} grade" if len(g) == 1 else grade_mix_text(g) + ' grade'
    bp = best_pick(r['qual'])
    return f"{lead}, {grades}. Best pick: {bp['Flavor Name']} ({bp['score_band']}, {fnum(P(bp))}g protein, {fnum(CAL(bp))} cal)."
BRANDS_WELL = brands_well_html(WELL, well_why, h2='Brands that do it well',
                               intro='Brands with at least 3 bars in our database, ranked by how much of their lineup qualifies '
                                     'and how well those bars grade. We made sure to include both brands you can find at most '
                                     'grocery stores and smaller independents.')

def fail_reasons(disq):
    rs = [('a processed oil', sum(1 for b in disq if proc_oil(b))),
          ('an artificial sweetener', sum(1 for b in disq if art_sw(b))),
          ('a C-or-below grade', sum(1 for b in disq if low_grade(b)))]
    rs.sort(key=lambda r: -r[1])
    return rs
def big_verdict(r):
    disq = [b for b in r['bars'] if not QF(b)]
    bp = best_pick(r['qual'])
    pick = f" Best pick: {bp['Flavor Name']} ({bp['score_band']}, {fnum(P(bp))}g protein)." if bp else ''
    if r['q'] == r['total']:
        return 'Every flavor qualifies.' + pick
    rs = fail_reasons(disq)
    every = [n for n, c in rs if c == len(disq)]
    main = every[0] if every else rs[0][0]
    if r['q'] == 0:
        return (f"None qualify: every flavor has {main}." if every else f"None qualify. Most flavors have {main}.")
    return f"{'Only ' if r['q'] * 2 < r['total'] else ''}{r['q']} of {r['total']} qualify. The rest mostly have {main}." + pick
BIG_HTML, BIG_ROWS = big_brands_html(
    ALL, QF, big_verdict, h2='How do the big brands fare on clean ingredients?',
    intro=('Every brand with national grocery, big-box or Costco distribution, with how many of its bars pass all three '
           'clean checks. Brand names link to our full reviews where we have one.'))

# ---------------------------------------------------------------------------
# Top 50 + Bar Finder CTA + criteria
# ---------------------------------------------------------------------------
T50 = top50_rows(Q, 50)
TOP50 = top50_html(T50, h2='Top 50 clean protein bars',
                   intro='Ranked by ingredient grade first, then by protein per calorie. Tap any row for nutrition facts and '
                         'the full ingredient list.')
FINDER = finder_cta_html(N, FINDER_HREF, desc=('The Bar Finder opens with this same screen applied: A or B grade, sucralose '
                                               'excluded (every artificial-sweetener bar we track contains it) and the No Seed '
                                               'Oil filter on. Add your own filters for protein, sugar, calories, brand, '
                                               'certifications, or ingredients to exclude.'))
CRITERIA = criteria_html(
    qualify_rule=('An A or B ingredient grade, no artificial sweeteners (sucralose, acesulfame potassium, aspartame, '
                  'saccharin), and no processed oils (canola, soybean, palm, palm kernel, sunflower and other refined seed '
                  'oils, or hydrogenated fat). Sugar alcohols, stevia, monk fruit, coconut oil and high-oleic oils do not '
                  f'count against a bar. {comma(N)} of the {DB_PUBLIC} bars we track qualify.'),
    picks=PICKS)

# ---------------------------------------------------------------------------
# FAQ (answers may hold links; JSON-LD gets the plain text)
# ---------------------------------------------------------------------------
CONSIDER, MIXED, AVOID = brand_split(ALL, QF)
MIX_EX = sorted(MIXED, key=lambda r: (-r['total'], r['brand'].lower()))[:2]
C.check(len(MIX_EX) == 2, 'two mixed-lineup brands to cite')
WHOLE_FOOD = [r for r in CONSIDER + MIXED if r['total'] >= 8 and r['q'] / r['total'] >= 0.9
              and sum(1 for b in r['qual'] if has_tag(b, 'Whole Food Forward')) >= r['q'] / 2]
WHOLE_FOOD.sort(key=lambda r: (-r['total'], r['brand'].lower()))
LEADERS = [r['brand'] for r in WHOLE_FOOD[:3]]
C.check(len(LEADERS) == 3, 'three whole-food brands qualify at or near 100%')
def mix_sentence():
    a, b = MIX_EX
    return (f"{a['brand']} qualifies at {round(100 * a['q'] / a['total'])}% ({a['q']} of {a['total']} flavors), "
            f"{b['brand']} at {round(100 * b['q'] / b['total'])}% ({b['q']} of {b['total']}).")
COLLAGEN_Q = [b for b in Q if 'collagen' in ingr(b).lower()]
FAQS = [
    ('What makes a protein bar "clean" on this page?',
     'For this guide, clean means three things at once: an A or B ingredient quality grade, no artificial sweeteners '
     '(sucralose, acesulfame potassium, aspartame, saccharin), and no processed oils (canola, soybean, palm, or hydrogenated '
     f'oils). {of_db(N, NT)} bars in our database meet all three criteria.'),
    ('Are clean protein bars better for you?',
     'Cleaner ingredients generally means fewer synthetic additives, more whole-food protein sources, and less dependence on '
     'ultra-processed fats and sweeteners. That said, macros still matter. A clean bar can still be high in calories or sugar '
     'even if the ingredient list is excellent.'),
    ('Why do so many protein bars fail the clean screen?',
     f'{len(MULTI)} of the {ND} disqualified bars fail more than one criterion at once, usually a processed oil and a below-B '
     'grade together. Manufacturers reach for cheap refined oils and synthetic sweeteners to hit specific price, shelf-life, '
     'or macro targets, and those same shortcuts tend to drag the ingredient grade down too.'),
    ('Does Barebells or Quest have any clean bars?',
     f'No. None of the {len(BB)} Barebells flavors or {len(QU)} Quest flavors clear the clean screen. Every flavor from both '
     f'brands contains an artificial sweetener, {BQ_PO} of {len(BQ)} also contain a processed oil, and {BQ_LOW} of {len(BQ)} '
     'grade C or below.'),
    ('What protein bars are clean bars?',
     f'{comma(N)} bars across {len(BRANDS_Q)} brands clear our clean screen, led by whole-food brands like '
     f'{names_and(LEADERS)} that qualify at or near 100%. Our Best 10 picks are at the top of this page, the Top 50 is '
     'further down, and the Bar Finder has all of them.'),
    ('Do clean protein bars have sugar alcohols?',
     f"Some do. This guide screens out artificial sweeteners and processed oils, not sugar alcohols, so {len(SA_Q)} of the "
     f"{comma(N)} clean bars contain one, like erythritol or IMO. If you want to skip them too, see our "
     f"{link('/no-sugar-alcohols', 'protein bars without sugar alcohols guide')}. The Bar Finder's Clean Ingredients filter "
     "is stricter than this page: A grade only, 12g+ protein, and no sugar alcohols."),
    ('Is erythritol considered a clean ingredient?',
     "It depends on your standard. Erythritol is a sugar alcohol, usually made by fermenting glucose from corn. Our scoring "
     "counts it as a concern, so it pulls a bar's grade down, but it doesn't disqualify a bar from this guide on its own. "
     f"{len(ERY_Q)} bars with erythritol still earn a B and make this list."),
    ('What protein sources score best?',
     'Egg whites and whey protein isolate rate highest in our scoring, with whey protein concentrate, casein and milk protein '
     'close behind. Plant proteins like pea and brown rice protein rate a step lower but still count in a bar\'s favor. '
     'Collagen rates lowest of the proteins: it still counts as a positive, just a small one, because it lacks some of the '
     f'essential amino acids your body needs to build muscle. {len(COLLAGEN_Q)} of the clean bars here contain collagen.'),
    ('Can a brand have some clean flavors and some not?',
     "Yes, and it's common. " + mix_sentence() + " Check the specific flavor before assuming a brand's whole lineup is clean "
     'just because one flavor is.'),
    ('How often is this list updated?',
     'We update the database when new bars are added or when brands change their formulas. Grades on this page are rebuilt '
     'from the same database every time it changes, so they always match the Bar Finder.'),
]

# ---------------------------------------------------------------------------
# Regions
# ---------------------------------------------------------------------------
H1 = 'The 10 Best Clean Protein Bars'
TITLE = f'10 Best Clean Protein Bars ({DB_PUBLIC} Checked)'
DESC = (f'{PCT_D}% of protein bars fail our clean screen: A or B grade, no artificial sweeteners, no processed oils. '
        f'Our 10 best from {comma(N)} that pass.')
OG_DESC = (f'We screened {DB_PUBLIC} protein bars for ingredient grade, artificial sweeteners and processed oils. '
           f'{comma(N)} pass all three. Here are the 10 best, each picked by a published rule.')
C.check(len(DESC) <= 155, f'meta description under 155 characters ({len(DESC)})')
FAQS_PLAIN = [(q, plain_text(a)) for q, a in FAQS]
REGIONS = v2_head_regions(title=TITLE, h1=H1, desc=DESC, og_desc=OG_DESC, url=URL, about='Clean Protein Bars',
                          published=PUBLISHED, faqs=FAQS_PLAIN, picks=PICKS)
EDITORIAL = f'  <section class="section off" id="what-it-means">{MEANS}  </section>'
HERO = (f'<h1 class="hero-title">{esc(H1)}</h1>\n'
        f'    <p class="hero-sub">"Clean" gets stamped on plenty of wrappers, but it rarely means anything you can check. Here it '
        f'means three things you can: an A or B ingredient grade, no artificial sweeteners like sucralose, and no processed oils '
        f'like canola, soybean or palm kernel oil.</p>\n'
        f'    <p class="hero-sub">Of the {DB_PUBLIC} bars we track, {comma(N)} pass all three. The other {PCT_D}% fail at least '
        f'one, and most fail more than one. Clean is about the ingredient list, not the macros, so a clean bar can still be '
        f'high in sugar or calories.</p>')
REGIONS += [
    ('hero', HERO),
    ('best10', best10_html(PICKS, h2='Best 10 clean protein bars', intro=B10_INTRO)),
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
        ('/no-artificial-sweeteners', 'No Artificial Sweeteners', 'Bars with zero sucralose, aspartame, or acesulfame potassium.'),
        ('/no-seed-oils', 'No Seed Oils', 'Every bar screened for canola, palm, soybean, and other refined oils.'),
        ('/no-sugar-alcohols', 'No Sugar Alcohols', 'Bars that skip maltitol, erythritol, and other sugar alcohols entirely.'),
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
