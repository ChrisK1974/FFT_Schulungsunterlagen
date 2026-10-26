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
- Kopiert optional je einen Ordner von den Ablagelaufwerken nach
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

# ---------------------------------------------------------------- Einstellungen
# Basisverzeichnis, unter dem die Regionen liegen
STANDARD_BASIS = r"C:\Projekte"

# Anzeigename -> Ordnername auf dem Laufwerk
REGIONEN = {
    "Nord": "NORD",
    "Ost": "OST",
    "Südost": "SUEDOST",
    "Süd": "SUED",
    "Südwest": "SUEDWEST",
    "West": "WEST",
}

# Kopierbereiche: Kennung -> (Pfad im Projekt, mögliche Unterordner, Startordner des Auswahldialogs)
# Hinweis: UNC-Pfade in r"..." ohne abschließenden Backslash angeben.
KOPIERBEREICHE = {
    "PT1": (Path("01_Eingangsunterlagen", "PT1"), ["Stellwerk", "ZX", "sonstiges"],
            r"\\Thsdiza06fs01\psp"),
    "PT2": (Path("01_Eingangsunterlagen", "PT2"), ["Stellwerk", "ZX"],
            r"\\destgsfs10\IL90-Projekte-ro"),
}

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

PSP_MUSTER = re.compile(r"^[A-Z]\d{5}-\d{2}$")           # z. B. M17525-01
AZ_MUSTER = re.compile(r"^\d{4}$")                       # z. B. 0180
RIL_MUSTER = re.compile(r"^[A-ZÄÖÜ][A-ZÄÖÜ0-9 ]{1,4}$")  # z. B. BLN, BL, BLN F
# Ordner "<RIL> - <Name>"
BST_MIT_KLARNAME = re.compile(r"^\s*[A-Za-zÄÖÜäöü0-9 ]{1,6}?\s*-\s*\S")
# Ordner nur "<RIL>" (1–5 Zeichen, beginnt mit Buchstabe)
BST_NUR_RIL = re.compile(r"^[A-Za-zÄÖÜäöü][A-Za-zÄÖÜäöü0-9 ]{0,4}$")
UNGUELTIG = re.compile(r'[<>:"/\\|?*]')


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


def ordner_kopieren(auftraege, q: queue.Queue):
    """
    Kopiert nacheinander alle Aufträge [(kennung, quelle, ziel), ...] rekursiv.
    Vorhandene Dateien werden NICHT überschrieben.
    """
    ergebnisse = []
    for kennung, quelle, ziel in auftraege:
        try:
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
        self.resizable(False, False)
        self.q = queue.Queue()
        self.wurzel = None
        self.bst_map = {}      # Anzeigetext in der Liste -> echter Ordnername

        self.basis = tk.StringVar(value=STANDARD_BASIS)
        self.region = tk.StringVar(value="Ost")
        self.bst = tk.StringVar()          # Auswahl aus Liste ODER getipptes RIL100-Kürzel
        self.klarname = tk.StringVar()
        self.psp = tk.StringVar()
        self.az = tk.StringVar()
        self.beschr = tk.StringVar()
        # je Kopierbereich: Quelle und Zielunterordner
        self.quellen = {k: tk.StringVar() for k in KOPIERBEREICHE}
        self.unterziele = {k: tk.StringVar(value=v[1][0]) for k, v in KOPIERBEREICHE.items()}

        f = ttk.Frame(self, padding=12)
        f.grid()
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

        # --- PT1 / PT2
        for kennung, (_, unterordner, start) in KOPIERBEREICHE.items():
            ueberschrift(f"{kennung}-Unterlagen  ({start})")
            zeile(f"{kennung}-Quellordner (optional):",
                  ttk.Entry(f, textvariable=self.quellen[kennung], width=55),
                  ttk.Button(f, text="Durchsuchen…",
                             command=lambda k=kennung: self.quelle_waehlen(k)))
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
        for v in (self.bst, self.klarname, self.psp, self.az, self.beschr):
            v.trace_add("write", lambda *_: self.vorschau_aktualisieren())
        self.liste_aktualisieren()

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
        teile = [self.az.get().strip(), self.psp.get().strip(), self.beschr.get().strip()]
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
        start = KOPIERBEREICHE[kennung][2]
        if not Path(start).exists():
            messagebox.showwarning(
                "Laufwerk nicht erreichbar",
                f"{kennung}-Laufwerk ist nicht erreichbar:\n{start}\n\n"
                "VPN/Netzwerkverbindung und Berechtigung prüfen. "
                "Der Auswahldialog öffnet sich trotzdem.")
            start = None
        d = filedialog.askdirectory(initialdir=start,
                                    title=f"{kennung}-Ordner wählen")
        if d:
            self.quellen[kennung].set(str(Path(d)))

    # ------------------------------------------------ Anlegen
    def anlegen(self):
        psp, az, beschr = self.psp.get().strip(), self.az.get().strip(), self.beschr.get().strip()
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

        quellen = {}
        for kennung in KOPIERBEREICHE:
            q = self.quellen[kennung].get().strip()
            if q:
                p = Path(q)
                if not p.is_dir():
                    messagebox.showerror("Fehler", f"{kennung}-Quelle nicht gefunden:\n{p}")
                    return
                quellen[kennung] = p

        warn = []
        if not existiert and not RIL_MUSTER.match(ril):
            warn.append(f"RIL100-Kürzel '{ril}' sieht ungewöhnlich aus (2–5 Zeichen erwartet).")
        if not AZ_MUSTER.match(az):
            warn.append(f"Anlagenzustand '{az}' ist nicht 4-stellig numerisch.")
        if not PSP_MUSTER.match(psp):
            warn.append(f"PSP-Element '{psp}' entspricht nicht dem Format M17525-01.")
        if not existiert:
            warn.append(f"Betriebsstellenordner wird neu angelegt:\n{bst}")
        if neu is not None:
            warn.append(f"Betriebsstellenordner wird umbenannt:\n{bst.name}  →  {neu.name}")
        if warn and not messagebox.askyesno("Hinweis", "\n\n".join(warn) + "\n\nFortfahren?"):
            return

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

        auftraege = [
            (k, q, wurzel / KOPIERBEREICHE[k][0] / self.unterziele[k].get() / q.name)
            for k, q in quellen.items()
        ]
        self.btn.config(state="disabled")
        self.status.config(text="Ermittle Dateien …")
        threading.Thread(target=ordner_kopieren, args=(auftraege, self.q), daemon=True).start()
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
