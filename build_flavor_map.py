"""Rebuild flavor-map.html from bars.js.

Opens the LIVE page and rewrites only the <!-- kyb:NAME --> regions:
  head         <title> and meta description
  hero         eyebrow and hero sub-line
  stats        the five stat cards
  sankey-aria  the <svg> opening tag (aria-label with the counts)
  flavor-data  the data <script> (L1 primary flavors, L2 variations)
  footnote     footnote under the chart
The chart code, nav and footer are kept as-is.

Flavors are parsed from each bar's Flavor Name with classify() below. Every
bar in bars.js lands in exactly one primary flavor and one variation (the
catch-all is Other / Other flavors). Edit the rules here, not the page.

Run: python3 build_flavor_map.py
"""
import json, re
from collections import Counter
from kyb_guide_lib import load_bars, esc, comma, replace_region, stamp_dates, today_iso

PAGE = 'flavor-map.html'

# Primary flavors: (id, label). Order on the page is by count, largest first.
PRIMARY = [('choc', 'Chocolate'), ('pb', 'Peanut Butter'), ('fruit', 'Fruit'), ('other', 'Other'),
           ('van', 'Vanilla'), ('car', 'Caramel'), ('cin', 'Cinnamon')]
# Variations that pair two flavors (used for the "#1 combo" stat).
COMBOS = {'PB Chocolate', 'PB + Jelly', 'PB Honey', 'PB Banana', 'Choc Almond', 'Choc Mint', 'Choc Caramel',
          'Fruit + Coconut', 'Fruit + Almond', 'Caramel Peanut', 'Caramel Almond', 'Caramel Coconut',
          'Vanilla Almond', 'Vanilla Chai', 'Cookies & Cream'}
SHORT = {'Chocolate Chip': 'Choc Chip', 'PB Chocolate': 'PB Choc'}

CHOC = r'choc|cocoa|cacao|brownie|fudge|mocha'
FRUIT = (r'appl|banana|berry|berries|cherry|lemon|lime|mango|peach|orange|cranberr|apricot|pineapple|\bfig|'
         r'pomegranate|tropical|grape|raisin|citrus|passion|kiwi|plum|pear\b|watermelon|acai|goji|date')


def classify(name):
    """Flavor Name -> (primary label, variation label)."""
    t = name.lower().replace('&', 'and')
    has = lambda rx: re.search(rx, t)
    if has(r"cookies? ?(and |'?n'? )?cr[eè]a?me?\b|\boreo"):
        return 'Vanilla', 'Cookies & Cream'
    if has(r'peanut butter|\bpb\b'):
        for rx, lab in [(r'jelly|jam\b', 'PB + Jelly'), (r'\bcups?\b', 'PB Cup'), (CHOC, 'PB Chocolate'),
                        (r'crunch|crisp', 'PB Crunch'), (r'honey', 'PB Honey'), (r'banana', 'PB Banana'),
                        (r'cookie', 'PB Cookie')]:
            if has(rx):
                return 'Peanut Butter', lab
        return 'Peanut Butter', 'Other PB'
    if has(CHOC) or has(r'cookie dough|mint chip|thin mint'):
        for rx, lab in [(r'chip|cookie dough', 'Chocolate Chip'), (r'brownie|fudge', 'Brownie'), (r'almond', 'Choc Almond'),
                        (r'mint', 'Choc Mint'), (r'caramel', 'Choc Caramel'), (r'dark', 'Dark Chocolate'),
                        (r'crunch|crisp', 'Choc Crunch')]:
            if has(rx):
                return 'Chocolate', lab
        return 'Chocolate', 'Other Chocolate'
    if has(r'caramel|toffee'):
        for rx, lab in [(r'peanut', 'Caramel Peanut'), (r'salt', 'Salted Caramel'), (r'almond', 'Caramel Almond'),
                        (r'coconut', 'Caramel Coconut')]:
            if has(rx):
                return 'Caramel', lab
        return 'Caramel', 'Plain Caramel'
    if has(r'vanilla|birthday cake|cake batter|frosting'):
        for rx, lab in [(r'almond', 'Vanilla Almond'), (r'chai', 'Vanilla Chai')]:
            if has(rx):
                return 'Vanilla', lab
        return 'Vanilla', 'Plain Vanilla'
    if has(r'\bpeanut'):
        return 'Peanut Butter', 'Other PB'
    if has(r'cinnamon|snickerdoodle|churro'):
        return 'Cinnamon', 'Cinnamon'
    if has(FRUIT):
        if has(r'coconut'):
            return 'Fruit', 'Fruit + Coconut'
        if has(r'almond'):
            return 'Fruit', 'Fruit + Almond'
        if has(r'cashew|pecan|walnut|pistachio|peanut|macadamia|hazelnut|nut\b|yogurt|oat|seed|chia'):
            return 'Fruit', 'Fruit + Other'
        return 'Fruit', 'Single Fruit'
    return 'Other', 'Other flavors'


