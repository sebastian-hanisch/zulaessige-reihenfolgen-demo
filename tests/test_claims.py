"""Jede Zahl im README (Abschnitt „Befunde“) wird hier über dieselben Experimentfunktionen wie in der App nachgerechnet (DEMO-PLAYBOOK §4).

Mediane über feste Pläne, nie ein einzelner Zufalls-Seed. Zählungen sind exakt; Anteile und Fehler mit Toleranz von einer Einheit der letzten Stelle.
Die Zahlen der Vormessung im Einzelplan (Budget 300 000 Ideale, 10 Pläne je Zelle) weichen bei Budget und Plananzahl ab; maßgeblich sind diese hier (Budget 50 000)."""

import math

import pytest

import zrf_algorithm as A
import zrf_constants as C
import zrf_evaluation as ev

from conftest import MINI, cached


def _by(rows, key=("n", "out")):
    return {tuple(r[k] for k in key): r for r in rows}


def test_ideals_and_orders_are_far_below_the_permutations():
    rows = _by(cached("ideals_vs_permutations_rows"))
    assert [rows[(12, o)]["ideals"] for o in C.E1_OUTS] == [256, 49, 23.5, 17] and [rows[(20, o)]["ideals"] for o in C.E1_OUTS] == [10172, 580.5, 204.5, 81.5]
    assert [round(rows[(20, o)]["log_ext"], 2) for o in C.E1_OUTS] == [13.27, 9.42, 6.99, 5.59] and [round(rows[(12, o)]["log_ext"], 2) for o in C.E1_OUTS] == [5.61, 3.32, 1.97, 0.98]
    assert round(rows[(20, 2.0)]["log_fact"], 2) == round(math.log10(math.factorial(20)), 2) == 18.39 and all(r["over"] == 0 and r["instances"] == 10 for r in rows.values())


def test_sparse_plans_overflow_the_budget():
    rows = _by(cached("ideals_vs_density_rows"))
    assert {r["instances"] for r in rows.values()} == {8}
    assert [rows[(20, o)]["ideals"] for o in C.E2_OUTS] == [12236, 635.5, 229.5, 97.5] and [rows[(20, o)]["over"] for o in C.E2_OUTS] == [0, 0, 0, 0]
    assert [rows[(30, o)]["over"] for o in C.E2_OUTS] == [8, 0, 0, 0] and [rows[(30, o)]["ideals"] for o in C.E2_OUTS] == [None, 17346, 1994.5, 547]
    assert [rows[(40, o)]["over"] for o in C.E2_OUTS] == [8, 7, 1, 0] and rows[(40, 4.0)]["ideals"] == 2326 and rows[(40, 3.0)]["ideals"] == 9024


def test_the_bound_by_the_chain_cover_always_holds():
    rows = cached("bound_rows")
    assert [(r["n"], r["out"], r["instances"], r["holds"]) for r in rows] == [(20, o, 30, 30) for o in C.E3_OUTS]
    assert [round(r["ratio"], 1) for r in rows] == [4.0, 9.7, 14.3, 11.6]


def test_the_naive_kahn_is_far_from_uniform():
    row = cached("naive_rows")
    assert row["instances"] == 20 and row["ratio_median"] == 102 and row["ratio_max"] == pytest.approx(432.0) and row["tv_median"] == pytest.approx(0.395, abs=0.001)


def test_the_estimator_is_close_but_scatters():
    rows = _by(cached("estimator_rows"), ("n",))
    assert [(rows[(n,)]["instances"]) for n in C.E5_NS] == [20, 20, 20]
    assert [round(rows[(n,)]["err_median"], 3) for n in C.E5_NS] == [0.034, 0.08, 0.108] and [round(rows[(n,)]["err_max"], 3) for n in C.E5_NS] == [0.265, 0.243, 0.552]


