# D-Cube: Grundlagen

## Zweck
Dieses Arbeitsblatt ordnet D-Cube in die Prüf- und Nachweisdokumentation der FFT ein. Es bereitet eine angeleitete Einführung am tatsächlich eingesetzten System vor und ist keine versionsspezifische Bedienungsanleitung.

## Was ist D-Cube?
D-Cube wird in den vorhandenen Referenzunterlagen im Zusammenhang mit Prüfschritten und Prüfprotokollen für Inlandsprojekte beschrieben. Die Zusammenfassung „Handhabung Prüfprotokolle“ nennt Prüfschritte durch Montage, Vorprüfung und Interne Abnahmeprüfung sowie den Export von Protokollen durch FFT.

**Quellenbezug:** [FFT-Handbücher – Zusammenfassung](../04_REFERENZEN/FFT_Handbucher_Zusammenfassung.md), Abschnitt 5 „Handhabung Prüfprotokolle“ und Abschnitt 7 „Übereinstimmungsprüfung“. Die Zusammenfassung dient der Orientierung; für den Einsatz sind die aktuellen Originalanweisungen maßgeblich.

Aus dieser Einordnung lassen sich keine konkreten Menüs, automatisierten Testfunktionen oder Schnittstellen ableiten. Verfügbare Funktionen, Rollenrechte und die Anwendbarkeit im jeweiligen Projekt müssen vor der Übung geklärt werden. Für Exportprojekte beschreibt die Referenz eine Erstellung der Prüfprotokolle aus Eingangsdaten und Vorlagen; eine identische Nutzung von D-Cube wird hier nicht vorausgesetzt.

## Relevanz für die Schulung
Teilnehmende sollen unterscheiden können:
- **Prüfgrundlage:** Welche Anforderung und welcher Anlagen-/Projektierungsstand sind zu prüfen?
- **Prüfdurchführung:** Welche Handlung wurde im Prüfaufbau unter welchen Bedingungen ausgeführt?
- **Prüfnachweis:** Welcher Prüfschritt und welches Ergebnis sind dokumentiert?
- **Fehlernachverfolgung:** Welcher JIRA-Vorgang beschreibt eine Abweichung und deren weitere Bearbeitung?

Ein ausgefüllter Prüfschritt belegt nur den dokumentierten Prüfumfang. Er ersetzt weder fehlende Nachweise noch eine Freigabeentscheidung.

## Lernziele
Nach Bearbeitung dieses Dokuments und einer angeleiteten Demonstration können Teilnehmende:
1. die Rolle von D-Cube im betrachteten Projekt beschreiben und von Simulation sowie Fehlernachverfolgung abgrenzen,
2. einen vorgegebenen Prüfschritt und dessen Zuordnung zum Prüfobjekt anhand der verfügbaren Unterlagen nachvollziehen,
3. die für einen nachvollziehbaren Prüfnachweis benötigten Angaben benennen,
4. die Verbindung zwischen Prüfergebnis, Prüfprotokoll und JIRA-Befund erläutern, ohne eine automatische Schnittstelle vorauszusetzen.

## Typische Inhalte einer Einführung
Die Schulungsleitung zeigt die folgenden Punkte am freigegebenen Übungsstand. Wo die eingesetzte Version Angaben nicht unmittelbar abbildet, wird deren Ablage im zugehörigen Prüfprotokoll erläutert.

| Thema | Leitfrage für die Demonstration | Zu sicherndes Ergebnis |
|-------|--------------------------------|------------------------|
| Projekt- und Standzuordnung | Zu welcher Anlage und welchem Bauzustand gehört der Nachweis? | Eindeutige Referenz und Dokumentenstand |
| Prüfschritt | Was ist zu prüfen, und welche Soll-Vorgabe gilt? | Bezug zu Prüfobjekt und Anforderung |
| Durchführung | Welche Voraussetzungen und Bedienhandlungen sind erforderlich? | Reproduzierbarer Ablauf |
| Ergebnis | Was wurde tatsächlich beobachtet, und ist die Prüfung vollständig? | Soll-/Ist-Vergleich, offene Punkte und Belege |
| Protokollbereitstellung | Wie wird der aktuelle Nachweis gemäß gültiger Anweisung bereitgestellt? | Zugeordneter Protokollstand |
| Abweichung | Wo wird ein Befund weiterverfolgt? | Verweis auf Prüfprotokoll und JIRA-Vorgang |

## Bezug zur Praxis
**Übung: Einen Prüfnachweis nachvollziehen (ca. 20–30 Minuten)**

Verwenden Sie einen von der Schulungsleitung bereitgestellten Übungsfall, etwa eine Fahrstraßensperrung im ATZ. Bearbeiten Sie die folgenden Schritte unter Anleitung:

1. Benennen Sie Prüfobjekt, Bauzustand, Software-/Datenstand und Anforderungsreferenz.
2. Suchen Sie den zugehörigen Prüfschritt in D-Cube oder in einem bereitgestellten Protokollauszug.
3. Erläutern Sie Voraussetzungen, Soll-Ergebnis und benötigte Belege vor der Durchführung.
4. Halten Sie nach dem freigegebenen Übungsablauf den Ist-Zustand fest. Kennzeichnen Sie nicht ausgeführte oder nicht bewertbare Anteile ausdrücklich.
5. Beschreiben Sie bei einer Abweichung, welche Angaben in das Prüfprotokoll und welche in den verknüpften JIRA-Vorgang gehören.

**Arbeitsergebnis:** Eine kurze Zuordnung „Anforderung → Prüfschritt → Beobachtung → Nachweis → gegebenenfalls Befund“.

**Erfolgskriterium:** Eine andere Person kann den betrachteten Stand und die Aussagegrenzen des Ergebnisses nachvollziehen. Ohne Systemzugang erfolgt die Übung anhand eines freigegebenen Auszugs; sie gilt dann nicht als Nachweis praktischer Werkzeugbedienung.

## Hinweise für Mentoren
Mentorinnen und Mentoren klären vor der Übung:
- welche D-Cube-Version und Anweisungen im Projekt gelten und welche Funktionen tatsächlich genutzt werden,
- welche Übungsrechte bestehen und wie Änderungen an produktiven Nachweisen ausgeschlossen werden,
- welche Angaben im Werkzeug und welche in ergänzenden Dokumenten geführt werden,
- wie unvollständige Prüfschritte, Korrekturen und Protokollstände nach dem gültigen Verfahren behandelt werden.

In der Auswertung lassen sie die Teilnehmenden einen Nachweis erläutern und prüfen insbesondere Standzuordnung, Vollständigkeit und Trennung von Prüfergebnis und Fehlerbearbeitungsstatus.
