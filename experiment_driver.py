#!/usr/bin/env python3
"""
Karpathy-Ralph Experimentation Loop Driver

Orchestrates multi-epoch, multi-subagent experimentation over the
nestshift-os simulation + paper pipeline.

Usage:
    python experiment_driver.py --workflow workflow.json --epochs 10
"""

import argparse
import json
import hashlib
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Hypothesis:
    id: str
    text: str
    target_metric: str
    expected_delta: float


@dataclass
class SubagentResult:
    role: str
    hypothesis_id: str
    workspace_dir: Path
    score: float = 0.0
    metric_delta: float = 0.0
    test_pass_rate: float = 0.0
    compile_ok: bool = False
    lines_changed: int = 0
    rationale_quality: float = 0.0
    accepted: bool = False
    log_path: Path = field(default_factory=Path)


@dataclass
class EpochManifest:
    epoch: int
    timestamp_start: str
    timestamp_end: Optional[str] = None
    hypotheses: List[Hypothesis] = field(default_factory=list)
    subagents: List[SubagentResult] = field(default_factory=list)
    aggregation_strategy: str = ""
    final_metrics: Dict = field(default_factory=dict)
    improvement_vs_baseline: float = 0.0


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def run_cmd(cmd: List[str], cwd: Path, timeout: int = 300) -> Tuple[int, str, str]:
    """Run a shell command and return (rc, stdout, stderr)."""
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def snapshot_sources(src_dirs: List[Path], dest: Path) -> None:
    """Copy source directories into a snapshot."""
    dest.mkdir(parents=True, exist_ok=True)
    for d in src_dirs:
        if d.exists():
            shutil.copytree(d, dest / d.name, dirs_exist_ok=True)


def compute_diff_size(prev: Path, curr: Path) -> int:
    """Approximate lines changed between two directories."""
    rc, out, _ = run_cmd(
        ["diff", "-ru", str(prev), str(curr)],
        cwd=Path("."),
        timeout=60,
    )
    if rc == 0:
        return 0
    return out.count("\n")


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

class Evaluator:
    def __init__(self, weights: Dict[str, float]):
        self.weights = weights

    def score(self, r: SubagentResult) -> float:
        # Normalize metric_delta arbitrarily; real impl should use baseline
        norm_delta = max(0.0, min(1.0, abs(r.metric_delta) * 10))
        diff_penalty = 1.0 / (1.0 + max(0, r.lines_changed - 50) / 100.0)

        s = 0.0
        s += self.weights.get("metric_delta", 0.4) * norm_delta
        s += self.weights.get("test_pass", 0.2) * r.test_pass_rate
        s += self.weights.get("compile_ok", 0.15) * (1.0 if r.compile_ok else 0.0)
        s += self.weights.get("diff_size", 0.15) * diff_penalty
        s += self.weights.get("rationale_quality", 0.10) * r.rationale_quality
        return round(s, 4)

    def run_tests(self, cwd: Path, cmd: List[str]) -> float:
        rc, out, _ = run_cmd(cmd, cwd, timeout=120)
        # Crude parsing: look for "X passed"
        if "passed" in out:
            parts = out.split()
            for i, p in enumerate(parts):
                if p == "passed" and i > 0:
                    try:
                        return 1.0  # Simplified: binary pass/fail for now
                    except ValueError:
                        pass
        return 1.0 if rc == 0 else 0.0

    def run_simulation(self, cwd: Path, cmd: List[str]) -> Dict:
        rc, out, _ = run_cmd(cmd, cwd, timeout=300)
        metrics_path = cwd / "simulation" / "results" / "experiment_results.json"
        if metrics_path.exists():
            with open(metrics_path) as f:
                return json.load(f)
        return {"error": "missing metrics", "stdout": out}

    def compile_paper(self, cwd: Path, cmd: List[str]) -> bool:
        rc, _, _ = run_cmd(cmd, cwd, timeout=120)
        return rc == 0


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

class Aggregator:
    @staticmethod
    def merge(results: List[SubagentResult], base_dir: Path) -> Path:
        """
        Merge accepted subagent workspaces into a unified working directory.
        Conflicts are resolved by highest score.
        """
        merged = base_dir / "merged"
        merged.mkdir(parents=True, exist_ok=True)

        # Start with baseline
        snapshot_sources(
            [base_dir / "simulation", base_dir / "papers", base_dir / "evals"],
            merged,
        )

        # Sort by score descending
        sorted_results = sorted(
            [r for r in results if r.accepted],
            key=lambda x: x.score,
            reverse=True,
        )

        applied_files: set = set()
        for r in sorted_results:
            ws = r.workspace_dir
            for src_file in ws.rglob("*"):
                if src_file.is_file():
                    rel = src_file.relative_to(ws)
                    if str(rel) not in applied_files:
                        dest = merged / rel
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src_file, dest)
                        applied_files.add(str(rel))
                    # If conflict: higher score already applied, skip

        return merged


# ---------------------------------------------------------------------------
# Hypothesis Generator
# ---------------------------------------------------------------------------

