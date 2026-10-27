"""Standardbibliothek-Tests; Logik und GUI-Steuerung auch ohne installierte Tk-Bindung."""
import importlib.util
import os
from pathlib import Path
import queue
import shutil
import sys
import threading
import types
import unittest
from unittest.mock import Mock, patch
from tempfile import TemporaryDirectory


TK_ERSATZ = False
try:
    import tkinter
except ImportError:
    TK_ERSATZ = True
    # Nur die Basisklassen werden für den Import gebraucht; keine echte GUI vortäuschen.
    tkinter = types.ModuleType("tkinter")
    tkinter.Tk = type("Tk", (), {})
    tkinter.ttk = types.ModuleType("tkinter.ttk")
    tkinter.ttk.Frame = type("Frame", (), {})
    tkinter.filedialog = types.ModuleType("tkinter.filedialog")
    tkinter.messagebox = types.ModuleType("tkinter.messagebox")
    for name in ("showerror", "showwarning", "showinfo", "askyesno"):
        setattr(tkinter.messagebox, name, Mock())
    sys.modules["tkinter"] = tkinter
    sys.modules["tkinter.ttk"] = tkinter.ttk
    sys.modules["tkinter.filedialog"] = tkinter.filedialog
    sys.modules["tkinter.messagebox"] = tkinter.messagebox

SPEZIFIKATION = importlib.util.spec_from_file_location(
    "stw_pruefstruktur_testmodul", Path(__file__).parents[1] / "stw_pruefstruktur.py")
stw = importlib.util.module_from_spec(SPEZIFIKATION)
SPEZIFIKATION.loader.exec_module(stw)
if TK_ERSATZ:
    for name in ("tkinter", "tkinter.ttk", "tkinter.filedialog", "tkinter.messagebox"):
        sys.modules.pop(name, None)


class Wert:
    def __init__(self, wert=""):
        self.wert = wert
        self.hauptthread = threading.get_ident()

    def get(self):
        if threading.get_ident() != self.hauptthread:
            raise AssertionError("Tk-Variable im Hintergrund gelesen")
        return self.wert

    def set(self, wert):
        self.wert = wert


class Anzeige(dict):
    def config(self, **werte):
        self.update(werte)

    def cget(self, name):
        return self.get(name, "")


class Baum:
    def __init__(self):
        self.eintraege = {}
        self.zaehler = 0

    def insert(self, eltern, _position, **werte):
        self.zaehler += 1
        knoten = str(self.zaehler)
        self.eintraege[knoten] = {"eltern": eltern, **werte}
        return knoten

    def get_children(self, eltern=""):
        return tuple(k for k, v in self.eintraege.items() if v["eltern"] == eltern)

    def delete(self, *knoten):
        for knotenname in knoten:
            self.delete(*self.get_children(knotenname))
            self.eintraege.pop(knotenname, None)

    def exists(self, knoten):
        return knoten in self.eintraege

    def item(self, knoten, **werte):
        self.eintraege[knoten].update(werte)
        return self.eintraege[knoten]


def steuerung(klasse, **attribute):
    objekt = types.SimpleNamespace(**attribute)
    for name, funktion in vars(klasse).items():
        if isinstance(funktion, staticmethod):
            setattr(objekt, name, funktion.__func__)
            continue
        if callable(funktion) and not name.startswith("__") and not hasattr(objekt, name):
            setattr(objekt, name, types.MethodType(funktion, objekt))
    return objekt


def auswahl(wurzel):
    return steuerung(
        stw.OrdnerAuswahl, kennung="PT1", quelle=Wert(str(wurzel)), standardziel=Wert("Stellwerk"),
        q=queue.Queue(), generation=1, job=None, ausstehend=False, fehler=None,
        wurzel=wurzel, quellwert="", hat_unterordner=True, knoten={}, markiert={},
        geladen=set(), ladend=set(), baum=Baum(), info=Anzeige(),
        geaendert=Mock(), after=Mock(return_value="job"), after_cancel=Mock())


