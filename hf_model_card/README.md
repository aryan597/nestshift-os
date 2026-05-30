# NestShift-OS Energy Forecaster

**Model type:** Gradient Boosting (LightGBM) dual-head architecture for residential half-hourly demand forecasting and spike prediction  
**Language:** English (UK)  
**License:** Apache-2.0  
**Repository:** https://github.com/nestshift/nestshift-os  
**Paper:** *A Multi-Agent, Local-First Edge AI Architecture for Autonomous Residential Energy Optimisation Under Dynamic Tariffs*

---

## Model Description

This repository contains two trained LightGBM regressors that form the **Energy Agent** forecasting core of the NestShift OS---a local-first, edge-deployable Home Energy Management System (HEMS).

- **`model_demand_forecaster.pkl`** — Primary mean-prediction head. Forecasts household half-hourly energy demand (kWh) using 17 time-series features.
- **`model_quantile_q90.pkl`** — Secondary quantile-regression head ($\alpha = 0.9$). Predicts the 90th percentile of demand, enabling proactive load-shedding before price spikes.

Both models are designed to run inference on a Raspberry Pi 5 (8 GB) in real time, with zero cloud dependency.

---

## Intended Use

- **Primary:** Residential energy demand forecasting for tariff-aware appliance scheduling (washing machine, dishwasher, EV charger, water heater).
- **Secondary:** Demand-spike early-warning for demand-response and peak-shaving applications.
- **Deployment target:** Edge hardware (Raspberry Pi 5, NVIDIA Jetson, or equivalent ARM/x86_64 Linux board).
- **Not suitable for:** Industrial-scale load forecasting, sub-second real-time grid balancing, or non-UK households without retraining.

---

## Training Data

| Attribute | Value |
|---|---|
| **Dataset** | Low Carbon London (LCL) — UK Power Networks |
| **Records** | 54,197 half-hourly readings |
| **Households** | 20 (representative sample) |
| **Date range** | 2011-12-06 to 2012-02-04 |
| **Geography** | London, United Kingdom |
| **Resolution** | 30 minutes |
| **Train / Val / Test split** | 40,673 / 6,384 / 7,140 (walk-forward temporal) |

### Feature Engineering

| Feature | Description |
|---|---|
| `hour_of_day` | 0–23 |
| `day_of_week` | 0–6 |
| `month` | 1–12 |
| `lag_1h` | Demand 1 half-hour ago |
| `lag_24h` | Demand 24 hours ago (48 steps) |
| `lag_48h` | Demand 48 hours ago (96 steps) |
| `rolling_mean_6h` | Mean over past 12 half-hours |
| `rolling_mean_24h` | Mean over past 48 half-hours |
| `rolling_mean_7d` | Mean over past 336 half-hours |
| `hour_sin`, `hour_cos` | Cyclical hour encoding |
| `dow_sin`, `dow_cos` | Cyclical day-of-week encoding |
| `month_sin`, `month_cos` | Cyclical month encoding |
| `is_dtou` | Binary: on Dynamic Time-of-Use tariff |
| `acorn_code` | ACORN demographic segment |

Missing lag values at household boundaries are backfilled up to 96 steps.

---

## Model Architecture

### Primary Head — Mean Forecaster

```
LightGBM LGBMRegressor
├── n_estimators: 1000 (best_iteration: 526)
├── learning_rate: 0.05
├── num_leaves: 31
├── max_depth: 8
├── subsample: 0.8
├── colsample_bytree: 0.8
├── min_child_samples: 20
├── objective: regression (MSE)
└── random_state: 42
```

### Secondary Head — Q90 Spike Predictor

```
LightGBM LGBMRegressor
├── n_estimators: 500 (best_iteration: 309)
├── learning_rate: 0.05
├── num_leaves: 31
├── max_depth: 6
├── subsample: 0.8
├── colsample_bytree: 0.8
├── objective: quantile
├── alpha: 0.9
└── random_state: 42
```

---

## Performance

### Mean Forecaster

| Split | Samples | MAE (kWh) | RMSE (kWh) | R² |
|---|---|---|---|---|
| Train | 40,673 | 0.073 | 0.145 | **0.897** |
| Validation | 6,384 | 0.091 | 0.177 | **0.893** |
| Test | 7,140 | 0.101 | 0.209 | **0.892** |

