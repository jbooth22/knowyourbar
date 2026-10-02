"""
score_and_export.py — Know Your Bar scoring pipeline
=====================================================
Scores all bars from raw ingredient text and exports bars.js.

Usage:
    python score_and_export.py \
        --db "KYB - New Protein Bar Database (2026).xlsx" \
        --schema "knowyourbar_scoring_schema_v12.xlsx"

Output:
    bars.js  (written to current directory)

Requirements:
    pip install pandas openpyxl

Notes:
    - ALL bars are scored from raw ingredient text using the alias/canonical
      lookup tables. The schema's Ingredient_Lines and Products sheets are NOT
      used. Only Canonical_Ingredients and Alias_Map are loaded.
    - Sub-ingredients inside parentheses (e.g. protein blends) are scored at
      60% weight, reflecting their smaller quantity relative to top-level items.
    - Every scored bar gets insight chips using the same logic.
    - Run this script whenever new bars are added or ingredient data changes.
    - After running, upload bars.js to GitHub and update bar counts in HTML files.
"""

import argparse
import json
import os
import re
import sys
import unicodedata
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP

import pandas as pd


# ── Grade bands ───────────────────────────────────────────────────────────────
COUNT_BANDS = [
    (0,   8,   0.05),
    (9,  12,   0.00),
    (13, 16,  -0.05),
    (17, 20,  -0.10),
    (21, 999, -0.15),
]
SCORE_BANDS = [
    (8,    float('inf'), 'A', 'Clean'),
    (4,    7.9999,       'B', 'Good'),
    (0,    3.9999,       'C', 'Okay'),
    (-3,  -0.0001,       'D', 'Mostly Processed'),   # was 'Poor' (2026-10-02)
    (float('-inf'), -3.0001, 'F', 'Highly Processed'),  # was 'Avoid' (2026-10-02): describe, don't prescribe
]

# ── Ingredient signals ────────────────────────────────────────────────────────
ARTIFICIAL_SW  = ['sucralose', 'acesulfame', 'aspartame', 'saccharin']
# Flat per-sweetener penalty, applied regardless of label position (schema v12)
ARTIFICIAL_SW_PENALTY = -2.0
SA_KEYWORDS    = ['erythritol', 'maltitol', 'xylitol', 'sorbitol',
                  'mannitol', 'isomalt', 'lactitol']
# Sugar alcohol test (2026-10-01). A plain substring test on 'isomalt' also
# matched "isomalto-oligosaccharide" (IMO), so 34 IMO-only bars carried a
# "Sugar Alcohols" chip although IMO is scored as a fiber (schema v10). The
# guide screens and the Bar Finder still treat IMO as a sugar alcohol on
# purpose, but they check for IMO by name themselves (IMO_RX in
# kyb_guide_lib.py, hasSugarAlcohol() in app.js), so their results don't change.
SA_RE          = re.compile(r'erythritol|maltitol|xylitol|sorbitol|mannitol|lactitol|isomalt(?!o)')
OIL_KEYWORDS   = ['palm oil', 'palm kernel oil', 'canola oil', 'soybean oil',
                  'hydrogenated', 'partially hydrogenated', 'palm fruit oil',
                  'sunflower oil', 'safflower oil', 'vegetable oil',
                  'rapeseed oil', 'cottonseed oil', 'corn oil',
                  'grapeseed oil', 'rice bran oil',
                  # 2026-09-24: "palm fat" is palm oil under another name (Love Good, Crave labels)
                  'palm fat']
HIGH_OLEIC_EX  = ['high oleic']
SKIP_PREFIXES  = [
    'organic ', 'natural ', 'pure ', 'raw ', 'whole ', 'roasted ',
    'unsweetened ', 'dried ', 'freeze dried ', 'dehydrated ', 'grass fed ', 'grass-fed ',
    'non gmo ', 'certified ', 'reduced fat ', 'low fat ', 'instant ',
    'enriched ', 'unbleached ', 'pasteurized ', 'homogenized ',
    'contains 2 or less of ', 'contains 2 percent or less of ',
]
SKIP_CLAUSES   = [
    'may contain', 'contains:',
    'manufactured in', 'processed in', 'made in',
]
# Diminishing returns on stacked protein sources (added schema v7, 2026-08-14):
# each additional *separately top-level-listed* protein ingredient beyond the
# single best-scoring one counts at this fraction of its normal weighted
# value. This does NOT apply to protein sources decomposed from the same
# parenthetical blend label (e.g. "Protein Blend (Milk Protein Isolate, Whey
# Protein Isolate)") - those are one FDA-labeled blend, not competing claims,
# and are already down-weighted via the 0.6 sub-ingredient multiplier. It
# only targets distinct top-level protein ingredients (e.g. Whey Protein
# Isolate ... Collagen ... Milk Protein Concentrate listed as separate top-
# level items), so a second or third source no longer adds nearly as much
# credit as the first just by being listed.
PROTEIN_STACK_DISCOUNT = 0.5
# Scoring v13 (2026-09-29, Jeff approved): the discount above now ALSO applies
# to proteins inside a blend. The v7 reasoning below the original comment (a
# blend is "already down-weighted via the 0.6 multiplier") did not hold: every
# sub-ingredient got 0.6 of the slot's weight with no cap on the group, so a
# 6- to 12-protein "Protein Blend (...)" at position 1 earned 4 to 7 full
# position-1 slots and carried bars with sucralose, erythritol and palm oil to
# an A (Pure Protein Cookies and Cream 10.8, MyProtein Chocolate Peanut Butter
# 9.6). Audit: claude/SCORING_BLEND_AUDIT_2026-09-29.md.
# Oil-blend parents whose bare plant-name subs are oils, not whole foods (v13).
VEG_OIL_PARENT_RE = re.compile(r'\bvegetable (?:oils?|fats?)\b')
VEG_OIL_REMAP_CATEGORIES = {'whole_food', 'starch_flour', 'protein', 'cocoa_chocolate'}
# Each further positive non-protein member of one blend counts at this fraction of the one before (v13).
BLEND_DIMINISH = 0.5
# A label with no ingredient scoring below 0 grades at least A (v13 clean-label floor).
CLEAN_LABEL_FLOOR = 8.0

