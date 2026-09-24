"""Rebuild brand-quadrant.html from bars.js.

Opens the LIVE page and rewrites only the <!-- kyb:NAME --> regions:
  head        <title>, meta description, og:title, og:description
  hero        hero sub-line and stat cards
  view        view explainer (All view counts)
  quad-data   the data <script> (ALL_BRANDS, VIEW_META, axis bounds)
  cta         CTA link text
Everything else (nav, footer, chart code) is kept as-is.

Brand rules (reverse-engineered from the original page, unchanged):
  * brands with 4+ bars in bars.js
  * ingredient_score = median bar ingredient_score
  * macro_score = median of per-bar
      0.6*min(P/Cal*100/15,1) + 0.25*(1-min(sugar/30,1)) + 0.15*min(fiber/20,1)
  * avg_protein / avg_calories / avg_sugar / avg_fiber = MEDIANS (the tooltip
    says "Avg"; the original page used medians and so does this)
  * modal_grade = most common grade (tie -> better grade), grade_dist = counts
  * mainstream = WIDE tier in build_brand_rankings.py + MAINSTREAM_EXTRA below
Quadrant midlines stay fixed: MID_ING 4.0 (the B-grade cutoff) and MID_MAC
0.525. Axis bounds are computed so every brand fits.

Run: python3 build_brand_quadrant.py
"""
import json, math, re, statistics as st
from collections import Counter
from kyb_guide_lib import (load_bars, num, score, fnum, esc, comma, replace_region,
                           stamp_dates, today_iso)
from build_brand_rankings import WIDE

PAGE = 'brand-quadrant.html'
MIN_FLAVORS = 4
MID_ING, MID_MAC = 4.0, 0.525

# Brands the original page flagged mainstream that are not in the WIDE tier.
MAINSTREAM_EXTRA = {
    'Aloha', 'BSN', "Bob's Red Mill", 'Built', 'GoMacro', 'Legendary', 'MRE BAR',
    'Magic Spoon', 'Misfits', 'No Cow', 'NuGo', 'PROBAR', 'Perfect Bar', 'Verb',
    'Wonderslim',
}
MAINSTREAM = WIDE | MAINSTREAM_EXTRA
GRADE_ORDER = 'ABCDF'


def macro(b):
    p, c = num(b.get('Protein (g)')) or 0, num(b.get('Calories')) or 0
    s, f = num(b.get('Sugars (g)')) or 0, num(b.get('Dietary Fiber (g)')) or 0
    pe = min((p / c * 100) / 15, 1) if c else 0
    return 0.6 * pe + 0.25 * (1 - min(s / 30, 1)) + 0.15 * min(f / 20, 1)


def med(vals):
    vals = [v for v in vals if v is not None]
    return st.median(vals) if vals else 0


def brand_rows(bars):
    by = {}
    for b in bars:
        if score(b) is None or not b.get('score_band'):
            continue
        by.setdefault(b['Brand Name'].strip(), []).append(b)
    rows = []
    for brand in sorted(by, key=lambda s: s.lower()):
        bs = by[brand]
        if len(bs) < MIN_FLAVORS:
            continue
        gd = Counter(b['score_band'] for b in bs)
        modal = sorted(gd, key=lambda g: (-gd[g], GRADE_ORDER.index(g)))[0]
        rows.append({
            'brand': brand,
            'flavor_count': len(bs),
            'ingredient_score': round(med([score(b) for b in bs]), 2),
            'macro_score': round(med([macro(b) for b in bs]), 3),
            'modal_grade': modal,
            'avg_protein': round(med([num(b.get('Protein (g)')) for b in bs]), 1),
            'avg_calories': round(med([num(b.get('Calories')) for b in bs]), 1),
            'avg_sugar': round(med([num(b.get('Sugars (g)')) for b in bs]), 1),
            'avg_fiber': round(med([num(b.get('Dietary Fiber (g)')) for b in bs]), 1),
            'grade_dist': {g: gd[g] for g in GRADE_ORDER if gd[g]},
            'is_mainstream': brand in MAINSTREAM,
        })
    return rows


def bounds(rows):
    ing = [r['ingredient_score'] for r in rows]
    mac = [r['macro_score'] for r in rows]
    return (math.floor(min(ing)) - 1, math.ceil(max(ing)) + 1,
            math.floor((min(mac) - 0.08) * 100) / 100, math.ceil((max(mac) + 0.08) * 100) / 100)


