"""Unit tests for routing.py. Run:  python -m unittest discover tests"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from routing import nearest_neighbour, route_length, split_into_trips, two_opt  # noqa: E402

P = lambda x, y, name="": {"x": x, "y": y, "bin_id": name}      # tiny helper to make a point
DEPOT = P(0, 0, "D")


class RoutingTests(unittest.TestCase):
    def test_route_length_returns_to_depot(self):
        self.assertEqual(route_length(DEPOT, [P(3, 4)]), 10)       # 5 km out, 5 km back

    def test_nearest_neighbour_order(self):
        a, b, c = P(1, 0, "a"), P(5, 0, "b"), P(2, 0, "c")
        self.assertEqual([s["bin_id"] for s in nearest_neighbour(DEPOT, [b, a, c])], ["a", "c", "b"])

    def test_two_opt_uncrosses_a_square(self):
        # Corners of a square visited in a crossing (bow-tie) order...
        crossed = [P(0, 1, "1"), P(1, 0, "2"), P(1, 1, "3")]
        better = two_opt(DEPOT, crossed)
        self.assertLess(route_length(DEPOT, better), route_length(DEPOT, crossed))
        self.assertAlmostEqual(route_length(DEPOT, better), 4.0)   # ...becomes the 4 km perimeter

    def test_two_opt_never_makes_it_worse(self):
        stops = [P(x, (x * 7) % 5) for x in range(1, 9)]
        self.assertLessEqual(route_length(DEPOT, two_opt(DEPOT, stops)), route_length(DEPOT, stops))

    def test_split_respects_capacity(self):
        stops = [P(i, 0) for i in range(5)]
        trips = split_into_trips(stops, capacity=250, load_of=lambda s: 100)   # 2 bins per trip max
        self.assertEqual([len(t) for t in trips], [2, 2, 1])


if __name__ == "__main__":
    unittest.main()
