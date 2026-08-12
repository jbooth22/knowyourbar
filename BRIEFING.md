# KnowYourBar.com — Project Briefing
*Upload this file at the start of every new Claude session.*
*Last updated: August 2026*

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
index.html              — Homepage. Links out to bar-finder.html for the actual tool; do not
                           confuse the two, see "Preset deep links" below for a bug this caused.
bar-finder.html         — The actual bar finder tool (filter/search/sort/compare UI, loads app.js).
                           Preset deep links (`?preset=SLUG`) point here, not at index.html.
app.js                  — All filter, search, sort, compare, expand logic
bars.js                 — Full bar database (1,000+ bars)
style.css               — ALL shared styles — single source of truth
_headers                — Cloudflare Pages cache + security headers
TEMPLATE_BRAND.html     — Master template for brand review pages
TEMPLATE_GUIDE.html     — Master template for lifestyle guide pages
score_and_export.py     — Scoring pipeline script
knowyourbar_scoring_schema_v4.xlsx — Ingredient scoring schema
build_brand_rankings.py — Regenerates all-protein-bar-brands.html from bars.js. Run this instead of
                           hand-editing that page. See BRAND_RANKING_METHODOLOGY.md before touching it.
sitemap.xml
robots.txt
llms.txt             — LLM crawler discovery file (do not delete)
BRIEFING.md             — This file (upload to every Claude session)
README.md               — Technical documentation
DEPLOY.md               — Deploy process
QA.md                   — QA checklist
BRAND_STANDARDS.md      — Locked v1 visual system (--bs-* tokens in style.css). Migration in progress, not
                           complete — see "Brand Standards v1 migration" section below before touching colors,
                           buttons, or type on any page.
BRAND_RANKING_METHODOLOGY.md — Canonical KYB Brand Score formula, category thresholds, and distribution-tier
                           list for all-protein-bar-brands.html. Load this before touching that page, same as
                           GUIDE_CRITERIA.md for guide pages.

Brand review pages (all rebuilt from TEMPLATE_BRAND.html):
  quest-bars.html
  rxbar-review.html
  clif-bar-review.html
  barebells-review.html
  kind-bars-review.html
  quest-vs-rxbar.html

Guide pages (all rebuilt from TEMPLATE_GUIDE.html):
  clean-protein-bars.html
  no-artificial-sweeteners.html
  no-sugar-alcohols.html
  no-seed-oils.html
  low-sugar-high-protein.html
  keto-protein-bars.html
  best-bars-for-diabetics.html
  caffeine-protein-bars.html   — added July 2026, fulfills the "bars with caffeine" future-feature item
  glp1-protein-bars.html

Data / visualization pages:
  all-protein-bar-brands.html  — Full brand summary table (all brands, filterable)
  brand-quadrant.html          — Magic Quadrant scatter plot (macro efficiency vs ingredient quality)

Other:
  ingredient_scoring.html      — How we score page
  flavor-map.html              — Sankey diagram visualization