def test_the_chain_method_mixes_after_about_a_hundred_steps_on_seven_tasks():
    rows = cached("mixing_rows")
    assert [r["steps"] for r in rows] == list(C.E6_STEPS) and {r["extensions"] for r in rows} == {18} and {r["runs"] for r in rows} == {3000}
    assert [r["tv"] for r in rows] == pytest.approx([0.637, 0.441, 0.235, 0.074, 0.03, 0.038], abs=0.001)


def test_a_unique_order_is_exactly_a_hamilton_path():
    row = cached("unique_rows")
    assert (row["instances"], row["agree"], row["unique"]) == (400, 400, 226)


def test_the_room_of_a_task_falls_with_the_density():
    rows = _by(cached("spread_rows"), ("out",))
    assert [rows[(o,)]["median"] for o in C.E8_OUTS] == [16, 10, 6, 4] and [round(rows[(o,)]["mean"], 2) for o in C.E8_OUTS] == [15.64, 10.35, 6.36, 4.24] and [rows[(o,)]["max"] for o in C.E8_OUTS] == [19, 19, 17, 13]


def test_verdict_texts_quote_the_readme_numbers():
    assert "im Median 580,5 Ideale und 10^9,4 zulässige Reihenfolgen gegen 10^18,4 Permutationen" in ev.verdict_permutations(cached("ideals_vs_permutations_rows"))[1]
    text = ev.verdict_density(cached("ideals_vs_density_rows"))[1]
    assert "im Median 547 bei Ausgangsgrad 4, über dem Budget von 50.000 in 8 von 8 Plänen bei Grad 1" in text and "Grad 1: 8 von 8; Grad 2: 7 von 8; Grad 3: 1 von 8; Grad 4: 0 von 8" in text
    assert "120 von 120 Plänen" in ev.verdict_bound(cached("bound_rows"))[1] and "das 4,0- bis 14,3-Fache" in ev.verdict_bound(cached("bound_rows"))[1]
    assert "im Median das 102-Fache" in ev.verdict_naive(cached("naive_rows"))[1] and "höchstens das 432-Fache" in ev.verdict_naive(cached("naive_rows"))[1]
    assert "12 Aufgaben: 3 % im Median, höchstens 27 %; 16 Aufgaben: 8 % im Median, höchstens 24 %; 20 Aufgaben: 11 % im Median, höchstens 55 %" in ev.verdict_estimator(cached("estimator_rows"))[1]
    assert "bei 0,64 / 0,44 / 0,23 / 0,07 / 0,03 / 0,04" in ev.verdict_mixing(cached("mixing_rows"))[1] and "erstmals nach 100 Schritten" in ev.verdict_mixing(cached("mixing_rows"))[1]
    assert "in 226 Fällen eindeutig" in ev.verdict_unique(cached("unique_rows"))[1] and "im Median 16 / 10 / 6 / 4 Plätze" in ev.verdict_spread(cached("spread_rows"))[1]


def test_the_hand_computed_mini_plans_are_the_documented_ones():
    """N-Graph: 5 Reihenfolgen und 8 Ideale; zwei Ketten der Länge 2: C(4, 2) = 6 Reihenfolgen und 3 * 3 Ideale; Abkürzung ändert nichts."""
    assert A.count_extensions(MINI["n_graph"][0], 50000) == 5 and A.ideal_table(MINI["n_graph"][0], 50000).ideals == 8
    assert A.count_extensions(MINI["zwei_ketten"][0], 50000) == 6 == math.comb(4, 2) and A.ideal_table(MINI["zwei_ketten"][0], 50000).ideals == 9
    assert A.count_extensions(MINI["abkuerzung"][0], 50000) == A.count_extensions(MINI["kette3"][0], 50000) == 1


def test_the_slider_maximum_has_the_documented_edge_count_and_budget():
    from zrf_scenario import edge_count
    assert edge_count(C.N_MAX, C.OUT_MAX) == 160 and C.IDEAL_BUDGET == 50000
