#!/usr/bin/env python3
"""
Rebuild the data on quest-vs-rxbar.html from live bars.js.

    python3 build_quest_vs_rxbar.py

Opens the live page and rewrites only the <!-- kyb:NAME --> regions (see
kyb_guide_lib.py / kyb_brand_lib.py). Nav, footer, fonts, canonical URL, the
Article JSON-LD headline, the H1 and the Explore CTA are never touched.

Every number, grade, chip and flavor name comes from bars.js. Chips are the
real score_insights chips, never hand-written labels. Keto counts use the
Keto guide's formula from GUIDE_CRITERIA.md. Structural claims go through
claims.check(); the build stops if one fails.
"""
from kyb_brand_lib import *

PAGE = 'quest-vs-rxbar.html'
A_NAME, B_NAME = 'Quest', 'RXBAR'

ALL = load_bars()
QA_ = sort_for_list([b for b in ALL if b['Brand Name'] == A_NAME])
RB = sort_for_list([b for b in ALL if b['Brand Name'] == B_NAME])
C = Claims()
NQ, NR = len(QA_), len(RB)

def st(bars):
    return dict(n=len(bars), rng=range_words(bars), sc=avg(bars, 'ingredient_score'), p=avg(bars, 'Protein (g)'),
                cal=avg(bars, 'Calories'), sug=avg(bars, 'Sugars (g)'), fib=avg(bars, 'Dietary Fiber (g)'),
                nc=sum(nc(b) for b in bars) / len(bars), p100=p100avg(bars),
                art=sum(1 for b in bars if has_tag(b, 'Artificial Sweeteners')),
                sa=sum(1 for b in bars if has_tag(b, 'Sugar Alcohols')),
                keto=sum(1 for b in bars if GUIDE_FILTERS['keto-protein-bars'](b)),
                gc=grade_counts(bars), nc_max=max(nc(b) for b in bars), nc_min=min(nc(b) for b in bars))
SQ, SR = st(QA_), st(RB)
def grades_slash(bars): return ' / '.join(g for g in BAND_ORDER if grade_counts(bars)[g])
def grades_dash(bars):
    b, w = grade_range(bars)
    return b if b == w else f'{b}-{w}'
A_COUNT_R = SR['gc']['A']
C.check(SQ['art'] == NQ and SQ['sa'] == NQ, 'every Quest flavor has artificial sweeteners and sugar alcohols')
C.check(SR['art'] == 0 and SR['sa'] == 0, 'RXBAR has no artificial sweeteners or sugar alcohols')
C.check(all(has_ing(b, 'sucralose') and has_ing(b, 'erythritol') for b in QA_), 'every Quest flavor has sucralose and erythritol')
C.check(SR['sc'] > SQ['sc'] and SQ['p'] > SR['p'] and SQ['nc'] < SR['nc'] and SQ['sug'] < SR['sug'] and SQ['p100'] > SR['p100'],
        'Quest wins protein/net carbs/sugar, RXBAR wins ingredient score')
C.check(A_COUNT_R > NR / 2 and SQ['gc']['A'] == 0, 'RXBAR is mostly A, Quest has no A')
C.check(SR['keto'] == 0, 'no RXBAR flavor qualifies as keto')

def win(a, b, higher=True):
    if a == b:
        return 'tie', 'tie'
    return ('win-a', 'tie') if (a > b) == higher else ('tie', 'win-b')

