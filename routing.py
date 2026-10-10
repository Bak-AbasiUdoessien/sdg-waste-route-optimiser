"""
routing.py  -  Route-planning algorithms, kept separate so they are easy to test.
Points are dicts with 'x' and 'y' in kilometres on a flat city map.
"""

import math


def dist(a, b):
    """Straight-line distance between two points (Pythagoras)."""
    return math.hypot(a["x"] - b["x"], a["y"] - b["y"])      # hypot(dx, dy) = sqrt(dx² + dy²)


def route_length(depot, stops):
    """Total km: depot -> every stop in order -> back to depot."""
    if not stops:
        return 0.0
    path = [depot] + stops + [depot]
    return sum(dist(path[i], path[i + 1]) for i in range(len(path) - 1))   # add up each leg


def nearest_neighbour(depot, stops):
    """
    Greedy first draft: from where you are, always drive to the closest unvisited bin.
    Fast and simple, but it often leaves some long, crossing legs at the end.
    """
    remaining = list(stops)
    route, here = [], depot
    while remaining:
        nxt = min(remaining, key=lambda s: dist(here, s))     # closest unvisited stop
        route.append(nxt)
        remaining.remove(nxt)
        here = nxt
    return route


def two_opt(depot, route):
    """
    Improve a route by "uncrossing" it. Take any two legs and reverse the section
    between them; keep the change if the route gets shorter. Repeat until no
    reversal helps. This is the classic 2-opt local search.
    """
    best = list(route)
    improved = True
    while improved:                                            # keep sweeping until a full pass finds nothing
        improved = False
        for i in range(len(best) - 1):
            for j in range(i + 1, len(best)):
                candidate = best[:i] + best[i:j + 1][::-1] + best[j + 1:]   # [::-1] reverses the middle section
                if route_length(depot, candidate) < route_length(depot, best) - 1e-9:   # 1e-9 ignores rounding noise
                    best, improved = candidate, True
    return best


def split_into_trips(route, capacity, load_of):
    """
    Walk along the optimised route and start a new trip (back to the depot to unload)
    whenever the next bin would overfill the truck. 'Route first, cluster second'.
    """
    trips, current, load = [], [], 0.0
    for stop in route:
        need = load_of(stop)                                   # how much this bin adds to the truck
        if current and load + need > capacity:                 # truck would overflow -> close this trip
            trips.append(current)
            current, load = [], 0.0
        current.append(stop)
        load += need
    if current:
        trips.append(current)                                  # the last, partly full trip
    return trips
