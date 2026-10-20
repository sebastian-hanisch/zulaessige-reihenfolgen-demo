"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, Permalink-Spezifikationen."""

import zrf_constants as C
import zrf_evaluation as ev
import zrf_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_slider_bounds_and_choices():
    for name, p in C.PRESETS.items():
        assert C.N_MIN <= p["n"] <= C.N_MAX, name
        assert C.OUT_MIN <= p["out"] <= C.OUT_MAX and abs(p["out"] / C.OUT_STEP - round(p["out"] / C.OUT_STEP)) < 1e-9, name   # auf dem Reglerraster
        assert 0 <= p["seed"] <= C.SEED_MAX and p["sampler"] in C.SAMPLERS and p["draws"] in C.DRAWS and p["steps"] in C.STEPS, name


def test_default_preset_equals_the_default_settings():
    first = next(iter(C.PRESETS.values()))
    assert ev.Settings(**first) == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_choice_specs_name_their_allowed_values_and_the_steps_snap_permalink_values():
    assert P.SETTING_SPECS["sampler_select"].choices == C.SAMPLERS and P.SETTING_SPECS["draws_select"].choices == C.DRAWS and P.SETTING_SPECS["steps_select"].choices == C.STEPS
    assert set(C.SAMPLER_NAMES) == set(C.SAMPLERS) and C.DEFAULT_SAMPLER in C.SAMPLERS and C.DEFAULT_DRAWS in C.DRAWS and C.DEFAULT_STEPS in C.STEPS
    assert list(C.DRAWS) == sorted(C.DRAWS) and list(C.STEPS) == sorted(C.STEPS) and P.SETTING_SPECS["out_slider"].step == C.OUT_STEP


def test_every_sampler_is_used_by_some_preset():
    assert {p["sampler"] for p in C.PRESETS.values()} == set(C.SAMPLERS)


def test_the_raster_of_the_experiments_stays_inside_the_slider_bounds():
    for ns in (C.E1_NS, C.E2_NS, C.E5_NS):
        assert all(C.N_MIN <= n <= C.N_MAX for n in ns)
    assert C.N_MIN <= C.E3_N <= C.N_MAX and C.N_MIN <= C.E4_N <= C.N_MAX and C.N_MIN <= C.E6_N <= C.N_MAX and C.N_MIN <= C.E8_N <= C.N_MAX
    for outs in (C.E1_OUTS, C.E2_OUTS, C.E3_OUTS, C.E8_OUTS):
        assert all(C.OUT_MIN <= o <= C.OUT_MAX for o in outs)
    assert C.IDEAL_BUDGET > 0 and C.NAIVE_LIMIT >= C.E4_RANGE[1] and C.ESTIMATE_SAMPLES > 0
