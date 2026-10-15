# ESTW L90: Glossar

## Zweck
Dieses Glossar erläutert zentrale Begriffe der Schulung zur Prüfung projektierter ESTW L90 Daten. Es dient der einheitlichen Verwendung in Präsentation, Aufgaben und Mentoring. Projektspezifische Definitionen und gültige Regelwerke haben Vorrang.

**Sprachliche Konvention:** „Befund“ bezeichnet eine dokumentierte Beobachtung bzw. Abweichung; eine vermutete Ursache wird als Hypothese gekennzeichnet. „Sperrung einer Fahrstraße“ und „Wiederinbetriebnahme“ bezeichnen im Übungskontext den jeweils festgelegten Prüfzustand und keine allgemeingültige Bedienfolge.

---

## Begriffe

### ATZ
**Anlagen Test Zentrum** – Umgebung, in der projektierte Daten, Softwarestände und Prüfszenarien getestet und nachvollzogen werden können.

Die Aussagekraft eines ATZ-Ergebnisses hängt vom dokumentierten Aufbau, den verwendeten Ständen und den Grenzen der Simulation ab.

### Bauzustand / Anlagenzustand
Eindeutig abgegrenzter Zustand einer Anlage mit zugehörigen Planunterlagen, Software- und Projektierungsständen. Ausgangs- und Zielzustand müssen für die Prüfung unterscheidbar dokumentiert sein.

### Bedienplatz / BBP
Arbeitsplatz mit Bedienoberfläche, über den Stellwerksfunktionen beobachtet und zulässige Bedienhandlungen ausgeführt werden. Die im Repository verwendete Bezeichnung **BBP** wird hier als Bedienplatz geführt; die genaue Systemausprägung ist projektbezogen zu klären.

### Befund / Fehler
Ein Befund hält beobachtetes Verhalten und gegebenenfalls die Abweichung von einer belegten Soll-Vorgabe fest. Ein bestätigter Fehler wird anhand weiterer Prüfung eingeordnet. Beobachtung, Ursachenhypothese und Bewertung sind getrennt zu dokumentieren.

### D-Cube
Im Referenzmaterial im Zusammenhang mit Prüfschritten und Prüfprotokollen für Inlandsprojekte beschriebenes Werkzeug. Konkreter Funktionsumfang, Bedienung und Rollenrechte richten sich nach dem eingesetzten Stand und der gültigen Anweisung. Siehe [D-Cube-Grundlagen](../02_ARBEITSBL%C3%84TTER/08_D-Cube_Grundlagen.md).

### Differenzprüfung
Prüfung eines gegenüber einem dokumentierten Ausgangszustand geänderten Zielzustands mit begründet abgegrenztem Umfang. Neben direkten Änderungen sind betroffene Abhängigkeiten, Schnittstellen und mögliche Rückwirkungen zu betrachten. „Nur Änderungen prüfen“ bedeutet nicht, unveränderte, aber beeinflusste Funktionen ohne Bewertung auszuschließen.

### ESTW
**Elektronisches Stellwerk** – System zur Steuerung und sicherungstechnischen Überwachung von Fahrwegen und den zugehörigen Elementen im Eisenbahnbetrieb.

### ESTW L90
Die in dieser Schulung betrachtete ESTW-Systemfamilie. Komponenten, Schnittstellen und Bedienfunktionen sind anhand der für das Projekt geltenden System- und Versionsunterlagen einzuordnen.

### FFT
Im Schulungskontext die **Interne Abnahmeprüfung**. Aufgaben und Entscheidungsbefugnisse ergeben sich aus den gültigen Vorgaben und der konkreten Beauftragung, nicht aus der Teilnahme an der Schulung.

### Fahrstraße
Durch das Stellwerk gesicherter Fahrweg für eine Zug- oder Rangierfahrt mit den jeweils festgelegten Abhängigkeiten, Verschlüssen und Ausschlüssen. Eine Bedienanforderung ist von der tatsächlichen Fahrstraßenbildung und einer möglichen Fahrtfreigabe zu unterscheiden.

### Fahrstraßensperrung
Im jeweiligen Projekt und Szenario festgelegte Einschränkung der Nutzung bzw. Einstellung einer Fahrstraße. Welche Funktionen gesperrt werden und welche Sicherungsabhängigkeiten fortbestehen müssen, ist aus den geltenden Vorgaben abzuleiten. Eine Sperranzeige allein weist nicht sämtliche Schutzwirkungen nach.

### Flankenschutz
Schutz einer Fahrstraße gegen gefährdende seitliche Fahrbewegungen aus benachbarten Gleisbereichen. Die erforderlichen Maßnahmen, etwa durch geeignete Weichenstellungen oder andere vorgesehene Schutzelemente, ergeben sich aus den Planunterlagen. Fahrstraßenausschlüsse und Flankenschutz sind zusammen zu betrachten, aber nicht gleichzusetzen.

