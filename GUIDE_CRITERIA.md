# Guide Page Criteria — Canonical Reference

**Purpose:** every guide page states a filtering formula and a qualifying count. Numbers have drifted from the formulas before (see Keto incident below). This doc is the single source of truth for what each guide actually filters on, so counts can be regenerated correctly whenever the database updates instead of being hand-typed or copied from a prior version.

**Global rule:** the site-wide "never state the exact database size, always '1,000+'" rule now lives in `BRIEFING.md`'s Locked Global Rules section (moved there 2026-08-09 so it's visible in every session, not just guide-page sessions — it was previously only here, which is why a brand-page session had no way to know about it). This file covers only what's specific to guide pages: qualifying counts per guide, which stay specific ("714 bars qualify") and are the credibility-building detail — only the total-database denominator gets the "1,000+" treatment.

**Live count as of this doc:** 1,181 bars in `bars.js`, 165 distinct brands as of the last time this line was updated (2026-08-19). Treat this as a snapshot, not a live value — re-check with `bars.js` directly (or `verify_brand_data.py`/`diff_bars_upload.py`) whenever it matters, rather than trusting this number. It will go stale the moment the database changes and nobody is required to update this line.

---

## The Keto incident (why this doc exists)

`keto-protein-bars.html` stated "469 of 983 bars qualify" for months. The actual formula on the page (≤8g net carbs, ≥10g protein, ≥8g fat, where net carbs = total carbs − fiber − sugar alcohols) run against the live database returns **109 bars**, not 469. There's no plausible database-growth story that explains a 4x gap — the number was wrong from whenever it was first written, not stale. Root cause unknown; likely typed by hand or copied from an earlier, differently-defined version of the guide. Fixed August 2026.

**Lesson:** any time a guide's qualifying count is touched, recompute it from `bars.js` using the formula below rather than trusting the existing number, even if it "looks about right."

---

## Per-guide filter definitions (verified against 1,028-bar live data)

| Guide | Filter | Live count | % of DB |
|---|---|---|---|
| No Sugar Alcohols | `score_insights` does NOT contain `Sugar Alcohols` | 729 | 71% |
| No Artificial Sweeteners | `score_insights` does NOT contain `Artificial Sweeteners` | 810 | 79% |
| No Seed Oils | `score_insights` does NOT contain `Processed Oils` | 587 | 57% |
| Clean Protein Bars | `score_band` in (A, B) AND no `Artificial Sweeteners` tag AND no `Processed Oils` tag | 351 | 34% |
| Low Sugar + High Protein | `Sugars (g)` ≤ 5 AND `Protein (g)` ≥ 15 | 265 | 26% |
| Best Bars for Diabetics | `Sugars (g)` ≤ 5 AND net carbs ≤ 10 AND `Dietary Fiber (g)` ≥ 5 AND `Protein (g)` ≥ 10 AND `score_band` in (A, B) AND ingredients do not contain the maltitol family (see below) | 104 | 8.8% |
| GLP-1 Bars | `Protein (g)` ≥ 15 AND `Calories` ≤ 200 AND `Sugars (g)` ≤ 4 AND `Dietary Fiber (g)` ≥ 3 AND `Sugar Alcohol (g)` = 0 AND `score_band` in (A, B) | **28** | **2.4%** |
| **Keto** | net carbs ≤ 8 AND `Protein (g)` ≥ 10 AND `Total Fat (g)` ≥ 8 AND ingredients do not contain the maltitol family (see below), where **net carbs = Total Carbohydrates − Dietary Fiber − Sugar Alcohol** | **97** | **8.2%** |

Note: rows above other than Keto and Diabetics were pulled from each page's own stated criteria and cross-checked for plausibility against the prior (983-bar) published numbers — the deltas are consistent with normal database growth (983 → 1,028 bars added over time), not formula errors. These are still due for a routine refresh against 1,181-bar data; `low-sugar-high-protein.html` in particular has not been touched since 2026-04-01, predating the v5/v6/v7 scoring pipeline fixes, so its published count should be treated as unreliable until refreshed, not just stale.

**Best Bars for Diabetics was recomputed against the 1,181-bar live database on 2026-08-18** (schema v7) as part of the guide's rev 8 rebuild — 104 of 1,181 bars qualify (8.8%).

**Keto was recomputed against the 1,181-bar live database on 2026-08-18** (schema v7) as part of the guide's rev 8 rebuild — 97 of 1,181 bars qualify (8.2%). This is a formula change, not just a data refresh: the old Keto page (and the row above prior to this update) used net carbs + protein + fat only, with no maltitol screen. Adding the maltitol-family exclusion (same logic as Diabetics, see below) drops the qualifying count from 127 to 97 — 30 bars hit the macro thresholds on paper but still contain maltitol, mostly Barebells and FITCRUNCH flavors. Jeff signed off on applying the exclusion (2026-08-19): narrower and more defensible is the right tradeoff here. Both this row and the Diabetics row are current as of that date; the other rows in this table are not.

