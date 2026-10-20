"""Gemeinsame Fixtures: die Mini-Pläne, an denen jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b).

Teure Experimente laufen einmal je Testlauf (`lru_cache`) und werden von Claims-, Verdikt- und Mutationstests gemeinsam genutzt."""

import sys
from functools import lru_cache
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

BUDGET = 50000

# Von Hand gerechnete Mini-Pläne: Name -> (Adjazenz, Zahl der Reihenfolgen, Zahl der Ideale, eindeutige Ordnung?)
MINI = {
    "kette3": (((1,), (2,), ()), 1, 4, True),
    "unabhaengig3": (((), (), ()), 6, 8, False),                                           # 3! Reihenfolgen, 2^3 Teilmengen sind Ideale
    "raute": (((1, 2), (3,), (3,), ()), 2, 6, False),                                      # 0, dann 1 und 2 in beliebiger Reihenfolge, dann 3
    "n_graph": (((2,), (2, 3), (), ()), 5, 8, False),                                      # a=0 -> c=2, b=1 -> c, b -> d=3: b a c d, b a d c, b d a c, a b c d, a b d c
    "zwei_ketten": (((1,), (), (3,), ()), 6, 9, False),                                    # zwei Ketten der Länge 2 mischen: C(4, 2); Ideale 3 * 3
    "abkuerzung": (((1, 2), (2,), ()), 1, 4, True),                                        # 0 -> 2 ist überflüssig, die Kette 0, 1, 2 bleibt
}


@pytest.fixture
def mini():
    return MINI


@lru_cache(maxsize=None)
def cached(name):
    """Einmal je Testlauf berechnete Experimente (Name der Funktion in zrf_experiments)."""
    import zrf_experiments as ex
    return getattr(ex, name)()