# ── Scoring v14 (2026-10-02, Jeff approved the thesis) ─────────────────────────
# What the grade measures: what a bar is made of, not how much of each macro it
# has. See claude/SCORING_V14_THESIS.md.
# 1. Good ingredients can add at most CREDIT_CAP points. Penalties always count
#    in full, so a pile of nuts and seeds can't cancel out a syrup.
CREDIT_CAP = 10.0
# 2. The clean-label floor tolerates trace minor concerns: ingredients scored -1
#    (natural flavors, glycerin, gums...) adding up to no more than this. A
#    trace "natural flavor" no longer costs a whole grade.
FLOOR_TOLERANCE = 0.5
# 3. An added sugar (FDA definition: sugars, syrups, honey, maple syrup, juice
#    concentrates; not whole fruit or dates, not sugar alcohols or zero-calorie
#    sweeteners) among the first ADDED_SUGAR_TOP top-level ingredients caps the
#    grade at B.
ADDED_SUGAR_TOP = 3
ADDED_SUGAR_EXCLUDE_SUBCATS = {'sugar_alcohol', 'artificial_sweetener', 'low_calorie_sweetener'}
CEILING_SCORE = 7.9
# 4. Restricted additives: banned or not authorized in the EU, or being revoked /
#    phased out by the FDA. Like artificial sweeteners they are used in
#    milligrams, so each group costs a flat RESTRICTED_PENALTY wherever it sits.
RESTRICTED_PENALTY = -2.0
RESTRICTED_GROUPS = {
    # FDA phase-out of petroleum-based dyes (2025-2027) and Red No. 3 revocation;
    # EU requires a hyperactivity warning on most of them. One penalty per bar.
    'synthetic dyes': re.compile(
        r'\b(?:fd&c\s*)?(?:red|yellow|blue|green)\s*(?:lake\s*)?(?:no\.?\s*|#\s*)?(?:40|3|5|6|1|2)\b'
        r'|allura red|tartrazine|sunset yellow|brilliant blue|indigo carmine|erythrosine|citrus red|orange b\b'
        r'|artificial colou?r'),
    'titanium dioxide': re.compile(r'titanium dioxide'),                # EU ban 2022
    'brominated vegetable oil': re.compile(r'brominated vegetable oil'), # FDA revoked 2024
    'potassium bromate': re.compile(r'potassium bromate'),               # not authorized in the EU
    'azodicarbonamide': re.compile(r'azodicarbonamide'),                 # not authorized in the EU
    'propylparaben': re.compile(r'propylparaben'),                       # EU revoked
    'partially hydrogenated oil': re.compile(r'partially hydrogenated'), # FDA ban (PHOs), 2018
}
# "Contains less than 2% of the following: X, Y, Z" (and variants: "and less
# than 2% of X", "Water and Less than 2%: X", "Less than 2% of each of the
# following: X") is standard FDA labeling for real minor ingredients — NOT
# an allergen/cross-contact disclaimer. It must not be truncated away; only
# the boilerplate lead-in phrase is stripped so the real ingredients after
# it continue to be parsed normally.
LESS_THAN_RE = re.compile(
    r'(contains\s+|and\s+)?less\s+than\s+[\d.]+\s*%\s*(of\s+(each\s+of\s+)?(the\s+following)?)?:?\s*',
    re.IGNORECASE,
)
PCT_DV_COLS    = [
    'Vitamin A (% DV)', 'Vitamin C (% DV)', 'Vitamin D (% DV)',
    'Vitamin E (% DV)', 'Vitamin K (% DV)', 'Thiamin / B1 (% DV)',
    'Riboflavin / B2 (% DV)', 'Niacin / B3 (% DV)', 'Vitamin B6 (% DV)',
    'Vitamin B12 (% DV)', 'Folic Acid (% DV)', 'Biotin (% DV)',
    'Pantothenic Acid (% DV)', 'Phosphorus (% DV)', 'Iodine (% DV)',
    'Magnesium (% DV)', 'Zinc (% DV)', 'Selenium (% DV)', 'Copper (% DV)',
    'Manganese (% DV)', 'Chromium (% DV)', 'Molybdenum (% DV)',
]
KEEP_COLS      = [
    'Brand Name', 'Flavor Name', 'Key', 'Size', 'Type', 'Website',
    'Custom Referral Link',
    'Amazon Affiliate', 'Serving Size (g)', 'Calories', 'Total Fat (g)',
    'Saturated Fat (g)', 'Trans Fat (g)', 'Cholesterol (mg)', 'Sodium (mg)',
    'Total Carbohydrates (g)', 'Dietary Fiber (g)', 'Sugars (g)',
    'Sugar Alcohol (g)', 'Protein (g)', 'Calcium (mg)', 'Iron (mg)',
    'Potassium (mg)', 'Creatine (g)', 'Caffeine (mg)', 'Melatonin (mg)',
] + PCT_DV_COLS + [
    'Kosher (Y/N)', 'Vegan (Y/N)', 'Non-GMO (Y/N)', 'Soy Free (Y/N)',
    'Dairy Free (Y/N)', 'Gluten Free (Y/N)', 'Nut Free (Y/N)', 'Ingredients',
    'ingredient_score', 'score_pos', 'score_neg', 'score_band',
    'score_band_label', 'positive_ingredients', 'concern_ingredients',
    'score_insights', 'score_source',
]


# ── Helpers ───────────────────────────────────────────────────────────────────
def get_count_adj(n):
    for lo, hi, adj in COUNT_BANDS:
        if lo <= n <= hi:
            return adj
    return 0


def get_band(score):
    # Bands are checked by lower bound only (2026-09-24). The old lo <= score <= hi
    # test left tiny gaps between bands (e.g. -0.0001 < score < 0), and a score that
    # fell in one matched nothing and defaulted to F (Aloha Chocolate Caramel Pecan,
    # score 0.0, graded F). SCORE_BANDS is ordered highest first, so the first lower
    # bound the score reaches is its band.
    for lo, hi, band, label in SCORE_BANDS:
        if score >= lo:
            return band, label
    return 'F', 'Highly Processed'


def round_score(x):
    """One decimal, half up, after clearing float noise. Never returns -0.0."""
    return float(Decimal(repr(round(x, 6))).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)) + 0.0


def position_weight(pos):
    table = {
        1: 1.00, 2: 0.85, 3: 0.72, 4: 0.61, 5: 0.52,
        6: 0.44, 7: 0.37, 8: 0.31, 9: 0.26, 10: 0.22,
        11: 0.20, 12: 0.18, 13: 0.17, 14: 0.16, 15: 0.15,
    }
    return table.get(pos, max(0.08, 0.15 - (pos - 15) * 0.007))


def normalize(text):
    text = str(text).lower().strip()
    text = re.sub(r'\*+', '', text)
    text = re.sub(r'\(.*?\)', '', text)
    # Transliterate accented letters (e.g. jalapeño -> jalapeno) instead of
    # deleting them, so accented ingredient names don't get split into
    # broken tokens by the character-strip step below.
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


SKIP_METHODS = {'ignore_clause', 'ignore_qualifier'}


