# small-model-lab

Small-model experiments on one RTX 3060 (12 GB) + 64 GB RAM.

The first experiment is a **design loop**. A small coder model writes landing-page HTML. Playwright renders each page, a local vision "System One" judge picks the better of two pages, and those picks train the coder with DPO (Unsloth). Held-out briefs are scored by the training judge, a second judge and a frontier model, to tell real gains from judge gaming.

- Status: `LEDGER.md`
- Plan and decisions: `PLAN.md`
- Original brief: `docs/brief.md`
- How work is split across agents: `AGENTS.md`
