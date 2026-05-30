# NestShift OS -- Proof-of-Concept Run Instructions
**For Innovator Founder Visa Technical Demonstration**

---

## What You Need
- Windows 11 PC (your 11th Gen Intel is perfect)
- The Python virtual environment already created in this folder
- No internet required for `--data-source synthetic` (recommended for instant results)
- Internet required for `--data-source real` (downloads 10GB LCL dataset)

---

## Step 1: Open Terminal
Press `Win + R`, type `cmd`, press Enter.

Or right-click the Start button → **Terminal**.

---

## Step 2: Navigate to Project Folder
Copy and paste this exact command (handles spaces in path):

```cmd
cd "E:\projects\nestshift ltd\os-image\nestshift-os"
```

---

## Step 3: Run the Energy Agent Trainer (Fast Mode -- 2 minutes)
This generates synthetic UK household data, trains the LightGBM model, and optimises energy schedules.

```cmd
venv\Scripts\python.exe nestshift_poc_trainer.py --data-source synthetic --households 100 --days 90
```

**What you will see:**
- `[DATA] Generating synthetic UK data: 100 households x 90 days`
- `[FEAT] Engineering features`
- `[TRAIN] Training LightGBM`
- `[OPT] Running energy schedule optimisation`
- `Average cost saving: XX.XX%`
- `Projected annual saving: £XXX.XX/household`

**Outputs created in `poc_outputs\`:**
- `model_demand_forecaster.pkl` -- The trained AI model
- `validation_metrics.json` -- Accuracy scores (MAE, RMSE, R²)
- `feature_importance.png` -- Which features matter most
- `forecast_vs_actual.png` -- 7-day prediction vs reality
- `energy_schedule.csv` -- Optimised device schedules
- `cost_savings_report.json` -- Business case numbers
- `training_log.txt` -- Full technical log

---

## Step 4: Run the NARE Brain Simulation (30 seconds)
This demonstrates the spiking neural network learning your behaviour.

```cmd
venv\Scripts\python.exe nestshift_poc_nare.py
```

**What you will see:**
- `[t+    0ms] SPIKE: sensors/motion/hallway`
- `[t+  100ms] USER OVERRIDE: devices/light/hallway`
- `FINAL LEARNED SYNAPSES` with weights and autonomy status

**Outputs created in `poc_outputs\`:**
- `nare_learning_curve.png` -- Synapses getting stronger over time
- `nare_spike_raster.png` -- Neural activity visualization
- `nare_synapse_map.json` -- Learned connections
- `nare_neural_trace.json` -- Explainability data

---

## Step 5: View Your Results
Open the output folder:

```cmd
explorer poc_outputs
```

Double-click any PNG to view the charts.
Open JSON files in Notepad or VS Code to see the numbers.

---

## Optional: Train on Real LCL Data (30-40 minutes download)
If you want to use the real Low Carbon London smart meter dataset:

```cmd
venv\Scripts\python.exe nestshift_poc_trainer.py --data-source real --households 20 --days 30
```

This will:
1. Download the 10GB LCL zip from data.london.gov.uk
2. Extract 2 CSV files
3. Train on real UK household data
4. Generate the same outputs

If the download is too slow, press **Ctrl+C** and use the synthetic mode instead.

---

## Quick Commands Cheat Sheet

| Goal | Command |
|------|---------|
| Fast demo (synthetic, 100 homes) | `venv\Scripts\python.exe nestshift_poc_trainer.py --data-source synthetic --households 100 --days 90` |
| Smaller demo (faster) | `venv\Scripts\python.exe nestshift_poc_trainer.py --data-source synthetic --households 30 --days 60` |
| Real data demo | `venv\Scripts\python.exe nestshift_poc_trainer.py --data-source real --households 20 --days 30` |
| NARE brain only | `venv\Scripts\python.exe nestshift_poc_nare.py` |
| Open outputs | `explorer poc_outputs` |

---

## For Your Visa Interview / Investor Pitch
Point to these files on your laptop:

1. **Technical proof**: `poc_outputs/model_demand_forecaster.pkl` + `validation_metrics.json`
2. **Business case**: `poc_outputs/cost_savings_report.json` (shows £X annual savings)
3. **AI differentiation**: `poc_outputs/nare_learning_curve.png` (neural learning)
4. **Product vision**: Show the `NestShift_Hub_Enclosure_Brief.pdf` (hardware is real)
5. **Code repository**: Show `nestshift_poc_trainer.py` (end-to-end pipeline)

**The story:**
> "This is a fully local AI system trained on UK smart meter data. It forecasts household energy demand with R² = 0.XX, then shifts flexible loads to the cheapest tariff slots, saving £XXX per year. The neural brain learns occupant behaviour through spike-timing-dependent plasticity — no cloud, no privacy violations. And we've designed the physical hub enclosure for CNC prototyping."
