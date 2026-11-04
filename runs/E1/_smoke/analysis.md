# E1 analysis

Labels: {'by_construction': 4, 'reference': 6}

| Judge | agree by-construction | agree reference | hi-conf vs ref (cov) | gate | ECE | flip rate | mean P(first)-0.5 | single~pairwise |
|---|---|---|---|---|---|---|---|---|
| omnijev-0.8b | 1.000 (n=4) | 0.833 (n=6) | 1.000 (n=4) (0.667) | PASS | 0.021 | 0.333 | -0.026 | 1.000 |

## omnijev-0.8b
scored 6 pairs, 0 rows with errors; mean pairwise latency 0.473 s

- **by_construction**: overall 1.000 (n=4); high-conf 1.000 (n=4), coverage 1.000
  - by_source: frontier_graded 1.000 (n=4)
  - by_flaw_severity: obvious 1.000 (n=4)
- **reference**: overall 0.833 (n=6); high-conf 1.000 (n=4), coverage 0.667
  - by_source: frontier_graded 0.833 (n=6)
  - by_flaw_severity: None 0.500 (n=2), obvious 1.000 (n=4)

Calibration vs reference (ECE 0.021); plot `calibration_omnijev-0.8b.png`

| bin | n | mean conf | accuracy |
|---|---|---|---|
| 0.50-0.55 | 2 | 0.522 | 0.500 |
| 0.55-0.60 | 0 | - | - |
| 0.60-0.65 | 0 | - | - |
| 0.65-0.70 | 0 | - | - |
| 0.70-0.75 | 0 | - | - |
| 0.75-0.80 | 0 | - | - |
| 0.80-0.85 | 0 | - | - |
| 0.85-0.90 | 0 | - | - |
| 0.90-0.95 | 0 | - | - |
| 0.95-1.00 | 4 | 0.980 | 1.000 |
