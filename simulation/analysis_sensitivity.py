#!/usr/bin/env python3
"""Sensitivity analysis: sweep lambda (comfort-cost trade-off) and beta (risk).
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np

from env.household import Household
from env.tariff import AgileTariff
from env.simulator import Simulator, SimulationConfig, analyze_outcomes
from controllers import hybrid_controller
from agents.energy_agent import EnergyAgent
from agents.automation_agent import AutomationAgent


def run_lambda_sweep(lambda_values, days=30, seed=42):
    """Run simulations with different comfort-cost biases."""
    results = []
    for lam in lambda_values:
        household = Household(seed=seed)
        tariff = AgileTariff(seed=seed)
        config = SimulationConfig(days=days, seed=seed, lambda_comfort=lam)
        sim = Simulator(household, tariff, config)

        energy_agent = EnergyAgent(comfort_bias=lam)
        automation_agent = AutomationAgent()

        outcomes = sim.run_with_learning(
            hybrid_controller, energy_agent, automation_agent
        )
        metrics = analyze_outcomes(outcomes)
        results.append({
            "lambda": lam,
            "cost": metrics["total_cost_gbp"],
            "comfort": metrics["avg_comfort_penalty"],
            "energy": metrics["total_energy_kwh"],
        })
    return results


def run_beta_sweep(beta_values, days=30, seed=42):
    """Run simulations with different risk aversion levels."""
    results = []
    for beta in beta_values:
        household = Household(seed=seed)
        tariff = AgileTariff(seed=seed)
        config = SimulationConfig(days=days, seed=seed, beta_risk=beta)
        sim = Simulator(household, tariff, config)

        energy_agent = EnergyAgent(comfort_bias=0.5, risk_aversion=beta)
        automation_agent = AutomationAgent()

        outcomes = sim.run_with_learning(
            hybrid_controller, energy_agent, automation_agent
        )
        metrics = analyze_outcomes(outcomes)
        results.append({
            "beta": beta,
            "cost": metrics["total_cost_gbp"],
            "comfort": metrics["avg_comfort_penalty"],
            "cost_std": metrics["cost_std"],
        })
    return results


def main():
    print("=" * 60)
    print("SENSITIVITY ANALYSIS")
    print("=" * 60)

    # Lambda sweep
    print("\n--- Lambda (comfort-cost bias) sweep ---")
    lambda_values = [0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0]
    lambda_results = run_lambda_sweep(lambda_values, days=30, seed=42)

    print(f"{'λ':>6} {'Cost (£)':>10} {'Comfort':>10} {'Energy':>10}")
    print("-" * 40)
    for r in lambda_results:
        print(f"{r['lambda']:>6.2f} {r['cost']:>10.2f} {r['comfort']:>10.4f} {r['energy']:>10.1f}")

    # Beta sweep
    print("\n--- Beta (risk aversion) sweep ---")
    beta_values = [0.0, 0.05, 0.1, 0.2, 0.5, 1.0]
    beta_results = run_beta_sweep(beta_values, days=30, seed=42)

    print(f"{'β':>6} {'Cost (£)':>10} {'Comfort':>10} {'Cost Std':>10}")
    print("-" * 40)
    for r in beta_results:
        print(f"{r['beta']:>6.2f} {r['cost']:>10.2f} {r['comfort']:>10.4f} {r['cost_std']:>10.2f}")

    # Save results
    import json
    Path("simulation/results").mkdir(parents=True, exist_ok=True)
    with open("simulation/results/sensitivity_analysis.json", "w") as f:
        json.dump({"lambda": lambda_results, "beta": beta_results}, f, indent=2)
    print("\n📁 Saved to simulation/results/sensitivity_analysis.json")

    return 0


if __name__ == "__main__":
    sys.exit(main())
