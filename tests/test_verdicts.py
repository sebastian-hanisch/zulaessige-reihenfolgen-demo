"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Zahl im Text und jede Schwelle der Art steht hier.

Ein Verdikt ist eine reine Funktion (Art, Text) und bekommt Zeilen, nicht Seeds; ohne diese Datei überleben fast alle Mutanten der Verdikt-Arithmetik."""

import zrf_evaluation as ev
import zrf_scenario as S

from conftest import MINI


def _analysis(name, **kw):
    adj = MINI[name][0]
    inst = S.Instance(tuple(tuple(w) for w in adj), tuple(range(len(adj))), frozenset())
    return ev.analyse_instance(inst, ev.Settings(n=len(adj), draws=20, **kw))


# --- Kernfrage ---------------------------------------------------------------------------------------------------------------------------

def test_question_names_the_count_the_ideals_the_room_and_the_naive_distortion():
    kind, text = ev.verdict_question(_analysis("n_graph"))
    assert kind == "info"
    assert "**Der Plan erlaubt 5 zulässige Reihenfolgen** von 24 Permutationen (10^0,7 gegen 10^1,4); die Zählung brauchte 8 Ideale statt 24 Permutationen." in text
    assert "Zwischen der frühesten und der spätesten möglichen Stelle einer Aufgabe liegen im Median 1,5 Plätze." in text
    assert "Der naive Zufalls-Kahn zieht die wahrscheinlichste Reihenfolge 2-mal so oft wie die unwahrscheinlichste, das Ziehen über die Zähltabelle trifft jede gleich oft." in text


def test_question_for_a_unique_order_names_the_hamilton_path_and_omits_the_naive_sentence():
    kind, text = ev.verdict_question(_analysis("kette3"))
    assert kind == "info" and "**Der Plan erlaubt 1 zulässige Reihenfolgen**" in text and "Die Reihenfolge ist **eindeutig**: je zwei aufeinanderfolgende Aufgaben hängen unmittelbar zusammen (Hamilton-Pfad), es gibt keinen Spielraum." in text
    assert "naive" not in text and "Zwischen der frühesten" not in text


def test_question_over_the_budget_is_a_warning_with_the_estimate():
    inst = S.Instance(((),) * 17, tuple(range(17)), frozenset())
    a = ev.analyse_instance(inst, ev.Settings(n=17, draws=10))
    kind, text = ev.verdict_question(a)
    assert kind == "warning"
    assert "**Der Plan hat mehr als 50.000 Ideale**: Die exakte Zählung bricht ab (Zählen ist #P-vollständig)." in text
    assert "Der Schätzer kommt auf etwa 355.687.428.096.000 zulässige Reihenfolgen (relativer Standardfehler etwa 0 %) von 355.687.428.096.000 Permutationen; das gleichverteilte Ziehen ist hier nicht möglich." in text


def test_the_empty_plan_has_a_defined_verdict():
    a = ev.analyse_instance(S.Instance((), (), frozenset()), ev.Settings(n=0, draws=1))
    assert ev.verdict_question(a) == ("info", "Der Plan ist leer.")


# --- E1 ---------------------------------------------------------------------------------------------------------------------------------

def _r(n, out, ideals, log_ext, log_fact, over=0):
    return {"n": n, "out": out, "instances": 10, "over": over, "ideals": ideals, "log_ext": log_ext, "log_fact": log_fact}


def test_permutations_names_the_largest_size_at_degree_two():
    rows = [_r(12, 2.0, 49.0, 3.32, 8.68), _r(20, 2.0, 580.5, 9.42, 18.39), _r(20, 1.0, 10172.0, 13.27, 18.39)]
    kind, text = ev.verdict_permutations(rows)
    assert kind == "info"
    assert "Bei 20 Aufgaben und Ausgangsgrad 2 hat der Plan im Median 580,5 Ideale und 10^9,4 zulässige Reihenfolgen gegen 10^18,4 Permutationen. Die DP zählt über die Ideale, nicht über die Permutationen." in text
    assert ev.verdict_permutations([_r(12, 2.0, 10 ** 9, 3.3, 8.7)])[0] == "warning" and ev.verdict_permutations([_r(12, 2.0, 49.0, 9.0, 8.7)])[0] == "warning"


# --- E2 ---------------------------------------------------------------------------------------------------------------------------------

def _d(n, out, ideals, over, log_ext=10.0):
    return {"n": n, "out": out, "instances": 8, "over": over, "ideals": ideals, "log_ext": log_ext, "log_fact": 30.0}


def test_density_names_the_middle_size_and_the_budget_cases_of_the_largest():
    rows = [_d(20, 1.0, 12236.0, 0), _d(20, 4.0, 97.5, 0), _d(30, 1.0, None, 8), _d(30, 4.0, 547.0, 0), _d(40, 1.0, None, 8), _d(40, 4.0, 2326.0, 0)]
    kind, text = ev.verdict_density(rows)
    assert kind == "info"
    assert ("Bei 30 Aufgaben wächst die Zahl der Ideale mit der Dünnheit des Plans: im Median 547 bei Ausgangsgrad 4, über dem Budget von 50.000 in 8 von 8 Plänen bei Grad 1. "
            "Bei 40 Aufgaben liegen über dem Budget: Grad 1: 8 von 8; Grad 4: 0 von 8.") in text


def test_density_without_a_budget_overflow_names_the_sparse_count_and_warns():
    rows = [_d(20, 1.0, 100.0, 0), _d(30, 1.0, 1000.0, 0), _d(30, 4.0, 547.0, 0), _d(40, 1.0, 2000.0, 0)]
    kind, text = ev.verdict_density(rows)
    assert kind == "warning" and "im Median 547 bei Ausgangsgrad 4, 1.000 bei Grad 1. Bei 40 Aufgaben" in text


# --- E3 ---------------------------------------------------------------------------------------------------------------------------------

def _b(out, holds, ratio):
    return {"n": 20, "out": out, "instances": 30, "holds": holds, "ratio": ratio}


def test_bound_counts_the_plans_where_it_holds_and_names_the_range_of_the_ratio():
    rows = [_b(1.0, 30, 4.004), _b(2.0, 30, 9.656), _b(3.0, 30, 14.257), _b(4.0, 30, 11.566)]
    kind, text = ev.verdict_bound(rows)
    assert kind == "info" and "liegt in 120 von 120 Plänen unter dem Produkt der (Kettenlänge + 1)" in text and "das 4,0- bis 14,3-Fache der tatsächlichen Zahl" in text
    assert ev.verdict_bound([_b(1.0, 29, 4.0), _b(2.0, 30, 5.0)])[0] == "warning"


# --- E4 ---------------------------------------------------------------------------------------------------------------------------------

def test_naive_names_the_ratios_and_the_distance():
    row = {"n": 9, "out": 1.5, "instances": 20, "ratio_median": 102.0, "ratio_max": 432.0, "tv_median": 0.4942}
    kind, text = ev.verdict_naive(row)
    assert kind == "info"
    assert "im Median das 102-Fache der unwahrscheinlichsten (höchstens das 432-Fache); der Abstand zur Gleichverteilung (Totalvariation) beträgt im Median 0,49." in text
    assert ev.verdict_naive({**row, "ratio_median": 1.0})[0] == "warning"


# --- E5 ---------------------------------------------------------------------------------------------------------------------------------

def _e(n, med, mx):
    return {"n": n, "out": 1.5, "instances": 20, "err_median": med, "err_max": mx}


def test_estimator_names_the_errors_per_size():
    rows = [_e(12, 0.034, 0.266), _e(16, 0.08, 0.243), _e(20, 0.108, 0.552)]
    kind, text = ev.verdict_estimator(rows)
    assert kind == "info"
    assert "12 Aufgaben: 3 % im Median, höchstens 27 %; 16 Aufgaben: 8 % im Median, höchstens 24 %; 20 Aufgaben: 11 % im Median, höchstens 55 %" in text and "1.000 Proben" in text
    assert ev.verdict_estimator([_e(12, 0.5, 0.9)])[0] == "warning"


# --- E6 ---------------------------------------------------------------------------------------------------------------------------------

def _m(steps, tv):
    return {"n": 7, "extensions": 18, "steps": steps, "runs": 3000, "tv": tv}


def test_mixing_names_the_distances_and_the_first_step_count_below_a_tenth():
    rows = [_m(7, 0.637), _m(20, 0.441), _m(49, 0.236), _m(100, 0.074), _m(200, 0.03), _m(400, 0.038)]
    kind, text = ev.verdict_mixing(rows)
    assert kind == "info"
    assert ("Bei 7 Aufgaben und 18 Reihenfolgen liegt der Abstand des Kettenverfahrens zur Gleichverteilung nach 7 / 20 / 49 / 100 / 200 / 400 Schritten bei 0,64 / 0,44 / 0,24 / 0,07 / 0,03 / 0,04 "
            "(Totalvariation, 3.000 Läufe je Schrittzahl). Unter 0,1 ist er erstmals nach 100 Schritten.") in text
    kind2, text2 = ev.verdict_mixing([_m(7, 0.6), _m(20, 0.4)])
    assert kind2 == "warning" and "Unter 0,1 kommt er in diesem Raster nicht." in text2
    assert ev.verdict_mixing([_m(7, 0.1), _m(20, 0.6)])[0] == "warning"


# --- E7 / E8 ----------------------------------------------------------------------------------------------------------------------------

def test_unique_names_the_counts_and_the_agreement():
    row = {"instances": 400, "agree": 400, "unique": 226}
    kind, text = ev.verdict_unique(row)
    assert kind == "info" and "Auf 400 kleinen Plänen ist die Ordnung in 226 Fällen eindeutig;" in text and "stimmt in 400 von 400 Fällen." in text
    assert ev.verdict_unique({**row, "agree": 399})[0] == "warning" and ev.verdict_unique({**row, "unique": 0})[0] == "warning"


def _s(out, med, mean, mx):
    return {"n": 20, "out": out, "instances": 20, "median": med, "mean": mean, "max": mx}


def test_spread_names_the_medians_over_the_densities_and_the_largest_room():
    rows = [_s(4.0, 4.0, 4.24, 13), _s(1.0, 16.0, 15.6, 19), _s(2.0, 10.0, 10.3, 19), _s(3.0, 6.0, 6.4, 17)]
    kind, text = ev.verdict_spread(rows)
    assert kind == "info"
    assert "Bei 20 Aufgaben liegen zwischen der frühesten und der spätesten möglichen Stelle einer Aufgabe im Median 16 / 10 / 6 / 4 Plätze (Ausgangsgrad 1 / 2 / 3 / 4); der größte Spielraum einer einzelnen Aufgabe beträgt 19 Plätze." in text
    assert ev.verdict_spread([_s(1.0, 3.0, 3.0, 5), _s(4.0, 9.0, 9.0, 11)])[0] == "warning"
