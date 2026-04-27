# KnowYourBar.com — Project Briefing
*Upload this file at the start of every new Claude session.*
*Last updated: April 2026*

---

## What this site is

KnowYourBar.com is a protein bar database and finder tool. We scored 1,000+ protein bars A-F by ingredient quality using a transparent, rule-based scoring system. No sponsorships. No bias. Users can filter, compare, and find bars that match their dietary goals.

**Live at:** knowyourbar.com
**Hosting:** Cloudflare Pages (deploys from GitHub, manual upload)
**GitHub:** jbooth22/knowyourbar
**Analytics:** GA4 — G-SW4MNP5W7J
**Affiliates:** Amazon (tag: knowyourbar0f-20), AvantLink, Impact

---

## File structure

```
index.html              — Main bar finder tool (homepage)
app.js                  — All filter, search, sort, compare, expand logic
bars.js                 — Full bar database (1,000+ bars)
style.css               — ALL shared styles — single source of truth
TEMPLATE_BRAND.html     — Master template for brand review pages
score_and_export.py     — Scoring pipeline script
knowyourbar_scoring_schema_v3.xlsx — Ingredient scoring schema
sitemap.xml
robots.txt
BRIEFING.md             — This file (upload to every Claude session)
README.md               — Technical documentation
DEPLOY.md               — Deploy process
QA.md                   — QA checklist

Brand review pages (all rebuilt from TEMPLATE_BRAND.html):
  quest-bars.html
  rxbar-review.html
  clif-bar-review.html
  barebells-review.html
  kind-bars-review.html
  quest-vs-rxbar.html

Guide pages:
  clean-protein-bars.html
  no-artificial-sweeteners.html
  no-sugar-alcohols.html
  no-seed-oils.html
  low-sugar-high-protein.html
  keto-protein-bars.html

Other:
  ingredient_scoring.html   — How we score page
  flavor-map.html           — Sankey diagram visualization
```

---

## Brand review pages — TEMPLATE_BRAND.html

All five brand pages (Quest, RXBAR, Clif Bar, Barebells, KIND) have been rebuilt from scratch using TEMPLATE_BRAND.html. This is the locked standard. Every future brand page must use this template.

### Template section order
1. Head: title, meta description, canonical, 4 JSON-LD schemas, OG/Twitter tags
2. Nav
3. Hero (H1 + short answer paragraph)
4. Scorecard snapshot (6 stats: flavors, grade range, score range, protein, calories, sweetener status)
5. Overview summary (2-3 paragraphs)
6. Grade distribution bar
7. Best and worst flavor cards (with chips)
8. Macro breakdown grid (6 macros) + SEO blurb
9. Ingredient quality patterns (chip frequency)
10. Full flavor table (6 columns: Flavor, Grade, Score, Protein, Cal, Sugar)
11. Bottom line (2 paragraphs)
12. Explore all bars CTA (dark tile, p tag not h2, 3 filter buttons)
13. Explore more (3 link cards with descriptions, div not h2)
14. FAQ section (7 questions minimum)
15. Footer (brand-block left, nav right, copy div OUTSIDE site-footer-inner)

### Flavor table structure
- 6 columns only — no Insights column in the table header
- Chips live inside the expand row (.ingr-chips), not in the table
- Expand row contains: ingr-macros strip, ingredient list, ingr-chips, ingr-buy button
- colspan must be 6 on all ingr rows
- toggleIngr index starts at 0 and increments per row

### JSON-LD schemas required on every brand page
1. Article (with url, image, datePublished, dateModified, about)
2. Dataset (static, same on every page)
3. BreadcrumbList (3 levels: Home > Brand Reviews > Page)
4. FAQPage (minimum 7 questions, must match visible FAQ exactly)

### SEO rules
- og:type must be "article" on brand pages (not "website")
- Title formula: "Are [BRAND] Bars Healthy? We Scored All [N] Flavors | Know Your Bar"
- Meta description: lead with a specific data point, under 155 chars, no em dashes
- H1: one per page, matches title formula
- H2: content sections only — CTA title uses p tag, Explore More uses div

---

## CSS architecture — READ BEFORE TOUCHING ANYTHING

**style.css is the single source of truth for all styles.**

