# E1 audit (auditor, 2026-11-03)
Script: `runs/E1/audit/audit.py` (run with `.venv/bin/python`); raw output `audit_script_output.txt`. Side-by-side PNGs of the 5 inspected pairs: `sm-*.png` (left=a, right=b). No code/scores/labels edited.

## Plumbing checks
- score_pairs.py: `p_first_ab` = P(first image better) for (a,b); `p_first_ba` same for (b,a); `p_a_ba = 1 - p_first_ba` (correct: first image in ba order is b); `p_a_avg = mean`. All 4x300 rows recomputed: 0 inconsistencies, 0 error rows, 0 missing values.
- Data: 300 pairs scored per judge (150 fg, 50 fh, 100 sm); reference labels cover only 120 (60 sm, 40 fh, 20 fg). Reference "better" on sm: 32 a / 28 b (no side bias). Reference agrees with by-construction on 20/20 fg.
- GATE (analyze_e1.py): `high_conf` = order-averaged p>=0.8 or <=0.2 (HI=0.8), scored against `reference` labels over ALL reference pairs (sm+fh+fg, 120), NOT by-construction and NOT sm-only. fg pairs are easy so they inflate it.
  | judge | gate subset (all ref, conf>=.8) | agree, 95% CI | sm-only conf>=.8 |
  |---|---|---|---|
  | omnijev-0.8b | n=19 | 0.842 [0.68,1.00] | n=16 0.875 [0.69,1.00] |
  | omnijev-4b | n=9 | 1.000 [1,1] | n=5 1.00 |
  | rsi-jev-4b | n=33 | 0.879 [0.76,0.97] | n=23 0.870 [0.74,1.00] |
  | imajev-9b | n=14 | 1.000 [1,1] | n=6 1.00 |

## Claim 1 (sm vs reference): HOLDS (numbers reproduce exactly)
Bootstrap seed 0, 2000 resamples, sm subset (n=60), order-averaged confidence = max(p,1-p). Coverage = share of the 60.
| judge | overall [CI] | conf>=0.6 (n, cov) agree [CI] | conf>=0.7 (n, cov) agree [CI] | conf>=0.8 (n, cov) agree [CI] | ref-conf>=.75 (n=23) |
|---|---|---|---|---|---|
| omnijev-0.8b | 0.733 [0.63,0.83] | 43, 0.72: 0.767 [0.63,0.88] | 28, 0.47: 0.857 [0.71,0.96] | 16, 0.27: 0.875 [0.69,1.0] | 0.826 |
| omnijev-4b | 0.567 [0.43,0.68] | 31, 0.52: 0.806 [0.68,0.94] | 9, 0.15: 0.889 [0.67,1.0] | 5, 0.08: 1.0 | 0.739 |
| rsi-jev-4b | 0.617 [0.48,0.73] | 44, 0.73: 0.727 [0.59,0.84] | 34, 0.57: 0.765 [0.62,0.91] | 23, 0.38: 0.870 [0.74,1.0] | 0.783 |
| imajev-9b | 0.667 [0.55,0.78] | 35, 0.58: 0.800 [0.66,0.91] | 18, 0.30: 0.889 [0.72,1.0] | 6, 0.10: 1.0 | 0.913 |
Caveats: the "0.86 / 0.89" figures use threshold |p-0.5|>=0.2 (conf>=0.7), which differs from the gate's 0.8 and was not pre-registered. Lower CI bounds at 0.7 are 0.71-0.72, i.e. consistent with ~70%, below the 0.75 bar. The 0.8b overall 0.733 is ~+0.2 over chance but the CI is [0.63,0.83]. Selecting on high confidence is an in-sample choice of subset.

## Claim 2 (position bias): PARTLY DOES NOT HOLD
Over all 300 pairs: mean P(first) = 0.469 (0.8b), 0.370 (4b), 0.520 (rsi), 0.376 (9b); flip rates 0.333, 0.583, 0.303, 0.397. So the stated range 0.34-0.46 / 28-76% looks like per-source cherry-ranges: by source (flip, P1): 0.8b sm .29/.43, fh .36/.43, fg .35/.51; 4b sm .67/.34, fh .76/.37, fg .47/.39; rsi sm .28/.46, fh .34/.43, **fg .31/.59 (bias toward FIRST)**; 9b sm .43/.37, fh .70/.34, fg .27/.39. Second-image bias is real for 4b and 9b, mild for 0.8b, absent/reversed for rsi overall. Order-averaging is still required (flip 28-76% on subsets holds). Note 4b and 9b flip on 67% / 43% of sm pairs, so their order-averaged p is often near 0.5 (explains tiny high-conf coverage).

