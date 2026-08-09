# KnowYourBar.com — Project Briefing
*Upload this file at the start of every new Claude session.*
*Last updated: 2026-08-09 — consolidated with README.md/DEPLOY.md and TEMPLATE_BRAND.html rebuilt in the same pass, see Locked Global Rules below*

---

## What this site is

KnowYourBar.com is a protein bar database and finder tool. We scored 1,000+ protein bars A-F by ingredient quality using a transparent, rule-based scoring system. No sponsorships. No bias. Users can filter, compare, and find bars that match their dietary goals.

**Live at:** knowyourbar.com
**Hosting:** Cloudflare Pages (deploys from GitHub, manual upload)
**GitHub:** jbooth22/knowyourbar
**Analytics:** GA4 — G-SW4MNP5W7J
**Affiliates:** Amazon (tag: knowyourbar0f-20), AvantLink, Impact

---

## Locked global rules — read this section even if nothing else
*Added 2026-08-09 because the "1,000+" rule below lived only in GUIDE_CRITERIA.md,
a file not on the mandatory upload list, and a brand-page session had no way to
discover it. These are the rules that cause real damage if missed, gathered in
the one file every session actually loads. Full detail and rationale for each
stays in its original section/file; this is the index, not a replacement.*

- **Never state the exact database size.** Always "1,000+" as the total bar
  count, everywhere: copy, meta tags, JSON-LD. Specific per-guide qualifying
  counts ("714 bars qualify") are fine and should stay specific. Full detail: GUIDE_CRITERIA.md.
- **Never write a grade, score, macro range, percentile, or ingredient pattern
  claim without running `verify_brand_data.py` first.** See "MANDATORY: run
  verify_brand_data.py" below. This is what quest-bars.html violated on 2026-08-09.
- **Run `diff_bars_upload.py` the moment a new bars.js is uploaded**, before
  touching any page. See "When a new bars.js is uploaded" below.
- **Never use regex for content or structural edits.** Literal string
  replacement only. Regex bulk edits have caused site damage before.
- **Every structural HTML edit needs a div/section/tr/td tag-balance count
  before and after**, with comments stripped before counting (comments can
  contain example tags that look like real markup and produce false mismatches).
- **No em dashes anywhere.** Not in copy, not in meta descriptions, not in
  JSON-LD. Full writing rules below under "Writing rules."
- **File delivery is scoped to only the files actually changed.** Don't
  re-send untouched files.
- **`style.css` caches for 1 hour, not 1 week.** If any document says a week,
  that document is stale — the Cache Headers table under Deploy Process is
  the current, verified truth (checked against the live `_headers` file).
- **Certification fields that are `null` in bars.js mean "not tracked," not
  "confirmed No."** Never write a percentage (including 0%) for untracked data.
- **FAQPage JSON-LD must match the visible FAQ text on the page, word for
  word.** Not yet true on every page as of 2026-08-09 — audit before assuming
  it's already correct on a page you didn't just touch.

---

## File structure

