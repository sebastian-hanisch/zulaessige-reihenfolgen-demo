"""Konstanten: Regler-Grenzen, Ziehverfahren, Raster der Experimente, Farben und Presets."""

# Rechenbudget: die exakte Zählung bricht über IDEAL_BUDGET Idealen ab (dünn besetzte Pläne ab etwa 30 Aufgaben); am Reglermaximum (n = 40) kostet der Abbruch etwa eine halbe Sekunde.
N_MIN, N_MAX, DEFAULT_N = 6, 40, 12
OUT_MIN, OUT_MAX, OUT_STEP, DEFAULT_OUT = 0.5, 4.0, 0.5, 2.0   # mittlerer Ausgangsgrad
SEED_MAX, DEFAULT_SEED = 999999, 1
IDEAL_BUDGET = 50000
SAMPLERS = ("uniform", "naive", "chain")
SAMPLER_NAMES = {"uniform": "Gleichverteilt (Zähltabelle)", "naive": "Naiver Zufalls-Kahn", "chain": "Kettenverfahren (benachbarte Vertauschungen)"}
DEFAULT_SAMPLER = "uniform"
DRAWS = (200, 1000, 5000)                                      # gezogene Reihenfolgen
DEFAULT_DRAWS = 1000
STEPS = (10, 50, 300)                                          # Schritte des Kettenverfahrens je gezogener Reihenfolge
DEFAULT_STEPS = 50
ESTIMATE_SAMPLES = 1000                                        # Proben des Schätzers
NAIVE_LIMIT = 5000                                             # so viele Reihenfolgen darf die exakte Rechnung des naiven Verfahrens höchstens aufzählen

# Feste Instanzen und Raster der Experimente (nie ein einzelner Zufalls-Seed als Befund)
E1_NS, E1_OUTS, E1_SEEDS = (12, 20), (1.0, 2.0, 3.0, 4.0), tuple(range(8000, 8010))
E2_NS, E2_OUTS, E2_SEEDS = (20, 30, 40), (1.0, 2.0, 3.0, 4.0), tuple(range(8000, 8008))
E3_N, E3_OUTS, E3_SEEDS = 20, (1.0, 2.0, 3.0, 4.0), tuple(range(8400, 8430))
E4_N, E4_OUT, E4_SEEDS, E4_RANGE = 9, 1.5, tuple(range(8200, 8220)), (5, 5000)
E5_NS, E5_OUT, E5_SEEDS = (12, 16, 20), 1.5, tuple(range(8300, 8320))
E6_N, E6_OUT, E6_SEED, E6_STEPS, E6_RUNS = 7, 1.0, 8700, (7, 20, 49, 100, 200, 400), 3000
E7_PLANS, E7_NMIN, E7_NSPAN = 400, 4, 6
E8_N, E8_OUTS, E8_SEEDS = 20, (1.0, 2.0, 3.0, 4.0), tuple(range(8600, 8620))

# Farben
COLOR_EXACT = "#2F6B65"
COLOR_SAMPLED = "#ff9f1c"
COLOR_NAIVE = "#d62728"
COLOR_FORWARD = "rgba(76,120,168,0.45)"
COLOR_BAR = "#2F6B65"
COLOR_BAR2 = "#ff9f1c"
COLOR_BAR3 = "#59a14f"
COLOR_BAR4 = "#4c78a8"


def _p(n, out, seed, sampler=DEFAULT_SAMPLER, draws=DEFAULT_DRAWS, steps=DEFAULT_STEPS):
    return {"n": n, "out": out, "seed": seed, "sampler": sampler, "draws": draws, "steps": steps}


PRESETS = {
    "Lehrbeispiel (12 Aufgaben)": _p(DEFAULT_N, DEFAULT_OUT, DEFAULT_SEED),
    "Eine einzige Reihenfolge": _p(12, 4.0, 30),
    "Fast alles ist möglich": _p(18, 0.5, 2),
    "Ideale statt Permutationen": _p(20, 2.0, 8000),
    "Zu viele Ideale": _p(30, 1.0, 1),
    "Der Zufalls-Kahn ist verzerrt": _p(9, 1.5, 8204, sampler="naive"),
    "Die Kette mischt langsam": _p(12, 2.0, 1, sampler="chain", draws=5000, steps=10),
}
PRESET_HELP = {
    "Lehrbeispiel (12 Aufgaben)": "Zwölf Aufgaben, gleichverteilt gezogen: wie viele Reihenfolgen der Plan erlaubt und wie viele Ideale die Zählung braucht. Das ist die Voreinstellung.",
    "Eine einzige Reihenfolge": "Je zwei aufeinanderfolgende Aufgaben hängen unmittelbar zusammen: Hamilton-Pfad, genau eine zulässige Reihenfolge, kein Spielraum.",
    "Fast alles ist möglich": "Dünner Plan mit 18 Aufgaben: Billionen Reihenfolgen, jede Aufgabe hat viele mögliche Stellen.",
    "Ideale statt Permutationen": "20 Aufgaben: wenige hundert Ideale und Milliarden Reihenfolgen statt 20! Permutationen.",
    "Zu viele Ideale": "30 dünn besetzte Aufgaben: über dem Budget bricht die exakte Zählung ab, es bleibt der Schätzer mit seiner Streuung.",
    "Der Zufalls-Kahn ist verzerrt": "Eine verfügbare Aufgabe zufällig nehmen zieht manche Reihenfolgen hundertfach häufiger als andere.",
    "Die Kette mischt langsam": "Kettenverfahren mit nur 10 Schritten je Reihenfolge: die Verteilung der Stellen ist noch weit von der Gleichverteilung entfernt.",
}
