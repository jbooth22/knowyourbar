"""Rebuild the homepage (index.html) from bars.js.

Opens the LIVE page and rewrites only the <!-- kyb:NAME --> regions:
  meta, social, jsonld   meta/og/twitter descriptions; FAQPage, WebSite,
                         Organization and Dataset JSON-LD
  hero-sub, finder-heading   bar and brand counts
  goals                  goal cards (criteria copied from the guide filters and
                         Bar Finder presets they link to)
  top-bars               featured A-rated bar cards
  grades, highlights     grade distribution box and "what moves the grade"
  stats                  dark-band stats
  faq                    visible FAQ (JSON-LD FAQ is built from the same list)
The personal intro story, nav, footer and styles are kept as-is.

Featured bars: FEATURED lists the bars to show (editorial, e.g. referral
partners). A featured bar is only shown while bars.js grades it A. If it
isn't A any more, the same brand's highest-scoring A flavor takes its place;
if the brand has none, the highest-scoring A bar from another referral
partner brand does. Cards are ordered by ingredient score.

Run: python3 build_index.py
"""
import json, re
from collections import defaultdict
import pandas as pd
from kyb_guide_lib import (load_bars, num, has_tag, score, esc, comma, replace_region, stamp_dates, today_iso,
                           Claims, GUIDE_FILTERS, P, CAL, grade_word, amazon_url, website_url, names_and)

PAGE = 'index.html'
SCHEMA = 'knowyourbar_scoring_schema_v12.xlsx'
FEATURED = [('Off the Farm', 'Peanut Butter and Jelly'), ('Gryp', 'Rocky Road and Sea Salt'),
            ('B.T.R. Nation', 'Peanut Butter Crunch')]
GCOL = {'A': '#2a7a1f', 'B': '#5a8a2f', 'C': '#b89a00', 'D': '#c87020', 'F': '#c83020'}


def title_words(s):
    return ' '.join(w[:1].upper() + w[1:] for w in s.split())