def main():
    bars = load_bars()
    total = len(bars)
    c1, c2 = Counter(), Counter()
    for b in bars:
        p, v = classify(b['Flavor Name'])
        c1[p] += 1
        c2[(p, v)] += 1
    assert sum(c1.values()) == total
    l1 = sorted(PRIMARY, key=lambda x: -c1[x[1]])
    l1_js = ',\n'.join(f"  {{id:{json.dumps(i)},{' ' * (6 - len(i))}label:{json.dumps(lab)},{' ' * (15 - len(lab))}n:{c1[lab]}}}"
                       for i, lab in l1)
    l2 = []
    for i, lab in l1:
        kids = sorted(((v, n) for (p, v), n in c2.items() if p == lab), key=lambda x: (-x[1], x[0]))
        l2 += [(i, v, n) for v, n in kids]
    l2_js = ',\n'.join(f"  {{p:{json.dumps(i)},{' ' * (6 - len(i))}label:{json.dumps(v)},{' ' * (16 - len(v))}n:{n}}}"
                       for i, v, n in l2)
    data = ('<script>\n'
            '// Flavor counts (built by build_flavor_map.py from bars.js)\n'
            f'const L1=[\n{l1_js},\n];\n\n'
            f'const L2=[\n{l2_js},\n];\n'
            '</script>')

    named = [(v, n) for _, v, n in l2 if not v.startswith(('Other', 'Plain', 'Single')) and v not in c1]
    top_var = max(named, key=lambda x: x[1])
    top_combo = max(((v, n) for v, n in named if v in COMBOS), key=lambda x: x[1])
    lead, lead_n = l1[0][1], c1[l1[0][1]]
    lead_pct = round(lead_n / total * 100)
    short = lambda v: SHORT.get(v, v)

    title = f'Protein Bar Flavor Map: {comma(total)} Bars Visualized | Know Your Bar'
    desc = (f'How {comma(total)} protein bars break down by flavor. {lead} leads at {lead_pct}%. Explore every primary '
            f'flavor and variation, from {short(top_var[0])} ({top_var[1]}) to {top_combo[0]} ({top_combo[1]}).')
    head = (f'  <title>{esc(title)}</title>\n'
            f'  <meta name="description" content="{esc(desc)}">')
    hero = (f'  <div class="eyebrow">Data visualization &middot; {comma(total)} bars</div>\n'
            f'  <h1 class="hero-title">The protein bar <em>flavor map</em></h1>\n'
            f'  <p class="hero-sub">How {comma(total)} protein bars break down by flavor, from primary category into '
            f'specific variations. Hover any flow to see the exact count.</p>')
    stats = '\n'.join(
        [f'  <div class="stat"><span class="stat-n">{c1[lab]}</span><span class="stat-l">{esc(lab)}</span></div>'
         for _, lab in l1[:3]] +
        [f'  <div class="stat"><span class="stat-n">{top_var[1]}</span><span class="stat-l">{esc(short(top_var[0]))}   #1 variation</span></div>',
         f'  <div class="stat"><span class="stat-n">{top_combo[1]}</span><span class="stat-l">{esc(short(top_combo[0]))}   #1 combo</span></div>'])
    aria = ', '.join(f'{lab} {c1[lab]}' for _, lab in l1)
    svg = f'    <svg id="sankey" role="img" aria-label="Sankey diagram: {comma(total)} protein bars by flavor. {esc(aria)}.">'
    foot = (f'<p class="footnote">Flavors parsed from bar names across {comma(total)} bars. '
            f'<a href="/bar-finder">Search all {comma(total)} bars &rarr;</a></p>')

    page = open(PAGE, encoding='utf-8').read()
    for name, content in [('head', head), ('hero', hero), ('stats', stats), ('sankey-aria', svg),
                          ('flavor-data', data), ('footnote', foot)]:
        page = replace_region(page, name, content)
    page = stamp_dates(page, today_iso())
    for bad in ('—', 'href="Yes"', 'href="None"'):
        if bad in page:
            raise SystemExit(f'ERROR: forbidden string {bad!r} in page. Not writing.')
    colors = re.search(r'const COLORS=\{(.*?)\};', page, re.S).group(1)
    for _, lab in PRIMARY:
        if f"'{lab}'" not in colors:
            raise SystemExit(f'ERROR: no color for primary flavor {lab!r} in the page COLORS map. Not writing.')
    open(PAGE, 'w', encoding='utf-8').write(page)
    print(f'{PAGE}: {total} bars; ' + ', '.join(f'{lab} {c1[lab]}' for _, lab in l1)
          + f'; #1 variation {top_var}, #1 combo {top_combo}; {len(l2)} variations')


if __name__ == '__main__':
    main()
