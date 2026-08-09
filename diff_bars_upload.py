#!/usr/bin/env python3
"""
diff_bars_upload.py — KnowYourBar database upload diff

WHY THIS EXISTS
----------------
Whenever a new bars.js is uploaded, previously-accurate page copy can silently
go stale if scores, grades, or macros changed for bars referenced on existing
pages. This script diffs the old and new bars.js so you know exactly what
changed before touching any page — new bars, removed bars, rescored bars,
grade changes, and macro corrections.

USAGE
-----
python3 diff_bars_upload.py old_bars.js new_bars.js
python3 diff_bars_upload.py old_bars.js new_bars.js --brand Quest

Run this immediately after any new bars.js upload, before writing or editing
any page. If it reports changes for a brand whose page already exists, that
page's copy needs a fresh verify_brand_data.py pass before it can be trusted.
"""

import argparse
import json


def load_bars(path):
    with open(path, encoding='utf-8') as f:
        content = f.read()
    content = content.replace('const BARS = ', '', 1).rstrip().rstrip(';')
    return json.loads(content)


def key(bar):
    return bar.get('Key') or f"{bar.get('Brand Name')} | {bar.get('Flavor Name')}"


TRACKED_FIELDS = [
    'ingredient_score', 'score_band', 'score_band_label',
    'Protein (g)', 'Calories', 'Sugars (g)', 'Sugar Alcohol (g)',
    'Dietary Fiber (g)', 'Total Fat (g)', 'Total Carbohydrates (g)',
    'Ingredients', 'score_insights',
]


def diff(old_path, new_path, brand_filter=None):
    old_bars = load_bars(old_path)
    new_bars = load_bars(new_path)

    if brand_filter:
        old_bars = [b for b in old_bars if brand_filter.lower() in (b.get('Brand Name') or '').lower()]
        new_bars = [b for b in new_bars if brand_filter.lower() in (b.get('Brand Name') or '').lower()]

    old_map = {key(b): b for b in old_bars}
    new_map = {key(b): b for b in new_bars}

    old_keys = set(old_map)
    new_keys = set(new_map)

    added = new_keys - old_keys
    removed = old_keys - new_keys
    shared = old_keys & new_keys

    print(f'=== bars.js diff: {old_path} -> {new_path} ===')
    if brand_filter:
        print(f'(filtered to brand match: "{brand_filter}")')
    print(f'Old count: {len(old_bars)}   New count: {len(new_bars)}\n')

    if added:
        print(f'--- ADDED ({len(added)}) ---')
        for k in sorted(added):
            b = new_map[k]
            print(f'  + {k}  [{b.get("score_band")}, score {b.get("ingredient_score")}]')
        print()

    if removed:
        print(f'--- REMOVED ({len(removed)}) ---')
        for k in sorted(removed):
            b = old_map[k]
            print(f'  - {k}  [{b.get("score_band")}, score {b.get("ingredient_score")}]')
        print()

    changed = []
    for k in sorted(shared):
        old_b, new_b = old_map[k], new_map[k]
        diffs = []
        for field in TRACKED_FIELDS:
            ov, nv = old_b.get(field), new_b.get(field)
            if ov != nv:
                diffs.append((field, ov, nv))
        if diffs:
            changed.append((k, diffs))

    if changed:
        print(f'--- CHANGED ({len(changed)} bars) ---')
        affected_brands = set()
        for k, diffs in changed:
            print(f'  ~ {k}')
            for field, ov, nv in diffs:
                ov_s = (str(ov)[:80] + '...') if ov and len(str(ov)) > 80 else ov
                nv_s = (str(nv)[:80] + '...') if nv and len(str(nv)) > 80 else nv
                print(f'      {field}: {ov_s!r} -> {nv_s!r}')
            affected_brands.add(new_map[k].get('Brand Name'))
        print(f'\nBrands with changed bars: {sorted(affected_brands)}')
        print('Run verify_brand_data.py for each of these brands before trusting existing page copy.')
    else:
        print('--- No field-level changes among bars present in both versions ---')

    if not added and not removed and not changed:
        print('\nNo changes detected at all. Database appears identical.')

    print('\nDone.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Diff two bars.js files to see what changed on a new upload.')
    parser.add_argument('old_bars', help='Path to the previous bars.js')
    parser.add_argument('new_bars', help='Path to the newly uploaded bars.js')
    parser.add_argument('--brand', default=None, help='Restrict diff to a single brand (substring match)')
    args = parser.parse_args()
    diff(args.old_bars, args.new_bars, args.brand)
