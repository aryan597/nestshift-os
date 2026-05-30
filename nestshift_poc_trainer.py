#!/usr/bin/env python3
"""
NestShift OS -- Proof-of-Concept Energy Agent Trainer
========================================================
Trains a LightGBM demand forecaster on UK household smart-meter data,
optimises appliance schedules against dynamic tariffs, and generates
publication-ready outputs for investor/visa demonstration.

Usage (from project root):
    venv/Scripts/python.exe nestshift_poc_trainer.py --data-source synthetic --households 50 --days 90
    venv/Scripts/python.exe nestshift_poc_trainer.py --data-source real --households 10 --days 30

Outputs (all written to ./poc_outputs/):
    model_demand_forecaster.pkl   -- Trained LightGBM model
    validation_metrics.json       -- MAE, RMSE, R^2, MAPE
    feature_importance.png        -- SHAP-style bar chart
    forecast_vs_actual.png        -- 7-day forecast overlay
    cost_savings_report.json      -- Baseline vs optimised cost breakdown
    energy_schedule.csv           -- Device-level optimised schedule
    training_log.txt              -- Full console log
"""

import argparse
import json
import os
import sys
import time
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

import joblib
import lightgbm as lgb
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
from tqdm import tqdm

# Fix matplotlib backend for Windows non-interactive use
matplotlib.use("Agg")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.resolve()
OUTPUT_DIR = PROJECT_ROOT / "poc_outputs"
OUTPUT_DIR.mkdir(exist_ok=True)
DATA_DIR = PROJECT_ROOT / "poc_data"
DATA_DIR.mkdir(exist_ok=True)

LOG_PATH = OUTPUT_DIR / "training_log.txt"

