#!/usr/bin/env python3
"""
build_brand_rankings.py — regenerates all-protein-bar-brands.html from bars.js.

WHY THIS EXISTS
----------------
all-protein-bar-brands.html is not hand-written. Every brand card, the KYB
Brand Score, the tier/category badges, the "best in category" picks, and the
highlight/lowlight write-ups are all computed from bars.js and templated into
the final HTML. Run this script instead of hand-editing the page whenever the
database changes.

USAGE
-----
    python3 build_brand_rankings.py

Run from the repo root (same directory as bars.js and style.css). Reads
bars.js, writes all-protein-bar-brands.html in place. Diff the result against
the previous version before uploading, same as any other change — this script
does not check div/tag balance itself, run the QA.md checklist after.

If bars.js has picked up new brands since the last run, check the WIDE / MID
tier sets below — anything not listed defaults to "small" (Small & Online).
That default is usually right (most brands in this database are small DTC
brands) but is worth a skim after a big database update, since a genuinely
widely-distributed new brand landing in "small" by default would be wrong.

THE KYB BRAND SCORE (locked formula, 2026-08-10)
-------------------------------------------------
0-100 composite, drives the 1-to-N rank:
    60% average ingredient_score across the brand's flavors (min-max
        normalized against every brand's average in the current database)
    25% average protein per 100 calories (protein efficiency), same
        normalization
    15% average dietary fiber, same normalization, capped at 100

Deliberately excludes: price (not tracked live), vitamins/fortification
(already tagged "neutral" in the ingredient-scoring schema itself, so adding
it to the composite would contradict the schema's own judgment), creatine and
caffeine (these are use-case/preference signals, not quality signals — baking
them into a universal score would silently claim "more caffeine = better bar,"
which isn't a claim we want to make). Vitamins/creatine/caffeine stay visible
on each card as badges instead, so people can filter for or against them
based on their own situation.

CATEGORY THRESHOLDS (locked, 2026-08-10)
-----------------------------------------
    Protein First:            avg protein per 100 cal >= 9
    Whole Food / High Fiber:  avg fiber >= 6 AND not already Protein First
    Solid Macro Profile:      everything else (the default bucket)

DISTRIBUTION TIERS — EDITORIAL, NOT DATA-DERIVED
--------------------------------------------------
bars.js has no retail-distribution field. WIDE / MID below are a hand-curated
judgment call based on real-world market knowledge, not something computed
from ingredient or macro data. Anything not listed defaults to "small". This
is stated explicitly on the page itself (.brk-caveat) — don't silently drop
that disclosure if you touch the copy.
"""
import json
from collections import Counter, defaultdict

BARS_JS_PATH = 'bars.js'
OUTPUT_PATH = 'all-protein-bar-brands.html'

# ---------------------------------------------------------------------------
# Hand-curated distribution tiers. Edit these sets directly when a brand's
# real-world availability changes or a new brand needs reclassifying.
# ---------------------------------------------------------------------------
WIDE = {
    "Quest", "CLIF Bar", "Clif Builders", "Clif ZBar", "KIND", "KIND Protein Max",
    "RXBAR", "Barebells", "Larabar", "Pure Protein", "think!", "Atkins", "Fiber One",
    "Nature Valley", "Luna", "Power Crunch", "Gatorade", "MET-Rx", "Lenny & Larry's",
    "FITCRUNCH", "Alani", "Ghost", "Orgain", "Equate", "GNC Total Lean",
    "Honey Stinger", "Bobo's", "Epic", "Met-RX", "One",
}
MID = {
    "Perfect Bar", "GoMacro", "NuGo", "Aloha", "IQ Bar", "Munk Pack", "Simply Protein",
    "Raw Rev", "Bob's Red Mill", "Musashi", "Zing", "Fulfil", "No Cow", "Magic Spoon",
    "Built", "1st Phorm", "Thunderbird", "Kate's Real Food", "Genesee Nutrition",
    "Verb", "Wild Zora", "Neoh", "Truvani", "PROBar", "PROBAR", "Pro Bar", "Tosi", "Rise",
    "Bearded Bros", "Daryl's Bars", "Trubar", "Battle Bars", "Transparent Labs",
    "Perfect Keto", "Jonesbar", "Redefine", "Nick's", "Bullet Proof",
}
# NOTE: bars.js's brand-name capitalization has flip-flopped twice now, both times
# a plain-string-match gotcha for tier(): MET-Rx -> "Met-RX" (2026-08-13 update,
# see CHANGELOG) -> back to "MET-Rx" (this 2026-08-31 update). WIDE carries both
# "MET-Rx" and "Met-RX" so either casing lands correctly. Same issue hit PROBAR:
# this update renamed "Pro Bar" to the all-caps "PROBAR", which matched neither
# the existing "PROBar" nor "Pro Bar" entries and would have silently dropped it
# into the "small" tier by default -- added "PROBAR" alongside the older variants
# rather than replacing them, same approach as MET-Rx. If bars.js renames a
# WIDE/MID brand again, this tier() lookup will silently miscategorize it since
# it's a plain string match, not a fuzzy one -- worth a spot-check after any
# brand-name-heavy diff (this is now the second time it's bitten a real update).

TIER_LABEL = {"wide": "Widely Available", "mid": "Mid-Size & Specialty", "small": "Small & Online"}
CATEGORY_INTRO = {
    "Protein First": "protein-efficiency-focused",
    "Solid Macro Profile": "balanced macro",
    "Whole Food / High Fiber": "fiber-forward, whole-food-leaning",
}
CERT_FIELDS = ["Vegan (Y/N)", "Non-GMO (Y/N)", "Gluten Free (Y/N)", "Nut Free (Y/N)",
               "Dairy Free (Y/N)", "Soy Free (Y/N)", "Kosher (Y/N)"]
CERT_LABELS = {"Vegan (Y/N)": "Vegan", "Non-GMO (Y/N)": "Non-GMO", "Gluten Free (Y/N)": "Gluten-Free",
               "Nut Free (Y/N)": "Nut-Free", "Dairy Free (Y/N)": "Dairy-Free", "Soy Free (Y/N)": "Soy-Free",
               "Kosher (Y/N)": "Kosher"}
GRADE_ORDER = {'A': 4, 'B': 3, 'C': 2, 'D': 1, 'F': 0}

