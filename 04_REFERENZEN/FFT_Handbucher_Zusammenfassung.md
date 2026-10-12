# FFT Handbucher - Kurz-Zusammenfassung

Diese Datei fasst die wichtigsten Punkte aus den Thales Verfahrensanweisungen zusammen.

---

## 1. Differenzprüfung (VA Differenzprüfung)

### Grundkonzept
- **Ziel:** Nur geänderte Teile prüfen, nicht das ganze System
- **Anwendung:** Bei Umbauten, Korrektionen, Releasewechsel
- **Basis:** Ausgangbasis ist i.d.R. die in Betrieb befindliche Anlage

### Voraussetzungen
- ✅ Freigabe Modul-Software (FB 034) liegt vor
- ✅ "Liste der Änderungen" liegt vor
- ✅ Abnahmeniederschrift der Vorgängerversion liegt vor
- ✅ Systeme im Status TQR approved

### ESTW L90 Spezifische Prüfungen
1. **ISA-Differenz-Report** - analysieren & ggf. an Anlage nachprüfen
2. **UDM-Differenz-Report** - analysieren & ggf. an Anlage nachprüfen
3. **ESTW-Differenzen** (MEM, SM, AzLM) - analysieren & nachprüfen
4. **ZX-Differenzen** - analysieren & nachprüfen
5. **Konfigurationsdaten** (Prokom, DATKOM) - analysieren & nachprüfen

### ESTW L90 5 Spezifisch
- Konfigurationsdaten mit Software (BeyondCompare, DDT, XMLDiff) vergleichen
- Filterregeln dokumentieren
- Alle SIL1/2/3/4 Systeme prüfen (IM, SCM, FEC, HMI, RBC, OCS, SAHARA)
- Logdateien analysieren
- Neue Prüfprotokolle für Montage/Vorprüfung bereitstellen

---

## 2. Handhabung elektronische Ablage (AA)

### Ablagestruktur
```
\\destgsfs01\operations$\TDIG_TBEG_OT\01_Abteilung\Prüfdokumentation
  └── <Kunde/Land/Nahverkehr>
      └── <Bereich/Projekt>
          └── <Bauzustand>
```

### DB AG Struktur
```
\\Prüfdokumentation\DB AG\<BZ-Kürzel>\<Nr. des Stbez.>\<UZ-Kürzel>
```
Beispiel: `\Prüfdokumentation\DB AG\EDGW\15\KKX1\0010`

### Benennung Anlagenzustand
- **Pflicht:** Anlagenzustandsnummer (0010, 0020, etc.)
- **Optional:** RL-Bezeichner (RL01, RL02)
- **Kommentar:** Z.B. "0080 (ZX Anpassung EOSX)"

### Wichtig
- Verzeichnisse von Vorgängerzuständen NICHT löschen
- Nur Dateien ablegen, die sich ändern
- Alte Versionen in History-Ordner verschieben

---

## 3. Handhabung JIRA-Prüfbücher (AA)

### JIRA vs. Excel
- **Vorteil:** Zentrales System, Versionskontrolle, Status-Tracking
- **Nachteil:** Kein "Einfrieren" auf Laufwerk möglich → Export notwendig

### Projekt-Struktur
- **1 Projekt pro:** Land/Bahnhof/Strecke/Bauzustand
- **Mehrere Prüfbücher pro Projekt:** Für Steuerbezirke, CTC/OCC, Module (IM, SM), etc.

### Issue-Eintrag muss enthalten
1. **Reproduzierungsbeschreibung** - genau & nachvollziehbar
2. **Screenshots & Logs** - anhängen
3. **PT1-Zuordnung** - zu welcher Anforderung?
4. **Priorität** - Kritisch, Hoch, Mittel, Niedrig
5. **Typ** - Projektierungsfehler, Systemfehler, Datenfehhler, Funktionsfehler
6. **Status-Transition** - Offen → Behoben → Verifiziert → Geschlossen

