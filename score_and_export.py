#!/usr/bin/env python3
"""
Know Your Bar — Score & Export Script
======================================
Run this whenever you add new bars to the database.

For bars already in the schema: uses the full pre-parsed
ingredient lines with position/clause weights for maximum accuracy.

For new bars not yet in the schema: auto-scores from the raw
ingredient string using alias + canonical matching.

Usage:
    Upload both files to Claude and say "run score_and_export"
    Claude runs this and returns bars.js ready for GitHub.

Files required:
    - Bar database Excel (BAR_DB_FILE)
    - Ingredient schema Excel (SCHEMA_FILE)
"""

import pandas as pd
import numpy as np
import json
import re
import os
from datetime import datetime
from collections import Counter

# ── Config ─────────────────────────────────────────────────
BAR_DB_FILE   = "KYB_-_New_Protein_Bar_Database__2026_.xlsx"
SCHEMA_FILE   = "knowyourbar_ingredient_schema_populated_v1.xlsx"
BAR_DB_SHEET  = "BarDB"
OUTPUT_FILE   = "bars.js"

# ── Score band thresholds ───────────────────────────────────
SCORE_BANDS = [
    (8,    float('inf'),     'A', 'Clean'),
    (4,    7.9999,           'B', 'Good'),
    (0,    3.9999,           'C', 'Okay'),
    (-3,  -0.0001,           'D', 'Poor'),
    (float('-inf'), -3.0001, 'F', 'Avoid'),
]

# ── Ingredient count adjustment bands ──────────────────────
COUNT_BANDS = [
    (0,  8,    0.05),
    (9,  12,   0.00),
    (13, 16,  -0.05),
    (17, 20,  -0.10),
    (21, 999, -0.15),
]

# ── % DV columns stored as decimals in Excel ───────────────
PCT_DV_COLS = [
    'Vitamin A (% DV)','Vitamin C (% DV)','Vitamin D (% DV)','Vitamin E (% DV)',
    'Vitamin K (% DV)','Thiamin / B1 (% DV)','Riboflavin / B2 (% DV)',
    'Niacin / B3 (% DV)','Vitamin B6 (% DV)','Vitamin B12 (% DV)',
    'Folic Acid (% DV)','Biotin (% DV)','Pantothenic Acid (% DV)',
    'Phosphorus (% DV)','Iodine (% DV)','Magnesium (% DV)','Zinc (% DV)',
    'Selenium (% DV)','Copper (% DV)','Manganese (% DV)','Chromium (% DV)',
    'Molybdenum (% DV)'
]

# ── Output columns ─────────────────────────────────────────
KEEP_COLS = [
    'Brand Name','Flavor Name','Size','Type','Website','Serving Size (g)',
    'Calories','Total Fat (g)','Saturated Fat (g)','Trans Fat (g)','Cholesterol (mg)',
    'Sodium (mg)','Total Carbohydrates (g)','Dietary Fiber (g)','Sugars (g)',
    'Sugar Alcohol (g)','Protein (g)',
    'Calcium (mg)','Iron (mg)','Potassium (mg)','Caffeine (mg)',
] + PCT_DV_COLS + [
    'Kosher (Y/N)','Vegan (Y/N)','Non-GMO (Y/N)','Soy Free (Y/N)',
    'Dairy Free (Y/N)','Gluten Free (Y/N)','Nut Free (Y/N)','Ingredients',
    'ingredient_score','score_band','score_band_label','score_explanation',
    'score_source'   # 'schema' | 'auto' | 'unscored'
]

# ── Common prefixes to strip during normalization ──────────
SKIP_PREFIXES = [
    'organic ','natural ','pure ','raw ','whole ','roasted ','unsweetened ',
    'dried ','dehydrated ','grass fed ','grass-fed ','non gmo ','certified ',
    'reduced fat ','low fat ','instant ','enriched ','unbleached ',
    'pasteurized ','homogenized '
]

