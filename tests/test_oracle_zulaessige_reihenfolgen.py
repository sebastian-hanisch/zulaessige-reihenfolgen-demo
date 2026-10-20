"""Orakel-Test zulaessige-reihenfolgen-demo: Zahl, Aufzählung, Positionen und Wahrscheinlichkeiten gegen networkx und Brute Force (DEMO-PLAYBOOK §12).

Unabhängige Rechenwege: `networkx.all_topological_sorts` (Aufzählung aller zulässigen Reihenfolgen), Aufzählung aller Permutationen und Teilmengen (kleine Pläne), die Definition
„Ideal = unter Vorgängern abgeschlossen“. Feste Instanzen (range, kein Zufall), zusammen unter 20 Sekunden."""

import itertools
import random
from collections import Counter

import pytest

import zrf_algorithm as A
import zrf_scenario as S

from conftest import BUDGET

nx = pytest.importorskip("networkx")


def _plans(count=100, nmin=5, nspan=5, base=800, outs=(0.5, 1.0, 2.0)):
    for k in range(count):
        n = nmin + k % nspan
        yield S.make_instance(n, outs[k % len(outs)], 0, base + k).adj


def _nx_orders(adj):
    g = nx.DiGraph()
    g.add_nodes_from(range(len(adj)))
    g.add_edges_from((a, b) for a in range(len(adj)) for b in adj[a])
    return {tuple(o) for o in nx.all_topological_sorts(g)}


def test_the_count_equals_the_orders_networkx_lists():
    for adj in _plans():
        assert A.count_extensions(adj, BUDGET) == len(_nx_orders(adj)), adj


def test_the_enumeration_equals_the_orders_networkx_lists():
    for adj in _plans(60):
        assert set(A.all_extensions(adj, 10 ** 6)) == _nx_orders(adj)


def test_the_count_equals_the_permutations_that_respect_the_relations():
    for adj in _plans(40, 4, 4):
        n = len(adj)
        ok = sum(1 for p in itertools.permutations(range(n)) if all(p.index(a) < p.index(b) for a in range(n) for b in adj[a]))
        assert A.count_extensions(adj, BUDGET) == ok


def test_the_ideals_equal_the_subsets_closed_under_predecessors():
    for adj in _plans(60, 4, 7):
        n = len(adj)
        pm = A.pred_masks(adj)
        brute = sum(1 for mask in range(1 << n) if all((pm[v] & ~mask) == 0 for v in range(n) if (mask >> v) & 1))
        assert A.ideal_table(adj, BUDGET).ideals == brute == A.count_ideals(adj, BUDGET)[0]


def test_positions_and_before_counts_equal_the_listed_orders():
    for adj in _plans(40, 5, 4):
        orders = _nx_orders(adj)
        t = A.ideal_table(adj, BUDGET)
        n = len(adj)
        for v in range(n):
            listed = Counter(o.index(v) for o in orders)
            assert A.position_counts(adj, t, v) == [listed[p] for p in range(n)]
            assert A.before_counts(adj, t, v) == [sum(1 for o in orders if o.index(v) < o.index(b)) for b in range(n)]


def test_the_position_bounds_are_the_smallest_and_largest_positions_over_all_orders():
    for adj in _plans(60, 5, 5):
        orders = _nx_orders(adj)
        bounds = A.position_bounds(adj)
        for v in range(len(adj)):
            places = [o.index(v) + 1 for o in orders]
            assert bounds[v] == (min(places), max(places)), (adj, v)


def test_the_uniform_sampler_is_uniform_and_the_naive_one_is_not():
    rng = random.Random(9)
    checked = 0
    for adj in _plans(60, 6, 4, base=900, outs=(1.0, 1.5)):
        orders = _nx_orders(adj)
        e = len(orders)
        if not 6 <= e <= 40:
            continue
        t = A.ideal_table(adj, BUDGET)
        draws = 400 * e
        cnt = Counter(A.sample_uniform(adj, t, rng) for _ in range(draws))
        assert set(cnt) == orders and max(abs(c / draws - 1 / e) * e for c in cnt.values()) < 0.3
        probs = A.naive_kahn_probabilities(adj)
        assert abs(sum(probs.values()) - 1) < 1e-9 and set(probs) == orders
        checked += 1
    assert checked >= 5


