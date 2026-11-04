# E1 run report

## Fill runs (foreground)
- omnijev-0.8b fill: exit=0 (log: runs/E1/scores/omnijev-0.8b.fill.log)
- omnijev-4b fill: exit=0 (log: runs/E1/scores/omnijev-4b.fill.log)
- analyze_e1.py: exit=0 (log: runs/E1/analyze.log)

## Row counts and duplicates
| File | Rows | Duplicate pair_ids |
|---|---|---|
| omnijev-0.8b.jsonl | 300 | 0 |
| omnijev-4b.jsonl | 300 | 0 |
| rsi-jev-4b.jsonl | 300 | 0 |
| imajev-9b.jsonl | 300 | 0 |

## Headline table (from runs/E1/analysis.md)
| Judge | agree by-construction | agree reference | hi-conf vs ref (cov) | gate | ECE | flip rate | mean P(first)-0.5 | single~pairwise |
|---|---|---|---|---|---|---|---|---|
| omnijev-0.8b | 0.687 (n=150) | 0.717 (n=120) | 0.842 (n=19) (0.158) | PASS | 0.077 | 0.333 | -0.031 | 0.707 |
| omnijev-4b | 0.900 (n=150) | 0.642 (n=120) | 1.000 (n=9) (0.075) | PASS | 0.104 | 0.583 | -0.130 | 0.780 |
| rsi-jev-4b | 0.773 (n=150) | 0.617 (n=120) | 0.879 (n=33) (0.275) | PASS | 0.126 | 0.303 | 0.020 | 0.710 |
| imajev-9b | 0.953 (n=150) | 0.717 (n=120) | 1.000 (n=14) (0.117) | PASS | 0.101 | 0.397 | -0.124 | 0.777 |

## By-construction agreement by severity (from analysis.md)
| Judge | moderate | obvious | subtle |
|---|---|---|---|
| omnijev-0.8b | 0.660 (n=50) | 0.880 (n=50) | 0.520 (n=50) |
| omnijev-4b | 0.980 (n=50) | 1.000 (n=50) | 0.720 (n=50) |
| rsi-jev-4b | 0.820 (n=50) | 0.980 (n=50) | 0.520 (n=50) |
| imajev-9b | 1.000 (n=50) | 1.000 (n=50) | 0.860 (n=50) |
