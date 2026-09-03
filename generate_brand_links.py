#!/usr/bin/env python3
"""
generate_brand_links.py — regenerate the "Every brand we've reviewed" section
on every brand page from a single manifest, instead of hand-editing each page.

WHY THIS EXISTS
----------------
Each brand page needs to link to every OTHER brand page. With 5 brand pages
that's 20 link instances across the site; with 20 pages it's 380. Hand-editing
every existing page every time a new brand page is added doesn't scale and is
easy to get inconsistent (miss one page, and it silently falls behind).

This script is the fix: brands_manifest.json is the one file you maintain.
Run this script and it rewrites the marked block in every brand page to match
the manifest, so every page always lists the same set of brands with no
manual per-page editing.

USAGE
-----
1. Add the new brand to brands_manifest.json (name + slug)
2. Build that brand's actual review page as usual (TEMPLATE_BRAND.html, run
   verify_brand_data.py first, etc.) - this script does not create pages
3. Run: python3 generate_brand_links.py
4. It rewrites the BRAND_LINKS_START...BRAND_LINKS_END block and the
   "X is one of N brands" count line in every *.html file whose slug is
   listed in the manifest
5. Upload the changed files to GitHub

Each brand page's HTML must contain these two markers (already present in
TEMPLATE_BRAND.html and every existing brand page as of 2026-08-10):

    <!-- BRAND_LINKS_START -->
    <div class="brand-link-grid"> ... </div>
    <!-- BRAND_LINKS_END -->

Do not hand-edit content between those markers. It will be overwritten the
next time this script runs, and will drift from the manifest if you do.
"""

import json
import re
import sys
from pathlib import Path


def load_manifest(path='brands_manifest.json'):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def build_pill_block(manifest, self_slug):
    others = [b for b in manifest['brands'] if b['slug'] != self_slug]
    lines = ['    <div class="brand-link-grid">']
    for b in others:
        lines.append(f'      <a href="/{b["slug"]}" class="brand-link-pill">{b["name"]}</a>')
    total = manifest.get('total_db_brand_count', '1,000+')
    lines.append(f'      <a href="/all-protein-bar-brands" class="brand-link-pill brand-link-pill-all">See all {total} brands &rarr;</a>')
    lines.append('    </div>')
    return '\n'.join(lines)


MARKER_RE = re.compile(
    r'(<!-- BRAND_LINKS_START -->\n).*?(\n\s*<!-- BRAND_LINKS_END -->)',
    re.S
)
COUNT_RE = re.compile(r'is one of \d+ brands we\'ve scored in full')


def update_page(path, manifest, self_name, self_slug, dry_run=False):
    content = Path(path).read_text(encoding='utf-8')

    if '<!-- BRAND_LINKS_START -->' not in content:
        print(f'  SKIP {path}: no BRAND_LINKS_START marker found (add it manually once, from TEMPLATE_BRAND.html)')
        return False

    pill_block = build_pill_block(manifest, self_slug)
    new_content, n = MARKER_RE.subn(lambda m: m.group(1) + pill_block + m.group(2), content)
    if n != 1:
        print(f'  WARNING {path}: expected exactly 1 marker match, found {n} — not touching this file, check markers by hand')
        return False

    brand_count = len(manifest['brands'])
    new_content = COUNT_RE.sub(f"is one of {brand_count} brands we've scored in full", new_content)

    if new_content == content:
        print(f'  OK {path}: already up to date')
        return False

    if dry_run:
        print(f'  WOULD UPDATE {path}')
    else:
        Path(path).write_text(new_content, encoding='utf-8')
        print(f'  UPDATED {path}')
    return True


def main():
    dry_run = '--dry-run' in sys.argv
    manifest = load_manifest()
    print(f'Manifest lists {len(manifest["brands"])} brands: {[b["name"] for b in manifest["brands"]]}\n')

    any_updated = False
    for b in manifest['brands']:
        page_path = f'{b["slug"]}.html'
        if not Path(page_path).exists():
            print(f'  SKIP {b["name"]}: {page_path} does not exist yet (manifest lists it, but the page hasn\'t been built)')
            continue
        updated = update_page(page_path, manifest, b['name'], b['slug'], dry_run)
        any_updated = any_updated or updated

    if dry_run:
        print('\nDry run only, no files written. Re-run without --dry-run to apply.')
    elif any_updated:
        print('\nDone. Upload the updated file(s) to GitHub.')
    else:
        print('\nEvery page already matches the manifest, nothing to do.')


if __name__ == '__main__':
    main()
