# knowyourbar.com

A protein bar database with ingredient quality scoring, macro filtering, comparison tools, and similar bar discovery. 1,000+ bars scored. No sponsored picks. No ads.

---

## What It Is

A static website hosted on Cloudflare Pages via GitHub. Users can search, filter, sort, and compare 1,000+ protein bars by macros, ingredient quality grade, brand, certifications, and dietary preferences. Every bar is scored A through F based on its ingredient list using a transparent, rule-based system.

---

## Working on this project

**This file is a public-facing overview, not the working reference.** For file structure, template conventions, deploy process, locked rules, and current known issues, see `BRIEFING.md` — that's the single source of truth for anyone (human or Claude) actively working on the site. This file used to duplicate that content independently and the two drifted apart (different stale numbers, different completion dates) until a 2026-08-09 cleanup consolidated everything into `BRIEFING.md`. Keeping this file short is intentional, not incomplete.

Note on file naming: brand pages use inconsistent naming (quest-bars.html vs rxbar-review.html). Standardization deferred until the site has enough link equity to absorb redirects safely.

---

## Database

**File:** bars.js
**Source:** KYB bar database spreadsheet (maintained locally, not in repo)
**Count:** 1,000+ bars (see BRIEFING.md's Locked Global Rules before writing this number anywhere else — always "1,000+", never an exact figure)
**Affiliate tag:** knowyourbar0f-20

Each bar object contains:
```
Brand Name, Flavor Name, score_band (A/B/C/D/F), ingredient_score (numeric),
Calories, Protein (g), Total Fat (g), Saturated Fat (g), Total Carbohydrates (g),
Dietary Fiber (g), Sugars (g), Sugar Alcohol (g), Sodium (mg), Cholesterol (mg),
Ingredients (full text), Amazon Affiliate (URL), Website (URL),
score_insights (chip data), positive_ingredients, concern_ingredients,
Vegan, Gluten Free, Dairy Free, Soy Free, Non-GMO, Nut Free, Kosher (all Y/N or null if untracked)
```

---

## Scoring System (public methodology reference)

**Schema file:** knowyourbar_scoring_schema_v4.xlsx

### How the pipeline works

All bars are scored from raw ingredient text using a single unified code path. The schema's Canonical_Ingredients and Alias_Map sheets are loaded. The Ingredient_Lines and Products sheets are not used. This is intentional and settled — see BRIEFING.md if this is ever in question.

### Parser behavior

- Top-level ingredients get full position weight
- Sub-ingredients inside parentheses get 60% weight
- Ingredients after "contains less than", "may contain", etc. are ignored

### Scoring formula

```
Final Score = sum of (base_score x position_weight x sub_multiplier) + count adjustment
```

### Position weights

| Position | Weight | Position | Weight |
|----------|--------|----------|--------|
| 1 | 1.00 | 6 | 0.44 |
| 2 | 0.85 | 7 | 0.37 |
| 3 | 0.72 | 8 | 0.31 |
| 4 | 0.61 | 9 | 0.26 |
| 5 | 0.52 | 10+ | Decreasing from 0.22 |

### Count adjustment

| Ingredient count | Adjustment |
|-----------------|------------|
| 1-8 | +0.05 |
| 9-12 | 0.00 |
| 13-16 | -0.05 |
| 17-20 | -0.10 |
| 21+ | -0.15 |

### Grade bands

| Grade | Label | Score range |
|-------|-------|-------------|
| A | Clean | >= 7.0 |
| B | Good | 4.0 to 6.9 |
| C | Okay | 1.0 to 3.9 |
| D | Poor | -2.0 to 0.9 |
| F | Avoid | Below -2.0 |

### Running the pipeline

Upload both files to Claude and say "run score_and_export":
1. Your bar database Excel
2. knowyourbar_scoring_schema_v4.xlsx

Claude will score all bars, export bars.js, and report the grade distribution and any unscored bars. Then run `diff_bars_upload.py` before touching any page — see BRIEFING.md.

Or run locally:
```bash
python3 score_and_export.py --db "your_database.xlsx" --schema "knowyourbar_scoring_schema_v4.xlsx"
```
Requires: `pip install pandas openpyxl`

---

## Insight Chips (public methodology reference)

Generated per bar from the scoring pipeline, stored in `score_insights`, displayed in the expand row. This table is the rule definitions — whether a given chip actually appears for a given brand is a data question, not a rule question. Run `verify_brand_data.py "<Brand>"` to see which chips actually apply to a specific brand before writing any copy that names one; a chip being defined here doesn't mean it fires for every brand (e.g. "Protein Leads" is a real rule but doesn't apply to any current Quest flavor).

| Chip | Type | Rule |
|------|------|------|
| Protein Leads | positive | First top-level ingredient is protein |
| Quality Protein Source | positive | High-quality protein (score >=3) in top 5 |
| Whole Food Forward | positive | 2+ of first 3 positions are whole food |
| Short Clean List | positive | 8 or fewer top-level ingredients |
| Fortified | neutral | Vitamins/minerals present |
| Long Ingredient List | neutral | 18+ top-level ingredients |
| Artificial Sweeteners | concern | Sucralose, ace-K, aspartame, or saccharin |
| Sugar Alcohols | concern | Erythritol, maltitol, xylitol, sorbitol, etc. |
| Processed Oils | concern | Palm, canola, soybean, or hydrogenated oils (high-oleic excluded) |
| Sweetener Heavy | concern elevated | Sweetener category in top 3 positions |
| Collagen Protein | concern elevated | First protein ingredient is collagen |

---

## SEO

**llms.txt** — AI crawler discovery file at `/llms.txt`. Documents the scoring system, database coverage, brand summaries, and guide pages in structured markdown so LLMs can cite the site accurately. Paired with explicit AI crawler rules in `robots.txt`. Full SEO conventions (title formulas, JSON-LD requirements, meta description rules) live in BRIEFING.md.

---

## Deployment, file structure, known issues, and pending work

All of this lives in `BRIEFING.md` now, not here. See "Deploy process," "File structure," and "Known issues / next priorities" in that file.

---

*Last updated: 2026-08-09 — trimmed to remove content duplicated in BRIEFING.md, which had drifted out of sync with this file.*
