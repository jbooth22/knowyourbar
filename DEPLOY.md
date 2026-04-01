# knowyourbar.com — Deployment Guide

---

## Standard Update (New Bars or Affiliate Links)

1. Update your bar database Excel (add bars, affiliate links, ingredient data)
2. Upload bar database Excel + `knowyourbar_scoring_schema.xlsx` to Claude
3. Say "run score_and_export"
4. Download `bars.js` from Claude's output
5. If new brands were added, also download updated `app.js`
6. If the bar count changed significantly, also download updated `index.html` (meta description)
7. Upload files to GitHub — Cloudflare deploys in ~60 seconds

---

## Brand Page Update

Brand pages should be regenerated any time bars.js is significantly updated.

1. Complete the standard update above first (get fresh bars.js)
2. Tell Claude "regenerate brand pages"
3. Download the four HTML files: `quest-bars.html`, `rxbar-review.html`, `clif-bar-review.html`, `barebells-review.html`
4. Download updated `sitemap.xml` if new pages were added
5. Upload all files to GitHub
6. In Google Search Console, re-request indexing for updated pages

---

## Adding a New Brand Review Page

1. Complete the standard update to get fresh bars.js
2. Tell Claude "generate a brand page for [Brand Name]" — provide the brand's exact name as it appears in the database
3. Add the page config to `BRAND_CONFIGS` in the generator (Claude will do this)
4. Download the new HTML file
5. Update `sitemap.xml` with the new URL
6. Add a footer link in `index.html` pointing to the new page
7. Upload all changed files to GitHub
8. Request indexing in Google Search Console

---

## Deployment Stack

| Component | Service | Notes |
|---|---|---|
| Hosting | Cloudflare Pages | Free tier, auto-deploys from GitHub |
| Repo | GitHub | Push files directly via web UI |
| Domain | GoDaddy | DNS nameservers pointed to Cloudflare |
| Analytics | GA4 | Tag G-SW4MNP5W7J in index.html |
| SEO | Google Search Console | Sitemap at /sitemap.xml |

---

## Files That Change Together

When you update `bars.js`, check if these also need updating:

| Changed | Also update |
|---|---|
| Bar count increased significantly | `index.html` meta description count |
| New brands added | `app.js` BRAND_LIST array |
| New brand pages added | `sitemap.xml`, `index.html` footer links |
| Scoring logic changed | All brand review pages (regenerate) |

---

## GitHub Upload Tips

- You can upload multiple files at once by dragging them into the GitHub file browser
- If a file does not appear updated after uploading, delete it from GitHub first then re-upload (clears a caching quirk)
- Cloudflare typically deploys within 60 seconds of a GitHub push
- Check deployment status at cloudflare.com dashboard under Pages

---

## Google Search Console

After uploading new or significantly changed pages:

1. Go to Search Console for knowyourbar.com
2. Paste the full URL into the inspection bar at the top
3. Click "Request Indexing"
4. Re-submit sitemap.xml if new pages were added (Sitemaps section in left nav)

Pages typically get indexed within a few days to a week after requesting.
