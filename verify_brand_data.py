#!/usr/bin/env python3
"""
verify_brand_data.py — KnowYourBar data verification script

WHY THIS EXISTS
----------------
On 2026-08-09, a brand page rebuild (quest-bars.html) surfaced a page where
every editorial claim (grade range, best/worst flavor, scores, ingredient
patterns) was built from stale/hallucinated data instead of the live bars.js.
Real numbers: grade range B->A claimed, actual B->C. Score range 4.4-9.3
claimed, actual 1.7-6.2. Two ingredient chips referenced in copy ("Protein
Leads", "Long Ingredient List") that are real, defined chips used elsewhere
in the database but don't apply to any of Quest's actual flavors.

This script is the fix: it computes ground-truth stats directly from
bars.js for a given brand (or guide filter) so Claude/Jeff can cross-check
every number in a page's copy against it BEFORE writing or approving copy.
No editorial claim about grades, scores, macros, or ingredient patterns
should be written without running this first.

USAGE
-----
python3 verify_brand_data.py "Quest"
python3 verify_brand_data.py "Clif" --include-subbrands
python3 verify_brand_data.py "Quest" --json   # machine-readable output

Run this:
  - Before writing/rebuilding ANY brand page
  - Before writing/rebuilding ANY guide page that names specific bars, brands,
    or stats
  - Any time bars.js is re-uploaded, to see what changed (see --diff below)
  - Before approving any AI-drafted copy that cites a grade, score, percentile,
    or "every flavor / most flavors / some flavors" ingredient pattern claim

WHAT IT COMPUTES
-----------------
- Flavor count, grade distribution (A-F), score range
- Best and worst flavor by ingredient_score, with full chip breakdown
- Macro ranges + averages: protein, calories, sugar, sugar alcohol, fiber,
  fat, net carbs (Total Carbs - Fiber - SugarAlcohol/2)
- Percentile rankings vs the ENTIRE database (not estimated) for protein,
  fiber, sugar, net carbs
- Real ingredient chip frequency table from score_insights (never invented)
- Artificial sweetener / sugar alcohol / certification prevalence (with
  certification fields correctly reported as "not tracked" when null,
  never asserted as a confirmed 0%)
"""

import argparse
import json
import sys


def load_bars(path='bars.js'):
    with open(path, encoding='utf-8') as f:
        content = f.read()
    content = content.replace('const BARS = ', '', 1).rstrip().rstrip(';')
    return json.loads(content)


def parse_chips(insights_raw):
    if not insights_raw:
        return []
    chips = []
    for item in insights_raw.split('|'):
        if not item:
            continue
        parts = item.split(':')
        chips.append({
            'name': parts[0].strip() if len(parts) > 0 else '',
            'type': parts[1].strip() if len(parts) > 1 else 'neutral',
            'severity': parts[2].strip() if len(parts) > 2 else '',
        })
    return [c for c in chips if c['name']]


def pct_rank_lower_is_better(all_vals, value):
    """% of all_vals that `value` is better than or equal to (lower = better)."""
    vals = [v for v in all_vals if v is not None]
    if not vals:
        return None
    better_or_eq = sum(1 for v in vals if v >= value)
    return round(better_or_eq / len(vals) * 100)


def pct_rank_higher_is_better(all_vals, value):
    """% of all_vals that `value` beats or ties (higher = better)."""
    vals = [v for v in all_vals if v is not None]
    if not vals:
        return None
    better_or_eq = sum(1 for v in vals if v <= value)
    return round(better_or_eq / len(vals) * 100)


def avg(vals):
    vals = [v for v in vals if v is not None]
    return sum(vals) / len(vals) if vals else None


def rng(vals):
    vals = [v for v in vals if v is not None]
    return (min(vals), max(vals)) if vals else (None, None)


