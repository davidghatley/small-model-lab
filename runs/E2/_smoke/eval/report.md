# E2 eval: smoke_r0 vs base
5 pairs with both pages clean (of 5 briefs). Page validity: {"x": {"n": 5, "clean": 5, "unclean": 0, "render_failed": 0, "blank": 0}, "y": {"n": 5, "clean": 5, "unclean": 0, "render_failed": 0, "blank": 0}}

- **omnijev-0.8b / all pairs** n=5: win rate of smoke_r0 0.6 CI[0.3, 0.9]; length-controlled None CI[0.087, 0.729]; bucketed LC 0.667; smoke_r0 longer in 40% of pairs (slope None).
- omnijev-0.8b / confident (order-avg >=0.7): n=1
  order-flip rate 0.6