# ---------------------------------------------------------------------------
# Scorecard
# ---------------------------------------------------------------------------
def card(name, bars, s, side):
    art_txt = f'All {s["n"]} flavors' if s['art'] == s['n'] else ('None' if s['art'] == 0 else f'{s["art"]} of {s["n"]} flavors')
    art_col = '#c83020' if s['art'] else '#2a7a1f'
    rows = [('Flavors scored', str(s['n'])), ('Grade range', grades_dash(bars)), ('Avg ingredient score', g1(s['sc'])),
            ('Avg protein', f"{g1(s['p'])}g"), ('Avg calories', fnum(round(s['cal']))), ('Avg sugar', f"{g1(s['sug'])}g"),
            ('Avg net carbs', f"{g1(s['nc'])}g")]
    body = '\n'.join(f'''        <div class="vs-stat-row">
          <span class="vs-stat-label">{lbl}</span>
          <span class="vs-stat-val">{val}</span>
        </div>''' for lbl, val in rows)
    return f'''      <div class="vs-brand-card brand-{side}">
        <div class="vs-brand-name brand-{side}">{name}</div>
{body}
        <div class="vs-stat-row">
          <span class="vs-stat-label">Artificial sweeteners</span>
          <span class="vs-stat-val" style="color:{art_col};">{art_txt}</span>
        </div>
      </div>'''
SCORECARD = f'''<h2>Quest vs RXBAR at a glance</h2>
    <div class="vs-scorecard">

{card(A_NAME, QA_, SQ, 'a')}

      <div class="vs-divider">vs</div>

{card(B_NAME, RB, SR, 'b')}

    </div>'''

# ---------------------------------------------------------------------------
# Overview
# ---------------------------------------------------------------------------
P_GAP = round(100 * (SQ['p'] - SR['p']) / SQ['p'])
HP = [b for b in RB if has_ing(b, 'pea protein')]
C.check(all(b['score_band'] != 'A' for b in HP) and all(b['score_band'] == 'A' for b in RB if b not in HP),
        "RXBAR's non-A flavors are exactly the pea-protein (high-protein) flavors")
C.check(all(has_ing(b, 'polydextrose') for b in QA_), 'every Quest flavor has polydextrose')
OVERVIEW = f'''<h2>What makes these two bars different</h2>
    <p>{esc(f"Quest and RXBAR are built on different philosophies. Quest engineers its macros: high protein, very low sugar, and minimal net carbs by using artificial sweeteners and sugar alcohols. That lets it hit {g1(SQ['p'])}g protein at {fnum(round(SQ['cal']))} calories with {g1(SQ['nc'])}g net carbs. The trade-off is ingredient quality, which sits at {grades_slash(QA_).replace(' / ', ' or ')} across all {NQ} flavors.")}</p>
    <p>{esc(f"RXBAR goes the other direction. Dates, egg whites, and nuts are the core of most flavors. No artificial sweeteners, no sugar alcohols. The result is an average ingredient score of {g1(SR['sc'])} and {A_COUNT_R} out of {NR} flavors earning an A. The trade-off is macros. Dates carry natural sugar, which is why RXBARs average {g1(SR['sug'])}g sugar and {g1(SR['nc'])}g net carbs. Protein averages {g1(SR['p'])}g, which is {P_GAP}% less per bar than Quest.")}</p>

    <div class="vs-callout brand-a">
      <div class="vs-callout-label">Quest</div>
      {esc(f"Quest achieves low sugar and high protein by using sucralose and erythritol as sweeteners, plus polydextrose as a prebiotic fiber. That lets it hit {g1(SQ['p'])}g protein and {g1(SQ['nc'])}g net carbs in {fnum(round(SQ['cal']))} calories without natural sugars. The average ingredient score of {g1(SQ['sc'])} reflects that sweetener dependence along with the use of isolated protein fractions rather than whole food protein sources. Every flavor grades {grades_slash(QA_).replace(' / ', ' or ')}, not A. That is a meaningful gap from RXBAR on ingredient quality, but it is a deliberate engineering choice, not an oversight.")}
    </div>
    <div class="vs-callout brand-b">
      <div class="vs-callout-label">RXBAR</div>
      {esc(f"RXBAR's classic ingredient list is simple: egg whites, dates, nuts, and not much else. That is why {A_COUNT_R} of {NR} flavors earn an A. The {num_word(len(HP))} {grades_slash(HP)}-grade flavors are the newer high-protein line, which adds pea protein and agave nectar. The cost of the whole-food approach is macros. Dates are high in natural sugar, which is why RXBARs average {g1(SR['sug'])}g sugar and {g1(SR['nc'])}g net carbs. That is fine if you are not tracking net carbs, but it rules them out for keto entirely.")}
    </div>'''

