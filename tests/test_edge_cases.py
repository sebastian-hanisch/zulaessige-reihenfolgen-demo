"""Randfälle, an denen Kernroutinen erfahrungsgemäß brechen (DEMO-PLAYBOOK §12): kleinste Pläne, Grenzen inklusive, Budgetgrenze, vollständige Ordnung, Regler-Extreme."""

import itertools
import math

import pytest

import zrf_algorithm as A
import zrf_constants as C
import zrf_evaluation as ev
import zrf_scenario as S

from conftest import BUDGET


def _analysis(adj, **kw):
    inst = S.Instance(tuple(tuple(w) for w in adj), tuple(range(len(adj))), frozenset())
    return ev.analyse_instance(inst, ev.Settings(n=len(adj), draws=50, **kw))


def test_a_single_task_has_one_order_and_no_room():
    a = _analysis(((),))
    assert a.extensions == 1 and a.ideals == 2 and a.unique and a.bounds == ((1, 1),) and a.draws == ((0,),) * 50 and ev.validate(a) == []


def test_exactly_two_tasks_with_and_without_relation():
    assert A.count_extensions(((1,), ()), BUDGET) == 1 and A.count_extensions(((), ()), BUDGET) == 2
    a = _analysis(((), ()))
    assert a.extensions == 2 and not a.unique and a.spread_median == 1 and set(a.draws) == {(0, 1), (1, 0)}


def test_independent_tasks_have_factorial_orders_and_power_of_two_ideals():
    n = 8
    a = _analysis(((),) * n)
    assert a.extensions == math.factorial(n) and a.ideals == 2 ** n and a.bound == 2 ** n and ev.validate(a) == []


def test_a_complete_order_has_one_order_and_ideals_equal_n_plus_one():
    n = 20
    adj = tuple(tuple(range(i + 1, n)) for i in range(n))
    a = _analysis(adj)
    assert a.extensions == 1 and a.ideals == n + 1 and a.unique and a.hamilton and ev.validate(a) == []


def test_the_budget_boundary_is_inclusive():
    adj = ((),) * 10                                                                               # 1024 Ideale
    assert A.ideal_table(adj, 1024) is not None and A.ideal_table(adj, 1023) is None and A.count_ideals(adj, 1024) == (1024, False)


def test_a_plan_over_the_budget_is_handled_end_to_end():
    adj = ((),) * 17                                                                               # 2^17 = 131 072 Ideale > Budget
    a = _analysis(adj, sampler="uniform")
    assert a.exceeded and a.extensions is None and a.table is None and a.fallback and a.sampler_used == "naive" and ev.validate(a) == []
    assert ev.verdict_question(a)[0] == "warning" and abs(a.estimate - math.factorial(17)) / math.factorial(17) < 1e-9      # lauter unabhängige Aufgaben: das Produkt ist bei jedem Weg 17!
    assert ev.position_distribution(a, 0)["exact"] is None and ev.before_distribution(a, 0)["exact"] is None and len(ev.position_distribution(a, 0)["sampled"]) == 17


def test_the_smallest_slider_plan_is_valid_for_every_sampler():
    for sampler in C.SAMPLERS:
        a = ev.analyse(ev.Settings(C.N_MIN, C.OUT_MIN, 1, sampler, C.DRAWS[0], C.STEPS[0]))
        assert a.n == 6 and ev.validate(a) == []


def test_the_largest_slider_plans_validate_exact_or_over_the_budget():
    """Worst-Case am Regler-Maximum (n = 40) bei dünner und dichter Besetzung, 5 000 Züge: kein Hänger, alle Prüfungen bestehen. Keine Zeit-Assertion."""
    for out in (C.OUT_MIN, 2.0, C.OUT_MAX):
        a = ev.analyse(ev.Settings(C.N_MAX, out, 3, "chain", C.DRAWS[-1], C.STEPS[0]))
        assert a.n == 40 and ev.validate(a) == [] and a.exceeded == (a.extensions is None)


def test_bounds_are_inclusive():
    """Reglergrenzen gelten inklusive: n = 6 und n = 40, Ausgangsgrad 0,5 und 4 sind erlaubt."""
    for n in (C.N_MIN, C.N_MAX):
        for out in (C.OUT_MIN, C.OUT_MAX):
            inst = S.make_instance(n, out, 0, 1)
            assert inst.n == n and A.topological_order(inst.adj) is not None


def test_the_empty_plan_is_handled_by_every_helper():
    a = ev.analyse_instance(S.Instance((), (), frozenset()), ev.Settings(n=0, draws=5))
    assert a.extensions == 1 and ev.validate(a) == [] and ev.verdict_question(a) == ("info", "Der Plan ist leer.") and a.draws == ((),) * 5 and a.spread_median == 0


def test_every_draw_count_and_step_count_gives_a_valid_analysis():
    for draws, steps in itertools.product(C.DRAWS, C.STEPS):
        a = ev.analyse(ev.Settings(10, 2.0, 2, "chain", draws, steps))
        assert len(a.draws) == draws and ev.validate(a) == []


def test_a_cycle_is_rejected_by_the_helpers_that_need_the_order():
    with pytest.raises(ValueError):
        A.closure_bits(((1,), (0,)))
    with pytest.raises(ValueError):
        A.position_bounds(((1,), (0,)))
