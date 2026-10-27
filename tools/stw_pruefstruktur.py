#!/usr/bin/env python3
"""
Prüfstruktur für Stellwerksprojekte anlegen (mit grafischer Oberfläche).

Ablage:  <Basis>\\<Region>\\<RIL100> - <Klarname>\\<Anlagenzustand>_<PSP>_<Projektbeschreibung>
Beispiel: C:\\Projekte\\OST\\BLN - Lübbenau\\0180_M17525-01_Zweigleisigkeit

- Region auswählen.
- Betriebsstelle aus der Liste der vorhandenen Ordner der Region wählen
  oder ein neues RIL100-Kürzel eintippen.
- Ordner, die nur aus dem RIL100-Kürzel bestehen (z. B. "BLN"), erscheinen
  ebenfalls in der Liste. Wird ein Klarname eingegeben, wird der Ordner zu
  "<RIL100> - <Klarname>" umbenannt (vervollständigt).
- Existiert der Ordner der Betriebsstelle nicht, wird er als
  "<RIL100> - <Klarname>" angelegt.
- Automatische Vorauswahl der Quellordner:
    PT1: nach Eingabe des PSP-Elements (auch mit Buchstabenzusatz, z. B. M19061-01A).
         Ist im Projektordner "001_PT1\\002_PT1 elektronisch" vorhanden, wird dieser gewählt:
         M17527-01  -> \\\\Thsdiza06fs01\\psp\\M17xxx\\M17527-01 Zweigleisigkeit Lübbenau-Cottbus\\001_PT1\\002_PT1 elektronisch
         M19061-01A -> \\\\Thsdiza06fs01\\psp\\M19xxx\\M19061-01A …\\001_PT1\\002_PT1 elektronisch
                       (ersatzweise M19061-01 …, falls kein Ordner mit "A" existiert)
    PT2: nach Wahl von Region und RIL100-Kürzel; es zählen nur die ersten 3 Stellen, z. B.
         OST + BLN -> \\\\destgsfs10\\IL90-Projekte-ro\\OST\\BLN0  (oder BLNX, BLN1 …)
- Kopiert optional je einen Ordner von den Ablagelaufwerken nach
  01_Eingangsunterlagen/PT1/<Stellwerk|ZX|sonstiges> und
  01_Eingangsunterlagen/PT2/<Stellwerk|ZX>
- Unterordner werden beliebig tief bei Bedarf geladen. Markierte Ordner enthalten
  alle Nachkommen; „Dateien in diesem Ordner“ kopiert nur die jeweilige Ebene.
  Ohne Unterordner wird die Quelle vollständig ins Standardziel übernommen.
- Netzwerkabfragen laufen verzögert im Hintergrund. Die Projektvorschau greift
  nicht auf das Dateisystem zu; vor dem Anlegen wird die Betriebsstelle neu geprüft.
- PT1 schlägt die Projektbeschreibung vor; eigene Eingaben bleiben erhalten.
- Lange Windows-Pfade einschließlich UNC-Freigaben werden unterstützt.
- Kopien werden über .part-Dateien atomar abgeschlossen, vorhandene Dateien
  bleiben erhalten. Abbrechen beendet nach der laufenden Datei; erneutes Anlegen
  setzt die Kopie fort. Fehler und Abbrüche stehen in Kopierfehler.txt.
- Verzeichnisverknüpfungen und Windows-Junctions werden nicht rekursiv betreten.
  Änderungen an Quellen und Auswahl während einer Kopie gelten erst für den
  nächsten Kopierlauf; laufende Aufträge verwenden eine feste Momentaufnahme.
  Diese wird vor dem Bestätigungsdialog gebildet. Gleiche Quellpfade behalten
  ihre Auswahl; nur ein ausdrücklich angefordertes Neuladen setzt sie zurück.
- Projektinfo.txt hält Quellen und Ordnerauswahl fest. Weitere Läufe hängen den
  neuen Kopierplan an; vorhandene Projektangaben bleiben unverändert erhalten.

Voraussetzung: Python 3.8+ (tkinter ist in der Windows-Installation enthalten)
Start: Doppelklick oder  python stw_pruefstruktur.py
"""
import os
import ntpath
import queue
import re
import shutil
import stat
import threading
import tkinter as tk
from datetime import date, datetime
from pathlib import Path
from tkinter import ttk, filedialog, messagebox

# ---------------------------------------------------------------- Einstellungen
# Basisverzeichnis, unter dem die Regionen liegen
STANDARD_BASIS = r"C:\Projekte"

# Anzeigename -> Ordnername auf dem Laufwerk (gilt auch für das PT2-Laufwerk)
REGIONEN = {
    "Nord": "NORD",
    "Ost": "OST",
    "Südost": "SUEDOST",
    "Süd": "SUED",
    "Südwest": "SUEDWEST",
    "West": "WEST",
}

# Kopierbereiche: Kennung -> (Pfad im Projekt, mögliche Unterordner, Laufwerk/Startordner)
# Hinweis: UNC-Pfade in r"..." ohne abschließenden Backslash angeben.
KOPIERBEREICHE = {
    "PT1": (Path("01_Eingangsunterlagen", "PT1"), ["Stellwerk", "ZX", "sonstiges"],
            r"\\Thsdiza06fs01\psp"),
    "PT2": (Path("01_Eingangsunterlagen", "PT2"), ["Stellwerk", "ZX"],
            r"\\destgsfs10\IL90-Projekte-ro"),
}

# PT1: Gruppenordner = erste 3 Zeichen der PSP + "xxx"  (M17527-01 -> M17xxx)
PT1_GRUPPE_STELLEN = 3
PT1_GRUPPE_SUFFIX = "xxx"
# PT1: innerhalb des Projektordners direkt in diesen Unterordner springen (falls vorhanden)
PT1_UNTERORDNER = Path("001_PT1", "002_PT1 elektronisch")
# PT2: nur die ersten 3 Stellen des RIL100-Kürzels verwenden (BLN0, BLNX -> BLN)
PT2_RIL_STELLEN = 3
# PT2: bevorzugte 4. Stelle in dieser Reihenfolge (BLN0 vor BLNX vor Rest)
PT2_BEVORZUGT = ["0", "X"]

# Einrückung mit 2 Leerzeichen = Unterordner
VORLAGE = """
00_Verwaltung
  Auftrag
  Schriftverkehr
  Termine_Besprechungen
01_Eingangsunterlagen
  PT1
    Stellwerk
    ZX
    sonstiges
  PT2
    Stellwerk
    ZX
02_Pruefgrundlagen
  Regelwerke_Richtlinien
  Normen
  Pruefanweisungen_Checklisten
  CAE_Freigaben
  Konfigurationen
03_Pruefung
  01_Formale_Pruefung
  02_Fachliche_Pruefung
  03_Datenpruefung
  04_Simulation_Test
04_Pruefbemerkungen
  Offen
  Erledigt
05_Ergebnisse
  Pruefprotokolle
  Pruefbericht
  Freigabe
99_Archiv
"""

# Kennzeichnung in der Auswahlliste für Ordner ohne Klarnamen
OHNE_KLARNAME = "  (Klarname fehlt)"
VERZOEGERUNG_SUCHE = 500
VERZOEGERUNG_BASIS = 500
VERZOEGERUNG_VORSCHAU = 400
BESCHR_MAX = 40
PROJEKTPFAD_MAX = 120
LANG_PRAEFIX = "\\\\?\\"
LANG_UNC_PRAEFIX = "\\\\?\\UNC\\"
ABBRUCH_HINWEIS = "Vom Benutzer abgebrochen (nach der laufenden Datei)."

PSP_MUSTER = re.compile(r"^[A-Z]\d{5}-\d{2}[A-Z]?$")     # z. B. M17525-01, M19061-01A
PT1_PSP_PRAEFIX = re.compile(r'^[A-Z]\d{5}-\d{2}[A-Z]?[\s_\-]*', re.IGNORECASE)
AZ_MUSTER = re.compile(r"^\d{4}$")                       # z. B. 0180
RIL_MUSTER = re.compile(r"^[A-ZÄÖÜ][A-ZÄÖÜ0-9 ]{1,4}$")  # z. B. BLN, BL, BLN F
# Ordner "<RIL> - <Name>"
BST_MIT_KLARNAME = re.compile(r'^(?P<ril>[A-ZÄÖÜ][A-ZÄÖÜ0-9 ]{1,4}?)\s*-\s*\S')
BST_NUR_RIL = re.compile(r'^[A-ZÄÖÜ][A-ZÄÖÜ0-9 ]{1,4}$')
KEINE_BETRIEBSSTELLE = {
    "ALT", "NEU", "TEMP", "TMP", "ARCHIV", "VORLAGE", "VORLAGEN",
    "KOPIE", "TEST", "SONSTIGES",
}
_AUSSCHLUSS = {x.casefold() for x in KEINE_BETRIEBSSTELLE}
UNGUELTIG = re.compile(r'[<>:"/\\|?*\x00-\x1f\x7f]')
RESERVIERT = re.compile(r"^(?:CON|PRN|AUX|NUL|COM[0-9]|LPT[0-9])(?:\.|$)", re.I)