def build_lookup(alias_map, canonical):
    """Build alias and canonical lookup dicts.

    Schema v11 fix: entries tagged ignore_clause/ignore_qualifier (allergen
    "contains"/"may contain"/"manufactured in" disclaimer fragments, and
    processing-note qualifiers like "for color"/"to preserve freshness")
    were previously included in `cl`/`al` like any real ingredient, just
    with base_score=0. That made them score-neutral, which looked harmless,
    but they still counted as a matched ingredient toward top_level_count
    (the ingredient-count adjustment) and showed up in the ingredient
    encyclopedia as if they were real foods (e.g. bare "almond"/"peanut"
    fragments sliced out of a "Contains: almonds, peanuts" statement). These
    are marked 'skip': True here and score_bar() now excludes them from
    `matched` entirely, instead of counting them as a real, if neutral,
    ingredient.
    """
    al, cl = {}, {}
    for _, row in alias_map.iterrows():
        key = normalize(str(row['normalized_alias_text']))
        if key not in al:
            al[key] = {
                'canonical_name': row['canonical_name'],
                'category': str(row.get('category', 'other')),
                'base_score': float(row['base_score']) if pd.notna(row['base_score']) else 0,
                'skip': str(row.get('score_method', '')) in SKIP_METHODS,
                'subcategory': str(row.get('subcategory', '')),
            }
    for _, row in canonical.iterrows():
        key = normalize(str(row['canonical_name']))
        if key not in cl:
            cl[key] = {
                'canonical_name': row['canonical_name'],
                'category': str(row.get('category', 'other')),
                'base_score': float(row['base_score']) if pd.notna(row['base_score']) else 0,
                'skip': str(row.get('score_method_default', '')) in SKIP_METHODS,
                'subcategory': str(row.get('subcategory', '')),
            }
    # Duplicate-alias guard (schema v12, 2026-09-23): when the same label
    # name appears on more than one Alias_Map row, only the FIRST row is
    # used. Before v12 this happened silently: v11 "merge" rows such as
    # strawberries -> strawberry (+2) were appended at the bottom, but an
    # older strawberries (+1) row above them kept winning, so the fix never
    # took effect. Now any duplicate that disagrees on score
    # stops the run so it gets fixed in the schema instead of hidden.
    seen, conflicts = {}, []
    for _, row in alias_map.iterrows():
        key = normalize(str(row['normalized_alias_text']))
        if len(key) < 2:
            continue
        val = float(row['base_score']) if pd.notna(row['base_score']) else 0
        if key in seen and seen[key] != val:
            conflicts.append(f'{key!r}: {seen[key]} vs {val}')
        seen.setdefault(key, val)
    if conflicts:
        raise ValueError('Alias_Map has duplicate label names with different scores '
                         '(only the first would be used):\n  ' + '\n  '.join(conflicts))
    return al, cl


# ── Variant normalization (schema v12) ─────────────────────────────────────
VARIANT_PREP_WORDS = ['organic','natural','pure','raw','roasted','dry roasted','unsweetened','dried','freeze dried',
              'dehydrated','sliced','diced','chopped','toasted','wild','fresh','certified organic','non gmo','gluten free']
def _singular(w):
    if len(w) <= 3 or w.endswith('ss') or w.endswith('us'): return w
    if w.endswith('ies'): return w[:-3] + 'y'
    if w.endswith(('ches','shes','sses','xes','oes')): return w[:-2]
    if w.endswith('s'): return w[:-1]
    return w
def ingredient_variants(norm):
    """Yield progressively normalized forms of an ingredient: prep words
    stripped (repeatedly, any order) and the last word singularized."""
    out = []
    s = norm
    changed = True
    while changed:
        changed = False
        if s.startswith('whole ') and not s.startswith('whole grain'):
            s = s[6:]; changed = True
        for p in sorted(VARIANT_PREP_WORDS, key=len, reverse=True):
            if s.startswith(p + ' '):
                s = s[len(p)+1:]; changed = True
    for base in dict.fromkeys([norm, s]):
        words = base.split()
        if not words: continue
        sg = ' '.join(words[:-1] + [_singular(words[-1])])
        for v in (base, sg):
            if v and v not in out: out.append(v)
    return out


def lookup_ingredient(norm, al, cl):
    if norm in al:
        return al[norm]
    stripped = norm
    for prefix in SKIP_PREFIXES:
        if stripped.startswith(prefix):
            stripped = stripped[len(prefix):]
            break
    if stripped != norm:
        if stripped in al:
            return al[stripped]
        if stripped in cl:
            return cl[stripped]
    if norm in cl:
        return cl[norm]
    # Variant fallback (schema v12, 2026-09-23): before the substring
    # fallback below, try the same ingredient with preparation words
    # stripped (dried, freeze dried, roasted, raw, ...) and the last word
    # singularized (strawberries -> strawberry). Previously these variants
    # fell through to the substring matcher or to separately-scored
    # canonical entries, so the same food could score differently depending
    # on how a label spelled it (e.g. strawberry +2 vs. strawberries +1).
    for v in ingredient_variants(norm):
        if v == norm:
            continue
        if v in al:
            return al[v]
        if v in cl:
            return cl[v]
    best, best_len = None, 0
    for key, val in al.items():
        if key in norm and len(key) > best_len and len(key) > 4:
            best, best_len = val, len(key)
    return best


# Compound label phrases (2026-10-01). Labels sometimes join two ingredients
# in one comma slot: "roasted peanuts and sea salt", "whey concentrate and
# sunflower lecithin", "salt and sucralose", "palm and/or canola oil". Before
# this, the partial-match fallback scored only ONE of them (in the whey example
# the whey was never scored). When a phrase has no exact or variant match, it is
# split on these words, and if every part is a known ingredient each part is
# scored in the same label slot. "X and/or Y" and "X or Y" mean the bar has one
# of them, so only the lower-scoring one counts (the conservative reading).
COMPOUND_SPLIT_RE = re.compile(r'\s+(and or|and|or|with)\s+')


def split_compound(norm, al, cl):
    """Return (parts, is_alternative) if `norm` splits into known ingredients
    on and / or / and/or / with, else None. Only used when `norm` itself has
    no exact or variant match."""
    text = re.sub(r'^(and or|and|or|with)\s+', '', norm)
    pieces = COMPOUND_SPLIT_RE.split(text)
    if len(pieces) < 3 and text == norm:
        return None
    parts = [p.strip() for p in pieces[0::2] if p.strip()]
    joins = pieces[1::2]
    if not parts:
        return None
    for p in parts:
        if len(p) < 2 or lookup_ingredient(p, al, cl) is None or match_method(p, al, cl) == 'partial':
            return None
    alternative = any(j in ('or', 'and or') for j in joins)
    return parts, alternative