- index.html has NO inline style block. It depends entirely on style.css.
- Brand/guide pages have minimal inline CSS (just :root vars). Everything else from style.css.
- style.css is 3,700+ lines. Do not replace it wholesale. Only append or use str_replace for targeted edits.

### CSS variables (defined in style.css :root)
```css
--black:      #0e0e0e
--white:      #f7f5f0
--off-white:  #efece6
--accent:     #d4f000   /* yellow-green */
--muted:      #888880
--border:     #d6d3cc
--font-display: 'Syne', sans-serif    /* headings */
--font-mono:    'DM Mono', monospace  /* labels, stats */
--font-body:    'DM Sans', sans-serif /* body text */
--radius:     6px
--radius-lg:  10px
```

### Page type classes
- Brand review pages: `<body class="page-brand">`
- Guide pages: `<body class="page-guide">`
- index.html: plain `<body>`

### New CSS classes added in April 2026 (brand template rebuild)
These exist in style.css and should not be duplicated:
- `.bw-chips` — chip row inside best/worst cards
- `.macro-summary-text` — accent-left blurb after macro grid
- `.explore-cta`, `.explore-cta-inner`, `.explore-cta-eyebrow`, `.explore-cta-title`, `.explore-cta-sub`, `.explore-cta-btns`, `.explore-cta-btn` — dark CTA tile
- `.explore-more-label`, `.explore-more-grid`, `.explore-more-card`, `.explore-more-title`, `.explore-more-desc` — explore more link cards
- `.ingr-macros` — macro strip inside expand rows
- `.ingr-chips` — chip row inside expand rows
- `.ingr-buy` — buy button inside expand rows
- `.site-footer-brand-block` — footer brand+tagline wrapper

### Hard rules — never break these
1. Never use regex to strip or modify CSS inside `<style>` tags
2. Never replace style.css entirely — only append or targeted str_replace
3. Never remove a wrapper `<div>` without checking div balance afterwards
4. After ANY HTML change: run the div balance check in QA.md
5. After ANY JS change: run `node --check app.js`
6. Always work from the actual uploaded file, not from memory of previous sessions

---

## Writing rules — apply everywhere on this site

This site must read like a knowledgeable person wrote it, not an AI. These rules are non-negotiable and apply to every page, every section, every sentence.

**Never use:**
- Em dashes ( — ) anywhere. Not in copy, not in meta descriptions, not in JSON-LD
- "It is worth noting"
- "It is important to"
- "Furthermore" / "Moreover" / "Additionally"
- "Delve" / "Leverage" / "Robust" / "Utilize" / "Crucial"
- "This is a deliberate brand strategy"
- Passive constructions that soften direct claims
- Filler qualifiers that pad without adding meaning

**Always use:**
- Short, direct sentences
- Specific numbers rather than vague descriptors
- Active voice
- Plain English verdicts — state what the data shows, don't hedge everything
- Second person ("you") when addressing the reader directly

**Tone:** Knowledgeable, direct, slightly opinionated but always data-backed. Think a trusted friend who has actually read all the ingredient labels, not a product reviewer covering their bases.

---

## The bar database (bars.js)

Each bar object has these key fields:
```
Brand Name, Flavor Name, score_band (A/B/C/D/F), ingredient_score (numeric),
Calories, Protein (g), Total Fat (g), Saturated Fat (g), Total Carbohydrates (g),
Dietary Fiber (g), Sugars (g), Sugar Alcohol (g), Sodium (mg), Cholesterol (mg),
Ingredients (full text), Amazon Affiliate (URL), Website (URL),
positive_ingredients, concern_ingredients,
Vegan (Y/N), Gluten Free (Y/N), Dairy Free (Y/N), Soy Free (Y/N),
Non-GMO (Y/N), Nut Free (Y/N), Kosher (Y/N)
```

Grade colors: A=#2a7a1f, B=#5a8a2f, C=#b89a00, D=#c87020, F=#c83020
Grade definitions: A=Clean, B=Good, C=Okay, D=Poor, F=Avoid

Net carbs formula: Total Carbs - Fiber - (Sugar Alcohol / 2)

