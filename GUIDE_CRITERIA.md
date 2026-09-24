# Guide Page Criteria — Canonical Reference

**Purpose:** every guide page states a filtering formula. This doc is the single source of truth for what each guide actually filters on — the formula only. Qualifying counts, percentages, and "recomputed on [date]" notes do not belong here; they go stale the moment `bars.js` changes and nobody is required to update them. Current qualifying counts per guide live in `BRIEFING.md`'s guide-status section, which gets updated at the end of each refresh session.

**Global rule:** the site-wide "never state the exact database size, always '1,000+'" rule lives in `BRIEFING.md`'s Locked Global Rules section. This file covers only the filter logic itself.

---

## The Keto incident (why this doc exists)

`keto-protein-bars.html` once stated a qualifying count that was roughly 4x the number the page's own stated formula actually returned when run against the live database. There's no plausible database-growth story that explains a 4x gap — the number was wrong from whenever it was first written, not stale. Root cause unknown; likely typed by hand or copied from an earlier, differently-defined version of the guide.

**Lesson:** any time a guide's qualifying count is needed, recompute it from `bars.js` using the formula below rather than trusting a previously-published number, even if it "looks about right." Never hand-type or copy-paste a count. This file exists so the formula itself never has to be reconstructed from a live page's copy — copy it from here instead.

---

## Per-guide filter definitions

| Guide | Filter |
|---|---|
| No Sugar Alcohols | `score_insights` does NOT contain `Sugar Alcohols` AND ingredients do not name IMO (isomalto-oligosaccharides). Code: `has_sugar_alcohol()` in kyb_guide_lib.py (2026-09-24) |
| No Artificial Sweeteners | `score_insights` does NOT contain `Artificial Sweeteners` |
| No Seed Oils | `score_insights` does NOT contain `Processed Oils` |
| Clean Protein Bars | `score_band` in (A, B) AND no `Artificial Sweeteners` tag AND no `Processed Oils` tag |
| Low Sugar + High Protein | `Sugars (g)` ≤ 5 AND `Protein (g)` ≥ 15 |
| Best Bars for Diabetics | `Sugars (g)` ≤ 5 AND net carbs ≤ 10 AND `Dietary Fiber (g)` ≥ 5 AND `Protein (g)` ≥ 10 AND `score_band` in (A, B) AND ingredients do not contain the maltitol family (see below) |
| GLP-1 Bars | `Protein (g)` ≥ 15 AND `Calories` ≤ 200 AND `Sugars (g)` ≤ 4 AND `Dietary Fiber (g)` ≥ 3 AND `Sugar Alcohol (g)` = 0 AND no sugar alcohol in the ingredients (`has_sugar_alcohol()`, same screen as No Sugar Alcohols) AND `score_band` in (A, B) |
| Keto | net carbs ≤ 8 AND `Protein (g)` ≥ 10 AND `Total Fat (g)` ≥ 8 AND ingredients do not contain the maltitol family (see below), where net carbs = Total Carbohydrates − Dietary Fiber − Sugar Alcohol |
| Caffeine | `Caffeine (mg)` > 0 (any declared amount qualifies, no minimum dose or ingredient-quality gate) |
| Vegan | `Vegan (Y/N)` = Yes (the bars.js certification field, not a computed screen, no macro or ingredient-quality gate) |
| Gluten Free | `Gluten Free (Y/N)` = Yes (the bars.js certification field, not a computed screen, no macro or ingredient-quality gate, same pattern as Vegan) |
| Dairy Free | `Dairy Free (Y/N)` = Yes (the bars.js certification field, not a computed screen, no macro or ingredient-quality gate, same pattern as Vegan/Gluten Free) |
| Soy Free | `Soy Free (Y/N)` = Yes (the bars.js certification field, not a computed screen, no macro or ingredient-quality gate, same pattern as Vegan/Gluten Free/Dairy Free). Category-explainer section (informational only, does not affect qualification) cross-checks the disqualified set for three named soy sources: soy protein (`soy protein\|textured soy\|soy flour\|isolated soy protein\|proteins?\s*\(soy\b\|\(soy,` — the last two alternatives catch "plant protein(s) (soy, pea, rice, ...)" blend labels), soy lecithin (`soy lecithin\|lecithins?\s*\(soy\)` — the second alternative catches reversed-order labeling common on imported/European-formatted bars, e.g. "lecithin (soy)"), and soybean oil (`soybean oil\|soy oil`). A bare `\bsoy\b` catch-all was tested and dropped: on the 2026-09-17 build (1,307 bars) it only ever fired on top of the three named checks above, except for one "may contain ... wheat, and soy" cross-contact allergen disclaimer (Honey Stinger Chocolate Chocolate Chip), which correctly falls into the unlabeled bucket rather than being counted as a real soy ingredient. **Do not describe soy protein or soy lecithin as "concern" ingredients when writing copy for this guide** — checked against `knowyourbar_scoring_schema_v11.xlsx`'s Canonical_Ingredients sheet: soy protein isolate scores +3, soy protein +2, soy protein concentrate +2 (all positive, protein/plant_protein), soy lecithin scores 0 (neutral, emulsifier); only soybean oil scores -1 (fat_oil/refined_or_seed_oil, same bucket as other seed oils). Soy free bars grade A/B at a notably higher rate than the database average (73.4% vs. 57.7% on the 2026-09-17 build), but that's correlation, not the soy screen itself: soy free bars also carry artificial sweeteners and processed oils at much lower rates than the database as a whole. Don't attribute the grade gap to soy protein/lecithin being penalized — they aren't. |
| High Fiber (three tiers) | `Dietary Fiber (g)` >= 5 (High Fiber), >= 8 (Very High Fiber), >= 11 (Extreme Fiber). Cumulative cutoffs on the same field, not three separate screens — every Extreme Fiber bar also counts as Very High Fiber and High Fiber. No macro or ingredient-quality gate beyond the fiber threshold itself. `high-fiber-protein-bars.html` leads with the Extreme Fiber (11g+) tier as its primary ranked list and main brand tables; High Fiber and Very High Fiber are presented as supporting context in a section inserted at the guide's standard GSC-keyword-gap insertion point (see "Template section order" in BRIEFING.md). The 5g cutoff matches the FDA's own "excellent source of fiber" labeling threshold — cite that as the rationale for where the High Fiber tier starts, don't invent a different justification. |