### Abnahmeprüfer-Verantwortung
- ✅ Prüfbuch anlegen/fortführen
- ✅ Systemversionen & Projektierungsstand definieren
- ✅ Issues kategorisieren
- ✅ Nur nach erfolgreicher Verifikation schließen
- ✅ Sicherheitskritische Fehler vor Freigabe lösen
- ✅ Nicht reproduzierbare Fehler nach Rücksprache mit Projekt schließen
- ✅ Exports zu definierten Zeitpunkten (Freigabe, Zwischenübergabe)

### Workflow
```
Offen → Behoben → Verifiziert → Geschlossen
              ↓
         Nicht reproduzierbar (mit Begründung)
```

---

## 4. Handhabung Prüfdokumentation (AA)

### Umfang der Prüfdokumentation

#### Zulassungen
- (EBA) Produktzulassung(en) - elektronisch
- (EBA) Systemzulassung(en) - elektronisch

#### Freigaben
- Generische Produktfreigabe - elektronisch
- Generische Systemfreigabe - elektronisch
- I.NVT-Freigabe (DB) - elektronisch
- Projektierungsfreigabe (FB034a-g) - elektronisch + Papier
- Änderungsmitteilungen - elektronisch/Papier
- **FB022 - Freigabe zur Übergabe an Kunden** - ZENTRAL!

#### Weitere Dokumente
- Planbasisliste (PBL)
- Planunterlagen (PT1)
- Prüfprotokolle
- Differenzlisten/Reports
- **JIRA-Prüfbuch-Export**
- Projektierungsübersicht
- PÜD (Domestic)
- Abnahmeprüfzeugnis (FB011)

### Prüfordner
- **Pro Projekt/Bauzustand:** Ein oder mehrere Prüfordner
- **Inhaltsverzeichnis:** Nach Standard-Template ausfüllen
- **Beschriftung:** Muss enthalten: Anlage, Bauzustand, "X von Y" (falls mehrere Ordner)
- **Archivierung:** Nach Projektabschluss (erfolgreicher Project Closure Review)

### FB022 - Freigabe zur Übergabe an Kunden
**Kritisch!**
- ✅ Nur wenn ALLE Voraussetzungen erfüllt
- ❌ KEINE Freigabe bei sicherheitskritischen Projektierungsfehlern
- ⚠️ Bei sicherheitskritischen Systemfehlern (Sev. 1): Bedingte Freigabe + Sonderfreigabe erforderlich
- 👁️ Muss vom Leiter FFT oder Teamleiter gegengezeichnet werden

### Abnahmeprüfer-Verantwortung
- ✅ Projektbegleitende Zusammenstellung (nicht erst am Ende!)
- ✅ Einfordern ausstehender Dokumente
- ✅ Einholung von Originalen (Papier)
- ✅ Korrekte Archivierung
- ✅ Verbleib bei Abnahmeprüfer bis Archivierung

---

## 5. Handhabung Prüfprotokolle (AA)

### Verantwortlichkeiten

**Inland (D-Cube):**
- Montage, Vorprüfung, Interne Abnahmeprüfung machen D-Cube-Prüfschritte
- FFT exportiert Protokolle mit aktuellem Stand
- FFT prüft, ob Montage & Vorprüfung ordnungsgemäß arbeiteten

**Export:**
- FFT erstellt aus Input-Daten & Templates die Prüfprotokolle
- Montage/Anlagenvorprüfung füllen Kapitel 1-3, 6, 8
- FFT füllt Kapitel 4, 5, 7
- FFT stellt sicher, dass alles ordnungsgemäß durchgeführt wurde

### Erstellung
- Aus `input_data_test_doc.XML` / Excellisten + Templates
- Bahnhofsspezifisch für Export
- Aus D-Cube für Inland

### Archivierung