# ── Clauses to truncate ingredient lists at ───────────────
SKIP_CLAUSES = [
    'contains less than','less than','may contain',
    'contains:','manufactured in','processed in','made in'
]

# ──────────────────────────────────────────────────────────


def normalize(text):
    text = str(text).lower().strip()
    text = re.sub(r'\*+', '', text)
    text = re.sub(r'\(.*?\)', '', text)
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


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
    weights = {1:1.0,2:0.85,3:0.72,4:0.61,5:0.52,6:0.44,7:0.37,8:0.31,
               9:0.26,10:0.22,11:0.20,12:0.18,13:0.17,14:0.16,15:0.15}
    if pos <= 15:
        return weights.get(pos, 0.15)
    return max(0.08, 0.15 - (pos - 15) * 0.007)


def build_lookups(alias_map, canonical):
    """Build alias and canonical lookup dicts"""
    alias_lookup = {}
    for _, row in alias_map.iterrows():
        key = normalize(str(row['normalized_alias_text']))
        if key not in alias_lookup:
            alias_lookup[key] = {
                'canonical_name': row['canonical_name'],
                'base_score': float(row['base_score']) if pd.notna(row['base_score']) else 0,
                'method': 'exact_alias'
            }

    canonical_lookup = {}
    for _, row in canonical.iterrows():
        key = normalize(str(row['canonical_name']))
        if key not in canonical_lookup:
            canonical_lookup[key] = {
                'canonical_name': row['canonical_name'],
                'base_score': float(row['base_score']) if pd.notna(row['base_score']) else 0,
                'method': 'canonical_match'
            }

    return alias_lookup, canonical_lookup


def lookup_ingredient(norm_text, alias_lookup, canonical_lookup):
    """Try to match a normalized ingredient text to a canonical"""
    # 1. Exact alias match
    if norm_text in alias_lookup:
        return {**alias_lookup[norm_text], 'confidence': 'high'}

    # 2. Strip common prefixes and retry
    stripped = norm_text
    for p in SKIP_PREFIXES:
        if stripped.startswith(p):
            stripped = stripped[len(p):]
            break
    if stripped != norm_text:
        if stripped in alias_lookup:
            return {**alias_lookup[stripped], 'confidence': 'auto', 'method': 'prefix_stripped'}
        if stripped in canonical_lookup:
            return {**canonical_lookup[stripped], 'confidence': 'auto', 'method': 'prefix_stripped_canonical'}

    # 3. Exact canonical name match
    if norm_text in canonical_lookup:
        return {**canonical_lookup[norm_text], 'confidence': 'auto'}

    # 4. Substring — longest alias contained in the ingredient text
    best, best_len = None, 0
    for key, val in alias_lookup.items():
        if key in norm_text and len(key) > best_len and len(key) > 4:
            best, best_len = val, len(key)
    if best:
        return {**best, 'confidence': 'auto', 'method': 'substring'}

    return None


