"""Rebuild the ingredient encyclopedia (all-ingredients.html) from bars.js
and the scoring schema.

Opens the LIVE page and rewrites only the <!-- kyb:NAME --> regions:
  head, jsonld, social   title, meta description, Article + FAQPage JSON-LD, og/twitter
  hero                   hero sub-line and stat cards
  cat-nav                category jump links
  sections               every category section and ingredient row
  cta-sub, report-card   bar counts in the two CTAs
  faq                    visible FAQ (JSON-LD FAQ is built from the same list)
Nav, footer, search script and styles are kept as-is.

Rows: every schema ingredient that appears in MIN_BARS or more bars
(kyb_ingredients.ingredient_counts: counted anywhere on the label, matched
exactly the way the scorer matches). Badge = schema base score, bar/percent =
share of all bars in bars.js, description = schema explanation. Sorted by
bar count within each category.

Section blurbs and FAQ answers are checked against the data; the build stops
and lists any claim that no longer holds.

Run: python3 build_all_ingredients.py
"""
import json, re
from kyb_guide_lib import (esc, comma, replace_region, stamp_dates, today_iso, Claims, names_and, pct0)
from kyb_ingredients import ingredient_counts, alias_score_conflicts, NOT_INGREDIENTS, INTERNAL

PAGE = 'all-ingredients.html'
MIN_BARS = 5
PUBLISHED = '2026-05-01'

CATS = [('protein', 'Protein Sources'), ('sweetener', 'Sweeteners'), ('whole_food', 'Whole Foods'),
        ('fat_oil', 'Fats & Oils'), ('cocoa_chocolate', 'Cocoa & Chocolate'),
        ('fiber_or_functional_carb', 'Fibers & Functional Carbs'), ('starch_flour', 'Starches & Flours'),
        ('additive', 'Additives'), ('emulsifier', 'Emulsifiers'), ('flavor_additive', 'Flavorings'),
        ('seasoning', 'Seasonings'), ('vitamin_mineral', 'Vitamins & Minerals'),
        ('acid_or_preservative', 'Acids & Preservatives'), ('color_additive', 'Color Additives'),
        ('botanical_or_functional', 'Botanicals & Functional'), ('other_food', 'Other Foods'),
        ('ingredient_group', 'Compound Ingredients')]
COLOR = {4: '#2a7a1f', 3: '#5a8a2f', 2: '#7a9a3f', 1: '#b89a00', 0: '#888880',
         -1: '#c87020', -2: '#c85020', -3: '#c83020', -4: '#8b0000'}


def sgn(v):
    return f'+{v}' if v > 0 else str(v)


def mn(v):
    """score for prose: +2, 0, &minus;1"""
    return f'+{v}' if v > 0 else ('0' if v == 0 else f'&minus;{abs(v)}')


def share_words(n, d):
    """'nearly half', 'more than 4 in 5' ... plain words for a share of bars."""
    p = n / d
    for lo, w in [(0.9, 'more than 9 in 10'), (0.8, 'more than 4 in 5'), (0.75, 'about 3 in 4'), (0.66, 'about 2 in 3'),
                  (0.55, 'more than half of all'), (0.45, 'nearly half of all'), (0.38, 'about 2 in 5'), (0.3, 'nearly 1 in 3'),
                  (0.23, 'about 1 in 4'), (0.18, 'about 1 in 5'), (0.0, None)]:
        if p >= lo:
            return w or f'{pct0(n, d)}%'


