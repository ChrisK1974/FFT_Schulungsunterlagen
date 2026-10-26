#!/usr/bin/env python3
"""
Prüfstruktur für Stellwerksprojekte anlegen (mit grafischer Oberfläche).

- Eingaben: PSP-Element, Anlagenzustand, Projektbeschreibung
- Legt die Verzeichnisstruktur nach VORLAGE an
- Kopiert optional einen Ordner der zentralen Ablage nach
  01_Eingangsunterlagen/PT1/<Stellwerk|ZX|sonstiges>

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
# Startordner des Auswahldialogs für PT1 (zentrales Ablagelaufwerk)
ZENTRALE_ABLAGE = r"\\server\projekte"   # z. B. r"P:\Projekte"
# Standard-Zielordner für die Projektverzeichnisse
STANDARD_ZIEL = str(Path.home() / "Pruefungen")

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
PT1_PFAD = Path("01_Eingangsunterlagen", "PT1")
PT1_UNTERORDNER = ["Stellwerk", "ZX", "sonstiges"]

PSP_MUSTER = re.compile(r"^[A-Z]\d{5}-\d{2}$")   # z. B. M17525-01
AZ_MUSTER = re.compile(r"^\d{4}$")               # z. B. 0180
UNGUELTIG = re.compile(r'[<>:"/\\|?*]')


# ---------------------------------------------------------------- Logik
def bereinigen(name: str) -> str:
    return UNGUELTIG.sub("_", name.strip()).replace(" ", "_")


def vorlage_parsen(text: str):
    pfade, stapel = [], []
    for zeile in text.splitlines():
        if not zeile.strip() or zeile.lstrip().startswith("#"):
            continue
        tiefe = (len(zeile) - len(zeile.lstrip(" "))) // 2
        stapel = stapel[:tiefe] + [bereinigen(zeile)]
        pfade.append(Path(*stapel))
    return pfade


def ordner_kopieren(quelle: Path, ziel: Path, q: queue.Queue):
    """Kopiert rekursiv; vorhandene Dateien werden NICHT überschrieben."""
    try:
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
            q.put(("fortschritt", i, src.name))
        q.put(("fertig", kopiert, uebersprungen, fehler))
    except Exception as e:  # z. B. Laufwerk nicht erreichbar
        q.put(("abbruch", str(e)))


# ---------------------------------------------------------------- Oberfläche
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Prüfstruktur Stellwerksprojekt")
        self.resizable(False, False)
        self.q = queue.Queue()
        self.wurzel = None

        self.psp = tk.StringVar()
        self.az = tk.StringVar()
        self.beschr = tk.StringVar()
        self.ziel = tk.StringVar(value=STANDARD_ZIEL)
        self.pt1 = tk.StringVar()
        self.pt1_ziel = tk.StringVar(value=PT1_UNTERORDNER[0])

        f = ttk.Frame(self, padding=12)
        f.grid()
        zeilen = [
            ("PSP-Element (z. B. M17525-01):", self.psp, None),
            ("Anlagenzustand (z. B. 0180):", self.az, None),
            ("Projektbeschreibung:", self.beschr, None),
            ("Zielverzeichnis:", self.ziel, self.ziel_waehlen),
            ("PT1 von zentraler Ablage (optional):", self.pt1, self.pt1_waehlen),
        ]
        for r, (text, var, cmd) in enumerate(zeilen):
            ttk.Label(f, text=text).grid(row=r, column=0, sticky="w", pady=3)
            ttk.Entry(f, textvariable=var, width=55).grid(row=r, column=1, padx=5)
            if cmd:
                ttk.Button(f, text="Durchsuchen…", command=cmd).grid(row=r, column=2)

        ttk.Label(f, text="PT1 kopieren nach:").grid(row=5, column=0, sticky="w", pady=3)
        ttk.Combobox(f, textvariable=self.pt1_ziel, values=PT1_UNTERORDNER,
                     state="readonly", width=20).grid(row=5, column=1, sticky="w", padx=5)

        self.vorschau = ttk.Label(f, foreground="gray")
        self.vorschau.grid(row=6, column=0, columnspan=3, sticky="w", pady=(8, 0))
        for v in (self.psp, self.az, self.beschr):
            v.trace_add("write", lambda *_: self.vorschau_aktualisieren())

        self.balken = ttk.Progressbar(f, length=500)
        self.balken.grid(row=7, column=0, columnspan=3, pady=8, sticky="we")
        self.status = ttk.Label(f, text="Bereit.")
        self.status.grid(row=8, column=0, columnspan=3, sticky="w")

        self.btn = ttk.Button(f, text="Struktur anlegen", command=self.anlegen)
        self.btn.grid(row=9, column=2, pady=(10, 0), sticky="e")
        self.vorschau_aktualisieren()

    def ordnername(self):
        return bereinigen(f"{self.psp.get()}_AZ{self.az.get()}_{self.beschr.get()}")

    def vorschau_aktualisieren(self):
        self.vorschau.config(text=f"Projektordner: {self.ordnername()}")

    def ziel_waehlen(self):
        d = filedialog.askdirectory(initialdir=self.ziel.get() or None)
        if d:
            self.ziel.set(d)

    def pt1_waehlen(self):
        start = ZENTRALE_ABLAGE if Path(ZENTRALE_ABLAGE).exists() else None
        d = filedialog.askdirectory(initialdir=start, title="PT1-Ordner auf zentraler Ablage wählen")
        if d:
            self.pt1.set(d)

    def anlegen(self):
        psp, az, beschr = self.psp.get().strip(), self.az.get().strip(), self.beschr.get().strip()
        if not (psp and az and beschr):
            messagebox.showerror("Fehlende Angaben",
                                 "Bitte PSP-Element, Anlagenzustand und Projektbeschreibung ausfüllen.")
            return
        warn = []
        if not PSP_MUSTER.match(psp):
            warn.append(f"PSP-Element '{psp}' entspricht nicht dem Format M17525-01.")
        if not AZ_MUSTER.match(az):
            warn.append(f"Anlagenzustand '{az}' ist nicht 4-stellig numerisch.")
        if warn and not messagebox.askyesno("Hinweis", "\n".join(warn) + "\n\nTrotzdem fortfahren?"):
            return

        wurzel = Path(self.ziel.get()) / self.ordnername()
        try:
            for p in vorlage_parsen(VORLAGE):
                (wurzel / p).mkdir(parents=True, exist_ok=True)
            info = wurzel / "Projektinfo.txt"
            if not info.exists():
                info.write_text(
                    f"PSP-Element:         {psp}\n"
                    f"Anlagenzustand:      {az}\n"
                    f"Projektbeschreibung: {beschr}\n"
                    f"Angelegt am:         {date.today():%d.%m.%Y}\n"
                    f"PT1-Quelle:          {self.pt1.get() or '-'}\n",
                    encoding="utf-8",
                )
        except OSError as e:
            messagebox.showerror("Fehler", f"Struktur konnte nicht angelegt werden:\n{e}")
            return

        self.wurzel = wurzel
        quelle = self.pt1.get().strip()
        if not quelle:
            self.status.config(text=f"Struktur angelegt: {wurzel}")
            messagebox.showinfo("Fertig", f"Struktur angelegt:\n{wurzel}")
            return

        quelle = Path(quelle)
        if not quelle.is_dir():
            messagebox.showerror("Fehler", f"PT1-Quelle nicht gefunden:\n{quelle}")
            return
        ziel = wurzel / PT1_PFAD / self.pt1_ziel.get() / quelle.name
        self.btn.config(state="disabled")
        self.status.config(text="Ermittle Dateien …")
        threading.Thread(target=ordner_kopieren, args=(quelle, ziel, self.q), daemon=True).start()
        self.after(100, self.abfragen)

    def abfragen(self):
        try:
            while True:
                m = self.q.get_nowait()
                if m[0] == "max":
                    self.balken.config(maximum=max(m[1], 1), value=0)
                elif m[0] == "fortschritt":
                    self.balken.config(value=m[1])
                    self.status.config(text=f"Kopiere {m[1]}/{int(self.balken['maximum'])}: {m[2]}")
                elif m[0] == "fertig":
                    _, kop, ueb, fehler = m
                    self.btn.config(state="normal")
                    txt = f"PT1 kopiert: {kop} Dateien, {ueb} bereits vorhanden (nicht überschrieben)."
                    self.status.config(text=txt)
                    if fehler:
                        (self.wurzel / "PT1_Kopierfehler.txt").write_text("\n".join(fehler), encoding="utf-8")
                        txt += f"\n\n{len(fehler)} Fehler – siehe PT1_Kopierfehler.txt"
                    messagebox.showinfo("Fertig", f"Struktur angelegt:\n{self.wurzel}\n\n{txt}")
                    return
                elif m[0] == "abbruch":
                    self.btn.config(state="normal")
                    messagebox.showerror("Abbruch", f"Kopieren fehlgeschlagen:\n{m[1]}")
                    return
        except queue.Empty:
            pass
        self.after(100, self.abfragen)


if __name__ == "__main__":
    App().mainloop()
