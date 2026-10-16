"""Rule-based, hypothesis-driven anomaly detection and risk-tier classification (pandas + NumPy).

Hypotheses (each is a rule with a weight):
  H1 amount_outlier : amount is >= 3.5x the account's own median transaction
  H2 off_hours      : transaction between 00:00 and 04:59
  H3 foreign        : transaction country differs from the account's home country (IN)
  H4 new_device     : device never seen in the account's first-seen device list
  H5 velocity       : >= 3 transactions on one account within 30 minutes
  H6 round_amount   : amount is a multiple of 1,000 and >= 5,000
Risk score = sum of weights of triggered rules.  Tiers: High >= 60, Medium 30-59, Low < 30.
A "critical pattern" = an account with 2+ High-risk transactions.

Run: python src/detect_anomalies.py
"""
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEIGHTS = {"amount_outlier": 35, "off_hours": 20, "foreign": 25, "new_device": 20, "velocity": 20, "round_amount": 15}
HIGH, MEDIUM = 60, 30
HOME = "IN"

df = pd.read_csv(ROOT / "data/transactions.csv", parse_dates=["timestamp"]).sort_values("timestamp").reset_index(drop=True)

# H1: amount relative to the account's own median (median is robust to a few extreme values)
df["amount_vs_median"] = (df["amount"] / df.groupby("account_id")["amount"].transform("median")).round(2)
df["amount_outlier"] = df["amount_vs_median"] >= 3.5

df["off_hours"] = df["timestamp"].dt.hour < 5
df["foreign"] = df["country"] != HOME

# H4: a device is "known" if it is the account's most frequently used device
top_device = df.groupby("account_id")["device_id"].agg(lambda s: s.value_counts().index[0])
df["new_device"] = df["device_id"] != df["account_id"].map(top_device)

# H5: >= 3 txns on the same account within a 30-minute window (centred count)
vel = np.zeros(len(df), dtype=bool)
for acc, g in df.groupby("account_id"):
    t = g["timestamp"].values.astype("datetime64[m]").astype(int)
    for pos, idx in enumerate(g.index):
        vel[idx] = (np.abs(t - t[pos]) <= 30).sum() >= 3
df["velocity"] = vel

df["round_amount"] = (df["amount"] % 1000 == 0) & (df["amount"] >= 5000)

rules = list(WEIGHTS)
df["risk_score"] = sum(df[r].astype(int) * w for r, w in WEIGHTS.items())
df["risk_tier"] = np.select([df["risk_score"] >= HIGH, df["risk_score"] >= MEDIUM], ["High", "Medium"], "Low")
df["triggered_rules"] = df[rules].apply(lambda r: ", ".join(k for k in rules if r[k]), axis=1)

out = ROOT / "outputs"
out.mkdir(exist_ok=True)
df.to_csv(out / "scored_transactions.csv", index=False)
high = df[df["risk_tier"] == "High"].sort_values(["account_id", "timestamp"])
high.to_csv(out / "high_risk_anomalies.csv", index=False)

# Critical patterns: accounts with 2+ high-risk transactions
crit = (high.groupby("account_id")
        .agg(high_risk_txns=("txn_id", "count"), total_amount=("amount", "sum"),
             first_seen=("timestamp", "min"), last_seen=("timestamp", "max"),
             rules_seen=("triggered_rules", lambda s: ", ".join(sorted(set(", ".join(s).split(", ")))))).reset_index())
crit = crit[crit["high_risk_txns"] >= 2].sort_values("total_amount", ascending=False)
crit["total_amount"] = crit["total_amount"].round(2)
crit.to_csv(out / "critical_patterns.csv", index=False)

tiers = df["risk_tier"].value_counts().reindex(["High", "Medium", "Low"]).fillna(0).astype(int)
tier_tbl = pd.DataFrame({"risk_tier": tiers.index, "transactions": tiers.values,
                         "pct_of_total": (100 * tiers.values / len(df)).round(1)})
tier_tbl.to_csv(out / "risk_tier_summary.csv", index=False)

print(f"Transactions analysed : {len(df)}")
print(tier_tbl.to_string(index=False))
print(f"High-risk anomalies   : {len(high)}")
print(f"Critical patterns     : {len(crit)} accounts with 2+ high-risk transactions")

# Detection check against injected labels (synthetic data only)
lab = pd.read_csv(ROOT / "data/injected_labels.csv")
chk = df.merge(lab, on="txn_id")
inj = chk["injected_label"] == "injected_anomaly"
flag = chk["risk_tier"] == "High"
print(f"\nCheck vs injected labels: caught {(inj & flag).sum()}/{inj.sum()} injected anomalies, "
      f"{(~inj & flag).sum()} false alarms in High tier, {((chk['risk_tier'] == 'Medium') & ~inj).sum()} normal txns in Medium")