**Inland:**
```
\\DESTGSFS02\zentral\TAS\Tsqtr\Prüfdoc\
  <Stellwerkstyp>\DBAG\<Bereich>\ESTW_<UZ/EZ>\<AZ-Nr>_<PSP>_<Projekt>
```
+ Auch Link in TOPP einstellen

**Export:**
```
\\destgsfs01\Operations$\TDIG_TBEG_OT\Prüfdokumentation\
  <Land>\<Strecke/Projekt>\<Bahnhof>\<Bauzustand>\Prüfprotokolle\Aktuelle Grundlage
```
+ Auch Sachnummer in CMCS einstellen (Kapitel 0)

### Änderungsmanagement
- Signifikante Datenänderungen → Neue Prüfprotokolle notwendig
- **Deckblätter & Verzeichnis:** Grundsätzlich austauschen
- **Bereits durchgeführte Protokollierungen:** NICHT in neue Protokolle übertragen
- **Mehrere Protokollblätter:** Verwenden für alte & neue Prüfungen
- **Alte Versionen:** In History-Ordner verschieben

---

## 6. Prüfung projektierter Daten (VA)

### Allgemeine Voraussetzungen
1. **Freigabe Modul-SW** (FB034 Export, FB034a-g Domestic)
2. **HW-Planunterlagen zur Ausführung** (PT2)
3. **Planbasisliste** (PBL) - freigegeben PM
4. **LST-Planunterlagen** (PT1) - freigegeben PM & Kunde (Minimum: PM)
5. **Systemfreigabe Generische Software** (FQR, GASC)
6. **PÜD** (Domestic) - Releaseplanung
7. **Dokumentenplan** (DOP) - Begleitdokumente

### Prüfbuch-Führung
- Mit Beginn anlegen (Neubau) oder fortführen (Umbau/Releasewechsel)
- JIRA-Prüfbuch verwenden (siehe AA Handhabung JIRA-Prüfbücher)

### Hardware Testanlage
- **Ort:** ATZ (Berlin, Stuttgart), ggf. ausgelagert, Remote per Guacamole
- **Hardware:** Möglichst identisch mit VDD-Freigabe
- **Ausnahmen:** Non-SIL / SIL0 können virtualisiert/simuliert werden
- **Redundanz:** 2v3-Systeme können auf 2v2 reduziert werden

### Simulation
- **Nur freigegebene Simulatoren & Daten verwenden**
- **Hauptsimulatoren:** SIMBA (Aussenanlage), TUS (ETCS L2), OBUSIM (Fahrsimulation)
- **Dokumentieren:** Simulationsversion in Prüfbuch
- **Fehler in Simulationsdaten:** Wie Projektierungsfehler behandeln
- **Simulator-Fehler:** Wie Systemfehler behandeln

### Neuanlage vs. Umbau/Korrektur/Releasewechsel
- **Neuanlage:** IMMER Vollprüfung aller relevanten SW-Anteile
- **Umbau/Korrektur/Releasewechsel:** Prüfer entscheidet: Voll- oder Differenzprüfung?

### Systemfehler
- **Parallel zu Prüfbuch:** In ClearQuest eintragen
- **Kontakt:** Defect Manager oder SEM
- **Sicherheitskritische Fehler:** Vor Freigabe lösen oder Sonderfreigabe einholen
- **Status:** Nicht gelöscht, nur als "erledigt" gekennzeichnet

### Datenträger
- Mit Abschluss Prüfung erstellen
- Geeignete Beschriftung
- Übergabe an Kundenanlage

---

## 7. Übereinstimmungsprüfung (VA)

### Allgemeine Voraussetzungen
1. **Projektspezifische Unterlagen** (PBL, PT1, PT2) - freigegeben PM
2. **Freigabe Modul-SW & RBC-SW** (FB034)
3. **Prüfprotokolle** (AA Handhabung Prüfprotokolle)
4. **Status TQR approved**
5. **Montage & Anlagenvorprüfung:** Anlage als fertig gemeldet

