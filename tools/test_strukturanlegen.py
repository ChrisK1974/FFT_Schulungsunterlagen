import json
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import Strukturanlegen as tool

TEST_STRUKTUR = (
    "Unterlagen\n"
    "  Planung [PT1]\n"
    "    Stellwerksdaten [PT1_STELLWERK]\n"
    "    Zuglenkung [PT1_ZX]\n"
    "    Weitere_Daten [PT1_SONSTIGES]\n"
    "  Projektierung [PT2]\n"
    "    Stellwerksdaten [PT2_STELLWERK]\n"
    "    Zuglenkung [PT2_ZX]\n"
)


class StrukturTests(unittest.TestCase):
    def test_hierarchie_kommentare_und_leerzeichen(self):
        struktur, kopierziele = tool.vorlage_parsen(
            "# Kommentar\n\n" + TEST_STRUKTUR)
        self.assertEqual(len(struktur), 8)
        self.assertNotIn(" [PT1]", "\n".join(p.as_posix() for p in struktur))
        self.assertEqual(kopierziele, {
            "PT1_STELLWERK": "Unterlagen/Planung/Stellwerksdaten",
            "PT1_ZX": "Unterlagen/Planung/Zuglenkung",
            "PT1_SONSTIGES": "Unterlagen/Planung/Weitere_Daten",
            "PT2_STELLWERK": "Unterlagen/Projektierung/Stellwerksdaten",
            "PT2_ZX": "Unterlagen/Projektierung/Zuglenkung",
        })

    def test_fehler_mit_zeilennummer(self):
        for zeile in (
            " Ordner", "    Ordner", "\tOrdner", "../Archiv", r"C:\Daten",
            "NUL", "con.txt", "Daten.", "Daten ", ".", "..", "Ordner?",
            "a" * 256, "Projektinfo.txt", ".projektpflege.json", ".stw-pflege.lock",
            "[PT1_ZX]",
        ):
            with self.subTest(zeile=zeile):
                with self.assertRaisesRegex(tool.PflegeFehler, "Zeile 1"):
                    tool.vorlage_parsen(zeile + "\n" + TEST_STRUKTUR)
        with self.assertRaisesRegex(tool.PflegeFehler, "Zeile 3.*doppelt"):
            tool.vorlage_parsen("Daten\n  Archiv\n  ARCHIV\n" + TEST_STRUKTUR)
        for text in ("", "# Nur Kommentare\n\n"):
            with self.subTest(text=text):
                with self.assertRaisesRegex(tool.PflegeFehler, "keine Ordner"):
                    tool.vorlage_parsen(text)

    def test_kopierkennungen_muessen_vollstaendig_eindeutig_und_bekannt_sein(self):
        examples = (
            (TEST_STRUKTUR.replace(" [PT1_ZX]", ""), "Fehlende PT-Kopierkennungen"),
            (TEST_STRUKTUR + "  Duplikat [PT1_ZX]\n", "Zeile .*doppelt"),
            (TEST_STRUKTUR.replace("[PT2_ZX]", "[PT2_FALSCH]"), "Unbekannte PT-Kopierkennung"),
            (TEST_STRUKTUR.replace("[PT1_STELLWERK]", "[PT1_STELLWERK] alt"),
             "PT-Kopierkennungen müssen am Ende"),
            ("Root\n"
             "  Beide [PT1_STELLWERK]\n"
             "    Unterordner [PT2_STELLWERK]\n"
             "  PT1_ZX [PT1_ZX]\n"
             "  PT1_Sonstiges [PT1_SONSTIGES]\n"
             "  PT2_ZX [PT2_ZX]\n", "Kopierziele .* überlappen"),
        )
        for text, expected in examples:
            with self.subTest(expected=expected):
                with self.assertRaisesRegex(tool.PflegeFehler, expected):
                    tool.vorlage_parsen(text)

    def test_fehlerhafte_datei_verhindert_jede_neuanlage(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            datei = root / "Ordnerstruktur.txt"
            for inhalt in (
                None, b"\xff", b"# leer\n",
                (TEST_STRUKTUR + "   Bruch\n").encode("utf-8"),
            ):
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
                datei.write_text(TEST_STRUKTUR, encoding="utf-8-sig")
                projekt = tool.projekt_anlegen(
                    root / "Projekte", "Ost", "BLN", "Test", "0180", "M17525-01", "Eins")
                first_map = {
                    "PT1_STELLWERK": "Unterlagen/Planung/Stellwerksdaten",
                    "PT1_ZX": "Unterlagen/Planung/Zuglenkung",
                    "PT1_SONSTIGES": "Unterlagen/Planung/Weitere_Daten",
                    "PT2_STELLWERK": "Unterlagen/Projektierung/Stellwerksdaten",
                    "PT2_ZX": "Unterlagen/Projektierung/Zuglenkung",
                }
                saved = json.loads((projekt / tool.META).read_text(encoding="utf-8"))
                self.assertEqual(saved["kopierziele"], first_map)
                self.assertTrue((projekt / first_map["PT1_STELLWERK"]).is_dir())
                revised = TEST_STRUKTUR.replace("Unterlagen", "Pruefakten").replace(
                    "Planung", "PT1_Dokumentation").replace(
                    "Projektierung", "PT2_Dokumentation")
                datei.write_text(revised, encoding="utf-8")
                zweites = tool.projekt_anlegen(
                    root / "Projekte", "Ost", "BLN", "", "0180", "M17525-01", "Zwei")
                self.assertTrue((zweites / "Pruefakten/PT1_Dokumentation/Stellwerksdaten").is_dir())
                self.assertEqual(
                    tool.projekt_lesen(zweites)["kopierziele"]["PT1_STELLWERK"],
                    "Pruefakten/PT1_Dokumentation/Stellwerksdaten")
                self.assertEqual(tool.projekt_lesen(projekt)["kopierziele"], first_map)
                self.assertTrue((projekt / first_map["PT1_STELLWERK"]).is_dir())
                source = root / "Server"
                source.mkdir()
                (source / "Plan.txt").write_text("Plan", encoding="utf-8")
                auswahl = [
                    tool.Auswahl(kennung, source, source, False, ziel, Path("."))
                    for kennung, (_, ziele, _) in tool.KOPIERBEREICHE.items()
                    for ziel in ziele
                ]
                result = tool.unterlagen_kopieren(
                    projekt, auswahl, threading.Event(), lambda *args: None)
                self.assertEqual(result["fehler"], [])
                self.assertEqual(result["kopiert"], len(first_map))
                for kopierkennung, zielpfad in first_map.items():
                    self.assertTrue((projekt / zielpfad / "Server/Plan.txt").is_file(),
                                    kopierkennung)

    def test_legacy_projects_keep_their_original_copy_locations(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            (project / "Projektinfo.txt").write_text(
                "Region: Ost\nBetriebsstelle: BLN\nAnlagenzustand: 0180\n"
                "PSP-Element: M17525-01\nProjektbeschreibung: Alt\n",
                encoding="utf-8")
            self.assertEqual(
                tool.projekt_lesen(project)["kopierziele"], tool.LEGACY_KOPIERZIELE)

    def test_invalid_saved_copy_destinations_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            metadata = {
                "version": 1, "region": "Ost", "bst": "BLN", "az": "0180",
                "psp": "M17525-01", "beschreibung": "Test",
                "kopierziele": dict(tool.LEGACY_KOPIERZIELE),
            }
            metadata["kopierziele"]["PT2_ZX"] = (
                metadata["kopierziele"]["PT1_ZX"] + "/Unterordner")
            (project / tool.META).write_text(json.dumps(metadata), encoding="utf-8")
            with self.assertRaisesRegex(tool.PflegeFehler, "überlappende PT-Kopierziele"):
                tool.projekt_lesen(project)

    def test_pruefknopf_meldet_erfolg_und_fehler(self):
        with patch.object(tool.messagebox, "showinfo") as info:
            tool.App.struktur_pruefen(SimpleNamespace())
            info.assert_called_once()
            self.assertIn("alle 5 PT-Kopierziele", info.call_args.args[1])
        with patch.object(tool, "struktur_laden", side_effect=tool.PflegeFehler("Zeile 4")):
            with patch.object(tool.messagebox, "showerror") as error:
                tool.App.struktur_pruefen(SimpleNamespace())
                error.assert_called_once_with("Ungültige Ordnerstruktur", "Zeile 4")


if __name__ == "__main__":
    unittest.main()
