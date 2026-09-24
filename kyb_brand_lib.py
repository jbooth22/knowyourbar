#!/usr/bin/env python3
"""
Shared helpers for KnowYourBar brand review page builds (TEMPLATE_BRAND.html
pages: barebells-review, quest-bars, rxbar-review, clif-bar-review,
kind-bars-review).

Same model as the guide builds (see kyb_guide_lib.py): a build script opens
the LIVE page and rewrites only the <!-- kyb:NAME --> regions. Everything
here returns markup that matches the live brand pages.

Percentiles follow verify_brand_data.py: the brand's AVERAGE is compared with
every bar in bars.js. "Top X%" = 100 minus the share of bars the average
beats or ties.
"""
from kyb_guide_lib import *

GRADE_COLOR = {'A': '#2a7a1f', 'B': '#5a8a2f', 'C': '#b89a00', 'D': '#c87020', 'F': '#c83020'}

# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------
def vals(bars, fn):
    out = []
    for b in bars:
        v = fn(b)
        if v is not None:
            out.append(v)
    return out

def field(name):
    return lambda b: num(b.get(name))

def sa(b):
    return num(b.get('Sugar Alcohol (g)')) or 0

def nc(b):
    # GUIDE_CRITERIA.md: full subtraction, never halved
    return net_carbs(b)

METRICS = {  # key: (label, value fn, unit, direction) direction: 'high', 'low' or None
    'protein': ('Protein', field('Protein (g)'), 'g', 'high'),
    'p100': ('Protein/100cal', p100, 'g', 'high'),
    'cal': ('Calories', field('Calories'), 'cal', 'low'),
    'sugar': ('Total Sugar', field('Sugars (g)'), 'g', 'low'),
    'sa': ('Sugar Alcohol', sa, 'g', 'low'),
    'fiber': ('Fiber', field('Dietary Fiber (g)'), 'g', 'high'),
    'fat': ('Total Fat', field('Total Fat (g)'), 'g', None),
    'nc': ('Net Carbs', nc, 'g', 'low'),
}

def top_pct(all_bars, fn, value, direction):
    """verify_brand_data.py method. Returns (top_pct, beaten_pct)."""
    allv = vals(all_bars, fn)
    if direction == 'high':
        beats = sum(1 for v in allv if v <= value)
    else:
        beats = sum(1 for v in allv if v >= value)
    share = round(100 * beats / len(allv))
    return 100 - share, share

def metric_stats(bars, all_bars, key):
    label, fn, unit, direction = METRICS[key]
    v = vals(bars, fn)
    a = sum(v) / len(v)
    st = dict(key=key, label=label, unit=unit, lo=min(v), hi=max(v), avg=a, direction=direction)
    if direction:
        st['top'], st['beats'] = top_pct(all_bars, fn, a, direction)
    else:
        db = vals(all_bars, fn)
        st['db_avg'] = sum(db) / len(db)
    return st

def verdict(st):
    """(text, color) for a macro card, from the percentile only."""
    d = st['direction']
    if d is None:
        rel = 'Below' if st['avg'] < st['db_avg'] else 'Above'
        return f'{rel} the database average', 'var(--muted)'
    word = 'lowest' if d == 'low' else ''
    if d == 'low' and st['hi'] == 0:
        return ('Zero, every flavor', GRADE_COLOR['A'])
    top = st['top']
    if top <= 20:
        return (f'Top {top}%{" lowest" if word else ""}, excellent', GRADE_COLOR['A'])
    if top <= 33:
        return (f'Top {top}%{" lowest" if word else ""}, above average', GRADE_COLOR['B'])
    if st['beats'] <= 20:
        more = 'more than most bars' if d == 'low' else 'less than most bars'
        return (f'Bottom {max(st["beats"], 1)}%, {more}', GRADE_COLOR['F'])
    if st['beats'] <= 33:
        return (f'Below average, bottom {st["beats"]}%', GRADE_COLOR['D'])
    return ('Middle of the pack', GRADE_COLOR['C'])

def rng_txt(st, dec=False):
    f = (lambda x: f'{x:.1f}') if dec else fnum
    return f'{f(st["lo"])}&ndash;{f(st["hi"])}{st["unit"]}' if st['lo'] != st['hi'] else f'{f(st["lo"])}{st["unit"]}'