class HypothesisGenerator:
    """Simple rule-based hypothesis generator. Replace with LLM call for v2."""

    TEMPLATES = [
        {
            "id": "H_SIM_BUG",
            "text": "Fix a known simulation bug (e.g., comfort_bias not wired, fixed seed)",
            "target": "cost_reduction",
        },
        {
            "id": "H_NEW_MODEL",
            "text": "Add a new physical model (battery, solar PV, EV V2G)",
            "target": "cost_reduction",
        },
        {
            "id": "H_FIGURES",
            "text": "Improve figure quality or add new analysis plots",
            "target": "paper_quality",
        },
        {
            "id": "H_LATEX",
            "text": "Rewrite a paper section with updated empirical results",
            "target": "paper_quality",
        },
        {
            "id": "H_EVAL",
            "text": "Add new eval scenarios or tighten existing tests",
            "target": "test_pass_rate",
        },
    ]

    def generate(self, prev_metrics: Dict, epoch: int) -> List[Hypothesis]:
        # Rotate through templates, biasing toward under-performing metrics
        hyps = []
        for i, t in enumerate(self.TEMPLATES):
            hyps.append(
                Hypothesis(
                    id=f"{t['id']}_{epoch:03d}_{i}",
                    text=t["text"],
                    target_metric=t["target"],
                    expected_delta=0.05,
                )
            )
        return hyps[:4]  # Max 4


# ---------------------------------------------------------------------------
# Main Driver
# ---------------------------------------------------------------------------

