"""
generate_sample_data.py
Creates SYNTHETIC smart-bin readings on a made-up 12 km x 12 km city grid.
(In a real system each bin would have a fill-level sensor.) NOT real data.
"""

import csv
import random
from pathlib import Path

OUT = Path(__file__).parent / "data" / "bins.csv"
random.seed(8)


def main():
    OUT.parent.mkdir(exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["bin_id", "x_km", "y_km", "capacity_litres", "fill_pct"])
        for i in range(1, 61):                                        # 60 bins
            hotspot = random.random() < 0.4                           # 40% near the busy market area
            x = random.gauss(8, 1.2) if hotspot else random.uniform(0, 12)   # market cluster around (8, 8)
            y = random.gauss(8, 1.2) if hotspot else random.uniform(0, 12)
            fill = random.randint(55, 100) if hotspot else random.randint(5, 95)   # market bins fill faster
            w.writerow([f"B{i:02d}", round(min(max(x, 0), 12), 2), round(min(max(y, 0), 12), 2),
                        random.choice([240, 660, 1100]), fill])        # common wheelie-bin and skip sizes
    print("wrote SYNTHETIC data/bins.csv (60 bins)")


if __name__ == "__main__":
    main()