def parse_and_score_ingredients(raw_text, alias_lookup, canonical_lookup):
    """Score a bar from its raw ingredient string (for new bars)"""
    if not raw_text or pd.isna(raw_text):
        return None, None, None, None, 'unscored', []

    text = str(raw_text).strip()
    lower = text.lower()
    for clause in SKIP_CLAUSES:
        idx = lower.find(clause)
        if idx > 0:
            text = text[:idx]
            lower = text.lower()

    # Parse top-level ingredients (flatten sub-ingredient parens)
    depth = 0
    cleaned = []
    for ch in text:
        if ch == '(':
            depth += 1
            cleaned.append(' ')
        elif ch == ')':
            depth -= 1
            cleaned.append(' ')
        elif ch == ',' and depth > 0:
            cleaned.append(';')
        else:
            cleaned.append(ch)
    parts = [p.strip() for p in ''.join(cleaned).split(',') if p.strip()]

    matched = []
    unmatched = []

    for i, part in enumerate(parts):
        norm = normalize(part)
        if not norm or len(norm) < 2:
            continue
        result = lookup_ingredient(norm, alias_lookup, canonical_lookup)
        pos_w = position_weight(i + 1)
        if result:
            matched.append({
                'canonical': result['canonical_name'],
                'score':     result['base_score'],
                'weight':    pos_w,
                'weighted':  result['base_score'] * pos_w,
                'confidence':result.get('confidence', 'auto'),
            })
        else:
            unmatched.append(part.strip())

    if not matched:
        return None, None, None, None, 'unscored', unmatched

    raw_score = sum(m['weighted'] for m in matched)
    n = len(matched)
    final = raw_score + get_count_adj(n)
    band, band_label = get_band(final)

    sorted_m = sorted(matched, key=lambda x: x['weighted'], reverse=True)
    top_pos = [m['canonical'] for m in sorted_m if m['weighted'] > 0.3][:3]
    top_neg = [m['canonical'] for m in sorted_m if m['weighted'] < -0.3][-3:]
    parts_ex = []
    if top_pos: parts_ex.append(f"Positives: {', '.join(top_pos)}")
    if top_neg: parts_ex.append(f"Concerns: {', '.join(top_neg)}")
    explanation = ' · '.join(parts_ex) if parts_ex else 'Neutral ingredient profile'

    source = 'auto'
    return round(final, 1), band, band_label, explanation, source, unmatched


def score_from_schema(pid, lines_by_pid, canonical_slim):
    """Score a bar using the pre-parsed schema ingredient lines"""
    if pid not in lines_by_pid:
        return None, None, None, None

    rows = lines_by_pid[pid]
    raw = rows['weighted'].sum()
    n = len(rows)
    final = raw + get_count_adj(n)
    band, band_label = get_band(final)

    sr = rows.sort_values('weighted', ascending=False)
    top_pos = sr[sr['weighted'] > 0.3]['canonical_name'].head(3).tolist()
    top_neg = sr[sr['weighted'] < -0.3]['canonical_name'].tail(3).tolist()
    parts = []
    if top_pos: parts.append(f"Positives: {', '.join(top_pos)}")
    if top_neg: parts.append(f"Concerns: {', '.join(top_neg)}")
    explanation = ' · '.join(parts) if parts else 'Neutral ingredient profile'

    return round(final, 1), band, band_label, explanation


