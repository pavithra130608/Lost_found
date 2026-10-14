import unittest
import os
import tempfile
from unittest.mock import patch

from ai.item_match import compare_items, find_item_matches, hill_climb


class ItemMatchingTests(unittest.TestCase):
    def make_report(self, **overrides):
        report = {
            "item_type": "Notebook",
            "color": "Blue",
            "brand": "",
            "location": "Library",
            "date": "2026-10-10",
            "description": "Blue ruled notebook with placement notes",
            "status": "Lost",
        }
        report.update(overrides)
        return report

    def test_notebook_with_similar_description_is_credible(self):
        result = compare_items(
            self.make_report(),
            self.make_report(
                description="Found a blue ruled notebook with placement notes",
                status="Found",
            ),
        )
        self.assertTrue(result["credible"])
        self.assertTrue(any("Descriptions" in reason for reason in result["reasons"]))

    def test_laptop_exact_type_can_match(self):
        result = compare_items(
            self.make_report(item_type="Laptop", description="Dell laptop with a cracked corner"),
            self.make_report(item_type="Laptop", description="Found a Dell laptop with a cracked corner"),
        )
        self.assertTrue(result["credible"])

    def test_backpack_and_bag_are_explicit_synonyms(self):
        result = compare_items(
            self.make_report(item_type="Backpack", description="Red backpack with a name tag"),
            self.make_report(item_type="Bag", description="Red bag with a name tag"),
        )
        self.assertTrue(result["credible"])
        self.assertTrue(any("Compatible item types" in reason for reason in result["reasons"]))

    def test_notebook_and_backpack_are_rejected_even_with_shared_details(self):
        result = compare_items(
            self.make_report(),
            self.make_report(item_type="Backpack"),
        )
        self.assertFalse(result["credible"])
        self.assertIn("Incompatible item types: Notebook vs Backpack.", result["reasons"])

    def test_notebook_and_bottle_are_rejected(self):
        result = compare_items(
            self.make_report(),
            self.make_report(item_type="Bottle"),
        )
        self.assertFalse(result["credible"])

    def test_case_whitespace_and_punctuation_are_normalized(self):
        result = compare_items(
            self.make_report(item_type="  NOTEBOOK! ", color="Dark-blue"),
            self.make_report(item_type="notebook", color="dark blue"),
        )
        self.assertTrue(result["credible"])

    def test_color_and_location_alone_do_not_make_a_candidate(self):
        result = compare_items(
            self.make_report(description="", brand=""),
            self.make_report(description="", brand=""),
        )
        self.assertFalse(result["credible"])
        self.assertTrue(any("Rejected:" in reason for reason in result["reasons"]))

    def test_claimed_reports_are_excluded(self):
        available = self.make_report(description="Blue ruled notebook with placement notes", status="Found")
        claimed = self.make_report(description="Blue ruled notebook with placement notes", status="Claimed")
        matches, rejected = find_item_matches(self.make_report(), [available, claimed])
        self.assertEqual(len(matches), 1)
        self.assertEqual(rejected, [])

    def test_missing_fields_are_not_counted_as_evidence(self):
        result = compare_items(
            self.make_report(description="", brand="", color="", location="", date=""),
            self.make_report(description="", brand="", color="", location="", date=""),
        )
        self.assertFalse(result["credible"])
        self.assertEqual(result["criteria"], {"item type": 100.0})

    def test_unreadable_photos_do_not_break_text_matching(self):
        with tempfile.TemporaryDirectory() as directory:
            lost_path = os.path.join(directory, "lost.jpg")
            found_path = os.path.join(directory, "found.jpg")
            open(lost_path, "wb").close()
            open(found_path, "wb").close()
            lost = self.make_report(
                image_path=lost_path,
                description="Blue ruled notebook with placement notes",
            )
            found = self.make_report(
                image_path=found_path,
                description="Found a blue ruled notebook with placement notes",
            )

            with patch("ai.item_match.calculate_image_similarity", return_value=None):
                result = compare_items(lost, found)

        self.assertTrue(result["credible"])
        self.assertNotIn("photo", result["criteria"])

    def test_hill_climbing_moves_to_a_better_neighbor(self):
        scores = {"low": 10, "middle": 20, "high": 30}
        result = hill_climb(
            "low",
            lambda current: [state for state in scores if state != current],
            scores.__getitem__,
        )
        self.assertEqual(result["path"], ["low", "high"])
        self.assertEqual(result["state"], "high")

    def test_hill_climbing_stops_when_no_neighbor_improves(self):
        scores = {"peak": 30, "lower": 20, "lowest": 10}
        neighbor_calls = []

        def neighbors(current):
            neighbor_calls.append(current)
            return [state for state in scores if state != current]

        result = hill_climb("peak", neighbors, scores.__getitem__)
        self.assertEqual(result["path"], ["peak"])
        self.assertEqual(neighbor_calls, ["peak"])

    def test_correct_candidate_ranks_above_weak_candidate(self):
        lost = self.make_report(
            description="blue spiral notebook with handwritten math notes and name inside"
        )
        weak = self.make_report(
            id=2,
            description="blue notebook with a few math notes",
            status="Found",
        )
        strong = self.make_report(
            id=3,
            description="blue spiral notebook with handwritten math notes and name inside",
            status="Found",
        )
        matches, _ = find_item_matches(lost, [weak, strong])
        self.assertEqual([entry["found"]["id"] for entry in matches], [3, 2])
        self.assertGreater(matches[0]["score"], matches[1]["score"])

    def test_multiple_restarts_are_run_and_discover_strong_candidate(self):
        lost = self.make_report(
            description="blue spiral notebook with handwritten math notes and name inside"
        )
        weak = self.make_report(
            id=2,
            description="blue notebook with a few math notes",
            status="Found",
        )
        strong = self.make_report(
            id=3,
            description="blue spiral notebook with handwritten math notes and name inside",
            status="Found",
        )
        with patch("ai.item_match.hill_climb", wraps=hill_climb) as search:
            matches, _ = find_item_matches(lost, [weak, strong], restarts=2)
        self.assertEqual(search.call_count, 2)
        self.assertEqual(matches[0]["found"]["id"], 3)

    def test_threshold_can_exclude_a_credible_candidate(self):
        found = self.make_report(
            id=2,
            description="Found a blue ruled notebook with class notes",
            status="Found",
        )
        matches, rejected = find_item_matches(
            self.make_report(),
            [found],
            minimum_score=100,
        )
        self.assertEqual(matches, [])
        self.assertTrue(any("below the minimum" in reason for reason in rejected[0]["reasons"]))

    def test_duplicate_report_ids_are_returned_once(self):
        found = self.make_report(
            id=2,
            description="Blue ruled notebook with placement notes",
            status="Found",
        )
        matches, _ = find_item_matches(self.make_report(), [found, dict(found)])
        self.assertEqual(len(matches), 1)

    def test_empty_candidate_set_returns_empty_results(self):
        self.assertEqual(find_item_matches(self.make_report(), []), ([], []))


if __name__ == "__main__":
    unittest.main()