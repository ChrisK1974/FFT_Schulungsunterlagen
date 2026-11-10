#!/usr/bin/env python3
"""Stellwerksprojekte anlegen und PT1-/PT2-Unterlagen direkt übernehmen.

Python 3.8+, nur Standardbibliothek. Start: Strukturanlegen_starten.bat
Bestehende Projekte aus der bisherigen Version werden ebenfalls unterstuetzt.
Vorhandene Dateien werden nicht überschrieben; identische Dateien können übersprungen werden.
Die editierbare Ordnerstruktur steht in Ordnerstruktur.txt neben diesem Programm.
"""
import hashlib
import json
import logging
import ntpath
import os
import queue
import re
import shutil
import stat
import sys
import tempfile
import threading
import time
import traceback
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


STANDARD_BASIS = r"C:\Projekte"
REGIONEN = {
    "Nord": "NORD", "Ost": "OST", "Südost": "SUEDOST",
    "Süd": "SUED", "Südwest": "SUEDWEST", "West": "WEST",
}
KOPIERBEREICHE = {
    "PT1": (Path("01_Eingangsunterlagen", "PT1"),
            ("Stellwerk", "ZX", "sonstiges"), r"\\Thsdiza06fs01\psp"),
    "PT2": (Path("01_Eingangsunterlagen", "PT2"),
            ("Stellwerk", "ZX"), r"\\destgsfs10\IL90-Projekte-ro"),
}
PT1_UNTERORDNER = Path("001_PT1", "002_PT1 elektronisch")
STRUKTURDATEI = (
    Path(sys.executable) if getattr(sys, "frozen", False) else Path(__file__)
).resolve().parent / "Ordnerstruktur.txt"
PSP_MUSTER = re.compile(r"[A-Z]\d{5}-\d{2}[A-Z]?\Z", re.ASCII)
AZ_MUSTER = re.compile(r"\d{4}\Z", re.ASCII)
RIL_MUSTER = re.compile(r"[A-ZÄÖÜ][A-ZÄÖÜ0-9 ]{1,4}\Z")
BST_MIT_KLARNAME = re.compile(r"^([A-ZÄÖÜ][A-ZÄÖÜ0-9 ]{1,4}?)\s*-\s*\S")
UNGUELTIG = re.compile(r'[<>:"/\\|?*\x00-\x1f\x7f]')
RESERVIERT = re.compile(
    r"^(?:CON|PRN|AUX|NUL|COM[0-9¹²³]|LPT[0-9¹²³])(?:\.|$)", re.I)
AUSSCHLUSS = {"ALT", "NEU", "TEMP", "TMP", "ARCHIV", "VORLAGE",
              "VORLAGEN", "KOPIE", "TEST", "SONSTIGES"}
META = ".projektpflege.json"
LOCK = ".stw-pflege.lock"
LANG = "\\\\?\\"
LANG_UNC = "\\\\?\\UNC\\"
LOG = logging.getLogger("stw")
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


class PflegeFehler(Exception):
    """Erwarteter, dem Benutzer anzuzeigender Arbeitsfehler."""


class Abbruch(Exception):
    pass


def langer_pfad(pfad):
    text = os.fspath(pfad)
    if os.name == "nt" and not text.startswith(LANG):
        text = ntpath.abspath(text)
        text = LANG_UNC + text[2:] if text.startswith("\\\\") else LANG + text
    return Path(text)


def anzeige_pfad(pfad):
    return (os.fspath(pfad)
            .replace(repr(LANG_UNC)[1:-1], repr("\\\\")[1:-1])
            .replace(repr(LANG)[1:-1], "")
            .replace(LANG_UNC, "\\\\").replace(LANG, ""))


def gleicher_pfad(a, b):
    return os.path.normcase(os.path.abspath(anzeige_pfad(a))) == os.path.normcase(
        os.path.abspath(anzeige_pfad(b)))


def bereinigen(text, leerzeichen=False):
    name = UNGUELTIG.sub("_", text.strip()).rstrip(". ")
    if RESERVIERT.match(name):
        name = "_" + name
    return (name if leerzeichen else name.replace(" ", "_")) or "_"


