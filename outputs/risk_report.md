# Risk Tier Classification Report

Transactions analysed: **538** | High-risk anomalies: **37** | Critical patterns: **12**

## Tier summary

| Tier | Transactions | % of total | Recommended action |
|---|---|---|---|
| High | 37 | 6.9% | Hold/step-up verify immediately; contact the account holder; escalate patterns to the fraud/risk team within 24h. |
| Medium | 4 | 0.7% | Queue for analyst review within 3 working days; auto-request device or location confirmation from the customer. |
| Low | 497 | 92.4% | No action; keep in routine monitoring and use for rule-tuning feedback. |

## Most common rules among High-risk transactions

- `amount_outlier`: 28 of 37 high-risk transactions
- `foreign`: 22 of 37 high-risk transactions
- `off_hours`: 19 of 37 high-risk transactions
- `new_device`: 18 of 37 high-risk transactions
- `velocity`: 12 of 37 high-risk transactions
- `round_amount`: 9 of 37 high-risk transactions

## Critical patterns (accounts with 2+ high-risk transactions)

| Account | High-risk txns | Total amount | Window | Rules seen |
|---|---|---|---|---|
| ACC-012 | 4 | 77,234.96 | 2026-03-13 02:24 to 2026-03-16 02:27 | amount_outlier, foreign, off_hours |
| ACC-003 | 3 | 49,527.19 | 2026-03-09 17:15 to 2026-03-09 17:31 | amount_outlier, new_device, velocity |
| ACC-006 | 3 | 41,685.89 | 2026-03-08 15:29 to 2026-03-10 15:20 | amount_outlier, foreign |
| ACC-009 | 3 | 33,918.18 | 2026-02-12 03:27 to 2026-02-14 03:26 | amount_outlier, new_device, off_hours |
| ACC-004 | 3 | 33,000.00 | 2026-03-03 03:12 to 2026-03-05 03:17 | amount_outlier, off_hours, round_amount |
| ACC-010 | 3 | 18,000.00 | 2026-03-21 10:47 to 2026-03-23 10:21 | amount_outlier, foreign, round_amount |
| ACC-007 | 3 | 15,000.00 | 2026-02-16 18:12 to 2026-02-18 18:25 | foreign, new_device, round_amount |
| ACC-002 | 3 | 13,512.38 | 2026-03-10 09:32 to 2026-03-12 09:41 | amount_outlier, foreign, new_device |
| ACC-001 | 3 | 13,462.41 | 2026-02-24 01:20 to 2026-02-26 01:30 | amount_outlier, new_device, off_hours |
| ACC-008 | 3 | 9,310.60 | 2026-03-01 02:16 to 2026-03-01 02:32 | amount_outlier, off_hours, velocity |
| ACC-005 | 3 | 6,726.42 | 2026-03-07 01:09 to 2026-03-07 01:25 | foreign, off_hours, velocity |
| ACC-011 | 3 | 5,059.78 | 2026-03-02 13:16 to 2026-03-02 13:32 | foreign, new_device, velocity |

## Recommendations

1. Prioritise the top 3 critical patterns by value for same-day review.
2. Add step-up authentication when a new device coincides with a large or foreign transaction (the most common high-risk combination).
3. Rate-limit bursts of 3+ payments within 30 minutes on one account.
4. Review Medium-tier cases weekly and feed confirmed false positives back into the rule weights.