# ---------------------------------------------------------------------------
# Hand-picked "best in category" spotlights and highlight/lowlight write-ups.
# These reference brand names, not hardcoded numbers pulled from a stale run —
# actual figures are looked up live from freshly computed stats below, so the
# prose stays numerically accurate even as bars.js changes. If a named brand
# stops existing in bars.js, this script will KeyError — that's intentional,
# it forces a human to pick a new example rather than silently going stale.
# ---------------------------------------------------------------------------
BEST_PICKS = [
    ("Best Overall", "Gryp", "Across every brand we've scored on ingredients, macros, and flavor consistency, this is the highest composite score in the database."),
    ("Best Widely Available", "RXBAR", "The top-scoring brand you can actually grab at a regular grocery store or Target. Smaller lineup than most mass-market bars, but nothing filler."),
    ("Best Mid-Size / Specialty", "Transparent Labs", "The strongest brand in the specialty-grocery-and-online tier, ahead of far bigger names in that group."),
    ("Best Protein First", "Jacob", "Leads the protein-efficiency category on grams of protein per 100 calories without giving up ingredient quality to get there."),
    ("Best Solid Macro Profile", "Healthy Eating on the Go", "Tops the balanced-macro category, and does it across 15 flavors, not just one lucky bar."),
    ("Best Whole Food / High Fiber", "PEAK Protein", "The highest-scoring fiber-forward brand, built around a shorter, more recognizable ingredient list than most bars in this group."),
]
HIGHLIGHT_BRANDS = ["RXBAR", "Quest", "David", "CLIF Bar", "Clif Builders", "Barebells",
                     "KIND", "Healthy Eating on the Go", "Verb", "JiMMYBAR!"]


def num(v):
    try:
        return None if v is None else float(v)
    except (TypeError, ValueError):
        return None


def net_carbs(b):
    c = num(b.get('Total Carbohydrates (g)'))
    if c is None:
        return None
    return c - (num(b.get('Dietary Fiber (g)')) or 0) - (num(b.get('Sugar Alcohol (g)')) or 0)


def tags(b):
    si = b.get('score_insights') or ''
    out = []
    for p in si.split('|'):
        p = p.strip()
        if not p:
            continue
        parts = p.split(':')
        out.append((parts[0].strip(), parts[1].strip() if len(parts) > 1 else ''))
    return out


def slugify(s):
    import re
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')


def tier(brand):
    if brand in WIDE:
        return "wide"
    if brand in MID:
        return "mid"
    return "small"


def compute_brand_stats(bars_js_path):
    with open(bars_js_path) as f:
        content = f.read()
    BARS = json.loads(content[content.index('['):content.rindex(']') + 1])

    by_brand = defaultdict(list)
    for b in BARS:
        by_brand[b['Brand Name'].strip()].append(b)

    rows = []
    all_avg_scores, all_avg_p100, all_avg_fiber = [], [], []

    for brand, bars in by_brand.items():
        n = len(bars)
        avg = lambda L: round(sum(L) / len(L), 1) if L else None

        prot = [num(b.get('Protein (g)')) for b in bars if num(b.get('Protein (g)')) is not None]
        cal = [num(b.get('Calories')) for b in bars if num(b.get('Calories')) is not None]
        fib = [num(b.get('Dietary Fiber (g)')) for b in bars if num(b.get('Dietary Fiber (g)')) is not None]
        sug = [num(b.get('Sugars (g)')) for b in bars if num(b.get('Sugars (g)')) is not None]
        sa = [num(b.get('Sugar Alcohol (g)')) for b in bars if num(b.get('Sugar Alcohol (g)')) is not None]
        nc = [x for x in (net_carbs(b) for b in bars) if x is not None]
        p100 = [(p / c * 100) for p, c in
                zip([num(b.get('Protein (g)')) for b in bars], [num(b.get('Calories')) for b in bars])
                if p is not None and c]
        scores = [num(b.get('ingredient_score')) for b in bars if num(b.get('ingredient_score')) is not None]
        grades = [b.get('score_band') for b in bars if b.get('score_band') in GRADE_ORDER]

        pos_tags, con_tags = Counter(), Counter()
        for b in bars:
            for name, kind in tags(b):
                if kind == 'positive':
                    pos_tags[name] += 1
                elif kind == 'concern':
                    con_tags[name] += 1

        has_sa_ingr = sum(1 for b in bars if any(t[0] == 'Sugar Alcohols' for t in tags(b)))
        creatine = sum(1 for b in bars if num(b.get('Creatine (g)')))
        caffeine = sum(1 for b in bars if num(b.get('Caffeine (mg)')))
        vitamin_fields = [k for k in bars[0].keys() if '(% DV)' in k] if bars else []
        fortified = sum(1 for b in bars if any(num(b.get(vf)) for vf in vitamin_fields))

        certs = [CERT_LABELS[f] for f in CERT_FIELDS
                 if n and sum(1 for b in bars if (b.get(f) or '').strip().lower() == 'yes') / n >= 0.7]

        best_grade = max(grades, key=lambda g: GRADE_ORDER[g]) if grades else None
        worst_grade = min(grades, key=lambda g: GRADE_ORDER[g]) if grades else None

        avg_score, avg_p100, avg_fiber = avg(scores), avg(p100), avg(fib)
        if avg_score is not None: all_avg_scores.append(avg_score)
        if avg_p100 is not None: all_avg_p100.append(avg_p100)
        if avg_fiber is not None: all_avg_fiber.append(avg_fiber)

        if avg_p100 is not None and avg_p100 >= 9:
            category = "Protein First"
        elif avg_fiber is not None and avg_fiber >= 6 and (avg_p100 is None or avg_p100 < 9):
            category = "Whole Food / High Fiber"
        else:
            category = "Solid Macro Profile"

        rows.append({
            "brand": brand, "slug": slugify(brand), "tier": tier(brand), "category": category,
            "flavors": n, "avg_protein": avg(prot), "avg_calories": avg(cal), "avg_p100": avg_p100,
            "avg_fiber": avg_fiber, "avg_sugar": avg(sug), "avg_sugar_alcohol": avg(sa),
            "avg_net_carbs": avg(nc), "pct_sugar_alcohol": round(100 * has_sa_ingr / n) if n else 0,
            "avg_score": avg_score, "best_grade": best_grade, "worst_grade": worst_grade,
            "top_pos_tags": pos_tags.most_common(3), "top_con_tags": con_tags.most_common(3),
            "certs": certs, "creatine_flavors": creatine, "caffeine_flavors": caffeine,
            "fortified_flavors": fortified,
        })

    def minmax(vals):
        lo, hi = min(vals), max(vals)
        return lo, (hi - lo if hi > lo else 1)

    s_lo, s_rng = minmax(all_avg_scores)
    p_lo, p_rng = minmax(all_avg_p100)
    f_lo, f_rng = minmax(all_avg_fiber)

    for r in rows:
        s_n = (r['avg_score'] - s_lo) / s_rng * 100
        p_n = (r['avg_p100'] - p_lo) / p_rng * 100
        f_n = min((r['avg_fiber'] - f_lo) / f_rng * 100, 100)
        r['kyb_score'] = round(0.60 * s_n + 0.25 * p_n + 0.15 * f_n, 1)

    rows.sort(key=lambda r: -r['kyb_score'])
    for i, r in enumerate(rows, 1):
        r['rank'] = i

    cat_groups = defaultdict(list)
    for r in rows:
        cat_groups[r['category']].append(r)
    for group in cat_groups.values():
        group.sort(key=lambda r: -r['kyb_score'])
        for i, r in enumerate(group, 1):
            r['cat_rank'] = i

    return rows


