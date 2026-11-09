#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$repo_dir"

python -m pytest
PYTHONPATH=src python scripts/run_experiments.py
test -s results/scenario_results.csv
test -s figures/policy_comparison.pdf
latexmk -pdf -cd manuscript/main.tex
test -s manuscript/main.pdf

echo "MinPause validation complete: tests, experiments, figures, and PDF succeeded."

