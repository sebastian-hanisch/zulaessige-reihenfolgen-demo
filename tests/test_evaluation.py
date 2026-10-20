"""Auswertung: Analyse von Mini-Plänen, Prüfung vor der Anzeige, Formate."""

import dataclasses
import math
import random

import zrf_algorithm as A
import zrf_constants as C
import zrf_evaluation as ev
import zrf_scenario as S

from conftest import BUDGET, MINI


def _analysis(name, **kw):
    adj = MINI[name][0]
    inst = S.Instance(tuple(tuple(w) for w in adj), tuple(range(len(adj))), frozenset())
    return ev.analyse_instance(inst, ev.Settings(n=len(adj), **kw))


def test_analysis_of_the_n_graph():
    a = _analysis("n_graph", draws=2000)
    assert (a.n, a.extensions, a.ideals, a.exceeded, a.unique, a.hamilton, a.bound) == (4, 5, 8, False, False, False, 9)
    assert a.bounds == ((1, 3), (1, 2), (3, 4), (2, 4)) and a.spread_median == 1.5 and a.sampler_used == "uniform" and not a.fallback and len(a.draws) == 2000 and ev.validate(a) == []
    assert a.naive_ratio == 2.0 and a.log_ext == math.log10(5) and a.log_fact == math.log10(24)


def test_analysis_of_a_chain_and_of_independent_tasks():
    a = _analysis("kette3")
    assert a.unique and a.hamilton and a.extensions == 1 and a.bounds == ((1, 1), (2, 2), (3, 3)) and a.spread_median == 0 and a.naive_ratio == 1.0
    b = _analysis("unabhaengig3")
    assert b.extensions == 6 and b.ideals == 8 and b.bound == 8 and b.spread_median == 2 and set(b.draws) <= set(A.all_extensions(b.adj, 10))


def test_position_distribution_by_hand_on_the_n_graph():
    a = _analysis("n_graph", draws=4000)
    d = ev.position_distribution(a, 2)
    assert d["exact"] == [0, 0, 0.4, 0.6] and ev.tv_distance(d["exact"], d["sampled"]) < 0.05 and abs(sum(d["sampled"]) - 1) < 1e-9
    assert ev.position_distribution(a, 0)["exact"] == [0.4, 0.4, 0.2, 0.0]


def test_before_distribution_by_hand_on_the_n_graph():
    a = _analysis("n_graph", draws=4000)
    d = ev.before_distribution(a, 0)
    assert d["exact"] == [0, 0.4, 1.0, 0.8] and all(abs(x - y) < 0.05 for x, y in zip(d["exact"], d["sampled"])) and d["sampled"][0] == 0
    assert ev.before_distribution(a, 1)["exact"] == [0.6, 0, 1.0, 1.0]


def test_the_sampled_distributions_replace_the_exact_ones_over_the_budget():
    inst = S.Instance(((),) * 17, tuple(range(17)), frozenset())
    a = ev.analyse_instance(inst, ev.Settings(n=17, draws=300))
    assert a.exceeded and ev.position_distribution(a, 3)["exact"] is None and ev.before_distribution(a, 3)["exact"] is None
    assert abs(sum(ev.position_distribution(a, 3)["sampled"]) - 1) < 1e-9 and ev.before_distribution(a, 3)["sampled"][3] == 0


def test_tv_distance_by_hand():
    assert ev.tv_distance([0.5, 0.5], [1.0, 0.0]) == 0.5 and ev.tv_distance([0.2, 0.8], [0.2, 0.8]) == 0 and ev.tv_distance([1, 0], [0, 1]) == 1


def test_a_given_table_equals_the_computed_one_and_none_means_over_the_budget():
    inst = S.make_instance(14, 2.0, 0, 3)
    s = ev.Settings(n=14, seed=3, draws=20)
    t = A.ideal_table(inst.adj, C.IDEAL_BUDGET)
    assert ev.analyse_instance(inst, s, table=t) == ev.analyse_instance(inst, s)
    forced = ev.analyse_instance(inst, s, table=None)
    assert forced.exceeded and forced.extensions is None and forced.fallback