```

---

## Brand review pages — TEMPLATE_BRAND.html

**Status as of 2026-08-11: barebells-review.html is the gold-standard reference for this template** — layout, font consistency, editorial grouping, and voice have all been through a full verification pass (headless-browser computed-style checks, not eyeballing) and a real content-quality revision. `quest-bars.html` and `rxbar-review.html` were rebuilt to the *structural* template earlier (2026-08-09) but predate the fixes below — they're on the known-issues list to bring up to the same standard, one page per session (see "Known issues" below). TEMPLATE_BRAND.html itself has been updated to match Barebells; **treat any older brand page as a reference for content only, never for markup or CSS pattern.**

All brand pages use TEMPLATE_BRAND.html. This is the locked standard. Every future brand page (Clif, KIND, and any new brand) must use this template as it stands today, not a copy of an older live page.

### Template section order
1. Head: page title (`<title>`/og/twitter — SEO-optimized), meta description, canonical, 4 JSON-LD schemas (headline uses the H1 text, not the page title — see "Title vs. H1" below)
2. Nav
3. Hero (H1 + short answer paragraph — H1 text can differ from the `<title>` tag, see below)
4. Macro breakdown grid (9 tiles: **Grade Range first**, then Protein, Protein/100cal, Calories, Total Sugar, Sugar Alcohol, Fiber, Total Fat, Net Carbs) + SEO blurb. There is no separate "scorecard snapshot" section — this grid replaced it entirely; do not recreate a stat strip above it.
5. Overview summary (2-3 paragraphs, grounded in specific measurable deltas — see "Voice and analysis principles" below)
6. Grade distribution bar
7. Best and worst flavor cards (with chips)
8. Ingredient quality patterns — grouped **Good qualities / Concerning qualities / Neutral**, not by frequency tier (see below)
9. Full flavor table (11 columns, rich expand rows — see "Flavor table structure")
10. Bottom line (2 paragraphs)
11. **Which [Brand] flavor should you actually buy** (`.pick-tile-grid`/`.pick-tile`, 3-5 situational picks grounded in real per-flavor deltas — new section added 2026-08-11, see below)
12. Discover module (CTA + related reading, one fused card)
13. Brand comparison table (grade ranges shown **best to worst**, e.g. "B → F", not worst to best — see below)
14. Every brand we've reviewed (scalable pill-grid, `.brand-link-pill` uses `border-radius: var(--bs-radius)` on brand-v1 pages, not a full capsule — see CSS gotchas)
15. FAQ section (7 questions minimum)
16. Footer (brand-block left, nav right, copy div OUTSIDE site-footer-inner)

### Grade range display convention (locked 2026-08-11)
**Always show grade ranges best-to-worst** (e.g. "B to F", "A to B"), never worst-to-best ("F to B"). This applies everywhere a range appears: hero copy, FAQ answers (JSON-LD and visible, keep them in sync), the picks-section intro, and every row of the brand-comparison table's grade-pair badges (`<span class="table-grade-badge grade-BEST">` first, arrow, then `grade-WORST`). It reads more naturally and matches how a person would actually describe "how good does this get, and how bad."

### Ingredient quality patterns grouping (locked 2026-08-11)
Group chips by **type** — "Good qualities" (positive), "Concerning qualities" (concern), "Neutral" (neutral, omit the group if there are none) — sorted most-frequent-first within each group. **Do not** group by frequency tier ("Every flavor / Most flavors / Some flavors"); that was the original approach and reads worse than grouping by what actually matters to the reader, which is whether the pattern helps or hurts. Every chip name and count still must come verbatim from `verify_brand_data.py`'s chip-frequency output — grouping changed, data-sourcing rule didn't.

### Title vs. H1 (separated 2026-08-11)
The page `<title>` (and og:title/twitter:title) and the visible H1 no longer have to be identical strings — optimize the meta title for search/social, and let the H1 read naturally as the actual page heading. Example from Barebells: title "Are Barebells Bars Healthy? 25 Flavors Ranked", H1 "Are Barebells Bars Healthy? We Ranked All 25 Flavors". The JSON-LD Article `headline` field should match the **H1**, not the meta title, since that's what's actually on the page.

### Flavor table structure
- 11 columns: BAR, CAL, PROT, P/100, FAT, CARB, FIBR, SGR, SGR ALC, CERTS, GRADE — same column set and classes as Bar Finder's table, minus the brand-name line and compare column
- Expand rows are rich, not a simple macro strip: `.expand-meta` (size/type/serving), `.expand-buy-row`, `.macro-rank-grid` (5 metrics — Protein/Calories/Sugar/Fiber/Fat — each ranked against the full ~1,088-bar database, green tag if in the top 25%, gray otherwise; Fat never gets the directional green treatment, it's always neutral), `.nutr-panel` (full nutrition facts), `.score-tile` (grade badge, score, positive/negative breakdown bar, chips, positive/concern ingredient columns), `.ingr-block` (full title-cased ingredient list)
- Percentile ranks in `.macro-rank-grid` must be computed against the live `bars.js` database at build time (see Barebells' `build.py` pattern) — never hand-typed or copied from another brand's page, the database size and every bar's standing changes between rebuilds
- colspan must be 11 on all ingr rows
- toggleIngr index starts at 0 and increments per row with no gaps

### JSON-LD schemas required on every brand page
1. Article (with url, image, datePublished, dateModified, about — headline matches H1, see above)
2. Dataset (static, same on every page)
3. BreadcrumbList (3 levels: Home > Brand Reviews > Page)
4. FAQPage (minimum 7 questions, must match visible FAQ exactly, word for word)

### SEO rules
- og:type must be "article" on brand pages (not "website")
- Page title formula: "Are [BRAND] Bars Healthy? [N] Flavors Ranked | Know Your Bar" (can vary slightly per brand for SEO fit — doesn't have to match H1, see above)
- H1 formula: "Are [BRAND] Bars Healthy? We Ranked All [N] Flavors" (or close variant — this is what a reader sees, optimize for that, not for keyword density)
- Meta description: lead with a specific data point, under 155 chars, no em dashes
- H1: one per page
- H2: content sections only — CTA title uses p tag, Explore More uses div

### Voice and analysis principles (added 2026-08-11, from the Barebells rewrite pass)
- **Don't lean on the raw ingredient score number as if it means something on its own.** It isn't out of 10 and has no external context. Explain *why* there's a gap (different protein source, more sweetener stacking, etc.), not "the gap is 11.7 points." Grade letters and specific ingredient/macro facts carry the argument; the raw score is supplementary data, not the story.
- **Ground "two lines"/sub-brand narratives in measurable deltas, not just a label.** "The vegan line scores worse" is weak. "The vegan line averages 4g less protein per bar (a 21% drop) and 3 of 4 vegan flavors stack a second sugar alcohol source that only 1 of 21 dairy flavors uses" is the actual finding. If a brand has no official sub-brand distinction, say so plainly rather than implying one exists ("Barebells doesn't officially split into sub-brands, but the data shows two distinct formulas hiding under one label").
- **Add a genuine "which flavor for which situation" analysis**, not just best/worst. Real examples from Barebells: highest-protein tie-breaker, lowest floor for a specific problem macro, best option within a disadvantaged sub-line, and what to skip outright. Every claim in that section still needs to trace back to `verify_brand_data.py` output or a direct computation from `bars.js` — same rule as everywhere else.
- **Keep percentile claims separated by metric.** Protein and sugar can both be "top 25%" by coincidence, but don't write one sentence that implies they share a percentile when they don't — pull each number from its own verified figure.
- **Verify compound claims, not just simple ones.** "All D grades belong to the vegan line" is a claim about grade *composition*, and it's easy to get wrong by pattern-matching from the F grades. Check it against the actual per-flavor list before writing it, the same as any other data claim.
- **Flavor names must match `bars.js` exactly, including spelling.** Don't let a flavor name drift across a rewrite pass (e.g. "Hazlenut Nougat" becoming "Hazelnut Nougat" or "Hazel Nougat" partway through a page). Grep the final file for the exact name to confirm consistency.
- **Treat the brand name as a singular entity** in verb agreement ("Barebells is," "Barebells lands," "Barebells carries"), not plural ("Barebells are," "Barebells have") — matches how the rest of the site already refers to brands.

---

## Brand ranking page — all-protein-bar-brands.html (rebuilt 2026-08-10)

Full rebuild, not an incremental edit. Old version had a static table with a hand-typed brand count that had drifted (title said 125, JSON-LD said 95+, live count was 133), and every "see this brand in the tool" link was broken — see the bug below. New version is fully generated by `build_brand_rankings.py`; read `BRAND_RANKING_METHODOLOGY.md` before touching the ranking formula, categories, tiers, or the highlight/best-in-category write-ups. Do not hand-edit the brand cards directly in the HTML — re-run the script.

**What changed structurally:** every brand gets a true 1-to-N rank by a composite score (60% ingredient quality / 25% protein efficiency / 15% fiber — full rationale in the methodology doc), a distribution tier (Widely Available / Mid-Size & Specialty / Small & Online — editorial, hand-curated, not derived from bars.js), and a lineup category (Protein First / Solid Macro Profile / Whole Food & High Fiber — computed from protein/100cal and fiber thresholds). The page has a live filter/sort/search bar (tier, category, sort by protein/fiber/flavors/name, brand search) implemented as vanilla JS toggling `.brk-hidden` on static cards, not a client-side re-render — every card is still server-rendered HTML for SEO, consistent with the "Brand page table architecture decision" below.

**Bar Finder deep-link bug fixed:** `app.js` matches `?brand=` params against slugified brand names with no fallback for un-slugified input. The old page linked with raw brand names (`?brand=Gryp`), which never matched, so every brand link on the page was broken. New links use the same slugify logic as app.js (`slugify()` in `build_brand_rankings.py`), verified with 0 mismatches across all 148 brands via a live Node check against app.js's own function. **If you ever add a new `bar-finder.html?brand=` link anywhere else on the site, slugify it the same way or it will silently fail exactly like this did.**

**Layout/font bug fixed 2026-08-11 — applies to ANY page-guide page, not just this one:** `.content` only gets a max-width from `.page-brand .content` in style.css. On `page-guide` pages, width comes from `.section-inner` (nested inside `.section`), and headings/body text only pick up the brand-v1 fonts (Barlow Condensed / DM Sans) if they carry the `.section-title` / `.section-body` classes — bare `<h2>`/`<p>` get browser default styling with no width constraint. The first build of this page used bare tags with no `.section-inner` wrapper, which produced exactly what it looked like: full-width unaligned text in a fallback system font. Fixed by wrapping every section's content in `<div class="section-inner">` and tagging headings/body copy correctly. **If a future page-guide page looks unstyled and full-width, check this first before assuming style.css didn't load.**

**Ranking score de-branded 2026-08-11:** the composite ranking number is intentionally not surfaced as a named/branded metric anywhere on the page — no boxed formula UI, no score badge on cards, no proper-noun name for it in copy. Jeff's call: explain the methodology, don't market the number.

**CSS:** new `.brk-*` classes appended to the end of style.css (pure append, no existing rules touched). Reuses `.bchip`, `.cert-badge`, `.boost-badge`, `.table-grade-badge`, `.macro-grid`/`.macro-card`, `.brand-compare-grade-pair`/`-arrow`, `.faq-item`, `.explore-cta*`, `.snapshot`/`.snap-item`, `.verdict-items` rather than redefining equivalents.

**brands_manifest.json:** `total_db_brand_count` updated from the stale `133+` to `148+` to match the live count, then `generate_brand_links.py` was re-run to propagate that into the pill-grid link on every brand page that already has the `BRAND_LINKS_START` marker (currently just `quest-bars.html` — RXBAR/Clif/Barebells/KIND review pages don't have the marker yet since they're still on the older template, so their brand-count text is still stale until they get rebuilt).

---

## Guide pages — TEMPLATE_GUIDE.html

All lifestyle guide pages have been rebuilt from TEMPLATE_GUIDE.html. This is the locked standard for all guide pages including the diabetics page.

### Template section order
1. Head: title, meta description, canonical, 4 JSON-LD schemas, OG/Twitter tags
2. Nav
3. Hero (H1 + short answer paragraph, hero sub text color: #e8e4dc)
4. Snapshot stats (uses .snapshot / .snap-item pattern — bar count, grade breakdown, key macro)
5. Top Picks (3 goal cards — .picks-grid with grade badge, brand, flavor, macros, buy links)
6. Category explainer + key factors (.score-card callouts with stat + description)
7. Findings dark section (.findings with .big-stat + .insights-grid)
8. Best brands / brands to avoid (.verdict-card pro/con)
9. Bar list table (columns vary by guide — default: Bar, Grade, Score, Protein, Cal, Sugar)
10. Bar Finder CTA (.explore-cta linking to pre-filtered tool URL)
11. Explore More (3 .explore-more-card links)
12. FAQ (7+ questions, must match JSON-LD exactly)
13. Footer

### Guide table notes
- First 25 rows visible, rows 26+ hidden with class="hidden-bar" and Show More toggle
- Keto guide uses Fat + Net Carbs columns instead of Calories + Sugar — patch manually if template is updated
- Diabetics guide uses 5-filter criteria: sugar, net carbs, fiber, no maltitol

### JSON-LD schemas required on every guide page
1. Article
2. Dataset (static, same as brand pages)
3. BreadcrumbList
4. FAQPage (minimum 7 questions, must match visible FAQ exactly)

### Disclaimer rule (diabetics page and similar)
Pages targeting health conditions must include a visible disclaimer: "We are not doctors or dieticians. These are the qualities we know people look for, so that's what we factored in."

---

## Brand Standards v1 migration — READ BEFORE TOUCHING COLORS OR BUTTONS

`BRAND_STANDARDS.md` defines a locked future visual system (`--bs-ink`, `--bs-paper`, ink-stamp buttons, Barlow Condensed, sentence case, no uppercase mono labels). It is **not fully live**. Current actual state:
- `style.css` has both token sets defined: the legacy `--black`/`--white`/`--accent` tokens (still what nearly every page actually renders with) and the new `--bs-*` tokens (used only in scoped `.brand-v1` overrides).
- Almost every page now has `<body class="brand-v1">`, but that only activates a handful of specific overrides already written into style.css — it does **not** mean the page has been rebuilt to the new spec. Check `BRAND_STANDARDS.md`'s migration checklist for which pages are actually done.
- Recent work (buy button standardization, boost badges) was done against the **legacy** token set, since that's what's actually rendering. Don't assume a full `--bs-*` rebuild is imminent — check with the site owner before investing in new legacy-system polish vs. waiting for the v1 migration on any given page.
- Before adding any new color, button style, or type treatment: check `BRAND_STANDARDS.md` first. If the page isn't migrated yet, match the existing legacy pattern on that page rather than introducing `--bs-*` tokens piecemeal.

---

## CSS architecture — READ BEFORE TOUCHING ANYTHING

**style.css is the single source of truth for all styles.**

- index.html has an inline `<style>` block for homepage-only CSS (hero, stats bar, sample card, grade strip, finder section, goal cards). This is intentional — do not move it to style.css.
- Brand/guide pages have minimal inline CSS. Historically this was a full duplicate `:root` block per page — as of the August 2026 cleanup pass (see below), most of that is gone. Everything else comes from style.css.
- style.css is 3,700+ lines. Do not replace it wholesale. Only append or use targeted str_replace.

### CSS variables (defined in style.css :root)
```css
--black:      #0e0e0e
--white:      #f7f5f0
--off-white:  #efece6
--accent:     #d4f000   /* yellow-green */
--muted:      #888880
--border:     #d6d3cc
--font-display: 'DM Sans', sans-serif /* headings — Syne was removed (single-story 'g' clipping); never reintroduce it */
--font-mono:    'DM Mono', monospace  /* labels, stats */
--font-body:    'DM Sans', sans-serif /* body text */
--radius:     6px
--radius-lg:  10px
```

### Page type classes
- Brand review pages: `<body class="page-brand">`
- Guide pages: `<body class="page-guide">`
- index.html: plain `<body>`
- Nearly all pages also carry `<body class="brand-v1">` — this opts them into partial BRAND_STANDARDS v1 overrides (see "Brand Standards v1 migration" below). It does not mean the page is fully migrated.

### New CSS classes added in April/May 2026
These exist in style.css and should not be duplicated:
- `.bw-chips` — chip row inside best/worst cards
- `.macro-summary-text` — accent-left blurb after macro grid
- `.explore-cta`, `.explore-cta-inner`, `.explore-cta-eyebrow`, `.explore-cta-title`, `.explore-cta-sub`, `.explore-cta-btns`, `.explore-cta-btn` — dark CTA tile
- `.explore-more-label`, `.explore-more-grid`, `.explore-more-card`, `.explore-more-title`, `.explore-more-desc` — explore more link cards
- `.ingr-macros` — macro strip inside expand rows
- `.ingr-chips` — chip row inside expand rows
- `.ingr-buy` — buy button inside expand rows
- `.site-footer-brand-block` — footer brand+tagline wrapper
- `.site-nav-mobile-bar-finder` — pinned Bar Finder button in mobile nav (always visible, outside hamburger)

### New CSS classes added in July 2026
- `.boost-badges`, `.boost-badge` — small indigo pills under the flavor name in the bar-finder results table, flagging Caffeine / Creatine / Vitamins as differentiators. Vitamin badge triggers at >2% DV on any single vitamin (not mineral) field — see `VITAMIN_DV_THRESHOLD` constant in `app.js`. Do not reuse this color for anything else; it's reserved for these three supplement flags.

### New CSS classes added in August 2026 (Barebells rebuild)
- `.pick-tile-grid`, `.pick-tile`, `.pick-tile-flavor` — the "which flavor for which situation" section. Reuses `.macro-card`'s shell (border, padding, uniform-height mechanism) via `class="macro-card pick-tile"` on each tile, so it inherits the font/height fixes below for free. When a tile recommends more than one flavor, put each name on its own line with `<br>` — comma-separated flavor lists inside a tile are hard to scan.
- `.macro-rank-grid`, `.macro-rank-cell`, `.macro-rank-lbl`, `.macro-rank-val`, `.macro-rank-tag` (`.rank-green`/`.rank-gray`), `.nutr-panel`, `.nutr-row`, `.nutr-label`, `.nutr-val`, `.score-tile`, `.score-tile-header`, `.score-breakdown`, `.score-breakdown-bar`, `.sbd-pos`/`.sbd-neg`, `.score-chips`, `.score-ingr-cols`, `.ingr-col`, `.ingr-col-label`, `.ingr-col-item` — the rich flavor-table expand row. All of these already exist in style.css from the Quest rebuild; they were just never fully documented here.

### Font-family gotcha — brand-v1 data elements (fixed 2026-08-11)
A number of data/numeric classes reference the old `--font-mono` variable (`'DM Mono'`) directly with no `.brand-v1` override, so on brand-v1 pages they silently render in the wrong monospace font instead of the brand-v1 standard (`--bs-font-data` = `'IBM Plex Mono'`) — visually inconsistent with everything around them but easy to miss since both are still "a mono font." **This was not caught by any automated check — it took a full leaf-node computed-style scan of the live page in a headless browser to find every instance.** Fixed classes: `.num-cell`, `.macro-avg`, `.bw-score`, `.col-num`, `.cert-badge`, `.bw-chip-group-label`, `.ingr-macros span`, `.macro-rank-val`, `.macro-rank-tag`, `.score-number`, `.sbd-label-pos`, `.sbd-label-neg`, `.nutr-val` — see the two `.brand-v1` rule groups in style.css right after the macro-card section (one group also normalizes color to `--bs-text-dim`, the other is font-only because those elements carry semantic colors like rank-green/gray or pos/neg green/orange that a forced color would erase). **If a future brand-v1 element looks like it's in "the old font," check whether it has a `.brand-v1` override for `font-family` before assuming style.css didn't load — it's very likely this exact bug pattern, not a loading problem.** Also check for inline `style="font-family:var(--font-mono)"` — CSS class overrides can't touch those; fix them directly in the HTML (the grade-distribution breakdown line under the grade bar had exactly this bug).

### Hero/content alignment gotcha (fixed 2026-08-11)
`.hero-inner` and `.content` are both centered 820px boxes, but historically `.hero` supplied horizontal padding as an *outer* wrapper while `.content` supplied its own horizontal padding *inside* its own box. Both boxes land at the same outer edge (the centering math works out identical either way), but the actual text inside them started at different x-positions — the H1 sat 24px to the left of every H2 below it. Fixed by moving the horizontal padding onto `.hero-inner` to match `.content`'s box model exactly (`.page-brand .hero`/`.page-guide .hero` now has `padding: 2.25rem 0 2rem`, no left/right; `.page-brand .hero-inner`/`.page-guide .hero-inner` now has `padding: 0 1.5rem`). Verified with `getBoundingClientRect().left` in a headless browser at both desktop and mobile widths, not by eye. **Don't reintroduce left/right padding on `.hero` directly — it belongs on `.hero-inner` now.**

### Buy button conventions (locked July 2026 — do not deviate)
Every "buy" link on the site follows one of exactly two styles, regardless of page:
- **Primary — "Buy on Amazon":** solid black background (`var(--black)`), white text. Classes: `.amazon-link` (bar-finder detail panel), `.cmp-buy-btn` (comparison table), `.buy-btn` (guide/brand listing cards), `.cta-amazon`, `.bar-link-amz`, `.bar-buy-btn`.
- **Secondary — "Buy from Brand":** transparent background, black text, black border (outlined, not solid). Classes: `.visit-link` (bar-finder detail panel), `.cmp-site-btn` (comparison table), `.bar-link-site` (guide/brand listing cards).
Both classes for a given context should always render side by side with the primary (solid) first. **Never use orange (`#FF9900` or similar) for any buy button** — that was the pre-July-2026 default and has been fully removed sitewide. If a new page or template needs a buy button, copy one of the six primary classes above; do not invent a new one.

