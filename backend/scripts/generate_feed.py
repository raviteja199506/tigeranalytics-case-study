import argparse
import csv
import random
import sys
from datetime import date, timedelta
from pathlib import Path

CATEGORIES = ["Milk", "Bread", "Eggs", "Coffee", "Rice", "Pasta", "Apples", "Cheese", "Yogurt"]
SIZES = ["250g", "500g", "1kg", "1L", "2L", "6pk", "12pk"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a synthetic pricing feed CSV")
    parser.add_argument("output", type=Path)
    parser.add_argument("--stores", type=int, default=100)
    parser.add_argument("--skus", type=int, default=1_000)
    parser.add_argument("--days", type=int, default=1)
    parser.add_argument("--start", type=date.fromisoformat, default=date.today())
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    catalog = [
        (f"SKU-{n:06d}", f"{rng.choice(CATEGORIES)} {rng.choice(SIZES)}", rng.uniform(0.5, 40))
        for n in range(1, args.skus + 1)
    ]

    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Store ID", "SKU", "Product Name", "Price", "Date"])
        for day in range(args.days):
            price_date = (args.start + timedelta(days=day)).isoformat()
            for store in range(1, args.stores + 1):
                for sku, name, base_price in catalog:
                    price = base_price * rng.uniform(0.9, 1.1)
                    writer.writerow([f"ST{store:05d}", sku, name, f"{price:.2f}", price_date])

    rows = args.stores * args.skus * args.days
    sys.stdout.write(f"Wrote {rows:,} rows to {args.output}\n")


if __name__ == "__main__":
    main()
