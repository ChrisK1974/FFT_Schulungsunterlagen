# JIRA-Prüfbuch Anleitung: ESTW L90

## Ziel
Dieses Arbeitsblatt erklärt die grundlegende Nutzung von JIRA für die Dokumentation von Prüfungen, Fehlern und Rückmeldungen.

---

## 1. Was ist ein JIRA-Prüfbuch?
Ein JIRA-Prüfbuch ist das zentrale Dokumentationssystem für Fehler, Mängel, Abweichungen und Prüfungen im Rahmen der Softwareprüfung.

Es dient dazu:
- Prüfungen nachvollziehbar zu dokumentieren
- Mängel zu erfassen
- Priorität und Status klar zu benennen
- Fehler nach Verifikation zu schließen

---

## 2. Typische Struktur
Ein Projekt im JIRA kann folgende Bereiche enthalten:

- **Prüfungen**
- **Fehler / Mängel**
- **Freigaben**
- **Anlagenzustand / Version**
- **Sicherheitskritische Fehler**

---

## 3. Fehlerarten

### 3.1 Projektierungsfehler
- PT1 wurde in der Projektierung nicht korrekt umgesetzt
- Signalisierung fehlt
- Fahrstraße logisch ungültig

### 3.2 Systemfehler
- Fehler im Produkt / System / Software
- Auf SEM / Defect Manager zu melden

### 3.3 Datenfehler
- Tabellenwerte falsch eingearbeitet
- Parameter veraltet

### 3.4 Funktionsfehler
- Bedienung funktioniert nicht wie erwartet
- Logik zeigt falsches Verhalten

---

## 4. Eintrag eines Fehlers: Pflichtfelder

Jeder Fehler sollte mindestens diese Felder enthalten:

- [ ] Fehlerbeschreibung
- [ ] Reproduktion
- [ ] Screenshots / Log-Dateien
- [ ] PT1-Referenz oder Prüfpunkt
- [ ] Version / Bauzustand
- [ ] Priorität
- [ ] Status
- [ ] Verantwortlicher

---

## 5. Beispiel: Fehler eintragen

### Fehlerbeschreibung
**Beispiel:** Fahrstraße X kann trotz freigegebenem Signal nicht korrekt gesetzt werden. Flankenschutzprüfung nicht erfüllt.

### Reproduktionsschritte
1. PT1-Plan öffnen
2. Fahrstraße X wählen
3. In Sicherheitslogik prüfen
4. Flankenschutzanalyse durchführen
5. Fehler dokumentieren

### Priorität
- [ ] Kritisch
- [ ] Hoch
- [ ] Mittel
- [ ] Niedrig

### Status
- [ ] Offen
- [ ] Behoben
- [ ] Verifiziert
- [ ] Geschlossen

---

## 6. Statuswechsel

### Standard-Workflow
```
Offen → Behoben → Verifiziert → Geschlossen
```

### Merksatz
- **Offen:** Fehler erkannt
- **Behoben:** Ursache beseitigt
- **Verifiziert:** Prüfer prüft erneut
- **Geschlossen:** Fehler akzeptiert und verifiziert

---

## 7. Sicherheitskritische Fehler

Sicherheitskritische Fehler dürfen nicht einfach geschlossen werden. Sie müssen:
- [ ] klar dokumentiert sein
- [ ] mit Ursache beschrieben sein
- [ ] mit Folgen und Risiken erklärt werden
- [ ] mit verantwortlicher Person dokumentiert sein
- [ ] vor Freigabe geprüft und bestätigt sein

---

## 8. Praktische Aufgabe

### Szenario
Ein Alarm in der Betriebsoberfläche zeigt an, dass eine Fahrstraße trotz korrekter PT1-Anforderung nicht korrekt freigegeben wird.

**Ihre Aufgabe:**
1. Erfassen Sie den Fehler in JIRA
2. Beschreiben Sie die Ursache
3. Zonieren Sie die Priorität
4. Verknüpfen Sie das mit einer PT1-Referenz
5. Dokumentieren Sie den Status

### Antwortraum
**Fehlerbeschreibung:**

____________________________________________________________________

**Ursache:**

____________________________________________________________________

**Priorität:**

____________________________________________________________________

**Status:**

____________________________________________________________________

---

## 9. Reflexion

- Was ist im JIRA-Prüfbuch besonders wichtig?
- Warum müssen Fehler mit Screenshots und Logdateien belegt werden?
- Wie wirkt sich eine unvollständige Fehlerdokumentation auf die Freigabe aus?

---

**Hinweis:** Die JIRA-Dokumentation ist ein Kernbestandteil der Prüfung und muss sauber und nachvollziehbar erfolgen.
