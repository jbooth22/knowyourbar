# knowyourbar.com

A hand-researched protein bar database with ingredient quality scoring, macro filtering, comparison tools, and similar bar discovery. No sponsored picks. No ads.

---

## What It Is

A static website hosted on Cloudflare Pages via GitHub. Users can search, filter, sort, and compare 817+ protein bars by macros, ingredient quality grade, brand, certifications, and dietary preferences. Every bar is scored A through F based on its ingredient list.

---

## File Structure

```
/
├── index.html              — Main bar finder tool
├── style.css               — All shared styles
├── app.js                  — All filter, sort, preset, comparison, URL state, and similar bars logic
├── bars.js                 — Full bar database (900+ bars, ~1.6MB)
├── bar_hero.png            — Hero image
├── score_and_export.py     — Scoring pipeline script
├── sitemap.xml
├── robots.txt
├── README.md               — This file
├── DEPLOY.md               — Deployment and update instructions
│
├── quest-bars.html         — Brand review: Quest
├── rxbar-review.html       — Brand review: RXBAR
├── clif-bar-review.html    — Brand review: Clif Bar
├── barebells-review.html   — Brand review: Barebells
├── clean-protein-bars.html — SEO guide: Clean Protein Bars (with Key Findings + charts)
└── ingredient_scoring.html — Scoring methodology explainer
```

Note on file naming: Brand pages use inconsistent naming (quest-bars.html vs rxbar-review.html). Standardization deferred until the site has enough link equity to absorb the redirects safely.

---

## Database

File: bars.js
Source: KYB - New Protein Bar Database (2026).xlsx (maintained locally, not in repo)
Current count: 900+ bars across 95+ brands
Affiliate tag: knowyourbar0f-20
Affiliate coverage: ~554 of 900+ bars (~68%)

### Known unscored bars (missing ingredient data in spreadsheet)
- Power Crunch | Chocolate Strawberry
- MET-Rx | Peanut Butter Granola
- MET-Rx | Chocolate Chip Granola
- MET-Rx | Mint Super Cookie

Add ingredient lists to the spreadsheet and re-run the pipeline to score them.

---

## Scoring System

Schema file: knowyourbar_scoring_schema_v3.xlsx (in repo)
Canonicals: 1,047 ingredients
Aliases: 2,021 ingredient name variants

### Critical: how the pipeline works

ALL bars are scored from raw ingredient text using a single unified code path.
The schema's Ingredient_Lines and Products sheets are NOT used.
Only Canonical_Ingredients and Alias_Map are loaded from the schema.

This is intentional and settled. Do not revert to schema pre-parsed scoring.

### Parser behavior

- Top-level ingredients get full position weight
- Sub-ingredients inside parentheses (e.g. protein blends) get 60% weight — they are present in smaller amounts than their parent ingredient
- Ingredients after "contains less than", "may contain", etc. are ignored

### Scoring formula

Final Score = sum of (base_score x position_weight x sub_multiplier) + count adjustment

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
| A | Clean | >= 8.0 |
| B | Good | 4.0 to 7.9 |
| C | Okay | 0.0 to 3.9 |
| D | Poor | -3.0 to -0.1 |
| F | Avoid | Below -3.0 |

### Current grade distribution (900+ bars)
A=117, B=305, C=287, D=173, F=22, Unscored=4

---

## Running the Pipeline

Upload both files to Claude and say "run score_and_export":
1. Your bar database Excel
2. knowyourbar_scoring_schema_v3.xlsx

Claude will score all bars, export bars.js, and report the grade distribution and any unscored bars.

After running: update the bar count in all HTML files (search and replace old number with new total). The ingredient scoring page pulls its count dynamically so it updates automatically.

Alternatively, run locally with Python:
```
python3 score_and_export.py --db "your_database.xlsx" --schema "knowyourbar_scoring_schema_v3.xlsx"
```
Requires: pip install pandas openpyxl