class DateienTest(unittest.TestCase):
    def setUp(self):
        # Bewusst im Repository, niemals im systemweiten temporären Verzeichnis.
        self.verzeichnis = TemporaryDirectory(prefix=".stw-test-", dir=Path.cwd())
        self.addCleanup(self.verzeichnis.cleanup)
        self.wurzel = Path(self.verzeichnis.name)
        self.quelle = self.wurzel / "quelle"
        self.ziel = self.wurzel / "ziel"
        self.quelle.mkdir()

    def kopieren(self, nur=False, ereignis=None):
        kanal = queue.Queue()
        stw.ordner_kopieren([("PT1", self.quelle, self.ziel, nur)], kanal, ereignis)
        meldungen = []
        while not kanal.empty():
            meldungen.append(kanal.get_nowait())
        self.assertEqual(meldungen[0], ("start", "PT1"))
        self.assertEqual(meldungen[-1][0], "fertig")
        return meldungen[-1][1][0], meldungen

    def test_atomare_kopie_und_metadaten(self):
        quelle = self.quelle / "a"
        quelle.write_text("vollständig", encoding="utf-8")
        os.utime(quelle, (1234567890, 1234567890))
        stw.datei_kopieren(quelle, self.wurzel / "a")
        self.assertEqual((self.wurzel / "a").read_text(encoding="utf-8"), "vollständig")
        self.assertEqual(int((self.wurzel / "a").stat().st_mtime), 1234567890)
        self.assertFalse((self.wurzel / "a.part").exists())

    def test_kopierfehler_entfernt_unvollstaendige_datei(self):
        ziel = self.wurzel / "a"

        def fehler(_quelle, teil):
            Path(teil).write_text("unvollständig")
            raise OSError("Netzwerk getrennt")

        with patch.object(stw.shutil, "copy2", side_effect=fehler):
            with self.assertRaisesRegex(OSError, "Netzwerk"):
                stw.datei_kopieren(self.quelle / "a", ziel)
        self.assertFalse(ziel.exists())
        self.assertFalse(ziel.with_name("a.part").exists())

    def test_replace_fehler_entfernt_part(self):
        (self.quelle / "a").write_text("a")
        with patch.object(Path, "replace", side_effect=OSError("gesperrt")):
            with self.assertRaisesRegex(OSError, "gesperrt"):
                stw.datei_kopieren(self.quelle / "a", self.wurzel / "a")
        self.assertFalse((self.wurzel / "a.part").exists())

    def test_cleanup_fehler_verdeckt_nicht_den_originalfehler(self):
        originalfehler = OSError("Originalfehler beim Kopieren")
        with patch.object(stw.shutil, "copy2", side_effect=originalfehler), \
                patch.object(Path, "unlink", side_effect=OSError("Cleanup fehlgeschlagen")):
            with self.assertRaises(OSError) as abgefangen:
                stw.datei_kopieren(self.quelle / "a", self.wurzel / "a")
        self.assertIs(abgefangen.exception, originalfehler)

    def test_part_ordner_wird_nicht_als_temporaere_datei_missbraucht(self):
        (self.quelle / "a").write_text("a")
        teilordner = self.wurzel / "a.part"
        teilordner.mkdir()
        (teilordner / "erhalten").write_text("Daten")
        with self.assertRaisesRegex(OSError, "Ordner"):
            stw.datei_kopieren(self.quelle / "a", self.wurzel / "a")
        self.assertEqual((teilordner / "erhalten").read_text(), "Daten")
        self.assertFalse((self.wurzel / "a").exists())
        self.assertFalse((teilordner / "a").exists())

    def test_waehrend_kopie_entstandenes_ziel_bleibt_erhalten(self):
        quelle = self.quelle / "a"
        ziel = self.wurzel / "a"
        quelle.write_text("Quelle")
        original = shutil.copy2

        def gleichzeitig(src, dst):
            original(src, dst)
            ziel.write_text("anderer Prozess")

        with patch.object(stw.shutil, "copy2", side_effect=gleichzeitig):
            self.assertFalse(stw.datei_kopieren(quelle, ziel))
        self.assertEqual(ziel.read_text(), "anderer Prozess")
        self.assertFalse((self.wurzel / "a.part").exists())

    def test_ein_walk_keine_ueberschreibung_part_dateien_ignorieren(self):
        (self.quelle / "a").write_text("neu")
        (self.quelle / "b").write_text("b")
        (self.quelle / "rest.PART").write_text("nicht kopieren")
        (self.quelle / "teil.part").mkdir()
        (self.quelle / "teil.part" / "versteckt").write_text("Unterordnerdaten")
        (self.quelle / "leer").mkdir()
        self.ziel.mkdir()
        (self.ziel / "a").write_text("alt")
        with patch.object(stw.os, "walk", wraps=os.walk) as laufen:
            ergebnis, meldungen = self.kopieren()
        self.assertEqual(laufen.call_count, 1)
        self.assertEqual(ergebnis[1:], (2, 1, [], None))
        self.assertEqual((self.ziel / "a").read_text(), "alt")
        self.assertTrue((self.ziel / "leer").is_dir())
        self.assertFalse((self.ziel / "rest.PART").exists())
        self.assertEqual((self.ziel / "teil.part" / "versteckt").read_text(), "Unterordnerdaten")
        self.assertIn(("max", 3), meldungen)

    def test_nur_dateien_und_leere_quelle(self):
        (self.quelle / "a").write_text("a")
        (self.quelle / "unter").mkdir()
        (self.quelle / "unter" / "b").write_text("b")
        ergebnis, _ = self.kopieren(nur=True)
        self.assertEqual(ergebnis[1], 1)
        self.assertFalse((self.ziel / "unter").exists())
        shutil.rmtree(self.ziel)
        shutil.rmtree(self.quelle)
        self.quelle.mkdir()
        ergebnis, _ = self.kopieren()
        self.assertEqual(ergebnis[1:4], (0, 0, []))
        self.assertTrue(self.ziel.is_dir())

    def test_walk_fehler_wird_gemeldet(self):
        def laufen(_pfad, onerror):
            onerror(PermissionError(13, "kein Zugriff", r"\\?\UNC\server\ablage"))
            return iter(())

        with patch.object(stw.os, "walk", side_effect=laufen):
            ergebnis, _ = self.kopieren()
        self.assertIn("kein Zugriff", ergebnis[3][0])
        self.assertIn(repr(r"\\server\ablage"), ergebnis[3][0])
        self.assertNotIn(repr(stw.LANG_UNC_PRAEFIX)[1:-1], ergebnis[3][0])

    def test_einzelfehler_setzt_weitere_dateien_fort(self):
        for name in ("a", "b"):
            (self.quelle / name).write_text(name)
        original = stw.datei_kopieren

        def kopieren(src, dst):
            if src.name == "a":
                raise OSError("gesperrt")
            original(src, dst)

        with patch.object(stw, "datei_kopieren", side_effect=kopieren):
            ergebnis, _ = self.kopieren()
        self.assertEqual(ergebnis[1], 1)
        self.assertEqual(len(ergebnis[3]), 1)

    def test_abbruch_nach_laufender_datei_und_folgeauftraege(self):
        for name in ("a", "b", "c"):
            (self.quelle / name).write_text(name)
        ereignis = threading.Event()
        original = stw.datei_kopieren

        def kopieren(src, dst):
            original(src, dst)
            ereignis.set()

        kanal = queue.Queue()
        with patch.object(stw, "datei_kopieren", side_effect=kopieren):
            stw.ordner_kopieren(
                [("PT1", self.quelle, self.ziel, False),
                 ("PT2", self.quelle, self.wurzel / "ziel2", False)], kanal, ereignis)
        meldungen = []
        while not kanal.empty():
            meldungen.append(kanal.get())
        ergebnisse = meldungen[-1][1]
        self.assertEqual([e[1] for e in ergebnisse], [1, 0])
        self.assertTrue(all(e[4] for e in ergebnisse))
        self.assertEqual(len(list(self.ziel.iterdir())), 1)
        self.assertFalse((self.wurzel / "ziel2").exists())

    def test_abbruch_vor_start(self):
        (self.quelle / "a").write_text("a")
        ereignis = threading.Event()
        ereignis.set()
        with patch.object(stw.os, "walk", side_effect=AssertionError("Laufwerkszugriff")), \
                patch.object(stw, "langer_pfad", side_effect=AssertionError("OS-Pfadgrenze")):
            ergebnis, _ = self.kopieren(ereignis=ereignis)
        self.assertEqual(ergebnis[1], 0)
        self.assertTrue(ergebnis[4])
        self.assertEqual(ergebnis[3], [])
        self.assertFalse(self.ziel.exists())

    def test_ordnerinhalt_sortierung_part_und_dateien(self):
        for name in ("z", "A", "b", "rest.part"):
            (self.quelle / name).mkdir()
        (self.quelle / "a.txt").write_text("a")
        (self.quelle / "angefangen.PART").write_text("ignorieren")
        ordner, dateien = stw.ordner_inhalt(self.quelle)
        self.assertEqual([p.name for p in ordner], ["A", "b", "rest.part", "z"])
        self.assertTrue(dateien)
        with self.assertRaises(OSError):
            stw.ordner_inhalt(self.wurzel / "fehlt")

    def test_zyklische_ordnerverknuepfung_wird_nicht_betreten(self):
        unter = self.quelle / "unter"
        unter.mkdir()
        (unter / "a").write_text("a")
        try:
            (unter / "zurueck").symlink_to(self.quelle, target_is_directory=True)
        except OSError as e:
            self.skipTest(f"Ordnerverknüpfungen nicht verfügbar: {e}")
        self.assertEqual(stw.ordner_inhalt(unter), ([], True))
        ergebnis, _ = self.kopieren()
        self.assertEqual(ergebnis[1:4], (1, 0, []))
        self.assertFalse((self.ziel / "unter" / "zurueck").exists())

    def test_junction_markierung_und_keine_rekursion(self):
        for tag in (0xA0000003, 0xA000000C):
            status = types.SimpleNamespace(
                st_mode=stw.stat.S_IFDIR, st_file_attributes=0x400, st_reparse_tag=tag)
            with self.subTest(tag=tag), patch.object(stw.os, "lstat", return_value=status):
                self.assertTrue(stw.ordner_verknuepfung(self.quelle))
        junction = self.quelle / "junction"
        junction.mkdir()
        (junction / "nicht_kopieren").write_text("a")
        with patch.object(stw, "ordner_verknuepfung",
                          side_effect=lambda pfad: Path(pfad).name == "junction"):
            self.assertEqual(stw.ordner_inhalt(self.quelle), ([], False))
            ergebnis, _ = self.kopieren()
        self.assertEqual(ergebnis[1:4], (0, 0, []))
        self.assertFalse((self.ziel / "junction").exists())

    def test_cloud_reparse_ordner_bleiben_im_baum_und_werden_kopiert(self):
        cloud, junction = self.quelle / "cloud", self.quelle / "junction"
        cloud.mkdir()
        junction.mkdir()
        (cloud / "Dokument").write_text("Cloud-Daten")
        (junction / "nicht_kopieren").write_text("Verknüpfungsdaten")
        original = os.lstat

        def status(pfad, *argumente, **schluessel):
            wert = original(pfad, *argumente, **schluessel)
            tag = 0x9000001A if Path(pfad) == cloud else (
                0xA0000003 if Path(pfad) == junction else None)
            if tag is not None:
                return types.SimpleNamespace(
                    st_mode=wert.st_mode, st_file_attributes=0x400, st_reparse_tag=tag)
            return wert

        with patch.object(stw.os, "lstat", side_effect=status):
            self.assertFalse(stw.ordner_verknuepfung(cloud))
            self.assertTrue(stw.ordner_verknuepfung(junction))
            self.assertEqual(stw.ordner_inhalt(self.quelle), ([cloud], False))
            ergebnis, _ = self.kopieren()
        self.assertEqual(ergebnis[1:4], (1, 0, []))
        self.assertEqual((self.ziel / "cloud" / "Dokument").read_text(), "Cloud-Daten")
        self.assertFalse((self.ziel / "junction").exists())

    def test_betriebsstelle_neu_vorhanden_und_rename(self):
        (self.quelle / "BLN").mkdir()
        karte = {stw.anzeige_name("BLN"): "BLN"}
        ergebnis = stw.betriebsstelle_pruefen(self.quelle, "BLN", "BLN", "Lübbenau", karte)
        self.assertEqual(ergebnis, (self.quelle / "BLN", True, self.quelle / "BLN - Lübbenau"))
        (self.quelle / "BLN - Lübbenau").mkdir()
        ergebnis = stw.betriebsstelle_pruefen(self.quelle, "BLN", "BLN", "", {})
        self.assertEqual(ergebnis, (self.quelle / "BLN - Lübbenau", True, None))
        self.assertEqual(stw.betriebsstelle_pruefen(self.quelle, "AB", "AB", "", {}),
                         (None, False, None))
        self.assertEqual(stw.betriebsstelle_pruefen(self.quelle, "AB - Ort", "AB", "", {}),
                         (self.quelle / "AB - Ort", False, None))

    def test_pt1_suffix_fallback_und_unterordner(self):
        gruppe = self.quelle / "M19xxx"
        projekt = gruppe / "M19061-01 Projekt"
        unter = projekt / stw.PT1_UNTERORDNER
        unter.mkdir(parents=True)
        einstellung = (stw.KOPIERBEREICHE["PT1"][0], ["Stellwerk"], str(self.quelle))
        with patch.dict(stw.KOPIERBEREICHE, PT1=einstellung):
            treffer, fehler = stw.pt1_ordner_finden("m19061-01a")
            self.assertEqual((treffer, fehler), ([unter], None))
            exakt = gruppe / "M19061-01A Zusatz"
            exakt.mkdir()
            self.assertEqual(stw.pt1_ordner_finden("M19061-01A")[0], [exakt])
        self.assertEqual(stw.zielname(unter), projekt.name)
        self.assertEqual(stw.beschreibung_aus_pt1(unter), "Projekt")

    def test_pt2_prioritaet(self):
        region = self.quelle / "OST"
        region.mkdir()
        for name in ("BLNX", "BLN1", "BLN0", "BLN0_alt", "AND0"):
            (region / name).mkdir()
        with patch.object(stw, "pt2_regionsordner", return_value=region):
            treffer, fehler = stw.pt2_ordner_finden("Ost", "BLN F")
        self.assertIsNone(fehler)
        self.assertEqual([p.name for p in treffer], ["BLN0", "BLNX", "BLN0_alt", "BLN1"])


