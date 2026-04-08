# knowyourbar.com

A hand-researched protein bar database with ingredient quality scoring, macro filtering, and comparison tools. No sponsored picks. No ads.

---

## What It Is

A static website hosted on Cloudflare Pages via GitHub. Users can search, filter, sort, and compare 756+ protein bars by macros, ingredient quality grade, brand, certifications, and dietary preferences. Every bar is scored A through F based on its ingredient list.

---

## File Structure

```
/
├── index.html              — Main bar finder tool
├── style.css               — All shared styles
├── app.js                  — All filter, sort, preset, comparison, and URL state logic
├── bars.js                 — Full bar database (756 bars, ~1.5MB)
├── bar_hero.png            — Hero image
├── sitemap.xml             — Sitemap for all pages
├── robots.txt
├── README.md               — This file
├── DEPLOY.md               — Deployment notes
│
├── quest-bars.html         — Brand review: Quest
├── rxbar-review.html       — Brand review: RXBAR
├── clif-bar-review.html    — Brand review: Clif Bar
├── barebells-review.html   — Brand review: Barebells
├── clean-protein-bars.html — SEO guide: Clean Protein Bars (with Key Findings + charts)
└── ingredient_scoring.html — Scoring methodology explainer
```

Note on file naming: Brand pages use inconsistent naming (quest-bars.html vs rxbar-review.html). Standardization to a /brands/ subfolder is planned but deferred until the site has enough link equity to absorb the redirects safely.

---

## Database

File: bars.js
Source: KYB - New Protein Bar Database (2026).xlsx (maintained locally, not in repo)
Current count: 756 bars across 90 brands
Affiliate tag: knowyourbar0f-20
Affiliate coverage: ~554 of 756 bars have Amazon affiliate links (~73%)

### Known unscored bars (missing ingredient data in spreadsheet)
- Power Crunch | Chocolate Strawberry
- MET-Rx | Peanut Butter Granola
- MET-Rx | Chocolate Chip Granola
- MET-Rx | Mint Super Cookie

These bars appear in the tool but show no grade. Add ingredient lists to the spreadsheet and re-run the pipeline to score them.

---

## Scoring System

Schema file: knowyourbar_scoring_schema_v3.xlsx (maintained locally, not in repo)
Canonicals: 1,047 ingredients
Aliases: 2,021 ingredient name variants

### How it works

1. Each bar's ingredient list is parsed into individual ingredients
2. Every ingredient is looked up against the alias map to a canonical ingredient
3. Each canonical has a base score from -4 (harmful) to +4 (excellent)
4. Scores are weighted by ingredient position (position 1 = 1.0x weight, decreasing)
5. A count adjustment is applied (short lists get a small bonus, very long lists get a penalty)
6. The total becomes the bar's ingredient quality score

### Grade bands
| Grade | Label | Score Range |
|-------|-------|-------------|
| A | Clean | >= 8.0 |
| B | Good | 4.0 to 7.9 |
| C | Okay | 0.0 to 3.9 |
| D | Poor | -3.0 to -0.1 |
| F | Avoid | Below -3.0 |

### Current grade distribution (756 bars)
A=158, B=234, C=209, D=109, F=42, Unscored=4

---

## Running the Pipeline

When new bars are added or ingredient data changes, run the scoring pipeline to regenerate bars.js.

Required files (upload both to Claude):
1. KYB - New Protein Bar Database (2026).xlsx — the bar spreadsheet
2. knowyourbar_scoring_schema_v3.xlsx — the scoring schema

Say: "I've uploaded the updated database and schema. Run score_and_export."

The pipeline will:
- Deduplicate bars by Brand + Flavor
- Score all bars with ingredients (schema lookup first, auto-scoring fallback)
- Export bars.js with all scored data
- Report grade distribution, affiliate link count, and any unscored bars

After the pipeline, update bar counts across all HTML files — search for the old count and replace with the new total. The ingredient scoring page pulls its count dynamically from bars.js so it updates automatically.

---

## Pages

### index.html — Main Tool
- Filter panel with 5 goal-oriented presets (Lose Weight, Clean Ingredients, Skip the Sugar, Most Protein Per Calorie, Keto Friendly)
- Core filters always visible: Presets, Ingredient Grade, Brand, Flavor keyword
- Advanced filters collapsed by default: Macro sliders, Certifications, Exclude ingredients
- Comparison feature: add up to 4 bars, shareable comparison URL
- URL state serialization (all filter state in URL params)
- FAQ accordion with FAQPage JSON-LD schema

### Brand Review Pages
Each follows the same structure:
- Hero with brand-specific headline
- Score overview with grade distribution chart
- Per-flavor bar table with ingredient list expand
- Pros/cons analysis
- FAQ accordion (5Q) with FAQPage JSON-LD schema

### clean-protein-bars.html
- Definition of "clean" (no artificial sweeteners, no sugar alcohols, A or B grade)
- Key Findings section with live data: big stat, 6 insight bullets, donut chart, bar chart
- Top 15 clean bars ranked with full bar cards
- CTA linking to /?preset=clean
- FAQ accordion (4Q) with FAQPage JSON-LD schema

### ingredient_scoring.html
- Full methodology: how ingredients are parsed, mapped, weighted, and scored
- Live grade distribution pulled from bars.js at runtime
- Ingredient count adjustment table
- Insight chip explainer
- FAQ accordion (5Q) with FAQPage JSON-LD schema

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

All pages share a consistent nav bar with hover dropdowns:
- Brand Reviews: Quest, RXBAR, Clif Bar, Barebells
- Guides: Clean Protein Bars
- How We Score (direct link)

Brand pages and standalone guides are self-contained (no style.css link). Nav CSS, FAQ CSS, and font loading are injected into their inline style blocks.

---

## SEO

Every page has:
- Unique title tag
- Meta description (under 158 characters)
- Canonical URL
- FAQPage JSON-LD schema with 4-5 questions
- Open Graph tags (og:title, og:description, og:url, og:image)
- Twitter card meta tags

The sitemap.xml includes all 7 pages. Submit to Google Search Console after any new page is added.

---

## Deployment

Host: Cloudflare Pages
Repo: GitHub (jbooth22)
Branch: main, auto-deploys on push

Current upload workflow (manual):
1. Download updated files
2. Go to GitHub repo
3. Delete old versions of changed files
4. Upload new files
5. Cloudflare detects the push and deploys automatically

Planned improvement: Set up local Git to replace the manual upload process. After one-time setup, git add . && git commit -m "..." && git push deploys everything in one step.

---

## Pending Work

### Features
- Macro rank — show where each bar ranks (e.g. "47th highest protein") in expanded row or comparison overlay
- Similar Bars — cross-brand discovery based on macro profile similarity, 3 results in expanded row
- More brand pages — Kind, Nature Valley, FITCRUNCH, Magic Spoon
- More SEO guides — protein bars for weight loss, protein bars without artificial sweeteners
- AI comparison summary — Claude API call to generate "choose this bar if..." per comparison

### Data
- Add ingredient data for 4 unscored bars (3 MET-Rx, 1 Power Crunch)
- Continue adding affiliate links (202 bars still missing)
- File structure reorganization: /brands/, /guides/, /assets/ subfolders (after link equity builds)

### DevOps
- Set up local Git for proper deployment workflow
- Standardize brand page file naming (quest.html, rxbar.html, etc.)

---

## Analytics

Google Analytics: G-SW4MNP5W7J (tag in index.html)

---

Last updated: April 2026