def main():
    R, N, canon = ingredient_counts()
    rows = {k: v for k, v in R.items() if v['bars'] >= MIN_BARS and v['category'] not in NOT_INGREDIENTS
            and not k.startswith(('contains ', 'includes '))}
    by = {c: sorted((k for k in rows if rows[k]['category'] == c), key=lambda k: (-rows[k]['bars'], k)) for c, _ in CATS}
    unknown = {rows[k]['category'] for k in rows} - {c for c, _ in CATS}
    if unknown:
        raise SystemExit(f'ERROR: schema categories with no section on the page: {sorted(unknown)}. Not writing.')
    leak = [(k, rows[k]['desc']) for k in rows if INTERNAL.search(rows[k]['desc'])]
    if leak:
        raise SystemExit('ERROR: schema change-log text would show on the page. Add these to PUBLIC_DESC in '
                         'kyb_ingredients.py. Not writing.\n' + '\n'.join(f'  {k}: {d}' for k, d in leak))
    cats = [(c, t) for c, t in CATS if by[c]]
    n_ing = len(rows)
    canon_n = f'{len(canon) // 100 * 100:,}+'
    ranked = sorted(rows, key=lambda k: -rows[k]['bars'])
    S = lambda k: rows[k]['score']
    B = lambda k: rows[k]['bars']
    pc = lambda k: f'{pct0(B(k), N)}%'
    cl = Claims()

    def has(k):
        return cl.check(k in rows, f'{k!r} is listed on the page')

    # ---------- section blurbs (every stated fact checked)
    blurb = {}
    ok = has('whey protein isolate') and has('collagen')
    cl.check(ok and S('whey protein isolate') == 4 and S('collagen') == 1, 'whey isolate +4, collagen +1')
    blurb['protein'] = (f'The backbone of every protein bar. Quality varies enormously, from whey protein isolate '
                        f'({mn(S("whey protein isolate"))}) to collagen ({mn(S("collagen"))}), which is missing essential amino acids.')
    sw = ['honey', 'cane sugar', 'brown rice syrup', 'maltitol', 'erythritol', 'sucralose']
    if all(has(k) for k in sw):
        cl.check((S('honey'), S('cane sugar'), S('brown rice syrup'), S('erythritol'), S('maltitol'), S('sucralose')) == (-1, -2, -3, -3, -4, -2),
                 'sweetener scale: honey -1, cane sugar -2, brown rice syrup -3, sugar alcohols -3/-4, sucralose -2')
    blurb['sweetener'] = ('The most consequential category. Sugars are scored by how processed they are: honey and maple syrup '
                          '&minus;1, cane sugar &minus;2, starch-based syrups like brown rice syrup &minus;3. Sugar alcohols score '
                          '&minus;3 to &minus;4, and each artificial sweetener costs a bar a flat &minus;2 wherever it appears on the label. '
                          'See <a href="/ingredient_scoring#sugars-fibers-sweeteners">how we score sweeteners</a>.')
    blurb['whole_food'] = ('Nuts, seeds, oats, dates, fruits: ingredients that look the same on a label as they do in nature. '
                           'Generally the best signals in any bar.')
    fat_top = by['fat_oil'][0]
    neg_fats = [k for k in by['fat_oil'] if S(k) < 0]
    if all(has(k) for k in ['cocoa butter', 'palm kernel oil', 'sunflower oil', 'canola oil']):
        cl.check(fat_top == 'cocoa butter' and S('cocoa butter') > 0, 'cocoa butter is the most common fat and scores positive')
        cl.check(S('sunflower oil') == -1 and S('canola oil') == -1, 'sunflower and canola oil score -1')
        cl.check(neg_fats[0] == 'palm kernel oil' and S('palm kernel oil') == -3, 'palm kernel oil is the most common negative fat, -3')
    blurb['fat_oil'] = (f'Cocoa butter is the most common fat and scores {mn(S("cocoa butter"))}. Seed oils like sunflower and canola '
                        f'are minor concerns ({mn(S("sunflower oil"))}). Palm kernel oil, the most common processed fat in bar coatings, '
                        f'is a hard negative ({mn(S("palm kernel oil"))}).')
    if has('cocoa') and has('unsweetened chocolate') and has('chocolate'):
        cl.check(S('cocoa') > 0 and S('unsweetened chocolate') > 0 and S('chocolate') == 0, 'cocoa/unsweetened chocolate positive, chocolate 0')
    blurb['cocoa_chocolate'] = ('Cocoa and unsweetened chocolate score well. "Chocolate coating" or sweetened chocolate chips are '
                                'compound ingredients, scored by what\'s inside them.')
    fib_pos = ['chicory root fiber', 'inulin']
    fib_eng = ['tapioca fiber', 'soluble corn fiber', 'polydextrose', 'isomalto-oligosaccharides']
    if all(has(k) for k in fib_pos + fib_eng):
        cl.check(all(S(k) == 1 for k in fib_pos) and all(S(k) == -1 for k in fib_eng), 'plant fibers +1, engineered fibers -1')
        cl.check(by['fiber_or_functional_carb'][0] == 'tapioca fiber', 'tapioca fiber is the most common fiber')
    blurb['fiber_or_functional_carb'] = ('Added fibers and functional carbs. Tapioca fiber is the most common. Fiber pulled from '
                                         'plants, like chicory root fiber and inulin, scores +1. Engineered starch fibers like tapioca '
                                         'fiber, soluble corn fiber, polydextrose and IMO score &minus;1: the label can count them as '
                                         'fiber, but they are highly processed.')
    zero = sum(1 for k in by['starch_flour'] if S(k) == 0)
    cl.check(zero > len(by['starch_flour']) / 2, 'most starches and flours score 0')
    blurb['starch_flour'] = (f'Mostly neutral texture and binding agents: {zero} of the {len(by["starch_flour"])} listed here score 0. '
                             f'None are clean signals, but few are red flags either.')
    if has('glycerin'):
        cl.check(by['additive'][0] == 'glycerin', 'glycerin is the most common additive')
    blurb['additive'] = (f'Humectants, stabilizers, and anti-caking agents. Glycerin is the most common: it\'s in '
                         f'{share_words(B("glycerin"), N)} bars ({pc("glycerin")}) to keep them chewy.')
    if all(has(k) for k in ['soy lecithin', 'sunflower lecithin', 'mono and diglycerides']):
        cl.check(S('soy lecithin') == 0 and S('sunflower lecithin') == 0 and S('mono and diglycerides') == -1, 'lecithins 0, mono and diglycerides -1')
    blurb['emulsifier'] = ('Keeps ingredients from separating. Soy and sunflower lecithin are standard and score neutral. '
                           'Mono and diglycerides score slightly negative (&minus;1).')
    nf_rank = ranked.index('natural flavors') + 1 if has('natural flavors') else 0
    ordinal = {1: 'most common', 2: 'second most common', 3: 'third most common'}.get(nf_rank)
    cl.check(ordinal is not None, 'natural flavors is a top-3 ingredient')
    if has('natural and artificial flavors'):
        cl.check(S('natural flavors') == -1 and S('natural and artificial flavors') < -1, 'natural flavors -1, natural and artificial worse')
    blurb['flavor_additive'] = (f'Natural flavors are the {ordinal} ingredient in the database, in {pc("natural flavors")} of bars, '
                                f'and score as a minor concern (&minus;1). "Natural and artificial flavors" scores worse '
                                f'({mn(S("natural and artificial flavors"))}).')
    cl.check(ranked[0] == 'salt' and S('salt') == 0, 'salt is the most common ingredient and scores 0')
    blurb['seasoning'] = (f'Salt is the most common ingredient in the database, in {share_words(B("salt"), N)} bars ({pc("salt")}). '
                          f'It is neutral by itself, but its position in the ingredient list matters.')
    cl.check(all(S(k) == 0 for k in by['vitamin_mineral']), 'all vitamins and minerals score 0')
    blurb['vitamin_mineral'] = ('Fortification additions. Vitamin E (tocopherols) doubles as a natural preservative. All score '
                                'neutral; their presence doesn\'t help or hurt a bar\'s score.')
    if has('citric acid') and has('potassium sorbate'):
        cl.check(by['acid_or_preservative'][0] == 'citric acid' and S('citric acid') == -1 and S('potassium sorbate') == -2,
                 'citric acid most common (-1), potassium sorbate -2')
    blurb['acid_or_preservative'] = ('Citric acid is the most common entry and a minor concern (&minus;1). Potassium sorbate scores '
                                     'as a full concern (&minus;2). Rosemary extract and tocopherols, used as natural preservatives, score neutral.')
    if has('rosemary extract') and has('tocopherols'):
        cl.check(S('rosemary extract') == 0 and S('tocopherols') == 0, 'rosemary extract and tocopherols 0')
    if has('titanium dioxide'):
        cl.check(by['color_additive'][0] == 'titanium dioxide' and S('titanium dioxide') < 0, 'titanium dioxide most common color, negative')
    blurb['color_additive'] = ('Titanium dioxide is the most common color additive and scores negative. Synthetic dyes like Red 40 '
                               'and Blue 1 score &minus;1; most color additives add nothing nutritionally.')
    for k in ['red 40', 'blue 1']:
        if has(k):
            cl.check(S(k) == -1, f'{k} scores -1')
    bot = {S(k) for k in by['botanical_or_functional']}
    cl.check(bot <= {0, 1}, 'botanicals score 0 to +1')
    for k in ['lions mane', 'l-theanine', 'ginger']:
        has(k)
    blurb['botanical_or_functional'] = ('Adaptogens and functional add-ins like lion\'s mane, ginger and L-theanine. Small amounts; '
                                       'they score neutral to slightly positive.')
    of = by['other_food']
    cl.check(all(S(k) == 0 for k in of), 'other foods score 0')
    blurb['other_food'] = ('Basic food components like water that score neutral.')
    for k in ['protein blend', 'chocolate chips']:
        has(k)
    cl.check(by['ingredient_group'][0] == 'protein blend', 'protein blend is the most common compound ingredient')
    blurb['ingredient_group'] = ('Compound ingredient groups where the ingredients inside are scored instead of the parent label. '
                                 '"Protein blend" and "chocolate chips" are the most common examples.')

    # ---------- FAQ
    for k in ['maltitol', 'erythritol', 'palm kernel oil', 'egg whites', 'pea protein', 'brown rice protein']:
        has(k)
    cl.check(S('maltitol') == -4 and S('erythritol') == -3, 'maltitol -4, erythritol -3')
    cl.check(S('egg whites') == 4 and S('pea protein') == 2 and S('brown rice protein') == 2, 'egg whites +4, pea and brown rice protein +2')
    pko, pko_top = B('palm kernel oil'), rows['palm kernel oil']['top']
    pko_sub = pko - pko_top
    cl.check(S('glycerin') == -1, 'glycerin -1')
    cl.stop_if_failed()

    faqs = [
        ('How many ingredients are in the protein bar encyclopedia?',
         f'This encyclopedia covers {n_ing} ingredients that each appear in {MIN_BARS} or more of the {comma(N)} protein bars in our '
         f'database. Our full scoring schema has {canon_n} canonical ingredients, but we cut off at {MIN_BARS} bars to keep the '
         f'reference useful rather than exhaustive.'),
        ('What does the bar (meter) next to each ingredient show?',
         f'The share of all {comma(N)} bars in our database that contain that ingredient anywhere on the label, including inside a '
         f'compound ingredient like a chocolate coating. Salt, for example, appears in {pc("salt")} of bars. Maltitol appears in '
         f'{pc("maltitol")}. The percentage is out of every bar in the database, not just the category.'),
        ('What do the score numbers mean?',
         'Scores run from -4 (worst) to +4 (best). A score of 0 is neutral. Positive scores indicate beneficial or clean ingredients. '
         'Negative scores indicate ingredients that drag down a bar\'s overall grade. The scores reflect ingredient quality in the '
         'context of a protein bar, not an absolute health judgment.'),
        ('Why is natural flavors scored as a minor concern (-1)?',
         'Natural flavors is a broad regulatory category that can include hundreds of substances. The term reveals nothing about '
         'what specific compounds are present. We score it as -1 because it adds no nutritional value and provides no transparency '
         'about what you are actually consuming. It is not a major concern, but it is not a positive signal either.'),
        ('Why does maltitol score worse than erythritol?',
         'Maltitol (-4) has a glycemic index around 35, significantly higher than erythritol (-3), which is close to zero. Maltitol '
         'also causes more GI distress than most sugar alcohols. Erythritol is largely absorbed before it reaches the colon and has a '
         'far lower impact on blood sugar. Both are sugar alcohols, but they behave very differently in the body.'),
        ('Why do tapioca fiber and soluble corn fiber score -1?',
         'They are starches that were rearranged so the body can\'t fully digest them. That lets a label count them as fiber and '
         'lower "net carbs." They aren\'t harmful, but they are highly processed stand-ins for fiber from food, so they score -1. '
         'Fiber pulled from plants, like chicory root fiber and inulin, scores +1.'),
        ('Is glycerin (glycerol) bad?',
         f'Glycerin is a humectant used to keep bars soft and extend shelf life. It has a mild sweetness and a small caloric impact. '
         f'We score it at -1 because it is a processing additive with no nutritional benefit, but it is not a red flag ingredient. '
         f'It appears in {share_words(B("glycerin"), N)} bars ({pc("glycerin")}), which shows how central it is to the texture and '
         f'shelf life of the modern protein bar.'),
        ('What is palm kernel oil doing in so many bars?',
         f'Palm kernel oil is the fat of choice for chocolate-style coatings because it creates a firm snap at room temperature '
         f'without refrigeration. It appears in {comma(pko)} bars, and in {comma(pko_sub)} of them it only shows up inside a compound '
         f'ingredient like "chocolate flavored coating" rather than on its own, which is why it\'s easy to miss. It scores -3 because '
         f'it is a highly saturated, industrially processed fat with environmental concerns around sourcing.'),
        ('Why are some protein sources scored higher than others?',
         'Scores reflect completeness of amino acid profile and processing level. Whey protein isolate and egg whites score +4 '
         'because they are complete proteins with excellent bioavailability and minimal processing. Collagen scores +1 because while '
         'it is technically protein, it lacks tryptophan and is not a complete protein source. Pea and brown rice protein score +2 '
         'as clean plant sources that, when combined, provide a complete amino acid profile.'),
    ]

    # ---------- regions
    title = f'Protein Bar Ingredients: {n_ing} Ingredients Explained & Scored'
    desc = (f'Every ingredient found across {comma(N)} protein bars, scored from +4 to -4 and explained. See which appear most, '
            f'score best, and which to avoid on any label.')
    head = (f'  <title>{esc(title)} | Know Your Bar</title>\n'
            f'  <meta name="description" content="{esc(desc)}">')
    art = {'@context': 'https://schema.org', '@type': 'Article', 'headline': title, 'description': desc,
           'url': 'https://knowyourbar.com/all-ingredients', 'image': 'https://knowyourbar.com/bar_hero.png',
           'datePublished': PUBLISHED, 'dateModified': today_iso(),
           'author': {'@type': 'Organization', 'name': 'Know Your Bar', 'url': 'https://knowyourbar.com'},
           'publisher': {'@type': 'Organization', 'name': 'Know Your Bar', 'url': 'https://knowyourbar.com'}}
    faq_ld = {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
        {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in faqs]}
    jsonld = ('  <script type="application/ld+json">\n  ' + json.dumps(art, ensure_ascii=False, indent=2).replace('\n', '\n  ')
              + '\n  </script>\n  <script type="application/ld+json">\n  '
              + json.dumps(faq_ld, ensure_ascii=False, separators=(',', ':')) + '\n  </script>')
    social = (f'  <meta property="og:title" content="{esc(title)}">\n'
              f'  <meta name="twitter:title" content="{esc(title)}">\n'
              f'  <meta property="og:description" content="{esc(desc)}">')
    hero = (f'    <p class="hero-sub">Every ingredient that appears in {MIN_BARS} or more of our {comma(N)} protein bars. Scored, '
            f'explained, and ranked by how many bars it appears in. Use it to read any label.</p>\n'
            f'    <div class="ing-hero-stats">\n'
            f'      <div class="ing-hero-stat"><strong>{n_ing}</strong>ingredients catalogued</div>\n'
            f'      <div class="ing-hero-stat"><strong>{comma(N)}</strong>bars analyzed</div>\n'
            f'      <div class="ing-hero-stat"><strong>{len(cats)}</strong>ingredient categories</div>\n'
            f'    </div>')
    catnav = '\n'.join(f'        <a href="#cat-{c}" class="cat-nav-link">{esc(t)}</a>' for c, t in cats)

    def row(k):
        s, col = S(k), COLOR[S(k)]
        p = f'{100 * B(k) / N:.1f}'
        return f'''          <div class="ing-row">
            <div class="ing-meta">
              <span class="ing-score-badge" style="background:{col};color:#fff;">{sgn(s)}</span>
              <div class="ing-info">
                <div class="ing-name">{esc(k)}</div>
                <div class="ing-desc">{esc(rows[k]['desc'])}</div>
              </div>
              <div class="ing-bars-label">{comma(B(k))} bars</div>
            </div>
            <div class="ing-bar-track">
              <div class="ing-bar-fill" style="width:{p}%;background:{col};"></div>
              <span class="ing-bar-pct">{p}%</span>
            </div>
          </div>'''

    secs = []
    for c, t in cats:
        secs.append(f'''  <!-- {t.upper()} -->
  <section class="ing-section" id="cat-{c}">
    <div class="ing-section-inner">
      <div class="ing-section-header">
        <div class="ing-section-title-group">
          <h2 class="ing-section-title">{esc(t)}</h2>
          <div class="ing-section-count">{len(by[c])} ingredient{'s' if len(by[c]) != 1 else ''}</div>
        </div>
        <p class="ing-section-desc">{blurb[c]}</p>
      </div>
      <div class="ing-list">
''' + '\n'.join(row(k) for k in by[c]) + '''
      </div>
    </div>
  </section>''')
    sections = '\n\n'.join(secs)
    cta = (f'    <p class="explore-cta-sub">Filter all {comma(N)} bars by ingredient quality grade, sweeteners, sugar alcohols, seed '
           f'oils, and more. Every bar scored A-F. No sponsored picks.</p>')
    card = f'          <div class="explore-more-desc">Patterns, surprises, and the best and worst ingredients across {comma(N)} bars.</div>'
    faq = '\n\n'.join(f'''      <div class="faq-item">
        <button class="faq-q">{esc(q)}</button>
        <div class="faq-a">{esc(a)}</div>
      </div>''' for q, a in faqs)

    page = open(PAGE, encoding='utf-8').read()
    for name, content in [('head', head), ('jsonld', jsonld), ('social', social), ('hero', hero), ('cat-nav', catnav),
                          ('sections', sections), ('cta-sub', cta), ('report-card', card), ('faq', faq)]:
        page = replace_region(page, name, content)
    page = stamp_dates(page, today_iso())
    visible = re.sub(r'<style.*?</style>', '', page, flags=re.S)  # a CSS comment on the live page uses an em dash
    for bad in ('\u2014', 'href="Yes"', 'href="None"'):
        if bad in visible:
            raise SystemExit(f'ERROR: forbidden string {bad!r} in page. Not writing.')
    open(PAGE, 'w', encoding='utf-8').write(page)
    for t, n, a, c in alias_score_conflicts():
        if n in rows:
            print(f'WARNING (schema): alias "{t}" scores {a:+d} but its canonical "{n}" scores {c:+d}; page shows {c:+d}')
    print(f'{PAGE}: {n_ing} ingredients in {len(cats)} categories from {comma(N)} bars (min {MIN_BARS} bars); '
          f'top: ' + ', '.join(f'{k} {B(k)}' for k in ranked[:5]))


if __name__ == '__main__':
    main()
