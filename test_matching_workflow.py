import json
import os
import tempfile
import unittest
from io import BytesIO
from unittest.mock import patch

from PIL import Image

from ai.image_match import (
    calculate_image_similarity,
    find_image_matches,
    save_uploaded_image,
)
from ai.storage import add_item, load_items, update_item_status


class ImageWorkflowTests(unittest.TestCase):
    def test_existing_image_search_and_upload_still_work(self):
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

            upload_bytes = BytesIO()
            Image.new("RGB", (12, 12), (200, 30, 80)).save(upload_bytes, format="PNG")

            class UploadedImage:
                def getvalue(self):
                    return upload_bytes.getvalue()

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