# ---------------------------------------------------------------------------
# Head-to-head
# ---------------------------------------------------------------------------
def h2h_row(metric, a, b, ca, cb):
    return f'''          <tr>
            <td class="metric">{metric}</td>
            <td class="val {ca}">{a}</td>
            <td class="val {cb}">{b}</td>
          </tr>'''
rows = []
w = win(SQ['sc'], SR['sc']); rows.append(h2h_row('Ingredient score', g1(SQ['sc']), g1(SR['sc']), *w))
rows.append(h2h_row('Grade', grades_slash(QA_), f"A ({A_COUNT_R} of {NR})", 'tie', 'win-b'))
w = win(SQ['p'], SR['p']); rows.append(h2h_row('Protein per bar', f"{g1(SQ['p'])}g", f"{g1(SR['p'])}g", *w))
w = win(SQ['cal'], SR['cal'], False); rows.append(h2h_row('Calories per bar', fnum(round(SQ['cal'])), fnum(round(SR['cal'])), *w))
w = win(SQ['p100'], SR['p100']); rows.append(h2h_row('Protein per 100 cal', f"{g1(SQ['p100'])}g", f"{g1(SR['p100'])}g", *w))
w = win(SQ['sug'], SR['sug'], False); rows.append(h2h_row('Sugar per bar', f"{g1(SQ['sug'])}g", f"{g1(SR['sug'])}g", *w))
w = win(SQ['nc'], SR['nc'], False); rows.append(h2h_row('Net carbs', f"{g1(SQ['nc'])}g", f"{g1(SR['nc'])}g", *w))
w = win(SQ['fib'], SR['fib']); rows.append(h2h_row('Fiber per bar', f"{g1(SQ['fib'])}g", f"{g1(SR['fib'])}g", *w))
def of(k, s): return f"All {s['n']} flavors" if s[k] == s['n'] else ('None' if s[k] == 0 else f"{s[k]} of {s['n']}")
rows.append(h2h_row('Artificial sweeteners', of('art', SQ), of('art', SR), *win(SQ['art'] / NQ, SR['art'] / NR, False)))
rows.append(h2h_row('Sugar alcohols', of('sa', SQ), of('sa', SR), *win(SQ['sa'] / NQ, SR['sa'] / NR, False)))
rows.append(h2h_row('Keto friendly', f"{SQ['keto']} of {NQ}" if SQ['keto'] < NQ else f"All {NQ} flavors", f"{SR['keto']} of {NR}",
                    *win(SQ['keto'] / NQ, SR['keto'] / NR)))
wff_q, wff_r = sum(has_tag(b, 'Whole Food Forward') for b in QA_), sum(has_tag(b, 'Whole Food Forward') for b in RB)
rows.append(h2h_row('Whole Food Forward flavors', f"{wff_q} of {NQ}", f"{wff_r} of {NR}", *win(wff_q / NQ, wff_r / NR)))
rows.append(h2h_row('Flavors in lineup', str(NQ), str(NR), 'tie', 'tie'))
H2H = f'''<h2>The numbers, head to head</h2>
    <p>Every metric that matters, side by side. No curated selection. Keto friendly uses our Keto guide's screen: 8g or less net carbs, 10g+ protein, 8g+ fat, no maltitol.</p>
    <div class="bar-table-wrap">
      <table class="compare-table">
        <colgroup>
          <col>
          <col>
          <col>
        </colgroup>
        <thead>
          <tr>
            <th>Metric</th>
            <th class="col-a">Quest (avg)</th>
            <th class="col-b">RXBAR (avg)</th>
          </tr>
        </thead>
        <tbody>
{chr(10).join(rows)}
        </tbody>
      </table>
    </div>'''