def strip_disclaimer_clause(text, clause):
    """Strip every occurrence of `clause` (case-insensitive, e.g. "may
    contain", "made in") from `text`, regardless of what paren/bracket
    depth it sits at.

    - A clause found at depth 0 is trailing whole-product disclaimer
      boilerplate: everything from the clause to the end of the string is
      dropped, same as the old depth-0-only behavior.
    - A clause found at depth >= 1 (schema v12 fix, this update) means the
      disclaimer itself is wrapped in a parenthetical/bracket — e.g. an
      ingredient's own "(Sugar, Cocoa Butter, May contain Sunflower
      Lecithin, Vanilla)" sub-breakdown, or a plain "(Contains milk and
      peanuts, made in a facility that also processes tree nuts)" aside.
      Only the disclaimer's own span is excised — from the clause to the
      bracket that closes its immediately-enclosing group — leaving any
      real sibling sub-ingredients earlier in that same group (e.g.
      "Sugar", "Cocoa Butter" above) and anything after the group's close
      untouched. Previously `find_depth0_clause` only ever matched a
      depth-0 occurrence, so a disclaimer wrapped in its own parentheses
      never truncated at all — its contents got comma-split like any
      other sub-ingredient group, producing fake top-level-looking
      canonical entries such as "may contain sunflower lecithin" or
      "milk and peanuts made in a facility that also processes tree nuts"
      (see BRIEFING.md's `allergen_or_contains_statement` category).

    Loops until no more occurrences of `clause` are found, since the same
    clause phrase can appear more than once in one ingredient string (e.g.
    two different sub-ingredient parentheticals each with their own "may
    contain" aside)."""
    while True:
        lower = text.lower()
        idx = lower.find(clause)
        if idx <= 0:
            return text
        depth = 0
        stack = []
        for ch in text[:idx]:
            if ch in '([':
                depth += 1
                stack.append(ch)
            elif ch in ')]':
                if stack:
                    stack.pop()
                depth = max(0, depth - 1)
        if depth == 0:
            text = text[:idx]
            continue
        # Depth >= 1: find the bracket that closes the group we're
        # currently inside (not necessarily the outermost one) by tracking
        # depth locally from idx forward — the first unmatched close we
        # hit is the one that ends this group.
        local_depth = 0
        close_idx = len(text)
        for j in range(idx, len(text)):
            ch = text[j]
            if ch in '([':
                local_depth += 1
            elif ch in ')]':
                if local_depth == 0:
                    close_idx = j
                    break
                local_depth -= 1
        text = text[:idx] + text[close_idx:]


def parse_ingredients(raw):
    """
    Parse ingredient string into (text, top_level_position, weight_multiplier).

    Top-level ingredients get weight_multiplier=1.0.
    Sub-ingredients inside parentheses OR square brackets get
    weight_multiplier=0.6 — they are present in smaller amounts than their
    parent ingredient.

    Schema v8 fix (2026-08-21): '[' and ']' are now tracked as nesting
    depth markers identically to '(' and ')'. Previously only parens were
    tracked, so bracketed compound-ingredient breakdowns (e.g. "cookie
    crumble [sugar (cane sugar, tapioca syrup), pea starch, shortening
    [palm oil, modified palm oil]]" — a common labeling style, especially
    on imported/EU-formatted bars) had their contents comma-split and
    scored as independent top-level, full-weight ingredients instead of
    sub-ingredients of their bracketed parent. That inflated the position
    count and applied full (1.0) weight to what are actually minor
    sub-components, which could meaningfully skew both the position-based
    weighting and, when a scored sub-component (e.g. palm oil) was
    involved, the letter grade itself. Found while auditing the 2026-08-21
    database update: 163 bars in the live database contain square
    brackets; 22 of those had their score shift by >=0.5 once brackets
    were depth-tracked, and 5 changed letter grade band entirely. Treating
    '[' / ']' exactly like '(' / ')' throughout this function (and in
    strip_disclaimer_clause above) fixes this with no separate code path.

    Schema v12 fix (this update): allergen/processing disclaimer clauses
    ("may contain", "contains:", "manufactured in", "processed in", "made
    in") are now stripped via `strip_disclaimer_clause` wherever they
    occur, not just at depth 0 — see that function's docstring.
    """
    if not raw or pd.isna(raw):
        return []
    text = str(raw).strip()
    text = LESS_THAN_RE.sub(', ', text)
    for clause in SKIP_CLAUSES:
        text = strip_disclaimer_clause(text, clause)

    items = []
    top_pos = 0
    i = 0
    depth = 0
    current_top = []
    current_sub = []

    while i < len(text):
        ch = text[i]
        if ch in '([':
            depth += 1
            if depth == 1:
                top_text = ''.join(current_top).strip().rstrip(',').strip()
                if top_text:
                    top_pos += 1
                    items.append((top_text, top_pos, 1.0))
                current_top = []
                current_sub = []
            else:
                # Opening a NESTED parenthetical/bracket (depth >= 2 after
                # this increment) inside an already-open sub-group, e.g.
                # "fruit and veggie juice concentrate (grape, date, lemon)"
                # sitting inside a "Grape layer (...)" wrapper. Flush
                # whatever text has accumulated in current_sub up to this
                # point as its own sub-ingredient(s) before starting to
                # accumulate the nested group's contents separately.
                # Schema v9 fix (2026-08-31 database update): previously
                # only the outermost paren boundary (depth 0<->1) ever
                # flushed anything, so a nested opener with no comma
                # immediately before it silently glued the parent phrase to
                # the first item inside the nested group once everything
                # finally flushed together at the outer close (e.g.
                # "fruit and veggie juice concentrate" + "grape" -> the
                # single unmatched token "fruit and veggie juice
                # concentrate grape"). Found auditing the schema-gap report
                # from this update; see claude/DATABASE_UPDATE_TRIAGE_2026-08-31.md.
                sub_text = ''.join(current_sub).strip().rstrip(',').strip()
                if sub_text:
                    for sub_part in re.split(r'[,;]', sub_text):
                        sub_part = sub_part.strip()
                        if sub_part:
                            items.append((sub_part, top_pos, 0.6))
                current_sub = []
        elif ch in ')]':
            if depth == 0:
                # Stray closing bracket/paren with no matching open in the
                # source data — ignore it rather than letting depth go
                # negative, which would otherwise corrupt parsing for the
                # rest of the ingredient list.
                i += 1
                continue
            depth -= 1
            if depth == 0:
                sub_text = ''.join(current_sub).strip()
                if sub_text:
                    for sub_part in re.split(r'[,;]', sub_text):
                        sub_part = sub_part.strip()
                        if sub_part:
                            items.append((sub_part, top_pos, 0.6))
                current_sub = []
            else:
                # Closing a NESTED parenthetical/bracket (depth still >= 1
                # after this decrement) -- flush its own contents as
                # sub-ingredients now, same reasoning as the nested-open
                # case above, rather than letting them run together with
                # whatever text follows before the outer group closes.
                sub_text = ''.join(current_sub).strip()
                if sub_text:
                    for sub_part in re.split(r'[,;]', sub_text):
                        sub_part = sub_part.strip()
                        if sub_part:
                            items.append((sub_part, top_pos, 0.6))
                current_sub = []
        elif ch in ',;' and depth == 0:
            # ';' separates top-level items too (EU-style labels, 2026-10-01):
            # "sucrose esters of fatty acids; sweetener: sucralose" was one item.
            top_text = ''.join(current_top).strip()
            if top_text:
                top_pos += 1
                items.append((top_text, top_pos, 1.0))
            current_top = []
        elif depth == 0:
            current_top.append(ch)
        else:
            current_sub.append(ch)
        i += 1

    top_text = ''.join(current_top).strip()
    if top_text:
        top_pos += 1
        items.append((top_text, top_pos, 1.0))

    # Unclosed parenthetical/bracket at end of string (more openers than
    # closers in the source data) — recover whatever was accumulated
    # inside it instead of silently dropping it.
    if depth > 0 and current_sub:
        sub_text = ''.join(current_sub).strip()
        if sub_text:
            for sub_part in re.split(r'[,;]', sub_text):
                sub_part = sub_part.strip()
                if sub_part:
                    items.append((sub_part, top_pos, 0.6))

    return items


