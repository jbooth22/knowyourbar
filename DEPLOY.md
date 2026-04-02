# knowyourbar.com — Deployment Guide

---

## Standard Update (New Bars or Affiliate Links)

**IMPORTANT: Always upload both files together.**

1. Update your bar database Excel (add bars, affiliate links, ingredient data)
2. Upload BOTH to Claude:
   - Your bar database Excel
   - `knowyourbar_scoring_schema.xlsx`
3. Say "run score_and_export"
4. Download `bars.js`
5. If new brands were added, also download `app.js`
6. If the bar count changed significantly, also download `index.html`
7. Upload to GitHub — Cloudflare deploys in ~60 seconds

**Why both files?** The schema Excel contains the canonical ingredient scores and pre-parsed ingredient lines. Without it, Claude rebuilds from a potentially stale cached state. With it, scores are fully reproducible and match the authoritative schema.

---

## Brand Page Update

Brand pages should be regenerated after any significant bars.js update.

1. Complete the standard update first (get fresh bars.js with both files)
2. Tell Claude "regenerate brand pages"
3. Download the four HTML files: `quest-bars.html`, `rxbar-review.html`, `clif-bar-review.html`, `barebells-review.html`
4. Upload to GitHub
5. Request indexing in Google Search Console for updated pages

---

## Adding a New Brand Review Page

1. Run the full scoring pipeline first
2. Tell Claude "generate a brand page for [Brand Name]"
3. Claude adds a config to `BRAND_CONFIGS` in the generator and produces the HTML
4. Download the new HTML file and updated `sitemap.xml`
5. Add a footer link in `index.html`
6. Upload all changed files to GitHub
7. Request indexing in Google Search Console

---

## Updating the Scoring Schema

When you want to add new canonical ingredients or fix scores:

1. Edit `knowyourbar_scoring_schema.xlsx` — add rows to `Canonical_Ingredients` and `Alias_Map`
2. Upload the updated schema + bar database to Claude
3. Run "run score_and_export" — all bars will be rescored with the new canonicals
4. Review the grade distribution to confirm expected changes
5. Upload bars.js to GitHub

**Known schema gaps to address (ingredients currently unmatched):**
- Palm Fruit Oil (11 bars) — suggest -1, fat_oil category
- Monkfruit Extract (8 bars) — suggest 0, sweetener category
- Agar (6 bars) — suggest 0, additive category
- Fructooligosaccharide (5 bars) — suggest +1, fiber_or_functional_carb category
- Hemp Seeds (4 bars) — suggest +3, whole_food category

---

## Files That Change Together

| Changed | Also update |
|---|---|
| Bar count increased significantly | `index.html` meta description count |
| New brands added | `app.js` BRAND_LIST array |
| New brand pages added | `sitemap.xml`, `index.html` footer links |
| Scoring logic or schema changed | All brand pages (regenerate), bars.js |

---

## Deployment Stack

| Component | Service |
|---|---|
| Hosting | Cloudflare Pages (free tier, auto-deploys from GitHub) |
| Repo | GitHub (upload via web UI) |
| Domain | GoDaddy (DNS nameservers pointed to Cloudflare) |
| Analytics | GA4 — tag G-SW4MNP5W7J in index.html |
| SEO | Google Search Console — sitemap at /sitemap.xml |

---

## GitHub Upload Tips

- Drag multiple files at once into the GitHub file browser
- If a file does not appear updated, delete it first then re-upload
- Cloudflare typically deploys within 60 seconds
- Check status at cloudflare.com dashboard under Pages

---

## Google Search Console

After uploading new or significantly changed pages:

1. Go to Search Console for knowyourbar.com
2. Paste the URL into the inspection bar
3. Click "Request Indexing"
4. Re-submit sitemap.xml if new pages were added (Sitemaps section in left nav)