# ---------------------------------------------------------------------------
# Grades, best flavors
# ---------------------------------------------------------------------------
def dist(name, bars, side):
    c = grade_counts(bars)
    segs = '\n'.join(f'          <div class="grade-seg" style="background:{GRADE_COLOR[g]};flex:{c[g]}" title="{grade_word(g)}: {c[g]} bar{"s" if c[g] != 1 else ""}">{g}</div>'
                     for g in BAND_ORDER if c[g])
    counts = ' &middot; '.join(f'{c[g]} {g} ({grade_word(g)})' for g in BAND_ORDER if c[g])
    return f'''      <div>
        <div class="vs-grade-block-label brand-{side}">{name} - {len(bars)} flavors</div>
        <div class="grade-dist">
{segs}
        </div>
        <p class="grade-dist-counts">{counts}</p>
      </div>'''
GRADES = f'''<h2>Ingredient quality grade distribution</h2>
    <p>How each brand's full lineup breaks down by ingredient quality grade. This is every flavor we've scored, not a hand-picked few.</p>
    <div class="vs-grade-pair">

{dist(A_NAME, QA_, 'a')}

{dist(B_NAME, RB, 'b')}

    </div>'''

def chips_html(b, indent):
    return ('\n' + indent).join(bchip(*c) for c in chip_list(b))
def buy_btn(b, cls):
    if amazon_url(b):
        return f'<a href="{esc(amazon_url(b))}"\n             target="_blank" rel="noopener sponsored" class="{cls}">Shop on Amazon</a>'
    if website_url(b):
        return f'<a href="{esc(website_url(b))}"\n             target="_blank" rel="noopener" class="{cls}">Shop on Brand Site</a>'
    return ''
BQ, BR_ = QA_[0], RB[0]
def best_card(name, b, side):
    return f'''      <div class="vs-best-card brand-{side}">
        <div class="vs-best-brand-tag brand-{side}">{name}</div>
        <div class="vs-best-flavor">{esc(nm(b))}</div>
        <div class="vs-best-score">Score {g1(score(b))} &middot; Grade {b['score_band']}</div>
        <div class="bw-chips">
          {chips_html(b, '          ')}
        </div>
        <div style="margin-top:.85rem;">
          {buy_btn(b, 'cta-amazon')}
        </div>
      </div>'''
BEST = f'''<h2>Best flavor from each brand by ingredient quality</h2>
    <div class="vs-best-pair">

{best_card(A_NAME, BQ, 'a')}

{best_card(B_NAME, BR_, 'b')}

    </div>'''

# ---------------------------------------------------------------------------
# Who should buy
# ---------------------------------------------------------------------------
q_nc_max = SQ['nc_max']
BUY = f'''<h2>The right bar for your goal</h2>
    <p>Neither brand wins outright. It depends on what you are optimizing for.</p>
    <div class="vs-buy-pair">

      <div class="vs-buy-card brand-a">
        <div class="vs-buy-title brand-a">Buy Quest if:</div>
        <ul class="vs-buy-list">
          <li>You are tracking macros and want the most protein per calorie</li>
          <li>{esc(f"You are on keto and need low net carbs (every Quest flavor lands at {fnum(q_nc_max)}g or less)")}</li>
          <li>Artificial sweeteners and sugar alcohols are not a concern for you</li>
          <li>{esc(f"You want more flavor variety ({NQ} options vs {NR})" if NQ > NR else "You want the higher-protein option")}</li>
          <li>You are lifting and protein is the priority above all else</li>
        </ul>
      </div>

      <div class="vs-buy-card brand-b">
        <div class="vs-buy-title brand-b">Buy RXBAR if:</div>
        <ul class="vs-buy-list">
          <li>Ingredient quality matters more than hitting a specific protein target</li>
          <li>You want to avoid artificial sweeteners and sugar alcohols entirely</li>
          <li>You prefer whole food ingredients over engineered formulas</li>
          <li>{esc(f"You are not on keto and about {fnum(round(SR['sug']))}g of natural sugar from dates works for you")}</li>
          <li>You want a bar that reads like a recipe, not a supplement label</li>
        </ul>
      </div>

    </div>'''
C.check(SQ['p100'] > SR['p100'], 'Quest has more protein per calorie')

