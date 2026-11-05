# Audit: E2 round 1 (r1) vs base and r0_cons (imajev-9b, 94 clean pairs)
Script: audit.py (reuses r0 audit logic; a=base so r1 win = 1-p_a_avg). Stats: audit_stats.json. Images: contact_sheet.png (12 random, base left | r1 right), top_wins_sheet.png (12 of the top 15 wins).

## 1. Page stats (mean per page, base / r0 / r1)
| metric | base | r0 | r1 |
|---|---|---|---|
| HTML chars | 4624 | 4835 | 6192 (+34%) |
| words | 94.8 | 101.3 | 115.3 |
| sections present (heuristic) | 90.7% | 89.1% | 87.7% |
| imgs / external imgs | 1.62 / 0.93 | 0.77 / 0.37 | 1.37 / 0.69 |
| 90-100vh hero | 23% | 4% | 3% |
| gradients | 1.85 | 1.20 | 1.45 |
| box-shadow | 0.95 | 2.71 | 4.55 |
| inline svg | 0.20 | 0.44 | 0.51 |
| trust hits / praise hits | 0.096 / 0.032 | 0.085 / 0.053 | 0.096 / 0.074 |
| "Welcome to X" h1 | 67% | 78% | 87% |
| #6a11cb->#2575fc palette | 28% | 34% | 63% |
Verbatim brief copy: 0 in all. Margin vs word delta r=0.22, vs HTML-length delta r=0.18 (weak). r1 is longer than base in 85% of pairs.

## 2. Collapse metrics
Across briefs (30 random briefs, 435 pairs; lower distance = more alike):
| metric | base | r0 | r1 |
|---|---|---|---|
| mean pairwise gray 64x40 distance | 0.358 | 0.309 | 0.330 |
| color 64x40 distance | 0.407 | 0.341 | 0.350 |
| color-histogram L1 | 1.306 | 0.877 | 0.864 |
| text word-set Jaccard | 0.109 | 0.102 | 0.108 |
| tag-bigram Jaccard | 0.400 | 0.467 | 0.412 |
| CSS class-set Jaccard | 0.306 | 0.279 | 0.203 |
| hex-colour Jaccard | 0.078 | 0.062 | 0.128 |
Palette (all 94): most common hero hue bucket share 30% / 37% / 61%; hero-mean-colour std 0.266 / 0.224 / 0.197; pages containing the #6a11cb + #2575fc pair 28% / 34% / 63%; distinct primary-colour bins 24 / 23 / 18; distinct hex values over the set 165 / 150 / 142. Text/structure across briefs is NOT collapsed (text Jaccard unchanged, class names more diverse, distinct h1 98%).
Within briefs (500 briefs x 4 training samples, round0 policy = base-ish, round1 policy = r0 adapter):
| | round0 | round1 |
|---|---|---|
| gray distance | 0.271 | 0.220 (-19%) |
| color distance | 0.316 | 0.254 (-20%) |
| hex Jaccard | 0.055 | 0.117 (2.1x) |
| text Jaccard | 0.273 | 0.277 (same) |
The 4 samples are never identical HTML. The red flag is confirmed but narrow: round-1 samples converged VISUALLY and in palette (not text), so the judge saw fewer decisive differences, hence 302 vs 1041 confident pairs.

## 3. Contact sheet (looked at)
r1: nearly every page opens with a rounded purple-to-blue gradient banner card, "Welcome to X", then white shadowed cards on light grey. Base has varied hero colours (orange, green, dark, grey), full-viewport heroes, black/broken images, unstyled forms. r1 still has broken imgs ("Client testimonial 1", black app icon in Covera), generic placeholder avatars, John/Jane Doe, crude content, and a few overflowing/unclosed pages. Ties (r1 beating base) are often the judge preferring any tidy card layout.

## 4. Top 15 wins (margins 0.32-0.38): 0027 0004 0069 0033 0021 0026 0049 0080 0024 0068 0076 0057 0010 0097 0031
Base side: 7/15 (47%) had a 90-100vh hero (r1: 1/15), mean 2.1 gradients, 1.3 external imgs (broken), and stacked rainbow section blocks (0004 green/yellow/brown, 0027 dark-green full-bleed with unstyled text). r1 side: compact purple hero + cards, 6.2k chars, 110 words. No verbatim copying, praise text 0.13/page (2 of 15 pages), trust hits 0.07. Wins are base failure avoidance plus the template; no content dropping (words +24, sections -6% in the top 15). Win rate by palette: pages with purple-blue pair 96.6% (59), without 85.7% (35), so the template adds ~11 points of win rate on top of an already high baseline.

## 5. Verdict
Both, with mode collapse mild and concentrated in palette and layout rather than content.
- Real: r1 is bigger (+34% HTML, +22% words) with more cards/shadows/svg than r0, and still fixes base failures (full-viewport hero 23%->3%). Against r0, r1's LC win under imajev rose from 0.71 to 0.88. Length-controlled still 0.88, and length correlation is weak, so it is not mere padding.
- Collapse: the purple/blue gradient template went 28% (base) -> 34% (r0) -> 63% (r1); top hero-hue share 30% -> 61%; within-brief visual diversity fell ~20% and palette overlap doubled; "Welcome to X" 87%. This is a judge-pleasing attractor (that palette wins 97% vs 86% without). Across-brief screenshot distance is still 8% below base and slightly above r0, so layout has not collapsed to one page.
- Estimate: about 11 of the 93 win-rate points are attributable to the template (palette split), the remainder mostly base-failure avoidance. Expect round 2 to gain little: sample diversity is down and the template already saturates the judge. Absolute quality is low (placeholder content, broken images persist).
Caveats: palette detection uses hero-region colours of 1280x800 screenshots and a hex regex; split-by-palette is confounded with other r1 traits; judge scores for r1 come from a single order-averaged run.