def vorlage_parsen(text):
    result, stack = [], []
    gesehen = {}
    for nummer, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        depth = indent // 2
        if "\t" in line or indent % 2 or depth > len(stack):
            raise PflegeFehler(
                "Zeile %s: Ungültige Einrückung. Je Ebene genau zwei Leerzeichen "
                "verwenden, keine Tabulatoren und keine Ebene überspringen." % nummer)
        name = line[indent:]
        if (name in {".", ".."} or name != name.strip() or name.endswith(".")
                or UNGUELTIG.search(name) or RESERVIERT.match(name)
                or len(name.encode("utf-16-le")) // 2 > 255):
            raise PflegeFehler(
                "Zeile %s: Ungültiger Ordnername %r. Keine Pfade, reservierten Namen "
                "oder abschließenden Leerzeichen/Punkte verwenden (maximal 255 Zeichen)." % (
                    nummer, name))
        if depth == 0 and name.casefold() in {META.casefold(), LOCK.casefold(), "projektinfo.txt"}:
            raise PflegeFehler("Zeile %s: %r ist für eine Programmdatei reserviert." % (nummer, name))
        stack = stack[:depth] + [name]
        pfad = Path(*stack)
        key = pfad.as_posix().casefold()
        if key in gesehen:
            raise PflegeFehler(
                "Zeile %s: Ordner %r ist doppelt (bereits in Zeile %s). "
                "Groß-/Kleinschreibung unterscheidet keine Ordner." % (
                    nummer, pfad.as_posix(), gesehen[key]))
        gesehen[key] = nummer
        result.append(pfad)
    if not result:
        raise PflegeFehler("Die Struktur enthält keine Ordner, nur Leerzeilen oder Kommentare.")
    return result


def struktur_laden():
    try:
        return vorlage_parsen(STRUKTURDATEI.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, PflegeFehler) as exc:
        raise PflegeFehler(
            "Strukturdatei kann nicht verwendet werden:\n%s\n\n%s\n\n"
            "Bitte die Datei im Texteditor korrigieren und als UTF-8 speichern. "
            "Es wurde keine neue Projektstruktur angelegt." % (STRUKTURDATEI, exc)) from exc


def ordner_verknuepfung(pfad):
    s = os.lstat(langer_pfad(pfad))
    return stat.S_ISLNK(s.st_mode) or getattr(s, "st_reparse_tag", 0) in {
        0xA0000003, 0xA000000C,
    }


def sicherer_ordner(pfad):
    pfad = langer_pfad(pfad).absolute()
    for part in reversed((pfad,) + tuple(pfad.parents)):
        if os.path.lexists(part):
            if ordner_verknuepfung(part) or not part.is_dir():
                raise PflegeFehler("Kein regulärer Ziel-/Quellordner: %s" % anzeige_pfad(part))
        else:
            part.mkdir()
    return pfad


def ist_unterhalb(pfad, basis):
    p, b = langer_pfad(pfad).resolve(), langer_pfad(basis).resolve()
    return p == b or b in p.parents


def ordner_inhalt(pfad):
    if ordner_verknuepfung(pfad):
        raise PflegeFehler("Verknüpfungen dürfen nicht als Quelle verwendet werden.")
    dirs, files = [], False
    with os.scandir(langer_pfad(pfad)) as entries:
        for entry in entries:
            if entry.is_dir(follow_symlinks=False):
                p = Path(pfad) / entry.name
                if not ordner_verknuepfung(p):
                    dirs.append(p)
            elif entry.is_file(follow_symlinks=False) and not entry.name.lower().endswith(".part"):
                files = True
    return sorted(dirs, key=lambda p: p.name.casefold()), files


def datei_hash(pfad):
    digest = hashlib.sha256()
    with langer_pfad(pfad).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def veroeffentlichen(teil, ziel):
    """Atomar ohne Ersetzen. Kein unsicherer exists()+replace()-Fallback."""
    if os.name == "nt":
        os.rename(teil, ziel)
    else:
        os.link(teil, ziel)


@contextmanager
def temporaere_datei(ziel):
    fd, name = tempfile.mkstemp(prefix=".stw-", suffix=".part", dir=str(ziel.parent))
    os.close(fd)
    teil = Path(name)
    try:
        yield teil
    finally:
        try:
            teil.unlink()
        except FileNotFoundError:
            pass
        except OSError:
            LOG.exception("Temporäre Datei konnte nicht entfernt werden: %s", teil)


def json_schreiben(ziel, daten, neu=False):
    ziel = langer_pfad(ziel)
    with temporaere_datei(ziel) as teil:
        with teil.open("w", encoding="utf-8") as out:
            json.dump(daten, out, ensure_ascii=False, indent=2)
            out.write("\n")
            out.flush()
            os.fsync(out.fileno())
        if neu:
            veroeffentlichen(teil, ziel)
        else:
            os.replace(teil, ziel)


def json_lesen(pfad):
    try:
        with langer_pfad(pfad).open(encoding="utf-8") as stream:
            value = json.load(stream)
    except (ValueError, UnicodeError) as exc:
        raise PflegeFehler("Ungültige JSON-Datei %s: %s" % (anzeige_pfad(pfad), exc)) from exc
    if not isinstance(value, dict):
        raise PflegeFehler("Ungültiges Datenformat: %s" % anzeige_pfad(pfad))
    return value


@contextmanager
def sperre(ordner):
    pfad = langer_pfad(ordner) / LOCK
    try:
        fd = os.open(str(pfad), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise PflegeFehler(
            "Projekt/Bereich ist gesperrt: %s\n"
            "Läuft das Tool bereits? Nach einem Absturz die Sperrdatei erst entfernen, "
            "wenn sicher kein anderer Lauf mehr aktiv ist." % anzeige_pfad(pfad)) from exc
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as out:
            out.write("PID %s; %s; %s\n" % (os.getpid(), datetime.now().isoformat(),
                                          uuid.uuid4().hex))
        yield
    finally:
        pfad.unlink()


def datei_kopieren(src, dst, size, mtime_ns, erwartet=None):
    """Prueft Quelle und fertiges Ziel; existierende Dateien werden nie ersetzt."""
    src, dst = langer_pfad(src), langer_pfad(dst)
    for ancestor in src.parents:
        if ordner_verknuepfung(ancestor):
            raise PflegeFehler("Quellpfad enthält eine Verknüpfung: %s" % ancestor)
    if os.path.lexists(dst):
        if erwartet and dst.is_file() and not ordner_verknuepfung(dst):
            if dst.stat().st_size == size and datei_hash(dst) == erwartet:
                return erwartet, False
        raise PflegeFehler("Zieldatei bereits vorhanden oder verändert: %s" % anzeige_pfad(dst))
    if ordner_verknuepfung(src):
        raise PflegeFehler("Quelldatei ist eine Verknüpfung: %s" % anzeige_pfad(src))
    before = src.stat()
    if not stat.S_ISREG(before.st_mode) or (before.st_size, before.st_mtime_ns) != (size, mtime_ns):
        raise PflegeFehler("Quelle seit Erfassung geändert: %s" % anzeige_pfad(src))
    sicherer_ordner(dst.parent)
    with temporaere_datei(dst) as teil:
        digest = hashlib.sha256()
        with src.open("rb") as incoming, teil.open("wb") as outgoing:
            for block in iter(lambda: incoming.read(1024 * 1024), b""):
                digest.update(block)
                outgoing.write(block)
            outgoing.flush()
            os.fsync(outgoing.fileno())
        after = src.stat()
        if (after.st_size, after.st_mtime_ns, after.st_ino) != (
                before.st_size, before.st_mtime_ns, before.st_ino):
            raise PflegeFehler("Quelle während Kopie geändert: %s" % anzeige_pfad(src))
        sha = digest.hexdigest()
        if erwartet and sha != erwartet:
            raise PflegeFehler("Quellinhalt passt nicht zum erwarteten Inhalt: %s" % src)
        shutil.copystat(src, teil, follow_symlinks=False)
        if teil.stat().st_size != size or datei_hash(teil) != sha:
            raise PflegeFehler("Prüfsummenfehler beim Kopieren: %s" % anzeige_pfad(src))
        veroeffentlichen(teil, dst)
        return sha, True


def region_ordner(basis, region):
    basis = langer_pfad(basis)
    soll = REGIONEN.get(region, region)
    erwartet = basis / soll

    # Den erwarteten Regionsordner direkt prüfen, ohne den Freigabe-Stamm
    # vollständig zu durchsuchen.
    if erwartet.is_dir():
        return erwartet

    # Fallback für abweichende Groß-/Kleinschreibung oder ältere Ordnernamen.
    # Erst den Namen filtern, damit irrelevante Einträge wie .ORC nicht
    # auf ihren Verzeichnisstatus geprüft werden.
    try:
        with os.scandir(basis) as entries:
            for entry in entries:
                if entry.name.casefold() not in {region.casefold(), soll.casefold()}:
                    continue
                if entry.is_dir(follow_symlinks=False):
                    return Path(entry.path)
    except FileNotFoundError:
        pass

    return erwartet


def ril_aus_eingabe(text):
    return " ".join(text.split("-", 1)[0].strip().upper().split())


def hat_klarname(text):
    return bool(BST_MIT_KLARNAME.match(text))


def betriebsstellen_auflisten(region):
    try:
        entries = list(langer_pfad(region).iterdir())
    except FileNotFoundError:
        return []
    return sorted((p.name for p in entries
                   if p.is_dir() and not ordner_verknuepfung(p)
                   and RIL_MUSTER.fullmatch(ril_aus_eingabe(p.name))
                   and ril_aus_eingabe(p.name) not in AUSSCHLUSS), key=str.casefold)


def zielname(quelle):
    quelle = Path(quelle)
    return quelle.parents[1].name if quelle.parts[-2:] == PT1_UNTERORDNER.parts else quelle.name


def beschreibung_aus_pt1(quelle):
    return re.sub(r"^[A-Z]\d{5}-\d{2}[A-Z]?(?:[\s_-]+|$)", "",
                  zielname(quelle), flags=re.I).strip(" _-")


def pt1_ordner_finden(psp):
    gruppe = langer_pfad(KOPIERBEREICHE["PT1"][2]) / (psp[:3] + "xxx")
    dirs = [p for p in gruppe.iterdir() if p.is_dir()]
    for key in dict.fromkeys((psp, re.sub(r"[A-Z]$", "", psp))):
        regex = re.compile("^" + re.escape(key) + r"(?:[\s_-]|$)", re.I)
        matches = sorted((p for p in dirs if regex.match(p.name)), key=lambda p: p.name.casefold())
        if matches:
            return [p / PT1_UNTERORDNER if (p / PT1_UNTERORDNER).is_dir() else p
                    for p in matches]
    raise PflegeFehler("Kein PT1-Projekt für %s in %s gefunden." % (psp, anzeige_pfad(gruppe)))


def pt2_ordner_finden(region, ril):
    root = region_ordner(KOPIERBEREICHE["PT2"][2], region)
    kern = ril.replace(" ", "")[:3]
    regex = re.compile("^" + re.escape(kern) + r"[0-9X]*(?:[\s_-].*)?$", re.I)
    rank = {(kern + suffix).casefold(): i for i, suffix in enumerate(("0", "X"))}

    matches = []
    with os.scandir(root) as entries:
        for entry in entries:
            # Unpassende Namen wie .ORC werden vor is_dir() aussortiert.
            if not regex.fullmatch(entry.name):
                continue
            if entry.is_dir(follow_symlinks=False):
                matches.append(Path(entry.path))

    if not matches:
        raise PflegeFehler("Kein PT2-Ordner für %s gefunden." % kern)
    return sorted(matches, key=lambda p: (rank.get(p.name.casefold(), 2), p.name.casefold()))


def projekt_lesen(projekt):
    projekt = langer_pfad(projekt)
    if not projekt.is_dir() or ordner_verknuepfung(projekt):
        raise PflegeFehler("Projektordner nicht vorhanden oder eine Verknüpfung.")
    if (projekt / META).exists():
        daten = json_lesen(projekt / META)
        if daten.get("version") != 1 or not all(isinstance(daten.get(k), str) and daten[k]
                                                for k in ("region", "bst", "az", "psp", "beschreibung")):
            raise PflegeFehler("Unbekannte oder unvollständige Projektmetadaten.")
        return daten
    info = projekt / "Projektinfo.txt"
    if not info.is_file():
        raise PflegeFehler("Kein Stellwerksprojekt: Projektinfo.txt fehlt.")
    keys = {"Region": "region", "Betriebsstelle": "bst", "Anlagenzustand": "az",
            "PSP-Element": "psp", "Projektbeschreibung": "beschreibung"}
    daten = {"version": 1}
    for line in info.read_text(encoding="utf-8-sig").splitlines():
        key, sep, value = line.partition(":")
        if sep and key.strip() in keys:
            daten.setdefault(keys[key.strip()], value.strip())
    if not all(daten.get(key) for key in keys.values()):
        raise PflegeFehler("Projektinfo.txt enthält nicht alle Projektangaben.")
    return daten


def projekt_anlegen(basis, region, auswahl, klar, az, psp, beschreibung):
    if not (os.fspath(basis).strip() and RIL_MUSTER.fullmatch(ril_aus_eingabe(auswahl))
            and AZ_MUSTER.fullmatch(az) and PSP_MUSTER.fullmatch(psp) and beschreibung.strip()):
        raise PflegeFehler("RIL100, Anlagenzustand, PSP oder Beschreibung ist ungültig.")
    struktur = struktur_laden()
    regionpfad = sicherer_ordner(region_ordner(basis, region))
    with sperre(regionpfad):
        namen = betriebsstellen_auflisten(regionpfad)
        ril = ril_aus_eingabe(auswahl)
        treffer = [n for n in namen if ril_aus_eingabe(n) == ril]
        if auswahl in treffer:
            name = auswahl
        elif len(treffer) > 1:
            raise PflegeFehler("Mehrere Betriebsstellen für %s: bitte vollständig auswählen." % ril)
        else:
            name = treffer[0] if treffer else ""
        if not name and not klar.strip():
            raise PflegeFehler("Für eine neue Betriebsstelle ist ein Klarname erforderlich.")
        bst = regionpfad / (name or bereinigen("%s - %s" % (ril, klar), True))
        neuer_name = (bereinigen("%s - %s" % (ril, klar), True)
                      if name and not hat_klarname(name) and klar.strip() else bst.name)
        neu = regionpfad / neuer_name
        if neu != bst and os.path.lexists(neu):
            raise PflegeFehler("Betriebsstellen-Ziel existiert bereits: %s" % anzeige_pfad(neu))
        bst_neu = not os.path.lexists(bst)
        if bst_neu:
            bst.mkdir()
        elif ordner_verknuepfung(bst):
            raise PflegeFehler("Betriebsstelle ist eine Verknüpfung.")
        projekt = bst / bereinigen("%s_%s_%s" % (az, psp, beschreibung))
        erstellt = []
        dateien = []
        try:
            try:
                projekt.mkdir()
            except FileExistsError as exc:
                raise PflegeFehler(
                    "Projekt existiert bereits: %s\nÜber 'Bestehendes Projekt' öffnen; "
                    "Neuanlage führt keine Projekte zusammen." % anzeige_pfad(projekt)) from exc
            erstellt.append(projekt)
            for rel in struktur:
                p = projekt / rel
                p.mkdir()
                erstellt.append(p)
            daten = {"version": 1, "region": region, "bst": neuer_name, "az": az,
                     "psp": psp, "beschreibung": beschreibung,
                     "angelegt": datetime.now().isoformat(timespec="seconds")}
            json_schreiben(projekt / META, daten, neu=True)
            dateien.append(projekt / META)
            info = projekt / "Projektinfo.txt"
            with info.open("x", encoding="utf-8") as out:
                dateien.append(info)
                out.write(
                    "Region:              {region}\nBetriebsstelle:      {bst}\n"
                    "Anlagenzustand:      {az}\nPSP-Element:         {psp}\n"
                    "Projektbeschreibung: {beschreibung}\nAngelegt am:         {angelegt}\n".format(**daten))
            # Erst das vollstaendig vorbereitete Projekt legitimiert die Umbenennung.
            if neu != bst:
                bst.rename(neu)
            return neu / projekt.name
        except Exception as exc:
            rollback = []
            for p in reversed(dateien):
                try:
                    p.unlink()
                except OSError as cleanup:
                    rollback.append(str(cleanup))
            for p in reversed(erstellt):
                try:
                    p.rmdir()
                except OSError as cleanup:
                    rollback.append(str(cleanup))
            if bst_neu:
                try:
                    bst.rmdir()
                except OSError as cleanup:
                    rollback.append(str(cleanup))
            if rollback:
                raise PflegeFehler(
                    "Anlegen fehlgeschlagen: %s\nRücknahme unvollständig; "
                    "Restordner bitte prüfen:\n%s" % (exc, "\n".join(rollback))) from exc
            raise


@dataclass(frozen=True)
class Auswahl:
    kennung: str
    wurzel: Path
    quelle: Path
    nur_dateien: bool
    ziel: str
    relativ: Path


def relativer_pfad(text):
    if not isinstance(text, str) or not text:
        raise PflegeFehler("Ungültiger relativer Pfad im Kopierplan.")
    # Relative Pfade werden plattformneutral mit '/' verarbeitet.
    teile = text.split("/")
    if any(t in ("", ".", "..") or bereinigen(t, True) != t for t in teile):
        raise PflegeFehler("Ungültiger relativer Pfad im Kopierplan: %r" % text)
    return Path(*teile)


def unterlagen_kopieren(projekt, auswahl, abbruch, melden):
    projekt = langer_pfad(projekt).absolute()
    projekt_lesen(projekt)
    ergebnis = {"kopiert": 0, "bereits_vorhanden": 0, "fehler": [], "hinweise": []}
    with sperre(projekt):
        ordner = {}
        dateien = []
        ziele = set()
        for a in auswahl:
            if a.kennung not in KOPIERBEREICHE or a.ziel not in KOPIERBEREICHE[a.kennung][1]:
                raise PflegeFehler("Ungültiger Kopierbereich oder Ziel.")
            root, source = langer_pfad(a.wurzel).absolute(), langer_pfad(a.quelle).absolute()
            try:
                relativ = source.relative_to(root)
            except ValueError as exc:
                raise PflegeFehler("Auswahl passt nicht zum Quellordner.") from exc
            if relativ != a.relativ:
                raise PflegeFehler("Auswahl passt nicht zum Quellordner.")
            if ist_unterhalb(source, projekt) or ist_unterhalb(projekt, source):
                raise PflegeFehler("Quelle und Projekt dürfen nicht ineinander liegen.")
            for ancestor in (source,) + tuple(source.parents):
                if ordner_verknuepfung(ancestor):
                    raise PflegeFehler("Quelle enthält eine Verknüpfung: %s" % ancestor)
            base = (KOPIERBEREICHE[a.kennung][0] / a.ziel
                    / bereinigen(zielname(root), True) / relativ)
            relativer_pfad(base.as_posix())

            def walk_error(exc):
                raise exc

            for current, dirs, names in os.walk(source, followlinks=False, onerror=walk_error):
                if abbruch.is_set():
                    raise Abbruch()
                relative = Path(current).relative_to(source)
                destdir = base / relative
                ordner[destdir.as_posix().casefold()] = destdir
                allowed = []
                for name in sorted(dirs, key=str.casefold):
                    path = Path(current) / name
                    if ordner_verknuepfung(path):
                        ergebnis["hinweise"].append(
                            "Verzeichnisverknüpfung ausgelassen: %s" % anzeige_pfad(path))
                    else:
                        allowed.append(name)
                dirs[:] = [] if a.nur_dateien else allowed
                for name in sorted(names, key=str.casefold):
                    if abbruch.is_set():
                        raise Abbruch()
                    src = Path(current) / name
                    if name.lower().endswith(".part") or ordner_verknuepfung(src):
                        ergebnis["hinweise"].append(
                            "Temporäre Datei/Verknüpfung ausgelassen: %s" % anzeige_pfad(src))
                        continue
                    info = src.stat()
                    if not stat.S_ISREG(info.st_mode):
                        raise PflegeFehler("Keine reguläre Quelldatei: %s" % anzeige_pfad(src))
                    dst = projekt / destdir / name
                    target = dst.relative_to(projekt).as_posix()
                    relativer_pfad(target)
                    key = target.casefold()
                    if key in ziele:
                        raise PflegeFehler("Mehrfach belegtes Kopierziel: %s" % target)
                    ziele.add(key)
                    dateien.append((src, dst, info.st_size, info.st_mtime_ns))

        for destdir in ordner.values():
            if abbruch.is_set():
                raise Abbruch()
            sicherer_ordner(projekt / relativer_pfad(destdir.as_posix()))

        total = len(dateien)
        for index, (src, dst, size, mtime_ns) in enumerate(dateien, 1):
            if abbruch.is_set():
                raise Abbruch()
            try:
                sicherer_ordner(dst.parent)
                erwartet = datei_hash(src) if os.path.lexists(dst) else None
                _, kopiert = datei_kopieren(src, dst, size, mtime_ns, erwartet)
                ergebnis["kopiert" if kopiert else "bereits_vorhanden"] += 1
            except (OSError, PflegeFehler) as exc:
                ergebnis["fehler"].append(
                    "%s: %s" % (anzeige_pfad(src), anzeige_pfad(str(exc))))
            melden("Prüfe/kopiere %s/%s: %s" % (index, total, src.name), index, total)
    return ergebnis


class OrdnerAuswahl(ttk.Frame):
    """Lazy Treeview; I/O nur im zentralen Hintergrund-Executor."""

    def __init__(self, master, app, kennung):
        super().__init__(master)
        self.app, self.kennung = app, kennung
        self.quelle = tk.StringVar()
        self.standard = tk.StringVar(value="Stellwerk")
        self.generation, self.job = 0, None
        self.wurzel = None
        self.ausstehend = False
        self.fehler = ""
        self.hat_unterordner = False
        self.knoten, self.markiert, self.geladen, self.ladend = {}, {}, set(), set()
        self.quellwert = ""
        self.columnconfigure(0, weight=1)
        top = ttk.Frame(self)
        top.grid(row=0, column=0, columnspan=2, sticky="ew")
        top.columnconfigure(0, weight=1)
        ttk.Entry(top, textvariable=self.quelle).grid(row=0, column=0, sticky="ew")
        ttk.Button(top, text="Durchsuchen …", command=self.waehlen).grid(row=0, column=1)
        ttk.Button(top, text="Neu laden", command=lambda: self.planen(True)).grid(row=0, column=2)
        self.baum = ttk.Treeview(self, columns=("ziel",), height=6, selectmode="browse")
        self.baum.heading("#0", text="Ordner / Auswahl")
        self.baum.heading("ziel", text="Kopieren nach")
        self.baum.column("#0", width=460)
        self.baum.column("ziel", width=130, stretch=False)
        self.baum.grid(row=1, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(self, orient="vertical", command=self.baum.yview)
        scroll.grid(row=1, column=1, sticky="ns")
        self.baum.configure(yscrollcommand=scroll.set)
        controls = ttk.Frame(self)
        controls.grid(row=2, column=0, sticky="ew")
        ttk.Button(controls, text="Alle", command=self.alle).pack(side="left")
        ttk.Button(controls, text="Keine", command=self.keine).pack(side="left")
        ttk.Label(controls, text="  Ziel für neue Häkchen: ").pack(side="left")
        ttk.Combobox(controls, textvariable=self.standard, state="readonly", width=14,
                     values=KOPIERBEREICHE[kennung][1]).pack(side="left")
        self.info = ttk.Label(self, text="Optional: keine Quelle gewählt.", wraplength=800)
        self.info.grid(row=3, column=0, sticky="w")
        self.suche_info = ttk.Label(self, text="", wraplength=800, foreground="gray")
        self.suche_info.grid(row=4, column=0, sticky="w")
        self.baum.bind("<<TreeviewOpen>>", self.oeffnen)
        self.baum.bind("<Button-1>", self.klicken)
        self.baum.bind("<space>", lambda _: self.taste())
        self.quelle.trace_add("write", lambda *_: self.planen())

    def waehlen(self):
        # Keine synchronen is_dir()-Abfragen auf moeglicherweise toten UNC-Pfaden.
        path = filedialog.askdirectory(title="%s-Quellordner wählen" % self.kennung)
        if path:
            self.app.auto_wert[self.kennung] = None
            self.quelle.set(path)

    def planen(self, neu=False):
        text = self.quelle.get().strip()
        if not neu and gleicher_pfad(text, self.quellwert):
            return
        self.quellwert = text
        self.generation += 1
        if self.job:
            self.after_cancel(self.job)
        self.ausstehend, self.fehler = True, ""
        self.info.configure(text="Quelle wird eingelesen …")
        self.app.knopf()
        self.job = self.after(400, self.wurzel_laden)
        if self.kennung == "PT1":
            self.app.beschreibung_vorschlagen(text)

    def wurzel_laden(self):
        self.job = None
        self.baum.delete(*self.baum.get_children())
        self.knoten, self.markiert, self.geladen, self.ladend = {}, {}, set(), set()
        text = self.quelle.get().strip()
        self.wurzel = langer_pfad(text) if text else None
        self.hat_unterordner = False
        if self.wurzel is None:
            self.ausstehend = False
            self.anzeigen()
        else:
            self.laden("", self.wurzel)

    def laden(self, node, path):
        if node in self.geladen or node in self.ladend:
            return
        self.ladend.add(node)
        generation = self.generation

        def fertig(result, error):
            if generation != self.generation:
                return
            self.ladend.discard(node)
            if node and not self.baum.exists(node):
                return
            if not node:
                self.ausstehend = False
            if error:
                self.fehler = str(error)
            else:
                self.geladen.add(node)
                self.baum.delete(*self.baum.get_children(node))
                dirs, files = result
                if not node:
                    self.hat_unterordner = bool(dirs)
                if files:
                    child = self.baum.insert(node, "end")
                    self.knoten[child] = (path, True)
                for p in dirs:
                    child = self.baum.insert(node, "end")
                    self.knoten[child] = (p, False)
                    self.baum.insert(child, "end", text="…")
            self.anzeigen()

        self.app.hintergrund(lambda: ordner_inhalt(path), fertig)

    def oeffnen(self, _=None):
        node = self.baum.focus()
        if node in self.knoten and not self.knoten[node][1]:
            self.laden(node, self.knoten[node][0])

    def uebergeordnet(self, p, nur):
        return next((z for (parent, files), z in self.markiert.items()
                     if not files and (parent in p.parents or (parent == p and nur))), None)

    def umschalten(self, node):
        if self.ausstehend or not self.hat_unterordner or node not in self.knoten:
            return
        p, nur = self.knoten[node]
        if self.uebergeordnet(p, nur):
            return
        key = (p, nur)
        if key in self.markiert:
            del self.markiert[key]
        else:
            if not nur:
                self.markiert = {k: z for k, z in self.markiert.items()
                                 if p not in k[0].parents and p != k[0]}
            self.markiert[key] = self.standard.get()
        self.anzeigen()

    def taste(self):
        self.umschalten(self.baum.focus())
        return "break"

    def klicken(self, event):
        node = self.baum.identify_row(event.y)
        if node not in self.knoten:
            return
        if self.baum.identify_column(event.x) == "#1":
            key = self.knoten[node]
            if key in self.markiert:
                menu = tk.Menu(self, tearoff=False)
                for ziel in KOPIERBEREICHE[self.kennung][1]:
                    menu.add_command(label=ziel, command=lambda z=ziel: self.ziel_setzen(key, z))
                try:
                    menu.tk_popup(event.x_root, event.y_root)
                finally:
                    menu.grab_release()
                    menu.destroy()
            return "break"
        if self.baum.identify("element", event.x, event.y) != "Treeitem.indicator":
            self.umschalten(node)

    def ziel_setzen(self, key, ziel):
        self.markiert[key] = ziel
        self.anzeigen()

    def alle(self):
        if not self.ausstehend and not self.fehler:
            self.markiert = {self.knoten[n]: self.standard.get()
                             for n in self.baum.get_children() if n in self.knoten}
            self.anzeigen()

    def keine(self):
        self.markiert.clear()
        self.anzeigen()

    def auswahl(self):
        if self.wurzel is None or self.ausstehend or self.fehler:
            return ()
        selected = (list((p, nur, z) for (p, nur), z in self.markiert.items())
                    if self.hat_unterordner else [(self.wurzel, False, self.standard.get())])
        return tuple(Auswahl(self.kennung, self.wurzel, p, nur, z, p.relative_to(self.wurzel))
                     for p, nur, z in selected)

    def anzeigen(self):
        for node, (p, nur) in self.knoten.items():
            parent = self.uebergeordnet(p, nur)
            own = self.markiert.get((p, nur))
            target = parent or own or (self.standard.get() if not self.hat_unterordner else "")
            mark = "[+]" if parent else ("[x]" if target else "[ ]")
            self.baum.item(node, text="%s %s" % (mark, "(Dateien in diesem Ordner)" if nur else p.name),
                           values=(target,))
        if self.fehler:
            text = "Quelle nicht lesbar: " + self.fehler
        elif self.ausstehend:
            text = "Quelle wird eingelesen …"
        elif self.wurzel is None:
            text = "Optional: keine Quelle gewählt."
        elif not self.hat_unterordner:
            text = "Keine Unterordner: gesamte Quelle wird übernommen."
        else:
            text = ("%s Auswahl(en). Ordner enthalten alle Nachkommen; "
                    "Ziel einer markierten Zeile anklicken zum Ändern." % len(self.markiert))
        self.info.configure(text=text, foreground="darkorange" if self.fehler else "gray")
        self.app.knopf()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Stellwerksprojekt – Anlegen und Datenpflege")
        breite = min(1000, self.winfo_screenwidth() - 80)
        hoehe = min(850, self.winfo_screenheight() - 100)
        self.geometry("%sx%s" % (breite, hoehe))
        self.minsize(min(760, breite), min(550, hoehe))
        self.q = queue.Queue()
        self.aktiv = False
        self.abbruch = threading.Event()
        self.schliessen_ausstehend = False
        self.projekt = None
        self.daten = None
        self.projekt_ladend = False
        self.auto_beschreibung = ""
        self.auto_wert = {"PT1": "", "PT2": ""}
        self.angezeigter_modus = "neu"
        self.such_nr = {"PT1": 0, "PT2": 0, "BST": 0, "PROJEKT": 0}
        self.such_jobs = {}
        self.auswahlen = {}
        self.modus = tk.StringVar(value="neu")
        self.basis = tk.StringVar(value=STANDARD_BASIS)
        self.region = tk.StringVar(value="Ost")
        self.bst = tk.StringVar()
        self.klarname = tk.StringVar()
        self.az = tk.StringVar()
        self.psp = tk.StringVar()
        self.beschreibung = tk.StringVar()
        self.projekttext = tk.StringVar(value="Noch kein Projekt geöffnet.")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        canvas = tk.Canvas(self, highlightthickness=0)
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        canvas.configure(yscrollcommand=scrollbar.set)
        f = ttk.Frame(canvas, padding=12)
        f.columnconfigure(1, weight=1)
        window = canvas.create_window(0, 0, window=f, anchor="nw")
        f.bind("<Configure>", lambda _: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(window, width=e.width))
        row = 0
        modes = ttk.Frame(f)
        modes.grid(row=row, column=0, columnspan=3, sticky="w")
        self.neu_radio = ttk.Radiobutton(modes, text="Neues Projekt", variable=self.modus, value="neu",
                                        command=self.modus_wechseln)
        self.neu_radio.pack(side="left")
        self.pflege_radio = ttk.Radiobutton(
            modes, text="Bestehendes Projekt nachpflegen", variable=self.modus,
            value="pflege", command=self.modus_wechseln)
        self.pflege_radio.pack(side="left", padx=12)
        row += 1
        self.oeffnen_btn = ttk.Button(f, text="Projektordner öffnen …", command=self.projekt_waehlen)
        self.oeffnen_btn.grid(row=row, column=0, sticky="w", pady=6)
        ttk.Label(f, textvariable=self.projekttext, wraplength=650).grid(
            row=row, column=1, columnspan=2, sticky="w")
        row += 1
        self.neu_widgets = []
        fields = [
            ("Basisverzeichnis", self.basis), ("Region", self.region),
            ("Betriebsstelle / RIL100", self.bst), ("Klarname (neu/Ergänzung)", self.klarname),
            ("Anlagenzustand", self.az), ("PSP-Element", self.psp),
            ("Projektbeschreibung", self.beschreibung),
        ]
        for label, variable in fields:
            ttk.Label(f, text=label + ":").grid(row=row, column=0, sticky="w", pady=3)
            if variable is self.region:
                widget = ttk.Combobox(f, textvariable=variable, values=list(REGIONEN), state="readonly")
            elif variable is self.bst:
                widget = ttk.Combobox(f, textvariable=variable)
                self.bst_box = widget
            else:
                widget = ttk.Entry(f, textvariable=variable)
            widget.grid(row=row, column=1, sticky="ew", padx=6)
            self.neu_widgets.append(widget)
            if variable is self.basis:
                button = ttk.Button(f, text="Durchsuchen …", command=self.basis_waehlen)
                button.grid(row=row, column=2)
                self.neu_widgets.append(button)
            row += 1
        self.vorschau = ttk.Label(f, wraplength=900, foreground="gray")
        self.vorschau.grid(row=row, column=0, columnspan=3, sticky="w", pady=6)
        row += 1
        ttk.Label(f, text="Ordnerstruktur: %s" % STRUKTURDATEI, wraplength=650).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=4)
        ttk.Button(f, text="Struktur prüfen", command=self.struktur_pruefen).grid(row=row, column=2)
        row += 1
        for kennung in KOPIERBEREICHE:
            box = ttk.LabelFrame(f, text="%s-Unterlagen (optional)" % kennung, padding=6)
            box.grid(row=row, column=0, columnspan=3, sticky="ew", pady=5)
            box.columnconfigure(0, weight=1)
            selection = OrdnerAuswahl(box, self, kennung)
            selection.grid(sticky="ew")
            self.auswahlen[kennung] = selection
            row += 1
        self.balken = ttk.Progressbar(f)
        self.balken.grid(row=row, column=0, columnspan=3, sticky="ew", pady=5)
        row += 1
        self.status = ttk.Label(f, text="Bereit.", wraplength=900)
        self.status.grid(row=row, column=0, columnspan=3, sticky="w")
        row += 1
        self.abbruch_btn = ttk.Button(f, text="Abbrechen", state="disabled", command=self.abbrechen)
        self.abbruch_btn.grid(row=row, column=1, sticky="e", pady=10)
        self.btn = ttk.Button(f, text="Projekt anlegen", command=self.starten)
        self.btn.grid(row=row, column=2, pady=10)
        for variable in (self.basis, self.region):
            variable.trace_add("write", lambda *_: self.bst_planen())
        for variable in (self.basis, self.region, self.bst, self.klarname,
                         self.az, self.psp, self.beschreibung):
            variable.trace_add("write", lambda *_: self.vorschau_anzeigen())
        self.psp.trace_add("write", lambda *_: self.suche_planen("PT1"))
        for variable in (self.region, self.bst):
            variable.trace_add("write", lambda *_: self.suche_planen("PT2"))
        self.protocol("WM_DELETE_WINDOW", self.schliessen)
        self.after(80, self.abfragen)
        self.bst_planen()
        self.modus_wechseln()

    def struktur_pruefen(self):
        try:
            struktur = struktur_laden()
        except PflegeFehler as exc:
            messagebox.showerror("Ungültige Ordnerstruktur", str(exc))
        else:
            messagebox.showinfo(
                "Ordnerstruktur gültig", "%s\n\n%s Ordner erfolgreich geprüft. "
                "Die Datei wird vor jeder Projektneuanlage erneut eingelesen." % (
                    STRUKTURDATEI, len(struktur)))

    def hintergrund(self, funktion, fertig):
        def arbeit():
            try:
                result, error = funktion(), None
            except (OSError, PflegeFehler, Abbruch) as exc:
                result, error = None, exc
            except Exception:
                LOG.exception("Unerwarteter Programmfehler")
                result, error = None, PflegeFehler(
                    "Unerwarteter Programmfehler:\n" + traceback.format_exc())
            self.q.put(("antwort", fertig, result, error))

        threading.Thread(target=arbeit, daemon=True).start()

    def abfragen(self):
        try:
            for _ in range(100):
                item = self.q.get_nowait()
                if item[0] == "antwort":
                    _, callback, result, error = item
                    callback(result, error)
                elif item[0] == "fortschritt":
                    _, text, current, total = item
                    self.status.configure(text=text)
                    self.balken.configure(maximum=max(total, 1), value=current)
        except queue.Empty:
            pass
        self.after(80, self.abfragen)

    def report_callback_exception(self, exc, value, tb):
        text = "".join(traceback.format_exception(exc, value, tb))
        LOG.error(text)
        messagebox.showerror("Programmfehler", text)

    def modus_wechseln(self):
        if self.aktiv:
            return
        pflege = self.modus.get() == "pflege"
        if not pflege and self.projekt_ladend:
            self.such_nr["PROJEKT"] += 1
            self.projekt_ladend = False
            self.projekttext.set("Noch kein Projekt geöffnet.")
        if pflege and self.angezeigter_modus != "pflege" and self.daten:
            self.projektwerte_setzen(self.daten)
        self.angezeigter_modus = self.modus.get()
        for widget in self.neu_widgets:
            widget.configure(state=("disabled" if pflege else
                                    "readonly" if widget.cget("textvariable") == str(self.region)
                                    else "normal") if isinstance(widget, (ttk.Entry, ttk.Combobox))
                             else ("disabled" if pflege else "normal"))
        self.oeffnen_btn.configure(state="normal" if pflege else "disabled")
        self.vorschau_anzeigen()
        self.knopf()

    def basis_waehlen(self):
        p = filedialog.askdirectory(title="Basisverzeichnis wählen")
        if p:
            self.basis.set(p)

    def bst_planen(self):
        self.such_nr["BST"] += 1
        nr = self.such_nr["BST"]
        if "BST" in self.such_jobs:
            self.after_cancel(self.such_jobs.pop("BST"))
        basis, region = self.basis.get(), self.region.get()

        def starten():
            self.such_jobs.pop("BST", None)

            def fertig(result, error):
                if nr != self.such_nr["BST"]:
                    return
                if error:
                    self.status.configure(text="Betriebsstellen nicht lesbar: %s" % error)
                else:
                    self.bst_box.configure(values=result)

            self.hintergrund(lambda: betriebsstellen_auflisten(region_ordner(basis, region)), fertig)

        self.such_jobs["BST"] = self.after(500, starten)

    def suche_planen(self, kennung):
        self.such_nr[kennung] += 1
        nr = self.such_nr[kennung]
        if kennung in self.such_jobs:
            self.after_cancel(self.such_jobs.pop(kennung))
        psp, region, ril = self.psp.get().strip().upper(), self.region.get(), ril_aus_eingabe(self.bst.get())

        def starten():
            self.such_jobs.pop(kennung, None)
            selection = self.auswahlen[kennung]
            if ((kennung == "PT1" and not PSP_MUSTER.fullmatch(psp))
                    or (kennung == "PT2" and not RIL_MUSTER.fullmatch(ril))):
                self.auto_quelle_leeren(kennung)
                selection.suche_info.configure(
                    text="Automatische Suche benötigt gültige PSP bzw. Region/RIL100.",
                    foreground="gray")
                return
            selection.suche_info.configure(text="Automatische Suche läuft …", foreground="gray")

            def fertig(result, error):
                if nr != self.such_nr[kennung]:
                    return
                selection = self.auswahlen[kennung]
                if error:
                    self.auto_quelle_leeren(kennung)
                    selection.suche_info.configure(text="Automatische Suche: %s" % error,
                                                   foreground="darkorange")
                    return
                current = selection.quelle.get().strip()
                auto = self.auto_wert[kennung]
                if not current or (auto is not None and gleicher_pfad(current, auto)):
                    p = anzeige_pfad(result[0])
                    self.auto_wert[kennung] = p
                    selection.quelle.set(p)
                text = "Gefunden: %s" % anzeige_pfad(result[0])
                if len(result) > 1:
                    text += "\nWeitere Treffer: " + "; ".join(anzeige_pfad(p) for p in result[1:4])
                    if len(result) > 4:
                        text += " …"
                text += "\nManuelle Auswahl bleibt erhalten."
                selection.suche_info.configure(text=text, foreground="darkgreen")

            self.hintergrund(lambda: pt1_ordner_finden(psp) if kennung == "PT1"
                             else pt2_ordner_finden(region, ril), fertig)

        self.such_jobs[kennung] = self.after(500, starten)

    def auto_quelle_leeren(self, kennung):
        widget = self.auswahlen[kennung]
        auto = self.auto_wert[kennung]
        if auto and gleicher_pfad(widget.quelle.get().strip(), auto):
            widget.quelle.set("")
        self.auto_wert[kennung] = ""

    def beschreibung_vorschlagen(self, quelle):
        if self.modus.get() != "neu":
            return
        aktuell = self.beschreibung.get()
        if not aktuell or aktuell == self.auto_beschreibung:
            self.auto_beschreibung = beschreibung_aus_pt1(quelle) if quelle else ""
            self.beschreibung.set(self.auto_beschreibung)

    def vorschau_anzeigen(self):
        if self.modus.get() == "pflege":
            text = ("PT1- und PT2-Unterlagen werden direkt in die Projektstruktur kopiert. "
                    "Es wird keine lokale Standverwaltung angelegt.")
        else:
            name = bereinigen("%s_%s_%s" % (
                self.az.get().strip(), self.psp.get().strip().upper(), self.beschreibung.get().strip()))
            bst = self.bst.get().strip()
            if not hat_klarname(bst) and self.klarname.get().strip():
                bst = "%s - %s" % (ril_aus_eingabe(bst), self.klarname.get().strip())
            path = (Path(self.basis.get()) / REGIONEN.get(self.region.get(), self.region.get())
                    / bereinigen(bst, True) / name)
            length = len(bereinigen(self.beschreibung.get()))
            text = "Vorschau: %s\nBeschreibung: %s/40; Projektpfad: %s/120 Zeichen (Empfehlung)." % (
                path, length, len(str(path)))
        self.vorschau.configure(text=text)

    def projekt_waehlen(self):
        if self.aktiv:
            return
        p = filedialog.askdirectory(title="Vorhandenen Projektordner mit Projektinfo.txt wählen")
        if p:
            self.projekt_laden(langer_pfad(p))

    def projekt_laden(self, path, auswahl_leeren=True):
        self.such_nr["PROJEKT"] += 1
        nr = self.such_nr["PROJEKT"]
        self.projekt = None
        self.daten = None
        self.projekt_ladend = True
        self.knopf()
        self.projekttext.set("Projekt wird geprüft …")

        def fertig(result, error):
            if nr != self.such_nr["PROJEKT"]:
                return
            self.projekt_ladend = False
            if error:
                self.projekttext.set("Kein Projekt geöffnet.")
                messagebox.showerror("Projekt nicht lesbar", anzeige_pfad(str(error)))
                return
            self.projekt, self.daten = path, result
            self.projekttext.set(anzeige_pfad(path))
            if auswahl_leeren:
                for kennung, widget in self.auswahlen.items():
                    self.auto_wert[kennung] = ""
                    widget.quelle.set("")
            self.projektwerte_setzen(result)
            self.knopf()

        self.hintergrund(lambda: projekt_lesen(path), fertig)

    def projektwerte_setzen(self, daten):
        self.region.set(daten["region"])
        self.bst.set(daten["bst"])
        self.az.set(daten["az"])
        self.psp.set(daten["psp"])
        self.beschreibung.set(daten["beschreibung"])

    def knopf(self):
        if not hasattr(self, "btn"):
            return
        blocked = any(a.ausstehend or (a.quelle.get().strip() and not a.auswahl())
                      for a in self.auswahlen.values())
        disabled = self.aktiv or (self.modus.get() == "pflege" and not self.projekt) or blocked
        self.btn.configure(state="disabled" if disabled else "normal",
                           text="Unterlagen übernehmen" if self.modus.get() == "pflege"
                           else "Projekt anlegen")

    def starten(self):
        if self.aktiv:
            return
        pflege = self.modus.get() == "pflege"
        projekt = self.projekt if pflege else None
        auswahl = tuple(a for widget in self.auswahlen.values() for a in widget.auswahl())
        if any(w.quelle.get().strip() and not w.auswahl() for w in self.auswahlen.values()):
            messagebox.showwarning("Auswahl fehlt", "Quellen fertig laden und Ordner auswählen.")
            return
        if pflege and not projekt:
            messagebox.showwarning("Projekt fehlt", "Bitte zuerst ein bestehendes Projekt öffnen.")
            return
        if pflege and not auswahl:
            messagebox.showwarning("Quelle fehlt", "Mindestens PT1 oder PT2 auswählen.")
            return
        args = (self.basis.get().strip(), self.region.get(), self.bst.get().strip(),
                self.klarname.get().strip(), self.az.get().strip(),
                self.psp.get().strip().upper(), self.beschreibung.get().strip())
        if not pflege and (not args[0] or not RIL_MUSTER.fullmatch(ril_aus_eingabe(args[2]))
                           or not AZ_MUSTER.fullmatch(args[4]) or not PSP_MUSTER.fullmatch(args[5])
                           or not args[6]):
            messagebox.showerror("Ungültige Angaben", "Basis, RIL100, vierstelligen Anlagenzustand, "
                                 "PSP (z. B. M17525-01) und Beschreibung prüfen.")
            return
        # Alle Werte vor dem modalen Dialog aufnehmen; keine spaeteren Tk-Zugriffe im Worker.
        text = (("Unterlagen direkt in die Projektstruktur kopieren:\n" +
                 "\n".join("%s: %s -> %s%s" % (
                     a.kennung, anzeige_pfad(a.quelle), a.ziel,
                     " [nur Dateien]" if a.nur_dateien else "") for a in auswahl))
                if auswahl else "Nur Projektstruktur anlegen.\n")
        if not pflege:
            text += "\n\nNeuanlage: vorhandene gleichnamige Projekte werden nicht zusammengeführt."
            if args[3]:
                text += "\nEin Betriebsstellenordner ohne Klarname wird ggf. vervollständigt."
            if len(bereinigen(args[6])) > 40:
                text += "\nHinweis: Beschreibung überschreitet die Empfehlung von 40 Zeichen."
        if auswahl:
            text += ("\n\nEs wird keine lokale Standverwaltung angelegt. "
                     "Vorhandene Dateien werden nicht überschrieben; identische Dateien werden übersprungen.")
        text += "\n\nFortfahren?"
        if not messagebox.askyesno("Auftrag bestätigen", text):
            return
        if not pflege:
            self.projekt, self.daten = None, None
        self.aktiv = True
        self.abbruch.clear()
        self.abbruch_btn.configure(state="normal")
        self.oeffnen_btn.configure(state="disabled")
        self.neu_radio.configure(state="disabled")
        self.pflege_radio.configure(state="disabled")
        self.status.configure(text="Auftrag wird vorbereitet …")
        self.knopf()
        last = [0.0]

        def melden(text, current, total):
            now = time.monotonic()
            if now - last[0] >= 0.1 or (total and current == total):
                last[0] = now
                self.q.put(("fortschritt", text, current, total))

        def arbeit():
            ziel = projekt
            if self.abbruch.is_set():
                raise Abbruch()
            if ziel is None:
                ziel = projekt_anlegen(*args)
                self.q.put(("antwort", self.projekt_erstellt, ziel, None))
            ergebnis = unterlagen_kopieren(ziel, auswahl, self.abbruch, melden) if auswahl else None
            return ziel, ergebnis

        self.hintergrund(arbeit, self.fertig)

    def projekt_erstellt(self, projekt, error):
        self.projekt = projekt
        self.daten = None
        self.projekttext.set(anzeige_pfad(projekt))
        self.modus.set("pflege")

    def fertig(self, result, error):
        self.aktiv = False
        self.abbruch_btn.configure(state="disabled")
        self.neu_radio.configure(state="normal")
        self.pflege_radio.configure(state="normal")
        self.modus_wechseln()
        self.knopf()
        if self.schliessen_ausstehend:
            self.destroy()
            return
        if error:
            text = ("Abgebrochen. Bereits übernommene Dateien bleiben im Projekt; "
                    "identische Dateien werden beim erneuten Start übersprungen."
                    if isinstance(error, Abbruch) else anzeige_pfad(str(error)))
            if self.projekt:
                text += "\nProjekt bleibt erhalten: %s" % anzeige_pfad(self.projekt)
            self.status.configure(text=text)
            messagebox.showwarning("Abgebrochen" if isinstance(error, Abbruch) else "Fehler", text)
        else:
            projekt, ergebnis = result
            self.projekt = projekt
            self.modus.set("pflege")
            self.modus_wechseln()
            text = ("Projekt angelegt: " if not ergebnis else "Unterlagen übernommen: ")
            text += anzeige_pfad(projekt)
            if ergebnis:
                text += ("\nKopiert: %s; bereits identisch vorhanden: %s; Fehler: %s" % (
                    ergebnis["kopiert"], ergebnis["bereits_vorhanden"], len(ergebnis["fehler"])))
                if ergebnis["fehler"]:
                    text += "\n\nFehler:\n" + "\n".join(ergebnis["fehler"])
                if ergebnis["hinweise"]:
                    text += "\n\nHinweise: %s Verknüpfungen/temporäre Dateien ausgelassen." % (
                        len(ergebnis["hinweise"]))
            self.status.configure(text=text)
            dialog = messagebox.showwarning if ergebnis and ergebnis["fehler"] else messagebox.showinfo
            dialog("Ergebnis", text)
        if self.projekt:
            self.projekt_laden(self.projekt, auswahl_leeren=False)

    def abbrechen(self):
        if self.aktiv and messagebox.askyesno(
                "Abbrechen?", "Nach der laufenden Datei/Prüfsumme abbrechen? "
                "Bereits kopierte Dateien bleiben im Projekt."):
            self.abbruch.set()
            self.abbruch_btn.configure(state="disabled")
            self.status.configure(text="Abbruch angefordert – laufende Datei wird abgeschlossen …")

    def schliessen(self):
        if not self.aktiv:
            self.destroy()
        elif self.schliessen_ausstehend:
            if messagebox.askyesno("Sofort beenden?",
                                  "Datei kann noch geschrieben werden. Sofort beenden?\n"
                                  "Die Sperrdatei muss dann ggf. manuell entfernt werden."):
                self.destroy()
        elif messagebox.askyesno("Abbrechen und schließen?",
                                 "Nach der laufenden Datei abbrechen und dann schließen?"):
            self.schliessen_ausstehend = True
            self.abbruch.set()
            self.abbruch_btn.configure(state="disabled")

    def destroy(self):
        for job in self.tk.call("after", "info"):
            self.tk.call("after", "cancel", job)
        super().destroy()


if __name__ == "__main__":
    App().mainloop()