class NamenTest(unittest.TestCase):
    def test_vorgegebene_bst_snippets_und_benannte_ril_gruppe(self):
        self.assertEqual(stw.BST_MIT_KLARNAME.pattern,
                         r'^(?P<ril>[A-ZÄÖÜ][A-ZÄÖÜ0-9 ]{1,4}?)\s*-\s*\S')
        self.assertEqual(stw.BST_NUR_RIL.pattern, r'^[A-ZÄÖÜ][A-ZÄÖÜ0-9 ]{1,4}$')
        treffer = stw.BST_MIT_KLARNAME.match("BLN F - Klarname")
        self.assertEqual(treffer.group("ril"), "BLN F")
        self.assertTrue(stw.hat_klarname("  BLN - Ort mit Zusatz  "))
        self.assertTrue(stw.hat_klarname("BLN - Ort\nZusatz"))
        self.assertEqual(stw._AUSSCHLUSS, {x.casefold() for x in stw.KEINE_BETRIEBSSTELLE})

    def test_vorgegebene_pt1_und_windows_namen(self):
        self.assertEqual(stw.PT1_PSP_PRAEFIX.pattern,
                         r'^[A-Z]\d{5}-\d{2}[A-Z]?[\s_\-]*')
        self.assertTrue(stw.PT1_PSP_PRAEFIX.flags & stw.re.IGNORECASE)
        self.assertEqual(stw.beschreibung_aus_pt1("M19061-01AProjekt__"), "Projekt")
        self.assertEqual(stw.beschreibung_aus_pt1("__Projekt__"), "Projekt")
        self.assertEqual(stw._windows_name("CON.txt."), "_CON.txt")
        self.assertEqual(stw.LANG_UNC_PRAEFIX, "\\\\?\\UNC\\")

    def test_strikte_betriebsstellen(self):
        for name in ("BL", "BLN", "BLN F", "AB123", "BLN - Lübbenau",
                     " BLN", "BLN ", " BLN - Lübbenau "):
            with self.subTest(name=name):
                self.assertTrue(stw.ist_betriebsstelle(name))
        for name in ("B", "bln", "BLn - Ort", "A12345", "123",
                     "BLN - ", "BLN_F"):
            with self.subTest(name=name):
                self.assertFalse(stw.ist_betriebsstelle(name))
        for name in stw.KEINE_BETRIEBSSTELLE:
            self.assertFalse(stw.ist_betriebsstelle(name))
            self.assertFalse(stw.ist_betriebsstelle(name + " - Ort"))
            self.assertFalse(stw.hat_klarname(name + " - Ort"))
            self.assertFalse(stw.ist_betriebsstelle(name.lower()))
            self.assertFalse(stw.ist_betriebsstelle(f" {name} - Ort "))

    def test_windows_bereinigung(self):
        for name in ("CON", "con.txt", "PRN", "AUX.log", "NUL",
                     *(f"COM{i}.txt" for i in range(10)),
                     *(f"LPT{i}" for i in range(10))):
            with self.subTest(name=name):
                self.assertTrue(stw.bereinigen_mit_leerzeichen(name).startswith("_"))
        self.assertEqual(stw.bereinigen_mit_leerzeichen(" Name.  "), "Name")
        self.assertEqual(stw.bereinigen_mit_leerzeichen('A\x00B\x1fC?D'), "A_B_C_D")
        self.assertEqual(stw.bereinigen("A B. "), "A_B")
        self.assertEqual(stw.bereinigen("..."), "_")
        self.assertEqual(stw.bereinigen("COM10"), "COM10")

    def test_anzeige_und_ril_eingabe(self):
        self.assertEqual(stw.anzeige_name("BLN"), "BLN" + stw.OHNE_KLARNAME)
        self.assertEqual(stw.anzeige_name("BLN - Ort"), "BLN - Ort")
        for text in ("bln", "BLN" + stw.OHNE_KLARNAME, "BLN - Ort",
                     "BLN (Klarname fehlt)", "BLN(Klarname fehlt)"):
            self.assertEqual(stw.ril_aus_eingabe(text), "BLN")
        self.assertEqual(stw.ril_aus_eingabe("Eintrag", {"Eintrag": "BLN - Ort"}), "BLN")

    def test_lange_windows_pfade_und_anzeige(self):
        ersatz_os = types.SimpleNamespace(name="nt", fspath=os.fspath)
        with patch.object(stw, "os", ersatz_os):
            for pfad, erwartet in (
                    (r"C:\Projekte\ABC", r"\\?\C:\Projekte\ABC"),
                    (r"\\server\freigabe\ABC", r"\\?\UNC\server\freigabe\ABC"),
                    (r"\\?\C:\ABC", r"\\?\C:\ABC")):
                self.assertEqual(str(stw.langer_pfad(pfad)), erwartet)
                self.assertEqual(stw.anzeige_pfad(erwartet),
                                 pfad if not pfad.startswith(stw.LANG_PRAEFIX) else r"C:\ABC")
        if os.name == "nt":
            self.assertTrue(str(stw.langer_pfad(Path("relativ"))).startswith(stw.LANG_PRAEFIX))
        else:
            self.assertEqual(stw.langer_pfad(Path("relativ")), Path("relativ"))

    def test_fehleranzeige_entfernt_auch_escaped_windows_praefixe(self):
        for pfad, ohne_praefix in (
                (r"\\?\C:\Projekte\Datei", r"C:\Projekte\Datei"),
                (r"\\?\UNC\server\ablage\Datei", r"\\server\ablage\Datei")):
            with self.subTest(pfad=pfad):
                self.assertEqual(stw.anzeige_pfad(f"Fehler: {pfad}"), f"Fehler: {ohne_praefix}")
                fehler = PermissionError(13, "Kein Zugriff", pfad)
                erwartet = PermissionError(13, "Kein Zugriff", ohne_praefix)
                self.assertEqual(stw.anzeige_pfad(str(fehler)), str(erwartet))

    def test_beschreibung_und_psp_gross(self):
        for name in ("M19061-01A Projekt", "m19061-01_Projekt", "M19061-01-Projekt",
                     "M19061-01AProjekt__", "M19061-01__Projekt__",
                     "M19061-01A -_ Projekt _-"):
            self.assertEqual(stw.beschreibung_aus_pt1(name), "Projekt")
        app = steuerung(stw.App, az=Wert("0180"), psp=Wert("m19061-01a"), beschr=Wert("Projekt"))
        self.assertEqual(app.projektordnername(), "0180_M19061-01A_Projekt")
        self.assertIn(Path("01_Eingangsunterlagen", "PT2", "Stellwerk"),
                      stw.vorlage_parsen(stw.VORLAGE))