def score_bar(raw, al, cl):
    """
    Score a single bar from its raw ingredient string.
    Returns (score, band, label, pos_str, neg_str, pos_total, neg_total, insight_str)
    or (None, None, None, '', '', None, None, '') if unscored.
    """
    if not raw or pd.isna(raw):
        return None, None, None, '', '', None, None, ''

    full_lower = str(raw).lower()
    parsed = parse_ingredients(raw)
    if not parsed:
        return None, None, None, '', '', None, None, ''

    matched = []
    unmatched = 0      # ingredients the schema doesn't know (blocks the clean-label floor)
    parent_norm = {}   # top_pos -> normalized text of the top-level item that owns the parenthetical
    group_seen = {}    # top_pos -> canonicals already counted in that label slot (scoring v13)
    for ing_text, top_pos, weight_mult in parsed:
        norm = normalize(ing_text)
        if not norm or len(norm) < 2:
            continue
        is_sub = weight_mult < 1.0
        if not is_sub:
            parent_norm[top_pos] = norm
        res = lookup_ingredient(norm, al, cl)
        if res is None or match_method(norm, al, cl) == 'partial':
            comp = split_compound(norm, al, cl)
            if comp:
                parts, alternative = comp
                cands = [(p, lookup_ingredient(p, al, cl)) for p in parts]
                cands = [(p, r) for p, r in cands if not r.get('skip')]
                if alternative and cands:
                    cands = [min(cands, key=lambda c: c[1]['base_score'])]
                for p, r in cands:
                    seen = group_seen.setdefault(top_pos, set())
                    if r['canonical_name'] in seen and (is_sub or len(cands) > 1):
                        continue
                    seen.add(r['canonical_name'])
                    pw = position_weight(top_pos) * weight_mult
                    matched.append({
                        'canonical': r['canonical_name'], 'category': r['category'],
                        'score': r['base_score'], 'weighted': r['base_score'] * pw,
                        'position': top_pos, 'is_sub': is_sub, 'compound': True,
                        'subcategory': r.get('subcategory', ''),
                    })
                continue
        if res and res.get('skip'):
            # Allergen "contains"/qualifier-note fragment (schema v11) —
            # not a real ingredient. Excluded from matched entirely so it
            # can't inflate top_level_count or appear in the encyclopedia.
            continue
        # Oil blends (scoring v13, 2026-09-29): inside "Vegetable Oil (Palm
        # Kernel, Palm, Shea, Peanut)" or "Vegetable Oil (Sunflower)" a bare
        # plant name is that plant's OIL, not the whole food. Before v13 the
        # lookup matched "peanut" -> peanuts (+3) and "sunflower" -> sunflower
        # seeds (+2), crediting an oil blend with whole-food points. Look the
        # sub up as "<name> oil"; if the schema has no fat_oil entry for it,
        # count it as a refined oil (-1 since v14; was a neutral 0).
        if (res and is_sub and VEG_OIL_PARENT_RE.search(parent_norm.get(top_pos, ''))
                and res['category'] in VEG_OIL_REMAP_CATEGORIES):
            oil = lookup_ingredient(normalize(f'{norm} oil'), al, cl)
            if oil and not oil.get('skip') and oil['category'] == 'fat_oil':
                res = oil
            else:
                res = {'canonical_name': f'{norm} oil', 'category': 'fat_oil', 'base_score': -1}  # v14: an unnamed refined oil
        # One label slot counts each ingredient once (scoring v13, 2026-09-29):
        # a repeat inside the same parenthetical ("Protein Blend (Whey Protein
        # Isolate, ... Whey Protein Cocoa Crisps [Whey Protein Isolate, ...])")
        # or a sub that restates its parent ("Isomalto-oligosaccharides (IMO)")
        # is not counted again.
        if res:
            seen = group_seen.setdefault(top_pos, set())
            if is_sub and res['canonical_name'] in seen:
                continue
            seen.add(res['canonical_name'])
        if not res:
            unmatched += 1
        if res:
            pw = position_weight(top_pos) * weight_mult
            matched.append({
                'canonical': res['canonical_name'],
                'category':  res['category'],
                'score':     res['base_score'],
                'weighted':  res['base_score'] * pw,
                'position':  top_pos,
                'is_sub':    weight_mult < 1.0,
                'subcategory': res.get('subcategory', ''),
            })

    if not matched:
        return None, None, None, '', '', None, None, ''

    # Flat artificial sweetener penalty (schema v12, 2026-09-23). Position
    # weighting assumes more of an ingredient means more impact. That holds
    # for bulk ingredients but not for high-intensity sweeteners, which are
    # used in milligrams and always sit near the end of a label, so under
    # position weighting sucralose cost a bar a median of -0.27 points.
    # Now each artificial sweetener named anywhere in the ingredient text
    # counts a flat ARTIFICIAL_SW_PENALTY once, regardless of position.
    # Counting keywords in the raw text (not matched ingredients) also
    # catches combined label phrases like "sucralose and acesulfame
    # potassium", which only match a single ingredient entry.
    for m in matched:
        if any(kw in m['canonical'].lower() for kw in ARTIFICIAL_SW):
            m['weighted'] = 0.0
    for kw in ARTIFICIAL_SW:
        if kw in full_lower:
            holder = next((m for m in matched
                           if kw in m['canonical'].lower() and m['weighted'] == 0.0), None)
            if holder is None:
                holder = next((m for m in matched if kw in m['canonical'].lower()), None)
            if holder is not None and holder['weighted'] == 0.0:
                holder['weighted'] = ARTIFICIAL_SW_PENALTY
            else:
                # Named in the text but not matched to an ingredient entry
                # (e.g. inside a combined phrase). Placed at the last label
                # position so it can't change the ingredient count.
                matched.append({
                    'canonical': kw, 'category': 'sweetener', 'score': ARTIFICIAL_SW_PENALTY,
                    'weighted': ARTIFICIAL_SW_PENALTY,
                    'position': max((m['position'] for m in matched), default=1), 'is_sub': True,
                })

    # Restricted additives (scoring v14): one flat penalty per group found in the
    # raw text, regardless of position; their own position-weighted entries are
    # zeroed so they aren't counted twice.
    restricted = [g for g, rx in RESTRICTED_GROUPS.items() if rx.search(full_lower)]
    for m in matched:
        if any(rx.search(m['canonical'].lower()) for rx in RESTRICTED_GROUPS.values()):
            m['weighted'] = 0.0
    for g in restricted:
        matched.append({
            'canonical': g, 'category': 'restricted_additive', 'score': RESTRICTED_PENALTY,
            'weighted': RESTRICTED_PENALTY, 'is_sub': True, 'subcategory': '',
            'position': max((m['position'] for m in matched), default=1),
        })

    # Diminishing credit inside any blend (scoring v13, 2026-09-29, Jeff approved).
    # A parenthetical is one label position, but every member used to earn its
    # own 0.6 share, so "Dried Whole Food Powders (kale, flax, rose hips, ...
    # 14 items)" or "Whole Grains (oats, teff, millet, quinoa, sorghum, chia)"
    # earned 7 to 10 points for trace or one-slot ingredients. Now the positive
    # non-protein members of one parenthetical count 1x, 0.5x, 0.25x ... (best
    # first). Proteins in a blend are handled by the stacking discount below.
    # Negative members (sugar, palm oil inside a coating) are unchanged.
    blend_pos = {}
    for m in matched:
        if (m['is_sub'] or m.get('compound')) and m['weighted'] > 0 and m['category'] != 'protein':
            # Parts of a compound phrase ("rolled oats and oat flour") share one
            # label slot, so they diminish like members of a blend (2026-10-01).
            blend_pos.setdefault((m['position'], m['is_sub']), []).append(m)
    for members in blend_pos.values():
        for i, m in enumerate(sorted(members, key=lambda x: -x['weighted'])):
            m['weighted'] *= BLEND_DIMINISH ** i

    # Diminishing returns on stacked protein sources (schema v7) — see
    # PROTEIN_STACK_DISCOUNT above. Scoring v13 (2026-09-29): applies to every
    # protein-category match, including proteins listed inside a blend. The
    # single best-scoring one keeps full weight.
    prot_all = [m for m in matched if m['category'] == 'protein']
    for i, m in enumerate(sorted(prot_all, key=lambda x: x['weighted'], reverse=True)):
        if i > 0:
            m['weighted'] *= PROTEIN_STACK_DISCOUNT

    top_level_count = max((m['position'] for m in matched), default=0)
    # Grade on the score as displayed (one decimal), 2026-09-24. Grading the
    # unrounded score let a bar show 4.0 with a C or 8.0 with a B; "+ 0.0"
    # turns -0.0 into 0.0 so no bar displays a negative zero.
    # Rounded half up on a cleaned value (2026-10-01): float sums like 7.9499999
    # vs 7.95 made a bar sitting exactly on a grade line round differently from
    # run to run (Jacob Berry 7.95, Kirkland Chocolate Chip Cookie Dough 3.95).
    credit = min(sum(m['weighted'] for m in matched if m['weighted'] > 0), CREDIT_CAP)
    penalty = sum(m['weighted'] for m in matched if m['weighted'] < 0)
    final = round_score(credit + penalty + get_count_adj(top_level_count))
    # Clean-label floor (scoring v13, 2026-09-29, Jeff approved). The score is
    # a sum, so a short label of only top-scoring whole foods ("Cashews, Dates")
    # couldn't add up to an A (5.6) while a longer label with a concern
    # ingredient could. If every ingredient on the label scores 0 or better
    # (no sweetener, oil or additive penalty anywhere, artificial sweeteners
    # included) and the schema knows every ingredient, the bar is at least an
    # A. The displayed score is lifted to the A line so score and grade agree.
    # v14: the floor also tolerates trace minor concerns (only -1 ingredients,
    # adding up to no more than FLOOR_TOLERANCE).
    negs = [m for m in matched if m['score'] < 0 or m['weighted'] < 0]
    minor_only = all(m['score'] == -1 and m['category'] not in ('sweetener', 'restricted_additive') for m in negs)
    if unmatched == 0 and (not negs or (minor_only and -sum(m['weighted'] for m in negs) <= FLOOR_TOLERANCE)):
        final = max(final, CLEAN_LABEL_FLOOR)
    # v14: an added sugar among the first three ingredients caps the grade at B.
    added_sugar_top = [m for m in matched if not m['is_sub'] and m['position'] <= ADDED_SUGAR_TOP
                       and m['category'] == 'sweetener' and m['score'] <= -1
                       and m.get('subcategory', '') not in ADDED_SUGAR_EXCLUDE_SUBCATS
                       and not SA_RE.search(m['canonical'].lower())
                       and not any(k in m['canonical'].lower() for k in ARTIFICIAL_SW)]
    if added_sugar_top and final >= CLEAN_LABEL_FLOOR:
        final = CEILING_SCORE
    band, label = get_band(final)

    sm = sorted(matched, key=lambda x: x['weighted'], reverse=True)
    pos_items = [m['canonical'] for m in sm if m['weighted'] > 0.3][:3]
    neg_items = [m['canonical'] for m in sm if m['weighted'] < -0.3][-3:]
    pos_total = round_score(min(sum(m['weighted'] for m in matched if m['weighted'] > 0), CREDIT_CAP))
    neg_total = round_score(sum(m['weighted'] for m in matched if m['weighted'] < 0))

    insight_str = generate_insights(matched, full_lower, top_level_count)

    return (
        final, band, label,
        ', '.join(pos_items), ', '.join(neg_items),
        pos_total, neg_total, insight_str,
    )


