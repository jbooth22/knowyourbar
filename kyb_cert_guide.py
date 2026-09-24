"""Shared builder for the label-based "free-from / certified" guides
(Dairy Free, Soy Free, Kosher). Each page script passes a small config: the
bars.js flag, the named ingredient sources it cross-checks, and the handful of
sentences that are specific to that guide. Everything numeric comes from
bars.js; copy that depends on a fact is checked (Claims) and the build stops
if one stops being true.

Region layout is the TEMPLATE_GUIDE one used by vegan / gluten-free:
head-meta, jsonld-*, social, hero, snapshot, picks,
what-disqualifies-a-protein-bar-from-bei, findings, brands, list-heading,
result-count, bar-rows, bar-data, cta-heading, explore-more, faq.
"""
import re
from collections import Counter
from kyb_guide_lib import *


def label_text(b):
    """Ingredient text without a trailing allergen / shared-facility statement."""
    return re.split(r'may contain|manufactured (?:in|on)|processed (?:in|on)|produced (?:in|on)|in a facility',
                    ingr(b), flags=re.I)[0]


class CertGuide:
    def __init__(self, cfg):
        self.cfg = c = cfg
        self.ALL = load_bars()
        self.QF = GUIDE_FILTERS[c['slug']]
        self.Q = [b for b in self.ALL if self.QF(b)]
        self.D = [b for b in self.ALL if not self.QF(b)]
        self.N, self.ND, self.NT = len(self.Q), len(self.D), len(self.ALL)
        self.C = Claims()
        c['Cap'] = c['word'][:1].upper() + c['word'][1:]
        self.SRC = [s['label'] for s in c['sources']]
        self.RX = {s['label']: s['rx'] for s in c['sources']}
        self.PROSE = {s['label']: s.get('prose', s['label'].lower()) for s in c['sources']}
        self.HIT = {l: [b for b in self.D if self.has(b, l)] for l in self.SRC}
        self.NAMED = [b for b in self.D if any(self.has(b, l) for l in self.SRC)]
        self.UNLAB = [b for b in self.D if b not in self.NAMED]
        self.ORDER = sorted(self.SRC, key=lambda l: -len(self.HIT[l]))
        self.split = brand_split(self.ALL, self.QF)
        for b in self.Q:
            found = [l for l in self.SRC if self.has(b, l)]
            if found and not c.get('sources_allowed_in_qualifying') and not reviewed_ok(b, c['word'].lower()):
                print(f"WARNING: {full(b)} is labeled {c['word']} in bars.js but its ingredients name "
                      f"{names_and(x.lower() for x in found)}. Check the label; the page follows bars.js.")

    def has(self, b, label):
        return bool(re.search(self.RX[label], label_text(b), re.I))

    # -- small helpers -------------------------------------------------------
    def ab(self, bars):
        return pct(sum(1 for x in bars if x.get('score_band') in ('A', 'B')), len(bars))

    def brand(self, name):
        return next((r for r in self.split[0] + self.split[1] + self.split[2] if r['brand'] == name), None)

    # -- sections ------------------------------------------------------------
    def picks(self):
        c, Q = self.cfg, self.Q
        PK = Picker(Q, diverse=True)
        SCO = Scoper(Q, 'on this page')
        NI = lambda b: top_level_ingredient_count(ingr(b))
        best = PK.balanced()
        top_p = PK.pick(lambda b: (-P(b), CAL(b)))
        low_s = PK.pick(lambda b: (SUG(b), -P(b)))
        top_f = PK.pick(lambda b: (-FIB(b), -P(b)))
        keto = GUIDE_FILTERS['keto-protein-bars']
        n_keto = sum(1 for b in Q if keto(b))
        sixth = PK.pick(lambda b: (net_carbs(b), -P(b)), keto) if n_keto else PK.pick(lambda b: (CAL(b), -P(b)))
        simple = PK.pick(lambda b: (NI(b), -P(b)))
        self.C.check(all([best, top_p, low_s, top_f, sixth, simple]), 'six distinct top picks available')
        lab = ', '.join(re.sub(r'\s*[\(\[].*$', '', it).strip().lower() for it in top_level_items(ingr(simple).strip().rstrip('.')))
        w = c['word']
        picks = [
            ['Best overall', best,
             f"{fnum(P(best))}g protein, {fnum(FIB(best))}g fiber, and {fnum(SUG(best))}g sugar in one {w} bar. "
             + ("Solid across the board rather than an extreme on one metric." if P(best) >= 15 and FIB(best) >= 5 and SUG(best) <= 5
                else "The best balance of protein, fiber, and sugar among the top-graded bars here.")],
            ['Highest protein', top_p, f"{fnum(P(top_p))}g protein at {fnum(CAL(top_p))} calories, {SCO(P, top_p, 'most')}."],
            ['Lowest sugar', low_s, f"{fnum(SUG(low_s))}g of sugar with {fnum(P(low_s))}g protein, {SCO(SUG, low_s, 'lowest', False)}."],
            ['Most fiber', top_f, f"{fnum(FIB(top_f))}g of fiber alongside {fnum(P(top_f))}g protein, {SCO(FIB, top_f, 'most')}."],
            (['Best for keto', sixth, self._keto_text(sixth, n_keto)] if n_keto else
             ['Lowest calorie', sixth, f"{fnum(CAL(sixth))} calories with {fnum(P(sixth))}g protein, {SCO(CAL, sixth, 'lowest', False)}."]),
            ['Simplest ingredient list', simple,
             f"{num_word(NI(simple)).capitalize()} ingredients: {lab}." if NI(simple) <= 6 else
             f"{NI(simple)} ingredients, the shortest label of any {simple['score_band']}-grade {w} bar left after the picks above."],
        ]
        add_sugar_tradeoff(picks)
        if P(simple) < 10 and 'tradeoff' not in picks[5][2]:
            picks[5][2] += f" The tradeoff is protein: just {fnum(P(simple))}g, closer to a whole-food snack than a protein bar."
        return picks

    def _keto_text(self, b, n_keto):
        w = self.cfg['word']
        sa = f" and {fnum(SA(b))}g sugar alcohol" if SA(b) else ''
        head = (f"{fnum(net_carbs(b))}g net carbs ({fnum(num(b.get('Total Carbohydrates (g)')))}g total carbs minus "
                f"{fnum(FIB(b))}g fiber{sa}), {fnum(P(b))}g protein, {fnum(num(b.get('Total Fat (g)')))}g fat.")
        tail = (f" One of {n_keto} {w} bars that also clear our keto screen." if n_keto > 1
                else f" The only {w} bar that also clears our keto screen.")
        return head + tail

    def card(self, label, bars_hit, desc, found=True):
        return (f'''<div class="score-card">
  <div class="score-card-label">{esc(label)}</div>
  <div class="score-card-val">{comma(len(bars_hit))} bars<span class="oil-card-pct">{g1(100 * len(bars_hit) / self.NT)}%</span></div>
  <div class="score-card-desc">{esc(desc)}</div>''' + (f'\n  {found_in_html(bars_hit)}' if found else '') + '\n</div>')

    def disq_section(self):
        c = self.cfg
        cards = '\n'.join(self.card(s['label'], self.HIT[s['label']], s['desc']) for s in
                          sorted(c['sources'], key=lambda s: -len(self.HIT[s['label']])))
        cards += '\n' + self.card(c['unlabeled_label'], self.UNLAB, c['unlabeled_desc'], found=False)
        return f'''
    <div class="section-inner">
      <h2 class="section-title">What disqualifies a protein bar from being {esc(c['word'])}</h2>
      <div class="section-body">
{c['disq_intro'](self)}
      </div>
      <div class="score-grid" style="margin-top:1.5rem;">
{cards}
      </div>
    </div>
'''

    def generic_insights(self):
        c, Q, ALL = self.cfg, self.Q, self.ALL
        consider, mixed, avoid = self.split
        full_brands = sorted((r for r in consider if r['d'] == 0), key=lambda r: (-r['total'], r['brand'].lower()))
        self.C.check(len(full_brands) >= 4, f"at least four brands are {c['word']} across the whole lineup")
        leaders = [f"{r['brand']} ({r['total']})" for r in full_brands[:4]]
        split_ex = min((r for r in consider + mixed + avoid if r['q'] and r['d'] and r['total'] >= 10),
                       key=lambda r: (abs(r['q'] / r['total'] - 0.5), -r['total'], r['brand']))
        pq, pa = avg(Q, 'Protein (g)'), avg(ALL, 'Protein (g)')
        fq, fa = avg(Q, 'Dietary Fiber (g)'), avg(ALL, 'Dietary Fiber (g)')
        fib = 'about the same fiber' if abs(fq - fa) < 0.3 else ('more fiber' if fq > fa else 'less fiber')
        prot = 'less protein' if pq < pa - 0.3 else ('more protein' if pq > pa + 0.3 else 'about the same protein')
        abq, aba = self.ab(Q), self.ab(ALL)
        gword = ('noticeably better than' if abq - aba >= 5 else 'slightly better than' if abq > aba + 1
                 else 'about the same as' if abs(abq - aba) <= 1 else 'slightly below' if abq > aba - 5 else 'noticeably below')
        self.full_brands, self.split_ex = full_brands, split_ex
        self.near_even = abs(split_ex['q'] / split_ex['total'] - 0.5) <= 0.15
        self.stats = dict(pq=pq, pa=pa, fq=fq, fa=fa, abq=abq, aba=aba, gword=gword, prot=prot, fib=fib)
        out = [
            (f"{len(full_brands)} brands are {c['word']} across their entire lineup.",
             f"Led by {names_and(leaders)}, {c['full_lineup_tail']}"),
            (f"{c['Cap']} bars grade {gword} the database average.",
             f"{abq}% of {c['word']} bars grade A or B, against {aba}% database-wide."),
            (f"{c['Cap']} bars average {prot}, {fib}.",
             f"{c['Cap']} bars average {fnum(round(pq, 1))}g of protein against a database-wide average of {fnum(round(pa, 1))}g, "
             f"and {g1(fq)}g of fiber vs. {g1(fa)}g."),
            ((f"{split_ex['brand']} splits closer to even than any other large lineup." if self.near_even else
              'Mixed lineups are the exception, not the rule.'),
             (f"{split_ex['q']} of the {split_ex['total']} {split_ex['brand']} flavors are {c['word']}, the rest are not." if self.near_even else
              f"{split_ex['brand']} is the clearest large example: {split_ex['q']} of {split_ex['total']} flavors are {c['word']}, the rest are not.")
             + ' Always check the specific flavor, not just the brand.'),
        ]
        skip = c.get('skip_generic', set())
        if 'grade' in skip:
            out = [x for x in out if 'grade' not in x[0] or 'across their entire lineup' in x[0]]
        return out

    def example_brand(self):
        """(brand, source) pattern sentence: e.g. Quest + whey for dairy free."""
        c = self.cfg
        name, src = c['example_brand'], c['example_source']
        bars = [b for b in self.ALL if b['Brand Name'] == name]
        hits = [b for b in bars if self.has(b, src)]
        self.C.check(bars and not any(self.QF(b) for b in bars) and hits,
                     f"{name}: none labeled {c['word']} and some use {src.lower()}")
        return name, len(hits), len(bars), src

    def brands(self):
        c = self.cfg
        consider, mixed, avoid = self.split
        def found(r):
            cnt = Counter(l for b in r['disq'] for l in self.SRC if self.has(b, l))
            top = [l for l, _ in sorted(cnt.items(), key=lambda kv: (-kv[1], self.ORDER.index(kv[0])))[:3]]
            return names_and([top[0]] + [self.PROSE[t] for t in top[1:]]) if top else c['unlabeled_label']
        W = c['Word']
        return brand_tables_html(
            self.split, self.QF, h2=f'Best Brands of {W} Protein Bars', intro=c['brands_intro'],
            table_id=c['table_id'],
            consider_note=(f"Every flavor from these {len(consider)} brands is {c['word']}." if all(r['d'] == 0 for r in consider)
                           else f"Every flavor, or nearly every flavor, from these {len(consider)} brands is {c['word']}."),
            avoid_note=c['avoid_note'],
            mixed_note=f"Some flavors are {c['word']}, some aren't. Check the specific flavor before buying.",
            avoid_head=c['avoid_head'], avoid_last_head=c['avoid_last_head'], avoid_last=found,
            mixed_head=f'{W} Flavors', pick_word=f"{c['word']} pick", pick_head=f'{W} Pick',
            consider_all=f"{c['Cap']} across the whole lineup", consider_some='{q} of {total} flavors are ' + c['word'])

    def faqs(self):
        c, s = self.cfg, self.stats
        W, w = c['Word'], c['word']
        ex_name, ex_hits, ex_total, ex_src = self.example
        brands_q = len({b['Brand Name'] for b in self.Q})
        a_q = sum(1 for b in self.Q if b.get('score_band') == 'A')
        top = self.ORDER[0]
        rest = [self.PROSE[l] for l in self.ORDER[1:]]
        more_than = (f"more than {names_and(rest)} combined" if len(self.HIT[top]) > sum(len(self.HIT[l]) for l in self.ORDER[1:])
                     else f"more than {' or '.join(rest)} on its own")
        faqs = [
            (f'What makes a protein bar {w} on this site?', c['what_makes'](self)),
            (f'How many {w} protein bars are in your database?',
             f"{comma(self.N)} of the {comma(self.NT)} bars we track are labeled {w}, spanning {brands_q} brands. {a_q} of those "
             f"{comma(self.N)} bars grade A for ingredient quality."),
            (f'Is {ex_name} {w}?',
             f"No. {ex_hits} of {ex_name}'s {ex_total} flavors {c['example_verb']} {ex_src.lower()} directly, and none of "
             f"{ex_name}'s flavors carry a {w} label."),
            (c['most_common_q'],
             f"{self.PROSE[top][:1].upper() + self.PROSE[top][1:]}. It shows up by name in {len(self.HIT[top])} of the {comma(self.NT)} bars we track, {more_than}. "
             + c['most_common_tail']),
            (c['not_labeled_q'],
             f"{c['not_labeled_lead']} {comma(len(self.UNLAB))} of the {comma(self.ND)} bars that don't carry our {w} label show no "
             f"{c['sources_or']} anywhere in their own ingredient list. {c['not_labeled_tail']}"),
            (f"Can a brand have some {w} flavors and some that aren't?",
             (f"Yes. {self.split_ex['brand']} splits closest to even of any large lineup we checked: " if self.near_even else
              f"Yes. {self.split_ex['brand']} is a good example: ")
             + f"{self.split_ex['q']} of {self.split_ex['total']} flavors are {w}. Always check the specific flavor, not just the brand."),
            (f'What protein bars are {w}?',
             f"{comma(self.N)} bars across {brands_q} brands carry a {w} label, led by brands like {self.full_brands[0]['brand']} "
             f"and {self.full_brands[1]['brand']} that qualify across their entire lineup. The full ranked list is in the table "
             'below, sorted by ingredient quality.'),
            (f'What protein bars are not {w}?',
             f"{comma(self.ND)} of the {comma(self.NT)} bars we track don't carry a {w} label. {c['not_what_tail'](self)}"),
            (c['quality_q'],
             f"{c['quality_lead'](self)} {c['Cap']} bars in our database grade A or B {s['abq']}% of the time, against {s['aba']}% "
             f"database-wide. {c['quality_tail'](self)}"),
        ] + c.get('extra_faqs', lambda g: [])(self) + [
            ('How often is this list updated?',
             'We update the database whenever new bars are added or a brand reformulates. Manufacturers do change their '
             'ingredient lists over time, so always confirm against the packaging in front of you. This page reflects the '
             f'database as of {today_iso()}.'),
        ]
        return faqs

    # -- assemble ------------------------------------------------------------
    def regions(self):
        c = self.cfg
        W, w = c['Word'], c['word']
        N, ND, NT = self.N, self.ND, self.NT
        self.example = self.example_brand()
        picks = self.picks()
        insights = c['lead_insights'](self) + self.generic_insights() + c.get('tail_insights', lambda g: [])(self)
        findings = findings_html(f'What we found screening {comma(NT)} bars', *c['big_stat'](self), insights)
        disq = self.disq_section()
        brands = self.brands()
        faqs = self.faqs()
        title = f'{pct0(N, NT)}% of Protein Bars Are {W}. See All {comma(N)}.'
        h1 = f'Best {W} Protein Bars - Ranking {comma(N)} Qualified Bars'
        desc = f'We checked {comma(NT)} protein bars against their {w} label. {comma(N)} qualify. See every one, ranked by ingredient quality, brand, and macros.'
        og = c['og_desc'].format(n=comma(N))
        regions = [r for r in guide_head_regions(title=title, h1=h1, desc=desc, og_desc=og, url=c['url'], about=f'{W} Protein Bars',
                                                 published=c['published'], faqs=faqs, picks=picks) if r[0] != 'social']
        regions += [
            ('social', social_title_html(title, og, c['url'])),
            ('hero', f'''<h1 class="hero-title">{esc(h1)}</h1>
    <p class="hero-sub" style="color:#e8e4dc;">We checked {comma(NT)} protein bars available in the US against their {esc(c['flag'])} label. The result: {comma(N)} bars, about {pct0(N, NT)}%, are labeled {esc(w)}. {esc(c['hero_extra'])} We rank the best {esc(w)} protein bars by ingredient quality, brand, and macros. Not just us telling you the flavors we like.</p>'''),
            ('snapshot', f'''
    <div class="snap-item"><div class="snap-value">{comma(N)}</div><div class="snap-label">Bars qualify</div></div>
    <div class="snap-item"><div class="snap-value">{comma(ND)}</div><div class="snap-label">Bars disqualified</div></div>
    <div class="snap-item"><div class="snap-value">{sum(1 for b in self.Q if b.get('score_band') == 'A')}</div><div class="snap-label">A-grade bars</div></div>
    <div class="snap-item"><div class="snap-value">{len({b['Brand Name'] for b in self.Q})}</div><div class="snap-label">Brands represented</div></div>
    <div class="snap-item"><div class="snap-value">{avg(self.Q, 'Protein (g)'):.1f}g</div><div class="snap-label">Avg protein</div></div>
  '''),
            ('picks', picks_section_html(f'Top picks for {w} protein bars',
                                         "Everyone has their own reason for wanting a protein bar, but if you're on this page, you "
                                         f"already know you want one that's {w}. Here are the best bars for what people typically look "
                                         f"for, all {w}. Grades below reflect ingredient quality only, not an overall bar rating.", picks)),
            ('what-disqualifies-a-protein-bar-from-bei', disq),
            ('findings', findings),
            ('brands', brands),
            ('cta-heading', f'<h2 class="explore-cta-main-heading">See every bar that fits, not just the {comma(N)} on this page</h2>'),
            ('explore-more', c['explore'](self)),
            ('faq', faq_items_html(faqs)),
        ]
        regions += guide_list_regions(self.Q, self.ALL, heading=f'{comma(N)} {w} protein bars, ranked by ingredient quality', lazy_attr=True)
        self.picks_out = picks
        return regions

    def build(self):
        regions = self.regions()
        n = build_guide_page(self.cfg['page'], regions, self.Q, self.ALL, self.C)
        print(f"{self.cfg['page']}: {self.N} qualify, {self.ND} disqualified, {n} rows, grade-sync 0 mismatches")
        for label, b, why in self.picks_out:
            print(f'  {label}: {full(b)} ({b["score_band"]})')


def explore_cards(cards):
    return '\n' + ''.join(f'''        <a href="{href}" class="explore-more-card">
          <div class="explore-more-title">{esc(t)}</div>
          <div class="explore-more-desc">{esc(d)}</div>
        </a>
''' for href, t, d in cards) + '      '
