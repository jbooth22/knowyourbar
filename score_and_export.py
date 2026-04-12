"""
score_and_export.py — Know Your Bar scoring pipeline
=====================================================
Scores all bars from raw ingredient text and exports bars.js.

Usage:
    python score_and_export.py \
        --db "KYB - New Protein Bar Database (2026).xlsx" \
        --schema "knowyourbar_scoring_schema_v3.xlsx"

Output:
    bars.js  (written to current directory)

Requirements:
    pip install pandas openpyxl

Notes:
    - ALL bars are scored from raw ingredient text using the alias/canonical
      lookup tables. The schema's Ingredient_Lines and Products sheets are NOT
      used. Only Canonical_Ingredients and Alias_Map are loaded.
    - Sub-ingredients inside parentheses (e.g. protein blends) are scored at
      60% weight, reflecting their smaller quantity relative to top-level items.
    - Every scored bar gets insight chips using the same logic.
    - Run this script whenever new bars are added or ingredient data changes.
    - After running, upload bars.js to GitHub and update bar counts in HTML files.
"""

import argparse
import json
import os
import re
import sys
from collections import Counter

import pandas as pd


# ── Grade bands ───────────────────────────────────────────────────────────────
COUNT_BANDS = [
    (0,   8,   0.05),
    (9,  12,   0.00),
    (13, 16,  -0.05),
    (17, 20,  -0.10),
    (21, 999, -0.15),
]
SCORE_BANDS = [
    (8,    float('inf'), 'A', 'Clean'),
    (4,    7.9999,       'B', 'Good'),
    (0,    3.9999,       'C', 'Okay'),
    (-3,  -0.0001,       'D', 'Poor'),
    (float('-inf'), -3.0001, 'F', 'Avoid'),
]

# ── Ingredient signals ────────────────────────────────────────────────────────
ARTIFICIAL_SW  = ['sucralose', 'acesulfame', 'aspartame', 'saccharin']
SA_KEYWORDS    = ['erythritol', 'maltitol', 'xylitol', 'sorbitol',
                  'mannitol', 'isomalt', 'lactitol']
OIL_KEYWORDS   = ['palm oil', 'palm kernel oil', 'canola oil', 'soybean oil',
                  'hydrogenated', 'partially hydrogenated', 'palm fruit oil']
HIGH_OLEIC_EX  = ['high oleic']
SKIP_PREFIXES  = [
    'organic ', 'natural ', 'pure ', 'raw ', 'whole ', 'roasted ',
    'unsweetened ', 'dried ', 'dehydrated ', 'grass fed ', 'grass-fed ',
    'non gmo ', 'certified ', 'reduced fat ', 'low fat ', 'instant ',
    'enriched ', 'unbleached ', 'pasteurized ', 'homogenized ',
]
SKIP_CLAUSES   = [
    'contains less than', 'less than', 'may contain', 'contains:',
    'manufactured in', 'processed in', 'made in',
]
PCT_DV_COLS    = [
    'Vitamin A (% DV)', 'Vitamin C (% DV)', 'Vitamin D (% DV)',
    'Vitamin E (% DV)', 'Vitamin K (% DV)', 'Thiamin / B1 (% DV)',
    'Riboflavin / B2 (% DV)', 'Niacin / B3 (% DV)', 'Vitamin B6 (% DV)',
    'Vitamin B12 (% DV)', 'Folic Acid (% DV)', 'Biotin (% DV)',
    'Pantothenic Acid (% DV)', 'Phosphorus (% DV)', 'Iodine (% DV)',
    'Magnesium (% DV)', 'Zinc (% DV)', 'Selenium (% DV)', 'Copper (% DV)',
    'Manganese (% DV)', 'Chromium (% DV)', 'Molybdenum (% DV)',
]
KEEP_COLS      = [
    'Brand Name', 'Flavor Name', 'Key', 'Size', 'Type', 'Website',
    'Amazon Affiliate', 'Serving Size (g)', 'Calories', 'Total Fat (g)',
    'Saturated Fat (g)', 'Trans Fat (g)', 'Cholesterol (mg)', 'Sodium (mg)',
    'Total Carbohydrates (g)', 'Dietary Fiber (g)', 'Sugars (g)',
    'Sugar Alcohol (g)', 'Protein (g)', 'Calcium (mg)', 'Iron (mg)',
    'Potassium (mg)', 'Caffeine (mg)',
] + PCT_DV_COLS + [
    'Kosher (Y/N)', 'Vegan (Y/N)', 'Non-GMO (Y/N)', 'Soy Free (Y/N)',
    'Dairy Free (Y/N)', 'Gluten Free (Y/N)', 'Nut Free (Y/N)', 'Ingredients',
    'ingredient_score', 'score_pos', 'score_neg', 'score_band',
    'score_band_label', 'positive_ingredients', 'concern_ingredients',
    'score_insights', 'score_source',
]


