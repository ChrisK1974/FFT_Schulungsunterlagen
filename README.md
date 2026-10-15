# 📚 FFT Schulungsunterlage: Prüfung projektierter ESTW L90 Daten

## Überblick

Diese Schulungsunterlage ist für neue Mitarbeiter der Abteilung **Interne Abnahmeprüfung (FFT)** im Geschäftsbereich Transportsysteme der Thales Deutschland GmbH konzipiert.

### Zielgruppe
- Neue FFT-Mitarbeiter
- Geringes bis mittleres ESTW L90 Vorwissen
- DB Infrago Kontext

### Lernziel
Nach dieser 2-tägigen Schulung können die Teilnehmenden **unter Mentoring durch einen erfahrenen Kollegen erste Softwareprüfungen im ATZ (Anlagen Test Zentrum) selbstständig durchführen**.

---

## 📋 Struktur der Schulungsunterlage

### Tag 1: Grundlagen & Sicherungsebene
- **Modul 1:** ESTW L90 Grundlagen
- **Modul 2:** Systemarchitektur & Komponenten
- **Modul 3:** Sicherungsprinzipien (Priorität!)
- **Modul 4:** Prüfprozesse & Dokumentation

### Tag 2: Bedienung & Praktische Prüfung
- **Modul 5:** Bedienoberfläche & Zuglenkung (Priorität!)
- **Modul 6:** Prüfprotokolle & Fehlerbehandlung
- **Modul 7:** Praktische Übungen im ATZ-Umfeld
- **Modul 8:** Case Studies & Szenarien

---

## 📁 Inhalt dieses Repositories

```text
FFT_Schulungsunterlagen/
├── README.md                                 # Diese Datei
├── HANDOVER.md                               # Umfassender Handover-Prompt
│
├── 01_PRAESENTATION/
│   └── FFT_Schulung_ESTW_L90_Pruefung.md     # Präsentationsstruktur (~80–100 Folien als Grundlage)
│
├── 02_ARBEITSBLÄTTER/
│   ├── 01_Lernzielkatalog.md
│   ├── 02_Sicherungsebene_Arbeitsblatt.md
│   ├── 03_Bedienoberfläche_Arbeitsblatt.md
│   ├── 04_Prüfprotokoll_Vorlage.md
│   ├── 05_JIRA_Prüfbuch_Anleitung.md
│   ├── 06_Fehlerbehandlung_Checkliste.md
│   ├── 07_Selbstreflexion_Checkpoint.md
│   └── 08_D-Cube_Grundlagen.md
│
├── 03_HAUSAUFGABEN/
│   ├── Hausaufgabe_Tag1_E-Learning.md
│   ├── Hausaufgabe_Tag2_Fallstudien.md
│   └── Loesungsuebersicht.md
│
├── 04_REFERENZEN/
│   ├── ESTW_L90_Glossar.md
│   ├── Checkliste_Softwareprüfung.md
│   └── FFT_Handbucher_Zusammenfassung.md
│
└── 05_MENTORING/
    ├── Mentoringplan_Struktur.md
    └── Feedback_Formular.md
```

> Hinweis: Einzelne originale Arbeitsdokumente und Prüfprotokolle liegen zusätzlich weiterhin in Office-Formaten (`.docx`, `.xlsx`) im Repository. Die oben aufgeführte Struktur beschreibt den aktuellen Schulungsstand der zentralen Unterlagen in Markdown.

---

## 🎯 Kernlernziele

Nach dieser Schulung können Teilnehmende:

1. ✅ **Sicherungsprinzipien verstehen** - speziell Flankenschutz bei Fahrstraßen-Sperren/-Inbetriebnahmen
2. ✅ **Bedienoberfläche bedienen** - ATZ-Bedienplatz nutzen, Zuglenkung durchführen
3. ✅ **Prüfprotokolle handhaben** - JIRA-Prüfbücher führen, Fehler dokumentieren
4. ✅ **Typische Fehler erkennen** - nicht umgesetzte PT1-Anforderungen, fehlende Signalisierungen, Tabellenwerte
5. ✅ **Im ATZ prüfen** - unter Mentoring erste Softwaretests durchführen

---

## ⏱️ Schulungsdauer

- **Präsenzschulung:** 2 Tage (8:30 - 17:00 Uhr)
- **Hausaufgaben:** ~3-4 Stunden zwischen den Tagen
- **Nachfolgendes Mentoring:** 12 Monate begleitete Praxiserfahrung

---

## 🎨 Design & Standards

