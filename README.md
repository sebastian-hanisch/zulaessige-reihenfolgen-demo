# Zulässige Reihenfolgen – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-zulaessige-reihenfolgen-demo.streamlit.app/)** -->

Siebtes Stück der Reihe **Ordnung und Abhängigkeit** (Arbeitstitel der Linie `dag-abhaengigkeiten`) in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“, Bereich Graphentheorie. Setzt einen **kreisfreien** Plan voraus, wie ihn die Stücke 1 bis 3 liefern (`di-kreis-demo`, `alle-kreise-demo`, `kreise-aufloesen-demo`); derselbe Generator, dieselbe Nummerierung. Die Schranke für die Zahl der Ideale kommt aus der Kettenzerlegung von Stück 6 (`ketten-antiketten-demo`), die Hülle aus Stück 5 (`wege-und-huelle-demo`). Vehikel: **Aufgabenabhängigkeiten** eines Vorhabens. Die Demo fragt: Wie viele Reihenfolgen erlaubt der Plan (so viel Spielraum hat die Planung), wie wählt man eine davon zufällig und fair, und wann ist das Zählen nicht mehr zu bezahlen?

Nachbarn: Eine **einzige** topologische Ordnung liefern Stück 1 und `scc-demo`; hier geht es um ihre **Zahl** und um faires Ziehen. Reihenfolgen mit Maschinen und Zielfunktion gehören in die Scheduling-Linie, kausale DAGs in die Linie Kausale Diagramme.

## Warum dieses Problem

Eine **zulässige Reihenfolge** (lineare Erweiterung) stellt jede Aufgabe nach ihren Vorgängern. Ihre Zahl misst den **Spielraum** der Planung: Eine Kette erlaubt genau eine, n unabhängige Aufgaben erlauben n!. Exakt zählen lässt sich über die **Ideale** (die unter „Vorgänger“ abgeschlossenen Aufgabenmengen), und dieselbe Tabelle liefert das **gleichverteilte Ziehen**. Der naheliegende Zufalls-Kahn (an jeder Stelle gleichverteilt eine verfügbare Aufgabe) zieht dagegen verzerrt. Zählen ist **#P-vollständig**: Bei dünn besetzten Plänen explodiert die Zahl der Ideale, dann bleiben ein **Schätzer** und ein **Kettenverfahren** mit benachbarten Vertauschungen.

## Befunde und Korrekturen gegenüber dem Plan

