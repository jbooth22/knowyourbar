"""Rebuild the methodology page (ingredient_scoring.html).

Opens the LIVE page and rewrites only the <!-- kyb:NAME --> regions:
  meta-desc    meta description
  faq-jsonld   FAQPage JSON-LD (built from the same list as the visible FAQ)
  calc         how the score is calculated: position weights, the three
               exceptions (flat artificial sweetener penalty, sub-ingredients,
               stacked proteins) and the ingredient-count adjustment
  bands        grade bands table and the share of bars in each band
  sweeteners   the v12 sugar / fiber / sweetener scale
  examples     example ingredients with their scores
  faq          visible FAQ
The live grade cards (filled from bars.js by the page's own JS), nav,
footer and every other section are kept as-is.

Every number on the page comes from one of three sources, so the page can't
drift from the scoring:
  score_and_export.py            weights, bands, count adjustment, penalties
  knowyourbar_scoring_schema_v12.xlsx   each ingredient's base score
  bars.js                        bar counts and grade shares
The build stops if an example ingredient's schema score falls outside the
tier or value the copy states.

Run: python3 build_ingredient_scoring.py
"""
import json, re
import pandas as pd
import score_and_export as sx
from kyb_guide_lib import load_bars, esc, comma, replace_region, stamp_dates, today_iso

PAGE = 'ingredient_scoring.html'
SCHEMA = 'knowyourbar_scoring_schema_v12.xlsx'


def signed(v):
    v = int(v) if float(v).is_integer() else v
    return f'+{v}' if v > 0 else ('0' if v == 0 else f'&minus;{abs(v)}')


def signed_txt(v):
    v = int(v) if float(v).is_integer() else v
    return f'+{v}' if v > 0 else str(v)


class Schema:
    def __init__(self, path):
        c = pd.read_excel(path, 'Canonical_Ingredients')
        self.n = len(c)
        self.score = {}
        for name, s in zip(c.canonical_name.str.lower().str.strip(), c.base_score):
            self.score.setdefault(name, float(s))
        self.min = float(c.base_score.min())
        self.max = float(c.base_score.max())
        self.lowest = sorted(n for n, s in self.score.items() if s == self.min)

    def __call__(self, name):
        if name not in self.score:
            raise SystemExit(f'ERROR: {name!r} is not in {SCHEMA}. Fix the example list. Not writing.')
        return self.score[name]


# Sugar / carb / fiber / sweetener tiers (SCORING_V12_SPEC Part A and B).
# (tier, why, allowed scores, [(label shown, schema name), ...])
TIERS = [
    ('Whole fruit and dates', 'Whole food with its fiber intact.', {2, 3},
     [('dates', 'dates'), ('date paste', 'date paste'), ('strawberries', 'strawberries'),
      ('blueberries', 'blueberries'), ('apple', 'apple')]),
    ('Lightly processed sweeteners', 'Real foods, but still added sugar.', {-1},
     [('honey', 'honey'), ('maple syrup', 'maple syrup'), ('coconut sugar', 'coconut sugar'),
      ('date syrup', 'date syrup')]),
    ('Refined sugars', 'Refined or concentrated down to mostly sugar.', {-2},
     [('cane sugar', 'cane sugar'), ('brown sugar', 'brown sugar'), ('agave', 'agave'), ('fructose', 'fructose'),
      ('molasses', 'molasses'), ('grape sugar', 'grape sugar'), ('fruit juice concentrates', 'fruit juice concentrate')]),
    ('Starch-converted sugars', 'Starch broken down into sugar. The most processed caloric sweeteners.', {-3},
     [('brown rice syrup', 'brown rice syrup'), ('tapioca syrup', 'tapioca syrup'), ('corn syrup', 'corn syrup'),
      ('glucose syrup', 'glucose syrup'), ('dextrose', 'dextrose'), ('maltodextrin', 'maltodextrin'),
      ('barley malt extract', 'barley malt extract'), ('fiber syrups', 'fiber syrup')]),
    ('Engineered fibers', 'Starches rearranged so the body can\'t fully digest them, so the label can count '
     'them as fiber and lower "net carbs." Not harmful, but highly processed.', {-1},
     [('soluble corn fiber', 'soluble corn fiber'), ('resistant dextrin', 'resistant dextrin'),
      ('tapioca fiber', 'tapioca fiber'), ('IMO (isomalto-oligosaccharides)', 'isomalto-oligosaccharides'),
      ('polydextrose', 'polydextrose')]),
    ('Plant-extracted fibers', 'Fiber pulled from a plant with little change to what it is.', {1},
     [('chicory root fiber', 'chicory root fiber'), ('inulin', 'inulin'), ('oligofructose', 'oligofructose'),
      ('acacia fiber', 'acacia fiber')]),
    ('Whole-food fibers', 'Fiber milled from a food.', {1},
     [('oat fiber', 'oat fiber'), ('pea fiber', 'pea fiber'), ('citrus fiber', 'citrus fiber'), ('beet fiber', 'beet fiber')]),
    ('Sugar alcohols', 'Bulk sweeteners used by the gram, so label position still reflects how much is in the bar.',
     {-3, -4}, [('erythritol', 'erythritol'), ('xylitol', 'xylitol'), ('sorbitol', 'sorbitol'),
                ('isomalt', 'isomalt'), ('maltitol', 'maltitol')]),
    ('Low-calorie plant sweeteners', 'Unchanged in v12.', {0, 1},
     [('stevia', 'stevia'), ('monk fruit', 'monk fruit'), ('allulose', 'allulose')]),
]
AS_NAMES = {'sucralose': 'sucralose', 'acesulfame': 'acesulfame potassium',
            'aspartame': 'aspartame', 'saccharin': 'saccharin'}

