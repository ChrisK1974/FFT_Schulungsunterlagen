# Lösungsübersicht zu den Hausaufgaben

## Zweck
Diese Übersicht unterstützt Schulungsleitende sowie Mentorinnen und Mentoren bei der Besprechung der beiden Hausaufgaben. Sie beschreibt erwartete Begründungen und Arbeitsergebnisse, keine verbindlichen projektspezifischen Musterlösungen oder Freigabeentscheidungen.

Bewertet werden fachliche Herleitung, Nachvollziehbarkeit und der Umgang mit Unsicherheit. Gleichwertige Lösungswege sind möglich. Wo die Aufgaben keine konkreten Versionen oder Objektkennungen vorgeben, ist „nachzutragen“ korrekt; erfundene Angaben sind kein Vollständigkeitsnachweis.

---

## Hausaufgabe Tag 1: Erwartete Inhalte

### ESTW L90 Grundverständnis (Teil 1 / Aufgabe 1)
Teilnehmende sollten beschreiben können, dass:
- das ESTW L90 der sicheren Steuerung und Überwachung von Fahrwegen dient,
- die Prüfung projektierter Daten die Umsetzung der anlagenspezifischen Anforderungen anhand der maßgeblichen Planunterlagen, Datenstände und Prüfergebnisse nachweist,
- Änderungen bei Umbauten und Softwarewechseln auch Schnittstellen und unveränderte, aber abhängige Funktionen betreffen können,
- funktionale Prüffragen das geforderte Verhalten betreffen, während sicherungstechnische Prüffragen insbesondere unzulässige Zustände und gefährdende Abläufe betrachten. Beide Perspektiven überschneiden sich: Eine Fahrstraße muss bei erfüllten Voraussetzungen einstellbar sein und bei unzulässigen Voraussetzungen verhindert werden.

Erwartet werden außerdem drei nachvollziehbare Kernaussagen aus dem vereinbarten E-Learning bzw. den Ersatzunterlagen mit Quellenbezug. Die Bewertung setzt keinen nicht bereitgestellten Kurs voraus.

### Flankenschutz (Teil 2 / Aufgabe 2)
Erwartet werden Aussagen dazu, dass:
- Flankenschutz eine Fahrstraße gegen gefährdende seitliche Fahrbewegungen schützt,
- notwendige Schutzmaßnahmen und Abhängigkeiten aus den Planunterlagen abzuleiten sind; räumliche Nachbarschaft allein begründet keine bestimmte Sperrmaßnahme,
- fehlende oder falsch zugeordnete Schutzabhängigkeiten bei einer Änderung zu untersuchen sind,
- eine mögliche Gefährdung benannt werden muss, ohne aus einer fehlenden Anzeige allein auf eine unwirksame Schutzfunktion zu schließen.

Für eine belastbare Bewertung werden unter anderem Fahrweg, mögliche gefährdende Bewegung, vorgesehene Schutzelemente und maßgeblicher Bauzustand benötigt.

### Fallanalyse (Teil 3 / Aufgabe 3)
Gute Antworten beinhalten typischerweise:
- Prüfung von Anforderungsstand, Ausgangszustand, geladenem Datenstand und zulässigem Übungsablauf vor weiteren Bedienhandlungen,
- Unterscheidung zwischen einer annehmbaren Bedienanforderung und einer tatsächlich unzulässigen Fahrstraßenbildung: Die bloße Anforderbarkeit beweist die vermutete Schutzverletzung noch nicht,
- einen positiven und einen negativen Prüffall anhand der vorgegebenen Schutzabhängigkeit,
- getrennte Erfassung von beobachtetem Verhalten und noch unbestätigter Ursache,
- Unterbrechung des betroffenen Prüfschritts und Abstimmung bei ungeklärter Sicherheitswirkung.

**Beispiel für den Prüfplan:** Zunächst den Quellenbezug der Schutzabhängigkeit prüfen; anschließend unter Anleitung im festgelegten Ausgangszustand die zulässige Fahrstraßenbildung und das Verhindern des laut Soll-Vorgabe unzulässigen Ablaufs nachweisen. Die konkrete Bedienfolge muss aus dem freigegebenen Übungsfall stammen.

**Beispiel für eine sachliche Befundformulierung:** „Im vorgegebenen Zustand war die Bedienanforderung für den benachbarten Fahrweg möglich. Laut referenzierter PT1-Vorgabe ist die beschriebene Fahrbewegung auszuschließen. Ob eine Fahrstraße gebildet wird und die Schutzabhängigkeit verletzt ist, ist noch offen.“ Objektkennungen, Stände, Bedienfolge und Belege sind zu ergänzen bzw. als fehlend zu markieren.

### Reflexion (Teil 4 / Aufgabe 4)
Erwartet werden mindestens eine konkrete offene Frage, der zugehörige Unterstützungsbedarf und eine Begründung für szenariobasiertes Lernen. Gute Antworten erläutern, wie sich theoretische Abhängigkeiten erst im Zusammenspiel von Ausgangszustand, Handlung und Reaktion überprüfen lassen.

---

## Hausaufgabe Tag 2: Erwartete Inhalte

