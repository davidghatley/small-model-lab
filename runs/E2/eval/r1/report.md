# E2 eval: r1 vs base
94 pairs with both pages clean (of 100 briefs). Page validity: {"x": {"n": 100, "clean": 98, "unclean": 2, "render_failed": 0, "blank": 0}, "y": {"n": 100, "clean": 96, "unclean": 4, "render_failed": 0, "blank": 0}}

- **omnijev-0.8b / all pairs** n=94: win rate of r1 0.851 CI[0.777, 0.926]; length-controlled 0.919 CI[0.832, 0.98]; bucketed LC 0.851; r1 longer in 85% of pairs (slope -1.868).
- **omnijev-0.8b / confident (order-avg >=0.7)** n=35: win rate of r1 0.943 CI[0.857, 1.0]; length-controlled 0.998 CI[0.963, 1.0]; bucketed LC 0.942; r1 longer in 77% of pairs (slope -6.899).
  order-flip rate 0.309
- **imajev-9b / all pairs** n=94: win rate of r1 0.926 CI[0.872, 0.968]; length-controlled 0.88 CI[0.793, 0.984]; bucketed LC 0.927; r1 longer in 85% of pairs (slope 2.414).
- **imajev-9b / confident (order-avg >=0.7)** n=49: win rate of r1 0.959 CI[0.898, 1.0]; length-controlled 0.914 CI[0.678, 0.967]; bucketed LC 0.961; r1 longer in 88% of pairs (slope 3.848).
  order-flip rate 0.34
