# E1 pairs QA

- staging folders: 200; pairs assembled: 200 (graded 150, hard 50)
- graded by severity: {'obvious': 50, 'moderate': 50, 'subtle': 50}
- side balance (intended_better, graded): a=84 b=66
- flagged pairs: 0; pairs with font failures: 0

## Pixel diff (strong vs flawed, top 800px)

| severity | n | median % changed | min % changed | median mean-abs-diff | min mean-abs-diff |
|---|---|---|---|---|---|
| obvious | 50 | 41.41 | 8.50 | 36.03 | 10.54 |
| moderate | 50 | 90.12 | 14.50 | 37.49 | 10.41 |
| subtle | 50 | 21.09 | 5.83 | 18.68 | 6.95 |

Flag threshold: <0.5% pixels changed (channel diff > 8).

## Flagged pairs

(none)

## Font failures

(none)
