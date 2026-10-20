"""Jede Einheit an den von Hand gerechneten Mini-Plänen (conftest.MINI), DEMO-PLAYBOOK §1b.

Handrechnungen stehen als Kommentar neben dem erwarteten Wert."""

import itertools
import random
from collections import Counter
from fractions import Fraction

import pytest

import zrf_algorithm as A

from conftest import BUDGET, MINI

N_GRAPH = MINI["n_graph"][0]
ALL_N_GRAPH = {(0, 1, 2, 3), (0, 1, 3, 2), (1, 0, 2, 3), (1, 0, 3, 2), (1, 3, 0, 2)}


@pytest.mark.parametrize("name", list(MINI))
def test_extensions_and_ideals_match_the_hand_values(name):
    adj, e, ideals, unique = MINI[name]
    t = A.ideal_table(adj, BUDGET)
    assert t.extensions == e and t.ideals == ideals and A.count_extensions(adj, BUDGET) == e and A.count_ideals(adj, BUDGET) == (ideals, False)
    assert (e == 1) == unique == A.hamilton_path_exists(adj)
    assert t.fwd[(1 << len(adj)) - 1] == e and t.ext[0] == e and sum(len(layer) for layer in t.layers) == ideals


def test_the_ideals_of_the_n_graph_by_hand():
    t = A.ideal_table(N_GRAPH, BUDGET)
    masks = {frozenset(v for v in range(4) if m >> v & 1) for layer in t.layers for m in layer}
    assert masks == {frozenset(s) for s in [(), (0,), (1,), (0, 1), (1, 3), (0, 1, 2), (0, 1, 3), (0, 1, 2, 3)]}
    assert [len(layer) for layer in t.layers] == [1, 2, 2, 2, 1]


def test_the_empty_plan_has_one_empty_order_and_a_single_task_one_order():
    assert A.count_extensions((), BUDGET) == 1 and A.count_extensions(((),), BUDGET) == 1 and A.ideal_table((), BUDGET).ideals == 1


def test_the_budget_stops_the_count_and_reports_it():
    adj = ((),) * 12                                                                               # 2^12 = 4096 Ideale
    assert A.ideal_table(adj, 4096) is not None and A.ideal_table(adj, 4095) is None and A.count_extensions(adj, 100) is None
    total, exceeded = A.count_ideals(adj, 100)
    assert exceeded and total > 100


def test_all_extensions_and_their_limit():
    assert set(A.all_extensions(N_GRAPH, 100)) == ALL_N_GRAPH and len(A.all_extensions(N_GRAPH, 100)) == 5
    assert A.all_extensions(N_GRAPH, 5) is not None and A.all_extensions(N_GRAPH, 4) is None
    assert A.all_extensions(((),) * 4, 23) is None and len(A.all_extensions(((),) * 4, 24)) == 24            # 4! = 24


def test_is_extension_accepts_every_hand_listed_order_and_rejects_wrong_ones():
    assert all(A.is_extension(N_GRAPH, o) for o in ALL_N_GRAPH)
    assert not A.is_extension(N_GRAPH, (0, 2, 1, 3)) and not A.is_extension(N_GRAPH, (0, 1, 2)) and not A.is_extension(N_GRAPH, (0, 1, 2, 2))
    assert not A.is_extension(N_GRAPH, (3, 1, 0, 2))                                               # 3 = d steht vor b = 1


def test_naive_kahn_probabilities_by_hand_on_the_n_graph():
    probs = A.naive_kahn_probabilities(N_GRAPH)
    assert probs == {(0, 1, 2, 3): 0.25, (0, 1, 3, 2): 0.25, (1, 0, 2, 3): 0.125, (1, 0, 3, 2): 0.125, (1, 3, 0, 2): 0.25}   # 0 oder 1 zuerst je 1/2, danach hängt es von der Zahl der verfügbaren ab
    assert sum(probs.values()) == 1 and max(probs.values()) / min(probs.values()) == 2
    assert A.naive_kahn_probabilities(((),) * 5, limit=100) is None and A.naive_kahn_probabilities(N_GRAPH, limit=4) is None


def test_the_uniform_sampler_hits_every_order_about_equally_often():
    t = A.ideal_table(N_GRAPH, BUDGET)
    rng = random.Random(3)
    cnt = Counter(A.sample_uniform(N_GRAPH, t, rng) for _ in range(5000))
    assert set(cnt) == ALL_N_GRAPH and all(abs(c / 5000 - 0.2) < 0.03 for c in cnt.values())