## Claim 3 (by construction, 150 fg): HOLDS
imajev-9b 0.953 [0.92,0.99], omnijev-4b 0.900 [0.85,0.95], rsi-jev-4b 0.773 [0.71,0.84], omnijev-0.8b 0.687 [0.61,0.76]. Subtle (n=50 each): 0.8b 0.52, rsi 0.52, 4b 0.72, 9b 0.86 (obvious 0.88/0.98/1.0/1.0; moderate 0.66/0.82/0.98/1.0). Subtle is hardest, and 0.8b and rsi are at chance there. Caveat: fg is not the E2 distribution, and fg accuracy is not predictive of sm accuracy (4b is 0.90 on fg but 0.567 on sm).

## Claim 4 (gate passes for all four): HOLDS AS CODED, WEAK EVIDENCE
Passes only because the gate pools all reference sources at conf>=0.8 (see table above). On sm only at 0.8: 0.8b n=16 CI lower bound 0.69 <0.75; 4b n=5 and 9b n=6 are not informative. The gate was written as "agreement on high-confidence pairs vs reference" without naming the subset; the E2-relevant reading is sm-only.

## Artifact / leakage baselines (sm vs reference, n=60, chance 0.5; CI = bootstrap)
non-background pixel fraction (higher wins) 0.567 [0.43,0.70]; mean brightness higher 0.550; pixel std higher 0.467; vertical-edge density higher 0.633 [0.52,0.75]; image size 0.5 (all 1280x800, no signal); always-a 0.533. Judges' agreement with "more non-bg" / "brighter wins" is 0.47-0.65 (imajev-9b 0.65 with brightness, probably coincidence). Conclusion: no simple pixel/size baseline comes near the judges; the weak edge-density signal (0.63) hints at "more content = better", worth noting since the reference labeler also rewards content richness. No leakage found, but I did not test text length or the reference's own bias.

## Five hi-confidence 0.8b disagreements with reference (sm). Only 4 exist at conf>=0.7; I added sm-0007 (conf 0.69).
| pair | judge | ref (conf) | my view |
|---|---|---|---|
| sm-0184 (p_a .19) | B (cramped unstyled but complete page) | A (0.75): minimal polished | A is just one headline on a gradient, B has all sections but ugly default HTML. Genuinely ambiguous; ref defensible on aesthetics, judge on completeness. |
| sm-0033 (.81) | A (single headline on gradient) | B (0.7) | Ref right: B has hero + grid (placeholders), A is empty. Judge wrong. |
| sm-0055 (.74) | A (hero+FAQ, broken black square, flush edges) | B (0.55) | Toss-up; ref itself low-confidence. A has more content, judge arguably right. |
| sm-0045 (.29) | B (teal hero, orphaned team text, tiny button) | A (0.7) | Ref right: A has coherent hierarchy and team grid. Judge wrong. |
| sm-0007 (.31) | B (many sections, default button, cramped) | A (0.75) | Slight edge to A (styled button, spacing) but close. Ref probably right, low margin. |
Tally: 2 clear judge errors, 3 ambiguous. 0.8b seems to like busier/more-section pages and be indifferent to polish, e.g. placeholders and default controls. The ref labeler, when unsure, is itself noisy; sm pairs are often both poor, so "agreement" is partly measuring noise.

## Calibration
analyze_e1.py ECE uses order-averaged confidence vs the REFERENCE labels (csrc=reference), over all 120 reference pairs (sm+fh+fg mixed), 10 bins of width 0.05 on [0.5,1]. Reported ECE: 0.8b 0.077, 4b 0.104, rsi 0.126, 9b 0.101. Not meaningful at this n: bins have n=25,22,21,16,8,9,11,3,2,3 (0.8b) and top bins <=3; per-bin accuracy noise is +-0.15-0.3. ECE is a weighted mean of absolute gaps so it has positive bias at small n, and the mixture of easy fg pairs makes it not the sm calibration. Treat as indicative only; a reliability plot at n=60 sm supports at best 3 bins (conf <0.6, 0.6-0.7, >=0.7). Also the reference is a single LLM labeler, not ground truth, so "calibration" is calibration to Opus.

## Verdict on E2 roles
- omnijev-0.8b as training judge: usable but not validated for fine taste. sm accuracy 0.73 [0.63,0.83], 0.86 [0.71,0.96] when confident (47% coverage). Reasonable if E2 keeps only pairs with conf>=0.7 (or uses margin-weighted DPO); do NOT use unfiltered. Subtle-flaw accuracy is chance (0.52), so expect it to reward content volume over polish.
- imajev-9b as held-out judge: best by-construction (0.953) and 0.667 overall on sm (CI [0.55,0.78]); high-confidence agreement 0.89 but only 18 pairs/6 at 0.8. Adequate as an independent check only on its confident subset, and should be reported alongside the reference labeler and ideally David's labels (labels/david.jsonl was absent). Neither judge's sm agreement with reference is statistically separable from 0.6-0.7.
- Errors found: (1) claim 2 range wrong for rsi-jev-4b (P(first) .52, first-biased on fg) and overall figures; (2) gate pools fg/fh/sm, inflating pass; (3) the 0.2-margin vs 0.8 threshold inconsistency; (4) 100 sm pairs scored but only 60 have reference labels.