def test_the_naive_sampler_is_not_uniform_in_a_clear_majority_of_plans_with_many_orders():
    skewed = total = 0
    for adj in _plans(60, 7, 3, base=1000, outs=(1.0, 1.5)):
        probs = A.naive_kahn_probabilities(adj, limit=3000)
        if probs and len(probs) >= 10:
            total += 1
            skewed += max(probs.values()) / min(probs.values()) > 2
    assert total >= 15 and skewed >= 0.8 * total


def test_a_unique_order_is_exactly_a_hamilton_path_of_relations():
    unique = 0
    for adj in _plans(300, 4, 6, base=1200, outs=(1.0, 2.0, 3.0, 4.0)):
        e = A.count_extensions(adj, BUDGET)
        assert (e == 1) == A.hamilton_path_exists(adj)
        unique += e == 1
    assert unique >= 20                                                                            # der Fall kommt in den Plänen vor, sonst wäre die Prüfung leer


def test_the_ideal_count_never_exceeds_the_bound_by_a_smallest_chain_cover():
    for adj in _plans(80, 6, 10, base=1500, outs=(1.0, 2.0, 3.0)):
        assert A.ideal_table(adj, BUDGET).ideals <= A.chain_bound(adj)


def test_the_count_does_not_depend_on_the_numbering_of_the_tasks():
    rng = random.Random(5)
    for adj in _plans(50, 5, 6, base=1600):
        n = len(adj)
        perm = list(range(n))
        rng.shuffle(perm)
        renamed = [[] for _ in range(n)]
        for a in range(n):
            for b in adj[a]:
                renamed[perm[a]].append(perm[b])
        renamed = tuple(tuple(sorted(w)) for w in renamed)
        assert A.count_extensions(renamed, BUDGET) == A.count_extensions(adj, BUDGET) and A.ideal_table(renamed, BUDGET).ideals == A.ideal_table(adj, BUDGET).ideals


def test_a_redundant_relation_changes_nothing_and_a_new_relation_between_incomparable_tasks_removes_orders():
    for adj in _plans(60, 5, 5, base=1700):
        n = len(adj)
        reach = A.closure_bits(adj)
        e = A.count_extensions(adj, BUDGET)
        for a in range(n):
            for b in range(n):
                if a == b:
                    continue
                adj2 = tuple(tuple(sorted(set(adj[v]) | ({b} if v == a else set()))) for v in range(n))
                if (reach[a] >> b) & 1 and b not in adj[a]:
                    assert A.count_extensions(adj2, BUDGET) == e                                   # Abkürzung: schon über einen Umweg verlangt
                elif not (reach[a] >> b) & 1 and not (reach[b] >> a) & 1:
                    assert A.count_extensions(adj2, BUDGET) < e


def test_the_estimator_is_close_to_the_count_on_average():
    for adj in _plans(6, 10, 3, base=1800, outs=(1.5,)):
        e = A.count_extensions(adj, BUDGET)
        est = A.knuth_estimate(adj, random.Random(3), 20000)
        assert abs(est - e) / e < 0.15, (e, est)


def test_the_chain_method_reaches_the_uniform_distribution_on_a_small_plan():
    adj = S.make_instance(7, 1.0, 0, 8700).adj
    orders = _nx_orders(adj)
    e = len(orders)
    start = tuple(A.topological_order(adj))
    rng = random.Random(7)
    runs = 3000
    cnt = Counter(A.mcmc_chain(adj, start, 300, rng) for _ in range(runs))
    assert set(cnt) <= orders
    tv = 0.5 * (sum(abs(c / runs - 1 / e) for c in cnt.values()) + (e - len(cnt)) / e)
    assert e == 18 and tv < 0.08
