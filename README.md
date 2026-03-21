# knowyourbar.com — Project README & Claude Briefing

## What This Is
A protein bar search and filter tool at **knowyourbar.com**. Users can search, filter, and compare 446+ protein bars by macros, ingredients, and dietary certifications. The database is hand-researched by the owner and is the core proprietary asset of the site.

---

## Tech Stack
- **Plain HTML/CSS/JS** — no frameworks, no build process
- **Hosted on Cloudflare Pages** — free, auto-deploys when GitHub is updated
- **GitHub repo** — source of truth for all files
- **Domain** — knowyourbar.com, registered on GoDaddy, DNS managed by Cloudflare

---

## File Structure

| File | Purpose |
|---|---|
| `index.html` | Page structure, table headers, filter panel HTML |
| `style.css` | All design and layout, including mobile responsive rules |
| `app.js` | All filter/search/sort logic, table rendering, expand row |
| `bars.js` | The full bar database exported from Excel as a JS constant |
| `sitemap.xml` | Submitted to Google Search Console for indexing |
| `robots.txt` | Allows all crawlers, points to sitemap |
| `export_bars.py` | Python script to regenerate bars.js from updated Excel file |

---

## How to Update the Database

### Option A — Let Claude do it (easiest)
1. Upload the updated Excel file to Claude
2. Say "export a new bars.js from this"
3. Claude runs the export and provides a new `bars.js` to download
4. Upload `bars.js` to GitHub → Cloudflare auto-deploys in ~60 seconds

### Option B — Run locally
```bash
pip install pandas openpyxl
python3 export_bars.py
```
Place `export_bars.py` in the same folder as the Excel file. It outputs a fresh `bars.js`.

### After updating bars.js, also check:
- Did any **new brands** get added? If yes, update `BRAND_LIST` in `app.js`
- Did the **bar count** change? If yes, update the two hardcoded counts in `index.html` (hero and footer). Note: the JS also sets this dynamically from `BARS.length` so it self-corrects at runtime, but the HTML fallback should match.

### Excel file details
- Sheet name: `BarDB`
- 51 columns including all macros, vitamins, minerals, certifications, and ingredients
- Certification columns use "Yes" / null (not "No")

---

## Deployment Process
1. Make changes to files locally or via Claude
2. Go to GitHub repo → **Add file → Upload files**
3. Drag updated files in → **Commit changes**
4. Cloudflare Pages auto-deploys in ~60 seconds
5. Verify at knowyourbar.com

**Never need to touch Cloudflare directly** — just push to GitHub and it deploys automatically.

---

## Filter Panel (Left Sidebar)

### Brand Filter
- Scrollable checklist of all 43 brands (alphabetical)
- Has a "Filter brands…" search box to quickly narrow the list
- Multi-select — users can pick one or more brands
- Shows selected count and a Clear button when active
- `BRAND_LIST` array is hardcoded in `app.js` — must be updated manually when new brands are added

**Current brand list:**
Alani, Aloha, Anabar, Atlas, Barebells, Bob's Red Mill, Built, CLIF Bar, Clif Builders, Clif ZBar, Daryl's Bars, David, Epic, FITCRUNCH, Fiber One, Fulfil, Gatorade, Honey Stinger, IQ Bar, Jambar, Kize, Laird, Mezcla, Mosh, Munk Pack, Nick's, No Cow, NuGo, One, PROBar, Prima, Pure Protein, Quest, RXBAR, Raw Rev, Rise, Send, Simply Protein, The Gluten Free Brothers, Trubar, Zing, gomacro, think!

### Flavor Keyword Search
- Text input, matches against flavor name only (not brand name)
- Works in combination with brand filter

### Certifications
- Toggle chips: Vegan, GF, Dairy Free, Soy Free, Non-GMO, Nut Free, Kosher
- Must match ALL selected certs (AND logic)

### Macro Sliders
- Min Protein (g)
- Max Calories
- Max Sugars (g)
- Max Sugar Alcohol (g)
- Min Fiber (g)
- Max Sodium (mg)

### Ingredient Exclusion
- Text input — type an ingredient (e.g. "Glycerin", "Peanuts")
- Text-matches against the full ingredient list
- Multiple exclusions can be added as tags
- Bars containing ANY excluded ingredient are removed

---

## Table Columns

### Desktop column order (all visible):
CAL · PROT · FAT · CARB · FIBR · SGR · SGR ALC · CHOL · SODM · CERTS · [link]

