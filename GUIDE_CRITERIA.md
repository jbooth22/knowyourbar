# Guide Page Criteria — Canonical Reference

**Purpose:** every guide page states a filtering formula and a qualifying count. Numbers have drifted from the formulas before (see Keto incident below). This doc is the single source of truth for what each guide actually filters on, so counts can be regenerated correctly whenever the database updates instead of being hand-typed or copied from a prior version.

**Global rule:** never state the total database size as an exact number (e.g. "983 bars," "1,048 bars") anywhere in copy, meta tags, or JSON-LD. Always use **"1,000+"** for the total. Specific qualifying counts per guide (e.g. "714 bars qualify") are fine and should stay specific — they're the credibility-building detail. Only the denominator gets the "1,000+" treatment.

**Live count as of this doc:** 1,028 bars in `bars.js`, 133 distinct brands. Re-check both whenever `bars.js` is regenerated — see "How to regenerate" below.

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
| Best Bars for Diabetics | `Sugars (g)` ≤ 5 AND net carbs ≤ 10 AND `Dietary Fiber (g)` ≥ 5 AND `Protein (g)` ≥ 10 AND `score_band` in (A, B) AND ingredients do not contain "maltitol" | 64 | 6% |
| GLP-1 Bars | `Protein (g)` ≥ 15 AND `Calories` < 200 AND `Sugars (g)` < 4 AND `Dietary Fiber (g)` ≥ 3 AND no `Sugar Alcohols` tag | 26 | 3% |
| **Keto** | net carbs ≤ 8 AND `Protein (g)` ≥ 10 AND `Total Fat (g)` ≥ 8, where **net carbs = Total Carbohydrates − Dietary Fiber − Sugar Alcohol** | **109** | **11%** |

Note: rows above other than Keto were pulled from each page's own stated criteria and cross-checked for plausibility against the prior (983-bar) published numbers — the deltas are consistent with normal database growth (983 → 1,028 bars added over time), not formula errors. Keto is confirmed broken; the rest are just due for a routine refresh.

### `score_insights` tag vocabulary (from `bars.js`)
Used by the tag-based filters above. Current tags in the live export:
`Artificial Sweeteners`, `Collagen Protein`, `Fortified`, `Long Ingredient List`, `Processed Oils`, `Protein Leads`, `Quality Protein Source`, `Short Clean List`, `Sugar Alcohols`, `Sweetener Heavy`, `Whole Food Forward`

### Net carbs formula (used by Keto; relevant to any future net-carb guide)
```
net_carbs = Total Carbohydrates (g) − Dietary Fiber (g) − Sugar Alcohol (g)
```
All three fields come straight off the nutrition panel data in `bars.js`. Do not compute net carbs as just `carbs − fiber` — sugar alcohols matter and dropping them is what broke Keto.

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
