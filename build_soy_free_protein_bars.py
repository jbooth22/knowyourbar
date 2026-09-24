#!/usr/bin/env python3
"""Rebuild soy-free-protein-bars.html from bars.js.

Run from the repo root:  python3 build_soy_free_protein_bars.py

Replaces the older full-page generator. Region-marker build via
kyb_cert_guide.CertGuide (live nav/footer/CSS/JS kept; regions from bars.js).

Screen: GUIDE_FILTERS['soy-free-protein-bars'] = `Soy Free (Y/N)` is Yes.
The three named soy sources use the GUIDE_CRITERIA.md patterns. Per that doc,
soy protein and soy lecithin are NOT concern ingredients in our scoring, so the
grade gap is described as correlation (artificial sweeteners / processed oils).
"""
from kyb_cert_guide import *

def disq_intro(g):
    h = {l: len(g.HIT[l]) for l in g.SRC}
    return f'''        <p>We check the Soy Free (Y/N) label on file for every bar, then cross-check ingredient lists ourselves for soy protein, soy lecithin, and soybean oil, the three named soy sources that show up most in the data. {comma(g.N)} of {comma(g.NT)} bars, about {pct0(g.N, g.NT)}%, carry a soy free label. The other {comma(g.ND)}, about {pct0(g.ND, g.NT)}%, don't.</p>
        <p>Soy lecithin is the most common named source at {comma(h['Soy Lecithin'])} bars ({g1(100 * h['Soy Lecithin'] / g.NT)}% of the full database), added as an emulsifier rather than a protein source, which is why it shows up even in bars that don't lean on soy for protein. Soy protein (isolate, concentrate, or flour) appears in {comma(h['Soy Protein'])} bars ({g1(100 * h['Soy Protein'] / g.NT)}%), and soybean oil in {comma(h['Soybean Oil'])} bars ({g1(100 * h['Soybean Oil'] / g.NT)}%). The remaining {comma(len(g.UNLAB))} bars, {g1(100 * len(g.UNLAB) / g.NT)}% of the full database, show no soy protein, soy lecithin, or soybean oil in their own ingredient list at all. They just aren't labeled soy free, which is a different claim from actually containing soy.</p>'''

def rates(g):
    def r(bars, tag): return pct(sum(1 for b in bars if has_tag(b, tag)), len(bars))
    return r(g.Q, 'Artificial Sweeteners'), r(g.ALL, 'Artificial Sweeteners'), r(g.Q, 'Processed Oils'), r(g.ALL, 'Processed Oils')

def lead_insights(g):
    asq, asa, poq, poa = rates(g)
    g.C.check(g.ORDER[0] == 'Soy Lecithin', 'soy lecithin is the most common named soy source')
    g.C.check(asq < asa and poq < poa, 'soy free bars carry artificial sweeteners and processed oils less often')
    lec = len(g.HIT['Soy Lecithin'])
    other = len(g.HIT['Soy Protein']) + len(g.HIT['Soybean Oil'])
    name, hits, total, _ = g.example
    return [
        ('Soy lecithin is the clearest single soy source, not soy protein.',
         f'{comma(lec)} bars ({g1(100 * lec / g.NT)}% of the database) name soy lecithin directly, '
         + ('more than the soy protein and soybean oil counts combined.' if lec > other else 'more than soy protein or soybean oil on its own.')
         + " It's an emulsifier, not a protein play, so it shows up even in bars that aren't trying to add soy."),
        (f'{name} shows the soy-protein pattern clearly.',
         f"{hits} of {name}'s {total} flavors use soy protein directly. None of {name}'s flavors are labeled soy free."),
        ("Soy free bars grade higher, but not because of the soy itself.",
         "Soy protein isolate scores well in our system and soy lecithin is neutral, so cutting soy doesn't directly raise a bar's "
         f"grade. What correlates is cleaner sweeteners and fats: soy free bars carry artificial sweeteners {asq}% of the time "
         f"versus {asa}% database-wide, and processed oils {poq}% versus {poa}%."),
    ]

def quality_tail(g):
    asq, asa, poq, poa = rates(g)
    return ("That's not because soy itself is penalized: soy protein isolate actually scores well in our system and soy lecithin is "
            f"neutral. It's correlation: brands that skip soy also tend to skip artificial sweeteners ({asq}% of soy free bars vs. "
            f"{asa}% database-wide) and processed oils ({poq}% vs. {poa}%). What soy free bars give up on average is protein: they "
            f"average {fnum(round(g.stats['pq'], 1))}g against a database-wide average of {fnum(round(g.stats['pa'], 1))}g.")

