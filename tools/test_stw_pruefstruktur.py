import tempfile
import unittest
from pathlib import Path
import stw_pruefstruktur_logik as tool


class PspTests(unittest.TestCase):
    def test_accepts_psp_with_optional_suffix(self):
        for psp in ("M19061-01", "M19061-01A"):
            with self.subTest(psp=psp):
                self.assertRegex(psp, tool.PSP_MUSTER)
        normalized = tool.normalisiere_psp("m19061-01a")
        self.assertEqual(normalized, "M19061-01A")
        self.assertRegex(normalized, tool.PSP_MUSTER)

    def test_rejects_invalid_psp_formats(self):
        for psp in ("M1906-01", "M19061-1", "M19061-01AB", "m19061-01a", "19061-01"):
            with self.subTest(psp=psp):
                self.assertNotRegex(psp, tool.PSP_MUSTER)

    def test_pt1_search_matches_complete_psp_and_group(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            group = root / "M19xxx"
            group.mkdir()
            expected = group / "M19061-01A Umbau"
            expected.mkdir()
            expected_without_suffix = group / "M19061-01 Umbau"
            expected_without_suffix.mkdir()
            (group / "M19061-01AB Umbau").mkdir()
            self.assertEqual(tool.pt1_gruppenordner("m19061-01a", root), group)
            treffer, fehler = tool.pt1_ordner_finden("m19061-01a", root)
            self.assertIsNone(fehler)
            self.assertEqual(treffer, [expected])
            treffer, fehler = tool.pt1_ordner_finden("m19061-01", root)
            self.assertIsNone(fehler)
            self.assertEqual(treffer, [expected_without_suffix])


class CopySafetyTests(unittest.TestCase):
    def test_auto_suggestion_does_not_create_copy_job(self):
        auswahl = tool.CopySelection()
        self.assertIsNone(tool.kopierauftrag_pruefen(
            "PT1", auswahl, ("M19061-01",), Path("/project/PT1/source"), "/share",
            "/share/M19xxx/M19061-01 Project"))

    def test_disabled_selection_ignores_existing_invalid_path(self):
        auswahl = tool.CopySelection()
        auswahl.set_source("/path/that/does/not/exist")
        self.assertIsNone(tool.kopierauftrag_pruefen(
            "PT1", auswahl, ("M19061-01",), Path("/project/PT1/source"), "/share"))

    def test_enabled_selection_without_explicit_approval_is_blocked(self):
        auswahl = tool.CopySelection()
        auswahl.set_source("/share/M19xxx/project/subfolder")
        auswahl.enabled = True
        with self.assertRaisesRegex(ValueError, "nicht ausdrücklich bestätigt"):
            tool.kopierauftrag_pruefen(
                "PT1", auswahl, ("M19061-01",), "/project/PT1/source", "/share")

    def test_confirmed_subfolder_can_be_selected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "share"
            source = root / "M19xxx" / "M19061-01 Umbau" / "Stellwerk"
            source.mkdir(parents=True)
            auswahl = tool.CopySelection()
            auswahl.set_source(source)
            auswahl.approve(("M19061-01", "Ost", "BLN"))
            auswahl.enabled = True
            job = tool.kopierauftrag_pruefen(
                "PT1", auswahl, ("M19061-01", "Ost", "BLN"), root / "target", root)
            self.assertEqual(job, ("PT1", source, root / "target"))

    def test_container_requires_separate_whole_folder_opt_in(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "share"
            source = root / "M19xxx" / "M19061-01 Umbau"
            source.mkdir(parents=True)
            auswahl = tool.CopySelection()
            auswahl.set_source(source)
            auswahl.approve(("psp",))
            auswahl.enabled = True
            with self.assertRaisesRegex(ValueError, "Gesamten Ordner"):
                job = tool.kopierauftrag_pruefen(
                    "PT1", auswahl, ("psp",), root / "target", root)
            auswahl.copy_all = True
            job = tool.kopierauftrag_pruefen(
                "PT1", auswahl, ("psp",), root / "target", root)
            self.assertEqual(job[1], source)

    def test_manually_selected_container_is_still_classified_as_broad(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "pt2"
            source = root / "OST" / "BLN0"
            source.mkdir(parents=True)
            self.assertTrue(tool.quelle_ist_gesamtordner("PT2", source, root))
            auswahl = tool.CopySelection()
            auswahl.set_source(source)
            auswahl.approve(("OST", "BLN"))
            auswahl.enabled = True
            with self.assertRaisesRegex(ValueError, "Gesamten Ordner"):
                tool.kopierauftrag_pruefen(
                    "PT2", auswahl, ("OST", "BLN"), root / "target", root)

    def test_named_project_container_is_broad_even_outside_share_root(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "share"
            project = Path(temp) / "manual" / "M19061-01A Projekt"
            project.mkdir(parents=True)
            self.assertTrue(tool.quelle_ist_gesamtordner(
                "PT1", project, root, kontext=("M19061-01A",)))

    def test_source_and_context_changes_revoke_approval(self):
        original = ("M19061-01A", "OST", "BLN", "basis", "ziel")
        for index in range(len(original)):
            with self.subTest(context_index=index):
                auswahl = tool.CopySelection()
                auswahl.set_source("/share/M19xxx/project/subfolder")
                auswahl.approve(original)
                auswahl.enabled = True
                changed = list(original)
                changed[index] += "-changed"
                self.assertTrue(auswahl.revoke_if_context_changed(changed))
                self.assertFalse(auswahl.enabled)
                self.assertFalse(auswahl.is_approved(original))

        auswahl = tool.CopySelection()
        auswahl.set_source("/share/first")
        auswahl.approve(original)
        auswahl.set_source("/share/second")
        self.assertFalse(auswahl.is_approved(original))

    def test_old_search_results_are_discarded_by_number_or_context(self):
        self.assertFalse(tool.suchergebnis_ist_aktuell(1, 2, ("OST", "BLN"), ("OST", "BLN")))
        self.assertFalse(tool.suchergebnis_ist_aktuell(2, 2, ("OST", "BLN"), ("NORD", "BLN")))
        self.assertTrue(tool.suchergebnis_ist_aktuell(2, 2, ("OST", "BLN"), ("OST", "BLN")))

    def test_source_and_target_overlap_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.assertTrue(tool.pfade_ueberlappen(root, root))
            self.assertTrue(tool.pfade_ueberlappen(root, root / "target"))
            self.assertTrue(tool.pfade_ueberlappen(root / "source", root))
            self.assertFalse(tool.pfade_ueberlappen(root / "source", root / "other"))


if __name__ == "__main__":
    unittest.main()
