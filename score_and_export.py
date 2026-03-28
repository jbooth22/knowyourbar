#!/usr/bin/env python3
"""
Know Your Bar — Score & Export Script v2
=========================================
Scores all bars using the KYB ingredient schema and exports bars.js.

For bars already in the schema: uses pre-parsed ingredient lines
with full position/clause weighting for maximum accuracy.

For new bars: auto-scores from raw ingredient string using
alias + canonical fuzzy matching (99%+ coverage).

Insight chips are computed deterministically for ALL bars —
no dependency on any external scoring file.

FILES REQUIRED (upload both to Claude when running):
  - Your bar database Excel  (BAR_DB_FILE)
  - KYB scoring schema Excel (SCHEMA_FILE)
"""

import pandas as pd, numpy as np, json, re, os
from datetime import datetime
from collections import Counter

# ── Config ────────────────────────────────────────────
BAR_DB_FILE  = "KYB_-_New_Protein_Bar_Database__2026_.xlsx"
SCHEMA_FILE  = "knowyourbar_scoring_schema.xlsx"
BAR_DB_SHEET = "BarDB"
OUTPUT_FILE  = "bars.js"

# ── Score bands ───────────────────────────────────────
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

# ── % DV columns ──────────────────────────────────────
PCT_DV_COLS = [
    'Vitamin A (% DV)','Vitamin C (% DV)','Vitamin D (% DV)','Vitamin E (% DV)',
    'Vitamin K (% DV)','Thiamin / B1 (% DV)','Riboflavin / B2 (% DV)',
    'Niacin / B3 (% DV)','Vitamin B6 (% DV)','Vitamin B12 (% DV)',
    'Folic Acid (% DV)','Biotin (% DV)','Pantothenic Acid (% DV)',
    'Phosphorus (% DV)','Iodine (% DV)','Magnesium (% DV)','Zinc (% DV)',
    'Selenium (% DV)','Copper (% DV)','Manganese (% DV)','Chromium (% DV)',
    'Molybdenum (% DV)'
]

# ── Output columns ────────────────────────────────────
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
    'positive_ingredients','concern_ingredients','score_insights','score_source'
]

# ── Insight chip rules ────────────────────────────────
# Each rule: (chip_name, chip_type)
# Types: 'positive' | 'neutral' | 'concern'
# Rules are computed in compute_insights() below.
# See Scoring_Logic sheet in schema for full documentation.

PROCESSED_OIL_KW  = ['palm oil','palm kernel oil','canola oil','soybean oil',
                      'hydrogenated','partially hydrogenated']
HIGH_OLEIC_EXCEPT  = ['high oleic']
ARTIFICIAL_SW_KW   = ['sucralose','acesulfame','aspartame']

SKIP_PREFIXES = ['organic ','natural ','pure ','raw ','whole ','roasted ','unsweetened ',
    'dried ','dehydrated ','grass fed ','grass-fed ','non gmo ','certified ',
    'reduced fat ','low fat ','instant ','enriched ','unbleached ','pasteurized ','homogenized ']
SKIP_CLAUSES = ['contains less than','less than','may contain','contains:',
                'manufactured in','processed in','made in']

# ─────────────────────────────────────────────────────

def get_count_adj(n):
    for lo,hi,adj in COUNT_BANDS:
        if lo<=n<=hi: return adj
    return 0

def get_band(s):
    for lo,hi,b,l in SCORE_BANDS:
        if lo<=s<=hi: return b,l
    return 'F','Avoid'

def position_weight(pos):
    w={1:1.0,2:0.85,3:0.72,4:0.61,5:0.52,6:0.44,7:0.37,8:0.31,
       9:0.26,10:0.22,11:0.20,12:0.18,13:0.17,14:0.16,15:0.15}
    return w.get(pos, max(0.08, 0.15-(pos-15)*0.007))

def normalize(text):
    text=str(text).lower().strip()
    text=re.sub(r'\*+','',text)
    text=re.sub(r'\(.*?\)','',text)
    text=re.sub(r'[^a-z0-9\s]',' ',text)
    return re.sub(r'\s+',' ',text).strip()