### Mobile column order (4 visible, rest hidden):
PROT · FAT · FIBR · SGR

Hidden on mobile via `.col-hide-mobile` CSS class applied to both `<th>` and `<td>` elements. The hidden columns are: CAL, CARB, SGR ALC, CHOL, SODM, CERTS.

### Column key:
| Header | Field | Unit |
|---|---|---|
| CAL | Calories | — |
| PROT | Protein (g) | g |
| FAT | Total Fat (g) | g |
| CARB | Total Carbohydrates (g) | g |
| FIBR | Dietary Fiber (g) | g |
| SGR | Sugars (g) | g |
| SGR ALC | Sugar Alcohol (g) | g |
| CHOL | Cholesterol (mg) | mg |
| SODM | Sodium (mg) | mg |
| CERTS | Cert badges (GF, DF, SF, etc.) | — |

---

## Expand Row (click any bar to open)
Clicking a row expands it to show a full nutrition label. Layout is two-column on desktop, single column on mobile.

**Left column — Nutrition Facts panel:**
- All primary macros (Calories, Protein, Fat, Sat Fat, Trans Fat, Cholesterol, Sodium, Carbs, Fiber, Sugars, Sugar Alcohol, Potassium, Calcium, Iron, Caffeine)
- Highlighted in accent color: Calories, Protein, Fiber, Sugars, Sugar Alcohol
- Vitamins and minerals shown in a 2-column grid if data exists (many bars have nulls here)

**Right column:**
- Dietary cert badges (Vegan, Gluten Free, Dairy Free, etc.)
- "Visit product page ↗" button linking to brand website
- Full ingredient list (word-wrapped, no horizontal scroll)

---

## Design System

### Fonts
- **Syne** — display/headings (Google Fonts)
- **DM Mono** — labels, numbers, monospace elements (Google Fonts)

### Colors (CSS variables in style.css)
```css
--black: #0e0e0e
--white: #f7f5f0
--off-white: #efece6
--accent: #d4f000        /* electric yellow-green — used for highlights */
--muted: #888880
--border: #d6d3cc
--success-bg: #edfce4    /* cert badge backgrounds */
--success-text: #2a7a1f  /* cert badge text */
```

### Responsive breakpoints
- **900px** — filter panel moves from sidebar to top, hero shrinks
- **700px** — expand row stacks vertically, mobile column hiding activates

---

## Decisions Made & Rationale

| Decision | Rationale |
|---|---|
| Plain HTML/JS, no framework | Owner has no dev experience, simple = maintainable, no build process needed |
| Client-side filtering | All 446 bars load in bars.js, filtering happens in browser — no server needed, instant results |
| Brand multi-select checklist | Better mobile UX than autocomplete, native OS behavior on phones |
| Flavor keyword search separate from brand | Lets users find "chocolate" across all brands without conflating brand/flavor search |
| Mobile shows PROT/FAT/FIBR/SGR | Most nutrition-relevant for protein bar decisions; full data available in expand |
| No flavor category filter | Flavor names are combination flavors, categories would be too complex for limited value |
| Comparison feature deferred | Significant build; current expand row solves single-bar detail; comparison is Phase 2 |
| Ingredient exclusion over inclusion | More useful for dietary restrictions (exclude Glycerin, exclude Peanuts) |

---

## Planned Future Features
- **Comparison feature** — select 3–5 bars, view side by side in a full-screen grid. Triggered by a "+" button on each row, sticky tray at bottom, swipeable comparison view on mobile.
- **Per-bar SEO pages** — auto-generate individual pages for each bar (e.g. `/bars/quest-chocolate-chip-cookie-dough`) using Astro or similar. High SEO value.
- **Metrics** — owner plans to add calculated columns (e.g. protein per calorie) to the Excel database directly
- **Monetization** — Amazon affiliate links, brand affiliate programs, eventually sponsored placements
- **Google Analytics** — not yet installed, Search Console is set up

---

## Google / SEO Status
- Google Search Console: verified and sitemap submitted
- Sitemap: https://knowyourbar.com/sitemap.xml
- Indexing: in progress (site is new)

---

## How to Brief Claude in a New Conversation

Paste this README and say something like:

> "I'm working on knowyourbar.com — a protein bar finder site. Here's the README with full context. I need to [describe what you need]."

Then attach any relevant files (index.html, app.js, style.css) if you need code changes. Claude can read and edit them directly.