def grade_counts(bars):
    return {g: sum(1 for b in bars if b.get('score_band') == g) for g in BAND_ORDER}

def grade_counts_txt(bars, sep=' &middot; ', words=False):
    c = grade_counts(bars)
    return sep.join(f'{c[g]} {g}' + (f' ({grade_word(g)})' if words else '') for g in BAND_ORDER if c[g])

def range_letters(bars, arrow='&ndash;'):
    best, worst = grade_range(bars)
    return best if best == worst else f'{best}{arrow}{worst}'

def range_words(bars):
    best, worst = grade_range(bars)
    return best if best == worst else f'{best} to {worst}'

# ---------------------------------------------------------------------------
# Section markup
# ---------------------------------------------------------------------------
def macro_card(label, rng, avg_txt, vtxt, color):
    return f'''      <div class="macro-card">
        <div class="macro-label">{label}</div>
        <div class="macro-range">{rng}</div>
        <div class="macro-avg">{avg_txt}</div>
        <div class="macro-verdict" style="color:{color}">{vtxt}</div>
      </div>'''

def macro_grid_html(bars, all_bars):
    cards = [macro_card('Grade range', range_letters(bars), f'{len(bars)} flavors scored',
                        grade_counts_txt(bars), 'var(--muted)')]
    stats = {}
    for key in ['protein', 'p100', 'cal', 'sugar', 'sa', 'fiber', 'fat', 'nc']:
        st = metric_stats(bars, all_bars, key)
        stats[key] = st
        dec = key in ('p100', 'nc')
        v, c = verdict(st)
        cards.append(macro_card(st['label'], rng_txt(st, dec), f'avg {st["avg"]:.1f}{st["unit"]}', v, c))
    return '    <div class="macro-grid">\n' + '\n'.join(cards) + '\n    </div>', stats

def grade_dist_html(bars):
    c = grade_counts(bars)
    segs = ''.join(
        f'<div class="grade-seg" style="background:{GRADE_COLOR[g]};flex:{c[g]}" title="{grade_word(g)}: {c[g]} bar{"s" if c[g] != 1 else ""}">{g}</div>'
        for g in BAND_ORDER if c[g])
    legend = ' &nbsp;&middot;&nbsp; '.join(f'{c[g]} {g} ({grade_word(g)})' for g in BAND_ORDER if c[g])
    return f'''    <div class="grade-dist">
      {segs}
    </div>
    <p style="font-family:var(--bs-font-data);font-size:13px;color:var(--muted);">
      {legend}
    </p>'''

def chip_list(b):
    """[(name, type, severity)] in bars.js order."""
    out = []
    for part in (b.get('score_insights') or '').split('|'):
        bits = [x.strip() for x in part.split(':')]
        if bits and bits[0]:
            out.append((bits[0], bits[1] if len(bits) > 1 else 'neutral', bits[2] if len(bits) > 2 else ''))
    return out

def bchip(name, typ, sev):
    cls = {'positive': 'pos', 'concern': 'con', 'neutral': 'neu'}.get(typ, 'neu')
    if typ == 'concern' and sev == 'elevated':
        cls += ' elev'
    return f'<span class="bchip {cls}">{esc(name)}</span>'

