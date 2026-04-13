# knowyourbar.com — Deployment Guide

---

## Standard Bar Database Update

Use this whenever you add bars, update affiliate links, or fix ingredient data.

### Step by step

1. Update your bar database Excel
2. Upload both files to Claude:
   - Your bar database Excel
   - knowyourbar_scoring_schema_v3.xlsx (in your GitHub repo)
3. Say "run score_and_export"
4. Download bars.js and upload to GitHub
5. If the bar count changed, update the count in all HTML files (search and replace)
6. Cloudflare deploys in ~60 seconds

### Running locally instead (if you ever set up Python)

```bash
python3 score_and_export.py \
    --db "KYB - New Protein Bar Database (2026).xlsx" \
    --schema "knowyourbar_scoring_schema_v3.xlsx"
```

Requires: pip install pandas openpyxl

---

## How the Pipeline Works (settled approach — do not change)

ALL bars are scored from raw ingredient text using a single unified code path.
Only Canonical_Ingredients and Alias_Map are loaded from the schema.
The schema's Ingredient_Lines and Products sheets are NOT used.

Sub-ingredients inside parentheses get 60% weight (they are present in smaller amounts than top-level ingredients). Every scored bar gets insight chips generated using the same logic.

This approach was settled after multiple sessions of iteration. If a future Claude session suggests reverting to schema pre-parsed scoring, refer it to this document.

---

## Files and What Changes Together

| What changed | Files to upload |
|---|---|
| New bars or affiliate links | bars.js |
| Bar count changed | bars.js + all .html files |
| Filter logic, presets, similar bars, rank | app.js |
| Visual changes | style.css + affected .html files |
| New brand page added | new .html + sitemap.xml + all pages (nav) |
| Scoring schema updated | Re-run pipeline, then bars.js |

---

## Full File List (GitHub repo)

```
index.html
style.css
app.js
bars.js
bar_hero.png
score_and_export.py
sitemap.xml
robots.txt
README.md
DEPLOY.md
quest-bars.html
rxbar-review.html
clif-bar-review.html
barebells-review.html
clean-protein-bars.html
ingredient_scoring.html
knowyourbar_scoring_schema_v3.xlsx
```

Files NOT in the repo (keep locally):
- KYB - New Protein Bar Database (2026).xlsx

---

## Adding a New Brand Review Page

1. Run pipeline first (get fresh bars.js)
2. Tell Claude: "Generate a brand review page for [Brand Name]"
3. Download the HTML
4. Update the nav dropdown on ALL existing pages (nav is inline in each HTML file)
5. Add to sitemap.xml
6. Upload all changed files
7. Request indexing in Google Search Console

---

## Adding a New SEO Guide Page

1. Tell Claude: "Build an SEO guide page for [topic]"
2. Download the HTML
3. Update the nav Guides dropdown on all pages
4. Add to sitemap.xml
5. Upload and request indexing

---

## Updating the Scoring Schema

When adding new canonical ingredients or fixing scores:

1. Edit knowyourbar_scoring_schema_v3.xlsx
   - Add rows to Canonical_Ingredients
   - Add rows to Alias_Map
2. Upload updated schema + bar database to Claude
3. Say "run score_and_export"
4. Compare grade distribution to current (A=86 B=282 C=266 D=158 F=21)
5. Upload bars.js

---

## Deployment Stack

| Component | Service |
|---|---|
| Hosting | Cloudflare Pages (free tier, auto-deploys from GitHub) |
| Repo | GitHub — jbooth22 |
| Domain | GoDaddy (DNS pointed to Cloudflare) |
| Analytics | GA4 — G-SW4MNP5W7J (in index.html) |
| Fonts | Google Fonts — Syne, DM Sans, DM Mono |
| Charts | Chart.js v4.4.0 via jsDelivr CDN (clean-protein-bars.html only) |

---

## GitHub Upload (Current Manual Workflow)

1. Go to github.com — jbooth22 repo
2. Drag updated files into the repo browser
3. Cloudflare detects the commit and deploys (~60 seconds)
4. Check status at cloudflare.com under Pages

Planned: Set up local Git so deployment is git add . && git commit -m "..." && git push.

---

## After Any Update — Checklist

- [ ] bars.js exported and uploaded
- [ ] Bar count updated in all HTML files if it changed
- [ ] sitemap.xml updated if new pages were added
- [ ] Nav updated on all pages if new pages were added
- [ ] Google Search Console: request indexing for changed pages

---

## Google Search Console

After uploading new or changed pages:
1. Go to Search Console for knowyourbar.com
2. Paste URL into the inspection bar
3. Click "Request Indexing"
4. Re-submit sitemap.xml if new pages were added (Sitemaps section)

---

## Known Data Gaps

Bars with missing ingredient data (show in tool with no grade):
- Power Crunch | Chocolate Strawberry
- MET-Rx | Peanut Butter Granola
- MET-Rx | Chocolate Chip Granola
- MET-Rx | Mint Super Cookie

Bars without affiliate links: ~263 of 817.
