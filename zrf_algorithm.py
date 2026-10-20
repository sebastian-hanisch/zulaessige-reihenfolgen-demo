"""Kern der Demo (nur Standardbibliothek): zulässige Reihenfolgen (lineare Erweiterungen) eines kreisfreien Plans.

`adj[v]` sind die Aufgaben, die nach v kommen sollen. Eine **zulässige Reihenfolge** stellt jede Aufgabe nach ihren Vorgängern. **Zählen** geht exakt über die **Ideale** (die unter „Vorgänger“
abgeschlossenen Aufgabenmengen als Bitmasken): `ideal_table` zählt Wege zu jedem Ideal (vorwärts) und Fortsetzungen (rückwärts) und bricht über einem Budget an Idealen ab (Zählen ist #P-vollständig).
Daraus folgen das **gleichverteilte Ziehen** (`sample_uniform`), die Verteilung der Stelle einer Aufgabe und die Wahrscheinlichkeit „A vor B“. Gegenstücke: der **naive Zufalls-Kahn**
(`naive_kahn_order`, nicht gleichverteilt), der **Schätzer** aus dem Produkt der Auswahlgrößen (`knuth_samples`, erwartungstreu) und das **Kettenverfahren** mit benachbarten Vertauschungen
(`mcmc_chain`). Aufwand wird in Idealen gezählt, nicht in Sekunden. Zufall nur über `random.Random.random()`."""

from collections import deque
from dataclasses import dataclass


# --- Graphhilfen ---------------------------------------------------------------------------------------------------------------------------

def topological_order(adj):
    """Kahn-Abbau; None, wenn der Graph einen Kreis hat."""
    n = len(adj)
    indeg = [0] * n
    for v in range(n):
        for w in adj[v]:
            indeg[w] += 1
    queue = deque(v for v in range(n) if indeg[v] == 0)
    order = []
    while queue:
        v = queue.popleft()
        order.append(v)
        for w in adj[v]:
            indeg[w] -= 1
            if indeg[w] == 0:
                queue.append(w)
    return order if len(order) == n else None


def _order(adj):
    order = topological_order(adj)
    if order is None:
        raise ValueError("Der Plan hat einen Kreis")
    return order


def pred_masks(adj):
    """pm[v] = Bitmaske der unmittelbaren Vorgänger von v."""
    pm = [0] * len(adj)
    for a in range(len(adj)):
        for b in adj[a]:
            pm[b] |= 1 << a
    return pm


def closure_bits(adj):
    """Transitive Hülle mit Bitmengen (Stück 5): reach[v] = Bitmaske der von v aus erreichbaren Aufgaben."""
    reach = [0] * len(adj)
    for v in reversed(_order(adj)):
        for w in adj[v]:
            reach[v] |= reach[w] | (1 << w)
    return reach


def _randbelow(rng, k):
    """Gleichverteilte ganze Zahl 0 bis k-1 aus rng.random() (versionsstabil), auch für sehr große k: Zusammensetzen aus 52-Bit-Stücken, Rest mod k (Verzerrung unter 2^-52)."""
    if k <= 1:
        return 0
    chunks = (k.bit_length() + 51) // 52 + 1
    r = 0
    for _ in range(chunks):
        r = (r << 52) | int(rng.random() * (1 << 52))
    return r % k


# --- Zählen über die Ideale ------------------------------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class IdealTable:
    layers: tuple      # layers[k] = Ideale mit k Aufgaben (Bitmasken)
    fwd: dict          # fwd[mask] = Zahl der Wege von der leeren Menge zu diesem Ideal
    ext: dict          # ext[mask] = Zahl der Fortsetzungen vom Ideal zur vollen Menge
    ideals: int

    @property
    def extensions(self) -> int:
        return self.ext[0]


def count_ideals(adj, budget):
    """Zahl der Ideale (Schichten der DP); (Zahl, True), wenn sie `budget` überschreitet (dann ist die Zahl nur die Untergrenze beim Abbruch), sonst (Zahl, False)."""
    layers, total = _ideal_layers(adj, budget)
    return total, layers is None


def _ideal_layers(adj, budget):
    """Schichten der Ideale mit Vorwärtszahlen; (None, Zahl beim Abbruch), wenn mehr als `budget` Ideale."""
    n = len(adj)
    pm = pred_masks(adj)
    fwd = {0: 1}
    layers = [[0]]
    total = 1
    for _ in range(n):
        nxt: dict = {}
        for mask in layers[-1]:
            c = fwd[mask]
            for v in range(n):
                if not (mask >> v) & 1 and (pm[v] & ~mask) == 0:
                    m2 = mask | (1 << v)
                    if m2 in nxt:
                        nxt[m2] += c
                    else:
                        nxt[m2] = c
        total += len(nxt)
        if total > budget:
            return None, total
        fwd.update(nxt)
        layers.append(list(nxt))
    return (layers, fwd), total