### Homepage-only CSS classes (in index.html inline style block)
- `.hero-trust` — time/ease anchor line under the CTA button
- `.hero-a-row`, `.hero-a-names`, `.hero-a-sep`, `.hero-a-all` — A-rated bar name row in hero
- `.hero-sample`, `.hero-sample-card`, `.hero-sample-header`, `.hero-sample-badge`, `.hero-sample-bar-*`, `.hero-sample-chip`, `.hero-sample-macros` — sample bar result card
- `.trust-strip`, `.trust-strip-mark`, `.trust-strip-quote` — trust strip between stats bar and finder
- `.goal-card--featured` — "Show me the best" featured goal card variant

### Hard rules — never break these
1. Never use regex to strip or modify CSS inside `<style>` tags
2. Never replace style.css entirely — only append or use targeted str_replace
3. Never remove a wrapper `<div>` without checking div balance afterwards
4. After ANY HTML change: run the div balance check in QA.md
5. After ANY JS change: run `node --check app.js`
6. Always work from the actual uploaded file, not from memory of previous sessions

---

## Brand page cleanup pass (August 2026)

Every brand page originally shipped with a full duplicate `<style>:root{...}</style>` block in its `<head>`, redeclaring `--black`, `--white`, `--off-white`, `--accent`, `--muted`, `--border`, `--font-display`, `--font-mono`, `--font-body`, `--radius`, `--radius-lg`, values that already exist in style.css's global `:root`. This caused real bugs (see below) and made it hard to tell, just by reading a page, which font or color was actually going to render, since it required tracing the cascade across two `:root` blocks plus the `.brand-v1` override layer.

