# knowyourbar.com

A protein bar database with ingredient quality scoring, macro filtering, comparison tools, and similar bar discovery. 1,000+ bars scored. No sponsored picks. No ads.

---

## What It Is

A static website hosted on Cloudflare Pages via GitHub. Users can search, filter, sort, and compare 1,000+ protein bars by macros, ingredient quality grade, brand, certifications, and dietary preferences. Every bar is scored A through F based on its ingredient list using a transparent, rule-based system.

---

## File Structure

```
/
├── index.html                          — Main bar finder tool
├── style.css                           — All shared styles (3,700+ lines)
├── app.js                              — All filter, sort, preset, comparison, URL state logic
├── bars.js                             — Full bar database (1,000+ bars)
├── TEMPLATE_BRAND.html                 — Master template for brand review pages
├── score_and_export.py                 — Scoring pipeline script
├── knowyourbar_scoring_schema_v3.xlsx  — Ingredient scoring schema
├── bar_hero.png                        — Hero image
├── sitemap.xml
├── robots.txt
├── llms.txt                            — LLM crawler discovery file (AI citation signal)
├── BRIEFING.md                         — Claude session instructions
├── README.md                           — This file
├── DEPLOY.md                           — Deployment instructions
├── QA.md                               — QA checklist
│
├── quest-bars.html                     — Brand review: Quest (16 flavors)
├── rxbar-review.html                   — Brand review: RXBAR (14 flavors)
├── clif-bar-review.html                — Brand review: Clif Bar (28 flavors)
├── barebells-review.html               — Brand review: Barebells (25 flavors)
├── kind-bars-review.html               — Brand review: KIND (19 flavors)
├── quest-vs-rxbar.html                 — Comparison page
│
├── clean-protein-bars.html             — Guide: Clean Protein Bars
├── no-artificial-sweeteners.html       — Guide: No Artificial Sweeteners
├── no-sugar-alcohols.html              — Guide: No Sugar Alcohols
├── no-seed-oils.html                   — Guide: No Seed Oils
├── low-sugar-high-protein.html         — Guide: Low Sugar High Protein
├── keto-protein-bars.html              — Guide: Keto Protein Bars
│
└── ingredient_scoring.html             — Scoring methodology explainer
```

Note on file naming: brand pages use inconsistent naming (quest-bars.html vs rxbar-review.html). Standardization deferred until the site has enough link equity to absorb redirects safely.

---

## Database

**File:** bars.js
**Source:** KYB bar database spreadsheet (maintained locally, not in repo)
**Count:** 1,000+ bars across 95+ brands
**Affiliate tag:** knowyourbar0f-20

Each bar object contains:
```
Brand Name, Flavor Name, score_band (A/B/C/D/F), ingredient_score (numeric),
Calories, Protein (g), Total Fat (g), Saturated Fat (g), Total Carbohydrates (g),
Dietary Fiber (g), Sugars (g), Sugar Alcohol (g), Sodium (mg), Cholesterol (mg),
Ingredients (full text), Amazon Affiliate (URL), Website (URL),
positive_ingredients, concern_ingredients,
Vegan, Gluten Free, Dairy Free, Soy Free, Non-GMO, Nut Free, Kosher (all Y/N)
```

---

## Scoring System

**Schema file:** knowyourbar_scoring_schema_v3.xlsx
**Canonicals:** 1,048 ingredients
**Aliases:** 2,024 ingredient name variants

### How the pipeline works

All bars are scored from raw ingredient text using a single unified code path. The schema's Canonical_Ingredients and Alias_Map sheets are loaded. The Ingredient_Lines and Products sheets are not used. This is intentional and settled.

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
2. knowyourbar_scoring_schema_v3.xlsx

Claude will score all bars, export bars.js, and report the grade distribution and any unscored bars.

Or run locally:
```bash
python3 score_and_export.py --db "your_database.xlsx" --schema "knowyourbar_scoring_schema_v3.xlsx"
```
Requires: `pip install pandas openpyxl`

---

## Brand Review Pages

All brand pages are built from TEMPLATE_BRAND.html and follow a locked structure. Do not edit brand pages by hand without reading TEMPLATE_BRAND.html first.

### Template section order
1. Head: title, meta, canonical, 4 JSON-LD schemas (Article, Dataset, BreadcrumbList, FAQPage), OG/Twitter
2. Nav
3. Hero: H1 + short answer paragraph
4. Scorecard: 6 stats (flavors, grade range, score range, protein, calories, sweetener status)
5. Overview summary: 2-3 paragraphs
6. Grade distribution bar
7. Best and worst flavor cards with chips
8. Macro grid (6 macros) + SEO blurb
9. Ingredient quality patterns with chip frequency bars
10. Flavor table: 6 columns (Flavor, Grade, Score, Protein, Cal, Sugar)
11. Bottom line
12. Explore all bars CTA (dark tile)
13. Explore more (3 link cards)
14. FAQ (7+ questions)
15. Footer

