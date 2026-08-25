# KnowYourBar.com — Project Briefing
*Upload this file at the start of every new Claude session.*
*Last updated: 2026-08-23*

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
score_and_export.py     — Scoring pipeline script. As of 2026-08-12 this includes parser-resilience
                           fixes (unbalanced parentheses, "contains less than 2%" handling, depth-aware
                           clause matching, accented-character normalization) — see "Scoring pipeline
                           integrity" below before treating an older copy of this script as current.
                           The script itself takes the schema file as a --schema argument, so it does
                           not need code changes when the schema version bumps (v5 -> v6 etc.) — only
                           the schema file and this briefing need to reference the current version.
knowyourbar_scoring_schema_v6.xlsx — Ingredient scoring schema (v6, released 2026-08-13 — see below).
                           Always use this, never an older v5/v4 copy.
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
  low-sugar-high-protein.html    — SLATED FOR DELETION, see "Guide pages" section below, decided 2026-08-19
  keto-protein-bars.html
  best-bars-for-diabetics.html
  caffeine-protein-bars.html   — rebuilt to rev 8 on 2026-08-20, fulfills the "bars with caffeine" future-feature item
  glp1-protein-bars.html

Data / visualization pages:
  all-protein-bar-brands.html  — Full brand summary table (all brands, filterable)
  brand-quadrant.html          — Magic Quadrant scatter plot (macro efficiency vs ingredient quality)

Other:
  ingredient_scoring.html      — How we score page
  flavor-map.html              — Sankey diagram visualization
```

---

## Database update: 1,181 → 1,245 bars, 165 → 185 brands (2026-08-21)

Monthly database update per the cadence policy set 2026-08-21 (updates run monthly, not ad hoc). New `bars.js` (1,245 bars, 185 brands) supplied pre-built against schema v8 — this session did not run `score_and_export.py`, only consumed the already-exported `bars.js`.

**`glp1-protein-bars.html` refreshed 2026-08-21** — recomputed from the new 1,245-bar database using the unchanged formula (Protein ≥15g, Calories ≤200, Sugars ≤4g, Fiber ≥3g, Sugar Alcohol =0, grade A/B). **28 → 41 qualifying bars (2.4% → 3.3%)**. This was a pure data refresh, no formula change.

What changed on the page:
- All header/meta/JSON-LD counts (title, description, OG/Twitter tags, Article/BreadcrumbList/FAQPage JSON-LD, H1, hero subtitle, snapshot stats, findings section, score-grid fail-rate cards)
- **Brand tables:** Consider grew from 1 brand (Junkless) to 5 (Junkless, Main Event, Ration, Fello, form — four new brands entered the database and immediately qualified). Mixed stayed the same 4 brands (NuGo, Wonderslim, Promix, BalanceDiet) with updated ratios/averages. Avoid grew from 165 to 176 brands.
- **Top Picks tiles:** "Best protein per calorie" and "Highest protein" both changed — the new brand **Ration** (25g protein per bar) now beats the old Wonderslim (15g) and Atlas (20g) picks on both counts. Caught this by recomputing each tile's winner fresh against the new 41-bar set rather than assuming the tiles were static; they are not — they need to be re-derived on every data refresh, same as the counts. **Add this check to the guide-refresh routine going forward** — it's easy to update the headline count and miss that a superlative pick (best/highest/most/lowest anything) has silently gone stale.
- **`gd-bar-data` script tag** (the lazy-expand JSON data source consumed by `toggleIngr`/`buildLazyExpand` in the page's inline JS) was also stale at the old 28-bar set with old `#N of 1181` rank text. Regenerated for all 41 bars. This tag isn't visually obvious on the page (it's a hidden `<script type="application/json">` block) — **check for it on every future guide-page data refresh**, since a normal visual QA pass won't catch it.
- Bar-list table body (41 rows, main + expand) rebuilt from scratch using a Python port of `app.js`'s `MACRO_RANKS` percentile-based rank-tag algorithm (`#N lowest/highest` vs `#N of 1245`), validated against the app.js source line-by-line before use.

QA performed: `verify_brand_data.py` spot-checks (Junkless, NuGo) matched generated table values exactly; broken-link scan on all 10 at-risk affiliate brands (0 flagged); all 4 JSON-LD blocks + the `gd-bar-data` JSON validated with `json.loads`; `node --check` on all 5 inline `<script>` blocks; tag-balance check (tr/td/table/div/section all balanced); Playwright screenshots at 1400px and 390px including an expanded bar row and an opened FAQ item.

**Bug caught during this refresh (fixed, not shipped):** my first pass at the Avoid-table generator rendered brands as clickable "jump to flavor" buttons whenever they had ≥1 qualifying flavor, but 3 small-lineup brands (Alio, Atlas, Julian Bakery — 2-4 tracked flavors each, 1-2 qualifying) belong in the Avoid table per the existing site convention, which always uses static (non-clickable) brand-name cells in the Avoid table regardless of qualifying count. Confirmed against the old page's actual markup before fixing.

**Remaining guide pages not yet refreshed against the new 1,245-bar database:** `no-artificial-sweeteners.html`, `clean-protein-bars.html`, `keto-protein-bars.html`, `caffeine-protein-bars.html`. (`best-bars-for-diabetics.html` refreshed 2026-08-21, `no-seed-oils.html` refreshed 2026-08-23, `no-sugar-alcohols.html` refreshed 2026-08-25, see below.) Fresh filter counts against the new database (no page edits made yet, computed for planning only):

| Guide | Old count | New count |
|---|---|---|
| No Sugar Alcohols | 729 | 919 |
| No Artificial Sweeteners | 810 | 1,004 |
| No Seed Oils | 587 | 759 |
| Clean Protein Bars | 351 | 530 |
| Low Sugar + High Protein | 265 | 318 (page slated for deletion, not refresh) |
| Best Bars for Diabetics | 104 | 112 (refreshed 2026-08-21) |
| Keto | 97 | 102 |
| Caffeine | 42 | 42 |

`all-protein-bar-brands.html` also needs a rebuild via `build_brand_rankings.py` against the new `bars.js`. Given the same level of care GLP-1 needed (superlative picks, lazy-load JSON, brand-table edge cases), each remaining guide page should get its own focused session rather than a bulk pass.



`keto-protein-bars.html` had 14 broken "Shop on Brand Site" links across the
page — `href="Yes"` instead of a real URL. Root cause: whatever generated
the page read `Custom Referral Link`'s raw Y/N value into the site-link slot
instead of always using `Website`. Breakdown:
- **10 in the `gd-bar-data` lazy-load JSON block** (`"ws": "Yes"`), at `i`
  indices 33, 34, 42, 43, 44, 52, 57, 58, 60, 63 — all 10 IQ Bar flavors
  (Toasted Coconut Chip, Peanut Butter Chip, Chocolate Sea Salt, Chocolate
  Mint Chip, Almond Butter Chip, Banana Nut, Salted Caramel Chip, Lemon
  Blueberry, Matcha Chai, Wild Blueberry).