- **Corporate Design:** Hitachi Rail
- **Farben:** Hitachi-Blau (#0066CC), Weiß, Grau
- **Schriftarten:** Segment, Helvetica
- **Regulatorische Basis:** Thales VA/AA (Verfahrensanweisungen/Arbeitsanweisungen)

---

## 📚 Referenzdokumente

Diese Schulung basiert auf folgenden Thales-Unterlagen:

1. **Differenzprüfung - GTS MLS Germany** - Prüfumfang bei Umbauten
2. **Handhabung elektronische Ablage** - Archivierung
3. **Handhabung JIRA-Prüfbücher** - Fehlerbehandlung (Schwerpunkt!)
4. **Handhabung Prüfdokumentation** - Prüfablauf
5. **Handhabung Prüfprotokolle** - Protokollstruktur
6. **Prüfung projektierter Daten** - Hauptprozess
7. **Übereinstimmungsprüfung** - Finale Validierung

---

## 🎓 Praktische Szenarien

Die Schulung basiert auf **echten Umbauten** bei DB Infrago:

### Szenario 1: Geplante Baumaßnahme - Fahrstraße Sperren
- Ausgangszustand: ESTW im Betrieb
- Aufgabe: Fahrstraße korrekt sperren, PT1-Anforderungen prüfen
- Fehlersuche: Flankenschutz-Probleme identifizieren

### Szenario 2: Softwarewechsel - Inbetriebnahme
- Ausgangszustand: Alte SW-Version in Betrieb
- Aufgabe: Neue SW-Version hochfahren, Prüfprotokolle durcharbeiten
- Fehlersuche: Nicht eingearbeitete Tabellenwerte, fehlende Signalisierungen

### Szenario 3: Fahrstraße Wieder-Inbetriebnahme nach Umbau
- Ausgangszustand: Fahrstraße war gesperrt
- Aufgabe: Alle PT1-Anforderungen verifizieren
- Fehlersuche: Flankenschutz-Konfiguration prüfen

---

## 🔄 12-Monats-Mentoring

### Phase 1: Beobachtung (Monat 1-3)
- Wöchentliche Mentoring-Treffen
- Beobachtung echter Prüfungen
- Erste kleine Aufgaben

### Phase 2: Co-Prüfer (Monat 4-8)
- **Meilenstein 1:** Erste SW-Wechsel-Inbetriebnahme unter Supervision
- Mentor und Prüfer teilen sich Aufgaben

### Phase 3: Eigenständigkeit (Monat 9-12)
- Eigenständige Prüfungen mit Mentor-Review
- **Meilenstein 2:** Vollständig eigenständige Prüfung & Inbetriebnahme
- **Zertifikat:** "FFT Prüfer - ESTW L90"

---

## 💡 Schwerpunkte der Schulung

### 1. Flankenschutz (Sicherungsebene)
**Häufigster Fehler in der Praxis!**
- Nebenfahrstraße nicht korrekt gesperrt
- Signalisierung bei Fahrstraßen-Änderungen fehlt
- Blockierter Bereich nicht konsistent

### 2. Bedienoberfläche (Bedienplatz)
- ATZ-Bedienplatz (BBP) nutzen
- Zuglenkung korrekt durchführen
- Fehler im Log erkennen

### 3. JIRA-Prüfbücher (Dokumentation)
- Fehler korrekt kategorisieren
- Reproduzierbarkeitsbeschreibung schreiben
- Prioritäten setzen
- Status-Transitions handhaben

### 4. Typische Fehler
- **Nicht umgesetzte PT1-Anforderungen**
- **Nicht eingearbeitete Tabellenwerte**
- **Fehlende Signalisierungen**

---

## 📞 Support & Kontakt

**Bei Fragen zur Schulung:**
- Schulungsleitung: [E-Mail]
- Mentor-Koordination: [E-Mail]
- ATZ-Support: [E-Mail]

**Im Repository:**
- Issues für Fragen/Verbesserungen
- Discussions für Erfahrungsaustausch

---

## ✅ Checkliste vor der Schulung

Vor der ersten Schulung prüfen:

- [ ] PowerPoint ist vollständig & getestet
- [ ] Alle Arbeitsblätter sind ausfüllbar
- [ ] Video-Links in Hausaufgaben funktionieren
- [ ] JIRA-Beispiel-Projekte sind vorbereitet
- [ ] ATZ-Szenarien 1-3 sind aufgesetzt
- [ ] Mentoren haben Schulung erhalten
- [ ] Repository ist für Teilnehmende zugänglich
- [ ] BBP-Bedienplatz ist reserviert
- [ ] Design ist konsistent (Hitachi)
- [ ] Glossar ist aktuell

---

## 📈 Erfolgskriterien

**Nach 2-Tage-Schulung:**
- ✅ ESTW L90 Grundkonzepte verstanden
- ✅ Flankenschutz-Problematik erkannt
- ✅ JIRA-Prüfbuch kann angelegt werden
- ✅ Erste ATZ-Szenarien können durchgearbeitet werden

**Nach 12-Monats-Mentoring:**
- ✅ Meilenstein 1 erfolgreich (SW-Wechsel unter Supervision)
- ✅ Meilenstein 2 erfolgreich (eigenständige Prüfung)
- ✅ Zertifikat ausgestellt
- ✅ Prüfer produktiv einsetzbar

---

## 📌 Wichtige Hinweise

1. **Echte ESTW L90 Daten** - Szenarien basieren auf echten Umbauten
2. **Flankenschutz ist kritisch** - Häufigste Fehlerquelle
3. **JIRA-Zugriff nötig** - Alle Teilnehmenden brauchen Schreib-Zugriff
4. **Mentoring ist essentiell** - 12 Monate sind nicht optional
5. **Wöchentliches Feedback** - Lernfortschritt kontinuierlich prüfen

---

## 📅 Versionsverwaltung

**Version:** 1.1  
**Erstellt:** Oktober 2026  
**Gültig bis:** Oktober 2027  
**Nächste Überprüfung:** Oktober 2027

---

## 📖 Weitere Informationen

Detaillierte Informationen zum gesamten Schulungsprojekt, zur Struktur und zu den Hintergründen finden Sie in:

👉 **[HANDOVER.md](./HANDOVER.md)** - Umfassender Handover-Prompt mit allen Details

---

**Viel Erfolg mit der Schulung!** 🎯
