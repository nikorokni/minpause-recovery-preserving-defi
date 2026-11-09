"""Exact policy synthesis for the small function sets used by DeFi markets."""

from __future__ import annotations

from itertools import combinations
from math import inf
from typing import Iterable

from .model import AttackPath, Operation, PausePolicy


def covers_all(paused: Iterable[str], paths: Iterable[AttackPath]) -> bool:
    """Return whether every attack path intersects the paused set."""

    paused_set = frozenset(paused)
    return all(bool(paused_set.intersection(path.operations)) for path in paths)


def _fairness_disparity(paused: frozenset[str], operations: tuple[Operation, ...]) -> float:
    groups = sorted({group for op in operations for group in op.group_costs})
    if not groups:
        return 0.0
    burdens = []
    for group in groups:
        total = sum(op.group_costs.get(group, 0.0) for op in operations)
        blocked = sum(op.group_costs.get(group, 0.0) for op in operations if op.name in paused)
        burdens.append(blocked / total if total > 0 else 0.0)
    return max(burdens) - min(burdens)


def synthesize_policy(
    operations: Iterable[Operation],
    attack_paths: Iterable[AttackPath],
    *,
    fairness_weight: float = 0.15,
    policy_name: str = "MinPause",
) -> PausePolicy:
    """Find the least-cost attack-covering pause set by exhaustive enumeration.

    Recovery-critical actions are fixed to the active state.  The exact search is
    intentional: a lending market exposes only a small number of independently
    pausable actions, so enumeration is transparent and reproducible.
    """

    ops = tuple(operations)
    paths = tuple(attack_paths)
    protected = {op.name for op in ops if op.recovery_critical}
    candidates = tuple(op for op in ops if op.name not in protected)

    if any(path.operations.issubset(protected) for path in paths):
        return PausePolicy(policy_name, frozenset(), False, inf, inf, inf)

    best: PausePolicy | None = None
    for size in range(len(candidates) + 1):
        for subset in combinations(candidates, size):
            paused = frozenset(op.name for op in subset)
            if not covers_all(paused, paths):
                continue
            pause_cost = sum(op.pause_cost for op in subset)
            disparity = _fairness_disparity(paused, ops)
            objective = pause_cost + fairness_weight * disparity
            candidate = PausePolicy(
                policy_name, paused, True, objective, pause_cost, disparity
            )
            tie_key = (candidate.objective, len(candidate.paused), sorted(candidate.paused))
            if best is None:
                best = candidate
            else:
                best_key = (best.objective, len(best.paused), sorted(best.paused))
                if tie_key < best_key:
                    best = candidate

    if best is None:
        return PausePolicy(policy_name, frozenset(), False, inf, inf, inf)
    return best