- **4 in server-rendered markup**, found only by re-scanning structurally
  rather than trusting the index list handed into the session: one
  `.pick-tile` featured card (IQ Bar Toasted Coconut Chip — the same bar as
  index 33 above, broken a second time in a different section of the page)
  and 3 `.ingr-row` expand panels for B.T.R. Nation (Cinnamon Cashew Crunch,
  Coffee Cashew Crunch, Peanut Butter Crunch — `data-idx` 2, 3, 5).

All 14 broken links belonged to bars where `Custom Referral Link == "Yes"`
(our highest-revenue-driving affiliate relationships), so this was actively
costing revenue, not cosmetic. Every one of the 14 also had a working Amazon
link, so nothing was a total dead end. Fixed via literal string replacement
keyed on each entry's unique Amazon product code to guarantee a 1:1 match;
all 14 verified against `Website` in live `bars.js` before writing. Full
repo-wide scan for `href="Yes"`, `href="None"`, `"ws": "Yes"`, `"ws":
"None"`, `"az": "None"` came back clean everywhere else — no other page
affected as of this date.

**44 bars across 10 brands currently carry `Custom Referral Link == "Yes"`
and are at elevated risk if any future guide/brand page rebuild reuses
whatever produced this bug:** B.T.R. Nation, Gryp, IQ Bar, Jesse's
GOODNITE!, Jesse's WAKEUP!, Lineage Provisions, Off the Farm, Real Food Bar,
Redefine, Takeaways. Any page including flavors from these brands should get
the broken-link-field scan (now in `QA.md` section 1) run against it
specifically, not just a generic pass.

`QA.md` and this file were both updated with the field-level warning and an
automated scan (`href="Yes"` / `href="None"` / `"ws": "Yes"` / `"ws":
"None"` / `"az": "None"`) so this class of bug is caught automatically
before future uploads rather than found by chance.

---

## Scoring pipeline integrity (schema v8, 2026-08-21)

**Bracket-depth parsing bug, found and fixed.** `parse_ingredients()` (and its helper `find_depth0_clause()`) in `score_and_export.py` only tracked `(` `)` for nesting depth. Square brackets — common in compound-ingredient labeling, e.g. `cookie crumble [sugar (cane sugar, tapioca syrup), pea starch, shortening [palm oil, modified palm oil]]`, especially on imported/EU-formatted bars — were invisible to the parser. Everything inside a `[...]` group got comma-split and scored as independent **top-level, full-weight** ingredients instead of **sub-ingredients at 0.6 weight**, inflating position counts and over/under-weighting minor sub-components. Fixed by treating `[`/`]` identically to `(`/`)` everywhere depth is tracked — no separate code path needed.

**Impact, measured against the live 1,245-bar database:** 163 bars contain square brackets. 22 of those shifted score by >=0.5 once brackets were depth-tracked, and **5 changed letter grade band**: Daryl's Bars "Campfire S'Mores" C->B, "Double Chocolate Brownie" B->A, "Chocolate Caramel Pecan" B->A, FITCRUNCH "Apple Pie" F->D, "Peanut Butter Cookie" D->C. Also affected (no grade flip, score shift only): Daryl's Bars (10 more flavors), FITCRUNCH "Strawberry Strudel", Gatorade "Chocolate Caramel", Mosh "Blueberry Almond Crunch", NuGo (3 flavors). **Checked against all 5 completed brand pages (Barebells, Quest, RXBAR, KIND, Clif) — zero bars affected**, so none of those pages need a refresh from this fix.

**23 new canonical ingredients + 7 new aliases added (`manual_v8` in `Canonical_Ingredients`/`Alias_Map`),** closing the schema-gap audit from 32 unique unmatched ingredient terms down to 1 (a stray `"15%"` numeric fragment, harmless/correctly ignored). New canonicals: cassava root fiber, beet fiber, whey hydrolysate, liquid whole egg, pasteurized (standalone descriptor, neutral), panax ginseng extract, rice crisp, raisin juice concentrate, valerian root extract, chamomile, beef liver powder, sodium aluminum sulfate, organic (standalone descriptor, neutral), glucose, hops extract, coriander, chili pepper, spearmint, dried licorice root, lucuma, dragon fruit powder, cognizin, einkorn flour. New aliases (mapping variant/case spellings to existing canonicals): whey concentrate -> whey protein concentrate, Cassava Fiber -> cassava root fiber, Beet Fibre -> beet fiber, Yogurt Flavored Coating -> yogurt coating, Bacterial Culture -> bacterial cultures, "and Salt" -> salt, condensed milk -> sweetened condensed milk. All scored by analogy to existing schema conventions (e.g. whole herbs/spices at neutral 0, functional botanical extracts at +1 matching chaga/lions mane precedent, plain flours at neutral 0 regardless of grain heritage).

**Net effect on the full database (same 1,245-bar upload, before -> after bracket fix + new canonicals):** A=236/B=450/C=347/D=169/F=43 -> A=240/B=449/C=345/D=169/F=42.

**Known pre-existing minor edge case, NOT part of this fix, flagged for a future pass:** the fallback substring matcher still has at least one bad mapping — `"Ethyl Alcohol"` (an actual named ingredient) falls through to the `"alcohol"` -> `glycerin` alias that v6's fix only patched for the `"non-alcoholic"` qualifier-phrase case. Confirmed low impact (1 bar, JiMMYBAR! Double Fudge Brownie, sub-weight 0.6) — not fixed here since it predates this update and is out of scope for the brackets/canonicals fix, but worth a v9-style fallback-substring sweep next time the pipeline is touched, per the process note in the v6 section below.

**Database size:** 1,245 bars as of this schema (up from 1,181 at v7) — 64 new bars, 20 new brands, plus 164 previously-blank Amazon Affiliate links filled via a corrected spreadsheet formula (dragged-formula gap on the last ~250 rows, caught and fixed same day).

**Pages affected — cascade NOT yet run (holding per the 2026-08-21 monthly-cadence policy):** all 7 completed guide pages (No Sugar Alcohols, No Artificial Sweeteners, No Seed Oils, Clean Protein Bars, Diabetics, Keto, GLP-1) now have stale qualifying counts/tables from both the 64 new bars AND this scoring fix — GLP-1 is worst-hit (28 -> 41 qualifying, +46%). `all-protein-bar-brands.html` needs a rebuild (20 new brands). None of the 5 completed brand pages need a refresh (verified above). Always use `knowyourbar_scoring_schema_v8.xlsx` + the current `score_and_export.py` going forward, not an older copy of either file.

---

## Scoring pipeline integrity (schema v7, 2026-08-14)