def bw_card_html(b, best):
    g = b.get('score_band')
    chips = chip_list(b)
    good = ''.join(bchip(*c) for c in chips if c[1] == 'positive')
    bad = ''.join(bchip(*c) for c in chips if c[1] == 'concern')
    groups = ''
    if good:
        groups += f'''
        <div class="bw-chip-group-label">Good</div>
        <div class="bw-chips">
          {good}
        </div>'''
    if bad:
        groups += f'''
        <div class="bw-chip-group-label">Concerning</div>
        <div class="bw-chips">
          {bad}
        </div>'''
    links = []
    if amazon_url(b):
        links.append(f'<a href="{esc(amazon_url(b))}" target="_blank" rel="noopener sponsored" class="amazon-link">Shop on Amazon</a>')
    if website_url(b):
        links.append(f'<a href="{esc(website_url(b))}" target="_blank" rel="noopener" class="visit-link">Shop on Brand Site</a>')
    return f'''      <div class="bw-card {'best' if best else 'worst'}">
        <div class="bw-card-top">
          <div class="bw-label">{'Highest' if best else 'Lowest'} ingredient quality</div>
          <span class="grade-badge" style="background:{GRADE_COLOR[g]}" title="{grade_word(g)}">{g}</span>
        </div>
        <div class="bw-flavor">{esc(b['Flavor Name'])}</div>
        <div class="bw-score">Score {fnum(score(b))} &middot; Grade {g} ({grade_word(g)})</div>
        <div class="ingr-macros">
            <span><strong>Calories</strong>{fnum(num(b.get('Calories')))}</span>
            <span><strong>Protein</strong>{fnum(num(b.get('Protein (g)')))}g</span>
            <span><strong>Protein/100cal</strong>{fnum(p100(b))}g</span>
            <span><strong>Fiber</strong>{fnum(num(b.get('Dietary Fiber (g)')))}g</span>
            <span><strong>Sugar</strong>{fnum(num(b.get('Sugars (g)')))}g</span>
            <span><strong>Sugar Alcohol</strong>{fnum(sa(b))}g</span>
          </div>{groups}
        <div class="bw-buy-group">
          {chr(10).join('          ' + l if i else l for i, l in enumerate(links))}
        </div>
      </div>'''

def chip_freq(bars):
    """{name: (count, type, severity)} sorted most frequent first."""
    f = {}
    for b in bars:
        for name, typ, sev in chip_list(b):
            c, t, s = f.get(name, (0, typ, sev))
            f[name] = (c + 1, t, 'elevated' if 'elevated' in (s, sev) else s)
    return dict(sorted(f.items(), key=lambda kv: (-kv[1][0], kv[0])))

def chip_patterns_html(bars):
    n = len(bars)
    freq = chip_freq(bars)
    out = []
    for label, typ in [('Good qualities', 'positive'), ('Concerning qualities', 'concern'), ('Neutral', 'neutral')]:
        items = [(k, v) for k, v in freq.items() if v[1] == typ]
        if not items:
            continue
        rows = '\n'.join(f'''      <div class="chip-freq-item">
        <div class="chip-freq-name">{bchip(k, v[1], v[2])}</div>
        <div class="chip-freq-bar"><div class="chip-freq-fill" style="width:{round(100 * v[0] / n)}%"></div></div>
        <div class="chip-freq-pct">{v[0]}/{n}</div>
      </div>''' for k, v in items)
        out.append(f'    <div class="chip-group-label">{label}</div>\n    <div class="chip-freq-row">\n{rows}\n    </div>')
    return '\n\n'.join(out)

# ---------------------------------------------------------------------------
# Full flavor table (static rows, brand-page format)
# ---------------------------------------------------------------------------
def _rank_cell(lbl, val, pair):
    return f'''<div class="macro-rank-cell">
      <span class="macro-rank-lbl">{lbl}</span>
      <span class="macro-rank-val">{val}</span>
      <span class="macro-rank-tag {pair[1]}">{pair[0]}</span>
    </div>'''