class AuswahlTest(unittest.TestCase):
    def setUp(self):
        self.wurzel = Path("quelle")
        self.auswahl = auswahl(self.wurzel)

    def einfuegen(self, pfad, nur=False, eltern=""):
        knoten = self.auswahl.baum.insert(eltern, "end")
        self.auswahl.knoten[knoten] = (pfad, nur)
        return knoten

    def test_eltern_sperren_nachkommen_und_loeschen_explizite_auswahl(self):
        eltern = self.einfuegen(self.wurzel / "a")
        kind = self.einfuegen(self.wurzel / "a" / "b", eltern=eltern)
        dateien = self.einfuegen(self.wurzel / "a", True, eltern)
        self.auswahl.umschalten(kind)
        self.assertEqual(len(self.auswahl.markiert), 1)
        self.auswahl.umschalten(eltern)
        self.assertEqual(self.auswahl.auswahl(),
                         [(self.wurzel / "a", False, "Stellwerk", Path("a"))])
        self.assertIn("▣", self.auswahl.baum.item(kind)["text"])
        self.assertIn("(übergeordnet)", self.auswahl.baum.item(dateien)["text"])
        self.auswahl.umschalten(kind)
        self.auswahl.umschalten(dateien)
        self.assertEqual(len(self.auswahl.markiert), 1)
        self.auswahl.umschalten(eltern)
        self.assertEqual(self.auswahl.auswahl(), [])

    def test_dateien_sind_nicht_rekursiv_und_zielwechsel(self):
        dateien = self.einfuegen(self.wurzel, True)
        ordner = self.einfuegen(self.wurzel / "a")
        self.auswahl.umschalten(dateien)
        self.auswahl.umschalten(ordner)
        self.auswahl.ziel_setzen((self.wurzel, True), "ZX")
        self.assertIn((self.wurzel, True, "ZX", Path(".")), self.auswahl.auswahl())
        self.assertEqual(len(self.auswahl.auswahl()), 2)
        self.assertIn("[nur Dateien]", self.auswahl.info["text"])
        self.auswahl.keine()
        self.assertEqual(self.auswahl.auswahl(), [])
        self.auswahl.alle()
        self.assertEqual(len(self.auswahl.auswahl()), 2)

    def test_elternauswahl_loescht_verborgene_nachkommen_ohne_dateisystemzugriff(self):
        eltern = self.einfuegen(self.wurzel / "a")
        self.auswahl.markiert[(self.wurzel / "a" / "verborgen" / "tief", False)] = "ZX"
        with patch.object(stw, "ordner_inhalt", side_effect=AssertionError("Vollscan")), \
                patch.object(stw.os, "walk", side_effect=AssertionError("Vollscan")):
            self.auswahl.umschalten(eltern)
        self.assertEqual(self.auswahl.auswahl(),
                         [(self.wurzel / "a", False, "Stellwerk", Path("a"))])

    def test_keine_unterordner_und_leere_quelle_implizit(self):
        self.auswahl.hat_unterordner = False
        self.assertEqual(self.auswahl.auswahl(),
                         [(self.wurzel, False, "Stellwerk", Path("."))])
        self.auswahl.standardziel.set("ZX")
        self.assertEqual(self.auswahl.auswahl()[0][2], "ZX")
        self.auswahl.fehler = "nicht lesbar"
        self.assertEqual(self.auswahl.auswahl(), [])
        self.auswahl.fehler = None
        self.auswahl.ausstehend = True
        self.assertEqual(self.auswahl.auswahl(), [])

    def test_veraltete_baumergebnisse_ignorieren_und_lazytiefe(self):
        self.auswahl.ausstehend = True
        self.auswahl.q.put((0, "", Path("alt"), [Path("alt/a")], True, None))
        self.auswahl.abfragen()
        self.assertTrue(self.auswahl.ausstehend)
        self.assertEqual(self.auswahl.knoten, {})
        self.auswahl.q.put((1, "", self.wurzel, [self.wurzel / "a"], True, None))
        self.auswahl.abfragen()
        self.assertFalse(self.auswahl.ausstehend)
        self.assertTrue(self.auswahl.hat_unterordner)
        ordner = next(k for k, (_, nur) in self.auswahl.knoten.items() if not nur)
        self.assertEqual(self.auswahl.baum.item(
            self.auswahl.baum.get_children(ordner)[0])["text"], "…")
        pfad = self.wurzel / "a"
        for tiefe in range(15):
            kind = pfad / str(tiefe)
            self.auswahl.q.put((1, ordner, pfad, [kind], True, None))
            self.auswahl.abfragen()
            ordner = next(k for k, wert in self.auswahl.knoten.items() if wert == (kind, False))
            pfad = kind
        self.assertEqual(len(pfad.parts), 17)

    def test_wurzelplanen_debounce_sperre_generation(self):
        self.auswahl.job = "vorher"
        self.auswahl.wurzel_planen()
        self.auswahl.after_cancel.assert_called_once_with("vorher")
        self.assertEqual(self.auswahl.generation, 2)
        self.assertTrue(self.auswahl.ausstehend)
        self.assertEqual(self.auswahl.after.call_args.args[0], 400)
        self.auswahl.geaendert.assert_called_once()

    def test_gleiche_quelle_behaelt_auswahl_ausser_explizitem_neuladen(self):
        self.auswahl.quellwert = str(self.wurzel)
        self.auswahl.markiert[(self.wurzel / "teil", False)] = "ZX"
        generation = self.auswahl.generation
        self.auswahl.quelle.set(str(self.wurzel / "."))
        self.auswahl.wurzel_planen()
        self.assertEqual(self.auswahl.generation, generation)
        self.assertFalse(self.auswahl.ausstehend)
        self.auswahl.after.assert_not_called()
        self.assertEqual(self.auswahl.markiert, {(self.wurzel / "teil", False): "ZX"})
        self.auswahl.wurzel_planen(neu_laden=True)
        self.assertEqual(self.auswahl.generation, generation + 1)
        self.assertTrue(self.auswahl.ausstehend)

    def test_ladefehler_aus_hintergrund_gesammelt(self):
        with patch.object(stw, "ordner_inhalt", side_effect=OSError("verweigert")):
            self.auswahl.laden("", self.wurzel)
            ergebnis = self.auswahl.q.get(timeout=5)
        self.auswahl.q.put(ergebnis)
        self.auswahl.abfragen()
        self.assertIn("verweigert", self.auswahl.fehler)
        self.assertEqual(self.auswahl.auswahl(), [])


