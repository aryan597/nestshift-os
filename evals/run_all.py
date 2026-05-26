#!/usr/bin/env python3
"""Run all evals and print summary table."""

import json
import sys
from datetime import datetime
from pathlib import Path

# Ensure paths
sys.path.insert(0, "evals")
sys.path.insert(0, "services/brain")
sys.path.insert(0, "services/api")


def run_evals():
    """Import and run all eval modules."""
    results = {}
    
    # Energy Agent
    print("Running Energy Agent evals...")
    from eval_energy_agent import eval_all_scenarios as energy_scenarios
    results["energy_agent"] = energy_scenarios()
    
    # Automation Agent
    print("Running Automation Agent evals...")
    from eval_automation_agent import eval_all_scenarios as auto_scenarios
    results["automation_agent"] = auto_scenarios()
    
    # NARE Brain
    print("Running NARE Brain evals...")
    from eval_nare_brain import eval_all_scenarios as nare_scenarios
    results["nare_brain"] = nare_scenarios()
    
    # Πsafe
    print("Running Πsafe evals...")
    from eval_pisafe import eval_all_scenarios as pisafe_scenarios
    results["pisafe"] = pisafe_scenarios()
    
    return results


def check_regression(current: dict, baseline_path: str) -> dict:
    """Check for regressions against baseline."""
    baseline_path = Path(baseline_path)
    if not baseline_path.exists():
        return {"has_baseline": False}
    
    with open(baseline_path) as f:
        baseline = json.load(f)
    
    warnings = []
    tolerance = 0.20  # 20% tolerance
    
    for eval_name in ["energy_agent", "automation_agent", "nare_brain", "pisafe"]:
        if eval_name not in current or eval_name not in baseline:
            continue
        
        cur = current[eval_name]
        base = baseline[eval_name]
        
        # Check pass rate
        cur_pass_rate = cur["passed"] / cur["tests"]
        base_pass_rate = base["passed"] / base["tests"]
        
        if cur_pass_rate < base_pass_rate - tolerance:
            warnings.append(
                f"{eval_name}: pass rate regressed from {base_pass_rate:.0%} to {cur_pass_rate:.0%}"
            )
        
        # Check latency
        cur_latency = cur.get("avg_latency_ms", 0)
        base_latency = base.get("avg_latency_ms", 0)
        
        if cur_latency > base_latency * (1 + tolerance):
            warnings.append(
                f"{eval_name}: latency increased from {base_latency:.1f}ms to {cur_latency:.1f}ms"
            )
    
    return {
        "has_baseline": True,
        "baseline": baseline,
        "warnings": warnings
    }


def main():
    print("\n" + "=" * 60)
    print("🏠 NestShift OS Evaluation Suite")
    print("=" * 60 + "\n")
    
    # Run all evals
    results = run_evals()
    
    # Add run metadata
    results["run_date"] = datetime.now().strftime("%Y-%m-%d")
    
    # Print summary table
    print("\n" + "=" * 60)
    print("📊 RESULTS SUMMARY")
    print("=" * 60)
    
    print("\n┌─────────────────────────────┬────────┬──────────┬─────────┐")
    print("│ Eval                        │ Tests  │ Status   │ Latency │")
    print("├─────────────────────────────┼────────┼──────────┼─────────┤")
    
    total_tests = 0
    total_passed = 0
    
    eval_names = [
        ("energy_agent", "Energy Agent"),
        ("automation_agent", "Automation Agent"),
        ("nare_brain", "NARE Brain"),
        ("pisafe", "Πsafe Safety Filter"),
    ]
    
    for eval_key, eval_name in eval_names:
        r = results.get(eval_key, {})
        tests = r.get("tests", 0)
        passed = r.get("passed", 0)
        latency = r.get("avg_latency_ms", 0)
        
        status = "✅ PASS" if passed == tests else "⚠️ PARTIAL" if passed > 0 else "❌ FAIL"
        
        print(f"│ {eval_name:<27} │ {passed:>4}/{tests:<1} │ {status:<8} │ {latency:>6.1f}ms │")
        
        total_tests += tests
        total_passed += passed
    
    print("└─────────────────────────────┴────────┴──────────┴─────────┘")
    
    # Overall status
    overall_status = "✅ ALL PASS" if total_passed == total_tests else f"⚠️ {total_passed}/{total_tests}"
    print(f"\nOverall: {overall_status}")
    
    # Check regressions
    baseline_path = "evals/results/baseline.json"
    regression = check_regression(results, baseline_path)
    
    if regression["has_baseline"]:
        if regression["warnings"]:
            print("\n⚠️ REGRESSION WARNINGS:")
            for w in regression["warnings"]:
                print(f"   - {w}")
        else:
            print("\n✅ No regressions detected vs baseline")
    
    # Save results
    results_dir = Path("evals/results")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    with open(results_dir / "latest.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📁 Results saved to evals/results/latest.json")
    
    # Prompt to save baseline if none exists
    if not regression["has_baseline"]:
        print("\n💡 First run - baseline not set.")
        print("   Run again after fixing issues to set baseline.")
    
    return 0 if total_passed == total_tests else 1


if __name__ == "__main__":
    sys.exit(main())