HINWEIS_LEER = {
    "PT1": "Wird nach Eingabe des PSP-Elements automatisch gesucht.",
    "PT2": "Wird nach Wahl von Region und Betriebsstelle automatisch gesucht.",
}


# ---------------------------------------------------------------- Logik
def langer_pfad(pfad):
    """Windows-Pfade einschließlich UNC für lange Dateinamen vorbereiten."""
    text = os.fspath(pfad)
    if os.name != "nt" or text.startswith(LANG_PRAEFIX):
        return Path(text)
    text = ntpath.abspath(text)
    if text.startswith("\\\\"):
        return Path(LANG_UNC_PRAEFIX + text[2:])
    return Path(LANG_PRAEFIX + text)


def anzeige_pfad(pfad):
    text = os.fspath(pfad)
    # OSError verwendet für Dateinamen repr(), also verdoppelte Backslashes.
    text = text.replace(repr(LANG_UNC_PRAEFIX)[1:-1], repr("\\\\")[1:-1])
    text = text.replace(repr(LANG_PRAEFIX)[1:-1], "")
    return text.replace(LANG_UNC_PRAEFIX, "\\\\").replace(LANG_PRAEFIX, "")


def gleicher_pfad(einer, anderer):
    if not einer or not anderer:
        return einer == anderer
    return Path(anzeige_pfad(einer)) == Path(anzeige_pfad(anderer))


def _windows_name(name):
    name = UNGUELTIG.sub("_", name.strip()).rstrip(". ")
    if RESERVIERT.match(name):
        name = "_" + name
    return name or "_"


def bereinigen(name: str) -> str:
    """Für Projekt- und Strukturordner: ungültige Zeichen und Leerzeichen -> _"""
    return _windows_name(name).replace(" ", "_")


def bereinigen_mit_leerzeichen(name: str) -> str:
    """Für Region/Betriebsstelle: Leerzeichen bleiben erhalten."""
    return _windows_name(name)


def hat_klarname(ordnername: str) -> bool:
    m = BST_MIT_KLARNAME.match(ordnername.strip())
    return bool(m) and m.group('ril').strip().casefold() not in _AUSSCHLUSS


def ist_betriebsstelle(ordnername: str) -> bool:
    name = ordnername.strip()
    if name.casefold() in _AUSSCHLUSS:
        return False
    return hat_klarname(name) or bool(BST_NUR_RIL.match(name))


def ril_aus_ordner(ordnername: str) -> str:
    teil = ordnername.split("-", 1)[0] if hat_klarname(ordnername) else ordnername
    return " ".join(teil.upper().split())


def anzeige_name(name: str) -> str:
    return name if hat_klarname(name) else name + OHNE_KLARNAME


def ril_aus_eingabe(text: str, bst_map=None) -> str:
    text = (bst_map or {}).get(text.strip(), text.strip())
    suffix = OHNE_KLARNAME.strip()
    if text.endswith(suffix):
        text = text[:-len(suffix)].rstrip()
    return ril_aus_ordner(text.split("-", 1)[0])


def betriebsstelle_pruefen(region, auswahl, ril, klar, bst_map):
    """Frische Prüfung; nur diese Funktion und Listenabfragen benötigen I/O."""
    region = langer_pfad(region)
    if not ril:
        return None, False, None
    ordner = region / bst_map[auswahl] if auswahl in bst_map else None
    if ordner is None or not ordner.is_dir():
        ordner = betriebsstelle_suchen(region, ril)
    if ordner is not None:
        neu = (region / bereinigen_mit_leerzeichen(f"{ril} - {klar}")
               if klar and not hat_klarname(ordner.name) else None)
        return ordner, True, neu
    if not klar and "-" in auswahl:
        klar = auswahl.split("-", 1)[1].strip()
    return ((region / bereinigen_mit_leerzeichen(f"{ril} - {klar}"), False, None)
            if klar else (None, False, None))


def beschreibung_aus_pt1(quelle):
    return PT1_PSP_PRAEFIX.sub('', zielname(Path(quelle))).strip(' _-')


def vorlage_parsen(text: str):
    pfade, stapel = [], []
    for zeile in text.splitlines():
        if not zeile.strip() or zeile.lstrip().startswith("#"):
            continue
        tiefe = (len(zeile) - len(zeile.lstrip(" "))) // 2
        stapel = stapel[:tiefe] + [bereinigen(zeile)]
        pfade.append(Path(*stapel))
    return pfade


def region_ordner(basis: Path, region_anzeige: str) -> Path:
    """Sucht den Regionsordner (Groß-/Kleinschreibung egal), sonst Standardname."""
    basis = langer_pfad(basis)
    soll = REGIONEN.get(region_anzeige, region_anzeige)
    try:
        if basis.is_dir():
            for d in basis.iterdir():
                if d.is_dir() and d.name.casefold() in (soll.casefold(), region_anzeige.casefold()):
                    return d
    except OSError:
        pass
    return basis / bereinigen_mit_leerzeichen(soll)


def betriebsstellen_auflisten(region: Path):
    """Alle Unterordner der Region, die wie eine Betriebsstelle aussehen."""
    region = langer_pfad(region)
    try:
        if not region.is_dir():
            return []
        return sorted((d.name for d in region.iterdir()
                       if d.is_dir() and ist_betriebsstelle(d.name)), key=str.casefold)
    except OSError:
        return []


def betriebsstelle_suchen(region: Path, ril: str):
    """Vorhandenen Ordner zum RIL100-Kürzel suchen (mit Klarname bevorzugt) oder None."""
    region = langer_pfad(region)
    try:
        if not region.is_dir():
            return None
        treffer = [d for d in region.iterdir()
                   if d.is_dir() and ist_betriebsstelle(d.name) and ril_aus_ordner(d.name) == ril]
    except OSError:
        return None
    if not treffer:
        return None
    return sorted(treffer, key=lambda d: (not hat_klarname(d.name), d.name.casefold()))[0]


# ---------------------------------------------------------------- Quellordner suchen
def pt1_gruppenordner(psp: str) -> Path:
    """M17527-01 -> \\\\Thsdiza06fs01\\psp\\M17xxx"""
    return langer_pfad(KOPIERBEREICHE["PT1"][2]) / (psp[:PT1_GRUPPE_STELLEN].upper() + PT1_GRUPPE_SUFFIX)


def pt1_ordner_finden(psp: str):
    """
    Sucht auf dem PT1-Laufwerk den Projektordner zur PSP.
    -> (Treffer, Fehlertext oder None).
    - Treffer: Name beginnt mit der PSP, gefolgt von Leerzeichen, '_', '-' oder Ende.
    - M19061-01A: erst exakt suchen, sonst ersatzweise nach M19061-01.
    - Existiert <Projektordner>\\001_PT1\\002_PT1 elektronisch, wird dieser geliefert.
    """
    psp = psp.strip().upper()
    gruppe = pt1_gruppenordner(psp)
    ohne_zusatz = re.sub(r"[A-Z]+$", "", psp)          # M19061-01A -> M19061-01
    suchbegriffe = [psp] if ohne_zusatz == psp else [psp, ohne_zusatz]
    try:
        if not gruppe.is_dir():
            return [], f"Ordner nicht gefunden: {anzeige_pfad(gruppe)}"
        ordner = [d for d in gruppe.iterdir() if d.is_dir()]
        treffer = []
        for begriff in suchbegriffe:
            muster = re.compile(r"^" + re.escape(begriff) + r"(?:[\s_\-]|$)", re.IGNORECASE)
            treffer = sorted((d for d in ordner if muster.match(d.name)),
                             key=lambda d: d.name.casefold())
            if treffer:
                break
        if not treffer:
            return [], f"Kein Ordner für {psp} in {anzeige_pfad(gruppe)} gefunden."
        ergebnis = []
        for d in treffer:
            unter = d / PT1_UNTERORDNER
            ergebnis.append(unter if unter.is_dir() else d)
    except OSError as e:
        return [], f"PT1-Laufwerk nicht lesbar: {anzeige_pfad(str(e))}"
    return ergebnis, None


def kurzpfad(kennung: str, pfad: Path) -> str:
    """Pfad relativ zum Laufwerk anzeigen (M19xxx\\M19061-01A …\\001_PT1\\…)."""
    try:
        return str(pfad.relative_to(langer_pfad(KOPIERBEREICHE[kennung][2])))
    except ValueError:
        return pfad.name


