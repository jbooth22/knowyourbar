# knowyourbar.com — Project README and Claude Briefing

A protein bar search, filter, and review tool at **knowyourbar.com**. Users can search, filter, and compare 712+ protein bars by macros, ingredients, dietary certifications, and ingredient quality scores. The database is hand-researched by the owner and is the core proprietary asset of the site.

---

## Tech Stack

- **Plain HTML/CSS/JS** — no frameworks, no build process
- **Hosted on Cloudflare Pages** — free tier, auto-deploys when GitHub is updated
- **GitHub repo** — source of truth for all deployed files
- **Domain** — knowyourbar.com on GoDaddy, DNS managed by Cloudflare
- **Analytics** — GA4 (G-SW4MNP5W7J) in index.html
- **SEO** — Google Search Console verified, sitemap submitted

---

## File Structure

### Deployed to GitHub (live site)

| File | Purpose |
|---|---|
| `index.html` | Main page: hero, filter panel, results table |
| `style.css` | All design and layout including mobile responsive rules |
| `app.js` | All filter/search/sort/preset/URL state logic, table rendering, expand row, chip rendering |
| `bars.js` | Full bar database (712 bars) exported as a JS constant |
| `ingredient_scoring.html` | Scoring methodology explainer at /ingredient_scoring.html |
| `bar_hero.png` | Product bar image used in hero sections |
| `quest-bars.html` | Quest brand review page |
| `rxbar-review.html` | RXBAR brand review page |
| `clif-bar-review.html` | Clif Bar brand review page |
| `barebells-review.html` | Barebells brand review page |
| `sitemap.xml` | Submitted to Google Search Console |
| `robots.txt` | Allows all crawlers, points to sitemap |
| `README.md` | This file |
| `DEPLOY.md` | Deployment and update instructions |

### Saved locally (NOT on GitHub)

| File | Purpose |
|---|---|
| `knowyourbar_scoring_schema.xlsx` | Master scoring schema. **Must be uploaded with bar database for every pipeline run.** |
| Your bar database Excel | Source of truth for all bar data (BarDB sheet). Current: KYB_-_New_Protein_Bar_Database__2026___12_.xlsx |

---

## CRITICAL: How to Run the Scoring Pipeline

**Always upload BOTH files to Claude:**
1. Your bar database Excel
2. `knowyourbar_scoring_schema.xlsx`

Without the schema file, Claude rebuilds from a potentially stale cached state and scores may differ from the authoritative result. With both files, results are fully reproducible every session.

**Steps:**
1. Add rows to the `BarDB` sheet (macros, certifications, ingredients, website URL, Amazon affiliate link)
2. Upload both files to Claude
3. Say "run score_and_export"
4. Download `bars.js` (and `app.js` if brands changed, `index.html` if count changed)
5. Upload to GitHub — Cloudflare deploys in ~60 seconds
6. If new brand pages were generated, upload those + updated `sitemap.xml`
7. Request indexing in Google Search Console for new/updated pages

---

## Bar Database Structure (BarDB sheet)

| Column | Description |
|---|---|
| A: Brand Name | Exact brand name — must match BRAND_LIST in app.js |
| B: Flavor Name | Full flavor name as printed on packaging |
| C: Key | Formula: Brand + " \| " + Flavor. Used as unique identifier. |
| D: Amazon Affiliate | Final affiliate URL: `https://www.amazon.com/dp/ASIN?tag=knowyourbar0f-20` |
| E+: All macros, certs, ingredients | Standard nutrition label data |

**Amazon Affiliate tag:** `knowyourbar0f-20`

The Key and Amazon Affiliate columns are Excel formulas — they evaluate correctly when pandas reads the file.

---

## Ingredient Scoring System

### How scores are calculated

Each bar's ingredient list is parsed into individual ingredients mapped to canonical names with base scores from -4 (harmful) to +4 (excellent). Base scores are weighted by ingredient position.

**Final Score** = Sum of (base_score x position_weight) + count adjustment

### Position weights

| Position | Weight | Position | Weight |
|---|---|---|---|
| 1st | 1.00 | 6th | 0.44 |
| 2nd | 0.85 | 7th | 0.37 |
| 3rd | 0.72 | 8th | 0.31 |
| 4th | 0.61 | 9th | 0.26 |
| 5th | 0.52 | 10th+ | Decreasing from 0.22 |

### Count adjustment

| Count | Adjustment |
|---|---|
| 8 or fewer | +0.05 |
| 9-12 | 0.00 |
| 13-16 | -0.05 |
| 17-20 | -0.10 |
| 21+ | -0.15 |

### Score bands

| Grade | Label | Score range |
|---|---|---|
| A | Clean | 8.0 and above |
| B | Good | 4.0 to 7.9 |
| C | Okay | 0.0 to 3.9 |
| D | Poor | -3.0 to -0.1 |
| F | Avoid | Below -3.0 |

### Score breakdown fields

Each bar stores `score_pos` (sum of positive weighted contributions) and `score_neg` (sum of negative weighted contributions) in addition to the net `ingredient_score`. These power the two-tone green/orange breakdown bar shown in the expand panel.