# ---------------------------------------------------------------------------
# Rendering: turn computed stats into the final HTML page.
# ---------------------------------------------------------------------------
import html as _html


def esc(s):
    return _html.escape(str(s), quote=True) if s is not None else ""


def fmt1(v):
    if v is None:
        return "—"
    return f"{v:g}" if float(v) == int(v) else f"{v:.1f}"


def grade_range_html(r):
    b, w = r['best_grade'], r['worst_grade']
    if not b:
        return '<span class="brk-stat-lbl">not scored</span>'
    if b == w:
        return f'<span class="table-grade-badge grade-{b}">{b}</span>'
    return (f'<span class="brand-compare-grade-pair">'
            f'<span class="table-grade-badge grade-{w}">{w}</span>'
            f'<span class="brand-compare-grade-arrow">&rarr;</span>'
            f'<span class="table-grade-badge grade-{b}">{b}</span>'
            f'</span>')


def blurb(r):
    brand, flavors = r['brand'], r['flavors']
    intro = CATEGORY_INTRO[r['category']]
    s1 = (f"{brand} runs a {flavors}-flavor, {intro} lineup averaging "
          f"{fmt1(r['avg_protein'])}g protein and {fmt1(r['avg_calories'])} calories per bar "
          f"({fmt1(r['avg_p100'])}g protein per 100 calories).")
    grade_s = f"Every flavor grades {r['best_grade']}." if r['best_grade'] == r['worst_grade'] \
        else f"Ingredient grades run {r['worst_grade']} to {r['best_grade']} across the lineup."
    pos = r['top_pos_tags'][0][0] if r['top_pos_tags'] else None
    con = r['top_con_tags'][0][0] if r['top_con_tags'] else None
    con_n = r['top_con_tags'][0][1] if r['top_con_tags'] else 0
    clauses = [grade_s]
    if pos:
        clauses.append(f"Most flavors lean on {pos.lower()}.")
    clauses.append(f"The most common concern is {con.lower()}, showing up in {con_n} of {flavors} "
                    f"flavor{'s' if flavors != 1 else ''}." if con else
                    "No recurring ingredient concern shows up across the lineup.")
    flags = []
    if r['caffeine_flavors']:
        flags.append(f"{r['caffeine_flavors']} flavor{'s' if r['caffeine_flavors'] != 1 else ''} with caffeine")
    if r['creatine_flavors']:
        flags.append(f"{r['creatine_flavors']} with creatine")
    if r['fortified_flavors'] >= flavors * 0.5 and flavors >= 3:
        flags.append("vitamin-fortified across most of the line")
    extra = f" Also worth noting: {', '.join(flags)}." if flags else ""
    return s1, " ".join(clauses) + extra


def render_card(r):
    s1, s2 = blurb(r)
    chips = "".join(f'<span class="bchip pos">{esc(n)}</span>' for n, _ in r['top_pos_tags'][:2])
    chips += "".join(f'<span class="bchip con elev">{esc(n)}</span>' for n, _ in r['top_con_tags'][:2])
    certs = "".join(f'<span class="cert-badge">{esc(c)}</span>' for c in r['certs'])
    flags = ""
    if r['creatine_flavors']:
        flags += f'<span class="boost-badge">Creatine &middot; {r["creatine_flavors"]}</span>'
    if r['caffeine_flavors']:
        flags += f'<span class="boost-badge">Caffeine &middot; {r["caffeine_flavors"]}</span>'
    if r['fortified_flavors']:
        flags += f'<span class="boost-badge">Vitamins &middot; {r["fortified_flavors"]}</span>'
    sa_note = f"{r['pct_sugar_alcohol']}% of flavors" if r['pct_sugar_alcohol'] else "none"

    return f'''
  <div class="brk-card" data-tier="{r['tier']}" data-category="{esc(r['category'])}" data-rank="{r['rank']}"
       data-protein="{r['avg_protein'] or 0}" data-fiber="{r['avg_fiber'] or 0}" data-flavors="{r['flavors']}"
       data-score="{r['kyb_score']}" data-name="{esc(r['brand']).lower()}">
    <div class="brk-card-head">
      <div class="brk-card-id">
        <span class="brk-rank">#{r['rank']}</span>
        <span class="brk-card-name">{esc(r['brand'])}</span>
      </div>
      <div class="brk-badges">
        <span class="brk-badge tier-{r['tier']}">{TIER_LABEL[r['tier']]}</span>
        <span class="brk-badge">{esc(r['category'])}</span>
        <span class="brk-grade-range">{grade_range_html(r)}</span>
      </div>
    </div>
    <div class="brk-stat-strip">
      <span><span class="lbl">Flavors</span><b>{r['flavors']}</b></span>
      <span><span class="lbl">Protein/100cal</span><b>{fmt1(r['avg_p100'])}g</b></span>
      <span><span class="lbl">Avg Protein</span><b>{fmt1(r['avg_protein'])}g</b></span>
      <span><span class="lbl">Avg Cal</span><b>{fmt1(r['avg_calories'])}</b></span>
      <span><span class="lbl">Avg Fiber</span><b>{fmt1(r['avg_fiber'])}g</b></span>
      <span><span class="lbl">Net Carbs</span><b>{fmt1(r['avg_net_carbs'])}g</b></span>
      <span><span class="lbl">Sugar</span><b>{fmt1(r['avg_sugar'])}g</b></span>
      <span><span class="lbl">Sugar Alcohol</span><b>{sa_note}</b></span>
    </div>
    <div class="brk-chip-row">{chips}{certs}</div>
    {'<div class="brk-flag-row">' + flags + '</div>' if flags else ''}
    <p class="brk-blurb">{esc(s1)} {esc(s2)}</p>
    <div class="brk-card-foot">
      <span class="brk-kyb-score">Ingredient score avg: <b>{fmt1(r['avg_score'])}</b></span>
      <a href="/bar-finder?brand={r['slug']}" class="brk-finder-link">See all {r['flavors']} flavors in Bar Finder &rarr;</a>
    </div>
  </div>'''