def ideal_table(adj, budget):
    """Tabelle der Ideale mit Vorwärts- und Rückwärtszahlen; None, wenn es mehr als `budget` Ideale gibt (dann bleibt nur Schätzen)."""
    res, total = _ideal_layers(adj, budget)
    if res is None:
        return None
    layers, fwd = res
    n = len(adj)
    pm = pred_masks(adj)
    ext = {(1 << n) - 1: 1}
    for k in range(n - 1, -1, -1):
        for mask in layers[k]:
            s = 0
            for v in range(n):
                if not (mask >> v) & 1 and (pm[v] & ~mask) == 0:
                    s += ext[mask | (1 << v)]
            ext[mask] = s
    return IdealTable(tuple(tuple(layer) for layer in layers), fwd, ext, total)


def count_extensions(adj, budget):
    """Zahl der zulässigen Reihenfolgen; None, wenn mehr als `budget` Ideale. Der leere Plan hat eine (die leere) Reihenfolge."""
    t = ideal_table(adj, budget)
    return None if t is None else t.extensions


def _available(pm, mask, n):
    return [v for v in range(n) if not (mask >> v) & 1 and (pm[v] & ~mask) == 0]


def sample_uniform(adj, table, rng):
    """Eine zulässige Reihenfolge, **gleichverteilt**: Schritt für Schritt eine verfügbare Aufgabe mit Wahrscheinlichkeit (Zahl der Fortsetzungen danach) / (Zahl der Fortsetzungen jetzt)."""
    n = len(adj)
    pm = pred_masks(adj)
    mask, order = 0, []
    while len(order) < n:
        opts = _available(pm, mask, n)
        weights = [table.ext[mask | (1 << v)] for v in opts]
        pick = _randbelow(rng, sum(weights))
        for v, w in zip(opts, weights):
            if pick < w:
                order.append(v)
                mask |= 1 << v
                break
            pick -= w
    return tuple(order)


def naive_kahn_order(adj, rng):
    """Naiver Zufalls-Kahn: an jeder Stelle eine verfügbare Aufgabe gleichverteilt (nicht gleichverteilt über die Reihenfolgen)."""
    n = len(adj)
    pm = pred_masks(adj)
    mask, order = 0, []
    while len(order) < n:
        opts = _available(pm, mask, n)
        v = opts[int(rng.random() * len(opts))]
        order.append(v)
        mask |= 1 << v
    return tuple(order)


def all_extensions(adj, limit):
    """Alle zulässigen Reihenfolgen durch Aufzählung (nur kleine Zahlen); None, wenn es mehr als `limit` gäbe."""
    n = len(adj)
    pm = pred_masks(adj)
    found: list = []

    def rec(mask, order):
        if len(found) > limit:
            return
        if len(order) == n:
            found.append(tuple(order))
            return
        for v in _available(pm, mask, n):
            rec(mask | (1 << v), order + [v])

    rec(0, [])
    return None if len(found) > limit else found


def naive_kahn_probabilities(adj, limit=5000):
    """Exakte Wahrscheinlichkeit jeder Reihenfolge beim naiven Zufalls-Kahn ({Reihenfolge: Wahrscheinlichkeit}); None, wenn mehr als `limit` Reihenfolgen."""
    n = len(adj)
    pm = pred_masks(adj)
    probs: dict = {}

    def rec(mask, order, p):
        if len(probs) > limit:
            return
        if len(order) == n:
            probs[tuple(order)] = p
            return
        opts = _available(pm, mask, n)
        for v in opts:
            rec(mask | (1 << v), order + [v], p / len(opts))

    rec(0, [], 1.0)
    return None if len(probs) > limit else probs


def is_extension(adj, order) -> bool:
    """Unabhängiger Prüfer: jede Aufgabe genau einmal, und jede Beziehung a vor b hält ein."""
    n = len(adj)
    if sorted(order) != list(range(n)):
        return False
    pos = {v: i for i, v in enumerate(order)}
    return all(pos[a] < pos[b] for a in range(n) for b in adj[a])


# --- Schätzen und Kettenverfahren --------------------------------------------------------------------------------------------------------------

def knuth_samples(adj, rng, samples):
    """Proben des Schätzers: Produkt der Zahl der verfügbaren Aufgaben längs einer naiven Zufallsordnung. Jede Reihenfolge hat dabei die Wahrscheinlichkeit 1 / Produkt, also ist der
    Erwartungswert der Probe die Zahl der Reihenfolgen (erwartungstreu); die Streuung wächst mit der Dünnheit des Plans. Gibt die Proben als Gleitkommazahlen."""
    n = len(adj)
    pm = pred_masks(adj)
    out = []
    for _ in range(samples):
        mask, x = 0, 1.0
        for _ in range(n):
            opts = _available(pm, mask, n)
            x *= len(opts)
            mask |= 1 << opts[int(rng.random() * len(opts))]
        out.append(x)
    return tuple(out)