def zielname(quelle: Path) -> str:
    """Name des Zielordners: bei ...\\001_PT1\\002_PT1 elektronisch den Projektordnernamen nehmen."""
    if len(quelle.parts) > 2 and quelle.parts[-2:] == PT1_UNTERORDNER.parts:
        return quelle.parents[1].name
    return quelle.name


def pt2_regionsordner(region_anzeige: str) -> Path:
    """Ost -> \\\\destgsfs10\\IL90-Projekte-ro\\OST"""
    return region_ordner(Path(KOPIERBEREICHE["PT2"][2]), region_anzeige)


def pt2_kern(ril: str) -> str:
    """Erste 3 Stellen des RIL100-Kürzels (ohne Leerzeichen)."""
    return ril.replace(" ", "")[:PT2_RIL_STELLEN]


def pt2_ordner_finden(region_anzeige: str, ril: str):
    """
    Sucht auf dem PT2-Laufwerk den Ordner zur Betriebsstelle.
    -> (Treffer, Fehlertext oder None).
    Es zählen nur die ersten 3 Stellen des RIL100-Kürzels; danach sind 0/X/Ziffern
    und ein Zusatz erlaubt (BLN, BLN0, BLNX, BLN1, BLN0_alt …).
    Reihenfolge: BLN0, BLNX, dann alphabetisch.
    """
    region = pt2_regionsordner(region_anzeige)
    kern = pt2_kern(ril)
    muster = re.compile(r"^" + re.escape(kern) + r"[0-9X]*(?:[\s_\-].*)?$", re.IGNORECASE)
    rang = {(kern + s).casefold(): i for i, s in enumerate(PT2_BEVORZUGT)}
    try:
        if not region.is_dir():
            return [], f"Ordner nicht gefunden: {anzeige_pfad(region)}"
        treffer = [d for d in region.iterdir() if d.is_dir() and muster.match(d.name)]
    except OSError as e:
        return [], f"PT2-Laufwerk nicht lesbar: {anzeige_pfad(str(e))}"
    if not treffer:
        return [], f"Kein Ordner für {kern} in {anzeige_pfad(region)} gefunden."
    treffer.sort(key=lambda d: (rang.get(d.name.casefold(), len(rang)), d.name.casefold()))
    return treffer, None


def datei_kopieren(src, dst):
    """Atomar veröffentlichen; False bei vorhandenem Ziel, sonst True; Reste entfernen."""
    src, dst = langer_pfad(src), langer_pfad(dst)
    teil = dst.with_name(dst.name + ".part")
    if os.path.lexists(dst):
        return False
    if teil.is_dir() or teil.is_symlink():
        raise OSError(f"Temporäres Kopierziel ist ein Ordner oder eine Verknüpfung: {teil}")
    try:
        shutil.copy2(src, teil)
        if os.path.lexists(dst):
            return False
        teil.replace(dst)
        return True
    finally:
        try:
            teil.unlink()
        except OSError:
            pass


def ordner_verknuepfung(pfad):
    """Symlinks/Junctions abweisen, Cloud-Reparse-Verzeichnisse aber zulassen."""
    status = os.lstat(langer_pfad(pfad))
    return (stat.S_ISLNK(status.st_mode)
            or getattr(status, "st_reparse_tag", 0) in {
                getattr(stat, "IO_REPARSE_TAG_MOUNT_POINT", 0xA0000003),
                getattr(stat, "IO_REPARSE_TAG_SYMLINK", 0xA000000C),
            })


def ordner_kopieren(auftraege, q: queue.Queue, abbruch: threading.Event = None):
    """Aufträge (Bezeichnung, Quelle, Ziel, nur_dateien), ohne Überschreiben.

    Pro Auftrag genau ein os.walk; .part-Dateien werden nie übernommen.
    Abbruch wird vor der nächsten Datei und während der Ermittlung geprüft.
    """
    abbruch = abbruch or threading.Event()
    ergebnisse = []
    for kennung, quelle, ziel, nur_dateien in auftraege:
        kopiert = uebersprungen = 0
        fehler, dateien, ordner = [], [], []
        abbruchtext = None
        try:
            q.put(("start", kennung))
            if abbruch.is_set():
                q.put(("max", 0))
                ergebnisse.append((kennung, 0, 0, [], ABBRUCH_HINWEIS))
                continue
            quelle, ziel = langer_pfad(quelle), langer_pfad(ziel)

            def lauf_fehler(fehlerwert):
                fehler.append(anzeige_pfad(str(fehlerwert)))

            if not abbruch.is_set():
                for wurzel, unterordner, namen in os.walk(quelle, onerror=lauf_fehler):
                    if abbruch.is_set():
                        break
                    durchlaufen = []
                    for name in unterordner:
                        if abbruch.is_set():
                            break
                        try:
                            if not ordner_verknuepfung(Path(wurzel) / name):
                                durchlaufen.append(name)
                        except OSError as e:
                            lauf_fehler(e)
                    unterordner[:] = durchlaufen
                    relativ = Path(wurzel).relative_to(quelle)
                    ordner.append(ziel / relativ)
                    dateien.extend((Path(wurzel) / n, ziel / relativ / n)
                                   for n in namen if not n.lower().endswith(".part"))
                    if nur_dateien:
                        unterordner.clear()
            q.put(("max", len(dateien)))
            for ordnerziel in ordner:
                if abbruch.is_set():
                    break
                try:
                    ordnerziel.mkdir(parents=True, exist_ok=True)
                except OSError as e:
                    fehler.append(f"{anzeige_pfad(ordnerziel)}: {anzeige_pfad(str(e))}")
            for i, (src, dst) in enumerate(dateien, 1):
                if abbruch.is_set():
                    break
                try:
                    if os.path.lexists(dst):
                        uebersprungen += 1
                    else:
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        if datei_kopieren(src, dst) is False:
                            uebersprungen += 1
                        else:
                            kopiert += 1
                except OSError as e:
                    fehler.append(f"{anzeige_pfad(src)}: {anzeige_pfad(str(e))}")
                q.put(("fortschritt", i, kennung, src.name))
        except Exception as e:  # z. B. Laufwerk nicht erreichbar
            fehler.append(anzeige_pfad(str(e)))
        if abbruch.is_set():
            abbruchtext = ABBRUCH_HINWEIS
        ergebnisse.append((kennung, kopiert, uebersprungen, fehler, abbruchtext))
    q.put(("fertig", ergebnisse))


def ordner_inhalt(pfad):
    """Direkte Unterordner sortiert und Kennzeichen für reguläre Dateien."""
    ordner, hat_dateien = [], False
    with os.scandir(langer_pfad(pfad)) as eintraege:
        for eintrag in eintraege:
            if eintrag.is_dir(follow_symlinks=False):
                unter = Path(pfad) / eintrag.name
                if not ordner_verknuepfung(unter):
                    ordner.append(unter)
            elif (not eintrag.name.lower().endswith(".part")
                  and eintrag.is_file(follow_symlinks=False)):
                hat_dateien = True
    return sorted(ordner, key=lambda p: p.name.casefold()), hat_dateien