**Root-cause bugs found and fixed in `style.css` (shared, affects every page):**
1. `.bar-flavor` was defined twice, the second definition hardcoded `font-family: 'Inter'`, a font outside the three-font system entirely. Removed; it now correctly inherits the body font.
2. `.brand-v1 .cta-amazon` (best/worst card buy buttons) had a color/background override but no `font-family`, so it fell through to a mono font. Added `font-family: var(--bs-font-body)`.
3. `.brand-v1 .explore-cta-eyebrow` ("Know Your Bar" label above the dark CTA tile) was never hidden, unlike `.brand-v1 .hero-eyebrow`, so it still rendered as the exact uppercase-letter-spaced-mono pattern the brand standard retired. Now hidden, matching `.hero-eyebrow`'s treatment.

**Per-page local `:root` cleanup**, verified with a headless-browser computed-style diff before and after each edit, not just a code read:
- `quest-bars.html`, `rxbar-review.html`: local `:root` block **removed entirely**. Every value matched the global default exactly, and the one page-level use of `--muted` (the grade-distribution count line) turned out to already be overridden by the sitewide `.brand-v1.page-brand p { color: var(--bs-text-dim) !important; }` rule, so it had no visible effect either way.
- `clif-bar-review.html`, `kind-bars-review.html`: local `:root` **trimmed to `--muted` only**. These two pages have flavor-table sub-label spans (e.g. "(Builders)", "(ZBar)", "(Protein Max)") whose color genuinely depends on the local `--muted` value (`#888880`) rather than the global one (`#5a5a54`), and no sitewide rule catches those spans. Removing `--muted` here would have visibly darkened those labels.
- `barebells-review.html`: local `:root` **trimmed to `--muted` only**. Its page-specific "Two Lines" comparison component (`.line-block-desc`, `.line-note`) depends on it the same way.
- `quest-vs-rxbar.html`: already had no local `:root` block, nothing to do.