`score_and_export.py` gained a new scoring rule: **diminishing returns on stacked protein sources.** Each additional *separately top-level-listed* protein ingredient beyond the single best-scoring one now counts at `PROTEIN_STACK_DISCOUNT = 0.5` (half weight) instead of full weight. This does NOT apply to protein sources decomposed from the same parenthetical blend label (e.g. "Protein Blend (Milk Protein Isolate, Whey Protein Isolate)") — those are one FDA-labeled blend, not competing claims, and are already down-weighted via the existing 0.6 sub-ingredient multiplier. It only targets distinct top-level protein ingredients (e.g. Whey Protein Isolate ... Collagen ... Milk Protein Concentrate listed as separate top-level items), so a second or third protein source no longer adds nearly as much credit as the first just by being listed. The single best-scoring protein match always keeps full weight.

**10 new canonical ingredients added (`v7_manual` in `Canonical_Ingredients`):** camu camu (whole_food, +2), mesquite powder (whole_food, +1), dandelion root powder (whole_food, +1), s.officinarum prebiotic fibre — UK spelling variant (fiber_or_functional_carb, +1), potassium chloride (seasoning, neutral), chili (seasoning, neutral), plus 4 neutral `ingredient_group` coating entries (cocoa/strawberry/lemon/vanilla flavored coating).

**Database size:** 1,181 bars as of this schema (up from 1,157 at v6).

**Pages affected:** spot-check any brand page with a multi-protein-source bar (e.g. a bar listing whey protein isolate AND collagen AND milk protein concentrate as separate top-level ingredients) before trusting its current copy — the stacking discount can shift its score even if nothing else changed. Barebells and Quest were checked against live `bars.js` on 2026-08-18 and their existing copy (last refreshed 2026-08-12, pre-dating this rule) still matches current grades exactly, so no v7-driven refresh was needed for either. Always use `knowyourbar_scoring_schema_v7.xlsx` + the current `score_and_export.py` going forward, not an older copy of either file.

---

## Scoring pipeline integrity (schema v6, 2026-08-13)

A routine database update (33 new bars, 3 new brands: Floura, Glove Crafted, and a renamed/corrected Met-RX) surfaced a second bug class beyond simple schema gaps: **the fallback substring matcher can silently mismatch an unmapped ingredient to an unrelated canonical entry that happens to share a substring.** `lookup_ingredient()` in `score_and_export.py` only reaches this fallback path when there's no exact alias/canonical match, so the fix in every case was adding the missing exact-match canonical/alias — no code change needed.

