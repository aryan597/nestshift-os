# Research & Publications

This document collects the academic and experimental background behind NestShift OS.

---

## Papers

- **Conservative version** — *A Multi-Agent, Local-First Edge AI Architecture for Autonomous Residential Energy Optimisation Under Dynamic Tariffs*. Demonstrates 9–13% cost reduction across four tariff scenarios.
- **Solar version** — *SolarShift: A Local-First Edge AI Architecture for Solar Self-Consumption and Dynamic Tariff Arbitrage*. Projects 12–38% savings for solar-equipped households.

Original drafts and LaTeX sources have been moved to the local archive for review.

---

## Simulation Framework

The `simulation/` directory contains a reproducible digital twin for evaluating multi-agent energy optimisation:

```bash
cd simulation/
python3 run_experiments.py          # Main Monte Carlo suite (4 tariffs × 4 controllers × 20 runs)
python3 analysis_learning_curve.py  # 90-day convergence analysis
python3 analysis_sensitivity.py     # Comfort-cost (λ) and risk (β) sweeps
python3 analysis_drift.py           # Behavioral drift detection scenario
```

Results are written to `simulation/results/`.

---

## Experiment Notes

Historical experiment logs and POC notebooks are archived locally. See the project maintainer for access to:

- `experiment.md` — early design notes
- `experiment_driver.py` — batch experiment runner
- `figures/` — generated paper figures
- `poc_outputs/` — model artifacts and validation plots
- `poc_data/` — training datasets (not committed to version control)

---

## Academic Use

If you use NestShift OS or its simulation framework in academic work, please cite the project and link to the repository.

*For publication-ready drafts and the full paper archive, contact NestShift Ltd.*