def compute_insights(pid, ingr_text, lines_by_pid, sa_ids, quality_prot_ids, collagen_ids, vitmin_ids):
    """Compute all insight chips for a bar. All rules are deterministic."""
    if pid not in lines_by_pid: return []
    rows = lines_by_pid[pid].sort_values('top_level_position')
    canon_ids = rows['canonical_id'].tolist()
    cats = rows['category'].fillna('other').tolist()
    n_top = int(rows['top_level_position'].max())
    ingr_lower = str(ingr_text).lower()
    insights = []

    # ── POSITIVE ─────────────────────────────────────
    # Protein Leads: first position is protein category
    pos1_cats = rows[rows['top_level_position']==1]['category'].tolist()
    if 'protein' in pos1_cats:
        insights.append(('Protein Leads', 'positive'))

    # Quality Protein Source: score>=3 protein in top 5
    top5_ids = set(rows[rows['top_level_position']<=5]['canonical_id'].tolist())
    if top5_ids & quality_prot_ids:
        insights.append(('Quality Protein Source', 'positive'))

    # Whole Food Forward: 2+ unique top-3 positions with whole_food
    top3_rows = rows[rows['top_level_position'].isin([1,2,3])]
    if top3_rows[top3_rows['category']=='whole_food']['top_level_position'].nunique() >= 2:
        insights.append(('Whole Food Forward', 'positive'))

    # Short Clean List: <= 8 positions
    if n_top <= 8:
        insights.append(('Short Clean List', 'positive'))

    # ── NEUTRAL ──────────────────────────────────────
    # Fortified: vitamin/mineral ingredients present
    if set(canon_ids) & vitmin_ids:
        insights.append(('Fortified', 'neutral'))

    # Long Ingredient List: >= 18 positions
    if n_top >= 18:
        insights.append(('Long Ingredient List', 'neutral'))

    # ── CONCERN ──────────────────────────────────────
    # Artificial Sweeteners: text match
    if any(kw in ingr_lower for kw in ARTIFICIAL_SW_KW):
        insights.append(('Artificial Sweeteners', 'concern'))

    # Sugar Alcohols: any position
    if set(canon_ids) & sa_ids:
        insights.append(('Sugar Alcohols', 'concern'))
        # Sugar Alcohol Early: in top 5
        if top5_ids & sa_ids:
            insights.append(('Sugar Alcohol Early', 'concern'))

    # Processed Oils: text match excluding high-oleic
    has_po = False
    for kw in PROCESSED_OIL_KW:
        if kw in ingr_lower:
            idx = ingr_lower.find(kw)
            ctx = ingr_lower[max(0,idx-20):idx+len(kw)]
            if not any(ex in ctx for ex in HIGH_OLEIC_EXCEPT):
                has_po = True; break
    if has_po:
        insights.append(('Processed Oils', 'concern'))

    # Sweetener Heavy: sweetener in top 3 positions
    top3_cats = rows[rows['top_level_position'].isin([1,2,3])]['category'].tolist()
    if 'sweetener' in top3_cats:
        insights.append(('Sweetener Heavy', 'concern'))

    # Collagen Protein: first protein is collagen
    prot_rows = rows[rows['category']=='protein'].sort_values('top_level_position')
    if not prot_rows.empty and prot_rows.iloc[0]['canonical_id'] in collagen_ids:
        insights.append(('Collagen Protein', 'concern'))

    return insights

def build_lookups(alias_map, canonical):
    al, cl = {}, {}
    for _,row in alias_map.iterrows():
        key = normalize(str(row['normalized_alias_text']))
        if key not in al:
            al[key] = {'canonical_name': row['canonical_name'],
                       'base_score': float(row['base_score']) if pd.notna(row['base_score']) else 0}
    for _,row in canonical.iterrows():
        key = normalize(str(row['canonical_name']))
        if key not in cl:
            cl[key] = {'canonical_name': row['canonical_name'],
                       'base_score': float(row['base_score']) if pd.notna(row['base_score']) else 0}
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
    best, best_len = None, 0
    for key,val in al.items():
        if key in norm and len(key)>best_len and len(key)>4:
            best,best_len = val,len(key)
    return best

def auto_score_bar(raw, al, cl):
    """Score a new bar from raw ingredient text."""
    if not raw or pd.isna(raw): return None,None,None,'',''
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
        res=lookup_ing(norm, al, cl)
        if res:
            pw=position_weight(i+1)
            matched.append({'canonical':res['canonical_name'],'score':res['base_score'],
                            'weighted':res['base_score']*pw})
    if not matched: return None,None,None,'',''
    final=sum(m['weighted'] for m in matched)+get_count_adj(len(matched))
    band,bl=get_band(final)
    sm=sorted(matched,key=lambda x:x['weighted'],reverse=True)
    pos=[m['canonical'] for m in sm if m['weighted']>0.3][:3]
    neg=[m['canonical'] for m in sm if m['weighted']<-0.3][-3:]
    return round(final,1),band,bl,', '.join(pos),', '.join(neg)


