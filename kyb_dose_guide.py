"""Shared bar-list builder for the two "declared dose" guides (Caffeine,
Creatine). Those pages keep a compact 9-column table (BAR, CAL, PROT, dose,
FAT, CARB, FIBER, SUGAR, GRADE) with every expand panel server-rendered (no
lazy JSON), and a 4-cell rank grid where the dose cell replaces Sugar/Fiber.
The expand panel reuses kyb_guide_lib.expand_html so it matches every other
guide; only the rank grid (and, for creatine, one nutrition row) differ.
"""
from kyb_guide_lib import *


def dose_rows(bars, all_bars, *, field, data_attr, fmt, grid_label, grid_tag, extra_badges=None, nutr_extra=None):
    """bars: the page's qualifying bars. fmt(v) -> '85mg' / '1.2g'.
    grid_tag(b) -> [text, class] for the dose cell. Returns tbody inner html."""
    ranker = Ranker(all_bars)
    out = []
    for idx, b in enumerate(sort_for_list(bars)):
        g, sc = b.get('score_band'), score(b) or 0
        v = num(b.get(field)) or 0
        badges = extra_badges(b) if extra_badges else ''
        out.append(f'''<tr class="bar-row" data-idx="{idx}" data-score="{fnum(sc)}" data-grade="{g}" data-protein="{fnum(P(b))}" data-cal="{fnum(CAL(b))}" data-{data_attr}="{fnum(v)}" data-search="{esc(full(b).lower())}" onclick="toggleIngr({idx}, this)">
  <td class="col-bar">
    <div class="bar-brand">{esc(b['Brand Name'])}</div>
    <div class="bar-flavor">{esc(b['Flavor Name'])}</div>{badges}
    <svg class="row-expand-icon" width="7" height="12" viewBox="0 0 7 12" fill="none"><path d="M1 1L6 6L1 11" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
  </td>
  <td class="col-num col-hide-mobile">{fnum(CAL(b))}</td>
  <td class="col-num">{fnum(P(b))}</td>
  <td class="col-num">{fmt(v)}</td>
  <td class="col-num col-hide-mobile">{fnum(num(b.get('Total Fat (g)')))}</td>
  <td class="col-num col-hide-mobile">{fnum(num(b.get('Total Carbohydrates (g)')))}</td>
  <td class="col-num">{fnum(FIB(b))}</td>
  <td class="col-num">{fnum(num(b.get('Sugars (g)')))}</td>
  <td class="col-grade"><span class="table-grade-badge grade-{g}" title="{grade_word(g)} &middot; score {fnum(sc)}">{g}</span></td>
</tr>''')
        rec = lazy_record(b, idx, ranker)
        if nutr_extra:
            rec['nu'] = nutr_extra(b, rec['nu'])
        h = expand_html(rec)
        def cell(lbl, val, pair):
            return (f'<div class="macro-rank-cell"><span class="macro-rank-lbl">{lbl}</span>'
                    f'<span class="macro-rank-val">{val}</span><span class="macro-rank-tag {pair[1]}">{pair[0]}</span></div>')
        rk = rec['rk']
        grid = (cell('Protein', f'{fnum(P(b))}g', rk['p']) + cell('Calories', fnum(CAL(b)), rk['c'])
                + cell(grid_label, fmt(v), grid_tag(b)) + cell('Fat', f'{fnum(rec["ftv"])}g', rk['ft']))
        i = h.index('<div class="macro-rank-grid">') + len('<div class="macro-rank-grid">')
        j = h.index('</div><div class="expand-columns">')
        h = h[:i] + grid + h[j:]
        out.append(f'<tr class="ingr-row" id="ingr-{idx}" style="display:none;"><td colspan="9" class="ingr-cell"><div class="expand-content">{h}</div></td></tr>')
    return '\n'.join(out)


def dose_list_regions(bars, all_bars, heading, page_size=50, **kw):
    n = len(bars)
    return [('list-heading', f'<h2 class="section-title">{esc(heading)}</h2>'),
            ('result-count', f'<div class="gd-result-count" id="gd-result-count">Showing {min(page_size, n)} of {comma(n)} bars</div>'),
            ('bar-rows', dose_rows(bars, all_bars, **kw)),
            ('bar-data', '')]


def brand_notes_by_grade(bars):
    """Per-brand summary rows over a page's bars (only its qualifying flavors)."""
    by = {}
    for b in bars:
        by.setdefault(b['Brand Name'], []).append(b)
    rows = []
    for brand, bs in by.items():
        ab = [b for b in bs if b.get('score_band') in ('A', 'B')]
        rows.append(dict(brand=brand, bars=bs, total=len(bs), ab=len(ab)))
    return rows