### Schema

- 1,011 canonical ingredients, all vetted
- 1,968 alias mappings
- Pre-parsed ingredient lines for 541 original schema bars
- New bars are auto-scored via the enhanced `auto_score_full` function which computes full detail including pos/neg totals and all insight chips

### Known unmatched ingredients (schema gaps)

These ingredients appear in auto-scored bars but have no canonical match. Worth adding to the schema in a future update:

| Ingredient | Frequency | Suggested score | Notes |
|---|---|---|---|
| Palm Fruit Oil | 11 bars | -1 | Processed oil, similar to palm oil |
| Monkfruit Extract | 8 bars | 0 | Natural zero-cal sweetener, clean |
| Agar | 6 bars | 0 | Natural thickener from seaweed |
| Fructooligosaccharide | 5 bars | +1 | Prebiotic fiber, positive |
| Hemp Seeds | 4 bars | +3 | Whole food, high protein |
| Cashew | 2 bars | +3 | Whole food nut (alias of cashews) |
| Chia Seed | 2 bars | +3 | Whole food seed |
| Dried Blueberry | 1 bar | +2 | Whole food fruit |

---

## Insight Chips

### Positive chips (green)

| Chip | Rule |
|---|---|
| Protein Leads | First ingredient position is protein category |
| Quality Protein Source | High-quality protein (score >= 3) in top 5 positions |
| Whole Food Forward | 2+ of first 3 positions are whole_food category |
| Short Clean List | 8 or fewer scored ingredients |

### Neutral chips (gray)

| Chip | Rule |
|---|---|
| Fortified | Vitamin or mineral ingredients present |
| Long Ingredient List | 18+ scored ingredients |

### Concern chips — two severity tiers

Minor (light gray) vs elevated (solid red background, white text).

| Chip | Rule | Elevated when |
|---|---|---|
| Artificial Sweeteners | Sucralose, acesulfame, aspartame, or saccharin in full text | Drag > 2.0 pts or in top 5 |
| Sugar Alcohols | Sugar alcohol canonical present anywhere | Drag > 2.0 pts or in top 5 |
| Processed Oils | Palm, canola, soybean, or hydrogenated oils (high-oleic excluded) | Oil drag > 0.5 pts |
| Sweetener Heavy | Sweetener category in top 3 positions | Always elevated |
| Collagen Protein | First protein ingredient is collagen | Always elevated |

"Sugar Alcohol Early" is no longer a separate chip — absorbed into Sugar Alcohols severity.

---

## URL State (Shareable Filters)

The filter state is serialized into the URL via `history.replaceState` on every filter change. All filter combinations are shareable and bookmarkable.

**URL parameters:**

| Param | Example | Description |
|---|---|---|
| `grade` | `?grade=A` | Ingredient grade filter (also accepts legacy `?band=A`) |
| `preset` | `?preset=clean` | Active quick filter preset |
| `brands` | `?brands=Quest,Barebells` | Comma-separated selected brands |
| `protein` | `?protein=20` | Min protein slider (only when non-default) |
| `cal` | `?cal=200` | Max calories slider |
| `fat` | `?fat=10` | Max fat slider |
| `carbs` | `?carbs=25` | Max carbs slider |
| `sugar` | `?sugar=5` | Max sugars slider |
| `sa` | `?sa=0` | Max sugar alcohol slider |
| `fiber` | `?fiber=8` | Min fiber slider |
| `sodium` | `?sodium=300` | Max sodium slider |
| `certs` | `?certs=GF,Vegan` | Active certifications |
| `excl` | `?excl=sucralose,maltitol` | Ingredient exclusions |
| `q` | `?q=chocolate` | Flavor search text |
| `sort` | `?sort=Protein+(g):desc` | Sort column and direction |
| `bar` | `?bar=quest-chocolate-brownie` | Auto-expand a specific bar |

Sliders only appear in the URL when set to a non-default value, keeping URLs clean for common cases.

---

## Brand Review Pages

| Page | URL | Target keyword |
|---|---|---|
| Quest | /quest-bars.html | "are quest bars healthy" |
| RXBAR | /rxbar-review.html | "are rxbars healthy" |
| Clif Bar | /clif-bar-review.html | "are clif bars healthy" |
| Barebells | /barebells-review.html | "are barebells bars healthy" |

Each page: verdict card, authority line ("Based on analysis of 712+ protein bars..."), snapshot stats (context-aware: shows "None"/"All" instead of 0/N or N/N), grade distribution, best/worst flavors, macro percentile cards, chip frequency chart, full expandable flavor table, bottom line, CTA.

Generated by `/tmp/brand_page_v2.py` in Claude sessions. Regenerate all four after any scoring update.

### SEO on brand pages

- Title: "Are [Brand] Bars Healthy? (Full Breakdown + Score Analysis)"
- Single H1 with target keyword
- Article and FAQ schema (JSON-LD)
- 2,800-5,000 words per page
- Full ingredient lists in static HTML (crawlable, hidden until expanded)

