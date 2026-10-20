"""Zweige der Hauptansicht (Nullspalte-Lehre): Jeder Weg, den die App zeigt, kommt in mindestens einem Preset oder einer festen Instanz vor.

Ein Preset, das seine Beschreibung nicht einlöst (z. B. „Eine einzige Reihenfolge“ mit zwei Reihenfolgen), fällt hier auf."""

import math

import pytest

import zrf_algorithm as A
import zrf_constants as C
import zrf_evaluation as ev


def _a(name):
    return ev.analyse(ev.Settings(**C.PRESETS[name]))


def test_lehrbeispiel_is_counted_exactly_and_drawn_uniformly():
    a = _a("Lehrbeispiel (12 Aufgaben)")
    assert a.n == 12 and a.extensions == 2240 and not a.exceeded and a.sampler_used == "uniform" and not a.fallback and a.ideals < 100 and ev.verdict_question(a)[0] == "info"


def test_a_single_order_has_no_room_to_move():
    a = _a("Eine einzige Reihenfolge")
    assert a.extensions == 1 and a.unique and a.hamilton and a.spread_median == 0 and all(lo == hi for lo, hi in a.bounds) and "eindeutig" in ev.verdict_question(a)[1]


def test_an_almost_unconstrained_plan_has_trillions_of_orders_and_wide_room():
    a = _a("Fast alles ist möglich")
    assert a.extensions > 10 ** 12 and not a.exceeded and a.spread_median >= 15 and a.log_ext > a.log_fact - 4


def test_ideals_instead_of_permutations_in_its_preset():
    a = _a("Ideale statt Permutationen")
    assert a.n == 20 and a.ideals < 5000 and a.extensions > 10 ** 10 and a.ideals * 10 ** 6 < math.factorial(20)


def test_too_many_ideals_fall_back_to_the_naive_sampler_and_the_estimator():
    a = _a("Zu viele Ideale")
    assert a.exceeded and a.extensions is None and a.table is None and a.ideals > C.IDEAL_BUDGET and a.fallback and a.sampler_used == "naive" and a.estimate > 10 ** 20
    kind, text = ev.verdict_question(a)
    assert kind == "warning" and "mehr als 50.000 Ideale" in text and a.settings.sampler == "uniform"


def test_the_naive_kahn_is_far_from_uniform_in_its_preset():
    a = _a("Der Zufalls-Kahn ist verzerrt")
    assert a.sampler_used == "naive" and a.naive_ratio >= 100 and sum(a.naive_probs.values()) == pytest.approx(1.0)
    positions = [ev.tv_distance(d["exact"], d["sampled"]) for d in (ev.position_distribution(a, v) for v in range(a.n))]
    assert max(positions) > 0.2


def test_a_chain_with_too_few_steps_is_far_from_uniform_in_its_preset():
    a = _a("Die Kette mischt langsam")
    assert a.sampler_used == "chain" and a.settings.steps == 10 and a.settings.draws == 5000
    positions = [ev.tv_distance(d["exact"], d["sampled"]) for d in (ev.position_distribution(a, v) for v in range(a.n))]
    assert max(positions) > 0.3
    uniform = ev.analyse(ev.Settings(**{**C.PRESETS["Die Kette mischt langsam"], "sampler": "uniform"}))
    assert max(ev.tv_distance(d["exact"], d["sampled"]) for d in (ev.position_distribution(uniform, v) for v in range(uniform.n))) < 0.1


def test_a_long_chain_reaches_the_uniform_distribution_on_the_same_plan():
    a = ev.analyse(ev.Settings(**{**C.PRESETS["Die Kette mischt langsam"], "steps": 300}))
    assert max(ev.tv_distance(d["exact"], d["sampled"]) for d in (ev.position_distribution(a, v) for v in range(a.n))) < 0.15


def test_the_chosen_sampler_is_respected_when_the_table_exists():
    for sampler in C.SAMPLERS:
        a = ev.analyse(ev.Settings(10, 2.0, 3, sampler, 200, 50))
        assert a.sampler_used == sampler and not a.fallback and len(a.draws) == 200 and all(A.is_extension(a.adj, o) for o in a.draws)


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_every_preset_passes_the_validation(name):
    assert ev.validate(_a(name)) == []
