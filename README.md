# knowyourbar.com — Project README and Claude Briefing

A protein bar search, filter, and review tool at **knowyourbar.com**. Users can search, filter, and compare 672+ protein bars by macros, ingredients, dietary certifications, and ingredient quality scores. The database is hand-researched by the owner and is the core proprietary asset of the site.

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
| `app.js` | All filter/search/sort/preset logic, table rendering, expand row, chip rendering |
| `bars.js` | Full bar database (672 bars) exported as a JS constant |
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
| `knowyourbar_scoring_schema.xlsx` | Master scoring schema. Upload to Claude to run score updates. |
| Your bar database Excel | Source of truth for all bar data (BarDB sheet) |

---

## How to Update the Site (Standard Pipeline)

**Step 1** — Add rows to the `BarDB` sheet in your bar database Excel. Fill in all macros, certifications, ingredients, website URL, and Amazon affiliate link where available.

**Step 2** — Upload both files to Claude: your bar database Excel and `knowyourbar_scoring_schema.xlsx`.

**Step 3** — Say "run score_and_export". Claude runs the full scoring pipeline and returns a new `bars.js`.

**Step 4** — Upload `bars.js` (and `app.js` if brands changed, `index.html` if meta count changed) to GitHub. Cloudflare auto-deploys in ~60 seconds.

**Step 5** — If new brand review pages were generated, upload those HTML files and the updated `sitemap.xml`.

**Step 6** — In Google Search Console, re-request indexing for any new or significantly updated pages.

**Note:** If files don't appear updated after uploading, delete them from GitHub first then re-upload to clear a GitHub caching quirk.

---

## Bar Database Structure (BarDB sheet)

| Column | Description |
|---|---|
| A: Brand Name | Exact brand name — must match BRAND_LIST in app.js |
| B: Flavor Name | Full flavor name as printed on packaging |
| C: Key | Formula: Brand + " | " + Flavor. Used as unique identifier. |
| D: Amazon Affiliate | Final affiliate URL: `https://www.amazon.com/dp/ASIN?tag=knowyourbar0f-20` |
| E+: All macros, certs, ingredients | Standard nutrition label data |

**Amazon Affiliate tag:** `knowyourbar0f-20`

The Key and Amazon Affiliate columns are Excel formulas — they evaluate correctly when pandas reads the file. No special handling needed.

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

### Score breakdown

Each bar stores `score_pos` and `score_neg` — total positive and negative weighted contributions. These appear as a two-tone bar (green/orange) in expand panels showing what drove the grade.

### Schema version

Current schema is v2: 1,011 canonical ingredients, 1,968 alias mappings, pre-parsed lines for all 541 original schema bars. New bars are auto-scored from raw ingredient text.

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

Chips render as minor (light orange) or elevated (dark orange-red, bolder) based on the ingredient's actual contribution to the score.

| Chip | Rule | Elevated when |
|---|---|---|
| Artificial Sweeteners | Sucralose, acesulfame, aspartame, or saccharin in full ingredient text | Drag > 2.0 pts or in top 5 positions |
| Sugar Alcohols | Sugar alcohol canonical present anywhere | Drag > 2.0 pts or in top 5 positions |
| Processed Oils | Palm, canola, soybean, or hydrogenated oils present (high-oleic excluded) | Oil drag > 0.5 pts |
| Sweetener Heavy | Sweetener category in top 3 positions | Always elevated |
| Collagen Protein | First protein ingredient is collagen | Always elevated |

"Sugar Alcohol Early" is no longer a separate chip — its signal is absorbed into Sugar Alcohols severity.

---

## Brand Review Pages

| Page | URL | Target keyword |
|---|---|---|
| Quest | /quest-bars.html | "are quest bars healthy" |
| RXBAR | /rxbar-review.html | "are rxbars healthy" |
| Clif Bar | /clif-bar-review.html | "are clif bars healthy" |
| Barebells | /barebells-review.html | "are barebells bars healthy" |

Each page contains: verdict card, authority line, snapshot stats, grade distribution, best/worst flavors, macro percentile cards, chip frequency chart, full expandable flavor table, bottom line, CTA.

Pages are generated by the brand page generator script (`/tmp/brand_page_v2.py` in Claude sessions). After running the scoring pipeline, regenerate all four with one command.

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
- "Buy on Amazon" button (orange, #FF9900) appears in expand rows only when non-null
- Uses `rel="noopener sponsored"` per Google guidelines
- 517 of 672 bars currently have affiliate links

---

## Filter Panel

### Quick filter presets

| Preset | Logic | Sort |
|---|---|---|
| High Protein Low Calorie | Protein calories >= 40% of total | Efficiency descending |
| High Protein, No Artificial Sweeteners | Protein >= 15g, no sucralose/acesulfame/aspartame/saccharin/maltitol | Protein descending |
| High Protein, Least Sugar | Protein >= 15g, sugar alcohol = 0 | Sugars ascending |
| High Fiber, Low Sugar | Fiber >= 8g, sugars <= 5g | Fiber descending |

### Brand filter

71 brands, scrollable checklist with search. `BRAND_LIST` in `app.js` is alphabetical — all brands use title case to ensure correct sorting.

**Current brands (71):** 88 Acres, Afar, Alani, Aloha, Anabar, Atkins, Atlas, B.T.R. Nation, Barebells, Bob's Red Mill, Bobo's, Built, CLIF Bar, Clif Builders, Clif ZBar, Daryl's Bars, David, Epic, Equate, FITCRUNCH, Fiber One, Forward, Fulfil, GNC Total Lean, Gatorade, Ghost, GoMacro, Gryp, Honey Stinger, IQ Bar, Jacob, Jambar, Kize, Laird, Larabar, Legendary, Lineage Provisions, Luna, Melo, Mezcla, Mosh, Munk Pack, Mush, Nature Valley, Neoh, Nick's, No Cow, NuGo, One, PEAK Protein, PROBar, Perfect Bar, Posana, Possible, Power Crunch, Prima, Pure Protein, Quest, RXBAR, Raw Rev, Ready, Redefine, Rise, Send, Simply Protein, Stars and Honey, The Gluten Free Brothers, Trubar, Wonderslim, Zing, think!

### Other filters

- Ingredient grade: A/B/C/D/F buttons. Also activated via `?band=X` URL param.
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

**Right:** Ingredient Quality Grade + score, +/- breakdown bar, insight chips with severity tiers, positive/concern ingredient columns, certifications, Visit product page link, Buy on Amazon button, full ingredient list in Title Case

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
| Total bars | 672 |
| With Amazon affiliate links | 517 |
| Brands | 71 |
| A (Clean) | 152 |
| B (Good) | 197 |
| C (Okay) | 187 |
| D (Poor) | 97 |
| F (Avoid) | 38 |
| Unscored | 1 (Power Crunch Chocolate Strawberry — no ingredient data) |

---

## Briefing Claude in a New Conversation

Paste this README and say:

> "I'm working on knowyourbar.com. Here's the README with full context. I need to [describe what you need]."

For scoring updates: attach your bar database Excel and `knowyourbar_scoring_schema.xlsx` then say "run score_and_export".

For brand page regeneration: run the scoring pipeline first, then say "regenerate brand pages".

For code changes: attach `index.html`, `app.js`, and/or `style.css` as needed.

Always upload changed files to GitHub right after Claude produces them.