# Example chips: (label, [schema names that must all share the score], css, description)
EXAMPLES = [
    ('High-scoring ingredients', [
        ('Whey Protein Isolate', ['whey protein isolate'], 'positive',
         "The gold standard protein for bars. Isolate is highly filtered, so it's dense in protein with minimal fat and carbs. A complete amino acid profile makes it excellent for muscle protein synthesis."),
        ('Egg Whites', ['egg whites'], 'positive',
         "A whole-food complete protein source with an exceptional amino acid profile. When it leads the ingredient list, you're getting real food as the primary ingredient - not a powder or isolate."),
        ('Almonds / Peanuts', ['almonds', 'peanuts'], 'positive',
         "Whole food ingredients that bring fiber, healthy fats, and natural protein. When nuts appear early in the list, it's a good sign the bar is built around real food rather than processed filler."),
        ('Oats', ['oats'], 'positive',
         'A minimally processed whole grain that adds complex carbs, fiber, and a clean energy source. Common in bars that lean toward real food formulations over engineered ingredient lists.'),
    ]),
    ('Neutral ingredients', [
        ('Salt', ['salt'], 'neutral',
         "Present in almost every bar. At typical quantities it's neither a benefit nor a concern - it scores neutral. Position matters though: if salt somehow led the ingredient list, that would be a different story."),
        ('Soy / Sunflower Lecithin', ['soy lecithin', 'sunflower lecithin'], 'neutral',
         'An emulsifier used to improve texture and shelf stability. Not harmful at the trace quantities found in bars, but not contributing nutritional value either. Scores neutral.'),
        ('Tapioca Starch', ['tapioca starch'], 'neutral',
         'A starch used for texture and binding. Common in "cleaner" bars as a more neutral binder compared to some alternatives. It\'s not a nutritional contributor, but it\'s not a red flag either.'),
    ]),
    ('Low-scoring ingredients', [
        ('Sugar / Cane Sugar', ['sugar', 'cane sugar'], 'concern',
         'Added caloric sweetener with no nutritional upside. Present in a huge share of bars. The position matters: sugar in spot #7 is a minor concern, sugar in spot #2 is a significant drag on the score.'),
        ('Soluble Corn Fiber', ['soluble corn fiber'], 'concern',
         'An engineered fiber made from corn starch. It lets a label count carbs as fiber and lower "net carbs," but it is a highly processed stand-in for fiber from food. It scores -1: below neutral, level with honey and maple syrup, and above refined sugars.'),
        ('Sucralose', ['sucralose'], 'concern', None),
        ('Palm Kernel Oil', ['palm kernel oil'], 'concern',
         'A highly processed industrial fat used for texture and shelf life. High in saturated fat and a poor-quality substitute for whole food fat sources like cocoa butter, nuts, or seeds.'),
        ('Maltitol', ['maltitol'], 'concern', None),
    ]),
]


