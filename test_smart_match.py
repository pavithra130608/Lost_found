import unittest
from ai.smart_match import get_smart_match_explanation


class SmartMatchExplanationTests(unittest.TestCase):
    def test_description_and_color_match_brand_differs(self):
        lost = {
            "item_type": "Phone",
            "color": "Blue",
            "brand": "Samsung",
            "location": "Library",
            "date": "2026-10-11",
            "description": "Blue smartphone with clear transparent case",
        }
        found = {
            "item_type": "Phone",
            "color": "Blue",
            "brand": "Vivo",
            "location": "Canteen",
            "date": "2026-09-01",  # > 30 days
            "description": "Blue smartphone with clear transparent case",
        }
        # Simulate match criteria
        match = {
            "score": 65.0,
            "criteria": {
                "item type": 100.0,
                "description": 100.0,
                "brand": 15.0,
                "color": 100.0,
                "location": 0.0,
                "date": 0.0,
            },
        }

        explanation = get_smart_match_explanation(lost, found, match)
        attrs = {a["name"]: a for a in explanation["attributes"]}

        self.assertEqual(attrs["Category"]["status"], "Match")
        self.assertEqual(attrs["Description"]["status"], "Match")
        self.assertEqual(attrs["Color"]["status"], "Match")
        self.assertEqual(attrs["Brand"]["status"], "Different")
        self.assertEqual(attrs["Location"]["status"], "Different")
        self.assertEqual(attrs["Date"]["status"], "Different")

        summary = explanation["summary"]
        self.assertIn("match", summary)
        self.assertIn("brand", summary)
        self.assertIn("differ", summary)

    def test_partial_match_detection(self):
        lost = {
            "item_type": "Backpack",
            "color": "Dark Blue",
            "brand": "Nike",
            "location": "Library",
            "date": "2026-10-10",
            "description": "Nike backpack with laptop and notebooks inside",
        }
        found = {
            "item_type": "Backpack",
            "color": "Blue",
            "brand": "Nike",
            "location": "Library block 103",
            "date": "2026-10-11",  # 1 day apart
            "description": "Blue backpack found with books inside",
        }
        match = {
            "score": 75.0,
            "criteria": {
                "item type": 100.0,
                "description": 45.0,
                "brand": 100.0,
                "color": 0.0,
                "location": 0.0,
                "date": 75.0,
            },
        }

        explanation = get_smart_match_explanation(lost, found, match)
        attrs = {a["name"]: a for a in explanation["attributes"]}

        self.assertEqual(attrs["Category"]["status"], "Match")
        self.assertEqual(attrs["Brand"]["status"], "Match")
        self.assertEqual(attrs["Description"]["status"], "Partial Match")
        self.assertEqual(attrs["Color"]["status"], "Partial Match")
        self.assertEqual(attrs["Location"]["status"], "Partial Match")
        self.assertEqual(attrs["Date"]["status"], "Partial Match")

        self.assertIn("partially match", explanation["summary"].lower())

    def test_empty_or_missing_attributes_handled_gracefully(self):
        lost = {"item_type": "Keys"}
        found = {"item_type": "Keys"}
        explanation = get_smart_match_explanation(lost, found)

        attrs = {a["name"]: a for a in explanation["attributes"]}
        self.assertEqual(attrs["Category"]["status"], "Match")
        self.assertEqual(attrs["Brand"]["status"], "Not Specified")
        self.assertEqual(attrs["Color"]["status"], "Not Specified")
        self.assertEqual(attrs["Photo"]["status"], "Not Specified")

    def test_render_smart_match_html(self):
        from ai.smart_match import render_smart_match_html, render_smart_match_summary_html
        lost = {"item_type": "Phone", "color": "Blue"}
        found = {"item_type": "Phone", "color": "Blue"}
        explanation = get_smart_match_explanation(lost, found)
        html = render_smart_match_html(explanation)
        self.assertIn("<table", html)
        self.assertIn("Match", html)
        self.assertIn("Category", html)

        # Ensure no line starts with 4+ spaces so Markdown does not treat it as a code block
        for line in html.splitlines():
            self.assertFalse(line.startswith("    "), f"Line has 4+ leading spaces: {line[:20]}")

        summary_html = render_smart_match_summary_html(explanation)
        self.assertIn("Smart Match Summary", summary_html)
        for line in summary_html.splitlines():
            self.assertFalse(line.startswith("    "), f"Summary line has 4+ leading spaces: {line[:20]}")


if __name__ == "__main__":
    unittest.main()