# ---------------------------------------------------------------------------
# Flavor tables
# ---------------------------------------------------------------------------
N_ING = top_level_ingredient_count
TOP_R = min([b for b in RB if b['score_band'] == grade_range(RB)[0]], key=lambda b: (N_ING(ingr(b)), -(score(b) or 0), nm(b)))
TOP_Q = BQ
def vs_row(b, idx, top):
    g = b['score_band']
    sub = ''
    if amazon_url(b):
        sub = f'''
                  <div class="bar-sub">
                    <a href="{esc(amazon_url(b))}" target="_blank" rel="noopener sponsored" class="buy-btn">Shop on Amazon</a>
                    <span class="expand-hint">tap for ingredients</span>
                  </div>'''
    return f'''
              <tr class="bar-row" onclick="toggleIngr({idx}, this)">
                <td class="bar-name-cell">
                  <div class="bar-flavor">{esc(nm(b))}{' <span class="top-pick-badge">Top Pick</span>' if top else ''}</div>{sub}
                </td>
                <td class="grade-cell"><span class="grade-badge" style="background:{GRADE_COLOR[g]}" title="{grade_word(g)}">{g}</span></td>
                <td class="num-cell">{g1(score(b))}</td>
                <td class="num-cell">{fnum(P(b))}g</td>
                <td class="num-cell">{fnum(CAL(b))}</td>
                <td class="num-cell">{fnum(SUG(b))}g</td>
              </tr>
              <tr class="ingr-row" id="ingr-{idx}">
                <td colspan="6" class="ingr-cell">
                  <div class="ingr-inner">
                    <div class="ingr-macros">
                      <span><strong>Protein</strong> {fnum(P(b))}g</span>
                      <span><strong>Calories</strong> {fnum(CAL(b))}</span>
                      <span><strong>Sugar</strong> {fnum(SUG(b))}g</span>
                      <span><strong>Fiber</strong> {fnum(FIB(b))}g</span>
                      <span><strong>Net Carbs</strong> {fnum(nc(b))}g</span>
                    </div>
                    <strong>Ingredients: </strong>{esc(ingr(b))}
                    <div class="ingr-chips">
                      {chips_html(b, '                      ')}
                    </div>
                  </div>
                </td>
              </tr>'''
def table(name, bars, side, start, top):
    rows = ''.join(vs_row(b, start + i, b is top) for i, b in enumerate(bars))
    return f'''      <div class="vs-flavor-table-block">
        <div class="vs-flavor-table-header">
          <span class="vs-flavor-table-brand brand-{side}">{name}</span>
          <span class="vs-flavor-table-count">{len(bars)} flavors &middot; {grades_dash(bars)} grades</span>
        </div>
        <div class="bar-table-wrap">
          <table>
            <thead>
              <tr>
                <th>Flavor</th>
                <th>Grade</th>
                <th>Score</th>
                <th>Protein</th>
                <th>Cal</th>
                <th>Sugar</th>
              </tr>
            </thead>
            <tbody>
{rows}

            </tbody>
          </table>
        </div>
      </div>'''
FLAVORS = f'''<h2>All flavors ranked by ingredient quality</h2>
    <p>Every flavor scored. Tap any row to expand the full ingredient list.</p>
    <div class="vs-flavor-tables">

{table(A_NAME, QA_, 'a', 0, TOP_Q)}

{table(B_NAME, RB, 'b', NQ, TOP_R)}

    </div>'''