def test_the_naive_kahn_sampler_follows_its_exact_probabilities_not_the_uniform_ones():
    rng = random.Random(4)
    cnt = Counter(A.naive_kahn_order(N_GRAPH, rng) for _ in range(8000))
    probs = A.naive_kahn_probabilities(N_GRAPH)
    assert all(abs(cnt[o] / 8000 - p) < 0.02 for o, p in probs.items()) and cnt[(1, 0, 2, 3)] / 8000 < 0.17    # 1/8 statt 1/5


def test_samples_are_valid_orders_and_the_samplers_are_deterministic():
    adj = MINI["raute"][0]
    t = A.ideal_table(adj, BUDGET)
    assert all(A.is_extension(adj, A.sample_uniform(adj, t, random.Random(s))) for s in range(20))
    assert A.sample_uniform(adj, t, random.Random(5)) == A.sample_uniform(adj, t, random.Random(5)) and A.naive_kahn_order(adj, random.Random(5)) == A.naive_kahn_order(adj, random.Random(5))


def test_randbelow_is_in_range_even_for_huge_bounds_and_uses_all_residues():
    rng = random.Random(1)
    assert all(0 <= A._randbelow(rng, k) < k for k in (1, 2, 7, 10 ** 30) for _ in range(50)) and A._randbelow(rng, 1) == 0
    assert {A._randbelow(rng, 5) for _ in range(200)} == {0, 1, 2, 3, 4}


def test_the_knuth_estimator_is_unbiased_by_exact_expectation():
    """Erwartungswert der Probe = Summe über alle Zufallswege von (Wahrscheinlichkeit mal Produkt) = Zahl der Reihenfolgen, mit Brüchen gerechnet."""
    for name in ("n_graph", "raute", "zwei_ketten", "unabhaengig3"):
        adj, e, *_ = MINI[name]
        pm = A.pred_masks(adj)
        n = len(adj)

        def expect(mask, prod, p):
            if mask == (1 << n) - 1:
                return Fraction(p) * prod
            opts = A._available(pm, mask, n)
            return sum(expect(mask | (1 << v), prod * len(opts), Fraction(p, len(opts))) for v in opts)

        assert expect(0, 1, 1) == e, name


def test_the_knuth_estimate_is_exact_for_a_chain_and_close_for_many_samples():
    chain = MINI["kette3"][0]
    assert A.knuth_samples(chain, random.Random(1), 5) == (1.0,) * 5 and A.knuth_estimate(chain, random.Random(1), 5) == 1.0
    est = A.knuth_estimate(N_GRAPH, random.Random(2), 5000)
    assert abs(est - 5) < 0.3
    assert A.knuth_samples(MINI["unabhaengig3"][0], random.Random(1), 4) == (6.0,) * 4             # 3 * 2 * 1 bei jedem Zufallsweg


def test_the_chain_method_stays_valid_and_does_not_move_a_chain():
    rng = random.Random(1)
    start = A.topological_order(N_GRAPH)
    assert all(A.is_extension(N_GRAPH, A.mcmc_chain(N_GRAPH, start, 50, random.Random(s))) for s in range(30))
    chain = MINI["kette3"][0]
    assert A.mcmc_chain(chain, (0, 1, 2), 100, rng) == (0, 1, 2) and A.mcmc_chain(((),), (0,), 10, rng) == (0,) and A.mcmc_chain(N_GRAPH, start, 0, rng) == tuple(start)


def test_the_chain_method_mixes_to_the_uniform_distribution_on_independent_tasks():
    adj = MINI["unabhaengig3"][0]
    rng = random.Random(6)
    cnt = Counter(A.mcmc_chain(adj, (0, 1, 2), 40, rng) for _ in range(6000))
    assert len(cnt) == 6 and all(abs(c / 6000 - 1 / 6) < 0.025 for c in cnt.values())


def test_position_bounds_by_hand_on_the_n_graph():
    assert A.position_bounds(N_GRAPH) == ((1, 3), (1, 2), (3, 4), (2, 4))
    assert A.position_bounds(MINI["kette3"][0]) == ((1, 1), (2, 2), (3, 3)) and A.position_bounds(((),) * 3) == ((1, 3),) * 3


def test_position_counts_by_hand_on_the_n_graph():
    t = A.ideal_table(N_GRAPH, BUDGET)
    assert A.position_counts(N_GRAPH, t, 2) == [0, 0, 2, 3]                                        # c steht an Stelle 3 (b a c d, a b c d) oder 4 (drei Reihenfolgen)
    assert A.position_counts(N_GRAPH, t, 0) == [2, 2, 1, 0]                                        # a zuerst (zwei Reihenfolgen), an Stelle 2 (b a c d, b a d c), an Stelle 3 (b d a c)
    for v in range(4):
        assert sum(A.position_counts(N_GRAPH, t, v)) == 5