class AppTest(unittest.TestCase):
    def app(self, **werte):
        attribute = dict(
            basis=Wert("basis"), region=Wert("Ost"), bst=Wert("BLN"), klarname=Wert("Ort"),
            psp=Wert("m19061-01a"), az=Wert("0180"), beschr=Wert("Projekt"),
            bst_nr=1, basis_job=None, vorschau_job=None, bst_q=queue.Queue(), bst_map={},
            such_job={"PT1": None, "PT2": None}, such_nr={"PT1": 0, "PT2": 0},
            such_q=queue.Queue(),
            bst_ergebnis=(None, False, None),
            bst_region=Path("basis/OST"), bst_fehler=None, liste_ausstehend=False,
            bst_box=Anzeige(), bst_status=Anzeige(), klar_entry=Anzeige(), vorschau=Anzeige(),
            beschr_hinweis=Anzeige(), laengen_hinweis=Anzeige(), auto_beschr="",
            after=Mock(return_value="job"), after_cancel=Mock(),
            auswahlen={}, quellen={"PT1": Wert(), "PT2": Wert()},
            auswahl_meldung="", kopier_thread=None, abbruch=threading.Event(),
            abbruch_btn=Anzeige(), btn=Anzeige(), status=Anzeige(), balken=Anzeige(maximum=1),
            q=queue.Queue(), schliessen_ausstehend=False, destroy=Mock(), wurzel=Path("projekt"))
        attribute.update(werte)
        return steuerung(stw.App, **attribute)

    def test_vorschau_und_liste_ohne_dateisystem(self):
        app = self.app(
            bst_ergebnis=(Path("basis/OST/BLN - Ort"), True, None),
            bst_map={"BLN - Ort": "BLN - Ort"})
        with patch.object(stw, "betriebsstelle_pruefen", side_effect=AssertionError("I/O")), \
                patch.object(stw, "region_ordner", side_effect=AssertionError("I/O")), \
                patch.object(Path, "is_dir", side_effect=AssertionError("I/O")), \
                patch.object(Path, "iterdir", side_effect=AssertionError("I/O")):
            app.vorschau_aktualisieren()
            app.projekt_vorschau()
            app.bst_anzeigen()
            app.liste_filtern()
        self.assertIn("M19061-01A", app.vorschau["text"])
        self.assertEqual(app.bst_box["values"], ["BLN - Ort"])
        app.beschr.set("X" * 41)
        app.vorschau_aktualisieren()
        self.assertEqual(app.laengen_hinweis["foreground"], "darkorange")

    def test_benannte_debounces_sind_getrennt_und_invalidieren_sofort(self):
        self.assertEqual(stw.VERZOEGERUNG_SUCHE, 500)
        self.assertEqual(stw.VERZOEGERUNG_BASIS, 500)
        self.assertEqual(stw.VERZOEGERUNG_VORSCHAU, 400)
        self.assertIs(stw.App.bst_pruefen.__annotations__["liste"], bool)
        app = self.app(bst_anzeigen=Mock())
        nr = app.bst_nr
        app.basis_geaendert()
        self.assertGreater(app.bst_nr, nr)
        self.assertTrue(app.liste_ausstehend)
        self.assertEqual(app.after.call_args.args[0], 500)
        aufrufe = app.after.call_count
        app.vorschau_planen()
        self.assertEqual(app.after.call_count, aufrufe)
        app.basis_job = None
        app.vorschau_planen()
        self.assertEqual(app.after.call_args.args[0], 400)

    def test_beschreibungslaenge_ist_bereinigt(self):
        app = self.app(beschr=Wert("CON"))
        app.projekt_vorschau()
        self.assertIn("Beschreibung: 4/40", app.laengen_hinweis["text"])
        app.beschr.set("X" * 39 + "...")
        app.projekt_vorschau()
        self.assertIn("Beschreibung: 39/40", app.laengen_hinweis["text"])
        self.assertEqual(app.laengen_hinweis["foreground"], "gray")

    def test_bst_snapshot_hintergrund_stale_und_reload_erhalten(self):
        app = self.app(liste_ausstehend=True)
        with patch.object(stw, "region_ordner", return_value=Path("basis/OST")), \
                patch.object(stw, "betriebsstellen_auflisten", return_value=["BLN - Ort"]), \
                patch.object(stw, "betriebsstelle_pruefen",
                             return_value=(Path("basis/OST/BLN - Ort"), True, None)):
            app.bst_starten()
            ergebnis = app.bst_q.get(timeout=5)
        self.assertIsNone(ergebnis[-1])
        app.bst_nr = ergebnis[0] + 1
        app.bst_q.put(ergebnis)
        app.bst_abfragen()
        self.assertTrue(app.liste_ausstehend)
        self.assertEqual(app.bst_map, {})
        app.bst_q.put((app.bst_nr, *ergebnis[1:]))
        app.bst_abfragen()
        self.assertFalse(app.liste_ausstehend)
        self.assertEqual(app.bst_map, {"BLN - Ort": "BLN - Ort"})
        self.assertTrue(app.bst_ergebnis[1])
        self.assertEqual(app.such_nr["PT2"], 1)

    def test_suche_ausnahme_und_veraltete_ergebnisse(self):
        app = self.app(such_job={"PT1": None}, such_nr={"PT1": 0}, such_q=queue.Queue(),
                       such_auftrag=Mock(return_value=(Mock(side_effect=RuntimeError("Suche kaputt")),
                                                      "Suche")),
                       hinweise={"PT1": Anzeige()}, such_ergebnis=Mock())
        app.suchen("PT1")
        ergebnis = app.such_q.get(timeout=5)
        self.assertEqual(ergebnis[3], "Suche kaputt")
        app.such_nr["PT1"] += 1
        app.such_q.put(ergebnis)
        app.such_abfragen()
        app.such_ergebnis.assert_not_called()
        app.such_q.put(("PT1", app.such_nr["PT1"], [], "Fehler"))
        app.such_abfragen()
        app.such_ergebnis.assert_called_once_with("PT1", [], "Fehler")

    def test_gleiches_suchergebnis_setzt_quelle_nicht_erneut(self):
        quelle = Wert("./quelle")
        app = self.app(
            quellen={"PT2": quelle}, auto_wert={"PT2": "./quelle"},
            hinweise={"PT2": Anzeige()})
        with patch.object(quelle, "set", wraps=quelle.set) as setzen:
            app.such_ergebnis("PT2", [Path("quelle")], None)
            app.such_ergebnis("PT2", [Path("quelle")], None)
        setzen.assert_not_called()
        self.assertEqual(app.auto_wert["PT2"], "quelle")

    def test_beschreibung_auto_manuell_leeren(self):
        app = self.app(beschr=Wert(), quellen={"PT1": Wert("M19061-01A Projekt")})
        app.beschreibung_aktualisieren()
        self.assertEqual(app.beschr.get(), "Projekt")
        app.quellen["PT1"].set("M19061-01 Anderes Projekt")
        app.beschreibung_aktualisieren()
        self.assertEqual(app.beschr.get(), "Anderes Projekt")
        app.beschr.set("Eigener Text")
        app.quellen["PT1"].set("M19061-01 Neu")
        app.beschreibung_aktualisieren()
        self.assertEqual(app.beschr.get(), "Eigener Text")
        self.assertEqual(app.beschr_hinweis["foreground"], "#1f5fbf")
        app.quellen["PT1"].set("")
        app.beschreibung_aktualisieren()
        self.assertEqual(app.beschr.get(), "Eigener Text")
        app.beschr.set("")
        app.quellen["PT1"].set("M19061-01 Auto")
        app.beschreibung_aktualisieren()
        app.quellen["PT1"].set("")
        app.beschreibung_aktualisieren()
        self.assertEqual(app.beschr.get(), "")

    def test_beschreibung_vergleicht_exakt_und_behaelt_letzten_auto_wert(self):
        app = self.app(beschr=Wert(), quellen={"PT1": Wert("M19061-01A Vorschlag")})
        app.beschreibung_aktualisieren()
        app.beschr.set(" Vorschlag ")
        app.quellen["PT1"].set("M19061-01A Neuer Vorschlag")
        app.beschreibung_aktualisieren()
        self.assertEqual(app.beschr.get(), " Vorschlag ")
        self.assertEqual(app.auto_beschr, "Vorschlag")
        self.assertEqual(app.beschr_hinweis["foreground"], "#1f5fbf")
        app.beschr.set("Vorschlag")
        app.beschreibung_aktualisieren()
        self.assertEqual(app.beschr.get(), "Neuer Vorschlag")
        self.assertEqual(app.auto_beschr, "Neuer Vorschlag")
        app.quellen["PT1"].set("")
        app.beschreibung_aktualisieren()
        self.assertEqual(app.beschr.get(), "")

    def test_anlegen_guard_waehrend_quellenladen(self):
        app = self.app(auswahlen={"PT1": types.SimpleNamespace(ausstehend=True)})
        with patch.object(stw.messagebox, "showwarning") as warnung:
            app.knopf_aktualisieren()
            app.anlegen()
        self.assertEqual(app.btn["state"], "disabled")
        warnung.assert_called_once()

    def test_knopf_sperrt_fehlende_auswahl_fehler_und_zeigt_genaue_meldung(self):
        auswahlbaum = auswahl(Path("quelle"))
        app = self.app(auswahlen={"PT1": auswahlbaum}, quellen={"PT1": Wert("quelle")})
        app.knopf_aktualisieren()
        self.assertEqual(app.btn["state"], "disabled")
        self.assertEqual(app.status["text"],
                         "Bitte in PT1 mindestens einen Ordner anhaken (oder Quellordner leeren).")
        auswahlbaum.markiert[(Path("quelle/teil"), False)] = "ZX"
        app.knopf_aktualisieren()
        self.assertEqual(app.btn["state"], "normal")
        self.assertEqual(app.status["text"], "Bereit.")
        auswahlbaum.fehler = "Quelle nicht lesbar: verweigert"
        app.knopf_aktualisieren()
        self.assertEqual(app.btn["state"], "disabled")
        self.assertEqual(app.status["text"],
                         "Bitte in PT1 mindestens einen Ordner anhaken (oder Quellordner leeren).")
        auswahlbaum.ausstehend = True
        app.knopf_aktualisieren()
        self.assertEqual(app.status["text"],
                         "Bitte in PT1 mindestens einen Ordner anhaken (oder Quellordner leeren).")
        app.kopier_thread = object()
        app.status.config(text="Abbruch angefordert")
        app.knopf_aktualisieren()
        self.assertEqual(app.status["text"], "Abbruch angefordert")

    def test_pflicht_nach_geladenen_quellen_nennt_alle_betroffenen_bereiche(self):
        auswahl_pt1, auswahl_pt2 = auswahl(Path("pt1")), auswahl(Path("pt2"))
        app = self.app(
            auswahlen={"PT1": auswahl_pt1, "PT2": auswahl_pt2},
            quellen={"PT1": Wert("pt1"), "PT2": Wert("pt2")})
        self.assertFalse(auswahl_pt1.ausstehend)
        self.assertFalse(auswahl_pt2.ausstehend)
        self.assertEqual(app.auswahl_offen(), ["PT1", "PT2"])
        app.knopf_aktualisieren()
        self.assertEqual(app.btn["state"], "disabled")
        self.assertEqual(app.status["text"],
                         "Bitte in PT1, PT2 mindestens einen Ordner anhaken "
                         "(oder Quellordner leeren).")
        with patch.object(stw.messagebox, "showwarning") as warnung:
            app.anlegen()
        self.assertEqual(warnung.call_args.args[0], "Auswahl fehlt")
        auswahl_pt1.markiert[(Path("pt1/teil"), False)] = "ZX"
        app.knopf_aktualisieren()
        self.assertEqual(app.auswahl_offen(), ["PT2"])
        self.assertEqual(app.status["text"],
                         "Bitte in PT2 mindestens einen Ordner anhaken (oder Quellordner leeren).")

    def test_abbruchknopf_fragt_vor_event_setzen(self):
        app = self.app(kopier_thread=object())
        with patch.object(stw.messagebox, "askyesno", return_value=False) as frage:
            app.kopieren_abbrechen()
        frage.assert_called_once()
        self.assertFalse(app.abbruch.is_set())
        with patch.object(stw.messagebox, "askyesno", return_value=True) as frage:
            app.kopieren_abbrechen()
        frage.assert_called_once()
        self.assertTrue(app.abbruch.is_set())

    def test_kopierende_waehrend_rueckfrage_wird_beruecksichtigt(self):
        app = self.app(kopier_thread=object())

        def fertig(*_):
            app.kopier_thread = None
            return True

        with patch.object(stw.messagebox, "askyesno", side_effect=fertig):
            app.kopieren_abbrechen()
        self.assertFalse(app.abbruch.is_set())
        app.kopier_thread = object()
        with patch.object(stw.messagebox, "askyesno", side_effect=fertig):
            app.schliessen()
        app.destroy.assert_called_once()

    def test_abbruchstatus_wird_nicht_ueberschrieben(self):
        app = self.app(kopier_thread=object())
        app.kopieren_abbrechen(rueckfrage=False)
        status = app.status["text"]
        app.q.put(("start", "PT1"))
        app.q.put(("max", 2))
        app.q.put(("fortschritt", 1, "PT1", "Datei"))
        app.abfragen()
        self.assertEqual(app.status["text"], status)
        self.assertTrue(app.abbruch.is_set())
        self.assertEqual(app.abbruch_btn["state"], "disabled")

    def test_fertig_warnung_logfehler_fallback_und_reset(self):
        app = self.app(kopier_thread=object(), knopf_aktualisieren=Mock())
        fehler = [f"Fehler {i}" for i in range(12)]
        with patch.object(Path, "write_text", side_effect=OSError("kein Platz")), \
                patch.object(stw.messagebox, "showwarning") as warnung:
            app.kopier_fertig([("PT1", 1, 2, fehler, None)])
        self.assertIsNone(app.kopier_thread)
        app.knopf_aktualisieren.assert_called_once()
        text = warnung.call_args.args[1]
        self.assertIn("kein Platz", text)
        self.assertIn("Fehler 9", text)
        self.assertNotIn("Fehler 10", text)

    def test_abbruch_protokoll_fortsetzen_und_schliessen_ohne_dialog(self):
        with TemporaryDirectory(prefix=".stw-test-", dir=Path.cwd()) as verzeichnis:
            app = self.app(kopier_thread=object(), wurzel=Path(verzeichnis),
                           schliessen_ausstehend=True)
            with patch.object(stw.messagebox, "showwarning") as warnung, \
                    patch.object(stw.messagebox, "showinfo") as info:
                app.kopier_fertig([("PT1", 2, 1, [], "Benutzerabbruch")])
            protokoll = (Path(verzeichnis) / "Kopierfehler.txt").read_text(encoding="utf-8")
        self.assertIn("2 Dateien", protokoll)
        self.assertIn("Fortsetzen", protokoll)
        self.assertIn(".part", protokoll)
        app.destroy.assert_called_once()
        warnung.assert_not_called()
        info.assert_not_called()

    def test_schliessen_bestaetigen_zweites_mal_force(self):
        app = self.app(kopier_thread=object())
        with patch.object(stw.messagebox, "askyesno", return_value=True) as frage:
            app.schliessen()
            self.assertTrue(app.schliessen_ausstehend)
            self.assertTrue(app.abbruch.is_set())
            app.destroy.assert_not_called()
            app.schliessen()
        self.assertEqual(frage.call_count, 2)
        app.destroy.assert_called_once()

    def test_anlegen_frisch_pruefen_oberes_psp_und_auswahlziel(self):
        with TemporaryDirectory(prefix=".stw-test-", dir=Path.cwd()) as verzeichnis:
            basis = Path(verzeichnis)
            quelle = basis / "quelle"
            (quelle / "teil").mkdir(parents=True)
            bst = basis / "OST" / "BLN - Ort"
            auswahl_pt1 = auswahl(quelle)
            auswahl_pt1.markiert[(quelle / "teil", False)] = "ZX"
            app = self.app(
                basis=Wert(str(basis)), bst_ergebnis=(None, False, None),
                auswahlen={"PT1": auswahl_pt1}, quellen={"PT1": Wert(str(quelle)), "PT2": Wert()},
                unterziele={"PT1": Wert("Stellwerk"), "PT2": Wert("Stellwerk")},
                liste_aktualisieren=Mock())
            with patch.object(stw, "betriebsstelle_pruefen",
                              return_value=(bst, False, None)) as pruefung, \
                    patch.object(stw.messagebox, "askyesno", return_value=True), \
                    patch.object(stw.threading, "Thread") as thread:
                app.anlegen()
            pruefung.assert_called_once()
            info = app.wurzel / "Projektinfo.txt"
            self.assertIn("M19061-01A", info.read_text(encoding="utf-8"))
            auftraege = thread.call_args.kwargs["args"][0]
            self.assertEqual(auftraege[0][0], "PT1/ZX/teil")
            self.assertEqual(auftraege[0][2],
                             app.wurzel / "01_Eingangsunterlagen/PT1/ZX/quelle/teil")
            self.assertFalse(auftraege[0][3])
            self.assertEqual(app.btn["state"], "disabled")
            self.assertEqual(app.abbruch_btn["state"], "normal")

    def test_projektinfo_haengt_neue_auswahl_an_ohne_original_zu_ersetzen(self):
        with TemporaryDirectory(prefix=".stw-test-", dir=Path.cwd()) as verzeichnis:
            basis = Path(verzeichnis)
            quelle = basis / "quelle"
            (quelle / "teil").mkdir(parents=True)
            (quelle / "stammdatei").write_text("a")
            bst = basis / "OST" / "BLN - Ort"
            auswahl_pt1 = auswahl(quelle)
            auswahl_pt1.markiert[(quelle / "teil", False)] = "ZX"
            app = self.app(
                basis=Wert(str(basis)), auswahlen={"PT1": auswahl_pt1},
                quellen={"PT1": Wert(str(quelle)), "PT2": Wert()},
                liste_aktualisieren=Mock())
            with patch.object(stw, "betriebsstelle_pruefen", return_value=(bst, False, None)), \
                    patch.object(stw.messagebox, "askyesno", return_value=True), \
                    patch.object(stw.threading, "Thread"):
                app.anlegen()
            info = app.wurzel / "Projektinfo.txt"
            original = info.read_bytes()
            self.assertIn("PT1/ZX/teil", original.decode("utf-8"))
            app.kopier_thread = None
            auswahl_pt1.markiert = {(quelle, True): "sonstiges"}
            with patch.object(stw, "betriebsstelle_pruefen", return_value=(bst, True, None)), \
                    patch.object(stw.messagebox, "askyesno", return_value=True), \
                    patch.object(stw.threading, "Thread") as thread:
                app.anlegen()
            ergaenzt = info.read_bytes()
            self.assertTrue(ergaenzt.startswith(original))
            self.assertIn("PT1/sonstiges/. (Dateien)", ergaenzt.decode("utf-8"))
            self.assertEqual(thread.call_args.kwargs["args"][0][0][0],
                             "PT1/sonstiges/. (Dateien)")

    def test_kompletter_plan_bleibt_bei_aenderungen_im_bestaetigungsdialog_fest(self):
        with TemporaryDirectory(prefix=".stw-test-", dir=Path.cwd()) as verzeichnis:
            basis = Path(verzeichnis)
            quelle, andere = basis / "genehmigte_quelle", basis / "andere_quelle"
            (quelle / "teil").mkdir(parents=True)
            (andere / "nicht_genehmigt").mkdir(parents=True)
            bst = basis / "OST" / "BLN - Ort"
            auswahl_pt1 = auswahl(quelle)
            auswahl_pt1.markiert[(quelle / "teil", False)] = "ZX"
            app = self.app(
                basis=Wert(str(basis)), auswahlen={"PT1": auswahl_pt1},
                quellen={"PT1": Wert(str(quelle)), "PT2": Wert()},
                liste_aktualisieren=Mock())
            genehmigter_name = app.projektordnername()

            def bestaetigen(*_):
                app.az.set("9999")
                app.psp.set("M99999-99")
                app.beschr.set("Nicht genehmigt")
                app.region.set("West")
                app.basis.set(str(basis / "anderer_ort"))
                app.quellen["PT1"].set(str(andere))
                app.auswahlen["PT1"] = auswahl(andere)
                return True

            with patch.object(stw, "betriebsstelle_pruefen", return_value=(bst, False, None)), \
                    patch.object(stw.messagebox, "askyesno", side_effect=bestaetigen), \
                    patch.object(stw.threading, "Thread") as thread:
                app.anlegen()
            self.assertEqual(app.wurzel, bst / genehmigter_name)
            auftraege = thread.call_args.kwargs["args"][0]
            self.assertIsInstance(auftraege, tuple)
            self.assertEqual(auftraege, (
                ("PT1/ZX/teil", quelle / "teil",
                 app.wurzel / "01_Eingangsunterlagen" / "PT1" / "ZX" / quelle.name / "teil",
                 False),))
            info = (app.wurzel / "Projektinfo.txt").read_text(encoding="utf-8")
            self.assertIn("Projektbeschreibung: Projekt", info)
            self.assertIn("Anlagenzustand:      0180", info)
            self.assertNotIn("Nicht genehmigt", info)
            self.assertNotIn(str(andere), info)


if __name__ == "__main__":
    unittest.main()