**Still open:** none of this touched page structure, layout, or content, only the CSS variable layer. The bigger Quest rebuild (replacing the top stat section, standardizing best/worst cards, mirroring the Bar Finder table) is still pending and will be templated against whatever the Bar Finder rebuild lands on, so it isn't scoped yet.

---

## Brand page table architecture decision (August 2026)

When the flavor table on brand/guide pages gets rebuilt to mirror Bar Finder's redesigned table, **it stays static HTML, generated to match Bar Finder's markup, not a live embed of Bar Finder itself.** Three approaches were considered:

- **A — Static, generated (chosen).** Brand/guide pages keep their current architecture: no `bars.js`, no `app.js`, hand-baked HTML matching Bar Finder's current design, scoped to that page's bars. The only change from today is discipline: generate this from Bar Finder's actual current row/expand-panel markup each time, rather than re-deriving it from memory in a fresh session, which is what caused drift before.
- **B — Live embed, filters pre-locked.** Rejected. Every brand page (16-25 bars) would ship the same ~2.2MB database + full app as the page showing all 1,000 bars, and would require new conditional branches inside `app.js` (hide compare button, hide brand column) that add complexity to the single most important shared file on the site.
- **C — Shared render functions, page-specific data.** The architecturally "correct" long-term answer: extract Bar Finder's row/panel rendering into reusable functions both Bar Finder and brand pages call, so markup and behavior are one codebase with zero drift, while brand pages still only load their own small bar list. Not done now, since it means refactoring `app.js`'s rendering internals while Bar Finder's design is still actively moving. Worth revisiting as its own project once Bar Finder is stable.

