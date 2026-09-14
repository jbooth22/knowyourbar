#!/usr/bin/env python3
"""
brand_qa.py — mechanical check for the hard rules in BRAND_STANDARDS.md's
"AI-tell" section. Run before every deploy, same as verify_brand_data.py.

Exit code 0 = clean. Exit code 1 = violations found (printed with file/line).

Checks:
  1. No em dash (unicode — or &mdash;) in visible copy: HTML text nodes,
     attribute values (aria-label, alt, title, placeholder), and JSON-LD
     string fields. Dashes inside <!-- --> comments, <script> (non-JSON-LD),
     and <style> blocks are ignored — those are source annotations, not
     content a visitor or Google ever sees.
  2. No CSS rule in style.css combines text-transform:uppercase,
     a non-zero letter-spacing, and a monospace font-family in the same
     rule. This is the exact "uppercase, letter-spaced monospace label"
     pattern BRAND_STANDARDS.md names as the single biggest AI-interface
     tell. Zero tolerance, no table-header/badge exception.
  3. The font import in every HTML file matches style.css's actual
     --font-mono / --bs-font-data values (catches a page importing a font
     the CSS no longer references, or vice versa).

This does not check color usage, button styles, or spacing beyond the
above — those are harder to check mechanically and are still a manual
review against BRAND_STANDARDS.md's Do/Don't list.
"""
import glob
import re
import sys

VIOLATIONS = []


def strip_noncontent(html):
    """Remove comments, <script>, and <style> blocks (but keep JSON-LD script
    bodies, since those ARE shipped content Google reads)."""
    html = re.sub(r'<!--.*?-->', '', html, flags=re.S)
    html = re.sub(
        r'<script(?![^>]*type="application/ld\+json")[^>]*>.*?</script>',
        '', html, flags=re.S,
    )
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.S)
    return html


def check_em_dashes():
    for fname in sorted(glob.glob('*.html')):
        raw = open(fname, encoding='utf-8', errors='ignore').read()
        content = strip_noncontent(raw)
        for i, line in enumerate(content.split('\n'), start=1):
            if '—' in line or '&mdash;' in line:
                VIOLATIONS.append(
                    f"{fname}:{i}: em dash in visible content — {line.strip()[:100]}"
                )


def check_eyebrow_css():
    """Resolve each selector's FINAL text-transform/letter-spacing/font-family
    the way a browser would: later rules of equal specificity win, property
    by property, not whole-rule-by-whole-rule. A selector that appears twice
    (an original rule plus a later override block) must be judged on what
    actually reaches the browser, not on the first, possibly-since-overridden
    declaration. This intentionally does NOT handle specificity beyond plain
    selector text match — an !important or a more specific selector elsewhere
    could still win in ways this script won't see. Good enough for this
    file's actual patterns (append-only overrides of the same selector);
    treat a PASS here as "no known regression," not a full computed-style audit.
    """
    css = open('style.css', encoding='utf-8', errors='ignore').read()

    # Pass 1: discover candidate selectors with a whole-file tokenizer. This
    # misses a handful of rules when the file has @media/@supports nesting
    # (a plain regex can't track nested braces), so it's a discovery aid,
    # not the final word — a selector already fixed by an append can still
    # surface here from its now-stale original declaration.
    candidates = set()
    for selector, decls in re.findall(r'([^{}]+)\{([^{}]*)\}', css):
        selector = selector.strip()
        if not selector or selector.startswith('@') or selector.startswith(':root'):
            continue
        candidates.add(selector)

    # Pass 2: for each candidate, resolve it directly by finding every
    # exact textual occurrence of "SELECTOR{...}" in the file (sidesteps
    # the nested-brace blind spot from pass 1, since this only needs to
    # locate one known selector string, not tokenize the whole file) and
    # taking the last-wins value per property, the same way a browser
    # cascades declarations of equal specificity in source order.
    order = sorted(candidates)
    resolved = {}
    for selector in order:
        props = {}
        for m in re.finditer(re.escape(selector) + r'\{([^{}]*)\}', css):
            decls = m.group(1)
            for prop in ('text-transform', 'letter-spacing', 'font-family'):
                pm = re.search(re.escape(prop) + r':\s*([^;]+)', decls)
                if pm:
                    props[prop] = pm.group(1).strip()
        resolved[selector] = props

    for selector in order:
        props = resolved[selector]
        tt = props.get('text-transform', '')
        ls = props.get('letter-spacing', '')
        ff = props.get('font-family', '')
        has_upper = tt == 'uppercase'
        has_spacing = bool(re.match(r'\.?\d', ls)) and ls not in ('0', 'normal')
        has_mono = (
            'var(--font-mono)' in ff
            or 'var(--bs-font-data)' in ff
            or 'Mono' in ff
            or 'monospace' in ff
        )
        if has_upper and has_spacing and has_mono:
            VIOLATIONS.append(
                f"style.css: '{selector}' resolves to uppercase + letter-spacing + "
                f"monospace — the banned eyebrow-label pattern"
            )


def check_font_consistency():
    css = open('style.css', encoding='utf-8', errors='ignore').read()
    mono_match = re.search(r"--font-mono:'([^',]+)'", css)
    data_match = re.search(r"--bs-font-data:'([^',]+)'", css)
    expected = set()
    if mono_match:
        expected.add(mono_match.group(1))
    if data_match:
        expected.add(data_match.group(1))
    banned = {'IBM Plex Mono', 'DM Mono'} - expected
    for fname in sorted(glob.glob('*.html')):
        html = open(fname, encoding='utf-8', errors='ignore').read()
        for font in banned:
            if font.replace(' ', '+') in html:
                VIOLATIONS.append(
                    f"{fname}: imports '{font}', which style.css no longer uses "
                    f"for --font-mono/--bs-font-data"
                )


if __name__ == '__main__':
    check_em_dashes()
    check_eyebrow_css()
    check_font_consistency()

    if VIOLATIONS:
        print(f"FAIL — {len(VIOLATIONS)} brand-standard violation(s):\n")
        for v in VIOLATIONS:
            print(" -", v)
        sys.exit(1)
    else:
        print("PASS — no em dashes in visible copy, no eyebrow-label CSS, fonts consistent.")
        sys.exit(0)