CFG = dict(
    slug='soy-free-protein-bars', page='soy-free-protein-bars.html', url='https://knowyourbar.com/soy-free-protein-bars',
    published='2026-09-17', flag='Soy Free (Y/N)', word='soy free', Word='Soy Free', table_id='sf',
    sources=[
        dict(label='Soy Protein', rx=r'soy protein|textured soy|soy flour|isolated soy protein|proteins?\s*\(soy\b|\(soy,',
             desc='Soy protein isolate, concentrate, or flour, usually added as a cheap way to boost the protein count, sometimes as part of a multi-source "plant protein" blend.'),
        dict(label='Soy Lecithin', rx=r'soy lecithin|lecithins?\s*\(soy\)',
             desc='An emulsifier that keeps the bar from separating, usually appearing low in the ingredient list. Imported and European-formatted bars often reverse the label to "lecithin (soy)".'),
        dict(label='Soybean Oil', rx=r'soybean oil|soy oil',
             desc='Used as a coating fat or moisture binder, most often in chocolate or peanut-butter-style coatings. The least common of the three named soy sources.'),
    ],
    sources_or='soy protein, soy lecithin, or soybean oil',
    unlabeled_label='Not labeled soy free',
    unlabeled_desc="No soy protein, soy lecithin, or soybean oil shows up anywhere in the ingredient list we can find, but the brand hasn't labeled or certified the bar soy free either. That is a labeling gap, not proof the bar contains soy.",
    disq_intro=disq_intro,
    hero_extra='Most of the rest carry soy lecithin as an emulsifier or soy protein to boost the protein count.',
    og_desc='{n} soy free protein bars with no soy protein, soy lecithin, or soybean oil in the recipe. Ranked by ingredient quality score.',
    big_stat=lambda g: (f'{g.ab(g.Q)}%', 'of soy free protein bars grade A or B for ingredient quality',
                        f'Soy free bars grade A or B {g.ab(g.Q)}% of the time, against {g.ab(g.ALL)}% database-wide. That is correlation, '
                        'not a soy penalty: see the sweetener and oil numbers below.'),
    lead_insights=lead_insights,
    skip_generic={'grade'},
    full_lineup_tail='these brands build around a protein and emulsifier system that never touches soy in any form, rather than swapping it out flavor by flavor.',
    example_brand='CLIF Bar', example_source='Soy Protein', example_verb='use',
    brands_intro='Some brands build their whole lineup without soy protein, soy lecithin, or soybean oil, others lean on it across the board. Grade columns below show ingredient quality only, not an overall bar rating. Click any brand name to jump to its flavors in the table below.',
    avoid_note='These brands lean on soy protein, soy lecithin, soybean oil, or an unlabeled formula across most or all of their lineup.',
    avoid_head='Flavors Without Soy Free Label', avoid_last_head='Soy Source Found',
    what_makes=lambda g: (f'We use the Soy Free (Y/N) label on file for each bar. {comma(g.N)} of the {comma(g.NT)} bars we track '
                          'carry that label. We also cross-check ingredient lists ourselves for soy protein, soy lecithin, and soybean '
                          'oil, the three named soy sources that show up most in the data.'),
    most_common_q='What is the most common soy ingredient in protein bars?',
    most_common_tail="It's used as a cheap emulsifier in all kinds of bars, not just ones built around a soy protein source.",
    not_labeled_q='Does not being labeled soy free mean a bar contains soy?',
    not_labeled_lead='Not necessarily.',
    not_labeled_tail="The brand just hasn't labeled or certified the bar, which is a different claim from it containing soy.",
    not_what_tail=lambda g: ('Soy lecithin is the most common named reason, followed by soy protein and soybean oil. Most of the '
                             "remaining bars simply haven't been labeled, without an identifiable soy ingredient in the list."),
    quality_q='Are soy free protein bars lower quality than regular bars?',
    quality_lead=lambda g: 'No, the opposite.' if g.stats['abq'] > g.stats['aba'] else 'Not in a meaningful way.',
    quality_tail=quality_tail,
    extra_faqs=lambda g: [('Is soy free the same as vegan?',
                           'No. A soy free bar just has no soy protein, soy lecithin, or soybean oil. It can still contain whey, milk, '
                           "honey, egg, or collagen. Check our Vegan Protein Bars guide separately if that's what you need.")],
    explore=lambda g: explore_cards([
        ('/dairy-free-protein-bars', 'Dairy Free Protein Bars', 'Bars with no whey, milk, or casein in the recipe.'),
        ('/vegan-protein-bars', 'Vegan Protein Bars', 'Bars with no whey, milk, honey, egg, or gelatin.'),
        ('/clean-protein-bars', 'Clean Protein Bars', 'A or B grade bars with no artificial sweeteners and no processed oils.')]),
)

if __name__ == '__main__':
    CertGuide(CFG).build()
