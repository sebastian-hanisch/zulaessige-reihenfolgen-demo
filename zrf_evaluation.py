"""Kennzahlen, Prüfung der Ergebnisse und Verdikte. Verdikte sind reine Funktionen (Art, Text): Zahlen kommen aus den Zeilen, nie aus dem Text.

Aufgaben sind in der Anzeige ab 1 nummeriert (`label`); im Kern ab 0."""

import math
import random
from dataclasses import dataclass, field
from statistics import median

import zrf_algorithm as A
import zrf_constants as C
from zrf_scenario import Instance, make_instance


@dataclass(frozen=True)
class Settings:
    n: int = C.DEFAULT_N
    out: float = C.DEFAULT_OUT
    seed: int = C.DEFAULT_SEED
    sampler: str = C.DEFAULT_SAMPLER
    draws: int = C.DEFAULT_DRAWS
    steps: int = C.DEFAULT_STEPS


@dataclass(frozen=True)
class Analysis:
    settings: Settings
    inst: Instance
    table: object = field(compare=False, repr=False)   # IdealTable oder None, wenn über dem Budget
    ideals: int                                        # Zahl der Ideale (Untergrenze beim Abbruch, wenn über dem Budget)
    exceeded: bool
    extensions: object                                 # Zahl der Reihenfolgen (int) oder None
    estimate: float                                    # Schätzer (Produkt der Auswahlgrößen), immer berechnet
    estimate_rel_se: float                             # geschätzter relativer Standardfehler des Schätzers
    bound: int                                         # Schranke der Ideale aus der Kettenzerlegung
    hamilton: bool                                     # Hamilton-Pfad der Beziehungen (eindeutige Ordnung)
    bounds: tuple                                      # früheste und späteste Stelle je Aufgabe
    sampler_used: str                                  # tatsächlich verwendetes Ziehverfahren (uniform fällt über dem Budget auf naive zurück)
    draws: tuple                                       # gezogene Reihenfolgen
    naive_probs: object = field(default=None, compare=False, repr=False)   # exakte Wahrscheinlichkeiten des naiven Verfahrens (kleine Pläne) oder None

    @property
    def n(self) -> int:
        return self.inst.n

    @property
    def adj(self):
        return self.inst.adj

    @property
    def fallback(self) -> bool:
        return self.sampler_used != self.settings.sampler

    @property
    def log_ext(self):
        """log10 der Zahl der Reihenfolgen (exakt oder geschätzt)."""
        return math.log10(self.extensions if self.extensions is not None else max(self.estimate, 1.0))

    @property
    def log_fact(self) -> float:
        return math.log10(math.factorial(self.n)) if self.n else 0.0

    @property
    def unique(self) -> bool:
        return self.extensions == 1

    @property
    def spread_median(self) -> float:
        return median(hi - lo for lo, hi in self.bounds) if self.bounds else 0

    @property
    def naive_ratio(self):
        if not self.naive_probs:
            return None
        return max(self.naive_probs.values()) / min(self.naive_probs.values())


def label(v: int) -> str:
    return str(v + 1)


def format_order(order, limit=14) -> str:
    nodes = [label(v) for v in order]
    if len(nodes) > limit:
        nodes = nodes[:8] + ["…"] + nodes[-3:]
    return " → ".join(nodes)


def analyse(settings: Settings) -> Analysis:
    return analyse_instance(make_instance(settings.n, settings.out, 0, settings.seed), settings)


def _draw(adj, table, settings, rng):
    """Zieht `settings.draws` Reihenfolgen mit dem gewählten Verfahren; gibt (verwendetes Verfahren, Reihenfolgen)."""
    sampler = settings.sampler
    if sampler == "uniform" and table is None:
        sampler = "naive"
    if sampler == "uniform":
        draws = tuple(A.sample_uniform(adj, table, rng) for _ in range(settings.draws))
    elif sampler == "naive":
        draws = tuple(A.naive_kahn_order(adj, rng) for _ in range(settings.draws))
    else:
        start = tuple(A.topological_order(adj))
        draws = tuple(A.mcmc_chain(adj, start, settings.steps, rng) for _ in range(settings.draws))
    return sampler, draws


