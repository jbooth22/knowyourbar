# knowyourbar.com — Deployment Guide

---

## Standard Bar Database Update

Use this when adding new bars, updating affiliate links, or fixing ingredient data.

**Required: upload both files to Claude every time.**

1. Update your bar database Excel (add bars, fix ingredients, add affiliate links)
2. Upload both files to Claude:
   - Your bar database Excel (e.g. `KYB - New Protein Bar Database (2026).xlsx`)
   - `knowyourbar_scoring_schema_v3.xlsx`
3. Say "run score_and_export"
4. Claude will output `bars.js` — download it
5. If the bar count changed, Claude will also update `index.html` and all HTML pages with the new count — download those too
6. Upload changed files to GitHub — Cloudflare deploys in ~60 seconds

**Why both files every time?** The schema contains canonical ingredient scores and pre-parsed ingredient lines. Without it, auto-scoring is used for all bars. With it, schema-matched bars get deterministic scores that match the authoritative ingredient database.

**Schema file name matters:** The file must be `knowyourbar_scoring_schema_v3.xlsx` — not an older version. The v3 schema has 1,047 canonicals and 2,021 aliases.

---

## Files and What Changes Together

| What changed | Files to upload |
|---|---|
| Bar database only (new affiliate links, minor data fixes) | `bars.js` |
| Bar count changed | `bars.js` + all `.html` files |
| New bars added | `bars.js` + all `.html` files |
| New brand page added | new `brand.html` + `sitemap.xml` + all pages (nav update) |
| Filter logic or preset changed | `app.js` |
| Visual/layout change | `style.css` + any affected `.html` files |
| Scoring schema updated | `bars.js` (re-run full pipeline after schema changes) |

---

## Full File List (what goes in GitHub)

```
index.html
style.css
app.js
bars.js
bar_hero.png
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
```

The Excel database and scoring schema are NOT in the repo. Keep them locally.

---

## Adding a New Brand Review Page

1. Run the full pipeline first (get a fresh `bars.js`)
2. Tell Claude: "Generate a brand review page for [Brand Name]"
3. Claude produces the HTML with bar table, grade chart, scoring note, and FAQ
4. Download the new HTML file
5. Update the nav on ALL existing pages (the dropdown links to brand pages are inline in each HTML file)
6. Add the new page to `sitemap.xml`
7. Upload all changed files to GitHub
8. Request indexing in Google Search Console

---

## Adding a New SEO Guide Page

Similar to brand pages:

1. Tell Claude: "Build an SEO guide page for [topic]" — Claude will pull real data from bars.js
2. Download the new HTML file
3. Update the nav Guides dropdown on all pages
4. Add to `sitemap.xml`
5. Upload and request indexing

---

## Updating the Scoring Schema

When adding new canonical ingredients or fixing scores:

1. Edit `knowyourbar_scoring_schema_v3.xlsx` — add rows to `Canonical_Ingredients` and `Alias_Map`
2. Save as `knowyourbar_scoring_schema_v3.xlsx` (keep the v3 name)
3. Upload both the updated schema and the bar database to Claude
4. Run "run score_and_export"
5. Review the grade distribution output — compare to previous (A=158, B=234, C=209, D=109, F=42)
6. Upload `bars.js` to GitHub

---

## Deployment Stack

| Component | Service |
|---|---|
| Hosting | Cloudflare Pages (free tier, auto-deploys from GitHub) |
| Repo | GitHub — jbooth22 |
| Domain | GoDaddy (DNS nameservers pointed to Cloudflare) |
| Analytics | GA4 — tag G-SW4MNP5W7J in index.html |
| SEO | Google Search Console — sitemap at /sitemap.xml |
| Fonts | Google Fonts — Syne, DM Sans, DM Mono |
| Charts | Chart.js v4.4.0 via jsDelivr CDN (clean-protein-bars.html only) |

---

## GitHub Upload Process (Current Manual Workflow)

1. Go to github.com — jbooth22 repo
2. For each file you're updating: click the file, click the pencil icon, paste new content, commit
   — OR — drag multiple files into the repo browser to upload them all at once
3. If a file won't update, delete it first then re-upload
4. Cloudflare detects the commit and deploys automatically (~60 seconds)
5. Check deployment status at cloudflare.com dashboard under Pages

**Planned improvement:** Set up local Git so you can run `git add . && git commit -m "..." && git push` instead. One-time setup, saves significant time on every multi-file update.

---

## Google Search Console

After uploading new or significantly changed pages:

1. Go to Search Console for knowyourbar.com
2. Paste the URL into the URL inspection bar at the top
3. Click "Request Indexing"
4. If new pages were added, re-submit sitemap.xml (Sitemaps section in left nav)

After a bar count or content update, requesting re-indexing on `index.html` and `clean-protein-bars.html` is worthwhile since those are the most crawled pages.

---

## Known Data Gaps

These bars are in the database but have no ingredient data — they show in the tool with no grade:

- Power Crunch | Chocolate Strawberry
- MET-Rx | Peanut Butter Granola
- MET-Rx | Chocolate Chip Granola
- MET-Rx | Mint Super Cookie

To fix: add ingredient lists to the spreadsheet, then run the pipeline.

Bars without affiliate links: ~202 of 756. Worth a targeted effort for high-traffic brands.

---

## Checklist After Any Update

- [ ] bars.js exported and uploaded
- [ ] Bar counts updated in all HTML files (or confirmed unchanged)
- [ ] No stale numbers in meta descriptions or page content
- [ ] New pages added to sitemap.xml
- [ ] Nav updated on all pages if new pages were added
- [ ] Google Search Console: indexing requested for changed pages
