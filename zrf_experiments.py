"""Experimente über feste Pläne (nie ein einzelner Zufalls-Seed): Mediane und Zählungen über `SEEDS`. Aufwand in Idealen und Schritten, nicht in Sekunden.

Jede Funktion gibt Zeilen (Wörterbücher) zurück, die die Abbildungen und die Verdikte in `zrf_evaluation` lesen; dieselben Funktionen rechnen die Zahlen im README (tests/test_claims.py)."""

import math
import random
from collections import Counter
from statistics import median

import zrf_algorithm as A
import zrf_constants as C
import zrf_scenario as S


def _plan(n, out, seed):
    return S.make_instance(n, out, 0, seed).adj


def ideal_rows(ns, outs, seeds, budget=C.IDEAL_BUDGET) -> list[dict]:
    """Zahl der Ideale und der Reihenfolgen je Größe und Dichte (Median über die Pläne unter dem Budget), dazu die Zahl der Pläne über dem Budget und log10 n!."""
    rows = []
    for n in ns:
        for out in outs:
            ideals, logs, over = [], [], 0
            for s in seeds:
                t = A.ideal_table(_plan(n, out, s), budget)
                if t is None:
                    over += 1
                else:
                    ideals.append(t.ideals)
                    logs.append(math.log10(t.extensions))
            rows.append({"n": n, "out": out, "instances": len(seeds), "over": over, "ideals": median(ideals) if ideals else None,
                         "log_ext": median(logs) if logs else None, "log_fact": math.log10(math.factorial(n))})
    return rows


def ideals_vs_permutations_rows() -> list[dict]:
    """E1: Ideale und Reihenfolgen gegen n! für kleine Pläne (alle unter dem Budget)."""
    return ideal_rows(C.E1_NS, C.E1_OUTS, C.E1_SEEDS)


def ideals_vs_density_rows() -> list[dict]:
    """E2: Zahl der Ideale über Größe und Dichte, mit der Zahl der Pläne über dem Budget."""
    return ideal_rows(C.E2_NS, C.E2_OUTS, C.E2_SEEDS)


def bound_rows() -> list[dict]:
    """E3: Zahl der Ideale gegen die Schranke aus der Kettenzerlegung (Produkt der Kettenlängen + 1), 30 Pläne je Dichte."""
    rows = []
    for out in C.E3_OUTS:
        holds, ratios = 0, []
        for s in C.E3_SEEDS:
            adj = _plan(C.E3_N, out, s)
            ideals = A.ideal_table(adj, C.IDEAL_BUDGET).ideals
            bound = A.chain_bound(adj)
            holds += ideals <= bound
            ratios.append(bound / ideals)
        rows.append({"n": C.E3_N, "out": out, "instances": len(C.E3_SEEDS), "holds": holds, "ratio": median(ratios)})
    return rows


def naive_rows() -> dict:
    """E4: Verzerrung des naiven Zufalls-Kahn: Verhältnis der wahrscheinlichsten zur unwahrscheinlichsten Reihenfolge und Totalvariation zur Gleichverteilung (Median)."""
    ratios, tvs = [], []
    for s in C.E4_SEEDS:
        adj = _plan(C.E4_N, C.E4_OUT, s)
        e = A.count_extensions(adj, C.IDEAL_BUDGET)
        if not C.E4_RANGE[0] <= e <= C.E4_RANGE[1]:
            continue
        probs = A.naive_kahn_probabilities(adj, C.NAIVE_LIMIT)
        ratios.append(max(probs.values()) / min(probs.values()))
        tvs.append(0.5 * sum(abs(p - 1 / e) for p in probs.values()))
    return {"n": C.E4_N, "out": C.E4_OUT, "instances": len(ratios), "ratio_median": median(ratios), "ratio_max": max(ratios), "tv_median": median(tvs)}


def estimator_rows() -> list[dict]:
    """E5: relativer Fehler des Schätzers (1 000 Proben) gegen die exakte Zahl (Median und Maximum über die Pläne)."""
    rows = []
    for n in C.E5_NS:
        errs = []
        for s in C.E5_SEEDS:
            adj = _plan(n, C.E5_OUT, s)
            e = A.count_extensions(adj, C.IDEAL_BUDGET)
            if e is None:
                continue
            est = A.knuth_estimate(adj, random.Random(s), C.ESTIMATE_SAMPLES)
            errs.append(abs(est - e) / e)
        rows.append({"n": n, "out": C.E5_OUT, "instances": len(errs), "err_median": median(errs), "err_max": max(errs)})
    return rows


def mixing_rows() -> list[dict]:
    """E6: Totalvariationsabstand des Kettenverfahrens zur Gleichverteilung nach t Schritten, an einem Plan mit wenigen Reihenfolgen (feste Zufallsquelle)."""
    adj = _plan(C.E6_N, C.E6_OUT, C.E6_SEED)
    e = A.count_extensions(adj, C.IDEAL_BUDGET)
    start = tuple(A.topological_order(adj))
    rng = random.Random(C.E6_SEED)
    rows = []
    for steps in C.E6_STEPS:
        cnt = Counter(A.mcmc_chain(adj, start, steps, rng) for _ in range(C.E6_RUNS))
        tv = 0.5 * (sum(abs(c / C.E6_RUNS - 1 / e) for c in cnt.values()) + (e - len(cnt)) / e)
        rows.append({"n": C.E6_N, "extensions": e, "steps": steps, "runs": C.E6_RUNS, "tv": tv})
    return rows


def unique_rows() -> dict:
    """E7: eindeutige Ordnung gegen Hamilton-Pfad der Beziehungen über viele kleine Pläne."""
    agree = unique = 0
    for k in range(C.E7_PLANS):
        n = C.E7_NMIN + k % C.E7_NSPAN
        adj = _plan(n, (1.0, 2.0, 3.0, 4.0)[k % 4], 8500 + k)
        e = A.count_extensions(adj, C.IDEAL_BUDGET)
        agree += (e == 1) == A.hamilton_path_exists(adj)
        unique += e == 1
    return {"instances": C.E7_PLANS, "agree": agree, "unique": unique}


def spread_rows() -> list[dict]:
    """E8: Spielraum je Aufgabe (späteste minus früheste mögliche Stelle) über Plan und Dichte (Median, Mittel, Maximum über alle Aufgaben aller Pläne)."""
    rows = []
    for out in C.E8_OUTS:
        spreads = []
        for s in C.E8_SEEDS:
            for lo, hi in A.position_bounds(_plan(C.E8_N, out, s)):
                spreads.append(hi - lo)
        rows.append({"n": C.E8_N, "out": out, "instances": len(C.E8_SEEDS), "median": median(spreads), "mean": sum(spreads) / len(spreads), "max": max(spreads)})
    return rows