def analyse_instance(inst: Instance, settings: Settings, table="auto") -> Analysis:
    """Zählen, Schätzen und Ziehen auf einem gegebenen Plan (Tests bauen Mini-Pläne von Hand). `table` darf von außen kommen (zwischengespeichert); „auto“ rechnet es."""
    adj = inst.adj
    n = len(adj)
    if table == "auto":
        table = A.ideal_table(adj, C.IDEAL_BUDGET)
    if table is None:
        ideals, _ = A.count_ideals(adj, C.IDEAL_BUDGET)
        exceeded, extensions = True, None
    else:
        ideals, exceeded, extensions = table.ideals, False, table.extensions
    samples = A.knuth_samples(adj, random.Random(settings.seed), C.ESTIMATE_SAMPLES)
    mean = sum(samples) / len(samples)
    var = sum((x - mean) ** 2 for x in samples) / max(1, len(samples) - 1)
    rel_se = math.sqrt(var / len(samples)) / mean if mean else 0.0
    rng = random.Random(settings.seed * 31 + 7)
    sampler, draws = _draw(adj, table, settings, rng)
    naive = A.naive_kahn_probabilities(adj, C.NAIVE_LIMIT) if extensions is not None and extensions <= C.NAIVE_LIMIT else None
    return Analysis(settings, inst, table, ideals, exceeded, extensions, mean, rel_se, A.chain_bound(adj), A.hamilton_path_exists(adj), A.position_bounds(adj), sampler, draws, naive)


def position_distribution(a: Analysis, v: int) -> dict:
    """Anteil der Reihenfolgen, in denen Aufgabe v an Stelle p steht (p ab 1): exakt (aus der Tabelle, sonst None) und als Häufigkeit unter den gezogenen Reihenfolgen."""
    n = a.n
    exact = None
    if a.table is not None:
        counts = A.position_counts(a.adj, a.table, v)
        exact = [c / a.extensions for c in counts]
    sampled = [0.0] * n
    for o in a.draws:
        sampled[o.index(v)] += 1 / len(a.draws)
    return {"exact": exact, "sampled": sampled}


def before_distribution(a: Analysis, v: int) -> dict:
    """Anteil der Reihenfolgen, in denen Aufgabe v vor b steht, für jedes b: exakt oder None und gezogen."""
    n = a.n
    exact = None
    if a.table is not None:
        exact = [c / a.extensions for c in A.before_counts(a.adj, a.table, v)]
    sampled = [0.0] * n
    for o in a.draws:
        pos = {t: i for i, t in enumerate(o)}
        for b in range(n):
            if pos[v] < pos[b]:
                sampled[b] += 1 / len(a.draws)
    return {"exact": exact, "sampled": sampled}


def tv_distance(p, q) -> float:
    return 0.5 * sum(abs(x - y) for x, y in zip(p, q))


def validate(a: Analysis) -> list[str]:
    """Unabhängige Prüfung vor der Anzeige: leere Liste, wenn alles stimmt; sonst die verletzten Regeln."""
    problems = []
    if not a.n:
        return problems
    adj = a.adj
    if not all(A.is_extension(adj, o) for o in a.draws):
        problems.append("Eine gezogene Reihenfolge verletzt eine Beziehung.")
    if a.extensions is not None:
        if not 1 <= a.extensions <= math.factorial(a.n):
            problems.append("Die Zahl der Reihenfolgen liegt außerhalb von 1 bis n!.")
        if a.table is not None and a.table.fwd[(1 << a.n) - 1] != a.extensions:
            problems.append("Vorwärts- und Rückwärtszahl der DP stimmen nicht überein.")
        if a.unique != a.hamilton:
            problems.append("Die Ordnung ist nicht genau dann eindeutig, wenn die Beziehungen einen Hamilton-Pfad bilden.")
    if not a.exceeded and a.ideals > a.bound:
        problems.append("Die Zahl der Ideale übersteigt die Schranke aus der Kettenzerlegung.")
    if any(not lo <= o.index(v) + 1 <= hi for o in a.draws for v, (lo, hi) in enumerate(a.bounds)):
        problems.append("Eine gezogene Stelle liegt außerhalb der Positionsbereiche.")
    if a.extensions is not None and a.extensions > 1 and a.estimate <= 0:
        problems.append("Der Schätzer ist nicht positiv.")
    if a.naive_probs is not None and abs(sum(a.naive_probs.values()) - 1) > 1e-9:
        problems.append("Die Wahrscheinlichkeiten des naiven Verfahrens summieren sich nicht zu eins.")
    return problems


# --- Zahlenformat --------------------------------------------------------------------------------------------------------------------------

def _i(x) -> str:
    """Ganze Zahl mit Punkt als Tausendertrenner."""
    return f"{x:,.0f}".replace(",", ".")


def _dec(x, digits=1) -> str:
    """Zahl mit Komma; ganze Werte ohne Nachkommastelle."""
    x = float(x)
    if x == int(x):
        return _i(x)
    return f"{x:,.{digits}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _pct(share, digits=0) -> str:
    return _dec(round(100.0 * share, digits), digits) if digits else _i(round(100.0 * share))


