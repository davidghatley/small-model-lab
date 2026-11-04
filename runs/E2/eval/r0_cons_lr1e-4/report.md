# E2 eval: r0_cons vs base
98 pairs with both pages clean (of 100 briefs). Page validity: {"x": {"n": 100, "clean": 98, "unclean": 2, "render_failed": 0, "blank": 0}, "y": {"n": 100, "clean": 98, "unclean": 2, "render_failed": 0, "blank": 0}}

- **omnijev-0.8b / all pairs** n=98: win rate of r0_cons 0.505 CI[0.464, 0.546]; length-controlled 0.371 CI[0.102, 0.665]; bucketed LC 0.505; r0_cons longer in 14% of pairs (slope 24.372).
- **omnijev-0.8b / confident (order-avg >=0.7)** n=2: win rate of r0_cons 1.0 CI[1.0, 1.0]; length-controlled None CI[nan, nan]; bucketed LC 1.0; r0_cons longer in 100% of pairs (slope None).
  order-flip rate 0.929
- **imajev-9b / all pairs** n=98: win rate of r0_cons 0.505 CI[0.464, 0.551]; length-controlled 0.473 CI[0.175, 0.727]; bucketed LC 0.505; r0_cons longer in 14% of pairs (slope 4.592).
- **imajev-9b / confident (order-avg >=0.7)** n=2: win rate of r0_cons 1.0 CI[1.0, 1.0]; length-controlled None CI[nan, nan]; bucketed LC 1.0; r0_cons longer in 100% of pairs (slope None).
  order-flip rate 0.949
