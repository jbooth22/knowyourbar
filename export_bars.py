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

# Columns to include in the website (keeps bars.js lean)
KEEP_COLS = [
    'Brand Name', 'Flavor Name', 'Size', 'Type', 'Website',
    'Serving Size (g)', 'Calories', 'Total Fat (g)', 'Saturated Fat (g)',
    'Cholesterol (mg)', 'Sodium (mg)', 'Total Carbohydrates (g)',
    'Dietary Fiber (g)', 'Sugars (g)', 'Sugar Alcohol (g)', 'Protein (g)',
    'Calcium (mg)', 'Iron (mg)', 'Potassium (mg)', 'Caffeine (mg)',
    'Kosher (Y/N)', 'Vegan (Y/N)', 'Non-GMO (Y/N)', 'Soy Free (Y/N)',
    'Dairy Free (Y/N)', 'Gluten Free (Y/N)', 'Nut Free (Y/N)', 'Ingredients',
]
# ────────────────────────────────────────────────────────


def export():
    print(f"Reading {EXCEL_FILE}...")
    df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME)

    # Only keep columns that exist in the spreadsheet
    cols = [c for c in KEEP_COLS if c in df.columns]
    df = df[cols].copy()

    # Clean strings — strip whitespace
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].str.strip()

    # Replace NaN with None (becomes null in JSON)
    df = df.where(pd.notna(df), None)

    bars = df.to_dict(orient='records')

    # Build the JS file
    json_str = json.dumps(bars, separators=(',', ':'), ensure_ascii=False)
    # Fix any lingering NaN that slipped through (shouldn't happen, but safety net)
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
