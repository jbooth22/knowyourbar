#!/usr/bin/env python3
"""Rebuild kosher-protein-bars.html from bars.js.

Run from the repo root:  python3 build_kosher_protein_bars.py

Replaces the older full-page generator. Region-marker build via
kyb_cert_guide.CertGuide (live nav/footer/CSS/JS kept; regions from bars.js).

Screen: GUIDE_FILTERS['kosher-protein-bars'] = `Kosher (Y/N)` is Yes. Kosher is
a supervised-process certification, not an ingredient screen, so the three
flagged ingredients (gelatin, confectioner's glaze/shellac, carmine/rennet) are
context only. A kosher-labeled bar can legitimately list certified gelatin, so
those are not warned about.
"""
from kyb_cert_guide import *

FLAGGED = "gelatin, confectioner's glaze, carmine, or rennet"

def disq_intro(g):
    h = {l: len(g.HIT[l]) for l in g.SRC}
    return f'''        <p>We check the Kosher (Y/N) label on file for every bar. Kosher is different from Vegan, Gluten Free, Dairy Free, and Soy Free: it's a supervised-process certification, not primarily an ingredient screen. Whey, milk, soy, wheat, sugar, and nuts can all be kosher when produced and supervised correctly, so an ingredient's mere presence usually doesn't disqualify a bar the way whey disqualifies Dairy Free. {comma(g.N)} of {comma(g.NT)} bars, about {pct0(g.N, g.NT)}%, carry a kosher label. The other {comma(g.ND)}, about {pct0(g.ND, g.NT)}%, don't.</p>
        <p>We do cross-check ingredient lists for three ingredients that are almost never kosher without their own specific certification: gelatin ({h['Gelatin']} bars, {g1(100 * h['Gelatin'] / g.NT)}%), confectioner's glaze or shellac ({h["Confectioner's Glaze / Shellac"]} bars, {g1(100 * h["Confectioner's Glaze / Shellac"] / g.NT)}%), and carmine or rennet ({h['Other Animal-Derived (Carmine, Rennet)']} bars, {g1(100 * h['Other Animal-Derived (Carmine, Rennet)'] / g.NT)}%). Together those account for only a small share of the {comma(g.ND)} bars that aren't labeled kosher. The remaining {comma(len(g.UNLAB))} bars, {g1(100 * len(g.UNLAB) / g.NT)}% of the full database, show none of those ingredients at all. They simply haven't been through kosher certification, which is a different claim from containing something non-kosher.</p>'''

def lead_insights(g):
    named_share = pct(len(g.NAMED), g.ND)
    unl_share = pct(len(g.UNLAB), g.ND)
    g.C.check(unl_share > 75, 'most non-kosher bars show none of the flagged ingredients')
    name, hits, total, _ = g.example
    return [
        ('Kosher disqualification is almost always about certification, not ingredients.',
         f'Only {named_share}% of non-kosher bars contain {FLAGGED}, the named factors we can actually detect. The other '
         f"{unl_share}% simply haven't sought certification."),
        (f'{name} shows the gelatin pattern clearly.',
         f"{hits} of {name}'s {total} flavors use gelatin directly. None of {name}'s flavors are labeled kosher."),
    ]

