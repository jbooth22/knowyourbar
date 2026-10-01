# Guide Page Spec v2 — "Best 10" rebuild

Status: **LOCKED 2026-09-29.** Pilot shipped the same day: `no-sugar-alcohols.html`, built by `build_no_sugar_alcohols.py` with the v2 section of `kyb_guide_lib.py`. **Also on v2 (2026-09-29, second session): `no-artificial-sweeteners.html`, `gluten-free-protein-bars.html`, `no-seed-oils.html`. (2026-09-30): `clean-protein-bars.html`, `best-bars-for-diabetics.html`, `keto-protein-bars.html`, `glp1-protein-bars.html`, `vegan-protein-bars.html`, `dairy-free-protein-bars.html`, `soy-free-protein-bars.html`, `kosher-protein-bars.html`, `high-fiber-protein-bars.html`, then `caffeine-protein-bars.html` and `creatine-protein-bars.html`** (locked slots and picks below). Every guide is now on v2. Roll out the rest one guide per session through the same lib.
Background and data: `claude/SEARCH_DEMAND_ANALYSIS_2026-09.md`.

Everything marked **LOCKED** below was decided with Jeff. Don't change it without asking him.

## Why
- Guides convert 20–48% of landing sessions to buy clicks (brand pages ~1–3%). Guides are where the revenue comes from.
- The largest v1 guides were over Googlebot's 2MB HTML limit (no-artificial-sweeteners 2.93MB, gluten-free 2.39MB; no-sugar-alcohols 2.71MB). On gluten-free, the FAQ and footer started past 2MB, so Google never saw them. The thirteen migrated guides are now 91–154KB. After clean (1.47MB → 125KB), no page in the repo is over 1MB except the exempt standalone kyb_scatter_interactive.html. The heaviest v1 guide left is soy-free (969KB).
- About 90% of each v1 guide's text is the same bar panels repeated across 13+ guides.
- Page-one competitors are curated "best N" lists. The v1 pages led with "Ranking 968 bars."

## Hard targets — LOCKED
- HTML under **400,000 bytes** (hard ceiling 1MB). No `gd-bar-data` inline JSON blob. Nothing renders the full qualifying list.
- The FAQ section and the footer both start inside the **first 300,000 bytes**.
- Keep all existing schema: Article, Dataset, BreadcrumbList, FAQPage, ItemList. ItemList = the Best 10 (each item links to `#pick-N`). ItemList is now on every v2 guide (the lib always emits it). Diabetics, keto and glp1 had no ItemList region in their heads; each builder inserts the `kyb:jsonld-itemlist` marker once, after the FAQPage region (literal insert, idempotent). Copy `ensure_itemlist_marker()` from build_glp1_protein_bars.py for any later guide whose head lacks the region.
- Checked by `qa_page_weight.py` / `v2_qa()` (QA.md section 1b), and every v2 build refuses to write a page that fails.
- Results: no-sugar-alcohols 154KB (FAQ ~136KB), no-artificial-sweeteners 130KB (FAQ ~114KB), gluten-free 122KB (FAQ ~108KB), no-seed-oils 133KB (FAQ ~116KB), clean 125KB (FAQ ~111KB), diabetics 134KB (FAQ ~118KB; was 456KB), keto 134KB (FAQ ~118KB; was 474KB), glp1 91KB (FAQ ~76KB; was 249KB), vegan 131KB (FAQ ~116KB; was 889KB), dairy-free 129KB (FAQ ~114KB; was 843KB), soy-free 129KB (FAQ ~114KB; was 969KB), kosher 130KB (FAQ ~116KB; was 612KB), high-fiber 127KB (FAQ ~113KB; was 479KB), caffeine 109KB (FAQ ~95KB; was 290KB), creatine 68KB (FAQ ~54KB; was 124KB).

