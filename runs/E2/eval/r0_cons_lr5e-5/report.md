# E2 eval: r0_cons vs base
96 pairs with both pages clean (of 100 briefs). Page validity: {"x": {"n": 100, "clean": 97, "unclean": 3, "render_failed": 0, "blank": 0}, "y": {"n": 100, "clean": 99, "unclean": 1, "render_failed": 0, "blank": 0}}

- **omnijev-0.8b / all pairs** n=96: win rate of r0_cons 0.646 CI[0.542, 0.74]; length-controlled 0.652 CI[0.545, 0.757]; bucketed LC 0.646; r0_cons longer in 56% of pairs (slope -0.651).
- **omnijev-0.8b / confident (order-avg >=0.7)** n=26: win rate of r0_cons 0.808 CI[0.654, 0.962]; length-controlled 0.828 CI[0.668, 0.968]; bucketed LC 0.806; r0_cons longer in 54% of pairs (slope -2.186).
  order-flip rate 0.344
- **imajev-9b / all pairs** n=96: win rate of r0_cons 0.708 CI[0.615, 0.802]; length-controlled 0.719 CI[0.618, 0.82]; bucketed LC 0.708; r0_cons longer in 56% of pairs (slope 3.044).
- **imajev-9b / confident (order-avg >=0.7)** n=35: win rate of r0_cons 0.771 CI[0.629, 0.914]; length-controlled 0.761 CI[0.525, 0.931]; bucketed LC 0.778; r0_cons longer in 71% of pairs (slope 4.518).
  order-flip rate 0.406
