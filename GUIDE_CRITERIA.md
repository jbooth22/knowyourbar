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
| No Sugar Alcohols | `score_insights` does NOT contain `Sugar Alcohols` |
| No Artificial Sweeteners | `score_insights` does NOT contain `Artificial Sweeteners` |
| No Seed Oils | `score_insights` does NOT contain `Processed Oils` |
| Clean Protein Bars | `score_band` in (A, B) AND no `Artificial Sweeteners` tag AND no `Processed Oils` tag |
| Low Sugar + High Protein | `Sugars (g)` ≤ 5 AND `Protein (g)` ≥ 15 |
| Best Bars for Diabetics | `Sugars (g)` ≤ 5 AND net carbs ≤ 10 AND `Dietary Fiber (g)` ≥ 5 AND `Protein (g)` ≥ 10 AND `score_band` in (A, B) AND ingredients do not contain the maltitol family (see below) |
| GLP-1 Bars | `Protein (g)` ≥ 15 AND `Calories` ≤ 200 AND `Sugars (g)` ≤ 4 AND `Dietary Fiber (g)` ≥ 3 AND `Sugar Alcohol (g)` = 0 AND `score_band` in (A, B) |
| Keto | net carbs ≤ 8 AND `Protein (g)` ≥ 10 AND `Total Fat (g)` ≥ 8 AND ingredients do not contain the maltitol family (see below), where net carbs = Total Carbohydrates − Dietary Fiber − Sugar Alcohol |
| Caffeine | `Caffeine (mg)` > 0 (any declared amount qualifies, no minimum dose or ingredient-quality gate) |
| Vegan | `Vegan (Y/N)` = Yes (the bars.js certification field, not a computed screen, no macro or ingredient-quality gate) |
| Gluten Free | `Gluten Free (Y/N)` = Yes (the bars.js certification field, not a computed screen, no macro or ingredient-quality gate, same pattern as Vegan) |

Note on sugar-alcohol screens: Keto and Diabetics exclude the maltitol family specifically (glycemic-index rationale, see below). GLP-1 is stricter and excludes ALL sugar alcohols (`Sugar Alcohol (g)` must equal exactly 0) — the rationale there is GI tolerance (bloating, digestive discomfort), not glycemic index. Do not reuse the maltitol-only check for GLP-1 or vice versa; confirm against `app.js`'s canonical presets before reusing either check on a new guide.

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
