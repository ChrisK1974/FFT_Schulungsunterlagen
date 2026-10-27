"""Echte Tk-Integrationstests; ohne Tk/Display ausdrücklich übersprungen."""
import importlib.util
from pathlib import Path
import threading
import time
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch

try:
    import tkinter as tk
except ImportError as fehler:
    raise unittest.SkipTest(f"Tk-Bindung nicht vorhanden: {fehler}")

SPEZIFIKATION = importlib.util.spec_from_file_location(
    "stw_pruefstruktur_guimodul", Path(__file__).parents[1] / "stw_pruefstruktur.py")
stw = importlib.util.module_from_spec(SPEZIFIKATION)
SPEZIFIKATION.loader.exec_module(stw)


class OberflaecheTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            fenster = tk.Tk()
            fenster.destroy()
        except tk.TclError as fehler:
            raise unittest.SkipTest(f"Kein GUI-Bildschirm erreichbar: {fehler}")

    def setUp(self):
        self.verzeichnis = TemporaryDirectory(prefix=".stw-gui-test-", dir=Path.cwd())
        self.wurzel = Path(self.verzeichnis.name)
        self.basis = self.wurzel / "basis"
        self.bst = self.basis / "OST" / "BLN - Lübbenau"
        self.bst.mkdir(parents=True)
        self.pt1 = self.wurzel / "pt1"
        self.pt2 = self.wurzel / "pt2"
        self.pt1.mkdir()
        self.pt2.mkdir()
        self.patches = [
            patch.object(stw, "STANDARD_BASIS", str(self.basis)),
            patch.dict(stw.KOPIERBEREICHE, {
                "PT1": (stw.KOPIERBEREICHE["PT1"][0], ["Stellwerk", "ZX", "sonstiges"],
                        str(self.pt1)),
                "PT2": (stw.KOPIERBEREICHE["PT2"][0], ["Stellwerk", "ZX"], str(self.pt2)),
            }),
        ]
        for p in self.patches:
            p.start()
        self.meldungen = {}
        for name in ("showerror", "showwarning", "showinfo", "askyesno"):
            p = patch.object(stw.messagebox, name, return_value=True)
            self.patches.append(p)
            self.meldungen[name] = p.start()
        self.app = stw.App()
        self.geschlossen = False
        self.rueckruffehler = []
        self.app.report_callback_exception = lambda *fehler: self.rueckruffehler.append(fehler)
        self.app.bst.set("BLN")
        self.app.az.set("0180")
        self.app.psp.set("m19061-01a")
        self.app.beschr.set("Projekt")
        self.app.update()

    def tearDown(self):
        if not self.geschlossen:
            self.app.abbruch.set()
            if self.app.kopier_thread is not None:
                self.app.kopier_thread.join(timeout=6)
            for auftrag in self.app.tk.call("after", "info"):
                self.app.tk.call("after", "cancel", auftrag)
            self.app.destroy()
        for p in reversed(self.patches):
            p.stop()
        self.verzeichnis.cleanup()
        self.assertEqual(self.rueckruffehler, [], "Ausnahme in einem echten Tk-Rückruf")

    def warten(self, bedingung, zeit=6):
        ende = time.monotonic() + zeit
        while not bedingung():
            self.assertLess(time.monotonic(), ende, "GUI-Bedingung nicht rechtzeitig erfüllt")
            self.app.update()
            self.assertEqual(self.rueckruffehler, [])
            time.sleep(0.01)

    def quelle_setzen(self, quelle):
        self.app.quellen["PT1"].set(str(quelle))
        auswahl = self.app.auswahlen["PT1"]
        self.assertTrue(auswahl.ausstehend)
        self.assertTrue(self.app.auswahl_offen())
        self.assertEqual(str(self.app.btn.cget("state")), "disabled")
        self.warten(lambda: not auswahl.ausstehend)
        return auswahl

    def knoten(self, auswahl, pfad, nur=False):
        return next(k for k, wert in auswahl.knoten.items() if wert == (pfad, nur))

    def anklicken(self, auswahl, knoten, spalte="#0"):
        auswahl.baum.see(knoten)
        self.app.update()
        x, y, breite, hoehe = auswahl.baum.bbox(knoten, spalte)
        auswahl.baum.event_generate("<Button-1>", x=x + min(55, breite // 2),
                                    y=y + hoehe // 2)
        self.app.update()

    def oeffnen(self, auswahl, knoten):
        auswahl.baum.focus(knoten)
        auswahl.baum.item(knoten, open=True)
        auswahl.baum.event_generate("<<TreeviewOpen>>")
        self.warten(lambda: knoten in auswahl.geladen)

    def test_native_initialisierung_bst_und_bildschirmhoehe(self):
        self.warten(lambda: self.app.bst_ergebnis[0] is not None)
        self.assertEqual(self.app.bst_ergebnis, (self.bst, True, None))
        self.assertIn("BLN - Lübbenau", self.app.bst_box.cget("values"))
        self.assertLessEqual(self.app.winfo_height(), self.app.winfo_screenheight() - 100)
        self.assertEqual(int(self.app.auswahlen["PT1"].baum.cget("height")), 7)
        self.assertEqual(int(self.app.auswahlen["PT2"].baum.cget("height")), 7)
        beschriftungen = [w.cget("text") for w in self.app.auswahlen["PT1"].winfo_children()
                          if isinstance(w, stw.ttk.Label)]
        self.assertIn("Standardziel für neue Häkchen", beschriftungen)
        self.assertIn("M19061-01A", self.app.vorschau.cget("text"))
        self.assertEqual(str(self.app.abbruch_btn.cget("state")), "disabled")

    def test_native_bildlauf_macht_anlegen_und_abbrechen_erreichbar(self):
        flaeche = self.app.btn.master.master
        self.assertIsInstance(flaeche, tk.Canvas)
        bildlauf = next(w for w in flaeche.master.winfo_children()
                        if isinstance(w, stw.ttk.Scrollbar))
        self.assertTrue(bildlauf.winfo_ismapped())
        self.assertEqual(str(bildlauf.cget("orient")), "vertical")
        flaeche.yview_moveto(0)
        self.app.update()
        if self.app.btn.master.winfo_reqheight() > flaeche.winfo_height():
            self.assertLess(flaeche.yview()[1], 1)
            self.assertGreater(self.app.btn.winfo_rooty() + self.app.btn.winfo_height(),
                               flaeche.winfo_rooty() + flaeche.winfo_height())
        flaeche.yview_moveto(1)
        self.app.update()
        oben = flaeche.winfo_rooty()
        unten = oben + flaeche.winfo_height()
        for knopf in (self.app.btn, self.app.abbruch_btn):
            with self.subTest(knopf=knopf.cget("text"),
                              bildschirmhoehe=self.app.winfo_screenheight()):
                self.assertTrue(knopf.winfo_ismapped())
                self.assertGreaterEqual(knopf.winfo_rooty(), oben)
                self.assertLessEqual(knopf.winfo_rooty() + knopf.winfo_height(), unten)
        self.assertLessEqual(self.app.winfo_height(), self.app.winfo_screenheight() - 100)

    def test_native_auswahl_klick_menu_pflicht_und_beliebige_tiefe(self):
        quelle = self.wurzel / "quelle"
        pfad = quelle / "a"
        for nummer in range(12):
            pfad = pfad / str(nummer)
        pfad.mkdir(parents=True)
        (quelle / "datei").write_text("Wurzel")
        auswahl = self.quelle_setzen(quelle)
        self.assertEqual(str(self.app.btn.cget("state")), "disabled")
        self.assertEqual(self.app.status.cget("text"),
                         "Bitte in PT1 mindestens einen Ordner anhaken (oder Quellordner leeren).")
        self.app.anlegen()
        self.assertEqual(self.meldungen["showwarning"].call_args.args[0], "Auswahl fehlt")
        self.assertFalse((self.bst / self.app.projektordnername()).exists())
        ordner = self.knoten(auswahl, quelle / "a")
        self.anklicken(auswahl, ordner)
        self.assertEqual(len(auswahl.auswahl()), 1)
        self.oeffnen(auswahl, ordner)
        kind = self.knoten(auswahl, quelle / "a" / "0")
        self.assertIn("(übergeordnet)", auswahl.baum.item(kind, "text"))
        self.anklicken(auswahl, kind)
        self.assertEqual(len(auswahl.auswahl()), 1)
        self.anklicken(auswahl, ordner, "#1")
        menu = next(w for w in auswahl.winfo_children() if isinstance(w, tk.Menu))
        menu.invoke(1)
        menu.unpost()
        self.assertEqual(auswahl.auswahl()[0][2], "ZX")
        self.assertEqual(auswahl.baum.item(kind, "values"), ("ZX",))
        self.anklicken(auswahl, ordner)
        dateien = self.knoten(auswahl, quelle, True)
        self.anklicken(auswahl, dateien)
        self.assertEqual(auswahl.auswahl(), [(quelle, True, "Stellwerk", Path("."))])
        self.assertIn("[nur Dateien]", auswahl.info.cget("text"))
        auswahl.alle()
        self.assertEqual(len(auswahl.auswahl()), 2)
        auswahl.keine()
        self.assertEqual(auswahl.auswahl(), [])
        pfad = quelle / "a"
        for nummer in range(12):
            knoten = self.knoten(auswahl, pfad)
            self.oeffnen(auswahl, knoten)
            pfad = pfad / str(nummer)
        self.assertIn((pfad, False), auswahl.knoten.values())

    def test_native_root_debounce_veraltet_leer_und_unlesbar(self):
        alt, neu = self.wurzel / "alt", self.wurzel / "neu"
        (alt / "altordner").mkdir(parents=True)
        neu.mkdir()
        gestartet, freigabe = threading.Event(), threading.Event()
        original = stw.ordner_inhalt

        def einlesen(pfad):
            if pfad == alt:
                gestartet.set()
                if not freigabe.wait(5):
                    raise TimeoutError("Testfreigabe fehlt")
            return original(pfad)

        with patch.object(stw, "ordner_inhalt", side_effect=einlesen):
            self.app.quellen["PT1"].set(str(alt))
            self.warten(gestartet.is_set)
            self.app.quellen["PT1"].set(str(neu))
            self.app.anlegen()
            self.assertEqual(self.meldungen["showwarning"].call_args.args[0],
                             "Auswahl wird geladen")
            freigabe.set()
            auswahl = self.app.auswahlen["PT1"]
            self.warten(lambda: not auswahl.ausstehend)
        self.assertEqual(auswahl.wurzel, neu)
        self.assertEqual(auswahl.knoten, {})
        self.app.unterziele["PT1"].set("ZX")
        self.assertEqual(auswahl.auswahl(), [(neu, False, "ZX", Path("."))])
        with patch.object(stw, "ordner_inhalt", side_effect=OSError("nicht lesbar")):
            self.app.quellen["PT1"].set(str(neu))
            auswahl.wurzel_planen(neu_laden=True)
            self.warten(lambda: not auswahl.ausstehend)
        self.app.anlegen()
        self.assertEqual(self.meldungen["showwarning"].call_args.args[0], "Quelle nicht lesbar")
        self.assertFalse((self.bst / self.app.projektordnername()).exists())

    def test_native_pflicht_fuer_zwei_geladene_quellen_ohne_haken(self):
        for kennung in ("PT1", "PT2"):
            quelle = self.wurzel / kennung
            (quelle / "teil").mkdir(parents=True)
            self.app.quellen[kennung].set(str(quelle))
        self.warten(lambda: all(not a.ausstehend for a in self.app.auswahlen.values()))
        self.assertEqual(self.app.auswahl_offen(), ["PT1", "PT2"])
        self.assertEqual(str(self.app.btn.cget("state")), "disabled")
        self.assertEqual(self.app.status.cget("text"),
                         "Bitte in PT1, PT2 mindestens einen Ordner anhaken "
                         "(oder Quellordner leeren).")
        self.app.anlegen()
        self.assertEqual(self.meldungen["showwarning"].call_args.args[0], "Auswahl fehlt")
        self.app.auswahlen["PT1"].alle()
        self.assertEqual(self.app.auswahl_offen(), ["PT2"])
        self.assertEqual(str(self.app.btn.cget("state")), "disabled")
        self.app.auswahlen["PT2"].alle()
        self.assertFalse(self.app.auswahl_offen())
        self.assertEqual(str(self.app.btn.cget("state")), "normal")

    def test_native_gleiche_quelle_behaelt_haken_und_ziele_bis_explizitem_reload(self):
        quelle = self.wurzel / "quelle"
        (quelle / "teil").mkdir(parents=True)
        auswahl = self.quelle_setzen(quelle)
        self.anklicken(auswahl, self.knoten(auswahl, quelle / "teil"))
        auswahl.ziel_setzen((quelle / "teil", False), "ZX")
        generation, markiert = auswahl.generation, dict(auswahl.markiert)
        self.app.quellen["PT1"].set(f"{quelle}/.")
        self.assertFalse(auswahl.ausstehend)
        self.assertEqual(auswahl.generation, generation)
        self.assertEqual(auswahl.markiert, markiert)
        auswahl.wurzel_planen(neu_laden=True)
        self.assertTrue(auswahl.ausstehend)
        self.warten(lambda: not auswahl.ausstehend)
        self.assertEqual(auswahl.generation, generation + 1)
        self.assertEqual(auswahl.markiert, {})
        self.assertEqual(str(self.app.btn.cget("state")), "disabled")

    def test_native_bst_invalidierung_beim_tippen_und_reload_erhalten(self):
        anderer = self.basis / "OST" / "ABC - Andere"
        anderer.mkdir()
        gestartet, freigabe = threading.Event(), threading.Event()
        original = stw.betriebsstelle_pruefen

        def pruefen(region, auswahl, ril, klar, karte):
            if ril == "BLN":
                gestartet.set()
                if not freigabe.wait(5):
                    raise TimeoutError("Testfreigabe fehlt")
            return original(region, auswahl, ril, klar, karte)

        with patch.object(stw, "betriebsstelle_pruefen", side_effect=pruefen):
            self.warten(gestartet.is_set)
            nr = self.app.bst_nr
            such_nr = self.app.such_nr["PT2"]
            self.app.bst.set("ABC")
            self.assertGreater(self.app.bst_nr, nr)
            self.assertGreater(self.app.such_nr["PT2"], such_nr)
            self.assertIsNone(self.app.bst_ergebnis[0])
            self.assertTrue(self.app.liste_ausstehend)
            freigabe.set()
            self.warten(lambda: self.app.bst_ergebnis[0] == anderer)
        self.assertFalse(self.app.liste_ausstehend)
        self.assertIn("ABC - Andere", self.app.bst_map)

    def kopie_vorbereiten(self):
        quelle = self.wurzel / "ursprung"
        quelle.mkdir()
        for name in ("eins", "zwei", "drei"):
            (quelle / name).write_text(name)
        self.quelle_setzen(quelle)
        return quelle

    def test_native_quellensuche_beim_tippen_sofort_invalidiert(self):
        alt = self.wurzel / "M19061-01A Alt"
        alt.mkdir()
        gestartet, freigabe = threading.Event(), threading.Event()

        def suchen(psp):
            if psp == "M19061-01A":
                gestartet.set()
                if not freigabe.wait(5):
                    raise TimeoutError("Testfreigabe fehlt")
                return [alt], None
            return [], "Kein neuer Treffer"

        with patch.object(stw, "pt1_ordner_finden", side_effect=suchen):
            self.warten(gestartet.is_set)
            nr = self.app.such_nr["PT1"]
            self.app.psp.set("m19062-01")
            self.assertGreater(self.app.such_nr["PT1"], nr)
            freigabe.set()
            self.warten(lambda: "Kein neuer Treffer" in self.app.hinweise["PT1"].cget("text"))
        self.assertEqual(self.app.quellen["PT1"].get(), "")
        self.assertEqual(self.app.auto_wert["PT1"], "")

    def blockierte_kopie(self):
        gestartet, freigabe = threading.Event(), threading.Event()
        original = stw.datei_kopieren

        def kopieren(src, dst):
            if not gestartet.is_set():
                gestartet.set()
                if not freigabe.wait(5):
                    raise OSError("Testfreigabe fehlt")
            return original(src, dst)

        return gestartet, freigabe, patch.object(stw, "datei_kopieren", side_effect=kopieren)

    def test_native_kopierauftraege_bleiben_snapshot_bei_quellenwechsel(self):
        quelle = self.kopie_vorbereiten()
        neu = self.wurzel / "spaeter"
        neu.mkdir()
        (neu / "falsch").write_text("nicht kopieren")
        gestartet, freigabe, kopie = self.blockierte_kopie()
        with kopie:
            self.app.anlegen()
            self.warten(gestartet.is_set)
            projekt = self.app.wurzel
            self.app.quellen["PT1"].set(str(neu))
            self.app.unterziele["PT1"].set("ZX")
            self.app.beschr.set("Nachträgliche Änderung")
            freigabe.set()
            self.warten(lambda: self.app.kopier_thread is None)
            self.warten(lambda: not self.app.auswahl_offen())
        ziel = projekt / "01_Eingangsunterlagen" / "PT1" / "Stellwerk" / quelle.name
        self.assertEqual({p.name for p in ziel.iterdir()}, {"eins", "zwei", "drei"})
        self.assertEqual(list(projekt.rglob("falsch")), [])
        self.assertEqual(list((projekt / "01_Eingangsunterlagen" / "PT1" / "ZX").iterdir()), [])
        self.assertIn("M19061-01A", (projekt / "Projektinfo.txt").read_text(encoding="utf-8"))
        self.assertEqual(str(self.app.abbruch_btn.cget("state")), "disabled")

    def test_native_after_im_bestaetigungsdialog_aendert_genehmigten_plan_nicht(self):
        quelle = self.wurzel / "M19061-01A Genehmigt"
        andere = self.wurzel / "M19061-01A Nichtgenehmigt"
        (quelle / "teil").mkdir(parents=True)
        (andere / "anderer_teil").mkdir(parents=True)
        (quelle / "teil" / "Dokument").write_text("Genehmigte Daten")
        self.app.beschr.set("")
        auswahl = self.quelle_setzen(quelle)
        self.anklicken(auswahl, self.knoten(auswahl, quelle / "teil"))
        auswahl.ziel_setzen((quelle / "teil", False), "ZX")
        self.app.auto_wert["PT1"] = str(quelle)
        if self.app.such_job["PT1"]:
            self.app.after_cancel(self.app.such_job["PT1"])
            self.app.such_job["PT1"] = None
        self.app.such_nr["PT1"] += 1
        projektname = self.app.projektordnername()

        def bestaetigen(*_):
            self.app.after(0, lambda: self.app.such_ergebnis("PT1", [andere], None))
            self.warten(lambda: self.app.quellen["PT1"].get() == str(andere)
                        and not auswahl.ausstehend)
            self.assertEqual(self.app.beschr.get(), "Nichtgenehmigt")
            self.assertEqual(auswahl.markiert, {})
            return True

        self.meldungen["askyesno"].side_effect = bestaetigen
        self.app.anlegen()
        self.warten(lambda: self.app.kopier_thread is None)
        self.assertEqual(self.app.wurzel, self.bst / projektname)
        ziel = (self.app.wurzel / "01_Eingangsunterlagen" / "PT1" / "ZX"
                / quelle.name / "teil" / "Dokument")
        self.assertEqual(ziel.read_text(), "Genehmigte Daten")
        info = (self.app.wurzel / "Projektinfo.txt").read_text(encoding="utf-8")
        self.assertIn("Projektbeschreibung: Genehmigt", info)
        self.assertIn("PT1/ZX/teil", info)
        self.assertNotIn("Nichtgenehmigt", info)
        self.assertFalse((self.bst / self.app.projektordnername()).exists())

    def test_native_auto_pt2_auswahl_ueberlebt_anlegen_abbruch_und_fortsetzen(self):
        quelle = self.pt2 / "OST" / "BLN0"
        (quelle / "teil").mkdir(parents=True)
        for name in ("eins", "zwei", "drei"):
            (quelle / "teil" / name).write_text(name)
        auswahl = self.app.auswahlen["PT2"]
        self.warten(lambda: self.app.auto_wert["PT2"] == str(quelle)
                    and not auswahl.ausstehend)
        self.anklicken(auswahl, self.knoten(auswahl, quelle / "teil"))
        auswahl.ziel_setzen((quelle / "teil", False), "ZX")
        generation, markiert = auswahl.generation, dict(auswahl.markiert)
        gestartet, freigabe, kopie = self.blockierte_kopie()
        with kopie, patch.object(self.app, "such_ergebnis",
                                wraps=self.app.such_ergebnis) as ergebnisse:
            self.app.anlegen()
            self.warten(gestartet.is_set)
            self.warten(lambda: any(aufruf.args[0] == "PT2"
                                   for aufruf in ergebnisse.call_args_list))
            self.assertEqual(auswahl.generation, generation)
            self.assertEqual(auswahl.markiert, markiert)
            self.app.abbruch_btn.invoke()
            freigabe.set()
            self.warten(lambda: self.app.kopier_thread is None)
        self.assertEqual(auswahl.markiert, markiert)
        self.assertFalse(self.app.auswahl_offen())
        self.app.anlegen()
        self.warten(lambda: self.app.kopier_thread is None)
        ziel = (self.app.wurzel / "01_Eingangsunterlagen" / "PT2" / "ZX"
                / quelle.name / "teil")
        self.assertEqual({p.name for p in ziel.iterdir()}, {"eins", "zwei", "drei"})
        self.assertEqual(auswahl.markiert, markiert)

    def test_native_part_ordner_auswaehlbar_aber_part_dateien_ignoriert(self):
        quelle = self.wurzel / "quelle"
        unter = quelle / "regulaerer_ordner.part"
        unter.mkdir(parents=True)
        (unter / "Dokument").write_text("Unterordnerdaten")
        (quelle / "Datei").write_text("Wurzeldaten")
        (quelle / "angefangen.part").write_text("nicht fertig")
        auswahl = self.quelle_setzen(quelle)
        self.assertIn((unter, False), auswahl.knoten.values())
        auswahl.alle()
        self.app.anlegen()
        self.warten(lambda: self.app.kopier_thread is None)
        ziel = self.app.wurzel / "01_Eingangsunterlagen" / "PT1" / "Stellwerk" / quelle.name
        self.assertEqual((ziel / unter.name / "Dokument").read_text(), "Unterordnerdaten")
        self.assertEqual((ziel / "Datei").read_text(), "Wurzeldaten")
        self.assertFalse((ziel / "angefangen.part").exists())

    def test_native_neues_ziel_anhaengen_und_projektinfo_original_erhalten(self):
        quelle = self.kopie_vorbereiten()
        self.app.anlegen()
        self.warten(lambda: self.app.kopier_thread is None)
        projekt = self.app.wurzel
        info = projekt / "Projektinfo.txt"
        original = info.read_bytes()
        self.assertIn("PT1/Stellwerk/.", original.decode("utf-8"))
        self.app.unterziele["PT1"].set("ZX")
        self.app.anlegen()
        self.warten(lambda: self.app.kopier_thread is None)
        ergaenzt = info.read_bytes()
        self.assertTrue(ergaenzt.startswith(original))
        self.assertIn("PT1/ZX/.", ergaenzt.decode("utf-8"))
        self.assertEqual(ergaenzt.decode("utf-8").count("Angelegt am:"), 1)
        self.assertIn("PT1/ZX/.", self.app.status.cget("text"))
        ziel = projekt / "01_Eingangsunterlagen" / "PT1" / "ZX" / quelle.name
        self.assertEqual({p.name for p in ziel.iterdir()}, {"eins", "zwei", "drei"})

    def test_native_abbruchknopf_status_protokoll_und_weiterarbeiten(self):
        quelle = self.kopie_vorbereiten()
        gestartet, freigabe, kopie = self.blockierte_kopie()
        with kopie:
            self.app.anlegen()
            self.warten(gestartet.is_set)
            self.assertEqual(str(self.app.abbruch_btn.cget("state")), "normal")
            flaeche = self.app.abbruch_btn.master.master
            flaeche.yview_moveto(1)
            self.app.update()
            self.assertGreaterEqual(self.app.abbruch_btn.winfo_rooty(), flaeche.winfo_rooty())
            self.assertLessEqual(
                self.app.abbruch_btn.winfo_rooty() + self.app.abbruch_btn.winfo_height(),
                flaeche.winfo_rooty() + flaeche.winfo_height())
            fragen_vorher = self.meldungen["askyesno"].call_count
            self.meldungen["askyesno"].return_value = False
            self.app.abbruch_btn.invoke()
            self.assertFalse(self.app.abbruch.is_set())
            self.assertEqual(str(self.app.abbruch_btn.cget("state")), "normal")
            self.meldungen["askyesno"].return_value = True
            self.app.abbruch_btn.invoke()
            self.assertEqual(self.meldungen["askyesno"].call_count, fragen_vorher + 2)
            status = self.app.status.cget("text")
            for _ in range(15):
                self.app.update()
                time.sleep(0.01)
            self.assertEqual(self.app.status.cget("text"), status)
            self.assertIn("Abbruch angefordert", status)
            freigabe.set()
            self.warten(lambda: self.app.kopier_thread is None)
        ziel = self.app.wurzel / "01_Eingangsunterlagen" / "PT1" / "Stellwerk" / quelle.name
        self.assertEqual(len(list(ziel.iterdir())), 1)
        protokoll = (self.app.wurzel / "Kopierfehler.txt").read_text(encoding="utf-8")
        self.assertIn("ABBRUCH", protokoll)
        self.assertIn("Fortsetzen", protokoll)
        self.assertEqual(self.meldungen["showwarning"].call_args.args[0], "Abgebrochen")
        self.assertEqual(str(self.app.btn.cget("state")), "normal")
        self.app.anlegen()
        self.warten(lambda: self.app.kopier_thread is None)
        self.assertEqual(len(list(ziel.iterdir())), 3)

    def test_native_schliessen_wartet_und_zeigt_keinen_fertigdialog(self):
        self.kopie_vorbereiten()
        gestartet, freigabe, kopie = self.blockierte_kopie()
        original = self.app.destroy

        def schliessen():
            self.geschlossen = True
            original()

        self.app.destroy = schliessen
        with kopie:
            self.app.anlegen()
            self.warten(gestartet.is_set)
            projekt = self.app.wurzel
            fragen_vorher = self.meldungen["askyesno"].call_count
            self.app.schliessen()
            self.assertTrue(self.app.schliessen_ausstehend)
            self.assertEqual(self.meldungen["askyesno"].call_count, fragen_vorher + 1)
            self.assertFalse(self.geschlossen)
            freigabe.set()
            self.warten(lambda: self.geschlossen)
        self.assertTrue((projekt / "Kopierfehler.txt").exists())
        self.assertFalse(self.app.tk.call("after", "info"))
        self.meldungen["showwarning"].assert_not_called()
        self.meldungen["showinfo"].assert_not_called()

    def test_native_beschreibung_manuell_auto_leeren_und_laengenwarnung(self):
        quelle = self.wurzel / "M19061-01A Beschreibung"
        quelle.mkdir()
        self.app.beschr.set("")
        self.app.quellen["PT1"].set(str(quelle))
        self.assertEqual(self.app.beschr.get(), "Beschreibung")
        self.assertIn("(aus PT1 übernommen)", self.app.beschr_hinweis.cget("text"))
        self.app.quellen["PT1"].set("")
        self.assertEqual(self.app.beschr.get(), "")
        self.app.quellen["PT1"].set(str(quelle))
        self.app.beschr.set("Eigener Text")
        self.app.quellen["PT1"].set(str(quelle))
        self.assertEqual(self.app.beschr.get(), "Eigener Text")
        self.assertEqual(self.app.auto_beschr, "Beschreibung")
        self.assertEqual(str(self.app.beschr_hinweis.cget("foreground")), "#1f5fbf")
        self.app.beschr.set(" Beschreibung ")
        self.app.quellen["PT1"].set(str(quelle))
        self.assertEqual(self.app.beschr.get(), " Beschreibung ")
        self.app.beschr.set("Beschreibung")
        self.app.quellen["PT1"].set("")
        self.assertEqual(self.app.beschr.get(), "")
        self.app.beschr.set("X" * 130)
        self.warten(lambda: not self.app.auswahl_offen())
        self.assertEqual(str(self.app.laengen_hinweis.cget("foreground")), "darkorange")
        self.meldungen["askyesno"].return_value = False
        self.app.anlegen()
        bestaetigung = self.meldungen["askyesno"].call_args.args[1]
        self.assertIn("Beschreibung länger als 40", bestaetigung)
        self.assertIn("Projektpfad länger als 120", bestaetigung)
        self.assertFalse((self.bst / self.app.projektordnername()).exists())


if __name__ == "__main__":
    unittest.main()
