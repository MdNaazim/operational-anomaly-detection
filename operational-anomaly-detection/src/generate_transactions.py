"""Generate a SYNTHETIC transaction dataset (520 records) with injected anomalies.

Ground-truth labels are written to a separate file (data/injected_labels.csv) and are NOT used by the detector;
they are only used afterwards to check what the rules caught.
Run: python src/generate_transactions.py
"""
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
rng = np.random.default_rng(11)
N_ACCOUNTS = 40
accounts = [f"ACC-{i:03d}" for i in range(1, N_ACCOUNTS + 1)]
scale = dict(zip(accounts, rng.integers(400, 3000, N_ACCOUNTS)))          # typical spend per account
devices = {a: [f"DEV-{a[-3:]}-A"] for a in accounts}
MERCH = ["Grocery", "Fuel", "Electronics", "Travel", "Dining", "Utilities", "Fashion"]
CHANNEL = ["POS", "Online", "UPI"]
BASE = pd.Timestamp("2026-02-01")

rows, labels = [], []


def add(acc, ts, amount, country="IN", device=None, label="normal", pattern=""):
    rows.append(dict(account_id=acc, timestamp=ts, merchant_category=rng.choice(MERCH), channel=rng.choice(CHANNEL),
                     amount=round(float(amount), 2), country=country, device_id=device or devices[acc][0]))
    labels.append((label, pattern))


# --- 1) Normal activity (483 records, plus 18 benign edge cases below): daytime, domestic, known device, typical amounts ---
for _ in range(483):
    a = rng.choice(accounts)
    ts = BASE + pd.Timedelta(days=int(rng.integers(0, 56)), hours=int(rng.integers(8, 22)), minutes=int(rng.integers(0, 60)))
    amt = scale[a] * np.clip(rng.lognormal(0, 0.35), 0.4, 2.0) + rng.random()   # +random cents: never a round number
    add(a, ts, amt)

# --- 2) Benign "noise" that should land in Low/Medium tiers, not High ---
for i in range(8):     # late-night legitimate purchase (one weak signal)
    a = accounts[20 + i]
    add(a, BASE + pd.Timedelta(days=int(rng.integers(0, 56)), hours=int(rng.integers(1, 4)), minutes=7), scale[a] * 1.1 + 0.37)
for i in range(6):     # legitimate travel: foreign transaction in daytime (one weak signal)
    a = accounts[28 + i]
    add(a, BASE + pd.Timedelta(days=int(rng.integers(0, 56)), hours=int(rng.integers(10, 19)), minutes=12),
        scale[a] * 1.2 + 0.21, country=rng.choice(["AE", "SG"]))
for i in range(4):     # new phone used late at night (two weak signals -> Medium tier)
    a = accounts[34 + i]
    add(a, BASE + pd.Timedelta(days=int(rng.integers(0, 56)), hours=2, minutes=41), scale[a] * 0.9 + 0.58,
        device=f"DEV-{a[-3:]}-NEWPHONE")

# --- 3) Injected high-risk scenarios: 12 accounts, 37 transactions in total ---
# (account index, number of txns, traits per txn, description)
SCENARIOS = [
    (0, 3, ("big", "night", "newdev"), "high-value night purchases from a new device"),
    (1, 3, ("foreign", "newdev", "big"), "large foreign transactions on a new device"),
    (2, 3, ("burst", "newdev", "big"), "rapid burst of large payments from a new device"),
    (3, 3, ("big", "round", "night"), "round-number large night transfers"),
    (4, 3, ("foreign", "night", "burst"), "foreign night-time burst"),
    (5, 3, ("big", "foreign"), "large foreign card-present spend"),
    (6, 3, ("round", "newdev", "foreign"), "round foreign payments from a new device"),
    (7, 3, ("burst", "big", "night"), "night-time burst of large payments"),
    (8, 3, ("newdev", "night", "big"), "device change followed by large night spend"),
    (9, 3, ("foreign", "big", "round"), "round-number foreign cash-out pattern"),
    (10, 3, ("burst", "foreign", "newdev"), "foreign burst on a new device"),
    (11, 4, ("big", "night", "foreign"), "repeated large foreign night spend"),
]
for idx, (acc_i, n, traits, desc) in enumerate(SCENARIOS):
    a = accounts[acc_i]
    start = BASE + pd.Timedelta(days=int(rng.integers(3, 50)))
    base_hour = int(rng.integers(1, 4)) if "night" in traits else int(rng.integers(9, 20))
    base_min = int(rng.integers(0, 20))
    for k in range(n):
        # burst: same hour, 8 minutes apart; otherwise: one transaction per day
        gap = k * 8 if "burst" in traits else k * 1440 + int(rng.integers(0, 30))
        ts = start.normalize() + pd.Timedelta(hours=base_hour, minutes=base_min + gap)
        amt = scale[a] * rng.uniform(5.5, 8.0) if "big" in traits else scale[a] * rng.uniform(1.0, 1.5)
        if "round" in traits:
            amt = max(5000, round(amt, -3))
        country = rng.choice(["AE", "SG", "GB", "US"]) if "foreign" in traits else "IN"
        dev = f"DEV-NEW-{acc_i:02d}-{k}" if "newdev" in traits else None
        add(a, ts, amt, country, dev, label="injected_anomaly", pattern=f"P{idx + 1:02d}: {desc}")

df = pd.DataFrame(rows)
lab = pd.DataFrame(labels, columns=["injected_label", "injected_pattern"])
df = pd.concat([df, lab], axis=1).sort_values("timestamp").reset_index(drop=True)
df.insert(0, "txn_id", [f"TXN-{i:04d}" for i in range(1, len(df) + 1)])
df.drop(columns=["injected_label", "injected_pattern"]).to_csv(ROOT / "data/transactions.csv", index=False)
df[["txn_id", "injected_label", "injected_pattern"]].to_csv(ROOT / "data/injected_labels.csv", index=False)
print(f"transactions={len(df)}  injected anomalies={(df.injected_label != 'normal').sum()}")
