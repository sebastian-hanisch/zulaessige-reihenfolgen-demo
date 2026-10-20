"""Zulässige Reihenfolgen - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Siebtes Stück der Reihe „Ordnung und Abhängigkeit“: Wie viele Reihenfolgen erlaubt ein Plan (Spielraum), wie wählt man eine davon zufällig und fair, und wann ist das Zählen nicht mehr zu bezahlen?
Zählen über die Ideale, gleichverteiltes Ziehen, der naive Zufalls-Kahn, ein Schätzer und das Kettenverfahren mit benachbarten Vertauschungen.

Lauffähig mit: streamlit run app.py
"""

import math

import pandas as pd
import streamlit as st

import zrf_algorithm as A
import zrf_constants as C
import zrf_evaluation as ev
import zrf_experiments as ex
from zrf_layout import dunkles_design, kopf_css
from zrf_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from zrf_visualization import (
    build_before_figure,
    build_bound_figure,
    build_bounds_figure,
    build_density_figure,
    build_estimator_figure,
    build_mixing_figure,
    build_naive_figure,
    build_order_figure,
    build_permutations_figure,
    build_position_figure,
    build_spread_figure,
    build_unique_figure,
)

st.set_page_config(page_title="Zulässige Reihenfolgen – Sebastian Hanisch", layout="wide")

_i, _dec, _big = ev._i, ev._dec, ev._big


def _show(verdict):
    kind, text = verdict
    {"success": st.success, "info": st.info, "warning": st.warning}[kind](text)


@st.cache_resource(show_spinner=False, max_entries=12)
def _analysis(settings):
    return ev.analyse(settings)


@st.cache_data(show_spinner=False)
def _permutations():
    return ex.ideals_vs_permutations_rows()


@st.cache_data(show_spinner=False)
def _density():
    return ex.ideals_vs_density_rows()


@st.cache_data(show_spinner=False)
def _bound():
    return ex.bound_rows()


@st.cache_data(show_spinner=False)
def _naive():
    return ex.naive_rows()


@st.cache_data(show_spinner=False)
def _estimator():
    return ex.estimator_rows()


@st.cache_data(show_spinner=False)
def _mixing():
    return ex.mixing_rows()


@st.cache_data(show_spinner=False)
def _unique():
    return ex.unique_rows()


