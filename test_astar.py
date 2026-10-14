import unittest

from ai.astar import DEMO_CAMPUS_GRAPH, astar_search, map_report_location


class AStarSearchTests(unittest.TestCase):
    def setUp(self):
        self.graph = {
            "Start": {"A": 2, "B": 5},
            "A": {"Start": 2, "B": 1, "Goal": 5},
            "B": {"Start": 5, "A": 1, "Goal": 2},
            "Goal": {"A": 5, "B": 2},
        }

    def test_finds_expected_shortest_path_and_distance(self):
        result = astar_search(self.graph, "Start", "Goal")
        self.assertEqual(result["path"], ["Start", "A", "B", "Goal"])
        self.assertEqual(result["distance"], 5.0)

    def test_start_and_destination_same(self):
        self.assertEqual(
            astar_search(self.graph, "A", "A"),
            {"path": ["A"], "distance": 0.0},
        )

    def test_unknown_start_and_destination_raise_clear_errors(self):
        with self.assertRaisesRegex(ValueError, "Unknown starting location"):
            astar_search(self.graph, "Unknown", "Goal")
        with self.assertRaisesRegex(ValueError, "Unknown destination"):
            astar_search(self.graph, "Start", "Unknown")

    def test_unreachable_destination_returns_none(self):
        graph = {"Start": {}, "Goal": {}}
        self.assertIsNone(astar_search(graph, "Start", "Goal"))

    def test_multiple_routes_choose_the_shorter_route(self):
        result = astar_search(self.graph, "Start", "Goal")
        self.assertEqual(result["distance"], 5.0)
        self.assertNotEqual(result["path"], ["Start", "B", "Goal"])

    def test_admissible_heuristic_does_not_overestimate_remaining_cost(self):
        remaining_costs = {"Start": 5, "A": 3, "B": 2, "Goal": 0}
        estimates = {"Start": 4, "A": 3, "B": 2, "Goal": 0}
        for node, exact_cost in remaining_costs.items():
            heuristic_value = estimates[node]
            self.assertLessEqual(heuristic_value, exact_cost)

        result = astar_search(
            self.graph,
            "Start",
            "Goal",
            heuristic=lambda node, _goal: estimates[node],
        )
        self.assertEqual(result["distance"], 5.0)

    def test_sample_graph_is_configurable_and_has_known_location_mapping(self):
        self.assertEqual(map_report_location(" library! "), "Library")
        self.assertIsNone(map_report_location("Library block 103"))
        self.assertIsNotNone(astar_search(DEMO_CAMPUS_GRAPH, "Library", "Auditorium"))

    def test_configured_alias_maps_only_to_existing_nodes(self):
        self.assertEqual(
            map_report_location("Library block 103", aliases={"Library block 103": "Library"}),
            "Library",
        )
        self.assertIsNone(
            map_report_location("Library block 103", aliases={"Library block 103": "Missing"}),
        )

    def test_negative_edge_cost_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "non-negative"):
            astar_search({"Start": {"Goal": -1}, "Goal": {}}, "Start", "Goal")


if __name__ == "__main__":
    unittest.main()