### Flavor table
- 6 columns only — no Insights column in the table
- Chips live in the expand row (.ingr-chips), not in the table header
- Each expand row: macro strip + ingredient list + chips + buy button
- colspan must be 6

### JSON-LD schemas on every brand page
- **Article:** headline, url, image, datePublished, dateModified, author, publisher, mainEntityOfPage, about
- **Dataset:** static, same on every brand page
- **BreadcrumbList:** Home > Brand Reviews > Page Name
- **FAQPage:** minimum 7 questions, must match visible FAQ exactly

---

## CSS Architecture

**style.css is the single source of truth for all styles.**

- `index.html` has NO inline style block
- Brand/guide pages have minimal inline CSS for `:root` vars only
- Do not replace style.css wholesale — only append or use targeted edits

### Page body classes
- `<body class="page-brand">` — brand review pages
- `<body class="page-guide">` — guide pages
- `<body>` — index.html (no class)

### Design tokens

| Token | Value |
|-------|-------|
| --black | #0e0e0e |
| --white | #f7f5f0 |
| --off-white | #efece6 |
| --accent | #d4f000 |
| --muted | #888880 |
| --border | #d6d3cc |
| --font-display | Syne |
| --font-body | DM Sans |
| --font-mono | DM Mono |

Grade colors: A=#2a7a1f, B=#5a8a2f, C=#b89a00, D=#c87020, F=#c83020

---

## Main Tool Features (index.html + app.js)

### Filters
- 5 goal presets: Lose Weight, Clean Ingredients, Skip the Sugar, High Protein, Keto Friendly
- Ingredient grade toggles: A/B/C/D/F
- Brand search (multi-select)
- Flavor keyword search
- Macro sliders: Protein (min), Calories (max), Fat (max), Carbs (max), Sugar (max), Sugar Alcohol (max), Fiber (min), Net Carbs (max)
- Certifications: Vegan, GF, DF, SF, Non-GMO, Nut Free
- Exclude ingredients (XSS-safe)

### Results table columns
BAR | CAL | PROT | P/100 | FAT | CARB | FIBR | SGR | SGR ALC | CERTS | GRADE | CMP

P/100 = protein grams per 100 calories (sortable)

### Bar expand row
Macro rank grid, nutrition facts, ingredient quality score, certifications, insight chips, similar bars, buy links, full ingredient list

### Similar bars algorithm
Weighted Euclidean distance on 5 normalized macros + grade proximity penalty:
- Protein: 35%, Calories: 25%, Sugar: 20%, Fiber: 10%, Fat: 10%
- Grade proximity: 0.06 penalty per grade apart
- Cross-brand only. Top 3 stored per bar.

### URL state
All filter state serialized to URL params — fully shareable and bookmarkable.

---

## Insight Chips

Generated per bar. Displayed in the expand row.

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

Every page has:
- Unique title tag and meta description
- Canonical URL
- FAQPage JSON-LD
- Article JSON-LD (brand/guide pages)
- Dataset JSON-LD
- BreadcrumbList JSON-LD (brand pages)
- Open Graph and Twitter card tags
- GA4: G-SW4MNP5W7J

Brand page title formula: "Are [Brand] Bars Healthy? We Scored All [N] Flavors | Know Your Bar"

Meta description rule: lead with a specific data point. Under 155 characters. No em dashes.

**llms.txt** — AI crawler discovery file at `/llms.txt`. Documents the scoring system, database coverage, brand summaries, and guide pages in structured markdown so LLMs can cite the site accurately. Paired with explicit AI crawler rules in `robots.txt`.

---

## Deployment

**Host:** Cloudflare Pages
**Repo:** GitHub (jbooth22/knowyourbar)
**Branch:** main, auto-deploys on push
**Workflow:** manual file upload via GitHub web UI

Cache: purge Cloudflare cache after uploads if changes are not showing. Use `?v=N` query string to bypass browser cache during testing.

**Rollback:** GitHub → file → History → find last working commit → download raw → re-upload

---

## Known Issues

- Footer layout on brand pages has a stacking issue (pending fix)
- KIND Minis and Thins not yet in database
- Some duplicate ASINs in bars.js: Barebells Caramel Peanut/Salted Peanut Caramel share B0DT7KS2QB; Clif ZBar Chocolate Mint and Clif Bar Cool Mint Chocolate share B0CXQ71XY8

---

## Pending Work

### Features
- Protein type filter (whey vs plant vs egg)
- Net carbs column in main table
- Brand comparison pages (Quest vs Barebells, etc.)
- Full brand rankings page

### Content
- KIND Minis and Thins — score and add to database
- Fix duplicate ASINs flagged above
- Continue adding Amazon affiliate links

---

*Last updated: April 2026*