# ---------------------------------------------------------------------------
# Bottom line + picks
# ---------------------------------------------------------------------------
top_list = ', '.join(x.split('(')[0].strip().lower() for x in re.split(r',(?![^()]*\))', ingr(TOP_R)))
BOTTOM = f'''<h2>Bottom line</h2>
    <p>The Quest vs RXBAR decision comes down to one question: do you care more about what is in the bar or what macros the bar delivers? Quest engineers macros. RXBAR sources ingredients. Both are legitimate choices depending on your goals, and neither is obviously wrong for the person it is designed for.</p>
    <p>{esc(f"If you are counting net carbs, need {fnum(round(SQ['p']))}g protein per bar, or are on keto, Quest wins on almost every macro metric. If you are avoiding artificial sweeteners, prefer whole food ingredients, and do not need the bar to double as a protein supplement, RXBAR is the better choice. The ingredient quality difference ({g1(SR['sc'])} vs {g1(SQ['sc'])}) is substantial. That gap reflects real differences in what you are eating.")}</p>

    <div class="vs-pick">
      <div class="vs-pick-eyebrow">Our Top Bar Pick</div>
      <div class="vs-pick-brand">RXBAR {esc(nm(TOP_R))}</div>
      <div class="vs-pick-reason">{esc(f"When the choice is between engineered macros and actual food, we pick actual food. RXBAR {nm(TOP_R)} scores {g1(score(TOP_R))} and earns {'an' if TOP_R['score_band'] in 'AF' else 'a'} {TOP_R['score_band']} with a {N_ING(ingr(TOP_R))}-ingredient list: {top_list}. You can read it in 10 seconds and recognize every item on it. If you need {fnum(round(SQ['p']))}g protein in under 200 calories with minimal carbs, Quest {nm(TOP_Q)} is the call instead. But as a bar we would eat daily, it is the {nm(TOP_R)}.")}</div>
      {buy_btn(TOP_R, 'vs-pick-amazon')}
    </div>

    <div class="vs-brand-verdict">
      <div class="vs-brand-verdict-eyebrow">Our Brand Pick</div>
      <div class="vs-brand-verdict-title">RXBAR</div>
      <div class="vs-brand-verdict-reason">{esc(f"We pick RXBAR as the better brand. The {g1(SR['sc'] - SQ['sc'])}-point gap in average ingredient score ({g1(SR['sc'])} vs {g1(SQ['sc'])}) reflects a fundamentally different approach to what goes into a bar. Dates, egg whites, and nuts are things your body knows what to do with. Sucralose, erythritol, and polydextrose are not terrible, but they are engineering solutions, not food. If your goal is protein efficiency or keto macros, Quest is the rational choice. But if you are asking which brand we trust more as a food company, it is RXBAR by a clear margin.")}</div>
    </div>'''
C.check(CAL(TOP_Q) < 200 and P(TOP_Q) >= 20, 'the Quest alternative pick is under 200 calories with 20g+ protein')
C.check(not any(w in ingr(TOP_R).lower() for w in ('agave', 'pea protein', 'isolate')), 'the RXBAR top pick is a simple whole-food list')

RELATED = f'''
      <a href="/quest-bars" class="explore-more-card">
        <div class="explore-more-title">Full Quest Review</div>
        <div class="explore-more-desc">All {NQ} flavors scored with full ingredient breakdowns, macro data, and grade distribution.</div>
      </a>
      <a href="/rxbar-review" class="explore-more-card">
        <div class="explore-more-title">Full RXBAR Review</div>
        <div class="explore-more-desc">All {NR} flavors scored with full ingredient breakdowns, macro data, and grade distribution.</div>
      </a>
      <a href="/no-artificial-sweeteners" class="explore-more-card">
        <div class="explore-more-title">No Artificial Sweeteners Guide</div>
        <div class="explore-more-desc">The best protein bars with zero sucralose, acesulfame K, or aspartame. RXBAR is a standout. Quest is not.</div>
      </a>'''