| Kosher | `Kosher (Y/N)` = Yes (the bars.js certification field, not a computed screen, no macro or ingredient-quality gate). Structurally different from Vegan/Gluten Free/Dairy Free/Soy Free: kosher is a supervised-process certification, not primarily an ingredient screen, so most ingredients (whey, milk, soy, wheat, sugar, nuts) don't disqualify a bar by their mere presence. Category-explainer section cross-checks the disqualified set for three ingredients that are almost never kosher without their own certification: gelatin (`\bgelatin\b`, 77 bars on the 2026-09-17 build, usually pork- or non-ritually-slaughtered-animal-derived), confectioner's glaze/shellac (`shellac\|confectioner.?s glaze`, 14 bars, an insect-derived coating resin), and a combined Other bucket for carmine/cochineal and rennet (`\bcarmine\b\|cochineal\|\brennet\b`, 5 bars). On the 2026-09-17 build, only ~7.6% of the 1,158 non-kosher bars contain any of these three factors; the other ~92% simply haven't pursued certification, which is the opposite pattern from Dairy Free/Soy Free (where a majority of the disqualified set has an identifiable disqualifying ingredient). Kosher bars do NOT grade meaningfully higher or lower than the database average (54.4% vs. 57.7% A/B rate on the 2026-09-17 build) — don't reuse Soy Free's "grades higher" framing for this guide, the two guides have genuinely different quality-correlation patterns. |

Note on sugar-alcohol screens: Keto and Diabetics exclude the maltitol family specifically (glycemic-index rationale, see below). GLP-1 is stricter and excludes ALL sugar alcohols (`Sugar Alcohol (g)` must equal exactly 0 AND the ingredient list must not name one; since 2026-09-24 the ingredient check is required because 75 bars named a sugar alcohol while declaring 0g or leaving the line blank) — the rationale there is GI tolerance (bloating, digestive discomfort), not glycemic index. Do not reuse the maltitol-only check for GLP-1 or vice versa; confirm against `app.js`'s canonical presets before reusing either check on a new guide.