def _big(x) -> str:
    """Große Zahl mit Tausenderpunkten; ab 15 Stellen in Zehnerpotenz (nur Anzeige)."""
    x = int(x)
    if x < 10 ** 15:
        return _i(x)
    exp = len(str(x)) - 1
    return f"{x / 10 ** exp:.2f}".replace(".", ",") + f" · 10^{exp}"


def _pow(log10) -> str:
    """Zehnerpotenz aus dem Zehnerlogarithmus, z. B. 10^9,4."""
    return "10^" + _dec(log10, 1)


# --- Verdikte -------------------------------------------------------------------------------------------------------------------------------

def verdict_question(a: Analysis) -> tuple[str, str]:
    """Kernfrage: Wie viel Spielraum hat der Plan, und wie wählt man fair eine Reihenfolge?"""
    if not a.n:
        return "info", "Der Plan ist leer."
    if a.exceeded:
        return "warning", (f"**Der Plan hat mehr als {_i(C.IDEAL_BUDGET)} Ideale**: Die exakte Zählung bricht ab (Zählen ist #P-vollständig). Der Schätzer kommt auf etwa {_big(a.estimate)} zulässige Reihenfolgen "
                           f"(relativer Standardfehler etwa {_pct(a.estimate_rel_se)} %) von {_big(math.factorial(a.n))} Permutationen; das gleichverteilte Ziehen ist hier nicht möglich.")
    parts = [f"**Der Plan erlaubt {_big(a.extensions)} zulässige Reihenfolgen** von {_big(math.factorial(a.n))} Permutationen ({_pow(a.log_ext)} gegen {_pow(a.log_fact)}); die Zählung brauchte {_i(a.ideals)} Ideale statt {_big(math.factorial(a.n))} Permutationen."]
    if a.unique:
        parts.append("Die Reihenfolge ist **eindeutig**: je zwei aufeinanderfolgende Aufgaben hängen unmittelbar zusammen (Hamilton-Pfad), es gibt keinen Spielraum.")
    else:
        parts.append(f"Zwischen der frühesten und der spätesten möglichen Stelle einer Aufgabe liegen im Median {_dec(a.spread_median)} Plätze.")
    if a.naive_ratio is not None and a.naive_ratio > 1:
        parts.append(f"Der naive Zufalls-Kahn zieht die wahrscheinlichste Reihenfolge {_dec(a.naive_ratio)}-mal so oft wie die unwahrscheinlichste, das Ziehen über die Zähltabelle trifft jede gleich oft.")
    return "info", " ".join(parts)


def verdict_permutations(rows: list[dict]) -> tuple[str, str]:
    """E1: Ideale und Reihenfolgen gegen n!."""
    ref = max((r for r in rows if r["out"] == 2.0), key=lambda r: r["n"])
    text = (f"Bei {_i(ref['n'])} Aufgaben und Ausgangsgrad {_dec(ref['out'])} hat der Plan im Median {_dec(ref['ideals'])} Ideale und {_pow(ref['log_ext'])} zulässige Reihenfolgen gegen {_pow(ref['log_fact'])} Permutationen. "
            f"Die DP zählt über die Ideale, nicht über die Permutationen.")
    return ("info" if all(r["ideals"] < 10 ** r["log_fact"] and r["log_ext"] < r["log_fact"] for r in rows) else "warning"), text


def verdict_density(rows: list[dict]) -> tuple[str, str]:
    """E2: Zahl der Ideale über Dichte und Größe, Budgetgrenze."""
    ref_n = sorted({r["n"] for r in rows})[1]
    dens = sorted((r for r in rows if r["n"] == ref_n), key=lambda r: r["out"])
    sparse, dense = dens[0], dens[-1]
    biggest = max(rows, key=lambda r: r["n"])
    bigs = sorted((r for r in rows if r["n"] == biggest["n"]), key=lambda r: r["out"])
    over_text = "; ".join(f"Grad {_dec(r['out'])}: {_i(r['over'])} von {_i(r['instances'])}" for r in bigs)
    text = (f"Bei {_i(ref_n)} Aufgaben wächst die Zahl der Ideale mit der Dünnheit des Plans: im Median {_dec(dense['ideals'])} bei Ausgangsgrad {_dec(dense['out'])}, "
            + (f"über dem Budget von {_i(C.IDEAL_BUDGET)} in {_i(sparse['over'])} von {_i(sparse['instances'])} Plänen bei Grad {_dec(sparse['out'])}. " if sparse["ideals"] is None else f"{_dec(sparse['ideals'])} bei Grad {_dec(sparse['out'])}. ")
            + f"Bei {_i(biggest['n'])} Aufgaben liegen über dem Budget: {over_text}.")
    return ("info" if sparse["over"] > dense["over"] else "warning"), text