---

## Pages

### index.html — Main Tool
- 5 goal-oriented presets: Lose Weight, Clean Ingredients, Skip the Sugar, Most Protein Per Calorie, Keto Friendly
- Core filters always visible: Presets, Ingredient Grade, Brand, Flavor keyword
- Advanced filters collapsed by default: Macro sliders, Certifications, Exclude ingredients
- Macro rank grid in expanded row: each of 5 macros shows rank (e.g. "#47 highest protein of 900+ bars")
- Similar bars section in expanded row: 3 cross-brand bars with comparable macro profiles
- Comparison feature: add up to 4 bars, shareable comparison URL
- URL state serialization (all filter state in URL params)
- FAQ accordion with FAQPage JSON-LD schema

### Expanded row features
- Macro rank grid: Protein (#N highest), Calories (#N lowest), Sugar (#N lowest), Fiber (#N highest), Fat (#N of 817) — color coded green/amber/gray by quartile
- Similar bars: 3 cards showing brand, grade, flavor, protein/calories/sugar, and why they're similar. Clicking jumps to that bar and expands it.
- Nutrition facts panel (full macro + vitamin/mineral data)
- Ingredient quality section: grade, score, +/- breakdown bar, insight chips, positive/concern ingredients
- Certifications, product page link, Amazon affiliate link
- Full ingredient list

### Brand Review Pages
- Hero with brand-specific headline
- Score overview with grade distribution
- Per-flavor bar table with ingredient list expand
- FAQ accordion (5Q) with FAQPage JSON-LD schema
- Self-contained (no style.css link) — nav, FAQ, and font CSS injected inline

### clean-protein-bars.html
- Definition of "clean": no artificial sweeteners, no sugar alcohols, A or B grade
- Key Findings section: big stat (65% of bars contain no artificial sweeteners or sugar alcohols), 6 insight bullets, donut chart (sweetener breakdown), bar chart (ingredient count vs quality score)
- Top 15 clean bars ranked with full bar cards
- CTA to /?preset=clean
- FAQ accordion (4Q) with FAQPage JSON-LD schema

### ingredient_scoring.html
- Full methodology: parsing, mapping, weighting, scoring
- Live grade distribution pulled from bars.js at runtime (uses BARS.length, not scored count)
- Insight chip explainer
- FAQ accordion (5Q) with FAQPage JSON-LD schema

---

## Insight Chips

Generated for every scored bar. Displayed in the expanded row ingredient quality section.

| Chip | Type | Rule |
|------|------|------|
| Protein Leads | positive | First top-level ingredient is protein category |
| Quality Protein Source | positive | High-quality protein (score >=3) in top 5 positions |
| Whole Food Forward | positive | 2+ of first 3 top-level positions are whole_food category |
| Short Clean List | positive | 8 or fewer top-level ingredients |
| Fortified | neutral | Vitamin or mineral ingredients present |
| Long Ingredient List | neutral | 18+ top-level ingredients |
| Artificial Sweeteners | concern | Sucralose, acesulfame, aspartame, or saccharin present |
| Sugar Alcohols | concern | Erythritol, maltitol, xylitol, sorbitol, etc. present |
| Processed Oils | concern | Palm, canola, soybean, or hydrogenated oils (high-oleic excluded) |
| Sweetener Heavy | concern (elevated) | Sweetener category in top 3 positions |
| Collagen Protein | concern (elevated) | First protein ingredient is collagen |

---

## Similar Bars Algorithm

Precomputed at page load as an IIFE over all scored bars.

Similarity = weighted euclidean distance on 5 normalized macros + grade proximity penalty:
- Protein: 35% weight
- Calories: 25% weight
- Sugar: 20% weight
- Fiber: 10% weight
- Fat: 10% weight
- Grade proximity: 0.06 penalty per grade apart (keeps like quality with like quality)

Cross-brand only. Top 3 results stored per bar. Clicking a similar bar card scrolls to and expands that bar; if filtered out, resets filters first.

---

## Macro Rank System

Precomputed at page load. For each of 5 macros, all bars sorted and ranks assigned (ties share rank).

| Macro | Direction word | Green when | Amber when |
|-------|---------------|------------|------------|
| Protein | highest | Top 25% | Bottom 25% |
| Calories | lowest | Top 25% | Bottom 25% |
| Sugar | lowest | Top 25% | Bottom 25% |
| Fiber | highest | Top 25% | Bottom 25% |
| Fat | of 817 (neutral) | never | never |

---

## Design System

| Token | Value |
|-------|-------|
| --black | #0e0e0e |
| --white | #f7f5f0 |
| --off-white | #efece6 |
| --accent | #d4f000 (electric yellow-green) |
| --muted | #6b6b65 |
| --border | #d6d3cc |
| --font-display | Syne (headings, wordmark) |
| --font-body | DM Sans (body text, paragraphs) |
| --font-mono | DM Mono (labels, tags, data) |

Grade colors: A=#2a7a1f, B=#5a8a2f, C=#b89a00, D=#c87020, F=#c83020

---

## Navigation

All pages share a consistent nav bar:
- Brand Reviews dropdown: Quest, RXBAR, Clif Bar, Barebells
- Guides dropdown: Clean Protein Bars
- How We Score (direct link)

Brand pages are self-contained. Nav CSS injected inline into each page's style block.

---

## SEO

Every page has:
- Unique title tag
- Meta description (under 158 characters)
- Canonical URL
- FAQPage JSON-LD schema (4-5 questions)
- Open Graph tags
- Twitter card meta tags

---

## Deployment

Host: Cloudflare Pages
Repo: GitHub (jbooth22)
Branch: main, auto-deploys on push

Current workflow: manual file upload via GitHub web UI.
Planned: local Git setup (git add . && git commit && git push).

---

## Pending Work

### Features
- More brand pages: Kind, Nature Valley, FITCRUNCH, Magic Spoon
- SEO guide: protein bars without artificial sweeteners
- SEO guide: protein bars for weight loss
- AI comparison summary: Claude API "choose this bar if..." per comparison overlay

### Data
- Add ingredient data for 4 unscored bars
- Continue adding affiliate links (~263 bars missing)
- File structure reorganization: /brands/, /guides/ subfolders (after link equity builds)

### DevOps
- Set up local Git
- Standardize brand page file naming

---

## Analytics

Google Analytics: G-SW4MNP5W7J (tag in index.html)

---

Last updated: April 2026

## CSS Architecture — READ BEFORE MAKING CHANGES

**One file rules everything: `style.css`**

- `style.css` contains ALL styles for the site — 2,400+ lines
- `index.html` has NO inline `<style>` block. It depends entirely on `style.css`
- Guide and brand pages have inline CSS for their own components, but fonts, nav, footer, and shared elements all come from `style.css`

### Font variables (change only in `style.css` `:root`)
```css
--font-display: 'Syne', sans-serif;   /* headings */
--font-mono: 'DM Mono', monospace;    /* labels, stats, tags */
--font-body: 'DM Sans', sans-serif;   /* body text */
```

### Rules
1. **Font changes: edit `:root` in `style.css` only.** Never change font-family in HTML files.
2. **Never use regex to strip or modify CSS inside `<style>` tags.** It cannot be done safely.
3. **Never delete lines from `style.css`.** Only append new rules at the bottom.
4. **Test every change against index.html first** — if bars render, filters work, and the layout holds, proceed.

### Safe changes to make in `style.css`
- Color values in `:root`
- Font sizes and weights on named classes
- Padding and margin adjustments
- Adding new classes at the bottom of the file

### Never do this
- Replace `style.css` entirely with a rewritten version
- Strip inline `<style>` blocks from HTML files using find/replace
- Bulk-replace CSS across multiple HTML files in one operation