### `score_insights` tag vocabulary (from `bars.js`)
Used by the tag-based filters above. Current tags in the live export:
`Artificial Sweeteners`, `Collagen Protein`, `Fortified`, `Long Ingredient List`, `Processed Oils`, `Protein Leads`, `Quality Protein Source`, `Short Clean List`, `Sugar Alcohols`, `Sweetener Heavy`, `Whole Food Forward`

### Net carbs formula (used by Keto and Diabetics; relevant to any future net-carb guide)
```
net_carbs = Total Carbohydrates (g) − Dietary Fiber (g) − Sugar Alcohol (g)
```
All three fields come straight off the nutrition panel data in `bars.js`. Do not compute net carbs as just `carbs − fiber` — sugar alcohols matter and dropping them is what broke Keto originally. This is a **full subtraction, no halving** — do not divide `Sugar Alcohol (g)` by 2 anywhere in this formula.

### Maltitol family exclusion (used by Diabetics and Keto)

Published glycemic index (GI) values for common sugar alcohols (sucrose = 65, glucose = 100):

| Sugar alcohol | GI |
|---|---|
| Mannitol | 0 |
| Erythritol | 0 |
| Lactitol | 6 |
| Sorbitol | 9 |
| Isomalt | 9 |
| Xylitol | 13 |
| Maltitol | 35 |
| Polyglycitol / hydrogenated starch hydrolysates (HSH) | 39 |

Six of the eight cluster tightly at GI 0–13 — close enough to negligible that the standard net carbs formula above already treats them fairly with no adjustment. Only maltitol and its relatives stand out at a meaningfully higher GI (~35), roughly half of table sugar's impact.

**Decision: exclude rather than adjust.** Building a formula with different fractions for eight different molecules is more precision than we can responsibly claim as non-experts. Instead, Diabetics and Keto hard-exclude any bar whose ingredients contain the maltitol family.

**Maltitol family exclusion check** — ingredients string contains any of:
```
maltitol                              (also catches "maltitol syrup")
polyglycitol
hydrogenated starch hydrolysate       (substring also catches plural "hydrolysates")
```
Do not add a bare `hsh` abbreviation check — too high a false-positive risk against unrelated bracket text in ingredient strings.

If a future guide also filters on net carbs, reuse this exact check rather than writing a new one.

### Gluten Free guide — gluten-source screen (category explainer content, not the qualification filter)

The qualification filter is just `Gluten Free (Y/N) = Yes` (see table above), same pattern as Vegan. The category-explainer section additionally cross-checks ingredient text for named gluten sources, purely to explain what's actually driving disqualification, this does not affect who qualifies:
```
wheat            (\bwheat\b, word-boundary — excludes "wheatgrass" style compounds)
barley / malt    (\bbarley\b, \bmalt extract\b, \bmalt syrup\b, \bmalted barley\b, \bbarley malt\b —
                  do NOT use a bare \bmalt\b check, it false-positives against maltitol and maltodextrin)
```
Compute both checks only against the DISQUALIFIED set (`Gluten Free (Y/N)` != Yes), not the full database — a bar can contain the word "wheat" in a "made in a facility that also processes wheat" cross-contact disclaimer while still being labeled gluten free itself, and that's a real case in the live data (Honey Stinger). Restricting the match to the disqualified set filters this out automatically without extra logic.

The remainder of the disqualified set (roughly 84% of it in the 2026-08-26 build) shows no wheat or barley in its own ingredient list at all — those bars simply haven't been labeled or certified gluten free by the brand, which is a different claim from actually containing gluten. Present this as its own explainer card ("Not labeled gluten free"), not folded into the Wheat or Barley counts, and don't claim or imply these bars contain gluten. If a future refresh changes bars.js, recompute this split fresh rather than reusing prior counts, same rule as every other guide.

Do not use a bare `oats` check as a disqualifying factor — oats are naturally gluten-free and only cross-contaminate during farming/milling; roughly 71% of oat-mentioning bars in the 2026-08-26 build are still labeled gluten free (several explicitly state "gluten-free oats"), so an oats-based screen would produce a majority-false-positive card.

---

## How to regenerate qualifying counts

Whenever `bars.js` is updated, recompute the qualifying count for whichever guide is being refreshed from scratch — never increment or copy a prior number. Rough approach (Python, using the exported `bars.js`):