**GLP-1 was recomputed against the 1,181-bar live database on 2026-08-19/20** (schema v7) as part of the guide's rev 8 rebuild — 28 of 1,181 bars qualify (2.4%), verified against `app.js`'s canonical `glp1` preset formula. This is the narrowest guide on the site by both qualification rate and brand spread (8 brands with any qualifying flavor at all, 1 of which — Junkless — clears the relaxed Consider threshold). Note the sugar alcohol rule here is **stricter** than Keto/Diabetics: this guide hard-excludes ALL sugar alcohols (`Sugar Alcohol (g)` must equal exactly 0), not just the maltitol family. The rationale is different too — Keto/Diabetics exclude maltitol specifically because of its glycemic impact, while GLP-1 excludes sugar alcohols broadly because GI tolerance (bloating, gas, digestive discomfort) is the stated concern for people on GLP-1 medications, and that isn't a glycemic-index question. Do not reuse the maltitol-family-only check here if this guide is touched again — confirm against `app.js` first, since the two exclusion rules look similar but are not the same.

### `score_insights` tag vocabulary (from `bars.js`)
Used by the tag-based filters above. Current tags in the live export:
`Artificial Sweeteners`, `Collagen Protein`, `Fortified`, `Long Ingredient List`, `Processed Oils`, `Protein Leads`, `Quality Protein Source`, `Short Clean List`, `Sugar Alcohols`, `Sweetener Heavy`, `Whole Food Forward`

### Net carbs formula (used by Keto and Diabetics; relevant to any future net-carb guide)
```
net_carbs = Total Carbohydrates (g) − Dietary Fiber (g) − Sugar Alcohol (g)
```
All three fields come straight off the nutrition panel data in `bars.js`. Do not compute net carbs as just `carbs − fiber` — sugar alcohols matter and dropping them is what broke Keto. This is a **full subtraction, no halving** — do not divide `Sugar Alcohol (g)` by 2 anywhere in this formula. (BRIEFING.md previously had a stray note suggesting `Sugar Alcohol / 2`; that was wrong and has been corrected — this file is the source of truth for the formula.)

### Maltitol family exclusion (used by Diabetics and Keto; decided 2026-08-18, extended to Keto 2026-08-19)

We looked into whether net carbs should be adjusted per sugar-alcohol type (some sources suggest dividing by 2 for certain ones) instead of using one flat formula. Research into published glycemic index (GI) values for sugar alcohols showed:

| Sugar alcohol | GI (sucrose = 65, glucose = 100) |
|---|---|
| Mannitol | 0 |
| Erythritol | 0 |
| Lactitol | 6 |
| Sorbitol | 9 |
| Isomalt | 9 |
| Xylitol | 13 |
| Maltitol | 35 |
| Polyglycitol / hydrogenated starch hydrolysates (HSH) | 39 |

Six of the eight (mannitol, erythritol, lactitol, sorbitol, isomalt, xylitol) cluster tightly at GI 0–13 — close enough to negligible that the standard net carbs formula above already treats them fairly with no adjustment. Only **maltitol and its syrupy relatives (maltitol syrup, polyglycitol, hydrogenated starch hydrolysates)** stand out at a meaningfully higher GI (~35), roughly half of table sugar's impact.

**Decision: exclude rather than adjust.** Building a formula with different fractions for eight different molecules is more precision than we can responsibly claim as non-experts, and it invites errors. Instead, the Diabetics guide hard-excludes any bar whose ingredients contain the maltitol family. A hard exclude is something we can state with confidence; a per-molecule formula is not.

**Maltitol family exclusion check** (Diabetics and Keto guides) — ingredients string contains any of:
```
maltitol                              (also catches "maltitol syrup")
polyglycitol
hydrogenated starch hydrolysate       (substring also catches plural "hydrolysates")
```
Do not add a bare `hsh` abbreviation check — too high a false-positive risk against unrelated bracket text in ingredient strings. As of the 2026-08-18 database (1,181 bars), 200 bars contain a term in this list, all currently caught by "maltitol" alone — no bar yet uses polyglycitol or HSH without also listing maltitol/maltitol syrup. The broadened check is a forward-looking safeguard, not a change to today's qualifying count.

**Extended to Keto (2026-08-19):** the Keto rebuild reused this exact check rather than building a separate one, since Keto's net-carbs math has the same sugar-alcohol nuance as Diabetics. If a future guide also filters on net carbs, reuse this check again rather than writing a new one.

---

## How to regenerate these numbers

Whenever `bars.js` is updated (new bars added, reformulations, etc.), recompute every row in the table above rather than incrementing the old number. Rough approach (Python, using the exported `bars.js`):

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

# then apply each guide's filter from the table above
```

Update: the qualifying count on the page (hero stat, snapshot bar, H1 if it includes the number, title tag, meta description, og/twitter tags, JSON-LD), the disqualified count if stated, the qualifying percentage if stated, and any derived stats (avg protein/fat of the qualifying set, A-grade count within the qualifying set, brands represented within the qualifying set). Don't just swap the headline number and leave supporting stats stale — that's exactly how Keto ended up half-fixed before.

---

## Open item: brand count is inconsistent site-wide

Found while fixing Keto, not yet resolved. Three different "total brands" figures currently exist on the site:
- `all-protein-bar-brands.html`: states 125 brands
- `keto-protein-bars.html` JSON-LD Dataset description: states "95+ brands"
- Live count from `bars.js`: **133 distinct brands**

This needs a sweep across every page that states a brand count (probably the homepage, `all-protein-bar-brands.html`, and any JSON-LD Dataset blocks that repeat the same boilerplate description). Flagging here so it doesn't get lost — not yet fixed as of this doc.
