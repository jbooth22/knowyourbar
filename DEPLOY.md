# Know Your Bar — Deployment Guide
## knowyourbar.com via GitHub + Cloudflare Pages

---

## Your Files

After downloading, you should have:
```
kyb-site/
├── index.html    ← The webpage
├── style.css     ← All the design/styling
├── app.js        ← All the filter/search logic
└── bars.js       ← Your full database (424 bars)
```

---

## Step 1 — Create a GitHub Repository

1. Go to **github.com** and sign in (or create a free account)
2. Click the **"+"** icon in the top right → **"New repository"**
3. Name it `knowyourbar` (or anything you like)
4. Leave it **Public** (required for free Cloudflare Pages)
5. Do NOT check "Add a README" — leave everything empty
6. Click **"Create repository"**

---

## Step 2 — Upload Your Files to GitHub

On the empty repo page, you'll see a prompt. Click **"uploading an existing file"**.

1. Drag all 4 files (`index.html`, `style.css`, `app.js`, `bars.js`) into the upload area
2. Scroll down to the "Commit changes" section
3. Leave the message as-is or write "Initial launch"
4. Click **"Commit changes"**

Your files are now on GitHub. ✓

---

## Step 3 — Connect to Cloudflare Pages

1. Go to **dash.cloudflare.com** and sign in
2. In the left sidebar, click **"Workers & Pages"**
3. Click **"Create application"** → **"Pages"** tab → **"Connect to Git"**
4. Click **"Connect GitHub"** and authorize Cloudflare
5. Find your `knowyourbar` repo and click **"Begin setup"**

**Build settings** (on the next screen):
- **Framework preset**: None
- **Build command**: *(leave blank)*
- **Build output directory**: *(leave blank)*

Click **"Save and Deploy"**

Cloudflare deploys in ~60 seconds. You'll get a temporary URL like `knowyourbar.pages.dev`.

---

## Step 4 — Connect knowyourbar.com

Since you already have experience with Cloudflare, this part should be familiar:

1. In your Cloudflare Pages project → **"Custom domains"**
2. Click **"Set up a custom domain"**
3. Enter `knowyourbar.com`
4. If your domain is already managed by Cloudflare, it connects automatically
5. Also add `www.knowyourbar.com` as a second custom domain pointing to the same project

HTTPS is automatic and free via Cloudflare. ✓

---

## Step 5 — Updating the Database (Adding Bars)

When you add bars to your Excel file and want to push them live:

1. Run the Python export script (provided separately) to regenerate `bars.js`
2. Go to your GitHub repo → click `bars.js` → click the ✏️ pencil icon
3. Select all the text, paste the new content
4. Scroll down → click **"Commit changes"**
5. Cloudflare auto-deploys in ~60 seconds

No servers. No build process. Just paste and commit.

---

## Costs

| Item | Cost |
|---|---|
| GitHub (public repo) | Free |
| Cloudflare Pages hosting | Free |
| Cloudflare SSL + CDN | Free |
| knowyourbar.com domain | ~$10–15/year |

**Total: ~$10–15/year** — just the domain.