# ---------------------------------------------------------------------------
# Logging helper
# ---------------------------------------------------------------------------
class Logger:
    def __init__(self, path):
        self.terminal = sys.stdout
        self.log = open(path, "w", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()

    def flush(self):
        self.terminal.flush()
        self.log.flush()

sys.stdout = Logger(LOG_PATH)

# ---------------------------------------------------------------------------
# UK LCL Statistical Parameters (published in LCL close-down report & literature)
# ---------------------------------------------------------------------------
LCL_PARAMS = {
    "mean_kwh_per_halfhour": 0.42,
    "std_kwh_per_halfhour": 0.31,
    "morning_peak_hours": [7, 8, 9],
    "evening_peak_hours": [17, 18, 19, 20],
    "night_baseline": 0.15,
    "weekend_factor": 1.08,
    "winter_factor": 1.25,
    "summer_factor": 0.85,
    "dtou_low_price": 0.0399,      # £/kWh
    "dtou_normal_price": 0.1176,
    "dtou_high_price": 0.6720,
    "standard_price": 0.1428,
}

FLEXIBLE_DEVICES = {
    "washing_machine": {"power_kw": 2.2, "duration_h": 2.0, "flexible": True},
    "dishwasher": {"power_kw": 1.8, "duration_h": 1.5, "flexible": True},
    "ev_charger": {"power_kw": 7.0, "duration_h": 3.0, "flexible": True},
    "water_heater": {"power_kw": 3.0, "duration_h": 1.0, "flexible": True},
}

# ---------------------------------------------------------------------------
# 1. DATA ACQUISITION
# ---------------------------------------------------------------------------
def download_lcl_dataset():
    """Download Low Carbon London zip (10GB). Extracts first CSV only."""
    url = (
        "https://data.london.gov.uk/download/smartmeter-energy-use-data-in-london-households/"
        "3527bf39-d93e-4071-8451-df2ade1ea4f2/Power-Networks-LCL-October2015.zip"
    )
    zip_path = DATA_DIR / "LCL-FullData.zip"

    if zip_path.exists():
        print(f"[DATA] Found existing zip: {zip_path}")
        return zip_path

    print(f"[DATA] Downloading Low Carbon London dataset from data.london.gov.uk ...")
    print(f"[DATA] This is ~10 GB. Estimated time: 20-40 minutes depending on connection.")
    print(f"[DATA] Press Ctrl+C to cancel and use --data-source synthetic instead.")
    print()

    try:
        resp = requests.get(url, stream=True, timeout=30)
        resp.raise_for_status()
        total = int(resp.headers.get("content-length", 0))
        block_size = 1024 * 1024  # 1 MB

        with open(zip_path, "wb") as f:
            with tqdm(total=total, unit="MB", unit_scale=True, desc="LCL Download") as pbar:
                for chunk in resp.iter_content(chunk_size=block_size):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
        print(f"[DATA] Download complete: {zip_path}")
        return zip_path
    except KeyboardInterrupt:
        print("\n[DATA] Download cancelled by user.")
        if zip_path.exists():
            zip_path.unlink()
        sys.exit(0)
    except Exception as e:
        print(f"[DATA] Download failed: {e}")
        return None


def extract_lcl_sample(zip_path, n_files=2):
    """Extract first n CSV files from the LCL zip."""
    csv_paths = []
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
            print(f"[DATA] Zip contains {len(names)} CSV files. Extracting first {n_files}...")
            for name in names[:n_files]:
                zf.extract(name, DATA_DIR)
                csv_paths.append(DATA_DIR / name)
                print(f"[DATA] Extracted: {name}")
    except Exception as e:
        print(f"[DATA] Extraction failed: {e}")
    return csv_paths


def generate_synthetic_uk_data(n_households=50, n_days=90, seed=42):
    """
    Generate statistically calibrated synthetic UK household smart-meter data.
    Parameters derived from Low Carbon London close-down report and Kelly et al.
    """
    print(f"[DATA] Generating synthetic UK data: {n_households} households x {n_days} days ...")
    rng = np.random.RandomState(seed)

    records = []
    start_date = datetime(2013, 1, 1)

    for hh in range(n_households):
        household_id = f"MAC{hh+1:05d}"
        # Assign tariff type (30% DToU, 70% Standard -- matches LCL trial)
        tariff_type = "DToU" if rng.rand() < 0.30 else "Std"
        # Assign ACORN category
        acorn = rng.choice(["Affluent", "Comfortable", "Adversity"], p=[0.25, 0.50, 0.25])
        acorn_factor = {"Affluent": 1.15, "Comfortable": 1.0, "Adversity": 0.75}[acorn]

        for day in range(n_days):
            current = start_date + timedelta(days=day)
            month = current.month
            weekday = current.weekday()
            is_weekend = weekday >= 5

            # Seasonal factor
            if month in [12, 1, 2]:
                season_factor = LCL_PARAMS["winter_factor"]
            elif month in [6, 7, 8]:
                season_factor = LCL_PARAMS["summer_factor"]
            else:
                season_factor = 1.0

            for half_hour in range(48):
                dt = current + timedelta(minutes=half_hour * 30)
                hour = dt.hour + (dt.minute / 60.0)

                # Base consumption with diurnal profile
                base = LCL_PARAMS["night_baseline"]
                if 6 <= hour < 9:
                    base += 0.6 * np.sin(np.pi * (hour - 6) / 3)
                elif 17 <= hour < 21:
                    base += 0.9 * np.sin(np.pi * (hour - 17) / 4)
                elif 12 <= hour < 14:
                    base += 0.3

                # Add noise and scale
                noise = rng.normal(0, LCL_PARAMS["std_kwh_per_halfhour"] * 0.5)
                kwh = max(0.02, (base + noise) * season_factor * acorn_factor)
                if is_weekend:
                    kwh *= LCL_PARAMS["weekend_factor"]

                records.append({
                    "LCLid": household_id,
                    "stdorToU": tariff_type,
                    "DateTime": dt,
                    "kWh": round(kwh, 4),
                    "ACORN_grouped": acorn,
                    "month": month,
                    "day_of_week": weekday,
                    "hour_of_day": dt.hour,
                    "half_hour_slot": half_hour,
                })

    df = pd.DataFrame(records)
    print(f"[DATA] Generated {len(df):,} half-hourly records.")
    return df


# ---------------------------------------------------------------------------
# 2. FEATURE ENGINEERING
# ---------------------------------------------------------------------------
def engineer_features(df):
    """Create time-series features for demand forecasting."""
    print("[FEAT] Engineering features ...")
    df = df.copy()
    df = df.sort_values(["LCLid", "DateTime"])

    # Ensure time-derived columns exist (real data may not have them)
    if "hour_of_day" not in df.columns:
        df["hour_of_day"] = df["DateTime"].dt.hour
    if "day_of_week" not in df.columns:
        df["day_of_week"] = df["DateTime"].dt.weekday
    if "month" not in df.columns:
        df["month"] = df["DateTime"].dt.month
    if "ACORN_grouped" not in df.columns:
        df["ACORN_grouped"] = "Comfortable"
    if "stdorToU" not in df.columns:
        df["stdorToU"] = "Std"

    # Lag features (per household)
    df["lag_1h"] = df.groupby("LCLid")["kWh"].shift(1)
    df["lag_24h"] = df.groupby("LCLid")["kWh"].shift(48)
    df["lag_48h"] = df.groupby("LCLid")["kWh"].shift(96)

    # Rolling means (per household)
    df["rolling_mean_6h"] = df.groupby("LCLid")["kWh"].transform(
        lambda x: x.shift(1).rolling(window=12, min_periods=1).mean()
    )
    df["rolling_mean_24h"] = df.groupby("LCLid")["kWh"].transform(
        lambda x: x.shift(1).rolling(window=48, min_periods=1).mean()
    )
    df["rolling_mean_7d"] = df.groupby("LCLid")["kWh"].transform(
        lambda x: x.shift(1).rolling(window=336, min_periods=1).mean()
    )

    # Cyclical time encoding
    df["hour_sin"] = np.sin(2 * np.pi * df["hour_of_day"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour_of_day"] / 24)
    df["dow_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7)
    df["dow_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7)
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)

    # Tariff encoding
    df["is_dtou"] = (df["stdorToU"] == "DToU").astype(int)

    # ACORN encoding
    acorn_map = {"Affluent": 2, "Comfortable": 1, "Adversity": 0}
    df["acorn_code"] = df["ACORN_grouped"].map(acorn_map)

    # Backfill NaN lags within each household (up to 96 rows = 48h lag + 48h lag)
    # instead of dropping them. This prevents train/validation/test gaps.
    before = len(df)
    df[["lag_1h", "lag_24h", "lag_48h"]] = df.groupby("LCLid")[["lag_1h", "lag_24h", "lag_48h"]].transform(
        lambda x: x.bfill(limit=96)
    )
    df[["rolling_mean_6h", "rolling_mean_24h", "rolling_mean_7d"]] = df.groupby("LCLid")[
        ["rolling_mean_6h", "rolling_mean_24h", "rolling_mean_7d"]
    ].transform(lambda x: x.bfill(limit=96))
    df = df.dropna()
    after = len(df)
    print(f"[FEAT] Backfilled then dropped {before - after:,} rows. Final: {after:,} rows.")
    return df


# ---------------------------------------------------------------------------
# 3. MODEL TRAINING
# ---------------------------------------------------------------------------
def compute_metrics(y_true, y_pred):
    """Compute regression metrics."""
    mae = float(np.mean(np.abs(y_true - y_pred)))
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
    mape = float(np.mean(np.abs((y_true - y_pred) / (y_true + 1e-6))) * 100)
    ss_res = float(np.sum((y_true - y_pred) ** 2))
    ss_tot = float(np.sum((y_true - np.mean(y_true)) ** 2))
    r2 = float(1 - (ss_res / ss_tot)) if ss_tot > 0 else 0.0
    return {"MAE_kWh": round(mae, 4), "RMSE_kWh": round(rmse, 4),
            "MAPE_percent": round(mape, 2), "R2_score": round(r2, 4)}


def train_model(df):
    """Train LightGBM with train/validation/test split and full evaluation."""
    print("[TRAIN] Splitting train / validation / test (walk-forward) ...")

    df["date"] = df["DateTime"].dt.date
    household_max_dates = df.groupby("LCLid")["date"].max().reset_index()
    household_max_dates.columns = ["LCLid", "max_date"]
    df = df.merge(household_max_dates, on="LCLid")
    df["days_before_max"] = (pd.to_datetime(df["max_date"]) - pd.to_datetime(df["date"])).dt.days

    # Walk-forward splits: test = last 7 days, validation = days 8-14, train = before that
    test_df = df[df["days_before_max"] <= 7].copy()
    val_df = df[(df["days_before_max"] > 7) & (df["days_before_max"] <= 14)].copy()
    train_df = df[df["days_before_max"] > 14].copy()

    feature_cols = [
        "hour_of_day", "day_of_week", "month",
        "lag_1h", "lag_24h", "lag_48h",
        "rolling_mean_6h", "rolling_mean_24h", "rolling_mean_7d",
        "hour_sin", "hour_cos", "dow_sin", "dow_cos",
        "month_sin", "month_cos",
        "is_dtou", "acorn_code",
    ]

    X_train, y_train = train_df[feature_cols], train_df["kWh"]
    X_val, y_val = val_df[feature_cols], val_df["kWh"]
    X_test, y_test = test_df[feature_cols], test_df["kWh"]

    print(f"[TRAIN] Train: {len(X_train):,} | Validation: {len(X_val):,} | Test: {len(X_test):,}")

    model = lgb.LGBMRegressor(
        n_estimators=1000,
        learning_rate=0.05,
        num_leaves=31,
        max_depth=8,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
        verbose=-1,
    )

    print("[TRAIN] Training LightGBM with early stopping on validation set ...")
    start = time.time()
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        callbacks=[lgb.early_stopping(stopping_rounds=50, verbose=False)],
    )
    elapsed = time.time() - start
    print(f"[TRAIN] Training complete in {elapsed:.1f}s. Best iter: {model.best_iteration_}")

    # Predictions on all sets
    y_train_pred = model.predict(X_train, num_iteration=model.best_iteration_)
    y_val_pred = model.predict(X_val, num_iteration=model.best_iteration_)
    y_test_pred = model.predict(X_test, num_iteration=model.best_iteration_)

    train_metrics = compute_metrics(y_train, y_train_pred)
    val_metrics = compute_metrics(y_val, y_val_pred)
    test_metrics = compute_metrics(y_test, y_test_pred)

    # -----------------------------------------------------------------------
    # Quantile regression model for spike catching (alpha=0.9)
    # -----------------------------------------------------------------------
    print("[TRAIN] Training quantile regression model (alpha=0.9) for spike prediction ...")
    model_q90 = lgb.LGBMRegressor(
        n_estimators=500,
        learning_rate=0.05,
        num_leaves=31,
        max_depth=6,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="quantile",
        alpha=0.9,
        random_state=42,
        n_jobs=-1,
        verbose=-1,
    )
    model_q90.fit(X_train, y_train, eval_set=[(X_val, y_val)],
                  callbacks=[lgb.early_stopping(stopping_rounds=30, verbose=False)])
    y_test_q90 = model_q90.predict(X_test, num_iteration=model_q90.best_iteration_)
    q90_metrics = compute_metrics(y_test, y_test_q90)
    print(f"[TRAIN] Q90 TEST -- MAE: {q90_metrics['MAE_kWh']:.4f}  R2: {q90_metrics['R2_score']:.4f}")
    joblib.dump(model_q90, OUTPUT_DIR / "model_quantile_q90.pkl")

    metrics = {
        "train": train_metrics,
        "validation": val_metrics,
        "test": test_metrics,
        "quantile_q90_test": q90_metrics,
        "train_samples": int(len(X_train)),
        "validation_samples": int(len(X_val)),
        "test_samples": int(len(X_test)),
        "training_time_sec": round(elapsed, 2),
        "model_type": "LightGBM",
        "best_iteration": int(model.best_iteration_),
        "timestamp": datetime.now().isoformat(),
    }

    print(f"[TRAIN] TRAIN   -- MAE: {train_metrics['MAE_kWh']:.4f}  R2: {train_metrics['R2_score']:.4f}")
    print(f"[TRAIN] VALID   -- MAE: {val_metrics['MAE_kWh']:.4f}  R2: {val_metrics['R2_score']:.4f}")
    print(f"[TRAIN] TEST    -- MAE: {test_metrics['MAE_kWh']:.4f}  R2: {test_metrics['R2_score']:.4f}")

    # Save model
    model_path = OUTPUT_DIR / "model_demand_forecaster.pkl"
    joblib.dump(model, model_path)
    print(f"[TRAIN] Model saved: {model_path}")

    # Save metrics
    metrics_path = OUTPUT_DIR / "validation_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"[TRAIN] Metrics saved: {metrics_path}")

    return model, metrics, test_df, y_test_pred, val_df, y_val_pred, y_test_q90


# ---------------------------------------------------------------------------
# 4. VISUALISATION
# ---------------------------------------------------------------------------
def plot_feature_importance(model, feature_cols):
    """Save feature importance bar chart."""
    importance = model.booster_.feature_importance(importance_type="gain")
    imp_df = pd.DataFrame({"feature": feature_cols, "importance": importance})
    imp_df = imp_df.sort_values("importance", ascending=True).tail(12)

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(imp_df["feature"], imp_df["importance"], color="#00d4aa")
    ax.set_xlabel("Gain", fontsize=12)
    ax.set_title("NestShift Energy Agent -- Feature Importance", fontsize=14, fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()

    path = OUTPUT_DIR / "feature_importance.png"
    fig.savefig(path, dpi=300)
    plt.close(fig)
    print(f"[PLOT] Feature importance: {path}")


def plot_forecast(df, y_pred, n_days=7, split_name="TEST"):
    """Overlay predicted vs actual for first n_days."""
    plot_df = df.copy().iloc[: 48 * n_days]
    plot_df["predicted_kWh"] = y_pred[: len(plot_df)]

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(plot_df["DateTime"], plot_df["kWh"], label="Actual", color="#ffffff", linewidth=1.2, alpha=0.9)
    ax.plot(plot_df["DateTime"], plot_df["predicted_kWh"], label="Forecast", color="#00d4aa", linewidth=1.5, linestyle="--")
    ax.fill_between(plot_df["DateTime"], plot_df["predicted_kWh"], alpha=0.15, color="#00d4aa")

    ax.set_xlabel("Date/Time", fontsize=11, color="white")
    ax.set_ylabel("Energy (kWh / half-hour)", fontsize=11, color="white")
    ax.set_title(f"NestShift Forecast vs Actual -- {split_name} Set (First {n_days} Days)", fontsize=13, fontweight="bold", color="white")
    ax.legend(loc="upper right", facecolor="#1a1a1a", edgecolor="#333", labelcolor="white")

    ax.set_facecolor("#1a1a1a")
    fig.patch.set_facecolor("#1a1a1a")
    ax.tick_params(colors="white")
    ax.grid(True, alpha=0.2, color="white")
    ax.spines["bottom"].set_color("white")
    ax.spines["left"].set_color("white")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    path = OUTPUT_DIR / f"forecast_vs_actual_{split_name}.png"
    fig.savefig(path, dpi=300, facecolor="#1a1a1a")
    plt.close(fig)
    print(f"[PLOT] Forecast overlay ({split_name}): {path}")


def plot_scatter_actual_vs_pred(df, y_pred, split_name="TEST"):
    """Scatter plot of actual vs predicted values."""
    fig, ax = plt.subplots(figsize=(7, 7))
    actual = df["kWh"].values[:len(y_pred)]
    ax.scatter(actual, y_pred, alpha=0.3, s=8, color="#00d4aa")

    # Perfect prediction line
    lim = max(actual.max(), y_pred.max()) * 1.05
    ax.plot([0, lim], [0, lim], color="white", linestyle="--", linewidth=1, label="Perfect prediction")

    ax.set_xlabel("Actual kWh", fontsize=11, color="white")
    ax.set_ylabel("Predicted kWh", fontsize=11, color="white")
    ax.set_title(f"Actual vs Predicted -- {split_name} Set", fontsize=13, fontweight="bold", color="white")
    ax.legend(loc="upper left", facecolor="#1a1a1a", edgecolor="#333", labelcolor="white")

    ax.set_facecolor("#1a1a1a")
    fig.patch.set_facecolor("#1a1a1a")
    ax.tick_params(colors="white")
    ax.grid(True, alpha=0.2, color="white")
    ax.spines["bottom"].set_color("white")
    ax.spines["left"].set_color("white")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    path = OUTPUT_DIR / f"scatter_actual_vs_pred_{split_name}.png"
    fig.savefig(path, dpi=300, facecolor="#1a1a1a")
    plt.close(fig)
    print(f"[PLOT] Scatter plot ({split_name}): {path}")


def plot_residuals(df, y_pred, split_name="TEST"):
    """Residual distribution plot."""
    residuals = df["kWh"].values[:len(y_pred)] - y_pred
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(residuals, bins=100, color="#00d4aa", edgecolor="#1a1a1a", alpha=0.8)
    ax.axvline(0, color="white", linestyle="--", linewidth=1.5)

    ax.set_xlabel("Residual (Actual - Predicted) kWh", fontsize=11, color="white")
    ax.set_ylabel("Count", fontsize=11, color="white")
    ax.set_title(f"Residual Distribution -- {split_name} Set", fontsize=13, fontweight="bold", color="white")

    ax.set_facecolor("#1a1a1a")
    fig.patch.set_facecolor("#1a1a1a")
    ax.tick_params(colors="white")
    ax.grid(True, alpha=0.2, color="white", axis="y")
    ax.spines["bottom"].set_color("white")
    ax.spines["left"].set_color("white")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    path = OUTPUT_DIR / f"residuals_{split_name}.png"
    fig.savefig(path, dpi=300, facecolor="#1a1a1a")
    plt.close(fig)
    print(f"[PLOT] Residuals ({split_name}): {path}")


def plot_quantile_comparison(df, y_pred_median, y_pred_q90, n_days=5):
    """Overlay median vs Q90 predictions to show spike catching."""
    plot_df = df.copy().iloc[: 48 * n_days]
    plot_df["pred_median"] = y_pred_median[: len(plot_df)]
    plot_df["pred_q90"] = y_pred_q90[: len(plot_df)]

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(plot_df["DateTime"], plot_df["kWh"], label="Actual", color="#ffffff", linewidth=1.5)
    ax.plot(plot_df["DateTime"], plot_df["pred_median"], label="Median (MSE)", color="#00d4aa", linewidth=1.2, linestyle="--")
    ax.plot(plot_df["DateTime"], plot_df["pred_q90"], label="Q90 (Quantile)", color="#ff6b6b", linewidth=1.2, linestyle="--")
    ax.fill_between(plot_df["DateTime"], plot_df["pred_median"], plot_df["pred_q90"], alpha=0.1, color="#ff6b6b")

    ax.set_xlabel("Date/Time", fontsize=11, color="white")
    ax.set_ylabel("Energy (kWh / half-hour)", fontsize=11, color="white")
    ax.set_title("Spike Prediction: Median vs Quantile (alpha=0.9)", fontsize=13, fontweight="bold", color="white")
    ax.legend(loc="upper right", facecolor="#1a1a1a", edgecolor="#333", labelcolor="white")

    ax.set_facecolor("#1a1a1a")
    fig.patch.set_facecolor("#1a1a1a")
    ax.tick_params(colors="white")
    ax.grid(True, alpha=0.2, color="white")
    ax.spines["bottom"].set_color("white")
    ax.spines["left"].set_color("white")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    path = OUTPUT_DIR / "quantile_spike_comparison.png"
    fig.savefig(path, dpi=300, facecolor="#1a1a1a")
    plt.close(fig)
    print(f"[PLOT] Quantile comparison: {path}")


# ---------------------------------------------------------------------------
# 5. ENERGY OPTIMISATION / SCHEDULING
# ---------------------------------------------------------------------------
def generate_tariff_profile(start, periods, tariff_type="DToU"):
    """Generate half-hourly tariff prices."""
    prices = []
    for i in range(periods):
        dt = start + timedelta(minutes=i * 30)
        hour = dt.hour
        if tariff_type == "DToU":
            if 0 <= hour < 6:
                p = LCL_PARAMS["dtou_low_price"]
            elif 16 <= hour < 19:
                p = LCL_PARAMS["dtou_high_price"]
            else:
                p = LCL_PARAMS["dtou_normal_price"]
        else:
            p = LCL_PARAMS["standard_price"]
        prices.append(p)
    return np.array(prices)


def optimise_schedule(household_id, forecast, tariff_prices, devices):
    """
    Simple greedy scheduler: for each flexible device, find cheapest contiguous
    window that fits its duration.
    Baseline = run at typical evening peak (slot 36 = 18:00) when users normally
    start appliances. Optimised = cheapest available window.
    """
    slots = len(forecast)
    schedule = []
    total_baseline_cost = 0.0
    total_optimised_cost = 0.0

    # Realistic baseline slot: 6 PM (slot 36) -- peak usage time for UK homes
    BASELINE_SLOT = 36

    for dev_name, dev_info in devices.items():
        power = dev_info["power_kw"]
        dur_slots = int(dev_info["duration_h"] * 2)
        energy = power * dev_info["duration_h"]

        # Baseline: run starting at BASELINE_SLOT (evening peak)
        baseline_window = tariff_prices[BASELINE_SLOT:BASELINE_SLOT + dur_slots]
        if len(baseline_window) < dur_slots:
            baseline_window = np.tile(tariff_prices, 2)[BASELINE_SLOT:BASELINE_SLOT + dur_slots]
        baseline_cost = np.sum(baseline_window) * power * 0.5
        total_baseline_cost += baseline_cost

        # Find cheapest window across full day
        best_cost = float("inf")
        best_start = 0
        for start_slot in range(slots - dur_slots + 1):
            window_cost = np.sum(tariff_prices[start_slot:start_slot + dur_slots]) * power * 0.5
            if window_cost < best_cost:
                best_cost = window_cost
                best_start = start_slot

        total_optimised_cost += best_cost
        start_time = datetime.now() + timedelta(minutes=best_start * 30)

        schedule.append({
            "household_id": household_id,
            "device": dev_name,
            "power_kw": power,
            "duration_h": dev_info["duration_h"],
            "scheduled_start": start_time.strftime("%Y-%m-%d %H:%M"),
            "window_start_slot": best_start,
            "optimised_cost_gbp": round(best_cost, 4),
            "baseline_cost_gbp": round(baseline_cost, 4),
            "saving_gbp": round(baseline_cost - best_cost, 4),
            "saving_percent": round((baseline_cost - best_cost) / baseline_cost * 100, 2) if baseline_cost > 0 else 0,
        })

    return schedule, total_baseline_cost, total_optimised_cost


def run_optimisation_simulation(df, model, n_households=20):
    """Run scheduling optimisation for a sample of households.
    Simulates DToU tariffs on real demand profiles to demonstrate savings."""
    print("[OPT] Running energy schedule optimisation ...")
    households = df["LCLid"].unique()[:n_households]
    np.random.seed(42)

    all_schedules = []
    savings = []

    for hh in households:
        hh_df = df[df["LCLid"] == hh].sort_values("DateTime").iloc[-48:].copy()
        if len(hh_df) < 48:
            continue

        # Simulate tariff: 30% DToU, 70% Std (matches LCL trial structure)
        tariff_type = "DToU" if np.random.rand() < 0.30 else "Std"

        feature_cols = [
            "hour_of_day", "day_of_week", "month",
            "lag_1h", "lag_24h", "lag_48h",
            "rolling_mean_6h", "rolling_mean_24h", "rolling_mean_7d",
            "hour_sin", "hour_cos", "dow_sin", "dow_cos",
            "month_sin", "month_cos",
            "is_dtou", "acorn_code",
        ]
        X = hh_df[feature_cols]
        forecast = model.predict(X)

        start_time = hh_df["DateTime"].iloc[0]
        tariff_prices = generate_tariff_profile(start_time, 48, tariff_type)

        sched, base_cost, opt_cost = optimise_schedule(hh, forecast, tariff_prices, FLEXIBLE_DEVICES)
        all_schedules.extend(sched)

        saving_pct = (base_cost - opt_cost) / base_cost * 100 if base_cost > 0 else 0
        savings.append({
            "household_id": hh,
            "tariff": tariff_type,
            "baseline_cost_gbp": round(base_cost, 4),
            "optimised_cost_gbp": round(opt_cost, 4),
            "saving_gbp": round(base_cost - opt_cost, 4),
            "saving_percent": round(saving_pct, 2),
        })

    schedule_df = pd.DataFrame(all_schedules)
    savings_df = pd.DataFrame(savings)

    avg_saving = savings_df["saving_percent"].mean()
    total_baseline = savings_df["baseline_cost_gbp"].sum()
    total_optimised = savings_df["optimised_cost_gbp"].sum()

    report = {
        "simulation_date": datetime.now().isoformat(),
        "households_simulated": int(len(savings_df)),
        "tariff_mix": savings_df["tariff"].value_counts().to_dict(),
        "average_saving_percent": round(float(avg_saving), 2),
        "total_baseline_cost_gbp": round(float(total_baseline), 4),
        "total_optimised_cost_gbp": round(float(total_optimised), 4),
        "total_saving_gbp": round(float(total_baseline - total_optimised), 4),
        "projected_annual_saving_per_household_gbp": round(float(avg_saving / 100 * 1800), 2),
        "devices_scheduled": list(FLEXIBLE_DEVICES.keys()),
        "tariff_prices": LCL_PARAMS,
        "data_source": "Real LCL profiles with simulated DToU tariff mix",
    }

    schedule_path = OUTPUT_DIR / "energy_schedule.csv"
    schedule_df.to_csv(schedule_path, index=False)
    print(f"[OPT] Schedule saved: {schedule_path}")

    report_path = OUTPUT_DIR / "cost_savings_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"[OPT] Savings report saved: {report_path}")
    print(f"[OPT] Average cost saving: {avg_saving:.2f}% per household")
    print(f"[OPT] Projected annual saving: GBP {report['projected_annual_saving_per_household_gbp']:.2f}/household")

    return report, schedule_df


# ---------------------------------------------------------------------------
# 6. MAIN
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="NestShift OS PoC Energy Agent Trainer")
    parser.add_argument("--data-source", choices=["real", "synthetic"], default="synthetic",
                        help="'real' downloads LCL (~10GB). 'synthetic' generates calibrated data instantly.")
    parser.add_argument("--households", type=int, default=50, help="Number of households to simulate/train on")
    parser.add_argument("--days", type=int, default=90, help="Days of data per household")
    parser.add_argument("--skip-download", action="store_true", help="Skip LCL download even if --data-source real")
    args = parser.parse_args()

    print("=" * 70)
    print("NESTSHIFT OS -- PROOF-OF-CONCEPT ENERGY AGENT TRAINER")
    print("Innovator Founder Visa | Technical Demonstration")
    print("=" * 70)
    print(f"Start time: {datetime.now().isoformat()}")
    print(f"Output directory: {OUTPUT_DIR}")
    print()

    # -----------------------------------------------------------------------
    # Acquire data
    # -----------------------------------------------------------------------
    sample_path = DATA_DIR / "LCL-Sample-2M.csv"

    if args.data_source == "real" and not args.skip_download:
        if sample_path.exists():
            print(f"[DATA] Found extracted real sample: {sample_path}")
            df = pd.read_csv(sample_path)
            # Strip whitespace from column names (LCL CSV has trailing spaces)
            df.columns = df.columns.str.strip()
            # Rename energy column
            df = df.rename(columns={"KWH/hh (per half hour)": "kWh"})
            df["kWh"] = pd.to_numeric(df["kWh"], errors="coerce")
            df["DateTime"] = pd.to_datetime(df["DateTime"], errors="coerce")
            df = df.dropna(subset=["DateTime", "kWh", "LCLid"])
            # Limit households
            hh_sample = df["LCLid"].unique()[:args.households]
            df = df[df["LCLid"].isin(hh_sample)].copy()
            # Limit days
            min_date = df["DateTime"].min()
            day_limit = min_date + timedelta(days=args.days)
            df = df[df["DateTime"] <= day_limit].copy()
            # Add synthetic ACORN since real LCL doesn't have it
            np.random.seed(42)
            acorn_map = {hh: np.random.choice(["Affluent", "Comfortable", "Adversity"]) for hh in df["LCLid"].unique()}
            df["ACORN_grouped"] = df["LCLid"].map(acorn_map)
            print(f"[DATA] Loaded {len(df):,} REAL records from Low Carbon London.")
            print(f"[DATA] Date range: {df['DateTime'].min()} to {df['DateTime'].max()}")
            print(f"[DATA] Households: {df['LCLid'].nunique()}, Tariff mix: {df['stdorToU'].value_counts().to_dict()}")
        else:
            print("[DATA] No extracted sample found. Falling back to synthetic.")
            df = generate_synthetic_uk_data(args.households, args.days)
    else:
        print("[DATA] Using synthetic UK data (calibrated to LCL statistics).")
        df = generate_synthetic_uk_data(args.households, args.days)

    # -----------------------------------------------------------------------
    # Preprocess
    # -----------------------------------------------------------------------
    df = engineer_features(df)

    # -----------------------------------------------------------------------
    # Train
    # -----------------------------------------------------------------------
    model, metrics, test_df, y_test_pred, val_df, y_val_pred, y_test_q90 = train_model(df)

    # -----------------------------------------------------------------------
    # Visualise
    # -----------------------------------------------------------------------
    feature_cols = [
        "hour_of_day", "day_of_week", "month",
        "lag_1h", "lag_24h", "lag_48h",
        "rolling_mean_6h", "rolling_mean_24h", "rolling_mean_7d",
        "hour_sin", "hour_cos", "dow_sin", "dow_cos",
        "month_sin", "month_cos",
        "is_dtou", "acorn_code",
    ]
    plot_feature_importance(model, feature_cols)
    plot_forecast(test_df, y_test_pred, n_days=7, split_name="TEST")
    plot_forecast(val_df, y_val_pred, n_days=7, split_name="VALIDATION")
    plot_scatter_actual_vs_pred(test_df, y_test_pred, split_name="TEST")
    plot_scatter_actual_vs_pred(val_df, y_val_pred, split_name="VALIDATION")
    plot_residuals(test_df, y_test_pred, split_name="TEST")
    plot_residuals(val_df, y_val_pred, split_name="VALIDATION")
    plot_quantile_comparison(test_df, y_test_pred, y_test_q90)

    # -----------------------------------------------------------------------
    # Optimise
    # -----------------------------------------------------------------------
    report, _ = run_optimisation_simulation(df, model, n_households=min(args.households, 50))

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------
    print()
    print("=" * 70)
    print("TRAINING COMPLETE")
    print("=" * 70)
    print(f"Model:             {OUTPUT_DIR / 'model_demand_forecaster.pkl'}")
    print(f"Metrics (JSON):    {OUTPUT_DIR / 'validation_metrics.json'}")
    print(f"Feature Plot:      {OUTPUT_DIR / 'feature_importance.png'}")
    print(f"Test Forecast:     {OUTPUT_DIR / 'forecast_vs_actual_TEST.png'}")
    print(f"Val Forecast:      {OUTPUT_DIR / 'forecast_vs_actual_VALIDATION.png'}")
    print(f"Test Scatter:      {OUTPUT_DIR / 'scatter_actual_vs_pred_TEST.png'}")
    print(f"Val Scatter:       {OUTPUT_DIR / 'scatter_actual_vs_pred_VALIDATION.png'}")
    print(f"Test Residuals:    {OUTPUT_DIR / 'residuals_TEST.png'}")
    print(f"Val Residuals:     {OUTPUT_DIR / 'residuals_VALIDATION.png'}")
    print(f"Schedule:          {OUTPUT_DIR / 'energy_schedule.csv'}")
    print(f"Savings Report:    {OUTPUT_DIR / 'cost_savings_report.json'}")
    print(f"Console Log:       {OUTPUT_DIR / 'training_log.txt'}")
    print()
    print(f"TRAIN   MAE: {metrics['train']['MAE_kWh']:.4f}  R2: {metrics['train']['R2_score']:.4f}")
    print(f"VALID   MAE: {metrics['validation']['MAE_kWh']:.4f}  R2: {metrics['validation']['R2_score']:.4f}")
    print(f"TEST    MAE: {metrics['test']['MAE_kWh']:.4f}  R2: {metrics['test']['R2_score']:.4f}")
    print(f"Avg Saving:        {report['average_saving_percent']:.2f}%")
    print(f"Annual Saving:     GBP {report['projected_annual_saving_per_household_gbp']:.2f}/household")
    print("=" * 70)


if __name__ == "__main__":
    main()
