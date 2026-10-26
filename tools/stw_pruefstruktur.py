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
- Automatische Suche schlägt Quellordner vor, wählt sie aber nicht als Kopierquelle:
    PT1: nach Eingabe des PSP-Elements, z. B.
         M17527-01 -> \\\\Thsdiza06fs01\\psp\\M17xxx\\M17527-01 Zweigleisigkeit Lübbenau-Cottbus
    PT2: nach Wahl von Region und RIL100-Kürzel, z. B.
         OST + BLN -> \\\\destgsfs10\\IL90-Projekte-ro\\OST\\BLN0
- Erst nach ausdrücklicher Auswahl/Freigabe und Opt-in werden Ordner kopiert nach
  01_Eingangsunterlagen/PT1/<Stellwerk|ZX|sonstiges> und
  01_Eingangsunterlagen/PT2/<Stellwerk|ZX>

Voraussetzung: Python 3.8+ (tkinter ist in der Windows-Installation enthalten)
Start: Doppelklick oder  python stw_pruefstruktur.py
"""
import queue
import re
import shutil
import threading
import tkinter as tk
from datetime import date
from pathlib import Path
from tkinter import ttk, filedialog, messagebox
from stw_pruefstruktur_logik import (
    CopySelection, PSP_MUSTER, kopierauftrag_pruefen as _kopierauftrag_pruefen,
    normalisiere_psp, pfade_ueberlappen,
    pt1_gruppenordner as _pt1_gruppenordner,
    pt1_ordner_finden as _pt1_ordner_finden,
    quelle_ist_gesamtordner as _quelle_ist_gesamtordner,
    suchergebnis_ist_aktuell,
)

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
# PT2: bevorzugter Ordner = RIL100-Kürzel + "0"  (BLN -> BLN0)
PT2_STANDARD_SUFFIX = "0"

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

AZ_MUSTER = re.compile(r"^\d{4}$")                       # z. B. 0180
RIL_MUSTER = re.compile(r"^[A-ZÄÖÜ][A-ZÄÖÜ0-9 ]{1,4}$")  # z. B. BLN, BL, BLN F
# Ordner "<RIL> - <Name>"
BST_MIT_KLARNAME = re.compile(r"^\s*[A-Za-zÄÖÜäöü0-9 ]{1,6}?\s*-\s*\S")
# Ordner nur "<RIL>" (1–5 Zeichen, beginnt mit Buchstabe)
BST_NUR_RIL = re.compile(r"^[A-Za-zÄÖÜäöü][A-Za-zÄÖÜäöü0-9 ]{0,4}$")
UNGUELTIG = re.compile(r'[<>:"/\\|?*]')

HINWEIS_LEER = {
    "PT1": "Wird nach Eingabe des PSP-Elements automatisch gesucht.",
    "PT2": "Wird nach Wahl von Region und Betriebsstelle automatisch gesucht.",
}


# ---------------------------------------------------------------- Logik
def bereinigen(name: str) -> str:
    """Für Projekt- und Strukturordner: ungültige Zeichen und Leerzeichen -> _"""
    return UNGUELTIG.sub("_", name.strip()).replace(" ", "_")


def bereinigen_mit_leerzeichen(name: str) -> str:
    """Für Region/Betriebsstelle: Leerzeichen bleiben erhalten."""
    return UNGUELTIG.sub("_", name.strip())


def hat_klarname(ordnername: str) -> bool:
    return bool(BST_MIT_KLARNAME.match(ordnername))


def ist_betriebsstelle(ordnername: str) -> bool:
    return hat_klarname(ordnername) or bool(BST_NUR_RIL.match(ordnername.strip()))


def ril_aus_ordner(ordnername: str) -> str:
    teil = ordnername.split("-", 1)[0] if hat_klarname(ordnername) else ordnername
    return " ".join(teil.upper().split())


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
    try:
        if not region.is_dir():
            return []
        return sorted((d.name for d in region.iterdir()
                       if d.is_dir() and ist_betriebsstelle(d.name)), key=str.casefold)
    except OSError:
        return []


def betriebsstelle_suchen(region: Path, ril: str):
    """Vorhandenen Ordner zum RIL100-Kürzel suchen (mit Klarname bevorzugt) oder None."""
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
    return _pt1_gruppenordner(
        psp, KOPIERBEREICHE["PT1"][2], PT1_GRUPPE_STELLEN, PT1_GRUPPE_SUFFIX)


def pt1_ordner_finden(psp: str):
    return _pt1_ordner_finden(
        psp, KOPIERBEREICHE["PT1"][2], PT1_GRUPPE_STELLEN, PT1_GRUPPE_SUFFIX)


def quelle_ist_gesamtordner(kennung, quelle, vorschlag=None, kontext=()):
    return _quelle_ist_gesamtordner(
        kennung, quelle, KOPIERBEREICHE[kennung][2], vorschlag, kontext)


def kopierauftrag_pruefen(kennung, auswahl, kontext, ziel, vorschlag=None):
    return _kopierauftrag_pruefen(
        kennung, auswahl, kontext, ziel, KOPIERBEREICHE[kennung][2], vorschlag)


def pt2_regionsordner(region_anzeige: str) -> Path:
    """Ost -> \\\\destgsfs10\\IL90-Projekte-ro\\OST"""
    return region_ordner(Path(KOPIERBEREICHE["PT2"][2]), region_anzeige)


def pt2_ordner_finden(region_anzeige: str, ril: str):
    """
    Sucht auf dem PT2-Laufwerk den Ordner zur Betriebsstelle.
    -> (Treffer, Fehlertext oder None). Treffer: Name = RIL100-Kürzel, optional
       gefolgt von Ziffern und/oder einem Zusatz (BLN0, BLN1, BLN0_alt …).
       RIL100 + "0" (z. B. BLN0) steht an erster Stelle.
    """
    region = pt2_regionsordner(region_anzeige)
    kern = ril.replace(" ", "")
    muster = re.compile(r"^" + re.escape(kern) + r"\d*(?:[\s_\-].*)?$", re.IGNORECASE)
    bevorzugt = (kern + PT2_STANDARD_SUFFIX).casefold()
    try:
        if not region.is_dir():
            return [], f"Ordner nicht gefunden: {region}"
        treffer = [d for d in region.iterdir() if d.is_dir() and muster.match(d.name)]
    except OSError as e:
        return [], f"PT2-Laufwerk nicht lesbar: {e}"
    if not treffer:
        return [], f"Kein Ordner für {ril} in {region} gefunden."
    treffer.sort(key=lambda d: (d.name.casefold() != bevorzugt, d.name.casefold()))
    return treffer, None


def ordner_kopieren(auftraege, q: queue.Queue):
    """
    Kopiert nacheinander alle Aufträge [(kennung, quelle, ziel), ...] rekursiv.
    Vorhandene Dateien werden NICHT überschrieben.
    """
    ergebnisse = []
    for kennung, quelle, ziel in auftraege:
        try:
            if pfade_ueberlappen(quelle, ziel):
                raise ValueError(f"Quelle und Ziel überschneiden sich: {quelle} → {ziel}")
            q.put(("start", kennung))
            dateien = [p for p in quelle.rglob("*") if p.is_file()]
            q.put(("max", len(dateien)))
            kopiert = uebersprungen = 0
            fehler = []
            ziel.mkdir(parents=True, exist_ok=True)
            for d in quelle.rglob("*"):
                if d.is_dir():
                    (ziel / d.relative_to(quelle)).mkdir(parents=True, exist_ok=True)
            for i, src in enumerate(dateien, 1):
                dst = ziel / src.relative_to(quelle)
                try:
                    if dst.exists():
                        uebersprungen += 1
                    else:
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src, dst)
                        kopiert += 1
                except OSError as e:
                    fehler.append(f"{src}: {e}")
                q.put(("fortschritt", i, kennung, src.name))
            ergebnisse.append((kennung, kopiert, uebersprungen, fehler, None))
        except Exception as e:  # z. B. Laufwerk nicht erreichbar
            ergebnisse.append((kennung, 0, 0, [], str(e)))
    q.put(("fertig", ergebnisse))


# ---------------------------------------------------------------- Oberfläche
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Prüfstruktur Stellwerksprojekt")
        self.geometry("800x720")
        self.minsize(700, 500)
        self.resizable(True, True)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.q = queue.Queue()
        self.such_q = queue.Queue()                       # Ergebnisse der Quellordner-Suche
        self.wurzel = None
        self.bst_map = {}                                 # Anzeigetext -> echter Ordnername
        self.such_job = {k: None for k in KOPIERBEREICHE}  # Verzögerung beim Tippen
        self.such_nr = {k: 0 for k in KOPIERBEREICHE}      # nur letzte Suche zählt
        self.hinweise = {}
        self.auswahlen = {k: CopySelection() for k in KOPIERBEREICHE}
        self.kopieren_vars = {k: tk.BooleanVar(value=False) for k in KOPIERBEREICHE}
        self.gesamt_vars = {k: tk.BooleanVar(value=False) for k in KOPIERBEREICHE}
        self.vorschlaege = {k: "" for k in KOPIERBEREICHE}

        self.basis = tk.StringVar(value=STANDARD_BASIS)
        self.region = tk.StringVar(value="Ost")
        self.bst = tk.StringVar()          # Auswahl aus Liste ODER getipptes RIL100-Kürzel
        self.klarname = tk.StringVar()
        self.psp = tk.StringVar()
        self.az = tk.StringVar()
        self.beschr = tk.StringVar()
        self.quellen = {k: tk.StringVar() for k in KOPIERBEREICHE}
        self.unterziele = {k: tk.StringVar(value=v[1][0]) for k, v in KOPIERBEREICHE.items()}

        haupt = ttk.Frame(self)
        haupt.grid(sticky="nsew")
        haupt.rowconfigure(0, weight=1)
        haupt.columnconfigure(0, weight=1)
        leinwand = tk.Canvas(haupt, highlightthickness=0)
        leinwand.grid(row=0, column=0, sticky="nsew")
        bildlauf = ttk.Scrollbar(haupt, orient="vertical", command=leinwand.yview)
        bildlauf.grid(row=0, column=1, sticky="ns")
        leinwand.configure(yscrollcommand=bildlauf.set)
        f = ttk.Frame(leinwand, padding=12)
        fenster = leinwand.create_window((0, 0), window=f, anchor="nw")
        f.bind("<Configure>", lambda _e: leinwand.configure(
            scrollregion=leinwand.bbox("all")))
        leinwand.bind("<Configure>", lambda e: leinwand.itemconfigure(
            fenster, width=e.width))
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
        zeile("PSP-Element (z. B. M17525-01A):", ttk.Entry(f, textvariable=self.psp, width=55))
        zeile("Projektbeschreibung:", ttk.Entry(f, textvariable=self.beschr, width=55))

        # --- PT1 / PT2
        for kennung, (_, unterordner, start) in KOPIERBEREICHE.items():
            ueberschrift(f"{kennung}-Unterlagen  ({start})")
            quell_entry = ttk.Entry(f, textvariable=self.quellen[kennung], width=55)
            zeile(f"{kennung}-Quellordner:", quell_entry,
                  ttk.Button(f, text="Durchsuchen…",
                             command=lambda k=kennung: self.quelle_waehlen(k)))
            controls = ttk.Frame(f)
            controls.grid(row=r, column=1, columnspan=2, sticky="w", padx=5, pady=2)
            ttk.Button(controls, text="Auswahl löschen / nicht kopieren",
                       command=lambda k=kennung: self.quelle_loeschen(k)).pack(side="left")
            ttk.Button(controls, text="Quelle bestätigen",
                       command=lambda k=kennung: self.quelle_bestaetigen(k)).pack(
                           side="left", padx=(5, 0))
            r += 1
            self.kopieren_vars[kennung].trace_add(
                "write", lambda *_args, k=kennung: self.kopieren_gewechselt(k))
            ttk.Checkbutton(f, text="Daten kopieren", variable=self.kopieren_vars[kennung]).grid(
                row=r, column=1, columnspan=2, sticky="w", padx=5); r += 1
            ttk.Checkbutton(
                f, text="Gesamten Ordner einschließlich aller Unterordner kopieren",
                variable=self.gesamt_vars[kennung],
                command=lambda k=kennung: self.gesamt_gewechselt(k)).grid(
                    row=r, column=1, columnspan=2, sticky="w", padx=5); r += 1
            vorschlag_zeile = ttk.Frame(f)
            vorschlag_zeile.grid(row=r, column=1, columnspan=2, sticky="w", padx=5)
            ttk.Button(vorschlag_zeile, text="Vorschlag als Quelle bestätigen",
                       command=lambda k=kennung: self.vorschlag_uebernehmen(k)).pack(side="left")
            self.hinweise[kennung] = ttk.Label(f, foreground="gray", wraplength=520,
                                               justify="left", text=HINWEIS_LEER[kennung])
            self.hinweise[kennung].pack(side="left", padx=5)
            r += 1
            zeile(f"{kennung} kopieren nach:",
                  ttk.Combobox(f, textvariable=self.unterziele[kennung], values=unterordner,
                               state="readonly", width=20))

        self.vorschau = ttk.Label(f, foreground="gray", wraplength=650, justify="left")
        self.vorschau.grid(row=r, column=0, columnspan=3, sticky="w", pady=(8, 0)); r += 1

        self.balken = ttk.Progressbar(f, length=500)
        self.balken.grid(row=r, column=0, columnspan=3, pady=8, sticky="we"); r += 1
        self.status = ttk.Label(f, text="Bereit.")
        self.status.grid(row=r, column=0, columnspan=3, sticky="w"); r += 1

        self.btn = ttk.Button(f, text="Struktur anlegen", command=self.anlegen)
        self.btn.grid(row=r, column=2, pady=(10, 0), sticky="e")

        self.region_box.bind("<<ComboboxSelected>>", lambda e: self.region_gewechselt())
        self.bst_box.bind("<<ComboboxSelected>>", lambda e: self.klarname.set(""))
        self.basis.trace_add("write", lambda *_: self.liste_aktualisieren())
        kontext_vars = (self.basis, self.region, self.bst, self.klarname,
                        self.psp, self.az, self.beschr, *self.unterziele.values())
        for v in kontext_vars:
            v.trace_add("write", lambda *_: self.kontext_gewechselt())
        for v in kontext_vars:
            v.trace_add("write", lambda *_: self.vorschau_aktualisieren())
        for k in KOPIERBEREICHE:
            self.quellen[k].trace_add("write", lambda *_args, kennung=k: self.quelle_gewechselt(kennung))
        # Sucheingaben sofort entwerten, noch vor dem Debounce.
        self.psp.trace_add("write", lambda *_: self.suche_planen("PT1"))
        self.bst.trace_add("write", lambda *_: self.suche_planen("PT2"))
        self.region.trace_add("write", lambda *_: self.suche_planen("PT2"))

        self.liste_aktualisieren()
        self.after(150, self.such_abfragen)
        self.suche_planen("PT2")

    # ------------------------------------------------ Automatische Vorauswahl PT1/PT2
    def kopierkontext(self):
        """Alle Angaben, die Quelle, Ziel oder Kopierfreigabe beeinflussen."""
        return (
            normalisiere_psp(self.psp.get()),
            self.region.get().strip(),
            self.ril_wert(),
            self.basis.get().strip(),
            self.bst.get().strip(),
            self.klarname.get().strip(),
            self.az.get().strip(),
            self.beschr.get().strip(),
            tuple(self.unterziele[k].get() for k in KOPIERBEREICHE),
        )

    def kontext_gewechselt(self):
        kontext = self.kopierkontext()
        for kennung, auswahl in self.auswahlen.items():
            if auswahl.revoke_if_context_changed(kontext):
                self.kopieren_vars[kennung].set(False)
                self.gesamt_vars[kennung].set(False)

    def quelle_gewechselt(self, kennung):
        self.auswahlen[kennung].set_source(self.quellen[kennung].get())
        if not self.auswahlen[kennung].enabled:
            self.kopieren_vars[kennung].set(False)
            self.gesamt_vars[kennung].set(False)

    def kopieren_gewechselt(self, kennung):
        self.auswahlen[kennung].enabled = self.kopieren_vars[kennung].get()

    def gesamt_gewechselt(self, kennung):
        self.auswahlen[kennung].copy_all = self.gesamt_vars[kennung].get()

    def quelle_loeschen(self, kennung):
        self.auswahlen[kennung].clear()
        self.quellen[kennung].set("")
        self.kopieren_vars[kennung].set(False)
        self.gesamt_vars[kennung].set(False)
        self.such_nr[kennung] += 1
        self.vorschlaege[kennung] = ""
        if self.such_job[kennung]:
            self.after_cancel(self.such_job[kennung])
            self.such_job[kennung] = None
        self.hinweise[kennung].config(
            text="Auswahl gelöscht. Es werden keine Daten kopiert.", foreground="gray")

    def quelle_bestaetigen(self, kennung):
        auswahl = self.auswahlen[kennung]
        if not auswahl.source:
            messagebox.showwarning("Keine Quelle", f"Bitte zuerst einen {kennung}-Quellordner wählen.")
            return
        if auswahl.approve(self.kopierkontext()):
            self.hinweise[kennung].config(
                text=f"Quelle ausdrücklich bestätigt:\n{auswahl.source}", foreground="#1f5fbf")

    def vorschlag_uebernehmen(self, kennung):
        vorschlag = self.vorschlaege[kennung]
        if not vorschlag:
            messagebox.showinfo("Kein Vorschlag", "Es liegt derzeit kein Suchtreffer als Vorschlag vor.")
            return
        self.quellen[kennung].set(vorschlag)
        auswahl = self.auswahlen[kennung]
        auswahl.approve(self.kopierkontext())
        self.hinweise[kennung].config(
            text=f"Vorschlag als Quelle bestätigt:\n{vorschlag}\n"
                 "Zum Kopieren zusätzlich „Daten kopieren“ aktivieren.",
            foreground="#1f5fbf")

    def such_auftrag(self, kennung):
        """-> (Funktion, Beschreibung) oder (None, None), wenn Angaben fehlen."""
        if kennung == "PT1":
            psp = normalisiere_psp(self.psp.get())
            if not PSP_MUSTER.match(psp):
                return None, None
            return (lambda: pt1_ordner_finden(psp)), f"Suche {psp} in {pt1_gruppenordner(psp)} …"
        if kennung == "PT2":
            ril = self.ril_wert()
            region = self.region.get()
            if not ril:
                return None, None
            region_pfad = Path(KOPIERBEREICHE["PT2"][2]) / REGIONEN.get(region, region)
            return ((lambda: pt2_ordner_finden(region, ril)),
                    f"Suche {ril} in {region_pfad} …")
        return None, None

    def suche_planen(self, kennung):
        """Beim Tippen 0,5 s warten, dann suchen (UNC-Zugriffe können langsam sein)."""
        self.such_nr[kennung] += 1
        nr = self.such_nr[kennung]
        kontext = self.such_kontext(kennung)
        self.vorschlaege[kennung] = ""
        if self.such_job[kennung]:
            self.after_cancel(self.such_job[kennung])
        self.such_job[kennung] = self.after(
            500, lambda: self.suchen(kennung, nr, kontext))

    def such_kontext(self, kennung):
        if kennung == "PT1":
            return (normalisiere_psp(self.psp.get()),)
        return (self.region.get().strip(), self.ril_wert())

    def suchen(self, kennung, nr, kontext):
        self.such_job[kennung] = None
        funktion, text = self.such_auftrag(kennung)
        if funktion is None:
            self.hinweise[kennung].config(text=HINWEIS_LEER[kennung], foreground="gray")
            return
        self.hinweise[kennung].config(text=text, foreground="gray")

        def arbeit():
            treffer, fehler = funktion()
            self.such_q.put((kennung, nr, kontext, treffer, fehler))

        threading.Thread(target=arbeit, daemon=True).start()

    def such_abfragen(self):
        try:
            while True:
                kennung, nr, kontext, treffer, fehler = self.such_q.get_nowait()
                if not suchergebnis_ist_aktuell(
                        nr, self.such_nr[kennung], kontext, self.such_kontext(kennung)):
                    continue
                self.such_ergebnis(kennung, treffer, fehler)
        except queue.Empty:
            pass
        self.after(150, self.such_abfragen)

    def such_ergebnis(self, kennung, treffer, fehler):
        hinweis = self.hinweise[kennung]
        if fehler or not treffer:
            hinweis.config(text="⚠ " + (fehler or "Nichts gefunden."), foreground="darkorange")
            return

        gefunden = str(treffer[0])
        self.vorschlaege[kennung] = gefunden
        zusatz = ""
        if len(treffer) > 1:
            andere = ", ".join(d.name for d in treffer[1:4]) + (" …" if len(treffer) > 4 else "")
            zusatz = f"\nWeitere Treffer: {andere} – gewünschten Ordner über „Durchsuchen…“ wählen."
        hinweis.config(
            text=f"Vorschlag (wird nicht automatisch kopiert): {treffer[0].name}{zusatz}",
            foreground="darkgreen")

    # ------------------------------------------------ Betriebsstellen-Liste
    def region_pfad(self):
        return region_ordner(Path(self.basis.get()), self.region.get())

    @staticmethod
    def anzeige(name: str) -> str:
        return name if hat_klarname(name) else name + OHNE_KLARNAME

    def liste_einlesen(self):
        namen = betriebsstellen_auflisten(self.region_pfad())
        self.bst_map = {self.anzeige(n): n for n in namen}
        return list(self.bst_map)

    def liste_aktualisieren(self):
        self.bst_box.config(values=self.liste_einlesen())
        self.vorschau_aktualisieren()

    def liste_filtern(self):
        """Beim Aufklappen: Liste neu einlesen und nach Eingabe filtern."""
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
        text = self.bst.get().strip()
        if text in self.bst_map:
            return ril_aus_ordner(self.bst_map[text])
        if "-" in text:
            text = text.split("-", 1)[0]
        return " ".join(text.upper().split())

    def projektordnername(self):
        """Hauptordner: <Anlagenzustand>_<PSP>_<Projektbeschreibung>"""
        teile = [self.az.get().strip(), normalisiere_psp(self.psp.get()), self.beschr.get().strip()]
        return bereinigen("_".join(t for t in teile if t))

    def betriebsstelle_ermitteln(self):
        """-> (Pfad, existiert, neuer_pfad); (None, False, None) wenn Klarname für Neuanlage fehlt."""
        region = self.region_pfad()
        auswahl = self.bst.get().strip()
        ril = self.ril_wert()
        if not ril:
            return None, False, None

        ordner = None
        if auswahl in self.bst_map and (region / self.bst_map[auswahl]).is_dir():
            ordner = region / self.bst_map[auswahl]
        if ordner is None:
            ordner = betriebsstelle_suchen(region, ril)

        klar = self.klarname.get().strip()
        if ordner is not None:
            if hat_klarname(ordner.name) or not klar:
                return ordner, True, None
            return ordner, True, region / bereinigen_mit_leerzeichen(f"{ril} - {klar}")

        if not klar and "-" in auswahl:
            klar = auswahl.split("-", 1)[1].strip()
        if not klar:
            return None, False, None
        return region / bereinigen_mit_leerzeichen(f"{ril} - {klar}"), False, None

    def vorschau_aktualisieren(self):
        try:
            bst, existiert, neu = self.betriebsstelle_ermitteln()
        except OSError:
            bst, existiert, neu = None, False, None
        if bst is None:
            if self.ril_wert():
                txt = "Betriebsstelle nicht vorhanden – bitte Klarname für Neuanlage eingeben."
            else:
                txt = (f"{len(self.bst_map)} Betriebsstelle(n) in {self.region_pfad()} gefunden – "
                       "bitte auswählen oder RIL100-Kürzel eingeben.")
            self.bst_status.config(text=txt, foreground="darkorange")
            self.klar_entry.config(state="normal")
            self.vorschau.config(text="")
            return

        ziel_bst = neu or bst
        if existiert and neu:
            self.bst_status.config(
                text=f"✏ Wird vervollständigt: {bst.name}  →  {neu.name}", foreground="#1f5fbf")
            self.klar_entry.config(state="normal")
        elif existiert and not hat_klarname(bst.name):
            self.bst_status.config(
                text=f"✔ Vorhanden ohne Klarname: {bst}  – Klarname eingeben, um den Ordnernamen "
                     "zu vervollständigen (optional).", foreground="darkgreen")
            self.klar_entry.config(state="normal")
        elif existiert:
            self.bst_status.config(text=f"✔ Vorhanden: {bst}", foreground="darkgreen")
            self.klar_entry.config(state="disabled")
        else:
            self.bst_status.config(text=f"➕ Wird neu angelegt: {bst}", foreground="darkorange")
            self.klar_entry.config(state="normal")
        self.vorschau.config(text=f"Projektordner: {ziel_bst / self.projektordnername()}")

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
        start = next((k for k in kandidaten if k and Path(k).is_dir()), None)
        if start is None:
            messagebox.showwarning(
                "Laufwerk nicht erreichbar",
                f"{kennung}-Laufwerk ist nicht erreichbar:\n{KOPIERBEREICHE[kennung][2]}\n\n"
                "VPN/Netzwerkverbindung und Berechtigung prüfen. "
                "Der Auswahldialog öffnet sich trotzdem.")
        d = filedialog.askdirectory(initialdir=start, title=f"{kennung}-Ordner wählen")
        if d:
            self.quellen[kennung].set(str(Path(d)))
            self.auswahlen[kennung].approve(self.kopierkontext())
            self.hinweise[kennung].config(
                text=f"Manuell ausgewählt und als Quelle bestätigt:\n{d}\n"
                     "Zum Kopieren zusätzlich „Daten kopieren“ aktivieren.",
                foreground="#1f5fbf")

    # ------------------------------------------------ Anlegen
    def anlegen(self):
        psp = normalisiere_psp(self.psp.get())
        if self.psp.get() != psp:
            self.psp.set(psp)
        az, beschr = self.az.get().strip(), self.beschr.get().strip()
        ril = self.ril_wert()
        if not (ril and psp and az and beschr):
            messagebox.showerror("Fehlende Angaben",
                                 "Bitte Betriebsstelle/RIL100-Kürzel, Anlagenzustand, PSP-Element und "
                                 "Projektbeschreibung ausfüllen.")
            return
        bst, existiert, neu = self.betriebsstelle_ermitteln()
        if bst is None:
            messagebox.showerror("Fehlende Angaben",
                                 f"Für '{ril}' gibt es noch keinen Ordner.\n"
                                 "Bitte Klarname der Betriebsstelle eingeben.")
            return
        if neu is not None and neu.exists():
            messagebox.showerror("Umbenennen nicht möglich",
                                 f"Der Ordner existiert bereits:\n{neu}\n\n"
                                 f"Bitte diesen Ordner in der Liste auswählen oder '{bst.name}' "
                                 "manuell zusammenführen.")
            return

        kontext = self.kopierkontext()
        auftraege = []
        breite_quellen = []
        ziel_bst = neu or bst
        for kennung in KOPIERBEREICHE:
            auswahl = self.auswahlen[kennung]
            ziel = (ziel_bst / self.projektordnername() / KOPIERBEREICHE[kennung][0]
                    / self.unterziele[kennung].get() / Path(auswahl.source or ".").name)
            try:
                auftrag = kopierauftrag_pruefen(
                    kennung, auswahl, kontext, ziel, self.vorschlaege[kennung])
            except ValueError as e:
                messagebox.showerror("Kopierauswahl prüfen", str(e))
                return
            if auftrag is None:
                continue
            _, quelle, ziel = auftrag
            if not quelle.is_dir():
                messagebox.showerror("Fehler", f"{kennung}-Quelle nicht gefunden:\n{quelle}")
                return
            auftraege.append(auftrag)
            if quelle_ist_gesamtordner(
                    kennung, quelle, self.vorschlaege[kennung], kontext):
                breite_quellen.append((kennung, quelle))

        warn = []
        if not existiert and not RIL_MUSTER.match(ril):
            warn.append(f"RIL100-Kürzel '{ril}' sieht ungewöhnlich aus (2–5 Zeichen erwartet).")
        if not AZ_MUSTER.match(az):
            warn.append(f"Anlagenzustand '{az}' ist nicht 4-stellig numerisch.")
        if not PSP_MUSTER.match(psp):
            warn.append(f"PSP-Element '{psp}' entspricht nicht dem Format M17525-01 "
                        "oder M19061-01A (optional ein abschließender Großbuchstabe).")
        if not existiert:
            warn.append(f"Betriebsstellenordner wird neu angelegt:\n{bst}")
        if neu is not None:
            warn.append(f"Betriebsstellenordner wird umbenannt:\n{bst.name}  →  {neu.name}")
        for k, p, _ in auftraege:
            warn.append(f"{k} wird kopiert von:\n{p}")

        for kennung, quelle in breite_quellen:
            text = (
                f"{kennung}: Es wird der gesamte Ordner rekursiv einschließlich aller "
                f"Unterordner kopiert:\n{quelle}\n\n"
                "Sind Sie sicher, dass dieser vollständige Ordner kopiert werden soll?")
            if not messagebox.askyesno(
                    "Gesamten Ordner kopieren", text, default="no", icon="warning"):
                return

        if warn and not messagebox.askyesno("Hinweis", "\n\n".join(warn) + "\n\nFortfahren?"):
            return

        auftraege_snapshot = tuple(auftraege)
        if neu is not None:
            try:
                bst.rename(neu)
            except OSError as e:
                messagebox.showerror(
                    "Umbenennen fehlgeschlagen",
                    f"'{bst.name}' konnte nicht in '{neu.name}' umbenannt werden:\n{e}\n\n"
                    "Ist eine Datei oder ein Explorer-Fenster in diesem Ordner geöffnet?")
                return
            bst = neu
            self.klarname.set("")

        wurzel = bst / self.projektordnername()
        quellen = {k: q for k, q, _ in auftraege}
        try:
            for p in vorlage_parsen(VORLAGE):
                (wurzel / p).mkdir(parents=True, exist_ok=True)
            info = wurzel / "Projektinfo.txt"
            if not info.exists():
                info.write_text(
                    f"Region:              {self.region.get()}\n"
                    f"Betriebsstelle:      {bst.name}\n"
                    f"Anlagenzustand:      {az}\n"
                    f"PSP-Element:         {psp}\n"
                    f"Projektbeschreibung: {beschr}\n"
                    f"Angelegt am:         {date.today():%d.%m.%Y}\n"
                    f"PT1-Quelle:          {quellen.get('PT1', '-')}\n"
                    f"PT2-Quelle:          {quellen.get('PT2', '-')}\n",
                    encoding="utf-8",
                )
        except OSError as e:
            messagebox.showerror("Fehler", f"Struktur konnte nicht angelegt werden:\n{e}")
            return

        self.wurzel = wurzel
        self.liste_aktualisieren()
        self.bst.set(self.anzeige(bst.name))

        if not quellen:
            self.status.config(text=f"Struktur angelegt: {wurzel}")
            messagebox.showinfo("Fertig", f"Struktur angelegt:\n{wurzel}")
            return

        self.btn.config(state="disabled")
        self.status.config(text="Ermittle Dateien …")
        threading.Thread(
            target=ordner_kopieren, args=(auftraege_snapshot, self.q), daemon=True).start()
        self.after(100, self.abfragen)

    def abfragen(self):
        try:
            while True:
                m = self.q.get_nowait()
                if m[0] == "start":
                    self.status.config(text=f"{m[1]}: Ermittle Dateien …")
                elif m[0] == "max":
                    self.balken.config(maximum=max(m[1], 1), value=0)
                elif m[0] == "fortschritt":
                    _, i, kennung, name = m
                    self.balken.config(value=i)
                    self.status.config(
                        text=f"{kennung}: Kopiere {i}/{int(self.balken['maximum'])}: {name}")
                elif m[0] == "fertig":
                    self.btn.config(state="normal")
                    zeilen, alle_fehler = [], []
                    for kennung, kop, ueb, fehler, abbruch in m[1]:
                        if abbruch:
                            zeilen.append(f"{kennung}: ABBRUCH – {abbruch}")
                        else:
                            zeilen.append(f"{kennung} kopiert: {kop} Dateien, {ueb} bereits "
                                          "vorhanden (nicht überschrieben).")
                        alle_fehler += [f"[{kennung}] {x}" for x in fehler]
                    txt = "\n".join(zeilen)
                    self.status.config(text=" | ".join(zeilen))
                    if alle_fehler:
                        (self.wurzel / "Kopierfehler.txt").write_text(
                            "\n".join(alle_fehler), encoding="utf-8")
                        txt += f"\n\n{len(alle_fehler)} Fehler – siehe Kopierfehler.txt"
                    messagebox.showinfo("Fertig", f"Struktur angelegt:\n{self.wurzel}\n\n{txt}")
                    return
        except queue.Empty:
            pass
        self.after(100, self.abfragen)


if __name__ == "__main__":
    App().mainloop()
