#!/usr/bin/env python3
"""Learning curve analysis: cost and comfort over time.

Shows how the proposed system improves from cold-start to convergence.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from env.household import Household
from env.tariff import AgileTariff
from env.simulator import Simulator, SimulationConfig, analyze_outcomes
from controllers import no_optimization_controller, hybrid_controller
from agents.energy_agent import EnergyAgent
from agents.automation_agent import AutomationAgent


def run_learning_curve(days=90, seed=42):
    """Run a single long simulation and track daily metrics."""
    household = Household(seed=seed)
    tariff = AgileTariff(seed=seed)
    config = SimulationConfig(days=days, seed=seed)
    sim = Simulator(household, tariff, config)

    energy_agent = EnergyAgent(comfort_bias=0.5)
    automation_agent = AutomationAgent()

    outcomes = sim.run_with_learning(
        hybrid_controller, energy_agent, automation_agent
    )

    # Daily aggregation
    daily_costs = {}
    daily_comfort = {}
    daily_energy = {}

    for o in outcomes:
        daily_costs[o.day] = daily_costs.get(o.day, 0) + o.cost_gbp
        daily_comfort[o.day] = daily_comfort.get(o.day, 0) + o.comfort_penalty
        daily_energy[o.day] = daily_energy.get(o.day, 0) + o.energy_kwh

    days_list = sorted(daily_costs.keys())
    costs = [daily_costs[d] for d in days_list]
    comforts = [daily_comfort[d] for d in days_list]
    energies = [daily_energy[d] for d in days_list]

    # Compute 7-day rolling average
    window = 7
    rolling_cost = []
    for i in range(len(costs)):
        start = max(0, i - window + 1)
        rolling_cost.append(np.mean(costs[start:i+1]))

    return {
        "days": days_list,
        "daily_costs": costs,
        "daily_comfort": comforts,
        "daily_energy": energies,
        "rolling_cost": rolling_cost,
        "automation_confidence": automation_agent.get_metrics()["confidence"],
        "total_events": automation_agent.get_metrics()["total_events"],
    }


def plot_learning_curve(data: dict, baseline_cost: float, output_path: str):
    """Plot learning curve with baseline comparison."""
    fig, axes = plt.subplots(2, 1, figsize=(10, 8))

    days = data["days"]

    # Cost subplot
    ax = axes[0]
    ax.plot(days, data["daily_costs"], alpha=0.3, color='blue', label='Daily cost')
    ax.plot(days, data["rolling_cost"], color='blue', linewidth=2, label='7-day average')
    ax.axhline(y=baseline_cost, color='red', linestyle='--', label='No-optimization baseline')
    ax.set_ylabel('Daily Cost (£)')
    ax.set_title('Learning Curve: Energy Cost Over Time (Agile Tariff)')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Comfort subplot
    ax = axes[1]
    ax.plot(days, data["daily_comfort"], color='green', alpha=0.7)
    ax.set_ylabel('Daily Comfort Penalty')
    ax.set_xlabel('Day')
    ax.set_title('Comfort Penalty Over Time')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    print(f"📊 Learning curve saved to {output_path}")


def main():
    print("=" * 60)
    print("LEARNING CURVE ANALYSIS")
    print("=" * 60)

    # First get baseline cost
    print("\nComputing no-optimization baseline...")
    from env.household import Household
    from env.tariff import AgileTariff
    from env.simulator import Simulator, SimulationConfig
    from controllers import no_optimization_controller

    household = Household(seed=42)
    tariff = AgileTariff(seed=42)
    config = SimulationConfig(days=90, seed=42)
    sim = Simulator(household, tariff, config)
    baseline_outcomes = sim.run(no_optimization_controller)
    baseline_metrics = analyze_outcomes(baseline_outcomes)
    baseline_daily = baseline_metrics["avg_daily_cost"]
    print(f"Baseline daily cost: £{baseline_daily:.2f}")

    # Run learning curve
    print("\nRunning 90-day learning simulation...")
    data = run_learning_curve(days=90, seed=42)

    print(f"\nFinal 7-day avg cost: £{data['rolling_cost'][-1]:.2f}")
    print(f"Automation confidence: {data['automation_confidence']:.2f}")
    print(f"Total learned events: {data['total_events']}")

    # Plot
    plot_learning_curve(data, baseline_daily, "simulation/results/learning_curve.png")

    return 0


if __name__ == "__main__":
    sys.exit(main())
