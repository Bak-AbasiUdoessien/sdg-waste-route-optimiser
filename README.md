# Waste Collection Route Optimiser (SDG 11 + SDG 12)

Most collection trucks drive the same fixed round every day, stopping at half-empty bins and burning diesel. This project plans a smarter day. Using bin fill levels (as smart-bin sensors would report them), it:
1. picks only the bins that are **full enough** to be worth emptying,
2. orders them into a short route using **nearest-neighbour + 2-opt**,
3. splits the route into **truck loads** that respect the truck's capacity, and
4. compares kilometres, diesel and CO₂ with the fixed round, and draws a map.

**SDG targets covered:** 11.6 (city waste management), 12.5 (less waste) and 13.2 (lower emissions).

## Run it
```bash
python generate_sample_data.py               # SYNTHETIC: 60 bins on a 12 km x 12 km grid
python plan.py                               # empty bins at least 70% full, 8,000 L truck
python plan.py --threshold 60 --truck 6000
python -m unittest discover tests
```
Then open **`route_map.svg`** in a browser. Each trip has its own colour, and you can hover over a bin to see its fill level. Everything uses the Python standard library.

## The algorithms (`routing.py`)
| Step | Idea | Why |
|---|---|---|
| Nearest neighbour | Always drive to the closest unvisited bin | A fast, decent first draft |
| 2-opt | Reverse any section of the route if that makes it shorter, and repeat until nothing improves | Removes crossing paths. It's the classic local search for the Travelling Salesman Problem |
| Route first, cluster second | Walk the optimised tour and return to the depot when the truck is full, then 2-opt each trip again | A simple way to handle truck capacity |

The output table separates **two** sources of savings: a smarter visiting order (shown by routing *all* bins smartly) and skipping bins that aren't full yet.

## Limitations
- Distances are straight lines. Real roads need a road network, for example OpenStreetMap via `osmnx`.
- A bin at 69% today may overflow tomorrow. A real system would forecast fill rates.
- 2-opt finds a good route, not a guaranteed best one. Google OR-Tools can solve the full Vehicle Routing Problem.
- The diesel use (0.5 L/km) is an assumption, so adjust it for your trucks.

## ⚠️ Data note
The bins, positions and fill levels are **invented**.