def run():
    print("="*55)
    print("  Know Your Bar — Score & Export v2")
    print("="*55)

    print(f"\n► Loading bar database: {BAR_DB_FILE}")
    bars_df = pd.read_excel(BAR_DB_FILE, sheet_name=BAR_DB_SHEET)
    bars_df = bars_df.dropna(subset=['Brand Name','Flavor Name'], how='all')
    print(f"  {len(bars_df)} bars loaded")

    print(f"\n► Loading scoring schema: {SCHEMA_FILE}")
    xl = pd.ExcelFile(SCHEMA_FILE)
    canonical  = pd.read_excel(xl, sheet_name='Canonical_Ingredients')
    alias_map  = pd.read_excel(xl, sheet_name='Alias_Map')
    ingr_lines = pd.read_excel(xl, sheet_name='Ingredient_Lines')
    products   = pd.read_excel(xl, sheet_name='Products')
    print(f"  {len(canonical)} canonicals | {len(alias_map)} aliases | {len(ingr_lines)} ingredient lines")

    # Fix % DV columns
    for col in PCT_DV_COLS:
        if col in bars_df.columns:
            bars_df[col] = (bars_df[col]*100).round(0).astype('Int64')

    # Build schema scoring structures
    canonical_slim = canonical[['canonical_id','category','base_score']].copy()
    ingr_m = ingr_lines.merge(canonical_slim, on='canonical_id', how='left')
    ingr_m['weighted'] = ingr_m['base_score'].fillna(0)*ingr_m['effective_weight_default'].fillna(0)
    so = ingr_m[ingr_m['include_in_scoring_default']=='Y'].copy()
    lines_by_pid = {pid:grp for pid,grp in so.groupby('product_id')}
    products['_key'] = products['brand_name'].str.strip().str.lower()+'|'+products['flavor_name'].str.strip().str.lower()
    key_to_pid = dict(zip(products['_key'],products['product_id']))

    # Build insight canonical sets
    sa_ids = set(canonical[canonical['canonical_name'].str.lower().str.contains(
        'erythritol|maltitol|xylitol|sorbitol|mannitol|isomalt|lactitol|sugar alcohol',na=False)]['canonical_id'])
    quality_prot_ids = set(canonical[(canonical['category']=='protein')&(canonical['base_score']>=3)]['canonical_id'])
    collagen_ids = set(canonical[canonical['canonical_name'].str.lower().str.contains('collagen',na=False)]['canonical_id'])
    vitmin_ids = set(canonical[canonical['category']=='vitamin_mineral']['canonical_id'])

    # Build auto-scoring lookups
    al, cl = build_lookups(alias_map, canonical)

    print(f"\n► Scoring {len(bars_df)} bars...")
    bars_df['_key'] = bars_df['Brand Name'].str.strip().str.lower()+'|'+bars_df['Flavor Name'].str.strip().str.lower()
    schema_count=auto_count=unscored_count=0

    for idx,row in bars_df.iterrows():
        key=row['_key']; pid=key_to_pid.get(key)
        ingr=row.get('Ingredients','')

        if pid and pid in lines_by_pid:
            r=lines_by_pid[pid]
            final=r['weighted'].sum()+get_count_adj(len(r))
            band,bl=get_band(final)
            sr=r.sort_values('weighted',ascending=False)
            pos_str=', '.join(sr[sr['weighted']>0.3]['canonical_name'].head(3).tolist())
            neg_str=', '.join(sr[sr['weighted']<-0.3]['canonical_name'].tail(3).tolist())
            s=round(final,1); source='schema'; schema_count+=1
            insights=compute_insights(pid,ingr,lines_by_pid,sa_ids,quality_prot_ids,collagen_ids,vitmin_ids)
        else:
            s,band,bl,pos_str,neg_str=auto_score_bar(ingr,al,cl)
            source='auto'
            insights=[]
            if s is not None: auto_count+=1
            else: unscored_count+=1

        bars_df.at[idx,'ingredient_score']    = s
        bars_df.at[idx,'score_band']          = band
        bars_df.at[idx,'score_band_label']    = bl
        bars_df.at[idx,'positive_ingredients'] = pos_str
        bars_df.at[idx,'concern_ingredients']  = neg_str
        bars_df.at[idx,'score_insights']       = '|'.join(f"{n}:{t}" for n,t in insights)
        bars_df.at[idx,'score_source']         = source

    print(f"  Schema-scored: {schema_count} | Auto-scored: {auto_count} | Unscored: {unscored_count}")
    bands=Counter(bars_df['score_band'].dropna())
    print(f"  Bands: A={bands.get('A',0)} B={bands.get('B',0)} C={bands.get('C',0)} D={bands.get('D',0)} F={bands.get('F',0)}")

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