def brand_row_html(b, idx, ranker):
    g = b.get('score_band')
    sc = score(b) or 0
    rec = lazy_record(b, idx, ranker)
    pos, neg, pp, npc = score_split(b)
    ranks = ''.join(_rank_cell(lbl, v, rec['rk'][k]) for k, lbl, v in [
        ('p', 'Protein', f'{fnum(rec["pv"])}g'), ('c', 'Calories', rec['cv']), ('s', 'Sugar', f'{rec["sv2"]}g'),
        ('f', 'Fiber', f'{rec["fv"]}g'), ('ft', 'Fat', f'{fnum(rec["ftv"])}g')])
    nutr = '\n'.join(f'''      <div class="nutr-row">
        <span class="nutr-label">{a}</span>
        <span class="nutr-val">{v}</span>
      </div>''' for a, v in rec['nu'])
    chips = ''
    for name, typ, sev in sorted(chip_list(b), key=lambda c: {'positive': 0, 'neutral': 1}.get(c[1], 2)):
        cls = CHIP_CLASS.get(typ, 'chip-neutral') + (' chip-elevated' if typ == 'concern' and sev == 'elevated' else '')
        chips += f'<span class="insight-chip {cls}">{esc(name)}</span>'
    pos_i = ''.join(f'<div class="ingr-col-item">{esc(x)}</div>' for x in rec['pi'])
    neg_i = ''.join(f'<div class="ingr-col-item">{esc(x)}</div>' for x in rec['ni'])
    certs = f'<div class="expand-certs-line">Certifications: {esc(", ".join(rec["ct"]))}</div>' if rec['ct'] else ''
    return f'''<tr class="bar-row" onclick="toggleIngr({idx}, this)">
            <td class="col-bar">
              <div class="bar-flavor">{esc(b['Flavor Name'])}</div>
              <svg class="row-expand-icon" width="7" height="12" viewBox="0 0 7 12" fill="none"><path d="M1 1L6 6L1 11" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </td>
            <td class="col-num col-hide-mobile">{fnum(num(b.get('Calories')))}</td>
            <td class="col-num">{fnum(num(b.get('Protein (g)')))}</td>
            <td class="col-num col-hide-mobile">{fnum(p100(b))}</td>
            <td class="col-num">{fnum(num(b.get('Total Fat (g)')))}</td>
            <td class="col-num col-hide-mobile">{fnum(num(b.get('Total Carbohydrates (g)')))}</td>
            <td class="col-num">{fnum(num(b.get('Dietary Fiber (g)')))}</td>
            <td class="col-num">{fnum(num(b.get('Sugars (g)')))}</td>
            <td class="col-num col-hide-mobile">{fnum(sa(b))}</td>
            <td class="col-certs col-hide-mobile"><div class="cert-badges">{cert_badges_html(b)}</div></td>
            <td class="col-grade"><span class="table-grade-badge grade-{g}" title="{grade_word(g)} &middot; score {fnum(sc)}">{g}</span></td>
          </tr>
          <tr class="ingr-row" id="ingr-{idx}">
            <td colspan="11" class="ingr-cell">
              <div class="expand-content">
                <div class="expand-meta">{esc(rec['sz'])} &middot; {esc(rec['ty'])} &middot; {rec['sv']}g serving</div>
                {certs}<div class="expand-buy-row">{buy_links_html(b)}</div>
                <div class="macro-rank-grid">{ranks}</div>
                <div class="expand-columns">
                  <div class="nutr-panel">
                    <div class="nutr-panel-title">Nutrition Facts</div>
{nutr}
                  </div>
                  <div class="expand-right">
    <div class="score-tile score-band-{g}">
      <div class="score-tile-header">
        <div class="score-grade-block">
          <div class="score-header-label">Ingredient Quality Grade</div>
          <div class="score-grade-row">
            <span class="score-band-badge">{g}</span>
            <span class="score-band-label">{grade_word(g)}</span>
          </div>
        </div>
        <div class="score-num-block">
          <div class="score-header-label">Ingredient Quality Score</div>
          <div class="score-number">{fnum(sc)}</div>
        </div>
      </div>
    <div class="score-breakdown">
      <div class="score-breakdown-bar">
        <div class="sbd-pos" style="width:{pp}%" title="Positive contributions: +{fnum(pos)}"></div>
        <div class="sbd-neg" style="width:{npc}%" title="Concern contributions: {fnum(neg)}"></div>
      </div>
      <div class="score-breakdown-labels">
        <span class="sbd-label-pos">+{fnum(pos)} positive</span>
        <span class="sbd-label-neg">{fnum(neg)} concerns</span>
      </div>
    </div>
      <div class="score-chips">{chips}</div>
      <div class="score-ingr-cols">
    <div class="ingr-col">
      <div class="ingr-col-label ingr-col-pos">Positive Ingredients</div>
      {pos_i}</div>
    <div class="ingr-col">
      <div class="ingr-col-label ingr-col-neg">Concern Ingredients</div>
      {neg_i}</div></div>
    </div>
                    <div class="ingr-block">
                      <div class="ingr-label">Ingredients</div><div class="ingr-text">{esc(ingr(b))}</div>
                    </div>
                  </div>
                </div>
              </div>
            </td>
          </tr>'''

