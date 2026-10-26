# Prüfstruktur Stellwerksprojekt

Starten Sie das Tool mit `python stw_pruefstruktur.py`. Für eine EXE verwenden
Sie lokal `build_exe.bat`.

## PT1-/PT2-Unterlagen sicher kopieren

- Die automatische Suche zeigt nur einen **Vorschlag** und löst keine Kopie aus.
- Wählen Sie den endgültigen Quellordner über **Durchsuchen…** oder übernehmen
  Sie den Vorschlag. Ein eingetippter Pfad muss mit **Quelle bestätigen**
  ausdrücklich freigegeben werden.
- Kopiert wird nur, wenn Sie zusätzlich **Daten kopieren** aktivieren.
- Mit **Auswahl löschen / nicht kopieren** werden Quelle und Freigabe entfernt.
- Projekt-/Betriebsstellenordner sowie Share-, Gruppen- und Regionsordner gelten
  als breite Quellen. Für diese müssen Sie zusätzlich **Gesamten Ordner
  einschließlich aller Unterordner kopieren** aktivieren und eine zweite
  Warnmeldung mit dem vollständigen Quellpfad bestätigen. Die Warnung ist
  standardmäßig auf Abbrechen gesetzt.
- Änderungen an PSP, Region, Betriebsstelle, Ziel oder Quelle widerrufen eine
  bestehende Freigabe. Wählen oder bestätigen Sie die Quelle dann erneut.
- Bestehende Dateien werden beim Kopieren nicht überschrieben.

## PSP-Elemente

Zulässig sind PSP-Elemente der Form `M17525-01` und mit genau einem optionalen
abschließenden Großbuchstaben, zum Beispiel `M19061-01A`. Die Eingabe wird
gespeichert und im Projektordner in Großbuchstaben verwendet. Das vollständige
Element wird bei der PT1-Suche abgeglichen: `M19061-01` trifft nicht
`M19061-01A`, und `M19061-01A` trifft nicht `M19061-01AB`.

## Tests

Das Programm selbst liegt vollständig in `stw_pruefstruktur.py`. Die
Entscheidungslogik und PT1-Suche lassen sich mit den beiliegenden Tests ohne GUI
oder reale Netzwerkpfade prüfen:

```sh
python -m unittest discover -s tools -p 'test_*.py'
```