- **Budget 50 000 statt 300 000 Ideale.** Der Einzelplan hatte die Grenze der exakten Zählung bei 300 000 Idealen gemessen; die Demo setzt sie auf 50 000, damit die Experimente in einer halben Minute rechnen. Dadurch liegen mehr dünn besetzte Pläne über dem Budget (30 Aufgaben, Grad 1: **8 von 8** wie in der Vormessung; 40 Aufgaben, Grad 2: **7 von 8** statt 6 von 10), die Aussage bleibt.
- **Weniger Pläne je Zelle in Experiment 2:** 8 statt 10, aus demselben Grund.
- **Mit dem Demo-Code unverändert:** Verzerrung des Zufalls-Kahn (**102-fach**, Abstand 0,40), Schätzfehler (Median 8 % bei 16 Aufgaben), Mischzeit (Abstand 0,07 nach 100 Schritten), Eindeutigkeit (**400 von 400**), Schranke (**120 von 120**).
- **Zitate:** Nur Brightwell und Winkler (Zählen ist #P-vollständig) sind genannt; die Quellen des Kettenverfahrens und des Schätzers sind nicht geprüft und stehen nicht im Text.

## Modell

Plan wie in den Stücken 1 bis 6 (Aufgaben mit zufälligen Nummern, Beziehungen „A vor B“, hier ohne Widersprüche, also ein DAG). Eine **zulässige Reihenfolge** ist eine Anordnung aller Aufgaben, in der jede Beziehung eingehalten ist; sie entspricht dem Ablauf eines einzelnen Teams, das alle Aufgaben nacheinander erledigt. Zufall kommt aus `random.Random(seed)` mit `random()` (plattformstabil); große Zufallszahlen für das gleichverteilte Ziehen werden aus 52-Bit-Stücken von `random()` zusammengesetzt. Details und Formeln: Expander „📐 Mathematische Formulierung“ in der App.

## Methodik

- **Zählen über die Ideale** (DP): Ideale als Bitmasken, Schicht für Schicht; je Ideal die **Zahl der Wege** vom leeren Ideal (vorwärts) und die **Zahl der Fortsetzungen** bis zur vollen Menge (rückwärts). Über dem **Budget** von 50 000 Idealen bricht die Zählung ab.
- **Gleichverteilt ziehen:** aus dem Ideal die nächste Aufgabe mit Wahrscheinlichkeit (Fortsetzungen danach) / (Fortsetzungen jetzt); jede Reihenfolge hat dann dieselbe Wahrscheinlichkeit.
- **Naiver Zufalls-Kahn:** an jeder Stelle gleichverteilt eine verfügbare Aufgabe; kleine Pläne mit **exakten** Wahrscheinlichkeiten je Reihenfolge.
- **Schätzer:** Produkt der Zahl der verfügbaren Aufgaben längs einer naiven Zufallsordnung (erwartungstreu); 1 000 Proben, relativer Standardfehler aus der Streuung der Proben.
- **Kettenverfahren:** von der Kahn-Ordnung aus je Schritt zufällig zwei benachbarte Aufgaben vertauschen (mit Pause 1/2), wenn keine von der anderen abhängt.
- **Spielraum:** früheste und späteste mögliche Stelle je Aufgabe aus der Hülle; Verteilung der Stelle und Wahrscheinlichkeit „A vor B“ exakt aus der Tabelle; neue Beziehung „A vor B“ lässt genau diesen Anteil der Reihenfolgen übrig.
- **Schranke:** Zahl der Ideale ≤ Produkt (Kettenlänge + 1) über eine kleinste Kettenzerlegung (Stück 6).
- **Unabhängige Prüfer:** Die App prüft jedes Ergebnis vor der Anzeige (jede gezogene Reihenfolge hält jede Beziehung ein, Vorwärts- und Rückwärtszahl der DP stimmen überein, Ideale unter der Schranke, eindeutig genau dann, wenn Hamilton-Pfad, gezogene Stellen innerhalb der Positionsbereiche, Wahrscheinlichkeiten des naiven Verfahrens ergeben eins).

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stehen in `tests/test_claims.py`; Mediane und Zählungen über feste Pläne, nie ein einzelner Zufalls-Seed.

| Frage | Befund |
|---|---|
| Wie viel kleiner als n! ist die Zahl der Reihenfolgen? (10 Pläne je Fall) | Bei 20 Aufgaben und Ausgangsgrad 1 / 2 / 3 / 4: **10.172 / 580,5 / 204,5 / 81,5 Ideale** und 10^13,3 / **10^9,4** / 10^7,0 / 10^5,6 Reihenfolgen gegen 10^18,4 Permutationen (20!); bei 12 Aufgaben 256 / 49 / 23,5 / 17 Ideale und 10^5,6 / 10^3,3 / 10^2,0 / 10^1,0 Reihenfolgen gegen 10^8,7. |
| Wann wird das Zählen unbezahlbar? (8 Pläne je Fall, Budget 50.000 Ideale) | Bei 30 Aufgaben liegt Grad 1 in **8 von 8** Plänen über dem Budget, Grad 2 / 3 / 4 im Median bei 17.346 / 1.994,5 / 547 Idealen; bei 40 Aufgaben sind es bei Grad 1 / 2 / 3 / 4 **8 / 7 / 1 / 0 von 8** Plänen über dem Budget (im Median der Pläne unter dem Budget: Grad 4 2.326 Ideale, Grad 3 9.024 bei sieben Plänen, Grad 2 33.234 bei dem einen Plan). |
| Wie gut ist die Schranke aus der Kettenzerlegung? (20 Aufgaben, 30 Pläne je Grad) | Die Zahl der Ideale liegt in **120 von 120** Plänen unter dem Produkt der (Kettenlänge + 1); die Schranke ist im Median das **4,0- / 9,7- / 14,3- / 11,6-Fache** der tatsächlichen Zahl (Grad 1 bis 4). |
| Ist der naive Zufalls-Kahn gleichverteilt? (20 Pläne, 9 Aufgaben, Grad 1,5, 5 bis 5.000 Reihenfolgen) | Nein: Die wahrscheinlichste Reihenfolge ist im Median das **102-Fache** der unwahrscheinlichsten (höchstens das **432-Fache**), der Abstand zur Gleichverteilung (Totalvariation) beträgt im Median **0,40**. Das Ziehen über die Zähltabelle trifft jede gleich oft. |
| Wie genau ist der Schätzer? (20 Pläne je Größe, Grad 1,5, 1.000 Proben) | Relativer Fehler im Median **3 / 8 / 11 %** bei 12 / 16 / 20 Aufgaben, höchstens **27 / 24 / 55 %**: erwartungstreu, aber bei dünnen Plänen streuend. |
| Wie schnell mischt das Kettenverfahren? (ein Plan mit 7 Aufgaben und 18 Reihenfolgen, 3.000 Läufe je Schrittzahl) | Abstand zur Gleichverteilung nach 7 / 20 / 49 / 100 / 200 / 400 Schritten **0,64 / 0,44 / 0,23 / 0,07 / 0,03 / 0,04**: unter 0,1 erstmals nach 100 Schritten (die letzten beiden Werte liegen im Rauschen der 3.000 Läufe). |
| Wann ist die Ordnung eindeutig? (400 Pläne mit 4 bis 9 Aufgaben) | In **226** Plänen eindeutig; eindeutig genau dann, wenn die Kahn-Ordnung eine Kette von Beziehungen ist (Hamilton-Pfad), in **400 von 400** Fällen. |
| Wie viel Spielraum hat eine Aufgabe? (20 Aufgaben, 20 Pläne je Grad) | Späteste minus früheste mögliche Stelle im Median **16 / 10 / 6 / 4** Plätze bei Grad 1 / 2 / 3 / 4 (Mittel 15,64 / 10,35 / 6,36 / 4,24, höchstens 19 / 19 / 17 / 13). |
| Ist die Rechnung korrekt? | Zahl der Reihenfolgen gleich der Aufzählung von `networkx.all_topological_sorts` auf **100** Plänen (n = 5 bis 9), Aufzählung gleich auf **60**, gleich der Zahl der Permutationen, die alle Beziehungen halten, auf **40** Plänen; Ideale gleich den Teilmengen, die unter Vorgängern abgeschlossen sind (**60** Pläne); Stelle einer Aufgabe, „A vor B“ und Positionsbereiche gleich der Aufzählung (**40** bzw. **60** Pläne); gleichverteiltes Ziehen trifft jede Reihenfolge nahe 1 / e. `tests/test_oracle_zulaessige_reihenfolgen.py` |

## Ehrliche Grenzen

- **Wenige Ideale.** Zählen ist #P-vollständig; bei dünn besetzten Plänen ab etwa 30 Aufgaben übersteigt die Zahl der Ideale das Budget, dann bleibt der Schätzer (Experiment 2).
- **Der Schätzer streut.** Je dünner der Plan, desto stärker; mit 1.000 Proben kann der Fehler 25 % und mehr betragen (Experiment 5).
- **Das Kettenverfahren ist nur gemessen, nicht bewiesen.** Wie viele Schritte genügen, zeigt die Demo an einem kleinen Plan (Experiment 6); die Regler lassen auch zu kurze Läufe zu.
- **Keine Bewertung der Reihenfolgen.** Es gibt keine Kosten, Rüstzeiten oder Maschinen; Zielfunktionen gehören in die Scheduling-Linie.
- **Ein Team, eine Aufgabe nach der anderen.** Parallelität zeigt Stück 6.
- **Zufallspläne** mit 6 bis 40 Aufgaben; echte Pläne sind oft stärker in Schichten gegliedert.
- **Größe:** bis 40 Aufgaben (der Abbruch über dem Budget kostet etwa eine halbe Sekunde), 5.000 gezogene Reihenfolgen.

## Tests

Das Verzeichnis `tests/` enthält zurzeit 145 Tests (Laufzeit etwa eine Minute auf dem Entwicklungsrechner):

- **Kern:** jede Einheit an von Hand gerechneten Mini-Plänen (Kette, unabhängige Aufgaben, Raute, **N-Graph** mit 5 Reihenfolgen und 8 Idealen von Hand aufgezählt, zwei Ketten mit C(4, 2) = 6, Abkürzung); Zählen, Budgetgrenze, beide Ziehverfahren, exakte Wahrscheinlichkeiten des naiven Verfahrens, Erwartungstreue des Schätzers **mit Brüchen exakt** gerechnet, Kettenverfahren, Positionsbereiche, Stelle einer Aufgabe, „A vor B“, Eindeutigkeit, Schranke.
- **Orakel** (`test_oracle_zulaessige_reihenfolgen.py`): `networkx.all_topological_sorts`, Aufzählung aller Permutationen und Teilmengen; Invarianten (unabhängig von der Nummerierung, Abkürzung ändert nichts, eine neue Beziehung zwischen unvergleichbaren Aufgaben entfernt Reihenfolgen und lässt genau den „A vor B“-Anteil übrig, Schätzer im Mittel nahe der Zahl, Kettenverfahren erreicht die Gleichverteilung).
- **Zweige** (`test_branches.py`): jedes Preset löst seine Beschreibung ein (eindeutige Ordnung, fast unbeschränkter Plan, Ideale statt Permutationen, über dem Budget mit Rückfall auf den naiven Zufalls-Kahn, verzerrter Zufalls-Kahn, zu kurzes Kettenverfahren).
- **Verdikte** (`test_verdicts.py`) an handgesetzten Werten; **Befunde** (`test_claims.py`) für jede Zahl dieses README.
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler am Minimum und Maximum), Layout (Schnellstart oben, aktives Preset hervorgehoben), Footer, Laufzeit-Importe, Worst-Case am Reglermaximum (n = 40, dünn bis dicht, 5.000 Züge) ohne Zeit-Assertion.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App: Zählen, Ziehen, Spielraum, acht Experimente |
| `requirements-dev.txt` | Laufzeit plus pytest und networkx (Gegenproben) |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `zrf_algorithm.py` | Kern: Ideale, Zähltabelle, Ziehen (gleichverteilt und naiv), Schätzer, Kettenverfahren, Positionsbereiche, Schranke |
| `zrf_constants.py` | Regler-Grenzen, Ziehverfahren, Budget, Raster der Experimente, Farben, Presets |
| `zrf_evaluation.py` | Analyse, Prüfung vor der Anzeige, Verdikte |
| `zrf_experiments.py` | Experimente über feste Pläne |
| `zrf_layout.py` | Fester Kopf (Stylesheet) |
| `zrf_presets.py` | Permalink, Presets (Schnellstart in der Seitenleiste, aktives Preset hervorgehoben), Zufalls-Seed-Button |
| `zrf_scenario.py` | Pläne mit verdeckter Wunschreihenfolge (derselbe Generator wie in den Stücken 1 bis 6) |
| `zrf_visualization.py` | Plotly-Abbildungen (gezogene Reihenfolge als Bogendiagramm, Stellenverteilung, „A vor B“, Positionsbereiche, Experimente; Achsen gesperrt) |
| `tests/` | Mini-Pläne, Orakel, Zweige, Verdikte, Befunde, Presets, Layout, AppTest, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Bewertung von Reihenfolgen** (Kosten, Rüstzeiten, Maschinen, Hu, Coffman–Graham): Scheduling-Linie.
- **Zähl- und Zufallsverfahren mit Garantie** (schnell mischende Ketten mit bewiesener Schranke, Näherungsschemata): nicht Teil dieses Stücks; die Demo misst nur.
- **Zählen über die Baumweite des Unvergleichbarkeitsgraphen:** nicht Teil dieses Stücks.
- **Echte Pläne oder Dateiimport:** die Pläne sind synthetisch.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly und pandas.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