# ── Helpers ───────────────────────────────────────────────────────────────────
def get_count_adj(n):
    for lo, hi, adj in COUNT_BANDS:
        if lo <= n <= hi:
            return adj
    return 0


def get_band(score):
    for lo, hi, band, label in SCORE_BANDS:
        if lo <= score <= hi:
            return band, label
    return 'F', 'Avoid'


def position_weight(pos):
    table = {
        1: 1.00, 2: 0.85, 3: 0.72, 4: 0.61, 5: 0.52,
        6: 0.44, 7: 0.37, 8: 0.31, 9: 0.26, 10: 0.22,
        11: 0.20, 12: 0.18, 13: 0.17, 14: 0.16, 15: 0.15,
    }
    return table.get(pos, max(0.08, 0.15 - (pos - 15) * 0.007))


def normalize(text):
    text = str(text).lower().strip()
    text = re.sub(r'\*+', '', text)
    text = re.sub(r'\(.*?\)', '', text)
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def build_lookup(alias_map, canonical):
    """Build alias and canonical lookup dicts."""
    al, cl = {}, {}
    for _, row in alias_map.iterrows():
        key = normalize(str(row['normalized_alias_text']))
        if key not in al:
            al[key] = {
                'canonical_name': row['canonical_name'],
                'category': str(row.get('category', 'other')),
                'base_score': float(row['base_score']) if pd.notna(row['base_score']) else 0,
            }
    for _, row in canonical.iterrows():
        key = normalize(str(row['canonical_name']))
        if key not in cl:
            cl[key] = {
                'canonical_name': row['canonical_name'],
                'category': str(row.get('category', 'other')),
                'base_score': float(row['base_score']) if pd.notna(row['base_score']) else 0,
            }
    return al, cl


def lookup_ingredient(norm, al, cl):
    if norm in al:
        return al[norm]
    stripped = norm
    for prefix in SKIP_PREFIXES:
        if stripped.startswith(prefix):
            stripped = stripped[len(prefix):]
            break
    if stripped != norm:
        if stripped in al:
            return al[stripped]
        if stripped in cl:
            return cl[stripped]
    if norm in cl:
        return cl[norm]
    best, best_len = None, 0
    for key, val in al.items():
        if key in norm and len(key) > best_len and len(key) > 4:
            best, best_len = val, len(key)
    return best


def parse_ingredients(raw):
    """
    Parse ingredient string into (text, top_level_position, weight_multiplier).

    Top-level ingredients get weight_multiplier=1.0.
    Sub-ingredients inside parentheses get weight_multiplier=0.6 — they are
    present in smaller amounts than their parent ingredient.
    """
    if not raw or pd.isna(raw):
        return []
    text = str(raw).strip()
    lower = text.lower()
    for clause in SKIP_CLAUSES:
        idx = lower.find(clause)
        if idx > 0:
            text = text[:idx]
            lower = text.lower()

    items = []
    top_pos = 0
    i = 0
    depth = 0
    current_top = []
    current_sub = []

    while i < len(text):
        ch = text[i]
        if ch == '(':
            depth += 1
            if depth == 1:
                top_text = ''.join(current_top).strip().rstrip(',').strip()
                if top_text:
                    top_pos += 1
                    items.append((top_text, top_pos, 1.0))
                current_top = []
                current_sub = []
        elif ch == ')':
            depth -= 1
            if depth == 0:
                sub_text = ''.join(current_sub).strip()
                if sub_text:
                    for sub_part in re.split(r'[,;]', sub_text):
                        sub_part = sub_part.strip()
                        if sub_part:
                            items.append((sub_part, top_pos, 0.6))
                current_sub = []
        elif ch == ',' and depth == 0:
            top_text = ''.join(current_top).strip()
            if top_text:
                top_pos += 1
                items.append((top_text, top_pos, 1.0))
            current_top = []
        elif depth == 0:
            current_top.append(ch)
        else:
            current_sub.append(ch)
        i += 1

    top_text = ''.join(current_top).strip()
    if top_text:
        top_pos += 1
        items.append((top_text, top_pos, 1.0))

    return items


