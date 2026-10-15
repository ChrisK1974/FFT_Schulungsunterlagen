# Hausaufgabe Tag 2: Fallstudien und Prüfvorbereitung

## Ziel
Diese Hausaufgabe festigt die Inhalte von **Tag 2** und bereitet die ersten Prüfaufgaben im Mentoring vor. Sie verbinden die Interpretation der Bedienoberfläche mit einer nachvollziehbaren Prüfstrategie und Fehlerdokumentation.

**Lernziele:** Sie können einen Bedienablauf anhand von Soll-Vorgaben beschreiben, Befunde reproduzierbar dokumentieren und geeignete Prüfschritte zur Eingrenzung möglicher Ursachen auswählen.

**Bearbeitungszeit:** ca. 90–120 Minuten  
**Abgabeform:** Schriftliche Bearbeitung der Aufgaben

**Material:** Arbeitsblätter „Bedienoberfläche“, „Prüfprotokoll-Vorlage“, „JIRA-Prüfbuch-Anleitung“ und „Fehlerbehandlung: Checkliste“ sowie die bereitgestellten Referenzunterlagen.

**Bearbeitungshinweise:** Planen Sie etwa 20 / 30 / 35 / 15 Minuten für die vier Teile ein. Nutzen Sie ausschließlich bereitgestellte Übungsdaten; reale Eingriffe oder Softwarewechsel sind nicht Teil der Hausaufgabe. Geben Sie Quellen und Standangaben an. Fehlende Objektkennungen, Versionen oder Parameter sind als „nachzutragen“ zu kennzeichnen.

---

## Teil 1: Bedienoberfläche und Zuglenkung

### Aufgabe 1: Bedienabläufe beschreiben
Beschreiben Sie einen aus der Schulung bekannten Bedienablauf und beantworten Sie die folgenden Fragen:

1. Welche Funktionen des ATZ-Bedienplatzes sind für die Prüfung besonders wichtig?
2. Welche Voraussetzungen, Bedienhandlungen und Rückmeldungen sind im gewählten Zuglenkungsszenario zu beachten? Welche sicherungstechnischen Voraussetzungen bleiben unabhängig davon wirksam?
3. Welche Anzeigen erwarten Sie bei Sperrung bzw. Wiederinbetriebnahme einer Fahrstraße laut der geltenden Bedien- und Projektierungsunterlagen? Welche zusätzlichen Nachweise benötigen Sie neben der Anzeige?
4. Welche Hinweise in Oberfläche oder Log können auf eine Abweichung hindeuten, und weshalb beweisen sie allein noch keinen Projektierungsfehler?

**Arbeitsergebnis:** Eine Ablaufbeschreibung mit Ausgangszustand, Bedienhandlung, erwarteter Rückmeldung und zugehöriger Quelle.

---

## Teil 2: Prüfprotokoll und Fehlerdokumentation

### Aufgabe 2: Dokumentationspraxis
Analysieren Sie die folgende Beobachtung aus einem vereinfachten Schulungsfall:

> Nach einem Softwarewechsel im ATZ fehlt am Bedienplatz eine erwartete Zustandsanzeige. Die zugehörige PT1-Anforderung und die bereitgestellten Projektierungsunterlagen sehen diese Anzeige unter den im Szenario festgelegten Voraussetzungen vor. Ob eine Anzeigeabweichung, ein abweichender Systemzustand oder eine fehlerhafte Ausgangsbedingung vorliegt, ist noch offen.

Bearbeiten Sie dazu:

1. Wie beschreiben Sie den Befund im Prüfprotokoll und im verknüpften JIRA-Vorgang, ohne die Ursache vorwegzunehmen?
2. Welche Informationen müssen enthalten sein, damit der Fehler reproduzierbar ist?
3. Welche möglichen sicherheitsrelevanten und betrieblichen Auswirkungen müssen geklärt werden? Begründen Sie eine vorläufige Bewertung und benennen Sie, wer diese nach geltendem Verfahren bestätigt.
4. Welche nächsten Schritte einschließlich Zuständigkeitsklärung, Korrekturprüfung und Nachtest schlagen Sie vor?

