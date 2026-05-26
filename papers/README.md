# NestShift Research Papers

This directory contains the academic papers derived from the NestShift OS project.

## Versions

### `version_a_conservative/`
**"A Multi-Agent, Local-First Edge AI Architecture for Autonomous Residential Energy Optimisation Under Dynamic Tariffs"**

- Close to the original April 2026 draft structure
- Replaces "expected outcomes" with actual simulation results
- 9-13% cost reduction demonstrated across Flat, ToU, Agile, and Volatile tariffs
- 20 Monte Carlo trials per scenario
- Includes learning curves, drift detection, and sensitivity analysis

**Target:** IEEE/ACM venues, Springer Energy Informatics, or arXiv preprint.

### `version_b_solar/`
**"SolarShift: A Local-First Edge AI Architecture for Solar Self-Consumption and Dynamic Tariff Arbitrage"**

- Reframes the contribution around solar forecasting + tariff arbitrage
- Introduces a 4th agent: Solar Forecasting Agent
- Projects 12-38% cost reduction with solar-equipped households
- Stronger novelty claim and market differentiation
- Includes Pi 3B+ hardware validation numbers

**Target:** Higher-impact venues (Nature Energy, Applied Energy, IEEE Transactions on Smart Grid).

## Simulation Framework

Both papers are backed by the digital twin simulation in `/simulation/`:

```bash
cd simulation/
python3 run_experiments.py          # Main Monte Carlo suite
python3 analysis_learning_curve.py  # 90-day convergence
python3 analysis_sensitivity.py     # Lambda + beta sweep
python3 analysis_drift.py           # Behavioral drift scenario
```

Results are written to `simulation/results/`.

## Compilation

```bash
cd version_a_conservative/
pdflatex paper.tex
bibtex paper
pdflatex paper.tex
pdflatex paper.tex
```

## Citation

If you use this work, please cite:

```bibtex
@article{aryan2026nestshift,
  title={A Multi-Agent, Local-First Edge AI Architecture for Autonomous Residential Energy Optimisation Under Dynamic Tariffs},
  author={Aryan, Somayajula},
  year={2026}
}
```