### Bedienoberfläche und Zuglenkung (Teil 1 / Aufgabe 1)
Teilnehmende sollten:
- für den gewählten Ablauf Ausgangszustand, Voraussetzungen, Bedienhandlung und erwartete Rückmeldung mit Quellenbezug angeben,
- Anzeigen anhand der geltenden Bedienunterlagen interpretieren, statt allgemeingültige Farben oder Symbole zu unterstellen,
- erläutern, dass Zuglenkung sicherungstechnische Voraussetzungen nicht ersetzt,
- Logs und Anzeigen als Indizien nutzen und mögliche Projektierungs-, System-, Simulations- oder Bedienursachen durch weitere Nachweise unterscheiden.

### Fehlerdokumentation (Teil 2 / Aufgabe 2)
Wichtige Punkte sind:
- Soll-Zustand mit PT1-/Dokumentenreferenz und beobachteter Ist-Zustand ohne vorweggenommene Ursache,
- Prüfobjekt, Bauzustand, Software-/Daten-/Simulationsstände, Ausgangsbedingungen, Bedienfolge und Belege,
- eindeutige Verknüpfung zwischen Prüfprotokoll und JIRA-Vorgang,
- vorläufige Auswirkungsbewertung mit offenem Klärungsbedarf und zuständiger Prüfverantwortung,
- geplanter Nachtest einschließlich korrigiertem Stand und erforderlichen Rückwirkungsprüfungen.

**Bewertungsgrenze:** Eine fehlende Zustandsanzeige am Bedienplatz ist zunächst eine Anzeige- bzw. Verhaltensabweichung. Eine Aussage über die Außenanlage oder die Kritikalität erfordert zusätzliche Nachweise. Eine pauschale Einstufung als „kritisch“ oder „unkritisch“ ist daher keine hinreichende Lösung.

### Tabellenwerte / Fallstudie (Teil 3 / Aufgabe 3)
Erwartet wird insbesondere:
- Vergleich von freigegebenem Soll-Stand, bereitgestellter Projektierung und nachweislich geladenem Stand,
- getrennte Untersuchung von Parameterabweichung und Verhaltensabweichung, solange deren Zusammenhang nicht belegt ist,
- Berücksichtigung von Änderungslisten, Standnachweisen, Simulation und Ausgangsbedingungen,
- Dokumentation bestätigter Befunde, verworfener oder offener Hypothesen und betroffener Folgeprüfungen.

Ein geeigneter Prüfplan enthält beispielsweise:

| Prüffrage | Vorgehen | Aussage / Grenze |
|-----------|----------|------------------|
| Entspricht die bereitgestellte Projektierung dem Soll? | Betroffenen Parameter und Änderungsumfang gegen freigegebene Unterlagen vergleichen | Belegt eine Datenabweichung, noch nicht deren Wirkung |
| Ist der vorgesehene Stand tatsächlich geladen? | Verfügbare Lade- und Standnachweise mit dem Prüfstand abgleichen | Belegt Standzuordnung; Kennung oder Prüfsumme allein beweist keine fachliche Richtigkeit |
| Erklärt die Datenabweichung das Verhalten? | Im genehmigten Prüfaufbau mit definierten Bedingungen und abgestimmtem Vergleichsstand prüfen | Erfordert getrennte Betrachtung anderer Ursachen und dokumentierte Ergebnisse |

### Transfer in die Praxis (Teil 4 / Aufgabe 4)
Erwartet werden drei begründete Prioritäten für die Prüfung, konkrete Unsicherheiten und eine überprüfbare Lernvereinbarung, beispielsweise die Erstellung eines vollständigen Befundeintrags mit anschließendem Mentor-Review.

---

## Hinweise für die Besprechung
Bei der Besprechung sollte besonders darauf geachtet werden:
- ob Fachbegriffe korrekt verwendet werden,
- ob sicherungstechnische Risiken erkannt werden,
- ob Fehler so beschrieben werden, dass sie für andere nachvollziehbar sind,
- ob Teilnehmende zwischen Beobachtung, Bewertung und Schlussfolgerung unterscheiden.

Nutzen Sie pro Arbeitsergebnis die folgenden qualitativen Kriterien; eine Gesamtnote oder formale Befähigung wird daraus nicht abgeleitet:

| Kriterium | Nachvollziehbar erfüllt, wenn … |
|-----------|--------------------------------|
| Fachliche Herleitung | Aussagen aus benannten Anforderungen und gültigen Quellen abgeleitet werden |
| Prüfstrategie | Schritte geeignet sind, die jeweilige Prüffrage zu beantworten und Hypothesen zu unterscheiden |
| Dokumentation | Ausgangszustand, Soll/Ist, Stände, Belege und offene Angaben erkennbar sind |
| Sicherheitsbewusstsein | Aussagegrenzen, Unterbrechungsbedarf und Zuständigkeiten berücksichtigt werden |
| Reflexion | Ein konkreter Lernbedarf mit Maßnahme und überprüfbarem Ergebnis formuliert wird |

Kennzeichnen Sie Kriterien als **erfüllt**, **teilweise erfüllt** oder **noch offen** und halten Sie die Begründung an einem konkreten Beispiel fest.

---

## Empfehlung
Überführen Sie offene Punkte in den Selbstreflexions-Checkpoint und das Feedback-Formular. Vereinbaren Sie gezielte Übungen im dafür freigegebenen ATZ-Aufbau. Ungeklärte Sicherheitsfragen sind vor der nächsten betroffenen praktischen Aufgabe mit der zuständigen Prüfverantwortung zu klären, nicht erst bei einem späteren Feedback-Termin.
