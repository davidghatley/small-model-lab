# E2 eval: r0_lr5e-5 vs base
97 pairs with both pages clean (of 100 briefs). Page validity: {"x": {"n": 100, "clean": 97, "unclean": 3, "render_failed": 0, "blank": 0}, "y": {"n": 100, "clean": 98, "unclean": 2, "render_failed": 0, "blank": 0}}

- **omnijev-0.8b / all pairs** n=97: win rate of r0_lr5e-5 0.485 CI[0.433, 0.541]; length-controlled 0.462 CI[0.271, 0.664]; bucketed LC 0.485; r0_lr5e-5 longer in 16% of pairs (slope 6.207).
- **omnijev-0.8b / confident (order-avg >=0.7)** n=2: win rate of r0_lr5e-5 0.5 CI[0.0, 1.0]; length-controlled None CI[nan, nan]; bucketed LC 0.5; r0_lr5e-5 longer in 50% of pairs (slope None).
  order-flip rate 0.907
- **imajev-9b / all pairs** n=97: win rate of r0_lr5e-5 0.495 CI[0.443, 0.552]; length-controlled 0.498 CI[0.303, 0.701]; bucketed LC 0.496; r0_lr5e-5 longer in 16% of pairs (slope 6.614).
- **imajev-9b / confident (order-avg >=0.7)** n=4: win rate of r0_lr5e-5 0.75 CI[0.25, 1.0]; length-controlled 0.983 CI[0.935, 0.988]; bucketed LC 0.833; r0_lr5e-5 longer in 75% of pairs (slope 14.549).
  order-flip rate 0.866
