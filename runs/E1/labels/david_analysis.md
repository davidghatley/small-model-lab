# E1: David's 30 hand labels vs everything else

Agreement = k/n over pairs where David did not say tie and the other side gave a pick. Judge pick = order-averaged P(a) > 0.5; 'conf>=0.7' = only pairs with |P-0.5| >= 0.2.

| vs | all (n=30, ties 7) | fg (n=5, ties 0) | fh (n=10, ties 1) | sm (n=15, ties 6) |
|---|---|---|---|---|
| truth/author | 14/14 | 5/5 | 9/9 | — |
| reference | 20/23 | 5/5 | 7/9 | 8/9 |
| omnijev-0.8b | 16/23 | 5/5 | 5/9 | 6/9 |
| omnijev-0.8b conf>=0.7 | 4/6 | 1/1 | 1/2 | 2/3 |
| omnijev-4b | 18/23 | 5/5 | 5/9 | 8/9 |
| omnijev-4b conf>=0.7 | 4/5 | 3/3 | — | 1/2 |
| rsi-jev-4b | 19/23 | 5/5 | 7/9 | 7/9 |
| rsi-jev-4b conf>=0.7 | 9/10 | 3/3 | 1/1 | 5/6 |
| imajev-9b | 19/23 | 5/5 | 6/9 | 8/9 |
| imajev-9b conf>=0.7 | 7/7 | 3/3 | 2/2 | 2/2 |
| reference (David clear only) | 12/13 | 5/5 | 3/4 | 4/4 |
| omnijev-0.8b (David clear only) | 6/13 | 5/5 | 0/4 | 1/4 |

## Per pair

| page | pair | David | strength | truth/author | ref (conf) | omni-0.8b P(a) | imajev-9b P(a) | note |
|---|---|---|---|---|---|---|---|---|
| p01 | fg-0067 | a | clear | a | a (0.9) | 0.57 | 0.565 |  |
| p02 | sm-0166 | b | clear |  | b (0.65) | 0.663 | 0.456 |  |
| p03 | fh-0162 | b | clear | b | b (0.65) | 0.541 | 0.524 |  |
| p04 | sm-0096 | b | slight |  | b (0.65) | 0.315 | 0.393 |  |
| p05 | sm-0197 | b | slight |  | a (0.7) | 0.481 | 0.509 | Broken images don't help :/ |
| p06 | sm-0098 | a | clear |  | a (0.8) | 0.821 | 0.597 |  |
| p07 | fh-0170 | b | slight | b | b (0.65) | 0.199 | 0.336 |  |
| p08 | sm-0061 | a | slight |  | a (0.65) | 0.675 | 0.538 |  |
| p09 | fh-0180 | b | slight | b | b (0.72) | 0.444 | 0.258 |  |
| p10 | fh-0188 | b | clear | b | b (0.8) | 0.524 | 0.277 |  |
| p11 | sm-0115 | tie | None |  | a (0.85) | 0.759 | 0.749 | both bad |
| p12 | fg-0058 | b | clear | b | b (0.95) | 0.479 | 0.211 |  |
| p13 | fh-0153 | a | slight | a | b (0.6) | 0.59 | 0.541 |  |
| p14 | sm-0168 | tie | None |  | a (0.7) | 0.956 | 0.86 | both bad |
| p15 | sm-0100 | b | clear |  | b (0.75) | 0.606 | 0.285 |  |
| p16 | sm-0187 | b | slight |  | b (0.7) | 0.354 | 0.42 |  |
| p17 | fg-0096 | b | clear | b | b (0.97) | 0.345 | 0.087 |  |
| p18 | fg-0040 | a | clear | a | a (0.68) | 0.645 | 0.684 |  |
| p19 | fh-0159 | a | clear | a | a (0.68) | 0.494 | 0.518 |  |
| p20 | sm-0089 | tie | None |  | a (0.8) | 0.647 | 0.676 | both bad |
| p21 | sm-0184 | a | clear |  | a (0.75) | 0.192 | 0.621 | B is just very bad, A just doesn't show much |
| p22 | fh-0165 | b | clear | b | a (0.65) | 0.798 | 0.671 |  |
| p23 | fg-0006 | b | clear | b | b (0.98) | 0.107 | 0.087 |  |
| p24 | sm-0119 | tie | None |  | a (0.75) | 0.78 | 0.493 | both bad |
| p25 | sm-0097 | b | slight |  | b (0.75) | 0.233 | 0.28 | both bad |
| p26 | fh-0161 | tie | None | a | a (0.58) | 0.701 | 0.569 |  |
| p27 | sm-0142 | tie | None |  | a (0.85) | 0.608 | 0.815 | Both bad |
| p28 | sm-0188 | tie | None |  | b (0.55) | 0.215 | 0.468 | both bad |
| p29 | fh-0192 | b | slight | b | b (0.6) | 0.353 | 0.455 |  |
| p30 | fh-0184 | b | slight | b | b (0.7) | 0.385 | 0.524 |  |
