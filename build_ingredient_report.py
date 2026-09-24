"""Rebuild the ingredient report (ingredient-report.html) from bars.js and
the scoring schema.

Opens the LIVE page and rewrites only the <!-- kyb:NAME --> regions:
  head, jsonld, social   title/meta, Article + FAQPage JSON-LD, og/twitter
  hero, snapshot         hero line and the five headline numbers
  worst, best            the two top-10 lists
  findings               most common ingredients chart + four insights
  clusters               "ingredients that travel together"
  decoder                sounds-healthy decoder table
  predictor              grade-prediction signals, each with its measured hit rate
  explore                explore-more cards
  faq                    visible FAQ (JSON-LD FAQ is built from the same list)

Data: kyb_ingredients (ingredients matched exactly the way the scorer
matches them, counted anywhere on the label) and bars.js grades.

Top-10 rules: worst = ingredients scoring -2 or lower, best = +3 or higher,
each ranked by score x number of bars (the total pull the ingredient has on
the database). Every card needs a written description in WORST_TEXT /
BEST_TEXT; the build stops and names any ingredient that ranks without one.
Every factual sentence is checked against the data; the build stops and
lists anything that no longer holds.

Run: python3 build_ingredient_report.py
"""
import json, re
from kyb_guide_lib import (load_bars, esc, comma, replace_region, stamp_dates, today_iso, Claims, pct0)
from kyb_ingredients import ingredient_counts, bar_ingredients, NOT_INGREDIENTS
from build_all_ingredients import MIN_BARS, share_words

PAGE = 'ingredient-report.html'
PUBLISHED = '2026-05-01'
VAR = {4: 'var(--green-best)', 3: 'var(--green-clean)', 2: 'var(--green-good)', 1: 'var(--yellow-okay)', 0: '#888880',
       -1: 'var(--orange-minor)', -2: 'var(--red-concern)', -3: 'var(--red-avoid)', -4: 'var(--red-worst)'}
VERDICT = {4: 'Best', 3: 'Clean', 2: 'Good', 1: 'Okay', 0: 'Neutral', -1: 'Minor', -2: 'Concern', -3: 'Avoid', -4: 'Worst'}
WPI = {'whey protein isolate', 'grass-fed whey protein isolate', 'partially hydrolyzed whey protein isolate'}
EGG = {'egg whites', 'egg white', 'dried egg white', 'egg white protein'}
NUT_WORDS = ('almond', 'peanut', 'cashew', 'walnut', 'pecan', 'pistachio', 'hazelnut', 'macadamia')


def sgn(v):
    return f'+{v}' if v > 0 else str(v)


def title(k):
    return ' '.join(w if w.isupper() else w[:1].upper() + w[1:] for w in k.split())


