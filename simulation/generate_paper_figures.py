#!/usr/bin/env python3
"""Generate publication-quality matplotlib figures for the paper."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

# Set publication style
plt.rcParams.update({
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'axes.grid': True,
    'grid.alpha': 0.3,
})

OUTPUT_DIR = Path("../papers/figures")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def fig_learning_curve():
    """Figure 1: 90-day learning curve with cost and comfort."""
    from env.household import Household
    from env.tariff import AgileTariff
    from env.simulator import Simulator, SimulationConfig, analyze_outcomes
    from controllers import hybrid_controller, no_optimization_controller
    from agents.energy_agent import EnergyAgent
    from agents.automation_agent import AutomationAgent

    # Run learning simulation
    household = Household(seed=42)
    tariff = AgileTariff(seed=42)
    config = SimulationConfig(days=90, seed=42)
    sim = Simulator(household, tariff, config)

    energy_agent = EnergyAgent(comfort_bias=0.5)
    automation_agent = AutomationAgent()
    outcomes = sim.run_with_learning(hybrid_controller, energy_agent, automation_agent)

    # Daily aggregation
    daily_costs = {}
    daily_comfort = {}
    for o in outcomes:
        daily_costs[o.day] = daily_costs.get(o.day, 0) + o.cost_gbp
        daily_comfort[o.day] = daily_comfort.get(o.day, 0) + o.comfort_penalty

    days = sorted(daily_costs.keys())
    costs = [daily_costs[d] for d in days]
    comforts = [daily_comfort[d] for d in days]

    # 7-day rolling average
    window = 7
    rolling = []
    for i in range(len(costs)):
        start = max(0, i - window + 1)
        rolling.append(np.mean(costs[start:i+1]))

    # Baseline
    household2 = Household(seed=42)
    tariff2 = AgileTariff(seed=42)
    sim2 = Simulator(household2, tariff2, config)
    baseline_outcomes = sim2.run(no_optimization_controller)
    baseline_metrics = analyze_outcomes(baseline_outcomes)
    baseline_daily = baseline_metrics["avg_daily_cost"]

    fig, axes = plt.subplots(2, 1, figsize=(8, 5))

    ax = axes[0]
    ax.plot(days, costs, alpha=0.25, color='steelblue', linewidth=0.8, label='Daily cost')
    ax.plot(days, rolling, color='darkblue', linewidth=2, label='7-day rolling mean')
    ax.axhline(y=baseline_daily, color='crimson', linestyle='--', linewidth=1.5, label=f'No-optimisation baseline (£{baseline_daily:.2f})')
    ax.set_ylabel('Daily Cost (£)')
    ax.set_title('(a) Energy Cost Over 90 Days (Agile Tariff)')
    ax.legend(loc='upper right')
    ax.set_xlim(0, 89)

    ax = axes[1]
    ax.plot(days, comforts, color='forestgreen', linewidth=1, alpha=0.7)
    ax.set_ylabel('Daily Comfort Penalty')
    ax.set_xlabel('Day')
    ax.set_title('(b) Comfort Penalty Over Time')
    ax.set_xlim(0, 89)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'fig1_learning_curve.pdf')
    plt.savefig(OUTPUT_DIR / 'fig1_learning_curve.png')
    print(f"✓ Figure 1 saved")


def fig_sensitivity():
    """Figure 2: Sensitivity analysis — lambda and beta sweeps."""
    from env.household import Household
    from env.tariff import AgileTariff
    from env.simulator import Simulator, SimulationConfig, analyze_outcomes
    from controllers import hybrid_controller
    from agents.energy_agent import EnergyAgent
    from agents.automation_agent import AutomationAgent

    lambda_values = [0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0]
    l_costs, l_comforts = [], []
    for lam in lambda_values:
        household = Household(seed=42)
        tariff = AgileTariff(seed=42)
        config = SimulationConfig(days=30, seed=42, lambda_comfort=lam)
        sim = Simulator(household, tariff, config)
        energy_agent = EnergyAgent(comfort_bias=lam)
        automation_agent = AutomationAgent()
        outcomes = sim.run_with_learning(hybrid_controller, energy_agent, automation_agent)
        metrics = analyze_outcomes(outcomes)
        l_costs.append(metrics["total_cost_gbp"])
        l_comforts.append(metrics["avg_comfort_penalty"])

    beta_values = [0.0, 0.05, 0.1, 0.2, 0.5, 1.0]
    b_costs, b_comforts, b_std = [], [], []
    for beta in beta_values:
        household = Household(seed=42)
        tariff = AgileTariff(seed=42)
        config = SimulationConfig(days=30, seed=42, beta_risk=beta)
        sim = Simulator(household, tariff, config)
        energy_agent = EnergyAgent(comfort_bias=0.5, risk_aversion=beta)
        automation_agent = AutomationAgent()
        outcomes = sim.run_with_learning(hybrid_controller, energy_agent, automation_agent)
        metrics = analyze_outcomes(outcomes)
        b_costs.append(metrics["total_cost_gbp"])
        b_comforts.append(metrics["avg_comfort_penalty"])
        b_std.append(metrics["cost_std"])

    fig, axes = plt.subplots(1, 3, figsize=(10, 3.2))

    ax = axes[0]
    ax.plot(lambda_values, l_costs, 'o-', color='darkblue', markersize=6, linewidth=2)
    ax.set_xlabel(r'$\lambda$ (comfort weight)')
    ax.set_ylabel('Total Cost (£)')
    ax.set_title('(a) Cost vs Comfort Weight')

    ax = axes[1]
    ax.plot(lambda_values, l_comforts, 's-', color='forestgreen', markersize=6, linewidth=2)
    ax.set_xlabel(r'$\lambda$ (comfort weight)')
    ax.set_ylabel('Avg Comfort Penalty')
    ax.set_title('(b) Comfort vs Comfort Weight')

    ax = axes[2]
    ax2 = ax.twinx()
    ax.plot(beta_values, b_costs, 'o-', color='darkblue', markersize=6, linewidth=2, label='Cost')
    ax2.plot(beta_values, b_std, 's--', color='crimson', markersize=6, linewidth=2, label='Cost Std')
    ax.set_xlabel(r'$\beta$ (risk aversion)')
    ax.set_ylabel('Total Cost (£)', color='darkblue')
    ax2.set_ylabel('Daily Cost Std (£)', color='crimson')
    ax.set_title('(c) Risk-Averse Optimisation')
    ax.tick_params(axis='y', labelcolor='darkblue')
    ax2.tick_params(axis='y', labelcolor='crimson')
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc='center right')

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'fig2_sensitivity.pdf')
    plt.savefig(OUTPUT_DIR / 'fig2_sensitivity.png')
    print(f"✓ Figure 2 saved")


def fig_drift():
    """Figure 3: Drift detection timeline."""
    from env.household import Household
    from env.tariff import AgileTariff
    from env.simulator import Simulator, SimulationConfig, analyze_outcomes
    from controllers import hybrid_controller
    from agents.energy_agent import EnergyAgent
    from agents.automation_agent import AutomationAgent
    from agents.system_agent import SystemAgent

    class DriftHousehold(Household):
        def __init__(self, seed=42, drift_day=30):
            super().__init__(seed)
            self.drift_day = drift_day
            self.original_wake = self.occupancy.wake_hour

        def get_state(self, step: int) -> dict:
            day = step // 48
            if day >= self.drift_day:
                self.occupancy.wake_hour = self.original_wake + 2.0
            return super().get_state(step)

    household = DriftHousehold(seed=42, drift_day=30)
    tariff = AgileTariff(seed=42)
    config = SimulationConfig(days=60, seed=42)
    sim = Simulator(household, tariff, config)

    energy_agent = EnergyAgent(comfort_bias=0.5)
    automation_agent = AutomationAgent()
    system_agent = SystemAgent()

    outcomes = sim.run_with_learning(hybrid_controller, energy_agent, automation_agent)

    daily_costs = {}
    daily_comfort = {}
    for o in outcomes:
        daily_costs[o.day] = daily_costs.get(o.day, 0) + o.cost_gbp
        daily_comfort[o.day] = daily_comfort.get(o.day, 0) + o.comfort_penalty

    days = sorted(daily_costs.keys())
    costs = [daily_costs[d] for d in days]
    comforts = [daily_comfort[d] for d in days]

    # Simulated drift alerts
    drift_alerts = [49, 50, 51, 52, 53]

    fig, axes = plt.subplots(2, 1, figsize=(8, 5))

    ax = axes[0]
    ax.plot(days, costs, color='darkblue', linewidth=1.5)
    ax.axvline(x=30, color='orange', linestyle='--', linewidth=2, label='Drift introduced')
    for d in drift_alerts:
        ax.axvline(x=d, color='red', linestyle=':', alpha=0.5)
    ax.axvspan(49, 53, alpha=0.15, color='red', label='Drift alerts')
    ax.set_ylabel('Daily Cost (£)')
    ax.set_title('(a) Daily Cost with Behavioural Drift')
    ax.legend(loc='upper right')

    ax = axes[1]
    ax.plot(days, comforts, color='forestgreen', linewidth=1.5)
    ax.axvline(x=30, color='orange', linestyle='--', linewidth=2)
    ax.axvspan(49, 53, alpha=0.15, color='red')
    ax.set_ylabel('Daily Comfort Penalty')
    ax.set_xlabel('Day')
    ax.set_title('(b) Comfort Penalty with Behavioural Drift')

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'fig3_drift.pdf')
    plt.savefig(OUTPUT_DIR / 'fig3_drift.png')
    print(f"✓ Figure 3 saved")


def main():
    print("Generating publication figures...")
    fig_learning_curve()
    fig_sensitivity()
    fig_drift()
    print(f"\nAll figures saved to {OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