## The grades-only rule — LOCKED (Jeff, 2026-09-29)
- Ingredient quality is shown and ranked by **GRADE (A to F) only**. Two bars in the same grade are treated as equal. The scoring isn't precise enough to separate them, so we leave a margin for error.
- The raw ingredient score is **never printed** on a v2 page, not in the Best 10, the tables, the Top 50, or the tap-to-expand panel. `v2_qa()` fails the build if "Ingredient Quality Score", `score-number` or `data-score` appears.
- The raw score is never used to rank a pick or break a tie.
- **Tie chain inside a slot (updated 2026-09-30, Jeff):** better grade → **buy link** (the brand's own referral link, i.e. `Custom Referral Link` = Yes, first; then an Amazon link; then brand site only) → more protein → less sugar → more fiber → fewer calories → **per-guide shuffle** → brand/flavor name.
  - The buy-link step only decides between bars already tied on the slot's own number and on grade (`buy_rank()` in kyb_guide_lib.py). It never lifts a bar over one with a better grade or number. "How we picked these" says so.
  - The per-guide shuffle (`set_tie_seed(<slug>)` at the top of every v2 builder, `tie_shuffle()`): bars tied on every step (e.g. Fello Everything Bagel / Spicy Pizza / Zesty BBQ, identical macros) are ordered by a stable hash of (guide slug, bar key), so the same twin doesn't win on every guide by alphabet. Same result on every rebuild. Name stays the last step.
  - Card copy never says a bar "wins the tie on" buy link, shuffle or name: the card just says "tied for".

## Page anatomy (in order) — LOCKED, as built
1. **Hero** (revised after Jeff's live QA, 2026-09-29): H1 + two short paragraphs. The first defines the category (what these ingredients are, why people avoid them, what we screen for). The second gives the key numbers in plain prose (how many qualify, what share doesn't, the gotcha). No "best overall" verdict line, no big-number stat block, and NO byline in the hero. NO visible "updated" date anywhere on the page (including FAQ answers: the v1 "This page reflects the database as of [date]" sentence is dropped on migration). The v2 shell also removes the footer's "Updated YYYY-MM-DD" stamp and puts an About link there instead. `dateModified` stays in Article schema and only changes when the generated content changes: the build hashes the regions and keeps the old date if the hash matches, so a rebuild never bumps it artificially.
2. **Best 10**: numbered category-winner cards (`id="pick-1"` … `pick-10`, 2 columns on desktop, 1 on phones). Each card shows the bar, the grade badge, 4 guide-relevant macros, a 1–2 sentence data-backed "why it won," and buy buttons (Brand Site + Amazon, whichever exist). Under the heading: "How we picked these →" jumps to section 10. (Diabetics cards show Protein, Sugar, Net carbs, Fiber via `best10_html(macros=...)`.)
3. ~~Best 10 at a glance~~: **removed (Jeff, 2026-09-29).** It repeated the cards directly above it.
4. **What "[criterion]" actually means + the gotchas**: the original editorial, kept as-is where still true, trimmed where it repeats the new sections.
5. **What we found**: 3 data findings + 1 chart (share of bars failing the screen, by grade, one bar per grade in grade colors, each labeled with its value; for a certification guide, the share that carries the label). Diabetics charts the share with maltitol or a relative by grade, because its grade check would make a plain "fails the screen" chart read 100% for C, D and F.
6. **Brands that do it well**: rules below. Compact table: Brand · Qualify (19/19) · Grades · Avg protein · Avg sugar (of qualifying bars) · Why (grade mix, main sweetener where relevant, and the brand's best pick with grade, protein and calories). No "Big brand" chip.
7. **"How do the big brands fare on [criterion]?"**: every Big Brand in the DB, in 4 columns: Brand · Qualify (31/31 over 100%, one merged column) · Avg grade of its qualifying bars · Verdict. The verdict is computed from the data and says something useful: the main sweetener and the best pick when bars qualify, a "check the label" note when most grade C or lower, and the ingredient behind the misses ("None qualify: every flavor has erythritol"). "Only X of Y" only when fewer than half qualify. Links to brand review pages where they exist (Quest, RXBAR, CLIF Bar/Clif Builders, Barebells, KIND).
8. **Top 50**: compact rows (brand over flavor in one cell, grade, protein, calories, sugar, fiber, buy). Numbers centered. **Both buy links side by side, labeled "Amazon" and "Brand"**, whichever exist (never one picked at random). Order: best grade, then most protein per 100 calories, then the tie chain. The rows are in the HTML so they get indexed. Tapping a row loads the nutrition/ingredients panel from `/bars.js` on the first tap (grade only, no score). On phones the buy links sit under the flavor name, and Calories, Fiber and the Buy column are hidden. Any other short bar list on a v2 page uses the same table (`compact_bar_table_html()`). `top50_html()` takes optional `cols` / `hide_mobile` (2026-09-30; defaults unchanged). Diabetics adds a Net carbs column (`KT_COLS['netcarbs']`) and also hides Sugar on phones; with five columns the table scrolled sideways at 360px. Keto shows Net carbs and Fat (`KT_COLS['fat']`) and hides Fat, Calories and Fiber on phones.
9. **Big CTA: "See all [N] in the Bar Finder →"**: deep link that matches the guide exactly (preset, certs, excl, grade, slider params, or a combination). The count in the Bar Finder must equal N (QA.md 1b). Links in use: No Sugar Alcohols → `?preset=no_sugar_alcohol` (968); No Artificial Sweeteners → `?excl=sucralose` (1,060); Gluten Free → `?certs=GF` (835); No Seed Oils → `?preset=no_seed_oil` (695); Clean → `?preset=no_seed_oil&grade=A,B&excl=sucralose` (514); Diabetics → `?grade=A,B&protein=10&sugar=5&fiber=5&netcarbs=10&excl=maltitol,polyglycitol,hydrogenated%20starch%20hydrolysate` (89); GLP-1 → `?preset=glp1` (21; the preset is the same screen); Vegan → `?certs=Vegan` (281 on database 42); Dairy Free → `?certs=Dairy%20Free` (247); Soy Free → `?certs=Soy%20Free` (292); Kosher → `?certs=Kosher` (154); High Fiber → `?fiber=11` (103; the Min Fiber slider, and its in-section 5g button `?fiber=5` = 613). All verified in a headless browser (diabetics key for key, 2026-09-30). **Exception, keto (Jeff, 2026-09-30):** no link can match because the Bar Finder has no minimum-fat slider. The button opens the closest screen, `?protein=10&netcarbs=8&excl=maltitol,polyglycitol,hydrogenated%20starch%20hydrolysate&sort=fat:desc` (170 = the 104 keto bars + 66 with under 8g fat, sorted so the 8g+ bars come first), and the heading, button and note say exactly that ("Open 170 low-carb bars in the Bar Finder"). A Min Fat slider is parked for a later session; when it ships, switch keto to an exact link.
10. **How we picked these**: what qualifies, the rules for every pick (including the buy-link tiebreak, stated plainly), each slot's rule in plain English, plus links to the sitewide methodology and the About page.
11. **FAQ**
12. **Related guides** (3 cards)
13. **Author line**: one quiet line at the very bottom of the page, above the footer: "Know Your Bar is built by Jeff Booth. About us · How we rate bars." Article schema still names Jeff as the author.

### Page-wide conventions (Jeff's live QA, 2026-09-29) — LOCKED
- **Bar Finder links are big buttons, never inline text links** in a paragraph or FAQ answer. Each button has a one-line note saying what it opens (`section_cta_html()`). Examples: no-sugar-alcohols `/bar-finder?excl=erythritol` ("See all 1,209 erythritol-free bars"), no-artificial-sweeteners `/bar-finder?excl=sucralose` (1,060) and the Clean Ingredients preset button (on no-artificial-sweeteners and clean, described as what it is: A grade, 12g+ protein, no artificial sweeteners, no sugar alcohols).
- **"Found in" brand lists** collapse to "A, B, C, D and 25 more". Expanding shows the rest inline, with "Show less" at the END of the list (`more_list_html()`, `v2_count_card_html()`). Never the v1 `<details>` version, which left "Hide" stuck mid-list.
- **Data tables are compact** (`.kt-table`): header labels wrap, numbers are centered, text columns take the remaining width, and nothing scrolls sideways on a 360px phone (checked in a headless browser).

The v1 Snapshot strip, the Consider/Mixed/Avoid brand tables and the full bar table are gone on v2 pages (replaced by sections 6, 7 and 8).

## Best 10 rules — LOCKED
Structure: **6 core slots on every guide + 4 guide-specific slots**, plus a fallback list per guide.

Guardrails for every slot:
- Must qualify for the guide.
- Grade B or better.
- Protein ≥ 10g (15g for Best overall and Best plant-based).
- **No bar appears twice on one guide.** Repeats are allowed ACROSS guides, never within one (Jeff, 2026-09-29).
- **At most 2 slots per brand** across the 10 (`V2_BRAND_CAP`; Jeff, 2026-09-29, was 3: Fello took 3 identical-macro cards on gluten-free).
- If a slot has no eligible bar, the guide's next fallback slot takes its place, so the list is always 10.
- A guide builder may carry a **HOLD** set of bar keys (kept out of the Best 10 and Top 50 on that page while a suspect grade is rechecked upstream). Held bars still count as qualifying and stay in the Bar Finder, and the criteria section says one bar is held. Only with Jeff's approval.

### Core slots
1. **Best overall**: best grade present on the list, then most protein per 100 calories. 15g+ protein. *(Formula locked 2026-09-29. It replaces the proposed 50/50 percentile composite, because Jeff ruled out ranking on the raw score.)*
2. **Cleanest ingredients**: an A-grade bar (B if no A qualifies) with the **shortest ingredient list** (top-level ingredient count). Same-grade bars are treated as equal on ingredient quality, so the tiebreak is a label you can count.
3. **Highest protein**: most protein, grade ≥ B, **capped at 300 calories** so a large candy-style bar can't win on size alone. The card and the criteria section both say the cap and why.
4. **Most protein per calorie**: protein ≥ 12g, grade ≥ B.
5. **Lowest calorie**: **best grade first, then fewest calories** (Jeff, 2026-09-29: a B bar was winning on every guide when calories came first), protein ≥ 10g, grade ≥ B.
6. **Best from a big brand**: the Best overall rule, limited to the Big Brands list, 10g+ protein.

Heads-up: the same clean bars win several core slots on most free-from guides (Immortal Chocolate, Kize PB, Tilt, Gryp Rocky Road, RXBAR). That's allowed; pick the 4 guide slots with overlap in mind. Clean's, diabetics', keto's, glp1's, vegan's, dairy-free's, soy-free's, kosher's and high-fiber's four guide slots were chosen so none of their guide picks repeat a pick from the earlier v2 guides.

**Honest card copy (2026-09-29):** when a bar that ranks higher in a slot was skipped (already on the list, or its brand is at the cap), the card's superlative is scoped ("the fewest calories of any remaining A-grade bar") and names the higher bar (`_why_honest()` in kyb_guide_lib.py).

### Guide-specific slot menu
"Best [subset]" slots use the Best overall rule inside the subset.

Jeff's direction (2026-09-30): favor slots people actually shop on (protein type, net carbs, certifications) over narrow ones, and rotate the newer slots into the remaining guides to keep lists fresh. He called date-sweetened, snack size, allulose, stevia/monk fruit, egg-white protein and oat-free too narrow to be meaningful. They stay on the four guides already locked with them; don't propose them for new guides.

Preferred for new guides:
- **Best whey protein** (whey on the label) — protein type. Added 2026-09-30 (clean, diabetics, keto).
- **Lowest net carbs** (total carbs − fiber − sugar alcohol) — keto, diabetics, clean.
- **Best non-GMO** (Non-GMO (Y/N) = Yes; field holds only Yes or blank). Added 2026-09-30.
- **Best soy-free / Best dairy-free / Best gluten-free** (the certification fields). Added 2026-09-30.
- Lowest sugar (protein ≥ 10g, grade ≥ B). **On guides that don't already exclude sugar alcohols, use the tightened variant: only bars with no sugar alcohol** (otherwise a maltitol bar wins on a 0g sugar line).
- Highest fiber / most fiber per calorie (high-fiber, diabetics, GLP-1) — `slot_highest_fiber()`
- **Best plant-based**: Vegan (Y/N) = Yes, **15g+ protein** (falls back to 10g only if no plant-based bar reaches 15g)
- No added oil at all (no-seed-oils guide)
- Best caffeine dose by zone (caffeine guide)

Not for new guides: ~~Best allulose-sweetened~~, ~~Best stevia/monk fruit only~~, ~~Best date-sweetened~~, ~~Best snack size~~, ~~Best oat-free~~, ~~Best egg-white protein~~ (Jeff, 2026-09-30). ~~Easiest to find~~ was dropped 2026-09-29 (duplicates "Best from a big brand"). ~~Least fat~~ was considered and not used. ~~Best organic~~: not possible until the database has a certified-organic field (Jeff: organic only counts if certified).

### no-sugar-alcohols — LOCKED 2026-09-29 (picks refreshed 2026-09-30)
Guide slots: **Lowest sugar, Best allulose-sweetened, Best date-sweetened, Best plant-based.** Fallbacks: Highest fiber, then Best snack size.

The Best 10 on database 41 with the 2026-09-30 tie chain (968 qualifying, 384 eligible). Changes from 2026-09-29, all Jeff-approved: #4 Ration → Gryp (referral link breaks the 14.7g/100 cal tie), #7 Fello Everything Bagel → Spicy Pizza and #10 Spicy Pizza → Zesty BBQ (per-guide shuffle of identical-macro twins).

| # | Slot | Pick | Data |
|---|---|---|---|
| 1 | Best overall | Immortal Chocolate | A · 15g · 160 cal · 10g sugar |
| 2 | Cleanest ingredients | Kize Peanut Butter | A · 10g · 210 cal · 12g sugar |
| 3 | Highest protein | Tilt Chocolate Sea Salt | B · 28g · 240 cal · 2g sugar |
| 4 | Most protein per calorie | Gryp Rocky Road and Sea Salt | B · 25g · 170 cal · 1g sugar |
| 5 | Lowest calorie | Simply Protein Cocoa Raspberry | A · 12g · 140 cal · 2g sugar |
| 6 | Best from a big brand | RXBAR Blueberry | A · 12g · 180 cal · 15g sugar |
| 7 | Lowest sugar | Fello Spicy Pizza | A · 15g · 190 cal · 1g sugar |
| 8 | Best allulose-sweetened | Samsara Masala Peanut | A · 15g · 210 cal · 2g sugar |
| 9 | Best date-sweetened | CuraBar Chocolate Sea Salt | A · 18g · 230 cal · 11g sugar |
| 10 | Best plant-based | Fello Zesty BBQ | A · 15g · 190 cal · 1g sugar |

The picks are recomputed on every build, so a bars.js update can change them. The build prints the list, and a failed copy claim stops the build.

### no-artificial-sweeteners — LOCKED 2026-09-29 (picks refreshed 2026-09-30)
Guide slots: **Best stevia or monk fruit** (stevia or monk fruit is the ONLY sweetener added: no allulose, no sugar alcohol, no added sugar or syrup; fruit/dates in the recipe are fine), **Lowest sugar** (among bars that also have no sugar alcohol, so a maltitol bar can't win on 0g sugar), **Best plant-based** (15g+), **Highest fiber** (Jeff swapped it in for Best date-sweetened to cut overlap with no-sugar-alcohols). Fallbacks: Best allulose-sweetened, then Best snack size.
Why tightened: the literal "stevia/monk fruit on the label" rule picked Tilt Vanilla Almond (allulose-syrup bar, stevia/monk fruit are its last two ingredients), and the literal lowest-sugar rule picked think! Girl Scout Thin Mints (0g sugar, 8g maltitol syrup).
Bar Finder: **`/bar-finder?excl=sucralose`** (1,060 = 1,060). No preset matches; every artificial-sweetener bar contains sucralose, and the build checks the sets are identical key for key. The Clean Ingredients preset is linked as a button in "what it means" and described as what it is (A grade, 12g+ protein, no artificial sweeteners, no sugar alcohols).
Database 41 (1,060 qualifying, 424 eligible). Page ~130KB (was 2.93MB), FAQ at ~114KB. 2026-09-30 changes: #4 Ration → Gryp (referral link), #8 Fello Everything Bagel → Spicy Pizza (shuffle).

| # | Slot | Pick | Data |
|---|---|---|---|
| 1 | Best overall | Daryl's Bars Vanilla Pumpkin Spice | A · 22g · 226 cal · 4g sugar |
| 2 | Cleanest ingredients | Kize Peanut Butter | A · 10g · 210 cal · 12g sugar |
| 3 | Highest protein | Tilt Chocolate Sea Salt | B · 28g · 240 cal · 2g sugar |
| 4 | Most protein per calorie | Gryp Rocky Road and Sea Salt | B · 25g · 170 cal · 1g sugar |
| 5 | Lowest calorie | Simply Protein Cocoa Raspberry | A · 12g · 140 cal · 2g sugar |
| 6 | Best from a big brand | RXBAR Blueberry | A · 12g · 180 cal · 15g sugar |
| 7 | Best stevia or monk fruit | B.T.R. Nation Peanut Butter Crunch | A · 15g · 230 cal · 3g sugar |
| 8 | Lowest sugar | Fello Spicy Pizza | A · 15g · 190 cal · 1g sugar |
| 9 | Best plant-based | Immortal Chocolate | A · 15g · 160 cal · 10g sugar |
| 10 | Highest fiber | Julian Bakery Peanut Butter | B · 20g · 200 cal · 1g sugar |

Editorial kept: the four-sweetener cards, stevia/monk fruit and sugar-alcohol explainer, the #no-sucralose section (anchor kept, linked from no-sugar-alcohols; its v1 "top 10" table dropped as a repeat of the Best 10/Top 50; excl=sucralose button added). Findings: sucralose behind every flagged bar (ace-K only with it, no aspartame/saccharin), sucralose rarely a trace, share by grade (v13: A 0%, B 0%, C 19%, D 44%, F 63%).

### gluten-free-protein-bars — LOCKED 2026-09-29 (picks refreshed 2026-09-30)
Guide slots: **Lowest sugar** (no sugar alcohol), **Best plant-based** (15g+), **Highest fiber**, **Best oat-free** (no oats on the label; 225 gluten-free bars contain oats). Fallbacks: Best snack size, then Best date-sweetened.
Bar Finder: **`/bar-finder?certs=GF`** (835 = 835). Gluten Free field holds only "Yes" or blank (checked every build).
**HOLD list:** empty. `Pure Protein | Cookies and Cream` was held on 2026-09-29 (graded A, 10.8, with sucralose, erythritol and palm oils). Scoring v13 fixed the cause and it now grades C, so the hold was removed. The HOLD mechanism stays in the builder for future cases.
Database 41 (835 qualifying, 293 eligible). Page ~122KB (was 2.39MB), FAQ at ~108KB. 2026-09-30 changes (shuffle): #1 Fello Everything Bagel → Zesty BBQ, #8 The Feel Bar Brownie Chocolate Chip → Mint Chocolate Chip.

| # | Slot | Pick | Data |
|---|---|---|---|
| 1 | Best overall | Fello Zesty BBQ | A · 15g · 190 cal · 1g sugar |
| 2 | Cleanest ingredients | Kize Peanut Butter | A · 10g · 210 cal · 12g sugar |
| 3 | Highest protein | Gryp Rocky Road and Sea Salt | B · 25g · 170 cal · 1g sugar |
| 4 | Most protein per calorie | Gryp Strawberries and Cream | B · 25g · 180 cal · 5g sugar |
| 5 | Lowest calorie | Simply Protein Cocoa Raspberry | A · 12g · 140 cal · 2g sugar |
| 6 | Best from a big brand | Kirkland Chocolate Brownie | B · 21g · 190 cal · 2g sugar |
| 7 | Lowest sugar | Fello Spicy Pizza | A · 15g · 190 cal · 1g sugar |
| 8 | Best plant-based | The Feel Bar Mint Chocolate Chip | A · 15g · 200 cal · 7g sugar |
| 9 | Highest fiber | Julian Bakery Peanut Butter | B · 20g · 200 cal · 1g sugar |
| 10 | Best oat-free | CuraBar Chocolate Sea Salt | A · 18g · 230 cal · 11g sugar |

Editorial kept: "What disqualifies a bar" (wheat / barley-malt / not labeled cards) plus a new short "What about oats?" note. Findings: 395 of 473 unlabeled bars name no wheat or barley; wheat is the top named source; gluten-free bars grade A/B a little more often (v13: 54% vs 48%) but average less protein. Chart = share labeled gluten free by grade (v13: A 65, B 75, C 71, D 49, F 39). The "database as of [date]" FAQ sentence was dropped (visible date + dateModified churn).

### no-seed-oils — LOCKED 2026-09-29 (picks refreshed 2026-09-30)
Guide slots: **No added oil at all** (no oil, fat, shortening or MCT of any kind on the label; Best overall rule inside it), **Lowest sugar** (no sugar alcohol), **Best date-sweetened**, **Best snack size** (under 150 cal). Jeff picked date + snack over plant-based + fiber to cut overlap with no-artificial-sweeteners. Fallbacks: Best plant-based (15g+), then Highest fiber.
Bar Finder: **`/bar-finder?preset=no_seed_oil`** (695 = 695; the build ports app.js `hasSeedOil()` and checks the sets match key for key).
Database 41 (695 qualifying, 336 eligible). Page ~133KB (was 1.96MB), FAQ at ~116KB. 2026-09-30 changes: #3 Tilt Chocolate Sea Salt → Vanilla Almond (shuffle), #4 Ration → Gryp (referral link), #8 Fello Everything Bagel → Zesty BBQ (shuffle).

| # | Slot | Pick | Data |
|---|---|---|---|
| 1 | Best overall | Immortal Chocolate | A · 15g · 160 cal · 10g sugar |
| 2 | Cleanest ingredients | Kize Peanut Butter | A · 10g · 210 cal · 12g sugar |
| 3 | Highest protein | Tilt Vanilla Almond | B · 28g · 240 cal · 2g sugar |
| 4 | Most protein per calorie | Gryp Rocky Road and Sea Salt | B · 25g · 170 cal · 1g sugar |
| 5 | Lowest calorie | RXBAR Blueberry | A · 12g · 180 cal · 15g sugar |
| 6 | Best from a big brand | RXBAR Strawberry Strudel | A · 12g · 190 cal · 14g sugar |
| 7 | No added oil at all | full turn Vanilla Honey Crunch | A · 20g · 250 cal · 14g sugar |
| 8 | Lowest sugar | Fello Zesty BBQ | A · 15g · 190 cal · 1g sugar |
| 9 | Best date-sweetened | CuraBar Chocolate Sea Salt | A · 18g · 230 cal · 11g sugar |
| 10 | Best snack size | Promix Mexican Hot Chocolate | B · 15g · 140 cal · 4g sugar |

Editorial kept: 13-oil cards, a short "what still counts as no seed oil" note (coconut oil, high-oleic oils, nut/seed butters), and the "Do Pure Protein, Perfect Bar, Built Bar, and IQBAR use seed oils?" section (anchor #brand-seed-oil-check; per-brand paragraphs kept, its v1 table dropped since all four are in the big-brands table). Findings: palm kernel oil is the top offender (429 bars, 8 as a trace), Barebells 23 of 25 fail, share by grade (v13: A 7% … F 95%). A hero claim that palm kernel oil "usually hides in the coating" was stopped by the build's own check (only 98 of 429 list it inside a coating/crisp item) and was removed.

### clean-protein-bars — LOCKED 2026-09-30
Screen (GUIDE_CRITERIA.md): A or B grade, no Artificial Sweeteners tag, no Processed Oils tag. Database 41: **514 qualify** (218 A, 296 B), 335 eligible, 794 fail.
Guide slots (Jeff, 2026-09-30, after two rounds): **Best whey protein** (whey on the label), **Lowest net carbs**, **Best non-GMO** (Non-GMO field), **Best soy-free** (Soy Free field). Fallbacks: **Best dairy-free**, then **Highest fiber**. Chosen so none of the four guide picks repeat a pick from the other v2 guides (the core six can't avoid it). Rejected on the way: date-sweetened, stevia/monk fruit, snack size, allulose, oat-free, egg-white protein (too narrow), organic (no certified-organic field), least fat, the spec's default four (all four picks repeated other guides).
Bar Finder: **`/bar-finder?preset=no_seed_oil&grade=A,B&excl=sucralose`** (514 = 514 headless; the build checks the sets match key for key). The Clean Ingredients preset does NOT match (83 bars: A only, 12g+ protein, no sugar alcohols; it also includes 2 Simply Protein bars with processed oil). It is linked as a secondary "stricter filter" button and described as what it is. Redefining the preset is a separate, sitewide job (see Open items).
Page 1.47MB → ~125KB, FAQ at ~111KB.

| # | Slot | Pick | Data | Buy link |
|---|---|---|---|---|
| 1 | Best overall | Immortal Chocolate | A · 15g · 160 cal · 10g sugar | brand only |
| 2 | Cleanest ingredients | Kize Peanut Butter | A · 10g · 210 cal · 12g sugar | Amazon |
| 3 | Highest protein | Tilt Vanilla Almond | B · 28g · 240 cal · 2g sugar | Amazon |
| 4 | Most protein per calorie | Gryp Rocky Road and Sea Salt | B · 25g · 170 cal · 1g sugar | referral |
| 5 | Lowest calorie | RXBAR Blueberry | A · 12g · 180 cal · 15g sugar | Amazon |
| 6 | Best from a big brand | RXBAR Strawberry Strudel | A · 12g · 190 cal · 14g sugar | Amazon |
| 7 | Best whey protein | Daryl's Bars Chocolate Hazelnut | A · 20g · 230 cal · 5g sugar | Amazon |
| 8 | Lowest net carbs | IQ Bar Chocolate Mint Chip | B · 12g · 170 cal · 2g net carbs | referral |
| 9 | Best non-GMO | Rello Vanilla Crisp | A · 20g · 260 cal · 12g sugar | Amazon |
| 10 | Best soy-free | The Feel Bar Brownie Chocolate Chip | A · 15g · 200 cal · 7g sugar | brand only |

IQ Bar ties BalanceDiet Creamy Peanut Butter Nougat at 2g net carbs and wins on the referral link.
Editorial kept and trimmed: the three screen cards (grade C or below / artificial sweeteners / processed oils, with inline "and N more" lists), "Why these three checks" (the v1 "What actually makes a protein bar clean" copy, minus the Low Sugar + High Protein reference), the four questions, and a new "What clean doesn't cover" note (macros; 17 clean bars contain a sugar alcohol; the stricter Clean Ingredients preset). Findings: most failing bars fail more than one check (533 of 794; 503 with a processed oil plus a C-or-below grade), Barebells and Quest fail completely, failing bars average more protein (14.5g vs 11.4g). Chart = share of bars with an artificial sweetener or processed oil, by grade (A 6, B 25, C 60, D 90, F 98).
FAQ fixes: erythritol (scored as a real concern, doesn't disqualify on its own; 7 erythritol bars grade B and qualify), protein sources (egg whites and whey isolate rate highest, then whey concentrate/casein/milk protein, then pea/rice; collagen is the weakest positive, not a concern), dropped "table below" / "Mixed Lineups table above" / "reflects September 2026", "ingredient score" → "ingredient grade", new "Do clean protein bars have sugar alcohols?".

### best-bars-for-diabetics — LOCKED 2026-09-30
Screen (GUIDE_CRITERIA.md, unchanged): sugar ≤ 5g, net carbs ≤ 10g (full subtraction), fiber ≥ 5g, protein ≥ 10g, A or B grade, no maltitol family. Database 41: **89 qualify** (18 A, 71 B), all 89 eligible, 1,219 fail.
Guide slots (Jeff, 2026-09-30): **Lowest net carbs**, **Lowest sugar** (tightened: no sugar alcohol), **Best whey protein**, **Best soy-free**. Fallbacks: **Best gluten-free**, then **Highest fiber**. None of the four guide picks repeats a pick from the five earlier v2 guides. Considered and not used: Highest fiber and Best non-GMO (both pick Julian Bakery Peanut Butter, already Highest fiber on no-artificial-sweeteners and gluten-free), Best plant-based (Fello twins, Zesty BBQ is on 3 guides), Best dairy-free (B.T.R. Peanut Butter Crunch, on no-artificial-sweeteners).
Best non-GMO, if Jeff ever wants it here: every qualifying non-GMO bar is B grade. After Julian Bakery Peanut Butter the rule picks The Feel Bar Blueberry Muffin (10g · 100 cal, brand only); the best one with an Amazon link is Stars and Honey Peanut Butter Blackberry (15g · 170 cal).
Bar Finder: **`/bar-finder?grade=A,B&protein=10&sugar=5&fiber=5&netcarbs=10&excl=maltitol,polyglycitol,hydrogenated%20starch%20hydrolysate`** (89 = 89 headless, key for key; the build ports app.js applyFilters, including "skip a slider when the field is empty", and checks the sets match). No preset, cert, excl or grade combination matches without the slider params. `excl=maltitol` alone also gives 89 today; the three-term version tracks the guide's rule.
Page 456KB → ~134KB, FAQ at ~118KB. The v1 page had no ItemList region; the builder adds the marker once (see Hard targets).

| # | Slot | Pick | Data | Buy link |
|---|---|---|---|---|
| 1 | Best overall | Daryl's Bars Cinnamon Bun | A · 21g · 230 cal · 4g sugar · 3g net carbs · 16g fiber | Amazon |
| 2 | Cleanest ingredients | Healthy Eating on the Go Chia Seed | A · 14g · 205 cal · 4g sugar · 9g net carbs · 5g fiber | brand only |
| 3 | Highest protein | Gryp Rocky Road and Sea Salt | B · 25g · 170 cal · 1g sugar · 10g net carbs · 7g fiber | referral |
| 4 | Most protein per calorie | Quest Oatmeal Chocolate Chip | B · 20g · 180 cal · 1g sugar · 5g net carbs · 14g fiber | Amazon |
| 5 | Lowest calorie | Simply Protein Cocoa Raspberry | A · 12g · 140 cal · 2g sugar · 8g net carbs · 7g fiber | Amazon |
| 6 | Best from a big brand | Kirkland Chocolate Brownie | B · 21g · 190 cal · 2g sugar · 10g net carbs · 10g fiber | brand only (Costco) |
| 7 | Lowest net carbs | IQ Bar Chocolate Sea Salt | B · 12g · 170 cal · 1g sugar · 2g net carbs · 8g fiber | referral + Amazon |
| 8 | Lowest sugar | Fello Everything Bagel | A · 15g · 190 cal · 1g sugar · 8g net carbs · 5g fiber | brand only |
| 9 | Best whey protein | Daryl's Bars Orange Creamsicle | A · 20g · 230 cal · 2g sugar · 4g net carbs · 14g fiber | Amazon |
| 10 | Best soy-free | B.T.R. Nation Coffee Cashew Crunch | A · 15g · 240 cal · 2g sugar · 6g net carbs · 10g fiber | referral + Amazon |

Ties: #7 four IQ Bar flavors at 2g net carbs, all with a referral link, the shuffle picks Chocolate Sea Salt (clean has Mint Chip); #8 three Fello twins, the shuffle picks Everything Bagel; #10 two identical B.T.R. flavors, the shuffle picks Coffee Cashew Crunch.
Decisions (Jeff, 2026-09-30): **keep** Quest Oatmeal Chocolate Chip (#4; B grade, sucralose and erythritol, the only qualifying bar with an artificial sweetener); **no HOLD** on Daryl's Cinnamon Bun (A with sugar and palm kernel oil in its yogurt coating, a late sub-ingredient); **add an IMO gotcha** instead of changing the screen: 7 of 89 qualifying bars (6 Daryl's, Kirkland Chocolate Brownie) list IMO, including picks #1, #6 and #9. The note says our scoring treats IMO as fiber and some research suggests it is partly digested like sugar. The build checks the counts and names.
Disclaimer (required, exact): "We are not doctors or dietitians. These are the qualities we know people look for, so that's what we factored in." (Jeff: spelled "dietitians".) It appears in the hero and as a callout in "what it means".
Editorial kept and trimmed: "What we screened for" and "What actually makes a bar good for diabetes" merged into one "what it means" section (net carbs explainer, four count cards: sugar / net carbs / fiber / maltitol with its "Found in" list, "Why we exclude maltitol instead of adjusting for it", the IMO note, the four questions, "Diabetes management is individual"). Findings: the maltitol trap (38% of bars with ≤1g listed sugar), net carbs catches more bars than sugar (896 vs 736), a clean grade isn't enough (90% of A-grade bars miss a sugar/net carb/fiber cutoff; every Quest flavor meets them but 15 of 16 grade C or below). Chart = share with maltitol or a relative by grade (A 0, B 1, C 15, D 32, F 63). Top 50 adds a Net carbs column.
Fixed (no longer true): the v1 FAQ "How is the brand table below different from the ranked bar list above?" (dropped, no such tables on v2); "check the flavor table above" in the IQ Bar and Quest FAQs; "check the brand table below" in the hero; the Quest FAQ said "Mixed by our screen: 1 of 16 ... clear" (now "Only 1 of 16 ... clears", naming the flavor and that the rest miss on grade); "can score an A" → "earn an A"; the v1 Bar Finder button opened the unfiltered Bar Finder; the old disclaimer wording. New FAQ: "What is the best protein bar for diabetics?" (from the picks, with the IMO caveat when it applies).
Open: the "Best from a big brand" card copy (lib) says "a brand you can find in most grocery stores", which doesn't fit Kirkland (Costco only). Also on gluten-free. A lib wording fix would change both pages; ask Jeff.

### keto-protein-bars — LOCKED 2026-09-30
Screen (GUIDE_CRITERIA.md, unchanged): net carbs ≤ 8g (full subtraction), fat ≥ 8g, protein ≥ 10g, no maltitol family. No grade gate. Database 41: **104 qualify** (15 A, 49 B, 22 C, 14 D, 4 F), 64 eligible for the Best 10; the Top 50 is all A/B (grade-first order, checked every build). 1,204 fail.
Guide slots (Jeff, 2026-09-30: "just pick the best ones"): **Lowest net carbs**, **Best whey protein**, **Highest fiber**, **Best dairy-free**. Fallbacks: **Best soy-free**, then **Best gluten-free**. Every option for a fourth slot repeated one other guide; dairy-free was the only one with an Amazon link and a referral link. Lowest net carbs can't avoid clean's pick: four IQ Bar flavors tie at 2g, and Mint Chip / Sea Salt win on fiber before the shuffle.
Bar Finder: exception, see section 9. The build checks that the link returns every keto bar plus only bars under 8g fat (170 headless, key for key; sort=fat:desc puts the 104 first).
Page 474KB → ~134KB, FAQ at ~118KB. ItemList marker inserted once (as diabetics).

| # | Slot | Pick | Data | Buy link |
|---|---|---|---|---|
| 1 | Best overall | Daryl's Bars Cinnamon Bun | A · 21g · 230 cal · 8g fat · 3g net carbs · 16g fiber | Amazon |
| 2 | Cleanest ingredients | Healthy Eating on the Go Chocolate Mint | A · 15g · 210 cal · 11g fat · 6g net carbs · 3g fiber | brand only |
| 3 | Highest protein | Daryl's Bars Orange Creamsicle | A · 20g · 230 cal · 9g fat · 4g net carbs · 14g fiber | Amazon |
| 4 | Most protein per calorie | Julian Bakery Almond Butter | B · 20g · 210 cal · 9g fat · 4g net carbs · 17g fiber | brand only |
| 5 | Lowest calorie | Fello Zesty BBQ | A · 15g · 190 cal · 10g fat · 8g net carbs · 5g fiber | brand only |
| 6 | Best from a big brand | IQ Bar Peanut Butter Chip | B · 12g · 160 cal · 10g fat · 3g net carbs · 9g fiber | referral + Amazon |
| 7 | Lowest net carbs | IQ Bar Chocolate Mint Chip | B · 12g · 170 cal · 12g fat · 2g net carbs · 8g fiber | referral + Amazon |
| 8 | Best whey protein | BalanceDiet Delicious Almond Coconut | B · 15g · 190 cal · 9g fat · 2g net carbs · 12g fiber | Amazon |
| 9 | Highest fiber | War On Sugar Peanut Butter Pistachio | B · 15g · 220 cal · 12g fat · 7g net carbs · 13g fiber | Amazon |
| 10 | Best dairy-free | B.T.R. Nation Peanut Butter Crunch | A · 15g · 230 cal · 15g fat · 7g net carbs · 10g fiber | referral + Amazon |

Repeats elsewhere: #1 and #3 (diabetics), #5 (NSA, GF, NSO), #7 (clean), #10 (NAS). #8 ties its identical twin Creamy Peanut Butter Nougat; the shuffle picks Almond Coconut. No A/B keto bar has an artificial sweetener.
Editorial kept and trimmed: "What we screened for" + "What actually makes a bar keto-friendly" merged into one "what it means" section (four count cards: net carbs / fat / protein / maltitol with its "Found in" list, "Why we exclude maltitol instead of adjusting for it", a new "Keto doesn't screen on ingredient grade" note (40 of 104 grade C or below), the IMO note (9 Daryl's bars, picks #1 and #3), the four questions, "How strict keto needs to be varies"). Disclaimer: the standard wording (same as diabetics). Findings: net carbs is the toughest check (1,027, 79%), the maltitol trap (38%), a clean grade and keto macros rarely line up (6% of A vs 12% of B clear keto; most A bars that miss contain dates, oats or honey, checked). Chart = share of bars that clear keto, by grade (A 6, B 12, C 7, D 6, F 3).
Fixed (no longer true): the brand-table-vs-ranked-list FAQ (dropped); "check the brand table below" (hero) and "check the flavor table above" (Quest FAQ) removed; the Quest FAQ said "Mixed by our screen: 6 of 16"; it now says "Partly": the rest miss on fat and all 6 that qualify grade C or below; "can score an A" → "earn an A"; the grade FAQ said grade was "extra context" (now: not part of the screen, 40 of 104 grade C or below, every Best 10 and Top 50 bar is A or B); title "Ranked by Ingredient Quality" → "10 Best Keto Protein Bars (1,000+ Checked)"; the v1 Bar Finder button opened the unfiltered Bar Finder. New FAQ: "What is the best keto protein bar?".
Note: "Brands that do it well" includes Atkins (6/9, C and D grades) because the locked rule needs 2+ big brands and only IQ Bar, Atkins and Quest have keto bars. Its row says the grades plainly.

### glp1-protein-bars — LOCKED 2026-09-30
Screen (GUIDE_CRITERIA.md, unchanged): protein ≥ 15g, calories ≤ 200, sugar ≤ 4g, fiber ≥ 3g, no sugar alcohol (0g on the label and none named in the ingredients, IMO included), A or B grade. Database 41: **21 qualify** (3 A, 18 B), all eligible (floor 15g), 1,287 fail. Fewer than 50 qualify, so the list section is "All 21 GLP-1 friendly protein bars".
Guide slots (picked by Claude 2026-09-30; Jeff asked for the best picks delivered without an approval round): **Best whey protein**, **Highest fiber**, **Lowest sugar**, **Best plant-based**. Fallbacks: **Lowest net carbs**, then **Best gluten-free**. With 21 bars, every fiber/sugar/certification option runs through Julian Bakery Peanut Butter first; it stays as Highest fiber (17g is the standout number for this audience) and is the only guide pick that repeats another guide. Lowest sugar uses the plain rule (no bar here has a sugar alcohol).
Bar Finder: **`/bar-finder?preset=glp1`** (21 = 21 headless, key for key; the build ports `PRESETS.glp1.apply`).
Page 249KB → ~91KB, FAQ at ~76KB. ItemList marker inserted once.

| # | Slot | Pick | Data | Buy link |
|---|---|---|---|---|
| 1 | Best overall | Fello Spicy Pizza | A · 15g · 190 cal · 1g sugar · 5g fiber | brand only |
| 2 | Cleanest ingredients | Fello Everything Bagel | A · 15g · 190 cal · 1g sugar · 5g fiber | brand only |
| 3 | Highest protein | Ration Jalapeno Cheddar | B · 25g · 190 cal · 1g sugar · 9g fiber | brand only |
| 4 | Most protein per calorie | Ration Toasted Oat Sea Salt | B · 25g · 170 cal · 1g sugar · 8g fiber | brand only |
| 5 | Lowest calorie | Promix Mexican Hot Chocolate | B · 15g · 140 cal · 4g sugar · 6g fiber | brand only |
| 6 | Best from a big brand | NuGo Espresso | B · 16g · 170 cal · 3g sugar · 6g fiber | Amazon |
| 7 | Best whey protein | Atlas Salted Peanut Butter | B · 20g · 200 cal · 1g sugar · 11g fiber | Amazon |
| 8 | Highest fiber | Julian Bakery Peanut Butter | B · 20g · 200 cal · 1g sugar · 17g fiber | brand only |
| 9 | Lowest sugar | Chief Hazelnut Brownie | B · 16g · 200 cal · 2g sugar · 4g fiber | Amazon |
| 10 | Best plant-based | NuGo Brownie Crunch | B · 16g · 180 cal · 3g sugar · 7g fiber | Amazon |

Repeats elsewhere: #1 (NSA, NAS, GF), #2 (diabetics), #5 (NSO), #8 (NAS, GF). The six core slots mostly go to brand-only bars (Fello, Ration, Promix); the four guide picks carry three of the page's four Amazon links. #9 ties at 2g sugar and wins on protein.
Editorial kept and trimmed: the six-check explainer (three "care about first" + three added checks) with four count cards (protein / calories / sugar / sugar alcohol with its "Found in" list), "Why no sugar alcohols at all" (stricter than keto/diabetics; ingredient list checked; IMO counts), "Why protein per calorie matters here", and the individual-tolerance line. Disclaimer: standard wording. Findings: the macros aren't the hard part (140 bars meet protein/calories/sugar/fiber; 96 of those have a sugar alcohol and 104 grade C or below), sugar is the toughest macro check (62%), only 9 of 197 brands have a qualifying flavor. Chart = share with a sugar alcohol by grade (A 8, B 15, C 33, D 52, F 70).
Fixed (no longer true): the v1 finding "the narrowest brand spread of any guide" (creatine is narrower: 6 brands vs 9; the v1 code only printed it when true, so the new copy doesn't claim it) and a draft "shortest list of any guide" (creatine has 14); the brand-table-vs-ranked-list FAQ (dropped); "check the brand table below" (hero) and "check the flavor table above" (NuGo/Promix FAQs); "Mixed by our screen" for NuGo 2/31 and Promix 1/13 (now "Only …", naming the flavors); "can score an A" → "earn an A"; "average 189.8 calories" → 190; the title "Ranked by Ingredient Quality". New FAQ: "What is the best protein bar for GLP-1?".

### vegan-protein-bars — LOCKED 2026-09-30
Screen (GUIDE_CRITERIA.md, unchanged): Vegan (Y/N) = Yes (field holds only Yes or blank, checked every build). Database 41: 263 qualify (59 A, 94 B, 69 C, 33 D, 8 F), 97 eligible. **Database 42 (Aloha's 18 bars marked vegan): 281 qualify**; the Best 10 is unchanged (every Aloha bar grades C or below).
Guide slots (picked by Claude 2026-09-30, no approval round per Jeff): **Highest fiber**, **Best gluten-free**, **Best soy-free**, **Lowest net carbs**. Fallbacks: **Best non-GMO**, then **Lowest sugar** (no sugar alcohol). Whey is impossible here and plant-based / dairy-free are redundant. Lowest sugar would have picked a Fello twin (on 4–5 guides already), so it's only a fallback. Lowest net carbs is kept for its referral + Amazon link even though four IQ Bar flavors tie at 2g and Mint Chip wins on fiber (also on clean and keto).
Bar Finder: **`/bar-finder?certs=Vegan`** (263 = 263 headless, key for key).
Page 889KB → ~130KB, FAQ at ~116KB (the page already had an ItemList region).

| # | Slot | Pick | Data | Buy link |
|---|---|---|---|---|
| 1 | Best overall | Immortal Chocolate | A · 15g · 160 cal · 10g sugar · 4g fiber | brand only |
| 2 | Cleanest ingredients | Skout Peanut Butter | A · 10g · 210 cal · 18g sugar · 5g fiber (4 ingredients) | Amazon |
| 3 | Highest protein | Posana Matcha Latte | B · 20g · 220 cal · 3g sugar · 9g fiber | brand only |
| 4 | Most protein per calorie | NuGo Espresso | B · 16g · 170 cal · 3g sugar · 6g fiber | Amazon |
| 5 | Lowest calorie | Simply Protein Cocoa Raspberry | A · 12g · 140 cal · 2g sugar · 7g fiber | Amazon |
| 6 | Best from a big brand | NuGo Brownie Crunch | B · 16g · 180 cal · 3g sugar · 7g fiber | Amazon |
| 7 | Highest fiber | Elavi Chocolate | B · 11g · 190 cal · 8g sugar · 12g fiber | Amazon |
| 8 | Best gluten-free | Simply Protein Dark Chocolate Almond | A · 13g · 160 cal · 2g sugar · 7g fiber | Amazon |
| 9 | Best soy-free | The Feel Bar Brownie Chocolate Chip | A · 15g · 200 cal · 7g sugar · 5g fiber | brand only |
| 10 | Lowest net carbs | IQ Bar Chocolate Mint Chip | B · 12g · 170 cal · 2g net carbs · 8g fiber | referral + Amazon |

8 of 10 have an Amazon link. Repeats elsewhere: #1 (4 guides), #4 and #6 (glp1), #5 (4 guides), #9 (clean), #10 (clean, keto); #2, #3, #7 and #8 are new.
Editorial kept and trimmed: "What disqualifies a protein bar from being vegan" with the seven animal-ingredient cards (now v2 count cards with inline "and N more" lists). Findings: pea protein is the plant-protein default (128 of 263, ahead of rice 84 and soy 49); vegan bars grade A/B more often (58% vs 48%) but average less protein (9.9g vs 13.3g); Barebells' four vegan flavors grade D to F, worse than its dairy lineup. Chart = share labeled vegan by grade (A 25, B 24, C 22, D 13, F 6).
Fixed (no longer true / against v2 rules): a v1 finding printed average ingredient SCORES ("5.2 vs 4.3"; grades only now); the FAQ "This page reflects the database as of [date]" (dropped); "The full ranked list is in the table below, sorted by ingredient quality"; OG copy "Ranked by ingredient quality score"; the hero's "Ranking N bars by ingredient quality ... Not just us telling you the flavors we like"; the separate "What protein bars are not vegan?" FAQ (merged into the cards; the whey FAQ covers it). New FAQ: "What is the best vegan protein bar?".
Data note: Aloha's 18 bars had a blank Vegan field; **Jeff marked them vegan in database 42** (2026-09-30). **CLIF Bar (Jeff):** no flavor names an animal ingredient, but Clif doesn't call its bars vegan because they may be made in bakeries that also use animal-based ingredients. The big-brands verdict says exactly that (`CLIF_WHY`, checked every build), and a new FAQ "Are CLIF Bars vegan?" answers it, citing Clif's own page (https://www.clifbar.com/stories/are-clif-bar-energy-bars-vegan-our-philosophy, checked 2026-09-30: "may be made in a bakery that uses dairy-based ingredients"; Clif uses "plant-based" rather than "vegan"). The link is an inline citation in the FAQ answer (opens in a new tab, no affiliate tag); the FAQ JSON-LD carries the plain text. The copy says "dairy-based" to match the source.
Note: "Brands that do it well" is led by fully vegan, all-A whole-food brands, several with low protein (Wise Bar 4g, Bearded Bros 6.6g avg). That's the locked ranking rule (share × grade); the Avg protein column shows it.

### dairy-free-protein-bars — LOCKED 2026-09-30
Screen (GUIDE_CRITERIA.md, unchanged): Dairy Free (Y/N) = Yes, the brand's label (field holds only Yes or blank). Database 42: **247 qualify** (69 A, 90 B, 72 C, 13 D, 3 F), 99 eligible, 1,061 fail. Built as a standalone v2 builder (the v1 page came from kyb_cert_guide.CertGuide, which soy-free and kosher still use).
Guide slots (picked by Claude 2026-09-30, no approval round): **Best soy-free**, **Best non-GMO**, **Best gluten-free**, **Highest fiber**. Fallbacks: **Lowest sugar** (no sugar alcohol), then **Lowest net carbs**. Whey is impossible; lowest sugar and net carbs would repeat IQ Bar Chocolate Mint Chip (already on clean, keto and vegan).
Bar Finder: **`/bar-finder?certs=Dairy%20Free`** (247 = 247 headless, key for key).
Page 843KB → ~129KB, FAQ at ~114KB (the page already had an ItemList region).

| # | Slot | Pick | Data | Buy link |
|---|---|---|---|---|
| 1 | Best overall | CuraBar Chocolate Sea Salt | A · 18g · 230 cal · 11g sugar | brand only |
| 2 | Cleanest ingredients | Kize Cookie Dough | A · 10g · 200 cal · 13g sugar (4 ingredients) | Amazon |
| 3 | Highest protein | HOL Salted Chocolate | A · 20g · 290 cal · 16g sugar | Amazon |
| 4 | Most protein per calorie | Julian Bakery Peanut Butter | B · 20g · 200 cal · 1g sugar | brand only |
| 5 | Lowest calorie | Act Bar Cashew Coconut | A · 10g · 190 cal · 7g sugar | brand only |
| 6 | Best from a big brand | IQ Bar Peanut Butter Chip | B · 12g · 160 cal · 1g sugar | referral + Amazon |
| 7 | Best soy-free | B.T.R. Nation Cinnamon Cashew Crunch | A · 15g · 240 cal · 2g sugar | referral + Amazon |
| 8 | Best non-GMO | HOL Peanut Butter Cacao | A · 20g · 280 cal · 16g sugar | Amazon |
| 9 | Best gluten-free | CuraBar Apple Cinnamon | A · 17g · 230 cal · 12g sugar | brand only |
| 10 | Highest fiber | Julian Bakery Almond Butter | B · 20g · 210 cal · 1g sugar · 17g fiber | brand only |

Repeats elsewhere: #1 (NSA, GF, NSO), #4 (NAS, GF, glp1), #6 (keto), #10 (keto). #7, #8 and #9 are new. 5 of 10 have an Amazon link (the dairy free field is dominated by brand-only small makers).
Editorial kept and trimmed: "What disqualifies" with the Whey / Milk / Casein / Not labeled cards, the "Is dairy free the same as vegan?" note. New: "What about vegan bars?" (177 vegan-labeled bars carry no dairy free label, incl. NuGo, GoMacro, Lenny & Larry's; the screen stays label-based, like CLIF Bar on vegan) and FAQs "What is the best dairy free protein bar?" and "Are vegan protein bars dairy free?". Findings: whey is the clearest source (534, all 16 Quest), many unlabeled bars name no dairy (458, 177 of them vegan), dairy free bars grade A/B more (64% vs 48%) with less protein (11g vs 13.3g). Chart = share labeled dairy free by grade (A 30, B 23, C 23, D 5, F 2).
Fixed: v1 printed percentages to a decimal ("64.4%", "40.8%"), OG "Ranked by ingredient quality score", "full ranked list in the table below", "This page reflects the database as of [date]"; the v1 "Best for keto" / "Simplest ingredient list" tiles are replaced by the Best 10.
Data note: Fro Pro Sweet Coconut lists sodium caseinate inside its coconut milk powder but is labeled dairy free. **Jeff confirmed the dairy free label is correct** (already in `REVIEWED_OK` in kyb_guide_lib.py since 2026-09-24; the first dairy-free v2 builder missed that list and was fixed to use `reviewed_ok()` for its warning and its Top 50 check).
Decision to make (Jeff): the 177 vegan-labeled bars without the dairy free label. Leaving them out is consistent with a label-based screen; marking them Dairy Free in the database would add them here (and to the Bar Finder filter) with no code change.

### soy-free-protein-bars — LOCKED 2026-09-30
Screen (GUIDE_CRITERIA.md, unchanged): Soy Free (Y/N) = Yes (brand label; field holds only Yes or blank). Database 42: **292 qualify** (59 A, 132 B, 71 C, 25 D, 5 F), 130 eligible, 1,016 fail. Standalone v2 builder (no longer kyb_cert_guide; only kosher still uses it). The three named soy sources use the GUIDE_CRITERIA patterns, and soy protein / lecithin are never described as concern ingredients (a short "Is soy bad for you?" note says so).
Guide slots (picked by Claude 2026-09-30, no approval round): **Best dairy-free**, **Best gluten-free**, **Best plant-based**, **Best non-GMO**. Fallbacks: **Best whey protein**, then **Highest fiber**. Soy-free shoppers are mostly allergy shoppers, so the other allergen labels come first; lowest sugar / net carbs would repeat IQ Bar Chocolate Mint Chip (3 guides) and highest fiber Julian Bakery Peanut Butter (4 guides). Chosen by trying every order of the preferred slots and keeping the one with the most new picks and Amazon links.
Bar Finder: **`/bar-finder?certs=Soy%20Free`** (292 = 292 headless, key for key).
Page 969KB → ~129KB, FAQ at ~114KB. The v1 head's font link imported DM Mono and IBM Plex Mono (the brand_qa.py failure); it now loads the same Roboto Mono / DM Sans / Barlow Condensed set as the other guides (literal head edit, kept by every rebuild). brand_qa.py now fails only on kosher.

| # | Slot | Pick | Data | Buy link |
|---|---|---|---|---|
| 1 | Best overall | The Feel Bar Mint Chocolate Chip | A · 15g · 200 cal · 7g sugar | brand only |
| 2 | Cleanest ingredients | Kize Peanut Butter | A · 10g · 210 cal · 12g sugar (4 ingredients) | Amazon |
| 3 | Highest protein | Legion Chocolate Chip Cookie Dough | B · 20g · 250 cal · 4g sugar | Amazon |
| 4 | Most protein per calorie | Takeaways Cheese Pizza | B · 12g · 120 cal · 1g sugar | referral |
| 5 | Lowest calorie | Kize Peanut Butter Crunch With Pumpkin Seeds | A · 10g · 190 cal · 10g sugar | Amazon |
| 6 | Best from a big brand | IQ Bar Peanut Butter Chip | B · 12g · 160 cal · 1g sugar | referral + Amazon |
| 7 | Best dairy-free | B.T.R. Nation Cinnamon Cashew Crunch | A · 15g · 240 cal · 2g sugar | referral + Amazon |
| 8 | Best gluten-free | The Feel Bar Brownie Chocolate Chip | A · 15g · 200 cal · 7g sugar | brand only |
| 9 | Best plant-based | Real Food Bar Cherry Cashew | B · 15g · 190 cal · 10g sugar | referral + Amazon |
| 10 | Best non-GMO | Organic Gorilla Peanut Butter Banana | A · 15g · 270 cal · 28g sugar | Amazon |

8 of 10 have an Amazon or referral link. New on any guide: #3, #4, #5, #9, #10. Repeats: #1 (GF), #2 (5 guides), #6 (keto, dairy-free), #7 (dairy-free), #8 (clean, vegan).
Editorial kept and trimmed: "What disqualifies" with Soy lecithin / Soy protein / Soybean oil / Not labeled cards. Findings: soy lecithin is the most common source (414 vs 341 soy protein; all 14 CLIF Bars use soy protein), soy free bars grade A/B more (65% vs 48%) as correlation, not a soy penalty (artificial sweeteners 0% vs 19%, processed oils 27% vs 47%), 516 unlabeled bars name no soy. Chart = share labeled soy free by grade (A 25, B 34, C 23, D 10, F 4).
Fixed: v1 decimals ("73.4%"), OG "Ranked by ingredient quality score", "full ranked list in the table below", "reflects the database as of [date]", the v1 tiles. New FAQ "What is the best soy free protein bar?".
Data note: Fro Pro Cookies and Cream is labeled soy free but lists soy lecithin. **Jeff removed its Soy Free label in the database (2026-09-30)**, and its old `REVIEWED_OK` entry was removed from kyb_guide_lib.py. The build warns about it until the next database upload is run; after that, soy-free drops to 291 (recompute, don't assume). The builder uses `reviewed_ok()` like dairy-free.

### kosher-protein-bars — LOCKED 2026-09-30
Screen (GUIDE_CRITERIA.md, unchanged): Kosher (Y/N) = Yes (field holds only Yes or blank). A supervised-process certification, not an ingredient screen; gelatin, confectioner's glaze/shellac and carmine/rennet are context cards only (a kosher-labeled bar may list certified gelatin; none does today). No grade gate. Database 42: **154 qualify** (30 A, 39 B, 38 C, 36 D, 11 F), 25 eligible for the Best 10 (A/B with 10g+ protein), 1,154 fail. The Top 50 is all A/B (checked). Standalone v2 builder; kyb_cert_guide.py now has no users.
Guide slots (picked by Claude 2026-09-30, no approval round): **Best whey protein**, **Lowest sugar** (no sugar alcohol), **Best gluten-free**, **Best non-GMO**. Fallbacks: **Highest fiber**, then **Lowest net carbs**. Dairy-free, soy-free and plant-based are empty (no eligible kosher bar carries those labels); fiber (5g top) and net carbs (17g top) are weak here. **Every pick has an Amazon link, and 9 of 10 are on no other guide** (only Simply Protein Cocoa Raspberry repeats).
Bar Finder: **`/bar-finder?certs=Kosher`** (154 = 154 headless, key for key).
Page 612KB → ~130KB, FAQ at ~116KB. Head font link fixed like soy-free; **brand_qa.py now passes on every page**.

| # | Slot | Pick | Data | Buy link |
|---|---|---|---|---|
| 1 | Best overall | KIND Raspberry Cocoa Crisp | B · 20g · 240 cal · 1g sugar | Amazon |
| 2 | Cleanest ingredients | Bearded Bros Peanut Butter Chocolate | A · 11g · 230 cal · 17g sugar (5 ingredients) | Amazon |
| 3 | Highest protein | KIND Sweet and Salty Caramel Peanut Crisp | B · 20g · 240 cal · 1g sugar | Amazon |
| 4 | Most protein per calorie | Simply Protein Lemon Coconut | B · 13g · 150 cal · 2g sugar | Amazon |
| 5 | Lowest calorie | Simply Protein Cocoa Raspberry | A · 12g · 140 cal · 2g sugar | Amazon |
| 6 | Best from a big brand | RXBAR Strawberry Peanut Butter | B · 18g · 260 cal · 16g sugar | Amazon |
| 7 | Best whey protein | Rise Honey Cinnamon (Snickerdoodle) | B · 18g · 280 cal · 17g sugar | Amazon |
| 8 | Lowest sugar | GoMacro Coconut Almond Butter Chocolate Chips | B · 11g · 270 cal · 7g sugar | Amazon |
| 9 | Best gluten-free | RXBAR Vanilla Peanut Butter | B · 18g · 270 cal · 16g sugar | Amazon |
| 10 | Best non-GMO | Rise Almond Honey | B · 18g · 280 cal · 17g sugar | Amazon |

Best overall is a B: no A-grade kosher bar has 15g+ protein (the card says "of any B-grade bar here"). The KIND picks are the allulose-sweetened Protein line (1g sugar). #8's "lowest sugar" excludes KIND and Simply Protein (already picked; the card says so).
Editorial kept and trimmed: "What keeps a protein bar from being kosher" (certification vs ingredients; Gelatin / Confectioner's glaze / Carmine or rennet / Not kosher-certified cards) plus a new "Kosher doesn't screen on ingredient grade" note (85 of 154 grade C or below). Findings: not being kosher is about certification (only ~8% of non-kosher bars contain a flagged ingredient), gelatin is the clearest non-kosher ingredient (all 13 Built flavors), kosher bars grade about average (45% A/B vs 48%) with much less protein (7.7g vs 13.3g; Larabar and Bobo's are the biggest kosher lineups). Chart = share certified kosher by grade (A 13, B 10, C 12, D 15, F 9: flat, which is the point).
Fixed: v1 decimals, OG "Ranked by ingredient quality score", "table below", "reflects the database as of [date]", the v1 tiles. New FAQs: "What is the best kosher protein bar?", "Is Built Bar kosher?".

### high-fiber-protein-bars — LOCKED 2026-09-30
Screen (GUIDE_CRITERIA.md, unchanged): Dietary Fiber ≥ 11g (the Extreme Fiber tier; 5g and 8g tiers shown as context). "The Extreme Fiber 100" stays as the tier's name in the hero, OG and one FAQ (the build checks N is still ~90–115). No grade gate. Database 42: **103 qualify** (6 A, 38 B, 37 C, 21 D, 1 F), 34 eligible, 1,205 under 11g.
Guide slots (picked by Claude 2026-09-30, no approval round): **Highest fiber**, **Lowest net carbs**, **Best whey protein**, **Best plant-based**. Fallbacks: **Most fiber per calorie**, then **Best gluten-free**. "Best from a big brand" is empty here (Quest Oatmeal Chocolate Chip is the only A/B big-brand bar with 11g+ and it's already Highest protein), so the builder lists that slot last and Most fiber per calorie takes it (card #10). Julian Bakery leads nearly every fiber/sugar/certification list, so it has two picks (#6 and #10, the brand cap).
Bar Finder: **`/bar-finder?fiber=11`** (103 = 103 headless, key for key; app.js skips the slider on an empty field, and every bar has a fiber value). The "three tiers" note has a `?fiber=5` button (613, checked).
Page 479KB → ~127KB, FAQ at ~113KB. Card macros: Fiber, Protein, Calories, Sugar. Top 50 columns: Grade, Fiber, Protein (+ Calories, Sugar on desktop).

| # | Slot | Pick | Data | Buy link |
|---|---|---|---|---|
| 1 | Best overall | Daryl's Bars Cinnamon Bun | A · 16g fiber · 21g · 230 cal | Amazon |
| 2 | Cleanest ingredients | Daryl's Bars Orange Creamsicle | A · 14g fiber · 20g · 230 cal | Amazon |
| 3 | Highest protein | Quest Oatmeal Chocolate Chip | B · 14g fiber · 20g · 180 cal | Amazon |
| 4 | Most protein per calorie | Atlas Salted Peanut Butter | B · 11g fiber · 20g · 200 cal | Amazon |
| 5 | Lowest calorie | Paleo Valley Apple Cinnamon | B · 13g fiber · 10g · 180 cal | Amazon |
| 6 | Highest fiber | Julian Bakery Peanut Butter | B · 17g fiber · 20g · 200 cal | brand only |
| 7 | Lowest net carbs | BalanceDiet Creamy Peanut Butter Nougat | B · 12g fiber · 2g net carbs · 15g | Amazon |
| 8 | Best whey protein | Santa Cruz Paleo Vanilla | B · 11g fiber · 20g · 240 cal | brand only |
| 9 | Best plant-based | Real Food Bar Cherry Cashew | B · 11g fiber · 15g · 190 cal | referral + Amazon |
| 10 | Most fiber per calorie | Julian Bakery Almond Butter | B · 17g fiber · 20g · 210 cal | brand only |

7 of 10 have an Amazon link. New on any guide: #5, #7, #8. The two Daryl's picks get part of their fiber from IMO; the editorial says so, and the IMO card now carries the same "partly digested like sugar" note as diabetics and keto.
Editorial kept and trimmed: "What actually pushes a bar past 11g of fiber" (five added-fiber cards + whole-food card), "The three tiers" folded in as a list with an A/B example per tier (Best overall rule) and the bloating note, and the Bar Finder slider link turned into a button. Findings: fiber drops off fast (613 → 243 → 103), 90% of 11g+ bars use an added fiber (tapioca fiber leads), high fiber isn't niche (13 of 16 Quest; five brands = 49 of 103) but 59 of 103 grade C or below. Chart = share with 11g+ fiber by grade (A 3, B 10, C 12, D 9, F 1).
Fixed: v1 decimals, OG "ranked by ingredient quality", "reflects the database as of [date]", the FAQ that called its pick "the highest ingredient quality score" (scores are never cited), the inline Bar Finder link (now a button), v1 tiles. New FAQs: "What is the best high fiber protein bar?", "Is Quest high in fiber?".
Data note: all 13 Built bars have 0g fiber. Jeff confirmed this is accurate (2026-09-30).

### caffeine-protein-bars and creatine-protein-bars — "small guides", 2026-09-30
Jeff asked for the best picks delivered without an approval round. These two categories are too small for a Best 10 under the locked guardrails (A/B grade, 10g+ protein, max 2 per brand), so each page shows **as many picks as the rules allow** instead of lowering the bar: caffeine **8** (13 eligible bars from 6 brands), creatine **6** (6 eligible from 3 brands). Title/H1 are "8 Best ..." / "The 6 Best ...". The criteria section says why (lib: `criteria_html(n_spots=)`; QA: `build_guide_page_v2(n_picks=)`; both default to 10, so the other thirteen guides are byte-identical). The builds check the count equals the maximum the rules allow.
- **Pick order vs card order:** the dose slots pick right after Best overall (`PICK_ORDER`), so they get first claim on the bars they're about; the cards still show the core slots first (`DISPLAY`). Card copy stays honest ("X ranks higher but is already on this list").
- **Bar Finder exception:** the Bar Finder has no caffeine or creatine filter, so no link can match. The CTA reads "Compare bars in the Bar Finder" / "Open the Bar Finder" (`/bar-finder`) and says the filter doesn't exist yet; both pages list every qualifying bar in an "All N" table (the Top 50 slot; `KT_COLS['caffeine']` / `['creatine']`). A "Has caffeine / Has creatine" toggle in the Bar Finder is parked (like Min Fat).
- **Big brands:** caffeine's table lists only the 3 big brands with a caffeinated bar (CLIF Bar, Clif Builders, Aloha) plus one line for the other 20; creatine has no big-brand bar, so the section is one paragraph.
- **Brands section, creatine:** every creatine brand (6), not only brands with 3+ bars; the usual rule would drop Rello and Daily Bar.
- **Chart:** grade mix of the qualifying bars (share of the N bars in each grade), since caffeine/creatine is 1–3% of every grade.

Caffeine (42 qualify, 24 A/B; screen = any caffeine; zones Light <50, Moderate 50–94, High 95–149, Very High 150+ mg). Guide slots: Most caffeine, Closest to a cup of coffee (50–94mg), Caffeine from coffee or tea (no isolated caffeine), Lowest sugar (no sugar alcohol). Empty: Most protein per calorie (every 12g+ bar already picked), Best from a big brand.

| # | Slot | Pick | Data | Link |
|---|---|---|---|---|
| 1 | Best overall | The Feel Bar Matcha Latte | B · 65mg · 15g · 180 cal | brand only |
| 2 | Cleanest ingredients | Quantum Peanut Butter Dark Chocolate | A · 100mg · 10g · 210 cal | Amazon |
| 3 | Highest protein | Real Food Bar Espresso Chip | B · 65mg · 15g · 210 cal | referral + Amazon |
| 4 | Lowest calorie | Verb Chocolate Chip Peanut Butter | B · 80mg · 10g · 190 cal | Amazon |
| 5 | Most caffeine | Quantum Salted Peanut Butter Crunch | A · 100mg · 10g · 200 cal | Amazon |
| 6 | Closest to a cup of coffee | Unhinged Chocolate and Coffee | A · 75mg · 11g · 190 cal | Amazon |
| 7 | Caffeine from coffee or tea | G2G Almond Mocha | B · 20mg (espresso) · 18g · 300 cal | Amazon |
| 8 | Lowest sugar | Verb Birthday Cake | B · 80mg · 10g · 10g sugar | Amazon |

Findings: ~3% of bars have caffeine (16 brands); the 150mg+ bars (Jesse's WAKEUP!, all F, under 3g protein; top 350mg = 88% of the FDA's 400mg); 19 of 42 have under 10g protein (8 of Verb's 11). Data note: Real Food Bar Espresso Chip lists 65mg caffeine but no coffee/caffeine ingredient (ask Jeff).

Creatine (14 qualify, 6 A/B; tiers Clinical 3g+ / Trace under 3g). Guide slot: Highest creatine dose. Empty: Best from a big brand.

| # | Slot | Pick | Data | Link |
|---|---|---|---|---|
| 1 | Best overall | Rello Vanilla Crisp | A · 1.2g · 20g · 260 cal | Amazon |
| 2 | Cleanest ingredients | Rello Chocolate Crunch | A · 1.2g · 20g · 260 cal | Amazon |
| 3 | Highest protein | JiMMYBAR! Strawberry | B · 5g · 20g · 220 cal | Amazon |
| 4 | Most protein per calorie | Daily Bar Cookie Dough Dazzler | B · 3g · 20g · 240 cal | Amazon |
| 5 | Lowest calorie | Daily Bar Chocolate Peanut Butter Banger | B · 3g · 20g · 260 cal | Amazon |
| 6 | Highest creatine dose | JiMMYBAR! Blueberry Lemon | B · 5g · 20g · 210 cal (maltitol, said on the card) | Amazon |

Findings: ~1% of bars (6 brands, no big brand); the only A-grade bars (Rello) carry 1.2g while the 3g+ bars grade B to F; every 5g bar uses a sugar alcohol. Editorial kept and trimmed: caffeine zones + where caffeine comes from + FDA 400mg; creatine two tiers + monohydrate + research dose. Fixed: v1 printed average ingredient scores (zones, tiers, findings); "brand table below" FAQ dropped; v1 snapshot/picks/dose tables gone. Data note: JiMMYBAR! Double Fudge Brownie's ingredient text has an unclosed parenthesis (counts as 1 top-level ingredient; it grades F either way).

### Cross-guide notes
- **Overlap:** slots 1–6 go to nearly the same bars on the free-from v2 guides (the same clean bars win every screen). Diabetics' narrower screen gives a mostly different core six (only Gryp, Simply Protein Cocoa Raspberry and Kirkland repeat). Repeats across guides are allowed; guide slots are chosen to reduce overlap.
- **Lowest sugar, tightened variant:** on NAS, GF, NSO and diabetics the slot only considers bars with no sugar alcohol (`has_sugar_alcohol()`), so a maltitol bar can't win on a 0g sugar line. no-sugar-alcohols is unaffected (every bar there already qualifies).
- **Tie wording:** a tie decided by buy link, shuffle or name prints as "tied for …" with no "wins the tie on" clause.
- **Big-brand verdicts:** "Only X of Y" is used only when fewer than half qualify. Their "Best pick" examples follow the tie chain, so they moved on several guides with the 2026-09-30 tiebreak. Diabetics' verdicts use singular "1 of 2 qualifies. The other one has …".
- **Shared helpers in kyb_guide_lib.py** (after the v2 section): `lead_sweetener()` / `brand_sweetener()` (V2_SWEETENERS), `section_cta_html()`, `v2_count_card_html()`, `slot_highest_fiber()`, and (2026-09-30) `buy_rank()`, `set_tie_seed()`, `tie_shuffle()`, `KT_COLS['netcarbs']`, `KT_COLS['fat']`, `top50_html(cols=, hide_mobile=)`.

### Suggested picks for the other guides (confirm at each guide's build session)
- caffeine / creatine: done 2026-09-30 (see their section above).

## Brands that do it well (section 6) — LOCKED
- Eligible: ≥ 3 bars in the DB and at least one qualifying.
- Rank: share of the brand's bars that qualify × average **grade points** of its qualifying bars (A=4 … F=0, divided by 4). Grades only, never the raw score (this replaces "avg ingredient score"). Ties go to the bigger lineup.
- Show 8: the top 8, then swap in brands until there are at least 2 Big Brands and at least 2 small/independent. One computed line each: how many qualify, the grade mix, and (on sweetener guides) the most common lead sweetener. (On diabetics the swap brings in Quest at 1/16 to reach two big brands; IQ Bar is the other.)

## Big Brands list — LOCKED 2026-09-29
Definition: national grocery / big-box / Costco distribution.
Quest, Barebells, RXBAR, KIND, CLIF Bar (+ Clif Builders, a separate brand name in bars.js), One, Pure Protein, Built, Nature Valley, Atkins, think!, Larabar, Kirkland, David, Power Crunch, FITCRUNCH, Lenny & Larry's, Perfect Bar, IQ Bar, Aloha, GoMacro, NuGo. (`BIG_BRANDS` in kyb_guide_lib.py; Clif ZBar is not on it.)
No Cow stays off the list (smaller distribution). It's eligible as a small/independent pick in "Brands that do it well."

## Authorship / About page — LOCKED, shipped 2026-09-29
- `about.html` ("Who's behind Know Your Bar"), written in Jeff's first person. Jeff is a regular consumer who eats these bars and started researching them. He's not a dietitian or medical professional, and nothing on the site is medical advice. The page covers how the data is built (AI-assisted tooling, reviewed; a rule-based score; the score's limits and the grades-only rule), independence (no paid placements, no sponsored picks, one algorithm for every bar), and how the site makes money (affiliate links; commissions never affect a grade or rank). Schema: AboutPage + Person + BreadcrumbList. In sitemap.xml.
- **Needs Jeff's rewrite (2026-09-30):** about.html says "commissions never change a rank" / "Commissions never affect a grade or a rank." With the buy-link tiebreak, a link now breaks exact ties in the Best 10. The v2 criteria section says this plainly; the About copy should too.
- ~~Byline under the hero~~: **moved (Jeff, 2026-09-29: it read like a blog).** v2 guides now carry one quiet author line at the very bottom of the page (`byline_html()`, section 13 above). Article `author` = Person Jeff Booth with `url` https://knowyourbar.com/about. Publisher stays Organization.
- Jeff is rewriting the About page copy himself.
- A dietitian review on the diabetes / GLP-1 guides is parked for later.

## Build mechanics (kyb_guide_lib.py, v2 section)
- `build_guide_page_v2()` migrates a v1 page on its first run (`v2_shell()`: keeps the head, nav and footer as deployed, replaces the body with the v2 skeleton, removes the v1 inline JS and the `gd-bar-data` blob). After that, it only rewrites `<!-- kyb:NAME -->` regions. Rebuilding with unchanged data gives a byte-identical page. The head is kept as deployed, including any page-scoped inline `<style>` (diabetics still carries its unused v1 `.diab-*` rules; never strip CSS with regex).
- Every v2 builder calls `set_tie_seed('<page slug>')` right after `PUBLISHED`, before any pick is computed.
- Slot building blocks: `slot_best_overall`, `slot_cleanest`, `slot_highest_protein(cal_cap)`, `slot_protein_per_cal`, `slot_lowest_calorie`, `slot_big_brand`, `slot_lowest_sugar`, `slot_highest_fiber`, `slot_subset(label, rule, test, why, floor)`, and `Slot(...)` for anything custom (the tightened "Lowest sugar, no sugar alcohol" slot and "Lowest net carbs" are local `Slot`s in their builders). `pick_best10(qualify, slots, fallbacks)` applies the guardrails.
- Editorial helpers: `v2_count_card_html()`, `section_cta_html()`, `lead_sweetener()` / `brand_sweetener()` (V2_SWEETENERS).
- Styles: the "2026-09-29 Guide page v2" and "Guide v2, QA pass 2" blocks appended at the end of style.css. No CSS changes were needed for the second rollout, clean or diabetics.
- `v2_shell_upgrade()` brings an already-migrated page up to the current body (drops the glance section, adds the author region).
- Buy clicks: the cards use `.pick-tile`, the Top 50 uses `.bar-row` and the tables use `table.brand-table`, so analytics.js reports them (`top_picks`, `table_row`, `expanded_row`, `summary_table`) without changes.
- How to migrate a guide: copy the closest migrated builder (sweetener guides: build_no_artificial_sweeteners.py; certification guides: build_gluten_free_protein_bars.py; ingredient-screen guides: build_no_seed_oils.py; multi-condition / macro screens: build_clean_protein_bars.py or build_best_bars_for_diabetics.py), keep the guide's own claims/checks, set the tie seed, and point it at `build_guide_page_v2()`. Macro screens can often match the Bar Finder with slider params (`protein`, `cal`, `fat`, `carbs`, `sugar`, `sa`, `fiber`, `netcarbs`); port app.js's filter and check key for key.

## Open items
- Done 2026-09-29: guide hero alignment and the Bar Finder Max Net Carbs slider; no-artificial-sweeteners, gluten-free, no-seed-oils on v2; scoring v13.
- Done 2026-09-30: clean on v2; buy-link tiebreak + per-guide shuffle; database 41 (Jacked Granny reformulation); diabetics, keto, glp1, vegan and dairy-free on v2; database 42 (Aloha marked vegan); soy-free, kosher and high-fiber on v2.
- **Min Fat slider** in the Bar Finder (parked, Jeff 2026-09-30): add a min-fat slider entry to `SLIDERS_CFG` and a key to both `sliderMap`s, then switch keto's button to an exact link (`...&fatmin=8`).
- **Clean Ingredients preset** (Jeff wants it fixed): redefine `PRESETS.clean` in app.js to match the clean guide (A or B, no artificial sweeteners, no seed oils via `hasSeedOil()`), then update the ~10 pages whose link labels describe the old behavior ("Browse A-Grade bars" on ingredient_scoring, "A-grade bars only" on quest-vs-rxbar, the homepage FAQ via build_index.py, KIND's "No Sugar Alcohols or Artificial Sweeteners", rxbar/clif/barebells/quest discover links, ingredient-report, all-protein-bar-brands via build_brand_rankings.py, and the no-artificial-sweeteners and clean "stricter filter" buttons). One session, sitewide, with Jeff's sign-off. After it, clean's finder link can become `?preset=clean`.
- **Rollout complete (2026-09-30):** all fifteen guides are on v2 (caffeine and creatine last). kyb_cert_guide.py and kyb_dose_guide.py have no users left.
- **Caffeine / creatine Bar Finder toggles** (parked): a "Has caffeine" / "Has creatine" filter would let both pages link to an exact list.
- "Best from a big brand" card copy says "most grocery stores", which doesn't fit Kirkland (Costco); on gluten-free and diabetics. Ask Jeff before changing the lib wording (it changes both pages).
- Add the About link to the shared footer on every other page (the thirteen v2 guides and about.html have it). Hand-edit or propagate carefully: never a regex across all pages.
- Add /about and the byline to llms.txt (build_llms_txt.py). While there: llms.txt still says "Full list:" for the v2 guides, which now show a Best 10 + Top 50.