# ---------------------------------------------------------------------------
# FAQ + head
# ---------------------------------------------------------------------------
low_nc_q = min(QA_, key=lambda b: (nc(b), band_rank(b), nm(b)))
n_low_nc = sum(1 for b in QA_ if nc(b) == nc(low_nc_q))
r2, r3 = RB[1], RB[2]
FAQS = [
    ('Which is healthier, Quest or RXBAR?',
     f"It depends on what healthy means to you. RXBAR scores significantly higher on ingredient quality. {A_COUNT_R} of {NR} flavors earn an A grade, "
     f"they use whole food ingredients, and contain zero artificial sweeteners. Quest bars score {grades_slash(QA_).replace(' / ', ' or ')}, use sucralose "
     f"and erythritol in every flavor, but deliver {g1(SQ['p'])}g protein at {g1(SQ['nc'])}g net carbs. If ingredient quality is your priority, RXBAR "
     "wins. If protein efficiency or keto macros matter more, Quest wins."),
    ('Which has more protein, Quest or RXBAR?',
     f"Quest bars average {g1(SQ['p'])}g protein per bar. RXBARs average {g1(SR['p'])}g. Quest also wins on protein efficiency: {g1(SQ['p100'])}g per "
     f"100 calories versus {g1(SR['p100'])}g for RXBAR. If protein is the primary goal, Quest is the more efficient choice."),
    ('Do Quest bars have artificial sweeteners?',
     f"Yes. All {NQ} Quest flavors we scored contain sucralose, plus erythritol as a sugar alcohol. That combination lets Quest hit about "
     f"{fnum(round(SQ['sug']))}g sugar and {g1(SQ['nc'])}g net carbs per bar without natural sugars, but it also holds ingredient grades to "
     f"{grades_slash(QA_).replace(' / ', ' or ')}."),
    ('Do RXBAR bars have artificial sweeteners?',
     f"No. Zero of the {NR} RXBAR flavors we scored contain sucralose, acesulfame potassium, aspartame, or saccharin. RXBARs are sweetened mostly by "
     f"dates (plus honey or agave in a few flavors), which is why they average {g1(SR['sug'])}g of sugar per bar."),
    ('Are Quest bars keto friendly?',
     f"Mostly. Every Quest flavor lands between {fnum(SQ['nc_min'])}g and {fnum(SQ['nc_max'])}g net carbs, averaging {g1(SQ['nc'])}g. "
     f"{SQ['keto']} of {NQ} also clear the rest of our Keto guide's screen (10g+ protein and 8g+ fat); the others fall short only on fat. "
     f"RXBARs average {g1(SR['nc'])}g net carbs and none qualify for keto."),
    ('Which Quest flavor is the best?',
     f"{nm(BQ)} scores highest among Quest flavors at {g1(score(BQ))} and earns {'an' if BQ['score_band'] in 'AF' else 'a'} {BQ['score_band']} grade. "
     f"{nm(low_nc_q)} {'ties for' if n_low_nc > 1 else 'has'} the lowest net carbs at {fnum(nc(low_nc_q))}g if keto is the priority."),
    ('Which RXBAR flavor is the best?',
     f"{nm(BR_)} scores highest at {g1(score(BR_))} and earns {'an' if BR_['score_band'] in 'AF' else 'a'} {BR_['score_band']} grade, followed by "
     f"{nm(r2)} at {g1(score(r2))} and {nm(r3)} at {g1(score(r3))}. For the simplest list, {nm(TOP_R)} has just {N_ING(ingr(TOP_R))} ingredients and "
     f"still grades {TOP_R['score_band']}."),
    ('Which bar has less sugar, Quest or RXBAR?',
     f"Quest wins significantly on sugar. Quest bars average {g1(SQ['sug'])}g of sugar per bar. RXBARs average {g1(SR['sug'])}g. The difference is "
     "that Quest uses artificial sweeteners and sugar alcohols to achieve low sugar, while RXBAR uses dates, which naturally contribute most of their "
     "sugar content. Both approaches are intentional trade-offs."),
]
nonketo_q = [b for b in QA_ if not GUIDE_FILTERS['keto-protein-bars'](b)]
C.check(all(nc(b) <= 8 and P(b) >= 10 and not has_maltitol_family(b) for b in nonketo_q), 'Quest flavors that miss keto miss only on fat')

TITLE = 'Quest vs RXBAR: Which Is Actually Healthier? | Know Your Bar'
DESC = (f"Quest: {fnum(round(SQ['p']))}g protein, {g1(SQ['nc'])}g net carbs, {grades_slash(QA_).replace(' / ', '/')} grade. RXBAR: "
        f"{fnum(round(SR['p']))}g protein, {g1(SR['nc'])}g net carbs, mostly A. Opposite trade-offs. Full breakdown across all {NQ + NR} flavors.")