def test_validate_names_every_kind_of_error():
    a = _analysis("n_graph", draws=20)
    assert ev.validate(a) == []
    bad_draw = dataclasses.replace(a, draws=((0, 2, 1, 3),))
    assert any("verletzt eine Beziehung" in p for p in ev.validate(bad_draw))
    zero = dataclasses.replace(a, extensions=0)
    assert any("außerhalb von 1 bis n!" in p for p in ev.validate(zero))
    huge = dataclasses.replace(a, extensions=25)
    assert any("außerhalb von 1 bis n!" in p for p in ev.validate(huge))
    bad_table = dataclasses.replace(a, table=dataclasses.replace(a.table, fwd={**a.table.fwd, 15: 7}))
    assert any("Vorwärts- und Rückwärtszahl" in p for p in ev.validate(bad_table))
    not_unique = dataclasses.replace(a, hamilton=True)
    assert any("Hamilton-Pfad" in p for p in ev.validate(not_unique))
    too_many = dataclasses.replace(a, ideals=a.bound + 1)
    assert any("Schranke" in p for p in ev.validate(too_many))
    off = dataclasses.replace(a, bounds=((1, 1), (1, 2), (3, 4), (2, 4)))
    assert any("Positionsbereiche" in p for p in ev.validate(off))
    no_est = dataclasses.replace(a, estimate=0.0)
    assert any("Schätzer" in p for p in ev.validate(no_est))
    bad_naive = dataclasses.replace(a, naive_probs={(0, 1, 2, 3): 0.5})
    assert any("naiven Verfahrens" in p for p in ev.validate(bad_naive))


def test_labels_and_orders():
    assert ev.label(0) == "1" and ev.format_order((0, 2, 5)) == "1 → 3 → 6"
    assert ev.format_order(tuple(range(20)), limit=14) == "1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → … → 18 → 19 → 20"


def test_number_formats():
    assert ev._i(1234567) == "1.234.567" and ev._dec(12.5) == "12,5" and ev._dec(12.0) == "12" and ev._dec(1.08333, 3) == "1,083" and ev._dec(1234.5) == "1.234,5"
    assert ev._pct(0.4567) == "46" and ev._pct(0.4567, 1) == "45,7" and ev._pct(1.0) == "100" and ev._pct(0.0) == "0"
    assert ev._big(999) == "999" and ev._big(10 ** 15) == "1,00 · 10^15" and ev._big(2.5e20) == "2,50 · 10^20" and ev._pow(9.42) == "10^9,4"


def test_settings_defaults_are_the_constants():
    s = ev.Settings()
    assert (s.n, s.out, s.seed, s.sampler, s.draws, s.steps) == (C.DEFAULT_N, C.DEFAULT_OUT, C.DEFAULT_SEED, C.DEFAULT_SAMPLER, C.DEFAULT_DRAWS, C.DEFAULT_STEPS)


def test_the_same_settings_give_the_same_analysis_and_the_seed_changes_the_draws():
    assert ev.analyse(ev.Settings(14, 2.0, 5, draws=50)) == ev.analyse(ev.Settings(14, 2.0, 5, draws=50))
    assert ev.analyse(ev.Settings(14, 2.0, 5, draws=50)).draws != ev.analyse(ev.Settings(14, 2.0, 6, draws=50)).draws


def test_the_estimator_error_shrinks_with_a_better_plan_and_is_zero_for_a_chain():
    a = _analysis("kette3")
    assert a.estimate == 1.0 and a.estimate_rel_se == 0.0
    b = ev.analyse(ev.Settings(14, 2.0, 2))
    assert 0 < b.estimate_rel_se < 0.5 and abs(b.estimate - b.extensions) / b.extensions < 6 * b.estimate_rel_se + 0.05
