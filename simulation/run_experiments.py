#!/usr/bin/env python3
"""Run digital twin experiments and generate publishable results.

Reproduces the evaluation methodology from the paper:
- Multi-day simulation epochs
- Monte Carlo averaging
- Baseline comparisons
- Sensitivity analysis
"""

import json
import sys
import time
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent))

from env.household import Household
from env.tariff import (FlatTariff, TimeOfUseTariff, AgileTariff,
                        VolatileTariff)
from env.simulator import Simulator, SimulationConfig, analyze_outcomes
from controllers import (no_optimization_controller, rule_based_controller,
                         proposed_controller, hybrid_controller)
from agents.energy_agent import EnergyAgent
from agents.automation_agent import AutomationAgent
from agents.system_agent import SystemAgent


def run_single_scenario(tariff, controller_name, controller_fn,
                        days=30, seed=42, **agent_kwargs) -> dict:
    """Run one simulation scenario."""
    household = Household(seed=seed)
    config = SimulationConfig(days=days, seed=seed)
    sim = Simulator(household, tariff, config)

    # Create agents if needed
    energy_agent = None
    automation_agent = None

    if controller_name in ["proposed", "hybrid"]:
        energy_agent = EnergyAgent(comfort_bias=agent_kwargs.get("comfort_bias", 0.5))
        automation_agent = AutomationAgent()

    # Run simulation
    if controller_name == "hybrid":
        outcomes = sim.run_with_learning(
            hybrid_controller, energy_agent, automation_agent
        )
    elif controller_name == "proposed":
        outcomes = sim.run_with_learning(
            proposed_controller, energy_agent, automation_agent
        )
    else:
        outcomes = sim.run(controller_fn)

    metrics = analyze_outcomes(outcomes)
    metrics["controller"] = controller_name
    metrics["tariff"] = tariff.__class__.__name__
    metrics["days"] = days
    metrics["seed"] = seed

    # Add agent-specific metrics
    if energy_agent:
        metrics.update(energy_agent.get_metrics())
    if automation_agent:
        metrics.update(automation_agent.get_metrics())

    return metrics


def run_monte_carlo(tariff, controller_name, controller_fn,
                    n_runs=10, days=30) -> List[dict]:
    """Run multiple Monte Carlo trials."""
    results = []
    for i in range(n_runs):
        result = run_single_scenario(
            tariff, controller_name, controller_fn,
            days=days, seed=1000 + i
        )
        results.append(result)
    return results


def compute_statistics(results: List[dict]) -> dict:
    """Aggregate statistics across Monte Carlo runs."""
    costs = [r["total_cost_gbp"] for r in results]
    energies = [r["total_energy_kwh"] for r in results]
    comforts = [r["avg_comfort_penalty"] for r in results]

    return {
        "mean_cost": np.mean(costs),
        "std_cost": np.std(costs),
        "mean_energy": np.mean(energies),
        "std_energy": np.std(energies),
        "mean_comfort": np.mean(comforts),
        "std_comfort": np.std(comforts),
        "cost_ci_low": np.percentile(costs, 2.5),
        "cost_ci_high": np.percentile(costs, 97.5),
    }


def cost_reduction(baseline_results: List[dict],
                   system_results: List[dict]) -> dict:
    """Compute cost reduction relative to baseline."""
    baseline_costs = [r["total_cost_gbp"] for r in baseline_results]
    system_costs = [r["total_cost_gbp"] for r in system_results]

    reductions = []
    for b, s in zip(baseline_costs, system_costs):
        if b > 0:
            reductions.append((b - s) / b * 100)

    return {
        "mean_reduction_pct": np.mean(reductions) if reductions else 0,
        "std_reduction_pct": np.std(reductions) if reductions else 0,
        "ci_low": np.percentile(reductions, 2.5) if reductions else 0,
        "ci_high": np.percentile(reductions, 97.5) if reductions else 0,
    }