### Funktionale und sicherungstechnische Prüffragen
Funktionale Prüffragen untersuchen das geforderte Verhalten unter festgelegten Bedingungen. Sicherungstechnische Prüffragen betrachten insbesondere die Verhinderung unzulässiger Zustände und gefährdender Abläufe. Es handelt sich um sich ergänzende Perspektiven, nicht um zwei vollständig getrennte Prüfbereiche.

### Inbetriebnahme
Überführung eines neuen oder geänderten Zustands in den betriebswirksamen Einsatz.

Eine Wiederinbetriebnahme betrifft die erneute Nutzung nach einer Änderung oder Unterbrechung. Die zugehörige ATZ-Übung ist von der tatsächlichen Inbetriebnahme und deren formalen Voraussetzungen zu unterscheiden.

### JIRA-Prüfbuch
In JIRA geführte strukturierte Prüf- und Fehlerdokumentation. Ein Befund wird mit Anforderung, Prüfobjekt, Stand, Reproduktionsschritten und Belegen erfasst und mit dem zugehörigen Prüfprotokoll verknüpft. Status und Zuständigkeiten richten sich nach dem gültigen Workflow; ein geschlossener Vorgang ist nicht mit einer Anlagenfreigabe gleichzusetzen.

### Nachtest / Rückwirkungsprüfung
Ein Nachtest prüft, ob eine gemeldete Abweichung im dokumentierten korrigierten Stand behoben ist. Eine Rückwirkungsprüfung untersucht zusätzlich, ob die Änderung andere relevante Funktionen oder Schnittstellen unbeabsichtigt beeinflusst. Der Umfang ist fachlich zu begründen.

### Nebenfahrstraße
In den Schulungsszenarien verwendete Bezeichnung für einen benachbarten Fahrweg, der hinsichtlich einer möglichen Gefährdung oder Abhängigkeit zu untersuchen ist. Die Bezeichnung allein legt weder eine Flankenschutzfunktion noch eine konkrete Sperrmaßnahme fest.

### Projektierte Daten
Anlagenspezifische Konfigurationsdaten, die Anforderungen und Planungsfestlegungen für das Stellwerk umsetzen. Sie sind von generischer Software sowie dem tatsächlich geladenen Datenstand zu unterscheiden; alle relevanten Stände sind im Prüfnachweis zuzuordnen.

### PT1-Anforderungen
Anforderungen aus den für die Prüfung maßgeblichen **LST-Planunterlagen (PT1)**. Für den Soll-/Ist-Abgleich sind Dokumentenstand, betroffene Objekte und konkrete Fundstelle anzugeben. PT1-Anforderungen werden nicht aus dem beobachteten Verhalten abgeleitet, sondern bilden dessen Prüfmaßstab.

### Signalisierung
Darstellung bzw. Übermittlung von Signalbegriffen oder Zuständen im jeweils benannten Zusammenhang. In dieser Schulung ist ausdrücklich zwischen dem Signalbild am Bedienplatz, einer sonstigen Zustandsanzeige und der tatsächlichen Signalfunktion der Außenanlage zu unterscheiden. Ein Anzeige- oder Logbefund allein beweist weder die korrekte noch die fehlerhafte Außenwirkung.

### Softwarewechsel
Austausch oder Aktualisierung eines Softwarestands. Ob zugleich Projektierungsdaten geändert werden und welche Abhängigkeiten bestehen, ist getrennt zu dokumentieren. Der Prüfumfang wird aus der Änderung und ihren möglichen Rückwirkungen abgeleitet.

### Soll-/Ist-Vergleich
Gegenüberstellung einer aus gültigen Quellen abgeleiteten Erwartung mit dem tatsächlich beobachteten bzw. nachgewiesenen Zustand. Ausgangsbedingungen und Standangaben gehören dazu; fehlende Angaben sind als offen zu kennzeichnen.

### Tabellenwerte
In Tabellen geführte anlagenspezifische Werte oder Parameter. Zu prüfen sind sowohl ihre Übernahme in den vorgesehenen Datenstand als auch ihre Wirkung im betroffenen Funktionszusammenhang. Versionskennung oder Prüfsumme allein belegt keine fachliche Richtigkeit.

### Übereinstimmungsprüfung
Prüfung der Übereinstimmung der realisierten Anlage und ihrer Zuordnungen mit den maßgeblichen Planungs- und Projektierungsgrundlagen nach der gültigen Verfahrensanweisung. Dazu gehören je nach Prüfumfang Nachweise zur Innen- und Außenanlage sowie zum Zusammenspiel von Bedienung, Kommando und Meldung. Sie ist nicht mit jedem allgemeinen Soll-/Ist-Vergleich im ATZ gleichzusetzen.

### Zuglenkung
Unterstützung bzw. Automatisierung der Fahrwegsteuerung anhand der dafür vorgesehenen Vorgaben. Sie ersetzt keine sicherungstechnischen Voraussetzungen für Fahrstraßenbildung oder Fahrtfreigabe. Die im Übungsfall verfügbaren Funktionen sind versionsbezogen zu erläutern.
