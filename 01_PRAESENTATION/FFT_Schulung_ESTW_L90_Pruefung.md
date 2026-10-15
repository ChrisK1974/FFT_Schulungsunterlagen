# FFT-Schulung: Prüfung projektierter ESTW L90 Daten

## Zweck
Diese Datei bildet die fachliche und didaktische Grundlage der zweitägigen Schulungspräsentation für neue FFT-Mitarbeitende. Sie verbindet die Einführung in ESTW L90 mit angeleiteten Prüfaufgaben im ATZ und der anschließenden Vertiefung im Mentoring.

Nach der Schulung sollen Teilnehmende einfache Prüfszenarien vorbereiten, Soll- und Ist-Zustand vergleichen und Abweichungen nachvollziehbar dokumentieren können. Eigenständige Freigabeentscheidungen sind kein Lernziel der zweitägigen Einführung.

## Geplanter Umfang
Für eine spätere Folienfassung sind etwa 80–100 Folien als Planungsrahmen vorgesehen. Die folgende Gliederung beschreibt die Inhalte; sie stellt noch keinen fertigen Foliensatz dar. Demonstrationen, Übungen und gemeinsame Auswertung erhalten Vorrang vor einer festen Folienzahl.

1. Einführung in ESTW L90
2. Systemarchitektur und Komponenten
3. Sicherungsprinzipien und Flankenschutz
4. Prüfprozesse und Dokumentation
5. Bedienoberfläche und Zuglenkung
6. Fehlerbehandlung und JIRA-Prüfbücher
7. Praktische Übungen im ATZ
8. Fallstudien und Szenarien
9. Mentoring und weitere Entwicklung

### Tag 1: Grundlagen und Sicherungsebene

#### 1. Einführung in ESTW L90
- **Lernziel:** Aufgaben eines elektronischen Stellwerks und Zweck der Prüfung projektierter Daten erläutern.
- **Kerninhalte:** Sicherung von Fahrwegen; anlagenspezifische Projektierung im Unterschied zur generischen Software; Rolle von FFT und ATZ im Prüfprozess.
- **Lernaktivität:** An einem vorbereiteten Beispiel Anforderung, Projektdatum und beobachtetes Verhalten zuordnen.
- **Ergebnissicherung:** In eigenen Worten erklären, weshalb eine plausible Anzeige allein kein ausreichender Sicherheitsnachweis ist.

#### 2. Systemarchitektur und Komponenten
- **Lernziel:** Bedienung, Stellwerkslogik, Schnittstellen und Außenanlage in einem Systemschema einordnen.
- **Kerninhalte:** Befehls- und Meldewege, relevante Komponenten des eingesetzten Systemstands, Simulation im ATZ sowie Grenzen der Prüfumgebung.
- **Lernaktivität:** Den Weg einer Bedienhandlung bis zur Rückmeldung im bereitgestellten Systemschema nachzeichnen.
- **Ergebnissicherung:** Benötigte Software-, Daten- und Simulationsstände für einen reproduzierbaren Prüflauf benennen.

#### 3. Sicherungsprinzipien und Flankenschutz
- **Lernziel:** Sicherungsabhängigkeiten einer Fahrstraße anhand der Planunterlagen begründen.
- **Kerninhalte:** Fahrweg, Fahrstraßenausschlüsse und Flankenschutz; Auswirkungen von Sperrung, Umbau und Wiederinbetriebnahme auf betroffene Abhängigkeiten.
- **Lernaktivität:** Eine Fahrstraße und potenziell gefährdende Fahrbewegungen aus benachbarten Bereichen analysieren. Erforderliche Schutzmaßnahmen aus den PT1-Unterlagen ableiten, nicht pauschal aus räumlicher Nähe.
- **Ergebnissicherung:** Einen positiven Prüffall und einen negativen Prüffall formulieren: Was muss unter definierten Voraussetzungen möglich sein, was muss verhindert werden?
- **Material:** Arbeitsblatt „Sicherungsebene“.

#### 4. Prüfprozesse und Dokumentation
- **Lernziel:** Einen Prüfauftrag in nachvollziehbare Schritte und Nachweise überführen.
- **Kerninhalte:** Prüfgrundlagen und Versionen; Voll- und Differenzprüfung; Rückwirkungen von Änderungen; Zuordnung von Anforderung, Prüfschritt und Ergebnis.
- **Lernaktivität:** Für eine Änderung den betroffenen Prüfumfang einschließlich Schnittstellen begründen und einen Protokolleintrag erstellen.
- **Ergebnissicherung:** Fehlende Voraussetzungen und offene Fragen kenntlich machen, statt sie durch Annahmen zu ersetzen.
- **Material:** Prüfprotokoll-Vorlage, D-Cube-Grundlagen und Hausaufgabe Tag 1.