def brand_table_html(bars, all_bars):
    ranker = Ranker(all_bars)
    return '\n'.join(brand_row_html(b, i, ranker) for i, b in enumerate(sort_for_list(bars)))

# ---------------------------------------------------------------------------
# Brand comparison table
# ---------------------------------------------------------------------------
SWEETENERS = [  # (label, regex) checked against ingredient text
    ('Sucralose', r'sucralose'), ('Acesulfame potassium', r'acesulfame'), ('Aspartame', r'aspartame'),
    ('Maltitol', r'maltitol'), ('Erythritol', r'erythritol'), ('Xylitol', r'xylitol'), ('Sorbitol', r'sorbitol'),
    ('Allulose', r'allulose'), ('Stevia', r'stevia|steviol|reb ?a'), ('Monk fruit', r'monk ?fruit|luo han'),
    ('Dates', r'\bdates?\b'), ('Honey', r'\bhoney\b'), ('Cane sugar', r'cane sugar|cane syrup|\bsugar\b'),
    ('Brown rice syrup', r'brown rice syrup'), ('Tapioca syrup', r'tapioca syrup'), ('Agave', r'agave'),
]

def sweetener_label(bars, k=2):
    """The (up to k) sweeteners found in at least half the brand's flavors,
    non-caloric first, e.g. 'Sucralose + maltitol'."""
    hits = []
    for label, pat in SWEETENERS:
        n = sum(1 for b in bars if re.search(pat, ingr(b), re.I))
        if n >= len(bars) / 2:
            hits.append(label)
    if not hits:
        return 'Mixed'
    top = hits[:k]
    return top[0] + ''.join(' + ' + x.lower() for x in top[1:])

def grade_pair_html(bars):
    best, worst = grade_range(bars)
    if best == worst:
        return f'<span class="table-grade-badge grade-{best}">{best}</span>'
    return (f'<span class="brand-compare-grade-pair"><span class="table-grade-badge grade-{best}">{best}</span>'
            f'<span class="brand-compare-grade-arrow">&rarr;</span><span class="table-grade-badge grade-{worst}">{worst}</span></span>')

def compare_row_html(name, bars, self_row=False):
    return f'''          <tr{' class="self-row"' if self_row else ''}>
            <td class="name">{esc(name)}</td>
            <td class="ctr">{grade_pair_html(bars)}</td>
            <td class="ctr">{avg([dict(x=p100(b)) for b in bars], 'x'):.1f}g</td>
            <td class="ctr col-hide-mobile">{avg(bars, 'Dietary Fiber (g)'):.1f}g</td>
            <td class="ctr col-hide-mobile">{avg(bars, 'Sugars (g)'):.1f}g</td>
            <td>{esc(sweetener_label(bars))}</td>
          </tr>'''

def compare_rows(self_name, groups):
    """groups: list of (display name, bars). First is the page's own brand."""
    return '\n'.join(compare_row_html(n, b, i == 0) for i, (n, b) in enumerate(groups))

# ---------------------------------------------------------------------------
# Pick tiles (brand "which flavor" and cross-brand alternatives)
# ---------------------------------------------------------------------------
def amazon_btn(b, label='Shop on Amazon'):
    return f'<a href="{esc(amazon_url(b))}" target="_blank" rel="noopener sponsored" class="amazon-link">{esc(label)}</a>' if amazon_url(b) else ''

def brand_pick_tile(label, flavors, text, buy=True):
    """flavors: list of bars. Buy buttons only for genuine buy recommendations."""
    names = '<br>'.join(esc(b['Flavor Name']) for b in flavors)
    btns = ''
    if buy:
        if len(flavors) == 1:
            btns = amazon_btn(flavors[0]) or (f'<a href="{esc(website_url(flavors[0]))}" target="_blank" rel="noopener" class="visit-link">Shop on Brand Site</a>' if website_url(flavors[0]) else '')
        else:
            btns = '\n          '.join(x for x in (amazon_btn(b, f"Shop {b['Flavor Name']}") for b in flavors) if x)
            btns = f'\n          {btns}\n        ' if btns else ''
    buy_html = f'\n        <div class="pick-tile-buy">{btns}</div>' if btns else ''
    return f'''      <div class="macro-card pick-tile">
        <div class="macro-label">{esc(label)}</div>
        <div class="pick-tile-flavor">{names}</div>
        <p>{esc(text)}</p>{buy_html}
      </div>'''