def position_rows():
    w = {p: sx.position_weight(p) for p in range(1, 16)}
    left = [(f'{p}{"st" if p == 1 else "nd" if p == 2 else "rd" if p == 3 else "th"}', f'{w[p]:.2f}') for p in range(1, 9)]
    right = [(f'{p}th', f'{w[p]:.2f}') for p in range(9, 15)] + [('15th+', f'{w[15]:.2f} and below'), ('', '')]
    return '\n'.join(f'          <tr><td>{a}</td><td>{b}</td><td>{c}</td><td>{d}</td></tr>' for (a, b), (c, d) in zip(left, right))


def count_rows():
    why = {0.05: 'Short, clean list bonus', 0.0: 'Neutral', -0.05: 'Slightly complex',
           -0.10: 'Complex formulation', -0.15: 'Highly processed penalty'}
    out = []
    for lo, hi, adj in sx.COUNT_BANDS:
        rng = f'{hi} or fewer' if lo == 0 else (f'{lo} or more' if hi >= 999 else f'{lo} &ndash; {hi}')
        a = f'+{adj:.2f}' if adj > 0 else ('0.00' if adj == 0 else f'&ndash;{abs(adj):.2f}')
        out.append(f'          <tr><td>{rng}</td><td>{a}</td><td>{why[round(adj, 2)]}</td></tr>')
    return '\n'.join(out)


def sub_mult():
    parsed = sx.parse_ingredients('a, b (c)')
    return [m for t, p, m in parsed if t == 'c'][0]


