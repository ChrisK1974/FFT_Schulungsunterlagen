# Übergabe: FFT-Schulungsunterlagen – Prüfung projektierter ESTW L90 Daten

## Ziel des Projekts
Dieses Repository unterstützt neue Mitarbeitende der Internen Abnahmeprüfung (FFT) beim Einstieg in die Prüfung projektierter ESTW L90 Daten im Anlagen Test Zentrum (ATZ). Die zweitägige Schulung vermittelt Grundlagen und angeleitete Anwendung; das anschließende Mentoring vertieft die Handlungssicherheit anhand definierter Prüfaufgaben.

Nach der Schulung sollen Teilnehmende Anforderungen nachvollziehen, einfache Prüfszenarien unter Anleitung bearbeiten und Ergebnisse reproduzierbar dokumentieren können. Die Schulungsunterlagen ersetzen weder gültige Verfahrens- und Arbeitsanweisungen noch eine formale Beauftragung oder Freigabe.

## Struktur und Inhalte
Die zentralen Schulungsunterlagen liegen als Markdown vor:

- `01_PRAESENTATION/` – Präsentationsunterlagen
- `02_ARBEITSBLÄTTER/` – Arbeitsblätter, Vorlagen und Übungen
- `03_HAUSAUFGABEN/` – Vertiefung nach Tag 1 und Tag 2 sowie Lösungshinweise
- `04_REFERENZEN/` – Glossar, Checklisten und Zusammenfassungen
- `05_MENTORING/` – Unterlagen für die 12-monatige Begleitung

Originale Leitfäden und Prüfprotokolle im Repository ergänzen diese Unterlagen. Für einen konkreten Prüfeinsatz sind deren Gültigkeit, Version und Projektbezug anhand der maßgeblichen Dokumentenbasis zu prüfen.

## Didaktisches Konzept
Die Schulung ist auf zwei Präsenztage ausgelegt:

### Tag 1
- Grundlagen ESTW L90
- Systemarchitektur und Komponenten
- Sicherungsprinzipien mit Fokus auf Flankenschutz
- Prüfprozesse und Dokumentation

### Tag 2
- Bedienoberfläche und Zuglenkung
- Prüfprotokolle und Fehlerbehandlung
- Praktische Übungen im ATZ
- Fallstudien und Szenarien

Jeder Themenblock folgt der Abfolge **Lernziel → fachliche Einordnung → angeleitete Anwendung → Ergebnissicherung**. Die Hausaufgabe zu Tag 1 bereitet Tag 2 vor; die Hausaufgabe zu Tag 2 unterstützt den Übergang ins Mentoring. Die Lösungsübersicht enthält Erwartungshorizonte, keine projektspezifischen Freigabeentscheidungen.

## Kerninhalte
Besondere Schwerpunkte sind:
- Flankenschutz und Abhängigkeiten zu benachbarten Fahrwegen bei Sperrung und Wiederinbetriebnahme von Fahrstraßen
- Abgleich von PT1-Anforderungen, projektierten Daten und beobachtetem Verhalten
- begründete Abgrenzung des Prüfumfangs bei Umbauten und Softwarewechseln, einschließlich betroffener Schnittstellen und möglicher Rückwirkungen
- nachvollziehbare Nachweise in Prüfprotokollen und verknüpften JIRA-Prüfbüchern
- Unterscheidung zwischen Beobachtung, möglicher Ursache und fachlicher Bewertung, etwa bei fehlenden Anzeigen oder abweichenden Tabellenwerten

Die Anzeige am Bedienplatz ist ein Prüfnachweis, ersetzt jedoch nicht den Nachweis der zugrunde liegenden sicherungstechnischen Funktion.

## Mentoring-Konzept
Nach der Schulung folgt ein 12-monatiges Mentoring mit drei Phasen:
1. Beobachtung
2. Co-Prüfer-Rolle
3. Eigenständige Prüfungen mit Mentor-Review

Die Zeiträume dienen der Planung. Der Übergang zur nächsten Phase richtet sich nach belegten Kompetenzen, vereinbartem Prüfumfang und den geltenden Zuständigkeiten. Lernfortschritte, offene Fragen und nächste Schritte werden im Feedback-Formular festgehalten; eine Teilnahme allein begründet keine Prüf- oder Inbetriebnahmebefugnis.

## Offene Punkte / Abgleich mit README
Die Dateiliste in der README beschreibt die zentralen Unterlagen bereits als Markdown und weist auf ergänzende Office-Dateien hin. Vor dem Schulungseinsatz sind noch folgende Punkte abzugleichen:

- Die Präsentationsdatei ist eine inhaltliche Ausarbeitungsgrundlage, kein fertiger Foliensatz.
- Für E-Learning, D-Cube und ATZ-Übungen sind geeignete Materialien, Zugänge und freigegebene Übungsstände durch die Schulungsleitung festzulegen.
- Die hier vorgesehenen Bearbeitungszeiten betragen etwa 90 Minuten nach Tag 1 und 90–120 Minuten nach Tag 2. Die pauschale Zeitangabe „zwischen den Tagen“ in der README ist bei der Schulungsplanung entsprechend einzuordnen.
- Aussagen der README zu Zertifikat, selbstständiger Inbetriebnahme und internen Vorgaben sind vor Verwendung durch die zuständigen Stellen zu bestätigen.

## Ergänzte fehlende Dateien
Ergänzt wurden die Präsentationsstruktur, die Arbeitsblätter 06–08, die beiden Hausaufgaben mit Lösungsübersicht, das Glossar und die Mentoring-Unterlagen sowie dieses Übergabedokument. Sie bilden zusammen mit den bestehenden Arbeitsblättern den didaktischen Rahmen; sie ersetzen keine projektspezifische Prüfplanung.

## Empfehlung
Vor dem ersten Einsatz sollte die Schulungsleitung:
1. Fachinhalte mit den aktuell gültigen Referenzunterlagen und dem vorgesehenen Anlagenzustand abgleichen.
2. Übungsdaten, Soll-Ergebnisse und zulässige Bedienhandlungen für die ATZ-Szenarien vorbereiten.
3. Die Aufgaben probeweise bearbeiten und den Zeitbedarf sowie die Verständlichkeit prüfen.
4. Mentorinnen und Mentoren auf gemeinsame Bewertungskriterien und den Umgang mit offenen Sicherheitsfragen abstimmen.

Eine spätere Überführung in Office-Formate ist optional. Dabei müssen Quellenbezüge, Versionsangaben und Aufgaben-Lösungs-Zuordnung erhalten bleiben.
