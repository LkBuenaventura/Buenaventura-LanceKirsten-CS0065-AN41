"""Regression checks for retrieval, capacity review, and JSON retention.

Run with: python -m unittest -v
Tests use temporary databases and never call the live USGS service.
"""
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import main


class CBRTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "memory.json"
        self.db_patch = patch.object(main, "DB_FILE", str(self.db))
        self.db_patch.start()
        self.addCleanup(self.db_patch.stop)
        self.flood = main.starter_cases()[2]
        self.query = dict(self.flood["problem"], intensity=5.0)

    def run_console(self, answers):
        output = io.StringIO()
        with patch("builtins.input", side_effect=answers), redirect_stdout(output):
            main.main()
        return output.getvalue()

    def test_capacity_calculation_and_original_unchanged(self):
        before = copy.deepcopy(self.flood)
        result = main.adapt_solution(self.flood["solution"], self.query, self.flood["problem"])
        self.assertEqual(result["shelter_capacity"], 7500)
        self.assertEqual(result["capacity_adaptation"]["original_capacity"], 5000)
        self.assertTrue(result["resource_allocation"]["Survival"])
        self.assertEqual(self.flood, before)

    def test_threshold_and_rounding(self):
        at_threshold = dict(self.query, intensity=4.0)
        result = main.adapt_solution(self.flood["solution"], at_threshold, self.flood["problem"])
        self.assertEqual(result["shelter_capacity"], 5000)
        odd_capacity = dict(self.flood["solution"], shelter_capacity=5001)
        result = main.adapt_solution(odd_capacity, self.query, self.flood["problem"])
        self.assertEqual(result["shelter_capacity"], 7502)

    def test_other_disaster_cannot_outrank_matching_type(self):
        typhoon = copy.deepcopy(self.flood)
        typhoon["problem"] = dict(self.query, disaster_type="Typhoon")
        match, score = main.retrieve_similar_case(self.query, [typhoon, self.flood])
        self.assertIs(match, self.flood)
        self.assertEqual(score, 13)
        self.assertEqual(main.retrieve_similar_case(self.query, [typhoon]), (None, 0))
        self.assertEqual(main.retrieve_similar_case(self.query, []), (None, 0))

    def test_legacy_resources_are_preserved(self):
        legacy = dict(self.flood["solution"], resource_allocation=["Food", "Water", "Rescue Boats", "Radio"])
        result = main.normalize_solution(legacy)
        self.assertEqual(result["resource_allocation"]["Survival"], ["Food", "Water"])
        self.assertEqual(result["resource_allocation"]["Logistics"], ["Rescue Boats"])
        self.assertEqual(result["resource_allocation"]["Other"], ["Radio"])
        self.assertIsInstance(legacy["resource_allocation"], list)

    def test_legacy_capacity_descriptions(self):
        for text, expected in [
            ("Requires 15,000 beds across 10 facilities.", 15000),
            ("20,000 displaced individuals accommodated in tents.", 20000),
            ("Establish tent cities to accommodate ~17500 displaced residents.", 17500),
            ("5,000", 5000),
        ]:
            with self.subTest(text=text):
                result = main.normalize_solution(dict(self.flood["solution"], shelter_capacity=text))
                self.assertEqual(result["shelter_capacity"], expected)

    def test_invalid_capacity_rejected(self):
        for capacity in (0, -1, True, 3.5, float("nan"), float("inf"), "unknown"):
            with self.subTest(capacity=capacity), self.assertRaises(ValueError):
                main.normalize_solution(dict(self.flood["solution"], shelter_capacity=capacity))

    def test_migration_backup_and_repeat_loading(self):
        old = copy.deepcopy(main.starter_cases()[0])
        old["solution"]["resource_allocation"] = ["Food", "Water", "Rescue Boats"]
        old["problem"].pop("proximity_hazard")
        self.db.write_text(json.dumps([old]), encoding="utf-8")
        original_bytes = self.db.read_bytes()
        loaded = main.load_database()
        self.assertEqual(len(loaded), 3)
        self.assertEqual(Path(str(self.db) + ".legacy.bak").read_bytes(), original_bytes)
        self.assertEqual(main.load_database(), loaded)
        self.assertEqual(len(main.load_database()), 3)

    def test_invalid_database_is_not_overwritten(self):
        self.db.write_text("{invalid", encoding="utf-8")
        output = self.run_console([])
        self.assertIn("Could not load the case base", output)
        self.assertEqual(self.db.read_text(encoding="utf-8"), "{invalid")

    def test_review_reprompts_then_revises_without_mutating(self):
        solution = dict(self.flood["solution"], shelter_capacity=7500)
        with patch("builtins.input", side_effect=["-1", "0", "abc", "2.5", "nan", "8000"]), redirect_stdout(io.StringIO()):
            result = main.review_solution(solution)
        self.assertEqual(result["shelter_capacity"], 8000)
        self.assertEqual(result["capacity_review"]["status"], "revised")
        self.assertEqual(solution["shelter_capacity"], 7500)

    def test_end_to_end_revision_retention_and_reload(self):
        output = self.run_console(["Flood", "Luzon", "River", "5", "8000", "y", "n"])
        for expected in ("Original capacity: 5,000", "Recommended capacity: 7,500", "Reviewed final shelter capacity: 8,000", "New Case Saved", "UPDATED CASE LIST"):
            self.assertIn(expected, output)
        loaded = main.load_database()
        self.assertEqual(len(loaded), 4)
        self.assertEqual(loaded[-1]["solution"]["shelter_capacity"], 8000)
        self.assertEqual(loaded[-1]["solution"]["capacity_review"]["recommended_capacity"], 7500)
        match, _ = main.retrieve_similar_case(self.query, loaded)
        self.assertEqual(match, loaded[-1])
        adapted = main.adapt_solution(match["solution"], self.query, match["problem"])
        self.assertNotIn("capacity_review", adapted)

    def test_accept_and_decline_to_save(self):
        output = self.run_console(["Flood", "Luzon", "River", "5", "", "n", "n"])
        self.assertIn("Reviewed final shelter capacity: 7,500", output)
        self.assertNotIn("New Case Saved", output)
        self.assertEqual(len(main.load_database()), 3)

    def test_invalid_inputs_then_valid_scenario(self):
        output = self.run_console([
            "Hurricane", "Flood", "", "Flood", "Luzon", "River", "nan",
            "Flood", "Luzon", "River", "6", "Flood", "Luzon", "River", "5", "", "n", "n",
        ])
        self.assertIn("Please choose", output)
        self.assertIn("Please enter a location", output)
        self.assertIn("finite, positive", output)
        self.assertIn("between 1 and 5", output)

    def test_offline_earthquake_lookup(self):
        # Simulate an unavailable optional requests package.
        with patch.dict("sys.modules", {"requests": None}), redirect_stdout(io.StringIO()):
            self.assertEqual(main.search_internet_for_cases(7.2), [])
        with patch.object(main, "search_internet_for_cases", return_value=[]):
            output = self.run_console(["Earthquake", "Visayas", "Mountain", "7.2", "", "n", "n"])
        self.assertIn("Bohol Earthquake", output)


if __name__ == "__main__":
    unittest.main()