CFG = dict(
    slug='kosher-protein-bars', page='kosher-protein-bars.html', url='https://knowyourbar.com/kosher-protein-bars',
    published='2026-09-17', flag='Kosher (Y/N)', word='kosher', Word='Kosher', table_id='ks',
    sources_allowed_in_qualifying=True,
    sources=[
        dict(label='Gelatin', rx=r'\bgelatin\b',
             desc='Almost always derived from pork or non-ritually-slaughtered animal collagen, used in the puff or crisp layer of several bars. Fish and certified-kosher beef gelatin exist, but plain "gelatin" on a US ingredient label defaults to non-kosher.'),
        dict(label="Confectioner's Glaze / Shellac", prose="confectioner's glaze", rx=r'shellac|confectioner.?s glaze',
             desc='A resin secreted by the lac insect, used as a shiny coating on some candy-coated pieces and drizzles. An insect-derived ingredient, not kosher without its own certification.'),
        dict(label='Other Animal-Derived (Carmine, Rennet)', prose='carmine or rennet', rx=r'\bcarmine\b|cochineal|\brennet\b',
             desc='Carmine/cochineal (an insect-derived red colorant) and rennet (traditionally animal-derived, used in some dairy-protein blends). The rarest of the three named factors here.'),
    ],
    sources_or=FLAGGED,
    unlabeled_label='Not kosher-certified',
    unlabeled_desc=f"No {FLAGGED} shows up anywhere in the ingredient list we can find. These bars aren't disqualified by a specific non-kosher ingredient, the brand simply hasn't pursued kosher certification, which is a supervised-process claim, not just an ingredient checklist.",
    disq_intro=disq_intro,
    hero_extra="Most of the rest simply haven't sought certification, not because of a specific non-kosher ingredient.",
    og_desc='{n} kosher-certified protein bars. Ranked by ingredient quality score.',
    big_stat=lambda g: (f'{pct(len(g.UNLAB), g.ND)}%', 'of non-kosher protein bars have no identifiable non-kosher ingredient at all',
                        f"{comma(len(g.UNLAB))} of the {comma(g.ND)} bars without a kosher label show no {FLAGGED} anywhere in "
                        'their own ingredient list. For most brands, not being kosher-certified is a business decision, not a '
                        'formulation problem.'),
    lead_insights=lead_insights,
    full_lineup_tail='these brands have pursued kosher certification across the board rather than for a single flagship flavor.',
    example_brand='Built', example_source='Gelatin', example_verb='use',
    brands_intro="Some brands pursue kosher certification across their whole lineup, others don't have a single kosher flavor. Grade columns below show ingredient quality only, not an overall bar rating. Click any brand name to jump to its flavors in the table below.",
    avoid_note="These brands aren't kosher-certified across most or all of their lineup, whether or not a specific non-kosher ingredient is identifiable.",
    avoid_head='Flavors Without Kosher Label', avoid_last_head='Likely Reason',
    what_makes=lambda g: (f'We use the Kosher (Y/N) label on file for each bar. {comma(g.N)} of the {comma(g.NT)} bars we track carry '
                          "that label. Kosher is a supervised-process certification, not just an ingredient list, so we can't fully "
                          'verify it ourselves the way we can with an ingredient-based screen. We do flag three ingredients that are '
                          "almost never kosher without their own certification: gelatin, confectioner's glaze or shellac, and carmine or rennet."),
    most_common_q='What ingredient most often disqualifies a bar from being kosher?',
    most_common_tail="But it's the exception, not the rule: most non-kosher bars don't contain any of the ingredients we flag at all.",
    not_labeled_q='Does not being labeled kosher mean a bar contains a non-kosher ingredient?',
    not_labeled_lead='Not necessarily, and usually not.',
    not_labeled_tail="For most brands, not being kosher-certified just means they haven't pursued the certification, not that the bar contains something non-kosher.",
    not_what_tail=lambda g: ("Most simply haven't gone through kosher certification. Gelatin is the most common of the few "
                             "ingredients we can actually flag as a likely reason, followed by confectioner's glaze and carmine or rennet."),
    quality_q='Are kosher protein bars lower or higher quality than regular bars?',
    quality_lead=lambda g: ('About the same.' if abs(g.stats['abq'] - g.stats['aba']) <= 5 else
                            'Higher, on average.' if g.stats['abq'] > g.stats['aba'] else 'Somewhat lower, on average.'),
    quality_tail=lambda g: ("Kosher certification is a separate claim from ingredient quality. What kosher bars do give up on average "
                            f"is protein: they average {fnum(round(g.stats['pq'], 1))}g against a database-wide average of "
                            f"{fnum(round(g.stats['pa'], 1))}g, since the kosher-certified set skews toward smaller, snack-style bars."),
    explore=lambda g: explore_cards([
        ('/dairy-free-protein-bars', 'Dairy Free Protein Bars', 'Bars with no whey, milk, or casein in the recipe.'),
        ('/vegan-protein-bars', 'Vegan Protein Bars', 'Bars with no whey, milk, honey, egg, or gelatin.'),
        ('/clean-protein-bars', 'Clean Protein Bars', 'A or B grade bars with no artificial sweeteners and no processed oils.')]),
)

if __name__ == '__main__':
    CertGuide(CFG).build()
