#!/usr/bin/env python3
"""
Know Your Bar — Score & Export Script
======================================
Scores all bars and exports bars.js for GitHub.

For bars in the schema: uses pre-parsed ingredient lines.
For new bars: auto-scores from raw ingredient string.
Merges flags and explanation tokens from the scores CSV if present.

Files required (upload all to Claude when running):
    BAR_DB_FILE   — your bar database Excel
    SCHEMA_FILE   — ingredient schema Excel
    SCORES_CSV    — optional: ChatGPT scores CSV for flags/tokens
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
SCORES_CSV    = "knowyourbar_bar_scores_merge.csv"   # optional
BAR_DB_SHEET  = "BarDB"
OUTPUT_FILE   = "bars.js"

SCORE_BANDS = [
    (8,    float('inf'),     'A', 'Clean'),
    (4,    7.9999,           'B', 'Good'),
    (0,    3.9999,           'C', 'Okay'),
    (-3,  -0.0001,           'D', 'Poor'),
    (float('-inf'), -3.0001, 'F', 'Avoid'),
]
COUNT_BANDS = [
    (0,8,0.05),(9,12,0.0),(13,16,-0.05),(17,20,-0.10),(21,999,-0.15)
]
PCT_DV_COLS = [
    'Vitamin A (% DV)','Vitamin C (% DV)','Vitamin D (% DV)','Vitamin E (% DV)',
    'Vitamin K (% DV)','Thiamin / B1 (% DV)','Riboflavin / B2 (% DV)',
    'Niacin / B3 (% DV)','Vitamin B6 (% DV)','Vitamin B12 (% DV)',
    'Folic Acid (% DV)','Biotin (% DV)','Pantothenic Acid (% DV)',
    'Phosphorus (% DV)','Iodine (% DV)','Magnesium (% DV)','Zinc (% DV)',
    'Selenium (% DV)','Copper (% DV)','Manganese (% DV)','Chromium (% DV)',
    'Molybdenum (% DV)'
]
KEEP_COLS = [
    'Brand Name','Flavor Name','Size','Type','Website','Serving Size (g)',
    'Calories','Total Fat (g)','Saturated Fat (g)','Trans Fat (g)','Cholesterol (mg)',
    'Sodium (mg)','Total Carbohydrates (g)','Dietary Fiber (g)','Sugars (g)',
    'Sugar Alcohol (g)','Protein (g)','Calcium (mg)','Iron (mg)','Potassium (mg)',
    'Caffeine (mg)',
] + PCT_DV_COLS + [
    'Kosher (Y/N)','Vegan (Y/N)','Non-GMO (Y/N)','Soy Free (Y/N)',
    'Dairy Free (Y/N)','Gluten Free (Y/N)','Nut Free (Y/N)','Ingredients',
    'ingredient_score','score_band','score_band_label',
    'score_explanation','score_flags','score_source'
]
SKIP_PREFIXES = [
    'organic ','natural ','pure ','raw ','whole ','roasted ','unsweetened ',
    'dried ','dehydrated ','grass fed ','grass-fed ','non gmo ','certified ',
    'reduced fat ','low fat ','instant ','enriched ','unbleached ',
    'pasteurized ','homogenized '
]
SKIP_CLAUSES = [
    'contains less than','less than','may contain',
    'contains:','manufactured in','processed in','made in'
]


def normalize(text):
    text = str(text).lower().strip()
    text = re.sub(r'\*+', '', text)
    text = re.sub(r'\(.*?\)', '', text)
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

def get_count_adj(n):
    for lo,hi,adj in COUNT_BANDS:
        if lo<=n<=hi: return adj
    return 0

def get_band(score):
    for lo,hi,band,label in SCORE_BANDS:
        if lo<=score<=hi: return band,label
    return 'F','Avoid'

def position_weight(pos):
    w = {1:1.0,2:0.85,3:0.72,4:0.61,5:0.52,6:0.44,7:0.37,8:0.31,
         9:0.26,10:0.22,11:0.20,12:0.18,13:0.17,14:0.16,15:0.15}
    return w.get(pos, max(0.08, 0.15-(pos-15)*0.007)) if pos<=15 else max(0.08,0.15-(pos-15)*0.007)

def build_lookups(alias_map, canonical):
    al, cl = {}, {}
    for _,row in alias_map.iterrows():
        key = normalize(str(row['normalized_alias_text']))
        if key not in al:
            al[key] = {'canonical_name':row['canonical_name'],
                       'base_score':float(row['base_score']) if pd.notna(row['base_score']) else 0}
    for _,row in canonical.iterrows():
        key = normalize(str(row['canonical_name']))
        if key not in cl:
            cl[key] = {'canonical_name':row['canonical_name'],
                       'base_score':float(row['base_score']) if pd.notna(row['base_score']) else 0}
    return al, cl

def lookup_ing(norm, al, cl):
    if norm in al: return al[norm]
    stripped = norm
    for p in SKIP_PREFIXES:
        if stripped.startswith(p): stripped=stripped[len(p):]; break
    if stripped != norm:
        if stripped in al: return al[stripped]
        if stripped in cl: return cl[stripped]
    if norm in cl: return cl[norm]
    best,best_len = None,0
    for key,val in al.items():
        if key in norm and len(key)>best_len and len(key)>4:
            best,best_len=val,len(key)
    return best

def auto_score(raw, al, cl):
    if not raw or pd.isna(raw): return None,None,None,None
    text=str(raw).strip(); lower=text.lower()
    for clause in SKIP_CLAUSES:
        idx=lower.find(clause)
        if idx>0: text=text[:idx]; lower=text.lower()
    depth=0; cleaned=[]
    for ch in text:
        if ch=='(': depth+=1; cleaned.append(' ')
        elif ch==')': depth-=1; cleaned.append(' ')
        elif ch==',' and depth>0: cleaned.append(';')
        else: cleaned.append(ch)
    parts=[p.strip() for p in ''.join(cleaned).split(',') if p.strip()]
    matched=[]
    for i,part in enumerate(parts):
        norm=normalize(part)
        if not norm or len(norm)<2: continue
        res=lookup_ing(norm,al,cl)
        if res:
            pw=position_weight(i+1)
            matched.append({'canonical':res['canonical_name'],'score':res['base_score'],
                            'weighted':res['base_score']*pw})
    if not matched: return None,None,None,None
    final=sum(m['weighted'] for m in matched)+get_count_adj(len(matched))
    band,bl=get_band(final)
    sm=sorted(matched,key=lambda x:x['weighted'],reverse=True)
    top_pos=[m['canonical'] for m in sm if m['weighted']>0.3][:3]
    top_neg=[m['canonical'] for m in sm if m['weighted']<-0.3][-3:]
    parts_ex=[]
    if top_pos: parts_ex.append(f"Positives: {', '.join(top_pos)}")
    if top_neg: parts_ex.append(f"Concerns: {', '.join(top_neg)}")
    ex=' · '.join(parts_ex) if parts_ex else 'Neutral ingredient profile'
    return round(final,1),band,bl,ex


def run():
    print("="*55)
    print("  Know Your Bar — Score & Export")
    print("="*55)

    print(f"\n► Loading bar database: {BAR_DB_FILE}")
    bars_df = pd.read_excel(BAR_DB_FILE, sheet_name=BAR_DB_SHEET)
    bars_df = bars_df.dropna(subset=['Brand Name','Flavor Name'], how='all')
    print(f"  {len(bars_df)} bars")

    print(f"\n► Loading ingredient schema: {SCHEMA_FILE}")
    xl = pd.ExcelFile(SCHEMA_FILE)
    ingr_lines = pd.read_excel(xl, sheet_name='Ingredient_Lines')
    canonical  = pd.read_excel(xl, sheet_name='Canonical_Ingredients')
    alias_map  = pd.read_excel(xl, sheet_name='Alias_Map')
    products   = pd.read_excel(xl, sheet_name='Products')
    print(f"  {len(products)} products | {len(ingr_lines)} lines | {len(canonical)} canonicals")

    # Load optional CSV
    csv_lookup = {}
    if os.path.exists(SCORES_CSV):
        print(f"\n► Loading scores CSV: {SCORES_CSV}")
        csv_df = pd.read_csv(SCORES_CSV)
        csv_df = csv_df.dropna(subset=['Brand Name','Flavor Name'])
        csv_df['_key'] = csv_df['Brand Name'].str.strip().str.lower()+'|'+csv_df['Flavor Name'].str.strip().str.lower()
        csv_df = csv_df.drop_duplicates(subset='_key', keep='first')
        for _,row in csv_df.iterrows():
            csv_lookup[row['_key']] = {
                'flags':  row.get('Ingredient Flags') if pd.notna(row.get('Ingredient Flags','')) else None,
                'tokens': row.get('Ingredient Score Explanation') if pd.notna(row.get('Ingredient Score Explanation','')) else None
            }
        print(f"  {len(csv_lookup)} entries loaded")

    # Fix % DV columns
    for col in PCT_DV_COLS:
        if col in bars_df.columns:
            bars_df[col] = (bars_df[col]*100).round(0).astype('Int64')

    # Schema scoring setup
    products['_key'] = products['brand_name'].str.strip().str.lower()+'|'+products['flavor_name'].str.strip().str.lower()
    key_to_pid = dict(zip(products['_key'],products['product_id']))
    canonical_slim = canonical[['canonical_id','base_score']].copy()
    sl = ingr_lines.merge(canonical_slim,on='canonical_id',how='left')
    sl['weighted'] = sl['base_score'].fillna(0)*sl['effective_weight_default'].fillna(0)
    so = sl[sl['include_in_scoring_default']=='Y'].copy()
    lines_by_pid = {pid:grp for pid,grp in so.groupby('product_id')}

    # Auto-scoring lookups
    al, cl = build_lookups(alias_map, canonical)

    print(f"\n► Scoring bars...")
    schema_count=auto_count=unscored_count=csv_merged=0
    all_unmatched=[]

    for idx,row in bars_df.iterrows():
        brand=str(row.get('Brand Name','')).strip()
        flavor=str(row.get('Flavor Name','')).strip()
        key=f"{brand.lower()}|{flavor.lower()}"
        pid=key_to_pid.get(key)

        if pid and pid in lines_by_pid:
            rows=lines_by_pid[pid]
            final=rows['weighted'].sum()+get_count_adj(len(rows))
            band,bl=get_band(final)
            sr=rows.sort_values('weighted',ascending=False)
            top_pos=sr[sr['weighted']>0.3]['canonical_name'].head(3).tolist()
            top_neg=sr[sr['weighted']<-0.3]['canonical_name'].tail(3).tolist()
            parts=[]
            if top_pos: parts.append(f"Positives: {', '.join(top_pos)}")
            if top_neg: parts.append(f"Concerns: {', '.join(top_neg)}")
            ingr_detail=' · '.join(parts) if parts else None
            s=round(final,1); source='schema'; schema_count+=1
        else:
            s,band,bl,ingr_detail=auto_score(row.get('Ingredients',''),al,cl)
            source='auto'
            if s is not None: auto_count+=1
            else: unscored_count+=1

        csv_data=csv_lookup.get(key,{})
        flags=csv_data.get('flags')
        tokens=csv_data.get('tokens')
        if flags: csv_merged+=1

        parts_combined=[]
        if tokens: parts_combined.append(str(tokens).strip())
        if ingr_detail: parts_combined.append(ingr_detail)
        combined=' · '.join(parts_combined) if parts_combined else 'Neutral ingredient profile'

        bars_df.at[idx,'ingredient_score'] =s
        bars_df.at[idx,'score_band']       =band
        bars_df.at[idx,'score_band_label'] =bl
        bars_df.at[idx,'score_explanation']=combined
        bars_df.at[idx,'score_flags']      =flags
        bars_df.at[idx,'score_source']     =source

    print(f"  Schema-scored: {schema_count} | Auto: {auto_count} | Unscored: {unscored_count}")
    if csv_lookup: print(f"  CSV flags merged: {csv_merged}")
    bands=Counter(bars_df['score_band'].dropna())
    print(f"  Bands: {dict(sorted(bands.items()))}")

    # Build output
    df_out=bars_df[[c for c in KEEP_COLS if c in bars_df.columns]].copy()
    df_out=df_out.where(pd.notna(df_out),None)
    for col in df_out.select_dtypes(include='object').columns:
        df_out[col]=df_out[col].apply(lambda x: x.strip() if isinstance(x,str) else x)

    bars=df_out.to_dict(orient='records')
    js='const BARS = '+json.dumps(bars,separators=(',',':'))+';'
    js=js.replace(':NaN,',':null,').replace(':NaN}',':null}')

    with open(OUTPUT_FILE,'w',encoding='utf-8') as f:
        f.write(js)

    size_kb=os.path.getsize(OUTPUT_FILE)/1024
    print(f"\n✓ {OUTPUT_FILE} written — {len(bars)} bars, {size_kb:.0f}KB")
    print(f"\nNext: upload bars.js to GitHub → Cloudflare deploys in ~60s")


if __name__ == '__main__':
    run()
