<p align="center">
  <img src="assets/minpause-banner.jpg" alt="MinPause banner: a selective circuit breaker blocks an attack path while recovery paths remain open" width="100%">
</p>

<p align="center">
  <a href="https://github.com/nikorokni/minpause-recovery-preserving-defi/actions/workflows/ci.yml"><img src="https://github.com/nikorokni/minpause-recovery-preserving-defi/actions/workflows/ci.yml/badge.svg" alt="Reproducibility workflow"></a>
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python 3.10+">
  <a href="manuscript/main.pdf"><img src="https://img.shields.io/badge/Paper-PDF-B31B1B?logo=adobeacrobatreader&logoColor=white" alt="Paper PDF"></a>
  <img src="https://img.shields.io/badge/Evaluation-Shadow%20Mode-0B7285" alt="Shadow-mode evaluation">
  <img src="https://img.shields.io/badge/Python%20tests-16%20passing-2F9E44" alt="16 passing Python tests">
  <img src="https://img.shields.io/badge/Solidity%20tests-2%20passing-2F9E44" alt="2 passing Solidity tests">
</p>

<p align="center">
  <strong>Pause less. Protect more.</strong><br>
  An auditable framework for selecting the minimum-cost emergency pause policy that blocks every supplied DeFi attack path while keeping borrower recovery operations available.
</p>

<p align="center">
  <a href="manuscript/main.pdf"><strong>Read the paper</strong></a> ·
  <a href="docs/MEHRAN_MATH_HANDOFF.md"><strong>Independent proof brief</strong></a> ·
  <a href="testnet/"><strong>Sepolia validation</strong></a> ·
  <a href="results/scenario_results.csv"><strong>Scenario results</strong></a> ·
  <a href="#reproduce-the-study"><strong>Reproduce</strong></a>
</p>

---

## Why MinPause?

Emergency controls in DeFi are commonly configured by hand. A global freeze is easy to reason about, but it blocks legitimate activity and can prevent borrowers from repaying debt or adding collateral. A narrow manual pause preserves availability, but may leave an alternative loss path executable.

MinPause treats incident response as a constrained weighted hitting-set problem:

> Select the least-cost set of operations that intersects every identified attack path, subject to `repay` and `add_collateral` remaining active.

If an incident cannot be contained without disabling a protected recovery operation, MinPause returns **infeasible** instead of silently weakening the guarantee.

## Research workflow

```mermaid
flowchart LR
    A[Incident alert] --> B[Attack-path set]
    B --> C[Action-effect model]
    C --> D{MinPause solver}
    R[Protected recovery actions] --> D
    V[Legitimate-use costs] --> D
    D --> E[Minimum pause policy]
    E --> F[Shadow-mode replay]
    F --> G[Security, availability, recovery]
```

The detector and attack-path extractor are outside the current scope. MinPause begins once a responder has a candidate family of paths to contain.

## Main results

The deterministic experiment uses **360 Latin-hypercube scenarios** and evaluates six policies per scenario, producing **2,160 policy-scenario runs**. The sixth policy deliberately omits one input path to measure model-risk sensitivity.

| Policy | Attack prevention | Legitimate availability | Recovery coverage | Mean policy size |
|---|---:|---:|---:|---:|
| No intervention | 0.0% | 100.0% | 81.2% | 0.00 |
| Global freeze | 100.0% | 0.0% | 2.5% | 9.00 |
| Coarse risk pause | 100.0% | 38.0% | 81.2% | 5.00 |
| Manual selective | 91.7% | 74.0% | 81.2% | 3.00 |
| **MinPause** | **100.0%** | **85.6%** | **81.2%** | **1.34** |
| MinPause — one path omitted | 94.3% | 85.7% | 81.2% | 1.29 |

<p align="center">
  <img src="figures/policy_comparison.png" alt="Comparison of attack prevention, legitimate availability, and recovery coverage" width="82%">
</p>

Recovery coverage is not 100% because keeping a recovery action callable does not mean every borrower has sufficient funds to use it. The model explicitly preserves this distinction.

<details>
<summary><strong>Robustness over detection delay and collateral shocks</strong></summary>

<p align="center">
  <img src="figures/robustness_surface.png" alt="Prevented loss across detection delays and collateral price shocks" width="78%">
