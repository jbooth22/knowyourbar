#!/usr/bin/env python3
"""Rebuild dairy-free-protein-bars.html from bars.js.

Run from the repo root:  python3 build_dairy_free_protein_bars.py

Replaces the older full-page generator. Region-marker build via
kyb_cert_guide.CertGuide: the live page keeps its nav, footer, fonts, CSS and
JS; only the <!-- kyb:NAME --> regions are rewritten, all from bars.js.

Screen: GUIDE_FILTERS['dairy-free-protein-bars'] = `Dairy Free (Y/N)` is Yes.
Whey, milk and casein are counted by ingredient text over the bars without the
label. A dairy-free-labeled bar whose ingredients name one is printed as a
WARNING (fix upstream in bars.js).
"""
from kyb_cert_guide import *

NOT_PLANT_MILK = r'(?<!coconut )(?<!almond )(?<!oat )(?<!rice )(?<!soy )(?<!cashew )(?<!hemp )'

def disq_intro(g):
    h = {l: len(g.HIT[l]) for l in g.SRC}
    return f'''        <p>We check the Dairy Free (Y/N) label on file for every bar, then cross-check ingredient lists ourselves for whey, milk, and casein, the three named dairy sources that show up most in the data. {comma(g.N)} of {comma(g.NT)} bars, about {pct0(g.N, g.NT)}%, carry a dairy free label. The other {comma(g.ND)}, about {pct0(g.ND, g.NT)}%, don't.</p>
        <p>Whey is the most common named source at {comma(h['Whey'])} bars ({g1(100 * h['Whey'] / g.NT)}% of the full database), usually as the bar's main protein. Milk shows up in {comma(h['Milk'])} bars ({g1(100 * h['Milk'] / g.NT)}%), and casein in {comma(h['Casein'])} bars ({g1(100 * h['Casein'] / g.NT)}%). The remaining {comma(len(g.UNLAB))} bars, {g1(100 * len(g.UNLAB) / g.NT)}% of the full database, show no whey, milk, or casein in their own ingredient list at all. They just aren't labeled dairy free, which is a different claim from actually containing dairy.</p>'''

def lead_insights(g):
    w = len(g.HIT['Whey'])
    other = len(g.HIT['Milk']) + len(g.HIT['Casein'])
    g.C.check(g.ORDER[0] == 'Whey', 'whey is the most common named dairy source')
    name, hits, total, _ = g.example
    return [
        ('Whey is the clearest single dairy source.',
         f'{comma(w)} bars ({g1(100 * w / g.NT)}% of the database) name whey directly, '
         + ('more than the milk and casein counts combined.' if w > other else 'more than milk or casein on its own.')),
        (f'{name} shows the pattern clearly.',
         f"{hits} of {name}'s {total} flavors use whey directly. None of {name}'s flavors are labeled dairy free."),
    ]

CFG = dict(
    slug='dairy-free-protein-bars', page='dairy-free-protein-bars.html', url='https://knowyourbar.com/dairy-free-protein-bars',
    published='2026-09-04', flag='Dairy Free (Y/N)', word='dairy free', Word='Dairy Free', table_id='df',
    sources=[
        dict(label='Whey', rx=r'\bwhey\b', desc='The most common dairy protein source, usually whey protein concentrate or isolate leading the ingredient list.'),
        dict(label='Milk', rx=NOT_PLANT_MILK + r'\bmilk\b|milkfat|butterfat|lactose|\bcheese|yogurt|\bghee\b|\bcream\b(?! of tartar)',
             desc='Shows up as nonfat milk, milk powder, or milk chocolate coating, usually a moisture or flavor component rather than the main protein source.'),
        dict(label='Casein', rx=r'casein', desc='Usually sodium or calcium caseinate, a slow-digesting milk protein added alongside or instead of whey.'),
    ],
    sources_or='whey, milk, or casein',
    unlabeled_label='Not labeled dairy free',
    unlabeled_desc="No whey, milk, or casein shows up anywhere in the ingredient list we can find, but the brand hasn't labeled or certified the bar dairy free either. That is a labeling gap, not proof the bar contains dairy.",
    disq_intro=disq_intro,
    hero_extra='Most of the rest lean on whey protein.',
    og_desc='{n} dairy free protein bars with no whey, milk, or casein in the recipe. Ranked by ingredient quality score.',
    big_stat=lambda g: (f'{g1(100 * len(g.UNLAB) / g.NT)}%', "of all protein bars show no whey, milk, or casein, yet still aren't labeled dairy free",
                        f"{comma(len(g.UNLAB))} of the {comma(g.NT)} bars we track have no whey, milk, or casein anywhere in their own "
                        "ingredient list, but the brand hasn't labeled or certified them dairy free. Not being labeled dairy free is "
                        'not the same as containing dairy.'),
    lead_insights=lead_insights,
    full_lineup_tail='these brands build around a plant, egg, or collagen protein source from the start, rather than swapping whey out flavor by flavor.',
    example_brand='Quest', example_source='Whey', example_verb='use',
    brands_intro='Some brands build their whole lineup without whey, milk, or casein, others lean on it across the board. Grade columns below show ingredient quality only, not an overall bar rating. Click any brand name to jump to its flavors in the table below.',
    avoid_note='These brands lean on whey, milk, casein, or an unlabeled formula across most or all of their lineup.',
    avoid_head='Flavors Without Dairy Free Label', avoid_last_head='Dairy Source Found',
    what_makes=lambda g: (f'We use the Dairy Free (Y/N) label on file for each bar. {comma(g.N)} of the {comma(g.NT)} bars we track '
                          'carry that label. We also cross-check ingredient lists ourselves for whey, milk, and casein, the three '
                          'named dairy sources that show up most in the data.'),
    most_common_q='What is the most common dairy ingredient in protein bars?',
    most_common_tail="Most brands use it as the bar's main protein source, not a minor add-in.",
    not_labeled_q='Does not being labeled dairy free mean a bar contains dairy?',
    not_labeled_lead='Not necessarily.',
    not_labeled_tail="The brand just hasn't labeled or certified the bar, which is a different claim from it containing dairy.",
    not_what_tail=lambda g: ('Whey is the most common named reason, followed by milk and casein. Most of the remaining bars simply '
                             "haven't been labeled, without an identifiable dairy ingredient in the list."),
    quality_q='Are dairy free protein bars lower quality than regular bars?',
    quality_lead=lambda g: 'No.' if g.stats['abq'] >= g.stats['aba'] else 'Slightly, on average.',
    quality_tail=lambda g: (f"What they give up on average is protein: dairy free bars average {fnum(round(g.stats['pq'], 1))}g "
                            f"against a database-wide average of {fnum(round(g.stats['pa'], 1))}g, since most whey-based bars are "
                            'built to maximize protein per calorie.'),
    extra_faqs=lambda g: [('Is dairy free the same as vegan?',
                           'No. A dairy free bar just has no whey, milk, or casein. It can still contain honey, egg white protein, '
                           "collagen, or gelatin, none of which are vegan. Check our Vegan Protein Bars guide separately if that's what you need.")],
    explore=lambda g: explore_cards([
        ('/gluten-free-protein-bars', 'Gluten Free Protein Bars', 'Bars with no wheat or barley in the recipe.'),
        ('/vegan-protein-bars', 'Vegan Protein Bars', 'Bars with no whey, milk, honey, egg, or gelatin.'),
        ('/clean-protein-bars', 'Clean Protein Bars', 'A or B grade bars with no artificial sweeteners and no processed oils.')]),
)

if __name__ == '__main__':
    CertGuide(CFG).build()
