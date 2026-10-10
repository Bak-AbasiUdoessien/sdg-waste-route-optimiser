"""
plan.py  -  Waste Collection Route Optimiser (SDG 11: Sustainable Cities, SDG 12)
Picks only the bins that are full enough to be worth emptying today, plans a short
route through them (nearest-neighbour + 2-opt), splits it into truck loads, and
compares the distance (and diesel, and CO2) with a fixed, unoptimised round.

Run:
    python generate_sample_data.py
    python plan.py                              # empty bins >= 70% full, 8,000-litre truck
    python plan.py --threshold 60 --truck 6000
"""

import argparse
import csv
import sys
from pathlib import Path

from routing import nearest_neighbour, route_length, split_into_trips, two_opt

ROOT = Path(__file__).parent
DEPOT = {"bin_id": "DEPOT", "x": 1.0, "y": 1.0}       # where trucks start and unload (made-up position)
DIESEL_L_PER_KM = 0.5                                  # assumption for a loaded refuse truck - adjust
DIESEL_KG_CO2_PER_L = 2.69                             # approx. US EPA: 10,180 g CO2 per US gallon / 3.785 L


def load_bins():
    with open(ROOT / "data" / "bins.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return [{"bin_id": r["bin_id"], "x": float(r["x_km"]), "y": float(r["y_km"]),
             "capacity": float(r["capacity_litres"]), "fill": float(r["fill_pct"])} for r in rows]


def litres(b):
    """Waste currently in a bin."""
    return b["capacity"] * b["fill"] / 100


def total_km(trips):
    return sum(route_length(DEPOT, t) for t in trips)        # each trip starts and ends at the depot


def svg(trips, skipped, path):
    """Draw the plan: each trip in its own colour, skipped bins grey, depot black."""
    scale, pad = 45, 20                                      # 45 px per km on a 12 km map
    to_px = lambda p: (round(pad + p["x"] * scale, 1), round(pad + (12 - p["y"]) * scale, 1))  # y flipped: north up
    colours = ["#d1495b", "#00798c", "#edae49", "#30638e", "#66a182", "#8d5a97", "#e07a5f", "#3d405b"]
    size = 12 * scale + 2 * pad
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size + 30}" font-family="sans-serif" font-size="11">',
           '<rect width="100%" height="100%" fill="white"/>']
    for b in skipped:
        x, y = to_px(b)
        out.append(f'<circle cx="{x}" cy="{y}" r="3" fill="#bbb"><title>{b["bin_id"]} {b["fill"]:.0f}% - skipped</title></circle>')
    for i, trip in enumerate(trips):
        colour = colours[i % len(colours)]
        pts = " ".join("%s,%s" % to_px(p) for p in [DEPOT] + trip + [DEPOT])   # "x,y x,y ..." for the polyline
        out.append(f'<polyline points="{pts}" fill="none" stroke="{colour}" stroke-width="2" opacity="0.8"/>')
        for b in trip:
            x, y = to_px(b)
            out.append(f'<circle cx="{x}" cy="{y}" r="5" fill="{colour}"><title>{b["bin_id"]} {b["fill"]:.0f}% '
                       f'({litres(b):.0f} L) - trip {i + 1}</title></circle>')
    dx, dy = to_px(DEPOT)
    out.append(f'<rect x="{dx - 7}" y="{dy - 7}" width="14" height="14" fill="black"/>')
    out.append(f'<text x="{pad}" y="{size + 18}">■ depot  ● bins on today\'s trips (one colour per trip)  '
               f'<tspan fill="#999">● skipped (not full enough)</tspan></text></svg>')
    path.write_text("\n".join(out), encoding="utf-8")


def main():
    p = argparse.ArgumentParser(description="Plan today's waste collection.")
    p.add_argument("--threshold", type=float, default=70, help="empty bins at or above this %% full (default 70)")
    p.add_argument("--truck", type=float, default=8000, help="truck capacity in litres (default 8000)")
    a = p.parse_args()
    if not (ROOT / "data" / "bins.csv").exists():
        sys.exit("No data. Run: python generate_sample_data.py")

    bins = load_bins()
    if any(litres(b) > a.truck for b in bins):
        sys.exit("A single bin holds more than the truck - increase --truck")
    due = [b for b in bins if b["fill"] >= a.threshold]
    skipped = [b for b in bins if b["fill"] < a.threshold]
    print(f"{len(due)} of {len(bins)} bins are at least {a.threshold:g}% full and will be emptied today")

    # Old way: visit EVERY bin, in ID order, every day.
    fixed = split_into_trips(bins, a.truck, litres)
    # New way: only the full bins, in a smart order.
    draft = nearest_neighbour(DEPOT, due)
    tour = two_opt(DEPOT, draft)
    trips = [two_opt(DEPOT, t) for t in split_into_trips(tour, a.truck, litres)]   # polish each trip on its own too

    # Same bins as the fixed round but in a smart order -> shows the routing gain on its own.
    all_smart = split_into_trips(two_opt(DEPOT, nearest_neighbour(DEPOT, bins)), a.truck, litres)
    rows = [("Fixed round (all bins, ID order)", fixed),
            ("All bins, nearest-neighbour + 2-opt", all_smart),
            ("Full bins, nearest-neighbour", split_into_trips(draft, a.truck, litres)),
            ("Full bins, nearest-neighbour + 2-opt", trips)]   # trips = 2-opt on the tour, then on each trip
    print(f"\n{'Plan':<40}{'Trips':>6}{'km':>8}{'Diesel L':>10}{'CO2 kg':>9}")
    for name, t in rows:
        km = total_km(t)
        print(f"{name:<40}{len(t):>6}{km:>8.1f}{km * DIESEL_L_PER_KM:>10.1f}{km * DIESEL_L_PER_KM * DIESEL_KG_CO2_PER_L:>9.1f}")
    saved = total_km(fixed) - total_km(trips)
    print(f"\nSmart plan saves {saved:.1f} km today ({100 * saved / total_km(fixed):.0f}% less driving)")
    route_gain = total_km(fixed) - total_km(all_smart)                 # from better ordering alone
    print(f"  of which {route_gain:.1f} km comes from a better order, the rest from skipping emptier bins")

    print("\nToday's trips:")
    for i, t in enumerate(trips, start=1):
        load = sum(litres(b) for b in t)
        print(f"  Trip {i}: {route_length(DEPOT, t):5.1f} km, {load:6.0f} L ({100 * load / a.truck:.0f}% full) "
              f"-> {' > '.join(b['bin_id'] for b in t)}")
    svg(trips, skipped, ROOT / "route_map.svg")
    print("\nSaved route_map.svg (open it in a browser and hover over the dots)")


if __name__ == "__main__":
    main()