**Arbeitsergebnis:** Ein beispielhafter Befundeintrag mit Kurzbeschreibung, Anforderungsbezug, Standangaben, Reproduktionsschritten, Soll-/Ist-Zustand, Belegen, Unsicherheiten und nächstem Bearbeitungsschritt. Ein fehlendes Signalbild am Bedienplatz darf nicht ohne weitere Prüfung mit einem fehlerhaften Außensignal gleichgesetzt werden.

---

## Teil 3: Fallstudie

### Aufgabe 3: Prüfstrategie entwickeln
Bearbeiten Sie das folgende Szenario:

> Im ATZ wird der Zielzustand einer geplanten Inbetriebnahme mit einem neuen Tabellenstand geprüft. Ein im Übungsfall benannter Parameter stimmt im bereitgestellten Datenvergleich nicht mit dem freigegebenen Soll-Stand überein. Zusätzlich weicht die beobachtete Systemreaktion vom erwarteten Verhalten ab. Ob tatsächlich der falsche Datenstand geladen ist und ob beide Beobachtungen dieselbe Ursache haben, ist noch zu klären.

Beantworten Sie dazu:

1. Wie vergleichen Sie freigegebenen Soll-Stand, bereitgestellten Projektierungsstand und nachweislich geladenen Datenstand?
2. Welche Referenzunterlagen, Änderungslisten, Versionsnachweise und Prüfergebnisse benötigen Sie?
3. Mit welchen unterscheidenden Prüfschritten grenzen Sie Projektierung, Laden des Datenstands, generische Software, Simulation und Bedienung als mögliche Ursachen ein?
4. Wie dokumentieren Sie bestätigte Abweichungen, nicht bestätigte Hypothesen und erforderliche Rückwirkungsprüfungen?

**Arbeitsergebnis:** Ein Prüfplan mit mindestens drei begründeten Prüfschritten.

| Hypothese / Prüffrage | Benötigte Grundlage | Prüfschritt | Erwartetes Unterscheidungsmerkmal |
|----------------------|---------------------|-------------|----------------------------------|
| | | | |
| | | | |
| | | | |

Beschreiben Sie die Aussagegrenzen Ihrer Nachweise: Eine übereinstimmende Versionskennung oder Prüfsumme belegt für sich allein weder fachlich richtige Parameter noch das korrekte Systemverhalten.

---

## Teil 4: Transfer in die Praxis

### Aufgabe 4: Vorbereitung auf echte Prüfungen
Reflektieren Sie kurz:

1. Welche drei Aspekte sind für Sie bei einer realen ATZ-Prüfung am wichtigsten, und warum?
2. Wo sehen Sie noch Unsicherheiten im Umgang mit JIRA-Prüfbüchern oder bei der Bewertung von Befunden?
3. Welche Unterstützung benötigen Sie für Ihre ersten vereinbarten Prüfaufgaben, und an welchem Arbeitsergebnis soll Ihr Lernfortschritt überprüft werden?

---

## Abgabe
Reichen Sie Ablaufbeschreibung, Befundeintrag, Prüfplan und Reflexion zum mit der Schulungsleitung bzw. der Mentorin oder dem Mentor vereinbarten Termin ein. Die Ergebnisse werden im ersten passenden Mentoring-Gespräch besprochen.

**Bewertungskriterien:** Klare Soll-/Ist-Trennung, vollständige Reproduktionsangaben, begründete Auswahl der Prüfschritte, angemessener Umgang mit Sicherheitsfragen und ausdrückliche Kennzeichnung verbleibender Unsicherheiten. Eine feste Fehlerpriorität lässt sich ohne geklärte Auswirkungen nicht pauschal vorgeben.
