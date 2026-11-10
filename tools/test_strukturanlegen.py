import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import Strukturanlegen as tool


class StrukturTests(unittest.TestCase):
    def test_hierarchie_kommentare_und_leerzeichen(self):
        self.assertEqual(
            tool.vorlage_parsen(
                "# Kommentar\n\nPruefung\n  Meine Unterlagen\n    Daten\n  Protokolle\nArchiv\n"),
            [Path("Pruefung"), Path("Pruefung/Meine Unterlagen"),
             Path("Pruefung/Meine Unterlagen/Daten"), Path("Pruefung/Protokolle"),
             Path("Archiv")],
        )

    def test_fehler_mit_zeilennummer(self):
        for zeile in (
            " Ordner", "    Ordner", "\tOrdner", "../Archiv", r"C:\Daten",
            "NUL", "con.txt", "Daten.", "Daten ", ".", "..", "Ordner?",
            "a" * 256, "Projektinfo.txt", ".projektpflege.json", ".stw-pflege.lock",
        ):
            with self.subTest(zeile=zeile):
                with self.assertRaisesRegex(tool.PflegeFehler, "Zeile 2"):
                    tool.vorlage_parsen("# Anleitung\n" + zeile)
        with self.assertRaisesRegex(tool.PflegeFehler, "Zeile 3.*doppelt"):
            tool.vorlage_parsen("Daten\n  Archiv\n  ARCHIV")
        for text in ("", "# Nur Kommentare\n\n"):
            with self.subTest(text=text):
                with self.assertRaisesRegex(tool.PflegeFehler, "keine Ordner"):
                    tool.vorlage_parsen(text)

    def test_fehlerhafte_datei_verhindert_jede_neuanlage(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            datei = root / "Ordnerstruktur.txt"
            for inhalt in (None, b"\xff", b"# leer\n", b"Daten\n   Archiv"):
                with self.subTest(inhalt=inhalt), patch.object(tool, "STRUKTURDATEI", datei):
                    if inhalt is not None:
                        datei.write_bytes(inhalt)
                    with self.assertRaises(tool.PflegeFehler) as error:
                        tool.projekt_anlegen(
                            root / "Projekte", "Ost", "BLN", "Test",
                            "0180", "M17525-01", "Projekt",
                        )
                    self.assertIn(str(datei), str(error.exception))
                    self.assertFalse((root / "Projekte").exists())

    def test_datei_wird_neu_eingelesen_und_kopierziele_bleiben_nutzbar(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            datei = root / "Ordnerstruktur.txt"
            with patch.object(tool, "STRUKTURDATEI", datei):
                datei.write_text("Meine Unterlagen\n  Archiv\n", encoding="utf-8-sig")
                projekt = tool.projekt_anlegen(
                    root / "Projekte", "Ost", "BLN", "Test", "0180", "M17525-01", "Eins")
                self.assertTrue((projekt / "Meine Unterlagen/Archiv").is_dir())
                datei.write_text("Andere Struktur\n", encoding="utf-8")
                zweites = tool.projekt_anlegen(
                    root / "Projekte", "Ost", "BLN", "", "0180", "M17525-01", "Zwei")
                self.assertTrue((zweites / "Andere Struktur").is_dir())
                self.assertFalse((zweites / "Meine Unterlagen").exists())
                self.assertTrue((projekt / "Meine Unterlagen/Archiv").is_dir())
                source = root / "Server"
                source.mkdir()
                (source / "Plan.txt").write_text("Plan", encoding="utf-8")
                auswahl = [tool.Auswahl(
                    "PT1", source, source, False, "Stellwerk", Path("."))]
                result = tool.unterlagen_kopieren(
                    projekt, auswahl, threading.Event(), lambda *args: None)
                self.assertEqual(result["fehler"], [])
                self.assertTrue((
                    projekt / "01_Eingangsunterlagen/PT1/Stellwerk/Server/Plan.txt").is_file())

    def test_pruefknopf_meldet_erfolg_und_fehler(self):
        with patch.object(tool.messagebox, "showinfo") as info:
            tool.App.struktur_pruefen(SimpleNamespace())
            info.assert_called_once()
        with patch.object(tool, "struktur_laden", side_effect=tool.PflegeFehler("Zeile 4")):
            with patch.object(tool.messagebox, "showerror") as error:
                tool.App.struktur_pruefen(SimpleNamespace())
                error.assert_called_once_with("Ungültige Ordnerstruktur", "Zeile 4")


if __name__ == "__main__":
    unittest.main()
