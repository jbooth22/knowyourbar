# KnowYourBar.com — Project Briefing
*Upload this file at the start of every new Claude session.*
*Last updated: 2026-09-30 (second session). **All fifteen guides are now on the v2 layout: caffeine-protein-bars.html ("8 Best", 290KB → 109KB) and creatine-protein-bars.html ("6 Best", 124KB → 68KB) went last, as "small guides" that show as many picks as the rules allow instead of 10; see `claude/GUIDE_PAGE_SPEC_V2.md`.** **Database 43 is live (only change vs 42: Fro Pro Cookies and Cream lost its Soy Free label, so soy-free is now 291 bars; bars.js, llms.txt and soy-free-protein-bars.html shipped, Best 10 unchanged). Database 42 added the Aloha vegan labels; high-fiber-protein-bars.html, kosher-protein-bars.html, soy-free-protein-bars.html, dairy-free-protein-bars.html, vegan-protein-bars.html, glp1-protein-bars.html, keto-protein-bars.html and best-bars-for-diabetics.html are on the v2 "Best 10" layout** (dairy-free 843KB → 129KB, see "2026-09-30 Database 42 + Dairy Free v2"; vegan 889KB → 131KB; glp1 249KB → 91KB, `?preset=glp1` matches exactly; see "2026-09-30 GLP-1 v2") (keto 474KB → 134KB; its Bar Finder button is a documented near-match because the Bar Finder has no minimum-fat slider; see "2026-09-30 Keto v2"). Diabetics (456KB → 134KB, now with ItemList schema and a Bar Finder deep link that matches its 89 bars exactly; see "2026-09-30 Diabetics v2" under Known issues, and `claude/GUIDE_PAGE_SPEC_V2.md` for its locked slots and picks). Earlier on 2026-09-30: **clean-protein-bars.html went v2** (1.47MB → 125KB; the last guide over 1MB), bars.js regenerated from database 41 (only the two Jacked Granny bars changed), and the Best 10 tie chain gained a **buy-link tiebreak** and a **per-guide shuffle for exact ties**, which changed a few picks on the four earlier v2 guides (see "2026-09-30 Clean v2 + tiebreak" under Known issues). Before that, 2026-09-29 (second session): **Scoring v13 shipped** (blend fixes + clean-label floor; see "Scoring pipeline" and `claude/SCORING_BLEND_AUDIT_2026-09-29.md`), and no-artificial-sweeteners, gluten-free-protein-bars and no-seed-oils went v2. Earlier on 2026-09-29: the no-sugar-alcohols v2 pilot, the About page and guide byline, a Bar Finder slider fix, and page-weight QA (see "2026-09-29 Guide v2 pilot"). Before that: 2026-09-28, the sitewide buy-button and mobile table UI pass (see "2026-09-28 UI pass" under CSS architecture and Known issues). Before that: 2026-09-17, refreshed against the live site zip Jeff uploaded that day (knowyourbar-main_36.zip), not just prior session notes. See the "Verified 2026-09-17" note under Known issues for exactly what was checked directly against the files vs. carried over from before. Soy Free and Kosher guide pages shipped later the same day. See the File structure and Known issues entries below.*

---

## What this site is

KnowYourBar.com is a protein bar database and finder tool. We scored 1,000+ protein bars A-F by ingredient quality using a transparent, rule-based scoring system. No sponsorships. No bias. Users can filter, compare, and find bars that match their dietary goals.

**Live at:** knowyourbar.com
**Hosting:** Cloudflare Pages (deploys from GitHub, manual upload)
**GitHub:** jbooth22/knowyourbar
**Analytics:** GA4 — G-SW4MNP5W7J
**Affiliates:** Amazon (tag: knowyourbar0f-20), AvantLink, Impact

**Do not upload or read `claude/CHANGELOG.md` as part of normal work.** It exists for exactly one situation: you're debugging something that smells like a repeat of a past bug, or a rule below feels arbitrary and you need the "why." In that specific moment, search it for the relevant entry — don't read it top to bottom, and don't pull it in "just in case" or "for context." If you're not actively debugging a suspected repeat, you don't need it.

---

## File structure

```
index.html              — Homepage. Links out to bar-finder.html for the actual tool.
bar-finder.html         — The actual bar finder tool (filter/search/sort/compare UI, loads app.js).
                           Preset deep links (?preset=SLUG) point here, not at index.html.
app.js                  — All filter, search, sort, compare, expand logic
bars.js                 — Full bar database. **Verified 2026-09-30: 1,308 bars, generated from
                           "KYB - New Protein Bar Database 2026 42.xlsx"** (42 = 41 plus Aloha's 18 bars marked vegan). (Database 40 reproduced the
                           database-39 bars.js byte for byte; 41 changed only Jacked Granny Chocolate and
                           PB and J macros, no grades.)
                           Public copy always says "1,000+," never an exact figure.
style.css               — ALL shared styles — single source of truth
_headers                — Cloudflare Pages cache + security headers
scan.html               — Barcode scanner (knowyourbar.com/scan). Camera scan (UPC/EAN) or manual
                           brand/flavor/UPC search, resolves to the same detail view as a bar-finder
                           expand row. Backed by upc_map.js (~2,100 UPCs / ~980 products, roughly 75%
                           of the database). **Status as of the 2026-09-17 site zip: linked in nav on
                           every page and present in sitemap.xml (lastmod 2026-09-12) — the earlier
                           "don't add the nav link / sitemap entry until iOS camera reliability is
                           resolved" hold appears to have been lifted, or the link went in before that
                           was fully confirmed. The live scan.html still contains the "Take a photo
                           instead" fallback (4 occurrences) — the v3 rewrite that was supposed to
                           remove it and add the FAQ/UX pass was delivered as a standalone file, not
                           yet applied to this repo copy as of this zip. Confirm with Jeff whether (a)
                           the iOS camera issue is actually resolved and the nav link is intentional, and
                           (b) whether the v3 scan.html rewrite still needs to be applied — don't assume
                           either from a past doc.**
upc_map.js              — UPC → bars.js key lookup for scan.html. ~2,117 UPCs across 981 products as of
                           2026-09-12; roughly 75% of the database has at least one mapped UPC.
about.html              — "Who's behind Know Your Bar" (shipped 2026-09-29). Jeff Booth, a regular
                           consumer, not a dietitian; how the data is built; independence; how the site
                           makes money. AboutPage + Person schema. Target of the guide byline.
                           **Its "commissions never change a rank" lines need Jeff's rewrite since the
                           2026-09-30 buy-link tiebreak (see Known issues).**
TEMPLATE_BRAND.html     — Master template for brand review pages
TEMPLATE_GUIDE.html     — Master template for v1 lifestyle guide pages (v2 guides are built by
                           kyb_guide_lib.py instead, see Guide pages below)
kyb_guide_lib.py        — Shared guide build library. The v1 helpers are at the top. The "GUIDE PAGE v2"
                           section (added 2026-09-29) holds the Best 10 picker, v2 page shell, v2 QA
                           and the Big Brands list. After it, a small block of shared v2 helpers (count
                           cards, in-section Bar Finder button, lead sweetener, Highest fiber slot).
                           2026-09-30: `buy_rank()`, `set_tie_seed()` / `tie_shuffle()` and the new
                           tie chain (see Guide pages); later that day `KT_COLS['netcarbs']` and
                           optional `cols` / `hide_mobile` on `top50_html()` (defaults unchanged), then
                           `KT_COLS['fat']` for keto.
score_and_export.py     — THE scoring pipeline script actually in use. Takes the schema file as a
                           --schema argument, so it doesn't need code changes when the schema version
                           bumps — only the schema file and this briefing need to reference the new version.
knowyourbar_scoring_schema_v12.xlsx — Current ingredient scoring schema (the 2026-09-28 repo zip
                           carries v12; the 2026-09-17 note here said v11). Always use the newest schema
                           in the repo + the current score_and_export.py, never an older copy of either.
build_*.py              — Per-page build scripts (one per guide/brand page, plus build_index.py etc.)
                           that regenerate each page from bars.js. **A copy edit on a generated page
                           must also go into its build script**, or the next rebuild reverts it.
build_brand_rankings.py — Regenerates all-protein-bar-brands.html from bars.js. Read
                           BRAND_RANKING_METHODOLOGY.md before touching the ranking formula/categories.
                           Also carries its own embedded copy of the shared `<footer class="site-footer">`
                           markup (used when generating brand-ranking-style pages) — kept in sync with the
                           collapsible-footer change below as of 2026-08-30, and with the affiliate-
                           disclosure line added 2026-09-14 (see the Buy buttons / affiliate disclosure
                           note under CSS architecture below).
generate_brand_links.py — Propagates the live brand count into the pill-grid link on brand pages that
                           carry the BRAND_LINKS_START marker. Historically `clif-bar-review.html` was
                           the one page missing the marker entirely — check its current state directly
                           before assuming that's still true, since it wasn't re-verified in this pass.
diff_bars_upload.py     — Diffs a new bars.js against the previous one; run before trusting a database
                           update's blast radius.
verify_brand_data.py    — Spot-checks a brand's grades/scores/chip frequencies against live bars.js.
                           Run before writing any copy claim (grade, score, macro, percentile, chip name).
update_sitemap_lastmod.py — Sets every sitemap <lastmod> from each page's dateModified/footer date.
                           Touches every URL at once; for a one-page change, edit that one lastmod by hand.
qa_page_weight.py       — Page-weight QA (QA.md section 1b, added 2026-09-29): v2 guides under 400KB with
                           the FAQ and footer inside the first 300KB, plus the v2 invariants. Reports every
                           other page over 1MB/2MB.
sitemap.xml / robots.txt
llms.txt                — LLM crawler discovery file (do not delete). **Found 2026-09-17: carries
                           inconsistent bar-count references (both "1,300" and "1,307" appear in the
                           file) — needs a pass to make every count consistent with the live 1,307-bar
                           database.** Resolved 2026-09-28: llms.txt now says "1,000+" for the database
                           size everywhere (build_llms_txt.py uses DB_PUBLIC / of_db). Its numeric claims are NOT covered by the monthly bars.js refresh
                           or by any guide/brand page's own rebuild checklist — nothing touches this file
                           automatically. Spot-check its stats against live bars.js periodically, not
                           just when adding a page. (It still says "Full list:" for the v2 guides, which
                           are now Best 10 + Top 50 pages.)
BRIEFING.md              — This file
README.md                — Public-facing technical overview (short, non-authoritative on anything
                           this file also states — see README's own note)
QA.md                    — QA checklist, run before every upload
GUIDE_CRITERIA.md        — Canonical filter formula per guide page — load before touching any guide's logic
claude/GUIDE_PAGE_SPEC_V2.md — LOCKED spec for the v2 "Best 10" guide layout, with every migrated guide's
                           locked slots, picks and Bar Finder link — load before building or migrating any guide
BRAND_RANKING_METHODOLOGY.md — Canonical KYB brand-ranking formula/tiers — load before touching that page
BRAND_STANDARDS.md      — Locked v1 visual system (--bs-* tokens). NOT fully live — see below.

Brand review pages (all rebuilt from TEMPLATE_BRAND.html):
  quest-bars.html, rxbar-review.html, clif-bar-review.html, barebells-review.html,
  kind-bars-review.html, quest-vs-rxbar.html (a brand-vs-brand page — TEMPLATE_VS.html, its old
  master template, was removed from the repo and is no longer even worth keeping as a project doc
  reference; it does not exist in the live site. If another brand-vs-brand page gets built, use
  quest-vs-rxbar.html itself as the structural/voice reference.)

  **Verified 2026-09-17, directly against the live files, not carried over from a prior note:**
  - `rxbar-review.html`'s title has changed from any earlier version — it currently reads "Are RXBAR
    Bars Actually Healthy? We Checked All 12 Flavors." If this was the planned CTR test (snapshot
    baseline, one change, wait 3-4 weeks, diff), confirm with Jeff when it went live so the 3-4 week
    clock is tracked from the right date — don't assume it just went out.
  - All five brand pages (Quest, RXBAR, Clif, Barebells, KIND) carry the 2026-09-14 buy-button
    redesign (`.pick-tile-buy` present on all 5) and the sitewide affiliate disclosure line. **Their
    JSON-LD `dateModified` fields were NOT all bumped for this pass** (Quest/RXBAR/Barebells still show
    8/10-8/12, Clif/KIND show 9/03) — that field is unreliable for judging "when was this page last
    touched" after a cosmetic/UX-only session; check for the actual feature (button markup, footer
    disclosure div) instead of trusting dateModified alone.

Guide pages (v1 pages rebuilt from TEMPLATE_GUIDE.html, rev 8; **thirteen guides are on v2**):
  **v2 "Best 10":** no-sugar-alcohols.html (pilot, 2026-09-29), no-artificial-sweeteners.html,
  gluten-free-protein-bars.html, no-seed-oils.html (2026-09-29), clean-protein-bars.html,
  best-bars-for-diabetics.html, keto-protein-bars.html, glp1-protein-bars.html, vegan-protein-bars.html, dairy-free-protein-bars.html, soy-free-protein-bars.html, kosher-protein-bars.html, high-fiber-protein-bars.html (2026-09-30).
  **Still v1:**
  low-sugar-high-protein.html (merged into Keto + Diabetics 2026-08-20, kept live at its URL as a
  short router page to preserve search equity rather than deleted),
  caffeine-protein-bars.html,
  creatine-protein-bars.html (**live — confirmed 2026-09-17**, a real page in sitemap.xml, not the
  "too thin for a full guide" placeholder an earlier note here described. Carries the emoji fix noted
  under Known gotchas below.),
  soy-free-protein-bars.html (**shipped 2026-09-17**, Soy Free (Y/N) cert field, 293 of 1,307 bars.
  Soy free bars grade A/B notably higher than the database average, correlation with fewer artificial
  sweeteners/processed oils, not because soy protein/lecithin are penalized -- see GUIDE_CRITERIA.md.),
  kosher-protein-bars.html (**shipped 2026-09-17**, Kosher (Y/N) cert field, 149 of 1,307 bars.
  Structurally different from the other cert guides: only ~8% of non-kosher bars have an identifiable
  non-kosher ingredient (gelatin/confectioner's glaze/carmine/rennet), the other ~92% simply aren't
  certified. Kosher bars grade about the same as the database average, unlike Soy Free -- see
  GUIDE_CRITERIA.md.).

Data / visualization pages:
  all-protein-bar-brands.html — Full brand summary table (generated, do not hand-edit)
  brand-quadrant.html         — Magic Quadrant scatter plot
  kyb_scatter_interactive.html — Standalone interactive D3 scatter page. Deliberately NOT linked from
                           site nav, sitemap.xml, or llms.txt — this is the page behind the 500+-upvote
                           Reddit post, kept as a standalone share link. Do not delete or fold into
                           navigation without checking with Jeff.

Other:
  ingredient_scoring.html — How we score page
  about.html               — About page (see above)
  flavor-map.html          — Sankey diagram visualization
  scan.html / upc_map.js   — see File structure entry above.
```

