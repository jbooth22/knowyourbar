# KnowYourBar — tonight's fixes (2026-08-13)

23 live pages fetched from the repo, audited, and fixed. All changes are literal, additive, or subtractive edits — no rewrites, no template restructuring. Diff each file against your live repo copy before committing.

## 1. Nav duplicate — "Caffeine Protein Bars" link
Removed the duplicate line from the Guides dropdown on every page that had it (15 pages).
Files: bar-finder.html, best-bars-for-diabetics.html, brand-quadrant.html, clean-protein-bars.html,
flavor-map.html, glp1-protein-bars.html, index.html, ingredient_scoring.html, keto-protein-bars.html,
low-sugar-high-protein.html, no-artificial-sweeteners.html, no-seed-oils.html, no-sugar-alcohols.html,
quest-vs-rxbar.html.
(The 5 already-rebuilt brand pages — Barebells, Quest, RXBAR, Clif, KIND — never had this bug.)

## 2. Font loading standardized across all 23 pages
Every page now loads the same Google Fonts stylesheet link:
`DM+Mono, DM+Sans (400-700), Barlow+Condensed (500-900), IBM+Plex+Mono, Inter (400-900)`

This is additive only — nothing was removed from any page's font set, so nothing that currently
renders in Inter will break. It just makes sure every page also has Barlow Condensed and IBM Plex
Mono available, since style.css references them via --bs-font-display / --bs-font-data in scoped
overrides used across the site (not just the 5 rebuilt brand pages).

- index.html (homepage) previously had NO font stylesheet link at all — only a <link rel="preconnect">
  with no matching stylesheet request. Its own inline <style> block uses --bs-font-display and
  --bs-font-data extensively (hero, top-bars section), so those were silently falling back to system
  fonts. This is now fixed — added the missing stylesheet link.
- The 9 guide pages, bar-finder.html, flavor-map.html, ingredient-report.html, all-ingredients.html,
  brand-quadrant.html, quest-vs-rxbar.html, and ingredient_scoring.html each had a different,
  incomplete font link (5 different variants site-wide before this fix). All now match.

## 3. Bar Finder FAQ removed
Removed the visible FAQ section and its FAQPage JSON-LD schema block from bar-finder.html entirely,
per your call. If you want that FAQ content preserved somewhere (it had good copy — "what is an
ingredient quality grade," sugar alcohol safety, etc.), it's sitting in pages/bar-finder.html in the
"before" zip; happy to fold it into a relevant guide page next time.

## NOT done tonight (deliberately — bigger, riskier, separate pass)
- style.css cleanup (85 unused classes, 19 fragmented @media blocks, 75 !important flags, the
  legacy --font-display vs --bs-font-display dual-token system). This touches every page at once
  and needs its own careful pass with before/after screenshots.
- The two orphan pages (all-ingredients.html, ingredient-report.html) — untouched, not linked
  anywhere. Worth a real look together; they're both substantial, finished content.

## IMPORTANT before tomorrow's guide rebuild
TEMPLATE_GUIDE.html (your generator template) still has the old, incomplete font link and would
propagate the same bug into every newly-generated guide page. Update its <link href="..."> to the
unified string above before running tomorrow's rebuild, or the guide pages will need this same fix
again afterward.
