# E1 analysis

Labels: {'by_construction': 150, 'reference': 120}

| Judge | agree by-construction | agree reference | hi-conf vs ref (cov) | gate | ECE | flip rate | mean P(first)-0.5 | single~pairwise |
|---|---|---|---|---|---|---|---|---|
| omnijev-0.8b | 0.687 (n=150) | 0.717 (n=120) | 0.842 (n=19) (0.158) | PASS | 0.077 | 0.333 | -0.031 | 0.707 |
| omnijev-4b | 0.900 (n=150) | 0.642 (n=120) | 1.000 (n=9) (0.075) | PASS | 0.104 | 0.583 | -0.130 | 0.780 |
| rsi-jev-4b | 0.773 (n=150) | 0.617 (n=120) | 0.879 (n=33) (0.275) | PASS | 0.126 | 0.303 | 0.020 | 0.710 |
| imajev-9b | 0.953 (n=150) | 0.717 (n=120) | 1.000 (n=14) (0.117) | PASS | 0.101 | 0.397 | -0.124 | 0.777 |

## omnijev-0.8b
scored 300 pairs, 0 rows with errors; mean pairwise latency 0.281 s

- **by_construction**: overall 0.687 (n=150); high-conf 1.000 (n=12), coverage 0.080
  - by_source: frontier_graded 0.687 (n=150)
  - by_flaw_severity: moderate 0.660 (n=50), obvious 0.880 (n=50), subtle 0.520 (n=50)
- **reference**: overall 0.717 (n=120); high-conf 0.842 (n=19), coverage 0.158
  - by_source: frontier_graded 0.800 (n=20), frontier_hard 0.650 (n=40), small_model 0.733 (n=60)
  - by_flaw_severity: None 0.700 (n=100), moderate 0.714 (n=7), obvious 1.000 (n=7), subtle 0.667 (n=6)

Calibration vs reference (ECE 0.077); plot `calibration_omnijev-0.8b.png`

| bin | n | mean conf | accuracy |
|---|---|---|---|
| 0.50-0.55 | 25 | 0.524 | 0.640 |
| 0.55-0.60 | 22 | 0.571 | 0.591 |
| 0.60-0.65 | 21 | 0.629 | 0.714 |
| 0.65-0.70 | 16 | 0.671 | 0.750 |
| 0.70-0.75 | 8 | 0.727 | 0.750 |
| 0.75-0.80 | 9 | 0.775 | 0.889 |
| 0.80-0.85 | 11 | 0.820 | 0.727 |
| 0.85-0.90 | 3 | 0.879 | 1.000 |
| 0.90-0.95 | 2 | 0.929 | 1.000 |
| 0.95-1.00 | 3 | 0.965 | 1.000 |

## omnijev-4b
scored 300 pairs, 0 rows with errors; mean pairwise latency 1.629 s

- **by_construction**: overall 0.900 (n=150); high-conf 1.000 (n=26), coverage 0.173
  - by_source: frontier_graded 0.900 (n=150)
  - by_flaw_severity: moderate 0.980 (n=50), obvious 1.000 (n=50), subtle 0.720 (n=50)
- **reference**: overall 0.642 (n=120); high-conf 1.000 (n=9), coverage 0.075
  - by_source: frontier_graded 0.900 (n=20), frontier_hard 0.625 (n=40), small_model 0.567 (n=60)
  - by_flaw_severity: None 0.590 (n=100), moderate 1.000 (n=7), obvious 1.000 (n=7), subtle 0.667 (n=6)

Calibration vs reference (ECE 0.104); plot `calibration_omnijev-4b.png`

| bin | n | mean conf | accuracy |
|---|---|---|---|
| 0.50-0.55 | 37 | 0.521 | 0.486 |
| 0.55-0.60 | 25 | 0.572 | 0.440 |
| 0.60-0.65 | 21 | 0.628 | 0.619 |
| 0.65-0.70 | 18 | 0.672 | 0.944 |
| 0.70-0.75 | 7 | 0.726 | 0.857 |
| 0.75-0.80 | 3 | 0.779 | 1.000 |
| 0.80-0.85 | 5 | 0.822 | 1.000 |
| 0.85-0.90 | 2 | 0.875 | 1.000 |
| 0.90-0.95 | 2 | 0.935 | 1.000 |
| 0.95-1.00 | 0 | - | - |

## rsi-jev-4b
scored 300 pairs, 0 rows with errors; mean pairwise latency 0.647 s

- **by_construction**: overall 0.773 (n=150); high-conf 0.950 (n=60), coverage 0.400
  - by_source: frontier_graded 0.773 (n=150)
  - by_flaw_severity: moderate 0.820 (n=50), obvious 0.980 (n=50), subtle 0.520 (n=50)
- **reference**: overall 0.617 (n=120); high-conf 0.879 (n=33), coverage 0.275
  - by_source: frontier_graded 0.750 (n=20), frontier_hard 0.550 (n=40), small_model 0.617 (n=60)
  - by_flaw_severity: None 0.590 (n=100), moderate 0.714 (n=7), obvious 1.000 (n=7), subtle 0.500 (n=6)

Calibration vs reference (ECE 0.126); plot `calibration_rsi-jev-4b.png`

| bin | n | mean conf | accuracy |
|---|---|---|---|
| 0.50-0.55 | 20 | 0.522 | 0.300 |
| 0.55-0.60 | 12 | 0.571 | 0.333 |
| 0.60-0.65 | 19 | 0.620 | 0.579 |
| 0.65-0.70 | 14 | 0.673 | 0.714 |
| 0.70-0.75 | 8 | 0.724 | 0.625 |
| 0.75-0.80 | 14 | 0.778 | 0.643 |
| 0.80-0.85 | 10 | 0.825 | 0.600 |
| 0.85-0.90 | 7 | 0.877 | 1.000 |
| 0.90-0.95 | 6 | 0.936 | 1.000 |
| 0.95-1.00 | 10 | 0.970 | 1.000 |

## imajev-9b
scored 300 pairs, 0 rows with errors; mean pairwise latency 2.575 s

- **by_construction**: overall 0.953 (n=150); high-conf 1.000 (n=68), coverage 0.453
  - by_source: frontier_graded 0.953 (n=150)
  - by_flaw_severity: moderate 1.000 (n=50), obvious 1.000 (n=50), subtle 0.860 (n=50)
- **reference**: overall 0.717 (n=120); high-conf 1.000 (n=14), coverage 0.117
  - by_source: frontier_graded 0.950 (n=20), frontier_hard 0.675 (n=40), small_model 0.667 (n=60)
  - by_flaw_severity: None 0.670 (n=100), moderate 1.000 (n=7), obvious 1.000 (n=7), subtle 0.833 (n=6)

Calibration vs reference (ECE 0.101); plot `calibration_imajev-9b.png`

| bin | n | mean conf | accuracy |
|---|---|---|---|
| 0.50-0.55 | 34 | 0.526 | 0.471 |
| 0.55-0.60 | 20 | 0.575 | 0.600 |
| 0.60-0.65 | 11 | 0.625 | 0.818 |
| 0.65-0.70 | 17 | 0.678 | 0.824 |
| 0.70-0.75 | 14 | 0.722 | 0.857 |
| 0.75-0.80 | 10 | 0.774 | 0.900 |
| 0.80-0.85 | 6 | 0.824 | 1.000 |
| 0.85-0.90 | 5 | 0.872 | 1.000 |
| 0.90-0.95 | 3 | 0.909 | 1.000 |
| 0.95-1.00 | 0 | - | - |