**Confirmed real mismatches found and fixed in v6:**
- **Honeydew** was matching "honey" and scoring **-2** instead of a fruit's **+2** (affected all 7 new Floura bars).
- **Buckwheat** / **Buckwheat Flour** were matching "wheat" and scoring **0** instead of **+2**/**+1** (affected 15 bars including KIND).
- **Isomaltooligosaccharide** (a prebiotic fiber) was matching "isomalt" (a sugar alcohol) and scoring **-3** instead of **+1** (4 bars).
- **"Non-Alcoholic"** (a qualifier phrase inside a parenthetical, e.g. "chocolate liquor (non-alcoholic)") was matching "alcohol" → glycerin and getting a false **-1** (8 G2G bars).
- **Fermented Watermelon Rind** was matching "water" (harmless, score 0 either way, fixed for correctness anyway).

**12 genuinely new ingredients scored:** amaranth, raisin paste, Floura SuperFiber Flour Mix, cantaloupe, white chia flour, potassium carbonate, rose extract, rooibos tea leaf, mango concentrate, honeydew, fermented watermelon rind, monoglyceride (singular form; plural already existed).

**Process note for future database updates:** don't just run the schema-gap audit (`audit_schema_gaps()` — catches only *zero*-match ingredients). Also scan for substring-fallback matches across the full database and eyeball the list for category-level mismatches (a real bug) vs. reasonable approximations (expected, e.g. "Diced Almonds" → "almonds" is fine). The full audit script used for this pass is not yet a checked-in file — ask Claude to re-run the fallback-path scan (compares `al`/`cl` exact-match hits vs. the substring-fallback hits) on any future upload before trusting the schema-gap audit alone.

**Net effect on the full database (v5 -> v6, same 1,157-bar upload):** grade distribution moved from A=215/B=413/C=342/D=155/F=32 to A=221/B=418/C=331/D=155/F=32 after the fixes above. Zero bars saw a 2+ letter grade swing between the pre-fix and post-fix run — spot-checked programmatically, not just eyeballed.

---

## Scoring pipeline integrity (schema v5, 2026-08-12)

A routine database update surfaced several real bugs in the scoring pipeline, not just missing schema coverage. All are fixed in `knowyourbar_scoring_schema_v5.xlsx` + the current `score_and_export.py` — **always use these, never an older v4 copy of either file.**

**What was wrong:**
1. **Alias/canonical desync** — 307 rows in `Alias_Map` carried `base_score=0` instead of inheriting their canonical's real score (Beef, Pork, Butter, Quinoa, etc. all scored as neutral instead of their true value). Fixed via full alias-to-canonical sync; also fixed 453 rows with drifted category/subcategory (chip-display only, no score impact).
2. **93 previously-unmatched ingredients** added to the schema.
3. **Accented characters** (jalapeño, etc.) were being deleted instead of transliterated by `normalize()`, breaking words into unmatched tokens.
4. **Malformed source data crashed parsing silently** — a single stray or unbalanced parenthesis anywhere in an `Ingredients` string would corrupt bracket-depth tracking and drop everything after it (15 bars affected). Parser now clamps depth at 0 and recovers unclosed trailing groups instead of failing silently.
5. **Biggest one: "Contains less than 2% of the following: X, Y, Z"** is standard FDA labeling for real minor ingredients, but the parser treated it like an allergen/cross-contact disclaimer and silently truncated everything after it — deleting things like Sucralose from nearly every affected flavor (89 bars hit). Fixed by stripping only the boilerplate lead-in phrase and continuing to parse the real ingredients after it. The same fix made all remaining truncation clauses (`may contain`, `contains:`, `manufactured in`, etc.) depth-aware, so a clause nested inside a sub-ingredient's own parenthetical no longer wrongly truncates the rest of the list (9 bars affected).

**Net effect on the full database:** grade distribution moved from A=160/B=382/C=339/D=172/F=31 to A=214/B=405/C=323/D=155/F=32.

**Pages with stale copy as a result — data accuracy, separate from the structural/voice work below:**
- `barebells-review.html` — nearly every flavor's grade/score shifted. **Refresh is DONE** (verified against live `bars.js` on 2026-08-18, page dateModified 2026-08-12 — copy matches current scores exactly, including the 4 vegan flavors grading D/F and Marshmallow Peanut Road leading at B).
- `quest-bars.html` — all 13 tracked flavors shifted; this wasn't caught until fix #5 above landed. Sucralose was specifically being dropped from Chocolate Chip Cookie Dough. **Refresh is DONE** (verified against live `bars.js` on 2026-08-18, page dateModified 2026-08-12 — copy matches current scores exactly).
- `rxbar-review.html` — one flavor ticked up slightly, stayed A grade. No refresh needed.

**Known low-priority cleanup:** 15 bars in the source database (`Ingredients` column) have genuine typos — stray or missing parentheses — that the parser now works around but that should ideally be fixed at the source for data cleanliness. Not urgent.

**v6 update (2026-08-13):** Quest, RXBAR, and Barebells had zero data changes in the v6 database upload — their page copy from the v5 refresh (where applicable) is still accurate, no new refresh needed on their account. The pages that DO need a `verify_brand_data.py` pass + copy refresh from this upload: `kind-bars-review.html` (see KIND sub-brand merge note below — this is now urgent, not just a structural rebuild candidate) and any future Clif/Met-RX/1st Phorm/etc. pages if built. Full brand-level diff is in the 2026-08-13 diff report; ask Claude to re-run `diff_bars_upload.py` against the current live `bars.js` if that report isn't handy.

**KIND sub-brand merge (2026-08-13):** the "KIND Protein Max" sub-brand no longer exists as a separate `Brand Name` in the database — its 4 flavors (Crispy Chocolate Peanut Butter, Sweet and Salty Caramel Peanut Crisp, Dark Chocolate Crisp, Raspberry Cocoa Crisp) now appear under plain "KIND". 11 new KIND flavors were also added (Almond Butter, Apple Cinnamon, Blueberry Almond, Blueberry Vanilla Cashew, Caramel Peanut, Crunchy Peanut Butter, Dark Chocolate Cocoa, Dark Chocolate Nut, Honey Oat, Maple Glazed Pecan and Sea Salt, Peanut Butter, Peanut Butter Banana Dark Chocolate) — this appears to be the "KIND Minis and Thins not yet in database" item from the Content known-issues list finally landing. **This resolves the KIND sub-brand scoping question** noted below as a rebuild blocker — treat all KIND flavors as one brand going forward, no more "KIND" vs. "KIND Protein Max" split.

**Met-RX brand rename (2026-08-13):** the old "MET-Rx" brand name/casing and its 3 previously-unscored placeholder bars (Peanut Butter Granola, Chocolate Chip Granola, Mint Super Cookie — all had `ingredient_score: null`) are gone, replaced by "Met-RX" (capitalization fixed) with 6 bars, all now scored with real ingredient data. No page exists for this brand yet.

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

**Rev 8 rebuild status (as of 2026-08-19):** `no-seed-oils.html` and `no-sugar-alcohols.html` were rebuilt to TEMPLATE_GUIDE.html rev 8 on 2026-08-14/15. `no-artificial-sweeteners.html` was rebuilt to the same rev 8 standard on 2026-08-17 — 940 of 1181 bars qualify (79.6%), screened for sucralose, acesulfame potassium, aspartame, and saccharin (sucralose accounts for nearly all disqualifications; zero bars currently contain aspartame or saccharin). `clean-protein-bars.html` was rebuilt to rev 8 on 2026-08-18 — 485 of 1181 bars qualify (41.1%), screened for A/B ingredient grade + no artificial sweeteners + no processed oils (up from the stale 340/983 that had been live since April). `best-bars-for-diabetics.html` was rebuilt to rev 8 on 2026-08-18 — 104 of 1181 bars qualify (8.8%), screened for sugar, net carbs, fiber, protein, grade, and the maltitol family (see GUIDE_CRITERIA.md's "Maltitol family exclusion" section for the research and exact term list). This rebuild also added a new "Is your brand good for diabetics?" section: a per-brand table (all 165 tracked brands, not just qualifying bars) rating each Likely / Mixed / Less Likely based on what share of its flavors clear the full screen, with reasoning text and avg sugar/net carbs/fiber/sugar-alcohol columns, plus the required "we are not doctors or dietitians" disclaimer. `keto-protein-bars.html` was rebuilt to rev 8 on 2026-08-19 — 97 of 1181 bars qualify (8.2%), screened for net carbs, protein, fat, and the maltitol family (net carbs ≤8g, protein ≥10g, fat ≥8g, no maltitol/maltitol syrup/polyglycitol/hydrogenated starch hydrolysates). This reused the Diabetics maltitol exclusion logic rather than a separate check, per GUIDE_CRITERIA.md. Jeff confirmed the exclusion (narrower and more defensible) on 2026-08-19; that decision and the updated formula are recorded in GUIDE_CRITERIA.md's Keto row. Applying the exclusion is what moves the count from 127 (macro thresholds alone) to 97 — worth knowing if the number looks low compared to a mental model built on the old, non-maltitol-screened Keto page. This rebuild also followed Diabetics' per-brand table pattern (Likely/Mixed/Less Likely across all 165 brands, not the Best/Avoid pattern used on `no-sugar-alcohols.html`) since only 8.2% of the database qualifies — the Best/Avoid pattern only reads well when a majority of bars pass. `glp1-protein-bars.html` was rebuilt to rev 8 on 2026-08-19/20 (full rebuild from the old `picks-grid`/`verdict-card` structure, not a table swap) — 28 of 1181 bars qualify (2.4%), screened for protein (≥15g), calories (≤200), sugar (≤4g), fiber (≥3g), zero sugar alcohols, and an A/B ingredient grade, using the canonical `app.js` formula. This is the narrowest guide on the site by qualification rate and brand spread (8 brands with any qualifying flavor). Unlike Keto and Diabetics, GLP-1 excludes ALL sugar alcohols outright rather than just the maltitol family — GI tolerance is the stated priority here, not glycemic index, so the exclusion is broader by design; see GUIDE_CRITERIA.md's GLP-1 row. This rebuild used the new Consider/Avoid/Mixed brand-table pattern from the start (see the unification note below), not the old flat Likely/Mixed/Less Likely table the page previously had. Seven of nine guide pages now share the rev 8 section order, filter/sort bar table, and full server-rendered rows (all 28 GLP-1 bars render server-side with no lazy-load needed, since the qualifying set is well under the ~60-row threshold).

**Brand-listing table architecture unified across low-qualification guides (decided and partially executed 2026-08-19/20):** Keto, Diabetics, and GLP-1 originally used a different brand-table pattern than the high-qualification guides (No Sugar Alcohols, No Artificial Sweeteners, Clean Protein Bars) — a single flat table rating all 165 brands Likely/Mixed/Less Likely, instead of the Consider/Avoid/Mixed three-table split — because their qualification rates are too low (Keto 8.2%, Diabetics 8.8%, GLP-1 ~3%) for a Best/Avoid split to read well by default. After checking actual per-brand distributions against live `bars.js`, the three-table model turned out to work fine at these rates (it just means a large Avoid table and a small Consider table), so Jeff decided to unify all guides on the same Consider/Avoid/Mixed naming and column pattern (Brand, Flavors That Qualify as a ratio, Ingredient Quality grade range, two metric columns relevant to that guide, Note) rather than keep a second table style. **Relaxed Consider threshold (locked 2026-08-19):** a brand qualifies for "Brands to Consider" if `qualifying/total >= 75%` AND `total - qualifying <= 2` (i.e. 100% is no longer required, but only small, low-count misses are folded in) — this exists because at low overall qualification rates, small-lineup brands with 1-2 non-qualifying flavors were falling into neither Consider (not literally 100%) nor Mixed (needs 3+ disqualified) under the original thresholds. Avoid keeps its original threshold (80%+ disqualified AND fewer than 3 qualifying); Mixed keeps its original threshold (3+ qualifying AND 3+ disqualified). `keto-protein-bars.html` was rebuilt on this new pattern 2026-08-19/20 (Consider: 5 brands, Mixed: 10, Avoid: 150) and is live. `glp1-protein-bars.html` was also rebuilt on this pattern 2026-08-19/20 (Consider: 1 brand — Junkless, 4/5 flavors; Mixed: 4 — NuGo, BalanceDiet, Promix, Wonderslim; Avoid: 160) and is live; at GLP-1's very low 2.4% qualification rate this produced the smallest Consider table of any guide so far (a single brand), which is expected given the brand spread rather than a sign anything's wrong. `best-bars-for-diabetics.html` still needs this same rebuild — it currently still has its original flat Likely/Mixed/Less-Likely table.

**New shared components added with the Keto rebuild, reusable on Diabetics/GLP-1:** `.guide-jump-row` / `.guide-jump-link` (a pill-shaped CTA linking to `#full-bar-list` placed just below Top Picks, so long brand tables don't force a huge scroll to reach the ranked bar list — generalized from the page-local `.diab-jump-link` that Diabetics already had, which should be swapped to the new shared class next time that page is touched) and `.brand-table-show-more` / `.brand-row-hidden` (a simple show/hide toggle for the Avoid table: rows past the first 15 are rendered with `display:none` and revealed on click — deliberately not the `gd-show-more`/`PAGE_SIZE` lazy-load mechanism used for the main ranked bar list, since that machinery is built around search/sort/grade-filter state a static brand table doesn't have). Both are in `style.css`.

**Mobile brand-table bug found and fixed sitewide (2026-08-19/20):** `table.brand-table` on every guide using the brand-table pattern was unreadable below 701px — cells word-wrapped one word per line instead of the table scrolling horizontally inside its existing `.table-scroll` wrapper. Root cause: the `min-width: 701px` media query that sets fixed column percentages has no mobile counterpart, so below 701px the table fell back to respecting `width: 100%` and squeezed every column instead of overflowing. This affected all already-live guides using `.brand-table` (No Sugar Alcohols, No Artificial Sweeteners, Clean Protein Bars, Diabetics) as well as the new Keto tables — confirmed via mobile screenshot before fixing, not a regression from the Keto rebuild. Fixed with a new `@media (max-width: 700px)` block appended to `style.css`: table sizes to content (`width: max-content; min-width: 100%`) with short columns kept on one line and only the last column (the free-text Note/Why column) wrapping, within a fixed width band. Verified via Playwright at 390px on Keto, No Sugar Alcohols, and Diabetics — table now correctly overflows and scrolls inside `.table-scroll` with no page-level horizontal overflow.

**`low-sugar-high-protein.html` is being deleted, not rebuilt (decided 2026-08-19):** Jeff's call — it overlaps too much with Keto (net carbs, protein, fat) and Diabetics (sugar, net carbs, fiber, protein) to offer standalone value now that both of those exist as dedicated rev 8 guides. Do not rebuild it. **This is a decision, not yet executed** — the file, its nav dropdown links, footer links, sitemap entry, and any `explore-more-card`/cross-links pointing to it (e.g. from `keto-protein-bars.html` and `best-bars-for-diabetics.html`) are all still live as of this note and need a dedicated cleanup pass across every page that references it. Per this briefing's locked rule, do not create or modify `_redirects` for the dropped URL without asking Jeff first — flag it and confirm whether a redirect (e.g. to `keto-protein-bars.html` or `best-bars-for-diabetics.html`) is wanted before touching Cloudflare routing config.

**`caffeine-protein-bars.html` rebuilt to rev 8 on 2026-08-20** (full rebuild from the old `picks-grid`/`verdict-card` structure, not a table swap) — 42 of 1,181 bars qualify (3.6%), screened for any declared `Caffeine (mg)` > 0 with no minimum dose and no ingredient-quality gate (a bar can be F-grade and still appear — this is a pure caffeine-content screen, not a quality filter, matching the old page's own framing that caffeine content and ingredient quality are separate questions). Unlike every other guide, this one had no existing row in `GUIDE_CRITERIA.md` or preset in `app.js` before this rebuild — the filter logic was reverse-engineered from the live pre-rebuild page (four caffeine zones: Light <50mg, Moderate 50-89mg, High 90-149mg, Very High 150mg+) and confirmed with Jeff before locking in; now documented in GUIDE_CRITERIA.md's new Caffeine row. Brand table (Consider: 9, Mixed: 1 — Einstein, Avoid: 5 — JiMMYBAR!, Jesse's WAKEUP!, CLIF Bar, Aloha, Clif Builders) uses a **guide-specific reframe** of the Consider/Mixed/Avoid pattern: because the page's own qualifying filter is just "has caffeine" (not a quality screen), the ratio column means something different here than on Keto/Diabetics/GLP-1 — it's the share of each brand's *caffeinated* flavors (not its full catalog) that clear an A/B ingredient-quality grade. Applying the standard full-165-brand-catalog version (like GLP-1's Avoid table) would have been meaningless for this guide, since ~150 brands have zero caffeinated flavors and "0/N" isn't a caffeine-relevant signal. Avoid table has no show-more toggle since it's only 5 rows (nothing to hide). Macro-rank grid uses Protein/Calories/Caffeine/Fat, with only Caffeine colored directional-green (`#N highest of 42`, ranked within the 42-bar caffeinated set, not the full 1,181-bar DB) — Protein/Calories/Fat are neutral gray, following the established convention that only metrics tied to a guide's own screening criteria get directional color. All nine guide pages now share the rev 8 section order, filter/sort bar table, and full server-rendered rows.

**`best-bars-for-diabetics.html` refreshed 2026-08-21** against the new 1,245-bar database (schema v8, no formula change) — 104 -> 112 qualifying (8.8% -> 9.0%). Same six-criteria formula: sugar <=5g, net carbs <=10g, fiber >=5g, protein >=10g, A/B grade, no maltitol family. What changed on the page: all header/meta/JSON-LD counts, hero/snapshot stats, Top Picks tiles (recomputed fresh against the new 112-bar set: Healthy Eating on the Go Chia Seed remains Best overall, Gryp/Daryl's Bars/Julian Bakery/IQ Bar keep their superlative slots), the "What we screened" fail-rate score-grid cards, the findings section (A-grade count 22->28, brands-with-qualifying 28->31), the full 112-row bar-list table (eager-rendered first 25 rows, lazy `gd-bar-data` JSON for the remaining 87, `#N of 1245` macro-rank tags throughout), and the FAQ (IQ Bar and Quest brand callouts, maltitol-trap %, qualifying-count answer).

**Brand-table architecture migrated to the locked Consider/Mixed/Avoid pattern in this refresh** (Diabetics had been the one remaining guide still on the old flat Likely/Mixed/Less-Likely table per the unification note below) — Consider: 11 brands (was a flat table before), Mixed: 15, Avoid: 159, using the same relaxed threshold as Keto/GLP-1 (Consider >=75% qualifying AND <=2 disqualified; Avoid >=80% disqualified AND <3 qualifying; else Mixed). Avoid-table brand names are static/non-clickable per the sitewide convention. Five Avoid-table brands (NuGo, Healthy Eating on the Go, Love Good, No Cow, Chief) have exactly 1 qualifying flavor each despite landing in Avoid at the brand level — this is expected given the threshold definition, not a bug (Healthy Eating on the Go's single qualifying flavor, Chia Seed, is in fact this page's "Best overall" Top Pick). The Avoid-row reason text was written to say "Only N of M ... flavors clears" rather than "None of M ... clear" for these five, since a literal "none" claim would have been false.

QA performed: recomputed qualifying count cross-checked against Jeff's expected 112 before writing any copy; `verify_brand_data.py` spot-checks on IQ Bar (10/10 flavors, all B) and Quest (6/16, all B where qualifying) matched; broken-link-field scan across all 1,245 bars found 14 pre-existing issues (KIND, 1st Phorm, BalanceDiet -- none overlap the Diabetics qualifying set or the 10 at-risk affiliate brands, so not fixed here, flagged for its own session); zero qualifying bars are dead-ends (missing both Amazon and Website links); all 4 JSON-LD blocks plus the `gd-bar-data` JSON validated with `json.loads`; tag balance checked (tr/td/table/div/section/button all matched after fixing one score-grid splice bug); `node --check` on all inline `<script>` blocks; FAQ visible text diffed programmatically against FAQPage JSON-LD (0 mismatches); Playwright screenshots at 1400px and 390px including an expanded bar row and the brand table, mobile table-scroll confirmed still working.

## Scoring pipeline bug found and fixed: `OIL_KEYWORDS` incomplete (2026-08-23)

While refreshing `no-seed-oils.html` against the new 1,245-bar database, Jeff caught that Barebells had swung from mostly-disqualified (23/25, matching the site's own pre-existing "Brands to Avoid" copy) to mostly-qualifying (19/25) under the newly-exported `bars.js`. Investigation traced this to `score_and_export.py`'s `OIL_KEYWORDS` list (line ~59), which only checked for 5 of the 13 oils the guide's own published definition claims to screen (palm, palm kernel, palm fruit, canola, soybean, plus a generic `hydrogenated` catch) — sunflower, safflower, vegetable, rapeseed, cottonseed, corn, grapeseed, and rice bran oil were never checked directly, so bars containing plain "sunflower oil" or "vegetable oil" (no "high-oleic" qualifier) were silently passing the "Processed Oils" tag. This is a pre-existing pipeline regression, not something introduced by the 1,181->1,245 database update — it affects every page reading the `Processed Oils` insight, most notably `no-seed-oils.html` and `clean-protein-bars.html` (both filter on it).

**Fix:** added the 8 missing oil names to `OIL_KEYWORDS`, matching the guide's own already-published FAQ definition. Re-ran `score_and_export.py` against Jeff's uploaded raw database (`KYB - New Protein Bar Database (2026).xlsx`) and diffed the output: **exactly 110 bars gained the `Processed Oils` tag, zero `ingredient_score` or `score_band` values changed anywhere in the database.** This confirms the fix is surgical — the numeric scoring engine already penalized these oils correctly via the canonical Alias_Map `fat_oil` category; only the qualitative insight-chip logic was blind to them. Strong independent corroboration: the *original* (pre-1245) `no-seed-oils.html` had brand-table numbers hardcoded from whenever it was last written, and those numbers (Barebells 23/25 disqualified, KIND 6/31, NuGo 15/30, think! 3/22, Bobo's 15/21, Daryl's Bars 3/19, 1st Phorm 4/19, Aloha 7/18, GoMacro 13/17) match the corrected recomputation **exactly**, brand for brand — the fix restores behavior that regressed at some point after that page was last written, it doesn't introduce a new interpretation.

**Corrected `bars.js` and the `score_and_export.py` fix are both in this session's outputs.** Upload `bars.js` to GitHub to make this live.

**`no-seed-oils.html` refreshed 2026-08-23** against the corrected 1,245-bar database — **649 of 1,245 bars qualify (52.1%)**, down from the broken pipeline's 759 (61.0%). Same filter, unchanged: `score_insights` does NOT contain `Processed Oils`. What changed on the page: all header/meta/JSON-LD counts and dates, hero/snapshot stats (649 qualify / 596 disqualified / 201 A-grade / 131 brands / 12.0g avg protein), the 10 oil-breakdown score-cards (counts, percentages, and "Found in" brand lists all recomputed, including a bracket-list-aware attribution fix so "Vegetable Oils (palm, palm kernel, canola)"-style labels attribute to the correct specific oil rather than a generic bucket), the Consider/Avoid/Mixed brand tables (Barebells now correctly back in Avoid at 2/25 qualifying), Top Picks (all 6 tiles re-verified against the corrected qualifying set — same picks held up: Healthy Eating on the Go Chia Seed, Gryp Rocky Road and Sea Salt, Musashi Chocolate and Rocky Road, Larabar Cashew Cookie, Julian Bakery Peanut Butter, Musashi White Chocolate and Caramel), the findings section, the full 649-row bar table (60 eager rows, `gd-bar-data` JSON for the remaining 589, `#N of 1245` macro-rank tags throughout), and the FAQ (Larabar dropped from "all qualify" to 26/29, NuGo now 15/30, the "brands that mostly disqualify" example swapped from Barebells to Wonderslim/Pure Protein/FITCRUNCH since Barebells' 2026-08-14-era copy was already accurate).

QA performed: recomputed qualifying count from scratch against the corrected `bars.js` before writing any copy; the OIL_KEYWORDS fix itself cross-checked via a 0-diff on `ingredient_score`/`score_band` across all 1,245 bars; `verify_brand_data.py` spot-checks on RXBAR (12/12, all A/B) and Barebells (0 A-grade, F->B range) matched; at-risk affiliate link scan across all 10 flagged brands (B.T.R. Nation, Gryp, IQ Bar, Jesse's GOODNITE!, Jesse's WAKEUP!, Lineage Provisions, Off the Farm, Real Food Bar, Redefine, Takeaways) found zero issues; all 5 JSON-LD blocks plus the `gd-bar-data` JSON validated with `json.loads`; tag balance checked (caught and fixed one duplicate `</section>` from a splice); `node --check` on all 3 inline `<script>` blocks; FAQ visible text diffed programmatically against FAQPage JSON-LD (0 mismatches); Playwright screenshots at 1400px and 390px including an expanded bar row, the brand tables, and an opened FAQ item — caught and fixed one rendering bug this way (a shell-escaping artifact had turned several apostrophes in the findings-section copy into triple-apostrophes, e.g. "isn'''t"; fixed via global regex, re-validated, re-screenshotted clean) and one stale-copy bug (the Bar Finder CTA still said "not just the 600 on this page").

**Not yet done: `clean-protein-bars.html` also filters on the `Processed Oils` tag and is currently live with the old, inflated count (530 qualifying under the broken pipeline; recomputes to 491 under the fix, a swing of 39 bars). Needs the same refresh treatment in its own session, per the one-guide-per-session pattern.** `all-protein-bar-brands.html` also needs regenerating (`build_brand_rankings.py`) since `bars.js` changed.

**`no-sugar-alcohols.html` refreshed 2026-08-25** against the 1,245-bar database — **919 of 1,245 bars qualify (73.8%)**, up from 859 of 1,181 (72.7%) on the stale version. Filter unchanged: `score_insights` does NOT contain `Sugar Alcohols`. Confirmed this filter is independent of the OIL_KEYWORDS bug (separate keyword list, no overlap with oil detection), so the shift is explained entirely by database growth — 326 disqualified vs. the old 322, proportionate to 1,181→1,245 growth, no anomaly. What changed on the page: all header/meta/JSON-LD/breadcrumb counts, hero/snapshot stats (919 qualify / 326 disqualified / 225 A-grade / 156 brands / 11.6g avg protein), the 6 sugar-alcohol breakdown score-cards (Maltitol 202/16%, Erythritol 91, IMO 52, Sorbitol 39, Xylitol 8, Isomalt 8, all with recomputed "Found in" brand lists), the glycerin section (61 brands with glycerin in every qualifying flavor, up from 43; 339 of 919 qualifying bars contain glycerin), the Consider/Avoid/Mixed brand tables (142/29/14 brands — Barebells still 25/25 disqualified, KIND still 31 flavors B–D, unchanged from before since neither depends on the oil bug), Top Picks (recomputed fresh against the 919-bar set: best overall unchanged — Healthy Eating on the Go Chia Seed — but "Best for keto" changed from Epic Venison Sea Salt Pepper to KIND Dark Chocolate Almond Mint, both true 0g-net-carb ties, KIND's higher fat content is the more keto-typical profile so it won the tiebreak), the findings section (maltitol-in-first-5-ingredients example count updated to 4 of 202 bars in a "contains 2% or less" clause, 0g-label-but-ingredient-present mismatch updated to 113 of 326 bars, both re-verified against the live ingredient text rather than trusted from the old copy), the full 919-row bar table (60 eager rows + `gd-bar-data` JSON for the remaining 859, `#N of 1245` macro-rank tags throughout, `rank-amber` used correctly for unfavorable-extreme macros per the actual `app.js` algorithm — confirmed by reading the source directly rather than trusting a paraphrase), and all 13 FAQ answers (both the visible HTML and the FAQPage JSON-LD copies, kept in sync and diff-checked against each other post-edit).

QA performed: `verify_brand_data.py` spot-checks (Barebells: 25/25 disqualified, F→B grade range; KIND: 31 flavors, B→D grade range) matched generated table values exactly; affiliate-link scan on all 40 qualifying bars from the 10 at-risk brands (B.T.R. Nation, Gryp, IQ Bar, Jesse's GOODNITE!, Jesse's WAKEUP!, Lineage Provisions, Off the Farm, Real Food Bar, Redefine, Takeaways) confirmed every link resolves from the `Website` field, zero `Custom Referral Link` Y/N leaks; all 5 JSON-LD blocks plus the `gd-bar-data` JSON validated with `json.loads`; tag-balance check (div/section/table/tbody/tr/td/script all matched); `node --check` on all 4 non-JSON inline `<script>` blocks; FAQ visible text diffed programmatically against the FAQPage JSON-LD (0 real mismatches; two false positives from the diff script's own entity-encoding were investigated and ruled out); Playwright screenshots at 1400px and 390px including an expanded bar row (macro ranks and score tile render correctly against the new 1,245-bar denominators) and the brand table (caught and fixed one copy bug this way — the auto-generated "N flavor(s) contain a sugar alcohol" note had bad singular/plural grammar for near-100%-clean Consider-table brands; fixed via regex and re-verified tag balance).


**`Key: null` data-quality flag — fixed 2026-08-20.** The 191 bars in `bars.js` with `Key: null` (found during the caffeine rebuild, including 15 of the 42 caffeinated bars) are resolved. `score_and_export.py` now backfills any missing/blank `Key` at load time as `f"{Brand Name} | {Flavor Name}"` — the same fallback pattern `diff_bars_upload.py`'s `key()` function already used — so every future export gets stable keys automatically; existing non-null `Key` values are never overwritten. Re-ran the export and confirmed via `diff_bars_upload.py` plus a supplementary full field-by-field diff that the *only* changes across all 1,181 bars were the 191 `Key` values going from `null` to their `Brand Name | Flavor Name` fallback — zero changes to `ingredient_score`, `score_band`, macros, `Ingredients`, or `score_insights`. `bars.js` now has zero `Key: null` entries. (Note: this session's re-export was run against a `BarDB` reconstructed from the current `bars.js` itself, since the raw source spreadsheet wasn't uploaded — safe here because `score_and_export.py` recomputes every score field fresh from the `Ingredients` text regardless of the input db's pre-existing values, so the reconstruction round-trips cleanly. Next time the real source spreadsheet is uploaded, re-run against it directly rather than reusing this reconstruction approach.)

**Mobile nav toggle fixed (2026-08-18):** all four rev 8 pages had the `#nav-toggle` hamburger button in the nav markup but no click handler wired up, so the mobile menu didn't open. Fixed by adding a small inline script right after `</nav>` on each page (`navToggle.addEventListener('click', () => navLinks.classList.toggle('open'))`) — the `.site-nav-links.open` CSS was already in `style.css` and needed no changes. Verified working on all four via Playwright at 390px. Any future rev 8 guide rebuild should include this handler from the start rather than needing this same fix again.

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
- Keto guide (rev 8, 2026-08-19) uses FAT + NET CARB columns instead of CAL + SGR in the bar table — a deliberate deviation from the rev 8 default column set (BAR/CAL/PROT/P100/FAT/CARB/FIBR/SGR/SGR ALC/CERTS/GRADE), since fat and net carbs are the two metrics keto followers actually filter on. If TEMPLATE_GUIDE.html's default column set changes, patch this page manually rather than re-running a generic rebuild against it.
- Diabetics guide uses 6-filter criteria: sugar, net carbs, fiber, protein, ingredient grade, no maltitol family (maltitol, maltitol syrup, polyglycitol, hydrogenated starch hydrolysates — see GUIDE_CRITERIA.md for why these are a hard exclude instead of a math adjustment). Also has a per-brand "is this brand good for diabetics" table below the main bar list — see GUIDE_CRITERIA.md and the "Rev 8 rebuild status" note above.
- GLP-1 guide uses the rev 8 default column set (BAR/CAL/PROT/P100/FAT/CARB/FIBR/SGR/SGR ALC/CERTS/GRADE), no deviation needed since protein/calories/sugar/fiber are all already in the default set. Filter is protein ≥15g, calories ≤200, sugar ≤4g, fiber ≥3g, zero sugar alcohols (all of them, not just the maltitol family — a deliberate stricter rule than Keto/Diabetics since GI tolerance rather than glycemic index is the priority), and A/B grade. Brand table uses Avg Protein + Avg Calories as its two metric columns.

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
Custom Referral Link (Y/N flag — "Yes" or "None", NOT a URL, see warning below),
positive_ingredients, concern_ingredients,
Vegan (Y/N), Gluten Free (Y/N), Dairy Free (Y/N), Soy Free (Y/N),
Non-GMO (Y/N), Nut Free (Y/N), Kosher (Y/N)
```

**`Custom Referral Link` is a boolean flag, not a URL — never write its raw
value into a link/href.** It marks whether this bar's brand relationship is
one of our highest-revenue-driving affiliate deals; the actual outbound URL
for "Shop on Brand Site" always comes from `Website`, regardless of what
`Custom Referral Link` says. Any page generator that reads this field must
use it only as a boolean gate (e.g. to decide styling/priority), never as
the href value itself. See "Known issues" below for the 2026-08-19 incident
this caused and the list of brands most at risk of a repeat.

Grade colors: A=#2a7a1f, B=#5a8a2f, C=#b89a00, D=#c87020, F=#c83020
Grade definitions: A=Clean, B=Good, C=Okay, D=Poor, F=Avoid

Net carbs formula: Total Carbs - Fiber - Sugar Alcohol (full subtraction, not divided by 2 — this line previously said "/2" which was wrong and caused a conflict with GUIDE_CRITERIA.md; see that file's "Net carbs formula" and "Maltitol family exclusion" sections for the full formula and the research behind it, corrected 2026-08-18)

### Building brand pages from bars.js
When building or rebuilding a brand page, always extract data directly from bars.js using node or Python. Do not rely on the old HTML page for ingredient data — it may be inaccurate. The pipeline:
1. Filter bars.js by brand name (check for all sub-brands, e.g. "Clif Builders", "Clif ZBar")
2. Sort by ingredient_score descending
3. Use exact ingredient text, amazon affiliate URL, and macro data from the database
4. Build rows using the template row pattern from TEMPLATE_BRAND.html

---

## Scoring pipeline

Bars scored using `score_and_export.py` against `knowyourbar_scoring_schema_v6.xlsx`
- 1,278 canonical ingredients
- 2,312 aliases
- Sub-ingredients in parentheses get 60% weight
- 220+ A-rated bars in current database (1,157 total bars as of 2026-08-13)

### Grade bands (current schema)
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
- Guide pages all rebuilt to consistent TEMPLATE_GUIDE.html (7 of 9 — `no-seed-oils.html`, `no-sugar-alcohols.html`, `no-artificial-sweeteners.html`, `clean-protein-bars.html`, `best-bars-for-diabetics.html`, `keto-protein-bars.html`, `glp1-protein-bars.html` — now on the newer rev 8 standard; see "Guide pages" section above for the rest)
- Mobile hamburger menu now functional on all rev 8 guide pages (fixed 2026-08-18 for the first 4; `keto-protein-bars.html` and `glp1-protein-bars.html` included the same handler from the start on their respective rebuilds, so no separate fix was needed)
- SEO schemas complete on all brand and guide pages
- ingredient_scoring.html fixed (horizontal scroll, grade bands table, copy)
- Sitemap updated — all live pages indexed
- Page speed grade A-93
- Cloudflare cache headers configured via _headers file

---

## Known issues / next priorities

### Brand pages needing the 2026-08-11 standard applied
`quest-bars.html` and `rxbar-review.html` were rebuilt to the structural template on 2026-08-09, before the alignment fix, font-family fix, grade-range tile, Good/Concerning patterns grouping, best-to-worst grade ordering, the "which flavor should you buy" section, and the voice/analysis pass documented above. They still work and the CSS fixes in style.css already apply to them (those were shared-file fixes, not per-page), but their **content and section list** predate all of it. Bring each up to the Barebells standard, one page per session, using Barebells as the structural and voice reference — not a from-scratch rebuild, since the underlying data/table architecture is already correct on both. `clif-bar-review.html` and `kind-bars-review.html` are still on the older pre-2026-08-09 template entirely and need the full rebuild. Clif still needs a sub-brand scoping decision (Clif Bar vs. Clif Builders). **KIND's scoping question is resolved as of the 2026-08-13 database update** — "KIND Protein Max" no longer exists as a separate brand, its 4 flavors merged into plain "KIND" alongside 11 newly-added KIND flavors — see "Scoring pipeline integrity (schema v6)" above. KIND's rebuild is otherwise unblocked and should also get a `verify_brand_data.py` pass for the new/merged flavors regardless of when the structural rebuild happens.

### Link integrity — brands at risk of the 2026-08-19 broken-link bug
44 bars across 10 brands (B.T.R. Nation, Gryp, IQ Bar, Jesse's GOODNITE!,
Jesse's WAKEUP!, Lineage Provisions, Off the Farm, Real Food Bar, Redefine,
Takeaways) have `Custom Referral Link == "Yes"` in bars.js. See the
"Data-integrity incident" section above for full detail. Only
`keto-protein-bars.html` was affected as of 2026-08-19. `caffeine-protein-bars.html`
(rebuilt 2026-08-20) includes 4 flavors from this at-risk list (3× Jesse's WAKEUP!,
1× Real Food Bar) and passed a pre-upload scan clean — links pulled correctly
from the `Website` field, not the `Custom Referral Link` Y/N flag. Any future
guide or brand page rebuild that includes flavors from these 10 brands
should get the broken-link-field scan from `QA.md` section 1 run against it
before presenting, since the underlying page generator that caused this bug
is not ruled out as reused elsewhere.

### Data accuracy — separate issue from the above
`barebells-review.html` and `quest-bars.html` needed a `verify_brand_data.py` pass and copy refresh after the schema v5 pipeline fix changed their underlying grades/scores. **This is done as of 2026-08-12** (re-verified against live `bars.js` on 2026-08-18, still accurate through schema v7). See "Scoring pipeline integrity" sections above for full detail.

### CSS
- ~~Stray duplicate `</body>` closing tag at the very end of `no-sugar-alcohols.html`~~ — fixed 2026-08-18, tag balance now passes clean on all 4 rev 8 guide pages.
- ~~Mobile long "Why"/Note column text causes tall, cramped, word-per-line brand-table rows on mobile~~ — fixed 2026-08-19/20 with a shared `@media (max-width: 700px)` block in `style.css`; table now overflows and scrolls horizontally inside `.table-scroll` instead of squeezing columns. Verified on Keto, No Sugar Alcohols, and Diabetics. See "Brand-listing table architecture" note above for full detail.
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