def generate_insights(matched, full_lower, top_level_count):
    """Generate insight chip string for a scored bar."""
    insights = []
    severity = {}

    top_only = [m for m in matched if not m['is_sub']]

    # Positive signals
    if top_only and top_only[0]['category'] == 'protein':
        insights.append(('Protein Leads', 'positive'))

    top5 = [m for m in matched if m['position'] <= 5]
    if any(m['category'] == 'protein' and m['score'] >= 3 for m in top5):
        insights.append(('Quality Protein Source', 'positive'))

    top3_top = [m for m in top_only if m['position'] <= 3]
    wf_positions = {m['position'] for m in top3_top if m['category'] == 'whole_food'}
    if len(wf_positions) >= 2:
        insights.append(('Whole Food Forward', 'positive'))

    if top_level_count <= 8:
        insights.append(('Short Clean List', 'positive'))

    # Neutral signals
    if any(m['category'] == 'vitamin_mineral' for m in matched):
        insights.append(('Fortified', 'neutral'))
    if top_level_count >= 18:
        insights.append(('Long Ingredient List', 'neutral'))

    # Concern signals
    if any(kw in full_lower for kw in ARTIFICIAL_SW):
        insights.append(('Artificial Sweeteners', 'concern'))
        sw_drag = abs(sum(m['weighted'] for m in matched if m['category'] == 'sweetener'))
        sw_top5 = any(m['category'] == 'sweetener' and m['position'] <= 5 for m in matched)
        severity['Artificial Sweeteners'] = 'elevated' if (sw_top5 or sw_drag > 2.0) else 'minor'

    if SA_RE.search(full_lower):
        sa_m = [m for m in matched if SA_RE.search(m['canonical'].lower())]
        sa_drag = abs(sum(m['weighted'] for m in sa_m))
        sa_min  = min((m['position'] for m in sa_m), default=99)
        insights.append(('Sugar Alcohols', 'concern'))
        severity['Sugar Alcohols'] = 'elevated' if (sa_min <= 5 or sa_drag > 2.0) else 'minor'

    has_oil = False
    oil_drag = 0
    for kw in OIL_KEYWORDS:
        if kw in full_lower:
            idx = full_lower.find(kw)
            ctx = full_lower[max(0, idx - 20):idx + len(kw)]
            if not any(ex in ctx for ex in HIGH_OLEIC_EX):
                has_oil = True
                oil_drag = abs(sum(
                    m['weighted'] for m in matched
                    if m['category'] == 'fat_oil' and m['weighted'] < 0
                ))
                break
    if has_oil:
        insights.append(('Processed Oils', 'concern'))
        severity['Processed Oils'] = 'elevated' if oil_drag > 0.5 else 'minor'

    restricted = [m['canonical'] for m in matched if m['category'] == 'restricted_additive']
    if restricted:
        insights.append(('Restricted Additives', 'concern'))
        severity['Restricted Additives'] = 'elevated'

    top3_cats = [m['category'] for m in top_only if m['position'] <= 3]
    if 'sweetener' in top3_cats:
        insights.append(('Sweetener Heavy', 'concern'))
        severity['Sweetener Heavy'] = 'elevated'

    # First protein on the label, including proteins inside a blend (2026-10-01).
    # Looking at top-level items only meant "Protein Blend (whey protein isolate,
    # ...), ..., hydrolyzed gelatin" reported collagen as the main protein.
    prot_any = [m for m in matched if m['category'] == 'protein']
    if prot_any:
        first_prot = min(prot_any, key=lambda x: x['position'])
        if 'collagen' in first_prot['canonical'].lower():
            insights.append(('Collagen Protein', 'concern'))
            severity['Collagen Protein'] = 'elevated'

    return '|'.join(
        f"{n}:{t}:{severity.get(n, '')}" if severity.get(n) else f"{n}:{t}"
        for n, t in insights
    )