Why A over C for now: A matches the site's existing architecture (no new dependency between brand pages and `app.js`), keeps brand pages fast and immediately crawlable for SEO (no client-side render needed for content to be indexable), and carries the least risk to `app.js`/Bar Finder while both are still changing. C remains the better end-state if drift becomes a recurring problem.

---

## index.html hero — current structure (May 2026)

The homepage hero has been significantly updated. Current structure in order:

1. Eyebrow: "The Protein Bar Database · No Sponsored Picks"
2. H1: "Every protein bar scored A-F on ingredient quality"
3. Subhead: "1,000+ bars graded A-F — see which ones actually pass. No affiliate deals, no brand payments. See how we score →"
4. CTA button: "Find My Bar →" (accent yellow, single button only — secondary button removed)
5. Trust anchor: "Answer 3 questions · Get your match in 30 seconds" (directly under button)
6. A-rated bar row: "Top A-rated bars: RXBAR Chocolate Sea Salt · Perfect Bar Dark Chocolate · IQ Bar Lemon Blueberry → See all 150+ A-rated bars"
7. Sample bar result card: Atlas Salted Peanut Butter — B grade, score 6, real chips and macros from database
8. (End of hero)

**Do not add a secondary CTA button.** The "How We Score" link lives as inline text in the subhead only.

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