def knuth_estimate(adj, rng, samples) -> float:
    xs = knuth_samples(adj, rng, samples)
    return sum(xs) / len(xs) if xs else 0.0


def mcmc_chain(adj, order, steps, rng):
    """Kettenverfahren: je Schritt eine Stelle i wählen, mit Wahrscheinlichkeit 1/2 pausieren, sonst die Aufgaben an i und i + 1 vertauschen, wenn keine von der anderen abhängt
    (benachbart genügt die unmittelbare Beziehung). Bleibt zulässig; die Gleichverteilung ist stationär, die Mischzeit wird gemessen, nicht bewiesen."""
    pm = pred_masks(adj)
    o = list(order)
    n = len(o)
    if n < 2:
        return tuple(o)
    for _ in range(steps):
        i = int(rng.random() * (n - 1))
        if rng.random() < 0.5:
            a, b = o[i], o[i + 1]
            if not (pm[b] >> a) & 1:
                o[i], o[i + 1] = b, a
    return tuple(o)


# --- Spielraum -----------------------------------------------------------------------------------------------------------------------------

def position_bounds(adj):
    """Früheste und späteste mögliche Stelle je Aufgabe (ab 1): Zahl der Vorgänger + 1 und n minus Zahl der Nachfolger (über die Hülle)."""
    n = len(adj)
    reach = closure_bits(adj)
    below = [0] * n
    for u in range(n):
        for v in range(n):
            if (reach[u] >> v) & 1:
                below[v] += 1
    return tuple((below[v] + 1, n - bin(reach[v]).count("1")) for v in range(n))


def position_counts(adj, table, v):
    """Zahl der Reihenfolgen, in denen Aufgabe v an Stelle p steht (p ab 1, Liste der Länge n): Summe über die Ideale ohne v, in denen v verfügbar ist, von Vorwärtszahl mal Fortsetzungen danach."""
    n = len(adj)
    pm = pred_masks(adj)
    counts = [0] * n
    for k in range(n):
        for mask in table.layers[k]:
            if not (mask >> v) & 1 and (pm[v] & ~mask) == 0:
                counts[k] += table.fwd[mask] * table.ext[mask | (1 << v)]
    return counts


def before_counts(adj, table, a):
    """Zahl der Reihenfolgen, in denen Aufgabe a vor b steht, für jedes b (Liste der Länge n; b = a: 0): Summe über die Ideale mit a, in denen b verfügbar ist, von Vorwärtszahl mal Fortsetzungen danach."""
    n = len(adj)
    pm = pred_masks(adj)
    counts = [0] * n
    for k in range(1, n):
        for mask in table.layers[k]:
            if (mask >> a) & 1:
                f = table.fwd[mask]
                for b in range(n):
                    if not (mask >> b) & 1 and (pm[b] & ~mask) == 0:
                        counts[b] += f * table.ext[mask | (1 << b)]
    return counts


def hamilton_path_exists(adj) -> bool:
    """Gibt es eine Reihenfolge, in der je zwei aufeinanderfolgende Aufgaben durch eine Beziehung verbunden sind? Im DAG heißt das: die Kahn-Ordnung ist eine Kette von Beziehungen."""
    order = _order(adj)
    return all(order[i + 1] in adj[order[i]] for i in range(len(order) - 1))


def kuhn_chain_lengths(adj):
    """Längen der Ketten einer kleinsten Kettenzerlegung (Stück 6: n minus größtes Matching auf der Hülle, Kuhn)."""
    n = len(adj)
    reach = closure_bits(adj)
    rel = [[w for w in range(n) if (reach[v] >> w) & 1] for v in range(n)]
    match_l = [-1] * n
    match_r = [-1] * n

    def augment(u, seen):
        for w in rel[u]:
            if w in seen:
                continue
            seen.add(w)
            if match_r[w] == -1 or augment(match_r[w], seen):
                match_r[w] = u
                match_l[u] = w
                return True
        return False

    for u in range(n):
        augment(u, set())
    lengths = []
    for v in range(n):
        if match_r[v] == -1:
            k, cur = 1, v
            while match_l[cur] != -1:
                cur = match_l[cur]
                k += 1
            lengths.append(k)
    return tuple(sorted(lengths, reverse=True))


def chain_bound(adj) -> int:
    """Obere Schranke der Zahl der Ideale (Stück 6): Produkt über die Ketten einer kleinsten Zerlegung von (Kettenlänge + 1); ein Ideal enthält von jeder Kette einen Anfang."""
    p = 1
    for k in kuhn_chain_lengths(adj):
        p *= k + 1
    return p