### Tag 2: Bedienung und praktische Prüfung

#### 5. Bedienoberfläche und Zuglenkung
- **Lernziel:** Bedienhandlungen, Anzeigen und Systemreaktionen im vorbereiteten Szenario unterscheiden.
- **Kerninhalte:** Bedienplatz (BBP), Zustandsanzeigen, Meldungen und Logs; Zuglenkung im Zusammenspiel mit sicherungstechnischen Abhängigkeiten.
- **Lernaktivität:** Ein vereinbartes Szenario unter Anleitung durchlaufen und erwartete sowie tatsächliche Rückmeldungen protokollieren.
- **Ergebnissicherung:** Erklären, warum Zuglenkung keine sicherungstechnischen Voraussetzungen ersetzt und eine Anzeigeabweichung zunächst eine Beobachtung ist.
- **Material:** Arbeitsblatt „Bedienoberfläche“.

#### 6. Fehlerbehandlung und JIRA-Prüfbücher
- **Lernziel:** Eine Abweichung reproduzierbar beschreiben und ihre weitere Bearbeitung vorbereiten.
- **Kerninhalte:** Soll-/Ist-Vergleich, Reproduktionsschritte, Belege, vorläufige Auswirkungsbewertung, Zuständigkeit und Nachtest; Trennung von Befund und Ursachenhypothese.
- **Lernaktivität:** Eine fehlende Anzeige nach Softwarewechsel als Übungsbefund dokumentieren und mit dem Prüfschritt verknüpfen.
- **Ergebnissicherung:** Die Gruppe prüft, ob eine andere Person den Befund anhand des Eintrags nachvollziehen kann.
- **Material:** JIRA-Prüfbuch-Anleitung und Fehlerbehandlungs-Checkliste.

#### 7. Praktische Übungen im ATZ
- **Lernziel:** Vorbereitung, Durchführung und Ergebnissicherung als zusammenhängenden Prüfablauf anwenden.
- **Szenarien:** Sperrung einer Fahrstraße, Softwarewechsel sowie Wiederinbetriebnahme nach Umbau, jeweils im freigegebenen Übungsaufbau.
- **Arbeitsauftrag:** Prüfgrundlage und Ausgangszustand festhalten, Soll-Ergebnis ableiten, vereinbarte Prüfschritte durchführen und Abweichungen dokumentieren.
- **Ergebnissicherung:** Pro Szenario mindestens einen begründeten Soll-/Ist-Vergleich sowie offene Punkte und erforderliche Nachtests vorstellen.

#### 8. Fallstudien und Szenarien
- **Lernziel:** Mögliche Ursachen eingrenzen, ohne aus Einzelbeobachtungen voreilige Schlüsse zu ziehen.
- **Kerninhalte:** Nicht umgesetzte PT1-Anforderungen, abweichende Tabellenwerte, fehlende Signalisierung und unvollständige Nachweise.
- **Lernaktivität:** In Kleingruppen einen Befund analysieren: Welche Fakten liegen vor? Welche Hypothesen bestehen? Welcher zusätzliche Prüfschritt unterscheidet diese?
- **Ergebnissicherung:** Prüfstrategie, Nachweise und Grenzen der Aussagekraft gemeinsam bewerten.
- **Material:** Hausaufgabe Tag 2 und Lösungsübersicht für die anschließende Besprechung.

### 9. Mentoring und weitere Entwicklung
- **Lernziel:** Den eigenen Lernstand einschätzen und einen konkreten nächsten Entwicklungsschritt vereinbaren.
- **Kerninhalte:** Zwölfmonatiger Rahmen mit Beobachtung, Co-Prüfer-Rolle und definierten eigenständigen Prüfaufgaben mit Mentor-Review.
- **Lernaktivität:** Selbstreflexions-Checkpoint ausfüllen und eine Lernvereinbarung mit überprüfbarem Nachweis formulieren.
- **Ergebnissicherung:** Aufgabe, Unterstützung und Review-Termin im Feedback-Formular festhalten.

## Hinweis
Die Schulungsleitung ergänzt vor Einsatz die gültigen Quellenstände, projektspezifischen Beispiele und freigegebenen Übungsdaten. Konkrete Bedienfolgen und Werkzeugfunktionen sind anhand der eingesetzten Version zu demonstrieren; diese Gliederung legt keine internen Prozess- oder Freigaberegeln fest.

Übungen erfolgen ausschließlich im dafür vorgesehenen Prüfaufbau unter Anleitung. Bei unklarer Sicherheitswirkung wird der betroffene Prüfschritt unterbrochen und die zuständige Prüfverantwortung einbezogen. Eine spätere `.pptx`-Fassung kann aus dieser Markdown-Grundlage abgeleitet werden.