def main():
    sch = Schema(SCHEMA)
    bars = load_bars()
    N = len(bars)
    grades = {g: sum(1 for b in bars if b.get('score_band') == g) for g in 'ABCDF'}
    pct = {g: round(100 * n / N) for g, n in grades.items()}
    AS = sx.ARTIFICIAL_SW
    pen = sx.ARTIFICIAL_SW_PENALTY
    n_as = sum(1 for b in bars if any(k in (b.get('Ingredients') or '').lower() for k in AS))
    sm = sub_mult()
    stack = sx.PROTEIN_STACK_DISCOUNT
    canon = f'{sch.n // 100 * 100:,}+'
    assert sch.min == -4 and sch.max == 4, 'base score range changed: update the copy'
    as_list = 'sucralose, acesulfame potassium, aspartame and saccharin'
    assert set(AS) == set(AS_NAMES), 'artificial sweetener list changed: update the copy'
    for kw, nm in AS_NAMES.items():
        if nm in sch.score and sch(nm) != pen:
            raise SystemExit(f'ERROR: {nm} base score {sch(nm)} differs from the flat penalty {pen}. Not writing.')

    # ---- calc
    calc = f'''      <p>Each bar's ingredient list is parsed into individual ingredients. Every ingredient is mapped to a canonical name and assigned a base score from <strong>&minus;4</strong> (harmful) to <strong>+4</strong> (excellent). The base score is then weighted by ingredient position - ingredients listed first are present in greater quantities, so they contribute more to the final score.</p>
      <p>A final adjustment is applied based on the total number of ingredients. Bars with short, focused lists receive a small bonus. Bars with highly complex formulations receive a small penalty.</p>

      <div class="callout">
        <p><strong>Final Score</strong> = Sum of (base_score &times; position_weight) for each ingredient + {signed(int(pen))} for each artificial sweetener + ingredient count adjustment</p>
      </div>

      <h3>Position weights</h3>
      <p>The first ingredient carries full weight (1.0). Each subsequent ingredient carries progressively less weight, reflecting the fact that ingredients are listed in descending order by quantity.</p>

      <table class="score-table">
        <colgroup>
          <col style="width:25%"><col style="width:25%"><col style="width:25%"><col style="width:25%">
        </colgroup>
        <thead>
          <tr><th>Position</th><th>Weight</th><th>Position</th><th>Weight</th></tr>
        </thead>
        <tbody>
{position_rows()}
        </tbody>
      </table>

      <h3>Three exceptions to position weighting</h3>
      <p><strong>Artificial sweeteners count a flat {signed(int(pen))} each.</strong> Sucralose, acesulfame potassium, aspartame and saccharin each cost a bar {abs(int(pen))} points, wherever they appear on the label. Position weighting assumes that more of an ingredient means more impact. That holds for bulk ingredients, but these sweeteners are hundreds of times sweeter than sugar and are used in milligrams, so they almost always sit near the end of the label, where position weighting made them count for almost nothing. Each sweetener is counted once, even when two are listed together in one phrase.</p>
      <p><strong>Sub-ingredients count at {round(sm * 100)}%.</strong> Ingredients inside parentheses or brackets, like the sugar in "chocolate (sugar, cocoa butter)", share their parent's position but carry {sm:g} of its weight, because each is only part of that ingredient.</p>
      <p><strong>Extra protein sources count at {round(stack * 100)}%.</strong> When a bar lists several protein sources, the best-scoring one counts in full and each additional one counts at {'half' if stack == 0.5 else f'{round(stack * 100)}%'} weight, so a long list of proteins can't inflate the score.</p>

      <h3>Ingredient count adjustment</h3>
      <table class="score-table">
        <thead>
          <tr><th>Ingredient count</th><th>Adjustment</th><th>Rationale</th></tr>
        </thead>
        <tbody>
{count_rows()}
        </tbody>
      </table>'''

    # ---- bands
    B = {band: lo for lo, hi, band, lab in sx.SCORE_BANDS}
    assert (B['A'], B['B'], B['C'], B['D']) == (8, 4, 0, -3), 'grade bands changed: update the copy'
    desc = {
        'A': 'Predominantly whole foods, quality proteins, minimal additives. The best ingredient profiles in the database.',
        'B': 'Solid ingredients with minor concerns. A well-formulated bar that makes reasonable trade-offs.',
        'C': 'Mixed profile. Some good ingredients, some processed. Acceptable but not exceptional.',
        'D': 'Mostly processed ingredients with limited redeeming qualities. Heavy use of sweeteners or additives.',
        'F': 'Heavy artificial sweeteners, low-quality processed oils, or minimal real nutrition. We include these bars so you can make informed decisions.',
    }
    rng = {'A': '&ge; 8.0', 'B': '4.0 &ndash; 7.9', 'C': '0.0 &ndash; 3.9', 'D': '&ndash;3.0 to &ndash;0.1', 'F': 'Below &ndash;3.0'}
    lab = {'A': 'Clean', 'B': 'Good', 'C': 'Okay', 'D': 'Poor', 'F': 'Avoid'}
    col = {'A': '#2a7a1f', 'B': '#5a8a2f', 'C': '#b89a00', 'D': '#c87020', 'F': '#c83020'}
    band_rows = '\n'.join(f'''          <tr>
            <td><div class="band-pill"><span class="band-dot" style="background:{col[g]}">{g}</span></div></td>
            <td>{lab[g]}</td>
            <td>{rng[g]}</td>
            <td>{desc[g]}</td>
          </tr>''' for g in 'ABCDF')
    bands = f'''      <p>The numeric score is converted into a letter grade. The thresholds are fixed and apply to every bar the same way. Across our {comma(N)} bars, {pct['A']}% score A, {pct['B']}% B, {pct['C']}% C, {pct['D']}% D and {pct['F']}% F.</p>

      <table class="score-table">
        <colgroup>
          <col style="width:60px">
          <col style="width:80px">
          <col style="width:120px">
          <col>
        </colgroup>
        <thead>
          <tr><th>Grade</th><th>Label</th><th>Score range</th><th>What it means</th></tr>
        </thead>
        <tbody>
{band_rows}
        </tbody>
      </table>'''

    # ---- sweeteners
    rows = []
    for tier, why, allowed, ex in TIERS:
        sc = [sch(n) for _, n in ex]
        bad = [(l, s) for (l, _), s in zip(ex, sc) if s not in allowed]
        if bad:
            raise SystemExit(f'ERROR: {tier}: schema scores {bad} fall outside {sorted(allowed)}. Update the copy. Not writing.')
        lo, hi = min(sc), max(sc)
        if lo == hi:
            score_cell, names = signed(lo), ', '.join(l for l, _ in ex)
        else:
            score_cell = f'{signed(lo)} to {signed(hi)}' if lo >= 0 else f'{signed(hi)} to {signed(lo)}'
            names = ', '.join(f'{l} ({signed(s)})' for (l, _), s in zip(ex, sc))
        rows.append((tier, why, score_cell, names))
    rows.insert(8, ('Artificial sweeteners', 'A flat penalty per sweetener, wherever it appears on the label (see above).',
                    f'{signed(int(pen))} each', as_list.replace(' and ', ', ')))
    tier_rows = '\n'.join(f'''          <tr>
            <td><strong>{esc(t)}</strong><br><span style="color:var(--bs-text-dim);font-size:.85em;">{esc(w)}</span></td>
            <td style="white-space:nowrap;">{s}</td>
            <td>{n}</td>
          </tr>''' for t, w, s, n in rows)
    sweeteners = f'''    <!-- Sugars, fibers and sweeteners -->
    <section class="content-section" id="sugars-fibers-sweeteners">
      <h2>How we score sugars, fibers and sweeteners</h2>
      <p>The rule: <strong>the more a sugar or carbohydrate has been processed away from a whole food, the lower it scores.</strong> Sugar is still sugar to your body, so no added caloric sweetener scores above &minus;1. Fibers follow the same logic: fiber from a food or plant scores +1, while starches engineered to count as fiber score &minus;1.</p>

      <table class="score-table">
        <colgroup>
          <col style="width:38%"><col style="width:17%"><col>
        </colgroup>
        <thead>
          <tr><th>Type</th><th>Score</th><th>Examples</th></tr>
        </thead>
        <tbody>
{tier_rows}
        </tbody>
      </table>

      <p>{comma(n_as)} of our {comma(N)} bars ({round(100 * n_as / N)}%) contain at least one artificial sweetener. Use the <a href="/no-artificial-sweeteners">No Artificial Sweeteners guide</a> to see the ones that don't.</p>

      <div class="callout">
        <p><strong>What changed in September 2026 (scoring v12):</strong> sugars now follow the processing scale above (honey and maple syrup went from &minus;2 to &minus;1; dextrose and maltodextrin dropped to &minus;3), soluble corn fiber, resistant dextrin, tapioca fiber and IMO went from 0 or +1 to &minus;1, and artificial sweeteners became a flat &minus;2 each instead of being discounted by label position. The grade bands did not change.</p>
      </div>
    </section>
'''

    # ---- examples
    blocks = []
    for head, items in EXAMPLES:
        chips = []
        for label, names, css, d in items:
            sc = {sch(n) for n in names}
            if len(sc) != 1:
                raise SystemExit(f'ERROR: example {label!r} groups ingredients with different scores {sc}. Not writing.')
            s = sc.pop()
            shown = signed(s).replace('&minus;', '&ndash;')
            if label == 'Sucralose':
                shown = f'{shown} flat'
                d = (f'A zero-calorie artificial sweetener, roughly 600 times sweeter than sugar. Research on its effects on the gut '
                     f'microbiome and metabolic response is still developing. It costs a bar a flat {abs(int(pen))} points wherever it '
                     f'appears on the label, the same as acesulfame potassium, aspartame and saccharin.')
            if label == 'Maltitol':
                others = [n for n in sch.lowest if 'maltitol' not in n]
                assert s == sch.min and 'hydrogenated palm kernel oil' in others
                d = ('Tied with hydrogenated palm kernel oil for the lowest score in our database. A sugar alcohol with a glycemic '
                     'index closer to real sugar than to erythritol, often causing digestive distress, and frequently used in large '
                     'quantities to hit "no sugar added" claims. If you see maltitol leading the list, that\'s an F-grade bar.')
            chips.append(f'''        <div class="chip-row">
          <span class="chip-sample chip-{css}" style="min-width:180px;">{esc(label)} &nbsp;<strong>{shown}</strong></span>
          <div>
            <div class="chip-desc">{esc(d)}</div>
          </div>
        </div>''')
        blocks.append(f'      <h3>{head}</h3>\n      <div class="chips-grid">\n' + '\n'.join(chips) + '\n      </div>')
    examples = "      <p>Here's how the scoring plays out with real ingredients you'll recognize on labels.</p>\n\n" + '\n\n'.join(blocks)

    # ---- FAQ (plain text; visible and JSON-LD built from the same list)
    faqs = [
        ('How does the Know Your Bar ingredient scoring system work?',
         f'Each bar\'s ingredient list is parsed into individual ingredients. Every ingredient is mapped to our database of {canon} '
         f'canonical ingredients, each assigned a quality score from +4 (excellent) to -4 (harmful). Scores are then weighted by '
         f'ingredient position: earlier ingredients are present in larger quantities and contribute more to the final score. '
         f'Artificial sweeteners are the exception: each one costs a flat {abs(int(pen))} points wherever it appears. The total, plus a '
         f'small adjustment for ingredient count, becomes the bar\'s ingredient quality score.'),
        ('What do the letter grades mean?',
         'Grades run A through F: A (Clean) means a score of 8 or higher, B (Good) is 4 to 7.9, C (Okay) is 0 to 3.9, D (Poor) is '
         '-3 to -0.1, and F (Avoid) is below -3. The grades reflect the overall ingredient quality of the bar based on what is in it '
         'and in what quantities.'),
        ('How do you score artificial sweeteners like sucralose?',
         f'Each artificial sweetener ({as_list}) costs a bar a flat {abs(int(pen))} points, no matter where it sits on the label. '
         f'These sweeteners are used in milligrams, so they almost always appear near the end of the list, where position weighting '
         f'would make them count for almost nothing. {comma(n_as)} of our {comma(N)} bars contain at least one.'),
        ('Why do some added fibers score below zero?',
         'Soluble corn fiber, resistant dextrin, tapioca fiber, IMO and polydextrose are starches that were rearranged so the body '
         'can\'t fully digest them. That lets the label count them as fiber and lower "net carbs." They aren\'t harmful, but they are '
         'highly processed stand-ins for fiber from food, so they score -1: below neutral, level with honey and maple syrup, and above refined sugars like cane sugar. Fiber from '
         'foods and plants, like oat fiber, chicory root fiber and inulin, scores +1.'),
        ('Why does honey score higher than brown rice syrup?',
         'The more a sugar has been processed away from a whole food, the lower it scores. Honey, maple syrup and coconut sugar are '
         'lightly processed, single-source foods and score -1. Refined sugars like cane sugar and agave score -2. Syrups made by '
         'breaking down starch into sugar, like brown rice syrup, tapioca syrup, dextrose and maltodextrin, score -3. Whole fruit '
         'and dates score +2 to +3 because the fiber is still there.'),
        ('Are you nutritionists or dieticians?',
         'No. We are not nutritionists, registered dieticians, or medical professionals. We are people who eat a lot of protein bars, '
         'got frustrated by vague health claims, and built a data-driven scoring system to make sense of ingredient lists. The system '
         'is our best effort at an objective framework, not medical advice.'),
        ('How often is the scoring system updated?',
         f'We update the scoring schema as we add new bars and refine how specific ingredients are scored. The current schema covers '
         f'{canon} canonical ingredients, and every bar is rescored whenever it changes. The most recent change, in September 2026, '
         f'updated how we score sugars, fibers and artificial sweeteners. If you think an ingredient is scored incorrectly, we want '
         f'to hear about it.'),
        ('Does ingredient quality score reflect taste or nutrition facts?',
         'No. The ingredient quality score reflects only the quality of the ingredients themselves, not macros, taste, or overall '
         'nutritional value. A bar could score high on ingredient quality but be high in calories. We recommend looking at both the '
         'ingredient grade and the macro profile when choosing a bar.'),
    ]
    faq_vis = ''.join(f'<div class="faq-item"><div class="faq-q">{esc(q)}</div><div class="faq-a"><p>{esc(a)}</p></div></div>'
                      for q, a in faqs)
    ld = {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
        {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in faqs]}
    faq_ld = '<script type="application/ld+json">\n' + json.dumps(ld, ensure_ascii=False, separators=(',', ':')) + '\n</script>'

    meta = (f'  <meta name="description" content="How we grade {comma(N)} protein bars A-F on ingredient quality: base scores, '
            f'position weights, and how we score sugars, fibers and artificial sweeteners.">')

    page = open(PAGE, encoding='utf-8').read()
    for name, content in [('meta-desc', meta), ('faq-jsonld', faq_ld), ('calc', calc), ('bands', bands),
                          ('sweeteners', sweeteners), ('examples', examples), ('faq', '  ' + faq_vis)]:
        page = replace_region(page, name, content)
    page = stamp_dates(page, today_iso())
    visible = re.sub(r'<style.*?</style>', '', page, flags=re.S)  # CSS comments on the live page use em dashes
    for bad in ('\u2014', 'href="Yes"', 'href="None"'):
        if bad in visible:
            raise SystemExit(f'ERROR: forbidden string {bad!r} in page. Not writing.')
    open(PAGE, 'w', encoding='utf-8').write(page)
    print(f'{PAGE}: {N} bars (A {pct["A"]}%, B {pct["B"]}%, C {pct["C"]}%, D {pct["D"]}%, F {pct["F"]}%); '
          f'{n_as} with artificial sweeteners; schema {sch.n} ingredients; {len(faqs)} FAQs')


if __name__ == '__main__':
    main()
