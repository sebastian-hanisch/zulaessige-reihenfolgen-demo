"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben.

Hauptbild ist die gezogene Reihenfolge als Bogendiagramm: die Aufgaben stehen in der gezogenen Reihenfolge auf einer Linie, jede Beziehung läuft oben von links nach rechts (sonst wäre die
Reihenfolge nicht zulässig). Dazu die Verteilung der Stelle einer Aufgabe, die Wahrscheinlichkeit „A vor B“ und die Positionsbereiche."""

import math

import plotly.graph_objects as go
from plotly.subplots import make_subplots

import zrf_constants as C
from zrf_evaluation import label

ARC_POINTS = 14


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.25), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def _arc(xa, xb, n, points=ARC_POINTS):
    span = abs(xb - xa)
    h = max(0.07, span / max(1, n - 1))
    xs = [xa + (xb - xa) * i / points for i in range(points + 1)]
    ys = [h * math.sin(math.pi * i / points) for i in range(points + 1)]
    return xs, ys


def build_order_figure(inst, order, highlight=()):
    """Gezogene Reihenfolge als Bogendiagramm: Aufgaben in der Reihenfolge `order`, Beziehungen als Bögen (alle von links nach rechts); `highlight` (Aufgaben) mit rotem Rand."""
    n = inst.n
    pos = {v: i for i, v in enumerate(order)}
    xs, ys = [], []
    for a in range(n):
        for b in inst.adj[a]:
            ax, ay = _arc(pos[a], pos[b], n)
            xs += ax + [None]
            ys += ay + [None]
    fig = go.Figure()
    if xs:
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=C.COLOR_FORWARD, width=1.2 if n <= 30 else 0.8), hoverinfo="skip", showlegend=False))
    marked = set(highlight)
    labelled = n <= 40
    fig.add_trace(go.Scatter(
        x=list(range(n)), y=[0] * n, mode="markers+text" if labelled else "markers",
        marker=dict(size=22 if n <= 30 else 18, color="#f2f2f2", line=dict(color=[C.COLOR_NAIVE if v in marked else "#333" for v in order], width=[3 if v in marked else 1 for v in order])),
        text=[label(v) for v in order] if labelled else None, textposition="middle center", textfont=dict(color="#222", size=11),
        hovertext=[f"Stelle {i + 1}: Aufgabe {label(v)}" for i, v in enumerate(order)], hoverinfo="text", showlegend=False))
    fig.update_xaxes(title_text="Reihenfolge →", range=[-0.8, n - 0.2], showticklabels=False, showgrid=False, zeroline=False)
    fig.update_yaxes(range=[-0.2, 1.12], showticklabels=False, showgrid=False, zeroline=True, zerolinecolor="rgba(128,128,128,0.35)")
    _base(fig, 300)
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=40))
    return fig


def build_position_figure(exact, sampled, sampler_name):
    """Anteil der Reihenfolgen mit Aufgabe v an Stelle p: exakt aus der Tabelle (falls vorhanden) gegen die Häufigkeit unter den gezogenen Reihenfolgen."""
    n = len(sampled)
    xs = list(range(1, n + 1))
    fig = go.Figure()
    if exact is not None:
        fig.add_trace(go.Bar(x=xs, y=[100 * p for p in exact], name="exakt (Zähltabelle)", marker_color=C.COLOR_EXACT))
    fig.add_trace(go.Bar(x=xs, y=[100 * p for p in sampled], name=f"gezogen: {sampler_name}", marker_color=C.COLOR_SAMPLED))
    fig.update_layout(barmode="group")
    fig.update_xaxes(title_text="Stelle in der Reihenfolge", dtick=1 if n <= 20 else None)
    fig.update_yaxes(title_text="Anteil der Reihenfolgen (%)")
    return _base(fig, 340)


def build_before_figure(exact, sampled, a, comparable):
    """Anteil der Reihenfolgen, in denen Aufgabe a vor b steht (je Aufgabe b); `comparable` (Menge): b hängt mit a zusammen, der Anteil ist 0 oder 1."""
    n = len(sampled)
    others = [b for b in range(n) if b != a]
    xs = [label(b) for b in others]
    fig = go.Figure()
    if exact is not None:
        fig.add_trace(go.Bar(x=xs, y=[100 * exact[b] for b in others], name="exakt (Zähltabelle)", marker_color=C.COLOR_EXACT))
    fig.add_trace(go.Bar(x=xs, y=[100 * sampled[b] for b in others], name="unter den gezogenen Reihenfolgen", marker_color=C.COLOR_SAMPLED))
    fig.update_layout(barmode="group")
    fig.update_xaxes(title_text=f"Aufgabe b (Aufgabe {label(a)} steht vor b)", type="category")
    fig.update_yaxes(title_text="Anteil der Reihenfolgen (%)", range=[0, 105])
    return _base(fig, 340)


def build_bounds_figure(bounds, expected=None):
    """Positionsbereiche: je Aufgabe ein Balken von der frühesten bis zur spätesten möglichen Stelle; Raute = erwartete Stelle (exakt oder aus den gezogenen Reihenfolgen)."""
    n = len(bounds)
    order = sorted(range(n), key=lambda v: (bounds[v][0], bounds[v][1], v))
    fig = go.Figure()
    fig.add_trace(go.Bar(y=[label(v) for v in order], x=[bounds[v][1] - bounds[v][0] + 1 for v in order], base=[bounds[v][0] - 0.5 for v in order], orientation="h",
                         marker_color=C.COLOR_BAR4, hovertext=[f"Aufgabe {label(v)}: Stelle {bounds[v][0]} bis {bounds[v][1]}" for v in order], hoverinfo="text", showlegend=False))
    if expected is not None:
        fig.add_trace(go.Scatter(y=[label(v) for v in order], x=[expected[v] for v in order], mode="markers", marker=dict(symbol="diamond", size=9, color=C.COLOR_NAIVE), name="erwartete Stelle"))
    fig.update_xaxes(title_text="Stelle in der Reihenfolge", range=[0.5, n + 0.5], dtick=1 if n <= 20 else None)
    fig.update_yaxes(type="category", autorange="reversed", title_text="Aufgabe")
    fig.update_layout(barmode="overlay")
    return _base(fig, max(260, min(900, 80 + 18 * n)))


# --- Experimente ---------------------------------------------------------------------------------------------------------------------------

_N_COLORS = {12: "#4c78a8", 20: "#f58518", 30: "#2F6B65", 40: "#b279a2"}


def build_permutations_figure(rows):
    """E1: Zehnerlogarithmus von n!, der Zahl der Reihenfolgen und der Zahl der Ideale je Fall."""
    xs = [f"{r['n']} Aufg., Grad {r['out']:g}".replace(".", ",") for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=xs, y=[r["log_fact"] for r in rows], name="Permutationen (n!)", marker_color=C.COLOR_NAIVE))
    fig.add_trace(go.Bar(x=xs, y=[r["log_ext"] for r in rows], name="zulässige Reihenfolgen", marker_color=C.COLOR_BAR2))
    fig.add_trace(go.Bar(x=xs, y=[math.log10(r["ideals"]) for r in rows], name="Ideale (Zustände der DP)", marker_color=C.COLOR_BAR))
    fig.update_layout(barmode="group")
    fig.update_xaxes(type="category", tickangle=-45)
    fig.update_yaxes(title_text="Zehnerlogarithmus (10^y)")
    return _base(fig, 420)


def build_density_figure(rows):
    """E2: Zahl der Ideale (Median der Pläne unter dem Budget, logarithmisch) über den Ausgangsgrad; Pläne über dem Budget liegen an der Budgetlinie (Raute)."""
    fig = go.Figure()
    outs = sorted({r["out"] for r in rows})
    for n in sorted({r["n"] for r in rows}):
        sel = {r["out"]: r for r in rows if r["n"] == n}
        under = [o for o in outs if sel[o]["ideals"] is not None]
        over = [o for o in outs if sel[o]["over"] > 0]
        color = _N_COLORS.get(n, "#888")
        fig.add_trace(go.Scatter(x=under, y=[sel[o]["ideals"] for o in under], mode="lines+markers", name=f"{n} Aufgaben", line=dict(color=color), marker=dict(size=8)))
        if over:
            fig.add_trace(go.Scatter(x=over, y=[C.IDEAL_BUDGET] * len(over), mode="markers+text", marker=dict(symbol="diamond", size=12, color=color), name=f"{n} Aufgaben: Plan über dem Budget",
                                     text=[f"{sel[o]['over']}/{sel[o]['instances']}" for o in over], textposition="top center"))
    fig.add_hline(y=C.IDEAL_BUDGET, line_dash="dot", line_color="rgba(128,128,128,0.8)", annotation_text="Budget", annotation_position="bottom right")
    fig.update_xaxes(title_text="mittlerer Ausgangsgrad", dtick=1)
    fig.update_yaxes(title_text="Zahl der Ideale (Median, logarithmisch)", type="log")
    fig.update_layout(legend=dict(orientation="h", y=-0.35))
    return lock_axes(fig.update_layout(height=420, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor="rgba(0,0,0,0)"))


def build_bound_figure(rows):
    """E3: Verhältnis von Schranke zu tatsächlicher Zahl der Ideale (Median) je Ausgangsgrad."""
    xs = [f"Grad {r['out']:g}".replace(".", ",") for r in rows]
    fig = go.Figure(go.Bar(x=xs, y=[r["ratio"] for r in rows], marker_color=C.COLOR_BAR, text=[f"{r['holds']}/{r['instances']} gelten" for r in rows], textposition="outside", cliponaxis=False))
    fig.add_hline(y=1, line_dash="dot", line_color="rgba(128,128,128,0.8)", annotation_text="Schranke = Zahl der Ideale", annotation_position="top right")
    fig.update_xaxes(type="category")
    fig.update_yaxes(title_text="Schranke / Ideale (Median)", rangemode="tozero")
    return _base(fig, 330)


def build_naive_figure(row):
    """E4: wahrscheinlichste gegen unwahrscheinlichste Reihenfolge beim naiven Zufalls-Kahn (Median und Maximum, logarithmisch); gleichverteilt wäre das Verhältnis 1."""
    xs = ["Median", "Maximum"]
    ys = [row["ratio_median"], row["ratio_max"]]
    fig = go.Figure(go.Bar(x=xs, y=ys, marker_color=C.COLOR_SAMPLED, text=[f"{y:,.0f}".replace(",", ".") for y in ys], textposition="outside", cliponaxis=False))
    fig.add_hline(y=1, line_dash="dot", line_color="rgba(128,128,128,0.8)", annotation_text="gleichverteilt: 1", annotation_position="top right")
    fig.update_xaxes(type="category")
    fig.update_yaxes(title_text="wahrscheinlichste / unwahrscheinlichste (logarithmisch)", type="log")
    return _base(fig, 330)


def build_estimator_figure(rows):
    """E5: relativer Fehler des Schätzers (Median und Maximum über die Pläne) je Größe."""
    xs = [f"{r['n']} Aufgaben" for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=xs, y=[100 * r["err_median"] for r in rows], name="Median", marker_color=C.COLOR_BAR))
    fig.add_trace(go.Bar(x=xs, y=[100 * r["err_max"] for r in rows], name="Maximum", marker_color=C.COLOR_BAR2))
    fig.update_layout(barmode="group")
    fig.update_xaxes(type="category")
    fig.update_yaxes(title_text="relativer Fehler (%)", rangemode="tozero")
    return _base(fig, 330)


def build_mixing_figure(rows):
    """E6: Totalvariationsabstand des Kettenverfahrens zur Gleichverteilung über die Zahl der Schritte (logarithmische Schrittachse)."""
    fig = go.Figure(go.Scatter(x=[r["steps"] for r in rows], y=[r["tv"] for r in rows], mode="lines+markers", line=dict(color=C.COLOR_BAR), marker=dict(size=9), showlegend=False))
    fig.add_hline(y=0.1, line_dash="dot", line_color="rgba(128,128,128,0.8)", annotation_text="0,1", annotation_position="top right")
    fig.update_xaxes(title_text="Schritte des Kettenverfahrens (logarithmisch)", type="log")
    fig.update_yaxes(title_text="Abstand zur Gleichverteilung (Totalvariation)", rangemode="tozero")
    return _base(fig, 330)


def build_unique_figure(row):
    """E7: Anteil der eindeutigen Ordnungen und Anteil der Pläne, in denen „eindeutig = Hamilton-Pfad“ gilt."""
    xs = ["eindeutige Ordnung", "eindeutig ⇔ Hamilton-Pfad gilt"]
    ys = [100 * row["unique"] / row["instances"], 100 * row["agree"] / row["instances"]]
    fig = go.Figure(go.Bar(x=xs, y=ys, marker_color=[C.COLOR_BAR2, C.COLOR_BAR], text=[f"{y:.0f} %" for y in ys], textposition="outside", cliponaxis=False))
    fig.update_xaxes(type="category")
    fig.update_yaxes(title_text="Anteil der Pläne (%)", range=[0, 112])
    return _base(fig, 330)


def build_spread_figure(rows):
    """E8: Spielraum je Aufgabe (späteste minus früheste mögliche Stelle, Median und Mittel) über den Ausgangsgrad."""
    rows = sorted(rows, key=lambda r: r["out"])
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[r["out"] for r in rows], y=[r["median"] for r in rows], mode="lines+markers", name="Median", line=dict(color=C.COLOR_BAR), marker=dict(size=9)))
    fig.add_trace(go.Scatter(x=[r["out"] for r in rows], y=[r["mean"] for r in rows], mode="lines+markers", name="Mittel", line=dict(color=C.COLOR_BAR2, dash="dash"), marker=dict(size=8, symbol="diamond")))
    fig.update_xaxes(title_text="mittlerer Ausgangsgrad", dtick=1)
    fig.update_yaxes(title_text="Plätze Spielraum je Aufgabe", rangemode="tozero")
    return _base(fig, 330)
