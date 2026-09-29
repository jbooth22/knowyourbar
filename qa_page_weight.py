#!/usr/bin/env python3
"""Page-weight QA (QA.md section 1b, added 2026-09-29).

Googlebot only processes the first 2MB of a page's HTML, so anything past that
(FAQ, footer, links) is never seen. Guide v2 pages have tighter targets:

  * v2 guide pages (carry <!-- kyb:v2 -->): HTML under 400,000 bytes, and the
    FAQ section and the footer must both START inside the first 300,000 bytes.
    Also: no v1 gd-bar-data JSON blob, all five schema types present, FAQPage
    JSON-LD matches the visible FAQ, no ingredient score printed, no visible
    "Updated" date (kyb_guide_lib.v2_qa).
  * every other page: OVER at 2,000,000 bytes or more, WARN at 1,000,000+.
    v1 guides still over 2MB are known and get fixed by the v2 rollout, so on
    a repo-wide run they are reported but don't fail the run. Name a page on
    the command line (or pass --strict) and OVER becomes a hard FAIL.
    kyb_scatter_interactive.html is exempt (standalone data viz share page).

Run from the repo root:
  python3 qa_page_weight.py                      # every page, v2 pages gate
  python3 qa_page_weight.py no-sugar-alcohols.html about.html   # these pages gate
Exit code 1 if anything fails.
"""
import glob, sys
from kyb_guide_lib import v2_qa, V2_MAX_BYTES, V2_FAQ_MAX_OFFSET

HARD, WARN = 2_000_000, 1_000_000
EXEMPT = {'kyb_scatter_interactive.html'}

def offset(page, needle):
    i = page.find(needle)
    return None if i == -1 else len(page[:i].encode('utf-8'))

def main(paths, strict=False):
    ok = True
    for path in sorted(paths):
        if path in EXEMPT and not strict:
            continue
        page = open(path, encoding='utf-8').read()
        size = len(page.encode('utf-8'))
        faq = offset(page, '<section class="guide-faq"')
        faq_s = f'FAQ at {faq:,}' if faq is not None else 'no FAQ section'
        if '<!-- kyb:v2 -->' in page:
            probs = v2_qa(page)
            status = 'FAIL' if probs else 'OK  '
            print(f'{status} {path}: {size:,} bytes (v2 limit {V2_MAX_BYTES:,}), {faq_s} (limit {V2_FAQ_MAX_OFFSET:,})')
            for p in probs:
                print(f'       - {p}')
            ok = ok and not probs
        else:
            status = ('FAIL' if strict else 'OVER') if size >= HARD else ('WARN' if size >= WARN else 'OK  ')
            print(f'{status} {path}: {size:,} bytes, {faq_s}')
            if faq is not None and faq >= HARD:
                print('       - FAQ starts past 2MB: Google never sees it')
            if strict:
                ok = ok and size < HARD
    print('\nPASS' if ok else '\nFAIL: fix before uploading')
    return ok

if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if a != '--strict']
    strict = '--strict' in sys.argv or bool(args)
    sys.exit(0 if main(args or glob.glob('*.html'), strict) else 1)
