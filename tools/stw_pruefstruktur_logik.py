"""Tk-freie Entscheidungslogik für die Prüfstruktur."""
import os
import re
from pathlib import Path


PSP_MUSTER = re.compile(r"^[A-Z]\d{5}-\d{2}[A-Z]?$")


class CopySelection:
    """Kopierauswahl mit an Quelle und Eingabekontext gebundener Freigabe."""
    def __init__(self):
        self.source = ""
        self.enabled = False
        self.copy_all = False
        self.approval = None

    def set_source(self, source):
        source = str(source).strip()
        if source != self.source:
            self.source = source
            self.approval = None
            self.enabled = False
            self.copy_all = False

    def approve(self, context):
        if not self.source:
            return False
        self.approval = (normalisierter_pfad(self.source), tuple(context))
        return True

    def is_approved(self, context):
        return (self.approval == (normalisierter_pfad(self.source), tuple(context))
                if self.source else False)

    def revoke_if_context_changed(self, context):
        if self.approval and self.approval[1] != tuple(context):
            self.approval = None
            self.enabled = False
            return True
        return False

    def clear(self):
        self.source = ""
        self.enabled = False
        self.copy_all = False
        self.approval = None


def normalisiere_psp(psp):
    return psp.strip().upper()


def normalisierter_pfad(pfad):
    """Normalisiert Pfade rein syntaktisch; führt keine Dateisystemabfrage aus."""
    return os.path.normcase(os.path.abspath(os.path.normpath(os.fspath(pfad))))


def pfade_ueberlappen(quelle, ziel):
    """True bei gleichen Pfaden oder wenn einer den anderen enthält."""
    quelle, ziel = normalisierter_pfad(quelle), normalisierter_pfad(ziel)
    try:
        gemeinsam = os.path.commonpath((quelle, ziel))
    except ValueError:
        return False
    gemeinsam = os.path.normcase(gemeinsam)
    return gemeinsam == quelle or gemeinsam == ziel


def quelle_ist_gesamtordner(kennung, quelle, wurzel, vorschlag=None, kontext=()):
    """Erkennt Freigabe-, Gruppen-, Regions- und Projekt-/Betriebsstellenordner."""
    if vorschlag and normalisierter_pfad(quelle) == normalisierter_pfad(vorschlag):
        return True
    name = Path(quelle).name
    if kennung == "PT1" and re.match(
            r"^[A-Z]\d{5}-\d{2}[A-Z]?(?:[\s_-]|$)", name, re.IGNORECASE):
        return True
    if kennung == "PT2" and len(kontext) > 2 and kontext[2]:
        ril = re.escape(str(kontext[2]).replace(" ", ""))
        if re.match(r"^" + ril + r"(?:\d|[\s_-]|$)", name, re.IGNORECASE):
            return True
    wurzel = normalisierter_pfad(wurzel)
    pfad = normalisierter_pfad(quelle)
    try:
        rel = os.path.relpath(pfad, wurzel)
    except ValueError:
        return False
    if rel == os.curdir:
        return True
    if rel == os.pardir or rel.startswith(os.pardir + os.sep) or os.path.isabs(rel):
        return False
    return len(Path(rel).parts) <= 2


def kopierauftrag_pruefen(kennung, auswahl, kontext, ziel, wurzel, vorschlag=None):
    """Validiert eine aktive Auswahl und liefert einen unveränderlichen Kopierauftrag."""
    if not auswahl.enabled:
        return None
    if not auswahl.source or not auswahl.is_approved(kontext):
        raise ValueError(
            f"{kennung}: Quelle nicht ausdrücklich bestätigt. Quelle löschen oder auswählen "
            "und anschließend bestätigen.")
    quelle = Path(auswahl.source)
    if quelle_ist_gesamtordner(
            kennung, quelle, wurzel, vorschlag, kontext) and not auswahl.copy_all:
        raise ValueError(
            f"{kennung}: Dieser breite Ordner darf nur mit „Gesamten Ordner einschließlich "
            "aller Unterordner kopieren“ verwendet werden.")
    if pfade_ueberlappen(quelle, ziel):
        raise ValueError(f"{kennung}: Quelle und Ziel überschneiden sich:\n{quelle}\n{ziel}")
    return (kennung, quelle, Path(ziel))


def suchergebnis_ist_aktuell(nummer, aktuelle_nummer, kontext, aktueller_kontext):
    return nummer == aktuelle_nummer and tuple(kontext) == tuple(aktueller_kontext)


def pt1_gruppenordner(psp, wurzel, gruppe_stellen=3, gruppe_suffix="xxx"):
    return Path(wurzel) / (normalisiere_psp(psp)[:gruppe_stellen] + gruppe_suffix)


def pt1_ordner_finden(psp, wurzel, gruppe_stellen=3, gruppe_suffix="xxx"):
    """Findet nur Ordner mit vollständiger PSP und einem klaren Trenner dahinter."""
    psp = normalisiere_psp(psp)
    gruppe = pt1_gruppenordner(psp, wurzel, gruppe_stellen, gruppe_suffix)
    muster = re.compile(r"^" + re.escape(psp) + r"(?:[\s_\-]|$)", re.IGNORECASE)
    try:
        if not gruppe.is_dir():
            return [], f"Ordner nicht gefunden: {gruppe}"
        treffer = sorted(
            (d for d in gruppe.iterdir() if d.is_dir() and muster.match(d.name)),
            key=lambda d: d.name.casefold())
    except OSError as e:
        return [], f"PT1-Laufwerk nicht lesbar: {e}"
    if not treffer:
        return [], f"Kein Ordner für {psp} in {gruppe} gefunden."
    return treffer, None
