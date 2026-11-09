"""Counterfactual evaluation of emergency pause policies."""

from __future__ import annotations

from dataclasses import asdict
from math import exp

import numpy as np

from .model import PausePolicy, Scenario, UserPosition
from .optimizer import synthesize_policy


def baseline_policies(scenario: Scenario) -> tuple[PausePolicy, ...]:
    names = {op.name for op in scenario.operations}
    costs = {op.name: op.pause_cost for op in scenario.operations}

    def make(name: str, paused: set[str]) -> PausePolicy:
        return PausePolicy(name, frozenset(paused), True, 0.0, sum(costs[p] for p in paused), 0.0)

    minpause = synthesize_policy(scenario.operations, scenario.attack_paths)
    return (
        make("No intervention", set()),
        make("Global freeze", names),
        make("Coarse risk pause", {"withdraw", "borrow", "liquidate", "flash_loan", "swap"}),
        make("Manual selective", {"borrow", "flash_loan", "oracle_update"}),
        minpause,
    )


def _can_recover(user: UserPosition, policy: PausePolicy) -> bool:
    if user.health_factor >= 1.0:
        return True
    debt = user.debt_value
    collateral = user.collateral_value
    if "repay" not in policy.paused:
        debt = max(1e-9, debt - user.available_repayment)
    if "add_collateral" not in policy.paused:
        collateral += user.available_extra_collateral
    return collateral * user.liquidation_threshold / debt >= 1.0


def evaluate_policy(scenario: Scenario, policy: PausePolicy) -> dict[str, float | int | str]:
    total_cost = sum(op.pause_cost for op in scenario.operations)
    blocked_volume = sum(op.pause_cost for op in scenario.operations if op.name in policy.paused)
    blocked_fraction = blocked_volume / total_cost

    path_blocked = np.array(
        [bool(policy.paused.intersection(path.operations)) for path in scenario.attack_paths],
        dtype=float,
    )
    attack_prevention = float(path_blocked.mean())
    remaining_at_detection = exp(-scenario.detection_delay_minutes / 55.0)
    prevented_loss = scenario.attack_loss_potential * remaining_at_detection * attack_prevention
    realized_attack_loss = scenario.attack_loss_potential - prevented_loss

    at_risk = [user for user in scenario.users if user.health_factor < 1.0]
    recovered = [user for user in at_risk if _can_recover(user, policy)]
    recovery_coverage = len(recovered) / len(at_risk) if at_risk else 1.0

    unrecovered = [user for user in at_risk if not _can_recover(user, policy)]
    shortfall = sum(
        max(0.0, user.debt_value - user.collateral_value * user.liquidation_threshold)
        for user in unrecovered
    )
    bad_debt = shortfall * (0.35 + 0.65 * scenario.utilization)
    liquidations = len(unrecovered) if "liquidate" not in policy.paused else 0
    deferred_positions = len(unrecovered) if "liquidate" in policy.paused else 0

    group_burdens = []
    for group in ("retail", "medium", "whale"):
        total = sum(op.group_costs.get(group, 0.0) for op in scenario.operations)
        blocked = sum(
            op.group_costs.get(group, 0.0)
            for op in scenario.operations
            if op.name in policy.paused
        )
        group_burdens.append(blocked / total if total else 0.0)
    fairness_disparity = max(group_burdens) - min(group_burdens)

    row = {
        "scenario_id": scenario.scenario_id,
        "incident_family": scenario.incident_family,
        "policy": policy.name,
        "feasible": int(policy.feasible),
        "paused_operations": ";".join(sorted(policy.paused)),
        "policy_size": len(policy.paused),
        "attack_prevention_rate": attack_prevention,
        "prevented_loss": prevented_loss,
        "realized_attack_loss": realized_attack_loss,
        "blocked_legitimate_fraction": blocked_fraction,
        "availability": 1.0 - blocked_fraction,
        "recovery_coverage": recovery_coverage,
        "bad_debt": bad_debt,
        "liquidations": liquidations,
        "deferred_positions": deferred_positions,
        "fairness_disparity": fairness_disparity,
    }
    for key, value in asdict(scenario).items():
        if key not in {"operations", "attack_paths", "users"}:
            row[key] = value
    return row


def run_scenarios(scenarios: list[Scenario]) -> list[dict[str, float | int | str]]:
    rows = []
    for scenario in scenarios:
        for policy in baseline_policies(scenario):
            rows.append(evaluate_policy(scenario, policy))
    return rows

