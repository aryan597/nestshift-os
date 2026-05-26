# NestShift OS Evals Framework

## Philosophy

Evals are **regression tests for agent behaviour and system performance** — not unit tests. They verify the system works correctly end-to-end before any deployment.

### Key Principles

1. **Prompts, agent outputs, and spike patterns are first-class artifacts** — every eval records its complete context
2. **Results are committed to git** — baseline JSON is tracked, enabling regression detection
3. **Baseline comparison** — current results that diverge >20% from baseline trigger warnings
4. **Simulation-first** — evals run against mock data, no real hardware required

## Structure

```
evals/
├── README.md                 # This file
├── eval_energy_agent.py      # Energy optimization scenarios
├── eval_automation_agent.py  # Behavioural pattern tests
├── eval_nare_brain.py        # LIF/STDP integration tests
├── eval_pisafe.py            # Safety constraint tests
├── run_all.py                # Run all evals and print summary
└── results/
    ├── baseline.json         # Committed baseline results
    └── latest.json           # Generated on each run
```

## Running Evals

```bash
# Run all evals
python evals/run_all.py

# Run individual eval
python evals/eval_energy_agent.py
python evals/eval_automation_agent.py
python evals/eval_nare_brain.py
python evals/eval_pisafe.py
```

## Adding New Evals

1. Create `evals/eval_<name>.py`
2. Implement test scenarios as functions with `assert` statements
3. Each scenario should log timing and pass/fail status
4. Add to `run_all.py` to include in full suite
5. After first successful run, commit `evals/results/baseline.json`

## Baseline Management

When adding new evals or changing system behaviour:
1. Run evals on a known-good system
2. Copy `latest.json` to `baseline.json`
3. Commit to git

The `run_all.py` script will compare results and warn on regressions.