---

## Amazon Affiliate Integration

- Affiliate tag: `knowyourbar0f-20`
- Links stored in `bars.js` as `Amazon Affiliate` field
- "Buy on Amazon" button (orange, #FF9900) appears only when non-null
- Uses `rel="noopener sponsored"` per Google guidelines
- 517 of 712 bars currently have affiliate links

---

## Filter Panel

### Quick filter presets

| Preset key | Label | Logic | Sort |
|---|---|---|---|
| `efficiency` | High Protein Low Calorie | Protein calories >= 40% of total | Efficiency desc |
| `clean` | High Protein, No Artificial Sweeteners | Protein >= 15g, no sucralose/acesulfame/aspartame/saccharin/maltitol | Protein desc |
| `lowsugar` | High Protein, Least Sugar | Protein >= 15g, sugar alcohol = 0 | Sugars asc |
| `fiber` | High Fiber, Low Sugar | Fiber >= 8g, sugars <= 5g | Fiber desc |

### Brand filter

79 brands, scrollable checklist with search. `BRAND_LIST` in `app.js` is alphabetical title-case.

**Current brands (79):** 88 Acres, Afar, Alio, Alani, Aloha, Amirita, Anabar, Atkins, Atlas, B.T.R. Nation, Barebells, Bob's Red Mill, Bobo's, Built, CLIF Bar, Clif Builders, Clif ZBar, Daryl's Bars, David, Epic, Equate, FITCRUNCH, Fiber One, Forward, Fulfil, GNC Total Lean, Gatorade, Ghost, GoMacro, Gryp, Honey Stinger, IQ Bar, Jacob, Jambar, Kize, Laird, Larabar, Legendary, Lenny & Larry's, Lineage Provisions, Luna, Magic Spoon, Melo, Mezcla, Mosh, Munk Pack, Mush, Nature Valley, Neoh, Nick's, No Cow, No Nuts!, NuGo, One, PEAK Protein, PROBar, Perfect Bar, Posana, Possible, Power Crunch, Prima, Pure Protein, Quest, RXBAR, Ratio, Raw Rev, Ready, Redefine, Rello, Rise, Send, Simply Protein, Skout, Stars and Honey, The Gluten Free Brothers, Trubar, Wonderslim, Zing, think!

### Other filters

- Ingredient grade: A/B/C/D/F buttons. Also activated via `?grade=X` URL param.
- Macro sliders: Min Protein, Max Calories, Max Fat, Max Carbs, Max Sugars, Max Sugar Alcohol, Min Fiber, Max Sodium
- Certifications: Vegan, GF, Dairy Free, Soy Free, Non-GMO, Nut Free, Kosher (AND logic)
- Ingredient exclusion: text match against full ingredient list, multiple tags

---

## Table

### Desktop columns
GRADE / CAL / PROT / FAT / CARB / FIBR / SGR / SGR ALC / CHOL / SODM / CERTS

GRADE column shows colored letter badge for every bar.

### Mobile columns (4 visible)
PROT / FAT / FIBR / SGR

### Expand row

**Left:** Nutrition Facts panel (all macros, vitamins/minerals if data exists)

**Right:** Ingredient Quality Grade + score, +/- breakdown bar (green = positive contributions total, orange = concern contributions total), insight chips with severity tiers, positive/concern ingredient columns, certifications, Visit product page link, Buy on Amazon button, full ingredient list in Title Case

---

## Design System

**Fonts:** Syne (headings/display), DM Sans (body text), DM Mono (labels/numbers/chips)

**CSS variables:**
- `--accent: #d4f000` (electric yellow-green)
- `--black: #0e0e0e` / `--white: #f7f5f0` / `--off-white: #efece6`
- `--muted: #6b6b65` / `--border: #d6d3cc`

**Grade colors:** A `#2a7a1f` / B `#5a8a2f` / C `#b89a00` / D `#c87020` / F `#c83020`

**Breakpoints:** 900px (sidebar to top), 700px (mobile columns, expand stacks)

---

## Current Database Stats

| Metric | Value |
|---|---|
| Total bars | 712 |
| With Amazon affiliate links | 517 |
| Brands | 79 |
| A (Clean) | 152 |
| B (Good) | 216 |
| C (Okay) | 199 |
| D (Poor) | 104 |
| F (Avoid) | 40 |
| Unscored | 1 (Power Crunch Chocolate Strawberry — no ingredient data) |

---

## Briefing Claude in a New Conversation

Paste this README and say:

> "I'm working on knowyourbar.com. Here's the README with full context. I need to [describe what you need]."

**For scoring updates:** attach BOTH your bar database Excel AND `knowyourbar_scoring_schema.xlsx`, then say "run score_and_export". The schema file is required every time for reproducible results.

**For brand page regeneration:** run the scoring pipeline first, then say "regenerate brand pages". The generator is at `/tmp/brand_page_v2.py` in Claude sessions.

**For code changes:** attach `index.html`, `app.js`, and/or `style.css` as needed.

Always upload changed files to GitHub right after Claude produces them.