Bars scored using `score_and_export.py` against `knowyourbar_scoring_schema_v4.xlsx`
- 1,163 canonical ingredients
- 2,194 aliases
- Sub-ingredients in parentheses get 60% weight
- 150+ A-rated bars in current database

### Grade bands (v4 schema)
| Grade | Label | Score range |
|-------|-------|-------------|
| A | Clean | >= 8.0 |
| B | Good | 4.0 to 7.9 |
| C | Okay | 0.0 to 3.9 |
| D | Poor | -3.0 to -0.1 |
| F | Avoid | < -3.0 |

### Count adjustment
| Ingredient count | Adjustment |
|-----------------|------------|
| 1-8 | +0.05 |
| 9-12 | 0.00 |
| 13-16 | -0.05 |
| 17-20 | -0.10 |
| 21+ | -0.15 |

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

### Preset deep links — VALID SLUGS ONLY
Brand and guide pages link to the bar finder tool with `/bar-finder.html?preset=SLUG` (**not** `/?preset=SLUG` — `bar-finder.html` is the actual finder page; `index.html` is a separate homepage that itself links out to `/bar-finder.html?preset=...` for its own goal cards. A stray `/?preset=` link exists in index.html's FAQ and appears to be stale — don't copy that pattern). Only these 6 slugs are defined in `app.js`'s `PRESETS` object — any other value silently does nothing:

