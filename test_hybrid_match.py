import json
import os
import tempfile
import unittest
from io import BytesIO
from unittest.mock import Mock, patch

from PIL import Image

from ai.fuzzy_match import calculate_match_score
from ai.hybrid_match import calculate_hybrid_match, get_hybrid_matches_for_lost
from ai.image_match import (
    calculate_image_similarity,
    find_image_matches,
    save_uploaded_image,
)
from ai.semantic_match import calculate_semantic_similarity
from ai.storage import add_item, load_items, update_item_status


class HybridMatchingTests(unittest.TestCase):
    def setUp(self):
        self.lost = {
            "id": 7,
            "item_type": "Backpack",
            "color": "Black",
            "brand": "Acme",
            "location": "Library",
            "description": "Black bag containing a laptop",
        }

    def test_semantically_similar_wording_uses_mock_score(self):
        found = {
            "id": 2,
            "item_type": "Backpack",
            "color": "Black",
            "brand": "Acme",
            "location": "Library",
            "description": "Dark backpack with a computer inside",
        }
        scorer = lambda _left, _right: 88

        result = calculate_hybrid_match(
            self.lost,
            found,
            semantic_scorer=scorer,
            image_scorer=lambda _lost, _found: None,
        )

        self.assertEqual(result["components"]["semantic"], 88)
        self.assertIn("Descriptions have similar meaning", result["reasons"])

    def test_different_descriptions_score_lower(self):
        found = dict(self.lost, id=3, description="A blue ceramic mug")
        high = calculate_hybrid_match(
            self.lost,
            dict(found, id=4),
            semantic_scorer=lambda _left, _right: 90,
            image_scorer=lambda _lost, _found: None,
        )
        low = calculate_hybrid_match(
            self.lost,
            found,
            semantic_scorer=lambda _left, _right: 10,
            image_scorer=lambda _lost, _found: None,
        )
        self.assertGreater(high["score"], low["score"])

    def test_missing_images_and_unknown_location_are_not_zero_weighted(self):
        lost = dict(self.lost, image_path="", location="North entrance")
        found = dict(self.lost, id=8, image_path="", location="West stairs")

        result = calculate_hybrid_match(
            lost,
            found,
            semantic_scorer=lambda _left, _right: 70,
        )

        self.assertNotIn("image", result["components"])
        self.assertNotIn("location", result["components"])
        self.assertAlmostEqual(result["score"], 82.86, places=2)

    def test_missing_known_location_and_empty_description(self):
        found = dict(self.lost, id=9, description="", location="Other")
        semantic_scorer = Mock(return_value=75)

        result = calculate_hybrid_match(
            self.lost,
            found,
            semantic_scorer=semantic_scorer,
            image_scorer=lambda _lost, _found: None,
        )

        semantic_scorer.assert_not_called()
        self.assertNotIn("semantic", result["components"])
        self.assertNotIn("location", result["components"])
        self.assertGreaterEqual(result["score"], 0)
        self.assertLessEqual(result["score"], 100)

    def test_empty_or_invalid_semantic_inputs_are_safe(self):
        self.assertIsNone(calculate_semantic_similarity("", "description"))
        self.assertIsNone(calculate_semantic_similarity(None, "description"))

    def test_semantic_cosine_score_is_bounded_and_model_free(self):
        vectors = {
            "same": [1.0, 0.0],
            "similar": [0.8, 0.6],
        }
        with patch(
            "ai.semantic_match._encode_description",
            side_effect=lambda text: vectors[text],
        ):
            self.assertEqual(
                calculate_semantic_similarity("same", "similar"),
                80.0,
            )

    def test_optional_components_are_weight_normalized(self):
        found = dict(self.lost, id=10, location="")
        result = calculate_hybrid_match(
            self.lost,
            found,
            semantic_scorer=lambda _left, _right: 50,
            image_scorer=lambda _lost, _found: None,
        )
        expected = (30 * 100 + 40 * 50) / (30 + 40)
        self.assertAlmostEqual(result["score"], expected, places=2)
        self.assertNotIn("location", result["components"])
        self.assertNotIn("image", result["components"])

    def test_claimed_reports_and_duplicate_ids_are_excluded(self):
        available = dict(self.lost, id=11, status="Found")
        claimed = dict(self.lost, id=12, status="claimed")
        matches = get_hybrid_matches_for_lost(
            self.lost,
            [available, dict(available), claimed],
            threshold=0,
            semantic_scorer=lambda _left, _right: 80,
            image_scorer=lambda _lost, _found: None,
        )
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["found"]["id"], 11)

    def test_matches_are_sorted_by_hybrid_score_descending(self):
        found_items = [
            dict(self.lost, id=21, description="low"),
            dict(self.lost, id=22, description="high"),
        ]
        score_by_description = {"low": 10, "high": 95}
        matches = get_hybrid_matches_for_lost(
            self.lost,
            found_items,
            threshold=0,
            semantic_scorer=lambda _left, right: score_by_description[right],
            image_scorer=lambda _lost, _found: None,
        )
        self.assertEqual([match["found"]["id"] for match in matches], [22, 21])
        self.assertGreaterEqual(matches[0]["score"], matches[1]["score"])

    def test_model_failure_falls_back_to_existing_fuzzy_score(self):
        found = dict(self.lost, id=30)
        with patch("ai.hybrid_match.calculate_semantic_similarity", return_value=None):
            with patch(
                "ai.hybrid_match.get_semantic_model_error",
                return_value="model download failed",
            ):
                result = calculate_hybrid_match(
                    self.lost,
                    found,
                    image_scorer=lambda _lost, _found: None,
                )

        self.assertTrue(result["fallback"])
        self.assertEqual(result["score"], calculate_match_score(self.lost, found))

    def test_existing_fuzzy_and_image_matching_continue_to_work(self):
        self.assertEqual(calculate_match_score(self.lost, dict(self.lost)), 100.0)
        with tempfile.TemporaryDirectory() as directory:
            image_path = os.path.join(directory, "item.png")
            image_bytes = BytesIO()
            Image.new("RGB", (24, 24), (20, 100, 180)).save(image_path)
            Image.new("RGB", (24, 24), (20, 100, 180)).save(image_bytes, format="PNG")

            self.assertEqual(
                calculate_image_similarity(image_bytes.getvalue(), image_path),
                100.0,
            )
            self.assertIsNone(
                calculate_image_similarity(image_bytes.getvalue(), "missing.png")
            )
            matches = find_image_matches(
                image_bytes.getvalue(),
                [{"id": 1, "image_path": image_path}],
            )
            self.assertEqual(matches[0]["score"], 100.0)

    def test_report_photo_upload_still_saves_supported_image(self):
        with tempfile.TemporaryDirectory() as directory:
            image_bytes = BytesIO()
            Image.new("RGB", (12, 12), (200, 30, 80)).save(
                image_bytes,
                format="PNG",
            )

            class UploadedImage:
                def getvalue(self):
                    return image_bytes.getvalue()

            with patch("ai.image_match.IMAGE_DIRECTORY", directory):
                saved_path = save_uploaded_image(UploadedImage())

            self.assertTrue(os.path.isfile(saved_path))
            self.assertTrue(saved_path.endswith(".jpg"))


class ReportWorkflowTests(unittest.TestCase):
    def test_report_add_and_claim_status_update_preserve_json_records(self):
        with tempfile.TemporaryDirectory() as directory:
            report_path = os.path.join(directory, "reports.json")
            original = [{"id": 1, "item_type": "Wallet", "status": "Found"}]
            with open(report_path, "w", encoding="utf-8") as report_file:
                json.dump(original, report_file)

            add_item(report_path, {"item_type": "Keys", "status": "Found"})
            self.assertTrue(update_item_status(report_path, "2", "Claimed"))
            self.assertFalse(update_item_status(report_path, "invalid", "Claimed"))

            saved = load_items(report_path)
            self.assertEqual(saved[0], original[0])
            self.assertEqual(saved[1]["id"], 2)
            self.assertEqual(saved[1]["status"], "Claimed")

    def test_malformed_records_are_ignored_without_changing_json_format(self):
        with tempfile.TemporaryDirectory() as directory:
            report_path = os.path.join(directory, "reports.json")
            with open(report_path, "w", encoding="utf-8") as report_file:
                report_file.write('[{"id": 1}, null, "bad record"]')
            self.assertEqual(load_items(report_path), [{"id": 1}])


if __name__ == "__main__":
    unittest.main()