def alt_tile(label, b, reason):
    g = b.get('score_band')
    links = [x for x in [amazon_btn(b), (f'<a href="{esc(website_url(b))}" target="_blank" rel="noopener" class="visit-link">Shop on Brand Site</a>' if website_url(b) else '')] if x]
    return f'''      <div class="macro-card pick-tile">
        <div class="pick-tile-body">
          <div class="pick-tile-category">{esc(label)}</div>
          <div class="pick-tile-brand">{esc(b['Brand Name'])}</div>
          <div class="pick-tile-flavor-name">{esc(b['Flavor Name'])}</div>
          <p class="pick-tile-reason">{esc(reason)}</p>
        </div>
        <div class="pick-tile-footer">
          <div class="pick-tile-quality">
            <span class="pick-tile-quality-label">Ingredient Quality</span>
            <span class="table-grade-badge grade-{g}">{g}</span>
            <span class="pick-tile-quality-word">{grade_word(g)}</span>
          </div>
          <div class="bar-links">
            {(chr(10) + '            ').join(links)}
          </div>
        </div>
      </div>'''

def band_rank(b):
    return BAND_ORDER.index(b.get('score_band'))

# ---------------------------------------------------------------------------
# Brand-page grade-sync check
# ---------------------------------------------------------------------------
def brand_grade_sync(page, brand_bars_list, all_bars):
    by = {esc(b['Flavor Name']): b for b in brand_bars_list}
    probs = []
    rows = re.findall(r'<tr class="bar-row" onclick="toggleIngr\((\d+), this\)">\s*<td class="col-bar">\s*<div class="bar-flavor">(.*?)</div>.*?'
                      r'title="(\w+) &middot; score ([^"]*)">(\w)</span>.*?score-band-badge">(\w)</span>.*?score-number">([^<]*)<', page, re.S)
    seen = set()
    for idx, fl, word, tsc, badge, eg, esc_ in rows:
        b = by.get(fl)
        if b is None:
            probs.append(f'row {idx}: {fl} not in bars.js for this brand')
            continue
        seen.add(fl)
        g, s = b.get('score_band'), fnum(score(b))
        if not (badge == eg == g and word == grade_word(g)):
            probs.append(f'row {idx}: {fl} grade {badge}/{eg} vs bars.js {g}')
        if not (tsc == esc_ == s):
            probs.append(f'row {idx}: {fl} score {tsc}/{esc_} vs bars.js {s}')
    for fl in by:
        if fl not in seen:
            probs.append(f'missing row: {fl}')
    # best/worst cards
    for fl, sc, g in re.findall(r'<div class="bw-flavor">(.*?)</div>\s*<div class="bw-score">Score ([^ ]+) &middot; Grade (\w)', page):
        b = by.get(fl)
        if b is None or fnum(score(b)) != sc or b.get('score_band') != g:
            probs.append(f'best/worst card: {fl} {g} {sc} does not match bars.js')
    # cross-brand alternative tiles
    names = {(esc(b['Brand Name']), esc(b['Flavor Name'])): b for b in all_bars}
    for br, fl, g in re.findall(r'<div class="pick-tile-brand">(.*?)</div>\s*<div class="pick-tile-flavor-name">(.*?)</div>.*?table-grade-badge grade-(\w)"', page, re.S):
        b = names.get((br, fl))
        if b is None or b.get('score_band') != g:
            probs.append(f'alternative tile: {br} | {fl} grade {g} does not match bars.js')
    return probs, len(rows)

# ---------------------------------------------------------------------------
# Page plumbing shared by the brand build scripts (added for quest-bars)
# ---------------------------------------------------------------------------
import sys, json as _json

class Claims:
    """Collects copy claims that no longer hold. check() returns the bool so a
    sentence can be dropped or reworded instead of failing, when that's safe."""
    def __init__(self):
        self.failed = []
    def check(self, ok, claim):
        if not ok:
            self.failed.append(claim)
        return bool(ok)
    def stop_if_failed(self):
        if self.failed:
            print('COPY NEEDS REVIEW, page not written. These claims are no longer true in bars.js:')
            for c in self.failed:
                print('  -', c)
            sys.exit(1)