| Slug | Label | Criteria |
|------|-------|----------|
| `lose_weight` | Lose Weight | 20g+ protein, under 200 cal, under 3g sugar, A/B grade |
| `clean` | Clean Ingredients | A grade, 12g+ protein, no artificial sweeteners or sugar alcohols |
| `skip_sugar` | Skip the Sugar | Under 2g sugar, under 4g sugar alcohol, no maltitol/sorbitol, A/B grade |
| `high_protein` | Most Protein Per Calorie | Protein efficiency ranked, 15g+ protein, A/B/C grade |
| `keto` | Keto Friendly | Under 5g net carbs, 10g+ fat, A/B grade |
| `glp1` | GLP-1 Friendly | 15g+ protein, under 200 cal, under 4g sugar, 3g+ fiber, no sugar alcohols, A/B grade (added, undocumented until 2026-08-11 — verify against `app.js` directly if this list and the live file ever disagree, the file is canonical) |

**Never invent preset slugs.** If a guide topic doesn't map cleanly to one of these, use the closest match or link to `/bar-finder.html` (unfiltered) with a relevant label.

### Results table columns
BAR | CAL | PROT | P/100 | FAT | CARB | FIBR | SGR | SGR ALC | CERTS | GRADE | CMP

P/100 = Protein grams per 100 calories (sortable)

Under the flavor name in the BAR cell, Caffeine/Creatine/Vitamins boost badges render when present (see `.boost-badge` above) — not a table column, but part of that cell's content.

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

**llms.txt** lives at `/llms.txt` in the repo root. It documents the scoring system, database, brand reviews, and guides for AI crawlers (ChatGPT, Claude, Perplexity, etc.). Update it when adding new brand pages or guide pages.

---

## What's working well
- Mobile experience (62% of traffic) — priority to maintain
- Filter panel and bar expand on desktop
- XSS patched (exclusion tags use DOM methods)
- Brand review pages all rebuilt to consistent TEMPLATE_BRAND.html
- Guide pages all rebuilt to consistent TEMPLATE_GUIDE.html
- SEO schemas complete on all brand and guide pages
- ingredient_scoring.html fixed (horizontal scroll, grade bands table, copy)
- Sitemap updated — all live pages indexed
- Page speed grade A-93
- Cloudflare cache headers configured via _headers file

---

## Known issues / next priorities

### Brand pages needing the 2026-08-11 standard applied
`quest-bars.html` and `rxbar-review.html` were rebuilt to the structural template on 2026-08-09, before the alignment fix, font-family fix, grade-range tile, Good/Concerning patterns grouping, best-to-worst grade ordering, the "which flavor should you buy" section, and the voice/analysis pass documented above. They still work and the CSS fixes in style.css already apply to them (those were shared-file fixes, not per-page), but their **content and section list** predate all of it. Bring each up to the Barebells standard, one page per session, using Barebells as the structural and voice reference — not a from-scratch rebuild, since the underlying data/table architecture is already correct on both. `clif-bar-review.html` and `kind-bars-review.html` are still on the older pre-2026-08-09 template entirely and need the full rebuild (sub-brand scoping decision required first for both — Clif Bar vs. Clif Builders, KIND vs. KIND Protein Max).

### CSS
- Footer layout on brand pages may still have a stacking issue — verify on mobile before marking resolved

### Content
- KIND Minis and Thins not yet in database — pending scoring
- Some duplicate ASINs in bars.js: Barebells Caramel Peanut/Salted Peanut Caramel share B0DT7KS2QB; Clif ZBar Chocolate Mint and Clif Bar Cool Mint Chocolate share B0CXQ71XY8; Clif Builders Chocolatey Peanut Butter and Crispy Peanut Butter Chocolate share B09QHBBGJT
- Trust strip on homepage uses founder statement placeholder — swap for a real external quote (Reddit mention, press) when available

### Future features
- Protein type filter (whey vs plant vs egg)
- Net carbs column in main table
- Brand comparison pages (Quest vs Barebells, RXBAR vs KIND, Clif vs KIND, Quest vs ONE Bar)
- More brand review pages: Perfect Bar, GoMacro, ONE Bar, IQBar, Aloha, Built Bar
- More guide pages: best bars for weight loss, bars with real food ingredients
- ~~bars with caffeine~~ — done, see `caffeine-protein-bars.html`
- ~~bars with vitamins~~ — partially covered by the Vitamins boost badge in the main finder table (July 2026); a dedicated guide page is still open if wanted

---

## Deploy process

1. Make changes in Claude
2. Run QA script from QA.md — must pass before upload
3. Download files from Claude
4. Upload to GitHub repo (drag and drop to repo root)
5. Cloudflare Pages auto-deploys within ~60 seconds
6. Purge Cloudflare cache if changes not showing
7. Test with `?v=N` query string to bypass browser cache during testing

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