### Building brand pages from bars.js
When building or rebuilding a brand page, always extract data directly from bars.js using node or Python. Do not rely on the old HTML page for ingredient data — it may be inaccurate. The pipeline:
1. Filter bars.js by brand name (check for all sub-brands, e.g. "Clif Builders", "Clif ZBar")
2. Sort by ingredient_score descending
3. Use exact ingredient text, amazon affiliate URL, and macro data from the database
4. Build rows using the template row pattern from TEMPLATE_BRAND.html

---

## Scoring pipeline

Bars scored using `score_and_export.py` against `knowyourbar_scoring_schema_v3.xlsx`
- 1,048+ canonical ingredients
- 2,024+ aliases
- Sub-ingredients in parentheses get 60% weight
- Grades: A (>=7), B (>=4), C (>=1), D (>=-2), F (<-2)

To rescore: upload new bar Excel + schema file and say "run score_and_export"

---

## Current site features (index.html + app.js)

### Filter panel
- Lifestyle presets: Lose Weight, Clean Ingredients, Skip the Sugar, High Protein, Keto Friendly
- Ingredient Quality Grade: A/B/C/D/F toggle buttons
- Brand filter: searchable multi-select
- Flavor keyword text search
- Macro sliders: Protein (min), Calories (max), Fat (max), Carbs (max), Sugars (max), Sugar Alcohol (max), Fiber (min), Net Carbs (max)
- Certifications: Vegan, GF, DF, SF, Non-GMO, Nut Free
- Exclude ingredients: text input, XSS-safe

### Results table columns
BAR | CAL | PROT | P/100 | FAT | CARB | FIBR | SGR | SGR ALC | CERTS | GRADE | CMP

P/100 = Protein grams per 100 calories (sortable)

### Bar expand
Shows: macro rank grid, nutrition facts panel, ingredient quality score, certifications, ingredient list, similar bars, buy links

---

## SEO structure

Every page has:
- Unique title and meta description
- Canonical link
- FAQPage JSON-LD schema
- Article JSON-LD schema (brand/guide pages)
- Dataset JSON-LD schema
- BreadcrumbList JSON-LD schema (brand pages)
- Open Graph tags
- GA4 tracking

Meta description strategy: lead with a specific surprising data point, not a generic description. No em dashes.

---

## What's working well
- Mobile experience (62% of traffic) — priority to maintain
- Filter panel and bar expand on desktop
- XSS patched (exclusion tags use DOM methods)
- Brand review pages all rebuilt to consistent template
- SEO schemas complete on all brand pages

---

## Known issues / next priorities

### CSS
- Footer layout on brand pages still has a stacking issue (on the list to fix)

### Content
- KIND Minis and Thins not yet in database — pending scoring
- Some duplicate ASINs in bars.js flagged: Barebells Caramel Peanut/Salted Peanut Caramel share B0DT7KS2QB; Clif ZBar Chocolate Mint and Clif Bar Cool Mint Chocolate share B0CXQ71XY8; Clif Builders Chocolatey Peanut Butter and Crispy Peanut Butter Chocolate share B09QHBBGJT

### Future features
- Protein type filter (whey vs plant vs egg)
- Net carbs column in main table
- Brand comparison pages (Quest vs Barebells, etc.)
- Full brand rankings page

---

## Deploy process

1. Make changes in Claude
2. Run QA script from QA.md — must pass before upload
3. Download files from Claude
4. Upload to GitHub repo (drag and drop to repo root)
5. Cloudflare Pages auto-deploys within ~60 seconds
6. Purge Cloudflare cache if changes not showing
7. Test with `?v=N` query string to bypass browser cache

### Rollback
Go to GitHub → file → History → find last working commit → download raw → re-upload

---

## Session discipline — how to work with Claude efficiently

**Start every session:**
1. Upload this BRIEFING.md
2. Upload the specific files you want to change (from GitHub)
3. State exactly what you want changed

**During session:**
- Claude works from uploaded files, not memory
- Claude runs verification checks before presenting output files
- Upload and verify before moving to the next change

**Never:**
- Ask Claude to change fonts/styles across all pages at once
- Let Claude use regex to modify HTML structure
- Upload files without seeing verification pass first
- Assume Claude remembers anything from a previous session — always upload BRIEFING.md

---

*This briefing is the single source of truth for working on this project.*
*Everything Claude needs is in this file plus whatever files you upload.*