@st.cache_data(show_spinner=False)
def _spread():
    return ex.spread_rows()


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in zrf_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🔀 Zulässige Reihenfolgen")
st.markdown(
    """
Eine **zulässige Reihenfolge** stellt jede Aufgabe nach ihren Vorgängern; die Zahl solcher Reihenfolgen misst den **Spielraum** der Planung: Eine Kette erlaubt genau eine, n unabhängige Aufgaben erlauben n!.
Exakt zählen lässt sich über die **Ideale** (die unter „Vorgänger“ abgeschlossenen Aufgabenmengen), und dieselbe Tabelle liefert das **gleichverteilte Ziehen**; der naheliegende Zufalls-Kahn dagegen zieht verzerrt.
Zählen ist **#P-vollständig**: Bei dünn besetzten Plänen explodiert die Zahl der Ideale, dann bleiben ein **Schätzer** und ein **Kettenverfahren** mit benachbarten Vertauschungen.

Das ist das siebte Stück der Reihe **Ordnung und Abhängigkeit** (Stücke 1 bis 6: **di-kreis-demo**, **alle-kreise-demo**, **kreise-aufloesen-demo**, **kritischer-pfad-demo**, **wege-und-huelle-demo**, **ketten-antiketten-demo**);
die Schranke für die Zahl der Ideale kommt aus der Kettenzerlegung von Stück 6. Weiter unten: die Experimente **🔬**, **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So zählt und zieht man zulässige Reihenfolgen", expanded=True):
    st.markdown(
        """
1. **Ideal:** Eine Menge von Aufgaben, die mit jeder Aufgabe auch alle ihre Vorgänger enthält. Jede zulässige Reihenfolge baut Schritt für Schritt ein Ideal auf, von der leeren Menge bis zu allen Aufgaben.
2. **Zählen:** Für jedes Ideal zählt man die Wege vom leeren Ideal hierher (vorwärts) und die Fortsetzungen bis zum vollen Ideal (rückwärts). Die Zahl der Reihenfolgen ist die Fortsetzungszahl des leeren Ideals; gerechnet wird nur über die Ideale, nicht über alle n! Permutationen.
3. **Gleichverteilt ziehen:** Aus dem aktuellen Ideal wählt man die nächste Aufgabe mit Wahrscheinlichkeit (Fortsetzungen danach) / (Fortsetzungen jetzt). Dann hat jede Reihenfolge dieselbe Wahrscheinlichkeit 1 / (Zahl der Reihenfolgen).
4. **Naiver Zufalls-Kahn:** An jeder Stelle gleichverteilt eine der verfügbaren Aufgaben nehmen. Das ist einfach, aber verzerrt: Reihenfolgen durch Stellen mit wenigen Alternativen werden bevorzugt.
5. **Schätzer:** Das Produkt der Zahl der verfügbaren Aufgaben längs einer naiven Zufallsordnung hat als Erwartungswert genau die Zahl der Reihenfolgen. Es streut stark, rechnet aber auch dort, wo die Tabelle zu groß wird.
6. **Kettenverfahren:** Man startet mit einer zulässigen Reihenfolge und vertauscht immer wieder zufällig zwei benachbarte Aufgaben, wenn keine von der anderen abhängt. Nach genug Schritten ist die Reihenfolge nahezu gleichverteilt; wie viele Schritte genug sind, misst die Demo.
7. **Spielraum:** Die früheste Stelle einer Aufgabe ist die Zahl ihrer Vorgänger plus eins, die späteste n minus die Zahl ihrer Nachfolger. Eine neue Beziehung „A vor B“ lässt genau den Anteil der Reihenfolgen übrig, in denen A ohnehin vor B steht.

| Begriff | Bedeutung |
|---|---|
| **Zulässige Reihenfolge** | Anordnung aller Aufgaben, in der jede nach ihren Vorgängern steht (lineare Erweiterung) |
| **Ideal** | Aufgabenmenge, die mit jeder Aufgabe ihre Vorgänger enthält |
| **Spielraum** | Zahl der zulässigen Reihenfolgen, oder je Aufgabe die Spanne ihrer möglichen Stellen |
| **#P-vollständig** | Das Zählen ist so schwer wie das Zählen aller Lösungen eines NP-Problems |
| **Gleichverteilt** | Jede zulässige Reihenfolge kommt mit derselben Wahrscheinlichkeit vor |
| **Totalvariation** | Halbe Summe der Abweichungen zweier Verteilungen: 0 gleich, 1 völlig verschieden |
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Plan**")
    n = st.slider("Aufgaben n", *bounds("n_slider"), key="n_slider", help="Wie viele Aufgaben der Plan hat (kreisfrei).")
    out = st.slider("Beziehungen je Aufgabe", *bounds("out_slider"), key="out_slider", step=C.OUT_STEP, help="Mittlerer Ausgangsgrad: Zahl der Beziehungen „A vor B“ geteilt durch die Zahl der Aufgaben. Je dünner, desto mehr Ideale.")
    seed = st.number_input("Zufalls-Seed des Plans", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neuen Plan erzeugen", width="stretch", on_click=randomize_seed)
    st.markdown("**Ziehen**")
    sampler = st.selectbox("Ziehverfahren", list(C.SAMPLERS), format_func=C.SAMPLER_NAMES.get, key="sampler_select",
                           help="Gleichverteilt braucht die exakte Zähltabelle; über dem Budget an Idealen fällt die Demo auf den naiven Zufalls-Kahn zurück.")
    draws = st.selectbox("Gezogene Reihenfolgen", list(C.DRAWS), format_func=_i, key="draws_select", help="Wie viele Reihenfolgen mit dem Ziehverfahren gezogen werden.")
    steps = st.selectbox("Schritte des Kettenverfahrens", list(C.STEPS), format_func=_i, key="steps_select", help="Wie viele zufällige Vertauschungen das Kettenverfahren je gezogener Reihenfolge ausführt.")

sync_query_params({"n_slider": int(n), "out_slider": float(out), "seed_input": int(seed), "sampler_select": sampler, "draws_select": int(draws), "steps_select": int(steps)})

settings = ev.Settings(int(n), float(out), int(seed), sampler, int(draws), int(steps))
with st.spinner("Zähle und ziehe..."):
    a = _analysis(settings)
inst = a.inst
problems = ev.validate(a)
for p in problems:
    st.error(f"Prüfung fehlgeschlagen: {p}")
signature = f"{inst.n}_{settings.out}_{settings.seed}"

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis")
st.caption(f"{_i(inst.n)} Aufgaben, {_i(inst.m)} Beziehungen. Aufgaben sind ab 1 nummeriert. Das Budget für die exakte Zählung sind {_i(C.IDEAL_BUDGET)} Ideale.")
m1, m2, m3, m4 = st.columns(4)
if a.exceeded:
    m1.metric("Zulässige Reihenfolgen", "über dem Budget", delta=f"geschätzt etwa {_big(a.estimate)}", delta_color="off")
else:
    m1.metric("Zulässige Reihenfolgen", _big(a.extensions), delta=f"von {_big(math.factorial(a.n))} Permutationen", delta_color="off")
m2.metric("Ideale", (">" if a.exceeded else "") + _i(C.IDEAL_BUDGET if a.exceeded else a.ideals), delta=f"Schranke {_big(a.bound)}", delta_color="off")
m3.metric("Spielraum je Aufgabe (Median)", f"{_dec(a.spread_median)} Plätze", delta="späteste minus früheste Stelle", delta_color="off")
m4.metric("Ordnung", "eindeutig" if a.unique else ("nicht eindeutig" if not a.exceeded else "sehr viele"), delta="Hamilton-Pfad der Beziehungen" if a.hamilton else "kein Hamilton-Pfad", delta_color="off")

tab_count, tab_draw, tab_room = st.tabs(["🔢 Zählen", "🎲 Ziehen", "🧭 Spielraum"])

# --- Tab 1: Zählen -------------------------------------------------------------------------------------------------------------------------

with tab_count:
    if not a.n:
        st.info("Der Plan ist leer.")
    elif a.exceeded:
        st.warning(f"Der Plan hat mehr als {_i(C.IDEAL_BUDGET)} Ideale: Die exakte Zählung (und damit das gleichverteilte Ziehen) bricht ab. Zählen ist #P-vollständig; bei dünn besetzten Plänen mit vielen unabhängigen Aufgaben wächst die Zahl der Ideale "
                   f"wie das Produkt der Kettenlängen plus eins (hier höchstens {_big(a.bound)}).")
        e1, e2, e3 = st.columns(3)
        e1.metric("Geschätzte Zahl der Reihenfolgen", _big(a.estimate), delta=f"{_i(C.ESTIMATE_SAMPLES)} Proben", delta_color="off")
        e2.metric("Relativer Standardfehler", f"{_dec(100 * a.estimate_rel_se)} %", delta="der Schätzung", delta_color="off")
        e3.metric("Zehnerlogarithmus", _dec(a.log_ext, 1), delta=f"n! hat {_dec(a.log_fact, 1)}", delta_color="off")
        st.caption("Der Schätzer multipliziert längs einer naiven Zufallsordnung die Zahl der verfügbaren Aufgaben; er ist erwartungstreu, streut aber bei dünnen Plänen stark (Experiment 5).")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Anteil an allen Permutationen", f"10^{_dec(a.log_ext - a.log_fact, 1)}", delta="Reihenfolgen gegen n!", delta_color="off")
        c2.metric("Zustände der DP", _i(a.ideals), delta=f"statt {_big(math.factorial(a.n))} Permutationen", delta_color="off")
        c3.metric("Schätzer (1 000 Proben)", _big(a.estimate), delta=f"{_dec(100 * abs(a.estimate - a.extensions) / a.extensions)} % neben der exakten Zahl", delta_color="inverse")
        st.plotly_chart(build_permutations_figure([{"n": a.n, "out": settings.out, "log_fact": a.log_fact, "log_ext": a.log_ext, "ideals": a.ideals}]), width="stretch", key="chart_plan_count")
        st.caption("Zehnerlogarithmus: Der Plan erlaubt weit weniger Reihenfolgen als Permutationen, und die DP rechnet mit noch viel weniger Zuständen (Idealen).")
        st.markdown(f"**Schranke:** Ein Ideal enthält von jeder Kette einer kleinsten Zerlegung (Stück 6, Längen {', '.join(_i(k) for k in A.kuhn_chain_lengths(a.adj))}) einen Anfang, also gibt es höchstens {_big(a.bound)} Ideale; es sind {_i(a.ideals)}.")

# --- Tab 2: Ziehen -------------------------------------------------------------------------------------------------------------------------

with tab_draw:
    if not a.n:
        st.info("Der Plan ist leer.")
    else:
        if a.fallback:
            st.warning("Das gleichverteilte Ziehen braucht die exakte Zähltabelle; sie fehlt über dem Budget. Gezogen wird stattdessen mit dem naiven Zufalls-Kahn (verzerrt).")
        st.markdown(f"**Verfahren:** {C.SAMPLER_NAMES[a.sampler_used]}" + (f", {_i(settings.steps)} Schritte je Reihenfolge" if a.sampler_used == "chain" else "") + f"; {_i(len(a.draws))} Reihenfolgen gezogen.")
        number = st.number_input("Welche gezogene Reihenfolge zeigen?", 1, len(a.draws), 1, key=f"draw_no_{signature}_{settings.sampler}_{settings.draws}", step=1)
        order = a.draws[int(number) - 1]
        st.plotly_chart(build_order_figure(inst, order), width="stretch", key="arc_order")
        st.markdown("**Reihenfolge:** " + ev.format_order(order, 24))
        task = st.selectbox("Aufgabe", list(range(a.n)), key=f"draw_task_{signature}", format_func=ev.label, help="Wo steht diese Aufgabe in den gezogenen Reihenfolgen?")
        dist = ev.position_distribution(a, task)
        if dist["exact"] is not None:
            tv = ev.tv_distance(dist["exact"], dist["sampled"])
            d1, d2 = st.columns(2)
            d1.metric("Abstand zur Gleichverteilung (Stelle der Aufgabe)", _dec(tv, 2), delta="Totalvariation, gezogen gegen exakt", delta_color="inverse")
            if a.naive_ratio is not None:
                d2.metric("Naiver Zufalls-Kahn: wahrscheinlichste / unwahrscheinlichste", f"{_dec(a.naive_ratio)}-fach", delta="exakt gerechnet (kleine Pläne)", delta_color="off")
        st.plotly_chart(build_position_figure(dist["exact"], dist["sampled"], C.SAMPLER_NAMES[a.sampler_used]), width="stretch", key="chart_positions")
        st.caption("Anteil der Reihenfolgen, in denen die gewählte Aufgabe an Stelle p steht. Wo das Ziehverfahren gleichverteilt ist, decken sich die Balken mit der exakten Verteilung; der naive Zufalls-Kahn und ein zu kurzes Kettenverfahren weichen sichtbar ab.")

# --- Tab 3: Spielraum ----------------------------------------------------------------------------------------------------------------------

with tab_room:
    if not a.n:
        st.info("Der Plan ist leer.")
    else:
        if a.table is not None:
            expected = [sum((p + 1) * c for p, c in enumerate(A.position_counts(a.adj, a.table, v))) / a.extensions for v in range(a.n)]
            source = "exakt"
        else:
            expected = [sum(o.index(v) + 1 for o in a.draws) / len(a.draws) for v in range(a.n)]
            source = "aus den gezogenen Reihenfolgen geschätzt"
        st.plotly_chart(build_bounds_figure(a.bounds, expected), width="stretch", key="chart_bounds")
        st.caption(f"Balken: früheste bis späteste mögliche Stelle einer Aufgabe (Zahl der Vorgänger + 1 bis n minus Zahl der Nachfolger). Rauten: erwartete Stelle, {source}.")
        if a.unique:
            st.success("Die Ordnung ist eindeutig: Jede Aufgabe hat genau eine mögliche Stelle, die Balken sind Punkte.")
        st.markdown("#### Eine Abhängigkeit mehr: was bleibt übrig?")
        task2 = st.selectbox("Aufgabe A", list(range(a.n)), key=f"room_task_{signature}", format_func=ev.label, help="A soll künftig vor B stehen: Wie viele Reihenfolgen bleiben?")
        before = ev.before_distribution(a, task2)
        values = before["exact"] if before["exact"] is not None else before["sampled"]
        reach = A.closure_bits(a.adj)
        comparable = {b for b in range(a.n) if b != task2 and ((reach[task2] >> b) & 1 or (reach[b] >> task2) & 1)}
        free = sorted((b for b in range(a.n) if b != task2 and b not in comparable), key=lambda b: (values[b], b))
        st.plotly_chart(build_before_figure(before["exact"], before["sampled"], task2, comparable), width="stretch", key="chart_before")
        st.caption("Anteil der Reihenfolgen, in denen A vor B steht. Für Aufgaben, die mit A zusammenhängen, ist der Anteil 0 oder 100 %; zwischen unabhängigen Aufgaben bleibt genau dieser Anteil übrig, wenn man „A vor B“ verlangt.")
        if free:
            rows = [{"B": ev.label(b), "Anteil mit A vor B (%)": round(100 * values[b], 1), "Reihenfolgen danach": _big(round(values[b] * a.extensions)) if a.extensions is not None else "–"} for b in free[:12]]
            st.markdown(f"**Die stärksten neuen Beziehungen von Aufgabe {ev.label(task2)} aus** ({'exakt' if before['exact'] is not None else 'geschätzt'}):")
            st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        else:
            st.info(f"Aufgabe {ev.label(task2)} ist mit jeder anderen Aufgabe vergleichbar: Eine neue Beziehung ändert nichts.")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Wie viel Spielraum hat der Plan, und wie wählt man fair eine Reihenfolge?")
_show(ev.verdict_question(a))

st.markdown("---")

# --- Experimente ---------------------------------------------------------------------------------------------------------------------------

with st.spinner("Rechne die Experimente (einmalig, etwa eine halbe Minute)..."):
    rows_pm, rows_dn, rows_bd, row_nv, rows_es, rows_mx, row_un, rows_sp = _permutations(), _density(), _bound(), _naive(), _estimator(), _mixing(), _unique(), _spread()

st.subheader("🔬 Experiment 1: Wie viel kleiner als n! ist die Zahl der Reihenfolgen?")
st.caption(f"Je Fall {len(C.E1_SEEDS)} feste Pläne; Median. Zehnerlogarithmen von n!, der Zahl der Reihenfolgen und der Zahl der Ideale.")
st.plotly_chart(build_permutations_figure(rows_pm), width="stretch", key="chart_permutations")
_show(ev.verdict_permutations(rows_pm))

st.subheader("🔬 Experiment 2: Wann wird das Zählen unbezahlbar?")
st.caption(f"Je Fall {len(C.E2_SEEDS)} feste Pläne; Median der Pläne unter dem Budget von {_i(C.IDEAL_BUDGET)} Idealen, Raute = Pläne über dem Budget.")
st.plotly_chart(build_density_figure(rows_dn), width="stretch", key="chart_density")
_show(ev.verdict_density(rows_dn))

st.subheader("🔬 Experiment 3: Wie gut ist die Schranke aus der Kettenzerlegung?")
st.caption(f"{C.E3_N} Aufgaben, je Fall {len(C.E3_SEEDS)} feste Pläne; Verhältnis von Schranke (Produkt der Kettenlängen plus eins) zur tatsächlichen Zahl der Ideale, Median.")
st.plotly_chart(build_bound_figure(rows_bd), width="stretch", key="chart_bound")
_show(ev.verdict_bound(rows_bd))

st.subheader("🔬 Experiment 4: Ist der naive Zufalls-Kahn gleichverteilt?")
st.caption(f"{row_nv['instances']} Pläne mit {C.E4_N} Aufgaben (Ausgangsgrad {_dec(C.E4_OUT)}) und {C.E4_RANGE[0]} bis {C.E4_RANGE[1]} Reihenfolgen; exakte Wahrscheinlichkeiten je Reihenfolge.")
st.plotly_chart(build_naive_figure(row_nv), width="stretch", key="chart_naive")
_show(ev.verdict_naive(row_nv))

st.subheader("🔬 Experiment 5: Wie genau ist der Schätzer?")
st.caption(f"Je Größe {len(C.E5_SEEDS)} feste Pläne mit Ausgangsgrad {_dec(C.E5_OUT)}, {_i(C.ESTIMATE_SAMPLES)} Proben; Abweichung von der exakten Zahl.")
st.plotly_chart(build_estimator_figure(rows_es), width="stretch", key="chart_estimator")
_show(ev.verdict_estimator(rows_es))

st.subheader("🔬 Experiment 6: Wie schnell mischt das Kettenverfahren?")
st.caption(f"Ein fester Plan mit {C.E6_N} Aufgaben, {_i(C.E6_RUNS)} Läufe je Schrittzahl, Start bei der Kahn-Ordnung; Abstand der Verteilung der Endreihenfolge zur Gleichverteilung.")
st.plotly_chart(build_mixing_figure(rows_mx), width="stretch", key="chart_mixing")
_show(ev.verdict_mixing(rows_mx))

st.subheader("🔬 Experiment 7: Wann ist die Ordnung eindeutig?")
st.caption(f"{C.E7_PLANS} kleine Pläne mit {C.E7_NMIN} bis {C.E7_NMIN + C.E7_NSPAN - 1} Aufgaben und Ausgangsgrad 1 bis 4.")
st.plotly_chart(build_unique_figure(row_un), width="stretch", key="chart_unique")
_show(ev.verdict_unique(row_un))

st.subheader("🔬 Experiment 8: Wie viel Spielraum hat eine einzelne Aufgabe?")
st.caption(f"{C.E8_N} Aufgaben, je Ausgangsgrad {len(C.E8_SEEDS)} feste Pläne; späteste minus früheste mögliche Stelle über alle Aufgaben aller Pläne.")
st.plotly_chart(build_spread_figure(rows_sp), width="stretch", key="chart_spread")
_show(ev.verdict_spread(rows_sp))

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    f"""
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Wenige Ideale** | Zählen ist #P-vollständig. Bei dünn besetzten Plänen ab etwa 30 Aufgaben übersteigt die Zahl der Ideale das Budget von {_i(C.IDEAL_BUDGET)}; dann bleibt der Schätzer. | - |
| **Schätzer mit hoher Streuung** | Je dünner der Plan, desto stärker streut das Produkt der Auswahlgrößen; mit {_i(C.ESTIMATE_SAMPLES)} Proben kann der Fehler 25 % und mehr betragen (Experiment 5). | - |
| **Kettenverfahren ohne Schranke** | Wie viele Schritte genügen, wird hier an kleinen Plänen gemessen, nicht bewiesen; die Regler lassen auch zu kurze Läufe zu. | Literatur zu schnell mischenden Ketten |
| **Alle Reihenfolgen gleich gut** | Die Demo bewertet keine Reihenfolge (keine Kosten, Rüstzeiten, Maschinen); Zielfunktionen gehören in die Scheduling-Linie. | Scheduling-Linie |
| **Ein Team, eine Aufgabe nach der anderen** | Eine Reihenfolge ist ein Ablauf für ein einzelnes Team; Parallelität zeigt Stück 6. | Stück 6 |
| **Zufallspläne** | Die Zahlen gelten für diese Pläne mit {C.N_MIN} bis {C.N_MAX} Aufgaben; echte Pläne sind oft schichtiger. | - |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Gegeben** eine endliche Ordnung $(V, \preceq)$ aus den Aufgaben; eine **zulässige Reihenfolge** (lineare Erweiterung) ist eine Anordnung $\sigma$ aller Aufgaben mit $a \prec b \Rightarrow \sigma(a) < \sigma(b)$.

| Symbol | Bedeutung |
|---|---|
| $e(P)$ | Zahl der zulässigen Reihenfolgen |
| $\mathcal{I}(P)$ | Menge der Ideale (unter Vorgängern abgeschlossene Mengen) |
| $f(I)$ | Zahl der Wege von $\emptyset$ zum Ideal $I$ |
| $g(I)$ | Zahl der Fortsetzungen von $I$ zu $V$ |

**Zählen über die Ideale.** Mit $f(\emptyset) = 1$ und $g(V) = 1$:

$$f(I) = \sum_{v \in I,\; I \setminus \{v\} \in \mathcal{I}} f(I \setminus \{v\}), \qquad g(I) = \sum_{v \notin I,\; I \cup \{v\} \in \mathcal{I}} g(I \cup \{v\}), \qquad e(P) = g(\emptyset) = f(V).$$

**Gleichverteilt ziehen.** Aus dem Ideal $I$ wählt man die nächste Aufgabe $v$ mit Wahrscheinlichkeit

$$\Pr[v \mid I] = \frac{g(I \cup \{v\})}{g(I)};$$

dann hat jede Reihenfolge die Wahrscheinlichkeit $1 / e(P)$.

**Stelle einer Aufgabe und „A vor B“.** Die Zahl der Reihenfolgen, in denen $v$ an Stelle $p$ steht, ist die Summe über die Ideale $I$ mit $|I| = p - 1$, $v \notin I$ und $I \cup \{v\} \in \mathcal{I}$:

$$e_p(v) = \sum_{I} f(I)\, g(I \cup \{v\}).$$

Verlangt man zusätzlich $a \prec b$ für unvergleichbare $a, b$, bleiben genau die Reihenfolgen mit $a$ vor $b$ übrig, also $e(P + (a \prec b)) = e(P) \cdot \Pr[a \text{ vor } b]$.

**Schätzer.** Wählt man bei jedem Schritt gleichverteilt aus den $d_t$ verfügbaren Aufgaben, hat eine Reihenfolge die Wahrscheinlichkeit $\prod_t 1/d_t$; die Probe $X = \prod_t d_t$ ist deshalb erwartungstreu:

$$\mathbb{E}[X] = \sum_{\sigma} \Pr[\sigma] \prod_t d_t(\sigma) = e(P).$$

**Schranke für die Ideale.** Zerlegt man $P$ in $w$ Ketten der Längen $\ell_1, \dots, \ell_w$ (Stück 6), wählt ein Ideal aus jeder Kette einen Anfang:

$$|\mathcal{I}(P)| \le \prod_{k=1}^{w} (\ell_k + 1).$$

**Eindeutigkeit.** $e(P) = 1$ gilt genau dann, wenn die Beziehungen einen Hamilton-Pfad enthalten, also je zwei aufeinanderfolgende Aufgaben der Kahn-Ordnung unmittelbar verbunden sind.

**Literatur.** G. Brightwell und P. Winkler: *Counting linear extensions*, Order 8, 1991 (Zählen ist #P-vollständig). Die DP über die Ideale ist Lehrbuchwissen; die Tests belegen sie gegen networkx und Aufzählung. Quellen für das Kettenverfahren und den Schätzer sind nicht geprüft und werden hier nicht zitiert.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
