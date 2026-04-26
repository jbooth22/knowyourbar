# KnowYourBar.com — QA Checklist

Run this before every upload to GitHub. If any check fails, fix it before deploying.

---

## 1. Pre-upload — automated checks

Run this in Claude before presenting files:

```python
# Paste into Claude to run QA
import re, os

pages_dir = '/mnt/user-data/outputs/kyb-site'
REQUIRED_IN_ALL = ['G-SW4MNP5W7J', 'style.css', 'site-nav-logo', 'site-footer-inner']
FORBIDDEN_IN_CONTENT = ['\u2014', '&mdash;', 'decided for you', 'dive into', 'delve']

pages = sorted([f for f in os.listdir(pages_dir) if f.endswith('.html')])
all_pass = True

for filename in pages:
    path = f'{pages_dir}/{filename}'
    with open(path) as f:
        html = f.read()
    # Strip scripts and styles for content checks
    content = re.sub(r'<style.*?</style>', '', html, flags=re.S)
    content = re.sub(r'<script.*?</script>', '', content, flags=re.S)
    
    fails = []
    for req in REQUIRED_IN_ALL:
        if req not in html:
            fails.append(f'MISSING: {req}')
    for forbidden in FORBIDDEN_IN_CONTENT:
        if forbidden in content:
            fails.append(f'FORBIDDEN: {forbidden}')
    if fails:
        all_pass = False
        print(f'FAIL {filename}: {", ".join(fails)}')
    else:
        print(f'OK   {filename}')

print('\nPASS' if all_pass else '\nFAIL — fix before uploading')
```

---

## 2. Visual QA — check these manually after uploading

### Homepage (knowyourbar.com)
- [ ] Bars load on first visit (the results table is not empty)
- [ ] Filter panel visible on left
- [ ] Preset buttons work (click "Keto Friendly" → bars update)
- [ ] Brand search works
- [ ] Ingredient exclusion filter works (type "sucralose" → results filter)
- [ ] Bar expand works (click a bar row → tray opens with ingredient detail)
- [ ] Compare feature works (select 2+ bars)
- [ ] Nav dropdowns work (hover Brand Reviews, hover Guides)
- [ ] Mobile: nav collapses to hamburger at narrow width

### Every guide and brand page
- [ ] Page loads and renders (not blank, not broken layout)
- [ ] Nav is present and sticky at top
- [ ] Footer is present with links grid
- [ ] H1 is visible and not clipped (check letters like g, y, p)
- [ ] No gray text on black background (check dark hero section)
- [ ] FAQ accordion opens and closes
- [ ] Amazon affiliate links open (check one)
- [ ] No "Data-backed guide" or "Brand Review" eyebrow text visible above H1

### Specific pages
- [ ] keto-protein-bars.html: bars render, filters work, "Show more" works, expand shows nutrition label
- [ ] quest-vs-rxbar.html: comparison table renders, flavor tabs switch between Quest and RXBAR
- [ ] flavor-map.html: Sankey diagram renders (desktop), bar chart renders (mobile)

---

## 3. SEO checks
- [ ] Every page has a unique `<title>` tag
- [ ] Every page has a unique `<meta name="description">`
- [ ] Every page has `<link rel="canonical">`
- [ ] sitemap.xml includes all pages
- [ ] No page has duplicate H1 tags

---

## 4. Rules that must never be broken

### Never do these:
1. **Never use regex to strip CSS from HTML files.** CSS inside `<style>` tags cannot be safely parsed with regex. Any font or styling change goes in `style.css` only.
2. **Never bulk-replace across all pages in one operation without a rollback plan.** Make changes to one page, verify it renders, then move to the next.
3. **Never delete `style.css` content.** The app (index.html) depends on 2,000+ lines of CSS in this file. Only append to it.
4. **Never replace the nav or footer HTML across all pages with regex.** It breaks differently on every page. Use CSS classes to standardize appearance instead.
5. **Never assume a change "looks right" from code alone.** Check a screenshot or live site after every deploy.

### Always do these:
1. Before any sitewide change: run the automated QA script above.
2. After any sitewide change: run it again and compare output.
3. When adding a new page: copy the nav HTML verbatim from an existing working page.
4. Font changes go in `style.css` `:root` only — change `--font-display`, `--font-body`, `--font-mono` there.
5. Keep the GitHub repo as the rollback source. Download files from GitHub history before making risky changes.

---

## 5. File inventory — every file that must be in the GitHub repo

| File | Purpose | Risk if missing |
|------|---------|----------------|
| `style.css` | All app and shared styles | Site completely unstyled |
| `app.js` | Filter, search, compare logic | No bar results, no filters |
| `bars.js` | All 900+ bar data | No bar results |
| `index.html` | Main tool | Homepage broken |
| `bar_hero.png` | Hero image | Image missing |
| `sitemap.xml` | SEO | Google crawl issues |
| `robots.txt` | SEO | Google crawl issues |
| All `.html` pages | Content | Page 404s |

---

## 6. After a failed deploy — recovery steps

1. Go to GitHub → the affected file → History → find last working commit
2. Download the raw file from that commit
3. Upload to Claude and say "restore this file to outputs"
4. Make only the minimal targeted fix needed
5. Re-run the QA script
6. Re-upload only the fixed file

---

*Last updated: April 2026*

---

## Deep HTML Structure Check (run on index.html after ANY change)

```python
import re, subprocess

with open('/mnt/user-data/outputs/kyb-site/index.html') as f:
    html = f.read()
with open('/mnt/user-data/outputs/kyb-site/app.js') as f:
    js = f.read()

failures = []
def check(label, condition):
    print(f"  {'OK  ' if condition else 'FAIL'}: {label}")
    if not condition: failures.append(label)

# Div balance in key sections
for name, start_tag, end_tag in [
    ('aside/filter-panel', '<aside', '</aside>'),
    ('results-panel', '<section class="results-panel"', '</section>'),
]:
    start = html.find(start_tag)
    end = html.find(end_tag, start)
    section = html[start:end+len(end_tag)] if start > -1 else ''
    opens = section.count('<div')
    closes = section.count('</div>')
    depth = 0; neg = False
    for line in section.split('\n'):
        depth += line.count('<div') - line.count('</div>')
        if depth < 0: neg = True; depth = 0
    check(f'{name} div balance ({opens}/{closes})', opens == closes and not neg)

# Critical IDs
for id_ in ['results-body','filter-panel','preset-list','grade-filter-btns',
            'brand-list','sliders-list','cert-grid','excl-tags',
            'search-input','excl-input','sort-col','result-count']:
    check(f'#{id_} present', f'id="{id_}"' in html)

# JS syntax
r = subprocess.run(['node','--check','/mnt/user-data/outputs/kyb-site/app.js'],capture_output=True,text=True)
check('app.js syntax', r.returncode == 0)

print('\nPASS' if not failures else f'\nFAIL: {failures}')
```

## Rule added after 2026-04-26 incident
**After removing any wrapper div from HTML, always run the div balance check.**
Removing a wrapper with regex leaves behind its closing `</div>`, which silently
breaks page structure. The div balance check catches this before upload.
