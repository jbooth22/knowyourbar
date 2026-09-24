"""Ingredient-level counts over bars.js, shared by the ingredient pages
(all-ingredients.html, ingredient-report.html).

Each bar's ingredient text is parsed and matched with the SAME code the
scorer uses (score_and_export.parse_ingredients / normalize /
lookup_ingredient) against the current scoring schema, so an ingredient's
name, category and score on these pages always match how bars are scored.

  bars     = number of bars that contain the ingredient anywhere on the
             label, including inside a compound ingredient ("chocolate
             coating (sugar, palm kernel oil ...)")
  top      = number of bars that list it as a top-level ingredient
  score    = base score from the Canonical_Ingredients sheet (a few Alias_Map
             rows carry a different score; see alias_score_conflicts()),
  category = schema category,
  desc     = schema explanation (em dashes shown as a colon, per site style)
"""
import re
from collections import Counter
import pandas as pd
import score_and_export as sx
from kyb_guide_lib import load_bars

SCHEMA = 'knowyourbar_scoring_schema_v12.xlsx'
# Schema categories that are label notes, not ingredients.
NOT_INGREDIENTS = {'qualifier_note', 'other', 'descriptor', 'allergen_or_contains_statement'}


# The schema's explanation column doubles as a change log ("[v12_scale_2026-09-23]",
# "was 0", "Corrected 2026-09-08: ..."). public_desc() strips that so only the
# reader-facing description reaches the site. Explanations that are nothing
# but a change note get a written description here.
PUBLIC_DESC = {
    'agave syrup': 'Refined sweetener syrup from the agave plant',
    'cane syrup': 'Refined sugar syrup from sugar cane',
    'invert cane syrup': 'Cane sugar syrup split into glucose and fructose',
    'brown rice crisps': 'Puffed brown rice pieces',
    'rice crisps': 'Puffed rice pieces',
    'hydrogenated vegetable oil': 'Hydrogenated oil: a highly processed fat, scored at the palm kernel oil level',
    'milk': 'Plain milk, scored the same as other plain milk forms',
    'milk powder': 'Dried milk, scored the same as whole milk powder and skim milk powder',
    'cashews': 'Whole nuts, scored the same as almonds and peanuts',
    'blueberries': 'Whole fruit',
    'palm fruit oil': 'Palm fruit oil is palm oil',
    'dried cranberries': 'Almost always sugar-infused, so one point below whole cranberries',
    'shea butter': 'Plant fat used in coatings',
    'canola protein': 'Plant protein from canola, scored the same as other plant proteins',
    'date paste': 'Dates in paste form, scored the same as dates',
    'raisin paste': 'Raisins in paste form, scored the same as raisins',
    'oligofructose': 'Plant-extracted fiber from chicory or inulin, scored the same as fructooligosaccharides',
    'agave inulin': 'Inulin fiber extracted from agave, scored the same as inulin',
    'acesulfame potassium': 'Artificial sweetener; every artificial sweetener carries the same flat -2',
}
INTERNAL = re.compile(r'\[|\bv1\d|\b20\d\d-\d\d|misfil|\bwas\b|\bwere\b|corrected|schema|alias|canonical|unclassified|'
                      r'plural of|set to|database update|matched to', re.I)


def public_desc(name, text):
    if name in PUBLIC_DESC:
        return PUBLIC_DESC[name]
    t = re.sub(r'\s*\[[^\]]*\]', '', text)                       # [v12_scale_2026-09-23]
    t = re.sub(r'\s*\((v1\d[^)]*|was [^)]*)\)', '', t)             # (v12 fiber scale) (was 0, ...)
    t = re.sub(r'\s*(Corrected|Added) 20\d\d-\d\d-\d\d.*$', '', t)   # trailing change notes
    t = re.sub(r'\.\s*Added 20\d\d-\d\d-\d\d.*$', '', t)
    t = re.sub(r';\s*\w+ were [^;.]*', '', t)
    t = re.sub(r'[;.]\s*[Ww]as [^;.]*', '', t)
    t = t.replace(' \u2014 ', ': ').replace('\u2014', ', ').replace(' -- ', ', ')
    t = re.sub(r':\s*[+-]?\d\s*$', '', t.strip())                   # trailing ': -1' (the badge shows the score)
    return t.strip().rstrip('.;:, ').strip()


def load_schema(path=SCHEMA):
    xl = pd.ExcelFile(path)
    canon = pd.read_excel(xl, 'Canonical_Ingredients')
    al, cl = sx.build_lookup(pd.read_excel(xl, 'Alias_Map'), canon)
    return canon, al, cl


def ingredient_counts(bars=None, path=SCHEMA):
    """Returns (rows, n_bars, canon_df). rows: {canonical_name: dict(bars, top, score, category, desc)}."""
    bars = bars if bars is not None else load_bars()
    canon, al, cl = load_schema(path)
    expl, base = {}, {}
    for n, e, sc in zip(canon.canonical_name, canon.explanation, canon.base_score):
        expl.setdefault(n, '' if pd.isna(e) else str(e).strip())
        base.setdefault(n, sc)
    cnt, top, meta = Counter(), Counter(), {}
    for b in bars:
        seen, tp = set(), set()
        for text, pos, mult in sx.parse_ingredients(b.get('Ingredients') or ''):
            norm = sx.normalize(text)
            if not norm or len(norm) < 2:
                continue
            r = sx.lookup_ingredient(norm, al, cl)
            if not r or r.get('skip'):
                continue
            k = r['canonical_name']
            seen.add(k)
            meta[k] = (r['category'], r['base_score'])
            if mult == 1.0:
                tp.add(k)
        cnt.update(seen)
        top.update(tp)
    rows = {k: dict(bars=cnt[k], top=top[k], category=meta[k][0], score=int(base[k] if k in base and pd.notna(base[k]) else meta[k][1]),
                    desc=public_desc(k, expl.get(k, ''))) for k in cnt}
    return rows, len(bars), canon


def alias_score_conflicts(path=SCHEMA):
    """Alias_Map rows whose base_score differs from their canonical's score."""
    xl = pd.ExcelFile(path)
    canon, al = pd.read_excel(xl, 'Canonical_Ingredients'), pd.read_excel(xl, 'Alias_Map')
    cs = dict(zip(canon.canonical_id, canon.base_score))
    out = []
    for t, cid, n, s in zip(al.alias_text_exact, al.canonical_id, al.canonical_name, al.base_score):
        if pd.notna(s) and pd.notna(cs.get(cid)) and cs[cid] != s:
            out.append((str(t), str(n), int(s), int(cs[cid])))
    return out


def bar_ingredients(bars, path=SCHEMA):
    """Per bar: list of dicts(name, pos, sub, category, subcategory) in label order,
    matched the same way the scorer matches (label notes excluded)."""
    canon, al, cl = load_schema(path)
    subcat = {}
    for n, s in zip(canon.canonical_name, canon.subcategory):
        subcat.setdefault(n, '' if pd.isna(s) else str(s))
    out = []
    for b in bars:
        items = []
        for text, pos, mult in sx.parse_ingredients(b.get('Ingredients') or ''):
            norm = sx.normalize(text)
            if not norm or len(norm) < 2:
                continue
            r = sx.lookup_ingredient(norm, al, cl)
            if not r or r.get('skip') or r['category'] in NOT_INGREDIENTS:
                continue
            items.append(dict(name=r['canonical_name'], pos=pos, sub=mult < 1.0, category=r['category'],
                              subcategory=subcat.get(r['canonical_name'], '')))
        out.append(items)
    return out