def names_and(xs):
    xs = list(xs)
    if not xs:
        return ''
    return xs[0] if len(xs) == 1 else ', '.join(xs[:-1]) + (',' if len(xs) > 2 else '') + ' and ' + xs[-1]

_WORDS = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve',
          'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen', 'twenty']
def num_word(n):
    return _WORDS[n] if 0 <= n < len(_WORDS) else str(n)

def P(b): return num(b.get('Protein (g)')) or 0
def CAL(b): return num(b.get('Calories')) or 0
def FIB(b): return num(b.get('Dietary Fiber (g)')) or 0
def SUG(b): return num(b.get('Sugars (g)')) or 0
def nm(b): return b['Flavor Name']
def has_ing(b, word): return word in ingr(b).lower()
def g1(x): return f'{x:.1f}'

def article_jsonld(headline, desc, url, brand_name, brand_url, published='2026-04-01'):
    d = {'@context': 'https://schema.org', '@type': 'Article', 'headline': headline, 'description': desc, 'url': url,
         'image': 'https://knowyourbar.com/bar_hero.png', 'datePublished': published, 'dateModified': today_iso(),
         'author': {'@type': 'Organization', 'name': 'Know Your Bar', 'url': 'https://knowyourbar.com'},
         'publisher': {'@type': 'Organization', 'name': 'Know Your Bar', 'url': 'https://knowyourbar.com'},
         'mainEntityOfPage': {'@type': 'WebPage', '@id': url},
         'about': {'@type': 'Brand', 'name': brand_name, 'url': brand_url}}
    if published is None:
        del d['datePublished']
    if brand_name is None:
        del d['about']
    return '<script type="application/ld+json">\n  ' + _json.dumps(d, indent=2, ensure_ascii=False).replace('\n', '\n  ') + '\n  </script>'

def faq_jsonld_brand(faqs):
    d = {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
        {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in faqs]}
    return '<script type="application/ld+json">\n  ' + _json.dumps(d, indent=2, ensure_ascii=False).replace('\n', '\n  ') + '\n  </script>'

def faq_items_brand(faqs):
    return '\n'.join(f'''
      <div class="faq-item">
        <button class="faq-q">{esc(q)}</button>
        <div class="faq-a">{esc(a)}</div>
      </div>''' for q, a in faqs) + '\n'

def social_html(title, desc, url):
    return f'''<meta property="og:type" content="article">
  <meta property="og:site_name" content="Know Your Bar">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(desc)}">
  <meta property="og:url" content="{url}">
  <meta property="og:image" content="https://knowyourbar.com/bar_hero.png">
  <!-- Twitter card -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(title)}">
  <meta name="twitter:description" content="{esc(desc)}">
  <meta name="twitter:image" content="https://knowyourbar.com/bar_hero.png">'''

def head_meta_html(title, desc):
    return f'''  <title>{esc(title)}</title>
  <meta name="description" content="{esc(desc)}">'''

def p100avg(bars):
    return avg([dict(x=p100(b)) for b in bars], 'x')

def no_as_sa(bars):
    return not any(has_tag(b, 'Artificial Sweeteners') or has_tag(b, 'Sugar Alcohols') for b in bars)

def compare_section_html(brand, groups, note_sentences):
    names = names_and(n for n, _ in groups[1:])
    return f'''<h2 class="brand-compare-title">How {esc(brand)} compares to {esc(names)}</h2>
      <div class="brand-compare-sub">All figures are per-brand averages across every flavor we've scored, not a single cherry-picked bar, and grade ranges show the full spread from that brand's best flavor to its worst.</div>
      <div class="brand-compare-table-wrap">
        <table class="brand-compare-table">
          <thead>
            <tr><th>Bar</th><th class="ctr">Grade range</th><th class="ctr" title="Protein per 100 calories">Protein/100cal</th><th class="ctr col-hide-mobile">Fiber avg</th><th class="ctr col-hide-mobile">Sugar avg</th><th>Sweetener</th></tr>
          </thead>
          <tbody>
{compare_rows(brand, groups)}
          </tbody>
        </table>
      </div>
      <div class="brand-compare-note">
        <div class="brand-compare-note-text">{esc(' '.join(note_sentences))}</div>
      </div>'''