def test_positions_counted_by_the_table_equal_the_positions_of_the_listed_orders():
    t = A.ideal_table(N_GRAPH, BUDGET)
    for v in range(4):
        listed = Counter(o.index(v) for o in ALL_N_GRAPH)
        assert A.position_counts(N_GRAPH, t, v) == [listed[p] for p in range(4)]


def test_before_counts_by_hand_on_the_n_graph():
    t = A.ideal_table(N_GRAPH, BUDGET)
    assert A.before_counts(N_GRAPH, t, 0) == [0, 2, 5, 4]                                          # a vor b: a b c d, a b d c; a vor c: immer; a vor d: nur b d a c fehlt
    for a in range(4):
        listed = [sum(1 for o in ALL_N_GRAPH if o.index(a) < o.index(b)) for b in range(4)]
        assert A.before_counts(N_GRAPH, t, a) == listed


def test_a_relation_between_incomparable_tasks_keeps_exactly_the_before_count():
    """Fügt man a vor b hinzu, bleiben genau before_counts[b] Reihenfolgen übrig (Grundlage der Frage „welche Abhängigkeit schränkt am stärksten ein“)."""
    t = A.ideal_table(N_GRAPH, BUDGET)
    for b, kept in ((1, 2), (3, 4)):
        adj2 = tuple(tuple(sorted(set(N_GRAPH[v]) | ({b} if v == 0 else set()))) for v in range(4))
        assert A.count_extensions(adj2, BUDGET) == A.before_counts(N_GRAPH, t, 0)[b] == kept


def test_hamilton_path_and_unique_order_agree_by_hand():
    assert A.hamilton_path_exists(MINI["kette3"][0]) and A.hamilton_path_exists(MINI["abkuerzung"][0]) and not A.hamilton_path_exists(MINI["raute"][0])
    assert A.hamilton_path_exists(()) and A.hamilton_path_exists(((),))


def test_the_ideal_bound_by_the_chain_cover_by_hand():
    assert A.kuhn_chain_lengths(MINI["zwei_ketten"][0]) == (2, 2) and A.chain_bound(MINI["zwei_ketten"][0]) == 9 == MINI["zwei_ketten"][2]   # Produkt (2 + 1) * (2 + 1)
    assert A.kuhn_chain_lengths(MINI["raute"][0]) == (3, 1) and A.chain_bound(MINI["raute"][0]) == 8 >= MINI["raute"][2]
    assert A.chain_bound(((),) * 3) == 8 and A.chain_bound(MINI["kette3"][0]) == 4


def test_a_cycle_is_rejected_by_the_helpers_that_need_the_order():
    for fn in (A.closure_bits, A.hamilton_path_exists):
        with pytest.raises(ValueError):
            fn(((1,), (0,)))


def test_the_count_equals_the_permutations_that_respect_the_relations_by_enumeration():
    for name, (adj, e, *_rest) in MINI.items():
        n = len(adj)
        ok = sum(1 for p in itertools.permutations(range(n)) if all(p.index(a) < p.index(b) for a in range(n) for b in adj[a]))
        assert ok == e, name


# --- Nachgezogen nach der Mutationsprüfung ----------------------------------------------------------------------------------------------------

class _ConstRandom:
    """Zufallsquelle, die immer 0.5 liefert und die Aufrufe zählt."""

    def __init__(self):
        self.calls = 0

    def random(self):
        self.calls += 1
        return 0.5


def test_randbelow_draws_the_documented_number_of_52_bit_chunks_and_composes_them_exactly():
    for k, calls in ((1 << 51, 2), (1 << 52, 3), ((1 << 104), 4), (10 ** 60, 5)):                  # (Bits + 51) // 52 + 1 Aufrufe
        rng = _ConstRandom()
        A._randbelow(rng, k)
        assert rng.calls == calls, k
    rng = _ConstRandom()
    huge = 10 ** 60                                                                                # 200 Bits: 5 Stücke, kleiner als k, also keine Restbildung
    assert A._randbelow(rng, huge) == sum((1 << 51) << (52 * i) for i in range(5)) % huge


def test_is_extension_checks_the_relations_of_the_last_task_too():
    adj = ((), (), (0,))                                                                           # Aufgabe 2 steht vor Aufgabe 0
    assert not A.is_extension(adj, (0, 1, 2)) and A.is_extension(adj, (2, 0, 1)) and A.is_extension(adj, (1, 2, 0))