def score_bar(raw, al, cl):
    """
    Score a single bar from its raw ingredient string.
    Returns (score, band, label, pos_str, neg_str, pos_total, neg_total, insight_str)
    or (None, None, None, '', '', None, None, '') if unscored.
    """
    if not raw or pd.isna(raw):
        return None, None, None, '', '', None, None, ''

    full_lower = str(raw).lower()
    parsed = parse_ingredients(raw)
    if not parsed:
        return None, None, None, '', '', None, None, ''

    matched = []
    for ing_text, top_pos, weight_mult in parsed:
        norm = normalize(ing_text)
        if not norm or len(norm) < 2:
            continue
        res = lookup_ingredient(norm, al, cl)
        if res:
            pw = position_weight(top_pos) * weight_mult
            matched.append({
                'canonical': res['canonical_name'],
                'category':  res['category'],
                'score':     res['base_score'],
                'weighted':  res['base_score'] * pw,
                'position':  top_pos,
                'is_sub':    weight_mult < 1.0,
            })

    if not matched:
        return None, None, None, '', '', None, None, ''

    top_level_count = max((m['position'] for m in matched), default=0)
    final = sum(m['weighted'] for m in matched) + get_count_adj(top_level_count)
    band, label = get_band(final)

    sm = sorted(matched, key=lambda x: x['weighted'], reverse=True)
    pos_items = [m['canonical'] for m in sm if m['weighted'] > 0.3][:3]
    neg_items = [m['canonical'] for m in sm if m['weighted'] < -0.3][-3:]
    pos_total = round(sum(m['weighted'] for m in matched if m['weighted'] > 0), 1)
    neg_total = round(sum(m['weighted'] for m in matched if m['weighted'] < 0), 1)

    insight_str = generate_insights(matched, full_lower, top_level_count)

    return (
        round(final, 1), band, label,
        ', '.join(pos_items), ', '.join(neg_items),
        pos_total, neg_total, insight_str,
    )