class OrdnerAuswahl(ttk.Frame):
    """Asynchroner, beliebig tief ladender Auswahlbaum mit getrennten Zielen."""

    def __init__(self, master, kennung, quelle, standardziel, geaendert):
        super().__init__(master)
        self.kennung, self.quelle = kennung, quelle
        self.standardziel, self.geaendert = standardziel, geaendert
        self.q = queue.Queue()
        self.generation = 0
        self.job = None
        self.ausstehend = False
        self.fehler = None
        self.wurzel = None
        self.quellwert = ""
        self.hat_unterordner = False
        self.knoten, self.markiert, self.geladen, self.ladend = {}, {}, set(), set()
        self.baum = ttk.Treeview(self, columns=("ziel",), height=7, selectmode="browse")
        self.baum.heading("#0", text="Ordner / Auswahl")
        self.baum.heading("ziel", text="Kopieren nach")
        self.baum.column("#0", width=400)
        self.baum.column("ziel", width=130, stretch=False)
        self.columnconfigure(0, weight=1)
        self.baum.grid(row=0, column=0, columnspan=4, sticky="nsew")
        bildlauf = ttk.Scrollbar(self, orient="vertical", command=self.baum.yview)
        bildlauf.grid(row=0, column=4, sticky="ns")
        self.baum.config(yscrollcommand=bildlauf.set)
        ttk.Button(self, text="Alle", command=self.alle).grid(row=1, column=0, sticky="w")
        ttk.Button(self, text="Keine", command=self.keine).grid(row=1, column=1, sticky="w")
        ttk.Label(self, text="Standardziel für neue Häkchen").grid(
            row=1, column=2, sticky="e")
        ttk.Combobox(self, textvariable=standardziel, state="readonly", width=15,
                     values=KOPIERBEREICHE[kennung][1]).grid(row=1, column=3, sticky="e")
        self.info = ttk.Label(self, text="Keine Quelle gewählt.", foreground="gray", wraplength=560)
        self.info.grid(row=2, column=0, columnspan=5, sticky="w")
        self.baum.bind("<<TreeviewOpen>>", self.oeffnen)
        self.baum.bind("<Button-1>", self.klicken)
        self.baum.bind("<space>", self.tastatur)
        quelle.trace_add("write", lambda *_: self.wurzel_planen())
        standardziel.trace_add("write", lambda *_: self.anzeigen())
        self.after(100, self.abfragen)

    def wurzel_planen(self, neu_laden=False):
        text = self.quelle.get().strip()
        if not neu_laden and gleicher_pfad(text, self.quellwert):
            return
        self.quellwert = text
        self.generation += 1
        if self.job:
            self.after_cancel(self.job)
        self.ausstehend = True
        self.fehler = None
        self.info.config(text="Quelle wird eingelesen …", foreground="gray")
        self.geaendert()
        self.job = self.after(VERZOEGERUNG_VORSCHAU, self.wurzel_laden)

    def wurzel_laden(self):
        self.job = None
        self.baum.delete(*self.baum.get_children())
        self.knoten, self.markiert, self.geladen, self.ladend = {}, {}, set(), set()
        text = self.quelle.get().strip()
        self.wurzel = Path(text) if text else None
        self.hat_unterordner = False
        if self.wurzel is None:
            self.ausstehend = False
            self.anzeigen()
            return
        self.laden("", self.wurzel)

    def laden(self, knoten, pfad):
        if knoten in self.geladen or knoten in self.ladend:
            return
        self.ladend.add(knoten)
        generation = self.generation

        def arbeit():
            try:
                ordner, dateien = ordner_inhalt(pfad)
                fehler = None
            except Exception as e:
                ordner, dateien, fehler = [], False, anzeige_pfad(str(e))
            self.q.put((generation, knoten, pfad, ordner, dateien, fehler))

        threading.Thread(target=arbeit, daemon=True).start()

    def abfragen(self):
        try:
            while True:
                generation, knoten, pfad, ordner, dateien, fehler = self.q.get_nowait()
                if generation != self.generation:
                    continue
                self.ladend.discard(knoten)
                if knoten and not self.baum.exists(knoten):
                    continue
                self.baum.delete(*self.baum.get_children(knoten))
                self.geladen.add(knoten)
                if not knoten:
                    self.ausstehend = False
                    self.hat_unterordner = bool(ordner)
                if fehler:
                    self.fehler = f"Quelle nicht lesbar: {anzeige_pfad(pfad)}: {fehler}"
                else:
                    if dateien:
                        eintrag = self.baum.insert(knoten, "end")
                        self.knoten[eintrag] = (pfad, True)
                    for unter in ordner:
                        eintrag = self.baum.insert(knoten, "end")
                        self.knoten[eintrag] = (unter, False)
                        self.baum.insert(eintrag, "end", text="…")
                self.anzeigen()
        except queue.Empty:
            pass
        self.after(100, self.abfragen)

    def oeffnen(self, _=None):
        knoten = self.baum.focus()
        if knoten in self.knoten and not self.knoten[knoten][1]:
            self.laden(knoten, self.knoten[knoten][0])

    def uebergeordnet(self, pfad, nur_dateien):
        for (anderer, nur), ziel in self.markiert.items():
            if not nur and ((anderer == pfad and nur_dateien) or anderer in pfad.parents):
                return ziel
        return None

    def umschalten(self, knoten):
        if self.ausstehend or not self.hat_unterordner or knoten not in self.knoten:
            return
        pfad, nur = self.knoten[knoten]
        if self.uebergeordnet(pfad, nur):
            return
        schluessel = (pfad, nur)
        if schluessel in self.markiert:
            del self.markiert[schluessel]
        else:
            if not nur:
                self.markiert = {k: z for k, z in self.markiert.items()
                                 if not (pfad in k[0].parents or k[0] == pfad)}
            self.markiert[schluessel] = self.standardziel.get()
        self.anzeigen()

    def tastatur(self, _=None):
        self.umschalten(self.baum.focus())
        return "break"

    def klicken(self, ereignis):
        knoten = self.baum.identify_row(ereignis.y)
        if knoten not in self.knoten:
            return
        if self.baum.identify_column(ereignis.x) == "#1":
            schluessel = self.knoten[knoten]
            if schluessel in self.markiert:
                menu = tk.Menu(self, tearoff=False)
                for ziel in KOPIERBEREICHE[self.kennung][1]:
                    menu.add_command(label=ziel, command=lambda z=ziel, k=schluessel:
                                     self.ziel_setzen(k, z))
                try:
                    menu.tk_popup(ereignis.x_root, ereignis.y_root)
                finally:
                    menu.grab_release()
            return "break"
        if self.baum.identify("element", ereignis.x, ereignis.y) != "Treeitem.indicator":
            self.umschalten(knoten)

    def ziel_setzen(self, schluessel, ziel):
        self.markiert[schluessel] = ziel
        self.anzeigen()

    def alle(self):
        if self.ausstehend or self.fehler:
            return
        self.markiert = {self.knoten[k]: self.standardziel.get()
                         for k in self.baum.get_children() if k in self.knoten}
        self.anzeigen()

    def keine(self):
        self.markiert.clear()
        self.anzeigen()

    def auswahl(self):
        if self.wurzel is None or self.ausstehend or self.fehler:
            return []
        if not self.hat_unterordner:
            return [(self.wurzel, False, self.standardziel.get(), Path("."))]
        return [(p, nur, ziel, p.relative_to(self.wurzel))
                for (p, nur), ziel in self.markiert.items()]

    def anzeigen(self):
        for knoten, (pfad, nur) in self.knoten.items():
            ziel = self.uebergeordnet(pfad, nur)
            if not self.hat_unterordner and self.wurzel is not None:
                ziel = self.standardziel.get()
            gewaehlt = (pfad, nur) in self.markiert
            zeichen = "▣" if ziel else ("☑" if gewaehlt else "☐")
            name = "(Dateien in diesem Ordner)" if nur else pfad.name
            self.baum.item(knoten, text=f"{zeichen} {name}" + (" (übergeordnet)" if ziel else ""),
                           values=(ziel or self.markiert.get((pfad, nur), ""),))
        if self.fehler:
            text = self.fehler
        elif self.ausstehend:
            text = "Quelle wird eingelesen …"
        elif self.wurzel is None:
            text = "Keine Quelle gewählt."
        elif not self.hat_unterordner:
            text = "Keine Unterordner: vollständige Quelle ins Standardziel kopieren."
        else:
            zusammenfassung = "; ".join(
                f"{p.relative_to(self.wurzel)} → {ziel}" + (" [nur Dateien]" if nur else "")
                for (p, nur), ziel in self.markiert.items())
            text = (f"{len(self.markiert)} Auswahl(en): {zusammenfassung or 'Bitte auswählen.'}\n"
                    "Ordner enthalten alle Nachkommen. Ziel markierter Zeilen anklicken zum Ändern.")
        self.info.config(text=text, foreground="darkorange" if self.fehler else "gray")
        self.geaendert()