def run():
    print("=" * 55)
    print("  Know Your Bar — Score & Export")
    print("=" * 55)

    # ── Load files ──────────────────────────────────────────
    print(f"\n► Loading bar database: {BAR_DB_FILE}")
    bars_df = pd.read_excel(BAR_DB_FILE, sheet_name=BAR_DB_SHEET)
    bars_df = bars_df.dropna(subset=['Brand Name', 'Flavor Name'], how='all')
    print(f"  {len(bars_df)} bars")

    print(f"\n► Loading ingredient schema: {SCHEMA_FILE}")
    xl = pd.ExcelFile(SCHEMA_FILE)
    ingr_lines = pd.read_excel(xl, sheet_name='Ingredient_Lines')
    canonical  = pd.read_excel(xl, sheet_name='Canonical_Ingredients')
    alias_map  = pd.read_excel(xl, sheet_name='Alias_Map')
    products   = pd.read_excel(xl, sheet_name='Products')
    print(f"  {len(products)} schema products")
    print(f"  {len(ingr_lines)} ingredient lines")
    print(f"  {len(canonical)} canonicals | {len(alias_map)} aliases")

    # ── Fix % DV columns ────────────────────────────────────
    for col in PCT_DV_COLS:
        if col in bars_df.columns:
            bars_df[col] = (bars_df[col] * 100).round(0).astype('Int64')

    # ── Build schema scoring structures ─────────────────────
    products['_key'] = (products['brand_name'].str.strip().str.lower() + '|' +
                        products['flavor_name'].str.strip().str.lower())
    key_to_pid = dict(zip(products['_key'], products['product_id']))

    canonical_slim = canonical[['canonical_id', 'base_score']].copy()
    scored_lines = ingr_lines.merge(canonical_slim, on='canonical_id', how='left')
    scored_lines['weighted'] = (
        scored_lines['base_score'].fillna(0) *
        scored_lines['effective_weight_default'].fillna(0)
    )
    scoring_only = scored_lines[scored_lines['include_in_scoring_default'] == 'Y'].copy()
    lines_by_pid = {pid: grp for pid, grp in scoring_only.groupby('product_id')}

    # ── Build auto-scoring lookups ───────────────────────────
    alias_lookup, canonical_lookup = build_lookups(alias_map, canonical)

    # ── Score all bars ───────────────────────────────────────
    print(f"\n► Scoring bars...")
    schema_count = auto_count = unscored_count = 0
    all_unmatched = []

    for idx, row in bars_df.iterrows():
        brand  = str(row.get('Brand Name', '')).strip()
        flavor = str(row.get('Flavor Name', '')).strip()
        key = f"{brand.lower()}|{flavor.lower()}"
        pid = key_to_pid.get(key)

        if pid and pid in lines_by_pid:
            # Use precise schema scoring
            s, b, bl, ex = score_from_schema(pid, lines_by_pid, canonical_slim)
            source = 'schema'
            schema_count += 1
        else:
            # Auto-score from raw ingredients
            ingr = row.get('Ingredients', '')
            s, b, bl, ex, source, unmatched = parse_and_score_ingredients(
                ingr, alias_lookup, canonical_lookup
            )
            if s is not None:
                auto_count += 1
                if unmatched:
                    all_unmatched.extend([
                        {'bar': f"{brand} - {flavor}", 'ingredient': u}
                        for u in unmatched
                    ])
            else:
                unscored_count += 1

        bars_df.at[idx, 'ingredient_score']  = s
        bars_df.at[idx, 'score_band']        = b
        bars_df.at[idx, 'score_band_label']  = bl
        bars_df.at[idx, 'score_explanation'] = ex
        bars_df.at[idx, 'score_source']      = source

    print(f"  Schema-scored (precise): {schema_count}")
    print(f"  Auto-scored (new bars):  {auto_count}")
    print(f"  Unscored (no ingredients): {unscored_count}")

    # ── Band distribution ────────────────────────────────────
    bands = Counter(bars_df['score_band'].dropna())
    print(f"\n  Score bands: " + " | ".join(f"{k}:{v}" for k,v in sorted(bands.items())))

    # ── Unmatched ingredient report ──────────────────────────
    if all_unmatched:
        print(f"\n  ⚠ {len(all_unmatched)} ingredient tokens couldn't be auto-matched.")
        print("  These bars are still scored but some ingredients scored as 0.")
        print("  Top unmatched (consider adding to schema):")
        unmatched_counts = Counter(u['ingredient'] for u in all_unmatched)
        for ingr, count in unmatched_counts.most_common(10):
            print(f"    {count}x  {ingr}")

    # ── Build output ─────────────────────────────────────────
    df_out = bars_df[[c for c in KEEP_COLS if c in bars_df.columns]].copy()
    df_out = df_out.where(pd.notna(df_out), None)
    for col in df_out.select_dtypes(include='object').columns:
        df_out[col] = df_out[col].apply(lambda x: x.strip() if isinstance(x, str) else x)

    bars = df_out.to_dict(orient='records')
    js = 'const BARS = ' + json.dumps(bars, separators=(',', ':')) + ';'
    js = js.replace(':NaN,', ':null,').replace(':NaN}', ':null}')

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(js)

    size_kb = os.path.getsize(OUTPUT_FILE) / 1024
    print(f"\n✓ bars.js written — {len(bars)} bars, {size_kb:.0f} KB")
    print(f"\nNext: upload bars.js to GitHub → Cloudflare deploys in ~60s")


if __name__ == '__main__':
    run()