```python
import json
with open('bars.js') as f:
    content = f.read()
arr = json.loads(content[content.index('['):content.rindex(']')+1])

def num(v):
    try: return float(v)
    except: return None

def net_carbs(b):
    c = num(b.get('Total Carbohydrates (g)'))
    if c is None: return None
    return c - (num(b.get('Dietary Fiber (g)')) or 0) - (num(b.get('Sugar Alcohol (g)')) or 0)

def tags(b):
    si = b.get('score_insights') or ''
    return set(p.split(':')[0].strip() for p in si.split('|') if p.strip())

# then apply the guide's filter from the table above
```

When updating a page, update every place the count appears: hero stat, snapshot bar, H1 (if it includes the number), title tag, meta description, og/twitter tags, JSON-LD, and any derived stats (avg protein/fat of the qualifying set, A-grade count within it, brands represented within it). Don't just swap the headline number and leave supporting stats stale — that's exactly how Keto ended up half-fixed before. Once the refresh is done, update the count in `BRIEFING.md`'s guide-status section — that's the only place a current count should live.

---

## Top Picks Selection (the 6-tile grid at the top of every guide)

### The problem this fixes

Through 2026-09-06, every guide's 6 "Top picks" tiles were selected as a
pure max/min of raw `ingredient_score` over the guide's qualifying set --
"Best overall" = highest raw score, etc. That's honest in the sense that
nothing was hand-picked, but `ingredient_score` is a -4 to +4 directional
per-ingredient scale, not deeply weighted and not quantity-aware --
comparing two bars' scores to the decimal claims more precision than the
scoring system has. In practice this meant one globally excellent bar
won "Best overall" (and often several other tiles) on nearly every guide
it qualified for, regardless of the guide's topic.

**This rule was documented but never actually shipped to the build scripts.**
Confirmed 2026-09-17: `build_dairy_free_protein_bars.py`, and by extension
the already-live `dairy-free-protein-bars.html`, `gluten-free-protein-bars.html`,
and `high-fiber-protein-bars.html` pages built from sibling scripts, all still
select tiles 2 through 6 as a pure max/min over the FULL qualifying set with
no band restriction. Found while building Soy Free: its unrestricted picks
included a D-grade "Best protein/calorie ratio" and a D-grade "Best total
protein" tile sitting right next to an A-grade "Best overall" tile on the
same page. `build_soy_free_protein_bars.py` and `build_kosher_protein_bars.py`
were the first to actually implement the band-restriction logic below. If a
future session refreshes Dairy Free, Gluten Free, or High Fiber, port this
fix over rather than assuming it's already there because this doc says so.

### The rule, applied fresh each time a guide is built or refreshed

1. **Band, not raw score, is the ingredient-quality signal.** Within the
   guide's qualifying set, find the best `score_band` actually present
   (usually A, sometimes B if none qualify at A). Treat every bar in
   that band as tied on ingredient quality -- per the scoring system's
   own precision, they are. Never pick a tile by comparing raw
   `ingredient_score` between two bars.
2. **Break the tie with a real, guide-specific number** -- net carbs for
   Keto, calories for GLP-1, caffeine mg for Caffeine, sodium or
   saturated fat for the free-from guides, and so on. Never break a tie
   with another ingredient-score comparison.
3. **Only one of the 6 tiles may be quality-anchored** ("Best overall").
   The other five must reference something actually distinctive about
   THAT guide's diet. If a category could be copy-pasted onto an
   unrelated guide with only the label swapped, replace it -- that
   genericness is exactly what caused the duplication above.
4. **No bar repeats across the 6 tiles on one guide.** Once a bar has
   filled a slot, exclude it from the rest of that guide's picks and
   move to the next-best bar in the band (fall back to allowing a
   repeat only if that leaves a category with nothing eligible -- a very
   small qualifying set). One flavor sweeping 4 of 6 tiles on a page is
   the same problem as the cross-guide version, just contained to one
   page.

That's the whole rule -- band, guide-specific tiebreak, no repeats on the
page. `build_soy_free_protein_bars.py` and `build_kosher_protein_bars.py`
both implement it with a `BAND_POOL` + `best_in_band()` helper (falls back
to the full qualifying set only when the top band has zero candidates for
a specific tile, e.g. Kosher's "Best for keto" tile, which had no A-grade
bar clearing the keto macro screen and fell back to B). Copy that pattern
rather than reinventing it.