def verdict_bound(rows: list[dict]) -> tuple[str, str]:
    """E3: Schranke aus der Kettenzerlegung."""
    total, holds = sum(r["instances"] for r in rows), sum(r["holds"] for r in rows)
    lo, hi = min(r["ratio"] for r in rows), max(r["ratio"] for r in rows)
    text = (f"Die Zahl der Ideale liegt in {_i(holds)} von {_i(total)} Plänen unter dem Produkt der (Kettenlänge + 1) über eine kleinste Kettenzerlegung; die Schranke ist im Median das {_dec(lo)}- bis {_dec(hi)}-Fache "
            f"der tatsächlichen Zahl.")
    return ("info" if holds == total else "warning"), text


def verdict_naive(row: dict) -> tuple[str, str]:
    """E4: naiver Zufalls-Kahn gegen gleichverteilt."""
    text = (f"Beim naiven Zufalls-Kahn (an jeder Stelle gleichverteilt eine verfügbare Aufgabe) ist die wahrscheinlichste Reihenfolge im Median das {_i(row['ratio_median'])}-Fache der unwahrscheinlichsten "
            f"(höchstens das {_i(row['ratio_max'])}-Fache); der Abstand zur Gleichverteilung (Totalvariation) beträgt im Median {_dec(row['tv_median'], 2)}.")
    return ("info" if row["ratio_median"] > 1 else "warning"), text


def verdict_estimator(rows: list[dict]) -> tuple[str, str]:
    """E5: Schätzer gegen die exakte Zahl."""
    parts = "; ".join(f"{_i(r['n'])} Aufgaben: {_pct(r['err_median'])} % im Median, höchstens {_pct(r['err_max'])} %" for r in rows)
    text = f"Der Schätzer (Produkt der Auswahlgrößen, {_i(C.ESTIMATE_SAMPLES)} Proben) weicht im Mittel so weit von der exakten Zahl ab: {parts}. Er ist erwartungstreu, streut aber stärker, je dünner der Plan ist."
    return ("info" if all(r["err_median"] < 0.5 for r in rows) else "warning"), text


def verdict_mixing(rows: list[dict]) -> tuple[str, str]:
    """E6: Mischzeit des Kettenverfahrens."""
    steps = " / ".join(_i(r["steps"]) for r in rows)
    tvs = " / ".join(_dec(r["tv"], 2) for r in rows)
    first_ok = next((r["steps"] for r in rows if r["tv"] < 0.1), None)
    text = (f"Bei {_i(rows[0]['n'])} Aufgaben und {_i(rows[0]['extensions'])} Reihenfolgen liegt der Abstand des Kettenverfahrens zur Gleichverteilung nach {steps} Schritten bei {tvs} (Totalvariation, {_i(rows[0]['runs'])} Läufe je Schrittzahl). "
            + (f"Unter 0,1 ist er erstmals nach {_i(first_ok)} Schritten." if first_ok else "Unter 0,1 kommt er in diesem Raster nicht."))
    return ("info" if rows[0]["tv"] > rows[-1]["tv"] and first_ok else "warning"), text


def verdict_unique(row: dict) -> tuple[str, str]:
    """E7: eindeutige Ordnung gegen Hamilton-Pfad."""
    text = (f"Auf {_i(row['instances'])} kleinen Plänen ist die Ordnung in {_i(row['unique'])} Fällen eindeutig; die Aussage „eindeutig genau dann, wenn die Kahn-Ordnung eine Kette von Beziehungen ist“ stimmt "
            f"in {_i(row['agree'])} von {_i(row['instances'])} Fällen.")
    return ("info" if row["agree"] == row["instances"] and row["unique"] > 0 else "warning"), text


def verdict_spread(rows: list[dict]) -> tuple[str, str]:
    """E8: Spielraum je Aufgabe."""
    rows = sorted(rows, key=lambda r: r["out"])
    parts = " / ".join(_dec(r["median"]) for r in rows)
    outs = " / ".join(_dec(r["out"]) for r in rows)
    text = (f"Bei {_i(rows[0]['n'])} Aufgaben liegen zwischen der frühesten und der spätesten möglichen Stelle einer Aufgabe im Median {parts} Plätze (Ausgangsgrad {outs}); "
            f"der größte Spielraum einer einzelnen Aufgabe beträgt {_i(max(r['max'] for r in rows))} Plätze.")
    return ("info" if rows[0]["median"] > rows[-1]["median"] else "warning"), text