def main():
    bars = load_bars()
    N = len(bars)
    by = defaultdict(list)
    for b in bars:
        by[b['Brand Name'].strip()].append(b)
    NB = len(by)
    G = {g: sum(1 for b in bars if b.get('score_band') == g) for g in 'ABCDF'}
    n_canon = len(pd.read_excel(SCHEMA, 'Canonical_Ingredients'))
    cnt = lambda slug: sum(1 for b in bars if GUIDE_FILTERS[slug](b))
    cl = Claims()
    PO = lambda b: has_tag(b, 'Processed Oils')
    AS = lambda b: has_tag(b, 'Artificial Sweeteners')
    AB = lambda bs: all(b['score_band'] in ('A', 'B') for b in bs)

    # ---------- featured bars
    partner = lambda b: b.get('Custom Referral Link') == 'Yes' or bool(amazon_url(b))
    picks = []
    for brand, flavor in FEATURED:
        b = next((x for x in bars if x['Brand Name'] == brand and x['Flavor Name'] == flavor), None)
        if not b or b['score_band'] != 'A':
            b = max((x for x in by.get(brand, []) if x['score_band'] == 'A' and partner(x)), key=score, default=None)
            if b:
                print(f'NOTE: featured {brand} {flavor} is no longer A; showing {brand} {b["Flavor Name"]} ({score(b):.1f}) instead')
        if not b:
            used = {p['Brand Name'] for p in picks} | {f[0] for f in FEATURED}
            b = max((x for x in bars if x['score_band'] == 'A' and x.get('Custom Referral Link') == 'Yes'
                     and x['Brand Name'] not in used), key=score)
            print(f'NOTE: featured {brand} has no A flavor; showing {b["Brand Name"]} {b["Flavor Name"]} instead')
        picks.append(b)
    picks.sort(key=lambda b: -score(b))

    def chips(b):
        pos = [p.strip() for p in (b.get('positive_ingredients') or '').split(',') if p.strip()]
        neg = list(dict.fromkeys(p.strip() for p in (b.get('concern_ingredients') or '').split(',') if p.strip()))
        items = [(p, 'pos') for p in pos[:2]] + ([(neg[-1], 'con')] if neg else [(p, 'pos') for p in pos[2:3]])
        return '\n'.join(f'          <span class="top-bar-chip {c}">{esc(title_words(t))}</span>' for t, c in items)

    def card(n, b):
        az, ws = amazon_url(b), website_url(b)
        buy = ''
        if az:
            buy += f'\n          <a href="{esc(az)}" target="_blank" rel="noopener sponsored" class="buy-amazon">Buy on Amazon</a>'
        if ws:
            buy += f'\n          <a href="{esc(ws)}" target="_blank" rel="noopener sponsored" class="buy-site">Buy from Brand</a>'
        f = lambda k: f'{num(b.get(k)):g}' if num(b.get(k)) is not None else '-'
        return f'''      <div class="top-bar-card">
        <div class="top-bar-rank">No. {n}</div>
        <div class="top-bar-header">
          <div class="top-bar-badge">{b['score_band']}</div>
          <div class="top-bar-title">
            <div class="top-bar-name">{esc(b['Flavor Name'])}</div>
            <div class="top-bar-brand">{esc(b['Brand Name'])}</div>
          </div>
          <div class="top-bar-score">
            <div class="top-bar-score-val">{score(b):.1f}</div>
            <div class="top-bar-score-lbl">Score</div>
          </div>
        </div>
        <div class="top-bar-chips">
{chips(b)}
        </div>
        <div class="top-bar-macros">
          <div class="top-bar-macro"><span class="top-bar-macro-val">{f('Protein (g)')}g</span><span class="top-bar-macro-lbl">Protein</span></div>
          <div class="top-bar-macro"><span class="top-bar-macro-val">{f('Calories')}</span><span class="top-bar-macro-lbl">Calories</span></div>
          <div class="top-bar-macro"><span class="top-bar-macro-val">{f('Sugars (g)')}g</span><span class="top-bar-macro-lbl">Sugar</span></div>
          <div class="top-bar-macro"><span class="top-bar-macro-val">{f('Dietary Fiber (g)')}g</span><span class="top-bar-macro-lbl">Fiber</span></div>
        </div>
        <div class="top-bar-buy">{buy}
        </div>
      </div>'''
    for b in picks:
        cl.check(b['score_band'] == 'A', f'featured {b["Brand Name"]} {b["Flavor Name"]} is A')
    top_bars = ('    <div class="top-bars-grid">\n\n' + '\n\n'.join(card(n, b) for n, b in enumerate(picks, 1))
                + f'\n\n    </div>\n    <div class="top-bars-caption">Ordered by ingredient score. '
                  f'<a href="/bar-finder?grade=A">See all {comma(G["A"])} A-rated bars &rarr;</a></div>')

    # ---------- goal cards (criteria match the page or preset each card opens)
    goals = [
        ('/bar-finder?preset=lose_weight', 'Lose weight', '20g+ protein, under 200 calories, 3g sugar or less, grade A or B'),
        ('/clean-protein-bars', 'Clean ingredients', 'Grade A or B, no artificial sweeteners, no processed oils'),
        ('/bar-finder?preset=skip_sugar', 'Skip the sugar', 'Under 2g sugar, no maltitol or sorbitol, grade A or B'),
        ('/no-artificial-sweeteners', 'No artificial sweeteners', 'Sucralose, ace-K, and the rest, filtered out entirely'),
        ('/no-seed-oils', 'No seed oils', 'No canola, soybean, sunflower, palm, or other processed oils'),
        ('/keto-protein-bars', 'Keto friendly', '8g or less net carbs, 10g+ protein, 8g+ fat, no maltitol'),
        ('/bar-finder?preset=high_protein', 'High protein', 'Ranked by protein per calorie, 15g+ protein, A&ndash;C grade'),
        ('/glp1-protein-bars', 'GLP-1 friendly', '15g+ protein, 200 calories or less, zero sugar alcohols, grade A or B'),
        ('/best-bars-for-diabetics', 'Diabetic-friendly', '5g or less sugar, 10g or less net carbs, 5g+ fiber, grade A or B'),
        ('/caffeine-protein-bars', 'Need a caffeine boost', 'Protein and caffeine in one bar'),
        ('/bar-finder?grade=A', 'Show me the best bars by ingredient quality', f'{comma(G["A"])} A-rated bars, ranked highest first, no filters needed'),
    ]
    goals_html = '\n'.join(f'''      <a href="{h}" class="goal-card">
        <div class="goal-card-name">{esc(n)}</div>
        <div class="goal-card-desc">{d}</div>
      </a>''' for h, n, d in goals)
    app = open('app.js', encoding='utf-8').read()
    for slug, must in [('lose_weight', 'prot >= 20 && cal <= 200 && sug <= 3'), ('skip_sugar', 'sug > 2'),
                       ('high_protein', 'prot >= 15')]:
        cl.check(must in app, f'Bar Finder preset {slug} still uses the criteria the card states')

    # ---------- grades box, highlights, stats
    grades = '\n'.join(f'        <div class="facts-row"><div class="facts-grade"><span class="facts-swatch" style="background:{GCOL[g]}"></span>'
                       f'{g} &middot; {grade_word(g)}</div><div class="facts-count">{comma(G[g])} bars &middot; '
                       f'<span class="facts-pct">{round(100 * G[g] / N)}%</span></div></div>' for g in 'ABCDF')
    highlights = '''          <div class="facts-highlight"><span class="facts-highlight-mark up">+</span><span class="facts-highlight-text">Whey isolate, nut butters, oats, and other whole-food proteins push a bar toward an A or B.</span></div>
          <div class="facts-highlight"><span class="facts-highlight-mark down">&minus;</span><span class="facts-highlight-text">Sugar alcohols, starch-based syrups, and processed oils drag it toward a D or F, especially near the top of the ingredient list. Each artificial sweetener costs a flat 2 points wherever it appears.</span></div>
          <div class="facts-highlight"><span class="facts-highlight-mark down">&minus;</span><span class="facts-highlight-text">A long list of isolates and gums with little else usually lands in the C range, technically fine, nothing to write home about.</span></div>'''
    stats = f'''      <div class="dark-stat"><div class="dark-stat-val">$0</div><div class="dark-stat-lbl">Sponsored picks</div></div>
      <div class="dark-stat"><div class="dark-stat-val">{comma(N)}</div><div class="dark-stat-lbl">Bars scored</div></div>
      <div class="dark-stat"><div class="dark-stat-val">{NB}</div><div class="dark-stat-lbl">Brands covered</div></div>
      <div class="dark-stat"><div class="dark-stat-val">{comma(n_canon)}</div><div class="dark-stat-lbl">Ingredients mapped</div></div>'''

    # ---------- FAQ (every brand list chosen by rule)
    big = {k: v for k, v in by.items() if len(v) >= 10}
    for k in ('RXBAR', 'Perfect Bar', 'Gryp'):
        cl.check(k in by and AB(by[k]), f'{k}: every flavor grades B or higher')
    clean_brands = sorted((k for k, v in big.items() if all(GUIDE_FILTERS['clean-protein-bars'](b) for b in v)), key=lambda k: (-len(by[k]), k))[:5]
    no_po = sorted((k for k, v in big.items() if not any(PO(b) for b in v)), key=lambda k: (-len(by[k]), k))[:5]
    no_as = sorted((k for k, v in by.items() if len(v) >= 15 and not any(AS(b) for b in v)), key=lambda k: (-len(by[k]), k))[:6]
    n_clean, n_nas = cnt('clean-protein-bars'), cnt('no-artificial-sweeteners')
    lw = sum(1 for b in bars if P(b) >= 20 and CAL(b) and CAL(b) <= 200 and num(b.get('Sugars (g)')) is not None
             and num(b['Sugars (g)']) <= 3 and b['score_band'] in ('A', 'B'))
    cl.stop_if_failed()
    faqs = [
        ('What is the healthiest protein bar?',
         'There is no single healthiest protein bar because it depends on your goals. RXBAR and Perfect Bar are the most consistent '
         'larger brands, every flavor in each lineup scores B or higher. A few smaller names do too, Gryp is one worth knowing before '
         'it shows up in stores. For pure ingredient quality with no artificial sweeteners or sugar alcohols, filter to '
         '<a href="/bar-finder?preset=clean">Grade A bars using the Protein Bar Finder</a>.'),
        ('What protein bar has the cleanest ingredients?',
         f'The cleanest protein bars score an A or B on ingredient quality and contain no artificial sweeteners and no processed oils. '
         f'{comma(n_clean)} of the {comma(N)} bars in our database meet that standard. Brands where every flavor qualifies include '
         f'{names_and(clean_brands)}. See the full <a href="/clean-protein-bars">Clean Protein Bars guide</a> for the ranked list.'),
        ('Are protein bars ultra-processed?',
         'Most protein bars qualify as ultra-processed foods under the NOVA classification system, meaning they contain industrial '
         'additives, isolates, or synthetic ingredients not found in home cooking. However, a meaningful minority use whole-food '
         'ingredients and minimal processing. Know Your Bar\'s ingredient scoring system identifies these bars: Grade A and B bars with '
         'short, recognizable ingredient lists represent the least-processed options in the category.'),
        ('Which protein bars have no seed oils?',
         f'Many protein bars contain canola, soybean, sunflower, or palm oil. {comma(cnt("no-seed-oils"))} of our {comma(N)} bars '
         f'contain none. Brands with no processed oils in any flavor include {names_and(no_po)}. Use the '
         f'<a href="/no-seed-oils">No Seed Oils guide</a> to see every qualifying bar.'),
        ('Are protein bars good for weight loss?',
         f'Protein bars can support weight loss when they are high in protein, moderate in calories, and low in added sugar, and when '
         f'they replace less nutritious snacks rather than adding calories on top of a full diet. Our '
         f'<a href="/bar-finder?preset=lose_weight">Lose Weight preset</a> in the Bar Finder shows bars with at least 20g of protein, '
         f'under 200 calories, 3g of sugar or less, and an A or B ingredient grade ({lw} bars today).'),
        ('How does Know Your Bar score protein bars?',
         'Every bar receives an A-F ingredient quality grade. Each ingredient is mapped to a quality score from +4 (excellent) to -4 '
         '(harmful), weighted by position in the ingredient list. Ingredients that appear earlier are present in larger quantities '
         'and contribute more to the final score. Artificial sweeteners are the exception: each one costs a flat 2 points wherever it '
         'appears. See the full methodology on our <a href="/ingredient_scoring">ingredient scoring page</a>.'),
        ('Which protein bars have no artificial sweeteners?',
         f'{round(100 * n_nas / N)}% of the bars in our database ({comma(n_nas)} of {comma(N)}) contain no artificial sweeteners. '
         f'Larger brands with none in any flavor include {names_and(no_as)}. See our '
         f'<a href="/no-artificial-sweeteners">No Artificial Sweeteners guide</a> for the ranked list.'),
        ('Are protein bars with sugar alcohols bad for you?',
         'Sugar alcohols like erythritol and maltitol are generally recognized as safe but can cause digestive discomfort in some '
         'people, particularly in larger amounts. Maltitol has a notably higher glycemic impact than other sugar alcohols, so it scores '
         '-4 while erythritol and the rest score -3, with severity depending on how prominently they appear in the ingredient list. '
         'See the <a href="/no-sugar-alcohols">No Sugar Alcohols guide</a> for the full ranked list, or filter the Bar Finder yourself.'),
    ]
    faq_html = '\n'.join(f'''    <div class="faq-item">
      <h3 class="faq-q">{esc(q)}</h3>
      <div class="faq-a"><p>{a}</p></div>
    </div>''' for q, a in faqs)
    plain = lambda h: re.sub(r'<[^>]+>', '', h)
    faq_ld = {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
        {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': plain(a)}} for q, a in faqs]}
    desc = f'Every protein bar scored A-F on ingredient quality. {comma(N)} bars ranked by macros, ingredients, and certifications. No sponsored picks.'
    website = {'@context': 'https://schema.org', '@type': 'WebSite', 'name': 'Know Your Bar', 'url': 'https://knowyourbar.com',
               'description': desc, 'potentialAction': {'@type': 'SearchAction', 'target': {'@type': 'EntryPoint',
               'urlTemplate': 'https://knowyourbar.com/bar-finder?q={search_term_string}'}, 'query-input': 'required name=search_term_string'}}
    org = {'@context': 'https://schema.org', '@type': 'Organization', 'name': 'Know Your Bar', 'url': 'https://knowyourbar.com',
           'logo': 'https://knowyourbar.com/bar_hero.png',
           'description': 'Independent protein bar rating site. Every bar scored A-F by ingredient quality. No sponsored picks, no affiliate rankings.',
           'sameAs': []}
    dataset = {'@context': 'https://schema.org', '@type': 'Dataset', 'name': 'Know Your Bar Protein Bar Ingredient Quality Database',
               'description': (f'{comma(N)} protein bars across {NB} brands scored A through F for ingredient quality. Each bar is parsed '
                               'ingredient by ingredient against a canonical scoring schema. Data includes macros, certifications, '
                               'ingredient scores, and insight chips for every bar.'),
               'url': 'https://knowyourbar.com', 'creator': {'@type': 'Organization', 'name': 'Know Your Bar', 'url': 'https://knowyourbar.com'},
               'dateModified': today_iso(), 'license': 'https://creativecommons.org/licenses/by-nc/4.0/',
               'variableMeasured': ['Ingredient quality grade (A through F)', 'Ingredient quality score', 'Macronutrients', 'Dietary certifications'],
               'measurementTechnique': 'Proprietary ingredient scoring algorithm mapping each ingredient to a canonical base score weighted by position in ingredient list',
               'spatialCoverage': 'United States', 'temporalCoverage': '2026'}
    ld = lambda o, c: (f'  <!-- JSON-LD: {c} -->\n' if c else '') + '  <script type="application/ld+json">\n  ' + \
        json.dumps(o, ensure_ascii=False, indent=2).replace('\n', '\n  ') + '\n  </script>'
    jsonld = '\n\n'.join([ld(faq_ld, ''), ld(website, 'WebSite + SearchAction'), ld(org, 'Organization'), ld(dataset, 'Dataset')])
    meta = f'  <meta name="description" content="{esc(desc)}">'
    social = f'''  <meta property="og:type" content="website">
  <meta property="og:site_name" content="Know Your Bar">
  <meta property="og:title" content="Protein Bar Reviews, Rankings &amp; Ingredient Scores">
  <meta property="og:description" content="Every protein bar scored A-F on ingredient quality. {comma(N)} bars. No sponsored picks. Find yours in 30 seconds.">
  <meta property="og:url" content="https://knowyourbar.com/">
  <meta property="og:image" content="https://knowyourbar.com/bar_hero.png">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="Protein Bar Reviews, Rankings &amp; Ingredient Scores">
  <meta name="twitter:description" content="Every protein bar scored A-F on ingredient quality. {comma(N)} bars. No sponsored picks.">'''
    hero = (f"    I've eaten a lot of protein bars, and it took me embarrassingly long to realize some hurt more than they helped: more "
            f"sugar and filler than actual protein. So I scored {comma(N)} bars, ingredient by ingredient, and graded each one A to F. "
            f"Never based on payment.")
    finder = f'    <h2 class="finder-hero-heading">Search {NB} brands and {comma(N)} bars to find one that works for you</h2>'

    page = open(PAGE, encoding='utf-8').read()
    for name, content in [('meta', meta), ('social', social), ('jsonld', jsonld), ('hero-sub', hero), ('finder-heading', finder),
                          ('goals', goals_html), ('top-bars', top_bars), ('grades', grades), ('highlights', highlights),
                          ('stats', stats), ('faq', faq_html)]:
        page = replace_region(page, name, content)
    page = stamp_dates(page, today_iso())
    visible = re.sub(r'<style.*?</style>|<!--.*?-->', '', page, flags=re.S)  # CSS and HTML comments on the live page use em dashes
    for bad in ('—', 'href="Yes"', 'href="None"'):
        if bad in visible:
            raise SystemExit(f'ERROR: forbidden string {bad!r} in page. Not writing.')
    open(PAGE, 'w', encoding='utf-8').write(page)
    print(f'{PAGE}: {comma(N)} bars, {NB} brands, A {G["A"]}; featured: ' + ', '.join(f'{b["Brand Name"]} {b["Flavor Name"]} ({score(b):.1f})' for b in picks))


if __name__ == '__main__':
    main()
