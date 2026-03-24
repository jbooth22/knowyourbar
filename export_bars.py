#!/usr/bin/env python3
"""
Know Your Bar — Database Export Script
=======================================
Run this whenever you update your Excel database.
It generates a new bars.js file ready to upload to GitHub.

Usage:
    python3 export_bars.py

Requirements:
    pip install pandas openpyxl

Place this script in the same folder as your Excel file,
or update EXCEL_FILE to point to the correct path.
"""

import pandas as pd
import json
import os
from datetime import datetime

# ── Config ──────────────────────────────────────────────
EXCEL_FILE  = "KYB_-_New_Protein_Bar_Database__2026_.xlsx"   # update if filename changes
SHEET_NAME  = "BarDB"
OUTPUT_FILE = "bars.js"

# Columns to include in the website
KEEP_COLS = [
    'Brand Name', 'Flavor Name', 'Size', 'Type', 'Website',
    'Serving Size (g)', 'Calories', 'Total Fat (g)', 'Saturated Fat (g)',
    'Trans Fat (g)', 'Cholesterol (mg)', 'Sodium (mg)',
    'Total Carbohydrates (g)', 'Dietary Fiber (g)', 'Sugars (g)',
    'Sugar Alcohol (g)', 'Protein (g)',
    'Calcium (mg)', 'Iron (mg)', 'Potassium (mg)', 'Caffeine (mg)',
    'Vitamin A (% DV)', 'Vitamin C (% DV)', 'Vitamin D (% DV)',
    'Vitamin E (% DV)', 'Vitamin K (% DV)', 'Thiamin / B1 (% DV)',
    'Riboflavin / B2 (% DV)', 'Niacin / B3 (% DV)', 'Vitamin B6 (% DV)',
    'Vitamin B12 (% DV)', 'Folic Acid (% DV)', 'Biotin (% DV)',
    'Pantothenic Acid (% DV)', 'Phosphorus (% DV)', 'Iodine (% DV)',
    'Magnesium (% DV)', 'Zinc (% DV)', 'Selenium (% DV)', 'Copper (% DV)',
    'Manganese (% DV)', 'Chromium (% DV)', 'Molybdenum (% DV)',
    'Kosher (Y/N)', 'Vegan (Y/N)', 'Non-GMO (Y/N)', 'Soy Free (Y/N)',
    'Dairy Free (Y/N)', 'Gluten Free (Y/N)', 'Nut Free (Y/N)', 'Ingredients',
]

# % DV columns are stored as decimals in Excel (e.g. 0.20 = 20%)
# These get multiplied by 100 during export to restore whole number percentages
PCT_DV_COLS = [
    'Vitamin A (% DV)', 'Vitamin C (% DV)', 'Vitamin D (% DV)',
    'Vitamin E (% DV)', 'Vitamin K (% DV)', 'Thiamin / B1 (% DV)',
    'Riboflavin / B2 (% DV)', 'Niacin / B3 (% DV)', 'Vitamin B6 (% DV)',
    'Vitamin B12 (% DV)', 'Folic Acid (% DV)', 'Biotin (% DV)',
    'Pantothenic Acid (% DV)', 'Phosphorus (% DV)', 'Iodine (% DV)',
    'Magnesium (% DV)', 'Zinc (% DV)', 'Selenium (% DV)', 'Copper (% DV)',
    'Manganese (% DV)', 'Chromium (% DV)', 'Molybdenum (% DV)',
]
# ────────────────────────────────────────────────────────


def export():
    print(f"Reading {EXCEL_FILE}...")
    df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME)

    # Fix % DV columns — Excel stores 20% as 0.20, multiply back to whole numbers
    for col in PCT_DV_COLS:
        if col in df.columns:
            df[col] = (df[col] * 100).round(0).astype('Int64')

    # Replace NaN with None (becomes null in JSON)
    df = df.where(pd.notna(df), None)

    # Only keep columns that exist in the spreadsheet
    cols = [c for c in KEEP_COLS if c in df.columns]
    df = df[cols].copy()

    # Clean strings — strip whitespace
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)

    bars = df.to_dict(orient='records')

    # Build the JS file
    json_str = json.dumps(bars, separators=(',', ':'), ensure_ascii=False)
    json_str = json_str.replace(':NaN,', ':null,').replace(':NaN}', ':null}')

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    output = f"// Know Your Bar — bars.js\n// Generated: {timestamp} — {len(bars)} bars\nconst BARS = {json_str};"

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(output)

    size_kb = os.path.getsize(OUTPUT_FILE) / 1024
    print(f"\n✓ Done!")
    print(f"  Bars exported : {len(bars)}")
    print(f"  Output file   : {OUTPUT_FILE}")
    print(f"  File size     : {size_kb:.0f} KB")
    print(f"\nNext step: upload bars.js to GitHub → Cloudflare auto-deploys in ~60s")


if __name__ == '__main__':
    export()