def generate_insights(matched, full_lower, top_level_count):
    """Generate insight chip string for a scored bar."""
    insights = []
    severity = {}

    top_only = [m for m in matched if not m['is_sub']]

    # Positive signals
    if top_only and top_only[0]['category'] == 'protein':
        insights.append(('Protein Leads', 'positive'))

    top5 = [m for m in matched if m['position'] <= 5]
    if any(m['category'] == 'protein' and m['score'] >= 3 for m in top5):
        insights.append(('Quality Protein Source', 'positive'))

    top3_top = [m for m in top_only if m['position'] <= 3]
    wf_positions = {m['position'] for m in top3_top if m['category'] == 'whole_food'}
    if len(wf_positions) >= 2:
        insights.append(('Whole Food Forward', 'positive'))

    if top_level_count <= 8:
        insights.append(('Short Clean List', 'positive'))

    # Neutral signals
    if any(m['category'] == 'vitamin_mineral' for m in matched):
        insights.append(('Fortified', 'neutral'))
    if top_level_count >= 18:
        insights.append(('Long Ingredient List', 'neutral'))

    # Concern signals
    if any(kw in full_lower for kw in ARTIFICIAL_SW):
        insights.append(('Artificial Sweeteners', 'concern'))
        sw_drag = abs(sum(m['weighted'] for m in matched if m['category'] == 'sweetener'))
        sw_top5 = any(m['category'] == 'sweetener' and m['position'] <= 5 for m in matched)
        severity['Artificial Sweeteners'] = 'elevated' if (sw_top5 or sw_drag > 2.0) else 'minor'

    if any(kw in full_lower for kw in SA_KEYWORDS):
        sa_m = [m for m in matched if any(kw in m['canonical'].lower() for kw in SA_KEYWORDS)]
        sa_drag = abs(sum(m['weighted'] for m in sa_m))
        sa_min  = min((m['position'] for m in sa_m), default=99)
        insights.append(('Sugar Alcohols', 'concern'))
        severity['Sugar Alcohols'] = 'elevated' if (sa_min <= 5 or sa_drag > 2.0) else 'minor'

    has_oil = False
    oil_drag = 0
    for kw in OIL_KEYWORDS:
        if kw in full_lower:
            idx = full_lower.find(kw)
            ctx = full_lower[max(0, idx - 20):idx + len(kw)]
            if not any(ex in ctx for ex in HIGH_OLEIC_EX):
                has_oil = True
                oil_drag = abs(sum(
                    m['weighted'] for m in matched
                    if m['category'] == 'fat_oil' and m['weighted'] < 0
                ))
                break
    if has_oil:
        insights.append(('Processed Oils', 'concern'))
        severity['Processed Oils'] = 'elevated' if oil_drag > 0.5 else 'minor'

    top3_cats = [m['category'] for m in top_only if m['position'] <= 3]
    if 'sweetener' in top3_cats:
        insights.append(('Sweetener Heavy', 'concern'))
        severity['Sweetener Heavy'] = 'elevated'

    prot_top = [m for m in top_only if m['category'] == 'protein']
    if prot_top:
        first_prot = min(prot_top, key=lambda x: x['position'])
        if 'collagen' in first_prot['canonical'].lower():
            insights.append(('Collagen Protein', 'concern'))
            severity['Collagen Protein'] = 'elevated'

    return '|'.join(
        f"{n}:{t}:{severity.get(n, '')}" if severity.get(n) else f"{n}:{t}"
        for n, t in insights
    )


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description='Score protein bars and export bars.js')
    parser.add_argument('--db',     required=True, help='Bar database Excel file')
    parser.add_argument('--schema', required=True, help='Scoring schema Excel file (v3)')
    parser.add_argument('--out',    default='bars.js', help='Output file (default: bars.js)')
    args = parser.parse_args()

    # Load database
    print(f'Loading database: {args.db}')
    df = pd.read_excel(args.db, sheet_name='BarDB')
    df = df.dropna(subset=['Brand Name', 'Flavor Name'], how='all')
    df = df.drop_duplicates(subset=['Brand Name', 'Flavor Name'], keep='last')
    print(f'  {len(df)} bars after deduplication')

    # Load schema (Canonical_Ingredients and Alias_Map only)
    print(f'Loading schema: {args.schema}')
    xl = pd.ExcelFile(args.schema)
    alias_map = pd.read_excel(xl, sheet_name='Alias_Map')
    canonical = pd.read_excel(xl, sheet_name='Canonical_Ingredients')
    print(f'  {len(canonical)} canonicals, {len(alias_map)} aliases')

    # Convert % DV columns
    for col in PCT_DV_COLS:
        if col in df.columns:
            df[col] = (df[col] * 100).round(0).astype('Int64')

    # Build lookup tables
    al, cl = build_lookup(alias_map, canonical)

    # Score all bars
    print('Scoring...')
    scored_count = unscored_count = 0
    for idx, row in df.iterrows():
        ingr = str(row.get('Ingredients', ''))
        s, band, label, pos_str, neg_str, pos_total, neg_total, insight_str = score_bar(ingr, al, cl)
        if s is not None:
            scored_count += 1
        else:
            unscored_count += 1
        df.at[idx, 'ingredient_score']     = s
        df.at[idx, 'score_band']           = band
        df.at[idx, 'score_band_label']     = label
        df.at[idx, 'positive_ingredients'] = pos_str
        df.at[idx, 'concern_ingredients']  = neg_str
        df.at[idx, 'score_pos']            = pos_total
        df.at[idx, 'score_neg']            = neg_total
        df.at[idx, 'score_insights']       = insight_str
        df.at[idx, 'score_source']         = 'auto'

    # Results summary
    bands = Counter(df['score_band'].dropna())
    with_chips = sum(1 for _, r in df.iterrows() if r.get('score_insights'))
    aff = sum(1 for _, r in df.iterrows() if str(r.get('Amazon Affiliate', '')).startswith('http'))

    print(f'\nResults:')
    print(f'  Scored:   {scored_count}')
    print(f'  Unscored: {unscored_count} (missing ingredient data)')
    print(f'  A={bands["A"]} B={bands["B"]} C={bands["C"]} D={bands["D"]} F={bands["F"]}')
    print(f'  With chips: {with_chips} ({with_chips/len(df)*100:.0f}%)')
    print(f'  Affiliate links: {aff}/{len(df)}')

    if unscored_count:
        print(f'\n  Unscored bars:')
        for _, row in df.iterrows():
            if not row.get('score_band'):
                print(f'    {row["Brand Name"]} | {row["Flavor Name"]}')

    # Export bars.js
    df_out = df[[c for c in KEEP_COLS if c in df.columns]].copy()
    df_out = df_out.where(pd.notna(df_out), None)
    for col in df_out.columns:
        if df_out[col].dtype == object:
            df_out[col] = df_out[col].apply(lambda x: x.strip() if isinstance(x, str) else x)

    bars_list = df_out.to_dict(orient='records')
    js = 'const BARS = ' + json.dumps(bars_list, separators=(',', ':')) + ';'
    js = js.replace(':NaN,', ':null,').replace(':NaN}', ':null}')

    with open(args.out, 'w') as f:
        f.write(js)

    size_kb = os.path.getsize(args.out) // 1024
    print(f'\nExported: {args.out} ({len(bars_list)} bars, {size_kb}KB)')
    print('Done. Upload bars.js to GitHub.')


if __name__ == '__main__':
    main()
