# MinPause

MinPause synthesizes the smallest legitimate-use-cost emergency pause policy that intersects every supplied DeFi attack path while keeping borrower recovery actions available.

The repository accompanies the conference-paper draft **“MinPause: Recovery-Preserving Emergency Control for DeFi Lending.”** The empirical manuscript is complete; four precisely scoped proof tasks are highlighted for the mathematical collaborator.

## Main result

Across 360 deterministic Latin-hypercube scenarios (1,800 policy evaluations), MinPause blocks 100% of the supplied attack paths while retaining 85.6% mean legitimate availability. Its mean policy pauses 1.34 operations, compared with nine under a global freeze.

These are simulation results, not claims of mainnet deployment. Attack paths are supplied to the optimizer and must be sound for the incident being analysed.

## Repository layout

```text
src/minpause/               Core model, optimizer, scenario generator, simulator
scripts/run_experiments.py  Reproduces CSV results, figures, and LaTeX macros
tests/                      Unit and integration tests
results/                    Scenario-level and aggregate experiment outputs
figures/                    Paper figures in PDF and PNG
manuscript/                 LaTeX source, bibliography, and compiled PDF
```

## Reproduce

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m pytest
python scripts/run_experiments.py
cd manuscript
latexmk -pdf main.tex
```

For a clean end-to-end run:

```bash
bash run_all.sh
```

## Mathematical completion

The orange boxes in Section 5 of the PDF and the handoff checklist in Appendix A contain the only intentionally incomplete parts:

1. attack-path coverage under the trace-to-set abstraction;
2. the feasibility iff condition;
3. finite borrower recovery and its resource conditions; and
4. the weighted-hitting-set complexity reduction.

All assumptions, notation, code locations, and requested proof outputs are included in the PDF.

## Scope

- Research prototype and shadow-mode evaluation only.
- No production or mainnet deployment claim.
- No automatic attack-path discovery.
- Not audited and not financial advice.

## Citation

Citation metadata will be added after the mathematical section is completed and the submission venue is selected.