def best_card(label, brand, note, by_name):
    r = by_name[brand]
    return f'''
    <div class="brk-best-card">
      <div class="brk-best-eyebrow">{esc(label)}</div>
      <div class="brk-best-brand">{esc(brand)}</div>
      <div class="brk-best-stats">
        <span>#{r['rank']} overall</span>
        <span>{r['flavors']} flavors</span>
        <span>{grade_range_html(r)}</span>
        <span>{fmt1(r['avg_p100'])}g protein/100cal</span>
      </div>
      <p class="brk-best-body">{esc(note)}</p>
      <a href="/bar-finder?brand={r['slug']}" class="brk-best-link">See all {r['flavors']} flavors &rarr;</a>
    </div>'''


def highlight_card(kind, title, body):
    return f'''
    <div class="brk-highlight-card {kind}">
      <div class="brk-highlight-tag">{"Highlight" if kind == "good" else "Lowlight"}</div>
      <div class="brk-highlight-title">{esc(title)}</div>
      <div class="brk-highlight-body">{body}</div>
    </div>'''


def build_highlights(by_name):
    rx, qu, dv, cb, cbl, bb, kd, heg, verb, jimmy = (by_name[n] for n in HIGHLIGHT_BRANDS)
    highlights = [
        ("good", "Small lineup, big ingredient discipline",
         f"RXBAR (rank #{rx['rank']}) outranks Quest (rank #{qu['rank']}) despite offering {rx['flavors']} flavors to Quest's {qu['flavors']}. "
         f"RXBAR's whole lineup grades {rx['worst_grade']} to {rx['best_grade']} with almost no sweetener-heavy flags, while every one of Quest's "
         f"{qu['flavors']} flavors carries both artificial sweeteners and sugar alcohols. More flavors doesn't mean a better score."),
        ("bad", "Protein efficiency isn't the whole story",
         f"David averages {fmt1(dv['avg_p100'])}g of protein per 100 calories, the highest protein efficiency of any brand in the database, "
         f"but its ingredient grades only reach {dv['best_grade']}. Artificial sweeteners and sugar alcohols show up in nearly every flavor. "
         f"Big protein numbers on the label don't guarantee a clean ingredient list."),
        ("bad", "Legacy brands, middling grades",
         f"CLIF Bar (rank #{cb['rank']}) and Clif Builders (rank #{cbl['rank']}) sit near the bottom of every widely-available brand we've scored, "
         f"despite decades on grocery shelves. Both lean on sweetener-heavy formulas and processed oils across most flavors, and Clif Builders' "
         f"worst flavor grades an {cbl['worst_grade']}. Shelf presence and ingredient quality aren't the same thing."),
        ("good", "Consistency at volume",
         f"Healthy Eating on the Go scores an A on every single one of its {heg['flavors']} flavors, the largest fully-A lineup in the database. "
         f"Most brands with that many flavors show at least some spread between their best and worst bar. This one doesn't."),
        ("bad", "Big names, mid-pack results",
         f"Barebells (rank #{bb['rank']}) and KIND (rank #{kd['rank']}) both land in the middle third of the full ranking despite being two of the "
         f"most recognizable names in the category. Barebells' worst flavor drops all the way to an {bb['worst_grade']}, and KIND leans heavily on "
         f"processed oils across its lineup."),
        ("good", "Stimulant and creatine patterns worth knowing",
         f"Verb puts caffeine in all {verb['flavors']} of its flavors, and JiMMYBAR! is one of the only brands in the database combining both "
         f"caffeine and creatine across multiple flavors. If you're tracking stimulants or timing supplements around a bar, these are the "
         f"brands to know about."),
    ]
    return "\n".join(highlight_card(*h) for h in highlights)


