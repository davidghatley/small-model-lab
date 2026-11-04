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

## small_model

- source: runs/E1/pages_base s0 vs s1 (Qwen2.5-Coder-7B base); script scripts/assemble_sm_pairs.py seed 0
- eligible briefs (clean, untruncated, minus 8 known bad ids): 192; pairs assembled: 100; rejected on render/blank check: 1 ['e1-0198']
- flagged pairs: 0 []
- near-identical (pixel_diff_pct < 1%): 0; < 0.5%: 0
- pixel_diff_pct (channel diff > 8, top 800px): min 16.91, p25 76.43, median 94.19, p75 99.82, max 100.00
- histogram: {'0-0.5%': 0, '0.5-1%': 0, '1-5%': 0, '5-20%': 1, '20-50%': 5, '50-100%': 94}
- reference subset: 60 ids (excluded <1% diff: True) in labels/batch2.txt, batch3.txt, reference_subset.json['small_model']
- contact sheet: runs/E1/pairs_contact_sm.png (left=a, right=b)