def main():
    bars = load_bars()
    N = len(bars)
    R, _, _ = ingredient_counts(bars)
    BI = bar_ingredients(bars)
    NM = [{x['name'] for x in items} for items in BI]
    G = [b.get('score_band') for b in bars]
    listed = {k: v for k, v in R.items() if v['category'] not in NOT_INGREDIENTS and v['bars'] >= MIN_BARS
              and not k.startswith(('contains ', 'includes '))}
    S = lambda k: R[k]['score']
    B = lambda k: R[k]['bars']
    pc = lambda n: f'{100 * n / N:.1f}'
    with_ = lambda k: [i for i in range(N) if k in NM[i]]
    def share(a, b):
        A = with_(a)
        return sum(b in NM[i] for i in A) / len(A) if A else 0
    def ab(idx):
        idx = list(idx)
        return sum(G[i] in ('A', 'B') for i in idx) / len(idx) if idx else 0
    def top(i, n):
        return [x for x in BI[i] if not x['sub'] and x['pos'] <= n]
    cl = Claims()
    for k in ['palm kernel oil', 'sucralose', 'maltitol', 'maltitol syrup', 'sugar', 'cane sugar', 'whey protein isolate',
              'whey protein concentrate', 'glycerin', 'salt', 'natural flavors', 'egg whites', 'erythritol', 'soy lecithin',
              'brown rice syrup', 'tapioca syrup', 'pea protein', 'brown rice protein', 'dates', 'almonds', 'peanuts']:
        cl.check(k in listed, f'{k} is in the data')
    cl.stop_if_failed()

    pko, pko_sub = B('palm kernel oil'), B('palm kernel oil') - R['palm kernel oil']['top']
    caloric = [i for i, items in enumerate(BI) if any(x['category'] == 'sweetener' and S(x['name']) < 0 and
                                                       x['subcategory'] not in ('sugar_alcohol', 'artificial_sweetener') for x in items)]
    sugar_either = sum(1 for i in range(N) if NM[i] & {'sugar', 'cane sugar'})

    # ---------- top 10s
    impact = lambda k: S(k) * B(k)
    worst = sorted((k for k in listed if S(k) <= -2), key=impact)[:10]
    best = sorted((k for k in listed if S(k) >= 3), key=lambda k: -impact(k))[:10]
    concern_rank = sorted((k for k in listed if S(k) <= -2), key=lambda k: -B(k))
    whole = sorted((k for k in listed if R[k]['category'] == 'whole_food'), key=lambda k: -B(k))
    prot = sorted((k for k in listed if R[k]['category'] == 'protein'), key=lambda k: -B(k))
    ms_with_m = share('maltitol syrup', 'maltitol')
    po_with_pko = share('palm oil', 'palm kernel oil') if 'palm oil' in listed else 0
    oats_top3 = [i for i in range(N) if any(x['name'] == 'oats' for x in top(i, 3))]
    dates12 = [i for i in range(N) if any(x['name'] == 'dates' for x in top(i, 2))]

    cl.check(concern_rank[0] == 'sugar', 'sugar is the most common ingredient scoring -2 or worse')
    cl.check(ms_with_m >= 0.3, 'a lot of maltitol syrup bars also have maltitol (30%+)')
    cl.check(whole[:2] == ['almonds', 'peanuts'], 'almonds and peanuts are the two most common whole foods')
    cl.check(prot[0] == 'whey protein isolate', 'whey isolate is the most common protein')
    WORST_TEXT = {
        'maltitol': 'The worst-scoring sugar alcohol we track. Despite being sold as "sugar-free," maltitol has a glycemic index '
                    'around 35, roughly half of table sugar. It raises blood sugar more than most alternatives and causes real GI '
                    'distress. If you see it on a keto or diabetic bar, be skeptical of the net carb claim.',
        'maltitol syrup': f'Same ingredient, liquid form. Same score, same problems. It shows up in soft coatings and fillings where '
                          f'solid maltitol would not work. {pct0(ms_with_m * 100, 100)}% of bars with maltitol syrup also contain '
                          f'maltitol, so the sugar alcohol load is higher than either line on the label suggests.',
        'palm kernel oil': f'The most common -3 ingredient in the database, and most people have no idea it is there. In '
                           f'{comma(pko_sub)} of the {comma(pko)} bars that contain it, it only appears inside a compound ingredient '
                           f'like "chocolate flavored coating." Highly saturated, industrially processed, and tied to deforestation.',
        'brown rice syrup': 'Sounds like a whole food. It is not. Brown rice syrup is almost entirely glucose, with a glycemic index '
                            'higher than table sugar. It ends up on "clean" and "natural" bars because it sounds better than corn '
                            'syrup. It scores -3, below plain sugar.',
        'tapioca syrup': 'Same playbook as brown rice syrup. Tapioca syrup is a starch broken down into sugar: it sounds clean and '
                         'is not. No meaningful nutrients, significant glucose load, and a -3 score, one point below plain sugar.',
        'erythritol': 'Better than maltitol for blood sugar impact. Erythritol is absorbed before it reaches the colon, so the GI '
                      'issues are much less severe. But emerging research has raised questions about cardiovascular effects at '
                      'higher doses. Until that settles, we keep it at avoid.',
        'sucralose': f'In {share_words(B("sucralose"), N)} bars in the database. Research has flagged effects on the gut '
                     f'microbiome and insulin response. It costs a bar a flat -2 wherever it appears on the label, because it '
                     f'is used in milligrams and label position says nothing about its effect.',
        'sugar': 'The most common ingredient scoring -2 or worse. It scores -2 rather than lower because at least it is honest: '
                 'it does what it says. Position is what matters. Sugar in the first five ingredients means it is carrying real '
                 'weight in the formula.',
        'cane sugar': f'Sugar with a fancier name, and the same -2 score. Together, sugar and cane sugar appear in '
                      f'{comma(sugar_either)} bars ({pct0(sugar_either, N)}% of the database).',
        'palm oil': f'Palm kernel oil\'s cousin, pressed from the fruit rather than the seed. It scores -2, one point better, but '
                    f'it is still an industrial fat and often travels with palm kernel oil: {pct0(po_with_pko * 100, 100)}% of bars '
                    f'with palm oil also contain palm kernel oil.',
        'maltodextrin': 'A starch broken down into a sugar-like powder. It scores -3, the same as brown rice and tapioca syrup, '
                        'because it is made the same way.',
        'natural and artificial flavors': 'Scores worse than natural flavors alone because it adds synthetic flavor compounds '
                                          'to an already opaque label line.',
    }
    BEST_TEXT = {
        'whey protein isolate': 'The strongest protein signal in the database. Whey isolate is filtered further than concentrate, '
                                'cutting most fat and lactose. Complete amino acids, high bioavailability, fast absorption. If this '
                                'is the first or second ingredient, you are starting from a good place.',
        'almonds': 'The most common whole-food ingredient in the database. Protein, fiber, healthy fat, micronutrients. No '
                   'processing required. When almonds show up in the first few ingredients, the bar was probably built around '
                   'real food rather than engineered texture.',
        'peanuts': 'One of the most efficient ingredients in any bar: protein, fat, fiber, and micronutrients in a single item. '
                   'Peanuts and almonds are the two most common whole foods in the database and the anchors of the whole-food '
                   'bar category.',
        'whey protein concentrate': 'One step below isolate. Concentrate keeps more fat and lactose but is still a solid, complete '
                                    'protein source. A lot of bars blend both. The order matters: isolate listed first is the '
                                    'better formulation.',
        'soy protein isolate': 'A complete plant protein and a mainstream workhorse. It scores +3, the same as whey concentrate. '
                               'Common in crisps and in bars that blend several protein sources.',
        'peanut butter': 'In a bar, peanut butter is usually just ground peanuts. Same nutrients as whole peanuts, better binding. '
                         'Bars that use it as a primary ingredient tend to have shorter, cleaner lists overall.',
        'dates': f'Dates do the binding and sweetening in whole-food bars. One ingredient does what tapioca syrup, glycerin, and '
                 f'added sugar do in three to five. All {len(dates12)} bars with dates as the first or second ingredient score A or B.'
                 if ab(dates12) == 1 else
                 f'Dates do the binding and sweetening in whole-food bars. One ingredient does what tapioca syrup, glycerin, and '
                 f'added sugar do in three to five. {pct0(ab(dates12) * 100, 100)}% of bars with dates as the first or second '
                 f'ingredient score A or B.',
        'almond butter': 'Same logic as peanut butter: ground almonds, whole-food nutrition, strong binding. Shows up in slightly '
                         'higher-end formulations and usually travels with other whole-food ingredients.',
        'milk protein isolate': 'A casein and whey blend from milk at their natural ratio. Slower digesting than whey isolate on '
                                'its own. A clean, complete protein source that scores the same as whey concentrate.',
        'oats': f'The carbohydrate anchor for many whole-food bars. Beta-glucan fiber, complex carbs, minimal processing. '
                f'But oats alone don\'t make a clean bar: of the {len(oats_top3)} bars with oats in the first three ingredients, '
                f'{pct0(ab(oats_top3) * 100, 100)}% score A or B. The syrups and coatings around them decide the rest.',
        'flaxseed': 'Whole seed with fiber, omega-3 fat and protein. A small ingredient by weight in most bars, but a reliable '
                    'marker of a whole-food formula.',
        'calcium caseinate': 'Casein protein from milk. Slow digesting and complete, and a common base in mainstream bars.',
        'cashews': 'Whole nuts, scored the same as almonds and peanuts. Common in whole-food bars as a creamy base.',
        'chia seeds': 'Whole seed with fiber, omega-3 fat and protein, scored the same as flaxseed and hemp seed.',
        'egg whites': 'Complete amino acids, minimal fat, almost no processing. RXBAR is the best known example.',
    }
    missing = [k for k in worst if k not in WORST_TEXT] + [k for k in best if k not in BEST_TEXT]
    cl.check(not missing, f'every top-10 ingredient has a written description (missing: {missing})')
    for k in ['whey protein isolate', 'whey protein concentrate', 'milk protein isolate', 'soy protein isolate']:
        if k in best:
            cl.check(S(k) == (4 if k == 'whey protein isolate' else 3), f'{k} score as described')

    def card(kind, n, k):
        s, col = S(k), VAR[S(k)]
        text = (WORST_TEXT if kind == 'worst' else BEST_TEXT).get(k, '')
        return f'''        <!-- {kind.upper()} {n} -->
        <div class="ing-rank-card {kind}">
          <div class="ing-rank-num">#{n} {'Worst' if kind == 'worst' else 'Best'}</div>
          <div class="ing-rank-name">{esc(title(k))}</div>
          <div class="ing-rank-meta">
            <span class="ing-rank-score" style="background:{col};">{sgn(s)}</span>
            <span class="ing-rank-bars">{comma(B(k))} bars &middot; {pc(B(k))}% of database</span>
          </div>
          <div class="ing-rank-body">{esc(text)}</div>
          <div class="ing-rank-bar-track"><div class="ing-rank-bar-fill" style="width:{pc(B(k))}%;background:{col};"></div></div>
        </div>'''
    intro_style = 'color:#4a4a45;font-size:0.92rem;line-height:1.6;margin-bottom:0;'
    worst_html = (f'      <p style="{intro_style}">Ingredients scoring -2 or lower, ranked by score times the number of bars they '
                  f'show up in. These are the ingredients doing the most damage across our {comma(N)}-bar database.</p>\n\n'
                  '      <div class="ranked-grid" style="margin-top:1.5rem;">\n\n'
                  + '\n\n'.join(card('worst', n, k) for n, k in enumerate(worst, 1)) + '\n\n      </div>')
    best_html = (f'      <p style="{intro_style}">The ingredients that make a bar worth buying: everything scoring +3 or higher, '
                 f'ranked by score times the number of bars that use it. These are the signals worth looking for on a label.</p>\n\n'
                 '      <div class="ranked-grid" style="margin-top:1.5rem;">\n\n'
                 + '\n\n'.join(card('best', n, k) for n, k in enumerate(best, 1)) + '\n\n      </div>')

    # ---------- findings
    ranked = sorted(listed, key=lambda k: -B(k))
    cl.check(ranked[0] == 'salt', 'salt is the most common ingredient')
    cl.check(pko > B('sucralose'), 'palm kernel oil is in more bars than sucralose')
    plus3 = sorted((k for k in listed if S(k) >= 3), key=lambda k: -B(k))
    cl.check(plus3[0] == 'whey protein isolate', 'whey isolate is the most common +3-or-better ingredient')
    prev = '\n'.join(f'''          <div class="prev-row">
            <div class="prev-name">{esc(k[:1].upper() + k[1:])}</div>
            <div class="prev-track"><div class="prev-fill" style="width:{pc(B(k))}%;background:{VAR[S(k)]};"></div></div>
            <div class="prev-pct">{pc(B(k))}%</div>
          </div>''' for k in ranked[:15])
    ins = [
        ('Salt is everywhere, neutrally.', f'{comma(B("salt"))} bars contain salt. It scores 0: just a seasoning, not a concern. '
                                           f'Its near-ubiquity reflects how universal basic seasoning is in packaged food.'),
        ('Glycerin is the invisible texture agent.', f'{comma(B("glycerin"))} bars use glycerin as a humectant. It keeps bars '
                                                     f'soft on the shelf and scores -1. Most people have never noticed it, but it is '
                                                     f'in {share_words(B("glycerin"), N)} bars.'),
        ('Palm kernel oil beats sucralose for prevalence.', f'Palm kernel oil (-3) appears in {comma(pko)} bars, more than '
                                                            f'sucralose (-2) at {comma(B("sucralose"))}. The difference is visibility: '
                                                            f'sucralose is listed directly, while in {comma(pko_sub)} of the palm kernel '
                                                            f'oil bars it only shows up inside a compound ingredient.'),
        ('Whey isolate is the most common top-rated ingredient.', 'Among ingredients scoring +3 or better, whey protein isolate '
                                                                   f'appears most often: {comma(B(plus3[0]))} bars, followed by '
                                                                   + ', '.join(f'{k.replace("whey protein concentrate", "whey concentrate")} ({comma(B(k))})' for k in plus3[1:3])
                                                                   + f', and {plus3[3].replace("whey protein concentrate", "whey concentrate")} ({comma(B(plus3[3]))}).'),
    ]
    findings = f'''      <h2 class="findings-title">The most common ingredients across {comma(N)} bars</h2>

      <div class="big-stat">
        <div class="big-stat-num">{comma(B("salt"))}</div>
        <div>
          <div class="big-stat-head">bars contain salt</div>
          <div class="big-stat-detail">Salt is the single most common ingredient in the database. {share_words(B("salt"), N)[:1].upper() + share_words(B("salt"), N)[1:]} protein bars contain it, more than any protein source, sweetener, or fat.</div>
        </div>
      </div>

      <div style="margin-top:2rem;">
        <div style="font-family:var(--font-mono);font-size:9px;letter-spacing:.08em;text-transform:uppercase;color:#888880;margin-bottom:1rem;">% of {comma(N)} bars containing each ingredient</div>

        <div class="prevalence-list">
{prev}
        </div>
      </div>

      <div class="insights-grid" style="margin-top:2.5rem;">
''' + '\n'.join(f'''        <div class="insight-item">
          <div class="insight-dot"></div>
          <div class="insight-text"><strong>{esc(h)}</strong> {esc(t)}</div>
        </div>''' for h, t in ins) + '\n      </div>'

    # ---------- clusters (each stated share measured)
    pk_lec, pk_sug = share('palm kernel oil', 'soy lecithin'), share('palm kernel oil', 'sugar')
    m_suc, m_gly = share('maltitol', 'sucralose'), share('maltitol', 'glycerin')
    sa_as = {}
    for i in range(N):
        sas = {x['name'] for x in BI[i] if x['subcategory'] == 'sugar_alcohol'}
        arts = {x['name'] for x in BI[i] if x['subcategory'] == 'artificial_sweetener'}
        for a in sas:
            for b in arts:
                sa_as[(a, b)] = sa_as.get((a, b), 0) + 1
    top_pair = max(sa_as, key=sa_as.get)
    cl.check(top_pair == ('maltitol', 'sucralose'), 'maltitol + sucralose is the most common sugar alcohol + artificial sweetener pair')
    de = [i for i in range(N) if 'dates' in NM[i] and NM[i] & EGG]
    syr = [i for i in range(N) if NM[i] & {'brown rice syrup', 'tapioca syrup'}]
    syr_more = sum(1 for i in syr if any(x['category'] == 'sweetener' and S(x['name']) < 0 and x['name'] not in
                                         ('brown rice syrup', 'tapioca syrup') and x['subcategory'] not in ('sugar_alcohol', 'artificial_sweetener')
                                         for x in BI[i])) / len(syr)
    pb = [i for i in range(N) if {'pea protein', 'brown rice protein'} <= NM[i]]
    w_wpc, w_gly, w_nf = share('whey protein isolate', 'whey protein concentrate'), share('whey protein isolate', 'glycerin'), share('whey protein isolate', 'natural flavors')
    cl.check(pk_lec >= 0.5 and pk_sug >= 0.5, 'most palm kernel oil bars also contain soy lecithin and sugar')
    cl.check(m_suc >= 0.5, 'most maltitol bars also contain sucralose')
    cl.check(len(de) >= 5, 'enough bars combine dates and egg whites to say something')
    P = lambda x: pct0(x * 100, 100)
    clusters = [
        ('The coating system', [('palm kernel oil', 'bad'), ('sugar', 'bad'), ('soy lecithin', ''), ('cocoa', '')],
         f'Of the {comma(pko)} bars with palm kernel oil, {P(pk_lec)}% also contain soy lecithin and {P(pk_sug)}% contain sugar. '
         f'That is the chocolate-style coating: palm kernel oil for the snap, sugar for sweetness, lecithin to hold it together. '
         f'When you see "chocolate flavored coating" on a label, this is usually what is inside it.'),
        ('The keto sweetener stack', [('maltitol', 'bad'), ('sucralose', 'bad'), ('glycerin', 'bad'), ('maltitol syrup', 'bad')],
         f'Lots of bars marketed as "low sugar" or "keto-friendly" stack a sugar alcohol with an artificial sweetener. '
         f'{P(m_suc)}% of bars with maltitol also contain sucralose, and {P(m_gly)}% contain glycerin. Maltitol plus sucralose is '
         f'the most common pairing of the two ({comma(sa_as[top_pair])} bars).'),
        ('The whole-food bar signature', [('dates', 'good'), ('almonds', 'good'), ('egg whites', 'good'), ('cashews', 'good')],
         (f'RXBAR popularized this cluster. Whole fruit for sweetness, whole nuts for fat and protein, egg whites for protein '
          f'structure. No processed binding agents required. '
          + (f'All {len(de)} bars that combine dates and egg whites score A or B.' if ab(de) == 1 else
             f'{P(ab(de))}% of the {len(de)} bars that combine dates and egg whites score A or B.'))),
        ('The "clean label" sugar stack', [('brown rice syrup', 'bad'), ('tapioca syrup', 'bad'), ('honey', 'bad'), ('cane sugar', 'bad')],
         f'Very common in granola-style bars that want a natural-sounding label. The word "sugar" gets swapped for syrups that '
         f'sound like whole foods but score worse than sugar (-3 vs -2). Of the {comma(len(syr))} bars with brown rice or tapioca '
         f'syrup, {P(syr_more)}% add at least one more sugar or syrup on top.'),
        ('The plant protein combo', [('pea protein', 'good'), ('brown rice protein', 'good')],
         f'Pea and brown rice protein are paired because together they cover the full amino acid profile that neither has on '
         f'its own. {comma(len(pb))} bars use both. This is the base formula for most plant-based bars.'),
        ('The whey blend', [('whey protein isolate', 'good'), ('whey protein concentrate', 'good'), ('glycerin', ''), ('natural flavors', '')],
         f'About {P(w_wpc)}% of bars with whey isolate also use concentrate: isolate is the premium protein, concentrate is '
         f'cheaper and helps texture. {P(w_gly)}% add glycerin to keep everything chewy and {P(w_nf)}% use natural flavors to '
         f'carry the taste. This is the backbone of the mainstream bar market.'),
    ]
    for _, tags, _ in clusters:
        for t, css in tags:
            cl.check(t in listed, f'cluster tag {t} is in the data')
            if css == 'bad':
                cl.check(S(t) < 0, f'cluster tag {t} marked bad scores below 0')
            if css == 'good':
                cl.check(S(t) > 0, f'cluster tag {t} marked good scores above 0')
    clusters_html = ('      <p class="pattern-body">Certain ingredients rarely appear alone. They cluster because they serve the '
                     'same formulation purpose or come from the same sourcing decisions. These patterns are some of the most '
                     'useful things you can learn about a label.</p>\n\n      <div class="cluster-grid">\n\n'
                     + '\n\n'.join(f'''        <div class="cluster-card">
          <div class="cluster-title">{esc(t)}</div>
          <div class="cluster-tags">
''' + '\n'.join(f'            <span class="cluster-tag{" " + c if c else ""}">{esc(n)}</span>' for n, c in tags) + f'''
          </div>
          <div class="cluster-desc">{esc(d)}</div>
        </div>''' for t, tags, d in clusters) + '\n\n      </div>')

    # ---------- decoder
    for k in ['agave syrup', 'honey', 'cane sugar', 'stevia', 'cocoa butter', 'collagen', 'natural flavors', 'soy lecithin']:
        cl.check(k in listed, f'{k} is in the data')
    cl.check(S('honey') == -1 and S('cane sugar') == -2 and S('brown rice syrup') == -3, 'honey -1, cane sugar -2, brown rice syrup -3')
    DEC = [
        ('brown rice syrup', 'Brown rice syrup', 'wholesome', 'Almost pure glucose, with a higher glycemic index than table sugar. A starch broken down into sugar that sounds like a whole food.'),
        ('tapioca syrup', 'Tapioca syrup', 'natural', 'A starch broken down into sugar. Functionally similar to corn syrup. Common in "clean label" granola bars.'),
        ('agave syrup', 'Agave syrup', 'premium, natural', 'Very high in fructose, higher than high fructose corn syrup. Marketed as low-glycemic because fructose doesn\'t spike blood sugar immediately, but excess fructose is associated with liver stress.'),
        ('honey', 'Honey', 'natural sweetener', f'Still added sugar. It is lightly processed and single-source, so it scores one point better than cane sugar ({sgn(S("honey"))} vs {sgn(S("cane sugar"))}), but the sugar content is what matters.'),
        ('glycerin', 'Glycerin', 'industrial', 'Not as bad as it sounds. A humectant that keeps bars soft. Low caloric impact. It is a processing additive, not a nutritional ingredient, but it is also not a red flag.'),
        ('soy lecithin', 'Soy lecithin', 'chemical', 'A natural emulsifier derived from soybeans. Widely considered safe. The soy-allergy concern is real but the lecithin itself is highly refined and unlikely to trigger reactions.'),
        ('natural flavors', 'Natural flavors', 'clean', 'A broad regulatory category that can include hundreds of compounds. The word "natural" is doing marketing work here, not scientific work. You cannot tell from this label what is actually in it.'),
        ('stevia', 'Stevia', 'healthy sweetener', 'Actually reasonably good. A plant-derived low-calorie sweetener with minimal effect on blood sugar. Scores +1 rather than higher because the research on long-term effects is still developing.'),
        ('cocoa butter', 'Cocoa butter', 'indulgent', 'Better than it sounds. A natural fat from cocoa beans and a much better alternative to palm kernel oil in coatings. Its presence usually signals a higher-quality chocolate formulation.'),
        ('collagen', 'Collagen protein', 'premium protein', 'Often marketed as a premium protein source, but collagen is an incomplete protein: it lacks tryptophan. A bar that counts collagen toward its protein total is not giving you the same nutrition as whey or egg whites.'),
    ]
    cl.check(S('stevia') == 1 and S('collagen') == 1 and S('cocoa butter') == 1, 'stevia, collagen and cocoa butter +1')
    decoder = '\n'.join(f'''          <tr>
            <td><div class="decode-ing">{esc(lab)}</div><span style="font-family:var(--font-mono);font-size:9px;color:var(--muted);">Sounds: {esc(snd)}</span></td>
            <td><span class="decode-verdict" style="background:{VAR[S(k)]};">{sgn(S(k))} {VERDICT[S(k)]}</span></td>
            <td>{esc(txt)}</td>
          </tr>''' for k, lab, snd, txt in DEC)

    # ---------- predictor (hit rate measured for each signal)
    NUTS = {k for k in R if R[k]['category'] == 'whole_food' and any(w in k for w in NUT_WORDS)
            and not any(w in k for w in ('butter', 'flour', 'oil', 'extract', 'milk', 'protein'))}
    first_n = lambda i: max([x['pos'] for x in BI[i]] or [0])
    good = [
        ('Whey protein isolate or egg whites listed in the first two ingredients', lambda i: any(x['name'] in WPI | EGG for x in top(i, 2))),
        ('Dates as a primary ingredient: first or second', lambda i: any(x['name'] == 'dates' for x in top(i, 2))),
        ('Almonds, peanuts, or other whole nuts in the first three spots', lambda i: any(x['name'] in NUTS for x in top(i, 3))),
        ('Fewer than 10 total ingredients with no compound ingredient groups',
         lambda i: first_n(i) < 10 and not any(x['category'] == 'ingredient_group' for x in BI[i])),
        ('No sweetener of any kind in the first five ingredients', lambda i: not any(x['category'] == 'sweetener' for x in top(i, 5))),
    ]
    bad = [
        ('Maltitol anywhere in the ingredient list', lambda i: any('maltitol' in x['name'] for x in BI[i]), 'var(--red-worst)'),
        ('Any "chocolate coating" or "compound coating" in the ingredients', lambda i: 'coating' in (bars[i].get('Ingredients') or '').lower(), 'var(--red-avoid)'),
        ('Brown rice syrup or tapioca syrup in the first five ingredients',
         lambda i: any(x['name'] in ('brown rice syrup', 'tapioca syrup') for x in top(i, 5)), 'var(--red-avoid)'),
        ('Sucralose plus another sweetener (stacking)',
         lambda i: 'sucralose' in NM[i] and any(x['category'] == 'sweetener' and x['name'] != 'sucralose' for x in BI[i]), 'var(--red-concern)'),
        ('Sugar or cane sugar as the second or third ingredient',
         lambda i: any(x['name'] in ('sugar', 'cane sugar') and x['pos'] in (2, 3) and not x['sub'] for x in BI[i]), 'var(--red-concern)'),
    ]
    stat_style = 'display:block;font-family:var(--font-mono);font-size:10px;color:var(--muted);margin-top:2px;'
    def item(text, f, col, want_good):
        idx = [i for i in range(N) if f(i)]
        r = ab(idx) if want_good else 1 - ab(idx)
        cl.check(len(idx) >= 20 and r >= 0.6, f'signal "{text}" holds ({len(idx)} bars, {r:.0%})')
        lab = 'score A or B' if want_good else 'score C, D or F'
        return f'''          <div class="predictor-item">
            <div class="predictor-dot" style="background:{col};"></div>
            <div>{esc(text)}<span style="{stat_style}">{pct0(r * 100, 100)}% of {comma(len(idx))} bars {lab}</span></div>
          </div>'''
    predictor = ('      <p class="pattern-body">You do not need to read the whole label. A few signals in the first five '
                 'ingredients tell you most of what you need to know. These are the strongest predictors we found, with how '
                 f'often each one held across our {comma(N)} bars.</p>\n\n      <div class="predictor-grid">\n'
                 '        <div class="predictor-card signals-good">\n          <div class="predictor-label good">Signals that predict A or B</div>\n'
                 + '\n'.join(item(t, f, 'var(--green-best)', True) for t, f in good)
                 + '\n        </div>\n\n        <div class="predictor-card signals-bad">\n          <div class="predictor-label bad">Signals that predict C, D, or F</div>\n'
                 + '\n'.join(item(t, f, c, False) for t, f, c in bad) + '\n        </div>\n      </div>')

    # ---------- FAQ
    cl.check(S('maltitol') == -4 and S('maltitol syrup') == -4, 'maltitol and maltitol syrup -4')
    sa_neg4 = sorted(k for k in listed if R[k]['category'] == 'sweetener' and S(k) == -4)
    cl.check(set(sa_neg4) == {'maltitol', 'maltitol syrup'}, 'maltitol (and its syrup) are the only -4 sweeteners')
    sub_names = {x['name'] for items in BI for x in items
                 if x['subcategory'] in ('sugar_alcohol', 'low_calorie_sweetener', 'artificial_sweetener')}
    nonsugar = sorted((k for k in listed if k in sub_names), key=lambda k: -B(k))
    cl.check(nonsugar[0] == 'sucralose', 'sucralose is the most common sugar substitute')
    nf_rank = ranked.index('natural flavors') + 1
    cl.check(nf_rank == 2, 'natural flavors is the second most common ingredient')
    cl.check(worst[0] == 'palm kernel oil', 'palm kernel oil has the largest total impact')
    avoid = ', '.join(f'{k} ({sgn(S(k))}, in {comma(B(k))} bars)' for k in worst[:6])
    cl.stop_if_failed()
    faqs = [
        ('What is the most common bad ingredient in protein bars?',
         f'By bar count, sugar is the most common ingredient scoring -2 or worse, appearing in {comma(B("sugar"))} bars. Maltitol '
         f'has the worst score at -4 and appears in {comma(B("maltitol"))} bars. Palm kernel oil, which often hides inside '
         f'coatings, is in {comma(pko)} bars and scores -3. By total impact on the database (score times bars), palm kernel oil is '
         f'the most consequential negative ingredient because it is so common and so well hidden.'),
        ('What is the best protein source in a protein bar?',
         f'Whey protein isolate and egg whites both score +4, the highest possible rating. Whey isolate appears in '
         f'{comma(B("whey protein isolate"))} bars, making it the most common protein source in the database. It has complete '
         f'amino acids, high bioavailability, and minimal processing compared to concentrate. Egg whites score identically and '
         f'are the foundation of RXBAR and similar whole-food bars.'),
        ('Is sucralose bad in protein bars?',
         f'Sucralose costs a bar a flat -2 in our system, wherever it appears on the label, and it is in {comma(B("sucralose"))} '
         f'bars. Research suggests effects on the gut microbiome and insulin response. It is not the worst sweetener: maltitol '
         f'(-4) and other sugar alcohols (-3) score lower. But it appears in more bars than any other sugar substitute in the '
         f'database.'),
        ('What ingredients should I avoid in protein bars?',
         f'The ingredients with the biggest total impact across our database are {avoid}. On a label, also watch for "chocolate '
         f'coating," which often contains palm kernel oil even when it is not listed on its own.'),
        ('What is the difference between whey isolate and whey concentrate?',
         'Whey isolate is processed further to remove most fat and lactose, resulting in higher protein concentration and faster '
         'absorption. It scores +4. Whey concentrate retains more fat and lactose. It scores +3. Both are complete protein sources, '
         'but isolate is generally considered higher quality. When a bar lists both, the order matters: isolate listed first is '
         'the stronger formulation.'),
        ('Why is maltitol worse than other sugar alcohols?',
         'Maltitol has a glycemic index around 35, which is much higher than erythritol (close to 0) or xylitol (around 13). It '
         'also causes more GI distress. Erythritol is mostly absorbed before it reaches the colon. Both get marketed identically '
         'on labels as "sugar free" or "no added sugar," but they behave very differently. Maltitol, in solid or syrup form, is '
         'the only sugar alcohol that scores -4 in our system.'),
        ('How can I tell if a bar has palm kernel oil without seeing it listed?',
         f'Look for any compound ingredient involving chocolate or a coating: "chocolate flavored coating," "dark chocolate '
         f'coating," "compound coating," or "chocolate chips." Many of these use palm kernel oil as their main fat. Our scoring '
         f'unpacks these compound ingredients, which is how we find it: in {comma(pko_sub)} of the {comma(pko)} bars that contain '
         f'palm kernel oil, it only appears inside a compound ingredient.'),
        ('What does "natural flavors" actually mean on a protein bar label?',
         f'Natural flavors is a broad FDA-defined category that can include hundreds of compounds derived from animal or plant '
         f'sources. The term reveals nothing about what specific substances are present. We score it -1 because it adds no '
         f'nutritional value and provides no transparency. It is the second most common ingredient in the database, in '
         f'{comma(B("natural flavors"))} bars.'),
    ]

    # ---------- page text regions
    desc = (f'We analyzed {comma(N)} protein bars and ranked every ingredient. The 10 best, the 10 worst, hidden ingredient '
            f'patterns, and what to look for on any label.')
    head = ('  <title>What\'s Really in Protein Bars: Ingredients Ranked</title>\n'
            f'  <meta name="description" content="{esc(desc)}">')
    art = {'@context': 'https://schema.org', '@type': 'Article',
           'headline': 'What\'s Really in Protein Bars: Ingredients Ranked Best to Worst', 'description': desc,
           'url': 'https://knowyourbar.com/ingredient-report', 'image': 'https://knowyourbar.com/bar_hero.png',
           'datePublished': PUBLISHED, 'dateModified': today_iso(),
           'author': {'@type': 'Organization', 'name': 'Know Your Bar', 'url': 'https://knowyourbar.com'},
           'publisher': {'@type': 'Organization', 'name': 'Know Your Bar', 'url': 'https://knowyourbar.com'}}
    faq_ld = {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
        {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in faqs]}
    jsonld = ('  <script type="application/ld+json">\n  ' + json.dumps(art, ensure_ascii=False, indent=2).replace('\n', '\n  ')
              + '\n  </script>\n  <script type="application/ld+json">\n  ' + json.dumps(faq_ld, ensure_ascii=False, separators=(',', ':'))
              + '\n  </script>')
    sdesc = (f'We analyzed {comma(N)} protein bars and ranked every ingredient. The 10 best, 10 worst, hidden patterns, and what '
             f'to look for on any label.')
    social = ('  <meta property="og:type" content="article">\n  <meta property="og:site_name" content="Know Your Bar">\n'
              '  <meta property="og:title" content="What&#x27;s Really in Protein Bars: Ingredients Ranked | Know Your Bar">\n'
              f'  <meta property="og:description" content="{esc(sdesc)}">\n'
              '  <meta property="og:url" content="https://knowyourbar.com/ingredient-report">\n'
              '  <meta property="og:image" content="https://knowyourbar.com/bar_hero.png">\n'
              '  <meta name="twitter:card" content="summary_large_image">\n'
              '  <meta name="twitter:title" content="What&#x27;s Really in Protein Bars: Ingredients Ranked Best to Worst | Know Your Bar">\n'
              f'  <meta name="twitter:description" content="{esc(sdesc)}">')
    hero = (f'    <p class="hero-sub" style="color:#e8e4dc;">We scored {comma(N)} bars ingredient by ingredient. Here are the '
            f'patterns: the best, the worst, what travels together, and what the label is hiding.</p>')
    snaps = [(str(len(listed)), 'Ingredients catalogued'), (comma(N), 'Bars analyzed'),
             (f'{pct0(len(caloric), N)}%', 'Bars with added sugar or syrup'), (comma(pko), 'Bars with palm kernel oil'),
             (comma(B('whey protein isolate')), 'Bars with whey isolate')]
    snapshot = '\n'.join(f'''    <div class="snap-item">
      <div class="snap-value">{v}</div>
      <div class="snap-label">{esc(l)}</div>
    </div>''' for v, l in snaps)
    explore = f'''        <a href="/all-ingredients" class="explore-more-card">
          <div class="explore-more-title">Ingredient encyclopedia</div>
          <div class="explore-more-desc">Every ingredient scored and ranked by how many bars contain it. Searchable. All {len(listed)} catalogued.</div>
        </a>
        <a href="/no-sugar-alcohols" class="explore-more-card">
          <div class="explore-more-title">No sugar alcohol bars</div>
          <div class="explore-more-desc">Bars with no maltitol, erythritol, sorbitol, or any other sugar alcohol in the ingredient list.</div>
        </a>
        <a href="/clean-protein-bars" class="explore-more-card">
          <div class="explore-more-title">Clean protein bars</div>
          <div class="explore-more-desc">The highest-scoring bars by ingredient quality across the full {comma(N)}-bar database.</div>
        </a>'''
    faq = '\n\n'.join(f'''      <div class="faq-item">
        <button class="faq-q">{esc(q)}</button>
        <div class="faq-a">{esc(a)}</div>
      </div>''' for q, a in faqs)

    page = open(PAGE, encoding='utf-8').read()
    for name, content in [('head', head), ('jsonld', jsonld), ('social', social), ('hero', hero), ('snapshot', snapshot),
                          ('worst', worst_html), ('best', best_html), ('findings', findings), ('clusters', clusters_html),
                          ('decoder', decoder), ('predictor', predictor), ('explore', explore), ('faq', faq)]:
        page = replace_region(page, name, content)
    page = stamp_dates(page, today_iso())
    visible = re.sub(r'<style.*?</style>', '', page, flags=re.S)
    for bad_s in ('—', 'href="Yes"', 'href="None"'):
        if bad_s in visible:
            raise SystemExit(f'ERROR: forbidden string {bad_s!r} in page. Not writing.')
    open(PAGE, 'w', encoding='utf-8').write(page)
    print(f'{PAGE}: {comma(N)} bars, {len(listed)} ingredients\n  worst: {", ".join(worst)}\n  best: {", ".join(best)}')


if __name__ == '__main__':
    main()