def compare_note(brand, groups):
    """Data-driven comparison note: F swings, protein-efficiency rank, which
    brands skip artificial sweeteners and sugar alcohols, most consistent."""
    ordinal = ['', 'first', 'second', 'third', 'fourth', 'fifth', 'sixth']
    by_p100 = sorted(groups, key=lambda g: -p100avg(g[1]))
    rank = [n for n, _ in by_p100].index(brand) + 1
    out = []
    f_swing = [n for n, g in groups if grade_range(g)[1] == 'F']
    if len(f_swing) >= 2:
        out.append(f"{names_and(f_swing)} {'both' if len(f_swing) == 2 else 'all'} swing down to F depending on flavor, so a single-flavor snapshot overstates {'both' if len(f_swing) == 2 else 'them'}.")
    elif len(f_swing) == 1:
        out.append(f"{f_swing[0]} is the only brand here with a flavor that grades F.")
    out.append(f"{brand} {'leads this group' if rank == 1 else 'ranks ' + ordinal[rank] + ' in this group'} on protein efficiency at "
               f"{g1(p100avg(dict(groups)[brand]))}g per 100 calories"
               + ('.' if rank == 1 else f", behind {names_and(n for n, _ in by_p100[:rank - 1])}."))
    clean = [n for n, g in groups if no_as_sa(g)]
    if clean:
        out.append(f"{names_and(clean)} skip{'s' if len(clean) == 1 else ''} both artificial sweeteners and sugar alcohols across every flavor.")
    narrow = [n for n, g in groups if grade_range(g) in (('A', 'A'), ('A', 'B'))]
    if narrow:
        out.append(f"{names_and(narrow)} {'is' if len(narrow) == 1 else 'are'} the most consistent, A down to B with nothing lower.")
    return out

def pick_alternatives(all_bars, flag, exclude_brands, keyword, rules, cal_window=30):
    """rules: list of (label, eligible(b), sort_key(b), reason(b)). Candidates
    are other brands' flavors whose name contains `keyword`, within
    `cal_window` calories above the flagship, with a buy link. No repeats."""
    pool = [b for b in all_bars if b['Brand Name'] not in exclude_brands and keyword in b['Flavor Name'].lower()
            and CAL(b) and CAL(b) <= CAL(flag) + cal_window and (amazon_url(b) or website_url(b))]
    used, out = set(), []
    for label, ok, key, reason in rules:
        c = [b for b in pool if b['Key'] not in used and ok(b)]
        if not c:
            continue
        b = min(c, key=lambda x: tuple(key(x)) + (x['Brand Name'].lower(), nm(x).lower()))
        used.add(b['Key'])
        out.append((label if isinstance(label, str) else label(b), b, reason(b)))
    return out

def cal_delta(flag, b):
    d = CAL(flag) - CAL(b)
    return f'{fnum(abs(d))} fewer calories' if d > 0 else (f'{fnum(-d)} more calories' if d < 0 else 'the same calories')

def grade_vs(flag, b):
    if b['score_band'] == flag['score_band']:
        return f"Same {b['score_band']} grade as {nm(flag)}."
    return f"Grades {b['score_band']} instead of {flag['score_band']}."

def build_brand_page(page_path, regions, brand_bars_list, all_bars, claims):
    """Replace regions, stamp dates, run grade-sync + link QA, write."""
    claims.stop_if_failed()
    page = open(page_path, encoding='utf-8').read()
    for name, content in regions:
        page = replace_region(page, name, content)
    page = stamp_dates(page, today_iso())
    problems, n_rows = brand_grade_sync(page, brand_bars_list, all_bars)
    for bad in ['href="Yes"', 'href="None"']:
        if bad in page:
            problems.append(f'broken link field: {bad}')
    if '—' in page:
        problems.append('em dash in page')
    if problems:
        print('GRADE-SYNC / QA FAILED, page not written:')
        for p in problems:
            print('  ', p)
        sys.exit(1)
    open(page_path, 'w', encoding='utf-8').write(page)
    return n_rows