# ── Main ──────────────────────────────────────────────────────────────────────
def match_method(norm, al, cl):
    """How lookup_ingredient() resolved `norm`: 'exact', 'variant' or 'partial'."""
    if norm in al or norm in cl:
        return 'exact'
    stripped = norm
    for prefix in SKIP_PREFIXES:
        if stripped.startswith(prefix):
            stripped = stripped[len(prefix):]
            break
    if stripped != norm and (stripped in al or stripped in cl):
        return 'exact'
    for v in ingredient_variants(norm):
        if v != norm and (v in al or v in cl):
            return 'variant'
    return 'partial'


# Words that say what KIND of ingredient a label phrase is. If a phrase
# containing one of these is resolved by the partial-match fallback to an
# ingredient of a different kind, it is very likely a false positive
# (e.g. "tapioca fiber syrup" -> tapioca fiber, "shea butter" -> dairy
# butter, "natural banana flavor" -> banana). Added schema v12, 2026-09-23.
PARTIAL_MATCH_SIGNALS = {
    'syrup': {'sweetener'}, 'sugar': {'sweetener'}, 'nectar': {'sweetener'},
    'honey': {'sweetener'}, 'oil': {'fat_oil'}, 'butter': {'fat_oil', 'whole_food'},
    'flavor': {'flavor_additive'}, 'flavour': {'flavor_additive'},
    'extract': {'flavor_additive', 'botanical_or_functional', 'color_additive'},
    'juice': {'sweetener', 'color_additive'}, 'concentrate': {'sweetener', 'color_additive', 'protein'},
    'protein': {'protein', 'ingredient_group'}, 'fiber': {'fiber_or_functional_carb'},
}


def audit_partial_matches(df, al, cl):
    """List label phrases scored by the partial-match fallback whose own
    wording points to a different kind of ingredient than the one they
    matched. Each one should get an explicit Alias_Map row. Run on every
    database update; an empty list is the goal."""
    suspects = Counter()
    for _, row in df.iterrows():
        raw = str(row.get('Ingredients', ''))
        if not raw or raw == 'nan':
            continue
        for ing_text, _, _ in parse_ingredients(raw):
            norm = normalize(ing_text)
            if len(norm) < 2:
                continue
            res = lookup_ingredient(norm, al, cl)
            if not res or res.get('skip') or match_method(norm, al, cl) != 'partial':
                continue
            if split_compound(norm, al, cl):
                continue   # scored as its separate parts (2026-10-01)
            words = set(norm.split())
            signals = [w for w in PARTIAL_MATCH_SIGNALS if w in words]
            if not signals:
                continue
            allowed = set().union(*(PARTIAL_MATCH_SIGNALS[w] for w in signals))
            if res['category'] in allowed or any(w in res['canonical_name'].lower() for w in signals):
                continue
            suspects[(norm, res['canonical_name'], res['base_score'])] += 1
    if not suspects:
        print('  Partial-match audit: no suspicious guesses found.')
        return
    print(f'  Partial-match audit: {len(suspects)} label phrases were guessed to a '
          f'different kind of ingredient. Add explicit Alias_Map rows for these:')
    for (norm, canon, score), n in suspects.most_common(30):
        print(f'    {n:3d}x  {norm!r} -> {canon} ({score:+g})')