def main():
    bars = load_bars()
    rows = brand_rows(bars)
    n_br, n_bars = len(rows), sum(r['flavor_count'] for r in rows)
    ms = [r for r in rows if r['is_mainstream']]
    su = [r for r in rows if not r['is_mainstream']]
    vm = {
        'all': {'desc': f'All {n_br} brands with {MIN_FLAVORS}+ scored flavors, regardless of distribution size',
                'brands': n_br, 'bars': n_bars},
        'mainstream': {'desc': 'Widely distributed brands found in major retail - Target, Walmart, Costco, GNC',
                       'brands': len(ms), 'bars': sum(r['flavor_count'] for r in ms)},
        'startup': {'desc': 'Smaller, independent, or digitally-native brands not yet in major retail',
                    'brands': len(su), 'bars': sum(r['flavor_count'] for r in su)},
    }
    i0, i1, m0, m1 = bounds(rows)
    assert i0 < MID_ING < i1 and m0 < MID_MAC < m1
    total = len(bars)

    desc = (f'{n_br} brands mapped by ingredient quality and macro efficiency. See which lead on both '
            f'and which trade one for the other. {comma(n_bars)} bars scored, no sponsorships.')
    title = 'Protein Bar Brands: Ingredients vs Macros | Know Your Bar'
    head = (f'  <title>{title}</title>\n'
            f'  <meta name="description" content="{esc(desc)}">\n'
            f'  <link rel="canonical" href="https://knowyourbar.com/brand-quadrant">\n'
            f'  <meta property="og:type" content="article">\n'
            f'  <meta property="og:title" content="{title}">\n'
            f'  <meta property="og:description" content="{esc(desc)}">')
    hero = (f'  <p class="qhero-sub">We scored {n_br} brands across {comma(n_bars)} bars on ingredient quality and macro efficiency. '
            f'No sponsorships. No affiliate influence. Just data.</p>\n'
            f'  <div class="qhero-stats">\n'
            f'    <div class="qhero-stat"><strong>{n_br}</strong><span>brands mapped</span></div>\n'
            f'    <div class="qhero-stat"><strong>{comma(n_bars)}</strong><span>bars scored</span></div>\n'
            f'    <div class="qhero-stat"><strong>{MIN_FLAVORS}+</strong><span>flavors to qualify</span></div>\n'
            f'    <div class="qhero-stat"><strong>2026</strong><span>data</span></div>\n'
            f'  </div>')
    view = (f'    <span id="view-desc">{esc(vm["all"]["desc"])}</span>\n'
            f'    <span class="qview-count" id="vc-brands">{n_br} brands</span>\n'
            f'    <span class="qview-count" id="vc-bars">{n_bars} bars</span>')
    vm_js = ',\n'.join(f"  {k}:{' ' * (11 - len(k))}{{desc:{json.dumps(v['desc'])},brands:{v['brands']},bars:{v['bars']}}}"
                       for k, v in vm.items())
    data = ('<script>\n'
            f'const ALL_BRANDS={json.dumps(rows, ensure_ascii=False, separators=(",", ":"))};\n\n'
            f'const VIEW_META={{\n{vm_js},\n}};\n\n'
            '// Axis bounds (computed by build_brand_quadrant.py; midlines fixed: 4.0 = B-grade cutoff)\n'
            f'const ING_MIN={fnum(i0)},ING_MAX={fnum(i1)},MAC_MIN={m0:g},MAC_MAX={m1:g};\n'
            f'const MID_ING={MID_ING},MID_MAC={MID_MAC};\n'
            '</script>')
    cta = f'    <a href="/bar-finder">Search and filter {comma(total)} bars &rarr;</a>'

    page = open(PAGE, encoding='utf-8').read()
    for name, content in [('head', head), ('hero', hero), ('view', view), ('quad-data', data), ('cta', cta)]:
        page = replace_region(page, name, content)
    page = stamp_dates(page, today_iso())

    # Checks
    for bad in ('—', 'href="Yes"', 'href="None"'):
        if bad in page:
            raise SystemExit(f'ERROR: forbidden string {bad!r} in page. Not writing.')
    pl = page[page.index('const PRIORITY_LABELS'):]
    pl = pl[:pl.index(']);')]
    names = {a or b for a, b in re.findall(r"'([^']*)'|\"([^\"]*)\"", pl)}
    missing = sorted(names - {r['brand'] for r in rows})
    if missing:
        print('NOTE: priority labels with no dot on the chart (under 4 flavors or renamed):', ', '.join(missing))
    open(PAGE, 'w', encoding='utf-8').write(page)
    print(f'{PAGE}: {n_br} brands, {n_bars} bars (mainstream {len(ms)}/{vm["mainstream"]["bars"]}, '
          f'startup {len(su)}/{vm["startup"]["bars"]}); axes ing {i0}..{i1}, mac {m0}..{m1}')


if __name__ == '__main__':
    main()