OG_TITLE = 'Quest vs RXBAR: Ingredient Quality, Protein, and Macros Compared'
OG_DESC = (f"Quest delivers {fnum(round(SQ['p']))}g protein at {g1(SQ['nc'])}g net carbs. RXBAR earns mostly A grades with whole food ingredients. "
           "Full data-driven comparison across all flavors.")
C.check(len(DESC) <= 160, f'meta description length {len(DESC)}')
nc_mult = round(SR['nc'] / SQ['nc'])
hero_txt = (f"Two of the most popular protein bars on the market, and they make opposite trade-offs. Quest scores "
            f"{grades_slash(QA_).replace(' / ', '/')} on ingredients but leads on protein and net carbs. RXBAR earns mostly A grades with "
            f"whole food ingredients but has {nc_mult}x the net carbs. Here is the full data breakdown across all {NQ + NR} flavors.")
HERO = f'<p class="hero-sub">{esc(hero_txt)}</p>'

# ---------------------------------------------------------------------------
# Assemble + QA
# ---------------------------------------------------------------------------
C.stop_if_failed()
page = open(PAGE, encoding='utf-8').read()
for name, content in [('head-meta', head_meta_html(TITLE, DESC)), ('jsonld-faq', faq_jsonld_brand(FAQS)), ('social', social_html(OG_TITLE, OG_DESC, 'https://knowyourbar.com/quest-vs-rxbar')),
                      ('hero', HERO), ('scorecard', SCORECARD), ('overview', OVERVIEW), ('h2h', H2H), ('grades', GRADES), ('best', BEST),
                      ('buy', BUY), ('flavors', FLAVORS), ('bottom', BOTTOM), ('related', RELATED), ('faq', faq_items_brand(FAQS))]:
    page = replace_region(page, name, content)
page = stamp_dates(page, today_iso())

problems = []
expected = QA_ + RB
rows = re.findall(r'toggleIngr\((\d+), this\)">\s*<td class="bar-name-cell">\s*<div class="bar-flavor">(.*?)(?: <span class="top-pick-badge">Top Pick</span>)?</div>.*?'
                  r'title="(\w+)">(\w)</span></td>\s*<td class="num-cell">([^<]*)</td>', page, re.S)
if len(rows) != len(expected):
    problems.append(f'{len(rows)} flavor rows on page, expected {len(expected)}')
for idx, fl, word, g, sc in rows:
    b = expected[int(idx)]
    if esc(nm(b)) != fl or g != b['score_band'] or word != grade_word(g) or sc != g1(score(b)):
        problems.append(f'row {idx}: {fl} {g} {sc} vs bars.js {nm(b)} {b["score_band"]} {g1(score(b))}')
for fl, sc, g in re.findall(r'<div class="vs-best-flavor">(.*?)</div>\s*<div class="vs-best-score">Score ([^ ]+) &middot; Grade (\w)', page):
    b = next((x for x in (BQ, BR_) if esc(nm(x)) == fl), None)
    if b is None or g1(score(b)) != sc or b['score_band'] != g:
        problems.append(f'best card {fl} {g} {sc} does not match bars.js')
for bad in ['href="Yes"', 'href="None"', '—']:
    if bad in page:
        problems.append(f'forbidden: {bad!r}')
if problems:
    print('GRADE-SYNC / QA FAILED, page not written:')
    for p in problems:
        print('  ', p)
    sys.exit(1)
open(PAGE, 'w', encoding='utf-8').write(page)
print(f'{PAGE}: Quest {NQ} flavors {SQ["rng"]} avg {g1(SQ["sc"])} | RXBAR {NR} flavors {SR["rng"]} avg {g1(SR["sc"])}')
print(f'Keto (guide screen): Quest {SQ["keto"]}/{NQ}, RXBAR {SR["keto"]}/{NR}')
print(f'Best: Quest {nm(BQ)} {g1(score(BQ))} | RXBAR {nm(BR_)} {g1(score(BR_))} | Top bar pick: RXBAR {nm(TOP_R)}')
print(f'Grade-sync: {len(rows)} flavor rows and both best-flavor cards checked against bars.js, 0 mismatches')