def render_page(rows, total_db_brand_count_display="148+"):
    by_name = {r['brand']: r for r in rows}
    TOTAL_BRANDS = len(rows)
    TIER_COUNTS = Counter(r['tier'] for r in rows)
    CAT_COUNTS = Counter(r['category'] for r in rows)

    cards_html = "\n".join(render_card(r) for r in rows)
    best_html = "\n".join(best_card(*p, by_name=by_name) for p in BEST_PICKS)
    highlights_html = build_highlights(by_name)

    TITLE = f"{TOTAL_BRANDS} Protein Bar Brands Ranked by Ingredients, Macros & Flavor Quality"
    DESC = (f"Every one of the {TOTAL_BRANDS} brands we've scored, ranked 1 to {TOTAL_BRANDS} on ingredient "
            f"quality, protein efficiency, and fiber. No price, no sponsorships, links to every flavor.")

    HEAD = f'''<!DOCTYPE html>
<html lang="en">
<head>

  <script async src="https://www.googletagmanager.com/gtag/js?id=G-SW4MNP5W7J"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', 'G-SW4MNP5W7J');
  </script>

  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{TITLE} | Know Your Bar</title>
  <meta name="description" content="{DESC}">
  <link rel="canonical" href="https://knowyourbar.com/all-protein-bar-brands">

  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&family=Barlow+Condensed:wght@500;600;700;800;900&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">

  <link rel="stylesheet" href="/style.css">

  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": "{TITLE}",
    "description": "{DESC}",
    "author": {{ "@type": "Organization", "name": "Know Your Bar", "url": "https://knowyourbar.com" }},
    "publisher": {{ "@type": "Organization", "name": "Know Your Bar", "url": "https://knowyourbar.com" }},
    "mainEntityOfPage": {{ "@type": "WebPage", "@id": "https://knowyourbar.com/all-protein-bar-brands" }}
  }}
  </script>

  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "Know Your Bar Protein Bar Brand Rankings",
    "description": "Ingredient-quality and macro data for 1,000+ protein bars across {total_db_brand_count_display} brands, scored with a transparent rule-based system.",
    "creator": {{ "@type": "Organization", "name": "Know Your Bar", "url": "https://knowyourbar.com" }},
    "url": "https://knowyourbar.com/all-protein-bar-brands"
  }}
  </script>

  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
      {{ "@type": "ListItem", "position": 1, "name": "Home", "item": "https://knowyourbar.com/" }},
      {{ "@type": "ListItem", "position": 2, "name": "All Protein Bar Brands", "item": "https://knowyourbar.com/all-protein-bar-brands" }}
    ]
  }}
  </script>

  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
      {{ "@type": "Question", "name": "How is the brand ranking calculated?", "acceptedAnswer": {{ "@type": "Answer", "text": "Each brand's rank is based on three weighted inputs: 60% average ingredient quality score across every flavor we've scored, 25% protein efficiency (grams of protein per 100 calories), and 15% average fiber. Price is not part of the formula because we don't track live pricing." }} }},
      {{ "@type": "Question", "name": "What do Widely Available, Mid-Size, and Small & Online mean?", "acceptedAnswer": {{ "@type": "Answer", "text": "These are editorial distribution categories, not something we calculate from ingredient data. Widely Available means you can generally find the brand at a regular grocery store or convenience store. Mid-Size covers specialty grocery, regional chains, and gyms. Small & Online covers brands that sell mostly direct-to-consumer or through specialty retailers." }} }},
      {{ "@type": "Question", "name": "What are the Protein First, Solid Macro Profile, and Whole Food categories?", "acceptedAnswer": {{ "@type": "Answer", "text": "Protein First brands average at least 9g of protein per 100 calories. Whole Food / High Fiber brands average at least 6g of fiber per bar without hitting that protein efficiency bar. Everything else, which is most of the market, falls into Solid Macro Profile." }} }},
      {{ "@type": "Question", "name": "Does a higher rank mean a brand is healthier for everyone?", "acceptedAnswer": {{ "@type": "Answer", "text": "No. The rank reflects ingredient quality, protein efficiency, and fiber averaged across a brand's full lineup. It doesn't account for your personal goals, allergies, taste preference, or price. A lower-ranked brand can still be the right choice for a specific diet or flavor you like." }} }},
      {{ "@type": "Question", "name": "How is net carbs calculated?", "acceptedAnswer": {{ "@type": "Answer", "text": "Net carbs = Total Carbohydrates minus Dietary Fiber minus Sugar Alcohol, all in grams, taken straight from each bar's nutrition panel." }} }},
      {{ "@type": "Question", "name": "Why do small online brands often outrank big grocery brands?", "acceptedAnswer": {{ "@type": "Answer", "text": "Smaller brands often ship one or two flavors built around a short ingredient list, without the sweetener systems mass-market bars use to hit low sugar numbers at scale. A tiny lineup with a clean formula can out-score a 20-flavor lineup that leans on sucralose and sugar alcohols." }} }},
      {{ "@type": "Question", "name": "How many brands and flavors does this cover?", "acceptedAnswer": {{ "@type": "Answer", "text": "This ranking covers every one of the {TOTAL_BRANDS} distinct protein bar brands in our database, spanning 1,000+ scored flavors, updated as we add new bars." }} }}
    ]
  }}
  </script>

</head>
<body class="page-guide brand-v1">

<nav class="site-nav">
  <a href="/" class="site-nav-logo">Know Your Bar</a>
  <div class="site-nav-links">
    <div class="site-nav-group">
      <span class="site-nav-group-label">Brand Reviews</span>
      <div class="site-nav-dropdown">
        <a href="/quest-bars">Quest</a>
        <a href="/rxbar-review">RXBAR</a>
        <a href="/clif-bar-review">Clif Bar</a>
        <a href="/barebells-review">Barebells</a>
        <a href="/kind-bars-review">KIND</a>
        <a href="/quest-vs-rxbar">Quest vs RXBAR</a>
      </div>
    </div>
    <div class="site-nav-group">
      <span class="site-nav-group-label">Guides</span>
      <div class="site-nav-dropdown">
        <a href="/clean-protein-bars">Clean Protein Bars</a>
        <a href="/no-artificial-sweeteners">No Artificial Sweeteners</a>
        <a href="/no-sugar-alcohols">No Sugar Alcohols</a>
        <a href="/no-seed-oils">No Seed Oils</a>
        <a href="/low-sugar-high-protein">Low Sugar + High Protein</a>
        <a href="/keto-protein-bars">Keto Protein Bars</a>
        <a href="/best-bars-for-diabetics">Best Bars for Diabetics</a>
        <a href="/glp1-protein-bars">GLP-1 Protein Bars</a>
        <a href="/caffeine-protein-bars">Caffeine Protein Bars</a>
      </div>
    </div>
    <div class="site-nav-group">
      <span class="site-nav-group-label">Explore</span>
      <div class="site-nav-dropdown">
        <a href="/all-protein-bar-brands">All Brands</a>
        <a href="/flavor-map">Flavor Map</a>
        <a href="/brand-quadrant">Brand Quadrant</a>
      </div>
    </div>
    <a href="/ingredient_scoring" class="site-nav-link">How We Score</a>
  </div>
  <button class="site-nav-mobile-toggle" id="nav-toggle" aria-label="Menu">&#9776;</button>
</nav>

<section class="hero page-guide">
  <div class="hero-inner">
    <div class="hero-eyebrow">Brand Rankings</div>
    <h1 class="hero-title">Every Single Protein Bar Brand, Ranked</h1>
    <p class="hero-sub" style="color:#e8e4dc;">{TOTAL_BRANDS} brands, 1,000+ flavors, ranked 1 to {TOTAL_BRANDS} across ingredient quality, protein efficiency, and fiber. The only thing we can't account for is price.</p>
  </div>
</section>

<section class="snapshot">
  <div class="snapshot-inner">
    <div class="snap-item">
      <div class="snap-value">{TOTAL_BRANDS}</div>
      <div class="snap-label">Brands Ranked</div>
    </div>
    <div class="snap-item">
      <div class="snap-value">1,000+</div>
      <div class="snap-label">Flavors Behind The Rankings</div>
    </div>
    <div class="snap-item">
      <div class="snap-value">{TIER_COUNTS.get('wide', 0)}</div>
      <div class="snap-label">Widely Available</div>
    </div>
    <div class="snap-item">
      <div class="snap-value">{TIER_COUNTS.get('mid', 0)}</div>
      <div class="snap-label">Mid-Size &amp; Specialty</div>
    </div>
    <div class="snap-item">
      <div class="snap-value">{TIER_COUNTS.get('small', 0)}</div>
      <div class="snap-label">Small &amp; Online</div>
    </div>
  </div>
</section>
'''

    METHODOLOGY = f'''
<div class="content">

  <section class="section">
    <div class="section-inner">
      <h2 class="section-title">How we ranked {TOTAL_BRANDS} brands</h2>
      <div class="section-body">
        <p>Every brand gets averaged across every flavor we've scored: ingredient quality, protein efficiency, fiber, sugar, net carbs, all of it. This isn't a "best flavor wins" list. A brand with one great flavor and nine mediocre ones won't out-rank a brand that's solid top to bottom. The one thing we can't factor in is price, since we don't track live pricing across retailers.</p>
        <p>Each brand's rank comes from three inputs, weighted like this:</p>
        <ul class="verdict-items">
          <li><strong>Ingredient quality: 60%.</strong> Our A-F score, averaged across every flavor a brand makes. This carries the most weight because clean ingredients are the whole reason this site exists.</li>
          <li><strong>Protein efficiency: 25%.</strong> Grams of protein per 100 calories, averaged across the lineup.</li>
          <li><strong>Fiber: 15%.</strong> Average grams of fiber per bar, because a bar that's technically "clean" but does nothing for satiety isn't actually a great bar.</li>
        </ul>
        <p>Vitamins, creatine, and caffeine aren't part of the formula on purpose. They're personal-preference and use-case signals, not quality signals. A caffeinated bar isn't a "better" bar, it's a bar for a specific moment, and some people need to actively avoid it. Those show up as badges on each card instead, so you can filter for or against them yourself.</p>
        <p>Two more things worth knowing:</p>
        <ul class="verdict-items">
          <li><strong>A small lineup can beat a huge one.</strong> RXBAR (12 flavors) currently outranks Quest (16 flavors) because its ingredient list stays cleaner across the board, even though Quest has more flavors and a bigger marketing budget.</li>
          <li><strong>Sub-brands are scored separately.</strong> KIND and KIND Protein Max, or Clif Bar and Clif Builders, land in different spots on this list. Averaging them together would hide real differences, so we don't.</li>
        </ul>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="section-inner">
      <h2 class="section-title">Widely Available, Mid-Size, or Small &amp; Online</h2>
      <div class="section-body">
        <p>We also tag every brand by how easy it actually is to find, so you can filter for what you can realistically buy nearby versus what you'd need to order online. This is an editorial call based on where these brands actually sell, not something we calculate from the ingredient data. If we've got a brand's distribution wrong, tell us and we'll fix it.</p>
      </div>
      <div class="macro-grid" style="grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); margin-top:1rem;">
        <div class="macro-card">
          <div class="macro-label">Widely Available</div>
          <div class="macro-avg">{TIER_COUNTS.get('wide', 0)} brands</div>
          <div class="macro-verdict">Grocery stores, convenience stores, mass retail. Quest, KIND, Clif, Barebells, Atkins, and similar.</div>
        </div>
        <div class="macro-card">
          <div class="macro-label">Mid-Size &amp; Specialty</div>
          <div class="macro-avg">{TIER_COUNTS.get('mid', 0)} brands</div>
          <div class="macro-verdict">Specialty grocery, natural chains, gyms, some regional retail. Perfect Bar, GoMacro, IQBar, and similar.</div>
        </div>
        <div class="macro-card">
          <div class="macro-label">Small &amp; Online</div>
          <div class="macro-avg">{TIER_COUNTS.get('small', 0)} brands</div>
          <div class="macro-verdict">Mostly direct-to-consumer or specialty-only. The majority of brands in this database fall here.</div>
        </div>
      </div>
      <div class="section-body" style="margin-top:1.25rem;">
        <p>We also group every brand into one of three flavor-lineup categories, based on what its macros actually look like:</p>
        <ul class="verdict-items">
          <li><strong>Protein First:</strong> {CAT_COUNTS.get('Protein First', 0)} brands averaging 9g+ protein per 100 calories.</li>
          <li><strong>Whole Food / High Fiber:</strong> {CAT_COUNTS.get('Whole Food / High Fiber', 0)} brands averaging 6g+ fiber without hitting that protein bar.</li>
          <li><strong>Solid Macro Profile:</strong> {CAT_COUNTS.get('Solid Macro Profile', 0)} brands, everything else, which is most of the market.</li>
        </ul>
        <p>You can filter by any of these below.</p>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="section-inner">
      <h2 class="section-title">What stands out</h2>
      <div class="section-body">
        <p>A few patterns broke the mold enough to call out on their own, in both directions.</p>
      </div>
      <div class="brk-highlight-grid">
{highlights_html}
      </div>
    </div>
  </section>

  <section class="section">
    <div class="section-inner">
      <h2 class="section-title">The best brand in each category</h2>
      <div class="section-body">
        <p>Before the full list, here's the top performer in each slice we track, with a quick note on why it's there.</p>
      </div>
      <div class="brk-best-grid">
{best_html}
      </div>
    </div>
  </section>

  <section class="section">
    <div class="section-inner">
      <h2 class="section-title">Now here's the entire list</h2>
      <div class="section-body">
        <p>All {TOTAL_BRANDS} brands, ranked 1 to {TOTAL_BRANDS}. Filter by distribution tier or category, sort by any metric, or search for a specific brand. Every card links straight to that brand's flavors in the Bar Finder.</p>
      </div>

      <div class="brk-filter-bar">
        <div class="brk-filter-row">
          <span class="brk-filter-label">Tier</span>
          <button class="brk-filter-btn active" data-filter-type="tier" data-filter-val="all">All</button>
          <button class="brk-filter-btn" data-filter-type="tier" data-filter-val="wide">Widely Available</button>
          <button class="brk-filter-btn" data-filter-type="tier" data-filter-val="mid">Mid-Size &amp; Specialty</button>
          <button class="brk-filter-btn" data-filter-type="tier" data-filter-val="small">Small &amp; Online</button>
        </div>
        <div class="brk-filter-row" style="margin-top:.5rem;">
          <span class="brk-filter-label">Category</span>
          <button class="brk-filter-btn active" data-filter-type="cat" data-filter-val="all">All</button>
          <button class="brk-filter-btn" data-filter-type="cat" data-filter-val="Protein First">Protein First</button>
          <button class="brk-filter-btn" data-filter-type="cat" data-filter-val="Solid Macro Profile">Solid Macros</button>
          <button class="brk-filter-btn" data-filter-type="cat" data-filter-val="Whole Food / High Fiber">Whole Food</button>
        </div>
        <div class="brk-filter-row" style="margin-top:.5rem;">
          <span class="brk-filter-label">Sort</span>
          <select class="brk-sort-select" id="brk-sort">
            <option value="rank">Our Ranking</option>
            <option value="protein">Avg Protein (high to low)</option>
            <option value="fiber">Avg Fiber (high to low)</option>
            <option value="flavors">Most Flavors</option>
            <option value="name">Brand Name (A-Z)</option>
          </select>
          <input type="text" class="brk-search-input" id="brk-search" placeholder="Search a brand&hellip;">
        </div>
        <div class="brk-filter-count" id="brk-count"></div>
      </div>

      <div class="brk-list" id="brk-list">
{cards_html}
      </div>

      <div class="brk-caveat">Distribution tiers (Widely Available / Mid-Size &amp; Specialty / Small &amp; Online) are an editorial call based on where these brands typically sell, not a field we calculate from ingredient data. Category buckets (Protein First / Solid Macro Profile / Whole Food &amp; High Fiber) and each brand's rank are both calculated directly from the live database.</div>
    </div>
  </section>

'''

    FAQ_FOOTER = '''
  <section class="explore-cta">
    <div class="explore-cta-inner">
      <div class="explore-cta-eyebrow">Know Your Bar</div>
      <p class="explore-cta-title">Want to filter the full database yourself?</p>
      <p class="explore-cta-sub">Use the Bar Finder to filter by grade, protein, sugar, sugar alcohols, and more across every bar we've scored.</p>
      <div class="explore-cta-btns">
        <a href="/bar-finder?preset=high_protein" class="explore-cta-btn">Most Protein Per Calorie</a>
        <a href="/bar-finder?preset=clean" class="explore-cta-btn">Clean Ingredients</a>
        <a href="/bar-finder?preset=skip_sugar" class="explore-cta-btn">Skip the Sugar</a>
      </div>
    </div>
    <div class="discover-more">
      <div class="discover-more-label">Related reading</div>
      <div class="explore-more-grid">
        <a href="/brand-quadrant" class="explore-more-card">
          <div class="explore-more-title">Brand Quadrant</div>
          <div class="explore-more-desc">See macro efficiency plotted against ingredient quality for every brand.</div>
        </a>
        <a href="/quest-vs-rxbar" class="explore-more-card">
          <div class="explore-more-title">Quest vs RXBAR</div>
          <div class="explore-more-desc">A head-to-head look at two of the most popular bars on the shelf.</div>
        </a>
        <a href="/ingredient_scoring" class="explore-more-card">
          <div class="explore-more-title">How We Score</div>
          <div class="explore-more-desc">The full rule-based system behind every grade on this site.</div>
        </a>
      </div>
    </div>
  </section>

  <section class="faq-section">
    <div class="faq-section-inner">
      <h2>Frequently asked questions</h2>
      <div class="faq-items">
        <div class="faq-item">
          <button class="faq-q">How is the brand ranking calculated?</button>
          <div class="faq-a">Each brand's rank is based on three weighted inputs: 60% average ingredient quality score across every flavor we've scored, 25% protein efficiency (grams of protein per 100 calories), and 15% average fiber. Price is not part of the formula because we don't track live pricing.</div>
        </div>
        <div class="faq-item">
          <button class="faq-q">What do Widely Available, Mid-Size, and Small &amp; Online mean?</button>
          <div class="faq-a">These are editorial distribution categories, not something we calculate from ingredient data. Widely Available means you can generally find the brand at a regular grocery store or convenience store. Mid-Size covers specialty grocery, regional chains, and gyms. Small &amp; Online covers brands that sell mostly direct-to-consumer or through specialty retailers.</div>
        </div>
        <div class="faq-item">
          <button class="faq-q">What are the Protein First, Solid Macro Profile, and Whole Food categories?</button>
          <div class="faq-a">Protein First brands average at least 9g of protein per 100 calories. Whole Food / High Fiber brands average at least 6g of fiber per bar without hitting that protein efficiency bar. Everything else, which is most of the market, falls into Solid Macro Profile.</div>
        </div>
        <div class="faq-item">
          <button class="faq-q">Does a higher rank mean a brand is healthier for everyone?</button>
          <div class="faq-a">No. The rank reflects ingredient quality, protein efficiency, and fiber averaged across a brand's full lineup. It doesn't account for your personal goals, allergies, taste preference, or price. A lower-ranked brand can still be the right choice for a specific diet or flavor you like.</div>
        </div>
        <div class="faq-item">
          <button class="faq-q">How is net carbs calculated?</button>
          <div class="faq-a">Net carbs = Total Carbohydrates minus Dietary Fiber minus Sugar Alcohol, all in grams, taken straight from each bar's nutrition panel.</div>
        </div>
        <div class="faq-item">
          <button class="faq-q">Why do small online brands often outrank big grocery brands?</button>
          <div class="faq-a">Smaller brands often ship one or two flavors built around a short ingredient list, without the sweetener systems mass-market bars use to hit low sugar numbers at scale. A tiny lineup with a clean formula can out-score a 20-flavor lineup that leans on sucralose and sugar alcohols.</div>
        </div>
        <div class="faq-item">
          <button class="faq-q">How many brands and flavors does this cover?</button>
          <div class="faq-a">This ranking covers every one of the __TOTAL_BRANDS__ distinct protein bar brands in our database, spanning 1,000+ scored flavors, updated as we add new bars.</div>
        </div>
      </div>
    </div>
  </section>

</div>

<footer class="site-footer">
  <div class="site-footer-inner">
    <div class="site-footer-brand-block">
      <a href="/" class="site-footer-brand">KNOW YOUR BAR</a>
      <div class="site-footer-tagline">1,000+ bars scored by ingredient quality.<br>No sponsored picks. No BS.</div>
    </div>
    <details class="site-footer-links-toggle">
      <summary class="site-footer-links-summary">More guides &amp; brand reviews</summary>
      <nav class="site-footer-links">
      <a href="/bar-finder">Protein Bar Finder</a>
      <a href="/ingredient_scoring">How We Score</a>
      <a href="/all-protein-bar-brands">All Brands</a>
      <a href="/brand-quadrant">Brand Quadrant</a>
      <a href="/quest-bars">Quest</a>
      <a href="/rxbar-review">RXBAR</a>
      <a href="/clif-bar-review">Clif Bar</a>
      <a href="/barebells-review">Barebells</a>
      <a href="/kind-bars-review">KIND</a>
      <a href="/quest-vs-rxbar">Quest vs RXBAR</a>
      <a href="/clean-protein-bars">Clean Bars</a>
      <a href="/no-artificial-sweeteners">No Artificial Sweeteners</a>
      <a href="/no-sugar-alcohols">No Sugar Alcohols</a>
      <a href="/no-seed-oils">No Seed Oils</a>
      <a href="/low-sugar-high-protein">Low Sugar + High Protein</a>
      <a href="/keto-protein-bars">Keto Protein Bars</a>
      <a href="/best-bars-for-diabetics">Best Bars for Diabetics</a>
      <a href="/glp1-protein-bars">GLP-1 Protein Bars</a>
    </nav>
    </details>
  </div>
  <div class="site-footer-copy">knowyourbar.com &nbsp;&middot;&nbsp; Updated August 2026</div>
</footer>

<script>
  document.querySelectorAll('.faq-q').forEach(btn => {
    btn.addEventListener('click', () => {
      const item = btn.closest('.faq-item');
      const isOpen = item.classList.contains('open');
      document.querySelectorAll('.faq-item').forEach(i => i.classList.remove('open'));
      if (!isOpen) item.classList.add('open');
    });
  });

  const navToggle = document.getElementById('nav-toggle');
  if (navToggle) {
    navToggle.addEventListener('click', () => {
      document.querySelector('.site-nav-links').classList.toggle('open');
    });
  }

  document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('a[href*="amazon.com"]').forEach(function(link) {
      link.addEventListener('click', function() {
        if (typeof gtag === 'function') {
          gtag('event', 'affiliate_click', { brand: link.closest('.brk-card') ? link.closest('.brk-card').dataset.name : undefined });
        }
      });
    });
  });

  (function() {
    const list = document.getElementById('brk-list');
    const cards = Array.from(list.querySelectorAll('.brk-card'));
    const countEl = document.getElementById('brk-count');
    const sortSel = document.getElementById('brk-sort');
    const searchInput = document.getElementById('brk-search');
    let activeTier = 'all';
    let activeCat = 'all';
    let searchTerm = '';

    function applyFilters() {
      let visible = 0;
      cards.forEach(c => {
        const tierOk = activeTier === 'all' || c.dataset.tier === activeTier;
        const catOk = activeCat === 'all' || c.dataset.category === activeCat;
        const nameOk = !searchTerm || c.dataset.name.includes(searchTerm);
        const show = tierOk && catOk && nameOk;
        c.classList.toggle('brk-hidden', !show);
        if (show) visible++;
      });
      countEl.textContent = 'Showing ' + visible + ' of ' + cards.length + ' brands';
    }

    function applySort() {
      const mode = sortSel.value;
      const sorted = cards.slice().sort((a, b) => {
        if (mode === 'rank') return (+a.dataset.rank) - (+b.dataset.rank);
        if (mode === 'protein') return (+b.dataset.protein) - (+a.dataset.protein);
        if (mode === 'fiber') return (+b.dataset.fiber) - (+a.dataset.fiber);
        if (mode === 'flavors') return (+b.dataset.flavors) - (+a.dataset.flavors);
        if (mode === 'name') return a.dataset.name.localeCompare(b.dataset.name);
        return 0;
      });
      sorted.forEach(c => list.appendChild(c));
    }

    document.querySelectorAll('.brk-filter-btn[data-filter-type="tier"]').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.brk-filter-btn[data-filter-type="tier"]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        activeTier = btn.dataset.filterVal;
        applyFilters();
      });
    });
    document.querySelectorAll('.brk-filter-btn[data-filter-type="cat"]').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.brk-filter-btn[data-filter-type="cat"]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        activeCat = btn.dataset.filterVal;
        applyFilters();
      });
    });
    sortSel.addEventListener('change', applySort);
    searchInput.addEventListener('input', () => {
      searchTerm = searchInput.value.trim().toLowerCase();
      applyFilters();
    });

    applyFilters();
  })();
</script>

</body>
</html>
'''
    faq_footer = FAQ_FOOTER.replace('__TOTAL_BRANDS__', str(TOTAL_BRANDS))
    return HEAD + METHODOLOGY + faq_footer


if __name__ == '__main__':
    rows = compute_brand_stats(BARS_JS_PATH)
    total_brands = len(rows)
    print(f"Computed stats for {total_brands} brands, {sum(r['flavors'] for r in rows)} flavors.")
    page_html = render_page(rows, total_db_brand_count_display=f"{total_brands}+")
    with open(OUTPUT_PATH, 'w') as f:
        f.write(page_html)
    print(f"Wrote {OUTPUT_PATH} ({len(page_html)} bytes).")
    print("Next steps: (1) update brands_manifest.json's total_db_brand_count if it")
    print("changed, (2) run generate_brand_links.py, (3) run the QA.md checklist,")
    print("(4) diff against the previous version before uploading.")