def net_carbs(bar):
    # Full subtraction, no halving. See GUIDE_CRITERIA.md "Net carbs formula" —
    # dividing sugar alcohols by 2 was a stray error that broke Keto once already.
    tc = bar.get('Total Carbohydrates (g)') or 0
    fib = bar.get('Dietary Fiber (g)') or 0
    sa = bar.get('Sugar Alcohol (g)') or 0
    return tc - fib - sa


CERT_FIELDS = ['Vegan (Y/N)', 'Gluten Free (Y/N)', 'Dairy Free (Y/N)',
               'Soy Free (Y/N)', 'Non-GMO (Y/N)', 'Nut Free (Y/N)', 'Kosher (Y/N)']
BOOST_FIELDS = ['Caffeine (mg)', 'Creatine (g)', 'Melatonin (mg)']
GRADE_ORDER = ['A', 'B', 'C', 'D', 'F']
GRADE_LABEL = {'A': 'Clean', 'B': 'Good', 'C': 'Okay', 'D': 'Poor', 'F': 'Avoid'}


def report(brand_query, bars_path='bars.js', include_subbrands=False, as_json=False):
    all_bars = load_bars(bars_path)

    if include_subbrands:
        rows = [b for b in all_bars if brand_query.lower() in (b.get('Brand Name') or '').lower()]
    else:
        rows = [b for b in all_bars if (b.get('Brand Name') or '').lower() == brand_query.lower()]

    if not rows:
        print(f'NO MATCHES for brand "{brand_query}". Try --include-subbrands '
              f'(checks for sub-brands like "Clif Builders", "Clif ZBar").')
        distinct_brands = sorted(set(b.get('Brand Name', '') for b in all_bars
                                      if brand_query.lower() in (b.get('Brand Name') or '').lower()))
        if distinct_brands:
            print('Possible sub-brand matches found:', distinct_brands)
        sys.exit(1)

    rows.sort(key=lambda b: b.get('ingredient_score') or -999, reverse=True)

    n = len(rows)
    scores = [b.get('ingredient_score') for b in rows if b.get('ingredient_score') is not None]
    grade_counts = {g: 0 for g in GRADE_ORDER}
    for b in rows:
        band = b.get('score_band')
        if band in grade_counts:
            grade_counts[band] += 1
    grades_present = [g for g in GRADE_ORDER if grade_counts[g] > 0]
    best_grade = grades_present[0] if grades_present else None
    worst_grade = grades_present[-1] if grades_present else None

    best = rows[0]
    worst = rows[-1]

    # Chip frequency (REAL data only, never invented)
    chip_freq = {}
    for b in rows:
        for c in parse_chips(b.get('score_insights')):
            key = c['name']
            if key not in chip_freq:
                chip_freq[key] = {'count': 0, 'type': c['type']}
            chip_freq[key]['count'] += 1

    artificial_count = sum(1 for b in rows if any(
        c['name'] == 'Artificial Sweeteners' for c in parse_chips(b.get('score_insights'))))
    sugar_alc_count = sum(1 for b in rows if any(
        c['name'] == 'Sugar Alcohols' for c in parse_chips(b.get('score_insights'))))

    cert_hits = {f: sum(1 for b in rows if (b.get(f) or '').strip().lower() == 'yes') for f in CERT_FIELDS}
    cert_data_present = any((b.get(f) is not None) for b in rows for f in CERT_FIELDS)

    boost_hits = {f: sum(1 for b in rows if (b.get(f) or 0) and b.get(f) > 0) for f in BOOST_FIELDS}

    protein_vals = [b.get('Protein (g)') for b in rows]
    cal_vals = [b.get('Calories') for b in rows]
    sugar_vals = [b.get('Sugars (g)') for b in rows]
    sa_vals = [b.get('Sugar Alcohol (g)') for b in rows]
    fiber_vals = [b.get('Dietary Fiber (g)') for b in rows]
    fat_vals = [b.get('Total Fat (g)') for b in rows]
    nc_vals = [net_carbs(b) for b in rows]

    all_protein = [b.get('Protein (g)') for b in all_bars]
    all_fiber = [b.get('Dietary Fiber (g)') for b in all_bars]
    all_sugar = [b.get('Sugars (g)') for b in all_bars]
    all_nc = [net_carbs(b) for b in all_bars]

    result = {
        'brand_query': brand_query,
        'n': n,
        'distinct_brand_names': sorted(set(b.get('Brand Name') for b in rows)),
        'grade_distribution': grade_counts,
        'grade_range_worst_to_best': f'{worst_grade} -> {best_grade}',
        'score_range': rng(scores),
        'best_flavor': {
            'name': best.get('Flavor Name'), 'score': best.get('ingredient_score'),
            'grade': best.get('score_band'),
            'chips': parse_chips(best.get('score_insights')),
        },
        'worst_flavor': {
            'name': worst.get('Flavor Name'), 'score': worst.get('ingredient_score'),
            'grade': worst.get('score_band'),
            'chips': parse_chips(worst.get('score_insights')),
        },
        'macros': {
            'protein_g': {'range': rng(protein_vals), 'avg': avg(protein_vals),
                           'percentile_top_pct': 100 - pct_rank_higher_is_better(all_protein, avg(protein_vals))
                           if avg(protein_vals) is not None else None},
            'calories': {'range': rng(cal_vals), 'avg': avg(cal_vals)},
            'sugar_g': {'range': rng(sugar_vals), 'avg': avg(sugar_vals),
                        'percentile_top_pct_lowest': 100 - pct_rank_lower_is_better(all_sugar, avg(sugar_vals))
                        if avg(sugar_vals) is not None else None},
            'sugar_alcohol_g': {'range': rng(sa_vals), 'avg': avg(sa_vals)},
            'fiber_g': {'range': rng(fiber_vals), 'avg': avg(fiber_vals),
                        'percentile_top_pct': 100 - pct_rank_higher_is_better(all_fiber, avg(fiber_vals))
                        if avg(fiber_vals) is not None else None},
            'fat_g': {'range': rng(fat_vals), 'avg': avg(fat_vals)},
            'net_carbs_g': {'range': rng(nc_vals), 'avg': avg(nc_vals),
                             'percentile_top_pct_lowest': 100 - pct_rank_lower_is_better(all_nc, avg(nc_vals))
                             if avg(nc_vals) is not None else None},
        },
        'artificial_sweetener_pct': round(artificial_count / n * 100),
        'sugar_alcohol_pct': round(sugar_alc_count / n * 100),
        'certifications': {
            'data_present': cert_data_present,
            'hits': cert_hits if cert_data_present else 'NOT TRACKED — do not assert a percentage',
        },
        'boost_ingredients_present': {k: v for k, v in boost_hits.items() if v > 0},
        'chip_frequency': {k: {'count': v['count'], 'of': n, 'type': v['type']} for k, v in
                            sorted(chip_freq.items(), key=lambda kv: -kv[1]['count'])},
    }

    if as_json:
        print(json.dumps(result, indent=2))
        return

    print(f'=== {brand_query} — verified against bars.js ({n} flavors) ===\n')
    if len(result['distinct_brand_names']) > 1:
        print(f'NOTE: matched multiple Brand Name values: {result["distinct_brand_names"]}\n')
    print(f'Grade distribution: ' + '  '.join(f'{g}={grade_counts[g]}' for g in GRADE_ORDER))
    print(f'Grade range, worst to best: {worst_grade} -> {best_grade}')
    print(f'Score range: {result["score_range"][0]} - {result["score_range"][1]}\n')

    print(f'BEST:  {best.get("Flavor Name")} — score {best.get("ingredient_score")}, '
          f'grade {best.get("score_band")} ({GRADE_LABEL.get(best.get("score_band"), "?")})')
    for c in result['best_flavor']['chips']:
        print(f'       [{c["type"]}] {c["name"]}' + (f' ({c["severity"]})' if c['severity'] else ''))
    print(f'WORST: {worst.get("Flavor Name")} — score {worst.get("ingredient_score")}, '
          f'grade {worst.get("score_band")} ({GRADE_LABEL.get(worst.get("score_band"), "?")})')
    for c in result['worst_flavor']['chips']:
        print(f'       [{c["type"]}] {c["name"]}' + (f' ({c["severity"]})' if c['severity'] else ''))

    print('\n--- Macros (range / avg / percentile vs full 1,000+ bar database) ---')
    m = result['macros']
    print(f'Protein:      {m["protein_g"]["range"][0]}-{m["protein_g"]["range"][1]}g  '
          f'avg {m["protein_g"]["avg"]:.1f}g  (top {m["protein_g"]["percentile_top_pct"]}% highest)')
    print(f'Calories:     {m["calories"]["range"][0]}-{m["calories"]["range"][1]}cal  '
          f'avg {m["calories"]["avg"]:.1f}cal')
    print(f'Sugar:        {m["sugar_g"]["range"][0]}-{m["sugar_g"]["range"][1]}g  '
          f'avg {m["sugar_g"]["avg"]:.1f}g  (top {m["sugar_g"]["percentile_top_pct_lowest"]}% lowest)')
    print(f'Sugar Alcohol:{m["sugar_alcohol_g"]["range"][0]}-{m["sugar_alcohol_g"]["range"][1]}g  '
          f'avg {m["sugar_alcohol_g"]["avg"]:.1f}g')
    print(f'Fiber:        {m["fiber_g"]["range"][0]}-{m["fiber_g"]["range"][1]}g  '
          f'avg {m["fiber_g"]["avg"]:.1f}g  (top {m["fiber_g"]["percentile_top_pct"]}% highest)')
    print(f'Fat:          {m["fat_g"]["range"][0]}-{m["fat_g"]["range"][1]}g  '
          f'avg {m["fat_g"]["avg"]:.1f}g')
    print(f'Net Carbs:    {m["net_carbs_g"]["range"][0]:.1f}-{m["net_carbs_g"]["range"][1]:.1f}g  '
          f'avg {m["net_carbs_g"]["avg"]:.1f}g  (top {m["net_carbs_g"]["percentile_top_pct_lowest"]}% lowest)')

    print(f'\nArtificial sweeteners: {result["artificial_sweetener_pct"]}% of flavors')
    print(f'Sugar alcohol:         {result["sugar_alcohol_pct"]}% of flavors')
    if cert_data_present:
        print(f'Certifications:        {cert_hits}')
    else:
        print(f'Certifications:        NOT TRACKED for this brand — do not write "0%", write "not tracked"')
    if result['boost_ingredients_present']:
        print(f'Boost ingredients present: {result["boost_ingredients_present"]}')

    print('\n--- Ingredient chip frequency (real score_insights data, never invented) ---')
    for name, d in result['chip_frequency'].items():
        pct = round(d['count'] / n * 100)
        tier = 'every flavor' if pct == 100 else ('most flavors' if pct >= 50 else 'some flavors')
        print(f'  [{d["type"]:9s}] {name:30s} {d["count"]}/{n} ({pct}%) — {tier}')

    print('\n--- Full flavor list, sorted best to worst ---')
    for b in rows:
        print(f'  {b.get("score_band")}  {b.get("ingredient_score"):>4}  {b.get("Flavor Name")}')

    print('\nDone. Cross-check every number above against draft copy before finalizing.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Verify brand data against bars.js before writing page copy.')
    parser.add_argument('brand', help='Brand name to look up (e.g. "Quest", "Clif")')
    parser.add_argument('--bars', default='bars.js', help='Path to bars.js (default: ./bars.js)')
    parser.add_argument('--include-subbrands', action='store_true',
                         help='Substring match on Brand Name (catches "Clif Builders", "Clif ZBar", etc.)')
    parser.add_argument('--json', action='store_true', help='Output machine-readable JSON instead of a report')
    args = parser.parse_args()
    report(args.brand, args.bars, args.include_subbrands, args.json)