Training time: **0.58 s** on Intel 11th-gen laptop (single-threaded inference ≈ 2 ms/sample).

### Q90 Quantile Head

| Split | MAE (kWh) | RMSE (kWh) | R² |
|---|---|---|---|
| Test | 0.161 | 0.264 | **0.829** |

---

## Downstream Optimisation Impact

When the mean forecaster drives a greedy scheduler against simulated UK dynamic tariffs (60 % Standard / 40 % DToU):

| Metric | Value |
|---|---|
| Mean cost reduction | **26.43 %** |
| Projected annual saving | **£475.70 / household** |
| Baseline behaviour | Run deferrable appliances at 6 pm peak |
| Devices scheduled | washing_machine, dishwasher, ev_charger, water_heater |

---

## Limitations and Biases

- **Temporal bias:** Trained on 2011–2012 data; modern smart-meter patterns may differ (more EVs, heat pumps, solar PV).
- **Geographic bias:** London-centric; northern UK households with electric heating may exhibit higher winter variance.
- **Tariff bias:** Evaluated on simulated Standard + DToU mix; real Octopus Agile or other dynamic tariffs may yield different savings.
- **Household size:** Sample of 20 households; generalisation to >5-bedroom homes or shared accommodation is untested.
- **MAPE instability:** MAPE is >50,000 % because near-zero readings in low-consumption periods create division-by-near-zero. Use MAE or R² for evaluation instead.

---

## How to Use

### Installation

```bash
pip install lightgbm joblib pandas numpy scikit-learn
```

### Load and predict

```python
import joblib
import pandas as pd
import numpy as np

# Load models
forecaster = joblib.load("model_demand_forecaster.pkl")
spike_head = joblib.load("model_quantile_q90.pkl")

# Prepare a DataFrame with the 17 feature columns
# (see Feature Engineering table above)
X = pd.DataFrame({
    "hour_of_day": [18],
    "day_of_week": [2],
    "month": [1],
    "lag_1h": [0.45],
    "lag_24h": [0.38],
    "lag_48h": [0.42],
    "rolling_mean_6h": [0.50],
    "rolling_mean_24h": [0.44],
    "rolling_mean_7d": [0.41],
    "hour_sin": [np.sin(2 * np.pi * 18 / 24)],
    "hour_cos": [np.cos(2 * np.pi * 18 / 24)],
    "dow_sin": [np.sin(2 * np.pi * 2 / 7)],
    "dow_cos": [np.cos(2 * np.pi * 2 / 7)],
    "month_sin": [np.sin(2 * np.pi * 1 / 12)],
    "month_cos": [np.cos(2 * np.pi * 1 / 12)],
    "is_dtou": [1],
    "acorn_code": [3],
})

mean_pred = forecaster.predict(X)[0]      # e.g. 0.52 kWh
q90_pred = spike_head.predict(X)[0]       # e.g. 0.91 kWh

# If q90_pred >> mean_pred, a spike is likely -> shed loads
```

---

## Files in this Repository

| File | Size | Description |
|---|---|---|
| `model_demand_forecaster.pkl` | 1.5 MB | Primary LightGBM mean predictor (526 trees) |
| `model_quantile_q90.pkl` | 0.9 MB | Secondary LightGBM Q90 quantile predictor (309 trees) |
| `validation_metrics.json` | 1 KB | Train / val / test metrics + Q90 metrics |
| `cost_savings_report.json` | 1 KB | Optimisation simulation results |
| `training_log.txt` | 2 KB | Full training & optimisation log |
| `feature_importance.png` | 103 KB | Feature importance plot (split gain) |
| `scatter_actual_vs_pred_TEST.png` | 329 KB | Test-set scatter plot |
| `residuals_TEST.png` | 71 KB | Test-set residual distribution |
| `forecast_vs_actual_TEST.png` | 499 KB | Time-series overlay on test set |
| `quantile_spike_comparison.png` | 510 KB | Q90 vs mean on spike events |

---

## Citation

```bibtex
@article{nestshift2026,
  title={A Multi-Agent, Local-First Edge AI Architecture for Autonomous Residential Energy Optimisation Under Dynamic Tariffs},
  author={Somayajula, Aryan},
  year={2026}
}
```

## Contact

**Somayajula Aryan** — Founder, NestShift Technologies Ltd  
📧 aryan@nestshifthome.co.uk  
🌐 https://nestshifthome.co.uk