# ---------------------------------------------------------------- Oberfläche
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Prüfstruktur Stellwerksprojekt")
        self.resizable(True, True)
        self.q = queue.Queue()
        self.such_q = queue.Queue()                       # Ergebnisse der Quellordner-Suche
        self.bst_q = queue.Queue()
        self.bst_nr = 0
        self.basis_job = None
        self.vorschau_job = None
        self.liste_ausstehend = False
        self.bst_ergebnis = (None, False, None)
        self.bst_region = Path(STANDARD_BASIS) / REGIONEN["Ost"]
        self.bst_fehler = None
        self.kopier_thread = None
        self.abbruch = threading.Event()
        self.schliessen_ausstehend = False
        self.auto_beschr = ""
        self.auswahl_meldung = ""
        self.auswahlen = {}
        self.wurzel = None
        self.bst_map = {}                                 # Anzeigetext -> echter Ordnername
        self.such_job = {k: None for k in KOPIERBEREICHE}  # Verzögerung beim Tippen
        self.such_nr = {k: 0 for k in KOPIERBEREICHE}      # nur letzte Suche zählt
        self.auto_wert = {k: "" for k in KOPIERBEREICHE}   # zuletzt automatisch gesetzter Pfad
        self.hinweise = {}

        self.basis = tk.StringVar(value=STANDARD_BASIS)
        self.region = tk.StringVar(value="Ost")
        self.bst = tk.StringVar()          # Auswahl aus Liste ODER getipptes RIL100-Kürzel
        self.klarname = tk.StringVar()
        self.psp = tk.StringVar()
        self.az = tk.StringVar()
        self.beschr = tk.StringVar()
        self.quellen = {k: tk.StringVar() for k in KOPIERBEREICHE}
        self.unterziele = {k: tk.StringVar(value=v[1][0]) for k, v in KOPIERBEREICHE.items()}

        # Die beiden Auswahlbäume müssen auch auf kleineren Bildschirmen bedienbar bleiben.
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        rahmen = ttk.Frame(self)
        rahmen.grid(sticky="nsew")
        rahmen.rowconfigure(0, weight=1)
        rahmen.columnconfigure(0, weight=1)
        flaeche = tk.Canvas(rahmen, highlightthickness=0)
        flaeche.grid(row=0, column=0, sticky="nsew")
        bildlauf = ttk.Scrollbar(rahmen, orient="vertical", command=flaeche.yview)
        bildlauf.grid(row=0, column=1, sticky="ns")
        flaeche.config(yscrollcommand=bildlauf.set)
        f = ttk.Frame(flaeche, padding=12)
        fenster = flaeche.create_window(0, 0, window=f, anchor="nw")
        f.bind("<Configure>", lambda _: flaeche.config(scrollregion=flaeche.bbox("all")))
        flaeche.bind("<Configure>", lambda e: flaeche.itemconfigure(fenster, width=e.width))
        r = 0

        def zeile(text, widget, button=None):
            nonlocal r
            ttk.Label(f, text=text).grid(row=r, column=0, sticky="w", pady=3)
            widget.grid(row=r, column=1, padx=5, sticky="w")
            if button:
                button.grid(row=r, column=2, sticky="we")
            r += 1

        def ueberschrift(text):
            nonlocal r
            ttk.Label(f, text=text, font=("", 10, "bold")).grid(
                row=r, column=0, sticky="w", pady=(8, 0))
            r += 1

        # --- Ablageort
        ueberschrift("Ablageort")
        zeile("Basisverzeichnis:", ttk.Entry(f, textvariable=self.basis, width=55),
              ttk.Button(f, text="Durchsuchen…", command=self.basis_waehlen))
        self.region_box = ttk.Combobox(f, textvariable=self.region, values=list(REGIONEN),
                                       state="readonly", width=20)
        zeile("Region:", self.region_box)
        self.bst_box = ttk.Combobox(f, textvariable=self.bst, width=52,
                                    postcommand=self.liste_filtern)
        zeile("Betriebsstelle / RIL100:", self.bst_box,
              ttk.Button(f, text="Aktualisieren", command=self.liste_aktualisieren))
        ttk.Label(f, text="Aus Liste wählen oder neues RIL100-Kürzel eintippen (z. B. BLN).",
                  foreground="gray").grid(row=r, column=1, sticky="w", padx=5); r += 1
        self.klar_entry = ttk.Entry(f, textvariable=self.klarname, width=55)
        zeile("Klarname (Neuanlage/Ergänzung):", self.klar_entry)
        self.bst_status = ttk.Label(f, foreground="gray", wraplength=650, justify="left")
        self.bst_status.grid(row=r, column=0, columnspan=3, sticky="w"); r += 1

        # --- Projekt
        ueberschrift("Projekt")
        zeile("Anlagenzustand (z. B. 0180):", ttk.Entry(f, textvariable=self.az, width=55))
        zeile("PSP-Element (z. B. M17525-01):", ttk.Entry(f, textvariable=self.psp, width=55))
        zeile("Projektbeschreibung:", ttk.Entry(f, textvariable=self.beschr, width=55))
        self.beschr_hinweis = ttk.Label(f, foreground="gray", wraplength=600)
        self.beschr_hinweis.grid(row=r, column=1, columnspan=2, sticky="w"); r += 1
        self.laengen_hinweis = ttk.Label(f, foreground="gray", wraplength=650)
        self.laengen_hinweis.grid(row=r, column=0, columnspan=3, sticky="w"); r += 1

        # --- PT1 / PT2
        for kennung, (_, unterordner, start) in KOPIERBEREICHE.items():
            ueberschrift(f"{kennung}-Unterlagen  ({start})")
            zeile(f"{kennung}-Quellordner (optional):",
                  ttk.Entry(f, textvariable=self.quellen[kennung], width=55),
                  ttk.Button(f, text="Durchsuchen…",
                             command=lambda k=kennung: self.quelle_waehlen(k)))
            self.hinweise[kennung] = ttk.Label(f, foreground="gray", wraplength=520,
                                               justify="left", text=HINWEIS_LEER[kennung])
            self.hinweise[kennung].grid(row=r, column=1, columnspan=2, sticky="w", padx=5); r += 1
            auswahl = OrdnerAuswahl(f, kennung, self.quellen[kennung],
                                     self.unterziele[kennung], self.knopf_aktualisieren)
            self.auswahlen[kennung] = auswahl
            auswahl.grid(row=r, column=0, columnspan=3, sticky="we"); r += 1

        self.vorschau = ttk.Label(f, foreground="gray", wraplength=650, justify="left")
        self.vorschau.grid(row=r, column=0, columnspan=3, sticky="w", pady=(8, 0)); r += 1

        self.balken = ttk.Progressbar(f, length=500)
        self.balken.grid(row=r, column=0, columnspan=3, pady=8, sticky="we"); r += 1
        self.status = ttk.Label(f, text="Bereit.")
        self.status.grid(row=r, column=0, columnspan=3, sticky="w"); r += 1

        self.btn = ttk.Button(f, text="Struktur anlegen", command=self.anlegen)
        self.btn.grid(row=r, column=2, pady=(10, 0), sticky="e")
        self.abbruch_btn = ttk.Button(f, text="Abbrechen", command=self.kopieren_abbrechen,
                                      state="disabled")
        self.abbruch_btn.grid(row=r, column=1, pady=(10, 0), sticky="e")
        self.protocol("WM_DELETE_WINDOW", self.schliessen)

        self.region_box.bind("<<ComboboxSelected>>", lambda e: self.region_gewechselt())
        self.bst_box.bind("<<ComboboxSelected>>", lambda e: self.klarname.set(""))
        self.basis.trace_add("write", lambda *_: self.basis_geaendert())
        self.region.trace_add("write", lambda *_: self.basis_geaendert())
        for v in (self.bst, self.klarname):
            v.trace_add("write", lambda *_: self.vorschau_planen())
        for v in (self.psp, self.az, self.beschr):
            v.trace_add("write", lambda *_: self.projekt_vorschau())
        # automatische Suche der Quellordner
        self.psp.trace_add("write", lambda *_: self.suche_planen("PT1"))
        self.bst.trace_add("write", lambda *_: self.suche_planen("PT2"))
        self.region.trace_add("write", lambda *_: self.suche_planen("PT2"))
        self.quellen["PT1"].trace_add("write", lambda *_: self.beschreibung_aktualisieren())

        self.liste_aktualisieren()
        self.after(150, self.such_abfragen)
        self.after(100, self.bst_abfragen)
        self.suche_planen("PT2")
        self.update_idletasks()
        breite = min(f.winfo_reqwidth() + 24, self.winfo_screenwidth() - 80)
        hoehe = min(f.winfo_reqheight() + 4, self.winfo_screenheight() - 100)
        self.geometry(f"{breite}x{hoehe}")

    # ------------------------------------------------ Automatische Vorauswahl PT1/PT2
    def such_auftrag(self, kennung):
        """-> (Funktion, Beschreibung) oder (None, None), wenn Angaben fehlen."""
        if kennung == "PT1":
            psp = self.psp.get().strip().upper()
            if not PSP_MUSTER.match(psp):
                return None, None
            return ((lambda: pt1_ordner_finden(psp)),
                    f"Suche {psp} in {anzeige_pfad(pt1_gruppenordner(psp))} …")
        if kennung == "PT2":
            ril = self.ril_wert()
            region = self.region.get()
            if not ril:
                return None, None
            return ((lambda: pt2_ordner_finden(region, ril)),
                    f"Suche {pt2_kern(ril)}* in "
                    f"{KOPIERBEREICHE['PT2'][2]} / {REGIONEN.get(region, region)} …")
        return None, None

    def suche_planen(self, kennung):
        """Beim Tippen 0,5 s warten, dann suchen (UNC-Zugriffe können langsam sein)."""
        if self.such_job[kennung]:
            self.after_cancel(self.such_job[kennung])
        self.such_nr[kennung] += 1
        self.such_job[kennung] = self.after(VERZOEGERUNG_SUCHE, lambda: self.suchen(kennung))

    def suchen(self, kennung):
        self.such_job[kennung] = None
        self.such_nr[kennung] += 1
        nr = self.such_nr[kennung]
        funktion, text = self.such_auftrag(kennung)
        if funktion is None:
            self.hinweise[kennung].config(text=HINWEIS_LEER[kennung], foreground="gray")
            self.auto_quelle_leeren(kennung)
            return
        self.hinweise[kennung].config(text=text, foreground="gray")

        def arbeit():
            try:
                treffer, fehler = funktion()
            except Exception as e:
                treffer, fehler = [], anzeige_pfad(str(e))
            self.such_q.put((kennung, nr, treffer, fehler))

        threading.Thread(target=arbeit, daemon=True).start()

    def auto_quelle_leeren(self, kennung):
        """Automatisch gesetzten Wert entfernen, manuelle Auswahl behalten."""
        aktuell = self.quellen[kennung].get().strip()
        if aktuell and gleicher_pfad(aktuell, self.auto_wert[kennung]):
            self.quellen[kennung].set("")
        self.auto_wert[kennung] = ""

    def such_abfragen(self):
        try:
            while True:
                kennung, nr, treffer, fehler = self.such_q.get_nowait()
                if nr != self.such_nr[kennung]:      # veraltetes Ergebnis
                    continue
                self.such_ergebnis(kennung, treffer, fehler)
        except queue.Empty:
            pass
        self.after(150, self.such_abfragen)

    def such_ergebnis(self, kennung, treffer, fehler):
        hinweis = self.hinweise[kennung]
        aktuell = self.quellen[kennung].get().strip()
        automatisch = not aktuell or gleicher_pfad(aktuell, self.auto_wert[kennung])

        if fehler or not treffer:
            hinweis.config(text="⚠ " + (fehler or "Nichts gefunden."), foreground="darkorange")
            if automatisch:
                self.auto_quelle_leeren(kennung)
            return

        gefunden = anzeige_pfad(treffer[0])
        anzeige = kurzpfad(kennung, treffer[0])
        zusatz = ""
        if len(treffer) > 1:
            andere = ", ".join(kurzpfad(kennung, d) for d in treffer[1:4]) + (" …" if len(treffer) > 4 else "")
            zusatz = f"\nWeitere Treffer: {andere} – ggf. über „Durchsuchen…“ ändern."
        if automatisch:
            if not gleicher_pfad(aktuell, gefunden):
                self.quellen[kennung].set(gefunden)
            self.auto_wert[kennung] = gefunden
            hinweis.config(text=f"✔ Vorausgewählt: {anzeige}{zusatz}", foreground="darkgreen")
        else:
            hinweis.config(text=f"Gefunden: {anzeige} – manuelle Auswahl bleibt erhalten.{zusatz}",
                           foreground="#1f5fbf")

    # ------------------------------------------------ Betriebsstellen-Liste
    def region_pfad(self):
        return self.bst_region

    @staticmethod
    def anzeige(name: str) -> str:
        return anzeige_name(name)

    def liste_einlesen(self):
        return list(self.bst_map)

    def liste_aktualisieren(self):
        self.basis_geaendert()

    def basis_geaendert(self):
        """Basis/Region separat entprellen; offene Listenanforderung beibehalten."""
        self.liste_ausstehend = True
        self.bst_nr += 1
        self.bst_ergebnis = (None, False, None)
        self.bst_fehler = None
        if self.basis_job:
            self.after_cancel(self.basis_job)
        if self.vorschau_job:
            self.after_cancel(self.vorschau_job)
            self.vorschau_job = None
        self.basis_job = self.after(VERZOEGERUNG_BASIS, lambda: self.bst_pruefen(True))
        self.bst_anzeigen()

    def vorschau_planen(self):
        """Betriebsstellenprüfung entprellen; Projektfelder benötigen keinen Zugriff."""
        self.bst_nr += 1
        self.bst_ergebnis = (None, False, None)
        self.bst_fehler = None
        if self.vorschau_job:
            self.after_cancel(self.vorschau_job)
            self.vorschau_job = None
        if self.basis_job is None:
            self.vorschau_job = self.after(
                VERZOEGERUNG_VORSCHAU, lambda: self.bst_pruefen(False))
        self.bst_anzeigen()

    def bst_planen(self, liste=False):
        if liste:
            self.basis_geaendert()
        else:
            self.vorschau_planen()

    def bst_starten(self):
        self.bst_pruefen(self.liste_ausstehend)

    def bst_pruefen(self, liste: bool):
        """Alle Tk-Werte vor dem Start des Hintergrundauftrags aufnehmen."""
        for name in ("basis_job", "vorschau_job"):
            auftrag = getattr(self, name)
            if auftrag:
                self.after_cancel(auftrag)
                setattr(self, name, None)
        self.bst_nr += 1
        nr = self.bst_nr
        basis, region = Path(self.basis.get()), self.region.get()
        auswahl, ril, klar = self.bst.get().strip(), self.ril_wert(), self.klarname.get().strip()
        karte = dict(self.bst_map)
        liste = liste or self.liste_ausstehend
        self.liste_ausstehend = liste

        def arbeit():
            try:
                regionpfad = region_ordner(basis, region)
                if liste:
                    karte_neu = {anzeige_name(n): n
                                 for n in betriebsstellen_auflisten(regionpfad)}
                else:
                    karte_neu = karte
                ergebnis = betriebsstelle_pruefen(regionpfad, auswahl, ril, klar, karte_neu)
                fehler = None
            except Exception as e:
                regionpfad = basis / REGIONEN.get(region, region)
                karte_neu, ergebnis, fehler = karte, (None, False, None), anzeige_pfad(str(e))
            self.bst_q.put((nr, regionpfad, karte_neu, liste, ergebnis, fehler))

        threading.Thread(target=arbeit, daemon=True).start()

    def bst_abfragen(self):
        try:
            while True:
                nr, region, karte, liste, ergebnis, fehler = self.bst_q.get_nowait()
                if nr != self.bst_nr:
                    continue
                self.bst_region = region
                if liste:
                    self.bst_map = karte
                    self.liste_ausstehend = False
                    self.liste_filtern()
                    self.suche_planen("PT2")
                self.bst_ergebnis, self.bst_fehler = ergebnis, fehler
                self.bst_anzeigen()
        except queue.Empty:
            pass
        self.after(100, self.bst_abfragen)

    def liste_filtern(self):
        """Nur die zwischengespeicherte Liste filtern, ohne Netzwerkzugriff."""
        alle = self.liste_einlesen()
        text = self.bst.get().strip().casefold()
        if text and text not in (n.casefold() for n in alle):
            gefiltert = [n for n in alle if text in n.casefold()]
        else:
            gefiltert = alle
        self.bst_box.config(values=gefiltert or alle)

    def region_gewechselt(self):
        self.bst.set("")
        self.klarname.set("")
        self.liste_aktualisieren()

    # ------------------------------------------------ Hilfen
    def ril_wert(self):
        return ril_aus_eingabe(self.bst.get(), self.bst_map)

    def projektordnername(self):
        """Hauptordner: <Anlagenzustand>_<PSP>_<Projektbeschreibung>"""
        teile = [self.az.get().strip(), self.psp.get().strip().upper(), self.beschr.get().strip()]
        return bereinigen("_".join(t for t in teile if t))

    def betriebsstelle_ermitteln(self):
        """Frisch prüfen, ausschließlich unmittelbar vor dem Anlegen."""
        region = region_ordner(Path(self.basis.get()), self.region.get())
        return betriebsstelle_pruefen(region, self.bst.get().strip(), self.ril_wert(),
                                     self.klarname.get().strip(), dict(self.bst_map))

    def beschreibung_aktualisieren(self):
        quelle = self.quellen["PT1"].get().strip()
        vorschlag = beschreibung_aus_pt1(quelle) if quelle else ""
        aktuell = self.beschr.get()
        automatisch = not aktuell or aktuell == self.auto_beschr
        if automatisch:
            self.auto_beschr = vorschlag
            self.beschr.set(vorschlag)
        self.beschreibung_anzeigen()

    def beschreibung_anzeigen(self):
        quelle = self.quellen["PT1"].get().strip()
        vorschlag = beschreibung_aus_pt1(quelle) if quelle else ""
        aktuell = self.beschr.get()
        automatisch = bool(self.auto_beschr) and aktuell == self.auto_beschr
        text = (f"{vorschlag} (aus PT1 übernommen)" if automatisch
                else f"Vorschlag aus PT1: {vorschlag}") if vorschlag else ""
        self.beschr_hinweis.config(
            text=text, foreground="#1f5fbf" if aktuell and not automatisch else "gray")

    def projekt_vorschau(self):
        """Projektpfad und bereinigte Länge ausschließlich aus zwischengespeicherten Werten."""
        self.beschreibung_anzeigen()
        bst, existiert, neu = self.bst_ergebnis
        basis = Path(self.basis.get()) / REGIONEN.get(self.region.get(), self.region.get())
        projekt = ((neu or bst) if bst else basis) / self.projektordnername()
        laenge = len(anzeige_pfad(projekt))
        beschreibung = self.beschr.get().strip()
        beschr_laenge = len(bereinigen(beschreibung)) if beschreibung else 0
        self.laengen_hinweis.config(
            text=f"Beschreibung: {beschr_laenge}/{BESCHR_MAX} Zeichen; "
                 f"Projektpfad: {laenge}/{PROJEKTPFAD_MAX} Zeichen (Empfehlung).",
            foreground="darkorange" if beschr_laenge > BESCHR_MAX or laenge > PROJEKTPFAD_MAX
            else "gray")
        self.vorschau.config(text=f"Projektordner: {anzeige_pfad(projekt)}" if bst else "")

    def vorschau_aktualisieren(self):
        self.bst_anzeigen()

    def bst_anzeigen(self):
        self.projekt_vorschau()
        bst, existiert, neu = self.bst_ergebnis
        if bst is None:
            if self.ril_wert():
                txt = "Betriebsstelle nicht vorhanden – bitte Klarname für Neuanlage eingeben."
            else:
                txt = (f"{len(self.bst_map)} Betriebsstelle(n) in "
                       f"{anzeige_pfad(self.region_pfad())} gefunden – "
                       "bitte auswählen oder RIL100-Kürzel eingeben.")
            self.bst_status.config(text=self.bst_fehler or txt, foreground="darkorange")
            self.klar_entry.config(state="normal")
            return

        if existiert and neu:
            self.bst_status.config(
                text=f"✏ Wird vervollständigt: {bst.name}  →  {neu.name}", foreground="#1f5fbf")
            self.klar_entry.config(state="normal")
        elif existiert and not hat_klarname(bst.name):
            self.bst_status.config(
                text=f"✔ Vorhanden ohne Klarname: {anzeige_pfad(bst)}  – Klarname eingeben, um den Ordnernamen "
                     "zu vervollständigen (optional).", foreground="darkgreen")
            self.klar_entry.config(state="normal")
        elif existiert:
            self.bst_status.config(text=f"✔ Vorhanden: {anzeige_pfad(bst)}", foreground="darkgreen")
            self.klar_entry.config(state="disabled")
        else:
            self.bst_status.config(text=f"➕ Wird neu angelegt: {anzeige_pfad(bst)}", foreground="darkorange")
            self.klar_entry.config(state="normal")

    def basis_waehlen(self):
        d = filedialog.askdirectory(initialdir=self.basis.get() or None)
        if d:
            self.basis.set(str(Path(d)))

    def quelle_waehlen(self, kennung):
        # Startordner: aktueller Wert > passender Unterordner > Laufwerk
        kandidaten = [self.quellen[kennung].get().strip()]
        if kennung == "PT1":
            psp = self.psp.get().strip().upper()
            if PSP_MUSTER.match(psp):
                kandidaten.append(str(pt1_gruppenordner(psp)))
        elif kennung == "PT2":
            kandidaten.append(str(pt2_regionsordner(self.region.get())))
        kandidaten.append(KOPIERBEREICHE[kennung][2])
        start = next((k for k in kandidaten if k and langer_pfad(k).is_dir()), None)
        if start is None:
            messagebox.showwarning(
                "Laufwerk nicht erreichbar",
                f"{kennung}-Laufwerk ist nicht erreichbar:\n{KOPIERBEREICHE[kennung][2]}\n\n"
                "VPN/Netzwerkverbindung und Berechtigung prüfen. "
                "Der Auswahldialog öffnet sich trotzdem.")
        d = filedialog.askdirectory(initialdir=start, title=f"{kennung}-Ordner wählen")
        if d:
            self.quellen[kennung].set(str(Path(d)))
            self.auto_wert[kennung] = ""   # manuelle Auswahl nicht mehr automatisch überschreiben
            self.hinweise[kennung].config(text="Manuell ausgewählt.", foreground="gray")

    # ------------------------------------------------ Anlegen
    def auswahl_offen(self):
        return [k for k, a in self.auswahlen.items()
                if a.ausstehend or (self.quellen[k].get().strip()
                                   and (a.fehler or not a.auswahl()))]

    def knopf_aktualisieren(self):
        if hasattr(self, "btn"):
            offen = self.auswahl_offen()
            if offen:
                meldung = (f"Bitte in {', '.join(offen)} mindestens einen Ordner anhaken "
                           "(oder Quellordner leeren).")
            else:
                meldung = ""
            self.btn.config(state="disabled" if self.kopier_thread is not None or meldung else "normal")
            if self.kopier_thread is None:
                if meldung:
                    self.status.config(text=meldung)
                elif self.auswahl_meldung and self.status.cget("text") == self.auswahl_meldung:
                    self.status.config(text="Bereit.")
                self.auswahl_meldung = meldung

    def kopieren_abbrechen(self, rueckfrage=True):
        if self.kopier_thread is not None:
            if rueckfrage and not messagebox.askyesno(
                    "Kopieren abbrechen?",
                    "Kopieren nach der laufenden Datei abbrechen?\n"
                    "Bereits kopierte Dateien bleiben erhalten."):
                return
            if self.kopier_thread is None:
                return
            self.abbruch.set()
            self.abbruch_btn.config(state="disabled")
            self.status.config(text="Abbruch angefordert – laufende Datei wird noch abgeschlossen …")

    def destroy(self):
        # Auch die von Unterwidgets registrierten Abfragen vor dem Schließen stoppen.
        for auftrag in self.tk.call("after", "info"):
            self.tk.call("after", "cancel", auftrag)
        super().destroy()

    def schliessen(self):
        if self.kopier_thread is None:
            self.destroy()
        elif self.schliessen_ausstehend:
            if messagebox.askyesno(
                    "Sofort schließen?",
                    "Die laufende Datei ist möglicherweise noch nicht fertig. "
                    "Sofort beenden? Eine .part-Datei kann zurückbleiben."):
                self.destroy()
        elif messagebox.askyesno("Kopie abbrechen?",
                                 "Kopieren nach der laufenden Datei abbrechen und Fenster schließen?"):
            if self.kopier_thread is None:
                self.destroy()
                return
            self.schliessen_ausstehend = True
            self.kopieren_abbrechen(rueckfrage=False)

    def anlegen(self):
        if self.kopier_thread is not None:
            return
        offen = self.auswahl_offen()
        if offen:
            self.knopf_aktualisieren()
            meldung = self.status.cget("text")
            if any(self.auswahlen[k].ausstehend for k in offen):
                titel = "Auswahl wird geladen"
            elif any(self.auswahlen[k].fehler for k in offen):
                titel = "Quelle nicht lesbar"
                meldung = "\n".join(self.auswahlen[k].fehler for k in offen
                                    if self.auswahlen[k].fehler)
            else:
                titel = "Auswahl fehlt"
            messagebox.showwarning(titel, meldung)
            return
        psp, az, beschr = self.psp.get().strip().upper(), self.az.get().strip(), self.beschr.get().strip()
        ril = self.ril_wert()
        if not (ril and psp and az and beschr):
            messagebox.showerror("Fehlende Angaben",
                                 "Bitte Betriebsstelle/RIL100-Kürzel, Anlagenzustand, PSP-Element und "
                                 "Projektbeschreibung ausfüllen.")
            return
        projektname, regionanzeige = self.projektordnername(), self.region.get()
        try:
            bst, existiert, neu = self.betriebsstelle_ermitteln()
        except OSError as e:
            messagebox.showerror("Betriebsstelle nicht lesbar", anzeige_pfad(str(e)))
            return
        if bst is None:
            messagebox.showerror("Fehlende Angaben",
                                 f"Für '{ril}' gibt es noch keinen Ordner.\n"
                                 "Bitte Klarname der Betriebsstelle eingeben.")
            return
        if neu is not None and neu.exists():
            messagebox.showerror("Umbenennen nicht möglich",
                                 f"Der Ordner existiert bereits:\n{anzeige_pfad(neu)}\n\n"
                                 f"Bitte diesen Ordner in der Liste auswählen oder '{bst.name}' "
                                 "manuell zusammenführen.")
            return

        quellen, auswahlplan = {}, {}
        for kennung in KOPIERBEREICHE:
            q = self.quellen[kennung].get().strip()
            if q:
                p = langer_pfad(q)
                if not p.is_dir():
                    messagebox.showerror("Fehler", f"{kennung}-Quelle nicht gefunden:\n{anzeige_pfad(p)}")
                    return
                auswahl = self.auswahlen[kennung]
                if auswahl.fehler:
                    messagebox.showwarning("Quelle nicht lesbar", auswahl.fehler)
                    return
                if not auswahl.auswahl():
                    messagebox.showwarning("Auswahl fehlt",
                                           f"Bitte für {kennung} mindestens einen Ordner oder "
                                           "„Dateien in diesem Ordner“ auswählen.")
                    return
                quellen[kennung] = p
                auswahlplan[kennung] = tuple(auswahl.auswahl())

        warn = []
        if not existiert and not RIL_MUSTER.match(ril):
            warn.append(f"RIL100-Kürzel '{ril}' sieht ungewöhnlich aus (2–5 Zeichen erwartet).")
        if not AZ_MUSTER.match(az):
            warn.append(f"Anlagenzustand '{az}' ist nicht 4-stellig numerisch.")
        if not PSP_MUSTER.match(psp.upper()):
            warn.append(f"PSP-Element '{psp}' entspricht nicht dem Format M17525-01 bzw. M19061-01A.")
        if not existiert:
            warn.append(f"Betriebsstellenordner wird neu angelegt:\n{anzeige_pfad(bst)}")
        if neu is not None:
            warn.append(f"Betriebsstellenordner wird umbenannt:\n{bst.name}  →  {neu.name}")
        projekt = (neu or bst) / projektname
        beschr_laenge = len(bereinigen(beschr))
        if beschr_laenge > BESCHR_MAX:
            warn.append(f"Beschreibung länger als {BESCHR_MAX} Zeichen ({beschr_laenge}, bereinigt).")
        if len(anzeige_pfad(projekt)) > PROJEKTPFAD_MAX:
            warn.append(f"Projektpfad länger als {PROJEKTPFAD_MAX} Zeichen "
                        f"({len(anzeige_pfad(projekt))}).")
        for k, p in quellen.items():
            auswahltext = [
                f"• {rel} → {ziel}" + (" [nur Dateien]" if nur else "")
                for _, nur, ziel, rel in auswahlplan[k]]
            warn.append(f"{k} wird kopiert von:\n{anzeige_pfad(p)}\n" + "\n".join(auswahltext))
        wurzel = projekt
        strukturpfade = tuple(vorlage_parsen(VORLAGE))
        auftraege = tuple(
            (f"{k}/{ziel}/{rel}" + (" (Dateien)" if nur else ""), p,
             wurzel / KOPIERBEREICHE[k][0] / ziel / zielname(q) / rel, nur)
            for k, q in quellen.items() for p, nur, ziel, rel in auswahlplan[k])
        quelltext = (
            f"PT1-Quelle:          {anzeige_pfad(quellen.get('PT1', '-'))}\n"
            f"PT2-Quelle:          {anzeige_pfad(quellen.get('PT2', '-'))}\n")
        auswahltext = "\n".join(
            f"- {k}/{ziel}/{rel}" + (" (Dateien)" if nur else "")
            + f" ← {anzeige_pfad(p)}"
            for k, auswahl in auswahlplan.items() for p, nur, ziel, rel in auswahl
        ) or "- Keine Quellen ausgewählt (nur Struktur)."
        auswahltext = "Ordnerauswahl:\n" + auswahltext + "\n"
        info_neu = (
            f"Region:              {regionanzeige}\n"
            f"Betriebsstelle:      {(neu or bst).name}\n"
            f"Anlagenzustand:      {az}\n"
            f"PSP-Element:         {psp}\n"
            f"Projektbeschreibung: {beschr}\n"
            f"Angelegt am:         {date.today():%d.%m.%Y}\n"
            + quelltext + auswahltext)
        info_fortsetzen = (f"\nKopierauftrag am {datetime.now():%d.%m.%Y %H:%M:%S}:\n"
                           + quelltext + auswahltext)
        if warn and not messagebox.askyesno("Hinweis", "\n\n".join(warn) + "\n\nFortfahren?"):
            return

        if neu is not None:
            try:
                bst.rename(neu)
            except OSError as e:
                messagebox.showerror(
                    "Umbenennen fehlgeschlagen",
                    f"'{bst.name}' konnte nicht in '{neu.name}' umbenannt werden:\n"
                    f"{anzeige_pfad(str(e))}\n\n"
                    "Ist eine Datei oder ein Explorer-Fenster in diesem Ordner geöffnet?")
                return
            bst = neu
            self.klarname.set("")

        try:
            for p in strukturpfade:
                (wurzel / p).mkdir(parents=True, exist_ok=True)
            info = wurzel / "Projektinfo.txt"
            if not info.exists():
                info.write_text(info_neu, encoding="utf-8")
            else:
                # Bestehende Projektangaben erhalten, den aktuellen Kopierplan nur anhängen.
                with info.open("a", encoding="utf-8") as protokoll:
                    protokoll.write(info_fortsetzen)
        except OSError as e:
            messagebox.showerror(
                "Fehler", f"Struktur konnte nicht angelegt werden:\n{anzeige_pfad(str(e))}")
            return

        self.wurzel = wurzel
        self.liste_aktualisieren()
        self.bst.set(self.anzeige(bst.name))

        if not quellen:
            self.status.config(text=f"Struktur angelegt: {anzeige_pfad(wurzel)}")
            messagebox.showinfo("Fertig", f"Struktur angelegt:\n{anzeige_pfad(wurzel)}")
            return

        self.abbruch.clear()
        self.schliessen_ausstehend = False
        self.status.config(text="Ermittle Dateien …")
        self.kopier_thread = threading.Thread(target=ordner_kopieren,
                                              args=(auftraege, self.q, self.abbruch), daemon=True)
        self.knopf_aktualisieren()
        self.abbruch_btn.config(state="normal")
        self.kopier_thread.start()
        self.after(100, self.abfragen)

    def kopier_fertig(self, ergebnisse):
        self.kopier_thread = None
        self.abbruch_btn.config(state="disabled")
        zeilen, alle_fehler = [], []
        abgebrochen = False
        for kennung, kop, ueb, fehler, abbruch in ergebnisse:
            zeile = (f"{kennung}: {kop} Dateien kopiert, {ueb} bereits vorhanden "
                     "(nicht überschrieben).")
            if abbruch:
                zeile += f" ABBRUCH – {abbruch}"
                abgebrochen = True
            zeilen.append(zeile)
            alle_fehler.extend(f"[{kennung}] {anzeige_pfad(x)}" for x in fehler)
        txt = "\n".join(zeilen)
        self.status.config(text=" | ".join(zeilen))
        if abgebrochen:
            txt += ("\n\nZum Fortsetzen mit denselben Quellen und Auswahlen erneut "
                    "„Struktur anlegen“ wählen. "
                    "Vollständig kopierte Dateien werden nicht überschrieben; "
                    ".part-Dateien werden beim nächsten Kopieren ersetzt.")
        if alle_fehler or abgebrochen:
            protokoll = txt + "\n\n" + "\n".join(alle_fehler)
            try:
                (langer_pfad(self.wurzel) / "Kopierfehler.txt").write_text(
                    protokoll, encoding="utf-8")
                txt += f"\n\n{len(alle_fehler)} Fehler – siehe Kopierfehler.txt"
            except OSError as e:
                txt += (f"\n\nKopierfehler.txt konnte nicht geschrieben werden: "
                        f"{anzeige_pfad(str(e))}\n"
                        + "\n".join(alle_fehler[:10]))
        self.knopf_aktualisieren()
        if self.schliessen_ausstehend:
            self.destroy()
            return
        meldung = messagebox.showwarning if alle_fehler or abgebrochen else messagebox.showinfo
        meldung("Abgebrochen" if abgebrochen else ("Kopierfehler" if alle_fehler else "Fertig"),
                f"Struktur angelegt:\n{anzeige_pfad(self.wurzel)}\n\n{txt}")

    def abfragen(self):
        try:
            while True:
                m = self.q.get_nowait()
                if m[0] == "start":
                    if not self.abbruch.is_set():
                        self.status.config(text=f"{m[1]}: Ermittle Dateien …")
                elif m[0] == "max":
                    self.balken.config(maximum=max(m[1], 1), value=0)
                elif m[0] == "fortschritt":
                    _, i, kennung, name = m
                    self.balken.config(value=i)
                    if not self.abbruch.is_set():
                        self.status.config(
                            text=f"{kennung}: Kopiere {i}/{int(self.balken['maximum'])}: {name}")
                elif m[0] == "fertig":
                    self.kopier_fertig(m[1])
                    return
        except queue.Empty:
            pass
        self.after(100, self.abfragen)


if __name__ == "__main__":
    App().mainloop()