class ExperimentDriver:
    def __init__(self, workflow_path: Path, project_root: Path):
        with open(workflow_path) as f:
            self.config = json.load(f)
        self.root = project_root
        self.log_dir = project_root / self.config["logging"]["dir"]
        self.evaluator = Evaluator(self.config["evaluation"]["weights"])
        self.hyp_gen = HypothesisGenerator()
        self.baseline_metrics: Dict = {}
        self.best_metrics: Dict = {}
        self.stagnant_count = 0

    def init_baseline(self) -> None:
        baseline_dir = self.log_dir / "artefacts" / "baseline"
        baseline_dir.mkdir(parents=True, exist_ok=True)

        print("[BASELINE] Snapshotting source code...")
        snapshot_sources(
            [self.root / "simulation", self.root / "papers", self.root / "evals"],
            baseline_dir,
        )

        print("[BASELINE] Running simulation...")
        self.baseline_metrics = self.evaluator.run_simulation(
            self.root, self.config["evaluation"]["sim_command"].split()
        )
        with open(baseline_dir / "metrics.json", "w") as f:
            json.dump(self.baseline_metrics, f, indent=2)

        print("[BASELINE] Compiling paper...")
        self.evaluator.compile_paper(
            self.root, self.config["evaluation"]["compile_command"].split()
        )
        pdf = self.root / "paper_main.pdf"
        if pdf.exists():
            shutil.copy2(pdf, baseline_dir / "baseline_paper.pdf")

        self.best_metrics = dict(self.baseline_metrics)
        print("[BASELINE] Complete.")

    def run_epoch(self, epoch: int) -> EpochManifest:
        print(f"\n{'='*60}")
        print(f"[EPOCH {epoch:03d}] Starting...")
        print(f"{'='*60}")

        manifest = EpochManifest(
            epoch=epoch,
            timestamp_start=datetime.now(timezone.utc).isoformat(),
        )

        epoch_dir = self.log_dir / "epochs" / f"epoch_{epoch:03d}"
        epoch_dir.mkdir(parents=True, exist_ok=True)

        # --- Phase 1: Hypotheses ---
        hypotheses = self.hyp_gen.generate(self.best_metrics, epoch)
        manifest.hypotheses = hypotheses
        print(f"[EPOCH {epoch:03d}] Generated {len(hypotheses)} hypotheses")

        # --- Phase 2: Spawn subagents (simulated for now) ---
        n_agents = min(
            self.config["subagents"]["count"]["max"],
            max(self.config["subagents"]["count"]["min"], len(hypotheses)),
        )
        results: List[SubagentResult] = []

        for i in range(n_agents):
            role = self.config["subagents"]["roles"][i % 4]
            hyp = hypotheses[i] if i < len(hypotheses) else hypotheses[-1]
            ws_dir = self.log_dir / "subagents" / f"epoch_{epoch:03d}_agent_{role}"
            ws_dir.mkdir(parents=True, exist_ok=True)

            print(f"[EPOCH {epoch:03d}] Subagent {role} attempting {hyp.id}...")

            # TODO: In v2, this spawns an actual subagent via Agent() tool.
            # For now, we create a placeholder result.
            result = SubagentResult(
                role=role,
                hypothesis_id=hyp.id,
                workspace_dir=ws_dir,
                log_path=ws_dir / "log.txt",
            )

            # Write subagent prompt to workspace
            with open(ws_dir / "PROMPT.txt", "w") as f:
                f.write(self._build_prompt(role, hyp, epoch))

            results.append(result)

        # --- Phase 3: Evaluation ---
        # In a real run, subagents would have modified files in their workspace.
        # We evaluate by merging each workspace individually and running tests.
        for r in results:
            # Placeholder evaluation until subagents are real
            r.test_pass_rate = 1.0
            r.compile_ok = True
            r.metric_delta = 0.0
            r.lines_changed = 0
            r.rationale_quality = 0.5
            r.score = self.evaluator.score(r)
            r.accepted = r.test_pass_rate == 1.0 and r.compile_ok

        manifest.subagents = results
        print(f"[EPOCH {epoch:03d}] Evaluation complete. Scores:")
        for r in results:
            print(f"  - Agent {r.role}: score={r.score:.3f} accepted={r.accepted}")

        # --- Phase 4: Aggregation ---
        accepted = [r for r in results if r.accepted]
        if not accepted:
            print(f"[EPOCH {epoch:03d}] No accepted subagents. Skipping aggregation.")
            manifest.aggregation_strategy = "none"
        else:
            best = max(accepted, key=lambda x: x.score)
            manifest.aggregation_strategy = f"best_agent_{best.role}"
            print(f"[EPOCH {epoch:03d}] Best agent: {best.role} (score={best.score:.3f})")

            # Merge workspaces
            merged_dir = Aggregator.merge(accepted, self.root)
            print(f"[EPOCH {epoch:03d}] Merged into {merged_dir}")

            # Run full sim on merged
            merged_metrics = self.evaluator.run_simulation(
                merged_dir, self.config["evaluation"]["sim_command"].split()
            )
            manifest.final_metrics = merged_metrics

            # Compute improvement
            # Simplified: compare a single key metric
            key = "cost_reduction_agile"
            prev_val = self.best_metrics.get(key, 0)
            curr_val = merged_metrics.get(key, 0)
            manifest.improvement_vs_baseline = curr_val - prev_val

            if manifest.improvement_vs_baseline > self.config["early_stop"]["min_improvement"]:
                self.stagnant_count = 0
                self.best_metrics = dict(merged_metrics)
                # Copy merged back to main project
                snapshot_sources([merged_dir], self.root)
            else:
                self.stagnant_count += 1

        # --- Phase 5: Logging ---
        manifest.timestamp_end = datetime.now(timezone.utc).isoformat()
        with open(epoch_dir / "manifest.json", "w") as f:
            json.dump(self._manifest_to_dict(manifest), f, indent=2)

        print(f"[EPOCH {epoch:03d}] Manifest written to {epoch_dir / 'manifest.json'}")
        return manifest

    def _build_prompt(self, role: str, hyp: Hypothesis, epoch: int) -> str:
        return f"""You are Subagent {role} in Epoch {epoch}.

HYPOTHESIS: {hyp.text}
TARGET METRIC: {hyp.target_metric}

PREVIOUS BEST METRICS:
{json.dumps(self.best_metrics, indent=2)}

RULES:
1. Do not break existing tests in evals/
2. All changes must be reversible
3. Log every action to log.txt
4. Target metric must improve by > 0.5%

OUTPUT FORMAT:
- Modified files (git diff)
- metrics.json
- Rationale (< 200 words)
"""

    def _manifest_to_dict(self, m: EpochManifest) -> Dict:
        return {
            "epoch": m.epoch,
            "timestamp_start": m.timestamp_start,
            "timestamp_end": m.timestamp_end,
            "hypotheses": [
                {"id": h.id, "text": h.text, "target": h.target_metric}
                for h in m.hypotheses
            ],
            "subagents": [
                {
                    "role": r.role,
                    "hypothesis": r.hypothesis_id,
                    "score": r.score,
                    "accepted": r.accepted,
                }
                for r in m.subagents
            ],
            "aggregation_strategy": m.aggregation_strategy,
            "final_metrics": m.final_metrics,
            "improvement_vs_baseline": m.improvement_vs_baseline,
        }

    def run(self) -> None:
        self.init_baseline()

        for epoch in range(1, self.config["max_epochs"] + 1):
            manifest = self.run_epoch(epoch)

            # Early stop check
            if self.stagnant_count >= self.config["early_stop"]["patience"]:
                print(f"\n[EARLY STOP] No improvement for {self.stagnant_count} epochs.")
                break

        # Final artefact
        final_dir = self.log_dir / "artefacts" / "final"
        final_dir.mkdir(parents=True, exist_ok=True)
        snapshot_sources(
            [self.root / "simulation", self.root / "papers", self.root / "evals"],
            final_dir,
        )
        with open(final_dir / "final_metrics.json", "w") as f:
            json.dump(self.best_metrics, f, indent=2)

        print(f"\n[DONE] Final artefacts in {final_dir}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Karpathy-Ralph Experiment Loop")
    parser.add_argument("--workflow", default="workflow.json", help="Path to workflow.json")
    parser.add_argument("--epochs", type=int, default=10, help="Max epochs to run")
    parser.add_argument("--root", default=".", help="Project root directory")
    args = parser.parse_args()

    driver = ExperimentDriver(
        workflow_path=Path(args.workflow),
        project_root=Path(args.root).resolve(),
    )
    driver.run()


if __name__ == "__main__":
    main()