def run_experiment_suite():
    """Run full experimental suite."""
    print("=" * 70)
    print("NESTSHIFT DIGITAL TWIN — EXPERIMENTAL EVALUATION")
    print("=" * 70)

    # Experiment parameters
    DAYS = 30
    N_RUNS = 20  # Monte Carlo runs per scenario

    tariffs = {
        "Flat": FlatTariff(price=0.30),
        "ToU": TimeOfUseTariff(off_peak=0.15, peak=0.45),
        "Agile": AgileTariff(seed=42, base_price=0.15, volatility=0.08),
        "Volatile": VolatileTariff(seed=99),
    }

    controllers = {
        "No-Optimization": no_optimization_controller,
        "Rule-Based": rule_based_controller,
        "Proposed": proposed_controller,
        "Hybrid": hybrid_controller,
    }

    all_results = {}

    for tariff_name, tariff in tariffs.items():
        print(f"\n{'─' * 70}")
        print(f"TARIFF: {tariff_name}")
        print(f"{'─' * 70}")

        tariff_results = {}

        for ctrl_name, ctrl_fn in controllers.items():
            print(f"  Running {ctrl_name}...", end=" ", flush=True)
            start = time.time()

            results = run_monte_carlo(tariff, ctrl_name, ctrl_fn,
                                      n_runs=N_RUNS, days=DAYS)
            stats = compute_statistics(results)

            elapsed = time.time() - start
            print(f"done in {elapsed:.1f}s | "
                  f"cost=£{stats['mean_cost']:.2f} ± {stats['std_cost']:.2f} | "
                  f"comfort={stats['mean_comfort']:.4f}")

            tariff_results[ctrl_name] = {
                "raw": results,
                "stats": stats,
            }

        # Compute cost reductions
        baseline_results = tariff_results["No-Optimization"]["raw"]
        for ctrl_name in ["Rule-Based", "Proposed", "Hybrid"]:
            system_results = tariff_results[ctrl_name]["raw"]
            reduction = cost_reduction(baseline_results, system_results)
            tariff_results[ctrl_name]["reduction"] = reduction
            print(f"    → {ctrl_name} cost reduction: "
                  f"{reduction['mean_reduction_pct']:.1f}% "
                  f"[{reduction['ci_low']:.1f}, {reduction['ci_high']:.1f}]")

        all_results[tariff_name] = tariff_results

    return all_results


def generate_tables(all_results: dict):
    """Generate LaTeX-ready tables."""
    print("\n" + "=" * 70)
    print("RESULTS TABLES")
    print("=" * 70)

    # Table 1: Cost comparison across tariffs and controllers
    print("\nTable 1: Mean Total Cost (£) over 30 days")
    print("-" * 70)
    header = f"{'Controller':<18}"
    for tariff_name in all_results:
        header += f"{tariff_name:>12}"
    print(header)
    print("-" * 70)

    for ctrl_name in ["No-Optimization", "Rule-Based", "Proposed", "Hybrid"]:
        row = f"{ctrl_name:<18}"
        for tariff_name in all_results:
            stats = all_results[tariff_name][ctrl_name]["stats"]
            row += f"{stats['mean_cost']:>10.2f} ± {stats['std_cost']:<2.2f}"
        print(row)

    # Table 2: Cost reduction percentages
    print("\nTable 2: Cost Reduction vs No-Optimization (%)")
    print("-" * 70)
    header = f"{'Controller':<18}"
    for tariff_name in all_results:
        header += f"{tariff_name:>12}"
    print(header)
    print("-" * 70)

    for ctrl_name in ["Rule-Based", "Proposed", "Hybrid"]:
        row = f"{ctrl_name:<18}"
        for tariff_name in all_results:
            reduction = all_results[tariff_name][ctrl_name]["reduction"]
            mean = reduction["mean_reduction_pct"]
            ci_low = reduction["ci_low"]
            ci_high = reduction["ci_high"]
            row += f"{mean:>10.1f} [{ci_low:.1f},{ci_high:.1f}]"
        print(row)

    # Table 3: Comfort penalty
    print("\nTable 3: Average Comfort Penalty")
    print("-" * 70)
    header = f"{'Controller':<18}"
    for tariff_name in all_results:
        header += f"{tariff_name:>12}"
    print(header)
    print("-" * 70)

    for ctrl_name in ["No-Optimization", "Rule-Based", "Proposed", "Hybrid"]:
        row = f"{ctrl_name:<18}"
        for tariff_name in all_results:
            stats = all_results[tariff_name][ctrl_name]["stats"]
            row += f"{stats['mean_comfort']:>12.4f}"
        print(row)


def save_results(all_results: dict, output_dir: str = "results"):
    """Save results to JSON."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Flatten for serialization
    serializable = {}
    for tariff, controllers in all_results.items():
        serializable[tariff] = {}
        for ctrl, data in controllers.items():
            serializable[tariff][ctrl] = {
                "stats": data["stats"],
                "reduction": data.get("reduction", {}),
            }

    with open(f"{output_dir}/experiment_results.json", "w") as f:
        json.dump(serializable, f, indent=2, default=str)

    print(f"\n📁 Results saved to {output_dir}/experiment_results.json")


def main():
    start_time = time.time()

    all_results = run_experiment_suite()
    generate_tables(all_results)
    save_results(all_results, output_dir="simulation/results")

    total_time = time.time() - start_time
    print(f"\n{'=' * 70}")
    print(f"Total experiment time: {total_time:.1f}s")
    print(f"{'=' * 70}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