### Prüfbuch
- Gefundene Mängel dokumentieren
- (Siehe AA Handhabung JIRA-Prüfbücher)

### Innenanlage
- **Verantwortung:** Montage & Anlagenvorprüfung
- **Prüfschritte:** Gemäß D-Cube
- **Verifizierung FFT:**
  - ✅ SW-Versionen korrekt eingespielt?
  - ✅ Stromversorgungsprotokolle durchgeführt bis HdF/IBN?

### Außenanlage

#### Neubau - 2 Vorgehensweisen

**Variante 1: (Vor-)Prüfung & Zuordnungsprüfung getrennt**
1. FFT prüft im ATZ mit Simulation
2. Montage & Vorprüfung prüfen Außenanlage mit Simulation
3. Innen- & Außenanlage zusammengeschaltet → Zuordnungsprüfung
4. Vereinfachte Prüfung (nur Kommando & Meldung pro Element)

**Variante 2: (Vor-)Prüfung & Zuordnungsprüfung gemeinsam**
1. FFT prüft im ATZ
2. FFT führt Zuordnungsprüfung mit echter Außenanlage durch
3. Vollständige Prüfung von Bedienebene bis Außenanlage
4. Ggf. Simulationen im Filtermodus für nicht fertige Elemente

#### Zugbeeinflussungssysteme

**ETCS Level 1:**
- Statische Prüfung der Telegramme gegen PT1
- Dynamische ETCS-Testfahrten mit ausgerüsteter Lokomotive

**ETCS Level 2 (RBC):**
- RBC-Projektierung (Steckenatlas) nach UNISIG = SIL4
- Balisen-Positionen & Inhalte verifizieren
- GSM-R Rufnummern prüfen (müssen identisch sein)
- Keine physikalische Zuordnungsprüfung (keine Verbindung zu Außenanlage)

#### Umbau/Korrektur/Releasewechsel
- **Nur betroffene HW-Anteile** prüfen
- Kann auf Kundenanlage durchgeführt werden, wenn keine Sperrpausen möglich
- Dokumentation in FB022 erforderlich

---

## 🎯 Kritische Punkte zusammengefasst

### Top 5 Fehlerquellen in der Praxis

1. **Flankenschutz nicht korrekt implementiert**
   - Nebenfahrstraße nicht gesperrt
   - Blockadenlogik fehlerhaft
   - **Prüfmethode:** Vier-Ecken-Analyse, Szenario-Durchlauf

2. **PT1-Anforderungen nicht umgesetzt**
   - Signalisierung vergessen
   - Bremskurvenberechnung nicht aktualisiert
   - **Prüfmethode:** Direkter PT1-Vergleich mit Projektdaten

3. **Tabellenwerte nicht eingearbeitet**
   - Fahrtzeiten veraltet
   - Parameter nicht aktualisiert
   - **Prüfmethode:** Versionsvergleich, Checksummen

4. **Signalisierungsfehler**
   - Fahrstraße freigegeben, aber Signal bleibt rot
   - Signalaspekt-Logik falsch
   - **Prüfmethode:** Bedienplatz-Durchlauf, Log-Analyse

5. **Dokumentationsfehler**
   - JIRA-Einträge unvollständig
   - Screenshots fehlen
   - PT1-Zuordnung unklar
   - **Prüfmethode:** JIRA-Audit, Checklisten

---

## 📞 Kontakte & Eskalation

**Bei Fragen zu:**
- **Prüfprozessen:** Leiter FFT / Teamleiter
- **Systemfehlern:** Defect Manager / SEM
- **JIRA-Prüfbücher:** JIRA-Administrator
- **Ablage & Archivierung:** Dokumentenmanagement
- **ATZ-Ressourcen:** Testfloor-Competence-Center

---

**Version:** 1.0  
**Gültig für:** ESTW L90, ESTW L90 5, ETCS L1/L2  
**Stand:** Oktober 2026
