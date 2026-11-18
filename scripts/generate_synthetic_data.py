"""
Generate a fully synthetic trip-level dataset for the Next-Visit Theo model
evaluation dashboard.

Nothing here comes from a real company. The schema mirrors the shape of a
typical casino-loyalty prediction table (one row per predicted next trip),
and the generating process is tuned so that the *kind* of patterns an
evaluation should surface (regression to the mean, small-denominator blow-ups,
segment-level bias) show up. All numbers are made up.

Usage:
    python scripts/generate_synthetic_data.py            # writes data/synthetic_trips.csv
    python scripts/generate_synthetic_data.py --seed 7   # different draw
"""
import argparse
import csv
from datetime import date, timedelta
from pathlib import Path

import numpy as np

TIERS = {
    #  name               share  median_theo  table_share
    "Chairman":          (0.03,  55_000,       0.80),
    "Black":             (0.10,   8_000,       0.60),
    "Platinum":          (0.33,   1_800,       0.40),
    "Red":               (0.55,     550,       0.25),
}


def generate(n: int, seed: int):
    rng = np.random.default_rng(seed)
    names = list(TIERS)
    shares = np.array([TIERS[t][0] for t in names])
    tier_idx = rng.choice(len(names), size=n, p=shares / shares.sum())

    rows = []
    start = date(2024, 1, 1)
    for i, ti in enumerate(tier_idx):
        tier = names[ti]
        _, median, table_share = TIERS[tier]
        game = "Table" if rng.random() < table_share else "Slot"

        # Booking lead time: most trips are booked within ~3 months, long tail to 240 days
        lead = int(min(240, rng.gamma(shape=1.6, scale=38)))

        # Each guest has an underlying "worth"; each trip is a noisy draw around it.
        typical = median * (1.5 if game == "Table" else 1.0)
        worth = typical * rng.lognormal(0, 0.7)
        s = 0.80 if game == "Table" else 0.60          # table play is more volatile
        actual = worth * rng.lognormal(-s * s / 2, s)  # mean-preserving trip noise

        # A slice of trips where the guest barely plays -> tiny denominators
        if rng.random() < 0.04:
            actual = rng.uniform(2, 40)

        # The "model" sees a noisy read of the guest's worth (history), and
        # shrinks toward the tier median -> regression to the mean.
        log_pred = 0.80 * np.log(worth * rng.lognormal(0, 0.35)) + 0.20 * np.log(typical)

        # Last-minute bookings carry less information -> noisier and optimistic
        if lead <= 15:
            log_pred += rng.normal(0.12, 0.40)
        # Entry tier (Red): model leans optimistic
        if ti == 3:
            log_pred += 0.15
        pred = float(np.exp(log_pred))

        visit = start + timedelta(days=int(rng.integers(0, 547)))
        rows.append({
            "trip_id": f"T{i + 1:05d}",
            "tier": tier,
            "game_type": game,
            "booking_lead_days": lead,
            "visit_month": visit.strftime("%Y-%m"),
            "predicted_theo": round(pred, 2),
            "actual_theo": round(float(actual), 2),
        })
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=8000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default=str(Path(__file__).resolve().parents[1] / "data" / "synthetic_trips.csv"))
    args = ap.parse_args()

    rows = generate(args.n, args.seed)
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows):,} rows -> {args.out}")


if __name__ == "__main__":
    main()