```
index.html              — Main bar finder tool (homepage)
app.js                  — All filter, search, sort, compare, expand logic
bars.js                 — Full bar database (1,000+ bars)
style.css               — ALL shared styles — single source of truth
_headers                — Cloudflare Pages cache + security headers. See Cache Headers
                           table under Deploy Process for current values — do not trust
                           a remembered value, re-check this file if it matters.
TEMPLATE_BRAND.html     — Master template for brand review pages. Rebuilt 2026-08-09 to
                           the "Option A" static-table architecture — see the note at the
                           top of that file before using it.
TEMPLATE_GUIDE.html     — Master template for lifestyle guide pages
TEMPLATE_VS.html        — Master template for brand-vs-brand comparison pages
score_and_export.py     — Scoring pipeline script
verify_brand_data.py    — Data verification script. Run before writing ANY brand/guide
                           page copy that cites grades, scores, macros, or ingredient
                           patterns. See "MANDATORY: run verify_brand_data.py" below.
diff_bars_upload.py     — Diffs old vs. new bars.js on every database upload to see what
                           actually changed. See "When a new bars.js is uploaded" below.
knowyourbar_scoring_schema_v4.xlsx — Ingredient scoring schema
sitemap.xml
robots.txt
llms.txt             — LLM crawler discovery file (do not delete)
BRIEFING.md             — This file (upload to every Claude session). Single source of
                           truth for process/rules — README.md, QA.md, GUIDE_CRITERIA.md,
                           and BRAND_STANDARDS.md hold detail that belongs to them
                           specifically, but this file is the index and the one place
                           locked global rules are guaranteed to be visible.
README.md               — Public-facing repo overview. Points here for anything process-
                           related rather than duplicating it, to avoid the two files
                           drifting apart the way they did before 2026-08-09.
QA.md                   — QA checklist, including Section 0 (data accuracy, run before
                           writing copy) and the automated pre-upload checks
GUIDE_CRITERIA.md       — Guide-page-specific filter formulas and live counts. The
                           site-wide "1,000+" rule is centralized in this file's Locked
                           Global Rules section, not here — this file covers only what's
                           specific to guide pages.
BRAND_STANDARDS.md      — Locked v1 visual system (--bs-* tokens in style.css), text form.
                           Migration in progress, not complete — see "Brand Standards v1
                           migration" section below before touching colors, buttons, or
                           type on any page.
brand-standards.html    — Same content as BRAND_STANDARDS.md, rendered with swatches and
                           type specimens. Keep both in sync if either changes; BRAND_STANDARDS.md
                           is the one meant for reliable text retrieval.

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

**Template rebuilt 2026-08-09 to the Bar Finder-mirrored architecture.** quest-bars.html was rebuilt first and used to validate the design (Playwright-tested at 1400px/390px, zero console errors), then TEMPLATE_BRAND.html itself was updated to match — see the architecture note at the top of that file. RXBAR, Clif, Barebells, and KIND still need the same rebuild; they currently carry the old 6-column table and 3-stat scorecard. Before rebuilding any of them: run `verify_brand_data.py` for that brand first, do not port numbers or structure from the existing live page.

Only quest-bars.html currently matches TEMPLATE_BRAND.html's live structure. RXBAR, Clif, Barebells, and KIND were built from an earlier version of this template and still need the 2026-08-09 rebuild applied. Every future brand page must use the current template.

### Template section order
1. Head: title, meta description, canonical, 4 JSON-LD schemas, OG/Twitter tags
2. Nav
3. Hero (H1 + short answer paragraph)
4. Scorecard snapshot (5 stats: flavors, grade range, artificial sweetener %, sugar alcohol % + avg, certifications)
5. Overview summary (2-3 paragraphs)
6. Grade distribution bar
7. Best and worst flavor cards (grade badge, six macros, Good/Concerning chip groups, buy buttons on both)
8. Macro breakdown grid (6 macros) + SEO blurb
9. Ingredient quality patterns (chip frequency, from real score_insights data only)
10. Full flavor table (11 columns mirroring Bar Finder: BAR, CAL, PROT, P/100, FAT, CARB, FIBR, SGR, SGR ALC, CERTS, GRADE)
11. Bottom line (2 paragraphs)
12. Explore all bars CTA (dark tile, p tag not h2, 3 filter buttons)
13. Explore more (3 link cards with descriptions, div not h2)
14. FAQ section (7 questions minimum)
15. Footer (brand-block left, nav right, copy div OUTSIDE site-footer-inner)

### Flavor table structure
- 11 columns, mirroring Bar Finder exactly minus the brand-name line and minus the compare column
- Chips live inside the expand row (.ingr-chips), never in the visible table
- Expand row contains, in order: buy buttons (.expand-buy-row, .amazon-link/.visit-link), ingr-macros strip, ingredient list, ingr-chips
- colspan must be 11 on every ingr row — if a column is added or removed, update every row's colspan, not just the first
- toggleIngr index starts at 0 and increments per row with no gaps, ordered cleanest (best score) to worst
- Every chip name must come from verify_brand_data.py's chip frequency output — never invented

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

### MANDATORY: run verify_brand_data.py before writing ANY page copy
**Incident (2026-08-09):** a Quest rebuild found every editorial claim on the live
quest-bars.html was stale or fabricated. Claimed grade range B->A, actual B->C.
Claimed scores 4.4-9.3, actual 1.7-6.2. Claimed best flavor at grade A/9.3, actual
grade B/6.2. Two ingredient chips referenced in copy ("Protein Leads", "Long
Ingredient List") don't apply to any of Quest's 16 flavors in the real
score_insights data (they're real, defined chips used elsewhere in the database
— Quest's specific ingredient lists just never trigger them) — the copy was
either generic/borrowed rather than checked against Quest's actual data. This
had been live and indexed by Google for an unknown period.

To prevent this from recurring, `verify_brand_data.py` (repo root) computes
ground-truth stats directly from bars.js: grade distribution, score range,
best/worst flavor with real chips, macro ranges/averages, percentile rankings
against the full 1,000+ bar database, real ingredient chip frequency, and
artificial sweetener / sugar alcohol / certification prevalence.

**Run it before writing or approving a single sentence of brand or guide page
copy that cites a grade, score, percentile, macro range, or ingredient pattern:**
```
python3 verify_brand_data.py "Quest"
python3 verify_brand_data.py "Clif" --include-subbrands
```
Cross-check every number in the draft against the script's output. If a number
in existing copy doesn't match, the existing copy is wrong — bars.js is always
the source of truth, never the other way around. Certification fields that are
`null` (not `"No"`) must be reported as "not tracked," never asserted as 0%.
Chip names that don't appear in the script's chip frequency table for that brand
must not appear anywhere in that brand's page copy, even if the chip is real and
used elsewhere in the database — a chip that's valid for one brand isn't
automatically valid for another, and it isn't automatically valid for this one.

This applies to every brand page rebuild still pending (RXBAR, Clif, Barebells,
KIND) and to any future one.

### When a new bars.js is uploaded
Before doing anything else with a newly uploaded bars.js:
1. Run `diff_bars_upload.py old_bars.js new_bars.js` (keep the previous bars.js
   around specifically to make this possible) to see exactly what changed —
   added bars, removed bars, and any bar whose score, grade, macros,
   ingredients, or score_insights changed. It prints which brands are affected.
2. For every brand the diff flags as affected, re-run `verify_brand_data.py`
   before touching that brand's page, even if the page was rebuilt recently.
   Scores and grades can shift between scoring-pipeline runs — a page that was
   accurate last month is not guaranteed accurate today.
3. If a brand's grade distribution or score range changed since its page was
   last written, flag it to the person before making any other edit. Don't
   silently rewrite the copy — they may want to review the change themselves,
   same as the quest-bars.html discovery on 2026-08-09.

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
Brand and guide pages link to the bar finder with `/?preset=SLUG`. Only these 5 slugs are defined in `app.js` — any other value silently does nothing:

| Slug | Label | Criteria |
|------|-------|----------|
| `lose_weight` | Lose Weight | 20g+ protein, under 200 cal, under 3g sugar, A/B grade |
| `clean` | Clean Ingredients | A grade, 12g+ protein, no artificial sweeteners or sugar alcohols |
| `skip_sugar` | Skip the Sugar | Under 2g sugar, under 4g sugar alcohol, no maltitol/sorbitol, A/B grade |
| `high_protein` | High Protein | Highest protein efficiency (g per calorie), 15g+ protein, A/B/C grade |
| `keto` | Keto Friendly | Under 5g net carbs, 10g+ fat, A/B grade |

**Never invent preset slugs.** If a guide topic doesn't map cleanly to one of these, use the closest match or link to `/?` (unfiltered) with a relevant label.

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

### CSS
- Footer layout on brand pages may still have a stacking issue — verify on mobile before marking resolved

### Content
- RXBAR, Clif, Barebells, KIND brand pages still on the pre-2026-08-09 template (old 6-column table, 3-stat scorecard, unverified copy). Rebuild each against `verify_brand_data.py` output, not the existing page.
- FAQPage JSON-LD does not match visible FAQ text word-for-word on at least quest-bars.html (confirmed 2026-08-09, predates that session). Other pages not yet audited — check before assuming any page is compliant with the "must match exactly" rule.
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
*Consolidated from the former DEPLOY.md (deleted 2026-08-09 — this section is now the only copy).*

### Any change
1. Make changes in Claude
2. Run QA script from QA.md — must pass before upload (Section 0's data checks run even earlier, before copy is written)
3. Download files from Claude
4. Upload to GitHub repo (drag and drop to repo root)
5. Cloudflare Pages auto-deploys within ~60 seconds
6. Test with `?v=N` query string to bypass browser cache during testing
7. Purge Cloudflare cache manually only if step 6 still shows stale content after the relevant file's cache window (see Cache Headers below) — for most files this resolves itself within the hour without a manual purge

**Rollback:** GitHub → file → History → find last working commit → download raw → re-upload.

### Standard bar database update
Use whenever bars are added, affiliate links change, or ingredient data is fixed.
1. Update the bar database Excel
2. Upload both files to Claude: the bar database Excel, and `knowyourbar_scoring_schema_v4.xlsx`
3. Say "run score_and_export"
4. **Run `diff_bars_upload.py` against the previous bars.js before doing anything else** — see "When a new bars.js is uploaded" above. This replaces any manual eyeballing of what changed.
5. Download bars.js and upload to GitHub
6. Do NOT search-and-replace an exact bar count into HTML files. The site's copy rule is "1,000+" as the denominator everywhere (see Locked Global Rules) — the only time any number changes is if the *threshold* itself is crossed (e.g. "1,000+" becomes "2,000+"), which is a deliberate copy decision, not a mechanical find-and-replace.

Requires locally: `pip install pandas openpyxl` (only needed if running `score_and_export.py` outside Claude).

### How the scoring pipeline works (settled — do not change)
All bars are scored from raw ingredient text using a single unified code path. Only `Canonical_Ingredients` and `Alias_Map` are loaded from the schema; the schema's `Ingredient_Lines` and `Products` sheets are not used. Sub-ingredients inside parentheses get 60% weight (present in smaller amounts than top-level ingredients). Every scored bar gets insight chips generated using the same logic. This was settled after multiple sessions of iteration — if a future session suggests reverting to schema pre-parsed scoring, point it here.

### Adding a new brand review page
1. Run the pipeline first (fresh bars.js)
2. Run `verify_brand_data.py "<Brand Name>"` before writing any copy
3. Generate the page from `TEMPLATE_BRAND.html`
4. Update the nav dropdown on ALL existing pages (nav is inline in each HTML file)
5. Add to `sitemap.xml`
6. Upload all changed files
7. Request indexing in Google Search Console

### Adding a new SEO guide page
1. Run `verify_brand_data.py` for any brand named in the guide, and cross-check filter-formula counts in `GUIDE_CRITERIA.md`
2. Generate from `TEMPLATE_GUIDE.html`
3. Update the nav Guides dropdown on all pages
4. Add to `sitemap.xml`
5. Upload and request indexing

### Updating the scoring schema
1. Edit `knowyourbar_scoring_schema_v4.xlsx` — add rows to `Canonical_Ingredients` and `Alias_Map`
2. Upload updated schema + bar database to Claude, say "run score_and_export"
3. Run `diff_bars_upload.py` against the previous bars.js to see the actual before/after grade distribution — do not compare against a hardcoded historical snapshot, grade counts change over time as the database grows and get stale as documentation the moment they're written down
4. Upload bars.js

### Files that change together
| What changed | Files to upload |
|---|---|
| New bars or affiliate links | bars.js |
| Filter logic, presets, similar bars, rank | app.js |
| Visual changes | style.css + affected .html files |
| New brand page added | new .html + sitemap.xml + nav on all pages |
| Scoring schema updated | Re-run pipeline, then bars.js |

Note: bar count is never a reason to touch HTML files (see the "1,000+" rule) — it's not in this table because it doesn't trigger any file changes on its own.

### Deployment stack
| Component | Service |
|---|---|
| Hosting | Cloudflare Pages (free tier, auto-deploys from GitHub) |
| Repo | GitHub — jbooth22 |
| Domain | GoDaddy (DNS pointed to Cloudflare) |
| Analytics | GA4 — G-SW4MNP5W7J (in index.html) |
| Fonts | Google Fonts — DM Sans, DM Mono, Barlow Condensed, IBM Plex Mono |
| Charts | Chart.js v4.4.0 via jsDelivr CDN (clean-protein-bars.html only) |

### Cache headers (`_headers` file at repo root — verified against the live file 2026-08-09)
| File(s) | max-age | In practice |
|---|---|---|
| `*.html`, `/` | 1 hour (3600s) | Content pages refresh fast |
| `bars.js` | 1 hour (3600s) | New scores/data go live quickly |
| `style.css` | 1 hour (3600s) | Fixed 2026 from a previous 1-week setting that caused persistent mobile caching complaints — **if any document says style.css caches for a week, that document is wrong, this table is the current truth** |
| `app.js` | 1 day (86400s) | Logic changes need up to 24h or a manual purge to reach all visitors |
| `bar_hero.png`, other images | 30 days (2592000s) | Rarely change |
| `sitemap.xml`, `robots.txt`, `llms.txt` | 1 day (86400s) | |

All entries use `must-revalidate`, so nothing is served stale forever, but `max-age` means the browser won't even check with the server until it expires. If a change genuinely isn't showing within the window above, manually purge (Cloudflare dashboard → Caching → Configuration → Purge Everything) rather than waiting.

### GitHub upload (current manual workflow)
1. Go to github.com — jbooth22 repo
2. Drag updated files into the repo browser
3. Cloudflare detects the commit and deploys (~60 seconds)
4. Check status at cloudflare.com under Pages

Planned: set up local Git so deployment is `git add . && git commit -m "..." && git push`.

### Google Search Console
After uploading new or changed pages:
1. Go to Search Console for knowyourbar.com
2. Paste URL into the inspection bar, click "Request Indexing"
3. Re-submit sitemap.xml if new pages were added (Sitemaps section)

### Known data gaps (verify against current bars.js before citing counts — these are a snapshot, not live)
Bars with missing ingredient data (show in tool with no grade): Power Crunch | Chocolate Strawberry; MET-Rx | Peanut Butter Granola; MET-Rx | Chocolate Chip Granola; MET-Rx | Mint Super Cookie.
Bars without affiliate links: check current count with a script, don't reuse an old number here — this file listed "~263 of 817" as of an earlier bars.js version, which is already a different total than the current database.

---

## Session discipline — how to work with Claude efficiently

**Start every session:**
1. Upload this BRIEFING.md
2. Upload the specific files you want to change (from GitHub)
3. State exactly what you want changed

**During session:**
- Claude works from uploaded files, not memory
- Before writing or editing any brand/guide page copy, run `verify_brand_data.py`
  for the relevant brand(s) and cross-check every grade/score/macro/pattern
  claim against it — see "MANDATORY: run verify_brand_data.py" above
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