---

## Standing operational rules (lessons from past incidents — still in force)

*Which pages currently need a refresh or rebuild is not tracked in this file — Jeff manages that and will say what he wants changed at the start of a session. A per-page status table went stale within days the one time this file tried to carry it, so it doesn't anymore. Never infer "done" or "not done" for a page from a past session's notes here — check the actual uploaded/live file. The 2026-09-17 session (see Known issues) found several things this file claimed were "not yet done" that had, in fact, already shipped — that's the exact failure mode this note is warning about.*

- **When in doubt about current state, check the live files, not this document.** This file is a working reference, not a guaranteed-current source of truth — it drifts between sessions, sometimes for weeks, and has been caught stating stale "still open" items that were already resolved. If Jeff says "I already did X" and this file disagrees, trust Jeff and verify against the uploaded files before arguing the point.
- **Monthly, not ad hoc, database-update cadence.** (A small targeted update like database 41's Jacked Granny fix is fine when Jeff uploads it: run the normal pipeline, `diff_bars_upload.py` first, then rebuild every page, and ship only pages whose content changed beyond dates.)
- **One guide/brand page per session** for a full refresh or rebuild — don't bulk-refresh several at once. (A batch of small, independent cosmetic/UX/copy fixes across several files in one session is a different kind of session and this rule doesn't block it. Jeff explicitly asked for three v2 migrations in one session on 2026-09-29, with approval of each guide's slots and picks before its build; treat that as his call per session, not a new default.)
- **Recompute the qualifying count from scratch on every guide refresh**, against live `bars.js` — never increment or copy a prior number.
- **Ingredient quality is shown and ranked by GRADE only (LOCKED 2026-09-29, Jeff).** Bars in the same grade are treated as equal: the score isn't precise enough to split them. Never print a raw ingredient score to readers on v2 pages, and never use it to rank a pick or break a tie. (v1 pages still show the score in expand panels until they migrate.)
- **Buy-link tiebreak (LOCKED 2026-09-30, Jeff).** Inside a Best 10 slot, right after grade: a bar with one of our brand referral links (`Custom Referral Link` = Yes) wins, then a bar with an Amazon link, then brand site only. It only decides between bars already tied on the slot's number and grade, and the criteria section says so. Exact ties on every step are then shuffled per guide (`set_tie_seed(<slug>)` in every v2 builder), so identical-macro twins don't win on every guide by alphabet.
- **A certification (Y/N) field filter is not immune to data hygiene bugs** — on every certification-field guide refresh (Vegan, Gluten Free, Dairy Free, and any future one), check the field's actual distinct values in live bars.js for anything other than exactly `'Yes'` or `None` before trusting a strict `==` filter. (The gluten-free v2 builder now checks this on every build.)
- **On every guide data refresh:** recompute every Best 10 / Top-Picks pick fresh against the new qualifying set (v2 builds do this automatically). On v1 guides only, also check the hidden `gd-bar-data` lazy-load block for a real render path. Verify with a headless browser (`getComputedStyle().display`), not the result-count text, which can lie. v2 guides have no `gd-bar-data` block; their Top 50 expand loads from bars.js. Brand pages (TEMPLATE_BRAND.html) use a fully static-generated table with no lazy-load block, so this class of bug does not apply there.
- **Every guide's Bar Finder button count must match the Bar Finder.** Open the deep link headless and compare `#result-count` with the guide's N (QA.md 1b). One approved exception: keto (no minimum-fat slider), whose button says it opens 170 bars and why; its count is checked against 170.
- **A suspect grade on a pick gets a HOLD, not a silent swap.** If a bar's grade looks wrong (e.g. an A with sucralose and palm oil), ask Jeff; if he agrees, add its key to the builder's `HOLD` set (kept out of the Best 10 and Top 50, still counted and still in the Bar Finder) and flag it for rescoring. Remove it once rescored.
- **Never re-score or edit bars.js directly, and never write a new script to work around a missing file (Jeff, 2026-09-29).** Scoring changes go into `score_and_export.py`; to apply them, ask Jeff for the current database Excel and run the normal pipeline. The repo already has too much tooling; ask for the file instead of building around it.
- **After any HTML change that touches a page's inline `<script>` block, run `node --check` against just that inline script.**
- **`llms.txt`'s numeric claims are not covered by any other refresh workflow** — spot-check it on its own schedule. **Currently overdue: see the inconsistent-count note under its File structure entry above.**
- **`Custom Referral Link` in bars.js is a Y/N boolean, never a URL.** The real outbound URL always comes from `Website`. Run QA.md's broken-link-field scan on every upload, repo-wide.
- **Avoid-table brand-name cells are always static/non-clickable**, regardless of how many qualifying flavors that brand has.
- **Every editorial claim (grade, score, macro range, percentile, chip name) must be verified against live `bars.js` with `verify_brand_data.py` before it's written.**
- **Percentile/macro-rank claims are computed against the live `bars.js` at build time**, never hand-typed or copied from a previous version of the page.
- **`low-sugar-high-protein.html` was merged into the Keto and Diabetics guides on 2026-08-20** and is kept live at its URL as a short router page. Don't point guide editorial at it (removed from clean 2026-09-30; diabetics' guide copy never referenced it); it's still in the shared nav/footer.
- **A schema-gap audit alone isn't enough on a new database upload** — also scan for fallback substring-matcher false positives.
- **Always use the current schema `.xlsx` + the current `score_and_export.py`** — currently v12 in the repo, never an older copy of either.
- **Isomalto-oligosaccharide (IMO) is a prebiotic fiber, not a sugar alcohol** — fixed schema v10, don't reintroduce the confusion. (Note: the guide screens `has_sugar_alcohol()` / app.js `hasSugarAlcohol()` still treat IMO as a sugar alcohol for the No Sugar Alcohols screen, and IMO bars like Daryl's carry a "Sugar Alcohols" chip. That's the guide screen, not the score. The diabetics guide counts IMO as fiber, per the label, and carries a note that some research suggests it is partly digested like sugar; Jeff chose the note over a screen change, 2026-09-30.)
- **A parser bug can hide behind an "unmatched ingredient" that looks like a random garbled phrase** — check for a nested parenthetical before assuming it's just a missing alias.
- **A substring-fallback false positive can hide inside an otherwise-plausible-looking match** — see the Honeydew/honey, Butterfly Pea Flower/butter, isomalt-family incidents in claude/CHANGELOG.md if a new one turns up.
- **A GSC keyword gap a page already answers goes into an anchored section on that page, not a new URL.** Keep those anchors when migrating to v2 (#no-sucralose, #brand-seed-oil-check and #no-erythritol are all linked from other pages or answer GSC queries).
- **Before assuming a ranking gap between peer pages has an on-page cause, verify there is one** — KIND vs. Barebells/RXBAR turned out to be mostly a domain-authority/competition gap, not a fixable defect.
- **`app.js`'s two slider-key maps (`readURLParams`'s and `serializeState`'s, both called `sliderMap`) must be edited together and must always match `SLIDERS_CFG` 1:1.** (The diabetics Bar Finder link depends on the `protein`, `sugar`, `fiber` and `netcarbs` keys.)
- **When reverting rebuild noise with git, match build script names with underscores too** (`build_no_seed_oils.py`, not just `no-seed-oils`). A hyphen-only filter reverted three freshly written builders on 2026-09-29; they were restored and verified byte-identical against the pages they had produced.

---

## Brand review pages — TEMPLATE_BRAND.html

All brand pages use TEMPLATE_BRAND.html — the locked standard, with `barebells-review.html` as the gold-standard reference. When a page needs bringing up to standard, use Barebells as the structural and voice reference, one page per session.

### Template section order
1. Head: title/meta/canonical, 4 JSON-LD schemas (Article `headline` matches the H1, not the `<title>`)
2. Nav
3. Hero (H1 + short answer paragraph)
4. Macro breakdown grid (9 tiles: **Grade Range first**, then Protein, Protein/100cal, Calories, Total Sugar, Sugar Alcohol, Fiber, Total Fat, Net Carbs) + SEO blurb
5. Overview summary (2-3 paragraphs, grounded in specific measurable deltas)
6. Grade distribution bar
7. Best and worst flavor cards (with chips)
8. Ingredient quality patterns — grouped **Good qualities / Concerning qualities / Neutral**, most-frequent-first within each group
9. Full flavor table (11 columns: BAR, CAL, PROT, P/100, FAT, CARB, FIBR, SGR, SGR ALC, CERTS, GRADE; rich expand rows — macro-rank grid computed live against the current database; colspan 11; toggleIngr index starts at 0, no gaps)
10. Bottom line (2 paragraphs)
11. "Which [Brand] flavor should you actually buy" (3-5 situational picks. As of 2026-09-14, every tile naming a genuine buy recommendation also gets a "Shop on Amazon" button — see the Buy buttons note under CSS architecture below.)
12. Discover module (CTA + related reading)
13. Brand comparison table — grade ranges **best to worst**
14. Every brand we've reviewed (pill-grid — generated by `generate_brand_links.py` from `brands_manifest.json`)
15. FAQ (7+ questions, must match FAQPage JSON-LD exactly)
16. Footer

### Locked conventions
- **Grade ranges always shown best-to-worst** everywhere a range appears.
- **Ingredient patterns grouped by type** (Good/Concerning/Neutral), not by frequency tier.
- **Title vs. H1 don't have to match** — optimize title for search/social, H1 for the reader; JSON-LD `headline` matches the H1.
- og:type is "article" on brand pages. Meta description leads with a specific data point, under 155 chars, no em dashes.

### Voice and analysis principles
- Don't lean on the raw ingredient score as if it means something on its own — explain *why* the gap exists.
- Ground sub-brand/"two lines" narratives in measurable deltas, not a label.
- The "which flavor for which situation" section needs real, verified per-flavor reasoning.
- Keep percentile claims separated by metric.
- Flavor names must match `bars.js` exactly, including spelling.
- Treat the brand name as singular in verb agreement ("Barebells is," not "Barebells are").

---

## Brand ranking page — all-protein-bar-brands.html

Fully generated by `build_brand_rankings.py`, never hand-edited. Composite rank: 60% ingredient quality / 25% protein efficiency / 15% fiber, intentionally not surfaced as a named/branded metric. Distribution tiers (Widely Available / Mid-Size & Specialty / Small & Online) are editorial, hand-curated in the script, not derived from `bars.js`. Full formula, thresholds, and the Bar Finder deep-link slugify rule live in `BRAND_RANKING_METHODOLOGY.md`. Re-run `build_brand_rankings.py` any time `bars.js` changes.

---

## Guide pages

### v2 "Best 10" layout (LOCKED 2026-09-29; live on no-sugar-alcohols, no-artificial-sweeteners, gluten-free, no-seed-oils, clean, diabetics, keto, glp1, vegan, dairy-free, soy-free, kosher, high-fiber)
The full spec, every locked decision, and each migrated guide's slots and picks are in `claude/GUIDE_PAGE_SPEC_V2.md`. Read it before migrating a guide. In short:
- Section order (revised after Jeff's live QA, 2026-09-29): hero (H1 + two short paragraphs that define the category and give the key numbers; no verdict line, stat block or byline; no visible date) → Best 10 cards → "what [criterion] means" editorial → What we found (3 findings + 1 chart) → Brands that do it well → How the big brands fare → Top 50 (tap to expand from bars.js, both buy links) → "See all N in the Bar Finder" → How we picked these → FAQ → Related guides → one-line author note at the very bottom. The "Best 10 at a glance" table was removed as redundant.
- Bar Finder links are always big buttons, never inline text links. "and N more" lists expand inline with "Show less" at the end. Data tables use the compact `.kt-table` style and must not scroll sideways at 360px.
- Best 10: 6 core slots (Best overall, Cleanest ingredients, Highest protein capped at 300 cal, Most protein per calorie, Lowest calorie (best grade first), Best from a big brand) + 4 guide-specific slots + fallbacks. Grade B+, 10g+ protein, no bar twice on a page, max 2 per brand. Best overall = best grade, then most protein per 100 calories, 15g+ protein. On guides that don't already exclude sugar alcohols, "Lowest sugar" only considers bars with no sugar alcohol.
- **Tie chain (2026-09-30):** grade → buy link (referral, then Amazon, then brand only) → protein → sugar → fiber → calories → per-guide shuffle → name.
- **Guide slots for new guides (Jeff, 2026-09-30):** prefer slots people shop on (Best whey protein, Lowest net carbs, Best non-GMO / soy-free / dairy-free / gluten-free, Lowest sugar, Highest fiber, Best plant-based) and rotate them across guides to keep lists fresh. Jeff finds date-sweetened, snack size, allulose, stevia/monk fruit, egg-white and oat-free too narrow; don't propose them again. Organic needs a certified-organic field first.
- Bar Finder deep links (all verified count-for-count headless 2026-09-30): no-sugar-alcohols `?preset=no_sugar_alcohol` (968), no-artificial-sweeteners `?excl=sucralose` (1,060), gluten-free `?certs=GF` (835), no-seed-oils `?preset=no_seed_oil` (695), clean `?preset=no_seed_oil&grade=A,B&excl=sucralose` (514), diabetics `?grade=A,B&protein=10&sugar=5&fiber=5&netcarbs=10&excl=maltitol,polyglycitol,hydrogenated%20starch%20hydrolysate` (89), glp1 `?preset=glp1` (21), vegan `?certs=Vegan` (281), dairy-free `?certs=Dairy%20Free` (247), soy-free `?certs=Soy%20Free` (292), kosher `?certs=Kosher` (154), high-fiber `?fiber=11` (103); keto is the exception: `?protein=10&netcarbs=8&excl=maltitol,polyglycitol,hydrogenated%20starch%20hydrolysate&sort=fat:desc` (170 = the 104 keto bars + 66 under 8g fat; the button says so). Params combine with AND in app.js, so preset + grade + excl + certs + slider params (`protein`, `cal`, `fat`, `carbs`, `sugar`, `sa`, `fiber`, `netcarbs`) can be stacked when no single one matches.
- Hard targets: under 400KB, FAQ and footer inside the first 300KB, all 5 schema types kept. The build refuses to write a page that misses any of these.
- How to migrate a guide: copy the closest migrated builder (sweetener guide → build_no_artificial_sweeteners.py; certification guide → build_gluten_free_protein_bars.py; ingredient screen → build_no_seed_oils.py; multi-screen / macro screen → build_clean_protein_bars.py or build_best_bars_for_diabetics.py), call `set_tie_seed('<slug>')`, and point it at `build_guide_page_v2()`. The first run converts the live page, keeping its head, nav and footer. Drop any v1 "as of [date]" FAQ sentence. If a v1 head has no `kyb:jsonld-itemlist` region, reuse `ensure_itemlist_marker()` from the diabetics, keto or glp1 builder.
- Article `author` is Person Jeff Booth (url /about). `dateModified` only moves when generated content changes.

### v1 (rev 8) standard, still used by every other guide until migrated
All v1 guide pages share the section order, table pattern, and column rules below.

### Template section order
1. Head: title/meta/canonical, 4 JSON-LD schemas, OG/Twitter
2. Nav
3. Hero (H1 + short answer paragraph)
4. Snapshot stats (`.snapshot`/`.snap-item`)
5. Top Picks (6 tiles, 2 rows of 3, `.pick-tile-grid.top-picks-6`). As of 2026-09-28 every tile reserves two button rows, so the grade row and the Brand Site button line up across the grid even when a bar has no Amazon link (CSS only, no markup change needed).
6. Category explainer + key factors (`.score-card` callouts)
7. Findings dark section (`.findings`, `.big-stat`, `.insights-grid`)
8. Brands to Consider / Mixed / Avoid table (see below)
9. Bar list table (first 25 rows visible, rest behind Show More; columns vary — see deviations below)
10. Bar Finder CTA (`.explore-cta` linking to a pre-filtered tool URL — **confirmed 2026-09-17: this now points at the extensionless `/bar-finder`, the old `.html?preset=` hardcoding across templates/pages that a prior note flagged as still-pending has already been fixed sitewide.**)
11. Explore More (3 `.explore-more-card` links)
12. FAQ (7+ questions, must match JSON-LD exactly)
13. Footer

A GSC keyword-gap section inserts between step 6 and step 7 in practice so far — treat that as the default insertion point for the next one too.

### Brand table pattern (unified across all v1 guides, locked 2026-08-19)
Every v1 guide uses the same **Consider / Mixed / Avoid** three-table split. (v2 guides replace it with "Brands that do it well" + "How do the big brands fare".)
- **Consider:** `qualifying/total >= 75%` AND `total − qualifying <= 2`
- **Avoid:** `>= 80%` disqualified AND fewer than 3 qualifying
- **Mixed:** everything else (3+ qualifying AND 3+ disqualified)
- Avoid-table rows past the first 15 are hidden behind a show-more toggle.
- The Caffeine guide reframes the ratio column to mean "share of a brand's *caffeinated* flavors that clear A/B grade."
- Mobile (below 700px, updated 2026-09-28): `table.brand-table` and `.brand-compare-table` still scroll sideways inside their wrapper, but headers now wrap, the first column (brand name) is pinned, a right-edge shadow plus a "Swipe to see more columns →" line show there's more, and flavor-list tables let the Flavor column wrap. All CSS, no markup changes.

### Column deviations from the rev 8 default (BAR/CAL/PROT/P100/FAT/CARB/FIBR/SGR/SGR ALC/CERTS/GRADE)
- **Keto** uses FAT + NET CARB instead of CAL + SGR.
- **Caffeine** macro-rank grid uses Protein/Calories/Caffeine/Fat, with only Caffeine getting directional-green color.
- (Vegan, dairy free, soy free and kosher are now v2.) — certification flags, not macro screens. (Gluten Free is now v2.)
- **High Fiber and Creatine's own column conventions were not re-verified this session** — check the live pages directly before assuming they follow the default set.

### Disclaimer rule (health-condition guides: Diabetics and similar)
Must include, exactly: "We are not doctors or dietitians. These are the qualities we know people look for, so that's what we factored in." (Jeff, 2026-09-30: spelled "dietitians". The diabetics v2 page carries it in the hero and as a callout in "what it means"; keto and glp1 use the same wording.)

Filter formulas for every guide live in `GUIDE_CRITERIA.md` — load it before touching any guide's logic, never reconstruct a formula from a live page's copy. **Confirm GUIDE_CRITERIA.md actually has entries for High Fiber and Creatine — it was written before those pages shipped and may not.**

---

## Brand Standards v1 migration — READ BEFORE TOUCHING COLORS OR BUTTONS

`BRAND_STANDARDS.md` defines a locked future visual system (`--bs-*` tokens, ink-stamp buttons, Barlow Condensed, sentence case, no uppercase mono labels). **It is not fully live.**

- `style.css` has both token sets: the legacy `--black`/`--white`/`--accent` tokens (what nearly every page actually renders with) and the new `--bs-*` tokens (scoped `.brand-v1` overrides only).
- Nearly every page carries `<body class="brand-v1">`, but that only activates specific overrides already written into style.css — it does **not** mean the page is fully migrated.
- Before adding any new color, button style, or type treatment: check `BRAND_STANDARDS.md` first.
- `all-ingredients.html` and `ingredient-report.html` deliberately bridge `--font-display` to `--bs-font-display` (early, page-scoped Barlow Condensed adoption) — intentional, not drift.

---

## CSS architecture — READ BEFORE TOUCHING ANYTHING

**style.css is the single source of truth for all styles.** Never replace it wholesale, only append or use targeted str_replace. **Note (2026-09-28):** the repo copy is minified into about 57 very long lines (~105KB), not the "4,500+ lines" an earlier version of this file described. Appending a readable block at the end is fine; grep by selector, not by line number.

- index.html has an intentional inline `<style>` block for homepage-only CSS. Leave it there.
- Brand and guide pages carry no duplicate `:root` token blocks. `style.css` carries shared `.callout-box` and `.criteria-list` classes for page-specific depth sections — use these instead of a new page-scoped variant.
- `button, input, select, textarea { font-family: inherit }` is in style.css right after the `body{}` rule.
- `.gd-show-more-btn` has its own rule set (aliased to `.show-more-btn`'s rules).
- best-bars-for-diabetics.html still carries its v1 page-scoped `<style>` block (`.diab-*` rules) in the head. The v2 body doesn't use it; it was left in place because the v2 shell keeps the head as deployed and CSS is never stripped with regex. Harmless; remove by hand only if Jeff wants it gone.

### 2026-09-28 UI pass (appended block at the end of style.css)
One appended block, headed "2026-09-28 UI pass", overrides earlier rules by source order. It covers:
- Buy buttons sitewide (see the Buy buttons rule under Known gotchas).
- Top Picks tile alignment (reserved two-row button area, footer pinned to the bottom of the tile).
- Mobile brand tables and brand comparison tables (wrapped headers, pinned first column, swipe hint, edge shadow).
- Main bar table on phones: pinned bar-name column; the expanded row's buttons and macro-rank cards stay inside the screen (sticky + container query units), macro-rank cards go 2 per row, buy buttons stack below 480px.
- `.brand-compare-table th` switched from 9px uppercase mono to 12px bold DM Sans (Brand Standards: no small data-font labels).
- Uses `:has()` and container query units. Needs iOS 16.4+ / Safari 16+; older browsers just get the previous plain scroll. GA4 (last 90 days, 2026-09-28): roughly 4 of ~1,470 iOS sessions were below iOS 16, so not worth a fallback.

### 2026-09-29 Guide page v2 (appended block at the end of style.css)
Headed "2026-09-29 Guide page v2". Styles for v2 guides and the About page: `.b10-*` (Best 10 cards, glance / brands / big-brands tables), `.t50-*` (Top 50 rows, inline buy link on phones), `.gchart-*` (findings chart), `.hero-stat`, `.guide-byline`, link styling inside `.guide-v2` / `.about-page` section bodies. After it comes a one-rule "2026-09-29 Guide hero alignment" block (`.page-guide .hero-inner { max-width: calc(820px + 3rem) }`, which affects every guide page). Everything above these blocks is byte-identical to before. The second v2 rollout (three guides), the clean migration and the diabetics migration needed no CSS changes.

### Shared footer — collapsible link list (2026-08-30)
The shared `.site-footer` carries an 18+-link `<nav class="site-footer-links">` for internal-linking SEO, wrapped in a native `<details class="site-footer-links-toggle">` — collapsed by default, expands on click. Any future page built from either template, or any new footer link added, should go inside the existing `<nav class="site-footer-links">`. On v2 guides and about.html the footer's "Updated YYYY-MM-DD" stamp is replaced by an About link (no visible dates on v2 pages).

**Affiliate disclosure added 2026-09-14.** "As an Amazon Associate and affiliate partner, we earn from qualifying purchases through the links on this site." — a `.site-footer-disclosure` div, always visible (outside the collapsible `<details>`), on every page with the shared footer, plus a second copy on index.html's separate `.home-footer`. **Confirmed live on all 5 brand pages + index.html, 2026-09-17.**

**Bar Finder's `.finder` layout is normal page flow, not a fixed-viewport app shell (2026-08-30).**

### CSS variables (style.css :root)
```css
--black:      #0e0e0e
--white:      #f7f5f0
--off-white:  #efece6
--accent:     #d4f000
--muted:      #5a5a54
--border:     #d6d3cc
--font-display: 'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif   /* Syne was removed — single-story 'g' clipping, never reintroduce */
--font-mono:    'Roboto Mono', 'Courier New', Courier, monospace
--font-body:    'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif
--radius:     6px
--radius-lg:  10px
--bs-paper #fbf9f4 · --bs-cream #f2ede0 · --bs-ink #17140f · --bs-ink-2 #2b271e · --bs-text-dim #5c584c · --bs-line-soft #d8d2c2 · --bs-radius 3px
```

### Page type classes
- Brand review: `<body class="page-brand">`. Guide: `<body class="page-guide">`. index.html: plain `<body>`.
- Nearly all pages also carry `brand-v1` (partial override layer).

### Known gotchas (still relevant, don't rediscover these)
- **Font-family:** several data/numeric classes reference `--font-mono` with no `.brand-v1` override — check for a missing `.brand-v1` font-family override before assuming style.css didn't load.
- **Form controls don't inherit font-family from the page by default** — see the global reset rule above.
- **Hero/content alignment:** horizontal padding belongs on `.hero-inner`, not `.hero` directly. (Fixed 2026-09-29 for every guide page: `.page-guide .hero-inner` was 820px including its 24px side padding, so the H1 sat 24px right of the section headings. It's now `calc(820px + 3rem)`. The H1 and section headings share a left edge at 1280, 900 and 390px on all 19 guides and about.html, measured in a headless browser. ingredient_scoring.html uses its own content layout, so its section headings sit further in than its hero, which is a separate, pre-existing issue.)
- **`table.brand-table` sets fixed percent widths on columns 2–6.** A new table with more columns squeezes columns 7+ to zero width. v2 tables add `.b10-v2` to reset widths.
- **A fifth numeric column in a v2 Top 50 overflows at 360px** (diabetics, 2026-09-30: Grade, Protein, Sugar, Net carbs scrolled 17px). Keep phones at three numeric columns next to the Bar cell (hide the rest with `hide_mobile`) and measure `.kt-wrap` scrollWidth at 360px.
- **Buy buttons — exactly two styles, same size (redesigned 2026-09-28, replaces the 2026-09-14 lime rule):** Amazon = paper fill, 2px ink border, ink bold text (outlined). Brand Site = solid ink fill, 2px ink border, paper bold text. Both marked with a ↗, 40px min height (44px on phones), hover on Amazon flips to solid ink. **No lime, no orange, no accent color** on any buy button: the grade colors are the only accent on the site, and a bright button competes with them. **Never leave an Amazon button with a paper fill and no border** — that is exactly the bug that made Amazon read as plain text (an older `.brand-v1 .amazon-link` rule set `background: var(--bs-paper) !important` with no border). Classes covered: `.amazon-link`/`.visit-link` (guides, brand pages, Bar Finder expand rows, scan), `.cta-amazon`/`.vs-pick-amazon`/`.buy-btn` (Quest vs RXBAR), `.cmp-buy-btn`/`.cmp-site-btn` (Bar Finder compare), and the homepage's `.buy-amazon`/`.buy-site` in index.html's inline `<style>` (homepage has no `brand-v1`). Labels still differ by page ("Shop on Amazon" vs "Buy on Amazon" / "Buy from Brand") — that's copy, not style, and was left alone.
- `.boost-badge` (Caffeine/Creatine/Vitamins flags) is reserved for exactly those three supplement flags. Creatine boost-badge text has been emoji-free since 2026-09-09 for the JS-rendered badge; `creatine-protein-bars.html`'s own static table had a separate hardcoded emoji bug fixed 2026-09-14 — if this page is ever regenerated from scratch, re-check for the same hardcoded emoji.

### Hard rules — never break these
1. Never use regex to strip or modify CSS inside `<style>` tags.
2. Never replace style.css entirely — only append or use targeted str_replace.
3. Never remove a wrapper `<div>` without checking div balance afterwards.
4. After ANY HTML change: run the div balance check in QA.md.
5. After ANY JS change: run `node --check app.js`, and check any page's own inline `<script>` block individually too.
6. Always work from the actual uploaded file, not memory of previous sessions.

---

## index.html hero — current structure

1. Eyebrow: "The Protein Bar Database · No Sponsored Picks"
2. H1: "Every protein bar scored A-F on ingredient quality"
3. Subhead with inline "See how we score →" link (no separate CTA button for it)
4. CTA button: "Find My Bar →" (single button only — **never add a secondary CTA**)
5. Trust anchor: "Answer 3 questions · Get your match in 30 seconds"
6. A-rated bar row linking to all A-rated bars
7. Sample bar result card (real chips/macros from the database)

*Not re-verified against the live index.html this session — check directly if this structure matters for the current task.*

---

## Writing rules — apply everywhere on this site

**Never use:** em dashes anywhere (copy, meta descriptions, JSON-LD) · "It is worth noting" · "It is important to" · "Furthermore"/"Moreover"/"Additionally" · "Delve"/"Leverage"/"Robust"/"Utilize"/"Crucial" · "This is a deliberate brand strategy" · passive constructions that soften direct claims · filler qualifiers · a raw ingredient score shown to readers on v2 pages (grades only).

**Always use:** short, direct sentences · specific numbers over vague descriptors · active voice · plain-English verdicts · second person ("you") when addressing the reader.

**Tone:** knowledgeable, direct, slightly opinionated but always data-backed — a trusted friend who's actually read the ingredient labels, not a product reviewer covering their bases.

---

## The bar database (bars.js)

```
Brand Name, Flavor Name, score_band (A/B/C/D/F), ingredient_score (numeric),
Calories, Protein (g), Total Fat (g), Saturated Fat (g), Total Carbohydrates (g),
Dietary Fiber (g), Sugars (g), Sugar Alcohol (g), Sodium (mg), Cholesterol (mg),
Ingredients (full text), Amazon Affiliate (URL), Website (URL),
Custom Referral Link (Y/N flag — "Yes" or "None", NOT a URL, see warning above),
score_insights, positive_ingredients, concern_ingredients,
Vegan (Y/N), Gluten Free (Y/N), Dairy Free (Y/N), Soy Free (Y/N),
Non-GMO (Y/N), Nut Free (Y/N), Kosher (Y/N)
```
(No certified-organic field yet; Jeff: organic only counts if certified, so an "Organic (Y/N)" field would be needed before any organic slot or guide.)

Grade colors: A=#2a7a1f, B=#5a8a2f, C=#b89a00, D=#c87020, F=#c83020. Grade labels: A=Clean, B=Good, C=Okay, D=Poor, F=Avoid.

**Net carbs formula:** `Total Carbs − Fiber − Sugar Alcohol` (full subtraction, never divided by 2 — see GUIDE_CRITERIA.md). **Fixed 2026-09-29: app.js's Max Net Carbs slider used to halve sugar alcohol (`carbs - fiber - (sa / 2)` in applyFilters). It now subtracts it fully, matching the Keto preset and every guide.** Effect: at a 5g cap the slider shows 166 bars instead of 70, and at 10g it shows 412 instead of 322.

### Building brand pages from bars.js
Always extract directly from `bars.js` via node/Python — never trust an old HTML page's copy for ingredient data.
1. Filter by brand name (check all sub-brands, e.g. "Clif Builders", "Clif ZBar")
2. Sort by `ingredient_score` descending
3. Use exact ingredient text, Amazon URL, and macro data from the database
4. Build rows using the row pattern from TEMPLATE_BRAND.html

---

## Scoring pipeline

Bars are scored with `score_and_export.py` against the current schema file (**`knowyourbar_scoring_schema_v12.xlsx`** in the repo) — sub-ingredients in parentheses **and** square brackets get 60% weight, a NESTED parenthetical/bracket is flushed and comma-split at every depth transition, and each additional top-level protein ingredient beyond the single best-scoring one is discounted to 0.5x weight. Position weights and the ingredient-count adjustment are unchanged since v4. Canonical-ingredient and alias counts change with every schema version — don't hardcode a number here, check the schema file itself.

**Scoring v13 (2026-09-29, Jeff approved; code only, schema file still v12).** Rules added in `score_and_export.py`: the protein stacking discount now applies inside blends; positive non-protein members of one parenthetical count 1x, 0.5x, 0.25x (`BLEND_DIMINISH`); an ingredient counts once per label slot; plant names inside a "vegetable oil (...)" blend score as oils; and a **clean-label floor**: a bar with no ingredient scoring below 0 (and every ingredient known to the schema) grades at least A (score lifted to 8.0, `CLEAN_LABEL_FLOOR`). Grade mix went from A 285 / B 437 / C 338 / D 184 / F 64 to A 233 / B 393 / C 308 / D 246 / F 128. Full audit and examples: `claude/SCORING_BLEND_AUDIT_2026-09-29.md`. (Database 41, 2026-09-30: same grade mix.)

**Schema gap audit (run on database 41, 2026-09-30):** 6 unmatched phrases (top: "AND/OR PALM" 5x on Anabar, all already tagged Processed Oils; "LEAVENING", "SWEETENER", "PRETZEL", "FLAVORING", "GUM") and 25 partial-match guesses worth an explicit Alias_Map row (e.g. "cocoa oil" → cocoa +2 on KIND Raspberry Cocoa Crisp and Vilgain Hazelnut Cream; "chia seed protein" → chia seed; "sorghum extract" → sorghum). None change a v2 guide's qualification today. Worth a schema pass next month.

### Grade bands (current)
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

To rescore: upload the new bar Excel + the current schema file and say "run score_and_export."

---

## Current site features (index.html + app.js)

### Filter panel
Lifestyle presets (Lose Weight, Clean Ingredients, Low Sugar, Most Protein Per Calorie, Keto Friendly, GLP-1 Friendly, No Sugar Alcohol, No Seed Oil) · Ingredient Quality Grade toggle (A-F) · Brand filter (searchable multi-select) · Flavor keyword search · Macro sliders (Protein min, Calories/Fat/Carbs/Sugars/Sugar Alcohol max, Fiber min, Net Carbs max) · Certifications (Vegan, GF, DF, SF, Non-GMO, Nut Free) · Exclude-ingredients text input (XSS-safe).

**Max sliders at the top of their range now mean "no limit" (fixed 2026-09-29).** Before, the default slider maxes (410 cal, 30g fat, 50g carbs, 29g sugar) silently hid every bar above them from every Bar Finder view. Among no-sugar-alcohol bars alone, that was 7 (4 Off the Farm bars, 2 Bobo's Stuffd Oatmeal, Possible Chocolate Almond), so the guide said 968 while the Bar Finder showed 961.

### Preset deep links — VALID SLUGS ONLY
Brand/guide pages link to `/bar-finder?preset=SLUG` (**confirmed 2026-09-17: the extensionless form, not `/bar-finder.html?preset=SLUG` — the hardcoded-`.html`-link cleanup that was flagged as still-pending has already shipped sitewide**). Only these slugs are defined in `app.js`'s `PRESETS` object — anything else silently does nothing:

| Slug | Label | Criteria |
|------|-------|----------|
| `lose_weight` | Lose Weight | 20g+ protein, under 200 cal, under 3g sugar, A/B grade |
| `clean` | Clean Ingredients | A grade, 12g+ protein, no artificial sweeteners or sugar alcohols. **Does NOT match the Clean Protein Bars guide** (83 bars vs 514; it also admits 2 Simply Protein bars with processed oil). Jeff wants it fixed; see Next. |
| `skip_sugar` | Low Sugar | Under 2g sugar, under 4g sugar alcohol, no maltitol/sorbitol, A/B grade |
| `high_protein` | Most Protein Per Calorie | Protein efficiency ranked, 15g+ protein, A/B/C grade |
| `keto` | Keto Friendly | Under 5g net carbs, 10g+ fat, A/B grade |
| `glp1` | GLP-1 Friendly | 15g+ protein, under 200 cal, under 4g sugar, 3g+ fiber, no sugar alcohols, A/B grade |
| `no_sugar_alcohol` | No Sugar Alcohol | No sugar alcohol (or IMO) in the ingredient list: `hasSugarAlcohol()`, the same screen as the No Sugar Alcohols guide (968 = 968, verified 2026-09-30) |
| `no_seed_oil` | No Seed Oil | No screened seed/vegetable oil in the ingredient text: `hasSeedOil()`, the same set as the No Seed Oils guide key for key (695 = 695, verified 2026-09-30; build_no_seed_oils.py and build_clean_protein_bars.py check it every build) |

**Never invent preset slugs.** If a guide topic doesn't map to one of these, link to `/bar-finder` unfiltered — or, if the guide's criteria matches an existing certification checkbox exactly, the real `?certs=Label` deep link support in app.js is a legitimate alternative, and `?excl=term` (substring match on the ingredient text) works when a single exclusion reproduces the guide's set exactly (verified: `?certs=GF` = 835 for gluten-free, `?excl=sucralose` = 1,060 for no-artificial-sweeteners, `?excl=erythritol` = 1,209). `?grade=A,B` is also supported, as are slider params (`protein`, `cal`, `fat`, `carbs`, `sugar`, `sa`, `fiber`, `netcarbs`; a slider skips bars with an empty field), and all params combine with AND: clean uses `?preset=no_seed_oil&grade=A,B&excl=sucralose` (514 = 514), diabetics uses `?grade=A,B&protein=10&sugar=5&fiber=5&netcarbs=10&excl=maltitol,polyglycitol,hydrogenated%20starch%20hydrolysate` (89 = 89). Verify the cert label string against app.js's `CERT_MAP` before using it — most keys are short forms (`GF`), but `Dairy Free`, `Soy Free`, and `Nut Free` are the multi-word labels whose keys are the full two-word label with a literal space (URL-encode as `%20`).

### Results table columns
BAR | CAL | PROT | P/100 | FAT | CARB | FIBR | SGR | SGR ALC | CERTS | GRADE | CMP (P/100 = protein g per 100 cal, sortable). Caffeine/Creatine/Vitamins boost badges render under the flavor name in the BAR cell when present.

### Bar expand
Macro rank grid, nutrition facts panel, ingredient quality score, certifications, ingredient list, similar bars, buy links.

---

## SEO structure

Every page has: unique title + meta description, canonical link, FAQPage JSON-LD, Article JSON-LD (brand/guide pages), Dataset JSON-LD, BreadcrumbList JSON-LD (brand pages), Open Graph tags, GA4 tracking. Meta description leads with a specific surprising data point, never a generic description, no em dashes. v2 guides: Article author is Person "Jeff Booth" (url /about), ItemList = the Best 10.

`llms.txt` documents the scoring system, database, brand reviews, and guides for AI crawlers — update it when adding new brand or guide pages. **See the inconsistent-bar-count note under its File structure entry above — it needs a fresh full spot-check, its last confirmed-accurate pass predates the 1,307-bar database, High Fiber, and Creatine.**

---

## What's working well
- Mobile experience (62% of traffic, last measured) — priority to maintain
- Brand review pages all built on TEMPLATE_BRAND.html; guide pages on the rev 8 TEMPLATE_GUIDE.html standard, except the thirteen v2 guides (no-sugar-alcohols, no-artificial-sweeteners, gluten-free, no-seed-oils, clean, diabetics, keto, glp1, vegan, dairy-free, soy-free, kosher, high-fiber)
- SEO schemas complete on all brand and guide pages
- Cloudflare cache headers configured via `_headers`

---

## Known issues / next priorities

*Per-page to-do status lives with Jeff, not here. What follows is durable, not a task list.*

**2026-09-30 High Fiber v2 (second session):**
- **Shipped: `high-fiber-protein-bars.html` on v2** (479KB → 127KB, FAQ at ~113KB). 103 qualify (11g+ fiber; 44 A/B). Slots: Highest fiber, Lowest net carbs, Best whey protein, Best plant-based; Most fiber per calorie fills the empty big-brand slot. 7 of 10 picks have an Amazon link. Bar Finder `?fiber=11` (103 = 103 headless, key for key); the tiers note has a `?fiber=5` button (613). "The Extreme Fiber 100" name kept as the tier's name.
- Built bars: all 13 have 0g fiber. Jeff confirmed this is accurate (2026-09-30); don't flag it again.
- Files changed: `high-fiber-protein-bars.html`, `build_high_fiber_protein_bars.py`. No lib, CSS or app.js changes; sitemap already 2026-09-30.
- QA: same full suite as the other v2 guides, all passing.

**2026-09-30 Kosher v2 (second session):**
- **Shipped: `kosher-protein-bars.html` on v2** (612KB → 130KB, FAQ at ~116KB). 154 qualify (69 A/B). Slots: Best whey protein, Lowest sugar, Best gluten-free, Best non-GMO; fallbacks Highest fiber, Lowest net carbs. Every Best 10 pick has an Amazon link; 9 of 10 are on no other guide. Bar Finder `?certs=Kosher` (154 = 154 headless, key for key). Head font link fixed; brand_qa.py passes on every page now.
- **Fro Pro follow-ups (Jeff):** Sweet Coconut's dairy free label is correct. It was already in `REVIEWED_OK` (kyb_guide_lib.py, 2026-09-24); the new dairy-free and soy-free v2 builders didn't use that list, so they flagged it again. Both now call `reviewed_ok()` (no page output changed). Cookies and Cream: Jeff removed its Soy Free label in the database, so its old `REVIEWED_OK` entry was removed. Database 43 applied this (soy-free 292 → 291).
- Files changed: `kosher-protein-bars.html`, `build_kosher_protein_bars.py`, `build_dairy_free_protein_bars.py`, `build_soy_free_protein_bars.py`, `kyb_guide_lib.py` (one REVIEWED_OK line). Every other builder still reproduces its page; no CSS or app.js changes; sitemap already 2026-09-30.
- QA: same full suite as the other v2 guides, all passing.

**2026-09-30 CLIF link + Soy Free v2 (second session):**
- Vegan: the "Are CLIF Bars vegan?" FAQ now cites Clif's own page (https://www.clifbar.com/stories/are-clif-bar-energy-bars-vegan-our-philosophy, Jeff supplied it; checked: "may be made in a bakery that uses dairy-based ingredients", Clif says "plant-based"). Copy says "dairy-based" to match. Inline citation link in the FAQ answer only (new tab, no affiliate tag); the big-brands verdict states the reason without a link.
- **Shipped: `soy-free-protein-bars.html` on v2** (969KB → 129KB, FAQ at ~114KB). 292 qualify. Slots: Best dairy-free, Best gluten-free, Best plant-based, Best non-GMO; fallbacks Best whey protein, Highest fiber. 8 of 10 picks have an Amazon or referral link; 5 are new to the guides. Bar Finder `?certs=Soy%20Free` (292 = 292 headless, key for key). Its head's font link was fixed (brand_qa.py now fails only on kosher).
- Data note: Fro Pro Cookies and Cream (soy free label + soy lecithin): Jeff removed the label in the database; see Kosher v2 above.
- Files changed: `vegan-protein-bars.html`, `build_vegan_protein_bars.py`, `soy-free-protein-bars.html`, `build_soy_free_protein_bars.py`. No lib, CSS or app.js changes; sitemap already 2026-09-30.
- QA: same full suite as the other v2 guides, all passing (three identical rebuilds, headless count, 1280/390/360 screenshots).

**2026-09-30 Database 42 + Dairy Free v2 (second session):**
- **Database 42:** the only change from 41 is Aloha's 18 bars marked vegan (Jeff, after the vegan migration flagged them). Pipeline run as usual (score_and_export.py + schema v12; same grade mix). Note: `diff_bars_upload.py` reported "no changes" because it doesn't compare the certification fields; a direct field diff showed the 18 Vegan changes. Pages changed beyond dates and shipped: vegan (263 → 281), dairy-free, soy-free and caffeine (Vegan cert badges in rows), all-protein-bar-brands (a cert badge), gluten-free (its Vegan related-card count), llms.txt (vegan count/share, brand count). Date-only rebuilds not shipped. sitemap: caffeine lastmod → 2026-09-30 by hand (the others were already 2026-09-30).
- **CLIF Bar on the vegan guide (Jeff):** Clif doesn't call its bars vegan because they may be made in bakeries that also use animal-based ingredients. The big-brands verdict says that, and a new FAQ "Are CLIF Bars vegan?" answers it. Screen unchanged (label-based).
- **Shipped: `dairy-free-protein-bars.html` on v2** (843KB → 129KB, FAQ at ~114KB). 247 qualify. Slots (no approval round): Best soy-free, Best non-GMO, Best gluten-free, Highest fiber; fallbacks Lowest sugar, Lowest net carbs. Bar Finder `?certs=Dairy%20Free` (247 = 247 headless, key for key). `build_dairy_free_protein_bars.py` is now a standalone v2 builder (no longer uses kyb_cert_guide; soy-free and kosher still do).
- **Data items:** (1) Fro Pro Sweet Coconut lists sodium caseinate but Jeff confirmed the dairy free label (already in REVIEWED_OK; see Kosher v2 above). (2) 177 vegan-labeled bars (NuGo, GoMacro, Lenny & Larry's, Bearded Bros, The Feel Bar, ...) have no dairy free label. The page explains this and points to the vegan guide; if Jeff wants them counted as dairy free, mark them in the database.
- Files changed: `bars.js`, `llms.txt`, `sitemap.xml`, `vegan-protein-bars.html` + `build_vegan_protein_bars.py`, `dairy-free-protein-bars.html` + `build_dairy_free_protein_bars.py`, `soy-free-protein-bars.html`, `caffeine-protein-bars.html`, `gluten-free-protein-bars.html`, `all-protein-bar-brands.html`. No lib, CSS or app.js changes.
- QA: full suite on vegan and dairy-free (sizes, FAQ offsets, 5 schema types, FAQ JSON-LD word for word, no score/visible date, tags balanced, inline scripts pass `node --check`, headless count match key for key, screenshots at 1280/390/360 with no sideways scroll, rows expand, "Show less" at the end, FAQ opens, three identical rebuilds); broken-link scan clean repo-wide; QA.md section 1 shows no new failures; div balance on the data-refreshed v1 pages; every builder rebuilt on database 42.

**2026-09-30 Vegan v2 (second session, same zip and database):**
- **Shipped: `vegan-protein-bars.html` on v2** (889KB → 130KB, FAQ at ~116KB). 263 qualify. Slots (no approval round): Highest fiber, Best gluten-free, Best soy-free, Lowest net carbs; fallbacks Best non-GMO, Lowest sugar. 8 of 10 picks have an Amazon link. Bar Finder `?certs=Vegan` (263 = 263 headless, key for key). Picks in `claude/GUIDE_PAGE_SPEC_V2.md`.
- Editorial fixes: a v1 finding printed average ingredient scores (grades only now); the "reflects the database as of [date]" FAQ sentence dropped; "full ranked list in the table below" and the OG "ranked by ingredient quality score" removed; the hero rewritten. The seven animal-ingredient cards kept (v2 count cards).
- Data note: Aloha (18 bars) had a blank Vegan field; fixed in database 42 (see above). CLIF Bar handled in copy (see above).
- Files changed: `vegan-protein-bars.html`, `build_vegan_protein_bars.py`. No lib, CSS or app.js changes. sitemap.xml already 2026-09-30.
- QA: full suite passing (130KB, FAQ ~116KB, 5 schema types, FAQ JSON-LD word for word, no score or visible date, tags balanced, inline scripts pass `node --check`, broken-link scan clean repo-wide, screenshots at 1280/390/360 reviewed with no sideways scroll, rows expand, "Show less" at the end, FAQ opens, H1/H2 aligned, three identical rebuilds).

**2026-09-30 GLP-1 v2 (second session, same zip and database):**
- **Shipped: `glp1-protein-bars.html` on v2** (249KB → 91KB, FAQ at ~76KB). 21 qualify (3 A, 18 B), so the list section shows all 21. Slots (picked without an approval round, per Jeff): Best whey protein, Highest fiber, Lowest sugar, Best plant-based; fallbacks Lowest net carbs, Best gluten-free. Bar Finder `?preset=glp1` (21 = 21 headless, key for key). Picks in `claude/GUIDE_PAGE_SPEC_V2.md`.
- Editorial fixes: the "narrowest brand spread of any guide" idea is no longer true (creatine has fewer brands and fewer bars), so neither the hero nor the findings claim it; brand-table FAQ dropped; "table above/below" references removed; NuGo (2/31) and Promix (1/13) FAQs said "Mixed" and now say "Only …" with the flavor names; "score an A" → "earn an A"; "189.8 calories" → 190; title; standard disclaimer. New: "What is the best protein bar for GLP-1?" FAQ and a findings line that 140 bars meet the four macro checks but most of those have a sugar alcohol or a C-or-below grade.
- Files changed: `glp1-protein-bars.html`, `build_glp1_protein_bars.py`. No lib, CSS or app.js changes (so every other page is unaffected). sitemap.xml already 2026-09-30.
- QA: full suite passing (91KB, FAQ ~76KB, 5 schema types, FAQ JSON-LD word for word, no score or visible date, tags balanced, inline scripts pass `node --check`, broken-link scan clean repo-wide, screenshots at 1280/390/360 reviewed with no sideways scroll, rows expand, "Show less" at the end, FAQ opens, H1/H2 aligned, three identical rebuilds).

**2026-09-30 Keto v2 (second session, same zip and database as diabetics below):**
- **Shipped: `keto-protein-bars.html` on v2** (474KB → 134KB, FAQ at ~118KB). 104 qualify (64 A/B; keto has no grade gate, so 40 grade C or below, which the page now says; the Best 10 and Top 50 use only A/B). Guide slots (Jeff: "just pick the best ones"): Lowest net carbs, Best whey protein, Highest fiber, Best dairy-free; fallbacks Best soy-free, Best gluten-free. 7 of the 10 picks have an Amazon link. Picks in `claude/GUIDE_PAGE_SPEC_V2.md`.
- **Bar Finder button (Jeff: option b):** no exact link exists because the Bar Finder has no minimum-fat slider. The button is "Open 170 low-carb bars in the Bar Finder" (`?protein=10&netcarbs=8&excl=maltitol,polyglycitol,hydrogenated%20starch%20hydrolysate&sort=fat:desc`) and the note says it includes 66 bars under 8g fat, sorted so the 104 keto bars come first. Verified headless (170, key for key; first 104 rows have 8g+ fat). A Min Fat slider is parked for a later session.
- ItemList schema added (same one-time marker insert as diabetics). Editorial fixes: brand-table FAQ dropped, "table above/below" references removed, the Quest FAQ ("Mixed ... 6 of 16") now says the rest miss on fat and all 6 grade C or below, "score an A" → "earn an A", the grade FAQ no longer calls grade "extra context", the title lost "Ranked by Ingredient Quality", the disclaimer uses the standard wording. New: "Keto doesn't screen on ingredient grade" note, IMO note (9 Daryl's bars, picks #1 and #3), "What is the best keto protein bar?" FAQ.
- Files changed: `keto-protein-bars.html`, `build_keto_protein_bars.py` (rewritten as a v2 builder), `kyb_guide_lib.py` (`KT_COLS['fat']`, one line). sitemap.xml already 2026-09-30. No CSS or app.js changes.
- QA: same suite as diabetics below, all passing (134KB, FAQ ~118KB, 5 schema types, FAQ JSON-LD word for word, no score or visible date, tags balanced, inline scripts pass `node --check`, broken-link scan clean, screenshots at 1280/390/360 reviewed with no sideways scroll, rows expand, "Show less" at the end, three identical rebuilds; every other builder, including diabetics and the five other v2 guides, reproduces its page apart from dates).
- Note: "Brands that do it well" includes Atkins (C/D grades) because the locked rule needs 2+ big brands and only IQ Bar, Atkins and Quest have keto bars.

**2026-09-30 Diabetics v2 (second session, worked from knowyourbar-main_50.zip, database 41):**
- **Shipped: `best-bars-for-diabetics.html` on v2** (456KB → 134KB, FAQ at ~118KB). 89 qualify (18 A, 71 B). Guide slots (Jeff): Lowest net carbs, Lowest sugar (no sugar alcohol), Best whey protein, Best soy-free; fallbacks Best gluten-free, Highest fiber. None of the four guide picks repeats a pick from the other five v2 guides. Bar Finder `?grade=A,B&protein=10&sugar=5&fiber=5&netcarbs=10&excl=maltitol,polyglycitol,hydrogenated%20starch%20hydrolysate` (89 = 89 headless, key for key; no preset/certs/excl/grade combination matches without slider params). Picks, ties and decisions in `claude/GUIDE_PAGE_SPEC_V2.md`.
- **ItemList schema added.** The v1 head had no ItemList region; `build_best_bars_for_diabetics.py` inserts the `kyb:jsonld-itemlist` marker once after the FAQPage region (`ensure_itemlist_marker()`, literal and idempotent). Reuse it for keto and glp1.
- **Decisions (Jeff):** keep Quest Oatmeal Chocolate Chip as Most protein per calorie (B grade, sucralose + erythritol, the only qualifying bar with an artificial sweetener); no HOLD on Daryl's Cinnamon Bun (A with sugar and palm kernel oil in its yogurt coating); add an IMO note rather than change the screen (7 of 89 qualifying bars, 3 Best 10 picks, count IMO as fiber). Disclaimer uses "dietitians".
- **Editorial fixes** (things no longer true on the site): the FAQ comparing "the brand table below" to "the ranked bar list above" (dropped); "check the flavor table above" in the IQ Bar and Quest FAQs and "check the brand table below" in the hero (removed); the Quest FAQ said "Mixed by our screen: 1 of 16 ... clear" (now "Only 1 of 16 ... clears: Oatmeal Chocolate Chip", the rest miss on grade); "can score an A" → "earn an A"; the title "Ranked by Ingredient Quality" → "10 Best Protein Bars for Diabetics (1,000+ Checked)"; the v1 Bar Finder button opened the unfiltered Bar Finder while claiming "not just the 89"; the old disclaimer wording ("dietitians ... we see people managing diabetes look for, so that is what we filtered on"). New FAQ: "What is the best protein bar for diabetics?". No visible dates; the page never referenced Low Sugar + High Protein in its own copy (only the shared nav/footer).
- **Lib (append-only, defaults unchanged):** `KT_COLS['netcarbs']` and optional `cols` / `hide_mobile` on `top50_html()`. The diabetics Top 50 adds Net carbs and hides Sugar, Calories and Fiber on phones (five numeric columns overflowed at 360px).
- Files changed: `best-bars-for-diabetics.html`, `build_best_bars_for_diabetics.py` (rewritten as a v2 builder), `kyb_guide_lib.py`. sitemap.xml already had 2026-09-30 for this URL. llms.txt unchanged (its rebuild reproduced the live file). No CSS or app.js changes.
- QA: full QA.md suite incl. 1b (134KB, FAQ at ~118KB, 5 schema types, FAQPage JSON-LD = visible FAQ word for word, no score, no visible date); section 1 script shows no new failures (pre-existing: TEMPLATE_*.html / index.html / scan.html em dashes, kyb_scatter_interactive.html exemptions); broken-link scan clean repo-wide; div/section/table/tr/a/p/ul/li balance; all three inline scripts pass `node --check`; IQ Bar numbers cross-checked with `verify_brand_data.py`; Bar Finder 89 = 89 headless and key for key; screenshots at 1280, 390 and 360px reviewed with no sideways scroll (page and every `.kt-wrap`), rows expand from bars.js with a grade and no score, "Show less" at the end of lists, FAQ opens, H1 and H2 share a left edge; the page rebuilt three times with identical output; every other builder reproduces its live page with only dates changing (10 date-only pages not shipped; the five other v2 guides are byte-identical). Pre-existing: brand_qa.py font imports on kosher and soy-free.
- **Flagged, not changed:** the lib's "Best from a big brand" card says "a brand you can find in most grocery stores", which doesn't fit Kirkland (Costco only); shows on gluten-free and diabetics. The diabetics head still carries its unused v1 `.diab-*` inline style block.

**2026-09-30 Clean v2 + tiebreak (worked from knowyourbar-main_49.zip, databases 40 and 41):**
- **Database:** database 40 reproduced the live bars.js byte for byte. Database 41 changed only Jacked Granny Chocolate and PB and J (new formula: sugar, fiber, fat, carbs; grades unchanged). bars.js regenerated through the normal pipeline. Because macro ranks and brand averages include those two bars, 18 generated pages changed beyond dates (all five v2 guides including clean, keto, diabetics, glp1, vegan, dairy-free, soy-free, kosher, high-fiber, the four brand reviews other than Quest, all-protein-bar-brands) plus llms.txt (High Fiber 5g+ count 612 → 613). Pages whose rebuild only changed a date were not shipped.
- **Shipped: `clean-protein-bars.html` on v2** (1.47MB → 125KB, FAQ at ~111KB; it was the last page over 1MB besides the exempt scatter page). 514 qualify. Guide slots (Jeff, after two rounds): Best whey protein, Lowest net carbs, Best non-GMO, Best soy-free; fallbacks Best dairy-free, Highest fiber. None of the four guide picks repeats another guide's pick. Bar Finder `?preset=no_seed_oil&grade=A,B&excl=sucralose` (514 = 514, key for key). Picks in `claude/GUIDE_PAGE_SPEC_V2.md`.
- **Editorial fixes on clean** (things no longer true in bars.js / the site): the erythritol FAQ said "neutral-to-minor concern" (the schema scores it as a real concern; 7 erythritol bars still grade B and qualify); the protein-sources FAQ said whey isolate scores below concentrate and collagen is a concern (whey isolate ties egg whites at the top; collagen is the weakest positive); the v1 CTA pointed at `preset=clean` (83 bars, not 514); the "Low Sugar + High Protein" reference was removed; FAQ references to "the table below" / "Mixed Lineups table above" / "reflects September 2026" dropped; "ingredient score" → "ingredient grade". New: a "What clean doesn't cover" note and FAQ (17 clean bars contain a sugar alcohol; the Clean Ingredients preset is stricter).
- **Shipped: buy-link tiebreak + per-guide shuffle** in kyb_guide_lib.py (`buy_rank()`, `set_tie_seed()`, `tie_shuffle()`, new `tie_chain()`, `_tie_context()` wording, and the "How we picked these" rules now say plainly that a buy link can break an exact tie). All five v2 builders call `set_tie_seed(<slug>)`. Pick changes on the earlier guides, all approved: Gryp Rocky Road replaces Ration as Most protein per calorie on no-sugar-alcohols, no-artificial-sweeteners and no-seed-oils (referral link, same 14.7g/100 cal); Fello Everything Bagel no longer appears on any guide (its identical twins Spicy Pizza / Zesty BBQ rotate in); Tilt Vanilla Almond on no-seed-oils; The Feel Bar Mint Chocolate Chip on gluten-free. Big-brand "Best pick" examples and Top 50 tie order moved on several guides for the same reason. (Diabetics, later the same day, uses Fello Everything Bagel as its Lowest sugar pick.)
- Files changed: `bars.js`, `kyb_guide_lib.py`, `build_clean_protein_bars.py` (rewritten as a v2 builder), the four other v2 builders (one `set_tie_seed` line each), `clean-protein-bars.html`, the 17 other data-changed pages, `llms.txt`, `sitemap.xml` (18 lastmods → 2026-09-30: 17 via update_sitemap_lastmod.py, all-protein-bar-brands by hand since it carries no date stamp). No CSS or app.js changes.
- QA: full QA.md suite incl. 1b on all five v2 guides; FAQPage JSON-LD = visible FAQ word for word; no score, no visible date; broken-link scan clean repo-wide; clean div/section/table/tr/a/p balance; every inline script on the five v2 guides passes `node --check`; all five Bar Finder counts matched headless; clean screenshots at 1280, 390 and 360px with no sideways scroll, rows expand from bars.js, "Show less" at the end of lists, FAQ opens, H1 and H2 share a left edge; every page rebuilt twice with identical output; the builders not touched in this session reproduce their live pages (dates aside). Pre-existing QA failures untouched: brand_qa.py font imports on kosher and soy-free.
- Data notes found along the way (fix in the database, not here): Tilt Vanilla Almond's Website URL points at the Chocolate Sea Salt product page; Jacked Granny PB and J lists peanuts first with 2g fat (Jeff confirmed the label).

**Next (in priority order):**
1. **Fix the Clean Ingredients preset** (Jeff asked): redefine `PRESETS.clean` in app.js to match the clean guide (A or B grade, no artificial sweeteners, no seed oils via `hasSeedOil()`), then update every page whose link label describes the old behavior (ingredient_scoring "Browse A-Grade bars", quest-vs-rxbar "A-grade bars only", the homepage FAQ via build_index.py, KIND/RXBAR/Clif/Barebells/Quest discover links, ingredient-report, build_brand_rankings.py, and the "stricter filter" buttons on no-artificial-sweeteners and clean). Then clean's Bar Finder button can use `?preset=clean`. One sitewide session with Jeff's sign-off.
2. **About page copy:** "commissions never change a rank" / "Commissions never affect a grade or a rank" is no longer strictly true with the buy-link tiebreak. Jeff is rewriting About himself.
3. Migrate the next guide to v2 (caffeine, creatine). kyb_cert_guide.py has no users left (keep it until Jeff decides to delete it).
3a. **v2 rollout is done** (caffeine and creatine shipped 2026-09-30). Small guides: `criteria_html(n_spots=)` and `build_guide_page_v2(n_picks=)` in kyb_guide_lib.py (default 10). Their Bar Finder buttons open the plain Bar Finder because it has no caffeine or creatine filter; a "Has caffeine / Has creatine" toggle is parked. Data questions for Jeff: Real Food Bar Espresso Chip lists 65mg caffeine with no coffee or caffeine ingredient; JiMMYBAR! Double Fudge Brownie's ingredient text has an unclosed parenthesis. llms.txt's creatine line now describes the v2 page (build_llms_txt.py).
3b. **Min Fat slider** in the Bar Finder (parked by Jeff): then switch keto's button to an exact 104-bar link.
4. Ask Jeff about the "Best from a big brand" card wording for Kirkland ("most grocery stores" vs Costco); a lib change touches gluten-free and diabetics.
5. Add the About link to the shared footer on every other page (hand-edit or a careful propagation, never a regex across pages), and add /about + the byline to llms.txt via build_llms_txt.py. While there, change llms.txt's "Full list:" wording for the v2 guides.
6. Watch GSC and GA4 for the fifteen v2 guides over 3–4 weeks (titles are now "10 Best ... (1,000+ Checked)"; buy_click placements are top_picks, table_row, expanded_row). no-sugar-alcohols went live first, so compare it against the others. Diabetics' old title carried the count ("89 Passed"); watch its CTR after the change.
7. Schema pass on the audit items above; consider an "Organic (Y/N)" (certified) field in the database.
8. Later from the search-demand analysis: a weight-loss guide (top preset), FODMAP/low-bloat, nut-free; the dietitian review on diabetes/GLP-1 (parked).

**2026-09-29 Guide v2 rollout (second session, worked from knowyourbar-main_48.zip):**
- Shipped on v2, each with its 4 guide slots, picks and Bar Finder link approved by Jeff before the build (all locked in `claude/GUIDE_PAGE_SPEC_V2.md`):
  - `no-artificial-sweeteners.html`: 2.93MB → 131KB, FAQ at ~115KB. 1,060 qualify. Slots: stevia/monk fruit only, lowest sugar (no sugar alcohol), plant-based, highest fiber. Bar Finder `?excl=sucralose` (1,060 = 1,060).
  - `gluten-free-protein-bars.html`: 2.39MB → 122KB, FAQ at ~108KB (was past 2MB, never seen by Google). 835 qualify. Slots: lowest sugar (no sugar alcohol), plant-based, highest fiber, oat-free. Bar Finder `?certs=GF` (835 = 835). A HOLD on Pure Protein Cookies and Cream (suspect A) was added, then emptied once scoring v13 graded it C.
  - `no-seed-oils.html`: 1.96MB → 132KB, FAQ at ~115KB. 695 qualify. Slots: no added oil at all, lowest sugar (no sugar alcohol), date-sweetened, snack size. Bar Finder `?preset=no_seed_oil` (695 = 695, and key for key).
- Editorial carried over and trimmed. Fixed along the way: a v1 claim that the Clean Ingredients preset only removes artificial sweeteners and sugar alcohols (it also requires A grade and 12g+ protein); FAQ answers pointing to "the full ranked list below"; inline Bar Finder links in FAQ/paragraphs (now buttons); "ranked by ingredient quality score" in OG copy; the "database as of [date]" FAQ sentence on gluten-free and no-seed-oils. The #no-sucralose and #brand-seed-oil-check anchors were kept. The build's own claim check stopped a new hero line ("palm kernel oil usually hides in the coating", true for only 98 of 429 bars), which was removed.
- Files changed: `no-artificial-sweeteners.html`, `gluten-free-protein-bars.html`, `no-seed-oils.html`, their three `build_*.py` scripts (now v2 builders), `kyb_guide_lib.py` (append-only: shared v2 helpers after the v2 section; the pilot and every v1 builder still reproduce their live pages, dates aside, and no-sugar-alcohols rebuilds byte-identical), `sitemap.xml` (three lastmods → 2026-09-29). No CSS or JS changes.
- **Then, same session, scoring v13** (see Scoring pipeline): `score_and_export.py` changed, bars.js regenerated from `KYB - New Protein Bar Database 2026 39.xlsx`, and every generated page rebuilt (all builders pass their claim checks; a second rebuild is byte-identical). Also changed: `kyb_guide_lib.py` (Best 10 brand cap 3 → 2, Lowest calorie ranks grade first, `_why_honest()` scopes a card's superlative when a higher-ranked bar was skipped, no "wins the tie on name" in the pilot's lowest-sugar card), `build_ingredient_scoring.py` + `build_llms_txt.py` (methodology copy for the new rules), `build_quest_bars.py` (singular/plural copy when one flavor grades B), the two sweetener guides' grade-share checks (now "never falls, F above A"), and `sitemap.xml` (lastmods refreshed). no-sugar-alcohols.html changes too (new picks), so it must be re-uploaded.
- QA: full QA.md suite incl. 1b on all three (sizes, FAQ/footer offsets, 5 schema types, FAQPage JSON-LD = visible FAQ word for word, no score printed, no visible date); broken-link scan clean repo-wide; div/section/table balance; inline scripts pass `node --check`; every Bar Finder button count matched headless; screenshots at 1280, 390 and 360px with no sideways scroll, rows expand from bars.js, "Show less" at the end of lists; each page rebuilt twice with identical output. Pre-existing QA failures untouched: TEMPLATE_*.html / index.html / scan.html em dashes, kyb_scatter_interactive.html exemptions, and the brand_qa.py font imports on kosher and soy-free.

**2026-09-29 Guide v2 pilot (worked from knowyourbar-main_46.zip):**
- Shipped: `no-sugar-alcohols.html` rebuilt on the v2 "Best 10" layout (2.71MB → 153KB after the QA pass). Every decision is locked in `claude/GUIDE_PAGE_SPEC_V2.md`, including the Best overall formula, the grades-only rule, the no-repeat rule, the 300-calorie cap on Highest protein, the dropped "Easiest to find" slot, and the no-sugar-alcohols slots (lowest sugar, allulose, date-sweetened, plant-based at 15g+).
- Shipped: `about.html` + the byline on v2 guides + Person author schema; `/about` added to sitemap.xml.
- Shipped: `app.js` fix so max sliders at the top of their range don't hide bars (see Filter panel). The no_sugar_alcohol deep link now shows 968, matching the guide. The v1 CTA on this page pointed at `skip_sugar`, a different screen. The v2 CTA uses `no_sugar_alcohol`.
- Shipped: `qa_page_weight.py` + QA.md section 1b (size < 400KB, FAQ/footer inside 300KB, Bar Finder count match).
- Files changed: `no-sugar-alcohols.html`, `build_no_sugar_alcohols.py`, `kyb_guide_lib.py` (v2 section appended; v1 builders re-run and still reproduce their live pages exactly, dates aside), `style.css` (appended blocks only: v2 styles + guide hero alignment), `app.js` (slider-at-max guard + net-carb full subtraction in applyFilters), `about.html` (new), `qa_page_weight.py` (new), `QA.md`, `GUIDE_CRITERIA.md` (v2 supersede note on Top Picks Selection), `sitemap.xml` (no-sugar-alcohols lastmod + /about).

**2026-09-28 UI pass (worked from knowyourbar-main_43.zip):**
- Shipped: sitewide buy-button restyle, Top Picks alignment, mobile table fixes (see "2026-09-28 UI pass" under CSS architecture). Files changed: `style.css` (appended block only, first 104,882 bytes byte-identical to before), `index.html` (inline `.top-bar-buy` rules only), `no-sugar-alcohols.html` + `build_no_sugar_alcohols.py`, `sitemap.xml` (no-sugar-alcohols lastmod only).
- `no-sugar-alcohols.html`: every exact total-database count ("1,308", 15 spots across title/meta/OG/hero/findings/FAQ + JSON-LD) now reads "1,000+", and `build_no_sugar_alcohols.py` writes "1,000+" instead of `{comma(NT)}` (10 spots) so a rebuild keeps it. Rebuilt output matched the hand edit exactly apart from dates. FAQ visible text and FAQPage JSON-LD verified word for word.
- **"1,000+" rule applied sitewide (2026-09-28, second pass).** Jeff confirmed the rule stands. `kyb_guide_lib.py` now has `DB_PUBLIC = '1,000+'` and `of_db(n, total, the=False)`, which renders "613 of 1,000+" / "613 of the 1,000+", and switches to a share ("92% of 1,000+") when n itself is 1,000 or more, since "1,205 of 1,000+" reads wrong. Every builder that printed the total database size now uses these instead of `{comma(NT)}` / `{comma(N)}` / `{TOTAL}` / `{comma(total)}`: all guide builders, `kyb_cert_guide.py`, build_index, build_all_ingredients, build_ingredient_report, build_ingredient_scoring, build_flavor_map, build_brand_quadrant, build_llms_txt. All 20 affected pages + llms.txt were rebuilt from the patched scripts; the word-level diff against the pre-change pages was only count swaps (plus one dropped "(1,060 of 1,308)" parenthetical on the homepage and one duplicated percent on vegan). Four static "The Bar Finder covers all 1,307+/1,308+ bars" lines (outside kyb markers, not regenerated) were fixed by hand. **Deliberately left exact:** percentages and every sub-count (those are computed from the real total), "1,300+"/"1,335 canonical ingredients" (ingredient count, not bar count), and the "#770 of 1308" macro-rank tags in expand rows (a rank needs its real denominator). **New copy rule:** never write `{comma(NT)}` or a raw total in public copy; use `{DB_PUBLIC}` or `{of_db(x, NT)}`.
- Before this pass, every builder reproduced its live page exactly (checked by rebuilding all of them against the 43 zip and diffing, dates aside), so rebuilding from the scripts is safe right now. (Re-confirmed against the _48 zip on 2026-09-29, and the _49 and _50 zips on 2026-09-30.)
- sitemap.xml lastmods were refreshed with `update_sitemap_lastmod.py` in the second pass (25 URLs moved to their pages' real dates, quest-vs-rxbar back to 2026-09-23 since that's its actual date).
- `brand_qa.py` FAILED on two pages: `kosher-protein-bars.html` and `soy-free-protein-bars.html` imported 'IBM Plex Mono' and 'DM Mono' in their font `<link>`. Both fixed 2026-09-30 during their v2 migrations; brand_qa.py now passes on every page.

**Verified 2026-09-17, directly against the live site zip (knowyourbar-main_33.zip) — this replaces several items a prior version of this file had wrong or stale:**
- High Fiber and Creatine guide pages already exist and are live (see File structure above) — a prior session recommended building these as if they didn't exist. They did.
- The `/bar-finder.html?preset=` hardcoded-link cleanup already shipped sitewide — a prior session flagged this as a pending fix; it's done.
- Brand pages were genuinely touched within the last week (buy-button redesign, affiliate disclosure, RXBAR title change) even though a couple of pages' JSON-LD `dateModified` fields weren't bumped for that pass — don't use `dateModified` alone as a proxy for "last worked on."
- `scan.html` is now linked in nav sitewide and listed in sitemap.xml, despite an earlier status doc saying not to do that until iOS camera reliability was confirmed, and its "Take a photo instead" fallback (which a later pass was supposed to remove) is still present. **Needs Jeff's input:** is the camera issue actually resolved, and does the v3 scan.html rewrite still need to be applied to this repo?
- `llms.txt` has inconsistent bar-count references ("1,300" and "1,307" both appear) — needs a fresh full spot-check.
- Kosher and Soy Free guide pages shipped 2026-09-17 (soy-free-protein-bars.html, kosher-protein-bars.html) — nav/footer propagated sitewide, sitemap.xml and llms.txt updated. Nut Free and Non-GMO remain untouched certification-field candidates if Jeff wants the next two.
- **Found while building Soy Free 2026-09-17: the documented "Top Picks Selection" band-restriction rule in GUIDE_CRITERIA.md was never actually implemented in the live dairy-free-protein-bars.html, gluten-free-protein-bars.html, or high-fiber-protein-bars.html pages (or their build scripts) — all three still pick tiles 2-6 as a pure max/min with no band restriction, so a D or C grade bar can sit next to an A-grade "Best overall" tile on the same page. build_soy_free_protein_bars.py and build_kosher_protein_bars.py are the first to actually implement it. Worth a follow-up pass on the older guides. (The v2 migration replaces these tiles with the Best 10, which fixes this; gluten-free is fixed as of 2026-09-29.)

**Still open, not re-verified this session (carried over, treat as "probably still true" not "confirmed"):**
- Guide table completeness (the Mechanism A/B lazy-row bugs) — all guide pages were last confirmed clean as of late August; not re-checked against this zip.
- CSS/footer mobile stacking, nav/footer sync gaps on a handful of pages, the duplicate-ASIN issue in bars.js, KIND Minis/Thins not yet in the database.
- Future features under discussion: protein-type filter (whey/plant/egg), net-carbs column in the main table, more brand comparison pages, more brand reviews (Perfect Bar, GoMacro, ONE Bar, IQBar, Aloha, Built Bar), a dedicated bars-with-vitamins guide.

For the full historical narrative behind any of the above (why a rule exists, what a past incident looked like), search `claude/CHANGELOG.md` for the relevant term or date — don't read it end to end.

---

## Deploy process

1. Make changes in Claude
2. Run the QA script from QA.md — must pass before upload
3. Download files from Claude
4. Upload to GitHub repo (drag and drop to repo root)
5. Cloudflare Pages auto-deploys within ~60 seconds
6. Purge Cloudflare cache if changes aren't showing
7. Test with `?v=N` to bypass browser cache

**Rollback:** GitHub → file → History → find last working commit → download raw → re-upload.

---

## Session discipline — how to work with Claude efficiently

**Start every session:** upload this BRIEFING.md, upload the specific files you want to change (from GitHub), state exactly what you want changed.

**During session:** Claude works from uploaded files, not memory. Claude runs verification checks before presenting output files. Upload and verify before moving to the next change. **If Claude is asked "what's next" or to assess current state without files being uploaded, it should say so and ask for the current site zip rather than reasoning from this document's claims about what is or isn't built — this file has been caught stating things as current that were already done or already out of date.**

**Deliverables: only changed files, never a full-site zip**, unless a genuinely full copy is needed — ask first.

**Never:** ask Claude to change fonts/styles across all pages at once · let Claude use regex to modify HTML structure · upload files without seeing verification pass first · assume Claude remembers anything from a previous session — always upload BRIEFING.md · deliver a full-site zip when only some files changed.

---

*This briefing is the single source of truth for working on this project, but it is written by past sessions and it drifts — verify anything load-bearing against the actual uploaded files before asserting it as fact. `claude/CHANGELOG.md` is a break-glass file, not a companion read.*