def audit_schema_gaps(df, al, cl):
    """
    Scan all bar ingredient lists for ingredients not found in the schema.
    Prints the top unmatched ingredients by frequency so they can be reviewed
    and added to the schema if appropriate.

    Run this before scoring so gaps are visible before results are finalized.
    """
    unmatched = Counter()
    total_parts = 0

    for _, row in df.iterrows():
        raw = str(row.get('Ingredients', ''))
        if not raw or raw == 'nan':
            continue
        parsed = parse_ingredients(raw)
        for ing_text, top_pos, weight_mult in parsed:
            norm = normalize(ing_text)
            if not norm or len(norm) < 2:
                continue
            total_parts += 1
            if lookup_ingredient(norm, al, cl) is None:
                clean = ing_text.strip()
                if 2 < len(clean) < 60:
                    unmatched[clean] += 1

    if not unmatched:
        print('  Schema audit: all ingredients matched — no gaps found.')
        return

    print(f'  Schema audit: {len(unmatched)} unique unmatched ingredients '
          f'across {total_parts} total ingredient parts.')
    print('  Top unmatched (review and add to schema if significant):')
    for ing, count in unmatched.most_common(20):
        print(f'    {count:3d}x  {ing}')


def main():
    parser = argparse.ArgumentParser(description='Score protein bars and export bars.js')
    parser.add_argument('--db',     required=True, help='Bar database Excel file')
    parser.add_argument('--schema', required=True, help='Scoring schema Excel file — always use the current knowyourbar_scoring_schema_vN.xlsx, check BRIEFING.md for which version is current')
    parser.add_argument('--out',    default='bars.js', help='Output file (default: bars.js)')
    parser.add_argument('--no-audit', action='store_true', help='Skip schema gap audit')
    args = parser.parse_args()

    # Load database
    print(f'Loading database: {args.db}')
    df = pd.read_excel(args.db, sheet_name='BarDB')
    df = df.dropna(subset=['Brand Name', 'Flavor Name'], how='all')
    df = df.drop_duplicates(subset=['Brand Name', 'Flavor Name'], keep='last')
    print(f'  {len(df)} bars after deduplication')

    # Backfill missing/blank Key values so every bar has a stable unique
    # identifier, matching the fallback diff_bars_upload.py's key() function
    # already uses ("Brand Name | Flavor Name"). This only fills rows where
    # Key is missing/blank — existing Key values are never overwritten.
    if 'Key' in df.columns:
        missing_key = df['Key'].isna() | (df['Key'].astype(str).str.strip().isin(['', 'nan', 'None']))
        if missing_key.any():
            df.loc[missing_key, 'Key'] = df.loc[missing_key].apply(
                lambda r: f"{r['Brand Name']} | {r['Flavor Name']}", axis=1
            )
            print(f'  Backfilled {int(missing_key.sum())} missing Key values (Brand Name | Flavor Name fallback)')

    # Load schema (Canonical_Ingredients and Alias_Map only)
    print(f'Loading schema: {args.schema}')
    xl = pd.ExcelFile(args.schema)
    alias_map = pd.read_excel(xl, sheet_name='Alias_Map')
    canonical = pd.read_excel(xl, sheet_name='Canonical_Ingredients')
    print(f'  {len(canonical)} canonicals, {len(alias_map)} aliases')

    # Convert % DV columns
    for col in PCT_DV_COLS:
        if col in df.columns:
            df[col] = (df[col] * 100).round(0).astype('Int64')

    # Build lookup tables
    al, cl = build_lookup(alias_map, canonical)

    # ── Schema gap audit ─────────────────────────────────────────────────────
    # Run before scoring so gaps are visible. Add missing ingredients to the
    # schema before re-running if any significant ones appear.
    if not args.no_audit:
        print('\nAuditing schema coverage...')
        audit_schema_gaps(df, al, cl)
        audit_partial_matches(df, al, cl)

    # Score all bars
    print('\nScoring...')
    scored_count = unscored_count = 0
    for idx, row in df.iterrows():
        ingr = str(row.get('Ingredients', ''))
        s, band, label, pos_str, neg_str, pos_total, neg_total, insight_str = score_bar(ingr, al, cl)
        if s is not None:
            scored_count += 1
        else:
            unscored_count += 1
        df.at[idx, 'ingredient_score']     = s
        df.at[idx, 'score_band']           = band
        df.at[idx, 'score_band_label']     = label
        df.at[idx, 'positive_ingredients'] = pos_str
        df.at[idx, 'concern_ingredients']  = neg_str
        df.at[idx, 'score_pos']            = pos_total
        df.at[idx, 'score_neg']            = neg_total
        df.at[idx, 'score_insights']       = insight_str
        df.at[idx, 'score_source']         = 'auto'

    # Results summary
    bands = Counter(df['score_band'].dropna())
    with_chips = sum(1 for _, r in df.iterrows() if r.get('score_insights'))
    aff = sum(1 for _, r in df.iterrows() if str(r.get('Amazon Affiliate', '')).startswith('http'))

    print(f'\nResults:')
    print(f'  Scored:   {scored_count}')
    print(f'  Unscored: {unscored_count} (missing ingredient data)')
    print(f'  A={bands["A"]} B={bands["B"]} C={bands["C"]} D={bands["D"]} F={bands["F"]}')
    print(f'  With chips: {with_chips} ({with_chips/len(df)*100:.0f}%)')
    print(f'  Affiliate links: {aff}/{len(df)}')

    if unscored_count:
        print(f'\n  Unscored bars:')
        for _, row in df.iterrows():
            if not row.get('score_band'):
                print(f'    {row["Brand Name"]} | {row["Flavor Name"]}')

    # Export bars.js
    df_out = df[[c for c in KEEP_COLS if c in df.columns]].copy()
    df_out = df_out.where(pd.notna(df_out), None)
    for col in df_out.columns:
        if df_out[col].dtype == object:
            df_out[col] = df_out[col].apply(lambda x: x.strip() if isinstance(x, str) else x)

    bars_list = df_out.to_dict(orient='records')
    js = 'const BARS = ' + json.dumps(bars_list, separators=(',', ':')) + ';'
    js = js.replace(':NaN,', ':null,').replace(':NaN}', ':null}')

    with open(args.out, 'w') as f:
        f.write(js)

    size_kb = os.path.getsize(args.out) // 1024
    print(f'\nExported: {args.out} ({len(bars_list)} bars, {size_kb}KB)')
    print('Done. Upload bars.js to GitHub.')


if __name__ == '__main__':
    main()
