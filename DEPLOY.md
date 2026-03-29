# Know Your Bar — Deployment Guide

---

## Your Site Files

Files that live on GitHub and are served live:

```
index.html              The main page
style.css               All design and layout
app.js                  All filter/search/scoring logic
bars.js                 Full bar database (541 bars, ~1MB)
ingredient_scoring.html Scoring methodology page
bar_hero.png            Product bar image used in both page heroes
sitemap.xml             For Google Search Console
robots.txt              Crawler instructions
README.md               Project docs and Claude briefing
DEPLOY.md               This file
```

Files that stay on your computer only (never upload to GitHub):

```
knowyourbar_scoring_schema.xlsx    Master ingredient scoring schema
score_and_export.py                Scoring pipeline script
Your bar database Excel            Source of truth for all bar data
```

---

## Routine Update Workflow (Adding New Bars)

1. Add new bars to your Excel database (`BarDB` sheet)
2. Upload your Excel + `knowyourbar_scoring_schema.xlsx` to Claude
3. Say "run score_and_export"
4. Claude returns a new `bars.js`
5. If new brands were added, tell Claude — it will update `BRAND_LIST` in `app.js`
6. Upload `bars.js` (and `app.js` if changed) to GitHub
7. Cloudflare auto-deploys in ~60 seconds
8. Verify at knowyourbar.com

**If files don't update after uploading:** Delete the file from GitHub first, then re-upload. This clears a GitHub caching quirk.

---

## Uploading Files to GitHub

1. Go to your GitHub repo
2. Click **Add file** > **Upload files**
3. Drag files in
4. Click **Commit changes**

For large files like `bars.js` that GitHub may resist: click the existing file, then the pencil icon to edit, select all, paste new content, commit.

---

## Deployment Infrastructure

| Layer | Provider | Cost |
|---|---|---|
| Hosting | Cloudflare Pages | Free |
| CDN + SSL | Cloudflare | Free |
| Git source | GitHub (public repo) | Free |
| Domain | GoDaddy / Cloudflare DNS | ~$12/year |

GitHub push triggers Cloudflare Pages build automatically. No build command needed — plain HTML/JS deploys as-is.

---

## DNS Setup (already live, for reference)

- Domain registered on GoDaddy
- Nameservers pointing to Cloudflare
- Cloudflare Pages custom domain: knowyourbar.com
- www.knowyourbar.com redirects to root domain
- HTTPS automatic via Cloudflare

---

## Analytics

- GA4 tag in `index.html` (Measurement ID: G-SW4MNP5W7J)
- Google Search Console verified, sitemap submitted
- No additional configuration needed

---

## Making Code Changes

For any changes to `index.html`, `style.css`, or `app.js`:

1. Attach the relevant file(s) to a Claude conversation
2. Paste the README for context
3. Describe the change
4. Claude edits the file and returns it
5. Upload to GitHub

Always work from the latest version of the file from GitHub — not from a previous Claude session, which may be stale.
