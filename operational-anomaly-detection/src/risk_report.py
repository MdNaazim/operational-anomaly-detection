"""Build the risk-tier classification report (markdown) and charts from detector outputs.
Run after detect_anomalies.py:  python src/risk_report.py
"""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
df = pd.read_csv(ROOT / "outputs/scored_transactions.csv", parse_dates=["timestamp"])
crit = pd.read_csv(ROOT / "outputs/critical_patterns.csv")
tiers = pd.read_csv(ROOT / "outputs/risk_tier_summary.csv")
high = df[df.risk_tier == "High"]

ACTIONS = {
    "High": "Hold/step-up verify immediately; contact the account holder; escalate patterns to the fraud/risk team within 24h.",
    "Medium": "Queue for analyst review within 3 working days; auto-request device or location confirmation from the customer.",
    "Low": "No action; keep in routine monitoring and use for rule-tuning feedback.",
}
rule_counts = high[["amount_outlier", "off_hours", "foreign", "new_device", "velocity", "round_amount"]].sum().sort_values(ascending=False)

lines = ["# Risk Tier Classification Report", "",
         f"Transactions analysed: **{len(df)}** | High-risk anomalies: **{len(high)}** | Critical patterns: **{len(crit)}**", "",
         "## Tier summary", "", "| Tier | Transactions | % of total | Recommended action |", "|---|---|---|---|"]
for r in tiers.itertuples():
    lines.append(f"| {r.risk_tier} | {r.transactions} | {r.pct_of_total}% | {ACTIONS[r.risk_tier]} |")
lines += ["", "## Most common rules among High-risk transactions", ""]
lines += [f"- `{k}`: {v} of {len(high)} high-risk transactions" for k, v in rule_counts.items()]
lines += ["", "## Critical patterns (accounts with 2+ high-risk transactions)", "",
          "| Account | High-risk txns | Total amount | Window | Rules seen |", "|---|---|---|---|---|"]
for r in crit.itertuples():
    lines.append(f"| {r.account_id} | {r.high_risk_txns} | {r.total_amount:,.2f} | {r.first_seen[:16]} to {r.last_seen[:16]} | {r.rules_seen} |")
lines += ["", "## Recommendations", "",
          "1. Prioritise the top 3 critical patterns by value for same-day review.",
          "2. Add step-up authentication when a new device coincides with a large or foreign transaction (the most common high-risk combination).",
          "3. Rate-limit bursts of 3+ payments within 30 minutes on one account.",
          "4. Review Medium-tier cases weekly and feed confirmed false positives back into the rule weights.", ""]
(ROOT / "outputs/risk_report.md").write_text("\n".join(lines))

fig, ax = plt.subplots(1, 3, figsize=(16, 4.5))
colors = {"High": "#d62728", "Medium": "#ff7f0e", "Low": "#2ca02c"}
ax[0].bar(tiers.risk_tier, tiers.transactions, color=[colors[t] for t in tiers.risk_tier])
ax[0].set_title("Transactions by risk tier")
for i, v in enumerate(tiers.transactions):
    ax[0].text(i, v, str(v), ha="center", va="bottom")
for t, g in df.groupby("risk_tier"):
    ax[1].scatter(g.timestamp, g.amount, s=14, alpha=.7, color=colors[t], label=t)
ax[1].set_yscale("log"); ax[1].legend(); ax[1].set_title("Amount over time by tier (log scale)"); ax[1].tick_params(axis="x", rotation=30)
ax[2].barh(crit.account_id, crit.total_amount, color="#d62728"); ax[2].invert_yaxis()
ax[2].set_title("Critical patterns: total high-risk value")
plt.tight_layout(); plt.savefig(ROOT / "docs/risk_overview.png", dpi=130)
print("report + chart saved")