</p>

MinPause covers every supplied path in the generated scenarios, but the economically preventable amount declines as detection is delayed. Policy synthesis therefore complements monitoring; it does not replace it.

</details>

## Mathematical model

For every pausable operation \(f\), let \(x_f=1\) mean “paused.” Each attack path \(P_k\) must be cut:

$$
\sum_{f\in P_k}x_f \ge 1 \qquad \forall P_k\in\mathcal P.
$$

Recovery-critical actions are fixed active:

$$
x_{\mathrm{repay}}=x_{\mathrm{addCollateral}}=0.
$$

The objective minimizes legitimate-use disruption plus group-burden disparity:

$$
\min_x\left(\sum_{f\in F}c_fx_f+\lambda\Delta(x)\right).
$$

The paper now contains complete statements and proofs for represented-path coverage (M1), feasibility (M2), resource-bounded recovery (M3), and NP-completeness/NP-hardness (M4). The [independent proof brief](docs/MEHRAN_MATH_HANDOFF.md) remains in the repository so a mathematical reviewer can audit the assumptions and return corrections without reading the full codebase.

## Controlled on-chain validation

The `testnet/` package contains an Euler-inspired, test-only Solidity market. Its deliberately unsafe `donateToReserves` transition can make a borrower unhealthy. The MinPause response pauses only that selector while `repay` and `addCollateral` remain callable.

- 2 deterministic Hardhat tests pass locally.
- A manual GitHub Actions workflow deploys the same fixture to **Sepolia**.
- The workflow saves contract addresses, transaction hashes, block numbers, selectors, and assertion results as an evidence artifact.
- This validates function-level enforcement and deployability; it is not a replay of Euler's historical mainnet state.

See [testnet/README.md](testnet/README.md) for the exact setup and the two required GitHub secrets.

## Repository map

```text
assets/
  minpause-banner.jpg          Repository banner
docs/
  MEHRAN_MATH_HANDOFF.md       Standalone independent proof-review brief
src/minpause/
  model.py                     Operations, paths, users, scenarios, policies
  optimizer.py                 Exact recovery-preserving pause synthesis
  scenarios.py                 Seeded Latin-hypercube experiment design
  simulation.py                Policy counterfactual evaluation
scripts/
  run_experiments.py           Regenerates CSVs, figures, and paper macros
tests/                          16 Python unit and integration tests
testnet/                        Solidity fixture, 2 tests, Sepolia deploy script
results/                        Scenario-level and aggregate outputs
figures/                        Publication figures in PNG and PDF
manuscript/
  main.tex                      Conference-paper source
  main.pdf                      Compiled paper
  references.bib                Bibliography
```

## Reproduce the study

```bash
git clone https://github.com/nikorokni/minpause-recovery-preserving-defi.git
cd minpause-recovery-preserving-defi

python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"

python -m pytest
python scripts/run_experiments.py
```

To rebuild everything, including the PDF:

```bash
bash run_all.sh
```

The full run regenerates the scenario CSV, aggregate summary, both figures, LaTeX result macros, and the manuscript PDF.

## Scope and claims

- Research prototype intended for **shadow-mode evaluation** before automation.
- Local Solidity validation is complete; public Sepolia deployment is claimed only when its workflow evidence artifact exists.
- No production or historical mainnet-fork validation claim.
- Attack paths are supplied to the optimizer; automatic path discovery is future work.
- The policy is only as sound as the supplied operation and attack-path model.
- The code has not been professionally audited and is not financial advice.

## Formal analysis status

| Item | Status | Required output |
|---|---|---|
| M1 — Attack-path coverage | Proved conditionally | Labelled transition system, hard dependency, catalogue completeness |
| M2 — Feasibility condition | Proved | Necessary and sufficient condition $P_k\setminus R\neq\varnothing$ |
| M3 — Finite borrower recovery | Proved conditionally | Exact resource condition and full-repayment boundary |
| M4 — Complexity | Proved | NP-completeness reduction from Minimum Weight Hitting Set |

The proofs are ready for independent mathematical review. Their assumptions are part of the claims: in particular, M1 does not cover attack paths absent from the supplied catalogue, and M3 does not guarantee that a borrower owns sufficient recovery resources.

## Citation

Citation metadata will be added after a submission venue is selected.

